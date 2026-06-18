from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _source(name: str) -> str:
    return (PROJECT_ROOT / "frontend" / "atlas" / name).read_text(encoding="utf-8")


def test_workspace_chat_stream_updates_force_bottom_scroll():
    source = _source("workspace-root-data-hook.tsx")
    assert "}, [feed.length, streamText, mainTab, requestFeedScrollToBottom]);" in source
    assert "const forceFeedScrollToBottom = useCallback(() => {" in source
    assert "feedPinnedToBottomRef.current = true;\n    requestFeedScrollToBottom();" in source
    assert "ResizeObserver(() => {\n      requestFeedScrollToBottom();" in source


def test_workspace_resize_observer_does_not_force_scroll_pin():
    source = _source("workspace-root-data-hook.tsx")
    request_section = source.split("const requestFeedScrollToBottom = useCallback(() => {", 1)[1].split(
        "const forceFeedScrollToBottom = useCallback(() => {", 1
    )[0]
    force_section = source.split("const forceFeedScrollToBottom = useCallback(() => {", 1)[1].split(
        "useEffect(() => {\n    requestFeedScrollToBottom();", 1
    )[0]
    resize_section = source.split("const observer = new ResizeObserver(() => {", 1)[1].split(
        "observer.observe(content);", 1
    )[0]

    assert "feedPinnedToBottomRef.current = true;" not in request_section
    assert "feedPinnedToBottomRef.current = true;" in force_section
    assert "requestFeedScrollToBottom();" in resize_section
    assert "forceFeedScrollToBottom();" not in resize_section
    assert "forceFeedScrollToBottom();" in source


def test_workspace_ask_user_cards_are_default_disabled():
    source = _source("workspace-root-data-hook.tsx")
    assert "const atlasAskUserCardsEnabled = (): boolean" in source
    assert "return false;" in source
    assert "if (!atlasAskUserCardsEnabled()) return;" in source


def test_oag_tool_card_shows_header_and_folds_details():
    source = _source("workspace-feed-cards.tsx")
    css = _source("styles.css")
    assert "const isOagTool = toolName === 'oag';" in source
    assert "const isRunCommandTool = toolName === 'run_command';" in source
    assert "const displayArgs = isOagTool ? rawArgsText" in source
    assert "const showArgsExpanded = isOagTool || obsOpen" in source
    assert "const defaultObsOpen = false;" in source
    assert "tool-card-command-args" in source
    assert ".tool-card .tool-card-command-args {" in css
    assert "font-family: var(--code-font);" in css
    assert "overflow-wrap: anywhere;" in css


def test_tool_detail_body_uses_iframe_surface():
    frame = _source("workspace-tool-detail-frame.tsx")
    feed = _source("workspace-feed-cards.tsx")

    assert "export const ToolDetailFrame" in frame
    assert 'className="tool-detail-frame"' in frame
    assert "srcDoc={srcDoc}" in frame
    assert 'sandbox="allow-same-origin allow-popups"' in frame
    assert "allow-scripts" not in frame
    assert "mode === 'markdown'" in frame
    assert "mode === 'diff'" in frame
    assert ".tool-detail-markdown {\n    max-width: 100%;" in frame
    assert "_postProcessMarkdownNode(root)" in frame
    assert "<ToolDetailFrame" in feed
    assert 'mode="diff"' in feed
    assert 'mode="grep"' in feed
    assert 'mode="text"' in feed
    assert 'mode="markdown"' in feed


def test_tool_detail_iframe_tracks_workspace_text_size():
    frame = _source("workspace-tool-detail-frame.tsx")

    assert "const toolDetailTypography = (): FrameTypography" in frame
    assert "window.getComputedStyle(document.documentElement)" in frame
    assert "rootStyle.getPropertyValue('--ui-control-font-size')" in frame
    assert "rootStyle.getPropertyValue('--ui-agent-font-size')" in frame
    assert "rootStyle.getPropertyValue('--ui-code-font-size')" in frame
    assert "rootStyle.getPropertyValue('--ui-agent-line-height')" in frame
    assert "setTypography(toolDetailTypography());" in frame
    assert "attributeFilter: ['data-theme', 'data-font-scale', 'data-platform', 'style']" in frame
    assert "font-size: var(--tool-body-font-size);" in frame
    assert "font-size: var(--tool-markdown-font-size);" in frame
    assert "font-size: var(--tool-code-font-size);" in frame
    assert "line-height: var(--tool-markdown-line-height);" in frame
    assert "--tool-markdown-font-size: ${typography.markdownFontSize};" in frame
    assert "--tool-code-font-size: ${typography.codeFontSize};" in frame


