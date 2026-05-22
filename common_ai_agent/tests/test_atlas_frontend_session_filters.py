from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_live_context_and_cost_require_matching_session_id():
    data_src = (PROJECT_ROOT / "frontend" / "atlas" / "data.jsx").read_text(encoding="utf-8")
    workspace_src = (PROJECT_ROOT / "frontend" / "atlas" / "workspace.jsx").read_text(encoding="utf-8")

    assert "if (!eventSession) return !opts.requireSession;" in data_src
    assert "eventMatchesActiveSession(m, { requireSession: true })" in data_src
    assert "if (!eventSession) return !opts.requireSession;" in workspace_src
    assert "workspaceEventMatchesActiveSession(m, { requireSession: true })" in workspace_src


def test_health_polling_rejects_different_user_snapshots():
    data_src = (PROJECT_ROOT / "frontend" / "atlas" / "data.jsx").read_text(encoding="utf-8")
    workspace_src = (PROJECT_ROOT / "frontend" / "atlas" / "workspace.jsx").read_text(encoding="utf-8")

    assert "function healthMatchesCurrentUser(payload)" in data_src
    assert "if (!healthMatchesCurrentUser(d)) return;" in data_src
    assert "const healthMatchesCurrentUser = (payload) =>" in workspace_src
    assert workspace_src.count("!healthMatchesCurrentUser(j)") >= 2


def test_agent_stream_events_require_matching_session_id():
    data_src = (PROJECT_ROOT / "frontend" / "atlas" / "data.jsx").read_text(encoding="utf-8")
    workspace_src = (PROJECT_ROOT / "frontend" / "atlas" / "workspace.jsx").read_text(encoding="utf-8")
    sim_debug_src = (PROJECT_ROOT / "frontend" / "atlas" / "sim-debug.jsx").read_text(encoding="utf-8")
    architect_src = (PROJECT_ROOT / "frontend" / "atlas" / "soc-architect.jsx").read_text(encoding="utf-8")

    assert data_src.count("eventMatchesActiveSession(m, { requireSession: true })") >= 6
    assert workspace_src.count("workspaceEventMatchesActiveSession(m, { requireSession: true })") >= 14
    assert sim_debug_src.count("atlasEventMatchesActiveSession(m, { requireSession: true })") >= 7
    assert architect_src.count("architectEventMatchesActiveSession(m, { requireSession: true })") >= 7
