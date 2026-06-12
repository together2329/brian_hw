"""Smoke pin for scripts/orch_profile.py (finding 29 debugging capability)."""
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_orch_profile_runs_on_minimal_fixture(tmp_path):
    db = tmp_path / "atlas.db"
    con = sqlite3.connect(db)
    con.execute(
        "CREATE TABLE llm_calls (ip_id TEXT, session_id TEXT, workflow TEXT,"
        " call_role TEXT, latency_ms REAL, cost_usd REAL, status TEXT, created_at REAL)"
    )
    import time
    con.execute(
        "INSERT INTO llm_calls VALUES ('ipx','a/d/ipx/pipeline/p1/02-fl-model-gen',"
        " 'pipeline','worker', 1234.5, 0.01, 'ok', ?)", (time.time(),)
    )
    con.execute(
        "CREATE TABLE orchestrator_runs (id TEXT, ip_id TEXT, model TEXT,"
        " status TEXT, started_at REAL, ended_at REAL)"
    )
    con.execute("CREATE TABLE ip_blocks (id TEXT, ip_name TEXT)")
    con.commit()

    jobs = tmp_path / ".session" / "workers-ipc" / "job1"
    jobs.mkdir(parents=True)
    (jobs / "request.json").write_text(json.dumps({"ip": "ipx", "context": "workflow: fl-model-gen"}))
    (jobs / "response.json").write_text(json.dumps({"status": "error", "duration_ms": 5000,
                                                    "error": "stage evidence failed: gate status=f"}))

    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "orch_profile.py"), "ipx",
         "--root", str(tmp_path), "--db", str(db)],
        capture_output=True, text=True, timeout=30,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "fl-model-gen" in r.stdout
    assert "stage-gate" in r.stdout  # error classified
