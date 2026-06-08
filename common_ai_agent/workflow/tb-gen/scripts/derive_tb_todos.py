#!/usr/bin/env python3
"""Derive TB validation TODOs from locked contracts and SSOT.

The cocotb generator writes the executable harness.  This script writes the
contract/evidence ledger that says what that harness must prove.  The visible
TodoTracker item stays compact; the per-contract responsibilities live in
``tb/tb_todo_plan.json`` for audit and repair routing.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
import re
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

import yaml


WORKFLOW_ROOT = Path(__file__).resolve().parents[2]
if str(WORKFLOW_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKFLOW_ROOT))

from behavioral_contracts import (  # noqa: E402
    BehavioralContractError,
    compare_behavioral_to_function_cycle,
    normalize_behavioral_contracts,
)
from structural_contracts import (  # noqa: E402
    StructuralContractError,
    compare_structural_to_ssot,
    normalize_structural_contracts,
    ssot_port_map,
)


TB_STAGE_NAMES = {
    "tb",
    "tb-gen",
    "ssot-tb",
    "ssot-tb-cocotb",
    "gen-tb",
    "sim",
    "simulation",
    "coverage",
    "goal-audit",
    "contract-check",
    "contract-reflection",
}


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _slug(value: Any, fallback: str = "item") -> str:
    text = re.sub(r"[^A-Za-z0-9_]+", "_", str(value or "")).strip("_")
    if not text:
        text = fallback
    if not re.match(r"^[A-Za-z_]", text):
        text = f"{fallback}_{text}"
    return text[:96]


def _norm_stage(value: Any) -> str:
    return re.sub(r"[\s_]+", "-", str(value or "").strip().lower())


def _present(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        text = value.strip()
        return bool(text) and text.lower() not in {"none", "n/a", "na", "tbd", "todo", "unknown"}
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return [{"name": key, "value": item} for key, item in value.items()]
    return [value]


def _load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.is_file():
        return rows
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not raw.strip():
            continue
        try:
            item = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            rows.append(item)
    return rows


def _resolve_project_root(root_arg: str, ip_root_arg: str, ip: str) -> Path:
    project_root = Path(os.path.expandvars(root_arg or os.environ.get("ATLAS_PROJECT_ROOT") or ".")).expanduser().resolve()
    if ip and (project_root / ip / "yaml" / f"{ip}.ssot.yaml").is_file():
        return project_root
    if ip and (project_root / "yaml" / f"{ip}.ssot.yaml").is_file():
        return project_root.parent
    ip_root_raw = (ip_root_arg or os.environ.get("ATLAS_IP_ROOT") or "").strip()
    if ip_root_raw:
        ip_root = Path(os.path.expandvars(ip_root_raw)).expanduser()
        if not ip_root.is_absolute():
            ip_root = project_root / ip_root
        ip_root = ip_root.resolve()
        candidate_root = ip_root.parent if (not ip or ip_root.name == ip or (ip_root / "yaml").is_dir()) else ip_root
        if ip and (candidate_root / ip / "yaml" / f"{ip}.ssot.yaml").is_file():
            return candidate_root
    return project_root


def _load_ssot(root: Path, ip: str) -> tuple[Path, dict[str, Any]]:
    path = root / ip / "yaml" / f"{ip}.ssot.yaml"
    if not path.is_file():
        raise SystemExit(f"[derive_tb_todos] missing SSOT: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8", errors="replace")) or {}
    if not isinstance(data, dict):
        raise SystemExit("[derive_tb_todos] SSOT top-level must be a mapping")
    return path, data


def _top_name(ssot: dict[str, Any], fallback: str) -> str:
    top = ssot.get("top_module")
    if isinstance(top, dict):
        return str(top.get("name") or fallback)
    if isinstance(top, str) and top.strip():
        return top.strip()
    return fallback


def _contract_id(entry: dict[str, Any]) -> str:
    for key in ("id", "contract_id", "contract_ref_id", "behavioral_contract_id"):
        value = str(entry.get(key) or "").strip()
        if value:
            return value
    return ""


def _obligation_ids(ip_dir: Path) -> set[str]:
    doc = _load_json(ip_dir / "req" / "obligations.json")
    ids: set[str] = set()
    for row in doc.get("obligations") if isinstance(doc.get("obligations"), list) else []:
        if isinstance(row, dict) and str(row.get("obligation_id") or "").strip():
            ids.add(str(row["obligation_id"]).strip())
    return ids


def _load_locked_contracts(ip_dir: Path, ip: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    req_dir = ip_dir / "req"
    known = _obligation_ids(ip_dir)
    issues: list[dict[str, Any]] = []
    docs: dict[str, Any] = {
        "behavioral_contracts": {"schema_version": 1, "type": "behavioral_contracts", "ip": ip, "contracts": []},
        "structural_contracts": {"schema_version": 1, "type": "structural_contracts", "ip": ip, "contracts": []},
        "present": {
            "behavioral_contracts": (req_dir / "behavioral_contracts.json").is_file(),
            "structural_contracts": (req_dir / "structural_contracts.json").is_file(),
        },
    }

    behavioral_path = req_dir / "behavioral_contracts.json"
    if behavioral_path.is_file():
        try:
            docs["behavioral_contracts"] = normalize_behavioral_contracts(
                ip,
                _load_json(behavioral_path),
                known_obligation_ids=known or None,
            )
        except BehavioralContractError as exc:
            issues.append({
                "id": "LOCKED_TRUTH_BEHAVIORAL_CONTRACTS_INVALID",
                "source_ref": "req/behavioral_contracts.json",
                "owner": "req-gen",
                "reason": str(exc),
            })

    structural_path = req_dir / "structural_contracts.json"
    if structural_path.is_file():
        try:
            docs["structural_contracts"] = normalize_structural_contracts(
                ip,
                _load_json(structural_path),
                known_obligation_ids=known or None,
            )
        except StructuralContractError as exc:
            issues.append({
                "id": "LOCKED_TRUTH_STRUCTURAL_CONTRACTS_INVALID",
                "source_ref": "req/structural_contracts.json",
                "owner": "req-gen",
                "reason": str(exc),
            })
    return docs, issues


def _collect_refs(value: Any, contract_id: str, path: str = "") -> list[str]:
    refs: list[str] = []
    ref_keys = {
        "source_refs",
        "contract_refs",
        "contract_ref",
        "behavioral_contract_refs",
        "behavioral_contracts",
        "structural_contract_refs",
        "structural_contracts",
        "locked_truth_projection",
    }

    def mentions(item: Any) -> bool:
        if isinstance(item, str):
            return item == contract_id
        if isinstance(item, list):
            return any(mentions(child) for child in item)
        if isinstance(item, dict):
            return any(mentions(child) for child in item.values())
        return False

    if isinstance(value, dict):
        if any(str(key) in ref_keys and mentions(item) for key, item in value.items()):
            refs.append(path)
        for key, item in value.items():
            refs.extend(_collect_refs(item, contract_id, f"{path}.{key}" if path else str(key)))
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            refs.extend(_collect_refs(item, contract_id, f"{path}[{idx}]"))
    return sorted(dict.fromkeys(ref for ref in refs if ref))


def _contract_projection_refs(ssot: dict[str, Any], contract_id: str) -> list[str]:
    refs: list[str] = []
    for section in (
        "function_model",
        "cycle_model",
        "fsm",
        "registers",
        "interrupts",
        "features",
        "dataflow",
        "test_requirements",
        "coverage_goals",
        "quality_gates",
        "io_list",
        "integration",
        "rtl_contract",
    ):
        if section in ssot:
            refs.extend(_collect_refs(ssot[section], contract_id, section))
    return sorted(dict.fromkeys(refs))


def _stage_contracts_for_tb(contract: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in _as_list(contract.get("stage_contracts")):
        if not isinstance(row, dict):
            continue
        stage = _norm_stage(row.get("stage") or row.get("workflow") or row.get("target"))
        if not stage or stage in TB_STAGE_NAMES:
            rows.append(row)
    return rows


def _task(
    tasks: list[dict[str, Any]],
    *,
    category: str,
    phase: str,
    source_ref: str,
    title: str,
    detail: str,
    criteria: list[str],
    value: Any = None,
    required: bool = True,
    priority: str = "high",
) -> dict[str, Any]:
    item = {
        "id": f"TB-{len(tasks) + 1:04d}",
        "category": category,
        "phase": phase,
        "source_ref": source_ref,
        "content": title,
        "detail": detail,
        "criteria": criteria,
        "ssot_refs": [source_ref] if source_ref else [],
        "ssot_context": value if isinstance(value, dict) else {"value": value} if value is not None else {},
        "required": required,
        "priority": priority,
    }
    tasks.append(item)
    return item


def _add_gate_tasks(tasks: list[dict[str, Any]]) -> None:
    gates = [
        (
            "authority_inputs",
            "authoring",
            "quality_gates.tb_gen.authority_inputs",
            "Gate: TB authority inputs are present and contract-owned",
            "TB generation must derive stimulus and expected behavior from locked req contracts, SSOT Function/Cycle models, equivalence goals, and the RTL contract.",
            [
                "SSOT YAML is present",
                "function_model, cycle_model, and test_requirements are present or an SSOT blocker is emitted",
                "verify/equivalence_goals.json and rtl/rtl_contract.json exist before generated scoreboard approval",
                "Locked behavioral/structural contract files are loaded directly when present",
            ],
        ),
        (
            "tb_artifacts",
            "authoring",
            "quality_gates.tb_gen.generated_artifacts",
            "Gate: generated cocotb/pyuvm TB artifacts are present",
            "Generated TB must contain the layered files, manifest, and generation report expected by the common TB flow.",
            [
                "test_<ip>.py, test_runner.py, transactions.py, sequences.py, agents.py, scoreboard.py, tb_coverage.py, and uvm_env.py exist",
                "tb_manifest.json top matches SSOT top_module.name",
                "tb_generation.json reports status=pass",
            ],
        ),
        (
            "scoreboard_self_check",
            "authoring",
            "quality_gates.tb_gen.scoreboard_self_check",
            "Gate: common equivalence scoreboard contract is loadable",
            "The generated TB must preserve EquivalenceScoreboard as the expected-behavior adapter instead of copying observed RTL behavior.",
            [
                "workflow/tb-gen/runtime/equivalence_scoreboard.py --self-check passes",
                "Generated scoreboard.py imports or wraps EquivalenceScoreboard",
                "scoreboard rows are configured from verify/equivalence_goals.json",
            ],
        ),
        (
            "scoreboard_events",
            "evidence",
            "quality_gates.tb_gen.scoreboard_events",
            "Gate: simulation emits passing scoreboard events for required goals",
            "TB validation is not closed by file generation alone. Simulation must emit RTL-observed scoreboard rows carrying goal IDs and coverage refs.",
            [
                "sim/scoreboard_events.jsonl exists",
                "At least one required unblocked goal has a passing scoreboard row",
                "Rows contain goal_id, scenario_id, stimulus, fl_expected, rtl_observed, passed, and coverage_refs",
            ],
        ),
        (
            "coverage_closure",
            "evidence",
            "quality_gates.tb_gen.coverage_closure",
            "Gate: TB evidence reaches functional/cycle coverage closure",
            "Coverage evidence must come from generic coverage artifacts and passing scoreboard rows, not IP-specific parsers or weakened bins.",
            [
                "cov/coverage.json exists",
                "coverage status is pass",
                "rtl_observed coverage has no missing bins or invalid rows when reported",
            ],
        ),
        (
            "contract_validation_closure",
            "evidence",
            "quality_gates.tb_gen.contract_validation_closure",
            "Gate: every locked contract has TB validation evidence",
            "Each obligation-owned behavioral/structural contract must map to stimulus, observation, scoreboard/assertion, and coverage or carry an explicit human gate.",
            [
                "Behavioral contract stimulus and scoreboard rows are authored",
                "Structural signals are mapped to driver/monitor responsibilities with timing/synchronization notes",
                "Passing scoreboard or coverage evidence references the contract/goal aliases",
            ],
        ),
        (
            "dynamic_todo_closure",
            "evidence",
            "quality_gates.tb_gen.dynamic_todo_closure",
            "Gate: every required tb_todo_plan item is closed",
            "TB-gen PASS for validation evidence is forbidden until every required authoring and evidence ledger row has pass status.",
            [
                "open_required_todos is zero for the requested audit mode",
                "all_required_todos_pass is true",
            ],
        ),
    ]
    for kind, phase, source_ref, title, detail, criteria in gates:
        task = _task(
            tasks,
            category="tb_gate.tb_gen",
            phase=phase,
            source_ref=source_ref,
            title=title,
            detail=detail,
            criteria=criteria,
            value={"gate_check": kind},
            priority="critical",
        )
        task["gate_todo"] = {"stage": "tb-gen", "kind": kind}


def _add_structural_tasks(tasks: list[dict[str, Any]], contracts: dict[str, Any], ssot: dict[str, Any]) -> None:
    ports = ssot_port_map(ssot)
    for contract in _as_list(contracts.get("contracts")):
        if not isinstance(contract, dict):
            continue
        cid = _contract_id(contract)
        for signal in _as_list(contract.get("signals")):
            if not isinstance(signal, dict):
                continue
            name = str(signal.get("name") or "").strip()
            if not name:
                continue
            direction = str(signal.get("dir") or "").strip() or str(signal.get("direction") or "").strip()
            timing = signal.get("timing") if isinstance(signal.get("timing"), dict) else {}
            ssot_timing = ports.get(name, {}).get("timing") if isinstance(ports.get(name), dict) else {}
            effective_timing = timing or (ssot_timing if isinstance(ssot_timing, dict) else {})
            kind = str(effective_timing.get("kind") or "unspecified")
            clock = effective_timing.get("clock_domain") or effective_timing.get("sync_to") or effective_timing.get("clock")
            criteria = [
                f"DUT port {name} is bound in tb_manifest.json",
                "Driver responsibility exists for input/inout signals" if direction in {"input", "inout"} else "Monitor observation exists for output/inout signals",
                "Signal width/direction follows the structural contract",
                f"Synchronization policy is recorded: kind={kind}, clock_domain={clock or 'n/a'}",
            ]
            _task(
                tasks,
                category="contract.structural.signal",
                phase="authoring",
                source_ref=f"contract.structural.{cid}.signals.{_slug(name)}",
                title=f"Map structural signal {name} into TB driver/monitor contract",
                detail=(
                    "The TB must treat structural contract IO as executable driver/monitor responsibilities. "
                    "Timing metadata records whether the signal is sync, async, reset, clock, or cross-domain."
                ),
                criteria=criteria,
                value={"contract_id": cid, "signal": signal, "effective_timing": effective_timing},
                priority="high",
            )


def _add_behavioral_contract_tasks(tasks: list[dict[str, Any]], contracts: dict[str, Any], ssot: dict[str, Any]) -> None:
    for contract in _as_list(contracts.get("contracts")):
        if not isinstance(contract, dict):
            continue
        cid = _contract_id(contract)
        if not cid:
            continue
        projections = _contract_projection_refs(ssot, cid)
        tb_stages = _stage_contracts_for_tb(contract)
        value = {
            "contract_id": cid,
            "obligations": contract.get("obligations") or [],
            "projection_refs": projections,
            "tb_stage_contracts": tb_stages,
        }
        _task(
            tasks,
            category="contract.behavioral.stimulus",
            phase="authoring",
            source_ref=f"contract.behavioral.{cid}.stimulus",
            title=f"Create TB stimulus for behavioral contract {cid}",
            detail="Generate sequence/scenario stimulus that exercises the contract decision table or transaction rule without deriving expected values from RTL.",
            criteria=[
                "Stimulus fields are driven from function_model/test_requirements/contract inputs",
                "At least one generated scenario or equivalence goal exercises this contract",
                "Blocked or ambiguous stimulus is emitted as tb_blocked.json instead of guessed",
            ],
            value=value,
            priority="high",
        )
        _task(
            tasks,
            category="contract.behavioral.scoreboard",
            phase="authoring",
            source_ref=f"contract.behavioral.{cid}.scoreboard",
            title=f"Bind behavioral contract {cid} to scoreboard expectation",
            detail="Scoreboard expected behavior must trace to FunctionalModel/contract tables and must not mirror DUT observations.",
            criteria=[
                "FunctionalModel or contract decision table is the expected-behavior source",
                "Generated scoreboard event rows carry an equivalence goal or contract alias",
                "Outputs/state updates from the contract are observable or explicitly blocked",
            ],
            value=value,
            priority="critical",
        )
        _task(
            tasks,
            category="contract.behavioral.coverage",
            phase="evidence",
            source_ref=f"contract.behavioral.{cid}.coverage",
            title=f"Close coverage evidence for behavioral contract {cid}",
            detail="A behavioral contract is validated only after simulation produces passing scoreboard/coverage evidence for the exercised contract.",
            criteria=[
                "Passing scoreboard row references this contract, its obligation, or an equivalence goal derived from it",
                "Coverage refs for the scenario/bin are hit",
                "Failures are routed to rtl-gen, tb-gen, ssot-gen, or human with evidence",
            ],
            value=value,
            priority="critical",
        )


def _named_rows(section: Any, keys: tuple[str, ...]) -> list[tuple[str, dict[str, Any]]]:
    if not isinstance(section, dict):
        return []
    rows: list[tuple[str, dict[str, Any]]] = []
    for key in keys:
        value = section.get(key)
        for idx, item in enumerate(_as_list(value)):
            if isinstance(item, dict):
                name = item.get("id") or item.get("name") or item.get("signal") or item.get("rule_id") or idx
                rows.append((f"{key}.{_slug(name)}", item))
            elif _present(item):
                rows.append((f"{key}.{idx}", {"value": item}))
    return rows


def _add_ssot_model_tasks(tasks: list[dict[str, Any]], ssot: dict[str, Any]) -> None:
    fm = ssot.get("function_model") if isinstance(ssot.get("function_model"), dict) else {}
    for suffix, row in _named_rows(fm, ("transactions", "invariants", "error_cases", "state_variables")):
        category = "function_model.scoreboard" if suffix.startswith(("transactions", "invariants", "error_cases")) else "function_model.observation"
        _task(
            tasks,
            category=category,
            phase="authoring",
            source_ref=f"function_model.{suffix}",
            title=f"Map function_model {suffix} into TB expected behavior",
            detail="The generated TB must use FunctionalModel as the reference adapter for this function-level behavior.",
            criteria=[
                "Stimulus or observation covers the model row",
                "Scoreboard expected data comes from FunctionalModel.apply or an equivalent model adapter",
                "Generated scoreboard rows preserve the source goal/scenario ID",
            ],
            value=row,
            priority="high",
        )

    cm = ssot.get("cycle_model") if isinstance(ssot.get("cycle_model"), dict) else {}
    for suffix, row in _named_rows(cm, ("handshake_rules", "pipeline", "latency", "ordering", "backpressure", "arbitration", "observability")):
        _task(
            tasks,
            category="cycle_model.monitor",
            phase="authoring",
            source_ref=f"cycle_model.{suffix}",
            title=f"Map cycle_model {suffix} into TB monitor/assertion",
            detail="Drivers, monitors, timeouts, and sampling must follow the SSOT cycle/handshake contract.",
            criteria=[
                "Drive and sample points are synchronized to the declared clock/reset domain",
                "Latency/ordering/backpressure rules become monitors, timeouts, or assertions",
                "Missing CDC/latency facts are blocked instead of guessed",
            ],
            value=row,
            priority="high",
        )


def _add_test_coverage_tasks(tasks: list[dict[str, Any]], ssot: dict[str, Any], goals: dict[str, Any]) -> None:
    test_req = ssot.get("test_requirements") if isinstance(ssot.get("test_requirements"), dict) else {}
    for idx, scenario in enumerate(_as_list(test_req.get("scenarios"))):
        row = scenario if isinstance(scenario, dict) else {"value": scenario}
        sid = row.get("id") or row.get("name") or idx
        _task(
            tasks,
            category="test_requirements.scenario",
            phase="authoring",
            source_ref=f"test_requirements.scenarios.{_slug(sid)}",
            title=f"Create executable TB scenario {sid}",
            detail="Each SSOT scenario must become bounded executable stimulus with explicit expected/checker mapping.",
            criteria=[
                "Scenario stimulus is represented by a sequence or bounded test",
                "Expected result/checker comes from SSOT/FunctionalModel, not RTL",
                "Scenario contributes scoreboard and/or coverage evidence",
            ],
            value=row,
            priority="high",
        )

    coverage_roots = []
    if isinstance(test_req.get("coverage_goals"), dict):
        coverage_roots.append(test_req["coverage_goals"])
    if isinstance(ssot.get("coverage_goals"), dict):
        coverage_roots.append(ssot["coverage_goals"])
    for root_idx, cov_root in enumerate(coverage_roots):
        for domain, raw in cov_root.items():
            bins = raw.get("bins") if isinstance(raw, dict) else raw
            for idx, bin_row in enumerate(_as_list(bins)):
                row = bin_row if isinstance(bin_row, dict) else {"value": bin_row}
                bid = row.get("id") or row.get("name") or f"{domain}_{idx}"
                _task(
                    tasks,
                    category="coverage.goal",
                    phase="evidence",
                    source_ref=f"coverage_goals.{_slug(domain)}.{_slug(bid)}",
                    title=f"Hit TB coverage bin {bid}",
                    detail="Coverage bins close only from passing RTL-observed scoreboard/simulation evidence.",
                    criteria=[
                        "Coverage bin appears in cov/coverage.json or coverage_functional.json",
                        "Bin is hit by a passing scoreboard/scenario row",
                        "Coverage gaps route back to tb-gen stimulus rather than weakening SSOT",
                    ],
                    value={"root": root_idx, "domain": domain, "bin": row},
                    priority="normal",
                )

    for idx, goal in enumerate(goals.get("goals") if isinstance(goals.get("goals"), list) else []):
        if not isinstance(goal, dict):
            continue
        gid = str(goal.get("goal_id") or goal.get("id") or f"goal_{idx}")
        required = goal.get("blocked") is not True and goal.get("optional") is not True and goal.get("required") is not False
        _task(
            tasks,
            category="equivalence.goal_scoreboard",
            phase="authoring",
            source_ref=f"verify.equivalence_goals.{_slug(gid)}",
            title=f"Bind equivalence goal {gid} to TB scoreboard",
            detail="Each unblocked equivalence goal must produce scoreboard evidence or a precise blocker.",
            criteria=[
                "Goal ID is emitted in sim/scoreboard_events.jsonl",
                "Stimulus and expected contract trace to the SSOT Function/Cycle model",
                "Module-scope goals observe real module-boundary RTL signals",
            ],
            value=goal,
            required=required,
            priority="critical" if required else "normal",
        )


def _authority_blockers(ip_dir: Path, ssot: dict[str, Any], contracts: dict[str, Any]) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    for section in ("function_model", "cycle_model", "test_requirements"):
        if not _present(ssot.get(section)):
            blockers.append({
                "id": f"MISSING_{section.upper()}",
                "source_ref": section,
                "owner": "ssot-gen",
                "reason": f"TB generation requires non-empty SSOT {section}.",
            })
    for rel, owner, reason in (
        ("verify/equivalence_goals.json", "fl-model-gen", "TB scoreboards require generated equivalence goals."),
        ("rtl/rtl_contract.json", "rtl-gen", "TB drivers/monitors require a concrete RTL contract."),
    ):
        if not (ip_dir / rel).is_file():
            blockers.append({"id": f"MISSING_{_slug(rel).upper()}", "source_ref": rel, "owner": owner, "reason": reason})

    behavioral = contracts.get("behavioral_contracts") if isinstance(contracts.get("behavioral_contracts"), dict) else {}
    if behavioral.get("contracts"):
        issues, _summary = compare_behavioral_to_function_cycle(behavioral, ssot)
        for idx, issue in enumerate(issues):
            blockers.append({
                "id": f"BEHAVIORAL_CONTRACT_PROJECTION_{idx}",
                "source_ref": "req/behavioral_contracts.json",
                "owner": "ssot-gen",
                "reason": issue,
            })
    structural = contracts.get("structural_contracts") if isinstance(contracts.get("structural_contracts"), dict) else {}
    if structural.get("contracts"):
        issues, _summary = compare_structural_to_ssot(structural, ssot)
        for idx, issue in enumerate(issues):
            blockers.append({
                "id": f"STRUCTURAL_CONTRACT_PROJECTION_{idx}",
                "source_ref": "req/structural_contracts.json",
                "owner": "ssot-gen",
                "reason": issue,
            })
    return blockers


def _artifact_fresh(path: Path, sources: list[Path]) -> bool:
    if not path.is_file():
        return False
    try:
        mtime = path.stat().st_mtime
        return all(not src.is_file() or mtime >= src.stat().st_mtime for src in sources)
    except OSError:
        return False


def _required_goal_ids(goals: dict[str, Any]) -> set[str]:
    out: set[str] = set()
    for goal in goals.get("goals") if isinstance(goals.get("goals"), list) else []:
        if not isinstance(goal, dict):
            continue
        gid = str(goal.get("goal_id") or goal.get("id") or "").strip()
        if gid and goal.get("blocked") is not True and goal.get("optional") is not True and goal.get("required") is not False:
            out.add(gid)
    return out


def _name_used_in_code(text: str, target: str) -> bool:
    """True only if `target` is a real import/name/attribute in parsed code.

    A comment or string-literal mention does not count: comments never enter the
    AST, and a bare string literal is an ``ast.Constant`` (not a Name/import), so
    a hollow ``# wire EquivalenceScoreboard`` placeholder is correctly rejected.
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if any(alias.name == target for alias in node.names):
                return True
        elif isinstance(node, ast.Import):
            if any(alias.name == target or alias.name.endswith("." + target) for alias in node.names):
                return True
        elif isinstance(node, ast.Name) and node.id == target:
            return True
        elif isinstance(node, ast.Attribute) and node.attr == target:
            return True
    return False


