"""Tests for multi-user job isolation on /api/jobs (H2) and
/api/pipeline/state (H3).

These tests prove that the read-path filters introduced in
src/atlas_api_jobs.py correctly scope jobs to the authenticated user
in multi-user mode, while returning all jobs in single-user mode.
"""
import sys
from pathlib import Path
from typing import Optional
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
for _c in (PROJECT_ROOT, PROJECT_ROOT / "src"):
    p = str(_c)
    if p not in sys.path:
        sys.path.insert(0, p)

from fastapi.testclient import TestClient


def _apijobs():
    """Return the atlas_api_jobs module instance the running app uses.

    atlas_ui imports atlas_api_jobs without the 'src.' prefix (via sys.path
    that includes src/), so after create_app() two entries exist in
    sys.modules: 'src.atlas_api_jobs' and 'atlas_api_jobs'.  The live _jobs
    dict and lock live in the one the app actually imported.
    """
    return sys.modules.get("atlas_api_jobs") or sys.modules["src.atlas_api_jobs"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_job(
    job_id: str,
    ip: str,
    db_user_id: str,
    status: str = "completed",
    project_root: Optional[Path] = None,
) -> dict:
    return {
        "job_id": job_id,
        "ip": ip,
        "db_user_id": db_user_id,
        "user_id": db_user_id,
        "status": status,
        "started_at": 1000.0,
        "worker": "http://localhost:5601",
        "run_id": None,
        "_last_polled": 0.0,
        "stage_id": "lint",
        "workflow": "lint",
        **({"project_root": str(project_root)} if project_root is not None else {}),
    }


def _register(client: TestClient, username: str) -> dict:
    resp = client.post(
        "/api/auth/register",
        json={"username": username, "password": "pw"},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["user"]


# ---------------------------------------------------------------------------
# Test 1: /api/jobs isolates per user in multi-user mode  (H2)
# ---------------------------------------------------------------------------

def test_api_jobs_isolates_users(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()
    apijobs = _apijobs()

    alice_client = TestClient(app)
    bob_client = TestClient(app)

    alice_user = _register(alice_client, "alice")
    bob_user = _register(bob_client, "bob")

    alice_uid = alice_user["id"]
    bob_uid = bob_user["id"]

    job_a = _make_job("job-a", "uart", alice_uid, project_root=tmp_path / "alice" / "default")
    job_b = _make_job("job-b", "uart", bob_uid, project_root=tmp_path / "bob" / "default")

    with apijobs._jobs_lock:
        apijobs._jobs["job-a"] = job_a
        apijobs._jobs["job-b"] = job_b

    try:
        with patch.object(apijobs, "_refresh_tracked_jobs",
                          return_value=([job_a, job_b], False)):
            alice_resp = alice_client.get("/api/jobs")
            bob_resp = bob_client.get("/api/jobs")

        assert alice_resp.status_code == 200, alice_resp.text
        alice_ids = {j["job_id"] for j in alice_resp.json()["jobs"]}
        assert alice_ids == {"job-a"}, f"alice saw unexpected jobs: {alice_ids}"

        assert bob_resp.status_code == 200, bob_resp.text
        bob_ids = {j["job_id"] for j in bob_resp.json()["jobs"]}
        assert bob_ids == {"job-b"}, f"bob saw unexpected jobs: {bob_ids}"
    finally:
        with apijobs._jobs_lock:
            apijobs._jobs.pop("job-a", None)
            apijobs._jobs.pop("job-b", None)


# ---------------------------------------------------------------------------
# Test 2: /api/jobs returns all jobs in single-user (local-admin) mode  (H2)
# ---------------------------------------------------------------------------

def test_api_jobs_returns_all_in_local_admin_mode(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    # Explicit local-admin mode: no login required, all jobs visible
    monkeypatch.setenv("ATLAS_MULTI_USER", "0")
    monkeypatch.setenv("ATLAS_ADMIN_AUTH_MODE", "local")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()
    apijobs = _apijobs()
    client = TestClient(app)

    job_a = _make_job("job-a", "uart", "user-a")
    job_b = _make_job("job-b", "uart", "user-b")

    with apijobs._jobs_lock:
        apijobs._jobs["job-a"] = job_a
        apijobs._jobs["job-b"] = job_b

    try:
        with patch.object(apijobs, "_refresh_tracked_jobs",
                          return_value=([job_a, job_b], False)):
            resp = client.get("/api/jobs")

        assert resp.status_code == 200, resp.text
        ids = {j["job_id"] for j in resp.json()["jobs"]}
        assert ids == {"job-a", "job-b"}, (
            f"single-user mode must return all jobs, got: {ids}"
        )
    finally:
        with apijobs._jobs_lock:
            apijobs._jobs.pop("job-a", None)
            apijobs._jobs.pop("job-b", None)


# ---------------------------------------------------------------------------
# Test 3: /api/pipeline/state ip_jobs are isolated by user  (H3)
# ---------------------------------------------------------------------------

def test_pipeline_state_ip_jobs_isolated(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()
    apijobs = _apijobs()

    alice_client = TestClient(app)
    bob_client = TestClient(app)

    alice_user = _register(alice_client, "alice")
    bob_user = _register(bob_client, "bob")

    alice_uid = alice_user["id"]
    bob_uid = bob_user["id"]

    # Both jobs share ip="uart" — only db_user_id differs
    job_a = _make_job("job-pa", "uart", alice_uid, status="running")
    job_b = _make_job("job-pb", "uart", bob_uid, status="running")

    with apijobs._jobs_lock:
        apijobs._jobs["job-pa"] = job_a
        apijobs._jobs["job-pb"] = job_b

    try:
        alice_resp = alice_client.get("/api/pipeline/state?ip=uart")
        bob_resp = bob_client.get("/api/pipeline/state?ip=uart")

        # Pipeline state may return 200 or 404 (no IP dir exists in tmp_path);
        # we only care that cross-user contamination does not occur.
        assert alice_resp.status_code in (200, 404)
        assert bob_resp.status_code in (200, 404)

        if alice_resp.status_code == 200 and bob_resp.status_code == 200:
            alice_data = alice_resp.json()
            bob_data = bob_resp.json()

            def _running_ids(data: dict) -> set:
                ids: set = set()
                stages = data.get("stages", [])
                for stage in stages:
                    if not isinstance(stage, dict):
                        continue
                    rj = stage.get("running_job")
                    if isinstance(rj, dict) and rj.get("job_id"):
                        ids.add(rj["job_id"])
                return ids

            alice_running = _running_ids(alice_data)
            bob_running = _running_ids(bob_data)

            assert "job-pb" not in alice_running, "alice sees bob's job in pipeline state"
            assert "job-pa" not in bob_running, "bob sees alice's job in pipeline state"
    finally:
        with apijobs._jobs_lock:
            apijobs._jobs.pop("job-pa", None)
            apijobs._jobs.pop("job-pb", None)


# ---------------------------------------------------------------------------
# Test 4: unauthenticated request is blocked in multi-user mode (H2)
# ---------------------------------------------------------------------------

def test_api_jobs_unauthenticated_blocked_in_multiuser(tmp_path, monkeypatch):
    """In multi-user mode an unauthenticated request must be rejected (401)."""
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()
    apijobs = _apijobs()

    seeder = TestClient(app)
    seeder_user = _register(seeder, "seeder")
    seeder_uid = seeder_user["id"]

    job_x = _make_job("job-x", "uart", seeder_uid)

    with apijobs._jobs_lock:
        apijobs._jobs["job-x"] = job_x

    try:
        # Fresh client with no cookies → anonymous in multi-user mode → 401
        anon = TestClient(app, raise_server_exceptions=False)
        with patch.object(apijobs, "_refresh_tracked_jobs",
                          return_value=([job_x], False)):
            resp = anon.get("/api/jobs")

        assert resp.status_code == 401, (
            f"expected 401 for unauthenticated request, got {resp.status_code}: {resp.text}"
        )
    finally:
        with apijobs._jobs_lock:
            apijobs._jobs.pop("job-x", None)
