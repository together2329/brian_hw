from __future__ import annotations

from typing import Any


JsonDoc = dict[str, Any]


class BehavioralContractError(ValueError):
    pass


REF_KEYS = {
    "source_refs",
    "contract_refs",
    "contract_ref",
    "behavioral_contract_refs",
    "behavioral_contracts",
    "locked_truth_projection",
}
BEHAVIORAL_SSOT_SECTIONS = (
    "function_model",
    "cycle_model",
    "fsm",
    "registers",
    "interrupts",
    "test_requirements",
    "quality_gates",
    "rtl_contract",
    "features",
    "dataflow",
)
FUNCTION_MODEL_ROW_KEYS = (
    "transactions",
    "state_variables",
    "derived_signals",
    "invariants",
    "rules",
    "reset",
    "error_cases",
)
CYCLE_MODEL_ROW_KEYS = (
    "handshake_rules",
    "pipeline",
    "latency",
    "ordering",
    "backpressure",
    "arbitration",
    "observability",
    "reset",
    "performance",
    "timing",
    "scenarios",
)
FUNCTION_EFFECT_KEYS = {
    "decision_table",
    "truth_table",
    "then",
    "expect",
    "result",
    "outputs",
    "output_rules",
    "state_updates",
    "postconditions",
    "side_effects",
    "error_cases",
}
FUNCTION_CONDITION_KEYS = {"preconditions", "when", "sample_condition", "inputs", "input_map"}
CYCLE_MACHINE_KEYS = {
    "rule",
    "predicate",
    "sample_condition",
    "signal",
    "valid",
    "ready",
    "clock",
    "reset",
    "condition",
    "stage",
    "cycle",
    "action",
    "min_cycles",
    "max_cycles",
    "latency",
    "ordering",
    "stable",
    "hold",
    "until",
    "output_rules",
    "observables",
    "observability",
    "throughput",
    "outstanding",
    "depth",
    "backpressure",
}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _non_empty_str(value: Any) -> str:
    return value.strip() if isinstance(value, str) and value.strip() else ""


