#!/usr/bin/env python3
"""mutation_guard.py — deterministic RTL mutation testing for one IP.

Measures whether the EXISTING cocotb suite actually KILLS small, behaviour-
changing RTL mutations. A surviving (compiling) mutant means the suite's
observations are too loose near that site -- the silent-PASS / shallow-
observation class. This is the dynamic "can the harness fail?" oracle that a
goal-count audit cannot provide: 8 deep goals that kill mutants beat 29
vacuous goals that kill nothing.

Contract:
- Mutates ONLY LLM-editable RTL listed in <ip>/list/<ip>.f. The FunctionalModel
  (model/functional_model.py) is the golden oracle and is NEVER mutated.
- Deterministic: fixed operator catalog, fixed left-to-right occurrence order,
  no randomness. Same RTL -> same mutant set -> same verdict.
- Always restores the original RTL (try/finally), even on error.

Output: <ip>/verify/mutation_report.json  (+ stdout summary)
A mutant is KILLED if the suite run reports test failures/errors OR any
scoreboard_events.jsonl row has passed=false.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# Operator catalog: (name, regex over comment-stripped code, replacement).
# Each match site (left-to-right, line order) becomes exactly one mutant.
OPERATORS: list[tuple[str, "re.Pattern[str]", str]] = [
    ("EQ_TO_NE",        re.compile(r"(?<![=!<>])==(?!=)"), "!="),
    ("NE_TO_EQ",        re.compile(r"(?<![=!])!=(?!=)"),    "=="),
    ("PLUS1_TO_MINUS1", re.compile(r"\+\s*1'b1"),           "- 1'b1"),
    ("MINUS1_TO_PLUS1", re.compile(r"-\s*1'b1"),            "+ 1'b1"),
    ("CONST1_TO_0",     re.compile(r"1'b1"),                "1'b0"),
    ("CONST0_TO_1",     re.compile(r"1'b0"),                "1'b1"),
    ("AND_TO_OR",       re.compile(r"(?<![&])&(?![&])"),    "|"),
    ("BITINDEX_REVERSE", re.compile(r"\[bit_index\]"),      "[4'd9 - bit_index]"),
]


def _code_part(line: str) -> tuple[str, str]:
    """Split a Verilog line into (code, comment) at the first //."""
    idx = line.find("//")
    if idx < 0:
        return line, ""
    return line[:idx], line[idx:]


def _filelist_rtl(ip_dir: Path) -> list[Path]:
    flist = ip_dir / "list" / f"{ip_dir.name}.f"
    files: list[Path] = []
    if flist.is_file():
        for raw in flist.read_text(encoding="utf-8", errors="replace").splitlines():
            s = raw.strip()
            if not s or s.startswith(("+", "-", "#")):
                continue
            p = ip_dir / s
            if p.suffix in {".sv", ".v"} and p.is_file():
                files.append(p)
    if not files:  # fallback: rtl/*.sv minus *_param.vh
        files = sorted((ip_dir / "rtl").glob("*.sv"))
    return files


def _enumerate_mutants(text: str) -> list[dict]:
    """Deterministic list of single-site mutants for one file's text."""
    mutants: list[dict] = []
    lines = text.split("\n")
    for li, line in enumerate(lines):
        code, comment = _code_part(line)
        for op_name, rx, repl in OPERATORS:
            for m in rx.finditer(code):
                new_code = code[: m.start()] + repl + code[m.end():]
                new_line = new_code + comment
                mutated = lines[:li] + [new_line] + lines[li + 1:]
                mutants.append({
                    "operator": op_name,
                    "line": li + 1,
                    "col": m.start() + 1,
                    "before": line.strip(),
                    "after": new_line.strip(),
                    "_text": "\n".join(mutated),
                })
    return mutants


def _compiles(ip_dir: Path, rtl_files: list[Path], top: str) -> bool:
    rels = [str(p.relative_to(ip_dir)) for p in rtl_files]
    proc = subprocess.run(
        ["iverilog", "-g2012", "-t", "null", "-I", "rtl", "-s", top, *rels],
        cwd=ip_dir, capture_output=True, text=True,
    )
    return proc.returncode == 0


