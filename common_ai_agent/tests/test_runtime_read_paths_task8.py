"""Task 8 — route runtime READ paths + harden the raw-DB inspector.

Covers the read-side + security contract owned by Task 8 (plan §2.11, R7/R14/
R20/R21/R24):

1. Session history reads the RUNTIME ``messages``/``parts`` in session mode (the
   control ``messages`` table can be empty); central mode is unchanged.
2. Cross-user runtime read is DENIED: Alice owns a session; Bob requests the raw
   runtime DB by Alice's session_uid -> 403, no rows, no path in the body.
3. The raw-DB inspector rejects path-like input (``/ \\ .. :``) and NEVER returns
   a ``path``/``db_path`` field — INCLUDING under is_admin/local-admin bypass.
4. The OMITTED IP-scoped readers (``_recent_events_for_ip`` and the room-context
   summaries) return an explicit runtime-unavailable marker (NOT ``[]``) in
   session mode, and real rows in central mode.
5. ``list_run_artifact_version_sets`` / dashboard ``_workflow_runs`` flag the
   per-run usage as runtime-unavailable in session mode (no silent 0-as-fact).
6. Chat reads (``list_chat_messages``) re-route to CONTROL when the AtlasDB is
   bound to a runtime file in session mode (chat lives in control).

These pin the CONTRACT directly against AtlasDB / AtlasDBRouter / the shared
admin-db inspector, so they are fast and need no live UI or real subprocess.

The ``_authorize_session_request`` fail-CLOSED case (R20) is verified at the
HTTP-route layer in :mod:`tests.test_chat_full_multiuser_system` siblings; here
we verify the equivalent decision primitive (a failing ownership lookup must
deny) via the shared inspector's deny-on-error behavior.
"""

from __future__ import annotations

import pytest

from core.atlas_db import AtlasDB
from core.atlas_db_router import AtlasDBRouter
from core.atlas_admin_db import (
    RuntimeInspectError,
    inspect_runtime_table,
    resolve_runtime_inspect_db,
)


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #


@pytest.fixture
def split_env(tmp_path, monkeypatch):
    """Explicit control DB + runtime root; SESSION mode. Returns (control, root)."""
    control_path = str(tmp_path / "atlas.db")
    runtime_root = str(tmp_path / "runtime")
    monkeypatch.setenv("ATLAS_CONTROL_DB_PATH", control_path)
    monkeypatch.setenv("ATLAS_RUNTIME_DB_ROOT", runtime_root)
    monkeypatch.setenv("ATLAS_RUNTIME_DB_MODE", "session")
    monkeypatch.delenv("ATLAS_DB_PATH", raising=False)
    AtlasDB(control_path, schema_set="full").close()
    return control_path, runtime_root


def _seed_owned_session(control_path, *, user_id, session_id, ip_id="ip-a", workflow="rtl-gen"):
    """Create a control session row + minted uid + runtime manifest. Returns route."""
    with AtlasDB(control_path, schema_set="full") as db:
        db.upsert_runtime_session(
            session_id, user_id=user_id, ip_id=ip_id, workflow=workflow
        )
    return AtlasDBRouter().runtime_route(session_id, create=True)


# --------------------------------------------------------------------------- #
# 1. Session history reads runtime messages in session mode; central unchanged.
# --------------------------------------------------------------------------- #


def test_session_history_reads_runtime_messages(split_env):
    control_path, _root = split_env
    session_id = "alice/ip-a/rtl-gen"
    route = _seed_owned_session(control_path, user_id="alice-uid", session_id=session_id)
    db_session_id = route.session_id

    # Worker writes a message+part into the RUNTIME DB (session mode).
    with AtlasDB(route.runtime_db_path, schema_set="runtime") as rdb:
        msg = rdb.save_message(session_id=db_session_id, role="assistant")
        rdb.save_part(message_id=msg["id"], session_id=db_session_id,
                      type="text", text="hello from runtime")

    # Control messages table is EMPTY for this session.
    with AtlasDB(control_path, schema_set="full") as cdb:
        assert cdb.get_messages(db_session_id) == []

    # Reading through the router (create=False) returns the runtime rows.
    runtime_db = AtlasDBRouter().runtime_db(db_session_id, create=False)
    try:
        msgs = runtime_db.get_messages(db_session_id)
        assert len(msgs) == 1
        parts = runtime_db.get_parts(msgs[0]["id"])
        assert any(p.get("text") == "hello from runtime" for p in parts)
    finally:
        runtime_db.close()


