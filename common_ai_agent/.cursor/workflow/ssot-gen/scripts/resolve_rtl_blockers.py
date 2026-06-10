#!/usr/bin/env python3
"""Apply RTL semantic blocker answers back into the SSOT.

The input is generic rtl-gen blocker evidence, not an IP-specific template.
Each answer is stored under custom.rtl_blocker_resolutions and, when the
blocker type is recognized, projected into the SSOT sections downstream tools
already consume: function_model, cycle_model, registers, error_handling,
test_requirements, traceability, and generation_flow.
"""

from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path
from typing import Any

import yaml


_MODULE_CONTRACT_KEYS = (
    "implements",
    "responsibility",
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
    "inputs",
    "outputs",
    "ports",
    "connections",
    "internal_interfaces",
    "wiring_only",
)

_CONNECTION_CONTRACT_QIDS = {
    "RTL_RESOLVE_CONNECTION_CONTRACTS",
    "RTL_CONNECTION_CONTRACTS",
    "RTL_MANIFEST_CONNECTION_CONTRACTS",
}

_CONNECTION_CONTAINER_KEYS = (
    "connection_contracts",
    "integration_connections",
    "module_connections",
    "connections",
    "contracts",
)

_CONNECTION_OPTIONAL_STRING_KEYS = (
    "instance",
    "direction",
    "source_ref",
    "ssot_ref",
    "source",
    "sink",
    "width",
    "clock_domain",
    "reset_domain",
    "tieoff",
    "reason",
)

_CONNECTION_OPTIONAL_BOOL_KEYS = (
    "allow_constant",
    "allow_unused",
)


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
        return doc if isinstance(doc, dict) else {}
    except Exception:
        return {}


def _load_answers(root: Path, ip: str, answers_path: Path | None) -> list[dict[str, Any]]:
    if answers_path is not None:
        doc = _load_json(answers_path)
    else:
        doc = _load_json(root / ".session" / ip / "ssot-gen" / "state.json")
    answers = doc.get("rtl_blocker_answers") if isinstance(doc, dict) else []
    if not isinstance(answers, list):
        return []
    return [a for a in answers if isinstance(a, dict)]


def _suggested_target_scale_answer(blocker: dict[str, Any]) -> dict[str, Any]:
    qdoc = _question_doc(blocker, "RTL_TARGET_SCALE_POLICY")
    suggested = qdoc.get("suggested_ssot_target_scale") if isinstance(qdoc.get("suggested_ssot_target_scale"), dict) else {}
    if not suggested:
        raise SystemExit("[resolve_rtl_blockers] RTL_TARGET_SCALE_POLICY has no suggested_ssot_target_scale")
    return {
        "id": "RTL_TARGET_SCALE_POLICY",
        "answer": "Use the suggested target scale candidate after human architecture review.",
    }


_MODULE_CONTRACT_QIDS = {
    "RTL_MODULE_CONTRACTS",
    "RTL_DYNAMIC_TODO_OWNERSHIP",
    "SSOT_BEHAVIOR_OWNERSHIP",
    "RTL_MODULE_BEHAVIOR_MATCH",
}


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value or "").strip()
    return [text] if text else []


def _question_ref_list(qdoc: dict[str, Any], key: str) -> list[str]:
    available = qdoc.get("available_refs") if isinstance(qdoc.get("available_refs"), dict) else {}
    return _string_list(available.get(key))


def _default_module_implements(name: str, file_name: str) -> str:
    text = f"{name} {file_name}".lower()
    if "read" in text:
        return "Owns DMA read-side transaction behavior from SSOT dataflow and cycle model evidence."
    if "write" in text:
        return "Owns DMA write-side transaction behavior from SSOT dataflow and cycle model evidence."
    if "fifo" in text or "queue" in text:
        return "Owns buffering and backpressure behavior between SSOT dataflow producers and consumers."
    if "irq" in text or "interrupt" in text:
        return "Owns interrupt/status behavior traced to SSOT error handling, registers, and test requirements."
    if "csr" in text or "reg" in text:
        return "Owns register-visible control/status behavior traced to SSOT registers and function model evidence."
    return "Owns the SSOT behavior assigned to this manifest RTL module."


def _recommended_module_contract_rows(qdoc: dict[str, Any]) -> list[dict[str, Any]]:
    modules = qdoc.get("missing_modules")
    if not isinstance(modules, list) or not modules:
        modules = qdoc.get("candidate_modules")
    if not isinstance(modules, list):
        modules = []

    source_sections = _question_ref_list(qdoc, "source_sections") or [
        "features",
        "io_list",
        "parameters",
        "function_model",
        "cycle_model",
        "dataflow",
        "fsm",
        "test_requirements",
    ]
    function_model_refs = _question_ref_list(qdoc, "function_model_refs")
    decomposition_refs = _question_ref_list(qdoc, "decomposition_refs")
    cycle_model_refs = _question_ref_list(qdoc, "cycle_model_refs")
    feature_refs = _question_ref_list(qdoc, "feature_refs")
    dataflow_refs = _question_ref_list(qdoc, "dataflow_refs")
    register_refs = _question_ref_list(qdoc, "register_refs")
    fsm_refs = _question_ref_list(qdoc, "fsm_refs")
    test_refs = _question_ref_list(qdoc, "test_refs")
    ports = _question_ref_list(qdoc, "ports")
    interfaces = _question_ref_list(qdoc, "interfaces") or ["control_data"]

    orphan_refs = _string_list(qdoc.get("orphan_refs"))
    if orphan_refs:
        function_model_refs = sorted({
            *function_model_refs,
            *(ref for ref in orphan_refs if ref == "function_model" or ref.startswith("function_model.")),
        })
        decomposition_refs = sorted({
            *decomposition_refs,
            *(ref for ref in orphan_refs if ref in {"decomposition", "functional_decomposition"} or ref.startswith(("decomposition.", "functional_decomposition."))),
        })

    rows: list[dict[str, Any]] = []
    for item in modules:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name") or item.get("module") or Path(str(item.get("file") or "")).stem).strip()
        file_name = str(item.get("file") or "").strip()
        if not name:
            continue
        rows.append({
            "name": name,
            "file": file_name,
            "implements": [_default_module_implements(name, file_name)],
            "source_sections": source_sections,
            "function_model_refs": function_model_refs,
            "decomposition_refs": decomposition_refs,
            "cycle_model_refs": cycle_model_refs,
            "feature_refs": feature_refs,
            "dataflow_refs": dataflow_refs,
            "register_refs": register_refs,
            "fsm_refs": fsm_refs,
            "test_refs": test_refs,
            "ports": ports,
            "internal_interfaces": interfaces,
            "wiring_only": False,
        })
    return rows


