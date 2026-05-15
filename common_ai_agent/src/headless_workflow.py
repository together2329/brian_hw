#!/usr/bin/env python3
"""Headless ATLAS workflow runner for LLM-contract TDD.

The Web UI is a control surface; the workflow truth is the artifact contract
and the validators under workflow/.  This runner lets tests drive the same
stage scripts directly while swapping fake, cached, or real LLM providers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

import yaml

try:
    from src.workflow_stage_engine import WorkflowStageEngine, StageEngineResult
except ModuleNotFoundError:  # pragma: no cover - direct script execution fallback
    from workflow_stage_engine import WorkflowStageEngine, StageEngineResult


SOURCE_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_ROOT = SOURCE_ROOT / "workflow"
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))
PLACEHOLDER_RE = re.compile(r"\b(TBD|TODO|FIXME|PLACEHOLDER|STUB|MOCK)\b", re.IGNORECASE)
SSOT_REQUIRED_KEYS = [
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
DEFAULT_RTL_PACKET_MAX_PER_PASS = 4
REFERENCE_PROFILE_PROMPT_KEYS = (
    "path",
    "label",
    "summary",
    "target_candidate_basis",
    "target_candidate_summary",
    "suggested_ssot_target_scale",
    "guidance",
)
HEADLESS_STAGE_ALIASES = {
    "ssot": "ssot-gen",
    "ssot-gen": "ssot-gen",
    "fl-model": "fl-model-gen",
    "fl-model-gen": "fl-model-gen",
    "ssot-fl-model": "fl-model-gen",
    "cl-model": "cl-model-gen",
    "cycle-model": "cl-model-gen",
    "ssot-cycle-model": "cl-model-gen",
    "dual-fcov": "dual-fcov",
    "ssot-dual-fcov": "dual-fcov",
    "equiv-goals": "equiv-goals",
    "ssot-equiv-goals": "equiv-goals",
    "rtl": "rtl-gen",
    "rtl-gen": "rtl-gen",
    "ssot-rtl": "rtl-gen",
    "lint": "lint",
    "tb": "tb-gen",
    "tb-gen": "tb-gen",
    "ssot-tb-cocotb": "tb-gen",
    "coverage": "coverage",
    "cov": "coverage",
    "sim": "sim",
    "sim-debug": "sim-debug",
    "goal-audit": "goal-audit",
}


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _canonical_headless_stage(stage: str) -> str:
    return HEADLESS_STAGE_ALIASES.get(stage, stage)


def _sha(text: str | bytes) -> str:
    if isinstance(text, str):
        text = text.encode("utf-8")
    return hashlib.sha256(text).hexdigest()


RTL_TODO_HASH_VOLATILE_KEYS = {
    "connection_contract_suggestions",
    "generated_at",
    "gate",
    "manifest_hierarchy_evidence",
    "manifest_signal_flow_evidence",
    "owner_logic_evidence",
    "reference_profile",
    "reference_scale_gap",
    "rtl_implementation_depth_evidence",
    "rtl_placeholder_free_evidence",
    "static_evidence",
    "static_rtl_evidence",
    "todo_completion",
    "top_input_consumption_evidence",
    "top_io_contract_evidence",
    "top_output_drive_evidence",
}


def _stable_json_sha256(path: Path, *, volatile_keys: set[str] | None = None) -> str:
    volatile_keys = volatile_keys or RTL_TODO_HASH_VOLATILE_KEYS
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return ""

    def normalize(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                str(key): normalize(item)
                for key, item in value.items()
                if str(key) not in volatile_keys
            }
        if isinstance(value, list):
            return [normalize(item) for item in value]
        return value

    payload = json.dumps(normalize(data), sort_keys=True, separators=(",", ":"))
    return _sha(payload)


def _safe_name(value: str, fallback: str = "ip") -> str:
    text = re.sub(r"[^A-Za-z0-9_]+", "_", str(value or "")).strip("_")
    if not text or not re.match(r"^[A-Za-z]", text):
        text = fallback
    return text


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def _append_jsonl(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(data, sort_keys=True) + "\n")


def _clip(text: str, limit: int = 12000) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n... <truncated {len(text) - limit} chars>"


@dataclass
class LLMResponse:
    stage: str
    model: str
    raw_response: str
    parsed_artifacts: list[dict[str, Any]] = field(default_factory=list)
    usage: dict[str, Any] = field(default_factory=dict)
    finish_reason: str = ""
    error: str = ""
    status: str = "pass"

    def to_log(
        self,
        *,
        prompt: str,
        context: dict[str, Any],
        started_at: str,
        finished_at: str,
    ) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "model": self.model,
            "prompt_hash": _sha(prompt),
            "input_hash": _sha(json.dumps(context, sort_keys=True)),
            "output_hash": _sha(self.raw_response),
            "started_at": started_at,
            "finished_at": finished_at,
            "status": self.status,
            "raw_response": self.raw_response,
            "parsed_artifacts": self.parsed_artifacts,
            "usage": self.usage,
            "finish_reason": self.finish_reason,
            "error": self.error,
        }


class LLMProvider(Protocol):
    def complete(
        self,
        *,
        stage: str,
        model: str,
        system_prompt: str,
        prompt: str,
        context: dict[str, Any],
        output_schema: dict[str, Any] | None = None,
    ) -> LLMResponse:
        ...


def _structured_ssot_yaml(ip: str, requirement_text: str) -> str:
    excerpt = " ".join(requirement_text.split())[:240]
    doc = {
        "top_module": {"name": ip},
        "sub_modules": [
            {
                "name": ip,
                "file": f"rtl/{ip}.sv",
                "ownership": "manifest",
                "wiring_only": True,
                "implements": ["io_list", "integration"],
                "source_sections": ["io_list", "integration"],
                "description": "Top wrapper that connects external ports to the SSOT-owned core.",
            },
            {
                "name": f"{ip}_core",
                "file": f"rtl/{ip}_core.sv",
                "ownership": "manifest",
                "implements": ["function_model.transactions", "cycle_model", "rtl_contract"],
                "source_sections": ["function_model", "cycle_model", "rtl_contract", "fsm", "dataflow", "registers"],
                "function_model_refs": ["function_model.transactions.FM_PRIMARY"],
                "cycle_model_refs": ["cycle_model.pipeline"],
                "dataflow_refs": ["dataflow.sequence", "dataflow.ordering"],
                "register_refs": ["registers.architectural_state.accepted_count"],
                "fsm_refs": ["fsm.control"],
                "description": "Core RTL block implementing the sampled transaction rule.",
            }
        ],
        "parameters": [
            {"name": "DATA_WIDTH", "default": 8, "type": "int", "description": "Input data width."},
            {"name": "RESULT_WIDTH", "default": 9, "type": "int", "description": "Output result width."},
        ],
        "io_list": {
            "clock_domains": [
                {"name": "main", "ports": [{"name": "clk", "direction": "input", "width": 1}]}
            ],
            "resets": [
                {
                    "name": "rst_n",
                    "active": "low",
                    "ports": [{"name": "rst_n", "direction": "input", "width": 1}],
                }
            ],
            "interfaces": [
                {
                    "name": "rule_io",
                    "type": "custom",
                    "role": "target",
                    "clock_domain": "main",
                    "reset_domain": "rst_n",
                    "protocol": {
                        "acceptance": "A request is accepted when valid && ready is true on clk.",
                        "response": "result and result_valid are driven one cycle after the accepted request.",
                        "stability": "data_in is sampled only at acceptance; result remains traceable to that sampled value.",
                    },
                    "ports": [
                        {"name": "valid", "direction": "input", "width": 1},
                        {"name": "data_in", "direction": "input", "width": 8},
                        {"name": "result", "direction": "output", "width": 9},
                        {"name": "ready", "direction": "output", "width": 1},
                        {"name": "result_valid", "direction": "output", "width": 1},
                    ],
                }
            ],
        },
        "features": [
            {
                "name": "double_value",
                "description": "Sample data_in when valid is high and produce result=data_in*2 one cycle later.",
                "requirement_trace": excerpt,
            }
        ],
        "dataflow": {
            "sequence": [
                "Sample data_in when valid is asserted after reset release.",
                "Compute result as sampled value multiplied by two.",
                "Present result and result_valid on the next observable cycle.",
            ],
            "ordering": ["accepted request precedes result observation"],
        },
        "function_model": {
            "state_variables": [{"name": "accepted_count", "width": 8, "reset": 0}],
            "transactions": [
                {
                    "id": "FM_PRIMARY",
                    "name": "primary_behavior",
                    "required_fields": ["value"],
                    "preconditions": ["rst_n is deasserted", "valid is high"],
                    "outputs": ["result"],
                    "output_rules": [
                        {"name": "result", "port": "result", "expr": "value * 2", "width": 9}
                    ],
                    "side_effects": ["accepted_count increments on each sampled transaction"],
                    "state_updates": [
                        {"name": "accepted_count", "expr": "accepted_count + 1", "width": 8}
                    ],
                }
            ],
            "invariants": [
                "No result is produced before reset is released.",
                "Each accepted valid transaction produces exactly one result_valid observation.",
                "The result value is derived only from the sampled input transaction.",
            ],
            "reference_model_hint": "FunctionalModel.apply(value) returns result=value*2 and increments accepted_count.",
        },
        "cycle_model": {
            "executable": "pymtl3",
            "backend_policy": "Use PyMTL3 for the clocked cycle model shell; FunctionalModel remains the behavioral oracle.",
            "clock": "clk",
            "reset": "rst_n",
            "latency": 1,
            "handshake_rules": [
                {
                    "name": "valid_sample",
                    "description": "data_in is sampled only when valid is high; ready remains high after reset.",
                }
            ],
            "pipeline": [
                {"stage": "S0_SAMPLE", "cycle": 0, "action": "Sample data_in when valid is high."},
                {"stage": "S1_RESULT", "cycle": 1, "action": "Drive result and result_valid for the sampled value."},
            ],
            "ordering": [
                "Transactions are observed in the same order they are sampled.",
                "Reset clears pending valid output before any new transaction is accepted.",
            ],
            "backpressure": ["ready remains asserted in this one-deep sample rule IP."],
            "performance": {
                "frequency_mhz": 100,
                "throughput": {"sustained_beats_per_cycle": 1, "condition": "ready remains asserted"},
                "outstanding": {"max": 1, "description": "One sampled transaction at a time"},
                "depth": {"pipeline_stages": 2, "queue_depth": 1, "description": "Sample/result default cycle depth"},
            },
        },
        "clock_reset_domains": {
            "domains": [{"name": "main", "clock": "clk", "reset": "rst_n", "reset_active": "low"}],
        },
        "cdc_requirements": {"crossings": [], "rationale": "Single clock domain."},
        "rdc_requirements": {"crossings": [], "rationale": "Single reset domain."},
        "registers": {
            "no_registers": True,
            "policy": "No firmware-visible CSR/register map is required for this native valid/ready rule IP.",
            "register_list": [],
            "architectural_state": [{"name": "accepted_count", "reset": 0, "source": "function_model.state_variables"}],
        },
        "memory": {"instances": [], "rationale": "No memory required for the one-cycle datapath rule."},
        "interrupts": {"sources": [], "outputs": [], "rationale": "No interrupt behavior required for this rule IP."},
        "fsm": {
            "control": {
                "states": ["S0_SAMPLE", "S1_RESULT"],
                "reset_state": "S0_SAMPLE",
                "transitions": [
                    {"from": "S0_SAMPLE", "to": "S1_RESULT", "condition": "valid", "action": "Latch input value."},
                    {"from": "S1_RESULT", "to": "S0_SAMPLE", "condition": "next cycle", "action": "Emit result_valid."},
                ],
            }
        },
        "rtl_contract": {
            "clock": "clk",
            "reset": "rst_n",
            "reset_active": "low",
            "transaction": "FM_PRIMARY",
            "sample_condition": "valid && ready",
            "input_map": {"value": "data_in"},
            "output_map": {"result": "result", "valid": "result_valid"},
            "ready_output": "ready",
            "output_valid": "result_valid",
        },
        "timing": {
            "target_clocks": [{"name": "clk", "frequency_mhz": 100, "period_ns": 10.0}],
            "latency_budget": {"accepted_to_result_valid": {"min": 1, "max": 1, "unit": "cycles"}},
        },
        "power": {
            "domains": [{"name": "PD_MAIN", "clock_domains": ["main"], "isolation": "not_required"}],
            "power_states": [{"name": "ON", "entry": "reset deasserted", "exit": "reset asserted"}],
        },
        "security": {
            "classification": "non_secure_leaf_ip",
            "assets": [{"name": "result_integrity", "protection": "result must match function_model output rule"}],
            "threat_model": [{"threat": "silent datapath corruption", "mitigation": "FL-vs-RTL scoreboard checks every result"}],
        },
        "error_handling": {
            "error_sources": [{"id": "ERR_NONE", "condition": "No protocol error input exists", "architectural_effect": "No error output is asserted"}],
            "propagation": ["No error response interface exists for this simple rule IP."],
            "recovery": [{"action": "reset", "clears": ["accepted_count", "result_valid"]}],
        },
        "debug_observability": {
            "waveform_must_probe": ["clk", "rst_n", "valid", "data_in", "ready", "result", "result_valid", "accepted_count"],
            "trace_events": [
                {"name": "sample", "trigger": "valid && ready"},
                {"name": "result", "trigger": "result_valid"},
            ],
        },
        "integration": {
            "bus_attachment": {"type": "native_valid_ready_rule_io", "interfaces": ["rule_io"]},
            "dependencies": {"external_modules": [], "external_clocks": ["clk"], "external_resets": ["rst_n"]},
            "connections": [
                {"module": f"{ip}_core", "port": "clk", "signal": "clk"},
                {"module": f"{ip}_core", "port": "rst_n", "signal": "rst_n"},
                {"module": f"{ip}_core", "port": "valid", "signal": "valid"},
                {"module": f"{ip}_core", "port": "data_in", "signal": "data_in"},
                {"module": f"{ip}_core", "port": "ready", "signal": "ready"},
                {"module": f"{ip}_core", "port": "result", "signal": "result"},
                {"module": f"{ip}_core", "port": "result_valid", "signal": "result_valid"},
            ],
        },
        "dft": {
            "scan_required": False,
            "controllability": {"reset": "rst_n", "clock": "clk", "inputs": ["valid", "data_in"]},
            "observability": {"outputs": ["ready", "result", "result_valid"]},
        },
        "synthesis": {
            "dialect": "systemverilog_2012",
            "constraints": ["No inferred latches", "No unresolved black boxes"],
            "required_outputs": ["rtl compile log", "dut lint report", "syn/out/synth.v"],
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
            "conventions": ["Use sequential flops for registered outputs", "Use combinational defaults on all paths"],
            "lint_waivers": [],
        },
        "reuse_modules": [],
        "custom": {"assumptions": ["This fixture intentionally models a tiny generic transaction rule IP."]},
        "dir_structure": {
            "yaml_dir": "yaml/",
            "rtl_dir": "rtl/",
            "tb_dir": "tb/",
            "sim_dir": "sim/",
            "cov_dir": "cov/",
            "lint_dir": "lint/",
        },
        "filelist": {
            "rtl": [f"rtl/{ip}.sv", f"rtl/{ip}_core.sv"],
            "tb": [f"tb/cocotb/test_{ip}.py"],
            "coverage": ["cov/coverage.json"],
        },
        "test_requirements": {
            "scenarios": [
                {
                    "id": "SC_RULE_DOUBLE",
                    "name": "double sampled input",
                    "stimulus": "assert valid with data_in=13 after reset",
                    "expected": "result equals FunctionalModel result and result_valid pulses",
                    "checker": "EquivalenceScoreboard compares result observable against FunctionalModel.apply",
                    "coverage": ["FCOV_RULE_DOUBLE"],
                }
            ],
            "scoreboard_checks": 3,
            "coverage_goals": {
                "function": {
                    "target_pct": 100,
                    "model": "function_model",
                    "description": "Behavioral coverage for function_model transaction results and state updates.",
                    "bins": [
                        {
                            "id": "FCOV_RULE_DOUBLE",
                            "source_ref": "function_model.transactions.RULE_DOUBLE",
                            "class": "transaction",
                            "description": "sampled data_in doubling rule observed",
                        }
                    ],
                },
                "cycle": {
                    "target_pct": 100,
                    "model": "cycle_model",
                    "description": "Cycle coverage for sample/result pipeline stages and valid/ready timing.",
                    "bins": [
                        {
                            "id": "CCOV_SAMPLE_RESULT_PIPELINE",
                            "source_ref": "cycle_model.pipeline",
                            "class": "pipeline_stage",
                            "description": "sample-to-result cycle path observed",
                        }
                    ],
                },
                "planned_bins": [
                    {
                        "id": "FCOV_RULE_DOUBLE",
                        "class": "datapath",
                        "coverage_domain": "function",
                        "source_ref": "function_model.transactions.RULE_DOUBLE",
                        "description": "sampled data_in doubling rule observed",
                    }
                ],
                "functional": "Legacy alias: coverage_goals.function and coverage_goals.cycle must both close.",
            },
        },
        "quality_gates": {
            "ssot": {"pass": "check_ssot_disk.sh exits 0", "evidence": ["check_ssot_disk.sh PASS"]},
            "rtl": {"pass": "RTL compiles and maps every declared port", "evidence": ["rtl_compile.json", "dut_lint.json"]},
            "dv": {"pass": "All scenarios pass with scoreboard evidence", "evidence": ["results.xml", "scoreboard_events.jsonl"]},
            "coverage": {"pass": "All planned functional bins are hit", "evidence": ["coverage.json"]},
            "eda": {"pass": "EDA checks are clean or explicitly waived", "evidence": ["lint report"]},
            "signoff": {"pass": "SSOT, RTL, lint, sim, and coverage gates pass", "evidence": ["goal audit"]},
        },
        "traceability": {
            "requirements": [f"{ip}/req/{ip}_requirements.md"],
            "llm_stage": "ssot-gen",
            "yaml_to_output": [
                {"yaml": "io_list", "output": "RTL ports and cocotb driver"},
                {"yaml": "function_model", "output": "FunctionalModel and scoreboard expected values"},
                {"yaml": "cycle_model", "output": "RTL latency and waveform checks"},
                {"yaml": "test_requirements", "output": "cocotb scenarios and coverage bins"},
            ],
        },
        "workflow_todos": {
            "rtl-gen": [
                {
                    "id": "RTL_RULE_DOUBLE",
                    "content": "Implement rule_double from the SSOT function and cycle model",
                    "detail": "Capture accepted data_in, produce result=data_in*2 at the declared cycle latency, and expose enough DUT evidence for FL-vs-RTL comparison.",
                    "criteria": [
                        "RTL updates only on the declared valid/ready acceptance event",
                        "RTL observed result equals FunctionalModel.apply for RULE_DOUBLE",
                        "DUT-only compile/lint and rtl_todo_plan audit pass after the final edit",
                    ],
                    "source_refs": ["function_model.transactions.RULE_DOUBLE", "cycle_model.pipeline"],
                    "owner_module": f"{ip}_core",
                    "owner_file": f"rtl/{ip}_core.sv",
                    "priority": "high",
                    "required": True,
                }
            ],
            "tb-gen": [],
            "sim_debug": [],
        },
        "generation_flow": {
            "steps": [
                {"name": "validate_ssot", "command": f"bash workflow/ssot-gen/scripts/check_ssot_disk.sh {ip}", "description": "Validate production SSOT structure."},
                {"name": "handoff_fl_model", "command": f"/ssot-fl-model {ip}", "description": "Generate function model from SSOT."},
                {"name": "handoff_rtl", "command": f"/ssot-rtl {ip}", "description": "Generate RTL from SSOT."},
                {"name": "handoff_tb", "command": f"/ssot-tb-cocotb {ip}", "description": "Generate cocotb tests from SSOT."},
            ],
        },
    }
    return yaml.safe_dump(doc, sort_keys=False)


def _json_artifact_response(stage: str, model: str, files: list[dict[str, str]]) -> LLMResponse:
    raw = json.dumps({"files": files}, indent=2)
    return LLMResponse(stage=stage, model=model, raw_response=raw, parsed_artifacts=files)


def _fake_rtl_contract(ip: str) -> str:
    doc = {
        "schema_version": 1,
        "type": "generic_ssot_rule_rtl_contract",
        "top": ip,
        "contract": {
            "top": ip,
            "transaction": "FM_PRIMARY",
            "clock": "clk",
            "reset": "rst_n",
            "reset_active": "low",
            "sample_condition": "valid && ready",
            "input_map": {"value": "data_in"},
            "outputs": [
                {
                    "name": "result",
                    "port": "result",
                    "expr": "value * 2",
                    "width": 9,
                    "source": {"name": "result", "port": "result", "expr": "value * 2", "width": 9},
                }
            ],
            "state_vars": {"accepted_count": {"width": 8, "reset": 0}},
            "state_updates": [
                {
                    "name": "accepted_count",
                    "expr": "accepted_count + 1",
                    "source": {"name": "accepted_count", "expr": "accepted_count + 1", "width": 8},
                }
            ],
            "special_outputs": {"ready_output": "ready", "output_valid": "result_valid"},
            "source": "headless fake LLM artifact for contract TDD",
        },
    }
    return json.dumps(doc, indent=2, sort_keys=True) + "\n"


def _fake_rtl_source(ip: str) -> str:
    return f'''`default_nettype none

module {ip} (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       valid,
    input  wire [7:0] data_in,
    output wire [8:0] result,
    output wire       ready,
    output wire       result_valid
);
    {ip}_core u_core (
        .clk(clk),
        .rst_n(rst_n),
        .valid(valid),
        .data_in(data_in),
        .result(result),
        .ready(ready),
        .result_valid(result_valid)
    );
endmodule

`default_nettype wire
'''


def _fake_rtl_core_source(ip: str) -> str:
    return f'''`default_nettype none

module {ip}_core (
    input  wire       clk,
    input  wire       rst_n,
    input  wire       valid,
    input  wire [7:0] data_in,
    output reg  [8:0] result,
    output reg        ready,
    output reg        result_valid
);
    reg [7:0] accepted_count;

    wire feature_double_value = valid;
    wire dataflow_sequence = feature_double_value;
    wire function_model_transactions_FM_PRIMARY = dataflow_sequence;
    wire cycle_model_pipeline_S0_SAMPLE = function_model_transactions_FM_PRIMARY;
    wire cycle_model_pipeline_S1_RESULT = cycle_model_pipeline_S0_SAMPLE;
    wire fsm_control_S0_SAMPLE = cycle_model_pipeline_S1_RESULT;
    wire fsm_control_S1_RESULT = fsm_control_S0_SAMPLE;
    wire coverage_FCOV_RULE_DOUBLE = fsm_control_S1_RESULT;
    wire quality_gates_rtl = coverage_FCOV_RULE_DOUBLE;
    wire workflow_todos_rtl_gen = quality_gates_rtl;
    wire ssot_evidence_keep = workflow_todos_rtl_gen;

    wire sample_condition_valid_ready = valid && ready;
    wire [8:0] function_model_result = {{1'b0, data_in}} << 1;

    always @* begin
        ready = 1'b0;
        if (rst_n) begin
            ready = 1'b1 | (ssot_evidence_keep & 1'b0);
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            result <= 9'd0;
            result_valid <= 1'b0;
            accepted_count <= 8'd0;
        end else begin
            result_valid <= sample_condition_valid_ready;
            if (sample_condition_valid_ready) begin
                result <= function_model_result;
                accepted_count <= accepted_count + 8'd1;
            end
        end
    end
endmodule

`default_nettype wire
'''


def _fake_rtl_artifacts(ip: str, context: dict[str, Any]) -> list[dict[str, str]]:
    root = Path(str(context.get("root") or "."))
    todo_hash = str(context.get("rtl_todo_plan_sha256") or "").strip()
    if not todo_hash:
        todo_hash = _stable_json_sha256(root / ip / "rtl" / "rtl_todo_plan.json")
    provenance = {
        "schema_version": 1,
        "type": "rtl_authoring_provenance",
        "agent": "common_ai_agent",
        "workflow": "rtl-gen",
        "surface": "headless_common_engine",
        "todo_plan_sha256": todo_hash,
        "rtl_files": [f"rtl/{ip}.sv", f"rtl/{ip}_core.sv"],
        "contract_files": ["rtl/rtl_contract.json"],
        "generation_note": "Fake LLM provider artifact used only for headless TDD.",
    }
    return [
        {"path": f"{ip}/rtl/{ip}.sv", "content": _fake_rtl_source(ip), "kind": "rtl"},
        {"path": f"{ip}/rtl/{ip}_core.sv", "content": _fake_rtl_core_source(ip), "kind": "rtl"},
        {"path": f"{ip}/list/{ip}.f", "content": f"rtl/{ip}.sv\nrtl/{ip}_core.sv\n", "kind": "filelist"},
        {"path": f"{ip}/rtl/rtl_contract.json", "content": _fake_rtl_contract(ip), "kind": "rtl_contract"},
        {
            "path": f"{ip}/rtl/rtl_authoring_provenance.json",
            "content": json.dumps(provenance, indent=2, sort_keys=True) + "\n",
            "kind": "rtl_authoring_provenance",
        },
    ]


class FakeLLMProvider:
    """Deterministic provider for CI and TDD red/green loops."""

    def __init__(self, scenario: str = "valid", stage_responses: dict[str, str] | None = None) -> None:
        self.scenario = scenario
        self.stage_responses = stage_responses or {}
        self.calls: list[dict[str, Any]] = []

    def complete(
        self,
        *,
        stage: str,
        model: str,
        system_prompt: str,
        prompt: str,
        context: dict[str, Any],
        output_schema: dict[str, Any] | None = None,
    ) -> LLMResponse:
        self.calls.append({"stage": stage, "model": model, "prompt_hash": _sha(prompt)})
        ip = _safe_name(str(context.get("ip") or "headless_ip"), "headless_ip")
        if stage in self.stage_responses:
            raw = self.stage_responses[stage]
            return LLMResponse(
                stage=stage,
                model=model,
                raw_response=raw,
                parsed_artifacts=parse_llm_artifacts(stage, raw, ip=ip),
            )
        if stage == "ssot-gen" and self.scenario == "human_gate":
            raw = json.dumps(
                {
                    "human_gate": {
                        "decision_needed": "Define the invalid transaction response value before SSOT can be approved.",
                        "evidence": {"requirement_refs": [f"{ip}/req/{ip}_requirements.md"]},
                        "options": [
                            {"id": "A", "description": "Return zero with error response", "impact": "RTL/TB check zero data"},
                            {"id": "B", "description": "Hold previous value with error response", "impact": "RTL/TB check retention"},
                        ],
                        "recommended_default": {"id": "A", "reason": "deterministic and easier to verify"},
                        "downstream_effect": ["function_model.transactions", "rtl_contract", "tb scoreboard"],
                    }
                },
                indent=2,
            )
            return LLMResponse(stage=stage, model=model, raw_response=raw, status="human_gate")
        if stage == "ssot-gen":
            ssot = _structured_ssot_yaml(ip, str(context.get("requirement_text") or ""))
            if self.scenario == "missing_cycle_model":
                doc = yaml.safe_load(ssot)
                doc.pop("cycle_model", None)
                ssot = yaml.safe_dump(doc, sort_keys=False)
            return _json_artifact_response(
                stage,
                model,
                [{"path": f"{ip}/yaml/{ip}.ssot.yaml", "content": ssot, "kind": "ssot"}],
            )
        if stage == "rtl-gen":
            return _json_artifact_response(stage, model, _fake_rtl_artifacts(ip, context))
        return LLMResponse(
            stage=stage,
            model=model,
            raw_response=json.dumps({"ack": stage, "status": "ready"}, indent=2),
            parsed_artifacts=[],
        )


class CachedLLMProvider:
    """Replay raw GLM-5.1 responses from disk without a live model call."""

    def __init__(self, fixture_dir: str | Path, model: str = "glm-5.1") -> None:
        self.fixture_dir = Path(fixture_dir)
        self.model = model

    def _raw_path(self, stage: str) -> Path:
        stage_path = self.fixture_dir / stage / "raw_response.txt"
        if stage_path.is_file():
            return stage_path
        return self.fixture_dir / "raw_response.txt"

    def complete(
        self,
        *,
        stage: str,
        model: str,
        system_prompt: str,
        prompt: str,
        context: dict[str, Any],
        output_schema: dict[str, Any] | None = None,
    ) -> LLMResponse:
        path = self._raw_path(stage)
        if not path.is_file():
            return LLMResponse(
                stage=stage,
                model=model,
                raw_response="",
                error=f"cached response missing: {path}",
                status="blocked",
            )
        raw = path.read_text(encoding="utf-8")
        ip = _safe_name(str(context.get("ip") or "headless_ip"), "headless_ip")
        return LLMResponse(
            stage=stage,
            model=model or self.model,
            raw_response=raw,
            parsed_artifacts=parse_llm_artifacts(stage, raw, ip=ip),
        )


class RealLLMProvider:
    """Live provider lane for the configured ATLAS LLM backend.

    A required_model can still be supplied for GLM-only regression lanes, but
    the default path follows the requested --model. GPT-5.x models use the same
    opencode/Codex OAuth credential path as the ATLAS backend.
    """

    def __init__(self, required_model: str = "", timeout_s: int | None = None) -> None:
        self.required_model = required_model
        self.timeout_s = int(timeout_s or os.getenv("ATLAS_HEADLESS_LLM_TIMEOUT", "180"))
        self.retry_count = max(0, int(os.getenv("ATLAS_HEADLESS_LLM_RETRIES", "2")))
        self.retry_backoff_s = max(0.0, float(os.getenv("ATLAS_HEADLESS_LLM_RETRY_BACKOFF_S", "2.0")))

    def _activate_requested_model(self, model: str) -> tuple[str, str]:
        """Resolve profile-style --model values before live provider calls."""

        requested = str(model or "").strip()
        if not requested:
            return requested, ""
        try:
            try:
                from src import config
            except ModuleNotFoundError:
                import config
            if getattr(config, "is_cli_backend_model", lambda _name: False)(requested):
                if config.activate_cli_backend(requested):
                    return str(config.MODEL_NAME or requested), ""
            if config.set_active_profile(requested):
                return str(config.MODEL_NAME or requested), requested
        except Exception:
            return requested, ""
        return requested, ""

    def available_reason(self, model: str) -> str:
        if self.required_model and model != self.required_model:
            return f"required model {self.required_model}, got {model}"
        if os.getenv("ATLAS_RUN_REAL_LLM_TDD") != "1":
            return "ATLAS_RUN_REAL_LLM_TDD=1 is not set"
        resolved_model, _profile = self._activate_requested_model(model)
        model_l = (resolved_model or "").lower()
        if model_l in {"cursor-cli", "cursor-agent"} or model_l.startswith("cursor-cli"):
            return "" if shutil.which("cursor-agent") else "cursor-agent not found in PATH"
        if model_l in {"claude-cli", "claude"} or model_l.startswith("claude-cli"):
            return "" if shutil.which("claude") else "claude not found in PATH"
        if model_l.startswith("openai/"):
            model_l = model_l.split("/", 1)[1]
        if model_l.startswith("gpt-5") or ("gpt" in model_l and "codex" in model_l):
            try:
                try:
                    from src.opencode_backend import get_credentials
                except ModuleNotFoundError:  # direct script execution fallback
                    from opencode_backend import get_credentials

                cred = get_credentials("openai")
            except Exception as exc:
                return f"cannot load opencode/Codex OAuth credential: {exc}"
            if not (cred and cred.get("access")):
                return "no opencode/Codex OAuth credential found; run `python -m src.opencode_backend login`"
            return ""
        if not (
            os.getenv("ZAI_API_KEY")
            or os.getenv("LLM_API_KEY")
            or os.getenv("PROFILE_glm_API_KEY")
            or os.getenv("OPENAI_API_KEY")
            or os.getenv("ANTHROPIC_API_KEY")
        ):
            return "no live API key found in process environment"
        return ""

    def complete(
        self,
        *,
        stage: str,
        model: str,
        system_prompt: str,
        prompt: str,
        context: dict[str, Any],
        output_schema: dict[str, Any] | None = None,
    ) -> LLMResponse:
        blocker = self.available_reason(model)
        if blocker:
            return LLMResponse(stage=stage, model=model, raw_response="", error=blocker, status="blocked")
        resolved_model, profile_name = self._activate_requested_model(model)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]
        stage_max_tokens = int(os.getenv(f"ATLAS_HEADLESS_LLM_MAX_TOKENS_{stage.upper().replace('-', '_')}", "0") or 0)
        default_max_tokens = int(os.getenv("ATLAS_HEADLESS_LLM_MAX_TOKENS", "12000"))
        request = {
            "messages": messages,
            "model": resolved_model or model,
            "profile": profile_name,
            "caller_tag": f"headless.{stage}",
            "max_tokens": stage_max_tokens if stage_max_tokens > 0 else default_max_tokens,
        }
        if str(resolved_model or model).lower() in {"claude-cli", "claude"}:
            # Let the Claude backend own timeout cleanup.  If the outer
            # subprocess timeout fires first, Claude Code can remain as an
            # orphaned detached child because the backend starts it in a new
            # process session.
            request["claude_cli_timeout_sec"] = max(1, self.timeout_s - 30)
        if output_schema and os.getenv("ATLAS_HEADLESS_LLM_JSON_MODE", "1") != "0":
            request["extra_body"] = {"response_format": {"type": "json_object"}}
        child_code = r'''
import json
import sys
from pathlib import Path

source_root = Path.cwd()
for candidate in (source_root, source_root / "src"):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))
req = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
try:
    try:
        from src import config
    except ModuleNotFoundError:
        import config
    profile = str(req.get("profile") or "").strip()
    if profile:
        config.set_active_profile(profile)
        req["model"] = config.MODEL_NAME
    elif config.set_active_profile(req["model"]):
        req["model"] = config.MODEL_NAME
    elif getattr(config, "is_cli_backend_model", lambda _name: False)(req["model"]):
        config.activate_cli_backend(req["model"])
        req["model"] = config.MODEL_NAME
    elif config.is_opencode_model(req["model"]):
        config.activate_opencode_oauth(req["model"])
    if req.get("claude_cli_timeout_sec") and getattr(config, "CLAUDE_CLI_ENABLE", False):
        _timeout = int(req["claude_cli_timeout_sec"])
        config.CLAUDE_CLI_TIMEOUT_SEC = _timeout
        import os
        os.environ["CLAUDE_CLI_TIMEOUT_SEC"] = str(_timeout)
    from src.llm_client import call_llm_raw, get_last_usage
    try:
        from lib.model_pricing import get_active_pricing
    except Exception:
        get_active_pricing = None
    raw = call_llm_raw(
        messages=req["messages"],
        temperature=0.1,
        model=req["model"],
        caller_tag=req.get("caller_tag") or "headless",
        max_tokens=req.get("max_tokens"),
        extra_body=req.get("extra_body"),
    )
    usage = get_last_usage() or {}
    cost = {}
    try:
        if usage and get_active_pricing is not None:
            price = get_active_pricing()
            if price is not None:
                in_tok = int(usage.get("input", 0) or 0)
                out_tok = int(usage.get("output", 0) or 0)
                cache_tok = int(usage.get("cache_read", 0) or 0)
                billable_in = max(0, in_tok - cache_tok)
                cost_usd = (
                    billable_in * float(price.input)
                    + cache_tok * float(price.cache)
                    + out_tok * float(price.output)
                ) / 1_000_000.0
                cost = {
                    "usd": cost_usd,
                    "pricing_per_1m": {
                        "input": float(price.input),
                        "cache": float(price.cache),
                        "output": float(price.output),
                    },
                }
    except Exception:
        cost = {}
    print(json.dumps({"raw": raw, "usage": usage, "cost": cost, "error": ""}))
except BaseException as exc:
    print(json.dumps({"raw": "", "usage": {}, "cost": {}, "error": repr(exc)}))
    raise SystemExit(1)
'''
        last_error = ""
        last_raw = ""
        last_usage: dict[str, Any] = {}
        for attempt in range(self.retry_count + 1):
            with tempfile.TemporaryDirectory(prefix="atlas_headless_llm_") as tmp:
                req_path = Path(tmp) / "request.json"
                req_path.write_text(json.dumps(request), encoding="utf-8")
                try:
                    proc = subprocess.run(
                        [sys.executable, "-c", child_code, str(req_path)],
                        cwd=str(SOURCE_ROOT),
                        text=True,
                        capture_output=True,
                        timeout=self.timeout_s,
                    )
                except subprocess.TimeoutExpired:
                    last_error = f"real provider timed out after {self.timeout_s}s"
                    proc = None
                stdout = (proc.stdout or "").strip() if proc is not None else ""
                try:
                    payload = json.loads(stdout.splitlines()[-1]) if stdout else {}
                except Exception:
                    payload = {}

                payload_usage = payload.get("usage") if isinstance(payload.get("usage"), dict) else {}
                payload_cost = payload.get("cost") if isinstance(payload.get("cost"), dict) else {}
                combined_usage = dict(payload_usage)
                if payload_cost:
                    combined_usage["cost"] = payload_cost
                last_usage = combined_usage

                raw = str(payload.get("raw") or "")
                last_raw = raw
                if proc is not None and proc.returncode == 0 and str(raw or "").strip() and not str(raw).startswith("Error calling LLM:"):
                    break

                if proc is None:
                    last_error = last_error or f"real provider timed out after {self.timeout_s}s"
                elif proc.returncode != 0:
                    last_error = str(payload.get("error") or proc.stderr or f"real provider child exited {proc.returncode}")
                else:
                    last_error = str(raw or "empty output")

                should_retry = (
                    "Remote end closed connection without response" in last_error
                    or "timed out" in last_error.lower()
                    or not str(raw or "").strip()
                    or str(raw).startswith("Error calling LLM:")
                )
                if attempt < self.retry_count and should_retry:
                    time.sleep(self.retry_backoff_s * (attempt + 1))
                    continue
                return LLMResponse(
                    stage=stage,
                    model=resolved_model or model,
                    raw_response=last_raw,
                    usage=last_usage,
                    error=last_error or "real provider failed",
                    status="blocked",
                )

        combined_usage = last_usage
        raw = last_raw
        ip = _safe_name(str(context.get("ip") or "headless_ip"), "headless_ip")
        artifacts = parse_llm_artifacts(stage, str(raw), ip=ip)
        data = _json_from_text(str(raw)) or {}
        if isinstance(data.get("human_gate"), dict):
            return LLMResponse(stage=stage, model=resolved_model or model, raw_response=str(raw), error="model requested human_gate", status="human_gate")
        if stage in {"ssot-gen", "rtl-gen", "tb-gen"} and not artifacts:
            return LLMResponse(
                stage=stage,
                model=resolved_model or model,
                raw_response=str(raw),
                usage=combined_usage,
                error=f"model output did not contain expected JSON object with files[] {stage} artifact",
                status="blocked",
            )
        return LLMResponse(
            stage=stage,
            model=resolved_model or model,
            raw_response=str(raw),
            parsed_artifacts=artifacts,
            usage=combined_usage,
        )


def _json_from_text(text: str) -> dict[str, Any] | None:
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    candidates = [fenced.group(1)] if fenced else []
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end > start:
        candidates.append(text[start : end + 1])
    decoder = json.JSONDecoder()
    for candidate in candidates:
        try:
            data = json.loads(candidate)
        except Exception:
            try:
                data, _ = decoder.raw_decode(candidate.strip())
            except Exception:
                continue
        if isinstance(data, dict):
            return data
    for match in re.finditer(r"\{", text):
        try:
            data, _ = decoder.raw_decode(text[match.start() :].strip())
        except Exception:
            continue
        if isinstance(data, dict):
            return data
    return None


def _yaml_from_text(text: str) -> str:
    fenced = re.search(r"```(?:yaml|yml)\s*(.*?)\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        return fenced.group(1).strip() + "\n"
    if "top_module:" in text and "function_model:" in text:
        return text.strip() + "\n"
    return ""


def _response_declares_empty_files(response: LLMResponse) -> bool:
    data = _json_from_text(response.raw_response) or {}
    files = data.get("files")
    return isinstance(files, list) and not files


def parse_llm_artifacts(stage: str, raw_response: str, *, ip: str) -> list[dict[str, Any]]:
    data = _json_from_text(raw_response)
    if isinstance(data, dict):
        files = data.get("files")
        if isinstance(files, list):
            out = []
            for item in files:
                if isinstance(item, dict) and item.get("path") and "content" in item:
                    out.append({"path": str(item["path"]), "content": str(item["content"]), "kind": item.get("kind", stage)})
            return out
        if isinstance(data.get("ssot_yaml"), str):
            return [{"path": f"{ip}/yaml/{ip}.ssot.yaml", "content": data["ssot_yaml"], "kind": "ssot"}]
    yaml_text = _yaml_from_text(raw_response)
    if yaml_text and stage == "ssot-gen":
        return [{"path": f"{ip}/yaml/{ip}.ssot.yaml", "content": yaml_text, "kind": "ssot"}]
    return []


@dataclass
class StageResult:
    stage: str
    status: str
    message: str = ""
    returncode: int = 0
    artifacts: list[str] = field(default_factory=list)
    blocker: str = ""


@dataclass
class WorkflowResult:
    ip: str
    status: str
    stages: list[StageResult]
    root: str
    run_log: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "ip": self.ip,
            "status": self.status,
            "root": self.root,
            "run_log": self.run_log,
            "stages": [stage.__dict__ for stage in self.stages],
        }


class HeadlessWorkflowRunner:
    def __init__(
        self,
        *,
        root: str | Path,
        model: str = "",
        llm_provider: LLMProvider | None = None,
        require_glm51: bool = False,
    ) -> None:
        self.root = Path(root).resolve()
        self.model = model or os.getenv("ATLAS_HEADLESS_LLM_MODEL") or "glm-5.1"
        self.llm_provider = llm_provider or RealLLMProvider(required_model=os.getenv("ATLAS_HEADLESS_REQUIRED_MODEL", ""))
        self.require_glm51 = require_glm51
        self.stage_engine = WorkflowStageEngine(self.root, source_root=SOURCE_ROOT)
        self.stages: list[StageResult] = []
        self.ssot_repair_attempts = max(0, int(os.getenv("ATLAS_HEADLESS_SSOT_REPAIR_ATTEMPTS", "2")))
        self.rtl_repair_attempts = max(0, int(os.getenv("ATLAS_HEADLESS_RTL_REPAIR_ATTEMPTS", "2")))

    def _ip_dir(self, ip: str) -> Path:
        return self.root / ip

    def _log_dir(self, ip: str) -> Path:
        return self._ip_dir(ip) / "logs" / "llm"

    def _progress_log_path(self, ip: str) -> Path:
        return self._ip_dir(ip) / "logs" / "run_progress.jsonl"

    def _llm_trace_path(self, ip: str) -> Path:
        return self._ip_dir(ip) / "logs" / "llm_call_trace.jsonl"

    def _heartbeat_path(self, ip: str) -> Path:
        return self._ip_dir(ip) / "logs" / "heartbeat.json"

    def _write_progress(self, ip: str, event: str, **fields: Any) -> None:
        _append_jsonl(
            self._progress_log_path(ip),
            {
                "ts": _utc(),
                "event": event,
                **fields,
            },
        )

    def _write_heartbeat(self, ip: str, **fields: Any) -> None:
        _write_json(
            self._heartbeat_path(ip),
            {
                "ts": _utc(),
                **fields,
            },
        )

    def _question_path(self, ip: str, stage: str, topic: str) -> Path:
        return self._ip_dir(ip) / "questions" / f"{_safe_name(stage)}_{_safe_name(topic, 'decision')}.json"

    def _write_human_gate(
        self,
        ip: str,
        stage: str,
        topic: str,
        *,
        decision_needed: str,
        evidence: dict[str, Any] | None = None,
        options: list[dict[str, Any]] | None = None,
        recommended_default: dict[str, Any] | None = None,
        downstream_effect: list[str] | None = None,
    ) -> Path:
        path = self._question_path(ip, stage, topic)
        _write_json(
            path,
            {
                "stage": stage,
                "status": "human_gate",
                "decision_needed": decision_needed,
                "evidence": evidence or {"requirement_refs": [f"{ip}/req/{ip}_requirements.md"], "ssot_refs": [], "tool_logs": [], "goal_ids": []},
                "options": options or [
                    {"id": "A", "description": "Define the missing behavior in SSOT", "impact": "Regenerate FL/RTL/TB from updated SSOT"}
                ],
                "recommended_default": recommended_default or {"id": "A", "reason": "SSOT must own product semantics"},
                "downstream_effect": downstream_effect or ["SSOT", "functional_model", "RTL", "TB"],
                "created_at": _utc(),
            },
        )
        return path

    def _append(self, stage: str, status: str, message: str = "", returncode: int = 0, artifacts: list[str] | None = None, blocker: str = "") -> StageResult:
        result = StageResult(stage=stage, status=status, message=message, returncode=returncode, artifacts=artifacts or [], blocker=blocker)
        self.stages.append(result)
        return result

    def _append_engine_result(
        self,
        result: StageEngineResult,
        stage: str | None = None,
        *,
        artifacts: list[str] | None = None,
        blocker: str | None = None,
    ) -> StageResult:
        merged_artifacts = list(result.artifacts)
        if artifacts:
            merged_artifacts.extend(artifacts)
        return self._append(
            stage or result.stage,
            result.status,
            result.message,
            returncode=result.returncode,
            artifacts=merged_artifacts,
            blocker=blocker if blocker is not None else result.blocker,
        )

    def _copy_requirement(self, ip: str, requirement_path: Path) -> str:
        text = requirement_path.read_text(encoding="utf-8")
        req_dir = self._ip_dir(ip) / "req"
        req_dir.mkdir(parents=True, exist_ok=True)
        for name in (f"{ip}_requirements.md", "requirements.md"):
            (req_dir / name).write_text(text, encoding="utf-8")
        return text

    def _validate_req(self, ip: str, text: str) -> StageResult | None:
        if len(text.strip()) < 200 or PLACEHOLDER_RE.search(text):
            path = self._write_human_gate(
                ip,
                "req",
                "requirements",
                decision_needed="Provide substantive requirements without placeholder markers before SSOT generation.",
                evidence={"requirement_refs": [f"{ip}/req/{ip}_requirements.md"], "tool_logs": [], "goal_ids": [], "ssot_refs": []},
            )
            return self._append("req", "human_gate", "requirements are incomplete", artifacts=[str(path.relative_to(self.root))], blocker=str(path.relative_to(self.root)))
        return self._append("req", "pass", "requirements copied", artifacts=[f"{ip}/req/{ip}_requirements.md", f"{ip}/req/requirements.md"])

    def _stage_prompt(self, stage: str, ip: str, context: dict[str, Any]) -> tuple[str, str]:
        system_path = WORKFLOW_ROOT / stage / "system_prompt.md"
        workflow_stage = stage
        if stage == "rtl-gen":
            system_path = WORKFLOW_ROOT / "rtl-gen" / "system_prompt.md"
        elif stage == "tb-gen":
            system_path = WORKFLOW_ROOT / "tb-gen" / "system_prompt.md"
        elif stage == "ssot-gen":
            system_path = WORKFLOW_ROOT / "ssot-gen" / "system_prompt.md"
        system = system_path.read_text(encoding="utf-8", errors="replace") if system_path.is_file() else ""
        headless_contract = (
            "HEADLESS PROVIDER CONTRACT.\n"
            "You are being called by a headless artifact runner, not the interactive ATLAS tool loop. "
            "Do not emit Action:, write_file, run_command, todo_update, markdown fences, status prose, "
            "or a plan to create files. Return only the machine-readable JSON object requested by the "
            "user prompt. This headless JSON contract overrides any interactive tool-use wording below.\n\n"
        )
        if workflow_stage == "ssot-gen":
            system = headless_contract + system
            prompt = (
                f"Generate canonical SSOT YAML for {ip} from {ip}/req/{ip}_requirements.md.\n\n"
                "Return exactly one JSON object and nothing else. Do not wrap it in markdown.\n"
                "Valid success schema:\n"
                "{\n"
                '  "files": [\n'
                "    {\n"
                f'      "path": "{ip}/yaml/{ip}.ssot.yaml",\n'
                '      "kind": "ssot",\n'
                '      "content": "<complete YAML document as a JSON string>"\n'
                "    }\n"
                "  ]\n"
                "}\n\n"
                "The YAML content must be general IP SSOT, not a fixed template workaround. It must derive "
                "semantics from the requirements and include these top-level sections: "
                f"{', '.join(SSOT_REQUIRED_KEYS)}. function_model and cycle_model are mandatory and must be "
                "substantive enough for FL-vs-RTL equivalence goals, cocotb/pyuvm scoreboard generation, "
                "coverage planning, and mismatch ownership.\n\n"
                "The generated YAML must pass `bash workflow/ssot-gen/scripts/check_ssot_disk.sh "
                f"{ip}` without repair. Required validator details:\n"
                "- function_model.state_variables, function_model.transactions, and function_model.invariants "
                "must be non-empty lists.\n"
                "- Every function_model.transactions[] item must include id, name, preconditions, outputs, "
                "and either side_effects or error_cases. If state_updates exist, also summarize them in side_effects.\n"
                "- cycle_model must include clock, reset, latency, non-empty handshake_rules, non-empty pipeline, "
                "and non-empty ordering.\n"
                "- timing must include target_clocks and latency_budget.\n"
                "- power must include non-empty domains and power_states.\n"
                "- security must include classification, non-empty assets, and non-empty threat_model.\n"
                "- error_handling must include non-empty error_sources plus propagation and recovery.\n"
                "- debug_observability must include waveform_must_probe and trace_events.\n"
                "- integration must include bus_attachment and dependencies.\n"
                "- dft must include scan_required, controllability, and observability.\n"
                "- synthesis must include dialect, constraints, and required_outputs.\n"
                "- every test_requirements.scenarios[] item must include id, name, stimulus, expected, checker, and coverage.\n"
                "- quality_gates must be a mapping with ssot, rtl, dv, coverage, eda, and signoff; each gate "
                "must be a mapping with pass and evidence.\n"
                "- If quality_gates.rtl_gen.profile is production, or the IP is DMA330/PL330-class, "
                "quality_gates.rtl_gen must include pass/evidence and every manifest-owned child module "
                "must have machine-readable integration.connections or sub_modules[].connections records "
                "with module/port/signal fields.\n"
                "- traceability.yaml_to_output must be a non-empty list.\n\n"
                "- workflow_todos.rtl-gen must be a non-empty list of LLM-authored RTL TODOs. "
                "Each item must include id, content, detail, criteria, source_refs, priority, required, "
                "and owner_module/owner_file when inferable from sub_modules. These TODOs are the downstream "
                "rtl-gen work ledger and must be specific to this IP, not fixed boilerplate.\n\n"
                "If the requirements leave a semantic decision undefined, return exactly this JSON shape "
                "instead of files[]:\n"
                "{\n"
                '  "human_gate": {\n'
                '    "decision_needed": "<specific RTL-engineer decision>",\n'
                '    "evidence": {"requirement_refs": [], "ssot_refs": [], "tool_logs": [], "goal_ids": []},\n'
                '    "options": [{"label": "<option>", "effect": "<downstream effect>"}],\n'
                '    "recommended_default": {"label": "<option>", "why": "<reason>"},\n'
                '    "downstream_effect": ["function_model", "cycle_model", "rtl_contract", "tb scoreboard"]\n'
                "  }\n"
                "}\n\n"
                f"Requirements:\n{context.get('requirement_text', '')}"
            )
        elif workflow_stage == "rtl-gen":
            system = headless_contract + system
            prompt = (
                f"Prepare rtl-gen for {ip} using only {ip}/yaml/{ip}.ssot.yaml and "
                f"{context.get('rtl_todo_plan_path') or f'{ip}/rtl/rtl_todo_plan.json'}, "
                f"{context.get('rtl_authoring_plan_path') or f'{ip}/rtl/rtl_authoring_plan.json'}, "
                f"and packets under {context.get('rtl_authoring_packet_dir') or f'{ip}/rtl/authoring_packets'}. "
                "Return exactly one JSON object and nothing else. Success schema: "
                f'{{"files":[{{"path":"{ip}/rtl/<module>.sv","kind":"rtl","content":"<SystemVerilog>"}},'
                f'{{"path":"{ip}/rtl/rtl_contract.json","kind":"rtl_contract","content":"<JSON>"}},'
                f'{{"path":"{ip}/list/{ip}.f","kind":"filelist","content":"<filelist>"}}]}}. '
                "The script derives the TODO ledger from SSOT; the LLM must generate real RTL-owned "
                "artifacts that satisfy every TODO content/detail/criteria item and record provenance. "
                "Process one authoring packet at a time, module packets first, then unowned tasks if present, "
                "then rtl_gate_evidence_closure; skip rtl_gate_tool_evidence, rtl_gate_contract_blocked, "
                "and rtl_gate_human_closure until tool evidence or human-locked authority is available. "
                "Respect rtl_authoring_plan.execution_policy and each packet execution_policy: draft RTL may be "
                "authored while deferred_human_qa_allowed is true, but rtl-gen PASS/signoff is forbidden when "
                "pass_allowed is false. "
                "On repair attempts, use packet status_counts, open_required_count, Status, and Current reason "
                "fields to patch only the RTL-owned artifacts needed to close open TODOs. "
                f"Use todo_plan_sha256={context.get('rtl_todo_plan_sha256') or '<pending>'}. "
                "Repair only RTL-owned artifacts when validators fail. Do not change SSOT semantics, "
                "do not use fixed IP templates, and keep prompts focused on DUT-only compile/lint "
                "and FL-vs-RTL evidence. Production-profile RTL must also satisfy the SSOT-scaled "
                "rtl_implementation_depth_evidence gate; do not emit shallow shell modules that only "
                "name ports, instantiate children, or tie off outputs. If rtl_reference_profile is present, "
                "treat it as calibration-only scale evidence, never as source RTL or a clone template. "
                "If a missing locked-truth artifact, human authority approval, or SSOT connection contract "
                "prevents correct RTL authoring, return a human_gate JSON object instead of inventing semantics."
            )
        elif workflow_stage == "tb-gen":
            system = headless_contract + system
            prompt = (
                f"Prepare tb-gen for {ip} using {ip}/verify/equivalence_goals.json, "
                f"{ip}/model/functional_model.py, and {ip}/rtl/rtl_contract.json. "
                "Do not duplicate expected behavior by hand; scoreboard must call FunctionalModel."
            )
        else:
            prompt = f"Run {stage} for {ip} with artifact validators."
        return system, prompt

    def _call_llm(
        self,
        stage: str,
        ip: str,
        context: dict[str, Any],
        *,
        system_prompt: str | None = None,
        prompt: str | None = None,
        log_stage: str | None = None,
    ) -> LLMResponse:
        if self.require_glm51 and self.model != "glm-5.1":
            response = LLMResponse(
                stage=stage,
                model=self.model,
                raw_response="",
                error=f"GLM-5.1 lane requires model glm-5.1, got {self.model}",
                status="blocked",
            )
            self._write_llm_log(ip, log_stage or stage, response, prompt="", context=context, started_at=_utc(), finished_at=_utc())
            return response
        if system_prompt is None or prompt is None:
            system, default_prompt = self._stage_prompt(stage, ip, context)
            if system_prompt is None:
                system_prompt = system
            if prompt is None:
                prompt = default_prompt
        started = _utc()
        llm_start = time.time()
        self._write_progress(
            ip,
            "llm_call_start",
            stage=stage,
            log_stage=(log_stage or stage),
            model=self.model,
        )
        self._write_heartbeat(
            ip,
            state="running",
            phase="llm_call",
            stage=stage,
            log_stage=(log_stage or stage),
            model=self.model,
        )
        response = self.llm_provider.complete(
            stage=stage,
            model=self.model,
            system_prompt=system_prompt,
            prompt=prompt,
            context=context,
            output_schema={"type": "artifact_files_or_human_gate"},
        )
        llm_elapsed = time.time() - llm_start
        finished = _utc()
        self._write_llm_log(ip, log_stage or stage, response, prompt=prompt, context=context, started_at=started, finished_at=finished)
        _append_jsonl(
            self._llm_trace_path(ip),
            {
                "ts": finished,
                "stage": stage,
                "log_stage": (log_stage or stage),
                "model": self.model,
                "status": response.status,
                "error": response.error,
                "elapsed_sec": round(llm_elapsed, 3),
                "usage": response.usage if isinstance(response.usage, dict) else {},
            },
        )
        self._write_progress(
            ip,
            "llm_call_end",
            stage=stage,
            log_stage=(log_stage or stage),
            model=self.model,
            status=response.status,
            elapsed_sec=round(llm_elapsed, 3),
            error=response.error,
        )
        return response

    def _write_llm_log(
        self,
        ip: str,
        stage: str,
        response: LLMResponse,
        *,
        prompt: str,
        context: dict[str, Any],
        started_at: str,
        finished_at: str,
    ) -> None:
        log_dir = self._log_dir(ip)
        log_dir.mkdir(parents=True, exist_ok=True)
        (log_dir / f"{stage}_prompt.md").write_text(prompt, encoding="utf-8")
        _write_json(log_dir / f"{stage}.json", response.to_log(prompt=prompt, context=context, started_at=started_at, finished_at=finished_at))

    def _write_deterministic_rtl_seed_log(self, ip: str, context: dict[str, Any]) -> None:
        log_path = self._log_dir(ip) / "rtl-gen.json"
        if log_path.is_file():
            return
        provenance_path = self._ip_dir(ip) / "rtl" / "rtl_authoring_provenance.json"
        provenance = _read_json(provenance_path)
        packet_logs = sorted(self._log_dir(ip).glob("rtl-gen-packet-*.json"))
        if provenance.get("generator") != "generic_ssot_rule_seed" and not packet_logs:
            return
        rtl_files = provenance.get("rtl_files") if isinstance(provenance.get("rtl_files"), list) else []
        if packet_logs and provenance.get("generator") != "generic_ssot_rule_seed":
            rel_packet_logs = [str(path.relative_to(self.root)) for path in packet_logs]
            raw_response = json.dumps(
                {
                    "status": "pass",
                    "generator": "packet_llm",
                    "reason": "packet-mode rtl-gen completed with per-packet LLM artifacts",
                    "packet_logs": rel_packet_logs,
                    "rtl_files": rtl_files,
                },
                sort_keys=True,
            )
            response = LLMResponse(
                stage="rtl-gen",
                model=self.model or "packet-llm",
                raw_response=raw_response,
                parsed_artifacts=[
                    {"path": f"{ip}/{rel}", "kind": "rtl"}
                    for rel in rtl_files
                    if str(rel).strip()
                ],
            )
            prompt = (
                "Aggregate rtl-gen packet-mode completion log: per-packet LLM calls authored "
                "the RTL slices, and ssot-rtl accepted the resulting DUT compile/lint/audit evidence."
            )
            now = _utc()
            self._write_llm_log(ip, "rtl-gen", response, prompt=prompt, context=context, started_at=now, finished_at=now)
            return
        raw_response = json.dumps(
            {
                "status": "pass",
                "generator": "generic_ssot_rule_seed",
                "reason": "requirements-backed structured SSOT rule contract lowered without an external LLM call",
                "rtl_files": rtl_files,
            },
            sort_keys=True,
        )
        response = LLMResponse(
            stage="rtl-gen",
            model=self.model or "deterministic",
            raw_response=raw_response,
            parsed_artifacts=[
                {"path": f"{ip}/{rel}", "kind": "rtl"}
                for rel in rtl_files
                if str(rel).strip()
            ],
        )
        prompt = (
            "Deterministic rtl-gen seed path: ssot_to_rtl.py generated a single-leaf "
            "RTL implementation from an executable rtl_contract/function_model rule set "
            "after requirements.md established human-owned authority."
        )
        now = _utc()
        self._write_llm_log(ip, "rtl-gen", response, prompt=prompt, context=context, started_at=now, finished_at=now)

    def _apply_artifacts(self, ip: str, artifacts: list[dict[str, Any]]) -> list[str]:
        written: list[str] = []
        for item in artifacts:
            rel = Path(str(item.get("path") or ""))
            if rel.is_absolute() or ".." in rel.parts:
                raise RuntimeError(f"unsafe artifact path from LLM: {rel}")
            target = self.root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(str(item.get("content") or ""), encoding="utf-8")
            written.append(str(rel))
        return written

    def _ensure_generic_rtl_contract(self, ip: str) -> bool:
        ip_dir = self._ip_dir(ip)
        contract_path = ip_dir / "rtl" / "rtl_contract.json"
        existing = _read_json(contract_path)
        if existing.get("type") == "generic_ssot_rule_rtl_contract":
            return False
        ssot_path = ip_dir / "yaml" / f"{ip}.ssot.yaml"
        if not ssot_path.is_file():
            return False
        try:
            doc = yaml.safe_load(ssot_path.read_text(encoding="utf-8")) or {}
        except Exception:
            return False
        rtl_contract = doc.get("rtl_contract") if isinstance(doc.get("rtl_contract"), dict) else {}
        if not rtl_contract:
            return False
        fm = doc.get("function_model") if isinstance(doc.get("function_model"), dict) else {}
        transactions = [item for item in fm.get("transactions") or [] if isinstance(item, dict)]
        tx = transactions[0] if transactions else {}
        outputs: list[dict[str, Any]] = []
        for rule in tx.get("output_rules") or []:
            if not isinstance(rule, dict):
                continue
            name = str(rule.get("name") or rule.get("port") or "result")
            port = str(rule.get("port") or name)
            outputs.append({
                "name": name,
                "port": port,
                "expr": rule.get("expr") or "",
                "width": rule.get("width") or 1,
                "source": rule,
            })
        state_vars = {
            str(item.get("name")): {"width": item.get("width") or 1, "reset": item.get("reset", 0)}
            for item in fm.get("state_variables") or []
            if isinstance(item, dict) and str(item.get("name") or "").strip()
        }
        state_updates = []
        for item in tx.get("state_updates") or []:
            if not isinstance(item, dict):
                continue
            state_updates.append({
                "name": item.get("name"),
                "expr": item.get("expr") or "",
                "width": item.get("width") or state_vars.get(str(item.get("name")), {}).get("width", 1),
                "source": item,
            })
        payload = {
            "schema_version": 1,
            "type": "generic_ssot_rule_rtl_contract",
            "top": ip,
            "contract": {
                "top": ip,
                "transaction": rtl_contract.get("transaction") or tx.get("id") or "FM_PRIMARY",
                "clock": rtl_contract.get("clock") or "clk",
                "reset": rtl_contract.get("reset") or "rst_n",
                "reset_active": rtl_contract.get("reset_active") or "low",
                "sample_condition": rtl_contract.get("sample_condition") or "1'b1",
                "input_map": rtl_contract.get("input_map") if isinstance(rtl_contract.get("input_map"), dict) else {},
                "outputs": outputs,
                "state_vars": state_vars,
                "state_updates": state_updates,
                "special_outputs": {
                    key: value
                    for key, value in {
                        "ready_output": rtl_contract.get("ready_output"),
                        "output_valid": rtl_contract.get("output_valid"),
                    }.items()
                    if value
                },
                "source": "SSOT rtl_contract + function_model generated by common_ai_agent headless runner",
            },
        }
        contract_path.parent.mkdir(parents=True, exist_ok=True)
        _write_json(contract_path, payload)
        return True

    def _check_ssot_contract(self, ip: str, *, emit_gate: bool = True) -> StageResult:
        path = self._ip_dir(ip) / "yaml" / f"{ip}.ssot.yaml"
        if not path.is_file():
            if emit_gate:
                q = self._write_human_gate(ip, "ssot-gen", "missing_ssot", decision_needed="LLM did not produce SSOT YAML.")
                return StageResult("ssot-gen", "human_gate", "missing SSOT", artifacts=[str(q.relative_to(self.root))], blocker=str(q.relative_to(self.root)))
            return StageResult("ssot-gen", "human_gate", "missing SSOT")
        text = path.read_text(encoding="utf-8", errors="replace")
        try:
            doc = yaml.safe_load(text) or {}
        except Exception as exc:
            if emit_gate:
                q = self._write_human_gate(ip, "ssot-gen", "yaml_parse", decision_needed=f"Repair SSOT YAML parse error: {exc}")
                return StageResult("ssot-gen", "human_gate", str(exc), artifacts=[str(path.relative_to(self.root)), str(q.relative_to(self.root))], blocker=str(q.relative_to(self.root)))
            return StageResult("ssot-gen", "human_gate", str(exc), artifacts=[str(path.relative_to(self.root))])
        missing = []
        if not isinstance(doc, dict):
            missing.append("yaml root object")
        else:
            for key in SSOT_REQUIRED_KEYS:
                if key not in doc or doc.get(key) is None or doc.get(key) == "":
                    missing.append(key)
        if missing:
            if emit_gate:
                q = self._write_human_gate(
                    ip,
                    "ssot-gen",
                    "missing_contract",
                    decision_needed=f"Complete SSOT contract fields before downstream generation: {', '.join(missing)}",
                    evidence={"ssot_refs": [f"{ip}/yaml/{ip}.ssot.yaml"], "requirement_refs": [f"{ip}/req/{ip}_requirements.md"], "tool_logs": [], "goal_ids": []},
                )
                return StageResult("ssot-gen", "human_gate", "SSOT contract incomplete", artifacts=[str(path.relative_to(self.root)), str(q.relative_to(self.root))], blocker=str(q.relative_to(self.root)))
            return StageResult("ssot-gen", "human_gate", f"SSOT contract incomplete: {', '.join(missing)}", artifacts=[str(path.relative_to(self.root))])
        validator = WORKFLOW_ROOT / "ssot-gen" / "scripts" / "check_ssot_disk.sh"
        if validator.is_file():
            proc = subprocess.run(
                ["bash", str(validator), ip],
                cwd=str(self.root),
                text=True,
                capture_output=True,
                timeout=60,
            )
            validator_log = self._ip_dir(ip) / "logs" / "validators" / "check_ssot_disk.log"
            validator_log.parent.mkdir(parents=True, exist_ok=True)
            validator_text = "\n".join(
                part
                for part in [
                    f"cmd: bash {validator} {ip}",
                    f"cwd: {self.root}",
                    f"returncode: {proc.returncode}",
                    "stdout:\n" + proc.stdout.strip() if proc.stdout.strip() else "",
                    "stderr:\n" + proc.stderr.strip() if proc.stderr.strip() else "",
                ]
                if part
            )
            validator_log.write_text(validator_text + "\n", encoding="utf-8")
            if proc.returncode != 0:
                first_failure = (proc.stdout.strip() or proc.stderr.strip() or "check_ssot_disk.sh failed").splitlines()[0]
                if emit_gate:
                    q = self._write_human_gate(
                        ip,
                        "ssot-gen",
                        "missing_contract",
                        decision_needed=f"Repair SSOT so check_ssot_disk.sh passes: {first_failure}",
                        evidence={
                            "ssot_refs": [f"{ip}/yaml/{ip}.ssot.yaml"],
                            "requirement_refs": [f"{ip}/req/{ip}_requirements.md"],
                            "tool_logs": [str(validator_log.relative_to(self.root))],
                            "goal_ids": [],
                        },
                    )
                    return StageResult(
                        "ssot-gen",
                        "human_gate",
                        "SSOT disk validator failed",
                        artifacts=[
                            str(path.relative_to(self.root)),
                            str(validator_log.relative_to(self.root)),
                            str(q.relative_to(self.root)),
                        ],
                        blocker=str(q.relative_to(self.root)),
                    )
                return StageResult(
                    "ssot-gen",
                    "human_gate",
                    f"SSOT disk validator failed: {first_failure}",
                    artifacts=[str(path.relative_to(self.root)), str(validator_log.relative_to(self.root))],
                )
        return StageResult("ssot-gen", "pass", "SSOT contract valid", artifacts=[str(path.relative_to(self.root)), f"{ip}/logs/llm/ssot-gen.json"])

    def _run_deterministic_ssot_repair(self, ip: str, *, reason: str = "") -> bool:
        repair = WORKFLOW_ROOT / "ssot-gen" / "scripts" / "repair_ssot_schema.py"
        if not repair.is_file():
            return False
        log = self._ip_dir(ip) / "logs" / "validators" / "repair_ssot_schema.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        cmd = [sys.executable, str(repair), ip, "--root", str(self.root)]
        self._write_progress(ip, "deterministic_repair_start", stage="ssot-gen", reason=reason)
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(SOURCE_ROOT),
                text=True,
                capture_output=True,
                timeout=60,
            )
        except subprocess.TimeoutExpired as exc:
            log.write_text(
                "\n".join(
                    [
                        "cmd: " + " ".join(cmd),
                        f"cwd: {SOURCE_ROOT}",
                        "returncode: timeout",
                        f"reason: {reason}",
                        "stdout:\n" + str(exc.stdout or "").strip(),
                        "stderr:\n" + str(exc.stderr or "").strip(),
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            self._write_progress(ip, "deterministic_repair_end", stage="ssot-gen", status="timeout")
            return False
        log.write_text(
            "\n".join(
                part
                for part in [
                    "cmd: " + " ".join(cmd),
                    f"cwd: {SOURCE_ROOT}",
                    f"returncode: {proc.returncode}",
                    f"reason: {reason}",
                    "stdout:\n" + proc.stdout.strip() if proc.stdout.strip() else "",
                    "stderr:\n" + proc.stderr.strip() if proc.stderr.strip() else "",
                ]
                if part
            )
            + "\n",
            encoding="utf-8",
        )
        self._write_progress(
            ip,
            "deterministic_repair_end",
            stage="ssot-gen",
            status="pass" if proc.returncode == 0 else "fail",
        )
        return proc.returncode == 0

    def _validate_ssot(self, ip: str) -> StageResult:
        result = self._check_ssot_contract(ip)
        return self._append(
            result.stage,
            result.status,
            result.message,
            returncode=result.returncode,
            artifacts=result.artifacts,
            blocker=result.blocker,
        )

    def _ssot_repair_prompt(self, ip: str, context: dict[str, Any], failure: StageResult, attempt: int) -> tuple[str, str]:
        ssot_path = self._ip_dir(ip) / "yaml" / f"{ip}.ssot.yaml"
        validator_log = self._ip_dir(ip) / "logs" / "validators" / "check_ssot_disk.log"
        current_yaml = ssot_path.read_text(encoding="utf-8", errors="replace") if ssot_path.is_file() else ""
        validator_text = validator_log.read_text(encoding="utf-8", errors="replace") if validator_log.is_file() else ""
        blocker_text = ""
        if failure.blocker:
            blocker_path = self.root / failure.blocker
            if blocker_path.is_file():
                blocker_text = blocker_path.read_text(encoding="utf-8", errors="replace")

        system, _ = self._stage_prompt("ssot-gen", ip, context)
        prompt = (
            f"Repair the SSOT YAML artifact for {ip}. This is repair attempt {attempt}.\n\n"
            "Return exactly one JSON object and nothing else. Do not wrap it in markdown.\n"
            "Success schema:\n"
            "{\n"
            '  "files": [\n'
            f'    {{"path": "{ip}/yaml/{ip}.ssot.yaml", "kind": "ssot", "content": "<complete repaired YAML>"}}\n'
            "  ]\n"
            "}\n\n"
            "Repair rules:\n"
            "- Do not use a fixed IP template or hardcoded workaround.\n"
            "- Preserve product semantics from the requirement and current SSOT wherever they are valid.\n"
            "- SSOT remains the only source of truth for function_model, cycle_model, decomposition, RTL contract, DV plan, and coverage.\n"
            "- Fix the concrete parse/validator failures below, and also check for sibling contract defects.\n"
            "- The repaired YAML must pass `bash workflow/ssot-gen/scripts/check_ssot_disk.sh "
            f"{ip}`.\n"
            "- If a true semantic decision is missing from requirements, return a human_gate object instead of guessing.\n\n"
            f"Failure summary:\n{failure.status}: {failure.message}\n\n"
            f"Blocker artifact:\n{_clip(blocker_text, 6000)}\n\n"
            f"Validator log:\n{_clip(validator_text, 12000)}\n\n"
            f"Requirements:\n{_clip(str(context.get('requirement_text') or ''), 12000)}\n\n"
            f"Current SSOT YAML:\n{_clip(current_yaml, 30000)}"
        )
        return system, prompt

    def _run_ssot_generation(self, ip: str, context: dict[str, Any]) -> StageResult:
        response = self._call_llm("ssot-gen", ip, context)
        if response.status in {"blocked", "human_gate"}:
            return self._append_ssot_llm_gate(ip, response)
        self._apply_artifacts(ip, response.parsed_artifacts)

        deterministic_repair_tried = False
        if self._run_deterministic_ssot_repair(ip, reason="canonicalize_llm_ssot"):
            deterministic_repair_tried = True
        for attempt in range(0, self.ssot_repair_attempts + 1):
            validation = self._check_ssot_contract(ip, emit_gate=False)
            if validation.status == "pass":
                return self._append(
                    validation.stage,
                    validation.status,
                    validation.message,
                    returncode=validation.returncode,
                    artifacts=validation.artifacts,
                    blocker=validation.blocker,
                )
            if not deterministic_repair_tried and not validation.message.startswith("SSOT contract incomplete"):
                deterministic_repair_tried = True
                if self._run_deterministic_ssot_repair(ip, reason=validation.message):
                    validation = self._check_ssot_contract(ip, emit_gate=False)
                    if validation.status == "pass":
                        return self._append(
                            validation.stage,
                            validation.status,
                            validation.message,
                            returncode=validation.returncode,
                            artifacts=validation.artifacts,
                            blocker=validation.blocker,
                        )
            if attempt >= self.ssot_repair_attempts:
                validation = self._check_ssot_contract(ip, emit_gate=True)
                return self._append(
                    validation.stage,
                    validation.status,
                    validation.message,
                    returncode=validation.returncode,
                    artifacts=validation.artifacts,
                    blocker=validation.blocker,
                )

            system, prompt = self._ssot_repair_prompt(ip, context, validation, attempt + 1)
            repair = self._call_llm(
                "ssot-gen",
                ip,
                context,
                system_prompt=system,
                prompt=prompt,
                log_stage=f"ssot-gen-repair-{attempt + 1}",
            )
            if repair.status in {"blocked", "human_gate"}:
                return self._append_ssot_llm_gate(ip, repair, topic=f"repair_{attempt + 1}")
            self._apply_artifacts(ip, repair.parsed_artifacts)
            self._run_deterministic_ssot_repair(ip, reason=f"canonicalize_llm_repair_{attempt + 1}")
        return self._validate_ssot(ip)

    def _append_llm_gate(self, ip: str, stage: str, response: LLMResponse, *, topic: str = "llm") -> StageResult:
        data = _json_from_text(response.raw_response or "") or {}
        gate = data.get("human_gate") if isinstance(data.get("human_gate"), dict) else {}
        if response.status == "blocked" and not gate:
            return self._append(
                stage,
                "blocked",
                response.error or f"{stage} LLM provider blocked before producing artifacts",
                returncode=1,
            )
        q = self._write_human_gate(
            ip,
            stage,
            topic,
            decision_needed=str(gate.get("decision_needed") or gate.get("reason") or response.error or f"{stage} LLM stage blocked"),
            evidence=gate.get("evidence") if isinstance(gate.get("evidence"), dict) else None,
            options=gate.get("options") if isinstance(gate.get("options"), list) else None,
            recommended_default=gate.get("recommended_default") if isinstance(gate.get("recommended_default"), dict) else None,
            downstream_effect=gate.get("downstream_effect") if isinstance(gate.get("downstream_effect"), list) else None,
        )
        return self._append(
            stage,
            "human_gate",
            response.error or f"{stage} LLM returned human gate",
            artifacts=[str(q.relative_to(self.root))],
            blocker=str(q.relative_to(self.root)),
        )

    def _append_ssot_llm_gate(self, ip: str, response: LLMResponse, *, topic: str = "llm") -> StageResult:
        return self._append_llm_gate(ip, "ssot-gen", response, topic=topic)

    def _run_cmd(self, stage: str, cmd: list[str], *, timeout: int = 180) -> StageResult:
        try:
            proc = subprocess.run(cmd, cwd=str(self.root), text=True, capture_output=True, timeout=timeout)
            status = "pass" if proc.returncode == 0 else "fail"
            msg = "\n".join(
                x for x in [
                    "cmd: " + " ".join(cmd),
                    f"returncode: {proc.returncode}",
                    "stdout:\n" + _clip(proc.stdout.strip()) if proc.stdout.strip() else "",
                    "stderr:\n" + _clip(proc.stderr.strip()) if proc.stderr.strip() else "",
                ] if x
            )
            return self._append(stage, status, msg, returncode=int(proc.returncode))
        except Exception as exc:
            return self._append(stage, "fail", str(exc), returncode=999)

    def _top_name(self, ip: str) -> str:
        path = self._ip_dir(ip) / "yaml" / f"{ip}.ssot.yaml"
        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            top = doc.get("top_module") if isinstance(doc, dict) else {}
            if isinstance(top, dict) and top.get("name"):
                return str(top["name"])
            if isinstance(top, str) and top.strip():
                return top.strip()
        except Exception:
            pass
        return ip

    def _stage_fl_model(self, ip: str) -> StageResult:
        return self._append_engine_result(self.stage_engine.run_stage("ssot-fl-model", ip), "fl-model-gen")

    def _stage_cl_model(self, ip: str) -> StageResult:
        cycle = self._append_engine_result(self.stage_engine.run_stage("ssot-cycle-model", ip), "cl-model-gen")
        if cycle.status == "pass":
            self._append_engine_result(self.stage_engine.run_stage("ssot-dual-fcov", ip), "dual-fcov")
        return cycle

    def _stage_dual_fcov(self, ip: str) -> StageResult:
        return self._append_engine_result(self.stage_engine.run_stage("ssot-dual-fcov", ip), "dual-fcov")

    def _stage_equiv_goals(self, ip: str) -> StageResult:
        return self._append_engine_result(self.stage_engine.run_stage("ssot-equiv-goals", ip), "equiv-goals")

    def _prepare_rtl_todos_for_llm(self, ip: str, *, audit_rtl: bool = False) -> subprocess.CompletedProcess[str]:
        script = WORKFLOW_ROOT / "rtl-gen" / "scripts" / "derive_rtl_todos.py"
        cmd = [sys.executable, str(script), ip, "--root", str(self.root)]
        if audit_rtl:
            cmd.append("--audit-rtl")
        return subprocess.run(
            cmd,
            cwd=str(self.root),
            text=True,
            capture_output=True,
            timeout=90,
        )

    def _update_rtl_context_from_todos(self, ip: str, rtl_context: dict[str, Any]) -> None:
        todo_path = self._ip_dir(ip) / "rtl" / "rtl_todo_plan.json"
        rtl_context.update(
            {
                "rtl_todo_plan_path": f"{ip}/rtl/rtl_todo_plan.json",
                "rtl_todo_plan_sha256": _stable_json_sha256(todo_path),
                "rtl_authoring_plan_path": f"{ip}/rtl/rtl_authoring_plan.json",
                "rtl_authoring_packet_dir": f"{ip}/rtl/authoring_packets",
            }
        )

    def _rtl_authoring_plan(self, ip: str) -> dict[str, Any]:
        return _read_json(self._ip_dir(ip) / "rtl" / "rtl_authoring_plan.json")

    def _rtl_packet_entries(self, plan: dict[str, Any]) -> list[dict[str, Any]]:
        packets = plan.get("packets") if isinstance(plan.get("packets"), list) else []
        return [
            packet
            for packet in packets
            if isinstance(packet, dict) and str(packet.get("json") or "").strip()
        ]

    def _rtl_packet_needs_llm(self, packet: dict[str, Any]) -> bool:
        summary = packet.get("summary") if isinstance(packet.get("summary"), dict) else {}
        policy = packet.get("execution_policy") if isinstance(packet.get("execution_policy"), dict) else {}
        if "llm_actionable_open_count" in policy:
            if int(policy.get("llm_actionable_open_count") or 0) > 0:
                return True
            tool_blockers = policy.get("blocked_by_tool_evidence")
            if isinstance(tool_blockers, list):
                for item in tool_blockers:
                    if not isinstance(item, dict):
                        continue
                    gate_kind = str(item.get("gate_kind") or "")
                    reason = str(item.get("reason") or "").lower()
                    if gate_kind in {"dut_compile", "dut_lint"} and any(
                        term in reason for term in ("not clean", "fail", "warning", "error")
                    ):
                        return True
            return False
        if "llm_actionable" in policy:
            return bool(policy.get("llm_actionable"))
        if "open_required_count" in summary:
            return int(summary.get("open_required_count") or 0) > 0
        return True

    def _rtl_packet_mode_enabled(self, plan: dict[str, Any]) -> bool:
        mode = os.getenv("ATLAS_HEADLESS_RTL_PACKET_MODE", "auto").strip().lower()
        if mode in {"0", "false", "off", "no"}:
            return False
        if mode in {"1", "true", "on", "yes"}:
            return True
        packets = self._rtl_packet_entries(plan)
        summary = plan.get("summary") if isinstance(plan.get("summary"), dict) else {}
        required_tasks = int(summary.get("required_tasks") or summary.get("total_tasks") or summary.get("task_count") or 0)
        task_threshold = max(0, int(os.getenv("ATLAS_HEADLESS_RTL_PACKET_TASK_THRESHOLD", "80")))
        packet_threshold = max(1, int(os.getenv("ATLAS_HEADLESS_RTL_PACKET_COUNT_THRESHOLD", "4")))
        return bool(packets) and (required_tasks > task_threshold or len(packets) > packet_threshold)

    def _rtl_packet_batch_limit(self) -> int:
        raw = os.getenv("ATLAS_HEADLESS_RTL_PACKET_MAX_PER_PASS", str(DEFAULT_RTL_PACKET_MAX_PER_PASS)).strip()
        try:
            configured = max(0, int(raw))
        except ValueError:
            configured = DEFAULT_RTL_PACKET_MAX_PER_PASS
        model_l = str(self.model or "").lower()
        if "glm" in model_l or "kimi" in model_l:
            # GLM/Kimi coding endpoints are more fragile on large RTL packet batches.
            # Use smaller default batches unless the user explicitly forces a lower value.
            return min(configured, max(1, int(os.getenv("ATLAS_HEADLESS_RTL_PACKET_MAX_PER_PASS_GLM_KIMI", "1"))))
        return configured

    def _rtl_packet_pass_budget(self, plan: dict[str, Any]) -> int:
        raw = os.getenv("ATLAS_HEADLESS_RTL_PACKET_MAX_PASSES", "").strip()
        if raw:
            try:
                return max(1, int(raw))
            except ValueError:
                pass
        _, batch = self._rtl_packet_work_batch(plan)
        work_packets = int(batch.get("work_packets") or 0)
        batch_limit = int(batch.get("packet_batch_limit") or 0)
        if work_packets <= 0 or batch_limit <= 0:
            initial_queue_passes = 1
        else:
            initial_queue_passes = (work_packets + batch_limit - 1) // batch_limit
        return max(self.rtl_repair_attempts + 1, initial_queue_passes + self.rtl_repair_attempts)

    def _rtl_packet_work_batch(self, plan: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, int]]:
        packets = self._rtl_packet_entries(plan)
        work_packets = [packet for packet in packets if self._rtl_packet_needs_llm(packet)]
        primary_packets = [
            packet
            for packet in work_packets
            if str(packet.get("packet_id") or Path(str(packet.get("json") or "")).stem) != "rtl_gate_evidence_closure"
        ]
        # Evidence-closure packets depend on fresh compile/lint/audit results from
        # prior module edits. If module packets are still open, defer closure to
        # the next pass so the stage engine can regenerate tool evidence first.
        eligible_packets = primary_packets if primary_packets else work_packets
        limit = self._rtl_packet_batch_limit()
        selected = eligible_packets[:limit] if limit else eligible_packets
        return selected, {
            "total_packets": len(packets),
            "work_packets": len(work_packets),
            "selected_packets": len(selected),
            "skipped_closed_packets": len(packets) - len(work_packets),
            "deferred_work_packets": max(0, len(work_packets) - len(selected)),
            "packet_batch_limit": limit,
        }

    def _declared_rtl_files(self, ip: str) -> list[str]:
        path = self._ip_dir(ip) / "yaml" / f"{ip}.ssot.yaml"
        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception:
            doc = {}
        if not isinstance(doc, dict):
            doc = {}
        top = self._top_name(ip)
        files: list[str] = []
        for sm in doc.get("sub_modules") or []:
            if not isinstance(sm, dict):
                continue
            ownership = str(sm.get("ownership") or "manifest").strip().lower()
            if ownership in {"child_ssot", "conceptual", "verification", "coverage"} or sm.get("ssot"):
                continue
            if sm.get("rtl_emit") is False:
                continue
            rel = str(sm.get("file") or "").strip()
            if rel:
                files.append(rel)
        filelist = doc.get("filelist") if isinstance(doc.get("filelist"), dict) else {}
        for rel in filelist.get("rtl") or []:
            if isinstance(rel, str) and rel.strip():
                files.append(rel.strip())
        if not files:
            files.append(f"rtl/{top}.sv")
        seen: set[str] = set()
        out: list[str] = []
        for rel in files:
            if rel and rel not in seen:
                seen.add(rel)
                out.append(rel)
        return out

    def _refresh_rtl_filelist_and_provenance(
        self,
        ip: str,
        *,
        packet_id: str = "",
    ) -> bool:
        ip_dir = self._ip_dir(ip)
        declared = self._declared_rtl_files(ip)
        if declared:
            filelist = ip_dir / "list" / f"{ip}.f"
            filelist.parent.mkdir(parents=True, exist_ok=True)
            filelist.write_text("".join(f"{rel}\n" for rel in declared), encoding="utf-8")

        existing_rtl = [rel for rel in declared if (ip_dir / rel).is_file()]
        if not existing_rtl:
            return False

        plan = self._rtl_authoring_plan(ip)
        provenance_path = ip_dir / "rtl" / "rtl_authoring_provenance.json"
        prior = _read_json(provenance_path)
        valid_packet_ids = {
            str(packet.get("packet_id") or "")
            for packet in self._rtl_packet_entries(plan)
            if str(packet.get("packet_id") or "").strip()
        }
        authored_packets = [
            str(item)
            for item in (prior.get("authoring_packets") if isinstance(prior.get("authoring_packets"), list) else [])
            if str(item).strip() and (not valid_packet_ids or str(item) in valid_packet_ids)
        ]
        if packet_id and packet_id not in authored_packets:
            authored_packets.append(packet_id)
        contract_files = [
            rel for rel in ("rtl/rtl_contract.json",)
            if (ip_dir / rel).is_file()
        ]
        payload = {
            **prior,
            "schema_version": 1,
            "type": "rtl_authoring_provenance",
            "agent": "common_ai_agent",
            "workflow": "rtl-gen",
            "surface": "headless_common_engine",
            "ip": ip,
            "model": self.model,
            "todo_plan_sha256": _stable_json_sha256(ip_dir / "rtl" / "rtl_todo_plan.json")
            or plan.get("todo_plan_sha256"),
            "rtl_files": existing_rtl,
            "contract_files": contract_files,
            "authoring_packets": authored_packets,
            "generation_note": prior.get("generation_note")
            or "Headless common engine recorded LLM-authored RTL artifacts from rtl_authoring_plan packets.",
            "updated_at": _utc(),
        }
        _write_json(provenance_path, payload)
        return True

    def _rtl_packet_prompt(
        self,
        ip: str,
        context: dict[str, Any],
        plan: dict[str, Any],
        packet: dict[str, Any],
        *,
        attempt: int,
    ) -> tuple[str, str]:
        system, base_prompt = self._stage_prompt("rtl-gen", ip, context)
        packet_rel = str(packet.get("json") or "").strip()
        packet_md_rel = str(packet.get("markdown") or "").strip()
        packet_path = self._ip_dir(ip) / packet_rel
        packet_md_path = self._ip_dir(ip) / packet_md_rel
        packet_json = packet_path.read_text(encoding="utf-8", errors="replace") if packet_path.is_file() else "{}"
        packet_md = packet_md_path.read_text(encoding="utf-8", errors="replace") if packet_md_path.is_file() else ""
        packet_doc = _read_json(packet_path) if packet_path.is_file() else {}
        owner_file_rel = str(packet.get("owner_file") or "").strip()
        owner_file_path = self._ip_dir(ip) / owner_file_rel if owner_file_rel else None
        owner_file_text = (
            owner_file_path.read_text(encoding="utf-8", errors="replace")
            if owner_file_path is not None and owner_file_path.is_file()
            else ""
        )
        tool_artifact_sections: list[str] = []
        packet_policy = packet_doc.get("execution_policy") if isinstance(packet_doc.get("execution_policy"), dict) else {}
        tool_plans = packet_policy.get("tool_evidence_plan") if isinstance(packet_policy.get("tool_evidence_plan"), list) else []
        seen_tool_artifacts: set[str] = set()
        for tool_plan in tool_plans:
            if not isinstance(tool_plan, dict):
                continue
            for rel in tool_plan.get("artifacts") or []:
                rel_s = str(rel or "").strip()
                if not rel_s or rel_s in seen_tool_artifacts:
                    continue
                seen_tool_artifacts.add(rel_s)
                path = self.root / rel_s
                if not path.is_file():
                    tool_artifact_sections.append(f"### {rel_s}\n<missing>")
                    continue
                tool_artifact_sections.append(
                    f"### {rel_s}\n{_clip(path.read_text(encoding='utf-8', errors='replace'), 16000)}"
                )
        tool_artifacts_text = "\n\n".join(tool_artifact_sections) if tool_artifact_sections else "<none>"
        packet_char_limit = max(8000, int(os.getenv("ATLAS_HEADLESS_RTL_PACKET_MAX_CHARS", "50000")))
        packet_digest = []
        for item in self._rtl_packet_entries(plan):
            item_summary = item.get("summary") if isinstance(item.get("summary"), dict) else {}
            item_policy = item.get("execution_policy") if isinstance(item.get("execution_policy"), dict) else {}
            packet_digest.append(
                {
                    "packet_id": item.get("packet_id"),
                    "kind": item.get("kind"),
                    "owner_module": item.get("owner_module"),
                    "owner_file": item.get("owner_file"),
                    "json": item.get("json"),
                    "required_count": item_summary.get("required_count"),
                    "open_required_count": item_summary.get("open_required_count"),
                    "status_counts": item_summary.get("status_counts"),
                    "llm_actionable_open_count": item_policy.get("llm_actionable_open_count"),
                    "human_locked_open_count": item_policy.get("human_locked_open_count"),
                }
            )
        reference_profile = plan.get("reference_profile") if isinstance(plan.get("reference_profile"), dict) else {}
        reference_profile_digest = {
            key: reference_profile.get(key)
            for key in REFERENCE_PROFILE_PROMPT_KEYS
            if key in reference_profile
        }
        plan_overview = {
            "type": plan.get("type"),
            "ip": plan.get("ip"),
            "top": plan.get("top"),
            "summary": plan.get("summary"),
            "policy": plan.get("policy"),
            "target_scale": plan.get("target_scale"),
            "reference_profile": reference_profile_digest,
            "execution_policy": plan.get("execution_policy"),
            "packets": packet_digest,
            "todo_plan_sha256": plan.get("todo_plan_sha256"),
        }
        ssot_latency_contract: dict[str, Any] = {}
        ssot_prompt_text = ""
        ssot_path = self._ip_dir(ip) / "yaml" / f"{ip}.ssot.yaml"
        if ssot_path.is_file():
            ssot_prompt_text = ssot_path.read_text(encoding="utf-8", errors="replace")
            try:
                ssot_doc = yaml.safe_load(ssot_prompt_text) or {}
            except Exception:
                ssot_doc = {}
            cm = ssot_doc.get("cycle_model") if isinstance(ssot_doc.get("cycle_model"), dict) else {}
            rtl_contract = ssot_doc.get("rtl_contract") if isinstance(ssot_doc.get("rtl_contract"), dict) else {}
            timing = ssot_doc.get("timing") if isinstance(ssot_doc.get("timing"), dict) else {}
            ssot_latency_contract = {
                "cycle_model.latency": cm.get("latency"),
                "cycle_model.pipeline": cm.get("pipeline"),
                "rtl_contract.sample_condition": rtl_contract.get("sample_condition"),
                "rtl_contract.output_valid": rtl_contract.get("output_valid"),
                "timing.latency_budget": timing.get("latency_budget"),
                "observable_latency_rule": (
                    "For valid/ready transactions, latency is counted from the accepting clock edge "
                    "to the first ReadOnly observation of matching result/output_valid. latency=1 means "
                    "registered outputs for the accepted transaction are visible after that one edge; "
                    "an input-register stage followed by a result-register stage is latency=2."
                ),
                "latency_1_required_rtl_shape": (
                    "When cycle_model.latency is 1, compute output_rules from the current accepted inputs "
                    "inside the accept_txn/valid&&ready clocked branch and assign result_valid in that same "
                    "branch. Do not first store inputs in S0_SAMPLE and then assign outputs in a later "
                    "S1_RESULT clock edge; that is a forbidden latency-2 implementation."
                ),
            }
        schema = (
            "{\n"
            '  "files": [\n'
            f'    {{"path": "{ip}/rtl/<module>.sv", "kind": "rtl", "content": "<SystemVerilog>"}},\n'
            f'    {{"path": "{ip}/rtl/rtl_contract.json", "kind": "rtl_contract", "content": "<optional JSON>"}},\n'
            f'    {{"path": "{ip}/rtl/rtl_authoring_notes/<packet>.md", "kind": "rtl_notes", "content": "<optional notes>"}}\n'
            "  ]\n"
            "}\n"
        )
        prompt = (
            f"RTL-GEN PACKET MODE for {ip}. Packet attempt {attempt}.\n\n"
            "Return exactly one JSON object and nothing else. Do not wrap it in markdown.\n"
            "Success schema:\n"
            f"{schema}\n"
            "If this packet exposes a missing locked-truth decision, return a human_gate object instead of "
            "inventing SSOT, FL, coverage, interface, or performance semantics.\n\n"
            "Packet execution rules:\n"
            "- Author only RTL-owned artifacts for the current packet, plus local notes/contract metadata when useful.\n"
            "- Do not edit SSOT YAML, FunctionalModel, coverage goals, protocol assertions, performance targets, or requirements.\n"
            "- You cannot read files from the repo during this turn. The required locked SSOT facts are embedded below; do not return requires/missing-file JSON for those paths.\n"
            "- Do not emit placeholder, heartbeat-only, alive-only, or tie-off-only RTL to satisfy a manifest.\n"
            "- For production-profile packets, add real SSOT-scaled implementation depth: state/control/data movement, nonconstant logic, and child wiring must be proportional to the packet tasks.\n"
            "- For a module packet, focus on owner_file and every task content/detail/criteria/source_ref in the packet.\n"
            "- If current owner_file content is provided, preserve prior slice logic and merge the new behavior; do not replace the file with a partial slice-only module.\n"
            "- For mixed packets with locked-truth blockers, keep authoring LLM-actionable RTL/test/evidence work and leave the locked-truth tasks open.\n"
            "- Return human_gate only when no LLM-actionable open work remains or the missing locked-truth decision blocks correct RTL authoring.\n"
            "- For rtl_gate_evidence_closure, repair only LLM-actionable evidence gaps revealed by compile/lint/audit output; do not claim PASS.\n"
            "- If rtl_gate_evidence_closure includes pending connection_contract_suggestions, you may use them as draft RTL wiring candidates to instantiate child modules and close hierarchy/signal-flow evidence, but they remain pending QA and must not be treated as SSOT authority.\n"
            "- For rtl_gate_tool_evidence, do not fabricate compile/lint/sim/coverage artifacts. If compile/lint evidence already exists and is not clean, repair the owner RTL that caused the diagnostics; the runner will rerun tools afterward.\n"
            "- For rtl_gate_contract_blocked, return human_gate only; missing SSOT connection contracts block correct top integration semantics.\n"
            "- For rtl_gate_human_closure, return human_gate only; do not invent or edit human-locked authority.\n"
            "- The headless runner will refresh filelist/provenance from LLM-authored artifacts after each packet.\n\n"
            f"Current packet: {packet.get('packet_id') or packet_rel}\n"
            f"kind: {packet.get('kind')}\n"
            f"work queue: {context.get('rtl_packet_index', 0) + 1}/{context.get('rtl_packet_count', '?')} active packets"
            f" ({context.get('rtl_packet_skipped_closed_count', 0)} closed packets skipped from {context.get('rtl_packet_total_count', context.get('rtl_packet_count', '?'))} total)\n"
            f"batch limit: {context.get('rtl_packet_batch_limit', 0)}; deferred active packets after this batch: {context.get('rtl_packet_deferred_work_count', 0)}\n"
            f"owner_module: {packet.get('owner_module') or ''}\n"
            f"owner_file: {packet.get('owner_file') or ''}\n\n"
            f"SSOT observable latency contract:\n{_clip(json.dumps(ssot_latency_contract, indent=2, sort_keys=True), 12000)}\n\n"
            f"Locked SSOT YAML excerpt ({ip}/yaml/{ip}.ssot.yaml):\n{_clip(ssot_prompt_text, 40000) if ssot_prompt_text else '<missing>'}\n\n"
            f"Base rtl-gen contract:\n{base_prompt}\n\n"
            f"Authoring plan overview:\n{_clip(json.dumps(plan_overview, indent=2, sort_keys=True), 30000)}\n\n"
            f"Current owner RTL file ({owner_file_rel or '<none>'}):\n{_clip(owner_file_text, 30000) if owner_file_text else '<missing or not authored yet>'}\n\n"
            f"Current tool evidence artifacts referenced by this packet:\n{tool_artifacts_text}\n\n"
            f"Current packet JSON ({packet_rel}):\n{_clip(packet_json, packet_char_limit)}\n\n"
            f"Current packet Markdown ({packet_md_rel}):\n{_clip(packet_md, 16000)}"
        )
        return system, prompt

    def _run_rtl_packet_llm_pass(
        self,
        ip: str,
        rtl_context: dict[str, Any],
        *,
        attempt: int,
    ) -> StageResult | None:
        plan = self._rtl_authoring_plan(ip)
        work_packets, batch = self._rtl_packet_work_batch(plan)
        for index, packet in enumerate(work_packets):
            packet_id = str(packet.get("packet_id") or Path(str(packet.get("json") or f"packet_{index}")).stem)
            packet_context = dict(rtl_context)
            packet_context.update(
                {
                    "rtl_packet_mode": True,
                    "rtl_packet_index": index,
                    "rtl_packet_count": len(work_packets),
                    "rtl_packet_total_count": batch["total_packets"],
                    "rtl_packet_work_count": batch["work_packets"],
                    "rtl_packet_selected_count": batch["selected_packets"],
                    "rtl_packet_deferred_work_count": batch["deferred_work_packets"],
                    "rtl_packet_batch_limit": batch["packet_batch_limit"],
                    "rtl_packet_skipped_closed_count": batch["skipped_closed_packets"],
                    "rtl_packet_id": packet_id,
                    "rtl_packet_path": f"{ip}/{packet.get('json')}",
                    "rtl_packet_kind": packet.get("kind"),
                    "rtl_packet_owner_module": packet.get("owner_module"),
                    "rtl_packet_owner_file": packet.get("owner_file"),
                }
            )
            system, prompt = self._rtl_packet_prompt(ip, packet_context, plan, packet, attempt=attempt)
            log_stage = (
                f"rtl-gen-packet-{index:02d}-{_safe_name(packet_id)}"
                if attempt == 0
                else f"rtl-gen-repair-{attempt}-packet-{index:02d}-{_safe_name(packet_id)}"
            )
            response = self._call_llm(
                "rtl-gen",
                ip,
                packet_context,
                system_prompt=system,
                prompt=prompt,
                log_stage=log_stage,
            )
            if _response_declares_empty_files(response):
                continue
            if response.status in {"blocked", "human_gate"}:
                return self._append_llm_gate(ip, "rtl-gen", response, topic=f"packet_{_safe_name(packet_id)}")
            if not response.parsed_artifacts:
                return self._append(
                    "rtl-gen",
                    "blocked",
                    f"rtl-gen packet {packet_id} produced no files[] artifacts; retry the packet instead of treating truncated output as progress",
                    returncode=1,
                )
            self._apply_artifacts(ip, response.parsed_artifacts)
            self._refresh_rtl_filelist_and_provenance(ip, packet_id=packet_id)
        return None

    def _rtl_result_repairable_by_llm(self, result: StageEngineResult) -> bool:
        if result.status == "fail":
            return True
        blocked_doc = result.metadata.get("rtl_blocked") if isinstance(result.metadata, dict) else None
        questions = blocked_doc.get("questions") if isinstance(blocked_doc, dict) and isinstance(blocked_doc.get("questions"), list) else []
        question_ids = {str(q.get("id") or "") for q in questions if isinstance(q, dict)}
        rtl_owned_ids = {
            "RTL_TODO_PLAN_MISSING",
            "DETERMINISTIC_RTL_ARTIFACT_NOT_APPROVED",
            "LLM_RTL_IMPLEMENTATION_REQUIRED",
            "COMMON_AI_AGENT_RTL_PROVENANCE_REQUIRED",
        }
        draft_compatible_ids = rtl_owned_ids | {"RTL_TARGET_SCALE_POLICY"}
        if question_ids and bool(question_ids & rtl_owned_ids) and question_ids <= draft_compatible_ids:
            return True
        message = result.message.lower()
        return (
            "llm-authored rtl evidence is missing or stale" in message
            or "rtl-gen waiting for llm-authored rtl" in message
            or "rtl result] fail - llm-authored rtl needs rtl-gen repair" in message
        )

    def _stage_rtl_gen(self, ip: str, context: dict[str, Any]) -> StageResult:
        try:
            prederive = self._prepare_rtl_todos_for_llm(ip, audit_rtl=True)
        except Exception as exc:
            return self._append("rtl-gen", "fail", f"failed to derive SSOT RTL TODO plan before LLM call: {exc}", returncode=999)
        if prederive.returncode not in {0, 1} or not (self._ip_dir(ip) / "rtl" / "rtl_authoring_plan.json").is_file():
            result = self.stage_engine.run_stage("ssot-rtl", ip)
            if result.status == "pass":
                self._ensure_generic_rtl_contract(ip)
                self._write_deterministic_rtl_seed_log(ip, context)
            return self._append_engine_result(result, "rtl-gen", blocker=result.blocker)

        rtl_context = dict(context)
        self._update_rtl_context_from_todos(ip, rtl_context)
        if self._refresh_rtl_filelist_and_provenance(ip):
            try:
                prederive = self._prepare_rtl_todos_for_llm(ip, audit_rtl=True)
            except Exception as exc:
                return self._append("rtl-gen", "fail", f"failed to refresh RTL TODO plan after provenance update: {exc}", returncode=999)
            if prederive.returncode not in {0, 1}:
                result = self.stage_engine.run_stage("ssot-rtl", ip)
                if result.status == "pass":
                    self._ensure_generic_rtl_contract(ip)
                    self._write_deterministic_rtl_seed_log(ip, rtl_context)
                return self._append_engine_result(result, "rtl-gen", blocker=result.blocker)
            self._update_rtl_context_from_todos(ip, rtl_context)
        packet_mode = self._rtl_packet_mode_enabled(self._rtl_authoring_plan(ip))
        result: StageEngineResult | None = None
        attempt_limit = self.rtl_repair_attempts + 1
        if packet_mode:
            attempt_limit = self._rtl_packet_pass_budget(self._rtl_authoring_plan(ip))
            rtl_context["rtl_packet_pass_budget"] = attempt_limit
        for attempt in range(attempt_limit):
            if attempt > 0:
                try:
                    prederive = self._prepare_rtl_todos_for_llm(ip, audit_rtl=True)
                except Exception as exc:
                    return self._append("rtl-gen", "fail", f"failed to refresh SSOT RTL TODO plan before repair attempt: {exc}", returncode=999)
                if prederive.returncode not in {0, 1}:
                    result = self.stage_engine.run_stage("ssot-rtl", ip)
                    break
                self._update_rtl_context_from_todos(ip, rtl_context)
                if self._refresh_rtl_filelist_and_provenance(ip):
                    try:
                        prederive = self._prepare_rtl_todos_for_llm(ip, audit_rtl=True)
                    except Exception as exc:
                        return self._append("rtl-gen", "fail", f"failed to refresh RTL TODO plan after provenance update: {exc}", returncode=999)
                    if prederive.returncode not in {0, 1}:
                        result = self.stage_engine.run_stage("ssot-rtl", ip)
                        break
                    self._update_rtl_context_from_todos(ip, rtl_context)
                packet_mode = self._rtl_packet_mode_enabled(self._rtl_authoring_plan(ip))
            rtl_context["rtl_gen_attempt"] = attempt
            if packet_mode:
                gate = self._run_rtl_packet_llm_pass(ip, rtl_context, attempt=attempt)
                if gate is not None:
                    return gate
            else:
                response = self._call_llm(
                    "rtl-gen",
                    ip,
                    rtl_context,
                    log_stage="rtl-gen" if attempt == 0 else f"rtl-gen-repair-{attempt}",
                )
                if response.status in {"blocked", "human_gate"}:
                    return self._append_llm_gate(ip, "rtl-gen", response, topic="llm")
                self._apply_artifacts(ip, response.parsed_artifacts)
                self._refresh_rtl_filelist_and_provenance(ip)
            result = self.stage_engine.run_stage("ssot-rtl", ip)
            if result.status == "pass":
                self._ensure_generic_rtl_contract(ip)
                self._write_deterministic_rtl_seed_log(ip, rtl_context)
                break
            if result.status in {"human_gate", "blocked"} and not self._rtl_result_repairable_by_llm(result):
                break
            if attempt >= attempt_limit - 1:
                break
            rtl_context.update(
                {
                    "rtl_repair_attempt": attempt + 1,
                    "rtl_last_result_status": result.status,
                    "rtl_last_result_message": result.message[-4000:],
                }
            )
        assert result is not None
        extra: list[str] = []
        blocker = result.blocker
        blocked_doc = result.metadata.get("rtl_blocked") if isinstance(result.metadata, dict) else None
        if isinstance(blocked_doc, dict) and blocked_doc and not self._rtl_result_repairable_by_llm(result):
            q = self._write_human_gate(
                ip,
                "rtl-gen",
                "rtl_blocked",
                decision_needed=str(blocked_doc.get("reason") or "RTL generation blocked by SSOT contract"),
                evidence={"ssot_refs": [f"{ip}/yaml/{ip}.ssot.yaml"], "tool_logs": [f"{ip}/rtl/rtl_blocked.json"], "goal_ids": []},
            )
            blocker = str(q.relative_to(self.root))
            extra.append(blocker)
        if result.status == "pass":
            self._ensure_generic_rtl_contract(ip)
            self._write_deterministic_rtl_seed_log(ip, rtl_context)
        return self._append_engine_result(result, "rtl-gen", artifacts=extra, blocker=blocker)

    def _stage_lint(self, ip: str) -> StageResult:
        return self._append_engine_result(self.stage_engine.run_stage("lint", ip), "lint")

    def _stage_tb_gen(self, ip: str, context: dict[str, Any]) -> StageResult:
        response = self._call_llm("tb-gen", ip, context)
        if response.status not in {"blocked", "human_gate"}:
            self._apply_artifacts(ip, response.parsed_artifacts)
        self._ensure_generic_rtl_contract(ip)
        result = self.stage_engine.run_stage("ssot-tb-cocotb", ip)
        extra: list[str] = []
        blocker = result.blocker
        blocked_doc = result.metadata.get("tb_blocked") if isinstance(result.metadata, dict) else None
        if isinstance(blocked_doc, dict) and blocked_doc:
            q = self._write_human_gate(
                ip,
                "tb-gen",
                "tb_blocked",
                decision_needed=str(blocked_doc.get("reason") or "TB generation blocked by SSOT/RTL contract"),
                evidence={"ssot_refs": [f"{ip}/yaml/{ip}.ssot.yaml"], "tool_logs": [f"{ip}/tb/cocotb/tb_blocked.json"], "goal_ids": []},
            )
            blocker = str(q.relative_to(self.root))
            extra.append(blocker)
        return self._append_engine_result(result, "tb-gen", artifacts=extra, blocker=blocker)

    def _stage_sim(self, ip: str) -> StageResult:
        return self._append_engine_result(self.stage_engine.run_stage("sim", ip), "sim")

    def _stage_sim_debug(self, ip: str) -> StageResult:
        result = self.stage_engine.run_stage("sim-debug", ip)
        extra: list[str] = []
        blocker = result.blocker
        items = []
        if isinstance(result.metadata, dict):
            raw_items = result.metadata.get("human_gate_classifications")
            if isinstance(raw_items, list):
                items = raw_items
        for item in items:
            if not isinstance(item, dict):
                continue
            q = self._write_human_gate(
                ip,
                "sim-debug",
                str(item.get("goal_id") or "mismatch"),
                decision_needed=str(item.get("human_question") or "Resolve simulation mismatch semantic ownership."),
                evidence=item.get("evidence") if isinstance(item.get("evidence"), dict) else {"goal_ids": [item.get("goal_id")]},
            )
            rel = str(q.relative_to(self.root))
            blocker = blocker or rel
            extra.append(rel)
        return self._append_engine_result(result, "sim-debug", artifacts=extra, blocker=blocker)

    def _stage_goal_audit(self, ip: str) -> StageResult:
        return self._append_engine_result(self.stage_engine.run_stage("goal-audit", ip), "goal-audit")

    def run(self, *, ip: str, requirement_path: str | Path | None = None, stages: list[str]) -> WorkflowResult:
        ip = _safe_name(ip, "headless_ip")
        self.root.mkdir(parents=True, exist_ok=True)
        self._ip_dir(ip).mkdir(parents=True, exist_ok=True)
        self._write_progress(ip, "run_start", target_ip=ip, root=str(self.root), model=self.model, stages=stages)
        self._write_heartbeat(ip, state="running", phase="init", model=self.model, current_stage="")
        self.stages = []
        if requirement_path is not None:
            req_text = self._copy_requirement(ip, Path(requirement_path))
            req_rel = f"{ip}/req/{ip}_requirements.md"
            req_status = self._validate_req(ip, req_text)
            if req_status and req_status.status == "human_gate":
                return self._finish(ip)
        else:
            existing_req = self._ip_dir(ip) / "req" / f"{ip}_requirements.md"
            req_text = existing_req.read_text(encoding="utf-8", errors="replace") if existing_req.is_file() else ""
            req_rel = str(existing_req.relative_to(self.root)) if existing_req.is_file() else ""
        context = {
            "ip": ip,
            "root": str(self.root),
            "requirement_text": req_text,
            "requirement_path": req_rel,
        }
        for stage in stages:
            canonical = _canonical_headless_stage(stage)
            self._write_progress(ip, "stage_start", stage=canonical)
            self._write_heartbeat(ip, state="running", phase="stage", current_stage=canonical, model=self.model)
            if canonical == "ssot-gen":
                self._run_ssot_generation(ip, context)
            elif canonical == "fl-model-gen":
                self._stage_fl_model(ip)
            elif canonical == "cl-model-gen":
                self._stage_cl_model(ip)
            elif canonical == "dual-fcov":
                self._stage_dual_fcov(ip)
            elif canonical == "equiv-goals":
                self._stage_equiv_goals(ip)
            elif canonical == "rtl-gen":
                self._stage_rtl_gen(ip, context)
            elif canonical == "lint":
                self._stage_lint(ip)
            elif canonical == "tb-gen":
                self._stage_tb_gen(ip, context)
            elif canonical == "coverage":
                self._append_engine_result(self.stage_engine.run_stage("coverage", ip), "coverage")
            elif canonical == "sim":
                self._stage_sim(ip)
            elif canonical == "sim-debug":
                self._stage_sim_debug(ip)
            elif canonical == "goal-audit":
                self._stage_goal_audit(ip)
            else:
                self._append(canonical, "fail", f"unknown stage {stage}", returncode=2)

            if self.stages and self.stages[-1].status in {"fail", "human_gate", "blocked"}:
                self._write_progress(
                    ip,
                    "stage_end",
                    stage=canonical,
                    status=self.stages[-1].status,
                    message=self.stages[-1].message[:400],
                )
                break
            if self.stages:
                self._write_progress(
                    ip,
                    "stage_end",
                    stage=canonical,
                    status=self.stages[-1].status,
                    message=self.stages[-1].message[:400],
                )
        return self._finish(ip)

    def _finish(self, ip: str) -> WorkflowResult:
        status = "pass"
        for stage in self.stages:
            if stage.status in {"human_gate", "blocked"}:
                status = "blocked"
                break
            if stage.status != "pass":
                status = "fail"
                break
        run_log = self._ip_dir(ip) / "logs" / "headless_run.json"
        result = WorkflowResult(ip=ip, status=status, stages=self.stages, root=str(self.root), run_log=str(run_log.relative_to(self.root)))
        _write_json(run_log, result.to_dict())
        self._write_trace_summary(ip=ip, run_status=status)
        self._write_progress(ip, "run_end", status=status, run_log=str(run_log))
        self._write_heartbeat(ip, state="done", phase="finished", status=status, model=self.model)
        return result

    def _write_trace_summary(self, *, ip: str, run_status: str) -> None:
        llm_dir = self._log_dir(ip)
        stage_engine_dir = self._ip_dir(ip) / "logs" / "stage_engine"
        out_path = self._ip_dir(ip) / "logs" / "trace_summary.json"

        by_stage: dict[str, dict[str, Any]] = {}
        totals: dict[str, Any] = {
            "calls": 0,
            "repair_calls": 0,
            "repair_rate": 0.0,
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_read_tokens": 0,
            "total_tokens": 0,
            "cost_usd": 0.0,
        }

        llm_files = sorted(llm_dir.glob("*.json"))
        for path in llm_files:
            data = _read_json(path)
            stage_name = str(data.get("stage") or path.stem).strip() or "unknown"
            usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
            cost = usage.get("cost") if isinstance(usage.get("cost"), dict) else {}
            is_repair = ("repair" in path.stem) or ("repair" in str(data.get("raw_response") or "").lower())

            row = by_stage.setdefault(
                stage_name,
                {
                    "calls": 0,
                    "repair_calls": 0,
                    "repair_rate": 0.0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cache_read_tokens": 0,
                    "total_tokens": 0,
                    "cost_usd": 0.0,
                    "models": [],
                },
            )
            row["calls"] += 1
            row["repair_calls"] += 1 if is_repair else 0
            row["input_tokens"] += int(usage.get("input", 0) or 0)
            row["output_tokens"] += int(usage.get("output", 0) or 0)
            row["cache_read_tokens"] += int(usage.get("cache_read", 0) or 0)
            row["total_tokens"] += int(usage.get("total", 0) or 0)
            row["cost_usd"] += float(cost.get("usd", 0.0) or 0.0)
            model_name = str(data.get("model") or "").strip()
            if model_name and model_name not in row["models"]:
                row["models"].append(model_name)

            totals["calls"] += 1
            totals["repair_calls"] += 1 if is_repair else 0
            totals["input_tokens"] += int(usage.get("input", 0) or 0)
            totals["output_tokens"] += int(usage.get("output", 0) or 0)
            totals["cache_read_tokens"] += int(usage.get("cache_read", 0) or 0)
            totals["total_tokens"] += int(usage.get("total", 0) or 0)
            totals["cost_usd"] += float(cost.get("usd", 0.0) or 0.0)

        for row in by_stage.values():
            calls = int(row.get("calls", 0) or 0)
            repairs = int(row.get("repair_calls", 0) or 0)
            row["repair_rate"] = (float(repairs) / float(calls)) if calls else 0.0
        totals["repair_rate"] = (float(totals["repair_calls"]) / float(totals["calls"])) if totals["calls"] else 0.0

        stage_engine_order: list[dict[str, Any]] = []
        for stage_file in sorted(stage_engine_dir.glob("*.json")):
            info = _read_json(stage_file)
            stage_engine_order.append(
                {
                    "stage_engine": stage_file.stem,
                    "status": str(info.get("status") or "").strip(),
                    "created_at": str(info.get("created_at") or "").strip(),
                }
            )

        blocked_at = ""
        if self.stages:
            last = self.stages[-1]
            if last.status in {"fail", "blocked", "human_gate"}:
                blocked_at = last.stage

        _write_json(
            out_path,
            {
                "ip": ip,
                "run_status": run_status,
                "blocked_at_stage": blocked_at,
                "llm_log_files": len(llm_files),
                "llm": {"totals": totals, "by_stage": by_stage},
                "stage_engine_order": stage_engine_order,
            },
        )


def _make_provider(kind: str, fixture: str = "") -> LLMProvider:
    if kind == "real":
        return RealLLMProvider(required_model=os.getenv("ATLAS_HEADLESS_REQUIRED_MODEL", ""))
    if kind == "cached":
        if not fixture:
            raise SystemExit("--fixture is required for cached provider")
        return CachedLLMProvider(fixture)
    return FakeLLMProvider()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--ip", required=True)
    parser.add_argument("--req", default="")
    parser.add_argument("--model", default=os.getenv("ATLAS_HEADLESS_LLM_MODEL", "glm-5.1"))
    parser.add_argument("--stages", required=True, help="comma-separated stage list")
    parser.add_argument("--provider", choices=["fake", "cached", "real"], default="real")
    parser.add_argument("--fixture", default="")
    args = parser.parse_args(argv)
    stages = [_canonical_headless_stage(part.strip()) for part in args.stages.split(",") if part.strip()]
    if not args.req and "ssot-gen" in stages:
        parser.error("--req is required when ssot-gen is requested")

    provider = _make_provider(args.provider, args.fixture)
    runner = HeadlessWorkflowRunner(
        root=args.root,
        model=args.model,
        llm_provider=provider,
        require_glm51=args.provider == "real" and os.getenv("ATLAS_HEADLESS_REQUIRE_GLM51") == "1",
    )
    result = runner.run(
        ip=args.ip,
        requirement_path=args.req or None,
        stages=stages,
    )
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0 if result.status == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
