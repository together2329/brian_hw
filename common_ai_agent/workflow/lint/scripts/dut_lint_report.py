#!/usr/bin/env python3
"""Run DUT-only RTL lint and write <ip>/lint/dut_lint.json.

The report is the canonical ATLAS progress evidence for lint approval. It
intentionally excludes TB, cocotb, vvp, and simulator-result artifacts.
The canonical lint gate runs both pyslang and Verilator.
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

REPO = Path(__file__).resolve().parents[3]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from core.pyslang_compat import compile_files as compile_pyslang_files
from core.pyslang_compat import diagnostic_is_error, diagnostic_line, diagnostic_message


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


def _strip_line_comment(line: str) -> str:
    return line.split("//", 1)[0]


def _policy_source_files(ip_dir: Path, entries: list[str]) -> list[tuple[str, Path]]:
    pairs: list[tuple[str, Path]] = []
    seen: set[Path] = set()
    for rel in entries:
        if not rel.endswith((".v", ".sv", ".vh", ".svh")):
            continue
        path = ip_dir / rel
        if not path.is_file():
            continue
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        pairs.append((rel, path))
    rtl_dir = ip_dir / "rtl"
    if rtl_dir.is_dir():
        for path in sorted(rtl_dir.glob("*_param.vh")):
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            pairs.append((str(path.relative_to(ip_dir)), path))
    return pairs


def _banned_syntax_patterns() -> list[tuple[str, re.Pattern[str], str]]:
    banned = [
        ("no_package", r"\b(?:package|endpackage)\b", "Do not use package/endpackage; use rtl/<ip>_param.vh plus module-local parameters."),
        ("no_import", r"\bimport\b|\b[A-Za-z_][A-Za-z0-9_]*::\*", "Do not use import or package scope references."),
        ("no_interface", r"\b(?:interface|endinterface|modport)\b", "Do not use interface/modport; use plain module ports."),
        ("no_function", r"\b(?:function|endfunction|task|endtask)\b", "Do not use function/task blocks in generated RTL."),
        ("no_for_loop", r"\bfor\s*\(", "Do not use for loops in generated RTL."),
        ("no_while_loop", r"\bwhile\s*\(", "Do not use while loops in generated RTL."),
        ("no_logic", r"\blogic\b", "Generated RTL uses Verilog-2001 syntax: use wire/reg, not logic."),
        ("no_typedef_enum", r"\b(?:typedef|enum)\b", "Generated RTL uses Verilog-2001 syntax: use localparam state encoding, not typedef/enum."),
        ("no_always_ff_comb", r"\balways_(?:ff|comb|latch)\b", "Generated RTL uses Verilog-2001 syntax: use always @(...) or always @(*)."),
        ("no_sv_integer_types", r"\b(?:bit|byte|int|longint|shortint)\b", "Generated RTL uses Verilog-2001 syntax: avoid SystemVerilog scalar integer types."),
    ]
    return [(rule, re.compile(pattern), message) for rule, pattern, message in banned]


def _style_violations(ip_dir: Path, entries: list[str]) -> list[dict[str, str | int]]:
    violations: list[dict[str, str | int]] = []
    banned_patterns = _banned_syntax_patterns()
    for rel, path in _policy_source_files(ip_dir, entries):
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for idx, raw in enumerate(lines, start=1):
            line = _strip_line_comment(raw)
            for rule, pattern, message in banned_patterns:
                if pattern.search(line):
                    violations.append({
                        "file": rel,
                        "line": idx,
                        "rule": rule,
                        "message": message,
                        "text": raw.strip()[:240],
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


def _parse_verilator_diagnostics(text: str) -> list[dict[str, str | int]]:
    """Extract file/line diagnostics from Verilator's lint output."""
    header_re = re.compile(
        r"^%(Warning|Error|Fatal)(?:-([A-Za-z0-9_]+))?:\s+(.+?):(\d+):(?:(\d+):)?\s*(.*)$"
    )
    diagnostics: list[dict[str, str | int]] = []
    current: dict[str, str | int] | None = None
    context: list[str] = []

    def finish_current() -> None:
        nonlocal current, context
        if current is None:
            context = []
            return
        snippet = ""
        for line in context:
            match = re.match(r"\s*\d+\s*\|\s?(.*)$", line)
            if match:
                snippet = match.group(1).rstrip()
                break
        if snippet:
            current["source"] = snippet
        diagnostics.append(current)
        current = None
        context = []

    for raw in text.splitlines():
        line = raw.rstrip()
        match = header_re.match(line)
        if match:
            finish_current()
            severity_raw, rule, file_name, line_no, column, message = match.groups()
            current = {
                "severity": "warning" if severity_raw.lower() == "warning" else "error",
                "rule": rule or severity_raw.upper(),
                "file": file_name.strip(),
                "line": int(line_no),
                "column": int(column or 0),
                "message": message.strip(),
            }
            continue
        if current is not None:
            context.append(line)
    finish_current()
    return diagnostics[:100]