def _has_executable_body(text: str) -> bool:
    """True if the module has at least one statement beyond a docstring/``pass``.

    A structural floor that distinguishes a generated stub with real content from
    an empty/placeholder file. It is intentionally not a content check — the
    per-obligation content grep is a separate, deeper guard.
    """
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return False
    for node in tree.body:
        if isinstance(node, ast.Pass):
            continue
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            continue  # module docstring
        return True
    return False


def _tb_artifact_issue(ip_dir: Path, ip: str, top: str) -> str:
    tb_dir = ip_dir / "tb" / "cocotb"
    required = [
        f"test_{ip}.py",
        "test_runner.py",
        "transactions.py",
        "sequences.py",
        "agents.py",
        "scoreboard.py",
        "tb_coverage.py",
        "uvm_env.py",
        "tb_manifest.json",
        "tb_generation.json",
    ]
    missing = [name for name in required if not (tb_dir / name).is_file()]
    if missing:
        return "Missing generated TB artifact(s): " + ", ".join(missing[:8])
    manifest = _load_json(tb_dir / "tb_manifest.json")
    if manifest.get("top") != top:
        return f"tb_manifest.json top {manifest.get('top')!r} does not match SSOT top {top!r}."
    generation = _load_json(tb_dir / "tb_generation.json")
    if generation.get("status") != "pass":
        return "tb_generation.json status is not pass."
    scoreboard_text = (tb_dir / "scoreboard.py").read_text(encoding="utf-8", errors="replace")
    if not _name_used_in_code(scoreboard_text, "EquivalenceScoreboard"):
        return "Generated scoreboard.py does not import/use EquivalenceScoreboard (comment/string mention does not count)."
    empty = [
        name
        for name in (f"test_{ip}.py", "transactions.py", "sequences.py", "scoreboard.py")
        if not _has_executable_body((tb_dir / name).read_text(encoding="utf-8", errors="replace"))
    ]
    if empty:
        return "Generated TB source(s) are empty stubs (no executable body): " + ", ".join(empty)
    return ""


