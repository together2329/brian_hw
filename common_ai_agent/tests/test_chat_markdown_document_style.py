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
    assert "max-width: 100%;" in css


def test_chat_markdown_uses_available_transcript_width():
    css = STYLES_CSS.read_text(encoding="utf-8")
    frame_src = CHAT_FRAME_TSX.read_text(encoding="utf-8")

    assert ".chat-message-body {" in css
    assert ".feed-entry-agent > .md-agent" in css
    assert ".feed-entry-agent > .md-agent.md-agent-stream-surface" in css
    assert "max-width: 88ch;" not in css
    assert "max-width: 100%;" in css
    assert ".md-chat-frame-body {\n    width: 100%;\n    max-width: 100%;" in frame_src


def test_chat_markdown_iframe_tracks_workspace_text_size():
    frame_src = CHAT_FRAME_TSX.read_text(encoding="utf-8")

    assert "const chatMarkdownTypography = (): FrameTypography" in frame_src
    assert "window.getComputedStyle(document.documentElement)" in frame_src
    assert "rootStyle.getPropertyValue('--ui-agent-font-size')" in frame_src
    assert "rootStyle.getPropertyValue('--ui-code-font-size')" in frame_src
    assert "rootStyle.getPropertyValue('--ui-agent-line-height')" in frame_src
    assert "setTypography(chatMarkdownTypography());" in frame_src
    assert "attributeFilter: ['data-theme', 'data-font-scale', 'data-platform', 'style']" in frame_src
    assert "font-size: var(--doc-body-font-size);" in frame_src
    assert "line-height: var(--doc-body-line-height);" in frame_src
    assert "font-size: var(--doc-code-font-size);" in frame_src
    assert "--doc-body-font-size: ${typography.bodyFontSize};" in frame_src
    assert "--doc-code-font-size: ${typography.codeFontSize};" in frame_src
    assert "--doc-body-line-height: ${typography.lineHeight};" in frame_src


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
    assert "const rectHeight = root.getBoundingClientRect().height || 0;" in frame_src
    assert "html, body { margin: 0; height: auto; min-height: 0;" in frame_src
    assert "const viewportHeight = frameRef.current?.contentWindow?.innerHeight || 0;" in frame_src
    assert "const stableMetric = (value: number): number => {" in frame_src
    assert "Math.abs(value - viewportHeight) <= 1" in frame_src
    assert "pendingMeasureFrameRef.current = window.requestAnimationFrame(measure);" in frame_src
    assert "resizeObserverRef.current = new ResizeObserver(() => scheduleMeasure());" in frame_src
    assert "setHeight(prev => (Math.abs(prev - next) <= 1 ? prev : next));" in frame_src
    assert "window.cancelAnimationFrame(pendingMeasureFrameRef.current);" in frame_src
    measure_section = frame_src.split("const measure = () => {", 1)[1].split("const scheduleMeasure = () => {", 1)[0]
    assert "stableMetric(root.scrollHeight || 0)" in measure_section
    assert "stableMetric(root.offsetHeight || 0)" in measure_section
    assert ")) + 2" not in measure_section
    assert "doc.body?.scrollHeight" not in measure_section
    assert "doc.documentElement?.scrollHeight" not in measure_section
