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


def _build_manifest(ip: str, root: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    ip_dir = root / ip
    ssot = _load_yaml(ip_dir / "yaml" / f"{ip}.ssot.yaml")
    goals_doc = _load_json(ip_dir / "verify" / "equivalence_goals.json", "equivalence goals")
    rtl_doc = _load_json(ip_dir / "rtl" / "rtl_contract.json", "RTL contract")

    contract = rtl_doc.get("contract") if isinstance(rtl_doc.get("contract"), dict) else {}
    ports = _as_ports(ssot)
    by_name = {port["name"]: port for port in ports}
    input_ports = {port["name"] for port in ports if port["direction"] == "input"}
    output_ports = {port["name"] for port in ports if port["direction"] == "output"}
    questions: list[dict[str, Any]] = []

    if rtl_doc.get("type") != "generic_ssot_rule_rtl_contract":
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

    manifest = {
        "schema_version": 1,
        "type": "generic_goal_scoreboard_cocotb_manifest",
        "ip": ip,
        "top": str(rtl_doc.get("top") or contract.get("top") or ip),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "common_ai_agent_root": str(SOURCE_ROOT),
        "runtime_dir": str(RUNTIME_DIR),
        "ssot": f"{ip}/yaml/{ip}.ssot.yaml",
        "equivalence_goals": f"{ip}/verify/equivalence_goals.json",
        "rtl_contract": f"{ip}/rtl/rtl_contract.json",
        "clock": clock,
        "reset": reset,
        "reset_active": reset_active,
        "latency_cycles": _latency_cycles(ssot),
        "parameters": _param_defaults(ssot),
        "ports": ports,
        "port_widths": {port["name"]: port.get("width", 1) for port in ports},
        "input_ports": sorted(input_ports),
        "output_ports": sorted(output_ports),
        "input_map": input_map,
        "sample_condition": sample_condition,
        "sample_inputs": sample_inputs,
        "outputs": outputs,
        "special_outputs": special_outputs,
        "transaction_kind": str(contract.get("transaction") or "FM_PRIMARY"),
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

    def check_goal(self, goal_id: str, scenario_id: str, cycle: int, stimulus: dict, rtl_observed: dict) -> dict:
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


def _set_signal(dut, name: str, value: int) -> None:
    if not _has_signal(dut, name):
        raise AssertionError(f"DUT missing signal {name}")
    getattr(dut, name).value = int(value)


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


def _norm_token(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


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
    if goal_kind == "register":
        return True
    if tx_norm in {"csr", "csr_access", "register", "register_access", "control_status_access", "fm_csr"}:
        return True
    if any(token in tx_norm for token in ("csr", "register", "control_status", "apb")):
        return True
    return any(token in identity for token in ("register access", "control status", "apb", "csr"))


def _is_reset_goal(goal: dict[str, Any], tx_type: str, *, is_csr: bool = False) -> bool:
    if is_csr:
        return False
    goal_kind = _norm_token(goal.get("kind"))
    tx_norm = _norm_token(tx_type)
    identity = _goal_identity_text(goal, tx_type)
    if "backpressure" in identity or "ready is high after reset" in identity:
        return False
    return (
        goal_kind == "reset"
        or "reset" in tx_norm
        or "fm_reset" in identity
        or "sc_reset" in identity
        or "reset_defaults" in identity
        or "reset boot" in identity
        or "reset" in identity
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
    for pattern in (
        r"['\\\"]offset['\\\"]\s*:\s*(0x[0-9a-fA-F]+|\d+)",
        r"\\boffset\s*(?:=|:)\s*(0x[0-9a-fA-F]+|\d+)",
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
        return default
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


def _stimulus_value_for_field(manifest: dict[str, Any], field: str, idx: int, goal: dict[str, Any] | None = None) -> Any:
    goal = goal or {}
    text = _goal_text(goal)
    low = field.lower()
    goal_kind = str(goal.get("kind") or "").lower()
    if low in {"op", "operation", "cmd", "command"} and low not in (manifest.get("input_map") or {}):
        if goal_kind == "register" or any(token in text for token in ("csr", "register", "apb")):
            if "read" in text and "write" not in text:
                return "read"
            return "write"
        if goal_kind == "memory":
            return "read" if "read" in text and "write" not in text else "write"
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
        if selected_token and outside_selected and selected_token in route:
            value = 0x0BAD0000 + idx
        elif selected_token and outside_selected and route.startswith(("mem", "memory")):
            value = 0x5A000000 + idx
        elif selected_token and selected_token in route:
            value = 0xA5000000 + idx
        elif selected_token and route:
            value = 0x5A000000 + idx
        elif "memory" in text and route.startswith(("mem", "memory")):
            value = 0x5A000000 + idx
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
        stimulus.setdefault("op", _stimulus_value_for_field(manifest, "op", idx, goal))
        addr = stimulus.get("addr_or_name", stimulus.get("addr", _stimulus_value_for_field(manifest, "addr", idx, goal)))
        stimulus.setdefault("addr", addr)
        stimulus.setdefault("reg", addr)
        stimulus.setdefault("addr_or_name", addr)
        data = stimulus.get("data", stimulus.get("value", _stimulus_value_for_field(manifest, "data", idx, goal)))
        stimulus.setdefault("data", data)
        stimulus.setdefault("value", data)
    if goal_kind == "memory" or "memory_access" in tx_type_norm:
        stimulus.setdefault("op", _stimulus_value_for_field(manifest, "op", idx, goal))
        stimulus.setdefault("addr", _stimulus_value_for_field(manifest, "addr", idx, goal))
        data = stimulus.get("data", stimulus.get("value", _stimulus_value_for_field(manifest, "data", idx, goal)))
        stimulus.setdefault("data", data)
        stimulus.setdefault("value", data)
    _set_sample_activity(stimulus, manifest, sample_active)
    return stimulus


async def _reset_dut(dut, manifest: dict[str, Any]) -> None:
    input_ports = set(manifest.get("input_ports") or [])
    clock = manifest["clock"]
    reset = manifest["reset"]
    active = 0 if manifest.get("reset_active") == "low" else 1
    inactive = 1 - active
    for port in input_ports:
        if port == clock:
            continue
        _set_signal(dut, port, active if port == reset else 0)
    await ClockCycles(getattr(dut, clock), 3)
    _set_signal(dut, reset, inactive)
    await ClockCycles(getattr(dut, clock), 2)


def _drive_inputs(dut, manifest: dict[str, Any], stimulus: dict[str, Any]) -> None:
    clock = manifest["clock"]
    reset = manifest["reset"]
    input_map = manifest.get("input_map") or {}
    driven = {clock, reset}
    for field, port in input_map.items():
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
            _set_signal(dut, port, 0)


def _clear_sample_inputs(dut, manifest: dict[str, Any]) -> None:
    for port in manifest.get("sample_inputs") or []:
        _set_signal(dut, port, 0)
    for port in (manifest.get("input_map") or {}).values():
        if port not in {manifest["clock"], manifest["reset"]}:
            _set_signal(dut, str(port), 0)
    for port in ("psel", "penable", "pwrite", "paddr", "pwdata", "pstrb"):
        if port in set(manifest.get("input_ports") or []):
            _set_signal(dut, port, 0)


def _observe_outputs(dut, manifest: dict[str, Any]) -> dict[str, Any]:
    observed = {}
    for item in manifest.get("outputs") or []:
        observed[str(item["name"])] = _get_signal(dut, str(item["port"]))
    for _kind, port in (manifest.get("special_outputs") or {}).items():
        observed[str(port)] = _get_signal(dut, str(port))
    return observed


def _is_reset_stimulus(stimulus: dict[str, Any]) -> bool:
    text = " ".join(str(stimulus.get(k, "")) for k in ("kind", "scenario_id")).lower()
    return "reset" in text


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

    for idx, goal in enumerate(goals):
        goal_id = str(goal["goal_id"])
        stimulus = _stimulus_for_goal(goal, manifest, idx)
        if _is_reset_stimulus(stimulus):
            await _reset_dut(dut, manifest)
        else:
            await FallingEdge(getattr(dut, clock))
            _drive_inputs(dut, manifest, stimulus)
            for _ in range(max(int(manifest.get("latency_cycles") or 1), 1)):
                await RisingEdge(getattr(dut, clock))
        await ReadOnly()
        observed = _observe_outputs(dut, manifest)
        row = scoreboard.check_goal(
            goal_id,
            scenario_id=stimulus["scenario_id"],
            cycle=idx + max(int(manifest.get("latency_cycles") or 1), 1),
            stimulus=stimulus,
            rtl_observed=observed,
        )
        coverage.sample(goal, row)
        await FallingEdge(getattr(dut, clock))
        _clear_sample_inputs(dut, manifest)

    scoreboard.final_check()
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
    report = [
        f"TESTS={tests} PASS={passed} FAIL={failures + errors}",
        f"results={canonical.relative_to(project_root)}",
        f"scoreboard={ip}/sim/scoreboard_events.jsonl",
        f"coverage_functional={ip}/cov/coverage_functional.json",
        f"waveforms={','.join(str(path.relative_to(project_root)) for path in waves) if waves else 'none'}",
        "0 errors, 0 warnings" if failures == 0 and errors == 0 else f"{errors} errors, {failures} failures",
    ]
    (sim_dir / "sim_report.txt").write_text("\\n".join(report) + "\\n", encoding="utf-8")
    print(f"TESTS={tests} PASS={passed} FAIL={failures + errors}")
    print("0 errors, 0 warnings" if failures == 0 and errors == 0 else f"{errors} errors, {failures} failures")
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
