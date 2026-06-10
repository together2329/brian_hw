#!/usr/bin/env python3
"""Emit generic SSOT-traced FL-vs-RTL equivalence goals.

The output is an artifact contract between FL model generation, TB generation,
sim_debug, and ATLAS progress. It is intentionally IP-agnostic: goals are
derived from SSOT sections and existing FL/decomposition/coverage artifacts,
not from fixed protocol templates.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any

import yaml


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise SystemExit(f"missing SSOT YAML: {path}")
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(doc, dict):
        raise SystemExit(f"invalid SSOT root: {path}")
    return doc


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return doc if isinstance(doc, dict) else {}


def _safe_name(raw: Any, fallback: str) -> str:
    text = str(raw or fallback).strip().upper()
    text = "".join(ch if ch.isalnum() else "_" for ch in text)
    while "__" in text:
        text = text.replace("__", "_")
    return text.strip("_") or fallback.upper()


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _authority_contract(ip: str) -> dict[str, Any]:
    """Describe general evaluation criteria and LLM/human ownership."""
    general_criteria = [
        {
            "id": "traceability",
            "criterion": "Every generated artifact traces to SSOT requirement, function_model, cycle_model, interface, coverage, or quality_gates refs.",
            "machine_evidence": ["source refs in decomposition/equivalence goals", "artifact manifests"],
            "llm_loop_allowed": True,
        },
        {
            "id": "functional_equivalence",
            "criterion": "RTL observable behavior matches FunctionalModel results for every required transaction/scenario.",
            "machine_evidence": ["scoreboard_events.jsonl", "fl_rtl_compare.json"],
            "llm_loop_allowed": True,
        },
        {
            "id": "module_equivalence",
            "criterion": "Each behavior-owning RTL module has module-boundary evidence before top-level signoff.",
            "machine_evidence": ["scope.level=module scoreboard rows", "module goal status"],
            "llm_loop_allowed": True,
        },
        {
            "id": "coverage_closure",
            "criterion": "SSOT coverage goals are hit by passing RTL-observed scoreboard evidence.",
            "machine_evidence": ["fcov_plan.json", "coverage.json", "scoreboard coverage_refs"],
            "llm_loop_allowed": True,
        },
        {
            "id": "interface_protocol",
            "criterion": "Ports, handshakes, ordering, reset, and error protocol obey SSOT io_list/cycle_model/interface contract.",
            "machine_evidence": ["protocol goals", "assertion failures", "waveform evidence"],
            "llm_loop_allowed": True,
        },
        {
            "id": "lint_compile",
            "criterion": "DUT-only RTL compile/lint has zero unwaived errors, warnings, and style diagnostics.",
            "machine_evidence": ["rtl_compile.json", "dut_lint.json"],
            "llm_loop_allowed": True,
        },
        {
            "id": "simulation_evidence",
            "criterion": "Simulation results are fresh, bounded, non-stale, and tied to structured scoreboard goals.",
            "machine_evidence": ["results.xml", "scoreboard_events.jsonl", "stale_evidence checks"],
            "llm_loop_allowed": True,
        },
        {
            "id": "performance_cycle",
            "criterion": "Cycle/performance targets from cycle_model/timing are measured or explicitly escalated.",
            "machine_evidence": ["latency/throughput measurements", "CL/performance sweep reports"],
            "llm_loop_allowed": "candidate_search_only",
        },
        {
            "id": "debug_observability",
            "criterion": "Waveforms and debug probes are sufficient to inspect reset, interface activity, state, outputs, and failures.",
            "machine_evidence": ["VCD/FST presence", "debug_observability goals", "waveform parser summary"],
            "llm_loop_allowed": True,
        },
        {
            "id": "maintainability",
            "criterion": "Generated RTL/TB is structured by SSOT-owned modules, avoids fixed IP templates, and remains reviewable.",
            "machine_evidence": ["module contracts", "dynamic todo plan", "filelist/manifest checks"],
            "llm_loop_allowed": True,
        },
        {
            "id": "human_decision",
            "criterion": "Intent, semantic rule changes, waivers, interface changes, performance tradeoffs, and final signoff are human-owned.",
            "machine_evidence": ["human_gate questions/answers", "approval state"],
            "llm_loop_allowed": False,
        },
    ]
    loopable_evidence_points = [
        {
            "loop": "traceability_closure",
            "criterion": "SSOT refs vs generated artifact refs",
            "llm_action": "Add missing refs/artifact ownership or open a human gate if ownership is undefined.",
        },
        {
            "loop": "rtl_function",
            "criterion": "FunctionalModel.apply expected values vs RTL observed values",
            "llm_action": "Patch RTL and rerun cocotb/sim-debug.",
        },
        {
            "loop": "module_function",
            "criterion": "scope.level=module equivalence goal against RTL module boundary observations",
            "llm_action": "Patch the owning RTL module only.",
        },
        {
            "loop": "coverage_closure",
            "criterion": "coverage goals vs RTL-observed scoreboard coverage rows",
            "llm_action": "Add stimulus/tests/vectors without changing coverage goals.",
        },
        {
            "loop": "lint_compile",
            "criterion": "DUT-only compile/lint diagnostics",
            "llm_action": "Patch RTL syntax, widths, drivers, and coding style.",
        },
        {
            "loop": "assertion_protocol",
            "criterion": "SSOT interface/cycle assertion failure",
            "llm_action": "Patch RTL or TB driver/monitor depending on classified owner.",
        },
        {
            "loop": "cl_performance",
            "criterion": "cycle_model/performance target vs measured latency/throughput",
            "llm_action": "Run parameter/architecture sweeps and report tradeoff candidates.",
        },
        {
            "loop": "regression_minimize",
            "criterion": "minimal vector still reproduces the same failure",
            "llm_action": "Reduce failing stimulus before patching.",
        },
        {
            "loop": "report_root_cause",
            "criterion": "scoreboard diff, logs, coverage miss, and waveform evidence",
            "llm_action": "Write root-cause report and repair prompt.",
        },
    ]
    return {
        "rule": (
            "LLM repair loops are allowed when a general criterion has objective "
            "machine evidence: PASS/FAIL/DIFF, coverage gap, lint diagnostic, "
            "assertion failure, stale evidence, traceability gap, or measured "
            "performance gap. Human gates own intent, semantic rule changes, "
            "waivers, interface changes, performance tradeoffs, and final signoff."
        ),
        "general_evaluation_criteria": general_criteria,
        "locked_artifacts": [
            {
                "name": "requirement",
                "path": f"{ip}/req/",
                "owner": "human",
                "change_rule": "Human owns intent, scope, priority, tradeoffs, and final acceptance.",
            },
            {
                "name": "ssot_spec",
                "path": f"{ip}/yaml/{ip}.ssot.yaml",
                "owner": "human-approved ssot-gen",
                "change_rule": "Behavior, interface, coverage goal, and waiver changes require human gate.",
            },
            {
                "name": "functional_model",
                "path": f"{ip}/model/functional_model.py",
                "owner": "human-approved fl-model-gen",
                "change_rule": "FunctionalModel is the golden oracle; sim-debug cannot change it to match RTL.",
            },
            {
                "name": "coverage_plan",
                "path": f"{ip}/cov/fcov_plan.json",
                "owner": "human-approved fl-model-gen",
                "change_rule": "LLM may add tests to hit bins, but cannot weaken or delete bins without approval.",
            },
            {
                "name": "interface_contract",
                "path": f"{ip}/yaml/{ip}.ssot.yaml#io_list",
                "owner": "human-approved ssot-gen",
                "change_rule": "Protocol and port contract changes require human approval.",
            },
            {
                "name": "performance_target",
                "path": f"{ip}/yaml/{ip}.ssot.yaml#cycle_model",
                "owner": "human-approved ssot-gen",
                "change_rule": "LLM may sweep candidates, but target/tradeoff changes require human approval.",
            },
        ],
        "llm_editable_artifacts": [
            f"{ip}/rtl/",
            f"{ip}/tb/",
            f"{ip}/sim/",
            f"{ip}/reports/",
            f"{ip}/vectors/",
        ],
        "loopable_evidence_points": loopable_evidence_points,
        "loopable_oracles": loopable_evidence_points,
        "non_loopable_decisions": [
            "change requirement intent or scope",
            "change SSOT behavioral rule",
            "change FunctionalModel golden semantics",
            "change coverage goal or waiver",
            "change interface contract",
            "change performance target or architecture tradeoff",
            "final signoff",
        ],
    }


def _rule_list(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        return [{"name": k, "expr": v} for k, v in value.items()]
    return [item for item in _as_list(value) if isinstance(item, dict)]


def _rule_names(rules: list[dict[str, Any]], fallback_prefix: str) -> list[str]:
    names: list[str] = []
    for idx, rule in enumerate(rules):
        name = str(rule.get("name") or rule.get("output") or rule.get("port") or f"{fallback_prefix}_{idx}").strip()
        if name and name not in names:
            names.append(name)
    return names


def _coverage_refs(fcov: dict[str, Any], *needles: str) -> list[str]:
    refs: list[str] = []
    bins = fcov.get("bins") if isinstance(fcov.get("bins"), list) else []
    wanted = [n.lower() for n in needles if n]
    for item in bins:
        if not isinstance(item, dict):
            continue
        hay = " ".join(str(item.get(k) or "") for k in ("id", "class", "source", "scenario", "description")).lower()
        if any(n in hay for n in wanted):
            bid = str(item.get("id") or "").strip()
            if bid and bid not in refs:
                refs.append(bid)
    return refs


def _fcov_bins(fcov: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in _as_list(fcov.get("bins")) if isinstance(item, dict) and str(item.get("id") or "").strip()]


def _unit_refs(decomp: dict[str, Any], *kinds: str) -> list[str]:
    refs: list[str] = []
    wanted = {k.lower() for k in kinds if k}
    for unit in _as_list(decomp.get("units")):
        if not isinstance(unit, dict):
            continue
        kind = str(unit.get("kind") or "").lower()
        if kind in wanted or not wanted:
            name = str(unit.get("name") or kind or "").strip()
            if name and name not in refs:
                refs.append(name)
    return refs


def _goal(
    goal_id: str,
    title: str,
    kind: str,
    ssot_refs: list[str],
    decomposition_refs: list[str],
    coverage_refs: list[str],
    transaction_type: str,
    required_fields: list[str],
    constraints: list[str],
    observables: list[str],
    latency: str,
    state_updates: list[str],
    error_policy: str,
    pass_criteria: list[str],
    *,
    blocked: bool = False,
    blocker: str = "",
    unverified: bool = False,
    default_owner: str = "rtl",
    possible_owners: list[str] | None = None,
    scope: dict[str, Any] | None = None,
    machine_spec: dict[str, Any] | None = None,
) -> dict[str, Any]:
    owners = possible_owners or ["ssot", "fl_model", "rtl", "tb", "coverage", "human"]
    stimulus_contract: dict[str, Any] = {
        "transaction_type": transaction_type,
        "required_fields": required_fields,
        "constraints": constraints,
    }
    if isinstance(machine_spec, dict) and machine_spec:
        stimulus_contract["machine_spec"] = machine_spec
    goal = {
        "goal_id": goal_id,
        "title": title,
        "kind": kind,
        "scope": scope or {"level": "top"},
        "ssot_refs": ssot_refs,
        "decomposition_refs": decomposition_refs,
        "coverage_refs": coverage_refs,
        "stimulus_contract": stimulus_contract,
        "expected_contract": {
            "model_api": "FunctionalModel.apply",
            "observables": observables,
            "latency": latency,
            "state_updates": state_updates,
            "error_policy": error_policy,
        },
        "pass_criteria": pass_criteria,
        "owner_on_fail": {
            "default": default_owner,
            "possible": owners,
        },
        "blocked": bool(blocked),
        "blocker": blocker,
        "unverified": bool(unverified),
    }
    return goal


def _tx_label(tx: dict[str, Any], fallback: str = "primary_behavior") -> str:
    return str(tx.get("name") or tx.get("id") or fallback).strip()


def _tx_norm_text(tx: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("id", "name", "description"):
        value = tx.get(key)
        if value:
            parts.append(str(value))
    for key in ("preconditions", "inputs", "outputs", "side_effects"):
        parts.extend(str(item) for item in _as_list(tx.get(key)) if str(item).strip())
    return " ".join(parts).lower().replace("_", " ").replace("-", " ")


def _select_primary_transaction(txs: list[dict[str, Any]]) -> dict[str, Any]:
    """Pick a useful nominal transaction instead of blindly using tx[0].

    SSOTs often list clear/reset/hold before the main operation. Scenario and
    coverage closure goals should exercise the nominal behavior path when the
    scenario only says "primary".
    """
    if not txs:
        return {}
    preferred_tokens = ("primary", "start", "accept", "request", "transfer", "command", "packet", "operation")
    avoid_tokens = ("reset", "clear", "hold", "idle", "error", "fault", "unsupported")
    for tx in txs:
        text = _tx_norm_text(tx)
        if any(token in text for token in preferred_tokens) and not any(token in text for token in ("reset", "error", "fault")):
            return tx
    for tx in txs:
        text = _tx_norm_text(tx)
        if not any(token in text for token in avoid_tokens):
            return tx
    return txs[0]


def _transaction_contract_from_tx(tx: dict[str, Any], *, fallback: str = "primary_behavior") -> dict[str, Any]:
    name = _tx_label(tx, fallback)
    outputs = [str(x) for x in _as_list(tx.get("outputs")) if str(x).strip()]
    output_rule_names = _rule_names(_rule_list(tx.get("output_rules")), "output")
    side_effects = [str(x) for x in _as_list(tx.get("side_effects")) if str(x).strip()]
    state_updates = _rule_names(_rule_list(tx.get("state_updates")), "state")
    required_fields = [str(x) for x in _as_list(tx.get("required_fields")) if str(x).strip()]
    error_cases = [str(x) for x in _as_list(tx.get("error_cases")) if str(x).strip()]
    preconditions = [str(x) for x in _as_list(tx.get("preconditions")) if str(x).strip()]
    observables = outputs + [item for item in output_rule_names if item not in outputs]
    structured_state = side_effects + [item for item in state_updates if item not in side_effects]
    return {
        "transaction_type": name,
        "required_fields": ["kind"] + [field for field in required_fields if field != "kind"],
        "constraints": preconditions,
        "observables": observables or ["FunctionalModel result payload"],
        "state_updates": structured_state,
        "error_policy": "; ".join(error_cases),
        "blocked": not observables and not structured_state and not error_cases,
    }


def _primary_transaction_contract(ssot: dict[str, Any]) -> dict[str, Any]:
    fm = ssot.get("function_model") if isinstance(ssot.get("function_model"), dict) else {}
    txs = [tx for tx in _as_list(fm.get("transactions")) if isinstance(tx, dict)]
    if not txs:
        return {
            "transaction_type": "undefined",
            "required_fields": [],
            "constraints": [],
            "observables": [],
            "state_updates": [],
            "error_policy": "",
            "blocked": True,
        }
    return _transaction_contract_from_tx(_select_primary_transaction(txs))


def _scenario_transaction_contract(ssot: dict[str, Any], sc: dict[str, Any], sid: str) -> dict[str, Any]:
    fm = ssot.get("function_model") if isinstance(ssot.get("function_model"), dict) else {}
    txs = [tx for tx in _as_list(fm.get("transactions")) if isinstance(tx, dict)]
    if not txs:
        return {
            "transaction_type": sid,
            "required_fields": ["scenario_id", "kind"],
            "constraints": [],
            "observables": ["Scenario expected result from SSOT"],
            "state_updates": [],
            "error_policy": "",
            "blocked": True,
        }
    scenario_text = " ".join(
        str(sc.get(key) or "")
        for key in ("id", "name", "stimulus", "expected", "checker")
    ).lower().replace("_", " ").replace("-", " ")
    for item in _as_list(sc.get("coverage")):
        scenario_text += " " + str(item).lower().replace("_", " ").replace("-", " ")
    for tx in txs:
        aliases = [
            str(tx.get("id") or "").lower().replace("_", " ").replace("-", " "),
            str(tx.get("name") or "").lower().replace("_", " ").replace("-", " "),
        ]
        if any(alias and alias in scenario_text for alias in aliases):
            return _transaction_contract_from_tx(tx)
    if "primary" in scenario_text or "nominal" in scenario_text or "legal" in scenario_text:
        return _primary_transaction_contract(ssot)
    return {
        "transaction_type": sid,
        "required_fields": ["scenario_id", "kind"],
        "constraints": [],
        "observables": ["Scenario expected result from SSOT"],
        "state_updates": [],
        "error_policy": "",
        "blocked": False,
    }


def _transaction_goals(ssot: dict[str, Any], decomp: dict[str, Any], fcov: dict[str, Any]) -> list[dict[str, Any]]:
    fm = ssot.get("function_model") if isinstance(ssot.get("function_model"), dict) else {}
    goals: list[dict[str, Any]] = []
    for idx, tx in enumerate(_as_list(fm.get("transactions"))):
        if not isinstance(tx, dict):
            continue
        name = str(tx.get("name") or tx.get("id") or f"transaction_{idx}").strip()
        gid = f"EQ_TRANSACTION_{_safe_name(tx.get('id') or name, str(idx + 1).zfill(3))}"
        outputs = [str(x) for x in _as_list(tx.get("outputs")) if str(x).strip()]
        output_rules = _rule_list(tx.get("output_rules"))
        output_rule_names = _rule_names(output_rules, "output")
        side_effects = [str(x) for x in _as_list(tx.get("side_effects")) if str(x).strip()]
        state_updates = _rule_names(_rule_list(tx.get("state_updates")), "state")
        error_cases = [str(x) for x in _as_list(tx.get("error_cases")) if str(x).strip()]
        preconditions = [str(x) for x in _as_list(tx.get("preconditions")) if str(x).strip()]
        observables = outputs + [name for name in output_rule_names if name not in outputs]
        structured_state = side_effects + [name for name in state_updates if name not in side_effects]
        required_fields = [str(x) for x in _as_list(tx.get("required_fields")) if str(x).strip()]
        blocked = not observables and not structured_state and not error_cases
        goals.append(_goal(
            gid,
            f"Transaction {name} matches FunctionalModel",
            "transaction",
            [f"function_model.transactions[{idx}]"],
            _unit_refs(decomp, "protocol", "register", "memory", "datapath", "fsm", "error"),
            _coverage_refs(fcov, str(tx.get("id") or ""), name),
            name,
            ["kind"] + [field for field in required_fields if field != "kind"],
            preconditions,
            observables or ["FunctionalModel result payload"],
            "cycle_model latency/ordering must hold when applicable",
            structured_state,
            "; ".join(error_cases),
            [
                "Scoreboard calls FunctionalModel.apply with the same transaction intent",
                "RTL observed outputs equal FL expected outputs",
                "RTL side effects match FL model state updates",
                "Linked functional coverage bins are hit when stimulus executes",
            ],
            blocked=blocked,
            blocker="function_model transaction lacks output_rules/outputs, state_updates/side_effects, and error_cases" if blocked else "",
            # CAND-06: transaction goals were the only FL-vs-RTL goals without a
            # stimulus channel — preconditions like "CTRL.ENABLE==1" need real
            # CSR writes the generic input vector cannot express, so CSR-gated
            # behavior could never close without a hand-written TB. A
            # function_model transaction may now declare its own
            # stimulus_machine_spec (same timeline schema as scenarios).
            machine_spec=tx.get("stimulus_machine_spec") if isinstance(tx.get("stimulus_machine_spec"), dict) else None,
        ))
    return goals


def _scenario_goals(ssot: dict[str, Any], decomp: dict[str, Any], fcov: dict[str, Any]) -> list[dict[str, Any]]:
    tr = ssot.get("test_requirements") if isinstance(ssot.get("test_requirements"), dict) else {}
    goals: list[dict[str, Any]] = []
    for idx, sc in enumerate(_as_list(tr.get("scenarios"))):
        if not isinstance(sc, dict):
            continue
        sid = str(sc.get("id") or f"SC{idx + 1:02d}").strip()
        name = str(sc.get("name") or sid).strip()
        stimulus = str(sc.get("stimulus") or "").strip()
        expected = str(sc.get("expected") or "").strip()
        checker = str(sc.get("checker") or "").strip()
        tx_contract = _scenario_transaction_contract(ssot, sc, sid)
        blocked = not stimulus or not expected or not checker
        goals.append(_goal(
            f"EQ_SCENARIO_{_safe_name(sid, str(idx + 1).zfill(3))}",
            f"Scenario {sid}: {name}",
            "transaction",
            [f"test_requirements.scenarios[{idx}]"],
            _unit_refs(decomp),
            _coverage_refs(fcov, sid, name),
            str(tx_contract["transaction_type"]),
            ["scenario_id"] + [
                field for field in list(tx_contract["required_fields"])
                if field not in {"scenario_id"}
            ],
            ([stimulus] if stimulus else []) + list(tx_contract["constraints"]),
            ([expected] if expected else []) + [
                item for item in list(tx_contract["observables"])
                if item not in {expected}
            ],
            "cycle_model latency/handshake constraints apply to the scenario",
            list(tx_contract["state_updates"]),
            str(tx_contract["error_policy"]),
            [
                "Generated sequence executes the SSOT stimulus",
                "Scoreboard expected result comes from FunctionalModel.apply and SSOT scenario expected field",
                "RTL observed result matches expected result",
                "Scenario coverage bin is hit",
            ],
            blocked=blocked or bool(tx_contract["blocked"]),
            blocker=(
                "scenario must define stimulus, expected, and checker"
                if blocked
                else (
                    "scenario references a FunctionalModel transaction without executable observables/state/error behavior"
                    if tx_contract["blocked"] else ""
                )
            ),
            machine_spec=sc.get("stimulus_machine_spec") if isinstance(sc.get("stimulus_machine_spec"), dict) else None,
        ))
    return goals


def _cycle_goals(ssot: dict[str, Any], decomp: dict[str, Any], fcov: dict[str, Any]) -> list[dict[str, Any]]:
    cm = ssot.get("cycle_model") if isinstance(ssot.get("cycle_model"), dict) else {}
    goals: list[dict[str, Any]] = []
    for idx, rule in enumerate(_as_list(cm.get("handshake_rules"))):
        if not isinstance(rule, dict):
            continue
        name = str(rule.get("name") or rule.get("id") or f"handshake_{idx}").strip()
        desc = str(rule.get("description") or rule).strip()
        goals.append(_goal(
            f"EQ_PROTOCOL_{_safe_name(name, str(idx + 1).zfill(3))}",
            f"Cycle/handshake rule {name}",
            "protocol",
            [f"cycle_model.handshake_rules[{idx}]"],
            _unit_refs(decomp, "protocol", "fsm"),
            _coverage_refs(fcov, name, "handshake", "protocol"),
            name,
            ["cycle", "observed_signals"],
            [desc],
            ["ready/valid/control observables named by SSOT and DUT ports"],
            str(cm.get("latency") or "cycle_model defined latency"),
            [],
            "",
            [
                "RTL holds payload/control stability according to cycle_model",
                "Handshake completion timing matches cycle_model latency/ordering",
                "Protocol coverage bin is hit",
            ],
        ))
    for idx, rule in enumerate(_as_list(cm.get("ordering"))):
        desc = str(rule.get("description") if isinstance(rule, dict) else rule).strip()
        name = str(rule.get("name") or rule.get("id") if isinstance(rule, dict) else f"ordering_{idx}").strip()
        goals.append(_goal(
            f"EQ_TIMING_{_safe_name(name, str(idx + 1).zfill(3))}",
            f"Ordering rule {name}",
            "timing",
            [f"cycle_model.ordering[{idx}]"],
            _unit_refs(decomp, "protocol", "fsm", "datapath"),
            _coverage_refs(fcov, name, "ordering"),
            name,
            ["cycle", "transaction_order"],
            [desc] if desc else [],
            ["ordered RTL observable sequence"],
            str(cm.get("latency") or "cycle_model defined latency"),
            [],
            "",
            [
                "RTL response order matches cycle_model ordering",
                "FL trace and RTL monitor trace preserve the same transaction order",
            ],
        ))
    return goals


def _register_memory_error_goals(ssot: dict[str, Any], decomp: dict[str, Any], fcov: dict[str, Any]) -> list[dict[str, Any]]:
    goals: list[dict[str, Any]] = []
    regs = ssot.get("registers") if isinstance(ssot.get("registers"), dict) else {}
    for idx, reg in enumerate(_as_list(regs.get("register_list"))):
        if not isinstance(reg, dict):
            continue
        name = str(reg.get("name") or reg.get("offset") or f"reg_{idx}").strip()
        goals.append(_goal(
            f"EQ_REGISTER_{_safe_name(name, str(idx + 1).zfill(3))}",
            f"Register access {name}",
            "register",
            [f"registers.register_list[{idx}]"],
            _unit_refs(decomp, "register"),
            _coverage_refs(fcov, name, "register"),
            "csr_access",
            ["op", "addr_or_name"],
            [str(reg)],
            ["read data", "write response", "side effects"],
            "register access latency from cycle_model/integration",
            ["register mirror update when writable"],
            "",
            [
                "RTL read/write response matches FunctionalModel register behavior",
                "Writable fields update as SSOT describes",
                "Read-only/reserved/error policies match SSOT",
            ],
        ))

    mem = ssot.get("memory") if isinstance(ssot.get("memory"), dict) else {}
    for idx, inst in enumerate(_as_list(mem.get("instances"))):
        if not isinstance(inst, dict):
            continue
        name = str(inst.get("name") or f"memory_{idx}").strip()
        goals.append(_goal(
            f"EQ_MEMORY_{_safe_name(name, str(idx + 1).zfill(3))}",
            f"Memory behavior {name}",
            "memory",
            [f"memory.instances[{idx}]"],
            _unit_refs(decomp, "memory"),
            _coverage_refs(fcov, name, "memory"),
            "memory_access",
            ["op", "addr", "data"],
            [str(inst)],
            ["read data", "write response", "retention"],
            "memory latency from cycle_model",
            ["memory contents"],
            "",
            [
                "RTL memory read/write behavior matches FunctionalModel state",
                "Byte-lane, boundary, and retention behavior match SSOT",
            ],
        ))

    err = ssot.get("error_handling") if isinstance(ssot.get("error_handling"), dict) else {}
    for idx, src in enumerate(_as_list(err.get("error_sources"))):
        name = str(src.get("name") if isinstance(src, dict) else src or f"error_{idx}").strip()
        goals.append(_goal(
            f"EQ_ERROR_{_safe_name(name, str(idx + 1).zfill(3))}",
            f"Error policy {name}",
            "error",
            [f"error_handling.error_sources[{idx}]"],
            _unit_refs(decomp, "error", "protocol"),
            _coverage_refs(fcov, name, "error"),
            name,
            ["fault_condition"],
            [str(src)],
            ["error response", "status/interrupt/debug observable"],
            "error propagation timing from cycle_model",
            ["error state/counter/status update"],
            str(err.get("propagation") or ""),
            [
                "Fault stimulus produces the SSOT-defined error response",
                "No illegal side effect occurs unless SSOT allows it",
                "Error coverage bin is hit",
            ],
        ))
    return goals


def _fsm_debug_goals(ssot: dict[str, Any], decomp: dict[str, Any], fcov: dict[str, Any]) -> list[dict[str, Any]]:
    goals: list[dict[str, Any]] = []
    fsm = ssot.get("fsm") if isinstance(ssot.get("fsm"), dict) else {}
    for block_name, block in fsm.items():
        if not isinstance(block, dict):
            continue
        for idx, transition in enumerate(_as_list(block.get("transitions"))):
            if not isinstance(transition, dict):
                continue
            src = str(transition.get("from") or "from").strip()
            dst = str(transition.get("to") or "to").strip()
            name = f"{block_name}_{src}_to_{dst}_{idx}"
            goals.append(_goal(
                f"EQ_STATE_{_safe_name(name, str(idx + 1).zfill(3))}",
                f"FSM transition {block_name}: {src} -> {dst}",
                "state",
                [f"fsm.{block_name}.transitions[{idx}]"],
                _unit_refs(decomp, "fsm"),
                _coverage_refs(fcov, block_name, src, dst),
                name,
                ["pre_state", "stimulus"],
                [str(transition.get("condition") or "")],
                ["next state", "state-dependent outputs"],
                "next-state timing from cycle_model pipeline/latency",
                [f"{block_name} state"],
                "",
                [
                    "RTL state transition matches SSOT condition",
                    "FSM transition coverage bin is hit",
                ],
            ))

    dbg = ssot.get("debug_observability") if isinstance(ssot.get("debug_observability"), dict) else {}
    probes = _as_list(dbg.get("waveform_must_probe"))
    if probes:
        goals.append(_goal(
            "EQ_DEBUG_OBSERVABILITY",
            "Required debug/waveform observability exists",
            "coverage",
            ["debug_observability.waveform_must_probe"],
            _unit_refs(decomp, "protocol", "register", "datapath", "fsm", "error"),
            _coverage_refs(fcov, "debug", "observability"),
            "debug_probe_capture",
            ["waveform_path"],
            [str(p) for p in probes],
            ["waveform contains required probes"],
            "throughout simulation window",
            [],
            "",
            [
                "Waveform includes SSOT-required debug probes",
                "sim_debug can inspect those probes around checked scenarios",
            ],
            possible_owners=["tb", "coverage", "rtl", "ssot", "human"],
        ))
    return goals


def _coverage_closure_goals(
    ssot: dict[str, Any],
    decomp: dict[str, Any],
    fcov: dict[str, Any],
    existing_goals: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Ensure every SSOT-planned functional bin has an executable owner.

    Coverage bins are part of the SSOT-derived verification contract. If a bin
    is not referenced by a transaction/scenario/protocol goal, TB generation has
    no generic way to hit it and the coverage stage will correctly block. These
    closure goals keep the source of truth in fcov_plan.json while creating an
    explicit FL-vs-RTL/TB path for otherwise orphan planned bins.
    """
    referenced = {
        str(ref)
        for goal in existing_goals
        if isinstance(goal, dict)
        for ref in _as_list(goal.get("coverage_refs"))
        if str(ref).strip()
    }
    contract = _primary_transaction_contract(ssot)
    goals: list[dict[str, Any]] = []
    for idx, item in enumerate(_fcov_bins(fcov)):
        bid = str(item.get("id") or "").strip()
        if not bid or bid in referenced:
            continue
        source = str(item.get("source") or "cov/fcov_plan.json").strip()
        description = str(item.get("description") or item.get("class") or bid).strip()
        goals.append(_goal(
            f"EQ_COVERAGE_{_safe_name(bid, str(idx + 1).zfill(3))}",
            f"Functional coverage bin {bid}: {description}",
            "coverage",
            [source],
            _unit_refs(decomp),
            [bid],
            str(contract["transaction_type"]),
            list(contract["required_fields"]),
            list(contract["constraints"]) + [description],
            list(contract["observables"]),
            "cycle_model latency/handshake constraints apply to coverage stimulus",
            list(contract["state_updates"]),
            str(contract["error_policy"]),
            [
                "Generated stimulus executes an SSOT-derived behavior path",
                "Scoreboard expected result comes from FunctionalModel.apply",
                "Coverage collector samples this planned bin only after the scoreboard row passes",
            ],
            blocked=bool(contract["blocked"]),
            blocker=(
                "coverage bin has no executable FunctionalModel transaction contract"
                if contract["blocked"] else ""
            ),
            default_owner="coverage",
            possible_owners=["ssot", "fl_model", "tb", "coverage", "human"],
        ))
    return goals


