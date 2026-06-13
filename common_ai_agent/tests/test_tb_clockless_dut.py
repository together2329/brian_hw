from __future__ import annotations

import asyncio
import importlib.util
import json
import sys
import types
from pathlib import Path

import yaml


REPO = Path(__file__).resolve().parents[1]
EMIT = REPO / "workflow" / "tb-gen" / "scripts" / "emit_goal_scoreboard_cocotb.py"


def _emit_module():
    spec = importlib.util.spec_from_file_location("emit_goal_scoreboard_cocotb_clockless", EMIT)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def _write_clockless_ip(root: Path, ip: str) -> None:
    ip_dir = root / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "verify").mkdir()
    (ip_dir / "rtl").mkdir()
    (ip_dir / "list").mkdir()
    ssot = {
        "ip": ip,
        "top_module": {"name": ip},
        "ports": [
            {"name": "a", "direction": "input", "width": 1},
            {"name": "b", "direction": "input", "width": 1},
            {"name": "y", "direction": "output", "width": 1},
        ],
        "function_model": {"state_variables": []},
        "cycle_model": {"latency": 0},
    }
    contract = {
        "schema_version": 1,
        "type": "generic_ssot_rule_rtl_contract",
        "ip": ip,
        "top": ip,
        "contract": {
            "top": ip,
            "transaction": "xor",
            "kind": "combinational",
            "clock": "none",
            "reset": "none",
            "reset_active": "none",
            "sample_condition": "1'b1",
            "input_map": {"a": "a", "b": "b"},
            "outputs": [{"name": "xor_y", "port": "y", "expr": "a ^ b", "width": 1}],
            "state_vars": {},
            "latency_cycles": 0,
            "no_clock": True,
            "no_reset": True,
            "no_state": True,
            "no_latch": True,
            "no_protocol_timing": True,
        },
    }
    goals = {
        "goals": [
            {
                "goal_id": "EQ_XOR",
                "kind": "transaction",
                "stimulus_contract": {
                    "transaction_type": "xor",
                    "required_fields": ["a", "b"],
                },
            }
        ]
    }
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(yaml.safe_dump(ssot), encoding="utf-8")
    (ip_dir / "rtl" / "rtl_contract.json").write_text(json.dumps(contract), encoding="utf-8")
    (ip_dir / "verify" / "equivalence_goals.json").write_text(json.dumps(goals), encoding="utf-8")
    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        f"module {ip}(input logic a, input logic b, output logic y); assign y = a ^ b; endmodule\n",
        encoding="utf-8",
    )
    (ip_dir / "list" / f"{ip}.f").write_text(f"rtl/{ip}.sv\n", encoding="utf-8")


def test_manifest_accepts_explicit_clockless_resetless_contract(tmp_path):
    ip = "scratch_xor2_v1"
    _write_clockless_ip(tmp_path, ip)
    manifest, questions = _emit_module()._build_manifest(ip, tmp_path)

    assert questions == []
    assert manifest["clock"] == ""
    assert manifest["reset"] == ""
    assert manifest["reset_active"] == ""
    assert manifest["clockless"] is True
    assert manifest["resetless"] is True
    assert manifest["input_map"] == {"a": "a", "b": "b"}
    assert {"name": "xor_y", "port": "y", "width": 1} in manifest["outputs"]
    assert {"name": "y", "port": "y", "width": 1} in manifest["outputs"]


def test_emitted_tb_uses_timer_wait_for_clockless_dut():
    test_py = _emit_module().TEST_PY
    timer_calls: list[tuple[int, str]] = []
    rising_edges: list[object] = []

    async def _timer(delay, units="ns"):
        timer_calls.append((int(delay), str(units)))

    async def _rising_edge(signal):
        rising_edges.append(signal)

    cocotb = types.ModuleType("cocotb")
    cocotb.test = lambda *a, **k: (lambda fn: fn)
    binary = types.ModuleType("cocotb.binary")
    binary.BinaryValue = lambda value: value
    clock = types.ModuleType("cocotb.clock")
    clock.Clock = object
    triggers = types.ModuleType("cocotb.triggers")
    triggers.ReadOnly = lambda *a, **k: _timer(0)
    triggers.RisingEdge = lambda signal: _rising_edge(signal)
    triggers.Timer = lambda delay, units="ns": _timer(delay, units)
    saved = {k: sys.modules.get(k) for k in ("cocotb", "cocotb.binary", "cocotb.clock", "cocotb.triggers")}
    sys.modules.update({"cocotb": cocotb, "cocotb.binary": binary, "cocotb.clock": clock, "cocotb.triggers": triggers})
    try:
        ns: dict = {}
        exec(compile(test_py, "<TEST_PY>", "exec"), ns)
    finally:
        for key, value in saved.items():
            if value is None:
                sys.modules.pop(key, None)
            else:
                sys.modules[key] = value

    class _Signal:
        value = 0

    class _Dut:
        a = _Signal()
        b = _Signal()
        y = _Signal()

    manifest = {
        "clock": "",
        "reset": "",
        "reset_active": "",
        "input_ports": ["a", "b"],
        "output_ports": ["y"],
        "inout_ports": [],
        "input_map": {"a": "a", "b": "b"},
        "sample_inputs": [],
        "port_widths": {"a": 1, "b": 1, "y": 1},
    }

    asyncio.run(ns["_reset_dut"](_Dut(), manifest))
    asyncio.run(ns["_wait_cycle"](_Dut(), manifest))

    assert timer_calls
    assert rising_edges == []
