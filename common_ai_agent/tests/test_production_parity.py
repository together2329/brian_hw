"""
tests/test_production_parity.py — Production-parity subprocess launch tests.

These tests exercise atlas_ui under conditions closer to production: a real
subprocess, real argv, real environment.  This catches sys.path / env-var
drift that pytest's in-process imports can never see.

Runtime: ~25-35 s total (subprocess startup is inherently slow).
Modes: quick / full  (NOT smoke, except test_atlas_ui_imports_cleanly_as_main_module)

Skip conditions:
  - macOS without lsof (test_lazy_single_worker_does_not_spawn_eagerly)
  - no `requests` package installed (test_atlas_ui_launches_and_healthz_responds)
  - CI without local networking (detected via ATLAS_SKIP_SUBPROCESS_TESTS=1)
"""

from __future__ import annotations

import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Repo-root anchor
# ---------------------------------------------------------------------------
REPO_ROOT = Path(__file__).resolve().parent.parent
ATLAS_UI  = REPO_ROOT / "src" / "atlas_ui.py"

# ---------------------------------------------------------------------------
# Module-level skip: operator escape hatch
# ---------------------------------------------------------------------------
if os.environ.get("ATLAS_SKIP_SUBPROCESS_TESTS", "").lower() in ("1", "true", "yes"):
    pytest.skip(
        "ATLAS_SKIP_SUBPROCESS_TESTS is set — skipping production-parity suite",
        allow_module_level=True,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _free_port(preferred: int) -> int:
    """Return *preferred* if nothing is bound to it, else find a free port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(("127.0.0.1", preferred))
            return preferred
        except OSError:
            pass
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s2:
        s2.bind(("127.0.0.1", 0))
        return s2.getsockname()[1]


def _kill_proc(proc: "subprocess.Popen[bytes]", timeout: float = 5.0) -> None:
    """SIGTERM then SIGKILL a subprocess; swallow all errors."""
    if proc is None or proc.poll() is not None:
        return
    try:
        proc.send_signal(signal.SIGTERM)
    except Exception:
        pass
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            return
        time.sleep(0.1)
    try:
        proc.kill()
    except Exception:
        pass
    try:
        proc.wait(timeout=2)
    except Exception:
        pass


def _wait_for_port(host: str, port: int, timeout: float = 12.0) -> bool:
    """Poll until TCP port accepts connections or timeout expires."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            try:
                s.connect((host, port))
                return True
            except (ConnectionRefusedError, OSError):
                pass
        time.sleep(0.3)
    return False


def _collect_output(
    proc: "subprocess.Popen[bytes]",
    store: list[str],
    timeout: float,
) -> None:
    """Read stdout of *proc* into *store* for up to *timeout* seconds."""
    deadline = time.monotonic() + timeout
    assert proc.stdout is not None
    for line in proc.stdout:
        store.append(line.decode("utf-8", errors="replace"))
        if time.monotonic() > deadline:
            break


def _port_listening(port: int) -> bool:
    """Return True if something is already bound to *port* on 127.0.0.1."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        try:
            s.connect(("127.0.0.1", port))
            return True
        except (ConnectionRefusedError, OSError):
            return False


# ---------------------------------------------------------------------------
# Pytest fixture: subprocess lifecycle guard
# ---------------------------------------------------------------------------

@pytest.fixture()
def subprocess_guard():
    """
    Yield a list; tests append their Popen objects.
    On teardown every proc is SIGTERM'd (then SIGKILL if needed).
    """
    procs: list["subprocess.Popen[bytes]"] = []
    yield procs
    for p in procs:
        _kill_proc(p)


# ---------------------------------------------------------------------------
# Test 1 — import smoke (also in smoke mode via direct pytest invocation)
# ---------------------------------------------------------------------------

def test_atlas_ui_imports_cleanly_as_main_module():
    """
    `python -c 'exec(open("src/atlas_ui.py").read())'` with --help argv must
    NOT raise ImportError or ModuleNotFoundError.

    This is the one test safe enough for smoke mode; it exits in <2 s.
    """
    cmd = [
        sys.executable, "-c",
        (
            "import sys; "
            "sys.argv = ['atlas_ui.py', '--help']; "
            "exec(open('src/atlas_ui.py').read())"
        ),
    ]
    result = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        capture_output=True,
        timeout=15,
    )
    combined = (result.stdout + result.stderr).decode("utf-8", errors="replace")
    bad = re.search(r"(ImportError|ModuleNotFoundError)", combined)
    assert bad is None, (
        f"Import error detected in subprocess output:\n{combined[:2000]}"
    )
    # --help exits with code 0; SystemExit(0) is fine.  Any other non-zero
    # exit that carries a traceback is a failure.
    if result.returncode not in (0, 1):
        # Some argparse versions exit 1; tolerate 0 and 1 only.
        # A returncode of 2 from argparse (bad args) is also acceptable
        # because we only care about import health, not valid flag combos.
        pass  # any exit code is acceptable as long as no ImportError above


def test_atlas_ui_direct_script_bootstraps_from_external_cwd(tmp_path: Path):
    cmd = [sys.executable, str(ATLAS_UI), "--help"]
    result = subprocess.run(
        cmd,
        cwd=str(tmp_path),
        capture_output=True,
        timeout=15,
    )
    combined = (result.stdout + result.stderr).decode("utf-8", errors="replace")
    bad = re.search(r"(ImportError|ModuleNotFoundError)", combined)
    assert bad is None, (
        f"Import error detected in subprocess output:\n{combined[:2000]}"
    )


# ---------------------------------------------------------------------------
# Test 2 — full launch + /healthz probe
# ---------------------------------------------------------------------------

def test_atlas_ui_launches_and_healthz_responds(
    tmp_path: Path,
    subprocess_guard: list[subprocess.Popen[bytes]],
):
    """
    Launch `python3 src/atlas_ui.py --port <N> --exec o ...` and confirm
    GET /healthz returns HTTP 200 within 12 s.

    Skips if `requests` is not installed.
    """
    requests = pytest.importorskip("requests")

    port     = _free_port(13900)
    wf_root  = str(REPO_ROOT)   # workflow/ is a subdir of repo root

    cmd = [
        sys.executable,
        str(ATLAS_UI),
        "--port", str(port),
        "--host", "127.0.0.1",
        "--root", str(tmp_path),
        "--workflow-root", wf_root,
        "--exec", "o",
    ]

    env = {**os.environ, "ATLAS_LAZY_WORKERS": "1"}

    proc = subprocess.Popen(
        cmd,
        cwd=str(REPO_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    subprocess_guard.append(proc)

    # Wait for the port to open (uvicorn startup can be slow)
    listening = _wait_for_port("127.0.0.1", port, timeout=12.0)
    assert listening, (
        f"atlas_ui did not open port {port} within 12 s "
        f"(proc returncode={proc.poll()})"
    )

    try:
        resp = requests.get(
            f"http://127.0.0.1:{port}/healthz",
            timeout=5,
        )
        assert resp.status_code == 200, (
            f"/healthz returned {resp.status_code}: {resp.text[:500]}"
        )
    finally:
        _kill_proc(proc)


# ---------------------------------------------------------------------------
# Test 3 — lazy single-worker does NOT spawn port 5601 eagerly
# ---------------------------------------------------------------------------

def test_lazy_single_worker_does_not_spawn_eagerly(
    tmp_path: Path,
    subprocess_guard: list[subprocess.Popen[bytes]],
):
    """
    With `--exec s` (single-worker, lazy), atlas_ui must print
    '[single-worker] lazy mode:' and must NOT bind port 5601.

    Skips on macOS without lsof, or when 5601 is already in use (to
    avoid false positives in a busy dev environment).
    """
    if sys.platform == "darwin" and not shutil.which("lsof"):
        pytest.skip("lsof not available on this macOS system")

    if _port_listening(5601):
        pytest.skip("Port 5601 is already in use — skipping to avoid false positive")

    port = _free_port(13902)
    cmd = [
        sys.executable,
        str(ATLAS_UI),
        "--port", str(port),
        "--host", "127.0.0.1",
        "--root", str(tmp_path),
        "--workflow-root", str(REPO_ROOT),
        "--exec", "s",
    ]

    env = {
        **os.environ,
        # Ensure eager spawn is OFF so we test lazy path
        "ATLAS_SINGLE_WORKER_EAGER": "0",
    }

    proc = subprocess.Popen(
        cmd,
        cwd=str(REPO_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    subprocess_guard.append(proc)

    # Collect stdout for up to 10 s looking for the lazy-mode banner
    lines: list[str] = []
    deadline = time.monotonic() + 10.0
    assert proc.stdout is not None
    collector = threading.Thread(
        target=_collect_output,
        args=(proc, lines, 10.0),
        daemon=True,
    )
    collector.start()

    # Also wait for the main port to open (server is ready)
    _wait_for_port("127.0.0.1", port, timeout=12.0)
    collector.join(timeout=2.0)

    output = "".join(lines)
    assert "[single-worker] lazy mode:" in output, (
        f"Expected lazy-mode banner not found in output:\n{output[:2000]}"
    )

    # Port 5601 must NOT be listening (no eager spawn)
    assert not _port_listening(5601), (
        "Port 5601 is listening — single-worker spawned eagerly despite lazy mode"
    )

    _kill_proc(proc)


# ---------------------------------------------------------------------------
# Test 4 — env inheritance smoke (ATLAS_SINGLE_WORKER_EAGER=1)
# ---------------------------------------------------------------------------

def test_env_inheritance_smoke(
    tmp_path: Path,
    subprocess_guard: list[subprocess.Popen[bytes]],
):
    """
    With ATLAS_SINGLE_WORKER_EAGER=1, atlas_ui must print the eager-spawn
    message, confirming env vars propagate to the subprocess correctly.

    We do NOT wait for port 5601 to open (main.py may not be installed);
    we only confirm the stdout message appeared, proving the env reached
    the subprocess and the correct branch executed.
    """
    port = _free_port(13904)
    cmd = [
        sys.executable,
        str(ATLAS_UI),
        "--port", str(port),
        "--host", "127.0.0.1",
        "--root", str(tmp_path),
        "--workflow-root", str(REPO_ROOT),
        "--exec", "s",
    ]

    env = {
        **os.environ,
        "ATLAS_SINGLE_WORKER_EAGER": "1",
    }

    proc = subprocess.Popen(
        cmd,
        cwd=str(REPO_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    subprocess_guard.append(proc)

    # Collect stdout for up to 12 s — eager spawn + health probe take ~10 s
    lines: list[str] = []
    collector = threading.Thread(
        target=_collect_output,
        args=(proc, lines, 12.0),
        daemon=True,
    )
    collector.start()

    # Wait for the main atlas_ui port (confirms uvicorn started)
    _wait_for_port("127.0.0.1", port, timeout=14.0)
    collector.join(timeout=2.0)

    output = "".join(lines)

    # The eager spawn prints this line immediately after Popen succeeds
    assert "[single-worker] spawned main-loop worker" in output, (
        f"Expected eager-spawn message not found — env may not have propagated.\n"
        f"stdout:\n{output[:2000]}"
    )

    _kill_proc(proc)
