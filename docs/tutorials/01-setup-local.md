# Tutorial 01 - Setup Local

Objetivo: subir backend e frontend localmente para a primeira execucao.

## Opcao A: Docker Compose (recomendado)

Na raiz do repo:

```bash
docker compose up --build
```

URLs:
- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000/api/v1/health`

## Opcao B: Sem Docker (Windows)

### Backend

No Git Bash ou PowerShell:

```bash
cd backend
py -3 -m venv .venv
source .venv/Scripts/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8010
```

### Frontend

Em outro terminal, a partir da raiz do repo:

```bash
cd frontend
npm install
VITE_API_BASE_URL=http://localhost:8010/api/v1 VITE_WS_BASE_URL=ws://localhost:8010 npm run dev
```

Frontend: `http://localhost:5173`

## Checklist de sucesso

- `GET /api/v1/health` retorna `{"status":"ok"}`
- Frontend abre e mostra status WS (vai ficar offline ate voce autenticar e criar mesa)