def _verilator_command(ip_name: str, top: str) -> list[str]:
    return [
        "verilator",
        "--lint-only",
        "-Wall",
        "-Irtl",
        "-f",
        f"list/{ip_name}.f",
        "--top-module",
        top,
    ]


def _diagnostic_file(diag, sm) -> str:
    loc = getattr(diag, "location", None)
    if loc is None or sm is None:
        return ""
    for arg in (loc, getattr(loc, "buffer", None)):
        if arg is None:
            continue
        try:
            file_name = sm.getFileName(arg)
            if file_name:
                return str(file_name)
        except Exception:
            pass
    for attr in ("fileName", "filename", "file"):
        value = getattr(loc, attr, None)
        if value:
            return str(value)
    return ""


def _pyslang_lint(ip_dir: Path, entries: list[str]) -> dict:
    paths = [ip_dir / rel for rel in entries if rel.endswith((".v", ".sv", ".vh", ".svh"))]
    missing = [str(path.relative_to(ip_dir)) for path in paths if not path.is_file()]
    if missing:
        output = "pyslang missing file(s): " + ", ".join(missing)
        return {
            "tool": "pyslang",
            "available": True,
            "command": "pyslang " + " ".join(str(p.relative_to(ip_dir)) for p in paths),
            "returncode": 1,
            "errors": len(missing),
            "warnings": 0,
            "diagnostics": [{"severity": "error", "message": output}],
            "output": output,
            "passed": False,
        }
    if not paths:
        output = "pyslang no DUT RTL files in filelist"
        return {
            "tool": "pyslang",
            "available": True,
            "command": "pyslang",
            "returncode": 1,
            "errors": 1,
            "warnings": 0,
            "diagnostics": [{"severity": "error", "message": output}],
            "output": output,
            "passed": False,
        }

    compiled = compile_pyslang_files(paths)
    sm = compiled.source_manager
    diagnostics = []
    errors = 0
    warnings = 0
    for diag in compiled.diagnostics or []:
        is_error = diagnostic_is_error(diag)
        if is_error:
            errors += 1
        else:
            warnings += 1
        diagnostics.append({
            "severity": "error" if is_error else "warning",
            "file": _diagnostic_file(diag, sm),
            "line": diagnostic_line(diag, sm),
            "message": diagnostic_message(compiled.pyslang, diag, sm),
        })

    if compiled.error and not errors:
        errors += 1
        diagnostics.append({
            "severity": "error",
            "file": "",
            "line": 0,
            "message": compiled.error,
        })

    output_lines = [
        f"pyslang files: {len(paths)}",
        f"errors={errors} warnings={warnings}",
    ]
    if compiled.error:
        output_lines.append(compiled.error)
    output_lines.extend(
        f"{d.get('severity', '')}: {d.get('file', '')}:{d.get('line', 0)} {d.get('message', '')}"
        for d in diagnostics
    )
    return {
        "tool": "pyslang",
        "available": True,
        "command": "pyslang " + " ".join(str(p.relative_to(ip_dir)) for p in paths),
        "returncode": 1 if errors else 0,
        "errors": errors,
        "warnings": warnings,
        "diagnostics": diagnostics[:100],
        "output": "\n".join(output_lines).strip() + "\n",
        "passed": errors == 0 and warnings == 0,
    }


