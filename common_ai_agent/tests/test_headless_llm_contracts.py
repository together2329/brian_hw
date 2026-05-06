from __future__ import annotations

import json
from pathlib import Path

from src.headless_workflow import CachedLLMProvider, FakeLLMProvider, HeadlessWorkflowRunner, LLMResponse, _structured_ssot_yaml


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
    log = json.loads((tmp_path / "work" / ip / "logs" / "llm" / "ssot-gen.json").read_text(encoding="utf-8"))
    assert "files[]" in log["error"]


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


def test_headless_rtl_prompt_is_focused_to_rtl_artifact_and_todos(tmp_path: Path):
    ip = "rtl_prompt_focus_ip"
    req = _write_req(tmp_path, ip)
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
    assert "Repair only RTL-owned artifacts" in prompt
    assert "Do not change SSOT semantics" in prompt
    assert "fixed IP templates" in prompt
    provenance = json.loads((tmp_path / "work" / ip / "rtl" / "rtl_authoring_provenance.json").read_text(encoding="utf-8"))
    assert provenance["agent"] == "common_ai_agent"
    assert provenance["workflow"] == "rtl-gen"
    assert provenance["todo_plan_sha256"]
