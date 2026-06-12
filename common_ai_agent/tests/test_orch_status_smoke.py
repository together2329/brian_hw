"""Smoke pin for scripts/orch_status.py (live where/why/what-next dashboard)."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_orch_status_runs_on_minimal_fixture(tmp_path):
    ip = "ipy"
    (tmp_path / ip / "rtl").mkdir(parents=True)
    (tmp_path / ip / "rtl" / "rtl_blocked.json").write_text(json.dumps({
        "questions": [{"id": "Q1", "decision_needed": "decide X", "options": ["do Y"]}],
    }))
    jobs = tmp_path / ".session" / "workers-ipc" / "j1"
    jobs.mkdir(parents=True)
    (jobs / "request.json").write_text(json.dumps({"ip": ip, "context": "workflow: rtl-gen"}))
    (jobs / "response.json").write_text(json.dumps({
        "status": "error", "duration_ms": 100,
        "error": "silent-fail: workflow=rtl-gen ran 9 tool calls but wrote 0 files",
    }))

    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "orch_status.py"), ip, "--root", str(tmp_path)],
        capture_output=True, text=True, timeout=60,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "silent-fail" in r.stdout          # failure classified
    assert "re-dispatch" in r.stdout          # next-action hint surfaced
    assert "decide X" in r.stdout             # blocker artifact surfaced
    assert "do Y" in r.stdout                 # remediation surfaced