def _recommended_default_answers(blocker: dict[str, Any]) -> list[dict[str, Any]]:
    questions = blocker.get("questions") if isinstance(blocker.get("questions"), list) else []
    answers: list[dict[str, Any]] = []
    for qdoc in questions:
        if not isinstance(qdoc, dict):
            continue
        qid = str(qdoc.get("id") or "").strip()
        if qid in _MODULE_CONTRACT_QIDS:
            rows = _recommended_module_contract_rows(qdoc)
            if rows:
                answers.append({
                    "id": qid,
                    "answer": "Use the blocker recommended default: repair sub_modules into a module contract ledger using available SSOT refs.",
                    "module_contracts": rows,
                })
        elif qid == "RTL_TARGET_SCALE_POLICY":
            answers.append(_suggested_target_scale_answer(blocker))
    return answers


def _ensure_dict(parent: dict[str, Any], key: str) -> dict[str, Any]:
    val = parent.get(key)
    if not isinstance(val, dict):
        val = {}
        parent[key] = val
    return val


def _ensure_list(parent: dict[str, Any], key: str) -> list[Any]:
    val = parent.get(key)
    if not isinstance(val, list):
        val = []
        parent[key] = val
    return val


def _norm_id(text: str) -> str:
    out = re.sub(r"[^a-zA-Z0-9]+", "_", text.lower()).strip("_")
    return out[:72] or "rtl_blocker_resolution"


def _find_txn(doc: dict[str, Any], txn_id: str) -> dict[str, Any]:
    fm = _ensure_dict(doc, "function_model")
    txns = _ensure_list(fm, "transactions")
    for txn in txns:
        if isinstance(txn, dict) and str(txn.get("id") or "").upper() == txn_id.upper():
            return txn
    txn = {"id": txn_id, "name": txn_id.lower(), "preconditions": [], "inputs": [], "outputs": [], "side_effects": [], "error_cases": []}
    txns.append(txn)
    return txn


def _answer_text(answer: dict[str, Any]) -> str:
    text = str(answer.get("answer") or answer.get("custom") or "").strip()
    selected = answer.get("selected")
    if not text and isinstance(selected, list):
        text = "; ".join(str(x) for x in selected if str(x).strip())
    return text or "Engineer selected the recommended option; see rtl_blocker_resolutions."


def _append_unique(items: list[Any], item: Any) -> None:
    if item not in items:
        items.append(item)


def _apply_primary_rules(doc: dict[str, Any], answer: dict[str, Any]) -> None:
    txn = _find_txn(doc, "FM_PRIMARY")
    text = _answer_text(answer)
    state_updates = _ensure_list(txn, "state_updates")
    output_rules = _ensure_list(txn, "output_rules")
    counter_rules = _ensure_list(txn, "counter_rules")
    event_rules = _ensure_list(txn, "event_rules")
    _append_unique(state_updates, {
        "id": "primary_accept_updates",
        "when": "valid input transaction or packet is accepted under cycle_model handshake",
        "updates": ["busy", "status fields", "error state", "datapath state", "counter state"],
        "source": text,
    })
    _append_unique(output_rules, {
        "id": "primary_observable_outputs",
        "when": "function_model primary transaction reaches observe point",
        "outputs": ["protocol response/status", "debug busy/error", "interrupt/status side effects"],
        "source": text,
    })
    _append_unique(counter_rules, {
        "id": "primary_counter_updates",
        "when": "accepted transaction completes or is classified as malformed/error",
        "counters": "increment only the counters named in registers.register_list or approved event policy",
        "source": text,
    })
    _append_unique(event_rules, {
        "id": "primary_event_latching",
        "when": "packet/transaction done, mismatch, malformed, or approved event source occurs",
        "events": "latch status/interrupt events until reset or approved clear/W1C policy",
        "source": text,
    })


def _crc_policy_from_answer(text: str) -> dict[str, Any]:
    low = text.lower()
    compute_only = "no trailer" in low or "compute only" in low
    sideband = "sideband" in low
    return {
        "expected_crc_source": "sideband" if sideband else ("none_compute_only" if compute_only else "last_4_valid_packet_bytes"),
        "include_trailer_bytes_in_crc": False if not compute_only else None,
        "trailer_endianness": "network_byte_order" if "network" in low or not compute_only else "not_applicable",
        "refin": "unspecified_false_until_overridden",
        "refout": "unspecified_false_until_overridden",
        "xorout": "0x00000000_unless_overridden",
        "residue": "compare_final_crc_to_expected_source" if not compute_only else "not_applicable",
        "source": text,
    }


def _apply_crc_policy(doc: dict[str, Any], answer: dict[str, Any]) -> None:
    text = _answer_text(answer)
    fm = _ensure_dict(doc, "function_model")
    policy = _crc_policy_from_answer(text)
    fm["crc_stream_policy"] = policy
    txn = _find_txn(doc, "FM_PRIMARY")
    _ensure_list(txn, "datapath_rules")
    _append_unique(txn["datapath_rules"], {
        "id": "crc32_stream_policy",
        "operation": "compute CRC32 over accepted AXI4-Stream payload bytes according to crc_stream_policy",
        **policy,
    })
    test_req = _ensure_dict(doc, "test_requirements")
    scenarios = _ensure_list(test_req, "scenarios")
    sid = "SC_CRC_POLICY"
    if not any(isinstance(s, dict) and s.get("id") == sid for s in scenarios):
        scenarios.append({
            "id": sid,
            "name": "crc_stream_policy",
            "stimulus": "Drive packet payload and expected CRC according to function_model.crc_stream_policy.",
            "expected": "RTL CRC result, pass/fail status, counters, and irq side effects match FunctionalModel.",
            "checker": "FL scoreboard compares computed CRC and event classification.",
            "coverage": ["crc_policy", "expected_crc_source", "residue"],
        })


def _apply_axis_tkeep_policy(doc: dict[str, Any], answer: dict[str, Any]) -> None:
    text = _answer_text(answer)
    low = text.lower()
    policy = {
        "tkeep_byte_order": "little_endian_lane" if "least" in low or "little" in low else ("big_endian_lane" if "most" in low or "big" in low else "lane_index_order"),
        "invalid_tkeep": "non_contiguous_tkeep_is_malformed" if "non-contiguous" in low or "sparse" in low else "all_masks_legal",
        "zero_tkeep": "ignored_unless_tlast" if "zero" in low and "ignored" in low else "defined_by_function_model",
        "source": text,
    }
    cm = _ensure_dict(doc, "cycle_model")
    cm["axis_tkeep_policy"] = policy
    rules = _ensure_list(cm, "handshake_rules")
    _append_unique(rules, {
        "signal": "axis_tkeep",
        "rule": (
            f"tkeep_byte_order={policy['tkeep_byte_order']}; "
            f"invalid_tkeep={policy['invalid_tkeep']}; zero_tkeep={policy['zero_tkeep']}"
        ),
    })
    err = _ensure_dict(doc, "error_handling")
    sources = _ensure_list(err, "error_sources")
    if policy["invalid_tkeep"] != "all_masks_legal":
        _append_unique(sources, {
            "id": "ERR_AXIS_TKEEP",
            "condition": policy["invalid_tkeep"],
            "architectural_effect": "malformed/error status and interrupt policy follow function_model event_rules",
        })


