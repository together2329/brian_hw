"""
tests/test_lazy_worker_reaper.py

Verify the lazy-worker reaper thread:
  1. Detects a dead worker (poll() != None) within ATLAS_LAZY_WORKER_REAPER_INTERVAL.
  2. Marks associated _jobs entries as "error" with a message containing "rc=<N>".
  3. Removes the dead proc from _LAZY_WORKER_PROCS.

No real processes or network connections are used.

Module globals referenced (src/atlas_api_jobs.py):
  L52  _LAZY_WORKER_PROCS
  L48  _jobs  / L48 _jobs_lock
  L66  _LAZY_WORKER_REAPER_STARTED
  L67  _LAZY_WORKER_REAPER_INTERVAL
"""
from __future__ import annotations

import threading
import time
import uuid
from unittest.mock import MagicMock

import pytest

import src.atlas_api_jobs as _mod


_WORKER_URL = "http://127.0.0.1:5621"
_WORKER_KEY = _WORKER_URL.rstrip("/")
_FAST_INTERVAL = 0.15           # seconds — low enough to complete in CI
_WAIT_TIMEOUT = 3.0             # max seconds to wait for reaper to act


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def clean_state(monkeypatch):
    """
    Reset all module-level lazy-worker state before each test so a
    previously started reaper thread does not interfere.

    Patching _LAZY_WORKER_REAPER_STARTED to False allows
    _ensure_lazy_worker_reaper() to start a fresh daemon thread.

    Patching _LAZY_WORKER_REAPER_INTERVAL to a small value (L67-68)
    makes the reaper fire within the test's wall-clock budget.
    """
    # Stash originals
    orig_procs = dict(_mod._LAZY_WORKER_PROCS)
    orig_jobs = dict(_mod._jobs)
    orig_started = _mod._LAZY_WORKER_REAPER_STARTED
    orig_interval = _mod._LAZY_WORKER_REAPER_INTERVAL

    # Clear shared dicts
    _mod._LAZY_WORKER_PROCS.clear()
    with _mod._jobs_lock:
        _mod._jobs.clear()

    # Reset reaper-started flag so a new thread can be launched
    monkeypatch.setattr(_mod, "_LAZY_WORKER_REAPER_STARTED", False)

    # Speed up the reaper loop (L1847: time.sleep(_LAZY_WORKER_REAPER_INTERVAL))
    monkeypatch.setattr(_mod, "_LAZY_WORKER_REAPER_INTERVAL", _FAST_INTERVAL)

    # Suppress DB writes from _mark_jobs_failed_for_worker -> _finish_job_db_run (L1829)
    monkeypatch.setattr(_mod, "_finish_job_db_run", lambda *a, **k: None)

    yield

    # Restore (best-effort; daemon thread will die with the process anyway)
    _mod._LAZY_WORKER_PROCS.clear()
    _mod._LAZY_WORKER_PROCS.update(orig_procs)
    with _mod._jobs_lock:
        _mod._jobs.clear()
        _mod._jobs.update(orig_jobs)
    monkeypatch.setattr(_mod, "_LAZY_WORKER_REAPER_STARTED", orig_started)
    monkeypatch.setattr(_mod, "_LAZY_WORKER_REAPER_INTERVAL", orig_interval)


def _dead_popen(returncode: int = -9) -> MagicMock:
    proc = MagicMock()
    proc.pid = 99999
    proc.poll.return_value = returncode
    return proc


def _insert_running_job(worker_url: str) -> str:
    """Insert a synthetic running job for worker_url into _jobs. Return job_id."""
    job_id = uuid.uuid4().hex
    with _mod._jobs_lock:
        _mod._jobs[job_id] = {
            "job_id": job_id,
            "status": "running",
            "worker": worker_url,
            "workflow": "rtl-gen",
        }
    return job_id


