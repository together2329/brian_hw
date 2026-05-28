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
# Cluster files extracted from workspace.jsx by refactor/atlas-modular:
#   Phase 13a → ssot-doc.jsx   (SsotDocPane)
#   Phase 13b → workflow-report.jsx
#   Phase 13c → ssot-digest.jsx (DigestCard, BlockDiagram, SsotDigestContent,
#                                SsotReviewPane — ~2023 lines)
#   Phase 13d → preview-pane.jsx (PreviewPane, FoldablePane,
#                                 DeferredMarkdownPreview — ~671 lines)
#   Phase 13f → ssot-qa-board.jsx (SsotQaBoard — ~1691 lines)
# Many source-grep tests below now read the union so moved strings still match.
SSOT_DIGEST_JSX = ROOT / "frontend" / "atlas" / "ssot-digest.jsx"
PREVIEW_PANE_JSX = ROOT / "frontend" / "atlas" / "preview-pane.jsx"
SSOT_QA_BOARD_JSX = ROOT / "frontend" / "atlas" / "ssot-qa-board.jsx"
# Phase 21/22/23 splits — formerly in ssot-digest.jsx / workspace-panels.jsx
SSOT_DIGEST_CONTENT_JSX = ROOT / "frontend" / "atlas" / "ssot-digest-content.jsx"
SSOT_REVIEW_JSX = ROOT / "frontend" / "atlas" / "ssot-review.jsx"
BLOCK_DIAGRAM_JSX = ROOT / "frontend" / "atlas" / "block-diagram.jsx"
WORKSPACE_PANELS_JSX = ROOT / "frontend" / "atlas" / "workspace-panels.jsx"
PROGRESS_TODO_PANELS_JSX = ROOT / "frontend" / "atlas" / "progress-todo-panels.jsx"
AGENT_STATUS_PANEL_JSX = ROOT / "frontend" / "atlas" / "agent-status-panel.jsx"


def _all_workspace_jsx() -> str:
    """workspace.jsx + every Phase 13/18/19/21/22/23 cluster file
    concatenated, for greps that don't care which file a moved string
    ended up in. Add to the tuple whenever a new cluster gets split out."""
    return "\n".join(
        p.read_text(encoding="utf-8")
        for p in (
            WORKSPACE_JSX,
            SSOT_DIGEST_JSX,
            SSOT_DIGEST_CONTENT_JSX,
            SSOT_REVIEW_JSX,
            BLOCK_DIAGRAM_JSX,
            PREVIEW_PANE_JSX,
            SSOT_QA_BOARD_JSX,
            WORKSPACE_PANELS_JSX,
            PROGRESS_TODO_PANELS_JSX,
            AGENT_STATUS_PANEL_JSX,
        )
        if p.exists()
    )
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


def _receive_slash_output(ws, marker: str) -> str:
    for _ in range(20):
        msg = ws.receive_json()
        text = str(msg.get("text") or "")
        if msg.get("type") == "slash_output" and marker in text:
            return text
    raise AssertionError(f"did not receive slash_output containing {marker!r}")


def test_ssot_qa_workbench_has_first_class_actions_and_no_history_panel():
    # SsotQaBoard moved to ssot-qa-board.jsx by Phase 13f. The board-internal
    # action strings (validate / import / grill-me / to-ssot) live there now;
    # the parent mount points (Q&A Session label, fullHeight prop) stay in
    # workspace.jsx (still in the surrounding Workspace component).
    src = WORKSPACE_JSX.read_text(encoding="utf-8")
    combined = _all_workspace_jsx()

    assert "Q&amp;A Session" in src
    assert "fullHeight={true}" in src
    assert "/api/ssot/import/upload" in combined
    assert "/api/ssot/validate" in combined
    assert "check_ssot_disk.sh" in combined
    assert "verify_ssot.py" in combined
    assert "runSsotCommand(`/grill-me ${data.ip}`)" in combined
    assert "runSsotCommand(`/to-ssot ${data.ip}`)" in combined
    assert "Validation" in combined
    assert "Import / Export" in combined
    assert "checklistOnly={true}" in src
    assert "importExportOnly={true}" in src
    # Locale UI strings + 3-step flow markers + Q&A readouts all moved into
    # SsotQaBoard's own render → ssot-qa-board.jsx.
    assert "무엇을 만들까?" in combined
    assert "Q&A 카드" in combined
    assert "Q&A readiness" in combined
    assert "Q&A 준비 상태" in combined
    assert "채워야 하는 9칸" not in combined
    assert "Answer Percent" not in combined
    assert "SSOT 3단계 흐름" in combined
    assert "2. Deep Interview" in combined
    assert "3. To SSOT" in combined
    assert "QaHistoryPanel history={visibleQaHistory}" not in combined
    assert "ADD_DATA_URI_TAGS: ['img']" in src
    assert "_sanitizePrismLanguageClasses(node)" in src
    assert "/^data[:;]/i.test(lang)" in src
    assert "const files = Array.from(ev.target.files || []);" in combined
    # The two SsotDigestContent file-input handlers moved to ssot-digest.jsx
    # in Phase 13c; count across workspace + cluster files.
    assert _all_workspace_jsx().count("const files = Array.from(e.target.files || []);") >= 2


