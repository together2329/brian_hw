from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

_EXPECTED_WORKFLOWS = [
    "ssot-gen", "fl-model-gen", "rtl-gen", "lint", "tb-gen",
    "sim", "coverage", "sim_debug", "contract-reflection", "syn", "sta", "pnr", "sta-post",
]


@pytest.fixture(autouse=True)
def _isolate_worker_route_state(monkeypatch):
    # These tests assert explicit worker-routing modes. Do not let a
    # developer shell's production env leak into the route behavior.
    monkeypatch.setenv("ATLAS_WORKER_TRANSPORT", "http")
    monkeypatch.delenv("ATLAS_WORKFLOW_WORKER_PER_USER", raising=False)
    monkeypatch.delenv("ATLAS_WORKFLOW_WORKER_PER_SESSION", raising=False)
    monkeypatch.delenv("ATLAS_LAZY_WORKERS", raising=False)
    monkeypatch.delenv("ATLAS_WORKER_LAZY_START", raising=False)
    try:
        import atlas_api_jobs as jobs
    except Exception:
        jobs = None
    if jobs is not None:
        with jobs._jobs_lock:
            jobs._jobs.clear()
        jobs._SESSION_WORKER_PORTS.clear()
        jobs._SESSION_WORKER_KEYS_BY_PORT.clear()
        with jobs._HEALTH_CACHE_LOCK:
            jobs._HEALTH_CACHE.clear()
    yield
    if jobs is not None:
        with jobs._jobs_lock:
            jobs._jobs.clear()
        jobs._SESSION_WORKER_PORTS.clear()
        jobs._SESSION_WORKER_KEYS_BY_PORT.clear()
        with jobs._HEALTH_CACHE_LOCK:
            jobs._HEALTH_CACHE.clear()


def _make_client(tmp_path: Path, monkeypatch) -> TestClient:
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setenv("ATLAS_EXEC_MODE", "orchestrator")
    monkeypatch.setenv("ATLAS_ORCHESTRATOR_MODE", "1")
    monkeypatch.setenv("ATLAS_SINGLE_MAIN_LOOP", "0")
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "SOURCE_ROOT", tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    client = TestClient(atlas_ui.create_app())
    monkeypatch.setenv("ATLAS_EXEC_MODE", "orchestrator")
    monkeypatch.setenv("ATLAS_ORCHESTRATOR_MODE", "1")
    monkeypatch.setenv("ATLAS_SINGLE_MAIN_LOOP", "0")
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


def test_workers_route_returns_13_workers(tmp_path: Path, monkeypatch) -> None:
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
    assert len(workers) == 13, f"expected 13 workers, got {len(workers)}: {[w['workflow'] for w in workers]}"

    workflow_names = {w["workflow"] for w in workers}
    assert "goal-audit" not in workflow_names, "dead goal-audit entry must not appear"
    assert workflow_names == set(_EXPECTED_WORKFLOWS), (
        f"workflow mismatch: got {workflow_names}"
    )


def test_workers_route_active_only_skips_idle_worker_fanout(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import urllib.request

    import atlas_api_jobs as jobs

    probed_urls: list[str] = []

    def _fake_urlopen(req, timeout=None):
        probed_urls.append(getattr(req, "full_url", str(req)))
        return _JsonResponse({"status": "ok"})

    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen)
    with jobs._jobs_lock:
        jobs._jobs.clear()
    with jobs._HEALTH_CACHE_LOCK:
        jobs._HEALTH_CACHE.clear()

    client = _make_client(tmp_path, monkeypatch)
    resp = client.get("/api/orchestrator/workers?ip=pl330&active_only=1")
    assert resp.status_code == 200, resp.text

    data = resp.json()
    assert data["active_only"] is True
    assert data["count"] == 0
    assert data["workers"] == []
    assert probed_urls == []


