#!/usr/bin/env python3
"""Write a generic SSOT draft from approved ATLAS Web Q&A state.

This is a workflow bridge, not an RTL generator and not an IP-specific
template. It converts the human-approved Web Q&A ledger into the canonical
33-section SSOT shape so downstream LLM workflows can operate from disk truth
instead of a long chat transcript. Unsupported or ambiguous details are
recorded as assumptions in the SSOT; implementation remains owned by rtl-gen,
tb-gen, sim_debug, and EDA workflows.
"""

from __future__ import annotations

import argparse
import ast
import json
import keyword
import re
import time
from pathlib import Path
from typing import Any

import yaml


REQUIRED_ORDER = [
    "top_module",
    "sub_modules",
    "parameters",
    "io_list",
    "features",
    "dataflow",
    "function_model",
    "cycle_model",
    "clock_reset_domains",
    "cdc_requirements",
    "rdc_requirements",
    "registers",
    "memory",
    "interrupts",
    "fsm",
    "timing",
    "power",
    "security",
    "error_handling",
    "debug_observability",
    "integration",
    "dft",
    "synthesis",
    "pnr",
    "coding_rules",
    "reuse_modules",
    "custom",
    "dir_structure",
    "filelist",
    "rtl_contract",
    "test_requirements",
    "quality_gates",
    "traceability",
    "workflow_todos",
    "generation_flow",
]


def _load_state(root: Path, ip: str) -> dict[str, Any]:
    path = root / ".session" / ip / "ssot-gen" / "state.json"
    if not path.is_file():
        session_root = root / ".session"
        if session_root.is_dir():
            for owner_dir in session_root.iterdir():
                if owner_dir.is_dir():
                    candidate = owner_dir / ip / "ssot-gen" / "state.json"
                    if candidate.is_file():
                        path = candidate
                        break
        if not path.is_file():
            raise SystemExit(f"[approved_to_ssot] missing approved state: {path}")
    doc = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict) or not doc.get("approved"):
        raise SystemExit(f"[approved_to_ssot] {ip} is not approved")
    ssot_path = root / ip / "yaml" / f"{ip}.ssot.yaml"
    if ssot_path.is_file():
        ssot_doc = yaml.safe_load(ssot_path.read_text(encoding="utf-8", errors="replace")) or {}
        if isinstance(ssot_doc, dict):
            custom = ssot_doc.get("custom") if isinstance(ssot_doc.get("custom"), dict) else {}
            decisions = custom.get("atlas_decisions") if isinstance(custom.get("atlas_decisions"), dict) else {}
            if decisions:
                doc["_ssot_decisions"] = decisions
            if custom:
                doc["_ssot_custom"] = custom
    return doc


def _decisions(state: dict[str, Any]) -> dict[str, str]:
    raw = state.get("_ssot_decisions") if isinstance(state.get("_ssot_decisions"), dict) else {}
    if not raw:
        raw = state.get("decisions") if isinstance(state.get("decisions"), dict) else {}
    return {str(k): str(v).strip() for k, v in raw.items() if str(v or "").strip()}


def _ssot_custom(state: dict[str, Any]) -> dict[str, Any]:
    custom = state.get("_ssot_custom") if isinstance(state.get("_ssot_custom"), dict) else {}
    return custom if isinstance(custom, dict) else {}


def _safe_markdown_text(value: Any) -> str:
    """Keep generated requirement markdown audit-clean without hiding approved facts."""
    text = str(value or "").strip()
    replacements = {
        "TBD": "open-decision marker",
        "TODO": "open-action marker",
        "FIXME": "fix-required marker",
        "PLACEHOLDER": "draft-marker",
        "placeholder": "draft-marker",
        "stub": "draft shell",
        "mock": "test double",
    }
    for old, new in replacements.items():
        text = re.sub(rf"\b{re.escape(old)}\b", new, text, flags=re.IGNORECASE)
    return text


def _write_requirements(root: Path, ip: str, state: dict[str, Any], doc: dict[str, Any]) -> Path:
    decisions = _decisions(state)
    req_dir = root / ip / "req"
    req_dir.mkdir(parents=True, exist_ok=True)
    out = req_dir / f"{ip}_requirements.md"

    top = doc.get("top_module") if isinstance(doc.get("top_module"), dict) else {}
    fm = doc.get("function_model") if isinstance(doc.get("function_model"), dict) else {}
    cm = doc.get("cycle_model") if isinstance(doc.get("cycle_model"), dict) else {}
    tr = doc.get("test_requirements") if isinstance(doc.get("test_requirements"), dict) else {}
    scenarios = tr.get("scenarios") if isinstance(tr.get("scenarios"), list) else []
    submods = doc.get("sub_modules") if isinstance(doc.get("sub_modules"), list) else []
    ios = doc.get("io_list") if isinstance(doc.get("io_list"), list) else []

    lines: list[str] = [
        f"# {ip} Requirements Ledger",
        "",
        f"- Source: human-approved ATLAS Web Q&A state captured for `{ip}`.",
        "- Authority: this file records requirement intent; the YAML SSOT remains the machine-readable source for downstream FL, RTL, DV, lint, simulation, and coverage stages.",
        f"- IP kind: {_safe_markdown_text(state.get('kind') or top.get('type') or 'leaf IP')}.",
        f"- Generated: {time.strftime('%Y-%m-%dT%H:%M:%S')}.",
        "",
        "## Approved Requirement Decisions",
    ]
    if decisions:
        for key in sorted(decisions):
            lines.append(f"- `{key}`: {_safe_markdown_text(decisions[key])}")
    else:
        lines.append("- No free-form decision rows were captured; SSOT generation used the approved IP kind and default review gates.")

    lines.extend([
        "",
        "## Behavioral Contract",
        f"- Top module `{ip}` must implement the approved function model and cycle model exactly as represented in `{ip}/yaml/{ip}.ssot.yaml`.",
        f"- Function model operations: {_safe_markdown_text(fm.get('description') or top.get('description') or 'approved transaction behavior')}.",
        f"- Cycle model obligation: {_safe_markdown_text(cm.get('description') or 'latency, sampling, and output timing are defined by the SSOT cycle model')}.",
        "- Any feature, port, state update, bus behavior, interrupt, memory, or coverage goal absent from the SSOT is outside this revision and requires a new approved requirement entry before implementation.",
        "- RTL generation, test generation, sim-debug, and coverage are expected to read the SSOT and must not infer hidden behavior from chat history.",
        "",
        "## Interface And Decomposition",
    ])
    for port in ios:
        if isinstance(port, dict):
            lines.append(
                f"- Port `{_safe_markdown_text(port.get('name'))}`: direction={_safe_markdown_text(port.get('direction'))}, "
                f"width={_safe_markdown_text(port.get('width'))}, role={_safe_markdown_text(port.get('description'))}."
            )
    if submods:
        lines.append("")
        lines.append("## Decomposition Units")
        for mod in submods:
            if isinstance(mod, dict):
                lines.append(
                    f"- `{_safe_markdown_text(mod.get('name'))}` owns {_safe_markdown_text(mod.get('description') or mod.get('responsibility') or 'an SSOT-defined function slice')}."
                )

    lines.extend([
        "",
        "## Verification And Coverage Intent",
        "- Verification must prove FL-vs-RTL equivalence for every SSOT goal before final signoff.",
        "- Functional coverage is the primary closure metric for this flow; structural metrics are required only when the SSOT explicitly requests tool evidence for them.",
        "- DUT-only lint must pass before simulation evidence can be used for signoff.",
    ])
    for idx, scenario in enumerate(scenarios, start=1):
        if isinstance(scenario, dict):
            lines.append(
                f"- Scenario {idx} `{_safe_markdown_text(scenario.get('id') or scenario.get('name') or idx)}`: "
                f"{_safe_markdown_text(scenario.get('description') or scenario.get('stimulus') or scenario)}"
            )

    lines.extend([
        "",
        "## Acceptance Criteria",
        f"- `{ip}/yaml/{ip}.ssot.yaml` parses and contains the functional model, cycle model, RTL contract, test requirements, quality gates, traceability, and downstream workflow action ledger.",
        "- Generated RTL implements only SSOT-approved behavior and passes DUT-only lint with zero errors.",
        "- Generated cocotb/pyuvm tests execute scoreboard comparisons against the functional model.",
        "- Simulation produces machine-readable pass evidence, FL-vs-RTL comparison evidence, and coverage evidence.",
        "- Final goal audit passes with fresh artifacts for requirements, SSOT, FL model, RTL, lint, DV, simulation, coverage, and equivalence.",
        "",
    ])
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def _all_text(ip: str, state: dict[str, Any]) -> str:
    decisions = _decisions(state)
    return " ".join([ip, str(state.get("kind") or ""), *decisions.values()]).lower()


def _mentions_without_local_negation(text: str, pattern: str, *, lookback: int = 80) -> bool:
    """Match a protocol/feature token unless the local phrase negates it."""
    low = (text or "").lower()
    for match in re.finditer(pattern, low, re.IGNORECASE):
        prefix = low[max(0, match.start() - lookback) : match.start()]
        prefix = re.split(r"[.;,\n]", prefix)[-1]
        if re.search(r"\b(no|none|without|not|non|n/a|not applicable)\b", prefix):
            continue
        return True
    return False


