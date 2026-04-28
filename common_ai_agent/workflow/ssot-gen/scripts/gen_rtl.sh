#!/usr/bin/env bash
# gen_rtl.sh — Generate RTL from YAML SSOT via Jinja2 templates
set -euo pipefail

MODULE_NAME="${1:-${HOOK_CMD_ARGS:-}}"
if [ -z "$MODULE_NAME" ]; then
  echo "[ERROR] Module name required. Usage: /gen-rtl <module_name>"
  exit 1
fi

GENERATORS_DIR="${MODULE_NAME}/generators"

if [ ! -f "$GENERATORS_DIR/gen_all.py" ]; then
  echo "[ERROR] No gen_all.py found at $GENERATORS_DIR"
  exit 1
fi

echo "=== SSOT RTL Generation: $MODULE_NAME ==="
cd "$(dirname "$GENERATORS_DIR")" && python3 generators/gen_rtl.py

echo "=== RTL Generation Complete ==="
ls -la rtl/*.sv 2>/dev/null || echo "(no .sv files generated)"
