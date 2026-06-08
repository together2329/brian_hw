#!/usr/bin/env bash
# =============================================================================
# atlas_tunnel.sh — start/stop a cloudflared quick tunnel exposing a local port
# (default 3000, the ATLAS UI) to the public internet for outside testing.
#
# Quick tunnels need NO cloudflare account or domain — they mint a random
# https://<words>.trycloudflare.com URL that lives only while the process runs.
# ATLAS's own login gate still protects the app; stop the tunnel when done.
#
# Usage:
#   scripts/atlas_tunnel.sh start [port]    # default port 3000
#   scripts/atlas_tunnel.sh stop  [port]
#   scripts/atlas_tunnel.sh status [port]
#   scripts/atlas_tunnel.sh url   [port]    # print the current public URL
#
# Examples:
#   scripts/atlas_tunnel.sh start          # expose :3000, print URL
#   scripts/atlas_tunnel.sh start 3002     # expose the admin server
#   scripts/atlas_tunnel.sh url            # re-print the :3000 URL
#   scripts/atlas_tunnel.sh stop           # tear the :3000 tunnel down
#
# Runtime files (log/pid/url) live under $ATLAS_TUNNEL_DIR (default
# /tmp/atlas_tunnel) so nothing untracked lands in the repo.
# =============================================================================
set -uo pipefail

CMD="${1:-}"
PORT="${2:-3000}"
RUN_DIR="${ATLAS_TUNNEL_DIR:-/tmp/atlas_tunnel}"
LOG="$RUN_DIR/cf_${PORT}.log"
PIDF="$RUN_DIR/cf_${PORT}.pid"
URLF="$RUN_DIR/cf_${PORT}.url"
MATCH="cloudflared tunnel --url http://localhost:${PORT}"

mkdir -p "$RUN_DIR"

usage() { echo "usage: $0 {start|stop|status|url} [port=3000]" >&2; exit 2; }

# PID of a live tunnel for this exact port (ours or one started by hand), or "".
find_pid() { pgrep -f "$MATCH" 2>/dev/null | head -1; }

case "$CMD" in
  start)
    command -v cloudflared >/dev/null 2>&1 || {
      echo "cloudflared not installed — run: brew install cloudflared" >&2; exit 1; }
    existing="$(find_pid)"
    if [ -n "$existing" ]; then
      echo "tunnel for :$PORT already running (pid $existing) -> $(cat "$URLF" 2>/dev/null || echo '(url unknown — check the process log)')"
      exit 0
    fi
    : > "$LOG"; : > "$URLF"
    nohup cloudflared tunnel --url "http://localhost:${PORT}" --no-autoupdate >"$LOG" 2>&1 &
    echo "$!" > "$PIDF"
    url=""
    for _ in $(seq 1 30); do
      url="$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$LOG" | head -1)"
      [ -n "$url" ] && break
      sleep 1
    done
    if [ -n "$url" ]; then
      echo "$url" > "$URLF"
      echo "tunnel up (:$PORT, pid $(cat "$PIDF")) -> $url"
    else
      echo "tunnel started (pid $(cat "$PIDF")) but no URL yet; tail $LOG:" >&2
      tail -5 "$LOG" >&2
      exit 1
    fi
    ;;
  stop|kill)
    pid="$(find_pid)"
    if [ -n "$pid" ]; then
      pkill -f "$MATCH" 2>/dev/null
      echo "stopped tunnel :$PORT (pid $pid)"
    else
      echo "no tunnel running for :$PORT"
    fi
    rm -f "$PIDF" "$URLF"
    ;;
  status)
    pid="$(find_pid)"
    if [ -n "$pid" ]; then
      echo "running (:$PORT, pid $pid) -> $(cat "$URLF" 2>/dev/null || echo '(url unknown)')"
    else
      echo "not running (:$PORT)"
    fi
    ;;
  url)
    if [ -s "$URLF" ] && [ -n "$(find_pid)" ]; then
      cat "$URLF"
    else
      echo "no active url for :$PORT (run: $0 start $PORT)" >&2; exit 1
    fi
    ;;
  *)
    usage
    ;;
esac
