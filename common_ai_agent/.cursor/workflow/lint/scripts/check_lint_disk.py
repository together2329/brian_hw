#!/usr/bin/env python3
"""check_lint_disk.py — Disk-truth validator for lint tasks.

Python port of check_lint_disk.sh for native-Windows portability.

Verifies lint_report.txt actually exists on disk + claims 0 errors / 0 warnings
AS PRESENT IN THE FILE (not just the assistant's prose).

Inputs (env):
  IP_NAME — IP slug (auto-detected from cwd)
  ALLOW_WARNINGS — set to "1" to allow >=0 warnings (default: 0 = strict)

Exit 0 = report file exists, contains 0 errors AND (0 warnings OR allowed).
Exit 1 = file missing OR contains non-zero errors / disallowed warnings.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path


def _auto_detect_ip() -> str:
    """Replicate: find . -maxdepth 3 -type f -name '*.ssot.yaml'
    | sort -t/ -k2 | head -1 | awk -F/ '{print $(NF-2)}'."""
    root = Path(".")
    matches: list[str] = []
    for path in root.glob("*/*/*.ssot.yaml"):
        matches.append("./" + path.as_posix())
    for path in root.glob("*/*.ssot.yaml"):
        matches.append("./" + path.as_posix())
    for path in root.glob("*.ssot.yaml"):
        matches.append("./" + path.as_posix())

    def sort_key(item: str) -> str:
        parts = item.split("/")
        return parts[1] if len(parts) > 1 else ""

    matches.sort(key=sort_key)
    if not matches:
        return ""
    fields = matches[0].split("/")
    if len(fields) >= 3:
        return fields[-3]
    return ""


def _first_match_line(report: Path, pattern: re.Pattern[str]) -> str:
    """grep -m1 -niE — first matching line with 'lineno:line' prefix."""
    for idx, line in enumerate(report.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if pattern.search(line):
            return f"{idx}:{line}"
    return ""


def main(argv: list[str]) -> int:
    ip = os.environ.get("IP_NAME") or (argv[0] if argv else "")
    if not ip:
        ip = _auto_detect_ip()

    if not ip or not Path(ip).is_dir():
        print("[check_lint_disk] FAIL: IP dir not found")
        return 1

    report = Path(ip) / "lint" / "lint_report.txt"
    if not report.is_file():
        print(f"[check_lint_disk] FAIL: {report.as_posix()} missing")
        return 1

    size = report.stat().st_size
    if size < 30:
        print(f"[check_lint_disk] FAIL: {report.as_posix()} too small ({size}B)")
        return 1

    text = report.read_text(encoding="utf-8", errors="replace")

    # Look for failure markers verbatim in the file.
    err_re = re.compile(r"[1-9][0-9]* error|FAIL|FATAL", re.IGNORECASE)
    if err_re.search(text):
        line = _first_match_line(report, err_re)
        print(f"[check_lint_disk] FAIL: {report.as_posix()} contains error markers")
        print(f"  → {line}")
        return 1

    if os.environ.get("ALLOW_WARNINGS", "0") != "1":
        warn_re = re.compile(r"[1-9][0-9]* warning", re.IGNORECASE)
        if warn_re.search(text):
            line = _first_match_line(report, warn_re)
            print(
                f"[check_lint_disk] FAIL: {report.as_posix()} contains warning markers "
                "(set ALLOW_WARNINGS=1 to permit)"
            )
            print(f"  → {line}")
            return 1

    # Must contain a positive pass signature.
    pass_re = re.compile(r"0 error|0 warning|lint clean|all clean|no issues", re.IGNORECASE)
    if pass_re.search(text):
        print(f"[check_lint_disk] PASS: {report.as_posix()} = {size}B, clean")
        return 0

    print(f"[check_lint_disk] FAIL: {report.as_posix()} lacks positive pass signature")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