def _apply_apb_policy(doc: dict[str, Any], answer: dict[str, Any]) -> None:
    text = _answer_text(answer)
    low = text.lower()
    use_error = "pslverr=1" in low or "error" in low
    policy = {
        "pslverr_on_decode_error": bool(use_error),
        "illegal_read_returns": "zero",
        "illegal_write_policy": "ignored_with_error_status" if use_error else "ignored",
        "unmapped_read_data": "zero",
        "status_side_effect": "set error/malformed status" if use_error else "none",
        "source": text,
    }
    regs = _ensure_dict(doc, "registers")
    cfg = _ensure_dict(regs, "config")
    cfg["access_policy"] = policy
    err = _ensure_dict(doc, "error_handling")
    err["apb_illegal_access_policy"] = policy


def _apply_optional_policy(doc: dict[str, Any], answer: dict[str, Any]) -> None:
    text = _answer_text(answer)
    custom = _ensure_dict(doc, "custom")
    custom["optional_behavior_policy"] = {
        "resolution": text,
        "rule": "Optional behavior must be represented as required, unsupported, or controlled by explicit parameter/register state.",
    }


def _io_ports(doc: dict[str, Any], *, direction: str | None = None) -> list[str]:
    ports: list[str] = []
    io = doc.get("io_list") if isinstance(doc.get("io_list"), dict) else {}
    for group in ("clock_domains", "resets", "interfaces"):
        for entry in io.get(group) or []:
            if not isinstance(entry, dict):
                continue
            for port in entry.get("ports") or []:
                if not isinstance(port, dict) or not port.get("name"):
                    continue
                pdir = str(port.get("direction") or "input").lower()
                if direction is None or pdir == direction:
                    ports.append(str(port["name"]))
    seen: set[str] = set()
    out: list[str] = []
    for port in ports:
        if port not in seen:
            seen.add(port)
            out.append(port)
    return out