def test_session_history_central_mode_unchanged(tmp_path, monkeypatch):
    monkeypatch.setenv("ATLAS_RUNTIME_DB_MODE", "central")
    monkeypatch.delenv("ATLAS_CONTROL_DB_PATH", raising=False)
    monkeypatch.delenv("ATLAS_RUNTIME_DB_ROOT", raising=False)
    db_path = str(tmp_path / "control.db")
    monkeypatch.setenv("ATLAS_DB_PATH", db_path)
    monkeypatch.setenv("ATLAS_CONTROL_DB_PATH", db_path)
    with AtlasDB(db_path, schema_set="full") as db:
        sess = db.create_session(user_id="u", title="t")
        m = db.save_message(session_id=sess["id"], role="assistant")
        db.save_part(message_id=m["id"], session_id=sess["id"], type="text", text="hi")
    # Central mode: the router returns the control path, so the same file holds it.
    route = AtlasDBRouter().runtime_route(sess["id"], create=False)
    assert route.mode == "central"
    rdb = AtlasDBRouter().runtime_db(sess["id"], create=False)
    try:
        assert len(rdb.get_messages(sess["id"])) == 1
    finally:
        rdb.close()


# --------------------------------------------------------------------------- #
# 2. Cross-user runtime read DENIED.
# --------------------------------------------------------------------------- #


def test_cross_user_runtime_read_denied(split_env):
    control_path, _root = split_env
    route = _seed_owned_session(
        control_path, user_id="alice-uid", session_id="alice/ip-a/rtl-gen"
    )
    alice_uid = route.session_uid
    # Write a row so a successful read WOULD return data (proves the deny is authz,
    # not just an empty file).
    with AtlasDB(route.runtime_db_path, schema_set="runtime") as rdb:
        rdb.save_message(session_id=route.session_id, role="assistant")

    with AtlasDB(control_path, schema_set="full") as cdb:
        # Bob (different user) requests Alice's runtime DB by her session_uid.
        with pytest.raises(RuntimeInspectError) as exc:
            inspect_runtime_table(
                cdb,
                session_uid=alice_uid,
                requesting_user_id="bob-uid",
                requesting_username="bob",
                is_admin=True,  # admin bypass must NOT grant cross-user access
                table=None,
            )
    assert exc.value.status == 403
    # No filesystem path in the safe message.
    assert "/" not in exc.value.message and "\\" not in exc.value.message


def test_owner_runtime_read_allowed_returns_no_path(split_env):
    control_path, _root = split_env
    route = _seed_owned_session(
        control_path, user_id="alice-uid", session_id="alice/ip-a/rtl-gen"
    )
    with AtlasDB(route.runtime_db_path, schema_set="runtime") as rdb:
        rdb.save_message(session_id=route.session_id, role="assistant")

    with AtlasDB(control_path, schema_set="full") as cdb:
        catalog = inspect_runtime_table(
            cdb,
            session_uid=route.session_uid,
            requesting_user_id="alice-uid",
            requesting_username="alice",
            is_admin=False,
            table=None,
        )
        rows = inspect_runtime_table(
            cdb,
            session_uid=route.session_uid,
            requesting_user_id="alice-uid",
            requesting_username="alice",
            is_admin=False,
            table="messages",
        )
    # Owner sees the runtime tables + rows.
    assert any(t["name"] == "messages" for t in catalog["tables"])
    assert rows["total"] >= 1
    # NEVER echo a filesystem path field.
    for payload in (catalog, rows):
        assert "path" not in payload
        assert "db_path" not in payload
        assert "runtime_db_path" not in payload
        for v in payload.values():
            assert not (isinstance(v, str) and ("/" in v and v.endswith(".db")))


# --------------------------------------------------------------------------- #
# 3. Path-like input rejected; never returns a path — incl. admin bypass.
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "bad",
    [
        "../../etc/passwd",
        "a/b",
        "a\\b",
        "..",
        "C:\\windows",
        "/abs/path.db",
        "x:y",
    ],
)
def test_runtime_inspect_rejects_path_like(split_env, bad):
    control_path, _root = split_env
    with AtlasDB(control_path, schema_set="full") as cdb:
        with pytest.raises(RuntimeInspectError) as exc:
            inspect_runtime_table(
                cdb,
                session_uid=bad,
                requesting_user_id="anyone",
                requesting_username="anyone",
                is_admin=True,  # bypass still must reject path-like input
                table=None,
            )
    # 404 (do not confirm it was almost a path), and no path leaked.
    assert exc.value.status == 404
    assert "/" not in exc.value.message and "\\" not in exc.value.message


