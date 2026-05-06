#!/usr/bin/env bash
# check_unmapped.sh — Fail-fast sanity check on synth.v.
# Exits 0 if clean, 7 if unmapped cells, 8 if unintended latches.
# Args: <ip_name>
set -uo pipefail

IP="${1:-}"
if [ -z "${IP}" ]; then echo "[SYN] usage: check_unmapped.sh <ip_name>" >&2; exit 2; fi
NETLIST="${IP}/syn/out/synth.v"
if [ ! -f "${NETLIST}" ]; then echo "[SYN] missing ${NETLIST}" >&2; exit 2; fi

UNMAPPED=$(grep -cE '^\s*\$_' "${NETLIST}" || true)
GENERIC=$(grep -cE '^\s*(\$paramod|\$_NOT_|\$_AND_|\$_OR_|\$_DFF_)' "${NETLIST}" || true)
# sky130 D-latch cell names: dlxtp, dlxtn, dlxbn, dlxbp, dlrtp, dlrbn, dlrbp,
# dlclkp, dlymetal*. Match the dl<2-3 alpha> prefix; `df<x>` (flip-flops)
# explicitly excluded.
LATCHES=$(grep -cE 'sky130_fd_sc_hd__dl(x|r|c|y)' "${NETLIST}" || true)

echo "[SYN] netlist: unmapped=${UNMAPPED} generic=${GENERIC} latch_cells=${LATCHES}"

if [ "${UNMAPPED}" -gt 0 ] || [ "${GENERIC}" -gt 0 ]; then
  echo "[SYN UNMAPPED] dfflibmap/abc did not bind every cell — check liberty path and synth.log" >&2
  exit 7
fi

# Latches are flagged; whether they are intended is up to the SSOT (latch: declared).
SSOT="${IP}/yaml/${IP}.ssot.yaml"
if [ "${LATCHES}" -gt 0 ]; then
  if grep -qE '^\s*latch_intended\s*:\s*true' "${SSOT}" 2>/dev/null; then
    echo "[SYN] ${LATCHES} latch cells (declared in SSOT — OK)"
  else
    echo "[SYN UNINTENDED LATCH] ${LATCHES} latch cells in netlist but SSOT does not declare latch_intended:true" >&2
    exit 8
  fi
fi
exit 0
