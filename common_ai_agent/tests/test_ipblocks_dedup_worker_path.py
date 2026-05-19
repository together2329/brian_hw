"""
Regression test: UI-create + worker-dispatch for same (user, ip_name) must
produce exactly ONE ip_blocks row, not two.

Before the fix: _dispatch_workflow_tool_bridge called _make_job_record without
db_user_id, so _record_job_db_start resolved a different workspace_id than the
UI path, causing a second ip_blocks row to be inserted.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))


@pytest.fixture()
def db(tmp_path):
    from core.atlas_db import AtlasDB

    db_path = str(tmp_path / "atlas.db")
    with AtlasDB(db_path) as _db:
        yield _db


def _count_ip_blocks(db, ip_name: str) -> int:
    rows = db._fetchall(
        "SELECT id FROM ip_blocks WHERE ip_name = ?",
        (ip_name,),
    )
    return len(rows)


def test_ui_path_then_worker_path_single_ip_block(db):
    """Simulate UI create then worker-path upsert: expect exactly 1 ip_blocks row."""
    ip_name = "cmux_dedup_test"
    user_uuid = "user-uuid-abc123"
    workspace_name = "test_project"

    # --- UI path: upsert_workspace with real UUID, then upsert_ip_block ---
    ui_workspace = db.upsert_workspace(
        workspace_name,
        owner_user_id=user_uuid,
        local_path="/tmp/test_project",
    )
    ui_ip_row = db.upsert_ip_block(
        ui_workspace["id"],
        ip_name,
        ssot_path=f"{ip_name}/yaml/{ip_name}.ssot.yaml",
    )

    assert _count_ip_blocks(db, ip_name) == 1

    # --- Worker path: _resolve_db_user_id with explicit_user_id=user_uuid ---
    # This simulates what _record_job_db_start does when db_user_id is correctly
    # passed as owner_user_id (the fix). It should find the same workspace.
    worker_workspace = db.upsert_workspace(
        workspace_name,
        owner_user_id=user_uuid,
        local_path="/tmp/test_project",
    )
    worker_ip_row = db.upsert_ip_block(
        worker_workspace["id"],
        ip_name,
    )

    assert _count_ip_blocks(db, ip_name) == 1, (
        "Expected single ip_blocks row after worker-path upsert, "
        f"got multiple — workspace_ids: UI={ui_workspace['id']!r} "
        f"worker={worker_workspace['id']!r}"
    )
    assert ui_ip_row["id"] == worker_ip_row["id"], (
        "ip_blocks row id must be identical across UI and worker paths"
    )
    assert ui_workspace["id"] == worker_workspace["id"], (
        "workspace_id must be identical across UI and worker paths"
    )


def test_different_owner_user_id_creates_separate_workspace(db):
    """Sanity: different owner_user_ids do create separate workspaces (not a bug)."""
    ip_name = "cmux_dedup_test2"

    ws_a = db.upsert_workspace("proj", owner_user_id="user-a", local_path="/tmp/proj")
    ws_b = db.upsert_workspace("proj", owner_user_id="user-b", local_path="/tmp/proj")

    assert ws_a["id"] != ws_b["id"]

    db.upsert_ip_block(ws_a["id"], ip_name)
    db.upsert_ip_block(ws_b["id"], ip_name)

    # Two rows expected — one per workspace
    assert _count_ip_blocks(db, ip_name) == 2


def test_empty_owner_user_id_vs_uuid_creates_separate_workspace_pre_fix(db):
    """
    Demonstrates the pre-fix bug: empty owner_user_id produces a different
    workspace than the UUID-keyed workspace, causing ip_blocks duplication.
    This test documents that the two workspaces ARE different — the fix
    prevents the empty-owner-id path from ever being taken on the worker path.
    """
    ip_name = "cmux_dedup_test3"
    user_uuid = "user-uuid-xyz"

    ws_real = db.upsert_workspace("proj", owner_user_id=user_uuid, local_path="/tmp/proj")
    ws_empty = db.upsert_workspace("proj", owner_user_id="", local_path="/tmp/proj")

    # The two workspaces are different rows (empty-owner is a different identity)
    assert ws_real["id"] != ws_empty["id"]

    db.upsert_ip_block(ws_real["id"], ip_name)
    db.upsert_ip_block(ws_empty["id"], ip_name)

    # Two ip_blocks rows — this is the duplicated state the fix prevents
    assert _count_ip_blocks(db, ip_name) == 2
