from collections.abc import Callable
from datetime import UTC, datetime
import mimetypes
from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Response,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
    status,
)

from app.application.audio.use_cases import (
    CreateAudioTrackCommand,
    CreateTriggerCommand,
    ExecuteDueSoundEventsCommand,
    GenerateAdaptiveAmbienceCommand,
    ScheduleSoundEventCommand,
)
from app.application.identity.use_cases import (
    IssueTokenCommand,
    ListUsersCommand,
    RegisterUserCommand,
    UpdateUserCommand,
)
from app.application.organization.use_cases import (
    EnsureOrganizationCommand,
    UpdateSubscriptionPlanCommand,
)
from app.application.session.use_cases import EndSessionCommand, StartSessionCommand
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
from app.interfaces.schemas.enterprise_audio import (
    AIContextResponse,
    AudioTrackResponse,
    CreateAudioTrackRequest,
    CreateTriggerRequest,
    GenerateAIContextRequest,
    TriggerResponse,
)
from app.interfaces.schemas.organization import OrganizationResponse, UpdatePlanRequest
from app.interfaces.schemas.session import SessionResponse, StartSessionRequest
from app.interfaces.schemas.tableops import (
    AddPlayerRequest,
    CreateTableRequest,
    CreateTableResponse,
    PlayerResponse,
    UpdateAvailabilityRequest,
)
from app.interfaces.schemas.users import UpdateUserRequest, UserSummaryResponse

ADMIN_OR_NARRATOR = {"admin", "narrator"}
READ_AUDIT_ROLES = {"admin", "narrator", "observer"}
VALID_ROLES = {"admin", "narrator", "observer"}
ADMIN_ONLY = {"admin"}
NON_STANDARD_AUDIO_MIME_MAP = {
    "audio/mp3": "audio/mpeg",
    "audio/x-wav": "audio/wav",
    "audio/wave": "audio/wav",
    "audio/x-m4a": "audio/mp4",
}
EXTENSION_AUDIO_MIME_MAP = {
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".ogg": "audio/ogg",
    ".opus": "audio/opus",
    ".m4a": "audio/mp4",
    ".aac": "audio/aac",
    ".flac": "audio/flac",
    ".weba": "audio/webm",
}


def _canonicalize_mime(raw: str | None) -> str | None:
    if not raw:
        return None
    normalized = raw.split(";", 1)[0].strip().lower()
    if not normalized:
        return None
    return NON_STANDARD_AUDIO_MIME_MAP.get(normalized, normalized)


def _guess_audio_mime_from_name(name: str | None) -> str | None:
    if not name:
        return None
    guessed, _ = mimetypes.guess_type(name)
    guessed_mime = _canonicalize_mime(guessed)
    if guessed_mime and guessed_mime.startswith("audio/"):
        return guessed_mime
    suffix = Path(name).suffix.lower()
    return EXTENSION_AUDIO_MIME_MAP.get(suffix)


def _resolve_upload_audio_mime(uploaded_mime: str | None, filename: str | None) -> str:
    canonical = _canonicalize_mime(uploaded_mime)
    if canonical and canonical.startswith("audio/"):
        return canonical
    guessed = _guess_audio_mime_from_name(filename)
    if guessed:
        return guessed
    raise HTTPException(status_code=415, detail="unsupported audio format")


