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
