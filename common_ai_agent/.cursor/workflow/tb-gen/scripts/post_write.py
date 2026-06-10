#!/usr/bin/env python3
"""post_write.py — Python port of post_write.sh (tb-gen).

Append a ``tb_write`` or ``tc_write`` benchmark log line.  Always writes a line:
if the ``grep -oP`` path extraction yields nothing it falls back to
``${ARGS%%,*}``.  The record TYPE is ``tc`` when the resolved file contains
``tc_`` (``grep -q "tc_"``), otherwise ``tb``.

Faithful port note: the ``grep -oP '(?<=path=")[^"]+|(?<=")[^"]+\\.(?:sv|v|py)'``
extraction is GNU-PCRE only and is shelled out to the identical pipeline so the
result matches the ``.sh`` on whatever host runs it (macOS BSD grep fails the
extraction and the ``${ARGS%%,*}`` fallback applies).
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
    if not file:
        file = args.split(",", 1)[0]

    # Bash: TYPE="tb"; echo "${FILE}" | grep -q "tc_" && TYPE="tc"
    type_ = "tc" if "tc_" in file else "tb"

    with open(log, "a", encoding="utf-8") as handle:
        handle.write(f"{ts} {type_}_write file={file}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
