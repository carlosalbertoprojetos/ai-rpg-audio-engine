# Audio Orchestrator SaaS

Intelligent SaaS audio orchestration backend and frontend modules.

## What it does

- Parses semantic scene prompts
- Builds layered scene composition
- Selects retrieval/generation providers with fallbacks
- Validates licenses for SaaS distribution
- Mixes layers and exports audio (`wav`, `mp3`, `ogg`)
- Caches generated scenes with Redis (fallback in-memory)
- Persists request/scene/provider logs in SQLite

## API

- `POST /api/generate-audio`
- `GET /api/audio/{file_name}`
- `GET /api/health`

### Example request

```json
{
  "prompt": "distant battle with wind",
  "output_format": "wav"
}
```

### Example response

```json
{
  "scene_id": "...",
  "audio_url": "/api/audio/scene-....wav",
  "output_format": "wav",
  "cached": false,
  "layers": []
}
```

## Local run

```bash
cd audio-orchestrator-saas
python -m pip install -r requirements.txt
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8090
```

## Docker

```bash
cd audio-orchestrator-saas/infra/docker
docker compose up --build
```

## Tests

```bash
cd audio-orchestrator-saas
pytest backend/tests -q
```
