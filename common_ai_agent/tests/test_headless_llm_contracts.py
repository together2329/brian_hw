from __future__ import annotations

import json
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


def _run_check_ssot(root: Path, ip: str) -> subprocess.CompletedProcess[str]:
    script = Path(__file__).resolve().parents[1] / "workflow" / "ssot-gen" / "scripts" / "check_ssot_disk.sh"
    return subprocess.run(
        ["bash", str(script), ip],
        cwd=str(root),
        text=True,
        capture_output=True,
        timeout=30,
    )


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


def test_cached_glm51_ssot_response_fails_with_exact_blocker(tmp_path: Path):
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

    assert result.status == "blocked"
    question = tmp_path / "work" / ip / "questions" / "ssot_gen_missing_contract.json"
    assert question.is_file()
    gate = json.loads(question.read_text(encoding="utf-8"))
    assert "cycle_model" in gate["decision_needed"]


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


def test_headless_rtl_gen_can_drive_authoring_packets(tmp_path: Path, monkeypatch):
    ip = "rtl_packet_mode_ip"
    req = _write_req(tmp_path, ip)
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
    packet_paths = sorted((tmp_path / "work" / ip / "rtl" / "authoring_packets").glob("module__rtl_packet_mode_ip_core*.json"))
    assert packet_paths
    packet_json = json.loads(packet_paths[0].read_text(encoding="utf-8"))
    assert any("ssot_context" in task for task in packet_json["tasks"])
    provenance = json.loads((tmp_path / "work" / ip / "rtl" / "rtl_authoring_provenance.json").read_text(encoding="utf-8"))
    assert provenance["surface"] == "headless_common_engine"
    assert provenance["authoring_packets"]
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
