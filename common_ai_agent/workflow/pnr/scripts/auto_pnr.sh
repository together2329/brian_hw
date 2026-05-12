#!/usr/bin/env bash
# auto_pnr.sh — One-shot PnR pipeline. Calls fp → place → cts → route in sequence.
# Args: <ip>
set -uo pipefail

if [ $# -eq 0 ] && [ -n "${HOOK_CMD_ARGS:-}" ]; then
  # shellcheck disable=SC2086
  set -- ${HOOK_CMD_ARGS}
fi

IP="${1:-}"; [ -z "${IP}" ] && { echo "[PNR] usage: auto_pnr.sh <ip>" >&2; exit 2; }
[ ! -d "${IP}" ] && { echo "[PNR] no such IP dir: ${IP}" >&2; exit 2; }

DIR="$(dirname "$0")"
bash "${DIR}/preflight.sh"  "${IP}" || exit $?
bash "${DIR}/run_fp.sh"     "${IP}" || exit $?
bash "${DIR}/run_place.sh"  "${IP}" || exit $?
bash "${DIR}/run_cts.sh"    "${IP}" || exit $?
bash "${DIR}/run_route.sh"  "${IP}" || exit $?
bash "${DIR}/write_report.sh" "${IP}" || true
echo "[PNR] full pipeline complete — see ${IP}/pnr/out/pnr.report.md"
