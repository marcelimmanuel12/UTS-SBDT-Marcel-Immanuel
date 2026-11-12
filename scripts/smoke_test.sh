#!/usr/bin/env bash
set -euo pipefail
BASE_URL="${BASE_URL:-http://localhost:8000}"
AUTH_URL="${AUTH_URL:-http://localhost:8080/realms/sbdt/protocol/openid-connect/token}"
command -v curl >/dev/null
command -v python3 >/dev/null
printf '1. Pemeriksaan health...\n'
curl -fsS "$BASE_URL/health"
printf '\n2. Mengambil JWT demo Keycloak...\n'
RESPONSE=$(curl -fsS --retry 10 --retry-delay 3 --retry-connrefused \
  -d grant_type=password -d client_id=sbdt-cli -d username=marcel \
  --data-urlencode 'password=Demo12345!' "$AUTH_URL")
TOKEN=$(printf '%s' "$RESPONSE" | python3 -c 'import json,sys; print(json.load(sys.stdin)["access_token"])')
printf '3. POST prediksi (WRITE => Primary)...\n'
curl -fsSi -X POST "$BASE_URL/predict" \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"transaction_amount":12500000,"transactions_24h":9,"new_device":true}'
printf '\n4. GET riwayat (READ => Replica; bisa ada jeda replikasi)...\n'
sleep 3
curl -fsSi "$BASE_URL/inferences" -H "Authorization: Bearer $TOKEN"
printf '\n5. Periksa role database...\n'
curl -fsS "$BASE_URL/health/database" -H "Authorization: Bearer $TOKEN"
printf '\n'
