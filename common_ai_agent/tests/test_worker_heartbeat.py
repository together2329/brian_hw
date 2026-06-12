"""Worker-loop heartbeat (finding 29 observability follow-on)."""
import json
import time
from pathlib import Path


class _StubEntry:
    def __init__(self):
        self.run_id = "r1"
        self.status = "running"
        self.logged = []

    def add_log(self, entry_type, content, role=""):
        self.logged.append((entry_type, content, role))


def test_heartbeat_mirrors_loop_progress(tmp_path, monkeypatch):
    from src.atlas_worker_ipc import _attach_heartbeat

    hb = tmp_path / "heartbeat.json"
    entry = _StubEntry()
    _attach_heartbeat(entry, hb, workflow="rtl-gen", ip="ipx")

    entry.add_log("action", "slash:/ssot-rtl ipx")
    entry.add_log("observation", "preflight passed")
    # force past the 2s throttle for the second write window
    time.sleep(2.1)
    entry.add_log("action", "edit rtl/ipx.sv")

    assert hb.is_file()
    doc = json.loads(hb.read_text())
    assert doc["type"] == "worker_heartbeat"
    assert doc["workflow"] == "rtl-gen" and doc["ip"] == "ipx"
    assert doc["actions"] == 2 and doc["events"] == 3
    assert "edit rtl/ipx.sv" in doc["last_action"]
    # original add_log still records everything
    assert len(entry.logged) == 3


def test_heartbeat_write_failure_never_breaks_logging(tmp_path):
    from src.atlas_worker_ipc import _attach_heartbeat

    entry = _StubEntry()
    # point at an unwritable path (a directory)
    bad = tmp_path / "as_dir"
    bad.mkdir()
    _attach_heartbeat(entry, bad, workflow="x", ip="y")
    time.sleep(0)  # first write attempt happens after throttle window check
    for i in range(3):
        entry.add_log("action", f"a{i}")
    assert len(entry.logged) == 3  # logging unaffected by OSError
