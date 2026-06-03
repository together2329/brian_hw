#!/usr/bin/env bash
# preflight.sh — Validate post-route STA tool, PDK, and PnR handoff inputs.
# Args: <ip>
set -uo pipefail

if [ $# -eq 0 ] && [ -n "${HOOK_CMD_ARGS:-}" ]; then
  # shellcheck disable=SC2086
  set -- ${HOOK_CMD_ARGS}
fi

PDK_ENV="$(cd "$(dirname "$0")/../.." && pwd -P)/scripts/pdk_env.sh"
[ -f "${PDK_ENV}" ] && source "${PDK_ENV}"

IP="${1:-}"
if [ -z "${IP}" ]; then echo "[STA-POST PREFLIGHT] usage: preflight.sh <ip>" >&2; exit 2; fi

ROUTED_V="${IP}/pnr/out/routed.v"
ROUTED_SPEF="${IP}/pnr/out/routed.spef"
ROUTED_DEF="${IP}/pnr/out/routed.def"
CTS_V="${IP}/pnr/out/cts.v"
SDC="${IP}/sta/out/${IP}.sdc"

echo "[STA-POST PREFLIGHT] cwd=$(pwd -P)"
echo "[STA-POST PREFLIGHT] PDK_ROOT=${PDK_ROOT:-}"
echo "[STA-POST PREFLIGHT] SKY130_LIB=${SKY130_LIB:-}"

if [ ! -d "${IP}" ]; then echo "[STA-POST PREFLIGHT] IP dir missing: ${IP}" >&2; exit 2; fi
if ! command -v sta >/dev/null 2>&1; then
  echo "[STA-POST TOOL MISSING] OpenSTA 'sta' not on PATH" >&2; exit 3
fi
if [ -z "${SKY130_LIB:-}" ] || [ ! -r "${SKY130_LIB}" ]; then
  echo "[STA-POST MISSING PDK] \$SKY130_LIB unreadable: ${SKY130_LIB:-}" >&2; exit 4
fi
if [ ! -s "${ROUTED_V}" ]; then
  echo "[STA-POST HANDOFF MISSING] ${ROUTED_V} — run /pnr-route first" >&2; exit 5
fi
if [ ! -s "${ROUTED_SPEF}" ]; then
  echo "[STA-POST SPEF MISSING] ${ROUTED_SPEF} — re-run /pnr-route to extract parasitics" >&2; exit 5
fi
if [ ! -f "${SDC}" ]; then
  echo "[STA-POST SDC MISSING] ${SDC} — run /sta-sdc first" >&2; exit 5
fi
if [ -f "${CTS_V}" ] && [ "${CTS_V}" -nt "${ROUTED_V}" ]; then
  echo "[STA-POST STALE NETLIST] ${CTS_V} newer than ${ROUTED_V}" >&2; exit 6
fi
if [ -f "${ROUTED_DEF}" ] && [ "${ROUTED_DEF}" -nt "${ROUTED_SPEF}" ]; then
  echo "[STA-POST STALE SPEF] ${ROUTED_DEF} newer than ${ROUTED_SPEF}" >&2; exit 6
fi

echo "[STA-POST PREFLIGHT] sta=$(command -v sta)"
echo "[STA-POST PREFLIGHT] routed_v=${ROUTED_V}"
echo "[STA-POST PREFLIGHT] routed_spef=${ROUTED_SPEF} size=$(wc -c < "${ROUTED_SPEF}")"
echo "[STA-POST PREFLIGHT] sdc=${SDC}"
echo "[STA-POST PREFLIGHT] OK"
