import json

import core.agent_client as agent_client
import core.tools as tools
from src.orchestrator import tools as orch_tools


_WORKFLOWS = (
    "ssot-gen",
    "fl-model-gen",
    "rtl-gen",
    "lint",
    "tb-gen",
    "sim",
    "coverage",
    "sim_debug",
    "syn",
    "sta",
    "pnr",
    "sta-post",
)


def _clear_worker_env(monkeypatch):
    for workflow in _WORKFLOWS:
        suffix = workflow.upper().replace("-", "_")
        for key in (
            f"ATLAS_WORKER_URL_{suffix}",
            f"ATLAS_{suffix}_WORKER_URL",
            f"WORKER_URL_{suffix}",
        ):
            monkeypatch.delenv(key, raising=False)
    for key in (
        "ATLAS_ORCHESTRATOR_MODE",
        "ATLAS_SINGLE_MAIN_LOOP",
        "ATLAS_EXEC_MODE",
        "ATLAS_DEFAULT_EXEC_MODE",
        "WORKER_URL_DEFAULT",
    ):
        monkeypatch.delenv(key, raising=False)
    agent_client.set_coordinator("")


def test_worker_call_resolves_ssot_gen_alias_to_orchestrator_port(monkeypatch):
    _clear_worker_env(monkeypatch)

    assert agent_client._resolve_worker("ssot-gen") == "http://127.0.0.1:5621"


def test_worker_call_resolves_alias_to_single_worker_port(monkeypatch):
    _clear_worker_env(monkeypatch)
    monkeypatch.setenv("ATLAS_EXEC_MODE", "single-worker")

    assert agent_client._resolve_worker("ssot-gen") == "http://127.0.0.1:5601"


def test_worker_call_respects_per_workflow_url_override(monkeypatch):
    _clear_worker_env(monkeypatch)
    monkeypatch.setenv("WORKER_URL_RTL_GEN", "http://127.0.0.1:5999/")

    assert agent_client._resolve_worker("rtl-gen") == "http://127.0.0.1:5999"


def test_worker_call_leaves_unknown_alias_unchanged(monkeypatch):
    _clear_worker_env(monkeypatch)

    assert agent_client._resolve_worker("custom-worker") == "custom-worker"


def test_dispatch_workflow_uses_direct_worker_when_ui_bridge_missing(monkeypatch):
    _clear_worker_env(monkeypatch)
    monkeypatch.setattr(tools, "_dispatch_workflow_callback", None)
    calls = []

    def fake_worker_call(**kwargs):
        calls.append(kwargs)
        return {
            "status": "completed",
            "result": "ssot updated",
            "files_modified": ["new_axi/yaml/new_axi.ssot.yaml"],
            "files_examined": [],
            "iterations": 1,
            "execution_time_ms": 10,
            "error": "",
        }

    monkeypatch.setattr(agent_client, "worker_call", fake_worker_call)

    output = tools.dispatch_workflow(
        workflow="ssot-gen",
        ip="new_axi",
        prompt="Quality pass for new_axi SSOT.",
        model="glm-5.1",
    )
    data = json.loads(output)

    assert data["ok"] is True
    assert data["source"] == "direct_worker_fallback"
    assert data["workflow"] == "ssot-gen"
    assert calls[0]["worker"] == "ssot-gen"
    assert calls[0]["workflow"] == "ssot-gen"
    assert calls[0]["model"] == "glm-5.1"
    assert "IP: new_axi" in calls[0]["task"]
    assert "Quality pass for new_axi SSOT." in calls[0]["task"]


def test_dispatch_workflow_keeps_manual_handoff_for_multi_stage_without_bridge(monkeypatch):
    _clear_worker_env(monkeypatch)
    monkeypatch.setattr(tools, "_dispatch_workflow_callback", None)

    output = tools.dispatch_workflow(
        stages=["ssot-gen", "rtl-gen"],
        ip="new_axi",
        prompt="Run the pipeline.",
    )

    assert "manual handoff" in output
    assert "direct fallback supports one concrete workflow only" in output


def test_orchestrator_tool_uses_direct_worker_when_bridge_missing(monkeypatch):
    _clear_worker_env(monkeypatch)
    monkeypatch.setattr(orch_tools, "_dispatch_workflow_bridge", lambda: None)
    calls = []

    def fake_worker_call(**kwargs):
        calls.append(kwargs)
        return {
            "status": "completed",
            "result": "ssot updated",
            "files_modified": ["new_axi/yaml/new_axi.ssot.yaml"],
            "files_examined": [],
            "iterations": 1,
            "execution_time_ms": 10,
            "error": "",
        }

    monkeypatch.setattr(agent_client, "worker_call", fake_worker_call)

    result, summary = orch_tools.dispatch_workflow(
        workflow="ssot-gen",
        ip="new_axi",
        prompt="Quality pass for new_axi SSOT.",
        orchestrator_run_id="orch-1",
        reason="quality pass",
    )

    assert result["ok"] is True
    assert result["source"] == "direct_worker_fallback"
    assert calls[0]["worker"] == "ssot-gen"
    assert "IP: new_axi" in calls[0]["task"]
    assert "Quality pass for new_axi SSOT." in calls[0]["task"]
    assert "direct_worker_fallback" in summary
