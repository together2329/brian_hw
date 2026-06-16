from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT_TSX = ROOT / "frontend" / "atlas" / "workspace-root.tsx"
WORKSPACE_DATA_HOOK_TSX = ROOT / "frontend" / "atlas" / "workspace-root-data-hook.tsx"
WORKSPACE_RAIL_TABS_TSX = ROOT / "frontend" / "atlas" / "workspace-rootui-rail-tabs.tsx"
SSOT_DOC_TSX = ROOT / "frontend" / "atlas" / "ssot-doc.tsx"
SSOT_DOC_FEEDBACK_API_TS = ROOT / "frontend" / "atlas" / "ssot-doc-feedback-api.ts"
SSOT_QA_BOARD_TSX = ROOT / "frontend" / "atlas" / "ssot-qa-board.tsx"


def _combined_doc_src() -> str:
    return (
        WORKSPACE_ROOT_TSX.read_text(encoding="utf-8")
        + "\n"
        + WORKSPACE_DATA_HOOK_TSX.read_text(encoding="utf-8")
        + "\n"
        + WORKSPACE_RAIL_TABS_TSX.read_text(encoding="utf-8")
        + "\n"
        + SSOT_DOC_TSX.read_text(encoding="utf-8")
        + "\n"
        + SSOT_DOC_FEEDBACK_API_TS.read_text(encoding="utf-8")
    )


def test_ssot_doc_tab_renders_inline_html_export():
    src = _combined_doc_src()

    assert "const SsotDocPane: any = " in src
    assert "data-testid=\"ssot-doc-frame\"" in src
    assert "format: 'html'" in src
    assert "inline: '1'" in src
    assert "mainTab === 'doc'" in src
    assert ">doc</span>" in src


def test_ssot_doc_tab_has_view_and_feedback_modes():
    src = _combined_doc_src()

    assert "const [docMode, setDocMode] = useState('view');" in src
    assert "View Mode" in src
    assert "Feedback Mode" in src
    assert "submitSsotDocFeedback" in src
    assert "setReloadKey(k => k + 1)" in src
    assert "docMode === 'feedback'" in src
    assert "feedbackPath" in src
    assert "feedbackComment" in src


def test_ssot_doc_feedback_mode_supports_drag_drop_comment_targeting():
    src = _combined_doc_src()

    assert "const docFrameRef = useRef<HTMLIFrameElement>(null);" in src
    assert "const [feedbackComment, setFeedbackComment] = useState('');" in src
    assert "const handleDocCommentDragStart = (ev: DragEvent<HTMLButtonElement>) =>" in src
    assert "draggable={docMode === 'feedback'}" in src
    assert "frameDoc.addEventListener('dragover', onDragOver);" in src
    assert "frameDoc.addEventListener('drop', onDrop);" in src
    assert "window.addEventListener('keydown', onKeyDown);" in src
    assert "buildSsotDocTargetFromElement" in src
    assert "markSsotDocSelection" in src
    assert "onLoad={() => setDocFrameReady(v => v + 1)}" in src


def test_ssot_doc_feedback_mode_exposes_source_and_chat_hooks():
    src = _combined_doc_src()

    assert "Show SSOT" in src
    assert "atlas-ssot-doc-comment" in src
    assert "/api/ssot/doc-source" in src
    assert "data-ssot-path" in src
    assert "selectedTarget" in src


def test_default_workflow_shows_ssot_import_export_tab():
    src = (
        WORKSPACE_DATA_HOOK_TSX.read_text(encoding="utf-8")
        + "\n"
        + WORKSPACE_RAIL_TABS_TSX.read_text(encoding="utf-8")
        + "\n"
        + WORKSPACE_ROOT_TSX.read_text(encoding="utf-8")
    )

    assert "const showSsotImportExportTab = !oagMode && (workflow === 'ssot-gen' || workflow === 'default');" in src
    assert ">Import / Export</span>" in src
    assert "importExportOnly={true}" in src


def test_to_ssot_button_uses_same_plain_mini_button_as_deep_interview():
    # The /to-ssot button render sites live in SsotQaBoard now → ssot-qa-board.jsx
    # (extracted in Phase 13f). The negative assertion (borderColor not set)
    # still applies across the union — if the highlighted-button style ever
    # leaks back into any workspace-cluster file, this catches it.
    src = WORKSPACE_ROOT_TSX.read_text(encoding="utf-8")
    qa_board_src = SSOT_QA_BOARD_TSX.read_text(encoding="utf-8")
    combined = src + "\n" + qa_board_src
    assert "borderColor: 'var(--ok)', color: 'var(--ok)'" not in combined
    assert "title=\"Run /to-ssot for this IP\"\n                  style={{ marginTop: 7 }}" in combined
    assert "onClick={() => runSsotCommand(`/to-ssot ${data!.ip}`)}" in combined
