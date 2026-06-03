#!/usr/bin/env bash
# run_openroad_dft.sh — Invoke OpenROAD on <ip>/dft/run.tcl; capture all output.
# Args: <ip_name>
set -uo pipefail

PDK_ENV="$(cd "$(dirname "$0")/../.." && pwd -P)/scripts/pdk_env.sh"
[ -f "${PDK_ENV}" ] && source "${PDK_ENV}"

IP="${1:-}"
if [ -z "${IP}" ]; then echo "[DFT] usage: run_openroad_dft.sh <ip_name>" >&2; exit 2; fi

TCL="${IP}/dft/run.tcl"
LOG="${IP}/dft/out/dft.log"
mkdir -p "${IP}/dft/out"

if [ ! -f "${TCL}" ]; then echo "[DFT] missing ${TCL} — run /dft-tcl first" >&2; exit 2; fi
if ! command -v openroad >/dev/null 2>&1; then
  echo "[DFT TOOL MISSING] openroad not on PATH" >&2; exit 3
fi
if [ -z "${SKY130_LIB:-}" ] || [ ! -r "${SKY130_LIB}" ]; then
  echo "[DFT MISSING PDK] \$SKY130_LIB unreadable" >&2; exit 4
fi

openroad -no_init -exit "${TCL}" 2>&1 | tee "${LOG}"
RC=${PIPESTATUS[0]}
echo "[DFT] openroad rc=${RC} log=${LOG}"
exit "${RC}"
