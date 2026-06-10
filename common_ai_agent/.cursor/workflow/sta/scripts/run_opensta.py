#!/usr/bin/env python3
"""run_opensta.py — Invoke OpenSTA on <ip>/sta/run.tcl; capture output to sta.log.

Python port of run_opensta.sh. Reproduces the bash pipeline
``sta ... 2>&1 | tee "$LOG" | tail -120`` with ``RC=${PIPESTATUS[0]}``: the full
merged stdout+stderr is written to the log, the last 120 lines are echoed to
stdout, and the process exit code is sta's own (not tee/tail).

Usage: run_opensta.py <ip_name>
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _sh_port_common import load_pdk_env  # noqa: E402


def main(argv: list[str]) -> int:
    if not argv and os.environ.get("HOOK_CMD_ARGS"):
        argv = os.environ["HOOK_CMD_ARGS"].split()

    env = load_pdk_env()

    ip = argv[0] if argv else ""
    if not ip:
        print("[STA] usage: run_opensta.py <ip_name>", file=sys.stderr)
        return 2

    tcl = f"{ip}/sta/run.tcl"
    log = f"{ip}/sta/out/sta.log"
    Path(f"{ip}/sta/out").mkdir(parents=True, exist_ok=True)

    if not Path(tcl).is_file():
        print(
            f"[STA] missing {tcl} — run /sta-sdc and write_sta_tcl first",
            file=sys.stderr,
        )
        return 2
    if shutil.which("sta") is None:
        print("[STA TOOL MISSING] OpenSTA 'sta' not on PATH", file=sys.stderr)
        return 3
    sky130_lib = env.get("SKY130_LIB") or os.environ.get("SKY130_LIB", "")
    if not sky130_lib or not os.access(sky130_lib, os.R_OK):
        print("[STA MISSING PDK] $SKY130_LIB unreadable", file=sys.stderr)
        return 4

    # sta -no_init -no_splash -exit "$TCL" 2>&1 | tee "$LOG" | tail -120
    proc = subprocess.run(
        ["sta", "-no_init", "-no_splash", "-exit", tcl],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    rc = proc.returncode  # PIPESTATUS[0]
    captured = proc.stdout or b""
    Path(log).write_bytes(captured)  # tee "$LOG"

    # tail -120 of the merged output to stdout.
    text = captured.decode("utf-8", errors="replace")
    had_trailing_nl = text.endswith("\n")
    lines = text.split("\n")
    if had_trailing_nl:
        lines = lines[:-1]
    tail = lines[-120:]
    if tail:
        sys.stdout.write("\n".join(tail) + "\n")
        sys.stdout.flush()

    print(f"[STA] sta rc={rc} log={log}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