def _scoreboard_evidence_issue(ip_dir: Path, goals: dict[str, Any]) -> str:
    required = _required_goal_ids(goals)
    rows = _load_jsonl(ip_dir / "sim" / "scoreboard_events.jsonl")
    if not rows:
        return "Missing or empty sim/scoreboard_events.jsonl."
    passed = [row for row in rows if row.get("passed") is True and str(row.get("goal_id") or "").strip()]
    if not passed:
        return "scoreboard_events.jsonl has no passing goal rows."
    if required:
        seen = {str(row.get("goal_id")) for row in passed}
        missing = sorted(required - seen)
        if missing:
            return "Missing passing scoreboard row(s) for required goal(s): " + ", ".join(missing[:8])
    for row in passed:
        for key in ("goal_id", "scenario_id", "stimulus", "fl_expected", "rtl_observed", "coverage_refs"):
            if key not in row:
                return f"scoreboard row for {row.get('goal_id')} missing {key}."
        if not str(row.get("scenario_id") or "").strip():
            return f"scoreboard row for {row.get('goal_id')} has empty scenario_id."
        for key in ("stimulus", "fl_expected", "rtl_observed"):
            if not row.get(key):
                return f"scoreboard row for {row.get('goal_id')} has empty {key} (vacuous evidence)."
    return ""


