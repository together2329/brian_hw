"""
tests/test_lazy_worker_real_cold_start.py — Real-subprocess cold-start storm.

Spawns 12 real uvicorn workers simultaneously (one per canonical workflow port
5621-5632) and measures time-to-last-ready plus peak RSS per PID.

Gate: only runs when ATLAS_LOAD_TEST=1.  The default CI sweep never touches
this file.

Runtime: up to 3 minutes (60 s health-poll timeout × sequential check path;
actual parallel spin-up is typically 30-90 s on a modern laptop).
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
import unittest
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pytest

# ---------------------------------------------------------------------------
# Module-level gate
# ---------------------------------------------------------------------------
if os.environ.get("ATLAS_LOAD_TEST") != "1":
    pytest.skip(
        "ATLAS_LOAD_TEST != 1 — skipping real cold-start load test",
        allow_module_level=True,
    )

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
MAIN_PY = REPO_ROOT / "src" / "main.py"

# Canonical ports for the 12 per-workflow workers (5621-5632).
WORKER_PORTS: List[int] = list(range(5621, 5633))

HEALTH_TIMEOUT_SEC = 60.0   # per-worker poll deadline
POLL_INTERVAL_SEC  = 0.5    # between /health probes
SIGKILL_GRACE_SEC  = 5.0    # SIGTERM → SIGKILL window

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rss_bytes(pid: int) -> int:
    """Return RSS in bytes for *pid*.  Uses psutil when available, falls back
    to `ps -o rss= -p PID` (macOS / Linux).  Returns 0 on any error."""
    try:
        import psutil  # type: ignore
        return psutil.Process(pid).memory_info().rss
    except Exception:
        pass
    try:
        out = subprocess.check_output(
            ["ps", "-o", "rss=", "-p", str(pid)],
            stderr=subprocess.DEVNULL,
        )
        kb = int(out.strip())
        return kb * 1024
    except Exception:
        return 0


def _health_ok(port: int) -> bool:
    """Single non-blocking HTTP GET to /health; return True on HTTP 200."""
    import urllib.request
    import urllib.error
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/health", timeout=2
        ) as resp:
            return resp.status == 200
    except Exception:
        return False


def _poll_until_ready(port: int, deadline: float) -> Optional[float]:
    """Poll /health until 200 or *deadline* (monotonic).
    Returns elapsed seconds since *poll_start* on success, None on timeout."""
    poll_start = time.monotonic()
    while time.monotonic() < deadline:
        if _health_ok(port):
            return time.monotonic() - poll_start
        time.sleep(POLL_INTERVAL_SEC)
    return None


def _kill_proc(proc: subprocess.Popen, grace: float = SIGKILL_GRACE_SEC) -> None:
    """SIGTERM → wait → SIGKILL; swallow all errors."""
    if proc.poll() is not None:
        return
    try:
        proc.send_signal(signal.SIGTERM)
    except Exception:
        pass
    deadline = time.monotonic() + grace
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            return
        time.sleep(0.2)
    try:
        proc.kill()
    except Exception:
        pass
    try:
        proc.wait(timeout=2)
    except Exception:
        pass


def _port_free(port: int) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        try:
            s.connect(("127.0.0.1", port))
            return False   # something answered → port is occupied
        except (ConnectionRefusedError, OSError):
            return True


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture()
def all_worker_procs():
    """Yield (procs dict).  Teardown terminates every process."""
    procs: Dict[int, subprocess.Popen] = {}
    yield procs
    for proc in procs.values():
        _kill_proc(proc)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestColdStartStorm:
    """Spawn 12 real workers simultaneously; measure time-to-last-ready."""

    def test_all_12_workers_reach_health_within_60s(self, all_worker_procs):
        """All 12 workers spawned simultaneously must respond to /health=ok
        within 60 seconds.  Prints a timing table; no hard latency assertion
        (this is a benchmark, not a strict SLA gate)."""

        # Pre-flight: warn if any port is already occupied (don't abort —
        # the test will simply time-out on that port and report it clearly).
        occupied = [p for p in WORKER_PORTS if not _port_free(p)]
        if occupied:
            print(f"\n[cold-start-storm] WARNING: ports already in use: {occupied}")
            print("  These workers will likely fail the health check. "
                  "Run `lsof -iTCP:5621-5632` to find and stop them.")

        spawn_start = time.monotonic()

        # Spawn all 12 in a tight loop — no semaphore so we stress cold-start.
        for port in WORKER_PORTS:
            cmd = [
                sys.executable,
                str(MAIN_PY),
                "--serve",
                "--host", "127.0.0.1",
                "--port", str(port),
                "--all-workflows",
            ]
            proc = subprocess.Popen(
                cmd,
                cwd=str(REPO_ROOT),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            all_worker_procs[port] = proc

        spawn_elapsed = time.monotonic() - spawn_start
        print(f"\n[cold-start-storm] spawned {len(WORKER_PORTS)} workers in "
              f"{spawn_elapsed:.2f}s")

        # Poll each worker in parallel using threads so we measure wall-clock.
        global_deadline = time.monotonic() + HEALTH_TIMEOUT_SEC
        ready_times: Dict[int, Optional[float]] = {}
        rss_at_peak: Dict[int, int] = {}

        import threading

        def _check(port: int) -> None:
            elapsed = _poll_until_ready(port, global_deadline)
            ready_times[port] = elapsed
            rss_at_peak[port] = _rss_bytes(all_worker_procs[port].pid)

        threads = [threading.Thread(target=_check, args=(p,), daemon=True)
                   for p in WORKER_PORTS]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=HEALTH_TIMEOUT_SEC + 5)

        # Print timing table.
        print("\n[cold-start-storm] Results:")
        print(f"  {'Port':>6}  {'Ready (s)':>10}  {'RSS (MB)':>10}  Status")
        print(f"  {'-'*6}  {'-'*10}  {'-'*10}  {'-'*8}")
        failed_ports = []
        for port in WORKER_PORTS:
            elapsed = ready_times.get(port)
            rss_mb  = rss_at_peak.get(port, 0) / (1024 * 1024)
            status  = "OK" if elapsed is not None else "TIMEOUT"
            if elapsed is None:
                failed_ports.append(port)
            elapsed_str = f"{elapsed:.2f}" if elapsed is not None else "—"
            print(f"  {port:>6}  {elapsed_str:>10}  {rss_mb:>9.1f}M  {status}")

        ready_count = sum(1 for v in ready_times.values() if v is not None)
        last_ready  = max((v for v in ready_times.values() if v is not None),
                          default=None)
        print(f"\n  Workers ready: {ready_count}/{len(WORKER_PORTS)}")
        if last_ready is not None:
            print(f"  Time to last worker ready: {last_ready:.2f}s")

        assert len(failed_ports) == 0, (
            f"Workers on ports {failed_ports} did not reach /health=ok "
            f"within {HEALTH_TIMEOUT_SEC}s.  "
            f"Check that src/main.py --serve starts cleanly on those ports."
        )
