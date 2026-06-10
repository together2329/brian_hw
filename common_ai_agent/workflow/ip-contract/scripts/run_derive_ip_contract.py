#!/usr/bin/env python3
"""run_derive_ip_contract.py — Python port of run_derive_ip_contract.sh.

Thin launcher that delegates to ``derive_ip_contract.py``.  CLI / env contract
preserved from the bash original (which used ``set -euo pipefail``):

  * IP name = first positional argument; missing ⇒ usage to stderr, exit 2.
  * ROOT    = ``$ATLAS_PROJECT_ROOT`` else ``$ATLAS_ROOT`` else ``ip_examples``.
  * All trailing args after the IP name are forwarded verbatim.

The bash used ``exec``; here we run the child and propagate its exit code,
which yields the same observable CLI behaviour.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main(argv: "list[str] | None" = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    ip = argv[0] if argv else ""
    if not ip:
        # Bash: echo "[derive-ip-contract] usage: $0 <ip_name> ..." with $0
        # being the .sh path.  Mirror that by using the .sh sibling path so the
        # usage line is identical to the original.
        prog = str(Path(__file__).resolve().with_suffix(".sh"))
        print(
            f"[derive-ip-contract] usage: {prog} <ip_name> [--root <ip-parent>]",
            file=sys.stderr,
        )
        return 2

    rest = argv[1:]  # Bash: shift || true
    root = os.environ.get("ATLAS_PROJECT_ROOT") or os.environ.get("ATLAS_ROOT") or "ip_examples"

    script_dir = Path(__file__).resolve().parent
    workflow_root = script_dir.parent.parent
    target = workflow_root / "ip-contract" / "scripts" / "derive_ip_contract.py"

    proc = subprocess.run(
        [sys.executable, str(target), ip, "--root", root, *rest]
    )
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
