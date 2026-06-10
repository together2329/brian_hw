#!/usr/bin/env python3
"""sim_capture.py — Python port of sim_capture.sh (sim).

Parse simulation output captured in ``HOOK_TOOL_OUTPUT`` and append a one-line
benchmark log entry summarising errors / warnings / pass / fail counts and an
overall PASS/FAIL status.

Status is PASS only when both the error and warning counts are zero, exactly
like the bash original.  A ``TESTS=<n> PASS=<n> FAIL=<n>`` summary line (last
occurrence) overrides the grep-counted pass/fail numbers.
"""

from __future__ import annotations

import os
import re
import time


_ERROR_RE = re.compile(r"error", re.IGNORECASE)
_WARNING_RE = re.compile(r"warning", re.IGNORECASE)
# grep -Ec "\[PASS\]| passed| PASS="  /  "\[FAIL\]| failed| FAIL=[1-9]"
_PASS_RE = re.compile(r"\[PASS\]| passed| PASS=")
_FAIL_RE = re.compile(r"\[FAIL\]| failed| FAIL=[1-9]")
_SUMMARY_RE = re.compile(r"TESTS=[0-9]+ PASS=[0-9]+ FAIL=[0-9]+")


def _count_lines(pattern: "re.Pattern[str]", text: str) -> int:
    """Replicate ``grep -c`` semantics: number of matching lines."""
    if not text:
        return 0
    return sum(1 for line in text.splitlines() if pattern.search(line))


def main() -> int:
    log = os.environ.get("BENCHMARK_LOG", ".benchmark")
    ts = time.strftime("%Y-%m-%dT%H:%M:%S")
    out = os.environ.get("HOOK_TOOL_OUTPUT", "")

    errors = _count_lines(_ERROR_RE, out)
    warnings = _count_lines(_WARNING_RE, out)
    passes = _count_lines(_PASS_RE, out)
    fails = _count_lines(_FAIL_RE, out)

    summary_matches = _SUMMARY_RE.findall(out)
    if summary_matches:
        summary = summary_matches[-1]
        passes = summary.split("PASS=", 1)[1].split(" ", 1)[0]
        fails = summary.split("FAIL=", 1)[1].split(" ", 1)[0]

    status = "PASS" if errors == 0 and warnings == 0 else "FAIL"

    with open(log, "a", encoding="utf-8") as handle:
        handle.write(
            f"{ts} sim_capture={status} errors={errors} warnings={warnings} "
            f"pass={passes} fail={fails}\n"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
