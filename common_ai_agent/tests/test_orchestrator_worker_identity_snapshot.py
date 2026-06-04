from __future__ import annotations

import json
import importlib
import sys
from pathlib import Path
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))


def _configure_trace_app(tmp_path: Path, monkeypatch) -> None:
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setenv("ATLAS_EXEC_MODE", "orchestrator")
    monkeypatch.setenv("ATLAS_ORCHESTRATOR_MODE", "1")
    monkeypatch.setenv("ATLAS_SINGLE_MAIN_LOOP", "0")
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "SOURCE_ROOT", tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)


def _authenticated_trace_client(tmp_path: Path, monkeypatch, username: str = "u") -> TestClient:
    import src.atlas_ui as atlas_ui

    _configure_trace_app(tmp_path, monkeypatch)
    client = TestClient(atlas_ui.create_app())
    reg = client.post("/api/auth/register", json={"username": username, "password": "pw"})
    assert reg.status_code == 200, reg.text
    return client


def test_workers_snapshot_names_request_user_workspace_and_session(tmp_path: Path, monkeypatch) -> None:
    import urllib.request

    import src.atlas_ui as atlas_ui

    jobs = importlib.import_module("atlas_api_jobs")
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setenv("ATLAS_EXEC_MODE", "orchestrator")
    monkeypatch.setenv("ATLAS_ORCHESTRATOR_MODE", "1")
    monkeypatch.setenv("ATLAS_SINGLE_MAIN_LOOP", "0")
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "SOURCE_ROOT", tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    def fake_urlopen(req, timeout=None):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "status": "ok",
            "workflow": "rtl-gen",
            "model": "gpt-5.3-codex",
            "owner": "u",
        }).encode("utf-8")
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        return mock_resp

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    with jobs._jobs_lock:
        jobs._jobs.clear()
        jobs._jobs["active-rtl"] = {
            "job_id": "active-rtl",
            "run_id": "run-active",
            "workflow": "rtl-gen",
            "stage_id": "rtl",
            "status": "running",
            "ip": "pl330",
            "user_id": "u",
            "model": "gpt-5.3-codex",
            "project_root": str(tmp_path / "u" / "alt"),
            "session": "u/alt/pl330/rtl-gen",
            "started_at": 1.0,
        }

    client = TestClient(atlas_ui.create_app())
    reg = client.post("/api/auth/register", json={"username": "u", "password": "pw"})
    assert reg.status_code == 200, reg.text
    resp = client.get("/api/orchestrator/workers?ip=pl330&workspace_session=alt&active_only=1")

    assert resp.status_code == 200, resp.text
    worker = resp.json()["workers"][0]
    assert worker["workflow"] == "rtl-gen"
    assert worker["worker_owner"] == "u"
    assert worker["workspace_session"] == "alt"
    assert worker["worker_session"] == "u/alt/pl330/rtl-gen"
    assert worker["active_jobs"][0]["session"] == "u/alt/pl330/rtl-gen"


def test_workers_snapshot_omits_identity_fields_in_single_user_mode(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import urllib.request

    import src.atlas_ui as atlas_ui

    jobs = importlib.import_module("atlas_api_jobs")
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "0")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setenv("ATLAS_EXEC_MODE", "orchestrator")
    monkeypatch.setenv("ATLAS_ORCHESTRATOR_MODE", "1")
    monkeypatch.setenv("ATLAS_SINGLE_MAIN_LOOP", "0")
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "SOURCE_ROOT", tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    def fake_urlopen(req, timeout=None):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "status": "ok",
            "workflow": "rtl-gen",
            "model": "gpt-5.3-codex",
            "owner": "u",
        }).encode("utf-8")
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        return mock_resp

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    with jobs._jobs_lock:
        jobs._jobs.clear()
        jobs._jobs["active-rtl"] = {
            "job_id": "active-rtl",
            "run_id": "run-active",
            "workflow": "rtl-gen",
            "stage_id": "rtl",
            "status": "running",
            "ip": "pl330",
            "user_id": "u",
            "model": "gpt-5.3-codex",
            "project_root": str(tmp_path),
            "session": "pl330/rtl-gen",
            "started_at": 1.0,
        }

    client = TestClient(atlas_ui.create_app())
    reg = client.post("/api/auth/register", json={"username": "u", "password": "pw"})
    assert reg.status_code == 200, reg.text
    resp = client.get("/api/orchestrator/workers?ip=pl330&active_only=1")

    assert resp.status_code == 200, resp.text
    worker = resp.json()["workers"][0]
    assert worker["workflow"] == "rtl-gen"
    assert worker["worker_owner"] == ""
    assert worker["workspace_session"] == ""
    assert worker["worker_session"] == ""
    assert worker["worker_partition"] == ""


