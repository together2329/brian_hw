#!/usr/bin/env bash
# gen_rtl.sh — Legacy alias for SSOT-to-RTL handoff.
set -euo pipefail

MODULE_NAME="${1:-${HOOK_CMD_ARGS:-}}"
if [ -z "$MODULE_NAME" ]; then
  echo "[ERROR] Module name required. Usage: /gen-rtl <module_name>"
  exit 1
fi

echo "[gen_rtl] BLOCKED: ssot-gen does not run fixed RTL generators."
echo "[gen_rtl] Validate SSOT, then run: /ssot-rtl $MODULE_NAME"
exit 2
