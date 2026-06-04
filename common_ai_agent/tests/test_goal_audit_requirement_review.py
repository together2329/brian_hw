from __future__ import annotations

import importlib.util
import hashlib
import json
import shutil
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    PROJECT_ROOT
    / "workflow"
    / "sim_debug"
    / "scripts"
    / "audit_fl_rtl_equivalence_goal.py"
)
PROMOTE_SCRIPT = (
    PROJECT_ROOT
    / "workflow"
    / "req-gen"
    / "scripts"
    / "promote_requirement_review.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location(f"audit_goal_{time.time_ns()}", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_promote_module():
    spec = importlib.util.spec_from_file_location(
        f"promote_requirement_review_{time.time_ns()}", PROMOTE_SCRIPT
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_goal_audit_points_req_blocker_at_pending_review_packet(tmp_path: Path) -> None:
    mod = _load_module()
    ip = "cpu_ref"
    ip_dir = tmp_path / ip
    review_packet = ip_dir / "doc" / f"{ip}_requirement_review.md"
    review_decision = ip_dir / "review" / "decision_needed_req_requirement_approval.json"
    review_packet.parent.mkdir(parents=True)
    review_decision.parent.mkdir(parents=True)
    review_packet.write_text("# Review\n\npending human approval\n", encoding="utf-8")
    review_decision.write_text(
        json.dumps(
            {
                "type": "review_decision_needed",
                "status": "review_decision_needed",
                "workflow": "req",
                "topic": "requirement_approval",
            }
        ),
        encoding="utf-8",
    )

    audit = mod.audit(ip, tmp_path)
    req_check = next(check for check in audit["checks"] if check["id"] == "req")

    assert req_check["status"] == "fail"
    assert f"{ip}/doc/{ip}_requirement_review.md" in req_check["evidence"]
    assert f"{ip}/review/decision_needed_req_requirement_approval.json" in req_check["evidence"]
    assert "approve or reject" in req_check["next_action"]
    assert "promote_requirement_review.py" in req_check["next_action"]


def test_goal_audit_rejects_long_requirement_markdown_without_approval_manifest(
    tmp_path: Path,
) -> None:
    mod = _load_module()
    ip = "cpu_ref"
    req_dir = tmp_path / ip / "req"
    req_dir.mkdir(parents=True)
    (req_dir / "requirements.md").write_text(
        "# Requirements\n\n" + ("human-approved CPU requirement text\n" * 80),
        encoding="utf-8",
    )

    audit = mod.audit(ip, tmp_path)
    req_check = next(check for check in audit["checks"] if check["id"] == "req")

    assert req_check["status"] == "fail"
    assert "approval_manifest=False" in req_check["detail"]
    assert "approval manifest" in req_check["detail"]
    assert audit["stop_condition"]["req_ok"] is False


def test_goal_audit_rejects_req_phase_marker_without_requirement_markdown(
    tmp_path: Path,
) -> None:
    mod = _load_module()
    ip = "cpu_ref"
    req_dir = tmp_path / ip / "req"
    req_dir.mkdir(parents=True)
    (req_dir / "phase1_ledger.log").write_text("phase1_evidence_refreshed\n", encoding="utf-8")

    audit = mod.audit(ip, tmp_path)
    req_check = next(check for check in audit["checks"] if check["id"] == "req")

    assert req_check["status"] == "fail"
    assert "no requirement markdown under req/" in req_check["detail"]
    assert "approval_manifest=False" in req_check["detail"]
    assert audit["stop_condition"]["req_ok"] is False


def test_goal_audit_accepts_starter_requirement_manifest(tmp_path: Path) -> None:
    mod = _load_module()
    ip = "counter_ref"
    req_dir = tmp_path / ip / "req"
    req_dir.mkdir(parents=True)
    req = req_dir / f"{ip}_requirements.md"
    req.write_text(
        "# Starter Requirements\n\n"
        + (
            "Feature: an 8-bit synchronous up counter samples enable on the rising clock edge, "
            "uses a synchronous reset, rolls over from 255 to 0, drives terminal-count from the "
            "current count value, and must close RTL compile, lint, simulation, coverage, and "
            "place-and-route evidence before signoff.\n"
        )
        * 8,
        encoding="utf-8",
    )
    (req_dir / "approval_manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "ip": ip,
                "artifact": f"req/{ip}_requirements.md",
                "status": "approved",
                "approved_by": "ssot-gen-automated-pipeline",
                "approval_mode": "starter",
                "bytes": req.stat().st_size,
                "checks": {
                    "minimum_bytes": True,
                    "no_tbd_markers": True,
                    "has_feature_table": True,
                    "has_interface_table": True,
                    "has_functional_behavior": True,
                    "has_verification_requirements": True,
                    "has_quality_gates": True,
                },
            }
        ),
        encoding="utf-8",
    )

    ok, _, detail = mod._approved_req_status(ip, tmp_path, tmp_path / ip)

    assert ok is True
    assert "starter_approved_by=ssot-gen-automated-pipeline" in detail


