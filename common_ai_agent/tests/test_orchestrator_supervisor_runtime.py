from __future__ import annotations

import json
import importlib
import shutil
import sys
import time
from pathlib import Path
from typing import Any

import pytest

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
        if "--request" in cmd:
            request_path = Path(cmd[cmd.index("--request") + 1])
            bridge_dir = request_path.parent / "tool-bridge"
            kwargs["_bridge_ready_at_spawn"] = all(
                (bridge_dir / leaf).exists()
                and ((bridge_dir / leaf).stat().st_mode & 0o777) == 0o700
                for leaf in (".", "requests", "responses")
            )
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
    assert request["tool_bridge_token"]
    assert (control_dir / "supervisor.log").exists()
    assert spawned[0][0][:3] == [sys.executable, "-m", "src.atlas_orchestrator_supervisor_ipc"]
    assert spawned[0][1]["_bridge_ready_at_spawn"] is True
    assert spawned[0][1]["env"]["ATLAS_WORKFLOW_ROOT"] == str(ip_workflow)
    assert "--request" in spawned[0][0]
    assert job["job_kind"] == "orchestrator-supervisor"
    assert job["workflow"] == "orchestrator"
    assert job["worker_transport"] == "ipc"
    assert job["orchestrator_run_id"] == outcome.run_id
    assert job["worker_log_path"] == f".session/orchestrators-ipc/{outcome.run_id}/supervisor.log"
    assert processes[f"ipc-orch-{outcome.run_id}"].pid == 4242


def test_supervisor_rejects_symlinked_session_parent_before_request_write(
    tmp_path: Path,
) -> None:
    runtime, _db, spawned, _jobs, _processes = _runtime(tmp_path)
    outside = tmp_path / "outside-session"
    outside.mkdir()
    (tmp_path / ".session").symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError, match="supervisor IPC path must not be a symlink"):
        runtime.submit_or_attach(user_id="user-1", ip_id="ip-1", ip_name="ipA")

    assert spawned == []
    assert not list(outside.rglob("request.json"))


def test_supervisor_rejects_symlinked_orchestrators_parent_before_request_write(
    tmp_path: Path,
) -> None:
    runtime, _db, spawned, _jobs, _processes = _runtime(tmp_path)
    outside = tmp_path / "outside-orchestrators"
    outside.mkdir()
    session_dir = tmp_path / ".session"
    session_dir.mkdir()
    (session_dir / "orchestrators-ipc").symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError, match="supervisor IPC path must not be a symlink"):
        runtime.submit_or_attach(user_id="user-1", ip_id="ip-1", ip_name="ipA")

    assert spawned == []
    assert not list(outside.rglob("request.json"))


def test_supervisor_paths_create_private_control_directories(tmp_path: Path) -> None:
    from src.orchestrator.supervisor_runtime import _prepare_supervisor_paths

    control = tmp_path / ".session" / "orchestrators-ipc" / "run-1"
    paths = {
        "control": control,
        "request": control / "request.json",
        "response": control / "response.json",
        "wake": control / "wake.jsonl",
        "cancel": control / "cancel.json",
        "log": control / "supervisor.log",
        "bridge": control / "tool-bridge",
    }

    _prepare_supervisor_paths(paths, tmp_path)

    for directory in (tmp_path / ".session", tmp_path / ".session" / "orchestrators-ipc", control):
        assert directory.is_dir()
        assert (directory.stat().st_mode & 0o777) == 0o700


def test_supervisor_paths_reject_symlinked_control_dir(tmp_path: Path) -> None:
    from src.orchestrator.supervisor_runtime import _prepare_supervisor_paths

    control = tmp_path / ".session" / "orchestrators-ipc" / "run-1"
    outside = tmp_path / "outside-control"
    outside.mkdir()
    control.parent.mkdir(parents=True)
    control.symlink_to(outside, target_is_directory=True)
    paths = {
        "control": control,
        "request": control / "request.json",
        "response": control / "response.json",
        "wake": control / "wake.jsonl",
        "cancel": control / "cancel.json",
        "log": control / "supervisor.log",
        "bridge": control / "tool-bridge",
    }

    with pytest.raises(ValueError, match="must not be a symlink"):
        _prepare_supervisor_paths(paths, tmp_path)

    assert not list(outside.rglob("request.json"))


def test_supervisor_control_dir_rejects_dot_segment_run_id(tmp_path: Path) -> None:
    from src.orchestrator.supervisor_wake import supervisor_control_dir

    control = supervisor_control_dir(tmp_path, "..")

    assert control.parent == tmp_path / ".session" / "orchestrators-ipc"
    assert control.name != ".."
    assert control.resolve() != tmp_path / ".session"


