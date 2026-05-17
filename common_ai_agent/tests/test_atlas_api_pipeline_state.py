from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

_EXPECTED_STAGE_IDS = [
    "ssot", "fl-model", "cl-model", "equivalence", "rtl",
    "lint", "tb", "sim", "coverage", "sim-debug",
    "syn", "sta", "pnr", "sta-post", "goal-audit",
]


def _make_client(tmp_path: Path, monkeypatch) -> TestClient:
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    client = TestClient(atlas_ui.create_app())
    reg = client.post("/api/auth/register", json={"username": "u", "password": "pw"})
    assert reg.status_code == 200, reg.text
    return client


def test_pipeline_state_returns_15_stages(tmp_path: Path, monkeypatch) -> None:
    ip = "smoke_ip"
    (tmp_path / ip).mkdir()

    client = _make_client(tmp_path, monkeypatch)
    resp = client.get(f"/api/pipeline/state?ip={ip}")
    assert resp.status_code == 200, resp.text

    data = resp.json()
    assert data["ip"] == ip
    assert "stages" in data
    stage_keys = list(data["stages"].keys())
    assert stage_keys == _EXPECTED_STAGE_IDS, stage_keys
    assert len(stage_keys) == 15

    _valid_states = {"idle", "ready", "running", "passed", "failed", "blocked", "stale", "locked"}
    for sid, sdata in data["stages"].items():
        assert sdata["state"] in _valid_states, f"{sid}: invalid state {sdata['state']}"
        assert "scoresheet" in sdata
        assert "glyph" in sdata
    # ssot has no deps and no artifacts → idle
    assert data["stages"]["ssot"]["state"] == "idle"


def test_pipeline_state_summarizes_nested_junit_testsuites(tmp_path: Path, monkeypatch) -> None:
    ip = "nested_junit_ip"
    sim_dir = tmp_path / ip / "sim"
    sim_dir.mkdir(parents=True)
    (sim_dir / "results.xml").write_text(
        """<testsuites>
  <testsuite name="alpha" tests="2" failures="0" errors="0">
    <testcase name="test_a"/>
    <testcase name="test_b"/>
  </testsuite>
  <testsuite name="beta" tests="2" failures="0" errors="0">
    <testcase name="test_c"/>
    <testcase name="test_d"/>
  </testsuite>
</testsuites>
""",
        encoding="utf-8",
    )

    client = _make_client(tmp_path, monkeypatch)
    resp = client.get(f"/api/pipeline/state?ip={ip}")
    assert resp.status_code == 200, resp.text

    sim = resp.json()["stages"]["sim"]
    assert sim["state"] == "passed"
    assert sim["top"] == "4 tests · 0 failures"


def test_pipeline_state_includes_real_worker_and_headless_progress_debug(tmp_path: Path, monkeypatch) -> None:
    ip = "progress_debug_ip"
    logs = tmp_path / ip / "logs"
    logs.mkdir(parents=True)
    (logs / "heartbeat.json").write_text(
        json.dumps(
            {
                "ts": "1970-01-01T00:00:01Z",
                "state": "running",
                "phase": "llm_call",
                "stage": "ssot-gen",
                "model": "deepseek",
                "pid": 123,
            }
        ),
        encoding="utf-8",
    )
    with (logs / "run_progress.jsonl").open("w", encoding="utf-8") as f:
        f.write(json.dumps({"ts": "1970-01-01T00:00:00Z", "event": "stage_start", "stage": "ssot-gen"}) + "\n")
        f.write(json.dumps({"ts": "1970-01-01T00:00:01Z", "event": "llm_call_start", "stage": "ssot-gen", "model": "deepseek"}) + "\n")

    client = _make_client(tmp_path, monkeypatch)

    import atlas_api_jobs

    jobs, lock = atlas_api_jobs.get_jobs_state()
    with lock:
        jobs.clear()
        jobs["job-progress"] = {
            "job_id": "job-progress",
            "run_id": "run-progress",
            "pipeline_id": "pipe-progress",
            "pipeline_index": 4,
            "worker": "http://localhost:9999",
            "workflow": "rtl-gen",
            "stage_id": "rtl",
            "ip": ip,
            "model": "gpt-5.3-codex",
            "session": f"{ip}/pipeline/pipe-progress/05-rtl-gen",
            "scope_path": ip,
            "started_at": time.time() - 7,
            "status": "running",
            "iterations": 2,
            "result_summary": "authoring RTL packet",
            "error": "",
        }

    resp = client.get(f"/api/pipeline/state?ip={ip}")
    assert resp.status_code == 200, resp.text

    progress_debug = resp.json()["progress_debug"]
    assert progress_debug["diagnosis"]["state"] == "running_worker_jobs"
    assert progress_debug["worker"]["active"][0]["workflow"] == "rtl-gen"
    assert progress_debug["worker"]["active"][0]["worker"] == "http://localhost:9999"
    assert progress_debug["worker"]["active"][0]["run_id"] == "run-progress"
    assert progress_debug["headless"]["diagnosis"]["state"] == "stuck_llm_call"
    assert progress_debug["headless"]["current"]["stage"] == "ssot-gen"

    debug_resp = client.get(f"/api/pipeline/progress-debug?ip={ip}")
    assert debug_resp.status_code == 200, debug_resp.text
    direct_debug = debug_resp.json()
    assert direct_debug["diagnosis"]["state"] == "running_worker_jobs"
    assert direct_debug["worker"]["active"][0]["job_id"] == "job-progress"
    assert direct_debug["headless"]["llm"]["active"] is True


