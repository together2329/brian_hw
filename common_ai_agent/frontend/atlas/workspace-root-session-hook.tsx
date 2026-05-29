// workspace-root-session-hook.tsx — the session/workflow/feed/streaming state
// machine carved out of the Workspace closure (strangler-fig TS split).
//
// Workspace in workspace.jsx is a ~5,315-line monolith that cannot fit under the
// per-file <1000-line ceiling, so the inert TS mirror splits its render body into
// cohesive custom hooks consumed by workspace-root.tsx. THIS file owns the upper
// half of that closure: the two-axis intent/workflow mode model, the
// workflow-ready overlay timers (begin/dismiss/finish/fail/update), the mobile
// drawer state, the activeSession + refs cluster, the input-route resolution
// (setInputRoute / sessionForInputRoute / setOrchestratorInputRoute /
// setWorkflowDispatchInputRoute / setChatViewSession), the NORMAL_FEED/PLAN_FEED
// seeds, and the session transition handlers (activateSession, sendPrompt,
// switchToDefaultSession, handleSwitchSession, switchIntent, switchWorkflow,
// refreshFeed, appendLiveFeedEntries). It performs the runtime
// window.ACTIVE_SESSION / ACTIVE_IP / CONTEXT / ATLAS_AGENT_RUNNING writes and the
// atlas-session-switched CustomEvent dispatch exactly as the legacy closure did.
//
// Because the streaming primitives (setStreaming/streamingRef/streamBufferRef/
// setStreamText) and the center-tab setter (setMainTab) live in the sibling
// useWorkspaceData hook, they are injected via the deps bag — the same pattern
// app-session-hook.tsx uses. The hook runs inside Workspace's render context so
// behavior is identical to the inlined closure.
//
// INERT mirror: legacy workspace.jsx still serves the live app. Typed in the
// permissive house style — window-sourced and dynamically-shaped values are
// `any` on purpose; do NOT tighten them.
import { useState, useEffect, useRef, useCallback } from 'react';
import type { MutableRefObject, Dispatch, SetStateAction } from 'react';
import {
  refreshChatSession,
  trimAtlasFeedState,
  coalesceAtlasFeedEntries,
} from './workspace-tool-theme';
import {
  normalizeUiSession,
  defaultWorkflowForExecMode,
  workflowForExecMode,
  initialInputRouteForExecMode,
  resolveActiveSession,
  routeSessionIp,
  activeIpForRoute,
  workflowFromSession,
  atlasUiOrchestratorMode,
} from './workspace-session-routing';
// NOTE: workspace-async-resource is listed as a permitted sibling import, but
// this slice references none of its preview-path symbols — those effects belong
// to the useWorkspaceData hook. No import is emitted here to keep the module
// free of unused bindings.

// Narrow `any` cast over window for cross-file globals owned by unmigrated .jsx
// (window.backend, window.CONTEXT, window.ACTIVE_SESSION, window.atlasData,
// window.ATLAS_USER, window.SCOPE_PATH, window.FLOW_STAGES, etc.).
const w = window as any;

// Workflow-ready overlay timeout. The canonical export lives in the sibling
// workspace-workflow-ready module, but that file is NOT in this slice's allowed
// import set (and importing it would couple the session machine to an overlay
// component). Mirror the source literal here, exactly as the legacy closure
// referenced the module-scope constant in workspace.jsx.
const WORKFLOW_READY_TIMEOUT_MS = 7000;

export interface UseWorkspaceSessionDeps {
  // Workspace props consumed by the session machine.
  uiLang: string;
  activeNamespace: string;
  activeWorkflow: string;
  // Cross-hook primitives owned by useWorkspaceData (injected so behavior in the
  // split mirror matches the single-closure original).
  setStreaming: Dispatch<SetStateAction<boolean>>;
  streamingRef: MutableRefObject<boolean>;
  streamBufferRef: MutableRefObject<string>;
  setStreamText: Dispatch<SetStateAction<string>>;
  setMainTab: Dispatch<SetStateAction<string>>;
}

