#!/usr/bin/env python3
"""check_sim_pass.py — Validator for SV and cocotb simulation output.

Python port of check_sim_pass.sh (sim + tb-gen).  This is the single canonical
source of truth; the tb-gen copy is a thin delegator that re-executes this file.

Contract (preserve the recent hardening exactly):
  * If IP_NAME is set and names an existing directory, defer to the on-disk
    check (check_sim_disk.sh) and exit with its status.
  * Otherwise inspect TOOL_OUTPUT:
      - Reject any explicit failure evidence FIRST, even when pass-like text
        also appears: ``FAIL=[1-9][0-9]*`` or ``[1-9][0-9]* failed`` ⇒ exit 1.
      - Require positive pass evidence: ``0 errors, 0 warnings`` or
        ``TESTS=<n> PASS=[1-9][0-9]* FAIL=0`` or ``[1-9][0-9]* passed`` ⇒ exit 0.
        (``TESTS=0 PASS=0 FAIL=0`` must NOT pass.)
      - Otherwise print the error/warning summary and exit 1.

The verdict text differs slightly between the two original .sh files (the sim/
copy emits the single-line "Sim not passing: ..." text, while the tb-gen copy
emits the two-line "Simulation reports failures; not passing" / "Simulation not
passing: ..." text).  Both variants are preserved here and selected by
``--variant`` (default ``sim``); the tb-gen delegator passes ``--variant
tb-gen``.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
from pathlib import Path


# Reject-first failure evidence: a non-zero FAIL count or "N failed" (N>=1).
_FAIL_RE = re.compile(r"FAIL=[1-9][0-9]*|[1-9][0-9]* failed")
# Positive pass evidence.
_PASS_RE = re.compile(
    r"0 errors, 0 warnings|TESTS=[0-9]+ PASS=[1-9][0-9]* FAIL=0|[1-9][0-9]* passed"
)
_ERROR_RE = re.compile(r"[0-9]+ error")
_WARNING_RE = re.compile(r"[0-9]+ warning")


def _first_match(pattern: "re.Pattern[str]", text: str) -> str:
    match = pattern.search(text)
    return match.group(0) if match else ""


def main(argv: "list[str] | None" = None) -> int:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument(
        "--variant",
        choices=("sim", "tb-gen"),
        default="sim",
        help="verdict-text variant matching the original .sh location",
    )
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[3]
    ip_name = os.environ.get("IP_NAME", "")
    if ip_name and Path(ip_name).is_dir():
        disk = repo_root / "workflow" / "sim" / "scripts" / "check_sim_disk.sh"
        proc = subprocess.run(["bash", str(disk), ip_name])
        if proc.returncode == 0:
            return 0
        # Original scripts only `exit 0` on disk PASS; on disk FAIL they fall
        # through to TOOL_OUTPUT inspection (bash `A && exit 0`).

    output = os.environ.get("TOOL_OUTPUT", "")

    if _FAIL_RE.search(output):
        if args.variant == "sim":
            # workflow/sim/scripts/check_sim_pass.sh — single-line verdict.
            print(
                "Sim not passing: reports failures. Expected: 0 errors, "
                "0 warnings or cocotb PASS summary"
            )
        else:
            # workflow/tb-gen/scripts/check_sim_pass.sh — two-line verdict.
            print("Simulation reports failures; not passing")
            print("Expected: 0 errors, 0 warnings or cocotb PASS summary")
        return 1

    if _PASS_RE.search(output):
        return 0

    errors = _first_match(_ERROR_RE, output) or "?"
    warnings = _first_match(_WARNING_RE, output) or "?"
    if args.variant == "sim":
        print(
            f"Sim not passing: {errors}, {warnings}. Expected: 0 errors, "
            "0 warnings or cocotb PASS summary"
        )
    else:
        print(f"Simulation not passing: {errors}, {warnings}")
        print("Expected: 0 errors, 0 warnings or cocotb PASS summary")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
