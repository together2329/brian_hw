// workspace-root-data-hook.tsx — strangler-fig migration slice of workspace.jsx.
//
// Owns: useWorkspaceData — the EXTRACTED custom hook carved from the Workspace
// closure that holds the data / derived-state half of the workspace:
//   - input + input-history (recordInputHistory / replaceInputHistory)
//   - slash-command list + the `/`-completion `filtered` memo
//   - the streaming /healthz poll loop + workspaceTelemetry sync
//     (atlas-data-changed / atlas-session-loaded)
//   - backendState, peerCount, streamText
//   - openFile / rightTab / mainTab / previewPath / fileContextMenu / gitShow /
//     centerLayout / chatFeedSummary tab+view state and the many tab-visibility
//     flags
//   - qaState / qaHistory (scope-matched, localStorage) + ssotApproval
//   - SSOT-QA refresh (refreshSsotQa / refreshSsotQaSessions /
//     activateSsotQaSession)
//   - askUser flow helpers (flowMatchesCurrentSession / activateAskUserSession)
//   - pendingQcard / ssotQaBoardData memos
//   - atQuery / fileMatches / filtered memos + @-file completion
//   - file-tree effects, deleteIpTreeFile, filePanelIp / visibleFileTree /
//     filePanelStatus and SCM-tab resolution
//   - the many atlas-* event-listener effects
//
// The session-half state (workflow / activeSession / feed / refs / route
// helpers) lives in useWorkspaceSession; it is threaded in here through the
// `deps` parameter so the two extracted hooks compose inside the Workspace
// render. This is an INERT mirror — legacy workspace.jsx still serves the live
// app. Window-sourced values are typed `any` on purpose; do not tighten them.

import { useState, useEffect, useRef, useCallback, useMemo, useReducer } from 'react';

import {
  refreshChatSession,
  trimAtlasFeedState,
  atlasBootScmProvider,
  atlasResolveScmTab,
  atlasScmTabLabel,
  INPUT_HISTORY_LIMIT,
  QA_HISTORY_LIMIT,
  QA_HISTORY_LEGACY_STORAGE_KEY,
} from './workspace-tool-theme';
import {
  WORKFLOW_REPORT_TABS,
  workspaceTelemetryFromMessages,
} from './workspace-report-status';
import {
  normalizeUiSession,
  healthMatchesCurrentUser,
  uiSessionRoute,
  uiHealthCountersMatchBrowserRoute,
  uiEffectiveHealthSession,
  atlasUiOrchestratorMode,
  defaultWorkflowForExecMode,
  ssotIpFromSession,
  isSsotYamlPath,
  routeScopeIp,
  activeIpForRoute,
  workflowFromSession,
  sessionForExecMode,
} from './workspace-session-routing';
import {
  persistAtlasPreviewPath,
  defaultPreviewPathForWorkflow,
  previewPathLooksStaleForWorkspace,
  atlasResourceCache,
} from './workspace-async-resource';
import {
  mergeHealthTelemetry,
  mergeContextTelemetry,
  buildQaHistoryScope,
  qaHistoryEntryMatchesScope,
  cleanInputHistory,
  loadStoredInputHistory,
  loadStoredPreviewPath,
  resolveActiveSsotIp,
} from './workspace-rootdata-telemetry';
import {
  conversationFeedFromMessages,
  parseAtQuery,
  filterSlashCommands,
  makeHasLiveFeedEntries,
  buildSsotQaBoardData,
  derivePendingQcard,
} from './workspace-rootdata-feed-completion';

// Re-export the deps contract from its extracted home so it stays importable
// from this module (public-contract preservation for the strangler-fig split).
export type { WorkspaceDataDeps } from './workspace-rootdata-telemetry';
import type { WorkspaceDataDeps } from './workspace-rootdata-telemetry';

const w = window as any;

