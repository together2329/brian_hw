import importlib
import os
import sys
import threading
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _reload_config(monkeypatch):
    for key in list(os.environ):
        if key.startswith(("LLM_", "PROFILE_", "MODEL_NAME", "CURSOR_AGENT_", "CLAUDE_CLI_")):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("USE_OPENCODE_OAUTH", "false")
    import config
    return importlib.reload(config)


def test_dispatch_runs_workers_in_parallel_and_writes_results(monkeypatch, tmp_path):
    from core import delegate_runner
    from core.parallel_todo_dispatcher import ParallelTodoDispatcher

    barrier = threading.Barrier(3)
    seen = []
    lock = threading.Lock()

    def fake_run(self, backend, task, context="", workflow_name="", model_override=None):
        with lock:
            seen.append(model_override)
        barrier.wait(timeout=5)
        return f"done:{model_override}"

    monkeypatch.setattr(delegate_runner.DelegateRunner, "run", fake_run)

    dispatcher = ParallelTodoDispatcher(project_root=tmp_path)
    job_id = dispatcher.dispatch(
        ["RTL-0001", "RTL-0002", "RTL-0003"],
        max_workers=3,
        models=["fake-1", "fake-2", "fake-3"],
    )
    result = dispatcher.wait(job_id, timeout_s=5)

    assert result["status"] == "completed"
    assert result["worker_count"] == 3
    assert sorted(seen) == ["fake-1", "fake-2", "fake-3"]
    for idx in range(3):
        assert (tmp_path / ".workers" / job_id / str(idx) / "result.json").is_file()


def test_profile_runtime_is_thread_local_and_main_profile_is_restored(monkeypatch, tmp_path):
    cfg = _reload_config(monkeypatch)
    monkeypatch.setenv("LLM_MODEL_NAME", "main-model")
    monkeypatch.setenv("MODEL_NAME", "main-model")
    monkeypatch.setenv("PROFILE_alpha_MODEL", "alpha-model")
    monkeypatch.setenv("PROFILE_alpha_BASE_URL", "https://alpha.example/v1")
    monkeypatch.setenv("PROFILE_alpha_API_KEY", "alpha-key")
    monkeypatch.setenv("PROFILE_beta_MODEL", "beta-model")
    monkeypatch.setenv("PROFILE_beta_BASE_URL", "https://beta.example/v1")
    monkeypatch.setenv("PROFILE_beta_API_KEY", "beta-key")
    cfg = importlib.reload(cfg)

    from core import delegate_runner
    from core.parallel_todo_dispatcher import ParallelTodoDispatcher

    barrier = threading.Barrier(2)
    seen = {}
    env_seen = {}
    lock = threading.Lock()
    before_model = cfg.MODEL_NAME
    before_env_model = os.environ.get("MODEL_NAME")

    def fake_run(self, backend, task, context="", workflow_name="", model_override=None):
        import config
        with lock:
            seen[model_override] = config.MODEL_NAME
            env_seen[model_override] = os.environ.get("MODEL_NAME")
        barrier.wait(timeout=5)
        return "ok"

    monkeypatch.setattr(delegate_runner.DelegateRunner, "run", fake_run)

    dispatcher = ParallelTodoDispatcher(project_root=tmp_path)
    job_id = dispatcher.dispatch(["a", "b"], max_workers=2, models=["alpha", "beta"])
    result = dispatcher.wait(job_id, timeout_s=5)

    assert result["status"] == "completed"
    assert seen == {"alpha-model": "alpha-model", "beta-model": "beta-model"}
    assert env_seen == {"alpha-model": before_env_model, "beta-model": before_env_model}
    assert cfg.MODEL_NAME == before_model
    assert os.environ.get("MODEL_NAME") == before_env_model


def test_auto_pick_reports_partial_workers_when_pool_is_smaller(monkeypatch, tmp_path):
    from core import delegate_runner
    from core.parallel_todo_dispatcher import ParallelTodoDispatcher, WorkerModel

    def fake_available_models(self):
        return [
            WorkerModel("claude-cli", "claude-cli", "claude-cli"),
            WorkerModel("glm", "glm-5.1", "glm-5.1"),
        ]

    def fake_run(self, backend, task, context="", workflow_name="", model_override=None):
        return f"done:{model_override}"

    monkeypatch.setattr(ParallelTodoDispatcher, "_available_models", fake_available_models)
    monkeypatch.setattr(delegate_runner.DelegateRunner, "run", fake_run)

    dispatcher = ParallelTodoDispatcher(project_root=tmp_path)
    job_id = dispatcher.dispatch(["one", "two", "three"], max_workers=3, models=None)
    result = dispatcher.wait(job_id, timeout_s=5)

    assert result["status"] == "partial"
    assert result["requested_worker_count"] == 3
    assert result["worker_count"] == 2
    assert result["todos_assigned"] == 3
    assert len(result["todos_done"]) == 3


def test_parallel_todo_dispatch_tool_is_registered():
    from core.tools import AVAILABLE_TOOLS

    assert "parallel_todo_dispatch" in AVAILABLE_TOOLS
