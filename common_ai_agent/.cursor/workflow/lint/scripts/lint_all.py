#!/usr/bin/env python3
"""lint_all.py — Run lint on all .sv/.v files (exclude tb_/tc_).

Python port of lint_all.sh. Finds RTL under ``find . -maxdepth 3``, excludes
tb_/tc_/_wave//sim/, lints each with verilator (iverilog fallback), prints a
per-file block + a TOTAL line, appends a benchmark line, and exits 0 iff zero
total errors.

Usage: lint_all.py
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


def _find_rtl() -> list[str]:
    """Reproduce: find . -maxdepth 3 \\( -name '*.sv' -o -name '*.v' \\)
    | grep -v 'tb_\\|tc_\\|_wave\\|/sim/' | sort."""
    matches: list[str] = []
    root = Path(".")
    # find . -maxdepth 3: depth 1..3 relative to '.'
    for pat in ("*.sv", "*.v", "*/*.sv", "*/*.v", "*/*/*.sv", "*/*/*.v"):
        for p in root.glob(pat):
            if p.is_file():
                matches.append("./" + p.as_posix())
    # grep -v on the path string
    filtered = [
        m for m in matches if not any(t in m for t in ("tb_", "tc_", "_wave", "/sim/"))
    ]
    return sorted(set(filtered))


def main(argv: list[str]) -> int:
    log = os.environ.get("BENCHMARK_LOG", ".benchmark")
    ts = time.strftime("%Y-%m-%dT%H:%M:%S")

    files = _find_rtl()
    if not files:
        print("No RTL files found.")
        return 1

    have_verilator = shutil.which("verilator") is not None
    have_iverilog = shutil.which("iverilog") is not None

    total_err = 0
    total_warn = 0
    for f in files:
        if have_verilator:
            proc = subprocess.run(
                ["verilator", "--lint-only", "-Wall", f],
                capture_output=True,
                text=True,
            )
        elif have_iverilog:
            proc = subprocess.run(
                ["iverilog", "-Wall", "-g2012", "-o", "/dev/null", f],
                capture_output=True,
                text=True,
            )
        else:
            print("No lint tool found (install verilator or iverilog)")
            return 1
        out = (proc.stdout or "") + (proc.stderr or "")
        err = sum(1 for ln in out.splitlines() if "error" in ln.lower())
        warn = sum(1 for ln in out.splitlines() if "warning" in ln.lower())
        total_err += err
        total_warn += warn
        if out:
            print(f"=== {f} === ({err} errors, {warn} warnings)")
            print(out.rstrip("\n"))
        else:
            print(f"=== {f} === OK")

    print("")
    print(f"TOTAL: {total_err} errors, {total_warn} warnings")
    with open(log, "a", encoding="utf-8") as fh:
        fh.write(f"{ts} lint_all errors={total_err} warnings={total_warn}\n")

    return 0 if total_err == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
