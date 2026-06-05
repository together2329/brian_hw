import signal


class _ServerState:
    def __init__(self, *, should_exit=False):
        self.should_exit = should_exit
        self.force_exit = False
        self._captured_signals = []


def test_atlas_uvicorn_exit_signal_does_not_reraise_first_sigint():
    import src.atlas_runtime_run as atlas_runtime_run

    state = _ServerState()

    atlas_runtime_run._handle_atlas_uvicorn_exit_signal(state, signal.SIGINT)

    assert state.should_exit is True
    assert state.force_exit is False
    assert state._captured_signals == []


def test_atlas_uvicorn_exit_signal_forces_second_sigint_without_reraise():
    import src.atlas_runtime_run as atlas_runtime_run

    state = _ServerState(should_exit=True)

    atlas_runtime_run._handle_atlas_uvicorn_exit_signal(state, signal.SIGINT)

    assert state.should_exit is True
    assert state.force_exit is True
    assert state._captured_signals == []


def test_atlas_uvicorn_exit_signal_keeps_non_sigint_reraise():
    import src.atlas_runtime_run as atlas_runtime_run

    state = _ServerState()

    atlas_runtime_run._handle_atlas_uvicorn_exit_signal(state, signal.SIGTERM)

    assert state.should_exit is True
    assert state.force_exit is False
    assert state._captured_signals == [signal.SIGTERM]