def _run_suite(ip_dir: Path, root: Path, timeout: int) -> tuple[bool, list[str], str]:
    """Run the IP's cocotb suite. Returns (killed, failing_goals, detail)."""
    runner = ip_dir / "tb" / "cocotb" / "test_runner.py"
    if not runner.is_file():
        return False, [], "no test_runner.py"
    env = dict(os.environ)
    env.setdefault("COMMON_AI_AGENT_ROOT", str(root))
    env.setdefault("ATLAS_PROJECT_ROOT", str(root))
    try:
        proc = subprocess.run(
            [sys.executable, str(runner)],
            cwd=root, capture_output=True, text=True, env=env, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return True, ["<timeout>"], "suite timed out (treated as killed)"

    # results.xml -> failures/errors
    results = ip_dir / "sim" / "results.xml"
    failures = errors = tests = 0
    if results.is_file():
        try:
            rootx = ET.parse(results).getroot()
            for node in [rootx, *rootx.findall(".//testsuite")]:
                tests += int(float(node.attrib.get("tests", 0) or 0))
                failures += int(float(node.attrib.get("failures", 0) or 0))
                errors += int(float(node.attrib.get("errors", 0) or 0))
            if tests == 0:
                cases = rootx.findall(".//testcase")
                tests = len(cases)
                failures = sum(1 for c in cases if c.find("failure") is not None)
                errors = sum(1 for c in cases if c.find("error") is not None)
        except Exception:
            pass

    # scoreboard rows with passed=false -> which goals caught it
    failing_goals: list[str] = []
    sb = ip_dir / "sim" / "scoreboard_events.jsonl"
    if sb.is_file():
        for raw in sb.read_text(encoding="utf-8", errors="replace").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            try:
                row = json.loads(raw)
            except Exception:
                continue
            if isinstance(row, dict) and row.get("passed") is False:
                gid = str(row.get("goal_id") or "?")
                if gid not in failing_goals:
                    failing_goals.append(gid)

    suite_failed = (proc.returncode != 0) or (failures + errors > 0) or bool(failing_goals)
    detail = f"rc={proc.returncode} tests={tests} fail={failures} err={errors} sb_fail={len(failing_goals)}"
    return suite_failed, failing_goals, detail


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("ip")
    ap.add_argument("--root", default=os.environ.get("ATLAS_PROJECT_ROOT") or ".")
    ap.add_argument("--top", default="")
    ap.add_argument("--max", type=int, default=120, help="cap on mutants")
    ap.add_argument("--timeout", type=int, default=120, help="per-suite-run seconds")
    ap.add_argument("--min-kill-rate", type=float, default=1.0,
                    help="gate: fail (exit 1) if kill-rate below this")
    ns = ap.parse_args()

    root = Path(ns.root).resolve()
    ip_dir = root / ns.ip
    top = ns.top or ns.ip
    rtl_files = _filelist_rtl(ip_dir)
    if not rtl_files:
        print(f"[mutation_guard] FAIL: no RTL files for {ns.ip}")
        return 1

    # Baseline: the unmutated suite must be GREEN, else kill-rate is meaningless.
    base_killed, _, base_detail = _run_suite(ip_dir, root, ns.timeout)
    if base_killed:
        print(f"[mutation_guard] FAIL: baseline suite is not green ({base_detail}); "
              f"fix the suite/RTL before mutation testing.")
        return 1
    print(f"[mutation_guard] baseline green: {base_detail}")

    results: list[dict] = []
    killed = survived = uncompilable = 0
    originals = {p: p.read_text(encoding="utf-8") for p in rtl_files}
    try:
        seq = 0
        for rtl in rtl_files:
            text = originals[rtl]
            for mut in _enumerate_mutants(text):
                if seq >= ns.max:
                    break
                seq += 1
                rtl.write_text(mut["_text"], encoding="utf-8")
                rec = {
                    "id": f"M{seq:03d}",
                    "file": str(rtl.relative_to(ip_dir)),
                    "operator": mut["operator"],
                    "line": mut["line"],
                    "before": mut["before"],
                    "after": mut["after"],
                }
                if not _compiles(ip_dir, rtl_files, top):
                    rec["status"] = "uncompilable"
                    uncompilable += 1
                else:
                    kld, goals, detail = _run_suite(ip_dir, root, ns.timeout)
                    rec["status"] = "killed" if kld else "SURVIVED"
                    rec["killed_by_goals"] = goals
                    rec["detail"] = detail
                    if kld:
                        killed += 1
                    else:
                        survived += 1
                results.append(rec)
                # restore immediately so the next compile/sim starts clean
                rtl.write_text(originals[rtl], encoding="utf-8")
            if seq >= ns.max:
                break
    finally:
        for p, txt in originals.items():
            p.write_text(txt, encoding="utf-8")

    behavioural = killed + survived
    kill_rate = (killed / behavioural) if behavioural else 0.0
    survivors = [r for r in results if r["status"] == "SURVIVED"]
    report = {
        "schema_version": 1,
        "type": "mutation_guard_report",
        "ip": ns.ip,
        "top": top,
        "rtl_files": [str(p.relative_to(ip_dir)) for p in rtl_files],
        "summary": {
            "total_mutants": len(results),
            "uncompilable": uncompilable,
            "behavioural": behavioural,
            "killed": killed,
            "survived": survived,
            "kill_rate": round(kill_rate, 4),
        },
        "survivors": [
            {k: r[k] for k in ("id", "file", "operator", "line", "before", "after")}
            for r in survivors
        ],
        "mutants": results,
    }
    out = ip_dir / "verify" / "mutation_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(f"[mutation_guard] mutants={len(results)} uncompilable={uncompilable} "
          f"behavioural={behavioural} killed={killed} survived={survived} "
          f"kill_rate={kill_rate:.1%}")
    for r in survivors:
        print(f"  SURVIVED {r['id']} {r['file']}:{r['line']} [{r['operator']}]  {r['before']}")
    print(f"[mutation_guard] wrote {out.relative_to(root)}")

    gate_ok = kill_rate >= ns.min_kill_rate
    print(f"[mutation_guard] gate {'PASS' if gate_ok else 'FAIL'} "
          f"(kill_rate {kill_rate:.1%} {'>=' if gate_ok else '<'} {ns.min_kill_rate:.0%})")
    return 0 if gate_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
