#!/usr/bin/env bash
# run_yosys.sh — Invoke yosys on <ip>/syn/run.ys; capture stdout/stderr to syn.log.
# Args: <ip_name>
set -uo pipefail

if [ $# -eq 0 ] && [ -n "${HOOK_CMD_ARGS:-}" ]; then
  # shellcheck disable=SC2086
  set -- ${HOOK_CMD_ARGS}
fi

PDK_ENV="$(cd "$(dirname "$0")/../.." && pwd -P)/scripts/pdk_env.sh"
[ -f "${PDK_ENV}" ] && source "${PDK_ENV}"

IP="${1:-}"
if [ -z "${IP}" ]; then echo "[SYN] usage: run_yosys.sh <ip_name>" >&2; exit 2; fi

SCRIPT="${IP}/syn/run.ys"
LOG="${IP}/syn/out/syn.log"
mkdir -p "${IP}/syn/out"

if [ ! -f "${SCRIPT}" ]; then echo "[SYN] missing ${SCRIPT}" >&2; exit 2; fi
if ! command -v yosys >/dev/null 2>&1; then
  echo "[SYN TOOL MISSING] yosys not on PATH" >&2; exit 3
fi
if [ -z "${SKY130_LIB:-}" ] || [ ! -r "${SKY130_LIB}" ]; then
  echo "[SYN MISSING PDK] \$SKY130_LIB unreadable" >&2; exit 4
fi

yosys -l "${LOG}" "${SCRIPT}" 2>&1 | tail -120
RC=${PIPESTATUS[0]}
echo "[SYN] yosys rc=${RC} log=${LOG} liberty=${SKY130_LIB}"
if [ "${RC}" -ne 0 ]; then
  echo "[SYN] yosys failed; last log lines:" >&2
  tail -80 "${LOG}" >&2 || true
fi
exit "${RC}"
