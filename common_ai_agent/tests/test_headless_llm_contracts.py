from __future__ import annotations

import json
import importlib.util
import subprocess
from pathlib import Path

import yaml

from src.headless_workflow import (
    CachedLLMProvider,
    FakeLLMProvider,
    HeadlessWorkflowRunner,
    LLMResponse,
    _structured_ssot_yaml,
    parse_llm_artifacts,
)


class CapturingProvider:
    def __init__(self, response: str):
        self.response = response
        self.calls = []

    def complete(self, **kwargs):
        self.calls.append(kwargs)
        return LLMResponse(
            stage=kwargs["stage"],
            model=kwargs["model"],
            raw_response=self.response,
            error="model output did not contain expected JSON object with files[] SSOT artifact",
            status="blocked",
        )


class SequencedArtifactProvider:
    def __init__(self, artifacts_by_call: list[list[dict[str, str]]]):
        self.artifacts_by_call = artifacts_by_call
        self.calls = []

    def complete(self, **kwargs):
        self.calls.append(kwargs)
        index = len(self.calls) - 1
        artifacts = self.artifacts_by_call[min(index, len(self.artifacts_by_call) - 1)]
        return LLMResponse(
            stage=kwargs["stage"],
            model=kwargs["model"],
            raw_response=json.dumps({"files": artifacts}, indent=2),
            parsed_artifacts=artifacts,
        )


def _write_req(tmp_path: Path, ip: str) -> Path:
    req = tmp_path / "req.md"
    text = (
        f"{ip} samples data_in when valid is asserted after reset deassertion. "
        "The output result equals two times the sampled value on the next cycle. "
        "ready remains asserted after reset, result_valid marks the result cycle, "
        "and the generated FunctionalModel is the only source of expected values. "
        "The testbench must use equivalence goals and produce scoreboard events. "
        "DUT-only compile and lint are required before simulation. "
    )
    req.write_text("# Requirement\n\n" + text * 5 + "\n", encoding="utf-8")
    return req


def _write_ssot_doc(root: Path, ip: str, doc: dict) -> Path:
    path = root / ip / "yaml" / f"{ip}.ssot.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    return path


def _base_ssot_doc(ip: str) -> dict:
    return yaml.safe_load(_structured_ssot_yaml(ip, "sample data_in when valid and double it. " * 20))


def _run_check_ssot(root: Path, ip: str, extra_args: list[str] | None = None) -> subprocess.CompletedProcess[str]:
    script = Path(__file__).resolve().parents[1] / "workflow" / "ssot-gen" / "scripts" / "check_ssot_disk.sh"
    return subprocess.run(
        ["bash", str(script), ip, *(extra_args or [])],
        cwd=str(root),
        text=True,
        capture_output=True,
        timeout=30,
    )


def _run_repair_ssot(root: Path, ip: str, extra_args: list[str] | None = None) -> subprocess.CompletedProcess[str]:
    script = Path(__file__).resolve().parents[1] / "workflow" / "ssot-gen" / "scripts" / "repair_ssot_schema.py"
    return subprocess.run(
        ["python3", str(script), ip, "--root", str(root), *(extra_args or [])],
        cwd=str(Path(__file__).resolve().parents[1]),
        text=True,
        capture_output=True,
        timeout=30,
    )


def _run_ssot_to_rtl(root: Path, ip: str) -> subprocess.CompletedProcess[str]:
    script = Path(__file__).resolve().parents[1] / "workflow" / "rtl-gen" / "scripts" / "ssot_to_rtl.py"
    return subprocess.run(
        ["python3", str(script), ip, "--root", str(root)],
        cwd=str(Path(__file__).resolve().parents[1]),
        text=True,
        capture_output=True,
        timeout=30,
    )


def _run_derive_rtl_todos(root: Path, ip: str, *, audit_rtl: bool = False) -> subprocess.CompletedProcess[str]:
    script = Path(__file__).resolve().parents[1] / "workflow" / "rtl-gen" / "scripts" / "derive_rtl_todos.py"
    args = ["python3", str(script), ip, "--root", str(root)]
    if audit_rtl:
        args.append("--audit-rtl")
    return subprocess.run(
        args,
        cwd=str(Path(__file__).resolve().parents[1]),
        text=True,
        capture_output=True,
        timeout=30,
    )


def _load_derive_rtl_todos():
    path = Path(__file__).resolve().parents[1] / "workflow" / "rtl-gen" / "scripts" / "derive_rtl_todos.py"
    spec = importlib.util.spec_from_file_location("derive_rtl_todos_under_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parse_llm_artifacts_tolerates_trailing_json_mode_noise():
    raw = json.dumps(
        {
            "files": [
                {
                    "path": "noise_ip/rtl/noise_ip.sv",
                    "kind": "rtl",
                    "content": "`default_nettype none\nmodule noise_ip; endmodule\n",
                }
            ]
        }
    ) + "]}"

    artifacts = parse_llm_artifacts("rtl-gen", raw, ip="noise_ip")

    assert artifacts == [
        {
            "path": "noise_ip/rtl/noise_ip.sv",
            "kind": "rtl",
            "content": "`default_nettype none\nmodule noise_ip; endmodule\n",
        }
    ]


def test_parse_llm_artifacts_finds_json_after_prose_braces():
    raw = (
        "Using `{DATA_WIDTH{1'b0}}` for reset and returning JSON next.\n"
        + json.dumps(
            {
                "files": [
                    {
                        "path": "brace_noise_ip/rtl/brace_noise_ip.sv",
                        "kind": "rtl",
                        "content": "module brace_noise_ip; endmodule\n",
                    }
                ]
            }
        )
    )

    artifacts = parse_llm_artifacts("rtl-gen", raw, ip="brace_noise_ip")

    assert artifacts == [
        {
            "path": "brace_noise_ip/rtl/brace_noise_ip.sv",
            "kind": "rtl",
            "content": "module brace_noise_ip; endmodule\n",
        }
    ]


def test_cached_glm51_ssot_response_validates_with_artifact_contract(tmp_path: Path):
    ip = "cached_glm_contract_ip"
    req = _write_req(tmp_path, ip)
    fixture = tmp_path / "fixtures" / "glm_5_1" / "valid_ssot"
    fixture.mkdir(parents=True)
    raw = json.dumps(
        {
            "files": [
                {
                    "path": f"{ip}/yaml/{ip}.ssot.yaml",
                    "kind": "ssot",
                    "content": _structured_ssot_yaml(ip, req.read_text(encoding="utf-8")),
                }
            ]
        },
        indent=2,
    )
    (fixture / "raw_response.txt").write_text(raw, encoding="utf-8")
    (fixture / "prompt.md").write_text("cached GLM-5.1 SSOT prompt\n", encoding="utf-8")
    (fixture / "expected_artifact_kind.json").write_text('{"kind":"ssot"}\n', encoding="utf-8")
    (fixture / "expected_validator_result.json").write_text('{"status":"pass"}\n', encoding="utf-8")

    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="glm-5.1",
        llm_provider=CachedLLMProvider(fixture),
    )
    result = runner.run(ip=ip, requirement_path=req, stages=["ssot-gen"])

    assert result.status == "pass"
    ssot = (tmp_path / "work" / ip / "yaml" / f"{ip}.ssot.yaml").read_text(encoding="utf-8")
    assert "function_model:" in ssot
    assert "cycle_model:" in ssot
    log = json.loads((tmp_path / "work" / ip / "logs" / "llm" / "ssot-gen.json").read_text(encoding="utf-8"))
    assert log["model"] == "glm-5.1"
    assert log["output_hash"]


def test_ssot_prompt_for_headless_real_provider_requires_json_artifact_only(tmp_path: Path):
    ip = "headless_prompt_contract_ip"
    req = _write_req(tmp_path, ip)
    provider = CapturingProvider("I'll start by scaffolding the IP directory.")
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="glm-5.1",
        llm_provider=provider,
    )

    result = runner.run(ip=ip, requirement_path=req, stages=["ssot-gen"])

    assert result.status == "blocked"
    assert provider.calls
    call = provider.calls[0]
    assert "HEADLESS PROVIDER CONTRACT" in call["system_prompt"]
    assert "Return exactly one JSON object and nothing else" in call["prompt"]
    assert f'"path": "{ip}/yaml/{ip}.ssot.yaml"' in call["prompt"]
    assert "function_model" in call["prompt"]
    assert "cycle_model" in call["prompt"]
    assert "human_gate" in call["prompt"]
    assert "machine-readable integration.connections" in call["prompt"]
    log = json.loads((tmp_path / "work" / ip / "logs" / "llm" / "ssot-gen.json").read_text(encoding="utf-8"))
    assert "files[]" in log["error"]


def test_check_ssot_disk_starter_accepts_minimal_ssot(tmp_path: Path):
    ip = "starter_pwm"
    doc = {
        "top_module": {
            "name": ip,
            "description": "Starter-mode PWM requirement. User-authored intent only; downstream boilerplate can be generated defaults.",
        },
        "io_list": {
            "interfaces": [
                {
                    "name": "pins",
                    "type": "raw",
                    "ports": [
                        {"name": "clk", "direction": "input", "width": 1},
                        {"name": "rst_n", "direction": "input", "width": 1},
                        {"name": "enable", "direction": "input", "width": 1},
                        {"name": "pwm_o", "direction": "output", "width": 1},
                    ],
                }
            ],
        },
        "function_model": {
            "description": "When enabled, pwm_o is high while the counter is below duty.",
            "transactions": [
                {"id": "tick", "description": "Advance one PWM cycle from user intent."},
            ],
        },
    }
    _write_ssot_doc(tmp_path, ip, doc)

    result = _run_check_ssot(tmp_path, ip, ["--mode", "starter"])

    assert result.returncode == 0, result.stdout + result.stderr
    assert "mode=starter" in result.stdout


