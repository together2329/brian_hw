#!/usr/bin/env python3
"""check_unmapped.py — Fail-fast sanity check on synth.v.

Python port of check_unmapped.sh for native-Windows portability.

Exits 0 if clean, 7 if unmapped cells, 8 if unintended latches.
Args: <ip_name>

Falls back to the HOOK_CMD_ARGS environment variable for the IP name when no
positional argument is supplied (matching the shell original).
"""

from __future__ import annotations

import os
import re
import shlex
import sys
from pathlib import Path


def _count_lines(text: str, pattern: re.Pattern[str]) -> int:
    """grep -cE — count input lines that match the pattern."""
    return sum(1 for line in text.splitlines() if pattern.search(line))


def main(argv: list[str]) -> int:
    args = list(argv)

    # `[ $# -eq 0 ] && [ -n "${HOOK_CMD_ARGS:-}" ]` → re-split HOOK_CMD_ARGS.
    if not args and os.environ.get("HOOK_CMD_ARGS", ""):
        args = shlex.split(os.environ["HOOK_CMD_ARGS"])

    ip = args[0] if args else ""
    if not ip:
        print("[SYN] usage: check_unmapped.sh <ip_name>", file=sys.stderr)
        return 2

    netlist = Path(ip) / "syn" / "out" / "synth.v"
    if not netlist.is_file():
        print(f"[SYN] missing {netlist}", file=sys.stderr)
        return 2

    text = netlist.read_text(encoding="utf-8", errors="replace")

    re_unmapped = re.compile(r"^\s*\$_")
    re_generic = re.compile(r"^\s*(\$paramod|\$_NOT_|\$_AND_|\$_OR_|\$_DFF_)")
    # sky130 D-latch cell names: dlxtp, dlxtn, dlxbn, dlxbp, dlrtp, dlrbn, dlrbp,
    # dlclkp, dlymetal*. Match the dl<2-3 alpha> prefix; `df<x>` (flip-flops)
    # explicitly excluded.
    re_latches = re.compile(r"sky130_fd_sc_hd__dl(x|r|c|y)")

    unmapped = _count_lines(text, re_unmapped)
    generic = _count_lines(text, re_generic)
    latches = _count_lines(text, re_latches)

    print(f"[SYN] netlist: unmapped={unmapped} generic={generic} latch_cells={latches}")

    if unmapped > 0 or generic > 0:
        print(
            "[SYN UNMAPPED] dfflibmap/abc did not bind every cell — check liberty path and synth.log",
            file=sys.stderr,
        )
        re_dump = re.compile(r"^\s*(\$paramod|\$_)")
        hits = [
            f"{idx}:{line}"
            for idx, line in enumerate(text.splitlines(), start=1)
            if re_dump.search(line)
        ][:20]
        for hit in hits:
            print(hit, file=sys.stderr)
        return 7

    # Latches are flagged; whether they are intended is up to the SSOT
    # (latch: declared).
    ssot = Path(ip) / "yaml" / f"{ip}.ssot.yaml"
    if latches > 0:
        re_intended = re.compile(r"^\s*latch_intended\s*:\s*true")
        declared = False
        if ssot.is_file():
            ssot_text = ssot.read_text(encoding="utf-8", errors="replace")
            declared = any(re_intended.search(line) for line in ssot_text.splitlines())
        if declared:
            print(f"[SYN] {latches} latch cells (declared in SSOT — OK)")
        else:
            print(
                f"[SYN UNINTENDED LATCH] {latches} latch cells in netlist but SSOT does "
                "not declare latch_intended:true",
                file=sys.stderr,
            )
            return 8
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
