"""Task 1/2 — SessionWorkerPolicy env parsing + defaults (single-active-owner plan).

These assert the Environment Contract + compatibility rules + Wave-3 residual
decisions (cap is net-new-only, max_active<=0 unbounded, invalid fails closed).
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.session_worker_policy import (  # noqa: E402
    POLICY_SESSION_SCOPED,
    POLICY_SINGLE_ACTIVE_OWNER,
    SessionWorkerPolicy,
)


def test_default_is_session_scoped_and_unbounded():
    p = SessionWorkerPolicy.from_env({})
    assert p.policy == POLICY_SESSION_SCOPED
    assert p.single_active_owner is False
    assert p.cap_enabled is False
    assert p.cap_exceeded(10_000) is False  # unbounded by default


def test_strict_via_new_policy_has_default_cap_30():
    p = SessionWorkerPolicy.from_env(
        {"ATLAS_SESSION_WORKER_POLICY": "single-active-owner"}
    )
    assert p.policy == POLICY_SINGLE_ACTIVE_OWNER
    assert p.single_active_owner is True
    assert p.cap_enabled is True
    assert p.max_active == 30  # documented default cap when strict + unset
    assert p.cap_exceeded(30) is True
    assert p.cap_exceeded(29) is False


def test_max_active_parsed_but_session_scoped_unbounded_when_absent():
    # Operator sets an explicit cap in session-scoped mode -> cap enforced.
    p = SessionWorkerPolicy.from_env({"ATLAS_SESSION_WORKER_MAX_ACTIVE": "5"})
    assert p.policy == POLICY_SESSION_SCOPED
    assert p.cap_enabled is True
    assert p.max_active == 5
    assert p.cap_exceeded(5) is True
    # Absent -> unbounded (current behavior preserved).
    assert SessionWorkerPolicy.from_env({}).cap_enabled is False


def test_legacy_flag_enables_strict_only_when_new_policy_absent():
    p = SessionWorkerPolicy.from_env({"ATLAS_SINGLE_WORKER_PER_OWNER": "1"})
    assert p.single_active_owner is True
    p_user = SessionWorkerPolicy.from_env({"ATLAS_SINGLE_WORKER_PER_USER": "1"})
    assert p_user.single_active_owner is True
    # New policy present always wins over the legacy flag.
    p2 = SessionWorkerPolicy.from_env(
        {
            "ATLAS_SINGLE_WORKER_PER_OWNER": "1",
            "ATLAS_SESSION_WORKER_POLICY": "session-scoped",
        }
    )
    assert p2.single_active_owner is False


def test_legacy_constructor_arg_supported():
    p = SessionWorkerPolicy.from_env({}, single_worker_per_owner=True)
    assert p.single_active_owner is True
    # ...but the explicit new policy still wins.
    p2 = SessionWorkerPolicy.from_env(
        {"ATLAS_SESSION_WORKER_POLICY": "session-scoped"},
        single_worker_per_owner=True,
    )
    assert p2.single_active_owner is False


def test_invalid_policy_fails_closed_with_warning_and_suppresses_legacy():
    p = SessionWorkerPolicy.from_env({"ATLAS_SESSION_WORKER_POLICY": "bogus"})
    assert p.policy == POLICY_SESSION_SCOPED
    assert p.warning  # diagnostic string is exposed
    # Invalid value is "present" => fail closed, do NOT let legacy flip to strict.
    p2 = SessionWorkerPolicy.from_env(
        {
            "ATLAS_SESSION_WORKER_POLICY": "bogus",
            "ATLAS_SINGLE_WORKER_PER_OWNER": "1",
        }
    )
    assert p2.single_active_owner is False


def test_max_active_nonpositive_is_unbounded_even_in_strict():
    p = SessionWorkerPolicy.from_env(
        {
            "ATLAS_SESSION_WORKER_POLICY": "single-active-owner",
            "ATLAS_SESSION_WORKER_MAX_ACTIVE": "0",
        }
    )
    assert p.single_active_owner is True
    assert p.cap_enabled is False
    assert p.cap_exceeded(10_000) is False


def test_numeric_fields_and_reaper_toggle():
    p = SessionWorkerPolicy.from_env(
        {
            "ATLAS_SESSION_WORKER_POLICY": "single-active-owner",
            "ATLAS_SESSION_WORKER_IDLE_TTL_SEC": "120",
            "ATLAS_SESSION_WORKER_REAPER_INTERVAL_SEC": "7",
            "ATLAS_SESSION_WORKER_STOP_ACK_SEC": "2",
            "ATLAS_SESSION_WORKER_KILL_GRACE_SEC": "4",
            "ATLAS_SESSION_WORKER_ENABLE_REAPER": "0",
        }
    )
    assert p.idle_ttl_sec == 120
    assert p.reaper_interval_sec == 7
    assert p.stop_ack_sec == 2
    assert p.kill_grace_sec == 4
    assert p.reaper_enabled is False


def test_garbage_numeric_falls_back_to_default():
    p = SessionWorkerPolicy.from_env(
        {
            "ATLAS_SESSION_WORKER_POLICY": "single-active-owner",
            "ATLAS_SESSION_WORKER_IDLE_TTL_SEC": "not-a-number",
        }
    )
    assert p.idle_ttl_sec == 900.0  # default preserved


def test_to_status_dict_shape():
    p = SessionWorkerPolicy.from_env(
        {"ATLAS_SESSION_WORKER_POLICY": "single-active-owner"}
    )
    d = p.to_status_dict()
    assert d == {
        "policy": "single-active-owner",
        "single_active_owner": True,
        "cap_enabled": True,
        "max_active": 30,
    }
