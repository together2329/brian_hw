from __future__ import annotations

import json
import hashlib
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src import review_decisions as rd


def test_decision_filename_uses_doc_contract_when_no_signature() -> None:
    # Filename uses `_safe_name` style (hyphens → underscores) so it matches
    # the pre-existing on-disk contract written by `headless_workflow.py`.
    assert rd.decision_filename("rtl-gen") == "decision_needed_pipeline_repeated_rtl_gen_mismatch.json"


def test_decision_filename_includes_signature_when_given() -> None:
    name = rd.decision_filename("rtl-gen", "EQ_GPIO_READBACK")
    assert name == "decision_needed_pipeline_repeated_rtl_gen_EQ_GPIO_READBACK_mismatch.json"


def test_write_creates_record_with_expected_fields(tmp_path: Path) -> None:
    ip_dir = tmp_path / "simple_gpio_lite"
    ip_dir.mkdir()
    path = rd.write_repeated_mismatch_decision(
        ip_dir,
        ip="simple_gpio_lite",
        owner="rtl-gen",
        signature="EQ_GPIO_READBACK",
        retry_attempts=2,
        evidence={"classification": "sim/mismatch_classification.json"},
        reason="retry budget exhausted",
    )
    assert path.exists()
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["schema"] == rd.SCHEMA
    assert record["ip"] == "simple_gpio_lite"
    assert record["owner"] == "rtl-gen"
    assert record["signature"] == "EQ_GPIO_READBACK"
    assert record["retry_attempts"] == 2
    assert record["evidence"]["classification"] == "sim/mismatch_classification.json"
    assert record["options"] == list(rd.DECISION_OPTIONS)
    assert record["created_at"]
    assert record["last_seen_at"]
    assert record["resolved_at"] is None


def test_rewrite_preserves_created_at_and_refreshes_last_seen(tmp_path: Path) -> None:
    ip_dir = tmp_path / "ip"
    ip_dir.mkdir()
    p1 = rd.write_repeated_mismatch_decision(
        ip_dir, ip="ip", owner="rtl-gen", signature="A", retry_attempts=1
    )
    record1 = json.loads(p1.read_text(encoding="utf-8"))

    p2 = rd.write_repeated_mismatch_decision(
        ip_dir, ip="ip", owner="rtl-gen", signature="A", retry_attempts=2
    )
    record2 = json.loads(p2.read_text(encoding="utf-8"))

    assert record2["created_at"] == record1["created_at"]
    assert record2["retry_attempts"] == 2
    # last_seen may or may not differ depending on resolution; never older.
    assert record2["last_seen_at"] >= record1["last_seen_at"]


def test_resolve_decision_sets_resolution(tmp_path: Path) -> None:
    ip_dir = tmp_path / "ip"
    ip_dir.mkdir()
    rd.write_repeated_mismatch_decision(
        ip_dir, ip="ip", owner="rtl-gen", retry_attempts=3
    )
    rd.resolve_decision(ip_dir, owner="rtl-gen", resolution="missing_ssot_semantics")
    record = json.loads(
        rd.decision_path(ip_dir, "rtl-gen").read_text(encoding="utf-8")
    )
    assert record["resolution"] == "missing_ssot_semantics"
    assert record["resolved_at"]


def test_resolve_decision_raises_when_missing(tmp_path: Path) -> None:
    ip_dir = tmp_path / "ip"
    ip_dir.mkdir()
    with pytest.raises(FileNotFoundError):
        rd.resolve_decision(ip_dir, owner="rtl-gen", resolution="x")


def test_list_open_decisions_excludes_resolved(tmp_path: Path) -> None:
    ip_dir = tmp_path / "ip"
    ip_dir.mkdir()
    rd.write_repeated_mismatch_decision(ip_dir, ip="ip", owner="rtl-gen", signature="A")
    rd.write_repeated_mismatch_decision(ip_dir, ip="ip", owner="tb-gen", signature="B")
    rd.resolve_decision(ip_dir, owner="rtl-gen", signature="A", resolution="false_evidence_gate")

    open_records = rd.list_open_decisions(ip_dir)
    assert len(open_records) == 1
    assert open_records[0]["owner"] == "tb-gen"
    assert rd.count_open_decisions(ip_dir) == 1


