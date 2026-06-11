#!/usr/bin/env python3
"""Audit ROCEV evidence coverage for local hardware IP directories."""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[2]


def load_json(path: Path) -> Any | None:
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None


def truthy_pass(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"pass", "passed", "ok", "closed", "proven", "success"}:
            return True
        if lowered in {"fail", "failed", "blocked", "error", "open", "not_closed"}:
            return False
    return None


def json_status(path: Path) -> str:
    data = load_json(path)
    if data is None:
        return "unreadable"
    if isinstance(data, dict):
        for key in ("passed", "pass", "success", "ok"):
            if key in data:
                result = truthy_pass(data[key])
                if result is not None:
                    return "pass" if result else "fail"
        for key in ("status", "result", "verdict"):
            if key in data:
                result = truthy_pass(data[key])
                if result is not None:
                    return "pass" if result else "fail"
                return str(data[key]).lower()
    return "present"


def xml_status(path: Path) -> str:
    try:
        root = ET.parse(path).getroot()
    except Exception:
        return "unreadable"
    failures = int(root.attrib.get("failures", "0") or 0)
    errors = int(root.attrib.get("errors", "0") or 0)
    tests = int(root.attrib.get("tests", "0") or 0)
    if tests == 0:
        testcases = list(root.iter("testcase"))
        tests = len(testcases)
    if failures or errors:
        return "fail"
    if tests > 0:
        return "pass"
    return "present"


def count_jsonl(path: Path, limit: int = 10000) -> dict[str, Any]:
    total = 0
    passed = 0
    failed = 0
    coverage_refs = 0
    unreadable = 0
    try:
        handle = path.open("r", encoding="utf-8", errors="replace")
    except OSError:
        return {"total": 0, "passed": 0, "failed": 0, "coverage_refs": 0, "unreadable": 0}
    with handle:
        for line in handle:
            if not line.strip():
                continue
            total += 1
            if total > limit:
                break
            try:
                row = json.loads(line)
            except Exception:
                unreadable += 1
                continue
            if isinstance(row, dict):
                if row.get("coverage_refs"):
                    coverage_refs += 1
                result = truthy_pass(row.get("passed"))
                if result is True:
                    passed += 1
                elif result is False:
                    failed += 1
                else:
                    status = truthy_pass(row.get("status") or row.get("result"))
                    if status is True:
                        passed += 1
                    elif status is False:
                        failed += 1
    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "coverage_refs": coverage_refs,
        "unreadable": unreadable,
    }


def obligation_count(path: Path) -> int | None:
    data = load_json(path)
    if data is None:
        return None
    if isinstance(data, list):
        return len(data)
    if isinstance(data, dict):
        for key in ("obligations", "items", "requirements"):
            value = data.get(key)
            if isinstance(value, list):
                return len(value)
        return len(data)
    return None


def coverage_status(path: Path) -> str:
    data = load_json(path)
    if data is None:
        return "unreadable"
    text = json.dumps(data).lower()
    if '"status": "blocked"' in text or '"status":"blocked"' in text:
        return "blocked"
    if '"meets_target": false' in text or '"meets_target":false' in text:
        return "gap"
    status = json_status(path)
    if status in {"pass", "closed", "ok"}:
        return "pass"
    return status


def first_existing(ip: Path, rels: list[str]) -> Path | None:
    for rel in rels:
        path = ip / rel
        if path.exists():
            return path
    return None


def has_any(ip: Path, patterns: list[str]) -> list[str]:
    found: list[str] = []
    for pattern in patterns:
        found.extend(str(path.relative_to(ip)) for path in ip.glob(pattern) if path.is_file())
    return sorted(found)


