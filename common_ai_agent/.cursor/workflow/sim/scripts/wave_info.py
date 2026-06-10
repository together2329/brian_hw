#!/usr/bin/env python3
"""wave_info.py — Python port of wave_info.sh (sim).

Summarise a VCD: size, top-level signals, and the last few time markers.

CLI / env contract preserved:
  * VCD = ``$HOOK_CMD_ARGS`` else first positional argument; if empty, search
    ``find . -maxdepth 2 -name '*.vcd'`` and take the first; if still empty,
    print the "No VCD found" guidance and exit 1.

Faithful port note (IMPORTANT bash-ism / latent bug — see report):
The original "Signals (top-level)" extraction is

    grep -oP '(?<=$var wire \\d+ )\\S+ \\S+(?= $end)' "$VCD" 2>/dev/null | head -30 \\
        || grep "^$var" "$VCD" | head -20

The ``grep -oP`` uses a *variable-length* look-behind.  On macOS BSD grep the
``-P`` flag is unsupported (``invalid option -- P``); even where ``-P`` exists
via ugrep the variable-length look-behind is rejected.  Because the failing
grep is piped into ``head``, the pipeline exit status is ``head``'s (0), so the
``||`` fallback never fires and the Signals section comes out **empty**.  To
preserve byte-for-byte parity with the ``.sh`` on whatever host runs it, this
port shells out to the very same grep pipeline rather than re-implementing the
extraction in Python.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _find_first_vcd(maxdepth: int) -> str:
    """Replicate ``find . -maxdepth <n> -name '*.vcd' | head -1`` (find order)."""
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


def _sh(cmd: str) -> str:
    """Run a shell snippet and return stdout (text), ignoring exit status."""
    proc = subprocess.run(["/bin/sh", "-c", cmd], capture_output=True, text=True)
    return proc.stdout


def _signals_block(vcd: str) -> str:
    # Identical pipeline to the .sh, including the masked ``||`` fallback.
    cmd = (
        "grep -oP '(?<=\\$var wire \\d+ )\\S+ \\S+(?= \\$end)' \"$VCD\" "
        "2>/dev/null | head -30 || grep \"^\\$var\" \"$VCD\" | head -20"
    )
    proc = subprocess.run(
        ["/bin/sh", "-c", cmd],
        capture_output=True,
        text=True,
        env={**os.environ, "VCD": vcd},
    )
    return proc.stdout


def main(argv: "list[str] | None" = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    vcd = os.environ.get("HOOK_CMD_ARGS") or (argv[0] if argv else "")
    if not vcd:
        vcd = _find_first_vcd(maxdepth=2)
    if not vcd:
        print(
            "No VCD found. Add $dumpfile/$dumpvars to TB and re-run /sim."
        )
        return 1

    print(f"=== VCD: {vcd} ===")
    # Size: $(du -h "${VCD}" | cut -f1)
    size = _sh(f'du -h "{vcd}" | cut -f1').rstrip("\n")
    print(f"Size: {size}")
    print()
    print("Signals (top-level):")
    sys.stdout.write(_signals_block(vcd))
    print()
    print("Time range:")
    # grep "^#" "${VCD}" | tail -5
    sys.stdout.write(_sh(f'grep "^#" "{vcd}" | tail -5'))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