def test_list_open_decisions_counts_generic_headless_records(tmp_path: Path) -> None:
    ip_dir = tmp_path / "ip"
    review_dir = ip_dir / "review"
    review_dir.mkdir(parents=True)
    generic = review_dir / "decision_needed_req_requirement_approval.json"
    generic.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "type": "review_decision_needed",
                "status": "review_decision_needed",
                "ip": "ip",
                "workflow": "req",
                "topic": "requirement_approval",
                "created_at": "2026-05-17T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )

    open_records = rd.list_open_decisions(ip_dir)
    assert len(open_records) == 1
    assert open_records[0]["workflow"] == "req"
    assert rd.count_open_decisions(ip_dir) == 1


def test_list_open_decisions_excludes_resolved_generic_records(tmp_path: Path) -> None:
    ip_dir = tmp_path / "ip"
    review_dir = ip_dir / "review"
    review_dir.mkdir(parents=True)
    generic = review_dir / "decision_needed_req_requirement_approval.json"
    generic.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "type": "review_decision_needed",
                "status": "resolved",
                "ip": "ip",
                "workflow": "req",
                "topic": "requirement_approval",
                "resolved_at": "2026-05-17T00:01:00Z",
            }
        ),
        encoding="utf-8",
    )

    assert rd.list_open_decisions(ip_dir) == []
    assert rd.count_open_decisions(ip_dir) == 0


def test_count_zero_when_review_dir_missing(tmp_path: Path) -> None:
    ip_dir = tmp_path / "ip"
    ip_dir.mkdir()
    assert rd.count_open_decisions(ip_dir) == 0
    assert rd.list_open_decisions(ip_dir) == []


def test_arm_m0_min_requirement_review_aid_paths_exist() -> None:
    """The real CPU approval decision must not point the Pipeline UI at stale
    or missing review aid files."""
    decision = (
        PROJECT_ROOT
        / "arm_m0_min"
        / "review"
        / "decision_needed_req_requirement_approval.json"
    )
    record = json.loads(decision.read_text(encoding="utf-8"))

    aids = record["evidence"]["review_aids"]
    assert aids == [
        "arm_m0_min/review/completion_readiness_checklist.md",
        "arm_m0_min/review/prompt_to_artifact_checklist.json",
        "arm_m0_min/review/prompt_to_artifact_checklist_audit.json",
        "doc/wiki/arm-m0-min-current-status.md",
        "arm_m0_min/doc/arm_m0_min_review_index.md",
        "arm_m0_min/doc/arm_m0_min_user_handoff.md",
        "arm_m0_min/doc/arm_m0_min_rtl_inventory.md",
        "arm_m0_min/doc/arm_m0_min_isa_decode_inventory.md",
    ]
    for aid in aids:
        assert (PROJECT_ROOT / aid).is_file(), aid


def test_arm_m0_min_review_index_references_review_aids() -> None:
    """The human review index should agree with the review-decision aid list."""
    decision = (
        PROJECT_ROOT
        / "arm_m0_min"
        / "review"
        / "decision_needed_req_requirement_approval.json"
    )
    record = json.loads(decision.read_text(encoding="utf-8"))
    index_text = (
        PROJECT_ROOT / "arm_m0_min" / "doc" / "arm_m0_min_review_index.md"
    ).read_text(encoding="utf-8")

    for aid in record["evidence"]["review_aids"]:
        if aid.endswith("arm_m0_min_review_index.md"):
            continue
        assert aid in index_text


