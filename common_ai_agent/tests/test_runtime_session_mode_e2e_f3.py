"""F3 gate — session-mode end-to-end through the REAL HTTP routes.

Plan F3 (``plans/atlas-runtime-db-100-users-v2.md``): in
``ATLAS_RUNTIME_DB_MODE=session`` drive >=2 sessions and confirm that

  1. live output ARRIVES (through the real broadcaster fan-out),
  2. the per-session RUNTIME DBs hold the queue rows,
  3. the CONTROL DB ``session_queue`` stays EMPTY (0 rows),
  4. rollups POPULATE the control DB, and
  5. cross-user history reads are DENIED (user B cannot read user A's session).

A live LLM is not available headless, so this is ONE cohesive integration test
that exercises the REAL plumbing end-to-end — only the worker *subprocess*
boundary is faked (a fake-alive process handle so ``manager.list_active()``
returns the sessions, exactly like ``tests/test_runtime_db_100_user_scale.py``).
EVERY other component is the genuine production object:

  * The REAL FastAPI app (``src.atlas_ui.create_app``) with a temp control DB +
    temp ``ATLAS_RUNTIME_DB_ROOT``, ``ATLAS_RUNTIME_DB_MODE=session``,
    ``ATLAS_MULTI_USER=1`` / ``ATLAS_MULTI_USER_PROC=1``.
  * The REAL ``/api/auth/register`` route to create 2 users (cookie auth; each
    ``TestClient`` keeps its own jar). One user is bootstrapped as admin via
    ``ATLAS_ADMIN_USERS`` so the REAL ``/api/admin/usage`` read route is driven.
  * The REAL ``/api/session/activate`` route to activate 2 distinct sessions —
    this mints each session's ``session_uid`` + per-session runtime DB +
    control manifest through the genuine router.
  * The REAL ``SessionProcessManager.send_input`` hot path to enqueue a prompt
    for each session (writes the ``in/prompt`` row into that session's RUNTIME
    DB via the router).
  * The REAL ``core.session_worker.SessionWorker`` / ``_OutputBatcher`` to
    simulate worker output so coalesced ``token_batch`` rows land in each
    runtime DB.
  * The REAL ``_MultiUserBridge._poll_process_outputs`` broadcaster (the manager
    built by ``create_app`` itself; we only inject fake ``_processes`` so
    ``list_active()`` sees both sessions) to deliver/expand output.
  * The REAL ``core.runtime_rollup.rollup_all_active``.

ASSERTIONS are made THROUGH the real HTTP read routes wherever a route exists:
  * ``GET /api/session/history`` returns each session's RUNTIME-DB message rows
    (``source == "db"``), proving the read path is routed to the runtime file.
  * ``GET /api/admin/usage`` (runtime mode) returns rollup-sourced
    ``cost_by_context`` rows — populated from the CONTROL-DB rollups.
  * ``GET /api/session/history`` for user B against user A's namespace is 403.
  * The CONTROL DB file is read with a raw sqlite3 connection (not AtlasDB) to
    prove 0 ``session_queue`` rows physically live there.

Run::

    ATLAS_RUNTIME_DB_MODE=session ATLAS_MULTI_USER=1 \
        PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
        python3 -m pytest tests/test_runtime_session_mode_e2e_f3.py -q
"""

from __future__ import annotations

import queue as _queue
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))


# --------------------------------------------------------------------------- #
# Test-only fake process handle (NO production-code change). Injected into the
# REAL SessionProcessManager so list_active()/is_alive() see the sessions —
# identical seam to tests/test_runtime_db_100_user_scale.py. The queue I/O is
# the genuine router-routed AtlasDB path; only the subprocess is faked.
# --------------------------------------------------------------------------- #


class _FakeAliveProc:
    """Stand-in for ``subprocess.Popen``: always reports alive (poll()->None)."""

    def __init__(self, pid: int = 0) -> None:
        self.pid = pid

    def poll(self) -> Optional[int]:
        return None  # None == still running, per SessionProcessManager.

    def terminate(self) -> None:  # pragma: no cover - duck-type completeness
        pass

    def wait(self, timeout: Optional[float] = None) -> int:  # pragma: no cover
        return 0


