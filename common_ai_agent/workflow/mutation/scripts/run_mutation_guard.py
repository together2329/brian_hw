#!/usr/bin/env python3
"""Python port of run_mutation_guard.sh — 1:1 behavioral equivalent.

Thin launcher: resolves WORKFLOW_ROOT relative to this script, picks ROOT from
ATLAS_PROJECT_ROOT/ATLAS_ROOT (default "ip_examples"), then execs
mutation/scripts/mutation_guard.py with `<ip> --root <root> [extra args...]`.

The shell original uses `set -euo pipefail` and `exec`; this port mirrors the
control flow: missing IP -> usage on stderr + exit 2, otherwise replace the
current process with the mutation_guard.py invocation (os.execv) so exit codes
propagate identically.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    # IP="${1:-}"
    ip = argv[0] if argv else ""
    if not ip:
        print(
            f"[mutation-guard] usage: {sys.argv[0]} <ip_name> "
            "[--root <ip-parent>] [mutation_guard.py args...]",
            file=sys.stderr,
        )
        return 2
    # shift || true  -> remaining args after the IP
    rest = argv[1:]

    # SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    script_dir = Path(__file__).resolve().parent
    # WORKFLOW_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
    workflow_root = (script_dir / ".." / "..").resolve()
    # ROOT="${ATLAS_PROJECT_ROOT:-${ATLAS_ROOT:-ip_examples}}"
    root = os.environ.get("ATLAS_PROJECT_ROOT") or os.environ.get("ATLAS_ROOT") or "ip_examples"

    guard = str(workflow_root / "mutation" / "scripts" / "mutation_guard.py")
    # exec python3 "${...}/mutation_guard.py" "$IP" --root "$ROOT" "$@"
    cmd = [sys.executable, guard, ip, "--root", root, *rest]
    os.execv(sys.executable, cmd)
    # os.execv does not return on success; unreachable.
    return 127  # pragma: no cover


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