def test_runtime_inspect_unknown_uid_404_no_path(split_env):
    control_path, _root = split_env
    with AtlasDB(control_path, schema_set="full") as cdb:
        with pytest.raises(RuntimeInspectError) as exc:
            resolve_runtime_inspect_db(
                cdb,
                session_uid="deadbeef" * 4,  # valid hex, no manifest
                requesting_user_id="someone",
                is_admin=True,
            )
    assert exc.value.status == 404
    assert "/" not in exc.value.message


# --------------------------------------------------------------------------- #
# 4. Omitted IP-scoped readers: explicit unavailable marker, not [].
# --------------------------------------------------------------------------- #


def test_recent_events_for_ip_marker_in_session_mode(split_env):
    control_path, _root = split_env
    from core.runtime_rollup import is_runtime_unavailable

    with AtlasDB(control_path, schema_set="full") as cdb:
        events = cdb._recent_events_for_ip("ip-a")
    assert is_runtime_unavailable(events)
    assert events != []


def test_recent_events_for_ip_real_rows_central_mode(tmp_path, monkeypatch):
    monkeypatch.setenv("ATLAS_RUNTIME_DB_MODE", "central")
    monkeypatch.delenv("ATLAS_RUNTIME_DB_ROOT", raising=False)
    db_path = str(tmp_path / "control.db")
    monkeypatch.setenv("ATLAS_DB_PATH", db_path)
    monkeypatch.setenv("ATLAS_CONTROL_DB_PATH", db_path)
    from core.runtime_rollup import is_runtime_unavailable

    with AtlasDB(db_path, schema_set="full") as db:
        db.record_trace_event(event_type="workflow_event", ip_id="ip-a",
                              payload={"x": 1})
        events = db._recent_events_for_ip("ip-a")
    assert not is_runtime_unavailable(events)
    assert any(e.get("event_type") == "workflow_event" for e in events)


def test_summarize_global_room_context_marker_session_mode(split_env):
    control_path, _root = split_env
    from core.runtime_rollup import is_runtime_unavailable

    with AtlasDB(control_path, schema_set="full") as cdb:
        # one IP so the recent-events branch is exercised.
        ws = cdb.upsert_workspace("w", owner_user_id="alice-uid", local_path="/tmp/w")
        cdb.upsert_ip_block(ws["id"], "ip-a")
        bundle = cdb.summarize_global_room_context()
    assert is_runtime_unavailable(bundle["recent_cross_ip_events"])


def test_summarize_ip_room_context_recent_events_marker(split_env):
    control_path, _root = split_env
    from core.runtime_rollup import is_runtime_unavailable

    with AtlasDB(control_path, schema_set="full") as cdb:
        ws = cdb.upsert_workspace("w", owner_user_id="alice-uid", local_path="/tmp/w")
        ip = cdb.upsert_ip_block(ws["id"], "ip-a")
        bundle = cdb.summarize_ip_room_context(ip["id"])
    assert bundle is not None
    assert is_runtime_unavailable(bundle["recent_events"])


# --------------------------------------------------------------------------- #
# 5. Per-run usage flagged runtime-unavailable (no silent 0-as-fact).
# --------------------------------------------------------------------------- #


def test_run_artifact_sets_flag_runtime_usage_unavailable(split_env):
    control_path, _root = split_env
    with AtlasDB(control_path, schema_set="full") as cdb:
        run = cdb.start_workflow_run(session_id="alice/ip-a/rtl-gen", workflow="rtl-gen")
        rows = cdb.list_run_artifact_version_sets()
    assert rows, "expected at least one run row"
    assert all(r.get("runtime_usage_unavailable") is True for r in rows)
    # The usage counts are 0 but the explicit flag makes that non-authoritative.
    assert all(r.get("llm_calls") == 0 for r in rows)


def test_workflow_runs_dashboard_flag_in_session_mode(split_env):
    control_path, _root = split_env
    from core.atlas_user_dashboard import _workflow_runs

    with AtlasDB(control_path, schema_set="full") as cdb:
        sess = cdb.create_session(user_id="alice-uid", title="t")
        cdb.start_workflow_run(session_id=sess["id"], workflow="rtl-gen")
        runs = _workflow_runs(cdb, "alice-uid")
    assert runs
    assert all(r.get("runtime_usage_unavailable") is True for r in runs)


