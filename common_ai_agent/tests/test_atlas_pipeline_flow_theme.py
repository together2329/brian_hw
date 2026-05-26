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
    assert "normalizeAtlasFontMode" in app
    assert "localStorage.getItem('atlasFontModeUserSet')" in app
    assert '[data-font="windows"]' in css
    assert "--windows-sans" in css
    assert "--windows-mono" in css
    assert "fonts.googleapis.com" not in index
    assert "fonts.gstatic.com" not in index
    assert "@import url(" not in css


def test_atlas_es_module_helpers_load_as_modules() -> None:
    atlas_dir = PROJECT_ROOT / "frontend" / "atlas"
    index = (atlas_dir / "index.html").read_text()

    for helper in (
        "lib/banner_logic.js",
        "lib/dashboard_helpers.js",
        "lib/workers_panel_logic.js",
    ):
        assert f'<script type="module" src="{helper}">' in index


def test_atlas_ignores_stale_agent_state_false_before_prompt_run_starts() -> None:
    workspace = (PROJECT_ROOT / "frontend" / "atlas" / "workspace.jsx").read_text()

    assert "awaitingRunStartRef.current = true" in workspace
    assert "backendRunStartedRef.current = true" in workspace
    assert "if (awaitingRunStartRef.current && !backendRunStartedRef.current) return;" in workspace


def test_atlas_worker_sidebar_polls_current_ip_scope() -> None:
    workspace = (PROJECT_ROOT / "frontend" / "atlas" / "workspace.jsx").read_text()

    assert "const workerIp = (() => {" in workspace
    assert "workspaceFetchWorkerSnapshot({ ip: workerIp, activeOnly: true })" in workspace
    assert "}, [activeIp]);" in workspace
    assert "Current context window of the selected/live worker session" in workspace
    assert "user/IP" in workspace
    assert "activeJobs.slice(0, 4)" in workspace


def test_atlas_orchestrator_chat_exposes_flow_strip() -> None:
    workspace = (PROJECT_ROOT / "frontend" / "atlas" / "workspace.jsx").read_text()

    assert "orchestratorFlowFromFeed" in workspace
    assert "renderOrchestratorFlowStrip" in workspace
    assert "Current orchestrator flow for the latest chat request" in workspace
    assert "Check state" in workspace
    assert "Dispatch" in workspace
    assert "Wait result" in workspace


def test_atlas_live_worker_thought_logs_default_collapsed() -> None:
    workspace = (PROJECT_ROOT / "frontend" / "atlas" / "workspace.jsx").read_text()

    assert "Live worker thoughts can contain long retry logs" in workspace
    assert "if (entries.some(e => e && e.kind === 'thought')) return true;" in workspace


def test_atlas_worker_panels_share_cached_worker_snapshot_fetch() -> None:
    atlas_dir = PROJECT_ROOT / "frontend" / "atlas"
    data = (atlas_dir / "data.jsx").read_text()
    workspace = (atlas_dir / "workspace.jsx").read_text()
    pipeline = (atlas_dir / "pipeline.jsx").read_text()

    assert "const workerSnapshotCache = new Map()" in data
    assert "fetchWorkerSnapshot, sessionFor" in data
    assert "workspaceFetchWorkerSnapshot({ ip, activeOnly: true, force: manual })" in workspace
    assert "WorkerOrchestraBar" in pipeline
    assert "pipelineFetchWorkerSnapshot({ ip, activeOnly: true })" in pipeline


def test_atlas_workspace_lands_on_chat_and_reports_worker_done_state() -> None:
    atlas_dir = PROJECT_ROOT / "frontend" / "atlas"
    app = (atlas_dir / "app.jsx").read_text()
    workspace = (atlas_dir / "workspace.jsx").read_text()
    css = (atlas_dir / "styles.css").read_text()
    atlas_ui = (PROJECT_ROOT / "src" / "atlas_ui.py").read_text()

    assert "return 'workspace';" in app
    assert "Workflow switches should land on Chat first." in workspace
    assert "setMainTab('chat');" in workspace
    assert "const active = (workflow || 'default') === s.id;" in workspace
    assert 'className="tab-chip tab-chip-primary"' in workspace
    assert "order: -100" in workspace
    assert ".tab-chip.tab-chip-primary" in css
    assert "flex-wrap: wrap;" in css
    assert "Worker done" in workspace
    assert "worker done" in workspace
    assert "finishSlashTurn" in workspace
    assert 'client_session.emit("slash_output", text=cleaned, finish=bool(finish))' in atlas_ui
    assert '"[Atlas UI language preference]\\n"' not in atlas_ui
    assert "Preferred visible language:" not in atlas_ui


