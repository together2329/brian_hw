#!/usr/bin/env python3
"""auto_syn.py — End-to-end synthesis driver. Single entry point for /syn.

Python port of auto_syn.sh for native-Windows portability. Same CLI, exit
codes, and pipeline ordering.

Args: <ip_name>
Pipeline: write run.ys → yosys → sanity gate → area.json → syn.report.md

Falls back to HOOK_CMD_ARGS for the IP name when no positional arg is given
(matching the shell original). Sources pdk_env semantics via pdk_env.py.

Each stage is invoked as the sibling Python port (preflight.py,
write_yosys_script.py, run_yosys.py, check_unmapped.py, parse_area.py,
write_report.py); on any stage failure auto_syn exits with that stage's rc.

Exit codes: 2 usage/missing IP dir, 4 PDK liberty unreadable, else the rc of
the first failing stage.
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

# Import the pdk_env port (mirrors `source pdk_env.sh`).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
import pdk_env  # noqa: E402


def _resolve_ip(argv: list[str]) -> str:
    args = list(argv)
    if not args and os.environ.get("HOOK_CMD_ARGS", ""):
        args = shlex.split(os.environ["HOOK_CMD_ARGS"])
    return args[0] if args else ""


def _run_stage(script: Path, ip: str) -> int:
    """``python3 <script> <ip>`` — return its exit code (shell ran ``bash``)."""
    proc = subprocess.run([sys.executable, str(script), ip])
    return proc.returncode


def _read_area_field(area_path: str, expr: str, default: str) -> str:
    """Mirror ``python3 -c "... print(...)" || echo <default>`` extraction."""
    try:
        with open(area_path, encoding="utf-8") as handle:
            d = json.load(handle)
        if expr == "total_cells":
            return str(d.get("total_cells", 0))
        if expr == "sequential":
            return str(d["by_kind"]["sequential"]["cells"])
        if expr == "total_area_um2":
            return str(d.get("total_area_um2", 0))
    except Exception:
        return default
    return default


def main(argv: list[str]) -> int:
    ip = _resolve_ip(argv)

    pdk_env.apply_pdk_env(os.environ)

    if not ip:
        print("[SYN] usage: auto_syn.sh <ip_name>", file=sys.stderr)
        return 2
    if not Path(ip).is_dir():
        print(f"[SYN] no such IP dir: {ip}", file=sys.stderr)
        return 2

    directory = Path(__file__).resolve().parent
    out = f"{ip}/syn/out"
    Path(out).mkdir(parents=True, exist_ok=True)

    # Tool / PDK preflight
    rc = _run_stage(directory / "preflight.py", ip)
    if rc != 0:
        return rc
    lib = os.environ.get("SKY130_LIB", "")
    if not lib or not os.access(lib, os.R_OK):
        print(f"[SYN MISSING PDK] $SKY130_LIB unreadable: {lib}", file=sys.stderr)
        return 4
    os.environ["SKY130_LIB"] = lib

    for stage in (
        "write_yosys_script.py",
        "run_yosys.py",
        "check_unmapped.py",
        "parse_area.py",
        "write_report.py",
    ):
        rc = _run_stage(directory / stage, ip)
        if rc != 0:
            return rc

    netlist = f"{out}/synth.v"
    area_json = f"{out}/area.json"
    cells = _read_area_field(area_json, "total_cells", "0")
    seq = _read_area_field(area_json, "sequential", "0")
    area = _read_area_field(area_json, "total_area_um2", "0")
    print(
        f"[SYN HANDOFF] {netlist} ready "
        f"(cells={cells}, FFs={seq}, area={area} μm²) — run /sta"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
