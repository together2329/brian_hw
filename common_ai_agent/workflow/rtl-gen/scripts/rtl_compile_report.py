#!/usr/bin/env python3
"""Run a canonical DUT RTL compile check and write machine-readable evidence."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import time
from pathlib import Path


def _read_filelist(ip_dir: Path, filelist: Path) -> list[str]:
    rtl_files: list[str] = []
    for raw in filelist.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or line.startswith(("+incdir+", "-I")):
            continue
        rel = line
        if rel.startswith(str(ip_dir.name) + "/"):
            rel = rel[len(ip_dir.name) + 1 :]
        if rel.endswith((".v", ".sv")):
            rtl_files.append(rel)
    return rtl_files


def _count_diagnostics(text: str) -> tuple[int, int]:
    errors = 0
    diagnostics = 0
    for line in text.splitlines():
        if re.search(r"\b(error|fatal):", line, re.I):
            errors += 1
        elif re.search(r"\b(warning|sorry):", line, re.I):
            diagnostics += 1
    return errors, diagnostics


def _strip_line_comment(line: str) -> str:
    return line.split("//", 1)[0]


def _policy_source_files(ip_dir: Path, rtl_files: list[str]) -> list[tuple[str, Path]]:
    pairs: list[tuple[str, Path]] = []
    seen: set[Path] = set()
    for rel in rtl_files:
        path = ip_dir / rel
        if path.is_file():
            resolved = path.resolve()
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


def _scan_style_violations(ip_dir: Path, rtl_files: list[str]) -> list[dict[str, object]]:
    violations: list[dict[str, object]] = []
    block_start_re = re.compile(r"\balways_(?:comb|ff|latch)\b|\balways\s*@")
    part_select_re = re.compile(r"\[[^\]]*(?:\$clog2|[A-Z][A-Z0-9_]*\s*[-+*/])[^\]]*:[^\]]*\]")
    banned_patterns = _banned_syntax_patterns()
    for rel, path in _policy_source_files(ip_dir, rtl_files):
        in_always = False
        depth = 0
        for lineno, raw in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            line = _strip_line_comment(raw)
            for rule, pattern, message in banned_patterns:
                if pattern.search(line):
                    violations.append({
                        "file": rel,
                        "line": lineno,
                        "rule": rule,
                        "message": message,
                        "text": raw.strip(),
                    })
            if not in_always and block_start_re.search(line):
                in_always = True
                depth = line.count("begin") - line.count("end")
            elif in_always:
                depth += line.count("begin") - line.count("end")
            if in_always and part_select_re.search(line):
                violations.append({
                    "file": rel,
                    "line": lineno,
                    "rule": "no_parameterized_part_select_in_procedural_block",
                    "message": "Move parameterized/constant part-selects out of always_* into continuous assign/helper wires.",
                    "text": raw.strip(),
                })
            if in_always and depth <= 0 and re.search(r"\bend\b", line):
                in_always = False
    return violations


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("ip", help="IP directory under the project root")
    ap.add_argument("--top", default="", help="Top module name; defaults to IP name")
    ap.add_argument("--filelist", default="", help="Filelist path relative to IP dir")
    ap.add_argument("--project-root", default=".", help="Project root")
    ns = ap.parse_args()

    project_root = Path(ns.project_root).resolve()
    ip_dir = (project_root / ns.ip).resolve()
    top = ns.top or ip_dir.name
    filelist = ip_dir / (ns.filelist or f"list/{ip_dir.name}.f")
    out_dir = ip_dir / "rtl"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_json = out_dir / "rtl_compile.json"
    out_log = out_dir / "rtl_compile.log"

    if not filelist.is_file():
        raise SystemExit(f"missing filelist: {filelist}")
    if not shutil.which("iverilog"):
        raise SystemExit("missing compile tool: iverilog")

    rtl_files = _read_filelist(ip_dir, filelist)
    output = Path("/tmp") / f"{ip_dir.name}_rtl_check.vvp"
    command = [
        "iverilog",
        "-g2012",
        "-Irtl",
        "-f",
        str(filelist.relative_to(ip_dir)),
        "-s",
        top,
        "-o",
        str(output),
    ]
    proc = subprocess.run(command, cwd=ip_dir, text=True, capture_output=True)
    text = (proc.stdout or "") + (proc.stderr or "")
    errors, diagnostics = _count_diagnostics(text)
    style_violations = _scan_style_violations(ip_dir, rtl_files)
    passed = proc.returncode == 0 and errors == 0 and diagnostics == 0 and not style_violations
    report = {
        "schema_version": 1,
        "type": "rtl_compile",
        "scope": "dut",
        "dut_only": True,
        "tool": "iverilog",
        "command": " ".join(command),
        "cwd": str(ip_dir),
        "top": top,
        "filelist": str(filelist.relative_to(ip_dir)),
        "rtl_files": rtl_files,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "returncode": proc.returncode,
        "errors": errors,
        "diagnostics": diagnostics,
        "style_violations": len(style_violations),
        "style_violation_details": style_violations,
        "passed": passed,
        "policy": (
            "returncode==0, no error/fatal/warning/sorry diagnostics, no procedural parameterized part-select style violations, "
            "and no generated-RTL policy violations: .sv filenames with Verilog-2001 default syntax, rtl/<ip>_param.vh for shared parameters, "
            "no package/import/interface/modport/function/task/for/while, and no logic/typedef/enum/always_ff/always_comb"
        ),
    }
    out_log.write_text(text, encoding="utf-8")
    out_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"[rtl_compile_report] wrote {out_json}")
    print(
        f"[rtl_compile_report] iverilog: errors={errors} "
        f"diagnostics={diagnostics} style_violations={len(style_violations)} "
        f"returncode={proc.returncode}"
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
