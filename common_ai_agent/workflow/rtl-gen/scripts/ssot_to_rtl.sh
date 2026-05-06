#!/usr/bin/env bash
set -euo pipefail

IP="${HOOK_CMD_ARGS:-$1}"
IP="${IP%% *}"

if [ -z "$IP" ]; then
  IP="$(find . -maxdepth 3 -type f -path "*/yaml/*.ssot.yaml" -print 2>/dev/null \
    | sed -E 's#^\./##; s#/yaml/.*##' \
    | sort -u \
    | head -1)"
fi

if [ -z "$IP" ]; then
  echo "[ssot-rtl] no IP provided and no */yaml/*.ssot.yaml found"
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python3 "$SCRIPT_DIR/derive_rtl_todos.py" "$IP" --root "$PWD"
python3 "$SCRIPT_DIR/ssot_to_rtl.py" "$IP" --root "$PWD"

if command -v iverilog >/dev/null 2>&1; then
  iverilog -g2012 -o "/tmp/${IP}_rtl_check.out" -c "$IP/list/$IP.f"
  echo "[ssot-rtl] compile PASS: iverilog -g2012 -o /tmp/${IP}_rtl_check.out -c $IP/list/$IP.f"
else
  echo "[ssot-rtl] iverilog not found; LLM-authored RTL preflight passed but compile was skipped"
fi

echo "[ssot-rtl] artifacts:"
find "$IP/rtl" "$IP/list" -type f | sort
