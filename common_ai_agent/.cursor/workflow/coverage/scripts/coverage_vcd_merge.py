#!/usr/bin/env python3
"""coverage_vcd_merge.py — Python port of coverage_vcd_merge.sh (coverage).

Wrap ``adapters/vcd_merge.py`` for the slash command: discover ``*.vcd`` under
``<DUT>/`` and merge them into ``<DUT>/cov/merged.vcd``.

CLI / env contract preserved (bash ``set -e``):
  * DUT = ``$HOOK_CMD_ARGS`` else first positional argument else ``gpio_pad``;
    spaces stripped.
  * MODE = ``concat`` unless overridden by ``--mode <m>`` (scanned across args).
  * Adapter path = ``<script_dir>/../adapters/vcd_merge.py``; missing ⇒ ERROR
    + exit 1.
  * ``find <DUT> -name '*.vcd' -not -path '*/cov/merged.vcd' | sort``.  None ⇒
    ERROR guidance + exit 1.  Exactly one ⇒ copy it to merged.vcd, exit 0.
  * Otherwise print the input list, run the adapter, and on rc 0 print the Next
    hints; propagate the adapter's exit code.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def _find_vcds(dut: str) -> "list[str]":
    # find "${DUT}" -name "*.vcd" -not -path "*/cov/merged.vcd" | sort
    results: "list[str]" = []
    for dirpath, _dirnames, filenames in os.walk(dut):
        for name in filenames:
            if name.endswith(".vcd"):
                full = str(Path(dirpath) / name)
                if not full.endswith("/cov/merged.vcd"):
                    results.append(full)
    return sorted(results)


def main(argv: "list[str] | None" = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    dut = os.environ.get("HOOK_CMD_ARGS") or (argv[0] if argv else "") or "gpio_pad"
    dut = dut.replace(" ", "")

    mode = "concat"
    for i, arg in enumerate(argv):
        if arg == "--mode" and i + 1 < len(argv):
            mode = argv[i + 1]

    script_dir = Path(__file__).resolve().parent
    adapter = script_dir / ".." / "adapters" / "vcd_merge.py"
    if not adapter.is_file():
        print(f"ERROR: adapter not found: {adapter}")
        return 1

    out_dir = Path(dut) / "cov"
    out = out_dir / "merged.vcd"
    out_dir.mkdir(parents=True, exist_ok=True)

    vcds = _find_vcds(dut)
    if not vcds:
        print(f"ERROR: no .vcd files found under {dut}/")
        print("  Common locations checked:")
        print(f"    {dut}/sim/*.vcd")
        print(f"    {dut}/cocotb/sim_build/*.vcd")
        print("  Run a simulation first (iverilog or cocotb with WAVES=1).")
        return 1

    if len(vcds) == 1:
        print(f"Only 1 .vcd found ({vcds[0]}) — nothing to merge.")
        shutil.copy(vcds[0], out)
        print(f"Copied to {out}")
        return 0

    print(f"=== VCD merge ({mode}) ===")
    print(f"DUT     : {dut}")
    print(f"Inputs  : {len(vcds)}")
    for path in vcds:
        print(f"  - {path}")
    print(f"Output  : {out}")
    print("")

    sys.stdout.flush()  # keep print()/subprocess stdout interleaving in order
    proc = subprocess.run(
        [sys.executable, str(adapter), "--mode", mode, "--out", str(out), *vcds]
    )
    rc = proc.returncode
    if rc == 0:
        print("")
        print(f"Next: open in gtkwave  →  gtkwave {out}")
        print("      or use /coverage-vcd-toggle to extract toggle coverage from this VCD")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
