"""Smoke pins for scripts/orch_trace.py (orchestrator decision replay)."""
from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

from src.orchestrator.trace import build_trace_from_records, format_trace, terminal_blocker_from_steps


ROOT = Path(__file__).resolve().parents[1]


def _insert_step(con, run_id: str, step: int, tool: str, args: dict, result: dict, verdict: str = "ok") -> None:
    con.execute(
        "INSERT INTO orchestrator_steps VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (
            f"s{step}",
            run_id,
            step,
            tool,
            "",
            json.dumps({"args": args}),
            "",
            "",
            json.dumps({"result": result, "summary": json.dumps(result)}),
            verdict,
            None,
            "",
            time.time() + step,
        ),
    )


def test_orch_trace_replays_dispatch_classify_and_final(tmp_path):
    db = tmp_path / "atlas.db"
    con = sqlite3.connect(db)
    con.execute(
        "CREATE TABLE orchestrator_runs (id TEXT PRIMARY KEY, session_id TEXT, workspace_id TEXT,"
        " ip_id TEXT, user_id TEXT, chat_message_id TEXT, pipeline_run_id TEXT, model TEXT,"
        " reasoning_effort TEXT, status TEXT, final_state TEXT, started_at REAL,"
        " ended_at REAL, updated_at REAL)"
    )
    con.execute(
        "CREATE TABLE orchestrator_steps (id TEXT PRIMARY KEY, run_id TEXT NOT NULL,"
        " step_index INT, tool_name TEXT, observed_state_json TEXT, decision_json TEXT,"
        " dispatched_workflow TEXT, dispatched_job_id TEXT, evidence_read_json TEXT,"
        " verdict TEXT, retry_budget_state_json TEXT, user_reply TEXT, created_at REAL)"
    )
    run_id = "run123"
    now = time.time()
    con.execute(
        "INSERT INTO orchestrator_runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (run_id, "admin/default/ipx/orchestrator", "ws", "ip", "user", "", "", "gpt-test", "", "blocked", "blocked", now, now + 1, now + 1),
    )
    _insert_step(
        con,
        run_id,
        0,
        "dispatch_workflow",
        {"ip": "ipx", "workflow": "sim", "reason": "refresh stale sim"},
        {"ok": True, "jobs": [{"job_id": "job-sim"}], "reset_downstream_budgets": ["sim-debug", "coverage"]},
    )
    _insert_step(
        con,
        run_id,
        1,
        "yield_run",
        {"reason": "wait for sim"},
        {},
        "job_complete:job-sim:error:[sim] FAIL",
    )
    _insert_step(
        con,
        run_id,
        2,
        "classify_failure",
        {"stage": "coverage", "excluded_owners": ["tb-gen"]},
        {
            "owner": "frontier",
            "next_workflow": "human-review-escalation",
            "confidence": "low",
            "reason": "route tb-gen refuted",
        },
    )
    _insert_step(
        con,
        run_id,
        3,
        "dispatch_workflow",
        {"ip": "ipx", "workflow": "__final__", "payload": {"state": "blocked"}, "reason": "stop cleanly"},
        {"ok": True, "final_state": "blocked"},
    )
    con.commit()

    ctrl = tmp_path / ".session" / "orchestrators-ipc" / run_id
    ctrl.mkdir(parents=True)
    (ctrl / "wake.jsonl").write_text(json.dumps({"event": "job_complete", "job_id": "job-sim"}) + "\n")
    (ctrl / "response.json").write_text(json.dumps({"status": "blocked", "final_state": "blocked", "steps_taken": 4}))

    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "orch_trace.py"), run_id, "--db", str(db), "--root", str(tmp_path)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "dispatch sim jobs=job-sim" in r.stdout
    assert "reset budgets: sim-debug,coverage" in r.stdout
    assert "wait -> job_complete:job-sim:error:[sim] FAIL" in r.stdout
    assert "classify coverage -> owner=frontier next=human-review-escalation confidence=low" in r.stdout
    assert "dispatch __final__ state=blocked" in r.stdout
    assert "job_complete" in r.stdout


def test_orch_trace_json_output(tmp_path):
    db = tmp_path / "atlas.db"
    con = sqlite3.connect(db)
    con.execute(
        "CREATE TABLE orchestrator_runs (id TEXT PRIMARY KEY, model TEXT, status TEXT,"
        " final_state TEXT, started_at REAL, ended_at REAL)"
    )
    con.execute(
        "CREATE TABLE orchestrator_steps (id TEXT PRIMARY KEY, run_id TEXT NOT NULL,"
        " step_index INT, tool_name TEXT, observed_state_json TEXT, decision_json TEXT,"
        " dispatched_workflow TEXT, dispatched_job_id TEXT, evidence_read_json TEXT,"
        " verdict TEXT, retry_budget_state_json TEXT, user_reply TEXT, created_at REAL)"
    )
    con.execute("INSERT INTO orchestrator_runs VALUES (?,?,?,?,?,?)", ("run-json", "m", "completed", "completed", time.time(), time.time()))
    _insert_step(con, "run-json", 0, "read_pipeline_state", {"ip": "ipx"}, {"failed": {}, "running": [], "passed": ["ssot"]})
    con.commit()

    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "orch_trace.py"), "run-json", "--db", str(db), "--json"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    doc = json.loads(r.stdout)
    assert doc["run_id"] == "run-json"
    assert doc["steps"][0]["detail"] == "read pipeline failed=0 running=0 passed=1"


