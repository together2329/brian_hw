#!/usr/bin/env python3
"""run_openroad_dft.py — Port of run_openroad_dft.sh.

Invoke OpenROAD on <ip>/dft/run.tcl; capture all output.  Args: <ip_name>
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _dft_common as common  # noqa: E402


def main(argv: "list[str]") -> int:
    common.load_pdk_env(os.environ)

    ip = argv[0] if argv else ""
    if not ip:
        print("[DFT] usage: run_openroad_dft.sh <ip_name>", file=sys.stderr)
        return 2

    tcl = f"{ip}/dft/run.tcl"
    log = f"{ip}/dft/out/dft.log"
    Path(f"{ip}/dft/out").mkdir(parents=True, exist_ok=True)

    if not Path(tcl).is_file():
        print(f"[DFT] missing {tcl} — run /dft-tcl first", file=sys.stderr)
        return 2
    if common.which("openroad") is None:
        print("[DFT TOOL MISSING] openroad not on PATH", file=sys.stderr)
        return 3
    sky130_lib = os.environ.get("SKY130_LIB", "")
    if not sky130_lib or not common.readable(sky130_lib):
        print("[DFT MISSING PDK] $SKY130_LIB unreadable", file=sys.stderr)
        return 4

    # `openroad -no_init -exit <tcl> 2>&1 | tee <log>` then RC=${PIPESTATUS[0]}.
    proc = subprocess.run(
        ["openroad", "-no_init", "-exit", tcl],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=dict(os.environ),
    )
    out = proc.stdout or b""
    sys.stdout.buffer.write(out)
    sys.stdout.buffer.flush()
    with open(log, "wb") as fh:  # tee (truncate, not append)
        fh.write(out)
    rc = proc.returncode
    print(f"[DFT] openroad rc={rc} log={log}")
    return rc


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
