#!/usr/bin/env python3
"""coverage_gaps.py — Python port of coverage_gaps.sh (coverage).

Identify the top-N uncovered regions from ``<DUT>/cov/annotated/`` output.
Verilator prefixes uncovered coverage points with a zero percent count such as
``%000000``; nonzero percent-prefixed counts (``%000002``) are hits and must
NOT be reported as gaps.

CLI / env contract preserved (bash ``set -e``):
  * DUT = ``$HOOK_CMD_ARGS`` else first positional argument else ``gpio_pad``;
    spaces stripped.
  * TOP_N = second positional argument else ``--top N`` else 10.
  * Missing ``<DUT>/cov/annotated`` ⇒ ERROR + exit 1.
  * Match unhit percent-prefixed annotations
    (``^%0+<space>`` or ``^%<spaces>0<space>``) recursively, take the first
    TOP_N, print them, then a by-file gap-count table (top 10 files).
  * Zero matches ⇒ guidance + exit 0.
"""

from __future__ import annotations

import os
import re
import sys
from collections import Counter
from pathlib import Path


# grep -rn -E '^%0+[[:space:]]|^%[[:space:]]+0[[:space:]]'
_GAP_RE = re.compile(r"^%0+[ \t]|^%[ \t]+0[ \t]")


def _grep_rn(ann: Path, top_n: int) -> "list[str]":
    """Replicate ``grep -rn -E <pat> <ann> | head -n <top_n>``.

    grep -r walks files (sorted), -n prefixes ``<file>:<lineno>:`` to each
    matching line.  Output order follows grep's recursive file traversal which
    we emulate with a sorted os.walk.
    """
    results: "list[str]" = []
    for dirpath, dirnames, filenames in os.walk(ann):
        dirnames.sort()
        for name in sorted(filenames):
            fpath = Path(dirpath) / name
            try:
                with open(fpath, "r", encoding="utf-8", errors="replace") as handle:
                    for lineno, line in enumerate(handle, start=1):
                        stripped = line.rstrip("\n")
                        if _GAP_RE.search(stripped):
                            results.append(f"{fpath}:{lineno}:{stripped}")
                            if len(results) >= top_n:
                                return results
            except OSError:
                continue
    return results


def _parse_args(argv: "list[str]") -> "tuple[str, int]":
    dut = os.environ.get("HOOK_CMD_ARGS") or (argv[0] if argv else "") or "gpio_pad"
    top_n_str = argv[1] if len(argv) > 1 else "10"
    # Honor "--top N" too (scan all args).
    for i, arg in enumerate(argv):
        if arg == "--top" and i + 1 < len(argv):
            top_n_str = argv[i + 1]
    dut = dut.replace(" ", "")
    try:
        top_n = int(top_n_str)
    except ValueError:
        top_n = 10
    return dut, top_n


def main(argv: "list[str] | None" = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    dut, top_n = _parse_args(argv)

    ann = Path(dut) / "cov" / "annotated"
    if not ann.is_dir():
        print(f"ERROR: {ann} not found — run /coverage-report first.")
        return 1

    print(f"=== Coverage Gaps (top {top_n}) — {ann}/ ===")
    print("")

    missed = _grep_rn(ann, top_n)

    if not missed:
        print("No unhit lines detected. Either coverage is 100% or annotation parse failed.")
        print(f"Try: head -50 {ann}/<somefile>.cov")
        return 0

    print(f"Top {len(missed)} unhit line(s):")
    for line in missed:
        print(f"  {line}")
    print("")

    # By-file gap count: cut -d: -f1 | sort | uniq -c | sort -rn | head -10
    #
    # Replicate the pipeline exactly so byte output matches the .sh:
    #   1. extract field 1 (path before first ':'),
    #   2. `sort` ascending then `uniq -c` → count per path, paths A→Z,
    #      count right-justified (BSD `uniq -c` pads to width 4 minimum),
    #   3. `sort -rn` → numeric-desc on the leading count; ties reverse the
    #      already-ascending path order (so equal counts come out Z→A),
    #   4. `head -10`.
    files = [line.split(":", 1)[0] for line in missed]
    counts = Counter(files)
    # Step 2: paths ascending, formatted like BSD `uniq -c` (right-justified
    # count in a 4-wide field, single space, then path).
    uniq_lines = [(cnt, name) for name, cnt in sorted(counts.items())]
    # Step 3: sort -rn — numeric desc on count, ties reverse path order.
    # Stable sort of the ascending-path list by (-count) keeps A→Z within a
    # count; `-r` reverses the whole stream, flipping ties to Z→A and counts to
    # desc. Emulate by sorting the ascending list descending with a reversed
    # secondary key.
    uniq_lines.sort(key=lambda item: (item[0], item[1]), reverse=True)
    print("=== By-file gap count (top 10 files) ===")
    for cnt, name in uniq_lines[:10]:
        print(f"{cnt:>4} {name}")
    print("")

    print(f"Hint: read each {ann}/<file>.cov to see context around the unhit lines,")
    print("then write directed tests that exercise those branches.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