def test_append_job_complete_wake_rejects_symlinked_orchestrators_parent(
    tmp_path: Path,
) -> None:
    from src.orchestrator.supervisor_wake import append_job_complete_wake

    outside = tmp_path / "outside-orchestrators"
    outside.mkdir()
    session_dir = tmp_path / ".session"
    session_dir.mkdir()
    (session_dir / "orchestrators-ipc").symlink_to(outside, target_is_directory=True)

    with pytest.raises(ValueError, match="supervisor wake path must not be a symlink"):
        append_job_complete_wake(
            tmp_path,
            run_id="run-1",
            job_id="job-1",
            status="completed",
        )

    assert not list(outside.rglob("wake.jsonl"))


def test_supervisor_tool_bridge_dispatches_in_parent_process(
    tmp_path: Path, monkeypatch
) -> None:
    runtime, _db, _spawned, _jobs, _processes = _runtime(tmp_path)
    ip_workflow = tmp_path / "ipA" / "workflow"
    (ip_workflow / "ssot-gen").mkdir(parents=True)
    core_tools = importlib.import_module("core.tools")
    calls: list[dict[str, Any]] = []

    def fake_dispatch(**kwargs: Any) -> dict[str, Any]:
        calls.append(dict(kwargs))
        return {
            "ok": True,
            "source": "dispatch_workflow_tool",
            "jobs": [{"job_id": "job-ssot", "workflow": kwargs.get("workflow")}],
        }

    monkeypatch.setattr(core_tools, "_dispatch_workflow_callback", fake_dispatch)
    outcome = runtime.submit_or_attach(
        user_id="user-1",
        ip_id="ip-1",
        ip_name="ipA",
        workspace_id="workspace-1",
        session_id="user/default/ipA/orchestrator",
        chat_message_id="chat-1",
        message_text="build ipA",
    )
    bridge_dir = tmp_path / ".session" / "orchestrators-ipc" / outcome.run_id / "tool-bridge"
    token = json.loads(
        (tmp_path / ".session" / "orchestrators-ipc" / outcome.run_id / "request.json").read_text(
            encoding="utf-8"
        )
    )["tool_bridge_token"]
    request_path = bridge_dir / "requests" / "req-1.json"
    request_path.write_text(
        json.dumps({
            "id": "req-1",
            "token": token,
            "tool": "dispatch_workflow",
            "kwargs": {"workflow": "ssot-gen", "ip": "ipA"},
        }),
        encoding="utf-8",
    )
    response_path = bridge_dir / "responses" / "req-1.json"
    deadline = time.monotonic() + 2.0
    while time.monotonic() < deadline and not response_path.exists():
        time.sleep(0.05)

    response = json.loads(response_path.read_text(encoding="utf-8"))
    assert response["ok"] is True
    assert response["result"]["source"] == "dispatch_workflow_tool"
    assert calls == [{"workflow": "ssot-gen", "ip": "ipA"}]


def test_supervisor_tool_bridge_rejects_unsafe_request_id(
    tmp_path: Path, monkeypatch
) -> None:
    runtime, _db, _spawned, _jobs, _processes = _runtime(tmp_path)
    core_tools = importlib.import_module("core.tools")
    calls: list[dict[str, Any]] = []

    def fake_dispatch(**kwargs: Any) -> dict[str, Any]:
        calls.append(dict(kwargs))
        return {"ok": True}

    monkeypatch.setattr(core_tools, "_dispatch_workflow_callback", fake_dispatch)
    outcome = runtime.submit_or_attach(user_id="user-1", ip_id="ip-1", ip_name="ipA")
    control_dir = tmp_path / ".session" / "orchestrators-ipc" / outcome.run_id
    bridge_dir = control_dir / "tool-bridge"
    token = json.loads((control_dir / "request.json").read_text(encoding="utf-8"))[
        "tool_bridge_token"
    ]
    request_path = bridge_dir / "requests" / "evil.json"
    request_path.write_text(
        json.dumps({
            "id": "../escape",
            "token": token,
            "tool": "dispatch_workflow",
            "kwargs": {"workflow": "ssot-gen", "ip": "ipA"},
        }),
        encoding="utf-8",
    )
    response_path = bridge_dir / "responses" / "evil.json"
    deadline = time.monotonic() + 2.0
    while time.monotonic() < deadline and not response_path.exists():
        time.sleep(0.05)

    response = json.loads(response_path.read_text(encoding="utf-8"))
    assert response["ok"] is False
    assert "not safe" in response["result"]["error"]
    assert calls == []
    assert not (bridge_dir / "escape.json").exists()


