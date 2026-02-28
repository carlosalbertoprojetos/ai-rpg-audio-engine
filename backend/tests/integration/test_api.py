import json
import time
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def _build_client() -> TestClient:
    settings = Settings(
        repository_mode="in_memory",
        event_bus_mode="in_memory",
        jwt_secret="test-secret-with-at-least-32-bytes",
        sound_event_poll_interval_seconds=0.1,
    )
    app = create_app(settings=settings)
    return TestClient(app)


def _bootstrap_auth(client: TestClient) -> str:
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "gm@tests.com",
            "display_name": "GM",
            "password": "StrongPass123",
            "organization_id": "org-1",
            "role": "admin",
        },
    )
    assert register_response.status_code == 200

    token_response = client.post(
        "/api/v1/auth/token",
        json={
            "email": "gm@tests.com",
            "password": "StrongPass123",
            "organization_id": "org-1",
        },
    )
    assert token_response.status_code == 200
    return token_response.json()["access_token"]

def _bootstrap_observer_token(client: TestClient) -> str:
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "obs@tests.com",
            "display_name": "Observer",
            "password": "StrongPass123",
            "organization_id": "org-1",
            "role": "observer",
        },
    )
    assert register_response.status_code == 200

    token_response = client.post(
        "/api/v1/auth/token",
        json={
            "email": "obs@tests.com",
            "password": "StrongPass123",
            "organization_id": "org-1",
        },
    )
    assert token_response.status_code == 200
    return token_response.json()["access_token"]


def test_create_table_and_update_player() -> None:
    with _build_client() as client:
        token = _bootstrap_auth(client)
        headers = {"Authorization": f"Bearer {token}"}

        table_response = client.post(
            "/api/v1/tables",
            json={"name": "Mesa Lunar"},
            headers=headers,
        )
        assert table_response.status_code == 200
        table_id = table_response.json()["id"]

        player_response = client.post(
            f"/api/v1/tables/{table_id}/players",
            json={"display_name": "Nox"},
            headers=headers,
        )
        assert player_response.status_code == 200
        player_id = player_response.json()["id"]

        update_response = client.patch(
            f"/api/v1/tables/{table_id}/players/{player_id}",
            json={"availability": "red"},
            headers=headers,
        )
        assert update_response.status_code == 200
        assert update_response.json()["availability"] == "red"


def test_websocket_receives_scheduled_event_execution() -> None:
    with _build_client() as client:
        token = _bootstrap_auth(client)
        headers = {"Authorization": f"Bearer {token}"}

        table_response = client.post(
            "/api/v1/tables",
            json={"name": "Mesa Arcana"},
            headers=headers,
        )
        assert table_response.status_code == 200
        table_id = table_response.json()["id"]

        execute_at = (datetime.now(UTC) + timedelta(milliseconds=250)).isoformat()
        schedule_response = client.post(
            "/api/v1/sound-events",
            json={
                "table_id": table_id,
                "session_id": "session-1",
                "action": "play:battle",
                "execute_at": execute_at,
            },
            headers=headers,
        )
        assert schedule_response.status_code == 200

        with client.websocket_connect(f"/api/v1/ws/tables/{table_id}?token={token}") as websocket:
            found_executed = False
            deadline = time.time() + 3
            while time.time() < deadline and not found_executed:
                payload = json.loads(websocket.receive_text())
                if payload["event_type"] == "sound.event.executed":
                    found_executed = True

            assert found_executed is True


def test_observer_cannot_create_table() -> None:
    with _build_client() as client:
        token = _bootstrap_observer_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.post("/api/v1/tables", json={"name": "Mesa Bloqueada"}, headers=headers)
        assert response.status_code == 403


def test_invalid_token_is_rejected() -> None:
    with _build_client() as client:
        headers = {"Authorization": "Bearer invalid.token.value"}
        response = client.post("/api/v1/tables", json={"name": "Mesa"}, headers=headers)
        assert response.status_code == 401


