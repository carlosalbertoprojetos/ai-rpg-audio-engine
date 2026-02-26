from collections.abc import Callable
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status

from app.application.audio.use_cases import ExecuteDueSoundEventsCommand, ScheduleSoundEventCommand
from app.application.identity.use_cases import IssueTokenCommand, RegisterUserCommand
from app.application.tableops.use_cases import (
    AddPlayerCommand,
    CreateTableCommand,
    UpdatePlayerAvailabilityCommand,
)
from app.container import Container
from app.interfaces.api.auth import (
    AuthContext,
    build_auth_dependency,
    ensure_same_organization,
    require_roles,
)
from app.interfaces.schemas.audio import ScheduleSoundEventRequest, SoundEventResponse
from app.interfaces.schemas.auth import IssueTokenRequest, RegisterRequest, TokenResponse
from app.interfaces.schemas.tableops import (
    AddPlayerRequest,
    CreateTableRequest,
    CreateTableResponse,
    PlayerResponse,
    UpdateAvailabilityRequest,
)

ADMIN_OR_NARRATOR = {"admin", "narrator"}
READ_AUDIT_ROLES = {"admin", "narrator", "observer"}
VALID_ROLES = {"admin", "narrator", "observer"}


def get_router(get_container: Callable[[], Container]) -> APIRouter:
    router = APIRouter()
    get_auth_context = build_auth_dependency(get_container)

    @router.get("/health")
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    @router.post("/auth/register")
    async def register(
        request: RegisterRequest,
        container: Container = Depends(get_container),
    ) -> dict[str, str]:
        if request.role not in VALID_ROLES:
            raise HTTPException(status_code=400, detail="invalid role")
        profile = await container.use_cases.register_user(
            RegisterUserCommand(
                email=request.email,
                display_name=request.display_name,
                password=request.password,
                organization_id=request.organization_id,
                role=request.role,
            )
        )
        return {"user_id": profile.user_id, "organization_id": profile.organization_id}

    @router.post("/auth/token", response_model=TokenResponse)
    async def issue_token(
        request: IssueTokenRequest,
        container: Container = Depends(get_container),
    ) -> TokenResponse:
        try:
            token_result = await container.use_cases.issue_token(
                IssueTokenCommand(
                    email=request.email,
                    password=request.password,
                    organization_id=request.organization_id,
                )
            )
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid credentials",
            ) from exc
        return TokenResponse(
            access_token=token_result.access_token,
            token_type=token_result.token_type,
        )

    @router.post("/tables", response_model=CreateTableResponse)
    async def create_table(
        request: CreateTableRequest,
        auth: AuthContext = Depends(get_auth_context),
        container: Container = Depends(get_container),
    ) -> CreateTableResponse:
        require_roles(auth, ADMIN_OR_NARRATOR, "create_table")
        table = await container.use_cases.create_table(
            CreateTableCommand(
                organization_id=auth.organization_id,
                name=request.name,
                actor_id=auth.user_id,
            )
        )
        return CreateTableResponse(
            id=table.id,
            organization_id=table.organization_id,
            name=table.name,
        )

    @router.post("/tables/{table_id}/players", response_model=PlayerResponse)
    async def add_player(
        table_id: str,
        request: AddPlayerRequest,
        auth: AuthContext = Depends(get_auth_context),
        container: Container = Depends(get_container),
    ) -> PlayerResponse:
        require_roles(auth, ADMIN_OR_NARRATOR, "add_player")
        try:
            player = await container.use_cases.add_player(
                AddPlayerCommand(
                    organization_id=auth.organization_id,
                    table_id=table_id,
                    display_name=request.display_name,
                    user_id=request.user_id,
                    actor_id=auth.user_id,
                )
            )
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return PlayerResponse(
            id=player.id,
            display_name=player.display_name,
            availability=player.availability,
            user_id=player.user_id,
        )

    @router.patch("/tables/{table_id}/players/{player_id}", response_model=PlayerResponse)
    async def update_player_availability(
        table_id: str,
        player_id: str,
        request: UpdateAvailabilityRequest,
        auth: AuthContext = Depends(get_auth_context),
        container: Container = Depends(get_container),
    ) -> PlayerResponse:
        require_roles(auth, ADMIN_OR_NARRATOR, "update_player_availability")
        try:
            player = await container.use_cases.update_player_availability(
                UpdatePlayerAvailabilityCommand(
                    organization_id=auth.organization_id,
                    table_id=table_id,
                    player_id=player_id,
                    availability=request.availability,
                    actor_id=auth.user_id,
                )
            )
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return PlayerResponse(
            id=player.id,
            display_name=player.display_name,
            availability=player.availability,
            user_id=player.user_id,
        )

    @router.post("/sound-events", response_model=SoundEventResponse)
    async def schedule_sound_event(
        request: ScheduleSoundEventRequest,
        auth: AuthContext = Depends(get_auth_context),
        container: Container = Depends(get_container),
    ) -> SoundEventResponse:
        require_roles(auth, ADMIN_OR_NARRATOR, "schedule_sound_event")
        table = await container.table_repository.get_by_id(request.table_id)
        if table is None:
            raise HTTPException(status_code=404, detail="table not found")
        ensure_same_organization(auth, table.organization_id)

        sound_event = await container.use_cases.schedule_sound_event(
            ScheduleSoundEventCommand(
                organization_id=auth.organization_id,
                table_id=request.table_id,
                session_id=request.session_id,
                action=request.action,
                execute_at=request.execute_at,
                target_track_id=request.target_track_id,
                actor_id=auth.user_id,
            )
        )
        return SoundEventResponse(
            id=sound_event.id,
            table_id=sound_event.table_id,
            session_id=sound_event.session_id,
            action=sound_event.action,
            execute_at=sound_event.execute_at,
            state=sound_event.state.value,
            target_track_id=sound_event.target_track_id,
        )

    @router.post("/sound-events/execute-due")
    async def execute_due_sound_events(
        auth: AuthContext = Depends(get_auth_context),
        container: Container = Depends(get_container),
    ) -> dict[str, int]:
        require_roles(auth, ADMIN_OR_NARRATOR, "execute_due_sound_events")
        events = await container.use_cases.execute_due_sound_events(
            command=ExecuteDueSoundEventsCommand(up_to=datetime.now(UTC))
        )
        return {"processed": len(events)}

    @router.get("/audit/{organization_id}")
    async def list_audit_logs(
        organization_id: str,
        auth: AuthContext = Depends(get_auth_context),
        container: Container = Depends(get_container),
    ) -> list[dict[str, str]]:
        require_roles(auth, READ_AUDIT_ROLES, "list_audit_logs")
        ensure_same_organization(auth, organization_id)
        entries = await container.audit_repository.list_by_organization(organization_id)
        return [
            {
                "id": entry.id,
                "action": entry.action,
                "target": entry.target,
                "created_at": entry.created_at.isoformat(),
            }
            for entry in entries
        ]

    @router.websocket("/ws/tables/{table_id}")
    async def table_ws(
        websocket: WebSocket,
        table_id: str,
        token: str,
        container: Container = Depends(get_container),
    ) -> None:
        try:
            payload = container.token_service.decode(token)
        except ValueError:
            await websocket.close(code=4401)
            return
        table = await container.table_repository.get_by_id(table_id)
        if table is not None and table.organization_id != payload.organization_id:
            await websocket.close(code=4403)
            return

        manager = container.socket_manager
        await manager.connect(table_id, websocket)
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            await manager.disconnect(table_id, websocket)

    return router