def test_workers_route_lazy_idle_skips_unspawned_worker_probes(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import urllib.request

    import atlas_api_jobs as jobs

    probed_urls: list[str] = []

    def _fake_urlopen(req, timeout=None):
        probed_urls.append(getattr(req, "full_url", str(req)))
        return _JsonResponse({"status": "ok"})

    monkeypatch.setenv("ATLAS_LAZY_WORKERS", "1")
    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen)
    with jobs._jobs_lock:
        jobs._jobs.clear()
    with jobs._LAZY_WORKER_LOCK:
        jobs._LAZY_WORKER_PROCS.clear()
    with jobs._HEALTH_CACHE_LOCK:
        jobs._HEALTH_CACHE.clear()

    client = _make_client(tmp_path, monkeypatch)
    resp = client.get("/api/orchestrator/workers?ip=pl330")
    assert resp.status_code == 200, resp.text

    data = resp.json()
    assert data["count"] == 13
    assert all(worker["status"] == "unreachable" for worker in data["workers"])
    assert all(worker["error"] == "lazy worker not spawned" for worker in data["workers"])
    assert probed_urls == []


def test_workers_route_active_only_probes_visible_active_workflows_only(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import urllib.request

    import atlas_api_jobs as jobs

    probed_urls: list[str] = []

    def _fake_urlopen(req, timeout=None):
        probed_urls.append(getattr(req, "full_url", str(req)))
        return _JsonResponse({
            "status": "ok",
            "workflow": "rtl-gen",
            "model": "gpt-5.3-codex",
        })

    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen)
    with jobs._jobs_lock:
        jobs._jobs.clear()
        jobs._jobs["active-rtl"] = {
            "job_id": "active-rtl",
            "run_id": "run_active",
            "workflow": "rtl-gen",
            "stage_id": "rtl",
            "status": "running",
            "ip": "pl330",
            "user_id": "u",
            "model": "gpt-5.3-codex",
            "project_root": str(tmp_path / "u" / "default"),
            "session": "u/default/pl330/rtl-gen",
            "started_at": 1.0,
        }
    with jobs._HEALTH_CACHE_LOCK:
        jobs._HEALTH_CACHE.clear()

    client = _make_client(tmp_path, monkeypatch)
    try:
        resp = client.get("/api/orchestrator/workers?ip=pl330&active_only=1")
        assert resp.status_code == 200, resp.text

        workers = resp.json()["workers"]
        assert [w["workflow"] for w in workers] == ["rtl-gen"]
        assert workers[0]["running_count"] == 1
        assert [item["job_id"] for item in workers[0]["running"]] == ["active-rtl"]
        assert len(probed_urls) == 1
        assert probed_urls[0].endswith("/health")
    finally:
        with jobs._jobs_lock:
            jobs._jobs.clear()
        with jobs._HEALTH_CACHE_LOCK:
            jobs._HEALTH_CACHE.clear()


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
            "project_root": str(tmp_path / "u" / "default"),
            "session": "u/default/pl330/rtl-gen",
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
            "project_root": str(tmp_path / "other" / "default"),
            "session": "other/default/pl330/rtl-gen",
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
    monkeypatch.setenv("WORKER_URL_RTL_GEN", "http://127.0.0.1:5623")
    monkeypatch.setenv("WORKER_URL_DEFAULT", "http://127.0.0.1:5601")

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
    assert rtl["url"] != "http://127.0.0.1:5601"
    assert rtl["status"] == "unreachable"
    assert default_rtl_url not in probed_urls

    jobs._SESSION_WORKER_PORTS.clear()
    jobs._SESSION_WORKER_KEYS_BY_PORT.clear()


