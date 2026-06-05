from __future__ import annotations

import json
import importlib
import os
import sys
import threading
import time
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


def _write_canonical_request_file(request: dict[str, Any]) -> tuple[Path, Path]:
    request_path = Path(str(request["control_dir"])) / "request.json"
    response_path = Path(str(request["response_path"]))
    request_path.parent.mkdir(parents=True, exist_ok=True)
    request_path.write_text(json.dumps(request), encoding="utf-8")
    return request_path, response_path


def test_supervisor_ipc_main_does_not_write_response_outside_control_dir(
    tmp_path: Path, monkeypatch
) -> None:
    supervisor = importlib.import_module("src.atlas_orchestrator_supervisor_ipc")
    db_path = tmp_path / "atlas.db"
    db = AtlasDB(str(db_path))
    db.init_db()
    db.close()
    request = _request(tmp_path, db_path)
    request_path, _response_path = _write_canonical_request_file(request)
    outside_response = tmp_path / "outside" / "response.json"
    outside_response.parent.mkdir()

    class FakeLoop:
        def __init__(self, db: Any, ctx: Any, initial_user_message: str) -> None:
            pass

        def run(self) -> RunOutcome:
            return RunOutcome(status="completed", final_state="done", steps_taken=1)

    monkeypatch.setattr(supervisor, "_build_loop", FakeLoop)

    rc = supervisor.main(
        ["--request", str(request_path), "--response", str(outside_response), "--run-id", "run-1"]
    )

    assert rc == 1
    assert not outside_response.exists()


def test_supervisor_ipc_rejects_outside_tool_bridge_dir_before_bridge_write(
    tmp_path: Path, monkeypatch
) -> None:
    supervisor = importlib.import_module("src.atlas_orchestrator_supervisor_ipc")
    db_path = tmp_path / "atlas.db"
    db = AtlasDB(str(db_path))
    db.init_db()
    db.close()
    request = _request(tmp_path, db_path)
    outside_bridge = tmp_path / "outside-bridge"
    request["tool_bridge_dir"] = str(outside_bridge)
    request["tool_bridge_token"] = "bridge-token"
    request_path, response_path = _write_canonical_request_file(request)

    class FakeLoop:
        def __init__(self, db: Any, ctx: Any, initial_user_message: str) -> None:
            pass

        def run(self) -> RunOutcome:
            from src.orchestrator import tools as orch_tools

            orch_tools.dispatch_workflow(
                workflow="ssot-gen",
                ip="ipA",
                model="worker-model",
                prompt="build ssot",
            )
            return RunOutcome(status="completed", final_state="done", steps_taken=1)

    monkeypatch.setattr(supervisor, "_build_loop", FakeLoop)

    rc = supervisor.main(
        ["--request", str(request_path), "--response", str(response_path), "--run-id", "run-1"]
    )

    assert rc == 1
    assert not list(outside_bridge.rglob("*.json"))
    assert not response_path.exists()


def test_supervisor_ipc_rejects_symlinked_tool_bridge_dir_before_bridge_write(
    tmp_path: Path, monkeypatch
) -> None:
    supervisor = importlib.import_module("src.atlas_orchestrator_supervisor_ipc")
    db_path = tmp_path / "atlas.db"
    db = AtlasDB(str(db_path))
    db.init_db()
    db.close()
    request = _request(tmp_path, db_path)
    outside_bridge = tmp_path / "outside-bridge"
    outside_bridge.mkdir()
    control_dir = Path(str(request["control_dir"]))
    control_dir.mkdir(parents=True, exist_ok=True)
    bridge_link = control_dir / "tool-bridge"
    bridge_link.symlink_to(outside_bridge, target_is_directory=True)
    request["tool_bridge_dir"] = str(bridge_link)
    request["tool_bridge_token"] = "bridge-token"
    request_path, response_path = _write_canonical_request_file(request)

    class FakeLoop:
        def __init__(self, db: Any, ctx: Any, initial_user_message: str) -> None:
            pass

        def run(self) -> RunOutcome:
            from src.orchestrator import tools as orch_tools

            orch_tools.read_pipeline_state(ip="ipA")
            return RunOutcome(status="completed", final_state="done", steps_taken=1)

    monkeypatch.setattr(supervisor, "_build_loop", FakeLoop)

    rc = supervisor.main(
        ["--request", str(request_path), "--response", str(response_path), "--run-id", "run-1"]
    )

    assert rc == 1
    assert not list(outside_bridge.rglob("*.json"))
    assert not response_path.exists()


