"""Task 10 — 100-session runtime-DB verification harness (plan §4 Task 10).

GOAL (plan §4 Task 10 / R6): PROVE the SLA on the REAL broadcaster path, NOT the
DB floor. Calling ``AtlasDB`` directly measures the single-file write floor; the
production cost is the SERIAL broadcaster fan-out (``_MultiUserBridge.
_poll_process_outputs`` iterating ``manager.list_active()`` one session at a time,
plan §2.7 / R3) plus the hot-path connection reuse (plan §2.6 / R2). So this
harness drives the genuine ``SessionProcessManager`` + ``_MultiUserBridge`` poll
loop, with FAKE ``_processes`` injected so ``list_active()`` returns all 100
sessions (R6) — no real LLM and no 100 real subprocesses in default CI.

What is exercised end-to-end (all REAL production code, only the subprocess
boundary faked):

* Router mints a uid + per-session runtime DB for each of 100 sessions
  (``user000/ip000/rtl-gen`` .. ``user099/ip099/rtl-gen``).
* 100 concurrent prompt enqueues (threads) inside one 60s window through the
  REAL ``SessionProcessManager.send_input`` hot path (per-(thread,path) handle
  reuse, the locked-retry budget) — per-enqueue latency measured.
* 100 synthetic output streams, each 200 ``token`` + 10 ``reasoning`` chunks,
  produced THROUGH the worker ``_OutputBatcher`` (``core.session_worker``) so
  real ``token_batch`` / ``reasoning_batch`` rows land in each session's runtime
  queue (coalescing exercised).
* The REAL broadcaster: ``bridge._poll_process_outputs()`` (a) iterates all 100
  sessions SERIALLY (R3), (b) reuses the long-lived per-(thread,path) connection
  (R2 — asserted ~0 new ``sqlite3.connect`` calls in steady state), (c) expands
  ``token_batch`` / ``reasoning_batch`` back to per-event outbox items, (d)
  advances the value-based cursor and marks out-rows delivered. Per-poll latency
  measured HERE (through the real path), never via a direct AtlasDB read.
* ``rollup_all_active`` after streams complete; rollup lag measured.

ASSERTIONS (collected MEASURED values, never sleep-for-pass):

* p95 enqueue <= 250ms; p95 poll <= 500ms (through the real bridge).
* zero lost prompts: every enqueued prompt is consumed exactly once.
* zero cross-session rows: each runtime DB holds ONLY its own session rows;
  control DB holds 0 ``session_queue`` rows.
* zero 'database is locked' (``fleet_health().locked_retry_count == 0`` AND no
  exception raised anywhere).
* [R5] per-session sum(expanded polled token text) == sum(emitted token text).
* rollup totals == raw runtime totals; rollup lag <= 10s.
* [R19] COLD-SPAWN p95 (runtime schema bootstrap + first enqueue) recorded as a
  SEPARATE metric.

All measured metrics are written to ``evidence/task10-100-session-scale.json``.
Latency thresholds are environment-sensitive: the test asserts the plan numbers
but ALSO always records the measured value so a slow CI box is debuggable.

An OPTIONAL env-gated real-subprocess smoke
(``ATLAS_RUNTIME_DB_REAL_SUBPROCESS_STRESS=1``, >=10 real subprocesses) is the
AUTHORITATIVE ``--db-path`` co-location check: each worker's ``session_queue``
AND its ``llm_calls`` / ``trace_events`` land in the SAME per-session runtime DB.
Skipped by default.

Run (default, no real subprocesses)::

    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
        python3 -m pytest tests/test_runtime_db_100_user_scale.py -q
"""

from __future__ import annotations

import json
import os
import queue
import sqlite3
import statistics
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from core.atlas_db import AtlasDB  # noqa: E402
from core.atlas_db_router import AtlasDBRouter  # noqa: E402
from core.session_process_manager import SessionProcessManager  # noqa: E402
from core.session_worker import SessionWorker  # noqa: E402
import core.atlas_multiuser as atlas_multiuser  # noqa: E402
from core import runtime_rollup  # noqa: E402


# Workload knobs (plan §4 Task 10).
N_SESSIONS = 100
TOKENS_PER_STREAM = 200
REASONING_PER_STREAM = 10
ENQUEUE_WINDOW_S = 60.0

# SLA thresholds (plan §4 Task 10 / line 199). Environment-sensitive: asserted
# AND always recorded so a slow box is debuggable.
P95_ENQUEUE_MS = 250.0
P95_POLL_MS = 500.0
ROLLUP_LAG_TARGET_S = runtime_rollup.ROLLUP_LAG_TARGET_S  # 10s


# --------------------------------------------------------------------------- #
# Test-only fake process plumbing (NO production-code change — R6).
#
# We inject these into a REAL SessionProcessManager / _MultiUserBridge so the
# genuine serial-fan-out + connection-reuse paths run, but without spawning 100
# real subprocesses. The fake is a process *handle* only: list_active() reads
# entry["proc"].poll() (None == alive); the queue I/O is the real AtlasDB path.
# --------------------------------------------------------------------------- #


class _FakeAliveProc:
    """Stand-in for ``subprocess.Popen``: always reports alive (poll()->None)."""

    def __init__(self, pid: int = 0) -> None:
        self.pid = pid

    def poll(self) -> Optional[int]:
        return None  # None == still running, per SessionProcessManager.

    # Defensive: never actually used in this harness, but keeps the duck type
    # complete if a code path probes terminate()/wait().
    def terminate(self) -> None:  # pragma: no cover - not exercised
        pass

    def wait(self, timeout: Optional[float] = None) -> int:  # pragma: no cover
        return 0


