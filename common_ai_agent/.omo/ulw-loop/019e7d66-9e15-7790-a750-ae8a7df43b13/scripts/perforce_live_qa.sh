#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd)"
SESSION_DIR="$ROOT/.omo/ulw-loop/019e7d66-9e15-7790-a750-ae8a7df43b13"
EVIDENCE_DIR="$SESSION_DIR/evidence"
SCRIPT_DIR="$SESSION_DIR/scripts"
mkdir -p "$EVIDENCE_DIR"

SUPER_PASS="P4test_123"
INITIAL_USER_PASS="Atlas_123"
USER_PASS="Atlas_456"
QA_CLEAN_CRITERION=""
QA_CLEAN_TMP=""
QA_CLEAN_ATLAS_PID=""
QA_CLEAN_P4PORT=""
QA_CLEAN_ATLAS_PORT=""
QA_CLEAN_IP=""

usage() {
  echo "usage: $0 c001|c002|c003" >&2
}

wait_http() {
  local url="$1"
  local label="$2"
  local i
  for i in $(seq 1 120); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep 0.25
  done
  echo "timed out waiting for $label at $url" >&2
  return 1
}

start_p4d() {
  local tmp="$1"
  local p4port="$2"
  mkdir -p "$tmp/p4root"
  p4d -r "$tmp/p4root" -p "localhost:$p4port" -L "$tmp/p4d.log" -J "$tmp/journal" --pid-file="$tmp/p4d.pid" -d >/dev/null
  local i
  for i in $(seq 1 80); do
    if P4CONFIG= p4 -p "localhost:$p4port" -u super info >/dev/null 2>&1; then
      return 0
    fi
    sleep 0.1
  done
  echo "p4d did not become ready on $p4port" >&2
  return 1
}

p4_bootstrap_user() {
  local tmp="$1"
  local p4port="$2"
  local tickets="$tmp/tickets"

  printf '%s\n%s\n' "$SUPER_PASS" "$SUPER_PASS" \
    | P4CONFIG= P4TICKETS="$tickets" p4 -p "localhost:$p4port" -u super passwd >/dev/null
  printf '%s\n' "$SUPER_PASS" \
    | P4CONFIG= P4TICKETS="$tickets" p4 -p "localhost:$p4port" -u super login >/dev/null

  P4CONFIG= P4TICKETS="$tickets" p4 -p "localhost:$p4port" -u super user -o atlasqa > "$tmp/atlasqa.user"
  perl -0pi -e 's/^Email:\s*.*/Email:\tatlasqa\@example.com/m; s/^FullName:\s*.*/FullName:\tAtlas QA/m' "$tmp/atlasqa.user"
  P4CONFIG= P4TICKETS="$tickets" p4 -p "localhost:$p4port" -u super user -f -i < "$tmp/atlasqa.user" >/dev/null
  printf '%s\n%s\n' "$INITIAL_USER_PASS" "$INITIAL_USER_PASS" \
    | P4CONFIG= P4TICKETS="$tickets" p4 -p "localhost:$p4port" -u super passwd atlasqa >/dev/null
  printf '%s\n%s\n%s\n' "$INITIAL_USER_PASS" "$USER_PASS" "$USER_PASS" \
    | P4CONFIG= P4TICKETS="$tickets" p4 -p "localhost:$p4port" -u atlasqa passwd >/dev/null
  printf '%s\n' "$USER_PASS" \
    | P4CONFIG= P4TICKETS="$tickets" p4 -p "localhost:$p4port" -u atlasqa login >/dev/null

  printf 'Protections:\n\tsuper user super * //...\n\twrite user atlasqa * //...\n' \
    | P4CONFIG= P4TICKETS="$tickets" p4 -p "localhost:$p4port" -u super protect -i >/dev/null
}

p4_super() {
  local tmp="$1"
  local p4port="$2"
  shift 2
  P4CONFIG= P4TICKETS="$tmp/tickets" p4 -p "localhost:$p4port" -u super "$@"
}

p4_user() {
  local tmp="$1"
  local p4port="$2"
  local client="$3"
  shift 3
  P4CONFIG= P4TICKETS="$tmp/tickets" p4 -p "localhost:$p4port" -u atlasqa -c "$client" -d "$ROOT" "$@"
}

