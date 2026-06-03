from __future__ import annotations

import subprocess
from pathlib import Path

from .contract_reflection_helpers import REFLECTION_SCRIPT, make_contract_ip, read_json, write_json


def _write_stage_artifacts(ip_dir: Path) -> None:
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


def _write_reflection(ip_dir: Path, fl_path: str = "model/functional_model.py") -> None:
    write_json(
        ip_dir / "verify" / "contract_reflection.json",
        {
            "contract_refs": [
                {
                    "contract_ref": "STATE_PAYLOAD_COUNT",
                    "fl": {"path": fl_path},
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


def test_contract_reflection_passes_when_every_contract_ref_has_stage_and_wave_evidence(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)
    _write_stage_artifacts(ip_dir)
    _ = (ip_dir / "sim" / "contract_ip.vcd").write_text(
        "$var wire 13 ! payload_byte_count [12:0] $end\n#0\nb10001 !\n",
        encoding="utf-8",
    )
    _write_reflection(ip_dir)

    result = subprocess.run(
        ["python3", str(REFLECTION_SCRIPT), "contract_ip", "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 0, result.stdout
    report = read_json(ip_dir / "signoff" / "contract_reflection_coverage.json")
    assert report["status"] == "pass"


def test_contract_reflection_fails_when_wave_only_declares_signal(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)
    _write_stage_artifacts(ip_dir)
    _ = (ip_dir / "sim" / "contract_ip.vcd").write_text(
        "$var wire 13 ! payload_byte_count [12:0] $end\n",
        encoding="utf-8",
    )
    _write_reflection(ip_dir)

    result = subprocess.run(
        ["python3", str(REFLECTION_SCRIPT), "contract_ip", "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 1
    assert "VCD missing samples for payload_byte_count" in result.stdout


def test_contract_reflection_fails_when_contract_ref_has_no_reflection(tmp_path: Path) -> None:
    _ = make_contract_ip(tmp_path)
    write_json(
        tmp_path / "contract_ip" / "verify" / "contract_reflection.json",
        {"contract_refs": [], "schema_version": 1, "type": "contract_reflection"},
    )

    result = subprocess.run(
        ["python3", str(REFLECTION_SCRIPT), "contract_ip", "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 1
    assert "missing reflection for STATE_PAYLOAD_COUNT" in result.stdout


def test_contract_reflection_rejects_artifact_paths_outside_ip_root(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)
    _write_reflection(ip_dir, fl_path="../outside.py")

    result = subprocess.run(
        ["python3", str(REFLECTION_SCRIPT), "contract_ip", "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 1
    assert "path escapes IP root" in result.stdout
