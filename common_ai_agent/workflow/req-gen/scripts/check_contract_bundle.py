#!/usr/bin/env python3
"""Validate the mandatory req/ contract authority bundle.

This is a naming wrapper around check_locked_truth_bundle.py so downstream
flows can refer to the gate by its actual role: contract authority validation.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from check_locked_truth_bundle import check_locked_truth_bundle  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate req/ contract authority bundle.")
    parser.add_argument("ip")
    parser.add_argument("--root", default=".")
    parser.add_argument("--review-candidate", action="store_true")
    args = parser.parse_args()
    ok, failures, summary = check_locked_truth_bundle(
        args.ip,
        Path(args.root),
        review_candidate=args.review_candidate,
    )
    counts = " ".join(f"{key}={value}" for key, value in summary.items())
    if ok:
        print(f"[check_contract_bundle] PASS {args.ip}: {counts}")
        return 0
    print(f"[check_contract_bundle] FAIL {args.ip}: {counts}")
    for failure in failures:
        print(f"- {failure}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
