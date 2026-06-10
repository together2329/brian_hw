#!/usr/bin/env python3
"""sig_search.py — Python port of sig_search.sh (sim_debug).

Search for a signal name across every ``*.vcd`` under the current tree
(``find . -maxdepth 4 -name '*.vcd'``).  For each VCD with a matching
``$var ... <query> ...`` line (case-insensitive, first 10 matches), print the
file header and the indented matches.

CLI / env contract preserved:
  * Query = ``$HOOK_CMD_ARGS`` else first positional argument; empty ⇒
    ``Usage: /sig <name>`` and exit 1.

Faithful port note: the bash ran ``grep -i "\$var.*${QUERY}"`` with ``$QUERY``
interpolated unescaped, so the query is treated as part of the regex (literal
``$var`` prefix + ``.*`` + the query as an ERE-ish fragment).  Python ``re``
mirrors this by inserting the raw query into the pattern.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys


def _find_vcds() -> "list[str]":
    """Replicate ``find . -maxdepth 4 -name '*.vcd'`` exactly (incl. the
    leading ``./`` prefix and find's traversal order)."""
    proc = subprocess.run(
        ["/bin/sh", "-c", 'find . -maxdepth 4 -name "*.vcd" 2>/dev/null'],
        capture_output=True, text=True,
    )
    return [line for line in proc.stdout.split("\n") if line]


def main(argv: "list[str] | None" = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    query = os.environ.get("HOOK_CMD_ARGS") or (argv[0] if argv else "")
    if not query:
        print("Usage: /sig <name>")
        return 1

    print(f"=== Search: '{query}' across VCDs ===")
    hits = 0
    try:
        pattern = re.compile(r"\$var.*" + query, re.IGNORECASE)
    except re.error:
        # A malformed query would make grep print a regex error and find no
        # matches; degrade to "no matches" rather than crash.
        pattern = None

    for vcd in _find_vcds():
        matches: "list[str]" = []
        if pattern is not None:
            try:
                with open(vcd, "r", encoding="utf-8", errors="replace") as handle:
                    matches = [
                        line.rstrip("\n") for line in handle if pattern.search(line)
                    ][:10]
            except OSError:
                matches = []
        if matches:
            print()
            print(f"  {vcd}:")
            for line in matches:
                print(f"    {line}")
            hits += 1

    # Bash final statement: [ $HITS -eq 0 ] && echo "(no matches ...)".
    # The script's exit status is that of this last compound command, so:
    #   * HITS == 0 → echo runs → exit 0
    #   * HITS  > 0 → the [ ] test is false → exit 1
    if hits == 0:
        print("(no matches in any VCD)")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
