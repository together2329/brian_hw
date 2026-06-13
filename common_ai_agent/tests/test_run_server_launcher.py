from pathlib import Path


REPO = Path(__file__).resolve().parent.parent


def test_run_server_kills_only_listener_pids_line_by_line():
    text = (REPO / "run_server.csh").read_text(encoding="utf-8")

    assert "-sTCP:LISTEN -t" in text
    assert "lsof -ti tcp:$port" not in text
    assert "while IFS= read -r pid" in text
    assert 'kill -9 "$pid"' in text
    assert "_atlas_wait_port_free" in text


def test_run_server_build_failures_do_not_fall_through_to_server_start():
    text = (REPO / "run_server.csh").read_text(encoding="utf-8")

    assert "cd frontend/atlas || _atlas_abort 1" in text
    assert "npm run build || _atlas_abort 1" in text
    assert "cd ../../ || _atlas_abort 1" in text


def test_run_server_kills_stray_admin_subprocess_not_just_listeners():
    """The admin server is a subprocess that can be orphaned/mid-restart and
    miss the LISTEN sweep, leaving :3002 taken. The launcher must also kill
    stray server processes by their invocation (line-by-line, not a broad
    pkill of the file path that would catch an editor)."""
    text = (REPO / "run_server.csh").read_text(encoding="utf-8")

    assert "_atlas_kill_stray_servers" in text
    assert "pgrep -f" in text
    assert "atlas_admin.py --port" in text          # targets the admin subprocess
    assert "atlas_ui.py --port" in text             # …and the main server
    assert "pgrep -f \"atlas_admin.py\"" not in text  # not the bare path (editor-safe)


def test_run_server_frees_ports_before_and_after_build():
    """A process can re-grab a port during the ~2s build, so the port-free
    sweep must run both before the build and again right before launch."""
    text = (REPO / "run_server.csh").read_text(encoding="utf-8")

    pre_build, sep, post_build = text.partition("npm run build")
    assert sep, "expected an 'npm run build' step"
    assert "_atlas_free_ports || _atlas_abort 1" in pre_build
    assert "_atlas_free_ports || _atlas_abort 1" in post_build