def test_goal_audit_accepts_starter_manifest_when_requirement_grew(tmp_path: Path) -> None:
    mod = _load_module()
    ip = "counter_ref"
    req_dir = tmp_path / ip / "req"
    req_dir.mkdir(parents=True)
    req = req_dir / f"{ip}_requirements.md"
    req.write_text(
        "# Starter Requirements\n\n"
        + (
            "Feature table: counter width reset enable rollover terminal count. "
            "Interface table: clk rst_n req_valid req_data rsp_ready rsp_data. "
            "Functional behavior: reset hold increment rollover. "
            "Verification requirements: compile lint sim coverage goal audit. "
            "Quality gates: all evidence must pass before signoff.\n"
        )
        * 12,
        encoding="utf-8",
    )
    recorded_bytes = req.stat().st_size - 10
    (req_dir / "approval_manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "ip": ip,
                "artifact": f"req/{ip}_requirements.md",
                "status": "approved",
                "approved_by": "ssot-gen-automated-pipeline",
                "approval_mode": "starter",
                "bytes": recorded_bytes,
                "checks": {
                    "minimum_bytes": True,
                    "no_tbd_markers": True,
                    "has_feature_table": True,
                    "has_interface_table": True,
                    "has_functional_behavior": True,
                    "has_verification_requirements": True,
                    "has_quality_gates": True,
                },
            }
        ),
        encoding="utf-8",
    )

    ok, _, detail = mod._approved_req_status(ip, tmp_path, tmp_path / ip)

    assert ok is True
    assert f"bytes_recorded={recorded_bytes}" in detail


def test_goal_audit_placeholder_scan_ignores_metadata_tbd_key(tmp_path: Path) -> None:
    mod = _load_module()
    ssot = tmp_path / "ip" / "yaml" / "ip.ssot.yaml"
    ssot.parent.mkdir(parents=True)
    ssot.write_text(
        "custom:\n"
        "  tbd:\n"
        "  - Future optional load-enable feature is outside this starter counter scope\n",
        encoding="utf-8",
    )

    assert mod._text_has_placeholder(ssot) is False


def test_goal_audit_placeholder_scan_ignores_negated_placeholder_phrase(tmp_path: Path) -> None:
    mod = _load_module()
    ssot = tmp_path / "ip" / "yaml" / "ip.ssot.yaml"
    ssot.parent.mkdir(parents=True)
    ssot.write_text(
        "note: explicit SSOT tieoff allowance, not a placeholder)\n",
        encoding="utf-8",
    )

    assert mod._text_has_placeholder(ssot) is False


def test_goal_audit_placeholder_scan_rejects_unresolved_todo(tmp_path: Path) -> None:
    mod = _load_module()
    artifact = tmp_path / "ip" / "doc" / "review.md"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("unresolved TODO: implement real contract\n", encoding="utf-8")

    assert mod._text_has_placeholder(artifact) is True


def test_goal_audit_rejects_approved_req_when_review_decision_still_open(
    tmp_path: Path,
) -> None:
    mod = _load_module()
    ip = "cpu_ref"
    ip_dir = tmp_path / ip
    source = ip_dir / "doc" / f"{ip}_requirement_review.md"
    req = ip_dir / "req" / f"{ip}_requirements.md"
    decision = ip_dir / "review" / "decision_needed_req_requirement_approval.json"
    source.parent.mkdir(parents=True)
    req.parent.mkdir(parents=True)
    decision.parent.mkdir(parents=True)
    source.write_text("# Review\n\n" + ("approved source packet\n" * 80), encoding="utf-8")
    req.write_text("# Requirements\n\n" + ("approved requirement artifact\n" * 80), encoding="utf-8")
    (req.parent / "approval_manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "type": "requirement_approval_manifest",
                "ip": ip,
                "approved_by": "test",
                "approved_at_utc": "2026-05-17T00:00:00Z",
                "source": f"{ip}/doc/{ip}_requirement_review.md",
                "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "target": f"{ip}/req/{ip}_requirements.md",
                "target_sha256": hashlib.sha256(req.read_bytes()).hexdigest(),
            }
        ),
        encoding="utf-8",
    )
    decision.write_text(
        json.dumps(
            {
                "type": "review_decision_needed",
                "status": "review_decision_needed",
                "workflow": "req",
                "topic": "requirement_approval",
            }
        ),
        encoding="utf-8",
    )

    audit = mod.audit(ip, tmp_path)
    req_check = next(check for check in audit["checks"] if check["id"] == "req")

    assert req_check["status"] == "fail"
    assert "review decision remains unresolved" in req_check["detail"]
    assert audit["stop_condition"]["req_ok"] is False


