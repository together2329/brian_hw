from __future__ import annotations

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
