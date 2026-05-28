from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_JSX = ROOT / "frontend" / "atlas" / "workspace.jsx"
# SsotDocPane was extracted from workspace.jsx into ssot-doc.jsx by Phase 13a
# of refactor/atlas-modular; the doc-tab pane logic + drag/drop handlers now
# live there. Tests below grep both files (the tab chip + mainTab routing
# stay in workspace.jsx; the pane internals live in ssot-doc.jsx).
SSOT_DOC_JSX = ROOT / "frontend" / "atlas" / "ssot-doc.jsx"


def _combined_doc_src() -> str:
    return (
        WORKSPACE_JSX.read_text(encoding="utf-8")
        + "\n"
        + SSOT_DOC_JSX.read_text(encoding="utf-8")
    )


def test_ssot_doc_tab_renders_inline_html_export():
    src = _combined_doc_src()

    assert "const SsotDocPane = " in src
    assert "data-testid=\"ssot-doc-frame\"" in src
    assert "format: 'html'" in src
    assert "inline: '1'" in src
    assert "mainTab === 'doc'" in src
    assert ">doc</span>" in src


def test_ssot_doc_tab_has_view_and_feedback_modes():
    src = _combined_doc_src()

    assert "const [docMode, setDocMode] = React.useState('view');" in src
    assert "View Mode" in src
    assert "Feedback Mode" in src
    assert "fetch('/api/ssot/doc-feedback'" in src
    assert "setReloadKey(k => k + 1)" in src
    assert "docMode === 'feedback'" in src
    assert "feedbackPath" in src
    assert "feedbackField" in src


def test_ssot_doc_feedback_mode_supports_drag_drop_comment_targeting():
    src = _combined_doc_src()

    assert "const docFrameRef = React.useRef(null);" in src
    assert "const commentTextareaRef = React.useRef(null);" in src
    assert "const handleDocCommentDragStart = (ev) =>" in src
    assert "draggable={docMode === 'feedback'}" in src
    assert "frameDoc.addEventListener('dragover', onDragOver);" in src
    assert "frameDoc.addEventListener('drop', onDrop);" in src
    assert "applyDocDropSection(resolveDocDropSection(ev.target));" in src
    assert "onLoad={() => setDocFrameReady(v => v + 1)}" in src


def test_default_workflow_shows_ssot_import_export_tab():
    src = WORKSPACE_JSX.read_text(encoding="utf-8")

    assert "const showSsotImportExportTab = workflow === 'ssot-gen' || workflow === 'default';" in src
    assert ">Import / Export</span>" in src
    assert "importExportOnly={true}" in src


def test_to_ssot_button_uses_same_plain_mini_button_as_deep_interview():
    src = WORKSPACE_JSX.read_text(encoding="utf-8")
    assert "borderColor: 'var(--ok)', color: 'var(--ok)'" not in src
    assert "title=\"Run /to-ssot for this IP\"\n                  style={{ marginTop: 7 }}" in src
    assert "title=\"Run /to-ssot for this IP\"\n              style={{ marginTop: 10 }}" in src
