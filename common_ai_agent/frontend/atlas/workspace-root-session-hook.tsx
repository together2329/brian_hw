// workspace-root-session-hook.tsx — the session/workflow/feed/streaming state
// machine carved out of the Workspace closure (strangler-fig TS split).
//
// Workspace used to live in workspace.jsx as a ~5,315-line monolith. The Vite
// workspace entry now composes cohesive TS hooks from workspace-root.tsx. THIS
// file owns the upper half of that closure: the two-axis intent/workflow mode model, the
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
// Typed in the permissive house style: window-sourced and dynamically-shaped
// values are `any` on purpose; do NOT tighten them in this migration slice.
import { useState, useEffect, useRef, useCallback } from 'react';
import type { MutableRefObject, Dispatch, SetStateAction } from 'react';
// PURE, unit-tested switch-gate (session-machine.test.ts: 16 green). Unlike the
// legacy workspace.jsx — a classic Babel <script> that had to inline-port this —
// the .tsx is bundled by vite and IMPORTS the canonical module directly, so the
// gate semantics cannot drift from the spec.
import { createSwitchGate } from './session-machine';
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
import { toPromptWireImages } from './workspace-prompt-images';
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

// Return type is INFERRED (no `: any`) so the composer's typed `ws` bag can see
// every key this hook exposes — tsc then ERRORS if workspace-root.tsx
// destructures a symbol this hook (or its data sibling) never returns. This is
// the gate that an `any` return previously hid.
export function useWorkspaceSession(deps: UseWorkspaceSessionDeps) {
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
  // ── switch-gate (synchronous mirror of workflowReady) ──────────────
  // workflowReady is React state: setWorkflowReady() only takes effect after
  // React commits, leaving a one-frame window where submitMsg's closed-over
  // workflowReady is still null and a prompt can be SENT into a session that is
  // already switching away (the prompt is then wiped by backend.js liveConnect
  // sessionChanged). This ref-held gate is a SYNCHRONOUS source of truth set in
  // the SAME tick as setWorkflowReady, so submitMsg can read "switching"
  // immediately and HOLD instead of send. It is the real, unit-tested factory
  // from session-machine.ts (the .jsx had to inline-port it; the .tsx imports it).
  const switchGateRef = useRef(createSwitchGate());

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
      // Seq-guard EVERYTHING in this timer, not just setWorkflowReady. A stale
      // dismiss timer (its switch was superseded by a newer beginWorkflowReady,
      // which bumped the seq) must NOT reopen the gate: the newer switch owns the
      // gate now and is still "switching". Reopening here would let input flow
      // (and the replay effect drain) mid-switch — the very race the gate closes.
      let owns = false;
      setWorkflowReady((current: any) => {
        owns = !!(current && current.seq === seq);
        return owns ? null : current;
      });
      // Switch settled (overlay dismissed): reopen the synchronous gate so input
      // flows again. Held msgs are preserved for the replay effect to drain.
      if (owns && switchGateRef.current) switchGateRef.current.markReady();
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
    if (workflowReadySeqRef.current === seq && switchGateRef.current) {
      switchGateRef.current.markReady();
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
    // Switch failed: reopen the gate immediately so input flows again. Held msgs
    // are preserved (no data loss); dismissWorkflowReady() will also markReady().
    // Seq-guard the gate call: a stale fail (its switch was superseded by a newer
    // beginWorkflowReady that bumped workflowReadySeqRef) must NOT reopen the gate
    // the newer switch now owns. Only the live owner may flip the gate to ready.
    if (workflowReadySeqRef.current === seq && switchGateRef.current) {
      switchGateRef.current.markFailed();
    }
    dismissWorkflowReady(seq, 1800);
  }, [dismissWorkflowReady, updateWorkflowReady]);
  const beginWorkflowReady = useCallback((target: any, session: any, ip: any = '') => {
    const seq = workflowReadySeqRef.current + 1;
    workflowReadySeqRef.current = seq;
    clearWorkflowReadyTimers();
    // SYNCHRONOUS write that beats React's commit: from this instant submitMsg's
    // gate read reports "switching" and HOLDS the prompt (closing the one-frame
    // race where the stale-closure workflowReady===null let a send through).
    // beginSwitch preserves any already-held pending across a re-switch.
    if (switchGateRef.current) {
      switchGateRef.current.beginSwitch(normalizeUiSession(session || '') || String(target || ''));
    }
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
      // BUG B: workflowReadyTimeoutRef is a SINGLE shared slot. If an overlapping
      // switch A resolved after switch B armed this net, A's finish/fail cleared B's
      // timer out of the shared slot — so dismissWorkflowReady's deferred markReady
      // may never run, and if B's continuation fetch never settles the gate is stuck
      // 'switching' forever. Give the LIVE switch a seq-guarded, direct reopen here so
      // the synchronous gate is guaranteed to reopen at the deadline regardless of the
      // shared-slot clobber. The seq guard (mirroring failWorkflowReady L178) preserves
      // the deliberate suppression of stale reopens — only the current owner reopens.
      if (workflowReadySeqRef.current === seq && switchGateRef.current) {
        switchGateRef.current.markReady();
      }
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
    { kind: 'agent', text: 'Workspace loaded.' },
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
    const workspaceSession = (
      (parts.length >= 4 && parts[0] === owner ? parts[1] : '')
      || normalizeUiSession((w as any).ATLAS_WORKSPACE_SESSION_ID || '')
      || 'default'
    );
    return resolveSession(
      (w.atlasData && w.atlasData.sessionFor)
        ? w.atlasData.sessionFor(ipName, workflowName)
        : `${owner}/${workspaceSession}/${ipName}/${workflowName}`,
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

  const sendPrompt = useCallback((text: any, sessionOverride?: any, msgIdOverride?: any) => {
    if (!w.backend || typeof w.backend.send !== 'function') {
      return { ok: false, error: 'backend unavailable' };
    }
    const promptText = typeof text === 'string' ? text : String(text?.text ?? '');
    const promptImages = typeof text === 'string'
      ? []
      : toPromptWireImages(Array.isArray(text?.images) ? text.images : []);
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
      const currentRoute = normalizeUiSession(
        w.ACTIVE_SESSION
        || activeSessionRef.current
        || activeSession
        || ''
      );
      const currentRouteIp = activeIpForRoute([
        w.ACTIVE_SESSION,
        activeSessionRef.current,
        activeSession,
      ]);
      if (currentRouteIp) return currentRouteIp;
      if (currentRoute.split('/').filter(Boolean).length >= 4) return 'default';
      return activeIpForRoute([activeNamespace]);
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
    //
    // msgIdOverride: a held-input REPLAY (ack-miss re-fire) passes the ORIGINAL
    // send's msg_id so the backend's per-session has_msg_id dedup collapses the
    // replay against the first send — preventing the double-execution race where
    // a fresh msg_id would slip past dedup if the worker warmed up in between.
    let msg_id = String(msgIdOverride || '').trim();
    if (!msg_id) {
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
    }
    let cancelAckWait: any = null;
    let lateResolvedCb: ((e: any) => void) | null = null;
    const onAckResolved = (cb: (e: any) => void) => { lateResolvedCb = cb; };
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
        const teardown = () => {
          try { if (unsubReceived) unsubReceived(); } catch (_) {}
          try { if (unsubAccepted) unsubAccepted(); } catch (_) {}
          try { clearTimeout(timer); } catch (_) {}
        };
        const finish = (result: any) => {
          if (done) return;
          done = true;
          teardown();
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
            if (done) {
              try { teardown(); } catch (_) {}
              try {
                if (lateResolvedCb) {
                  lateResolvedCb({
                    ok: false,
                    error: m.error || 'backend received input but did not accept it',
                    event: m,
                    transport: transportEvent,
                  });
                }
              } catch (_) {}
              return;
            }
            finish({
              ok: false,
              error: m.error || 'backend received input but did not accept it',
              event: m,
              transport: transportEvent,
            });
            return;
          }
          if (done) {
            try { teardown(); } catch (_) {}
            try { if (lateResolvedCb) lateResolvedCb({ ok: true, event: m, transport: transportEvent }); } catch (_) {}
            return;
          }
          finish({ ok: true, event: m, transport: transportEvent });
        });
        timer = setTimeout(() => {
          if (done) return;
          if (transportEvent) {
            done = true;
            try { if (unsubReceived) { unsubReceived(); unsubReceived = null; } } catch (_) {}
            try { clearTimeout(timer); } catch (_) {}
            resolve({
              ok: false,
              pending: true,
              latency: true,
              msg_id,
              error: 'backend received input but did not confirm worker delivery',
              transport: transportEvent,
            });
            return;
          }
          finish({
            ok: false,
            error: 'backend did not acknowledge receipt',
          });
        }, 7000);
      });
    })();
    const msg: any = {
      type: 'prompt',
      msg_id,
      text: promptText,
      session,
      ip: promptScope,
      workflow: promptWorkflow,
      ui_lang: w.ATLAS_UI_LANG || uiLang,
    };
    if (promptImages.length) {
      msg.images = promptImages;
    }
    try {
      w.backend.send(msg);
    } catch (e: any) {
      try { if (cancelAckWait) cancelAckWait(); } catch (_) {}
      return { ok: false, error: String(e && e.message || e) };
    }
    return { ok: true, msg_id, session, workflow: promptWorkflow, ip: promptScope, ack, onAckResolved };
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
    const workspaceSession = normalizeUiSession(sessionId || (w as any).ATLAS_WORKSPACE_SESSION_ID || '') || 'default';
    const current = normalizeUiSession(activeSession || w.ACTIVE_SESSION || '');
    const curParts = current.split('/').filter(Boolean);
    const ip = routeSessionIp(current) || curParts[curParts.length - 2] || 'default';
    const workflow = workflowFromSession(current) || curParts[curParts.length - 1] || 'default';
    const newNamespace = `${owner}/${workspaceSession}/${ip}/${workflow}`;

    try {
      await fetch('/api/sessions/' + encodeURIComponent(owner) + '/activate', { method: 'POST' });
    } catch (_) {}

    (w as any).ATLAS_WORKSPACE_SESSION_ID = workspaceSession;
    try { localStorage.setItem('atlasWorkspaceSessionId', workspaceSession); } catch (_) {}
    window.history.replaceState(null, '', '/?session_id=' + encodeURIComponent(owner) + '&session=' + encodeURIComponent(newNamespace));

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
    setStreaming(false);
    streamBufferRef.current = '';
    setStreamText('');
    if (!orchestratorMode) {
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
    const routeIp = activeIpForRoute([
      w.ACTIVE_SESSION,
      activeSessionRef.current,
      activeSession,
      activeNamespace,
    ]) || 'default';
    const sid = activateSession(routeIp, next);
    const parts = (sid || activeSession || w.ACTIVE_SESSION || '').split('/');
    const owner = normalizeUiSession((w.ATLAS_USER && w.ATLAS_USER.username) || '') || parts[0] || 'default';
    const workspaceSession = parts.length >= 4 && parts[0] === owner ? parts[1] : 'default';
    const ip = routeSessionIp(sid) || routeIp || (parts.length >= 4 ? parts[2] : parts[1]) || 'default';
    w.ACTIVE_IP = ip;
    setWorkflowDispatchInputRoute(next, ip);
    setChatViewSession(sid);
    const readySeq = beginWorkflowReady(next, sid, ip);
    updateWorkflowReady(readySeq, { phase: 'session', message: 'Session selected' });
    if (w.backend) {
      updateWorkflowReady(readySeq, { phase: 'session', message: 'Binding websocket to workflow session' });
      if (w.backend.switchSession) w.backend.switchSession(sid);
      else if (w.backend.connect) w.backend.connect(sid);
    }
    let activated = false;
    let activationPayload: any = null;
    let activationReadyFailed = false;
    let activationStatus = 0;
    try {
      updateWorkflowReady(readySeq, { phase: 'backend', message: 'Activating backend session' });
      const res = await fetch('/api/session/activate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          owner,
          workspace_session: workspaceSession,
          ip: ip,
          workflow: next,
        }),
      });
      activationStatus = Number((res && res.status) || 0);
      activationPayload = await res.json().catch(() => null);
      activated = !!(res && res.ok);
      if (!activated) {
        const rejected = activationStatus >= 400 && activationStatus < 500;
        updateWorkflowReady(readySeq, {
          phase: 'backend',
          message: rejected ? 'Backend activation rejected' : 'Backend activation fallback queued',
        });
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
      const canFallbackPrompt = !activated && !(activationStatus >= 400 && activationStatus < 500);
      if (canFallbackPrompt && next !== 'orchestrator') {
        sendPrompt(`/wf ${next}`, sid);
      }
    }
    if (activationReadyFailed) {
      return;
    }
    if (!activated) {
      if (activationStatus >= 400 && activationStatus < 500) {
        const message = (activationPayload && (activationPayload.error || activationPayload.message))
          || `Backend activation rejected (${activationStatus})`;
        failWorkflowReady(readySeq, message);
      } else if (w.backend) {
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
    // Synchronous switch-gate: submitMsg consults switchGateRef.current.isSwitching()
    // (or .submit()) BEFORE sending so input typed in the one-frame window after a
    // switch is HELD, not eaten. Exported so the input/submit layer can read it.
    switchGateRef,
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
