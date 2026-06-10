#!/usr/bin/env python3
"""coverage_build.py — Verilator build with line + toggle coverage flags.

Python port of coverage_build.sh.  Reads the filelist from
``<DUT>/list/<DUT>.f`` and builds instrumented C++ sources into
``build_<DUT>_cov/``.

CLI parity with the .sh:
  * DUT comes from ``HOOK_CMD_ARGS`` env, then argv[1], default ``gpio_pad``.
  * All whitespace is stripped from the DUT name.
  * verilator stdout+stderr is tee'd to ``<BUILD>.verilator.log``.
  * Exit 1 (with guidance) when verilator is missing, the filelist is absent,
    or the verilator build fails; exit 0 on success.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


def _logical_cwd() -> str:
    """Mirror bash $(pwd): prefer the logical $PWD over the symlink-resolved cwd."""
    pwd = os.environ.get("PWD")
    if pwd:
        try:
            if os.path.samefile(pwd, os.getcwd()):
                return pwd
        except OSError:
            pass
    return os.getcwd()


def main(argv: "list[str] | None" = None) -> int:
    argv = sys.argv[1:] if argv is None else argv

    raw_dut = os.environ.get("HOOK_CMD_ARGS")
    if not raw_dut:
        raw_dut = argv[0] if argv else "gpio_pad"
    # strip whitespace (matches "${DUT// /}" plus surrounding trim)
    dut = "".join(raw_dut.split())

    if shutil.which("verilator") is None:
        print("ERROR: verilator not found in PATH")
        print("  Install: brew install verilator   (or use system package manager)")
        return 1

    flist = Path(dut) / "list" / f"{dut}.f"
    if not flist.is_file():
        print(f"ERROR: filelist not found: {flist}")
        print(f"  Looking from: {_logical_cwd()}")
        return 1

    build = f"build_{dut}_cov"
    print("=== Verilator coverage build ===")
    print(f"DUT       : {dut}")
    print(f"Filelist  : {flist}")
    print(f"Build dir : {build}")
    print("")

    cmd = [
        "verilator",
        "--cc",
        "--exe",
        "--coverage",
        "--coverage-line",
        "--coverage-toggle",
        "--trace",
        "--top-module",
        dut,
        "-f",
        str(flist),
        "--Mdir",
        build,
        "-Wno-fatal",
    ]

    log_path = Path(f"{build}.verilator.log")
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    combined = proc.stdout or ""
    # tee: echo to stdout and to the log file.
    sys.stdout.write(combined)
    sys.stdout.flush()
    log_path.write_text(combined, encoding="utf-8")

    if proc.returncode != 0:
        print("")
        print(f"BUILD FAILED — see {build}.verilator.log")
        return 1

    print("")
    print(f"BUILD OK — instrumented sources in {build}/")
    cpp_count = len(list(Path(build).glob("*.cpp")))
    print(f"  C++ source files: {cpp_count}")
    print("")
    print("Next: run testbench under SIM=verilator, then /coverage-merge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
