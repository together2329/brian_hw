import json
import base64
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

WORKSPACE_JSX = ROOT / "frontend" / "atlas" / "workspace.jsx"
DATA_JSX = ROOT / "frontend" / "atlas" / "data.jsx"
ATLAS_UI_PY = ROOT / "src" / "atlas_ui.py"
CORE_TOOLS_PY = ROOT / "core" / "tools.py"
TOOL_SCHEMA_PY = ROOT / "core" / "tool_schema.py"
TO_SSOT_SKILL = ROOT / "workflow" / "ssot-gen" / "skills" / "to-ssot" / "SKILL.md"
SSOT_SYSTEM_PROMPT = ROOT / "workflow" / "ssot-gen" / "system_prompt.md"
COMMON_ENGINE_FLOW = ROOT / "workflow" / "COMMON_ENGINE_FLOW.md"
VERIFY_SSOT_SCRIPT = ROOT / "workflow" / "ssot-gen" / "scripts" / "verify_ssot.py"
VERIFY_SSOT_COMMAND = ROOT / "workflow" / "ssot-gen" / "commands" / "verify-ssot.json"


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
    assert "/api/ssot/validate" in src
    assert "check_ssot_disk.sh" in src
    assert "runSsotCommand(`/grill-me ${data.ip}`)" in src
    assert "runSsotCommand(`/to-ssot ${data.ip}`)" in src
    assert "Validation" in src
    assert "Import / Export" in src
    assert "checklistOnly={true}" in src
    assert "importExportOnly={true}" in src
    assert "무엇을 만들까?" in src
    assert "채워야 하는 9칸" in src
    assert "SSOT Percent" in src
    assert "SSOT 3단계 흐름" in src
    assert "2. Deep Interview" in src
    assert "3. To SSOT" in src
    assert "QaHistoryPanel history={visibleQaHistory}" not in src


def test_ssot_preview_uses_fresh_yaml_without_llm_narrator():
    workspace_src = WORKSPACE_JSX.read_text(encoding="utf-8")
    data_src = DATA_JSX.read_text(encoding="utf-8")
    atlas_ui_src = ATLAS_UI_PY.read_text(encoding="utf-8")

    assert "NarratorBanner" not in workspace_src
    assert "/api/ssot/narrate" not in workspace_src
    assert "api_ssot_narrate" not in atlas_ui_src
    assert "caller_tag=\"ssot-narrate\"" not in atlas_ui_src
    assert 'data-role="tool-count"' not in workspace_src
    assert "fetch('/api/ssot', { cache: 'no-store' })" in data_src
    assert "meta.mtime || 0" in workspace_src
    assert "meta.size || 0" in workspace_src


def test_ssot_preview_ignores_yaml_hash_comments_in_digest_parser():
    workspace_src = WORKSPACE_JSX.read_text(encoding="utf-8")

    assert "const stripSsotYamlComment = (line) =>" in workspace_src
    assert "const ssotPreviewLines = (text)" in workspace_src
    assert "const lines = ssotPreviewLines(content);" in workspace_src
    assert "const lines = ssotPreviewLines(section.text);" in workspace_src
    assert "const lines = ssotPreviewLines(text);" in workspace_src
    assert "let text = stripSsotYamlComment(value).trim();" in workspace_src
    assert "ch === '#' && !single && !double" in workspace_src


def test_to_ssot_no_longer_reads_retired_import_manifest():
    atlas_ui_src = ATLAS_UI_PY.read_text(encoding="utf-8")
    gate_start = atlas_ui_src.index("def _handle_to_ssot_gate")
    gate_end = atlas_ui_src.index("def _handle_repair_ssot_command", gate_start)
    gate_src = atlas_ui_src[gate_start:gate_end]
    spec_start = atlas_ui_src.index("def _render_approved_ssot_spec")
    spec_end = atlas_ui_src.index("def _emit_ssot_approval_ready", spec_start)
    spec_src = atlas_ui_src[spec_start:spec_end]
    qna_start = atlas_ui_src.index("def _render_ssot_llm_qna_prompt")
    qna_end = atlas_ui_src.index("def _render_approved_ssot_spec", qna_start)
    qna_src = atlas_ui_src[qna_start:qna_end]

    assert "import_manifest.json" not in gate_src
    assert "import_manifest.json" not in spec_src
    assert "import_manifest.json" not in qna_src
    assert "`{ip}/req/imports/`" in gate_src
    assert "{ip}/wiki/import-evidence.md" in spec_src
    assert "`{ip}/req/imports/`" in qna_src

    for path in (TO_SSOT_SKILL, SSOT_SYSTEM_PROMPT, COMMON_ENGINE_FLOW):
        src = path.read_text(encoding="utf-8")
        assert "import_manifest.json" not in src