def _build_bridge_with_real_manager(
    manager: SessionProcessManager,
) -> atlas_multiuser._MultiUserBridge:
    """Build a real ``_MultiUserBridge`` bound to *manager* (R6 drive surface).

    We bypass ``__init__`` (which would build its own SessionProcessManager) and
    wire the SAME private fields ``__init__`` sets, then inject the real,
    fake-process-populated manager. Every method we drive
    (``_poll_process_outputs``, ``_ensure_session``, ``get_session``,
    ``next_event``) is the genuine production implementation.
    """
    bridge = atlas_multiuser._MultiUserBridge.__new__(
        atlas_multiuser._MultiUserBridge
    )
    bridge._sessions = {}
    bridge._sessions_lock = threading.RLock()
    bridge._single_user = False
    bridge._strict_session_routing = False
    bridge._single_worker_per_owner = False
    bridge._owner_active_sessions = {}
    bridge._active_session_id = "default"
    bridge._active_lock = threading.Lock()
    bridge._agent_starter = None
    bridge._process_manager = manager
    bridge._process_output_cursors = {}
    bridge._default_session = bridge._ensure_session("default")
    return bridge


def _inject_fake_process(manager: SessionProcessManager, session_id: str) -> None:
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
        except queue.Empty:
            break
    return out


def _pct(values: List[float], pct: float) -> float:
    """Nearest-rank percentile (deterministic, no interpolation surprises)."""
    if not values:
        return 0.0
    ordered = sorted(values)
    if pct <= 0:
        return ordered[0]
    if pct >= 100:
        return ordered[-1]
    rank = int(round((pct / 100.0) * len(ordered) + 0.5)) - 1
    rank = max(0, min(rank, len(ordered) - 1))
    return ordered[rank]


def _latency_block(values_ms: List[float]) -> Dict[str, float]:
    if not values_ms:
        return {"count": 0, "p50": 0.0, "p95": 0.0, "p99": 0.0, "max": 0.0}
    return {
        "count": len(values_ms),
        "p50": round(_pct(values_ms, 50), 3),
        "p95": round(_pct(values_ms, 95), 3),
        "p99": round(_pct(values_ms, 99), 3),
        "max": round(max(values_ms), 3),
        "mean": round(statistics.fmean(values_ms), 3),
    }


def _session_ids(n: int) -> List[str]:
    return [f"user{i:03d}/ip{i:03d}/rtl-gen" for i in range(n)]


def _control_session_queue_count(control_path: str) -> int:
    """Count ``session_queue`` rows physically in the CONTROL DB file.

    Opened with a raw sqlite3 connection (NOT AtlasDB) so we read exactly what
    is on disk in the control file, asserting nothing leaked there in session
    mode (plan §4 Task 10: control DB has 0 session_queue rows).
    """
    conn = sqlite3.connect(control_path)
    try:
        row = conn.execute("SELECT COUNT(*) FROM session_queue").fetchone()
        return int(row[0]) if row else 0
    except sqlite3.OperationalError:
        # Table absent in control file => definitively zero queue rows there.
        return 0
    finally:
        conn.close()


def _control_manifest_updated_at(control_path: str) -> Dict[str, float]:
    """Snapshot ``session_runtime_dbs.updated_at`` for every manifest row.

    Read with a RAW sqlite3 connection straight off the control file on disk
    (NOT AtlasDB / NOT the router cache) so we observe exactly what was last
    persisted. ``updated_at`` is bumped only by ``upsert_session_runtime_db``
    (manifest create/refresh). A flat snapshot across repeated polls is the
    on-disk proof that the hot poll path did not re-upsert the manifest, i.e.
    did not write the Control DB (feedback #1 / Task 10 steady-state assertion).
    """
    conn = sqlite3.connect(control_path)
    try:
        rows = conn.execute(
            "SELECT session_id, updated_at FROM session_runtime_dbs"
        ).fetchall()
        return {str(r[0]): float(r[1]) for r in rows}
    except sqlite3.OperationalError:
        # Manifest table absent => no rows to snapshot.
        return {}
    finally:
        conn.close()


# --------------------------------------------------------------------------- #
# Fixture: isolated session-mode environment (temp control DB + runtime root).
# --------------------------------------------------------------------------- #


@pytest.fixture()
def session_mode_env(tmp_path, monkeypatch):
    """Configure ATLAS_RUNTIME_DB_MODE=session with temp control + runtime root."""
    control_path = str(tmp_path / "control" / "atlas.db")
    runtime_root = str(tmp_path / "runtime")
    Path(control_path).parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("ATLAS_CONTROL_DB_PATH", control_path)
    monkeypatch.setenv("ATLAS_DB_PATH", control_path)
    monkeypatch.setenv("ATLAS_RUNTIME_DB_ROOT", runtime_root)
    monkeypatch.setenv("ATLAS_RUNTIME_DB_MODE", "session")
    # Do NOT scan host processes for orphan workers during the synthetic run
    # (no real subprocesses exist; the ps scan is pure overhead + flakiness).
    monkeypatch.setenv("ATLAS_SESSION_WORKER_PRUNE_ORPHANS", "0")
    return {"control_path": control_path, "runtime_root": runtime_root}


# --------------------------------------------------------------------------- #
# THE harness: 100-session scale proof through the REAL bridge path.
# --------------------------------------------------------------------------- #


