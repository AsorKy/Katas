#!/usr/bin/env bash
# Recorre el flujo completo contra una API ya levantada.
# Uso: ./scripts/smoke.sh            (usa http://localhost:8000)
#      BASE=http://localhost:9000 ./scripts/smoke.sh
set -euo pipefail

BASE="${BASE:-http://localhost:8000}"
EMAIL="smoke-$(date +%s)@example.com"
PASSWORD="smoke-password-123"
JSON='Content-Type: application/json'

paso() { echo "ok  $1"; }
falla() { echo "FALLO en '$1': esperaba $2 y llegó $3"; exit 1; }

# status <método> <ruta> <esperado> <paso> [json] [token]  -> deja el cuerpo en $BODY
status() {
  local method=$1 path=$2 esperado=$3 nombre=$4 data=${5:-} token=${6:-}
  local args=(-s -w '\n%{http_code}' -X "$method" "$BASE$path")
  [ -n "$data" ]  && args+=(-H "$JSON" -d "$data")
  [ -n "$token" ] && args+=(-H "Authorization: Bearer $token")
  local out; out=$(curl "${args[@]}")
  local code=${out##*$'\n'}
  BODY=${out%$'\n'*}
  [ "$code" = "$esperado" ] || { echo "$BODY"; falla "$nombre" "$esperado" "$code"; }
  paso "$nombre ($code)"
}

campo() { sed -E "s/.*\"$1\":\"?([^\",}]+)\"?.*/\1/" <<<"$BODY"; }

status GET  /health          200 "health"
status POST /auth/register   201 "registro"       "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}"
status POST /auth/login      200 "login"          "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}"
TOKEN=$(campo access_token)

status GET  /me              200 "me"             "" "$TOKEN"
status POST /songs           201 "crear canción"  "{\"title\":\"Smoke $(date +%s)\",\"duration_s\":200,\"genre_id\":1,\"artists\":[{\"artist_id\":1,\"role\":\"main\"}]}" "$TOKEN"
SONG_ID=$(campo id)

status POST /playlists       201 "crear playlist" '{"name":"smoke"}' "$TOKEN"
PLAYLIST_ID=$(campo id)

status POST "/playlists/$PLAYLIST_ID/songs" 201 "añadir canción" "{\"song_id\":$SONG_ID}" "$TOKEN"
status GET  "/playlists/$PLAYLIST_ID"       200 "leer playlist" "" "$TOKEN"

echo "TODO OK: el flujo completo funciona contra $BASE"
