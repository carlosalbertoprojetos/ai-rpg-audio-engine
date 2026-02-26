# RPGSoundDesk

Plataforma SaaS de mesa de som para RPG online com IA adaptativa, arquitetura DDD + Clean Architecture.

## Estrutura

- `docs/architecture.md`: Fase 1 completa (analise, arquitetura, validacao e estrategia)
- `backend/`: FastAPI + WebSocket + camadas DDD/Clean + testes
- `frontend/`: React + cliente WebSocket + UI de mesa de som com LEDs
- `docker-compose.yml`: PostgreSQL, Redis, MinIO, backend e frontend
- `.github/workflows/ci.yml`: pipeline de lint/test/build

## Subir stack local

```bash
docker compose up --build
```

Frontend: `http://localhost:5173`  
Backend: `http://localhost:8000/api/v1/health`

## Backend local (sem Docker)

```bash
cd backend
pip install -e .[dev]
uvicorn app.main:app --reload
```

Variaveis principais:
- `REPOSITORY_MODE=in_memory|postgres`
- `EVENT_BUS_MODE=in_memory|redis`
- `JWT_SECRET=<segredo forte>`

## Frontend local (sem Docker)

```bash
cd frontend
npm install
npm run dev
```

## Qualidade

```bash
cd backend && ruff check app tests && pytest -q
cd frontend && npm run lint && npm run build
```

## Autenticacao (JWT + RBAC)

1. `POST /api/v1/auth/register`
2. `POST /api/v1/auth/token`
3. Usar `Authorization: Bearer <token>` nas rotas protegidas
4. WebSocket de mesa: `/api/v1/ws/tables/{table_id}?token=<token>`
