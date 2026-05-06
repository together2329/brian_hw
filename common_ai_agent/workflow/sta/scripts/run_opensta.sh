#!/usr/bin/env bash
# run_opensta.sh — Invoke OpenSTA on <ip>/sta/run.tcl; capture all output to sta.log.
# Args: <ip_name>
set -uo pipefail

IP="${1:-}"
if [ -z "${IP}" ]; then echo "[STA] usage: run_opensta.sh <ip_name>" >&2; exit 2; fi

TCL="${IP}/sta/run.tcl"
LOG="${IP}/sta/out/sta.log"
mkdir -p "${IP}/sta/out"

if [ ! -f "${TCL}" ]; then echo "[STA] missing ${TCL} — run /sta-sdc and write_sta_tcl first" >&2; exit 2; fi
if ! command -v sta >/dev/null 2>&1; then
  echo "[STA TOOL MISSING] OpenSTA 'sta' not on PATH" >&2; exit 3
fi
if [ -z "${SKY130_LIB:-}" ] || [ ! -r "${SKY130_LIB}" ]; then
  echo "[STA MISSING PDK] \$SKY130_LIB unreadable" >&2; exit 4
fi

# OpenSTA flags: -no_init skips ~/.sta init, -no_splash silences banner,
# -exit forces non-interactive completion. tee mirrors output to terminal.
sta -no_init -no_splash -exit "${TCL}" 2>&1 | tee "${LOG}"
RC=${PIPESTATUS[0]}
echo "[STA] sta rc=${RC} log=${LOG}"
exit "${RC}"
