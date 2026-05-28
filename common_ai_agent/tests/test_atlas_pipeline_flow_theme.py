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
    # The right-rail worker sidebar lives inside AgentStatusPanel, which
    # Phase 13g moved into workspace-panels.jsx.
    workspace = (PROJECT_ROOT / "frontend" / "atlas" / "workspace.jsx").read_text()
    panels = (PROJECT_ROOT / "frontend" / "atlas" / "workspace-panels.jsx").read_text()
    # Phase 19: AgentStatusPanel extracted from workspace-panels.jsx.
    agent_status = (PROJECT_ROOT / "frontend" / "atlas" / "agent-status-panel.jsx").read_text()
    combined = workspace + "\n" + panels + "\n" + agent_status

    assert "const workerIp = (() => {" in combined
    assert "workspaceFetchWorkerSnapshot({ ip: workerIp, activeOnly: true })" in combined
    assert "}, [activeIp]);" in combined
    assert "Current context window of the selected/live worker session" in combined
    assert "user/IP" in combined
    assert "activeJobs.slice(0, 4)" in combined


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
    # Phase 20: WorkerOrchestraBar + its pipelineFetchWorkerSnapshot
    # call site extracted from pipeline.jsx → pipeline-trace.jsx.
    pipeline_trace = (atlas_dir / "pipeline-trace.jsx").read_text()
    pipeline_combined = pipeline + "\n" + pipeline_trace

    assert "const workerSnapshotCache = new Map()" in data
    assert "fetchWorkerSnapshot, sessionFor" in data
    assert "workspaceFetchWorkerSnapshot({ ip, activeOnly: true, force: manual })" in workspace
    assert "WorkerOrchestraBar" in pipeline_combined
    assert "pipelineFetchWorkerSnapshot({ ip, activeOnly: true })" in pipeline_combined


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
    # /api/file/delete (and the guard messages) were extracted from atlas_ui.py
    # into atlas_api_files.py by Phase 8/9 of refactor/atlas-modular. The route
    # was renamed at that point: `@app.delete("/api/file")` → `@app.delete("/api/file/delete")`.
    atlas_ui = (PROJECT_ROOT / "src" / "atlas_ui.py").read_text()
    api_files = (PROJECT_ROOT / "src" / "atlas_api_files.py").read_text()
    ui_plus_files = atlas_ui + "\n" + api_files

    assert "fileContextMenu" in workspace
    assert "onContextMenu={(event) => {" in workspace
    assert "method: 'DELETE'" in workspace
    assert "new URLSearchParams({ ip: cleanIp, path: cleanPath })" in workspace
    assert "atlasResourceCache('file').delete(cleanPath)" in workspace
    assert "file-context-menu" in css
    assert "file-context-menu-danger" in css
    assert '@app.delete("/api/file/delete")' in ui_plus_files
    assert "path is outside the selected IP" in ui_plus_files
    assert "directory delete is not supported from the UI" in ui_plus_files


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
    assert "canonicalSession,\n      window.ACTIVE_SESSION" in workspace
    assert "activeSession,\n      activeNamespace" in workspace
    assert "const activeSessionWorkflow = workflowFromSession(" in workspace
    assert "activeSessionWorkflow\n          || routeWorkflow\n          || workflow" in workspace
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


def test_atlas_prompt_input_waits_for_ack_before_clear() -> None:
    workspace = (PROJECT_ROOT / "frontend" / "atlas" / "workspace.jsx").read_text()

    assert "window.backend.subscribe('agent_received'" in workspace
    assert "sent.ack.then" in workspace
    assert "Input not confirmed." in workspace

    normal_send = workspace.rindex("const sent = sendPrompt(raw);")
    normal_tail = workspace[normal_send:workspace.index(
        "// Keep the submitted user message clean.",
        normal_send,
    )]
    assert normal_tail.index("waitForPromptAck(") < normal_tail.index("clearSubmittedInput();")
    assert normal_tail.index("waitForPromptAck(") < normal_tail.index("setFeed(f => [...f, { kind: 'user', text: raw }]);")


def test_atlas_auth_required_revalidates_cookie_before_login() -> None:
    app = (PROJECT_ROOT / "frontend" / "atlas" / "app.jsx").read_text()

    assert "const authRequiredProbeRef = React.useRef(0);" in app
    assert "A single WebSocket can close with auth_required" in app
    assert "fetch('/api/users/me', { cache: 'no-store', credentials: 'include' })" in app
    assert "if (r.status === 401 || r.status === 403) return { authFailed: true };" in app
    assert "window.backend.switchSession(recoveredNs);" in app
    assert "preserve_running: true" in app


