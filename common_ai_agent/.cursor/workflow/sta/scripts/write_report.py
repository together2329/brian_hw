#!/usr/bin/env python3
"""write_report.py — Compose <ip>/sta/out/sta.report.md from wns.json + sta.log.

Python port of write_report.sh; a 1:1 translation of its embedded python heredoc.

Usage: write_report.py <ip_name>
"""

from __future__ import annotations

import datetime
import json
import os
import re
import sys
from pathlib import Path


def _run(ip: str, json_p: str, log_p: str, rpt_p: str) -> None:
    d = json.loads(Path(json_p).read_text(encoding="utf-8", errors="replace"))
    log = (
        Path(log_p).read_text(encoding="utf-8", errors="replace")
        if Path(log_p).exists()
        else ""
    )
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    errors = re.findall(r"^Error: .*$", log, re.M)[:10]
    warns = re.findall(r"^Warning: .*$", log, re.M)[:10]

    result = (
        "PASS"
        if d["summary"].get("all_setup_met") and d["summary"].get("all_hold_met")
        else ("HOLD FAIL" if not d["summary"].get("all_hold_met") else "SETUP FAIL")
    )

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
    for c in d.get("clocks", []):
        fmt = lambda x: f"{x:.3f}" if isinstance(x, (int, float)) else "n/a"  # noqa: E731
        lines.append(
            f"| `{c['name']}` | {c['period_ns']} | {fmt(c['setup_wns_ns'])} | "
            f"{fmt(c['setup_tns_ns'])} | {c['setup_violations']} | "
            f"{fmt(c['hold_wns_ns'])} | {c['hold_violations']} |"
        )

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
        for w in warns:
            lines.append(f"- {w}")
        for e in errors:
            lines.append(f"- **{e}**")
        lines.append("")

    if "FAIL" in result:
        lines += [
            "## Next steps",
            "",
            "Setup violations → tighten clock period in SSOT, re-run `/syn`, then `/sta`.",
            "Hold violations  → check async / CDC paths in SSOT `false_paths` first; otherwise fix in RTL.",
            "",
        ]

    Path(rpt_p).write_text("\n".join(lines), encoding="utf-8")
    print(f"[STA] wrote {rpt_p}")


def main(argv: list[str]) -> int:
    if not argv and os.environ.get("HOOK_CMD_ARGS"):
        argv = os.environ["HOOK_CMD_ARGS"].split()

    ip = argv[0] if argv else ""
    if not ip:
        print("[STA] usage: write_report.py <ip_name>", file=sys.stderr)
        return 2

    out = f"{ip}/sta/out"
    json_p = f"{out}/wns.json"
    log = f"{out}/sta.log"
    rpt = f"{out}/sta.report.md"
    if not Path(json_p).is_file():
        print(f"[STA] missing {json_p}", file=sys.stderr)
        return 2

    _run(ip, json_p, log, rpt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
