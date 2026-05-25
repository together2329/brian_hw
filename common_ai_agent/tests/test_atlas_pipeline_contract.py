from __future__ import annotations

import json
import re
import shlex
from pathlib import Path

import atlas_api_jobs as jobs


def test_default_pipeline_is_ssot_to_signoff_chain() -> None:
    stage_ids = [stage["id"] for stage in jobs._PIPELINE_STAGES]

    assert stage_ids == [
        "ssot",
        "fl-model",
        "cl-model",
        "equivalence",
        "rtl",
        "lint",
        "tb",
        "sim",
        "coverage",
        "sim-debug",
        "syn",
        "sta",
        "pnr",
        "sta-post",
        "goal-audit",
    ]
    assert len(stage_ids) == len(set(stage_ids))


def test_frontend_full_flow_matches_backend_default_pipeline() -> None:
    stage_ids = [stage["id"] for stage in jobs._PIPELINE_STAGES]
    pipeline_js = (
        Path(__file__).resolve().parents[1] / "frontend" / "atlas" / "pipeline.jsx"
    ).read_text(encoding="utf-8")

    match = re.search(
        r"id:\s*'full'.*?stages:\s*\[([^\]]+)\]",
        pipeline_js,
        flags=re.S,
    )

    assert match, "frontend full flow definition not found"
    frontend_stage_ids = re.findall(r"'([^']+)'", match.group(1))
    assert frontend_stage_ids == stage_ids


def test_fl_model_workflow_prompt_is_stage_specific() -> None:
    ip = "demo_ip"

    fl_prompt = jobs._default_workflow_prompt("fl-model-gen", ip, "fl-model")
    cl_prompt = jobs._default_workflow_prompt("fl-model-gen", ip, "cl-model")
    eq_prompt = jobs._default_workflow_prompt("fl-model-gen", ip, "equivalence")

    assert "Do not run /ssot-fl-model or emit_fl_model.py" in fl_prompt
    assert "check_fl_model_artifacts.py" in fl_prompt
    assert "FunctionalModel.apply(txn)" in fl_prompt
    assert "/ssot-cycle-model demo_ip" in cl_prompt
    assert "/ssot-dual-fcov demo_ip" in cl_prompt
    assert "/ssot-equiv-goals demo_ip" in eq_prompt
    assert len({fl_prompt, cl_prompt, eq_prompt}) == 3


def test_rtl_workflow_prompt_requires_final_stage_driver_after_repairs() -> None:
    prompt = jobs._default_workflow_prompt("rtl-gen", "demo_ip", "rtl")

    assert "run /ssot-rtl demo_ip" in prompt
    assert "rerun /ssot-rtl demo_ip as the final validation step" in prompt
    assert "standalone compile/lint evidence alone" in prompt


def test_ssot_gen_rtl_blocker_prompt_uses_resolver_driver() -> None:
    prompt = jobs._workflow_prompt_with_stage_driver(
        workflow="ssot-gen",
        ip="demo_ip",
        stage_id="ssot",
        prompt="Repair rtl_blocked.json RTL_MODULE_CONTRACTS using defaults.",
    )

    assert "/resolve-rtl-blockers demo_ip --use-recommended-defaults" in prompt
    assert "/repair-ssot demo_ip" in prompt
    assert "do not rewrite the IP from scratch" in prompt


def test_pipeline_workflow_lookup_keeps_first_fl_model_stage() -> None:
    assert jobs._PIPELINE_BY_WORKFLOW["fl-model-gen"]["id"] == "fl-model"
    assert jobs._PIPELINE_BY_WORKFLOW["sim_debug"]["id"] == "sim-debug"


def test_pipeline_stage_aliases_match_orchestrator_vocabulary() -> None:
    assert jobs._resolve_pipeline_stage("equiv-goals")["id"] == "equivalence"
    assert jobs._resolve_pipeline_stage("ssot-equiv-goals")["id"] == "equivalence"
    assert jobs._resolve_pipeline_stage("cl-model-gen")["id"] == "cl-model"
    assert jobs._resolve_pipeline_stage("rtl-gen")["id"] == "rtl"
    assert jobs._resolve_pipeline_stage("psta")["id"] == "sta-post"


def test_rtl_blocker_artifact_fails_job_with_question_ids(tmp_path) -> None:
    ip = "demo_dma"
    rtl_dir = tmp_path / ip / "rtl"
    rtl_dir.mkdir(parents=True)
    (rtl_dir / "rtl_blocked.json").write_text(
        json.dumps(
            {
                "reason": "SSOT-derived dynamic RTL TODO gate is blocked",
                "questions": [
                    {"id": "RTL_DYNAMIC_TODO_OWNERSHIP"},
                    {"id": "RTL_MODULE_CONTRACTS"},
                ],
            }
        ),
        encoding="utf-8",
    )

    failed, reason = jobs._job_artifact_failure(
        {"ip": ip, "stage_id": "rtl", "workflow": "rtl-gen"},
        tmp_path,
    )

    assert failed
    assert "rtl/rtl_blocked.json" in reason
    assert "RTL_DYNAMIC_TODO_OWNERSHIP" in reason
    assert "RTL_MODULE_CONTRACTS" in reason


