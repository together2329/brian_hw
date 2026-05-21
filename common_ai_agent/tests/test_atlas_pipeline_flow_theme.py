from pathlib import Path


def test_enhanced_pipeline_flow_has_light_theme_palette() -> None:
    css = (
        Path(__file__).resolve().parents[1]
        / "frontend"
        / "atlas"
        / "styles.css"
    ).read_text()

    assert '[data-theme="light"] .enh-canvas-wrap' in css
    assert '#f8fafc' in css
    assert '[data-theme="light"] .enh-lane rect' in css
    assert '[data-theme="light"] .enh-node rect' in css
    assert '[data-theme="light"] .enh-pill text' in css