def test_pipeline_state_passed_when_ssot_present(tmp_path: Path, monkeypatch) -> None:
    ip = "smoke_ssot_ip"
    yaml_dir = tmp_path / ip / "yaml"
    yaml_dir.mkdir(parents=True)

    # write a minimal ssot with 34 sections
    sections = "\n".join(
        f"  - name: section_{i}\n    description: desc_{i}" for i in range(34)
    )
    ssot_text = f"ip: {ip}\nsections:\n{sections}\n"
    (yaml_dir / f"{ip}.ssot.yaml").write_text(ssot_text, encoding="utf-8")

    client = _make_client(tmp_path, monkeypatch)
    resp = client.get(f"/api/pipeline/state?ip={ip}")
    assert resp.status_code == 200, resp.text

    data = resp.json()
    ssot_stage = data["stages"]["ssot"]
    assert ssot_stage["state"] == "passed", f"expected passed, got {ssot_stage['state']}"
    # scoresheet entries are now labeled dicts: {state, label, evidence_path}
    first_dot = ssot_stage["scoresheet"][0]
    assert isinstance(first_dot, dict)
    assert first_dot["state"] == "pass"
    assert first_dot["label"]  # non-empty
    assert "ssot" in first_dot["evidence_path"]
    assert ssot_stage["top"] != ""
    assert ssot_stage["source"] == "fs"  # came from filesystem (no DB row)


def test_pipeline_state_db_row_overrides_filesystem(tmp_path: Path, monkeypatch) -> None:
    """A workflow_runs row in the DB should make stage='passed' even with NO
    on-disk evidence, and 'failed' when status='error'. This is the DB-first
    state derivation that lets the UI reflect runs even after artifact moves."""
    import os
    from core.atlas_db import AtlasDB

    ip = "db_state_ip"
    (tmp_path / ip).mkdir()  # IP dir exists, but no rtl/ artifacts

    # Pre-create the DB and insert a completed rtl-gen run for this IP.
    db_path = tmp_path / "atlas.db"
    os.environ["ATLAS_DB_PATH"] = str(db_path)
    with AtlasDB(str(db_path)) as db:
        ws = db.upsert_workspace(tmp_path.name or "default", local_path=str(tmp_path))
        ipb = db.upsert_ip_block(ws["id"], ip)
        run = db.start_workflow_run(
            session_id="default",
            workspace_id=ws["id"],
            ip_id=ipb["id"],
            workflow="rtl-gen",
            mode="pipeline",
            model_profile="gpt-5.3-codex",
            reasoning_effort="high",
            trigger="test",
        )
        db.finish_workflow_run(run["id"], status="completed")

    client = _make_client(tmp_path, monkeypatch)
    resp = client.get(f"/api/pipeline/state?ip={ip}")
    assert resp.status_code == 200, resp.text

    data = resp.json()
    rtl_stage = data["stages"]["rtl"]
    # No rtl/*.sv on disk, but DB has a completed rtl-gen run → state must
    # come from the DB and be 'passed'.
    assert rtl_stage["state"] == "passed", f"expected passed (DB-first), got {rtl_stage['state']}"
    assert rtl_stage["source"] == "db"


