from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Union


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "workflow" / "sim_debug" / "scripts" / "check_simulation_quality.py"
JsonValue = Union[None, bool, int, float, str, list["JsonValue"], dict[str, "JsonValue"]]
JsonMap = dict[str, JsonValue]


def _write_json(path: Path, payload: JsonMap) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_rows(ip_dir: Path, rows: list[JsonMap]) -> None:
    path = ip_dir / "sim" / "scoreboard_events.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _row(scenario_id: str, observed: JsonMap) -> JsonMap:
    return {
        "goal_id": f"EQ_{scenario_id}",
        "scenario_id": scenario_id,
        "cycle": 1,
        "stimulus": {"kind": scenario_id},
        "fl_expected": {"model_api": "FunctionalModel.apply", "model_result": {"ok": 1}},
        "rtl_observed": observed,
        "passed": True,
        "mismatch": "",
        "coverage_refs": [f"{scenario_id}_covered"],
    }


def _make_ip(tmp_path: Path) -> Path:
    ip_dir = tmp_path / "quality_ip"
    _write_json(
        ip_dir / "verify" / "ip_contract.json",
        {
            "observability": {
                "required_rtl_observed": [
                    "sram_wr_valid",
                    "sram_wr_strb",
                    "readback_valid",
                    "pready",
                ]
            }
        },
    )
    return ip_dir