def test_workers_snapshot_partitions_are_per_workflow(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import urllib.request

    import src.atlas_ui as atlas_ui

    jobs = importlib.import_module("atlas_api_jobs")
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setenv("ATLAS_EXEC_MODE", "orchestrator")
    monkeypatch.setenv("ATLAS_ORCHESTRATOR_MODE", "1")
    monkeypatch.setenv("ATLAS_SINGLE_MAIN_LOOP", "0")
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "SOURCE_ROOT", tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    def fake_urlopen(req, timeout=None):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"status":"unreachable"}'
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        return mock_resp

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    with jobs._jobs_lock:
        jobs._jobs.clear()
        for workflow in ("ssot-gen", "rtl-gen"):
            jobs._jobs[f"active-{workflow}"] = {
                "job_id": f"active-{workflow}",
                "run_id": f"run-{workflow}",
                "workflow": workflow,
                "stage_id": workflow,
                "status": "running",
                "ip": "pl330",
                "user_id": "u",
                "model": "gpt-5.3-codex",
                "project_root": str(tmp_path / "u" / "alt"),
                "session": f"u/alt/pl330/{workflow}",
                "started_at": 1.0,
            }

    client = TestClient(atlas_ui.create_app())
    reg = client.post("/api/auth/register", json={"username": "u", "password": "pw"})
    assert reg.status_code == 200, reg.text
    resp = client.get("/api/orchestrator/workers?ip=pl330&workspace_session=alt&active_only=1")

    assert resp.status_code == 200, resp.text
    by_workflow = {worker["workflow"]: worker for worker in resp.json()["workers"]}
    assert by_workflow["ssot-gen"]["worker_session"] == "u/alt/pl330/ssot-gen"
    assert by_workflow["rtl-gen"]["worker_session"] == "u/alt/pl330/rtl-gen"
    assert by_workflow["ssot-gen"]["worker_partition"].endswith("_u_alt_pl330_ssot-gen")
    assert by_workflow["rtl-gen"]["worker_partition"].endswith("_u_alt_pl330_rtl-gen")
    assert by_workflow["ssot-gen"]["worker_partition"] != by_workflow["rtl-gen"]["worker_partition"]