def test_atlas_ip_file_tree_exposes_right_click_delete() -> None:
    atlas_dir = PROJECT_ROOT / "frontend" / "atlas"
    workspace = (atlas_dir / "workspace.jsx").read_text()
    css = (atlas_dir / "styles.css").read_text()
    atlas_ui = (PROJECT_ROOT / "src" / "atlas_ui.py").read_text()

    assert "fileContextMenu" in workspace
    assert "onContextMenu={(event) => {" in workspace
    assert "method: 'DELETE'" in workspace
    assert "new URLSearchParams({ ip: cleanIp, path: cleanPath })" in workspace
    assert "atlasResourceCache('file').delete(cleanPath)" in workspace
    assert "file-context-menu" in css
    assert "file-context-menu-danger" in css
    assert '@app.delete("/api/file")' in atlas_ui
    assert "path is outside the selected IP" in atlas_ui
    assert "directory delete is not supported from the UI" in atlas_ui


def test_atlas_session_switches_hydrate_chat_history_without_full_reload() -> None:
    data = (PROJECT_ROOT / "frontend" / "atlas" / "data.jsx").read_text()
    workspace = (PROJECT_ROOT / "frontend" / "atlas" / "workspace.jsx").read_text()

    # Workflow, pipeline, and ask_user session switches must re-read the
    # destination session conversation. Keeping hydrateConversation=false here
    # makes chat look empty/stale after moving between screens or workflows.
    assert "window.atlasData.refreshSessionState(sid, false)" not in workspace
    assert "function refreshActiveConversation(session, opts = {})" in data
    assert "limit: CHAT_SWITCH_LIMIT" in data
    assert "refreshChatSession(sid)" in workspace
    assert "refreshChatSession(newNamespace)" in workspace


def test_atlas_background_file_refresh_is_quiet() -> None:
    data = (PROJECT_ROOT / "frontend" / "atlas" / "data.jsx").read_text()

    assert "opts.quiet" in data
    assert "refreshFileTree(window.SCOPE_PATH || '', { quiet: true })" in data
    assert "if (!quiet) window.FILE_TREE = []" in data


def test_atlas_prompt_send_prefers_current_ip_workflow_session() -> None:
    workspace = (PROJECT_ROOT / "frontend" / "atlas" / "workspace.jsx").read_text()
    backend = (PROJECT_ROOT / "frontend" / "atlas" / "backend.js").read_text()

    # The first message after an IP/workflow switch used to prefer stale
    # activeNamespace over the visible IP/workflow, so it could run in
    # <user>/default/<workflow> and be filtered out of the current chat.
    assert "const canonicalSession = (window.atlasData && window.atlasData.sessionFor)" in workspace
    assert "window.atlasData.sessionFor(promptScope, promptWorkflow)" in workspace
    assert "canonicalSession,\n        window.ACTIVE_SESSION" in workspace
    assert "activeSession,\n        activeNamespace" in workspace
    assert "const activeSessionWorkflow = workflowFromSession(" in workspace
    assert "activeSessionWorkflow\n            || routeWorkflow\n            || workflow" in workspace
    assert "const sessionChanged = targetSessionId !== currentSessionId;" in backend
    assert "clearPendingAcks();" in backend
    assert "liveQueue = [];" in backend
    assert "if (targetSessionId !== currentSessionId) {\n      liveConnect(targetSessionId);\n      return;\n    }" in backend


def test_atlas_prompt_send_does_not_repeat_scope_preamble() -> None:
    atlas_dir = PROJECT_ROOT / "frontend" / "atlas"
    workspace = (atlas_dir / "workspace.jsx").read_text()
    architect = (atlas_dir / "soc-architect.jsx").read_text()
    main = (PROJECT_ROOT / "src" / "main.py").read_text()

    assert "confine every file read" not in workspace
    assert "confine every file read" not in architect
    assert "sendPrompt(raw);" in workspace
    assert "text," in architect
    assert "[PATH_SCOPE: Keep file reads, writes, edits" in main


def test_atlas_prompt_ack_is_sent_before_slow_session_setup() -> None:
    atlas_ui = (PROJECT_ROOT / "src" / "atlas_ui.py").read_text()

    ack_pos = atlas_ui.index('"type": "agent_received"')
    setup_pos = atlas_ui.index("if _session_raw:\n                        try:")
    assert ack_pos < setup_pos
    assert "slow worker startup cannot trigger a duplicate send" in atlas_ui


def test_atlas_single_worker_workflow_switch_owns_chat_session() -> None:
    workspace = (PROJECT_ROOT / "frontend" / "atlas" / "workspace.jsx").read_text()
    data = (PROJECT_ROOT / "frontend" / "atlas" / "data.jsx").read_text()

    # In Single Worker mode the workflow selector is not just a visual filter:
    # selecting rtl-gen must activate <user>/<ip>/rtl-gen and hydrate that chat,
    # otherwise the SSOT transcript remains visible under an RTL label.
    assert "const defaultWorkflowForExecMode = () => atlasUiOrchestratorMode() ? 'orchestrator' : 'default';" in workspace
    assert "Single Worker mode binds the selected workflow to the active chat" in workspace
    assert "if (atlasUiOrchestratorMode()) return;" in workspace
    assert "const targetSession = sessionForInputRoute(ip, wf);" in workspace
    assert "setChatViewSession(targetSession);" in workspace
    assert "refreshChatSession(targetSession, { force: true });" in workspace
    assert "workflowName === 'default' || workflowName === 'orchestrator'" not in workspace
    assert "const effectiveWorkspace = activeWorkflow ||" in data
    assert "window.CONTEXT.workspace = activeWorkflow || backendActive || '';" in data
    assert "body: JSON.stringify({ session })" in data


