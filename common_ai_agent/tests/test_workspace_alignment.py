"""Regression test: chat path and dispatch path must resolve to the same workspace row.

Bug: _record_orchestrator_chat used owner_user_id="local-admin" as fallback while
_job_db_workspace_and_ip used "" — producing two different workspace rows for the
same (project_root, user), so workflow_runs created under the chat path were
invisible when queried through the dispatch path.

Fix: _job_db_workspace_and_ip now also falls back to "local-admin".
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

_REPO = Path(__file__).resolve().parents[1]
for _p in (_REPO, _REPO / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from core.atlas_db import AtlasDB
from src import atlas_api_jobs as jobs_mod


def _make_client(tmp_path: Path, monkeypatch) -> tuple[TestClient, Path]:
    import src.atlas_ui as atlas_ui
    from src.orchestrator import runner as runner_mod

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setenv("ATLAS_ADMIN_AUTH_MODE", "db")
    monkeypatch.setenv("ATLAS_ADMIN_LOGIN_REQUIRED", "1")
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.delenv("ATLAS_LOCAL_ADMIN", raising=False)
    monkeypatch.delenv("ATLAS_ADMIN_BYPASS", raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    class _StubRunner:
        def submit_or_attach(self, **kwargs):
            from src.orchestrator.runner import SubmitOutcome
            return SubmitOutcome(run_id="stub-run-1", status="started")

        def shutdown(self, wait=False):
            pass

    stub = _StubRunner()
    runner_mod.set_runner_for_test(stub)
    monkeypatch.setattr(runner_mod, "get_runner", lambda db_path: stub)

    client = TestClient(atlas_ui.create_app())
    reg = client.post("/api/auth/register", json={"username": "u_align", "password": "pw"})
    assert reg.status_code == 200, reg.text

    yield client, tmp_path

    runner_mod.set_runner_for_test(None)


@pytest.fixture
def ctx(tmp_path, monkeypatch):
    gen = _make_client(tmp_path, monkeypatch)
    result = next(gen)
    yield result
    try:
        next(gen)
    except StopIteration:
        pass


def test_workspace_id_aligned_across_chat_and_dispatch(ctx):
    """Single workspace row for same project_root regardless of call path."""
    client, tmp_path = ctx
    db_path = str(tmp_path / "atlas.db")
    ip = "foo_align"

    # --- Chat path ---
    chat_resp = client.post(
        "/api/pipeline/orchestrator/chat",
        json={"message": f"run ip={ip}", "ip": ip},
    )
    assert chat_resp.status_code == 200, chat_resp.text
    assert chat_resp.json().get("ok"), chat_resp.text

    # --- Dispatch path ---
    dispatch_resp = client.post(
        "/api/pipeline/dispatch",
        json={"ip": ip, "stages": ["ssot"]},
    )
    assert dispatch_resp.status_code == 200, dispatch_resp.text
    assert dispatch_resp.json().get("ok"), dispatch_resp.text

    # --- Assert single workspace row via DB ---
    with AtlasDB(db_path) as db:
        rows = db._fetchall(
            "SELECT id, owner_user_id, name FROM workspaces WHERE name = ?",
            (tmp_path.name,),
        )

    assert len(rows) == 1, (
        f"Expected 1 workspace row for name={tmp_path.name!r}, "
        f"got {len(rows)}: {rows}"
    )


def test_ip_blocks_share_workspace_across_paths(ctx):
    """ip_blocks created by chat and dispatch share the same workspace_id."""
    client, tmp_path = ctx
    db_path = str(tmp_path / "atlas.db")
    ip = "foo_align2"

    client.post(
        "/api/pipeline/orchestrator/chat",
        json={"message": f"run ip={ip}", "ip": ip},
    )
    client.post(
        "/api/pipeline/dispatch",
        json={"ip": ip, "stages": ["ssot"]},
    )

    with AtlasDB(db_path) as db:
        ws_rows = db._fetchall(
            "SELECT id FROM workspaces WHERE name = ?",
            (tmp_path.name,),
        )
        assert len(ws_rows) == 1, f"workspace rows: {ws_rows}"
        ws_id = ws_rows[0]["id"]

        ip_rows = db._fetchall(
            "SELECT id, workspace_id FROM ip_blocks WHERE ip_name = ?",
            (ip,),
        )
        assert len(ip_rows) >= 1
        for r in ip_rows:
            assert r["workspace_id"] == ws_id, (
                f"ip_block workspace_id={r['workspace_id']} != workspace id={ws_id}"
            )
