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
    # One of the !healthMatchesCurrentUser(j) call sites lives inside
    # AgentStatusPanel, which Phase 13g moved into workspace-panels.jsx.
    panels_src = (PROJECT_ROOT / "frontend" / "atlas" / "workspace-panels.jsx").read_text(encoding="utf-8")
    workspace_plus_panels = workspace_src + "\n" + panels_src

    assert "function healthMatchesCurrentUser(payload)" in data_src
    assert "if (!healthMatchesCurrentUser(d)) return;" in data_src
    assert "const healthMatchesCurrentUser = (payload) =>" in workspace_src
    assert workspace_plus_panels.count("!healthMatchesCurrentUser(j)") >= 2


def test_agent_stream_events_require_matching_session_id():
    data_src = (PROJECT_ROOT / "frontend" / "atlas" / "data.jsx").read_text(encoding="utf-8")
    workspace_src = (PROJECT_ROOT / "frontend" / "atlas" / "workspace.jsx").read_text(encoding="utf-8")
    sim_debug_src = (PROJECT_ROOT / "frontend" / "atlas" / "sim-debug.jsx").read_text(encoding="utf-8")
    architect_src = (PROJECT_ROOT / "frontend" / "atlas" / "soc-architect.jsx").read_text(encoding="utf-8")

    assert data_src.count("eventMatchesActiveSession(m, { requireSession: true })") >= 6
    assert workspace_src.count("workspaceEventMatchesActiveSession(m, { requireSession: true })") >= 14
    assert sim_debug_src.count("atlasEventMatchesActiveSession(m, { requireSession: true })") >= 7
    assert architect_src.count("architectEventMatchesActiveSession(m, { requireSession: true })") >= 7


def test_orchestrator_exec_mode_pins_orchestrator_workflow_first():
    data_src = (PROJECT_ROOT / "frontend" / "atlas" / "data.jsx").read_text(encoding="utf-8")
    workspace_src = (PROJECT_ROOT / "frontend" / "atlas" / "workspace.jsx").read_text(encoding="utf-8")

    assert "const ORCHESTRATOR_FLOW_STAGE" in data_src
    assert "return [ORCHESTRATOR_FLOW_STAGE].concat(deduped);" in data_src
    assert "atlas-run-policy-changed" in data_src
    assert "refreshWorkflowStagesForPolicy" in data_src
    assert "orchestrator: {" in workspace_src
    assert "const next = (currentWorkflow === w ? defaultWorkflowForExecMode() : w) || defaultWorkflowForExecMode();" in workspace_src
    assert "next !== 'orchestrator'" in workspace_src
    # OrchestratorWorkflowPane render moved into workflow-report.jsx by
    # Phase 13b of refactor/atlas-modular.
    workflow_report_src = (PROJECT_ROOT / "frontend" / "atlas" / "workflow-report.jsx").read_text(encoding="utf-8")
    assert "return <OrchestratorWorkflowPane activeIp={activeIp} />;" in (workspace_src + "\n" + workflow_report_src)


def test_workspace_chat_routing_prefers_active_session_ip_over_stale_scope():
    workspace_src = (PROJECT_ROOT / "frontend" / "atlas" / "workspace.jsx").read_text(encoding="utf-8")
    data_src = (PROJECT_ROOT / "frontend" / "atlas" / "data.jsx").read_text(encoding="utf-8")

    assert "() => resolveSession(window.ACTIVE_SESSION, activeNamespace, activeSession)" in workspace_src
    assert "return activeIpForRoute([\n      window.ACTIVE_SESSION,\n      activeNamespace," in workspace_src
    # Source indent is 6 spaces (IIFE body is one level deeper than the
    # surrounding `const promptScope = (() =>` at 4 spaces).
    assert "const promptScope = (() => {\n      return activeIpForRoute([" in workspace_src
    assert "const scoped = normalizeUiSession(window.SCOPE_PATH || '');" not in workspace_src
    assert "const browserActiveIp = activeIpFromSession();" in data_src
    assert "const routeActiveIp = effectiveRoute.ip || browserActiveIp || backendActiveIp;" in data_src


def test_health_context_preserves_browser_ip_when_backend_reports_other_ip():
    data_src = (PROJECT_ROOT / "frontend" / "atlas" / "data.jsx").read_text(encoding="utf-8")
    workspace_src = (PROJECT_ROOT / "frontend" / "atlas" / "workspace.jsx").read_text(encoding="utf-8")
    routing_src = (PROJECT_ROOT / "frontend" / "atlas" / "lib" / "session_routing.js").read_text(encoding="utf-8")

    assert "function browserSessionOverridesHealth(payload)" in data_src
    assert "const effectiveSession = healthOverride ? browserSession : (healthSession || browserSession);" in data_src
    assert "const acceptHealthCounters = healthCountersMatchBrowserRoute(d);" in data_src
    assert "const healthMetaApplies = !healthSession || !effectiveSession || healthSession === effectiveSession;" in data_src

    assert "const uiEffectiveHealthSession = (payload) =>" in workspace_src
    # acceptCounters + costIpChanged refs live inside AgentStatusPanel, moved
    # to workspace-panels.jsx by Phase 13g.
    panels_src = (PROJECT_ROOT / "frontend" / "atlas" / "workspace-panels.jsx").read_text(encoding="utf-8")
    workspace_plus_panels = workspace_src + "\n" + panels_src
    assert "const acceptCounters = uiHealthCountersMatchBrowserRoute(j);" in workspace_plus_panels
    assert "costIpChanged" in workspace_plus_panels

    assert "function shouldUseBrowserSession(cfg)" in routing_src
    assert "function healthCountersMatchRoute(cfg)" in routing_src


def test_new_ip_creation_keeps_orchestrator_mode_on_orchestrator_session():
    app_src = (PROJECT_ROOT / "frontend" / "atlas" / "app.jsx").read_text(encoding="utf-8")

    assert "if (mode === 'orchestrator') return 'orchestrator';" in app_src
    assert "workflow: requestedWorkflow" in app_src
    assert "const workflow = requestedExecMode === 'orchestrator' ? 'orchestrator' : payloadWorkflow;" in app_src
