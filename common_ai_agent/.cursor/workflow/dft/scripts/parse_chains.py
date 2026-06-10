#!/usr/bin/env python3
"""parse_chains.py — Port of parse_chains.sh. Parse OpenROAD report_dft output → scan_chains.json.

Args: <ip_name>
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


# The body is a single python heredoc in the bash original; run it verbatim so
# the parse logic, JSON output and exit code (sys.exit(10) on 0 chains) match.
_PARSE_PY = r"""
import json, re, sys, pathlib

ip, log_p, scan_p, ssot_p, out_p = sys.argv[1:6]
log  = pathlib.Path(log_p).read_text(encoding="utf-8", errors="replace")
scan = pathlib.Path(scan_p).read_text(encoding="utf-8", errors="replace")
ssot = pathlib.Path(ssot_p).read_text(encoding="utf-8", errors="replace") if pathlib.Path(ssot_p).exists() else ""

try:
    import yaml; cfg = yaml.safe_load(ssot) or {}
except Exception:
    cfg = {}
dft_cfg = cfg.get("dft", {}) or {}
se_port = dft_cfg.get("scan_enable_port", "scan_en")
_t = cfg.get("top_module")
if isinstance(_t, dict): _t = _t.get("name")
top = _t or cfg.get("top") or ip

# Count scan FFs in the netlist (sdfrtp / sdfxtp / sdfstp etc. — sky130 scan-FF cell prefix is `sdf`).
ffs_in_chains = len(re.findall(r"sky130_fd_sc_hd__sdf\w+", scan))
total_ffs     = ffs_in_chains + len(re.findall(r"sky130_fd_sc_hd__df[rxs]\w+", scan))

# OpenROAD report_dft format (approximate — parser must be tolerant):
#   Scan chain 0: length=N, scan_in=scan_in[0], scan_out=scan_out[0], clock=clk
chains = []
for m in re.finditer(
    r"Scan\s+chain\s+(\d+)\s*:?\s*length\s*=\s*(\d+)[^\n]*?scan[_ ]in\s*=\s*(\S+)[^\n]*?scan[_ ]out\s*=\s*(\S+)(?:[^\n]*?clock\s*=\s*(\S+))?",
    log, re.I):
    chains.append({
      "id": int(m.group(1)),
      "length": int(m.group(2)),
      "scan_in":  m.group(3).rstrip(",;"),
      "scan_out": m.group(4).rstrip(",;"),
      "clock":   (m.group(5) or "").rstrip(",;") or "unknown",
      "edge":    "rising",
    })

# Fallback: if the regex missed but the netlist clearly has scan FFs, do a
# softer count-only summary so the gate can still pass.
if not chains and ffs_in_chains > 0:
    chains.append({
      "id": 0, "length": ffs_in_chains,
      "scan_in":  f"{dft_cfg.get('scan_in_prefix','scan_in')}[0]",
      "scan_out": f"{dft_cfg.get('scan_out_prefix','scan_out')}[0]",
      "clock": dft_cfg.get("scan_clock") or "unknown", "edge": "rising",
    })

if chains:
    lengths = [c["length"] for c in chains]
    summary = {
      "total_ffs": total_ffs,
      "ffs_in_chains": sum(lengths),
      "ffs_skipped":   max(0, total_ffs - sum(lengths)),
      "chains": len(chains),
      "max_length": max(lengths),
      "min_length": min(lengths),
      "scan_enable_port": se_port,
      "mode": "scan_insert",
    }
else:
    summary = {
      "total_ffs": total_ffs, "ffs_in_chains": 0, "ffs_skipped": total_ffs,
      "chains": 0, "max_length": 0, "min_length": 0,
      "scan_enable_port": se_port, "mode": "scan_insert_failed",
    }

obj = {"top": top, "tool": "openroad_internal", "scan_chains": chains, "summary": summary}
pathlib.Path(out_p).write_text(json.dumps(obj, indent=2), encoding="utf-8")
print(f"[DFT] scan_chains.json: chains={len(chains)} ffs_in_chains={summary['ffs_in_chains']} total_ffs={total_ffs} → {out_p}")

# Sanity gate: 0 chains with dft.enabled=true is a fail.
if summary["chains"] == 0:
    print("[DFT NO SCAN FFS] no chains stitched — design may be combinational-only or insert_dft failed silently", file=sys.stderr)
    sys.exit(10)
"""


def main(argv: "list[str]") -> int:
    ip = argv[0] if argv else ""
    if not ip:
        print("[DFT] usage: parse_chains.sh <ip_name>", file=sys.stderr)
        return 2

    log = f"{ip}/dft/out/dft.log"
    scan = f"{ip}/dft/out/scan.v"
    ssot = f"{ip}/yaml/{ip}.ssot.yaml"
    json_out = f"{ip}/dft/out/scan_chains.json"

    if not Path(log).is_file():
        print(f"[DFT] missing {log}", file=sys.stderr)
        return 2
    if not (Path(scan).is_file() and Path(scan).stat().st_size > 0):
        print(f"[DFT] missing {scan}", file=sys.stderr)
        return 2

    # Feed the body on stdin (`python3 -`) so tracebacks report File "<stdin>",
    # matching the bash heredoc form.
    proc = subprocess.run(
        [sys.executable, "-", ip, log, scan, ssot, json_out],
        input=_PARSE_PY.lstrip("\n"),
        text=True,
    )
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