def test_headless_runner_uses_starter_mode_for_ssot_contract_check(tmp_path: Path):
    ip = "runner_starter_pwm"
    doc = {
        "top_module": {"name": ip, "description": "Minimal starter SSOT."},
        "io_list": {"interfaces": [{"name": "pins", "ports": [{"name": "clk", "direction": "input", "width": 1}]}]},
        "function_model": {"description": "Starter behavior intent.", "transactions": [{"id": "tick"}]},
    }
    _write_ssot_doc(tmp_path, ip, doc)
    runner = HeadlessWorkflowRunner(root=tmp_path, llm_provider=FakeLLMProvider(), run_mode="starter")

    result = runner._check_ssot_contract(ip, emit_gate=False)

    assert result.status == "pass"


def test_check_ssot_disk_engineering_allows_signoff_only_sections_to_be_absent(tmp_path: Path):
    ip = "engineering_no_pnr_dft"
    doc = _base_ssot_doc(ip)
    doc["top_module"]["file"] = f"rtl/{ip}.sv"
    doc["sub_modules"] = [
        sub for sub in (doc.get("sub_modules") or [])
        if not (isinstance(sub, dict) and sub.get("name") == ip)
    ]
    doc.pop("dft", None)
    doc.pop("pnr", None)
    _write_ssot_doc(tmp_path, ip, doc)

    engineering = _run_check_ssot(tmp_path, ip, ["--mode", "engineering"])
    signoff = _run_check_ssot(tmp_path, ip, ["--mode", "signoff"])

    assert engineering.returncode == 0, engineering.stdout + engineering.stderr
    assert "mode=engineering" in engineering.stdout
    assert signoff.returncode != 0
    assert "required sections" in signoff.stdout or "top-level section keys" in signoff.stdout


def test_repair_ssot_schema_writes_provenance_sidecar_for_generated_defaults(tmp_path: Path):
    ip = "starter_repair_provenance"
    doc = _base_ssot_doc(ip)
    doc.pop("dft", None)
    doc.pop("pnr", None)
    doc.pop("quality_gates", None)
    _write_ssot_doc(tmp_path, ip, doc)

    result = _run_repair_ssot(tmp_path, ip, ["--mode", "starter"])

    assert result.returncode == 0, result.stdout + result.stderr
    sidecar = tmp_path / ip / "yaml" / f"{ip}.ssot.provenance.json"
    assert sidecar.is_file()
    provenance = json.loads(sidecar.read_text(encoding="utf-8"))
    assert provenance["run_mode"] == "starter"
    fields = {item["path"]: item for item in provenance["fields"]}
    assert fields["quality_gates"]["authority"] == "generated_default"
    assert fields["quality_gates"]["review_needed_for"] == "signoff"
    assert fields["quality_gates.ssot.pass"]["authority"] == "generated_default"
    assert fields["quality_gates.ssot.pass"]["signoff_critical"] is True
    assert fields["top_module"]["authority"] == "user"
    assert fields["top_module.name"]["authority"] == "user"


def test_check_ssot_disk_requires_production_rtl_gen_gate(tmp_path: Path):
    ip = "production_missing_rtl_gen_gate"
    doc = _base_ssot_doc(ip)
    doc["quality_gates"]["rtl_gen"] = {"profile": "production"}
    doc["integration"]["connections"] = [
        {"module": f"{ip}_core", "port": "clk", "signal": "clk"},
    ]
    _write_ssot_doc(tmp_path, ip, doc)

    result = _run_check_ssot(tmp_path, ip)

    assert result.returncode != 0
    assert "quality_gates.rtl_gen.pass and .evidence are required" in result.stdout


def test_check_ssot_disk_requires_production_multi_module_connections(tmp_path: Path):
    ip = "production_missing_connections"
    doc = _base_ssot_doc(ip)
    doc["quality_gates"]["rtl_gen"] = {
        "profile": "production",
        "pass": "production RTL gates close",
        "evidence": ["rtl/rtl_todo_plan.json"],
    }
    doc["sub_modules"].append(
        {
            "name": f"{ip}_core",
            "file": f"rtl/{ip}_core.sv",
            "ownership": "manifest",
            "implements": ["function_model.transactions", "cycle_model.pipeline"],
            "source_sections": ["function_model", "cycle_model"],
            "description": "Active child module that requires machine-readable top integration wiring.",
        }
    )
    doc["integration"].pop("connections", None)
    _write_ssot_doc(tmp_path, ip, doc)

    result = _run_check_ssot(tmp_path, ip)

    assert result.returncode != 0
    assert "production multi-module SSOT requires machine-readable integration.connections" in result.stdout

    doc["integration"]["connections"] = [
        {"module": f"{ip}_core", "port": "clk", "signal": "clk"},
        {"module": f"{ip}_core", "port": "rst_n", "signal": "rst_n"},
        {"module": f"{ip}_core", "port": "valid", "signal": "valid"},
    ]
    _write_ssot_doc(tmp_path, ip, doc)

    result = _run_check_ssot(tmp_path, ip)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "[check_ssot_disk] PASS" in result.stdout


def test_check_ssot_disk_allows_deferred_connection_contract_todo(tmp_path: Path):
    ip = "production_deferred_connections"
    doc = _base_ssot_doc(ip)
    doc["quality_gates"]["rtl_gen"] = {
        "profile": "production",
        "pass": "production RTL gates close",
        "evidence": ["rtl/rtl_todo_plan.json"],
    }
    doc["integration"].pop("connections", None)
    doc["workflow_todos"]["rtl-gen"].append(
        {
            "id": "RTL_RESOLVE_CONNECTION_CONTRACTS",
            "content": "Resolve production multi-module connection contracts before top integration signoff",
            "detail": "Add machine-readable integration.connections or sub_modules[].connections records with module/port/signal data.",
            "criteria": ["Top integration remains blocked until connection contracts exist"],
            "source_refs": ["integration.connections", "sub_modules[].connections", "quality_gates.rtl_gen"],
            "priority": "high",
            "required": True,
        }
    )
    _write_ssot_doc(tmp_path, ip, doc)

    result = _run_check_ssot(tmp_path, ip)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "[check_ssot_disk] PASS" in result.stdout


def test_repair_downgrades_smoke_fixture_from_production_target_scale_gate(tmp_path: Path):
    ip = "timer"
    doc = _base_ssot_doc(ip)
    doc["top_module"]["description"] = "Small countdown timer smoke-test fixture for the SSOT pipeline."
    doc["quality_gates"]["rtl_gen"] = {
        "profile": "production",
        "pass": "production RTL gates close",
        "evidence": ["rtl/rtl_todo_plan.json"],
    }
    doc["workflow_todos"]["rtl-gen"].append(
        {
            "id": "RTL_TARGET_SCALE_POLICY",
            "content": "Lock or waive RTL target-scale policy before production signoff",
            "detail": "The SSOT is production-profile and needs target_scale.",
            "criteria": ["quality_gates.rtl_gen.target_scale contains positive structural minima"],
            "source_refs": ["quality_gates.rtl_gen.target_scale"],
            "priority": "high",
            "required": True,
        }
    )
    _write_ssot_doc(tmp_path, ip, doc)

    result = _run_repair_ssot(tmp_path, ip)

    assert result.returncode == 0, result.stdout + result.stderr
    repaired = yaml.safe_load((tmp_path / ip / "yaml" / f"{ip}.ssot.yaml").read_text(encoding="utf-8"))
    assert repaired["quality_gates"]["rtl_gen"]["profile"] == "standard"
    rtl_todos = repaired["workflow_todos"]["rtl-gen"]
    assert all(item.get("id") != "RTL_TARGET_SCALE_POLICY" for item in rtl_todos)
    result = _run_check_ssot(tmp_path, ip)
    assert result.returncode == 0, result.stdout + result.stderr


def test_check_ssot_disk_requires_executable_function_model_output_rules(tmp_path: Path):
    ip = "missing_output_rules_ip"
    doc = _base_ssot_doc(ip)
    for tx in doc["function_model"]["transactions"]:
        tx.pop("output_rules", None)
    _write_ssot_doc(tmp_path, ip, doc)

    result = _run_check_ssot(tmp_path, ip)

    assert result.returncode != 0
    assert "function_model.transactions[] must include at least one executable output_rules entry" in result.stdout


def test_ssot_downstream_readiness_blocks_prose_only_function_transactions(tmp_path: Path):
    ip = "prose_only_fm_ip"
    doc = _base_ssot_doc(ip)
    doc["function_model"]["transactions"].append(
        {
            "id": "FM_STATUS_POLL",
            "name": "status_poll",
            "preconditions": ["host reads status register"],
            "outputs": ["status bus returns the current pending interrupt state"],
            "side_effects": ["no architectural state change"],
            "error_cases": ["none"],
        }
    )
    _write_ssot_doc(tmp_path, ip, doc)

    result = _run_check_ssot(tmp_path, ip)

    assert result.returncode != 0
    assert "function_model.transactions[1] must include executable output_rules or state_updates" in result.stdout

    repaired = _run_repair_ssot(tmp_path, ip, ["--strict-downstream"])

    assert repaired.returncode == 2
    blockers_path = tmp_path / ip / "req" / "ssot_downstream_blockers.json"
    blockers = json.loads(blockers_path.read_text(encoding="utf-8"))
    assert any(issue["id"] == "SSOT_FM_MACHINE_RULES_MISSING_FM_STATUS_POLL" for issue in blockers["issues"])