export const useWorkspaceData = (deps: WorkspaceDataDeps) => {
  const {
    activeNamespace,
    workflow,
    setWorkflow,
    activeSession,
    setActiveSession,
    activeSessionRef,
    feed,
    setFeed,
    chatViewSessionRef,
    hydratedConversationSessionRef,
    liveFeedStartedRef,
    workerLogCursorsRef,
    streamingRef,
    streamBufferRef,
    inputRef,
    feedRef,
    intent,
    switchIntent,
    resolveSession,
    setChatViewSession,
    sessionForInputRoute,
    setOrchestratorInputRoute,
    setWorkflowDispatchInputRoute,
    activateSession,
    NORMAL_FEED,
    PLAN_FEED,
  } = deps;

  // ── Telemetry: /healthz poll loop ───────────────────────────────
  const [backendState, setBackendState] = useState<any>(() => {
    if (!w.backend) return 'missing';
    return w.backend.getConnectionState ? w.backend.getConnectionState() : 'connecting';
  });
  const [commandBusy, setCommandBusy] = useState<any>(null);
  const [workspaceTelemetry, setWorkspaceTelemetry] = useState<any>({
    toolCount: 0,
    lastTool: '',
    lastToolStatus: '',
    lastToolResult: '',
    tokensIn: 0,
    tokensCache: 0,
    tokensOut: 0,
    costUsd: 0,
    costScope: '',
    costUser: '',
    costIp: '',
    costCalls: 0,
    lastCostDelta: 0,
    model: '',
    activeSession: '',
    agentAlive: false,
    agentRunning: false,
  });

  useEffect(() => {
    let cancelled = false;
    const poll = () => {
      fetch('/healthz?cost=0', { cache: 'no-store' })
        .then((r) => (r.ok ? r.json() : null))
        .then((j: any) => {
          if (cancelled || !j || !healthMatchesCurrentUser(j)) return;
          const effectiveSession = uiEffectiveHealthSession(j);
          const acceptCounters = uiHealthCountersMatchBrowserRoute(j);
          const effectiveRoute = uiSessionRoute(effectiveSession);
          setWorkspaceTelemetry((prev: any) => ({
            ...prev,
            ...mergeHealthTelemetry(prev, j, effectiveSession, acceptCounters, effectiveRoute),
          }));
        })
        .catch(() => {});
    };
    poll();
    const id = setInterval(poll, 30000);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  useEffect(() => {
    const syncContextUsage = () => {
      const ctx = w.CONTEXT || {};
      setWorkspaceTelemetry((prev: any) => ({
        ...prev,
        ...mergeContextTelemetry(prev, ctx),
      }));
    };
    window.addEventListener('atlas-data-changed', syncContextUsage);
    window.addEventListener('atlas-session-loaded', syncContextUsage);
    syncContextUsage();
    return () => {
      window.removeEventListener('atlas-data-changed', syncContextUsage);
      window.removeEventListener('atlas-session-loaded', syncContextUsage);
    };
  }, []);

  const [peerCount, setPeerCount] = useState<number>(1);
  const [streamText, setStreamText] = useState<string>('');
  const [openFile, setOpenFile] = useState<any>(null);
  const [rightTab, setRightTab] = useState<string>('todo'); // todo | progress | git
  const [mainTab, setMainTab] = useState<string>('chat');
  const [previewPath, setPreviewPath] = useState<any>(() => loadStoredPreviewPath());
  const [fileContextMenu, setFileContextMenu] = useState<any>(null);
  useEffect(() => {
    const close = () => setFileContextMenu(null);
    const onKey = (event: any) => {
      if (event && event.key === 'Escape') close();
    };
    window.addEventListener('click', close);
    window.addEventListener('resize', close);
    window.addEventListener('keydown', onKey);
    return () => {
      window.removeEventListener('click', close);
      window.removeEventListener('resize', close);
      window.removeEventListener('keydown', onKey);
    };
  }, []);

  const [gitShow, setGitShow] = useState<any>(null); // {sha, ip, subject} | null
  useEffect(() => {
    const onShow = (ev: any) => {
      const d = (ev && ev.detail) || {};
      if (!d.sha) return;
      setGitShow({ sha: d.sha, ip: d.ip || '', subject: d.subject || '' });
      setMainTab((t: string) => (t === 'chat' || t === 'qa' || t === 'checklist' || t === 'import_export' || t === 'split') ? 'preview' : t);
    };
    window.addEventListener('atlas-git-show', onShow);
    return () => window.removeEventListener('atlas-git-show', onShow);
  }, []);

  const [centerLayout, setCenterLayout] = useState<string>('classic');
  const [chatFeedSummary, setChatFeedSummary] = useState<boolean>(
    () => w.ATLAS_CHAT_FEED_SUMMARY !== false,
  );

  // qaState is keyed by flow_id. Dynamic flows are added on-the-fly when the
  // agent emits an ask_user event over the WS.
  const [qaState, setQaState] = useState<Record<string, any>>({});
  const qaStateRef = useRef<any>(qaState);
  useEffect(() => { qaStateRef.current = qaState; }, [qaState]);
  const [qaHistory, setQaHistory] = useState<any[]>([]);
  const [ssotApproval, setSsotApproval] = useState<any>(null);
  const [ssotQa, setSsotQa] = useState<any>(null);
  const [ssotQaSessions, setSsotQaSessions] = useState<any[]>([]);

  // ── Input + input history ───────────────────────────────────────
  const [input, setInput] = useState<string>('');
  const heldSubmitRef = useRef<any>(null);

  // Fold/drag-select comment events from PreviewPane prefill the chat input
  // with `@<path> L<lo>-L<hi> (label)` and focus it.
  useEffect(() => {
    const handler = (ev: any) => {
      try {
        const d = ev.detail || {};
        const path = String(d.path || '');
        const lo = Number(d.lineStart || d.lo || 0);
        const hi = Number(d.lineEnd || d.hi || 0);
        const label = String(d.label || '').trim();
        const text = String(d.text || '');
        const lang = String(d.lang || '');
        if (!path || !lo || !hi) return;
        const labelStr = label ? ` (${label})` : '';
        let block = '';
        if (text) {
          const fence = lang || '';
          block = `\n\n\`\`\`${fence}\n${text}\n\`\`\`\n\n`;
        }
        const next = `@${path} L${lo}-${hi}${labelStr}${block || '\n\n'}`;
        setInput(next);
        requestAnimationFrame(() => requestAnimationFrame(() => {
          const el = inputRef.current;
          if (!el) return;
          el.focus();
          try { el.selectionStart = el.selectionEnd = el.value.length; } catch (_) {}
          el.style.height = 'auto';
          el.style.height = Math.min(el.scrollHeight, 192) + 'px';
        }));
      } catch (_) {}
    };
    window.addEventListener('atlas-fold-comment', handler);
    return () => window.removeEventListener('atlas-fold-comment', handler);
  }, []);

  const [inputHistory, setInputHistory] = useState<string[]>(
    () => loadStoredInputHistory(INPUT_HISTORY_LIMIT),
  );
  const inputHistoryIndexRef = useRef<any>(null);
  const inputHistoryDraftRef = useRef<string>('');
  const [showSlash, setShowSlash] = useState<boolean>(false);
  const [slashSel, setSlashSel] = useState<number>(0);
  const [slashCommands, setSlashCommands] = useState<any[]>(() => (
    Array.isArray(w.SLASH_COMMANDS) ? w.SLASH_COMMANDS : []
  ));

  const replaceInputHistory = useCallback((items: any) => {
    const cleaned = cleanInputHistory(items, INPUT_HISTORY_LIMIT);
    setInputHistory(cleaned);
    try { localStorage.setItem('atlasInputHistory', JSON.stringify(cleaned)); } catch (_) {}
  }, []);

  useEffect(() => {
    let alive = true;
    fetch('/api/input-history?limit=' + INPUT_HISTORY_LIMIT, { cache: 'no-store' })
      .then((r) => (r.ok ? r.json() : null))
      .then((d: any) => {
        if (!alive || !d || !Array.isArray(d.history)) return;
        replaceInputHistory(d.history);
      })
      .catch(() => {});
    return () => { alive = false; };
  }, [replaceInputHistory]);

  const recordInputHistory = useCallback((raw: any) => {
    const text = String(raw || '').trim();
    if (!text) return;
    inputHistoryIndexRef.current = null;
    inputHistoryDraftRef.current = '';
    setInputHistory((prev: string[]) => {
      const next = [...prev, text].slice(-INPUT_HISTORY_LIMIT);
      try { localStorage.setItem('atlasInputHistory', JSON.stringify(next)); } catch (_) {}
      return next;
    });
    fetch('/api/input-history', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    }).catch(() => {});
  }, []);

  // ── Session-derived data ────────────────────────────────────────
  const currentSession = useMemo(
    () => resolveSession(w.ACTIVE_SESSION, activeNamespace, activeSession),
    [activeNamespace, activeSession, resolveSession],
  );

  const activeIp = (() => {
    return activeIpForRoute([
      w.ACTIVE_SESSION,
      activeNamespace,
      currentSession,
      activeSession,
    ]);
  })();

  useEffect(() => {
    // Single Worker mode binds the selected workflow to the active chat session.
    if (atlasUiOrchestratorMode()) return;
    const wf = normalizeUiSession(workflow || '');
    if (!wf || wf === 'default' || wf === 'orchestrator') return;
    const ip = activeIp
      || routeScopeIp(w.SCOPE_PATH || '')
      || activeIpForRoute([
        w.ACTIVE_SESSION,
        activeSessionRef.current,
        activeSession,
        activeNamespace,
      ]);
    if (!ip || ip.toLowerCase() === 'default') return;

    const targetSession = sessionForInputRoute(ip, wf);
    if (!targetSession) return;
    setWorkflowDispatchInputRoute(wf, ip);
    const current = normalizeUiSession(w.ACTIVE_SESSION || activeSessionRef.current || activeSession || '');
    if (targetSession === current) {
      setChatViewSession(targetSession);
      return;
    }

    w.ACTIVE_SESSION = targetSession;
    w.ACTIVE_IP = ip;
    activeSessionRef.current = targetSession;
    setActiveSession(targetSession);
    setChatViewSession(targetSession);
    liveFeedStartedRef.current = false;
    hydratedConversationSessionRef.current = targetSession;
    workerLogCursorsRef.current.clear();
    setFeed(NORMAL_FEED);
    try { localStorage.setItem('atlasActiveSession', targetSession); } catch (_) {}
    if (w.backend) {
      try {
        if (typeof w.backend.switchSession === 'function') w.backend.switchSession(targetSession);
        else if (typeof w.backend.connect === 'function') w.backend.connect(targetSession);
      } catch (_) {}
    }
    refreshChatSession(targetSession, { force: true });
  }, [
    activeIp,
    activeNamespace,
    activeSession,
    sessionForInputRoute,
    setChatViewSession,
    setWorkflowDispatchInputRoute,
    workflow,
  ]);

  const activeSsotIp = useCallback(
    () => resolveActiveSsotIp(activeIp, currentSession),
    [activeIp, currentSession],
  );

  // ── Q&A history (per session+IP, localStorage) ──────────────────
  const qaHistoryScope = useMemo(
    () => buildQaHistoryScope(
      normalizeUiSession(currentSession || w.ACTIVE_SESSION || ''),
      activeSsotIp(),
    ),
    [activeSsotIp, currentSession],
  );

  const qaHistoryMatchesScope = useCallback(
    (entry: any) => qaHistoryEntryMatchesScope(entry, qaHistoryScope.session, qaHistoryScope.ip),
    [qaHistoryScope.ip, qaHistoryScope.session],
  );

  useEffect(() => {
    try {
      const raw = localStorage.getItem(qaHistoryScope.key);
      const parsed = raw ? JSON.parse(raw) : null;
      if (Array.isArray(parsed)) {
        setQaHistory(parsed.filter(qaHistoryMatchesScope).slice(0, QA_HISTORY_LIMIT));
        return;
      }
      const legacyRaw = localStorage.getItem(QA_HISTORY_LEGACY_STORAGE_KEY);
      const legacyParsed = legacyRaw ? JSON.parse(legacyRaw) : [];
      const migrated = Array.isArray(legacyParsed)
        ? legacyParsed.filter(qaHistoryMatchesScope).slice(0, QA_HISTORY_LIMIT)
        : [];
      if (migrated.length) {
        localStorage.setItem(qaHistoryScope.key, JSON.stringify(migrated));
      }
      setQaHistory(migrated);
    } catch (_) {
      setQaHistory([]);
    }
  }, [qaHistoryMatchesScope, qaHistoryScope.key]);

  useEffect(() => {
    try {
      const scoped = qaHistory.filter(qaHistoryMatchesScope).slice(0, QA_HISTORY_LIMIT);
      if (scoped.length) {
        localStorage.setItem(qaHistoryScope.key, JSON.stringify(scoped));
      } else {
        localStorage.removeItem(qaHistoryScope.key);
      }
    } catch (_) {}
  }, [qaHistory, qaHistoryMatchesScope, qaHistoryScope.key]);

  const visibleQaHistory = useMemo(
    () => qaHistory.filter(qaHistoryMatchesScope).slice(0, QA_HISTORY_LIMIT),
    [qaHistory, qaHistoryMatchesScope],
  );

  const clearQaHistory = useCallback(() => {
    setQaHistory([]);
    try { localStorage.removeItem(qaHistoryScope.key); } catch (_) {}
  }, [qaHistoryScope.key]);

  // Keep preview aligned with the active IP/workflow without clobbering
  // deliberate file-tree selections.
  useEffect(() => {
    const ip = activeSsotIp();
    if (!ip) return;
    const wf = workflow || workflowFromSession(currentSession || w.ACTIVE_SESSION || '') || defaultWorkflowForExecMode();
    const canonical = defaultPreviewPathForWorkflow(ip, wf);
    if (!canonical || previewPath === canonical) return;
    const cur = String(previewPath || '');
    const looksLikeStaleSsot = /\/ssot\.yaml$/i.test(cur) || /^[A-Za-z0-9_]+\/yaml\/[^/]+\.ssot\.yaml$/.test(cur);
    if (!cur || previewPathLooksStaleForWorkspace(cur, ip) || looksLikeStaleSsot) {
      setPreviewPath(canonical);
      persistAtlasPreviewPath(canonical);
    }
  }, [activeSsotIp, currentSession, previewPath, workflow]);

  // Inline-code chip click handlers — wired up from _processInlineChips().
  useEffect(() => {
    const onPath = (ev: any) => {
      const path = String(ev?.detail?.path || '').trim();
      if (!path) return;
      setPreviewPath(path);
      persistAtlasPreviewPath(path);
      setMainTab((t: string) => (t === 'split' || t === 'preview') ? t : 'split');
    };
    const onIp = (ev: any) => {
      const ip = String(ev?.detail?.ip || '').trim();
      if (!ip) return;
      const known = (w.IP_OPTIONS || []).map((s: any) => String(s).toLowerCase());
      if (known.length && !known.includes(ip.toLowerCase())) return;
      if (w.atlasData && typeof w.atlasData.setScopePath === 'function') {
        w.atlasData.setScopePath(ip);
      }
      setPreviewPath(`${ip}/yaml/${ip}.ssot.yaml`);
    };
    window.addEventListener('atlas-chip-open', onPath);
    window.addEventListener('atlas-chip-ip', onIp);
    return () => {
      window.removeEventListener('atlas-chip-open', onPath);
      window.removeEventListener('atlas-chip-ip', onIp);
    };
  }, []);

  // ── SSOT-QA refresh ─────────────────────────────────────────────
  const refreshSsotQa = useCallback(async (sessionOverride?: any) => {
    const session = normalizeUiSession(sessionOverride || currentSession || w.ACTIVE_SESSION || '');
    const ip = ssotIpFromSession(session) || activeSsotIp();
    if (!ip) {
      setSsotQa({ ip: '', toc: [], sections: [], summary: { total: 0, approved: 0, pending: 0 } });
      return null;
    }
    try {
      const qs = new URLSearchParams({ ip });
      if (session) qs.set('session', session);
      const r = await fetch('/api/ssot/qa?' + qs.toString(), { cache: 'no-store' });
      if (!r.ok) return null;
      const d = await r.json();
      setSsotQa(d);
      return d;
    } catch (_) {
      return null;
    }
  }, [activeSsotIp, currentSession]);

  const refreshSsotQaSessions = useCallback(async () => {
    try {
      const r = await fetch('/api/ssot/qa/sessions', { cache: 'no-store' });
      if (!r.ok) return null;
      const d = await r.json();
      const rows = Array.isArray(d.sessions) ? d.sessions : [];
      setSsotQaSessions(rows);
      return rows;
    } catch (_) {
      return null;
    }
  }, []);

  useEffect(() => {
    if (workflow !== 'ssot-gen') return;
    const ip = activeSsotIp();
    if (!ip) return;
    const loadedIp = String(ssotQa?.ip || '').trim();
    const session = normalizeUiSession(currentSession || w.ACTIVE_SESSION || '');
    const loadedSession = normalizeUiSession(ssotQa?.session || '');
    const sameSession = !session || !loadedSession || session === loadedSession;
    if (loadedIp === ip && sameSession) return;
    refreshSsotQa(session);
    refreshSsotQaSessions();
  }, [
    activeSsotIp,
    currentSession,
    refreshSsotQa,
    refreshSsotQaSessions,
    ssotQa?.ip,
    ssotQa?.session,
    workflow,
  ]);

  const activateSsotQaSession = useCallback((row: any) => {
    const sid = normalizeUiSession(row?.session || '');
    if (!sid) return;
    w.ACTIVE_SESSION = sid;
    setActiveSession(sid);
    try { localStorage.setItem('atlasActiveSession', sid); } catch (_) {}
    if (row?.ip && w.atlasData?.setScopePath) {
      w.atlasData.setScopePath(row.ip);
    }
    refreshChatSession(sid);
    setWorkflow('ssot-gen');
    refreshSsotQa(sid);
  }, [refreshSsotQa]);

  const flowMatchesCurrentSession = useCallback((flowId: any, eventSession?: any) => {
    const flow = w.QA_FLOWS && w.QA_FLOWS[flowId];
    const flowSession = normalizeUiSession(eventSession || (flow && flow.session) || '');
    const active = normalizeUiSession(currentSession || w.ACTIVE_SESSION || '');
    if (!flowSession || !active || flowSession === active) return true;
    const flowParts = flowSession.split('/').filter(Boolean);
    const activeParts = active.split('/').filter(Boolean);
    const minLen = Math.min(flowParts.length, activeParts.length);
    if (minLen < 2) return false;
    return flowParts.slice(-minLen).join('/') === activeParts.slice(-minLen).join('/');
  }, [currentSession]);

  const activateAskUserSession = useCallback((session: any, ip: any, eventWorkflow: any) => {
    const sid = normalizeUiSession(session || '');
    if (!sid) return;
    if (flowMatchesCurrentSession('', sid)) return;
    w.ACTIVE_SESSION = sid;
    setActiveSession(sid);
    try { localStorage.setItem('atlasActiveSession', sid); } catch (_) {}
    if (ip && w.atlasData?.setScopePath) {
      w.atlasData.setScopePath(ip);
    }
    if (eventWorkflow) {
      setWorkflow(eventWorkflow);
    }
    refreshChatSession(sid);
  }, [flowMatchesCurrentSession]);

  // Force a re-render when the live data layer refreshes FILE_TREE / TODOS /
  // SSOT_FILES so dependent panels show fresh data.
  const [, bumpRender] = useReducer((x: number) => x + 1, 0);
  useEffect(() => {
    const h = () => bumpRender();
    window.addEventListener('atlas-data-changed', h);
    return () => window.removeEventListener('atlas-data-changed', h);
  }, []);

  useEffect(() => {
    refreshSsotQa();
    refreshSsotQaSessions();
    const h = (ev: any) => {
      if (!ev.detail || ['SESSION_STATE', 'SCOPE_PATH', 'SSOT_QA', 'SSOT_FILES'].includes(ev.detail)) {
        refreshSsotQa();
        refreshSsotQaSessions();
      }
    };
    window.addEventListener('atlas-data-changed', h);
    return () => window.removeEventListener('atlas-data-changed', h);
  }, [refreshSsotQa, refreshSsotQaSessions]);

  useEffect(() => {
    const onData = (ev: any) => {
      if (ev.detail === 'CONTEXT') {
        setChatFeedSummary(w.ATLAS_CHAT_FEED_SUMMARY !== false);
      }
      if (ev.detail === 'CONTEXT' || ev.detail === 'FLOW_STAGES') {
        const backendWorkflow = (w.CONTEXT && w.CONTEXT.workspace) || '';
        const backendViewWorkflow = (w.CONTEXT && w.CONTEXT.view_workspace) || '';
        const activeWorkflow = workflowFromSession(w.ACTIVE_SESSION || '');
        const nextWorkflow = (
          atlasUiOrchestratorMode() && backendViewWorkflow && backendViewWorkflow !== 'default'
        ) ? backendViewWorkflow : (activeWorkflow || backendWorkflow);
        const known = (w.FLOW_STAGES || []).some((s: any) => s.id === nextWorkflow);
        if (!nextWorkflow || nextWorkflow === 'default') {
          setWorkflow(defaultWorkflowForExecMode());
        } else if (known) {
          setWorkflow(nextWorkflow);
        } else {
          setWorkflow(defaultWorkflowForExecMode());
        }
        if (atlasUiOrchestratorMode()) {
          const viewWorkflow = (known && nextWorkflow && nextWorkflow !== 'default')
            ? nextWorkflow
            : 'orchestrator';
          if (viewWorkflow === 'orchestrator') {
            setOrchestratorInputRoute(activeIp);
          } else {
            setWorkflowDispatchInputRoute(viewWorkflow, activeIp);
          }
        }
      }
      if (ev.detail === 'SCOPE_PATH') {
        const activeWorkflow = workflowFromSession(w.ACTIVE_SESSION || '');
        const scopedIp = routeScopeIp(w.SCOPE_PATH || '');
        const routeIp = activeIpForRoute([
          w.ACTIVE_SESSION,
          activeSessionRef.current,
          activeSession,
          activeNamespace,
        ]);
        if (routeIp && scopedIp && scopedIp !== routeIp) return;
        activateSession(routeIp || scopedIp || '', activeWorkflow || (w.CONTEXT && w.CONTEXT.workspace) || '');
      }
    };
    onData({ detail: 'CONTEXT' });
    window.addEventListener('atlas-data-changed', onData);
    return () => window.removeEventListener('atlas-data-changed', onData);
  }, [activateSession, activeIp, activeNamespace, activeSession, setOrchestratorInputRoute, setWorkflowDispatchInputRoute, workflow]);

  useEffect(() => {
    const onSessionSwitched = (ev: any) => {
      const detail = ev?.detail || {};
      const sid = sessionForExecMode(detail.namespace || detail.session || '');
      if (!sid) return;
      w.ACTIVE_SESSION = sid;
      activeSessionRef.current = sid;
      setActiveSession(sid);
      try { localStorage.setItem('atlasActiveSession', sid); } catch (_) {}
      const nextWorkflow = workflowFromSession(sid);
      setWorkflow(nextWorkflow || defaultWorkflowForExecMode());
      if (atlasUiOrchestratorMode()) {
        const ip = ssotIpFromSession(sid) || activeIp || '';
        if (nextWorkflow && nextWorkflow !== 'default' && nextWorkflow !== 'orchestrator') {
          setWorkflowDispatchInputRoute(nextWorkflow, ip);
        } else {
          setOrchestratorInputRoute(ip);
        }
      }
      refreshChatSession(sid);
    };
    window.addEventListener('atlas-session-switched', onSessionSwitched);
    return () => window.removeEventListener('atlas-session-switched', onSessionSwitched);
  }, [activeIp, setOrchestratorInputRoute, setWorkflowDispatchInputRoute]);

  // Hydrate the chat feed from the active conversation.json.
  useEffect(() => {
    const hasLiveFeedEntries = makeHasLiveFeedEntries(NORMAL_FEED, PLAN_FEED);
    const hasPendingAskUser = () => {
      const state = qaStateRef.current || {};
      return Object.values(state).some((st: any) => st && !st.submitted);
    };
    const onConvLoaded = (ev: any) => {
      const msgs = (ev.detail && ev.detail.messages) || [];
      const session = normalizeUiSession((ev.detail && ev.detail.session) || '');
      const activeNow = normalizeUiSession(w.ACTIVE_SESSION || activeSessionRef.current || '');
      const viewNow = normalizeUiSession(chatViewSessionRef.current || '');
      if (!atlasUiOrchestratorMode() && workflowFromSession(session) === 'orchestrator') return;
      if (session && activeNow && session !== activeNow && (!viewNow || session !== viewNow)) return;
      const telemetry = workspaceTelemetryFromMessages(msgs);
      if (telemetry.count || telemetry.result) {
        setWorkspaceTelemetry((prev: any) => ({
          ...prev,
          toolCount: Math.max(Number(prev.toolCount || 0), Number(telemetry.count || 0)),
          lastTool: telemetry.last || prev.lastTool,
          lastToolStatus: telemetry.status || prev.lastToolStatus,
          lastToolResult: telemetry.result || prev.lastToolResult,
        }));
      }
      if (session && session === activeNow) setActiveSession(session);
      if (streamingRef.current || (streamBufferRef.current || '').trim()) {
        return;
      }
      const newFeed = conversationFeedFromMessages(msgs, session);
      setFeed((prev: any) => {
        const prevSession = normalizeUiSession(hydratedConversationSessionRef.current || '');
        const namespaceChanged = !!(session && prevSession && session !== prevSession);
        const activeDisplaySession = normalizeUiSession(w.ACTIVE_SESSION || activeSessionRef.current || '');
        const viewDisplaySession = normalizeUiSession(chatViewSessionRef.current || '');
        const sameActiveSession = !session || session === activeDisplaySession || (!!viewDisplaySession && session === viewDisplaySession);
        if (sameActiveSession && !namespaceChanged && liveFeedStartedRef.current && hasLiveFeedEntries(prev)) {
          return prev;
        }
        const lateEmptySnapshot = (
          sameActiveSession
          && !namespaceChanged
          && newFeed.length === 0
          && (hasLiveFeedEntries(prev) || hasPendingAskUser())
        );
        if (lateEmptySnapshot) {
          return prev;
        }
        if (session) hydratedConversationSessionRef.current = session;
        if (namespaceChanged) {
          liveFeedStartedRef.current = false;
          workerLogCursorsRef.current.clear();
        }
        if (viewDisplaySession && session === viewDisplaySession && newFeed.length === 0) {
          const viewWorkflow = workflowFromSession(viewDisplaySession) || 'worker';
          return [{ kind: 'agent', text: `No ${viewWorkflow} worker transcript yet.`, createdAt: Date.now() }];
        }
        return trimAtlasFeedState(newFeed);
      });
    };
    window.addEventListener('atlas-conversation-loaded', onConvLoaded);
    if (w.ATLAS_LAST_CONVERSATION) {
      onConvLoaded({ detail: w.ATLAS_LAST_CONVERSATION });
    }
    return () => window.removeEventListener('atlas-conversation-loaded', onConvLoaded);
  }, []);

  // Derived: the latest unsubmitted qcard.
  const pendingQcard = useMemo(
    () => derivePendingQcard(feed, qaState, flowMatchesCurrentSession),
    [feed, qaState, flowMatchesCurrentSession],
  );

  // Tabbed center layout — auto-switch to Q&A tab when ask_user fires.
  const _qcardActiveFlow = pendingQcard?.flowId || null;
  const _qcardSubmitted = !!(pendingQcard && qaState[pendingQcard.flowId]?.submitted);
  useEffect(() => {
    if (centerLayout !== 'tabbed') return;
    if (_qcardActiveFlow && !_qcardSubmitted && mainTab !== 'qa') {
      setMainTab('qa');
    } else if (!_qcardActiveFlow && mainTab === 'qa' && workflow !== 'ssot-gen') {
      setMainTab('chat');
    }
  }, [centerLayout, _qcardActiveFlow, _qcardSubmitted, workflow]);

  const [askSel, setAskSel] = useState<number>(0);
  const pendingQcardActiveTab = pendingQcard
    ? (qaState[pendingQcard.flowId]?.active || 0)
    : 0;
  const showQaTab = centerLayout === 'tabbed' || workflow === 'ssot-gen' || !!pendingQcard;
  const showSsotChecklistTab = workflow === 'ssot-gen';
  const showSsotImportExportTab = workflow === 'ssot-gen' || workflow === 'default';
  const showSsotTab = workflow === 'ssot-gen' || (w.SSOT_FILES || []).length > 0 || isSsotYamlPath(previewPath);
  const showSsotDocTab = showSsotTab;
  const showSimSummaryTab = workflow === 'sim_debug';
  const showDebugTab = workflow === 'sim_debug';
  const showCoverageTab = workflow === 'coverage';
  const workflowReportMeta = WORKFLOW_REPORT_TABS[workflow] || null;
  const showWorkflowReportTab = !!workflowReportMeta;
  const ssotQaBoardData = useMemo(
    () => buildSsotQaBoardData(ssotQa, activeSsotIp(), currentSession || w.ACTIVE_SESSION || ''),
    [activeSsotIp, currentSession, ssotQa],
  );
  const lastWorkflowTabRef = useRef<any>(null);
  useEffect(() => {
    if (lastWorkflowTabRef.current === workflow) return;
    lastWorkflowTabRef.current = workflow;
    setMainTab('chat');
  }, [workflow]);
  useEffect(() => { setAskSel(0); }, [pendingQcard?.flowId, pendingQcardActiveTab]);

  // Auto-focus the ask_user prompt area when one opens.
  useEffect(() => {
    if (pendingQcard) {
      setTimeout(() => {
        const el = document.querySelector('.ask-prompt') as any;
        el?.focus();
      }, 30);
    }
  }, [pendingQcard?.flowId]);

  // ── @ file completion ───────────────────────────────────────────
  const atQuery = useMemo(() => parseAtQuery(input), [input]);

  const [atDirCache, setAtDirCache] = useState<Record<string, any>>({});
  const [atDirEntries, setAtDirEntries] = useState<any[]>([]);

  useEffect(() => {
    if (!atQuery) { setAtDirEntries([]); return; }
    const key = atQuery.parentAbs;
    if (atDirCache[key]) { setAtDirEntries(atDirCache[key]); return; }
    let cancelled = false;
    fetch('/api/files?path=' + encodeURIComponent(key))
      .then((r) => r.json())
      .then((d: any) => {
        if (cancelled) return;
        const entries = (d && d.entries) || [];
        setAtDirCache((c: any) => ({ ...c, [key]: entries }));
        setAtDirEntries(entries);
      })
      .catch(() => { if (!cancelled) setAtDirEntries([]); });
    return () => { cancelled = true; };
  }, [atQuery && atQuery.parentAbs]);

  const fileMatches = useMemo(() => {
    if (!atQuery) return [];
    const f = atQuery.filter;
    const list = !f
      ? atDirEntries
      : atDirEntries.filter((e: any) => e.name.toLowerCase().startsWith(f));
    return list.slice(0, 30);
  }, [atQuery && atQuery.filter, atDirEntries]);

  const filtered = useMemo(
    () => filterSlashCommands(input, slashCommands),
    [input, slashCommands],
  );

  const [showAt, setShowAt] = useState<boolean>(false);
  const [atSel, setAtSel] = useState<number>(0);

  useEffect(() => {
    if (/^\/[^\s]*$/.test(input)) { setShowSlash(true); setSlashSel(0); setShowAt(false); }
    else setShowSlash(false);
    if (atQuery) { setShowAt(true); setAtSel(0); }
    else setShowAt(false);
  }, [input, atQuery && atQuery.parentAbs, atQuery && atQuery.filter]);

  useEffect(() => {
    const refreshSlashCommands = () => {
      setSlashCommands(Array.isArray(w.SLASH_COMMANDS) ? w.SLASH_COMMANDS : []);
      setSlashSel(0);
    };
    refreshSlashCommands();
    const onDataChanged = (ev: any) => {
      if (!ev.detail || ev.detail === 'SLASH_COMMANDS') refreshSlashCommands();
    };
    window.addEventListener('atlas-data-changed', onDataChanged);
    return () => window.removeEventListener('atlas-data-changed', onDataChanged);
  }, []);

  const acceptAtCompletion = (entry: any) => {
    if (!atQuery) return;
    const before = input.slice(0, atQuery.pos);
    const after = input.slice(atQuery.pos + atQuery.token.length);
    const parent = atQuery.parentRel ? atQuery.parentRel + '/' : '';
    const fullParent = atQuery.ipScoped
      ? `${atQuery.ipPrefix}/${parent}`
      : parent;
    if (entry.type === 'dir') {
      setInput(before + '@' + parent + entry.name + '/' + after);
    } else {
      setInput(before + '@' + fullParent + entry.name + ' ' + after);
      setShowAt(false);
    }
  };

  useEffect(() => {
    if (feedRef.current) feedRef.current.scrollTop = feedRef.current.scrollHeight;
  }, [feed, streamText, mainTab]);

  // shift+tab swaps Normal ↔ Plan.
  useEffect(() => {
    const onKey = (e: any) => {
      if (e.key === 'Tab' && e.shiftKey) {
        e.preventDefault();
        switchIntent(intent === 'normal' ? 'plan' : 'normal');
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [intent, workflow]);

  // ── File tree panel ─────────────────────────────────────────────
  const filePanelIp = (activeIp && String(activeIp).trim() !== 'default')
    ? String(activeIp).trim()
    : '';
  const visibleFileTree = filePanelIp ? (w.FILE_TREE || []) : [];
  const filePanelStatus = filePanelIp
    ? (w.FILE_TREE_ERROR
        ? `(file tree error — ${w.FILE_TREE_ERROR})`
        : (w.FILE_TREE_LOADING ? '(loading file tree...)' : '(empty — select an IP or refresh)'))
    : '(select IP_ID to show files)';
  const deleteIpTreeFile = useCallback(async (path: any, ip: any) => {
    const cleanPath = String(path || '').trim();
    const cleanIp = String(ip || filePanelIp || '').trim();
    if (!cleanPath || !cleanIp) return;
    const ok = window.confirm(`Delete ${cleanPath}? This cannot be undone.`);
    if (!ok) return;
    try {
      const params = new URLSearchParams({ ip: cleanIp, path: cleanPath });
      const response = await fetch(`/api/file?${params.toString()}`, {
        method: 'DELETE',
        cache: 'no-store',
        credentials: 'include',
      });
      let data: any = {};
      try { data = await response.json(); } catch (_) {}
      if (!response.ok) throw new Error(data.error || data.detail || `HTTP ${response.status}`);
      atlasResourceCache('file').delete(cleanPath);
      if (previewPath === cleanPath) {
        setPreviewPath('');
        persistAtlasPreviewPath('');
        setMainTab('chat');
      }
      window.dispatchEvent(new CustomEvent('atlas-file-changed', {
        detail: { path: cleanPath, ip: cleanIp, deleted: true },
      }));
      await w.atlasData?.refreshFileTree?.(cleanIp, { recursive: true, quiet: true });
    } catch (error: any) {
      window.alert(`Delete failed: ${String((error && error.message) || error)}`);
    }
  }, [filePanelIp, previewPath]);

  const scmProvider = atlasBootScmProvider();
  const ScmTabComponent = atlasResolveScmTab(scmProvider);
  const scmTabLabel = atlasScmTabLabel(scmProvider, ScmTabComponent);
  const showBuiltinGitTab = !!(
    typeof w.GitTab === 'function'
    && (scmProvider !== 'git' || ScmTabComponent !== w.GitTab)
  );

  // ── chat submit (with switch-gate guard) ───────────────────────────
  // The session-half primitives needed to send/hold a prompt are threaded in
  // through the spread session bag (workspace-root composes dataDeps as
  // { ...session }), so they are read off `deps` with the file's permissive
  // `any` house style rather than re-declared in the typed contract.
  const sessionBag = deps as any;
  const submitMsg = useCallback((cmd?: any) => {
    const raw = String(cmd ?? input).trim();
    if (!raw) return;
    const setStreaming = sessionBag.setStreaming;
    const setStreamText = sessionBag.setStreamText;
    const workflowReady = sessionBag.workflowReady;
    const switchGateRef = sessionBag.switchGateRef;
    const sendPrompt = sessionBag.sendPrompt;

    const holdSubmittedInput = (reason: string) => {
      heldSubmitRef.current = { raw, cmd, createdAt: Date.now() };
      setInput((cur: any) => {
        const curText = String(cur || '').trim();
        return curText ? cur : raw;
      });
      setShowSlash(false);
      if (typeof setStreaming === 'function') setStreaming(false);
      streamBufferRef.current = '';
      if (typeof setStreamText === 'function') setStreamText('');
      setFeed((f: any) => [...f, { kind: 'agent', text: reason, createdAt: Date.now() }]);
    };

    // Race fix: read the synchronous gate FIRST. workflowReady is React state and
    // lags one commit behind beginWorkflowReady's setWorkflowReady(); the gate was
    // set in the SAME tick, so it reports "switching" immediately even when the
    // closed-over workflowReady is still the stale null. Either signal holds the
    // input via the EXISTING held-input mechanism (heldSubmitRef), which the
    // replay effect below flushes once the switch settles.
    const switchingNow = !!(switchGateRef && switchGateRef.current && switchGateRef.current.isSwitching());
    if (workflowReady || switchingNow) {
      const holdTarget = (workflowReady && workflowReady.target) || workflow || 'workflow';
      holdSubmittedInput(`Input held. Waiting for \`${holdTarget}\` to be ready; it will send automatically if unchanged.`);
      return;
    }

    // Cleared to send: record history, clear the box, and dispatch to the backend.
    recordInputHistory(raw);
    setInput((cur: any) => {
      const curText = String(cur || '').trim();
      if (!curText || curText === raw) return '';
      if (cmd != null && curText.startsWith('/')) return '';
      return cur;
    });
    setShowSlash(false);
    setFeed((f: any) => [...f, { kind: 'user', text: raw, createdAt: Date.now() }]);
    if (typeof sendPrompt === 'function') sendPrompt(raw);
  }, [input, workflow, recordInputHistory, setFeed, setInput, setShowSlash, streamBufferRef, sessionBag]);

  // Held-input replay: when the switch settles (workflowReady cleared) and the
  // backend is open, re-fire the held prompt if the user hasn't changed it. This
  // is the EXISTING replay mechanism (heldSubmitRef) reused — no parallel queue.
  useEffect(() => {
    const held = heldSubmitRef.current;
    if (!held || sessionBag.workflowReady) return undefined;
    const state = w.backend && typeof w.backend.getConnectionState === 'function'
      ? w.backend.getConnectionState()
      : backendState;
    if (state !== 'open') return undefined;
    if (String(input || '').trim() !== held.raw) {
      heldSubmitRef.current = null;
      return undefined;
    }
    const timer = setTimeout(() => {
      const latest = heldSubmitRef.current;
      if (!latest || latest.raw !== held.raw) return;
      if (String(input || '').trim() !== latest.raw) {
        heldSubmitRef.current = null;
        return;
      }
      heldSubmitRef.current = null;
      submitMsg(latest.cmd ?? latest.raw);
    }, 80);
    return () => clearTimeout(timer);
  }, [backendState, input, sessionBag.workflowReady, submitMsg]);

  return {
    // telemetry / backend
    backendState, setBackendState,
    commandBusy, setCommandBusy,
    workspaceTelemetry, setWorkspaceTelemetry,
    peerCount, setPeerCount,
    streamText, setStreamText,
    // tabs / preview / layout
    openFile, setOpenFile,
    rightTab, setRightTab,
    mainTab, setMainTab,
    previewPath, setPreviewPath,
    fileContextMenu, setFileContextMenu,
    gitShow, setGitShow,
    centerLayout, setCenterLayout,
    chatFeedSummary, setChatFeedSummary,
    // q&a
    qaState, setQaState, qaStateRef,
    qaHistory, setQaHistory,
    ssotApproval, setSsotApproval,
    ssotQa, setSsotQa,
    ssotQaSessions, setSsotQaSessions,
    visibleQaHistory, clearQaHistory,
    qaHistoryScope, qaHistoryMatchesScope,
    refreshSsotQa, refreshSsotQaSessions, activateSsotQaSession,
    flowMatchesCurrentSession, activateAskUserSession,
    pendingQcard, pendingQcardActiveTab, ssotQaBoardData,
    askSel, setAskSel,
    // input / history / slash / at
    input, setInput, heldSubmitRef,
    inputHistory, setInputHistory,
    inputHistoryIndexRef, inputHistoryDraftRef,
    replaceInputHistory, recordInputHistory,
    showSlash, setShowSlash,
    slashSel, setSlashSel,
    slashCommands, setSlashCommands,
    atQuery, atDirCache, setAtDirCache, atDirEntries, setAtDirEntries,
    fileMatches, filtered, acceptAtCompletion,
    showAt, setShowAt, atSel, setAtSel,
    submitMsg,
    // session-derived
    currentSession, activeIp, activeSsotIp,
    // tab visibility
    showQaTab, showSsotChecklistTab, showSsotImportExportTab,
    showSsotTab, showSsotDocTab, showSimSummaryTab, showDebugTab,
    showCoverageTab, workflowReportMeta, showWorkflowReportTab,
    // file tree
    filePanelIp, visibleFileTree, filePanelStatus, deleteIpTreeFile,
    // scm
    scmProvider, ScmTabComponent, scmTabLabel, showBuiltinGitTab,
  };
};
