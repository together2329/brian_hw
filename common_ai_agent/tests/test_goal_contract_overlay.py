from __future__ import annotations

import subprocess
from pathlib import Path

from .contract_reflection_helpers import EVIDENCE_SCRIPT, REFLECTION_SCRIPT, make_contract_ip, read_json, write_json, write_rows


OVERLAY_SCRIPT = Path(__file__).resolve().parents[1] / "workflow" / "contract-reflection" / "scripts" / "emit_goal_contract_overlay.py"


def _write_reflection_stage_files(ip_dir: Path) -> None:
    for path in (
        "yaml/contract_ip.ssot.yaml",
        "model/functional_model.py",
        "model/cycle_model.py",
        "rtl/contract_ip.sv",
        "tb/cocotb/test_contract_ip.py",
    ):
        target = ip_dir / path
        target.parent.mkdir(parents=True, exist_ok=True)
        _ = target.write_text("// marker\n" if path.endswith(".sv") else "# marker\n", encoding="utf-8")


def test_goal_contract_overlay_adds_equivalence_goal_obligations_and_reflection(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)
    _write_reflection_stage_files(ip_dir)
    write_json(
        ip_dir / "verify" / "equivalence_goals.json",
        {
            "goals": [
                {"goal_id": "EQ_ALPHA", "title": "alpha goal"},
                {"goal_id": "EQ_BETA", "title": "beta goal"},
            ],
            "schema_version": 1,
            "type": "equivalence_goals",
        },
    )
    write_json(
        ip_dir / "verify" / "contract_reflection.json",
        {
            "contract_refs": [
                {
                    "contract_ref": "STATE_PAYLOAD_COUNT",
                    "fl": {"path": "model/functional_model.py"},
                    "cl": {"path": "model/cycle_model.py"},
                    "rtl": {"owner_files": ["rtl/contract_ip.sv"], "observable_via": ["payload_byte_count"]},
                    "sim": {"scoreboard": "sim/scoreboard_events.jsonl", "wave": "sim/contract_ip.vcd"},
                    "ssot": {"path": "yaml/contract_ip.ssot.yaml"},
                    "tb": {"path": "tb/cocotb/test_contract_ip.py", "monitor": "payload_monitor"},
                }
            ],
            "schema_version": 1,
            "type": "contract_reflection",
        },
    )
    write_rows(
        ip_dir / "sim" / "scoreboard_events.jsonl",
        [
            {
                "goal_id": "EQ_PAYLOAD",
                "scenario_id": "SC_PAYLOAD",
                "passed": True,
                "rtl_observed": {"payload_byte_count": 17, "sram_wr_strb": 0x1FFFF},
            },
            {"goal_id": "EQ_ALPHA", "scenario_id": "SC_ALPHA", "passed": True, "rtl_observed": {"payload_byte_count": 1}},
            {"goal_id": "EQ_BETA", "scenario_id": "SC_BETA", "passed": True, "rtl_observed": {"payload_byte_count": 2}},
        ],
    )
    _ = (ip_dir / "sim" / "contract_ip.vcd").write_text(
        "$var wire 13 ! payload_byte_count [12:0] $end\n#0\nb1 !\n#10\nb10 !\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["python3", str(OVERLAY_SCRIPT), "contract_ip", "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 0, result.stdout
    requirements = read_json(ip_dir / "verify" / "requirements_index.json")
    contract = read_json(ip_dir / "verify" / "evidence_contract.json")
    reflection = read_json(ip_dir / "verify" / "contract_reflection.json")
    assert "OBL_GOAL_EQ_ALPHA" in str(requirements)
    assert "OBL_GOAL_EQ_BETA" in str(contract)
    assert "LEGACY_SCOREBOARD_GOAL_CLOSURE" in str(reflection)

    evidence = subprocess.run(
        ["python3", str(EVIDENCE_SCRIPT), "contract_ip", "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    reflection_result = subprocess.run(
        ["python3", str(REFLECTION_SCRIPT), "contract_ip", "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert evidence.returncode == 0, evidence.stdout
    assert reflection_result.returncode == 0, reflection_result.stdout


def test_goal_contract_overlay_bootstraps_missing_contract_files_from_equivalence_goals(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)
    (ip_dir / "verify" / "requirements_index.json").unlink()
    (ip_dir / "verify" / "evidence_contract.json").unlink()
    _write_reflection_stage_files(ip_dir)
    write_json(
        ip_dir / "verify" / "equivalence_goals.json",
        {"goals": [{"goal_id": "EQ_ALPHA"}], "schema_version": 1, "type": "equivalence_goals"},
    )
    write_rows(
        ip_dir / "sim" / "scoreboard_events.jsonl",
        [{"goal_id": "EQ_ALPHA", "scenario_id": "SC_ALPHA", "passed": True, "rtl_observed": {"payload_byte_count": 1}}],
    )
    _ = (ip_dir / "sim" / "contract_ip.vcd").write_text("$var wire 13 ! payload_byte_count [12:0] $end\n#0\nb1 !\n", encoding="utf-8")

    result = subprocess.run(
        ["python3", str(OVERLAY_SCRIPT), "contract_ip", "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 0, result.stdout
    requirements = read_json(ip_dir / "verify" / "requirements_index.json")
    contract = read_json(ip_dir / "verify" / "evidence_contract.json")
    assert requirements["type"] == "requirements_index"
    assert contract["type"] == "evidence_contract"
    assert "OBL_GOAL_EQ_ALPHA" in str(contract)


def test_goal_contract_overlay_is_byte_idempotent_after_first_write(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)
    _write_reflection_stage_files(ip_dir)
    write_json(
        ip_dir / "verify" / "equivalence_goals.json",
        {"goals": [{"goal_id": "EQ_ALPHA"}], "schema_version": 1, "type": "equivalence_goals"},
    )
    write_json(
        ip_dir / "verify" / "contract_reflection.json",
        {
            "contract_refs": [
                {
                    "contract_ref": "STATE_PAYLOAD_COUNT",
                    "fl": {"path": "model/functional_model.py"},
                    "cl": {"path": "model/cycle_model.py"},
                    "rtl": {"owner_files": ["rtl/contract_ip.sv"], "observable_via": ["payload_byte_count"]},
                    "sim": {"scoreboard": "sim/scoreboard_events.jsonl", "wave": "sim/contract_ip.vcd"},
                    "ssot": {"path": "yaml/contract_ip.ssot.yaml"},
                    "tb": {"path": "tb/cocotb/test_contract_ip.py", "monitor": "payload_monitor"},
                }
            ],
            "schema_version": 1,
            "type": "contract_reflection",
        },
    )
    write_rows(
        ip_dir / "sim" / "scoreboard_events.jsonl",
        [
            {
                "goal_id": "EQ_PAYLOAD",
                "scenario_id": "SC_PAYLOAD",
                "passed": True,
                "rtl_observed": {"payload_byte_count": 17, "sram_wr_strb": 0x1FFFF},
            },
            {"goal_id": "EQ_ALPHA", "scenario_id": "SC_ALPHA", "passed": True, "rtl_observed": {"payload_byte_count": 1}},
        ],
    )
    _ = (ip_dir / "sim" / "contract_ip.vcd").write_text("$var wire 13 ! payload_byte_count [12:0] $end\n#0\nb1 !\n", encoding="utf-8")

    first = subprocess.run(["python3", str(OVERLAY_SCRIPT), "contract_ip", "--root", str(tmp_path)], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    before = {path: (ip_dir / path).read_bytes() for path in ("verify/requirements_index.json", "verify/evidence_contract.json", "verify/contract_reflection.json")}
    second = subprocess.run(["python3", str(OVERLAY_SCRIPT), "contract_ip", "--root", str(tmp_path)], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    after = {path: (ip_dir / path).read_bytes() for path in before}

    assert first.returncode == 0, first.stdout
    assert second.returncode == 0, second.stdout
    assert after == before


def test_goal_contract_overlay_does_not_claim_closure_without_scoreboard_row(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)
    _write_reflection_stage_files(ip_dir)
    write_json(
        ip_dir / "verify" / "equivalence_goals.json",
        {"goals": [{"goal_id": "EQ_MISSING"}], "schema_version": 1, "type": "equivalence_goals"},
    )
    _ = (ip_dir / "sim" / "contract_ip.vcd").write_text("$var wire 13 ! payload_byte_count [12:0] $end\n#0\nb1 !\n", encoding="utf-8")

    result = subprocess.run(
        ["python3", str(OVERLAY_SCRIPT), "contract_ip", "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    contract = read_json(ip_dir / "verify" / "evidence_contract.json")
    assert result.returncode == 0, result.stdout
    assert "requires a matching scoreboard row before closure" in str(contract)
    assert "EQ_MISSING closes through" not in str(contract)
