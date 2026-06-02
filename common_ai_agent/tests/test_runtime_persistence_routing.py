"""Task 6 — route runtime persistence (messages / trace_events / llm_calls).

Covers plan §2.10 + R16 + R17 for the WRITE side owned by Task 6:

1. A worker (ATLAS_DB_PATH=runtime, the Task-3 spawn env) writes its llm_calls
   row into the SESSION RUNTIME DB; the CONTROL DB sees 0 worker rows.
2. A session-scoped llm_calls write from the ORCHESTRATOR (a concrete
   ctx.session_id) lands in the session's RUNTIME DB in session mode, routed via
   the AtlasDBRouter — not the control AtlasDB.
3. Room CHAT (chat_message / chat_consumed) stays in the CONTROL DB even when the
   calling AtlasDB is bound to a runtime file (R17 write-time predicate).
4. CENTRAL mode (default): every write lands on the control DB exactly as today
   (the predicate is a no-op).
5. A headless worker in SESSION mode with NO resolvable session SURFACES a
   routing failure instead of silently writing an unroutable session_id='' row
   (R16) — and in CENTRAL mode the empty session stays historically valid.

The tests pin the routing CONTRACT directly against AtlasDB / AtlasDBRouter /
the headless resolver, so they are fast and do not need a live UI or a real
subprocess.
"""

from __future__ import annotations

import pytest

from core.atlas_db import AtlasDB
from core.atlas_db_router import AtlasDBRouter


# --------------------------------------------------------------------------- #
# Shared fixtures / helpers
# --------------------------------------------------------------------------- #


@pytest.fixture
def split_env(tmp_path, monkeypatch):
    """Configure an explicit control DB + runtime root in SESSION mode.

    Returns (control_path, runtime_root). The router reads these envs at call
    time, so a test can flip ATLAS_RUNTIME_DB_MODE afterwards.
    """
    control_path = str(tmp_path / "atlas.db")
    runtime_root = str(tmp_path / "runtime")
    monkeypatch.setenv("ATLAS_CONTROL_DB_PATH", control_path)
    monkeypatch.setenv("ATLAS_RUNTIME_DB_ROOT", runtime_root)
    monkeypatch.setenv("ATLAS_RUNTIME_DB_MODE", "session")
    # Initialize the control DB (full schema) up front.
    AtlasDB(control_path, schema_set="full").close()
    return control_path, runtime_root


def _seed_session(control_path: str, session_id: str) -> str:
    """Create a session row with a minted session_uid; return the runtime path."""
    with AtlasDB(control_path, schema_set="full") as db:
        db.upsert_runtime_session(
            session_id,
            user_id="u-test",
            ip_id="ip-test",
            workflow="rtl-gen",
        )
    route = AtlasDBRouter().runtime_route(session_id, create=True)
    return route.runtime_db_path


def _count_llm_calls(db_path: str, schema_set: str, session_id: str) -> int:
    with AtlasDB(db_path, schema_set=schema_set) as db:
        rows = db._execute(
            "SELECT COUNT(*) AS n FROM llm_calls WHERE session_id = ?",
            (session_id,),
        ).fetchone()
    return int(dict(rows)["n"])


# --------------------------------------------------------------------------- #
# 1. Worker llm_calls land in the runtime DB; control count 0.
# --------------------------------------------------------------------------- #


def test_worker_llm_calls_land_in_runtime_not_control(split_env, monkeypatch):
    control_path, _root = split_env
    session_id = "u-test/ip-test/rtl-gen"
    runtime_path = _seed_session(control_path, session_id)

    # Task-3 spawn env: the worker's ATLAS_DB_PATH IS the runtime file. A plain
    # AtlasDB() inside the worker therefore writes llm_calls to the runtime DB.
    monkeypatch.setenv("ATLAS_DB_PATH", runtime_path)
    monkeypatch.setenv("ATLAS_ACTIVE_SESSION", session_id)

    with AtlasDB(runtime_path, schema_set="runtime") as wdb:
        wdb.record_llm_call(
            session_id=session_id,
            ip_id="ip-test",
            workflow="rtl-gen",
            model="claude-opus-4-7",
            call_role="worker",
            tokens_input=1000,
            tokens_output=200,
        )

    # Runtime DB has the worker row.
    assert _count_llm_calls(runtime_path, "runtime", session_id) == 1
    # Control DB has ZERO worker rows for this session.
    assert _count_llm_calls(control_path, "full", session_id) == 0


