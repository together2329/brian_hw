#!/usr/bin/env python3
"""check_no_ip_coverage_workarounds.py — port of the same-named .sh (tb-gen).

Reject per-IP coverage workaround artifacts from tb-gen.  Static/code coverage
must be produced by workflow/coverage; tb-gen must not create one-off Verilator
harnesses or summary parsers under an IP TB directory to force coverage DONE.

CLI / env contract preserved (bash ``set -u``):
  * IP = ``$IP_NAME`` else first positional argument.  If empty, discover it
    from ``find . -maxdepth 3 -type f -name '*.ssot.yaml' | sort -t/ -k2 |
    head -1 | awk -F/ '{print $(NF-2)}'``.
  * If IP is empty or ``$IP`` is not a directory ⇒ FAIL, exit 1.
  * Forbidden artifacts under ``<ip>/tb`` (any depth) by name:
      ``*coverage_summary*.py``, ``*cov_harness*.sv``,
      ``*coverage_harness*.sv``, ``*verilator*harness*.sv``.
    Any match ⇒ FAIL (print sorted unique list), exit 1.  None ⇒ PASS, exit 0.
"""

from __future__ import annotations

import fnmatch
import os
import sys
from pathlib import Path


_FORBIDDEN_GLOBS = (
    "*coverage_summary*.py",
    "*cov_harness*.sv",
    "*coverage_harness*.sv",
    "*verilator*harness*.sv",
)


def _discover_ip() -> str:
    """Mirror: find -name '*.ssot.yaml' (maxdepth 3) | sort -t/ -k2 | head -1
    then awk -F/ '{print $(NF-2)}'."""
    base_depth = len(Path(".").parts)
    candidates: "list[str]" = []
    for dirpath, dirnames, filenames in os.walk("."):
        depth = len(Path(dirpath).parts) - base_depth + 1
        if depth > 3:
            dirnames[:] = []
            continue
        for name in filenames:
            if name.endswith(".ssot.yaml"):
                candidates.append(str(Path(dirpath) / name))
        if depth >= 3:
            dirnames[:] = []

    if not candidates:
        return ""

    # sort -t/ -k2 : sort by the 2nd '/'-delimited field onward.
    def _key(path: str) -> "list[str]":
        fields = path.split("/")
        return fields[1:]

    candidates.sort(key=_key)
    first = candidates[0]
    # awk -F/ '{print $(NF-2)}'
    fields = first.split("/")
    if len(fields) >= 3:
        return fields[-3]
    return ""


def main(argv: "list[str] | None" = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    ip = os.environ.get("IP_NAME") or (argv[0] if argv else "")
    if not ip:
        ip = _discover_ip()

    if not ip or not Path(ip).is_dir():
        print("[check_no_ip_coverage_workarounds] FAIL: cannot locate IP directory")
        return 1

    bad: "list[str]" = []
    tb_dir = Path(ip) / "tb"
    if tb_dir.is_dir():
        for dirpath, _dirnames, filenames in os.walk(tb_dir):
            for name in filenames:
                if any(fnmatch.fnmatch(name, pat) for pat in _FORBIDDEN_GLOBS):
                    bad.append(str(Path(dirpath) / name))
        bad = sorted(set(bad))

    if bad:
        print(
            "[check_no_ip_coverage_workarounds] FAIL: IP-specific coverage "
            "workaround artifacts found"
        )
        for path in bad:
            print(path)
        print(
            "Static/code coverage must use workflow/coverage generic tools and "
            "SSOT summary."
        )
        return 1

    print(
        "[check_no_ip_coverage_workarounds] PASS: no IP-specific coverage "
        f"workaround artifacts under {ip}/tb"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
