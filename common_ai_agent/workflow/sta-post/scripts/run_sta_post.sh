#!/usr/bin/env bash
# run_sta_post.sh — Invoke OpenSTA on <ip>/sta-post/run.tcl.
# Args: <ip>
set -uo pipefail

IP="${1:-}"
if [ -z "${IP}" ]; then echo "[STA-POST] usage: run_sta_post.sh <ip>" >&2; exit 2; fi

TCL="${IP}/sta-post/run.tcl"
LOG="${IP}/sta-post/out/sta.log"
mkdir -p "${IP}/sta-post/out"

[ ! -f "${TCL}" ] && { echo "[STA-POST] missing ${TCL}" >&2; exit 2; }
if ! command -v sta >/dev/null 2>&1; then
  echo "[STA-POST TOOL MISSING] OpenSTA 'sta' not on PATH" >&2; exit 3
fi
[ -z "${SKY130_LIB:-}" ] && { echo "[STA-POST MISSING PDK]" >&2; exit 4; }

sta -no_init -no_splash -exit "${TCL}" 2>&1 | tee "${LOG}"
RC=${PIPESTATUS[0]}
echo "[STA-POST] sta rc=${RC} log=${LOG}"
exit "${RC}"
