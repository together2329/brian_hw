from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_enhanced_pipeline_flow_has_light_theme_palette() -> None:
    css = (PROJECT_ROOT / "frontend" / "atlas" / "styles.css").read_text()

    assert '[data-theme="light"] .enh-canvas-wrap' in css
    assert '#f8fafc' in css
    assert '[data-theme="light"] .enh-lane rect' in css
    assert '[data-theme="light"] .enh-node rect' in css
    assert '[data-theme="light"] .enh-pill text' in css


def test_atlas_windows_font_mode_is_local_first() -> None:
    atlas_dir = PROJECT_ROOT / "frontend" / "atlas"
    app = (atlas_dir / "app.jsx").read_text()
    css = (atlas_dir / "styles.css").read_text()
    index = (atlas_dir / "index.html").read_text()

    assert "ATLAS_FONT_MODE_OPTIONS" in app
    assert "{ key: 'windows', label: 'Windows' }" in app
    assert "atlasIsWindowsPlatform()" in app
    assert '[data-font="windows"]' in css
    assert "--windows-sans" in css
    assert "--windows-mono" in css
    assert "fonts.googleapis.com" not in index
    assert "fonts.gstatic.com" not in index
    assert "@import url(" not in css


def test_atlas_ignores_stale_agent_state_false_before_prompt_run_starts() -> None:
    workspace = (PROJECT_ROOT / "frontend" / "atlas" / "workspace.jsx").read_text()

    assert "awaitingRunStartRef.current = true" in workspace
    assert "backendRunStartedRef.current = true" in workspace
    assert "if (awaitingRunStartRef.current && !backendRunStartedRef.current) return;" in workspace
