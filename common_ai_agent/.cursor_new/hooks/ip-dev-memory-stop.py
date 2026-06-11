#!/usr/bin/env python3
"""Cursor stop hook wrapper for IP development memory closure."""

import subprocess
import sys
from pathlib import Path


def find_root() -> Path:
    current = Path.cwd().resolve()
    for candidate in (current, *current.parents):
        if (candidate / "scripts" / "ip_dev_memory.py").is_file():
            return candidate
    return current


def main() -> int:
    root = find_root()
    payload = sys.stdin.read()
    proc = subprocess.run(
        [sys.executable, str(root / "scripts" / "ip_dev_memory.py"), "hook-stop", "--surface", "cursor"],
        input=payload,
        text=True,
    )
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