def test_organization_scope_mismatch_denies_sound_event() -> None:
    with _build_client() as client:
        token_org1 = _bootstrap_auth(client)
        headers_org1 = {"Authorization": f"Bearer {token_org1}"}

        table_response = client.post(
            "/api/v1/tables",
            json={"name": "Mesa Org1"},
            headers=headers_org1,
        )
        assert table_response.status_code == 200
        table_id = table_response.json()["id"]

        register_org2 = client.post(
            "/api/v1/auth/register",
            json={
                "email": "gm2@tests.com",
                "display_name": "GM2",
                "password": "StrongPass123",
                "organization_id": "org-2",
                "role": "admin",
            },
        )
        assert register_org2.status_code == 200
        token_org2 = client.post(
            "/api/v1/auth/token",
            json={
                "email": "gm2@tests.com",
                "password": "StrongPass123",
                "organization_id": "org-2",
            },
        )
        assert token_org2.status_code == 200
        headers_org2 = {"Authorization": f"Bearer {token_org2.json()['access_token']}"}

        execute_at = (datetime.now(UTC) + timedelta(milliseconds=250)).isoformat()
        response = client.post(
            "/api/v1/sound-events",
            json={
                "table_id": table_id,
                "session_id": "session-2",
                "action": "play:forest",
                "execute_at": execute_at,
            },
            headers=headers_org2,
        )
        assert response.status_code == 403


def test_admin_can_list_users_and_edit_user() -> None:
    with _build_client() as client:
        token = _bootstrap_auth(client)
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/api/v1/users", headers=headers)
        assert response.status_code == 200
        users = response.json()
        assert len(users) >= 1

        user_id = users[0]["user_id"]
        patch = client.patch(
            f"/api/v1/users/{user_id}",
            json={"display_name": "GM Edited", "role": "narrator"},
            headers=headers,
        )
        assert patch.status_code == 200
        assert patch.json()["display_name"] == "GM Edited"
        assert patch.json()["role"] == "narrator"


def test_observer_cannot_list_users() -> None:
    with _build_client() as client:
        token = _bootstrap_observer_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/api/v1/users", headers=headers)
        assert response.status_code == 403


def test_session_lifecycle_and_enterprise_audio_features() -> None:
    with _build_client() as client:
        token = _bootstrap_auth(client)
        headers = {"Authorization": f"Bearer {token}"}

        table_response = client.post(
            "/api/v1/tables",
            json={"name": "Mesa Enterprise"},
            headers=headers,
        )
        assert table_response.status_code == 200
        table_id = table_response.json()["id"]

        start_session = client.post(
            "/api/v1/sessions",
            json={"table_id": table_id},
            headers=headers,
        )
        assert start_session.status_code == 200
        session_id = start_session.json()["id"]
        assert start_session.json()["state"] == "running"

        create_track = client.post(
            "/api/v1/audio-tracks",
            json={"title": "Track 1", "s3_key": "org-demo/track1.mp3", "duration_seconds": 180},
            headers=headers,
        )
        assert create_track.status_code == 200

        list_tracks = client.get("/api/v1/audio-tracks", headers=headers)
        assert list_tracks.status_code == 200
        assert len(list_tracks.json()) >= 1

        create_trigger = client.post(
            "/api/v1/triggers",
            json={
                "table_id": table_id,
                "condition_type": "scene_change",
                "payload": {"scene": "battle"},
            },
            headers=headers,
        )
        assert create_trigger.status_code == 200

        ai_context = client.post(
            "/api/v1/ai-contexts",
            json={"session_id": session_id, "mood": "battle"},
            headers=headers,
        )
        assert ai_context.status_code == 200
        assert "combat" in ai_context.json()["recommended_track_tags"]

        end_session = client.post(f"/api/v1/sessions/{session_id}/end", headers=headers)
        assert end_session.status_code == 200
        assert end_session.json()["state"] == "finished"


def test_subscription_update_flow() -> None:
    with _build_client() as client:
        token = _bootstrap_auth(client)
        headers = {"Authorization": f"Bearer {token}"}

        get_org = client.get("/api/v1/organizations/org-1", headers=headers)
        assert get_org.status_code == 200
        assert get_org.json()["subscription_plan"] == "starter"

        update_plan = client.patch(
            "/api/v1/organizations/org-1/subscription",
            json={"plan": "pro"},
            headers=headers,
        )
        assert update_plan.status_code == 200
        assert update_plan.json()["subscription_plan"] == "pro"
