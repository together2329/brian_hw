from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STYLES_CSS = ROOT / "frontend" / "atlas" / "styles.css"
FEED_CARDS_TSX = ROOT / "frontend" / "atlas" / "workspace-feed-cards.tsx"


def test_agent_chat_markdown_uses_document_card_surface():
    css = STYLES_CSS.read_text(encoding="utf-8")
    feed_src = FEED_CARDS_TSX.read_text(encoding="utf-8")

    assert "className=\"feed-entry feed-entry-agent has-hover-affordance\"" in feed_src
    assert ".feed-entry-agent {" in css
    assert "border-radius: 8px;" in css
    assert "background: color-mix(in oklch, var(--bg-2) 78%, var(--bg));" in css
    assert ".feed-entry-agent > .md-agent" in css
    assert "max-width: 88ch;" in css


def test_chat_markdown_syntax_has_readable_document_rules():
    css = STYLES_CSS.read_text(encoding="utf-8")

    assert ".md-agent h1 {" in css
    assert "font-size: 20px;" in css
    assert ".md-agent h2 {" in css
    assert "font-size: 17px;" in css
    assert ".md-agent table {" in css
    assert "border-collapse: separate;" in css
    assert "border-radius: 6px;" in css
    assert ".md-agent blockquote {" in css
    assert "border-left: 4px solid var(--accent);" in css
    assert ".md-agent pre {" in css
    assert "padding: 12px 14px;" in css
    assert ".feed-entry-user {" in css
