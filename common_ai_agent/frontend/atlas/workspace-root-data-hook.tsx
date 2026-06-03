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

import { type SetStateAction, useState, useEffect, useRef, useCallback, useMemo, useReducer } from 'react';

import {
  refreshChatSession,
  trimAtlasFeedState,
  atlasBootScmProvider,
  atlasResolveScmTab,
  atlasScmTabLabel,
  workspaceFetchWorkerSnapshot,
  atlasIsIterationMarkerText,
  INPUT_HISTORY_LIMIT,
  QA_HISTORY_LIMIT,
  QA_HISTORY_LEGACY_STORAGE_KEY,
} from './workspace-tool-theme';
import { useResizable, useVerticalResizable } from './workspace-resize-splitters';
import { WorkspaceChatPane, WorkspacePromptRow, type WorkspacePromptKeyResult } from './workspace-root-render';
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

const askText = (value: any, fallback = ''): string => {
  const text = String(value ?? '').trim();
  return text || fallback;
};

const askNumber = (value: any, fallback: number): number => {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
};

type LiveLlmRuntime = {
  model: string;
  reasoningEffort: string;
};

const liveLlmRuntimeFrom = (message: any): LiveLlmRuntime => ({
  model: String(
    message?.model
    ?? message?.active_model
    ?? message?.activeModel
    ?? message?.runtime_model
    ?? '',
  ).trim(),
  reasoningEffort: String(
    message?.reasoning_effort
    ?? message?.reasoningEffort
    ?? message?.effort
    ?? '',
  ).trim(),
});

const hasLiveLlmRuntime = (runtime: LiveLlmRuntime): boolean =>
  !!(runtime.model || runtime.reasoningEffort);

const askKind = (value: any): string => {
  const kind = String(value || '').toLowerCase();
  if (kind === 'multi') return 'multi';
  if (kind === 'input' || kind === 'text') return 'input';
  return 'single';
};

const askOptionFrom = (option: any, index: number): any => {
  const obj = option && typeof option === 'object' ? option : { label: option };
  const id = askText(obj.id ?? obj.value ?? obj.key ?? obj.label, String(index + 1));
  const label = askText(obj.label ?? obj.text ?? obj.title ?? obj.value, id);
  return {
    ...obj,
    id,
    label,
    detail: askText(obj.detail ?? obj.description ?? obj.hint),
    selected: !!obj.selected || !!obj.default || !!obj.locked,
    locked: !!obj.locked,
  };
};

const askQuestionFrom = (raw: any, index: number): any => {
  const q = raw && typeof raw === 'object' ? raw : { question: raw };
  const options = Array.isArray(q.options)
    ? q.options.map((option: any, optIndex: number) => askOptionFrom(option, optIndex))
    : [];
  return {
    ...q,
    id: askText(q.id ?? q.decision_key ?? q.key, `q${index + 1}`),
    question: askText(q.question ?? q.prompt ?? q.text, 'Answer required'),
    subtitle: askText(q.subtitle ?? q.decision_label ?? q.label),
    kind: askKind(q.kind),
    multiline: !!q.multiline,
    placeholder: askText(q.placeholder),
    options,
  };
};

