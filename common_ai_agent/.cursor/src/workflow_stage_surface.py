#!/usr/bin/env python3
"""UI-neutral adapter around the shared workflow stage engine.

The engine owns execution and disk-truth validation.  This module owns the
small amount of surface policy that every UI needs to agree on: session name,
workflow name, repair prompts, and human-gate signals.
"""

from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Literal

try:
    from src.workflow_lint_kpi import lint_kpi_dots
    from src.workflow_stage_engine import STAGE_WORKFLOW, WorkflowStageEngine, canonical_stage
except ModuleNotFoundError:  # pragma: no cover - direct script execution fallback
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from src.workflow_lint_kpi import lint_kpi_dots
    from src.workflow_stage_engine import STAGE_WORKFLOW, WorkflowStageEngine, canonical_stage


COMMON_ENGINE_STAGES = {
    "ssot-fl-model",
    "ssot-cycle-model",
    "ssot-dual-fcov",
    "ssot-equiv-goals",
    "ssot-rtl",
    "lint",
    "ssot-tb",
    "ssot-tb-cocotb",
    "coverage",
    "sim",
    "sim-debug",
    "goal-audit",
    "contract-check",
}


LLM_RTL_BLOCKERS = {
    "RTL_TODO_PLAN_MISSING",
    "DETERMINISTIC_RTL_ARTIFACT_NOT_APPROVED",
    "LLM_RTL_IMPLEMENTATION_REQUIRED",
    "COMMON_AI_AGENT_RTL_PROVENANCE_REQUIRED",
}

RTL_DRAFT_COMPATIBLE_BLOCKERS = LLM_RTL_BLOCKERS | {
    "RTL_TARGET_SCALE_POLICY",
}


def _is_llm_rtl_blocker(doc: Any) -> bool:
    if not isinstance(doc, dict):
        return False
    questions = doc.get("questions")
    if not isinstance(questions, list) or not questions:
        return False
    ids = {
        str(question.get("id") or "")
        for question in questions
        if isinstance(question, dict)
    }
    return bool(ids & LLM_RTL_BLOCKERS) and ids <= RTL_DRAFT_COMPATIBLE_BLOCKERS


@dataclass
class StageSurfaceResult:
    handled: bool
    alias: str
    workflow: str = ""
    session: str = ""
    message: str = ""
    status: str = ""
    queue_prompts: list[str] = field(default_factory=list)
    rtl_blocked: bool = False
    sim_human_gate_doc: dict[str, Any] | None = None
    keep_running: bool = False


def is_common_stage(alias: str) -> bool:
    return canonical_stage(alias) in COMMON_ENGINE_STAGES


def _rtl_authoring_summary(project_root: Path, ip: str) -> str:
    path = project_root / ip / "rtl" / "rtl_authoring_plan.json"
    try:
        plan = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return ""
    summary = plan.get("summary") if isinstance(plan.get("summary"), dict) else {}
    if not summary:
        return ""
    parts = []
    for key in (
        "packets",
        "module_packets",
        "sliced_module_packets",
        "required_tasks",
        "max_packet_required_tasks",
        "target_scale_present",
        "deferred_human_qa_allowed",
        "pass_allowed",
        "recommended_packet_batch_limit",
        "llm_actionable_packets",
        "llm_actionable_tasks",
        "human_locked_packets",
        "human_locked_tasks",
    ):
        if key in summary:
            parts.append(f"{key}={summary[key]}")
    next_packets = summary.get("next_llm_packets") if isinstance(summary.get("next_llm_packets"), list) else []
    if next_packets:
        parts.append("next_llm_packets=" + "|".join(str(item) for item in next_packets[:5]))
    reference_profile = plan.get("reference_profile") if isinstance(plan.get("reference_profile"), dict) else {}
    suggested = reference_profile.get("suggested_ssot_target_scale") if isinstance(reference_profile.get("suggested_ssot_target_scale"), dict) else {}
    if suggested and not bool(summary.get("target_scale_present")):
        parts.append("reference_target_scale_candidate=true")
    return ", ".join(parts)