def test_atlas_workflow_switch_shows_readiness_overlay() -> None:
    workspace = (PROJECT_ROOT / "frontend" / "atlas" / "workspace.jsx").read_text()
    styles = (PROJECT_ROOT / "frontend" / "atlas" / "styles.css").read_text()

    assert "const WorkflowReadyOverlay = ({ state }) =>" in workspace
    assert "beginWorkflowReady(next, sid, ip)" in workspace
    assert "session_worker_warmup" in workspace
    assert "Ready to receive input" in workspace
    assert "disabled={!!workflowReady}" in workspace
    assert "<WorkflowReadyOverlay state={workflowReady} />" in workspace
    assert ".workflow-ready-overlay" in styles
    assert ".workflow-ready-step[data-state=\"active\"]" in styles


def test_atlas_left_workflow_ip_panels_are_vertically_resizable() -> None:
    workspace = (PROJECT_ROOT / "frontend" / "atlas" / "workspace.jsx").read_text()
    styles = (PROJECT_ROOT / "frontend" / "atlas" / "styles.css").read_text()

    assert "const useVerticalResizable = (initial, storageKey, minH, maxH) =>" in workspace
    assert "const HorizontalSplitter = ({ height, onResize, onReset, title }) =>" in workspace
    assert "atlasLeftWorkflowH" in workspace
    assert "useVerticalResizable(178, 'atlasLeftWorkflowH', 126, 540)" in workspace
    assert "aria-label=\"Resize Workflow and IP panels\"" in workspace
    assert "className=\"box left-workflow-box\"" in workspace
    assert "className=\"left-workflow-list\"" in workspace
    assert "<HorizontalSplitter" in workspace
    assert ".left-stack-splitter" in styles
    assert ".left-workflow-list" in styles


def test_atlas_ssot_qa_does_not_seed_nine_default_boxes() -> None:
    workspace = (PROJECT_ROOT / "frontend" / "atlas" / "workspace.jsx").read_text()
    atlas_ui = (PROJECT_ROOT / "src" / "atlas_ui.py").read_text()

    assert "'9 boxes to fill'" not in workspace
    assert "'채워야 하는 9칸'" not in workspace
    assert "Do not seed default questions" in workspace
    assert "they must not seed the UI with synthetic required boxes" in atlas_ui
    assert "\"total\": len(requirement_rows)" in atlas_ui


def test_atlas_live_worker_feed_is_bounded_for_responsiveness() -> None:
    workspace = (PROJECT_ROOT / "frontend" / "atlas" / "workspace.jsx").read_text()
    logic = (PROJECT_ROOT / "frontend" / "atlas" / "lib" / "orchestrator_chat_logic.mjs").read_text()

    assert "const MAX_RENDERED_FEED_ENTRIES = 240;" in workspace
    assert "Older entries are hidden in this view for speed." in workspace
    assert "const trimAtlasFeedState = (items, maxEntries = 600)" in workspace
    assert "trimAtlasFeedState(coalesceAtlasFeedEntries" in workspace
    assert "const MAX_THOUGHT_LINES = 80;" in logic
    assert "older thought lines hidden for speed" in logic


def test_atlas_conversation_hydration_rejects_stale_session_payloads() -> None:
    atlas_dir = PROJECT_ROOT / "frontend" / "atlas"
    app = (atlas_dir / "app.jsx").read_text()
    workspace = (atlas_dir / "workspace.jsx").read_text()

    # Cloudflare reconnects can deliver a late conversation snapshot for a
    # previous namespace. That snapshot must not reset the active IP/workflow
    # selectors or replace the current chat feed.
    assert "eventSession !== liveSession" in app
    assert "ev.type === 'atlas-conversation-loaded' || ev.type === 'atlas-session-loaded'" in app
    assert "if (session && activeNow && session !== activeNow && (!viewNow || session !== viewNow)) return;" in workspace


def test_atlas_conversation_hydration_accepts_text_only_messages() -> None:
    workspace = (PROJECT_ROOT / "frontend" / "atlas" / "workspace.jsx").read_text()

    # Some persisted conversation rows store display text in `text` instead
    # of OpenAI-style `content`. Hydration must render those rows after a
    # reload/tunnel reconnect instead of leaving the chat blank.
    assert "const rawContent = m.content !== undefined ? m.content : m.text;" in workspace
    assert "typeof rawContent === 'string' ? rawContent" in workspace
