from fastapi.testclient import TestClient

from backend.main import create_app


def test_generate_audio_endpoint_creates_scene_and_audio_file() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.post(
        "/api/generate-audio",
        json={"prompt": "Medieval forest ambience with distant battle", "output_format": "wav"},
    )
    assert response.status_code == 200
    payload = response.json()

    assert payload["scene_id"]
    assert payload["audio_url"].startswith("/api/audio/")
    assert payload["layers"]

    audio_response = client.get(payload["audio_url"])
    assert audio_response.status_code == 200
    assert audio_response.headers["content-type"].startswith("audio/")
    assert len(audio_response.content) > 200


def test_generate_audio_uses_cache_for_same_request() -> None:
    app = create_app()
    client = TestClient(app)
    body = {"prompt": "Epic cinematic battle music", "output_format": "wav"}

    first = client.post("/api/generate-audio", json=body)
    second = client.post("/api/generate-audio", json=body)

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["cached"] is True
