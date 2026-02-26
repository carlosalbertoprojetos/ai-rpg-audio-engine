#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8010}"
ORG="${ORG:-org-demo}"
EMAIL="${EMAIL:-gm@demo.com}"
PASSWORD="${PASSWORD:-StrongPass123}"

echo "Register..."
curl -s -X POST "$BASE_URL/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"display_name\":\"GM\",\"password\":\"$PASSWORD\",\"organization_id\":\"$ORG\",\"role\":\"admin\"}" >/dev/null || true

echo "Token..."
TOKEN="$(curl -s -X POST "$BASE_URL/api/v1/auth/token" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\",\"organization_id\":\"$ORG\"}" | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")"

echo "Create table..."
TABLE_ID="$(curl -s -X POST "$BASE_URL/api/v1/tables" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"name":"Mesa Bash"}' | python -c "import sys,json; print(json.load(sys.stdin)['id'])")"
echo "TableId: $TABLE_ID"

echo "Add player..."
PLAYER_ID="$(curl -s -X POST "$BASE_URL/api/v1/tables/$TABLE_ID/players" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"display_name":"Luna"}' | python -c "import sys,json; print(json.load(sys.stdin)['id'])")"
echo "PlayerId: $PLAYER_ID"

echo "Set player unavailable..."
curl -s -X PATCH "$BASE_URL/api/v1/tables/$TABLE_ID/players/$PLAYER_ID" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"availability":"red"}' >/dev/null

echo "Schedule sound event..."
EXECUTE_AT="$(python -c "import datetime; print((datetime.datetime.utcnow() + datetime.timedelta(seconds=2)).isoformat() + 'Z')")"
curl -s -X POST "$BASE_URL/api/v1/sound-events" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"table_id\":\"$TABLE_ID\",\"session_id\":\"session-bash\",\"action\":\"play:battle\",\"execute_at\":\"$EXECUTE_AT\"}" >/dev/null

echo "Audit (first 5):"
curl -s "$BASE_URL/api/v1/audit/$ORG" -H "Authorization: Bearer $TOKEN" | python - <<'PY'
import sys, json
items = json.load(sys.stdin)
print(json.dumps(items[:5], indent=2))
PY

echo "Done."

