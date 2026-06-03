#!/usr/bin/env bash
set -euo pipefail

IP="${1:-}"
if [ -z "$IP" ]; then
  echo "[mutation-guard] usage: $0 <ip_name> [--root <ip-parent>] [mutation_guard.py args...]" >&2
  exit 2
fi
shift || true

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKFLOW_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
ROOT="${ATLAS_PROJECT_ROOT:-${ATLAS_ROOT:-ip_examples}}"

exec python3 "${WORKFLOW_ROOT}/mutation/scripts/mutation_guard.py" "$IP" --root "$ROOT" "$@"