def test_runtime_db_100_user_scale(session_mode_env):
    control_path = session_mode_env["control_path"]
    runtime_root = session_mode_env["runtime_root"]

    router = AtlasDBRouter(
        control_path=control_path,
        runtime_root=runtime_root,
        mode="session",
    )
    manager = SessionProcessManager(db_path=control_path, router=router)
    bridge = _build_bridge_with_real_manager(manager)

    session_ids = _session_ids(N_SESSIONS)

    # Per-session expected token text (the ground truth for the R5 no-drop/no-dup
    # parity assertion). Built once, emitted through the worker batcher below.
    expected_token_text: Dict[str, str] = {}
    expected_reasoning_text: Dict[str, str] = {}
    for sid in session_ids:
        expected_token_text[sid] = "".join(
            f"t{sid[-1]}{i}|" for i in range(TOKENS_PER_STREAM)
        )
        expected_reasoning_text[sid] = "".join(
            f"r{i}|" for i in range(REASONING_PER_STREAM)
        )

    # -- Phase A: COLD-SPAWN (R19) ----------------------------------------- #
    # Cold-spawn p95 = runtime DB schema bootstrap (first router open of a brand
    # new per-session file) + the FIRST enqueue into it. Measured per session as
    # a SEPARATE metric: it is the accept-before-ready window the plan calls out.
    cold_spawn_ms: List[float] = []
    for sid in session_ids:
        t0 = time.perf_counter()
        # First runtime_route(create=True) mints the uid + manifest; first
        # runtime_db open bootstraps the 5-table runtime schema; first enqueue
        # writes the very first row. This is the full cold path.
        route = router.runtime_route(sid, create=True)
        db = router.runtime_db(sid, create=True)
        db.enqueue_message(sid, "out", "worker_started", {"pid": 0})
        cold_spawn_ms.append((time.perf_counter() - t0) * 1000.0)
        # Mark this session alive so the broadcaster fan-out includes it (R6).
        _inject_fake_process(manager, sid)
        assert route.session_uid, f"no uid minted for {sid}"

    assert sorted(manager.list_active()) == sorted(session_ids), (
        "fake _processes injection must make list_active() return all sessions "
        f"(got {len(manager.list_active())} of {N_SESSIONS})"
    )

    # -- Phase B: 100 concurrent prompt enqueues in one window (latency) ---- #
    # Through the REAL SessionProcessManager.send_input hot path: per-(thread,
    # path) handle reuse + the locked-retry budget. One prompt per session,
    # fired from 100 threads, all inside the 60s window. We measure per-enqueue
    # wall latency and assert exactly-once consumption later.
    enqueue_ms: List[float] = []
    enqueue_lock = threading.Lock()
    enqueue_errors: List[str] = []
    prompt_ids: Dict[str, str] = {}
    barrier = threading.Barrier(N_SESSIONS)
    window_start = time.monotonic()

    def _enqueue(sid: str) -> None:
        try:
            barrier.wait(timeout=30)  # release all 100 threads together
            t0 = time.perf_counter()
            msg_id = manager.send_input(sid, "prompt", {"text": f"prompt::{sid}"})
            dt = (time.perf_counter() - t0) * 1000.0
            with enqueue_lock:
                enqueue_ms.append(dt)
                if msg_id is None:
                    enqueue_errors.append(f"{sid}: send_input returned None")
                else:
                    prompt_ids[sid] = msg_id
        except Exception as exc:  # captured, never sleep-for-pass
            with enqueue_lock:
                enqueue_errors.append(f"{sid}: {type(exc).__name__}: {exc}")

    threads = [threading.Thread(target=_enqueue, args=(sid,)) for sid in session_ids]
    for th in threads:
        th.start()
    for th in threads:
        th.join(timeout=ENQUEUE_WINDOW_S)
    window_elapsed = time.monotonic() - window_start

    assert not enqueue_errors, f"enqueue errors: {enqueue_errors[:10]}"
    assert window_elapsed <= ENQUEUE_WINDOW_S, (
        f"enqueue window exceeded 60s: {window_elapsed:.1f}s"
    )
    assert len(prompt_ids) == N_SESSIONS, (
        f"expected {N_SESSIONS} prompts enqueued, got {len(prompt_ids)}"
    )

    # -- Phase C: 100 synthetic output streams THROUGH the worker batcher --- #
    # Each session gets a real SessionWorker whose _OutputBatcher coalesces the
    # token/reasoning emits into token_batch / reasoning_batch rows in that
    # session's runtime queue (exercises coalescing). Run concurrently to stress
    # the per-path locks, but each worker writes only its OWN runtime file.
    stream_errors: List[str] = []
    stream_lock = threading.Lock()

    def _stream(sid: str) -> None:
        try:
            route = router.runtime_route(sid, create=True)
            worker = SessionWorker(session_id=sid, db_path=route.runtime_db_path)
            try:
                # Interleave a reasoning chunk every ~20 tokens so the batcher
                # flushes the open token buffer in-position (order preserved) and
                # both batch row types are produced.
                r_idx = 0
                for i in range(TOKENS_PER_STREAM):
                    worker.emit_content(f"t{sid[-1]}{i}|")
                    if i % 20 == 19 and r_idx < REASONING_PER_STREAM:
                        worker.emit_reasoning(f"r{r_idx}|")
                        r_idx += 1
                while r_idx < REASONING_PER_STREAM:
                    worker.emit_reasoning(f"r{r_idx}|")
                    r_idx += 1
                worker.flush_batcher()  # final flush of any open buffer
            finally:
                worker.close()
        except Exception as exc:
            with stream_lock:
                stream_errors.append(f"{sid}: {type(exc).__name__}: {exc}")

    stream_threads = [
        threading.Thread(target=_stream, args=(sid,)) for sid in session_ids
    ]
    for th in stream_threads:
        th.start()
    for th in stream_threads:
        th.join(timeout=ENQUEUE_WINDOW_S)
    assert not stream_errors, f"stream errors: {stream_errors[:10]}"

    # Sanity: the streams coalesced. Count raw out batch-rows in one runtime DB
    # and confirm it is far below the 210 individual chunks (coalescing worked).
    sample_route = router.runtime_route(session_ids[0], create=False)
    sample_db = AtlasDB(sample_route.runtime_db_path, schema_set="runtime")
    try:
        batch_rows = sample_db._fetchone(
            "SELECT COUNT(*) AS n FROM session_queue "
            "WHERE direction='out' AND msg_type IN ('token_batch','reasoning_batch')"
        )
        n_batch_rows = int(dict(batch_rows)["n"]) if batch_rows else 0
    finally:
        sample_db.close()
    assert 0 < n_batch_rows < (TOKENS_PER_STREAM + REASONING_PER_STREAM), (
        "coalescing should produce far fewer batch rows than chunks; "
        f"got {n_batch_rows} for {TOKENS_PER_STREAM + REASONING_PER_STREAM} chunks"
    )

    # -- Phase D: drive the REAL broadcaster (serial fan-out, R3/R2/R5) ----- #
    # Repeatedly call the genuine _poll_process_outputs loop until every
    # session's out stream is fully delivered. Per-poll latency measured HERE
    # (the real path), and we instrument sqlite3.connect during STEADY-STATE
    # polls to assert ~0 new opens (R2 connection reuse).
    poll_ms: List[float] = []
    delivered_events: Dict[str, List[Dict[str, Any]]] = {sid: [] for sid in session_ids}

    def _harvest() -> None:
        for sid in session_ids:
            session = bridge.get_session(sid)
            for evt in _drain_outbox(session):
                delivered_events.setdefault(str(evt.get("session_id") or sid), []).append(evt)

    # One warm pass first so connection handles are established before we count
    # opens (the steady-state reuse claim is about polls AFTER warm-up).
    t0 = time.perf_counter()
    bridge._poll_process_outputs()
    poll_ms.append((time.perf_counter() - t0) * 1000.0)
    _harvest()

    # Steady-state open instrumentation (R2): patch sqlite3.connect to count.
    real_connect = sqlite3.connect
    open_counter = {"n": 0}

    def _counting_connect(*args: Any, **kwargs: Any):
        open_counter["n"] += 1
        return real_connect(*args, **kwargs)

    # Keep polling (counting opens) until all sessions fully delivered, then run
    # EXTRA guaranteed steady-state passes so the R2 reuse claim is exercised
    # across multiple full fan-outs (each pass iterates all 100 sessions
    # serially through _get_runtime_db). MIN_STEADY_POLLS makes the open-count
    # assertion meaningful even when one pass drains every session.
    MIN_STEADY_POLLS = 5
    deadline = time.monotonic() + ENQUEUE_WINDOW_S
    sqlite3.connect = _counting_connect
    steady_polls = 0

    def _all_delivered() -> bool:
        return all(
            sum(1 for e in delivered_events.get(sid, []) if e.get("type") == "token")
            >= TOKENS_PER_STREAM
            and sum(
                1 for e in delivered_events.get(sid, []) if e.get("type") == "reasoning"
            )
            >= REASONING_PER_STREAM
            for sid in session_ids
        )

    try:
        while time.monotonic() < deadline:
            t0 = time.perf_counter()
            bridge._poll_process_outputs()
            poll_ms.append((time.perf_counter() - t0) * 1000.0)
            steady_polls += 1
            _harvest()
            # Stop once everything is delivered AND we have enough steady passes
            # for the connection-reuse assertion to be load-bearing.
            if _all_delivered() and steady_polls >= MIN_STEADY_POLLS:
                break
    finally:
        sqlite3.connect = real_connect
    steady_state_opens = open_counter["n"]

    # -- Assertions: R5 output parity (no-drop / no-dup) ------------------- #
    token_parity_ok = True
    reasoning_parity_ok = True
    parity_failures: List[str] = []
    for sid in session_ids:
        evts = delivered_events.get(sid, [])
        got_tokens = "".join(
            str(e.get("text") or "") for e in evts if e.get("type") == "token"
        )
        got_reasoning = "".join(
            str(e.get("text") or "") for e in evts if e.get("type") == "reasoning"
        )
        if got_tokens != expected_token_text[sid]:
            token_parity_ok = False
            parity_failures.append(
                f"{sid}: token len got={len(got_tokens)} "
                f"want={len(expected_token_text[sid])}"
            )
        if got_reasoning != expected_reasoning_text[sid]:
            reasoning_parity_ok = False
            parity_failures.append(
                f"{sid}: reasoning len got={len(got_reasoning)} "
                f"want={len(expected_reasoning_text[sid])}"
            )

    # -- Assertions: zero lost prompts (exactly-once consumption) ---------- #
    # Each session's runtime queue has exactly one 'in'/'prompt' row, matching
    # the enqueued id. Consume it once via dequeue_message and confirm a second
    # dequeue returns nothing (consumed exactly once, plan §4 Task 10).
    prompt_consumed_once = True
    prompt_failures: List[str] = []
    for sid in session_ids:
        route = router.runtime_route(sid, create=False)
        rdb = AtlasDB(route.runtime_db_path, schema_set="runtime")
        try:
            in_rows = rdb._fetchall(
                "SELECT id, msg_type FROM session_queue "
                "WHERE session_id=? AND direction='in' AND msg_type='prompt'",
                (sid,),
            )
            if len(in_rows) != 1:
                prompt_consumed_once = False
                prompt_failures.append(f"{sid}: {len(in_rows)} prompt rows (want 1)")
                continue
            if str(in_rows[0]["id"]) != prompt_ids[sid]:
                prompt_consumed_once = False
                prompt_failures.append(f"{sid}: prompt id mismatch")
            first = rdb.dequeue_message(sid, "in", timeout=0)
            second = rdb.dequeue_message(sid, "in", timeout=0)
            # 'second' may be another in-row type if any; but for 'prompt' the
            # first dequeue (lowest created_at,rowid) is the prompt and there is
            # exactly one, so a re-dequeue must not return the SAME id again.
            if first is None or str(first.get("id")) != prompt_ids[sid]:
                prompt_consumed_once = False
                prompt_failures.append(f"{sid}: first dequeue != prompt")
            if second is not None and str(second.get("id")) == prompt_ids[sid]:
                prompt_consumed_once = False
                prompt_failures.append(f"{sid}: prompt re-consumed (dup)")
        finally:
            rdb.close()

    # -- Assertions: zero cross-session rows ------------------------------- #
    # Each runtime DB holds ONLY its own session's rows.
    cross_session_clean = True
    cross_session_failures: List[str] = []
    for sid in session_ids:
        route = router.runtime_route(sid, create=False)
        rdb = AtlasDB(route.runtime_db_path, schema_set="runtime")
        try:
            foreign = rdb._fetchone(
                "SELECT COUNT(*) AS n FROM session_queue WHERE session_id != ?",
                (sid,),
            )
            n_foreign = int(dict(foreign)["n"]) if foreign else 0
            if n_foreign != 0:
                cross_session_clean = False
                cross_session_failures.append(f"{sid}: {n_foreign} foreign rows")
        finally:
            rdb.close()
    control_queue_rows = _control_session_queue_count(control_path)
    if control_queue_rows != 0:
        cross_session_clean = False
        cross_session_failures.append(
            f"control DB has {control_queue_rows} session_queue rows (want 0)"
        )

    # -- Phase E: rollups + lag -------------------------------------------- #
    rollup_t0 = time.perf_counter()
    rollup_results = runtime_rollup.rollup_all_active(router=router)
    rollup_command_ms = (time.perf_counter() - rollup_t0) * 1000.0
    rollup_lag_s = max((r.rollup_lag_s for r in rollup_results), default=0.0)
    rollup_statuses = {}
    for r in rollup_results:
        rollup_statuses[r.status] = rollup_statuses.get(r.status, 0) + 1

    # Raw runtime totals (read each runtime file directly) vs rollup grand
    # totals (control DB rollup rows). They must match (plan §4 Task 10).
    raw_queue_in = 0
    raw_queue_out = 0
    for sid in session_ids:
        route = router.runtime_route(sid, create=False)
        rdb = AtlasDB(route.runtime_db_path, schema_set="runtime")
        try:
            row = rdb._fetchone(
                "SELECT "
                "SUM(CASE WHEN direction='in' THEN 1 ELSE 0 END) AS qin, "
                "SUM(CASE WHEN direction='out' THEN 1 ELSE 0 END) AS qout "
                "FROM session_queue"
            )
            d = dict(row) if row else {}
            raw_queue_in += int(d.get("qin") or 0)
            raw_queue_out += int(d.get("qout") or 0)
        finally:
            rdb.close()

    control = router.control_db()
    try:
        grand = runtime_rollup.rollup_grand_totals(control)
        rollup_rows = control.list_runtime_usage_rollups()
    finally:
        control.close()
    rollup_queue_in = sum(int(r.get("queue_in") or 0) for r in rollup_rows)
    rollup_queue_out = sum(int(r.get("queue_out") or 0) for r in rollup_rows)
    rollup_totals_match = (
        rollup_queue_in == raw_queue_in and rollup_queue_out == raw_queue_out
    )

    # -- Phase F: fleet health (locked retries, undelivered consistency) --- #
    health = runtime_rollup.fleet_health(router=router, process_manager=manager)
    locked_retry_count = int(health.get("locked_retry_count", 0))
    total_undelivered = int(health.get("total_undelivered", 0))
    manager_locked = manager.locked_retry_count()

    # -- Compose metrics + write evidence ---------------------------------- #
    enqueue_block = _latency_block(enqueue_ms)
    poll_block = _latency_block(poll_ms)
    cold_block = _latency_block(cold_spawn_ms)

    metrics: Dict[str, Any] = {
        "task": "task10-100-session-scale",
        "generated_at": time.time(),
        "mode": "session",
        "n_sessions": N_SESSIONS,
        "tokens_per_stream": TOKENS_PER_STREAM,
        "reasoning_per_stream": REASONING_PER_STREAM,
        "enqueue_window_s": round(window_elapsed, 3),
        "thresholds": {
            "p95_enqueue_ms": P95_ENQUEUE_MS,
            "p95_poll_ms": P95_POLL_MS,
            "rollup_lag_target_s": ROLLUP_LAG_TARGET_S,
        },
        "enqueue_latency_ms": enqueue_block,
        "poll_latency_ms": poll_block,
        "cold_spawn_latency_ms": cold_block,
        "steady_state_sqlite_opens": steady_state_opens,
        "steady_state_polls": steady_polls,
        "coalesced_batch_rows_sample": n_batch_rows,
        "rollup": {
            "command_ms": round(rollup_command_ms, 3),
            "max_lag_s": round(rollup_lag_s, 3),
            "statuses": rollup_statuses,
            "raw_queue_in": raw_queue_in,
            "raw_queue_out": raw_queue_out,
            "rollup_queue_in": rollup_queue_in,
            "rollup_queue_out": rollup_queue_out,
            "grand_totals": {k: grand.get(k) for k in (
                "messages", "trace_events", "session_count", "stale_sessions"
            )},
        },
        "counts": {
            "prompts_enqueued": len(prompt_ids),
            "tokens_emitted_total": N_SESSIONS * TOKENS_PER_STREAM,
            "reasoning_emitted_total": N_SESSIONS * REASONING_PER_STREAM,
            "control_session_queue_rows": control_queue_rows,
            "total_undelivered": total_undelivered,
        },
        "parity": {
            "token_no_drop_no_dup": token_parity_ok,
            "reasoning_no_drop_no_dup": reasoning_parity_ok,
            "prompt_consumed_exactly_once": prompt_consumed_once,
            "zero_cross_session_rows": cross_session_clean,
            "rollup_totals_match_raw": rollup_totals_match,
        },
        "locked": {
            "fleet_locked_retry_count": locked_retry_count,
            "manager_locked_retry_count": manager_locked,
        },
        "failures": {
            "enqueue": enqueue_errors,
            "stream": stream_errors,
            "parity": parity_failures[:20],
            "prompt": prompt_failures[:20],
            "cross_session": cross_session_failures[:20],
        },
    }

    evidence_dir = PROJECT_ROOT / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    evidence_path = evidence_dir / "task10-100-session-scale.json"
    evidence_path.write_text(json.dumps(metrics, indent=2, sort_keys=True))
    # Echo so the measured JSON is visible in the pytest -s / captured output.
    print("\n[task10-metrics] " + json.dumps(metrics, sort_keys=True))

    manager.stop_all()

    # ------------------------------------------------------------------ #
    # ASSERTIONS — measured values, plan thresholds (line 199). Latency is
    # environment-sensitive: asserted AND already recorded above.
    # ------------------------------------------------------------------ #
    # Correctness (NOT environment-sensitive — hard gates):
    assert token_parity_ok, f"[R5] token drop/dup: {parity_failures[:10]}"
    assert reasoning_parity_ok, f"[R5] reasoning drop/dup: {parity_failures[:10]}"
    assert prompt_consumed_once, f"lost/dup prompts: {prompt_failures[:10]}"
    assert cross_session_clean, f"cross-session rows: {cross_session_failures[:10]}"
    assert control_queue_rows == 0, (
        f"control DB must hold 0 session_queue rows, got {control_queue_rows}"
    )
    assert rollup_totals_match, (
        "rollup totals != raw runtime totals: "
        f"in {rollup_queue_in} vs {raw_queue_in}, "
        f"out {rollup_queue_out} vs {raw_queue_out}"
    )
    # Zero 'database is locked' (no exception raised AND counters zero):
    assert locked_retry_count == 0, f"fleet locked_retry_count={locked_retry_count}"
    assert manager_locked == 0, f"manager locked_retry_count={manager_locked}"
    # All delivered => fleet reports zero undelivered out-rows remaining:
    assert total_undelivered == 0, (
        f"fleet_health total_undelivered={total_undelivered} (want 0 after full poll)"
    )
    # R2 steady-state connection reuse: ~0 new opens (allow a tiny slack for any
    # incidental control-DB touch, but it must be far below per-poll-per-session).
    assert steady_state_opens <= 5, (
        f"[R2] steady-state sqlite opens={steady_state_opens} "
        f"over {steady_polls} polls x {N_SESSIONS} sessions (want ~0; reuse broken)"
    )
    # Rollup freshness:
    assert rollup_lag_s <= ROLLUP_LAG_TARGET_S, (
        f"rollup lag {rollup_lag_s:.2f}s > {ROLLUP_LAG_TARGET_S}s"
    )
    # SLA latency (environment-sensitive; measured value already in evidence):
    assert enqueue_block["p95"] <= P95_ENQUEUE_MS, (
        f"p95 enqueue {enqueue_block['p95']}ms > {P95_ENQUEUE_MS}ms "
        f"(full block: {enqueue_block})"
    )
    assert poll_block["p95"] <= P95_POLL_MS, (
        f"p95 poll {poll_block['p95']}ms > {P95_POLL_MS}ms (full block: {poll_block})"
    )


