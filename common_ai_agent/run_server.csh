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

# Kill stray ATLAS server processes by their exact invocation. The admin runs
# as a SUBPROCESS (src/atlas_runtime_run.py:_launch_admin_server) and can be
# orphaned or mid-restart — bound to :3002 but not yet/anymore in LISTEN state,
# so the port-listener sweep below misses it and the next start hits
# "address already in use" on :3002. Matching ' --port' (always present in the
# real invocations) avoids killing an editor that merely has the file open.
_atlas_kill_stray_servers() {
  for pat in 'atlas_admin.py --port' 'atlas_ui.py --port'; do
    spids="$(pgrep -f "$pat" 2>/dev/null || true)"
    [ -n "$spids" ] || continue
    echo "Killing stray ATLAS process(es) matching '$pat':"
    printf '%s\n' "$spids" | while IFS= read -r pid; do
      [ -n "$pid" ] || continue
      echo "  $pid"
      kill -9 "$pid" 2>/dev/null || true
    done
  done
}

# Clear both server ports: kill stray server processes, then any remaining
# LISTEN holders, then verify the ports are actually free (abort if not).
_atlas_free_ports() {
  _atlas_kill_stray_servers
  for port in 3000 3002; do
    pids="$(_atlas_port_listeners "$port")"
    if [ -n "$pids" ]; then
      echo "Killing LISTEN process(es) on port $port:"
      printf '%s\n' "$pids" | while IFS= read -r pid; do
        [ -n "$pid" ] || continue
        echo "  $pid"
        kill -9 "$pid" 2>/dev/null || true
      done
    fi
  done
  for port in 3000 3002; do
    if ! _atlas_wait_port_free "$port"; then
      echo "ATLAS UI: port $port is still in use on 127.0.0.1." >&2
      lsof -nP -iTCP:"$port" -sTCP:LISTEN >&2 || true
      return 1
    fi
  done
  return 0
}

# Clear ports before building…
_atlas_free_ports || _atlas_abort 1

cd frontend/atlas || _atlas_abort 1
npm run build || _atlas_abort 1
cd ../../ || _atlas_abort 1

# …and again right before launch, so a process that re-grabbed a port during the
# ~2s build window (e.g. a respawned admin subprocess) is cleared too.
_atlas_free_ports || _atlas_abort 1

python3 src/atlas_ui.py --root /Users/brian/Desktop/Project/NEW_WORKSPACE  --workflow-root /Users/brian/Desktop/Project/brian_hw/common_ai_agent/workflow --port 3000 --admin 3002 --exec s