def test_to_ssot_preview_and_verify_share_canonical_format_contract():
    workspace_src = WORKSPACE_JSX.read_text(encoding="utf-8")
    atlas_ui_src = ATLAS_UI_PY.read_text(encoding="utf-8")
    skill_src = TO_SSOT_SKILL.read_text(encoding="utf-8")
    system_prompt_src = SSOT_SYSTEM_PROMPT.read_text(encoding="utf-8")
    tools_src = CORE_TOOLS_PY.read_text(encoding="utf-8")
    schema_src = TOOL_SCHEMA_PY.read_text(encoding="utf-8")
    command_src = VERIFY_SSOT_COMMAND.read_text(encoding="utf-8")

    gate_start = atlas_ui_src.index("def _handle_to_ssot_gate")
    gate_end = atlas_ui_src.index("def _handle_repair_ssot_command", gate_start)
    gate_src = atlas_ui_src[gate_start:gate_end]

    canonical_keys = (
        "top_module",
        "sub_modules",
        "decomposition",
        "rtl_contract",
        "io_list",
        "function_model",
        "cycle_model",
        "error_handling",
        "debug_observability",
        "test_requirements",
        "quality_gates",
        "workflow_todos",
        "generation_flow",
    )
    for key in canonical_keys:
        assert key in gate_src
        assert key in skill_src

    assert "Do NOT wrap the document in `ssot:`" in gate_src
    assert "Do NOT use legacy aliases" in gate_src
    assert "verify_ssot.py {ip} --mode engineering" in gate_src
    assert "verify_ssot.py <ip> --mode engineering" in skill_src
    assert "verify_ssot.py <ip> --mode engineering" in system_prompt_src
    assert "verify_ssot" in command_src
    assert '"verify_ssot": verify_ssot' in tools_src
    assert '"verify_ssot": _fn(' in schema_src

    assert "rtl_contract: 'RTL Contract'" in workspace_src
    assert "error_handling: 'Error Handling'" in workspace_src
    assert "debug_observability: 'Debug / Observability'" in workspace_src
    assert "test_requirements: 'Test Requirements'" in workspace_src
    assert "{ id: 'rtl_contract'" in workspace_src
    assert "{ id: 'verification'" in workspace_src
    assert "{ id: 'implementation'" in workspace_src
    assert "const testSection = sectionByKey(sections, 'test_requirements');" in workspace_src
    assert "...listBlocksFromSection(testSection, 'scenarios')" in workspace_src
    assert "explicit no-register policy" in workspace_src
    assert "explicit no-FSM policy" in workspace_src
    assert "const interfaceFromBlock = (block" in workspace_src
    assert "listBlocksFromSection(section, 'bus_interfaces')" in workspace_src
    assert "listBlocksFromSection(section, 'bus_interface')" in workspace_src
    assert "listBlocksFromSection(section, 'busInterfaces')" in workspace_src
    assert "interfaceFromBlock(block, ssotTitleFor(section.key), 'bus')" in workspace_src