def test_ssot_preview_uses_fresh_yaml_without_llm_narrator():
    workspace_src = WORKSPACE_JSX.read_text(encoding="utf-8")
    data_src = DATA_JSX.read_text(encoding="utf-8")
    atlas_ui_src = ATLAS_UI_PY.read_text(encoding="utf-8")
    # meta.mtime/size readouts live in SsotDigestContent → ssot-digest.jsx
    # since Phase 13c.
    combined = _all_workspace_jsx()

    assert "NarratorBanner" not in workspace_src
    assert "/api/ssot/narrate" not in workspace_src
    assert "api_ssot_narrate" not in atlas_ui_src
    assert "caller_tag=\"ssot-narrate\"" not in atlas_ui_src
    assert 'data-role="tool-count"' not in workspace_src
    assert "fetch('/api/ssot', { cache: 'no-store' })" in data_src
    assert "meta.mtime || 0" in combined
    assert "meta.size || 0" in combined


def test_ssot_preview_ignores_yaml_hash_comments_in_digest_parser():
    workspace_src = WORKSPACE_JSX.read_text(encoding="utf-8")

    assert "const stripSsotYamlComment = (line) =>" in workspace_src
    assert "const ssotPreviewLines = (text)" in workspace_src
    assert "const lines = ssotPreviewLines(content);" in workspace_src
    assert "const lines = ssotPreviewLines(section.text);" in workspace_src
    assert "const lines = ssotPreviewLines(text);" in workspace_src
    assert "let text = stripSsotYamlComment(value).trim();" in workspace_src
    assert "ch === '#' && !single && !double" in workspace_src


def test_ssot_preview_attention_status_uses_bang_glyph():
    workspace_src = WORKSPACE_JSX.read_text(encoding="utf-8")
    # statusForPresence + the glyph render site moved into SsotDigestContent /
    # SsotReviewPane (ssot-digest.jsx) in Phase 13c; the status-helper consts
    # ssotNeedsAttentionStatus/ssotStatusGlyph still live in workspace.jsx.
    combined = _all_workspace_jsx()

    assert "const ssotNeedsAttentionStatus = (status) =>" in workspace_src
    assert "const ssotStatusGlyph = (status) =>" in workspace_src
    assert "const statusForPresence = (present) => present ? 'approved' : 'needs_review';" in combined
    assert "statuses.some(ssotNeedsAttentionStatus)" in combined
    assert "{ssotStatusGlyph(status)}" in combined


def test_fsm_graph_defaults_to_native_renderer_not_mermaid():
    workspace_src = WORKSPACE_JSX.read_text(encoding="utf-8")
    graph_branch = workspace_src[workspace_src.index("{mode === 'graph' ? ("):workspace_src.index("{mode === 'mermaid' ? (")]

    assert "<FsmLayeredSvgDiagram graph={graph} diagramId={diagramId} />" in graph_branch
    assert "<MermaidFsmGraph" not in graph_branch
    assert "<code>{mermaidCode}</code>" in workspace_src


def test_preview_feedback_controls_are_mode_gated():
    # Spread across three files now:
    #   - PreviewPane component (feedbackMode default + overlay) → preview-pane.jsx (13d)
    #   - SsotDigestContent / SsotReviewPane parents (previewMode + ssotPreviewMode
    #     state + caller-site feedbackMode={…} props) → ssot-digest.jsx (13c)
    # workspace.jsx may still hold sibling state. Grep all three.
    combined = _all_workspace_jsx()

    assert "feedbackMode = false" in combined
    assert "feedbackMode && floating" in combined
    assert "const [previewMode, setPreviewMode] = React.useState('view');" in combined
    assert "const [ssotPreviewMode, setSsotPreviewMode] = React.useState('view');" in combined
    assert "feedbackMode={previewMode === 'feedback'}" in combined
    assert "feedbackMode={ssotPreviewMode === 'feedback'}" in combined