def _infer_ip_type(ip: str, state: dict[str, Any]) -> str:
    text = _all_text(ip, state)
    ip_low = (ip or "").lower()
    bus_ip_name = bool(re.search(r"(^|_)(bus|fabric|interconnect|crossbar|bridge|gateway|router|arbiter)($|_)", ip_low))
    bus_arch_intent = (
        any(k in text for k in ("interconnect", "crossbar", "bus fabric", "bus bridge", "system bus", "memory bus"))
        or re.search(r"\bbridge\s*/\s*fabric\b", text)
        or re.search(r"\b(address\s+decode|address\s+decoder|route[sd]?|routing|arbiter|bus\s+gateway)\b", text)
    )
    if bus_ip_name or bus_arch_intent:
        return "bus"
    if _mentions_without_local_negation(text, r"\bdma\b"):
        return "dma"
    serial_peripheral_name = bool(re.search(r"(^|_)(qspi|quad_spi|spi|smbus|i2c|i3c|uart|gpio|pwm|timer)($|_)", ip_low))
    serial_peripheral_intent = (
        _mentions_without_local_negation(text, r"\b(qspi|quad\s+spi|spi|smbus|i2c|i3c|uart|gpio|pwm|timer)\b")
        and _mentions_without_local_negation(text, r"\b(controller|peripheral|slave|master|flash|serial)\b")
    )
    if serial_peripheral_name or serial_peripheral_intent:
        return "peripheral"
    isa_intent = (
        any(
            _mentions_without_local_negation(text, pat)
            for pat in (
                r"\bcpu\b",
                r"\brisc[- ]?v\b",
                r"\brv32\b",
                r"\bprocessor\b",
                r"\bcpu\s+core\b",
                r"\bprocessor\s+core\b",
                r"\bcore\s+pipeline\b",
            )
        )
        or re.search(r"\b(armv[0-9a-z-]*|cortex[- ]?m|thumb|isa)\b", text, re.IGNORECASE)
        or (
            "instruction" in text
            and any(k in text for k in ("decode", "decoded", "execute", "alu", "branch", "pc_next", "next-pc", "register write"))
        )
    )
    if isa_intent:
        return "cpu"
    if (
        _mentions_without_local_negation(text, r"\b(sram|fifo|memory|ram)\b")
        and "monitor" not in text
    ):
        return "memory"
    if any(k in text for k in ("accelerator", "compute", "crypto", "filter", "codec")):
        return "accelerator"
    return "peripheral"


def _parse_number(value: str) -> Any:
    value = value.strip().rstrip(".")
    if re.fullmatch(r"0x[0-9a-fA-F_]+", value):
        return int(value.replace("_", ""), 16)
    if re.fullmatch(r"\d+", value):
        return int(value)
    return value


def _parse_parameters(text: str) -> list[dict[str, Any]]:
    params: list[dict[str, Any]] = []
    seen: set[str] = set()
    for name, value in re.findall(r"\b([A-Z][A-Z0-9_]{1,})\s*=\s*([^,;.\s]+(?:/[0-9]+)?)", text or ""):
        if name in seen:
            continue
        seen.add(name)
        params.append(
            {
                "name": name,
                "default": _parse_number(value),
                "type": "int" if re.match(r"^(0x[0-9a-fA-F_]+|\d+|[A-Z0-9_]+/[0-9]+)$", value) else "param",
                "description": f"Approved parameter from Web Q&A: {name}={value}",
                "drives": ["rtl", "tb", "coverage"],
            }
        )
    for name, default, desc in [
        ("DATA_WIDTH", 32, "Primary data path width in bits"),
        ("ADDR_WIDTH", 8, "Local address width for control/register addressing"),
    ]:
        if name not in seen:
            params.append(
                {
                    "name": name,
                    "default": default,
                    "type": "int",
                    "description": desc,
                    "drives": ["rtl", "tb"],
                }
            )
            seen.add(name)
    return params


def _param_default(params: list[dict[str, Any]], name: str, fallback: Any) -> Any:
    for item in params:
        if item.get("name") == name:
            return item.get("default", fallback)
    return fallback


