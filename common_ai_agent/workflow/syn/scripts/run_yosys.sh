#!/usr/bin/env bash
# run_yosys.sh — Invoke yosys on <ip>/syn/run.ys; capture stdout/stderr to syn.log.
# Args: <ip_name>
set -uo pipefail

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

yosys -l "${LOG}" -q "${SCRIPT}"
RC=$?
echo "[SYN] yosys rc=${RC} log=${LOG}"
exit "${RC}"