def test_check_ssot_disk_allows_inout_output_rule_observable(tmp_path: Path):
    ip = "inout_observable_ip"
    doc = _base_ssot_doc(ip)
    doc["io_list"]["interfaces"].append(
        {
            "name": "bidir_pad",
            "type": "custom",
            "clock_domain": "main",
            "ports": [{"name": "gpio_pins", "direction": "inout", "width": 32, "description": "Bidirectional pad"}],
            "protocol": {"drive": "Output-mode bits are driven; input-mode bits are observed."},
        }
    )
    tx = doc["function_model"]["transactions"][0]
    tx["output_rules"] = [{"name": "gpio_pins", "port": "gpio_pins", "expr": "data_in", "width": 32}]
    _write_ssot_doc(tmp_path, ip, doc)

    result = _run_check_ssot(tmp_path, ip)

    assert result.returncode == 0, result.stdout + result.stderr


def test_repair_ssot_schema_infers_shift_output_rules_and_concrete_port_maps(tmp_path: Path):
    ip = "repair_shift_rules_ip"
    doc = _base_ssot_doc(ip)
    tx = doc["function_model"]["transactions"][0]
    tx.pop("output_rules", None)
    tx.pop("state_updates", None)
    tx["outputs"] = [
        "On the immediately following cycle result_valid is one and result equals unsigned shift left by one of data_in.",
        "accepted_count increments by one on the commit edge.",
    ]
    tx["side_effects"] = ["accepted_count increments by one on each valid and ready commit."]
    doc["rtl_contract"]["transaction"] = (
        "FM_ACCEPT_SHIFT prose: result equals data_in shifted left by one and accepted_count increments."
    )
    doc["rtl_contract"]["input_map"] = {
        "data_in": "io_list.interfaces.rule_io.ports.data_in",
        "valid": "io_list.interfaces.rule_io.ports.valid",
        "ready": "io_list.interfaces.rule_io.ports.ready",
    }
    doc["rtl_contract"]["output_map"] = {
        "result": "io_list.interfaces.rule_io.ports.result",
        "result_valid": "io_list.interfaces.rule_io.ports.result_valid",
        "ready": "io_list.interfaces.rule_io.ports.ready",
    }
    _write_ssot_doc(tmp_path, ip, doc)
    assert _run_check_ssot(tmp_path, ip).returncode != 0

    repaired = _run_repair_ssot(tmp_path, ip)

    assert repaired.returncode == 0, repaired.stdout + repaired.stderr
    result = _run_check_ssot(tmp_path, ip)
    assert result.returncode == 0, result.stdout + result.stderr
    loaded = yaml.safe_load((tmp_path / ip / "yaml" / f"{ip}.ssot.yaml").read_text(encoding="utf-8"))
    tx = loaded["function_model"]["transactions"][0]
    assert tx["output_rules"][0]["port"] == "result"
    assert tx["output_rules"][0]["expr"] == "data_in << 1"
    assert tx["state_updates"][0]["name"] == "accepted_count"
    assert loaded["rtl_contract"]["transaction"] == tx["id"]
    assert loaded["rtl_contract"]["input_map"]["data_in"] == "data_in"
    assert loaded["rtl_contract"]["output_map"]["result"] == "result"


def test_repair_ssot_schema_moves_internal_output_rules_to_state_updates(tmp_path: Path):
    ip = "repair_internal_output_rule_ip"
    doc = _base_ssot_doc(ip)
    fm = doc["function_model"]
    fm["state_variables"].append({"name": "int_status_q", "reset": 0, "width": 8})
    fm["transactions"].append(
        {
            "id": "FM_W1C_CLEAR",
            "name": "w1c_clear_with_set_priority",
            "preconditions": ["w1c write to interrupt status"],
            "outputs": ["int_status_q is updated after clear and new event set priority"],
            "side_effects": ["update interrupt status state"],
            "output_rules": [
                {
                    "name": "int_status_next_rule",
                    "expr": "(int_status_q & ~w1c_mask) | event_set",
                    "width": 8,
                    "port": "int_status_next",
                }
            ],
        }
    )
    _write_ssot_doc(tmp_path, ip, doc)
    assert _run_check_ssot(tmp_path, ip).returncode != 0

    repaired = _run_repair_ssot(tmp_path, ip)

    assert repaired.returncode == 0, repaired.stdout + repaired.stderr
    result = _run_check_ssot(tmp_path, ip)
    assert result.returncode == 0, result.stdout + result.stderr
    loaded = yaml.safe_load((tmp_path / ip / "yaml" / f"{ip}.ssot.yaml").read_text(encoding="utf-8"))
    tx = next(item for item in loaded["function_model"]["transactions"] if item["id"] == "FM_W1C_CLEAR")
    assert tx["output_rules"] == []
    assert any(item["name"] == "int_status_q" for item in tx["state_updates"])


def test_repair_ssot_schema_does_not_promote_rule_helpers_to_io(tmp_path: Path):
    ip = "repair_rule_helper_ports_ip"
    doc = _base_ssot_doc(ip)
    iface_ports = doc["io_list"]["interfaces"][0]["ports"]
    iface_ports.extend(
        [
            {
                "name": "read_mux",
                "width": 1,
                "direction": "input",
                "description": "Auto-derived 1-bit input from rule expression 'read_mux'",
            },
            {
                "name": "edge_event",
                "width": 1,
                "direction": "input",
                "description": "Auto-derived 1-bit input from rule expression 'edge_event'",
            },
        ]
    )
    doc["function_model"]["derived_signals"] = [
        {"name": "edge_event", "expr": "status_q & enable_q", "width": 1}
    ]
    doc["function_model"]["state_variables"].extend(
        [
            {"name": "status_q", "reset": 0, "width": 8},
            {"name": "enable_q", "reset": 0, "width": 8},
        ]
    )
    tx = doc["function_model"]["transactions"][0]
    tx["required_fields"] = ["paddr"]
    tx["output_rules"] = [
        {"name": "result", "port": "result", "expr": "read_mux(paddr)", "width": 9},
        {"name": "result_valid", "port": "result_valid", "expr": "reduction_or(edge_event)", "width": 1},
    ]
    tx["state_updates"] = [{"name": "status_q", "expr": "status_q | edge_event", "width": 8}]
    doc["rtl_contract"]["input_map"] = {
        "paddr": "paddr",
        "read_mux": "read_mux",
        "edge_event": "edge_event",
    }
    _write_ssot_doc(tmp_path, ip, doc)

    repaired = _run_repair_ssot(tmp_path, ip)

    assert repaired.returncode == 0, repaired.stdout + repaired.stderr
    loaded = yaml.safe_load((tmp_path / ip / "yaml" / f"{ip}.ssot.yaml").read_text(encoding="utf-8"))
    port_names = {
        port["name"]
        for iface in loaded["io_list"]["interfaces"]
        for port in iface.get("ports", [])
    }
    assert "read_mux" not in port_names
    assert "edge_event" not in port_names
    assert "paddr" not in loaded["rtl_contract"].get("unresolved_expression_refs", [])
    assert "read_mux" not in loaded["rtl_contract"]["input_map"]
    assert "edge_event" not in loaded["rtl_contract"]["input_map"]