def _pick_named_port(text: str, candidates: list[str]) -> str:
    words = {w.lower() for w in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", text or "")}
    for cand in candidates:
        if cand.lower() in words:
            return cand
    return candidates[0] if candidates else ""


def _apply_rtl_clock_port(doc: dict[str, Any], answer: dict[str, Any]) -> None:
    text = _answer_text(answer)
    inputs = _io_ports(doc, direction="input")
    clock_candidates = [p for p in inputs if p.lower() in {"clk", "clock", "pclk", "aclk"} or p.lower().endswith("clk")]
    port = _pick_named_port(text, clock_candidates or inputs)
    contract = _ensure_dict(doc, "rtl_contract")
    if port:
        contract["clock"] = port
    contract["clock_source"] = text


def _apply_rtl_reset_port(doc: dict[str, Any], answer: dict[str, Any]) -> None:
    text = _answer_text(answer)
    inputs = _io_ports(doc, direction="input")
    reset_candidates = [
        p for p in inputs
        if p.lower() in {"rst", "reset", "rst_n", "resetn", "aresetn", "presetn"} or "reset" in p.lower()
    ]
    port = _pick_named_port(text, reset_candidates or inputs)
    low = text.lower()
    active = "low" if ("active-low" in low or "active low" in low or port.lower().endswith("_n") or port.lower().endswith("n")) else "high"
    contract = _ensure_dict(doc, "rtl_contract")
    if port:
        contract["reset"] = port
    contract["reset_active"] = active
    contract["reset_source"] = text


def _apply_rtl_output_map(doc: dict[str, Any], answer: dict[str, Any]) -> None:
    qid = str(answer.get("id") or answer.get("question_id") or "")
    raw_name = qid.removeprefix("RTL_OUTPUT_MAP_")
    rule_name = re.sub(r"[^A-Za-z0-9_]+", "_", raw_name.lower()).strip("_") or "output_0"
    text = _answer_text(answer)
    outputs = _io_ports(doc, direction="output")
    port = _pick_named_port(text, outputs)
    contract = _ensure_dict(doc, "rtl_contract")
    output_map = _ensure_dict(contract, "output_map")
    if port:
        output_map[rule_name] = port
    notes = _ensure_list(contract, "output_map_sources")
    _append_unique(notes, {"rule": rule_name, "port": port, "source": text})


def _apply_rtl_input_map(doc: dict[str, Any], answer: dict[str, Any]) -> None:
    qid = str(answer.get("id") or answer.get("question_id") or "")
    raw_name = qid.removeprefix("RTL_INPUT_MAP_")
    field = re.sub(r"[^A-Za-z0-9_]+", "_", raw_name.lower()).strip("_")
    text = _answer_text(answer)
    low = text.lower()
    contract = _ensure_dict(doc, "rtl_contract")
    input_map = _ensure_dict(contract, "input_map")
    inputs = _io_ports(doc, direction="input")
    input_set = {item.lower(): item for item in inputs}
    selected = ""

    def consider_mapping(mapping: Any) -> None:
        nonlocal selected
        if selected or not isinstance(mapping, dict):
            return
        for key, value in mapping.items():
            key_norm = re.sub(r"[^A-Za-z0-9_]+", "_", str(key).lower()).strip("_")
            if key_norm != field:
                continue
            port = str(value or "").strip()
            if port.lower() in input_set:
                selected = input_set[port.lower()]
                return

    for source in (answer, _parse_structured_answer(str(answer.get("custom") or "")), _parse_structured_answer(str(answer.get("answer") or ""))):
        if isinstance(source, dict):
            consider_mapping(source.get("input_map"))
            rtl_contract = source.get("rtl_contract")
            if isinstance(rtl_contract, dict):
                consider_mapping(rtl_contract.get("input_map"))
            consider_mapping(source)

    if not selected and not any(token in low for token in ("do not bind", "not from input_map", "no input_map")):
        patterns = [
            rf"input_map\.{re.escape(field)}\s*[:=]\s*([A-Za-z_][A-Za-z0-9_]*)",
            rf"{re.escape(field)}\s*[:=]\s*([A-Za-z_][A-Za-z0-9_]*)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match and match.group(1).lower() in input_set:
                selected = input_set[match.group(1).lower()]
                break

    notes = _ensure_list(contract, "input_map_sources")
    if selected and field:
        input_map[field] = selected
        _append_unique(notes, {"field": field, "port": selected, "source": text})
    else:
        _append_unique(notes, {"field": field, "port": "", "source": text, "status": "not_applied"})


def _output_rule_rows_from_answer(answer: dict[str, Any], target_name: str) -> list[dict[str, Any]]:
    candidates: list[Any] = []
    for key in ("output_rules", "rule", "rules"):
        if key in answer:
            candidates.append(answer.get(key))
    for key in ("custom", "answer"):
        parsed = _parse_structured_answer(str(answer.get(key) or ""))
        if parsed is not None:
            candidates.append(parsed)

    rows: list[dict[str, Any]] = []

    def collect(candidate: Any) -> None:
        if isinstance(candidate, dict):
            if isinstance(candidate.get("output_rules"), list):
                rows.extend(item for item in candidate["output_rules"] if isinstance(item, dict))
            elif isinstance(candidate.get("output_rules"), dict):
                for name, value in candidate["output_rules"].items():
                    item = dict(value) if isinstance(value, dict) else {"expr": value}
                    item.setdefault("name", name)
                    rows.append(item)
            elif any(key in candidate for key in ("name", "port", "expr", "expression", "value")):
                rows.append(candidate)
            else:
                for value in candidate.values():
                    if isinstance(value, (dict, list)):
                        collect(value)
        elif isinstance(candidate, list):
            rows.extend(item for item in candidate if isinstance(item, dict))

    for candidate in candidates:
        collect(candidate)

    text = _answer_text(answer)
    if not rows:
        expr_match = re.search(r"\bexpr(?:ession)?\s*[:=]\s*([^,\n;]+)", text, re.IGNORECASE)
        if expr_match:
            row: dict[str, Any] = {"name": target_name, "expr": expr_match.group(1).strip()}
            width_match = re.search(r"\bwidth\s*[:=]\s*(\d+)", text, re.IGNORECASE)
            port_match = re.search(r"\bport\s*[:=]\s*([A-Za-z_][A-Za-z0-9_]*)", text, re.IGNORECASE)
            txn_match = re.search(r"\b(FM_[A-Za-z0-9_]+)\b", text)
            if width_match:
                row["width"] = int(width_match.group(1))
            if port_match:
                row["port"] = port_match.group(1)
            if txn_match:
                row["transaction"] = txn_match.group(1)
            rows.append(row)
    return rows


def _apply_rtl_expr_rule(doc: dict[str, Any], answer: dict[str, Any]) -> None:
    qid = str(answer.get("id") or answer.get("question_id") or "")
    raw_name = qid.removeprefix("RTL_EXPR_")
    target_name = re.sub(r"[^A-Za-z0-9_]+", "_", raw_name.lower()).strip("_")
    rows = _output_rule_rows_from_answer(answer, target_name)
    fm = _ensure_dict(doc, "function_model")
    txns = _ensure_list(fm, "transactions")
    applied: list[dict[str, Any]] = []

    for row in rows:
        name = re.sub(r"[^A-Za-z0-9_]+", "_", str(row.get("name") or row.get("port") or target_name).lower()).strip("_")
        if target_name and name not in {target_name, ""}:
            continue
        expr = str(row.get("expr") or row.get("expression") or row.get("value") or "").strip()
        if not expr:
            continue
        txn_filter = str(row.get("transaction") or row.get("txn") or "").strip().upper()
        port = str(row.get("port") or target_name).strip()
        width = row.get("width", 1)
        matched = False
        for txn in txns:
            if not isinstance(txn, dict):
                continue
            txn_id = str(txn.get("id") or "").strip().upper()
            if txn_filter and txn_id != txn_filter:
                continue
            output_rules = _ensure_list(txn, "output_rules")
            for rule in output_rules:
                if not isinstance(rule, dict):
                    continue
                rule_name = re.sub(
                    r"[^A-Za-z0-9_]+",
                    "_",
                    str(rule.get("name") or rule.get("port") or "").lower(),
                ).strip("_")
                if rule_name != target_name:
                    continue
                rule["expr"] = expr
                rule.setdefault("width", width)
                if port:
                    rule.setdefault("port", port)
                matched = True
                applied.append({"transaction": txn_id, "name": rule_name, "expr": expr})
        if not matched and txn_filter:
            txn = _find_txn(doc, txn_filter)
            item = {"name": target_name, "expr": expr, "width": width}
            if port:
                item["port"] = port
            _ensure_list(txn, "output_rules").append(item)
            applied.append({"transaction": txn_filter, "name": target_name, "expr": expr})

    custom = _ensure_dict(doc, "custom")
    history = _ensure_list(custom, "rtl_expr_resolution_history")
    history.append({
        "blocker_id": qid,
        "applied": applied,
        "source": _answer_text(answer),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    })


def _apply_valid_ready_sample_condition(doc: dict[str, Any], blocker: dict[str, Any], answer: dict[str, Any]) -> None:
    qid = str(answer.get("id") or answer.get("question_id") or "RTL_VALID_READY_SAMPLE_CONDITION")
    qdoc = _question_doc(blocker, qid)
    text = _answer_text(answer)
    parsed = _parse_structured_answer(text)
    sample = ""
    if isinstance(parsed, dict):
        sample = str(parsed.get("sample_condition") or parsed.get("rtl_contract", {}).get("sample_condition") or "").strip()
    if not sample:
        match = re.search(r"sample_condition\s*[:=]\s*([^\n;]+)", text, re.IGNORECASE)
        if match:
            sample = match.group(1).strip()
    if not sample:
        current = str(qdoc.get("current_sample_condition") or "valid").strip() or "valid"
        ready = str(qdoc.get("ready_port") or "ready").strip() or "ready"
        sample = f"({current}) and {ready}"
    contract = _ensure_dict(doc, "rtl_contract")
    contract["sample_condition"] = sample
    contract["sample_condition_source"] = text
    if qid == "RTL_VALID_READY_SAMPLE_CONDITION":
        txn = _find_txn(doc, "FM_PRIMARY")
        txn["sample_condition"] = sample
    else:
        fm = _ensure_dict(doc, "function_model")
        txns = _ensure_list(fm, "transactions")
        fm["transactions"] = [
            txn for txn in txns
            if not (
                isinstance(txn, dict)
                and str(txn.get("id") or "").upper() == "FM_PRIMARY"
                and not any(txn.get(key) for key in ("output_rules", "state_updates", "counter_rules", "event_rules"))
                and not any(txn.get(key) for key in ("inputs", "outputs", "preconditions", "side_effects", "error_cases"))
            )
        ]
    cm = _ensure_dict(doc, "cycle_model")
    rules = _ensure_list(cm, "handshake_rules")
    _append_unique(rules, {
        "signal": "valid_ready",
        "rule": f"Transfer acceptance and state updates use sample_condition={sample}.",
    })


def _observable_rule_rows(answer: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[Any] = []
    for key in ("observable_state_rules", "output_rules", "state_updates", "rules"):
        if key in answer:
            candidates.append(answer.get(key))
    for key in ("custom", "answer"):
        parsed = _parse_structured_answer(str(answer.get(key) or ""))
        if parsed is not None:
            candidates.append(parsed)

    rows: list[dict[str, Any]] = []

    def collect(candidate: Any) -> None:
        if isinstance(candidate, dict):
            if isinstance(candidate.get("observable_state_rules"), list):
                rows.extend(item for item in candidate["observable_state_rules"] if isinstance(item, dict))
            elif isinstance(candidate.get("observable_state_rules"), dict):
                for name, value in candidate["observable_state_rules"].items():
                    if isinstance(value, dict):
                        item = dict(value)
                        item.setdefault("name", name)
                        rows.append(item)
                    else:
                        rows.append({"name": name, "expr": value})
            elif isinstance(candidate.get("output_rules"), list):
                rows.extend({**item, "rule_type": "output_rule"} for item in candidate["output_rules"] if isinstance(item, dict))
            elif isinstance(candidate.get("state_updates"), list):
                rows.extend({**item, "rule_type": "state_update"} for item in candidate["state_updates"] if isinstance(item, dict))
            elif any(key in candidate for key in ("name", "port", "expr", "expression", "value")):
                rows.append(candidate)
            else:
                for value in candidate.values():
                    if isinstance(value, (dict, list)):
                        collect(value)
        elif isinstance(candidate, list):
            rows.extend(item for item in candidate if isinstance(item, dict))

    for candidate in candidates:
        collect(candidate)
    return rows


def _apply_observable_state_rules(doc: dict[str, Any], blocker: dict[str, Any], answer: dict[str, Any]) -> None:
    qid = str(answer.get("id") or answer.get("question_id") or "RTL_OBSERVABLE_STATE_RULES")
    qdoc = _question_doc(blocker, qid)
    rows = _observable_rule_rows(answer)
    missing = {
        str(item)
        for item in qdoc.get("missing_observable_state") or []
        if str(item).strip()
    }
    txn = _find_txn(doc, "FM_PRIMARY")
    output_rules = _ensure_list(txn, "output_rules")
    state_updates = _ensure_list(txn, "state_updates")
    contract = _ensure_dict(doc, "rtl_contract")
    output_map = _ensure_dict(contract, "output_map")
    applied: list[str] = []
    for row in rows:
        name = str(row.get("name") or row.get("state") or row.get("port") or "").strip()
        expr = str(row.get("expr") or row.get("expression") or row.get("value") or "").strip()
        if not name or not expr:
            continue
        if missing and name not in missing:
            continue
        port = str(row.get("port") or name).strip()
        width = row.get("width", 1)
        rule_type = str(row.get("rule_type") or row.get("kind") or "output_rule").lower()
        item = {
            "name": name,
            "expr": expr,
            "width": width,
            "description": f"Resolved RTL observable-state rule from blocker answer {qid}: {name}={expr}",
        }
        if rule_type in {"state_update", "state", "update"}:
            _append_unique(state_updates, item)
        else:
            item["port"] = port
            _append_unique(output_rules, item)
            output_map[name] = port
        applied.append(name)
    custom = _ensure_dict(doc, "custom")
    history = _ensure_list(custom, "rtl_observable_state_resolution_history")
    history.append({
        "blocker_id": qid,
        "applied": applied,
        "unresolved": sorted(missing - set(applied)) if missing else [],
        "source": _answer_text(answer),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    })


def _question_doc(blocker: dict[str, Any], qid: str) -> dict[str, Any]:
    questions = blocker.get("questions") if isinstance(blocker.get("questions"), list) else []
    for qdoc in questions:
        if isinstance(qdoc, dict) and str(qdoc.get("id") or "") == qid:
            return qdoc
    return {}


def _strip_fence(text: str) -> str:
    text = text.strip()
    if not text.startswith("```"):
        return text
    text = re.sub(r"^```(?:json|yaml|yml)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _parse_structured_answer(text: str) -> Any:
    text = _strip_fence(text)
    if not text:
        return None
    try:
        return json.loads(text)
    except Exception:
        pass
    try:
        return yaml.safe_load(text)
    except Exception:
        return None


def _contract_rows_from_answer(answer: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[Any] = []
    for key in ("module_contracts", "contracts", "modules"):
        if key in answer:
            candidates.append(answer.get(key))
    for key in ("custom", "answer"):
        parsed = _parse_structured_answer(str(answer.get(key) or ""))
        if parsed is not None:
            candidates.append(parsed)

    rows: list[dict[str, Any]] = []

    def collect(candidate: Any) -> None:
        if isinstance(candidate, dict):
            if isinstance(candidate.get("module_contracts"), list):
                rows.extend(item for item in candidate["module_contracts"] if isinstance(item, dict))
            elif isinstance(candidate.get("module_contracts"), dict):
                for name, value in candidate["module_contracts"].items():
                    if isinstance(value, dict):
                        item = dict(value)
                        item.setdefault("name", name)
                        rows.append(item)
            elif isinstance(candidate.get("contracts"), list):
                rows.extend(item for item in candidate["contracts"] if isinstance(item, dict))
            elif isinstance(candidate.get("contracts"), dict):
                for name, value in candidate["contracts"].items():
                    if isinstance(value, dict):
                        item = dict(value)
                        item.setdefault("name", name)
                        rows.append(item)
            elif isinstance(candidate.get("modules"), list):
                rows.extend(item for item in candidate["modules"] if isinstance(item, dict))
            elif isinstance(candidate.get("modules"), dict):
                for name, value in candidate["modules"].items():
                    if isinstance(value, dict):
                        item = dict(value)
                        item.setdefault("name", name)
                        rows.append(item)
            elif any(key in candidate for key in ("name", "module", "file")):
                rows.append(candidate)
            else:
                for value in candidate.values():
                    if isinstance(value, (dict, list)):
                        collect(value)
        elif isinstance(candidate, list):
            rows.extend(item for item in candidate if isinstance(item, dict))

    for candidate in candidates:
        collect(candidate)
    return rows


def _first_nonempty(row: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = str(row.get(key) or "").strip()
        if value:
            return value
    return ""


def _normalize_connection_row(row: dict[str, Any], *, module_hint: str = "") -> tuple[dict[str, Any] | None, str]:
    module = _first_nonempty(
        row,
        ("module", "module_name", "child_module", "child", "name", "file"),
    ) or module_hint
    port = _first_nonempty(row, ("port", "child_port", "pin", "endpoint"))
    signal = _first_nonempty(row, ("signal", "net", "wire", "expr", "expression", "source_signal"))
    missing = [name for name, value in (("module", module), ("port", port), ("signal", signal)) if not value]
    if missing:
        label = _first_nonempty(row, ("module", "name", "instance", "port")) or "<unnamed>"
        return None, f"{label}: missing {', '.join(missing)}"
    normalized: dict[str, Any] = {
        "module": module,
        "port": port,
        "signal": signal,
        "machine_readable": True,
    }
    for key in _CONNECTION_OPTIONAL_STRING_KEYS:
        value = str(row.get(key) or "").strip()
        if value:
            normalized[key] = value
    for key in _CONNECTION_OPTIONAL_BOOL_KEYS:
        if key in row:
            normalized[key] = _as_bool(row.get(key))
    return normalized, ""


def _connection_rows_from_answer(answer: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    """Extract explicit module/port/signal connection rows from an answer.

    This is intentionally generic and conservative: rows are applied only when
    they carry machine-readable module, port, and signal fields. Free-form text
    is retained in the resolution log but never converted into wiring.
    """

    candidates: list[Any] = []
    for key in _CONNECTION_CONTAINER_KEYS:
        if key in answer:
            candidates.append({key: answer.get(key)})
    for key in ("custom", "answer"):
        parsed = _parse_structured_answer(str(answer.get(key) or ""))
        if parsed is not None:
            candidates.append(parsed)

    rows: list[dict[str, Any]] = []
    rejected: list[str] = []

    def append_row(row: dict[str, Any], *, module_hint: str = "") -> None:
        normalized, reason = _normalize_connection_row(row, module_hint=module_hint)
        if normalized is None:
            rejected.append(reason)
        else:
            rows.append(normalized)

    def append_port_map(value: Any, *, module_hint: str) -> None:
        if isinstance(value, dict):
            for port, signal in value.items():
                if isinstance(signal, dict):
                    nested = dict(signal)
                    nested.setdefault("module", module_hint)
                    nested.setdefault("port", str(port))
                    append_row(nested)
                else:
                    append_row({"module": module_hint, "port": str(port), "signal": signal})
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    append_row(item, module_hint=module_hint)

    def collect(candidate: Any, *, module_hint: str = "") -> None:
        if isinstance(candidate, list):
            for item in candidate:
                collect(item, module_hint=module_hint)
            return
        if not isinstance(candidate, dict):
            return

        if any(key in candidate for key in ("port", "signal", "net", "wire", "expr", "expression")):
            append_row(candidate, module_hint=module_hint)

        row_module = _first_nonempty(
            candidate,
            ("module", "module_name", "child_module", "child", "name", "file"),
        ) or module_hint
        if isinstance(candidate.get("connections"), dict) and row_module:
            append_port_map(candidate["connections"], module_hint=row_module)
        elif isinstance(candidate.get("connections"), list):
            collect(candidate["connections"], module_hint=row_module)

        for key in _CONNECTION_CONTAINER_KEYS:
            if key == "connections":
                continue
            if key not in candidate:
                continue
            value = candidate.get(key)
            if isinstance(value, list):
                collect(value, module_hint=module_hint)
            elif isinstance(value, dict):
                if any(field in value for field in ("port", "signal", "net", "wire", "expr", "expression")):
                    append_row(value, module_hint=module_hint)
                else:
                    for name, nested in value.items():
                        hint = str(name or "").strip() or module_hint
                        if isinstance(nested, dict):
                            if any(field in nested for field in ("port", "signal", "net", "wire", "expr", "expression")):
                                row = dict(nested)
                                row.setdefault("module", hint)
                                append_row(row)
                            else:
                                append_port_map(nested, module_hint=hint)
                        elif isinstance(nested, list):
                            collect(nested, module_hint=hint)

    for candidate in candidates:
        collect(candidate)

    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for row in rows:
        key = (
            str(row.get("module") or ""),
            str(row.get("instance") or ""),
            str(row.get("port") or ""),
            str(row.get("signal") or ""),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped, rejected


def _as_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        return [item.strip() for item in re.split(r"[,;\n]+", text) if item.strip()]
    if value is None:
        return []
    return [str(value).strip()]


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def _target_scale_payloads_from_answer(blocker: dict[str, Any], answer: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    candidates: list[Any] = []
    for key in ("target_scale", "scale_targets", "implementation_scale"):
        if isinstance(answer.get(key), dict):
            candidates.append({"target_scale": answer[key]})
    for key in ("target_scale_waiver", "scale_waiver", "implementation_scale_waiver"):
        if isinstance(answer.get(key), dict):
            candidates.append({"target_scale_waiver": answer[key]})
    for key in ("custom", "answer"):
        parsed = _parse_structured_answer(str(answer.get(key) or ""))
        if parsed is not None:
            candidates.append(parsed)

    scale: dict[str, Any] = {}
    waiver: dict[str, Any] = {}

    def collect(candidate: Any) -> None:
        nonlocal scale, waiver
        if not isinstance(candidate, dict):
            return
        for key in ("target_scale", "scale_targets", "implementation_scale"):
            if isinstance(candidate.get(key), dict):
                scale.update(candidate[key])
        for key in ("target_scale_waiver", "scale_waiver", "implementation_scale_waiver"):
            if isinstance(candidate.get(key), dict):
                waiver.update(candidate[key])
        if any(str(key).endswith("_min") or str(key).startswith("min_") for key in candidate):
            scale.update(candidate)
        if {"approved", "reason"} & set(candidate):
            waiver.update(candidate)

    for candidate in candidates:
        collect(candidate)

    text = _answer_text(answer).lower()
    if not scale and not waiver and any(token in text for token in ("recommended", "suggested", "candidate", "use reference")):
        qdoc = _question_doc(blocker, str(answer.get("id") or answer.get("question_id") or ""))
        suggested = qdoc.get("suggested_ssot_target_scale") if isinstance(qdoc.get("suggested_ssot_target_scale"), dict) else {}
        if suggested:
            scale.update(suggested)

    return scale, waiver


def _apply_target_scale_policy(doc: dict[str, Any], blocker: dict[str, Any], answer: dict[str, Any]) -> None:
    scale, waiver = _target_scale_payloads_from_answer(blocker, answer)
    qg = _ensure_dict(doc, "quality_gates")
    rtl_gen = _ensure_dict(qg, "rtl_gen")

    def positive_int(value: Any) -> int | None:
        if isinstance(value, bool):
            return None
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return None
        return parsed if parsed > 0 else None

    clean_scale: dict[str, Any] = {}
    for key, value in scale.items():
        if key in {"basis", "source", "reference_profile", "policy"} and str(value).strip():
            clean_scale[key] = str(value).strip()
            continue
        parsed = positive_int(value)
        if parsed is not None:
            clean_scale[str(key)] = parsed
    if clean_scale and any(str(key).endswith("_min") or str(key).startswith("min_") for key in clean_scale):
        clean_scale.setdefault("basis", "human-approved RTL target scale from RTL blocker resolution")
        rtl_gen["target_scale"] = clean_scale
        rtl_gen.pop("target_scale_waiver", None)
    elif waiver:
        reason = str(waiver.get("reason") or waiver.get("rationale") or _answer_text(answer)).strip()
        rtl_gen["target_scale_waiver"] = {
            "approved": bool(waiver.get("approved", True)),
            "reason": reason,
            "owner": str(waiver.get("owner") or waiver.get("approver") or "human-review").strip(),
        }


def _submodule_index(doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for sm in doc.get("sub_modules") or []:
        if not isinstance(sm, dict):
            continue
        for key in (sm.get("name"), sm.get("module"), sm.get("file")):
            text = str(key or "").strip()
            if text:
                index[text] = sm
                index[Path(text).stem] = sm
    return index


def _merge_module_contract(sm: dict[str, Any], row: dict[str, Any], *, source: str) -> list[str]:
    changed: list[str] = []
    for key in _MODULE_CONTRACT_KEYS:
        if key not in row:
            continue
        value = row.get(key)
        if key == "wiring_only":
            normalized: Any = _as_bool(value)
        elif key in {"connections"}:
            normalized = value if isinstance(value, dict) else _parse_structured_answer(str(value or "")) or value
        elif key in {"ports", "internal_interfaces"} and isinstance(value, dict):
            normalized = value
        else:
            normalized = _as_string_list(value)
        if normalized in ({}, [], "", None):
            continue
        if sm.get(key) != normalized:
            sm[key] = normalized
            changed.append(key)
    if changed:
        sm["contract_status"] = "approved_by_rtl_blocker_answer"
        sm["contract_source"] = source
        sm["contract_updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return changed


def _apply_rtl_module_contracts(doc: dict[str, Any], blocker: dict[str, Any], answer: dict[str, Any]) -> None:
    """Project structured module-contract answers into sub_modules[].

    This intentionally does not invent contracts from module names. The RTL
    gate asks for implementation ownership; the resolver only applies a
    machine-readable answer from ATLAS/ssot-gen/human review.
    """

    rows = _contract_rows_from_answer(answer)
    qid = str(answer.get("id") or answer.get("question_id") or "RTL_MODULE_CONTRACTS").strip()
    qdoc = _question_doc(blocker, qid) or _question_doc(blocker, "RTL_MODULE_CONTRACTS")
    missing = qdoc.get("missing_modules") if isinstance(qdoc.get("missing_modules"), list) else []
    if not missing and isinstance(qdoc.get("unmatched_modules"), list):
        missing = qdoc.get("unmatched_modules") or []
    expected: list[tuple[str, set[str]]] = []
    for item in missing:
        if not isinstance(item, dict):
            continue
        display = str(item.get("name") or item.get("file") or "").strip()
        keys: set[str] = set()
        for key in (item.get("name"), item.get("file"), Path(str(item.get("file") or "")).stem):
            text = str(key or "").strip()
            if text:
                keys.add(text)
        if keys:
            expected.append((display or sorted(keys)[0], keys))
    index = _submodule_index(doc)
    applied: list[dict[str, Any]] = []
    unresolved: list[dict[str, str]] = []
    source = _answer_text(answer)

    for row in rows:
        key = str(row.get("name") or row.get("module") or row.get("file") or "").strip()
        sm = index.get(key) or index.get(Path(key).stem)
        if sm is None:
            unresolved.append({"name": key or "<missing name>", "reason": "no matching sub_modules[] row"})
            continue
        changed = _merge_module_contract(sm, row, source=source)
        if changed:
            applied.append({
                "name": str(sm.get("name") or key),
                "file": str(sm.get("file") or ""),
                "fields": changed,
            })

    answered: set[str] = set()
    for row in rows:
        for key in (row.get("name"), row.get("module"), row.get("file"), Path(str(row.get("file") or "")).stem):
            text = str(key or "").strip()
            if text:
                answered.add(text)
    missing_displays: set[str] = set()
    for display, keys in expected:
        if not keys.intersection(answered):
            missing_displays.add(display)
    for display in sorted(missing_displays):
        unresolved.append({"name": display, "reason": "no structured contract answer"})

    custom = _ensure_dict(doc, "custom")
    history = _ensure_list(custom, "rtl_module_contract_resolution_history")
    history.append({
        "source": "rtl_blocked.json -> ATLAS ask_user",
        "blocker_id": qid or "RTL_MODULE_CONTRACTS",
        "applied": applied,
        "unresolved": unresolved,
        "required_fields": qdoc.get("required_fields") or list(_MODULE_CONTRACT_KEYS),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    })


def _connection_identity(row: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(row.get("module") or ""),
        str(row.get("instance") or ""),
        str(row.get("port") or ""),
        str(row.get("signal") or ""),
    )


def _apply_rtl_connection_contracts(doc: dict[str, Any], blocker: dict[str, Any], answer: dict[str, Any]) -> None:
    """Project approved connection-contract answers into integration metadata.

    The resolver records only explicit module/port/signal rows. It may mirror
    those rows into matching sub_modules[].connections, but it never derives or
    guesses missing wiring from RTL names.
    """

    rows, rejected = _connection_rows_from_answer(answer)
    qid = str(answer.get("id") or answer.get("question_id") or "RTL_RESOLVE_CONNECTION_CONTRACTS").strip()
    qdoc = _question_doc(blocker, qid)
    integration = _ensure_dict(doc, "integration")
    connections = _ensure_list(integration, "connections")
    existing = {
        _connection_identity(item)
        for item in connections
        if isinstance(item, dict)
    }
    applied: list[dict[str, Any]] = []
    for row in rows:
        identity = _connection_identity(row)
        if identity not in existing:
            connections.append(row)
            existing.add(identity)
        applied.append({
            "module": row["module"],
            "port": row["port"],
            "signal": row["signal"],
        })

    submodule_updates: list[dict[str, str]] = []
    unmatched_modules: list[str] = []
    index = _submodule_index(doc)
    for row in rows:
        module = str(row.get("module") or "")
        sm = index.get(module) or index.get(Path(module).stem)
        if sm is None:
            unmatched_modules.append(module)
            continue
        sm_connections = sm.get("connections")
        if not isinstance(sm_connections, dict):
            sm_connections = {}
            sm["connections"] = sm_connections
        port = str(row["port"])
        signal = str(row["signal"])
        if sm_connections.get(port) != signal:
            sm_connections[port] = signal
        sm["connection_contract_status"] = "approved_by_rtl_blocker_answer"
        sm["connection_contract_source"] = _answer_text(answer)
        sm["connection_contract_updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        submodule_updates.append({"module": module, "port": port, "signal": signal})

    if rows:
        integration["connection_contract_status"] = "approved_by_rtl_blocker_answer"
        integration["connection_contract_source"] = _answer_text(answer)
        integration["connection_contract_updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    unresolved: list[dict[str, str]] = [{"name": item, "reason": "invalid or incomplete connection row"} for item in rejected]
    unresolved.extend(
        {"name": module, "reason": "no matching sub_modules[] row; kept in integration.connections"}
        for module in sorted(set(unmatched_modules))
    )
    custom = _ensure_dict(doc, "custom")
    history = _ensure_list(custom, "rtl_connection_contract_resolution_history")
    history.append({
        "source": "rtl_blocked.json -> ATLAS ask_user",
        "blocker_id": qid or "RTL_RESOLVE_CONNECTION_CONTRACTS",
        "applied": applied,
        "submodule_updates": submodule_updates,
        "unresolved": unresolved,
        "required_fields": qdoc.get("required_fields") or ["module", "port", "signal"],
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    })


def _record_resolution(doc: dict[str, Any], blocker: dict[str, Any], answer: dict[str, Any]) -> None:
    custom = _ensure_dict(doc, "custom")
    rows = _ensure_list(custom, "rtl_blocker_resolutions")
    qid = str(answer.get("id") or answer.get("question_id") or "")
    questions = blocker.get("questions") if isinstance(blocker.get("questions"), list) else []
    qdoc = next((q for q in questions if isinstance(q, dict) and q.get("id") == qid), {})
    rows.append({
        "id": qid,
        "decision_needed": qdoc.get("decision_needed") or answer.get("decision_needed") or "",
        "answer": _answer_text(answer),
        "evidence": qdoc.get("evidence") or "",
        "source": "rtl_blocked.json -> ATLAS ask_user",
        "resolved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    })
    trace = _ensure_dict(doc, "traceability")
    links = _ensure_list(trace, "rtl_blocker_to_ssot")
    links.append({
        "blocker_id": qid,
        "answer": _answer_text(answer),
        "ssot_fields": [
            "custom.rtl_blocker_resolutions",
            "function_model",
            "cycle_model",
            "registers",
            "error_handling",
            "test_requirements",
            "sub_modules",
            "integration.connections",
            "quality_gates",
        ],
    })


def apply_answers(doc: dict[str, Any], blocker: dict[str, Any], answers: list[dict[str, Any]]) -> dict[str, Any]:
    handlers = {
        "FM_PRIMARY_STRUCTURED_RULES": _apply_primary_rules,
        "CRC_STREAM_POLICY": _apply_crc_policy,
        "AXIS_TKEEP_POLICY": _apply_axis_tkeep_policy,
        "APB_ILLEGAL_ACCESS_POLICY": _apply_apb_policy,
        "OPTIONAL_BEHAVIOR_POLICY": _apply_optional_policy,
        "RTL_CLOCK_PORT": _apply_rtl_clock_port,
        "RTL_RESET_PORT": _apply_rtl_reset_port,
    }
    for answer in answers:
        qid = str(answer.get("id") or answer.get("question_id") or "").strip()
        if not qid:
            continue
        _record_resolution(doc, blocker, answer)
        if qid == "RTL_VALID_READY_SAMPLE_CONDITION":
            _apply_valid_ready_sample_condition(doc, blocker, answer)
            continue
        if qid == "RTL_SAMPLE_CONDITION":
            _apply_valid_ready_sample_condition(doc, blocker, answer)
            continue
        if qid == "RTL_OBSERVABLE_STATE_RULES":
            _apply_observable_state_rules(doc, blocker, answer)
            continue
        if qid.startswith("RTL_INPUT_MAP_"):
            _apply_rtl_input_map(doc, answer)
            continue
        if qid.startswith("RTL_EXPR_"):
            _apply_rtl_expr_rule(doc, answer)
            continue
        if qid in {
            "RTL_DYNAMIC_TODO_OWNERSHIP",
            "RTL_MODULE_CONTRACTS",
            "RTL_MODULE_BEHAVIOR_MATCH",
            "SSOT_BEHAVIOR_OWNERSHIP",
        }:
            _apply_rtl_module_contracts(doc, blocker, answer)
            continue
        if qid in _CONNECTION_CONTRACT_QIDS:
            _apply_rtl_connection_contracts(doc, blocker, answer)
            continue
        if qid == "RTL_TARGET_SCALE_POLICY":
            _apply_target_scale_policy(doc, blocker, answer)
            continue
        handler = handlers.get(qid)
        if handler:
            handler(doc, answer)
        elif qid.startswith("RTL_OUTPUT_MAP_"):
            _apply_rtl_output_map(doc, answer)
    flow = _ensure_dict(doc, "generation_flow")
    handoffs = _ensure_list(flow, "blocker_resolution_history")
    handoffs.append({
        "source": "rtl-gen",
        "artifact": "rtl/rtl_blocked.json",
        "answers": [str(a.get("id") or "") for a in answers],
        "next": "rerun fl-model-gen/fcov and rtl-gen preflight before RTL implementation",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    })
    return doc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("ip")
    ap.add_argument("--root", default=".")
    ap.add_argument("--answers-json", default="")
    ap.add_argument(
        "--use-suggested-target-scale",
        action="store_true",
        help="Explicitly lock the RTL_TARGET_SCALE_POLICY suggested_ssot_target_scale into SSOT target_scale.",
    )
    ap.add_argument(
        "--use-recommended-defaults",
        action="store_true",
        help="Apply machine-readable recommended defaults from rtl_blocked.json for module-contract/ownership blockers.",
    )
    ns = ap.parse_args()
    root = Path(ns.root).resolve()
    ip_dir = root / ns.ip
    ssot_path = ip_dir / "yaml" / f"{ns.ip}.ssot.yaml"
    blocker_path = ip_dir / "rtl" / "rtl_blocked.json"
    if not ssot_path.is_file():
        raise SystemExit(f"[resolve_rtl_blockers] missing SSOT: {ssot_path}")
    if not blocker_path.is_file():
        raise SystemExit(f"[resolve_rtl_blockers] missing blocker: {blocker_path}")
    doc = yaml.safe_load(ssot_path.read_text(encoding="utf-8")) or {}
    if not isinstance(doc, dict):
        raise SystemExit("[resolve_rtl_blockers] SSOT top-level must be mapping")
    blocker = _load_json(blocker_path)
    answers_path = Path(ns.answers_json).resolve() if ns.answers_json else None
    answers = _load_answers(root, ns.ip, answers_path)
    if ns.use_suggested_target_scale:
        answers.append(_suggested_target_scale_answer(blocker))
    if ns.use_recommended_defaults:
        answers.extend(_recommended_default_answers(blocker))
    if not answers:
        raise SystemExit("[resolve_rtl_blockers] no rtl_blocker_answers found")
    doc = apply_answers(doc, blocker, answers)
    ssot_path.write_text(yaml.safe_dump(doc, sort_keys=False, width=120), encoding="utf-8")
    resolved_path = ip_dir / "rtl" / "rtl_blocked_resolved.json"
    resolved_path.write_text(json.dumps({
        "schema_version": 1,
        "type": "rtl_blocker_resolution",
        "status": "applied_to_ssot",
        "answers": answers,
        "ssot": str(ssot_path.relative_to(root)),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }, indent=2) + "\n", encoding="utf-8")
    print(f"[resolve_rtl_blockers] applied {len(answers)} answer(s) to {ssot_path.relative_to(root)}")
    print(f"[resolve_rtl_blockers] wrote {resolved_path.relative_to(root)}")
    print("next: validate SSOT, regenerate FL model/coverage, rerun rtl-gen preflight")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
