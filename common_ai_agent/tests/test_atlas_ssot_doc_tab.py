from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_JSX = ROOT / "frontend" / "atlas" / "workspace.jsx"


def test_ssot_doc_tab_renders_inline_html_export():
    src = WORKSPACE_JSX.read_text(encoding="utf-8")

    assert "const SsotDocPane = " in src
    assert "data-testid=\"ssot-doc-frame\"" in src
    assert "format: 'html'" in src
    assert "inline: '1'" in src
    assert "mainTab === 'doc'" in src
    assert ">doc</span>" in src


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
