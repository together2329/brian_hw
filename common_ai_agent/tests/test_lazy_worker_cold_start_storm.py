"""
tests/test_lazy_worker_cold_start_storm.py

Verify that a 12-way cold-start storm:
  1. Does not raise for any thread.
  2. Never exceeds ATLAS_LAZY_WORKER_SPAWN_PARALLEL (default 4) concurrent
     subprocess.Popen calls inside _LAZY_WORKER_SPAWN_SEM.
  3. Each call completes within the configured timeout.

No real processes or network connections are used.
"""
from __future__ import annotations

import os
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import MagicMock

import pytest

import src.atlas_api_jobs as _mod


# ── helpers ──────────────────────────────────────────────────────────────────

_NUM_WORKERS = 12
_BASE_PORT = 5621
_SPAWN_PARALLEL = 4          # matches env default
_HEALTH_DELAY = 0.05         # seconds before fake health returns "ok"
_TIMEOUT_S = 5.0             # generous; much less than the 15s production default


def _make_fake_popen(url: str) -> MagicMock:
    """Return a fake Popen whose .poll() returns None (alive)."""
    proc = MagicMock()
    proc.pid = hash(url) & 0xFFFF
    proc.poll.return_value = None   # stays alive
    return proc


class SpawnCounter:
    """Tracks peak concurrent Popen calls made inside _LAZY_WORKER_SPAWN_SEM.

    Because subprocess.Popen() is called synchronously inside
    ``with _LAZY_WORKER_SPAWN_SEM:``, the semaphore is held for the
    duration of the Popen call only — it is released immediately after
    Popen returns (the ready-wait loop runs *outside* the semaphore).
    So peak concurrency == max threads simultaneously inside fake_popen,
    which we measure with an enter/exit pair around the body of fake_popen.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._current = 0
        self.peak = 0
        self.total = 0

    def enter(self) -> None:
        """Call at the start of fake_popen body."""
        with self._lock:
            self._current += 1
            if self._current > self.peak:
                self.peak = self._current
            self.total += 1

    def exit(self) -> None:
        """Call just before fake_popen returns."""
        with self._lock:
            self._current -= 1


def _worker_url(port: int) -> str:
    return f"http://127.0.0.1:{port}"


def _make_job(port: int) -> dict:
    return {
        "job_id": uuid.uuid4().hex,
        "workflow": "rtl-gen",
        "worker": _worker_url(port),
        "project_root": "/tmp/fake_project",
    }


# ── fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _reset_lazy_worker_state(monkeypatch):
    """
    Isolate module-level state between test runs so the semaphore,
    proc dict, URL locks, and reaper flag start clean.

    Module globals accessed (src/atlas_api_jobs.py):
      L52  _LAZY_WORKER_PROCS
      L56  _LAZY_WORKER_URL_LOCKS
      L60  _LAZY_WORKER_SPAWN_SEM       -- recreated with test parallelism
      L66  _LAZY_WORKER_REAPER_STARTED
    """
    monkeypatch.setattr(_mod, "_LAZY_WORKER_PROCS", {})
    monkeypatch.setattr(_mod, "_LAZY_WORKER_URL_LOCKS", {})
    monkeypatch.setattr(_mod, "_LAZY_WORKER_LAST_BUSY", {})
    monkeypatch.setattr(_mod, "_LAZY_WORKER_REAPER_STARTED", False)
    monkeypatch.setattr(
        _mod, "_LAZY_WORKER_SPAWN_SEM", threading.Semaphore(_SPAWN_PARALLEL)
    )
    # Disable idle-TTL so the fast-looping reaper does not terminate
    # freshly-spawned workers before the storm test can assert spawn counts.
    monkeypatch.setattr(_mod, "_LAZY_WORKER_IDLE_TTL_SEC", 0.0)
    # Speed up the ready-wait polling loop (L2011: time.sleep(0.25))
    monkeypatch.setattr(time, "sleep", lambda _s: None)
    yield
    # Clean up any leftover procs dict entries
    _mod._LAZY_WORKER_PROCS.clear()
    _mod._LAZY_WORKER_URL_LOCKS.clear()
    _mod._LAZY_WORKER_LAST_BUSY.clear()


# ── tests ─────────────────────────────────────────────────────────────────────

class TestColdStartStorm:
    """12-way cold-start: semaphore serializes spawns; all calls succeed."""

    def test_all_calls_return_without_raising(self, monkeypatch):
        """All 12 concurrent _ensure_lazy_worker calls must complete without exception."""
        spawn_counter = SpawnCounter()
        self._patch_module(monkeypatch, spawn_counter)

        errors: list[Exception] = []
        with ThreadPoolExecutor(max_workers=_NUM_WORKERS) as pool:
            futures = {
                pool.submit(_mod._ensure_lazy_worker, _make_job(_BASE_PORT + i)): i
                for i in range(_NUM_WORKERS)
            }
            for fut in as_completed(futures):
                exc = fut.exception()
                if exc is not None:
                    errors.append(exc)

        assert errors == [], f"Unexpected exceptions: {errors}"

    def test_spawn_parallelism_never_exceeds_semaphore_limit(self, monkeypatch):
        """Peak concurrent Popen invocations must not exceed _SPAWN_PARALLEL (4)."""
        spawn_counter = SpawnCounter()
        self._patch_module(monkeypatch, spawn_counter)

        with ThreadPoolExecutor(max_workers=_NUM_WORKERS) as pool:
            futs = [
                pool.submit(_mod._ensure_lazy_worker, _make_job(_BASE_PORT + i))
                for i in range(_NUM_WORKERS)
            ]
            for f in as_completed(futs):
                f.exception()  # drain without re-raising

        assert spawn_counter.peak <= _SPAWN_PARALLEL, (
            f"Peak concurrent spawns {spawn_counter.peak} exceeded "
            f"semaphore limit {_SPAWN_PARALLEL}"
        )

    def test_exactly_one_spawn_per_distinct_worker_url(self, monkeypatch):
        """Each of the 12 distinct ports triggers exactly one Popen (no double-spawn)."""
        spawn_counter = SpawnCounter()
        self._patch_module(monkeypatch, spawn_counter)

        with ThreadPoolExecutor(max_workers=_NUM_WORKERS) as pool:
            futs = [
                pool.submit(_mod._ensure_lazy_worker, _make_job(_BASE_PORT + i))
                for i in range(_NUM_WORKERS)
            ]
            for f in as_completed(futs):
                f.exception()

        assert spawn_counter.total == _NUM_WORKERS, (
            f"Expected {_NUM_WORKERS} spawns, got {spawn_counter.total}"
        )

    def test_each_call_completes_within_timeout(self, monkeypatch):
        """Each thread finishes well within _TIMEOUT_S (health probes resolve fast)."""
        spawn_counter = SpawnCounter()
        self._patch_module(monkeypatch, spawn_counter)

        wall_times: list[float] = []
        lock = threading.Lock()

        def timed_call(port: int) -> None:
            t0 = time.monotonic()
            _mod._ensure_lazy_worker(_make_job(port))
            with lock:
                wall_times.append(time.monotonic() - t0)

        with ThreadPoolExecutor(max_workers=_NUM_WORKERS) as pool:
            futs = [pool.submit(timed_call, _BASE_PORT + i) for i in range(_NUM_WORKERS)]
            for f in as_completed(futs):
                f.exception()

        for elapsed in wall_times:
            assert elapsed < _TIMEOUT_S, (
                f"Call took {elapsed:.2f}s, exceeded limit {_TIMEOUT_S}s"
            )

    # ── shared patching helper ────────────────────────────────────────────────

    def _patch_module(self, monkeypatch, spawn_counter: SpawnCounter) -> None:
        """Wire all module-level side-effects to fast, in-process fakes."""

        # Enable lazy workers (L1655: _lazy_workers_enabled checks env)
        monkeypatch.setenv("ATLAS_LAZY_WORKERS", "1")

        # Lower the start timeout so any poll loop exits quickly (L1977)
        monkeypatch.setenv("ATLAS_LAZY_WORKER_START_TIMEOUT", str(_TIMEOUT_S))

        # _local_worker_target must return a valid (host, port) so the spawn
        # branch is entered (L1903-1906).
        monkeypatch.setattr(
            _mod, "_local_worker_target",
            lambda url: ("127.0.0.1", int(url.split(":")[-1]))
        )

        # _worker_url_is_shared_default is called at L1907; just return False.
        monkeypatch.setattr(
            _mod, "_worker_url_is_shared_default",
            lambda workflow, url: False
        )

        # _lazy_worker_command must return a list (L1927); content doesn't matter.
        monkeypatch.setattr(
            _mod, "_lazy_worker_command",
            lambda *, job, host, port, all_workflows: ["echo", "fake"]
        )

        # subprocess.Popen: return a fake proc, track concurrency (L1954).
        # enter() before building the proc, exit() before returning so
        # _current accurately reflects threads inside the Popen call body.
        def fake_popen(cmd, **kwargs):
            spawn_counter.enter()
            try:
                # derive a stable key from the port arg in cmd
                port_str = cmd[cmd.index("--port") + 1] if "--port" in cmd else "0"
                return _make_fake_popen(f"http://127.0.0.1:{port_str}")
            finally:
                spawn_counter.exit()

        monkeypatch.setattr(_mod.subprocess, "Popen", fake_popen)

        # _probe_worker_health: first call returns unreachable, second returns ok.
        # We use a per-URL call counter so each URL independently becomes healthy.
        call_counts: dict[str, int] = {}
        call_lock = threading.Lock()

        def fake_probe(worker_url: str, timeout: float = 1.0) -> dict:
            with call_lock:
                n = call_counts.get(worker_url, 0)
                call_counts[worker_url] = n + 1
            # _ensure_lazy_worker calls _probe_worker_health three times per URL:
            #   1. L1897: pre-lock early-exit check      -> unreachable (enter lock)
            #   2. L1915: re-check inside url_lock       -> unreachable (enter spawn)
            #   3. L1996: ready-wait loop after spawn    -> ok (return success)
            if n < 2:
                return {"status": "unreachable"}
            return {"status": "ok"}

        monkeypatch.setattr(_mod, "_probe_worker_health", fake_probe)

        # Suppress side-effects that would write to disk or start real threads.
        monkeypatch.setattr(_mod, "_register_lazy_worker_atexit", lambda: None)
        monkeypatch.setattr(_mod, "_ensure_lazy_worker_reaper", lambda: None)
        monkeypatch.setattr(_mod, "_finish_job_db_run", lambda *a, **k: None)

        # Path.mkdir: avoid filesystem writes from log_dir.mkdir (L1948)
        monkeypatch.setattr(
            "pathlib.Path.mkdir",
            lambda self, *a, **k: None,
        )
        # Path.open: avoid real file opens for log_fh (L1950)
        monkeypatch.setattr(
            "pathlib.Path.open",
            lambda self, *a, **k: (_ for _ in ()).throw(OSError("mocked")),
        )
