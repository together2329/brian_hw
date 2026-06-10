#!/usr/bin/env python3
"""write_report.py — Port of write_report.sh (DFT).

Compose <ip>/dft/out/dft.report.md from scan_chains.json (+ coverage.json if
Fault ATPG ran).  Args: <ip_name>
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


# The report body is a single python heredoc in the bash original; run it
# verbatim so the emitted markdown is byte-for-byte identical.
_REPORT_PY = r"""
import json, pathlib, sys, datetime
ip, json_p, cov_p, log_p, rpt_p = sys.argv[1:6]
d = json.loads(pathlib.Path(json_p).read_text(encoding="utf-8", errors="replace"))
cov = None
if pathlib.Path(cov_p).exists():
    try: cov = json.loads(pathlib.Path(cov_p).read_text(encoding="utf-8", errors="replace"))
    except Exception: cov = None
date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

mode = d['summary'].get('mode', 'scan_insert')
header = "_passthrough_ (DFT not enabled in SSOT)" if mode == "passthrough" else f"**{mode}** ({d.get('tool')})"

lines = [
  f"# DFT Report — {ip}",
  "",
  f"- date    : {date}",
  f"- top     : {d.get('top')}",
  f"- mode    : {header}",
  "",
]
if mode == "passthrough":
    lines += [
      "PnR will consume `<ip>/syn/out/synth.v` (copied to `scan.v`) directly.",
      "Enable in SSOT to insert scan chains:",
      "",
      "```yaml",
      "dft:",
      "  enabled: true",
      "  scan_enable_port: scan_en",
      "  max_chains: 4",
      "  max_chain_length: 100",
      "```",
      "",
    ]
else:
    s = d['summary']
    lines += [
      f"- scan_enable_port: `{s.get('scan_enable_port')}`",
      f"- total FFs       : {s.get('total_ffs')}",
      f"- FFs in chains   : {s.get('ffs_in_chains')}",
      f"- FFs skipped     : {s.get('ffs_skipped')}",
      f"- chains          : {s.get('chains')}",
      f"- chain length    : min={s.get('min_length')}, max={s.get('max_length')}",
      "",
      "## Per-chain detail",
      "",
      "| id | length | scan_in | scan_out | clock |",
      "|---|---|---|---|---|",
    ] + [
      f"| {c['id']} | {c['length']} | `{c['scan_in']}` | `{c['scan_out']}` | `{c['clock']}` |"
      for c in d.get('scan_chains', [])
    ] + [""]

if cov:
    lines += [
      "## ATPG (Fault)",
      "",
      f"- fault model     : `{cov.get('fault_model') or 'stuck_at'}`",
      f"- coverage        : {(cov.get('coverage') or 0)*100:.2f}%",
      f"- target          : {(cov.get('target') or 0)*100:.0f}%",
      f"- below target?   : {'**YES — investigate untested logic**' if cov.get('below_target') else 'no'}",
      "",
    ]

lines += [
  "## Open-source DFT gaps (informational)",
  "",
  "These are NOT inserted by the workflow:",
  "- MBIST (memory BIST) — add via RTL boilerplate if needed",
  "- JTAG / IEEE 1149.1 boundary scan — manual RTL",
  "- Logic BIST / PRPG / MISR",
  "- Test compression (chain compaction)",
  "",
]
pathlib.Path(rpt_p).write_text("\n".join(lines), encoding="utf-8")
print(f"[DFT] wrote {rpt_p}")
"""


def main(argv: "list[str]") -> int:
    ip = argv[0] if argv else ""
    if not ip:
        print("[DFT] usage: write_report.sh <ip_name>", file=sys.stderr)
        return 2

    out = f"{ip}/dft/out"
    json_p = f"{out}/scan_chains.json"
    cov = f"{out}/coverage.json"
    log = f"{out}/dft.log"
    rpt = f"{out}/dft.report.md"
    if not Path(json_p).is_file():
        print(f"[DFT] missing {json_p}", file=sys.stderr)
        return 2

    # Feed the body on stdin (`python3 -`) so tracebacks report File "<stdin>".
    proc = subprocess.run(
        [sys.executable, "-", ip, json_p, cov, log, rpt],
        input=_REPORT_PY.lstrip("\n"),
        text=True,
    )
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
