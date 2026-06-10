#!/usr/bin/env python3
"""write_report.py — Port of write_report.sh (PnR). Aggregate per-stage stats into pnr.report.md.

Args: <ip>
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _pnr_common as common  # noqa: E402


# The report body is a single python heredoc in the bash original; run it
# verbatim so the emitted markdown is byte-for-byte identical.
_REPORT_PY = r"""
import json, pathlib, sys, datetime
ip, out, rpt = sys.argv[1:4]
out = pathlib.Path(out)
date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

def jload(name):
    p = out / name
    if p.exists():
        try: return json.loads(p.read_text(encoding="utf-8", errors="replace"))
        except Exception: return None
    return None

density = jload("density.json") or {}
drc     = jload("drc.json") or {}

def has(name):  return (out / name).exists() and (out / name).stat().st_size > 0
artifacts = {
  "floorplan.def": has("floorplan.def"),
  "placed.def":    has("placed.def"),
  "cts.def":       has("cts.def"),
  "cts.v":         has("cts.v"),
  "routed.def":    has("routed.def"),
  "routed.v":      has("routed.v"),
  "routed.spef":   has("routed.spef"),
}

stage = "fp" if not artifacts["placed.def"] else \
        "place" if not artifacts["cts.def"] else \
        "cts" if not artifacts["routed.def"] else "done"

lines = [
  f"# PnR Report — {ip}",
  "",
  f"- date  : {date}",
  f"- stage : **{stage}**",
  "",
  "## Artifacts",
  "",
  "| file | present |",
  "|---|---|",
]
for k, v in artifacts.items():
    lines.append(f"| `{out / k}` | {'✓' if v else '—'} |")

lines += [
  "",
  "## Placement",
  "",
  f"- design area     : {density.get('design_area_um2')} μm²",
  f"- utilization     : {density.get('utilization_pct')}%",
  "",
  "## DRC",
  "",
  f"- violation count : {drc.get('drc_count', 0)}",
]
if drc.get("first_10"):
    lines.append("")
    lines.append("First 10 violations:")
    lines += [f"  - {v}" for v in drc["first_10"]]
lines += [
  "",
  "## Handoff to /sta-post",
  "",
  f"- {out / 'routed.v'}: {'ready ✓' if artifacts['routed.v'] else 'missing ✗'}",
  f"- {out / 'routed.spef'}: {'ready ✓' if artifacts['routed.spef'] else 'missing ✗'}",
  "",
]
pathlib.Path(rpt).write_text("\n".join(lines), encoding="utf-8")
print(f"[PNR] wrote {rpt}")
"""


def main(argv: "list[str]") -> int:
    argv = common.argv_from_hook(argv)

    ip = argv[0] if argv else ""
    if not ip:
        print("[PNR] usage: write_report.sh <ip>", file=sys.stderr)
        return 2

    out = f"{ip}/pnr/out"
    rpt = f"{out}/pnr.report.md"

    proc = common.run_embedded_py(_REPORT_PY, [ip, out, rpt])
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
