from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAIL_TABS_TSX = ROOT / "frontend" / "atlas" / "workspace-rootui-rail-tabs.tsx"
DATA_HOOK_TSX = ROOT / "frontend" / "atlas" / "workspace-root-data-hook.tsx"
MARKDOWN_CHIPS_TSX = ROOT / "frontend" / "atlas" / "workspace-markdown-chips.tsx"


def test_file_tree_open_preserves_full_view_preview_mode():
    src = RAIL_TABS_TSX.read_text(encoding="utf-8")
    file_click_branch = src.split("if (n.type === 'file')", 1)[1].split("} else {", 1)[0]

    assert "ws.readAtlasAsyncResource?.('file', fullPath)?.catch?.(() => {});" in file_click_branch
    assert "setPreviewPath(fullPath);" in file_click_branch
    assert "ws.persistAtlasPreviewPath?.(fullPath);" in file_click_branch
    assert "setMainTab((tab: string) => tab === 'preview' ? 'preview' : 'split');" in file_click_branch
    assert "setMainTab('split');" not in file_click_branch


def test_markdown_and_chat_path_chips_require_file_tree_match():
    chips_src = MARKDOWN_CHIPS_TSX.read_text(encoding="utf-8")
    data_hook_src = DATA_HOOK_TSX.read_text(encoding="utf-8")

    assert "atlasResolveOpenablePath?: (path: unknown) => string;" in chips_src
    assert "export const _resolveOpenableChipPath" in chips_src
    assert "if (typeof _mdWin.atlasResolveOpenablePath === 'function')" in chips_src
    assert "const resolvedPath = kind === 'path' ? _resolveOpenableChipPath(txt) : '';" in chips_src
    assert "if (kind === 'path' && !resolvedPath) return;" in chips_src
    assert "const resolvedPath = _resolveOpenableChipPath(path);" in chips_src
    assert "if (!resolvedPath) {" in chips_src
    assert "code.dataset.path = resolvedPath;" in chips_src
    assert "_activateChipPath(resolvedPath);" in chips_src

    assert "const resolveChatOpenPath = useCallback" in data_hook_src
    assert ".filter((n: any) => n && n.type === 'file')" in data_hook_src
    assert "return suffix || '';" in data_hook_src
    assert "w.atlasResolveOpenablePath = resolveChatOpenPath;" in data_hook_src
