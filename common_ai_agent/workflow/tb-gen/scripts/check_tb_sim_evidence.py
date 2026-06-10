#!/usr/bin/env python3
"""check_tb_sim_evidence.py — tb-gen validator for PASS or precise escalation.

Python port of check_tb_sim_evidence.sh (ENFORCED in the sim + coverage stages).

A tb-gen simulation task is complete when:
  1. Real TB artifacts exist and have assertion paths.
  2. A real simulation result artifact exists.
  3. Either all tests pass, or failures are captured with [SIM ESCALATE]
     evidence so the next owner can be rtl-gen/sim_debug.

Preserved hardening:
  * results.xml / sim_report.txt presence is required.
  * tests > 0 is required for PASS (no parsed testcases ⇒ FAIL unless escalation).
  * failures require [SIM ESCALATE] evidence.
  * freshness: evidence must not be older than the newest TB file by > 0.5s.
  * stale failure text (FAIL / SIM ESCALATE) in the report when the latest XML
    reports zero failures is blocked.

Delegation:
  * check_tb_disk: prefer the sibling check_tb_disk.py if it exists, otherwise
    fall back to check_tb_disk.sh (bash).
  * check_scoreboard_events.py when verify/equivalence_goals.json exists.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent


def _locate_ip() -> str:
    ip = os.environ.get("IP_NAME") or (sys.argv[1] if len(sys.argv) > 1 else "")
    if not ip:
        candidates = []
        for path in Path(".").glob("*/*/*.ssot.yaml"):
            candidates.append(str(path))
        for path in Path(".").glob("*/*.ssot.yaml"):
            candidates.append(str(path))
        for path in Path(".").glob("*.ssot.yaml"):
            candidates.append(str(path))

        def _key(p: str) -> str:
            parts = p.split("/")
            return parts[1] if len(parts) > 1 else ""

        candidates = sorted(set(candidates), key=_key)
        if candidates:
            parts = candidates[0].split("/")
            if len(parts) >= 3:
                ip = parts[-3]
    return ip


def _run_check_tb_disk(ip: str) -> "subprocess.CompletedProcess[str]":
    """Delegate to check_tb_disk.py if present, else check_tb_disk.sh."""
    py = SCRIPT_DIR / "check_tb_disk.py"
    if py.is_file():
        cmd = [sys.executable, str(py), ip]
    else:
        cmd = ["bash", str(SCRIPT_DIR / "check_tb_disk.sh"), ip]
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


def _result_xml_paths(ip_dir: Path) -> "list[Path]":
    canonical = ip_dir / "sim" / "results.xml"
    candidates: "list[Path]" = []
    seen = set()
    for path in ip_dir.rglob("*results.xml"):
        try:
            resolved = path.resolve()
        except OSError:
            continue
        if resolved in seen:
            continue
        candidates.append(path)
        seen.add(resolved)
    if not candidates:
        return []
    canonical_resolved = canonical.resolve() if canonical.exists() else None
    noncanonical = [
        p
        for p in candidates
        if canonical_resolved is None or p.resolve() != canonical_resolved
    ]
    if not noncanonical:
        return sorted(
            candidates,
            key=lambda p: p.stat().st_mtime if p.exists() else 0,
            reverse=True,
        )[:1]
    newest = max(p.stat().st_mtime for p in noncanonical if p.exists())
    latest_by_dir: "dict[Path, Path]" = {}
    for path in noncanonical:
        parent = path.parent
        current = latest_by_dir.get(parent)
        if current is None or path.stat().st_mtime > current.stat().st_mtime:
            latest_by_dir[parent] = path
    selected = [
        p
        for p in latest_by_dir.values()
        if p.exists() and p.stat().st_mtime >= newest - 10.0
    ]
    if canonical.is_file() and canonical.stat().st_mtime >= newest - 2.0:
        selected.append(canonical)
    return sorted(
        selected, key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True
    )


def _line_has_failure(raw: str) -> bool:
    low = raw.strip().lower()
    if not low:
        return False
    if re.search(r"\b(assertionerror|traceback|fatal|aborted)\b", low):
        return True
    if "[fail]" in low:
        return True
    if re.search(r"\bfail\s*[=:]\s*[1-9][0-9]*\b", low):
        return True
    if re.search(r"\bfailures?\s*[=:]\s*[1-9][0-9]*\b", low):
        return True
    if re.search(r"[1-9][0-9]*\s+failed\b", low):
        return True
    if re.search(r"\b(failed|failure)\b", low):
        zero_failure = re.search(
            r"(\b0\s+failed\b|\bno\s+failures?\b|\bfail\s*[=:]\s*0\b|\bfailures?\s*[=:]\s*0\b)",
            low,
        )
        return zero_failure is None
    return False


def _analyze(ip_dir: Path, report_path: Path, cov_dir: Path) -> int:
    tests = failures = errors = 0
    xml_paths = _result_xml_paths(ip_dir)
    evidence_paths = [p for p in xml_paths if p.exists()]
    if report_path.is_file():
        evidence_paths.append(report_path)
    tb_paths = [
        p
        for root in (ip_dir / "tb", ip_dir / "sim")
        for p in (root.rglob("*") if root.is_dir() else [])
        if p.is_file() and p.suffix in {".py", ".sv", ".v", ".vh", ".f", ".mk"}
    ]
    if evidence_paths and tb_paths:
        newest_evidence = max(p.stat().st_mtime for p in evidence_paths)
        newest_tb = max(p.stat().st_mtime for p in tb_paths)
        if newest_evidence + 0.5 < newest_tb:
            newest_tb_path = max(tb_paths, key=lambda p: p.stat().st_mtime)
            newest_ev_path = max(evidence_paths, key=lambda p: p.stat().st_mtime)
            print("[check_tb_sim_evidence] FAIL: simulation evidence is older than generated TB")
            print(f"  newest TB      : {newest_tb_path}")
            print(f"  newest evidence: {newest_ev_path}")
            return 1
    for xml_path in xml_paths:
        try:
            root = ET.parse(xml_path).getroot()
        except Exception as exc:
            print(f"[check_tb_sim_evidence] FAIL: cannot parse {xml_path}: {exc}")
            return 1
        suites = [root, *root.findall(".//testsuite")]
        file_tests = file_failures = file_errors = 0
        for node in suites:
            file_tests += int(float(node.attrib.get("tests", 0) or 0))
            file_failures += int(float(node.attrib.get("failures", 0) or 0))
            file_errors += int(float(node.attrib.get("errors", 0) or 0))
        cases = root.findall(".//testcase")
        if file_tests == 0 and cases:
            file_tests = len(cases)
            file_failures = sum(1 for case in cases if case.find("failure") is not None)
            file_errors = sum(1 for case in cases if case.find("error") is not None)
        tests += file_tests
        failures += file_failures
        errors += file_errors

    report = (
        report_path.read_text(encoding="utf-8", errors="replace")
        if report_path.is_file()
        else ""
    )
    report_has_failure = any(_line_has_failure(line) for line in report.splitlines())
    cov_failed = 0
    escalations: "list[object]" = []
    for cov_path in (
        sorted(cov_dir.glob("coverage*.json")) if cov_dir.is_dir() else []
    ):
        try:
            cov = json.loads(cov_path.read_text(encoding="utf-8"))
        except Exception:
            cov = {}
        raw_failed = cov.get("failed") if isinstance(cov, dict) else None
        try:
            cov_failed += int(raw_failed)
        except Exception:
            cov_failed += 0
        raw_escalations = cov.get("escalations") if isinstance(cov, dict) else []
        if isinstance(raw_escalations, list):
            escalations.extend(raw_escalations)
    has_escalation = bool(escalations) or "[SIM ESCALATE]" in report
    hard_fail_eq = os.getenv("ATLAS_TB_HARD_FAIL_EQ", "1") == "1"

    scoreboard_failed = 0
    scoreboard_path = ip_dir / "sim" / "scoreboard_events.jsonl"
    if scoreboard_path.is_file():
        for raw in scoreboard_path.read_text(
            encoding="utf-8", errors="replace"
        ).splitlines():
            line = raw.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except Exception:
                scoreboard_failed += 1
                continue
            if isinstance(row, dict) and row.get("passed") is False:
                scoreboard_failed += 1

    scoreboard_fail_for_gate = scoreboard_failed if hard_fail_eq else 0
    total_fail = failures + errors + max(cov_failed, 0) + scoreboard_fail_for_gate
    if tests <= 0 and not has_escalation:
        print("[check_tb_sim_evidence] FAIL: no parsed testcases in fresh result XML; PASS requires at least one executed test")
        return 1

    if total_fail == 0:
        if report_has_failure or has_escalation:
            print("[check_tb_sim_evidence] FAIL: latest result XML has zero failures but sim_report/coverage still contains FAIL or SIM ESCALATE text")
            print("  Rewrite the final sim_report/coverage artifacts from the latest passing run; do not leave stale failure evidence in final artifacts.")
            return 1
        if scoreboard_failed > 0 and not hard_fail_eq:
            print(f"[check_tb_sim_evidence] PASS_SOFT_EQ: tests={tests} failures=0 errors=0 scoreboard_failed={scoreboard_failed} (ATLAS_TB_HARD_FAIL_EQ=0 override)")
            return 0
        print(f"[check_tb_sim_evidence] PASS: tests={tests} failures=0 errors=0")
        return 0

    if has_escalation:
        print(f"[check_tb_sim_evidence] PASS_OR_ESCALATE: tests={tests} failures={failures} errors={errors} cov_failed={cov_failed} scoreboard_failed={scoreboard_failed} escalations={len(escalations)}")
        return 0

    print(f"[check_tb_sim_evidence] FAIL: tests={tests} failures={failures} errors={errors} cov_failed={cov_failed} scoreboard_failed={scoreboard_failed}, but no SIM ESCALATE evidence")
    return 1


def main() -> int:
    ip = _locate_ip()
    if not ip or not Path(ip).is_dir():
        print("[check_tb_sim_evidence] FAIL: cannot locate IP directory")
        return 1

    disk = _run_check_tb_disk(ip)
    if disk.returncode != 0:
        sys.stdout.write(disk.stdout or "")
        return 1

    ip_path = Path(ip)
    if (ip_path / "verify" / "equivalence_goals.json").is_file():
        sb_proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPT_DIR / "check_scoreboard_events.py"),
                ip,
                "--root",
                ".",
                "--source-check",
                "--require-events",
                "--require-all-goals",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        if sb_proc.returncode != 0:
            sys.stdout.write(sb_proc.stdout or "")
            return 1
        sys.stdout.write(sb_proc.stdout or "")

    report = ip_path / "sim" / "sim_report.txt"
    cov_dir = ip_path / "cov"

    has_results_xml = any(
        p.is_file() for p in ip_path.rglob("*results.xml")
    )
    if not has_results_xml and not report.is_file():
        print("[check_tb_sim_evidence] FAIL: no *results.xml or sim_report.txt")
        return 1

    return _analyze(ip_path, report, cov_dir)


if __name__ == "__main__":
    raise SystemExit(main())
