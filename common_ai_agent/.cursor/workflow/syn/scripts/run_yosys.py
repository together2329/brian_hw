#!/usr/bin/env python3
"""run_yosys.py — Invoke yosys on <ip>/syn/run.ys; capture log to syn.log.

Python port of run_yosys.sh for native-Windows portability. Same CLI, exit
codes, and invocation (``yosys -l <log> <script>``).

Args: <ip_name>

Falls back to HOOK_CMD_ARGS for the IP name when no positional arg is given
(matching the shell original). Sources pdk_env semantics via pdk_env.py.

Exit codes: 2 usage/missing script, 3 yosys not on PATH, 4 PDK liberty
unreadable, otherwise yosys's own return code (PIPESTATUS[0] in the shell).
"""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

# Import the pdk_env port (mirrors `source pdk_env.sh`).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))
import pdk_env  # noqa: E402


def _resolve_ip(argv: list[str]) -> str:
    args = list(argv)
    if not args and os.environ.get("HOOK_CMD_ARGS", ""):
        args = shlex.split(os.environ["HOOK_CMD_ARGS"])
    return args[0] if args else ""


def _tail(text: str, n: int) -> str:
    """``tail -<n>`` on a string's lines (preserving the trailing newline)."""
    lines = text.splitlines(keepends=True)
    return "".join(lines[-n:])


def main(argv: list[str]) -> int:
    ip = _resolve_ip(argv)
    if not ip:
        print("[SYN] usage: run_yosys.sh <ip_name>", file=sys.stderr)
        return 2

    pdk_env.apply_pdk_env(os.environ)

    script = f"{ip}/syn/run.ys"
    log = f"{ip}/syn/out/syn.log"
    Path(ip, "syn", "out").mkdir(parents=True, exist_ok=True)

    if not Path(script).is_file():
        print(f"[SYN] missing {script}", file=sys.stderr)
        return 2
    if shutil.which("yosys") is None:
        print("[SYN TOOL MISSING] yosys not on PATH", file=sys.stderr)
        return 3
    lib = os.environ.get("SKY130_LIB", "")
    if not lib or not os.access(lib, os.R_OK):
        print("[SYN MISSING PDK] $SKY130_LIB unreadable", file=sys.stderr)
        return 4

    # `yosys -l "$LOG" "$SCRIPT" 2>&1 | tail -120` — yosys writes its own log via
    # -l; here we additionally merge stdout+stderr, echo the last 120 lines, and
    # take yosys's exit code (PIPESTATUS[0]).
    proc = subprocess.run(
        ["yosys", "-l", log, script],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    rc = proc.returncode
    combined = proc.stdout or ""
    sys.stdout.write(_tail(combined, 120))
    sys.stdout.flush()

    print(f"[SYN] yosys rc={rc} log={log} liberty={lib}")
    if rc != 0:
        print("[SYN] yosys failed; last log lines:", file=sys.stderr)
        try:
            log_text = Path(log).read_text(encoding="utf-8", errors="replace")
            sys.stderr.write(_tail(log_text, 80))
            sys.stderr.flush()
        except OSError:
            pass
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
