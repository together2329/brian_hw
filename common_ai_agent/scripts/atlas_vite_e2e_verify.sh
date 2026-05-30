#!/usr/bin/env bash
# ATLAS vite frontend — one-shot end-to-end verification.
#
# Builds the vite dist, runs tsc + vitest, starts the ATLAS server on a TEST
# port (NOT 3000 — leaves your running app alone), then drives a REAL headless
# Chromium through render -> auth -> workspace -> "hi" -> /ws/agent response
# handshake (scripts/atlas_vite_e2e.mjs). Exits 0 only if everything passes.
#
# Usage:
#   scripts/atlas_vite_e2e_verify.sh
#   ATLAS_E2E_PORT=3025 PYTHON=python3 scripts/atlas_vite_e2e_verify.sh
#
# Env: ATLAS_E2E_PORT (3019), PYTHON (python3), ATLAS_ADMIN_USER/PASS (admin/1151),
#      ATLAS_COOKIE_FILE (/tmp/atlas_cookie), SKIP_VITEST=1 to skip the unit suite.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # .../common_ai_agent
FE="$ROOT/frontend/atlas"
PORT="${ATLAS_E2E_PORT:-3019}"
PY="${PYTHON:-python3}"
export ATLAS_E2E_BASE="http://127.0.0.1:$PORT"
export ATLAS_E2E_SHOTS="${ATLAS_E2E_SHOTS:-/tmp/atlas_e2e_shots}"
SRV_LOG="/tmp/atlas_e2e_server_${PORT}.log"

pass=0; fail=0
ok(){   printf '  \033[32m✓\033[0m %s\n' "$1"; pass=$((pass+1)); }
bad(){  printf '  \033[31m✗\033[0m %s\n' "$1"; fail=$((fail+1)); }
step(){ printf '\n=== %s ===\n' "$1"; }

SRV=""
cleanup(){
  [ -n "$SRV" ] && kill "$SRV" 2>/dev/null
  # also reap anything left on the test port
  lsof -nP -iTCP:"$PORT" -sTCP:LISTEN -t 2>/dev/null | xargs -r kill 2>/dev/null
}
trap cleanup EXIT

cd "$FE" || { echo "no $FE"; exit 2; }

step "1/5  tsc --noEmit (type check)"
if npx tsc --noEmit; then ok "tsc: 0 errors"; else bad "tsc: errors"; fi

if [ "${SKIP_VITEST:-0}" = "1" ]; then
  step "2/5  vitest (skipped via SKIP_VITEST=1)"
else
  step "2/5  vitest run (unit/render smoke)"
  if npx vitest run; then ok "vitest: green"; else bad "vitest: failures"; fi
fi

step "3/5  vite build (dist)"
if npm run build; then ok "build: OK (dist refreshed)"; else bad "build: FAILED"; echo "  -> aborting (no dist to serve)"; exit 1; fi

step "4/5  start ATLAS server on :$PORT (ATLAS_FRONTEND_MODE=vite)"
lsof -nP -iTCP:"$PORT" -sTCP:LISTEN -t 2>/dev/null | xargs -r kill 2>/dev/null
( cd "$ROOT" && ATLAS_FRONTEND_MODE=vite "$PY" src/atlas_ui.py --port "$PORT" >"$SRV_LOG" 2>&1 ) &
SRV=$!
up=0
for _ in $(seq 1 45); do
  if curl -s -o /dev/null --max-time 2 "http://127.0.0.1:$PORT/healthz"; then up=1; break; fi
  sleep 1
done
if [ "$up" = "1" ]; then ok "server up (log: $SRV_LOG)"; else bad "server did not listen — see $SRV_LOG"; exit 1; fi

step "5/5  headless-browser e2e (render + auth + workspace + 'hi' -> /ws/agent)"
if ! node -e "require.resolve('playwright')" >/dev/null 2>&1; then
  echo "  playwright not found — installing (npm i -D playwright + chromium)…"
  npm i -D playwright >/dev/null 2>&1 && npx playwright install chromium >/dev/null 2>&1 \
    || echo "  (playwright install failed — install manually: npm i -D playwright && npx playwright install chromium)"
fi
if node "$ROOT/scripts/atlas_vite_e2e.mjs"; then ok "e2e: PASS (render+workspace+chat handshake)"; else bad "e2e: FAIL (see reason above; shots in $ATLAS_E2E_SHOTS)"; fi

printf '\n===== RESULT: %d passed, %d failed =====\n' "$pass" "$fail"
if [ "$fail" -eq 0 ]; then printf '\033[32mATLAS vite E2E: ✅ VERIFIED\033[0m\n'; else printf '\033[31mATLAS vite E2E: ❌ NOT verified — see above\033[0m\n'; fi
exit "$fail"
