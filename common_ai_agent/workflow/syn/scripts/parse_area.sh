#!/usr/bin/env bash
# parse_area.sh — Read <ip>/syn/out/syn.log + synth.v, emit <ip>/syn/out/area.json.
# Args: <ip_name>
set -uo pipefail

IP="${1:-}"
if [ -z "${IP}" ]; then echo "[SYN] usage: parse_area.sh <ip_name>" >&2; exit 2; fi

LOG="${IP}/syn/out/syn.log"
NETLIST="${IP}/syn/out/synth.v"
OUT="${IP}/syn/out/area.json"

if [ ! -f "${LOG}" ]; then echo "[SYN] missing ${LOG}" >&2; exit 2; fi
if [ ! -f "${NETLIST}" ]; then echo "[SYN] missing ${NETLIST}" >&2; exit 2; fi

python3 - "${IP}" "${LOG}" "${NETLIST}" "${OUT}" <<'PY'
import json, re, sys, pathlib
ip, log_path, net_path, out_path = sys.argv[1:5]
log = pathlib.Path(log_path).read_text(errors="replace")
net = pathlib.Path(net_path).read_text(errors="replace")

# Parse the FINAL `=== <top> ===` stat block (yosys appends one per stat call).
blocks = re.findall(r"=== ([^=]+?) ===\s*\n([\s\S]+?)(?=\n===|\Z)", log)
# Prefer the cumulative `design hierarchy` block when present
# (multi-module designs); fall back to last block. `top_name` field stays
# the SSOT-declared IP name, not yosys's per-block label.
top_name = ip
total_cells = 0
total_area = 0.0
by_cell = {}
if blocks:
    pick = next((b for b in reversed(blocks) if "design hierarchy" in b[0].lower()), blocks[-1])
    body = pick[1]
    # yosys stat (with -liberty) format:
    #          23  304.042   cells
    #           1    5.005   sky130_fd_sc_hd__a21oi_1
    # For larger IPs yosys switches to scientific notation:
    #         612 8.59E+03   cells
    #         224 5.61E+03   sky130_fd_sc_hd__dfrtp_1
    NUM = r"[0-9.]+(?:[eE][+-]?\d+)?"
    m_total = re.search(rf"^\s*(\d+)\s+({NUM})\s+cells\b", body, re.M)
    if m_total:
        total_cells = int(m_total.group(1))
        total_area  = float(m_total.group(2))
    # Fallback: Chip area summary line (always plain decimal).
    if total_area == 0.0:
        m_chip = re.search(r"Chip area for(?:\s+top)?\s+module[^:]*:\s+([0-9.]+)", body)
        if m_chip: total_area = float(m_chip.group(1))
    # Per-cell rows: "<count> <area>  <cell_name>"
    for c_count, c_area, c_name in re.findall(
        rf"^\s*(\d+)\s+({NUM})\s+(sky130_fd_sc_hd__\S+)\s*$", body, re.M):
        by_cell[c_name] = int(c_count)

# Sequential vs combinational by liberal pattern match on cell name.
SEQ = re.compile(r"sky130_fd_sc_hd__(?:dfrtp|dfxtp|dfstp|dfbbn|sdf|edf|latch|dlrtp|dlxtp)")
seq_cells = sum(c for k, c in by_cell.items() if SEQ.search(k))
seq_area  = 0.0  # area per cell type not in stat output by default
comb_cells = total_cells - seq_cells

obj = {
  "top": top_name,
  "corner": pathlib.Path(__import__("os").environ.get("SKY130_LIB", "")).name or "unknown",
  "total_cells": total_cells,
  "total_area_um2": total_area,
  "by_kind": {
    "sequential":    {"cells": seq_cells,  "area_um2": None},
    "combinational": {"cells": comb_cells, "area_um2": None},
  },
  "by_cell": dict(sorted(by_cell.items(), key=lambda kv: -kv[1])[:32]),
}
pathlib.Path(out_path).write_text(json.dumps(obj, indent=2))
print(f"[SYN] area.json: total={total_cells} cells, seq={seq_cells}, comb={comb_cells}, area={total_area} um2 → {out_path}")
PY
