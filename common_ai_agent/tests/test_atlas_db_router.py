"""Wave 1 / Unit A — AtlasDBRouter (control vs runtime split).

Covers plan §2.1, §2.5, §2.11 and Task 1:
  - central mode -> runtime path == control path (behavior preserving)
  - session mode -> manifest row + <root>/<uid[0:2]>/<uid>.db, basename != raw id
  - traversal-like uid rejected (containment guard)
  - fail closed when no uid and derived-key flag off
  - derived-key fallback only behind ATLAS_RUNTIME_DB_ALLOW_DERIVED_KEY
  - deterministic same path for same session_id across two calls (no re-mint)
"""

from __future__ import annotations

import hashlib
import os
import sqlite3
from pathlib import Path

import pytest

from core.atlas_db import AtlasDB
from core.atlas_db_router import AtlasDBRouter, RuntimeDBError


@pytest.fixture()
def paths(tmp_path):
    control = str(tmp_path / "atlas.db")
    runtime_root = str(tmp_path / "runtime")
    return control, runtime_root


def _hex(s: str) -> bool:
    return bool(s) and all(c in "0123456789abcdef" for c in s.lower())


# ──────────────────────────────────────────────────────────────
# central mode
# ──────────────────────────────────────────────────────────────

def test_central_mode_runtime_path_equals_control_path(paths):
    control, runtime_root = paths
    r = AtlasDBRouter(control_path=control, runtime_root=runtime_root, mode="central")
    assert r.control_db_path() == control
    assert r.runtime_db_path("alice/ip_deep/rtl-gen") == control
    route = r.runtime_route("alice/ip_deep/rtl-gen")
    assert route.mode == "central"
    assert route.runtime_db_path == control
    assert route.session_uid is None


def test_central_mode_is_the_default_when_no_env(paths, monkeypatch):
    control, runtime_root = paths
    monkeypatch.delenv("ATLAS_RUNTIME_DB_MODE", raising=False)
    r = AtlasDBRouter(control_path=control, runtime_root=runtime_root)
    assert r.mode() == "central"
    assert r.runtime_db_path("whatever") == control