def _clock_reset(decisions: dict[str, str], top_freq: int = 100) -> tuple[str, int, str, str, str]:
    text = decisions.get("clock_reset", "")
    freq = top_freq
    m = re.search(r"(\d+)\s*mhz", text, re.IGNORECASE)
    if m:
        freq = int(m.group(1))
    clk = "clk"
    clock_tokens = re.findall(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\b", text)
    for cand in clock_tokens:
        low = cand.lower()
        if low in {"aclk", "pclk", "hclk", "clk"} or (low.endswith("clk") and low != "clock"):
            clk = cand
            break
    rst = "rst_n" if re.search(r"rst_n|resetn|aresetn|active[- ]low", text, re.IGNORECASE) else "rst"
    m = re.search(r"\b(rst_n|aresetn|presetn|resetn)\b", text, re.IGNORECASE)
    if not m:
        m = re.search(r"\b(rst|reset)\b", text, re.IGNORECASE)
    if m:
        rst = m.group(1)
    polarity = "active_low" if re.search(r"active[- ]low|rst_n|resetn|aresetn", text, re.IGNORECASE) else "active_high"
    sync = "async_assert_sync_deassert" if re.search(r"async|asynchronous", text, re.IGNORECASE) else "sync"
    return clk, freq, rst, polarity, sync


def _port(name: str, width: Any, direction: str, description: str) -> dict[str, Any]:
    return {"name": name, "width": width, "direction": direction, "description": description}


def _apb_ports(addr_width: Any, data_width: Any) -> list[dict[str, Any]]:
    pstrb_width = data_width // 8 if isinstance(data_width, int) and data_width > 0 else f"{data_width}/8"
    return [
        _port("paddr", addr_width, "input", "APB address"),
        _port("psel", 1, "input", "APB select"),
        _port("penable", 1, "input", "APB enable/access phase"),
        _port("pwrite", 1, "input", "APB write enable"),
        _port("pwdata", data_width, "input", "APB write data"),
        _port("pstrb", pstrb_width, "input", "APB byte strobes"),
        _port("prdata", data_width, "output", "APB read data"),
        _port("pready", 1, "output", "APB ready"),
        _port("pslverr", 1, "output", "APB slave error"),
    ]


def _axi_lite_ports(addr_width: Any, data_width: Any) -> list[dict[str, Any]]:
    return [
        _port("s_axi_awaddr", addr_width, "input", "AXI4-Lite write address"),
        _port("s_axi_awvalid", 1, "input", "AXI4-Lite write address valid"),
        _port("s_axi_awready", 1, "output", "AXI4-Lite write address ready"),
        _port("s_axi_wdata", data_width, "input", "AXI4-Lite write data"),
        _port("s_axi_wstrb", f"{data_width}/8", "input", "AXI4-Lite write strobes"),
        _port("s_axi_wvalid", 1, "input", "AXI4-Lite write data valid"),
        _port("s_axi_wready", 1, "output", "AXI4-Lite write data ready"),
        _port("s_axi_bresp", 2, "output", "AXI4-Lite write response"),
        _port("s_axi_bvalid", 1, "output", "AXI4-Lite write response valid"),
        _port("s_axi_bready", 1, "input", "AXI4-Lite write response ready"),
        _port("s_axi_araddr", addr_width, "input", "AXI4-Lite read address"),
        _port("s_axi_arvalid", 1, "input", "AXI4-Lite read address valid"),
        _port("s_axi_arready", 1, "output", "AXI4-Lite read address ready"),
        _port("s_axi_rdata", data_width, "output", "AXI4-Lite read data"),
        _port("s_axi_rresp", 2, "output", "AXI4-Lite read response"),
        _port("s_axi_rvalid", 1, "output", "AXI4-Lite read data valid"),
        _port("s_axi_rready", 1, "input", "AXI4-Lite read data ready"),
    ]


def _axis_ports(data_width: Any, keep_width: Any) -> list[dict[str, Any]]:
    return [
        _port("s_axis_tdata", data_width, "input", "AXI4-Stream payload data"),
        _port("s_axis_tkeep", keep_width, "input", "AXI4-Stream byte-valid mask"),
        _port("s_axis_tvalid", 1, "input", "AXI4-Stream input valid"),
        _port("s_axis_tready", 1, "output", "AXI4-Stream input ready/backpressure"),
        _port("s_axis_tlast", 1, "input", "AXI4-Stream packet boundary"),
    ]


def _rule_expr_names(expr: Any) -> set[str]:
    names = set(re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", str(expr or "")))
    return {
        name
        for name in names
        if name not in {"true", "false", "True", "False"}
        and not keyword.iskeyword(name)
    }


def _signal_width(name: str, params: list[dict[str, Any]]) -> Any:
    low = name.lower()
    bool_exact = {
        "valid",
        "ready",
        "result_valid",
        "packet_ok",
        "ack",
        "nack",
        "irq",
        "we",
        "rw",
        "read",
        "write",
        "broadcast",
        "accept",
        "reject",
        "miss",
        "sck",
        "cs",
        "cs_n",
        "sck_phase",
        "done",
        "busy",
        "error",
        "axi_error",
        "manager_go",
        "op_is_load",
        "op_is_store",
        "nonsecure_access",
        "target_secure",
        "terminal_instr",
        "undefined_instr",
        "invalid_operand",
        "watchdog_timeout",
        "halted",
        "transfer_done",
    }
    bool_suffixes = (
        "_valid",
        "_ready",
        "_we",
        "_read",
        "_write",
        "_enable",
        "_irq",
        "_pending",
        "_error",
        "_unsupported",
        "_illegal",
        "_violation",
        "_timeout",
        "_done",
        "_halted",
        "_hit",
        "_ok",
        "_req",
        "_seen",
        "_flag",
        "_active",
        "_rise",
        "_fall",
        "_sample",
        "_launch",
    )
    if (
        re.search(r"(^|_)(dq|io|lane)s?($|_)", low)
        or "nibble" in low
        or low.startswith(("dq_", "qspi_dq", "spi_dq"))
        or low in {"dq_i", "dq_o", "dq_oe", "dq_i_rise", "dq_i_fall", "dq_o_rise", "dq_o_fall"}
    ):
        return _param_default(params, "DQ_WIDTH", _param_default(params, "IO_WIDTH", 4))
    if (
        low in bool_exact
        or low.startswith(("is_", "has_", "illegal_", "unsupported_", "enable_", "disable_"))
        or low.endswith(bool_suffixes)
        or low.endswith(("valid", "ready"))
    ):
        return 1
    if low in {"resp", "response", "resp_code", "response_code"} or low.endswith("_code"):
        return _param_default(params, "RESP_WIDTH", _param_default(params, "STATUS_WIDTH", 2))
    if "addr" in low:
        return _param_default(params, "ADDR_WIDTH", 7)
    if "command" in low or low in {"cmd", "op", "opcode"}:
        return _param_default(params, "COMMAND_WIDTH", 8)
    if "pec" in low or "crc" in low:
        return _param_default(params, "PEC_WIDTH", 8)
    if "count" in low:
        return _param_default(params, "COUNT_WIDTH", 16)
    return _param_default(params, "DATA_WIDTH", 32)


def _validate_rule_expr(expr: str, *, context: str) -> None:
    try:
        ast.parse(_normal_machine_expr(expr), mode="eval")
    except Exception as exc:
        raise SystemExit(f"[approved_to_ssot] invalid machine_rules expression for {context}: {expr!r}: {exc}")


def _normal_machine_expr(expr: Any) -> str:
    return str(expr or "").strip().strip(".")


def _machine_rule_chunks(decisions: dict[str, str]) -> list[str]:
    chunks: list[str] = []
    for value in decisions.values():
        text = str(value or "")
        for match in re.finditer(r"\b(?:machine_rules?|rtl_rules?|ssot_rules?)\s*:\s*", text, re.IGNORECASE):
            chunks.append(text[match.end() :])
    return chunks


def _machine_rules(decisions: dict[str, str], params: list[dict[str, Any]]) -> dict[str, Any]:
    """Parse explicit machine-checkable rules from approved Q&A text.

    This keeps the deterministic bridge generic: it does not invent IP
    behavior from an IP name. The human/LLM-approved Q&A can provide a compact
    rule ledger such as:
      machine_rules: sample_condition=valid; output result=data_in ^ command; state accepted_count=accepted_count+1
    """
    chunks = _machine_rule_chunks(decisions)
    if not chunks:
        return {}
    sample_condition = "valid"
    output_rules_by_name: dict[str, dict[str, Any]] = {}
    state_updates_by_name: dict[str, dict[str, Any]] = {}
    for raw in re.split(r";|\n", "\n".join(chunks)):
        item = raw.strip(" .")
        if not item:
            continue
        sample = re.match(r"(?:sample_condition|sample|when)\s*=\s*(.+)", item, re.IGNORECASE)
        if sample:
            sample_condition = _normal_machine_expr(sample.group(1))
            _validate_rule_expr(sample_condition, context="sample_condition")
            continue
        out = re.match(r"(?:output|out)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.+)", item, re.IGNORECASE)
        if out:
            name, expr = out.groups()
            expr = _normal_machine_expr(expr)
            _validate_rule_expr(expr, context=f"output {name}")
            output_rules_by_name.setdefault(name, {
                "name": name,
                "expr": expr,
                "width": _signal_width(name, params),
                "port": name,
                "description": f"Machine-checkable output rule approved in ATLAS Q&A: {name}={expr}",
            })
            continue
        state = re.match(r"(?:state|update)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.+)", item, re.IGNORECASE)
        if state:
            name, expr = state.groups()
            expr = _normal_machine_expr(expr)
            _validate_rule_expr(expr, context=f"state {name}")
            state_updates_by_name.setdefault(name, {
                "name": name,
                "expr": expr,
                "width": _signal_width(name, params),
                "reset": 0,
                "description": f"Machine-checkable state update approved in ATLAS Q&A: {name}={expr}",
            })
    if not output_rules_by_name and not state_updates_by_name:
        return {}
    return {
        "sample_condition": sample_condition,
        "output_rules": list(output_rules_by_name.values()),
        "state_updates": list(state_updates_by_name.values()),
    }


def _machine_input_names(machine: dict[str, Any], params: list[dict[str, Any]]) -> list[str]:
    if not machine:
        return []
    param_names = {str(item.get("name")) for item in params if isinstance(item, dict) and item.get("name")}
    output_names = {str(item.get("name")) for item in machine.get("output_rules") or [] if isinstance(item, dict)}
    state_names = {str(item.get("name")) for item in machine.get("state_updates") or [] if isinstance(item, dict)}
    names = _rule_expr_names(machine.get("sample_condition"))
    for item in (machine.get("output_rules") or []) + (machine.get("state_updates") or []):
        if isinstance(item, dict):
            names |= _rule_expr_names(item.get("expr"))
    names -= param_names
    names -= output_names
    names -= state_names
    names -= {"accepted_count", "busy", "error"}
    return sorted(names)


def _valid_ready_ports(
    data_width: Any,
    count_width: Any,
    params: list[dict[str, Any]],
    extra_inputs: list[str] | None = None,
    extra_outputs: list[str] | None = None,
) -> list[dict[str, Any]]:
    explicit_inputs = set(extra_inputs or [])
    explicit_outputs = set(extra_outputs or [])
    fallback_defaults = not explicit_inputs and not explicit_outputs
    ports: list[dict[str, Any]] = []
    if fallback_defaults or "valid" in explicit_inputs:
        ports.append(_port("valid", 1, "input", "Input transaction valid"))
    ports.append(_port("ready", 1, "output", "Input transaction ready"))
    if fallback_defaults or "data_in" in explicit_inputs:
        ports.append(_port("data_in", data_width, "input", "Input transaction payload"))
    if fallback_defaults or "result" in explicit_outputs:
        ports.append(_port("result", data_width, "output", "Primary result observable"))
    if fallback_defaults or "result_valid" in explicit_outputs:
        ports.append(_port("result_valid", 1, "output", "Result valid pulse"))
    ports.append(_port("accepted_count", count_width, "output", "Accepted transaction count"))
    existing = {p["name"] for p in ports}
    for name in extra_inputs or []:
        if name not in existing:
            ports.append(_port(name, _signal_width(name, params), "input", f"Approved transaction input field: {name}"))
            existing.add(name)
    for name in extra_outputs or []:
        if name not in existing:
            ports.append(_port(name, _signal_width(name, params), "output", f"Approved transaction output observable: {name}"))
            existing.add(name)
    return ports


def _needs_valid_ready_interface(text: str) -> bool:
    low = (text or "").lower()
    return (
        ("valid" in low and "ready" in low)
        or "valid-ready" in low
        or "valid ready" in low
        or "data_in" in low
        or "result_valid" in low
        or "accepted_count" in low
    )


def _valid_ready_sample_condition(sample: Any, text: str) -> str:
    sample_s = str(sample or "valid").strip() or "valid"
    low = sample_s.lower()
    if _needs_valid_ready_interface(text) and not any(
        token in low for token in ("ready", "accept", "pready", "penable")
    ):
        return f"({sample_s}) and ready"
    return sample_s


def _interfaces(ip: str, state: dict[str, Any], params: list[dict[str, Any]], machine: dict[str, Any] | None = None) -> dict[str, Any]:
    decisions = _decisions(state)
    text = _all_text(ip, state)
    clk, freq, rst, polarity, sync = _clock_reset(decisions)
    data_width = _param_default(params, "DATA_WIDTH", 32)
    count_width = _param_default(params, "COUNT_WIDTH", 16)
    addr_width = _param_default(params, "APB_ADDR_WIDTH", _param_default(params, "ADDR_WIDTH", 8))
    keep_width = _param_default(params, "KEEP_WIDTH", "DATA_WIDTH/8")
    interfaces: list[dict[str, Any]] = []
    bus = decisions.get("bus_interface", "")
    bus_text = f"{bus} {text}".lower()
    if _needs_valid_ready_interface(bus_text):
        machine = machine or {}
        extra_inputs = _machine_input_names(machine, params)
        extra_outputs = [
            str(item.get("port") or item.get("name"))
            for item in machine.get("output_rules") or []
            if isinstance(item, dict) and str(item.get("port") or item.get("name") or "")
        ]
        interfaces.append(
            {
                "name": "valid_ready_transaction",
                "type": "valid_ready",
                "role": "sink",
                "description": "Native valid/ready transaction interface derived from approved Web Q&A.",
                "ports": _valid_ready_ports(data_width, count_width, params, extra_inputs, extra_outputs),
            }
        )
    if _mentions_without_local_negation(bus_text, r"\bapb\b"):
        interfaces.append(
            {
                "name": "apb_slave",
                "type": "APB4",
                "role": "slave",
                "description": bus or "APB4 slave control/status interface",
                "ports": _apb_ports(addr_width, data_width),
            }
        )
    if _mentions_without_local_negation(bus_text, r"\b(axi4[- ]lite|axil|axi lite)\b"):
        interfaces.append(
            {
                "name": "axi_lite_slave",
                "type": "AXI4-Lite",
                "role": "slave",
                "description": bus or "AXI4-Lite control/status interface",
                "ports": _axi_lite_ports(addr_width, data_width),
            }
        )
    if _mentions_without_local_negation(text, r"\b(axis|axi4[- ]stream|axi[- ]stream)\b"):
        interfaces.append(
            {
                "name": "axis_input",
                "type": "AXI4-Stream",
                "role": "sink",
                "description": "Streaming payload input observed or transformed by the IP",
                "ports": _axis_ports(data_width, keep_width),
            }
        )
    if not interfaces:
        interfaces.append(
            {
                "name": "custom_control",
                "type": "custom",
                "role": "slave",
                "description": decisions.get("bus_interface") or "Custom control/data interface from approved Q&A",
                "ports": [
                    _port("cfg_valid", 1, "input", "Configuration/transaction valid"),
                    _port("cfg_ready", 1, "output", "Configuration/transaction ready"),
                    _port("cfg_data", data_width, "input", "Configuration/transaction payload"),
                    _port("status_data", data_width, "output", "Observed status/result payload"),
                ],
            }
        )
    interrupt = decisions.get("interrupt", "")
    if interrupt and not re.search(r"\b(no|none|not applicable|n/a)\b", interrupt, re.IGNORECASE):
        interfaces.append(
            {
                "name": "interrupt_output",
                "type": "level_irq",
                "role": "source",
                "description": interrupt,
                "ports": [_port("irq", 1, "output", "Level interrupt output")],
            }
        )
    interfaces.append(
        {
            "name": "debug_status",
            "type": "custom",
            "role": "output",
            "description": "Minimal waveform and status observability required by SSOT quality gates",
            "ports": [
                _port("busy", 1, "output", "IP is processing an accepted transaction or packet"),
                _port("error", 1, "output", "Sticky or current error indication"),
            ],
        }
    )
    return {
        "clock_domains": [
            {
                "name": "primary_clk",
                "frequency_mhz": freq,
                "description": decisions.get("clock_reset") or "Primary IP clock domain",
                "ports": [_port(clk, 1, "input", "Primary clock")],
            }
        ],
        "resets": [
            {
                "name": rst,
                "polarity": polarity,
                "sync_async": sync,
                "description": decisions.get("clock_reset") or "Primary reset",
                "ports": [_port(rst, 1, "input", "Primary reset")],
            }
        ],
        "interfaces": interfaces,
    }


def _parse_registers(text: str, data_width: Any) -> dict[str, Any]:
    if not text or re.search(r"\b(no|none|without|no csr|no register)\b", text, re.IGNORECASE):
        return {
            "config": {
                "register_width": data_width,
                "memory_mapped_registers": False,
                "note": text or "No firmware-visible registers were approved.",
            },
            "register_list": [],
        }
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, int]] = set()

    def add_row(name: str, offset: int, access: str, desc: str) -> None:
        clean = re.sub(r"[^A-Za-z0-9_]+", "_", str(name or "")).strip("_").upper()
        if not clean:
            return
        key = (clean, int(offset))
        if key in seen:
            return
        seen.add(key)
        rows.append(
            {
                "name": clean,
                "offset": int(offset),
                "width": data_width,
                "access": access.lower(),
                "reset": _infer_reset_value(desc),
                "category": _register_category(clean, desc),
                "description": desc.strip(),
                "fields": _fields_from_desc(clean, access.lower(), desc),
            }
        )

    for raw in re.split(r";|\n", text):
        item = raw.strip(" .")
        if not item:
            continue
        m = re.search(r"\b([A-Z][A-Z0-9_]+)\s+(0x[0-9a-fA-F]+)\s+([A-Z0-9_/]+)\s*(.*)", item)
        if not m:
            continue
        name, offset, access, desc = m.groups()
        add_row(name, int(offset, 16), access, desc.strip() or item)

    # Also accept prose maps such as "INTEN at 0x020" or
    # "DBGSTATUS/DBGCMD/DBGINST0 at 0xD00-0xD08"; this keeps the parser
    # generic while avoiding a silent fallback to a single CONTROL register.
    ignored_names = {"TRM", "CSR", "APB", "AXI", "RO", "RW", "WO", "W1C", "KB"}
    for raw in re.split(r",|;|\n", text):
        item = raw.strip(" .")
        if not re.search(r"\b(?:at|@|from)\s+0x[0-9a-fA-F]+", item, re.IGNORECASE):
            continue
        offsets = [int(tok, 16) for tok in re.findall(r"0x[0-9a-fA-F]+", item)]
        if not offsets:
            continue
        head = re.split(r"\b(?:at|@|from)\s+0x[0-9a-fA-F]+", item, maxsplit=1, flags=re.IGNORECASE)[0]
        head = head.rsplit(":", 1)[-1]
        raw_names: list[str] = []
        for token in re.findall(r"\b[A-Z][A-Za-z0-9_]*(?:/[A-Z][A-Za-z0-9_]*)*\b", head):
            parts = [token.replace("/", "_")] if "/" in token and len(offsets) == 1 else token.split("/")
            for part in parts:
                name = part.strip("_").upper()
                if name and name not in ignored_names and not name.isdigit():
                    raw_names.append(name)
        if not raw_names:
            raw_names = [re.sub(r"[^A-Za-z0-9_]+", "_", head).strip("_").upper() or "REG"]
        base = offsets[0]
        range_offsets = "-" in item and len(offsets) == 2 and len(raw_names) > len(offsets)
        for idx, name in enumerate(raw_names):
            offset = base + (4 * idx) if range_offsets else (offsets[idx] if idx < len(offsets) else base + (4 * idx))
            access = "ro" if re.search(r"\b(status|id|pc|fault|config|read)\b", item, re.IGNORECASE) else "rw"
            add_row(name, offset, access, item)
    if not rows:
        rows.append(
            {
                "name": "CONTROL",
                "offset": 0,
                "width": data_width,
                "access": "rw",
                "reset": 0,
                "category": "control",
                "description": text,
                "fields": [{"name": "enable", "bits": [0, 0], "access": "rw", "reset": 0}],
            }
        )
    return {
        "config": {
            "register_width": data_width,
            "memory_mapped_registers": True,
            "note": text,
        },
        "register_list": rows,
    }


