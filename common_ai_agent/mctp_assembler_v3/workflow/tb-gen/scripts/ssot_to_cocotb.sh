#!/usr/bin/env bash
set -euo pipefail

IP="${HOOK_CMD_ARGS:-${1:-}}"
IP="${IP%% *}"

if [ -z "$IP" ]; then
  IP="$(find . -maxdepth 3 -type f -path "*/yaml/*.ssot.yaml" -print 2>/dev/null \
    | sed -E 's#^\./##; s#/yaml/.*##' \
    | sort -u \
    | head -1)"
fi

if [ -z "$IP" ]; then
  echo "[ssot-tb] no IP provided and no */yaml/*.ssot.yaml found"
  exit 2
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ "${ATLAS_ALLOW_FIXED_TB_FALLBACK:-}" != "1" ]; then
  echo "[ssot-tb] fixed fallback generator is disabled"
  echo "[ssot-tb] use ATLAS /ssot-tb so tb-gen derives pyuvm/cocotb from SSOT and RTL"
  echo "[ssot-tb] set ATLAS_ALLOW_FIXED_TB_FALLBACK=1 only for explicit legacy migration"
  exit 2
fi
python3 "$SCRIPT_DIR/ssot_to_cocotb.py" "$IP" --root "$PWD"