def test_supervisor_tool_bridge_rejects_symlinked_responses_dir_before_dispatch(
    tmp_path: Path, monkeypatch
) -> None:
    runtime, _db, _spawned, _jobs, _processes = _runtime(tmp_path)
    core_tools = importlib.import_module("core.tools")
    calls: list[dict[str, Any]] = []

    def fake_dispatch(**kwargs: Any) -> dict[str, Any]:
        calls.append(dict(kwargs))
        return {"ok": True, "source": "dispatch_workflow_tool"}

    monkeypatch.setattr(core_tools, "_dispatch_workflow_callback", fake_dispatch)
    outcome = runtime.submit_or_attach(user_id="user-1", ip_id="ip-1", ip_name="ipA")
    control_dir = tmp_path / ".session" / "orchestrators-ipc" / outcome.run_id
    bridge_dir = control_dir / "tool-bridge"
    token = json.loads((control_dir / "request.json").read_text(encoding="utf-8"))[
        "tool_bridge_token"
    ]
    outside = tmp_path / "outside-responses"
    outside.mkdir()
    responses_dir = bridge_dir / "responses"
    responses_dir.rmdir()
    responses_dir.symlink_to(outside, target_is_directory=True)
    request_path = bridge_dir / "requests" / "req-1.json"
    request_path.write_text(
        json.dumps({
            "id": "req-1",
            "token": token,
            "tool": "dispatch_workflow",
            "kwargs": {"workflow": "ssot-gen", "ip": "ipA"},
        }),
        encoding="utf-8",
    )
    response_path = bridge_dir / "responses" / "req-1.json"
    deadline = time.monotonic() + 2.0
    while time.monotonic() < deadline and not response_path.exists():
        time.sleep(0.05)

    assert not (outside / "req-1.json").exists()
    assert not responses_dir.is_symlink()
    response = json.loads(response_path.read_text(encoding="utf-8"))
    assert response["ok"] is False
    assert "responses must not be a symlink" in response["result"]["error"]
    assert calls == []


def test_supervisor_tool_bridge_rejects_symlinked_bridge_root(
    tmp_path: Path, monkeypatch
) -> None:
    runtime, _db, _spawned, _jobs, _processes = _runtime(tmp_path)
    core_tools = importlib.import_module("core.tools")
    calls: list[dict[str, Any]] = []

    def fake_dispatch(**kwargs: Any) -> dict[str, Any]:
        calls.append(dict(kwargs))
        return {"ok": True}

    monkeypatch.setattr(core_tools, "_dispatch_workflow_callback", fake_dispatch)
    outcome = runtime.submit_or_attach(user_id="user-1", ip_id="ip-1", ip_name="ipA")
    control_dir = tmp_path / ".session" / "orchestrators-ipc" / outcome.run_id
    bridge_dir = control_dir / "tool-bridge"
    token = json.loads((control_dir / "request.json").read_text(encoding="utf-8"))[
        "tool_bridge_token"
    ]
    outside_bridge = tmp_path / "outside-bridge"
    (outside_bridge / "requests").mkdir(parents=True)
    (outside_bridge / "responses").mkdir()
    shutil.rmtree(bridge_dir)
    bridge_dir.symlink_to(outside_bridge, target_is_directory=True)
    (outside_bridge / "requests" / "req-1.json").write_text(
        json.dumps({
            "id": "req-1",
            "token": token,
            "tool": "dispatch_workflow",
            "kwargs": {"workflow": "ssot-gen", "ip": "ipA"},
        }),
        encoding="utf-8",
    )

    time.sleep(0.2)

    assert calls == []
    assert not (outside_bridge / "responses" / "req-1.json").exists()


