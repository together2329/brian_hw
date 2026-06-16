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
