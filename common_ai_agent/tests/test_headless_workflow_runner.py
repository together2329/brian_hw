from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import pytest

from src.headless_workflow import FakeLLMProvider, HeadlessWorkflowRunner, RealLLMProvider


FULL_STAGES = [
    "ssot-gen",
    "fl-model-gen",
    "equiv-goals",
    "rtl-gen",
    "lint",
    "tb-gen",
    "sim",
    "coverage",
    "sim-debug",
    "goal-audit",
]


def _write_req(tmp_path: Path, ip: str, *, ambiguous: bool = False) -> Path:
    req = tmp_path / f"{ip}_req.md"
    base = (
        f"{ip} accepts a valid ready-style transaction after reset release. "
        "The input value is sampled only when valid is asserted, and the output "
        "result must equal twice the sampled input value on the next observable "
        "cycle. The ready output remains asserted after reset. The result_valid "
        "signal marks the result cycle. Invalid transactions report a deterministic "
        "error response without changing accepted_count. The functional model is "
        "the expected-behavior oracle for scoreboard rows, while the cycle model "
        "defines the sample and observation timing. DUT-only compile and lint "
        "evidence must pass before simulation evidence is accepted. Functional "
        "coverage must include the accepted datapath case, reset behavior, and "
        "the declared error behavior. FL-vs-RTL comparison must classify every "
        "mismatch to SSOT, FL model, RTL, TB, coverage, tool, or human gate. "
    )
    if ambiguous:
        base = (
            f"{ip} accepts transactions and has some error behavior that is not "
            "defined yet. A human must decide the invalid transaction response "
            "before SSOT signoff can proceed. "
        ) * 8
    req.write_text("# Requirement\n\n" + base * 5 + "\n", encoding="utf-8")
    return req


def _needs_sim_tools() -> None:
    if not shutil.which("iverilog"):
        pytest.skip("iverilog is required for generated cocotb simulation")
    pytest.importorskip("cocotb_test")


def test_fake_llm_headless_flow_reaches_goal_audit_pass(tmp_path: Path):
    _needs_sim_tools()
    ip = "stream_transform_counter"
    req = _write_req(tmp_path, ip)
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="fake-contract-model",
        llm_provider=FakeLLMProvider(),
    )

    result = runner.run(ip=ip, requirement_path=req, stages=FULL_STAGES)

    assert result.status == "pass", json.dumps(result.to_dict(), indent=2)
    ip_dir = tmp_path / "work" / ip
    audit = json.loads((ip_dir / "sim" / "fl_rtl_goal_audit.json").read_text(encoding="utf-8"))
    assert audit["status"] == "pass"
    assert (ip_dir / "logs" / "llm" / "ssot-gen.json").is_file()
    assert (ip_dir / "logs" / "llm" / "rtl-gen.json").is_file()
    assert (ip_dir / "logs" / "llm" / "tb-gen.json").is_file()
    assert json.loads((ip_dir / "logs" / "headless_run.json").read_text(encoding="utf-8"))["status"] == "pass"
    compare = json.loads((ip_dir / "sim" / "fl_rtl_compare.json").read_text(encoding="utf-8"))
    assert compare["status"] == "pass"
    assert compare["summary"]["goals_untested"] == 0
    coverage = json.loads((ip_dir / "cov" / "coverage.json").read_text(encoding="utf-8"))
    assert coverage["source"] == "ssot_coverage_summary"
    assert coverage["status"] == "pass"


def test_fake_llm_headless_flow_blocks_missing_cycle_model(tmp_path: Path):
    ip = "missing_cycle_model_ip"
    req = _write_req(tmp_path, ip)
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="fake-contract-model",
        llm_provider=FakeLLMProvider(scenario="missing_cycle_model"),
    )

    result = runner.run(ip=ip, requirement_path=req, stages=["ssot-gen", "fl-model-gen"])

    assert result.status == "blocked"
    question = tmp_path / "work" / ip / "questions" / "ssot_gen_missing_contract.json"
    assert question.is_file()
    gate = json.loads(question.read_text(encoding="utf-8"))
    assert gate["status"] == "human_gate"
    assert "cycle_model" in gate["decision_needed"]
    assert not (tmp_path / "work" / ip / "model" / "functional_model.py").exists()


def test_headless_human_gate_artifact_created_for_ambiguous_requirement(tmp_path: Path):
    ip = "ambiguous_error_policy_ip"
    req = _write_req(tmp_path, ip, ambiguous=True)
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="fake-contract-model",
        llm_provider=FakeLLMProvider(scenario="human_gate"),
    )

    result = runner.run(ip=ip, requirement_path=req, stages=["ssot-gen"])

    assert result.status == "blocked"
    question = tmp_path / "work" / ip / "questions" / "ssot_gen_llm.json"
    assert question.is_file()
    gate = json.loads(question.read_text(encoding="utf-8"))
    assert "invalid transaction response" in gate["decision_needed"]
    assert gate["options"]


def test_headless_runner_rejects_non_glm51_when_glm51_requested(tmp_path: Path):
    ip = "glm_reject_ip"
    req = _write_req(tmp_path, ip)
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="deepseek-v3",
        llm_provider=RealLLMProvider(required_model="glm-5.1"),
        require_glm51=True,
    )

    result = runner.run(ip=ip, requirement_path=req, stages=["ssot-gen"])

    assert result.status == "blocked"
    log = json.loads((tmp_path / "work" / ip / "logs" / "llm" / "ssot-gen.json").read_text(encoding="utf-8"))
    assert log["model"] == "deepseek-v3"
    assert "requires model glm-5.1" in log["error"]


def test_real_glm51_unavailable_creates_blocker_without_network(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    ip = "real_glm_unavailable_ip"
    req = _write_req(tmp_path, ip)
    monkeypatch.setenv("ATLAS_RUN_REAL_LLM_TDD", "1")
    monkeypatch.delenv("ZAI_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("PROFILE_glm_API_KEY", raising=False)

    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="glm-5.1",
        llm_provider=RealLLMProvider(required_model="glm-5.1"),
        require_glm51=True,
    )

    result = runner.run(ip=ip, requirement_path=req, stages=["ssot-gen"])

    assert result.status == "blocked"
    log = json.loads((tmp_path / "work" / ip / "logs" / "llm" / "ssot-gen.json").read_text(encoding="utf-8"))
    assert log["model"] == "glm-5.1"
    assert "no live API key" in log["error"]
    assert (tmp_path / "work" / ip / "questions" / "ssot_gen_llm.json").is_file()
