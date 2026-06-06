import signal
import subprocess
import sys
import time


class _ShutdownServerState:
    def __init__(self):
        self.should_exit = False


class _ServerState:
    def __init__(self, *, should_exit=False):
        self.should_exit = should_exit
        self.force_exit = False
        self._captured_signals = []


def test_atlas_uvicorn_exit_signal_ignores_first_sigint():
    import src.atlas_runtime_run as atlas_runtime_run

    state = _ServerState()

    atlas_runtime_run._handle_atlas_uvicorn_exit_signal(state, signal.SIGINT)

    assert state.should_exit is False
    assert state.force_exit is False
    assert state._captured_signals == []


def test_atlas_uvicorn_exit_signal_ignores_repeated_sigint():
    import src.atlas_runtime_run as atlas_runtime_run

    state = _ServerState()

    atlas_runtime_run._handle_atlas_uvicorn_exit_signal(state, signal.SIGINT)
    atlas_runtime_run._handle_atlas_uvicorn_exit_signal(state, signal.SIGINT)

    assert state.should_exit is False
    assert state.force_exit is False
    assert state._captured_signals == []


def test_atlas_uvicorn_exit_signal_sigint_does_not_force_existing_shutdown():
    import src.atlas_runtime_run as atlas_runtime_run

    state = _ServerState(should_exit=True)

    atlas_runtime_run._handle_atlas_uvicorn_exit_signal(state, signal.SIGINT)

    assert state.should_exit is True
    assert state.force_exit is False
    assert state._captured_signals == []


def test_atlas_uvicorn_exit_signal_keeps_non_sigint_reraise():
    import src.atlas_runtime_run as atlas_runtime_run

    state = _ServerState()

    atlas_runtime_run._handle_atlas_uvicorn_exit_signal(state, signal.SIGTERM)

    assert state.should_exit is True
    assert state.force_exit is False
    assert state._captured_signals == [signal.SIGTERM]


def test_stdin_shutdown_watcher_requests_graceful_uvicorn_exit():
    import threading
    import src.atlas_runtime_run as atlas_runtime_run

    state = _ShutdownServerState()
    stop_event = threading.Event()

    atlas_runtime_run._start_shutdown_watcher(state, stop_event)
    stop_event.set()

    deadline = time.time() + 2.0
    while time.time() < deadline and not state.should_exit:
        time.sleep(0.01)

    assert state.should_exit is True


def test_terminate_child_process_reaps_live_subprocess():
    import src.atlas_runtime_run as atlas_runtime_run

    proc = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(60)"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        atlas_runtime_run._terminate_child_process(proc, "test-child", timeout=1.0)

        assert proc.poll() is not None
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=3)