def _infer_reset_value(text: str) -> Any:
    m = re.search(r"default\s+(0x[0-9a-fA-F_]+|\d+)", text or "", re.IGNORECASE)
    if m:
        return _parse_number(m.group(1))
    return 0


def _register_category(name: str, desc: str) -> str:
    lower = f"{name} {desc}".lower()
    if "status" in lower or "count" in lower or "busy" in lower:
        return "status"
    if "irq" in lower or "interrupt" in lower:
        return "interrupt"
    if "poly" in lower or "seed" in lower or "cfg" in lower or "ctrl" in lower:
        return "control"
    return "data"


def _fields_from_desc(name: str, access: str, desc: str) -> list[dict[str, Any]]:
    bits = re.findall(r"\b([a-zA-Z][a-zA-Z0-9_]*)\b", desc or "")
    fields: list[dict[str, Any]] = []
    ignored = {"rw", "ro", "w1c", "default", "while", "with", "bits", "set", "are", "the", "and", "or"}
    for bit, token in enumerate(bits[:8]):
        clean = token.lower()
        if clean in ignored or clean.isdigit():
            continue
        fields.append({"name": clean, "bits": [bit, bit], "access": access, "reset": 0})
    return fields or [{"name": name.lower(), "bits": ["WIDTH-1", 0], "access": access, "reset": _infer_reset_value(desc)}]


def _sub_modules(ip: str, state: dict[str, Any]) -> list[dict[str, Any]]:
    decisions = _decisions(state)
    text = decisions.get("submodule_structure", "")
    modules: list[tuple[str, str]] = []
    if text:
        if re.search(
            r"\b(single\s+(?:generated\s+)?top(?:[- ]level)?|single\s+module|"
            r"no\s+(?:separate\s+)?rtl\s+submodule|no\s+child\s+ssot|"
            r"conceptual\s+units?\s+only)\b",
            text,
            re.IGNORECASE,
        ):
            names = [
                re.sub(r"[^a-zA-Z0-9_]+", "_", raw.strip().lower()).strip("_")
                for raw in re.findall(r"\b([a-zA-Z][a-zA-Z0-9_]*_[a-zA-Z0-9_]+)\b", text)
            ]
            ignored = {
                "top_module",
                "top_level",
                "child_ssot",
                "rtl_submodule",
                "submodule_files",
            }
            rows: list[dict[str, Any]] = []
            for name in names:
                if not name or name in ignored or name in {row["name"].removeprefix(f"{ip}_") for row in rows}:
                    continue
                rows.append(
                    {
                        "name": f"{ip}_{name}" if not name.startswith(ip) else name,
                        "ownership": "conceptual",
                        "ssot_gen": False,
                        "rtl_emit": False,
                        "description": (
                            f"Conceptual functional decomposition unit `{name}` from approved Q&A; "
                            "implemented inside the single generated top module for this revision."
                        ),
                        "source_sections": ["function_model", "cycle_model", "features", "test_requirements"],
                        "function_model_refs": ["function_model.transactions.FM_PRIMARY"],
                        "cycle_model_refs": ["cycle_model.handshake_rules", "cycle_model.pipeline"],
                        "test_refs": ["test_requirements.scenarios"],
                    }
                )
            if rows:
                return rows
            return [
                {
                    "name": f"{ip}_single_top_behavior",
                    "ownership": "conceptual",
                    "ssot_gen": False,
                    "rtl_emit": False,
                    "description": "Conceptual decomposition is implemented inside the single generated top module for this revision.",
                    "source_sections": ["function_model", "cycle_model", "features", "test_requirements"],
                    "function_model_refs": ["function_model.transactions.FM_PRIMARY"],
                    "cycle_model_refs": ["cycle_model.handshake_rules", "cycle_model.pipeline"],
                    "test_refs": ["test_requirements.scenarios"],
                }
            ]
        m = re.search(r"(?:manifest\s+)?submodules?\s*:\s*(.+?)(?:\.\s|$)", text, re.IGNORECASE | re.DOTALL)
        tail = m.group(1) if m else text
        tail = re.split(
            r"\btop\s+wrapper\b|\btop[- ]level\b|\bwrapper\s+(?:is|owns|connects)\b|"
            r"\bmust\b|\bshall\b|\bshould\b|\bdo\s+not\b|\bdon't\b",
            tail,
            maxsplit=1,
            flags=re.IGNORECASE,
        )[0]
        if ";" in tail:
            raw_items = re.split(r";|\n", tail)
        elif "," in tail:
            raw_items = re.split(r",|\n", tail)
        else:
            raw_items = [tail]
        for raw in raw_items:
            token = raw.strip(" .")
            if not token or re.search(r"\b(no child|child ssot|v1|none)\b", token, re.IGNORECASE):
                continue
            token = re.sub(r"\b(manifest|submodules?|top wrapper|wrapper|blocks?|ownership)\b", "", token, flags=re.IGNORECASE).strip(" .:-")
            match = re.match(r"`?([A-Za-z][A-Za-z0-9_]*)`?(?:\s+|$|[-:])(?P<desc>.*)", token, re.DOTALL)
            if not match:
                continue
            raw_name = match.group(1)
            if raw_name.lower() in {"and", "or", "the", "a", "an", "module", "modules", "submodule", "submodules"}:
                continue
            name = re.sub(r"[^a-zA-Z0-9_]+", "_", raw_name.lower()).strip("_")
            desc = (match.group("desc") or token).strip(" .:-")
            if name and name not in {item[0] for item in modules}:
                modules.append((name, desc))
    if not modules:
        modules = [
            ("control", "control block derived from approved submodule structure"),
            ("datapath", "datapath block derived from approved submodule structure"),
            ("status", "status block derived from approved submodule structure"),
            ("irq_ctrl", "interrupt control block derived from approved submodule structure"),
        ]
    rows = []
    for idx, (name, description) in enumerate(modules):
        module_name = f"{ip}_{name}" if not name.startswith(ip) else name
        file_name = f"rtl/{ip}_{name}.sv" if not name.startswith(ip) else f"rtl/{name}.sv"
        primary_owner = idx == 0
        row = {
            "name": module_name,
            "file": file_name,
            "ownership": "manifest",
            "ssot_gen": True,
            "description": description or f"{name.replace('_', ' ')} block derived from approved submodule structure",
            "implements": (
                "Primary owner for SSOT function_model, cycle_model, dataflow, and test-observable behavior."
                if primary_owner
                else "Implements the approved primary behavior slice assigned by the SSOT module ledger."
            ),
            "source_sections": [
                "function_model",
                "cycle_model",
                "features",
                "dataflow",
                "fsm",
                "test_requirements",
                "traceability",
            ],
            "function_model_refs": ["function_model"] if primary_owner else ["function_model.transactions.FM_PRIMARY"],
            "decomposition_refs": ["decomposition", "functional_decomposition"] if primary_owner else [],
            "cycle_model_refs": ["cycle_model.handshake_rules", "cycle_model.pipeline", "cycle_model.latency"],
            "feature_refs": ["features"],
            "dataflow_refs": ["dataflow.sequence", "dataflow.sinks"],
            "fsm_refs": ["fsm.control"],
            "test_refs": ["test_requirements.scenarios"],
            "trace_refs": ["traceability.yaml_to_output"],
        }
        rows.append(row)
    rows.append(
        {
            "name": ip,
            "file": f"rtl/{ip}.sv",
            "ownership": "manifest",
            "ssot_gen": True,
            "description": "Top-level wrapper matching SSOT top_module and external interfaces",
            "kind": "wrapper",
            "wiring_only": True,
            "source_sections": ["top_module", "io_list", "sub_modules", "filelist"],
            "ports": ["io_list.clock_domains", "io_list.resets", "io_list.interfaces"],
            "connections": ["External SSOT ports are wired to manifest-owned implementation modules."],
        }
    )
    return rows