def _inject_fake_process(manager: Any, session_id: str) -> None:
    """Register a fake-alive process so ``manager.list_active()`` includes it."""
    with manager._lock:  # the real manager lock guarding _processes
        manager._processes[session_id] = {
            "proc": _FakeAliveProc(),
            "started_at": time.time(),
        }


def _drain_outbox(session: Any) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    while True:
        try:
            out.append(session._outbox.get_nowait())
        except _queue.Empty:
            break
    return out


def _register(client: TestClient, username: str) -> Dict[str, Any]:
    resp = client.post(
        "/api/auth/register",
        json={"username": username, "password": "pw"},
    )
    assert resp.status_code == 200, f"register {username}: {resp.status_code} {resp.text}"
    return resp.json()


def _activate(client: TestClient, owner: str, ip: str, workflow: str):
    return client.post(
        "/api/session/activate",
        json={"session_id": owner, "ip": ip, "workflow": workflow},
    )


def _control_session_queue_count(control_path: str) -> int:
    """Count ``session_queue`` rows physically in the CONTROL DB file.

    Opened with a raw sqlite3 connection (NOT AtlasDB) so we read exactly what
    is on disk in the control file. A missing table => definitively 0 there.
    """
    conn = sqlite3.connect(control_path)
    try:
        row = conn.execute("SELECT COUNT(*) FROM session_queue").fetchone()
        return int(row[0]) if row else 0
    except sqlite3.OperationalError:
        return 0
    finally:
        conn.close()