setup_stream_client() {
  local tmp="$1"
  local p4port="$2"
  local client="$3"

  p4_super "$tmp" "$p4port" depot -o GOOD_SOC > "$tmp/depot.spec"
  perl -0pi -e 's/^Type:\s*.*/Type: stream/m' "$tmp/depot.spec"
  p4_super "$tmp" "$p4port" depot -i < "$tmp/depot.spec" >/dev/null

  cat > "$tmp/stream.spec" <<'STREAM'
Stream: //GOOD_SOC/GOOD_IP
Owner: atlasqa
Name: GOOD_IP
Parent: none
Type: mainline
ParentView: noinherit
Paths:
	share ...
STREAM
  p4_super "$tmp" "$p4port" stream -i < "$tmp/stream.spec" >/dev/null

  P4CONFIG= P4TICKETS="$tmp/tickets" p4 -p "localhost:$p4port" -u atlasqa -c "$client" client -S //GOOD_SOC/GOOD_IP -o "$client" > "$tmp/client.spec"
  perl -0pi -e "s#^Root:\\s*.*#Root: $ROOT#m; s#^Options:\\s*.*#Options: noallwrite clobber nocompress unlocked nomodtime normdir#m" "$tmp/client.spec"
  P4CONFIG= P4TICKETS="$tmp/tickets" p4 -p "localhost:$p4port" -u atlasqa -c "$client" client -i < "$tmp/client.spec" >/dev/null
}

seed_perforce_ip() {
  local tmp="$1"
  local p4port="$2"
  local client="$3"
  local ip="$4"
  rm -rf "$ROOT/$ip"
  mkdir -p "$ROOT/$ip/rtl" "$ROOT/$ip/yaml"
  printf 'top_module:\n  name: %s\n' "$ip" > "$ROOT/$ip/yaml/$ip.ssot.yaml"
  printf 'module existing; initial begin $display("DEPOT_EXISTING"); end endmodule\n' > "$ROOT/$ip/rtl/existing.sv"
  printf 'module sync_target; initial begin $display("DEPOT_SYNC_TARGET"); end endmodule\n' > "$ROOT/$ip/rtl/sync_target.sv"
  p4_user "$tmp" "$p4port" "$client" add "$ip/rtl/existing.sv" "$ip/rtl/sync_target.sv" >/dev/null
  p4_user "$tmp" "$p4port" "$client" submit -d "seed $ip" "$ip/..." >/dev/null
  p4_user "$tmp" "$p4port" "$client" sync -f "$ip/..." >/dev/null
  printf 'module new_file; endmodule\n' > "$ROOT/$ip/rtl/new_file.sv"
}

start_atlas() {
  local tmp="$1"
  local atlas_port="$2"
  local ip="$3"
  local p4port="${4:-}"
  local client="${5:-}"
  local log="$tmp/atlas-$atlas_port.log"

  if [[ -n "$p4port" ]]; then
    env \
      ATLAS_ADMIN_AUTH_MODE=local \
      ATLAS_MULTI_USER=0 \
      ATLAS_MULTI_USER_PROC=0 \
      ATLAS_LAZY_WORKERS=1 \
      ATLAS_FRONTEND_MODE=vite \
      ATLAS_SCM_PROVIDER=perforce \
      ATLAS_SCM_ADAPTER_PERFORCE=core.scm_perforce:PerforceP4Adapter \
      P4CONFIG= \
      P4TICKETS="$tmp/tickets" \
      P4PORT="localhost:$p4port" \
      P4USER=atlasqa \
      P4CLIENT="$client" \
      python3 -m src.atlas_ui --host 127.0.0.1 --port "$atlas_port" --root "$ROOT" -ip "$ip" -w default --exec o > "$log" 2>&1 &
  else
    env \
      ATLAS_ADMIN_AUTH_MODE=local \
      ATLAS_MULTI_USER=0 \
      ATLAS_MULTI_USER_PROC=0 \
      ATLAS_LAZY_WORKERS=1 \
      ATLAS_FRONTEND_MODE=vite \
      ATLAS_SCM_PROVIDER=perforce \
      P4CONFIG= \
      python3 -m src.atlas_ui --host 127.0.0.1 --port "$atlas_port" --root "$ROOT" -ip "$ip" -w default --exec o > "$log" 2>&1 &
  fi
  echo $!
}

stop_pid() {
  local pid="${1:-}"
  if [[ -n "$pid" ]] && kill -0 "$pid" >/dev/null 2>&1; then
    kill "$pid" >/dev/null 2>&1 || true
    for _ in $(seq 1 40); do
      kill -0 "$pid" >/dev/null 2>&1 || return 0
      sleep 0.1
    done
    kill -9 "$pid" >/dev/null 2>&1 || true
  fi
}

