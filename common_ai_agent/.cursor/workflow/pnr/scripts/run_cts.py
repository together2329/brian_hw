#!/usr/bin/env python3
"""run_cts.py — Port of run_cts.sh. Clock tree synthesis.

Reads placed.def. Writes cts.def + cts.v.  Args: <ip>
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _pnr_common as common  # noqa: E402


_BUFLIST_PY = r"""
import sys, pathlib
try:
    import yaml; d = yaml.safe_load(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")) or {}
except Exception: d = {}
bufs = (d.get("pnr") or {}).get("cts_buf_list") or "sky130_fd_sc_hd__clkbuf_4 sky130_fd_sc_hd__clkbuf_8"
if isinstance(bufs, list):
    print(" ".join(str(item).strip() for item in bufs if str(item).strip()))
else:
    print(" ".join(str(bufs).replace(",", " ").split()))
"""


def main(argv: "list[str]") -> int:
    argv = common.argv_from_hook(argv)
    common.load_pdk_env(os.environ)

    ip = argv[0] if argv else ""
    if not ip:
        print("[PNR] usage: run_cts.sh <ip>", file=sys.stderr)
        return 2

    rc = common.check_tools()
    if rc != 0:
        return rc
    _netlist, rc = common.check_handoff(ip)
    if rc != 0:
        return rc
    _top = common.top_from_ssot(ip)
    sdc = f"{ip}/sta/out/{ip}.sdc"
    placed = f"{ip}/pnr/out/placed.def"
    tcl = f"{ip}/pnr/tcl/cts.tcl"
    deff = f"{ip}/pnr/out/cts.def"
    net = f"{ip}/pnr/out/cts.v"
    log = f"{ip}/pnr/out/pnr.log"
    Path(f"{ip}/pnr/tcl").mkdir(parents=True, exist_ok=True)
    Path(f"{ip}/pnr/out").mkdir(parents=True, exist_ok=True)

    rc = common.check_stale("PLACE", placed, deff)
    if rc != 0:
        return rc

    proc = common.run_embedded_py(_BUFLIST_PY, [f"{ip}/yaml/{ip}.ssot.yaml"], capture=True)
    buflist = proc.stdout.strip()

    tlef = os.environ["SKY130_TLEF"]
    lef = os.environ["SKY130_LEF"]
    lib = os.environ["SKY130_LIB"]
    tcl_text = (
        f"read_lef {tlef}\n"
        f"read_lef {lef}\n"
        f"read_liberty {lib}\n"
        f"read_def {placed}\n"
        f"read_sdc {sdc}\n"
        "\n"
        f'clock_tree_synthesis -buf_list "{buflist}"\n'
        "detailed_placement\n"
        f"write_def {deff}\n"
        f"write_verilog {net}\n"
        "report_clock_skew\n"
        "exit\n"
    )
    Path(tcl).write_text(tcl_text, encoding="utf-8")

    print(f"[PNR-CTS] openroad → {deff} + {net}")
    rc = common.run_openroad_tee(tcl, log)
    if (
        rc != 0
        or not (Path(deff).is_file() and Path(deff).stat().st_size > 0)
        or not (Path(net).is_file() and Path(net).stat().st_size > 0)
    ):
        print(f"[PNR-CTS] FAILED rc={rc}", file=sys.stderr)
        return rc
    print(f"[PNR-CTS HANDOFF] {deff}, {net} ready — run /pnr-route")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
