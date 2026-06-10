#!/usr/bin/env python3
"""write_report.py — Compose <ip>/syn/out/syn.report.md from area.json + syn.log.

Python port of write_report.sh for native-Windows portability. Same CLI, exit
codes, and byte-identical report output (modulo the embedded timestamp, which
the shell original also makes nondeterministic via datetime.now()).

Args: <ip_name>

Falls back to HOOK_CMD_ARGS for the IP name when no positional arg is given
(matching the shell original).

Exit codes: 2 usage / missing area.json.
"""

from __future__ import annotations

import datetime
import json
import os
import pathlib
import re
import shlex
import sys
from pathlib import Path

# Import the pdk_env port to mirror the shell `source pdk_env.sh` (no-op for the
# report body, but keeps the environment parity with the .sh pipeline).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
import pdk_env  # noqa: E402


def _resolve_ip(argv: list[str]) -> str:
    args = list(argv)
    if not args and os.environ.get("HOOK_CMD_ARGS", ""):
        args = shlex.split(os.environ["HOOK_CMD_ARGS"])
    return args[0] if args else ""


def _emit_report(
    ip: str, area_path: str, log_path: str, net_path: str, rpt_path: str
) -> None:
    """Body of the shell heredoc, verbatim semantics."""
    area = json.loads(
        pathlib.Path(area_path).read_text(encoding="utf-8", errors="replace")
    )
    log = (
        pathlib.Path(log_path).read_text(encoding="utf-8", errors="replace")
        if pathlib.Path(log_path).exists()
        else ""
    )
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
    pathlib.Path(rpt_path).write_text("\n".join(lines), encoding="utf-8")
    print(f"[SYN] wrote {rpt_path}")


def main(argv: list[str]) -> int:
    ip = _resolve_ip(argv)
    if not ip:
        print("[SYN] usage: write_report.sh <ip_name>", file=sys.stderr)
        return 2

    pdk_env.apply_pdk_env(os.environ)

    out = f"{ip}/syn/out"
    area = f"{out}/area.json"
    log = f"{out}/syn.log"
    net = f"{out}/synth.v"
    rpt = f"{out}/syn.report.md"

    if not Path(area).is_file():
        print(f"[SYN] missing {area}", file=sys.stderr)
        return 2

    _emit_report(ip, area, log, net, rpt)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
