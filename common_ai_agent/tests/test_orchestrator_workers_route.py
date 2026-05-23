from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

_EXPECTED_WORKFLOWS = [
    "ssot-gen", "fl-model-gen", "rtl-gen", "lint", "tb-gen",
    "sim", "coverage", "sim_debug", "syn", "sta", "pnr", "sta-post",
]


def _make_client(tmp_path: Path, monkeypatch) -> TestClient:
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "SOURCE_ROOT", tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    client = TestClient(atlas_ui.create_app())
    reg = client.post("/api/auth/register", json={"username": "u", "password": "pw"})
    assert reg.status_code == 200, reg.text
    return client


def test_workers_route_returns_12_workers(tmp_path: Path, monkeypatch) -> None:
    # Stub urlopen so health probes don't block on real network.
    import urllib.request

    def _fake_urlopen(req, timeout=None):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"status": "unreachable"}'
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        return mock_resp

    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen)

    client = _make_client(tmp_path, monkeypatch)
    resp = client.get("/api/orchestrator/workers?ip=pl330")
    assert resp.status_code == 200, resp.text

    data = resp.json()
    assert "workers" in data, data

    workers = data["workers"]
    assert len(workers) == 12, f"expected 12 workers, got {len(workers)}: {[w['workflow'] for w in workers]}"

    workflow_names = {w["workflow"] for w in workers}
    assert "goal-audit" not in workflow_names, "dead goal-audit entry must not appear"
    assert workflow_names == set(_EXPECTED_WORKFLOWS), (
        f"workflow mismatch: got {workflow_names}"
    )


def test_workers_route_marks_workflow_and_model_mismatch(tmp_path: Path, monkeypatch) -> None:
    import urllib.request

    monkeypatch.setenv("WORKER_URL_RTL_GEN", "http://127.0.0.1:9988")
    monkeypatch.setenv("ATLAS_WORKER_MODEL_RTL_GEN", "gpt-5.3-codex")

    def _fake_urlopen(req, timeout=None):
        url = getattr(req, "full_url", str(req))
        body = {"status": "unreachable"}
        if "9988" in url:
            body = {"status": "ok", "workflow": "lint", "model": "glm-5.1"}
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(body).encode("utf-8")
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        return mock_resp

    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen)

    client = _make_client(tmp_path, monkeypatch)
    resp = client.get("/api/orchestrator/workers?ip=pl330")
    assert resp.status_code == 200, resp.text
    rtl = next(item for item in resp.json()["workers"] if item["workflow"] == "rtl-gen")
    assert rtl["status"] == "mismatch"
    assert rtl["workflow_mismatch"] is True
    assert rtl["model_mismatch"] is True
    assert rtl["bound_workflow"] == "lint"
    assert rtl["worker_health_model"] == "glm-5.1"


def test_workers_route_scopes_running_jobs_to_request_user(tmp_path: Path, monkeypatch) -> None:
    import urllib.request

    import atlas_api_jobs as jobs
    from core.atlas_db import AtlasDB

    def _fake_urlopen(req, timeout=None):
        url = getattr(req, "full_url", str(req))
        body = {
            "status": "ok",
            "runs": 2,
            "running": [{"run_id": "foreign-health-run"}],
            "running_models": ["private-model"],
        }
        if "5623" in url:
            body.update({"workflow": "rtl-gen", "model": "gpt-5.3-codex"})
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(body).encode("utf-8")
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        return mock_resp

    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen)

    client = _make_client(tmp_path, monkeypatch)
    login = client.post("/api/auth/login", json={"username": "u", "password": "pw"})
    assert login.status_code == 200, login.text
    with AtlasDB(tmp_path / "atlas.db") as db:
        user = db.get_user_by_username("u")
    assert user is not None

    with jobs._jobs_lock:
        jobs._jobs.clear()
        jobs._jobs["mine"] = {
            "job_id": "mine",
            "run_id": "run_mine",
            "workflow": "rtl-gen",
            "stage_id": "rtl",
            "status": "running",
            "ip": "pl330",
            "user_id": "u",
            "db_user_id": user["id"],
            "model": "gpt-5.3-codex",
            "session": "u/pl330/rtl-gen",
            "started_at": 2.0,
        }
        jobs._jobs["other"] = {
            "job_id": "other",
            "run_id": "run_other",
            "workflow": "rtl-gen",
            "stage_id": "rtl",
            "status": "running",
            "ip": "pl330",
            "user_id": "other",
            "db_user_id": "other-user-id",
            "model": "private-model",
            "session": "other/pl330/rtl-gen",
            "started_at": 3.0,
        }

    try:
        resp = client.get("/api/orchestrator/workers?ip=pl330")
        assert resp.status_code == 200, resp.text
        rtl = next(item for item in resp.json()["workers"] if item["workflow"] == "rtl-gen")
        assert rtl["running_count"] == 1
        assert [item["job_id"] for item in rtl["running"]] == ["mine"]
        assert rtl["worker_running_models"] == ["gpt-5.3-codex"]
        assert "foreign-health-run" not in json.dumps(rtl)
        assert "other" not in json.dumps(rtl)
        assert "private-model" not in json.dumps(rtl)
    finally:
        with jobs._jobs_lock:
            jobs._jobs.clear()
