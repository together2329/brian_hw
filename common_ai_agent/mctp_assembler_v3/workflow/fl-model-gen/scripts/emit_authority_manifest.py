#!/usr/bin/env python3
"""Emit per-IP Human-LLM authority manifest (9 gates, 9 loops, 6 rules).

Materializes the Human-vs-LLM authority principle as a machine-readable
authority.json and human-readable authority.md under <root>/<ip>/governance/.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml


# ---------------------------------------------------------------------------
# Static authority data (verbatim — do not paraphrase)
# ---------------------------------------------------------------------------

_PRINCIPLE = (
    "Human = 정답/목표/판단 기준 확정. LLM = 그 기준에 수렴하도록 생성·실행·수정 loop 수행."
)

_OPERATING_RULES: list[dict[str, str]] = [
    {"id": "R1", "rule": "LLM은 RTL을 고칠 수 있다", "scope": "rtl/, tb/, vectors/"},
    {"id": "R2", "rule": "LLM은 test를 추가할 수 있다", "scope": "tb/, sim/"},
    {"id": "R3", "rule": "LLM은 coverage gap을 채울 수 있다", "scope": "tb stimulus, vectors/"},
    {
        "id": "R4",
        "rule": "LLM은 spec/FL/coverage/perf target을 바꾸려면 change request 필수",
        "scope": "yaml/, model/, cov/",
    },
    {
        "id": "R5",
        "rule": "사람 승인 전에는 golden artifact 변경 금지",
        "scope": "model/functional_model.py, model/cycle_model.py, cov/fl_fcov_plan.json, cov/cl_fcov_plan.json",
    },
    {
        "id": "R6",
        "rule": "PASS의 의미는 항상 locked truth 기준으로만 판단",
        "scope": "all evidence rooted in SSOT + FL",
    },
]

_LLM_LOOPS: list[dict[str, str]] = [
    {
        "id": "L1",
        "title": "RTL correctness loop",
        "evidence_point": "FL expected vs RTL actual diff",
        "llm_action": "Patch RTL and rerun cocotb",
        "owner_on_fail": "rtl",
        "validator_path": "{ip}/sim/scoreboard_events.jsonl",
        "linked_goals": "EQ_TRANSACTION_*",
    },
    {
        "id": "L2",
        "title": "Module-level loop",
        "evidence_point": "scope.level=module equivalence diff at module boundary",
        "llm_action": "Patch only the owning RTL module",
        "owner_on_fail": "rtl",
        "validator_path": "{ip}/sim/module_scoreboard_*.jsonl",
        "linked_goals": "EQ_MODULE_*",
    },
    {
        "id": "L3",
        "title": "Coverage closure loop",
        "evidence_point": "coverage goals vs hit bins",
        "llm_action": "Add stimulus/tests; never weaken coverage goals",
        "owner_on_fail": "tb",
        "validator_path": "{ip}/cov/coverage.json",
        "linked_goals": "EQ_COVERAGE_*",
    },
    {
        "id": "L4",
        "title": "Lint/compile loop",
        "evidence_point": "DUT-only lint/compile diagnostics",
        "llm_action": "Patch RTL syntax/width/driver/style",
        "owner_on_fail": "rtl",
        "validator_path": "{ip}/lint/dut_lint.json",
        "linked_goals": "lint_compile criterion",
    },
    {
        "id": "L5",
        "title": "Assertion/protocol loop",
        "evidence_point": "SSOT interface/cycle assertion failure",
        "llm_action": "Patch RTL or TB monitor depending on classified owner",
        "owner_on_fail": "rtl|tb",
        "validator_path": "{ip}/sim/assertion_failures.jsonl",
        "linked_goals": "EQ_PROTOCOL_*, EQ_TIMING_*",
    },
    {
        "id": "L6",
        "title": "CL performance loop",
        "evidence_point": "cycle_model performance target vs measured latency/throughput",
        "llm_action": "Run parameter/architecture sweeps and propose tradeoff candidates",
        "owner_on_fail": "rtl|architect",
        "validator_path": "{ip}/reports/perf_sweep.json",
        "linked_goals": "EQ_TIMING_*, performance_cycle criterion",
    },
    {
        "id": "L7",
        "title": "PPA loop (Synthesis / DFT / PnR / STA / Power / Area)",
        "evidence_point": "synthesis/dft/pnr/sta/power reports vs PPA budget",
        "llm_action": "Propose RTL/architecture improvements per sub-stage; final acceptance is human",
        "owner_on_fail": "architect|human",
        "validator_path": "{ip}/reports/ppa_sweep.json",
        "sub_stages": [
            {"stage": "synthesis", "evidence": "{ip}/reports/synth/qor.json", "metrics": ["WNS","TNS","cell_area","register_count","est_power"]},
            {"stage": "dft",        "evidence": "{ip}/reports/dft/atpg.json", "metrics": ["fault_coverage","pattern_count","scan_chains","scan_shift_power","dft_area_overhead"]},
            {"stage": "pnr",        "evidence": "{ip}/reports/pnr/route.json", "metrics": ["post_route_WNS","clock_skew","wirelength","cell_density","congestion_overflow","ir_drop_risk"]},
            {"stage": "sta",        "evidence": "{ip}/reports/sta/timing.json", "metrics": ["setup_slack","hold_slack","fmax_mhz"]},
            {"stage": "power",      "evidence": "{ip}/reports/power/power.json", "metrics": ["dynamic_mw","leakage_mw","toggle_hotspot"]},
            {"stage": "area",       "evidence": "{ip}/reports/pnr/area.json", "metrics": ["total_um2","utilization_pct","macro_area"]},
        ],
        "feedback": "CL predicted vs measured: latency_ns=cycles*period; throughput=tx/cycle*Fmax; energy/op=power/ops; area_efficiency=throughput/area",
        "linked_goals": "EQ_PPA_*",
    },
    {
        "id": "L8",
        "title": "Regression minimization loop",
        "evidence_point": "Large failing test → minimal reproducer that still fails",
        "llm_action": "Bisect/shrink stimulus until a minimal vector reproduces the same failure; then patch RTL or escalate",
        "owner_on_fail": "tb|rtl",
        "validator_path": "{ip}/sim/min_repro_*.jsonl",
        "linked_goals": "any failing EQ_* goal",
    },
    {
        "id": "L9",
        "title": "Report / root-cause loop",
        "evidence_point": "Diff/log/coverage-miss/waveform evidence",
        "llm_action": "Synthesize fail_analysis.md with expected vs actual, likely cause, and suggested RTL patch — never modify FL/spec/coverage to make tests pass",
        "owner_on_fail": "tb|rtl|architect",
        "validator_path": "{ip}/reports/fail_analysis.md",
        "linked_goals": "any failing EQ_* goal",
    },
]

_REPO_LAYOUT: dict[str, list[str]] = {
    "locked": [
        "yaml/",
        "model/",
        "cov/fl_fcov_plan.json",
        "cov/cl_fcov_plan.json",
        "verify/equivalence_goals.json",
    ],
    "llm_editable": ["rtl/", "tb/", "sim/", "vectors/", "assertions/", "reports/"],
    "agent_runnable_validators": [
        "lint/",
        "sim/",
        "cov/coverage.json",
        "reports/ppa_sweep.json",
    ],
}


# ---------------------------------------------------------------------------
# SSOT / artifact helpers
# ---------------------------------------------------------------------------


def _load_ssot(ip_dir: Path, ip: str) -> dict[str, Any] | None:
    path = ip_dir / "yaml" / f"{ip}.ssot.yaml"
    if not path.is_file():
        return None
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _load_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return doc if isinstance(doc, dict) else None


def _dir_non_empty(path: Path) -> bool:
    return path.is_dir() and any(True for _ in path.iterdir())


# ---------------------------------------------------------------------------
# Gate status detection
# ---------------------------------------------------------------------------


def _detect_gate_status(ip: str, ip_dir: Path, ssot: dict[str, Any] | None) -> list[dict[str, Any]]:
    gates: list[dict[str, Any]] = []

    # G1 Requirement
    req_dir = ip_dir / "req"
    g1_status = "approved" if _dir_non_empty(req_dir) else "pending"
    gates.append({
        "id": "G1",
        "title": "Requirement 승인",
        "status": g1_status,
        "evidence_required": [f"{ip}/req/* exists, human-signed"],
        "locked_artifacts": [f"{ip}/req/"],
    })

    # G2 Spec
    if ssot is not None:
        g2_status = "approved"
    else:
        g2_status = "blocked"
    gates.append({
        "id": "G2",
        "title": "Spec 승인",
        "status": g2_status,
        "evidence_required": [f"{ip}/yaml/{ip}.ssot.yaml exists, all 20 sections complete"],
        "locked_artifacts": [f"{ip}/yaml/{ip}.ssot.yaml"],
    })

    # G3 Interface
    io_list = ssot.get("io_list", {}) if ssot else {}
    io_non_empty = bool(io_list) and (
        (isinstance(io_list, dict) and any(v for v in io_list.values()))
        or (isinstance(io_list, list) and len(io_list) > 0)
    )
    g3_status = "approved" if io_non_empty else "pending"
    gates.append({
        "id": "G3",
        "title": "Interface 승인",
        "status": g3_status,
        "evidence_required": ["io_list section non-empty", "interface contract approved"],
        "locked_artifacts": [f"{ip}/yaml/{ip}.ssot.yaml#io_list"],
    })

    # G4 FL golden
    fm_py = ip_dir / "model" / "functional_model.py"
    fl_check = _load_json(ip_dir / "model" / "fl_model_check.json")
    sig = ip_dir / "model" / "model_signature.json"
    if fm_py.is_file() and fl_check is not None and fl_check.get("passed") is True and sig.is_file():
        g4_status = "approved"
    elif fm_py.is_file() or fl_check is not None:
        g4_status = "pending"
    else:
        g4_status = "blocked"
    gates.append({
        "id": "G4",
        "title": "FL golden model 승인",
        "status": g4_status,
        "evidence_required": [
            f"{ip}/model/functional_model.py exists",
            f"{ip}/model/fl_model_check.json passed=true",
            f"{ip}/model/model_signature.json fresh",
        ],
        "locked_artifacts": [
            f"{ip}/model/functional_model.py",
            f"{ip}/model/model_signature.json",
        ],
    })

    # G5 Coverage
    fl_fcov = _load_json(ip_dir / "cov" / "fl_fcov_plan.json")
    cl_fcov_path = ip_dir / "cov" / "cl_fcov_plan.json"
    # Determine if CL is required: cycle_model section in SSOT is non-empty
    cl_required = False
    if ssot:
        cm = ssot.get("cycle_model", {})
        cl_required = isinstance(cm, dict) and bool(cm)
    fl_ok = fl_fcov is not None and fl_fcov.get("planned_before_rtl") is True
    cl_ok = cl_fcov_path.is_file() if cl_required else True
    g5_status = "approved" if fl_ok and cl_ok else "pending"
    gates.append({
        "id": "G5",
        "title": "Coverage goal 승인",
        "status": g5_status,
        "evidence_required": [
            f"{ip}/cov/fl_fcov_plan.json exists with planned_before_rtl=true",
            f"{ip}/cov/cl_fcov_plan.json exists when CL is required",
        ],
        "locked_artifacts": [
            f"{ip}/cov/fl_fcov_plan.json",
            f"{ip}/cov/cl_fcov_plan.json",
            f"{ip}/cov/fcov_plan.json",
        ],
    })

    # G6 CL/performance target
    cm_section = ssot.get("cycle_model", {}) if ssot else {}
    cm_non_empty = isinstance(cm_section, dict) and bool(cm_section)
    cycle_model_py = ip_dir / "model" / "cycle_model.py"
    # CL needed if cycle_model section present and non-trivial (has latency or targets)
    cl_needed = cm_non_empty and (
        "latency" in cm_section or "targets" in cm_section
    )
    if cm_non_empty and (not cl_needed or cycle_model_py.is_file()):
        g6_status = "approved"
    elif cm_non_empty:
        g6_status = "pending"
    else:
        g6_status = "pending"
    gates.append({
        "id": "G6",
        "title": "CL/performance target 승인",
        "status": g6_status,
        "evidence_required": [
            "cycle_model.targets or latency declared",
            "synthesis.ppa_targets.frequency_mhz_min set when timing-sensitive",
        ],
        "locked_artifacts": [
            f"{ip}/yaml/{ip}.ssot.yaml#cycle_model",
            f"{ip}/model/cycle_model.py",
        ],
    })

    # G7 RTL architecture
    decomp = _load_json(ip_dir / "model" / "decomposition.json")
    g7_status = "approved" if decomp is not None and decomp.get("complete") is True else "pending"
    gates.append({
        "id": "G7",
        "title": "RTL architecture 방향 승인",
        "status": g7_status,
        "evidence_required": [
            f"{ip}/yaml/{ip}.ssot.yaml#sub_modules approved",
            "decomposition.json complete",
        ],
        "locked_artifacts": [
            f"{ip}/yaml/{ip}.ssot.yaml#sub_modules",
            f"{ip}/model/decomposition.json",
        ],
    })

    # G8 PPA/DFT
    ppa_targets = None
    if ssot:
        syn = ssot.get("synthesis", {})
        if isinstance(syn, dict):
            ppa_targets = syn.get("ppa_targets")
    g8_status = "approved" if ppa_targets else "pending"
    gates.append({
        "id": "G8",
        "title": "PPA/DFT trade-off 승인",
        "status": g8_status,
        "evidence_required": [
            f"{ip}/reports/ppa_sweep.json reviewed",
            "DFT coverage target set",
        ],
        "locked_artifacts": [
            f"{ip}/yaml/{ip}.ssot.yaml#synthesis.ppa_targets",
            f"{ip}/yaml/{ip}.ssot.yaml#dft",
        ],
    })

    # G9 Final sign-off
    sign_off = _load_json(ip_dir / "golden" / "sign_off.json")
    g9_status = "approved" if sign_off is not None and sign_off.get("signed") is True else "pending"
    gates.append({
        "id": "G9",
        "title": "Final sign-off",
        "status": g9_status,
        "evidence_required": [
            "all gates G1..G8 approved",
            "all equivalence_goals.json goals not blocked",
            "fl_cl_rtl regression passed",
        ],
        "locked_artifacts": [f"{ip}/golden/sign_off.json"],
    })

    return gates


# ---------------------------------------------------------------------------
# Manifest builders
# ---------------------------------------------------------------------------


def _interp(value: Any, ip: str) -> Any:
    if isinstance(value, str):
        return value.replace("{ip}", ip)
    if isinstance(value, list):
        return [_interp(v, ip) for v in value]
    if isinstance(value, dict):
        return {k: _interp(v, ip) for k, v in value.items()}
    return value


def _build_loops(ip: str) -> list[dict[str, Any]]:
    return [_interp(loop, ip) for loop in _LLM_LOOPS]


def _build_manifest(ip: str, ip_dir: Path) -> dict[str, Any]:
    ssot = _load_ssot(ip_dir, ip)
    gates = _detect_gate_status(ip, ip_dir, ssot)
    loops = _build_loops(ip)

    approved = sum(1 for g in gates if g["status"] == "approved")
    pending = sum(1 for g in gates if g["status"] == "pending")
    blocked = sum(1 for g in gates if g["status"] == "blocked")

    return {
        "schema_version": 1,
        "type": "human_llm_authority_manifest",
        "ip": ip,
        "principle": _PRINCIPLE,
        "cardinal_rule": (
            "LLM은 RTL/test/vector/report을 자유롭게 수정한다. "
            "그러나 RTL이 FL과 어긋났을 때 FL을 바꿔서 PASS시키는 것은 금지된다. "
            "FL/spec/coverage_goal/perf_target/interface contract 변경은 사람 승인 없이는 불가능하며, "
            "PASS의 의미는 항상 locked truth(FL+SSOT) 기준으로만 판단한다. "
            "model_signature.json drift가 감지되면 downstream worker는 [SSOT HANDOFF] golden_changed를 발행하고 멈춰야 한다."
        ),
        "general_flow_guarantee": (
            "이 manifest는 IP-agnostic이다. 9 gates / 9 loops / 6 rules / repo_layout 모두 "
            "특정 IP의 프로토콜이나 도메인을 가정하지 않으며, 게이트 상태는 on-disk artifact 존재/내용만 "
            "근거로 자동 감지된다. 어떤 IP의 SSOT도 동일한 manifest 골격을 받는다."
        ),
        "operating_rules": _OPERATING_RULES,
        "human_gates": gates,
        "llm_loops": loops,
        "repo_layout": _REPO_LAYOUT,
        "summary": {
            "gates_total": 9,
            "gates_approved": approved,
            "gates_pending": pending,
            "gates_blocked": blocked,
            "loops_total": len(loops),
            "loops_with_evidence_path": sum(1 for l in loops if l.get("validator_path")),
        },
    }


# ---------------------------------------------------------------------------
# Markdown renderer
# ---------------------------------------------------------------------------


def _status_checkbox(status: str) -> str:
    if status == "approved":
        return "[x]"
    if status == "blocked":
        return "[!]"
    return "[ ]"


def _render_markdown(manifest: dict[str, Any]) -> str:
    ip = manifest["ip"]
    lines: list[str] = []

    lines.append(f"# Human-LLM Authority Manifest — {ip}")
    lines.append("")
    lines.append(f"> {manifest['principle']}")
    lines.append("")
    if manifest.get("cardinal_rule"):
        lines.append("## Cardinal Rule")
        lines.append(f"> {manifest['cardinal_rule']}")
        lines.append("")
    if manifest.get("general_flow_guarantee"):
        lines.append("## General Flow Guarantee")
        lines.append(f"> {manifest['general_flow_guarantee']}")
        lines.append("")

    lines.append("## Operating Rules")
    for idx, rule in enumerate(manifest["operating_rules"], 1):
        lines.append(
            f"{idx}. **{rule['id']}** — {rule['rule']} (scope: {rule['scope']})"
        )
    lines.append("")

    summary = manifest["summary"]
    lines.append(f"## Human Gates ({summary['gates_total']})")
    for gate in manifest["human_gates"]:
        cb = _status_checkbox(gate["status"])
        lines.append(f"- {cb} **{gate['id']} {gate['title']}** — {gate['status']}")
    lines.append("")

    lines.append(f"## LLM Loops ({summary['loops_total']})")
    for loop in manifest["llm_loops"]:
        lines.append(
            f"- **{loop['id']} {loop['title']}** — {loop['evidence_point']} → "
            f"{loop['llm_action']}. "
            f"Validator: {loop['validator_path']}. "
            f"Owner-on-fail: {loop['owner_on_fail']}."
        )
        for sub in loop.get("sub_stages", []) or []:
            metrics = ", ".join(sub.get("metrics", []))
            lines.append(
                f"  - {sub['stage']}: {sub.get('evidence','')} ({metrics})"
            )
        if loop.get("feedback"):
            lines.append(f"  - feedback: {loop['feedback']}")
    lines.append("")

    layout = manifest["repo_layout"]
    lines.append("## Repo Layout")
    lines.append(f"**Locked (human-owned)**: {', '.join(layout['locked'])}")
    lines.append(f"**LLM-editable**: {', '.join(layout['llm_editable'])}")
    lines.append(f"**Agent-runnable validators**: {', '.join(layout['agent_runnable_validators'])}")
    lines.append("")

    lines.append("## Summary")
    lines.append(f"- Gates approved: {summary['gates_approved']}/{summary['gates_total']}")
    lines.append(f"- Gates pending: {summary['gates_pending']}/{summary['gates_total']}")
    lines.append(f"- Gates blocked: {summary['gates_blocked']}/{summary['gates_total']}")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Emit per-IP Human-LLM authority manifest under <root>/<ip>/governance/"
    )
    parser.add_argument("ip", help="IP name (e.g. smbus)")
    parser.add_argument("--root", default=".", help="Root directory containing <ip>/")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    ip_dir = root / args.ip

    if not ip_dir.is_dir():
        print(f"[emit_authority_manifest] ERROR: IP directory not found: {ip_dir}")
        return 1

    manifest = _build_manifest(args.ip, ip_dir)

    gov_dir = ip_dir / "governance"
    gov_dir.mkdir(parents=True, exist_ok=True)

    json_path = gov_dir / "authority.json"
    md_path = gov_dir / "authority.md"

    json_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    md_path.write_text(_render_markdown(manifest), encoding="utf-8")

    s = manifest["summary"]
    print(
        f"[emit_authority_manifest] wrote {json_path.relative_to(root)}"
        f"  gates={s['gates_approved']}approved/{s['gates_pending']}pending/{s['gates_blocked']}blocked"
        f"  loops={s['loops_total']}"
    )
    print(f"[emit_authority_manifest] wrote {md_path.relative_to(root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
