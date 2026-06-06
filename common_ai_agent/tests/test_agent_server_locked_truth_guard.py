from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from typing import List, Union
from unittest.mock import patch

from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))


ManifestRequirement = dict[str, Union[str, bool]]
ManifestPayload = dict[str, Union[str, List[ManifestRequirement]]]


def _write_guard_manifest(ip_dir: Path, payload: ManifestPayload) -> Path:
    manifest = ip_dir / "req" / "approval_manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    return manifest


def test_requirement_manifest_stays_unlocked_until_all_required_items_lock(tmp_path: Path) -> None:
    locked_truth_guard = importlib.import_module("core.locked_truth_guard")

    project_root = tmp_path
    ip = "mctp"
    ip_dir = project_root / ip
    req_file = ip_dir / "req" / f"{ip}_requirements.md"
    requirements_index = ip_dir / "req" / "requirements_index.json"
    req_file.parent.mkdir(parents=True)
    req_file.write_text("draft requirements\n", encoding="utf-8")
    requirements_index.write_text("{}\n", encoding="utf-8")

    _write_guard_manifest(ip_dir, {
        "requirements": [
            {"id": "REQ_MCTP_HEADER", "status": "locked", "required": True},
            {"id": "REQ_MCTP_PAYLOAD", "status": "pending", "required": True},
        ],
    })

    assert locked_truth_guard.is_locked_truth_active(project_root, ip) is False
    assert locked_truth_guard.locked_truth_write_error(project_root, ip, str(req_file)) is None

    _write_guard_manifest(ip_dir, {
        "requirements": [
            {"id": "REQ_MCTP_HEADER", "status": "locked", "required": True},
            {"id": "REQ_MCTP_PAYLOAD", "status": "locked", "required": True},
        ],
    })

    assert locked_truth_guard.is_locked_truth_active(project_root, ip) is True
    error = locked_truth_guard.locked_truth_write_error(project_root, ip, str(req_file))
    assert error is not None
    assert "locked truth is approved" in error
    json_error = locked_truth_guard.locked_truth_write_error(project_root, ip, str(requirements_index))
    assert json_error is not None
    assert "requirements_index.json" in json_error


def test_requirement_manifest_ignores_optional_unlocked_items(tmp_path: Path) -> None:
    locked_truth_guard = importlib.import_module("core.locked_truth_guard")

    project_root = tmp_path
    ip = "timer"
    ip_dir = project_root / ip
    _write_guard_manifest(ip_dir, {
        "requirements": [
            {"id": "REQ_TIMER_COUNT", "status": "approved", "required": True},
            {"id": "REQ_TIMER_INTERRUPT", "status": "pending", "required": False},
        ],
    })

    assert locked_truth_guard.is_locked_truth_active(project_root, ip) is True


def test_requirement_manifest_status_does_not_lock_pending_required_items(tmp_path: Path) -> None:
    locked_truth_guard = importlib.import_module("core.locked_truth_guard")

    project_root = tmp_path
    ip = "timer"
    ip_dir = project_root / ip
    _write_guard_manifest(ip_dir, {
        "status": "requirements_locked",
        "requirements": [
            {"id": "REQ_TIMER_COUNT", "status": "locked", "required": True},
            {"id": "REQ_TIMER_IRQ", "status": "pending", "required": True},
        ],
    })

    assert locked_truth_guard.is_locked_truth_active(project_root, ip) is False


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