def test_pipeline_dag_fans_out_after_rtl() -> None:
    selected = [
        "ssot",
        "fl-model",
        "cl-model",
        "equivalence",
        "rtl",
        "lint",
        "tb",
        "sim",
        "coverage",
        "sim-debug",
        "syn",
        "sta",
        "pnr",
        "sta-post",
        "goal-audit",
    ]

    assert jobs._pipeline_stage_dependencies("fl-model", selected) == ["ssot"]
    assert jobs._pipeline_stage_dependencies("cl-model", selected) == ["ssot"]
    assert jobs._pipeline_stage_dependencies("equivalence", selected) == ["fl-model", "cl-model"]
    assert jobs._pipeline_stage_dependencies("rtl", selected) == ["equivalence"]
    assert jobs._pipeline_stage_dependencies("lint", selected) == ["rtl"]
    assert jobs._pipeline_stage_dependencies("tb", selected) == ["rtl"]
    assert jobs._pipeline_stage_dependencies("syn", selected) == ["rtl"]
    assert jobs._pipeline_stage_dependencies("sim", selected) == ["tb"]
    assert jobs._pipeline_stage_dependencies("coverage", selected) == ["sim"]
    assert jobs._pipeline_stage_dependencies("sim-debug", selected) == ["sim"]
    assert jobs._pipeline_stage_dependencies("sta", selected) == ["syn"]
    assert jobs._pipeline_stage_dependencies("pnr", selected) == ["syn"]
    assert jobs._pipeline_stage_dependencies("sta-post", selected) == ["pnr"]
    assert jobs._pipeline_stage_dependencies("goal-audit", selected) == selected[:-1]


def test_pipeline_serial_schedule_keeps_single_previous_dependency() -> None:
    selected = ["rtl", "lint", "tb", "syn"]

    assert jobs._pipeline_stage_dependencies("rtl", selected, schedule="serial") == []
    assert jobs._pipeline_stage_dependencies("lint", selected, schedule="serial") == ["rtl"]
    assert jobs._pipeline_stage_dependencies("tb", selected, schedule="serial") == ["lint"]
    assert jobs._pipeline_stage_dependencies("syn", selected, schedule="serial") == ["tb"]