def run_common_stage_surface(
    *,
    project_root: str | Path,
    source_root: str | Path | None,
    alias: str,
    ip: str,
    template: str = "",
    run_mode: str = "",
) -> StageSurfaceResult:
    """Run a common stage and return UI-neutral side-effect instructions."""
    engine_alias = canonical_stage(alias)
    if engine_alias not in COMMON_ENGINE_STAGES:
        return StageSurfaceResult(handled=False, alias=engine_alias)

    result = WorkflowStageEngine(project_root, source_root=source_root, run_mode=run_mode).run_stage(engine_alias, ip)
    workflow = STAGE_WORKFLOW.get(engine_alias, engine_alias)
    template = template or engine_alias
    surface = StageSurfaceResult(
        handled=True,
        alias=engine_alias,
        workflow=workflow,
        session=f"{ip}/{workflow}",
        message=result.message,
        status=result.status,
    )
    metadata = result.metadata if isinstance(result.metadata, dict) else {}
    project_root_path = Path(project_root)

    if engine_alias == "ssot-rtl" and _is_llm_rtl_blocker(metadata.get("rtl_blocked")):
        authoring_summary = _rtl_authoring_summary(project_root_path, ip)
        surface.queue_prompts = [
            "/mode normal",
            "/wf rtl-gen",
            "/clear",
            f"/todo template {template} {ip}",
            (
                f"Implement RTL for {ip} from yaml/{ip}.ssot.yaml and the dynamic "
                "RTL ledger stored at rtl/rtl_todo_plan.json. "
                "rtl/rtl_todo_tracker.json contains one visible TODO per SSOT ledger group (phase) "
                "followed by a final deterministic gen-rtl gate; the gate loops back to Phase 1 until "
                "the ledger closes. This ATLAS worker runs shell commands from "
                f"the active IP root, so do not prefix tool paths with {ip}/.\n"
                "Use rtl/rtl_authoring_plan.json and open packets under "
                "rtl/authoring_packets/ as the work queue; review "
                "rtl/rtl_authoring_status.md for a human-readable queue preview"
                f"{f' ({authoring_summary})' if authoring_summary else ''}. Process module packets first, "
                "then unowned tasks, then rtl_gate_closure inside this same gen-rtl loop. For sliced packets, merge into the same "
                "owner_file and preserve prior slice logic; start from next_llm_packets when listed "
                "and skip packets whose llm_actionable_open_count is zero.\n\n"
                "Write only RTL-owned "
                "artifacts, keep SSOT/function model/coverage/interface targets locked, write "
                "rtl/rtl_authoring_provenance.json with common_ai_agent rtl-gen provenance, then rerun "
                "/gen-rtl until the dynamic TODO gate, DUT-only compile, and DUT-only lint pass.\n\n"
                "Stage-engine evidence:\n```text\n"
                f"{result.message}\n"
                "```"
            ),
        ]
        surface.keep_running = True
        return surface

    if engine_alias == "ssot-rtl" and metadata.get("rtl_blocked"):
        surface.rtl_blocked = True
        surface.keep_running = True
        return surface

    if engine_alias == "ssot-rtl" and metadata.get("needs_repair"):
        authoring_summary = _rtl_authoring_summary(project_root_path, ip)
        surface.queue_prompts = [
            "/mode normal",
            "/wf rtl-gen",
            "/clear",
            f"/todo template {template} {ip}",
            (
                f"Repair generated RTL for {ip} from yaml/{ip}.ssot.yaml using the "
                "common stage-engine evidence below. Repair only RTL-owned artifacts; do not "
                "change SSOT semantics and do not use fixed IP templates. Use "
                "rtl/rtl_authoring_plan.json and open packets under rtl/authoring_packets/"
                "; review rtl/rtl_authoring_status.md for the current queue preview"
                f"{f' ({authoring_summary})' if authoring_summary else ''}; merge sliced packet repairs into "
                "existing owner files instead of replacing earlier packet logic; do not prefix tool paths "
                f"with {ip}/ because shell commands run from the active IP root; start from next_llm_packets "
                "when listed and skip packets whose llm_actionable_open_count is zero. Rerun DUT-only compile "
                "and lint through the common engine before reporting DONE.\n\n"
                "Stage-engine evidence:\n```text\n"
                f"{result.message}\n"
                "```"
            ),
        ]
        surface.keep_running = True
        return surface

    if engine_alias == "ssot-tb-cocotb" and metadata.get("needs_repair"):
        surface.queue_prompts = [
            "/mode normal",
            "/wf tb-gen",
            "/clear",
            f"/todo template {template} {ip}",
            (
                f"Repair generated pyuvm/cocotb TB for {ip} using SSOT, FunctionalModel, "
                "equivalence_goals.json, rtl_contract.json, and tb/tb_todo_plan.json as the "
                "contract/evidence ledger. Do not use fixed IP templates. Preserve "
                "EquivalenceScoreboard, rerun derive_tb_todos.py --audit-tb, and rerun the "
                "common TB stage before reporting DONE.\n\n"
                "Stage-engine evidence:\n```text\n"
                f"{result.message}\n"
                "```"
            ),
        ]
        surface.keep_running = True
        return surface

    if engine_alias == "sim-debug" and isinstance(metadata.get("mismatch_classification"), dict):
        surface.sim_human_gate_doc = metadata["mismatch_classification"]
        surface.keep_running = True

    return surface