const buildAskUserFlow = (message: any): any => {
  const flowId = askText(message?.flow_id ?? message?.flowId);
  if (!flowId) return null;
  const session = normalizeUiSession(message?.session ?? message?.session_id ?? message?.namespace ?? '');
  const ip = askText(message?.ip ?? ssotIpFromSession(session));
  const wf = askText(message?.workflow ?? workflowFromSession(session));
  const source = askText(message?.source);
  const stage = askText(message?.stage ?? wf, 'ask_user');
  const questions = Array.isArray(message?.questions)
    ? message.questions.map((q: any, index: number) => askQuestionFrom(q, index))
    : [];

  if (questions.length) {
    return {
      flowId,
      flow: {
        flow_id: flowId,
        batched: true,
        questions,
        stage,
        step: askNumber(message?.step, 1),
        total: askNumber(message?.total, questions.length),
        session,
        ip,
        workflow: wf,
        source,
      },
      state: {
        batched: true,
        active: 0,
        states: questions.map((q: any) => ({
          opts: (q.options || []).map((option: any) => ({ ...option })),
          custom: '',
        })),
      },
    };
  }

  const single = askQuestionFrom({
    question: message?.question,
    prompt: message?.prompt,
    text: message?.text,
    subtitle: message?.subtitle,
    kind: message?.kind,
    multiline: message?.multiline,
    placeholder: message?.placeholder,
    options: message?.options,
  }, 0);
  return {
    flowId,
    flow: {
      flow_id: flowId,
      question: single.question,
      subtitle: single.subtitle,
      kind: single.kind,
      multiline: single.multiline,
      placeholder: single.placeholder,
      options: single.options,
      stage,
      step: askNumber(message?.step, 1),
      total: askNumber(message?.total, 1),
      session,
      ip,
      workflow: wf,
      source,
    },
    state: {
      opts: single.options.map((option: any) => ({ ...option })),
      custom: '',
    },
  };
};

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
    // Composer-owned (lifted into workspace-root.tsx). Previously this hook
    // OWNED the useState for both, but useWorkspaceSession needs their setters
    // and runs first, so the composer now owns them and threads them into both
    // hooks. Re-surfaced in this hook's return for the JSX destructure.
    streamText,
    setStreamText,
    mainTab,
    setMainTab,
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
    // submitMsg dispatch-hub primitives (now typed; no `deps as any` cast).
    workflowReady,
    switchGateRef,
    setWorkflowReady,
    clearWorkflowReadyTimers,
    workflowReadySeqRef,
    sendPrompt,
    appendLiveFeedEntries,
    inputRouteState,
    inputRouteRef,
    setIntent,
    switchToDefaultSession,
    switchWorkflow,
  } = deps;

  // ── Telemetry: /healthz poll loop ───────────────────────────────
  const [backendState, setBackendState] = useState<any>(() => {
    if (!w.backend) return 'missing';
    return w.backend.getConnectionState ? w.backend.getConnectionState() : 'connecting';
  });
  const [commandBusy, setCommandBusy] = useState<any>(null);
  const [liveLlmRuntime, setLiveLlmRuntime] = useState<LiveLlmRuntime>({
    model: '',
    reasoningEffort: '',
  });
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
  // streamText is composer-owned now (destructured from deps above).
  const feedPinnedToBottomRef = useRef<boolean>(true);
  const feedScrollFrameRef = useRef<number | null>(null);
  const feedScrollFallbackTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const streamTextFrameRef = useRef<number | null>(null);
  const streamTextFallbackTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const cancelStreamTextDisplay = useCallback(() => {
    if (streamTextFrameRef.current !== null) {
      if (typeof window.cancelAnimationFrame === 'function') {
        window.cancelAnimationFrame(streamTextFrameRef.current);
      }
      streamTextFrameRef.current = null;
    }
    if (streamTextFallbackTimerRef.current !== null) {
      clearTimeout(streamTextFallbackTimerRef.current);
      streamTextFallbackTimerRef.current = null;
    }
  }, []);

  const scheduleStreamTextDisplay = useCallback(() => {
    if (streamTextFrameRef.current !== null || streamTextFallbackTimerRef.current !== null) return;
    if (typeof window.requestAnimationFrame === 'function') {
      streamTextFrameRef.current = window.requestAnimationFrame(() => {
        streamTextFrameRef.current = null;
        setStreamText(streamBufferRef.current);
      });
      return;
    }
    streamTextFallbackTimerRef.current = setTimeout(() => {
      streamTextFallbackTimerRef.current = null;
      setStreamText(streamBufferRef.current);
    }, 16);
  }, [setStreamText, streamBufferRef]);

  useEffect(() => () => {
    cancelStreamTextDisplay();
  }, [cancelStreamTextDisplay]);

  const cancelFeedScrollRequest = useCallback(() => {
    if (feedScrollFrameRef.current !== null) {
      if (typeof window.cancelAnimationFrame === 'function') {
        window.cancelAnimationFrame(feedScrollFrameRef.current);
      }
      feedScrollFrameRef.current = null;
    }
    if (feedScrollFallbackTimerRef.current !== null) {
      clearTimeout(feedScrollFallbackTimerRef.current);
      feedScrollFallbackTimerRef.current = null;
    }
  }, []);

  useEffect(() => () => {
    cancelFeedScrollRequest();
  }, [cancelFeedScrollRequest]);

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
  // mainTab is composer-owned now (destructured from deps above).
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
  const [inputResetToken, setInputResetToken] = useState<number>(0);
  const replaceInput = useCallback((value: SetStateAction<string>) => {
    setInput(value);
    setInputResetToken((token: number) => token + 1);
  }, []);
  const heldSubmitRef = useRef<any>(null);
  const submittedInputConsumedRef = useRef<boolean>(false);
  // BUG A: when the held-input replay re-fires an ack-miss hold, this carries the
  // ORIGINAL send's msg_id so the re-entered submitMsg threads it into sendPrompt
  // (re-send under the same id → backend has_msg_id dedup collapses the duplicate
  // instead of executing the prompt twice). Consumed-and-cleared at the sendPrompt
  // call sites; null for every non-replay submit.
  const replayMsgIdRef = useRef<any>(null);
  // Optimistic run-start arming: set true after a confirmed prompt send so the
  // agent_state handler doesn't swallow the backend's first running:false before
  // the agent actually starts. (workspace.jsx L2737-L2738 component-scope refs.)
  const awaitingRunStartRef = useRef<boolean>(false);
  const backendRunStartedRef = useRef<boolean>(false);
  const latencyStatusRef = useRef<{ msgId: any } | null>(null);
  const latencyTimerRef = useRef<any>(null);

  useEffect(() => () => {
    try {
      if (latencyTimerRef.current) clearTimeout(latencyTimerRef.current);
    } catch (_) {}
  }, []);

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
        replaceInput(next);
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

  useEffect(() => {
    const handler = (ev: any) => {
      try {
        const text = String(ev?.detail?.text || '').trimEnd();
        if (!text) return;
        replaceInput(text);
        setMainTab('chat');
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
    window.addEventListener('atlas-ssot-doc-comment', handler);
    return () => window.removeEventListener('atlas-ssot-doc-comment', handler);
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

  const eventMatchesCurrentSession = useCallback((m: any, opts: { requireSession?: boolean } = {}) => {
    const eventSession = normalizeUiSession((m && (m.session_id || m.session || m.namespace)) || '');
    const active = normalizeUiSession(w.ACTIVE_SESSION || activeSessionRef.current || currentSession || '');
    if (!active) return !opts.requireSession;
    if (!eventSession) return !opts.requireSession;
    if (eventSession === active) return true;
    const eventParts = eventSession.split('/').filter(Boolean);
    const activeParts = active.split('/').filter(Boolean);
    const minLen = Math.min(eventParts.length, activeParts.length);
    return minLen >= 2 && eventParts.slice(-minLen).join('/') === activeParts.slice(-minLen).join('/');
  }, [activeSessionRef, currentSession]);

  const parkLiveStream = useCallback(() => {
    cancelStreamTextDisplay();
    const text = String(streamBufferRef.current || '').replace(/\u0000/g, '');
    if (text.trim()) {
      appendLiveFeedEntries({ kind: 'agent', text, createdAt: Date.now(), live: true });
    }
    streamBufferRef.current = '';
    setStreamText('');
  }, [appendLiveFeedEntries, cancelStreamTextDisplay, setStreamText, streamBufferRef]);

  useEffect(() => {
    if (!w.backend || typeof w.backend.subscribe !== 'function') return undefined;
    const subs: Array<(() => void) | undefined> = [];
    const finishRun = () => {
      parkLiveStream();
      setStreaming(false);
      setLiveLlmRuntime({ model: '', reasoningEffort: '' });
      awaitingRunStartRef.current = false;
      backendRunStartedRef.current = false;
      setCommandBusy(null);
    };
    try {
      subs.push(w.backend.subscribe('token', (m: any) => {
        if (!eventMatchesCurrentSession(m)) return;
        const runtime = liveLlmRuntimeFrom(m);
        if (hasLiveLlmRuntime(runtime)) setLiveLlmRuntime(runtime);
        const text = String((m && (m.text ?? m.token ?? m.content)) || '').replace(/\u0000/g, '');
        if (!text) return;
        const controlPlaneToken = !!(m && (
          m.control === true ||
          m.control_plane === true ||
          m.stream === false ||
          m.source === 'api/session/activate'
        ));
        streamBufferRef.current += text;
        scheduleStreamTextDisplay();
        if (!controlPlaneToken) setStreaming(true);
      }));
      subs.push(w.backend.subscribe('reasoning', (m: any) => {
        if (!eventMatchesCurrentSession(m)) return;
        const text = String((m && m.text) || '').trim();
        if (text) appendLiveFeedEntries({ kind: 'thought', text, createdAt: Date.now(), live: true });
      }));
      subs.push(w.backend.subscribe('tool', (m: any) => {
        if (!eventMatchesCurrentSession(m)) return;
        const text = String((m && m.text) || '').trim();
        if (!text) return;
        parkLiveStream();
        appendLiveFeedEntries({
          kind: atlasIsIterationMarkerText(text) ? 'iter_marker' : 'action',
          text,
          tool: (m && m.tool) || '',
          createdAt: Date.now(),
          live: true,
        });
      }));
      subs.push(w.backend.subscribe('tool_result', (m: any) => {
        if (!eventMatchesCurrentSession(m)) return;
        const text = String((m && (m.text || m.content)) || '').trim();
        if (text) appendLiveFeedEntries({ kind: 'obs', text, tool: (m && m.tool) || '', createdAt: Date.now(), live: true });
      }));
      subs.push(w.backend.subscribe('slash_output', (m: any) => {
        if (!eventMatchesCurrentSession(m)) return;
        const text = String((m && m.text) || '').trim();
        if (!text) return;
        parkLiveStream();
        appendLiveFeedEntries({ kind: 'agent', text, createdAt: Date.now(), live: true });
        setCommandBusy(null);
      }));
      subs.push(w.backend.subscribe('flush', (m: any) => {
        if (!eventMatchesCurrentSession(m)) return;
        parkLiveStream();
      }));
      subs.push(w.backend.subscribe('context', (m: any) => {
        if (!eventMatchesCurrentSession(m)) return;
        const runtime = liveLlmRuntimeFrom(m);
        if (hasLiveLlmRuntime(runtime)) setLiveLlmRuntime(runtime);
      }));
      subs.push(w.backend.subscribe('done', (m: any) => {
        if (!eventMatchesCurrentSession(m)) return;
        finishRun();
      }));
      subs.push(w.backend.subscribe('agent_state', (m: any) => {
        if (!eventMatchesCurrentSession(m)) return;
        const controlPlaneState = !!(m && (
          m.control === true ||
          m.control_plane === true ||
          m.stream === false ||
          m.source === 'api/session/activate'
        ));
        if (m && m.running === true) {
          if (controlPlaneState) return;
          const runtime = liveLlmRuntimeFrom(m);
          if (hasLiveLlmRuntime(runtime)) setLiveLlmRuntime(runtime);
          backendRunStartedRef.current = true;
          setStreaming(true);
          return;
        }
        if (m && m.running === false) {
          finishRun();
        }
      }));
      subs.push(w.backend.subscribe('error', (m: any) => {
        if (!eventMatchesCurrentSession(m)) return;
        const message = String((m && (m.message || m.error)) || '').trim();
        if (message) appendLiveFeedEntries({ kind: 'agent', text: `[error] ${message}`, createdAt: Date.now(), live: true });
        finishRun();
      }));
    } catch (_) {}
    return () => {
      subs.forEach((unsub) => { try { if (unsub) unsub(); } catch (_) {} });
    };
  }, [
    appendLiveFeedEntries,
    eventMatchesCurrentSession,
    parkLiveStream,
    scheduleStreamTextDisplay,
    setStreamText,
    setStreaming,
    streamBufferRef,
  ]);

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
      // SERVER-DRIVEN SWITCH GATE REOPEN (the active-blocker fix).
      // The client switch path (switchWorkflow -> beginWorkflowReady ->
      // finishWorkflowReady) is the ONLY path that drives the synchronous
      // switch-gate ready again. A SERVER-announced workflow switch (surfaced as
      // "Workflow switched to X (was Y)") reaches the Workspace ONLY through this
      // atlas-session-switched handler, which previously updated UI state but
      // never touched the gate. If the gate is still 'switching' (e.g. a CLIENT
      // beginSwitch is in flight and the server now confirms, OR a stale
      // overlay), markReady() never fires and the first prompt typed after the
      // switch is HELD forever (drain only runs once the gate is ready AND the
      // overlay clears). Reopen the gate here exactly once and clear the overlay
      // so the held-input replay effect drains in FIFO order.
      const gate = switchGateRef && switchGateRef.current;
      if (gate && typeof gate.isSwitching === 'function' && gate.isSwitching()) {
        // Bump the seq FIRST so any in-flight stale client dismiss/fail timer
        // (which is seq-guarded against workflowReadySeqRef.current) becomes a
        // no-op and cannot re-close or re-open the gate behind us — keeping the
        // single markReady() below authoritative.
        if (workflowReadySeqRef && workflowReadySeqRef.current != null) {
          workflowReadySeqRef.current = (Number(workflowReadySeqRef.current) || 0) + 1;
        }
        if (typeof clearWorkflowReadyTimers === 'function') clearWorkflowReadyTimers();
        // markReady() preserves held pending for the replay drain; fires once.
        if (typeof gate.markReady === 'function') gate.markReady();
        // Clear the overlay so the held-input replay effect (gated on
        // !workflowReady) can fire and drain the FIFO.
        if (typeof setWorkflowReady === 'function') setWorkflowReady(null);
      }
    };
    window.addEventListener('atlas-session-switched', onSessionSwitched);
    return () => window.removeEventListener('atlas-session-switched', onSessionSwitched);
  }, [activeIp, setOrchestratorInputRoute, setWorkflowDispatchInputRoute, switchGateRef, setWorkflowReady, clearWorkflowReadyTimers, workflowReadySeqRef]);

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
  }, [centerLayout, mainTab, _qcardActiveFlow, _qcardSubmitted, setMainTab, workflow]);

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
    requestFeedScrollToBottom();
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
      replaceInput(before + '@' + parent + entry.name + '/' + after);
    } else {
      replaceInput(before + '@' + fullParent + entry.name + ' ' + after);
      setShowAt(false);
    }
  };

  const updateFeedPinnedToBottom = useCallback(() => {
    const el = feedRef.current;
    if (!el) return;
    const distance = Number(el.scrollHeight || 0) - Number(el.scrollTop || 0) - Number(el.clientHeight || 0);
    feedPinnedToBottomRef.current = distance <= 96;
  }, [feedRef]);

  const requestFeedScrollToBottom = useCallback(() => {
    feedPinnedToBottomRef.current = true;
    if (feedScrollFrameRef.current !== null || feedScrollFallbackTimerRef.current !== null) return;
    const run = () => {
      feedScrollFrameRef.current = null;
      if (feedScrollFallbackTimerRef.current !== null) {
        clearTimeout(feedScrollFallbackTimerRef.current);
        feedScrollFallbackTimerRef.current = null;
      }
      if (!feedPinnedToBottomRef.current) return;
      const el = feedRef.current;
      if (!el) return;
      el.scrollTop = el.scrollHeight;
    };
    if (typeof window.requestAnimationFrame === 'function') {
      feedScrollFrameRef.current = window.requestAnimationFrame(run);
      return;
    }
    feedScrollFallbackTimerRef.current = setTimeout(run, 16);
  }, [feedRef]);

  useEffect(() => {
    if (!feedPinnedToBottomRef.current) return;
    requestFeedScrollToBottom();
  }, [feed, streamText, mainTab, requestFeedScrollToBottom]);

  useEffect(() => {
    const el = feedRef.current;
    if (!el || typeof ResizeObserver === 'undefined') return undefined;
    const content = el.querySelector('[data-workspace-chat-content="true"]');
    if (!content) return undefined;
    const observer = new ResizeObserver(() => {
      if (feedPinnedToBottomRef.current) requestFeedScrollToBottom();
    });
    observer.observe(content);
    return () => observer.disconnect();
  }, [feedRef, mainTab, requestFeedScrollToBottom]);

  useEffect(() => {
    if (!w.backend || typeof w.backend.subscribe !== 'function') return undefined;
    const unsubAsk = w.backend.subscribe('ask_user', (message: any) => {
      const built = buildAskUserFlow(message);
      if (!built) return;
      const eventSession = normalizeUiSession(
        message?.session_id || message?.session || message?.namespace || built.flow.session || '',
      );
      const eventIp = askText(message?.ip ?? built.flow.ip ?? ssotIpFromSession(eventSession));
      const eventWorkflow = askText(message?.workflow ?? built.flow.workflow ?? workflowFromSession(eventSession));
      if (eventSession && !eventMatchesCurrentSession(message)) {
        activateAskUserSession(eventSession, eventIp, eventWorkflow);
      }
      w.QA_FLOWS = w.QA_FLOWS || {};
      w.QA_FLOWS[built.flowId] = built.flow;
      liveFeedStartedRef.current = true;
      feedPinnedToBottomRef.current = true;
      setQaState((state: any) => {
        const cur = state[built.flowId];
        if (cur && cur.submitted) return state;
        return { ...state, [built.flowId]: built.state };
      });
      setFeed((items: any) => {
        const list = Array.isArray(items) ? items : [];
        if (list.some((entry: any) => entry?.kind === 'qcard' && entry.flowId === built.flowId)) {
          return items;
        }
        return trimAtlasFeedState([
          ...list,
          { kind: 'qcard', flowId: built.flowId, createdAt: Date.now(), live: true },
        ]);
      });
      if (centerLayout === 'tabbed') setMainTab('qa');
      requestFeedScrollToBottom();
    });
    const closePending = (message: any) => {
      const flowId = askText(message?.flow_id ?? message?.flowId);
      if (!flowId) return;
      setQaState((state: any) => {
        const cur = state[flowId];
        if (!cur || cur.submitted) return state;
        return { ...state, [flowId]: { ...cur, submitted: true } };
      });
    };
    const unsubAnswered = w.backend.subscribe('ask_user_answered', closePending);
    const unsubClosed = w.backend.subscribe('ask_user_closed', closePending);
    return () => {
      try { if (unsubAsk) unsubAsk(); } catch (_) {}
      try { if (unsubAnswered) unsubAnswered(); } catch (_) {}
      try { if (unsubClosed) unsubClosed(); } catch (_) {}
    };
  }, [
    activateAskUserSession,
    centerLayout,
    eventMatchesCurrentSession,
    feedRef,
    liveFeedStartedRef,
    requestFeedScrollToBottom,
    setFeed,
    setMainTab,
  ]);

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

  // Commands that put the banner into a transient "busy" state while the
  // backend processes them (workspace.jsx L3793-L3799).
  const slashBusyForRaw = (value: any) => {
    const head = String(value || '').trim().split(/\s+/, 1)[0].toLowerCase();
    if (head === '/compact' || head === '/co') {
      return { kind: 'compact', text: 'Compacting history' };
    }
    return null;
  };

  // ── ask_user text-answer helpers (workspace.jsx L5371-L5463) ────────────
  // Parse a plain chat message into an ask_user answer when a qcard is open, so
  // the user can answer by typing instead of clicking. Ported verbatim.
  const matchAnswerToken = (raw: any, opts: any[]) => {
    const text = String(raw || '').trim();
    if (!text) return null;
    if (/^\d+$/.test(text)) {
      const idx = parseInt(text, 10) - 1;
      return opts[idx] || null;
    }
    const low = text.toLowerCase();
    return opts.find((o: any) =>
      String(o.id || '').toLowerCase() === low ||
      String(o.label || '').toLowerCase() === low
    ) || null;
  };

  const parseTextAnswer = (raw: any, question: any, opts: any[]) => {
    const text = String(raw || '').trim();
    const kind = question?.kind === 'multi' ? 'multi'
      : question?.kind === 'input' ? 'input'
      : 'single';
    if (!text || kind === 'input' || !opts.length) {
      return { selected: [] as any[], custom: text };
    }
    if (kind === 'multi') {
      const tokens = text.split(/[,\s]+/).map((x: string) => x.trim()).filter(Boolean);
      const selected: any[] = [];
      const unmatched: any[] = [];
      for (const token of tokens) {
        const match = matchAnswerToken(token, opts);
        if (match) selected.push(match.id);
        else unmatched.push(token);
      }
      if (selected.length) {
        return { selected: Array.from(new Set(selected)), custom: unmatched.join(' ') };
      }
      return { selected: [], custom: text };
    }
    const match = matchAnswerToken(text, opts);
    return match ? { selected: [match.id], custom: '' } : { selected: [], custom: text };
  };

  const applyParsedAnswer = (tabState: any, question: any, parsed: any) => {
    const selected = new Set(parsed.selected || []);
    const kind = question?.kind === 'multi' ? 'multi'
      : question?.kind === 'input' ? 'input'
      : 'single';
    const opts = (tabState.opts || []).map((o: any) => ({
      ...o,
      selected: kind === 'multi'
        ? (!!o.locked || selected.has(o.id))
        : selected.has(o.id),
    }));
    return { ...tabState, opts, custom: parsed.custom || '' };
  };

  const tabHasAnswer = (tabState: any) => {
    return !!(
      (tabState?.opts || []).some((o: any) => o.selected) ||
      String(tabState?.custom || '').trim()
    );
  };

  const historySnapshotFor = (flowId: any, flow: any, st: any) => {
    if (!flow || !st) return null;
    const session = normalizeUiSession(flow.session || currentSession || w.ACTIVE_SESSION || '');
    const ip = String(flow.ip || ssotIpFromSession(session) || activeSsotIp() || '').trim();
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
    return {
      flowId,
      ts: Date.now(),
      session,
      ip,
      workflow: flow.workflow || '',
      source: flow.source || '',
      items,
    };
  };

  const answerPendingFromInput = (raw: any) => {
    const flowId = pendingQcard?.flowId;
    const flow = flowId && w.QA_FLOWS && w.QA_FLOWS[flowId];
    const st = flowId && qaState[flowId];
    const text = String(raw || '').trim();
    if (!flowId || !flow || !st || st.submitted || !text) return false;

    let nextState = st;
    let shouldSubmit = false;
    let snapshot: any = null;

    if (st.batched) {
      const questions = flow.questions || [];
      const states = (st.states || questions.map((q: any) => ({
        opts: (q.options || []).map((o: any) => ({ ...o })),
        custom: '',
      }))).map((tab: any) => ({
        ...tab,
        opts: (tab.opts || []).map((o: any) => ({ ...o })),
      }));
      const lines = text.split(/\n+/).map((x: string) => x.trim()).filter(Boolean);
      let lineIdx = 0;
      const active = Math.max(0, Math.min(st.active || 0, Math.max(0, questions.length - 1)));
      const openTargets = questions.map((_: any, i: number) => i).filter((i: number) => !tabHasAnswer(states[i]));
      const targets = lines.length > 1
        ? Array.from(new Set((openTargets.length ? openTargets : [active])))
        : [active];
      for (const idx of targets as number[]) {
        if (idx < 0 || idx >= questions.length || lineIdx >= lines.length) continue;
        const q = questions[idx];
        const parsed = parseTextAnswer(lines[lineIdx], q, states[idx]?.opts || []);
        states[idx] = applyParsedAnswer(states[idx] || { opts: [], custom: '' }, q, parsed);
        lineIdx += 1;
      }
      const allAnswered = states.length > 0 && states.every(tabHasAnswer);
      const firstOpen = states.findIndex((tab: any) => !tabHasAnswer(tab));
      nextState = {
        ...st,
        states,
        active: allAnswered ? questions.length : Math.max(0, firstOpen),
        submitted: allAnswered,
      };
      shouldSubmit = allAnswered;
      if (shouldSubmit && w.backend) {
        const answers = states.map((tab: any) => ({
          selected: tab.opts.filter((o: any) => o.selected).map((o: any) => o.id),
          custom: tab.custom || '',
        }));
        w.backend.send({ type: 'answer', flow_id: flowId, answers });
        snapshot = historySnapshotFor(flowId, flow, nextState);
      }
    } else {
      const parsed = parseTextAnswer(text, flow, st.opts || []);
      nextState = {
        ...applyParsedAnswer(st, flow, parsed),
        submitted: true,
      };
      shouldSubmit = true;
      if (w.backend) {
        w.backend.send({
          type: 'answer',
          flow_id: flowId,
          selected: nextState.opts.filter((o: any) => o.selected).map((o: any) => o.id),
          custom: nextState.custom || '',
        });
        snapshot = historySnapshotFor(flowId, flow, nextState);
      }
    }

    setFeed((f: any) => [...f, { kind: 'user', text: raw, createdAt: Date.now() }]);
    setQaState((s: any) => ({ ...s, [flowId]: nextState }));
    if (snapshot) {
      setQaHistory((h: any[]) => {
        if (h.length && h[0].flowId === snapshot.flowId) return h;
        return [snapshot, ...h].slice(0, QA_HISTORY_LIMIT);
      });
    }
    setMainTab(shouldSubmit ? 'chat' : 'qa');
    setAskSel(0);
    if (shouldSubmit) setStreaming(true);
    return true;
  };

  // ── chat submit (FAITHFUL port of workspace.jsx submitMsg L3801-L4356) ─────
  // The full dispatch hub: switch-gate guard → pendingQcard answer-from-input →
  // client-side slash commands → orchestrator-chat / worker job-dispatch HTTP
  // branches → backend slash commands (ack-aware) → default agent prompt
  // (ack-aware). Session-half primitives are now read from the destructured,
  // TYPED deps above — the old `deps as any` cast (which left setStreamText
  // undefined at runtime) is gone. setStreamText is the data hook's OWN state.
  const submitMsg = useCallback((cmd?: any, opts?: { clearCurrentInput?: boolean }) => {
    const raw = String(cmd ?? inputRef.current?.value ?? input).trim();
    submittedInputConsumedRef.current = false;
    if (!raw) return;
    requestFeedScrollToBottom();
    const clearCurrentInput = !!(opts && opts.clearCurrentInput);

    // BUG A: read-and-clear the replay msg_id for THIS dispatch. Set only by the
    // held-input replay when re-firing an ack-miss hold; threaded into sendPrompt
    // so the re-send reuses the original msg_id (backend dedup collapses the dup).
    // Cleared immediately so a fresh submit in the same tick can't inherit it.
    const replayMsgId = replayMsgIdRef.current;
    replayMsgIdRef.current = null;
    const isAckMissReplay = !!replayMsgId;

    const clearSubmittedInput = () => {
      submittedInputConsumedRef.current = true;
      recordInputHistory(raw);
      replaceInput((cur: string) => {
        const curText = String(cur || '').trim();
        if (clearCurrentInput) return '';
        if (!curText || curText === raw) return '';
        if (cmd != null && curText.startsWith('/')) return '';
        return cur;
      });
      setShowSlash(false);
    };
    const acknowledgeLocalSend = () => {
      clearSubmittedInput();
      if (!isAckMissReplay) {
        setFeed((f: any) => [...f, { kind: 'user', text: raw, createdAt: Date.now() }]);
      }
    };
    const holdSubmittedInput = (reason: string, opts?: { msgId?: any; autoReplay?: boolean }) => {
      submittedInputConsumedRef.current = false;
      // msgId is set ONLY for an ack-miss hold (the prompt WAS sent under a
      // concrete msg_id but the worker dropped it / never confirmed). The replay
      // re-fires under that SAME msg_id so the backend's per-session has_msg_id
      // dedup collapses the duplicate — closing BUG A's double-execution race.
      // A backend-down / switch hold was never sent, so it carries no msgId and
      // the replay mints a fresh id as usual.
      heldSubmitRef.current = {
        raw,
        cmd,
        createdAt: Date.now(),
        msgId: opts?.msgId || null,
        autoReplay: opts?.autoReplay !== false,
      };
      setInput((cur: any) => {
        const curText = String(cur || '').trim();
        return curText ? cur : raw;
      });
      setShowSlash(false);
      setStreaming(false);
      awaitingRunStartRef.current = false;
      streamBufferRef.current = '';
      setStreamText('');
      setFeed((f: any) => [...f, { kind: 'agent', text: reason, createdAt: Date.now() }]);
    };
    const clearLatencyStatus = () => {
      try {
        if (latencyTimerRef.current) {
          clearTimeout(latencyTimerRef.current);
          latencyTimerRef.current = null;
        }
      } catch (_) {}
      if (!latencyStatusRef.current) return;
      latencyStatusRef.current = null;
      setFeed((f: any) => f.filter((e: any) => !(e && e.pendingMsgId)));
    };
    const promptBackendState = () => {
      if (!w.backend) return 'missing';
      if (typeof w.backend.getConnectionState === 'function') {
        return w.backend.getConnectionState() || backendState || 'unknown';
      }
      return backendState || 'unknown';
    };
    const showLatencyStatus = (msgId: any, onStranded?: () => void) => {
      const id = msgId || '__latency__';
      const prev = latencyStatusRef.current;
      if (prev && prev.msgId === id) return;
      latencyStatusRef.current = { msgId: id };
      setFeed((f: any) => {
        const filtered = f.filter((e: any) => !(e && e.pendingMsgId));
        return [...filtered, {
          kind: 'agent',
          text: '전송 중 - 워커가 바쁩니다 (대기 중)',
          pendingMsgId: id,
          createdAt: Date.now(),
        }];
      });
      try {
        if (latencyTimerRef.current) clearTimeout(latencyTimerRef.current);
      } catch (_) {}
      const arm = () => {
        latencyTimerRef.current = setTimeout(() => {
          if (!latencyStatusRef.current || latencyStatusRef.current.msgId !== id) return;
          if (!backendReadyForPrompt()) {
            clearLatencyStatus();
            if (typeof onStranded === 'function') onStranded();
            return;
          }
          arm();
        }, 30000);
      };
      arm();
    };
    const promptAckDebugDetail = (sent: any, msgId?: any) => {
      const pairs = [
        ['session', sent && sent.session],
        ['worker_session', sent && sent.worker_session],
        ['transport_session', sent && sent.transport_session],
        ['ip', sent && sent.ip],
        ['workflow', sent && sent.workflow],
        ['msg_id', msgId || (sent && sent.msg_id)],
        ['backend', promptBackendState()],
      ].filter(([, value]) => String(value || '').trim());
      return pairs.length
        ? ` (${pairs.map(([key, value]) => `${key}=${String(value)}`).join(' ')})`
        : '';
    };
    const backendReadyForPrompt = () => w.backend && promptBackendState() === 'open';
    // onMiss receives the reason AND the original msg_id (when one exists) so the
    // held-input replay can re-fire under the SAME msg_id. The id is only present
    // for a prompt that actually reached backend.send (sent.ok === true with a
    // sent.msg_id) — i.e. the worker dropped it or never confirmed delivery.
    const waitForPromptAck = (sent: any, onAck: (e: any) => void, onMiss: (r: any, msgId?: any, sent?: any) => void) => {
      if (!sent || sent.ok === false) {
        onMiss(sent?.error || backendState || 'unknown', sent?.msg_id, sent);
        return;
      }
      if (!sent.ack || typeof sent.ack.then !== 'function') {
        onAck(null);
        return;
      }
      sent.ack.then((ack: any) => {
        if (ack && ack.ok) {
          clearLatencyStatus();
          onAck(ack.event || ack);
          return;
        }
        if (ack && ack.pending) {
          showLatencyStatus(sent.msg_id, () => {
            onMiss('backend did not confirm worker delivery', sent.msg_id, sent);
          });
          if (typeof sent.onAckResolved === 'function') {
            sent.onAckResolved((late: any) => {
              clearLatencyStatus();
              if (late && late.ok) {
                onAck(late.event || late);
                return;
              }
              onMiss((late && late.error) || 'backend did not acknowledge receipt', sent.msg_id, Object.assign({}, sent || {}, {
                worker_session: late && late.event && late.event.session_id,
                transport_session: late && late.transport && late.transport.session_id,
              }));
            });
          }
          return;
        }
        onMiss((ack && ack.error) || 'backend did not acknowledge receipt', sent.msg_id, Object.assign({}, sent || {}, {
          worker_session: ack && ack.event && ack.event.session_id,
          transport_session: ack && ack.transport && ack.transport.session_id,
        }));
      });
    };
    const holdUnacknowledgedInput = (reason: string, msgId?: any, sent?: any) => {
      clearLatencyStatus();
      const replayFailed = isAckMissReplay && msgId && String(replayMsgId) === String(msgId);
      const prefix = replayFailed ? 'Input not confirmed after retry.' : 'Input not confirmed.';
      const suffix = replayFailed
        ? 'kept it in the input box.'
        : 'kept it in the input box and will retry once if unchanged.';
      holdSubmittedInput(
        `${prefix} ${reason || 'Backend did not acknowledge receipt'}${promptAckDebugDetail(sent, msgId)}; ${suffix}`,
        { msgId, autoReplay: !replayFailed },
      );
    };

    // Race fix: read the synchronous gate FIRST. workflowReady is React state and
    // lags one commit behind beginWorkflowReady's setWorkflowReady(); the gate was
    // set in the SAME tick, so it reports "switching" immediately even when the
    // closed-over workflowReady is still the stale null. Either signal holds the
    // input via the held-input mechanism, which the replay effect below flushes
    // once the switch settles.
    const workflowReadyBlocking = !!(workflowReady && workflowReady.phase !== 'ready');
    const switchingNow = !!(switchGateRef && switchGateRef.current && switchGateRef.current.isSwitching());
    if (workflowReadyBlocking || switchingNow) {
      const holdTarget = (workflowReady && workflowReady.target) || workflow || 'workflow';
      let queued = 0;
      // While SWITCHING, enqueue into the gate's FIFO so that N>1 prompts typed
      // during a single switch are all preserved (the single-slot heldSubmitRef
      // would otherwise overwrite all but the last). The replay effect below
      // drains this FIFO in order once the switch settles. submit() only returns
      // action:"held" while switching; if the gate already reopened (ready) we
      // fall through to the normal single-slot hold below.
      if (switchingNow && switchGateRef.current) {
        const outcome = switchGateRef.current.submit({ text: raw, meta: { cmd: cmd ?? null } });
        queued = Number((outcome as any)?.queued || 0);
      }
      const gateRoute = switchGateRef?.current?.route?.();
      const targetSession = normalizeUiSession(
        (workflowReady && workflowReady.session) ||
        (gateRoute && (gateRoute as any).target) ||
        currentSession ||
        w.ACTIVE_SESSION ||
        '',
      );
      const detailPairs = [
        ['target', holdTarget],
        ['session', targetSession],
        ['phase', workflowReady && workflowReady.phase],
        ['backend', promptBackendState()],
        ['queued', queued || switchGateRef?.current?.pendingCount?.()],
      ].filter(([, value]) => String(value || '').trim());
      const debug = detailPairs.length
        ? ` (${detailPairs.map(([key, value]) => `${key}=${String(value)}`).join(' ')})`
        : '';
      holdSubmittedInput(`Input queued during route switch${debug}. It will auto-send when the route is ready; a copy is kept in the input box.`);
      return;
    }

    if (pendingQcard && !raw.startsWith('/')) {
      if (answerPendingFromInput(raw)) {
        clearSubmittedInput();
        return;
      }
    }

    // ── Client-side slash commands ──────────────────────────────
    // Some commands operate on browser state (SCOPE_PATH lives in
    // localStorage / window) and don't need an agent round-trip.
    // Handle them here BEFORE sending anything to the backend.
    const sessionMatch = raw.match(/^\/(session|sess)(\s+(.*))?$/);
    if (sessionMatch) {
      clearSubmittedInput();
      const arg = (sessionMatch[3] || '').trim();
      setFeed((f: any) => [...f, { kind: 'user', text: raw, createdAt: Date.now() }]);
      const _clearStreaming = () => {
        setStreaming(false);
        streamBufferRef.current = '';
        setStreamText('');
      };
      if (!arg) {
        setFeed((f: any) => [...f, {
          kind: 'agent',
          text: `Current session: \`${activeSession || w.ACTIVE_SESSION || 'default'}\`\nUse \`/session default\` to return to the default session.`,
        }]);
        _clearStreaming();
        return;
      }
      if (arg.toLowerCase() === 'default') {
        const sid = switchToDefaultSession();
        setFeed((f: any) => [...f, { kind: 'agent', text: `Session set to \`${sid}\`.` }]);
        _clearStreaming();
        return;
      }
      const sid = resolveSession(arg, activeSession, w.ACTIVE_SESSION);
      w.ACTIVE_SESSION = sid;
      setActiveSession(sid);
      try { localStorage.setItem('atlasActiveSession', sid); } catch (_) {}
      refreshChatSession(sid);
      setFeed((f: any) => [...f, { kind: 'agent', text: `Session set to \`${sid}\`.` }]);
      _clearStreaming();
      return;
    }

    const m = raw.match(/^\/(scope|cd)(\s+(.*))?$/);
    if (m) {
      clearSubmittedInput();
      const arg = (m[3] || '').trim();
      const cur = w.SCOPE_PATH || '';
      const _clearStreaming = () => {
        setStreaming(false);
        streamBufferRef.current = '';
        setStreamText('');
      };
      if (!arg) {
        setFeed((f: any) => [...f, { kind: 'user', text: raw, createdAt: Date.now() }]);
        setFeed((f: any) => [...f, {
          kind: 'agent',
          text: cur
            ? `Current scope: \`${cur}\`\nUse \`/scope <path>\` to change, \`/scope /\` to reset.`
            : 'No scope set — agent works on the whole project.\nUse `/scope <path>` to confine it.',
        }]);
        _clearStreaming();
        return;
      }
      const next = (arg === '/' || arg === '~' || arg === '-') ? '' : arg.replace(/^\/+|\/+$/g, '');
      w.atlasData.setScopePath(next);
      setFeed((f: any) => [...f, { kind: 'user', text: raw, createdAt: Date.now() }]);
      setFeed((f: any) => [...f, {
        kind: 'agent',
        text: next
          ? `✓ Scope set to \`${next}\`. Future prompts will tell the agent to stay inside this directory.`
          : '✓ Scope cleared. Agent operates on the whole project again.',
      }]);
      _clearStreaming();
      return;
    }

    // /plan, /normal, /mode plan, /mode normal — flip UI intent locally AND
    // forward to backend so agent_mode flips. Normalize the WIRE form to the
    // canonical command the backend slash registry actually handles.
    const modeMatch = raw.match(/^\/(plan|mode\s+plan|mode\s+normal|normal)$/i);
    if (modeMatch) {
      clearSubmittedInput();
      const target = /^\/(plan|mode\s+plan)$/i.test(raw) ? 'plan' : 'normal';
      const wire = target === 'plan' ? '/plan' : '/mode normal';
      setIntent(target);
      setFeed((f: any) => [...f, { kind: 'user', text: raw, createdAt: Date.now() }]);
      sendPrompt(wire);
      setStreaming(false);
      streamBufferRef.current = '';
      setStreamText('');
      return;
    }

    const wfMatch = raw.match(/^\/(wf|workflow)(\s+(\S+))?$/i);
    if (wfMatch) {
      clearSubmittedInput();
      const targetWf = (wfMatch[3] || '').trim();
      setFeed((f: any) => [...f, { kind: 'user', text: raw, createdAt: Date.now() }]);
      if (targetWf) {
        switchWorkflow(targetWf);
      } else {
        setFeed((f: any) => [...f, {
          kind: 'agent',
          text: `Current workflow: \`${workflow || 'default'}\``,
        }]);
      }
      setStreaming(false);
      streamBufferRef.current = '';
      setStreamText('');
      return;
    }

    const pipelineMatch = raw.match(/^\/(pipeline|pipe|full-pipeline)(\s+(\S+))?$/i);
    if (pipelineMatch) {
      clearSubmittedInput();
      const ipName = (pipelineMatch[3] || w.ACTIVE_IP || activeIp || '').trim();
      setFeed((f: any) => [...f, { kind: 'user', text: raw, createdAt: Date.now() }]);
      const _clearStreaming = () => {
        setStreaming(false);
        streamBufferRef.current = '';
        setStreamText('');
      };
      if (!ipName || ipName === 'default') {
        setFeed((f: any) => [...f, {
          kind: 'agent',
          text: 'Usage: `/pipeline <ip>` — dispatches SSOT → FL/CL → RTL → lint → TB → sim → coverage → syn → sta → pnr → sta-post.',
        }]);
        _clearStreaming();
        return;
      }
      fetch('/api/pipeline/dispatch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ip: ipName }),
      })
        .then(async (r) => {
          const j = await r.json().catch(() => ({}));
          if (!r.ok || j.error || j.detail) throw new Error(j.error || j.detail || `HTTP ${r.status}`);
          return j;
        })
        .then((j: any) => {
          const stages = Array.isArray(j.stages)
            ? j.stages.map((s: any) => s && s.id).filter(Boolean).join(' → ')
            : '';
          setFeed((f: any) => [...f, {
            kind: 'agent',
            text: `Dispatched pipeline \`${j.pipeline_id || 'unknown'}\` for \`${ipName}\`${stages ? `.\nStages: ${stages}` : '.'}`,
          }]);
          window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'JOBS' }));
        })
        .catch((err: any) => setFeed((f: any) => [...f, {
          kind: 'agent',
          text: 'Pipeline dispatch failed: ' + (err && err.message || err),
        }]));
      _clearStreaming();
      return;
    }

    // /commit <msg> — labeled checkpoint in the active IP's per-IP git.
    const commitMatch = raw.match(/^\/commit(\s+([\s\S]+))?$/i);
    if (commitMatch) {
      clearSubmittedInput();
      const msg = (commitMatch[2] || '').trim() || 'manual checkpoint';
      const ipName = (w.ACTIVE_IP || activeIp || '').trim();
      setFeed((f: any) => [...f, { kind: 'user', text: raw, createdAt: Date.now() }]);
      if (!ipName || ipName === 'default') {
        setFeed((f: any) => [...f, {
          kind: 'agent',
          text: '⚠ no active IP — pick one from the IP_ID dropdown first.',
        }]);
      } else {
        fetch(`/api/ip/${encodeURIComponent(ipName)}/git/commit`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: msg, session_id: String((window as any).ACTIVE_SESSION || '').trim() || undefined }),
        })
          .then((r) => r.json())
          .then((j: any) => {
            const ok = j && j.ok;
            const hash = (j && j.hash) || '?';
            const detail = (j && (j.stderr || j.error || '')).slice(0, 200);
            setFeed((f: any) => [...f, {
              kind: 'agent',
              text: ok ? `✅ committed \`${hash}\` — ${msg}` : `⚠ commit failed: ${detail || 'unknown error'}`,
            }]);
          })
          .catch((err: any) => setFeed((f: any) => [...f, {
            kind: 'agent',
            text: '⚠ commit request failed: ' + (err && err.message || err),
          }]));
      }
      setStreaming(false);
      streamBufferRef.current = '';
      setStreamText('');
      return;
    }

    // /feedback <text> — drop a message into the feedback table for admin review.
    const feedbackMatch = raw.match(/^\/feedback(\s+([\s\S]+))?$/i);
    if (feedbackMatch) {
      clearSubmittedInput();
      const text = (feedbackMatch[2] || '').trim();
      setFeed((f: any) => [...f, { kind: 'user', text: raw, createdAt: Date.now() }]);
      if (!text) {
        setFeed((f: any) => [...f, {
          kind: 'agent',
          text: 'Usage: `/feedback <your message>` — sends a message to the admin team.',
        }]);
      } else {
        fetch('/api/feedback', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ content: text }),
        })
          .then((r) => r.json())
          .then((j: any) => setFeed((f: any) => [...f, {
            kind: 'agent',
            text: j && j.ok
              ? `✅ feedback received (id: \`${(j.id || '').slice(0, 8)}\`). Thanks!`
              : `⚠ feedback failed: ${(j && (j.error || j.detail)) || 'unknown error'}`,
          }]))
          .catch((err: any) => setFeed((f: any) => [...f, {
            kind: 'agent',
            text: '⚠ feedback request failed: ' + (err && err.message || err),
          }]));
      }
      setStreaming(false);
      streamBufferRef.current = '';
      setStreamText('');
      return;
    }

    // ── Orchestrator-mode HTTP branches ─────────────────────────────────────
    const isOrch = atlasUiOrchestratorMode();
    const orchIp = String(activeIp || '').trim();
    const inputRoute = inputRouteRef.current || {};
    const dispatchWorkflow = inputRoute.type === 'workflow-dispatch'
      ? normalizeUiSession(inputRoute.workflow || '')
      : '';
    const dispatchSession = dispatchWorkflow
      ? (normalizeUiSession(inputRoute.session || '') || sessionForInputRoute(orchIp, dispatchWorkflow))
      : '';
    if (
      atlasUiOrchestratorMode()
      && dispatchWorkflow
      && dispatchWorkflow !== 'orchestrator'
      && orchIp
      && orchIp.toLowerCase() !== 'default'
      && !raw.startsWith('/')
    ) {
      clearSubmittedInput();
      setFeed((f: any) => [...f, { kind: 'user', text: raw, createdAt: Date.now() }]);
      setStreaming(true);
      awaitingRunStartRef.current = true;
      fetch('/api/job/dispatch', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          workflow: dispatchWorkflow,
          ip: orchIp,
          prompt: raw,
          session: dispatchSession,
          exec_mode: 'orchestrator',
          run_mode: w.ATLAS_RUN_MODE || (w.ATLAS_BOOT_CONFIG && w.ATLAS_BOOT_CONFIG.run_mode) || '',
          trigger_source: 'worker_direct_chat',
        }),
      })
        .then(async (r) => {
          const j = await r.json().catch(() => ({}));
          if (!r.ok || j.error || j.detail) throw new Error(j.error || j.detail || `HTTP ${r.status}`);
          return j;
        })
        .then((j: any) => {
          const result = {
            ok: true,
            job_id: j.job_id || '',
            workflow: j.workflow || dispatchWorkflow,
            ip: orchIp,
            session: j.session || dispatchSession,
            worker: j.worker || '',
            status: j.status || 'queued',
          };
          setFeed((f: any) => [...f, {
            kind: 'action',
            text: `▶ dispatch_workflow workflow="${dispatchWorkflow}" ip="${orchIp}"`,
            tool: 'dispatch_workflow',
            args: `workflow="${dispatchWorkflow}", ip="${orchIp}"`,
            createdAt: Date.now(),
          }, {
            kind: 'obs',
            text: JSON.stringify(result, null, 2),
            tool: 'dispatch_workflow',
            createdAt: Date.now(),
          }]);
          window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'JOBS' }));
          [1200, 3500, 7000].forEach((delay) => setTimeout(() => {
            const route = inputRouteRef.current || {};
            const sid = normalizeUiSession(route.session || '');
            if (route.type === 'workflow-dispatch' && sid === dispatchSession) {
              refreshChatSession(dispatchSession, { force: true, viewOnly: true });
            }
          }, delay));
        })
        .catch((e: any) => {
          setFeed((f: any) => [...f, { kind: 'agent', text: `[${dispatchWorkflow}] dispatch failed: ${String(e && e.message || e)}` }]);
        })
        .finally(() => {
          setStreaming(false);
          awaitingRunStartRef.current = false;
          streamBufferRef.current = '';
          setStreamText('');
        });
      return;
    }
    if (isOrch && orchIp && orchIp.toLowerCase() !== 'default' && !raw.startsWith('/')) {
      clearSubmittedInput();
      const sessionParts = normalizeUiSession(w.ACTIVE_SESSION || activeSessionRef.current || activeSession || '').split('/').filter(Boolean);
      const orchOwner = normalizeUiSession((w.ATLAS_USER && w.ATLAS_USER.username) || '') || sessionParts[0] || 'default';
      const orchSession = resolveSession(
        (w.atlasData && w.atlasData.sessionFor)
          ? w.atlasData.sessionFor(orchIp, 'orchestrator')
          : `${orchOwner}/${orchIp}/orchestrator`,
      );
      const returningFromWorkerView = !!normalizeUiSession(chatViewSessionRef.current || '');
      if (atlasUiOrchestratorMode()) {
        setWorkflow('orchestrator');
        setMainTab('chat');
        setChatViewSession('');
        setOrchestratorInputRoute(orchIp);
        w.CONTEXT = Object.assign({}, w.CONTEXT || {}, {
          workspace: 'orchestrator',
          view_workspace: 'orchestrator',
        });
        if (orchSession) {
          const activeBefore = normalizeUiSession(w.ACTIVE_SESSION || activeSessionRef.current || '');
          hydratedConversationSessionRef.current = orchSession;
          if (activeBefore !== orchSession) {
            w.ACTIVE_SESSION = orchSession;
            activeSessionRef.current = orchSession;
            setActiveSession(orchSession);
            try { localStorage.setItem('atlasActiveSession', orchSession); } catch (_) {}
          }
          if (activeBefore !== orchSession && w.backend) {
            try {
              if (typeof w.backend.switchSession === 'function') w.backend.switchSession(orchSession);
              else if (typeof w.backend.connect === 'function') w.backend.connect(orchSession);
            } catch (_) {}
          }
        }
      }
      setFeed((f: any) => [...(returningFromWorkerView ? [] : f), { kind: 'user', text: raw, createdAt: Date.now() }]);
      setStreaming(true);
      awaitingRunStartRef.current = true;
      fetch('/api/pipeline/orchestrator/chat', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: raw,
          ip: orchIp,
          session: orchSession,
        }),
      })
        .then((r) => r.json().catch(() => ({})))
        .then((d: any) => {
          if (d && d.error) {
            setFeed((f: any) => [...f, { kind: 'agent', text: `[orchestrator] ${d.error}` }]);
            setStreaming(false);
            return;
          }
          if (d && d.reply && String(d.reply).trim()) {
            setFeed((f: any) => [...f, { kind: 'agent', text: String(d.reply), createdAt: Date.now() }]);
            setStreaming(false);
          }
        })
        .catch((e: any) => {
          setFeed((f: any) => [...f, { kind: 'agent', text: `[orchestrator] ${String(e)}` }]);
          setStreaming(false);
        });
      return;
    }

    // Backend slash commands — anything starting with '/' the client-side
    // branches above didn't handle (/context, /help, /clear, /status, /model …).
    // Do NOT arm the agent-run streaming state for them: the backend's events
    // drive the banner (running:true only when an agent actually runs).
    if (raw.startsWith('/')) {
      // `/ip <name>` | `/use <name>`: drive the FRONTEND IP switch too.
      try {
        const _ipm = raw.match(/^\/(?:ip|use)\s+(\S+)/i);
        if (_ipm && !_ipm[1].startsWith('-')) {
          const _argIp = _ipm[1];
          const _cur = String(w.ACTIVE_IP || '');
          if (_argIp && _argIp.toLowerCase() !== 'default' && _argIp.toLowerCase() !== _cur.toLowerCase()) {
            window.dispatchEvent(new CustomEvent('atlas:select-ip', { detail: { ip: _argIp } }));
          }
        }
      } catch (_) {}
      if (!backendReadyForPrompt()) {
        holdSubmittedInput(`Input held. Backend is ${promptBackendState()}; it will send automatically if unchanged.`);
        return;
      }
      const busyState = slashBusyForRaw(raw);
      const sent = sendPrompt(raw, undefined, replayMsgId);
      if (!sent || sent.ok === false) {
        if (busyState) setCommandBusy(null);
        holdSubmittedInput(`Input held. Backend is not ready (${sent?.error || backendState || 'unknown'}); it will send automatically if unchanged.`);
        return;
      }
      if (busyState) setCommandBusy(busyState);
      acknowledgeLocalSend();
      waitForPromptAck(
        sent,
        () => {},
        (reason: any, msgId?: any) => {
          if (busyState) setCommandBusy(null);
          holdUnacknowledgedInput(reason, msgId);
        },
      );
      return;
    }

    if (!backendReadyForPrompt()) {
      holdSubmittedInput(`Input held. Backend is ${promptBackendState()}; it will send automatically if unchanged.`);
      return;
    }
    const sent = sendPrompt(raw, undefined, replayMsgId);
    if (!sent || sent.ok === false) {
      holdSubmittedInput(`Input held. Backend is not ready (${sent?.error || backendState || 'unknown'}); it will send automatically if unchanged.`);
      return;
    }
    acknowledgeLocalSend();
    setStreaming(true);
    awaitingRunStartRef.current = true;
    backendRunStartedRef.current = false;
    setStreamText('');
    waitForPromptAck(
      sent,
      () => {},
      holdUnacknowledgedInput,
    );
    // Keep the submitted user message clean. Active IP/path scope is already
    // injected into the workflow system prompt by the backend.
  }, [
    input, workflow, activeIp, activeSession, currentSession,
    backendState, pendingQcard, qaState,
    recordInputHistory, setFeed, setInput, setShowSlash, setStreaming, setStreamText,
    setQaState, setQaHistory, setMainTab, setAskSel, setCommandBusy, setActiveSession, setIntent, setWorkflow,
    streamBufferRef, workflowReady, switchGateRef, sendPrompt, resolveSession,
    sessionForInputRoute, setChatViewSession, setOrchestratorInputRoute,
    switchToDefaultSession, switchWorkflow, activeSsotIp,
    activeSessionRef, chatViewSessionRef, hydratedConversationSessionRef, inputRouteRef,
    requestFeedScrollToBottom,
  ]);

  // Held-input replay: when the switch settles (workflowReady cleared) and the
  // backend is open, re-fire the held prompt(s) in FIFO order.
  //
  // Two held-input sources feed this one flush, never a parallel queue:
  //   1. The gate FIFO (switchGateRef): prompts typed DURING a switch are
  //      enqueued via gate.submit() so N>1 are all preserved. drain() here is
  //      the gate's ONLY live caller — without it the FIFO would accumulate
  //      forever (the orphaned-pending leak). We drain it once the switch
  //      settles and re-fire every held prompt in order.
  //   2. The single-slot heldSubmitRef: prompts held while the backend was
  //      down/closed (NOT switching — the gate is ready in that case). This is
  //      a single overwrite slot and the gate FIFO is empty for it.
  // The most-recent held prompt is also mirrored back into the input box (by
  // holdSubmittedInput), so the "did the user change it?" guard only applies to
  // that last entry; earlier FIFO entries are committed prompts and replay
  // unconditionally once the switch is over.
  useEffect(() => {
    if (workflowReady && workflowReady.phase !== 'ready') return undefined;
    const state = w.backend && typeof w.backend.getConnectionState === 'function'
      ? w.backend.getConnectionState()
      : backendState;
    if (state !== 'open') return undefined;

    const gate = switchGateRef && switchGateRef.current;
    // PEEK (don't drain) the FIFO depth so the held msgs survive an effect
    // cleanup/re-run before the commit point below; drain() is deferred into the
    // timer so it happens exactly once, at the moment we actually re-fire.
    // NOTE: route() can't be used here — by the time this effect runs the switch
    // has settled and the gate is back to "ready" (markReady/markFailed ran), so
    // route() reports the ready singleton with no pending field even though the
    // FIFO still holds the switch-time prompts. pendingCount() stays accurate.
    const queuedDepth = gate && typeof gate.pendingCount === 'function' ? gate.pendingCount() : 0;
    const held = heldSubmitRef.current;
    if (!queuedDepth && !held) return undefined;

    // The last held prompt was mirrored into the box (single-slot UX). The gate
    // FIFO entries are already-committed prompts and replay unconditionally; only
    // the single-slot held entry is gated on the box being unchanged.
    if (held && String(input || '').trim() !== held.raw && !queuedDepth) {
      heldSubmitRef.current = null;
      return undefined;
    }

    const timer = setTimeout(() => {
      const liveGate = switchGateRef && switchGateRef.current;
      // drain() is the gate FIFO's ONLY live caller — this empties it exactly
      // once, closing the orphaned-pending leak. Re-fire earliest-first.
      const fifo: any[] = liveGate && typeof liveGate.drain === 'function' ? liveGate.drain() : [];
      const latest = heldSubmitRef.current;
      heldSubmitRef.current = null;
      // The single-slot held entry replays only when the gate FIFO did not carry
      // it (i.e. it was a backend-down hold, not a switch hold) and the box still
      // matches it. A switch hold already lives in the FIFO, so we skip it here
      // to avoid a duplicate send.
      if (latest && latest.autoReplay !== false && !fifo.length && String(input || '').trim() === latest.raw) {
        // Carry the ack-miss hold's ORIGINAL msg_id so the re-fire below re-sends
        // under the same id (BUG A: backend has_msg_id dedup collapses the dup).
        fifo.push({ text: latest.raw, meta: { cmd: latest.cmd ?? null, msgId: latest.msgId || null } });
      }
      for (const m of fifo) {
        const meta = (m && m.meta) || {};
        const replayCmd = meta.cmd != null ? meta.cmd : (m ? m.text : undefined);
        // Switch-hold FIFO entries were never sent (no msgId) → submitMsg mints a
        // fresh id. Only an ack-miss replay carries the original id to reuse.
        replayMsgIdRef.current = meta.msgId || null;
        submitMsg(replayCmd);
      }
      replayMsgIdRef.current = null;
    }, 80);
    return () => clearTimeout(timer);
  }, [backendState, input, workflowReady, submitMsg, switchGateRef]);

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
          Number(wk.queued_count || 0) > 0 ||
          Number(wk.blocked_count || 0) > 0
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
      inputHistoryDraftRef.current = String(inputRef.current?.value ?? input);
      idx = inputHistory.length - 1;
    } else {
      idx += delta;
    }
    if (idx < 0) idx = 0;
    if (idx >= inputHistory.length) {
      inputHistoryIndexRef.current = null;
      replaceInput(inputHistoryDraftRef.current || '');
      return true;
    }
    inputHistoryIndexRef.current = idx;
    replaceInput(inputHistory[idx] || '');
    setShowSlash(false);
    setShowAt(false);
    return true;
  };

  const submitMsgKeyResult = (cmd?: any, opts?: { clearCurrentInput?: boolean }): WorkspacePromptKeyResult => {
    submitMsg(cmd, opts);
    return submittedInputConsumedRef.current ? 'submitted' : 'handled';
  };

  const onPromptKey = (e: any): WorkspacePromptKeyResult => {
    if (showSlash) {
      if (e.key === 'ArrowDown') { e.preventDefault(); setSlashSel((s: number) => Math.min(s + 1, filtered.length - 1)); return 'handled'; }
      if (e.key === 'ArrowUp')   { e.preventDefault(); setSlashSel((s: number) => Math.max(s - 1, 0)); return 'handled'; }
      if (e.key === 'Tab' || e.key === 'Enter') {
        if (filtered[slashSel]) {
          e.preventDefault();
          if (e.key === 'Enter') return submitMsgKeyResult(filtered[slashSel].cmd, { clearCurrentInput: true });
          replaceInput(filtered[slashSel].cmd + ' ');
          return 'handled';
        }
      }
      if (e.key === 'Escape') { e.preventDefault(); setShowSlash(false); return 'handled'; }
    }
    if (showAt) {
      if (e.key === 'ArrowDown') { e.preventDefault(); setAtSel((s: number) => Math.min(s + 1, fileMatches.length - 1)); return 'handled'; }
      if (e.key === 'ArrowUp')   { e.preventDefault(); setAtSel((s: number) => Math.max(s - 1, 0)); return 'handled'; }
      if (e.key === 'Tab' || e.key === 'Enter') {
        if (fileMatches[atSel]) {
          e.preventDefault();
          acceptAtCompletion(fileMatches[atSel]);
          return 'handled';
        }
      }
      if (e.key === 'Escape') { e.preventDefault(); setShowAt(false); return 'handled'; }
    }
    if (e.key === 'ArrowUp') {
      if (navigateInputHistory(-1)) {
        e.preventDefault();
        requestAnimationFrame(() => {
          const el = inputRef.current;
          if (el) el.setSelectionRange(el.value.length, el.value.length);
        });
        return 'handled';
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
        return 'handled';
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
        replaceInput(next);
        requestAnimationFrame(() => {
          el.selectionStart = el.selectionEnd = lo + 1;
          el.style.height = 'auto';
          el.style.height = Math.min(el.scrollHeight, 192) + 'px';
        });
        return 'handled';
      }
      if (!e.shiftKey) {
        e.preventDefault();
        return submitMsgKeyResult(e.currentTarget?.value ?? input, { clearCurrentInput: true });
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
      onScroll={updateFeedPinnedToBottom}
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
      inputResetToken={inputResetToken}
      inputRef={inputRef}
      inputRouteState={inputRouteState}
      inputRouteRef={inputRouteRef}
      inputHistoryIndexRef={inputHistoryIndexRef}
      inputHistoryDraftRef={inputHistoryDraftRef}
      onKey={onPromptKey}
      pendingQcard={pendingQcard}
      workflowReady={workflowReady}
      atlasUiOrchestratorMode={atlasUiOrchestratorMode}
      workflowForExecMode={workflowForExecMode}
      defaultWorkflowForExecMode={defaultWorkflowForExecMode}
    />
  );

  return {
    // telemetry / backend
    backendState, setBackendState,
    commandBusy, setCommandBusy,
    liveLlmRuntime,
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
    input, setInput: replaceInput, heldSubmitRef,
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