# --------------------------------------------------------------------------- #
# Steady-state Control-DB write proof (feedback #1 / Task 10 closing line).
#
# feedback #1 is already CODE-FIXED by SessionProcessManager._runtime_path_cache:
# a warm poll resolves the runtime path from the cache and never calls
# AtlasDBRouter.runtime_route(create=True), so it never re-upserts the
# session_runtime_dbs manifest (= a Control-DB write). This test is the missing
# PROOF, not a code change. It asserts that after warm-up, many repeated
# broadcaster passes over active sessions:
#
#   (a) do NOT change any session's session_runtime_dbs.updated_at (on-disk
#       snapshot read with raw sqlite3 — the manifest is the only thing the hot
#       path could touch in the Control DB), AND
#   (b) make ZERO upsert_session_runtime_db calls (a Control-DB write counter
#       wrapped at the AtlasDB class level — catches the router's own control_db
#       instances too).
#
# Both signals must stay flat across >= MIN_STEADY_POLLS full fan-outs.
#
# The assertion has TEETH: forcing create=True per poll (modelled here by
# clearing the manager's _runtime_path_cache before each poll, which is exactly
# what the un-fixed code did) makes BOTH (a) and (b) trip. We exercise that
# negative control inline so the proof is self-verifying without leaving the
# test asserting the wrong behavior.
# --------------------------------------------------------------------------- #


