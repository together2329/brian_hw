from __future__ import annotations

import json
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "workflow" / "tb-gen" / "scripts" / "check_scoreboard_events.py"


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_scoreboard(ip_dir: Path, rtl_observed: dict) -> None:
    path = ip_dir / "sim" / "scoreboard_events.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "goal_id": "EQ_DATA",
                "scenario_id": "SC_DATA",
                "cycle": 1,
                "stimulus": {"kind": "READ"},
                "fl_expected": {"model_api": "FunctionalModel.apply", "model_result": {"data_o": 3}},
                "rtl_observed": rtl_observed,
                "passed": True,
                "mismatch": "",
                "coverage_refs": ["SC_DATA_executed"],
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _make_ip(root: Path) -> Path:
    ip_dir = root / "observable_ip"
    _write_json(
        ip_dir / "verify" / "equivalence_goals.json",
        {
            "goals": [
                {
                    "goal_id": "EQ_DATA",
                    "expected_contract": {
                        "observables": [
                            "data_o",
                            "valid_o",
                            "human prose description with spaces",
                            "result_o=0.",
                        ]
                    },
                }
            ]
        },
    )
    return ip_dir


def test_scoreboard_gate_rejects_missing_signal_like_observable(tmp_path: Path) -> None:
    ip_dir = _make_ip(tmp_path)
    _write_scoreboard(ip_dir, {"data_o": 3})

    result = subprocess.run(
        ["python3", str(SCRIPT), "observable_ip", "--root", str(tmp_path), "--require-events"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 1
    assert "valid_o" in result.stdout
    assert "human prose" not in result.stdout
    assert "result_o=0" not in result.stdout


def test_scoreboard_gate_accepts_signal_observables_and_ignores_prose(tmp_path: Path) -> None:
    ip_dir = _make_ip(tmp_path)
    _write_scoreboard(ip_dir, {"data_o": 3, "valid_o": 1})

    result = subprocess.run(
        ["python3", str(SCRIPT), "observable_ip", "--root", str(tmp_path), "--require-events"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 0, result.stdout
    assert "PASS" in result.stdout
