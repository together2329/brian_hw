#!/usr/bin/env bash
# write_report.sh — Compose <ip>/sta/out/sta.report.md from wns.json + sta.log.
# Args: <ip_name>
set -uo pipefail

if [ $# -eq 0 ] && [ -n "${HOOK_CMD_ARGS:-}" ]; then
  # shellcheck disable=SC2086
  set -- ${HOOK_CMD_ARGS}
fi

IP="${1:-}"
if [ -z "${IP}" ]; then echo "[STA] usage: write_report.sh <ip_name>" >&2; exit 2; fi

OUT="${IP}/sta/out"
JSON="${OUT}/wns.json"
LOG="${OUT}/sta.log"
RPT="${OUT}/sta.report.md"
if [ ! -f "${JSON}" ]; then echo "[STA] missing ${JSON}" >&2; exit 2; fi

python3 - "${IP}" "${JSON}" "${LOG}" "${RPT}" <<'PY'
import json, pathlib, sys, re, datetime
ip, json_p, log_p, rpt_p = sys.argv[1:5]
d = json.loads(pathlib.Path(json_p).read_text())
log = pathlib.Path(log_p).read_text(errors="replace") if pathlib.Path(log_p).exists() else ""
date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
errors = re.findall(r"^Error: .*$",   log, re.M)[:10]
warns  = re.findall(r"^Warning: .*$", log, re.M)[:10]

result = "PASS" if d['summary'].get('all_setup_met') and d['summary'].get('all_hold_met') else \
         ("HOLD FAIL" if not d['summary'].get('all_hold_met') else "SETUP FAIL")

lines = [
  f"# STA Report — {ip}",
  "",
  f"- date    : {date}",
  f"- top     : {d.get('top')}",
  f"- corner  : {d.get('corner')}",
  f"- result  : **{result}**",
  "",
  "## Per-clock summary",
  "",
  "| clock | period (ns) | setup WNS | setup TNS | setup viol | hold WNS | hold viol |",
  "|---|---|---|---|---|---|---|",
]
for c in d.get('clocks', []):
    fmt = lambda x: f"{x:.3f}" if isinstance(x, (int, float)) else "n/a"
    lines.append(f"| `{c['name']}` | {c['period_ns']} | {fmt(c['setup_wns_ns'])} | {fmt(c['setup_tns_ns'])} | {c['setup_violations']} | {fmt(c['hold_wns_ns'])} | {c['hold_violations']} |")

lines += [
  "",
  "## Worst paths",
  "",
  f"- setup: {d['summary'].get('worst_setup_path') or '_(none)_'}",
  f"- hold : {d['summary'].get('worst_hold_path') or '_(none)_'}",
  "",
]

if errors or warns:
    lines.append("## Tool messages")
    lines.append("")
    for w in warns:  lines.append(f"- {w}")
    for e in errors: lines.append(f"- **{e}**")
    lines.append("")

if "FAIL" in result:
    lines += [
      "## Next steps",
      "",
      "Setup violations → tighten clock period in SSOT, re-run `/syn`, then `/sta`.",
      "Hold violations  → check async / CDC paths in SSOT `false_paths` first; otherwise fix in RTL.",
      "",
    ]

pathlib.Path(rpt_p).write_text("\n".join(lines))
print(f"[STA] wrote {rpt_p}")
PY
