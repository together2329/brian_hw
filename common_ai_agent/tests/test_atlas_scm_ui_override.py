import sys
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_ROOT = str(Path(__file__).resolve().parents[1])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def _create_app(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("ATLAS_COOKIE_SECRET", "test-secret")
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    from src import atlas_ui

    atlas_ui.PROJECT_ROOT = tmp_path
    return atlas_ui.create_app()


def test_scm_ui_override_file_is_served_and_injected_before_workspace(tmp_path: Path, monkeypatch):
    override = tmp_path / "perforce-scm-tab.jsx"
    override.write_text(
        "window.SCMTab = function CustomScmTab(){ return <div>custom scm</div>; };\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("ATLAS_SCM_PROVIDER", "perforce")
    monkeypatch.setenv("ATLAS_SCM_UI_OVERRIDE_PERFORCE", str(override))

    client = TestClient(_create_app(tmp_path, monkeypatch))

    html = client.get("/").text
    override_idx = html.index('data-atlas-scm-ui-override="1"')
    workspace_idx = html.index('data-filename="workspace.jsx"')
    assert override_idx < workspace_idx
    assert 'src="/api/scm/ui/override.js?v=' in html
    assert '"scm_provider":"perforce"' in html
    assert '"scm_ui_override":true' in html

    script = client.get("/api/scm/ui/override.js")
    assert script.status_code == 200
    assert "window.SCMTab" in script.text
    assert script.headers["cache-control"] == "no-store, max-age=0"


def test_scm_ui_override_rejects_non_js_files(tmp_path: Path, monkeypatch):
    override = tmp_path / "bad.txt"
    override.write_text("window.SCMTab = function Nope(){};\n", encoding="utf-8")
    monkeypatch.setenv("ATLAS_SCM_PROVIDER", "perforce")
    monkeypatch.setenv("ATLAS_SCM_UI_OVERRIDE_PERFORCE", str(override))

    client = TestClient(_create_app(tmp_path, monkeypatch))

    response = client.get("/api/scm/ui/override.js")
    assert response.status_code == 400
    assert response.json()["error"] == "SCM UI override must be .js or .jsx"


def test_workspace_uses_provider_aware_scm_tab_override_contract():
    src = (Path(PROJECT_ROOT) / "frontend" / "atlas" / "workspace.jsx").read_text(encoding="utf-8")

    assert "window.AtlasSCMTabOverrides" in src
    assert "window.SCMTab" in src
    assert "<ScmTabComponent" in src
    assert "fallbackTab={window.GitTab}" in src
    assert "showBuiltinGitTab" in src
    assert "setMainTab('git_native')" in src
    assert 'provider="git"' in src


def test_builtin_git_tab_can_force_git_provider():
    src = (Path(PROJECT_ROOT) / "frontend" / "atlas" / "git-tab.jsx").read_text(encoding="utf-8")

    assert "function GitTab({ initialIp, provider = '' })" in src
    assert "provider=${encodeURIComponent(forcedProvider)}" in src
    assert "provider: forcedProvider || undefined" in src
