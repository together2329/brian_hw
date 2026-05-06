#!/usr/bin/env python3
"""Generate executable SSOT functional-model artifacts.

The generated model is intentionally SSOT-driven and independent from RTL.
It provides a transaction-level reference that TB scoreboards can import.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import time
from pathlib import Path
from typing import Any

import yaml


def _load_ssot(ip_dir: Path, ip: str) -> dict[str, Any]:
    path = ip_dir / "yaml" / f"{ip}.ssot.yaml"
    if not path.is_file():
        raise SystemExit(f"missing SSOT YAML: {path}")
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise SystemExit(f"invalid SSOT YAML root: {path}")
    return data


def _param_map(ssot: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    params = ssot.get("parameters")
    if isinstance(params, list):
        for item in params:
            if isinstance(item, dict) and item.get("name"):
                out[str(item["name"])] = item.get("default")
    return out


def _safe_name(raw: Any, fallback: str) -> str:
    text = str(raw or fallback).strip().lower()
    text = "".join(ch if ch.isalnum() else "_" for ch in text)
    while "__" in text:
        text = text.replace("__", "_")
    return text.strip("_") or fallback


def _scenario_bins(ssot: dict[str, Any]) -> list[dict[str, Any]]:
    tr = ssot.get("test_requirements") if isinstance(ssot.get("test_requirements"), dict) else {}
    scenarios = tr.get("scenarios") if isinstance(tr.get("scenarios"), list) else []
    bins: list[dict[str, Any]] = []
    for idx, sc in enumerate(scenarios, 1):
        if not isinstance(sc, dict):
            continue
        sid = str(sc.get("id") or f"SC{idx:02d}")
        bins.append({
            "id": f"{sid}_executed",
            "class": "scenario",
            "source": f"test_requirements.scenarios[{idx - 1}]",
            "scenario": sid,
            "description": str(sc.get("name") or sc.get("expected") or sid),
        })
    return bins


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return [{"name": key, "value": val} for key, val in value.items()]
    return [value]


def _authority_contract(ip: str) -> dict[str, Any]:
    general_criteria = [
        "traceability: every generated artifact traces to SSOT refs",
        "functional_equivalence: RTL observables match FunctionalModel results",
        "module_equivalence: behavior-owning modules have module-boundary evidence",
        "coverage_closure: SSOT coverage goals are hit by passing RTL-observed evidence",
        "interface_protocol: io_list/cycle_model handshakes, reset, ordering, and errors hold",
        "lint_compile: DUT-only compile/lint has zero unwaived diagnostics",
        "simulation_evidence: results, scoreboard rows, and coverage are fresh and structured",
        "performance_cycle: cycle/performance targets are measured or escalated",
        "debug_observability: waveform/probe evidence is inspectable",
        "maintainability: no fixed IP workaround; modules/TB remain SSOT-owned and reviewable",
        "human_decision: intent, waivers, oracle changes, tradeoffs, and final signoff are human-owned",
    ]
    loopable_evidence_points = [
        "traceability gap",
        "FL expected vs RTL actual diff",
        "module FL expected vs RTL boundary actual diff",
        "coverage goal vs coverage result gap",
        "lint/compile diagnostic",
        "interface/cycle assertion failure",
        "CL target vs measured performance gap",
        "minimal regression reproducer",
        "report/root-cause evidence gap",
    ]
    return {
        "rule": (
            "LLM loops are allowed against general machine-checkable criteria "
            "(diffs, diagnostics, coverage gaps, traceability gaps, stale evidence, "
            "assertions, and measurements). Intended behavior, oracle semantics, "
            "waivers, interface changes, performance tradeoffs, and signoff require human approval."
        ),
        "general_evaluation_criteria": general_criteria,
        "locked_artifacts": [
            f"{ip}/req/",
            f"{ip}/yaml/{ip}.ssot.yaml",
            f"{ip}/model/functional_model.py",
            f"{ip}/cov/fcov_plan.json",
            f"{ip}/yaml/{ip}.ssot.yaml#io_list",
            f"{ip}/yaml/{ip}.ssot.yaml#cycle_model",
        ],
        "llm_editable_artifacts": [
            f"{ip}/rtl/",
            f"{ip}/tb/",
            f"{ip}/sim/",
            f"{ip}/vectors/",
            f"{ip}/reports/",
        ],
        "loopable_evidence_points": loopable_evidence_points,
        "loopable_oracles": loopable_evidence_points,
        "human_gate_required_for": [
            "requirement intent/scope change",
            "SSOT behavior or waiver change",
            "FunctionalModel golden semantic change",
            "coverage goal change",
            "interface contract change",
            "performance target/tradeoff change",
            "final signoff",
        ],
    }


def _module_file(ip: str, top: str, module: dict[str, Any]) -> str:
    rel = str(module.get("file") or "").strip()
    if rel:
        return rel
    name = str(module.get("name") or top or ip).strip()
    return f"rtl/{name}.sv"


def _module_contract_refs(module: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for key in (
        "implements",
        "source_sections",
        "ssot_refs",
        "function_model_refs",
        "decomposition_refs",
        "cycle_model_refs",
        "feature_refs",
        "dataflow_refs",
        "register_refs",
        "fsm_refs",
        "test_refs",
        "trace_refs",
    ):
        value = module.get(key)
        if isinstance(value, str):
            refs.extend(item.strip() for item in value.replace(";", ",").split(",") if item.strip())
        elif isinstance(value, list):
            refs.extend(str(item).strip() for item in value if str(item).strip())
        elif isinstance(value, dict):
            refs.extend(str(item).strip() for item in value if str(item).strip())
    return sorted({ref for ref in refs if ref})


def _top_name(ssot: dict[str, Any], ip: str) -> str:
    top = ssot.get("top_module")
    if isinstance(top, dict):
        return str(top.get("name") or ip)
    if top:
        return str(top)
    return ip


def _active_rtl_modules(ssot: dict[str, Any], ip: str) -> list[dict[str, Any]]:
    top = _top_name(ssot, ip)
    modules: list[dict[str, Any]] = []
    raw = ssot.get("sub_modules")
    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict):
                continue
            ownership = str(item.get("ownership") or "manifest").lower()
            if ownership in {"child_ssot", "conceptual", "coverage", "verification"} or item.get("ssot"):
                continue
            if item.get("rtl_emit") is False:
                continue
            name = str(item.get("name") or top)
            modules.append({
                "name": name,
                "file": _module_file(ip, top, item),
                "refs": _module_contract_refs(item),
                "raw": item,
            })
    if not modules:
        modules.append({
            "name": top,
            "file": f"rtl/{top}.sv",
            "refs": ["top_module", "function_model", "cycle_model", "rtl_contract"],
            "raw": {},
        })
    if len(modules) == 1 and not modules[0]["refs"]:
        modules[0]["refs"] = ["top_module", "function_model", "cycle_model", "rtl_contract"]
    return modules


def _ref_is_covered(ref: str, owner_ref: str) -> bool:
    return ref == owner_ref or ref.startswith(owner_ref + ".") or owner_ref.startswith(ref + ".")


def _covered_by_module(ref: str, module: dict[str, Any], *, single_owner: bool) -> bool:
    if single_owner:
        return True
    refs = module.get("refs") if isinstance(module.get("refs"), list) else []
    return any(_ref_is_covered(ref, str(owner_ref)) for owner_ref in refs)


def _item_name(item: Any, idx: int, fallback: str) -> str:
    if isinstance(item, dict):
        for key in ("id", "name", "field", "signal", "port", "state", "stage", "event", "register"):
            if item.get(key) not in (None, ""):
                return str(item[key])
    return f"{fallback}_{idx}"


def _function_model_leaf_refs(ssot: dict[str, Any]) -> list[dict[str, str]]:
    fm = ssot.get("function_model") if isinstance(ssot.get("function_model"), dict) else {}
    refs: list[dict[str, str]] = []
    for idx, item in enumerate(_as_list(fm.get("state_variables"))):
        name = _item_name(item, idx, "state")
        refs.append({"ref": f"function_model.state_variables.{_safe_name(name, 'state')}", "kind": "state_variable"})
    for idx, tx in enumerate(_as_list(fm.get("transactions"))):
        if not isinstance(tx, dict):
            tx = {"name": str(tx)}
        tx_name = _item_name(tx, idx, "transaction")
        tx_ref = f"function_model.transactions.{_safe_name(tx.get('id') or tx_name, 'transaction')}"
        refs.append({"ref": tx_ref, "kind": "transaction"})
        for key in (
            "preconditions",
            "inputs",
            "outputs",
            "output_rules",
            "state_updates",
            "side_effects",
            "counter_rules",
            "event_rules",
            "error_cases",
        ):
            for sub_idx, sub in enumerate(_as_list(tx.get(key))):
                sub_name = _item_name(sub, sub_idx, key.rstrip("s") or "entry")
                refs.append({"ref": f"{tx_ref}.{key}.{_safe_name(sub_name, 'entry')}", "kind": key})
    for idx, item in enumerate(_as_list(fm.get("invariants"))):
        name = _item_name(item, idx, "invariant")
        refs.append({"ref": f"function_model.invariants.{_safe_name(name, 'invariant')}", "kind": "invariant"})
    return refs


def _cycle_model_leaf_refs(ssot: dict[str, Any]) -> list[dict[str, str]]:
    cm = ssot.get("cycle_model") if isinstance(ssot.get("cycle_model"), dict) else {}
    refs: list[dict[str, str]] = []
    for key in ("clock", "reset", "latency"):
        if cm.get(key) not in (None, "", [], {}):
            refs.append({"ref": f"cycle_model.{key}", "kind": key})
    for key in (
        "handshake_rules",
        "pipeline",
        "ordering",
        "backpressure",
        "observability",
        "arbitration",
        "stall_rules",
        "completion",
        "timeouts",
    ):
        for idx, item in enumerate(_as_list(cm.get(key))):
            name = _item_name(item, idx, key.rstrip("s") or "rule")
            refs.append({"ref": f"cycle_model.{key}.{_safe_name(name, 'rule')}", "kind": key})
    return refs


def _module_contracts(ssot: dict[str, Any], ip: str) -> tuple[list[dict[str, Any]], list[str], list[dict[str, str]]]:
    modules = _active_rtl_modules(ssot, ip)
    leaf_refs = _function_model_leaf_refs(ssot) + _cycle_model_leaf_refs(ssot)
    single_owner = len(modules) == 1
    contracts: list[dict[str, Any]] = []
    covered: set[str] = set()
    for module in modules:
        module_leaf_refs = [
            item["ref"]
            for item in leaf_refs
            if _covered_by_module(item["ref"], module, single_owner=single_owner)
        ]
        covered.update(module_leaf_refs)
        refs = module.get("refs") if isinstance(module.get("refs"), list) else []
        contracts.append({
            "name": module["name"],
            "kind": "rtl_module",
            "rtl_module": module["name"],
            "rtl_file": module["file"],
            "source_sections": sorted({ref.split(".", 1)[0] for ref in refs + module_leaf_refs if ref}),
            "ssot_refs": sorted({*refs, *module_leaf_refs}),
            "function_model_refs": sorted(ref for ref in module_leaf_refs if ref.startswith("function_model.")),
            "cycle_model_refs": sorted(ref for ref in module_leaf_refs if ref.startswith("cycle_model.")),
            "verification_scope": "module",
            "requires_module_equivalence": bool(module_leaf_refs),
            "blocked": not bool(module_leaf_refs),
            "blocker": "" if module_leaf_refs else "module has no function_model or cycle_model ownership refs",
        })
    orphan_refs = sorted(item["ref"] for item in leaf_refs if item["ref"] not in covered)
    return contracts, orphan_refs, leaf_refs


def _fcov_bins(ssot: dict[str, Any]) -> list[dict[str, Any]]:
    bins = _scenario_bins(ssot)
    tr = ssot.get("test_requirements") if isinstance(ssot.get("test_requirements"), dict) else {}
    coverage_goals = tr.get("coverage_goals") if isinstance(tr.get("coverage_goals"), dict) else {}
    planned_bins = coverage_goals.get("planned_bins") if isinstance(coverage_goals.get("planned_bins"), list) else []
    for idx, item in enumerate(planned_bins):
        if not isinstance(item, dict):
            continue
        bid = _safe_name(item.get("id") or item.get("name"), f"planned_bin_{idx}")
        bins.append({
            "id": bid,
            "class": str(item.get("class") or "planned_functional"),
            "source": f"test_requirements.coverage_goals.planned_bins[{idx}]",
            "description": str(item.get("description") or item.get("goal") or bid),
        })
    fm = ssot.get("function_model") if isinstance(ssot.get("function_model"), dict) else {}
    for idx, tx in enumerate(fm.get("transactions") or []):
        if isinstance(tx, dict):
            name = _safe_name(tx.get("name") or tx.get("id"), f"transaction_{idx}")
            bins.append({
                "id": f"function_{name}",
                "class": "transaction_type",
                "source": f"function_model.transactions[{idx}]",
                "description": str(tx.get("description") or tx.get("expected") or name),
            })
    cm = ssot.get("cycle_model") if isinstance(ssot.get("cycle_model"), dict) else {}
    for idx, rule in enumerate(cm.get("handshake_rules") or []):
        if isinstance(rule, dict):
            name = _safe_name(rule.get("name") or rule.get("id"), f"handshake_{idx}")
            bins.append({
                "id": f"cycle_{name}",
                "class": "protocol",
                "source": f"cycle_model.handshake_rules[{idx}]",
                "description": str(rule.get("description") or rule),
            })
    fsm = ssot.get("fsm") if isinstance(ssot.get("fsm"), dict) else {}
    fsm_blocks = fsm.values() if fsm and all(isinstance(v, dict) for v in fsm.values()) else [fsm]
    for block_name, block in zip(fsm.keys() if fsm else [], fsm_blocks):
        if not isinstance(block, dict):
            continue
        for idx, trn in enumerate(block.get("transitions") or []):
            if isinstance(trn, dict):
                src = _safe_name(trn.get("from"), "from")
                dst = _safe_name(trn.get("to"), "to")
                bins.append({
                    "id": f"fsm_{_safe_name(block_name, 'fsm')}_{src}_to_{dst}_{idx}",
                    "class": "state_transition",
                    "source": f"fsm.{block_name}.transitions[{idx}]",
                    "description": str(trn.get("condition") or trn),
                })
    err = ssot.get("error_handling") if isinstance(ssot.get("error_handling"), dict) else {}
    for idx, src in enumerate(err.get("error_sources") or []):
        name = _safe_name(src.get("name") if isinstance(src, dict) else src, f"error_{idx}")
        bins.append({
            "id": f"error_{name}",
            "class": "error",
            "source": f"error_handling.error_sources[{idx}]",
            "description": str(src),
        })
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for item in bins:
        if item["id"] in seen:
            continue
        seen.add(item["id"])
        unique.append(item)
    return unique


def _decomposition(ssot: dict[str, Any], ip: str) -> dict[str, Any]:
    module_contracts, orphan_refs, leaf_refs = _module_contracts(ssot, ip)
    units: list[dict[str, Any]] = []
    for contract in module_contracts:
        units.append({
            "name": contract["name"],
            "kind": "rtl_module",
            "source_sections": contract["source_sections"],
            "rtl_candidates": [contract["rtl_module"]],
            "rtl_file": contract["rtl_file"],
            "ssot_refs": contract["ssot_refs"],
            "function_model_refs": contract["function_model_refs"],
            "cycle_model_refs": contract["cycle_model_refs"],
            "verification_impact": ["module-level FL-vs-RTL scoreboard", "module functional coverage"],
            "requires_module_equivalence": contract["requires_module_equivalence"],
            "blocked": contract["blocked"],
            "blocker": contract["blocker"],
        })
    io_list = ssot.get("io_list") if isinstance(ssot.get("io_list"), dict) else {}
    if io_list.get("interfaces"):
        units.append({
            "name": f"{ip}_protocol_model",
            "kind": "protocol",
            "source_sections": ["io_list", "cycle_model"],
            "rtl_candidates": [f"{ip}_axi_slv", f"{ip}_protocol"],
            "verification_impact": ["driver", "monitor", "protocol coverage"],
        })
    regs = ssot.get("registers") if isinstance(ssot.get("registers"), dict) else {}
    if regs.get("register_map") or regs.get("register_list") or regs.get("config"):
        units.append({
            "name": f"{ip}_register_model",
            "kind": "register",
            "source_sections": ["registers", "error_handling"],
            "rtl_candidates": [f"{ip}_regs", f"{ip}_apb_regs"],
            "verification_impact": ["register sequences", "readback scoreboard"],
        })
    if isinstance(ssot.get("memory"), dict) and ssot["memory"].get("instances"):
        units.append({
            "name": f"{ip}_memory_model",
            "kind": "memory",
            "source_sections": ["memory", "function_model"],
            "rtl_candidates": [f"{ip}_mem", f"{ip}_core"],
            "verification_impact": ["address retention", "byte strobes", "boundary coverage"],
        })
    features = ssot.get("features") if isinstance(ssot.get("features"), list) else []
    if features:
        units.append({
            "name": f"{ip}_datapath_model",
            "kind": "datapath",
            "source_sections": ["features", "dataflow", "function_model"],
            "rtl_candidates": [f"{ip}_core", f"{ip}_datapath"],
            "verification_impact": ["functional scoreboard", "transaction coverage"],
        })
    fsm = ssot.get("fsm") if isinstance(ssot.get("fsm"), dict) else {}
    has_fsm = bool(fsm.get("states") or any(isinstance(v, dict) and (v.get("states") or v.get("transitions")) for v in fsm.values()))
    if has_fsm:
        units.append({
            "name": f"{ip}_fsm_model",
            "kind": "fsm",
            "source_sections": ["fsm", "cycle_model"],
            "rtl_candidates": [f"{ip}_core"],
            "verification_impact": ["state transition coverage", "waveform debug"],
        })
    if isinstance(ssot.get("error_handling"), dict):
        units.append({
            "name": f"{ip}_error_model",
            "kind": "error",
            "source_sections": ["error_handling"],
            "rtl_candidates": [f"{ip}_core", f"{ip}_error"],
            "verification_impact": ["negative tests", "mismatch classification"],
        })
    security = ssot.get("security") if isinstance(ssot.get("security"), dict) else {}
    if security.get("assets") or security.get("threats"):
        units.append({
            "name": f"{ip}_security_model",
            "kind": "security",
            "source_sections": ["security", "debug_observability"],
            "rtl_candidates": [f"{ip}_security", f"{ip}_core"],
            "verification_impact": ["security bins", "debug observability checks"],
        })
    return {
        "schema_version": 1,
        "type": "fl_model_decomposition",
        "ip": ip,
        "source": f"{ip}/yaml/{ip}.ssot.yaml",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "units": units,
        "module_contracts": module_contracts,
        "orphan_function_cycle_refs": orphan_refs,
        "function_cycle_ref_count": len(leaf_refs),
        "authority_contract": _authority_contract(ip),
        "drives": ["rtl_module_plan", "tb_environment_plan", "functional_coverage_plan"],
        "complete": bool(units) and not orphan_refs and all(not item.get("blocked") for item in module_contracts),
    }


def _model_source(ip: str, ssot: dict[str, Any], params: dict[str, Any], bins: list[dict[str, Any]]) -> str:
    payload = {
        "ip": ip,
        "parameters": params,
        "top_module": ssot.get("top_module") if isinstance(ssot.get("top_module"), dict) else {},
        "memory": ssot.get("memory") if isinstance(ssot.get("memory"), dict) else {},
        "registers": ssot.get("registers") if isinstance(ssot.get("registers"), dict) else {},
        "function_model": ssot.get("function_model") if isinstance(ssot.get("function_model"), dict) else {},
        "cycle_model": ssot.get("cycle_model") if isinstance(ssot.get("cycle_model"), dict) else {},
        "fcov_bins": bins,
    }
    return f'''#!/usr/bin/env python3
"""Executable SSOT functional model for {ip}.