# --------------------------------------------------------------------------- #
# 6. Chat reads re-route to CONTROL from a runtime-bound AtlasDB.
# --------------------------------------------------------------------------- #


def test_chat_read_reroutes_to_control_from_runtime_db(split_env):
    control_path, _root = split_env
    route = _seed_owned_session(
        control_path, user_id="alice-uid", session_id="alice/ip-a/rtl-gen"
    )
    # Post a chat (lands in control by the Task-6 write predicate).
    with AtlasDB(control_path, schema_set="full") as cdb:
        ws = cdb.upsert_workspace("w", owner_user_id="alice-uid", local_path="/tmp/w")
        ip = cdb.upsert_ip_block(ws["id"], "ip-a")
        cdb.record_chat_message(ip_id=ip["id"], user_id="alice-uid",
                                content="need a fifo", display_name="alice")
        # Read chat from a CONTROL-bound db -> sees it.
        assert len(cdb.list_chat_messages(ip_id=ip["id"], limit=10)) == 1

    # Read chat from a RUNTIME-bound AtlasDB: the runtime file has no chat rows,
    # but the reader re-routes to control and still returns the message.
    with AtlasDB(route.runtime_db_path, schema_set="runtime") as rdb:
        rerouted = rdb.list_chat_messages(ip_id=ip["id"], limit=10)
    assert len(rerouted) == 1
    assert rerouted[0].get("payload", {}).get("content") == "need a fifo"


# --------------------------------------------------------------------------- #
# Deny-on-error primitive (R20 spirit): a manifest with no session row denies.
# --------------------------------------------------------------------------- #


# --------------------------------------------------------------------------- #
# 7. "No silently-empty admin surface" parity vs central mode.
# --------------------------------------------------------------------------- #


_SUMMARY_ONLY_TABS = (
    "tool_usage",
    "todo_usage",
    "todo_flow",
    "interventions",
    "trace_events",
    "input_history",
    "workflow_stages",
)


def _is_summary_only(value) -> bool:
    return (
        isinstance(value, list)
        and len(value) == 1
        and isinstance(value[0], dict)
        and bool(value[0].get("__summary_only__"))
    )


def test_admin_usage_summary_only_marker_in_session_mode(split_env):
    control_path, _root = split_env
    from core.atlas_admin_usage import build_admin_usage_payload

    with AtlasDB(control_path, schema_set="full") as cdb:
        payload = build_admin_usage_payload(cdb)
    assert payload.get("runtime_mode") is True
    for tab in _SUMMARY_ONLY_TABS:
        assert _is_summary_only(payload[tab]), f"{tab} must be summary-only marker"
        assert payload[tab] != [], f"{tab} must NOT be silently empty"


def test_admin_usage_central_mode_returns_real_lists(tmp_path, monkeypatch):
    monkeypatch.setenv("ATLAS_RUNTIME_DB_MODE", "central")
    monkeypatch.delenv("ATLAS_RUNTIME_DB_ROOT", raising=False)
    db_path = str(tmp_path / "control.db")
    monkeypatch.setenv("ATLAS_DB_PATH", db_path)
    monkeypatch.setenv("ATLAS_CONTROL_DB_PATH", db_path)
    from core.atlas_admin_usage import build_admin_usage_payload

    with AtlasDB(db_path, schema_set="full") as db:
        payload = build_admin_usage_payload(db)
    # Central mode: these are REAL lists (possibly empty), never the marker.
    for tab in _SUMMARY_ONLY_TABS:
        assert not _is_summary_only(payload.get(tab, []))


def test_inspect_denies_when_session_row_missing(split_env):
    control_path, _root = split_env
    route = _seed_owned_session(
        control_path, user_id="alice-uid", session_id="alice/ip-a/rtl-gen"
    )
    uid = route.session_uid
    # Drop the sessions row but leave the manifest -> ownership unprovable -> deny.
    with AtlasDB(control_path, schema_set="full") as cdb:
        cdb._execute("DELETE FROM sessions WHERE session_uid = ?", (uid,))
        with pytest.raises(RuntimeInspectError) as exc:
            resolve_runtime_inspect_db(
                cdb, session_uid=uid, requesting_user_id="alice-uid", is_admin=True
            )
    assert exc.value.status == 404
