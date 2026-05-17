from __future__ import annotations

import importlib.util
import json
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    PROJECT_ROOT
    / "workflow"
    / "req-gen"
    / "scripts"
    / "audit_prompt_to_artifact_checklist.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location(
        f"audit_prompt_to_artifact_checklist_{time.time_ns()}",
        SCRIPT,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_real_arm_m0_min_prompt_to_artifact_audit_is_completion_ready() -> None:
    mod = _load_module()
    result = mod.audit("arm_m0_min", PROJECT_ROOT)

    assert result["status"] == "pass"
    assert result["completion_ready"] is True
    assert result["blocked_items"] == []
    assert result["final_audit"] == {
        "status": "pass",
        "passed": "16/16",
        "blockers": [],
    }
    assert result["errors"] == []


def test_prompt_to_artifact_audit_reports_missing_evidence(tmp_path: Path) -> None:
    mod = _load_module()
    ip = "toy_cpu"
    review_dir = tmp_path / ip / "review"
    sim_dir = tmp_path / ip / "sim"
    review_dir.mkdir(parents=True)
    sim_dir.mkdir(parents=True)
    (sim_dir / "fl_rtl_goal_audit.json").write_text(
        json.dumps(
            {
                "status": "fail",
                "summary": {
                    "passed_checks": 0,
                    "total_checks": 1,
                    "blockers": ["missing"],
                },
            }
        ),
        encoding="utf-8",
    )
    (review_dir / "prompt_to_artifact_checklist.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "type": "prompt_to_artifact_completion_checklist",
                "ip": ip,
                "status": "blocked",
                "blocked_on": ["missing"],
                "completion_rule": "Do not mark complete.",
                "checklist": [
                    {
                        "id": "cpu_ip_exists",
                        "requirement": "CPU IP exists",
                        "status": "pass",
                        "evidence": [f"{ip}/yaml/{ip}.ssot.yaml"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = mod.audit(ip, tmp_path)

    assert result["status"] == "fail"
    assert result["completion_ready"] is False
    assert result["errors"] == [
        f"cpu_ip_exists: missing evidence: {ip}/yaml/{ip}.ssot.yaml"
    ]


def test_prompt_to_artifact_audit_rejects_stale_blocked_missing_paths(
    tmp_path: Path,
) -> None:
    mod = _load_module()
    ip = "toy_cpu"
    review_dir = tmp_path / ip / "review"
    req_dir = tmp_path / ip / "req"
    sim_dir = tmp_path / ip / "sim"
    review_dir.mkdir(parents=True)
    req_dir.mkdir(parents=True)
    sim_dir.mkdir(parents=True)
    (req_dir / f"{ip}_requirements.md").write_text("# approved\n", encoding="utf-8")
    (sim_dir / "fl_rtl_goal_audit.json").write_text(
        json.dumps(
            {
                "status": "pass",
                "summary": {
                    "passed_checks": 1,
                    "total_checks": 1,
                    "blockers": [],
                },
            }
        ),
        encoding="utf-8",
    )
    (review_dir / "prompt_to_artifact_checklist.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "type": "prompt_to_artifact_completion_checklist",
                "ip": ip,
                "status": "blocked",
                "blocked_on": ["req"],
                "completion_rule": "Do not mark complete.",
                "checklist": [
                    {
                        "id": "human_req_approval",
                        "requirement": "approval exists",
                        "status": "blocked",
                        "evidence": [],
                        "missing": [f"{ip}/req/{ip}_requirements.md"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    result = mod.audit(ip, tmp_path)

    assert result["status"] == "fail"
    assert result["errors"] == [
        f"human_req_approval: expected missing path exists: {ip}/req/{ip}_requirements.md"
    ]


def test_prompt_to_artifact_audit_write_persists_json(tmp_path: Path) -> None:
    mod = _load_module()
    ip = "toy_cpu"
    review_dir = tmp_path / ip / "review"
    sim_dir = tmp_path / ip / "sim"
    evidence_dir = tmp_path / ip / "yaml"
    review_dir.mkdir(parents=True)
    sim_dir.mkdir(parents=True)
    evidence_dir.mkdir(parents=True)
    (evidence_dir / f"{ip}.ssot.yaml").write_text("top_module: toy_cpu\n", encoding="utf-8")
    (sim_dir / "fl_rtl_goal_audit.json").write_text(
        json.dumps(
            {
                "status": "fail",
                "summary": {
                    "passed_checks": 0,
                    "total_checks": 1,
                    "blockers": ["req"],
                },
            }
        ),
        encoding="utf-8",
    )
    (review_dir / "prompt_to_artifact_checklist.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "type": "prompt_to_artifact_completion_checklist",
                "ip": ip,
                "status": "blocked",
                "blocked_on": ["req"],
                "completion_rule": "Do not mark complete.",
                "checklist": [
                    {
                        "id": "ssot_exists",
                        "requirement": "SSOT exists",
                        "status": "pass",
                        "evidence": [f"{ip}/yaml/{ip}.ssot.yaml"],
                    },
                    {
                        "id": "final_audit",
                        "requirement": "Final audit passes",
                        "status": "blocked",
                        "evidence": [f"{ip}/sim/fl_rtl_goal_audit.json"],
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    assert mod.main([ip, "--root", str(tmp_path), "--write"]) == 0

    output = review_dir / "prompt_to_artifact_checklist_audit.json"
    written = json.loads(output.read_text(encoding="utf-8"))
    assert written["status"] == "blocked"
    assert written["completion_ready"] is False
    assert written["blocked_items"] == ["final_audit"]
    assert written["written_to"] == f"{ip}/review/prompt_to_artifact_checklist_audit.json"
