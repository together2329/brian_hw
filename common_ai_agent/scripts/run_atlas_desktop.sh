#!/usr/bin/env bash
# run_atlas_desktop.sh — launch the ATLAS Tauri desktop window (dev mode).
#
# The Tauri shell is a native window that loads the RUNNING ATLAS backend
# (http://localhost:3000). So the backend must already be serving on :3000.
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

# The window loads localhost:3000 — the backend must be up.
if ! curl -fsS -m 3 http://127.0.0.1:3000/healthz >/dev/null 2>&1; then
  echo "⚠ ATLAS backend not reachable on http://localhost:3000."
  echo "  Start it first in another shell. To show the NEW Vite frontend (and gpt-5.5):"
  echo "    ATLAS_FRONTEND_MODE=vite <your atlas server launch command> --model gpt-5.5"
  echo "  (USE_OPENCODE_OAUTH=true in .config is needed for gpt — see doc/wiki/worker-model-gpt-switch.md)"
  echo "  Then re-run this script."
  exit 1
fi

if [[ "${1:-}" == "--prod" ]]; then
  APP="src-tauri/target/release/bundle/macos/ATLAS.app"
  if [[ -d "$APP" ]]; then
    echo "Opening $APP"
    exec open "$APP"
  fi
  echo "✗ Built app not found at $APP — run a release build first:  $TAURI build"
  exit 1
fi

echo "Launching ATLAS desktop (tauri dev) → http://localhost:3000 …"
exec "$TAURI" dev
