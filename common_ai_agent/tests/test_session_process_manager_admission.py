"""Task 4 — SpawnResult admission ordering + terminate_session semantics.

Deterministic + fast: subprocess.Popen is faked, so no real worker is launched.
Covers Wave-3 H9 (cap check ordering), H2/H3 (reserve exempts a same-owner
replacement), H4 (warm-idle skips the stop-ack wait), and list_active_metadata.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import core.session_process_manager as spm  # noqa: E402
from core.session_process_manager import (  # noqa: E402
    SPAWN_STATUS_CAPACITY_WAIT,
    SPAWN_STATUS_READY,
    SPAWN_STATUS_STARTED,
    SessionProcessManager,
)
from core.session_worker_policy import SessionWorkerPolicy  # noqa: E402


class _FakeProc:
    _next_pid = 41000

    def __init__(self):
        _FakeProc._next_pid += 1
        self.pid = _FakeProc._next_pid
        self._alive = True

    def poll(self):
        return None if self._alive else 0

    def terminate(self):
        self._alive = False

    def kill(self):
        self._alive = False

    def wait(self, timeout=None):
        self._alive = False
        return 0


@pytest.fixture
def mgr(tmp_path, monkeypatch):
    monkeypatch.setenv("ATLAS_SESSION_WORKER_PRUNE_ORPHANS", "0")  # skip `ps`
    monkeypatch.setattr(spm.subprocess, "Popen", lambda *a, **k: _FakeProc())
    m = SessionProcessManager(db_path=str(tmp_path / "atlas.db"))
    try:
        yield m
    finally:
        # entries hold fake procs; clear without touching real handles
        m._processes.clear()


def _strict(max_active):
    return SessionWorkerPolicy.from_env(
        {
            "ATLAS_SESSION_WORKER_POLICY": "single-active-owner",
            "ATLAS_SESSION_WORKER_MAX_ACTIVE": str(max_active),
        }
    )


def test_spawn_result_started_then_cap_refuses_net_new(mgr):
    policy = _strict(2)
    r1 = mgr.spawn_result("alice/ip/wf", policy=policy)
    r2 = mgr.spawn_result("bob/ip/wf", policy=policy)
    assert (r1.ok, r1.status) == (True, SPAWN_STATUS_STARTED)
    assert (r2.ok, r2.status) == (True, SPAWN_STATUS_STARTED)
    assert mgr.active_count() == 2

    # 3rd net-new owner over the cap -> capacity_wait, NO process spawned.
    r3 = mgr.spawn_result("carol/ip/wf", policy=policy)
    assert r3.ok is False
    assert r3.status == SPAWN_STATUS_CAPACITY_WAIT
    assert r3.reason == "max_active"
    assert r3.active_count == 2 and r3.max_active == 2
    assert mgr.active_count() == 2
    assert mgr.is_alive("carol/ip/wf") is False


def test_alive_session_is_ready_even_at_cap_h9_ordering(mgr):
    policy = _strict(2)
    mgr.spawn_result("alice/ip/wf", policy=policy)
    mgr.spawn_result("bob/ip/wf", policy=policy)
    # Re-activating an already-live session must short-circuit to READY (no new
    # slot), even though active_count == max_active (H9 ordering).
    r = mgr.spawn_result("alice/ip/wf", policy=policy)
    assert r.ok is True
    assert r.status == SPAWN_STATUS_READY
    assert mgr.active_count() == 2


def test_reserve_replacement_exempt_from_cap_h2_h3(mgr):
    policy = _strict(2)
    mgr.spawn_result("alice/ip/wf", policy=policy)
    mgr.spawn_result("bob/ip/wf", policy=policy)
    assert mgr.spawn_result("carol/ip/wf", policy=policy).status == SPAWN_STATUS_CAPACITY_WAIT

    # A same-owner replacement reserves the freed slot and is NOT cap-refused.
    r = mgr.spawn_result(
        "alice/ip/wf2", policy=policy, reserve=True, replacing="alice/ip/wf"
    )
    assert r.ok is True
    assert r.status == SPAWN_STATUS_STARTED
    assert "replacing:alice/ip/wf" in r.reason


def test_terminate_and_reserve_slot_blocks_net_new_until_replacement_spawns(mgr):
    policy = _strict(2)
    mgr.spawn_result("alice/ip/wf", policy=policy)
    mgr.spawn_result("bob/ip/wf", policy=policy)

    assert mgr.terminate_and_reserve_slot(
        "alice/ip/wf", "alice/ip/wf2", reason="switch"
    ) is True
    assert mgr.active_count() == 1

    blocked = mgr.spawn_result("carol/ip/wf", policy=policy)
    assert blocked.ok is False
    assert blocked.status == SPAWN_STATUS_CAPACITY_WAIT
    assert blocked.active_count == 2
    assert mgr.is_alive("carol/ip/wf") is False

    replacement = mgr.spawn_result("alice/ip/wf2", policy=policy)
    assert replacement.ok is True
    assert replacement.status == SPAWN_STATUS_STARTED
    assert mgr.active_count() == 2


def test_terminate_and_reserve_slot_clears_reservation_when_terminate_raises(mgr, monkeypatch):
    policy = _strict(1)

    def raise_terminate(*args, **kwargs):
        raise RuntimeError("terminate failed")

    monkeypatch.setattr(mgr, "terminate_session", raise_terminate)

    assert mgr.terminate_and_reserve_slot(
        "alice/ip/wf", "alice/ip/wf2", reason="switch"
    ) is False
    assert "alice/ip/wf2" not in mgr._reserved_sessions
    assert mgr.spawn_result("bob/ip/wf", policy=policy).ok is True


def test_unbounded_policy_never_refuses(mgr):
    policy = SessionWorkerPolicy.from_env(
        {"ATLAS_SESSION_WORKER_POLICY": "session-scoped"}
    )
    for i in range(50):
        assert mgr.spawn_result(f"u{i}/ip/wf", policy=policy).ok is True
    assert mgr.active_count() == 50


def test_spawn_bool_wrapper_unbounded(mgr):
    # Legacy spawn() takes no policy -> cap OFF -> always True on success.
    for i in range(10):
        assert mgr.spawn(f"u{i}/ip/wf") is True
    assert mgr.active_count() == 10


def test_terminate_idle_skips_stop_ack_h4(mgr, monkeypatch):
    sent = []
    monkeypatch.setattr(mgr, "send_input", lambda *a, **k: sent.append((a, k)))
    mgr.spawn_result("alice/ip/wf", policy=_strict(5))

    started = time.monotonic()
    ok = mgr.terminate_session(
        "alice/ip/wf",
        graceful=True,
        has_running_prompt=False,  # warm-idle
        stop_timeout_sec=5.0,      # would be a 5s wait if (wrongly) honored
        kill_grace_sec=1.0,
    )
    elapsed = time.monotonic() - started
    assert ok is True
    assert sent == []                  # no 'stop' enqueued for a warm-idle worker
    assert elapsed < 1.0               # did NOT wait the 5s stop-ack budget
    assert mgr.is_alive("alice/ip/wf") is False


def test_terminate_busy_enqueues_stop_h4(mgr, monkeypatch):
    sent = []
    monkeypatch.setattr(mgr, "send_input", lambda *a, **k: sent.append((a, k)))
    mgr.spawn_result("alice/ip/wf", policy=_strict(5))

    ok = mgr.terminate_session(
        "alice/ip/wf",
        reason="switch",
        graceful=True,
        has_running_prompt=True,   # busy -> graceful stop attempted
        stop_timeout_sec=0.2,
        kill_grace_sec=1.0,
    )
    assert ok is True
    assert len(sent) == 1
    assert sent[0][0][1] == "stop"     # send_input(session_id, "stop", payload)


def test_terminate_untracked_is_noop_true(mgr):
    assert mgr.terminate_session("ghost/ip/wf") is True
    assert mgr.kill("ghost/ip/wf") is True


def test_list_active_metadata_shape(mgr):
    mgr.spawn_result("alice/ip/wf", policy=_strict(5))
    meta = mgr.list_active_metadata()
    assert len(meta) == 1
    row = meta[0]
    assert row["owner"] == "alice"
    assert row["session_id"] == "alice/ip/wf"
    assert row["alive"] is True
    assert row["running"] is None       # manager has no agent_running view
    assert isinstance(row["pid"], int)
    assert row["idle_age_sec"] >= 0.0
    assert row["state"] in {"starting", "ready"}


def test_metadata_skips_dead_entries(mgr):
    mgr.spawn_result("alice/ip/wf", policy=_strict(5))
    # Mark the fake proc dead -> excluded from metadata + active_count.
    mgr._processes["alice/ip/wf"]["proc"]._alive = False
    assert mgr.list_active_metadata() == []
    assert mgr.active_count() == 0