def _features(ip: str, decisions: dict[str, str], regs: dict[str, Any]) -> list[dict[str, Any]]:
    purpose = decisions.get("purpose") or f"{ip} approved behavior"
    rows = [
        {
            "name": "approved_primary_behavior",
            "trigger": "A valid protocol transaction, packet, or command is accepted on the external interface.",
            "datapath": purpose,
            "control": "Control state follows the approved function_model and cycle_model sections.",
            "output": "Externally observable outputs, status, counters, interrupts, and/or responses match the approved behavior.",
        }
    ]
    if regs.get("register_list"):
        rows.append(
            {
                "name": "csr_control_status",
                "trigger": "Firmware accesses the approved CSR map through the configured bus interface.",
                "datapath": decisions.get("register_map", "Approved registers control and expose IP state."),
                "control": "Access policy, reset defaults, W1C behavior, and read-only state are implemented per register_list.",
                "output": "CSR read data and side effects match register_list.",
            }
        )
    if decisions.get("interrupt") and not re.search(r"\b(no|none|n/a)\b", decisions["interrupt"], re.IGNORECASE):
        rows.append(
            {
                "name": "interrupt_status",
                "trigger": "An approved interrupt source event occurs.",
                "datapath": decisions["interrupt"],
                "control": "Interrupt status latches until cleared according to approved CSR or control policy.",
                "output": "irq reflects enabled pending interrupt sources.",
            }
        )
    return rows


def _scenarios(ip: str, decisions: dict[str, str]) -> list[dict[str, Any]]:
    text = decisions.get("test_expectation", "")
    candidates = [x.strip(" .") for x in re.split(r",|;", text) if x.strip(" .")]
    scenarios: list[dict[str, Any]] = [
        {
            "id": "SC_RESET",
            "name": "reset_defaults",
            "stimulus": "Assert and deassert reset using the approved clock/reset scheme.",
            "expected": "All state, status outputs, counters, handshakes, and interrupts return to approved reset defaults.",
            "checker": "Cycle checker compares reset-visible RTL state against function_model reset values.",
            "coverage": ["reset", "cycle_model.reset"],
        }
    ]
    for idx, item in enumerate(candidates[:8], start=1):
        name = re.sub(r"[^a-zA-Z0-9]+", "_", item.lower()).strip("_")[:48] or f"approved_scenario_{idx}"
        scenarios.append(
            {
                "id": f"SC{idx}",
                "name": name,
                "stimulus": item,
                "expected": f"RTL behavior matches approved Q&A expectation: {item}",
                "checker": "FL scoreboard and protocol monitor compare RTL outputs, side effects, and coverage bin hit.",
                "coverage": [name, "function_model", "cycle_model"],
            }
        )
    if len(scenarios) < 4:
        for idx, name in enumerate(["nominal_transaction", "error_or_malformed_input", "backpressure_or_stall"], start=len(scenarios)):
            scenarios.append(
                {
                    "id": f"SC_AUTO_{idx}",
                    "name": name,
                    "stimulus": f"Drive {name.replace('_', ' ')} using approved interfaces for {ip}.",
                    "expected": "Outputs, status, and side effects match the function_model.",
                    "checker": "Reference model comparison plus protocol assertions.",
                    "coverage": [name],
                }
            )
    return scenarios


def _function_model(
    ip: str,
    decisions: dict[str, str],
    regs: dict[str, Any],
    params: list[dict[str, Any]],
    machine: dict[str, Any] | None = None,
) -> dict[str, Any]:
    text = " ".join(decisions.values())
    data_width = _param_default(params, "DATA_WIDTH", 32)
    count_width = _param_default(params, "COUNT_WIDTH", 16)
    machine = machine or {}
    machine_state_names = {
        str(item.get("name"))
        for item in machine.get("state_updates") or []
        if isinstance(item, dict) and item.get("name")
    }
    state_vars = [
        {"name": "busy", "source": "accepted transaction or packet in progress", "reset": 0, "description": "Processing state"},
        {"name": "error", "source": "approved error/malformed condition", "reset": 0, "description": "Error indication"},
    ]
    if _needs_valid_ready_interface(text) and (
        not machine_state_names or "accepted_count" in machine_state_names
    ):
        state_vars.append(
            {
                "name": "accepted_count",
                "source": "valid_ready_transaction",
                "width": count_width,
                "reset": 0,
                "description": "Number of accepted valid/ready transactions.",
                "output": True,
            }
        )
    for name in sorted(machine_state_names - {"accepted_count"}):
        state_vars.append(
            {
                "name": name,
                "source": "machine_rules",
                "width": _signal_width(name, params),
                "reset": 0,
                "description": f"State variable defined by approved machine_rules: {name}",
            }
        )
    for reg in regs.get("register_list") or []:
        state_vars.append(
            {
                "name": str(reg.get("name", "reg")).lower(),
                "source": "register_list",
                "reset": reg.get("reset", 0),
                "description": reg.get("description", "Approved CSR state"),
            }
        )
    primary_tx: dict[str, Any] = {
        "id": "FM_PRIMARY",
        "name": "primary_behavior",
        "preconditions": ["valid input transaction or packet is accepted"],
        "inputs": ["external interface signals", "configuration/register state"],
        "outputs": [decisions.get("purpose") or f"{ip} performs approved behavior"],
        "side_effects": ["updates status, counters, events, and observable outputs according to approved Q&A"],
        "error_cases": [{"condition": "malformed input or invalid control policy", "result": "error status follows error_handling section"}],
    }
    sample_condition = _valid_ready_sample_condition(machine.get("sample_condition") or "valid", text)
    if _needs_valid_ready_interface(text) and machine.get("output_rules"):
        primary_tx.update(
            {
                "scenario_id": "SC_NOMINAL_TRANSACTION",
                "sample_condition": sample_condition,
                "output_rules": machine.get("output_rules") or [],
                "state_updates": machine.get("state_updates") or [],
            }
        )
    return {
        "purpose": "Cycle-independent reference model that rtl-gen and tb-gen must implement and compare against.",
        "state_variables": state_vars,
        "transactions": [
            {
                "id": "FM_RESET",
                "name": "reset",
                "preconditions": ["reset asserted"],
                "inputs": ["clock", "reset"],
                "outputs": ["busy == 0", "error == 0", "registers and counters equal approved reset defaults"],
                "side_effects": ["clears transient protocol state", "clears pending non-retained status"],
                "error_cases": [],
            },
            primary_tx,
            {
                "id": "FM_CSR",
                "name": "control_status_access",
                "preconditions": ["firmware/control bus access is accepted"],
                "inputs": ["address", "write data", "write enable", "byte strobes"],
                "outputs": ["read data and side effects match registers.register_list"],
                "side_effects": ["RW and W1C fields update exactly as specified"],
                "error_cases": [{"condition": "unsupported address or illegal access", "result": "bus error/status error according to error_handling"}],
            },
        ],
        "invariants": [
            "No output, counter, status bit, or interrupt may change except as a consequence of an approved transaction, event, reset, or CSR side effect.",
            "The function_model is the scoreboard source of truth for tb-gen.",
            "Any behavior not represented here must be escalated to ssot-gen before RTL signoff.",
        ],
        "reference_model_hint": "Generate a Python FunctionalModel.apply(txn) from state_variables and transactions, then compare every RTL-observable result against it.",
    }


