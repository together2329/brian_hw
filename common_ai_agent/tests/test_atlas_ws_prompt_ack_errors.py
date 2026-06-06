import sys
import json
from pathlib import Path

from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))


def _register(client: TestClient, username: str) -> None:
    response = client.post(
        "/api/auth/register",
        json={"username": username, "password": "pw"},
    )
    assert response.status_code == 200, response.text


def _write_approval_manifest(project_root: Path, ip: str, *, status: str = "approved") -> None:
    manifest = project_root / ip / "req" / "approval_manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(json.dumps({"status": status}), encoding="utf-8")


def test_locked_truth_draft_overlay_wraps_unapproved_ip(tmp_path):
    import src.atlas_ui as atlas_ui

    ip = "mctp_draft"
    (tmp_path / ip).mkdir()

    wrapped, applied = atlas_ui._apply_locked_truth_draft_overlay(
        tmp_path,
        f"alice/default/{ip}/default",
        {"ip": ip},
        "I want req -> obligation -> contract -> evidence flow to make mctp rtl",
    )

    assert applied is True
    assert wrapped.startswith("[ATLAS LOCKED TRUTH DRAFT MODE]")
    assert "Do not run workflow stages." in wrapped
    assert "Lock truth per requirement" in wrapped
    assert "every required requirement is locked or approved" in wrapped
    assert "Prefer short tiktaka" in wrapped
    assert "Prefer normal chat for one or two missing decisions" in wrapped
    assert "Ask one concise natural-language question at a time" in wrapped
    assert "Ask only for lock-blocking ambiguity" in wrapped
    assert "Do not ask optional refinement questions" in wrapped
    assert "If enough information exists, stop interviewing" in wrapped
    assert "If 3 or more lock-blocking decisions remain" in wrapped
    assert "Do not launch ask_user automatically" in wrapped
    assert "Use ask_user only for grill-me/deep-interview" in wrapped
    assert "batched structured decisions" in wrapped
    assert "Do not leave lock-blocking open questions as a prose list" in wrapped
    assert "Existing RTL/doc/SSOT artifacts are read-only candidate evidence" in wrapped
    assert "Do not mark a legacy-derived requirement locked" in wrapped
    assert "/draft-req" in wrapped
    assert "/finalize-req" in wrapped
    assert "ready_for_human_review, not locked" in wrapped
    assert "/lock-req" in wrapped
    assert "lock_requirement_set.py" in wrapped
    assert "check_locked_truth_bundle.py" in wrapped
    assert "Do not say approved or locked unless" in wrapped
    assert "req/locked_truth.md" in wrapped
    assert "req/approval_manifest.json" in wrapped
    assert "After ask_user answers, do not dump the full draft" in wrapped
    assert "Produce only:" not in wrapped
    assert "[USER MESSAGE]" in wrapped
    assert "req -> obligation" in wrapped


def test_locked_truth_draft_overlay_skips_approved_ip(tmp_path):
    import src.atlas_ui as atlas_ui

    ip = "mctp_locked"
    _write_approval_manifest(tmp_path, ip, status="approved")

    wrapped, applied = atlas_ui._apply_locked_truth_draft_overlay(
        tmp_path,
        f"alice/default/{ip}/default",
        {"ip": ip},
        "Implement the RTL now",
    )

    assert applied is False
    assert wrapped == "Implement the RTL now"


def test_locked_truth_draft_overlay_skips_approved_ip_in_session_workspace(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    ip = "timer_new_concept"
    monkeypatch.setenv("ATLAS_ROOT", str(tmp_path))
    workspace_root = tmp_path / "brian" / "brian_session"
    _write_approval_manifest(workspace_root, ip, status="approved")

    wrapped, applied = atlas_ui._apply_locked_truth_draft_overlay(
        tmp_path,
        f"brian/brian_session/{ip}/default",
        {"ip": ip},
        "Generate RTL from SSOT",
    )

    assert applied is False
    assert wrapped == "Generate RTL from SSOT"


def test_locked_truth_draft_overlay_skips_slash_command(tmp_path):
    import src.atlas_ui as atlas_ui

    ip = "mctp_draft"
    (tmp_path / ip).mkdir()

    wrapped, applied = atlas_ui._apply_locked_truth_draft_overlay(
        tmp_path,
        f"alice/default/{ip}/default",
        {"ip": ip},
        "/verify-ssot",
    )

    assert applied is False
    assert wrapped == "/verify-ssot"


def test_api_commands_includes_default_req_lifecycle_commands(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()
    client = TestClient(app)
    _register(client, "alice")
    response = client.get("/api/commands")
    assert response.status_code == 200, response.text
    commands = response.json()["commands"]
    by_name = {cmd.get("name"): cmd for cmd in commands}

    assert by_name["draft-req"]["cmd"] == "/draft-req"
    assert by_name["finalize-req"]["cmd"] == "/finalize-req"
    assert "locked-truth-finalize" in by_name["finalize-req"]["aliases"]
    assert by_name["lock-req"]["cmd"] == "/lock-req"
    assert "truth-lock" in by_name["lock-req"]["aliases"]
    assert "lock-truth" in by_name["lock-req"]["aliases"]


def test_prompt_forbidden_session_returns_delivery_ack(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "SOURCE_ROOT", tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()
    client = TestClient(app)
    _register(client, "alice")

    with client.websocket_connect("/ws/agent?session_id=alice/default/default") as ws:
        assert ws.receive_json()["type"] == "hello"
        ws.send_json({
            "type": "prompt",
            "session": "bob/ip_alpha/rtl-gen",
            "text": "Hi",
            "msg_id": "forbidden-target",
            "ip": "ip_alpha",
            "workflow": "rtl-gen",
        })
        accepted = ws.receive_json()

    assert accepted["type"] == "agent_accepted"
    assert accepted["msg_id"] == "forbidden-target"
    assert accepted["ok"] is False
    assert "invalid or forbidden session" in accepted["error"]
