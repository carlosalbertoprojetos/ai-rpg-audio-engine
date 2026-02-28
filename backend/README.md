# RPGSoundDesk Backend

## Run

```bash
pip install -e .[dev]
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Auth flow

1. `POST /api/v1/auth/register`
2. `POST /api/v1/auth/token`
3. Send `Authorization: Bearer <token>` on protected routes
4. WebSocket: `/api/v1/ws/tables/{table_id}?token=<token>`

## Enterprise endpoints

- Organization/Subscription:
  - `GET /api/v1/organizations/{organization_id}`
  - `PATCH /api/v1/organizations/{organization_id}/subscription`
- Sessions:
  - `POST /api/v1/sessions`
  - `POST /api/v1/sessions/{session_id}/end`
- Audio/Triggers/AI:
  - `POST /api/v1/audio-tracks`
  - `GET /api/v1/audio-tracks`
  - `POST /api/v1/triggers`
  - `POST /api/v1/ai-contexts`

## Runtime modes

- `REPOSITORY_MODE=in_memory|postgres`
- `EVENT_BUS_MODE=in_memory|redis`

## Test & Lint

```bash
pytest -q
ruff check app tests
```
