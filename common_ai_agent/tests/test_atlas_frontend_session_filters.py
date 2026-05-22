from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_live_context_and_cost_require_matching_session_id():
    data_src = (PROJECT_ROOT / "frontend" / "atlas" / "data.jsx").read_text(encoding="utf-8")
    workspace_src = (PROJECT_ROOT / "frontend" / "atlas" / "workspace.jsx").read_text(encoding="utf-8")

    assert "if (!eventSession) return !opts.requireSession;" in data_src
    assert "eventMatchesActiveSession(m, { requireSession: true })" in data_src
    assert "if (!eventSession) return !opts.requireSession;" in workspace_src
    assert "workspaceEventMatchesActiveSession(m, { requireSession: true })" in workspace_src
