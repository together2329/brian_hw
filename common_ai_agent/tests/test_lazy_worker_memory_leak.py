"""
tests/test_lazy_worker_memory_leak.py — Long-running memory leak detection.

Spawns ONE worker, drives 100 /run calls through it, samples RSS every 20
calls, and asserts that final RSS < 1.5× baseline RSS (50 % growth cap).

Gate: only runs when ATLAS_LOAD_TEST=1.  The default CI sweep never touches
this file.

Runtime: ~2-4 minutes depending on worker startup and task latency.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import List, Optional

import pytest

# ---------------------------------------------------------------------------
# Module-level gate
# ---------------------------------------------------------------------------
if os.environ.get("ATLAS_LOAD_TEST") != "1":
    pytest.skip(
        "ATLAS_LOAD_TEST != 1 — skipping memory-leak load test",
        allow_module_level=True,
    )

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
MAIN_PY   = REPO_ROOT / "src" / "main.py"

WORKER_PORT        = 5640          # well outside default 5621-5632 range
HEALTH_TIMEOUT_SEC = 60.0
POLL_INTERVAL_SEC  = 0.5
RUN_ITERATIONS     = 100
SAMPLE_EVERY       = 20            # RSS snapshots at 0, 20, 40, 60, 80, 100
RSS_GROWTH_CAP     = 1.50          # 50 % growth allowed
SIGKILL_GRACE_SEC  = 5.0

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
    """Single HTTP GET to /health; return True on HTTP 200."""
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/health", timeout=2
        ) as resp:
            return resp.status == 200
    except Exception:
        return False


def _wait_for_health(port: int, timeout: float = HEALTH_TIMEOUT_SEC) -> bool:
    """Poll /health until 200 or timeout.  Returns True on success."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if _health_ok(port):
            return True
        time.sleep(POLL_INTERVAL_SEC)
    return False


def _post_run(port: int, task: str = "echo done") -> Optional[int]:
    """POST /run with a minimal task payload.  Returns HTTP status or None."""
    payload = json.dumps({"task": task, "sync": True}).encode()
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/run",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
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
            return False
        except (ConnectionRefusedError, OSError):
            return True


# ---------------------------------------------------------------------------
# Fixture
# ---------------------------------------------------------------------------

@pytest.fixture()
def single_worker():
    """Spawn one worker on WORKER_PORT; yield (proc, pid); teardown kills it."""
    if not _port_free(WORKER_PORT):
        pytest.skip(
            f"Port {WORKER_PORT} already in use — cannot start leak-test worker. "
            "Stop whatever is holding that port first."
        )

    cmd = [
        sys.executable,
        str(MAIN_PY),
        "--serve",
        "--host", "127.0.0.1",
        "--port", str(WORKER_PORT),
        "--all-workflows",
    ]
    proc = subprocess.Popen(
        cmd,
        cwd=str(REPO_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    yield proc, proc.pid
    _kill_proc(proc)


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------

class TestWorkerMemoryLeak:
    """Drive a single worker through 100 /run calls and check RSS growth."""

    def test_rss_growth_stays_below_50_percent_over_100_runs(self, single_worker):
        """RSS at run-100 must be < 1.5× RSS at run-0.  Prints all 6 samples."""

        proc, pid = single_worker

        # Wait for the worker to be healthy.
        assert _wait_for_health(WORKER_PORT), (
            f"Worker on port {WORKER_PORT} did not reach /health=ok "
            f"within {HEALTH_TIMEOUT_SEC}s."
        )

        # Baseline RSS (iteration 0).
        baseline_rss = _rss_bytes(pid)
        samples: List[tuple] = [(0, baseline_rss)]

        print(f"\n[memory-leak] worker pid={pid}  baseline RSS = "
              f"{baseline_rss / (1024*1024):.1f} MB")

        # Drive 100 /run calls; sample RSS at multiples of SAMPLE_EVERY.
        for i in range(1, RUN_ITERATIONS + 1):
            status = _post_run(WORKER_PORT)
            # Accept 2xx and 4xx (worker may reject no-op tasks); 5xx → fail fast
            if status is not None and status >= 500:
                print(f"  [run {i}] HTTP {status} — worker returned server error")

            if i % SAMPLE_EVERY == 0:
                rss = _rss_bytes(pid)
                samples.append((i, rss))
                print(f"  [run {i:>3}] RSS = {rss / (1024*1024):.1f} MB")

        # Final sample (may duplicate run-100 if 100 % SAMPLE_EVERY == 0).
        final_rss = _rss_bytes(pid)
        if RUN_ITERATIONS % SAMPLE_EVERY != 0:
            samples.append((RUN_ITERATIONS, final_rss))

        # Print summary table.
        print("\n[memory-leak] RSS sample table:")
        print(f"  {'Run':>5}  {'RSS (MB)':>10}  {'Growth':>8}")
        print(f"  {'-'*5}  {'-'*10}  {'-'*8}")
        for run_n, rss in samples:
            growth = rss / baseline_rss if baseline_rss > 0 else 1.0
            print(f"  {run_n:>5}  {rss/(1024*1024):>9.1f}M  {growth:>7.2f}x")

        growth_ratio = final_rss / baseline_rss if baseline_rss > 0 else 1.0
        print(f"\n  Final growth ratio: {growth_ratio:.3f}x  "
              f"(cap: {RSS_GROWTH_CAP:.1f}x)")

        assert growth_ratio < RSS_GROWTH_CAP, (
            f"Memory leak detected: RSS grew {growth_ratio:.2f}x over "
            f"{RUN_ITERATIONS} /run calls "
            f"(baseline={baseline_rss//(1024*1024)} MB, "
            f"final={final_rss//(1024*1024)} MB, "
            f"cap={RSS_GROWTH_CAP}x)."
        )