def test_arm_m0_min_prompt_to_artifact_checklist_matches_current_state() -> None:
    """The machine-readable checklist should map the user goal to concrete
    artifacts and match the approved completion state."""
    checklist_path = (
        PROJECT_ROOT / "arm_m0_min" / "review" / "prompt_to_artifact_checklist.json"
    )
    checklist = json.loads(checklist_path.read_text(encoding="utf-8"))
    assert checklist["type"] == "prompt_to_artifact_completion_checklist"
    assert checklist["ip"] == "arm_m0_min"
    assert checklist["status"] == "pass"
    assert checklist["blocked_on"] == []
    assert "final_audit.status is pass" in checklist["completion_rule"]

    items = {item["id"]: item for item in checklist["checklist"]}
    expected_ids = {
        "cpu_ip_exists",
        "wiki_guidance_used",
        "ssot_exists",
        "models_exist",
        "rtl_exists",
        "compile_and_lint",
        "tb_and_sim",
        "equivalence",
        "coverage",
        "human_req_approval",
        "final_audit",
    }
    assert set(items) == expected_ids

    for item in checklist["checklist"]:
        for rel_path in item.get("evidence", []):
            assert (PROJECT_ROOT / rel_path).exists(), rel_path

    compare = json.loads(
        (PROJECT_ROOT / "arm_m0_min" / "sim" / "fl_rtl_compare.json").read_text(
            encoding="utf-8"
        )
    )
    eq = items["equivalence"]["expected_summary"]
    summary = compare["summary"]
    assert summary["goals_checked"] == eq["goals_checked"]
    assert summary["goals_passed"] == eq["goals_passed"]
    assert summary["goals_failed"] == eq["goals_failed"]
    assert summary["goals_blocked"] == eq["goals_blocked"]

    coverage = json.loads(
        (PROJECT_ROOT / "arm_m0_min" / "cov" / "coverage.json").read_text(
            encoding="utf-8"
        )
    )
    assert coverage["function_coverage"]["hit"] == 19
    assert coverage["function_coverage"]["total"] == 19
    assert coverage["cycle_coverage"]["hit"] == 17
    assert coverage["cycle_coverage"]["total"] == 17

    audit = json.loads(
        (PROJECT_ROOT / "arm_m0_min" / "sim" / "fl_rtl_goal_audit.json").read_text(
            encoding="utf-8"
        )
    )
    assert audit["status"] == "pass"
    assert audit["summary"]["passed_checks"] == 16
    assert audit["summary"]["total_checks"] == 16
    assert audit["summary"]["blockers"] == []
    assert items["human_req_approval"]["status"] == "pass"
    assert items["final_audit"]["status"] == "pass"
    assert (
        PROJECT_ROOT / "arm_m0_min" / "req" / "arm_m0_min_requirements.md"
    ).is_file()
    assert (
        PROJECT_ROOT / "arm_m0_min" / "req" / "approval_manifest.json"
    ).is_file()


def test_arm_m0_min_prompt_to_artifact_audit_artifact_matches_current_state() -> None:
    audit = json.loads(
        (
            PROJECT_ROOT
            / "arm_m0_min"
            / "review"
            / "prompt_to_artifact_checklist_audit.json"
        ).read_text(encoding="utf-8")
    )

    assert audit["type"] == "prompt_to_artifact_checklist_audit"
    assert audit["status"] == "pass"
    assert audit["completion_ready"] is True
    assert audit["blocked_items"] == []
    assert audit["errors"] == []
    assert audit["final_audit"] == {
        "status": "pass",
        "passed": "16/16",
        "blockers": [],
    }
    assert audit["written_to"] == "arm_m0_min/review/prompt_to_artifact_checklist_audit.json"


def test_arm_m0_min_handoff_preserves_approval_boundary() -> None:
    """The user-facing handoff must explain how to verify the approved CPU and
    preserve the req artifact boundary."""
    handoff = (
        PROJECT_ROOT / "arm_m0_min" / "doc" / "arm_m0_min_user_handoff.md"
    ).read_text(encoding="utf-8")

    assert "status=pass passed=16/16 blockers=none" in handoff
    assert "PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest" in handoff
    assert "promote_requirement_review.py arm_m0_min" in handoff
    assert "Do not manually edit `arm_m0_min/req/arm_m0_min_requirements.md`" in handoff
    assert "승인된 범위" in handoff
    assert "이 범위가 부족하면 승인 상태를 그대로 두지 말고 SSOT scope를 다시 열어야 합니다." in handoff


def test_arm_m0_min_readme_is_safe_entry_point() -> None:
    """The IP root README should orient reviewers to the approved CPU state."""
    readme = (PROJECT_ROOT / "arm_m0_min" / "README.md").read_text(encoding="utf-8")

    assert "doc/arm_m0_min_user_handoff.md" in readme
    assert "review/approval_request.md" in readme
    assert "status=pass passed=16/16 blockers=none" in readme
    assert "Do not manually edit `req/arm_m0_min_requirements.md`" in readme
    assert "req/approval_manifest.json" in readme
    assert "production ARM compatibility" in readme