# --------------------------------------------------------------------------- #
# 2. Session-scoped trace from the orchestrator (ctx.session_id) -> runtime.
# --------------------------------------------------------------------------- #


def test_orchestrator_session_scoped_write_routes_to_runtime(split_env):
    from src.orchestrator.react_bridge import _runtime_db_for_session

    control_path, _root = split_env
    session_id = "u-test/ip-test/rtl-gen"
    runtime_path = _seed_session(control_path, session_id)

    control_db = AtlasDB(control_path, schema_set="full")
    try:
        # The orchestrator routes its session-scoped accounting through the
        # router: a concrete session_id in session mode -> the runtime DB.
        with _runtime_db_for_session(control_db, session_id) as acct_db:
            assert acct_db.db_path != control_db.db_path
            acct_db.record_llm_call(
                session_id=session_id,
                run_id="run-1",
                ip_id="ip-test",
                workflow="orchestrator",
                call_role="orchestrator",
                tokens_input=50,
                tokens_output=10,
            )
            # A session-scoped trace event lands in the same runtime file.
            acct_db.record_trace_event(
                event_type="orchestrator_step",
                payload={"k": "v"},
                session_id=session_id,
                run_id="run-1",
            )
    finally:
        control_db.close()

    assert _count_llm_calls(runtime_path, "runtime", session_id) == 1
    assert _count_llm_calls(control_path, "full", session_id) == 0

    with AtlasDB(runtime_path, schema_set="runtime") as rdb:
        traces = rdb.list_trace_events(session_id=session_id)
    assert any(t["event_type"] == "orchestrator_step" for t in traces)

    # The control DB holds no orchestrator_step trace for this session.
    with AtlasDB(control_path, schema_set="full") as cdb:
        ctrl_traces = cdb.list_trace_events(session_id=session_id)
    assert not any(t["event_type"] == "orchestrator_step" for t in ctrl_traces)


def test_orchestrator_no_session_uses_control(split_env):
    """No session_id -> the orchestrator keeps writing to the control db."""
    from src.orchestrator.react_bridge import _runtime_db_for_session

    control_path, _root = split_env
    control_db = AtlasDB(control_path, schema_set="full")
    try:
        target = _runtime_db_for_session(control_db, "")
        assert target is control_db
    finally:
        control_db.close()


# --------------------------------------------------------------------------- #
# 3. Room chat stays in control even when the caller is on a runtime file (R17).
# --------------------------------------------------------------------------- #


def test_chat_message_stays_in_control_from_runtime_db(split_env):
    control_path, _root = split_env
    session_id = "u-test/ip-test/rtl-gen"
    runtime_path = _seed_session(control_path, session_id)

    # A worker bound to its runtime file posts a chat message. The write-time
    # predicate must re-route it to the CONTROL DB (room chat is not session
    # scoped and the chat ledger must be a single-DB join).
    with AtlasDB(runtime_path, schema_set="runtime") as wdb:
        wdb.record_chat_message(
            ip_id="ip-test",
            user_id="u-test",
            content="hello from worker",
        )
        # chat_consumed (the read watermark for the SAME ledger) must co-locate.
        wdb.record_chat_consumed(
            chat_id="x", session_id=session_id, ip_id="ip-test"
        )

    # Control DB sees both chat rows.
    with AtlasDB(control_path, schema_set="full") as cdb:
        msgs = cdb.list_chat_messages("ip-test", limit=10)
        consumed = cdb.list_trace_events(session_id=session_id)
    assert [m["payload"]["content"] for m in msgs] == ["hello from worker"]
    assert any(t["event_type"] == "chat_consumed" for t in consumed)

    # Runtime DB has NO chat rows.
    with AtlasDB(runtime_path, schema_set="runtime") as rdb:
        rt_chat = rdb._execute(
            "SELECT COUNT(*) AS n FROM trace_events "
            "WHERE event_type IN ('chat_message', 'chat_consumed')"
        ).fetchone()
    assert int(dict(rt_chat)["n"]) == 0


def test_global_room_chat_stays_in_control_from_runtime_db(split_env):
    control_path, _root = split_env
    session_id = "u-test/ip-test/rtl-gen"
    runtime_path = _seed_session(control_path, session_id)

    with AtlasDB(runtime_path, schema_set="runtime") as wdb:
        wdb.record_chat_message(
            ip_id=None,  # global room
            user_id="u-test",
            content="global note",
        )

    with AtlasDB(control_path, schema_set="full") as cdb:
        msgs = cdb.list_chat_messages(None, limit=10)
    assert [m["payload"]["content"] for m in msgs] == ["global note"]