def test_import_to_ssot_uses_manifest_and_split_roots():
    atlas_ui_src = ATLAS_UI_PY.read_text(encoding="utf-8")
    # Phase 12 refactor: slash handlers (_handle_to_ssot_gate,
    # _handle_repair_ssot_command, _handle_import_command, …) moved to
    # src/atlas_slash_handlers.py — read source from there now.
    slash_src = ATLAS_UI_PY.with_name("atlas_slash_handlers.py").read_text(encoding="utf-8")
    gate_start = slash_src.index("def _handle_to_ssot_gate")
    gate_end = slash_src.index("def _handle_repair_ssot_command", gate_start)
    gate_src = slash_src[gate_start:gate_end]
    import_start = slash_src.index("def _handle_import_command")
    import_end = slash_src.index("def _handle_grill_me_command", import_start)
    import_src = slash_src[import_start:import_end]
    spec_start = atlas_ui_src.index("def _render_approved_ssot_spec")
    spec_end = atlas_ui_src.index("def _emit_ssot_approval_ready", spec_start)
    spec_src = atlas_ui_src[spec_start:spec_end]
    qna_start = atlas_ui_src.index("def _render_ssot_llm_qna_prompt")
    qna_end = atlas_ui_src.index("def _render_approved_ssot_spec", qna_start)
    qna_src = atlas_ui_src[qna_start:qna_end]

    assert "import_manifest.json" in import_src
    assert "extracted_decisions.json" in import_src
    assert "import-llm-queued" not in import_src
    assert "import_manifest.json" in gate_src
    assert "extracted_decisions.json" in gate_src
    assert "blocked: import evidence index is incomplete" in gate_src
    assert "blocked: {ip} still has missing SSOT decisions" in gate_src
    assert "`{ip}/req/imports/`" in gate_src
    assert "ATLAS_WORKFLOW_ROOT" in gate_src
    assert "ATLAS_PROJECT_ROOT" in gate_src
    assert "--root {script_root}" in gate_src
    assert "{ip}/wiki/import-evidence.md" in spec_src
    assert "import_manifest.json" in qna_src
    assert "`{ip}/req/imports/`" in qna_src
    # CLI flag definitions live in src/atlas_runtime.py post Phase-4 refactor;
    # accept either location so the assertion tracks intent (the flags are wired
    # somewhere in the server-side codebase) rather than the file boundary.
    runtime_src = ATLAS_UI_PY.with_name("atlas_runtime.py").read_text(encoding="utf-8")
    assert "--workflow-root" in atlas_ui_src or "--workflow-root" in runtime_src
    assert "--ip-root" in atlas_ui_src or "--ip-root" in runtime_src

    for path in (TO_SSOT_SKILL, SSOT_SYSTEM_PROMPT, COMMON_ENGINE_FLOW):
        src = path.read_text(encoding="utf-8")
        assert "import_manifest.json" in src
        assert "ATLAS_WORKFLOW_ROOT" in src


def test_to_ssot_preview_and_verify_share_canonical_format_contract():
    workspace_src = WORKSPACE_JSX.read_text(encoding="utf-8")
    atlas_ui_src = ATLAS_UI_PY.read_text(encoding="utf-8")
    skill_src = TO_SSOT_SKILL.read_text(encoding="utf-8")
    system_prompt_src = SSOT_SYSTEM_PROMPT.read_text(encoding="utf-8")
    tools_src = CORE_TOOLS_PY.read_text(encoding="utf-8")
    schema_src = TOOL_SCHEMA_PY.read_text(encoding="utf-8")
    command_src = VERIFY_SSOT_COMMAND.read_text(encoding="utf-8")

    # Phase 12 refactor: gate handler moved to atlas_slash_handlers.py.
    slash_src = ATLAS_UI_PY.with_name("atlas_slash_handlers.py").read_text(encoding="utf-8")
    gate_start = slash_src.index("def _handle_to_ssot_gate")
    gate_end = slash_src.index("def _handle_repair_ssot_command", gate_start)
    gate_src = slash_src[gate_start:gate_end]

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
    assert "verify_ssot.py" in gate_src
    assert "--root {script_root}" in gate_src
    assert 'verify_ssot.py" <ip> --root "$ATLAS_PROJECT_ROOT" --mode engineering' in skill_src
    assert 'verify_ssot.py" <ip> --root "$ATLAS_PROJECT_ROOT" --mode engineering' in system_prompt_src
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
    # Policy banners ride inside SsotDigestContent, which moved from
    # ssot-digest.jsx → ssot-digest-content.jsx in Phase 22. Use the
    # full combined-source helper so we don't have to chase each split.
    ws_plus_digest = _all_workspace_jsx()
    assert "explicit no-register policy" in ws_plus_digest
    assert "explicit no-FSM policy" in ws_plus_digest
    assert "const interfaceFromBlock = (block" in workspace_src
    assert "const mapBlocksFromText = (text, parentKey = '') =>" in workspace_src
    assert "...mapBlocksFromSection(section, key)" in workspace_src
    assert "scalarInterfaceFromSection(section, key, fallbackName)" in workspace_src
    assert "nestedFieldFromText(block?.text, 'busType', 'name')" in workspace_src
    assert "block?.mapKey || blockField(block, 'name')" in workspace_src
    assert "interfaceFromBlock(block, ssotTitleFor(section.key), 'bus')" in workspace_src
    assert "Quickstart" not in workspace_src
    assert "quickstartSteps" not in workspace_src
    # Register render config + meaningfulFields filter + RegisterBitFieldView
    # mount are inside SsotDigestContent → ssot-digest.jsx (Phase 13c).
    assert "const registerConfig = {" in ws_plus_digest
    assert "const meaningfulFields = (reg.fields || []).filter(_hasMeaningfulRegisterField);" in ws_plus_digest
    assert "<RegisterBitFieldView" in ws_plus_digest
    assert "gridTemplateColumns: '82px minmax(0, 1fr) auto'" in workspace_src


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