def _resolve_stream_audio_mime(stored_mime: str | None, object_key: str) -> str:
    canonical = _canonicalize_mime(stored_mime)
    if canonical and canonical.startswith("audio/"):
        return canonical
    guessed = _guess_audio_mime_from_name(object_key)
    if guessed:
        return guessed
    return "audio/mpeg"


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
        await container.use_cases.ensure_organization(
            EnsureOrganizationCommand(
                organization_id=request.organization_id,
                owner_user_id=profile.user_id,
                name=f"Organization {request.organization_id}",
            )
        )
        return {"user_id": profile.user_id, "organization_id": profile.organization_id}

    @router.get("/organizations/{organization_id}", response_model=OrganizationResponse)
    async def get_organization(
        organization_id: str,
        auth: AuthContext = Depends(get_auth_context),
        container: Container = Depends(get_container),
    ) -> OrganizationResponse:
        require_roles(auth, READ_AUDIT_ROLES, "get_organization")
        ensure_same_organization(auth, organization_id)
        organization = await container.organization_repository.get_by_id(organization_id)
        if organization is None:
            raise HTTPException(status_code=404, detail="organization not found")
        return OrganizationResponse(
            id=organization.id,
            name=organization.name,
            owner_user_id=organization.owner_user_id,
            subscription_plan=organization.subscription.plan,
            subscription_status=organization.subscription.status.value,
            billing_cycle=organization.subscription.billing_cycle,
        )

    @router.patch(
        "/organizations/{organization_id}/subscription",
        response_model=OrganizationResponse,
    )
    async def update_subscription(
        organization_id: str,
        request: UpdatePlanRequest,
        auth: AuthContext = Depends(get_auth_context),
        container: Container = Depends(get_container),
    ) -> OrganizationResponse:
        require_roles(auth, ADMIN_ONLY, "update_subscription")
        ensure_same_organization(auth, organization_id)
        organization = await container.use_cases.update_subscription_plan(
            UpdateSubscriptionPlanCommand(
                organization_id=organization_id,
                actor_id=auth.user_id,
                plan=request.plan,
            )
        )
        return OrganizationResponse(
            id=organization.id,
            name=organization.name,
            owner_user_id=organization.owner_user_id,
            subscription_plan=organization.subscription.plan,
            subscription_status=organization.subscription.status.value,
            billing_cycle=organization.subscription.billing_cycle,
        )

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

    @router.get("/users", response_model=list[UserSummaryResponse])
    async def list_users(
        auth: AuthContext = Depends(get_auth_context),
        container: Container = Depends(get_container),
    ) -> list[UserSummaryResponse]:
        require_roles(auth, ADMIN_ONLY, "list_users")
        users = await container.use_cases.list_users(
            ListUsersCommand(organization_id=auth.organization_id)
        )
        return [
            UserSummaryResponse(
                user_id=user.user_id,
                email=user.email,
                display_name=user.display_name,
                organization_id=user.organization_id,
                role=user.role,
            )
            for user in users
        ]

    @router.patch("/users/{user_id}", response_model=UserSummaryResponse)
    async def update_user(
        user_id: str,
        request: UpdateUserRequest,
        auth: AuthContext = Depends(get_auth_context),
        container: Container = Depends(get_container),
    ) -> UserSummaryResponse:
        require_roles(auth, ADMIN_ONLY, "update_user")
        try:
            updated = await container.use_cases.update_user(
                UpdateUserCommand(
                    organization_id=auth.organization_id,
                    user_id=user_id,
                    display_name=request.display_name,
                    role=request.role,
                )
            )
        except ValueError as exc:
            message = str(exc)
            if "scope mismatch" in message:
                raise HTTPException(status_code=403, detail=message) from exc
            raise HTTPException(status_code=404, detail=message) from exc

        if updated.organization_id != auth.organization_id:
            raise HTTPException(status_code=403, detail="organization scope mismatch")

        return UserSummaryResponse(
            user_id=updated.user_id,
            email=updated.email,
            display_name=updated.display_name,
            organization_id=updated.organization_id,
            role=updated.role,
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

    @router.post("/sessions", response_model=SessionResponse)
    async def start_session(
        request: StartSessionRequest,
        auth: AuthContext = Depends(get_auth_context),
        container: Container = Depends(get_container),
    ) -> SessionResponse:
        require_roles(auth, ADMIN_OR_NARRATOR, "start_session")
        try:
            session_entity = await container.use_cases.start_session(
                StartSessionCommand(
                    organization_id=auth.organization_id,
                    table_id=request.table_id,
                    actor_id=auth.user_id,
                )
            )
        except ValueError as exc:
            detail = str(exc)
            if "scope mismatch" in detail:
                raise HTTPException(status_code=403, detail=detail) from exc
            raise HTTPException(status_code=404, detail=detail) from exc
        return SessionResponse(
            id=session_entity.id,
            table_id=session_entity.table_id,
            state=session_entity.state.value,
            started_at=session_entity.started_at,
            ended_at=session_entity.ended_at,
        )

    @router.post("/sessions/{session_id}/end", response_model=SessionResponse)
    async def end_session(
        session_id: str,
        auth: AuthContext = Depends(get_auth_context),
        container: Container = Depends(get_container),
    ) -> SessionResponse:
        require_roles(auth, ADMIN_OR_NARRATOR, "end_session")
        try:
            session_entity = await container.use_cases.end_session(
                EndSessionCommand(
                    organization_id=auth.organization_id,
                    session_id=session_id,
                    actor_id=auth.user_id,
                )
            )
        except ValueError as exc:
            detail = str(exc)
            if "scope mismatch" in detail:
                raise HTTPException(status_code=403, detail=detail) from exc
            raise HTTPException(status_code=404, detail=detail) from exc
        return SessionResponse(
            id=session_entity.id,
            table_id=session_entity.table_id,
            state=session_entity.state.value,
            started_at=session_entity.started_at,
            ended_at=session_entity.ended_at,
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

    @router.post("/audio-tracks", response_model=AudioTrackResponse)
    async def create_audio_track(
        request: CreateAudioTrackRequest,
        auth: AuthContext = Depends(get_auth_context),
        container: Container = Depends(get_container),
    ) -> AudioTrackResponse:
        require_roles(auth, ADMIN_OR_NARRATOR, "create_audio_track")
        track = await container.use_cases.create_audio_track(
            CreateAudioTrackCommand(
                organization_id=auth.organization_id,
                title=request.title,
                s3_key=request.s3_key,
                duration_seconds=request.duration_seconds,
                actor_id=auth.user_id,
            )
        )
        return AudioTrackResponse(
            id=track.id,
            organization_id=track.organization_id,
            title=track.title,
            s3_key=track.s3_key,
            duration_seconds=track.duration_seconds,
        )

    @router.post("/audio-tracks/upload", response_model=AudioTrackResponse)
    async def upload_audio_track(
        title: str = Form(min_length=1, max_length=160),
        duration_seconds: int = Form(gt=0, lt=72000),
        file: UploadFile = File(...),
        auth: AuthContext = Depends(get_auth_context),
        container: Container = Depends(get_container),
    ) -> AudioTrackResponse:
        require_roles(auth, ADMIN_OR_NARRATOR, "upload_audio_track")
        body = await file.read()
        if not body:
            raise HTTPException(status_code=400, detail="empty audio file")
        key = f"{auth.organization_id}/{uuid4()}-{file.filename or 'audio.bin'}"
        content_type = _resolve_upload_audio_mime(file.content_type, file.filename)

        await container.audio_storage.ensure_ready()
        await container.audio_storage.upload(key=key, data=body, content_type=content_type)

        track = await container.use_cases.create_audio_track(
            CreateAudioTrackCommand(
                organization_id=auth.organization_id,
                title=title,
                s3_key=key,
                duration_seconds=duration_seconds,
                actor_id=auth.user_id,
            )
        )
        return AudioTrackResponse(
            id=track.id,
            organization_id=track.organization_id,
            title=track.title,
            s3_key=track.s3_key,
            duration_seconds=track.duration_seconds,
        )

    @router.get("/audio-tracks/{track_id}/stream")
    async def stream_audio_track(
        track_id: str,
        token: str = Query(min_length=10),
        container: Container = Depends(get_container),
    ) -> Response:
        try:
            payload = container.token_service.decode(token)
        except ValueError as exc:
            raise HTTPException(status_code=401, detail="invalid token") from exc
        track = await container.audio_track_repository.get_by_id(track_id)
        if track is None:
            raise HTTPException(status_code=404, detail="track not found")
        if track.organization_id != payload.organization_id:
            raise HTTPException(status_code=403, detail="organization scope mismatch")
        try:
            body, content_type = await container.audio_storage.download(track.s3_key)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail="audio object not found") from exc
        resolved_mime = _resolve_stream_audio_mime(content_type, track.s3_key)
        filename = Path(track.s3_key).name
        return Response(
            content=body,
            media_type=resolved_mime,
            headers={
                "Accept-Ranges": "bytes",
                "Content-Disposition": f'inline; filename="{filename}"',
            },
        )

    @router.get("/audio-tracks", response_model=list[AudioTrackResponse])
    async def list_audio_tracks(
        auth: AuthContext = Depends(get_auth_context),
        container: Container = Depends(get_container),
    ) -> list[AudioTrackResponse]:
        require_roles(auth, READ_AUDIT_ROLES, "list_audio_tracks")
        tracks = await container.audio_track_repository.list_by_organization(auth.organization_id)
        return [
            AudioTrackResponse(
                id=track.id,
                organization_id=track.organization_id,
                title=track.title,
                s3_key=track.s3_key,
                duration_seconds=track.duration_seconds,
            )
            for track in tracks
        ]

    @router.post("/triggers", response_model=TriggerResponse)
    async def create_trigger(
        request: CreateTriggerRequest,
        auth: AuthContext = Depends(get_auth_context),
        container: Container = Depends(get_container),
    ) -> TriggerResponse:
        require_roles(auth, ADMIN_OR_NARRATOR, "create_trigger")
        table = await container.table_repository.get_by_id(request.table_id)
        if table is None:
            raise HTTPException(status_code=404, detail="table not found")
        ensure_same_organization(auth, table.organization_id)
        trigger = await container.use_cases.create_trigger(
            CreateTriggerCommand(
                organization_id=auth.organization_id,
                table_id=request.table_id,
                condition_type=request.condition_type,
                payload=request.payload,
                actor_id=auth.user_id,
            )
        )
        return TriggerResponse(
            id=trigger.id,
            table_id=trigger.table_id,
            condition_type=trigger.condition_type,
            payload=trigger.payload,
        )

    @router.post("/ai-contexts", response_model=AIContextResponse)
    async def generate_ai_context(
        request: GenerateAIContextRequest,
        auth: AuthContext = Depends(get_auth_context),
        container: Container = Depends(get_container),
    ) -> AIContextResponse:
        require_roles(auth, ADMIN_OR_NARRATOR, "generate_ai_context")
        context = await container.use_cases.generate_adaptive_ambience(
            GenerateAdaptiveAmbienceCommand(
                organization_id=auth.organization_id,
                session_id=request.session_id,
                mood=request.mood,
                actor_id=auth.user_id,
            )
        )
        return AIContextResponse(
            id=context.id,
            session_id=context.session_id,
            mood=context.mood,
            recommended_track_tags=context.recommended_track_tags,
        )

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