def test_orch_trace_marks_completed_after_tool_failed_as_blocked(tmp_path):
    db = tmp_path / "atlas.db"
    con = sqlite3.connect(db)
    con.execute(
        "CREATE TABLE orchestrator_runs (id TEXT PRIMARY KEY, model TEXT, status TEXT,"
        " final_state TEXT, started_at REAL, ended_at REAL)"
    )
    con.execute(
        "CREATE TABLE orchestrator_steps (id TEXT PRIMARY KEY, run_id TEXT NOT NULL,"
        " step_index INT, tool_name TEXT, observed_state_json TEXT, decision_json TEXT,"
        " dispatched_workflow TEXT, dispatched_job_id TEXT, evidence_read_json TEXT,"
        " verdict TEXT, retry_budget_state_json TEXT, user_reply TEXT, created_at REAL)"
    )
    now = time.time()
    con.execute("INSERT INTO orchestrator_runs VALUES (?,?,?,?,?,?)", ("bad-run", "m", "completed", "completed", now, now + 1))
    _insert_step(
        con,
        "bad-run",
        0,
        "dispatch_workflow",
        {"ip": "ipx", "workflow": "tb-gen", "reason": "repair coverage"},
        {"ok": False, "error": "dispatch_workflow bridge timed out"},
        "tool_failed",
    )
    con.commit()

    r = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "orch_trace.py"), "bad-run", "--db", str(db)],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "status=tool_failed" in r.stdout
    assert "terminal anomaly: run recorded completed after tool_failed at step 0" in r.stdout
    assert "dispatch tb-gen [NO JOB] [FAILED]" in r.stdout
    assert "error: dispatch_workflow bridge timed out" in r.stdout


def test_terminal_blocker_detects_nonfinal_dispatch_without_job():
    rows = [
        {
            "step_index": 0,
            "tool_name": "dispatch_workflow",
            "decision_json": json.dumps({"args": {"workflow": "tb-gen"}}),
            "evidence_read_json": json.dumps({"result": {"ok": True, "jobs": []}}),
            "verdict": "ok",
            "created_at": time.time(),
        }
    ]
    blocker = terminal_blocker_from_steps(rows)
    assert blocker is not None
    assert blocker["kind"] == "dispatch_no_job"
    assert blocker["workflow"] == "tb-gen"


def test_trace_surfaces_stale_active_worker_heartbeat(tmp_path):
    run_id = "run-stale-worker"
    job_id = "job-stale"
    worker_dir = tmp_path / ".session" / "workers-ipc" / job_id
    worker_dir.mkdir(parents=True)
    (worker_dir / "request.json").write_text(
        json.dumps({"workflow": "rtl-gen", "ip": "ipx"}) + "\n",
        encoding="utf-8",
    )
    (worker_dir / "heartbeat.json").write_text(
        json.dumps(
            {
                "workflow": "rtl-gen",
                "status": "running",
                "last_action": "Iter 22 / 60",
                "elapsed_s": 191.4,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (worker_dir / "worker.log").write_text("still thinking\n", encoding="utf-8")
    old = time.time() - 240
    os.utime(worker_dir / "heartbeat.json", (old, old))
    os.utime(worker_dir / "worker.log", (old, old))
    rows = [
        {
            "step_index": 0,
            "tool_name": "dispatch_workflow",
            "decision_json": json.dumps(
                {"args": {"workflow": "rtl-gen", "reason": "repair missing RTL contract"}}
            ),
            "evidence_read_json": json.dumps({"result": {"ok": True, "jobs": [{"job_id": job_id}]}}),
            "verdict": "ok",
            "created_at": time.time(),
        },
        {
            "step_index": 1,
            "tool_name": "yield_run",
            "decision_json": json.dumps({"args": {"reason": "wait for rtl-gen"}}),
            "evidence_read_json": json.dumps({"result": {}}),
            "verdict": "timer",
            "created_at": time.time(),
        },
    ]
    trace = build_trace_from_records(
        run_id,
        run={"id": run_id, "status": "yielded", "started_at": time.time(), "model": "gpt-test"},
        raw_steps=rows,
        project_root=tmp_path,
    )

    assert trace["workers"][0]["job_id"] == job_id
    assert trace["workers"][0]["workflow"] == "rtl-gen"
    assert trace["workers"][0]["response_present"] is False
    assert trace["workers"][0]["stale"] is True
    rendered = format_trace(trace)
    assert "workers:" in rendered
    assert "job-stale rtl-gen status=running STALE" in rendered
    assert "last=Iter 22 / 60" in rendered


def test_atlas_trace_strip_consumes_shared_decision_trace_api():
    src = (ROOT / "frontend" / "atlas" / "pipeline-trace-workers.tsx").read_text()
    assert "/api/orchestrator/runs/latest/trace" in src
    assert "setDecisionTrace(j)" in src
    assert "data-status={status}" in src
    assert "decisionTrace?.workers" in src
    assert "stale worker" in src
    assert "orchestratorTraceUrl(ip, 20)" in src  # legacy JSONL fallback remains
