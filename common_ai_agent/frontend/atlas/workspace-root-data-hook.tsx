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
  workspaceFetchWorkerSnapshot,
  INPUT_HISTORY_LIMIT,
  QA_HISTORY_LIMIT,
  QA_HISTORY_LEGACY_STORAGE_KEY,
} from './workspace-tool-theme';
import { useResizable, useVerticalResizable } from './workspace-resize-splitters';
import { WorkspaceChatPane, WorkspacePromptRow } from './workspace-root-render';
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
  workflowForExecMode,
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
    dir,
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
    streaming,
    setStreaming,
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

  // streaming is owned by the composer (shared with the session half) but the
  // ref-sync + window-broadcast side effects live here next to the chat feed,
  // exactly as the legacy closure had them (workspace.jsx L2739-L2747).
  useEffect(() => { streamingRef.current = streaming; }, [streaming, streamingRef]);
  useEffect(() => {
    try {
      window.ATLAS_AGENT_RUNNING = !!streaming;
      window.dispatchEvent(new CustomEvent('atlas-agent-running', {
        detail: { running: !!streaming },
      }));
    } catch (_) {}
  }, [streaming]);

  const [openFile, setOpenFile] = useState<any>(null);

  // ── Column widths (drag-resizable, persisted in localStorage) ───────
  // 0 = collapsed; any positive width is clamped to [min, max]. Ported
  // verbatim from workspace.jsx L2030-L2033 — the grid template reads
  // `${leftW}px ... ${rightW}px`, so an undefined width breaks the whole
  // 5-track layout.
  const [leftW,  setLeftW,  toggleLeft]  = useResizable(230, 'atlasLeftW',  160, 480, false);
  const [rightW, setRightW, toggleRight] = useResizable(360, 'atlasRightW', 260, 600);
  const [splitRightW, setSplitRightW] = useResizable(520, 'atlasSplitRightW', 300, 900, false);
  const [leftWorkflowH, setLeftWorkflowH, resetLeftWorkflowH] = useVerticalResizable(178, 'atlasLeftWorkflowH', 126, 540);

  // ── File-tree sort / expand / collapse state ────────────────────────
  // sort: 'name' (alphabetical, dirs first; default) or 'recent'.
  // expand: 'shallow' (top level only) or 'deep' (recursive descent).
  // Both persist across reloads (workspace.jsx L2060-L2085).
  const [fileSort, setFileSort] = useState<string>(() => {
    try { return localStorage.getItem('atlasFileSort') === 'recent' ? 'recent' : 'name'; }
    catch (_) { return 'name'; }
  });
  useEffect(() => {
    try { localStorage.setItem('atlasFileSort', fileSort); } catch (_) {}
  }, [fileSort]);
  const [fileExpand, setFileExpand] = useState<string>(() => {
    try { return localStorage.getItem('atlasFileExpand') === 'deep' ? 'deep' : 'shallow'; }
    catch (_) { return 'shallow'; }
  });
  useEffect(() => {
    try { localStorage.setItem('atlasFileExpand', fileExpand); } catch (_) {}
    if (w.atlasData && w.atlasData.refreshFileTree) {
      const scope = String(w.SCOPE_PATH || '').trim();
      if (scope && scope !== 'default') {
        w.atlasData.refreshFileTree(scope, { recursive: true });
      }
    }
  }, [fileExpand]);
  const [collapsedFileDirs, setCollapsedFileDirs] = useState<Set<string>>(() => new Set());

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

  // ── question card handlers ─────────────────────────────────────
  // Both single-question and batched (tabbed) flows share these helpers; in
  // batched mode they operate on the active tab's slice (states[active])
  // instead of the top-level opts/custom. Ported verbatim from
  // workspace.jsx L5324-L5645 — passed to AskUserPrompt / FeedEntry.
  const toggleOpt = (flowId: string, optId: string) => {
    const flow = w.QA_FLOWS[flowId];
    setQaState((s: any) => {
      const cur = s[flowId];
      if (cur.submitted) return s;
      if (cur.batched) {
        const idx = cur.active || 0;
        const q = flow.questions[idx];
        const tabState = cur.states[idx];
        let opts;
        if (q.kind === 'multi') {
          opts = tabState.opts.map((o: any) =>
            o.id === optId ? (o.locked ? o : { ...o, selected: !o.selected }) : o
          );
        } else {
          opts = tabState.opts.map((o: any) => ({ ...o, selected: o.id === optId }));
        }
        const states = cur.states.map((st: any, i: number) =>
          i === idx ? { ...st, opts } : st
        );
        return { ...s, [flowId]: { ...cur, states } };
      }
      let opts;
      if (flow.kind === 'multi') {
        opts = cur.opts.map((o: any) => o.id === optId ? (o.locked ? o : { ...o, selected: !o.selected }) : o);
      } else {
        opts = cur.opts.map((o: any) => ({ ...o, selected: o.id === optId }));
      }
      return { ...s, [flowId]: { ...cur, opts } };
    });
  };

  const setCustom = (flowId: string, val: string) => {
    setQaState((s: any) => {
      const cur = s[flowId];
      if (!cur) return s;
      if (cur.batched) {
        const idx = cur.active || 0;
        const states = cur.states.map((st: any, i: number) =>
          i === idx ? { ...st, custom: val } : st
        );
        return { ...s, [flowId]: { ...cur, states } };
      }
      return { ...s, [flowId]: { ...cur, custom: val } };
    });
  };

  const setActiveTab = (flowId: string, idx: number) => {
    setQaState((s: any) => {
      const cur = s[flowId];
      if (!cur || !cur.batched) return s;
      const flow = w.QA_FLOWS[flowId];
      const max = (flow.questions || []).length; // .length = Submit tab
      const next = Math.max(0, Math.min(max, idx));
      return { ...s, [flowId]: { ...cur, active: next } };
    });
  };

  const advanceBatchedQuestion = (flowId: string) => {
    setQaState((s: any) => {
      const cur = s[flowId];
      if (!cur || !cur.batched) return s;
      const flow = w.QA_FLOWS[flowId];
      const tabCount = (flow.questions || []).length;
      const active = cur.active || 0;
      const next = Math.max(0, Math.min(tabCount, active + 1));
      return { ...s, [flowId]: { ...cur, active: next } };
    });
  };

  // submitCard ships an ask_user answer back to the agent over the WS.
  // Batched flows package every per-tab answer into a single {answers: [...]}
  // payload so the backend resolves all of them in one round-trip — matches
  // the textual UI's batched ask_user.
  const submitCard = (flowId: string) => {
    // Functional updater so we always read the latest qaState — this matters
    // when a toggle was just queued (e.g. single-kind Enter = toggle+submit)
    // and we'd otherwise see pre-toggle state.
    let snapshot: any = null;
    setQaState((s: any) => {
      const st = s[flowId];
      if (!st || st.submitted) return s;
      if (w.backend) {
        if (st.batched) {
          const answers = (st.states || []).map((tab: any) => ({
            selected: tab.opts.filter((o: any) => o.selected).map((o: any) => o.id),
            custom: tab.custom || '',
          }));
          w.backend.send({ type: 'answer', flow_id: flowId, answers });
        } else {
          const selectedIds = st.opts.filter((o: any) => o.selected).map((o: any) => o.id);
          w.backend.send({
            type: 'answer',
            flow_id: flowId,
            selected: selectedIds,
            custom: st.custom || '',
          });
        }
      }
      // Build a serializable history snapshot of THIS submit so we can prepend
      // it to qaHistory after the state update flushes.
      try {
        const flow = w.QA_FLOWS && w.QA_FLOWS[flowId];
        if (flow) {
          const items = flow.batched
            ? (flow.questions || []).map((q: any, i: number) => {
                const tab = (st.states || [])[i] || { opts: [], custom: '' };
                return {
                  question: q.question || '',
                  kind: q.kind || 'single',
                  selected: tab.opts.filter((o: any) => o.selected)
                    .map((o: any) => ({ id: o.id, label: o.label })),
                  custom: tab.custom || '',
                };
              })
            : [{
                question: flow.question || '',
                kind: flow.kind || 'single',
                selected: (st.opts || []).filter((o: any) => o.selected)
                  .map((o: any) => ({ id: o.id, label: o.label })),
                custom: st.custom || '',
              }];
          snapshot = {
            flowId,
            ts: Date.now(),
            session: normalizeUiSession(flow.session || currentSession || w.ACTIVE_SESSION || ''),
            ip: String(flow.ip || ssotIpFromSession(flow.session || currentSession || w.ACTIVE_SESSION || '') || activeSsotIp() || '').trim(),
            workflow: flow.workflow || '',
            source: flow.source || '',
            items,
          };
        }
      } catch (_) {}
      return { ...s, [flowId]: { ...st, submitted: true } };
    });
    if (snapshot) {
      setQaHistory((h: any[]) => {
        if (h.length && h[0].flowId === snapshot.flowId) return h; // dedupe re-submits
        return [snapshot, ...h].slice(0, QA_HISTORY_LIMIT);
      });
    }
    setStreaming(true);  // agent resumes after receiving answer
  };

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

  // ── Brief live-worker strip for the orchestrator chat ───────────────────
  // Shows which workers the orchestrator currently has running, inline in the
  // chat (sourced from the same snapshot the Workers tab polls). Each chip is
  // a click-through to that worker's own session for full detail.
  // (workspace.jsx L5067-L5091)
  const [orchWorkers, setOrchWorkers] = useState<any[]>([]);
  useEffect(() => {
    const ip = String(activeIp || '').trim();
    if (String(workflow || '') !== 'orchestrator' || !ip || ip.toLowerCase() === 'default') {
      setOrchWorkers([]);
      return undefined;
    }
    let dead = false;
    const poll = async () => {
      if (dead || (typeof document !== 'undefined' && document.visibilityState === 'hidden')) return;
      try {
        const snap = await workspaceFetchWorkerSnapshot({ ip, activeOnly: true });
        if (dead) return;
        const all = Array.isArray(snap && snap.workers) ? snap.workers : [];
        setOrchWorkers(all.filter((wk: any) =>
          Number(wk.running_count || 0) > 0 ||
          Number(wk.pending_count || 0) > 0 ||
          Number(wk.queued_count || 0) > 0
        ));
      } catch (_) {}
    };
    poll();
    const t = setInterval(poll, 3000);
    return () => { dead = true; clearInterval(t); };
  }, [workflow, activeIp]);

  // ── Worker-session LIVE transcript poll ─────────────────────────────────
  // When viewing a worker session (not the orchestrator), surface the live
  // ReAct steps of the worker the orchestrator dispatched. Those steps are NOT
  // in this session's conversation.json (the worker writes elsewhere) — but the
  // worker agent-server exposes them via /api/job/{id}/log. We map
  // (ip, workflow) → running job_id through /api/pipeline/progress-debug, then
  // poll the job log and append new entries to the feed.
  // (workspace.jsx L5100-L5219)
  const workerLogJobRef = useRef<string>('');
  const workerLogSinceRef = useRef<number>(0);
  const workerLogSeenRef = useRef<Set<number>>(new Set());
  const workerLogAutoTabRef = useRef<string>('');
  const [workerProgress, setWorkerProgress] = useState<any>(null);
  useEffect(() => {
    const ip = String(activeIp || '').trim();
    const wf = String(workflow || '');
    if (!wf || wf === 'orchestrator' || !ip || ip.toLowerCase() === 'default') return undefined;
    workerLogJobRef.current = '';
    workerLogSinceRef.current = 0;
    workerLogSeenRef.current = new Set();
    setWorkerProgress(null);
    let dead = false;

    const appendLiveFeedEntries = sessionBag.appendLiveFeedEntries;

    const toEntry = (e: any, job: any = {}) => {
      const mapper = w.AtlasOrchestratorChatLogic?.feedEntryFromWorkerLogEntry;
      if (typeof mapper === 'function') return mapper(e, job);
      const type = String(e.type || e.role || '').toLowerCase();
      const text = String(e.content || '').trim();
      if (!text) return null;
      const createdAt = Number(e.timestamp || 0) * 1000 || 0;
      const worker = {
        job_id: String(job.job_id || ''),
        run_id: String(job.run_id || ''),
        workflow: String(job.workflow || job.stage_id || wf || ''),
        stage_id: String(job.stage_id || ''),
        status: String(job.status || ''),
        worker: String(job.worker || ''),
      };
      if (type === 'response' || type === 'assistant') return { kind: 'agent', text, createdAt, live: true, worker };
      if (type === 'action') return { kind: 'action', text, createdAt, live: true, worker };
      if (type === 'observation' || type === 'obs') return { kind: 'obs', text, createdAt, live: true, worker };
      // task / plan / context / system / thought → thought (truncate noisy context)
      return { kind: 'thought', text: text.length > 1200 ? text.slice(0, 1200) + ' …' : text, createdAt, live: true, worker };
    };

    const findJobId = async () => {
      try {
        const r = await fetch(`/api/pipeline/progress-debug?ip=${encodeURIComponent(ip)}`, { credentials: 'include', cache: 'no-store' });
        if (!r.ok) return '';
        const d = await r.json();
        const active = (d && d.worker && Array.isArray(d.worker.active)) ? d.worker.active
          : (d && Array.isArray(d.active)) ? d.active : [];
        const match = active.find((j: any) => String(j.workflow || '') === wf)
          || active.find((j: any) => String(j.stage_id || '') === wf)
          || active.find((j: any) => {
            const stageId = String(j.stage_id || '');
            return !!stageId && wf.startsWith(stageId);
          });
        return match ? String(match.job_id || '') : '';
      } catch (_) { return ''; }
    };

    const poll = async () => {
      if (dead || (typeof document !== 'undefined' && document.visibilityState === 'hidden')) return;
      try {
        if (!workerLogJobRef.current) {
          workerLogJobRef.current = await findJobId();
          if (!workerLogJobRef.current) return;
        }
        const jid = workerLogJobRef.current;
        const r = await fetch(`/api/job/${encodeURIComponent(jid)}/log?since=${workerLogSinceRef.current}`, { credentials: 'include', cache: 'no-store' });
        if (!r.ok) { if (r.status === 404) workerLogJobRef.current = ''; return; }
        const d = await r.json();
        const jb = d.job || {};
        setWorkerProgress({
          workflow: wf,
          status: String(d.status || jb.status || 'running'),
          startedAt: Number(jb.started_at || 0),
          iterations: Number(jb.iterations || 0),
        });
        const entries = Array.isArray(d.entries) ? d.entries : [];
        const fresh: any[] = [];
        let maxIdx = workerLogSinceRef.current;
        for (const e of entries) {
          const idx = Number(e.index);
          if (Number.isFinite(idx)) {
            if (workerLogSeenRef.current.has(idx)) continue;
            workerLogSeenRef.current.add(idx);
            if (idx + 1 > maxIdx) maxIdx = idx + 1;
          }
          const fe = toEntry(e, {
            ...jb,
            job_id: jb.job_id || jid,
            workflow: jb.workflow || wf,
            status: jb.status || d.status || '',
          });
          if (fe) fresh.push(fe);
        }
        workerLogSinceRef.current = maxIdx;
        if (fresh.length) {
          // Route through appendLiveFeedEntries so entries are `live`-stamped
          // and liveFeedStartedRef is set — otherwise a late conversation
          // hydration (empty conversation.json) would wipe them.
          if (typeof appendLiveFeedEntries === 'function') appendLiveFeedEntries(fresh);
          setStreaming((s: boolean) => (s ? false : s));
          // First live steps for this job → surface the CHAT tab so the user
          // who clicked the strip chip actually sees the worker working.
          // Only override the workflow-default tabs; never fight a manual pick.
          if (workerLogAutoTabRef.current !== jid) {
            workerLogAutoTabRef.current = jid;
            setMainTab((prev: string) => (
              prev === 'checklist' || prev === 'sim_summary' ||
              prev === 'coverage' || prev === 'workflow_report' || prev === 'debug'
            ) ? 'chat' : prev);
          }
        }
        // job finished → stop chasing it (next active job, if any, re-resolves)
        if (d.status && ['passed', 'failed', 'error', 'done', 'completed', 'cancelled'].includes(String(d.status))) {
          workerLogJobRef.current = '';
        }
      } catch (_) {}
    };
    poll();
    const t = setInterval(poll, 1500);
    return () => { dead = true; clearInterval(t); };
  }, [workflow, activeIp]);

  // ── input history navigation + textarea key handling ────────────────────
  // (workspace.jsx L5221-L5318) — used by the bound renderPromptRow textarea.
  const navigateInputHistory = (delta: number): boolean => {
    if (!inputHistory.length) return false;
    let idx = inputHistoryIndexRef.current;
    if (idx === null || idx === undefined) {
      if (delta > 0) return false;
      inputHistoryDraftRef.current = input;
      idx = inputHistory.length - 1;
    } else {
      idx += delta;
    }
    if (idx < 0) idx = 0;
    if (idx >= inputHistory.length) {
      inputHistoryIndexRef.current = null;
      setInput(inputHistoryDraftRef.current || '');
      return true;
    }
    inputHistoryIndexRef.current = idx;
    setInput(inputHistory[idx] || '');
    setShowSlash(false);
    setShowAt(false);
    return true;
  };

  const onPromptKey = (e: any) => {
    if (showSlash) {
      if (e.key === 'ArrowDown') { e.preventDefault(); setSlashSel((s: number) => Math.min(s + 1, filtered.length - 1)); return; }
      if (e.key === 'ArrowUp')   { e.preventDefault(); setSlashSel((s: number) => Math.max(s - 1, 0)); return; }
      if (e.key === 'Tab' || e.key === 'Enter') {
        if (filtered[slashSel]) {
          e.preventDefault();
          if (e.key === 'Enter') submitMsg(filtered[slashSel].cmd);
          else setInput(filtered[slashSel].cmd + ' ');
          return;
        }
      }
      if (e.key === 'Escape') { e.preventDefault(); setShowSlash(false); return; }
    }
    if (showAt) {
      if (e.key === 'ArrowDown') { e.preventDefault(); setAtSel((s: number) => Math.min(s + 1, fileMatches.length - 1)); return; }
      if (e.key === 'ArrowUp')   { e.preventDefault(); setAtSel((s: number) => Math.max(s - 1, 0)); return; }
      if (e.key === 'Tab' || e.key === 'Enter') {
        if (fileMatches[atSel]) {
          e.preventDefault();
          acceptAtCompletion(fileMatches[atSel]);
          return;
        }
      }
      if (e.key === 'Escape') { e.preventDefault(); setShowAt(false); return; }
    }
    if (e.key === 'ArrowUp') {
      if (navigateInputHistory(-1)) {
        e.preventDefault();
        requestAnimationFrame(() => {
          const el = inputRef.current;
          if (el) el.setSelectionRange(el.value.length, el.value.length);
        });
      }
      return;
    }
    if (e.key === 'ArrowDown') {
      if (navigateInputHistory(1)) {
        e.preventDefault();
        requestAnimationFrame(() => {
          const el = inputRef.current;
          if (el) el.setSelectionRange(el.value.length, el.value.length);
        });
      }
      return;
    }
    // Plain Enter submits. Shift+Enter and Alt/Option+Enter both insert a
    // literal newline so multi-line prompts compose naturally.
    if (e.key === 'Enter') {
      if (e.altKey) {
        e.preventDefault();
        const el = e.target;
        const lo = el.selectionStart;
        const hi = el.selectionEnd;
        const next = el.value.slice(0, lo) + '\n' + el.value.slice(hi);
        setInput(next);
        requestAnimationFrame(() => {
          el.selectionStart = el.selectionEnd = lo + 1;
          el.style.height = 'auto';
          el.style.height = Math.min(el.scrollHeight, 192) + 'px';
        });
        return;
      }
      if (!e.shiftKey) {
        e.preventDefault();
        submitMsg();
      }
      // Shift+Enter: textarea native handles newline; onChange fires auto-grow.
    }
  };

  // ── bound render helpers ────────────────────────────────────────────────
  // The composer wants render FUNCTIONS (renderChatPane/renderPromptRow) that
  // close over the live feed/input/stream state. The presentational bodies
  // were extracted to workspace-root-render.tsx (WorkspaceChatPane /
  // WorkspacePromptRow); here we adapt them by closing over current state and
  // forwarding it as props — matching workspace.jsx L5745-L5750 / L5751-L6005.
  const renderChatPane = (style: any = {}) => (
    <WorkspaceChatPane
      feedRef={feedRef}
      streamText={streamText}
      style={style}
      feedEntriesProps={{
        feed,
        qaState,
        chatFeedSummary,
        toggleOpt,
        setCustom,
        submitCard,
        dir,
      }}
    />
  );
  const renderPromptRow = () => (
    <WorkspacePromptRow
      workflow={workflow}
      activeIp={activeIp}
      feed={feed}
      orchWorkers={orchWorkers}
      workerProgress={workerProgress}
      input={input}
      setInput={setInput}
      inputRef={inputRef}
      inputRouteState={sessionBag.inputRouteState}
      inputRouteRef={sessionBag.inputRouteRef}
      inputHistoryIndexRef={inputHistoryIndexRef}
      inputHistoryDraftRef={inputHistoryDraftRef}
      onKey={onPromptKey}
      pendingQcard={pendingQcard}
      workflowReady={sessionBag.workflowReady}
      atlasUiOrchestratorMode={atlasUiOrchestratorMode}
      workflowForExecMode={workflowForExecMode}
      defaultWorkflowForExecMode={defaultWorkflowForExecMode}
    />
  );

  return {
    // telemetry / backend
    backendState, setBackendState,
    commandBusy, setCommandBusy,
    workspaceTelemetry, setWorkspaceTelemetry,
    peerCount, setPeerCount,
    streamText, setStreamText,
    // streaming (composer-owned; re-surfaced for the JSX destructure + spinner)
    streaming, setStreaming,
    // column widths + collapse toggles
    leftW, setLeftW, toggleLeft,
    rightW, setRightW, toggleRight,
    splitRightW, setSplitRightW,
    leftWorkflowH, setLeftWorkflowH, resetLeftWorkflowH,
    // tabs / preview / layout
    openFile, setOpenFile,
    rightTab, setRightTab,
    mainTab, setMainTab,
    previewPath, setPreviewPath,
    fileContextMenu, setFileContextMenu,
    gitShow, setGitShow,
    centerLayout, setCenterLayout,
    chatFeedSummary, setChatFeedSummary,
    // file-tree sort / expand / collapse
    fileSort, setFileSort,
    fileExpand, setFileExpand,
    collapsedFileDirs, setCollapsedFileDirs,
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
    // q&a card handlers (passed to AskUserPrompt / FeedEntry)
    toggleOpt, setCustom, submitCard, setActiveTab, advanceBatchedQuestion,
    // input / history / slash / at
    input, setInput, heldSubmitRef,
    inputRef,
    inputHistory, setInputHistory,
    inputHistoryIndexRef, inputHistoryDraftRef,
    replaceInputHistory, recordInputHistory,
    navigateInputHistory, onPromptKey,
    showSlash, setShowSlash,
    slashSel, setSlashSel,
    slashCommands, setSlashCommands,
    atQuery, atDirCache, setAtDirCache, atDirEntries, setAtDirEntries,
    fileMatches, filtered, acceptAtCompletion,
    showAt, setShowAt, atSel, setAtSel,
    submitMsg,
    // live worker strips / progress
    orchWorkers, setOrchWorkers,
    workerProgress, setWorkerProgress,
    // bound render helpers (close over feed/input/stream state)
    feedRef,
    renderChatPane, renderPromptRow,
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