def test_repair_ssot_schema_derives_apb_helpers_and_breaks_output_self_dependencies(tmp_path: Path):
    ip = "repair_apb_helpers_ip"
    doc = _base_ssot_doc(ip)
    doc["io_list"] = {
        "clock_domains": [{"name": "bus", "ports": [{"name": "pclk", "direction": "input", "width": 1}]}],
        "resets": [{"name": "presetn", "polarity": "active_low", "ports": [{"name": "presetn", "direction": "input", "width": 1}]}],
        "interfaces": [
            {
                "name": "apb4",
                "type": "apb4",
                "role": "target",
                "clock_domain": "bus",
                "ports": [
                    {"name": "paddr", "direction": "input", "width": 12},
                    {"name": "psel", "direction": "input", "width": 1},
                    {"name": "penable", "direction": "input", "width": 1},
                    {"name": "pwrite", "direction": "input", "width": 1},
                    {"name": "pwdata", "direction": "input", "width": 32},
                    {"name": "pstrb", "direction": "input", "width": 4},
                    {"name": "prdata", "direction": "output", "width": 32},
                    {"name": "pready", "direction": "output", "width": 1},
                    {"name": "pslverr", "direction": "output", "width": 1},
                ],
            }
        ],
    }
    tx = doc["function_model"]["transactions"][0]
    tx["id"] = "FM_APB_WRITE_RW"
    tx["preconditions"] = ["apb_valid_write == 1", "addr == 0x00"]
    tx["inputs"] = ["paddr", "pwdata", "pstrb"]
    doc["registers"] = {
        "config": {"register_width": 32, "addr_width": 12},
        "register_list": [
            {"name": "CTRL", "offset": 0, "width": 32, "access": "rw"},
            {"name": "STATUS", "offset": 4, "width": 32, "access": "ro"},
        ],
    }
    doc["function_model"]["state_variables"].extend(
        [
            {"name": "ctrl_reg", "reset": 0, "width": 32},
            {"name": "status_reg", "reset": 0, "width": 32},
        ]
    )
    doc["function_model"]["derived_signals"] = [
        {
            "name": "wmask",
            "expr": "((pstrb & 0xF) * 255)",
            "width": 32,
            "description": "stale non-byte-lane APB mask from LLM draft",
        }
    ]
    tx["output_rules"] = [
        {"name": "apb_write_pready", "port": "pready", "width": 1, "expr": "1 if apb_valid_write else pready"},
        {"name": "apb_write_pslverr", "port": "pslverr", "width": 1, "expr": "0 if apb_valid_write else pslverr"},
        {"name": "apb_read_prdata", "port": "prdata", "width": 32, "expr": "read_mux if legal_addr else 0"},
    ]
    tx["state_updates"] = [
        {"name": "ctrl_reg_next", "expr": "pwdata if wr_ctrl else ctrl_reg", "width": 32},
    ]
    doc["rtl_contract"] = {
        "transaction": "FM_APB_WRITE_RW",
        "clock": "pclk",
        "reset": "presetn",
        "sample_condition": "1",
        "input_map": {"paddr": "paddr", "psel": "psel", "penable": "penable", "pwrite": "pwrite", "pwdata": "pwdata", "pstrb": "pstrb"},
        "output_map": {"pready": "pready", "pslverr": "pslverr", "prdata": "prdata"},
        "output_rules": list(tx["output_rules"]),
    }
    _write_ssot_doc(tmp_path, ip, doc)

    repaired = _run_repair_ssot(tmp_path, ip)

    assert repaired.returncode == 0, repaired.stdout + repaired.stderr
    loaded = yaml.safe_load((tmp_path / ip / "yaml" / f"{ip}.ssot.yaml").read_text(encoding="utf-8"))
    derived = {item["name"]: item for item in loaded["function_model"]["derived_signals"]}
    assert derived["apb_valid_write"]["expr"] == "psel and penable and pwrite"
    assert derived["apb_valid_read"]["expr"] == "psel and penable and not pwrite"
    assert derived["addr"]["expr"] == "paddr"
    assert derived["wmask"]["expr"] == (
        "((0x000000FF if (pstrb & 0x1) != 0 else 0) | "
        "(0x0000FF00 if (pstrb & 0x2) != 0 else 0) | "
        "(0x00FF0000 if (pstrb & 0x4) != 0 else 0) | "
        "(0xFF000000 if (pstrb & 0x8) != 0 else 0))"
    )
    assert derived["legal_addr"]["expr"] == "(addr == 0) or (addr == 4)"
    assert derived["wr_ctrl"]["expr"] == "apb_valid_write and (addr == 0)"
    assert derived["rd_status"]["expr"] == "apb_valid_read and (addr == 4)"
    assert "ctrl_reg if addr == 0 else" in derived["read_mux"]["expr"]
    tx = loaded["function_model"]["transactions"][0]
    expr_by_port = {rule["port"]: rule["expr"] for rule in tx["output_rules"]}
    assert expr_by_port["pready"] == "1"
    assert expr_by_port["pslverr"] == "0"
    preflight = _run_ssot_to_rtl(tmp_path, ip)
    assert "RTL_INPUT_MAP_APB_VALID_WRITE" not in preflight.stdout
    assert "RTL_INPUT_MAP_LEGAL_ADDR" not in preflight.stdout
    assert "RTL_INPUT_MAP_READ_MUX" not in preflight.stdout
    assert "RTL_INPUT_MAP_WR_CTRL" not in preflight.stdout
    assert "RTL_EXPR_APB_READ_PRDATA" not in preflight.stdout
    assert "RTL_OUTPUT_DEP_APB_WRITE_PREADY" not in preflight.stdout
    assert "RTL_OUTPUT_DEP_APB_WRITE_PSLVERR" not in preflight.stdout


def test_repair_ssot_schema_accepts_parameterized_apb_addr_width_and_backfills_outputs(tmp_path: Path):
    ip = "repair_apb_param_width_ip"
    doc = _base_ssot_doc(ip)
    doc["parameters"] = [
        {"name": "ADDR_WIDTH", "default": 12},
        {"name": "DATA_WIDTH", "default": 32},
    ]
    doc["io_list"] = {
        "clock_domains": [{"name": "bus", "ports": [{"name": "pclk", "direction": "input", "width": 1}]}],
        "resets": [{"name": "presetn", "polarity": "active_low", "ports": [{"name": "presetn", "direction": "input", "width": 1}]}],
        "interfaces": [
            {
                "name": "apb4",
                "type": "apb4",
                "role": "target",
                "clock_domain": "bus",
                "ports": [
                    {"name": "paddr", "direction": "input", "width": "ADDR_WIDTH"},
                    {"name": "psel", "direction": "input", "width": 1},
                    {"name": "penable", "direction": "input", "width": 1},
                    {"name": "pwrite", "direction": "input", "width": 1},
                    {"name": "pwdata", "direction": "input", "width": "DATA_WIDTH"},
                    {"name": "pstrb", "direction": "input", "width": 4},
                    {"name": "prdata", "direction": "output", "width": "DATA_WIDTH"},
                    {"name": "pready", "direction": "output", "width": 1},
                    {"name": "pslverr", "direction": "output", "width": 1},
                ],
            }
        ],
    }
    tx = doc["function_model"]["transactions"][0]
    tx["id"] = "FM_APB_WRITE"
    tx["name"] = "apb_write"
    tx["preconditions"] = ["apb_valid_write == 1"]
    tx.pop("outputs", None)
    tx["output_rules"] = [
        {"name": "pready_o", "port": "pready", "expr": 1, "width": 1},
        {"name": "pslverr_o", "port": "pslverr", "expr": 0, "width": 1},
    ]
    tx["state_updates"] = [
        {"name": "data_out_reg_next", "expr": "pwdata", "width": "DATA_WIDTH"},
    ]
    doc["rtl_contract"] = {
        "transaction": "FM_APB_WRITE",
        "clock": "pclk",
        "reset": "presetn",
        "sample_condition": "apb_valid_write",
        "input_map": {"paddr": "paddr", "psel": "psel", "penable": "penable", "pwrite": "pwrite"},
        "output_map": {"pready": "pready", "pslverr": "pslverr", "prdata": "prdata"},
        "output_rules": list(tx["output_rules"]),
    }
    _write_ssot_doc(tmp_path, ip, doc)

    repaired = _run_repair_ssot(tmp_path, ip)

    assert repaired.returncode == 0, repaired.stdout + repaired.stderr
    loaded = yaml.safe_load((tmp_path / ip / "yaml" / f"{ip}.ssot.yaml").read_text(encoding="utf-8"))
    derived = {item["name"]: item for item in loaded["function_model"]["derived_signals"]}
    assert derived["addr"]["width"] == "ADDR_WIDTH"
    tx = loaded["function_model"]["transactions"][0]
    assert tx["outputs"]
    assert any(item.get("port") == "pready" for item in tx["outputs"] if isinstance(item, dict))
    assert any(item.get("state") == "data_out_reg_next" for item in tx["outputs"] if isinstance(item, dict))
    result = _run_check_ssot(tmp_path, ip)
    assert result.returncode == 0, result.stdout + result.stderr


def test_repair_ssot_schema_loads_wrapped_expression_scalars(tmp_path: Path):
    ip = "repair_wrapped_expr_ip"
    doc = _base_ssot_doc(ip)
    doc["io_list"] = {
        "clock_domains": [{"name": "bus", "ports": [{"name": "pclk", "direction": "input", "width": 1}]}],
        "resets": [{"name": "presetn", "polarity": "active_low", "ports": [{"name": "presetn", "direction": "input", "width": 1}]}],
        "interfaces": [
            {
                "name": "apb4",
                "type": "apb4",
                "role": "target",
                "ports": [
                    {"name": "paddr", "direction": "input", "width": 12},
                    {"name": "psel", "direction": "input", "width": 1},
                    {"name": "penable", "direction": "input", "width": 1},
                    {"name": "pwrite", "direction": "input", "width": 1},
                    {"name": "pstrb", "direction": "input", "width": 4},
                    {"name": "pwdata", "direction": "input", "width": 32},
                    {"name": "prdata", "direction": "output", "width": 32},
                    {"name": "pready", "direction": "output", "width": 1},
                    {"name": "pslverr", "direction": "output", "width": 1},
                ],
            }
        ],
    }
    tx = doc["function_model"]["transactions"][0]
    tx["id"] = "FM_APB_WRITE"
    tx["output_rules"] = [{"name": "pready_o", "port": "pready", "expr": 1, "width": 1}]
    tx["state_updates"] = [
        {
            "name": "byte_mask",
            "expr": "((0x000000FF if (pstrb & 0x1) != 0 else 0) | (0x0000FF00 if (pstrb & 0x2) != 0 else 0) | (0x00FF0000 if (pstrb & 0x4) != 0 else 0) | (0xFF000000 if (pstrb & 0x8) != 0 else 0))",
            "width": 32,
        }
    ]
    doc["rtl_contract"] = {
        "transaction": "FM_APB_WRITE",
        "clock": "pclk",
        "reset": "presetn",
        "sample_condition": "1",
        "input_map": {"pstrb": "pstrb", "psel": "psel", "penable": "penable", "pwrite": "pwrite"},
        "output_map": {"pready": "pready", "pslverr": "pslverr", "prdata": "prdata"},
        "output_rules": list(tx["output_rules"]),
    }
    _write_ssot_doc(tmp_path, ip, doc)
    ssot_path = tmp_path / ip / "yaml" / f"{ip}.ssot.yaml"
    text = ssot_path.read_text(encoding="utf-8")
    text = text.replace(
        "expr: ((0x000000FF if (pstrb & 0x1) != 0 else 0) | (0x0000FF00 if (pstrb & 0x2) != 0 else 0) | (0x00FF0000 if (pstrb & 0x4) != 0 else 0) | (0xFF000000 if (pstrb & 0x8) != 0 else 0))",
        "expr: ((0x000000FF if (pstrb & 0x1) != 0 else 0) | (0x0000FF00 if (pstrb & 0x2) != 0 else 0) | (0x00FF0000 if (pstrb & 0x4) != 0 else 0)\n        | (0xFF000000 if (pstrb & 0x8) != 0 else 0))",
    )
    ssot_path.write_text(text, encoding="utf-8")

    repaired = _run_repair_ssot(tmp_path, ip)

    assert repaired.returncode == 0, repaired.stdout + repaired.stderr
    loaded = yaml.safe_load(ssot_path.read_text(encoding="utf-8"))
    expr = loaded["function_model"]["transactions"][0]["state_updates"][0]["expr"]
    assert "0xFF000000" in expr