# --------------------------------------------------------------------------- #
# 4. Central mode: everything goes to control exactly as today.
# --------------------------------------------------------------------------- #


def test_central_mode_chat_and_trace_write_in_place(tmp_path, monkeypatch):
    monkeypatch.setenv("ATLAS_RUNTIME_DB_MODE", "central")
    # No ATLAS_CONTROL_DB_PATH: the predicate must NOT re-route to an env default
    # and must write in place on the explicitly-opened db (today's behavior).
    monkeypatch.delenv("ATLAS_CONTROL_DB_PATH", raising=False)
    monkeypatch.delenv("ATLAS_DB_PATH", raising=False)

    db_path = str(tmp_path / "explicit.db")
    with AtlasDB(db_path, schema_set="full") as db:
        db.record_chat_message(ip_id="ip-c", user_id="u", content="central chat")
        db.record_trace_event(
            event_type="workflow_event",
            session_id="s-central",
            payload={"x": 1},
        )
        db.record_llm_call(session_id="s-central", call_role="worker", tokens_input=5)

    # All three landed in the SAME explicit db (no re-route, no env default).
    with AtlasDB(db_path, schema_set="full") as db:
        assert [m["payload"]["content"] for m in db.list_chat_messages("ip-c")] == [
            "central chat"
        ]
        assert len(db.list_trace_events(session_id="s-central")) == 1
        assert len(db.list_llm_calls(session_id="s-central")) == 1


def test_central_mode_orchestrator_uses_control_db(tmp_path, monkeypatch):
    from src.orchestrator.react_bridge import _runtime_db_for_session

    monkeypatch.setenv("ATLAS_RUNTIME_DB_MODE", "central")
    db_path = str(tmp_path / "control.db")
    control_db = AtlasDB(db_path, schema_set="full")
    try:
        # Even with a concrete session_id, central mode keeps writes on control.
        target = _runtime_db_for_session(control_db, "u/ip/wf")
        assert target is control_db
    finally:
        control_db.close()


# --------------------------------------------------------------------------- #
# 5. Headless worker with no resolvable session: failure is surfaced (R16).
# --------------------------------------------------------------------------- #


def test_headless_no_session_in_session_mode_raises(monkeypatch):
    from src.headless_workflow import (
        WorkerSessionRoutingError,
        _resolve_worker_accounting_session,
    )

    monkeypatch.setenv("ATLAS_RUNTIME_DB_MODE", "session")
    monkeypatch.delenv("ATLAS_ACTIVE_SESSION", raising=False)
    monkeypatch.delenv("ATLAS_SESSION_ID", raising=False)

    with pytest.raises(WorkerSessionRoutingError):
        _resolve_worker_accounting_session()


def test_headless_resolves_session_from_active_session_env(monkeypatch):
    from src.headless_workflow import _resolve_worker_accounting_session

    monkeypatch.setenv("ATLAS_RUNTIME_DB_MODE", "session")
    # build_worker_env sets ATLAS_ACTIVE_SESSION, NOT ATLAS_SESSION_ID.
    monkeypatch.setenv("ATLAS_ACTIVE_SESSION", "u/ip/rtl-gen")
    monkeypatch.delenv("ATLAS_SESSION_ID", raising=False)

    assert _resolve_worker_accounting_session() == "u/ip/rtl-gen"


def test_headless_central_mode_allows_empty_session(monkeypatch):
    from src.headless_workflow import _resolve_worker_accounting_session

    monkeypatch.setenv("ATLAS_RUNTIME_DB_MODE", "central")
    monkeypatch.delenv("ATLAS_ACTIVE_SESSION", raising=False)
    monkeypatch.delenv("ATLAS_SESSION_ID", raising=False)

    # Central mode: an empty session is historically valid, not an error.
    assert _resolve_worker_accounting_session() == ""


def test_headless_prefers_active_session_over_legacy_session_id(monkeypatch):
    from src.headless_workflow import _resolve_worker_session_id

    monkeypatch.setenv("ATLAS_ACTIVE_SESSION", "active/ip/wf")
    monkeypatch.setenv("ATLAS_SESSION_ID", "legacy-id")
    assert _resolve_worker_session_id() == "active/ip/wf"