def test_same_user_same_session_workflow_reuses_one_worker_process(
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
    monkeypatch.setenv("ATLAS_WORKFLOW_WORKER_PORT_BASE", "6100")
    monkeypatch.setenv("ATLAS_WORKFLOW_WORKER_PORT_SPAN", "200")

    with jobs._jobs_lock:
        jobs._jobs.clear()
    jobs._SESSION_WORKER_PORTS.clear()
    jobs._SESSION_WORKER_KEYS_BY_PORT.clear()

    (tmp_path / "ip_a").mkdir(parents=True)

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
        "ip": "ip_a",
        "exec_mode": "orchestrator",
    })
    assert first.status_code == 200, first.text
    assert second.status_code == 200, second.text

    first_body = first.json()
    second_body = second.json()
    assert first_body["worker"] == second_body["worker"]
    assert first_body["status"] == "running"
    assert second_body["status"] == "already_running"
    assert second_body["run_id"] == first_body["run_id"]
    assert len(run_calls) == 1
    assert run_calls[0]["payload"]["session"].startswith("u/default/ip_a/")

    with jobs._jobs_lock:
        jobs._jobs.clear()
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


def test_workers_route_restricts_runtime_snapshot_for_non_admin(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import urllib.request

    import atlas_api_jobs as jobs

    def _fake_urlopen(req, timeout=None):
        return _JsonResponse({"status": "unreachable"})

    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen)
    client = _make_client(tmp_path, monkeypatch)

    with jobs._jobs_lock:
        jobs._jobs.clear()
        jobs._jobs["foreign"] = {
            "job_id": "foreign",
            "run_id": "foreign-run",
            "workflow": "rtl-gen",
            "stage_id": "rtl",
            "status": "running",
            "ip": "pl330",
            "user_id": "bob",
            "db_user_id": "bob-db",
            "worker_transport": "ipc",
            "worker": "ipc://bob_partition/rtl-gen",
            "session": "bob/default/pl330/rtl-gen",
            "project_root": str(tmp_path / "bob" / "default"),
            "prompt": "bob secret prompt",
            "started_at": 1.0,
        }

    try:
        resp = client.get("/api/orchestrator/workers?ip=pl330")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        dumped = json.dumps(body)
        assert body["runtime"] == {"transport": "http", "restricted": True}
        assert "bob secret prompt" not in dumped
        assert "bob/default/pl330/rtl-gen" not in dumped
        assert "ipc://bob_partition" not in dumped
        assert "bob-db" not in dumped
    finally:
        with jobs._jobs_lock:
            jobs._jobs.clear()


def test_workers_route_filters_admin_runtime_snapshot_by_workspace_session(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import urllib.request

    import atlas_api_jobs as jobs

    class FakeProc:
        def __init__(self, pid: int) -> None:
            self.pid = pid

        def poll(self) -> None:
            return None

    def _fake_urlopen(req, timeout=None):
        return _JsonResponse({"status": "unreachable"})

    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen)
    monkeypatch.setenv("ATLAS_ADMIN_USERS", "u")
    client = _make_client(tmp_path, monkeypatch)

    with jobs._jobs_lock:
        jobs._jobs.clear()
        jobs._jobs["visible"] = {
            "job_id": "visible",
            "run_id": "visible-run",
            "workflow": "rtl-gen",
            "stage_id": "rtl",
            "status": "running",
            "ip": "pl330",
            "user_id": "u",
            "db_user_id": "u-db",
            "worker_transport": "ipc",
            "worker": "ipc://u_alt_partition/rtl-gen",
            "session": "u/alt/pl330/rtl-gen",
            "project_root": str(tmp_path / "u" / "alt"),
            "prompt": "u alt prompt",
            "started_at": 2.0,
        }
        jobs._jobs["foreign"] = {
            "job_id": "foreign",
            "run_id": "foreign-run",
            "workflow": "rtl-gen",
            "stage_id": "rtl",
            "status": "running",
            "ip": "pl330",
            "user_id": "bob",
            "db_user_id": "bob-db",
            "worker_transport": "ipc",
            "worker": "ipc://bob_partition/rtl-gen",
            "session": "bob/default/pl330/rtl-gen",
            "project_root": str(tmp_path / "bob" / "default"),
            "prompt": "bob secret prompt",
            "started_at": 1.0,
        }
    with jobs._IPC_WORKER_LOCK:
        jobs._IPC_WORKER_PROCS.clear()
        jobs._IPC_WORKER_PROCS["visible-run"] = FakeProc(111)
        jobs._IPC_WORKER_PROCS["foreign-run"] = FakeProc(222)

    try:
        resp = client.get("/api/orchestrator/workers?ip=pl330&workspace_session=alt")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        dumped = json.dumps(body)
        runtime_jobs = body["runtime"]["ipc"]["jobs"]
        assert {job["job_id"] for job in runtime_jobs} == {"visible"}
        runtime_processes = body["runtime"]["ipc"]["processes"]
        assert {proc["run_id"] for proc in runtime_processes} == {"visible-run"}
        assert {proc["pid"] for proc in runtime_processes} == {111}
        assert "bob secret prompt" not in dumped
        assert "bob/default/pl330/rtl-gen" not in dumped
        assert "ipc://bob_partition" not in dumped
        assert "foreign-run" not in dumped
        assert "222" not in dumped
        assert "bob-db" not in dumped
    finally:
        with jobs._jobs_lock:
            jobs._jobs.clear()
        with jobs._IPC_WORKER_LOCK:
            jobs._IPC_WORKER_PROCS.clear()


