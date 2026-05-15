from __future__ import annotations

import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

_EXPECTED_STAGE_IDS = [
    "ssot", "fl-model", "cl-model", "equivalence", "rtl",
    "lint", "tb", "sim", "coverage", "sim-debug",
    "syn", "sta", "pnr", "sta-post", "goal-audit",
]


def _make_client(tmp_path: Path, monkeypatch) -> TestClient:
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    client = TestClient(atlas_ui.create_app())
    reg = client.post("/api/auth/register", json={"username": "u", "password": "pw"})
    assert reg.status_code == 200, reg.text
    return client


def test_pipeline_state_returns_15_stages(tmp_path: Path, monkeypatch) -> None:
    ip = "smoke_ip"
    (tmp_path / ip).mkdir()

    client = _make_client(tmp_path, monkeypatch)
    resp = client.get(f"/api/pipeline/state?ip={ip}")
    assert resp.status_code == 200, resp.text

    data = resp.json()
    assert data["ip"] == ip
    assert "stages" in data
    stage_keys = list(data["stages"].keys())
    assert stage_keys == _EXPECTED_STAGE_IDS, stage_keys
    assert len(stage_keys) == 15

    _valid_states = {"idle", "ready", "running", "passed", "failed", "blocked", "stale", "locked"}
    for sid, sdata in data["stages"].items():
        assert sdata["state"] in _valid_states, f"{sid}: invalid state {sdata['state']}"
        assert "scoresheet" in sdata
        assert "glyph" in sdata
    # ssot has no deps and no artifacts → idle
    assert data["stages"]["ssot"]["state"] == "idle"


def test_pipeline_state_passed_when_ssot_present(tmp_path: Path, monkeypatch) -> None:
    ip = "smoke_ssot_ip"
    yaml_dir = tmp_path / ip / "yaml"
    yaml_dir.mkdir(parents=True)

    # write a minimal ssot with 34 sections
    sections = "\n".join(
        f"  - name: section_{i}\n    description: desc_{i}" for i in range(34)
    )
    ssot_text = f"ip: {ip}\nsections:\n{sections}\n"
    (yaml_dir / f"{ip}.ssot.yaml").write_text(ssot_text, encoding="utf-8")

    client = _make_client(tmp_path, monkeypatch)
    resp = client.get(f"/api/pipeline/state?ip={ip}")
    assert resp.status_code == 200, resp.text

    data = resp.json()
    ssot_stage = data["stages"]["ssot"]
    assert ssot_stage["state"] == "passed", f"expected passed, got {ssot_stage['state']}"
    assert ssot_stage["scoresheet"][0] == "pass"
    assert ssot_stage["top"] != ""