def _rtl_contract(ip: str, decisions: dict[str, str], io: dict[str, Any], fm: dict[str, Any]) -> dict[str, Any]:
    text = " ".join(decisions.values())
    clk = io["clock_domains"][0]["ports"][0]["name"]
    rst = io["resets"][0]
    reset_active = "low" if str(rst.get("polarity") or "").lower() == "active_low" else "high"
    primary = {}
    for tx in fm.get("transactions") or []:
        if isinstance(tx, dict) and tx.get("id") == "FM_PRIMARY":
            primary = tx
            break
    output_rules = primary.get("output_rules") if isinstance(primary.get("output_rules"), list) else []
    state_updates = primary.get("state_updates") if isinstance(primary.get("state_updates"), list) else []
    if not _needs_valid_ready_interface(text) or not output_rules:
        return {
            "owner": "rtl-gen",
            "status": "requires_rtl_gen_refinement",
            "transaction": primary.get("id") or "FM_PRIMARY",
            "clock": clk,
            "reset": rst["name"],
            "reset_active": reset_active,
            "note": "No machine-checkable valid/ready datapath rule was approved in Web Q&A; rtl-gen must refine from SSOT before implementation.",
        }
    state_names = {
        str(item.get("name"))
        for item in fm.get("state_variables") or []
        if isinstance(item, dict) and item.get("name")
    }
    output_names = {
        str(item.get("name") or item.get("port"))
        for item in output_rules
        if isinstance(item, dict) and (item.get("name") or item.get("port"))
    }
    sample_condition = _valid_ready_sample_condition(primary.get("sample_condition") or "valid", text)
    rule_names = _rule_expr_names(sample_condition)
    for item in output_rules + state_updates:
        if isinstance(item, dict):
            rule_names |= _rule_expr_names(item.get("expr"))
    input_names = sorted(
        name
        for name in rule_names - state_names - output_names - {"true", "false", "True", "False"}
        if name not in {"ready", "result_valid"}
    )
    output_map = {
        str(item.get("name") or item.get("port")): str(item.get("port") or item.get("name"))
        for item in output_rules
        if isinstance(item, dict) and (item.get("name") or item.get("port"))
    }
    output_map.setdefault("accepted_count", "accepted_count")
    return {
        "owner": "ssot-gen",
        "type": "generic_structured_rule_contract",
        "transaction": "FM_PRIMARY",
        "clock": clk,
        "reset": rst["name"],
        "reset_active": reset_active,
        "sample_condition": sample_condition,
        "input_map": {name: name for name in input_names},
        "output_map": output_map,
        "ready_output": "ready",
        "output_valid": "result_valid" if "result_valid" in output_map.values() else "",
        "output_rules": output_rules,
        "state_updates": state_updates,
        "contract_invariants": [
            "ready is asserted whenever reset is deasserted and the SSOT does not define backpressure.",
            "result and result_valid update only when sample_condition is true.",
            "accepted_count increments once per accepted transaction.",
        ],
    }


def _cycle_model(decisions: dict[str, str], io: dict[str, Any]) -> dict[str, Any]:
    clk = io["clock_domains"][0]["ports"][0]["name"]
    freq = io["clock_domains"][0].get("frequency_mhz") or 100
    rst = io["resets"][0]
    rules = [
        {"signal": "valid_ready", "rule": "A transfer is accepted only on valid && ready or the equivalent approved protocol phase."},
        {"signal": "outputs", "rule": "Outputs remain stable while downstream backpressure prevents acceptance."},
    ]
    text = json.dumps(io).lower()
    if "apb" in text:
        rules.append({"signal": "apb", "rule": "APB transfers use setup phase psel && !penable followed by access phase psel && penable && pready."})
    if "axi4-stream" in text:
        rules.append({"signal": "axis", "rule": "AXI4-Stream accepts beats on tvalid && tready; tlast closes the packet transaction."})
    return {
        "purpose": "Cycle-accurate protocol, reset, latency, and observability contract for rtl-gen.",
        "executable": "pymtl3",
        "backend_policy": "Use PyMTL3 for the clocked cycle model shell; FunctionalModel remains the behavioral oracle.",
        "clock": clk,
        "reset": {
            "signal": rst["name"],
            "polarity": rst["polarity"],
            "assertion": rst["sync_async"],
            "deassertion": "State may accept new work after reset deassertion and any required synchronization.",
        },
        "latency": {
            "control_access": {"min_cycles": 1, "max_cycles": "protocol_backpressure_bound", "description": "CSR/control latency is bounded by protocol ready/valid phases."},
            "primary_transaction": {"min_cycles": 1, "max_cycles": "implementation_defined_by_function_model", "description": "Primary behavior completes when output/status event is observed."},
        },
        "handshake_rules": rules,
        "pipeline": [
            {"stage": "S0_ACCEPT", "cycle": 0, "action": "Accept protocol transaction/beat/command under approved handshake."},
            {"stage": "S1_UPDATE", "cycle": "0..N", "action": "Update function_model state and datapath/control state."},
            {"stage": "S2_OBSERVE", "cycle": "N..M", "action": "Publish output response, status, interrupt, counter, or debug event."},
        ],
        "ordering": [
            "Accepted transactions preserve externally visible ordering unless an explicit reordering feature is listed.",
            "CSR side effects occur in program order at the accepted control transaction boundary.",
        ],
        "backpressure": ["Input data and control state remain stable while the selected protocol applies backpressure."],
        "performance": {
            "frequency_mhz": freq,
            "throughput": {"sustained_beats_per_cycle": 1, "condition": "No downstream or internal backpressure"},
            "outstanding": {"max": 1, "description": "Default one accepted operation until Q&A declares deeper buffering"},
            "depth": {"pipeline_stages": 3, "queue_depth": 1, "description": "Accept/update/observe default cycle structure"},
        },
        "observability": ["busy", "error", "all protocol valid/ready signals", "all CSR side-effect points"],
    }


