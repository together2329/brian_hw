#!/usr/bin/env python3
"""Audit one IP against the generic FL-vs-RTL equivalence goal.

This is intentionally disk-driven and IP-agnostic.  It does not generate RTL,
tests, or waivers.  It verifies that the existing artifacts prove the SSOT ->
FL model -> equivalence goals -> scoreboard -> sim -> compare -> coverage
loop with machine-readable evidence.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


PLACEHOLDER_MARKERS = ("TBD", "TODO", "FIXME", "PLACEHOLDER", "stub", "mock")
REAL_RTL_TOOLS = ("verilator", "pyslang", "slang", "iverilog")


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _read_json(path: Path) -> tuple[dict[str, Any], str]:
    if not path.is_file():
        return {}, f"missing {_rel(path, path.parent.parent if path.parent.parent.exists() else path.parent)}"
    try:
        doc = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception as exc:
        return {}, f"cannot parse {_rel(path, path.parent.parent if path.parent.parent.exists() else path.parent)}: {exc}"
    if not isinstance(doc, dict):
        return {}, f"{path.name} root must be a JSON object"
    return doc, ""


def _load_yaml(path: Path) -> tuple[dict[str, Any], str]:
    if not path.is_file():
        return {}, f"missing {path}"
    try:
        import yaml  # type: ignore
    except Exception as exc:
        return {}, f"PyYAML unavailable for SSOT parse: {exc}"
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8", errors="replace")) or {}
    except Exception as exc:
        return {}, f"cannot parse {path}: {exc}"
    if not isinstance(doc, dict):
        return {}, "SSOT root must be a mapping"
    return doc, ""


def _text_has_placeholder(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return True
    for raw_line in text.splitlines():
        line = raw_line.strip().lower()
        if not line:
            continue
        if re.search(r"<\s*(tbd|placeholder)\s*>", line):
            return True
        if re.search(r"(^|[\s:#\"'\-])(?:todo|fixme|tbd|placeholder)\s*(?:[:=\]\)]|$)", line):
            return True
        if re.search(r"\b(stub|mock)\b", line):
            if re.search(r"\b(no|non|not|without|avoid|forbid|forbidden|prevents?|must not)\b.{0,48}\b(stub|mock)\b", line):
                continue
            if re.search(r"\b(stub|mock)\b.{0,32}\b(module|function|class|file|rtl|model|implementation|logic|shell|return)\b", line):
                return True
    return False


def _check(
    checks: list[dict[str, Any]],
    check_id: str,
    ok: bool,
    *,
    label: str,
    evidence: str | list[str] = "",
    owner: str = "LLM loop",
    detail: str = "",
    next_action: str = "",
) -> None:
    checks.append({
        "id": check_id,
        "label": label,
        "status": "pass" if ok else "fail",
        "owner": owner,
        "evidence": evidence,
        "detail": detail,
        "next_action": next_action,
    })


def _parse_results(path: Path) -> dict[str, Any]:
    result = {"exists": path.is_file(), "tests": 0, "failures": 0, "errors": 0, "parse_error": ""}
    if not path.is_file():
        return result
    try:
        root = ET.fromstring(path.read_text(encoding="utf-8", errors="replace"))
    except Exception as exc:
        result.update({"parse_error": str(exc), "errors": 1})
        return result
    for elem in root.iter():
        if elem.tag.endswith("testsuite"):
            result["tests"] += int(float(elem.attrib.get("tests", "0") or 0))
            result["failures"] += int(float(elem.attrib.get("failures", "0") or 0))
            result["errors"] += int(float(elem.attrib.get("errors", "0") or 0))
    if result["tests"] == 0:
        cases = [elem for elem in root.iter() if elem.tag.endswith("testcase")]
        result["tests"] = len(cases)
        for case in cases:
            result["failures"] += len([child for child in list(case) if child.tag.endswith("failure")])
            result["errors"] += len([child for child in list(case) if child.tag.endswith("error")])
    return result


def _coverage_bins(coverage: dict[str, Any]) -> dict[str, bool]:
    top_bins = coverage.get("functional_bins") if isinstance(coverage.get("functional_bins"), dict) else {}
    functional = coverage.get("functional") if isinstance(coverage.get("functional"), dict) else {}
    bins = dict(top_bins)
    nested = functional.get("bins") if isinstance(functional.get("bins"), dict) else {}
    bins.update(nested)
    out: dict[str, bool] = {}
    for key, value in bins.items():
        if isinstance(value, bool):
            out[str(key)] = value
        elif isinstance(value, dict):
            out[str(key)] = bool(value.get("hit") or value.get("passed") or value.get("covered"))
        elif isinstance(value, (int, float)):
            out[str(key)] = value > 0
    return out


def _goals(goals_doc: dict[str, Any]) -> list[dict[str, Any]]:
    goals = goals_doc.get("goals")
    return [goal for goal in goals if isinstance(goal, dict)] if isinstance(goals, list) else []


def _goal_schema_errors(goal: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = [
        "goal_id",
        "title",
        "kind",
        "ssot_refs",
        "stimulus_contract",
        "expected_contract",
        "pass_criteria",
        "owner_on_fail",
        "blocked",
    ]
    for key in required:
        if key not in goal:
            errors.append(f"{goal.get('goal_id') or '<missing goal_id>'}: missing {key}")
    if not str(goal.get("goal_id") or "").strip():
        errors.append("goal missing stable goal_id")
    if not goal.get("ssot_refs"):
        errors.append(f"{goal.get('goal_id')}: missing SSOT trace refs")
    owner = goal.get("owner_on_fail") if isinstance(goal.get("owner_on_fail"), dict) else {}
    default_owner = str(owner.get("default") or "").strip()
    possible_owners = [str(item) for item in owner.get("possible") or [] if str(item).strip()]
    if not default_owner:
        errors.append(f"{goal.get('goal_id')}: owner_on_fail.default is required")
    elif possible_owners and default_owner not in possible_owners:
        errors.append(f"{goal.get('goal_id')}: default owner_on_fail must be listed in possible owners")
    elif str(goal.get("kind") or "").lower() != "coverage" and default_owner != "rtl":
        errors.append(f"{goal.get('goal_id')}: non-coverage default owner_on_fail must be rtl")
    return errors


def _report_passed(report: dict[str, Any]) -> bool:
    if report.get("passed") is True:
        return True
    status = str(report.get("status") or "").lower()
    return status in {"pass", "passed", "ok"} and int(report.get("errors") or 0) == 0


def _report_dut_only(report: dict[str, Any]) -> bool:
    scope = str(report.get("scope") or report.get("type") or "").lower()
    return report.get("dut_only") is True or scope in {"dut", "rtl", "dut_lint", "rtl_lint", "rtl_compile"}


def _report_uses_real_tool(report: dict[str, Any]) -> bool:
    text = " ".join(str(report.get(key) or "") for key in ("tool", "command", "cmd")).lower()
    return any(tool in text for tool in REAL_RTL_TOOLS)


def _is_stale(source_paths: list[Path], evidence_paths: list[Path], root: Path) -> list[str]:
    sources = [path for path in source_paths if path.is_file()]
    evidence = [path for path in evidence_paths if path.is_file()]
    if not sources or not evidence:
        return []
    newest_source = max(sources, key=lambda path: path.stat().st_mtime)
    newest_source_mtime = newest_source.stat().st_mtime
    stale: list[str] = []
    for path in evidence:
        if path.stat().st_mtime + 0.5 < newest_source_mtime:
            stale.append(f"{_rel(path, root)} older than {_rel(newest_source, root)}")
    return stale


def audit(ip: str, root: Path) -> dict[str, Any]:
    root = root.resolve()
    ip_dir = root / ip
    ssot_path = ip_dir / "yaml" / f"{ip}.ssot.yaml"
    model_path = ip_dir / "model" / "functional_model.py"
    fl_check_path = ip_dir / "model" / "fl_model_check.json"
    decomp_path = ip_dir / "model" / "decomposition.json"
    fcov_plan_path = ip_dir / "cov" / "fcov_plan.json"
    goals_path = ip_dir / "verify" / "equivalence_goals.json"
    score_path = ip_dir / "sim" / "scoreboard_events.jsonl"
    compare_path = ip_dir / "sim" / "fl_rtl_compare.json"
    classify_path = ip_dir / "sim" / "mismatch_classification.json"
    coverage_path = ip_dir / "cov" / "coverage.json"
    results_candidates = [ip_dir / "sim" / "results.xml", ip_dir / "tb" / "cocotb" / "results.xml"]
    results_path = next((path for path in results_candidates if path.is_file()), results_candidates[0])
    compile_path = ip_dir / "rtl" / "rtl_compile.json"
    lint_candidates = [ip_dir / "lint" / "dut_lint.json", ip_dir / "lint" / "rtl_lint.json"]
    lint_path = next((path for path in lint_candidates if path.is_file()), lint_candidates[0])

    checks: list[dict[str, Any]] = []

    req_paths = sorted((ip_dir / "req").glob("*.md")) if (ip_dir / "req").is_dir() else []
    req_bytes = sum(path.stat().st_size for path in req_paths if path.is_file())
    req_ok = bool(req_paths) and req_bytes >= 1000 and all(not _text_has_placeholder(path) for path in req_paths)
    _check(
        checks,
        "req",
        req_ok,
        label="Human-approved requirement artifact exists",
        evidence=[_rel(path, root) for path in req_paths],
        owner="human gate",
        detail=(
            "requirement markdown must exist under req/, contain at least 1000 bytes "
            f"of substantive text, and contain no TODO/TBD markers; bytes={req_bytes}"
        ),
        next_action=f"capture requirement intent in {ip}/req/*.md before SSOT signoff",
    )

    ssot_doc, ssot_error = _load_yaml(ssot_path)
    ssot_ok = (
        not ssot_error
        and isinstance(ssot_doc.get("function_model"), dict)
        and isinstance(ssot_doc.get("cycle_model"), dict)
        and bool(ssot_doc.get("top_module"))
        and not _text_has_placeholder(ssot_path)
    )
    _check(
        checks,
        "ssot",
        ssot_ok,
        label="SSOT contains function_model and cycle_model source of truth",
        evidence=_rel(ssot_path, root),
        owner="ssot-gen",
        detail=ssot_error or "SSOT parsed with function_model and cycle_model",
        next_action="repair SSOT from requirement answers; do not infer product behavior in RTL",
    )

    fl_check, fl_check_error = _read_json(fl_check_path)
    fl_ok = model_path.is_file() and not _text_has_placeholder(model_path) and fl_check.get("passed") is True
    _check(
        checks,
        "fl_model",
        fl_ok,
        label="Executable functional model passes self-check",
        evidence=[_rel(model_path, root), _rel(fl_check_path, root)],
        owner="fl-model-gen",
        detail=fl_check_error or f"fl_model_check.passed={fl_check.get('passed')}",
        next_action=f"rerun /ssot-equiv-goals {ip} after repairing FunctionalModel from SSOT",
    )

    decomp, decomp_error = _read_json(decomp_path)
    units = decomp.get("units") if isinstance(decomp.get("units"), list) else []
    decomp_ok = decomp.get("complete") is True and len(units) > 0
    _check(
        checks,
        "fl_decomposition",
        decomp_ok,
        label="Functional model decomposition is complete",
        evidence=_rel(decomp_path, root),
        owner="fl-model-gen",
        detail=decomp_error or f"complete={decomp.get('complete')} units={len(units)}",
        next_action="split FunctionalModel behavior into units before coverage/equivalence planning",
    )

    fcov, fcov_error = _read_json(fcov_plan_path)
    plan_bins = fcov.get("bins") if isinstance(fcov.get("bins"), list) else []
    fcov_ok = fcov.get("planned_before_rtl") is True and len(plan_bins) > 0
    _check(
        checks,
        "fcov_plan",
        fcov_ok,
        label="Functional coverage plan exists before RTL signoff",
        evidence=_rel(fcov_plan_path, root),
        owner="fl-model-gen",
        detail=fcov_error or f"planned_before_rtl={fcov.get('planned_before_rtl')} bins={len(plan_bins)}",
        next_action="derive functional coverage bins from SSOT/decomposition before RTL/TB signoff",
    )

    goals_doc, goals_error = _read_json(goals_path)
    goals = _goals(goals_doc)
    goal_errors: list[str] = []
    seen_goal_ids: set[str] = set()
    for goal in goals:
        goal_errors.extend(_goal_schema_errors(goal))
        gid = str(goal.get("goal_id") or "").strip()
        if gid in seen_goal_ids:
            goal_errors.append(f"duplicate goal_id {gid}")
        seen_goal_ids.add(gid)
    blocked_goals = [goal for goal in goals if goal.get("blocked") is True]
    goals_ok = len(goals) > 0 and not blocked_goals and not goal_errors
    _check(
        checks,
        "equivalence_goals",
        goals_ok,
        label="SSOT-traceable equivalence goals are generated",
        evidence=_rel(goals_path, root),
        owner="fl-model-gen",
        detail=goals_error or f"total={len(goals)} blocked={len(blocked_goals)} errors={goal_errors[:6]}",
        next_action=f"rerun /ssot-equiv-goals {ip} or answer SSOT blockers",
    )

    module_contracts = decomp.get("module_contracts") if isinstance(decomp.get("module_contracts"), list) else []
    module_goals = [
        goal for goal in goals
        if isinstance(goal.get("scope"), dict) and goal["scope"].get("level") == "module"
    ]
    required_module_contracts = [
        item for item in module_contracts
        if isinstance(item, dict)
        and item.get("requires_module_equivalence") is not False
        and item.get("blocked") is not True
    ]
    module_goal_modules = {
        str(goal.get("scope", {}).get("rtl_module") or "")
        for goal in module_goals
        if isinstance(goal.get("scope"), dict)
    }
    missing_module_goals = [
        str(item.get("rtl_module") or item.get("name") or "")
        for item in required_module_contracts
        if str(item.get("rtl_module") or item.get("name") or "") not in module_goal_modules
    ]
    blocked_module_goals = [goal.get("goal_id") for goal in module_goals if goal.get("blocked") is True]
    module_contract_active = bool(module_contracts or module_goals)
    module_equiv_ok = (
        not module_contract_active
        or (bool(required_module_contracts) and not missing_module_goals and not blocked_module_goals)
    )
    _check(
        checks,
        "module_equivalence_goals",
        module_equiv_ok,
        label="Each RTL owner module has an exact FL-vs-RTL functionality goal",
        evidence=_rel(goals_path, root),
        owner="fl-model-gen",
        detail=(
            "legacy fixture without module contracts"
            if not module_contract_active
            else (
                f"module_contracts={len(module_contracts)} module_goals={len(module_goals)} "
                f"missing={missing_module_goals[:8]} blocked={blocked_module_goals[:8]}"
            )
        ),
        next_action="rerun /ssot-fl-model and /ssot-equiv-goals; every module owning function_model refs needs a scope.level=module goal",
    )

    rtl_files = sorted((ip_dir / "rtl").glob("*.sv")) + sorted((ip_dir / "rtl").glob("*.v"))
    list_file = ip_dir / "list" / f"{ip}.f"
    rtl_ok = bool(rtl_files) and list_file.is_file() and all(not _text_has_placeholder(path) for path in rtl_files)
    _check(
        checks,
        "rtl_artifacts",
        rtl_ok,
        label="RTL and filelist artifacts exist without placeholder markers",
        evidence=[_rel(path, root) for path in rtl_files] + ([_rel(list_file, root)] if list_file.is_file() else []),
        owner="rtl-gen",
        detail=f"rtl_files={len(rtl_files)} list_exists={list_file.is_file()}",
        next_action=f"run /ssot-rtl {ip}; repair only RTL when SSOT/FL behavior is clear",
    )

    compile_report, compile_error = _read_json(compile_path)
    compile_ok = _report_passed(compile_report) and _report_dut_only(compile_report) and _report_uses_real_tool(compile_report)
    _check(
        checks,
        "dut_compile",
        compile_ok,
        label="DUT-only RTL compile evidence passes with a real HDL tool",
        evidence=_rel(compile_path, root),
        owner="rtl-gen",
        detail=compile_error or f"passed={compile_report.get('passed')} dut_only={_report_dut_only(compile_report)} tool={compile_report.get('tool')}",
        next_action="run a DUT-only compile command with verilator/pyslang/slang/iverilog and repair diagnostics",
    )

    lint_report, lint_error = _read_json(lint_path)
    lint_ok = _report_passed(lint_report) and _report_dut_only(lint_report) and _report_uses_real_tool(lint_report)
    _check(
        checks,
        "dut_lint",
        lint_ok,
        label="DUT-only lint evidence passes with a real HDL lint/parser tool",
        evidence=_rel(lint_path, root),
        owner="rtl-gen",
        detail=lint_error or f"passed={lint_report.get('passed')} dut_only={_report_dut_only(lint_report)} tool={lint_report.get('tool')}",
        next_action="run DUT-only lint; do not count cocotb/pytest as RTL lint evidence",
    )

    scoreboard_script = Path(__file__).resolve().parents[2] / "tb-gen" / "scripts" / "check_scoreboard_events.py"
    try:
        scoreboard_run = subprocess.run(
            [
                sys.executable,
                str(scoreboard_script),
                ip,
                "--root",
                str(root),
                "--source-check",
                "--require-events",
                "--require-all-goals",
            ],
            text=True,
            capture_output=True,
            timeout=30,
        )
        scoreboard_ok = scoreboard_run.returncode == 0
        scoreboard_detail = (scoreboard_run.stdout or scoreboard_run.stderr or "").strip()
    except Exception as exc:
        scoreboard_ok = False
        scoreboard_detail = str(exc)
    _check(
        checks,
        "scoreboard_contract",
        scoreboard_ok,
        label="TB consumes equivalence_goals.json and emits required scoreboard rows",
        evidence=[_rel(score_path, root), _rel(scoreboard_script, root)],
        owner="tb-gen",
        detail=scoreboard_detail,
        next_action=f"repair cocotb/pyuvm TB to instantiate EquivalenceScoreboard and cover all required goals",
    )

    sim_result = _parse_results(results_path)
    waveforms = sorted((ip_dir / "sim").glob("*.vcd")) + sorted((ip_dir / "sim").glob("*.fst"))
    sim_ok = (
        sim_result["exists"]
        and sim_result["tests"] > 0
        and sim_result["failures"] == 0
        and sim_result["errors"] == 0
        and bool(waveforms)
    )
    _check(
        checks,
        "simulation",
        sim_ok,
        label="RTL simulation completed with waveform evidence",
        evidence=[_rel(results_path, root)] + [_rel(path, root) for path in waveforms],
        owner="sim",
        detail=json.dumps(sim_result, sort_keys=True),
        next_action=f"run /sim {ip}; simulation must emit results.xml, scoreboard_events.jsonl, and waveform",
    )

    compare, compare_error = _read_json(compare_path)
    compare_summary = compare.get("summary") if isinstance(compare.get("summary"), dict) else {}
    missing_evidence = compare_summary.get("missing_evidence") if isinstance(compare_summary.get("missing_evidence"), list) else []
    stale_evidence = compare_summary.get("stale_evidence") if isinstance(compare_summary.get("stale_evidence"), list) else []
    compare_ok = (
        compare.get("status") == "pass"
        and int(compare_summary.get("total") or 0) > 0
        and compare_summary.get("goals_checked") == compare_summary.get("total")
        and not missing_evidence
        and not stale_evidence
    )
    _check(
        checks,
        "fl_rtl_compare",
        compare_ok,
        label="FL-vs-RTL comparator passes all equivalence goals",
        evidence=_rel(compare_path, root),
        owner="sim_debug",
        detail=compare_error or f"status={compare.get('status')} summary={compare_summary}",
        next_action=f"run /sim-debug {ip}; repair classified owner or answer human gate",
    )

    classify, classify_error = _read_json(classify_path)
    classifications = classify.get("classifications") if isinstance(classify.get("classifications"), list) else []
    class_schema_ok = all(
        isinstance(item, dict)
        and item.get("owner")
        and item.get("classification")
        and (
            (item.get("llm_loop_allowed") is True and item.get("repair_prompt"))
            or (item.get("llm_loop_allowed") is False and item.get("human_question"))
        )
        for item in classifications
    )
    classification_ok = classify.get("status") == "pass" and len(classifications) == 0
    _check(
        checks,
        "mismatch_classification",
        classification_ok,
        label="Mismatches are absent or fully routed before signoff",
        evidence=_rel(classify_path, root),
        owner="sim_debug",
        detail=classify_error or f"status={classify.get('status')} classifications={len(classifications)} schema_ok={class_schema_ok}",
        next_action="loopable classifications may repair the owner; human classifications must open ATLAS question and persist answer",
    )

    coverage, coverage_error = _read_json(coverage_path)
    coverage_hits = _coverage_bins(coverage)
    required_cov_refs = {
        str(ref)
        for goal in goals
        for ref in (goal.get("coverage_refs") or [])
        if str(ref).strip()
    }
    missing_cov_refs = sorted(ref for ref in required_cov_refs if coverage_hits.get(ref) is not True)
    functional = coverage.get("functional") if isinstance(coverage.get("functional"), dict) else {}
    pct = float(functional.get("pct") or 0.0) if isinstance(functional.get("pct"), (int, float)) else 0.0
    rtl_observed = coverage.get("rtl_observed") if isinstance(coverage.get("rtl_observed"), dict) else {}
    rtl_observed_status = str(rtl_observed.get("status") or "").lower()
    missing_rtl_bins = rtl_observed.get("missing_bins") if isinstance(rtl_observed.get("missing_bins"), list) else []
    invalid_rtl_rows = rtl_observed.get("invalid_rows") if isinstance(rtl_observed.get("invalid_rows"), list) else []
    function_domain = coverage.get("function_coverage") if isinstance(coverage.get("function_coverage"), dict) else {}
    cycle_domain = coverage.get("cycle_coverage") if isinstance(coverage.get("cycle_coverage"), dict) else {}
    function_domain_ok = function_domain.get("meets_target") is not False
    cycle_domain_ok = cycle_domain.get("meets_target") is not False
    coverage_ok = (
        coverage.get("source") == "ssot_coverage_summary"
        and coverage.get("status") not in {"fail", "failed", "error"}
        and not missing_cov_refs
        and not missing_rtl_bins
        and not invalid_rtl_rows
        and rtl_observed_status in {"pass", "passed", "ok"}
        and function_domain_ok
        and cycle_domain_ok
        and (pct >= 100.0 or not required_cov_refs)
    )
    _check(
        checks,
        "functional_coverage",
        coverage_ok,
        label="Functional coverage is backed by RTL-observed scoreboard evidence",
        evidence=_rel(coverage_path, root),
        owner="tb-gen",
        detail=coverage_error or (
            f"source={coverage.get('source')} status={coverage.get('status')} pct={pct} required_refs={len(required_cov_refs)} "
            f"missing_refs={missing_cov_refs[:8]} missing_rtl_bins={missing_rtl_bins[:8]} "
            f"invalid_rows={invalid_rtl_rows[:4]} rtl_observed_status={rtl_observed_status} "
            f"function_domain_ok={function_domain_ok} cycle_domain_ok={cycle_domain_ok}"
        ),
        next_action="rerun /coverage after /sim; coverage must be proven by passing scoreboard rows with real rtl_observed signals",
    )

    stale = _is_stale(
        [ssot_path, model_path, fl_check_path, decomp_path, fcov_plan_path, goals_path],
        [score_path, results_path, coverage_path, compare_path, classify_path],
        root,
    )
    _check(
        checks,
        "fresh_evidence",
        not stale,
        label="Simulation, compare, and coverage evidence is newer than SSOT/model inputs",
        evidence=stale,
        owner="LLM loop",
        detail="; ".join(stale) if stale else "evidence is fresh",
        next_action=f"rerun /sim {ip} and /sim-debug {ip} after source artifact changes",
    )

    failed = [item for item in checks if item["status"] != "pass"]
    doc = {
        "schema_version": 1,
        "type": "fl_rtl_goal_audit",
        "ip": ip,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": "pass" if not failed else "fail",
        "source_of_truth": {
            "ssot": _rel(ssot_path, root),
            "functional_model": _rel(model_path, root),
            "cycle_model": "SSOT cycle_model section",
            "equivalence_goals": _rel(goals_path, root),
        },
        "summary": {
            "total_checks": len(checks),
            "passed_checks": len(checks) - len(failed),
            "failed_checks": len(failed),
            "blockers": [item["id"] for item in failed],
        },
        "checks": checks,
        "stop_condition": {
            "req_ok": any(item["id"] == "req" and item["status"] == "pass" for item in checks),
            "ssot_ok": any(item["id"] == "ssot" and item["status"] == "pass" for item in checks),
            "fl_model_pass": any(item["id"] == "fl_model" and item["status"] == "pass" for item in checks),
            "cycle_model_present": any(item["id"] == "ssot" and item["status"] == "pass" for item in checks),
            "equivalence_goals_generated": any(item["id"] == "equivalence_goals" and item["status"] == "pass" for item in checks),
            "scoreboard_from_goals": any(item["id"] == "scoreboard_contract" and item["status"] == "pass" for item in checks),
            "simulation_complete": any(item["id"] == "simulation" and item["status"] == "pass" for item in checks),
            "fl_rtl_compare_complete": any(item["id"] == "fl_rtl_compare" and item["status"] == "pass" for item in checks),
            "mismatches_classified_or_zero": class_schema_ok and compare_path.is_file() and classify_path.is_file(),
            "coverage_linked": any(item["id"] == "functional_coverage" and item["status"] == "pass" for item in checks),
            "signoff_evidence_backed": not failed,
        },
    }
    sim_dir = ip_dir / "sim"
    sim_dir.mkdir(parents=True, exist_ok=True)
    (sim_dir / "fl_rtl_goal_audit.json").write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    return doc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ip")
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    doc = audit(args.ip, root)
    summary = doc["summary"]
    print(f"[goal-audit] wrote {args.ip}/sim/fl_rtl_goal_audit.json")
    print(
        "[goal-audit] "
        f"status={doc['status']} passed={summary['passed_checks']}/{summary['total_checks']} "
        f"blockers={','.join(summary['blockers']) if summary['blockers'] else 'none'}"
    )
    return 0 if doc["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
