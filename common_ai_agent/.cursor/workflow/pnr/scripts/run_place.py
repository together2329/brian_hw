#!/usr/bin/env python3
"""run_place.py — Port of run_place.sh. Global + detailed placement.

Args: <ip>. Reads floorplan.def. Writes placed.def.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _pnr_common as common  # noqa: E402


_DENSITY_PY = r"""
import sys, pathlib
try:
    import yaml; d = yaml.safe_load(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")) or {}
except Exception: d = {}
print((d.get("pnr") or {}).get("global_density", 0.65))
"""

_RECORD_DENSITY_PY = r"""
import re, json, sys, pathlib
log = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
m = re.search(r"design area\s+(\d+(?:\.\d+)?)\s+u\^2.*?(\d+)\s*%\s*utilization", log, re.S)
obj = {"design_area_um2": float(m.group(1)) if m else None,
       "utilization_pct": int(m.group(2)) if m else None}
pathlib.Path(sys.argv[2]).write_text(json.dumps(obj, indent=2), encoding="utf-8")
"""


def main(argv: "list[str]") -> int:
    argv = common.argv_from_hook(argv)
    common.load_pdk_env(os.environ)

    ip = argv[0] if argv else ""
    if not ip:
        print("[PNR] usage: run_place.sh <ip>", file=sys.stderr)
        return 2

    rc = common.check_tools()
    if rc != 0:
        return rc
    _netlist, rc = common.check_handoff(ip)
    if rc != 0:
        return rc
    _top = common.top_from_ssot(ip)
    sdc = f"{ip}/sta/out/{ip}.sdc"
    fp = f"{ip}/pnr/out/floorplan.def"
    tcl = f"{ip}/pnr/tcl/place.tcl"
    deff = f"{ip}/pnr/out/placed.def"
    log = f"{ip}/pnr/out/pnr.log"
    Path(f"{ip}/pnr/tcl").mkdir(parents=True, exist_ok=True)
    Path(f"{ip}/pnr/out").mkdir(parents=True, exist_ok=True)

    rc = common.check_stale("FLOORPLAN", fp, deff)
    if rc != 0:
        return rc

    proc = common.run_embedded_py(_DENSITY_PY, [f"{ip}/yaml/{ip}.ssot.yaml"], capture=True)
    density = proc.stdout.strip()

    tlef = os.environ["SKY130_TLEF"]
    lef = os.environ["SKY130_LEF"]
    lib = os.environ["SKY130_LIB"]
    tcl_text = (
        f"read_lef {tlef}\n"
        f"read_lef {lef}\n"
        f"read_liberty {lib}\n"
        f"read_def {fp}\n"
        f"read_sdc {sdc}\n"
        "\n"
        f"global_placement -density {density}\n"
        "detailed_placement\n"
        "check_placement\n"
        f"write_def {deff}\n"
        "report_design_area\n"
        "exit\n"
    )
    Path(tcl).write_text(tcl_text, encoding="utf-8")

    print(f"[PNR-PLACE] openroad → {deff}  (density={density})")
    rc = common.run_openroad_tee(tcl, log)

    log_text = Path(log).read_text(encoding="utf-8", errors="replace") if Path(log).exists() else ""
    if re.search(r"WARN: .*overlap|ERROR.*placement", log_text):
        print(
            "[PNR PLACE OVERLAPS] check_placement found overlaps — usually utilization too high",
            file=sys.stderr,
        )
        return 11
    if rc != 0 or not (Path(deff).is_file() and Path(deff).stat().st_size > 0):
        print(f"[PNR-PLACE] FAILED rc={rc}", file=sys.stderr)
        return rc

    # Record density for the report (best-effort).
    common.run_embedded_py(_RECORD_DENSITY_PY, [log, f"{ip}/pnr/out/density.json"])
    print(f"[PNR-PLACE HANDOFF] {deff} ready — run /pnr-cts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
