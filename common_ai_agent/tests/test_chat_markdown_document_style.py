from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STYLES_CSS = ROOT / "frontend" / "atlas" / "styles.css"
FEED_CARDS_TSX = ROOT / "frontend" / "atlas" / "workspace-feed-cards.tsx"
CHAT_FRAME_TSX = ROOT / "frontend" / "atlas" / "workspace-chat-markdown-frame.tsx"
MARKDOWN_CHIPS_TSX = ROOT / "frontend" / "atlas" / "workspace-markdown-chips.tsx"
DATA_HOOK_TSX = ROOT / "frontend" / "atlas" / "workspace-root-data-hook.tsx"


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


def test_chat_iframe_reprocesses_path_chips_after_file_tree_refresh():
    frame_src = CHAT_FRAME_TSX.read_text(encoding="utf-8")
    chip_src = MARKDOWN_CHIPS_TSX.read_text(encoding="utf-8")

    assert "const [dataRevision, setDataRevision] = useState(0);" in frame_src
    assert "window.addEventListener('atlas-data-changed', onDataChanged);" in frame_src
    assert "detail === 'FILE_TREE'" in frame_src
    assert "detail === 'SCOPE_PATH'" in frame_src
    assert "setDataRevision((n) => n + 1);" in frame_src
    assert "useEffect(() => {\n    postProcessFrame();\n  }, [postProcessFrame]);" in frame_src
    assert "}, [html, dataRevision]);" in frame_src
    assert "if (kind === 'path' && !resolvedPath) return;" in chip_src
    assert "if (el.dataset && el.dataset.chip) return;" in chip_src


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


def test_chat_transcript_cards_fill_available_width():
    css = STYLES_CSS.read_text(encoding="utf-8")

    entry_rule = css.split(".feed-entry-agent,\n.feed-entry-user {", 1)[1].split("}", 1)[0]
    assert "width: 100%;" in entry_rule
    assert "max-width: none;" in entry_rule
    assert "box-sizing: border-box;" in entry_rule

    # The card should fill the pane, but the prose surface can keep a readable
    # measure inside the card/iframe.
    body_rule = css.split(".chat-message-body {", 1)[1].split("}", 1)[0]
    assert "max-width: 88ch;" in body_rule

    light_feed_rule = css.split('[data-theme="light"] .feed-entry {', 1)[1].split("}", 1)[0]
    assert "max-width: none;" in light_feed_rule


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


def test_tool_cards_use_document_font_for_readable_text():
    css = STYLES_CSS.read_text(encoding="utf-8")

    tool_section = css.split("/* ToolCard", 1)[1]
    card_rule = tool_section.split(".tool-card {", 1)[1].split("}", 1)[0]
    assert "font-family: var(--sans);" in card_rule
    assert "font-size: 14px;" in card_rule
    assert "line-height: 1.58;" in card_rule
    assert "letter-spacing: 0;" in card_rule

    head_rule = css.split(".tool-card .tool-card-head {", 1)[1].split("}", 1)[0]
    assert "font-family: var(--sans);" in head_rule
    assert "font-size: 14px;" in head_rule
    assert "line-height: 1.58;" in head_rule

    args_rule = css.split(".tool-card .tool-card-args  {", 1)[1].split("}", 1)[0]
    assert "font-family: var(--sans);" in args_rule
    assert "font-size: 14px;" in args_rule
    assert "line-height: 1.58;" in args_rule
    assert "letter-spacing: 0;" in args_rule

    tool_name_rule = css.split(".tool-card .tool-card-tool  {", 1)[1].split("}", 1)[0]
    assert "font-family: var(--code-font);" in tool_name_rule


def test_reasoning_blocks_match_chat_document_rhythm():
    css = STYLES_CSS.read_text(encoding="utf-8")

    block_rule = css.split(".react-block {", 1)[1].split("}", 1)[0]
    assert "font-family: var(--sans);" in block_rule
    assert "font-size: 14px;" in block_rule
    assert "line-height: 1.62;" in block_rule
    assert "letter-spacing: 0;" in block_rule

    tag_rule = css.split(".react-block .rb-tag {", 1)[1].split("}", 1)[0]
    assert "font-size: 12px;" in tag_rule
    assert "line-height: 1.45;" in tag_rule
    assert "letter-spacing: 0.02em;" in tag_rule
    assert "text-transform: none;" in tag_rule


def test_plain_markdown_file_paths_become_openable_chips():
    chips_src = MARKDOWN_CHIPS_TSX.read_text(encoding="utf-8")
    frame_src = CHAT_FRAME_TSX.read_text(encoding="utf-8")

    assert "export const _PLAIN_FILE_PATH_RE" in chips_src
    assert "export const _processPlainFilePathChips" in chips_src
    assert "!parent.closest('code, pre, a, button, input, textarea, select, script, style')" in chips_src
    assert "code.dataset.chip = 'path';" in chips_src
    assert "code.dataset.path = resolvedPath;" in chips_src
    assert "code.classList.add('chip', 'chip-path');" in chips_src
    assert "_activateChipPath(resolvedPath);" in chips_src
    assert "_processPlainFilePathChips(node);" in chips_src
    assert chips_src.index("_processPlainFilePathChips(node);") < chips_src.index("_processInlineChips(node);")

    assert ".md-chat-frame-body code.chip-path" in frame_src
    assert "cursor: pointer;" in frame_src


def test_chat_path_open_resolves_against_current_file_tree():
    data_hook_src = DATA_HOOK_TSX.read_text(encoding="utf-8")

    assert "import { activeIpFromSession } from './data-helpers';" in data_hook_src
    assert "const resolveChatOpenPath = useCallback" in data_hook_src
    assert ".filter((n: any) => n && n.type === 'file')" in data_hook_src
    assert "activeIp && rel && !rel.startsWith(`${activeIp}/`) ? `${activeIp}/${rel}` : rel" in data_hook_src
    assert "p.endsWith(`/${requested}`)" in data_hook_src
    assert "requested.endsWith(`/${p}`)" in data_hook_src
    assert "return suffix || '';" in data_hook_src
    assert "w.atlasResolveOpenablePath = resolveChatOpenPath;" in data_hook_src
    assert "const path = resolveChatOpenPath(ev?.detail?.path || '');" in data_hook_src
    assert "w.readAtlasAsyncResource?.('file', path)?.catch?.(() => {});" in data_hook_src
    assert "setMainTab((t: string) => (t === 'split' || t === 'preview') ? t : 'split');" in data_hook_src


def test_step_update_status_badges_use_compact_document_typography():
    css = STYLES_CSS.read_text(encoding="utf-8")

    badge_rule = css.split(".step-update-card .atlas-status-badge.compact {", 1)[1].split("}", 1)[0]
    assert "font-family: var(--sans);" in badge_rule
    assert "font-size: 12px;" in badge_rule
    assert "line-height: 1.45;" in badge_rule
    assert "letter-spacing: 0;" in badge_rule
    assert "text-transform: none;" in badge_rule

    transition_rule = css.split(".step-update-transition {", 1)[1].split("}", 1)[0]
    assert "font-size: 12px;" in transition_rule
    assert "letter-spacing: 0;" in transition_rule
    assert "text-transform: none;" in transition_rule
