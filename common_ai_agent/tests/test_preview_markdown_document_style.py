from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PREVIEW_PANE_TSX = ROOT / "frontend" / "atlas" / "preview-pane.tsx"
STYLES_CSS = ROOT / "frontend" / "atlas" / "styles.css"


def test_markdown_preview_uses_document_surface():
    src = PREVIEW_PANE_TSX.read_text(encoding="utf-8")

    assert "className=\"md-agent md-preview\"" in src
    assert "<DeferredMarkdownPreview body={body} sourcePath={path} />" in src


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