def test_supervisor_ipc_runs_controlled_loop_and_writes_response(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    supervisor = importlib.import_module("src.atlas_orchestrator_supervisor_ipc")

    db_path = tmp_path / "atlas.db"
    db = AtlasDB(str(db_path))
    db.init_db()
    db.close()
    request = _request(tmp_path, db_path)
    request_path, response_path = _write_canonical_request_file(request)
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
    request_path, response_path = _write_canonical_request_file(request)
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


def test_supervisor_ipc_configures_src_path_for_top_level_config_import(
    tmp_path: Path, monkeypatch
) -> None:
    supervisor = importlib.import_module("src.atlas_orchestrator_supervisor_ipc")
    source_root = Path(__file__).resolve().parents[1]
    src_root = str(source_root / "src")
    monkeypatch.syspath_prepend(str(source_root))
    monkeypatch.setattr(
        sys,
        "path",
        [item for item in sys.path if item != src_root],
    )
    sys.modules.pop("config", None)

    request = _request(tmp_path, tmp_path / "atlas.db")
    request["source_root"] = str(source_root)

    supervisor._configure_env(request)

    assert src_root in sys.path
    config = importlib.import_module("config")
    config_file = config.__file__
    assert config_file is not None
    assert Path(config_file).resolve() == source_root / "src" / "config.py"


def test_supervisor_ipc_enrich_dispatch_overwrites_spoofed_payload_context(
    tmp_path: Path,
) -> None:
    supervisor = importlib.import_module("src.atlas_orchestrator_supervisor_ipc")
    request = _request(tmp_path, tmp_path / "atlas.db")

    enriched = supervisor._enrich_dispatch_kwargs(
        {
            "workflow": "ssot-gen",
            "ip": "wrongIp",
            "model": "worker-model",
            "exec_mode": "thread",
            "payload": {
                "db_user_id": "attacker",
                "orchestrator_session_id": "attacker/default/wrongIp/orchestrator",
                "workspace_session": "other",
                "orchestrator_run_id": "",
                "trigger_source": "manual",
                "ip": "wrongIp",
            },
        },
        request,
    )

    payload = enriched["payload"]
    assert enriched["ip"] == "ipA"
    assert enriched["model"] == "worker-model"
    assert enriched["exec_mode"] == "orchestrator"
    assert payload["db_user_id"] == "user-db-1"
    assert payload["orchestrator_session_id"] == "user/default/ipA/orchestrator"
    assert payload["workspace_session"] == "default"
    assert payload["orchestrator_run_id"] == "run-1"
    assert payload["trigger_source"] == "orchestrator_chat"
    assert payload["ip"] == "ipA"


def test_supervisor_ipc_no_bridge_request_clears_stale_bridge_callbacks(
    tmp_path: Path, monkeypatch
) -> None:
    supervisor = importlib.import_module("src.atlas_orchestrator_supervisor_ipc")
    core_tools = importlib.import_module("core.tools")
    request = _request(tmp_path, tmp_path / "atlas.db")
    monkeypatch.setattr(core_tools, "_dispatch_workflow_callback", lambda **_: {"ok": True})
    monkeypatch.setattr(core_tools, "_read_pipeline_state_callback", lambda **_: {"ok": True})
    monkeypatch.setenv("ATLAS_ORCHESTRATOR_TOOL_BRIDGE_DIR", "/tmp/stale-bridge")
    monkeypatch.setenv("ATLAS_ORCHESTRATOR_TOOL_BRIDGE_TOKEN", "stale-token")

    supervisor._configure_env(request)
    supervisor._install_tool_bridge(request)

    assert "ATLAS_ORCHESTRATOR_TOOL_BRIDGE_DIR" not in os.environ
    assert "ATLAS_ORCHESTRATOR_TOOL_BRIDGE_TOKEN" not in os.environ
    assert core_tools._dispatch_workflow_callback is None
    assert core_tools._read_pipeline_state_callback is None


def test_supervisor_ipc_dispatch_workflow_uses_parent_tool_bridge(
    tmp_path: Path, monkeypatch
) -> None:
    supervisor = importlib.import_module("src.atlas_orchestrator_supervisor_ipc")
    bridge_mod = importlib.import_module("src.orchestrator.ipc_tool_bridge")

    db_path = tmp_path / "atlas.db"
    db = AtlasDB(str(db_path))
    db.init_db()
    db.close()
    request = _request(tmp_path, db_path)
    bridge_dir = tmp_path / ".session" / "orchestrators-ipc" / "run-1" / "tool-bridge"
    request["tool_bridge_dir"] = str(bridge_dir)
    request["tool_bridge_token"] = "bridge-token-1"
    request_path, response_path = _write_canonical_request_file(request)
    captured: dict[str, Any] = {}
    stop = threading.Event()

    def bridge_loop() -> None:
        deadline = time.monotonic() + 5.0
        requests_dir = bridge_dir / "requests"
        while not stop.is_set() and time.monotonic() < deadline:
            for item in list(requests_dir.glob("*.json")):
                data = json.loads(item.read_text(encoding="utf-8"))
                captured["bridge_request"] = data
                request_id = str(data.get("id") or item.stem)
                bridge_mod.write_json_atomic(
                    bridge_dir / "responses" / f"{request_id}.json",
                    {
                        "ok": True,
                        "id": request_id,
                        "tool": data.get("tool"),
                        "result": {
                            "ok": True,
                            "source": "parent_tool_bridge",
                            "workflow": data.get("kwargs", {}).get("workflow"),
                        },
                        "summary": "parent bridge ok",
                    },
                )
                item.unlink()
                stop.set()
            time.sleep(0.02)

    class FakeLoop:
        def __init__(self, db: Any, ctx: Any, initial_user_message: str) -> None:
            captured["ctx"] = ctx

        def run(self) -> RunOutcome:
            from src.orchestrator import tools as orch_tools

            result, summary = orch_tools.dispatch_workflow(
                workflow="ssot-gen",
                ip="ipA",
                model="worker-model",
                prompt="build ssot",
            )
            captured["result"] = result
            captured["summary"] = summary
            return RunOutcome(status="completed", final_state="done", steps_taken=1)

    thread = threading.Thread(target=bridge_loop, daemon=True)
    thread.start()
    monkeypatch.setattr(supervisor, "_build_loop", FakeLoop)

    rc = supervisor.main(
        ["--request", str(request_path), "--response", str(response_path), "--run-id", "run-1"]
    )
    thread.join(timeout=1.0)

    assert rc == 0
    kwargs = captured["bridge_request"]["kwargs"]
    payload = kwargs["payload"]
    assert captured["bridge_request"]["token"] == "bridge-token-1"
    assert kwargs["model"] == "worker-model"
    assert payload["db_user_id"] == "user-db-1"
    assert payload["orchestrator_session_id"] == "user/default/ipA/orchestrator"
    assert payload["workspace_session"] == "default"
    assert payload["orchestrator_run_id"] == "run-1"
    assert payload["trigger_source"] == "orchestrator_chat"
    assert captured["result"]["source"] == "parent_tool_bridge"
    assert captured["result"]["workflow"] == "ssot-gen"
    assert "parent_tool_bridge" in captured["summary"]


def test_supervisor_ipc_read_pipeline_state_uses_request_context(
    tmp_path: Path, monkeypatch
) -> None:
    supervisor = importlib.import_module("src.atlas_orchestrator_supervisor_ipc")
    bridge_mod = importlib.import_module("src.orchestrator.ipc_tool_bridge")

    db_path = tmp_path / "atlas.db"
    db = AtlasDB(str(db_path))
    db.init_db()
    db.close()
    request = _request(tmp_path, db_path)
    bridge_dir = tmp_path / ".session" / "orchestrators-ipc" / "run-1" / "tool-bridge"
    request["tool_bridge_dir"] = str(bridge_dir)
    request["tool_bridge_token"] = "state-token-1"
    request_path, response_path = _write_canonical_request_file(request)
    captured: dict[str, Any] = {}
    stop = threading.Event()

    def bridge_loop() -> None:
        deadline = time.monotonic() + 5.0
        requests_dir = bridge_dir / "requests"
        while not stop.is_set() and time.monotonic() < deadline:
            for item in list(requests_dir.glob("*.json")):
                data = json.loads(item.read_text(encoding="utf-8"))
                captured["bridge_request"] = data
                request_id = str(data.get("id") or item.stem)
                bridge_mod.write_json_atomic(
                    bridge_dir / "responses" / f"{request_id}.json",
                    {
                        "ok": True,
                        "id": request_id,
                        "tool": data.get("tool"),
                        "result": {
                            "ok": True,
                            "source": "read_pipeline_state_tool",
                            "ip": data.get("kwargs", {}).get("ip"),
                        },
                        "summary": "state bridge ok",
                    },
                )
                item.unlink()
                stop.set()
            time.sleep(0.02)

    class FakeLoop:
        def __init__(self, db: Any, ctx: Any, initial_user_message: str) -> None:
            captured["ctx"] = ctx

        def run(self) -> RunOutcome:
            from src.orchestrator import tools as orch_tools

            result, summary = orch_tools.read_pipeline_state(ip="ipA")
            captured["result"] = result
            captured["summary"] = summary
            return RunOutcome(status="completed", final_state="done", steps_taken=1)

    thread = threading.Thread(target=bridge_loop, daemon=True)
    thread.start()
    monkeypatch.setattr(supervisor, "_build_loop", FakeLoop)

    rc = supervisor.main(
        ["--request", str(request_path), "--response", str(response_path), "--run-id", "run-1"]
    )
    thread.join(timeout=1.0)

    assert rc == 0
    kwargs = captured["bridge_request"]["kwargs"]
    assert captured["bridge_request"]["token"] == "state-token-1"
    assert kwargs["db_user_id"] == "user-db-1"
    assert kwargs["scope"] == "user/default/ipA/orchestrator"
    assert kwargs["ip"] == "ipA"
    assert captured["result"]["source"] == "read_pipeline_state_tool"
    assert captured["result"]["ip"] == "ipA"
