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
    head_section = standard.split('className="tool-card-head"', 1)[1].split("</div>", 1)[0]
    assert "ToolDetailFrame" not in head_section
    assert "<ToolDetailFrame" in obs_card


def test_tool_command_text_uses_iframe_surface():
    source = _source("workspace-feed-cards.tsx")
    standard = source.split("export const _StandardToolCardRaw", 1)[1].split(
        "export const StandardToolCard", 1
    )[0]

    assert "const commandUsesFrame = !!displayArgs" in standard
    assert "const commandFrameOpen = commandUsesFrame && showArgsExpanded" in standard
    assert "const displayArgsSummary = commandUsesFrame ? _toolCommandSummary(displayArgs) : displayArgs" in standard
    assert ">{displayArgsSummary}</span>" in standard
    assert "text={displayArgs}" in standard
    assert 'mode="text"' in standard
    assert "title={`Tool call: ${_toolDisplay(tool)}`}" in standard
    head_section = standard.split('className="tool-card-head"', 1)[1].split("</div>", 1)[0]
    assert "text={displayArgs}" not in head_section


def test_reasoning_blocks_use_iframe_surface():
    source = _source("workspace-feed-cards.tsx")
    thought = source.split("export const CollapsibleThought", 1)[1].split(
        "const _READ_RESULT_TOOL_RE", 1
    )[0]

    assert "const visibleThoughtText = collapsed ? tail.join('\\n') : displayText;" in thought
    assert "<ToolDetailFrame" in thought
    assert "text={visibleThoughtText}" in thought
    assert 'tool="reasoning"' in thought
    assert 'title="Reasoning"' in thought