def test_verify_ssot_script_checks_preview_readable_starter_yaml(tmp_path):
    ip = "mini_preview_ip"
    ssot_path = tmp_path / ip / "yaml" / f"{ip}.ssot.yaml"
    ssot_path.parent.mkdir(parents=True)
    ssot_path.write_text(
        """
top_module:
  name: mini_preview_ip
  description: "Small preview-readable starter SSOT used by the verify_ssot regression test."
io_list:
  interfaces:
    - name: control
      type: custom
      ports:
        - { name: clk, direction: input, width: 1, description: clock }
        - { name: done, direction: output, width: 1, description: completion flag }
function_model:
  transactions:
    - id: FM_DONE
      name: completion
      outputs: [done]
""".strip()
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(VERIFY_SSOT_SCRIPT), ip, "--root", str(tmp_path), "--mode", "starter"],
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "[verify_ssot] PASS" in result.stdout
    report = json.loads((tmp_path / ip / "req" / "ssot_validation.json").read_text(encoding="utf-8"))
    assert report["ok"] is True
    assert report["blockers"] == []


def test_verify_ssot_script_rejects_wrapped_yaml(tmp_path):
    ip = "wrapped_ip"
    ssot_path = tmp_path / ip / "yaml" / f"{ip}.ssot.yaml"
    ssot_path.parent.mkdir(parents=True)
    ssot_path.write_text(
        """
ssot:
  top_module:
    name: wrapped_ip
    description: "Wrongly wrapped SSOT."
""".strip()
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(VERIFY_SSOT_SCRIPT),
            ip,
            "--root",
            str(tmp_path),
            "--mode",
            "starter",
            "--skip-disk-check",
        ],
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 1
    assert "Top-level wrapper key" in result.stdout
    report = json.loads((tmp_path / ip / "req" / "ssot_validation.json").read_text(encoding="utf-8"))
    assert any(item["id"] == "ssot.wrapper_key" for item in report["blockers"])


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


def test_ssot_import_upload_normalizes_markdown_image_data_uri(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "0")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    client = TestClient(atlas_ui.create_app())
    _register(client)
    content = b"![diagram](data:image/png:base64,iVBORw0KGgo=)\n"
    response = client.post(
        "/api/ssot/import/upload",
        json={
            "ip": "mctp_assembler",
            "files": [
                {
                    "name": "diagram.md",
                    "content_b64": base64.b64encode(content).decode("ascii"),
                }
            ],
        },
    )

    assert response.status_code == 200, response.text
    saved = tmp_path / response.json()["paths"][0]
    saved_text = saved.read_text(encoding="utf-8")
    assert "data:image/png;base64,iVBORw0KGgo=" in saved_text
    assert "data:image/png:base64" not in saved_text


def test_ssot_qa_sessions_list_does_not_parse_ssot_yaml(tmp_path, monkeypatch):
    import yaml
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "0")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    ip = "first_access_heavy"
    session_dir = tmp_path / ".session" / "default" / ip / "ssot-gen"
    session_dir.mkdir(parents=True)
    (session_dir / "state.json").write_text(
        json.dumps(
            {
                "ip": ip,
                "status": "draft",
                "approved": False,
                "updated_at": 1,
            }
        ),
        encoding="utf-8",
    )
    (session_dir / "qa.json").write_text(
        json.dumps(
            {
                "items": [
                    {"decision_key": "purpose", "status": "approved", "answer": "DMA engine."},
                    {"decision_key": "register_map", "status": "pending", "answer": ""},
                ]
            }
        ),
        encoding="utf-8",
    )
    ssot_path = tmp_path / ip / "yaml" / f"{ip}.ssot.yaml"
    ssot_path.parent.mkdir(parents=True)
    ssot_path.write_text("custom:\n  atlas_decisions:\n    purpose: should not be parsed\n", encoding="utf-8")

    class ParseForbidden(BaseException):
        pass

    def forbid_yaml_parse(*_args, **_kwargs):
        raise ParseForbidden("sessions list parsed the SSOT YAML")

    client = TestClient(atlas_ui.create_app())
    _register(client)
    monkeypatch.setattr(yaml, "safe_load", forbid_yaml_parse)

    response = client.get("/api/ssot/qa/sessions")

    assert response.status_code == 200, response.text
    row = next(item for item in response.json()["sessions"] if item["ip"] == ip)
    assert row["summary"] == {"total": 2, "approved": 1, "pending": 1}
    assert row["status"] == "draft"