def audit_ip(ip: Path) -> dict[str, Any]:
    req_files = has_any(ip, ["req/*requirements.md", "req/locked_truth.md"])
    obligations_path = ip / "req/obligations.json"
    evidence_plan = first_existing(ip, ["req/evidence_plan.json", "verify/evidence_contract.json"])
    eq_goals = ip / "verify/equivalence_goals.json"
    rtl_compile = ip / "rtl/rtl_compile.json"
    lint = ip / "lint/dut_lint.json"
    results = ip / "sim/results.xml"
    scoreboard = first_existing(
        ip,
        [
            "sim/scoreboard_events.jsonl",
            "verify/scoreboard_events.jsonl",
            "verify/module_equivalence_scoreboard.jsonl",
        ],
    )
    coverage = first_existing(ip, ["cov/coverage.json", "cov/coverage_functional.json"])
    formal_status = ip / "verify/formal_status.json"
    sva_files = has_any(ip, ["verify/*.sva"])
    signoff = first_existing(ip, ["signoff/truth_coverage.json", "signoff/ip_signoff.json"])
    waves = has_any(ip, ["sim/*.vcd", "sim/*.fst"])

    scoreboard_summary = count_jsonl(scoreboard) if scoreboard else None
    evidence = {
        "requirement": {"present": bool(req_files), "paths": req_files[:5]},
        "obligation": {
            "present": obligations_path.exists(),
            "path": str(obligations_path.relative_to(ip)) if obligations_path.exists() else None,
            "count": obligation_count(obligations_path) if obligations_path.exists() else None,
        },
        "contract": {
            "present": bool(evidence_plan or eq_goals.exists()),
            "paths": [
                str(path.relative_to(ip))
                for path in [evidence_plan, eq_goals if eq_goals.exists() else None]
                if path is not None
            ],
        },
        "rtl_compile": {
            "present": rtl_compile.exists(),
            "status": json_status(rtl_compile) if rtl_compile.exists() else "missing",
        },
        "lint": {
            "present": lint.exists(),
            "status": json_status(lint) if lint.exists() else "missing",
        },
        "simulation": {
            "present": results.exists(),
            "status": xml_status(results) if results.exists() else "missing",
        },
        "scoreboard": {
            "present": scoreboard is not None,
            "path": str(scoreboard.relative_to(ip)) if scoreboard else None,
            "summary": scoreboard_summary,
        },
        "coverage": {
            "present": coverage is not None,
            "path": str(coverage.relative_to(ip)) if coverage else None,
            "status": coverage_status(coverage) if coverage else "missing",
        },
        "waveform": {"present": bool(waves), "paths": waves[:5]},
        "formal": {
            "present": formal_status.exists() or bool(sva_files),
            "status": json_status(formal_status) if formal_status.exists() else "not_run",
            "sva": sva_files[:5],
        },
        "signoff": {
            "present": signoff is not None,
            "path": str(signoff.relative_to(ip)) if signoff else None,
            "status": json_status(signoff) if signoff else "missing",
        },
    }

    gaps = []
    if not evidence["requirement"]["present"]:
        gaps.append("missing requirement file")
    if not evidence["obligation"]["present"]:
        gaps.append("missing obligations.json")
    if not evidence["contract"]["present"]:
        gaps.append("missing evidence plan or equivalence goals")
    for key in ("rtl_compile", "lint", "simulation"):
        if evidence[key]["status"] not in {"pass", "present"}:
            gaps.append(f"{key} is {evidence[key]['status']}")
    if not evidence["scoreboard"]["present"]:
        gaps.append("missing scoreboard rows")
    elif scoreboard_summary and scoreboard_summary["failed"]:
        gaps.append("scoreboard has failed rows")
    if evidence["coverage"]["status"] in {"missing", "blocked", "gap", "fail"}:
        gaps.append(f"coverage is {evidence['coverage']['status']}")

    scoreboard_ok = evidence["scoreboard"]["present"] and not (
        scoreboard_summary and scoreboard_summary["failed"]
    )
    essentials = [
        evidence["requirement"]["present"],
        evidence["obligation"]["present"],
        evidence["contract"]["present"],
        evidence["rtl_compile"]["status"] == "pass",
        evidence["lint"]["status"] == "pass",
        evidence["simulation"]["status"] == "pass",
        scoreboard_ok,
        evidence["coverage"]["status"] == "pass",
    ]
    if all(essentials) and not gaps:
        validation = "closed"
    elif any(essentials):
        validation = "partial"
    else:
        validation = "open"

    return {
        "ip": ip.name,
        "path": str(ip.relative_to(REPO)),
        "validation": validation,
        "gaps": gaps,
        "evidence": evidence,
    }


def discover_ips(limit: int | None) -> list[Path]:
    candidates: list[tuple[int, str, Path]] = []
    ignored = {".git", ".cursor", ".cursor_new", ".codex_ref", ".agents", "doc", "tests", "workflow"}
    for child in REPO.iterdir():
        if not child.is_dir() or child.name in ignored or child.name.startswith("."):
            continue
        evidence_files = 0
        for rel in (
            "req",
            "rtl",
            "lint",
            "sim",
            "cov",
            "verify",
            "signoff",
        ):
            if (child / rel).exists():
                evidence_files += 1
        if evidence_files >= 2:
            candidates.append((evidence_files, child.name, child))
    candidates.sort(key=lambda item: (-item[0], item[1]))
    paths = [path for _score, _name, path in candidates]
    return paths[:limit] if limit else paths


def render_markdown(results: list[dict[str, Any]]) -> str:
    lines = [
        "# ROCEV IP Audit",
        "",
        "| IP | Validation | Key evidence | Gaps |",
        "|---|---|---|---|",
    ]
    for result in results:
        evidence = result["evidence"]
        key_bits = []
        for key in ("rtl_compile", "lint", "simulation", "coverage", "signoff"):
            item = evidence[key]
            if item["present"]:
                key_bits.append(f"{key}:{item['status']}")
        if evidence["scoreboard"]["present"]:
            summary = evidence["scoreboard"]["summary"] or {}
            key_bits.append(f"scoreboard:{summary.get('total', 0)} rows")
        if evidence["waveform"]["present"]:
            key_bits.append("waveform")
        if evidence["formal"]["present"]:
            key_bits.append(f"formal:{evidence['formal']['status']}")
        gaps = "; ".join(result["gaps"][:3]) if result["gaps"] else "-"
        lines.append(
            f"| `{result['ip']}` | {result['validation']} | "
            f"{', '.join(key_bits) or '-'} | {gaps} |"
        )
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ips", nargs="*", help="IP directories to audit")
    parser.add_argument("--limit", type=int, default=None, help="Limit discovered IP count")
    parser.add_argument("--markdown", action="store_true", help="Print markdown instead of JSON")
    parser.add_argument("--output", type=Path, help="Write output to this path")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    if args.ips:
        ips = [(REPO / ip) for ip in args.ips]
    else:
        ips = discover_ips(args.limit)

    missing = [str(ip) for ip in ips if not ip.exists()]
    if missing:
        print(f"missing IP directories: {', '.join(missing)}", file=sys.stderr)
        return 2

    results = [audit_ip(ip) for ip in ips]
    if args.markdown:
        rendered = render_markdown(results)
    else:
        rendered = json.dumps({"count": len(results), "results": results}, indent=2)
        rendered += "\n"

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
