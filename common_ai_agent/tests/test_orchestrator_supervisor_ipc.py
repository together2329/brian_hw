from __future__ import annotations

import json
import importlib
import os
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src.orchestrator.loop import RunOutcome  # noqa: E402

AtlasDB = importlib.import_module("core.atlas_db").AtlasDB


def _request(tmp_path: Path, db_path: Path) -> dict[str, Any]:
    control_dir = tmp_path / ".session" / "orchestrators-ipc" / "run-1"
    return {
        "schema_version": 1,
        "kind": "orchestrator-supervisor",
        "run_id": "run-1",
        "project_root": str(tmp_path),
        "source_root": str(Path(__file__).resolve().parents[1]),
        "db_path": str(db_path),
        "user_id": "user-name",
        "db_user_id": "user-db-1",
        "workspace_id": "workspace-1",
        "ip_id": "ip-db-1",
        "ip_name": "ipA",
        "session_id": "user/default/ipA/orchestrator",
        "workspace_session": "default",
        "chat_message_id": "chat-1",
        "initial_user_message": "build ipA",
        "model": "gpt-test",
        "reasoning_effort": "medium",
        "control_dir": str(control_dir),
        "wake_path": str(control_dir / "wake.jsonl"),
        "cancel_path": str(control_dir / "cancel.json"),
        "response_path": str(control_dir / "response.json"),
    }


def test_supervisor_ipc_runs_controlled_loop_and_writes_response(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    supervisor = importlib.import_module("src.atlas_orchestrator_supervisor_ipc")

    db_path = tmp_path / "atlas.db"
    db = AtlasDB(str(db_path))
    db.init_db()
    db.close()
    request_path = tmp_path / "request.json"
    response_path = tmp_path / "response.json"
    request_path.write_text(json.dumps(_request(tmp_path, db_path)), encoding="utf-8")
    captured: dict[str, Any] = {}

    class FakeLoop:
        def __init__(self, db: Any, ctx: Any, initial_user_message: str) -> None:
            captured["ctx"] = ctx
            captured["initial_user_message"] = initial_user_message
            captured["db_path"] = getattr(db, "db_path", "")

        def run(self) -> RunOutcome:
            return RunOutcome(status="completed", final_state="done", steps_taken=2)

    monkeypatch.setattr(supervisor, "_build_loop", FakeLoop)

    rc = supervisor.main(
        ["--request", str(request_path), "--response", str(response_path), "--run-id", "run-1"]
    )

    assert rc == 0
    response = json.loads(response_path.read_text(encoding="utf-8"))
    assert response["kind"] == "orchestrator-supervisor"
    assert response["run_id"] == "run-1"
    assert response["status"] == "completed"
    assert response["final_state"] == "done"
    assert response["steps_taken"] == 2
    assert capsys.readouterr().out == ""


def test_supervisor_ipc_propagates_request_context(
    tmp_path: Path, monkeypatch
) -> None:
    supervisor = importlib.import_module("src.atlas_orchestrator_supervisor_ipc")
    ip_workflow = tmp_path / "ipA" / "workflow"
    (ip_workflow / "ssot-gen").mkdir(parents=True)

    db_path = tmp_path / "atlas.db"
    db = AtlasDB(str(db_path))
    db.init_db()
    db.close()
    request = _request(tmp_path, db_path)
    request_path = tmp_path / "request.json"
    response_path = tmp_path / "response.json"
    request_path.write_text(json.dumps(request), encoding="utf-8")
    captured: dict[str, Any] = {}

    class FakeLoop:
        def __init__(self, db: Any, ctx: Any, initial_user_message: str) -> None:
            captured["ctx"] = ctx
            captured["initial_user_message"] = initial_user_message

        def run(self) -> RunOutcome:
            return RunOutcome(status="blocked", final_state="need_user", steps_taken=1)

    monkeypatch.setattr(supervisor, "_build_loop", FakeLoop)

    rc = supervisor.main(
        ["--request", str(request_path), "--response", str(response_path), "--run-id", "run-1"]
    )

    ctx = captured["ctx"]
    assert rc == 2
    assert ctx.run_id == "run-1"
    assert ctx.user_id == "user-db-1"
    assert ctx.ip_id == "ip-db-1"
    assert ctx.ip_name == "ipA"
    assert ctx.workspace_id == "workspace-1"
    assert ctx.session_id == "user/default/ipA/orchestrator"
    assert ctx.project_root == tmp_path
    assert hasattr(ctx.runner, "register_waker")
    assert captured["initial_user_message"] == "build ipA"
    assert os.environ["ATLAS_WORKER_TRANSPORT"] == "ipc"
    assert os.environ["ATLAS_ORCHESTRATOR_MODE"] == "1"
    assert os.environ["ATLAS_ACTIVE_SESSION"] == "user/default/ipA/orchestrator"
    assert os.environ["ATLAS_ACTIVE_IP"] == "ipA"
    assert os.environ["ATLAS_WORKFLOW_ROOT"] == str(ip_workflow)
    assert os.environ["ATLAS_IP_ID"] == "ip-db-1"
    assert os.environ["ATLAS_DB_PATH"] == str(db_path)
    assert os.environ["ATLAS_MEMORY_DB_PATH"] == str(db_path)
