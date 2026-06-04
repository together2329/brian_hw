from __future__ import annotations

import importlib
import sys
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))


def test_react_task_session_files_use_request_project_root(tmp_path: Path) -> None:
    agent_server = importlib.import_module("core.agent_server")
    react_loop = importlib.import_module("core.react_loop")

    source_root = tmp_path / "source"
    project_root = tmp_path / "alice" / "alt"
    session_name = "alice/alt/pl330/rtl-gen"
    expected_session_dir = project_root / ".session" / session_name
    captured: dict[str, object] = {}
    entry = agent_server._create_run("record session files")
    old_project_root = getattr(agent_server, "_project_root")
    old_persistence = getattr(agent_server, "_PERSISTENCE_ENABLED")
    source_root.mkdir(parents=True)

    def fake_run_react_agent_impl(*, messages, tracker, deps, **_kwargs):
        captured["history_file"] = deps.cfg.HISTORY_FILE
        captured["todo_file"] = deps.cfg.TODO_FILE
        captured["session_dir"] = deps.cfg.SESSION_DIR
        tracker.current = 1
        return messages + [{"role": "assistant", "content": "Final Answer: session closed"}], "normal"

    try:
        setattr(agent_server, "_project_root", str(source_root))
        setattr(agent_server, "_PERSISTENCE_ENABLED", False)
        with patch.object(react_loop, "run_react_agent_impl", side_effect=fake_run_react_agent_impl):
            agent_server._run_react_task(
                entry,
                "record session files",
                model="test-model",
                todos=[{"content": "capture session todo"}],
                session_name=session_name,
                ip="pl330",
                workflow="",
                project_root=str(project_root),
            )
    finally:
        setattr(agent_server, "_project_root", old_project_root)
        setattr(agent_server, "_PERSISTENCE_ENABLED", old_persistence)

    assert entry.status == "completed", entry.error
    assert captured["session_dir"] == str(expected_session_dir)
    assert captured["history_file"] == str(expected_session_dir / "conversation.json")
    assert captured["todo_file"] == str(expected_session_dir / "todo.json")
    assert (expected_session_dir / "conversation.json").is_file()
    assert (expected_session_dir / "todo.json").is_file()
    assert not (source_root / ".session" / session_name / "conversation.json").exists()
    assert not (source_root / ".session" / session_name / "todo.json").exists()


def test_run_rejects_project_root_for_another_session_owner(
    tmp_path: Path,
    monkeypatch,
) -> None:
    agent_server = importlib.import_module("core.agent_server")
    called = False

    def fake_run_react_task(*_args, **_kwargs):
        nonlocal called
        called = True

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setattr(agent_server, "_run_react_task", fake_run_react_task)

    client = TestClient(agent_server.create_app())
    response = client.post("/run", json={
        "task": "reject mismatched root",
        "sync": True,
        "workflow": "rtl-gen",
        "ip": "pl330",
        "session": "alice/alt/pl330/rtl-gen",
        "project_root": str(tmp_path / "bob" / "default"),
    })

    assert response.status_code == 403, response.text
    assert called is False
    assert not (tmp_path / "bob" / "default" / ".session").exists()


def test_run_rejects_short_session_project_root_binding(
    tmp_path: Path,
    monkeypatch,
) -> None:
    agent_server = importlib.import_module("core.agent_server")
    called = False

    def fake_run_react_task(*_args, **_kwargs):
        nonlocal called
        called = True

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setattr(agent_server, "_run_react_task", fake_run_react_task)

    client = TestClient(agent_server.create_app())
    response = client.post("/run", json={
        "task": "reject short session binding",
        "sync": True,
        "workflow": "rtl-gen",
        "ip": "pl330",
        "session": "pl330/rtl-gen",
        "project_root": str(tmp_path / "bob" / "default"),
    })

    assert response.status_code == 403, response.text
    assert called is False
    assert not (tmp_path / "bob" / "default" / ".session").exists()


def test_run_rejects_project_root_outside_worker_boundary(
    tmp_path: Path,
    monkeypatch,
) -> None:
    agent_server = importlib.import_module("core.agent_server")
    called = False
    outside_root = tmp_path.parent / f"{tmp_path.name}_outside" / "alice" / "alt"

    def fake_run_react_task(*_args, **_kwargs):
        nonlocal called
        called = True

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setattr(agent_server, "_run_react_task", fake_run_react_task)

    client = TestClient(agent_server.create_app())
    response = client.post("/run", json={
        "task": "reject outside root",
        "sync": True,
        "workflow": "rtl-gen",
        "ip": "pl330",
        "session": "alice/alt/pl330/rtl-gen",
        "project_root": str(outside_root),
    })

    assert response.status_code == 403, response.text
    assert called is False
    assert not (outside_root / ".session").exists()


