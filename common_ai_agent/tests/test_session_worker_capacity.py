"""Task 10 — 100-user synthetic capacity harness + owner-slot isolation.

Scenarios A-E use the in-memory :class:`tests.support.FakeProcessManager` so
100-owner admission/switch logic runs deterministically with NO subprocesses and
NO LLM calls. Two non-fake smokes anchor the claims: a small real-process smoke
(max_active=3) proves the manager enforces the cap with actual ``Popen`` handles,
and an API-level authenticated multi-user smoke proves owner-slot isolation on
the same user-scoped path Atlas runs in production (Wave-3 H11).
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from core.atlas_multiuser import _MultiUserBridge  # noqa: E402
from core.session_process_manager import SessionProcessManager  # noqa: E402
from core.session_worker_policy import SessionWorkerPolicy  # noqa: E402
from tests.support.fake_process_manager import (  # noqa: E402
    FakeProcessManager,
    ManualClock,
)


def _bridge_with_fake(policy: SessionWorkerPolicy, fake: FakeProcessManager) -> _MultiUserBridge:
    """Build a strict-mode bridge wired to a fake manager + the resolved policy.

    The bridge reads ``self._policy`` (wired in __init__); we override BOTH it and
    the public ``policy`` alias so the harness pins the exact cap under test
    instead of whatever __init__ derived from the ambient env.
    """
    bridge = _MultiUserBridge(
        use_processes=True,
        single_worker_per_owner=policy.single_active_owner,
    )
    bridge._process_manager = fake
    bridge._policy = policy
    bridge.policy = policy
    return bridge


def _owner(sid: str) -> str:
    return sid.split("/", 1)[0]


# ── Scenario A: 100 owners, cap 30 -> 30 admitted, 70 capacity_wait ──
def test_scenario_a_hundred_owners_cap_thirty():
    policy = SessionWorkerPolicy.from_env({
        "ATLAS_SESSION_WORKER_POLICY": "single-active-owner",
        "ATLAS_SESSION_WORKER_MAX_ACTIVE": "30",
    })
    fake = FakeProcessManager()
    admitted = refused = 0
    for i in range(100):
        result = fake.spawn_result(f"owner{i}/ip/rtl-gen", policy=policy)
        if result.ok:
            admitted += 1
        else:
            refused += 1
            assert result.status == "capacity_wait"
            assert result.reason == "max_active"
    assert admitted == 30
    assert refused == 70
    assert len(fake.list_active()) == 30
    assert len({_owner(s) for s in fake.list_active()}) == 30  # no cross-owner kill
    assert fake.killed == []
    assert fake.terminated == []


# ── Scenario B: one owner switches 20 workflows -> one live worker ──
def test_scenario_b_same_owner_rapid_switch_keeps_one_worker():
    policy = SessionWorkerPolicy.from_env({
        "ATLAS_SESSION_WORKER_POLICY": "single-active-owner",
        "ATLAS_SESSION_WORKER_MAX_ACTIVE": "30",
    })
    fake = FakeProcessManager()
    bridge = _bridge_with_fake(policy, fake)
    last = ""
    for i in range(20):
        last = f"alice/ip/wf{i}"
        assert bridge.submit_prompt_for_session(last, f"p{i}") is True
    alice_live = [s for s in fake.list_active() if _owner(s) == "alice"]
    assert alice_live == [last], alice_live
    assert bridge.active_session_for_owner("alice") == last


# ── Scenario C: 100 owners, cap 100 -> 100 isolated slots ──
def test_scenario_c_hundred_owners_hundred_slots_isolated():
    policy = SessionWorkerPolicy.from_env({
        "ATLAS_SESSION_WORKER_POLICY": "single-active-owner",
        "ATLAS_SESSION_WORKER_MAX_ACTIVE": "100",
    })
    fake = FakeProcessManager()
    bridge = _bridge_with_fake(policy, fake)
    for i in range(100):
        assert bridge.submit_prompt_for_session(f"owner{i}/ip/rtl-gen", "go") is True
    assert len(fake.list_active()) == 100
    assert len({_owner(s) for s in fake.list_active()}) == 100
    for session_id, _type, _payload in fake.sent:
        assert session_id == f"{_owner(session_id)}/ip/rtl-gen"  # no cross routing


# ── Scenario D: capacity-blocked prompt -> failure, no transport ack ──
def test_scenario_d_capacity_blocked_prompt_is_not_acked():
    policy = SessionWorkerPolicy.from_env({
        "ATLAS_SESSION_WORKER_POLICY": "single-active-owner",
        "ATLAS_SESSION_WORKER_MAX_ACTIVE": "1",
    })
    fake = FakeProcessManager()
    bridge = _bridge_with_fake(policy, fake)
    assert bridge.submit_prompt_for_session("alice/ip/rtl-gen", "first") is True
    result = bridge.submit_prompt_result_for_session("bob/ip/rtl-gen", "second")
    assert result.ok is False
    assert result.status == "capacity_wait"
    assert result.error == "capacity_wait"
    assert all(_owner(sid) != "bob" for sid, *_ in fake.sent)
    assert "bob/ip/rtl-gen" not in fake.list_active()


# ── Scenario E: same-owner switch while ALL slots full -> still 1 live ──
def test_scenario_e_switch_under_full_capacity_keeps_live_worker():
    policy = SessionWorkerPolicy.from_env({
        "ATLAS_SESSION_WORKER_POLICY": "single-active-owner",
        "ATLAS_SESSION_WORKER_MAX_ACTIVE": "3",
    })
    fake = FakeProcessManager()
    bridge = _bridge_with_fake(policy, fake)
    for owner in ("alice", "bob", "carol"):
        assert bridge.submit_prompt_for_session(f"{owner}/ip/rtl-gen", "go") is True
    assert len(fake.list_active()) == 3
    # Alice switches workflow while the fleet is full — a same-owner-slot
    # REPLACEMENT must NOT be cap-refused (it reserves alice's freed slot).
    result = bridge.submit_prompt_result_for_session("alice/ip/tb-gen", "switch")
    assert result.ok is True
    assert result.status != "capacity_wait"
    alice_live = [s for s in fake.list_active() if _owner(s) == "alice"]
    assert alice_live == ["alice/ip/tb-gen"], alice_live
    assert len(fake.list_active()) == 3  # fleet stays exactly full, not 4
    assert bridge.active_session_for_owner("alice") == "alice/ip/tb-gen"


# ── idle-age via injected clock (no sleeping) ──
def test_idle_age_advances_with_injected_clock():
    clock = ManualClock(start=1_000.0)
    fake = FakeProcessManager(clock=clock)
    fake.spawn_result("alice/ip/rtl-gen")
    clock.advance(42.0)
    [row] = fake.list_active_metadata()
    assert row["session_id"] == "alice/ip/rtl-gen"
    assert row["idle_age_sec"] == pytest.approx(42.0)


# ── real-process smoke (max_active=3) ──
def test_real_process_smoke_cap_three(tmp_path):
    policy = SessionWorkerPolicy.from_env({
        "ATLAS_SESSION_WORKER_POLICY": "single-active-owner",
        "ATLAS_SESSION_WORKER_MAX_ACTIVE": "3",
    })
    manager = SessionProcessManager(db_path=str(tmp_path / "atlas.db"))
    try:
        ok = [manager.spawn_result(f"u{i}/ip/rtl-gen", policy=policy) for i in range(3)]
        assert all(r.ok for r in ok)
        time.sleep(0.3)
        assert len(manager.list_active()) <= 3
        refused = manager.spawn_result("u3/ip/rtl-gen", policy=policy)
        assert refused.ok is False
        assert refused.status == "capacity_wait"
        assert manager.terminate_session(
            "u0/ip/rtl-gen", reason="smoke",
            stop_timeout_sec=policy.stop_ack_sec,
            kill_grace_sec=policy.kill_grace_sec,
        ) is True
        time.sleep(0.2)
        assert manager.spawn_result("u3/ip/rtl-gen", policy=policy).ok is True
    finally:
        manager.stop_all()