def test_tool_iframe_keeps_header_and_fold_control_outside():
    source = _source("workspace-feed-cards.tsx")
    standard = source.split("export const _StandardToolCardRaw", 1)[1].split(
        "export const StandardToolCard", 1
    )[0]
    obs_card = source.split("export const ObsCard", 1)[1].split(
        "export const _parseJsonObject", 1
    )[0]

    assert 'className="tool-card-head"' in standard
    assert "const displayArgs = isOagTool ? rawArgsText" in standard
    assert "const showArgsExpanded = isOagTool || obsOpen" in standard
    assert "<ObsCard" in standard
    assert "embedded={true}" in standard
    assert "commandFrameOpen" not in standard
    assert "text={displayArgs}" not in standard
    head_section = standard.split('className="tool-card-head"', 1)[1].split("</div>", 1)[0]
    assert "ToolDetailFrame" not in head_section
    assert "<ToolDetailFrame" in obs_card


def test_tool_detail_iframe_autoheight_defers_resizeobserver_updates():
    frame = _source("workspace-tool-detail-frame.tsx")

    assert "const pendingMeasureFrameRef = useRef<number | null>(null);" in frame
    assert "const scheduleMeasure = () => {" in frame
    assert "const rectHeight = root.getBoundingClientRect().height || 0;" in frame
    assert "html, body { margin: 0; height: auto; min-height: 0;" in frame
    assert "const viewportHeight = frameRef.current?.contentWindow?.innerHeight || 0;" in frame
    assert "const stableMetric = (value: number): number => {" in frame
    assert "Math.abs(value - viewportHeight) <= 1" in frame
    assert "pendingMeasureFrameRef.current = window.requestAnimationFrame(measure);" in frame
    assert "resizeObserverRef.current = new ResizeObserver(() => scheduleMeasure());" in frame
    assert "setHeight(prev => (Math.abs(prev - next) <= 1 ? prev : next));" in frame
    assert "window.cancelAnimationFrame(pendingMeasureFrameRef.current);" in frame


def test_tool_detail_iframe_restores_diff_replacement_palette():
    frame = _source("workspace-tool-detail-frame.tsx")

    assert "export const diffClassForLine" in frame
    assert "export const renderedToolBodyHtml" in frame
    assert "if (/^\\s*(?:\\d+|[|>]*\\s*\\d+)\\s+\\+/.test(line)) return 'add';" in frame
    assert "if (/^\\s*(?:\\d+|[|>]*\\s*\\d+)\\s+-/.test(line)) return 'del';" in frame
    assert ".diff-line.add {" in frame
    assert "border-left-color: var(--tool-add);" in frame
    assert "background: color-mix(in oklch, var(--tool-add) 16%, transparent);" in frame
    assert ".diff-line.del {" in frame
    assert "border-left-color: var(--tool-del);" in frame
    assert "background: color-mix(in oklch, var(--tool-del) 16%, transparent);" in frame
    assert "white-space: pre;" in frame


def test_tool_detail_iframe_tints_numbered_replacement_rows():
    frame = _source("workspace-tool-detail-frame.tsx")

    assert "diffClassForLine(line)" in frame
    assert 'const kind = diffClassForLine(line);' in frame
    assert '<span class="diff-line ${kind}">' in frame
    assert '<span class="diff-prefix">' in frame
    assert "if (/^\\s*(?:\\d+|[|>]*\\s*\\d+)\\s+\\+/.test(line)) return 'add';" in frame
    assert "if (/^\\s*(?:\\d+|[|>]*\\s*\\d+)\\s+-/.test(line)) return 'del';" in frame