_KPI_DOT = Literal["pass", "warn", "fail", "idle"]


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _dot(condition: bool | None, *, missing_is: _KPI_DOT = "idle") -> _KPI_DOT:
    if condition is None:
        return missing_is
    return "pass" if condition else "fail"


def _kpi_ssot(ip_dir: Path, ip: str) -> List[_KPI_DOT]:
    path = ip_dir / "yaml" / f"{ip}.ssot.yaml"
    if not path.is_file():
        return ["idle"] * 5
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return ["idle"] * 5
    lines = text.splitlines()
    section_count = sum(1 for ln in lines if ln.startswith("  - name:") or ln.startswith("- name:"))
    tbd_count = sum(1 for ln in lines if "TBD" in ln)
    has_isa = any("isa" in ln.lower() for ln in lines)
    has_reg = any("register" in ln.lower() or "regfile" in ln.lower() for ln in lines)
    return [
        "pass" if section_count > 0 else "warn",   # section_count
        "warn",                                      # qa_resolved (no qa artifact here, conservative)
        "pass" if tbd_count == 0 else "fail",        # tbd=0
        "pass" if has_isa else "idle",               # isa_spec
        "pass" if has_reg else "idle",               # register_file
    ]


def _kpi_fl_model(ip_dir: Path) -> List[_KPI_DOT]:
    chk = _read_json(ip_dir / "model" / "fl_model_check.json")
    fcov = _read_json(ip_dir / "cov" / "fcov_plan.json")
    if chk is None and fcov is None:
        return ["idle"] * 4
    emit_passed: _KPI_DOT = "pass" if (chk or {}).get("emit_passed") else ("warn" if chk is None else "fail")
    self_chk: _KPI_DOT = "pass" if (chk or {}).get("self_check", {}).get("passed") else ("idle" if chk is None else "warn")
    fcov_plan: _KPI_DOT = "pass" if fcov is not None else "idle"
    manifest_ok: _KPI_DOT = "pass" if (chk or {}).get("manifest_ok") else ("idle" if chk is None else "warn")
    return [emit_passed, self_chk, fcov_plan, manifest_ok]


def _kpi_cl_model(ip_dir: Path) -> List[_KPI_DOT]:
    chk = _read_json(ip_dir / "model" / "cl_model_check.json")
    if chk is None:
        return ["idle"] * 3
    emit_passed: _KPI_DOT = "pass" if chk.get("emit_passed") else "fail"
    _cl_sc = chk.get("cl_self_check")
    _cl_sc_ok = _cl_sc.get("passed") if isinstance(_cl_sc, dict) else bool(_cl_sc)
    cl_self_chk: _KPI_DOT = "pass" if _cl_sc_ok else "warn"
    cycle_cov: _KPI_DOT = "pass" if chk.get("cycle_cov_plan") else "idle"
    return [emit_passed, cl_self_chk, cycle_cov]


