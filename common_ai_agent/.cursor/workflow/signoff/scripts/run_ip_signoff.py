#!/usr/bin/env python3
"""run_ip_signoff.py — Python port of run_ip_signoff.sh (signoff).

Thin launcher that resolves the IP name and project root, then delegates to
``check_ip_signoff.py`` (re-executed via the running interpreter so the verdict
and exit code come straight from that script).

CLI / env contract preserved from the bash original:
  * IP name = ``$IP_NAME`` else first positional argument.
  * ROOT    = ``$ATLAS_PROJECT_ROOT`` else ``$ATLAS_ROOT`` else ``.``.
  * Missing IP ⇒ usage to stderr, exit 2.
  * Remaining args accept ``--root <dir>`` / ``--root=<dir>``; anything else ⇒
    "unknown argument" to stderr, exit 2.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main(argv: "list[str] | None" = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    ip = os.environ.get("IP_NAME") or (argv[0] if argv else "")
    root = os.environ.get("ATLAS_PROJECT_ROOT") or os.environ.get("ATLAS_ROOT") or "."

    if not ip:
        print(
            "[ip-signoff] usage: run_ip_signoff.sh <ip> [--root <ip-parent>]",
            file=sys.stderr,
        )
        return 2

    # Bash: shift || true  (drop the IP positional, if present)
    rest = argv[1:] if argv else []
    i = 0
    while i < len(rest):
        arg = rest[i]
        if arg == "--root":
            root = rest[i + 1] if i + 1 < len(rest) else ""
            i += 2
        elif arg.startswith("--root="):
            root = arg[len("--root="):]
            i += 1
        else:
            print(f"[ip-signoff] unknown argument: {arg}", file=sys.stderr)
            return 2

    script_dir = Path(__file__).resolve().parent
    proc = subprocess.run(
        [sys.executable, str(script_dir / "check_ip_signoff.py"), ip, "--root", root]
    )
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
