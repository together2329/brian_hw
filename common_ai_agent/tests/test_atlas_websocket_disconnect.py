import errno


def test_windows_proactor_connection_reset_is_a_disconnect():
    from src.atlas_ui import _is_disconnect_os_error

    exc = ConnectionResetError(10054, "An existing connection was forcibly closed by the remote host")
    exc.winerror = 10054

    assert _is_disconnect_os_error(exc)


def test_posix_socket_reset_and_broken_pipe_are_disconnects():
    from src.atlas_ui import _is_disconnect_os_error

    assert _is_disconnect_os_error(OSError(errno.ECONNRESET, "Connection reset by peer"))
    assert _is_disconnect_os_error(BrokenPipeError(errno.EPIPE, "Broken pipe"))


def test_unrelated_os_error_is_not_a_disconnect():
    from src.atlas_ui import _is_disconnect_os_error

    assert not _is_disconnect_os_error(OSError(errno.ENOENT, "No such file or directory"))
