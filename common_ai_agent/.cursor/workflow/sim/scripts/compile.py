#!/usr/bin/env python3
"""compile.py — Python port of compile.sh (sim).

Compile-only check of a testbench.

CLI / env contract preserved:
  * TB = ``$HOOK_CMD_ARGS`` else first positional argument; if empty, the
    default is ``find . -maxdepth 3 -name 'tb_*.sv' | head -1``.  Empty ⇒
    ``No TB found.`` and exit 1.
  * If ``iverilog`` is on PATH: ``iverilog -g2012 -Wall -o
    /tmp/_sim_compile_only.vvp <TB>`` (2>&1), else ``verilator --lint-only
    -Wall <TB>`` (2>&1).
  * Print the captured output, the error count (``grep -c -i "error"``) as
    ``Compile: N errors``, append a benchmark log line, and exit with the
    compiler's return code (``[ "${RC}" -eq 0 ]``).
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import time


_ERROR_RE = re.compile(r"error", re.IGNORECASE)


def _count_lines(pattern: "re.Pattern[str]", text: str) -> int:
    if not text:
        return 0
    return sum(1 for line in text.splitlines() if pattern.search(line))


def _default_tb() -> str:
    proc = subprocess.run(
        ["/bin/sh", "-c", 'find . -maxdepth 3 -name "tb_*.sv" | head -1'],
        capture_output=True, text=True,
    )
    return proc.stdout.strip()


def main(argv: "list[str] | None" = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    tb = os.environ.get("HOOK_CMD_ARGS") or (argv[0] if argv else "")
    log = os.environ.get("BENCHMARK_LOG", ".benchmark")
    ts = time.strftime("%Y-%m-%dT%H:%M:%S")

    if not tb:
        tb = _default_tb()
    if not tb:
        print("No TB found.")
        return 1

    if shutil.which("iverilog") is not None:
        cmd = ["iverilog", "-g2012", "-Wall", "-o", "/tmp/_sim_compile_only.vvp", tb]
    else:
        cmd = ["verilator", "--lint-only", "-Wall", tb]

    proc = subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    rc = proc.returncode
    out = proc.stdout.rstrip("\n")  # OUT=$(... 2>&1)

    print(out)  # echo "${OUT}"
    errors = _count_lines(_ERROR_RE, out)
    print()
    print(f"Compile: {errors} errors")
    with open(log, "a", encoding="utf-8") as handle:
        handle.write(f"{ts} compile errors={errors} tb={tb}\n")

    # Bash final line: [ "${RC}" -eq 0 ]  → exit status mirrors compile rc.
    return 0 if rc == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
