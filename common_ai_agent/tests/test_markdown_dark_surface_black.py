from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STYLES_CSS = ROOT / "frontend" / "atlas" / "styles.css"


def test_dark_markdown_surfaces_use_neutral_black():
    css = STYLES_CSS.read_text(encoding="utf-8")

    assert '[data-theme="dark"] .md-preview,' in css
    assert '[data-theme="dark"] .feed-entry-agent {' in css
    assert "background: #070b10;" in css
    assert '[data-theme="dark"] .feed-entry-user {' in css
    assert "background: #0b1118 !important;" in css
    assert ".chat-transcript-entry {" in css
    assert "background: #070b10;" in css


def test_dark_markdown_nested_surfaces_avoid_brown_tint():
    css = STYLES_CSS.read_text(encoding="utf-8")

    assert '[data-theme="dark"] .md-agent pre,' in css
    assert '[data-theme="dark"] .md-preview pre {' in css
    assert "background: #05080c;" in css
    assert '[data-theme="dark"] .md-agent table,' in css
    assert '[data-theme="dark"] .md-preview table {' in css
    assert '[data-theme="dark"] .md-agent blockquote,' in css
    assert '[data-theme="dark"] .md-preview blockquote {' in css
    assert "background: #0d141c;" in css
    assert "border-color: #263240;" in css
