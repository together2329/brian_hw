#!/usr/bin/env python3
"""Compare structured FL-vs-RTL scoreboard evidence against equivalence goals."""

from __future__ import annotations

import argparse
import json
import os
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


def _resolve_project_root(root_arg: str, ip_root_arg: str, ip: str) -> Path:
    project_root = Path(os.path.expandvars(root_arg or os.environ.get("ATLAS_PROJECT_ROOT") or ".")).expanduser().resolve()
    ip_root_raw = (ip_root_arg or os.environ.get("ATLAS_IP_ROOT") or "").strip()
    if ip_root_raw:
        ip_root = Path(os.path.expandvars(ip_root_raw)).expanduser()
        if not ip_root.is_absolute():
            ip_root = project_root / ip_root
        ip_root = ip_root.resolve()
        if not ip or ip_root.name == ip or (ip_root / "yaml").is_dir():
            return ip_root.parent
    return project_root


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return doc if isinstance(doc, dict) else {}


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.is_file():
        return rows
    for line_no, raw in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except Exception as exc:
            rows.append({
                "goal_id": "",
                "passed": False,
                "mismatch": f"scoreboard_events.jsonl parse error at line {line_no}: {exc}",
            })
            continue
        if isinstance(item, dict):
            rows.append(item)
    return rows


