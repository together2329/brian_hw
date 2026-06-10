#!/usr/bin/env python3
"""write_report.py — Generate lint_report.txt from .benchmark log.

Python port of write_report.sh. Reads the last lint line from $BENCHMARK_LOG,
extracts errors=/warnings= counts, lists RTL files, picks the tool, and writes
``lint_report.txt`` (also echoed to stdout).

Usage: write_report.py
"""

from __future__ import annotations

import os
import re
import shutil
import sys
import time
from pathlib import Path


def _grep_lines(path: str, needle: str) -> list[str]:
    p = Path(path)
    if not p.is_file():
        return []
    return [
        ln
        for ln in p.read_text(encoding="utf-8", errors="replace").splitlines()
        if needle in ln
    ]


def _find_rtl_str() -> str:
    """find . -maxdepth 3 \\( -name '*.sv' -o -name '*.v' \\)
    | grep -v 'tb_\\|tc_' | sort | tr '\\n' ' '."""
    matches: list[str] = []
    root = Path(".")
    for pat in ("*.sv", "*.v", "*/*.sv", "*/*.v", "*/*/*.sv", "*/*/*.v"):
        for p in root.glob(pat):
            if p.is_file():
                matches.append("./" + p.as_posix())
    filtered = [m for m in matches if "tb_" not in m and "tc_" not in m]
    ordered = sorted(set(filtered))
    # tr '\n' ' ' turns each line + its newline into "<path> ", trailing space kept.
    return "".join(f"{m} " for m in ordered)


def main(argv: list[str]) -> int:
    log = os.environ.get("BENCHMARK_LOG", ".benchmark")
    out = "lint_report.txt"
    ts = time.strftime("%Y-%m-%dT%H:%M:%S")

    lint_lines = _grep_lines(log, "lint")
    last = lint_lines[-1] if lint_lines else ""

    m_e = re.search(r"errors=(\d+)", last)
    errors = m_e.group(1) if m_e else "?"
    m_w = re.search(r"warnings=(\d+)", last)
    warnings = m_w.group(1) if m_w else "?"

    files = _find_rtl_str()
    tool = "verilator" if shutil.which("verilator") is not None else "iverilog"

    # $(grep "lint.*errors=[^0]" LOG | tail -5 || echo "NONE")
    err_lines = [ln for ln in _grep_lines(log, "lint") if re.search(r"errors=[^0]", ln)]
    err_block = "\n".join(err_lines[-5:]) if err_lines else "NONE"

    issue_lines = _grep_lines(log, "lint_issues")
    issue_block = "\n".join(issue_lines[-20:]) if issue_lines else "NONE"

    text = (
        "=== Lint Report ===\n"
        f"Date  : {ts}\n"
        f"Files : {files}\n"
        f"Tool  : {tool}\n"
        f"Result: {errors} errors, {warnings} warnings\n"
        "\n"
        "[Errors]\n"
        f"{err_block}\n"
        "\n"
        "[Issues Log]\n"
        f"{issue_block}\n"
    )
    Path(out).write_text(text, encoding="utf-8")

    print(f"Written: {out}")
    # cat "$OUT": echo the file contents verbatim.
    sys.stdout.write(text)
    sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
