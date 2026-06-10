#!/usr/bin/env python3
"""coverage.py — Python port of coverage.sh (tb-gen).

Simple branch coverage hint (grep-based, no simulator required).

CLI / env contract preserved:
  * MODULE = ``$HOOK_CMD_ARGS`` else first positional argument; if empty,
    pick the first ``./*.sv`` (maxdepth 1) excluding ``tb_*`` / ``tc_*``.
  * ``SRC = ${MODULE%.sv}.sv`` (so both ``foo`` and ``foo.sv`` resolve to
    ``foo.sv``).  Missing SRC ⇒ ``DUT not found: <src>`` and exit 1.
  * Print approximate if/case branch counts and, if ``tc_<module>.sv`` exists,
    its task count and task lines.

Faithful port note: the branch counts come from the very same grep invocations
the ``.sh`` used (``grep -c "if\\s*("`` etc.).  These regexes rely on
``\\s``/``\\d`` which BSD grep treats literally — the port shells out to the
identical commands so the counts match the ``.sh`` on whatever host runs it.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _grep_c(pattern: str, path: str) -> str:
    """Run ``grep -c <pattern> <path> || true`` and return the count string."""
    proc = subprocess.run(
        ["grep", "-c", pattern, path], capture_output=True, text=True
    )
    # grep -c prints the count on stdout regardless of match; `|| true` in the
    # .sh keeps a no-match (rc 1) from aborting. Return the trimmed stdout.
    return proc.stdout.strip()


def _find_default_module() -> str:
    # find . -maxdepth 1 -name "*.sv" | grep -v "tb_\|tc_" | head -1 | sed 's|./||'
    proc = subprocess.run(
        ["/bin/sh", "-c",
         r"""find . -maxdepth 1 -name "*.sv" | grep -v "tb_\|tc_" | head -1 | sed 's|./||' """],
        capture_output=True, text=True,
    )
    return proc.stdout.strip()


def main(argv: "list[str] | None" = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    module = os.environ.get("HOOK_CMD_ARGS") or (argv[0] if argv else "")
    if not module:
        module = _find_default_module()

    # SRC="${MODULE%.sv}.sv" ; TC="tc_${MODULE%.sv}.sv"
    stem = module[:-3] if module.endswith(".sv") else module
    src = f"{stem}.sv"
    tc = f"tc_{stem}.sv"

    if not Path(src).is_file():
        print(f"DUT not found: {src}")
        return 1

    print(f"=== Coverage Hint: {src} ===")
    print()

    if_branches = _grep_c(r"if\s*(", src)
    case_items = _grep_c(r"^\s*[0-9a-fA-Fx']*\s*:", src)
    print("DUT branches (approx):")
    print(f"  if statements : {if_branches}")
    print(f"  case items    : {case_items}")
    print()

    if Path(tc).is_file():
        tc_tasks = _grep_c(r"^task", tc)
        print(f"Test cases in {tc}: {tc_tasks} tasks")
        # grep "^task" "${TC}" | sed 's/^/  /'
        proc = subprocess.run(
            ["/bin/sh", "-c", f'grep "^task" "{tc}" | sed "s/^/  /"'],
            capture_output=True, text=True,
        )
        sys.stdout.write(proc.stdout)
    else:
        print(f"TC file not found: {tc} — run /gen-tc first")

    print()
    print("Note: For full coverage use verilator --coverage or VCS/Questa")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