def _module_contracts(decomp: dict[str, Any]) -> list[dict[str, Any]]:
    raw = decomp.get("module_contracts")
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    contracts: list[dict[str, Any]] = []
    for unit in _as_list(decomp.get("units")):
        if not isinstance(unit, dict) or unit.get("kind") != "rtl_module":
            continue
        contracts.append({
            "name": unit.get("name"),
            "rtl_module": unit.get("rtl_module") or unit.get("name"),
            "rtl_file": unit.get("rtl_file"),
            "ssot_refs": unit.get("ssot_refs") or unit.get("source_sections") or [],
            "function_model_refs": unit.get("function_model_refs") or [],
            "cycle_model_refs": unit.get("cycle_model_refs") or [],
            "requires_module_equivalence": unit.get("requires_module_equivalence", True),
            "blocked": unit.get("blocked", False),
            "blocker": unit.get("blocker", ""),
        })
    return contracts


def _module_equivalence_goals(ssot: dict[str, Any], decomp: dict[str, Any], fcov: dict[str, Any]) -> list[dict[str, Any]]:
    """Create one exact-functionality equivalence goal for each RTL owner module.

    These goals are deliberately not style/structure checks.  They require the
    same stimulus intent to produce the same FunctionalModel result at the RTL
    module boundary, or an explicit SSOT blocker if that boundary is undefined.
    """
    tx_contract = _primary_transaction_contract(ssot)
    goals: list[dict[str, Any]] = []
    for idx, contract in enumerate(_module_contracts(decomp)):
        name = str(contract.get("name") or contract.get("rtl_module") or f"module_{idx}").strip()
        rtl_module = str(contract.get("rtl_module") or name).strip()
        rtl_file = str(contract.get("rtl_file") or "").strip()
        ssot_refs = [str(ref) for ref in _as_list(contract.get("ssot_refs")) if str(ref).strip()]
        function_refs = [str(ref) for ref in _as_list(contract.get("function_model_refs")) if str(ref).strip()]
        cycle_refs = [str(ref) for ref in _as_list(contract.get("cycle_model_refs")) if str(ref).strip()]
        requires = contract.get("requires_module_equivalence") is not False
        if not requires:
            continue
        structural_blocked = (
            bool(contract.get("blocked"))
            or bool(tx_contract["blocked"])
        )
        unverified = (not function_refs) and not structural_blocked
        blocked = structural_blocked
        blocker_bits: list[str] = []
        if contract.get("blocker"):
            blocker_bits.append(str(contract.get("blocker")))
        if tx_contract["blocked"]:
            blocker_bits.append("FunctionalModel transaction contract lacks executable observables/state/error behavior")
        if not function_refs:
            blocker_bits.append("[unverified] module owns no function_model refs, so exact functionality cannot be compared (advisory; downstream stages proceed but module-equivalence is not enforced)")
        scope = {
            "level": "module",
            "rtl_module": rtl_module,
            "rtl_file": rtl_file,
            "boundary": "module RTL observable outputs must be compared against FunctionalModel.apply",
        }
        goals.append(_goal(
            f"EQ_MODULE_{_safe_name(rtl_module or name, str(idx + 1).zfill(3))}",
            f"Module {rtl_module or name} functionality equals FunctionalModel",
            "module",
            ssot_refs or function_refs or cycle_refs,
            [name],
            _coverage_refs(fcov, name, rtl_module, "module"),
            str(tx_contract["transaction_type"]),
            list(tx_contract["required_fields"]),
            list(tx_contract["constraints"]) + [
                "Use the module boundary stimulus/monitor contract from SSOT decomposition; do not compare against RTL-internal self-derived expected values."
            ],
            list(tx_contract["observables"]),
            str(tx_contract["latency"]) if "latency" in tx_contract else "cycle_model latency/ordering must hold at the module boundary",
            list(tx_contract["state_updates"]),
            str(tx_contract["error_policy"]),
            [
                "Drive the RTL module boundary with stimulus derived from the same SSOT transaction intent used for FunctionalModel.apply",
                "Observe only RTL module boundary outputs/state exposed by SSOT or rtl_contract",
                "Compare RTL observed values against FunctionalModel.apply output; do not copy FL expected into rtl_observed",
                "Record a scoreboard row for this module goal before top-level signoff",
            ],
            blocked=blocked,
            blocker="; ".join(blocker_bits),
            unverified=unverified,
            scope=scope,
        ))
    return goals


