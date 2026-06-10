#!/usr/bin/env python3
"""gen_rtl.py — Python port of gen_rtl.sh (ssot-gen).

Legacy alias for the SSOT-to-RTL handoff.  ssot-gen does not run fixed RTL
generators, so this script always blocks (exit 2) after printing guidance.

CLI / env contract (preserved from bash ``set -euo pipefail``):
  * Module name = first positional argument else ``$HOOK_CMD_ARGS``.
  * Missing module name ⇒ ``[ERROR] ...`` usage, exit 1.
  * Otherwise print the two BLOCKED guidance lines, exit 2.
"""

from __future__ import annotations

import os
import sys


def main(argv: "list[str] | None" = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    # Bash: MODULE_NAME="${1:-${HOOK_CMD_ARGS:-}}"
    module_name = argv[0] if argv else os.environ.get("HOOK_CMD_ARGS", "")

    if not module_name:
        print("[ERROR] Module name required. Usage: /gen-rtl <module_name>")
        return 1

    print("[gen_rtl] BLOCKED: ssot-gen does not run fixed RTL generators.")
    print(f"[gen_rtl] Validate SSOT, then run: /gen-rtl {module_name}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
