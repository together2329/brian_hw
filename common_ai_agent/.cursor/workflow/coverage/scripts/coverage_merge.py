#!/usr/bin/env python3
"""coverage_merge.py — Python port of coverage_merge.sh (coverage).

Merge all per-test ``coverage.dat`` / ``*.cov.dat`` files under ``<DUT>/`` into
``<DUT>/cov/merged.dat`` via ``verilator_coverage``.

CLI / env contract preserved (bash ``set -e``):
  * DUT = ``$HOOK_CMD_ARGS`` else first positional argument else ``gpio_pad``;
    spaces stripped.
  * Missing ``verilator_coverage`` ⇒ ERROR + exit 1.
  * ``find <DUT> \\( -name 'coverage.dat' -o -name '*.cov.dat' \\)``; none ⇒
    ERROR guidance + exit 1.
  * Print the found list, run ``verilator_coverage --write <out> <files...>``,
    then ``Merged → ...`` and ``ls -lh`` of the output, plus the Next hint.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def _find_dat_files(dut: str) -> "list[str]":
    # find "${DUT}" \( -name "coverage.dat" -o -name "*.cov.dat" \)
    results: "list[str]" = []
    for dirpath, _dirnames, filenames in os.walk(dut):
        for name in filenames:
            if name == "coverage.dat" or name.endswith(".cov.dat"):
                results.append(str(Path(dirpath) / name))
    return results


def main(argv: "list[str] | None" = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    dut = os.environ.get("HOOK_CMD_ARGS") or (argv[0] if argv else "") or "gpio_pad"
    dut = dut.replace(" ", "")

    if shutil.which("verilator_coverage") is None:
        print("ERROR: verilator_coverage not found (ships with verilator)")
        return 1

    out_dir = Path(dut) / "cov"
    out_dir.mkdir(parents=True, exist_ok=True)

    dat_files = _find_dat_files(dut)
    if not dat_files:
        print(f"ERROR: no coverage.dat found under {dut}/")
        print("  Did you run the regression with verilator backend yet?")
        print(f"  e.g. cd {dut}/cocotb && make SIM=verilator MODULE=tests.tb")
        return 1

    print("=== Coverage merge ===")
    print(f"Found {len(dat_files)} coverage.dat file(s):")
    for path in dat_files:
        print(f"  {path}")
    print("")

    merged = out_dir / "merged.dat"
    sys.stdout.flush()  # keep print()/subprocess stdout interleaving in order
    subprocess.run(
        ["verilator_coverage", "--write", str(merged), *dat_files]
    )
    print("")
    print(f"Merged → {merged}")
    # ls -lh "${OUT}/merged.dat"
    ls = subprocess.run(["ls", "-lh", str(merged)], capture_output=True, text=True)
    sys.stdout.write(ls.stdout)
    print("")
    print("Next: /coverage-report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
