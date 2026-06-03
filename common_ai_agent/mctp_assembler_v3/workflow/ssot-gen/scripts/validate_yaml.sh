#!/usr/bin/env bash
# validate_yaml.sh — Run Cerberus schema validation on all YAML SSOT files
set -euo pipefail

MODULE_NAME="${1:-${HOOK_CMD_ARGS:-}}"
if [ -z "$MODULE_NAME" ]; then
  echo "[ERROR] Module name required. Usage: /validate-yaml <module_name>"
  exit 1
fi

YAML_DIR="${MODULE_NAME}/yaml"
SCHEMA="${YAML_DIR}/${MODULE_NAME}_schema.yaml"

if [ ! -f "$SCHEMA" ]; then
  echo "[SKIP] No schema file at $SCHEMA"
  exit 0
fi

echo "=== YAML Schema Validation: $MODULE_NAME ==="
FAIL_COUNT=0

for yaml_file in "$YAML_DIR"/*.yaml; do
  # Skip the schema itself
  if [[ "$(basename "$yaml_file")" == "${MODULE_NAME}_schema.yaml" ]]; then
    continue
  fi
  echo -n "  validating $(basename "$yaml_file") ... "
  python3 -c "
import yaml, sys
from cerberus import Validator
try:
    with open('$yaml_file') as f: data = yaml.safe_load(f)
    with open('$SCHEMA') as f: schema = yaml.safe_load(f)
    v = Validator(schema)
    if v.validate(data):
        print('PASS')
    else:
        print('FAIL')
        for field, err in v.errors.items(): print(f'  {field}: {err}')
        sys.exit(1)
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)
" 2>&1
  if [ $? -ne 0 ]; then
    FAIL_COUNT=$((FAIL_COUNT + 1))
  fi
done

if [ $FAIL_COUNT -eq 0 ]; then
  echo "=== ALL YAML FILES VALIDATED ==="
  exit 0
else
  echo "=== $FAIL_COUNT VALIDATION FAILURE(S) ==="
  exit 1
fi
