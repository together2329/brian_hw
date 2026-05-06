#!/usr/bin/env bash
# write_report.sh — Compose <ip>/syn/out/syn.report.md from area.json + syn.log.
# Args: <ip_name>
set -uo pipefail

IP="${1:-}"
if [ -z "${IP}" ]; then echo "[SYN] usage: write_report.sh <ip_name>" >&2; exit 2; fi

OUT="${IP}/syn/out"
AREA="${OUT}/area.json"
LOG="${OUT}/syn.log"
NET="${OUT}/synth.v"
RPT="${OUT}/syn.report.md"

if [ ! -f "${AREA}" ]; then echo "[SYN] missing ${AREA}" >&2; exit 2; fi

python3 - "${IP}" "${AREA}" "${LOG}" "${NET}" "${RPT}" <<'PY'
import json, pathlib, sys, re, os, datetime
ip, area_path, log_path, net_path, rpt_path = sys.argv[1:6]
area = json.loads(pathlib.Path(area_path).read_text())
log  = pathlib.Path(log_path).read_text(errors="replace") if pathlib.Path(log_path).exists() else ""
warnings = re.findall(r"^Warning: .*$", log, re.M)[:20]
top5 = list(area.get("by_cell", {}).items())[:5]
date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

lines = [
  f"# Synthesis Report — {ip}",
  "",
  f"- date    : {date}",
  f"- top     : {area.get('top')}",
  f"- corner  : {area.get('corner')}",
  f"- netlist : {net_path}",
  f"- log     : {log_path}",
  "",
  "## Area",
  "",
  f"- total cells : {area.get('total_cells')}",
  f"- total area  : {area.get('total_area_um2')} μm²",
  f"- sequential  : {area['by_kind']['sequential']['cells']} cells",
  f"- combinational: {area['by_kind']['combinational']['cells']} cells",
  "",
  "## Top cell types",
  "",
  "| cell | count |",
  "|---|---|",
] + [f"| `{k}` | {v} |" for k, v in top5] + [
  "",
  "## Warnings (first 20)",
  "",
]
if warnings:
    lines += [f"- {w}" for w in warnings]
else:
    lines.append("_(none)_")
lines.append("")
pathlib.Path(rpt_path).write_text("\n".join(lines))
print(f"[SYN] wrote {rpt_path}")
PY
