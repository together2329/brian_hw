#!/usr/bin/env python3
"""preflight.py — Validate post-route STA tool, PDK, and PnR handoff inputs.

Python port of preflight.sh. Emits the same diagnostic lines and exit codes.

Usage: preflight.py <ip>
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _sh_port_common import load_pdk_env  # noqa: E402


def _wc_c(n: int) -> str:
    """Mirror ``wc -c < file`` output.

    BSD wc (this machine) right-justifies the count with a leading space and a
    minimum total field width of 8 (e.g. 15 -> '      15', 12345678 ->
    ' 12345678'). GNU wc emits the bare number. We reproduce the BSD format so
    the differential against the .sh passes on Darwin; on a GNU host a caller
    wanting bare output can post-process. Flagged as a platform-dependent
    bash-ism in the port report.
    """
    s = str(n)
    width = max(8, len(s) + 1)
    return s.rjust(width)


def main(argv: list[str]) -> int:
    if not argv and os.environ.get("HOOK_CMD_ARGS"):
        argv = os.environ["HOOK_CMD_ARGS"].split()

    env = load_pdk_env()

    ip = argv[0] if argv else ""
    if not ip:
        print("[STA-POST PREFLIGHT] usage: preflight.py <ip>", file=sys.stderr)
        return 2

    routed_v = f"{ip}/pnr/out/routed.v"
    routed_spef = f"{ip}/pnr/out/routed.spef"
    routed_def = f"{ip}/pnr/out/routed.def"
    cts_v = f"{ip}/pnr/out/cts.v"
    sdc = f"{ip}/sta/out/{ip}.sdc"

    pdk_root = env.get("PDK_ROOT") or os.environ.get("PDK_ROOT", "")
    sky130_lib = env.get("SKY130_LIB") or os.environ.get("SKY130_LIB", "")

    print(f"[STA-POST PREFLIGHT] cwd={os.getcwd()}")
    print(f"[STA-POST PREFLIGHT] PDK_ROOT={pdk_root}")
    print(f"[STA-POST PREFLIGHT] SKY130_LIB={sky130_lib}")

    if not Path(ip).is_dir():
        print(f"[STA-POST PREFLIGHT] IP dir missing: {ip}", file=sys.stderr)
        return 2
    if shutil.which("sta") is None:
        print("[STA-POST TOOL MISSING] OpenSTA 'sta' not on PATH", file=sys.stderr)
        return 3
    if not sky130_lib or not os.access(sky130_lib, os.R_OK):
        print(
            f"[STA-POST MISSING PDK] $SKY130_LIB unreadable: {sky130_lib}",
            file=sys.stderr,
        )
        return 4
    if not (Path(routed_v).is_file() and Path(routed_v).stat().st_size > 0):
        print(
            f"[STA-POST HANDOFF MISSING] {routed_v} — run /pnr-route first",
            file=sys.stderr,
        )
        return 5
    if not (Path(routed_spef).is_file() and Path(routed_spef).stat().st_size > 0):
        print(
            f"[STA-POST SPEF MISSING] {routed_spef} — re-run /pnr-route to extract parasitics",
            file=sys.stderr,
        )
        return 5
    if not Path(sdc).is_file():
        print(f"[STA-POST SDC MISSING] {sdc} — run /sta-sdc first", file=sys.stderr)
        return 5
    if (
        Path(cts_v).is_file()
        and os.path.getmtime(cts_v) > os.path.getmtime(routed_v)
    ):
        print(
            f"[STA-POST STALE NETLIST] {cts_v} newer than {routed_v}", file=sys.stderr
        )
        return 6
    if (
        Path(routed_def).is_file()
        and os.path.getmtime(routed_def) > os.path.getmtime(routed_spef)
    ):
        print(
            f"[STA-POST STALE SPEF] {routed_def} newer than {routed_spef}",
            file=sys.stderr,
        )
        return 6

    spef_size = _wc_c(Path(routed_spef).stat().st_size)
    print(f"[STA-POST PREFLIGHT] sta={shutil.which('sta')}")
    print(f"[STA-POST PREFLIGHT] routed_v={routed_v}")
    print(f"[STA-POST PREFLIGHT] routed_spef={routed_spef} size={spef_size}")
    print(f"[STA-POST PREFLIGHT] sdc={sdc}")
    print("[STA-POST PREFLIGHT] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
