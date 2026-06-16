from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _source(name: str) -> str:
    return (PROJECT_ROOT / "frontend" / "atlas" / name).read_text(encoding="utf-8")


def _make_fake_dist(root: Path) -> Path:
    dist = root / "frontend" / "atlas" / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "assets" / "app-OAGTEST.js").write_text("// test asset\n", encoding="utf-8")
    (dist / "index.vite.html").write_text(
        "<!doctype html><html><head></head><body>index</body></html>",
        encoding="utf-8",
    )
    return root / "frontend" / "atlas"


def test_atlas_boot_config_exposes_oag_mode(tmp_path, monkeypatch):
    monkeypatch.setenv("OAG_MODE", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER", "0")
    import src.atlas_ui as aui

    try:
        from starlette.testclient import TestClient
    except Exception:  # pragma: no cover
        from fastapi.testclient import TestClient  # type: ignore

    monkeypatch.setattr(aui, "FRONTEND", _make_fake_dist(tmp_path))
    html = TestClient(aui.create_app()).get("/").text
    marker = "window.ATLAS_BOOT_CONFIG="
    start = html.index(marker) + len(marker)
    payload, _ = json.JSONDecoder().raw_decode(html[start:])
    assert payload["oag_mode"] is True


def test_oag_flow_stages_default_only():
    source = _source("data-helpers.tsx")
    assert "import { atlasOagMode } from './runtime-flags';" in source
    assert "if (atlasOagMode()) return [DEFAULT_FLOW_STAGE];" in source


def test_oag_workspace_tabs_hide_ssot_doc_req_and_show_sim_debug():
    data_hook = _source("workspace-root-data-hook.tsx")
    rail_tabs = _source("workspace-rootui-rail-tabs.tsx")
    routing = _source("workspace-session-routing.tsx")

    assert "if (atlasOagMode()) return 'default';" in routing
    assert "const oagMode = atlasOagMode();" in data_hook
    assert "const showSsotImportExportTab = !oagMode && (workflow === 'ssot-gen' || workflow === 'default');" in data_hook
    assert "const showSsotTab = !oagMode &&" in data_hook
    assert "const showSsotDocTab = !oagMode && showSsotTab;" in data_hook
    assert "const showReqTab = !oagMode &&" in data_hook
    assert "const showDebugTab = workflow === 'sim_debug' || (oagMode && workflow === 'default');" in data_hook
    assert ">{oagMode ? 'SIM_DEBUG' : 'debug'}</span>" in rail_tabs


def test_workspace_right_panel_defaults_collapsed():
    data_hook = _source("workspace-root-data-hook.tsx")
    splitter = _source("workspace-resize-splitters.tsx")

    assert "defaultCollapsed = false" in splitter
    assert "return defaultCollapsed ? 0 : initial;" in splitter
    assert "useResizable(360, 'atlasRightWDefaultFolded', 260, 600, true, true)" in data_hook


def test_workspace_copy_button_uses_typed_import():
    chips = _source("workspace-markdown-chips.tsx")

    assert "import { CopyBtn as UiCopyBtn, copyToClipboard as uiCopyToClipboard } from './ui-utils';" in chips
    assert "export const _copyToClipboard = uiCopyToClipboard;" in chips
    assert "export const CopyBtn = UiCopyBtn;" in chips
    assert "export const CopyBtn = window.CopyBtn;" not in chips
