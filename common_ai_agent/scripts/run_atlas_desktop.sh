#!/usr/bin/env bash
# run_atlas_desktop.sh - launch the ATLAS Tauri desktop window.
#
# The Tauri shell loads a running ATLAS backend. When --root is supplied, this
# launcher starts a local backend with that root unless a matching backend is
# already serving.
#
# Usage:
#   scripts/run_atlas_desktop.sh --root /path/to/ip-parent --ip NEWIP_MCTP
#   scripts/run_atlas_desktop.sh --backend-url http://127.0.0.1:3000/?ip=NEWIP_MCTP
#   scripts/run_atlas_desktop.sh --prod --root /path/to/ip-parent --ip NEWIP_MCTP
set -euo pipefail

HERE="$(cd "$(dirname "$0")/.." && pwd)"
cd "$HERE"

MODE="dev"
HOST="${ATLAS_DESKTOP_HOST:-127.0.0.1}"
PORT="${ATLAS_DESKTOP_PORT:-3000}"
ROOT="${ATLAS_DESKTOP_ROOT:-}"
ROOT_EXPLICIT=0
if [[ -n "$ROOT" ]]; then
  ROOT_EXPLICIT=1
fi
IP="${ATLAS_DESKTOP_IP:-}"
WORKFLOW="${ATLAS_DESKTOP_WORKFLOW:-default}"
SESSION_ID="${ATLAS_DESKTOP_SESSION_ID:-${USER:-default}}"
BACKEND_URL_RAW="${ATLAS_DESKTOP_BACKEND_URL:-}"
BACKEND_URL_EXPLICIT=0
SCM_PROVIDER="${ATLAS_DESKTOP_SCM_PROVIDER:-${ATLAS_SCM_PROVIDER:-}}"
EXEC_MODE="${ATLAS_DESKTOP_EXEC:-s}"
START_BACKEND="${ATLAS_DESKTOP_START_BACKEND:-auto}"
BACKEND_PID=""

usage() {
  sed -n '2,11p' "$0"
  cat <<'USAGE'

Options:
  --root PATH             IP parent/project root passed to atlas_ui.py --root.
  --ip NAME               Active IP used for URL/session bootstrap.
  --workflow NAME         Active workflow, default: default.
  --session-id NAME       Session owner segment, default: current user.
  --backend-url URL       Existing backend URL to load.
  --backend URL           Alias for --backend-url.
  --host HOST             Local backend host when --root starts a backend.
  --port PORT             Local backend port when --root starts a backend.
  --scm-provider NAME     SCM provider env, e.g. perforce.
  --exec MODE             Backend exec mode, default: s.
  --no-start-backend      Require an already-running backend.
  --prod                  Open the built .app instead of tauri dev.
  -h, --help              Show this help.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --prod)
      MODE="prod"
      shift
      ;;
    --root)
      ROOT="${2:-}"
      ROOT_EXPLICIT=1
      shift 2
      ;;
    --root=*)
      ROOT="${1#*=}"
      ROOT_EXPLICIT=1
      shift
      ;;
    --ip|-ip)
      IP="${2:-}"
      shift 2
      ;;
    --ip=*)
      IP="${1#*=}"
      shift
      ;;
    --workflow|-w)
      WORKFLOW="${2:-}"
      shift 2
      ;;
    --workflow=*|--wf=*)
      WORKFLOW="${1#*=}"
      shift
      ;;
    --session-id|-s|--session)
      SESSION_ID="${2:-}"
      shift 2
      ;;
    --session-id=*|--session=*)
      SESSION_ID="${1#*=}"
      shift
      ;;
    --backend-url|--backend)
      BACKEND_URL_RAW="${2:-}"
      BACKEND_URL_EXPLICIT=1
      shift 2
      ;;
    --backend-url=*|--backend=*)
      BACKEND_URL_RAW="${1#*=}"
      BACKEND_URL_EXPLICIT=1
      shift
      ;;
    --host)
      HOST="${2:-}"
      shift 2
      ;;
    --host=*)
      HOST="${1#*=}"
      shift
      ;;
    --port)
      PORT="${2:-}"
      shift 2
      ;;
    --port=*)
      PORT="${1#*=}"
      shift
      ;;
    --scm-provider)
      SCM_PROVIDER="${2:-}"
      shift 2
      ;;
    --scm-provider=*)
      SCM_PROVIDER="${1#*=}"
      shift
      ;;
    --exec|--exec-mode)
      EXEC_MODE="${2:-}"
      shift 2
      ;;
    --exec=*|--exec-mode=*)
      EXEC_MODE="${1#*=}"
      shift
      ;;
    --no-start-backend)
      START_BACKEND="0"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$BACKEND_URL_RAW" ]]; then
  BACKEND_URL_RAW="http://${HOST}:${PORT}/"