def test_pipeline_state_db_failed_propagates_error_summary(tmp_path: Path, monkeypatch) -> None:
    """A workflow_runs row with status=error should map to state=failed
    and surface error_summary in the response."""
    import os
    from core.atlas_db import AtlasDB

    ip = "db_failed_ip"
    (tmp_path / ip).mkdir()

    db_path = tmp_path / "atlas.db"
    os.environ["ATLAS_DB_PATH"] = str(db_path)
    with AtlasDB(str(db_path)) as db:
        ws = db.upsert_workspace(tmp_path.name or "default", local_path=str(tmp_path))
        ipb = db.upsert_ip_block(ws["id"], ip)
        run = db.start_workflow_run(
            session_id="default",
            workspace_id=ws["id"],
            ip_id=ipb["id"],
            workflow="lint",
            mode="pipeline",
            model_profile="gpt-5.3-codex",
            reasoning_effort="medium",
            trigger="test",
        )
        db.finish_workflow_run(run["id"], status="error", error_summary="lint produced 7 errors")

    client = _make_client(tmp_path, monkeypatch)
    resp = client.get(f"/api/pipeline/state?ip={ip}")
    assert resp.status_code == 200, resp.text

    data = resp.json()
    lint_stage = data["stages"]["lint"]
    assert lint_stage["state"] == "failed", f"expected failed, got {lint_stage['state']}"
    assert lint_stage["error_summary"] == "lint produced 7 errors"
    assert lint_stage["source"] == "db"


def test_pipeline_state_locked_reason_names_missing_upstream(tmp_path: Path, monkeypatch) -> None:
    """A locked stage should populate locked_reason like 'needs ssot'."""
    ip = "locked_ip"
    (tmp_path / ip).mkdir()

    client = _make_client(tmp_path, monkeypatch)
    resp = client.get(f"/api/pipeline/state?ip={ip}")
    assert resp.status_code == 200, resp.text

    data = resp.json()
    # fl-model depends on ssot; with no ssot artifact and no DB row, fl-model
    # should be locked with reason 'needs ssot'.
    fl = data["stages"]["fl-model"]
    assert fl["state"] == "locked", f"expected locked, got {fl['state']}"
    assert fl["locked_reason"] and "ssot" in fl["locked_reason"], fl["locked_reason"]


def test_pipeline_state_includes_orchestrator_block_enabled_by_default(
    tmp_path: Path, monkeypatch
) -> None:
    """The orchestrator/handoffs_by_workflow keys are always present in the
    response, and Pipeline defaults to orchestrator mode unless explicitly disabled."""
    monkeypatch.delenv("ATLAS_ORCHESTRATOR_MODE", raising=False)
    ip = "orch_off_ip"
    (tmp_path / ip).mkdir()
    client = _make_client(tmp_path, monkeypatch)
    data = client.get(f"/api/pipeline/state?ip={ip}").json()

    assert "orchestrator" in data
    assert "handoffs_by_workflow" in data
    orch = data["orchestrator"]
    assert orch["enabled"] is True
    assert orch["mode"] == "json"
    assert orch["pending_handoffs"] == 0
    assert orch["claimed_handoffs"] == 0
    assert orch["review_decisions"] == 0
    assert orch["decisions_needed"] == 0
    assert data["handoffs_by_workflow"] == {}