def test_orchestrator_trace_and_worker_activity_use_request_workspace_root(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import src.atlas_ui as atlas_ui

    trace_mod = importlib.import_module("core.orchestrator_trace")

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setenv("ATLAS_EXEC_MODE", "orchestrator")
    monkeypatch.setenv("ATLAS_ORCHESTRATOR_MODE", "1")
    monkeypatch.setenv("ATLAS_SINGLE_MAIN_LOOP", "0")
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "SOURCE_ROOT", tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    trace_mod.record_trace(
        "pl330",
        project_root=tmp_path / "u" / "default",
        lens="result",
        actor="ssot-gen-worker",
        kind="http_recv",
        corr="corr_default",
        run_id="default-run",
        session="u/default/pl330/ssot-gen",
    )
    trace_mod.record_trace(
        "pl330",
        project_root=tmp_path / "u" / "alt",
        lens="result",
        actor="rtl-gen-worker",
        kind="http_recv",
        corr="corr_alt",
        run_id="alt-run",
        session="u/alt/pl330/rtl-gen",
    )

    client = TestClient(atlas_ui.create_app())
    reg = client.post("/api/auth/register", json={"username": "u", "password": "pw"})
    assert reg.status_code == 200, reg.text

    trace = client.get("/api/orchestrator/trace?ip=pl330&workspace_session=alt")
    assert trace.status_code == 200, trace.text
    events = trace.json()["events"]
    assert [event["run_id"] for event in events] == ["alt-run"]

    workers = client.get("/api/orchestrator/workers?ip=pl330&workspace_session=alt&active_only=1")
    assert workers.status_code == 200, workers.text
    orchestrator = workers.json()["orchestrator"]
    assert orchestrator["active_target"] == "rtl-gen"
    assert orchestrator["active_corr"] == "corr_alt"


def test_workers_trace_reads_request_workspace_root(tmp_path: Path, monkeypatch) -> None:
    import urllib.request

    import src.atlas_ui as atlas_ui

    jobs = importlib.import_module("atlas_api_jobs")
    trace = importlib.import_module("core.orchestrator_trace")
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setenv("ATLAS_EXEC_MODE", "orchestrator")
    monkeypatch.setenv("ATLAS_ORCHESTRATOR_MODE", "1")
    monkeypatch.setenv("ATLAS_SINGLE_MAIN_LOOP", "0")
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "SOURCE_ROOT", tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    def fake_urlopen(req, timeout=None):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "status": "ok",
            "workflow": "rtl-gen",
            "model": "gpt-5.3-codex",
            "owner": "u",
        }).encode("utf-8")
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        return mock_resp

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    with jobs._jobs_lock:
        jobs._jobs.clear()

    global_corr = trace.record_trace(
        "pl330",
        lens="interaction",
        actor="ssot-gen-worker",
        kind="http_recv",
        project_root=tmp_path,
        session="u/default/pl330/ssot-gen",
    )
    alt_corr = trace.record_trace(
        "pl330",
        lens="interaction",
        actor="rtl-gen-worker",
        kind="http_recv",
        project_root=tmp_path / "u" / "alt",
        session="u/alt/pl330/rtl-gen",
    )

    client = TestClient(atlas_ui.create_app())
    reg = client.post("/api/auth/register", json={"username": "u", "password": "pw"})
    assert reg.status_code == 200, reg.text

    trace_resp = client.get("/api/orchestrator/trace?ip=pl330&workspace_session=alt")
    assert trace_resp.status_code == 200, trace_resp.text
    corr_ids = {event["corr"] for event in trace_resp.json()["events"]}
    assert corr_ids == {alt_corr}
    assert global_corr not in corr_ids

    workers_resp = client.get("/api/orchestrator/workers?ip=pl330&workspace_session=alt")
    assert workers_resp.status_code == 200, workers_resp.text
    assert workers_resp.json()["orchestrator"]["active_target"] == "rtl-gen"


