#!/usr/bin/env python3
"""auto_sta.py — End-to-end STA driver. Single entry point for /sta.

Python port of auto_sta.sh. Pipeline: handoff gate → SDC → tcl → OpenSTA → parse
WNS/TNS → report. Each stage is delegated to the sibling .py port (which is itself
byte-identical to its .sh), and a non-zero stage exit aborts with that code, just
like the bash ``|| exit $?`` chain.

Usage: auto_sta.py <ip_name>
"""

from __future__ import annotations

import glob
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _sh_port_common import load_pdk_env  # noqa: E402

_DIR = Path(__file__).resolve().parent


def _run_stage(script: str, ip: str) -> int:
    """Replicate ``bash "${DIR}/<script>.sh" "$IP" || exit $?`` using the .py port."""
    proc = subprocess.run([sys.executable, str(_DIR / script), ip])
    return proc.returncode


def main(argv: list[str]) -> int:
    if not argv and os.environ.get("HOOK_CMD_ARGS"):
        argv = os.environ["HOOK_CMD_ARGS"].split()

    env = load_pdk_env()

    ip = argv[0] if argv else ""
    if not ip:
        print("[STA] usage: auto_sta.py <ip_name>", file=sys.stderr)
        return 2
    if not Path(ip).is_dir():
        print(f"[STA] no such IP dir: {ip}", file=sys.stderr)
        return 2

    netlist = f"{ip}/syn/out/synth.v"
    out = f"{ip}/sta/out"
    Path(out).mkdir(parents=True, exist_ok=True)

    # Handoff gate.
    if not (Path(netlist).is_file() and Path(netlist).stat().st_size > 0):
        print(f"[STA HANDOFF MISSING] {netlist} — run /syn first", file=sys.stderr)
        return 5

    rtl_files = glob.glob(f"{ip}/rtl/*.sv") + glob.glob(f"{ip}/rtl/*.v")
    if rtl_files:
        # ls -t ... | head -1: newest by mtime; ties broken by ascending name.
        newest_rtl = sorted(rtl_files, key=lambda p: (-os.path.getmtime(p), p))[0]
        if newest_rtl and os.path.getmtime(newest_rtl) > os.path.getmtime(netlist):
            print(
                f"[STA STALE NETLIST] {newest_rtl} newer than {netlist} — re-run /syn",
                file=sys.stderr,
            )
            return 6

    # Tool / PDK preflight.
    if shutil.which("sta") is None:
        print("[STA TOOL MISSING] OpenSTA 'sta' not on PATH", file=sys.stderr)
        return 3
    lib = env.get("SKY130_LIB") or os.environ.get("SKY130_LIB", "")
    if not os.access(lib, os.R_OK):
        print(f"[STA MISSING PDK] $SKY130_LIB unreadable: {lib}", file=sys.stderr)
        return 4
    os.environ["SKY130_LIB"] = lib
    print(f"[STA] liberty={lib}")
    # Flush before spawning children: they write to the inherited stdout fd
    # directly, so an unflushed parent buffer would interleave after them.
    sys.stdout.flush()

    for script in (
        "write_sdc.py",
        "write_sta_tcl.py",
        "run_opensta.py",
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
            f"{c['name']}@{c['period_ns']}ns: setup_wns={c['setup_wns_ns']:.3f} "
            f"hold_wns={c['hold_wns_ns']:.3f}"
            for c in d.get("clocks", [])
        )
        print(f"[STA RESULT] {res} — {clocks}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
