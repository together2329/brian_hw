from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _source(name: str) -> str:
    return (PROJECT_ROOT / "frontend" / "atlas" / name).read_text(encoding="utf-8")


def test_workspace_chat_stream_updates_force_bottom_scroll():
    source = _source("workspace-root-data-hook.tsx")
    assert "}, [feed.length, streamText, mainTab, requestFeedScrollToBottom]);" in source
    assert "useEffect(() => {\n    requestFeedScrollToBottom();" in source
    assert "ResizeObserver(() => {\n      requestFeedScrollToBottom();" in source


def test_workspace_ask_user_cards_are_default_disabled():
    source = _source("workspace-root-data-hook.tsx")
    assert "const atlasAskUserCardsEnabled = (): boolean" in source
    assert "return false;" in source
    assert "if (!atlasAskUserCardsEnabled()) return;" in source


def test_oag_tool_card_shows_header_and_folds_details():
    source = _source("workspace-feed-cards.tsx")
    assert "const isOagTool = toolName === 'oag';" in source
    assert "const displayArgs = isOagTool ? rawArgsText" in source
    assert "const showArgsExpanded = isOagTool || obsOpen" in source
    assert "const defaultObsOpen = isOagTool\n    ? false" in source


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
    assert "_postProcessMarkdownNode(root)" in frame
    assert "<ToolDetailFrame" in feed
    assert 'mode="diff"' in feed
    assert 'mode="grep"' in feed
    assert 'mode="text"' in feed
    assert 'mode="markdown"' in feed


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
    assert "pendingMeasureFrameRef.current = window.requestAnimationFrame(measure);" in frame
    assert "resizeObserverRef.current = new ResizeObserver(() => scheduleMeasure());" in frame
    assert "setHeight(prev => (Math.abs(prev - next) <= 1 ? prev : next));" in frame
    assert "window.cancelAnimationFrame(pendingMeasureFrameRef.current);" in frame


def test_tool_detail_iframe_restores_diff_replacement_palette():
    frame = _source("workspace-tool-detail-frame.tsx")

    assert ".diff-line.add {" in frame
    assert "border-left-color: var(--tool-add);" in frame
    assert "background: color-mix(in oklch, var(--tool-add) 16%, transparent);" in frame
    assert ".diff-line.del {" in frame
    assert "border-left-color: var(--tool-del);" in frame
    assert "background: color-mix(in oklch, var(--tool-del) 16%, transparent);" in frame
    assert "white-space: pre;" in frame


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
