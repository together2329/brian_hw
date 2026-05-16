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
    # scoresheet entries are now labeled dicts: {state, label, evidence_path}
    first_dot = ssot_stage["scoresheet"][0]
    assert isinstance(first_dot, dict)
    assert first_dot["state"] == "pass"
    assert first_dot["label"]  # non-empty
    assert "ssot" in first_dot["evidence_path"]
    assert ssot_stage["top"] != ""
    assert ssot_stage["source"] == "fs"  # came from filesystem (no DB row)


def test_pipeline_state_db_row_overrides_filesystem(tmp_path: Path, monkeypatch) -> None:
    """A workflow_runs row in the DB should make stage='passed' even with NO
    on-disk evidence, and 'failed' when status='error'. This is the DB-first
    state derivation that lets the UI reflect runs even after artifact moves."""
    import os
    from core.atlas_db import AtlasDB

    ip = "db_state_ip"
    (tmp_path / ip).mkdir()  # IP dir exists, but no rtl/ artifacts

    # Pre-create the DB and insert a completed rtl-gen run for this IP.
    db_path = tmp_path / "atlas.db"
    os.environ["ATLAS_DB_PATH"] = str(db_path)
    with AtlasDB(str(db_path)) as db:
        ws = db.upsert_workspace(tmp_path.name or "default", local_path=str(tmp_path))
        ipb = db.upsert_ip_block(ws["id"], ip)
        run = db.start_workflow_run(
            session_id="default",
            workspace_id=ws["id"],
            ip_id=ipb["id"],
            workflow="rtl-gen",
            mode="pipeline",
            model_profile="gpt-5.3-codex",
            reasoning_effort="high",
            trigger="test",
        )
        db.finish_workflow_run(run["id"], status="completed")

    client = _make_client(tmp_path, monkeypatch)
    resp = client.get(f"/api/pipeline/state?ip={ip}")
    assert resp.status_code == 200, resp.text

    data = resp.json()
    rtl_stage = data["stages"]["rtl"]
    # No rtl/*.sv on disk, but DB has a completed rtl-gen run → state must
    # come from the DB and be 'passed'.
    assert rtl_stage["state"] == "passed", f"expected passed (DB-first), got {rtl_stage['state']}"
    assert rtl_stage["source"] == "db"


def test_pipeline_state_db_failed_propagates_error_summary(tmp_path: Path, monkeypatch) -> None:
    """A workflow_runs row with status=error should map to state=failed
    and surface error_summary in the response."""
    import os
    from core.atlas_db import AtlasDB

    ip = "db_failed_ip"
    (tmp_path / ip).mkdir()

    db_path = tmp_path / "atlas.db"
    os.environ["ATLAS_DB_PATH"] = str(db_path)
    with AtlasDB(str(db_path)) as db:
        ws = db.upsert_workspace(tmp_path.name or "default", local_path=str(tmp_path))
        ipb = db.upsert_ip_block(ws["id"], ip)
        run = db.start_workflow_run(
            session_id="default",
            workspace_id=ws["id"],
            ip_id=ipb["id"],
            workflow="lint",
            mode="pipeline",
            model_profile="gpt-5.3-codex",
            reasoning_effort="medium",
            trigger="test",
        )
        db.finish_workflow_run(run["id"], status="error", error_summary="lint produced 7 errors")

    client = _make_client(tmp_path, monkeypatch)
    resp = client.get(f"/api/pipeline/state?ip={ip}")
    assert resp.status_code == 200, resp.text

    data = resp.json()
    lint_stage = data["stages"]["lint"]
    assert lint_stage["state"] == "failed", f"expected failed, got {lint_stage['state']}"
    assert lint_stage["error_summary"] == "lint produced 7 errors"
    assert lint_stage["source"] == "db"


def test_pipeline_state_locked_reason_names_missing_upstream(tmp_path: Path, monkeypatch) -> None:
    """A locked stage should populate locked_reason like 'needs ssot'."""
    ip = "locked_ip"
    (tmp_path / ip).mkdir()

    client = _make_client(tmp_path, monkeypatch)
    resp = client.get(f"/api/pipeline/state?ip={ip}")
    assert resp.status_code == 200, resp.text

    data = resp.json()
    # fl-model depends on ssot; with no ssot artifact and no DB row, fl-model
    # should be locked with reason 'needs ssot'.
    fl = data["stages"]["fl-model"]
    assert fl["state"] == "locked", f"expected locked, got {fl['state']}"
    assert fl["locked_reason"] and "ssot" in fl["locked_reason"], fl["locked_reason"]
