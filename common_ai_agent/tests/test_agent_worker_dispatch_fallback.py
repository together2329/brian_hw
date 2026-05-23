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
        "ATLAS_ACTIVE_SESSION",
        "ATLAS_DEFAULT_SESSION_ID",
        "ATLAS_USER_SESSION_ID",
        "ATLAS_WORKER_LAZY_START",
        "WORKER_URL_DEFAULT",
    ):
        monkeypatch.delenv(key, raising=False)
    agent_client.set_coordinator("")
    try:
        import src.atlas_api_jobs as atlas_jobs
        atlas_jobs._SESSION_WORKER_PORTS.clear()
        atlas_jobs._SESSION_WORKER_KEYS_BY_PORT.clear()
    except Exception:
        pass


def _assert_scoped_worker_url(url: str, legacy_url: str) -> None:
    assert url.startswith("http://127.0.0.1:")
    assert url != legacy_url


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

    def fake_worker_start(**kwargs):
        calls.append(kwargs)
        return {
            "status": "pending",
            "run_id": "run-ssot",
            "worker": "http://127.0.0.1:5621",
        }

    monkeypatch.setattr(agent_client, "worker_start", fake_worker_start)

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
    assert data["run_id"] == "run-ssot"
    assert data["session"] == "default/new_axi/ssot-gen"
    _assert_scoped_worker_url(data["worker_url"], "http://127.0.0.1:5621")
    assert calls[0]["worker"] == data["worker_url"]
    assert calls[0]["workflow"] == "ssot-gen"
    assert calls[0]["model"] == "glm-5.1"
    assert calls[0]["session"] == "default/new_axi/ssot-gen"
    assert calls[0]["ip"] == "new_axi"
    assert "IP: new_axi" in calls[0]["task"]
    assert "Quality pass for new_axi SSOT." in calls[0]["task"]


def test_dispatch_workflow_direct_fallback_scopes_worker_url_by_active_user(monkeypatch):
    _clear_worker_env(monkeypatch)
    monkeypatch.setattr(tools, "_dispatch_workflow_callback", None)
    calls = []

    def fake_worker_start(**kwargs):
        calls.append(kwargs)
        return {
            "status": "pending",
            "run_id": f"run-{len(calls)}",
            "worker": kwargs["worker"],
        }

    monkeypatch.setattr(agent_client, "worker_start", fake_worker_start)

    monkeypatch.setenv("ATLAS_ACTIVE_SESSION", "brian/new_axi/orchestrator")
    first = json.loads(tools.dispatch_workflow(
        workflow="rtl-gen",
        ip="new_axi",
        prompt="Generate RTL.",
    ))
    monkeypatch.setenv("ATLAS_ACTIVE_SESSION", "happygrowth/new_axi/orchestrator")
    second = json.loads(tools.dispatch_workflow(
        workflow="rtl-gen",
        ip="new_axi",
        prompt="Generate RTL.",
    ))

    assert first["session"] == "brian/new_axi/rtl-gen"
    assert second["session"] == "happygrowth/new_axi/rtl-gen"
    _assert_scoped_worker_url(calls[0]["worker"], "http://127.0.0.1:5623")
    _assert_scoped_worker_url(calls[1]["worker"], "http://127.0.0.1:5623")
    assert calls[0]["worker"] != calls[1]["worker"]
    assert first["worker_url"] == calls[0]["worker"]
    assert second["worker_url"] == calls[1]["worker"]


def test_dispatch_workflow_lazy_starts_via_registered_callback(monkeypatch, tmp_path):
    _clear_worker_env(monkeypatch)
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setattr(tools, "_dispatch_workflow_callback", None)
    lazy_calls = []
    worker_starts = []

    def fake_lazy(worker_url, workflow, project_root):
        lazy_calls.append((worker_url, workflow, project_root))

    def fake_worker_start(**kwargs):
        worker_starts.append(kwargs)
        return {
            "status": "pending",
            "run_id": "run-lazy",
            "worker": "http://127.0.0.1:5621",
        }

    monkeypatch.setattr(tools, "_ensure_lazy_worker_callback", fake_lazy)
    monkeypatch.setattr(agent_client, "worker_start", fake_worker_start)

    output = tools.dispatch_workflow(
        workflow="ssot-gen",
        ip="new_axi",
        prompt="Quality pass for new_axi SSOT.",
    )
    data = json.loads(output)

    assert data["ok"] is True
    _assert_scoped_worker_url(data["worker_url"], "http://127.0.0.1:5621")
    assert lazy_calls == [
        (data["worker_url"], "ssot-gen", str(tmp_path))
    ]
    assert worker_starts[0]["worker"] == data["worker_url"]


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
        "worker_start",
        lambda **_kwargs: {
            "status": "pending",
            "run_id": "run-atlas-jobs",
            "worker": "http://127.0.0.1:5621",
        },
    )

    output = tools.dispatch_workflow(
        workflow="ssot-gen",
        ip="new_axi",
        prompt="Quality pass for new_axi SSOT.",
    )
    data = json.loads(output)

    assert data["ok"] is True
    _assert_scoped_worker_url(data["worker_url"], "http://127.0.0.1:5621")
    assert lazy_calls == [
        (data["worker_url"], "ssot-gen", str(tmp_path))
    ]