def _kpi_equivalence(ip_dir: Path) -> List[_KPI_DOT]:
    doc = _read_json(ip_dir / "verify" / "equivalence_goals.json")
    if doc is None:
        return ["idle"] * 3
    parses: _KPI_DOT = "pass"
    goals_resolved: _KPI_DOT = "pass" if doc.get("goals_resolved") else "warn"
    sub_refs: _KPI_DOT = "pass" if doc.get("sub_module_refs") else "idle"
    return [parses, goals_resolved, sub_refs]


def _kpi_rtl(ip_dir: Path) -> List[_KPI_DOT]:
    compile_doc = _read_json(ip_dir / "rtl" / "rtl_compile.json")
    lint_doc = _read_json(ip_dir / "lint" / "dut_lint.json")
    todo_doc = _read_json(ip_dir / "rtl" / "rtl_todo_plan.json")
    prov_path = ip_dir / "rtl" / "rtl_authoring_provenance.json"
    if compile_doc is None and lint_doc is None and todo_doc is None and not prov_path.is_file():
        return ["idle"] * 4
    compile_rc: _KPI_DOT
    if compile_doc is None:
        compile_rc = "idle"
    else:
        rc = compile_doc.get("rc", compile_doc.get("return_code", compile_doc.get("returncode", 1)))
        compile_rc = "pass" if rc == 0 else "fail"
    lint_clean: _KPI_DOT
    if lint_doc is None:
        lint_clean = "idle"
    else:
        errs = lint_doc.get("errors", lint_doc.get("error_count", 1))
        lint_clean = "pass" if errs == 0 else "fail"
    todo_audit: _KPI_DOT
    if todo_doc is None:
        todo_audit = "idle"
    else:
        todo_audit = "pass" if todo_doc.get("status") == "pass" else "warn"
    provenance: _KPI_DOT = "pass" if prov_path.is_file() else "fail"
    return [compile_rc, lint_clean, todo_audit, provenance]


def _kpi_lint(ip_dir: Path) -> List[_KPI_DOT]:
    return lint_kpi_dots(ip_dir)


def _kpi_tb(ip_dir: Path) -> List[_KPI_DOT]:
    tb_dir = ip_dir / "tb" / "cocotb"
    if not tb_dir.is_dir():
        tb_dir = ip_dir / "tb"
    todo_doc = _read_json(ip_dir / "tb" / "tb_todo_plan.json")
    if not tb_dir.is_dir() and todo_doc is None:
        return ["idle"] * 4
    py_files = list(tb_dir.rglob("*.py")) if tb_dir.is_dir() else []
    top_present: _KPI_DOT = "pass" if py_files else "fail"
    has_scoreboard = any("scoreboard" in f.name.lower() for f in py_files)
    scoreboard: _KPI_DOT = "pass" if has_scoreboard else "warn"
    if todo_doc is None:
        tc_count: _KPI_DOT = "pass" if len(py_files) >= 2 else "warn"
    else:
        gate = todo_doc.get("gate") if isinstance(todo_doc.get("gate"), dict) else {}
        tc_count = "pass" if gate.get("status") == "pass" else "warn"
    manifest_files = list(tb_dir.rglob("Makefile")) + list(tb_dir.rglob("*.yaml")) + list(tb_dir.rglob("*.json"))
    manifest: _KPI_DOT = "pass" if manifest_files or todo_doc is not None else "warn"
    return [top_present, scoreboard, tc_count, manifest]


def _count_metric(value: object, default: int = -1) -> int:
    """Normalize count-like JSON fields used by generated reports.

    Older reports store `mismatches` as an integer. Newer scoreboard output may
    store it as a list of mismatch rows. KPI rendering must be tolerant because
    the Pipeline screen polls this path continuously.
    """
    if value is None:
        return default
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, list):
        return len(value)
    if isinstance(value, dict):
        for key in ("count", "total", "mismatch_count", "num_mismatches"):
            if key in value:
                return _count_metric(value.get(key), default=default)
        return len(value)
    try:
        return int(str(value).strip())
    except Exception:
        return default