# Steady-state knobs: a smaller fleet is enough to prove zero Control-DB writes
# while keeping the test fast (the property is per-poll-per-session, so 25
# sessions x many passes already covers the per-session fan-out).
STEADY_N_SESSIONS = 25
STEADY_TOKENS_PER_STREAM = 12
STEADY_MIN_POLLS = 8


def _build_active_fleet(router, manager, bridge, session_ids):
    """Activate every session (cold-spawn manifest write) + seed output rows.

    Returns nothing; afterwards manager.list_active() == session_ids and each
    session's runtime DB has STEADY_TOKENS_PER_STREAM undelivered out-rows.
    """
    for sid in session_ids:
        # Cold path: runtime_route(create=True) mints uid + upserts the manifest
        # (the ONLY legitimate Control-DB write for this session). Seed output.
        route = router.runtime_route(sid, create=True)
        rdb = AtlasDB(route.runtime_db_path, schema_set="runtime")
        try:
            for i in range(STEADY_TOKENS_PER_STREAM):
                rdb.enqueue_message(sid, "out", "token", {"text": f"x{i}|", "i": i})
        finally:
            rdb.close()
        _inject_fake_process(manager, sid)


def test_steady_state_polling_does_not_write_control_db(session_mode_env):
    """After warm-up, repeated broadcaster passes write ZERO to the Control DB.

    Proves feedback #1's required assertion: session_runtime_dbs.updated_at must
    not change AND a Control-DB write counter stays flat across many polls.
    """
    control_path = session_mode_env["control_path"]
    runtime_root = session_mode_env["runtime_root"]

    router = AtlasDBRouter(
        control_path=control_path, runtime_root=runtime_root, mode="session"
    )
    manager = SessionProcessManager(db_path=control_path, router=router)
    bridge = _build_bridge_with_real_manager(manager)
    session_ids = _session_ids(STEADY_N_SESSIONS)

    _build_active_fleet(router, manager, bridge, session_ids)
    assert sorted(manager.list_active()) == sorted(session_ids)

    # Control-DB write counter: wrap upsert_session_runtime_db at the CLASS level
    # so it catches every AtlasDB instance, including the router's own
    # control_db() handles opened inside runtime_route(create=True). This is the
    # exact write feedback #1 names ("upsert session_runtime_dbs on every poll").
    real_upsert = AtlasDB.upsert_session_runtime_db
    upsert_calls = {"n": 0}

    def _counting_upsert(self, *args, **kwargs):
        upsert_calls["n"] += 1
        return real_upsert(self, *args, **kwargs)

    # -- Warm-up: one poll pass so _runtime_path_cache + connection handles are
    # established. The steady-state claim is about polls AFTER warm-up.
    bridge._poll_process_outputs()
    for sid in session_ids:
        # Drain the warm-up outbox so later passes start clean.
        _drain_outbox(bridge.get_session(sid))

    # Snapshot updated_at AFTER warm-up (raw sqlite3, straight off disk).
    before = _control_manifest_updated_at(control_path)
    assert len(before) == STEADY_N_SESSIONS, (
        f"manifest snapshot must cover all sessions, got {len(before)}"
    )

    # -- Steady state: many repeated broadcaster passes, write counter armed. -- #
    AtlasDB.upsert_session_runtime_db = _counting_upsert
    try:
        for _ in range(STEADY_MIN_POLLS):
            bridge._poll_process_outputs()
            for sid in session_ids:
                _drain_outbox(bridge.get_session(sid))
    finally:
        AtlasDB.upsert_session_runtime_db = real_upsert
    steady_upserts = upsert_calls["n"]

    after = _control_manifest_updated_at(control_path)

    # (a) on-disk proof: no manifest updated_at moved across the steady polls.
    changed = {
        sid: (before.get(sid), after.get(sid))
        for sid in session_ids
        if before.get(sid) != after.get(sid)
    }
    # (b) write-counter proof: zero manifest upserts during steady-state polling.
    assert steady_upserts == 0, (
        f"steady-state polling made {steady_upserts} Control-DB "
        f"upsert_session_runtime_db writes over {STEADY_MIN_POLLS} polls x "
        f"{STEADY_N_SESSIONS} sessions (want 0; hot path re-upserts the manifest)"
    )
    assert not changed, (
        "session_runtime_dbs.updated_at changed during steady-state polling "
        f"(want flat): {dict(list(changed.items())[:5])}"
    )

    # -- Negative control (teeth): model the UN-FIXED hot READ path, which
    # resolved with create=True and re-upserted the manifest on a cold cache.
    # The read paths are now create=False (defense in depth ON TOP OF the path
    # cache, review #1 follow-up), so merely clearing the cache no longer trips an
    # upsert — we must force the old create=True read to prove the steady-state
    # assertion above is load-bearing. The test is LEFT asserting the correct
    # (zero-write) behavior.
    forced_before = _control_manifest_updated_at(control_path)
    teeth_calls = {"n": 0}

    def _counting_upsert_teeth(self, *args, **kwargs):
        teeth_calls["n"] += 1
        return real_upsert(self, *args, **kwargs)

    mgr_cls = type(manager)
    real_get_runtime_db = mgr_cls._get_runtime_db

    def _create_true_get_runtime_db(self, session_id, db_path=None, create=True):
        # simulate the pre-fix read path: resolve with create=True
        return real_get_runtime_db(self, session_id, db_path=db_path, create=True)

    AtlasDB.upsert_session_runtime_db = _counting_upsert_teeth
    mgr_cls._get_runtime_db = _create_true_get_runtime_db
    try:
        for _ in range(3):
            with manager._db_handles_lock:
                manager._runtime_path_cache.clear()  # force cache miss
            bridge._poll_process_outputs()
            for sid in session_ids:
                _drain_outbox(bridge.get_session(sid))
    finally:
        AtlasDB.upsert_session_runtime_db = real_upsert
        mgr_cls._get_runtime_db = real_get_runtime_db
    forced_after = _control_manifest_updated_at(control_path)
    forced_changed = sum(
        1 for sid in session_ids
        if forced_before.get(sid) != forced_after.get(sid)
    )
    # The negative control MUST trip both signals — otherwise the steady-state
    # assertion is vacuous (could pass even with a broken hot path).
    assert teeth_calls["n"] > 0, (
        "negative control failed to force a Control-DB write — the steady-state "
        "assertion would be vacuous (no teeth)"
    )
    assert forced_changed > 0, (
        "negative control failed to move any updated_at — the on-disk "
        "steady-state assertion would be vacuous (no teeth)"
    )

    # -- Evidence ---------------------------------------------------------- #
    evidence = {
        "task": "task10-steady-state-control-write-proof",
        "feedback_item": "#1",
        "generated_at": time.time(),
        "mode": "session",
        "n_sessions": STEADY_N_SESSIONS,
        "steady_polls": STEADY_MIN_POLLS,
        "fan_out_passes_total": STEADY_MIN_POLLS,
        "steady_state": {
            "control_db_upsert_writes": steady_upserts,
            "manifest_updated_at_changed_count": len(changed),
            "manifest_rows_snapshotted": len(before),
        },
        "negative_control": {
            "forced_create_true_polls": 3,
            "control_db_upsert_writes": teeth_calls["n"],
            "manifest_updated_at_changed_count": forced_changed,
            "has_teeth": teeth_calls["n"] > 0 and forced_changed > 0,
        },
        "assertions": {
            "steady_state_zero_control_writes": steady_upserts == 0,
            "steady_state_updated_at_flat": not changed,
        },
    }
    evidence_dir = PROJECT_ROOT / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    evidence_path = evidence_dir / "task10-steady-state-control-write.json"
    evidence_path.write_text(json.dumps(evidence, indent=2, sort_keys=True))
    print("\n[task10-steady-state] " + json.dumps(evidence, sort_keys=True))

    manager.stop_all()