def _verilator_lint(ip_name: str, top: str, ip_dir: Path) -> dict:
    command = _verilator_command(ip_name, top)
    if not shutil.which("verilator"):
        output = "verilator not found; install Verilator to run canonical DUT lint"
        return {
            "tool": "verilator",
            "available": False,
            "command": " ".join(command),
            "returncode": 127,
            "errors": 1,
            "warnings": 0,
            "diagnostics": [{"severity": "error", "message": output}],
            "output": output + "\n",
            "passed": False,
        }
    proc = subprocess.run(command, cwd=ip_dir, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = proc.stdout or ""
    diag = _count_diagnostics(output)
    diagnostics = _parse_verilator_diagnostics(output)
    return {
        "tool": "verilator",
        "available": True,
        "command": " ".join(command),
        "returncode": proc.returncode,
        "errors": diag["errors"],
        "warnings": diag["warnings"],
        "diagnostics": diagnostics,
        "output": output,
        "passed": proc.returncode == 0 and diag["errors"] == 0 and diag["warnings"] == 0,
    }


def _log_output(tool_results: list[dict]) -> str:
    chunks = []
    for result in tool_results:
        chunks.append(
            f"===== {result['tool']} =====\n"
            f"command: {result['command']}\n"
            f"returncode: {result['returncode']}\n"
            f"errors: {result['errors']} warnings: {result['warnings']}\n"
            f"{result.get('output') or ''}"
        )
    return "\n".join(chunks).rstrip() + "\n"


def _report_tool_results(tool_results: list[dict]) -> list[dict]:
    return [
        {
            "tool": result["tool"],
            "available": result.get("available", True),
            "command": result["command"],
            "returncode": result["returncode"],
            "errors": result["errors"],
            "warnings": result["warnings"],
            "diagnostics": result.get("diagnostics", []),
            "passed": result["passed"],
        }
        for result in tool_results
    ]


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

    rtl_files = _filelist_entries(ip_dir, ip_name)
    lint_dir = ip_dir / "lint"
    lint_dir.mkdir(parents=True, exist_ok=True)
    tool_results = [
        _pyslang_lint(ip_dir, rtl_files),
        _verilator_lint(ip_name, top, ip_dir),
    ]
    output = _log_output(tool_results)
    errors = sum(int(result.get("errors") or 0) for result in tool_results)
    warnings = sum(int(result.get("warnings") or 0) for result in tool_results)
    tool_passed = all(bool(result.get("passed")) for result in tool_results)
    suppression_violations = _suppression_violations(ip_dir, rtl_files)
    style_violations = _style_violations(ip_dir, rtl_files)
    combined_returncode = 0 if tool_passed else 1
    report = {
        "schema_version": 1,
        "type": "dut_lint",
        "scope": "dut",
        "dut_only": True,
        "tool": "pyslang+verilator",
        "command": " && ".join(result["command"] for result in tool_results),
        "cwd": str(ip_dir.relative_to(project_root)),
        "top": top,
        "filelist": str(filelist.relative_to(project_root)),
        "rtl_files": rtl_files,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "returncode": combined_returncode,
        "errors": errors,
        "warnings": warnings,
        "waived_warnings": 0,
        "tool_results": _report_tool_results(tool_results),
        "suppression_violation_count": len(suppression_violations),
        "suppression_violations": suppression_violations,
        "style_violation_count": len(style_violations),
        "style_violations": style_violations,
        "policy": (
            "DUT RTL must be lint-clean without ad-hoc verilator lint_off/lint_on or -Wno suppressions, "
            "and generated RTL must keep .sv filenames while defaulting to the Verilog-2001 subset: "
            "no package/import/interface/modport/function/task/for/while and no logic/typedef/enum/always_ff/always_comb."
        ),
        "passed": (
            tool_passed
            and errors == 0
            and warnings == 0
            and not suppression_violations
            and not style_violations
        ),
    }
    (lint_dir / "dut_lint.log").write_text(output, encoding="utf-8")
    (lint_dir / "dut_lint.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"[dut_lint_report] wrote {lint_dir / 'dut_lint.json'}")
    print(
        f"[dut_lint_report] pyslang+verilator: errors={errors} warnings={warnings} "
        f"suppression_violations={len(suppression_violations)} "
        f"style_violations={len(style_violations)} returncode={combined_returncode}"
    )
    for result in tool_results:
        print(
            f"[dut_lint_report]   {result['tool']}: errors={result['errors']} "
            f"warnings={result['warnings']} returncode={result['returncode']}"
        )
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