def _present(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        text = value.strip()
        return bool(text) and text.lower() not in {"none", "n/a", "na", "tbd", "todo", "unknown"}
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _id_from(entry: JsonDoc, keys: tuple[str, ...]) -> str:
    for key in keys:
        value = _non_empty_str(entry.get(key))
        if value:
            return value
    return ""


def _string_refs(value: Any) -> list[str]:
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    if not isinstance(value, list):
        return []
    refs: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            refs.append(item.strip())
        elif isinstance(item, dict):
            ref = _id_from(item, ("id", "name", "contract_ref", "contract_ref_id"))
            if ref:
                refs.append(ref)
    return sorted(dict.fromkeys(refs))


def _decision_rows(raw: Any) -> list[JsonDoc]:
    if isinstance(raw, dict):
        rows = raw.get("rows")
    else:
        rows = raw
    return [dict(item) for item in _as_list(rows) if isinstance(item, dict)]


def _truth_rows(raw: Any) -> list[JsonDoc]:
    if isinstance(raw, dict):
        rows = raw.get("rows")
    else:
        rows = raw
    return [dict(item) for item in _as_list(rows) if isinstance(item, dict)]


def _has_machine_behavior(entry: JsonDoc) -> bool:
    for key in ("decision_table", "state_transitions", "transactions", "rules", "truth_table", "invariants"):
        value = entry.get(key)
        if isinstance(value, list) and value:
            return True
        if isinstance(value, dict):
            rows = value.get("rows")
            if isinstance(rows, list) and rows:
                return True
    return False


def _validate_decision_table(rows: list[JsonDoc], issues: list[str], label: str) -> None:
    for index, row in enumerate(rows):
        row_label = f"{label}.decision_table[{index}]"
        if row.get("when") in (None, "", []):
            issues.append(f"{row_label} requires when")
        if not any(row.get(key) not in (None, "", [], {}) for key in ("then", "outputs", "state_updates", "expect", "result")):
            issues.append(f"{row_label} requires then/outputs/state_updates/expect/result")


def _validate_state_transitions(rows: list[Any], issues: list[str], label: str) -> None:
    for index, row in enumerate(rows):
        row_label = f"{label}.state_transitions[{index}]"
        if not isinstance(row, dict):
            issues.append(f"{row_label} entries must be objects")
            continue
        if not _non_empty_str(row.get("from")) and not _non_empty_str(row.get("from_state")):
            issues.append(f"{row_label} requires from/from_state")
        if not _non_empty_str(row.get("to")) and not _non_empty_str(row.get("to_state")):
            issues.append(f"{row_label} requires to/to_state")
        if row.get("when") in (None, "", []):
            issues.append(f"{row_label} requires when")


def _validate_transactions(rows: list[Any], issues: list[str], label: str) -> None:
    for index, row in enumerate(rows):
        row_label = f"{label}.transactions[{index}]"
        if not isinstance(row, dict):
            issues.append(f"{row_label} entries must be objects")
            continue
        if not _id_from(row, ("id", "name", "transaction_id")):
            issues.append(f"{row_label} requires id/name")
        if not any(row.get(key) not in (None, "", [], {}) for key in ("preconditions", "when", "outputs", "state_updates", "postconditions", "then")):
            issues.append(f"{row_label} requires preconditions/when plus outputs/state_updates/postconditions")


def _validate_stage_contracts(raw: Any, issues: list[str], label: str) -> list[JsonDoc]:
    result: list[JsonDoc] = []
    for index, entry in enumerate(_as_list(raw)):
        row_label = f"{label}.stage_contracts[{index}]"
        if not isinstance(entry, dict):
            issues.append(f"{row_label} entries must be objects")
            continue
        stage = _non_empty_str(entry.get("stage"))
        if not stage:
            issues.append(f"{row_label} requires stage")
        if not any(
            _non_empty_str(entry.get(key))
            for key in ("check", "validator", "artifact", "observable", "assertion", "pass_condition", "coverage")
        ):
            issues.append(f"{row_label} requires check/validator/artifact/observable/assertion/pass_condition")
        item = dict(entry)
        if stage:
            item["stage"] = stage
        result.append(item)
    return result


def normalize_behavioral_contracts(
    ip: str,
    raw: Any,
    *,
    known_obligation_ids: set[str] | None = None,
) -> JsonDoc:
    issues: list[str] = []
    if isinstance(raw, dict):
        if raw.get("ip") not in (None, ip):
            issues.append(f"behavioral_contracts ip mismatch: expected {ip}, got {raw.get('ip')!r}")
        contracts_raw = raw.get("contracts")
    elif isinstance(raw, list):
        contracts_raw = raw
    else:
        contracts_raw = None
    if not isinstance(contracts_raw, list) or not contracts_raw:
        issues.append("behavioral_contracts requires non-empty contracts[]")
        contracts_raw = []

    contracts: list[JsonDoc] = []
    contract_ids: set[str] = set()
    for entry in contracts_raw:
        if not isinstance(entry, dict):
            issues.append("behavioral_contracts contracts[] entries must be objects")
            continue
        contract_id = _id_from(entry, ("id", "behavioral_contract_id", "contract_id", "contract_ref_id"))
        if not contract_id:
            issues.append("behavioral contract requires id")
            contract_id = "<missing>"
        if contract_id in contract_ids:
            issues.append(f"duplicate behavioral contract id {contract_id}")
        contract_ids.add(contract_id)
        label = f"behavioral_contracts.{contract_id}"

        obligation_refs = _string_refs(entry.get("obligations", entry.get("obligation_refs")))
        if not obligation_refs:
            issues.append(f"{label} requires obligations[]")
        if known_obligation_ids is not None:
            for ref in obligation_refs:
                if ref not in known_obligation_ids:
                    issues.append(f"{label} references unknown obligation {ref}")

        if not _has_machine_behavior(entry):
            issues.append(
                f"{label} requires machine-readable behavior: "
                "decision_table, state_transitions, transactions, rules, truth_table, or invariants"
            )

        decision_table = _decision_rows(entry.get("decision_table"))
        if entry.get("decision_table") is not None:
            if not decision_table:
                issues.append(f"{label}.decision_table requires rows")
            _validate_decision_table(decision_table, issues, label)

        truth_table = _truth_rows(entry.get("truth_table"))
        if entry.get("truth_table") is not None and not truth_table:
            issues.append(f"{label}.truth_table requires rows")

        _validate_state_transitions(_as_list(entry.get("state_transitions")), issues, label)
        _validate_transactions(_as_list(entry.get("transactions")), issues, label)
        stage_contracts = _validate_stage_contracts(entry.get("stage_contracts"), issues, label)
        if not stage_contracts:
            issues.append(f"{label} requires stage_contracts[] so downstream stage ownership is explicit")

        item = dict(entry)
        item["id"] = contract_id
        item["obligations"] = obligation_refs
        item["stage_contracts"] = stage_contracts
        if decision_table:
            item["decision_table"] = decision_table
        if truth_table:
            item["truth_table"] = truth_table
        item.pop("behavioral_contract_id", None)
        item.pop("contract_id", None)
        item.pop("contract_ref_id", None)
        item.pop("obligation_refs", None)
        contracts.append(item)

    if issues:
        raise BehavioralContractError("; ".join(issues))
    return {
        "schema_version": 1,
        "type": "behavioral_contracts",
        "ip": ip,
        "contracts": sorted(contracts, key=lambda item: str(item["id"])),
    }


def behavioral_contract_ids(doc: JsonDoc) -> set[str]:
    return {
        str(item["id"])
        for item in _as_list(doc.get("contracts"))
        if isinstance(item, dict) and _non_empty_str(item.get("id"))
    }


def behavioral_contract_map(doc: JsonDoc) -> dict[str, JsonDoc]:
    return {
        str(item["id"]): item
        for item in _as_list(doc.get("contracts"))
        if isinstance(item, dict) and _non_empty_str(item.get("id"))
    }


def behavioral_obligation_refs(doc: JsonDoc) -> dict[str, list[str]]:
    refs: dict[str, list[str]] = {}
    for contract in _as_list(doc.get("contracts")):
        if not isinstance(contract, dict):
            continue
        contract_id = _non_empty_str(contract.get("id"))
        if not contract_id:
            continue
        for obligation_id in _string_refs(contract.get("obligations")):
            refs.setdefault(obligation_id, []).append(contract_id)
    return {key: sorted(dict.fromkeys(value)) for key, value in refs.items()}


def _strings(value: Any) -> set[str]:
    if isinstance(value, str):
        return {value}
    if isinstance(value, list):
        result: set[str] = set()
        for item in value:
            result.update(_strings(item))
        return result
    if isinstance(value, dict):
        result: set[str] = set()
        for item in value.values():
            result.update(_strings(item))
        return result
    return set()


def _collect_refs(value: Any) -> set[str]:
    if isinstance(value, dict):
        result: set[str] = set()
        for key, item in value.items():
            if str(key) in REF_KEYS:
                result.update(_strings(item))
            result.update(_collect_refs(item))
        return result
    if isinstance(value, list):
        result: set[str] = set()
        for item in value:
            result.update(_collect_refs(item))
        return result
    return set()


def _path_token(value: Any, fallback: str) -> str:
    text = str(value or fallback).strip()
    if not text:
        return fallback
    return ".".join(part for part in text.replace("/", "_").replace(" ", "_").split(".") if part) or fallback


def _row_path(root: str, key: str, index: int, entry: JsonDoc) -> str:
    ident = _id_from(entry, ("id", "name", "transaction_id", "rule_id", "signal", "stage", "state"))
    suffix = _path_token(ident, f"[{index}]")
    if suffix.startswith("["):
        return f"{root}.{key}{suffix}"
    return f"{root}.{key}.{suffix}"


def _iter_model_rows(section_value: Any, root: str, row_keys: tuple[str, ...]) -> list[tuple[str, str, JsonDoc]]:
    if not isinstance(section_value, dict):
        return []
    rows: list[tuple[str, str, JsonDoc]] = []
    for key in row_keys:
        value = section_value.get(key)
        if isinstance(value, list):
            for index, item in enumerate(value):
                if isinstance(item, dict):
                    rows.append((_row_path(root, key, index, item), key, item))
                elif _present(item):
                    rows.append((f"{root}.{key}[{index}]", key, {"value": item}))
            continue
        if isinstance(value, dict):
            if _collect_refs(value):
                rows.append((f"{root}.{key}", key, value))
            for name, item in value.items():
                if isinstance(item, dict):
                    rows.append((f"{root}.{key}.{_path_token(name, 'item')}", key, item))
                elif isinstance(item, list):
                    for index, child in enumerate(item):
                        if isinstance(child, dict):
                            rows.append((f"{root}.{key}.{_path_token(name, 'item')}[{index}]", key, child))
                elif _present(item) and key in {"latency", "performance", "reset", "timing"}:
                    rows.append((f"{root}.{key}.{_path_token(name, 'item')}", key, {"value": item}))
    return rows


def _machine_value(key: str, value: Any) -> bool:
    if key in REF_KEYS or key in {"id", "name", "description", "source_refs", "contract_refs"}:
        return False
    if key in {"decision_table", "truth_table"}:
        if isinstance(value, dict):
            rows = value.get("rows")
            return isinstance(rows, list) and bool(rows)
        return isinstance(value, list) and bool(value)
    if isinstance(value, dict):
        return any(_machine_value(str(child_key), child) for child_key, child in value.items())
    if isinstance(value, list):
        if not value:
            return False
        if key in {"outputs", "inputs"}:
            return any(isinstance(item, dict) or ("=" in str(item) or ":" in str(item)) for item in value)
        return True
    if isinstance(value, str):
        return key in {
            "expr",
            "when",
            "condition",
            "rule",
            "predicate",
            "sample_condition",
            "signal",
            "valid",
            "ready",
            "clock",
            "reset",
            "stage",
            "then",
            "expect",
            "result",
            "action",
        } and _present(value)
    return _present(value)


def _has_any_machine_key(entry: JsonDoc, keys: set[str]) -> bool:
    return any(_machine_value(key, entry.get(key)) for key in keys if key in entry)


def _has_function_semantics(entry: JsonDoc, row_key: str) -> bool:
    if row_key == "transactions":
        has_condition = _has_any_machine_key(entry, FUNCTION_CONDITION_KEYS) or _machine_value(
            "decision_table", entry.get("decision_table")
        ) or _machine_value("truth_table", entry.get("truth_table"))
        has_effect = _has_any_machine_key(entry, FUNCTION_EFFECT_KEYS)
        return has_condition and has_effect
    if row_key == "state_variables":
        return any(_machine_value(key, entry.get(key)) for key in ("width", "reset", "expr", "source", "type"))
    return _has_any_machine_key(entry, FUNCTION_EFFECT_KEYS | FUNCTION_CONDITION_KEYS | {"expr", "rule", "condition"})


def _has_cycle_semantics(entry: JsonDoc, row_key: str) -> bool:
    if row_key == "handshake_rules":
        has_signal = any(_machine_value(key, entry.get(key)) for key in ("signal", "valid", "ready"))
        has_rule = any(_machine_value(key, entry.get(key)) for key in ("rule", "predicate", "sample_condition", "condition"))
        return has_signal and has_rule
    if row_key == "pipeline":
        has_stage = any(_machine_value(key, entry.get(key)) for key in ("stage", "cycle"))
        has_action = any(_machine_value(key, entry.get(key)) for key in ("action", "output_rules", "state_updates", "condition"))
        return has_stage and has_action
    if row_key == "latency":
        return any(_machine_value(key, entry.get(key)) for key in ("min_cycles", "max_cycles", "cycles", "value"))
    return _has_any_machine_key(entry, CYCLE_MACHINE_KEYS)


def _model_hits(
    ssot_doc: JsonDoc,
    contract_id: str,
    *,
    section: str,
    row_keys: tuple[str, ...],
    semantic_check: Any,
) -> list[JsonDoc]:
    hits: list[JsonDoc] = []
    section_value = ssot_doc.get(section) if isinstance(ssot_doc, dict) else None
    for path, row_key, entry in _iter_model_rows(section_value, section, row_keys):
        if contract_id not in _collect_refs(entry):
            continue
        hits.append({"path": path, "row": row_key, "machine": bool(semantic_check(entry, row_key))})
    return hits


def _cycle_model_waived(contract: JsonDoc) -> bool:
    for key in ("cycle_model_waiver", "cycle_waiver", "cycle_model_not_applicable", "no_cycle_model"):
        if _present(contract.get(key)):
            return True
    return False


def compare_behavioral_to_ssot(behavioral_doc: JsonDoc, ssot_doc: JsonDoc) -> tuple[list[str], JsonDoc]:
    issues: list[str] = []
    contract_ids = behavioral_contract_ids(behavioral_doc)
    section_refs: set[str] = set()
    section_hits: dict[str, list[str]] = {}
    for section in BEHAVIORAL_SSOT_SECTIONS:
        value = ssot_doc.get(section) if isinstance(ssot_doc, dict) else None
        refs = _collect_refs(value)
        hits = sorted(contract_ids & refs)
        if hits:
            section_hits[section] = hits
        section_refs.update(refs)
    for contract_id in sorted(contract_ids - section_refs):
        issues.append(
            f"behavioral contract {contract_id} is not projected into SSOT behavior sections "
            "(function_model/cycle_model/fsm/registers/test_requirements/quality_gates)"
        )
    summary: JsonDoc = {
        "contract_refs": sorted(contract_ids),
        "behavioral_sections": sorted(section_hits),
        "section_hits": section_hits,
        "matched": sorted(contract_ids & section_refs),
    }
    return issues, summary


def compare_behavioral_to_function_cycle(behavioral_doc: JsonDoc, ssot_doc: JsonDoc) -> tuple[list[str], JsonDoc]:
    """Check locked behavioral contracts are projected as real FL/CL model rows.

    `compare_behavioral_to_ssot` is intentionally broad: it proves a behavioral
    contract is reflected somewhere in the Design Spec. This gate is narrower
    and stronger. It rejects anchor-only projection where a contract ID appears
    in traceability or on an empty model row but does not carry executable
    function/cycle semantics.
    """

    issues: list[str] = []
    contracts = behavioral_contract_map(behavioral_doc)
    function_hits: dict[str, list[str]] = {}
    cycle_hits: dict[str, list[str]] = {}
    function_anchor_only: dict[str, list[str]] = {}
    cycle_anchor_only: dict[str, list[str]] = {}
    cycle_waived: list[str] = []

    for contract_id, contract in sorted(contracts.items()):
        function_rows = _model_hits(
            ssot_doc,
            contract_id,
            section="function_model",
            row_keys=FUNCTION_MODEL_ROW_KEYS,
            semantic_check=_has_function_semantics,
        )
        cycle_rows = _model_hits(
            ssot_doc,
            contract_id,
            section="cycle_model",
            row_keys=CYCLE_MODEL_ROW_KEYS,
            semantic_check=_has_cycle_semantics,
        )
        function_machine = [str(item["path"]) for item in function_rows if item.get("machine")]
        cycle_machine = [str(item["path"]) for item in cycle_rows if item.get("machine")]
        function_anchor = [str(item["path"]) for item in function_rows if not item.get("machine")]
        cycle_anchor = [str(item["path"]) for item in cycle_rows if not item.get("machine")]
        if function_machine:
            function_hits[contract_id] = sorted(function_machine)
        elif function_anchor:
            function_anchor_only[contract_id] = sorted(function_anchor)
            issues.append(
                f"behavioral contract {contract_id} has anchor-only function_model projection at "
                f"{', '.join(sorted(function_anchor))}; add preconditions plus output_rules/state_updates "
                "or decision_table rows"
            )
        else:
            issues.append(
                f"behavioral contract {contract_id} is not projected into a function_model row with "
                "behavioral contract_refs"
            )

        if _cycle_model_waived(contract):
            cycle_waived.append(contract_id)
        elif cycle_machine:
            cycle_hits[contract_id] = sorted(cycle_machine)
        elif cycle_anchor:
            cycle_anchor_only[contract_id] = sorted(cycle_anchor)
            issues.append(
                f"behavioral contract {contract_id} has anchor-only cycle_model projection at "
                f"{', '.join(sorted(cycle_anchor))}; add handshake/latency/pipeline/ordering/backpressure "
                "machine rules or an explicit cycle_model_waiver"
            )
        else:
            issues.append(
                f"behavioral contract {contract_id} is not projected into a cycle_model row with "
                "behavioral contract_refs; add timing/protocol rows or an explicit cycle_model_waiver"
            )

    summary: JsonDoc = {
        "contract_refs": sorted(contracts),
        "function_model_hits": function_hits,
        "cycle_model_hits": cycle_hits,
        "function_anchor_only": function_anchor_only,
        "cycle_anchor_only": cycle_anchor_only,
        "cycle_model_waived": sorted(cycle_waived),
        "matched_function_model": sorted(function_hits),
        "matched_cycle_model": sorted(set(cycle_hits) | set(cycle_waived)),
    }
    return issues, summary