# --------------------------------------------------------------------------- #
# OPTIONAL env-gated real-subprocess smoke (authoritative --db-path co-location).
#
# Skipped by default. Enable with ATLAS_RUNTIME_DB_REAL_SUBPROCESS_STRESS=1.
# Spawns >=10 REAL subprocesses that go through the SAME env channel
# build_worker_env sets (--db-path == ATLAS_DB_PATH == ATLAS_TRACE_DB_PATH ==
# runtime file), then asserts each worker's session_queue AND its llm_calls /
# trace_events land in the SAME per-session runtime DB (co-location). We use a
# tiny LLM-free worker script (no real agent / no real LLM) that writes through
# the standard env-driven AtlasDB opens, so the co-location contract is proven
# without needing a model.
# --------------------------------------------------------------------------- #


_SUBPROCESS_WORKER_SRC = r'''
import os, sys
sys.path.insert(0, os.environ["ATLAS_SOURCE_ROOT"])
sys.path.insert(0, os.path.join(os.environ["ATLAS_SOURCE_ROOT"], "src"))
from core.atlas_db import AtlasDB

session_id = sys.argv[1]
db_path = sys.argv[2]  # the --db-path the manager bound (the runtime file)

# 1. session_queue: bound from --db-path, exactly like the real worker.
qdb = AtlasDB(os.path.expanduser(db_path), schema_set="runtime")
qdb.init_db()
qdb.enqueue_message(session_id, "out", "worker_started", {"pid": os.getpid()})

# 2. llm_calls + trace_events: the real worker writes these via its SECONDARY
#    AtlasDB opens that build_worker_env redirects with ATLAS_DB_PATH /
#    ATLAS_TRACE_DB_PATH. Open EXACTLY through that env (no explicit path) to
#    prove the env channel co-locates them onto the SAME runtime file.
secondary = AtlasDB(os.environ["ATLAS_DB_PATH"], schema_set="runtime")
secondary.init_db()
secondary.record_llm_call(session_id=session_id, model="fake", tokens_input=3, tokens_output=5)

trace_db = AtlasDB(os.environ["ATLAS_TRACE_DB_PATH"], schema_set="runtime")
trace_db.init_db()
trace_db.record_trace_event(event_type="worker_smoke", session_id=session_id, payload={"k": "v"})
'''


