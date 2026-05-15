from __future__ import annotations

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


def test_fl_model_workflow_prompt_is_stage_specific() -> None:
    ip = "demo_ip"

    fl_prompt = jobs._default_workflow_prompt("fl-model-gen", ip, "fl-model")
    cl_prompt = jobs._default_workflow_prompt("fl-model-gen", ip, "cl-model")
    eq_prompt = jobs._default_workflow_prompt("fl-model-gen", ip, "equivalence")

    assert "/ssot-fl-model demo_ip" in fl_prompt
    assert "/ssot-cycle-model demo_ip" in cl_prompt
    assert "/ssot-dual-fcov demo_ip" in cl_prompt
    assert "/ssot-equiv-goals demo_ip" in eq_prompt
    assert len({fl_prompt, cl_prompt, eq_prompt}) == 3


def test_pipeline_workflow_lookup_keeps_first_fl_model_stage() -> None:
    assert jobs._PIPELINE_BY_WORKFLOW["fl-model-gen"]["id"] == "fl-model"
    assert jobs._PIPELINE_BY_WORKFLOW["sim_debug"]["id"] == "sim-debug"


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
    monkeypatch.setenv("WORKER_URL_DEFAULT", "http://localhost:8001")
    stages = [jobs._PIPELINE_BY_ID[stage] for stage in ("rtl", "lint", "tb", "syn")]

    assert jobs._resolve_pipeline_schedule("auto", stages) == "serial"


def test_pipeline_auto_schedule_uses_dag_with_multiple_workers(monkeypatch) -> None:
    monkeypatch.setenv("WORKER_URL_DEFAULT", "http://localhost:8001")
    monkeypatch.setenv("WORKER_URL_LINT", "http://localhost:8002")
    monkeypatch.setenv("WORKER_URL_TB_GEN", "http://localhost:8003")
    monkeypatch.setenv("WORKER_URL_SYN", "http://localhost:8004")
    stages = [jobs._PIPELINE_BY_ID[stage] for stage in ("rtl", "lint", "tb", "syn")]

    assert jobs._resolve_pipeline_schedule("auto", stages) == "dag"


def test_pipeline_explicit_schedule_overrides_worker_count(monkeypatch) -> None:
    monkeypatch.setenv("WORKER_URL_DEFAULT", "http://localhost:8001")
    stages = [jobs._PIPELINE_BY_ID[stage] for stage in ("rtl", "lint", "tb", "syn")]

    assert jobs._resolve_pipeline_schedule("dag", stages) == "dag"
    assert jobs._resolve_pipeline_schedule("serial", stages) == "serial"


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