def test_pipeline_auto_schedule_uses_serial_with_one_worker(monkeypatch) -> None:
    for key in ("WORKER_URL_RTL_GEN", "WORKER_URL_LINT", "WORKER_URL_TB_GEN", "WORKER_URL_SYN"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("ATLAS_EXEC_MODE", "orchestrator")
    monkeypatch.delenv("ATLAS_ORCHESTRATOR_MODE", raising=False)
    monkeypatch.delenv("ATLAS_SINGLE_MAIN_LOOP", raising=False)
    monkeypatch.setenv("WORKER_URL_DEFAULT", "http://localhost:8001")
    stages = [jobs._PIPELINE_BY_ID[stage] for stage in ("rtl", "lint", "tb", "syn")]

    assert jobs._resolve_pipeline_schedule("auto", stages) == "serial"


def test_pipeline_auto_schedule_uses_dag_with_multiple_workers(monkeypatch) -> None:
    monkeypatch.setenv("ATLAS_EXEC_MODE", "orchestrator")
    monkeypatch.delenv("ATLAS_ORCHESTRATOR_MODE", raising=False)
    monkeypatch.delenv("ATLAS_SINGLE_MAIN_LOOP", raising=False)
    monkeypatch.setenv("WORKER_URL_DEFAULT", "http://localhost:8001")
    monkeypatch.setenv("WORKER_URL_LINT", "http://localhost:8002")
    monkeypatch.setenv("WORKER_URL_TB_GEN", "http://localhost:8003")
    monkeypatch.setenv("WORKER_URL_SYN", "http://localhost:8004")
    stages = [jobs._PIPELINE_BY_ID[stage] for stage in ("rtl", "lint", "tb", "syn")]

    assert jobs._resolve_pipeline_schedule("auto", stages) == "dag"


def test_pipeline_explicit_schedule_overrides_worker_count(monkeypatch) -> None:
    monkeypatch.setenv("ATLAS_EXEC_MODE", "single-worker")
    monkeypatch.delenv("ATLAS_ORCHESTRATOR_MODE", raising=False)
    monkeypatch.setenv("WORKER_URL_DEFAULT", "http://localhost:8001")
    stages = [jobs._PIPELINE_BY_ID[stage] for stage in ("rtl", "lint", "tb", "syn")]

    assert jobs._resolve_pipeline_schedule("dag", stages) == "dag"
    assert jobs._resolve_pipeline_schedule("serial", stages) == "serial"


def test_pipeline_auto_schedule_is_serial_in_single_worker_mode(monkeypatch) -> None:
    monkeypatch.setenv("ATLAS_EXEC_MODE", "single-worker")
    monkeypatch.delenv("ATLAS_ORCHESTRATOR_MODE", raising=False)
    monkeypatch.setenv("WORKER_URL_DEFAULT", "http://localhost:8001")
    monkeypatch.setenv("WORKER_URL_LINT", "http://localhost:8002")
    stages = [jobs._PIPELINE_BY_ID[stage] for stage in ("rtl", "lint")]

    assert jobs._resolve_pipeline_schedule("auto", stages) == "serial"


def test_pipeline_stage_order_is_canonical_even_when_requested_out_of_order() -> None:
    stages = [jobs._PIPELINE_BY_ID[stage] for stage in ("tb", "rtl", "sim", "lint")]

    assert [stage["id"] for stage in jobs._ordered_pipeline_stages(stages)] == [
        "rtl",
        "lint",
        "tb",
        "sim",
    ]


def test_pipeline_dag_waits_for_selected_upstream_when_middle_stage_is_omitted() -> None:
    assert jobs._pipeline_stage_dependencies("rtl", ["ssot", "rtl"]) == ["ssot"]
    assert jobs._pipeline_stage_dependencies("rtl", ["fl-model", "cl-model", "rtl"]) == [
        "fl-model",
        "cl-model",
    ]
    assert jobs._pipeline_stage_dependencies("lint", ["ssot", "lint"]) == ["ssot"]


def test_advance_pipeline_starts_all_ready_dag_children(monkeypatch) -> None:
    pipeline_id = "pipe123"
    rtl_job = {
        "job_id": "rtl-job",
        "pipeline_id": pipeline_id,
        "stage_id": "rtl",
        "workflow": "rtl-gen",
        "status": "completed",
        "pipeline_index": 0,
        "depends_on": [],
    }
    lint_job = {
        "job_id": "lint-job",
        "pipeline_id": pipeline_id,
        "stage_id": "lint",
        "workflow": "lint",
        "status": "queued",
        "pipeline_index": 1,
        "depends_on": ["rtl-job"],
    }
    tb_job = {
        "job_id": "tb-job",
        "pipeline_id": pipeline_id,
        "stage_id": "tb",
        "workflow": "tb-gen",
        "status": "queued",
        "pipeline_index": 2,
        "depends_on": ["rtl-job"],
    }
    syn_job = {
        "job_id": "syn-job",
        "pipeline_id": pipeline_id,
        "stage_id": "syn",
        "workflow": "syn",
        "status": "queued",
        "pipeline_index": 3,
        "depends_on": ["rtl-job"],
    }
    sim_job = {
        "job_id": "sim-job",
        "pipeline_id": pipeline_id,
        "stage_id": "sim",
        "workflow": "sim",
        "status": "queued",
        "pipeline_index": 4,
        "depends_on": ["tb-job"],
    }

    dispatched: list[str] = []
    monkeypatch.setattr(jobs, "_dispatch_job_to_worker", lambda job: dispatched.append(job["stage_id"]))
    with jobs._jobs_lock:
        jobs._jobs.clear()
        for job in (rtl_job, lint_job, tb_job, syn_job, sim_job):
            jobs._jobs[job["job_id"]] = job
    try:
        jobs._advance_pipeline_from(rtl_job)

        assert set(dispatched) == {"lint", "tb", "syn"}
        assert lint_job["status"] == "pending"
        assert tb_job["status"] == "pending"
        assert syn_job["status"] == "pending"
        assert sim_job["status"] == "queued"
    finally:
        with jobs._jobs_lock:
            jobs._jobs.clear()


def test_sim_error_still_dispatches_sim_debug_for_classification(monkeypatch) -> None:
    pipeline_id = "pipe-sim-debug"
    sim_job = {
        "job_id": "sim-job",
        "pipeline_id": pipeline_id,
        "stage_id": "sim",
        "workflow": "sim",
        "status": "error",
        "pipeline_index": 0,
        "depends_on": [],
    }
    coverage_job = {
        "job_id": "coverage-job",
        "pipeline_id": pipeline_id,
        "stage_id": "coverage",
        "workflow": "coverage",
        "status": "queued",
        "pipeline_index": 1,
        "depends_on": ["sim-job"],
    }
    sim_debug_job = {
        "job_id": "sim-debug-job",
        "pipeline_id": pipeline_id,
        "stage_id": "sim-debug",
        "workflow": "sim_debug",
        "status": "queued",
        "pipeline_index": 2,
        "depends_on": ["sim-job"],
    }
    goal_audit_job = {
        "job_id": "goal-audit-job",
        "pipeline_id": pipeline_id,
        "stage_id": "goal-audit",
        "workflow": "sim_debug",
        "status": "queued",
        "pipeline_index": 3,
        "depends_on": ["sim-job", "coverage-job", "sim-debug-job"],
    }

    dispatched: list[str] = []

    def fake_dispatch(job):
        dispatched.append(job["stage_id"])
        job["status"] = "running"

    monkeypatch.setattr(jobs, "_dispatch_job_to_worker", fake_dispatch)
    with jobs._jobs_lock:
        jobs._jobs.clear()
        for job in (sim_job, coverage_job, sim_debug_job, goal_audit_job):
            jobs._jobs[job["job_id"]] = job
    try:
        jobs._advance_pipeline_from(sim_job)

        assert dispatched == ["sim-debug"]
        assert sim_debug_job["status"] == "running"
        assert coverage_job["status"] == "blocked"
        assert goal_audit_job["status"] == "blocked"
    finally:
        with jobs._jobs_lock:
            jobs._jobs.clear()


def test_stage_engine_failure_overrides_completed_artifact_recovery(tmp_path: Path) -> None:
    ip = "stage_fail_ip"
    log_dir = tmp_path / ip / "logs" / "stage_engine"
    log_dir.mkdir(parents=True)
    (log_dir / "sim-debug.json").write_text(
        json.dumps({"status": "fail", "summary": {"goals_failed": 18}}),
        encoding="utf-8",
    )
    sim_dir = tmp_path / ip / "sim"
    sim_dir.mkdir(parents=True)
    (sim_dir / "mismatch_classification.json").write_text(
        json.dumps({"status": "action_required"}),
        encoding="utf-8",
    )

    failed, reason = jobs._job_artifact_failure(
        {"ip": ip, "stage_id": "sim-debug", "workflow": "sim_debug"},
        tmp_path,
    )

    assert failed is True
    assert "logs/stage_engine/sim-debug.json status=fail" in reason


def test_unreachable_worker_recovery_is_gated_before_downstream_advance(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import urllib.error
    import urllib.request

    ip = "recovered_fail_ip"
    pipeline_id = "pipe-recover-gate"
    rtl_job = {
        "job_id": "rtl-job",
        "pipeline_id": pipeline_id,
        "stage_id": "rtl",
        "workflow": "rtl-gen",
        "status": "running",
        "run_id": "run-lost",
        "worker": "http://127.0.0.1:9",
        "pipeline_index": 0,
        "depends_on": [],
        "_last_polled": 0,
    }
    tb_job = {
        "job_id": "tb-job",
        "pipeline_id": pipeline_id,
        "stage_id": "tb",
        "workflow": "tb-gen",
        "status": "queued",
        "pipeline_index": 1,
        "depends_on": ["rtl-job"],
    }
    dispatched: list[str] = []

    def fake_urlopen(*_args, **_kwargs):
        raise urllib.error.URLError("Connection refused")

    def fake_failure(job: dict, _project_root: Path) -> tuple[bool, str]:
        if job.get("stage_id") == "rtl":
            return True, f"{ip}/logs/stage_engine/ssot-rtl.json gate status=fail"
        return False, ""

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(jobs, "_job_artifact_recovery", lambda _job, _pr: (True, "recovered from artifact"))
    monkeypatch.setattr(jobs, "_job_artifact_failure", fake_failure)
    monkeypatch.setattr(jobs, "_dispatch_job_to_worker", lambda job: dispatched.append(job["stage_id"]))

    with jobs._jobs_lock:
        jobs._jobs.clear()
        jobs._jobs[rtl_job["job_id"]] = rtl_job
        jobs._jobs[tb_job["job_id"]] = tb_job
    try:
        jobs._refresh_tracked_jobs(tmp_path)

        assert rtl_job["status"] == "error"
        assert "stage evidence failed" in rtl_job["error"]
        assert tb_job["status"] == "blocked"
        assert dispatched == []
    finally:
        with jobs._jobs_lock:
            jobs._jobs.clear()


def test_dead_lazy_worker_uses_recovered_evidence_before_advancing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    ip = "dead_worker_recovered_ip"
    pipeline_id = "pipe-dead-worker"
    worker_url = "http://127.0.0.1:7777"
    rtl_job = {
        "job_id": "rtl-job",
        "pipeline_id": pipeline_id,
        "stage_id": "rtl",
        "workflow": "rtl-gen",
        "status": "running",
        "worker": worker_url,
        "pipeline_index": 0,
        "depends_on": [],
        "project_root": str(tmp_path),
    }
    tb_job = {
        "job_id": "tb-job",
        "pipeline_id": pipeline_id,
        "stage_id": "tb",
        "workflow": "tb-gen",
        "status": "queued",
        "pipeline_index": 1,
        "depends_on": ["rtl-job"],
        "project_root": str(tmp_path),
    }
    dispatched: list[str] = []

    monkeypatch.setattr(jobs, "_job_artifact_recovery", lambda _job, _pr: (True, "recovered from artifact"))
    monkeypatch.setattr(jobs, "_job_artifact_failure", lambda _job, _pr: (False, ""))
    monkeypatch.setattr(jobs, "_dispatch_job_to_worker", lambda job: dispatched.append(job["stage_id"]))

    with jobs._jobs_lock:
        jobs._jobs.clear()
        jobs._jobs[rtl_job["job_id"]] = rtl_job
        jobs._jobs[tb_job["job_id"]] = tb_job
    try:
        transitioned = jobs._mark_jobs_failed_for_worker(worker_url, "rc=-15")

        assert transitioned == 1
        assert rtl_job["status"] == "completed"
        assert tb_job["status"] == "pending"
        assert dispatched == ["tb"]
    finally:
        with jobs._jobs_lock:
            jobs._jobs.clear()


def test_dead_lazy_worker_recovered_artifact_still_honors_gate_failure(
    tmp_path: Path,
    monkeypatch,
) -> None:
    ip = "dead_worker_failed_ip"
    pipeline_id = "pipe-dead-worker-fail"
    worker_url = "http://127.0.0.1:8888"
    rtl_job = {
        "job_id": "rtl-job",
        "pipeline_id": pipeline_id,
        "stage_id": "rtl",
        "workflow": "rtl-gen",
        "status": "running",
        "worker": worker_url,
        "pipeline_index": 0,
        "depends_on": [],
        "project_root": str(tmp_path),
    }
    tb_job = {
        "job_id": "tb-job",
        "pipeline_id": pipeline_id,
        "stage_id": "tb",
        "workflow": "tb-gen",
        "status": "queued",
        "pipeline_index": 1,
        "depends_on": ["rtl-job"],
        "project_root": str(tmp_path),
    }
    dispatched: list[str] = []

    def fake_failure(job: dict, _project_root: Path) -> tuple[bool, str]:
        if job.get("stage_id") == "rtl":
            return True, f"{ip}/logs/stage_engine/ssot-rtl.json gate status=fail"
        return False, ""

    monkeypatch.setattr(jobs, "_job_artifact_recovery", lambda _job, _pr: (True, "recovered from artifact"))
    monkeypatch.setattr(jobs, "_job_artifact_failure", fake_failure)
    monkeypatch.setattr(jobs, "_dispatch_job_to_worker", lambda job: dispatched.append(job["stage_id"]))

    with jobs._jobs_lock:
        jobs._jobs.clear()
        jobs._jobs[rtl_job["job_id"]] = rtl_job
        jobs._jobs[tb_job["job_id"]] = tb_job
    try:
        transitioned = jobs._mark_jobs_failed_for_worker(worker_url, "rc=-15")

        assert transitioned == 1
        assert rtl_job["status"] == "error"
        assert "stage evidence failed" in rtl_job["error"]
        assert tb_job["status"] == "blocked"
        assert dispatched == []
    finally:
        with jobs._jobs_lock:
            jobs._jobs.clear()


def test_coverage_blocked_artifact_is_not_reported_as_pass(tmp_path: Path) -> None:
    ip = "coverage_blocked_ip"
    cov_dir = tmp_path / ip / "cov"
    cov_dir.mkdir(parents=True)
    (cov_dir / "coverage.json").write_text(
        json.dumps({"status": "blocked"}),
        encoding="utf-8",
    )

    failed, reason = jobs._job_artifact_failure(
        {"ip": ip, "stage_id": "coverage", "workflow": "coverage"},
        tmp_path,
    )

    assert failed is True
    assert "cov/coverage.json status=blocked" in reason


def test_rtl_current_pass_evidence_supersedes_stale_blocked_artifacts(tmp_path: Path) -> None:
    ip = "rtl_stale_blocker_ip"
    ip_dir = tmp_path / ip
    for subdir in ("rtl", "lint", "list", "logs/stage_engine"):
        (ip_dir / subdir).mkdir(parents=True, exist_ok=True)
    (ip_dir / "list" / f"{ip}.f").write_text(f"rtl/{ip}.sv\n", encoding="utf-8")
    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        (
            f"module {ip}(input logic clk, output logic y);\n"
            "  logic [31:0] counter;\n"
            "  logic parity;\n"
            "  always @(posedge clk) begin\n"
            "    counter <= counter + 32'd1;\n"
            "    parity <= ^counter;\n"
            "  end\n"
            "  assign y = parity | counter[0];\n"
            "endmodule\n"
            "// extra structural text keeps the disk-truth size gate realistic\n"
            "// without relying on a generated canned artifact marker.\n"
        ),
        encoding="utf-8",
    )
    (ip_dir / "rtl" / "rtl_compile.json").write_text(
        json.dumps({"passed": True, "returncode": 0, "errors": 0}),
        encoding="utf-8",
    )
    (ip_dir / "lint" / "dut_lint.json").write_text(
        json.dumps({"passed": True, "returncode": 0, "errors": 0, "warnings": 0}),
        encoding="utf-8",
    )
    (ip_dir / "rtl" / "rtl_todo_plan.json").write_text(
        json.dumps(
            {
                "gate": {
                    "status": "pass",
                    "all_required_todos_pass": True,
                    "open_required_todos": 0,
                    "static_missing": 0,
                    "blocking_questions": 0,
                },
                "todo_completion": {"all_required_todos_pass": True},
            }
        ),
        encoding="utf-8",
    )
    (ip_dir / "logs" / "stage_engine" / "ssot-rtl.json").write_text(
        json.dumps(
            {
                "status": "blocked",
                "headline": "[RTL BLOCKED] stale preflight",
                "metadata": {
                    "rtl_todo_plan": {
                        "gate": {
                            "status": "fail",
                            "open_required_todos": 12,
                            "all_required_todos_pass": False,
                        }
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    (ip_dir / "rtl" / "rtl_blocked.json").write_text(
        json.dumps(
            {
                "status": "blocked",
                "reason": "stale preflight blocker",
                "questions": [{"id": "LLM_RTL_IMPLEMENTATION_REQUIRED"}],
            }
        ),
        encoding="utf-8",
    )

    failed, reason = jobs._job_artifact_failure(
        {"ip": ip, "stage_id": "rtl", "workflow": "rtl-gen"},
        tmp_path,
    )

    assert failed is False
    assert reason == ""


def test_rtl_completion_registers_version_and_fans_out_context(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    ip = "demo_ip"
    (tmp_path / ip / "rtl").mkdir(parents=True)
    (tmp_path / ip / "list").mkdir(parents=True)
    (tmp_path / ip / "rtl" / f"{ip}.sv").write_text(
        "module demo_ip(input logic clk, output logic done); assign done = clk; endmodule\n",
        encoding="utf-8",
    )
    (tmp_path / ip / "list" / f"{ip}.f").write_text(f"../rtl/{ip}.sv\n", encoding="utf-8")

    pipeline_id = "pipe-rtl-version"
    rtl_job = {
        "job_id": "rtl-job",
        "run_id": "worker-run-rtl",
        "pipeline_id": pipeline_id,
        "stage_id": "rtl",
        "workflow": "rtl-gen",
        "status": "completed",
        "pipeline_index": 0,
        "depends_on": [],
        "project_root": str(tmp_path),
        "ip": ip,
    }
    lint_job = {
        "job_id": "lint-job",
        "pipeline_id": pipeline_id,
        "stage_id": "lint",
        "workflow": "lint",
        "status": "queued",
        "pipeline_index": 1,
        "depends_on": ["rtl-job"],
        "project_root": str(tmp_path),
        "ip": ip,
    }
    tb_job = {
        "job_id": "tb-job",
        "pipeline_id": pipeline_id,
        "stage_id": "tb",
        "workflow": "tb-gen",
        "status": "queued",
        "pipeline_index": 2,
        "depends_on": ["rtl-job"],
        "project_root": str(tmp_path),
        "ip": ip,
    }

    dispatched: list[dict] = []
    monkeypatch.setattr(jobs, "_dispatch_job_to_worker", lambda job: dispatched.append(dict(job)))
    with jobs._jobs_lock:
        jobs._jobs.clear()
        for job in (rtl_job, lint_job, tb_job):
            jobs._jobs[job["job_id"]] = job
    try:
        jobs._advance_pipeline_from(rtl_job)
    finally:
        with jobs._jobs_lock:
            jobs._jobs.clear()

    assert rtl_job["rtl_version"] == "rtl-v001"
    assert rtl_job["rtl_sha256_tree"]
    assert rtl_job["artifact_versions"]["rtl"]["version"] == "rtl-v001"
    assert {job["stage_id"] for job in dispatched} == {"lint", "tb"}
    assert all(job["rtl_version_id"] == rtl_job["rtl_version_id"] for job in dispatched)
    assert all(job["artifact_versions"]["rtl"]["version"] == "rtl-v001" for job in dispatched)

    from core.atlas_db import AtlasDB

    with AtlasDB(str(tmp_path / "atlas.db")) as db:
        versions = db.list_rtl_versions()
    assert len(versions) == 1
    assert versions[0]["version"] == "rtl-v001"
    assert versions[0]["artifact_manifest"][0]["path"].startswith(f"{ip}/")


def test_pipeline_propagates_ssot_rtl_tb_versions_to_sim(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    ip = "demo_ip"
    (tmp_path / ip / "yaml").mkdir(parents=True)
    (tmp_path / ip / "rtl").mkdir(parents=True)
    (tmp_path / ip / "list").mkdir(parents=True)
    (tmp_path / ip / "tb").mkdir(parents=True)
    (tmp_path / ip / "yaml" / f"{ip}.ssot.yaml").write_text("ip: demo_ip\n", encoding="utf-8")
    (tmp_path / ip / "rtl" / f"{ip}.sv").write_text("module demo_ip; endmodule\n", encoding="utf-8")
    (tmp_path / ip / "list" / f"{ip}.f").write_text(f"../rtl/{ip}.sv\n", encoding="utf-8")
    (tmp_path / ip / "tb" / "run_tests.py").write_text("def test_smoke(): pass\n", encoding="utf-8")

    pipeline_id = "pipe-artifacts"
    ssot_job = {
        "job_id": "ssot-job",
        "run_id": "worker-ssot",
        "pipeline_id": pipeline_id,
        "stage_id": "ssot",
        "workflow": "ssot-gen",
        "status": "completed",
        "pipeline_index": 0,
        "depends_on": [],
        "project_root": str(tmp_path),
        "ip": ip,
    }
    rtl_job = {
        "job_id": "rtl-job",
        "run_id": "worker-rtl",
        "pipeline_id": pipeline_id,
        "stage_id": "rtl",
        "workflow": "rtl-gen",
        "status": "queued",
        "pipeline_index": 1,
        "depends_on": ["ssot-job"],
        "project_root": str(tmp_path),
        "ip": ip,
    }
    tb_job = {
        "job_id": "tb-job",
        "run_id": "worker-tb",
        "pipeline_id": pipeline_id,
        "stage_id": "tb",
        "workflow": "tb-gen",
        "status": "queued",
        "pipeline_index": 2,
        "depends_on": ["rtl-job"],
        "project_root": str(tmp_path),
        "ip": ip,
    }
    sim_job = {
        "job_id": "sim-job",
        "pipeline_id": pipeline_id,
        "stage_id": "sim",
        "workflow": "sim",
        "status": "queued",
        "pipeline_index": 3,
        "depends_on": ["tb-job"],
        "project_root": str(tmp_path),
        "ip": ip,
    }

    dispatched: list[dict] = []

    def fake_dispatch(job):
        dispatched.append(dict(job))
        job["status"] = "running"

    monkeypatch.setattr(jobs, "_dispatch_job_to_worker", fake_dispatch)
    with jobs._jobs_lock:
        jobs._jobs.clear()
        for job in (ssot_job, rtl_job, tb_job, sim_job):
            jobs._jobs[job["job_id"]] = job
    try:
        jobs._advance_pipeline_from(ssot_job)
        assert rtl_job["artifact_versions"]["ssot"]["version"] == "ssot-v001"
        rtl_job["status"] = "completed"
        jobs._advance_pipeline_from(rtl_job)
        assert tb_job["artifact_versions"]["ssot"]["version"] == "ssot-v001"
        assert tb_job["artifact_versions"]["rtl"]["version"] == "rtl-v001"
        tb_job["status"] = "completed"
        jobs._advance_pipeline_from(tb_job)
    finally:
        with jobs._jobs_lock:
            jobs._jobs.clear()

    assert sim_job["artifact_versions"]["ssot"]["version"] == "ssot-v001"
    assert sim_job["artifact_versions"]["rtl"]["version"] == "rtl-v001"
    assert sim_job["artifact_versions"]["tb"]["version"] == "tb-v001"

    from core.atlas_db import AtlasDB

    with AtlasDB(str(tmp_path / "atlas.db")) as db:
        artifact_versions = db.list_artifact_versions()
        edges = db.list_artifact_version_edges()
    assert {row["artifact_type"] for row in artifact_versions} == {"ssot", "rtl", "tb"}
    assert {edge["relation"] for edge in edges} == {"generated_from", "verified_against"}


def test_worker_dispatch_posts_rtl_version_context(monkeypatch) -> None:
    import json
    import urllib.request

    posted: dict = {}

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps({"run_id": "worker-run-1"}).encode("utf-8")

    def fake_urlopen(req, timeout=10):
        posted.update(json.loads(req.data.decode("utf-8")))
        return _Resp()

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    job = {
        "job_id": "lint-job",
        "worker": "http://localhost:8001",
        "workflow": "lint",
        "stage_id": "lint",
        "template": "lint-fix",
        "ip": "demo_ip",
        "model": "gpt-5.3-codex",
        "session": "demo_ip/pipeline/p1/02-lint",
        "project_root": "/tmp/project",
        "source_root": "/tmp/source",
        "prompt": "[ATLAS ARCHITECT WORKFLOW CONTEXT]\n- ip: demo_ip\n\nrun /lint-ip demo_ip",
        "rtl_version_id": "rv_123",
        "rtl_version": "rtl-v001",
        "rtl_sha256_tree": "tree123",
        "rtl_git_tag": "atlas/demo_ip/rtl-v001",
        "artifact_versions": {
            "ssot": {"id": "av_ssot", "artifact_type": "ssot", "version": "ssot-v001"},
            "rtl": {"id": "av_rtl", "artifact_type": "rtl", "version": "rtl-v001"},
        },
    }
    with jobs._jobs_lock:
        jobs._jobs.clear()
        jobs._jobs[job["job_id"]] = job
    try:
        jobs._dispatch_job_to_worker(job)
    finally:
        with jobs._jobs_lock:
            jobs._jobs.clear()

    assert posted["rtl_version_id"] == "rv_123"
    assert posted["artifact_versions"][0]["version"] == "ssot-v001"
    assert "rtl_version_id: rv_123" in posted["context"]
    assert "rtl_git_tag: atlas/demo_ip/rtl-v001" in posted["context"]
    assert "ssot: ssot-v001" in posted["context"]


def test_worker_launch_command_anchors_to_served_project_root(tmp_path: Path) -> None:
    command = jobs._worker_launch_command(
        "http://localhost:8001",
        "fl-model-gen",
        "demo_ip/pipeline/abc/01-fl-model-gen",
        tmp_path,
        "deepseek",
    )

    assert command.startswith(f"cd {shlex.quote(str(tmp_path))} && ")
    assert f"ATLAS_PROJECT_ROOT={shlex.quote(str(tmp_path))}" in command
    assert "PYTHONPATH=" in command
    assert "src/main.py" in command
    assert "--serve --port 8001" in command
    assert "--workflow fl-model-gen" in command
    assert "--worker-name fl-model-gen" in command
    assert "--model deepseek" in command


def test_artifact_recovery_recognizes_signoff_stage_outputs(tmp_path: Path) -> None:
    ip = "demo_ip"
    ip_dir = tmp_path / ip
    for rel in ("model", "cov", "verify", "syn/out", "sta/out", "pnr/out", "sta-post/out"):
        (ip_dir / rel).mkdir(parents=True, exist_ok=True)
    (ip_dir / "model" / "functional_model.py").write_text("# model\n", encoding="utf-8")
    (ip_dir / "cov" / "cl_fcov_plan.json").write_text("{}\n", encoding="utf-8")
    (ip_dir / "verify" / "equivalence_goals.json").write_text("{}\n", encoding="utf-8")
    (ip_dir / "syn" / "out" / "synth.v").write_text("module demo_ip; endmodule\n", encoding="utf-8")
    (ip_dir / "sta" / "out" / "wns.json").write_text("{}\n", encoding="utf-8")
    (ip_dir / "pnr" / "out" / "routed.spef").write_text("*SPEF\n", encoding="utf-8")
    (ip_dir / "sta-post" / "out" / "wns.json").write_text("{}\n", encoding="utf-8")

    for stage in ("fl-model", "cl-model", "equivalence", "syn", "sta", "pnr", "sta-post"):
        recovered, detail = jobs._job_artifact_recovery(
            {"ip": ip, "stage_id": stage, "workflow": jobs._PIPELINE_BY_ID[stage]["workflow"]},
            tmp_path,
        )
        assert recovered, stage
        assert detail.startswith("recovered from artifact:")


def test_rtl_artifact_recovery_refreshes_stale_provenance_with_existing_filelist(tmp_path: Path) -> None:
    ip = "demo_ip"
    ip_dir = tmp_path / ip
    for rel in ("yaml", "rtl", "list"):
        (ip_dir / rel).mkdir(parents=True, exist_ok=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        "\n".join(
            [
                "top_module:",
                f"  name: {ip}",
                "sub_modules:",
                f"  - name: {ip}",
                f"    file: rtl/{ip}.sv",
                "    ownership: manifest",
                f"  - name: {ip}_engine",
                f"    file: rtl/{ip}_engine.sv",
                "    ownership: manifest",
                "filelist:",
                "  rtl:",
                f"    - rtl/{ip}.sv",
                f"    - rtl/{ip}_engine.sv",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}.sv").write_text(f"module {ip}; endmodule\n", encoding="utf-8")
    (ip_dir / "rtl" / f"{ip}_engine.sv").write_text(f"module {ip}_engine; endmodule\n", encoding="utf-8")
    (ip_dir / "rtl" / "rtl_todo_plan.json").write_text('{"type":"rtl_todo_plan","tasks":[]}\n', encoding="utf-8")
    (ip_dir / "rtl" / "rtl_authoring_plan.json").write_text('{"packets":[]}\n', encoding="utf-8")
    (ip_dir / "rtl" / "rtl_authoring_provenance.json").write_text(
        json.dumps(
            {
                "type": "rtl_authoring_provenance",
                "agent": "common_ai_agent",
                "workflow": "rtl-gen",
                "surface": "headless_common_engine",
                "todo_plan_sha256": "stale",
                "rtl_files": [f"rtl/{ip}.sv"],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "list" / f"{ip}.f").write_text(f"rtl/{ip}.sv\n", encoding="utf-8")
    job = {"ip": ip, "stage_id": "rtl", "workflow": "rtl-gen", "model": "glm-5.1"}

    assert jobs._refresh_rtl_authoring_provenance_for_job(job, tmp_path) is True

    provenance = json.loads((ip_dir / "rtl" / "rtl_authoring_provenance.json").read_text(encoding="utf-8"))
    assert provenance["rtl_files"] == [f"rtl/{ip}.sv", f"rtl/{ip}_engine.sv"]
    assert provenance["todo_plan_sha256"] != "stale"
    assert (ip_dir / "list" / f"{ip}.f").read_text(encoding="utf-8").splitlines() == [
        f"rtl/{ip}.sv",
        f"rtl/{ip}_engine.sv",
    ]
