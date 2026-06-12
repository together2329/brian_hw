# Free the server ports before (re)building so a re-run never hits "address already in use".
# This file is commonly sourced from zsh, so keep PID handling line-oriented.
_atlas_abort() {
  return "$1" 2>/dev/null || exit "$1"
}

_atlas_port_listeners() {
  lsof -nP -iTCP:"$1" -sTCP:LISTEN -t 2>/dev/null || true
}

_atlas_wait_port_free() {
  port="$1"
  tries=20
  while [ "$tries" -gt 0 ]; do
    if [ -z "$(_atlas_port_listeners "$port")" ]; then
      return 0
    fi
    sleep 0.1
    tries=$((tries - 1))
  done
  return 1
}

for port in 3000 3002; do
  pids="$(_atlas_port_listeners "$port")"
  if [ -n "$pids" ]; then
    echo "Killing LISTEN process(es) on port $port:"
    printf '%s\n' "$pids" | while IFS= read -r pid; do
      [ -n "$pid" ] || continue
      echo "  $pid"
      kill -9 "$pid" 2>/dev/null || true
    done
    if ! _atlas_wait_port_free "$port"; then
      echo "ATLAS UI: port $port is still in use on 127.0.0.1." >&2
      lsof -nP -iTCP:"$port" -sTCP:LISTEN >&2 || true
      _atlas_abort 1
    fi
  fi
done

cd frontend/atlas || _atlas_abort 1
npm run build || _atlas_abort 1
cd ../../ || _atlas_abort 1
python3 src/atlas_ui.py --root /Users/brian/Desktop/Project/NEW_WORKSPACE  --workflow-root /Users/brian/Desktop/Project/brian_hw/common_ai_agent/workflow --port 3000 --admin 3002 --exec s
