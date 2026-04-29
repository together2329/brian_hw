#!/usr/bin/env bash
# kill-port.sh — free a TCP port that's stuck holding the Atlas server.
#
# Usage:
#   ./kill-port.sh             # default: 8765 (atlas), 8080 (legacy web)
#   ./kill-port.sh 8765        # just one
#   ./kill-port.sh 8765 8080   # multiple
#
# Strategy: lsof -ti <port> → list PIDs → kill (TERM), then -9 if still alive.

set -u

ports=("$@")
if [[ ${#ports[@]} -eq 0 ]]; then
  ports=(8765 8080)
fi

did_kill=0
for port in "${ports[@]}"; do
  pids=$(lsof -ti ":$port" 2>/dev/null || true)
  if [[ -z "$pids" ]]; then
    echo "  ✓ port $port already free"
    continue
  fi
  echo "  → port $port held by: $pids"
  # Polite first
  echo "$pids" | xargs kill 2>/dev/null || true
  sleep 0.5
  pids2=$(lsof -ti ":$port" 2>/dev/null || true)
  if [[ -n "$pids2" ]]; then
    # Stubborn — escalate
    echo "    still alive after SIGTERM, sending SIGKILL: $pids2"
    echo "$pids2" | xargs kill -9 2>/dev/null || true
    sleep 0.3
  fi
  if [[ -z "$(lsof -ti ":$port" 2>/dev/null || true)" ]]; then
    echo "  ✓ port $port now free"
    did_kill=1
  else
    echo "  ✗ port $port STILL HELD — try: sudo lsof -i :$port"
  fi
done

# Tidy up the pidfile if we used it
[[ -f /tmp/atlas_ui.pid ]] && rm -f /tmp/atlas_ui.pid

exit 0
