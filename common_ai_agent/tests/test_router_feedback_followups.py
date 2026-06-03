"""Follow-up fixes for the wiki "Feedback Resolution Review - 2026-06-03".

Covers the items that the second-pass review flagged as PARTIAL plus the
additional findings:

  #1  hot/read paths must resolve with create=False so a COLD-cache first
      poll_output / reseed_output_cursor / latest_output_id never upserts
      session_runtime_dbs (no manifest updated_at move). A session with no
      manifest yet reads empty (no crash, no upsert).
  #2  delete gate:
      - gap2: a runtime cleanup ERROR must BLOCK the control delete (the
        control session is preserved, never orphaned behind a deleted row).
      - gap1 / finding C: session_delete_response maps the outcome to honest
        HTTP codes (200 deleted / 409 force-required / 500 runtime error).
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
for p in (PROJECT_ROOT, PROJECT_ROOT / "src"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from core.atlas_db import AtlasDB
from core.atlas_db_router import AtlasDBRouter
from core.session_process_manager import SessionProcessManager


def _session_router(control: str, runtime_root: str) -> AtlasDBRouter:
    return AtlasDBRouter(control_path=control, runtime_root=runtime_root, mode="session")


# ─────────────────────────────────────────────────────────────
# #1 — cold-cache read paths must not upsert the manifest
# ─────────────────────────────────────────────────────────────

def test_cold_manager_read_paths_do_not_upsert_manifest(tmp_path, monkeypatch):
    control = str(tmp_path / "atlas.db")
    runtime_root = str(tmp_path / "runtime")
    sid = "alice/ip_a/rtl-gen"

    # Activation/first write already created the manifest + runtime file.
    _session_router(control, runtime_root).runtime_db(sid, create=True)
    ctrl = AtlasDB(control, schema_set="full")
    before = ctrl.get_session_runtime_db(sid)
    assert before is not None
    updated_before = before["updated_at"]

    # Spy on the manifest upsert (the only Control-DB write a poll could trigger).
    calls = {"n": 0}
    orig = AtlasDB.upsert_session_runtime_db

    def _spy(self, *a, **k):
        calls["n"] += 1
        return orig(self, *a, **k)

    monkeypatch.setattr(AtlasDB, "upsert_session_runtime_db", _spy)

    time.sleep(0.01)  # ensure any updated_at change would be visible
    mgr = SessionProcessManager(db_path=control, router=_session_router(control, runtime_root))
    try:
        # A FRESH (cold-cache) manager's first reads on each path.
        assert mgr.poll_output(sid) == []
        assert mgr.latest_output_id(sid) is None
        assert mgr.reseed_output_cursor(sid) is None
    finally:
        mgr.stop_all()

    assert calls["n"] == 0, "cold read paths must NOT upsert session_runtime_dbs"
    after = ctrl.get_session_runtime_db(sid)
    assert after["updated_at"] == updated_before, "manifest updated_at must not move on read"


def test_cold_read_no_manifest_returns_empty_without_upsert(tmp_path, monkeypatch):
    control = str(tmp_path / "atlas.db")
    runtime_root = str(tmp_path / "runtime")
    AtlasDB(control, schema_set="full")  # init control schema

    calls = {"n": 0}
    orig = AtlasDB.upsert_session_runtime_db

    def _spy(self, *a, **k):
        calls["n"] += 1
        return orig(self, *a, **k)

    monkeypatch.setattr(AtlasDB, "upsert_session_runtime_db", _spy)

    mgr = SessionProcessManager(db_path=control, router=_session_router(control, runtime_root))
    try:
        # Session never activated -> no manifest -> reads are empty, no crash.
        assert mgr.poll_output("ghost/ip/wf") == []
        assert mgr.latest_output_id("ghost/ip/wf") is None
        assert mgr.reseed_output_cursor("ghost/ip/wf") is None
    finally:
        mgr.stop_all()
    assert calls["n"] == 0


def test_write_path_still_materializes_manifest(tmp_path):
    """Sanity: the WRITE path (create=True) DOES still create the manifest, so the
    read-path create=False fix didn't disable activation."""
    control = str(tmp_path / "atlas.db")
    runtime_root = str(tmp_path / "runtime")
    sid = "alice/ip_w/rtl-gen"
    ctrl = AtlasDB(control, schema_set="full")
    assert ctrl.get_session_runtime_db(sid) is None
    _session_router(control, runtime_root).runtime_db(sid, create=True)
    assert ctrl.get_session_runtime_db(sid) is not None


# ─────────────────────────────────────────────────────────────
# #2 gap2 — a runtime cleanup error must block the control delete
# ─────────────────────────────────────────────────────────────

def test_runtime_cleanup_error_blocks_control_delete(tmp_path, monkeypatch):
    from core import runtime_rollup

    control = str(tmp_path / "atlas.db")
    runtime_root = str(tmp_path / "runtime")
    monkeypatch.setenv("ATLAS_RUNTIME_DB_MODE", "session")
    monkeypatch.setenv("ATLAS_CONTROL_DB_PATH", control)
    monkeypatch.setenv("ATLAS_RUNTIME_DB_ROOT", runtime_root)

    db = AtlasDB(control, schema_set="full")
    sid = "alice/ip_a/rtl-gen"
    db.upsert_runtime_session(sid, user_id="u_alice", owner="alice", ip="ip_a", workflow="rtl-gen")
    _session_router(control, runtime_root).runtime_db(sid, create=True)
    assert db.get_session(sid) is not None

    def _boom(*a, **k):
        raise RuntimeError("simulated runtime cleanup failure")

    monkeypatch.setattr(runtime_rollup, "delete_session_runtime", _boom)

    result = db.delete_session(sid)
    assert result["deleted"] is False
    assert "error" in result["runtime"]
    # The control session must be PRESERVED — never deleted while runtime cleanup
    # failed (would orphan the runtime file/manifest behind a gone session row).
    assert db.get_session(sid) is not None


# ─────────────────────────────────────────────────────────────
# #2 gap1 / finding C — honest HTTP status from the delete outcome
# ─────────────────────────────────────────────────────────────

def test_session_delete_response_status_codes():
    from atlas_session_delete import session_delete_response

    assert session_delete_response(
        {"deleted": True, "runtime": {"deleted": True}}
    ).status_code == 200
    assert session_delete_response(
        {"deleted": False, "runtime": {"force_required": True, "skipped_reason": "queue_non_empty"}}
    ).status_code == 409
    assert session_delete_response(
        {"deleted": False, "runtime": {"error": "boom"}}
    ).status_code == 500