def test_tool_detail_iframe_highlights_edit_read_and_search_previews():
    frame = _source("workspace-tool-detail-frame.tsx")
    feed = _source("workspace-feed-cards.tsx")

    assert "if (_WRITE_RESULT_TOOL_RE.test(t)) return 10;" in feed
    assert "if (_REPLACE_RESULT_TOOL_RE.test(t)) return 10;" in feed
    assert "hintText={hintText}" in feed

    assert "_toolOutputLanguage" in frame
    assert "_highlightInlineCode" in frame
    assert "_grepOutputRows" in frame
    assert "export const highlightedToolCodeHtml" in frame
    assert "export const toolDetailLanguage" in frame
    assert "tool-detail-code" in frame
    assert "language-${lang}" in frame
    assert "_grepOutputRows(visibleText)" in frame
    assert "highlightedToolCodeHtml(row.code, rowLang)" in frame
    assert "highlightedToolCodeHtml(code, diffLang)" in frame
    assert ".token.string" in frame
    assert "Prism.plugins.autoloader.loadLanguages(language" in frame


def test_tool_result_previews_default_only_for_write_and_replace():
    frame = _source("workspace-tool-detail-frame.tsx")
    feed = _source("workspace-feed-cards.tsx")

    preview_fn = feed.split("export const _toolResultPreviewLines", 1)[1].split(
        "export const _toolResultDefaultsClosed", 1
    )[0]
    assert "if (_WRITE_RESULT_TOOL_RE.test(t)) return 10;" in preview_fn
    assert "if (_REPLACE_RESULT_TOOL_RE.test(t)) return 10;" in preview_fn
    assert "read_file|read_lines|grep_file" not in preview_fn
    assert "run_command" not in preview_fn

    standard = feed.split("export const _StandardToolCardRaw", 1)[1].split(
        "export const StandardToolCard", 1
    )[0]
    assert "const defaultObsOpen = false;" in standard
    assert "const headClickable = !!obs || argsIsLong" in standard
    assert "obs && (isPreviewTool || obsOpen)" in standard

    assert "if (/^run_command$/i.test(String(tool || ''))) return 'none';" in frame
    measure_section = frame.split("const measure = () => {", 1)[1].split("const scheduleMeasure = () => {", 1)[0]
    assert "stableMetric(root.scrollHeight || 0)" in measure_section
    assert "stableMetric(root.offsetHeight || 0)" in measure_section
    assert ")) + 2" not in measure_section
    assert "doc.body?.scrollHeight" not in measure_section
    assert "doc.documentElement?.scrollHeight" not in measure_section


def test_reasoning_coalesces_cumulative_snapshots():
    source = _source("workspace-tool-theme.tsx")

    assert "export const mergeAtlasThoughtText" in source
    assert "if (nextText.startsWith(prevText)) return nextText;" in source
    assert "if (prevText.startsWith(nextText)) return prevText;" in source
    assert "for (let overlap = maxOverlap; overlap > 0; overlap--)" in source
    assert "compactAtlasThoughtText(mergeAtlasThoughtText(prevText, nextText))" in source
    feed = _source("workspace-feed-cards.tsx")
    thought = feed.split("export const CollapsibleThought", 1)[1].split(
        "const _READ_RESULT_TOOL_RE", 1
    )[0]
    assert 'tool="reasoning"' not in thought


def test_reasoning_stream_updates_single_live_card():
    source = _source("workspace-root-data-hook.tsx")

    assert "const liveReasoningEntryIdRef = useRef<string>('');" in source
    assert "const liveReasoningTextRef = useRef<string>('');" in source
    assert "const appendLiveReasoning = useCallback" in source
    assert "compactAtlasThoughtText(mergeAtlasThoughtText(liveReasoningTextRef.current, text))" in source
    assert "entry && entry.kind === 'thought' && entry.reasoningStreamId === streamId" in source
    assert "if (idx >= 0) list[idx] = next;" in source
    assert "else list.push(next);" in source
    reasoning_handler = source.split("w.backend.subscribe('reasoning'", 1)[1].split(
        "w.backend.subscribe('tool'", 1
    )[0]
    assert "appendLiveReasoning(m && m.text);" in reasoning_handler
    assert "appendLiveFeedEntries({ kind: 'thought'" not in reasoning_handler