stop_p4d() {
  local tmp="$1"
  local p4port="$2"
  P4CONFIG= P4TICKETS="$tmp/tickets" p4 -p "localhost:$p4port" -u super admin stop >/dev/null 2>&1 || true
  if [[ -f "$tmp/p4d.pid" ]]; then
    local pid
    pid="$(cat "$tmp/p4d.pid" 2>/dev/null || true)"
    stop_pid "$pid"
  fi
}

write_cleanup_receipt() {
  local criterion="$1"
  local tmp="$2"
  local atlas_pid="${3:-}"
  local p4port="${4:-}"
  local atlas_port="${5:-}"
  local ip="${6:-}"
  local receipt="$EVIDENCE_DIR/$criterion-cleanup.txt"
  {
    echo "cleanup:"
    [[ -n "$atlas_pid" ]] && echo "- stopped atlas pid $atlas_pid"
    [[ -n "$p4port" ]] && echo "- stopped p4d on localhost:$p4port"
    [[ -n "$atlas_port" ]] && echo "- atlas port $atlas_port listeners: $(lsof -nP -iTCP:$atlas_port -sTCP:LISTEN 2>/dev/null | wc -l | tr -d ' ')"
    [[ -n "$p4port" ]] && echo "- p4 port $p4port listeners: $(lsof -nP -iTCP:$p4port -sTCP:LISTEN 2>/dev/null | wc -l | tr -d ' ')"
    [[ -n "$ip" ]] && echo "- removed $ROOT/$ip: $([[ -e "$ROOT/$ip" ]] && echo no || echo yes)"
    echo "- removed tmp $tmp: $([[ -e "$tmp" ]] && echo no || echo yes)"
  } > "$receipt"
}

cleanup_active() {
  stop_pid "$QA_CLEAN_ATLAS_PID"
  if [[ -n "$QA_CLEAN_P4PORT" && -n "$QA_CLEAN_TMP" ]]; then
    stop_p4d "$QA_CLEAN_TMP" "$QA_CLEAN_P4PORT"
  fi
  if [[ -n "$QA_CLEAN_IP" ]]; then
    rm -rf "$ROOT/$QA_CLEAN_IP"
  fi
  if [[ -n "$QA_CLEAN_TMP" ]]; then
    rm -rf "$QA_CLEAN_TMP"
  fi
  if [[ -n "$QA_CLEAN_CRITERION" ]]; then
    write_cleanup_receipt \
      "$QA_CLEAN_CRITERION" \
      "$QA_CLEAN_TMP" \
      "$QA_CLEAN_ATLAS_PID" \
      "$QA_CLEAN_P4PORT" \
      "$QA_CLEAN_ATLAS_PORT" \
      "$QA_CLEAN_IP"
  fi
  return 0
}

arm_cleanup() {
  QA_CLEAN_CRITERION="$1"
  QA_CLEAN_TMP="$2"
  QA_CLEAN_ATLAS_PID="${3:-}"
  QA_CLEAN_P4PORT="${4:-}"
  QA_CLEAN_ATLAS_PORT="${5:-}"
  QA_CLEAN_IP="${6:-}"
  trap cleanup_active EXIT
}

run_c001() {
  local criterion="C001"
  local ip="ulw_p4_c001"
  local p4port="16671"
  local atlas_port="8792"
  local client="atlas_ulw_c001"
  local tmp
  tmp="$(mktemp -d /tmp/ulw-c001.XXXXXX)"
  local atlas_pid=""
  arm_cleanup "$criterion" "$tmp" "$atlas_pid" "$p4port" "$atlas_port" "$ip"

  start_p4d "$tmp" "$p4port"
  p4_bootstrap_user "$tmp" "$p4port"
  setup_stream_client "$tmp" "$p4port" "$client"
  seed_perforce_ip "$tmp" "$p4port" "$client" "$ip"
  atlas_pid="$(start_atlas "$tmp" "$atlas_port" "$ip" "$p4port" "$client")"
  QA_CLEAN_ATLAS_PID="$atlas_pid"
  wait_http "http://127.0.0.1:$atlas_port/healthz?cost=0" "atlas C001"

  ATLAS_BASE_URL="http://127.0.0.1:$atlas_port" \
  PROJECT_ROOT="$ROOT" \
  QA_IP="$ip" \
  C001_ARTIFACT_JSON="$EVIDENCE_DIR/C001-browser-add-edit-sync.json" \
  C001_SCREENSHOT="$EVIDENCE_DIR/C001-browser-add-edit-sync.png" \
  P4CONFIG= \
  P4TICKETS="$tmp/tickets" \
  P4PORT="localhost:$p4port" \
  P4USER=atlasqa \
  P4CLIENT="$client" \
  node "$SCRIPT_DIR/c001_browser_add_edit_sync.mjs"
}