def test_repair_ssot_schema_adds_register_write_effects(tmp_path: Path):
    ip = "repair_register_write_effect_ip"
    doc = _base_ssot_doc(ip)
    doc["registers"] = {
        "register_list": [
            {
                "name": "CTRL",
                "offset": 0,
                "width": 32,
                "access": "rw",
                "reset": 0,
                "fields": [
                    {"name": "enable", "bits": [0, 0], "access": "rw", "reset": 0, "description": "Enable control"}
                ],
            },
            {
                "name": "STATUS",
                "offset": 4,
                "width": 32,
                "access": "rw",
                "reset": 0,
                "fields": [
                    {
                        "name": "done",
                        "bits": [0, 0],
                        "access": "w1c",
                        "reset": 0,
                        "description": "Done status",
                        "write_side_effect": "clear done status",
                    }
                ],
            },
        ]
    }
    _write_ssot_doc(tmp_path, ip, doc)
    assert _run_check_ssot(tmp_path, ip).returncode != 0

    repaired = _run_repair_ssot(tmp_path, ip)

    assert repaired.returncode == 0, repaired.stdout + repaired.stderr
    result = _run_check_ssot(tmp_path, ip)
    assert result.returncode == 0, result.stdout + result.stderr
    loaded = yaml.safe_load((tmp_path / ip / "yaml" / f"{ip}.ssot.yaml").read_text(encoding="utf-8"))
    fields = {
        field["name"]: field
        for reg in loaded["registers"]["register_list"]
        for field in reg["fields"]
    }
    assert fields["enable"]["write_effect"]
    assert fields["done"]["write_effect"] == "clear done status"


def test_repair_ssot_schema_normalizes_verilog_rule_expressions(tmp_path: Path):
    ip = "repair_verilog_expr_ip"
    doc = _base_ssot_doc(ip)
    tx = doc["function_model"]["transactions"][0]
    doc["io_list"]["interfaces"][0]["ports"].extend(
        [
            {"name": "running", "direction": "output", "width": 1},
            {"name": "count", "direction": "output", "width": 16},
        ]
    )
    tx["output_rules"] = [
        {"name": "result", "port": "result", "expr": "({1'b0, data_in} << 1)", "width": 9},
        {"name": "result_valid", "port": "result_valid", "expr": "1'b1", "width": 1},
        {"name": "running", "port": "running", "expr": "(load_value != 0) ? 1 : 0", "width": 1},
        {"name": "count", "port": "count", "expr": "(count > 0) ? (count - 1) : 0", "width": 16},
    ]
    doc["rtl_contract"]["output_rules"] = [
        {"name": "result", "port": "result", "expr": "({1'b0, data_in} << 1)", "width": 9}
    ]
    _write_ssot_doc(tmp_path, ip, doc)

    repaired = _run_repair_ssot(tmp_path, ip)

    assert repaired.returncode == 0, repaired.stdout + repaired.stderr
    loaded = yaml.safe_load((tmp_path / ip / "yaml" / f"{ip}.ssot.yaml").read_text(encoding="utf-8"))
    rules = loaded["function_model"]["transactions"][0]["output_rules"]
    assert rules[0]["expr"] == "data_in << 1"
    assert rules[1]["expr"] == "1"
    assert rules[2]["expr"] == "(1 if load_value != 0 else 0)"
    assert rules[3]["expr"] == "((count - 1) if count > 0 else 0)"
    assert loaded["rtl_contract"]["output_rules"][0]["expr"] == "data_in << 1"


def test_repair_ssot_schema_assigns_decomposition_refs_to_monolithic_top(tmp_path: Path):
    ip = "repair_top_decomp_owner_ip"
    doc = _base_ssot_doc(ip)
    doc["sub_modules"] = [
        {
            "name": ip,
            "file": f"rtl/{ip}.sv",
            "ownership": "manifest",
            "implements": ["function_model.transactions", "decomposition.units"],
            "source_sections": ["function_model", "cycle_model"],
            "description": "Monolithic top implements the SSOT behavior.",
        }
    ]
    doc["decomposition"] = {
        "units": [
            {"id": "ingress_handshake", "kind": "control"},
            {"id": "shift_datapath", "kind": "datapath"},
        ],
        "source_refs": ["sub_modules", "function_model", "cycle_model", "integration"],
    }
    _write_ssot_doc(tmp_path, ip, doc)

    repaired = _run_repair_ssot(tmp_path, ip)

    assert repaired.returncode == 0, repaired.stdout + repaired.stderr
    loaded = yaml.safe_load((tmp_path / ip / "yaml" / f"{ip}.ssot.yaml").read_text(encoding="utf-8"))
    top_row = next(row for row in loaded["sub_modules"] if row["name"] == ip)
    assert "function_model.transactions.FM_PRIMARY" in top_row["function_model_refs"]
    assert "decomposition" in top_row["decomposition_refs"]