Generated from yaml/{ip}.ssot.yaml. This model is independent from RTL and is
intended to be imported by cocotb/pyuvm scoreboards.
"""

from __future__ import annotations

import ast
import json
import re


SSOT_MODEL = {payload!r}
RESP_OKAY = 0
RESP_SLVERR = 2


def _parse_int(value, default=0):
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    text = str(value).strip().replace("_", "")
    if not text:
        return default
    literal = text.lower()
    if "'" in literal:
        try:
            base_tag = literal.split("'", 1)[1][0]
            digits = literal.split(base_tag, 1)[1]
            digits = digits.replace("x", "0").replace("z", "0")
            base = {{"h": 16, "d": 10, "b": 2}}.get(base_tag, 10)
            return int(digits, base)
        except Exception:
            return default
    if text.startswith("0x"):
        return int(text, 16)
    try:
        return int(text, 10)
    except ValueError:
        return default


_BINOPS = {{
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.FloorDiv: lambda a, b: a // b,
    ast.Div: lambda a, b: a // b,
    ast.Mod: lambda a, b: a % b,
    ast.LShift: lambda a, b: a << b,
    ast.RShift: lambda a, b: a >> b,
    ast.BitAnd: lambda a, b: a & b,
    ast.BitOr: lambda a, b: a | b,
    ast.BitXor: lambda a, b: a ^ b,
}}
_UNARYOPS = {{
    ast.UAdd: lambda a: a,
    ast.USub: lambda a: -a,
    ast.Invert: lambda a: ~a,
    ast.Not: lambda a: 0 if a else 1,
}}
_CMPOPS = {{
    ast.Eq: lambda a, b: a == b,
    ast.NotEq: lambda a, b: a != b,
    ast.Lt: lambda a, b: a < b,
    ast.LtE: lambda a, b: a <= b,
    ast.Gt: lambda a, b: a > b,
    ast.GtE: lambda a, b: a >= b,
}}


def _normal_expr(text):
    text = str(text or "").strip()
    text = text.replace("&&", " and ").replace("||", " or ")
    text = re.sub(r"(?<![=!<>])!(?!=)", " not ", text)
    return text


def _literal_int(text):
    text = str(text).strip().replace("_", "")
    return bool(re.fullmatch(r"(?:0x[0-9a-fA-F]+|[0-9]+|[0-9]*'[hHdDbB][0-9a-fA-FxXzZ]+)", text))


def _eval_ast(node, env):
    if isinstance(node, ast.Expression):
        return _eval_ast(node.body, env)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool):
            return int(node.value)
        if isinstance(node.value, int):
            return node.value
        if isinstance(node.value, str):
            return _parse_int(node.value, 0)
        raise ValueError(f"unsupported constant {{node.value!r}}")
    if isinstance(node, ast.Name):
        if node.id in env:
            return _parse_int(env[node.id], 0)
        raise KeyError(f"unknown rule name {{node.id}}")
    if isinstance(node, ast.BinOp) and type(node.op) in _BINOPS:
        return _BINOPS[type(node.op)](_eval_ast(node.left, env), _eval_ast(node.right, env))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARYOPS:
        return _UNARYOPS[type(node.op)](_eval_ast(node.operand, env))
    if isinstance(node, ast.BoolOp):
        values = [_eval_ast(v, env) for v in node.values]
        if isinstance(node.op, ast.And):
            return int(all(values))
        if isinstance(node.op, ast.Or):
            return int(any(values))
    if isinstance(node, ast.Compare):
        left = _eval_ast(node.left, env)
        verdicts = []
        for op, comparator in zip(node.ops, node.comparators):
            right = _eval_ast(comparator, env)
            if type(op) not in _CMPOPS:
                raise ValueError(f"unsupported comparison {{type(op).__name__}}")
            verdicts.append(_CMPOPS[type(op)](left, right))
            left = right
        return int(all(verdicts))
    if isinstance(node, ast.IfExp):
        return _eval_ast(node.body if _eval_ast(node.test, env) else node.orelse, env)
    raise ValueError(f"unsupported rule expression node {{type(node).__name__}}")


def _eval_rule_expr(expr, env):
    if isinstance(expr, bool):
        return int(expr)
    if isinstance(expr, int):
        return expr
    text = _normal_expr(expr)
    if not text:
        return 0
    if _literal_int(text):
        return _parse_int(text, 0)
    return _eval_ast(ast.parse(text, mode="eval"), env)


def _expr_names(expr):
    try:
        node = ast.parse(_normal_expr(expr), mode="eval")
    except Exception:
        return set()
    return {{item.id for item in ast.walk(node) if isinstance(item, ast.Name)}}


def _rule_items(value):
    if isinstance(value, dict):
        return [{{"name": k, "expr": v}} for k, v in value.items()]
    return [item for item in value or [] if isinstance(item, dict)]


class FunctionalModel:
    def __init__(self, params=None):
        self.params = dict(SSOT_MODEL.get("parameters") or {{}})
        if params:
            self.params.update(params)
        self.state_defaults = self._state_defaults()
        self.state = dict(self.state_defaults)
        self.registers = self._register_defaults()
        self.trace = []

    @staticmethod
    def _norm(value):
        text = str(value or "").strip().lower()
        text = re.sub(r"[^a-z0-9]+", "_", text)
        return text.strip("_")

    def _state_defaults(self):
        defaults = {{}}
        fm = SSOT_MODEL.get("function_model") or {{}}
        for idx, item in enumerate(fm.get("state_variables") or []):
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or f"state_{{idx}}")
            defaults[name] = item.get("reset", 0)
        defaults.setdefault("busy", 0)
        defaults.setdefault("error", 0)
        return defaults

    def _register_defaults(self):
        defaults = {{}}
        regs = SSOT_MODEL.get("registers") or {{}}
        for idx, item in enumerate(regs.get("register_list") or []):
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or f"REG{{idx}}")
            defaults[name] = item.get("reset", 0)
            off = item.get("offset")
            if off is not None:
                defaults[str(off)] = item.get("reset", 0)
        return defaults

    def reset(self):
        self.state = dict(self.state_defaults)
        self.registers = self._register_defaults()
        self.trace.clear()

    def _looks_like_register_access(self, txn):
        kind = self._norm(txn.get("kind") or txn.get("transaction") or "")
        return (
            kind in {{"csr", "csr_access", "register", "register_access", "control_status_access", "fm_csr"}}
            or "reg" in txn
            or "addr_or_name" in txn
        )

    def _transactions(self):
        fm = SSOT_MODEL.get("function_model") or {{}}
        return [tx for tx in fm.get("transactions") or [] if isinstance(tx, dict)]

    def _find_transaction(self, kind):
        wanted = self._norm(kind)
        for tx in self._transactions():
            aliases = [
                tx.get("id"),
                tx.get("name"),
                self._norm(tx.get("id")),
                self._norm(tx.get("name")),
            ]
            if wanted in {{self._norm(x) for x in aliases if x}}:
                return tx
        if wanted in {{"reset", "rst"}}:
            return {{"id": "RESET", "name": "reset", "outputs": ["state reset"], "side_effects": ["reset"]}}
        return None

    def _record(self, kind, txn, result):
        entry = {{
            "kind": kind,
            "scenario_id": txn.get("scenario_id", ""),
            "result": result,
            "state": dict(self.state),
        }}
        self.trace.append(entry)
        return result

    def _rule_env(self, txn):
        env = {{}}
        env.update(self.params)
        env.update(self.state)
        env.update(self.registers)
        env.update(txn)
        env.setdefault("true", 1)
        env.setdefault("false", 0)
        return env

    def _apply_structured_rules(self, tx, txn):
        output_rules = _rule_items(tx.get("output_rules"))
        state_updates = _rule_items(tx.get("state_updates"))
        if not output_rules and not state_updates:
            return None

        env = self._rule_env(txn)
        result = {{
            "resp": RESP_OKAY,
            "transaction_id": tx.get("id"),
            "transaction_name": tx.get("name"),
            "sample_accepted": 0,
        }}
        pending_outputs = []
        for idx, rule in enumerate(output_rules):
            name = str(rule.get("name") or rule.get("output") or rule.get("port") or f"output_{{idx}}")
            aliases = [
                str(v)
                for v in (rule.get("output"), rule.get("port"))
                if v is not None and str(v).strip() and str(v).strip() != name
            ]
            pending_outputs.append((
                name,
                rule.get("expr", rule.get("expression", rule.get("value", 0))),
                rule.get("width") or rule.get("bits"),
                aliases,
            ))

        def _resolve_pending_outputs(required_names=None):
            nonlocal pending_outputs
            required = set(required_names or [])
            unresolved_errors = {{}}
            for _pass in range(max(len(pending_outputs), 1) + 1):
                progressed = False
                next_pending = []
                for name, expr, width, aliases in pending_outputs:
                    try:
                        value = _eval_rule_expr(expr, env)
                    except KeyError as exc:
                        unresolved_errors[name] = str(exc)
                        next_pending.append((name, expr, width, aliases))
                        continue
                    if width is not None:
                        value &= (1 << max(_parse_int(width, 0), 0)) - 1 if _parse_int(width, 0) > 0 else value
                    result[name] = value
                    env[name] = value
                    for alias in aliases:
                        result.setdefault(alias, value)
                        env[alias] = value
                    unresolved_errors.pop(name, None)
                    progressed = True
                pending_outputs = next_pending
                if not pending_outputs:
                    break
                if required and required.issubset(env):
                    break
                if not progressed:
                    break
            if required:
                unresolved_required = sorted(name for name in required if name not in env)
                if unresolved_required:
                    detail = ", ".join(
                        f"{{name}}: {{unresolved_errors.get(name, 'unresolved dependency')}}"
                        for name in unresolved_required
                    )
                    raise KeyError(f"unresolved sample condition dependencies: {{detail}}")
            return unresolved_errors

        output_names = set()
        for name, _expr, _width, aliases in pending_outputs:
            output_names.add(name)
            output_names.update(aliases)
        sample_expr = tx.get("sample_condition")
        sample_accepted = True
        if sample_expr not in (None, ""):
            needed_outputs = _expr_names(sample_expr) & output_names
            if needed_outputs:
                _resolve_pending_outputs(needed_outputs)
            sample_accepted = bool(_eval_rule_expr(sample_expr, env))
        result["sample_accepted"] = int(sample_accepted)

        unresolved_errors = _resolve_pending_outputs()
        if pending_outputs:
            missing = ", ".join(f"{{name}}: {{unresolved_errors.get(name, 'unresolved dependency')}}" for name, _expr, _width, _aliases in pending_outputs)
            raise KeyError(f"unresolved output rule dependencies: {{missing}}")

        updates = {{}}
        pending_updates = []
        if sample_accepted:
            for idx, rule in enumerate(state_updates):
                pending_updates.append((
                    str(rule.get("name") or rule.get("state") or f"state_{{idx}}"),
                    rule.get("expr", rule.get("expression", rule.get("value", 0))),
                ))
        unresolved_errors = {{}}
        for _pass in range(max(len(pending_updates), 1) + 1):
            progressed = False
            next_pending = []
            for name, expr in pending_updates:
                try:
                    value = _eval_rule_expr(expr, env)
                except KeyError as exc:
                    unresolved_errors[name] = str(exc)
                    next_pending.append((name, expr))
                    continue
                updates[name] = value
                env[name] = value
                unresolved_errors.pop(name, None)
                progressed = True
            pending_updates = next_pending
            if not pending_updates:
                break
            if not progressed:
                break
        if pending_updates:
            missing = ", ".join(f"{{name}}: {{unresolved_errors.get(name, 'unresolved dependency')}}" for name, _expr in pending_updates)
            raise KeyError(f"unresolved state update dependencies: {{missing}}")
        if updates:
            self.state.update(updates)
            result["state_updates"] = dict(updates)
        return result

    def _apply_register_access(self, txn):
        if not self._looks_like_register_access(txn):
            return None
        op = self._norm(txn.get("op") or txn.get("kind"))
        key = txn.get("reg", txn.get("addr", txn.get("name", "")))
        key = str(key)
        if op in {{"write", "wr", "csr_write", "control_status_access"}}:
            self.registers[key] = txn.get("data", txn.get("value", 0))
            return {{"resp": RESP_OKAY, "write": True, "reg": key, "value": self.registers[key]}}
        if op in {{"read", "rd", "csr_read"}}:
            return {{"resp": RESP_OKAY, "read": True, "reg": key, "value": self.registers.get(key, 0)}}
        return None

    def _apply_primary(self, tx, txn):
        structured = self._apply_structured_rules(tx, txn)
        if structured is not None:
            return structured
        malformed = bool(txn.get("malformed") or txn.get("error") or txn.get("invalid"))
        self.state["busy"] = 1
        if malformed:
            self.state["error"] = 1
        for name, value in list(self.state.items()):
            lname = self._norm(name)
            if "count" in lname and not malformed:
                self.state[name] = _parse_int(value, 0) + 1
            if ("bad" in lname or "error" in lname or "malformed" in lname) and malformed:
                self.state[name] = _parse_int(value, 0) + 1
            if ("good" in lname or "pass" in lname) and not malformed:
                self.state[name] = _parse_int(value, 0) + 1
        self.state["busy"] = 0
        result = {{
            "resp": RESP_OKAY,
            "transaction_id": tx.get("id"),
            "transaction_name": tx.get("name"),
            "outputs_spec": tx.get("outputs") or [],
            "side_effects_spec": tx.get("side_effects") or [],
            "malformed": malformed,
        }}
        return result

    def apply(self, txn):
        txn = dict(txn or {{}})
        kind = self._norm(txn.get("kind") or txn.get("op") or txn.get("transaction") or "")
        reg_result = self._apply_register_access(txn)
        if reg_result is not None:
            return self._record(kind or "register_access", txn, reg_result)
        tx = self._find_transaction(kind)
        if tx is None:
            return self._record(kind or "unknown", txn, {{"kind": kind or "unknown", "resp": RESP_SLVERR, "error": "unsupported_transaction"}})
        if self._norm(tx.get("name")) == "reset" or self._norm(tx.get("id")) in {{"reset", "fm_reset"}}:
            self.reset()
            return self._record(kind or "reset", txn, {{"kind": "reset", "resp": RESP_OKAY, "state": dict(self.state)}})
        return self._record(kind, txn, self._apply_primary(tx, txn))

    def coverage_seed_bins(self):
        return {{item["id"]: False for item in SSOT_MODEL.get("fcov_bins", [])}}


def run_self_check():
    model = FunctionalModel()
    txs = SSOT_MODEL.get("function_model", {{}}).get("transactions", [])
    results = []
    for idx, tx in enumerate(txs):
        if not isinstance(tx, dict):
            continue
        kind = tx.get("id") or tx.get("name") or f"transaction_{{idx}}"
        txn = {{"kind": kind, "scenario_id": f"self_{{kind}}"}}
        for field_idx, field in enumerate(tx.get("required_fields") or []):
            name = str(field)
            if name and name not in txn:
                txn[name] = field_idx + idx + 1
        output_rules = _rule_items(tx.get("output_rules"))
        state_updates = _rule_items(tx.get("state_updates"))
        rule_names = set()
        rule_names.update(_expr_names(tx.get("sample_condition", "")))
        for rule in output_rules + state_updates:
            rule_names.update(_expr_names(rule.get("expr", rule.get("expression", rule.get("value", "")))))
        output_names = {{
            str(rule.get("name") or rule.get("output") or rule.get("port"))
            for rule in output_rules
            if rule.get("name") or rule.get("output") or rule.get("port")
        }}
        update_names = {{
            str(rule.get("name") or rule.get("state"))
            for rule in state_updates
            if rule.get("name") or rule.get("state")
        }}
        known_names = set(model.params) | set(model.state) | set(model.registers) | output_names | update_names
        known_names.update({{"true", "false", "True", "False", "and", "or", "not"}})
        for name in sorted(rule_names - known_names):
            if name and name not in txn:
                txn[name] = idx + len(txn) + 1
        result = model.apply(txn)
        results.append({{
            "id": tx.get("id"),
            "name": tx.get("name"),
            "kind": kind,
            "passed": result.get("resp") == RESP_OKAY,
            "result": result,
        }})
    unsupported = model.apply({{"kind": "__unsupported_self_check__"}})
    checks = [item["passed"] for item in results]
    checks.append(unsupported.get("resp") == RESP_SLVERR)
    return {{
        "passed": all(checks),
        "checks": len(checks),
        "failed": checks.count(False),
        "transactions": len(txs),
        "transaction_results": results,
        "unsupported_transaction_check": unsupported.get("resp") == RESP_SLVERR,
        "trace_entries": len(model.trace),
        "coverage_bins": len(SSOT_MODEL.get("fcov_bins", [])),
    }}


if __name__ == "__main__":
    print(json.dumps(run_self_check(), indent=2))
'''


def _run_generated_self_check(path: Path) -> dict[str, Any]:
    spec = importlib.util.spec_from_file_location("generated_functional_model", path)
    if spec is None or spec.loader is None:
        return {"passed": False, "error": "cannot import generated model"}
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    result = mod.run_self_check()
    return result if isinstance(result, dict) else {"passed": False, "error": "self_check returned non-dict"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ip")
    parser.add_argument("--root", default=".")
    parser.add_argument("--no-check", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    ip_dir = root / args.ip
    ssot = _load_ssot(ip_dir, args.ip)
    params = _param_map(ssot)
    bins = _fcov_bins(ssot)
    model_dir = ip_dir / "model"
    cov_dir = ip_dir / "cov"
    model_dir.mkdir(parents=True, exist_ok=True)
    cov_dir.mkdir(parents=True, exist_ok=True)

    decomposition = _decomposition(ssot, args.ip)
    fcov_plan = {
        "schema_version": 1,
        "type": "functional_coverage_plan",
        "ip": args.ip,
        "source": f"{args.ip}/yaml/{args.ip}.ssot.yaml",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "planned_before_rtl": True,
        "authority_contract": _authority_contract(args.ip),
        "bins": bins,
        "summary": {
            "total_bins": len(bins),
            "scenario_bins": sum(1 for b in bins if b.get("class") == "scenario"),
            "transaction_bins": sum(1 for b in bins if b.get("class") == "transaction_type"),
            "protocol_bins": sum(1 for b in bins if b.get("class") == "protocol"),
            "state_transition_bins": sum(1 for b in bins if b.get("class") == "state_transition"),
            "error_bins": sum(1 for b in bins if b.get("class") == "error"),
        },
    }

    model_path = model_dir / "functional_model.py"
    model_path.write_text(_model_source(args.ip, ssot, params, bins), encoding="utf-8")
    (model_dir / "decomposition.json").write_text(json.dumps(decomposition, indent=2) + "\n", encoding="utf-8")
    (cov_dir / "fcov_plan.json").write_text(json.dumps(fcov_plan, indent=2) + "\n", encoding="utf-8")

    check = {"passed": True, "skipped": True}
    if not args.no_check:
        check = _run_generated_self_check(model_path)
    report = {
        "schema_version": 1,
        "type": "fl_model_check",
        "ip": args.ip,
        "source": str(model_path.relative_to(ip_dir)),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "passed": bool(check.get("passed")),
        "self_check": check,
        "decomposition_units": len(decomposition["units"]),
        "fcov_bins": len(bins),
        "authority_contract": _authority_contract(args.ip),
    }
    (model_dir / "fl_model_check.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"[emit_fl_model] wrote {model_path}")
    print(f"[emit_fl_model] decomposition_units={len(decomposition['units'])} fcov_bins={len(bins)} passed={report['passed']}")
    return 0 if report["passed"] and decomposition["units"] and bins else 1


if __name__ == "__main__":
    raise SystemExit(main())
