#!/usr/bin/env python3
"""error_log.py — Append lint error/warning lines from $HOOK_TOOL_OUTPUT.

Python port of error_log.sh. Greps the hook tool output for error/warning lines
(case-insensitive, first 10), and if any exist appends a ``<ts> lint_issues:``
header plus each line indented two spaces to $BENCHMARK_LOG (default .benchmark).

Usage: error_log.py   (driven by env: HOOK_TOOL_OUTPUT, BENCHMARK_LOG)
"""

from __future__ import annotations

import os
import sys
import time


def main(argv: list[str]) -> int:
    log = os.environ.get("BENCHMARK_LOG", ".benchmark")
    ts = time.strftime("%Y-%m-%dT%H:%M:%S")
    output = os.environ.get("HOOK_TOOL_OUTPUT", "")

    # echo "$HOOK_TOOL_OUTPUT" | grep -i -E "error|warning" | head -10
    matched = [
        ln
        for ln in output.split("\n")
        if "error" in ln.lower() or "warning" in ln.lower()
    ][:10]

    # [ -n "$LINES" ] && echo "...lint_issues:" >> LOG && echo "$LINES" | sed 's/^/  /' >> LOG
    if matched:
        with open(log, "a", encoding="utf-8") as fh:
            fh.write(f"{ts} lint_issues:\n")
            fh.write("\n".join("  " + ln for ln in matched) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
