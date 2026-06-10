#!/usr/bin/env python3
"""check_rtl_disk.py — Disk-truth validator for rtl-gen tasks.

Python port of check_rtl_disk.sh for native-Windows portability.

Verifies real RTL artifacts exist on disk + compile clean. Replaces
stdout-grep validators that let agents fake "0 lint errors" without
actually writing or compiling files.

Inputs (env):
  IP_NAME — IP slug (auto-detected from cwd if missing)
  MIN_RTL — minimum bytes per .v/.sv file (default 200)

Exit 0 = filelist exists + every listed RTL file >= MIN_RTL bytes
         + iverilog -c compile passes (parse-only, no -o).
Exit 1 = otherwise.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def _auto_detect_ip() -> str:
    """Replicate: find . -maxdepth 3 -type f -name '*.ssot.yaml'
    | sort -t/ -k2 | head -1 | awk -F/ '{print $(NF-2)}'."""
    root = Path(".")
    matches: list[str] = []
    for pat in ("*/*/*.ssot.yaml", "*/*.ssot.yaml", "*.ssot.yaml"):
        for path in root.glob(pat):
            matches.append("./" + path.as_posix())

    def sort_key(item: str) -> str:
        parts = item.split("/")
        return parts[1] if len(parts) > 1 else ""

    matches.sort(key=sort_key)
    if not matches:
        return ""
    fields = matches[0].split("/")
    return fields[-3] if len(fields) >= 3 else ""


def _strip_filelist_line(line: str) -> str:
    """Port of: echo "$line" | sed 's|//.*||' | xargs.

    Removes // comments, then xargs collapses/strips surrounding whitespace
    (and would split on whitespace; filelist entries are single tokens)."""
    no_comment = re.sub(r"//.*", "", line)
    # xargs with no command echoes the args space-joined after word-splitting.
    tokens = no_comment.split()
    return " ".join(tokens)


def main(argv: list[str]) -> int:
    ip = os.environ.get("IP_NAME") or (argv[0] if argv else "")
    if not ip:
        ip = _auto_detect_ip()

    if not ip or not Path(ip).is_dir():
        print("[check_rtl_disk] FAIL: IP dir not found")
        return 1

    list_path = Path(ip) / "list" / f"{ip}.f"
    min_rtl = int(os.environ.get("MIN_RTL", "200"))

    if not list_path.is_file():
        print(f"[check_rtl_disk] FAIL: filelist {list_path.as_posix()} missing")
        return 1

    fail = 0
    for raw_line in list_path.read_text(encoding="utf-8", errors="replace").splitlines():
        f = _strip_filelist_line(raw_line)
        if not f:
            continue
        # Skip non-RTL files (e.g. tb_*.sv lines for sim mode).
        if not re.search(r"\.(v|sv|vh|svh)$", f):
            continue
        # Resolve relative to IP/.. (filelist paths usually relative to IP root).
        fpath = Path(ip) / f
        if not fpath.is_file():
            fpath = Path(f)  # fallback: as-given
        if not fpath.is_file():
            print(f"[check_rtl_disk] FAIL: filelist references missing file: {f}")
            fail = 1
            continue
        sz = fpath.stat().st_size
        if sz < min_rtl:
            print(f"[check_rtl_disk] FAIL: {f} = {sz}B (need ≥{min_rtl})")
            fail = 1

    if fail != 0:
        return 1

    # Compile check (parse-only). iverilog -c reads filelist, -o /dev/null → parse only.
    # Filelist paths are usually relative to IP root, so cd there first.
    if shutil.which("iverilog"):
        list_rel = list_path.name
        null_out = "NUL" if os.name == "nt" else "/dev/null"
        with tempfile.NamedTemporaryFile(
            mode="w+", suffix="_rtl_compile.err", delete=False, encoding="utf-8"
        ) as errfile:
            err_path = errfile.name
        try:
            with open(err_path, "w", encoding="utf-8") as errf:
                proc = subprocess.run(
                    ["iverilog", "-g2012", "-Irtl", "-f", f"list/{list_rel}", "-o", null_out],
                    cwd=ip,
                    stdout=errf,
                    stderr=errf,
                )
            if proc.returncode != 0:
                print("[check_rtl_disk] FAIL: iverilog compile errors:")
                with open(err_path, encoding="utf-8", errors="replace") as errf:
                    for line in errf.read().splitlines()[:10]:
                        print(f"  {line}")
                return 1
        finally:
            try:
                os.unlink(err_path)
            except OSError:
                pass

    print(f"[check_rtl_disk] PASS: filelist OK, all RTL files ≥{min_rtl}B, compile clean")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
