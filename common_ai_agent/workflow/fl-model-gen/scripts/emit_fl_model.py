#!/usr/bin/env python3
"""Generate executable SSOT functional-model artifacts.

The generated model is intentionally SSOT-driven and independent from RTL.
It provides a transaction-level reference that TB scoreboards can import.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

import yaml

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))


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
    elif isinstance(params, dict):
        for name, value in params.items():
            if isinstance(value, dict):
                out[str(name)] = value.get("default", value.get("value"))
            else:
                out[str(name)] = value
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


EVIDENCE_STOPWORDS = {
    "access",
    "according",
    "all",
    "an",
    "and",
    "any",
    "approved",
    "as",
    "be",
    "before",
    "behavior",
    "boundary",
    "clear",
    "clears",
    "control",
    "counter",
    "counters",
    "cycle",
    "effect",
    "effects",
    "error",
    "event",
    "events",
    "exactly",
    "externally",
    "feature",
    "field",
    "fields",
    "fl",
    "for",
    "from",
    "function_model",
    "gen",
    "implement",
    "input",
    "is",
    "listed",
    "model",
    "module",
    "non",
    "observable",
    "output",
    "pending",
    "preserve",
    "protocol",
    "retained",
    "rtl",
    "rule",
    "side",
    "state",
    "the",
    "to",
    "transaction",
    "with",
}

REFERENCE_STOPWORDS = {
    "backpressure",
    "cycle_model",
    "dataflow",
    "error_cases",
    "fsm",
    "function_model",
    "handshake_rules",
    "inputs",
    "invariants",
    "observability",
    "ordering",
    "output_rules",
    "outputs",
    "pipeline",
    "preconditions",
    "register_list",
    "registers",
    "side_effects",
    "state_updates",
    "state_variables",
    "test_requirements",
    "transactions",
}


def _present(value: Any) -> bool:
    if value is None:
        return False
    if value is False:
        return False
    if isinstance(value, str):
        return bool(value.strip()) and value.strip().lower() not in {"none", "n/a", "na", "tbd", "todo"}
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


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
            refs.extend(item.strip() for item in re.split(r"[,;\n]+", value) if item.strip())
        elif isinstance(value, list):
            refs.extend(str(item).strip() for item in value if str(item).strip())
        elif isinstance(value, dict):
            refs.extend(str(item).strip() for item in value if str(item).strip())
    return _expand_relative_refs(refs)


def _expand_relative_refs(refs: list[str]) -> list[str]:
    """Expand shorthand SSOT refs like `.store` using the prior ref prefix."""

    out: list[str] = []
    base_prefix = ""
    for raw in refs:
        ref = str(raw or "").strip()
        if not ref:
            continue
        if ref.startswith(".") and base_prefix:
            ref = base_prefix + ref
        if not ref.startswith(".") and "." in ref:
            base_prefix = ref.rsplit(".", 1)[0]
        out.append(ref)
    return sorted({ref for ref in out if ref})


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
    return _ref_prefix_covered(ref, owner_ref) or _ref_leaf_strong_match(ref, owner_ref)


def _ref_prefix_covered(ref: str, owner_ref: str) -> bool:
    ref_norm = ref.lower()
    owner_norm = owner_ref.lower()
    return (
        ref_norm == owner_norm
        or ref_norm.startswith(owner_norm + ".")
        or owner_norm.startswith(ref_norm + ".")
    )


def _ref_leaf_strong_match(ref: str, owner_ref: str) -> bool:
    ref_parent, _, ref_leaf = ref.rpartition(".")
    owner_parent, _, owner_leaf = owner_ref.rpartition(".")
    if not ref_parent or ref_parent.lower() != owner_parent.lower():
        return False

    def leaf_parts(leaf: str) -> set[str]:
        raw = [part for part in re.split(r"[_\W]+", leaf.lower()) if part]
        parts = {part for part in raw if len(part) > 1}
        if len(raw) > 1:
            parts.update(part for part in raw if len(part) == 1)
        return parts

    ref_parts = leaf_parts(ref_leaf)
    owner_parts = leaf_parts(owner_leaf)
    if not ref_parts or not owner_parts:
        return False
    return owner_parts.issubset(ref_parts) or ref_parts.issubset(owner_parts)


def _covered_by_module(ref: str, module: dict[str, Any], *, single_owner: bool) -> str:
    if single_owner:
        return "single_owner"
    refs = module.get("refs") if isinstance(module.get("refs"), list) else []
    prefix_matches: list[str] = []
    for owner_ref in refs:
        owner_ref = str(owner_ref)
        if _ref_prefix_covered(ref, owner_ref):
            prefix_matches.append(owner_ref)
    leaf_matches: list[str] = []
    for owner_ref in refs:
        owner_ref = str(owner_ref)
        if _ref_leaf_strong_match(ref, owner_ref):
            leaf_matches.append(owner_ref)
    matches = [*prefix_matches, *leaf_matches]
    if matches:
        return max(matches, key=lambda item: (len(item.split(".")), len(item)))
    return ""


def _owner_token_set(value: Any) -> set[str]:
    tokens: set[str] = set()

    def add_text(text: Any) -> None:
        for token in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", str(text or "")):
            for part in re.split(r"[_\W]+", token):
                lower = part.lower().strip("_")
                if len(lower) <= 1 or lower in EVIDENCE_STOPWORDS or lower in REFERENCE_STOPWORDS:
                    continue
                tokens.add(lower)
            lower_token = token.lower().strip("_")
            if len(lower_token) > 1 and lower_token not in EVIDENCE_STOPWORDS and lower_token not in REFERENCE_STOPWORDS:
                tokens.add(lower_token)

    def visit(item: Any) -> None:
        if item is None:
            return
        if isinstance(item, dict):
            for key, val in item.items():
                if str(key).lower() not in {"metadata", "notes"}:
                    visit(val)
            return
        if isinstance(item, list):
            for val in item:
                visit(val)
            return
        add_text(item)

    visit(value)
    return tokens


def _module_owner_terms(module: dict[str, Any], top: str) -> tuple[set[str], set[str]]:
    top_terms = _owner_token_set(top)
    name_text = " ".join(str(module.get(key) or "") for key in ("name", "file"))
    name_terms = _owner_token_set(name_text) - top_terms - {"rtl", "sv", "v", "module"}
    ref_terms: set[str] = set()
    for owner_ref in module.get("refs") or []:
        ref_terms.update(_owner_token_set(owner_ref))
    return name_terms, ref_terms - top_terms


def _semantic_leaf_terms(ref: str, value: Any) -> set[str]:
    terms = _owner_token_set(ref)
    if re.fullmatch(r"function_model\.transactions\.[^.]+", ref) and isinstance(value, dict):
        primary = {
            key: value.get(key)
            for key in ("id", "name", "opcode", "op", "category", "class", "type", "kind")
            if _present(value.get(key))
        }
        terms.update(_owner_token_set(primary))
        return terms
    terms.update(_owner_token_set(value))
    return terms


def _semantic_owner_match(item: dict[str, Any], modules: list[dict[str, Any]], top: str) -> dict[str, str] | None:
    ref = str(item.get("ref") or "")
    task_terms = _semantic_leaf_terms(ref, item.get("value"))
    task_terms -= {"function", "model", "cycle", "transactions", "transaction", "state", "variables"}
    if not task_terms:
        return None
    scored: list[tuple[int, int, dict[str, Any], str]] = []
    for index, module in enumerate(modules):
        name_terms, ref_terms = _module_owner_terms(module, top)
        name_hits = task_terms & name_terms
        ref_hits = task_terms & ref_terms
        score = len(ref_hits) * 2 + len(name_hits) * 3
        if score <= 0:
            continue
        hit_terms = sorted(ref_hits | name_hits)
        scored.append((score, -index, module, "semantic_terms:" + ",".join(hit_terms[:6])))
    if not scored:
        return None
    scored.sort(key=lambda value: (value[0], value[1]), reverse=True)
    if len(scored) > 1 and scored[0][0] == scored[1][0]:
        return None
    score, _neg_index, module, matched_ref = scored[0]
    if score < 2:
        return None
    return {"module": str(module["name"]), "file": str(module["file"]), "matched_ref": matched_ref}


def _control_owner_fallback(ref: str, modules: list[dict[str, Any]], top: str) -> dict[str, str] | None:
    if not ref.startswith(("function_model.", "cycle_model.")):
        return None
    candidates: list[tuple[int, int, dict[str, Any], str]] = []
    for index, module in enumerate(modules):
        name_terms, ref_terms = _module_owner_terms(module, top)
        combined = name_terms | ref_terms
        score = 0
        if combined & {"engine", "core", "controller", "control", "fsm"}:
            score += 4
        if combined & {"pipeline", "execute", "decode", "fetch"}:
            score += 2
        if "top" in combined:
            score += 1
        if score:
            candidates.append((score, -index, module, "control_owner_fallback"))
    if not candidates:
        return None
    candidates.sort(key=lambda value: (value[0], value[1]), reverse=True)
    if len(candidates) > 1 and candidates[0][0] == candidates[1][0]:
        return None
    _score, _neg_index, module, matched_ref = candidates[0]
    return {"module": str(module["name"]), "file": str(module["file"]), "matched_ref": matched_ref}


def _owner_for_leaf(
    item: dict[str, Any],
    modules: list[dict[str, Any]],
    top: str,
    *,
    single_owner: bool,
) -> dict[str, str]:
    ref = str(item.get("ref") or "")
    matches: list[tuple[dict[str, Any], str]] = []
    for module in modules:
        matched_ref = _covered_by_module(ref, module, single_owner=single_owner)
        if matched_ref:
            matches.append((module, matched_ref))
    if matches:
        # Same tie-breaker pattern used by derive_rtl_todos._owner_for: when
        # two modules share the same most-specific owner_ref (e.g. both
        # ``uart_lite_tx`` and ``uart_lite_rx`` carry ``cycle_model.pipeline``),
        # decide ownership by name-vs-ref token overlap so leaf tokens like
        # ``RX_IDLE`` route to the matching module.
        def _specificity(entry: tuple[dict[str, Any], str]) -> tuple[int, int]:
            return (len(str(entry[1]).split(".")), len(str(entry[1])))
        best = _specificity(max(matches, key=_specificity))
        top_tier = [entry for entry in matches if _specificity(entry) == best]
        if len(top_tier) > 1:
            ref_tokens = _owner_token_set(ref)
            top_tokens = _owner_token_set(top)
            scored: list[tuple[int, dict[str, Any], str]] = []
            for module, matched_ref in top_tier:
                name_tokens = _owner_token_set(module.get("name", "")) - top_tokens
                hits = len(ref_tokens & name_tokens)
                scored.append((hits, module, matched_ref))
            scored.sort(key=lambda row: row[0], reverse=True)
            if scored[0][0] > scored[1][0]:
                _, module, matched_ref = scored[0]
                return {"module": str(module["name"]), "file": str(module["file"]), "matched_ref": matched_ref}
        module, matched_ref = top_tier[0]
        return {"module": str(module["name"]), "file": str(module["file"]), "matched_ref": matched_ref}
    semantic_owner = _semantic_owner_match(item, modules, top)
    if semantic_owner is not None:
        return semantic_owner
    if (
        ref.startswith(("function_model.state_variables.", "function_model.invariants."))
        or ref in {"cycle_model.clock", "cycle_model.reset", "cycle_model.latency"}
    ):
        control_owner = _control_owner_fallback(ref, modules, top)
        if control_owner is not None:
            return control_owner
    section = ref.split(".", 1)[0]
    section_matches = [
        module
        for module in modules
        if any(str(owner_ref) == section or str(owner_ref).startswith(section + ".") for owner_ref in (module.get("refs") or []))
    ]
    if len(section_matches) == 1:
        module = section_matches[0]
        return {"module": str(module["name"]), "file": str(module["file"]), "matched_ref": f"unique_{section}_owner"}
    control_owner = _control_owner_fallback(ref, modules, top)
    if control_owner is not None:
        return control_owner
    return {"module": "", "file": "", "matched_ref": ""}


def _item_name(item: Any, idx: int, fallback: str) -> str:
    if isinstance(item, dict):
        for key in ("id", "name", "field", "signal", "port", "state", "stage", "event", "register"):
            if item.get(key) not in (None, ""):
                return str(item[key])
    return f"{fallback}_{idx}"


def _function_model_leaf_refs(ssot: dict[str, Any]) -> list[dict[str, Any]]:
    fm = ssot.get("function_model") if isinstance(ssot.get("function_model"), dict) else {}
    refs: list[dict[str, Any]] = []
    for idx, item in enumerate(_as_list(fm.get("state_variables"))):
        name = _item_name(item, idx, "state")
        refs.append({
            "ref": f"function_model.state_variables.{_safe_name(name, 'state')}",
            "kind": "state_variable",
            "value": item,
        })
    for idx, tx in enumerate(_as_list(fm.get("transactions"))):
        if not isinstance(tx, dict):
            tx = {"name": str(tx)}
        tx_name = _item_name(tx, idx, "transaction")
        tx_ref = f"function_model.transactions.{_safe_name(tx.get('id') or tx_name, 'transaction')}"
        refs.append({"ref": tx_ref, "kind": "transaction", "value": tx})
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
                refs.append({"ref": f"{tx_ref}.{key}.{_safe_name(sub_name, 'entry')}", "kind": key, "value": sub})
    for idx, item in enumerate(_as_list(fm.get("invariants"))):
        name = _item_name(item, idx, "invariant")
        refs.append({"ref": f"function_model.invariants.{_safe_name(name, 'invariant')}", "kind": "invariant", "value": item})
    return refs


def _cycle_model_leaf_refs(ssot: dict[str, Any]) -> list[dict[str, Any]]:
    cm = ssot.get("cycle_model") if isinstance(ssot.get("cycle_model"), dict) else {}
    refs: list[dict[str, Any]] = []
    for key in ("clock", "reset", "latency"):
        if cm.get(key) not in (None, "", [], {}):
            refs.append({"ref": f"cycle_model.{key}", "kind": key, "value": cm.get(key)})
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
            refs.append({"ref": f"cycle_model.{key}.{_safe_name(name, 'rule')}", "kind": key, "value": item})
    return refs


def _structural_leaf_refs(ssot: dict[str, Any]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for idx, item in enumerate(_as_list(ssot.get("parameters"))):
        name = _item_name(item, idx, "parameter")
        refs.append({"ref": f"parameters.{_safe_name(name, 'parameter')}", "kind": "parameter", "value": item})
    dataflow = ssot.get("dataflow") if isinstance(ssot.get("dataflow"), dict) else {}
    for key in ("paths", "streams", "channels", "flows"):
        for idx, item in enumerate(_as_list(dataflow.get(key))):
            name = _item_name(item, idx, key.rstrip("s") or "path")
            refs.append({"ref": f"dataflow.{key}.{_safe_name(name, 'path')}", "kind": f"dataflow_{key}", "value": item})
    memory = ssot.get("memory") if isinstance(ssot.get("memory"), dict) else {}
    for key in ("instances", "memories", "buffers", "queues", "fifos"):
        for idx, item in enumerate(_as_list(memory.get(key))):
            name = _item_name(item, idx, key.rstrip("s") or "memory")
            refs.append({"ref": f"memory.{key}.{_safe_name(name, 'memory')}", "kind": f"memory_{key}", "value": item})
    registers = ssot.get("registers") if isinstance(ssot.get("registers"), dict) else {}
    for key in ("register_map", "register_list", "config"):
        for idx, item in enumerate(_as_list(registers.get(key))):
            name = _item_name(item, idx, key.rstrip("s") or "register")
            refs.append({"ref": f"registers.{key}.{_safe_name(name, 'register')}", "kind": f"registers_{key}", "value": item})
    for idx, item in enumerate(_as_list(ssot.get("features"))):
        name = _item_name(item, idx, "feature")
        refs.append({"ref": f"features.{_safe_name(name, 'feature')}", "kind": "feature", "value": item})
    return refs


def _module_contracts(ssot: dict[str, Any], ip: str) -> tuple[list[dict[str, Any]], list[str], list[dict[str, Any]]]:
    modules = _active_rtl_modules(ssot, ip)
    top = _top_name(ssot, ip)
    leaf_refs = _function_model_leaf_refs(ssot) + _cycle_model_leaf_refs(ssot)
    structural_leaf_refs = _structural_leaf_refs(ssot)
    single_owner = len(modules) == 1
    refs_by_module: dict[str, list[str]] = {str(module["name"]): [] for module in modules}
    matches_by_module: dict[str, list[dict[str, str]]] = {str(module["name"]): [] for module in modules}
    structural_refs_by_module: dict[str, list[str]] = {str(module["name"]): [] for module in modules}
    structural_matches_by_module: dict[str, list[dict[str, str]]] = {str(module["name"]): [] for module in modules}
    orphan_refs: list[str] = []
    for item in leaf_refs:
        owner = _owner_for_leaf(item, modules, top, single_owner=single_owner)
        owner_name = owner.get("module") or ""
        ref = str(item["ref"])
        if owner_name and owner_name in refs_by_module:
            refs_by_module[owner_name].append(ref)
            matches_by_module[owner_name].append({
                "ref": ref,
                "matched_ref": str(owner.get("matched_ref") or ""),
            })
        else:
            orphan_refs.append(ref)
    for item in structural_leaf_refs:
        owner = _owner_for_leaf(item, modules, top, single_owner=single_owner)
        owner_name = owner.get("module") or ""
        ref = str(item["ref"])
        if owner_name and owner_name in structural_refs_by_module:
            structural_refs_by_module[owner_name].append(ref)
            structural_matches_by_module[owner_name].append({
                "ref": ref,
                "matched_ref": str(owner.get("matched_ref") or ""),
            })
    contracts: list[dict[str, Any]] = []
    for module in modules:
        module_leaf_refs = sorted(set(refs_by_module[str(module["name"])]))
        module_structural_refs = sorted(set(structural_refs_by_module[str(module["name"])]))
        refs = module.get("refs") if isinstance(module.get("refs"), list) else []
        raw_module = module.get("raw") if isinstance(module.get("raw"), dict) else {}
        if raw_module.get("wiring_only"):
            wiring_refs = [
                str(ref)
                for ref in refs
                if str(ref).split(".", 1)[0] in {"top_module", "io_list", "integration"}
            ]
            module_structural_refs = sorted({*module_structural_refs, *wiring_refs})
        elif (
            not refs
            and (
                str(module.get("name") or "") == top
                or Path(str(module.get("file") or "")).stem == top
            )
        ):
            module_structural_refs = sorted({*module_structural_refs, "top_module", "integration"})
        # ``_cycle_model_leaf_refs`` only extracts a fixed list of generic
        # cycle_model categories (pipeline, handshake_rules, …) so IP-specific
        # sections such as ``cycle_model.baud_generator`` never produce leaf
        # refs. When the SSOT manifest still lists those sections as
        # explicit owner refs (depth >= 2 — not just the bare top-level
        # section name) the module is correctly attributing semantic
        # ownership and should not be reported as blocked.
        specific_owner_refs = [r for r in refs if "." in str(r)]
        blocked = not bool(module_leaf_refs or module_structural_refs or specific_owner_refs)
        contracts.append({
            "name": module["name"],
            "kind": "rtl_module",
            "rtl_module": module["name"],
            "rtl_file": module["file"],
            "source_sections": sorted({ref.split(".", 1)[0] for ref in refs + module_leaf_refs + module_structural_refs if ref}),
            "ssot_refs": sorted({*refs, *module_leaf_refs, *module_structural_refs}),
            "function_model_refs": sorted(ref for ref in module_leaf_refs if ref.startswith("function_model.")),
            "cycle_model_refs": sorted(ref for ref in module_leaf_refs if ref.startswith("cycle_model.")),
            "structural_refs": module_structural_refs,
            "owner_matches": matches_by_module[str(module["name"])],
            "structural_owner_matches": structural_matches_by_module[str(module["name"])],
            "verification_scope": "module",
            "requires_module_equivalence": bool(module_leaf_refs),
            "blocked": blocked,
            "blocker": "" if not blocked else "module has no function_model, cycle_model, or structural SSOT ownership refs",
        })
    return contracts, sorted(orphan_refs), leaf_refs


def _fcov_bins(ssot: dict[str, Any]) -> list[dict[str, Any]]:
    bins = _scenario_bins(ssot)
    tr = ssot.get("test_requirements") if isinstance(ssot.get("test_requirements"), dict) else {}
    coverage_goals = tr.get("coverage_goals") if isinstance(tr.get("coverage_goals"), dict) else {}
    def _goal_domain(item: dict[str, Any]) -> str:
        raw = str(
            item.get("coverage_domain")
            or item.get("domain")
            or item.get("model")
            or item.get("coverage_type")
            or item.get("class")
            or item.get("source")
            or item.get("source_ref")
            or ""
        ).lower()
        if "cycle_model" in raw or any(tok in raw for tok in ("cycle", "handshake", "latency", "protocol", "fsm")):
            return "cycle"
        return "function"

    planned_bins = coverage_goals.get("planned_bins") if isinstance(coverage_goals.get("planned_bins"), list) else []
    for idx, item in enumerate(planned_bins):
        if not isinstance(item, dict):
            continue
        bid = _safe_name(item.get("id") or item.get("name"), f"planned_bin_{idx}")
        domain = _goal_domain(item)
        bins.append({
            "id": bid,
            "class": str(item.get("class") or "planned_functional"),
            "coverage_domain": domain,
            "source": f"test_requirements.coverage_goals.planned_bins[{idx}]",
            "source_ref": str(item.get("source_ref") or item.get("source") or ""),
            "description": str(item.get("description") or item.get("goal") or bid),
        })
    for key, domain in (("function", "function"), ("function_coverage", "function"), ("cycle", "cycle"), ("cycle_coverage", "cycle")):
        section = coverage_goals.get(key)
        if not isinstance(section, dict):
            continue
        section_bins = section.get("bins") or section.get("planned_bins") or section.get("coverage_bins") or []
        if not isinstance(section_bins, list):
            continue
        for idx, item in enumerate(section_bins):
            if not isinstance(item, dict):
                continue
            bid = _safe_name(item.get("id") or item.get("name"), f"{domain}_bin_{idx}")
            bins.append({
                "id": bid,
                "class": str(item.get("class") or domain),
                "coverage_domain": domain,
                "source": str(item.get("source") or item.get("source_ref") or f"test_requirements.coverage_goals.{key}.bins[{idx}]"),
                "source_ref": str(item.get("source_ref") or item.get("source") or ""),
                "description": str(item.get("description") or item.get("goal") or bid),
            })
    fm = ssot.get("function_model") if isinstance(ssot.get("function_model"), dict) else {}
    for idx, tx in enumerate(fm.get("transactions") or []):
        if isinstance(tx, dict):
            name = _safe_name(tx.get("name") or tx.get("id"), f"transaction_{idx}")
            bins.append({
                "id": f"function_{name}",
                "class": "transaction_type",
                "coverage_domain": "function",
                "source": f"function_model.transactions[{idx}]",
                "source_ref": f"function_model.transactions.{_safe_name(tx.get('id') or tx.get('name'), f'transaction_{idx}')}",
                "description": " ".join(
                    part
                    for part in (
                        str(tx.get("id") or "").strip(),
                        str(tx.get("description") or tx.get("expected") or name).strip(),
                    )
                    if part
                ),
            })
    cm = ssot.get("cycle_model") if isinstance(ssot.get("cycle_model"), dict) else {}
    def _add_cycle_bin(bid: str, klass: str, source: str, description: str) -> None:
        bins.append({
            "id": bid,
            "class": klass,
            "coverage_domain": "cycle",
            "source": source,
            "source_ref": source,
            "description": description,
        })

    for idx, rule in enumerate(cm.get("handshake_rules") or []):
        if isinstance(rule, dict):
            name = _safe_name(rule.get("name") or rule.get("id"), f"handshake_{idx}")
            _add_cycle_bin(f"cycle_{name}", "protocol", f"cycle_model.handshake_rules[{idx}]", str(rule.get("description") or rule))
    latency = cm.get("latency")
    if isinstance(latency, dict):
        for name, spec in latency.items():
            _add_cycle_bin(
                f"cycle_latency_{_safe_name(name, 'latency')}",
                "latency",
                f"cycle_model.latency.{name}",
                str(spec),
            )
    for idx, stage in enumerate(cm.get("pipeline") or []):
        if isinstance(stage, dict):
            name = _safe_name(stage.get("stage") or stage.get("name") or stage.get("id"), f"stage_{idx}")
            _add_cycle_bin(
                f"cycle_pipeline_{name}",
                "pipeline_stage",
                f"cycle_model.pipeline[{idx}]",
                str(stage.get("action") or stage),
            )
    for idx, rule in enumerate(cm.get("ordering") or []):
        _add_cycle_bin(
            f"cycle_ordering_{idx}",
            "ordering",
            f"cycle_model.ordering[{idx}]",
            str(rule),
        )
    for idx, rule in enumerate(cm.get("backpressure") or []):
        _add_cycle_bin(
            f"cycle_backpressure_{idx}",
            "backpressure",
            f"cycle_model.backpressure[{idx}]",
            str(rule),
        )
    perf = cm.get("performance") if isinstance(cm.get("performance"), dict) else {}
    for key in ("outstanding", "depth", "queue_depth", "pipeline_depth", "frequency_mhz", "throughput", "sustained_beats_per_cycle"):
        value = perf.get(key, cm.get(key))
        if value is None:
            continue
        klass = "frequency" if "frequency" in key else "throughput" if "throughput" in key or "beats" in key else "performance"
        _add_cycle_bin(
            f"cycle_perf_{_safe_name(key, 'metric')}",
            klass,
            f"cycle_model.performance.{key}",
            str(value),
        )
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
                    "coverage_domain": "cycle",
                    "source": f"fsm.{block_name}.transitions[{idx}]",
                    "source_ref": f"fsm.{block_name}.transitions[{idx}]",
                    "description": str(trn.get("condition") or trn),
                })
    err = ssot.get("error_handling") if isinstance(ssot.get("error_handling"), dict) else {}
    for idx, src in enumerate(err.get("error_sources") or []):
        name = _safe_name(src.get("name") if isinstance(src, dict) else src, f"error_{idx}")
        bins.append({
            "id": f"error_{name}",
            "class": "error",
            "coverage_domain": "function",
            "source": f"error_handling.error_sources[{idx}]",
            "source_ref": f"error_handling.error_sources[{idx}]",
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
            "structural_refs": contract.get("structural_refs", []),
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
        "units": units,
        "module_contracts": module_contracts,
        "orphan_function_cycle_refs": orphan_refs,
        "function_cycle_ref_count": len(leaf_refs),
        "authority_contract": _authority_contract(ip),
        "drives": ["rtl_module_plan", "tb_environment_plan", "functional_coverage_plan"],
        "complete": bool(units) and not orphan_refs and all(
            not item.get("blocked") or item.get("requires_module_equivalence") is False
            for item in module_contracts
        ),
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
    reduction_or = re.fullmatch(r"\|\s*\((.*)\)", text)
    if reduction_or:
        text = f"reduction_or({{reduction_or.group(1)}})"
    text = text.replace("&&", " and ").replace("||", " or ")
    text = re.sub(r"(?<![=!<>])!(?!=)", " not ", text)
    return text


def _literal_int(text):
    text = str(text).strip().replace("_", "")
    return bool(re.fullmatch(r"(?:0x[0-9a-fA-F]+|[0-9]+|[0-9]*'[hHdDbB][0-9a-fA-FxXzZ]+)", text))


def _h_bin_to_gray(value):
    v = _parse_int(value, 0)
    return v ^ (v >> 1)


def _h_gray_to_bin(value):
    g = _parse_int(value, 0)
    b = g
    s = g >> 1
    while s:
        b ^= s
        s >>= 1
    return b


def _h_popcount(value):
    return bin(_parse_int(value, 0) & ((1 << 256) - 1)).count("1")


def _h_parity(value):
    return _h_popcount(value) & 1


def _h_clog2(value):
    v = _parse_int(value, 0)
    if v <= 1:
        return 0
    return (v - 1).bit_length()


def _default_rule_helpers():
    return {{
        "bin_to_gray": _h_bin_to_gray,
        "gray_to_bin": _h_gray_to_bin,
        "popcount": _h_popcount,
        "parity": _h_parity,
        "clog2": _h_clog2,
        "min": lambda a, b: min(_parse_int(a, 0), _parse_int(b, 0)),
        "max": lambda a, b: max(_parse_int(a, 0), _parse_int(b, 0)),
        "abs": lambda a: abs(_parse_int(a, 0)),
        "any": lambda *args: int(any(
            _parse_int(a, 0) for a in (
                args[0] if len(args) == 1 and isinstance(args[0], (list, tuple, range)) else args
            )
        )),
        "all": lambda *args: int(all(
            _parse_int(a, 0) for a in (
                args[0] if len(args) == 1 and isinstance(args[0], (list, tuple, range)) else args
            )
        )),
        "sum": lambda *args: int(sum(
            _parse_int(a, 0) for a in (
                args[0] if len(args) == 1 and isinstance(args[0], (list, tuple, range)) else args
            )
        )),
        "len": lambda *args: len(args[0]) if len(args) == 1 and isinstance(args[0], (list, tuple, range)) else len(args),
    }}


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
    if isinstance(node, ast.Subscript):
        base = _eval_ast(node.value, env)
        sl = node.slice
        if isinstance(sl, ast.Index):
            sl = sl.value
        if isinstance(sl, ast.Slice):
            hi = _eval_ast(sl.lower, env) if sl.lower is not None else 0
            lo = _eval_ast(sl.upper, env) if sl.upper is not None else 0
            if hi < lo:
                hi, lo = lo, hi
            width = hi - lo + 1
            mask = (1 << width) - 1
            return (base >> lo) & mask
        idx = _eval_ast(sl, env)
        return (base >> idx) & 1
    if isinstance(node, ast.GeneratorExp):
        return _eval_comprehension(node, env, generator=True)
    if isinstance(node, ast.ListComp):
        return _eval_comprehension(node, env, generator=False)
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError(f"unsupported rule call {{ast.dump(node.func)}}")
        func = env.get(node.func.id)
        if not callable(func):
            raise ValueError(f"unsupported rule helper {{node.func.id}}")
        if node.keywords:
            raise ValueError(f"unsupported keyword args for rule helper {{node.func.id}}")
        args = [_eval_ast(arg, env) for arg in node.args]
        return _parse_int(func(*args), 0)
    raise ValueError(f"unsupported rule expression node {{type(node).__name__}}")


def _eval_comprehension(node, env, generator=False):
    """Evaluate a generator expression or list comprehension.

    Supports single-clause ``for`` with optional ``if`` filter, e.g.:
        ``(x for x in range(8) if x > 0)``
    Nested comprehensions are not supported.
    """
    if not node.generators:
        raise ValueError("comprehension with no generators")
    comp = node.generators[0]
    if len(node.generators) > 1:
        raise ValueError("nested comprehensions are not supported in rule expressions")
    if not isinstance(comp.target, ast.Name):
        raise ValueError("comprehension target must be a simple name")
    var_name = comp.target.id
    iter_values = _eval_iter(comp.iter, env)
    results = []
    for val in iter_values:
        local_env = dict(env)
        local_env[var_name] = val
        # Apply if-filters
        skip = False
        for if_clause in comp.ifs:
            if not _eval_ast(if_clause, local_env):
                skip = True
                break
        if skip:
            continue
        results.append(_eval_ast(node.elt, local_env))
    return results if not generator else results


def _eval_iter(node, env):
    """Evaluate an iterable source (range call or name reference)."""
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        if node.func.id == "range":
            args = [_eval_ast(a, env) for a in node.args]
            if len(args) == 1:
                return list(range(args[0]))
            if len(args) == 2:
                return list(range(args[0], args[1]))
            if len(args) == 3:
                return list(range(args[0], args[1], args[2]))
            raise ValueError(f"range() expects 1-3 args, got {{len(args)}}")
        # Other callables: evaluate and treat result as iterable if possible
        func = env.get(node.func.id)
        if callable(func):
            call_args = [_eval_ast(a, env) for a in node.args]
            result = func(*call_args)
            if isinstance(result, (list, tuple, range)):
                return list(result)
            return [_parse_int(result, 0)]
    if isinstance(node, ast.Name):
        val = env.get(node.id)
        if isinstance(val, (list, tuple, range)):
            return list(val)
        return [_parse_int(val, 0)]
    raise ValueError(f"unsupported iterable in comprehension: {{ast.dump(node)}}")


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
        self._declared_state_names = set(self.state_defaults)
        self.registers = self._register_defaults()
        self._enum_bindings = self._enum_value_bindings()
        self.trace = []

    def _enum_value_bindings(self):
        """Map every declared FSM/enum state NAME to its integer encoding so
        state_update exprs written as enum names (e.g. ``fsm_state = COUNT``)
        resolve in the rule evaluator. The declared enum order IS the encoding
        rtl-gen emits for the SystemVerilog localparams, so FL and RTL agree.
        Without these bindings _eval_ast raises 'unknown rule name COUNT' and the
        FSM trace state never advances past reset (campaign finding 36)."""
        bindings = {{}}
        fm = SSOT_MODEL.get("function_model") or {{}}
        sources = list(fm.get("state_variables") or [])
        regs = SSOT_MODEL.get("registers") or {{}}
        sources += list(regs.get("internal_state_registers") or [])
        for item in sources:
            if not isinstance(item, dict):
                continue
            enum = item.get("enum")
            if not isinstance(enum, (list, tuple)):
                continue
            for value, name in enumerate(enum):
                key = str(name).strip()
                if key and key not in bindings:
                    bindings[key] = value
        return bindings

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

    @staticmethod
    def _field_bounds(field):
        bits = field.get("bits")
        if isinstance(bits, (list, tuple)) and len(bits) >= 2:
            hi = _parse_int(bits[0], 0)
            lo = _parse_int(bits[1], 0)
            return (max(hi, lo), min(hi, lo))
        if "msb" in field and "lsb" in field:
            hi = _parse_int(field.get("msb"), 0)
            lo = _parse_int(field.get("lsb"), 0)
            return (max(hi, lo), min(hi, lo))
        if "lsb" in field and ("width" in field or "bit_width" in field):
            lo = _parse_int(field.get("lsb"), 0)
            width = max(1, _parse_int(field.get("width", field.get("bit_width", 1)), 1))
            return (lo + width - 1, lo)
        return (0, 0)

    def _state_name_for_register(self, reg):
        name = str(reg.get("name") or "").strip()
        if not name:
            return ""
        fm = SSOT_MODEL.get("function_model") or {{}}
        for row in fm.get("state_variables") or []:
            if not isinstance(row, dict):
                continue
            source = str(row.get("source") or "").strip().lower()
            state_name = str(row.get("name") or "").strip()
            if state_name and source == f"registers.{{name}}".lower():
                return state_name
        norm = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
        candidates = [
            norm,
            f"{{norm}}_reg",
            f"{{norm}}_q",
            f"{{norm}}_r",
            f"{{norm}}_value",
        ]
        for field in reg.get("fields") or []:
            if isinstance(field, dict):
                fname = re.sub(r"[^a-z0-9]+", "_", str(field.get("name") or "").lower()).strip("_")
                if fname:
                    candidates.extend([fname, f"{{fname}}_reg", f"{{fname}}_q", f"{{fname}}_r"])
        for candidate in candidates:
            if candidate in self.state:
                return candidate
        return ""

    def _register_read_value(self, reg):
        name = str(reg.get("name") or "")
        state_name = self._state_name_for_register(reg)
        if state_name:
            value = _parse_int(self.state.get(state_name), 0)
        else:
            value = _parse_int(self.registers.get(name, reg.get("reset", 0)), 0)
        for field in reg.get("fields") or []:
            if not isinstance(field, dict):
                continue
            fname = str(field.get("name") or "")
            if fname in self.state:
                fval = _parse_int(self.state.get(fname), 0)
            elif f"{{fname}}_q" in self.state:
                fval = _parse_int(self.state.get(f"{{fname}}_q"), 0)
            elif fname in self.registers:
                fval = _parse_int(self.registers.get(fname), 0)
            else:
                continue
            hi, lo = self._field_bounds(field)
            width = max(1, hi - lo + 1)
            mask = (1 << width) - 1
            value = (value & ~(mask << lo)) | ((fval & mask) << lo)
        return value

    def _read_mux(self, addr):
        addr_i = _parse_int(addr, 0)
        regs = SSOT_MODEL.get("registers") or {{}}
        for reg in regs.get("register_list") or []:
            if not isinstance(reg, dict):
                continue
            off = reg.get("offset")
            if off is not None and addr_i == _parse_int(off, 0):
                return self._register_read_value(reg)
        return 0

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

    def _derived_signal_items(self):
        fm = SSOT_MODEL.get("function_model") or {{}}
        return _rule_items(fm.get("derived_signals"))

    def _resolve_derived_signals(self, env):
        pending = []
        for idx, item in enumerate(self._derived_signal_items()):
            name = str(
                item.get("name")
                or item.get("signal")
                or item.get("output")
                or item.get("port")
                or f"derived_{{idx}}"
            )
            expr = item.get("expr", item.get("expression", item.get("value", "")))
            if name and expr not in (None, ""):
                pending.append((name, expr, item.get("width") or item.get("bits")))

        unresolved_errors = {{}}
        for _pass in range(max(len(pending), 1) + 1):
            progressed = False
            next_pending = []
            for name, expr, width in pending:
                try:
                    value = _eval_rule_expr(expr, env)
                except KeyError as exc:
                    unresolved_errors[name] = str(exc)
                    next_pending.append((name, expr, width))
                    continue
                if width is not None:
                    width_i = _parse_int(width, 0)
                    value &= (1 << max(width_i, 0)) - 1 if width_i > 0 else value
                env[name] = value
                unresolved_errors.pop(name, None)
                progressed = True
            pending = next_pending
            if not pending or not progressed:
                break
        return unresolved_errors

    @staticmethod
    def _norm_state_token(value):
        text = re.sub(r"[^a-z0-9]+", "_", str(value or "").lower()).strip("_")
        for suffix in ("_reg", "_q", "_r", "_ff"):
            if text.endswith(suffix):
                text = text[: -len(suffix)]
                break
        return text

    def _state_update_target(self, update_name):
        name = str(update_name or "").strip()
        if name in self._declared_state_names:
            return name
        norm_name = self._norm_state_token(name)
        best = ""
        best_len = 0
        for state_name in self._declared_state_names:
            norm_state = self._norm_state_token(state_name)
            if not norm_state:
                continue
            if norm_name == norm_state or norm_name.endswith("_" + norm_state) or f"_{{norm_state}}_" in norm_name:
                if len(norm_state) > best_len:
                    best = state_name
                    best_len = len(norm_state)
        return best

    def _rule_env(self, txn):
        env = {{}}
        env.update(_default_rule_helpers())
        env.update(self._enum_bindings)
        env.update(self.params)
        env.update(self.state)
        env.update(self.registers)
        env.update(txn)
        env["read_mux"] = self._read_mux
        env["reduction_or"] = lambda value: 1 if _parse_int(value, 0) != 0 else 0
        env.setdefault("true", 1)
        env.setdefault("false", 0)
        self._resolve_derived_signals(env)
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
                target = self._state_update_target(name)
                if target and target != name:
                    updates[target] = value
                    env[target] = value
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
            commit_updates = {{}}
            for update_name, value in updates.items():
                target = self._state_update_target(update_name)
                if target:
                    commit_updates[target] = value
                else:
                    commit_updates[update_name] = value
            self.state.update(commit_updates)
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
        # T1 #1 — Cardinal rule enforcement:
        # When SSOT does not declare structured output_rules/state_updates for
        # this transaction, do NOT fabricate state via name heuristics. Return
        # an SSOT-question-annotated result so the gap surfaces in the trace
        # and downstream validators can escalate to ssot-gen / human.
        return {{
            "resp": RESP_OKAY,
            "transaction_id": tx.get("id"),
            "transaction_name": tx.get("name"),
            "outputs_spec": tx.get("outputs") or [],
            "side_effects_spec": tx.get("side_effects") or [],
            "ssot_gap": (
                "structured output_rules/state_updates undefined for transaction "
                + str(tx.get("id") or tx.get("name") or "<unknown>")
            ),
            "synthetic_state": False,
        }}

    def apply(self, txn):
        txn = dict(txn or {{}})
        kind = self._norm(txn.get("kind") or txn.get("op") or txn.get("transaction") or "")
        tx = self._find_transaction(kind)
        if tx is not None:
            if self._norm(tx.get("name")) == "reset" or self._norm(tx.get("id")) in {{"reset", "fm_reset"}}:
                self.reset()
                return self._record(kind or "reset", txn, {{"kind": "reset", "resp": RESP_OKAY, "state": dict(self.state)}})
            return self._record(kind, txn, self._apply_primary(tx, txn))
        reg_result = self._apply_register_access(txn)
        if reg_result is not None:
            return self._record(kind or "register_access", txn, reg_result)
        if tx is None:
            return self._record(kind or "unknown", txn, {{"kind": kind or "unknown", "resp": RESP_SLVERR, "error": "unsupported_transaction"}})

    def _eval_precondition(self, expr, env):
        """Evaluate a single precondition string against env.

        SSOT preconditions are mostly Python-evaluable but occasionally carry
        a trailing natural-language clause in parentheses (e.g.
        '(req_i & req_mask) != 0 (at least one unmasked active request)').
        Normalize SQL-style OR/AND/NOT to Python operators, strip trailing
        natural-language parentheticals, and try progressively shorter
        prefixes until ast.parse succeeds. Unparseable preconditions are
        treated as True so they don't block transaction matching.
        """
        text = str(expr or "").strip()
        if not text:
            return True
        # Normalize boolean operators (SSOT prose sometimes uses uppercase).
        text = re.sub(r"\\bOR\\b", " or ",  text)
        text = re.sub(r"\\bAND\\b", " and ", text)
        text = re.sub(r"\\bNOT\\b", " not ", text)
        # Drop trailing parenthesized natural-language comments
        # ('something words ...'). Detect by alpha-majority content.
        def _strip_nl_tail(s):
            # Find a trailing " (...)" where contents are mostly alphabetic.
            depth = 0
            best_end = len(s)
            i = len(s) - 1
            # Walk from the right, capture the last balanced "(...)" tail.
            while i >= 0:
                ch = s[i]
                if ch == ")":
                    depth += 1
                elif ch == "(":
                    depth -= 1
                    if depth == 0:
                        inner = s[i + 1:best_end - 1]
                        alpha = sum(1 for c in inner if c.isalpha())
                        if alpha >= max(3, len(inner) // 2) and " " in inner:
                            # Natural language tail.
                            return s[:i].rstrip()
                        break
                i -= 1
            return s
        text = _strip_nl_tail(text)
        # Try ast.parse on the full string, then on progressively shorter
        # prefixes ending at a comparison/logical operator.
        candidates = [text]
        for tok in (" and ", " or "):
            for piece in text.split(tok):
                candidates.append(piece.strip())
        for cand in candidates:
            if not cand:
                continue
            try:
                tree = ast.parse(cand, mode="eval")
            except Exception:
                continue
            try:
                return bool(eval(compile(tree, "<precond>", mode="eval"), {{"__builtins__": {{}}}}, dict(env)))
            except Exception:
                continue
        return True

    def _select_transaction(self, inputs):
        """Pick the transaction whose preconditions all hold given inputs.

        Mutually-exclusive preconditions (typical SSOT pattern) yield a single
        active transaction. If multiple match, the first declared wins.
        Returns (tx, txn_payload) or (None, None) if none match.
        """
        env = dict(self.state)
        env.update(self.registers)
        env.update(inputs or {{}})
        for tx in self._transactions():
            if self._norm(tx.get("name")) == "reset" or self._norm(tx.get("id")) in {{"reset", "fm_reset"}}:
                continue
            preconds = [p for p in (tx.get("preconditions") or []) if isinstance(p, str)]
            if all(self._eval_precondition(p, env) for p in preconds):
                txn = {{"kind": tx.get("id") or tx.get("name")}}
                txn.update(inputs or {{}})
                return tx, txn
        return None, None

    def step(self, inputs=None):
        """Cycle-accurate step: select active transaction from preconditions,
        apply its output_rules and state_updates against current state and
        inputs, register the result. Mirrors the RTL's per-cycle behaviour
        when cocotb drives the same inputs cycle-by-cycle.

        Returns the structured result dict (same shape as apply()).
        """
        inputs = inputs or {{}}
        tx, txn = self._select_transaction(inputs)
        if tx is None:
            # No transaction matched preconditions: hold state, emit zero outputs.
            return {{"kind": "idle", "resp": RESP_OKAY, "state": dict(self.state)}}
        try:
            return self._record(tx.get("id") or "", txn, self._apply_primary(tx, txn))
        except KeyError as exc:
            # output_rule references a signal that's neither SSOT state, FL
            # register, nor caller-provided input (e.g. decoded combinational
            # signals: branch_taken, is_store). Surface a partial idle result
            # rather than crash — the per-cycle co-sim path treats this as
            # 'no comparable expected at this cycle for this IP'.
            return {{
                "kind": "step_unresolved",
                "resp": RESP_OKAY,
                "transaction_id": tx.get("id"),
                "transaction_name": tx.get("name"),
                "step_unresolved": str(exc),
            }}

    def csr_write(self, offset, data):
        """Apply an APB-style CSR write via _apply_register_access. Drives
        the registers dict + any state_variables sourced from those register
        fields (e.g. arb_enabled <- CTRL.enable)."""
        result = self._apply_register_access({{"kind": "csr_write", "op": "write", "addr": offset, "reg": offset, "data": data, "value": data}})
        # Mirror register field reset/source mapping into state_variables when
        # state_variables.source is a register field path.
        regs = SSOT_MODEL.get("registers") or {{}}
        reg_list = regs.get("register_list") or []
        fm = SSOT_MODEL.get("function_model") or {{}}
        state_vars = fm.get("state_variables") or []
        # Find which register matched the offset.
        matched_reg = None
        for r in reg_list:
            if r.get("offset") == offset:
                matched_reg = r
                break
        if matched_reg is None:
            return result
        for sv in state_vars:
            src = str(sv.get("source") or "")
            if not src.startswith("registers."):
                continue
            parts = src.split(".")
            if len(parts) >= 2 and parts[1] != matched_reg.get("name"):
                continue
            if len(parts) >= 3:
                field_name = parts[2]
                for f in matched_reg.get("fields") or []:
                    if f.get("name") == field_name:
                        bits = f.get("bits") or [0, 0]
                        hi, lo = (int(bits[0]), int(bits[1])) if len(bits) >= 2 else (0, 0)
                        mask = (1 << (hi - lo + 1)) - 1
                        self.state[sv.get("name")] = (data >> lo) & mask
                        break
            else:
                self.state[sv.get("name")] = data
        return result

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
        derived_signals = _rule_items((SSOT_MODEL.get("function_model") or {{}}).get("derived_signals"))
        rule_names = set()
        rule_names.update(_expr_names(tx.get("sample_condition", "")))
        for rule in output_rules + state_updates:
            rule_names.update(_expr_names(rule.get("expr", rule.get("expression", rule.get("value", "")))))
        for rule in derived_signals:
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
        derived_names = {{
            str(rule.get("name") or rule.get("signal") or rule.get("output") or rule.get("port"))
            for rule in derived_signals
            if rule.get("name") or rule.get("signal") or rule.get("output") or rule.get("port")
        }}
        known_names = set(model.params) | set(model.state) | set(model.registers) | output_names | update_names
        known_names.update(derived_names)
        known_names.update({{"true", "false", "True", "False", "and", "or", "not"}})
        known_names.update(_default_rule_helpers().keys())
        known_names.update({{"read_mux", "reduction_or", "range"}})
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

    # T1 #5 — invariants / reset / error_case coverage
    fm_block = SSOT_MODEL.get("function_model", {{}}) or {{}}
    invariants_raw = fm_block.get("invariants") or []
    if isinstance(invariants_raw, dict):
        invariants_raw = [{{"name": k, "expr": v}} for k, v in invariants_raw.items()]
    invariants = []
    for inv in invariants_raw:
        if isinstance(inv, str):
            invariants.append({{"name": inv[:40], "expr": inv}})
        elif isinstance(inv, dict):
            expr = inv.get("expr") or inv.get("expression") or inv.get("rule") or inv.get("invariant")
            if expr is None and len(inv) == 1:
                k, v = next(iter(inv.items())); expr = v if isinstance(v, str) else None
                inv = {{"name": str(k), "expr": expr}}
            if expr is not None:
                invariants.append({{"name": inv.get("name") or str(expr)[:40], "expr": expr}})
    invariants_eval_env = {{}}
    invariants_eval_env.update(_default_rule_helpers())
    invariants_eval_env.update(model.params)
    invariants_eval_env.update(model.state)
    invariants_eval_env.update(model.registers)
    invariants_evaluated = 0
    invariants_failed = []
    invariants_skipped = []
    for inv in invariants:
        try:
            ok = bool(_eval_rule_expr(inv["expr"], invariants_eval_env))
            invariants_evaluated += 1
            if not ok:
                invariants_failed.append({{"name": inv["name"], "expr": inv["expr"]}})
        except Exception as exc:
            invariants_skipped.append({{"name": inv["name"], "expr": inv["expr"], "reason": str(exc)[:80]}})

    reset_consistency = True
    reset_diff = {{}}
    try:
        baseline_defaults = dict(model.state_defaults)
        snapshot_model = FunctionalModel()
        snapshot_model.reset()
        for k, v in baseline_defaults.items():
            actual = snapshot_model.state.get(k)
            if actual != v:
                reset_consistency = False
                reset_diff[k] = {{"expected": v, "actual": actual}}
    except Exception as exc:
        reset_consistency = False
        reset_diff["__error__"] = str(exc)[:80]

    error_cases_total = 0
    error_cases_planned = 0
    for tx in txs:
        if not isinstance(tx, dict):
            continue
        cases = tx.get("error_cases") or []
        if isinstance(cases, list):
            error_cases_total += len(cases)
            error_cases_planned += sum(1 for c in cases if isinstance(c, dict) and c.get("condition"))

    overall_pass = all(checks) and not invariants_failed and reset_consistency

    return {{
        "passed": overall_pass,
        "checks": len(checks),
        "failed": checks.count(False),
        "transactions": len(txs),
        "transaction_results": results,
        "unsupported_transaction_check": unsupported.get("resp") == RESP_SLVERR,
        "trace_entries": len(model.trace),
        "coverage_bins": len(SSOT_MODEL.get("fcov_bins", [])),
        "invariants_total": len(invariants),
        "invariants_evaluated": invariants_evaluated,
        "invariants_failed": invariants_failed,
        "invariants_skipped": invariants_skipped,
        "reset_consistency": reset_consistency,
        "reset_diff": reset_diff,
        "error_cases_total": error_cases_total,
        "error_cases_planned": error_cases_planned,
    }}


if __name__ == "__main__":
    print(json.dumps(run_self_check(), indent=2))
'''


def _run_semantic_validation(ip: str, root: Path, *, use_llm: bool) -> dict[str, Any]:
    """Run the FL-vs-behavioral-contract semantic gate.

    Imported lazily so a fresh checkout missing the validator module degrades to an
    explicit ``not_run`` status (never a crash and never a silent pass).
    """
    try:
        from validate_fl_semantics import validate_fl_semantics
    except Exception as exc:  # pragma: no cover - defensive import guard
        return {
            "status": "not_run",
            "passed": True,
            "reason": f"semantic validator unavailable: {type(exc).__name__}: {exc}",
        }
    try:
        return validate_fl_semantics(ip, root, use_llm=use_llm)
    except Exception as exc:  # pragma: no cover - validator must not break emit
        return {
            "status": "not_run",
            "passed": True,
            "reason": f"semantic validation raised {type(exc).__name__}: {exc}",
        }


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
    parser.add_argument(
        "--no-semantic",
        action="store_true",
        help="skip the FL-vs-behavioral-contract semantic validation gate entirely",
    )
    parser.add_argument(
        "--no-semantic-llm",
        action="store_true",
        help="run the deterministic semantic backstop only (skip the LLM judge)",
    )
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

    # Semantic validation: the self-check only runs the FL model against itself
    # and never asks whether the FL transactions faithfully implement the locked
    # behavioral contracts. The semantic gate (deterministic backstop + optional
    # LLM judge) flags fictional state (e.g. an FSM/state_updates projected onto a
    # cycle-waived combinational IP) before the bad FL model reaches sim.
    semantic = _run_semantic_validation(args.ip, root, use_llm=not args.no_semantic_llm) \
        if not args.no_semantic else {"status": "skipped", "passed": True, "reason": "--no-semantic"}
    semantic_passed = bool(semantic.get("passed", True))

    report = {
        "schema_version": 1,
        "type": "fl_model_check",
        "ip": args.ip,
        "source": str(model_path.relative_to(ip_dir)),
        "passed": bool(check.get("passed")) and semantic_passed,
        "self_check": check,
        "semantic_validation": semantic,
        "decomposition_units": len(decomposition["units"]),
        "fcov_bins": len(bins),
        "authority_contract": _authority_contract(args.ip),
    }
    (model_dir / "fl_model_check.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    # T1 #4 — wall-clock metadata lives in manifest.json, not in payloads.
    manifest = {
        "schema_version": 1,
        "ip": args.ip,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "emitter": "fl-model-gen",
        "produced": [
            "model/functional_model.py",
            "model/decomposition.json",
            "model/fl_model_check.json",
            "cov/fcov_plan.json",
        ],
    }
    (model_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"[emit_fl_model] wrote {model_path}")
    print(f"[emit_fl_model] decomposition_units={len(decomposition['units'])} fcov_bins={len(bins)} passed={report['passed']}")
    if not semantic_passed:
        print(f"[emit_fl_model] SEMANTIC GATE FAIL: {semantic.get('reason', 'FL model violates locked behavioral contracts')}")
        for violation in semantic.get("violations", []) or []:
            if isinstance(violation, dict) and violation.get("detail"):
                print(f"  - {violation['detail']}")
    return 0 if report["passed"] and decomposition["units"] and bins else 1


if __name__ == "__main__":
    raise SystemExit(main())
