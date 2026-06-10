#!/usr/bin/env python3
"""find-mas.py — Python port of find-mas.sh (rtl-gen).

Locate ``*_mas.md`` files for rtl_gen / tb_gen.  Searches both the IP directory
structure (``<ip>/mas/<ip>_mas.md``) and the legacy flat layout
(``<ip>_mas.md``).

CLI / env contract preserved:
  * DIR = first positional argument, default ``.``.
  * Header uses ``realpath "$DIR"``.
  * MAS files: ``find <DIR> -maxdepth 4 -name '*_mas.md' | sort``.
  * Empty ⇒ "No *_mas.md files found." help block, exit 0.
  * Otherwise enumerate each MAS, detecting structured vs flat layout, printing
    line count + modified time + per-artifact presence (``✓`` / ``✗ missing``),
    and an Overview snippet; then a total and MODULE_NAME guidance.

Faithful port note: modified time (``stat -f "%Sm"`` BSD with GNU fallback),
``realpath``, the line-count ``wc -l`` and the Overview ``grep`` are shelled out
so the formatting matches the ``.sh`` on whatever host runs it.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _sh(cmd: str) -> str:
    proc = subprocess.run(["/bin/sh", "-c", cmd], capture_output=True, text=True)
    return proc.stdout


def _realpath(path: str) -> str:
    return _sh(f'realpath "{path}"').rstrip("\n")


def _mtime(path: str) -> str:
    # stat -f "%Sm" -t "%Y-%m-%d %H:%M" "$f" 2>/dev/null
    #   || stat -c "%y" "$f" 2>/dev/null | cut -d'.' -f1
    cmd = (
        f'stat -f "%Sm" -t "%Y-%m-%d %H:%M" "{path}" 2>/dev/null '
        f"""|| stat -c "%y" "{path}" 2>/dev/null | cut -d'.' -f1"""
    )
    return _sh(cmd).rstrip("\n")


def _line_count(path: str) -> str:
    # wc -l < "$f" | tr -d ' '
    return _sh(f'wc -l < "{path}" | tr -d " "').rstrip("\n")


def _overview(path: str) -> str:
    # OVERVIEW=$(grep -A1 "^## 1\. Overview" "$f" 2>/dev/null | tail -1 | head -c 80)
    # Command substitution strips trailing newlines, so drop them here too.
    cmd = (
        f'grep -A1 "^## 1\\. Overview" "{path}" 2>/dev/null | tail -1 | head -c 80'
    )
    return _sh(cmd).rstrip("\n")


def _find_mas(directory: str) -> "list[str]":
    cmd = f'find "{directory}" -maxdepth 4 -name "*_mas.md" 2>/dev/null | sort'
    out = _sh(cmd)
    return [line for line in out.split("\n") if line]


def main(argv: "list[str] | None" = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    directory = argv[0] if argv else "."

    print(f"=== MAS Files in: {_realpath(directory)} ===")
    print()

    mas_files = _find_mas(directory)
    if not mas_files:
        print("No *_mas.md files found.")
        print()
        print("Expected IP structure:")
        print("  <ip_name>/")
        print("  ├── mas/<ip_name>_mas.md   ← MAS document")
        print("  ├── rtl/<ip_name>.sv")
        print("  ├── list/<ip_name>.f")
        print("  ├── tb/tb_<ip_name>.sv")
        print("  ├── sim/sim_report.txt")
        print("  └── lint/lint_report.txt")
        print()
        print(
            "Tip: Run 'python3 src/main.py -w mas_gen' to generate a MAS "
            "document first."
        )
        return 0

    count = 0
    for f in mas_files:
        count += 1
        # MODULE=$(basename "$f" "_mas.md")
        module = os.path.basename(f)
        if module.endswith("_mas.md"):
            module = module[: -len("_mas.md")]
        created = _mtime(f)
        size = _line_count(f)

        parent_dir = os.path.basename(os.path.dirname(f))
        if parent_dir == "mas":
            ip_dir = os.path.dirname(os.path.dirname(f))
            ip_name = os.path.basename(ip_dir)
            layout = "structured"
            rtl_path = f"{ip_dir}/rtl/{ip_name}.sv"
            tb_path = f"{ip_dir}/tb/tb_{ip_name}.sv"
            list_path = f"{ip_dir}/list/{ip_name}.f"
            sim_path = f"{ip_dir}/sim/"
            lint_path = f"{ip_dir}/lint/"
        else:
            layout = "flat"
            rtl_path = f"{os.path.dirname(f)}/{module}.sv"
            tb_path = f"{os.path.dirname(f)}/tb_{module}.sv"
            list_path = ""
            sim_path = ""
            lint_path = ""

        overview = _overview(f)

        print(f"[{count}] {module}  ({layout})")
        print(f"    MAS    : {f}")
        print(f"    Lines  : {size} | Modified: {created}")
        if layout == "structured":
            rtl_status = "✓" if Path(rtl_path).is_file() else "✗ missing"
            tb_status = "✓" if Path(tb_path).is_file() else "✗ missing"
            list_status = "✓" if Path(list_path).is_file() else "✗ missing"
            print(f"    RTL    : {rtl_path}  [{rtl_status}]")
            print(f"    TB     : {tb_path}  [{tb_status}]")
            print(f"    Filelist: {list_path}  [{list_status}]")
            print(f"    Sim    : {sim_path}")
            print(f"    Lint   : {lint_path}")
        else:
            print(
                "    Layout : flat (consider migrating to "
                "<ip>/mas/<ip>_mas.md structure)"
            )
        # [ -n "$OVERVIEW" ] && echo "    Overview: $OVERVIEW..."
        if overview:
            print(f"    Overview: {overview}...")
        print()

    print(f"Total: {count} MAS document(s) found.")
    print()

    module_name = os.environ.get("MODULE_NAME", "")
    if module_name:
        print(f"Active MODULE_NAME: {module_name}")
        print(f"  → MAS: {module_name}/mas/{module_name}_mas.md")
        print(f"  → RTL: {module_name}/rtl/{module_name}.sv")
        print(f"  → TB:  {module_name}/tb/tb_{module_name}.sv")
    else:
        print("To set active module: export MODULE_NAME=<ip_name>")
        print("  rtl_gen will read: ${MODULE_NAME}/mas/${MODULE_NAME}_mas.md")
        print("  rtl_gen will write: ${MODULE_NAME}/rtl/${MODULE_NAME}.sv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