def test_derive_rtl_todos_assigns_memory_owner_from_function_state_update(tmp_path: Path):
    ip = "memory_owner_ip"
    doc = _base_ssot_doc(ip)
    doc["sub_modules"] = [
        {
            "name": f"{ip}_irq",
            "file": f"rtl/{ip}_irq.sv",
            "ownership": "manifest",
            "function_model_refs": ["function_model.transactions.FM_EDGE_SET_IRQ_STATUS"],
            "source_sections": ["function_model", "interrupts"],
        },
        {"name": ip, "file": f"rtl/{ip}.sv", "ownership": "manifest", "description": "top"},
    ]
    doc["memory"] = {
        "instances": [
            {
                "name": "gpio_in_prev_core",
                "type": "register",
                "width": 8,
                "depth": 1,
                "latency": 0,
            }
        ]
    }
    doc["function_model"]["state_variables"] = [
        {
            "name": "gpio_in_prev_core",
            "source": "memory.instances.gpio_in_prev_core",
            "reset": 0,
        }
    ]
    doc["function_model"]["transactions"] = [
        {
            "id": "FM_EDGE_SET_IRQ_STATUS",
            "preconditions": ["core_sample_event == 1"],
            "inputs": ["gpio_in_sync_core", "gpio_in_prev_core"],
            "state_updates": [
                {
                    "name": "gpio_in_prev_core_next",
                    "width": 8,
                    "expr": "gpio_in_sync_core & 0xFF",
                }
            ],
            "output_rules": [],
        }
    ]
    _write_ssot_doc(tmp_path, ip, doc)

    derived = _run_derive_rtl_todos(tmp_path, ip)

    assert derived.returncode in {0, 2}, derived.stdout + derived.stderr
    plan = json.loads((tmp_path / ip / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    by_ref = {task["source_ref"]: task for task in plan["tasks"]}
    memory_task = by_ref["memory.instances.gpio_in_prev_core"]
    assert memory_task["owner_module"] == f"{ip}_irq"
    assert memory_task["owner_file"] == f"rtl/{ip}_irq.sv"
    assert memory_task["owner_match"].startswith("function_model_memory_owner:")


def test_derive_rtl_todos_assigns_sync_memory_owner_from_semantic_refs(tmp_path: Path):
    ip = "memory_owner_ip"
    doc = _base_ssot_doc(ip)
    doc["sub_modules"] = [
        {
            "name": f"{ip}_sync2",
            "file": f"rtl/{ip}_sync2.sv",
            "ownership": "manifest",
            "function_model_refs": ["function_model.transactions.FM_SYNC_SAMPLE"],
            "cycle_model_refs": ["cycle_model.pipeline", "cycle_model.latency.sync_visibility"],
            "dataflow_refs": ["dataflow.input_path"],
            "source_sections": ["function_model", "cycle_model", "dataflow"],
        },
        {"name": ip, "file": f"rtl/{ip}.sv", "ownership": "manifest", "description": "top"},
    ]
    doc["memory"] = {
        "instances": [
            {"name": "sync_stage1_ff", "type": "register", "width": "GPIO_WIDTH", "depth": 1, "latency": 0},
            {"name": "sync_prev_ff", "type": "register", "width": "GPIO_WIDTH", "depth": 1, "latency": 0},
        ]
    }
    _write_ssot_doc(tmp_path, ip, doc)

    derived = _run_derive_rtl_todos(tmp_path, ip)

    assert derived.returncode in {0, 2}, derived.stdout + derived.stderr
    plan = json.loads((tmp_path / ip / "rtl" / "rtl_todo_plan.json").read_text(encoding="utf-8"))
    by_ref = {task["source_ref"]: task for task in plan["tasks"]}
    for name in ("sync_stage1_ff", "sync_prev_ff"):
        memory_task = by_ref[f"memory.instances.{name}"]
        assert memory_task["owner_module"] == f"{ip}_sync2"
        assert memory_task["owner_file"] == f"rtl/{ip}_sync2.sv"
        assert memory_task["owner_match"].startswith("memory_semantic_terms:")


def test_connection_contract_parser_accepts_from_to_module_port_rows():
    derive = _load_derive_rtl_todos()
    modules = [
        {"name": "gpio_apb_regs", "file": "rtl/gpio_apb_regs.sv", "refs": [], "raw": {}},
        {"name": "gpio_top_int", "file": "rtl/gpio_top_int.sv", "refs": [], "raw": {}},
    ]
    doc = {
        "integration": {
            "connections": [
                {
                    "from_module": "gpio_apb_regs",
                    "from_port": "data_out_reg",
                    "to_module": "gpio_top_int",
                    "to_port": "gpio_out_drv",
                    "signal": "data_out_reg",
                }
            ]
        }
    }

    contracts = derive._collect_connection_contracts(doc, modules, "gpio_top")

    assert len(contracts) == 1
    assert contracts[0]["source_ref"] == "integration.connections[0]"
    assert contracts[0]["module"] == "gpio_top_int"
    assert contracts[0]["port"] == "gpio_out_drv"
    assert contracts[0]["signal"] == "data_out_reg"
    assert contracts[0]["signal_terms"] == ["data_out_reg"]
    assert contracts[0]["machine_readable"] is True


def test_connection_contract_audit_accepts_internal_wiring_module_signal(tmp_path: Path):
    derive = _load_derive_rtl_todos()
    ip = "internal_contract_ip"
    ip_dir = tmp_path / ip
    rtl_dir = ip_dir / "rtl"
    rtl_dir.mkdir(parents=True)
    (rtl_dir / f"{ip}.sv").write_text(
        f"""
module {ip}(input logic clk, output logic [15:0] gpio_out);
  {ip}_top_int u_top_int(.clk(clk), .gpio_out(gpio_out));
endmodule
""",
        encoding="utf-8",
    )
    (rtl_dir / f"{ip}_top_int.sv").write_text(
        f"""
module {ip}_top_int(input logic clk, output logic [15:0] gpio_out);
  logic [31:0] data_out_reg;
  logic [15:0] gpio_out_drv;
  {ip}_apb_regs u_regs(.clk(clk), .data_out_reg(data_out_reg));
  assign gpio_out_drv = data_out_reg[15:0];
  assign gpio_out = gpio_out_drv;
endmodule
""",
        encoding="utf-8",
    )
    (rtl_dir / f"{ip}_apb_regs.sv").write_text(
        f"""
module {ip}_apb_regs(input logic clk, output logic [31:0] data_out_reg);
  always @(posedge clk) data_out_reg <= 32'h0;
endmodule
""",
        encoding="utf-8",
    )
    plan = {
        "top": ip,
        "summary": {
            "owner_modules": [
                {"name": f"{ip}_apb_regs", "file": f"rtl/{ip}_apb_regs.sv", "wiring_only": False},
                {"name": f"{ip}_top_int", "file": f"rtl/{ip}_top_int.sv", "wiring_only": True},
                {"name": ip, "file": f"rtl/{ip}.sv", "wiring_only": False},
            ],
            "rtl_quality_profile": "standard",
        },
        "ssot_connection_contracts": [
            {
                "source_ref": "integration.connections[0]",
                "module": f"{ip}_top_int",
                "port": "gpio_out_drv",
                "signal": "data_out_reg",
                "signal_terms": ["data_out_reg"],
                "machine_readable": True,
            }
        ],
    }

    evidence = derive._audit_manifest_hierarchy(ip_dir, plan)

    assert evidence["status"] == "pass"
    assert evidence["port_connection_status"] == "pass"
    assert evidence["connection_contract_status"] == "pass"
    assert evidence["connection_contract_issues"] == []


def test_reserved_register_field_uses_parent_register_evidence_terms():
    derive = _load_derive_rtl_todos()

    terms = derive._evidence_terms(
        "registers.field",
        "registers.register_list.IRQ_EN_RISE.fields.reserved",
        {"name": "reserved", "reset": 0, "access": "rw"},
    )

    assert "reserved" not in terms
    assert {"IRQ_EN_RISE", "IRQ", "EN", "RISE", "GPIO_MASK", "mask"}.issubset(set(terms))


def test_register_field_alias_can_use_parent_register_evidence_terms():
    derive = _load_derive_rtl_todos()

    terms = derive._evidence_terms(
        "registers.field",
        "registers.register_list.DATA_OUT.fields.dout",
        {"name": "dout", "reset": 0, "access": "rw"},
    )

    assert "dout" in terms
    assert {"DATA_OUT", "DATA", "OUT"}.issubset(set(terms))


def test_repair_ssot_schema_collapses_leaf_manifest_to_top_only(tmp_path: Path):
    ip = "repair_leaf_manifest_ip"
    doc = _base_ssot_doc(ip)
    doc["sub_modules"] = [
        {"name": f"{ip}_control", "file": f"rtl/{ip}_control.sv", "ownership": "manifest", "description": "abstract control"},
        {"name": f"{ip}_datapath", "file": f"rtl/{ip}_datapath.sv", "ownership": "manifest", "description": "abstract datapath"},
        {"name": ip, "file": f"rtl/{ip}.sv", "ownership": "manifest", "description": "top"},
    ]
    doc["filelist"] = {"rtl": [f"rtl/{ip}.sv"]}
    doc["decomposition"] = {
        "purpose": "Leaf IP with monolithic RTL implementation.",
        "units": [{"id": "primary", "rtl_candidates": [ip]}],
    }
    doc["integration"] = {}
    _write_ssot_doc(tmp_path, ip, doc)

    repaired = _run_repair_ssot(tmp_path, ip)

    assert repaired.returncode == 0, repaired.stdout + repaired.stderr
    loaded = yaml.safe_load((tmp_path / ip / "yaml" / f"{ip}.ssot.yaml").read_text(encoding="utf-8"))
    assert [row["name"] for row in loaded["sub_modules"]] == [ip]
    assert loaded["filelist"]["rtl"] == [f"rtl/{ip}.sv"]
    assert loaded["sub_modules"][0]["function_model_refs"]


def test_repair_ssot_schema_records_optional_behavior_policy(tmp_path: Path):
    ip = "repair_optional_policy_ip"
    doc = _base_ssot_doc(ip)
    doc.setdefault("workflow_todos", {})["rtl-gen"] = [
        {
            "id": "RTL_OPTIONAL_ASSERTIONS",
            "content": "Optional SVA binders may be added for waveform checks.",
            "required": False,
            "owner_module": ip,
            "owner_file": f"rtl/{ip}.sv",
        }
    ]
    _write_ssot_doc(tmp_path, ip, doc)

    repaired = _run_repair_ssot(tmp_path, ip)

    assert repaired.returncode == 0, repaired.stdout + repaired.stderr
    loaded = yaml.safe_load((tmp_path / ip / "yaml" / f"{ip}.ssot.yaml").read_text(encoding="utf-8"))
    policy = loaded["custom"]["optional_behavior_policy"]
    assert policy["resolution"] == "non_required_optional_items_disabled_unless_ssot_marks_required_or_parameterized"


def test_repair_ssot_schema_marks_ready_high_tieoff_policy(tmp_path: Path):
    ip = "repair_ready_tieoff_ip"
    doc = _base_ssot_doc(ip)
    doc["cycle_model"]["reset"] = {
        "assertion": "ready is driven HIGH during reset.",
        "deassertion": "ready remains HIGH in idle operation.",
    }
    _write_ssot_doc(tmp_path, ip, doc)

    repaired = _run_repair_ssot(tmp_path, ip)

    assert repaired.returncode == 0, repaired.stdout + repaired.stderr
    loaded = yaml.safe_load((tmp_path / ip / "yaml" / f"{ip}.ssot.yaml").read_text(encoding="utf-8"))
    ready_port = next(
        port
        for iface in loaded["io_list"]["interfaces"]
        for port in iface.get("ports", [])
        if port.get("name") == "ready"
    )
    assert ready_port["allow_constant"] is True
    assert ready_port["tieoff"] == "1'b1"


def test_repair_ssot_schema_promotes_transaction_output_rules_to_rtl_contract(tmp_path: Path):
    ip = "repair_contract_output_rules_ip"
    doc = _base_ssot_doc(ip)
    tx0 = doc["function_model"]["transactions"][0]
    tx0["id"] = "FM_ACCEPT"
    tx0["output_rules"] = []
    doc["function_model"]["transactions"].append({
        "id": "FM_EMIT",
        "name": "emit_result",
        "preconditions": ["emit_armed is set"],
        "inputs": ["latched_byte"],
        "outputs": ["result and result_valid update"],
        "side_effects": ["result is externally observable"],
        "output_rules": [
            {"name": "shifted_result", "port": "result", "expr": "(latched_byte << 1) & 511", "width": 9},
            {"name": "result_valid_high", "port": "result_valid", "expr": "1'b1", "width": 1},
        ],
    })
    doc["function_model"]["state_variables"].append({"name": "latched_byte", "reset": 0, "width": 8})
    doc["rtl_contract"]["transaction"] = "FM_ACCEPT"
    doc["rtl_contract"].pop("output_rules", None)
    _write_ssot_doc(tmp_path, ip, doc)

    repaired = _run_repair_ssot(tmp_path, ip)

    assert repaired.returncode == 0, repaired.stdout + repaired.stderr
    loaded = yaml.safe_load((tmp_path / ip / "yaml" / f"{ip}.ssot.yaml").read_text(encoding="utf-8"))
    contract = loaded["rtl_contract"]
    assert {rule["port"] for rule in contract["output_rules"]} >= {"result", "result_valid"}
    assert any(rule["expr"] == "1" for rule in contract["output_rules"])


def test_repair_ssot_schema_adds_observable_state_output_rules(tmp_path: Path):
    ip = "repair_observable_state_ip"
    doc = _base_ssot_doc(ip)
    doc["io_list"]["interfaces"][0]["ports"].append(
        {"name": "accepted_count", "direction": "output", "width": 8}
    )
    doc["rtl_contract"]["output_map"]["accepted_count"] = "accepted_count"
    doc["rtl_contract"]["output_rules"] = [
        {"name": "result", "port": "result", "expr": "data_in << 1", "width": 9}
    ]
    _write_ssot_doc(tmp_path, ip, doc)

    repaired = _run_repair_ssot(tmp_path, ip)

    assert repaired.returncode == 0, repaired.stdout + repaired.stderr
    loaded = yaml.safe_load((tmp_path / ip / "yaml" / f"{ip}.ssot.yaml").read_text(encoding="utf-8"))
    contract_rules = loaded["rtl_contract"]["output_rules"]
    tx_rules = loaded["function_model"]["transactions"][0]["output_rules"]
    assert any(rule["port"] == "accepted_count" and rule["expr"] == "accepted_count" for rule in contract_rules)
    assert any(rule["port"] == "accepted_count" and rule["expr"] == "accepted_count" for rule in tx_rules)


def test_headless_ssot_generation_canonicalizes_llm_ssot_before_pass(tmp_path: Path):
    ip = "headless_canonical_repair_ip"
    req = _write_req(tmp_path, ip)
    doc = _base_ssot_doc(ip)
    doc["sub_modules"] = [
        {
            "name": ip,
            "file": f"rtl/{ip}.sv",
            "ownership": "manifest",
            "implements": ["function_model.transactions", "decomposition.modules"],
            "source_sections": ["function_model", "cycle_model"],
            "description": "Monolithic top implements the SSOT behavior.",
        }
    ]
    doc["decomposition"] = {
        "modules": [{"name": ip, "role": "monolithic behavior owner"}],
        "internal_state": [{"name": "accepted_count"}],
    }
    provider = SequencedArtifactProvider(
        [[{"path": f"{ip}/yaml/{ip}.ssot.yaml", "kind": "ssot", "content": yaml.safe_dump(doc, sort_keys=False)}]]
    )
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="cursor-cli",
        llm_provider=provider,
    )

    result = runner.run(ip=ip, requirement_path=req, stages=["ssot-gen"])

    assert result.status == "pass"
    loaded = yaml.safe_load((tmp_path / "work" / ip / "yaml" / f"{ip}.ssot.yaml").read_text(encoding="utf-8"))
    top_row = next(row for row in loaded["sub_modules"] if row["name"] == ip)
    assert "decomposition" in top_row["decomposition_refs"]
    progress = (tmp_path / "work" / ip / "logs" / "run_progress.jsonl").read_text(encoding="utf-8")
    assert "canonicalize_llm_ssot" in progress


def test_cached_glm51_ssot_response_repairs_missing_cycle_before_downstream(tmp_path: Path):
    ip = "cached_missing_cycle_ip"
    req = _write_req(tmp_path, ip)
    fixture = tmp_path / "fixtures" / "glm_5_1" / "missing_cycle"
    fixture.mkdir(parents=True)
    doc = _structured_ssot_yaml(ip, req.read_text(encoding="utf-8"))
    import yaml

    parsed = yaml.safe_load(doc)
    parsed.pop("cycle_model", None)
    raw = json.dumps(
        {
            "files": [
                {
                    "path": f"{ip}/yaml/{ip}.ssot.yaml",
                    "kind": "ssot",
                    "content": yaml.safe_dump(parsed, sort_keys=False),
                }
            ]
        },
        indent=2,
    )
    (fixture / "raw_response.txt").write_text(raw, encoding="utf-8")
    (fixture / "expected_validator_result.json").write_text('{"status":"human_gate","missing":"cycle_model"}\n', encoding="utf-8")

    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="glm-5.1",
        llm_provider=CachedLLMProvider(fixture),
    )
    result = runner.run(ip=ip, requirement_path=req, stages=["ssot-gen", "fl-model-gen"])

    assert result.status == "pass"
    ssot = yaml.safe_load((tmp_path / "work" / ip / "yaml" / f"{ip}.ssot.yaml").read_text(encoding="utf-8"))
    assert "cycle_model" in ssot
    assert (tmp_path / "work" / ip / "logs" / "validators" / "repair_ssot_schema.log").is_file()


