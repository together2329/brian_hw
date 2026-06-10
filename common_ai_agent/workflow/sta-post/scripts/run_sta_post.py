#!/usr/bin/env python3
"""run_sta_post.py — Invoke OpenSTA on <ip>/sta-post/run.tcl.

Python port of run_sta_post.sh. Reproduces ``sta ... 2>&1 | tee "$LOG"`` with
``RC=${PIPESTATUS[0]}``: the full merged output goes to both the log and stdout
(no tail truncation here, unlike /sta), and the process exits with sta's code.

Usage: run_sta_post.py <ip>
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
        print("[STA-POST] usage: run_sta_post.py <ip>", file=sys.stderr)
        return 2

    tcl = f"{ip}/sta-post/run.tcl"
    log = f"{ip}/sta-post/out/sta.log"
    Path(f"{ip}/sta-post/out").mkdir(parents=True, exist_ok=True)

    if not Path(tcl).is_file():
        print(f"[STA-POST] missing {tcl}", file=sys.stderr)
        return 2
    if shutil.which("sta") is None:
        print("[STA-POST TOOL MISSING] OpenSTA 'sta' not on PATH", file=sys.stderr)
        return 3
    sky130_lib = env.get("SKY130_LIB") or os.environ.get("SKY130_LIB", "")
    if not sky130_lib or not os.access(sky130_lib, os.R_OK):
        print("[STA-POST MISSING PDK] $SKY130_LIB unreadable", file=sys.stderr)
        return 4

    # sta -no_init -no_splash -exit "$TCL" 2>&1 | tee "$LOG"
    proc = subprocess.run(
        ["sta", "-no_init", "-no_splash", "-exit", tcl],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    rc = proc.returncode
    captured = proc.stdout or b""
    Path(log).write_bytes(captured)  # tee "$LOG"
    sys.stdout.flush()
    sys.stdout.buffer.write(captured)  # tee's stdout copy (full, untruncated)
    sys.stdout.buffer.flush()

    print(f"[STA-POST] sta rc={rc} log={log}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
