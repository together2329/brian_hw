#!/usr/bin/env python3
"""run_route.py — Port of run_route.sh. Global + detailed route + SPEF extraction.

Args: <ip>. Reads cts.def + cts.v. Writes routed.def + routed.v + routed.spef.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _pnr_common as common  # noqa: E402


# Const-net normalisation heredoc (writes ROUTE_DEF from CTS_DEF).
_NORMALIZE_PY = r"""
import pathlib
import re
import sys

src, dst = map(pathlib.Path, sys.argv[1:3])
const_nets = {"zero_", "one_", "const0", "const1", "_zero_", "_one_"}
changed = 0
out = []
for line in src.read_text(encoding="utf-8", errors="replace").splitlines():
    match = re.match(r"^(\s*-\s+)(\S+)(\b.*\+\s+USE\s+)(GROUND|POWER)(\s*;.*)$", line)
    net_name = match.group(2).lower() if match else ""
    net_leaf = net_name.rsplit("/", 1)[-1]
    if match and (net_name in const_nets or net_leaf in const_nets):
        line = "".join([match.group(1), match.group(2), match.group(3), "SIGNAL", match.group(5)])
        changed += 1
    out.append(line)
dst.write_text("\n".join(out) + "\n", encoding="utf-8")
if changed:
    print(f"[PNR-ROUTE] normalized {changed} constant tie net(s) to USE SIGNAL for detailed_route")
"""

_DRC_JSON_PY = r"""
import json, sys, pathlib, re
out, count, rpt = sys.argv[1:4]
violations = []
if pathlib.Path(rpt).exists():
    text = pathlib.Path(rpt).read_text(encoding="utf-8", errors="replace")
    for m in re.finditer(r"^violation .*$", text, re.M):
        if len(violations) < 10: violations.append(m.group(0))
pathlib.Path(out).write_text(
  json.dumps({"drc_count": int(count), "first_10": violations}, indent=2),
  encoding="utf-8",
)
"""


def main(argv: "list[str]") -> int:
    argv = common.argv_from_hook(argv)
    common.load_pdk_env(os.environ)

    ip = argv[0] if argv else ""
    if not ip:
        print("[PNR] usage: run_route.sh <ip>", file=sys.stderr)
        return 2

    rc = common.check_tools()
    if rc != 0:
        return rc
    _top = common.top_from_ssot(ip)
    sdc = f"{ip}/sta/out/{ip}.sdc"
    cts_def = f"{ip}/pnr/out/cts.def"
    cts_net = f"{ip}/pnr/out/cts.v"
    route_def = f"{ip}/pnr/out/cts_route.def"
    tcl = f"{ip}/pnr/tcl/route.tcl"
    deff = f"{ip}/pnr/out/routed.def"
    net = f"{ip}/pnr/out/routed.v"
    spef = f"{ip}/pnr/out/routed.spef"
    drc = f"{ip}/pnr/out/drc.rpt"
    log = f"{ip}/pnr/out/pnr.log"
    Path(f"{ip}/pnr/tcl").mkdir(parents=True, exist_ok=True)
    Path(f"{ip}/pnr/out").mkdir(parents=True, exist_ok=True)

    rc = common.check_stale("CTS", cts_def, deff)
    if rc != 0:
        return rc
    rc = common.check_stale("CTS-NET", cts_net, net)
    if rc != 0:
        return rc

    common.run_embedded_py(_NORMALIZE_PY, [cts_def, route_def])

    tlef = os.environ["SKY130_TLEF"]
    lef = os.environ["SKY130_LEF"]
    lib = os.environ["SKY130_LIB"]
    tcl_text = (
        f"read_lef {tlef}\n"
        f"read_lef {lef}\n"
        f"read_liberty {lib}\n"
        f"read_def {route_def}\n"
        f"read_sdc {sdc}\n"
        "\n"
        f"global_route -guide_file {ip}/pnr/out/route.guide\n"
        f"detailed_route -output_drc {drc}\n"
        f"write_def {deff}\n"
        f"write_verilog {net}\n"
        "\n"
        "# Parasitic extraction → SPEF for /sta-post sign-off.\n"
        "define_process_corner -ext_model_index 0 X\n"
        "extract_parasitics -ext_model_file $::env(SKY130_RCX_RULES) -corner_cnt 1\n"
        f"write_spef {spef}\n"
        "exit\n"
    )
    Path(tcl).write_text(tcl_text, encoding="utf-8")

    print(f"[PNR-ROUTE] openroad → {deff} + {net} + {spef}")
    rc = common.run_openroad_tee(tcl, log)

    # DRC summary
    drc_count = "0"
    if Path(drc).is_file():
        text = Path(drc).read_text(encoding="utf-8", errors="replace")
        n = sum(1 for line in text.splitlines() if re.match(r"^violation", line))
        drc_count = str(n)
    common.run_embedded_py(_DRC_JSON_PY, [f"{ip}/pnr/out/drc.json", drc_count, drc])

    if rc != 0 or not (Path(deff).is_file() and Path(deff).stat().st_size > 0) or not (
        Path(net).is_file() and Path(net).stat().st_size > 0
    ):
        print(f"[PNR-ROUTE] FAILED rc={rc}", file=sys.stderr)
        return rc
    if not (Path(spef).is_file() and Path(spef).stat().st_size > 0):
        print(f"[PNR SPEF FAILED] {spef} empty — sign-off STA cannot proceed", file=sys.stderr)
        return 12
    print(f"[PNR HANDOFF] {spef} ready  drc={drc_count}  — run /sta-post")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