def _missing_contract_goals(ssot: dict[str, Any]) -> list[dict[str, Any]]:
    goals: list[dict[str, Any]] = []
    if not isinstance(ssot.get("function_model"), dict) or not _as_list(ssot.get("function_model", {}).get("transactions")):
        goals.append(_goal(
            "EQ_BLOCKED_FUNCTION_MODEL",
            "Functional model transaction contract is missing",
            "coverage",
            ["function_model"],
            [],
            [],
            "undefined",
            [],
            [],
            [],
            "undefined",
            [],
            "",
            ["Human-approved SSOT must define executable function_model transactions"],
            blocked=True,
            blocker="SSOT function_model.transactions is missing or empty",
            possible_owners=["ssot", "human"],
        ))
    if not isinstance(ssot.get("cycle_model"), dict):
        goals.append(_goal(
            "EQ_BLOCKED_CYCLE_MODEL",
            "Cycle model contract is missing",
            "timing",
            ["cycle_model"],
            [],
            [],
            "undefined",
            [],
            [],
            [],
            "undefined",
            [],
            "",
            ["Human-approved SSOT must define cycle_model timing/order rules"],
            blocked=True,
            blocker="SSOT cycle_model is missing",
            possible_owners=["ssot", "human"],
        ))
    return goals


def _dedupe(goals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for goal in goals:
        gid = str(goal.get("goal_id") or "").strip()
        if not gid or gid in seen:
            continue
        seen.add(gid)
        out.append(goal)
    return out


def emit(ip: str, root: Path) -> dict[str, Any]:
    ip_dir = root / ip
    ssot_path = ip_dir / "yaml" / f"{ip}.ssot.yaml"
    model_path = ip_dir / "model" / "functional_model.py"
    decomp_path = ip_dir / "model" / "decomposition.json"
    fcov_path = ip_dir / "cov" / "fcov_plan.json"

    ssot = _load_yaml(ssot_path)
    decomp = _load_json(decomp_path)
    fcov = _load_json(fcov_path)

    base_goals = (
        _missing_contract_goals(ssot)
        + _transaction_goals(ssot, decomp, fcov)
        + _scenario_goals(ssot, decomp, fcov)
        + _cycle_goals(ssot, decomp, fcov)
        + _register_memory_error_goals(ssot, decomp, fcov)
        + _fsm_debug_goals(ssot, decomp, fcov)
        + _module_equivalence_goals(ssot, decomp, fcov)
    )
    goals = _dedupe(base_goals + _coverage_closure_goals(ssot, decomp, fcov, base_goals))
    # Tag each goal with a `sample_cycle` derived from cycle_model.pipeline.
    # Opt-in via SSOT.cycle_model.use_per_cycle_expected: true. This keeps
    # auto-tagging off for IPs whose cycle_model.pipeline.output_rules
    # expressions reference signals that the cocotb stimulus does not yet
    # propagate by name (e.g. arbiter_rr's `req_i` vs stimulus field
    # `requests`), and lets uart-class IPs opt in once their output_rules
    # use constants or already-resolved env names.
    _cycle_model = ssot.get("cycle_model") if isinstance(ssot.get("cycle_model"), dict) else {}
    if bool(_cycle_model.get("use_per_cycle_expected", False)):
        _pipeline = _cycle_model.get("pipeline") or []
        _abs_cycles: list[int] = []
        _stage_cycle: dict[str, int] = {}
        for _entry in _pipeline:
            if not isinstance(_entry, dict):
                continue
            _raw = _entry.get("cycle")
            _cnum: int | None = None
            if isinstance(_raw, int):
                _cnum = _raw
            elif isinstance(_raw, str) and _raw.strip().isdigit():
                _cnum = int(_raw.strip())
            if _cnum is not None:
                _abs_cycles.append(_cnum)
                _sname = _entry.get("stage")
                if isinstance(_sname, str) and _sname:
                    _stage_cycle[_sname] = _cnum
        # Build transaction id -> sample_stage map from SSOT (opt-in field).
        _tx_stage: dict[str, str] = {}
        for _tx in (ssot.get("function_model") or {}).get("transactions") or []:
            if isinstance(_tx, dict):
                _sst = _tx.get("sample_stage")
                if isinstance(_sst, str) and _sst:
                    for _key in (_tx.get("id"), _tx.get("name")):
                        if _key:
                            _tx_stage[str(_key)] = _sst
        if _abs_cycles:
            _sample_cycle_default = max(_abs_cycles)
            for _g in goals:
                if not isinstance(_g, dict) or "sample_cycle" in _g:
                    continue
                # Resolve per-transaction sample_stage first; an explicit
                # sample_stage authored by the SSOT means the IP author has
                # committed to a stable comparison point regardless of
                # stimulus shape (e.g. FM_TX_BYTE -> TX_START), so honor it.
                _per_goal: int | None = None
                gid = str(_g.get("goal_id") or "")
                tx_payload = _g.get("transaction") if isinstance(_g.get("transaction"), dict) else None
                tx_kind = str(tx_payload.get("kind") or "") if tx_payload else ""
                stage = _tx_stage.get(tx_kind) if tx_kind else None
                if stage is None and gid.startswith("EQ_TRANSACTION_"):
                    tail = gid[len("EQ_TRANSACTION_"):]
                    for _k, _v in _tx_stage.items():
                        if _safe_name(_k, _k).upper() == tail.upper():
                            stage = _v
                            break
                if stage and stage in _stage_cycle:
                    _per_goal = _stage_cycle[stage]
                    _g["sample_cycle"] = _per_goal
                    continue
                # No sample_stage match: only auto-tag default sample_cycle
                # when this goal has a real stimulus_machine_spec
                # (assign / csr_writes / timeline). Without machine_spec,
                # RTL stays idle and cycle_view comparison against SSOT
                # pipeline.output_rules produces false negatives (expected
                # "TX_START drives 0" vs observed "TX_IDLE driving 1").
                # model_result is the right verdict for unsequenced goals.
                _ms = (
                    _g.get("stimulus_contract", {}).get("machine_spec")
                    if isinstance(_g.get("stimulus_contract"), dict)
                    else None
                )
                _has_ms = bool(
                    isinstance(_ms, dict)
                    and (_ms.get("assign") or _ms.get("csr_writes") or _ms.get("timeline"))
                )
                if _has_ms:
                    _g["sample_cycle"] = _sample_cycle_default
    blocked = sum(1 for g in goals if g.get("blocked"))
    unverified = sum(1 for g in goals if g.get("unverified"))
    required = sum(1 for g in goals if not g.get("blocked"))
    module_goals = [g for g in goals if isinstance(g.get("scope"), dict) and g["scope"].get("level") == "module"]
    doc = {
        "ip": ip,
        "schema_version": 1,
        "type": "fl_rtl_equivalence_goals",
        "source_of_truth": {
            "ssot": f"{ip}/yaml/{ip}.ssot.yaml",
            "functional_model": f"{ip}/model/functional_model.py",
            "functional_model_exists": model_path.is_file(),
            "cycle_model_section": "cycle_model",
            "decomposition": f"{ip}/model/decomposition.json",
            "coverage_plan": f"{ip}/cov/fcov_plan.json",
            "authority_contract": _authority_contract(ip),
        },
        "summary": {
            "total": len(goals),
            "required": required,
            "optional": 0,
            "blocked": blocked,
            "unverified": unverified,
            "module_total": len(module_goals),
            "module_required": sum(1 for g in module_goals if g.get("blocked") is not True),
            "module_blocked": sum(1 for g in module_goals if g.get("blocked") is True),
            "module_unverified": sum(1 for g in module_goals if g.get("unverified") is True),
        },
        "goals": goals,
    }
    out = ip_dir / "verify" / "equivalence_goals.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    return doc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ip")
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    doc = emit(args.ip, root)
    summary = doc["summary"]
    print(f"[emit_equivalence_goals] wrote {args.ip}/verify/equivalence_goals.json")
    print(
        "[emit_equivalence_goals] "
        f"total={summary['total']} required={summary['required']} "
        f"blocked={summary['blocked']} unverified={summary.get('unverified', 0)}"
    )
    return 0 if int(summary.get("total") or 0) > 0 and int(summary.get("blocked") or 0) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