def _doc(ip: str, state: dict[str, Any]) -> dict[str, Any]:
    decisions = _decisions(state)
    source_custom = _ssot_custom(state)
    params = _parse_parameters(decisions.get("parameters", ""))
    machine = _machine_rules(decisions, params)
    ip_type = _infer_ip_type(ip, state)
    clk, freq, rst_name, _rst_pol, _rst_sync = _clock_reset(decisions)
    io = _interfaces(ip, state, params, machine)
    data_width = _param_default(params, "DATA_WIDTH", 32)
    regs = _parse_registers(decisions.get("register_map", ""), data_width)
    subs = _sub_modules(ip, state)
    features = _features(ip, decisions, regs)
    scenarios = _scenarios(ip, decisions)
    fm = _function_model(ip, decisions, regs, params, machine)
    memories_none = re.search(r"\b(no local ram|no ram|no memory|none|csr window only)\b", decisions.get("memory_map", ""), re.IGNORECASE)
    irq_text = decisions.get("interrupt", "")
    irq_enabled = bool(irq_text and not re.search(r"\b(no|none|not applicable|n/a)\b", irq_text, re.IGNORECASE))
    rtl_files = [row["file"] for row in subs if row.get("file")]
    if f"rtl/{ip}.sv" not in rtl_files:
        rtl_files.append(f"rtl/{ip}.sv")
    doc: dict[str, Any] = {
        "top_module": {
            "name": ip,
            "version": "1.0",
            "type": ip_type,
            "description": decisions.get("purpose") or str(state.get("kind") or f"{ip} leaf IP"),
            "reference_spec": "approved ATLAS Web Q&A state",
            "target": {"technology": "generic", "clock_freq_mhz": freq, "area_um2": "not_constrained", "power_mw": "not_constrained"},
        },
        "sub_modules": subs,
        "parameters": params,
        "io_list": io,
        "features": features,
        "dataflow": {
            "source": "approved external input/control interfaces",
            "sequence": [
                "accept transaction or packet using cycle_model handshake",
                "apply function_model transaction and update internal state",
                "publish response/status/interrupt/debug outputs",
            ],
            "sinks": ["external outputs", "register reads", "interrupt/status/debug observability"],
            "notes": decisions.get("purpose") or "Dataflow follows approved Q&A purpose.",
        },
        "function_model": fm,
        "cycle_model": _cycle_model(decisions, io),
        "clock_reset_domains": {
            "domains": [{"name": "primary_clk", "clock": clk, "frequency_mhz": freq, "description": decisions.get("clock_reset") or "Primary clock"}],
            "reset_scheme": {"signal": rst_name, "description": decisions.get("clock_reset") or "Primary reset"},
        },
        "cdc_requirements": {"crossings": [], "synchronizers": [], "note": "Approved Q&A describes a single clock domain unless later SSOT revision adds crossings."},
        "rdc_requirements": {"crossings": [], "synchronizers": [], "note": "Approved Q&A describes a single reset domain unless later SSOT revision adds crossings."},
        "registers": regs,
        "memory": {
            "instances": [] if memories_none else [{"name": "state_storage", "type": "flop_or_small_array", "description": decisions.get("memory_map") or "State storage required by function_model"}],
            "note": decisions.get("memory_map") or "No explicit memory map was approved beyond control/status state.",
        },
        "interrupts": {
            "sources": _interrupt_sources(irq_text) if irq_enabled else [],
            "output": {"signal": "irq" if irq_enabled else "none", "polarity": "level_high" if irq_enabled else "not_applicable", "type": "level" if irq_enabled else "none"},
            "note": irq_text or "No interrupt behavior approved.",
        },
        "fsm": {
            "control": {
                "states": ["IDLE", "ACCEPT", "PROCESS", "RESPOND", "ERROR"],
                "transitions": [
                    {"from": "IDLE", "to": "ACCEPT", "condition": "approved protocol transaction is accepted"},
                    {"from": "ACCEPT", "to": "PROCESS", "condition": "function_model primary transaction begins"},
                    {"from": "PROCESS", "to": "RESPOND", "condition": "observable output/status is ready"},
                    {"from": "PROCESS", "to": "ERROR", "condition": "error_handling condition detected"},
                    {"from": "RESPOND", "to": "IDLE", "condition": "response/status event observed and no further work pending"},
                    {"from": "ERROR", "to": "IDLE", "condition": "approved clear/reset policy completes"},
                ],
            }
        },
        "timing": {
            "target_clocks": [{"name": clk, "frequency_mhz": freq, "duty_cycle": 0.5, "uncertainty_ns": 0.2}],
            "latency_budget": {
                "control_access_cycles": {"min": 1, "max": "protocol_bound", "measured_from": "accepted control transaction", "measured_to": "response visible"},
                "primary_transaction_cycles": {"min": 1, "max": "implementation_bound_from_cycle_model", "measured_from": "accepted input", "measured_to": "observable result/event"},
            },
            "throughput": {"goal": "Sustain one accepted transaction whenever upstream valid and downstream/internal ready permit."},
            "timing_exceptions": [],
            "sta_expectations": {"setup_wns_ns_min": 0.0, "hold_wns_ns_min": 0.0, "required_reports": ["sta/out/timing.rpt", "sta/out/wns.json"]},
        },
        "power": {
            "domains": [{"name": "PD_MAIN", "voltage": "nominal", "clock_domains": ["primary_clk"], "isolation": "not_required_single_domain"}],
            "clock_gating": {"required": False, "rationale": "No explicit low-power mode was approved in Web Q&A."},
            "reset_retention": {"retention_required": False, "reset_value_source": "function_model state_variables"},
            "power_states": [{"name": "ON", "entry": "reset deasserted", "exit": "reset asserted or integration power-down", "guarantees": ["function_model behavior active"]}],
            "upf_required": False,
        },
        "security": {
            "classification": "non_secure_leaf_ip",
            "assets": [
                {"name": "configuration_state", "protection": "CSR/control state changes only through approved access policy."},
                {"name": "observable_results", "protection": "Results/status/interrupts must reflect function_model without silent corruption."},
            ],
            "threat_model": [
                {"threat": "illegal access or malformed input", "mitigation": "error_handling path and DV malformed/error scenarios"},
                {"threat": "state corruption across reset/backpressure", "mitigation": "cycle_model reset and stable-backpressure checks"},
            ],
            "privilege_model": "Integration-level privilege policy is outside this leaf IP unless explicitly added to registers/security.",
            "safety_goals": ["No silent data/status corruption", "No unbounded protocol deadlock under approved handshakes"],
        },
        "error_handling": {
            "error_sources": [
                {"id": "ERR_MALFORMED_OR_ILLEGAL", "condition": "malformed input, illegal CSR access, or function_model error case", "architectural_effect": "error status and optional interrupt follow approved policy"},
            ],
            "propagation": ["Errors are visible through status/debug outputs and bus response or interrupt when the approved interface supports it."],
            "recovery": [{"action": "reset or approved clear/control operation", "clears": ["error", "pending interrupt/status"], "preserves": ["configuration state unless reset policy says otherwise"]}],
        },
        "debug_observability": {
            "waveform_must_probe": [clk, rst_name, "busy", "error", "all valid/ready or protocol phase signals", "all CSR side-effect state"],
            "status_outputs": ["busy", "error"],
            "trace_events": [
                {"name": "accepted_transaction", "trigger": "protocol transaction accepted"},
                {"name": "observable_result", "trigger": "function_model output/status event occurs"},
                {"name": "error_detected", "trigger": "error_handling condition detected"},
            ],
            "debug_registers": [reg.get("name") for reg in regs.get("register_list", []) if reg.get("category") in {"status", "interrupt"}],
        },
        "integration": {
            "bus_attachment": {"control": decisions.get("bus_interface") or "approved interface", "data": decisions.get("purpose") or "approved leaf behavior"},
            "address_map_requirements": {"memory_map": decisions.get("memory_map") or "Assigned by SoC/integration; leaf IP uses local offsets when registers exist."},
            "dependencies": {"external_modules": [], "external_clocks": [clk], "external_resets": [rst_name]},
            "connections": [],
            "connection_contract_status": (
                "missing machine-readable module wiring; child RTL drafts may proceed from owner packets, "
                "but top integration/signoff must stay blocked until SSOT authors integration.connections "
                "or sub_modules[].connections with module/port/signal records"
            ),
            "integration_notes": [
                "Do not modify SoC/RISC-V development files during leaf IP generation.",
                "Top integration owns base address assignment and system-level routing.",
            ],
        },
        "dft": {
            "scan_required": False,
            "scan_ports": [],
            "test_mode_ports": [],
            "controllability": {"reset": rst_name, "clocks": [clk]},
            "observability": {"required_internal_points": ["busy", "error", "function_model state variables"]},
            "mbist_required": False,
            "notes": "No explicit DFT requirement approved; maintain reset controllability and waveform observability.",
        },
        "synthesis": {
            "dialect": "systemverilog_2012",
            "top_module": ip,
            "constraints": [
                "No inferred latches",
                "No combinational loops on ready/valid or bus response paths",
                "All sequential state has reset behavior matching function_model",
                "DUT-only lint must pass before TB/sim signoff",
            ],
            "ppa_targets": {"area_um2_max": None, "power_mw_max": None, "frequency_mhz_min": freq},
            "required_outputs": ["syn/out/area.rpt", "syn/out/timing_summary.rpt", "sta/out/wns.json"],
        },
        "pnr": {
            "utilization_pct": 60,
            "aspect_ratio": 1.0,
            "core_space_um": 2.0,
            "global_density": 0.65,
            "io_layers": {"horizontal": "met3", "vertical": "met2"},
            "cts_buf_list": ["sky130_fd_sc_hd__clkbuf_4", "sky130_fd_sc_hd__clkbuf_8"],
            "routing": {"signal_layers": {"min": "met1", "max": "met5"}, "drc_waivers": []},
        },
        "coding_rules": {
            "verilog_style": "systemverilog_2012",
            "file_extension": ".sv",
            "parameter_header": f"rtl/{ip}_param.vh",
            "conventions": [
                "Flatten external protocol ports unless the SSOT explicitly approves interface constructs.",
                "Separate protocol/control/datapath/status responsibilities according to sub_modules.",
                "Avoid style-only lint violations by using default nettype discipline and explicit widths.",
                "Generated RTL uses the project SystemVerilog subset in .sv files: input logic/output logic ports, internal logic, localparam state encoding, always @ blocks.",
                "Do not use typedef, enum, always_ff, always_comb, package, import, function, task, for, or while in generated RTL.",
            ],
            "lint_waivers": [],
        },
        "reuse_modules": [],
        "custom": {
            "approved_web_decisions": decisions,
            "atlas_decisions": decisions,
            "atlas_decision_sources": source_custom.get("atlas_decision_sources", {}),
            "atlas_imports": source_custom.get("atlas_imports", []),
            "atlas_import_conflicts": source_custom.get("atlas_import_conflicts", []),
            "optional_behavior_policy": {
                "resolution": (
                    "No optional RTL behavior is implied by prose. Features not explicitly approved "
                    "are disabled for this revision unless represented by an explicit SSOT parameter, "
                    "register field, or feature row with reset default and coverage bins."
                ),
                "source": "approved ATLAS Web Q&A state",
                "downstream_rule": "rtl-gen, tb-gen, sim-debug, and coverage must treat this policy as the only optional-behavior authority.",
            },
            "assumptions": [
                "Any behavior not explicitly approved in Web Q&A is treated as integration-owned or must be escalated before signoff.",
                "The deterministic SSOT bridge creates a reviewable draft; downstream LLM workflows may refine within the same approved facts.",
            ],
        },
        "dir_structure": {"output_dirs": {"rtl": "rtl/", "list": "list/", "tb": "tb/", "sim": "sim/", "cov": "cov/", "lint": "lint/"}, "yaml_dir": "yaml/", "generators_dir": "generators/"},
        "filelist": {"rtl": rtl_files, "list": [f"list/{ip}.f"], "tb": [f"tb/cocotb/test_{ip}.py", "tb/cocotb/test_runner.py"], "sim": [f"sim/{ip}.vcd", "sim/results.xml"], "cov": ["cov/coverage.json", "cov/fcov_plan.json"]},
        "rtl_contract": _rtl_contract(ip, decisions, io, fm),
        "test_requirements": {
            "scenarios": scenarios,
            "scoreboard_checks": len(scenarios),
            "coverage_goals": {
                "function": {
                    "target_pct": 100,
                    "model": "function_model",
                    "description": "Behavioral coverage for function_model transactions, architectural state updates, outputs, errors, and CSR/control effects.",
                    "bins": [
                        {
                            "id": "FCOV_PRIMARY_TRANSACTION",
                            "source_ref": "function_model.transactions.FM_PRIMARY",
                            "class": "transaction",
                            "description": "Primary approved function_model transaction observed by scoreboard",
                        }
                    ],
                },
                "cycle": {
                    "target_pct": 100,
                    "model": "cycle_model",
                    "description": "Cycle coverage for cycle_model handshake, latency, ordering, backpressure, protocol phase, and FSM timing behavior.",
                    "bins": [
                        {
                            "id": "CCOV_PRIMARY_HANDSHAKE",
                            "source_ref": "cycle_model.handshake_rules",
                            "class": "handshake",
                            "description": "Primary cycle_model handshake rule observed by checker/waveform evidence",
                        }
                    ],
                },
                "functional": "Legacy alias: coverage_goals.function and coverage_goals.cycle must both close.",
                "evidence": (
                    "Function/cycle closure uses cov/fcov_plan.json, cov/coverage_functional.json, "
                    "sim/scoreboard_events.jsonl, and cov/coverage.json. Tool-instrumented structural "
                    "metrics are optional unless an explicit SSOT metric goal with matching tool evidence is added."
                ),
            },
        },
        "quality_gates": {
            "ssot": {"pass": "All production SSOT sections validate with check_ssot_disk.sh and no unresolved open-decision markers.", "evidence": ["check_ssot_disk.sh PASS"]},
            "rtl": {"pass": "RTL implements function_model/cycle_model and DUT-only compile/lint pass with fresh evidence.", "evidence": ["list/<ip>.f", "rtl compile report", "dut lint report"]},
            "rtl_gen": {
                "profile": "production" if any(token in ip.lower() for token in ("pl330", "dma330", "dma_330")) else "standard",
                "pass": (
                    "rtl-gen execution_policy.pass_allowed is true, every required SSOT-derived RTL TODO is closed, "
                    "and provenance proves common_ai_agent rtl-gen authored the RTL without fixed-template fallback behavior."
                ),
                "evidence": ["rtl/rtl_authoring_plan.json", "logs/rtl-gen/rtl_todo_plan.json", "rtl/provenance.json", "rtl_compile.json", "lint/dut_lint.json"],
            },
            "dv": {"pass": "Every SSOT scenario has an executable cocotb/pyuvm test, checker, FL-vs-RTL equivalence goal, and scoreboard comparison.", "evidence": ["verify/equivalence_goals.json", "sim/scoreboard_events.jsonl", "tb/cocotb/results.xml", "sim/results.xml"]},
            "coverage": {"pass": "Functional coverage bins meet planned threshold and limitations are zero or explicitly waived.", "evidence": ["cov/coverage.json", "cov/fcov_plan.json"]},
            "eda": {"pass": "Synthesis/STA/DFT evidence is produced or explicitly out-of-scope for this leaf signoff.", "evidence": ["syn/out/area.rpt", "sta/out/wns.json"]},
            "signoff": {"pass": "SSOT, FL/equivalence, RTL, lint, DV, simulation, coverage, and required EDA gates pass with fresh artifacts.", "evidence": ["ATLAS /api/progress signoff PASS"]},
        },
        "traceability": {
            "yaml_to_output": [
                {"yaml": "top_module", "output": "RTL top module, filelist, TB top binding"},
                {"yaml": "io_list", "output": "RTL port list and protocol monitors"},
                {"yaml": "registers", "output": "CSR RTL, firmware-visible behavior, CSR tests"},
                {"yaml": "function_model", "output": "Python FunctionalModel.apply(txn), scoreboard expected results"},
                {"yaml": "cycle_model", "output": "Protocol timing assertions, latency/backpressure tests, waveform checks"},
                {"yaml": "function_model/cycle_model/test_requirements", "output": "verify/equivalence_goals.json and FL-vs-RTL scoreboard contracts"},
                {"yaml": "test_requirements.scenarios", "output": "cocotb/pyuvm tests and functional coverage bins"},
                {"yaml": "quality_gates", "output": "ATLAS progress pass/fail criteria"},
            ]
        },
        "workflow_todos": {
            "rtl-gen": [
                {
                    "id": "RTL_IMPLEMENT_APPROVED_BEHAVIOR",
                    "content": "Implement every approved SSOT behavior in RTL-owned manifest modules",
                    "detail": (
                        "Use function_model transactions, cycle_model timing, interfaces, registers, "
                        "error handling, debug observability, and sub_modules ownership to implement "
                        "the DUT without placeholder tie-offs or fixed IP templates."
                    ),
                    "criteria": [
                        "Every required rtl_todo_plan task reaches todo_completion.status=pass after audit",
                        "DUT-only compile/lint reports are fresh and clean after the final RTL edit",
                        "RTL preserves SSOT authority: SSOT, FunctionalModel, coverage goals, interface rules, and performance targets are not edited to make RTL pass",
                    ],
                    "source_refs": ["function_model", "cycle_model", "sub_modules", "quality_gates.rtl", "quality_gates.rtl_gen"],
                    "owner_module": f"{ip}_core",
                    "owner_file": f"rtl/{ip}.sv",
                    "priority": "high",
                    "required": True,
                },
                {
                    "id": "RTL_TARGET_SCALE_POLICY",
                    "content": "Lock or waive RTL target-scale policy before production signoff",
                    "detail": (
                        "Production-profile RTL can use reference-derived scale candidates as review inputs, "
                        "but rtl-gen must not treat them as truth until a human locks positive minima in "
                        "quality_gates.rtl_gen.target_scale or approves target_scale_waiver."
                    ),
                    "criteria": [
                        "quality_gates.rtl_gen.target_scale contains at least one positive structural minimum such as source_files_min, modules_min, or depth_score_min",
                        "or quality_gates.rtl_gen.target_scale_waiver.approved is true with owner and reason",
                        "rtl_todo_plan.json target_scale_policy gate passes after rerunning rtl-gen TODO derivation",
                    ],
                    "source_refs": ["quality_gates.rtl_gen.target_scale", "quality_gates.rtl_gen.target_scale_waiver", "reports/rtl_reference_profile.json"],
                    "owner_module": ip,
                    "owner_file": f"rtl/{ip}.sv",
                    "priority": "high",
                    "required": True,
                    "answer_schema": {
                        "format": "YAML or JSON",
                        "root_key": "target_scale or target_scale_waiver",
                        "target_scale_fields": [
                            "source_files_min",
                            "modules_min",
                            "lines_min",
                            "depth_score_min",
                            "nonconstant_assigns_min",
                            "procedural_blocks_min",
                            "instances_min",
                            "basis",
                        ],
                        "target_scale_waiver_required_fields": ["approved", "reason", "owner"],
                        "rule": "Only human-approved SSOT minima or waiver can close this gate; do not infer target scale from generated RTL.",
                    },
                    "example_answer": {
                        "target_scale": {
                            "source_files_min": 4,
                            "modules_min": 8,
                            "lines_min": 1200,
                            "depth_score_min": 120,
                            "basis": "Human-approved architecture review calibrated from rtl_reference_profile.json.",
                        },
                        "target_scale_waiver": {
                            "approved": True,
                            "reason": "Smaller variant intentionally does not enforce reference-scale minima.",
                            "owner": "human-review",
                        },
                    },
                },
                {
                    "id": "RTL_RESOLVE_CONNECTION_CONTRACTS",
                    "content": "Resolve production multi-module connection contracts before top integration signoff",
                    "detail": (
                        "The SSOT may declare manifest child modules before machine-readable wiring is approved. "
                        "Child module drafts may proceed from owner packets; top wiring, PASS, and signoff must remain "
                        "blocked until SSOT authors integration.connections or sub_modules[].connections records."
                    ),
                    "criteria": [
                        "integration.connections or sub_modules[].connections lists every active child module connection as module/port/signal data",
                        "rtl_authoring_plan.execution_policy.connection_contract_gap.status becomes ok",
                        "Top/gate authoring packet integration_signoff_allowed is true after rerunning rtl-gen TODO derivation",
                    ],
                    "source_refs": ["integration.connections", "sub_modules[].connections", "quality_gates.rtl_gen"],
                    "owner_module": ip,
                    "owner_file": f"rtl/{ip}.sv",
                    "priority": "high",
                    "required": True,
                    "answer_schema": {
                        "format": "YAML or JSON",
                        "root_key": "connection_contracts",
                        "item_required_fields": ["module", "port", "signal"],
                        "item_optional_fields": [
                            "instance",
                            "direction",
                            "source_ref",
                            "allow_constant",
                            "allow_unused",
                            "tieoff",
                            "reason",
                        ],
                        "rule": "Only approved rows become SSOT wiring contracts; do not infer missing wiring from RTL.",
                    },
                    "example_answer": {
                        "connection_contracts": [
                            {
                                "module": f"{ip}_engine",
                                "instance": "u_engine",
                                "port": "done_o",
                                "signal": "done",
                                "source_ref": "integration.connections.done_o",
                            }
                        ]
                    },
                }
            ],
            "tb-gen": [],
            "sim_debug": [],
        },
        "generation_flow": {
            "steps": [
                {"name": "validate_ssot", "command": f"bash workflow/ssot-gen/scripts/check_ssot_disk.sh {ip}", "description": "Validate production SSOT structure and model sections"},
                {"name": "handoff_fl_model", "command": "/wf fl-model-gen", "description": "Generate executable FunctionalModel and decomposition from SSOT"},
                {"name": "handoff_equivalence_goals", "command": f"/ssot-equiv-goals {ip}", "description": "Derive SSOT-traced FL-vs-RTL equivalence goals before TB generation"},
                {"name": "handoff_rtl", "command": f"/ssot-rtl {ip}", "description": "Generate RTL directly from validated SSOT and prove DUT-only compile/lint"},
                {"name": "handoff_tb", "command": f"/ssot-tb-cocotb {ip}", "description": "Generate cocotb/pyuvm tests from SSOT scenarios and FL scoreboard"},
                {"name": "handoff_sim_debug", "command": "/wf sim_debug", "description": "Classify sim/waveform/coverage failures against SSOT, FL, RTL, or TB owner"},
            ]
        },
    }
    return {key: doc[key] for key in REQUIRED_ORDER}


