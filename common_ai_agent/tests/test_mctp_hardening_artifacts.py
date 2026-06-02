from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast


REPO = Path(__file__).resolve().parents[1]
IP_DIR = REPO / "mctp_assembler_scratch"


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_directed_scenarios_have_dut_observed_e2e_summary() -> None:
    manifest = _read_json(IP_DIR / "tc" / "scenario_manifest.json")
    scenario_items = cast(list[dict[str, Any]], manifest["scenarios"])
    expected_ids = {
        str(item["scenario_id"])
        for item in scenario_items
        if isinstance(item, dict)
    }

    summary = _read_json(IP_DIR / "sim" / "scenario_e2e_summary.json")

    assert summary["status"] == "pass"
    assert summary["total_directed_scenarios"] == len(expected_ids)
    assert set(summary["missing_scenarios"]) == set()
    rows = summary["scenarios"]
    assert isinstance(rows, list)
    observed_ids = {str(row["scenario_id"]) for row in rows if isinstance(row, dict)}
    assert observed_ids == expected_ids
    for row in rows:
        assert isinstance(row, dict)
        assert row["dut_observed"] is True
        assert row["scoreboard_passed"] is True
        assert row["rtl_observable_count"] > 0


def test_monitors_prove_sram_axi_and_apb_hardening() -> None:
    monitor = _read_json(IP_DIR / "sim" / "monitor_evidence.json")

    assert monitor["status"] == "pass"
    checks = cast(dict[str, bool], monitor["checks"])
    for key in (
        "sram_payload_no_holes",
        "sram_payload_only",
        "sram_no_header_or_pad_write",
        "axi_write_protocol_pass",
        "axi_read_protocol_pass",
        "apb_per_q_readback_pass",
    ):
        assert checks[key] is True
    summary = cast(dict[str, int], monitor["summary"])
    assert summary["sram_write_count"] > 0
    assert summary["axi_write_transactions"] > 0
    assert summary["axi_read_transactions"] > 0
    assert summary["apb_reads"] > 0


def test_survived_mutants_are_classified_and_formal_is_recorded() -> None:
    classification = _read_json(IP_DIR / "mutation" / "survivor_classification.json")
    formal = _read_json(IP_DIR / "verify" / "formal_status.json")

    assert classification["status"] == "pass"
    classification_summary = cast(dict[str, int], classification["summary"])
    assert classification_summary["total_survivors"] <= 16
    assert classification_summary["classified"] == classification_summary["total_survivors"]
    allowed = {"equivalent", "irrelevant", "test_hole"}
    survivors = cast(list[dict[str, str]], classification["survivors"])
    for survivor in survivors:
        assert survivor["disposition"] in allowed
        assert survivor["rationale"]
        assert survivor["next_action"]
    assert formal["status"] == "optional_not_run"
    assert formal["tool"] == "sby"
    properties = cast(list[dict[str, Any]], formal["properties"])
    assert len(properties) >= 5
    assert (IP_DIR / "verify" / "safety_properties.sva").is_file()
