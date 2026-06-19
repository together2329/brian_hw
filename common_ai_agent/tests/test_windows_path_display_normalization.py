from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _source(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_display_path_normalizer_covers_windows_and_font_separator_glyphs():
    chips = _source("frontend/atlas/workspace-markdown-chips.tsx")
    frame = _source("frontend/atlas/workspace-tool-detail-frame.tsx")

    assert "export const _DISPLAY_PATH_SEPARATOR_RE" in chips
    assert "\\u20A9" in chips
    assert "\\u00A5" in chips
    assert "\\uFFE5" in chips
    assert "\\uFF3C" in chips
    assert ".replace(_DISPLAY_PATH_SEPARATOR_RE, '/')" in chips
    assert "export const _normalizeDisplayPathToken" in chips
    assert "export const _DISPLAY_PATH_TOKEN_RE" in chips
    assert "export const _PLAIN_FILE_PATH_RE" in chips
    assert "/[\\/\\\\\\u20A9\\u00A5\\uFFE5\\uFF3C]/.test(text)" in chips
    assert "text.includes('/')" not in chips
    assert "const t = _normalizeDisplayedToolPaths(text).trim();" in chips
    assert "_normalizeDisplayedToolPaths(rawTxt)" in chips
    assert "_normalizeDisplayedToolPaths(match[2] || '')" in chips

    assert "_normalizeDisplayedToolPaths(text)" in frame


def test_git_commit_display_uses_path_normalizer():
    git_tab = _source("frontend/atlas/git-tab.tsx")

    assert "import { _normalizeDisplayedToolPaths } from './workspace-markdown-chips';" in git_tab
    assert "const displayPathText = (value: unknown): string => _normalizeDisplayedToolPaths(value);" in git_tab
    assert "setDiffBody(displayPathText(d && d.diff || ''));" in git_tab
    assert "title={displayPathText(gitStatus.cwd || '')}" in git_tab
    assert "{displayPathText(c.subject)}" in git_tab
    assert "{displayPathText(selectedCommit.subject)}" in git_tab
    assert "{displayPathText(diffHeader)}</pre>" in git_tab
    assert "{displayPathText(revertTarget.subject)}" in git_tab