def test_atlas_single_worker_workflow_switch_owns_chat_session() -> None:
    workspace = (PROJECT_ROOT / "frontend" / "atlas" / "workspace.jsx").read_text()
    data = (PROJECT_ROOT / "frontend" / "atlas" / "data.jsx").read_text()

    # In Single Worker mode the workflow selector is not just a visual filter:
    # selecting rtl-gen must activate <user>/<ip>/rtl-gen and hydrate that chat,
    # otherwise the SSOT transcript remains visible under an RTL label.
    assert "const defaultWorkflowForExecMode = () => atlasUiOrchestratorMode() ? 'orchestrator' : 'default';" in workspace
    assert "const initialInputRouteForExecMode = () =>" in workspace
    assert "const sessionForExecMode = (session) =>" in workspace
    assert "if (!atlasUiOrchestratorMode() && workflowFromSession(session) === 'orchestrator') return;" in workspace
    assert "type: atlasUiOrchestratorMode() ? 'orchestrator-chat' : 'workflow-chat'," in workspace
    assert "requestedType === 'workflow-chat'" in workspace
    assert "type: atlasUiOrchestratorMode() ? 'workflow-dispatch' : 'workflow-chat'," in workspace
    assert "const isOrch = atlasUiOrchestratorMode();" in workspace
    assert ": `ask:${inputRouteWorkflow}`;" in workspace
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


def test_atlas_submit_holds_input_until_prompt_target_is_ready() -> None:
    workspace = (PROJECT_ROOT / "frontend" / "atlas" / "workspace.jsx").read_text()
    submit_start = workspace.index("const submitMsg = (cmd) => {")
    submit_body = workspace[submit_start:workspace.index("  // Subscribe to backend events", submit_start)]

    assert "const clearSubmittedInput = () => {" in submit_body
    assert "recordInputHistory(raw);" in submit_body
    assert "setInput(cur => {" in submit_body
    assert "curText === raw" in submit_body
    assert "const holdSubmittedInput = (reason) => {" in submit_body
    assert "heldSubmitRef.current = { raw, cmd, createdAt: Date.now() };" in submit_body
    assert "Input held. Waiting for" in submit_body
    assert "it will send automatically if unchanged" in submit_body
    assert "backendReadyForPrompt" in submit_body
    assert "Input held. Backend is" in submit_body
    assert "submitMsg(latest.cmd ?? latest.raw);" in workspace

    # Regression guard: the textarea must not be cleared before workflow or
    # backend readiness is checked. Clearing only happens through the accepted
    # input helper after the target path has been selected.
    assert "recordInputHistory(raw);\n    setInput('');" not in submit_body
    assert submit_body.index("if (workflowReady)") < submit_body.index("clearSubmittedInput();\n      const arg")


def test_atlas_compact_slash_shows_busy_status() -> None:
    workspace = (PROJECT_ROOT / "frontend" / "atlas" / "workspace.jsx").read_text()
    submit_start = workspace.index("const submitMsg = (cmd) => {")
    submit_body = workspace[submit_start:workspace.index("  // Subscribe to backend events", submit_start)]

    assert "const [commandBusy, setCommandBusy] = React.useState(null);" in workspace
    assert "const slashBusyForRaw = (value) => {" in workspace
    assert "head === '/compact' || head === '/co'" in workspace
    assert "setCommandBusy(busyState);" in submit_body
    assert "Compacting history" in workspace
    assert "setCommandBusy(null);" in workspace


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
    # Q&A board UI ("Do not seed default questions" guard comment) moved
    # to ssot-qa-board.jsx by Phase 13f; the backend guard + requirement_rows
    # bookkeeping moved to atlas_qa.py by Phase 10.
    workspace = (PROJECT_ROOT / "frontend" / "atlas" / "workspace.jsx").read_text()
    qa_board = (PROJECT_ROOT / "frontend" / "atlas" / "ssot-qa-board.jsx").read_text()
    jsx_combined = workspace + "\n" + qa_board
    atlas_ui = (PROJECT_ROOT / "src" / "atlas_ui.py").read_text()
    atlas_qa = (PROJECT_ROOT / "src" / "atlas_qa.py").read_text()
    py_combined = atlas_ui + "\n" + atlas_qa

    assert "'9 boxes to fill'" not in jsx_combined
    assert "'채워야 하는 9칸'" not in jsx_combined
    assert "Do not seed default questions" in jsx_combined
    assert "they must not seed the UI with synthetic required boxes" in py_combined
    assert "\"total\": len(requirement_rows)" in py_combined


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
