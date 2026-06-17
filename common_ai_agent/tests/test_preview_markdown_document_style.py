from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PREVIEW_PANE_TSX = ROOT / "frontend" / "atlas" / "preview-pane.tsx"
STYLES_CSS = ROOT / "frontend" / "atlas" / "styles.css"


def test_markdown_preview_uses_document_surface():
    src = PREVIEW_PANE_TSX.read_text(encoding="utf-8")

    assert "<DeferredMarkdownPreview body={body} sourcePath={path} />" in src
    assert "className=\"md-preview-frame\"" in src
    assert "<main class=\"md-agent md-preview\">${html}</main>" in src


def test_markdown_preview_styles_markdown_syntax_as_document():
    css = STYLES_CSS.read_text(encoding="utf-8")

    assert ".md-preview {" in css
    assert "max-width: 980px;" in css
    assert "margin: 0 auto;" in css
    assert "padding: 28px 42px 56px;" in css
    assert ".md-preview h1" in css
    assert ".md-preview h2" in css
    assert ".md-preview table" in css
    assert "border-radius: 6px;" in css
    assert ".md-preview blockquote" in css
    assert ".md-preview img" in css
    assert ".md-preview input[type=\"checkbox\"]" in css
    assert "[data-theme=\"light\"] .md-preview" in css


def test_markdown_preview_uses_iframe_srcdoc_surface():
    src = PREVIEW_PANE_TSX.read_text(encoding="utf-8")

    assert "const MARKDOWN_PREVIEW_IFRAME_CSS = `" in src
    assert "const srcDoc = useMemo(() => {" in src
    assert "srcDoc={srcDoc}" in src
    assert "onLoad={postProcessFrame}" in src
    assert "_postProcessMarkdownNode(root);" in src
    assert "root.querySelectorAll('img[src]')" in src


def test_markdown_preview_iframe_keeps_scripts_disabled():
    src = PREVIEW_PANE_TSX.read_text(encoding="utf-8")

    assert 'sandbox="allow-same-origin allow-popups"' in src
    assert "allow-scripts" not in src
    assert 'referrerPolicy="no-referrer"' in src
    assert "<base target=\"_blank\" />" in src
