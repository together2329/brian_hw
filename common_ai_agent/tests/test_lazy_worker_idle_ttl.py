"""
tests/test_lazy_worker_idle_ttl.py

Verify the idle-TTL path in _lazy_worker_reaper_loop:

  - When _probe_worker_health returns running_count=0 for >= ATLAS_LAZY_WORKER_IDLE_TTL_SEC
    seconds, the reaper calls proc.terminate() and removes the entry from
    _LAZY_WORKER_PROCS.

Uses monkeypatching; no real processes or network connections.

Module globals patched:
  _LAZY_WORKER_REAPER_INTERVAL  → 0.1 s (fast loop)
  _LAZY_WORKER_IDLE_TTL_SEC     → 0.5 s (short TTL)
  _LAZY_WORKER_REAPER_STARTED   → False (allow fresh thread)
"""
from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest

import src.atlas_api_jobs as _mod


_WORKER_URL = "http://127.0.0.1:19901"
_WORKER_KEY = _WORKER_URL.rstrip("/")

_FAST_INTERVAL = 0.1   # reaper loop sleep
_SHORT_TTL     = 0.5   # idle TTL
_WAIT_TIMEOUT  = 3.0   # max seconds for the reaper to act


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def clean_state(monkeypatch):
    """Reset lazy-worker module state before each test."""
    orig_procs      = dict(_mod._LAZY_WORKER_PROCS)
    orig_last_busy  = dict(_mod._LAZY_WORKER_LAST_BUSY)
    orig_jobs       = dict(_mod._jobs)
    orig_started    = _mod._LAZY_WORKER_REAPER_STARTED
    orig_interval   = _mod._LAZY_WORKER_REAPER_INTERVAL
    orig_ttl        = _mod._LAZY_WORKER_IDLE_TTL_SEC

    _mod._LAZY_WORKER_PROCS.clear()
    _mod._LAZY_WORKER_LAST_BUSY.clear()
    with _mod._jobs_lock:
        _mod._jobs.clear()

    monkeypatch.setattr(_mod, "_LAZY_WORKER_REAPER_STARTED", False)
    monkeypatch.setattr(_mod, "_LAZY_WORKER_REAPER_INTERVAL", _FAST_INTERVAL)
    monkeypatch.setattr(_mod, "_LAZY_WORKER_IDLE_TTL_SEC", _SHORT_TTL)

    # Suppress DB writes
    monkeypatch.setattr(_mod, "_finish_job_db_run", lambda *a, **k: None)

    yield

    _mod._LAZY_WORKER_PROCS.clear()
    _mod._LAZY_WORKER_PROCS.update(orig_procs)
    _mod._LAZY_WORKER_LAST_BUSY.clear()
    _mod._LAZY_WORKER_LAST_BUSY.update(orig_last_busy)
    with _mod._jobs_lock:
        _mod._jobs.clear()
        _mod._jobs.update(orig_jobs)
    monkeypatch.setattr(_mod, "_LAZY_WORKER_REAPER_STARTED", orig_started)
    monkeypatch.setattr(_mod, "_LAZY_WORKER_REAPER_INTERVAL", orig_interval)
    monkeypatch.setattr(_mod, "_LAZY_WORKER_IDLE_TTL_SEC", orig_ttl)


def _alive_proc() -> MagicMock:
    proc = MagicMock()
    proc.pid = 88888
    proc.poll.return_value = None  # process alive
    return proc


# ── tests ─────────────────────────────────────────────────────────────────────

class TestLazyWorkerIdleTTL:

    def test_idle_worker_is_terminated(self, clean_state):
        """proc.terminate() is called within WAIT_TIMEOUT when worker is idle."""
        proc = _alive_proc()
        _mod._LAZY_WORKER_PROCS[_WORKER_KEY] = proc
        # Set last_busy far enough in the past to exceed TTL immediately
        _mod._LAZY_WORKER_LAST_BUSY[_WORKER_KEY] = (
            time.monotonic() - _SHORT_TTL - 1.0
        )

        idle_health = {"status": "ok", "running_count": 0}

        with patch.object(_mod, "_probe_worker_health", return_value=idle_health):
            _mod._ensure_lazy_worker_reaper()

            deadline = time.monotonic() + _WAIT_TIMEOUT
            while time.monotonic() < deadline:
                if proc.terminate.called:
                    break
                time.sleep(0.05)

        assert proc.terminate.called, (
            f"Expected proc.terminate() to be called within {_WAIT_TIMEOUT}s"
        )

    def test_idle_worker_removed_from_procs(self, clean_state):
        """After TTL expiry the worker URL must be absent from _LAZY_WORKER_PROCS."""
        proc = _alive_proc()
        _mod._LAZY_WORKER_PROCS[_WORKER_KEY] = proc
        _mod._LAZY_WORKER_LAST_BUSY[_WORKER_KEY] = (
            time.monotonic() - _SHORT_TTL - 1.0
        )

        idle_health = {"status": "ok", "running_count": 0}

        with patch.object(_mod, "_probe_worker_health", return_value=idle_health):
            _mod._ensure_lazy_worker_reaper()

            deadline = time.monotonic() + _WAIT_TIMEOUT
            while time.monotonic() < deadline:
                with _mod._LAZY_WORKER_LOCK:
                    still_there = _WORKER_KEY in _mod._LAZY_WORKER_PROCS
                if not still_there:
                    break
                time.sleep(0.05)

        with _mod._LAZY_WORKER_LOCK:
            still_there = _WORKER_KEY in _mod._LAZY_WORKER_PROCS
        assert not still_there, "Idle worker must be removed from _LAZY_WORKER_PROCS"

    def test_busy_worker_not_terminated(self, clean_state):
        """A worker with running_count > 0 must not be terminated."""
        proc = _alive_proc()
        _mod._LAZY_WORKER_PROCS[_WORKER_KEY] = proc
        # Even if last_busy is old, the probe returns busy — TTL resets
        _mod._LAZY_WORKER_LAST_BUSY[_WORKER_KEY] = (
            time.monotonic() - _SHORT_TTL - 1.0
        )

        busy_health = {"status": "ok", "running_count": 3}

        with patch.object(_mod, "_probe_worker_health", return_value=busy_health):
            _mod._ensure_lazy_worker_reaper()

            # Wait long enough for reaper to fire a few times
            time.sleep(_FAST_INTERVAL * 6)

        assert not proc.terminate.called, (
            "proc.terminate() must NOT be called for a busy worker"
        )

    def test_disabled_ttl_never_terminates(self, clean_state, monkeypatch):
        """When ATLAS_LAZY_WORKER_IDLE_TTL_SEC=0 the idle path is skipped."""
        monkeypatch.setattr(_mod, "_LAZY_WORKER_IDLE_TTL_SEC", 0.0)

        proc = _alive_proc()
        _mod._LAZY_WORKER_PROCS[_WORKER_KEY] = proc
        _mod._LAZY_WORKER_LAST_BUSY[_WORKER_KEY] = time.monotonic() - 9999.0

        idle_health = {"status": "ok", "running_count": 0}

        with patch.object(_mod, "_probe_worker_health", return_value=idle_health):
            _mod._ensure_lazy_worker_reaper()
            time.sleep(_FAST_INTERVAL * 6)

        assert not proc.terminate.called, (
            "TTL=0 must disable idle-TTL termination"
        )