def _interrupt_sources(text: str) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    for idx, token in enumerate(re.split(r",|;|\band\b", text), start=1):
        name = re.sub(r"[^a-zA-Z0-9]+", "_", token.lower()).strip("_")
        if not name or name in {"irq", "interrupt", "sources", "are"}:
            continue
        sources.append({"id": f"IRQ{idx}", "name": name[:48], "condition": token.strip(), "clear": "approved CSR/control clear policy"})
    return sources or [{"id": "IRQ1", "name": "approved_event", "condition": text, "clear": "approved CSR/control clear policy"}]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("ip")
    ap.add_argument("--root", default=".")
    ns = ap.parse_args()
    root = Path(ns.root).resolve()
    state = _load_state(root, ns.ip)
    doc = _doc(ns.ip, state)
    yaml_dir = root / ns.ip / "yaml"
    yaml_dir.mkdir(parents=True, exist_ok=True)
    out = yaml_dir / f"{ns.ip}.ssot.yaml"
    header = (
        "# =============================================================================\n"
        f"# {ns.ip}.ssot.yaml -- YAML Single Source of Truth\n"
        f"# Generated from ATLAS Web Q&A approval at {time.strftime('%Y-%m-%dT%H:%M:%S')}\n"
        "# Generator: workflow/ssot-gen/scripts/approved_to_ssot.py (generic SSOT bridge)\n"
        "# =============================================================================\n\n"
    )
    out.write_text(header + yaml.safe_dump(doc, sort_keys=False, width=120), encoding="utf-8")
    loaded = yaml.safe_load(out.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise SystemExit("[approved_to_ssot] generated YAML failed parse sanity check")
    missing = [key for key in REQUIRED_ORDER if key not in loaded]
    if missing:
        raise SystemExit("[approved_to_ssot] generated YAML missing sections: " + ", ".join(missing))
    req_out = _write_requirements(root, ns.ip, state, loaded)
    print(f"[approved_to_ssot] wrote {out.relative_to(root)}")
    print(f"[approved_to_ssot] wrote {req_out.relative_to(root)}")
    print(f"[approved_to_ssot] PASS: YAML parses with {len(loaded.keys())} top-level sections")
    print("[SSOT HANDOFF] -> rtl-gen")
    print(f"SSOT: {out.relative_to(root)}")
    print(f"top_module: {ns.ip}")
    print(f"type: {loaded.get('top_module', {}).get('type', 'unknown')}")
    print("next: /ssot-rtl " + ns.ip)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