def test_ssot_validate_api_runs_verifier_from_project_root(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "0")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    ip = "mini_validate_ip"
    ssot_path = tmp_path / ip / "yaml" / f"{ip}.ssot.yaml"
    ssot_path.parent.mkdir(parents=True)
    ssot_path.write_text(
        """
top_module:
  name: mini_validate_ip
  description: "Small preview-readable starter SSOT used by the API validation regression test."
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

    client = TestClient(atlas_ui.create_app())
    _register(client)
    response = client.post("/api/ssot/validate", json={"ip": ip, "mode": "starter"})

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["ok"] is True
    assert payload["mode"] == "starter"
    assert "verify_ssot.py" in payload["command"]
    assert f"--root {tmp_path}" in payload["command"]
    assert "[verify_ssot] PASS" in payload["stdout"]


def test_ssot_validate_api_infers_ip_when_project_root_is_ip_root(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    ip = "rooted_validate_ip"
    ip_root = tmp_path / ip
    ip_root.mkdir()
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "0")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(ip_root)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", ip_root)

    ssot_path = ip_root / "yaml" / f"{ip}.ssot.yaml"
    ssot_path.parent.mkdir(parents=True)
    ssot_path.write_text(
        """
top_module:
  name: rooted_validate_ip
  description: "Starter SSOT under an IP root rather than a project root."
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

    client = TestClient(atlas_ui.create_app())
    _register(client, username="rooted")
    response = client.post("/api/ssot/validate", json={"mode": "starter"})

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["ok"] is True
    assert payload["ip"] == ip
    assert f"--root {ip_root}" in payload["command"]


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


def test_ssot_qa_api_does_not_seed_default_required_decisions(tmp_path, monkeypatch):
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
    assert requirements["total"] == 0
    assert requirements["filled"] == 0
    assert requirements["missing"] == 0
    assert requirements["items"] == []
    assert "register_map" not in requirements["missing_keys"]


def test_new_ip_tbd_scaffold_does_not_fill_ssot_answer_percent(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "0")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    ip = "empty_axi"
    client = TestClient(atlas_ui.create_app())
    _register(client, username="qa_user")

    with client.websocket_connect(f"/ws/agent?session_id=qa_user/{ip}/ssot-gen") as ws:
        assert ws.receive_json()["type"] == "hello"
        ws.send_json({"type": "prompt", "text": f"/new-ip {ip}"})
        plan = _receive_slash_output(ws, "[SSOT PLAN]")

    assert "- · `purpose`" in plan
    assert "missing decisions: purpose" in plan

    response = client.get(f"/api/ssot/qa?ip={ip}")
    assert response.status_code == 200, response.text
    requirements = response.json()["requirements"]
    assert requirements["total"] == 0
    assert requirements["filled"] == 0
    assert requirements["missing"] == 0
    assert requirements["missing_keys"] == []


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
    assert "![diagram](images/" in saved_text
    assert "data:image/png;base64" not in saved_text
    assert "data:image/png:base64" not in saved_text
    image_refs = [part.split(")", 1)[0] for part in saved_text.split("](")[1:]]
    assert image_refs
    for rel in image_refs:
        assert (saved.parent / rel).is_file()


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
