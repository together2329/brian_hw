#!/usr/bin/env python3
"""post_write.py — Python port of post_write.sh (rtl-gen).

Append a ``rtl_write`` benchmark log line.  Unlike sim/post_write.sh this
*always* writes a line: if the ``grep -oP`` path extraction yields nothing it
falls back to ``${ARGS%%,*}`` (the substring up to the first comma).

Faithful port note: the ``grep -oP '(?<=path=")[^"]+|(?<=")[^"]+\\.(?:sv|v)'``
extraction is GNU-PCRE only; on hosts without it (macOS BSD grep) the command
fails and the ``${ARGS%%,*}`` fallback kicks in.  The extraction is shelled out
to the identical pipeline so the result matches the ``.sh`` on whatever host
runs it.
"""

from __future__ import annotations

import os
import subprocess
import time


_GREP_CMD = (
    """grep -oP '(?<=path=")[^"]+|(?<=")[^"]+\\.(?:sv|v)' 2>/dev/null | head -1"""
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
    if not file:
        # Bash: FILE="${ARGS%%,*}" (substring up to first comma).
        file = args.split(",", 1)[0]

    with open(log, "a", encoding="utf-8") as handle:
        handle.write(f"{ts} rtl_write file={file}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