def test_arm_m0_min_readiness_checklist_matches_open_req_blocker() -> None:
    """While the CPU approval decision is open, the human-facing checklist
    must match the actual final audit blocker instead of claiming completion."""
    decision = (
        PROJECT_ROOT
        / "arm_m0_min"
        / "review"
        / "decision_needed_req_requirement_approval.json"
    )
    record = json.loads(decision.read_text(encoding="utf-8"))
    if record.get("status") != "review_decision_needed":
        pytest.skip("arm_m0_min requirement review is no longer open")

    checklist = (
        PROJECT_ROOT
        / "arm_m0_min"
        / "review"
        / "completion_readiness_checklist.md"
    ).read_text(encoding="utf-8")
    audit = json.loads(
        (PROJECT_ROOT / "arm_m0_min" / "sim" / "fl_rtl_goal_audit.json").read_text(
            encoding="utf-8"
        )
    )
    summary = audit["summary"]

    assert audit["status"] == "fail"
    assert summary["blockers"] == ["req"]
    assert "Status: ready for human requirement review, not complete." in checklist
    assert f"`passed={summary['passed_checks']}/{summary['total_checks']}`" in checklist
    assert "`blockers=req`" in checklist
    assert "approve_locked_scope" in checklist
    assert "Regression result: pass in latest verification" in checklist
    assert "80 passed" not in checklist
    assert not (PROJECT_ROOT / "arm_m0_min" / "req" / "arm_m0_min_requirements.md").exists()
    assert not (PROJECT_ROOT / "arm_m0_min" / "req" / "approval_manifest.json").exists()


def test_arm_m0_min_requirement_review_pinned_hashes_match_artifacts() -> None:
    """The open approval decision must pin the exact artifacts a human is
    reviewing; stale hashes would make approval unsafe."""
    decision = (
        PROJECT_ROOT
        / "arm_m0_min"
        / "review"
        / "decision_needed_req_requirement_approval.json"
    )
    record = json.loads(decision.read_text(encoding="utf-8"))
    if record.get("status") != "review_decision_needed":
        pytest.skip("arm_m0_min requirement review has been resolved")
    evidence = record["evidence"]

    approval_target = evidence["approval_target"]
    approval_path = PROJECT_ROOT / approval_target["path"]
    assert approval_path.is_file()
    assert hashlib.sha256(approval_path.read_bytes()).hexdigest() == approval_target["sha256"]

    snapshot = evidence["machine_evidence_snapshot"]
    expected_paths = {
        "completion_audit_sha256": "arm_m0_min/doc/arm_m0_min_completion_audit.md",
        "ssot_sha256": "arm_m0_min/yaml/arm_m0_min.ssot.yaml",
        "fl_rtl_compare_sha256": "arm_m0_min/sim/fl_rtl_compare.json",
        "coverage_sha256": "arm_m0_min/cov/coverage.json",
    }
    for key, rel_path in expected_paths.items():
        path = PROJECT_ROOT / rel_path
        assert path.is_file(), rel_path
        assert hashlib.sha256(path.read_bytes()).hexdigest() == snapshot[key]


def test_concurrent_writes_same_decision_no_rename_race(tmp_path: Path) -> None:
    """Two threads rewriting the same review-decision file must not race on
    the tmp→target rename. Pre-fix this raised
    `[Errno 2] No such file or directory: '...tmp' -> '...json'` because both
    threads shared a single `.tmp` filename. Per-thread unique tmp suffixes
    fix it. Surfaced by T26 of the deep^4 adversarial test."""
    import threading

    ip_dir = tmp_path / "ip"
    ip_dir.mkdir()
    barrier = threading.Barrier(2)
    errors: list[str] = []

    def write(retries: int) -> None:
        barrier.wait()
        try:
            for _ in range(20):
                rd.write_repeated_mismatch_decision(
                    ip_dir, ip="ip", owner="rtl-gen", retry_attempts=retries
                )
        except Exception as e:
            errors.append(str(e))

    t1 = threading.Thread(target=write, args=(3,))
    t2 = threading.Thread(target=write, args=(5,))
    t1.start(); t2.start(); t1.join(); t2.join()
    assert errors == [], errors
    record = json.loads(rd.decision_path(ip_dir, "rtl-gen").read_text())
    assert record["retry_attempts"] in (3, 5)