def test_trace_workspace_scope_rejects_same_user_legacy_session_shape(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import src.atlas_ui as atlas_ui

    trace = importlib.import_module("core.orchestrator_trace")
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setenv("ATLAS_EXEC_MODE", "orchestrator")
    monkeypatch.setenv("ATLAS_ORCHESTRATOR_MODE", "1")
    monkeypatch.setenv("ATLAS_SINGLE_MAIN_LOOP", "0")
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "SOURCE_ROOT", tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    legacy_corr = trace.record_trace(
        "pl330",
        lens="interaction",
        actor="ssot-gen-worker",
        kind="http_recv",
        project_root=tmp_path / "u" / "alt",
        session="u/pl330/ssot-gen",
    )
    scoped_corr = trace.record_trace(
        "pl330",
        lens="interaction",
        actor="rtl-gen-worker",
        kind="http_recv",
        project_root=tmp_path / "u" / "alt",
        session="u/alt/pl330/rtl-gen",
    )

    client = TestClient(atlas_ui.create_app())
    reg = client.post("/api/auth/register", json={"username": "u", "password": "pw"})
    assert reg.status_code == 200, reg.text

    trace_resp = client.get("/api/orchestrator/trace?ip=pl330&workspace_session=alt")
    assert trace_resp.status_code == 200, trace_resp.text
    corr_ids = {event["corr"] for event in trace_resp.json()["events"]}
    assert corr_ids == {scoped_corr}
    assert legacy_corr not in corr_ids


def test_orchestrator_trace_rejects_path_shaped_ip(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import src.atlas_ui as atlas_ui

    trace = importlib.import_module("core.orchestrator_trace")
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setenv("ATLAS_EXEC_MODE", "orchestrator")
    monkeypatch.setenv("ATLAS_ORCHESTRATOR_MODE", "1")
    monkeypatch.setenv("ATLAS_SINGLE_MAIN_LOOP", "0")
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "SOURCE_ROOT", tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    corr = trace.record_trace(
        "outside",
        lens="interaction",
        actor="rtl-gen-worker",
        kind="http_recv",
        project_root=tmp_path / "u",
        session="u/default/pl330/rtl-gen",
    )

    client = TestClient(atlas_ui.create_app())
    reg = client.post("/api/auth/register", json={"username": "u", "password": "pw"})
    assert reg.status_code == 200, reg.text

    trace_resp = client.get(
        "/api/orchestrator/trace",
        params={"ip": "../outside", "workspace_session": "default"},
    )
    clear_resp = client.delete(
        "/api/orchestrator/trace",
        params={"ip": "../outside", "workspace_session": "default"},
    )

    assert trace_resp.status_code == 400, trace_resp.text
    assert clear_resp.status_code == 400, clear_resp.text
    outside_events = trace.read_trace("outside", project_root=tmp_path / "u")
    assert {event["corr"] for event in outside_events} == {corr}


def test_orchestrator_trace_delete_requires_auth_and_scopes_to_user_workspace(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import src.atlas_ui as atlas_ui

    atlas_db = importlib.import_module("core.atlas_db")
    trace = importlib.import_module("core.orchestrator_trace")
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setenv("ATLAS_EXEC_MODE", "orchestrator")
    monkeypatch.setenv("ATLAS_ORCHESTRATOR_MODE", "1")
    monkeypatch.setenv("ATLAS_SINGLE_MAIN_LOOP", "0")
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "SOURCE_ROOT", tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    trace.record_trace(
        "pl330",
        lens="interaction",
        actor="rtl-gen-worker",
        kind="http_recv",
        project_root=tmp_path / "owner" / "default",
        session="owner/default/pl330/rtl-gen",
    )

    client = TestClient(atlas_ui.create_app())
    unauth = client.delete("/api/orchestrator/trace?ip=pl330")
    assert unauth.status_code == 401, unauth.text

    owner_reg = client.post("/api/auth/register", json={"username": "owner", "password": "pw"})
    assert owner_reg.status_code == 200, owner_reg.text
    with atlas_db.AtlasDB(str(tmp_path / "atlas.db")) as db:
        owner = db.get_user_by_username("owner")
        assert owner is not None
        workspace = db.upsert_workspace(
            "default",
            owner_user_id=str(owner["id"]),
            local_path=str(tmp_path / "owner" / "default"),
        )
        ip_row = db.upsert_ip_block(str(workspace["id"]), "pl330")
        db.start_workflow_run(
            session_id="owner/default/pl330/rtl-gen",
            workspace_id=str(workspace["id"]),
            ip_id=str(ip_row["id"]),
            workflow="rtl-gen",
        )

    other_reg = client.post("/api/auth/register", json={"username": "other", "password": "pw"})
    assert other_reg.status_code == 200, other_reg.text
    other_clear = client.delete("/api/orchestrator/trace?ip=pl330")
    assert other_clear.status_code == 200, other_clear.text
    assert trace.read_trace("pl330", project_root=tmp_path / "owner" / "default")

    owner_login = client.post("/api/auth/login", json={"username": "owner", "password": "pw"})
    assert owner_login.status_code == 200, owner_login.text
    allowed = client.delete("/api/orchestrator/trace?ip=pl330")
    assert allowed.status_code == 200, allowed.text
    assert allowed.json()["cleared"] is True
    assert trace.read_trace("pl330", project_root=tmp_path / "owner" / "default") == []


def test_trace_get_rejects_traversal_ip_before_filesystem_read(tmp_path: Path, monkeypatch) -> None:
    trace = importlib.import_module("core.orchestrator_trace")
    client = _authenticated_trace_client(tmp_path, monkeypatch)

    trace.record_trace(
        "../alt/pl330",
        lens="interaction",
        actor="rtl-gen-worker",
        kind="http_recv",
        project_root=tmp_path / "u" / "default",
        session="u/default/pl330/rtl-gen",
    )

    resp = client.get("/api/orchestrator/trace", params={"ip": "../alt/pl330"})

    assert resp.status_code == 400, resp.text


def test_trace_clear_requires_login_when_multi_user_enabled(tmp_path: Path, monkeypatch) -> None:
    import src.atlas_ui as atlas_ui

    trace = importlib.import_module("core.orchestrator_trace")
    _configure_trace_app(tmp_path, monkeypatch)
    trace.record_trace(
        "pl330",
        lens="interaction",
        actor="rtl-gen-worker",
        kind="http_recv",
        project_root=tmp_path,
        session="u/default/pl330/rtl-gen",
    )
    trace_path = tmp_path / "pl330" / "orchestrator" / "trace.jsonl"
    assert trace_path.is_file()
    client = TestClient(atlas_ui.create_app())

    resp = client.delete("/api/orchestrator/trace", params={"ip": "pl330"})

    assert resp.status_code == 401, resp.text
    assert trace_path.is_file()


def test_trace_clear_scopes_same_ip_name_to_requesting_user_workspace(tmp_path: Path, monkeypatch) -> None:
    import src.atlas_ui as atlas_ui

    atlas_db_mod = importlib.import_module("core.atlas_db")
    trace = importlib.import_module("core.orchestrator_trace")
    _configure_trace_app(tmp_path, monkeypatch)
    client = TestClient(atlas_ui.create_app())
    reg_bob = client.post("/api/auth/register", json={"username": "bob", "password": "pw"})
    assert reg_bob.status_code == 200, reg_bob.text
    trace.record_trace(
        "pl330",
        lens="interaction",
        actor="rtl-gen-worker",
        kind="http_recv",
        project_root=tmp_path / "bob" / "default",
        session="bob/default/pl330/rtl-gen",
    )
    with atlas_db_mod.AtlasDB(str(tmp_path / "atlas.db")) as db:
        bob = db.get_user_by_username("bob")
        assert bob is not None
        workspace = db.upsert_workspace(
            "default",
            owner_user_id=str(bob["id"]),
            local_path=str(tmp_path / "bob" / "default"),
        )
        ip_row = db.upsert_ip_block(
            workspace["id"],
            "pl330",
            ssot_path="pl330/yaml/pl330.ssot.yaml",
        )
        db.start_workflow_run(
            workspace_id=workspace["id"],
            ip_id=ip_row["id"],
            workflow="rtl-gen",
        )
    reg_alice = client.post("/api/auth/register", json={"username": "alice", "password": "pw"})
    assert reg_alice.status_code == 200, reg_alice.text

    resp = client.delete("/api/orchestrator/trace", params={"ip": "pl330"})

    assert resp.status_code == 200, resp.text
    assert trace.read_trace("pl330", project_root=tmp_path / "bob" / "default")


def test_trace_clear_rejects_traversal_ip_before_unlink(tmp_path: Path, monkeypatch) -> None:
    trace = importlib.import_module("core.orchestrator_trace")
    client = _authenticated_trace_client(tmp_path, monkeypatch)
    trace.record_trace(
        "../alt/pl330",
        lens="interaction",
        actor="rtl-gen-worker",
        kind="http_recv",
        project_root=tmp_path / "u" / "default",
        session="u/default/pl330/rtl-gen",
    )
    trace_path = tmp_path / "u" / "alt" / "pl330" / "orchestrator" / "trace.jsonl"
    assert trace_path.is_file()

    resp = client.delete("/api/orchestrator/trace", params={"ip": "../alt/pl330"})

    assert resp.status_code == 400, resp.text
    assert trace_path.is_file()
