#!/usr/bin/env python3
"""parse_area.py — Read <ip>/syn/out/syn.log + synth.v, emit area.json.

Python port of parse_area.sh for native-Windows portability. Same CLI, exit
codes, and byte-identical area.json output.

Args: <ip_name>

Falls back to HOOK_CMD_ARGS for the IP name when no positional arg is given
(matching the shell original). Sources pdk_env semantics via pdk_env.py so the
``corner`` field (derived from SKY130_LIB basename) resolves identically to
``source pdk_env.sh``.

Exit codes: 2 usage / missing log or netlist.
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import shlex
import sys
from pathlib import Path

# Import the pdk_env port for SKY130_LIB resolution (drives the `corner` field).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
import pdk_env  # noqa: E402


def _resolve_ip(argv: list[str]) -> str:
    args = list(argv)
    if not args and os.environ.get("HOOK_CMD_ARGS", ""):
        args = shlex.split(os.environ["HOOK_CMD_ARGS"])
    return args[0] if args else ""


def _emit_area(ip: str, log_path: str, net_path: str, out_path: str) -> None:
    """Body of the shell heredoc, verbatim semantics."""
    log = pathlib.Path(log_path).read_text(encoding="utf-8", errors="replace")
    net = pathlib.Path(net_path).read_text(encoding="utf-8", errors="replace")  # noqa: F841

    # Parse the FINAL `=== <top> ===` stat block (yosys appends one per stat call).
    blocks = re.findall(r"=== ([^=]+?) ===\s*\n([\s\S]+?)(?=\n===|\Z)", log)
    top_name = ip
    total_cells = 0
    total_area = 0.0
    by_cell: dict[str, int] = {}
    if blocks:
        pick = next(
            (b for b in reversed(blocks) if "design hierarchy" in b[0].lower()),
            blocks[-1],
        )
        body = pick[1]
        NUM = r"[0-9.]+(?:[eE][+-]?\d+)?"
        m_total = re.search(rf"^\s*(\d+)\s+({NUM})\s+cells\b", body, re.M)
        if m_total:
            total_cells = int(m_total.group(1))
            total_area = float(m_total.group(2))
        if total_area == 0.0:
            m_chip = re.search(
                r"Chip area for(?:\s+top)?\s+module[^:]*:\s+([0-9.]+)", body
            )
            if m_chip:
                total_area = float(m_chip.group(1))
        for c_count, c_area, c_name in re.findall(
            rf"^\s*(\d+)\s+({NUM})\s+(sky130_fd_sc_hd__\S+)\s*$", body, re.M
        ):
            by_cell[c_name] = int(c_count)

    SEQ = re.compile(
        r"sky130_fd_sc_hd__(?:dfrtp|dfxtp|dfstp|dfbbn|sdf|edf|latch|dlrtp|dlxtp)"
    )
    seq_cells = sum(c for k, c in by_cell.items() if SEQ.search(k))
    seq_area = 0.0  # noqa: F841 - area per cell type not in stat output by default
    comb_cells = total_cells - seq_cells

    obj = {
        "top": top_name,
        "corner": pathlib.Path(os.environ.get("SKY130_LIB", "")).name or "unknown",
        "total_cells": total_cells,
        "total_area_um2": total_area,
        "by_kind": {
            "sequential": {"cells": seq_cells, "area_um2": None},
            "combinational": {"cells": comb_cells, "area_um2": None},
        },
        "by_cell": dict(sorted(by_cell.items(), key=lambda kv: -kv[1])[:32]),
    }
    pathlib.Path(out_path).write_text(json.dumps(obj, indent=2), encoding="utf-8")
    print(
        f"[SYN] area.json: total={total_cells} cells, seq={seq_cells}, "
        f"comb={comb_cells}, area={total_area} um2 → {out_path}"
    )


def main(argv: list[str]) -> int:
    ip = _resolve_ip(argv)
    if not ip:
        print("[SYN] usage: parse_area.sh <ip_name>", file=sys.stderr)
        return 2

    pdk_env.apply_pdk_env(os.environ)

    log = f"{ip}/syn/out/syn.log"
    netlist = f"{ip}/syn/out/synth.v"
    out = f"{ip}/syn/out/area.json"

    if not Path(log).is_file():
        print(f"[SYN] missing {log}", file=sys.stderr)
        return 2
    if not Path(netlist).is_file():
        print(f"[SYN] missing {netlist}", file=sys.stderr)
        return 2

    _emit_area(ip, log, netlist, out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
