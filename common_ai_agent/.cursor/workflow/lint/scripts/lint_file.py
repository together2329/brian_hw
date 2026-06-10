#!/usr/bin/env python3
"""lint_file.py — Run lint on a single file.

Python port of lint_file.sh. File comes from $HOOK_CMD_ARGS or argv[1]. Lints
with verilator (iverilog fallback), prints the tool output (or "OK — no issues"),
a per-file summary, appends a benchmark line, and exits 0 iff zero errors.

Usage: lint_file.py <file.sv>
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


def main(argv: list[str]) -> int:
    file = os.environ.get("HOOK_CMD_ARGS") or (argv[0] if argv else "")
    log = os.environ.get("BENCHMARK_LOG", ".benchmark")
    ts = time.strftime("%Y-%m-%dT%H:%M:%S")

    if not file:
        print("Usage: /lint-file <file.sv>")
        return 1
    if not Path(file).is_file():
        print(f"File not found: {file}")
        return 1

    if shutil.which("verilator") is not None:
        proc = subprocess.run(
            ["verilator", "--lint-only", "-Wall", file],
            capture_output=True,
            text=True,
        )
    elif shutil.which("iverilog") is not None:
        proc = subprocess.run(
            ["iverilog", "-Wall", "-g2012", "-o", "/dev/null", file],
            capture_output=True,
            text=True,
        )
    else:
        print("No lint tool found")
        return 1

    out = (proc.stdout or "") + (proc.stderr or "")
    err = sum(1 for ln in out.splitlines() if "error" in ln.lower())
    warn = sum(1 for ln in out.splitlines() if "warning" in ln.lower())

    # [ -n "$OUT" ] && echo "$OUT" || echo "OK — no issues"
    if out:
        # echo "$OUT" prints the captured output followed by a single newline;
        # bash strips the trailing newline from $(...) capture, so re-add one.
        print(out.rstrip("\n"))
    else:
        print("OK — no issues")
    print("")
    print(f"{file}: {err} errors, {warn} warnings")

    with open(log, "a", encoding="utf-8") as fh:
        fh.write(f"{ts} lint_file={file} errors={err} warnings={warn}\n")

    return 0 if err == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
