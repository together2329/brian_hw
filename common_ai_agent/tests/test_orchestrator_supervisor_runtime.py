from __future__ import annotations

import json
import importlib
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

AtlasDB = importlib.import_module("core.atlas_db").AtlasDB


class _FakeProcess:
    pid = 4242

    def poll(self) -> None:
        return None


def _runtime(tmp_path: Path):
    from src.orchestrator.supervisor_runtime import OrchestratorSupervisorRuntime

    db = AtlasDB(str(tmp_path / "atlas.db"))
    db.init_db()
    spawned: list[tuple[list[str], dict[str, Any]]] = []
    jobs: dict[str, dict[str, Any]] = {}
    processes: dict[str, Any] = {}

    def process_factory(cmd: list[str], **kwargs: Any):
        spawned.append((cmd, kwargs))
        return _FakeProcess()

    runtime = OrchestratorSupervisorRuntime(
        db,
        project_root=tmp_path,
        source_root=Path(__file__).resolve().parents[1],
        process_factory=process_factory,
        register_job=lambda job_id, job: jobs.__setitem__(job_id, job),
        register_process=lambda run_id, proc: processes.__setitem__(run_id, proc),
        start_watcher=False,
    )
    return runtime, db, spawned, jobs, processes


def test_first_submit_spawns_supervisor_job(tmp_path: Path, monkeypatch) -> None:
    runtime, _db, spawned, jobs, processes = _runtime(tmp_path)
    ip_workflow = tmp_path / "ipA" / "workflow"
    (ip_workflow / "ssot-gen").mkdir(parents=True)

    outcome = runtime.submit_or_attach(
        user_id="user-1",
        ip_id="ip-1",
        ip_name="ipA",
        workspace_id="workspace-1",
        session_id="user/default/ipA/orchestrator",
        chat_message_id="chat-1",
        message_text="build ipA",
        model="gpt-test",
        reasoning_effort="medium",
    )

    control_dir = tmp_path / ".session" / "orchestrators-ipc" / outcome.run_id
    request = json.loads((control_dir / "request.json").read_text(encoding="utf-8"))
    job = jobs[f"orch-{outcome.run_id}"]
    assert outcome.status == "started"
    assert request["kind"] == "orchestrator-supervisor"
    assert request["run_id"] == outcome.run_id
    assert request["initial_user_message"] == "build ipA"
    assert request["wake_path"] == str(control_dir / "wake.jsonl")
    assert (control_dir / "supervisor.log").exists()
    assert spawned[0][0][:3] == [sys.executable, "-m", "src.atlas_orchestrator_supervisor_ipc"]
    assert spawned[0][1]["env"]["ATLAS_WORKFLOW_ROOT"] == str(ip_workflow)
    assert "--request" in spawned[0][0]
    assert job["job_kind"] == "orchestrator-supervisor"
    assert job["workflow"] == "orchestrator"
    assert job["worker_transport"] == "ipc"
    assert job["orchestrator_run_id"] == outcome.run_id
    assert job["worker_log_path"] == f".session/orchestrators-ipc/{outcome.run_id}/supervisor.log"
    assert processes[f"ipc-orch-{outcome.run_id}"].pid == 4242


def test_second_submit_appends_user_reply_and_writes_wake_event(
    tmp_path: Path, monkeypatch
) -> None:
    runtime, db, spawned, _jobs, _processes = _runtime(tmp_path)
    first = runtime.submit_or_attach(
        user_id="user-1",
        ip_id="ip-1",
        ip_name="ipA",
        workspace_id="workspace-1",
        session_id="user/default/ipA/orchestrator",
        chat_message_id="chat-1",
        message_text="build ipA",
    )

    second = runtime.submit_or_attach(
        user_id="user-1",
        ip_id="ip-1",
        ip_name="ipA",
        workspace_id="workspace-1",
        session_id="user/default/ipA/orchestrator",
        chat_message_id="chat-2",
        message_text="also add lint",
    )

    wake_path = tmp_path / ".session" / "orchestrators-ipc" / first.run_id / "wake.jsonl"
    events = [json.loads(line) for line in wake_path.read_text(encoding="utf-8").splitlines()]
    steps = db.list_orchestrator_steps(first.run_id)
    assert second.run_id == first.run_id
    assert second.status == "appended"
    assert len(spawned) == 1
    assert steps[-1]["tool_name"] == "user_reply"
    assert steps[-1]["user_reply"] == "also add lint"
    assert events[-1]["type"] == "user_message"
    assert events[-1]["message"] == "also add lint"
    assert events[-1]["chat_message_id"] == "chat-2"


def test_different_ip_gets_independent_supervisor(
    tmp_path: Path, monkeypatch
) -> None:
    runtime, _db, spawned, jobs, _processes = _runtime(tmp_path)

    first = runtime.submit_or_attach(user_id="user-1", ip_id="ip-1", ip_name="ipA")
    second = runtime.submit_or_attach(user_id="user-1", ip_id="ip-2", ip_name="ipB")

    assert first.run_id != second.run_id
    assert len(spawned) == 2
    assert f"orch-{first.run_id}" in jobs
    assert f"orch-{second.run_id}" in jobs
