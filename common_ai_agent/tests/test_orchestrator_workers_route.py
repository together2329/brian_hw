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


class _JsonResponse:
    def __init__(self, body: dict):
        self._body = body

    def read(self):
        return json.dumps(self._body).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


def _clear_worker_url_env(monkeypatch) -> None:
    for wf in _EXPECTED_WORKFLOWS:
        suffix = wf.upper().replace("-", "_")
        for key in (
            f"ATLAS_WORKER_URL_{suffix}",
            f"ATLAS_{suffix}_WORKER_URL",
            f"WORKER_URL_{suffix}",
        ):
            monkeypatch.delenv(key, raising=False)
    monkeypatch.delenv("WORKER_URL_DEFAULT", raising=False)


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


def test_workers_route_uses_request_user_worker_url_when_idle(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import urllib.request

    import atlas_api_jobs as jobs

    _clear_worker_url_env(monkeypatch)
    monkeypatch.setenv("ATLAS_WORKFLOW_WORKER_PER_USER", "1")
    monkeypatch.setenv("ATLAS_EXEC_MODE", "orchestrator")
    monkeypatch.setenv("ATLAS_SINGLE_MAIN_LOOP", "0")
    monkeypatch.setenv("ATLAS_WORKFLOW_WORKER_PORT_BASE", "6000")
    monkeypatch.setenv("ATLAS_WORKFLOW_WORKER_PORT_SPAN", "200")

    with jobs._jobs_lock:
        jobs._jobs.clear()
    jobs._SESSION_WORKER_PORTS.clear()
    jobs._SESSION_WORKER_KEYS_BY_PORT.clear()

    default_rtl_url = "http://127.0.0.1:5623/health"
    probed_urls: list[str] = []

    def _fake_urlopen(req, timeout=None):
        url = getattr(req, "full_url", str(req))
        probed_urls.append(url)
        if url == default_rtl_url:
            return _JsonResponse({
                "status": "ok",
                "workflow": "rtl-gen",
                "owner": "other-user",
            })
        return _JsonResponse({"status": "unreachable"})

    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen)

    client = _make_client(tmp_path, monkeypatch)
    # _make_client disables multi-user worker processes for its legacy tests;
    # this test intentionally enables the production per-user path after app
    # construction because the route reads the env at request time.
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "1")

    resp = client.get("/api/orchestrator/workers?ip=ip_a")
    assert resp.status_code == 200, resp.text

    rtl = next(item for item in resp.json()["workers"] if item["workflow"] == "rtl-gen")
    assert rtl["url"] != "http://127.0.0.1:5623"
    assert rtl["status"] == "unreachable"
    assert default_rtl_url not in probed_urls

    jobs._SESSION_WORKER_PORTS.clear()
    jobs._SESSION_WORKER_KEYS_BY_PORT.clear()


def test_workers_route_masks_health_from_other_owner(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import urllib.request

    import atlas_api_jobs as jobs

    _clear_worker_url_env(monkeypatch)
    monkeypatch.setenv("ATLAS_WORKFLOW_WORKER_PER_USER", "1")
    monkeypatch.setenv("ATLAS_EXEC_MODE", "orchestrator")
    monkeypatch.setenv("ATLAS_SINGLE_MAIN_LOOP", "0")
    monkeypatch.setenv("ATLAS_WORKFLOW_WORKER_PORT_BASE", "6200")
    monkeypatch.setenv("ATLAS_WORKFLOW_WORKER_PORT_SPAN", "200")

    with jobs._jobs_lock:
        jobs._jobs.clear()
    jobs._SESSION_WORKER_PORTS.clear()
    jobs._SESSION_WORKER_KEYS_BY_PORT.clear()

    def _fake_urlopen(req, timeout=None):
        return _JsonResponse({
            "status": "ok",
            "workflow": "rtl-gen",
            "owner": "other-user",
            "running": [{"run_id": "foreign-run"}],
            "runs": 1,
        })

    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen)

    client = _make_client(tmp_path, monkeypatch)
    # _make_client disables multi-user worker processes for its legacy tests;
    # this route should still mask foreign health once the production
    # per-user worker path is enabled.
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "1")

    resp = client.get("/api/orchestrator/workers?ip=ip_a")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    rtl = next(item for item in body["workers"] if item["workflow"] == "rtl-gen")
    assert rtl["status"] == "unreachable"
    assert rtl["health_status"] == "unreachable"
    assert rtl["active_count"] == 0
    assert "other-user" not in json.dumps(body)
    assert "foreign-run" not in json.dumps(body)

    jobs._SESSION_WORKER_PORTS.clear()
    jobs._SESSION_WORKER_KEYS_BY_PORT.clear()


