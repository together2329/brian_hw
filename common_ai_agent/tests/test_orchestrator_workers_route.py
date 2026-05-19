from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

_EXPECTED_WORKFLOWS = [
    "ssot-gen", "fl-model-gen", "rtl-gen", "lint", "tb-gen",
    "sim", "coverage", "sim_debug", "syn", "sta", "pnr", "sta-post",
]


def _make_client(tmp_path: Path, monkeypatch) -> TestClient:
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "SOURCE_ROOT", tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    client = TestClient(atlas_ui.create_app())
    reg = client.post("/api/auth/register", json={"username": "u", "password": "pw"})
    assert reg.status_code == 200, reg.text
    return client


def test_workers_route_returns_12_workers(tmp_path: Path, monkeypatch) -> None:
    # Stub urlopen so health probes don't block on real network.
    import urllib.request

    def _fake_urlopen(req, timeout=None):
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"status": "unreachable"}'
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        return mock_resp

    monkeypatch.setattr(urllib.request, "urlopen", _fake_urlopen)

    client = _make_client(tmp_path, monkeypatch)
    resp = client.get("/api/orchestrator/workers?ip=pl330")
    assert resp.status_code == 200, resp.text

    data = resp.json()
    assert "workers" in data, data

    workers = data["workers"]
    assert len(workers) == 12, f"expected 12 workers, got {len(workers)}: {[w['workflow'] for w in workers]}"

    workflow_names = {w["workflow"] for w in workers}
    assert "goal-audit" not in workflow_names, "dead goal-audit entry must not appear"
    assert workflow_names == set(_EXPECTED_WORKFLOWS), (
        f"workflow mismatch: got {workflow_names}"
    )