fi

if [[ -z "$ROOT" && "$BACKEND_URL_EXPLICIT" == 0 ]]; then
  ROOT="${ATLAS_ROOT:-${HOME:-}/ATLAS}"
  if [[ -z "$ROOT" || "$ROOT" == "/ATLAS" ]]; then
    echo "HOME is not set; pass --root explicitly." >&2
    exit 1
  fi
  mkdir -p "$ROOT"
fi

if [[ -n "$ROOT" ]]; then
  if [[ ! -d "$ROOT" ]]; then
    echo "backend root not found: $ROOT" >&2
    exit 1
  fi
  ROOT="$(cd "$ROOT" && pwd -P)"
fi

append_query_param() {
  local url="$1"
  local key="$2"
  local value="$3"
  if [[ -z "$value" ]]; then
    printf '%s\n' "$url"
    return
  fi
  python3 - "$url" "$key" "$value" <<'PY'
from __future__ import annotations

import sys
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

raw_url, key, value = sys.argv[1:4]
parts = urlsplit(raw_url)
query = dict(parse_qsl(parts.query, keep_blank_values=True))
query.setdefault(key, value)
print(urlunsplit((parts.scheme, parts.netloc, parts.path or "/", urlencode(query), parts.fragment)))
PY
}

decorate_backend_url() {
  local url="$1"
  url="$(append_query_param "$url" "ip" "$IP")"
  url="$(append_query_param "$url" "workflow" "$WORKFLOW")"
  url="$(append_query_param "$url" "session_id" "$SESSION_ID")"
  if [[ -n "$IP" && -n "$SESSION_ID" && -n "$WORKFLOW" ]]; then
    url="$(append_query_param "$url" "session" "${SESSION_ID}/${IP}/${WORKFLOW}")"
  fi
  url="$(append_query_param "$url" "scm" "$SCM_PROVIDER")"
  printf '%s\n' "$url"
}

backend_base() {
  local url="$1"
  url="${url%%\?*}"
  printf '%s\n' "${url%/}"
}

healthz_project_root() {
  local base="$1"
  curl -fsS -m 2 "$base/healthz" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("project_root", ""))'
}

print_command() {
  local first=1
  for arg in "$@"; do
    if [[ "$first" == 1 ]]; then
      first=0
    else
      printf ' '
    fi
    printf '%q' "$arg"
  done
  printf '\n'
}

backend_command() {
  local -a cmd=(
    env
    "ATLAS_FRONTEND_MODE=${ATLAS_FRONTEND_MODE:-vite}"
  )
  if [[ -n "$ROOT" ]]; then
    cmd+=("ATLAS_ROOT=$ROOT")
  fi
  if [[ -n "$SCM_PROVIDER" ]]; then
    cmd+=("ATLAS_SCM_PROVIDER=$SCM_PROVIDER")
  fi
  if [[ "$SCM_PROVIDER" == "perforce" && -z "${ATLAS_SCM_ADAPTER_PERFORCE:-}" ]]; then
    cmd+=("ATLAS_SCM_ADAPTER_PERFORCE=core.scm_perforce:PerforceP4Adapter")
  fi
  cmd+=(
    python3 src/atlas_ui.py
    --host "$HOST"
    --port "$PORT"
    --root "$ROOT"
    --workflow-root "$HERE"
    --session "$SESSION_ID"
    -ip "${IP:-default}"
    --workflow "$WORKFLOW"
    --exec "$EXEC_MODE"
  )
  print_command "${cmd[@]}"
}

BACKEND_URL="$(decorate_backend_url "$BACKEND_URL_RAW")"

if [[ "${ATLAS_DESKTOP_DRY_RUN:-}" == "1" ]]; then
  echo "backend_url=$BACKEND_URL"
  if [[ -n "$ROOT" ]]; then
    echo -n "backend_command="
    backend_command
  fi
  echo "mode=$MODE"
  exit 0
fi

