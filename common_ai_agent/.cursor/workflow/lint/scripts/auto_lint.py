#!/usr/bin/env python3
"""auto_lint.py — Auto-triggered after every .sv/.v write; quick lint of file.

Python port of auto_lint.sh. Extracts the changed file from $HOOK_TOOL_ARGS,
lints it with verilator (or iverilog fallback), and appends a benchmark line
``<ts> auto_lint file=<f> errors=<E> warnings=<W>`` to $BENCHMARK_LOG (default
.benchmark). Exit 0 always (matches the bash early-exit-0 + implicit success).

Usage: auto_lint.py   (driven entirely by env: HOOK_TOOL_ARGS, BENCHMARK_LOG)
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path


def _extract_file(args: str) -> str:
    """Reproduce grep -oP '(?<=path=")[^"]+|(?<=")[^"]+\\.(?:sv|v)' | head -1."""
    # First alternative: a value following path="
    m = re.search(r'(?<=path=")[^"]+', args)
    if m:
        return m.group(0)
    # Second alternative: any quoted token ending in .sv/.v
    m = re.search(r'(?<=")[^"]+\.(?:sv|v)', args)
    if m:
        return m.group(0)
    return ""


def main(argv: list[str]) -> int:
    log = os.environ.get("BENCHMARK_LOG", ".benchmark")
    ts = time.strftime("%Y-%m-%dT%H:%M:%S")
    args = os.environ.get("HOOK_TOOL_ARGS", "")
    file = _extract_file(args)

    # [ -z "$FILE" ] || [ ! -f "$FILE" ] && exit 0
    if not file or not Path(file).is_file():
        return 0

    if shutil.which("verilator") is not None:
        out = subprocess.run(
            ["verilator", "--lint-only", "-Wall", file],
            capture_output=True,
            text=True,
        )
    else:
        out = subprocess.run(
            ["iverilog", "-Wall", "-g2012", "-o", "/dev/null", file],
            capture_output=True,
            text=True,
        )
    combined = (out.stdout or "") + (out.stderr or "")

    # grep -c -i "error" / "warning": count lines containing the term.
    err = sum(1 for ln in combined.splitlines() if "error" in ln.lower())
    warn = sum(1 for ln in combined.splitlines() if "warning" in ln.lower())

    with open(log, "a", encoding="utf-8") as fh:
        fh.write(f"{ts} auto_lint file={file} errors={err} warnings={warn}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