@pytest.mark.skipif(
    os.environ.get("ATLAS_RUNTIME_DB_REAL_SUBPROCESS_STRESS") not in ("1", "true", "yes", "on"),
    reason="real-subprocess co-location smoke is opt-in (ATLAS_RUNTIME_DB_REAL_SUBPROCESS_STRESS=1)",
)
def test_runtime_db_real_subprocess_colocation(session_mode_env, tmp_path):
    control_path = session_mode_env["control_path"]
    runtime_root = session_mode_env["runtime_root"]
    n_workers = 10

    router = AtlasDBRouter(
        control_path=control_path, runtime_root=runtime_root, mode="session"
    )
    manager = SessionProcessManager(db_path=control_path, router=router)

    worker_script = tmp_path / "_colocation_worker.py"
    worker_script.write_text(_SUBPROCESS_WORKER_SRC)

    session_ids = _session_ids(n_workers)
    runtime_paths: Dict[str, str] = {}
    procs: List[Tuple[str, subprocess.Popen]] = []
    for sid in session_ids:
        route = router.runtime_route(sid, create=True)
        runtime_paths[sid] = route.runtime_db_path
        # build_worker_env sets ATLAS_DB_PATH / ATLAS_TRACE_DB_PATH == runtime
        # file and --db-path is the same. Drive the subprocess through that env.
        env = manager.build_worker_env(sid)
        env["ATLAS_SOURCE_ROOT"] = str(PROJECT_ROOT)
        # Authoritative co-location: all three channels point at the runtime file.
        assert env["ATLAS_DB_PATH"] == env["ATLAS_TRACE_DB_PATH"]
        assert AtlasDB(env["ATLAS_DB_PATH"]).db_path  # resolvable
        proc = subprocess.Popen(
            [sys.executable, str(worker_script), sid, route.runtime_db_path],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        procs.append((sid, proc))

    for sid, proc in procs:
        out, err = proc.communicate(timeout=60)
        assert proc.returncode == 0, (
            f"subprocess {sid} failed rc={proc.returncode}: "
            f"{err.decode('utf-8', 'replace')[:500]}"
        )

    # Authoritative assertion: queue row AND llm_calls AND trace_events all in
    # the SAME per-session runtime file, and the control DB has none of them.
    for sid in session_ids:
        rt = sqlite3.connect(runtime_paths[sid])
        rt.row_factory = sqlite3.Row
        try:
            q = rt.execute(
                "SELECT COUNT(*) AS n FROM session_queue WHERE session_id=?", (sid,)
            ).fetchone()["n"]
            llm = rt.execute(
                "SELECT COUNT(*) AS n FROM llm_calls WHERE session_id=?", (sid,)
            ).fetchone()["n"]
            tr = rt.execute(
                "SELECT COUNT(*) AS n FROM trace_events WHERE session_id=? "
                "AND event_type='worker_smoke'",
                (sid,),
            ).fetchone()["n"]
        finally:
            rt.close()
        assert q >= 1, f"{sid}: queue row not in runtime DB"
        assert llm == 1, f"{sid}: llm_calls not co-located in runtime DB (got {llm})"
        assert tr == 1, f"{sid}: trace_events not co-located in runtime DB (got {tr})"

    # Control DB must NOT have received the worker's runtime rows.
    assert _control_session_queue_count(control_path) == 0
    ctrl = sqlite3.connect(control_path)
    try:
        for table in ("llm_calls", "trace_events"):
            try:
                n = ctrl.execute(
                    f"SELECT COUNT(*) AS n FROM {table} "
                    "WHERE session_id LIKE 'user%/ip%/rtl-gen'"
                ).fetchone()[0]
            except sqlite3.OperationalError:
                n = 0
            assert n == 0, f"control DB leaked {n} {table} rows from workers"
    finally:
        ctrl.close()

    manager.stop_all()