def test_runtime_session_mode_e2e_f3(tmp_path, monkeypatch):
    # tmp_path may sit under a symlinked /tmp (macOS /tmp -> /private/tmp); the
    # history route resolves PROJECT_ROOT/.session and then does relative_to(
    # PROJECT_ROOT), so PROJECT_ROOT must be the RESOLVED path or that fails.
    tmp = tmp_path.resolve()
    control_path = str(tmp / "atlas.db")
    runtime_root = str(tmp / "runtime")

    # --- Configure the REAL app for session mode + multi-user (process mode) --
    monkeypatch.setenv("HOME", str(tmp / "home"))
    monkeypatch.setenv("ATLAS_DB_PATH", control_path)
    monkeypatch.setenv("ATLAS_CONTROL_DB_PATH", control_path)
    monkeypatch.setenv("ATLAS_RUNTIME_DB_ROOT", runtime_root)
    monkeypatch.setenv("ATLAS_RUNTIME_DB_MODE", "session")
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "1")
    monkeypatch.setenv("ATLAS_STRICT_SESSION_ROUTING", "0")
    monkeypatch.setenv("ATLAS_ORCHESTRATOR_MODE", "0")
    # Do not scan host processes for orphan workers (no real subprocesses).
    monkeypatch.setenv("ATLAS_SESSION_WORKER_PRUNE_ORPHANS", "0")
    # Bootstrap `alice` as admin via the real role path so the REAL
    # /api/admin/usage route is reachable; disable the fixed default-admin so
    # registering a fresh username is not blocked.
    monkeypatch.setenv("ATLAS_ADMIN_USERS", "alice")
    monkeypatch.setenv("ATLAS_DEFAULT_ADMIN_ENABLED", "0")
    monkeypatch.chdir(tmp)

    import src.atlas_ui as atlas_ui
    from core.atlas_db_router import AtlasDBRouter
    from core.session_worker import SessionWorker
    from core import runtime_rollup

    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp)
    monkeypatch.setattr(atlas_ui, "SOURCE_ROOT", tmp)

    app = atlas_ui.create_app()

    # The app builds its own REAL SessionProcessManager (process mode). It MUST
    # be in session mode and bound to our temp control DB (router reads env at
    # call time). This is the genuine production object — we never swap it.
    bridge = app.state.bridge
    manager = bridge._process_manager
    assert manager is not None, "process-mode bridge must build a real manager"
    assert manager._router.mode() == "session", "router must be in session mode"
    assert (
        Path(manager._router.control_db_path()).resolve() == Path(control_path).resolve()
    ), "manager router must use the temp control DB"

    # A separate router pinned to the same temp paths for our direct on-disk
    # verification reads (rollup_all_active + raw runtime DB inspection).
    router = AtlasDBRouter(
        control_path=control_path, runtime_root=runtime_root, mode="session"
    )

    # --- Register 2 users (REAL /api/auth/register, cookie-per-client) --------
    alice = TestClient(app)  # admin (ATLAS_ADMIN_USERS=alice)
    bob = TestClient(app)    # plain user
    alice_user = _register(alice, "alice")
    bob_user = _register(bob, "bob")
    assert alice_user["user"]["role"] == "admin", alice_user
    assert bob_user["user"]["role"] != "admin", bob_user

    # --- Activate 2 distinct sessions (REAL /api/session/activate) ------------
    # This mints each session's uid + per-session runtime DB + control manifest.
    SA = "alice/ip_alpha/rtl-gen"
    SB = "bob/ip_beta/rtl-gen"
    ra = _activate(alice, "alice", "ip_alpha", "rtl-gen")
    rb = _activate(bob, "bob", "ip_beta", "rtl-gen")
    assert ra.status_code == 200, ra.text
    assert rb.status_code == 200, rb.text
    pa, pb = ra.json(), rb.json()
    assert pa["db_session_id"] == SA, pa
    assert pb["db_session_id"] == SB, pb
    uid_a = pa.get("session_uid")
    uid_b = pb.get("session_uid")
    assert uid_a and uid_b and uid_a != uid_b, (uid_a, uid_b)

    # Each activation resolves to a per-session runtime shard path distinct from
    # the control DB and from each other. The control MANIFEST row and the .db
    # FILE are both materialized lazily on the first runtime WRITE (send_input /
    # worker output below), so we only assert the routed paths here and verify
    # the manifest + file after the writes have happened.
    route_a = router.runtime_route(SA, create=False)
    route_b = router.runtime_route(SB, create=False)
    assert route_a.runtime_db_path != route_b.runtime_db_path
    assert route_a.runtime_db_path != control_path
    assert route_b.runtime_db_path != control_path

    # --- Mark both sessions alive so the broadcaster fan-out includes them ----
    _inject_fake_process(manager, SA)
    _inject_fake_process(manager, SB)
    assert sorted(manager.list_active()) == sorted([SA, SB]), manager.list_active()

    # --- Enqueue a prompt for each via the REAL manager.send_input -----------
    # Routes through the genuine router -> writes the in/prompt row into that
    # session's RUNTIME DB (NOT the control DB).
    prompt_id_a = manager.send_input(SA, "prompt", {"text": "F3 prompt alice"})
    prompt_id_b = manager.send_input(SB, "prompt", {"text": "F3 prompt bob"})
    assert prompt_id_a, "send_input(A) returned no id (session not alive?)"
    assert prompt_id_b, "send_input(B) returned no id (session not alive?)"

    # --- Simulate worker output via the REAL _OutputBatcher ------------------
    # The SessionWorker funnels token emits through _OutputBatcher into coalesced
    # token_batch rows in each session's runtime queue. We ALSO write a
    # messages/parts row into the runtime DB so the history read route has
    # runtime-resident conversation rows to surface (the live worker writes both
    # session_queue out-rows AND messages/parts to the same runtime file).
    TOKENS_PER_STREAM = 8
    expected_tokens: Dict[str, str] = {}
    runtime_msg_text: Dict[str, str] = {}
    for sid in (SA, SB):
        route = router.runtime_route(sid, create=True)
        worker = SessionWorker(session_id=sid, db_path=route.runtime_db_path)
        try:
            expected = ""
            for i in range(TOKENS_PER_STREAM):
                chunk = f"{sid[0]}tok{i}|"
                worker.emit_content(chunk)
                expected += chunk
            worker.flush_batcher()  # coalesce into token_batch row(s)
        finally:
            worker.close()
        expected_tokens[sid] = expected
        # Conversation message rows in the SAME runtime DB (read by history).
        rdb = router.runtime_db(sid, create=True)
        try:
            text = f"runtime-conversation::{sid}"
            msg = rdb.save_message(sid, "assistant")
            rdb.save_part(msg["id"], sid, "text", text=text)
        finally:
            rdb.close()
        runtime_msg_text[sid] = text

    # The token emits coalesced into far fewer batch rows than chunks.
    for sid in (SA, SB):
        route = router.runtime_route(sid, create=False)
        rdb = router.runtime_db(sid, create=False)
        try:
            row = rdb._fetchone(
                "SELECT COUNT(*) AS n FROM session_queue "
                "WHERE direction='out' AND msg_type='token_batch'"
            )
            n_batch = int(dict(row)["n"]) if row else 0
        finally:
            rdb.close()
        assert 0 < n_batch < TOKENS_PER_STREAM, (
            f"{sid}: token coalescing produced {n_batch} batch rows "
            f"for {TOKENS_PER_STREAM} chunks"
        )

    # After the writes, each session's per-session runtime DB FILE physically
    # exists under the runtime root, and the control DB carries a manifest row
    # pointing at it (written by the router on the first create=True open).
    assert Path(route_a.runtime_db_path).is_file(), route_a.runtime_db_path
    assert Path(route_b.runtime_db_path).is_file(), route_b.runtime_db_path
    control = router.control_db()
    try:
        man_a = control.get_session_runtime_db(SA)
        man_b = control.get_session_runtime_db(SB)
    finally:
        control.close()
    assert man_a and man_a.get("session_uid") == uid_a, man_a
    assert man_b and man_b.get("session_uid") == uid_b, man_b

    # --- Drive the REAL broadcaster: live output must ARRIVE ------------------
    # Repeatedly call the genuine _poll_process_outputs loop (it iterates
    # manager.list_active(), polls each runtime DB via the router, expands
    # token_batch back to per-token events) until every session's tokens are
    # delivered to its outbox.
    delivered: Dict[str, List[Dict[str, Any]]] = {SA: [], SB: []}

    def _harvest() -> None:
        for sid in (SA, SB):
            for evt in _drain_outbox(bridge.get_session(sid)):
                delivered.setdefault(str(evt.get("session_id") or sid), []).append(evt)

    def _all_tokens_in() -> bool:
        for sid in (SA, SB):
            got = "".join(
                str(e.get("text") or "")
                for e in delivered.get(sid, [])
                if e.get("type") == "token"
            )
            if expected_tokens[sid] not in got:
                return False
        return True

    deadline = time.monotonic() + 30.0
    polls = 0
    while time.monotonic() < deadline:
        bridge._poll_process_outputs()
        polls += 1
        _harvest()
        if _all_tokens_in() and polls >= 2:
            break

    # F3 (1): LIVE OUTPUT ARRIVED through the real broadcaster, in order.
    for sid in (SA, SB):
        got_tokens = "".join(
            str(e.get("text") or "")
            for e in delivered.get(sid, [])
            if e.get("type") == "token"
        )
        assert expected_tokens[sid] in got_tokens, (
            f"{sid}: emitted tokens did not arrive through broadcaster; "
            f"want substring {expected_tokens[sid]!r}, got {got_tokens!r}"
        )

    # --- F3 (2): runtime DBs hold the queue rows -----------------------------
    # Each runtime DB has the in/prompt row (matching the enqueued id) AND the
    # out token_batch rows, and NO foreign-session rows.
    prompt_ids = {SA: prompt_id_a, SB: prompt_id_b}
    for sid in (SA, SB):
        rdb = router.runtime_db(sid, create=False)
        try:
            in_rows = rdb._fetchall(
                "SELECT id FROM session_queue "
                "WHERE session_id=? AND direction='in' AND msg_type='prompt'",
                (sid,),
            )
            out_rows = rdb._fetchone(
                "SELECT COUNT(*) AS n FROM session_queue WHERE direction='out'"
            )
            foreign = rdb._fetchone(
                "SELECT COUNT(*) AS n FROM session_queue WHERE session_id != ?",
                (sid,),
            )
        finally:
            rdb.close()
        assert len(in_rows) == 1, f"{sid}: expected 1 prompt row, got {len(in_rows)}"
        assert str(in_rows[0]["id"]) == str(prompt_ids[sid]), (
            f"{sid}: runtime prompt id != enqueued id"
        )
        assert int(dict(out_rows)["n"]) > 0, f"{sid}: no out rows in runtime DB"
        assert int(dict(foreign)["n"]) == 0, f"{sid}: cross-session rows present"

    # --- F3 (3): the CONTROL DB session_queue stays EMPTY --------------------
    control_queue_rows = _control_session_queue_count(control_path)
    assert control_queue_rows == 0, (
        f"control DB must hold 0 session_queue rows in session mode, "
        f"got {control_queue_rows}"
    )

    # --- F3 (4): run the REAL rollup and confirm it POPULATES the control DB --
    results = runtime_rollup.rollup_all_active(router=router)
    statuses = {r.session_id: r.status for r in results}
    assert statuses.get(SA) == "ok", f"rollup A status={statuses.get(SA)}"
    assert statuses.get(SB) == "ok", f"rollup B status={statuses.get(SB)}"

    control = router.control_db()
    try:
        rollup_rows = control.list_runtime_usage_rollups()
    finally:
        control.close()
    rollup_by_uid = {str(r.get("session_uid")): r for r in rollup_rows}
    assert uid_a in rollup_by_uid, f"no control rollup for session A uid={uid_a}"
    assert uid_b in rollup_by_uid, f"no control rollup for session B uid={uid_b}"
    for uid, sid in ((uid_a, SA), (uid_b, SB)):
        r = rollup_by_uid[uid]
        # queue_in counts the prompt we enqueued; queue_out + messages count the
        # worker's runtime writes. Each must be non-zero -> rollup folded real
        # runtime rows into the control DB.
        assert int(r.get("queue_in") or 0) >= 1, f"{sid}: rollup queue_in=0"
        assert int(r.get("queue_out") or 0) >= 1, f"{sid}: rollup queue_out=0"
        assert int(r.get("messages") or 0) >= 1, f"{sid}: rollup messages=0"

    # These rollup rows physically live in the CONTROL DB file (raw read).
    ctrl = sqlite3.connect(control_path)
    try:
        n_rollup = ctrl.execute(
            "SELECT COUNT(*) FROM runtime_usage_rollups"
        ).fetchone()[0]
    finally:
        ctrl.close()
    assert n_rollup >= 2, f"control DB runtime_usage_rollups has {n_rollup} rows"

    # --- F3 (4) via the REAL HTTP read route: admin usage shows rollups -------
    # In runtime mode /api/admin/usage sources totals from the control rollups
    # (cost_by_context). Driven as the admin user (alice).
    usage_resp = alice.get("/api/admin/usage")
    assert usage_resp.status_code == 200, usage_resp.text
    usage = usage_resp.json()
    assert usage.get("runtime_mode") is True, "admin usage not in runtime mode"
    context_sids = {str(row.get("session_id")) for row in usage.get("cost_by_context", [])}
    assert SA in context_sids, f"admin usage cost_by_context missing {SA}: {context_sids}"
    assert SB in context_sids, f"admin usage cost_by_context missing {SB}: {context_sids}"
    # A plain (non-admin) user is denied the admin read route.
    assert bob.get("/api/admin/usage").status_code == 403

    # --- F3 (1/5) via the REAL HTTP read route: history reads RUNTIME rows ----
    # Each session's /api/session/history surfaces the messages we wrote into
    # the RUNTIME DB (source=="db"), proving the read path is routed to the
    # per-session runtime file (not the control DB).
    for client, sid in ((alice, SA), (bob, SB)):
        h = client.get("/api/session/history", params={"session": sid})
        assert h.status_code == 200, h.text
        body = h.json()
        contents = [
            str(m.get("content") or m.get("text") or "") for m in body.get("messages", [])
        ]
        assert runtime_msg_text[sid] in contents, (
            f"{sid}: history did not surface the RUNTIME-DB message; "
            f"source={body.get('source')!r} contents={contents!r}"
        )
        assert "db" in str(body.get("source") or ""), (
            f"{sid}: history source {body.get('source')!r} is not DB-routed"
        )

    # --- F3 (5): cross-user history read is DENIED ---------------------------
    # User B (bob) cannot read user A's (alice's) session, and vice versa.
    assert alice.get("/api/session/history", params={"session": SA}).status_code == 200
    forbidden_b_reads_a = bob.get("/api/session/history", params={"session": SA})
    forbidden_a_reads_b = alice.get("/api/session/history", params={"session": SB})
    assert forbidden_b_reads_a.status_code == 403, forbidden_b_reads_a.text
    assert forbidden_a_reads_b.status_code == 403, forbidden_a_reads_b.text

    # Belt-and-suspenders: the control DB never accumulated queue rows during the
    # whole flow (re-check after rollup, which only READS the runtime files).
    assert _control_session_queue_count(control_path) == 0
