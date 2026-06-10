#!/usr/bin/env python3
"""wave_info.py — Python port of wave_info.sh (sim_debug).

Mirror of workflow/sim/scripts/wave_info with extended search depth (sim_debug
is invoked from any cwd, not just an IP root) plus an ASCII-VCD sanity guard.

CLI / env contract preserved:
  * VCD = ``$HOOK_CMD_ARGS`` else first positional argument; if empty, search
    ``find . -maxdepth 4 -name '*.vcd'`` (first); if still empty, print the
    extended "No VCD found" guidance and exit 1.
  * ASCII-VCD guard: if the first 256 bytes do not contain ``$date`` /
    ``$timescale`` / ``$var``, print the "not parseable ASCII VCD" guidance and
    exit 2.

Faithful port note: the "Signals (top-level)" extraction uses the same
``grep -oP`` variable-length look-behind pipeline as sim/wave_info.sh and is
therefore shelled out verbatim — see that port's docstring and the report for
the latent empty-output bug on hosts without GNU grep ``-P``.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _find_first_vcd(maxdepth: int) -> str:
    base_depth = len(Path(".").parts)
    for dirpath, dirnames, filenames in os.walk("."):
        depth = len(Path(dirpath).parts) - base_depth + 1
        if depth > maxdepth:
            dirnames[:] = []
            continue
        for name in filenames:
            if name.endswith(".vcd"):
                return str(Path(dirpath) / name)
        if depth >= maxdepth:
            dirnames[:] = []
    return ""


def _sh(cmd: str, vcd: str | None = None) -> str:
    env = dict(os.environ)
    if vcd is not None:
        env["VCD"] = vcd
    proc = subprocess.run(
        ["/bin/sh", "-c", cmd], capture_output=True, text=True, env=env
    )
    return proc.stdout


def _is_ascii_vcd(vcd: str) -> bool:
    """Replicate: head -c 256 | LC_ALL=C grep -qa '$date|$timescale|$var'."""
    try:
        with open(vcd, "rb") as handle:
            head = handle.read(256)
    except OSError:
        return False
    return any(tok in head for tok in (b"$date", b"$timescale", b"$var"))


def main(argv: "list[str] | None" = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    vcd = os.environ.get("HOOK_CMD_ARGS") or (argv[0] if argv else "")
    if not vcd:
        vcd = _find_first_vcd(maxdepth=4)
    if not vcd:
        print(
            "No VCD found. Add $dumpfile/$dumpvars to TB and re-run /sim, "
            "or pass /wave <file>."
        )
        return 1

    print(f"=== VCD: {vcd} ===")
    size = _sh(f'du -h "{vcd}" | cut -f1').rstrip("\n")
    print(f"Size: {size}")

    if not _is_ascii_vcd(vcd):
        print()
        print(f"ERROR: {vcd} is not parseable ASCII VCD.")
        print("It may be FST/LXT/binary simulator data with a .vcd suffix.")
        print("Re-run TB with an ASCII VCD dump, or provide a matching converter")
        print("(for example fst2vcd/lxt2vcd) and the real waveform format.")
        return 2

    print()
    print("Signals (top-level):")
    cmd = (
        "grep -oP '(?<=\\$var wire \\d+ )\\S+ \\S+(?= \\$end)' \"$VCD\" "
        "2>/dev/null | head -30 || grep \"^\\$var\" \"$VCD\" | head -20"
    )
    sys.stdout.write(_sh(cmd, vcd=vcd))
    print()
    print("Time range:")
    sys.stdout.write(_sh(f'grep "^#" "{vcd}" | tail -5'))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
