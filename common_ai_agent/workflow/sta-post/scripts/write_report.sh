#!/usr/bin/env bash
# write_report.sh — Compose <ip>/sta-post/out/sta.report.md, including
# pre-vs-post delta when /sta wns.json exists.
# Args: <ip>
set -uo pipefail

IP="${1:-}"
if [ -z "${IP}" ]; then echo "[STA-POST] usage: write_report.sh <ip>" >&2; exit 2; fi

OUT="${IP}/sta-post/out"
JSON="${OUT}/wns.json"
PRE_JSON="${IP}/sta/out/wns.json"
RPT="${OUT}/sta.report.md"

[ ! -f "${JSON}" ] && { echo "[STA-POST] missing ${JSON}" >&2; exit 2; }

python3 - "${IP}" "${JSON}" "${PRE_JSON}" "${RPT}" <<'PY'
import json, pathlib, sys, datetime
ip, post_p, pre_p, rpt_p = sys.argv[1:5]
post = json.loads(pathlib.Path(post_p).read_text())
pre  = None
if pathlib.Path(pre_p).exists():
    try: pre = json.loads(pathlib.Path(pre_p).read_text())
    except Exception: pass

date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
result = "PASS" if post['summary'].get('all_setup_met') and post['summary'].get('all_hold_met') else \
         ("HOLD FAIL" if not post['summary'].get('all_hold_met') else "SETUP FAIL")

lines = [
  f"# Post-Route STA Report — {ip}",
  "",
  f"- date    : {date}",
  f"- top     : {post.get('top')}",
  f"- corner  : {post.get('corner')}",
  f"- mode    : **{post.get('mode')}** (parasitic-aware sign-off)",
  f"- result  : **{result}**",
  "",
  "## Per-clock summary",
  "",
  "| clock | period (ns) | setup WNS | setup TNS | setup viol | hold WNS | hold viol | skew (ps) |",
  "|---|---|---|---|---|---|---|---|",
]
def fmt(x, p=3): return f"{x:.{p}f}" if isinstance(x, (int, float)) else "n/a"
for c in post.get("clocks", []):
    lines.append(f"| `{c['name']}` | {c['period_ns']} | {fmt(c['setup_wns_ns'])} | {fmt(c['setup_tns_ns'])} | {c['setup_violations']} | {fmt(c['hold_wns_ns'])} | {c['hold_violations']} | {fmt(c.get('max_skew_ps'), 1)} |")

# Delta vs /sta if pre-route data exists
if pre:
    pre_by = {c['name']: c for c in pre.get('clocks', [])}
    lines += [
      "",
      "## Pre-route /sta vs sign-off /sta-post",
      "",
      "Setup degrades when real net delays are counted. A positive Δ (less negative or improved) is suspicious — usually missing SDC or empty SPEF.",
      "",
      "| clock | pre setup_wns | post setup_wns | Δ | pre hold_wns | post hold_wns | Δ |",
      "|---|---|---|---|---|---|---|",
    ]
    for c in post.get('clocks', []):
        p = pre_by.get(c['name'])
        if not p: continue
        d_s = (c['setup_wns_ns'] - p['setup_wns_ns']) if (c['setup_wns_ns'] is not None and p.get('setup_wns_ns') is not None) else None
        d_h = (c['hold_wns_ns']  - p['hold_wns_ns'])  if (c['hold_wns_ns']  is not None and p.get('hold_wns_ns')  is not None) else None
        suspicious = (d_s is not None and d_s > 0)
        flag = " ⚠️" if suspicious else ""
        lines.append(f"| `{c['name']}` | {fmt(p.get('setup_wns_ns'))} | {fmt(c['setup_wns_ns'])} | {fmt(d_s)}{flag} | {fmt(p.get('hold_wns_ns'))} | {fmt(c['hold_wns_ns'])} | {fmt(d_h)} |")
    lines.append("")
    if any((c['setup_wns_ns'] is not None and pre_by.get(c['name'], {}).get('setup_wns_ns') is not None
            and (c['setup_wns_ns'] - pre_by[c['name']]['setup_wns_ns']) > 0) for c in post.get('clocks', [])):
        lines += [
          "**⚠️ Setup WNS improved post-route** — investigate. Possible causes:",
          "- SPEF empty / not loaded → check `read_spef` in run.tcl, file size",
          "- Wrong corner liberty",
          "- SDC not loaded → check `read_sdc`",
          "",
        ]

if "FAIL" in result:
    lines += [
      "## Next steps",
      "",
      "Setup violations → re-floorplan with lower utilization, or change CTS buffer list.",
      "Hold violations  → check `false_paths` in SSOT for async/CDC, then add hold buffers (rerun /pnr-route with `-fix_hold`).",
      "",
    ]

pathlib.Path(rpt_p).write_text("\n".join(lines))
print(f"[STA-POST] wrote {rpt_p}")
PY
