from __future__ import annotations

import json
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


def test_count_zero_when_review_dir_missing(tmp_path: Path) -> None:
    ip_dir = tmp_path / "ip"
    ip_dir.mkdir()
    assert rd.count_open_decisions(ip_dir) == 0
    assert rd.list_open_decisions(ip_dir) == []


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