def test_pipeline_state_orchestrator_mode_json_when_enabled(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("ATLAS_ORCHESTRATOR_MODE", "1")
    ip = "orch_on_ip"
    (tmp_path / ip).mkdir()
    client = _make_client(tmp_path, monkeypatch)
    data = client.get(f"/api/pipeline/state?ip={ip}").json()

    orch = data["orchestrator"]
    assert orch["enabled"] is True
    # Gateway not built yet → durable JSON-queue path is the only mode.
    assert orch["mode"] == "json"


def test_pipeline_state_counts_handoffs_from_disk(
    tmp_path: Path, monkeypatch
) -> None:
    """A pending handoff on disk should be reflected in the API counts."""
    from src import handoff_queue as hq

    monkeypatch.setenv("ATLAS_ORCHESTRATOR_MODE", "1")
    ip = "counts_ip"
    ip_dir = tmp_path / ip
    ip_dir.mkdir()
    record = {
        "schema": hq.SCHEMA,
        "handoff_id": hq.make_handoff_id(ip, "sim-debug", "rtl-gen", "EQ_A"),
        "ip": ip,
        "from_workflow": "sim-debug",
        "to_workflow": "rtl-gen",
        "scope": hq.make_scope(user_id="u", session_id="S", pipeline_run_id="P"),
        "reason": "FL-vs-RTL mismatch",
        "goal_ids": ["EQ_A"],
    }
    hq.write_pending(ip_dir, record)

    client = _make_client(tmp_path, monkeypatch)
    # The /api/pipeline/state endpoint uses a 2s micro-cache keyed by ip; a
    # fresh client with the same ip is a cache miss so this read sees disk.
    data = client.get(f"/api/pipeline/state?ip={ip}").json()

    orch = data["orchestrator"]
    assert orch["pending_handoffs"] == 1
    assert orch["claimed_handoffs"] == 0

    rtl = data["handoffs_by_workflow"]["rtl-gen"]
    assert rtl["pending"] == 1
    assert rtl["claimed"] == 0
    assert rtl["latest"]["handoff_id"] == record["handoff_id"]
    assert rtl["latest"]["from_workflow"] == "sim-debug"
    assert rtl["latest"]["goal_ids"] == ["EQ_A"]


def test_pipeline_state_counts_review_decisions_from_disk(
    tmp_path: Path, monkeypatch
) -> None:
    from src import review_decisions as rd

    monkeypatch.setenv("ATLAS_ORCHESTRATOR_MODE", "1")
    ip = "decisions_ip"
    ip_dir = tmp_path / ip
    ip_dir.mkdir()
    rd.write_repeated_mismatch_decision(
        ip_dir, ip=ip, owner="rtl-gen", signature="EQ_X", retry_attempts=3
    )

    client = _make_client(tmp_path, monkeypatch)
    data = client.get(f"/api/pipeline/state?ip={ip}").json()
    assert data["orchestrator"]["decisions_needed"] == 1


def test_pipeline_state_counts_generic_headless_review_decisions_from_disk(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("ATLAS_ORCHESTRATOR_MODE", "1")
    ip = "generic_decision_ip"
    review_dir = tmp_path / ip / "review"
    review_dir.mkdir(parents=True)
    (review_dir / "decision_needed_req_requirement_approval.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "type": "review_decision_needed",
                "status": "review_decision_needed",
                "ip": ip,
                "workflow": "req",
                "topic": "requirement_approval",
                "severity": "signoff_blocker",
                "decision_needed": "Approve or reject requirements.",
                "evidence": {
                    "human_facing_request": f"{ip}/review/approval_request.md",
                    "review_packet": f"{ip}/doc/{ip}_requirement_review.md",
                    "review_aids": [
                        f"{ip}/review/completion_readiness_checklist.md",
                        f"{ip}/review/prompt_to_artifact_checklist.json",
                        f"{ip}/review/prompt_to_artifact_checklist_audit.json",
                        "doc/wiki/arm-m0-min-current-status.md",
                        f"{ip}/doc/{ip}_review_index.md",
                        f"{ip}/doc/{ip}_user_handoff.md",
                        f"{ip}/doc/{ip}_rtl_inventory.md",
                        f"{ip}/doc/{ip}_isa_decode_inventory.md",
                    ],
                },
                "recommended_option": "approve_locked_scope",
            }
        ),
        encoding="utf-8",
    )

    client = _make_client(tmp_path, monkeypatch)
    data = client.get(f"/api/pipeline/state?ip={ip}").json()
    assert data["orchestrator"]["decisions_needed"] == 1
    item = data["orchestrator"]["decision_items"][0]
    assert item["path"] == f"{ip}/review/decision_needed_req_requirement_approval.json"
    assert item["workflow"] == "req"
    assert item["topic"] == "requirement_approval"
    assert item["severity"] == "signoff_blocker"
    assert item["recommended_option"] == "approve_locked_scope"
    assert item["evidence"]["human_facing_request"] == f"{ip}/review/approval_request.md"
    assert item["evidence"]["review_aids"] == [
        f"{ip}/review/completion_readiness_checklist.md",
        f"{ip}/review/prompt_to_artifact_checklist.json",
        f"{ip}/review/prompt_to_artifact_checklist_audit.json",
        "doc/wiki/arm-m0-min-current-status.md",
        f"{ip}/doc/{ip}_review_index.md",
        f"{ip}/doc/{ip}_user_handoff.md",
        f"{ip}/doc/{ip}_rtl_inventory.md",
        f"{ip}/doc/{ip}_isa_decode_inventory.md",
    ]


def test_real_arm_m0_min_pipeline_state_is_complete_after_req_approval(
    tmp_path: Path, monkeypatch
) -> None:
    """The generated CPU should stop surfacing the req review decision after
    approval and show the final goal audit as passed."""
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.chdir(PROJECT_ROOT)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", PROJECT_ROOT)

    client = TestClient(atlas_ui.create_app())
    reg = client.post("/api/auth/register", json={"username": "audit", "password": "pw"})
    assert reg.status_code == 200, reg.text

    data = client.get("/api/pipeline/state?ip=arm_m0_min").json()
    assert data["orchestrator"]["decisions_needed"] == 0
    assert data["orchestrator"]["decision_items"] == []
    assert data["stages"]["goal-audit"]["state"] == "passed"
    assert data["stages"]["goal-audit"]["error_summary"] in (None, "")


