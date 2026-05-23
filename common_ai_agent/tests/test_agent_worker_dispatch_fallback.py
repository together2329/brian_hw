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
        "ATLAS_LAZY_WORKERS",
        "ATLAS_PROJECT_ROOT",
        "ATLAS_WORKER_LAZY_START",
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


def test_dispatch_workflow_lazy_starts_via_registered_callback(monkeypatch, tmp_path):
    _clear_worker_env(monkeypatch)
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setattr(tools, "_dispatch_workflow_callback", None)
    lazy_calls = []
    worker_calls = []

    def fake_lazy(worker_url, workflow, project_root):
        lazy_calls.append((worker_url, workflow, project_root))

    def fake_worker_call(**kwargs):
        worker_calls.append(kwargs)
        return {
            "status": "completed",
            "result": "ssot updated",
            "files_modified": [],
            "files_examined": [],
            "iterations": 1,
            "execution_time_ms": 10,
            "error": "",
        }

    monkeypatch.setattr(tools, "_ensure_lazy_worker_callback", fake_lazy)
    monkeypatch.setattr(agent_client, "worker_call", fake_worker_call)

    output = tools.dispatch_workflow(
        workflow="ssot-gen",
        ip="new_axi",
        prompt="Quality pass for new_axi SSOT.",
    )
    data = json.loads(output)

    assert data["ok"] is True
    assert lazy_calls == [
        ("http://127.0.0.1:5621", "ssot-gen", str(tmp_path))
    ]
    assert worker_calls[0]["worker"] == "ssot-gen"


def test_dispatch_workflow_lazy_starts_via_atlas_jobs_when_callback_missing(
    monkeypatch, tmp_path
):
    _clear_worker_env(monkeypatch)
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setattr(tools, "_dispatch_workflow_callback", None)
    monkeypatch.setattr(tools, "_ensure_lazy_worker_callback", None)
    import src.atlas_api_jobs as atlas_jobs

    lazy_calls = []

    def fake_lazy(worker_url, workflow, project_root):
        lazy_calls.append((worker_url, workflow, project_root))

    monkeypatch.setattr(
        atlas_jobs,
        "_ensure_lazy_worker_for_direct_dispatch",
        fake_lazy,
    )
    monkeypatch.setattr(
        agent_client,
        "worker_call",
        lambda **_kwargs: {
            "status": "completed",
            "result": "ssot updated",
            "files_modified": [],
            "files_examined": [],
            "iterations": 1,
            "execution_time_ms": 10,
            "error": "",
        },
    )

    output = tools.dispatch_workflow(
        workflow="ssot-gen",
        ip="new_axi",
        prompt="Quality pass for new_axi SSOT.",
    )
    data = json.loads(output)

    assert data["ok"] is True
    assert lazy_calls == [
        ("http://127.0.0.1:5621", "ssot-gen", str(tmp_path))
    ]


def test_dispatch_workflow_reports_lazy_spawn_failure(monkeypatch, tmp_path):
    _clear_worker_env(monkeypatch)
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setattr(tools, "_dispatch_workflow_callback", None)

    def fail_lazy(*_args):
        raise RuntimeError("spawn exploded")

    def fail_worker_call(**_kwargs):
        raise AssertionError("worker_call should not run after lazy failure")

    monkeypatch.setattr(tools, "_ensure_lazy_worker_callback", fail_lazy)
    monkeypatch.setattr(agent_client, "worker_call", fail_worker_call)

    output = tools.dispatch_workflow(
        workflow="ssot-gen",
        ip="new_axi",
        prompt="Quality pass for new_axi SSOT.",
    )
    data = json.loads(output)

    assert data["ok"] is False
    assert data["source"] == "direct_worker_lazy_spawn_failed"
    assert data["worker"] == "http://127.0.0.1:5621"
    assert "spawn exploded" in data["result"]["error"]


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