def test_ssot_gen_repairs_invalid_yaml_before_human_gate(tmp_path: Path):
    ip = "ssot_repair_retry_ip"
    req = _write_req(tmp_path, ip)
    bad_yaml = f"top_module:\n  name: {ip}\n    bad_indent: true\n"
    good_yaml = _structured_ssot_yaml(ip, req.read_text(encoding="utf-8"))
    provider = SequencedArtifactProvider(
        [
            [{"path": f"{ip}/yaml/{ip}.ssot.yaml", "kind": "ssot", "content": bad_yaml}],
            [{"path": f"{ip}/yaml/{ip}.ssot.yaml", "kind": "ssot", "content": good_yaml}],
        ]
    )
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="gpt-5.5",
        llm_provider=provider,
    )

    result = runner.run(ip=ip, requirement_path=req, stages=["ssot-gen"])

    assert result.status == "pass", json.dumps(result.to_dict(), indent=2)
    assert len(provider.calls) == 2
    assert provider.calls[1]["stage"] == "ssot-gen"
    assert "Repair the SSOT YAML artifact" in provider.calls[1]["prompt"]
    assert "fixed IP template" in provider.calls[1]["prompt"]
    assert not (tmp_path / "work" / ip / "questions" / "ssot_gen_yaml_parse.json").exists()
    assert (tmp_path / "work" / ip / "logs" / "llm" / "ssot-gen-repair-1.json").is_file()
    ssot = (tmp_path / "work" / ip / "yaml" / f"{ip}.ssot.yaml").read_text(encoding="utf-8")
    assert "function_model:" in ssot
    assert "cycle_model:" in ssot


def test_ssot_gen_canonicalizes_unquoted_expression_after_llm_repair(tmp_path: Path):
    ip = "ssot_repair_expression_quote_ip"
    req = _write_req(tmp_path, ip)
    bad_yaml = f"top_module:\n  name: {ip}\n    bad_indent: true\n"
    repair_yaml = _structured_ssot_yaml(ip, req.read_text(encoding="utf-8")).replace(
        "condition: valid",
        "condition: !enable && !clear && !start",
        1,
    )
    provider = SequencedArtifactProvider(
        [
            [{"path": f"{ip}/yaml/{ip}.ssot.yaml", "kind": "ssot", "content": bad_yaml}],
            [{"path": f"{ip}/yaml/{ip}.ssot.yaml", "kind": "ssot", "content": repair_yaml}],
        ]
    )
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="gpt-5.5",
        llm_provider=provider,
    )

    result = runner.run(ip=ip, requirement_path=req, stages=["ssot-gen"])

    assert result.status == "pass", json.dumps(result.to_dict(), indent=2)
    assert len(provider.calls) == 2
    assert not (tmp_path / "work" / ip / "questions" / "ssot_gen_yaml_parse.json").exists()
    loaded = yaml.safe_load((tmp_path / "work" / ip / "yaml" / f"{ip}.ssot.yaml").read_text(encoding="utf-8"))

    def values(value):
        if isinstance(value, dict):
            for item in value.values():
                yield from values(item)
        elif isinstance(value, list):
            for item in value:
                yield from values(item)
        else:
            yield str(value)

    assert "!enable && !clear && !start" in set(values(loaded))


def test_ssot_gen_uses_deterministic_schema_repair_before_llm_retry(tmp_path: Path):
    ip = "ssot_deterministic_repair_ip"
    req = _write_req(tmp_path, ip)
    doc = _base_ssot_doc(ip)
    doc["function_model"]["transactions"].append(
        {
            "id": "FM_STATUS_POLL",
            "name": "status_poll",
            "preconditions": ["status read is accepted under cycle_model rules"],
            "outputs": ["current status is observable without changing architectural state"],
            "side_effects": ["status read preserves accepted_count"],
            "state_updates": [{"name": "accepted_count", "expr": "accepted_count", "width": 8}],
        }
    )
    doc["cycle_model"].pop("performance", None)
    doc["rtl_contract"].pop("transaction", None)
    doc["test_requirements"]["coverage_goals"]["function"]["bins"].append(
        {"id": "FCOV_BAD_FEATURE_REF", "source_ref": "features.double_value", "class": "feature", "description": "bad ref"}
    )
    doc["test_requirements"]["coverage_goals"]["cycle"]["bins"].append(
        {"id": "CCOV_BAD_TIMING_REF", "source_ref": "timing.latency_budget", "class": "timing", "description": "bad ref"}
    )
    bad_yaml = yaml.safe_dump(doc, sort_keys=False)
    _write_ssot_doc(tmp_path, ip, doc)
    assert _run_check_ssot(tmp_path, ip).returncode != 0
    provider = SequencedArtifactProvider(
        [[{"path": f"{ip}/yaml/{ip}.ssot.yaml", "kind": "ssot", "content": bad_yaml}]]
    )
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="gpt-5.5",
        llm_provider=provider,
    )

    result = runner.run(ip=ip, requirement_path=req, stages=["ssot-gen"])

    assert result.status == "pass", json.dumps(result.to_dict(), indent=2)
    assert len(provider.calls) == 1
    assert (tmp_path / "work" / ip / "logs" / "validators" / "repair_ssot_schema.log").is_file()
    assert not (tmp_path / "work" / ip / "logs" / "llm" / "ssot-gen-repair-1.json").exists()
    repaired = yaml.safe_load((tmp_path / "work" / ip / "yaml" / f"{ip}.ssot.yaml").read_text(encoding="utf-8"))
    tx = next(item for item in repaired["function_model"]["transactions"] if item["id"] == "FM_STATUS_POLL")
    assert tx["side_effects"]
    assert repaired["cycle_model"]["performance"]
    assert repaired["rtl_contract"]["transaction"]
    function_refs = [item["source_ref"] for item in repaired["test_requirements"]["coverage_goals"]["function"]["bins"]]
    cycle_refs = [item["source_ref"] for item in repaired["test_requirements"]["coverage_goals"]["cycle"]["bins"]]
    assert all("function_model" in ref for ref in function_refs)
    assert all("cycle_model" in ref or ref.startswith("fsm.") for ref in cycle_refs)