def test_run_rejects_symlinked_project_root(
    tmp_path: Path,
    monkeypatch,
) -> None:
    agent_server = importlib.import_module("core.agent_server")
    called = False
    target = tmp_path / "bob" / "default"
    link = tmp_path / "alice" / "alt"
    target.mkdir(parents=True)
    link.parent.mkdir(parents=True)
    link.symlink_to(target, target_is_directory=True)

    def fake_run_react_task(*_args, **_kwargs):
        nonlocal called
        called = True

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setattr(agent_server, "_run_react_task", fake_run_react_task)

    client = TestClient(agent_server.create_app())
    response = client.post("/run", json={
        "task": "reject symlink root",
        "sync": True,
        "workflow": "rtl-gen",
        "ip": "pl330",
        "session": "alice/alt/pl330/rtl-gen",
        "project_root": str(link),
    })

    assert response.status_code == 403, response.text
    assert called is False
    assert not (target / ".session").exists()


def test_worker_run_rejects_project_root_outside_worker_workspace(
    tmp_path: Path,
    monkeypatch,
) -> None:
    agent_server = importlib.import_module("core.agent_server")

    allowed_root = tmp_path / "alice" / "alt"
    outside_root = tmp_path / "bob" / "alt"
    allowed_root.mkdir(parents=True)
    outside_root.mkdir(parents=True)
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(allowed_root))
    monkeypatch.setenv("ATLAS_WORKSPACE_ROOT", str(allowed_root))
    called = False

    def fake_run_react_task(*_args, **_kwargs) -> None:
        nonlocal called
        called = True

    with patch.object(agent_server, "_run_react_task", side_effect=fake_run_react_task):
        response = TestClient(agent_server.create_app()).post("/run", json={
            "project_root": str(outside_root),
            "session": "alice/alt/pl330/rtl-gen",
            "task": "should not run",
            "workflow": "rtl-gen",
        })

    assert response.status_code == 403, response.text
    assert response.json()["detail"] == "project_root outside worker workspace"
    assert called is False


def test_worker_run_rejects_session_owner_mismatch_inside_worker_workspace(
    tmp_path: Path,
    monkeypatch,
) -> None:
    agent_server = importlib.import_module("core.agent_server")

    allowed_root = tmp_path / "alice" / "alt"
    allowed_root.mkdir(parents=True)
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(allowed_root))
    monkeypatch.setenv("ATLAS_WORKSPACE_ROOT", str(allowed_root))
    called = False

    def fake_run_react_task(*_args, **_kwargs) -> None:
        nonlocal called
        called = True

    with patch.object(agent_server, "_run_react_task", side_effect=fake_run_react_task):
        response = TestClient(agent_server.create_app()).post("/run", json={
            "project_root": str(allowed_root),
            "session": "bob/alt/pl330/rtl-gen",
            "task": "should not run",
            "workflow": "rtl-gen",
        })

    assert response.status_code == 403, response.text
    assert response.json()["detail"] == "project_root outside worker workspace"
    assert called is False


def test_worker_run_uses_env_project_root_when_request_omits_project_root(
    tmp_path: Path,
    monkeypatch,
) -> None:
    agent_server = importlib.import_module("core.agent_server")
    react_loop = importlib.import_module("core.react_loop")

    source_root = tmp_path / "source"
    allowed_root = tmp_path / "alice" / "alt"
    session_name = "alice/alt/pl330/rtl-gen"
    expected_session_dir = allowed_root / ".session" / session_name
    captured: dict[str, object] = {}
    source_root.mkdir(parents=True)
    allowed_root.mkdir(parents=True)
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(allowed_root))
    monkeypatch.setenv("ATLAS_WORKSPACE_ROOT", str(allowed_root))
    monkeypatch.setattr(agent_server, "_project_root", str(source_root))
    monkeypatch.setattr(agent_server, "_PERSISTENCE_ENABLED", False)

    def fake_run_react_agent_impl(*, messages, tracker, deps, **_kwargs):
        captured["history_file"] = deps.cfg.HISTORY_FILE
        captured["todo_file"] = deps.cfg.TODO_FILE
        captured["session_dir"] = deps.cfg.SESSION_DIR
        tracker.current = 1
        return messages + [{"role": "assistant", "content": "Final Answer: session closed"}], "normal"

    with patch.object(react_loop, "run_react_agent_impl", side_effect=fake_run_react_agent_impl):
        response = TestClient(agent_server.create_app()).post("/run", json={
            "session": session_name,
            "task": "record session files",
            "todos": [{"content": "capture session todo"}],
            "sync": True,
        })

    assert response.status_code == 200, response.text
    assert captured["session_dir"] == str(expected_session_dir)
    assert captured["history_file"] == str(expected_session_dir / "conversation.json")
    assert captured["todo_file"] == str(expected_session_dir / "todo.json")
    assert (expected_session_dir / "conversation.json").is_file()
    assert (expected_session_dir / "todo.json").is_file()
    assert not (source_root / ".session" / session_name / "conversation.json").exists()
