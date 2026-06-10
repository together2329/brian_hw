#!/usr/bin/env python3
"""auto_sta_post.py — End-to-end sign-off STA driver.

Python port of auto_sta_post.sh. Chains preflight → tcl → OpenSTA → parse →
report via the sibling .py ports, aborting on the first non-zero stage (bash
``|| exit $?``), then prints the [STA-POST RESULT] one-liner.

Usage: auto_sta_post.py <ip>
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _sh_port_common import load_pdk_env  # noqa: E402

_DIR = Path(__file__).resolve().parent


def _run_stage(script: str, ip: str) -> int:
    proc = subprocess.run([sys.executable, str(_DIR / script), ip])
    return proc.returncode


def main(argv: list[str]) -> int:
    if not argv and os.environ.get("HOOK_CMD_ARGS"):
        argv = os.environ["HOOK_CMD_ARGS"].split()

    # ``source pdk_env.sh`` so SKY130_LIB is in the environment the stages inherit.
    load_pdk_env()

    ip = argv[0] if argv else ""
    if not ip:
        print("[STA-POST] usage: auto_sta_post.py <ip>", file=sys.stderr)
        return 2
    if not Path(ip).is_dir():
        print(f"[STA-POST] no such IP dir: {ip}", file=sys.stderr)
        return 2

    out = f"{ip}/sta-post/out"
    Path(out).mkdir(parents=True, exist_ok=True)

    sys.stdout.flush()
    for script in (
        "preflight.py",
        "write_sta_post_tcl.py",
        "run_sta_post.py",
        "parse_wns.py",
        "write_report.py",
    ):
        rc = _run_stage(script, ip)
        if rc != 0:
            return rc

    wns_json = f"{out}/wns.json"
    if Path(wns_json).is_file():
        d = json.load(open(wns_json))
        res = (
            "PASS"
            if d["summary"].get("all_setup_met") and d["summary"].get("all_hold_met")
            else ("HOLD FAIL" if not d["summary"].get("all_hold_met") else "SETUP FAIL")
        )
        clocks = ", ".join(
            f"{c['name']}@{c['period_ns']}ns: setup_wns={c['setup_wns_ns']} "
            f"hold_wns={c['hold_wns_ns']}"
            for c in d.get("clocks", [])
        )
        print(f"[STA-POST RESULT] {res} (sign-off, parasitic-aware) — {clocks}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
