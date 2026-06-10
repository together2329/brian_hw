#!/usr/bin/env python3
"""syn_check.py — Python port of syn_check.sh (rtl-gen).

Synthesis feasibility check.

CLI / env contract preserved:
  * FILE = ``$HOOK_CMD_ARGS`` else first positional argument; if empty, the
    default is ``find . -maxdepth 1 -name '*.sv' | grep -v 'tb_' | head -1``.
    Empty ⇒ ``No RTL file found.`` and exit 1.
  * If ``yosys`` is on PATH: run ``yosys -p 'read_verilog -sv <f>; synth'``,
    count ``ERROR`` lines (case-sensitive ``grep -c "ERROR"``), log + exit 0
    iff zero.
  * Else: ``iverilog -Wall -Winfloop -g2012 -o /dev/null <f>``, count
    ``error`` lines (case-sensitive ``grep -c "error"``), log + exit 0 iff zero.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time


def _count(needle: str, text: str) -> int:
    # grep -c "<needle>" : count of lines containing the literal needle.
    if not text:
        return 0
    return sum(1 for line in text.splitlines() if needle in line)


def _default_file() -> str:
    cmd = r"""find . -maxdepth 1 -name "*.sv" | grep -v "tb_" | head -1"""
    proc = subprocess.run(["/bin/sh", "-c", cmd], capture_output=True, text=True)
    return proc.stdout.strip()


def main(argv: "list[str] | None" = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    log = os.environ.get("BENCHMARK_LOG", ".benchmark")
    ts = time.strftime("%Y-%m-%dT%H:%M:%S")

    file = os.environ.get("HOOK_CMD_ARGS") or (argv[0] if argv else "")
    if not file:
        file = _default_file()
    if not file:
        print("No RTL file found.")
        return 1

    if shutil.which("yosys") is not None:
        proc = subprocess.run(
            ["yosys", "-p", f"read_verilog -sv {file}; synth"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
        )
        out = proc.stdout.rstrip("\n")
        print(out)
        errors = _count("ERROR", out)
        print()
        print(f"Yosys: {errors} errors")
        with open(log, "a", encoding="utf-8") as handle:
            handle.write(f"{ts} syn_check=yosys errors={errors} file={file}\n")
        return 0 if errors == 0 else 1

    # Fallback: strict iverilog compile.
    print("Yosys not found. Running strict iverilog compile...")
    proc = subprocess.run(
        ["iverilog", "-Wall", "-Winfloop", "-g2012", "-o", "/dev/null", file],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    out = proc.stdout.rstrip("\n")
    print(out)
    errors = _count("error", out)
    print()
    print(f"iverilog strict: {errors} errors")
    with open(log, "a", encoding="utf-8") as handle:
        handle.write(f"{ts} syn_check=iverilog errors={errors} file={file}\n")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
