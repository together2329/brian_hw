from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))


def test_worker_run_restores_locked_truth_mutation_under_request_project_root(
    tmp_path: Path,
    monkeypatch,
) -> None:
    agent_server = importlib.import_module("core.agent_server")
    react_loop = importlib.import_module("core.react_loop")

    project_root = tmp_path / "alice" / "alt"
    source_root = tmp_path / "source"
    ip = "pl330"
    session_name = "alice/alt/pl330/rtl-gen"
    req_dir = project_root / ip / "req"
    req_file = req_dir / f"{ip}_requirements.md"
    manifest_file = req_dir / "approval_manifest.json"
    req_dir.mkdir(parents=True)
    source_root.mkdir(parents=True)
    req_file.write_text("locked requirement\n", encoding="utf-8")
    manifest_file.write_text(
        json.dumps({"artifact": f"req/{ip}_requirements.md", "status": "approved"}) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(project_root))
    monkeypatch.setenv("ATLAS_WORKSPACE_ROOT", str(project_root))
    monkeypatch.setattr(agent_server, "_project_root", str(source_root))
    monkeypatch.setattr(agent_server, "_PERSISTENCE_ENABLED", False)

    def fake_run_react_agent_impl(*, messages, tracker, **_kwargs):
        req_file.write_text("mutated by worker\n", encoding="utf-8")
        tracker.current = 1
        return messages + [{"role": "assistant", "content": "Final Answer: changed req"}], "normal"

    with patch.object(react_loop, "run_react_agent_impl", side_effect=fake_run_react_agent_impl):
        response = TestClient(agent_server.create_app()).post("/run", json={
            "ip": ip,
            "project_root": str(project_root),
            "session": session_name,
            "sync": True,
            "task": "attempt locked truth mutation",
            "workflow": "rtl-gen",
        })

    payload = response.json()
    assert response.status_code == 200, response.text
    assert payload["status"] == "error"
    assert "locked truth modified and restored" in payload["error"]
    assert payload["locked_truth_modified"] == [f"{ip}/req/{ip}_requirements.md"]
    assert req_file.read_text(encoding="utf-8") == "locked requirement\n"
    assert not (source_root / ip / "req" / f"{ip}_requirements.md").exists()