def test_workers_route_admin_runtime_snapshot_filters_request_workspace(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import urllib.request

    import src.atlas_ui as atlas_ui
    import atlas_api_jobs as jobs

    def _fake_urlopen(req, timeout=None):
        return _JsonResponse({"status": "unreachable"})

    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setenv("ATLAS_EXEC_MODE", "orchestrator")
    monkeypatch.setenv("ATLAS_ORCHESTRATOR_MODE", "1")
    monkeypatch.setenv("ATLAS_SINGLE_MAIN_LOOP", "0")
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.setenv("ATLAS_ADMIN_AUTH_MODE", "db")
    monkeypatch.setenv("ATLAS_ADMIN_LOGIN_REQUIRED", "1")
    monkeypatch.setenv("ATLAS_ADMIN_USERS", "admin")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "SOURCE_ROOT", tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    client = TestClient(atlas_ui.create_app())
    reg = client.post("/api/auth/register", json={"username": "admin", "password": "1151"})
    assert reg.status_code == 200, reg.text
    assert reg.json()["user"]["role"] == "admin"

    with jobs._jobs_lock:
        jobs._jobs.clear()
        jobs._jobs["admin-job"] = {
            "job_id": "admin-job",
            "run_id": "admin-run",
            "workflow": "rtl-gen",
            "stage_id": "rtl",
            "status": "running",
            "ip": "pl330",
            "user_id": "admin",
            "db_user_id": reg.json()["user"]["id"],
            "worker_transport": "ipc",
            "worker": "ipc://admin_partition/rtl-gen",
            "session": "admin/default/pl330/rtl-gen",
            "project_root": str(tmp_path / "admin" / "default"),
            "prompt": "admin prompt",
            "started_at": 2.0,
        }
        jobs._jobs["foreign"] = {
            "job_id": "foreign",
            "run_id": "foreign-run",
            "workflow": "rtl-gen",
            "stage_id": "rtl",
            "status": "running",
            "ip": "pl330",
            "user_id": "bob",
            "db_user_id": "bob-db",
            "worker_transport": "ipc",
            "worker": "ipc://bob_partition/rtl-gen",
            "session": "bob/default/pl330/rtl-gen",
            "project_root": str(tmp_path / "bob" / "default"),
            "prompt": "bob secret prompt",
            "started_at": 1.0,
        }

    try:
        resp = client.get("/api/orchestrator/workers?ip=pl330")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        dumped = json.dumps(body)
        assert "admin-run" in dumped
        assert "bob secret prompt" not in dumped
        assert "bob/default/pl330/rtl-gen" not in dumped
        assert "ipc://bob_partition" not in dumped
        assert "bob-db" not in dumped
    finally:
        with jobs._jobs_lock:
            jobs._jobs.clear()


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
    assert run_calls[0]["payload"]["session"].startswith("u/default/ip_a/")
    assert run_calls[1]["payload"]["session"].startswith("v/default/ip_b/")

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


def test_multiuser_single_worker_dispatch_scopes_worker_urls_per_user(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import urllib.request

    import atlas_api_jobs as jobs

    _clear_worker_url_env(monkeypatch)
    monkeypatch.setenv("ATLAS_WORKFLOW_WORKER_PER_USER", "1")
    monkeypatch.setenv("ATLAS_LAZY_WORKERS", "0")
    monkeypatch.setenv("ATLAS_EXEC_MODE", "single-worker")
    monkeypatch.setenv("ATLAS_SINGLE_MAIN_LOOP", "0")
    monkeypatch.setenv("ATLAS_WORKFLOW_WORKER_PORT_BASE", "6000")
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
                "workflow": "ssot-gen",
                "model": "gpt-5.5",
                "owner": "",
            })
        if "/status/" in url:
            return _JsonResponse({"status": "running"})
        return _JsonResponse({"status": "ok"})

    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen)

    client = _make_client(tmp_path, monkeypatch)
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "1")
    first = client.post("/api/job/dispatch", json={
        "workflow": "ssot-gen",
        "ip": "ip_a",
        "exec_mode": "single-worker",
    })
    assert first.status_code == 200, first.text

    reg_v = client.post("/api/auth/register", json={"username": "v", "password": "pw"})
    assert reg_v.status_code == 200, reg_v.text
    second = client.post("/api/job/dispatch", json={
        "workflow": "ssot-gen",
        "ip": "ip_b",
        "exec_mode": "single-worker",
    })
    assert second.status_code == 200, second.text

    first_body = first.json()
    second_body = second.json()
    assert first_body["status"] == "running"
    assert second_body["status"] == "running"
    assert first_body["worker"] != second_body["worker"]
    assert first_body["worker"] != "http://127.0.0.1:5601"
    assert second_body["worker"] != "http://127.0.0.1:5601"
    assert len(run_calls) == 2
    assert run_calls[0]["payload"]["session"].startswith("u/default/ip_a/")
    assert run_calls[1]["payload"]["session"].startswith("v/default/ip_b/")

    with jobs._jobs_lock:
        jobs._jobs.clear()
    jobs._SESSION_WORKER_PORTS.clear()
    jobs._SESSION_WORKER_KEYS_BY_PORT.clear()