choose_backend_for_root() {
  local base
  local project_root
  base="$(backend_base "$BACKEND_URL_RAW")"
  if project_root="$(healthz_project_root "$base" 2>/dev/null)"; then
    if [[ -z "$ROOT" || "$project_root" == "$ROOT" ]]; then
      return 0
    fi
    if [[ "$BACKEND_URL_EXPLICIT" == 1 || "$START_BACKEND" == "0" ]]; then
      echo "backend at $base serves $project_root, not --root $ROOT" >&2
      exit 1
    fi
  fi

  if [[ -z "$ROOT" || "$START_BACKEND" == "0" ]]; then
    echo "ATLAS backend not reachable at $base." >&2
    echo "Start one with:" >&2
    echo "  scripts/run_atlas_desktop.sh --root /path/to/ip-parent --ip <ip-name>" >&2
    exit 1
  fi

  for candidate in $(seq "$PORT" "$((PORT + 20))"); do
    local candidate_base="http://${HOST}:${candidate}"
    if ! healthz_project_root "$candidate_base" >/dev/null 2>&1; then
      PORT="$candidate"
      BACKEND_URL_RAW="${candidate_base}/"
      BACKEND_URL="$(decorate_backend_url "$BACKEND_URL_RAW")"
      return 0
    fi
  done

  echo "no free local backend port found from $PORT to $((PORT + 20))" >&2
  exit 1
}

start_backend_if_needed() {
  local base
  local current_root
  base="$(backend_base "$BACKEND_URL_RAW")"
  if current_root="$(healthz_project_root "$base" 2>/dev/null)"; then
    if [[ -z "$ROOT" || "$current_root" == "$ROOT" ]]; then
      return 0
    fi
  fi

  local log_file="${ATLAS_DESKTOP_BACKEND_LOG:-${TMPDIR:-/tmp}/atlas-desktop-backend-${PORT}.log}"
  echo "Starting ATLAS backend at $base with --root $ROOT"
  echo "Backend log: $log_file"
  local -a env_args=("ATLAS_FRONTEND_MODE=${ATLAS_FRONTEND_MODE:-vite}")
  if [[ -n "$SCM_PROVIDER" ]]; then
    env_args+=("ATLAS_SCM_PROVIDER=$SCM_PROVIDER")
  fi
  if [[ -n "$ROOT" ]]; then
    env_args+=("ATLAS_ROOT=$ROOT")
  fi
  if [[ "$SCM_PROVIDER" == "perforce" && -z "${ATLAS_SCM_ADAPTER_PERFORCE:-}" ]]; then
    env_args+=("ATLAS_SCM_ADAPTER_PERFORCE=core.scm_perforce:PerforceP4Adapter")
  fi
  env "${env_args[@]}" \
    python3 src/atlas_ui.py \
      --host "$HOST" \
      --port "$PORT" \
      --root "$ROOT" \
      --workflow-root "$HERE" \
      --session "$SESSION_ID" \
      -ip "${IP:-default}" \
      --workflow "$WORKFLOW" \
      --exec "$EXEC_MODE" \
      >"$log_file" 2>&1 &
  BACKEND_PID="$!"
  trap '[[ -n "$BACKEND_PID" ]] && kill "$BACKEND_PID" 2>/dev/null || true' EXIT

  for _ in $(seq 1 60); do
    if healthz_project_root "$base" >/dev/null 2>&1; then
      return 0
    fi
    sleep 0.5
  done
  echo "backend did not become ready; see $log_file" >&2
  exit 1
}

choose_backend_for_root
start_backend_if_needed

if [[ "$MODE" == "prod" ]]; then
  APP="src-tauri/target/release/bundle/macos/ATLAS.app"
  BIN="$APP/Contents/MacOS/atlas-desktop"
  if [[ ! -x "$BIN" ]]; then
    echo "built app not found at $APP - run a release build first:" >&2
    echo "  frontend/atlas/node_modules/.bin/tauri build" >&2
    exit 1
  fi
  echo "Opening $APP -> $BACKEND_URL"
  env ATLAS_DESKTOP_BACKEND_URL="$BACKEND_URL" "$BIN" --backend-url "$BACKEND_URL"
  exit $?
fi

TAURI="frontend/atlas/node_modules/.bin/tauri"
if [[ ! -x "$TAURI" ]]; then
  echo "Tauri CLI not installed." >&2
  echo "Run: (cd frontend/atlas && npm install -D @tauri-apps/cli@^2 @tauri-apps/api@^2)" >&2
  exit 1
fi

echo "Launching ATLAS desktop (tauri dev) -> $BACKEND_URL"
env ATLAS_DESKTOP_BACKEND_URL="$BACKEND_URL" "$TAURI" dev