def _wait_for_status(job_id: str, expected: str, timeout: float = _WAIT_TIMEOUT) -> bool:
    """Poll _jobs[job_id]['status'] until it equals expected or timeout expires."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with _mod._jobs_lock:
            status = _mod._jobs.get(job_id, {}).get("status")
        if status == expected:
            return True
        time.sleep(0.05)
    return False


# ── tests ─────────────────────────────────────────────────────────────────────

class TestLazyWorkerReaper:
    """Reaper daemon marks dead-worker jobs as error and cleans up _LAZY_WORKER_PROCS."""

    def test_job_marked_error_after_worker_dies(self, clean_state):
        """Running job transitions to 'error' once the reaper detects rc=-9."""
        proc = _dead_popen(returncode=-9)
        _mod._LAZY_WORKER_PROCS[_WORKER_KEY] = proc
        job_id = _insert_running_job(_WORKER_URL)

        _mod._ensure_lazy_worker_reaper()

        reached = _wait_for_status(job_id, "error")
        assert reached, (
            f"Job {job_id} did not transition to 'error' within {_WAIT_TIMEOUT}s. "
            f"Current status: {_mod._jobs.get(job_id, {}).get('status')!r}"
        )

    def test_error_message_contains_returncode(self, clean_state):
        """The error field must reference the worker's exit code (rc=-9)."""
        proc = _dead_popen(returncode=-9)
        _mod._LAZY_WORKER_PROCS[_WORKER_KEY] = proc
        job_id = _insert_running_job(_WORKER_URL)

        _mod._ensure_lazy_worker_reaper()
        _wait_for_status(job_id, "error")

        with _mod._jobs_lock:
            job = _mod._jobs.get(job_id, {})
        error_msg = str(job.get("error") or "")
        assert "rc=-9" in error_msg, (
            f"Expected 'rc=-9' in error message, got: {error_msg!r}"
        )

    def test_dead_proc_removed_from_lazy_worker_procs(self, clean_state):
        """After reaping, the dead proc must be absent from _LAZY_WORKER_PROCS."""
        proc = _dead_popen(returncode=-9)
        _mod._LAZY_WORKER_PROCS[_WORKER_KEY] = proc
        job_id = _insert_running_job(_WORKER_URL)

        _mod._ensure_lazy_worker_reaper()
        _wait_for_status(job_id, "error")

        # Give the reaper one more interval to finalize the proc removal
        time.sleep(_FAST_INTERVAL * 2)

        with _mod._LAZY_WORKER_LOCK:
            still_present = _WORKER_KEY in _mod._LAZY_WORKER_PROCS
        assert not still_present, (
            "Dead proc was not removed from _LAZY_WORKER_PROCS after reaping"
        )

    def test_alive_worker_job_not_marked_error(self, clean_state):
        """A job whose worker is still alive must remain in 'running' status."""
        alive_proc = MagicMock()
        alive_proc.pid = 12345
        alive_proc.poll.return_value = None   # alive

        _mod._LAZY_WORKER_PROCS[_WORKER_KEY] = alive_proc
        job_id = _insert_running_job(_WORKER_URL)

        _mod._ensure_lazy_worker_reaper()

        # Wait long enough for the reaper to have fired at least once
        time.sleep(_FAST_INTERVAL * 3)

        with _mod._jobs_lock:
            status = _mod._jobs.get(job_id, {}).get("status")
        assert status == "running", (
            f"Expected job to remain 'running', got {status!r}"
        )

    def test_only_matching_worker_jobs_are_failed(self, clean_state):
        """Jobs assigned to a different worker must not be touched by the reaper."""
        other_url = "http://127.0.0.1:5999"
        other_key = other_url.rstrip("/")

        dead_proc = _dead_popen(returncode=1)
        _mod._LAZY_WORKER_PROCS[_WORKER_KEY] = dead_proc

        dead_job_id = _insert_running_job(_WORKER_URL)
        safe_job_id = _insert_running_job(other_url)

        _mod._ensure_lazy_worker_reaper()
        _wait_for_status(dead_job_id, "error")

        with _mod._jobs_lock:
            safe_status = _mod._jobs.get(safe_job_id, {}).get("status")
        assert safe_status == "running", (
            f"Job on unrelated worker should stay 'running', got {safe_status!r}"
        )

    def test_reaper_thread_is_daemon(self, clean_state, monkeypatch):
        """The reaper thread must be a daemon so it never blocks process exit."""
        launched: list[threading.Thread] = []
        real_thread = threading.Thread

        def capturing_thread(*args, **kwargs):
            t = real_thread(*args, **kwargs)
            launched.append(t)
            return t

        monkeypatch.setattr(threading, "Thread", capturing_thread)
        _mod._ensure_lazy_worker_reaper()

        assert launched, "No thread was started by _ensure_lazy_worker_reaper()"
        assert launched[-1].daemon, "Reaper thread must be a daemon thread"
