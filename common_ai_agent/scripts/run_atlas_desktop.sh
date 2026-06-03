#!/usr/bin/env bash
# run_atlas_desktop.sh — launch the ATLAS Tauri desktop window (dev mode).
#
# The Tauri shell is a native window that loads the RUNNING ATLAS backend.
# Set ATLAS_DESKTOP_BACKEND_URL to choose a backend, for example:
#   ATLAS_DESKTOP_BACKEND_URL='http://127.0.0.1:3000/?ip=NEWIP_MCTP'
# Set ATLAS_DESKTOP_IP to append ?ip=<value> when the URL has no query.
# The backend must already be serving.
# See doc/wiki/tauri-desktop-shell.md for the architecture (Option A).
#
# Usage:
#   scripts/run_atlas_desktop.sh            # tauri dev (rebuilds shell, opens window)
#   scripts/run_atlas_desktop.sh --prod     # open the built .app (after `tauri build`)
set -euo pipefail

HERE="$(cd "$(dirname "$0")/.." && pwd)"   # common_ai_agent/
cd "$HERE"

TAURI="frontend/atlas/node_modules/.bin/tauri"
if [[ ! -x "$TAURI" ]]; then
  echo "✗ Tauri CLI not installed."
  echo "  Run: (cd frontend/atlas && npm install -D @tauri-apps/cli@^2 @tauri-apps/api@^2)"
  exit 1
fi

BACKEND_URL="${ATLAS_DESKTOP_BACKEND_URL:-http://localhost:3000/}"
if [[ -n "${ATLAS_DESKTOP_IP:-}" && "$BACKEND_URL" != *"?"* ]]; then
  BACKEND_URL="${BACKEND_URL%/}/?ip=${ATLAS_DESKTOP_IP}"
fi
BACKEND_BASE="${BACKEND_URL%%\?*}"
BACKEND_BASE="${BACKEND_BASE%/}"

# The window loads BACKEND_URL — the backend must be up.
if ! curl -fsS -m 3 "$BACKEND_BASE/healthz" >/dev/null 2>&1; then
  echo "⚠ ATLAS backend not reachable at $BACKEND_BASE."
  echo "  Start it first in another shell. For the desktop artifact root:"
  echo "    ATLAS_FRONTEND_MODE=vite ATLAS_SCM_PROVIDER=perforce \\"
  echo "      ATLAS_SCM_ADAPTER_PERFORCE=core.scm_perforce:PerforceP4Adapter \\"
  echo "      python3 src/atlas_ui.py --host 127.0.0.1 --port 3000 \\"
  echo "      --root /Users/brian/Desktop/Project/ROOT_IP"
  echo "  (USE_OPENCODE_OAUTH=true in .config is needed for gpt — see doc/wiki/worker-model-gpt-switch.md)"
  echo "  Then re-run this script."
  exit 1
fi

if [[ "${1:-}" == "--prod" ]]; then
  APP="src-tauri/target/release/bundle/macos/ATLAS.app"
  if [[ -d "$APP" ]]; then
    BIN="$APP/Contents/MacOS/atlas-desktop"
    echo "Opening $APP → $BACKEND_URL"
    exec env ATLAS_DESKTOP_BACKEND_URL="$BACKEND_URL" "$BIN" --backend-url "$BACKEND_URL"
  fi
  echo "✗ Built app not found at $APP — run a release build first:  $TAURI build"
  exit 1
fi

echo "Launching ATLAS desktop (tauri dev) → $BACKEND_URL …"
exec env ATLAS_DESKTOP_BACKEND_URL="$BACKEND_URL" "$TAURI" dev