def _junit_counts(results_xml: Path) -> tuple[int, int, int]:
    root = ET.parse(str(results_xml)).getroot()
    suite_nodes = [node for node in root.iter() if node.tag.endswith("testsuite")]
    if root.tag.endswith("testsuite"):
        suite_nodes = [root]

    tests = failures = errors = 0
    for node in suite_nodes:
        tests += int(float(node.get("tests", 0) or 0))
        failures += int(float(node.get("failures", 0) or 0))
        errors += int(float(node.get("errors", 0) or 0))

    if tests == 0:
        tests = int(float(root.get("tests", 0) or 0))
    if failures == 0:
        failures = int(float(root.get("failures", 0) or 0))
    if errors == 0:
        errors = int(float(root.get("errors", 0) or 0))

    cases = [node for node in root.iter() if node.tag.endswith("testcase")]
    if tests == 0 and cases:
        tests = len(cases)
    if failures == 0 and cases:
        failures = sum(
            1 for case in cases
            if any(child.tag.endswith("failure") for child in list(case))
        )
    if errors == 0 and cases:
        errors = sum(
            1 for case in cases
            if any(child.tag.endswith("error") for child in list(case))
        )
    return tests, failures, errors


def _kpi_sim(ip_dir: Path) -> List[_KPI_DOT]:
    results_xml = ip_dir / "sim" / "results.xml"
    if not results_xml.is_file():
        results_xml = ip_dir / "tb" / "cocotb" / "results.xml"
    compare_doc = _read_json(ip_dir / "sim" / "fl_rtl_compare.json")
    if not results_xml.is_file() and compare_doc is None:
        return ["idle"] * 4
    xml_pass: _KPI_DOT = "idle"
    if results_xml.is_file():
        try:
            _tests, failures, errors = _junit_counts(results_xml)
            failures += errors
            xml_pass = "pass" if failures == 0 else "fail"
        except Exception:
            xml_pass = "warn"
    mismatches: _KPI_DOT = "idle"
    if compare_doc is not None:
        mm = _count_metric(
            compare_doc.get("mismatch_count", compare_doc.get("mismatches")),
            default=-1,
        )
        mismatches = "pass" if mm == 0 else ("fail" if mm > 0 else "warn")
    vcd_files = list((ip_dir / "sim").rglob("*.vcd")) if (ip_dir / "sim").is_dir() else []
    vcd_present: _KPI_DOT = "pass" if vcd_files else "idle"
    seed_cov: _KPI_DOT = "pass" if compare_doc and compare_doc.get("seed_coverage") else "idle"
    return [xml_pass, mismatches, vcd_present, seed_cov]


def _kpi_coverage(ip_dir: Path) -> List[_KPI_DOT]:
    doc = _read_json(ip_dir / "cov" / "coverage.json")
    if doc is None:
        return ["idle"] * 4
    bins_hit = doc.get("bins_hit", 0)
    bins_total = doc.get("bins_total", doc.get("total_bins", 0))
    bins_dot: _KPI_DOT = "pass" if bins_total > 0 and bins_hit >= bins_total else ("warn" if bins_total > 0 else "idle")
    cycle_cov: _KPI_DOT = "pass" if doc.get("cycle_coverage") else "warn"
    func_cov: _KPI_DOT = "pass" if doc.get("functional_coverage") else "warn"
    uncov = doc.get("uncovered_count", doc.get("uncov_count", -1))
    uncov_dot: _KPI_DOT = "pass" if uncov == 0 else ("warn" if uncov > 0 else "idle")
    return [bins_dot, cycle_cov, func_cov, uncov_dot]


def _kpi_sim_debug(ip_dir: Path) -> List[_KPI_DOT]:
    doc = _read_json(ip_dir / "sim" / "mismatch_classification.json")
    if doc is None:
        return ["idle"] * 3
    class_present: _KPI_DOT = "pass"
    owner_routed: _KPI_DOT = "pass" if doc.get("owner_workflow") else "warn"
    feedback: _KPI_DOT = "pass" if doc.get("feedback_packet") else "warn"
    return [class_present, owner_routed, feedback]