export function useWorkspaceSession(deps: UseWorkspaceSessionDeps): any {
  const {
    uiLang,
    activeNamespace,
    activeWorkflow,
    setStreaming,
    streamingRef,
    streamBufferRef,
    setStreamText,
    setMainTab,
  } = deps;

  // Two-axis mode model:
  //   intent: 'normal' | 'plan'   (top-level — shift+tab to swap)
  //   workflow: null | 'ssot' | 'rtl_gen' | 'lint' | 'tb_gen'
  const [intent, setIntent] = useState('normal');
  const [workflow, setWorkflow] = useState<any>(() => defaultWorkflowForExecMode());
  const [workflowReady, setWorkflowReady] = useState<any>(null);
  const workflowReadySeqRef = useRef(0);
  const workflowReadyTimeoutRef = useRef<any>(null);
  const workflowReadyClearRef = useRef<any>(null);

  const clearWorkflowReadyTimers = useCallback(() => {
    if (workflowReadyTimeoutRef.current) {
      clearTimeout(workflowReadyTimeoutRef.current);
      workflowReadyTimeoutRef.current = null;
    }
    if (workflowReadyClearRef.current) {
      clearTimeout(workflowReadyClearRef.current);
      workflowReadyClearRef.current = null;
    }
  }, []);
  const dismissWorkflowReady = useCallback((seq: any, delay = 650) => {
    if (workflowReadyClearRef.current) {
      clearTimeout(workflowReadyClearRef.current);
      workflowReadyClearRef.current = null;
    }
    workflowReadyClearRef.current = setTimeout(() => {
      setWorkflowReady((current: any) => (current && current.seq === seq ? null : current));
      workflowReadyClearRef.current = null;
    }, delay);
  }, []);
  const updateWorkflowReady = useCallback((seq: any, patch: any) => {
    if (!seq) return;
    setWorkflowReady((current: any) => (
      current && current.seq === seq
        ? { ...current, ...(patch || {}) }
        : current
    ));
  }, []);
  const finishWorkflowReady = useCallback((seq: any, patch: any = {}, delay = 650) => {
    if (!seq) return;
    if (workflowReadyTimeoutRef.current) {
      clearTimeout(workflowReadyTimeoutRef.current);
      workflowReadyTimeoutRef.current = null;
    }
    updateWorkflowReady(seq, { phase: 'ready', message: 'Ready to receive input', ...(patch || {}) });
    dismissWorkflowReady(seq, delay);
  }, [dismissWorkflowReady, updateWorkflowReady]);
  const failWorkflowReady = useCallback((seq: any, message: any) => {
    if (!seq) return;
    if (workflowReadyTimeoutRef.current) {
      clearTimeout(workflowReadyTimeoutRef.current);
      workflowReadyTimeoutRef.current = null;
    }
    updateWorkflowReady(seq, { phase: 'error', message: message || 'Workflow activation failed' });
    dismissWorkflowReady(seq, 1800);
  }, [dismissWorkflowReady, updateWorkflowReady]);
  const beginWorkflowReady = useCallback((target: any, session: any, ip: any = '') => {
    const seq = workflowReadySeqRef.current + 1;
    workflowReadySeqRef.current = seq;
    clearWorkflowReadyTimers();
    setWorkflowReady({
      seq,
      target: target || defaultWorkflowForExecMode(),
      session: normalizeUiSession(session || ''),
      ip: String(ip || '').trim(),
      phase: 'route',
      message: 'Switching chat route',
      startedAt: Date.now(),
    });
    workflowReadyTimeoutRef.current = setTimeout(() => {
      setWorkflowReady((current: any) => (
        current && current.seq === seq
          ? { ...current, phase: 'ready', message: 'Ready timeout reached; input is enabled' }
          : current
      ));
      dismissWorkflowReady(seq, 1000);
      workflowReadyTimeoutRef.current = null;
    }, WORKFLOW_READY_TIMEOUT_MS);
    return seq;
  }, [clearWorkflowReadyTimers, dismissWorkflowReady]);

  useEffect(() => () => clearWorkflowReadyTimers(), [clearWorkflowReadyTimers]);

  useEffect(() => {
    const nextWorkflow = String(activeWorkflow || '').trim();
    const known = (w.FLOW_STAGES || []).some((s: any) => s && s.id === nextWorkflow);
    if (!nextWorkflow || nextWorkflow === 'default') {
      setWorkflow(defaultWorkflowForExecMode());
    } else if (known) {
      setWorkflow(nextWorkflow);
    } else {
      setWorkflow(defaultWorkflowForExecMode());
    }
  }, [activeWorkflow]);

  // Mobile drawer state — left/right panels slide in over content on narrow viewports.
  const [leftDrawerOpen, setLeftDrawerOpen] = useState(false);
  const [rightDrawerOpen, setRightDrawerOpen] = useState(false);
  const [mobileHintDismissed, setMobileHintDismissed] = useState(() => {
    try { return localStorage.getItem('atlasMobileHintDismissed') === '1'; } catch (_) { return false; }
  });
  const isMobile = typeof window !== 'undefined' && window.innerWidth < 900;

  // Mobile header CustomEvent listeners — MobileHeader in app.jsx fires these
  // so the ☰ and ⋮ buttons in the compact header open the existing drawers.
  useEffect(() => {
    if (!isMobile) return undefined;
    const onLeft = () => { setLeftDrawerOpen(o => !o); setRightDrawerOpen(false); };
    const onRight = () => { setRightDrawerOpen(o => !o); setLeftDrawerOpen(false); };
    window.addEventListener('atlas:mobile-left-drawer', onLeft);
    window.addEventListener('atlas:mobile-right-drawer', onRight);
    return () => {
      window.removeEventListener('atlas:mobile-left-drawer', onLeft);
      window.removeEventListener('atlas:mobile-right-drawer', onRight);
    };
  }, [isMobile]);

  const NORMAL_FEED = [
    { kind: 'agent', text: 'Connected. Type a message and press Enter to talk to the agent.' },
  ];
  const PLAN_FEED = [
    { kind: 'agent', text: '**Plan mode** · read-only. The agent will analyze and propose without executing mutating tools. Use `apply` (or switch back to Normal) to run the plan.' },
  ];

  const resolveSession = useCallback((...candidates: any[]) => {
    for (const candidate of candidates) {
      try {
        const sid = normalizeUiSession(candidate || '');
        if (sid) return sid;
      } catch (_) {}
    }
    return 'default';
  }, []);

  const [feed, setFeed] = useState<any[]>(NORMAL_FEED);
  const [activeSession, setActiveSession] = useState(() => {
    try {
      // resolveActiveSession() prefers URL `?ip=` over the
      // localStorage `atlasActiveSession` snapshot — without that
      // precedence, a deep link like /?ip=cmux_url_test silently
      // resolves to the previous session's IP because localStorage
      // beat the URL.
      const sid = normalizeUiSession(activeNamespace || w.ACTIVE_SESSION || resolveActiveSession()) || 'default';
      w.ACTIVE_SESSION = sid;
      try { localStorage.setItem('atlasActiveSession', sid); } catch (_) {}
      return sid;
    } catch (_) {
      w.ACTIVE_SESSION = 'default';
      return 'default';
    }
  });
  const activeSessionRef = useRef(activeSession);
  const [chatViewSessionState, setChatViewSessionState] = useState('');
  const chatViewSessionRef = useRef('');
  const [inputRouteState, setInputRouteState] = useState<any>(() => initialInputRouteForExecMode());
  const inputRouteRef = useRef<any>(inputRouteState);
  const hydratedConversationSessionRef = useRef(activeSession);
  const liveFeedStartedRef = useRef(false);
  const workerLogCursorsRef = useRef(new Map());
  const setInputRoute = useCallback((route: any) => {
    const requestedType = String((route && route.type) || '').trim();
    const type = requestedType === 'workflow-dispatch'
      ? 'workflow-dispatch'
      : requestedType === 'workflow-chat'
        ? 'workflow-chat'
        : 'orchestrator-chat';
    const wf = type === 'orchestrator-chat'
      ? 'orchestrator'
      : workflowForExecMode((route && route.workflow) || '');
    const session = normalizeUiSession((route && route.session) || '');
    const next = {
      type,
      workflow: wf,
      session,
    };
    const prev = inputRouteRef.current || {};
    if (
      prev.type === next.type
      && prev.workflow === next.workflow
      && prev.session === next.session
    ) {
      return;
    }
    inputRouteRef.current = next;
    setInputRouteState(next);
  }, []);
  const sessionForInputRoute = useCallback((ip: any, wf: any) => {
    const workflowName = normalizeUiSession(wf || 'orchestrator') || 'orchestrator';
    const ipName = normalizeUiSession(
      ip || activeIpForRoute([
        w.ACTIVE_SESSION,
        activeSessionRef.current,
        activeSession,
        activeNamespace,
      ]) || ''
    ) || 'default';
    const parts = normalizeUiSession(w.ACTIVE_SESSION || activeSessionRef.current || activeSession || '').split('/').filter(Boolean);
    const owner = normalizeUiSession((w.ATLAS_USER && w.ATLAS_USER.username) || '') || parts[0] || 'default';
    return resolveSession(
      (w.atlasData && w.atlasData.sessionFor)
        ? w.atlasData.sessionFor(ipName, workflowName)
        : `${owner}/${ipName}/${workflowName}`,
    );
  }, [activeNamespace, activeSession, resolveSession]);
  const setOrchestratorInputRoute = useCallback((ip: any = '') => {
    const routeIp = ip || activeIpForRoute([
      w.ACTIVE_SESSION,
      activeSessionRef.current,
      activeSession,
      activeNamespace,
    ]);
    setInputRoute({
      type: 'orchestrator-chat',
      workflow: 'orchestrator',
      session: sessionForInputRoute(routeIp, 'orchestrator'),
    });
  }, [activeNamespace, activeSession, sessionForInputRoute, setInputRoute]);
  const setWorkflowDispatchInputRoute = useCallback((wf: any, ip: any = '') => {
    const workflowName = normalizeUiSession(wf || '');
    if (atlasUiOrchestratorMode() && (workflowName === 'orchestrator' || !workflowName)) {
      setOrchestratorInputRoute(ip);
      return;
    }
    const effectiveWorkflow = workflowForExecMode(workflowName || defaultWorkflowForExecMode());
    const routeIp = ip || activeIpForRoute([
      w.ACTIVE_SESSION,
      activeSessionRef.current,
      activeSession,
      activeNamespace,
    ]);
    setInputRoute({
      type: atlasUiOrchestratorMode() ? 'workflow-dispatch' : 'workflow-chat',
      workflow: effectiveWorkflow,
      session: sessionForInputRoute(routeIp, effectiveWorkflow),
    });
  }, [activeNamespace, activeSession, sessionForInputRoute, setInputRoute, setOrchestratorInputRoute]);
  const setChatViewSession = useCallback((sid: any) => {
    const normalized = normalizeUiSession(sid || '');
    chatViewSessionRef.current = normalized;
    setChatViewSessionState(normalized);
  }, []);
  useEffect(() => {
    const sid = normalizeUiSession(chatViewSessionState || '');
    if (!sid || workflowFromSession(sid) === 'orchestrator') return undefined;
    let cancelled = false;
    const tick = () => {
      if (cancelled) return;
      if (normalizeUiSession(chatViewSessionRef.current || '') !== sid) return;
      refreshChatSession(sid, { force: true, viewOnly: true });
    };
    const first = setTimeout(tick, 1500);
    const interval = setInterval(tick, 2500);
    return () => {
      cancelled = true;
      clearTimeout(first);
      clearInterval(interval);
    };
  }, [chatViewSessionState]);
  const appendLiveFeedEntries = useCallback((entries: any) => {
    const fresh = (Array.isArray(entries) ? entries : [entries])
      .filter(Boolean)
      .map((e: any) => ({ ...e, live: e.live !== false }));
    if (!fresh.length) return;
    liveFeedStartedRef.current = true;
    setFeed((f: any) => trimAtlasFeedState(coalesceAtlasFeedEntries(f, fresh)));
  }, []);
  useEffect(() => { activeSessionRef.current = activeSession; }, [activeSession]);
  useEffect(() => {
    const sid = normalizeUiSession(activeNamespace || '');
    if (!sid || sid === activeSessionRef.current) return;
    const prevSid = activeSessionRef.current;
    w.ACTIVE_SESSION = sid;
    activeSessionRef.current = sid;
    setActiveSession(sid);
    const newWf = sid.split('/').pop();
    setChatViewSession(newWf && newWf !== 'orchestrator' ? sid : '');
    try { localStorage.setItem('atlasActiveSession', sid); } catch (_) {}
    // A namespace change means a different IP/workflow transcript. Clear the
    // visible feed immediately so worker-to-worker switches don't keep showing
    // stale SSOT/RTL chat while the new conversation or worker log hydrates.
    if (sid !== prevSid) {
      liveFeedStartedRef.current = false;
      hydratedConversationSessionRef.current = sid;
      workerLogCursorsRef.current.clear();
      setFeed(NORMAL_FEED);
    }
    if (w.backend) {
      try {
        if (typeof w.backend.switchSession === 'function') w.backend.switchSession(sid);
        else if (typeof w.backend.connect === 'function') w.backend.connect(sid);
      } catch (_) {}
    }
    refreshChatSession(sid, { force: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeNamespace, setChatViewSession]);

  const refreshFeed = (newIntent: any, _newWorkflow?: any) => {
    // Do not reset the conversation on mode/workflow switches. The
    // authoritative history lives in .session/<workflow>/conversation.json
    // and is hydrated asynchronously; wiping the browser feed here makes
    // reloads and /wf transitions look like the session was lost.
    setFeed((f: any) => (f && f.length ? f : (newIntent === 'plan' ? PLAN_FEED : NORMAL_FEED)));
  };

  const activateSession = useCallback((scopePath: any, wf: any) => {
    const rawSid = (w.atlasData && w.atlasData.sessionFor)
      ? w.atlasData.sessionFor(scopePath || w.SCOPE_PATH || '', wf || '')
      : 'default';
    const sid = resolveSession(rawSid);
    const prevSid = normalizeUiSession(activeSessionRef.current || w.ACTIVE_SESSION || '');
    w.ACTIVE_SESSION = sid;
    activeSessionRef.current = sid;
    const ip = routeSessionIp(sid);
    if (ip) w.ACTIVE_IP = ip;
    const sessionWorkflow = workflowFromSession(sid);
    setChatViewSession(sessionWorkflow && sessionWorkflow !== 'orchestrator' ? sid : '');
    if (sid !== prevSid) {
      liveFeedStartedRef.current = false;
      hydratedConversationSessionRef.current = sid;
      workerLogCursorsRef.current.clear();
      setFeed(NORMAL_FEED);
    }
    setActiveSession(sid);
    try { localStorage.setItem('atlasActiveSession', sid); } catch (_) {}
    try {
      const parts = sid.split('/').filter(Boolean);
      const owner = parts[0] || '';
      window.dispatchEvent(new CustomEvent('atlas-session-switched', {
        detail: {
          sessionId: owner,
          namespace: sid,
          session: sid,
          ip,
          workflow: sessionWorkflow || wf || defaultWorkflowForExecMode(),
        },
      }));
    } catch (_) {}
    refreshChatSession(sid, { force: sid !== prevSid });
    return sid;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resolveSession, setChatViewSession]);

  const sendPrompt = useCallback((text: any, sessionOverride?: any) => {
    if (!w.backend || typeof w.backend.send !== 'function') {
      return { ok: false, error: 'backend unavailable' };
    }
    const activeSessionWorkflow = workflowFromSession(
      w.ACTIVE_SESSION
      || activeSessionRef.current
      || activeSession
      || activeNamespace
      || ''
    );
    const routeWorkflow = normalizeUiSession((inputRouteRef.current || {}).workflow || '');
    const promptWorkflow = String(
      atlasUiOrchestratorMode()
        ? 'orchestrator'
        : (
          activeSessionWorkflow
          || routeWorkflow
          || workflow
          || activeWorkflow
          || defaultWorkflowForExecMode()
          || ''
        )
    ).trim();
    const promptScope = (() => {
      return activeIpForRoute([
        w.ACTIVE_SESSION,
        activeSessionRef.current,
        activeSession,
        activeNamespace,
      ]);
    })();
    const canonicalSession = (w.atlasData && w.atlasData.sessionFor)
      ? w.atlasData.sessionFor(promptScope, promptWorkflow)
      : '';
    const session = resolveSession(
      sessionOverride,
      canonicalSession,
      w.ACTIVE_SESSION,
      activeSessionRef.current,
      activeSession,
      activeNamespace,
    );
    // crypto.randomUUID is secure-context only (localhost / https).
    // Accessing it from http://<lan-ip>/ throws — fall back to
    // getRandomValues, which IS available in non-secure contexts.
    let msg_id;
    try {
      msg_id = window.crypto.randomUUID();
    } catch (_) {
      const b = new Uint8Array(16);
      window.crypto.getRandomValues(b);
      b[6] = (b[6] & 0x0f) | 0x40;
      b[8] = (b[8] & 0x3f) | 0x80;
      const h = Array.from(b, x => x.toString(16).padStart(2, '0'));
      msg_id = `${h.slice(0, 4).join('')}-${h.slice(4, 6).join('')}-${h.slice(6, 8).join('')}-${h.slice(8, 10).join('')}-${h.slice(10, 16).join('')}`;
    }
    let cancelAckWait: any = null;
    const ack = (() => {
      if (!w.backend || typeof w.backend.subscribe !== 'function') {
        return Promise.resolve({ ok: false, error: 'backend ack unavailable' });
      }
      return new Promise((resolve) => {
        let done = false;
        let transportEvent: any = null;
        let unsubReceived: any = null;
        let unsubAccepted: any = null;
        let timer: any = null;
        const finish = (result: any) => {
          if (done) return;
          done = true;
          try { if (unsubReceived) unsubReceived(); } catch (_) {}
          try { if (unsubAccepted) unsubAccepted(); } catch (_) {}
          try { clearTimeout(timer); } catch (_) {}
          resolve(result);
        };
        cancelAckWait = () => finish({ ok: false, error: 'send failed before backend acceptance' });
        unsubReceived = w.backend.subscribe('agent_received', (m: any) => {
          if (!m || m.msg_id !== msg_id) return;
          transportEvent = m;
        });
        unsubAccepted = w.backend.subscribe('agent_accepted', (m: any) => {
          if (!m || m.msg_id !== msg_id) return;
          if (m.ok === false) {
            finish({
              ok: false,
              error: m.error || 'backend received input but did not accept it',
              event: m,
              transport: transportEvent,
            });
            return;
          }
          finish({ ok: true, event: m, transport: transportEvent });
        });
        timer = setTimeout(() => {
          finish({
            ok: false,
            error: transportEvent
              ? 'backend received input but did not confirm worker delivery'
              : 'backend did not acknowledge receipt',
            transport: transportEvent,
          });
        }, 7000);
      });
    })();
    const msg = {
      type: 'prompt',
      msg_id,
      text,
      session,
      ip: promptScope,
      workflow: promptWorkflow,
      ui_lang: w.ATLAS_UI_LANG || uiLang,
    };
    try {
      w.backend.send(msg);
    } catch (e: any) {
      try { if (cancelAckWait) cancelAckWait(); } catch (_) {}
      return { ok: false, error: String(e && e.message || e) };
    }
    return { ok: true, msg_id, session, workflow: promptWorkflow, ip: promptScope, ack };
  }, [activeNamespace, activeSession, activeWorkflow, resolveSession, uiLang, workflow]);

  const switchToDefaultSession = useCallback(() => {
    const sid = (w.atlasData && w.atlasData.sessionFor)
      ? (w.atlasData.sessionFor('', '') || 'default')
      : 'default';
    w.ACTIVE_SESSION = sid;
    setActiveSession(sid);
    try { localStorage.setItem('atlasActiveSession', sid); } catch (_) {}
    refreshChatSession(sid);
    return sid;
  }, []);

  const handleSwitchSession = useCallback(async (sessionId: any) => {
    const owner = normalizeUiSession((w.ATLAS_USER && w.ATLAS_USER.username) || '') || sessionId;
    const current = normalizeUiSession(activeSession || w.ACTIVE_SESSION || '');
    const suffix = current.split('/').slice(1).join('/');
    const newNamespace = suffix ? `${owner}/${suffix}` : owner;

    try {
      await fetch('/api/sessions/' + encodeURIComponent(owner) + '/activate', { method: 'POST' });
    } catch (_) {}

    window.history.replaceState(null, '', '/?session_id=' + encodeURIComponent(owner));

    if (w.backend) {
      if (w.backend.switchSession) w.backend.switchSession(newNamespace);
      else if (w.backend.connect) w.backend.connect(newNamespace);
    }

    w.ACTIVE_SESSION = newNamespace;
    setActiveSession(newNamespace);
    try { localStorage.setItem('atlasActiveSession', newNamespace); } catch (_) {}

    setStreaming(false);
    streamBufferRef.current = '';
    setStreamText('');

    refreshChatSession(newNamespace);

    window.dispatchEvent(new CustomEvent('atlas-session-switched', { detail: { sessionId: owner, namespace: newNamespace } }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeSession]);

  const switchIntent = (i: any) => {
    setIntent(i);
    refreshFeed(i, workflow);
    // Tell the BACKEND about the mode swap — local React state alone
    // doesn't change the agent's behaviour. /plan flips agent_mode to
    // 'plan' (no mutating tools); /mode normal flips it back.
    if (w.backend) {
      const cmd = i === 'plan' ? '/plan' : '/mode normal';
      sendPrompt(cmd);
    }
  };
  const switchWorkflow = async (workflowArg: any) => {
    // Click a workflow chip → activate the backend workspace through the
    // canonical session API. The API path performs the workspace setup
    // synchronously; stale queued `/wf` prompts are avoided because they
    // can land late during fast workflow sweeps.
    const currentWorkflow = workflow || '';
    const next = (currentWorkflow === workflowArg ? defaultWorkflowForExecMode() : workflowArg) || defaultWorkflowForExecMode();
    const sessionWorkflow = workflowFromSession(activeSession || w.ACTIVE_SESSION || '');
    if ((next || '') === currentWorkflow && !(next === 'orchestrator' && sessionWorkflow !== 'orchestrator')) return;
    const runningNow = streamingRef.current || w.ATLAS_AGENT_RUNNING === true;
    // In orchestrator mode the orchestrator coordinates workers across stages,
    // and the left-rail workflow chips just switch which worker's workspace is
    // *viewed* — switching must NOT stop the run. Only single-worker mode binds
    // one agent to the active workflow, so only it prompts to stop before switch.
    const orchestratorMode = atlasUiOrchestratorMode();
    if (runningNow && !orchestratorMode) {
      const label = next || 'default';
      if (!window.confirm(`Agent is running. Stop it and switch workflow to "${label}"?`)) return;
      try { if (w.backend) w.backend.send({ type: 'stop' }); } catch (_) {}
      try {
        fetch('/api/control/stop', {
          method: 'POST', cache: 'no-store', keepalive: true,
        }).catch(() => {});
      } catch (_) {}
    }
    if (!orchestratorMode) {
      setStreaming(false);
      try {
        w.ATLAS_AGENT_RUNNING = false;
        window.dispatchEvent(new CustomEvent('atlas-agent-running', { detail: { running: false } }));
      } catch (_) {}
    }
    if (orchestratorMode) {
      const viewWorkflow = next || 'orchestrator';
      const parts = normalizeUiSession(activeSession || w.ACTIVE_SESSION || '').split('/').filter(Boolean);
      const routeIp = activeIpForRoute([
        w.ACTIVE_SESSION,
        activeSessionRef.current,
        activeSession,
        activeNamespace,
      ]);
      const owner = normalizeUiSession((w.ATLAS_USER && w.ATLAS_USER.username) || '') || parts[0] || 'default';
      const ip = (routeIp && routeIp !== 'default')
        ? routeIp
        : ((parts.length >= 3 && parts[1]) ? parts[1] : 'default');
      const sessionFor = (wfArg: any) => resolveSession(
        (w.atlasData && w.atlasData.sessionFor)
          ? w.atlasData.sessionFor(ip, wfArg)
          : `${owner}/${ip}/${wfArg}`
      );
      const orchestratorSid = sessionFor('orchestrator');
      const activeNow = normalizeUiSession(w.ACTIVE_SESSION || activeSessionRef.current || '');
      const viewSid = viewWorkflow === 'orchestrator' ? orchestratorSid : sessionFor(viewWorkflow);
      const readySeq = beginWorkflowReady(viewWorkflow, viewSid, ip);

      // In orchestrator execution the backend websocket and prompt target must
      // stay on the orchestrator session. Worker chips are a transcript/artifact
      // view only; switching the runtime to a worker namespace drops future
      // orchestrator replies on the floor.
      if (activeNow !== orchestratorSid) {
        w.ACTIVE_SESSION = orchestratorSid;
        activeSessionRef.current = orchestratorSid;
        setActiveSession(orchestratorSid);
        try { localStorage.setItem('atlasActiveSession', orchestratorSid); } catch (_) {}
        if (w.backend) {
          try {
            if (typeof w.backend.switchSession === 'function') w.backend.switchSession(orchestratorSid);
            else if (typeof w.backend.connect === 'function') w.backend.connect(orchestratorSid);
          } catch (_) {}
        }
      }
      updateWorkflowReady(readySeq, { phase: 'session', message: 'View session selected' });

      setWorkflow(viewWorkflow);
      w.CONTEXT = Object.assign({}, w.CONTEXT || {}, {
        workspace: 'orchestrator',
        view_workspace: viewWorkflow,
      });
      refreshFeed(intent, viewWorkflow);
      setMainTab('chat');
      if (viewWorkflow === 'orchestrator') {
        setOrchestratorInputRoute(ip);
        setChatViewSession('');
        refreshChatSession(orchestratorSid, { force: true });
        finishWorkflowReady(readySeq, { message: 'Orchestrator view ready' });
        return;
      }
      liveFeedStartedRef.current = false;
      hydratedConversationSessionRef.current = viewSid;
      setChatViewSession(viewSid);
      setWorkflowDispatchInputRoute(viewWorkflow, ip);
      requestAnimationFrame(() => setMainTab('chat'));
      refreshChatSession(viewSid, { force: true, viewOnly: true });
      finishWorkflowReady(readySeq, { message: 'Worker view ready' });
      return;
    }
    setWorkflow(next);
    w.CONTEXT = Object.assign({}, w.CONTEXT || {}, { workspace: next });
    refreshFeed(intent, next);
    const sid = activateSession(w.SCOPE_PATH || '', next);
    const parts = (activeSession || w.ACTIVE_SESSION || '').split('/');
    const owner = normalizeUiSession((w.ATLAS_USER && w.ATLAS_USER.username) || '') || parts[0] || 'default';
    const ip = w.SCOPE_PATH || parts[1] || 'default';
    setWorkflowDispatchInputRoute(next, ip);
    setChatViewSession(sid);
    const readySeq = beginWorkflowReady(next, sid, ip);
    updateWorkflowReady(readySeq, { phase: 'session', message: 'Session selected' });
    let activated = false;
    let activationPayload: any = null;
    let activationReadyFailed = false;
    try {
      updateWorkflowReady(readySeq, { phase: 'backend', message: 'Activating backend session' });
      const res = await fetch('/api/session/activate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          owner,
          ip: ip,
          workflow: next,
        }),
      });
      activationPayload = await res.json().catch(() => null);
      activated = !!(res && res.ok);
      if (!activated) {
        updateWorkflowReady(readySeq, { phase: 'backend', message: 'Backend activation fallback queued' });
      } else {
        const warm = activationPayload && activationPayload.session_worker_warmup;
        const warmStatus = warm && String(warm.status || '').trim();
        const warmAlive = warm && warm.alive === true;
        const warmEnabled = warm && warm.enabled !== false;
        updateWorkflowReady(readySeq, {
          phase: 'worker',
          message: warmEnabled
            ? `Session worker ${warmStatus || (warmAlive ? 'ready' : 'warming')}`
            : 'Backend session active',
        });
        if (warmEnabled && warm.alive === false && warmStatus === 'error') {
          activationReadyFailed = true;
          failWorkflowReady(readySeq, warm.error || 'Session worker failed to start');
        } else if (warmAlive || !warmEnabled) {
          updateWorkflowReady(readySeq, {
            phase: 'worker',
            message: warmAlive ? 'Session worker hot; ready to receive input' : 'Backend route ready',
          });
        }
      }
    } catch (_) {}
    if (w.backend) {
      updateWorkflowReady(readySeq, { phase: 'worker', message: 'Binding websocket to workflow session' });
      if (w.backend.switchSession) w.backend.switchSession(sid);
      else if (w.backend.connect) w.backend.connect(sid);
      if (!activated && next !== 'orchestrator') {
        sendPrompt(`/wf ${next}`, sid);
      }
    }
    if (activationReadyFailed) {
      return;
    }
    if (!activated) {
      if (w.backend) {
        finishWorkflowReady(readySeq, { message: 'Fallback route queued; input route ready' }, 1200);
      } else {
        failWorkflowReady(readySeq, 'Backend is not connected');
      }
    } else if (activationPayload) {
      const warm = activationPayload.session_worker_warmup;
      finishWorkflowReady(readySeq, {
        message: warm && warm.alive === true
          ? 'Session worker hot; ready to receive input'
          : 'Workflow session ready',
      });
    }
  };
  useEffect(() => {
    const onWorkflowViewRequest = (ev: any) => {
      const wf = String((ev && ev.detail && ev.detail.workflow) || '').trim();
      if (!wf) return;
      switchWorkflow(wf);
    };
    window.addEventListener('atlas-workflow-view-request', onWorkflowViewRequest);
    return () => window.removeEventListener('atlas-workflow-view-request', onWorkflowViewRequest);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [switchWorkflow]);

  return {
    // mode model
    intent, setIntent,
    workflow, setWorkflow,
    workflowReady, setWorkflowReady,
    workflowReadySeqRef,
    workflowReadyTimeoutRef,
    workflowReadyClearRef,
    clearWorkflowReadyTimers,
    dismissWorkflowReady,
    updateWorkflowReady,
    finishWorkflowReady,
    failWorkflowReady,
    beginWorkflowReady,
    // drawer state
    leftDrawerOpen, setLeftDrawerOpen,
    rightDrawerOpen, setRightDrawerOpen,
    mobileHintDismissed, setMobileHintDismissed,
    isMobile,
    // feed seeds + state
    NORMAL_FEED,
    PLAN_FEED,
    feed, setFeed,
    appendLiveFeedEntries,
    refreshFeed,
    // session + refs
    resolveSession,
    activeSession, setActiveSession,
    activeSessionRef,
    chatViewSessionState, setChatViewSessionState,
    chatViewSessionRef,
    inputRouteState, setInputRouteState,
    inputRouteRef,
    hydratedConversationSessionRef,
    liveFeedStartedRef,
    workerLogCursorsRef,
    // input-route resolution
    setInputRoute,
    sessionForInputRoute,
    setOrchestratorInputRoute,
    setWorkflowDispatchInputRoute,
    setChatViewSession,
    // session transition handlers
    activateSession,
    sendPrompt,
    switchToDefaultSession,
    handleSwitchSession,
    switchIntent,
    switchWorkflow,
  };
}