def test_headless_rtl_prompt_is_focused_to_rtl_artifact_and_todos(tmp_path: Path, monkeypatch):
    ip = "rtl_prompt_focus_ip"
    req = _write_req(tmp_path, ip)
    monkeypatch.setenv("ATLAS_HEADLESS_RTL_PACKET_MODE", "0")
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="glm-5.1",
        llm_provider=FakeLLMProvider(),
    )
    result = runner.run(ip=ip, requirement_path=req, stages=["ssot-gen", "fl-model-gen", "equiv-goals", "rtl-gen"])

    assert result.status == "pass", json.dumps(result.to_dict(), indent=2)
    prompt = (tmp_path / "work" / ip / "logs" / "llm" / "rtl-gen_prompt.md").read_text(encoding="utf-8")
    assert f"{ip}/yaml/{ip}.ssot.yaml" in prompt
    assert f"{ip}/rtl/rtl_todo_plan.json" in prompt
    assert f"{ip}/rtl/rtl_authoring_plan.json" in prompt
    assert f"{ip}/rtl/authoring_packets" in prompt
    assert "Process one authoring packet at a time" in prompt
    assert "execution_policy" in prompt
    assert "deferred_human_qa_allowed" in prompt
    assert "pass_allowed is false" in prompt
    assert "Repair only RTL-owned artifacts" in prompt
    assert "Do not change SSOT semantics" in prompt
    assert "rtl_implementation_depth_evidence" in prompt
    assert "rtl_reference_profile" in prompt
    assert "calibration-only scale evidence" in prompt
    assert "fixed IP templates" in prompt
    provenance = json.loads((tmp_path / "work" / ip / "rtl" / "rtl_authoring_provenance.json").read_text(encoding="utf-8"))
    assert provenance["agent"] == "common_ai_agent"
    assert provenance["workflow"] == "rtl-gen"
    assert provenance["todo_plan_sha256"]


def test_headless_rtl_prompt_declares_json_no_tool_contract(tmp_path: Path):
    ip = "rtl_prompt_contract_ip"
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="gpt-5.3-codex",
        llm_provider=FakeLLMProvider(),
    )

    system, prompt = runner._stage_prompt("rtl-gen", ip, {"ip": ip, "root": str(tmp_path / "work")})

    assert "HEADLESS PROVIDER CONTRACT" in system
    assert "Do not emit Action:" in system
    assert "Return only the machine-readable JSON object" in system
    assert "Return exactly one JSON object" in prompt
    assert '"files"' in prompt


def test_headless_rtl_gen_can_drive_authoring_packets(tmp_path: Path, monkeypatch):
    ip = "rtl_packet_mode_ip"
    req = _write_req(tmp_path, ip)
    stale_provenance_dir = tmp_path / "work" / ip / "rtl"
    stale_provenance_dir.mkdir(parents=True, exist_ok=True)
    (stale_provenance_dir / "rtl_authoring_provenance.json").write_text(
        json.dumps(
            {
                "ip": "old_ip",
                "model": "old-model",
                "authoring_packets": ["module__timer_core__function_model"],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("ATLAS_HEADLESS_RTL_PACKET_MODE", "1")
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="glm-5.1",
        llm_provider=FakeLLMProvider(),
    )

    result = runner.run(ip=ip, requirement_path=req, stages=["ssot-gen", "fl-model-gen", "equiv-goals", "rtl-gen"])

    assert result.status == "pass", json.dumps(result.to_dict(), indent=2)
    packet_prompts = sorted((tmp_path / "work" / ip / "logs" / "llm").glob("rtl-gen-packet-*_prompt.md"))
    assert packet_prompts
    first_prompt = packet_prompts[0].read_text(encoding="utf-8")
    assert "RTL-GEN PACKET MODE" in first_prompt
    assert "Current packet JSON" in first_prompt
    assert "implementation depth" in first_prompt
    assert "Current owner RTL file" in first_prompt
    assert "preserve prior slice logic" in first_prompt
    assert "Packet execution rules" in first_prompt
    assert "active packets" in first_prompt
    assert "closed packets skipped" in first_prompt
    assert "dummy" not in first_prompt.lower()
    authoring_plan_text = (tmp_path / "work" / ip / "rtl" / "rtl_authoring_plan.json").read_text(encoding="utf-8")
    assert "dummy" not in authoring_plan_text.lower()
    packet_paths = sorted((tmp_path / "work" / ip / "rtl" / "authoring_packets").glob("module__rtl_packet_mode_ip_core*.json"))
    assert packet_paths
    packet_json = json.loads(packet_paths[0].read_text(encoding="utf-8"))
    assert "dummy" not in json.dumps(packet_json).lower()
    assert any("ssot_context" in task for task in packet_json["tasks"])
    provenance = json.loads((tmp_path / "work" / ip / "rtl" / "rtl_authoring_provenance.json").read_text(encoding="utf-8"))
    assert provenance["surface"] == "headless_common_engine"
    assert provenance["ip"] == ip
    assert provenance["model"] == "glm-5.1"
    assert provenance["authoring_packets"]
    assert "module__timer_core__function_model" not in provenance["authoring_packets"]
    assert f"rtl/{ip}.sv" in provenance["rtl_files"]


def test_headless_rtl_gen_retries_failed_rtl_authoring(tmp_path: Path, monkeypatch):
    class RetryRtlProvider(FakeLLMProvider):
        def __init__(self) -> None:
            super().__init__()
            self.rtl_calls = 0

        def complete(self, **kwargs):
            if kwargs["stage"] == "rtl-gen":
                self.rtl_calls += 1
                if self.rtl_calls == 1:
                    self.calls.append({"stage": kwargs["stage"], "model": kwargs["model"], "prompt_hash": "empty-rtl"})
                    return LLMResponse(
                        stage=kwargs["stage"],
                        model=kwargs["model"],
                        raw_response=json.dumps({"files": []}, indent=2),
                        parsed_artifacts=[],
                    )
            return super().complete(**kwargs)

    ip = "rtl_retry_ip"
    req = _write_req(tmp_path, ip)
    monkeypatch.setenv("ATLAS_HEADLESS_RTL_PACKET_MODE", "0")
    monkeypatch.setenv("ATLAS_HEADLESS_RTL_REPAIR_ATTEMPTS", "1")
    provider = RetryRtlProvider()
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="glm-5.1",
        llm_provider=provider,
    )

    result = runner.run(ip=ip, requirement_path=req, stages=["ssot-gen", "fl-model-gen", "equiv-goals", "rtl-gen"])

    assert result.status == "pass", json.dumps(result.to_dict(), indent=2)
    assert provider.rtl_calls == 2
    assert (tmp_path / "work" / ip / "logs" / "llm" / "rtl-gen-repair-1.json").is_file()
    repair_prompt = (tmp_path / "work" / ip / "logs" / "llm" / "rtl-gen-repair-1_prompt.md").read_text(encoding="utf-8")
    assert "Current reason" in repair_prompt
    assert "open_required_count" in repair_prompt


def test_headless_rtl_gen_accepts_llm_human_gate_for_locked_truth(tmp_path: Path, monkeypatch):
    class RtlHumanGateProvider(FakeLLMProvider):
        def complete(self, **kwargs):
            if kwargs["stage"] == "rtl-gen":
                raw = json.dumps(
                    {
                        "human_gate": {
                            "decision_needed": "Define machine-readable SSOT connection contracts before RTL authoring.",
                            "evidence": {
                                "ssot_refs": ["integration.connections"],
                                "tool_logs": [f"{kwargs['context']['ip']}/rtl/rtl_authoring_plan.json"],
                            },
                            "options": [
                                {"label": "Add integration.connections", "effect": "rtl-gen can wire child modules by contract"},
                            ],
                            "recommended_default": {
                                "label": "Add module/port/signal contracts",
                                "why": "production multi-module RTL needs explicit wiring truth",
                            },
                            "downstream_effect": ["rtl_authoring_plan", "rtl child port maps"],
                        }
                    },
                    indent=2,
                )
                return LLMResponse(
                    stage=kwargs["stage"],
                    model=kwargs["model"],
                    raw_response=raw,
                    error="model requested human_gate",
                    status="human_gate",
                )
            return super().complete(**kwargs)

    ip = "rtl_human_gate_ip"
    req = _write_req(tmp_path, ip)
    monkeypatch.setenv("ATLAS_HEADLESS_RTL_PACKET_MODE", "0")
    monkeypatch.setenv("ATLAS_HEADLESS_RTL_REPAIR_ATTEMPTS", "1")
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="glm-5.1",
        llm_provider=RtlHumanGateProvider(),
    )

    result = runner.run(ip=ip, requirement_path=req, stages=["ssot-gen", "fl-model-gen", "equiv-goals", "rtl-gen"])

    assert result.status == "blocked", json.dumps(result.to_dict(), indent=2)
    assert result.stages[-1].stage == "rtl-gen"
    assert result.stages[-1].status == "human_gate"
    blocker = tmp_path / "work" / ip / "questions" / "rtl_gen_llm.json"
    assert blocker.is_file()
    question = json.loads(blocker.read_text(encoding="utf-8"))
    assert "connection contracts" in question["decision_needed"]
    prompt = (tmp_path / "work" / ip / "logs" / "llm" / "rtl-gen_prompt.md").read_text(encoding="utf-8")
    assert "return a human_gate JSON object" in prompt
