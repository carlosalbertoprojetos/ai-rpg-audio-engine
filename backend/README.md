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

## Runtime modes

- `REPOSITORY_MODE=in_memory|postgres`
- `EVENT_BUS_MODE=in_memory|redis`

## Test & Lint

```bash
pytest -q
ruff check app tests
```
