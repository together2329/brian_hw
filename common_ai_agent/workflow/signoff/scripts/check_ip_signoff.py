#!/usr/bin/env python3
"""Strict local IP signoff gate.

This script aggregates the machine-checkable evidence required by
IP_SIGNOFF.md.  It intentionally does not modify locked truth and does not infer
semantic approval from prose.  It writes a JSON and Markdown signoff report and
exits non-zero when required local evidence is missing or failing.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import yaml


RTL_TODO_HASH_VOLATILE_KEYS = {
    "connection_contract_suggestions",
    "generated_at",
    "gate",
    "manifest_hierarchy_evidence",
    "manifest_signal_flow_evidence",
    "owner_logic_evidence",
    "reference_profile",
    "reference_scale_gap",
    "rtl_implementation_depth_evidence",
    "rtl_placeholder_free_evidence",
    "static_evidence",
    "static_rtl_evidence",
    "todo_completion",
    "top_input_consumption_evidence",
    "top_io_contract_evidence",
    "top_output_drive_evidence",
}

REQUIRED_SCOREBOARD_KEYS = {
    "goal_id",
    "scenario_id",
    "cycle",
    "stimulus",
    "fl_expected",
    "rtl_observed",
    "passed",
    "mismatch",
    "coverage_refs",
}

BASE_CONTRACT_EVIDENCE_IDS = {
    "ssot",
    "fl_equivalence",
    "cl_contract",
    "equivalence_goals",
    "rtl_compile",
    "dut_lint",
    "tb_python_compile",
    "simulation",
    "scoreboard_schema",
    "coverage",
}

SIGNAL_OBSERVABLE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_$]*(?:\[[^\]]+\])?$")


def _observable_signal_names(goal: dict[str, Any]) -> set[str]:
    contract = goal.get("expected_contract") if isinstance(goal.get("expected_contract"), dict) else {}
    observables = contract.get("observables")
    if not isinstance(observables, list):
        return set()

    names: set[str] = set()
    for item in observables:
        if not isinstance(item, str):
            continue
        text = item.strip()
        if SIGNAL_OBSERVABLE_RE.fullmatch(text):
            names.add(text.split("[", 1)[0])
    return names


def _scoreboard_goal_observables(goals_path: Path) -> tuple[dict[str, set[str]], list[str]]:
    doc, err = _read_json(goals_path)
    if err:
        return {}, [err]
    goals = doc.get("goals")
    if not isinstance(goals, list):
        return {}, [f"{goals_path} has no goals[] list"]

    out: dict[str, set[str]] = {}
    issues: list[str] = []
    for idx, goal in enumerate(goals):
        if not isinstance(goal, dict):
            issues.append(f"goals[{idx}] is not an object")
            continue
        gid = str(goal.get("goal_id") or "").strip()
        if not gid:
            issues.append(f"goals[{idx}] missing goal_id")
            continue
        out[gid] = _observable_signal_names(goal)
    return out, issues


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _read_json(path: Path) -> tuple[dict[str, Any], str]:
    if not path.is_file():
        return {}, f"missing {path}"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {}, f"invalid JSON {path}: {exc}"
    if not isinstance(data, dict):
        return {}, f"{path} root must be a JSON object"
    return data, ""


def _read_yaml(path: Path) -> tuple[dict[str, Any], str]:
    if not path.is_file():
        return {}, f"missing {path}"
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        return {}, f"invalid YAML {path}: {exc}"
    if not isinstance(data, dict):
        return {}, f"{path} root must be a mapping"
    return data, ""


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _stable_json_sha256(path: Path) -> str:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return ""

    def normalize(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                str(key): normalize(item)
                for key, item in value.items()
                if str(key) not in RTL_TODO_HASH_VOLATILE_KEYS
            }
        if isinstance(value, list):
            return [normalize(item) for item in value]
        return value

    payload = json.dumps(normalize(data), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _as_int(value: Any) -> int:
    try:
        return int(value or 0)
    except Exception:
        return 0


@dataclass
class Gate:
    name: str
    status: str
    artifact: str
    summary: str
    issues: list[str]


class SignoffChecker:
    def __init__(self, ip: str, root: Path, *, require_human_waiver_approval: bool) -> None:
        self.ip = ip
        self.root = root.resolve()
        self.ip_dir = self.root / ip
        self.require_human_waiver_approval = require_human_waiver_approval
        self.gates: list[Gate] = []
        self.ip_contract: dict[str, Any] = {}

    def rel(self, path: Path) -> str:
        try:
            return path.relative_to(self.ip_dir).as_posix()
        except ValueError:
            try:
                return path.relative_to(self.root).as_posix()
            except ValueError:
                return str(path)

    def add(self, name: str, status: str, artifact: Path | str, summary: str, issues: list[str] | None = None) -> None:
        art = self.rel(artifact) if isinstance(artifact, Path) else artifact
        self.gates.append(Gate(name=name, status=status, artifact=art, summary=summary, issues=issues or []))

    def check_ssot(self) -> None:
        path = self.ip_dir / "yaml" / f"{self.ip}.ssot.yaml"
        doc, err = _read_yaml(path)
        issues = [err] if err else []
        if not issues:
            for key in ("top_module", "io_list", "function_model", "cycle_model"):
                if key not in doc:
                    issues.append(f"missing required SSOT key: {key}")
        self.add("ssot", "fail" if issues else "pass", path, "SSOT exists and parses", issues)

    def check_ip_contract(self) -> None:
        path = self.ip_dir / "verify" / "ip_contract.json"
        doc, err = _read_json(path)
        issues = [err] if err else []
        if not issues:
            self.ip_contract = doc
            if doc.get("type") != "ip_evidence_contract":
                issues.append("type must be ip_evidence_contract")
            if doc.get("generation") != "derived_from_ip_artifacts_not_static_profile":
                issues.append("generation must prove contract was derived from IP artifacts, not a static profile")
            policy = doc.get("policy") if isinstance(doc.get("policy"), dict) else {}
            if policy.get("no_static_profile_selection") is not True:
                issues.append("policy.no_static_profile_selection must be true")
            capabilities = doc.get("capabilities") if isinstance(doc.get("capabilities"), list) else []
            if not capabilities:
                issues.append("capabilities must be non-empty")
            required_evidence = doc.get("required_evidence") if isinstance(doc.get("required_evidence"), list) else []
            evidence_ids = {
                str(item.get("id") or "")
                for item in required_evidence
                if isinstance(item, dict)
            }
            missing_base = sorted(BASE_CONTRACT_EVIDENCE_IDS - evidence_ids)
            if missing_base:
                issues.append(f"required_evidence missing base obligations: {', '.join(missing_base)}")
            observability = doc.get("observability") if isinstance(doc.get("observability"), dict) else {}
            observed = observability.get("required_rtl_observed")
            if not isinstance(observed, list) or not observed:
                issues.append("observability.required_rtl_observed must be non-empty")
        capabilities_count = len(doc.get("capabilities")) if isinstance(doc.get("capabilities"), list) else 0
        evidence_count = len(doc.get("required_evidence")) if isinstance(doc.get("required_evidence"), list) else 0
        self.add(
            "ip_contract",
            "fail" if issues else "pass",
            path,
            f"capabilities={capabilities_count} required_evidence={evidence_count}",
            issues,
        )

    def check_fl(self) -> None:
        path = self.ip_dir / "model" / "fl_model_check.json"
        doc, err = _read_json(path)
        issues = [err] if err else []
        if not issues and doc.get("passed") is not True:
            issues.append("fl_model_check.json passed must be true")
        self.add("fl_model", "fail" if issues else "pass", path, "FL artifact check passed=true", issues)

    def check_cl(self) -> None:
        path = self.ip_dir / "model" / "cl_model_check.json"
        doc, err = _read_json(path)
        issues = [err] if err else []
        self_check = doc.get("self_check") if isinstance(doc.get("self_check"), dict) else {}
        if not issues and doc.get("passed") is not True:
            issues.append("cl_model_check.json passed must be true")
        if not issues and self_check.get("passed") is not True:
            issues.append("cl_model_check.json self_check.passed must be true")
        self.add("cl_model", "fail" if issues else "pass", path, "CL self-check passed=true", issues)

    def check_equivalence_goals(self) -> None:
        path = self.ip_dir / "verify" / "equivalence_goals.json"
        doc, err = _read_json(path)
        issues = [err] if err else []
        goals = doc.get("goals") if isinstance(doc.get("goals"), list) else []
        blocked = [
            goal for goal in goals
            if isinstance(goal, dict) and (goal.get("blocked") is True or str(goal.get("status") or "").lower() == "blocked")
        ]
        if not issues and not goals:
            issues.append("equivalence_goals.json must contain goals[]")
        if blocked:
            issues.append(f"{len(blocked)} blocked equivalence goal(s)")
        self.add(
            "equivalence_goals",
            "fail" if issues else "pass",
            path,
            f"goals={len(goals)} blocked={len(blocked)}",
            issues,
        )

    def check_rtl_todo(self) -> None:
        path = self.ip_dir / "rtl" / "rtl_todo_plan.json"
        doc, err = _read_json(path)
        issues = [err] if err else []
        gate = doc.get("gate") if isinstance(doc.get("gate"), dict) else {}
        if not issues:
            if gate.get("status") != "pass":
                issues.append(f"rtl_todo gate status is {gate.get('status')!r}, expected pass")
            for key in ("blocking_questions", "orphan_tasks", "open_required_todos", "static_missing"):
                if _as_int(gate.get(key)) != 0:
                    issues.append(f"rtl_todo gate {key}={gate.get(key)}, expected 0")
            if gate.get("all_required_todos_pass") is not True:
                issues.append("rtl_todo gate all_required_todos_pass must be true")
        self.add("rtl_todo", "fail" if issues else "pass", path, "RTL todo/static audit gate", issues)

    def check_rtl_provenance(self) -> None:
        path = self.ip_dir / "rtl" / "rtl_authoring_provenance.json"
        todo_path = self.ip_dir / "rtl" / "rtl_todo_plan.json"
        doc, err = _read_json(path)
        issues = [err] if err else []
        if not issues:
            for key, expected in (
                ("type", "rtl_authoring_provenance"),
                ("agent", "common_ai_agent"),
                ("workflow", "rtl-gen"),
            ):
                if doc.get(key) != expected:
                    issues.append(f"{key} must be {expected}")
            if doc.get("surface") not in {"atlas_ui", "textual_ui", "headless_common_engine"}:
                issues.append("surface must be an approved common_ai_agent surface")
            rtl_files = doc.get("rtl_files") if isinstance(doc.get("rtl_files"), list) else []
            if not rtl_files:
                issues.append("rtl_files must be non-empty")
            if todo_path.is_file():
                expected_hashes = {_sha256_file(todo_path), _stable_json_sha256(todo_path)}
                if doc.get("todo_plan_sha256") not in expected_hashes:
                    issues.append("todo_plan_sha256 does not match current rtl_todo_plan.json")
            else:
                issues.append("missing rtl_todo_plan.json for provenance hash check")
        self.add("rtl_provenance", "fail" if issues else "pass", path, "RTL provenance matches current todo plan", issues)

    def check_compile(self) -> None:
        path = self.ip_dir / "rtl" / "rtl_compile.json"
        doc, err = _read_json(path)
        issues = [err] if err else []
        if not issues:
            if doc.get("passed") is not True:
                issues.append("rtl_compile passed must be true")
            if doc.get("dut_only") is not True:
                issues.append("rtl_compile dut_only must be true")
            for key in ("errors", "diagnostics", "style_violations"):
                if _as_int(doc.get(key)) != 0:
                    issues.append(f"rtl_compile {key}={doc.get(key)}, expected 0")
        self.add("rtl_compile", "fail" if issues else "pass", path, "DUT-only RTL compile is clean", issues)

    def check_lint(self) -> None:
        path = self.ip_dir / "lint" / "dut_lint.json"
        doc, err = _read_json(path)
        issues = [err] if err else []
        if not issues:
            if doc.get("passed") is not True:
                issues.append("dut_lint passed must be true")
            if doc.get("dut_only") is not True:
                issues.append("dut_lint dut_only must be true")
            for key in ("errors", "warnings", "suppression_violation_count", "style_violation_count", "waived_warnings"):
                if _as_int(doc.get(key)) != 0:
                    issues.append(f"dut_lint {key}={doc.get(key)}, expected 0")
        self.add("lint", "fail" if issues else "pass", path, "DUT-only lint is clean", issues)

    def check_tb_compile(self) -> None:
        path = self.ip_dir / "tb" / "cocotb" / "tb_py_compile.json"
        doc, err = _read_json(path)
        issues = [err] if err else []
        if not issues:
            if doc.get("passed") is not True:
                issues.append("tb_py_compile passed must be true")
            errors = doc.get("errors") if isinstance(doc.get("errors"), list) else []
            if errors:
                issues.append(f"tb_py_compile has {len(errors)} error(s)")
            files = doc.get("files") if isinstance(doc.get("files"), list) else []
            if not files:
                issues.append("tb_py_compile files must be non-empty")
        self.add("tb_python_compile", "fail" if issues else "pass", path, "TB Python compiled before simulation", issues)

    def check_sim(self) -> None:
        report = self.ip_dir / "sim" / "sim_report.txt"
        results = self.ip_dir / "sim" / "results.xml"
        issues: list[str] = []
        tests = failures = errors = 0
        if not report.is_file():
            issues.append(f"missing {report}")
        else:
            text = report.read_text(encoding="utf-8", errors="replace")
            if re.search(r"\bFAIL=[1-9][0-9]*\b", text):
                issues.append("sim_report.txt contains non-zero FAIL")
            if "TESTS=" not in text:
                issues.append("sim_report.txt missing TESTS summary")
        if not results.is_file():
            issues.append(f"missing {results}")
        else:
            try:
                root = ET.parse(results).getroot()
                cases = root.findall(".//testcase")
                tests = len(cases) or int(float(root.attrib.get("tests", 0) or 0))
                failures = sum(1 for case in cases if case.find("failure") is not None)
                errors = sum(1 for case in cases if case.find("error") is not None)
                if not cases:
                    failures = int(float(root.attrib.get("failures", 0) or 0))
                    errors = int(float(root.attrib.get("errors", 0) or 0))
            except Exception as exc:
                issues.append(f"cannot parse results.xml: {exc}")
        if not issues:
            if tests <= 0:
                issues.append("simulation must execute at least one test")
            if failures or errors:
                issues.append(f"simulation failures={failures} errors={errors}")
        self.add("simulation", "fail" if issues else "pass", results, f"tests={tests} failures={failures} errors={errors}", issues)

    def check_simulation_quality(self) -> None:
        path = self.ip_dir / "sim" / "simulation_quality.json"
        doc, err = _read_json(path)
        issues = [err] if err else []
        if not issues and doc.get("status") != "pass":
            raw_issues = doc.get("issues") if isinstance(doc.get("issues"), list) else []
            issue_text = [str(item) for item in raw_issues[:20]]
            issues.append(f"simulation_quality status is {doc.get('status')!r}, expected pass")
            issues.extend(issue_text)
        summary = doc.get("summary") if isinstance(doc.get("summary"), dict) else {}
        self.add(
            "simulation_quality",
            "fail" if issues else "pass",
            path,
            f"status={doc.get('status')} issues={summary.get('issues')}",
            issues,
        )

    def check_scoreboard(self) -> None:
        path = self.ip_dir / "sim" / "scoreboard_events.jsonl"
        goals_path = self.ip_dir / "verify" / "equivalence_goals.json"
        issues: list[str] = []
        rows = 0
        covered: set[str] = set()
        goal_observables, goal_issues = _scoreboard_goal_observables(goals_path)
        issues.extend(goal_issues)
        if not path.is_file():
            issues.append(f"missing {path}")
        else:
            for lineno, raw in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
                if not raw.strip():
                    continue
                rows += 1
                try:
                    row = json.loads(raw)
                except Exception as exc:
                    issues.append(f"line {lineno}: invalid JSON: {exc}")
                    continue
                if not isinstance(row, dict):
                    issues.append(f"line {lineno}: row must be object")
                    continue
                missing = sorted(REQUIRED_SCOREBOARD_KEYS - set(row))
                if missing:
                    issues.append(f"line {lineno}: missing keys {missing}")
                if row.get("passed") is not True:
                    issues.append(f"line {lineno}: passed must be true")
                fl_expected = row.get("fl_expected") if isinstance(row.get("fl_expected"), dict) else {}
                if not fl_expected.get("model_api"):
                    issues.append(f"line {lineno}: fl_expected.model_api missing")
                rtl_observed = row.get("rtl_observed")
                if not isinstance(rtl_observed, dict) or not rtl_observed:
                    issues.append(f"line {lineno}: rtl_observed must be non-empty object")
                gid = str(row.get("goal_id") or "").strip()
                if gid:
                    covered.add(gid)
                    if goal_observables and gid not in goal_observables:
                        issues.append(f"line {lineno}: unknown goal_id {gid}")
                    if isinstance(rtl_observed, dict):
                        missing_observables = sorted(goal_observables.get(gid, set()) - set(rtl_observed))
                        if missing_observables:
                            issues.append(
                                f"line {lineno}: rtl_observed missing expected observable(s) "
                                f"for {gid}: {', '.join(missing_observables)}"
                            )
        if rows <= 0:
            issues.append("scoreboard must contain at least one row")
        self.add("scoreboard", "fail" if issues else "pass", path, f"rows={rows} goals_with_rows={len(covered)}", issues[:20])

    def check_coverage(self) -> None:
        path = self.ip_dir / "cov" / "coverage.json"
        doc, err = _read_json(path)
        issues = [err] if err else []
        if not issues and doc.get("status") not in {"pass", "ok"}:
            issues.append(f"coverage status is {doc.get('status')!r}, expected pass")
        if not issues:
            limitations = doc.get("limitations") if isinstance(doc.get("limitations"), list) else []
            if limitations:
                issues.append(f"coverage limitations require review: {len(limitations)}")
        self.add("coverage", "fail" if issues else "pass", path, f"status={doc.get('status')}", issues)

    def check_truth_coverage(self) -> None:
        path = self.ip_dir / "signoff" / "truth_coverage.json"
        doc, err = _read_json(path)
        issues = [err] if err else []
        summary = doc.get("summary") if isinstance(doc.get("summary"), dict) else {}
        if not issues:
            if doc.get("type") != "truth_coverage":
                issues.append("type must be truth_coverage")
            if doc.get("status") != "pass":
                issues.append(f"truth_coverage status is {doc.get('status')!r}, expected pass")
            if _as_int(summary.get("uncovered_required")) != 0:
                issues.append(f"uncovered_required={summary.get('uncovered_required')}, expected 0")
            uncovered = doc.get("uncovered_required") if isinstance(doc.get("uncovered_required"), list) else []
            if uncovered:
                issues.append(f"uncovered_required list has {len(uncovered)} item(s)")
        self.add(
            "truth_coverage",
            "fail" if issues else "pass",
            path,
            f"status={doc.get('status')} uncovered_required={summary.get('uncovered_required')}",
            issues,
        )

    def check_mutation_guard(self) -> None:
        path = self.ip_dir / "mutation" / "mutation_report.json"
        if not path.is_file():
            self.add(
                "mutation_guard",
                "pass",
                path,
                "not run; advisory until a human approves an IP-class kill-rate policy",
                [],
            )
            return

        doc, err = _read_json(path)
        issues = [err] if err else []
        summary = doc.get("summary") if isinstance(doc.get("summary"), dict) else {}
        if not issues and doc.get("status") == "fail":
            issues.append("mutation_guard status=fail")
        self.add(
            "mutation_guard",
            "fail" if issues else "pass",
            path,
            f"status={doc.get('status')} kill_rate={summary.get('kill_rate')}",
            issues,
        )

    def check_verification_hardening(self) -> None:
        scenario_path = self.ip_dir / "sim" / "scenario_e2e_summary.json"
        monitor_path = self.ip_dir / "sim" / "monitor_evidence.json"
        survivor_path = self.ip_dir / "mutation" / "survivor_classification.json"
        formal_path = self.ip_dir / "verify" / "formal_status.json"
        safety_path = self.ip_dir / "verify" / "safety_properties.sva"
        artifact_paths = [scenario_path, monitor_path, survivor_path, formal_path, safety_path]
        if not any(path.is_file() for path in artifact_paths):
            self.add(
                "verification_hardening",
                "pass",
                "sim/scenario_e2e_summary.json + sim/monitor_evidence.json + mutation/survivor_classification.json + verify/formal_status.json",
                "not run; advisory until an IP emits verification-hardening artifacts",
                [],
            )
            return

        issues: list[str] = []

        scenario, err = _read_json(scenario_path)
        if err:
            issues.append(err)
        else:
            if scenario.get("status") != "pass":
                issues.append(f"scenario_e2e_summary status is {scenario.get('status')!r}, expected pass")
            if _as_int(scenario.get("total_directed_scenarios")) < 26:
                issues.append("scenario_e2e_summary must cover at least 26 directed scenarios")
            if scenario.get("missing_scenarios"):
                issues.append("scenario_e2e_summary has missing_scenarios")
            if scenario.get("failed_scenarios"):
                issues.append("scenario_e2e_summary has failed_scenarios")

        monitor, err = _read_json(monitor_path)
        if err:
            issues.append(err)
        else:
            checks = cast(dict[str, Any], monitor.get("checks") if isinstance(monitor.get("checks"), dict) else {})
            for key in (
                "sram_payload_no_holes",
                "sram_payload_only",
                "sram_no_header_or_pad_write",
                "axi_write_protocol_pass",
                "axi_read_protocol_pass",
                "apb_per_q_readback_pass",
            ):
                if checks.get(key) is not True:
                    issues.append(f"monitor_evidence.{key} must be true")
            if monitor.get("status") != "pass":
                issues.append(f"monitor_evidence status is {monitor.get('status')!r}, expected pass")

        survivor, err = _read_json(survivor_path)
        if err:
            issues.append(err)
        else:
            summary = cast(dict[str, Any], survivor.get("summary") if isinstance(survivor.get("summary"), dict) else {})
            if survivor.get("status") != "pass":
                issues.append(f"survivor_classification status is {survivor.get('status')!r}, expected pass")
            if _as_int(summary.get("classified")) != _as_int(summary.get("total_survivors")):
                issues.append("survivor_classification classified count must equal total_survivors")

        formal, err = _read_json(formal_path)
        if err:
            issues.append(err)
        else:
            if formal.get("status") not in {"pass", "optional_not_run"}:
                issues.append(f"formal_status status is {formal.get('status')!r}, expected pass or optional_not_run")
            properties = cast(list[Any], formal.get("properties") if isinstance(formal.get("properties"), list) else [])
            if len(properties) < 5:
                issues.append("formal_status must record at least five properties")
        if not safety_path.is_file():
            issues.append(f"missing {safety_path}")

        self.add(
            "verification_hardening",
            "fail" if issues else "pass",
            "sim/scenario_e2e_summary.json + sim/monitor_evidence.json + mutation/survivor_classification.json + verify/formal_status.json",
            "directed scenarios, protocol monitors, survivor classification, and optional formal artifacts present",
            issues,
        )

    def check_waivers(self) -> None:
        path = self.ip_dir / "signoff" / "goal_ledger.json"
        doc, err = _read_json(path)
        issues = [err] if err else []
        blockers: list[str] = []
        if not issues:
            human_review = doc.get("human_review_needed") if isinstance(doc.get("human_review_needed"), list) else []
            if human_review:
                blockers.append(f"human_review_needed has {len(human_review)} item(s)")
            waivers = doc.get("known_waivers") if isinstance(doc.get("known_waivers"), list) else []
            for idx, waiver in enumerate(waivers):
                if not isinstance(waiver, dict):
                    issues.append(f"known_waivers[{idx}] must be object")
                    continue
                for key in ("id", "reason", "source"):
                    if not str(waiver.get(key) or "").strip():
                        issues.append(f"known_waivers[{idx}] missing {key}")
                if self.require_human_waiver_approval and not str(waiver.get("approved_by") or "").strip():
                    blockers.append(f"known_waivers[{idx}] missing approved_by for production signoff")
        status = "fail" if issues else "blocked" if blockers else "pass"
        self.add("waivers", status, path, "waivers explicit and reviewable", [*issues, *blockers])

    def run(self) -> dict[str, Any]:
        if not self.ip_dir.is_dir():
            self.add("ip_dir", "fail", self.ip_dir, "IP directory exists", [f"missing {self.ip_dir}"])
        else:
            self.check_ssot()
            self.check_ip_contract()
            self.check_fl()
            self.check_cl()
            self.check_equivalence_goals()
            self.check_rtl_todo()
            self.check_rtl_provenance()
            self.check_compile()
            self.check_lint()
            self.check_tb_compile()
            self.check_sim()
            self.check_simulation_quality()
            self.check_scoreboard()
            self.check_coverage()
            self.check_truth_coverage()
            self.check_mutation_guard()
            self.check_verification_hardening()
            self.check_waivers()

        failing = [gate for gate in self.gates if gate.status == "fail"]
        blocked = [gate for gate in self.gates if gate.status == "blocked"]
        status = "fail" if failing else "blocked" if blocked else "pass"
        payload = {
            "schema_version": 1,
            "type": "ip_signoff",
            "generated_at": _utc(),
            "ip": self.ip,
            "status": status,
            "mode": "local_evidence",
            "contract": "IP_SIGNOFF.md",
            "ip_contract": self.rel(self.ip_dir / "verify" / "ip_contract.json"),
            "summary": {
                "total_gates": len(self.gates),
                "passed": sum(1 for gate in self.gates if gate.status == "pass"),
                "failed": len(failing),
                "blocked": len(blocked),
            },
            "gates": [
                {
                    "name": gate.name,
                    "status": gate.status,
                    "artifact": gate.artifact,
                    "summary": gate.summary,
                    "issues": gate.issues,
                }
                for gate in self.gates
            ],
        }
        return payload


def _write_markdown(path: Path, report: dict[str, Any]) -> None:
    lines = [
        f"# IP Signoff - {report['ip']}",
        "",
        f"- Status: `{report['status']}`",
        f"- Generated: `{report['generated_at']}`",
        f"- Contract: `{report['contract']}`",
        "",
        "| Gate | Status | Artifact | Summary |",
        "| --- | --- | --- | --- |",
    ]
    for gate in report["gates"]:
        lines.append(
            f"| `{gate['name']}` | `{gate['status']}` | `{gate['artifact']}` | {gate['summary']} |"
        )
    issue_lines = [
        f"- `{gate['name']}`: " + "; ".join(gate["issues"])
        for gate in report["gates"]
        if gate.get("issues")
    ]
    if issue_lines:
        lines += ["", "## Issues", "", *issue_lines]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ip")
    parser.add_argument("--root", default=".")
    parser.add_argument(
        "--require-human-waiver-approval",
        action="store_true",
        help="Block signoff when known waivers do not carry approved_by.",
    )
    args = parser.parse_args()

    checker = SignoffChecker(
        args.ip,
        Path(args.root),
        require_human_waiver_approval=args.require_human_waiver_approval,
    )
    report = checker.run()

    signoff_dir = checker.ip_dir / "signoff"
    signoff_dir.mkdir(parents=True, exist_ok=True)
    json_path = signoff_dir / "ip_signoff.json"
    md_path = signoff_dir / "ip_signoff.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    _write_markdown(md_path, report)

    print(f"[check_ip_signoff] status={report['status']} gates={report['summary']}")
    print(f"[check_ip_signoff] wrote {json_path}")
    print(f"[check_ip_signoff] wrote {md_path}")
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
