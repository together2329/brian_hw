#!/usr/bin/env bash
# write_report.sh — Aggregate per-stage stats into pnr.report.md.
# Args: <ip>
set -uo pipefail

if [ $# -eq 0 ] && [ -n "${HOOK_CMD_ARGS:-}" ]; then
  # shellcheck disable=SC2086
  set -- ${HOOK_CMD_ARGS}
fi

IP="${1:-}"; [ -z "${IP}" ] && { echo "[PNR] usage: write_report.sh <ip>" >&2; exit 2; }

OUT="${IP}/pnr/out"
RPT="${OUT}/pnr.report.md"

python3 - "${IP}" "${OUT}" "${RPT}" <<'PY'
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
PY
