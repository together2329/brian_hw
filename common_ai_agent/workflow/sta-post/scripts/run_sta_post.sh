#!/usr/bin/env bash
# run_sta_post.sh — Invoke OpenSTA on <ip>/sta-post/run.tcl.
# Args: <ip>
set -uo pipefail

if [ $# -eq 0 ] && [ -n "${HOOK_CMD_ARGS:-}" ]; then
  # shellcheck disable=SC2086
  set -- ${HOOK_CMD_ARGS}
fi

PDK_ENV="$(cd "$(dirname "$0")/../.." && pwd -P)/scripts/pdk_env.sh"
[ -f "${PDK_ENV}" ] && source "${PDK_ENV}"

IP="${1:-}"
if [ -z "${IP}" ]; then echo "[STA-POST] usage: run_sta_post.sh <ip>" >&2; exit 2; fi

TCL="${IP}/sta-post/run.tcl"
LOG="${IP}/sta-post/out/sta.log"
mkdir -p "${IP}/sta-post/out"

[ ! -f "${TCL}" ] && { echo "[STA-POST] missing ${TCL}" >&2; exit 2; }
if ! command -v sta >/dev/null 2>&1; then
  echo "[STA-POST TOOL MISSING] OpenSTA 'sta' not on PATH" >&2; exit 3
fi
if [ -z "${SKY130_LIB:-}" ] || [ ! -r "${SKY130_LIB}" ]; then
  echo "[STA-POST MISSING PDK] \$SKY130_LIB unreadable" >&2; exit 4
fi

sta -no_init -no_splash -exit "${TCL}" 2>&1 | tee "${LOG}"
RC=${PIPESTATUS[0]}
echo "[STA-POST] sta rc=${RC} log=${LOG}"
exit "${RC}"