def test_dispatch_workflow_reports_lazy_spawn_failure(monkeypatch, tmp_path):
    _clear_worker_env(monkeypatch)
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setattr(tools, "_dispatch_workflow_callback", None)

    def fail_lazy(*_args):
        raise RuntimeError("spawn exploded")

    def fail_worker_start(**_kwargs):
        raise AssertionError("worker_start should not run after lazy failure")

    monkeypatch.setattr(tools, "_ensure_lazy_worker_callback", fail_lazy)
    monkeypatch.setattr(agent_client, "worker_start", fail_worker_start)

    output = tools.dispatch_workflow(
        workflow="ssot-gen",
        ip="new_axi",
        prompt="Quality pass for new_axi SSOT.",
    )
    data = json.loads(output)

    assert data["ok"] is False
    assert data["source"] == "direct_worker_lazy_spawn_failed"
    _assert_scoped_worker_url(data["worker"], "http://127.0.0.1:5621")
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


def test_dispatch_workflow_direct_fallback_routes_cl_model_to_fl_worker(monkeypatch):
    _clear_worker_env(monkeypatch)
    monkeypatch.setattr(tools, "_dispatch_workflow_callback", None)
    calls = []

    def fake_worker_start(**kwargs):
        calls.append(kwargs)
        return {
            "status": "pending",
            "run_id": "run-cl",
            "worker": "http://127.0.0.1:5622",
        }

    monkeypatch.setattr(agent_client, "worker_start", fake_worker_start)

    output = tools.dispatch_workflow(
        workflow="cl-model-gen",
        ip="new_axi",
        stages=["cl-model-gen"],
        prompt="Generate the cycle-level model.",
    )
    data = json.loads(output)

    assert data["ok"] is True
    assert data["workflow"] == "fl-model-gen"
    assert data["worker"] == "fl-model-gen"
    assert data["session"] == "default/new_axi/fl-model-gen"
    _assert_scoped_worker_url(data["worker_url"], "http://127.0.0.1:5622")
    assert calls[0]["worker"] == data["worker_url"]
    assert calls[0]["workflow"] == "fl-model-gen"
    assert "/ssot-cycle-model new_axi" in calls[0]["task"]
    assert "/ssot-dual-fcov new_axi" in calls[0]["task"]
    assert "Generate the cycle-level model." in calls[0]["task"]


def test_dispatch_workflow_direct_fallback_routes_equiv_goals_to_fl_worker(monkeypatch):
    _clear_worker_env(monkeypatch)
    monkeypatch.setattr(tools, "_dispatch_workflow_callback", None)
    calls = []

    def fake_worker_start(**kwargs):
        calls.append(kwargs)
        return {
            "status": "pending",
            "run_id": "run-eq",
            "worker": "http://127.0.0.1:5622",
        }

    monkeypatch.setattr(agent_client, "worker_start", fake_worker_start)

    output = tools.dispatch_workflow(
        workflow="equiv-goals",
        ip="new_axi",
        stages=["equiv-goals"],
        prompt="Generate equivalence goals.",
    )
    data = json.loads(output)

    assert data["ok"] is True
    assert data["workflow"] == "fl-model-gen"
    assert data["worker"] == "fl-model-gen"
    _assert_scoped_worker_url(data["worker_url"], "http://127.0.0.1:5622")
    assert calls[0]["worker"] == data["worker_url"]
    assert calls[0]["workflow"] == "fl-model-gen"
    assert "/ssot-equiv-goals new_axi" in calls[0]["task"]
    assert "Generate equivalence goals." in calls[0]["task"]


def test_dispatch_workflow_direct_fallback_routes_model_bundle_to_fl_worker(monkeypatch):
    _clear_worker_env(monkeypatch)
    monkeypatch.setattr(tools, "_dispatch_workflow_callback", None)
    calls = []

    def fake_worker_start(**kwargs):
        calls.append(kwargs)
        return {
            "status": "pending",
            "run_id": "run-model-bundle",
            "worker": "http://127.0.0.1:5622",
        }

    monkeypatch.setattr(agent_client, "worker_start", fake_worker_start)

    output = tools.dispatch_workflow(
        workflow="model-equivalence",
        ip="new_axi",
        stages=["fl-model-gen", "cl-model-gen", "equiv-goals"],
        prompt="Generate FL, CL, and equivalence.",
    )
    data = json.loads(output)

    assert data["ok"] is True
    assert data["workflow"] == "fl-model-gen"
    assert data["worker"] == "fl-model-gen"
    _assert_scoped_worker_url(data["worker_url"], "http://127.0.0.1:5622")
    assert calls[0]["worker"] == data["worker_url"]
    assert "/ssot-fl-model new_axi" in calls[0]["task"]
    assert "/ssot-cycle-model new_axi" in calls[0]["task"]
    assert "/ssot-dual-fcov new_axi" in calls[0]["task"]
    assert "/ssot-equiv-goals new_axi" in calls[0]["task"]


def test_orchestrator_tool_uses_direct_worker_when_bridge_missing(monkeypatch):
    _clear_worker_env(monkeypatch)
    monkeypatch.setattr(orch_tools, "_dispatch_workflow_bridge", lambda: None)
    calls = []

    def fake_worker_start(**kwargs):
        calls.append(kwargs)
        return {
            "status": "pending",
            "run_id": "run-orch-ssot",
            "worker": "http://127.0.0.1:5621",
        }

    monkeypatch.setattr(agent_client, "worker_start", fake_worker_start)

    result, summary = orch_tools.dispatch_workflow(
        workflow="ssot-gen",
        ip="new_axi",
        prompt="Quality pass for new_axi SSOT.",
        orchestrator_run_id="orch-1",
        reason="quality pass",
    )

    assert result["ok"] is True
    assert result["source"] == "direct_worker_fallback"
    _assert_scoped_worker_url(result["worker_url"], "http://127.0.0.1:5621")
    assert calls[0]["worker"] == result["worker_url"]
    assert "IP: new_axi" in calls[0]["task"]
    assert "Quality pass for new_axi SSOT." in calls[0]["task"]
    assert "direct_worker_fallback" in summary