run_c002() {
  local criterion="C002"
  local ip="ulw_p4_c002"
  local p4port="16672"
  local atlas_port="8793"
  local client="atlas_ulw_c002"
  local tmp
  tmp="$(mktemp -d /tmp/ulw-c002.XXXXXX)"
  local atlas_pid=""
  arm_cleanup "$criterion" "$tmp" "$atlas_pid" "$p4port" "$atlas_port" "$ip"

  start_p4d "$tmp" "$p4port"
  p4_bootstrap_user "$tmp" "$p4port"
  setup_stream_client "$tmp" "$p4port" "$client"
  rm -rf "$ROOT/$ip"
  mkdir -p "$ROOT/$ip/rtl" "$ROOT/$ip/yaml"
  printf 'top_module:\n  name: %s\n' "$ip" > "$ROOT/$ip/yaml/$ip.ssot.yaml"
  atlas_pid="$(start_atlas "$tmp" "$atlas_port" "$ip" "$p4port" "$client")"
  QA_CLEAN_ATLAS_PID="$atlas_pid"
  wait_http "http://127.0.0.1:$atlas_port/healthz?cost=0" "atlas C002"

  local artifact="$EVIDENCE_DIR/C002-http-malformed-edit.txt"
  {
    echo "### request: malformed edit path traversal"
    curl -i -sS \
      -H 'Content-Type: application/json' \
      -X POST "http://127.0.0.1:$atlas_port/api/scm/edit" \
      --data "{\"ip\":\"$ip\",\"provider\":\"perforce\",\"paths\":[\"../../.env\"]}"
    echo
    echo "### pane after malformed edit"
    curl -i -sS "http://127.0.0.1:$atlas_port/api/scm/pane?ip=$ip&provider=perforce"
    echo
    echo "### p4 opened after malformed edit"
    P4CONFIG= P4TICKETS="$tmp/tickets" p4 -p "localhost:$p4port" -u atlasqa -c "$client" -d "$ROOT" opened "$ip/..." 2>&1 || true
  } > "$artifact"

  grep -q "HTTP/1.1 200 OK" "$artifact"
  grep -q '"ok":false' "$artifact"
  grep -q "no valid paths to edit/open" "$artifact"
  grep -q "File(s) not opened on this client" "$artifact"
}

run_c003() {
  local criterion="C003"
  local ip="ulw_git_c003"
  local atlas_port="8794"
  local tmp
  tmp="$(mktemp -d /tmp/ulw-c003.XXXXXX)"
  local atlas_pid=""
  arm_cleanup "$criterion" "$tmp" "$atlas_pid" "" "$atlas_port" "$ip"

  rm -rf "$ROOT/$ip"
  mkdir -p "$ROOT/$ip"
  git -C "$ROOT/$ip" init -b ipbranch >/dev/null
  printf 'git override regression\n' > "$ROOT/$ip/README.md"
  git -C "$ROOT/$ip" add README.md >/dev/null
  git -C "$ROOT/$ip" -c user.name=AtlasQA -c user.email=atlasqa@example.com commit -m "seed git override ip" >/dev/null

  atlas_pid="$(start_atlas "$tmp" "$atlas_port" "$ip")"
  QA_CLEAN_ATLAS_PID="$atlas_pid"
  wait_http "http://127.0.0.1:$atlas_port/healthz?cost=0" "atlas C003"

  local artifact="$EVIDENCE_DIR/C003-http-git-override.txt"
  curl -i -sS "http://127.0.0.1:$atlas_port/api/git/status?ip=$ip&provider=git" > "$artifact"
  grep -q "HTTP/1.1 200 OK" "$artifact"
  grep -q '"provider":"git"' "$artifact"
  grep -q '"branch":"ipbranch"' "$artifact"
}

case "${1:-}" in
  c001) run_c001 ;;
  c002) run_c002 ;;
  c003) run_c003 ;;
  *) usage; exit 2 ;;
esac