def _kpi_goal_audit(ip_dir: Path) -> List[_KPI_DOT]:
    doc = _read_json(ip_dir / "sim" / "fl_rtl_goal_audit.json")
    if doc is None:
        return ["idle"] * 3
    failed = doc.get("failed_checks", doc.get("failed_check_count", -1))
    blockers = doc.get("blockers", doc.get("blocker_count", -1))
    status = doc.get("status", "")
    failed_dot: _KPI_DOT = "pass" if failed == 0 else ("fail" if failed > 0 else "warn")
    blockers_dot: _KPI_DOT = "pass" if blockers == 0 else ("fail" if blockers > 0 else "warn")
    status_dot: _KPI_DOT = "pass" if status == "pass" else ("fail" if status == "fail" else "warn")
    return [failed_dot, blockers_dot, status_dot]


def _kpi_signoff(ip_dir: Path, stage: str) -> List[_KPI_DOT]:
    stage_dirs = {
        "syn": "syn/out",
        "sta": "sta/out",
        "pnr": "pnr/out",
        "sta-post": "sta-post/out",
    }
    rel = stage_dirs.get(stage)
    if rel is None:
        return ["idle"] * 5
    out_dir = ip_dir / rel
    if not out_dir.is_dir():
        return ["idle"] * 5
    report_files = list(out_dir.glob("*.json")) + list(out_dir.glob("*.md"))
    if not report_files:
        return ["idle"] * 5
    doc: dict[str, Any] = {}
    for f in report_files:
        if f.suffix == ".json":
            d = _read_json(f)
            if isinstance(d, dict):
                doc.update(d)
    tool_rc: _KPI_DOT = "pass" if doc.get("rc", doc.get("return_code", 0)) == 0 else "fail"
    area: _KPI_DOT = "pass" if doc.get("area") else "idle"
    slack = doc.get("timing_slack", doc.get("wns"))
    timing: _KPI_DOT = "pass" if isinstance(slack, (int, float)) and slack >= 0 else ("fail" if isinstance(slack, (int, float)) else "idle")
    fanout: _KPI_DOT = "pass" if doc.get("fanout") else "idle"
    power: _KPI_DOT = "pass" if doc.get("power") else "idle"
    return [tool_rc, area, timing, fanout, power]


_SIGNOFF_STAGES = {"syn", "sta", "pnr", "sta-post"}


def compute_kpi_dots(
    ip: str,
    stage: str,
    *,
    root: Path | None = None,
) -> List[Literal["pass", "warn", "fail", "idle"]]:
    if root is None:
        root = Path(__file__).resolve().parents[1]
    ip_dir = root / ip
    if not ip_dir.is_dir():
        return ["idle"] * 5

    dots: List[_KPI_DOT]
    if stage in ("ssot", "ssot-gen"):
        dots = _kpi_ssot(ip_dir, ip)
    elif stage in ("fl-model", "fl-model-gen"):
        dots = _kpi_fl_model(ip_dir)
    elif stage in ("cl-model", "cl-model-gen"):
        dots = _kpi_cl_model(ip_dir)
    elif stage in ("equivalence", "equiv-goals"):
        dots = _kpi_equivalence(ip_dir)
    elif stage in ("rtl", "rtl-gen"):
        dots = _kpi_rtl(ip_dir)
    elif stage == "lint":
        dots = _kpi_lint(ip_dir)
    elif stage in ("tb", "tb-gen"):
        dots = _kpi_tb(ip_dir)
    elif stage == "sim":
        dots = _kpi_sim(ip_dir)
    elif stage == "coverage":
        dots = _kpi_coverage(ip_dir)
    elif stage == "sim-debug":
        dots = _kpi_sim_debug(ip_dir)
    elif stage == "goal-audit":
        dots = _kpi_goal_audit(ip_dir)
    elif stage in _SIGNOFF_STAGES:
        dots = _kpi_signoff(ip_dir, stage)
    else:
        dots = ["idle"] * 5

    return dots[:5]


