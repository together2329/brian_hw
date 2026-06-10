#!/usr/bin/env python3
"""Derive a per-IP verification/evidence contract from SSOT artifacts.

This intentionally does not select a static IP profile.  It inspects the IP's
own SSOT, IO, transactions, state, timing, and equivalence goals, then emits the
evidence obligations that downstream stages should satisfy.
"""

from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path
from typing import Any

import yaml


SIGNAL_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_$]*(?:\[[^\]]+\])?$")


BASE_EVIDENCE = [
    {
        "id": "ssot",
        "stage_id": "ssot",
        "artifact": "yaml/<ip>.ssot.yaml",
        "required": True,
        "rationale": "All downstream obligations are derived from locked truth.",
    },
    {
        "id": "fl_equivalence",
        "stage_id": "emit_fl",
        "artifact": "model/fl_model_check.json",
        "required": True,
        "rationale": "A golden functional oracle is required for general IP equivalence.",
    },
    {
        "id": "cl_contract",
        "stage_id": "emit_cl",
        "artifact": "model/cl_model_check.json",
        "required": True,
        "rationale": "Cycle/timing obligations must be explicit even when simple.",
    },
    {
        "id": "equivalence_goals",
        "stage_id": "emit_equiv_goals",
        "artifact": "verify/equivalence_goals.json",
        "required": True,
        "rationale": "Scoreboard rows must map to concrete goals.",
    },
    {
        "id": "rtl_compile",
        "stage_id": "rtl_compile",
        "artifact": "rtl/rtl_compile.json",
        "required": True,
        "rationale": "DUT-only RTL must compile without diagnostics.",
    },
    {
        "id": "dut_lint",
        "stage_id": "dut_lint",
        "artifact": "lint/dut_lint.json",
        "required": True,
        "rationale": "DUT-only lint must be clean or explicitly waived.",
    },
    {
        "id": "tb_python_compile",
        "stage_id": "tb_python_compile",
        "artifact": "tb/cocotb/tb_py_compile.json",
        "required": True,
        "rationale": "Generated TB must parse before simulation.",
    },
    {
        "id": "simulation",
        "stage_id": "sim",
        "artifact": "sim/results.xml",
        "required": True,
        "rationale": "Executable RTL evidence is required.",
    },
    {
        "id": "scoreboard_schema",
        "stage_id": "scoreboard_schema",
        "artifact": "sim/scoreboard_events.jsonl",
        "required": True,
        "rationale": "Simulation must emit structured FL-vs-RTL evidence.",
    },
    {
        "id": "coverage",
        "stage_id": "coverage",
        "artifact": "cov/coverage.json",
        "required": True,
        "rationale": "Required scenarios and bins must close against RTL-observed evidence.",
    },
    {
        "id": "truth_coverage",
        "stage_id": "truth_coverage",
        "artifact": "signoff/truth_coverage.json",
        "required": True,
        "rationale": "Every required locked-truth obligation must have executable evidence.",
    },
]


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as exc:
        raise SystemExit(f"[derive_ip_contract] FAIL: cannot parse {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"[derive_ip_contract] FAIL: {path} root must be a mapping")
    return data


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _text(value: Any) -> str:
    return str(value or "").strip()


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def _is_negative_backpressure_statement(text: str) -> bool:
    lowered = text.strip().lower()
    return bool(re.match(r"^(?:no|none|never|without)\s+(?:backpressure|stall|stalls|flow[ -]?control)\b", lowered))


def _interfaces(ssot: dict[str, Any]) -> list[dict[str, Any]]:
    io = ssot.get("io_list") if isinstance(ssot.get("io_list"), dict) else {}
    return [item for item in _as_list(io.get("interfaces")) if isinstance(item, dict)]


def _interface_ports(interface: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in _as_list(interface.get("ports")) if isinstance(item, dict)]


def _all_ports(ssot: dict[str, Any]) -> list[dict[str, Any]]:
    ports: list[dict[str, Any]] = []
    io = ssot.get("io_list") if isinstance(ssot.get("io_list"), dict) else {}
    for domain in _as_list(io.get("clock_domains")):
        if isinstance(domain, dict):
            ports.extend(item for item in _as_list(domain.get("ports")) if isinstance(item, dict))
    for reset in _as_list(io.get("resets")):
        if isinstance(reset, dict):
            ports.extend(item for item in _as_list(reset.get("ports")) if isinstance(item, dict))
    for interface in _interfaces(ssot):
        ports.extend(_interface_ports(interface))
    return ports


def _port_names(ports: list[dict[str, Any]]) -> set[str]:
    return {_text(port.get("name")) for port in ports if _text(port.get("name"))}


def _has_named_signal(names: set[str], fragments: tuple[str, ...]) -> bool:
    lowered = {name.lower() for name in names}
    return any(any(fragment in name for fragment in fragments) for name in lowered)


def _add_capability(caps: dict[str, dict[str, Any]], cap_id: str, source: str, evidence: str) -> None:
    entry = caps.setdefault(cap_id, {"id": cap_id, "sources": [], "evidence": []})
    if source and source not in entry["sources"]:
        entry["sources"].append(source)
    if evidence and evidence not in entry["evidence"]:
        entry["evidence"].append(evidence)


def _derive_capabilities(ssot: dict[str, Any], goals: dict[str, Any]) -> list[dict[str, Any]]:
    caps: dict[str, dict[str, Any]] = {}
    interfaces = _interfaces(ssot)
    ports = _all_ports(ssot)
    names = _port_names(ports)

    if interfaces:
        _add_capability(caps, "interface_protocol", "io_list.interfaces", "interface ports and role/type declarations")
    if _has_named_signal(names, ("valid",)) and _has_named_signal(names, ("ready",)):
        _add_capability(caps, "ready_valid_handshake", "io_list.interfaces", "valid/ready signal names")
    if _has_named_signal(names, ("req",)) and _has_named_signal(names, ("ack", "grant", "gnt")):
        _add_capability(caps, "request_ack_handshake", "io_list.interfaces", "req/ack-like signal names")
    if _has_named_signal(names, ("last", "som", "eom", "sof", "eof", "tlast")):
        _add_capability(caps, "packet_boundary", "io_list.interfaces", "packet/frame boundary signal names")
    if _has_named_signal(names, ("tdata", "tvalid", "tready", "tlast", "data_i", "data_o")):
        _add_capability(caps, "streaming_data", "io_list.interfaces", "stream-like data/control names")
    has_spi_like = (
        _has_named_signal(names, ("sclk", "sck", "spi_clk"))
        and _has_named_signal(names, ("mosi", "miso", "sdio"))
        and _has_named_signal(names, ("cs", "ss_n", "cs_n", "chip_select"))
    )
    has_uart_like = _has_named_signal(names, ("tx", "uart_tx", "rxd", "rx", "uart_rx"))
    if has_spi_like:
        _add_capability(caps, "serial_shift_protocol", "io_list.interfaces", "SPI-like serial clock/data/select signal names")
    if has_uart_like:
        _add_capability(caps, "serial_shift_protocol", "io_list.interfaces", "UART-like serial tx/rx signal names")
        _add_capability(caps, "uart_frame_protocol", "io_list.interfaces", "UART-like serial tx/rx signal names")
    if _has_named_signal(names, ("cs", "ss_n", "cs_n", "chip_select")):
        _add_capability(caps, "chip_select_protocol", "io_list.interfaces", "chip-select signal names")

    for interface in interfaces:
        itype = _text(interface.get("type")).lower()
        source = f"io_list.interfaces.{_text(interface.get('name')) or 'unnamed'}"
        if any(token in itype for token in ("apb", "axi", "ahb", "wishbone", "csr", "register")):
            _add_capability(caps, "bus_transaction", source, f"interface type {interface.get('type')}")
        if any(token in itype for token in ("stream", "axis", "avalon-st", "packet")):
            _add_capability(caps, "streaming_data", source, f"interface type {interface.get('type')}")
        if any(token in itype for token in ("spi", "serial", "uart")):
            _add_capability(caps, "serial_shift_protocol", source, f"interface type {interface.get('type')}")
        if "uart" in itype:
            _add_capability(caps, "uart_frame_protocol", source, f"interface type {interface.get('type')}")

    registers = ssot.get("registers") if isinstance(ssot.get("registers"), dict) else {}
    if _as_list(registers.get("register_list")):
        _add_capability(caps, "register_state", "registers.register_list", "declared register state")

    memory = ssot.get("memory") if isinstance(ssot.get("memory"), dict) else {}
    if _as_list(memory.get("instances")):
        _add_capability(caps, "memory_state", "memory.instances", "declared memories")

    interrupts = ssot.get("interrupts") if isinstance(ssot.get("interrupts"), dict) else {}
    if _as_list(interrupts.get("sources")) or interrupts.get("output"):
        _add_capability(caps, "interrupt_behavior", "interrupts", "interrupt source/output declaration")

    fsm = ssot.get("fsm")
    if isinstance(fsm, dict) and fsm:
        _add_capability(caps, "fsm_state", "fsm", "declared FSM")

    cycle = ssot.get("cycle_model") if isinstance(ssot.get("cycle_model"), dict) else {}
    pipeline = _as_list(cycle.get("pipeline"))
    if len(pipeline) > 1:
        _add_capability(caps, "multi_cycle_timing", "cycle_model.pipeline", f"pipeline stages={len(pipeline)}")
    latency = cycle.get("latency") if isinstance(cycle.get("latency"), dict) else {}
    if any(isinstance(item, dict) and int(item.get("max_cycles") or 0) > 1 for item in latency.values()):
        _add_capability(caps, "multi_cycle_timing", "cycle_model.latency", "latency max_cycles > 1")
    backpressure_items = [_text(item) for item in _as_list(cycle.get("backpressure")) if _text(item)]
    if any(not _is_negative_backpressure_statement(item) for item in backpressure_items):
        _add_capability(caps, "backpressure", "cycle_model.backpressure", " ".join(backpressure_items)[:120])

    dataflow = ssot.get("dataflow") if isinstance(ssot.get("dataflow"), dict) else {}
    if _as_list(dataflow.get("sequence")):
        _add_capability(caps, "datapath_transform", "dataflow.sequence", "declared dataflow sequence")

    error_handling = ssot.get("error_handling") if isinstance(ssot.get("error_handling"), dict) else {}
    error_sources = _as_list(error_handling.get("error_sources"))
    if any(isinstance(item, dict) and _text(item.get("id")).upper() not in {"", "ERR_NONE"} for item in error_sources):
        _add_capability(caps, "error_path", "error_handling.error_sources", "declared non-trivial error path")

    debug = ssot.get("debug_observability") if isinstance(ssot.get("debug_observability"), dict) else {}
    if _as_list(debug.get("signals")):
        _add_capability(caps, "debug_observability", "debug_observability.signals", "declared debug signals")

    goals_list = _as_list(goals.get("goals"))
    if any(isinstance(goal, dict) and isinstance(goal.get("scope"), dict) for goal in goals_list):
        _add_capability(caps, "module_equivalence", "verify.equivalence_goals", "module-scoped goals present")

    return sorted(caps.values(), key=lambda item: item["id"])


def _derive_observables(ssot: dict[str, Any], goals: dict[str, Any]) -> dict[str, Any]:
    ports = _all_ports(ssot)
    output_ports = sorted(
        {
            _text(port.get("name"))
            for port in ports
            if _text(port.get("name")) and _text(port.get("direction")).lower() == "output"
        }
    )

    rule_ports: set[str] = set()
    fm = ssot.get("function_model") if isinstance(ssot.get("function_model"), dict) else {}
    for txn in _as_list(fm.get("transactions")):
        if not isinstance(txn, dict):
            continue
        for rule in _as_list(txn.get("output_rules")):
            if isinstance(rule, dict):
                port = _text(rule.get("port") or rule.get("name"))
                if port:
                    rule_ports.add(port)

    goal_observables: set[str] = set()
    for goal in _as_list(goals.get("goals")):
        if not isinstance(goal, dict):
            continue
        contract = goal.get("expected_contract") if isinstance(goal.get("expected_contract"), dict) else {}
        for item in _as_list(contract.get("observables")):
            if isinstance(item, str) and SIGNAL_RE.fullmatch(item.strip()):
                goal_observables.add(item.strip().split("[", 1)[0])

    debug = ssot.get("debug_observability") if isinstance(ssot.get("debug_observability"), dict) else {}
    debug_signals = sorted(
        {
            _text(item.get("name"))
            for item in _as_list(debug.get("signals"))
            if isinstance(item, dict) and _text(item.get("name"))
        }
    )

    return {
        "required_rtl_observed": sorted(set(output_ports) | rule_ports | goal_observables),
        "debug_optional": debug_signals,
        "sources": ["io_list output ports", "function_model output_rules", "equivalence goal observables"],
    }


def _derive_monitors(capabilities: list[dict[str, Any]], ssot: dict[str, Any]) -> list[dict[str, Any]]:
    cap_ids = {cap["id"] for cap in capabilities}
    monitors = [
        {
            "id": "clock_reset_monitor",
            "required": True,
            "kind": "structural",
            "source": "io_list.clock_domains/io_list.resets",
        }
    ]
    if "interface_protocol" in cap_ids:
        for interface in _interfaces(ssot):
            name = _text(interface.get("name")) or "interface"
            monitors.append(
                {
                    "id": f"interface_monitor_{_slug(name)}",
                    "required": True,
                    "kind": "transaction",
                    "source": f"io_list.interfaces.{name}",
                }
            )
    if "ready_valid_handshake" in cap_ids:
        monitors.append({"id": "ready_valid_monitor", "required": True, "kind": "temporal", "source": "valid/ready ports"})
    if "request_ack_handshake" in cap_ids:
        monitors.append({"id": "request_ack_monitor", "required": True, "kind": "temporal", "source": "req/ack ports"})
    if "packet_boundary" in cap_ids:
        monitors.append({"id": "packet_boundary_monitor", "required": True, "kind": "temporal", "source": "boundary ports"})
    if "serial_shift_protocol" in cap_ids:
        monitors.append({"id": "serial_frame_monitor", "required": True, "kind": "temporal", "source": "serial clock/data/select ports"})
    if "uart_frame_protocol" in cap_ids:
        monitors.append({"id": "uart_frame_monitor", "required": True, "kind": "temporal", "source": "UART tx/rx serial frame ports"})
    if "chip_select_protocol" in cap_ids:
        monitors.append({"id": "chip_select_monitor", "required": True, "kind": "temporal", "source": "chip-select ports"})
    if "backpressure" in cap_ids:
        monitors.append({"id": "backpressure_monitor", "required": True, "kind": "temporal", "source": "cycle_model.backpressure"})
    if "interrupt_behavior" in cap_ids:
        monitors.append({"id": "interrupt_monitor", "required": True, "kind": "temporal", "source": "interrupts"})
    return monitors


def _derive_mutations(capabilities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cap_ids = {cap["id"] for cap in capabilities}
    mutations = [
        {"id": "operator_flip", "required": True, "supported_by_current_guard": True},
        {"id": "constant_flip", "required": True, "supported_by_current_guard": True},
        {"id": "comparator_flip", "required": True, "supported_by_current_guard": True},
    ]
    if {"register_state", "memory_state", "fsm_state"} & cap_ids:
        mutations.append({"id": "state_update_drop", "required": True, "supported_by_current_guard": True})
        mutations.append({"id": "reset_value_flip", "required": True, "supported_by_current_guard": False})
    if {"ready_valid_handshake", "request_ack_handshake", "backpressure"} & cap_ids:
        mutations.append({"id": "handshake_hold_drop", "required": True, "supported_by_current_guard": True})
    if "packet_boundary" in cap_ids:
        mutations.append({"id": "boundary_flag_flip", "required": True, "supported_by_current_guard": False})
    if "serial_shift_protocol" in cap_ids:
        mutations.append({"id": "bit_order_flip", "required": True, "supported_by_current_guard": True})
        mutations.append({"id": "serial_clock_edge_flip", "required": True, "supported_by_current_guard": True})
    if "uart_frame_protocol" in cap_ids:
        mutations.append({"id": "uart_start_stop_polarity_flip", "required": True, "supported_by_current_guard": True})
        mutations.append({"id": "serial_timing_flip", "required": True, "supported_by_current_guard": True})
    if "chip_select_protocol" in cap_ids:
        mutations.append({"id": "chip_select_polarity_flip", "required": True, "supported_by_current_guard": True})
    if "interrupt_behavior" in cap_ids:
        mutations.append({"id": "interrupt_clear_priority_flip", "required": True, "supported_by_current_guard": False})
    return mutations


def _derive_evidence(capabilities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cap_ids = {cap["id"] for cap in capabilities}
    evidence = [dict(item) for item in BASE_EVIDENCE]
    if {"ready_valid_handshake", "request_ack_handshake", "backpressure", "packet_boundary", "serial_shift_protocol", "chip_select_protocol"} & cap_ids:
        evidence.append(
            {
                "id": "protocol_assertions",
                "stage_id": "protocol_assertions",
                "artifact": "verify/protocol_assertions.sv",
                "required": False,
                "rationale": "Temporal interfaces need protocol checks; currently advisory unless generated.",
            }
        )
    if "multi_cycle_timing" in cap_ids:
        evidence.append(
            {
                "id": "cycle_measurement",
                "stage_id": "sim",
                "artifact": "sim/scoreboard_events.jsonl",
                "required": True,
                "rationale": "Multi-cycle behavior must be visible in cycle-indexed evidence.",
            }
        )
    if "debug_observability" in cap_ids:
        evidence.append(
            {
                "id": "debug_waveform",
                "stage_id": "sim",
                "artifact": "sim/*.vcd",
                "required": False,
                "rationale": "Debug observability is advisory unless failures require waveform inspection.",
            }
        )
    evidence.append(
        {
            "id": "mutation_guard",
            "stage_id": "mutation_guard",
            "artifact": "mutation/mutation_report.json",
            "required": False,
            "rationale": "Mutation kill-rate measures harness depth; enforcement is human policy.",
        }
    )
    return evidence


def derive_contract(ip: str, root: Path) -> dict[str, Any]:
    ip_dir = root / ip
    ssot_path = ip_dir / "yaml" / f"{ip}.ssot.yaml"
    if not ssot_path.is_file():
        raise SystemExit(f"[derive_ip_contract] FAIL: missing {ssot_path}")
    ssot = _read_yaml(ssot_path)
    goals = _read_json(ip_dir / "verify" / "equivalence_goals.json")

    capabilities = _derive_capabilities(ssot, goals)
    return {
        "schema_version": 1,
        "type": "ip_evidence_contract",
        "generation": "derived_from_ip_artifacts_not_static_profile",
        "generated_at": _utc(),
        "ip": ip,
        "source_artifacts": {
            "ssot": f"{ip}/yaml/{ip}.ssot.yaml",
            "equivalence_goals": f"{ip}/verify/equivalence_goals.json",
        },
        "capabilities": capabilities,
        "interfaces": [
            {
                "name": _text(interface.get("name")),
                "type": _text(interface.get("type")),
                "role": _text(interface.get("role")),
                "ports": sorted(_text(port.get("name")) for port in _interface_ports(interface) if _text(port.get("name"))),
            }
            for interface in _interfaces(ssot)
        ],
        "observability": _derive_observables(ssot, goals),
        "required_monitors": _derive_monitors(capabilities, ssot),
        "required_mutations": _derive_mutations(capabilities),
        "required_evidence": _derive_evidence(capabilities),
        "policy": {
            "locked_truth_changes_require_human": True,
            "no_static_profile_selection": True,
            "mutation_enforcement_requires_human_policy": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ip")
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    contract = derive_contract(args.ip, root)
    out_dir = root / args.ip / "verify"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "ip_contract.json"
    out_path.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        "[derive_ip_contract] PASS: "
        f"capabilities={len(contract['capabilities'])} "
        f"monitors={len(contract['required_monitors'])} "
        f"evidence={len(contract['required_evidence'])} "
        f"wrote={out_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
