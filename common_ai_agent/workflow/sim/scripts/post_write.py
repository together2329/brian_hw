#!/usr/bin/env python3
"""post_write.py — Python port of post_write.sh (sim).

Append a benchmark log line recording the file written by the most recent write
tool call, parsed from ``HOOK_TOOL_ARGS``.

Faithful port note: the original extracts the path with

    FILE=$(echo "${ARGS}" | grep -oP '(?<=path=")[^"]+|(?<=")[^"]+\\.(?:sv|v|py)' | head -1)

and only logs when ``$FILE`` is non-empty (no fallback).  ``grep -oP`` is a
GNU-PCRE feature; on hosts without it (e.g. macOS BSD grep) the command fails,
``$FILE`` is empty and NOTHING is written (the log file is not even created).
To reproduce that exactly on whatever host runs it, the extraction is shelled
out to the identical ``grep -oP`` pipeline rather than re-implemented in Python.
"""

from __future__ import annotations

import os
import subprocess
import time


_GREP_CMD = (
    """grep -oP '(?<=path=")[^"]+|(?<=")[^"]+\\.(?:sv|v|py)' 2>/dev/null | head -1"""
)


def _extract_file(args: str) -> str:
    proc = subprocess.run(
        ["/bin/sh", "-c", f'echo "$ARGS" | {_GREP_CMD}'],
        capture_output=True, text=True, env={**os.environ, "ARGS": args},
    )
    return proc.stdout.rstrip("\n")


def main() -> int:
    log = os.environ.get("BENCHMARK_LOG", ".benchmark")
    ts = time.strftime("%Y-%m-%dT%H:%M:%S")
    args = os.environ.get("HOOK_TOOL_ARGS", "")

    file = _extract_file(args)
    if file:
        with open(log, "a", encoding="utf-8") as handle:
            handle.write(f"{ts} write file={file}\n")
        return 0
    # Bash final statement is ``[ -n "${FILE}" ] && echo ... >> "${LOG}"``.
    # When FILE is empty the ``[ -n ]`` test is false, so the script's exit
    # status is 1 and nothing is logged.  Mirror that exit code.
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