def test_goal_audit_rejects_approved_req_when_source_hash_does_not_match(
    tmp_path: Path,
) -> None:
    mod = _load_module()
    ip = "cpu_ref"
    ip_dir = tmp_path / ip
    source = ip_dir / "doc" / f"{ip}_requirement_review.md"
    req = ip_dir / "req" / f"{ip}_requirements.md"
    source.parent.mkdir(parents=True)
    req.parent.mkdir(parents=True)
    source.write_text("# Review\n\n" + ("approved source packet\n" * 80), encoding="utf-8")
    req.write_text("# Requirements\n\n" + ("approved requirement artifact\n" * 80), encoding="utf-8")
    (req.parent / "approval_manifest.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "type": "requirement_approval_manifest",
                "ip": ip,
                "approved_by": "test",
                "approved_at_utc": "2026-05-17T00:00:00Z",
                "source": f"{ip}/doc/{ip}_requirement_review.md",
                "source_sha256": "wrong",
                "target": f"{ip}/req/{ip}_requirements.md",
                "target_sha256": hashlib.sha256(req.read_bytes()).hexdigest(),
            }
        ),
        encoding="utf-8",
    )

    audit = mod.audit(ip, tmp_path)
    req_check = next(check for check in audit["checks"] if check["id"] == "req")

    assert req_check["status"] == "fail"
    assert "source_sha256 does not match" in req_check["detail"]
    assert audit["stop_condition"]["req_ok"] is False


def test_arm_m0_min_temp_approval_promotion_completes_final_audit(tmp_path: Path) -> None:
    """Real approval must be sufficient to complete the actual CPU artifact,
    but this regression validates that path only on a temp copy."""
    audit_mod = _load_module()
    promote_mod = _load_promote_module()
    ip = "arm_m0_min"
    source_ip = PROJECT_ROOT / ip
    tmp_ip = tmp_path / ip
    shutil.copytree(
        source_ip,
        tmp_ip,
        ignore=shutil.ignore_patterns("cocotb_build", "__pycache__", "req"),
    )

    assert not (tmp_ip / "req" / f"{ip}_requirements.md").exists()
    review_decision = tmp_ip / "review" / "decision_needed_req_requirement_approval.json"
    source = tmp_ip / "doc" / f"{ip}_requirement_review.md"
    review_decision.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "type": "review_decision_needed",
                "status": "review_decision_needed",
                "ip": ip,
                "workflow": "req",
                "topic": "requirement_approval",
                "evidence": {
                    "approval_target": {
                        "path": f"{ip}/doc/{ip}_requirement_review.md",
                        "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                    },
                    "machine_evidence_snapshot": {
                        "completion_audit_sha256": hashlib.sha256(
                            (tmp_ip / "doc" / f"{ip}_completion_audit.md").read_bytes()
                        ).hexdigest(),
                        "ssot_sha256": hashlib.sha256(
                            (tmp_ip / "yaml" / f"{ip}.ssot.yaml").read_bytes()
                        ).hexdigest(),
                        "fl_rtl_compare_sha256": hashlib.sha256(
                            (tmp_ip / "sim" / "fl_rtl_compare.json").read_bytes()
                        ).hexdigest(),
                        "coverage_sha256": hashlib.sha256(
                            (tmp_ip / "cov" / "coverage.json").read_bytes()
                        ).hexdigest(),
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    manifest = promote_mod.promote(
        ip,
        tmp_path,
        source=Path(f"{ip}/doc/{ip}_requirement_review.md"),
        approved_by="brian",
        decision_note="temp approval validation",
    )
    assert manifest["resolved_review_decision"] == (
        f"{ip}/review/decision_needed_req_requirement_approval.json"
    )

    audit = audit_mod.audit(ip, tmp_path)
    assert audit["status"] == "pass"
    assert audit["summary"] == {
        "total_checks": 16,
        "passed_checks": 16,
        "failed_checks": 0,
        "blockers": [],
    }