def _coverage_issue(ip_dir: Path) -> str:
    coverage = _load_json(ip_dir / "cov" / "coverage.json")
    if not coverage:
        return "Missing cov/coverage.json."
    status = str(coverage.get("status") or "").strip().lower()
    if status not in {"pass", "passed", "ok"}:
        return f"coverage.json status is missing or not pass: {coverage.get('status')!r}."
    rtl_observed = coverage.get("rtl_observed") if isinstance(coverage.get("rtl_observed"), dict) else {}
    if rtl_observed:
        if str(rtl_observed.get("status") or "").strip().lower() not in {"pass", "passed", "ok"}:
            return "coverage.json rtl_observed.status is not pass."
        missing_bins = rtl_observed.get("missing_bins") if isinstance(rtl_observed.get("missing_bins"), list) else []
        invalid_rows = rtl_observed.get("invalid_rows") if isinstance(rtl_observed.get("invalid_rows"), list) else []
        if missing_bins:
            return "coverage.json rtl_observed missing bins: " + ", ".join(str(item) for item in missing_bins[:8])
        if invalid_rows:
            return "coverage.json rtl_observed has invalid rows."
    return ""


def _completion_for_task(
    task: dict[str, Any],
    *,
    audit_tb: bool,
    audit_evidence: bool,
    ip_dir: Path,
    ip: str,
    top: str,
    goals: dict[str, Any],
    blockers: list[dict[str, Any]],
) -> tuple[str, str, list[str]]:
    phase = str(task.get("phase") or "authoring")
    gate = task.get("gate_todo") if isinstance(task.get("gate_todo"), dict) else {}
    kind = str(gate.get("kind") or "")
    basis = ["tb/tb_todo_plan.json", str(task.get("source_ref") or "")]
    if blockers and kind == "authority_inputs":
        return "open", f"{len(blockers)} authority blocker(s) remain.", basis
    if not audit_tb:
        return "planned", "TB audit has not run yet.", basis
    if phase == "authoring":
        issue = _tb_artifact_issue(ip_dir, ip, top)
        if issue:
            return "open", issue, basis + ["tb/cocotb/"]
        if kind in {"authority_inputs", "tb_artifacts", "scoreboard_self_check", ""}:
            return "pass", "TB authoring artifacts are present and structurally mapped.", basis + ["tb/cocotb/tb_manifest.json"]
    if not audit_evidence:
        return "planned", "Simulation/coverage evidence audit has not run yet.", basis
    if kind == "scoreboard_events" or phase == "evidence":
        sb_issue = _scoreboard_evidence_issue(ip_dir, goals)
        if sb_issue:
            return "open", sb_issue, basis + ["sim/scoreboard_events.jsonl"]
        if kind == "coverage_closure" or str(task.get("category") or "").startswith("coverage."):
            cov_issue = _coverage_issue(ip_dir)
            if cov_issue:
                return "open", cov_issue, basis + ["cov/coverage.json"]
        return "pass", "Simulation scoreboard/coverage evidence is present for this TB ledger row.", basis
    return "pass", "TB evidence row is closed.", basis