def test_same_user_different_sessions_use_separate_worker_processes(
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
    assert first_body["worker"] != second_body["worker"]
    assert first_body["status"] == "running"
    assert second_body["status"] == "running"
    assert second_body["run_id"] != ""
    assert len(run_calls) == 2
    assert run_calls[0]["payload"]["session"].startswith("u/default/ip_a/")
    assert run_calls[1]["payload"]["session"].startswith("u/default/ip_b/")

    with jobs._jobs_lock:
        jobs._jobs.clear()
    jobs._SESSION_WORKER_PORTS.clear()
    jobs._SESSION_WORKER_KEYS_BY_PORT.clear()


def test_workers_warm_route_uses_workspace_session_for_worker_jobs(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import atlas_api_jobs as jobs

    _clear_worker_url_env(monkeypatch)
    monkeypatch.setenv("ATLAS_WORKFLOW_WORKER_PER_USER", "1")
    monkeypatch.setenv("ATLAS_LAZY_WORKERS", "1")
    monkeypatch.setenv("ATLAS_WORKER_WARM_POOL", "1")
    monkeypatch.setenv("ATLAS_EXEC_MODE", "orchestrator")
    monkeypatch.setenv("ATLAS_SINGLE_MAIN_LOOP", "0")

    captured: list[dict[str, object]] = []

    def _capture(job: dict[str, object], *, reason: str = "", background: bool = True) -> dict[str, object]:
        captured.append(dict(job))
        return {
            "workflow": str(job.get("workflow") or ""),
            "worker": str(job.get("worker") or ""),
            "status": "scheduled",
        }

    monkeypatch.setattr(jobs, "_schedule_warm_worker", _capture)

    client = _make_client(tmp_path, monkeypatch)
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "1")
    resp = client.post("/api/orchestrator/workers/warm", json={
        "ip": "uart",
        "session_id": "u/alt/uart/rtl-gen",
        "workflow": "rtl-gen",
        "workflows": ["rtl-gen"],
    })

    assert resp.status_code == 200, resp.text
    assert resp.json()["workspace_session"] == "alt"
    assert [job["session"] for job in captured] == ["u/alt/uart/rtl-gen"]
    assert captured[0]["project_root"] == str(tmp_path / "u" / "alt")
    assert str(captured[0]["worker_partition"]).endswith("_u_alt_uart_rtl-gen")


@pytest.mark.parametrize("workspace_session", ["../bob", "/bob", "alt/child"])
def test_workers_warm_route_normalizes_path_like_workspace_session_to_default(
    tmp_path: Path,
    monkeypatch,
    workspace_session: str,
) -> None:
    import atlas_api_jobs as jobs

    _clear_worker_url_env(monkeypatch)
    monkeypatch.setenv("ATLAS_WORKFLOW_WORKER_PER_USER", "1")
    monkeypatch.setenv("ATLAS_LAZY_WORKERS", "1")
    monkeypatch.setenv("ATLAS_WORKER_WARM_POOL", "1")
    monkeypatch.setenv("ATLAS_EXEC_MODE", "orchestrator")
    monkeypatch.setenv("ATLAS_SINGLE_MAIN_LOOP", "0")

    captured: list[dict[str, object]] = []

    def _capture(job: dict[str, object], *, reason: str = "", background: bool = True) -> dict[str, object]:
        captured.append(dict(job))
        return {
            "workflow": str(job.get("workflow") or ""),
            "worker": str(job.get("worker") or ""),
            "status": "scheduled",
        }

    monkeypatch.setattr(jobs, "_schedule_warm_worker", _capture)

    client = _make_client(tmp_path, monkeypatch)
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "1")
    resp = client.post("/api/orchestrator/workers/warm", json={
        "ip": "uart",
        "workspace_session": workspace_session,
        "workflow": "rtl-gen",
        "workflows": ["rtl-gen"],
    })

    assert resp.status_code == 200, resp.text
    assert resp.json()["workspace_session"] == "default"
    assert [job["session"] for job in captured] == ["u/default/uart/rtl-gen"]
    assert captured[0]["project_root"] == str(tmp_path / "u" / "default")


def test_workers_warm_route_rejects_invalid_ip_before_scheduling(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import atlas_api_jobs as jobs

    _clear_worker_url_env(monkeypatch)
    monkeypatch.setenv("ATLAS_WORKFLOW_WORKER_PER_USER", "1")
    monkeypatch.setenv("ATLAS_LAZY_WORKERS", "1")
    monkeypatch.setenv("ATLAS_WORKER_WARM_POOL", "1")
    monkeypatch.setenv("ATLAS_EXEC_MODE", "orchestrator")
    monkeypatch.setenv("ATLAS_SINGLE_MAIN_LOOP", "0")

    captured: list[dict[str, object]] = []
    monkeypatch.setattr(jobs, "_schedule_warm_worker", lambda job, **_kwargs: captured.append(dict(job)))

    client = _make_client(tmp_path, monkeypatch)
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "1")
    resp = client.post("/api/orchestrator/workers/warm", json={
        "ip": "../outside",
        "workspace_session": "alt",
        "workflow": "rtl-gen",
        "workflows": ["rtl-gen"],
    })

    assert resp.status_code == 400, resp.text
    assert captured == []