def test_simulation_quality_rejects_drop_that_writes_sram(tmp_path: Path) -> None:
    ip_dir = _make_ip(tmp_path)
    _write_rows(
        ip_dir,
        [
            _row("SC_PACKET_DROP", {"sram_wr_valid": 1, "sram_wr_strb": 3, "readback_valid": 0, "pready": 0}),
            _row("SC_AXI_READBACK", {"sram_wr_valid": 0, "sram_wr_strb": 0, "readback_valid": 1, "pready": 0}),
            _row("SC_APB_REGISTER", {"sram_wr_valid": 0, "sram_wr_strb": 0, "readback_valid": 0, "pready": 1}),
        ],
    )

    result = subprocess.run(
        ["python3", str(SCRIPT), "quality_ip", "--root", str(tmp_path), "--require-class", "drop"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 1
    assert "drop scenario wrote SRAM" in result.stdout


def test_simulation_quality_rejects_missing_required_observable(tmp_path: Path) -> None:
    ip_dir = _make_ip(tmp_path)
    _write_rows(ip_dir, [_row("SC_APB_REGISTER", {"sram_wr_valid": 0, "sram_wr_strb": 0, "pready": 1})])

    result = subprocess.run(
        ["python3", str(SCRIPT), "quality_ip", "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 1
    assert "missing required observable(s): readback_valid" in result.stdout


def test_simulation_quality_rejects_missing_required_class(tmp_path: Path) -> None:
    ip_dir = _make_ip(tmp_path)
    _write_rows(
        ip_dir,
        [_row("SC_APB_REGISTER", {"sram_wr_valid": 0, "sram_wr_strb": 0, "readback_valid": 0, "pready": 1})],
    )

    result = subprocess.run(
        ["python3", str(SCRIPT), "quality_ip", "--root", str(tmp_path), "--require-class", "drop"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 1
    assert "missing required simulation class drop" in result.stdout


def test_simulation_quality_rejects_ip_paths_outside_root(tmp_path: Path) -> None:
    escaped_ip = tmp_path.parent / "escaped_quality_ip"

    result = subprocess.run(
        ["python3", str(SCRIPT), "../escaped_quality_ip", "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 1
    assert "must stay under --root" in result.stdout
    assert not (escaped_ip / "sim" / "simulation_quality.json").exists()


def test_simulation_quality_accepts_contract_driven_scenarios(tmp_path: Path) -> None:
    ip_dir = _make_ip(tmp_path)
    _write_rows(
        ip_dir,
        [
            _row(
                "SC_SRAM_PACK_NO_HOLES",
                {
                    "sram_wr_valid": 1,
                    "sram_wr_addr": 32,
                    "sram_wr_data": 1234,
                    "sram_wr_strb": 15,
                    "readback_valid": 0,
                    "pready": 0,
                },
            ),
            _row("SC_PACKET_DROP", {"sram_wr_valid": 0, "sram_wr_strb": 0, "readback_valid": 0, "pready": 0}),
            _row("SC_AXI_READBACK", {"sram_wr_valid": 0, "sram_wr_strb": 0, "readback_valid": 1, "readback_last": 1, "pready": 0}),
            _row("SC_APB_REGISTER", {"sram_wr_valid": 0, "sram_wr_strb": 0, "readback_valid": 0, "pready": 1}),
        ],
    )

    result = subprocess.run(
        [
            "python3",
            str(SCRIPT),
            "quality_ip",
            "--root",
            str(tmp_path),
            "--require-class",
            "memory_pack",
            "--require-class",
            "drop",
            "--require-class",
            "readback",
            "--require-class",
            "register",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 0, result.stdout
    report = json.loads((ip_dir / "sim" / "simulation_quality.json").read_text(encoding="utf-8"))
    assert report["status"] == "pass"
    assert report["summary"]["rows"] == 4


def test_simulation_quality_rejects_multi_assemble_without_distinct_context(tmp_path: Path) -> None:
    ip_dir = _make_ip(tmp_path)
    _write_rows(
        ip_dir,
        [
            _row(
                "SC_MULTI_FRAGMENT_3PKT_SHORT_LAST",
                {
                    "sram_wr_valid": 1,
                    "sram_wr_addr": 0,
                    "sram_wr_data": 0x1234,
                    "sram_wr_strb": 0xFFFF,
                    "payload_byte_count": 16,
                    "descriptor_count": 1,
                    "debug_context_key": 0,
                    "readback_valid": 0,
                    "pready": 0,
                },
            )
        ],
    )

    result = subprocess.run(
        ["python3", str(SCRIPT), "quality_ip", "--root", str(tmp_path), "--require-class", "multi_assemble"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 1
    assert "multi assemble row lacks accumulated payload evidence" in result.stdout


def test_simulation_quality_rejects_valid_interleave_with_drop_or_error(tmp_path: Path) -> None:
    ip_dir = _make_ip(tmp_path)
    _write_rows(
        ip_dir,
        [
            _row(
                "SC_INTERLEAVE_TWO_Q_COMPLETE",
                {
                    "sram_wr_valid": 0,
                    "sram_wr_strb": 0,
                    "debug_drop_pulse": 1,
                    "ctx_error": 1,
                    "debug_context_key": 0xC46,
                    "descriptor_count": 1,
                    "readback_valid": 0,
                    "pready": 0,
                },
            )
        ],
    )

    result = subprocess.run(
        ["python3", str(SCRIPT), "quality_ip", "--root", str(tmp_path), "--require-class", "interleave"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 1
    assert "valid/interleave scenario asserted drop or error" in result.stdout


def test_simulation_quality_rejects_max_tu_without_expected_payload_count(tmp_path: Path) -> None:
    ip_dir = _make_ip(tmp_path)
    row = _row(
        "SC_MAX_TU_4096_129_BEATS",
        {
            "sram_wr_valid": 1,
            "sram_wr_addr": 0,
            "sram_wr_data": 0x1234,
            "sram_wr_strb": 0xFFFF,
            "ctx_payload_count": 16,
            "descriptor_count": 1,
            "readback_valid": 0,
            "pready": 0,
        },
    )
    row["fl_expected"] = {
        "observables": ["No overflow and descriptor byte count equals 4096"],
        "stimulus_contract": {"scenario_payload_bytes": 4096},
    }
    _write_rows(ip_dir, [row])

    result = subprocess.run(
        ["python3", str(SCRIPT), "quality_ip", "--root", str(tmp_path), "--require-class", "boundary"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 1
    assert "payload evidence 16 below expected 4096" in result.stdout