def _scoreboard_schema_errors(row: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = [
        "goal_id",
        "scenario_id",
        "cycle",
        "stimulus",
        "fl_expected",
        "rtl_observed",
        "passed",
        "mismatch",
        "coverage_refs",
    ]
    for key in required:
        if key not in row:
            errors.append(f"missing {key}")
    if not str(row.get("goal_id") or "").strip():
        errors.append("empty goal_id")
    if not str(row.get("scenario_id") or "").strip():
        errors.append("empty scenario_id")
    cycle = row.get("cycle")
    if isinstance(cycle, bool) or not isinstance(cycle, (int, float)):
        errors.append("cycle must be numeric")
    if not isinstance(row.get("passed"), bool):
        errors.append("passed must be boolean")
    mismatch = row.get("mismatch")
    if not isinstance(mismatch, str):
        errors.append("mismatch must be a string")
    elif row.get("passed") is True and mismatch.strip():
        errors.append("passed row must not carry mismatch text")
    elif row.get("passed") is False and not mismatch.strip():
        errors.append("failing row must explain mismatch")
    if not isinstance(row.get("coverage_refs"), list):
        errors.append("coverage_refs must be a list")
    return errors


def _parse_results(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"exists": False, "total": 0, "fail": 0, "errors": 0, "source": ""}
    result = {"exists": True, "total": 0, "fail": 0, "errors": 0, "source": str(path)}
    try:
        root = ET.fromstring(path.read_text(encoding="utf-8", errors="replace"))
    except Exception as exc:
        result.update({"fail": 1, "errors": 1, "parse_error": str(exc)})
        return result
    tests = failures = errors = 0
    for elem in root.iter():
        if elem.tag.endswith("testsuite"):
            tests += int(float(elem.attrib.get("tests", "0") or 0))
            failures += int(float(elem.attrib.get("failures", "0") or 0))
            errors += int(float(elem.attrib.get("errors", "0") or 0))
    if tests == 0 and root.tag.endswith("testsuite"):
        tests = int(float(root.attrib.get("tests", "0") or 0))
        failures = int(float(root.attrib.get("failures", "0") or 0))
        errors = int(float(root.attrib.get("errors", "0") or 0))
    if tests == 0:
        testcases = [e for e in root.iter() if e.tag.endswith("testcase")]
        tests = len(testcases)
        for case in testcases:
            failures += len([c for c in list(case) if c.tag.endswith("failure")])
            errors += len([c for c in list(case) if c.tag.endswith("error")])
    result.update({"total": tests, "fail": failures + errors, "errors": errors, "failures": failures})
    return result


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _strip_volatile_fields(value: Any) -> Any:
    """Return a JSON-like value with run metadata removed for no-op detection."""
    if isinstance(value, dict):
        return {
            str(key): _strip_volatile_fields(item)
            for key, item in value.items()
            if key != "generated_at"
        }
    if isinstance(value, list):
        return [_strip_volatile_fields(item) for item in value]
    return value


def _preserve_generated_at_on_noop(path: Path, doc: dict[str, Any]) -> dict[str, Any]:
    """Keep output hashes stable when a rerun produces the same evidence.

    Approval decisions may pin raw evidence hashes. A comparator rerun should
    not invalidate those pins solely because wall-clock metadata changed.
    """
    if not path.is_file():
        return doc
    try:
        existing = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return doc
    if not isinstance(existing, dict):
        return doc
    if _strip_volatile_fields(existing) != _strip_volatile_fields(doc):
        return doc
    generated_at = existing.get("generated_at")
    if isinstance(generated_at, str) and generated_at.strip():
        doc["generated_at"] = generated_at
    return doc


def _stale_evidence(root: Path, sources: list[Path], evidence: list[Path]) -> list[str]:
    existing_sources = [path for path in sources if path.is_file()]
    existing_evidence = [path for path in evidence if path.is_file()]
    if not existing_sources or not existing_evidence:
        return []
    newest_source = max(existing_sources, key=lambda path: path.stat().st_mtime)
    newest_source_mtime = newest_source.stat().st_mtime
    stale: list[str] = []
    for path in existing_evidence:
        if path.stat().st_mtime + 0.5 < newest_source_mtime:
            stale.append(f"{_rel(path, root)} older than {_rel(newest_source, root)}")
    return stale


def _derived_stale_evidence(root: Path, source: Path, derived: list[Path]) -> list[str]:
    if not source.is_file():
        return []
    source_mtime = source.stat().st_mtime
    stale: list[str] = []
    for path in derived:
        if not path.is_file():
            continue
        if path.stat().st_mtime + 0.5 < source_mtime:
            stale.append(f"{_rel(path, root)} older than {_rel(source, root)}")
    return stale


def _goal_map(goals_doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for goal in goals_doc.get("goals") if isinstance(goals_doc.get("goals"), list) else []:
        if not isinstance(goal, dict):
            continue
        gid = str(goal.get("goal_id") or "").strip()
        if gid:
            out[gid] = goal
    return out


def _module_scope_error(goal: dict[str, Any], row: dict[str, Any]) -> str:
    scope = goal.get("scope") if isinstance(goal.get("scope"), dict) else {}
    if scope.get("level") != "module":
        return ""
    row_scope = row.get("scope") if isinstance(row.get("scope"), dict) else {}
    if row_scope.get("level") != "module":
        return "module equivalence row missing scope.level=module"
    if row_scope.get("rtl_module") != scope.get("rtl_module"):
        return f"module equivalence row rtl_module={row_scope.get('rtl_module')!r} expected {scope.get('rtl_module')!r}"
    return ""


def _coverage_hit_map(coverage: dict[str, Any]) -> dict[str, bool]:
    functional = coverage.get("functional") if isinstance(coverage.get("functional"), dict) else {}
    bins = functional.get("bins") if isinstance(functional.get("bins"), dict) else {}
    top_bins = coverage.get("functional_bins") if isinstance(coverage.get("functional_bins"), dict) else {}
    out: dict[str, bool] = {}
    for key, value in {**top_bins, **bins}.items():
        if isinstance(value, bool):
            out[str(key)] = value
        elif isinstance(value, dict):
            out[str(key)] = bool(value.get("hit") or value.get("passed") or value.get("covered"))
        elif isinstance(value, (int, float)):
            out[str(key)] = value > 0
    for key, value in coverage.items():
        if isinstance(value, bool):
            out.setdefault(str(key), value)
    return out


_KIND_STIMULUS_PATTERNS = (
    ("reset", {"rst_n": 0, "reset": 1, "enable": 0, "clear": 0}),
    ("clear", {"clear": 1}),
    ("hold", {"enable": 0, "clear": 0}),
    ("idle", {"enable": 0, "clear": 0}),
    ("advance", {"enable": 1, "clear": 0}),
    ("run", {"enable": 1, "clear": 0}),
    ("step", {"enable": 1, "clear": 0}),
    ("count", {"enable": 1, "clear": 0}),
    ("accept", {"enable": 1, "clear": 0}),
    ("transfer", {"enable": 1, "clear": 0}),
    ("request", {"enable": 1, "clear": 0}),
)


def _stimulus_contract_violation(rows: list[dict[str, Any]]) -> str:
    """Return a non-empty reason when the TB stimulus contradicts the named transaction kind."""
    for row in rows:
        if not isinstance(row, dict):
            continue
        stimulus = row.get("stimulus") if isinstance(row.get("stimulus"), dict) else {}
        fl = row.get("fl_expected") if isinstance(row.get("fl_expected"), dict) else {}
        fl_txn = fl.get("transaction") if isinstance(fl.get("transaction"), dict) else {}
        fl_result = fl.get("model_result") if isinstance(fl.get("model_result"), dict) else {}
        if not stimulus:
            stimulus = fl_txn
        if not stimulus:
            continue
        kind_candidates = [
            stimulus.get("kind"),
            fl_txn.get("kind"),
            fl_result.get("transaction_name"),
            fl_result.get("transaction_id"),
        ]
        kind = ""
        for candidate in kind_candidates:
            text_candidate = str(candidate or "").lower()
            if any(token in text_candidate for token, _ in _KIND_STIMULUS_PATTERNS):
                kind = text_candidate
                break
        if not kind:
            kind = str(stimulus.get("kind") or "").lower()
        if not kind:
            continue
        violations: list[str] = []
        for token, signals in _KIND_STIMULUS_PATTERNS:
            if token not in kind:
                continue
            for signal, expected in signals.items():
                if signal not in stimulus:
                    continue
                actual = stimulus.get(signal)
                if isinstance(actual, bool):
                    actual = int(actual)
                if isinstance(actual, (int, float)) and int(actual) != int(expected):
                    violations.append(f"{signal}={int(actual)} (kind '{kind}' requires {signal}={int(expected)})")
        if violations:
            return "stimulus contradicts transaction kind: " + "; ".join(violations)
    return ""


def _apb_stimulus_contract_violation(rows: list[dict[str, Any]]) -> str:
    legal_offsets = {0x00, 0x04, 0x08, 0x0C, 0x10}
    legal_write_offsets = {0x00, 0x08, 0x0C}
    for row in rows:
        if not isinstance(row, dict):
            continue
        stimulus = row.get("stimulus") if isinstance(row.get("stimulus"), dict) else {}
        fl = row.get("fl_expected") if isinstance(row.get("fl_expected"), dict) else {}
        fl_txn = fl.get("transaction") if isinstance(fl.get("transaction"), dict) else {}
        fl_result = fl.get("model_result") if isinstance(fl.get("model_result"), dict) else {}
        if not stimulus:
            stimulus = fl_txn
        kind_text = " ".join(
            str(item or "").lower()
            for item in (
                stimulus.get("kind"),
                fl_txn.get("kind"),
                fl_result.get("transaction_id"),
                fl_result.get("transaction_name"),
            )
        )
        required: dict[str, int] = {}
        paddr_rule = ""
        if "fm_read_data_in" in kind_text or "read_synchronized_input" in kind_text:
            required = {"psel": 1, "penable": 1, "pwrite": 0, "paddr": 0x04}
        elif "fm_apb_write_rw" in kind_text or "write_data_out_dir_irq_en" in kind_text:
            required = {"psel": 1, "penable": 1, "pwrite": 1}
            paddr_rule = "legal_write"
        elif "fm_w1c_irq_status" in kind_text or "clear_pending_w1c" in kind_text:
            required = {"psel": 1, "penable": 1, "pwrite": 1, "paddr": 0x10}
        elif "fm_apb_illegal_offset" in kind_text or "illegal_offset_error_response" in kind_text:
            required = {"psel": 1, "penable": 1}
            paddr_rule = "illegal"
        if not required and not paddr_rule:
            continue
        violations: list[str] = []
        for signal, expected in required.items():
            if signal not in stimulus:
                violations.append(f"missing {signal}={expected}")
                continue
            actual = stimulus.get(signal)
            if isinstance(actual, bool):
                actual = int(actual)
            if isinstance(actual, (int, float)) and int(actual) != expected:
                violations.append(f"{signal}={int(actual)} expected {expected}")
        if paddr_rule and "paddr" not in stimulus and "addr" not in stimulus:
            violations.append("missing paddr")
        paddr_value = stimulus.get("paddr", stimulus.get("addr"))
        if isinstance(paddr_value, bool):
            paddr_value = int(paddr_value)
        if isinstance(paddr_value, (int, float)):
            paddr_int = int(paddr_value)
            if paddr_rule == "legal_write" and paddr_int not in legal_write_offsets:
                violations.append(f"paddr=0x{paddr_int:X} is not a legal writable APB offset")
            elif paddr_rule == "illegal" and paddr_int in legal_offsets:
                violations.append(f"paddr=0x{paddr_int:X} is a legal APB offset, not an illegal-offset stimulus")
        if violations:
            return "APB stimulus does not satisfy transaction precondition: " + "; ".join(violations)
    return ""


def _goal_looks_like_csr(goal: dict[str, Any], tx_type: str) -> bool:
    text = " ".join(
        str(item or "").lower()
        for item in (
            goal.get("goal_id"),
            goal.get("kind"),
            goal.get("title"),
            tx_type,
            goal.get("stimulus_contract"),
        )
    )
    return any(token in text for token in ("apb", "csr", "register", "paddr", "psel", "penable"))


def _abstract_stimulus_contract_gap(goal: dict[str, Any], rows: list[dict[str, Any]], manifest: Any = None) -> str:
    if not isinstance(manifest, dict):
        return ""
    contract = goal.get("stimulus_contract") if isinstance(goal.get("stimulus_contract"), dict) else {}
    if contract.get("machine_spec"):
        return ""
    required = [str(item) for item in contract.get("required_fields") or [] if str(item).strip()]
    if not required:
        return ""
    tx_type = str(contract.get("transaction_type") or "")
    if _goal_looks_like_csr(goal, tx_type):
        return ""

    input_map = manifest.get("input_map") if isinstance(manifest.get("input_map"), dict) else {}
    input_ports = {str(item) for item in manifest.get("input_ports") or []}
    sample_inputs = {str(item) for item in manifest.get("sample_inputs") or []}
    metadata = {"kind", "scenario_id", "cycle", "observed_signals"}
    undriven: list[str] = []
    for field in required:
        if field in metadata:
            continue
        mapped_port = input_map.get(field)
        if mapped_port and str(mapped_port) in input_ports:
            continue
        if field in input_ports or field in sample_inputs:
            continue
        if any(isinstance(row.get("stimulus"), dict) and field in row["stimulus"] for row in rows):
            undriven.append(field)
    if not undriven:
        return ""
    scalar_fields = {"addr", "address", "data", "value", "op", "operation", "cmd", "command"}
    if len(undriven) == 1 and undriven[0].lower() in scalar_fields:
        return ""
    preview = ", ".join(undriven[:8])
    suffix = "" if len(undriven) <= 8 else f", ... +{len(undriven) - 8}"
    return (
        "TB stimulus carries FunctionalModel-only required fields that are not "
        f"driven through input_map/input_ports and no protocol encoder or machine_spec is present: {preview}{suffix}"
    )


def _classify_failure(goal: dict[str, Any], rows: list[dict[str, Any]], reason: str, manifest: Any = None) -> dict[str, Any]:
    text = " ".join(
        [reason]
        + [str(r.get("mismatch") or r.get("error") or r.get("owner_hint") or "") for r in rows if isinstance(r, dict)]
        + [str(goal.get("blocker") or "")]
    ).lower()
    repair_reason = reason
    stimulus_violation = _stimulus_contract_violation(rows)
    if stimulus_violation:
        text = text + " " + stimulus_violation.lower() + " driver"
        repair_reason = f"{repair_reason}; {stimulus_violation}" if repair_reason else stimulus_violation
    apb_stimulus_violation = _apb_stimulus_contract_violation(rows)
    if apb_stimulus_violation:
        text = text + " " + apb_stimulus_violation.lower() + " driver"
        repair_reason = (
            f"{repair_reason}; {apb_stimulus_violation}" if repair_reason else apb_stimulus_violation
        )
    abstract_stimulus_gap = _abstract_stimulus_contract_gap(goal, rows, manifest)
    if abstract_stimulus_gap:
        text = text + " " + abstract_stimulus_gap.lower() + " driver"
        repair_reason = f"{repair_reason}; {abstract_stimulus_gap}" if repair_reason else abstract_stimulus_gap
    locked_change = (
        "change functionalmodel" in text
        or "functionalmodel change" in text
        or "change functional model" in text
        or "functional model change" in text
        or "golden model change" in text
        or "coverage goal change" in text
        or "change coverage goal" in text
        or "coverage target change" in text
        or "interface contract change" in text
        or "change interface contract" in text
        or "performance target change" in text
        or "change performance target" in text
        or "waiver" in text
    )
    if goal.get("blocked") or "ambiguous" in text or "undefined" in text or "ssot question" in text:
        classification = "ssot_ambiguity"
        owner = "ssot-gen"
        loop = False
    elif "contradiction" in text or "conflict" in text:
        classification = "ssot_contradiction"
        owner = "ssot-gen"
        loop = False
    elif locked_change:
        classification = "locked_artifact_change_requires_human"
        owner = "human"
        loop = False
    elif (
        "module equivalence row" in text
        or "scope.level=module" in text
        or "must record scope" in text
        or "no comparable rtl observable" in text
    ):
        classification = "tb_bug"
        owner = "tb-gen"
        loop = True
    elif "fl_model" in text or "functional model" in text or "model api" in text:
        classification = "fl_model_bug"
        owner = "human"
        loop = False
    elif "missing scoreboard" in text or "untested" in text:
        classification = "coverage_bug"
        owner = "tb-gen"
        loop = True
    elif "driver" in text or "monitor" in text or "scoreboard" in text or "tb" in text:
        classification = "tb_bug"
        owner = "tb-gen"
        loop = True
    elif "coverage" in text:
        classification = "coverage_bug"
        owner = "tb-gen"
        loop = True
    elif "tool" in text or "parse error" in text or "missing results" in text:
        classification = "tool_issue"
        owner = "sim_debug"
        loop = True
    elif "waiver" in text:
        classification = "waiver_required"
        owner = "human"
        loop = False
    else:
        classification = "rtl_bug"
        owner = "rtl-gen"
        loop = True

    first = rows[0] if rows else {}
    return {
        "goal_id": goal.get("goal_id"),
        "classification": classification,
        "owner": owner,
        "llm_loop_allowed": loop,
        "reason": repair_reason,
        "evidence": {
            "ssot_refs": goal.get("ssot_refs") or [],
            "scoreboard_rows": rows[:8],
            "fl_expected": first.get("fl_expected") if isinstance(first, dict) else {},
            "rtl_observed": first.get("rtl_observed") if isinstance(first, dict) else {},
            "sim_result": "failed",
        },
        "authority_policy": {
            "locked_artifacts": ["requirement", "ssot_spec", "functional_model", "coverage_plan", "interface_contract", "performance_target"],
            "llm_editable_artifacts": ["rtl", "tb", "test_vector", "scoreboard_implementation", "lint_fix", "report"],
            "rule": "Do not change locked oracle artifacts from sim-debug; open a human gate instead.",
        },
        "repair_prompt": _repair_prompt(goal, classification, owner, repair_reason) if loop else "",
        "human_question": _human_question(goal, repair_reason) if not loop else "",
    }


def _repair_prompt(goal: dict[str, Any], classification: str, owner: str, reason: str) -> str:
    gid = str(goal.get("goal_id") or "")
    if classification == "rtl_bug":
        return (
            f"Repair RTL for {gid}. Keep SSOT and FunctionalModel expected behavior unchanged. "
            f"Use equivalence goal pass criteria and scoreboard mismatch evidence. Reason: {reason}"
        )
    if classification == "fl_model_bug":
        return (
            f"Repair FunctionalModel for {gid} to match SSOT refs {goal.get('ssot_refs')}. "
            f"Do not copy RTL observed behavior unless SSOT proves it. Reason: {reason}"
        )
    if classification in {"tb_bug", "coverage_bug"}:
        return (
            f"Repair TB/scoreboard/coverage for {gid}. Keep expected values sourced from "
            f"FunctionalModel.apply and SSOT. Reason: {reason}"
        )
    return f"Repair {owner} for {gid}. Reason: {reason}"


def _human_question(goal: dict[str, Any], reason: str) -> str:
    return (
        "Decision needed:\n"
        f"  Define or approve expected behavior for {goal.get('goal_id')}.\n\n"
        "Locked artifact rule:\n"
        "  Requirement, SSOT/spec, FunctionalModel golden semantics, coverage goals, "
        "interface contracts, and performance targets require human approval before "
        "they change. RTL/TB/tests may be repaired automatically after the oracle is locked.\n\n"
        "Evidence:\n"
        f"  SSOT refs: {', '.join(str(x) for x in goal.get('ssot_refs') or [])}\n"
        f"  Reason: {reason}\n\n"
        "Options:\n"
        "  A. Update SSOT with the intended behavior and regenerate FL/equivalence goals.\n"
        "  B. Mark this behavior as not required and provide an explicit waiver/rationale.\n\n"
        "Recommended default:\n"
        "  Update SSOT, because RTL/TB expected values must remain source-of-truth driven.\n\n"
        "Downstream effect:\n"
        "  SSOT, FunctionalModel, equivalence goals, TB scoreboard, and coverage may change."
    )


def _stale_oracle_classification(stale_evidence: list[str]) -> dict[str, Any]:
    reason = (
        "derived FL/equivalence oracle artifacts are older than the current SSOT; "
        "scoreboard mismatches cannot be assigned to RTL until the oracle is regenerated"
    )
    return {
        "goal_id": "",
        "classification": "stale_oracle",
        "owner": "fl-model-gen",
        "llm_loop_allowed": True,
        "reason": reason,
        "evidence": {
            "stale_evidence": stale_evidence,
            "sim_result": "stale",
        },
        "authority_policy": {
            "locked_artifacts": ["ssot_spec", "interface_contract", "performance_target"],
            "llm_editable_artifacts": ["functional_model", "equivalence_goals", "coverage_plan", "tb", "scoreboard_implementation"],
            "rule": "Regenerate derived oracle artifacts from SSOT before classifying RTL/TB mismatches.",
        },
        "repair_prompt": (
            "Regenerate FunctionalModel, FL checks, coverage/equivalence oracle artifacts from the current SSOT, "
            "then rerun tb-gen, sim, coverage, sim-debug, and goal-audit. Do not repair RTL from stale oracle evidence."
        ),
        "human_question": "",
    }


def compare(ip: str, root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    ip_dir = root / ip
    goals_path = ip_dir / "verify" / "equivalence_goals.json"
    score_path = ip_dir / "sim" / "scoreboard_events.jsonl"
    result_candidates = [
        ip_dir / "sim" / "results.xml",
        ip_dir / "tb" / "cocotb" / "results.xml",
    ]
    results_path = next((p for p in result_candidates if p.is_file()), result_candidates[0])
    coverage_path = ip_dir / "cov" / "coverage.json"
    fl_check_path = ip_dir / "model" / "fl_model_check.json"
    ssot_path = ip_dir / "yaml" / f"{ip}.ssot.yaml"
    model_path = ip_dir / "model" / "functional_model.py"
    decomp_path = ip_dir / "model" / "decomposition.json"
    fcov_plan_path = ip_dir / "cov" / "fcov_plan.json"
    tb_manifest_path = ip_dir / "tb" / "cocotb" / "tb_manifest.json"

    goals_doc = _load_json(goals_path)
    goals = _goal_map(goals_doc)
    tb_manifest = _load_json(tb_manifest_path)
    rows = _load_jsonl(score_path)
    rows_by_goal: dict[str, list[dict[str, Any]]] = {gid: [] for gid in goals}
    orphan_rows: list[dict[str, Any]] = []
    for row in rows:
        schema_errors = _scoreboard_schema_errors(row)
        if schema_errors:
            row = dict(row)
            row["_schema_errors"] = schema_errors
            row["passed"] = False
            if not str(row.get("mismatch") or "").strip():
                row["mismatch"] = "scoreboard schema error: " + "; ".join(schema_errors)
        gid = str(row.get("goal_id") or "").strip()
        if gid in rows_by_goal:
            rows_by_goal[gid].append(row)
        else:
            orphan_rows.append(row)

    sim_result = _parse_results(results_path)
    coverage = _load_json(coverage_path)
    coverage_hits = _coverage_hit_map(coverage)
    fl_check = _load_json(fl_check_path)

    checked = passed = failed = blocked = untested = 0
    goal_results: list[dict[str, Any]] = []
    classifications: list[dict[str, Any]] = []

    missing_evidence: list[str] = []
    if not goals_path.is_file():
        missing_evidence.append(str(goals_path.relative_to(root)))
    if not score_path.is_file():
        missing_evidence.append(str(score_path.relative_to(root)))
    if not sim_result.get("exists"):
        missing_evidence.append(str(results_path.relative_to(root)))
    if fl_check and fl_check.get("passed") is not True:
        missing_evidence.append(str(fl_check_path.relative_to(root)) + " passed=false")
    stale_evidence = _stale_evidence(
        root,
        [ssot_path, model_path, fl_check_path, decomp_path, fcov_plan_path, goals_path],
        [score_path, results_path, coverage_path],
    )
    stale_oracle_evidence = _derived_stale_evidence(
        root,
        ssot_path,
        [model_path, fl_check_path, decomp_path, fcov_plan_path, goals_path],
    )
    stale_blocks_compare = bool(stale_evidence or stale_oracle_evidence)
    if stale_oracle_evidence:
        classifications.append(_stale_oracle_classification(stale_oracle_evidence))

    for gid, goal in goals.items():
        goal_rows = rows_by_goal.get(gid) or []
        cov_refs = [str(x) for x in goal.get("coverage_refs") or []]
        cov_hit = all(coverage_hits.get(ref, False) for ref in cov_refs) if cov_refs and coverage_hits else None
        if stale_blocks_compare:
            status = "stale"
            if goal_rows:
                checked += 1
        elif goal.get("blocked"):
            status = "blocked"
            blocked += 1
            reason = str(goal.get("blocker") or "equivalence goal is blocked by SSOT")
            classifications.append(_classify_failure(goal, goal_rows, reason, tb_manifest))
        elif not goal_rows:
            status = "untested"
            untested += 1
            reason = "missing scoreboard evidence for goal"
            classifications.append(_classify_failure(goal, goal_rows, reason, tb_manifest))
        else:
            checked += 1
            row_failures = [r for r in goal_rows if r.get("passed") is not True]
            for row in goal_rows:
                scope_error = _module_scope_error(goal, row)
                if scope_error:
                    row = dict(row)
                    row["passed"] = False
                    row["mismatch"] = scope_error
                    row_failures.append(row)
            if row_failures:
                status = "fail"
                failed += 1
                reason = str(row_failures[0].get("mismatch") or row_failures[0].get("error") or "scoreboard mismatch")
                classifications.append(_classify_failure(goal, row_failures, reason, tb_manifest))
            else:
                status = "pass"
                passed += 1
        goal_results.append({
            "goal_id": gid,
            "status": status,
            "events": len(goal_rows),
            "coverage_refs": cov_refs,
            "coverage_hit": cov_hit,
        })

    if orphan_rows:
        if stale_blocks_compare:
            pass
        else:
            classifications.append({
                "goal_id": "",
                "classification": "tb_bug",
                "owner": "tb-gen",
                "llm_loop_allowed": True,
                "reason": "scoreboard emitted rows without a known goal_id",
                "evidence": {"scoreboard_rows": orphan_rows[:8], "sim_result": "failed"},
                "repair_prompt": "Repair TB scoreboard to emit only goal_id values from equivalence_goals.json.",
                "human_question": "",
            })

    if sim_result.get("fail") and not stale_blocks_compare:
        classification = "tool_issue" if sim_result.get("parse_error") or sim_result.get("errors") else "tb_bug"
        owner = "sim_debug" if classification == "tool_issue" else "tb-gen"
        reason = (
            "simulation result XML reports failures/errors outside scoreboard evidence"
            if not sim_result.get("parse_error") else
            f"simulation result XML parse error: {sim_result.get('parse_error')}"
        )
        classifications.append({
            "goal_id": "",
            "classification": classification,
            "owner": owner,
            "llm_loop_allowed": True,
            "reason": reason,
            "evidence": {
                "sim_result": sim_result,
                "scoreboard_rows": rows[:8],
            },
            "repair_prompt": (
                "Repair simulation/TB infrastructure so every failing testcase is tied "
                "to a scoreboard goal_id with expected/got evidence, then rerun /sim "
                "and /sim-debug."
            ),
            "human_question": "",
        })
        failed = max(failed, 1)

    total = len(goals)
    status = "pending"
    if total == 0:
        status = "pending"
    elif stale_blocks_compare:
        status = "stale"
    elif blocked:
        status = "blocked"
    elif failed or orphan_rows:
        status = "fail"
    elif untested or missing_evidence:
        status = "pending"
    elif checked == total and passed == total:
        status = "pass"

    compare_doc = {
        "schema_version": 1,
        "type": "fl_rtl_compare",
        "ip": ip,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": status,
        "sources": {
            "equivalence_goals": str(goals_path.relative_to(root)),
            "scoreboard_events": str(score_path.relative_to(root)),
            "results_xml": str(results_path.relative_to(root)),
            "coverage": str(coverage_path.relative_to(root)),
            "fl_model_check": str(fl_check_path.relative_to(root)),
        },
        "summary": {
            "total": total,
            "goals_checked": checked,
            "goals_passed": passed,
            "goals_failed": failed,
            "goals_blocked": blocked,
            "goals_untested": untested,
            "scoreboard_events": len(rows),
            "orphan_scoreboard_events": len(orphan_rows),
            "missing_evidence": missing_evidence,
            "stale_evidence": stale_evidence,
            "stale_oracle_evidence": stale_oracle_evidence,
            "sim_results": sim_result,
        },
        "goals": goal_results,
    }
    classify_doc = {
        "schema_version": 1,
        "type": "mismatch_classification",
        "ip": ip,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": "pass" if not classifications and status == "pass" else ("pending" if status == "pending" else "action_required"),
        "classifications": classifications,
    }

    sim_dir = ip_dir / "sim"
    sim_dir.mkdir(parents=True, exist_ok=True)
    compare_path = sim_dir / "fl_rtl_compare.json"
    classify_path = sim_dir / "mismatch_classification.json"
    compare_doc = _preserve_generated_at_on_noop(compare_path, compare_doc)
    classify_doc = _preserve_generated_at_on_noop(classify_path, classify_doc)
    compare_path.write_text(json.dumps(compare_doc, indent=2) + "\n", encoding="utf-8")
    classify_path.write_text(json.dumps(classify_doc, indent=2) + "\n", encoding="utf-8")
    return compare_doc, classify_doc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ip")
    parser.add_argument("--root", default=os.environ.get("ATLAS_PROJECT_ROOT") or ".")
    parser.add_argument("--ip-root", "--ip_root", dest="ip_root", default=os.environ.get("ATLAS_IP_ROOT") or "")
    args = parser.parse_args()
    root = _resolve_project_root(args.root, args.ip_root, args.ip)
    compare_doc, classify_doc = compare(args.ip, root)
    summary = compare_doc["summary"]
    print(f"[compare_fl_rtl_results] wrote {args.ip}/sim/fl_rtl_compare.json")
    print(f"[compare_fl_rtl_results] wrote {args.ip}/sim/mismatch_classification.json")
    print(
        "[compare_fl_rtl_results] "
        f"status={compare_doc['status']} total={summary['total']} "
        f"checked={summary['goals_checked']} passed={summary['goals_passed']} "
        f"failed={summary['goals_failed']} blocked={summary['goals_blocked']} "
        f"untested={summary['goals_untested']} classifications={len(classify_doc['classifications'])}"
    )
    return 0 if compare_doc["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