def test_pipeline_state_marks_goal_audit_failed_when_audit_json_fails(
    tmp_path: Path, monkeypatch
) -> None:
    ip = "goal_audit_fail_ip"
    sim_dir = tmp_path / ip / "sim"
    sim_dir.mkdir(parents=True)
    (sim_dir / "fl_rtl_goal_audit.json").write_text(
        json.dumps(
            {
                "status": "fail",
                "summary": {
                    "passed": 15,
                    "total": 16,
                    "blockers": ["req"],
                },
            }
        ),
        encoding="utf-8",
    )

    client = _make_client(tmp_path, monkeypatch)
    data = client.get(f"/api/pipeline/state?ip={ip}").json()
    goal_audit = data["stages"]["goal-audit"]
    assert goal_audit["state"] == "failed"
    assert goal_audit["source"] == "fs"
    assert goal_audit["error_summary"] == "blockers=req"


def test_orchestrator_mode_get_reflects_env(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ATLAS_ORCHESTRATOR_MODE", "1")
    client = _make_client(tmp_path, monkeypatch)
    data = client.get("/api/pipeline/orchestrator_mode").json()
    assert data == {"enabled": True, "mode": "json"}

    monkeypatch.setenv("ATLAS_ORCHESTRATOR_MODE", "0")
    data = client.get("/api/pipeline/orchestrator_mode").json()
    assert data == {"enabled": False, "mode": None}


def test_orchestrator_mode_post_toggles_env_and_state_payload(
    tmp_path: Path, monkeypatch
) -> None:
    import os

    monkeypatch.delenv("ATLAS_ORCHESTRATOR_MODE", raising=False)
    ip = "toggle_ip"
    (tmp_path / ip).mkdir()
    client = _make_client(tmp_path, monkeypatch)

    # baseline: default on
    base = client.get(f"/api/pipeline/state?ip={ip}").json()
    assert base["orchestrator"]["enabled"] is True

    # toggle off
    r = client.post("/api/pipeline/orchestrator_mode", json={"enabled": False})
    assert r.status_code == 200
    assert r.json() == {"enabled": False, "mode": None}
    assert os.environ.get("ATLAS_ORCHESTRATOR_MODE") == "0"

    # /api/pipeline/state must reflect the new mode on the next call
    # (the endpoint clears the 2 s micro-cache so this is immediate).
    off = client.get(f"/api/pipeline/state?ip={ip}").json()
    assert off["orchestrator"]["enabled"] is False
    assert off["orchestrator"]["mode"] is None

    # toggle on
    r = client.post("/api/pipeline/orchestrator_mode", json={"enabled": True})
    assert r.status_code == 200
    assert r.json() == {"enabled": True, "mode": "json"}
    on = client.get(f"/api/pipeline/state?ip={ip}").json()
    assert on["orchestrator"]["enabled"] is True
    assert on["orchestrator"]["mode"] == "json"


def test_orchestrator_mode_post_rejects_bad_body(tmp_path: Path, monkeypatch) -> None:
    client = _make_client(tmp_path, monkeypatch)

    r = client.post("/api/pipeline/orchestrator_mode", json={})
    assert r.status_code == 400
    assert "enabled" in r.json()["error"]

    r = client.post("/api/pipeline/orchestrator_mode", json={"enabled": "yes"})
    assert r.status_code == 400
    assert "bool" in r.json()["error"]

    r = client.post(
        "/api/pipeline/orchestrator_mode",
        content=b"not-json",
        headers={"Content-Type": "application/json"},
    )
    assert r.status_code == 400


def test_pipeline_run_policy_get_post_and_state_payload(tmp_path: Path, monkeypatch) -> None:
    import os

    monkeypatch.delenv("ATLAS_RUN_MODE", raising=False)
    monkeypatch.delenv("ATLAS_ORCHESTRATOR_MODE", raising=False)
    ip = "policy_ip"
    (tmp_path / ip).mkdir()
    client = _make_client(tmp_path, monkeypatch)

    base = client.get("/api/pipeline/run_policy")
    assert base.status_code == 200
    assert base.json()["run_mode"] == "engineering"
    assert base.json()["exec_mode"] == "orchestrator"

    r = client.post("/api/pipeline/run_policy", json={
        "run_mode": "starter",
        "exec_mode": "orchestrator",
    })
    assert r.status_code == 200, r.text
    assert r.json()["run_mode"] == "starter"
    assert r.json()["exec_mode"] == "orchestrator"
    assert os.environ.get("ATLAS_RUN_MODE") == "starter"
    assert os.environ.get("ATLAS_ORCHESTRATOR_MODE") == "1"

    state = client.get(f"/api/pipeline/state?ip={ip}").json()
    assert state["run_mode"] == "starter"
    assert state["exec_mode"] == "orchestrator"
    assert state["policy"]["run_mode"] == "starter"
    assert state["policy"]["exec_mode"] == "orchestrator"

    bad = client.post("/api/pipeline/run_policy", json={"run_mode": "tiny"})
    assert bad.status_code == 400
    assert "run_mode" in bad.json()["error"]


def test_pipeline_state_summarizes_ssot_provenance_sidecar(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ATLAS_RUN_MODE", "signoff")
    ip = "prov_ip"
    yaml_dir = tmp_path / ip / "yaml"
    yaml_dir.mkdir(parents=True)
    (yaml_dir / f"{ip}.ssot.provenance.json").write_text(
        json.dumps({
            "/top_module/name": {"authority": "user"},
            "/clocking/core_clk/frequency_mhz": {
                "authority": "generated_default",
                "mode_allowed": ["starter"],
                "signoff_critical": True,
                "review": "Confirm target frequency before signoff.",
            },
            "/security/assets/0/name": {
                "authority": "generated_default",
                "review": "Generated security asset must be confirmed before signoff.",
            },
            "/reset/policy": {"authority": "review_needed"},
        }),
        encoding="utf-8",
    )
    client = _make_client(tmp_path, monkeypatch)

    state = client.get(f"/api/pipeline/state?ip={ip}").json()
    summary = state["provenance_summary"]
    assert summary["generated_defaults"] == 2
    assert summary["review_needed"] == 1
    assert summary["user"] == 1
    assert summary["signoff_blocked"] is True
    assert summary["critical_generated_defaults"] == 2
    assert summary["source"] == f"yaml/{ip}.ssot.provenance.json"


def test_pipeline_dispatch_records_run_and_exec_mode(tmp_path: Path, monkeypatch) -> None:
    import atlas_api_jobs as jobs

    ip = "dispatch_policy_ip"
    (tmp_path / ip).mkdir()
    client = _make_client(tmp_path, monkeypatch)

    with jobs._jobs_lock:
        jobs._jobs.clear()

    def fake_dispatch(job):
        job["run_id"] = "fake-run"
        job["status"] = "completed"
        job["finished_at"] = time.time()

    monkeypatch.setattr(jobs, "_dispatch_job_to_worker", fake_dispatch)
    r = client.post("/api/pipeline/dispatch", json={
        "ip": ip,
        "stages": ["ssot", "rtl"],
        "schedule": "auto",
        "run_mode": "signoff",
        "exec_mode": "single-worker",
    })
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["run_mode"] == "signoff"
    assert data["exec_mode"] == "single-worker"
    assert data["schedule"] == "serial"
    assert [job["run_mode"] for job in data["jobs"]] == ["signoff", "signoff"]
    assert [job["exec_mode"] for job in data["jobs"]] == ["single-worker", "single-worker"]

    with jobs._jobs_lock:
        stored = list(jobs._jobs.values())
    assert all(job["run_mode"] == "signoff" for job in stored)
    assert all(job["exec_mode"] == "single-worker" for job in stored)
    assert "[ATLAS RUN POLICY]" in stored[0]["prompt"]
    assert "- run_mode: signoff" in stored[0]["prompt"]


def test_pipeline_state_rejects_oversize_ip(tmp_path: Path, monkeypatch) -> None:
    """A 500-char ip used to crash with `OSError [Errno 63] File name too long`
    at downstream stat() calls. Validator now caps at 64 chars. Surfaced by
    deep^6 round T44."""
    client = _make_client(tmp_path, monkeypatch)
    long_ip = "a" * 500
    r = client.get(f"/api/pipeline/state?ip={long_ip}")
    assert r.status_code == 400
    assert "invalid or missing ip" in r.json()["error"]


def test_pipeline_state_isolates_handoffs_by_authenticated_user(
    tmp_path: Path, monkeypatch
) -> None:
    """Two different authenticated users polling the same IP must not see
    each other's handoffs. Pre-fix, _state_cache was keyed by (ip,) only and
    _orchestrator_block returned ALL handoffs regardless of user. Surfaced
    by deep^6 round T41."""
    from src import handoff_queue as hq

    monkeypatch.setenv("ATLAS_ORCHESTRATOR_MODE", "1")
    ip = "iso_ip"
    ip_dir = tmp_path / ip
    ip_dir.mkdir()

    # Seed one handoff per user
    for user in ("u_alice", "u_bob"):
        rec = {
            "schema": hq.SCHEMA,
            "handoff_id": hq.make_handoff_id(ip, "sim-debug", "rtl-gen", user.upper()),
            "ip": ip,
            "from_workflow": "sim-debug",
            "to_workflow": "rtl-gen",
            "scope": hq.make_scope(user_id=user, session_id="S", pipeline_run_id="P"),
        }
        hq.write_pending(ip_dir, rec)

    client = _make_client(tmp_path, monkeypatch)
    # The fixture's user is named "u" — register an alice user so we can
    # exercise the per-user cache key from two distinct sessions.
    client.post("/api/auth/register", json={"username": "u_alice", "password": "pw"})
    client.post("/api/auth/register", json={"username": "u_bob", "password": "pw"})

    # Log in as u_alice and poll
    client.post("/api/auth/login", json={"username": "u_alice", "password": "pw"})
    data_alice = client.get(f"/api/pipeline/state?ip={ip}").json()
    # Log in as u_bob and poll
    client.post("/api/auth/login", json={"username": "u_bob", "password": "pw"})
    data_bob = client.get(f"/api/pipeline/state?ip={ip}").json()

    pending_alice = data_alice["orchestrator"]["pending_handoffs"]
    pending_bob = data_bob["orchestrator"]["pending_handoffs"]
    # Each user sees only their own handoff (1 each), not the global total (2)
    assert pending_alice == 1, f"alice saw {pending_alice} handoffs (expected 1)"
    assert pending_bob == 1, f"bob saw {pending_bob} handoffs (expected 1)"
    # And handoffs_by_workflow agrees
    assert data_alice["handoffs_by_workflow"]["rtl-gen"]["pending"] == 1
    assert data_bob["handoffs_by_workflow"]["rtl-gen"]["pending"] == 1


def test_stage_carries_workflow_and_handoffs_count(tmp_path: Path, monkeypatch) -> None:
    """Each stage object in the response must expose its workflow name and a
    per-workflow handoff count so the StageCard can render [take] without
    threading the full pipeline state down."""
    from src import handoff_queue as hq

    ip = "stage_handoffs_ip"
    ip_dir = tmp_path / ip
    ip_dir.mkdir()
    hq.write_pending(ip_dir, {
        "schema": hq.SCHEMA,
        "handoff_id": hq.make_handoff_id(ip, "sim-debug", "rtl-gen", "Q"),
        "ip": ip,
        "from_workflow": "sim-debug",
        "to_workflow": "rtl-gen",
        "scope": hq.make_scope(user_id="u", session_id="S", pipeline_run_id="P"),
    })

    client = _make_client(tmp_path, monkeypatch)
    data = client.get(f"/api/pipeline/state?ip={ip}").json()
    rtl = data["stages"]["rtl"]
    assert rtl["workflow"] == "rtl-gen"
    assert rtl["handoffs"]["pending"] == 1
    # A stage with no handoffs still has the field, zero-filled
    ssot = data["stages"]["ssot"]
    assert ssot["workflow"] == "ssot-gen"
    assert ssot["handoffs"] == {"pending": 0, "claimed": 0, "done": 0, "review": 0, "latest": None}


def test_handoff_list_returns_pending_for_user(tmp_path: Path, monkeypatch) -> None:
    from src import handoff_queue as hq

    ip = "list_ip"
    ip_dir = tmp_path / ip
    ip_dir.mkdir()
    hq.write_pending(ip_dir, {
        "schema": hq.SCHEMA,
        "handoff_id": hq.make_handoff_id(ip, "sim-debug", "rtl-gen", "L1"),
        "ip": ip,
        "from_workflow": "sim-debug",
        "to_workflow": "rtl-gen",
        "scope": hq.make_scope(user_id="u", session_id="S", pipeline_run_id="P"),
    })

    client = _make_client(tmp_path, monkeypatch)
    r = client.get(f"/api/handoff/list?ip={ip}&workflow=rtl-gen")
    assert r.status_code == 200
    data = r.json()
    assert len(data["pending"]) == 1
    assert data["pending"][0]["to_workflow"] == "rtl-gen"
    assert data["claimed"] == []
    # filter param honored
    r2 = client.get(f"/api/handoff/list?ip={ip}&workflow=tb-gen")
    assert r2.json()["pending"] == []


def test_handoff_save_writes_pending_and_busts_cache(tmp_path: Path, monkeypatch) -> None:
    ip = "save_ip"
    (tmp_path / ip).mkdir()
    client = _make_client(tmp_path, monkeypatch)
    # Seed cache
    base = client.get(f"/api/pipeline/state?ip={ip}").json()
    assert base["orchestrator"]["pending_handoffs"] == 0

    r = client.post("/api/handoff/save", json={
        "ip": ip,
        "from_workflow": "sim-debug",
        "to_workflow": "rtl-gen",
        "reason": "user-driven test",
        "suffix": "TEST",
    })
    assert r.status_code == 200, r.text
    payload = r.json()
    assert payload["ok"] is True
    assert payload["state"] == "pending"
    assert payload["handoff_id"]

    # Cache should be busted — immediate next poll sees pending=1
    after = client.get(f"/api/pipeline/state?ip={ip}").json()
    assert after["orchestrator"]["pending_handoffs"] == 1


def test_handoff_save_preserves_session_and_pipeline_scope(tmp_path: Path, monkeypatch) -> None:
    ip = "scoped_save_ip"
    (tmp_path / ip).mkdir()
    client = _make_client(tmp_path, monkeypatch)
    session_id = f"u/{ip}/orchestrator"
    pipeline_run_id = "pipe-scope-123"

    r = client.post("/api/handoff/save", json={
        "ip": ip,
        "from_workflow": "sim-debug",
        "to_workflow": "rtl-gen",
        "reason": "needs RTL repair",
        "suffix": "SCOPED",
        "session_id": session_id,
        "pipeline_run_id": pipeline_run_id,
        "user_id": "spoofed-user",
    })
    assert r.status_code == 200, r.text
    scope = r.json()["scope"]
    assert scope == {
        "user_id": "u",
        "session_id": session_id,
        "pipeline_run_id": pipeline_run_id,
    }

    listed = client.get(
        f"/api/handoff/list?ip={ip}&workflow=rtl-gen&"
        f"session_id={session_id}&pipeline_run_id={pipeline_run_id}"
    )
    assert listed.status_code == 200, listed.text
    pending = listed.json()["pending"]
    assert len(pending) == 1
    assert pending[0]["scope"] == scope


def test_handoff_save_rejects_missing_fields(tmp_path: Path, monkeypatch) -> None:
    ip = "save_bad_ip"
    (tmp_path / ip).mkdir()
    client = _make_client(tmp_path, monkeypatch)
    r = client.post("/api/handoff/save", json={"ip": ip})
    assert r.status_code == 400
    assert "from_workflow" in r.json()["error"]


def test_handoff_take_claims_oldest_pending(tmp_path: Path, monkeypatch) -> None:
    from src import handoff_queue as hq

    ip = "take_ip"
    ip_dir = tmp_path / ip
    ip_dir.mkdir()
    for suffix, ts in (("OLD", "2026-05-16T08:00:00Z"), ("NEW", "2026-05-16T12:00:00Z")):
        rec = {
            "schema": hq.SCHEMA,
            "handoff_id": hq.make_handoff_id(ip, "sim-debug", "rtl-gen", suffix),
            "ip": ip,
            "from_workflow": "sim-debug",
            "to_workflow": "rtl-gen",
            "scope": hq.make_scope(user_id="u", session_id="S", pipeline_run_id="P"),
            "created_at": ts,
        }
        hq.write_pending(ip_dir, rec)

    client = _make_client(tmp_path, monkeypatch)
    r = client.post("/api/handoff/take", json={"ip": ip, "workflow": "rtl-gen"})
    assert r.status_code == 200, r.text
    payload = r.json()
    assert payload["ok"] is True
    assert payload["status"] == "claimed"
    assert payload["handoff"]["handoff_id"].endswith("__OLD")
    assert payload["handoff"]["claimed_by"].startswith("ui-")
    # Second take gets NEW
    r2 = client.post("/api/handoff/take", json={"ip": ip, "workflow": "rtl-gen"})
    assert r2.json()["handoff"]["handoff_id"].endswith("__NEW")
    # Third take gets none_available
    r3 = client.post("/api/handoff/take", json={"ip": ip, "workflow": "rtl-gen"})
    assert r3.json()["status"] == "none_available"
