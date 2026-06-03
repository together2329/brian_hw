"""Task 3 — owner-slot enforcement in _MultiUserBridge (single-active-owner).

Uses the in-memory FakeProcessManager so switches/terminations are deterministic
with no subprocesses. Covers: switch terminates previous w/ no sibling, other
owners untouched, idempotent same-session, termination_failed refuses a sibling,
private worker_switching/worker_evicted events, guarded slot clear on
exit/delete/death, per-model owner_slot_key, and session-scoped non-displacement.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.atlas_multiuser import (  # noqa: E402
    _SESSION_PRIVATE_BROADCAST_TYPES,
    _MultiUserBridge,
    _SessionBridge,
)
from core.session_worker_policy import SessionWorkerPolicy  # noqa: E402
from tests.support.fake_process_manager import FakeProcessManager  # noqa: E402


def _bridge(fake, *, strict=True, max_active=30):
    b = _MultiUserBridge(use_processes=True, single_worker_per_owner=strict)
    b._process_manager = fake
    env = (
        {
            "ATLAS_SESSION_WORKER_POLICY": "single-active-owner",
            "ATLAS_SESSION_WORKER_MAX_ACTIVE": str(max_active),
        }
        if strict
        # Default is now strict, so session-scoped must be requested explicitly.
        else {"ATLAS_SESSION_WORKER_POLICY": "session-scoped"}
    )
    pol = SessionWorkerPolicy.from_env(env)
    b._policy = pol
    b.policy = pol
    return b


def _alive_for(fake, owner):
    return sorted(s for s in fake.list_active() if s.split("/", 1)[0] == owner)


# ── switch terminates previous, no sibling ──────────────────────

def test_switch_terminates_previous_no_sibling():
    fake = FakeProcessManager()
    b = _bridge(fake)
    b.activate_session("alice/ip_a/ssot-gen", warm=True)
    assert _alive_for(fake, "alice") == ["alice/ip_a/ssot-gen"]

    b.activate_session("alice/ip_a/rtl-gen", warm=True)
    # exactly one alice worker alive — the new one; the old was terminated.
    assert _alive_for(fake, "alice") == ["alice/ip_a/rtl-gen"]
    assert ("alice/ip_a/ssot-gen", "activate") in [(s, r) for s, r in fake.terminated]
    assert b.active_session_for_owner("alice") == "alice/ip_a/rtl-gen"


def test_switch_via_prompt_path_keeps_one_worker():
    fake = FakeProcessManager()
    b = _bridge(fake)
    last = ""
    for i in range(8):
        last = f"alice/ip/wf{i}"
        assert b.submit_prompt_for_session(last, f"p{i}") is True
    assert _alive_for(fake, "alice") == [last]


def test_warm_switch_reservation_blocks_net_new_owner_steal():
    fake = FakeProcessManager()
    b = _bridge(fake, max_active=2)
    assert b.warm_session("alice/ip/wf0")["status"] == "started"
    assert b.warm_session("bob/ip/wf0")["status"] == "started"

    switch = b._prepare_owner_slot_for_session("alice/ip/wf1", "warm")
    assert switch["switch_status"] == "switched"
    assert fake.is_alive("alice/ip/wf0") is False

    blocked = b.warm_session("carol/ip/wf0")
    assert blocked["status"] == "capacity_wait"
    assert blocked["alive"] is False
    assert fake.is_alive("carol/ip/wf0") is False

    warmed = b.warm_session("alice/ip/wf1")
    assert warmed["status"] == "started"
    assert sorted(fake.list_active()) == ["alice/ip/wf1", "bob/ip/wf0"]


def test_activate_without_warm_releases_reserved_capacity():
    fake = FakeProcessManager()
    b = _bridge(fake, max_active=2)
    assert b.warm_session("alice/ip/wf0")["status"] == "started"
    assert b.warm_session("bob/ip/wf0")["status"] == "started"

    b.activate_session("alice/ip/wf1", warm=False)
    assert fake.is_alive("alice/ip/wf0") is False

    carol = b.warm_session("carol/ip/wf0")
    assert carol["status"] == "started"
    assert sorted(fake.list_active()) == ["bob/ip/wf0", "carol/ip/wf0"]


# ── other owners untouched ──────────────────────────────────────

def test_switch_does_not_touch_other_owner():
    fake = FakeProcessManager()
    b = _bridge(fake)
    b.activate_session("bob/ip_a/rtl-gen", warm=True)
    b.activate_session("alice/ip_a/ssot-gen", warm=True)
    b.activate_session("alice/ip_a/rtl-gen", warm=True)

    assert "bob/ip_a/rtl-gen" in fake.list_active()
    assert all(sid.split("/", 1)[0] != "bob" for sid, _r in fake.terminated)
    assert b.active_session_for_owner("bob") == "bob/ip_a/rtl-gen"


# ── idempotent same-session ─────────────────────────────────────

def test_repeated_same_session_activation_is_idempotent():
    fake = FakeProcessManager()
    b = _bridge(fake)
    b.activate_session("alice/ip/ssot-gen", warm=True)
    b.activate_session("alice/ip/rtl-gen", warm=True)  # 1 terminate
    before = len(fake.terminated)
    b.activate_session("alice/ip/rtl-gen", warm=True)  # noop
    b.activate_session("alice/ip/rtl-gen", warm=True)  # noop
    assert len(fake.terminated) == before  # no extra terminations
    assert _alive_for(fake, "alice") == ["alice/ip/rtl-gen"]


# ── termination_failed refuses a sibling ────────────────────────

def test_termination_failed_refuses_sibling_via_activate():
    fake = FakeProcessManager(fail_terminate_for={"alice/ip/ssot-gen"})
    b = _bridge(fake)
    b.activate_session("alice/ip/ssot-gen", warm=True)
    assert _alive_for(fake, "alice") == ["alice/ip/ssot-gen"]

    # Switching cannot terminate the old worker -> NO sibling is spawned and the
    # slot stays with the old session.
    b.activate_session("alice/ip/rtl-gen", warm=True)
    assert _alive_for(fake, "alice") == ["alice/ip/ssot-gen"]
    assert "alice/ip/rtl-gen" not in fake.list_active()
    assert b.active_session_for_owner("alice") == "alice/ip/ssot-gen"


def test_prepare_owner_slot_returns_structured_status():
    fake = FakeProcessManager()
    b = _bridge(fake)
    b.activate_session("alice/ip/ssot-gen", warm=True)
    res = b._prepare_owner_slot_for_session("alice/ip/rtl-gen", "activate")
    assert res["switch_status"] == "switched"
    assert res["previous_session"] == "alice/ip/ssot-gen"
    assert res["terminated_session"] == "alice/ip/ssot-gen"
    assert res["owner_slot"] == "alice"


# ── private worker_switching / worker_evicted ───────────────────

def test_lifecycle_events_are_private_broadcast_types():
    assert "worker_switching" in _SESSION_PRIVATE_BROADCAST_TYPES
    assert "worker_evicted" in _SESSION_PRIVATE_BROADCAST_TYPES


def test_switch_emits_private_worker_switching_on_both_sessions(monkeypatch):
    events = []
    monkeypatch.setattr(
        _SessionBridge, "emit",
        lambda self, msg_type, **kw: events.append((self.session_id, msg_type)),
    )
    fake = FakeProcessManager()
    b = _bridge(fake)
    b.activate_session("alice/ip/ssot-gen", warm=True)
    events.clear()
    b._prepare_owner_slot_for_session("alice/ip/rtl-gen", "activate")
    switching = {sid for sid, t in events if t == "worker_switching"}
    assert switching == {"alice/ip/ssot-gen", "alice/ip/rtl-gen"}


# ── guarded clear on exit/delete/death ──────────────────────────

def test_exit_session_clears_owner_slot():
    fake = FakeProcessManager()
    b = _bridge(fake)
    b.activate_session("alice/ip/ssot-gen", warm=True)
    b.exit_session("alice/ip/ssot-gen")
    assert b.active_session_for_owner("alice") == ""


def test_clear_is_guarded_when_slot_repointed():
    fake = FakeProcessManager()
    b = _bridge(fake)
    b.activate_session("alice/ip/ssot-gen", warm=True)
    b.activate_session("alice/ip/rtl-gen", warm=True)  # slot now rtl-gen
    # A late exit of the OLD session must NOT clear the slot now held by rtl-gen.
    b.exit_session("alice/ip/ssot-gen")
    assert b.active_session_for_owner("alice") == "alice/ip/rtl-gen"


def test_clear_owner_slot_helper_only_clears_when_equal():
    fake = FakeProcessManager()
    b = _bridge(fake)
    b.activate_session("alice/ip/rtl-gen", warm=True)
    b._clear_owner_slot("alice/ip/OTHER")  # different session -> no-op
    assert b.active_session_for_owner("alice") == "alice/ip/rtl-gen"
    b._clear_owner_slot("alice/ip/rtl-gen")  # matches -> cleared
    assert b.active_session_for_owner("alice") == ""


# ── per-model owner slot key ────────────────────────────────────

def test_owner_slot_key_honors_per_model(monkeypatch):
    fake = FakeProcessManager()
    b = _bridge(fake)
    # Pin every model env var deterministically: _owner_slot_with_model reads
    # LLM_ACTIVE_MODEL_NAME first, then MODEL_NAME, then LLM_MODEL_NAME — the
    # ambient test env may already set the higher-priority one.
    monkeypatch.delenv("ATLAS_SESSION_PER_MODEL", raising=False)
    assert b.owner_slot_key("alice/ip/wf") == "alice"
    monkeypatch.setenv("ATLAS_SESSION_PER_MODEL", "1")
    monkeypatch.setenv("LLM_ACTIVE_MODEL_NAME", "gpt-5.3-codex")
    monkeypatch.delenv("MODEL_NAME", raising=False)
    monkeypatch.delenv("LLM_MODEL_NAME", raising=False)
    # '.' is sanitized to '_' (only [A-Za-z0-9_-] survive); '-' is preserved.
    assert b.owner_slot_key("alice/ip/wf") == "alice__gpt-5_3-codex"
    # idempotent: already-scoped segment[0] is unchanged
    assert b.owner_slot_key("alice__gpt-5_3-codex/ip/wf") == "alice__gpt-5_3-codex"


def test_mark_active_and_clear_use_model_scoped_slot(monkeypatch):
    fake = FakeProcessManager()
    b = _bridge(fake)
    monkeypatch.setenv("ATLAS_SESSION_PER_MODEL", "1")
    monkeypatch.setenv("LLM_ACTIVE_MODEL_NAME", "gpt-5.3-codex")
    monkeypatch.delenv("MODEL_NAME", raising=False)
    monkeypatch.delenv("LLM_MODEL_NAME", raising=False)

    b.activate_session("alice/ip/rtl-gen", warm=True)

    slot = "alice__gpt-5_3-codex"
    assert b.active_session_for_owner("alice") == "alice/ip/rtl-gen"
    assert b.active_session_for_owner(slot) == "alice/ip/rtl-gen"
    assert b._owner_active_sessions == {slot: "alice/ip/rtl-gen"}
    b._clear_owner_slot("alice/ip/rtl-gen")
    assert b._owner_active_sessions == {}


# ── session-scoped mode: no displacement ────────────────────────

def test_session_scoped_mode_no_displacement():
    fake = FakeProcessManager()
    b = _bridge(fake, strict=False)
    b.activate_session("alice/ip/ssot-gen", warm=True)
    b.activate_session("alice/ip/rtl-gen", warm=True)
    # Both workers remain alive — no single-active displacement in session-scoped.
    assert _alive_for(fake, "alice") == ["alice/ip/rtl-gen", "alice/ip/ssot-gen"]
    assert fake.terminated == []