def test_supervisor_tool_bridge_rejects_missing_token(
    tmp_path: Path, monkeypatch
) -> None:
    runtime, _db, _spawned, _jobs, _processes = _runtime(tmp_path)
    core_tools = importlib.import_module("core.tools")
    calls: list[dict[str, Any]] = []

    def fake_dispatch(**kwargs: Any) -> dict[str, Any]:
        calls.append(dict(kwargs))
        return {"ok": True}

    monkeypatch.setattr(core_tools, "_dispatch_workflow_callback", fake_dispatch)
    outcome = runtime.submit_or_attach(user_id="user-1", ip_id="ip-1", ip_name="ipA")
    bridge_dir = tmp_path / ".session" / "orchestrators-ipc" / outcome.run_id / "tool-bridge"
    request_path = bridge_dir / "requests" / "req-no-token.json"
    request_path.write_text(
        json.dumps({
            "id": "req-no-token",
            "tool": "dispatch_workflow",
            "kwargs": {"workflow": "ssot-gen", "ip": "ipA"},
        }),
        encoding="utf-8",
    )
    response_path = bridge_dir / "responses" / "req-no-token.json"
    deadline = time.monotonic() + 2.0
    while time.monotonic() < deadline and not response_path.exists():
        time.sleep(0.05)

    response = json.loads(response_path.read_text(encoding="utf-8"))
    assert response["ok"] is False
    assert "token mismatch" in response["result"]["error"]
    assert calls == []


def test_supervisor_tool_bridge_rejects_symlink_request(
    tmp_path: Path, monkeypatch
) -> None:
    runtime, _db, _spawned, _jobs, _processes = _runtime(tmp_path)
    core_tools = importlib.import_module("core.tools")
    calls: list[dict[str, Any]] = []

    def fake_dispatch(**kwargs: Any) -> dict[str, Any]:
        calls.append(dict(kwargs))
        return {"ok": True}

    monkeypatch.setattr(core_tools, "_dispatch_workflow_callback", fake_dispatch)
    outcome = runtime.submit_or_attach(user_id="user-1", ip_id="ip-1", ip_name="ipA")
    control_dir = tmp_path / ".session" / "orchestrators-ipc" / outcome.run_id
    bridge_dir = control_dir / "tool-bridge"
    target_path = tmp_path / "external-request.json"
    target_path.write_text(
        json.dumps({
            "id": "link",
            "token": json.loads((control_dir / "request.json").read_text(encoding="utf-8"))[
                "tool_bridge_token"
            ],
            "tool": "dispatch_workflow",
            "kwargs": {"workflow": "ssot-gen", "ip": "ipA"},
        }),
        encoding="utf-8",
    )
    link_path = bridge_dir / "requests" / "link.json"
    link_path.symlink_to(target_path)
    response_path = bridge_dir / "responses" / "link.json"
    deadline = time.monotonic() + 2.0
    while time.monotonic() < deadline and not response_path.exists():
        time.sleep(0.05)

    response = json.loads(response_path.read_text(encoding="utf-8"))
    assert response["ok"] is False
    assert "symlink" in response["result"]["error"]
    assert calls == []


def test_supervisor_paths_reject_symlinked_request_file(tmp_path: Path) -> None:
    from src.orchestrator.supervisor_runtime import _prepare_supervisor_paths

    control = tmp_path / ".session" / "orchestrators-ipc" / "run-1"
    paths = {
        "control": control,
        "request": control / "request.json",
        "response": control / "response.json",
        "wake": control / "wake.jsonl",
        "cancel": control / "cancel.json",
        "log": control / "supervisor.log",
        "bridge": control / "tool-bridge",
    }
    control.mkdir(parents=True)
    target = tmp_path / "outside-request.json"
    target.write_text("{}", encoding="utf-8")
    paths["request"].symlink_to(target)

    with pytest.raises(ValueError, match="file must not be a symlink"):
        _prepare_supervisor_paths(paths, tmp_path)


def test_supervisor_paths_reject_symlinked_log_file(tmp_path: Path) -> None:
    from src.orchestrator.supervisor_runtime import _prepare_supervisor_paths

    control = tmp_path / ".session" / "orchestrators-ipc" / "run-1"
    paths = {
        "control": control,
        "request": control / "request.json",
        "response": control / "response.json",
        "wake": control / "wake.jsonl",
        "cancel": control / "cancel.json",
        "log": control / "supervisor.log",
        "bridge": control / "tool-bridge",
    }
    control.mkdir(parents=True)
    target = tmp_path / "outside.log"
    target.write_text("", encoding="utf-8")
    paths["log"].symlink_to(target)

    with pytest.raises(ValueError, match="file must not be a symlink"):
        _prepare_supervisor_paths(paths, tmp_path)


def test_call_bridge_timeout_removes_stale_request(tmp_path: Path) -> None:
    from src.orchestrator.ipc_tool_bridge import call_bridge

    bridge_dir = tmp_path / "bridge"
    result = call_bridge(
        bridge_dir,
        tool="dispatch_workflow",
        kwargs={"workflow": "ssot-gen"},
        timeout_s=0.01,
        token="token-1",
    )

    assert result["ok"] is False
    assert not list((bridge_dir / "requests").glob("*.json"))


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
