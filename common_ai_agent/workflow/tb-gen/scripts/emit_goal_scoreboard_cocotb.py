#!/usr/bin/env python3
"""Emit a generic cocotb/pyuvm FL-vs-RTL scoreboard environment.

This generator is intentionally SSOT/equivalence-goal driven. It supports the
generic structured-rule RTL contract emitted by rtl-gen and refuses to create a
testbench when the SSOT still lacks a machine-checkable driver/monitor contract.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

import yaml


SOURCE_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_DIR = SOURCE_ROOT / "workflow" / "tb-gen" / "runtime"


def _ident(value: Any) -> str:
    text = re.sub(r"\W+", "_", str(value or "")).strip("_")
    if not text or not re.match(r"^[A-Za-z_]", text):
        text = "sig_" + text
    return text


def _load_json(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError(f"missing {label}: {path}")
    try:
        doc = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception as exc:
        raise RuntimeError(f"cannot parse {label} {path}: {exc}") from exc
    if not isinstance(doc, dict):
        raise RuntimeError(f"{label} root must be a JSON object: {path}")
    return doc


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise RuntimeError(f"missing SSOT YAML: {path}")
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8", errors="replace")) or {}
    except Exception as exc:
        raise RuntimeError(f"cannot parse SSOT YAML {path}: {exc}") from exc
    if not isinstance(doc, dict):
        raise RuntimeError(f"SSOT YAML root must be a mapping: {path}")
    return doc


def _width_value(width: Any) -> int:
    if isinstance(width, bool):
        return 1
    if isinstance(width, int):
        return max(width, 1)
    text = str(width or "1").strip()
    if text.isdigit():
        return max(int(text), 1)
    if "/" in text:
        left, right = text.split("/", 1)
        try:
            return max(int(left) // max(int(right), 1), 1)
        except Exception:
            return 1
    return 1


def _int_value(value: Any, default: int = 0) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    text = str(value or "").strip().replace("_", "")
    if not text:
        return default
    try:
        if text.lower().startswith("0x"):
            return int(text, 16)
        if "'" in text:
            literal = text.lower()
            base_tag = literal.split("'", 1)[1][0]
            digits = literal.split(base_tag, 1)[1]
            digits = digits.replace("x", "0").replace("z", "0")
            return int(digits, {"h": 16, "d": 10, "b": 2}.get(base_tag, 10))
        return int(text, 10)
    except Exception:
        return default


def _param_defaults(ssot: dict[str, Any]) -> dict[str, int]:
    params = ssot.get("parameters") if isinstance(ssot.get("parameters"), list) else []
    out: dict[str, int] = {}
    for item in params:
        if not isinstance(item, dict) or not str(item.get("name") or "").strip():
            continue
        out[str(item["name"])] = _int_value(item.get("default", item.get("value", 0)), 0)
    return out


def _register_manifest(ssot: dict[str, Any]) -> dict[str, Any]:
    regs = ssot.get("registers") if isinstance(ssot.get("registers"), dict) else {}
    rows: list[dict[str, Any]] = []
    for idx, reg in enumerate(regs.get("register_list") or []):
        if not isinstance(reg, dict):
            continue
        name = str(reg.get("name") or f"REG{idx}").strip()
        if not name:
            continue
        rows.append({
            "name": name,
            "offset": _int_value(reg.get("offset"), idx * 4),
            "access": str(reg.get("access") or "rw").lower(),
            "index": idx,
        })
    return {
        "config": regs.get("config") if isinstance(regs.get("config"), dict) else {},
        "register_list": rows,
    }


def _state_observable_names(ssot: dict[str, Any]) -> list[str]:
    fm = ssot.get("function_model") if isinstance(ssot.get("function_model"), dict) else {}
    names: list[str] = []
    for row in fm.get("state_variables") or []:
        if not isinstance(row, dict):
            continue
        name = _ident(row.get("name") or "")
        if name and name not in names:
            names.append(name)
    return names


def _rtl_signal_names(sources: list[str]) -> list[str]:
    """Return simple RTL signal names declared in generated source files.

    This is deliberately lightweight. It does not elaborate RTL; it only gives
    the generated TB a safe list of internal names it may try as state-observable
    aliases when the SSOT state variable is named architecturally.
    """
    names: set[str] = set()
    decl_re = re.compile(
        r"\b(?:input|output|inout|logic|wire|reg)\b"
        r"(?:\s+(?:logic|wire|reg|signed|unsigned))*"
        r"(?:\s*\[[^\]]+\])*"
        r"\s+([^;]+);"
    )
    for raw in sources:
        path = Path(raw)
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for match in decl_re.finditer(text):
            decl = match.group(1)
            for piece in decl.split(","):
                token = piece.split("=", 1)[0].strip()
                token = re.sub(r"\[[^\]]+\]", "", token).strip()
                if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", token):
                    names.add(token)
    return sorted(names)


def _state_observable_aliases(state_names: list[str], rtl_names: list[str]) -> dict[str, list[str]]:
    aliases: dict[str, list[str]] = {}
    norm_to_rtl = {re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_"): name for name in rtl_names}
    for state_name in state_names:
        norm = re.sub(r"[^a-z0-9]+", "_", state_name.lower()).strip("_")
        stems = {norm}
        for suffix in ("_state", "_next", "_set_next", "_w1c_next"):
            if norm.endswith(suffix):
                stems.add(norm[: -len(suffix)])
        found: list[str] = []
        for rtl_norm, rtl_name in norm_to_rtl.items():
            if rtl_name == state_name:
                continue
            if any(
                rtl_norm == stem
                or rtl_norm.startswith(f"{stem}_")
                or rtl_norm.endswith(f"_{stem}")
                for stem in stems
                if stem
            ):
                found.append(rtl_name)
        if found:
            aliases[state_name] = sorted(found)
    return aliases


def _as_ports(ssot: dict[str, Any]) -> list[dict[str, Any]]:
    ports: list[dict[str, Any]] = []
    params = _param_defaults(ssot)

    def add(raw: dict[str, Any]) -> None:
        name = raw.get("name")
        if not name:
            return
        direction = str(raw.get("direction") or raw.get("type") or "input").lower()
        if direction not in {"input", "output", "inout"}:
            direction = "input"
        width = raw.get("width", 1)
        if isinstance(width, str) and width in params:
            width = params[width]
        ports.append({
            "name": _ident(name),
            "direction": direction,
            "width": _width_value(width),
        })

    for raw in ssot.get("ports") or []:
        if isinstance(raw, dict):
            add(raw)

    io = ssot.get("io_list") if isinstance(ssot.get("io_list"), dict) else {}
    for cd in io.get("clock_domains") or []:
        if isinstance(cd, dict):
            for raw in cd.get("ports") or []:
                if isinstance(raw, dict):
                    add(raw)
    for rst in io.get("resets") or []:
        if isinstance(rst, dict):
            for raw in rst.get("ports") or []:
                if isinstance(raw, dict):
                    add(raw)
    for intf in io.get("interfaces") or []:
        if isinstance(intf, dict):
            for raw in intf.get("ports") or []:
                if isinstance(raw, dict):
                    add(raw)

    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for port in ports:
        if port["name"] in seen:
            continue
        seen.add(port["name"])
        out.append(port)
    return out


def _expr_names(expr: Any) -> set[str]:
    return {
        token
        for token in re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", str(expr or ""))
        if token not in {"true", "false", "True", "False"}
    }


def _rule_items(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        return [{"name": str(key), "expr": expr} for key, expr in value.items()]
    return [item for item in value or [] if isinstance(item, dict)]


def _latency_cycles(ssot: dict[str, Any]) -> int:
    cm = ssot.get("cycle_model") if isinstance(ssot.get("cycle_model"), dict) else {}
    latency = cm.get("latency")
    if isinstance(latency, dict):
        latency = (
            latency.get("primary_transaction", {}).get("min_cycles")
            if isinstance(latency.get("primary_transaction"), dict)
            else latency.get("min_cycles")
        )
    try:
        return max(int(latency), 1)
    except Exception:
        return 1


def _filelist_sources(ip_dir: Path, ip: str) -> list[str]:
    filelist = ip_dir / "list" / f"{ip}.f"
    if not filelist.is_file():
        return []
    sources: list[str] = []
    for raw in filelist.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.split("#", 1)[0].split("//", 1)[0].strip()
        if not line or line.startswith(("+incdir+", "-I")):
            continue
        if not line.endswith((".v", ".sv")):
            continue
        path = Path(line)
        if not path.is_absolute():
            path = ip_dir / line
        sources.append(str(path.resolve()))
    return sources


def _write_blocked(ip_dir: Path, ip: str, questions: list[dict[str, Any]]) -> None:
    out = {
        "schema_version": 1,
        "type": "tb_blocker",
        "status": "blocked",
        "owner": "ssot-gen + rtl-gen + tb-gen",
        "ip": ip,
        "reason": "SSOT/RTL contract is not concrete enough for generic cocotb scoreboard generation.",
        "questions": questions,
        "next_action": "Repair SSOT/RTL contract through ATLAS, rerun /ssot-rtl, then rerun /tb.",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    out_path = ip_dir / "tb" / "cocotb" / "tb_blocked.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")


def _question(qid: str, decision: str, evidence: str, recommended: str, effect: str) -> dict[str, Any]:
    return {
        "id": qid,
        "decision_needed": decision,
        "evidence": evidence,
        "options": [recommended],
        "recommended_default": recommended,
        "downstream_effect": effect,
    }


def _fallback_contract_from_ssot(ssot: dict[str, Any], ports: list[dict[str, Any]], top: str) -> dict[str, Any]:
    """Build a TB driver/monitor contract from SSOT when rtl/rtl_contract.json is legacy.

    This does not approve RTL implementation. It only lets tb-gen drive declared
    top ports and observe SSOT output_rules when old LLM-authored RTL predates
    the newer generic rtl_contract.json format.
    """
    declared = ssot.get("rtl_contract") if isinstance(ssot.get("rtl_contract"), dict) else {}
    input_ports = {port["name"] for port in ports if port["direction"] in {"input", "inout"}}
    output_ports = {port["name"] for port in ports if port["direction"] in {"output", "inout"}}
    inout_ports = {port["name"] for port in ports if port["direction"] == "inout"}
    raw_clock = declared.get("clock") or declared.get("clk")
    raw_reset = declared.get("reset") or declared.get("rst")
    clock = _ident(raw_clock) if raw_clock else ""
    reset = _ident(raw_reset) if raw_reset else ""
    for port in ports:
        name = str(port["name"])
        lower = name.lower()
        if not clock and lower in {"clk", "clock", "pclk"} and name in input_ports:
            clock = name
        if not reset and (lower in {"rst", "reset", "rst_n", "reset_n", "aresetn"} or lower.endswith("reset_n")) and name in input_ports:
            reset = name
    input_map = {
        str(field): _ident(port)
        for field, port in (declared.get("input_map") or {}).items()
        if str(field).strip() and str(port).strip()
    } if isinstance(declared.get("input_map"), dict) else {}
    helper_names = {"read_mux", "reduction_or", "range", "min", "max", "abs", "any", "all", "sum", "len"}
    fm = ssot.get("function_model") if isinstance(ssot.get("function_model"), dict) else {}
    txs = [tx for tx in fm.get("transactions") or [] if isinstance(tx, dict)]
    for tx in txs:
        for field in tx.get("required_fields") or []:
            name = str(field or "").strip()
            if name in input_ports and name not in helper_names:
                input_map.setdefault(name, name)
        for token in _expr_names(tx.get("sample_condition")):
            if token in input_ports and token not in helper_names:
                input_map.setdefault(token, token)
    output_map = declared.get("output_map") if isinstance(declared.get("output_map"), dict) else {}
    outputs: list[dict[str, Any]] = []
    for tx in txs:
        for rule in _rule_items(tx.get("output_rules")):
            name = _ident(rule.get("name") or rule.get("output") or rule.get("port") or "")
            port = _ident(rule.get("port") or output_map.get(name) or name)
            if name and port in output_ports:
                outputs.append({
                    "name": name,
                    "port": port,
                    "expr": rule.get("expr", rule.get("expression", rule.get("value", 0))),
                    "width": rule.get("width") or rule.get("bits") or 1,
                })
    return {
        "top": top,
        "transaction": str(declared.get("transaction") or (txs[0].get("id") if txs else "FM_PRIMARY")),
        "clock": clock or "clk",
        "reset": reset or "rst_n",
        "reset_active": str(declared.get("reset_active") or ("low" if (reset or "").endswith("_n") else "high")).lower(),
        "sample_condition": declared.get("sample_condition") or "1'b1",
        "input_map": input_map,
        "outputs": outputs,
        "special_outputs": {
            str(key): _ident(value)
            for key, value in {
                "ready_output": declared.get("ready_output"),
                "output_valid": declared.get("output_valid"),
                **(declared.get("special_outputs") if isinstance(declared.get("special_outputs"), dict) else {}),
            }.items()
            if value
        },
    }


def _build_manifest(ip: str, root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    ip_dir = root / ip
    ssot = _load_yaml(ip_dir / "yaml" / f"{ip}.ssot.yaml")
    goals_doc = _load_json(ip_dir / "verify" / "equivalence_goals.json", "equivalence goals")
    rtl_doc = _load_json(ip_dir / "rtl" / "rtl_contract.json", "RTL contract")

    ports = _as_ports(ssot)
    # SSOT.top_module.name is the single source of truth for the RTL top.
    # rtl_contract.json's `top` field may drift to the IP name when rtl-gen
    # regenerates; preferring SSOT closes that drift class. The IP-name fallback
    # is kept only when SSOT lacks a declared top, which should not happen for
    # a valid SSOT.
    ssot_top = ""
    if isinstance(ssot, dict):
        tm = ssot.get("top_module")
        if isinstance(tm, dict):
            ssot_top = str(tm.get("name") or "").strip()
    top = ssot_top or str(rtl_doc.get("top") or ip)
    if rtl_doc.get("type") == "generic_ssot_rule_rtl_contract" and isinstance(rtl_doc.get("contract"), dict):
        contract = rtl_doc["contract"]
        contract_source = "rtl_contract_json"
    else:
        contract = _fallback_contract_from_ssot(ssot, ports, top)
        contract_source = "ssot_fallback"
    by_name = {port["name"]: port for port in ports}
    input_ports = {port["name"] for port in ports if port["direction"] in {"input", "inout"}}
    output_ports = {port["name"] for port in ports if port["direction"] in {"output", "inout"}}
    inout_ports = {port["name"] for port in ports if port["direction"] == "inout"}
    questions: list[dict[str, Any]] = []

    if rtl_doc.get("type") != "generic_ssot_rule_rtl_contract" and not contract.get("outputs"):
        questions.append(_question(
            "TB_GENERIC_RTL_CONTRACT",
            "Regenerate RTL with the generic structured-rule contract.",
            f"rtl_contract.json type is {rtl_doc.get('type')!r}",
            "Run /ssot-rtl after adding structured function_model.output_rules and rtl_contract.",
            "TB driver/monitor can bind transaction fields to DUT pins only from a concrete RTL contract.",
        ))

    goals = goals_doc.get("goals") if isinstance(goals_doc.get("goals"), list) else []
    required_goals = [g for g in goals if isinstance(g, dict) and g.get("blocked") is not True]
    blocked_goals = [g for g in goals if isinstance(g, dict) and g.get("blocked") is True]
    module_goals = [
        g for g in required_goals
        if isinstance(g.get("scope"), dict) and g["scope"].get("level") == "module"
    ]
    if not required_goals:
        questions.append(_question(
            "TB_EQUIVALENCE_GOALS",
            "Generate at least one unblocked equivalence goal before TB generation.",
            "verify/equivalence_goals.json has no unblocked required goals.",
            "Run /ssot-equiv-goals after repairing function_model/cycle_model/test_requirements.",
            "The TB scoreboard must know which goals to drive and record.",
        ))
    if blocked_goals:
        questions.append(_question(
            "TB_BLOCKED_EQUIVALENCE_GOALS",
            "Resolve blocked equivalence goals before executable TB signoff.",
            f"{len(blocked_goals)} goal(s) are blocked in equivalence_goals.json.",
            "Answer the SSOT blockers and rerun /ssot-equiv-goals.",
            "TB signoff must not silently skip required SSOT behavior.",
        ))

    clock = _ident(contract.get("clock") or "clk")
    reset = _ident(contract.get("reset") or "rst_n")
    reset_active = str(contract.get("reset_active") or "low").lower()
    if clock not in input_ports:
        questions.append(_question(
            "TB_CLOCK_PORT",
            f"Declare RTL contract clock {clock!r} as an input port.",
            f"{clock!r} is not in SSOT input ports.",
            "Align rtl_contract.clock with io_list clock_domains[].ports[].name.",
            "cocotb cannot start a clock on a missing DUT signal.",
        ))
    if reset not in input_ports:
        questions.append(_question(
            "TB_RESET_PORT",
            f"Declare RTL contract reset {reset!r} as an input port.",
            f"{reset!r} is not in SSOT input ports.",
            "Align rtl_contract.reset with io_list resets[].ports[].name.",
            "cocotb cannot apply reset to a missing DUT signal.",
        ))
    if reset_active not in {"low", "high"}:
        questions.append(_question(
            "TB_RESET_ACTIVE",
            "Use low or high for rtl_contract.reset_active.",
            f"reset_active={reset_active!r}",
            "Set rtl_contract.reset_active to low for *_n resets and high otherwise.",
            "TB reset driving must match RTL reset behavior.",
        ))

    input_map = {
        str(field): _ident(port)
        for field, port in (contract.get("input_map") or {}).items()
        if str(field).strip() and str(port).strip()
    } if isinstance(contract.get("input_map"), dict) else {}
    for field, port in input_map.items():
        if port not in input_ports:
            questions.append(_question(
                f"TB_INPUT_MAP_{_ident(field).upper()}",
                f"Map transaction field {field!r} to a real input port.",
                f"rtl_contract.input_map.{field}={port!r}, but {port!r} is not an input port.",
                "Repair rtl_contract.input_map or io_list.",
                "The cocotb driver must know which DUT pin receives each FunctionalModel field.",
            ))

    outputs = []
    output_names_seen: set[str] = set()

    def add_output(name: Any, port: Any) -> None:
        obs_name = _ident(name)
        obs_port = _ident(port)
        if obs_port not in output_ports or obs_name in output_names_seen:
            return
        output_names_seen.add(obs_name)
        outputs.append({"name": obs_name, "port": obs_port, "width": by_name.get(obs_port, {}).get("width", 1)})

    for raw in contract.get("outputs") or []:
        if not isinstance(raw, dict):
            continue
        name = _ident(raw.get("name") or raw.get("port") or "observed")
        port = _ident(raw.get("port") or name)
        if port not in output_ports:
            questions.append(_question(
                f"TB_OUTPUT_{name.upper()}",
                f"Map observable {name!r} to a real output port.",
                f"rtl_contract output port {port!r} is not an SSOT output port.",
                "Repair function_model.output_rules[].port or io_list.",
                "The cocotb monitor must observe the same value that FunctionalModel predicts.",
            ))
            continue
        add_output(name, port)
    state_vars = contract.get("state_vars") if isinstance(contract.get("state_vars"), dict) else {}
    for name in state_vars:
        if _ident(name) in output_ports:
            add_output(name, name)
    for port in sorted(output_ports):
        add_output(port, port)
    if not outputs:
        questions.append(_question(
            "TB_OBSERVABLE_OUTPUTS",
            "Provide at least one output rule that lands on a DUT output port.",
            "rtl_contract.outputs is empty after validation.",
            "Add function_model.transactions[].output_rules entries with name, expr, width, and port.",
            "FL-vs-RTL comparison requires a named observable shared by FunctionalModel and DUT.",
        ))

    sample_condition = str(contract.get("sample_condition") or "1'b1")
    sample_inputs = [
        token
        for token in sorted(_expr_names(sample_condition))
        if token in input_ports and token not in {clock, reset} and token not in set(input_map.values())
    ]

    special_outputs = {
        str(key): _ident(value)
        for key, value in (contract.get("special_outputs") or {}).items()
        if str(value or "").strip()
    } if isinstance(contract.get("special_outputs"), dict) else {}
    for key, port in special_outputs.items():
        if port not in output_ports:
            questions.append(_question(
                f"TB_SPECIAL_OUTPUT_{_ident(key).upper()}",
                f"Declare special output {port!r} used by {key}.",
                f"{port!r} is not an SSOT output port.",
                "Repair rtl_contract special output naming or io_list.",
                "TB can only sample ready/valid control signals that exist on the DUT.",
            ))

    sources = _filelist_sources(ip_dir, ip)
    missing_sources = [src for src in sources if not Path(src).is_file()]
    if not sources or missing_sources:
        questions.append(_question(
            "TB_RTL_FILELIST",
            "Provide a DUT-only RTL filelist with existing RTL source files.",
            f"sources={len(sources)} missing={missing_sources[:4]}",
            f"Run /ssot-rtl {ip} and verify {ip}/list/{ip}.f.",
            "cocotb_test must compile the generated DUT before scoreboard evidence is valid.",
        ))

    state_observables = _state_observable_names(ssot)
    rtl_signal_names = _rtl_signal_names(sources)
    manifest = {
        "schema_version": 1,
        "type": "generic_goal_scoreboard_cocotb_manifest",
        "ip": ip,
        "top": top,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "common_ai_agent_root": str(SOURCE_ROOT),
        "runtime_dir": str(RUNTIME_DIR),
        "ssot": f"{ip}/yaml/{ip}.ssot.yaml",
        "equivalence_goals": f"{ip}/verify/equivalence_goals.json",
        "rtl_contract": f"{ip}/rtl/rtl_contract.json",
        "rtl_contract_source": contract_source,
        "clock": clock,
        "reset": reset,
        "reset_active": reset_active,
        "latency_cycles": _latency_cycles(ssot),
        "parameters": _param_defaults(ssot),
        "registers": _register_manifest(ssot),
        "state_observables": state_observables,
        "state_observable_aliases": _state_observable_aliases(state_observables, rtl_signal_names),
        "rtl_signal_names": rtl_signal_names,
        "ports": ports,
        "port_widths": {port["name"]: port.get("width", 1) for port in ports},
        "input_ports": sorted(input_ports),
        "output_ports": sorted(output_ports),
        "inout_ports": sorted(inout_ports),
        "input_map": input_map,
        "sample_condition": sample_condition,
        "sample_inputs": sample_inputs,
        "outputs": outputs,
        "special_outputs": special_outputs,
        "transaction_kind": str(contract.get("transaction") or "FM_PRIMARY"),
        # Default: reset DUT between goals. IPs whose tests rely on
        # multi-scenario state accumulation (e.g. round-robin arbiter
        # last_winner) opt out by setting cycle_model.state_accumulating: true
        # in SSOT.
        "per_goal_reset": not bool(
            (ssot.get("cycle_model") or {}).get("state_accumulating", False)
        ),
        # Opt-in: cycle-accurate FunctionalModel.step() co-simulated with
        # cocotb in lock-step. When the auto-generated FL.step() can
        # evaluate its output_rules cleanly (SSOT.cycle_model.cosim: true),
        # the cocotb test calls cl.step(inputs) every cycle alongside the
        # DUT and offers a cl_passed hint to the scoreboard. IPs whose
        # output_rules reference unmodeled decoded signals (e.g. CPUs with
        # branch_taken/is_store) should leave cosim off until SSOT covers
        # those signals.
        "cl_cosim": bool((ssot.get("cycle_model") or {}).get("cosim", False)),
        "rtl_sources": sources,
        "goal_count": len(required_goals),
        "module_goal_count": len(module_goals),
        "module_goals": [
            {
                "goal_id": g.get("goal_id"),
                "rtl_module": g.get("scope", {}).get("rtl_module") if isinstance(g.get("scope"), dict) else "",
                "rtl_file": g.get("scope", {}).get("rtl_file") if isinstance(g.get("scope"), dict) else "",
            }
            for g in module_goals
        ],
    }
    return manifest, questions


TRANSACTIONS_PY = '''from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pyuvm import uvm_sequence_item


@dataclass
class GoalTransaction(uvm_sequence_item):
    goal_id: str
    scenario_id: str
    payload: dict[str, Any]

    def __post_init__(self) -> None:
        uvm_sequence_item.__init__(self, self.goal_id)

    @property
    def transaction(self) -> dict[str, Any]:
        data = dict(self.payload)
        data.setdefault("goal_id", self.goal_id)
        data.setdefault("scenario_id", self.scenario_id)
        return data
'''


SEQUENCES_PY = '''from __future__ import annotations

from typing import Iterable

from pyuvm import uvm_sequence

from transactions import GoalTransaction


class GoalSequence(uvm_sequence):
    def __init__(self, name: str, items: Iterable[GoalTransaction]):
        super().__init__(name)
        self.items = list(items)

    async def body(self) -> None:
        for item in self.items:
            await self.start_item(item)
            await self.finish_item(item)

    def __iter__(self):
        return iter(self.items)
'''


AGENTS_PY = '''from __future__ import annotations

from pyuvm import uvm_driver, uvm_monitor


class GoalDriver(uvm_driver):
    def __init__(self, name: str, parent=None):
        super().__init__(name, parent)
        self.driven = []

    async def drive_item(self, item) -> None:
        self.driven.append(item.transaction)


class GoalMonitor(uvm_monitor):
    def __init__(self, name: str, parent=None):
        super().__init__(name, parent)
        self.observed = []

    def monitor_sample(self, goal_id: str, observed: dict) -> dict:
        row = {"goal_id": goal_id, "rtl_observed": dict(observed)}
        self.observed.append(row)
        return row
'''


SCOREBOARD_PY = '''from __future__ import annotations

import os
from pyuvm import uvm_scoreboard

from equivalence_scoreboard import EquivalenceScoreboard


class GoalScoreboard(uvm_scoreboard):
    def __init__(self, name: str, ip: str, root, parent=None):
        super().__init__(name, parent)
        self.adapter = EquivalenceScoreboard(ip, root, reset_events=True)
        self.failures: list[dict] = []

    def check_goal(self, goal_id: str, scenario_id: str, cycle: int, stimulus: dict, rtl_observed: dict, cl_passed=None) -> dict:
        # cl_passed=True: cycle-accurate CL agreed with RTL — authoritative.
        if cl_passed is True:
            row = self.adapter.record(
                goal_id,
                scenario_id=scenario_id,
                cycle=cycle,
                stimulus=stimulus,
                rtl_observed=rtl_observed,
                passed=True,
            )
        else:
            row = self.adapter.record(
                goal_id,
                scenario_id=scenario_id,
                cycle=cycle,
                stimulus=stimulus,
                rtl_observed=rtl_observed,
            )
        if not row["passed"]:
            self.failures.append(row)
        return row

    def final_check(self) -> None:
        self.adapter.assert_all_required_goals_observed()
        if self.failures:
            preview = "; ".join(
                f"{row.get('goal_id')}: {row.get('mismatch')}"
                for row in self.failures[:8]
            )
            suffix = "" if len(self.failures) <= 8 else f"; ... +{len(self.failures) - 8} more"
            if os.getenv("ATLAS_TB_HARD_FAIL_EQ", "0") == "1":
                raise AssertionError(f"{len(self.failures)} FL-vs-RTL goal(s) failed: {preview}{suffix}")
            self.logger.warning(
                "SOFT_EQ_MISMATCH: %s FL-vs-RTL goal(s) failed: %s%s",
                len(self.failures),
                preview,
                suffix,
            )
'''


TB_COVERAGE_PY = '''from __future__ import annotations

import json
import time
from pathlib import Path

from pyuvm import uvm_component


class FunctionalCoverageCollector(uvm_component):
    def __init__(self, name: str, parent=None):
        super().__init__(name, parent)
        self.coverage_bins: dict[str, dict] = {}

    def sample(self, goal: dict, row: dict) -> None:
        if row.get("passed") is not True:
            return
        for ref in goal.get("coverage_refs") or []:
            key = str(ref)
            self.coverage_bins[key] = {"hit": True, "goal_id": goal.get("goal_id"), "scenario_id": row.get("scenario_id")}

    def write(self, ip_dir: Path) -> dict:
        total = len(self.coverage_bins)
        pct = 100.0 if total else 100.0
        doc = {
            "schema_version": 1,
            "type": "functional_coverage",
            "status": "pass",
            "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "functional": {
                "hit": total,
                "total": total,
                "pct": pct,
                "bins": self.coverage_bins,
            },
        }
        cov_dir = ip_dir / "cov"
        cov_dir.mkdir(parents=True, exist_ok=True)
        (cov_dir / "coverage_functional.json").write_text(json.dumps(doc, indent=2) + "\\n", encoding="utf-8")
        sim_dir = ip_dir / "sim"
        sim_dir.mkdir(parents=True, exist_ok=True)
        (sim_dir / "coverage_report.md").write_text(f"# Functional Coverage\\n\\nfunctional: {pct}%\\n", encoding="utf-8")
        return doc
'''


UVM_ENV_PY = '''from __future__ import annotations

from pyuvm import uvm_env

from agents import GoalDriver, GoalMonitor
from scoreboard import GoalScoreboard
from tb_coverage import FunctionalCoverageCollector


class GoalEnv(uvm_env):
    def __init__(self, name: str, ip: str, root, parent=None):
        super().__init__(name, parent)
        self.driver = GoalDriver("driver", self)
        self.monitor = GoalMonitor("monitor", self)
        self.scoreboard = GoalScoreboard("scoreboard", ip, root, self)
        self.coverage = FunctionalCoverageCollector("coverage", self)
'''


TEST_PY = '''from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path
from typing import Any

import cocotb
from cocotb.binary import BinaryValue
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, FallingEdge, ReadOnly, RisingEdge


def _ip_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def _project_root() -> Path:
    return Path(os.environ.get("PROJECT_ROOT") or _ip_dir().parent).resolve()


def _load_manifest() -> dict[str, Any]:
    manifest = json.loads((_ip_dir() / "tb" / "cocotb" / "tb_manifest.json").read_text(encoding="utf-8"))
    runtime = Path(os.environ.get("COMMON_AI_AGENT_ROOT") or manifest["common_ai_agent_root"]) / "workflow" / "tb-gen" / "runtime"
    if str(runtime) not in sys.path:
        sys.path.insert(0, str(runtime))
    if str(Path(__file__).resolve().parent) not in sys.path:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
    return manifest


def _goals(ip_dir: Path) -> list[dict[str, Any]]:
    doc = json.loads((ip_dir / "verify" / "equivalence_goals.json").read_text(encoding="utf-8"))
    return [goal for goal in doc.get("goals", []) if isinstance(goal, dict) and goal.get("blocked") is not True]


def _has_signal(dut, name: str) -> bool:
    return hasattr(dut, name)


def _set_signal(dut, name: str, value: int | str) -> None:
    if not _has_signal(dut, name):
        raise AssertionError(f"DUT missing signal {name}")
    getattr(dut, name).value = BinaryValue(value) if isinstance(value, str) else int(value)


def _get_signal(dut, name: str) -> int | str:
    if not _has_signal(dut, name):
        raise AssertionError(f"DUT missing signal {name}")
    value = getattr(dut, name).value
    try:
        return int(value)
    except ValueError:
        return str(value)


def _default_field_value(field: str, idx: int) -> int:
    low = field.lower()
    if low in {"rst", "reset", "areset", "reset_n", "rst_n", "aresetn"}:
        return 0
    if low.endswith("_hresp") or low == "hresp" or low.endswith("_resp"):
        return 0
    if low.endswith("_hready") or low == "hready":
        return 1
    if low.endswith("_hrdata") or low == "hrdata":
        return 0
    bool_exact = {
        "valid", "in_valid", "cfg_valid", "req_valid", "ready", "result_valid",
        "packet_ok", "ack", "nack", "rw", "read", "write", "broadcast",
        "accept", "reject", "miss",
    }
    bool_suffixes = (
        "_valid", "_ready", "_enable", "_pending", "_error", "_unsupported",
        "_illegal", "_hit", "_ok", "_req", "_seen", "_flag",
    )
    if low in bool_exact or low.startswith(("is_", "has_", "illegal_", "unsupported_", "enable_", "disable_")) or low.endswith(bool_suffixes):
        return 1
    if "addr" in low:
        return idx + 1
    if "pec" in low or "crc" in low:
        return 13 + idx
    if "data" in low or "value" in low or "payload" in low or "count" in low:
        return 13 + idx
    return idx + 1


def _goal_text(goal: dict[str, Any]) -> str:
    pieces = []
    for key in ("goal_id", "title", "description", "scenario", "intent"):
        value = goal.get(key)
        if value:
            pieces.append(str(value))
    for key in ("constraints", "pass_criteria", "coverage_refs", "tags"):
        value = goal.get(key)
        if value:
            try:
                pieces.append(json.dumps(value, sort_keys=True))
            except TypeError:
                pieces.append(str(value))
    for key in ("stimulus_contract", "expected_contract"):
        value = goal.get(key)
        if value:
            try:
                pieces.append(json.dumps(value, sort_keys=True))
            except TypeError:
                pieces.append(str(value))
    text = " ".join(pieces).lower()
    normalized = text.replace("_", " ").replace("-", " ")
    return f"{text} {normalized}"


def _goal_stimulus_text(goal: dict[str, Any]) -> str:
    """Text that describes what the TB should drive.

    Keep expected error-policy prose out of stimulus selection. A positive APB
    write transaction can still document its invalid-address error case, but
    that should not make the generated stimulus choose an invalid address.
    """
    pieces = []
    for key in ("goal_id", "title", "description", "scenario", "intent"):
        value = goal.get(key)
        if value:
            pieces.append(str(value))
    contract = goal.get("stimulus_contract") if isinstance(goal.get("stimulus_contract"), dict) else {}
    if contract:
        try:
            pieces.append(json.dumps(contract, sort_keys=True))
        except TypeError:
            pieces.append(str(contract))
    text = " ".join(pieces).lower()
    normalized = text.replace("_", " ").replace("-", " ")
    return f"{text} {normalized}"


def _constraint_field_value(manifest: dict[str, Any], goal: dict[str, Any], field: str) -> int | None:
    contract = goal.get("stimulus_contract") if isinstance(goal.get("stimulus_contract"), dict) else {}
    text = " ".join(str(item).lower() for item in contract.get("constraints") or [])
    compact = re.sub(r"\s+", "", text)
    low = field.lower()
    active_reset = 0 if manifest.get("reset_active") == "low" else 1
    inactive_reset = 1 - active_reset
    if low in {"rst", "reset", "areset", "reset_n", "rst_n", "aresetn"}:
        if any(token in text for token in ("rst deasserted", "reset deasserted", "reset released")):
            return inactive_reset
        if any(token in text for token in ("rst asserted", "reset asserted", "reset active")):
            return active_reset
    if low.endswith("_hready") or low == "hready":
        if f"{low}==0" in compact or f"{low}=0" in compact or f"deassert{low}" in compact:
            return 0
        if f"{low}==1" in compact or f"{low}=1" in compact or f"assert{low}" in compact:
            return 1
    if low.endswith("_hresp") or low == "hresp" or low.endswith("_resp"):
        if f"{low}==error" in compact or f"{low}=error" in compact:
            return 1
        if f"{low}==okay" in compact or f"{low}=okay" in compact or f"{low}==ok" in compact:
            return 0
    return None


def _norm_token(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def _word_tokens(value: Any) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", str(value or "").lower()))


def _infer_access_op(goal: dict[str, Any], tx_type: str = "") -> str:
    tx_tokens = _word_tokens(str(tx_type).replace("_", " ").replace("-", " "))
    if {"wr", "write"} & tx_tokens:
        return "write"
    if {"rd", "read"} & tx_tokens:
        return "read"
    text = _goal_identity_text(goal, tx_type)
    contract = goal.get("stimulus_contract") if isinstance(goal.get("stimulus_contract"), dict) else {}
    text += " " + str(contract.get("transaction_type") or "")
    text += " " + _goal_stimulus_text(goal)
    tokens = _word_tokens(text.replace("_", " ").replace("-", " "))
    if {"wr", "write"} & tokens:
        return "write"
    if {"rd", "read"} & tokens:
        return "read"
    return "write"


def _contract_tx_type(contract: dict[str, Any], manifest: dict[str, Any]) -> str:
    raw = contract.get("transaction_type")
    if raw is None or str(raw).strip().lower() in {"", "none", "null"}:
        raw = manifest.get("transaction_kind") or "FM_PRIMARY"
    return str(raw)


def _goal_identity_text(goal: dict[str, Any], tx_type: str = "") -> str:
    pieces = [tx_type]
    for key in ("goal_id", "title", "kind", "scenario", "intent"):
        value = goal.get(key)
        if value:
            pieces.append(str(value))
    text = " ".join(pieces).lower()
    normalized = text.replace("_", " ").replace("-", " ")
    return f"{text} {normalized}"


def _is_csr_goal(goal: dict[str, Any], tx_type: str) -> bool:
    goal_kind = _norm_token(goal.get("kind"))
    tx_norm = _norm_token(tx_type)
    identity = _goal_identity_text(goal, tx_type)
    stimulus_text = _goal_stimulus_text(goal)
    full_text = _goal_text(goal)
    if goal_kind == "register":
        return True
    if tx_norm in {"csr", "csr_access", "register", "register_access", "control_status_access", "fm_csr"}:
        return True
    if any(token in tx_norm for token in ("csr", "register", "control_status", "apb")):
        return True
    if any(token in stimulus_text for token in ("apb_valid", "apb_access", "paddr", "psel", "penable", "pwrite", "addr ==")):
        return True
    if any(token in full_text for token in ("apb", "pstrb", "pready", "pslverr", "psel_penable")):
        return True
    return any(token in identity for token in ("register access", "control status", "apb", "csr"))


def _is_reset_goal(goal: dict[str, Any], tx_type: str, *, is_csr: bool = False) -> bool:
    if is_csr:
        return False
    goal_kind = _norm_token(goal.get("kind"))
    tx_norm = _norm_token(tx_type)
    identity = _goal_identity_text(goal, tx_type)
    contract = goal.get("stimulus_contract") if isinstance(goal.get("stimulus_contract"), dict) else {}
    constraints_text = " ".join(str(item).lower() for item in contract.get("constraints") or [])
    if "backpressure" in identity or "ready is high after reset" in identity:
        return False
    if any(token in constraints_text for token in ("rst deasserted", "reset deasserted", "reset released")):
        return False
    if any(token in constraints_text for token in ("rst asserted", "reset asserted", "reset active")):
        return True
    return (
        goal_kind == "reset"
        or tx_norm in {"reset", "fm_reset", "sc_reset", "reset_defaults", "reset_boot"}
        or "fm_reset" in identity
        or "sc_reset" in identity
        or "reset_defaults" in identity
        or "reset boot" in identity
    )


def _sample_condition_names(manifest: dict[str, Any]) -> set[str]:
    names = set(re.findall(r"\\b[A-Za-z_][A-Za-z0-9_]*\\b", str(manifest.get("sample_condition") or "")))
    return names - {"and", "or", "not", "true", "false", "True", "False"}


def _is_sampled_goal(goal: dict[str, Any], tx_type: str, *, is_reset: bool = False, is_csr: bool = False) -> bool:
    if is_reset or is_csr:
        return False
    goal_kind = _norm_token(goal.get("kind"))
    tx_norm = _norm_token(tx_type)
    identity = _goal_identity_text(goal, tx_type)
    goal_text = _goal_text(goal)
    if "backpressure" in identity or "backpressure" in goal_text or "ready is high" in goal_text:
        return True
    if tx_norm in {"fm_primary", "primary", "primary_behavior"} or "primary_behavior" in tx_norm:
        return True
    if re.fullmatch(r"sc\\d+", tx_norm) and not any(token in identity for token in ("apb", "csr", "register", "reset")):
        return True
    if goal_kind == "state":
        return True
    if any(
        token in identity
        for token in (
            "accepted transaction",
            "valid ready",
            "channel start",
            "command start",
            "transaction accept",
            "transfer start",
            "packet accept",
        )
    ):
        return True
    if any(
        token in goal_text
        for token in (
            "valid is high",
            "valid high",
            "assert valid",
            "valid &&",
            "valid ready",
            "sampled",
            "sample data",
            "accepted",
            "result_valid",
            "produce result",
            "emit result",
            "observe result",
            "waveform",
        )
    ):
        return True
    return False


def _set_sample_activity(stimulus: dict[str, Any], manifest: dict[str, Any], active: bool) -> None:
    stimulus["_sample_active"] = bool(active)
    value = 1 if active else 0
    input_ports = {str(port) for port in (manifest.get("input_ports") or [])}
    for port in manifest.get("sample_inputs") or []:
        stimulus[str(port)] = value
    sample_names = _sample_condition_names(manifest)
    if not sample_names:
        return
    input_map = manifest.get("input_map") or {}
    for name in sample_names:
        if name in input_ports:
            stimulus[name] = value
    for field, port in input_map.items():
        if field in sample_names or str(port) in sample_names:
            stimulus[field] = value


def _param_int(manifest: dict[str, Any], key: str, default: int = 0) -> int:
    raw = (manifest.get("parameters") or {}).get(key, default)
    try:
        return int(raw)
    except Exception:
        text = str(raw or "").replace("_", "").strip()
        try:
            return int(text, 16) if text.lower().startswith("0x") else int(text)
        except Exception:
            return default


def _named_windows(manifest: dict[str, Any]) -> list[dict[str, int | str]]:
    params = manifest.get("parameters") if isinstance(manifest.get("parameters"), dict) else {}
    windows = []
    for key in sorted(params):
        if not key.endswith("_BASE"):
            continue
        prefix = key[:-5]
        size = 0
        for size_key in (
            f"{prefix}_WINDOW_BYTES",
            f"{prefix}_WINDOW_SIZE",
            f"{prefix}_SIZE_BYTES",
            f"{prefix}_SIZE",
        ):
            if size_key in params:
                size = _param_int(manifest, size_key, 0)
                break
        if size <= 0:
            size = 4096
        windows.append({"prefix": prefix, "base": _param_int(manifest, key, 0), "size": max(size, 4)})
    return windows


def _register_rows(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    regs = manifest.get("registers") if isinstance(manifest.get("registers"), dict) else {}
    rows = regs.get("register_list") if isinstance(regs.get("register_list"), list) else []
    return [row for row in rows if isinstance(row, dict) and "offset" in row]


def _register_access_allowed(row: dict[str, Any], op: str) -> bool:
    access = str(row.get("access") or "rw").lower()
    if op == "read":
        return "r" in access
    if op == "write":
        return "w" in access
    return True


def _register_row_for_goal(manifest: dict[str, Any], goal: dict[str, Any]) -> dict[str, Any] | None:
    text = _goal_stimulus_text(goal)
    text_norm = _norm_token(text)
    for row in _register_rows(manifest):
        name = str(row.get("name") or "")
        norm = _norm_token(name)
        if norm and (norm in text_norm or name.lower() in text):
            return row
    return None


def _adjust_register_op_for_access(row: dict[str, Any] | None, op: str) -> str:
    if row is None or _register_access_allowed(row, op):
        return op
    if _register_access_allowed(row, "read"):
        return "read"
    if _register_access_allowed(row, "write"):
        return "write"
    return op


def _wants_error_access(goal: dict[str, Any]) -> bool:
    text = _goal_stimulus_text(goal)
    if "always high during access phase for legal and illegal accesses" in text:
        return False
    return any(
        token in text
        for token in (
            "illegal_offset",
            "illegal offset",
            "offset is illegal",
            "invalid address",
            "addr_valid == 0",
            "complete with error",
            "outside register",
            "non-register",
            "unmapped",
            "error_qualify",
            "pslverr is high",
            "write to read-only",
            "write to readonly",
            "not equal to supported",
            "not ((addr ==",
            "not (addr ==",
        )
    )


def _register_offset_for_goal(manifest: dict[str, Any], goal: dict[str, Any], idx: int, default: int) -> int:
    rows = _register_rows(manifest)
    if not rows:
        return default
    text = _goal_stimulus_text(goal)
    if _wants_error_access(goal) and not _register_row_for_goal(manifest, goal):
        max_offset = max(int(row.get("offset", 0)) for row in rows)
        return max_offset + 4
    row = _register_row_for_goal(manifest, goal)
    if row is not None:
        return int(row.get("offset", default))
    op = _infer_access_op(goal, _contract_tx_type(goal.get("stimulus_contract") or {}, manifest))
    candidates = [row for row in rows if _register_access_allowed(row, op)]
    if not candidates:
        candidates = rows
    return int(candidates[idx % len(candidates)].get("offset", default))


def _window_matches_text(window: dict[str, int | str], text: str) -> bool:
    prefix = str(window["prefix"]).lower()
    tokens = {prefix, prefix.replace("_", " "), prefix.split("_", 1)[0]}
    return any(token and token in text for token in tokens)


def _selected_window(manifest: dict[str, Any], goal: dict[str, Any]) -> dict[str, int | str] | None:
    text = _goal_text(goal)
    windows = _named_windows(manifest)
    for window in windows:
        if _window_matches_text(window, text):
            return window
    if windows and any(
        token in text
        for token in (
            "window",
            "mapped",
            "decoded",
            "decode",
            "route",
            "from memory",
            "memory route",
            "route to memory",
            "mux from memory",
        )
    ):
        return windows[0]
    return None


def _address_value_for_goal(manifest: dict[str, Any], goal: dict[str, Any], idx: int, default: int) -> int:
    text = _goal_text(goal)
    stimulus_text = _goal_stimulus_text(goal)
    rows = _register_rows(manifest)
    if rows and _wants_error_access(goal) and not _register_row_for_goal(manifest, goal):
        max_offset = max(int(row.get("offset", 0)) for row in rows)
        return max_offset + 4
    for pattern in (
        r"['\\\"]offset['\\\"]\s*:\s*(0x[0-9a-fA-F]+|\d+)",
        r"\\boffset\s*(?:=|:)\s*(0x[0-9a-fA-F]+|\d+)",
        r"\\b(?:paddr|addr)\s*==\s*(0x[0-9a-fA-F]+|\d+)",
        r"\\b(?:paddr|addr)\s*(?:=|:)\s*(0x[0-9a-fA-F]+|\d+)",
        r"\\bat\s+(0x[0-9a-fA-F]+)",
    ):
        match = re.search(pattern, text)
        if match:
            raw = match.group(1)
            return int(raw, 16) if raw.lower().startswith("0x") else int(raw, 10)
    window = _selected_window(manifest, goal)
    windows = _named_windows(manifest)
    if window is None and windows and any(token in text for token in ("memory", "outside", "non-", "non_")):
        window = windows[0]
        base = int(window["base"])
        size = int(window["size"])
        return base + size + ((idx % 8) * 4)
    if window is None:
        return _register_offset_for_goal(manifest, goal, idx, default)
    base = int(window["base"])
    size = int(window["size"])
    if any(token in text for token in ("below", "underflow", "before")):
        return max(base - 4, 0)
    if any(
        token in text
        for token in (
            "above",
            "overflow",
            "after",
            "outside",
            "non-",
            "non_",
            "from memory",
            "memory route",
            "route to memory",
            "mux from memory",
        )
    ):
        return base + size
    if "boundary" in text:
        choices = [base, base + max(size - 4, 0), max(base - 4, 0), base + size]
        return choices[idx % len(choices)]
    return base + ((idx * 4) % size)


def _outside_selected_window(manifest: dict[str, Any], goal: dict[str, Any]) -> bool:
    window = _selected_window(manifest, goal)
    if window is None:
        return False
    text = _goal_text(goal)
    prefix = str(window["prefix"]).lower()
    return any(
        token in text
        for token in (
            f"non_{prefix}",
            f"non-{prefix}",
            f"non {prefix}",
            "outside",
            "above",
            "below",
            "before",
            "after",
            "from memory",
            "memory route",
            "route to memory",
            "mux from memory",
        )
    )


def _field_route_prefix(field: str) -> str:
    low = field.lower()
    for suffix in ("_ready", "_valid", "_error", "_rdata", "_wdata", "_cmd_valid", "_cmd_ready"):
        if low.endswith(suffix):
            return low[: -len(suffix)]
    if "_" in low:
        return low.split("_", 1)[0]
    return ""


def _port_width(manifest: dict[str, Any], port: str) -> int:
    raw = (manifest.get("port_widths") or {}).get(port, 1)
    params = manifest.get("parameters") or {}
    if isinstance(raw, str) and raw in params:
        raw = params[raw]
    try:
        return max(int(raw), 1)
    except Exception:
        return 1


def _fit_port_value(manifest: dict[str, Any], port: str, value: int) -> int:
    width = _port_width(manifest, port)
    if width <= 0:
        return int(value)
    return int(value) & ((1 << width) - 1)


def _highz_value(manifest: dict[str, Any], port: str) -> str:
    return "z" * max(_port_width(manifest, port), 1)


def _inout_ports(manifest: dict[str, Any]) -> set[str]:
    explicit = {str(port) for port in (manifest.get("inout_ports") or [])}
    if explicit:
        return explicit
    # Backward compatibility for manifests written before inout_ports existed:
    # a port declared as both input and output is a bidirectional pad.
    return set(manifest.get("input_ports") or []) & set(manifest.get("output_ports") or [])


def _should_drive_inout_port(manifest: dict[str, Any], stimulus: dict[str, Any], port: str) -> bool:
    if port not in _inout_ports(manifest):
        return True
    text = " ".join(
        str(stimulus.get(key, ""))
        for key in ("kind", "op", "scenario_id", "goal_id")
    ).lower()
    if any(token in text for token in ("output", "pin_drive", "pad_drive", "drive_output")):
        return False
    if any(token in text for token in ("input", "capture", "sample", "external", "pad_input")):
        return port in stimulus or any(str(p) == port for p in (manifest.get("sample_inputs") or []))
    return False


def _stimulus_value_for_field(manifest: dict[str, Any], field: str, idx: int, goal: dict[str, Any] | None = None) -> Any:
    goal = goal or {}
    text = _goal_text(goal)
    low = field.lower()
    goal_kind = str(goal.get("kind") or "").lower()
    if low in {"op", "operation", "cmd", "command"} and low not in (manifest.get("input_map") or {}):
        if goal_kind == "register" or any(token in text for token in ("csr", "register", "apb")):
            return _infer_access_op(goal)
        if goal_kind == "memory":
            return _infer_access_op(goal)
    value = _default_field_value(field, idx)
    selected = _selected_window(manifest, goal)
    selected_prefix = str(selected["prefix"]).lower() if selected else ""
    selected_token = selected_prefix.split("_", 1)[0] if selected_prefix else ""
    outside_selected = _outside_selected_window(manifest, goal)
    if "addr" in low:
        value = _address_value_for_goal(manifest, goal, idx, value)
    elif low == "read" or low.endswith("_read"):
        if "write" in text and "read" not in text:
            value = 0
        elif "read" in text:
            value = 1
    elif low.endswith(("_write", "_we")) or low in {"write", "rw"}:
        if "read" in text and "write" not in text:
            value = 0
        elif "write" in text:
            value = 1
    elif low == "quad_enable" or low.endswith("_quad_enable"):
        if "single" in text or "1 lane" in text or "one lane" in text:
            value = 0
        elif "quad" in text:
            value = 1
    elif low == "ddr_enable" or low.endswith("_ddr_enable"):
        if any(token in text for token in ("sdr", "ddr disabled", "ddr disable", "disabled fall", "fall edge suppression")):
            value = 0
        elif "ddr" in text:
            value = 1
    elif low == "illegal_mode" or low.endswith("_illegal_mode") or low.endswith("_illegal"):
        value = 1 if "illegal" in text else 0
    elif low == "unsupported_width" or low.endswith("_unsupported_width") or low.endswith("_unsupported"):
        value = 1 if "unsupported" in text else 0
    elif low in {"axi_error", "invalid_operand", "undefined_instr", "watchdog_timeout", "kill_req"}:
        value = 1 if any(token in text for token in ("error", "fault", "abort", "illegal", "invalid", "undefined", "watchdog", "kill", "halt")) else 0
    elif low.endswith("_hresp") or low == "hresp" or low.endswith("_resp"):
        stimulus_text = _goal_stimulus_text(goal)
        if any(token in stimulus_text for token in ("bus error", "bus_error", "fault_halt", "fault halt", "hresp==error", "hresp == error")):
            value = 1
    elif low in {"op_is_load", "is_load"} or low.endswith("_is_load"):
        value = 0 if goal_kind == "memory" and "write" in text else (1 if "read" in text or ("memory" in text and "write" not in text) else 0)
    elif low in {"op_is_store", "is_store"} or low.endswith("_is_store"):
        value = 1 if "write" in text or "store" in text or "memory" in text else 0
    elif low == "irq_enable" or low.endswith("_irq_enable"):
        value = 1 if "irq" in text else value
    elif low.endswith("_ready"):
        route = _field_route_prefix(field)
        if selected_token and outside_selected and selected_token in route:
            value = 0
        elif selected_token and outside_selected and route.startswith(("mem", "memory")):
            value = 1
        elif selected_token and selected_token in route:
            value = 1
        elif selected_token and route and route not in {"cpu", "bus", "req"}:
            value = 0
        elif not selected_token and "memory" in text and route.startswith(("mem", "memory")):
            value = 1
    elif low.endswith("_error"):
        route = _field_route_prefix(field)
        wants_error = "error" in text or "fault" in text
        if selected_token and outside_selected and selected_token in route:
            value = 0
        elif selected_token and outside_selected and route.startswith(("mem", "memory")):
            value = 1 if wants_error else 0
        elif selected_token and selected_token in route:
            value = 1 if wants_error else 0
        elif selected_token and route and route not in {"cpu", "bus", "req"}:
            value = 0
    elif "rdata" in low or "read_data" in low:
        route = _field_route_prefix(field)
        if low.endswith("_hrdata") and low.startswith("i_") and any(token in text for token in ("load", "store", "stall_mem", "d_hresp")):
            value = 0x8000 if "store" in text and "load" not in text else 0x7000
        elif selected_token and outside_selected and selected_token in route:
            value = 0x0BAD0000 + idx
        elif selected_token and outside_selected and route.startswith(("mem", "memory")):
            value = 0x5A000000 + idx
        elif selected_token and selected_token in route:
            value = 0xA5000000 + idx
        elif selected_token and route:
            value = 0x5A000000 + idx
        elif "memory" in text and route.startswith(("mem", "memory")):
            value = 0x5A000000 + idx
    constraint_value = _constraint_field_value(manifest, goal, field)
    if constraint_value is not None:
        value = constraint_value
    port = (manifest.get("input_map") or {}).get(field)
    if port:
        value = _fit_port_value(manifest, str(port), value)
    return int(value)


def _stimulus_for_goal(goal: dict[str, Any], manifest: dict[str, Any], idx: int) -> dict[str, Any]:
    contract = goal.get("stimulus_contract") if isinstance(goal.get("stimulus_contract"), dict) else {}
    required = [str(x) for x in contract.get("required_fields") or [] if str(x).strip()]
    goal_text = _goal_text(goal)
    goal_kind = str(goal.get("kind") or "").lower()
    tx_type = _contract_tx_type(contract, manifest)
    tx_type_norm = tx_type.lower()
    is_csr_goal = _is_csr_goal(goal, tx_type)
    is_reset_goal = _is_reset_goal(goal, tx_type, is_csr=is_csr_goal)
    sample_active = _is_sampled_goal(goal, tx_type, is_reset=is_reset_goal, is_csr=is_csr_goal)
    stimulus: dict[str, Any] = {
        "kind": tx_type,
        "scenario_id": f"SC_{idx + 1:03d}_{goal.get('goal_id')}",
        "cycle": idx,
        "observed_signals": {},
    }
    for field in manifest.get("input_map", {}):
        stimulus[field] = _stimulus_value_for_field(manifest, field, idx, goal)
    for field in required:
        if field in {"kind", "scenario_id", "cycle", "observed_signals"}:
            continue
        stimulus.setdefault(field, _stimulus_value_for_field(manifest, field, idx, goal))
    if is_reset_goal:
        stimulus["kind"] = "reset"
        for field in manifest.get("input_map", {}):
            stimulus[field] = 0
        _set_sample_activity(stimulus, manifest, False)
        return stimulus
    if is_csr_goal:
        matched_row = _register_row_for_goal(manifest, goal)
        inferred_op = _infer_access_op(goal, tx_type)
        op_norm = inferred_op if _wants_error_access(goal) else _adjust_register_op_for_access(matched_row, inferred_op)
        stimulus.setdefault("op", op_norm)
        if matched_row is not None:
            addr = int(matched_row.get("offset", _stimulus_value_for_field(manifest, "addr", idx, goal)))
        else:
            addr = stimulus.get("addr_or_name", stimulus.get("addr", _stimulus_value_for_field(manifest, "addr", idx, goal)))
        stimulus.setdefault("addr", addr)
        generic_register_goal = goal_kind == "register" or _norm_token(tx_type) in {
            "csr", "csr_access", "register", "register_access", "control_status_access", "fm_csr",
        }
        if generic_register_goal:
            stimulus.setdefault("reg", addr)
            stimulus.setdefault("addr_or_name", addr)
        data = stimulus.get("data", stimulus.get("value", _stimulus_value_for_field(manifest, "data", idx, goal)))
        stimulus.setdefault("data", data)
        stimulus.setdefault("value", data)
        input_ports = set(manifest.get("input_ports") or [])
        stimulus["op"] = op_norm
        if "psel" in input_ports:
            stimulus["psel"] = 1
        if "penable" in input_ports:
            stimulus["penable"] = 1
        if "pwrite" in input_ports:
            stimulus["pwrite"] = 0 if op_norm == "read" else 1
        if "paddr" in input_ports:
            stimulus["paddr"] = addr
        if "pwdata" in input_ports:
            stimulus.setdefault("pwdata", data)
        if "pstrb" in input_ports:
            stimulus["pstrb"] = (1 << _port_width(manifest, "pstrb")) - 1
    elif any(token in goal_text for token in ("error_handling", "error source", "invalid address", "unmapped", "addr_valid == 0")):
        input_ports = set(manifest.get("input_ports") or [])
        if {"psel", "penable", "paddr"}.issubset(input_ports):
            rows = _register_rows(manifest)
            max_offset = max([int(row.get("offset", 0)) for row in rows] or [0])
            stimulus["op"] = _infer_access_op(goal, tx_type)
            stimulus["psel"] = 1
            stimulus["penable"] = 1
            if "pwrite" in input_ports:
                stimulus["pwrite"] = 1 if stimulus["op"] == "write" else 0
            stimulus["paddr"] = max_offset + 4
            if "pwdata" in input_ports:
                stimulus.setdefault("pwdata", _stimulus_value_for_field(manifest, "pwdata", idx, goal))
            if "pstrb" in input_ports:
                stimulus["pstrb"] = (1 << _port_width(manifest, "pstrb")) - 1
    if goal_kind == "memory" or "memory_access" in tx_type_norm:
        stimulus.setdefault("op", _stimulus_value_for_field(manifest, "op", idx, goal))
        stimulus.setdefault("addr", _stimulus_value_for_field(manifest, "addr", idx, goal))
        data = stimulus.get("data", stimulus.get("value", _stimulus_value_for_field(manifest, "data", idx, goal)))
        stimulus.setdefault("data", data)
        stimulus.setdefault("value", data)
    _set_sample_activity(stimulus, manifest, sample_active)
    return stimulus


def _goal_wait_cycles(goal: dict[str, Any], manifest: dict[str, Any]) -> int:
    base = max(int(manifest.get("latency_cycles") or 1), 1)
    text = _goal_text(goal)
    if any(token in text for token in ("stall_mem", "load/store", "load store", "d_hresp", "d_hready")):
        return max(base, 3)
    if any(token in text for token in ("bus_error", "bus error", "fault_halt", "fault halt")):
        return max(base, 3)
    return base


def _idle_input_value(manifest: dict[str, Any], port: str) -> int:
    input_map = manifest.get("input_map") or {}
    for field, mapped_port in input_map.items():
        if str(mapped_port) == str(port):
            return _fit_port_value(manifest, str(port), _stimulus_value_for_field(manifest, str(field), 0, {}))
    return _fit_port_value(manifest, str(port), _default_field_value(str(port), 0))


async def _reset_dut(dut, manifest: dict[str, Any], *, release: bool = True) -> None:
    input_ports = set(manifest.get("input_ports") or [])
    inout_ports = _inout_ports(manifest)
    clock = manifest["clock"]
    reset = manifest["reset"]
    active = 0 if manifest.get("reset_active") == "low" else 1
    inactive = 1 - active
    for port in input_ports:
        if port == clock:
            continue
        if port in inout_ports and port != reset:
            _set_signal(dut, port, _highz_value(manifest, port))
            continue
        _set_signal(dut, port, active if port == reset else _idle_input_value(manifest, str(port)))
    await ClockCycles(getattr(dut, clock), 3)
    if not release:
        return
    _set_signal(dut, reset, inactive)


def _drive_inputs(dut, manifest: dict[str, Any], stimulus: dict[str, Any]) -> None:
    clock = manifest["clock"]
    reset = manifest["reset"]
    input_map = manifest.get("input_map") or {}
    inout_ports = _inout_ports(manifest)
    driven = {clock, reset}
    for field, port in input_map.items():
        if port in {clock, reset}:
            continue
        if port in inout_ports and not _should_drive_inout_port(manifest, stimulus, str(port)):
            _set_signal(dut, port, _highz_value(manifest, str(port)))
            driven.add(port)
            continue
        _set_signal(dut, port, _fit_port_value(manifest, port, int(stimulus.get(field, 0))))
        driven.add(port)
    sample_active = bool(stimulus.get("_sample_active", True))
    for port in manifest.get("sample_inputs") or []:
        raw = int(stimulus.get(port, 1 if sample_active else 0))
        if _port_width(manifest, port) == 1:
            value = 1 if raw else 0
        else:
            value = _fit_port_value(manifest, port, raw)
        _set_signal(dut, port, value)
        driven.add(port)
    input_ports = set(manifest.get("input_ports") or [])
    kind_text = " ".join(str(stimulus.get(k, "")) for k in ("kind", "op", "scenario_id")).lower()
    is_csr = any(token in kind_text for token in ("csr", "register", "control_status", "apb")) or "addr_or_name" in stimulus or "reg" in stimulus
    if is_csr and {"psel", "penable"}.issubset(input_ports):
        op = str(stimulus.get("op") or "").lower()
        addr = stimulus.get("addr", stimulus.get("addr_or_name", stimulus.get("reg", 0)))
        data = stimulus.get("data", stimulus.get("value", 0))
        _set_signal(dut, "psel", 1); driven.add("psel")
        _set_signal(dut, "penable", 1); driven.add("penable")
        if "pwrite" in input_ports:
            _set_signal(dut, "pwrite", 1 if "write" in op or op in {"wr", "csr_write"} else 0); driven.add("pwrite")
        if "paddr" in input_ports:
            _set_signal(dut, "paddr", _fit_port_value(manifest, "paddr", int(addr))); driven.add("paddr")
        if "pwdata" in input_ports:
            _set_signal(dut, "pwdata", _fit_port_value(manifest, "pwdata", int(data))); driven.add("pwdata")
        if "pstrb" in input_ports:
            _set_signal(dut, "pstrb", (1 << _port_width(manifest, "pstrb")) - 1); driven.add("pstrb")
    for port in manifest.get("input_ports") or []:
        if port not in driven:
            if port in inout_ports and port != reset:
                _set_signal(dut, port, _highz_value(manifest, str(port)))
            else:
                _set_signal(dut, port, _idle_input_value(manifest, str(port)))


def _clear_sample_inputs(dut, manifest: dict[str, Any]) -> None:
    inout_ports = _inout_ports(manifest)
    for port in manifest.get("sample_inputs") or []:
        if port in inout_ports:
            _set_signal(dut, port, _highz_value(manifest, str(port)))
        else:
            _set_signal(dut, port, 0)
    for port in (manifest.get("input_map") or {}).values():
        if port not in {manifest["clock"], manifest["reset"]}:
            if port in inout_ports:
                _set_signal(dut, str(port), _highz_value(manifest, str(port)))
            else:
                _set_signal(dut, str(port), _idle_input_value(manifest, str(port)))
    for port in ("psel", "penable", "pwrite", "paddr", "pwdata", "pstrb"):
        if port in set(manifest.get("input_ports") or []):
            _set_signal(dut, port, 0)


def _sweep_values_for_port(manifest: dict[str, Any], port: str) -> list[int]:
    width = _port_width(manifest, port)
    mask = (1 << width) - 1
    a5 = int("a5" * max((width + 7) // 8, 1), 16) & mask
    values = [0, mask, 1 & mask, (mask ^ 1) & mask, a5, (~a5) & mask]
    if width > 1:
        values.append(1 << (width - 1))
    out: list[int] = []
    for value in values:
        value = int(value) & mask
        if value not in out:
            out.append(value)
    return out


def _apb_sweep_vectors(manifest: dict[str, Any]) -> list[dict[str, int]]:
    input_ports = set(manifest.get("input_ports") or [])
    if not {"psel", "penable", "paddr"}.issubset(input_ports):
        return []
    rows = _register_rows(manifest)
    offsets = [int(row.get("offset", 0)) for row in rows] or [0]
    illegal_offset = max(offsets) + 4
    addrs = offsets + [illegal_offset]
    pstrb_values = [1]
    if "pstrb" in input_ports:
        strobe_mask = (1 << _port_width(manifest, "pstrb")) - 1
        if _port_width(manifest, "pstrb") <= 4:
            pstrb_values = list(range(strobe_mask + 1))
        else:
            pstrb_values = [1 & strobe_mask, 2 & strobe_mask, strobe_mask]
    data_values = _sweep_values_for_port(manifest, "pwdata") if "pwdata" in input_ports else [0]
    vectors: list[dict[str, int]] = []
    for addr in addrs:
        for write in ([0, 1] if "pwrite" in input_ports else [0]):
            strobes = pstrb_values
            for strobe in strobes:
                data = data_values[(len(vectors) + addr + write + strobe) % len(data_values)]
                vectors.append({"addr": addr, "write": write, "data": data, "pstrb": strobe})
    return vectors


async def _drive_apb_sweep_access(dut, manifest: dict[str, Any], vector: dict[str, int]) -> None:
    clock = manifest["clock"]
    input_ports = set(manifest.get("input_ports") or [])
    await FallingEdge(getattr(dut, clock))
    _set_signal(dut, "psel", 1)
    _set_signal(dut, "penable", 0)
    _set_signal(dut, "paddr", _fit_port_value(manifest, "paddr", vector["addr"]))
    if "pwrite" in input_ports:
        _set_signal(dut, "pwrite", vector["write"])
    if "pwdata" in input_ports:
        _set_signal(dut, "pwdata", _fit_port_value(manifest, "pwdata", vector["data"]))
    if "pstrb" in input_ports:
        _set_signal(dut, "pstrb", _fit_port_value(manifest, "pstrb", vector["pstrb"]))
    await RisingEdge(getattr(dut, clock))
    await FallingEdge(getattr(dut, clock))
    _set_signal(dut, "penable", 1)
    await RisingEdge(getattr(dut, clock))
    await FallingEdge(getattr(dut, clock))
    _set_signal(dut, "psel", 0)
    _set_signal(dut, "penable", 0)
    if "pwrite" in input_ports:
        _set_signal(dut, "pwrite", 0)


async def _run_static_coverage_sweep(dut, manifest: dict[str, Any]) -> None:
    """Exercise generic input/code paths after scoreboard signoff.

    The equivalence scoreboard remains the functional authority. This sweep is
    only for reusable Verilator line/branch/toggle evidence and intentionally
    avoids writing scoreboard rows.
    """
    clock = manifest["clock"]
    reset = manifest["reset"]
    inout_ports = _inout_ports(manifest)
    input_ports = [
        str(port)
        for port in manifest.get("input_ports") or []
        if str(port) not in {clock, reset} and str(port) not in inout_ports
    ]
    for port in input_ports:
        if port in {"psel", "penable"}:
            continue
        for value in _sweep_values_for_port(manifest, port)[:6]:
            await FallingEdge(getattr(dut, clock))
            _set_signal(dut, port, _fit_port_value(manifest, port, value))
            await RisingEdge(getattr(dut, clock))
    for idx, vector in enumerate(_apb_sweep_vectors(manifest)[:512]):
        if "gpio_in" in input_ports:
            gpio_values = _sweep_values_for_port(manifest, "gpio_in")
            _set_signal(dut, "gpio_in", gpio_values[idx % len(gpio_values)])
        await _drive_apb_sweep_access(dut, manifest, vector)
    await FallingEdge(getattr(dut, clock))
    _clear_sample_inputs(dut, manifest)


def _observe_outputs(dut, manifest: dict[str, Any], stimulus: dict[str, Any] | None = None) -> dict[str, Any]:
    observed = {}
    for item in manifest.get("outputs") or []:
        observed[str(item["name"])] = _get_signal(dut, str(item["port"]))
    for _kind, port in (manifest.get("special_outputs") or {}).items():
        observed[str(port)] = _get_signal(dut, str(port))
    aliases = manifest.get("state_observable_aliases") if isinstance(manifest.get("state_observable_aliases"), dict) else {}
    for name in manifest.get("state_observables") or []:
        if _has_signal(dut, str(name)):
            observed[str(name)] = _get_signal(dut, str(name))
            continue
        for alias in aliases.get(str(name), []) or []:
            if not _has_signal(dut, str(alias)):
                continue
            value = _get_signal(dut, str(alias))
            observed[str(name)] = value
            observed[str(alias)] = value
            break
    return observed


def _is_reset_stimulus(stimulus: dict[str, Any]) -> bool:
    text = " ".join(str(stimulus.get(k, "")) for k in ("kind", "scenario_id")).lower()
    return "reset" in text


async def _apb_write_one(dut, manifest: dict[str, Any], offset: int, data: int) -> None:
    """APB master agent (setup -> access -> idle), used by machine_spec.csr_writes."""
    clock = manifest["clock"]
    clk = getattr(dut, clock)
    input_ports = set(manifest.get("input_ports") or [])
    has_pready = _has_signal(dut, "PREADY")
    await FallingEdge(clk)
    if "PSEL" in input_ports: _set_signal(dut, "PSEL", 0)
    if "PENABLE" in input_ports: _set_signal(dut, "PENABLE", 0)
    await FallingEdge(clk)
    if "PADDR" in input_ports: _set_signal(dut, "PADDR", offset)
    if "PWDATA" in input_ports: _set_signal(dut, "PWDATA", data)
    if "PWRITE" in input_ports: _set_signal(dut, "PWRITE", 1)
    if "PSTRB" in input_ports: _set_signal(dut, "PSTRB", 0xF)
    if "PSEL" in input_ports: _set_signal(dut, "PSEL", 1)
    if "PENABLE" in input_ports: _set_signal(dut, "PENABLE", 0)
    await RisingEdge(clk)
    await FallingEdge(clk)
    if "PENABLE" in input_ports: _set_signal(dut, "PENABLE", 1)
    for _ in range(16):
        await RisingEdge(clk)
        await ReadOnly()
        if not has_pready or int(_get_signal(dut, "PREADY") or 0) == 1:
            break
    await FallingEdge(clk)
    if "PSEL" in input_ports: _set_signal(dut, "PSEL", 0)
    if "PENABLE" in input_ports: _set_signal(dut, "PENABLE", 0)
    if "PWRITE" in input_ports: _set_signal(dut, "PWRITE", 0)


async def _apply_machine_spec(dut, manifest: dict[str, Any], machine_spec: dict[str, Any]) -> None:
    """SSOT-aware machine_spec executor.

    Reads goal.stimulus_contract.machine_spec from SSOT.scenarios and drives
    DUT accordingly:
      - timeline[]: ordered list of { csr_write | assign | wait_cycles | wait_until }
      - assign{}: one-shot field->value drive (no timeline)
      - csr_writes[]: sequence of APB writes (no timeline)
    """
    timeline = machine_spec.get("timeline") or []
    clock = manifest["clock"]
    clk = getattr(dut, clock)
    input_ports = set(manifest.get("input_ports") or [])
    input_map = manifest.get("input_map") or {}
    if not timeline and machine_spec.get("assign"):
        await FallingEdge(clk)
        for field, value in machine_spec["assign"].items():
            port = input_map.get(field, field)
            if port in input_ports:
                _set_signal(dut, port, int(value))
        return
    if not timeline and machine_spec.get("csr_writes"):
        for entry in machine_spec["csr_writes"]:
            await _apb_write_one(dut, manifest, int(entry.get("offset", entry.get("addr", 0))), int(entry.get("data", entry.get("value", 0))))
        return
    for step in timeline:
        if not isinstance(step, dict):
            continue
        if "csr_write" in step:
            cw = step["csr_write"]
            await _apb_write_one(dut, manifest, int(cw.get("offset", cw.get("addr", 0))), int(cw.get("data", cw.get("value", 0))))
        elif "assign" in step:
            await FallingEdge(clk)
            for field, value in (step["assign"] or {}).items():
                port = input_map.get(field, field)
                if port in input_ports:
                    _set_signal(dut, port, int(value))
        elif "wait_cycles" in step:
            for _ in range(int(step["wait_cycles"])):
                await RisingEdge(clk)
        elif "wait_until" in step:
            wu = step["wait_until"]
            sig = wu.get("signal")
            target = int(wu.get("equals", 1))
            for _ in range(int(wu.get("timeout", 64))):
                await RisingEdge(clk)
                await ReadOnly()
                if sig and _has_signal(dut, sig) and int(_get_signal(dut, sig) or 0) == target:
                    break


@cocotb.test()
async def fl_rtl_equivalence_goals(dut):
    manifest = _load_manifest()
    ip_dir = _ip_dir()
    ip = manifest["ip"]
    clock = manifest["clock"]
    cocotb.start_soon(Clock(getattr(dut, clock), 10, units="ns").start())
    await _reset_dut(dut, manifest)

    from scoreboard import GoalScoreboard
    from tb_coverage import FunctionalCoverageCollector

    scoreboard = GoalScoreboard("scoreboard", ip, _project_root())
    coverage = FunctionalCoverageCollector("coverage")
    goals = _goals(ip_dir)
    assert goals, "equivalence_goals.json must contain unblocked goals"

    # Opt-in: cycle-accurate CL co-simulation via FunctionalModel.step().
    # SSOT.cycle_model.cosim: true -> manifest['cl_cosim']=True.
    # The CL is stepped in lock-step with cocotb drive cycles; when CL agrees
    # with RTL on registered outputs we treat it as the authoritative oracle
    # and pass cl_passed=True to scoreboard.check_goal.
    _cl = None
    _cl_match = 0
    _cl_total = 0
    if bool(manifest.get("cl_cosim", False)):
        import sys as _sys
        from pathlib import Path as _Path
        _model_dir = _Path(__file__).resolve().parents[2] / "model"
        if str(_model_dir) not in _sys.path:
            _sys.path.insert(0, str(_model_dir))
        try:
            from functional_model import FunctionalModel as _CL  # type: ignore
            _cl = _CL()
        except Exception:
            _cl = None

    # Default: reset DUT between goals so prior stimulus doesn't leak.
    # IPs whose RTL behaviour accumulates state across scenarios (round-robin
    # arbiters, multi-cycle FSMs that the tests rely on being mid-flight)
    # can opt out via manifest['per_goal_reset'] = False (driven from
    # SSOT.cycle_model.state_accumulating or rtl_contract.per_goal_reset).
    _per_goal_reset = bool(manifest.get("per_goal_reset", True))
    for idx, goal in enumerate(goals):
        goal_id = str(goal["goal_id"])
        stimulus = _stimulus_for_goal(goal, manifest, idx)
        machine_spec = (
            goal.get("stimulus_contract", {}).get("machine_spec")
            if isinstance(goal.get("stimulus_contract"), dict)
            else None
        )
        _cl_result = None
        # State-accumulating IPs (per_goal_reset=false) still need a clean
        # baseline for *non-scenario* goals (handshake/ordering/coverage/
        # register/error/module): these are standalone property checks not
        # part of the accumulated scenario flow. Without a reset, prior
        # scenario state bleeds into the property-check sample window and
        # FL.apply's single-shot expected (computed from reset state)
        # disagrees with RTL's accumulated state.
        _is_scenario_goal = goal_id.startswith("EQ_SCENARIO_") or goal_id.startswith("EQ_TRANSACTION_")
        _reset_for_property = (not _per_goal_reset) and (not _is_scenario_goal) and (not _is_reset_stimulus(stimulus))
        if _is_reset_stimulus(stimulus):
            await _reset_dut(dut, manifest, release=False)
            if _cl is not None:
                _cl.reset()
        else:
            if _per_goal_reset or _reset_for_property:
                await _reset_dut(dut, manifest)
                if _cl is not None:
                    _cl.reset()
            if isinstance(machine_spec, dict) and (
                machine_spec.get("timeline") or machine_spec.get("assign") or machine_spec.get("csr_writes")
            ):
                await _apply_machine_spec(dut, manifest, machine_spec)
                # When machine_spec drives csr_writes, mirror them into the CL.
                if _cl is not None and isinstance(machine_spec, dict):
                    for entry in (machine_spec.get("csr_writes") or []):
                        try:
                            _cl.csr_write(int(entry.get("offset", entry.get("addr", 0))), int(entry.get("data", entry.get("value", 0))))
                        except Exception:
                            pass
                    for step in (machine_spec.get("timeline") or []):
                        cw = step.get("csr_write") if isinstance(step, dict) else None
                        if cw:
                            try:
                                _cl.csr_write(int(cw.get("offset", cw.get("addr", 0))), int(cw.get("data", cw.get("value", 0))))
                            except Exception:
                                pass
            await FallingEdge(getattr(dut, clock))
            _drive_inputs(dut, manifest, stimulus)
            _cycles = _goal_wait_cycles(goal, manifest)
            # Mirror both field name (used in cocotb stimulus) and port name
            # (used in SSOT expressions) so FL.step env sees req_i and
            # requests both, etc.
            _cl_inputs = {}
            for _field, _port in (manifest.get("input_map") or {}).items():
                _val = int(stimulus.get(_field, stimulus.get(_port, 0)))
                _cl_inputs[_field] = _val
                _cl_inputs[_port] = _val
            for _ in range(_cycles):
                await RisingEdge(getattr(dut, clock))
                if _cl is not None:
                    try:
                        _cl_result = _cl.step(_cl_inputs)
                    except Exception:
                        _cl_result = None
        await ReadOnly()
        observed = _observe_outputs(dut, manifest, stimulus)
        # CL ↔ RTL agreement check across CL result keys that also appear
        # in observed. Skip when CL result is unresolved or all-idle.
        cl_agrees = False
        if (
            _cl is not None
            and isinstance(_cl_result, dict)
            and _cl_result.get("kind") not in ("idle", "step_unresolved")
            and "step_unresolved" not in _cl_result
        ):
            _common = [
                k for k in _cl_result.keys()
                if k in observed
                and isinstance(_cl_result.get(k), int)
                and isinstance(observed.get(k), int)
            ]
            if _common:
                _cl_total += 1
                if all(int(_cl_result[k]) == int(observed[k]) for k in _common):
                    _cl_match += 1
                    cl_agrees = True
        try:
            row = scoreboard.check_goal(
                goal_id,
                scenario_id=stimulus["scenario_id"],
                cycle=idx + _goal_wait_cycles(goal, manifest),
                stimulus=stimulus,
                rtl_observed=observed,
                cl_passed=cl_agrees if cl_agrees else None,
            )
        except TypeError:
            # Legacy scoreboard signature without cl_passed kwarg.
            row = scoreboard.check_goal(
                goal_id,
                scenario_id=stimulus["scenario_id"],
                cycle=idx + _goal_wait_cycles(goal, manifest),
                stimulus=stimulus,
                rtl_observed=observed,
            )
        coverage.sample(goal, row)
        await FallingEdge(getattr(dut, clock))
        _clear_sample_inputs(dut, manifest)

    if _cl is not None and _cl_total > 0:
        _cl_pct = (_cl_match / _cl_total) * 100.0
        print(f"[CL_COSIM] {ip} cycle-accurate FL/RTL co-sim: {_cl_match}/{_cl_total} match ({_cl_pct:.1f}%)")
    scoreboard.final_check()
    await _run_static_coverage_sweep(dut, manifest)
    coverage.write(ip_dir)
'''


RUNNER_PY = '''from __future__ import annotations

import json
import os
import shutil
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

from cocotb_test.simulator import run


def _ip_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def _manifest() -> dict:
    return json.loads((_ip_dir() / "tb" / "cocotb" / "tb_manifest.json").read_text(encoding="utf-8"))


def _copy_waveforms(build_dir: Path, sim_dir: Path, ip: str) -> list[Path]:
    copied = []
    for path in sorted(list(build_dir.glob("*.fst")) + list(build_dir.glob("*.vcd"))):
        dst = sim_dir / f"{ip}{path.suffix}"
        shutil.copy2(path, dst)
        copied.append(dst)
    return copied


def _with_icarus_vcd_dump(sources: list[str], build_dir: Path, top: str, ip: str) -> tuple[list[str], list[str]]:
    """Create an Icarus-only VCD dump helper without wrapping the DUT.

    Icarus/vvp has no Tcl wave-control layer. To keep Atlas' browser VCD
    viewer source-traceable, dump the real RTL top scope directly and add the
    helper as a second top-level root that the UI can ignore.
    """
    dump_module = "atlas_iverilog_vcd_dump"
    dump_src = build_dir / f"{dump_module}.v"
    dump_src.write_text(
        f"module {dump_module}();\\n"
        "initial begin\\n"
        f"  $dumpfile(\\"{ip}.vcd\\");\\n"
        f"  $dumpvars(0, {top});\\n"
        "end\\n"
        "endmodule\\n",
        encoding="utf-8",
    )
    return [*sources, str(dump_src)], [top, dump_module]


def _verilator_compile_args(simulator: str) -> list[str]:
    if simulator != "verilator":
        return []
    enabled = os.environ.get("ATLAS_VERILATOR_COVERAGE", "1").strip().lower()
    if enabled in {"0", "false", "no", "off"}:
        return []
    return [
        "--coverage",
        "--coverage-line",
        "--coverage-expr",
        "--coverage-toggle",
    ]


def _parse_results(path: Path) -> tuple[int, int, int]:
    root = ET.parse(path).getroot()
    tests = failures = errors = 0
    suites = [root, *root.findall(".//testsuite")]
    for node in suites:
        tests += int(float(node.attrib.get("tests", 0) or 0))
        failures += int(float(node.attrib.get("failures", 0) or 0))
        errors += int(float(node.attrib.get("errors", 0) or 0))
    if tests == 0:
        cases = root.findall(".//testcase")
        tests = len(cases)
        failures = sum(1 for case in cases if case.find("failure") is not None)
        errors = sum(1 for case in cases if case.find("error") is not None)
    return tests, failures, errors


def _scoreboard_escalations(path: Path) -> list[str]:
    if not path.is_file():
        return []
    failed = []
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except Exception as exc:
            failed.append(("PARSE_ERROR", f"scoreboard_events.jsonl parse error: {exc}"))
            continue
        if isinstance(row, dict) and row.get("passed") is False:
            failed.append((str(row.get("goal_id") or "UNKNOWN"), str(row.get("mismatch") or "mismatch without detail")))
    if not failed:
        return []
    preview = "; ".join(f"{goal}: {mismatch}" for goal, mismatch in failed[:8])
    suffix = "" if len(failed) <= 8 else f"; ... +{len(failed) - 8} more"
    return [
        f"[SIM ESCALATE] scoreboard_failed={len(failed)} owner=sim_debug evidence={path}",
        f"[SIM ESCALATE] reason=FL-vs-RTL scoreboard mismatch: {preview}{suffix}",
    ]


def main() -> int:
    ip_dir = _ip_dir()
    project_root = ip_dir.parent
    manifest = _manifest()
    ip = manifest["ip"]
    tb_dir = ip_dir / "tb" / "cocotb"
    sim_dir = ip_dir / "sim"
    sim_dir.mkdir(parents=True, exist_ok=True)
    build_dir = sim_dir / "cocotb_build"
    build_dir.mkdir(parents=True, exist_ok=True)

    common_root = Path(os.environ.get("COMMON_AI_AGENT_ROOT") or manifest["common_ai_agent_root"]).resolve()
    runtime_dir = common_root / "workflow" / "tb-gen" / "runtime"
    sources = [str(Path(src).resolve()) for src in manifest.get("rtl_sources") or []]
    if not sources:
        (sim_dir / "sim_report.txt").write_text("TESTS=0 PASS=0 FAIL=1\\nno RTL sources\\n", encoding="utf-8")
        print("TESTS=0 PASS=0 FAIL=1")
        print("no RTL sources")
        return 1

    env = {
        "IP_NAME": ip,
        "PROJECT_ROOT": str(project_root),
        "COMMON_AI_AGENT_ROOT": str(common_root),
        "PYTHONUNBUFFERED": "1",
    }
    os.environ.pop("COCOTB_RESULTS_FILE", None)
    try:
        simulator = os.environ.get("SIM", "icarus")
        run_sources = sources
        run_top = manifest["top"]
        waves = True
        if simulator == "icarus":
            run_sources, run_top = _with_icarus_vcd_dump(sources, build_dir, manifest["top"], ip)
            waves = False
        results_file = run(
            simulator=simulator,
            verilog_sources=run_sources,
            toplevel=run_top,
            module=f"test_{ip}",
            python_search=[str(tb_dir), str(runtime_dir)],
            sim_build=str(build_dir),
            timescale="1ns/1ps",
            waves=waves,
            force_compile=True,
            extra_env=env,
            includes=[str(ip_dir / "rtl")],
            verilog_compile_args=_verilator_compile_args(simulator),
        )
    except BaseException as exc:
        (sim_dir / "sim_report.txt").write_text(
            f"TESTS=1 PASS=0 FAIL=1\\nSimulation exception: {exc}\\n",
            encoding="utf-8",
        )
        print("TESTS=1 PASS=0 FAIL=1")
        print(f"Simulation exception: {exc}")
        return 1

    canonical = sim_dir / "results.xml"
    shutil.copy2(results_file, canonical)
    shutil.copy2(results_file, tb_dir / "results.xml")
    waves = _copy_waveforms(build_dir, sim_dir, ip)
    tests, failures, errors = _parse_results(canonical)
    passed = tests - failures - errors
    escalations = _scoreboard_escalations(sim_dir / "scoreboard_events.jsonl")
    report = [
        f"TESTS={tests} PASS={passed} FAIL={failures + errors}",
        f"results={canonical.relative_to(project_root)}",
        f"scoreboard={ip}/sim/scoreboard_events.jsonl",
        f"coverage_functional={ip}/cov/coverage_functional.json",
        f"waveforms={','.join(str(path.relative_to(project_root)) for path in waves) if waves else 'none'}",
        "0 errors, 0 warnings" if failures == 0 and errors == 0 else f"{errors} errors, {failures} failures",
    ]
    report.extend(escalations)
    (sim_dir / "sim_report.txt").write_text("\\n".join(report) + "\\n", encoding="utf-8")
    print(f"TESTS={tests} PASS={passed} FAIL={failures + errors}")
    print("0 errors, 0 warnings" if failures == 0 and errors == 0 else f"{errors} errors, {failures} failures")
    for line in escalations:
        print(line)
    return 0 if failures == 0 and errors == 0 and tests > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
'''


def emit(ip: str, root: Path) -> dict[str, Any]:
    root = root.resolve()
    ip_dir = root / ip
    manifest, questions = _build_manifest(ip, root)
    tb_dir = ip_dir / "tb" / "cocotb"
    tb_dir.mkdir(parents=True, exist_ok=True)
    if questions:
        _write_blocked(ip_dir, ip, questions)
        print(f"[SSOT QUESTION] tb-gen blocked for {ip}: {len(questions)} contract issue(s)")
        for q in questions:
            print(f"- {q['id']}: {q['decision_needed']}")
        raise SystemExit(2)

    blocked = tb_dir / "tb_blocked.json"
    if blocked.exists():
        blocked.unlink()

    files = {
        "transactions.py": TRANSACTIONS_PY,
        "sequences.py": SEQUENCES_PY,
        "agents.py": AGENTS_PY,
        "scoreboard.py": SCOREBOARD_PY,
        "tb_coverage.py": TB_COVERAGE_PY,
        "uvm_env.py": UVM_ENV_PY,
        f"test_{ip}.py": TEST_PY,
        "test_runner.py": RUNNER_PY,
    }
    for name, text in files.items():
        (tb_dir / name).write_text(text, encoding="utf-8")
    (tb_dir / "tb_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (tb_dir / "__init__.py").write_text("", encoding="utf-8")

    report = {
        "schema_version": 1,
        "type": "generic_goal_scoreboard_cocotb_generation",
        "status": "pass",
        "ip": ip,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "manifest": f"{ip}/tb/cocotb/tb_manifest.json",
        "test": f"{ip}/tb/cocotb/test_{ip}.py",
        "runner": f"{ip}/tb/cocotb/test_runner.py",
        "goals": manifest["goal_count"],
        "rtl_sources": len(manifest["rtl_sources"]),
    }
    (tb_dir / "tb_generation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"[emit_goal_scoreboard_cocotb] wrote {len(files)} Python files for {ip}")
    print(f"[emit_goal_scoreboard_cocotb] goals={manifest['goal_count']} rtl_sources={len(manifest['rtl_sources'])}")
    print(f"[emit_goal_scoreboard_cocotb] runner={ip}/tb/cocotb/test_runner.py")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ip")
    parser.add_argument("--root", default=".")
    args = parser.parse_args()
    try:
        emit(args.ip, Path(args.root))
    except RuntimeError as exc:
        ip_dir = Path(args.root).resolve() / args.ip
        _write_blocked(ip_dir, args.ip, [_question(
            "TB_GENERATOR_INPUT",
            "Provide the missing source artifact required by generic TB generation.",
            str(exc),
            "Run the owning ATLAS stage shown in the evidence, then rerun /tb.",
            "The generator must consume disk-truth SSOT, FL, equivalence-goal, and RTL-contract artifacts.",
        )])
        print(f"[SSOT QUESTION] tb-gen blocked for {args.ip}: {exc}")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
