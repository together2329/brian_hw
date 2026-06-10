#!/usr/bin/env python3
"""error_capture.py — Python port of error_capture.sh (rtl-gen).

Extract up to the first five error/failed lines from ``HOOK_TOOL_OUTPUT`` and,
when any are found, append a ``<ts> rtl_errors:`` header followed by each
matching line (indented two spaces) to the benchmark log.
"""

from __future__ import annotations

import os
import re
import time


# grep -i -E "error|failed"
_ERR_RE = re.compile(r"error|failed", re.IGNORECASE)


def main() -> int:
    log = os.environ.get("BENCHMARK_LOG", ".benchmark")
    ts = time.strftime("%Y-%m-%dT%H:%M:%S")
    out = os.environ.get("HOOK_TOOL_OUTPUT", "")

    matches = [line for line in out.splitlines() if _ERR_RE.search(line)][:5]
    if matches:
        with open(log, "a", encoding="utf-8") as handle:
            handle.write(f"{ts} rtl_errors:\n")
            for line in matches:
                handle.write(f"  {line}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
