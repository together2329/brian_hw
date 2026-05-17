import json
import base64
import sys
from pathlib import Path

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

WORKSPACE_JSX = ROOT / "frontend" / "atlas" / "workspace.jsx"


def _register(client: TestClient, username: str = "alice") -> None:
    response = client.post(
        "/api/auth/register",
        json={"username": username, "password": "pw"},
    )
    assert response.status_code == 200, response.text


def test_ssot_qa_workbench_has_first_class_actions_and_no_history_panel():
    src = WORKSPACE_JSX.read_text(encoding="utf-8")

    assert "Q&amp;A Session" in src
    assert "fullHeight={true}" in src
    assert "/api/ssot/import/upload" in src
    assert "runSsotCommand(`/grill-me ${data.ip}`)" in src
    assert "runSsotCommand(`/to-ssot ${data.ip}`)" in src
    assert "Check List" in src
    assert "checklistOnly={true}" in src
    assert "무엇을 만들까?" in src
    assert "채워야 하는 9칸" in src
    assert "RTL 생성 준비도" in src
    assert "1. 새로 원하는 것 = Chat" in src
    assert "2. 이미 가진 문서 = Import" in src
    assert "3. 모르는 것 = Deep Interview" in src
    assert "4. 약속장 만들기 = To SSOT" in src
    assert "QaHistoryPanel history={visibleQaHistory}" not in src


def test_ssot_qa_api_reports_remaining_required_decisions(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "0")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    ip = "mctp_assembler"
    state_dir = tmp_path / ".session" / "default" / ip / "ssot-gen"
    state_dir.mkdir(parents=True)
    (state_dir / "state.json").write_text(
        json.dumps(
            {
                "ip": ip,
                "kind": "MCTP packet assembler",
                "decisions": {
                    "purpose": "Assemble MCTP packets from PCIe VDM payloads.",
                    "bus_interface": "AXI slave data path plus APB control.",
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    client = TestClient(atlas_ui.create_app())
    _register(client)
    response = client.get(f"/api/ssot/qa?ip={ip}")

    assert response.status_code == 200, response.text
    requirements = response.json()["requirements"]
    assert requirements["total"] >= 9
    assert requirements["filled"] == 2
    assert requirements["missing"] == requirements["total"] - 2
    assert "register_map" in requirements["missing_keys"]


def test_ssot_import_upload_saves_attachment_and_returns_import_command(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "0")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    client = TestClient(atlas_ui.create_app())
    _register(client)
    content = b"# MCTP\n\nAXI slave data path plus APB control registers.\n"
    response = client.post(
        "/api/ssot/import/upload",
        json={
            "ip": "mctp_assembler",
            "session": "default/mctp_assembler/ssot-gen",
            "files": [
                {
                    "name": "mctp requirements.md",
                    "content_b64": base64.b64encode(content).decode("ascii"),
                }
            ],
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["ok"] is True
    assert payload["ip"] == "mctp_assembler"
    assert payload["paths"][0].startswith("mctp_assembler/req/imports/")
    assert payload["command"].startswith("/import --ip mctp_assembler @mctp_assembler/req/imports/")
    saved = tmp_path / payload["paths"][0]
    assert saved.is_file()
    assert "AXI slave" in saved.read_text(encoding="utf-8")
