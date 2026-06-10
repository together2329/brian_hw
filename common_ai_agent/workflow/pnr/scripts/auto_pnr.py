#!/usr/bin/env python3
"""auto_pnr.py — Port of auto_pnr.sh. One-shot PnR pipeline.

Calls preflight → fp → place → cts → route → report in sequence.  Args: <ip>

The bash original shells out to the sibling ``*.sh`` stage scripts; this port
shells out to the sibling ``*.py`` ports via ``sys.executable`` so the staged
behaviour (and each stage's stdout/stderr/exit code) is preserved.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _pnr_common as common  # noqa: E402


def main(argv: "list[str]") -> int:
    argv = common.argv_from_hook(argv)

    ip = argv[0] if argv else ""
    if not ip:
        print("[PNR] usage: auto_pnr.sh <ip>", file=sys.stderr)
        return 2
    if not Path(ip).is_dir():
        print(f"[PNR] no such IP dir: {ip}", file=sys.stderr)
        return 2

    d = os.path.dirname(os.path.abspath(__file__))

    def stage(script: str) -> int:
        return subprocess.run([sys.executable, os.path.join(d, script), ip]).returncode

    for script in ("preflight.py", "run_fp.py", "run_place.py", "run_cts.py", "run_route.py"):
        rc = stage(script)
        if rc != 0:
            return rc

    # write_report is best-effort (`|| true`).
    subprocess.run([sys.executable, os.path.join(d, "write_report.py"), ip])
    print(f"[PNR] full pipeline complete — see {ip}/pnr/out/pnr.report.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
