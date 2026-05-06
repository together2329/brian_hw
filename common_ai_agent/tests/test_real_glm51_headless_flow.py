from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from src.headless_workflow import HeadlessWorkflowRunner, RealLLMProvider


def _write_real_req(tmp_path: Path, ip: str) -> Path:
    req = tmp_path / f"{ip}_requirements.md"
    text = (
        f"{ip} is a small ready/valid stream transform IP used to validate the "
        "headless GLM-5.1 workflow. After reset deassertion, it samples data_in "
        "only when valid is asserted. The ready output remains high after reset. "
        "One cycle after a sampled transaction, result_valid pulses and result "
        "equals twice the sampled data_in value. The accepted_count architectural "
        "state increments once per sampled transaction and resets to zero. Invalid "
        "transactions are not part of this minimal signoff subset. The generated "
        "FunctionalModel must be the expected-behavior source for the cocotb/pyuvm "
        "scoreboard. DUT-only compile, DUT-only lint, structured scoreboard events, "
        "FL-vs-RTL comparison, functional coverage linked to equivalence goals, and "
        "goal audit evidence are required before signoff can pass. "
    )
    req.write_text("# GLM-5.1 Headless Requirement\n\n" + text * 5 + "\n", encoding="utf-8")
    return req


@pytest.mark.skipif(
    os.getenv("ATLAS_RUN_REAL_LLM_TDD") != "1",
    reason="real GLM-5.1 headless workflow test disabled",
)
def test_real_glm51_headless_flow_from_req_to_goal_audit(tmp_path: Path):
    model = os.getenv("ATLAS_HEADLESS_LLM_MODEL", "glm-5.1")
    ip = "real_glm51_stream_transform"
    req = _write_real_req(tmp_path, ip)
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model=model,
        llm_provider=RealLLMProvider(required_model="glm-5.1"),
        require_glm51=True,
    )

    result = runner.run(
        ip=ip,
        requirement_path=req,
        stages=[
            "ssot-gen",
            "fl-model-gen",
            "equiv-goals",
            "rtl-gen",
            "lint",
            "tb-gen",
            "sim",
            "sim-debug",
            "goal-audit",
        ],
    )

    log_path = tmp_path / "work" / ip / "logs" / "llm" / "ssot-gen.json"
    assert log_path.is_file()
    log = json.loads(log_path.read_text(encoding="utf-8"))
    assert log["model"] == model
    if result.status == "blocked":
        assert log["error"] or (tmp_path / "work" / ip / "questions").is_dir()
        return

    assert result.status == "pass", json.dumps(result.to_dict(), indent=2)
    audit = json.loads((tmp_path / "work" / ip / "sim" / "fl_rtl_goal_audit.json").read_text(encoding="utf-8"))
    assert audit["status"] == "pass"