def test_multiuser_dispatch_uses_separate_worker_process_urls_per_user(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import urllib.request

    import atlas_api_jobs as jobs

    _clear_worker_url_env(monkeypatch)
    monkeypatch.setenv("ATLAS_WORKFLOW_WORKER_PER_USER", "1")
    monkeypatch.setenv("ATLAS_LAZY_WORKERS", "0")
    monkeypatch.setenv("ATLAS_EXEC_MODE", "orchestrator")
    monkeypatch.setenv("ATLAS_SINGLE_MAIN_LOOP", "0")
    monkeypatch.setenv("ATLAS_WORKFLOW_WORKER_PORT_BASE", "5800")
    monkeypatch.setenv("ATLAS_WORKFLOW_WORKER_PORT_SPAN", "200")

    with jobs._jobs_lock:
        jobs._jobs.clear()
    jobs._SESSION_WORKER_PORTS.clear()
    jobs._SESSION_WORKER_KEYS_BY_PORT.clear()

    for ip in ("ip_a", "ip_b"):
        (tmp_path / ip).mkdir(parents=True)

    run_calls: list[dict] = []

    def _fake_urlopen(req, timeout=None):
        url = getattr(req, "full_url", str(req))
        if url.endswith("/run"):
            payload = json.loads((getattr(req, "data", b"") or b"{}").decode("utf-8"))
            run_calls.append({"url": url, "payload": payload})
            return _JsonResponse({"run_id": f"run_{len(run_calls)}"})
        if url.endswith("/health"):
            base = url.rsplit("/health", 1)[0]
            owner = ""
            for item in run_calls:
                if str(item["url"]).startswith(base):
                    owner = str(item["payload"].get("session") or "").split("/", 1)[0]
                    break
            return _JsonResponse({
                "status": "ok",
                "workflow": "rtl-gen",
                "model": "gpt-5.3-codex",
                "owner": owner,
            })
        if "/status/" in url:
            return _JsonResponse({"status": "running"})
        return _JsonResponse({"status": "ok"})

    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen)

    client = _make_client(tmp_path, monkeypatch)
    first = client.post("/api/job/dispatch", json={
        "workflow": "rtl-gen",
        "ip": "ip_a",
        "exec_mode": "orchestrator",
    })
    assert first.status_code == 200, first.text

    reg_v = client.post("/api/auth/register", json={"username": "v", "password": "pw"})
    assert reg_v.status_code == 200, reg_v.text
    second = client.post("/api/job/dispatch", json={
        "workflow": "rtl-gen",
        "ip": "ip_b",
        "exec_mode": "orchestrator",
    })
    assert second.status_code == 200, second.text

    first_body = first.json()
    second_body = second.json()
    assert first_body["status"] == "running"
    assert second_body["status"] == "running"
    assert first_body["worker"] != second_body["worker"]
    assert first_body["worker"] != "http://127.0.0.1:5623"
    assert second_body["worker"] != "http://127.0.0.1:5623"
    assert len(run_calls) == 2
    assert run_calls[0]["payload"]["session"].startswith("u/ip_a/")
    assert run_calls[1]["payload"]["session"].startswith("v/ip_b/")

    workers = client.get("/api/orchestrator/workers?ip=ip_b")
    assert workers.status_code == 200, workers.text
    rtl = next(item for item in workers.json()["workers"] if item["workflow"] == "rtl-gen")
    assert rtl["url"] == second_body["worker"]
    assert rtl["running_count"] == 1
    assert [item["job_id"] for item in rtl["running"]] == [second_body["job_id"]]

    with jobs._jobs_lock:
        jobs._jobs.clear()
    jobs._SESSION_WORKER_PORTS.clear()
    jobs._SESSION_WORKER_KEYS_BY_PORT.clear()


def test_same_user_same_workflow_queues_on_one_worker_process(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import urllib.request

    import atlas_api_jobs as jobs

    _clear_worker_url_env(monkeypatch)
    monkeypatch.setenv("ATLAS_WORKFLOW_WORKER_PER_USER", "1")
    monkeypatch.setenv("ATLAS_LAZY_WORKERS", "0")
    monkeypatch.setenv("ATLAS_EXEC_MODE", "orchestrator")
    monkeypatch.setenv("ATLAS_SINGLE_MAIN_LOOP", "0")
    monkeypatch.setenv("ATLAS_WORKFLOW_WORKER_PORT_BASE", "5900")
    monkeypatch.setenv("ATLAS_WORKFLOW_WORKER_PORT_SPAN", "200")

    with jobs._jobs_lock:
        jobs._jobs.clear()
    jobs._SESSION_WORKER_PORTS.clear()
    jobs._SESSION_WORKER_KEYS_BY_PORT.clear()

    for ip in ("ip_a", "ip_b"):
        (tmp_path / ip).mkdir(parents=True)

    run_calls: list[dict] = []

    def _fake_urlopen(req, timeout=None):
        url = getattr(req, "full_url", str(req))
        if url.endswith("/run"):
            payload = json.loads((getattr(req, "data", b"") or b"{}").decode("utf-8"))
            run_calls.append({"url": url, "payload": payload})
            return _JsonResponse({"run_id": f"run_{len(run_calls)}"})
        if url.endswith("/health"):
            return _JsonResponse({
                "status": "ok",
                "workflow": "rtl-gen",
                "model": "gpt-5.3-codex",
                "owner": "u",
            })
        if "/status/" in url:
            return _JsonResponse({"status": "running"})
        return _JsonResponse({"status": "ok"})

    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen)

    client = _make_client(tmp_path, monkeypatch)
    first = client.post("/api/job/dispatch", json={
        "workflow": "rtl-gen",
        "ip": "ip_a",
        "exec_mode": "orchestrator",
    })
    second = client.post("/api/job/dispatch", json={
        "workflow": "rtl-gen",
        "ip": "ip_b",
        "exec_mode": "orchestrator",
    })
    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text

    first_body = first.json()
    second_body = second.json()
    assert first_body["worker"] == second_body["worker"]
    assert first_body["status"] == "running"
    assert second_body["status"] == "queued"
    assert second_body["run_id"] == ""
    assert len(run_calls) == 1

    with jobs._jobs_lock:
        jobs._jobs.clear()
    jobs._SESSION_WORKER_PORTS.clear()
    jobs._SESSION_WORKER_KEYS_BY_PORT.clear()