def test_central_mode_runtime_db_opens_full_schema(paths):
    control, runtime_root = paths
    r = AtlasDBRouter(control_path=control, runtime_root=runtime_root, mode="central")
    db = r.runtime_db("alice/ip_deep/rtl-gen")
    # control file must carry the full schema (users table is control-only).
    names = {row[0] for row in db._fetchall(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    assert "users" in names
    assert "workspaces" in names


# ──────────────────────────────────────────────────────────────
# session mode
# ──────────────────────────────────────────────────────────────

def test_session_mode_writes_manifest_and_sharded_path(paths):
    control, runtime_root = paths
    r = AtlasDBRouter(control_path=control, runtime_root=runtime_root, mode="session")
    sid = "alice/ip_deep/rtl-gen"
    route = r.runtime_route(sid, create=True)

    assert route.mode == "session"
    assert _hex(route.session_uid)
    # Path shape: <root>/<uid[0:2]>/<uid>.db
    expected = (
        Path(runtime_root).resolve()
        / route.session_uid[0:2]
        / f"{route.session_uid}.db"
    )
    assert Path(route.runtime_db_path) == expected
    # basename is the uid, NOT the raw session_id segment.
    assert os.path.basename(route.runtime_db_path) != "rtl-gen"
    assert os.path.basename(route.runtime_db_path) == f"{route.session_uid}.db"
    # under the runtime root.
    assert str(Path(route.runtime_db_path)).startswith(str(Path(runtime_root).resolve()))

    # manifest row exists in the CONTROL db and matches.
    control_db = AtlasDB(db_path=control, schema_set="full")
    manifest = control_db.get_session_runtime_db(sid)
    assert manifest is not None
    assert manifest["session_uid"] == route.session_uid
    assert manifest["runtime_db_path"] == route.runtime_db_path
    assert manifest["status"] == "active"


def test_session_mode_runtime_db_has_only_subset_tables(paths):
    control, runtime_root = paths
    r = AtlasDBRouter(control_path=control, runtime_root=runtime_root, mode="session")
    db = r.runtime_db("alice/ip_deep/rtl-gen")
    names = {row[0] for row in db._fetchall(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    assert names == {"session_queue", "messages", "parts", "trace_events", "llm_calls"}
    # no control tables materialized.
    assert "users" not in names
    assert "workspaces" not in names


def test_session_mode_basename_not_raw_for_traversal_like_id(paths):
    """A nasty raw session_id never reaches the filesystem; uid is hex-only."""
    control, runtime_root = paths
    r = AtlasDBRouter(control_path=control, runtime_root=runtime_root, mode="session")
    route = r.runtime_route("../../../etc/passwd", create=True)
    assert _hex(route.session_uid)
    assert ".." not in route.runtime_db_path
    assert "etc" not in os.path.basename(route.runtime_db_path)
    # still contained.
    assert str(Path(route.runtime_db_path).resolve()).startswith(
        str(Path(runtime_root).resolve())
    )


# ──────────────────────────────────────────────────────────────
# traversal / containment guard
# ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    "bad_uid",
    ["../../etc/passwd", "a/b", "..", "xx/../../yy", "AB.;rm", "", "/abs"],
)
def test_unsafe_uid_rejected_by_containment_guard(paths, bad_uid):
    control, runtime_root = paths
    r = AtlasDBRouter(control_path=control, runtime_root=runtime_root, mode="session")
    with pytest.raises(RuntimeDBError):
        r._expected_runtime_path(bad_uid)


def test_expected_path_always_under_root(paths):
    control, runtime_root = paths
    r = AtlasDBRouter(control_path=control, runtime_root=runtime_root, mode="session")
    uid = "deadbeef" * 4  # 32 hex chars
    p = r._expected_runtime_path(uid)
    Path(p).resolve().relative_to(Path(runtime_root).resolve())  # raises if escapes


# ──────────────────────────────────────────────────────────────
# fail-closed + derived key flag
# ──────────────────────────────────────────────────────────────

def test_fail_closed_when_no_uid_and_derived_key_off(paths, monkeypatch):
    control, runtime_root = paths
    monkeypatch.delenv("ATLAS_RUNTIME_DB_ALLOW_DERIVED_KEY", raising=False)
    r = AtlasDBRouter(control_path=control, runtime_root=runtime_root, mode="session")
    # empty session id, create=False -> nothing to resolve, no derived key.
    with pytest.raises(RuntimeDBError):
        r.runtime_route("", create=False)


def test_create_false_unknown_session_fails_closed(paths, monkeypatch):
    """create=False must not mint; unknown session with flag off fails closed."""
    control, runtime_root = paths
    monkeypatch.delenv("ATLAS_RUNTIME_DB_ALLOW_DERIVED_KEY", raising=False)
    r = AtlasDBRouter(control_path=control, runtime_root=runtime_root, mode="session")
    with pytest.raises(RuntimeDBError):
        r.runtime_route("never-seen-session", create=False)


def test_derived_key_fallback_only_behind_flag(paths, monkeypatch):
    control, runtime_root = paths
    monkeypatch.setenv("ATLAS_RUNTIME_DB_ALLOW_DERIVED_KEY", "1")
    r = AtlasDBRouter(control_path=control, runtime_root=runtime_root, mode="session")
    route = r.runtime_route("raw-session-x", create=False)
    expected_uid = hashlib.sha256(b"raw-session-x").hexdigest()[:24]
    assert route.session_uid == expected_uid
    assert _hex(route.session_uid)


# ──────────────────────────────────────────────────────────────
# determinism / no re-mint (R4)
# ──────────────────────────────────────────────────────────────

def test_same_session_id_same_path_across_two_calls(paths):
    control, runtime_root = paths
    r = AtlasDBRouter(control_path=control, runtime_root=runtime_root, mode="session")
    sid = "alice/ip_deep/rtl-gen"
    p1 = r.runtime_db_path(sid, create=True)
    p2 = r.runtime_db_path(sid, create=True)
    assert p1 == p2
    # uid stable too.
    u1 = r.runtime_route(sid).session_uid
    u2 = r.runtime_route(sid).session_uid
    assert u1 == u2


def test_session_route_resolution_reuses_control_connection(paths, monkeypatch):
    control, runtime_root = paths
    r = AtlasDBRouter(control_path=control, runtime_root=runtime_root, mode="session")
    sid = "alice/ip_deep/rtl-gen"
    r.runtime_route(sid, create=True)
    real_connect = sqlite3.connect
    opens = {"count": 0}

    def counting_connect(*args, **kwargs):
        opens["count"] += 1
        return real_connect(*args, **kwargs)

    monkeypatch.setattr(sqlite3, "connect", counting_connect)
    for _ in range(20):
        r.runtime_route(sid, create=False)

    assert opens["count"] == 0


def test_create_false_runtime_db_does_not_create_missing_file(paths):
    control, runtime_root = paths
    r = AtlasDBRouter(control_path=control, runtime_root=runtime_root, mode="session")
    sid = "alice/ip_deep/rtl-gen"
    route = r.runtime_route(sid, create=True)
    runtime_path = Path(route.runtime_db_path)

    assert not runtime_path.exists()
    with pytest.raises(RuntimeDBError):
        r.runtime_db(sid, create=False)
    assert not runtime_path.exists()


def test_no_remint_across_fresh_router_instances(paths):
    """A second router (e.g. after a retry/respawn) resolves the SAME path."""
    control, runtime_root = paths
    sid = "bob/some_ip/sim"
    r1 = AtlasDBRouter(control_path=control, runtime_root=runtime_root, mode="session")
    p1 = r1.runtime_db_path(sid, create=True)
    r2 = AtlasDBRouter(control_path=control, runtime_root=runtime_root, mode="session")
    p2 = r2.runtime_db_path(sid, create=True)
    assert p1 == p2


# ──────────────────────────────────────────────────────────────
# config resolution
# ──────────────────────────────────────────────────────────────

def test_invalid_mode_raises(paths):
    control, runtime_root = paths
    r = AtlasDBRouter(control_path=control, runtime_root=runtime_root, mode="bogus")
    with pytest.raises(RuntimeDBError):
        r.mode()


def test_runtime_root_default_is_control_dir_runtime(tmp_path, monkeypatch):
    control = str(tmp_path / "sub" / "atlas.db")
    monkeypatch.delenv("ATLAS_RUNTIME_DB_ROOT", raising=False)
    r = AtlasDBRouter(control_path=control)
    assert Path(r.runtime_root()) == Path(control).resolve().parent / "runtime"


def test_env_read_at_call_time(tmp_path, monkeypatch):
    """Mode is resolved from env at call time, not cached at construction."""
    control = str(tmp_path / "atlas.db")
    runtime_root = str(tmp_path / "runtime")
    monkeypatch.setenv("ATLAS_CONTROL_DB_PATH", control)
    monkeypatch.setenv("ATLAS_RUNTIME_DB_ROOT", runtime_root)
    monkeypatch.setenv("ATLAS_RUNTIME_DB_MODE", "central")
    r = AtlasDBRouter()  # no overrides -> all from env
    assert r.mode() == "central"
    monkeypatch.setenv("ATLAS_RUNTIME_DB_MODE", "session")
    assert r.mode() == "session"


def test_uid_mint_preserves_existing_session_metadata(paths):
    """Review LOW #1 regression: minting a session_uid for a session that lacks
    one must NOT blank its ip/workflow/owner/title (the old upsert_runtime_session
    path rewrote the whole row, defaulting those fields to ''/None)."""
    control, runtime_root = paths
    db = AtlasDB(db_path=control, schema_set="full")
    sid = "alice/ip_deep/rtl-gen"
    db.upsert_runtime_session(
        sid,
        user_id="u_alice",
        owner="alice",
        ip="ip_deep",
        workflow="rtl-gen",
        title="Deep RTL",
        status="active",
    )
    # Simulate an older/migrated session row that carries metadata but no uid.
    db.update_session(sid, session_uid="")
    before = db.get_session(sid)
    assert before["ip"] == "ip_deep" and before["workflow"] == "rtl-gen"
    assert not before.get("session_uid")

    r = AtlasDBRouter(control_path=control, runtime_root=runtime_root, mode="session")
    route = r.runtime_route(sid, create=True)
    assert _hex(route.session_uid or "")

    after = db.get_session(sid)
    # metadata preserved (NOT blanked) ...
    assert after["ip"] == "ip_deep"
    assert after["workflow"] == "rtl-gen"
    assert after["owner"] == "alice"
    assert after["title"] == "Deep RTL"
    assert after["user_id"] == "u_alice"
    # ... and session_uid is backfilled to match the route.
    assert after["session_uid"] == route.session_uid
    # determinism: a second resolve returns the same uid (manifest fast-path).
    assert r.runtime_route(sid, create=True).session_uid == route.session_uid
