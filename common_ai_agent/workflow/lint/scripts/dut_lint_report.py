#!/usr/bin/env python3
"""Run DUT-only RTL lint and write <ip>/lint/dut_lint.json.

The report is the canonical ATLAS progress evidence for lint approval. It
intentionally excludes TB, cocotb, vvp, and simulator-result artifacts.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def _filelist_entries(ip_dir: Path, ip_name: str) -> list[str]:
    filelist = ip_dir / "list" / f"{ip_name}.f"
    entries: list[str] = []
    if not filelist.is_file():
        return entries
    for raw in filelist.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.split("//", 1)[0].strip()
        if not line or line.startswith("+"):
            continue
        if line.endswith((".v", ".sv", ".vh", ".svh")) and "/tb/" not in line and not line.startswith("tb/"):
            entries.append(line)
    return entries


def _suppression_violations(ip_dir: Path, entries: list[str]) -> list[dict[str, str | int]]:
    """Find ad-hoc lint suppression comments in DUT RTL sources.

    Generated RTL should root-cause lint warnings. Suppression comments hide
    diagnostics from Verilator, so the canonical report marks them as policy
    violations unless a higher-level flow later proves an exact SSOT waiver.
    """

    violations: list[dict[str, str | int]] = []
    suppression_re = re.compile(r"verilator\s+lint_(?:off|on)\b|-Wno-[A-Za-z0-9_]+")
    for rel in entries:
        if not rel.endswith((".v", ".sv", ".vh", ".svh")):
            continue
        path = ip_dir / rel
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for idx, line in enumerate(lines, start=1):
            if suppression_re.search(line):
                violations.append({
                    "file": rel,
                    "line": idx,
                    "text": line.strip()[:240],
                })
    return violations


def _count_diagnostics(text: str) -> dict[str, int]:
    summary = re.search(r"%Error:\s+Exiting due to\s+(\d+)\s+error\(s\),\s+(\d+)\s+warning\(s\)", text, re.I)
    if summary:
        return {"errors": int(summary.group(1)), "warnings": int(summary.group(2))}
    errors = 0
    warnings = 0
    for line in text.splitlines():
        upper = line.upper()
        if re.search(r"%ERROR:\s+EXITING DUE TO \d+ WARNING", upper):
            continue
        if re.search(r"%ERROR\b|(^|\s)(ERROR|FATAL)(:|-)|\b\d+\s+ERROR\(S\)", line, re.I):
            errors += 1
        elif re.search(r"%WARNING-|:\s*WARNING:|\bSORRY:", line, re.I):
            warnings += 1
    return {"errors": errors, "warnings": warnings}


def _tool_command(ip_name: str, top: str) -> tuple[str, list[str]]:
    if shutil.which("verilator"):
        return "verilator", [
            "verilator",
            "--lint-only",
            "-Wall",
            "-Irtl",
            "-f",
            f"list/{ip_name}.f",
            "--top-module",
            top,
        ]
    if shutil.which("iverilog"):
        return "iverilog", [
            "iverilog",
            "-g2012",
            "-Wall",
            "-Irtl",
            "-f",
            f"list/{ip_name}.f",
            "-s",
            top,
            "-o",
            f"/tmp/{ip_name}_dut_lint.vvp",
        ]
    raise RuntimeError("No DUT lint tool found: install verilator or iverilog")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ip", help="IP directory/name, for example dma")
    parser.add_argument("--top", default=None, help="Top module name; defaults to IP name")
    args = parser.parse_args()

    project_root = Path.cwd().resolve()
    ip_dir = (project_root / args.ip).resolve()
    ip_name = ip_dir.name
    top = args.top or ip_name
    if not ip_dir.is_dir():
        print(f"[dut_lint_report] FAIL: IP dir not found: {ip_dir}", file=sys.stderr)
        return 2
    filelist = ip_dir / "list" / f"{ip_name}.f"
    if not filelist.is_file():
        print(f"[dut_lint_report] FAIL: filelist missing: {filelist}", file=sys.stderr)
        return 2

    lint_dir = ip_dir / "lint"
    lint_dir.mkdir(parents=True, exist_ok=True)
    tool, command = _tool_command(ip_name, top)
    proc = subprocess.run(command, cwd=ip_dir, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = proc.stdout or ""
    diag = _count_diagnostics(output)
    rtl_files = _filelist_entries(ip_dir, ip_name)
    suppression_violations = _suppression_violations(ip_dir, rtl_files)
    report = {
        "schema_version": 1,
        "type": "dut_lint",
        "scope": "dut",
        "dut_only": True,
        "tool": tool,
        "command": " ".join(command),
        "cwd": str(ip_dir.relative_to(project_root)),
        "top": top,
        "filelist": str(filelist.relative_to(project_root)),
        "rtl_files": rtl_files,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "returncode": proc.returncode,
        "errors": diag["errors"],
        "warnings": diag["warnings"],
        "waived_warnings": 0,
        "suppression_violation_count": len(suppression_violations),
        "suppression_violations": suppression_violations,
        "policy": "DUT RTL must be lint-clean without ad-hoc verilator lint_off/lint_on or -Wno suppressions unless represented by exact SSOT waivers.",
        "passed": (
            proc.returncode == 0
            and diag["errors"] == 0
            and diag["warnings"] == 0
            and not suppression_violations
        ),
    }
    (lint_dir / "dut_lint.log").write_text(output, encoding="utf-8")
    (lint_dir / "dut_lint.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"[dut_lint_report] wrote {lint_dir / 'dut_lint.json'}")
    print(
        f"[dut_lint_report] {tool}: errors={diag['errors']} warnings={diag['warnings']} "
        f"suppression_violations={len(suppression_violations)} returncode={proc.returncode}"
    )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
