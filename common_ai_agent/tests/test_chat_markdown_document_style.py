from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STYLES_CSS = ROOT / "frontend" / "atlas" / "styles.css"
FEED_CARDS_TSX = ROOT / "frontend" / "atlas" / "workspace-feed-cards.tsx"
CHAT_FRAME_TSX = ROOT / "frontend" / "atlas" / "workspace-chat-markdown-frame.tsx"


def test_agent_chat_markdown_uses_document_card_surface():
    css = STYLES_CSS.read_text(encoding="utf-8")
    feed_src = FEED_CARDS_TSX.read_text(encoding="utf-8")

    assert "className=\"feed-entry feed-entry-agent chat-transcript-entry has-hover-affordance\"" in feed_src
    assert ".feed-entry-agent {" in css
    assert ".chat-transcript-entry {" in css
    assert "border-radius: 6px;" in css
    assert "background: #070b10;" in css
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


def test_completed_agent_chat_uses_iframe_srcdoc_surface():
    frame_src = CHAT_FRAME_TSX.read_text(encoding="utf-8")

    assert "export const ChatMarkdownFrame" in frame_src
    assert "const CHAT_MARKDOWN_FRAME_CSS = `" in frame_src
    assert "className=\"chat-markdown-frame\"" in frame_src
    assert "srcDoc={srcDoc}" in frame_src
    assert "<main class=\"md-agent md-chat-frame-body\">${html}</main>" in frame_src
    assert "_postProcessMarkdownNode(root)" in frame_src
    assert "sandbox=\"allow-same-origin allow-popups\"" in frame_src
    assert "allow-scripts" not in frame_src
    assert "referrerPolicy=\"no-referrer\"" in frame_src


def test_chat_iframe_is_completed_only_and_keeps_tools_outside():
    feed_src = FEED_CARDS_TSX.read_text(encoding="utf-8")
    agent_branch = feed_src.split("if (entry.kind === 'agent')", 1)[1].split("if (entry.kind === 'thought')", 1)[0]

    assert "entry._animate" in agent_branch
    assert "<Typewriter text={entry.text || ''} />" in agent_branch
    assert "terminalKind" in agent_branch
    assert "<AtlasTerminalTranscript text={entry.text || ''} kind={terminalKind} />" in agent_branch
    assert "<ChatMarkdownFrame text={entry.text || ''} />" in agent_branch
    assert agent_branch.index("entry._animate") < agent_branch.index("ChatMarkdownFrame")
    assert agent_branch.index("terminalKind") < agent_branch.index("ChatMarkdownFrame")

    tool_card_section = feed_src.split("export const _StandardToolCardRaw", 1)[1].split("export const Typewriter", 1)[0]
    assert "ChatMarkdownFrame" not in tool_card_section


def test_chat_iframe_autoheight_defers_resizeobserver_updates():
    frame_src = CHAT_FRAME_TSX.read_text(encoding="utf-8")

    assert "const pendingMeasureFrameRef = useRef<number | null>(null);" in frame_src
    assert "const scheduleMeasure = () => {" in frame_src
    assert "pendingMeasureFrameRef.current = window.requestAnimationFrame(measure);" in frame_src
    assert "resizeObserverRef.current = new ResizeObserver(() => scheduleMeasure());" in frame_src
    assert "setHeight(prev => (Math.abs(prev - next) <= 1 ? prev : next));" in frame_src
    assert "window.cancelAnimationFrame(pendingMeasureFrameRef.current);" in frame_src


def test_streaming_parent_dom_matches_iframe_document_surface():
    css = STYLES_CSS.read_text(encoding="utf-8")
    frame_src = CHAT_FRAME_TSX.read_text(encoding="utf-8")

    assert ".feed-entry-agent > .md-agent.md-agent-stream-surface {" in css
    assert "max-width: 88ch;" in css
    assert "font-size: 14px;" in css
    assert "line-height: 1.68;" in css
    assert "white-space: pre-wrap;" in css
    assert "overflow-wrap: anywhere;" in css
    assert "[data-theme=\"dark\"] .feed-entry-agent > .md-agent.md-agent-stream-surface" in css
    assert "background: #070b10;" in css
    assert "[data-theme=\"light\"] .feed-entry-agent > .md-agent.md-agent-stream-surface" in css
    assert "background: #ffffff;" in css

    assert "max-width: 88ch;" in frame_src
    assert "font-size: 14px;" in frame_src
    assert "line-height: 1.68;" in frame_src


def test_live_streaming_uses_document_surface_class():
    feed_src = FEED_CARDS_TSX.read_text(encoding="utf-8")

    live_section = feed_src.split("export const LiveAgentPreview", 1)[1].split("export const _FeedEntryRaw", 1)[0]
    agent_section = feed_src.split("if (entry.kind === 'agent')", 1)[1].split("if (entry.kind === 'thought')", 1)[0]

    assert 'className="md-agent md-agent-stream-surface chat-message-body"' in live_section
    assert 'className="md-agent md-agent-stream-surface chat-message-body"' in agent_section
    assert 'className="md-agent-stream-text"' in feed_src
    assert 'className="stream-caret"' in feed_src
    assert "whiteSpace: 'pre-wrap'" not in live_section
    assert "overflowWrap: 'anywhere'" not in live_section


def test_chat_feed_uses_transcript_header_and_body_classes():
    css = STYLES_CSS.read_text(encoding="utf-8")
    feed_src = FEED_CARDS_TSX.read_text(encoding="utf-8")
    frame_src = CHAT_FRAME_TSX.read_text(encoding="utf-8")

    assert "chat-transcript-entry" in feed_src
    assert 'className="chat-message-head"' in feed_src
    assert "chat-message-role" in feed_src
    assert "chat-message-body" in feed_src
    assert ".chat-transcript-entry {" in css
    assert ".chat-message-head {" in css
    assert "border-bottom: 1px solid #263240;" in css
    assert ".chat-message-body {" in css
    assert "max-width: 88ch;" in css
    assert ".feed-entry-user .md-user.md-agent" in css
    assert "font-family: var(--sans);" in css
    assert "marginTop: 0" in frame_src


def test_chat_transcript_role_labels_have_readable_line_box():
    css = STYLES_CSS.read_text(encoding="utf-8")

    role_rule = css.split(".feed-entry-label,", 1)[1].split(".feed-entry-agent .chat-message-role", 1)[0]
    assert "font-size: 12px !important;" in role_rule
    assert "line-height: 1.45;" in role_rule
    assert "text-transform: none;" in role_rule
    assert "letter-spacing: 0.02em !important;" in role_rule

    head_rule = css.split(".chat-message-head {", 1)[1].split("}", 1)[0]
    assert "min-height: 28px;" in head_rule
    assert "padding: 2px 0 8px;" in head_rule


def test_chat_transcript_spacing_is_tight_between_agent_and_tools():
    css = STYLES_CSS.read_text(encoding="utf-8")

    entry_rule = css.split(".chat-transcript-entry {", 1)[1].split("}", 1)[0]
    assert "margin: 0 0 10px !important;" in entry_rule
    assert ".chat-transcript-entry + .tool-card {" in css
    tool_gap_rule = css.split(".chat-transcript-entry + .tool-card {", 1)[1].split("}", 1)[0]
    assert "margin-top: 2px;" in tool_gap_rule
