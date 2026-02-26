# Tutorial 05 - API Rapida (curl)

Objetivo: executar o fluxo principal via API (sem UI).

Assumindo backend em `http://localhost:8010` e org `org-demo`.

## 1) Registrar usuario

```bash
curl -s -X POST http://localhost:8010/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"gm@demo.com","display_name":"GM","password":"StrongPass123","organization_id":"org-demo","role":"admin"}'
```

## 2) Login e obter token

```bash
TOKEN=$(curl -s -X POST http://localhost:8010/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"email":"gm@demo.com","password":"StrongPass123","organization_id":"org-demo"}' | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
echo $TOKEN
```

## 3) Criar mesa

```bash
TABLE_ID=$(curl -s -X POST http://localhost:8010/api/v1/tables \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name":"Mesa API"}' | python -c "import sys,json; print(json.load(sys.stdin)['id'])")
echo $TABLE_ID
```

## 4) Adicionar jogador

```bash
curl -s -X POST http://localhost:8010/api/v1/tables/$TABLE_ID/players \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"display_name":"Nox"}'
```

## 5) Atualizar disponibilidade (LED)

```bash
PLAYER_ID=$(curl -s -X POST http://localhost:8010/api/v1/tables/$TABLE_ID/players \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"display_name":"Luna"}' | python -c "import sys,json; print(json.load(sys.stdin)['id'])")

curl -s -X PATCH http://localhost:8010/api/v1/tables/$TABLE_ID/players/$PLAYER_ID \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"availability":"red"}'
```

## 6) Agendar evento sonoro

```bash
python - <<'PY'
import datetime
print((datetime.datetime.utcnow() + datetime.timedelta(seconds=2)).isoformat() + "Z")
PY
```

```bash
EXECUTE_AT="(cole aqui o timestamp acima)"
curl -s -X POST http://localhost:8010/api/v1/sound-events \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"table_id\":\"$TABLE_ID\",\"session_id\":\"session-1\",\"action\":\"play:battle\",\"execute_at\":\"$EXECUTE_AT\"}"
```

## 7) Ver auditoria

```bash
curl -s http://localhost:8010/api/v1/audit/org-demo -H "Authorization: Bearer $TOKEN"
```

