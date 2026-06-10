#!/usr/bin/env python3
"""lint.py — Python port of lint.sh (rtl-gen).

RTL lint for the rtl_gen workspace.

CLI / env contract preserved:
  * FILE = ``$HOOK_CMD_ARGS`` else first positional argument; if empty, the
    default is ``find . -maxdepth 2 \\( -name '*.sv' -o -name '*.v' \\) |
    grep -v '^./tb_' | grep -v '^./tc_' | head -5`` (a space-separated list).
    Empty ⇒ ``No RTL files found.`` and exit 1.
  * For each file: prefer ``verilator --lint-only -Wall``, else
    ``iverilog -Wall -g2012 -o /dev/null``, else ``No lint tool ...`` exit 1.
  * Per file: if there was output, print ``--- <f> ---`` then the output, else
    ``--- <f>: OK ---``.  Sum error/warning counts (``grep -c -i``), print the
    totals, append a benchmark log line, exit 0 iff zero errors.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path


_ERROR_RE = re.compile(r"error", re.IGNORECASE)
_WARNING_RE = re.compile(r"warning", re.IGNORECASE)


def _count_lines(pattern: "re.Pattern[str]", text: str) -> int:
    if not text:
        return 0
    return sum(1 for line in text.splitlines() if pattern.search(line))


def _default_files() -> "list[str]":
    cmd = (
        r"""find . -maxdepth 2 \( -name "*.sv" -o -name "*.v" \) """
        r"""| grep -v "^./tb_" | grep -v "^./tc_" | head -5"""
    )
    proc = subprocess.run(["/bin/sh", "-c", cmd], capture_output=True, text=True)
    return proc.stdout.split()


def main(argv: "list[str] | None" = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    log = os.environ.get("BENCHMARK_LOG", ".benchmark")
    ts = time.strftime("%Y-%m-%dT%H:%M:%S")

    file_arg = os.environ.get("HOOK_CMD_ARGS") or (argv[0] if argv else "")
    if file_arg:
        # Bash word-splits the (unquoted) ${FILE} list in the for-loop.
        files = file_arg.split()
    else:
        files = _default_files()

    if not files:
        print("No RTL files found.")
        return 1

    errors = 0
    warnings = 0
    have_verilator = shutil.which("verilator") is not None
    have_iverilog = shutil.which("iverilog") is not None

    for f in files:
        if have_verilator:
            cmd = ["verilator", "--lint-only", "-Wall", f]
        elif have_iverilog:
            cmd = ["iverilog", "-Wall", "-g2012", "-o", "/dev/null", f]
        else:
            print("No lint tool (install verilator or iverilog)")
            return 1

        proc = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
        )
        # Bash: OUT=$(... 2>&1) — command substitution strips trailing newlines.
        out = proc.stdout.rstrip("\n")
        errors += _count_lines(_ERROR_RE, out)
        warnings += _count_lines(_WARNING_RE, out)
        if out:
            print(f"--- {f} ---")
            print(out)  # echo "${OUT}" re-adds a single trailing newline
        else:
            print(f"--- {f}: OK ---")

    print()
    print(f"Lint: {errors} errors, {warnings} warnings")
    with open(log, "a", encoding="utf-8") as handle:
        handle.write(f"{ts} lint errors={errors} warnings={warnings}\n")

    return 0 if errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