# Per-stage KPI dot labels and evidence path hints. Index aligns with the
# corresponding _kpi_*() helper output above; lengths must match.
_KPI_LABELS: dict[str, list[str]] = {
    "ssot": ["sections", "qa resolved", "tbd=0", "isa_spec", "register_file"],
    "fl-model": ["emit_passed", "self_check", "fcov_plan", "manifest_ok"],
    "cl-model": ["emit_passed", "cl_self_check", "cycle_cov_plan"],
    "equivalence": ["parses", "goals_resolved", "sub_module_refs"],
    "rtl": ["compile_rc", "lint_clean", "todo_audit", "provenance"],
    "lint": ["pyslang", "verilator", "errors=0", "warnings<=waivers", "policy"],
    "tb": ["top_present", "scoreboard", "todo_audit", "manifest"],
    "sim": ["results.xml", "mismatches=0", "vcd_present", "seed_coverage"],
    "coverage": ["bins_hit", "cycle_cov", "func_cov", "uncov_count"],
    "sim-debug": ["classification", "owner_routed", "feedback_packet"],
    "goal-audit": ["failed_checks=0", "blockers=0", "status=pass"],
    "syn": ["tool_rc", "area", "timing_slack", "fanout", "power"],
    "sta": ["tool_rc", "area", "timing_slack", "fanout", "power"],
    "pnr": ["tool_rc", "area", "timing_slack", "fanout", "power"],
    "sta-post": ["tool_rc", "area", "timing_slack", "fanout", "power"],
}

_KPI_EVIDENCE: dict[str, list[str]] = {
    "ssot": ["yaml/{ip}.ssot.yaml"] * 5,
    "fl-model": [
        "model/fl_model_check.json", "model/fl_model_check.json",
        "cov/fcov_plan.json", "model/fl_model_check.json",
    ],
    "cl-model": ["model/cl_model_check.json"] * 3,
    "equivalence": ["verify/equivalence_goals.json"] * 3,
    "rtl": [
        "rtl/rtl_compile.json", "lint/dut_lint.json",
        "rtl/rtl_todo_plan.json", "rtl/rtl_authoring_provenance.json",
    ],
    "lint": ["lint/dut_lint.json"] * 5,
    "tb": ["tb/cocotb/", "tb/cocotb/", "tb/tb_todo_plan.json", "tb/tb_todo_plan.json"],
    "sim": [
        "sim/results.xml", "sim/fl_rtl_compare.json",
        "sim/", "sim/fl_rtl_compare.json",
    ],
    "coverage": ["cov/coverage.json"] * 4,
    "sim-debug": ["sim/mismatch_classification.json"] * 3,
    "goal-audit": ["sim/fl_rtl_goal_audit.json"] * 3,
    "syn": ["syn/out/"] * 5,
    "sta": ["sta/out/"] * 5,
    "pnr": ["pnr/out/"] * 5,
    "sta-post": ["sta-post/out/"] * 5,
}


_STAGE_ALIASES_FOR_LABELS = {
    "ssot-gen": "ssot",
    "fl-model-gen": "fl-model",
    "cl-model-gen": "cl-model",
    "equiv-goals": "equivalence",
    "rtl-gen": "rtl",
    "tb-gen": "tb",
}


def compute_kpi_dots_labeled(
    ip: str,
    stage: str,
    *,
    root: Path | None = None,
) -> list[dict[str, str]]:
    """Same dots as compute_kpi_dots(), each paired with a human label and
    an evidence file path hint. Returns up to 5 entries:
        [{"state": "pass", "label": "compile_rc", "evidence_path": "rtl/rtl_compile.json"}, ...]
    """
    canonical = _STAGE_ALIASES_FOR_LABELS.get(stage, stage)
    states = compute_kpi_dots(ip, stage, root=root)
    labels = _KPI_LABELS.get(canonical, [f"kpi {i+1}" for i in range(len(states))])
    evidence = _KPI_EVIDENCE.get(canonical, [""] * len(states))
    out: list[dict[str, str]] = []
    n = min(len(states), len(labels), len(evidence), 5)
    for i in range(n):
        out.append({
            "state": states[i],
            "label": labels[i].format(ip=ip),
            "evidence_path": evidence[i].format(ip=ip),
        })
    # Append remaining states (if helper returned more than labels) with
    # generic labels — keeps shape consistent.
    for i in range(n, min(len(states), 5)):
        out.append({"state": states[i], "label": f"kpi {i+1}", "evidence_path": ""})
    return out