def _update_completion(
    plan: dict[str, Any],
    *,
    audit_tb: bool,
    audit_evidence: bool,
    ip_dir: Path,
    ip: str,
    top: str,
    goals: dict[str, Any],
    blockers: list[dict[str, Any]],
) -> None:
    tasks = [task for task in plan.get("tasks", []) if isinstance(task, dict)]
    for task in tasks:
        status, reason, basis = _completion_for_task(
            task,
            audit_tb=audit_tb,
            audit_evidence=audit_evidence,
            ip_dir=ip_dir,
            ip=ip,
            top=top,
            goals=goals,
            blockers=blockers,
        )
        task["todo_completion"] = {
            "status": status,
            "required": bool(task.get("required", True)),
            "phase": task.get("phase") or "authoring",
            "criteria_total": len(task.get("criteria") or []),
            "reason": reason,
            "evidence_basis": [item for item in basis if item],
        }

    def open_tasks(phases: set[str]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for task in tasks:
            if not task.get("required", True) or str(task.get("phase") or "authoring") not in phases:
                continue
            completion = task.get("todo_completion") if isinstance(task.get("todo_completion"), dict) else {}
            if completion.get("status") != "pass":
                out.append({
                    "task_id": task.get("id"),
                    "category": task.get("category"),
                    "phase": task.get("phase"),
                    "source_ref": task.get("source_ref"),
                    "reason": completion.get("reason"),
                })
        return out

    authoring_open = open_tasks({"authoring"})
    validation_open = open_tasks({"authoring", "evidence"})
    plan["todo_completion"] = {
        "audit_tb": audit_tb,
        "audit_evidence": audit_evidence,
        "authoring_required_tasks": sum(1 for task in tasks if task.get("required", True) and task.get("phase") == "authoring"),
        "authoring_open_tasks": len(authoring_open),
        "validation_required_tasks": sum(1 for task in tasks if task.get("required", True)),
        "validation_open_tasks": len(validation_open),
        "open_authoring": authoring_open[:128],
        "open_validation": validation_open[:128],
        "authoring_todos_pass": audit_tb and not authoring_open,
        "all_required_todos_pass": audit_evidence and not validation_open,
        "rule": "tb-gen may claim authoring PASS after authoring rows close; contract validation PASS requires --audit-evidence after sim/coverage.",
    }


def _tracker_task(plan: dict[str, Any]) -> dict[str, Any]:
    ip = str(plan.get("ip") or "unknown")
    summary = plan.get("summary") if isinstance(plan.get("summary"), dict) else {}
    completion = plan.get("todo_completion") if isinstance(plan.get("todo_completion"), dict) else {}
    gate = plan.get("gate") if isinstance(plan.get("gate"), dict) else {}
    detail = [
        f"Single visible UI TODO for {summary.get('total_tasks', 0)} SSOT/contract-derived TB ledger item(s).",
        "Internal ledger: tb/tb_todo_plan.json.",
        "Visible tracker source: tb/tb_todo_tracker.json and todo/tb_todo_tracker.json.",
        "Generate or repair TB only; SSOT, req contracts, FL/CL model, and RTL expected behavior remain locked.",
        f"Current audit snapshot: gate={gate.get('status') or 'unknown'}, authoring_open={completion.get('authoring_open_tasks', 'unknown')}, validation_open={completion.get('validation_open_tasks', 'unknown')}.",
    ]
    criteria = [
        "Read yaml/<ip>.ssot.yaml, req/*contracts.json when present, verify/equivalence_goals.json, rtl/rtl_contract.json, and tb/tb_todo_plan.json.",
        "Generated pyuvm/cocotb TB maps structural IO timing/synchronization and behavioral contracts to drivers, monitors, scoreboard, and coverage.",
        "Run workflow/tb-gen/scripts/derive_tb_todos.py <ip> --root <project-root> --audit-tb after TB generation.",
        "Run workflow/tb-gen/scripts/derive_tb_todos.py <ip> --root <project-root> --audit-evidence after sim/coverage evidence exists.",
        "tb/tb_todo_plan.json gate.status is pass for the requested audit mode.",
        "Any failed contract/gate row routes back into this same gen-tb repair loop or emits tb_blocked.json.",
    ]
    return {
        "content": f"[gen-tb] Generate TB from SSOT contract ledger for {ip}",
        "activeForm": f"Generating TB from SSOT contract ledger for {ip}",
        "status": "pending",
        "detail": "\n".join(detail),
        "criteria": "\n".join(criteria),
        "priority": "high",
    }


def _convert_to_tracker(plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": f"{plan.get('ip', 'unknown')}-tb",
        "description": (
            "Auto-generated gen-tb TodoTracker: one visible TODO wraps the full "
            "TB contract/evidence ledger in tb/tb_todo_plan.json."
        ),
        "source_plan": "tb/tb_todo_plan.json",
        "source_task_count": len(plan.get("tasks") if isinstance(plan.get("tasks"), list) else []),
        "lock_additions": False,
        "tasks": [_tracker_task(plan)],
    }


def _stable_hash(obj: Any) -> str:
    def scrub(value: Any) -> Any:
        if isinstance(value, dict):
            return {str(k): scrub(v) for k, v in value.items() if str(k) not in {"generated_at", "todo_completion", "gate"}}
        if isinstance(value, list):
            return [scrub(item) for item in value]
        return value

    payload = json.dumps(scrub(obj), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _write_outputs(ip_dir: Path, plan: dict[str, Any]) -> None:
    tb_dir = ip_dir / "tb"
    logs_dir = ip_dir / "logs" / "tb-gen"
    todo_dir = ip_dir / "todo"
    tb_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    todo_dir.mkdir(parents=True, exist_ok=True)
    plan_text = json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    for path in (tb_dir / "tb_todo_plan.json", logs_dir / "tb_todo_plan.json", todo_dir / "tb_todo_plan.json"):
        path.write_text(plan_text, encoding="utf-8")
    tracker = _convert_to_tracker(plan)
    tracker_text = json.dumps(tracker, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    for path in (tb_dir / "tb_todo_tracker.json", todo_dir / "tb_todo_tracker.json"):
        path.write_text(tracker_text, encoding="utf-8")
    trace_rows = [
        {
            "task_id": task.get("id"),
            "category": task.get("category"),
            "phase": task.get("phase"),
            "source_ref": task.get("source_ref"),
            "contract_ref": (task.get("ssot_context") or {}).get("contract_id") if isinstance(task.get("ssot_context"), dict) else "",
            "completion": task.get("todo_completion"),
        }
        for task in plan.get("tasks", [])
        if isinstance(task, dict)
    ]
    (tb_dir / "tb_traceability.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "type": "tb_traceability_matrix",
                "ip": plan.get("ip"),
                "top": plan.get("top"),
                "generated_at": plan.get("generated_at"),
                "rows": trace_rows,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_dynamic_blocker(ip_dir: Path, plan: dict[str, Any]) -> None:
    path = ip_dir / "tb" / "cocotb" / "tb_blocked.json"
    blockers = plan.get("blockers") if isinstance(plan.get("blockers"), list) else []
    if blockers:
        path.parent.mkdir(parents=True, exist_ok=True)
        questions = []
        for blocker in blockers[:64]:
            if not isinstance(blocker, dict):
                continue
            questions.append(
                {
                    "id": blocker.get("id") or "TB_CONTRACT_BLOCKER",
                    "decision_needed": blocker.get("reason") or "Repair TB authority input before generation.",
                    "evidence": blocker.get("source_ref") or "tb/tb_todo_plan.json",
                    "owner": blocker.get("owner") or "ssot-gen",
                    "recommended_default": "Repair the locked req/SSOT/RTL contract source and rerun /gen-tb.",
                }
            )
        path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "type": "ssot_derived_tb_todo_blocker",
                    "status": "blocked",
                    "ip": plan.get("ip"),
                    "reason": "SSOT-derived dynamic TB TODO gate is blocked.",
                    "questions": questions,
                    "next_action": "Repair req/SSOT/RTL authority artifacts and rerun /gen-tb.",
                    "evidence": "tb/tb_todo_plan.json",
                    "timestamp": _utc(),
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        return

    if not path.is_file():
        return
    current = _load_json(path)
    if current.get("type") == "ssot_derived_tb_todo_blocker":
        try:
            path.unlink()
        except OSError:
            pass


def derive_plan(root: Path, ip: str, *, audit_tb: bool = False, audit_evidence: bool = False) -> dict[str, Any]:
    ssot_path, ssot = _load_ssot(root, ip)
    ip_dir = root / ip
    top = _top_name(ssot, ip)
    contracts, contract_issues = _load_locked_contracts(ip_dir, ip)
    goals = _load_json(ip_dir / "verify" / "equivalence_goals.json")
    blockers = contract_issues + _authority_blockers(ip_dir, ssot, contracts)

    tasks: list[dict[str, Any]] = []
    _task(
        tasks,
        category="tb_flow.seed",
        phase="authoring",
        source_ref="top_module",
        title="Read SSOT and build dynamic TB validation ledger",
        detail="Use tb_todo_plan.json as the verification checklist. Fixed templates are generator helpers only, not authority.",
        criteria=[
            "tb_todo_plan.json was regenerated from the current SSOT and locked contracts",
            "Each structural/behavioral contract maps to TB authoring or evidence responsibilities",
            "No expected behavior is inferred from RTL observations",
        ],
        value={"ip": ip, "top": top},
        priority="high",
    )
    _add_gate_tasks(tasks)
    _add_structural_tasks(tasks, contracts.get("structural_contracts", {}), ssot)
    _add_behavioral_contract_tasks(tasks, contracts.get("behavioral_contracts", {}), ssot)
    _add_ssot_model_tasks(tasks, ssot)
    _add_test_coverage_tasks(tasks, ssot, goals)

    counts = Counter(str(task.get("category") or "") for task in tasks)
    by_phase = Counter(str(task.get("phase") or "") for task in tasks)
    behavioral_rows = _as_list((contracts.get("behavioral_contracts") or {}).get("contracts"))
    structural_rows = _as_list((contracts.get("structural_contracts") or {}).get("contracts"))
    plan: dict[str, Any] = {
        "schema_version": 1,
        "type": "ssot_derived_tb_todo_plan",
        "ip": ip,
        "top": top,
        "generated_at": _utc(),
        "source": str(ssot_path.relative_to(root)),
        "summary": {
            "total_tasks": len(tasks),
            "required_tasks": sum(1 for task in tasks if task.get("required", True)),
            "by_category": dict(sorted(counts.items())),
            "by_phase": dict(sorted(by_phase.items())),
            "locked_truth_behavioral_contracts": len(behavioral_rows),
            "locked_truth_structural_contracts": len(structural_rows),
            "equivalence_goals": len(goals.get("goals") if isinstance(goals.get("goals"), list) else []),
            "blocking_questions": len(blockers),
        },
        "policy": {
            "visible_todo_rule": "Expose one visible gen-tb TODO while preserving every per-contract validation row in tb/tb_todo_plan.json.",
            "authority_rule": "Expected behavior comes from locked req contracts plus SSOT Function/Cycle model; RTL is DUT structure only.",
            "timing_rule": "Structural signal timing.kind/clock_domain/sync_to drives TB driver/monitor synchronization when present.",
            "validation_rule": "TB authoring PASS requires --audit-tb; contract validation closure requires --audit-evidence after sim and coverage.",
        },
        "locked_truth_contracts": {
            "present": contracts.get("present", {}),
            "behavioral_contract_ids": [_contract_id(row) for row in behavioral_rows if isinstance(row, dict) and _contract_id(row)],
            "structural_contract_ids": [_contract_id(row) for row in structural_rows if isinstance(row, dict) and _contract_id(row)],
            "load_issues": contract_issues[:32],
        },
        "blockers": blockers,
        "tasks": tasks,
        "todo_completion": {},
        "gate": {},
    }
    _update_completion(
        plan,
        audit_tb=audit_tb,
        audit_evidence=audit_evidence,
        ip_dir=ip_dir,
        ip=ip,
        top=top,
        goals=goals,
        blockers=blockers,
    )
    completion = plan["todo_completion"]
    if blockers:
        status = "blocked"
    elif audit_evidence:
        status = "pass" if completion.get("all_required_todos_pass") else "fail"
    elif audit_tb:
        status = "pass" if completion.get("authoring_todos_pass") else "fail"
    else:
        status = "planned"
    plan["gate"] = {
        "status": status,
        "audit_tb": audit_tb,
        "audit_evidence": audit_evidence,
        "blocking_questions": len(blockers),
        "authoring_open_todos": completion.get("authoring_open_tasks"),
        "validation_open_todos": completion.get("validation_open_tasks"),
        "all_required_todos_pass": completion.get("all_required_todos_pass"),
        "plan_sha256": _stable_hash(plan),
    }
    _write_outputs(ip_dir, plan)
    _write_dynamic_blocker(ip_dir, plan)
    return plan


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ip")
    parser.add_argument("--root", default=os.environ.get("ATLAS_PROJECT_ROOT") or ".")
    parser.add_argument("--ip-root", "--ip_root", dest="ip_root", default=os.environ.get("ATLAS_IP_ROOT") or "")
    parser.add_argument("--audit-tb", action="store_true")
    parser.add_argument("--audit-evidence", action="store_true")
    ns = parser.parse_args()
    audit_tb = bool(ns.audit_tb or ns.audit_evidence)
    root = _resolve_project_root(ns.root, ns.ip_root, ns.ip)
    plan = derive_plan(root, ns.ip, audit_tb=audit_tb, audit_evidence=bool(ns.audit_evidence))
    summary = plan.get("summary") if isinstance(plan.get("summary"), dict) else {}
    gate = plan.get("gate") if isinstance(plan.get("gate"), dict) else {}
    completion = plan.get("todo_completion") if isinstance(plan.get("todo_completion"), dict) else {}
    print(
        "[derive_tb_todos] "
        f"{ns.ip}: tasks={summary.get('total_tasks', 0)} "
        f"blockers={summary.get('blocking_questions', 0)} "
        f"authoring_open={completion.get('authoring_open_tasks', 'unknown')} "
        f"validation_open={completion.get('validation_open_tasks', 'unknown')} "
        f"gate={gate.get('status')}"
    )
    if gate.get("status") == "blocked":
        return 2
    return 1 if gate.get("status") == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
