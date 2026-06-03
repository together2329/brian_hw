// app.tsx — TypeScript migration of app.jsx (strangler-fig). Top-level shell.
// Renders Workspace only. Owns dir + theme.
//
// Launcher and Pipeline screens were design-time mocks and have been
// removed; the live agent UI lives entirely inside Workspace.
//
// Split: the module-level helpers + standalone status components +
// ErrorBoundary moved to app-helpers.tsx; the mobile header family moved to
// app-mobile.tsx; the entire presentational render tree moved to app-shell.tsx
// (AppShell); the agent-running/workspace-switch state moved to
// app-agent-hook.tsx (useAtlasAgentRunning); the boot-handshake state machine
// moved to app-boot-hook.tsx (useAtlasBoot). This file keeps the irreducibly
// large `App` root component's stateful hook body (a single React function
// whose hooks/closures share namespace/auth state and so cannot be split
// mid-function without changing behavior) and the createRoot().render() entry.
//
// Automatic JSX runtime — no React import needed for JSX. We still read the
// global React/ReactDOM owned by the page bootstrap via window where needed.
import { useState, useEffect, useCallback, useMemo, useRef, useReducer } from 'react';
import {
  DEFAULT_ATLAS_RESOLUTION,
  atlasResolutionPreset,
  DEFAULT_ATLAS_EXEC_MODE,
  ATLAS_EXEC_MODE_LOCKED,
  normalizeAtlasFontMode,
  normalizeAtlasRunMode,
  normalizeAtlasExecMode,
  atlasBootConfig,
  atlasPolicyConfig,
  mergeAtlasPolicyResponse,
  atlasShouldHoldDashboardActivation,
} from './app-helpers';
import { useAtlasAgentRunning } from './app-agent-hook';
import { useAtlasBoot } from './app-boot-hook';
import { useAtlasAuthGate } from './app-auth-hook';
import { useAtlasSessionSync } from './app-session-hook';
import { useAtlasScreen } from './app-screen-hook';
import { AppShell } from './app-shell';

const App = () => {
  const dir = 'B';     // Workbench is the only visible Atlas shell mode.
  const [theme, setTheme] = useState('dark');
  const [uiLang, setUiLang] = useState(() => {
    try {
      const saved = localStorage.getItem('atlasUiLang');
      const explicit = localStorage.getItem('atlasUiLangUserSet') === '1';
      return explicit && saved === 'ko' ? 'ko' : 'en';
    }
    catch (_) { return 'en'; }
  });
  const [fontMode, setFontMode] = useState(() => {
    // Default to 'mono' (SF Mono — the orchestrator-chat demo look). Only a
    // font the user explicitly picked from the dropdown overrides it; a
    // stale non-user-set value falls through to mono.
    try {
      const saved = normalizeAtlasFontMode(localStorage.getItem('atlasFontMode'));
      const userSet = localStorage.getItem('atlasFontModeUserSet') === '1';
      if (saved && userSet) return saved;
      return 'mono';
    } catch (_) { return 'mono'; }
  });
  const [fontScale, setFontScale] = useState(() => {
    // Default to 'compact' (13px base) — matches the orchestrator-chat demo
    // the user signed off on. The size dropdown bumps it up from here.
    try {
      const saved = localStorage.getItem('atlasFontScale');
      return ['compact', 'normal', 'large', 'xl'].includes(saved as string) ? (saved as string) : 'compact';
    } catch (_) { return 'compact'; }
  });
  const [resolution, setResolution] = useState(() => {
    try {
      return atlasResolutionPreset(localStorage.getItem('atlasResolution') as string).key;
    } catch (_) { return DEFAULT_ATLAS_RESOLUTION; }
  });
  const [runMode, setRunMode] = useState(() => {
    try { return normalizeAtlasRunMode(atlasBootConfig().run_mode || localStorage.getItem('atlasRunMode')); }
    catch (_) { return 'engineering'; }
  });
  const [execMode, setExecMode] = useState(() => {
    if (ATLAS_EXEC_MODE_LOCKED) return 'single-worker';
    try { return normalizeAtlasExecMode(atlasBootConfig().exec_mode || localStorage.getItem('atlasExecMode')); }
    catch (_) { return DEFAULT_ATLAS_EXEC_MODE; }
  });
  useEffect(() => {
    window.ATLAS_UI_LANG = uiLang;
    try { localStorage.setItem('atlasUiLang', uiLang); } catch (_) {}
    window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'UI_LANG' }));
  }, [uiLang]);
  useEffect(() => {
    try { localStorage.setItem('atlasFontMode', fontMode); } catch (_) {}
  }, [fontMode]);
  useEffect(() => {
    try { localStorage.setItem('atlasFontScale', fontScale); } catch (_) {}
  }, [fontScale]);
  useEffect(() => {
    const preset = atlasResolutionPreset(resolution);
    document.documentElement.setAttribute('data-resolution', preset.key);
    document.documentElement.style.setProperty('--atlas-canvas-w', `${preset.width}px`);
    document.documentElement.style.setProperty('--atlas-canvas-h', `${preset.height}px`);
    window.ATLAS_RESOLUTION = preset;
    try { localStorage.setItem('atlasResolution', preset.key); } catch (_) {}
    window.dispatchEvent(new CustomEvent('atlas-resolution-changed', { detail: preset }));
  }, [resolution]);
  useEffect(() => {
    window.ATLAS_RUN_MODE = runMode;
    window.ATLAS_EXEC_MODE = execMode;
    try {
      localStorage.setItem('atlasRunMode', runMode);
      localStorage.setItem('atlasExecMode', execMode);
    } catch (_) {}
    try {
      window.dispatchEvent(new CustomEvent('atlas-run-policy-changed', {
        detail: { run_mode: runMode, exec_mode: execMode },
      }));
    } catch (_) {}
  }, [runMode, execMode]);
  useEffect(() => {
    const clearBootAssetBanner = () => {
      try {
        if (
          window.React &&
          window.ReactDOM &&
          window.Babel &&
          window.marked &&
          window.mermaid &&
          window.DOMPurify &&
          window.Prism &&
          typeof window.__atlasClearAssetLoadErrors === 'function'
        ) {
          window.__atlasClearAssetLoadErrors();
        }
      } catch (_) {}
    };
    clearBootAssetBanner();
    const t = setTimeout(clearBootAssetBanner, 500);
    return () => clearTimeout(t);
  }, []);
  const chooseUiLang = useCallback((next: string) => {
    setUiLang(next === 'ko' ? 'ko' : 'en');
    try { localStorage.setItem('atlasUiLangUserSet', '1'); } catch (_) {}
  }, []);
  const TOP_WORKFLOWS = useMemo(() => new Set([
    'architect', 'contract-reflection', 'coverage', 'fl-model-gen', 'goal-audit', 'lint',
    'mas-gen', 'orchestrator', 'pnr', 'rtl-gen', 'signoff', 'sim', 'sim_debug',
    'ssot-gen', 'sta', 'sta-post', 'syn', 'tb-gen',
  ]), []);
  const WORKFLOW_DEFAULT = 'default';
  const WORKFLOW_OPTIONS = useMemo(() => {
    const sorted = Array.from(TOP_WORKFLOWS)
      .filter(wf => wf !== 'orchestrator')
      .sort();
    if (execMode === 'orchestrator') {
      return ['orchestrator', WORKFLOW_DEFAULT].concat(sorted);
    }
    return [WORKFLOW_DEFAULT].concat(sorted);
  }, [TOP_WORKFLOWS, execMode]);
  const isWorkflowSegment = useCallback((value: unknown) => {
    const wf = String(value || '');
    return wf === WORKFLOW_DEFAULT || TOP_WORKFLOWS.has(wf);
  }, [TOP_WORKFLOWS]);
  const normalizeSession = useCallback((value: unknown): string => {
    const norm = (window.atlasData && window.atlasData.normalizeSessionName) || window.normalizeAtlasSessionName;
    try { return (norm && norm(value || '')) || ''; }
    catch (_) { return ''; }
  }, []);
  const newIpInitialWorkflow = useCallback(() => {
    const policy = atlasPolicyConfig();
    const mode = normalizeAtlasExecMode(execMode || policy.exec_mode || window.ATLAS_EXEC_MODE || window.ATLAS_DEFAULT_EXEC_MODE);
    if (mode === 'orchestrator') return 'orchestrator';
    return normalizeSession(policy.initial_workflow || '') || 'default';
  }, [execMode, normalizeSession]);
  const preserveRunningForCurrentMode = useCallback(() => {
    const policy = atlasPolicyConfig();
    if (window.AtlasExecPolicy && window.AtlasExecPolicy.preserveRunning) {
      try { return window.AtlasExecPolicy.preserveRunning(policy, execMode); } catch (_) {}
    }
    return !!policy.preserve_running_on_workflow_switch;
  }, [execMode]);
  const loggedInOwner = useCallback(() => (
    normalizeSession((window.ATLAS_USER && window.ATLAS_USER.username) || '')
  ), [normalizeSession]);

  const splitSessionNamespace = useCallback((session: unknown) => {
    const sid = normalizeSession(session);
    const parts = sid.split('/').filter(Boolean);
    if (!parts.length) return { sessionId: WORKFLOW_DEFAULT, ipId: WORKFLOW_DEFAULT, workflow: WORKFLOW_DEFAULT };
    const last = parts[parts.length - 1];
    if (parts.length >= 3 && isWorkflowSegment(last)) {
      return {
        sessionId: parts[0],
        workspaceSession: parts.length >= 4 ? parts[1] : '',
        ipId: parts[parts.length - 2] || WORKFLOW_DEFAULT,
        workflow: last,
      };
    }
    if (parts.length >= 2 && parts[1] === WORKFLOW_DEFAULT) {
      return { sessionId: parts[0], ipId: WORKFLOW_DEFAULT, workflow: WORKFLOW_DEFAULT };
    }
    if (parts.length === 2 && TOP_WORKFLOWS.has(last)) {
      return { sessionId: 'default', ipId: parts[0], workflow: last };
    }
    return { sessionId: parts[0] || 'default', ipId: '', workflow: '' };
  }, [TOP_WORKFLOWS, isWorkflowSegment, normalizeSession]);
  // Bumped to Date.now() whenever the user explicitly picks an IP /
  // workflow / session. While the timestamp is fresh, the periodic
  // /healthz sync defers to the UI selection — otherwise a stale
  // CONTEXT tick fired between the optimistic local update and the
  // /api/session/activate POST landing on the backend would snap the
  // dropdowns back to the previous (often "default") triple.
  const userPickAtRef = useRef(0);

  const initialUrlNamespaceRef = useRef((() => {
    try {
      const url = new URL(window.location.href);
      const rawSession = normalizeSession(url.searchParams.get('session') || '');
      // splitSessionNamespace('') returns sentinel defaults, so only trust
      // its ipId/workflow when an actual ?session= was provided. Otherwise
      // the literal ?ip= / ?workflow= query params are authoritative for
      // deep links like /?ip=cmux_p0_test.
      const parsed = rawSession ? splitSessionNamespace(rawSession) : { sessionId: '', ipId: '', workflow: '' };
      const rawParts = rawSession.split('/').filter(Boolean);
      const parsedOwner = parsed.sessionId === 'default' && rawParts.length < 3 ? '' : parsed.sessionId;
      const owner = normalizeSession(
        parsedOwner || url.searchParams.get('session_id') || window.ATLAS_USER_SESSION_ID || ''
      ) || 'default';
      const workspaceSession = normalizeSession(
        parsed.workspaceSession
        || url.searchParams.get('workspace_session')
        || url.searchParams.get('workspace')
        || (window as any).ATLAS_WORKSPACE_SESSION_ID
        || ''
      ) || 'default';
      const ipParam = normalizeSession(url.searchParams.get('ip') || url.searchParams.get('ip_id') || '');
      const wfParam = normalizeSession(url.searchParams.get('workflow') || url.searchParams.get('wf') || '');
      const ip = ipParam || normalizeSession(parsed.ipId || '');
      const wf = wfParam || normalizeSession(parsed.workflow || '');
      if (!rawSession && !ip && !wf) return '';
      return `${owner}/${workspaceSession}/${ip || WORKFLOW_DEFAULT}/${wf || WORKFLOW_DEFAULT}`;
    } catch (_) {
      return '';
    }
  })());

  const holdInitialDashboardActivation = atlasShouldHoldDashboardActivation();
  const initialStoredNamespace = (() => {
    if (holdInitialDashboardActivation) return '';
    try { return normalizeSession(localStorage.getItem('atlasActiveSession') || ''); }
    catch (_) { return ''; }
  })();
  const initialBootstrapNamespace = normalizeSession(initialUrlNamespaceRef.current || '')
    || (holdInitialDashboardActivation ? '' : normalizeSession(window.ACTIVE_SESSION || initialStoredNamespace || ''));
  const initialSplit = splitSessionNamespace(initialBootstrapNamespace);
  const [activeSessionId, setActiveSessionId] = useState(
    normalizeSession(window.ATLAS_USER_SESSION_ID || initialSplit.sessionId) || 'default'
  );
  const [activeNamespace, setActiveNamespace] = useState(
    initialBootstrapNamespace || (holdInitialDashboardActivation ? '' : `${activeSessionId}/default/default/default`)
  );
  const [activeIp, setActiveIp] = useState(initialSplit.ipId || WORKFLOW_DEFAULT);
  useEffect(() => {
    window.ACTIVE_IP = activeIp || WORKFLOW_DEFAULT;
  }, [activeIp]);
  const [activeDbSession, setActiveDbSession] = useState(() => ({
    dbSessionId: String(window.ATLAS_DB_SESSION_ID || '').trim(),
    sessionUid: String(window.ATLAS_SESSION_UID || '').trim(),
    sessionLabel: String(window.ATLAS_SESSION_LABEL || '').trim(),
    namespace: initialBootstrapNamespace || '',
  }));
  const splitActiveNamespace = useCallback(() => {
    const namespace = normalizeSession(window.ACTIVE_SESSION || activeNamespace || '');
    return namespace
      ? splitSessionNamespace(namespace)
      : { sessionId: '', ipId: '', workflow: '' };
  }, [activeNamespace, normalizeSession, splitSessionNamespace]);
  const [sessionIdOptions, setSessionIdOptions] = useState<string[]>([]);
  const [ipOptions, setIpOptions] = useState<string[]>([]);
  // Inline notice for + IP / + SESSION errors. window.alert/prompt
  // wedges the cmux WKWebView (native dialogs hang every browser RPC),
  // so route validation feedback through a transient banner instead.
  const [topNotice, setTopNotice] = useState('');
  const [nameEntry, setNameEntry] = useState<{ kind: string; value: string } | null>(null);
  const [nameEntryBusy, setNameEntryBusy] = useState(false);
  const nameEntryInputRef = useRef<HTMLInputElement | null>(null);
  const showNotice = useCallback((msg: unknown) => {
    setTopNotice(String(msg || ''));
    setTimeout(() => setTopNotice(''), 5000);
  }, []);
  useEffect(() => {
    const urlNamespace = normalizeSession(initialUrlNamespaceRef.current || '');
    if (!urlNamespace) return;
    window.ACTIVE_SESSION = urlNamespace;
    try { localStorage.setItem('atlasActiveSession', urlNamespace); } catch (_) {}
  }, [normalizeSession]);
  const makePromptMsgId = useCallback(() => {
    try {
      if (window.crypto && typeof window.crypto.randomUUID === 'function') {
        return window.crypto.randomUUID();
      }
    } catch (_) {}
    try {
      const b = new Uint8Array(16);
      window.crypto.getRandomValues(b);
      b[6] = (b[6] & 0x0f) | 0x40;
      b[8] = (b[8] & 0x3f) | 0x80;
      const h = Array.from(b, x => x.toString(16).padStart(2, '0'));
      return `${h.slice(0, 4).join('')}-${h.slice(4, 6).join('')}-${h.slice(6, 8).join('')}-${h.slice(8, 10).join('')}-${h.slice(10, 16).join('')}`;
    } catch (_) {
      return `atlas-${Date.now()}-${Math.random().toString(16).slice(2)}`;
    }
  }, []);
  useEffect(() => {
    if (!nameEntry) return undefined;
    const timer = setTimeout(() => {
      try { nameEntryInputRef.current && nameEntryInputRef.current.focus(); } catch (_) {}
    }, 0);
    return () => clearTimeout(timer);
  }, [nameEntry && nameEntry.kind]);
  const saveRunPolicy = useCallback(async (nextRunMode: string, nextExecMode: string) => {
    const run_mode = normalizeAtlasRunMode(nextRunMode);
    const exec_mode = normalizeAtlasExecMode(nextExecMode);
    setRunMode(run_mode);
    setExecMode(exec_mode);
    try {
      const r = await fetch('/api/pipeline/run_policy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ run_mode, exec_mode }),
      });
      const j = await r.json().catch(() => ({}));
      if (r.ok) {
        mergeAtlasPolicyResponse(j);
        if (j.run_mode) setRunMode(normalizeAtlasRunMode(j.run_mode));
        if (j.exec_mode) setExecMode(normalizeAtlasExecMode(j.exec_mode));
        try { window.dispatchEvent(new CustomEvent('atlas:pipeline-poll')); } catch (_) {}
      } else if (j.error) {
        showNotice(j.error);
      }
    } catch (e: any) {
      showNotice(`Run policy update failed: ${e && e.message ? e.message : e}`);
    }
  }, [showNotice]);

  // Agent-running indicator + workspace-switch in-flight toast. Extracted to
  // app-agent-hook.tsx (self-contained: subscribes only to window.backend).
  // The window.ATLAS_AGENT_RUNNING bridge lives inside that hook now.
  const {
    agentRunning, agentRunningRef, setAgentRunningState, wfSwitching, setWfSwitching,
  } = useAtlasAgentRunning();

  // First-connect handshake indicator. Runs a small protocol on mount:
  //   1) WS connects               → 'ws'
  //   2) Backend hello received    → 'hello'
  //   3) /healthz responds 200     → 'health'
  //   4) /api/session/list resolves → 'sessions'
  //   5) all of the above complete → 'ready' → banner fades after 1.2 s
  // While any step is outstanding the banner shows a spinner with the
  // current step label. Lets the user see the boot is actually doing
  // something instead of staring at a blank chrome.
  // Auth gate — mounts LoginScreen until /api/users/me returns 200.
  const [authState, setAuthState] = useState('checking');
  const authRequiredProbeRef = useRef(0);

  // First-connect handshake state machine — extracted to app-boot-hook.tsx.
  // Self-contained (depends only on authState + window.backend); App's auth
  // effect below still flips bootSteps.ws via the returned setBootSteps.
  const {
    bootSteps, setBootSteps, bootHidden, setBootHidden,
    bootDisplayDone, bootFailed,
  } = useAtlasBoot(authState);

  // Auth gate (auth_required listener + /api/users/me probe + run_policy
  // hydration) — extracted to app-auth-hook.tsx. The window.ATLAS_USER /
  // ATLAS_USER_SESSION_ID / ACTIVE_SESSION bridges live inside that hook now.
  useAtlasAuthGate({
    WORKFLOW_DEFAULT, authState, execMode, authRequiredProbeRef,
    normalizeSession, splitSessionNamespace,
    setBootSteps, setAuthState, setActiveSessionId, setActiveNamespace,
    setActiveIp, setRunMode, setExecMode,
  });

  const workflowForExecMode = useCallback((workflow: unknown) => {
    const wf = normalizeSession(workflow || WORKFLOW_DEFAULT) || WORKFLOW_DEFAULT;
    if (execMode !== 'orchestrator' && wf === 'orchestrator') return WORKFLOW_DEFAULT;
    if (execMode === 'orchestrator' && wf === WORKFLOW_DEFAULT) return 'orchestrator';
    return wf;
  }, [execMode, normalizeSession]);

  const currentWorkflow = useCallback(() => {
    const wf = splitActiveNamespace().workflow
      || normalizeSession(window.CONTEXT && window.CONTEXT.workspace)
      || '';
    return workflowForExecMode(wf || WORKFLOW_DEFAULT);
  }, [normalizeSession, splitActiveNamespace, workflowForExecMode]);

  const namespaceFor = useCallback((sessionId: unknown, ipId: unknown, workflow: unknown) => {
    const rawSession = normalizeSession(sessionId);
    const rawParts = rawSession.split('/').filter(Boolean);
    const owner = loggedInOwner()
      || rawParts[0]
      || normalizeSession(window.ATLAS_USER_SESSION_ID || '')
      || 'default';
    const activeParts = normalizeSession(window.ACTIVE_SESSION || '').split('/').filter(Boolean);
    const workspaceSession = (
      (rawParts.length >= 2 && rawParts[0] === owner ? rawParts[1] : '')
      || (activeParts.length >= 4 && activeParts[0] === owner ? activeParts[1] : '')
      || normalizeSession((window as any).ATLAS_WORKSPACE_SESSION_ID || '')
      || 'default'
    );
    const ip = normalizeSession(ipId || WORKFLOW_DEFAULT) || WORKFLOW_DEFAULT;
    const wf = normalizeSession(workflow || WORKFLOW_DEFAULT) || WORKFLOW_DEFAULT;
    return `${owner}/${workspaceSession}/${ip}/${wf}`;
  }, [loggedInOwner, normalizeSession]);

  const activateBackendWorkflow = useCallback((workflow: unknown, session?: unknown) => {
    // Empty input is the only true skip — `default` and `user` are
    // legitimate workspace names (`workflow/default/` exists), so
    // we DO fire /wf for them now. Without this, picking `default`
    // from the workflow dropdown left the agent pinned to whatever
    // workflow was active before — config.TODO_FILE / system prompt /
    // todo template all kept the old workspace's wiring.
    const wf = normalizeSession(workflow) || 'default';
    if (window.backend && typeof window.backend.send === 'function') {
      const parts = splitSessionNamespace(session || window.ACTIVE_SESSION || '');
      window.backend.send({
        type: 'prompt',
        text: `/wf ${wf}`,
        session: session || window.ACTIVE_SESSION || 'default',
        ip: parts.ipId || activeIp || WORKFLOW_DEFAULT,
        workflow: wf,
        ui_lang: window.ATLAS_UI_LANG || uiLang,
      });
    }
  }, [activeIp, normalizeSession, splitSessionNamespace, uiLang]);

  const stopForWorkflowSwitch = useCallback(() => {
    setAgentRunningState(false);
    try {
      if (window.backend && typeof window.backend.send === 'function') {
        window.backend.send({ type: 'stop' });
      }
    } catch (_) {}
    try {
      fetch('/api/control/stop', {
        method: 'POST',
        cache: 'no-store',
        keepalive: true,
      }).catch(() => {});
    } catch (_) {}
  }, [setAgentRunningState]);

  const confirmStopForWorkflowSwitch = useCallback((workflow: unknown) => {
    const running = agentRunningRef.current || agentRunning || window.ATLAS_AGENT_RUNNING === true;
    if (!running) return true;
    const wf = normalizeSession(workflow) || WORKFLOW_DEFAULT;
    const ok = window.confirm(`Agent is running. Stop it and switch workflow to "${wf}"?`);
    if (!ok) return false;
    stopForWorkflowSwitch();
    return true;
  }, [agentRunning, normalizeSession, stopForWorkflowSwitch]);

  const syncNamespaceUrl = useCallback((namespace: unknown, owner: unknown, ip: unknown, workflow: unknown) => {
    try {
      const url = new URL(window.location.href);
      const sid = normalizeSession(namespace || '');
      if (sid && sid !== 'default') url.searchParams.set('session', sid);
      else url.searchParams.delete('session');
      if (owner && owner !== 'default') url.searchParams.set('session_id', owner as string);
      else url.searchParams.delete('session_id');
      if (ip) url.searchParams.set('ip', ip as string);
      else url.searchParams.delete('ip');
      if (workflow) url.searchParams.set('workflow', workflow as string);
      else url.searchParams.delete('workflow');
      window.history.replaceState(null, '', url);
    } catch (_) {}
  }, [normalizeSession]);

  const applySessionMeta = useCallback((payload: any, fallbackNamespace?: unknown) => {
    const data = payload && typeof payload === 'object' ? payload : {};
    const nested = data.session && typeof data.session === 'object' ? data.session : {};
    const namespace = normalizeSession(data.namespace || nested.namespace || fallbackNamespace || '');
    const dbSessionId = String(data.db_session_id || nested.db_session_id || nested.id || namespace || '').trim();
    const sessionUid = String(data.session_uid || data.runtime_session_id || nested.session_uid || '').trim();
    const sessionLabel = String(
      data.session_label
      || nested.session_label
      || (sessionUid ? `S-${sessionUid.slice(0, 8)}` : '')
    ).trim();
    const next = { dbSessionId, sessionUid, sessionLabel, namespace };
    window.ATLAS_DB_SESSION_ID = dbSessionId;
    window.ATLAS_SESSION_UID = sessionUid;
    window.ATLAS_SESSION_LABEL = sessionLabel;
    setActiveDbSession(next);
    return next;
  }, [normalizeSession]);

  const activateNamespace = useCallback((sessionId: unknown, ipId: unknown, workflow: unknown, syncWorkflow = true, opts: any = {}) => {
    userPickAtRef.current = Date.now();
    const rawSession = normalizeSession(sessionId);
    const rawParts = rawSession.split('/').filter(Boolean);
    const owner = loggedInOwner() || rawParts[0] || 'default';
    const activeParts = normalizeSession(window.ACTIVE_SESSION || '').split('/').filter(Boolean);
    const workspaceSession = (
      (rawParts.length >= 2 && rawParts[0] === owner ? rawParts[1] : '')
      || (activeParts.length >= 4 && activeParts[0] === owner ? activeParts[1] : '')
      || normalizeSession((window as any).ATLAS_WORKSPACE_SESSION_ID || '')
      || 'default'
    );
    const ip = normalizeSession(ipId || WORKFLOW_DEFAULT) || WORKFLOW_DEFAULT;
    const wf = workflowForExecMode(workflow || WORKFLOW_DEFAULT);
    const preserveRunning = !!(opts && opts.preserveRunning);
    const namespace = namespaceFor(`${owner}/${workspaceSession}`, ip, wf);
    const prev = window.ACTIVE_SESSION || '';
    const prevParts = splitSessionNamespace(prev || '');
    const prevWf = prevParts.workflow || WORKFLOW_DEFAULT;
    const workflowChanged = !!(prev && prev !== namespace && prevWf !== wf);
    if (workflowChanged) {
      setWfSwitching({ from: prevWf, to: wf, ip, preserveRunning });
    }
    // Stop only when the UI knows an agent is actually running. Stopped
    // workflow changes should load directly without manufacturing a stale
    // "end of loop" state.
    if (prev && prev !== namespace && agentRunningRef.current && !preserveRunning) {
      try {
        setAgentRunningState(false);
        fetch('/api/control/stop', { method: 'POST' }).catch(() => {});
      } catch (_) {}
    }
    syncNamespaceUrl(namespace, owner, ip, wf);
    setActiveSessionId(owner);
    window.ACTIVE_IP = ip;
    setActiveIp(ip);
    setActiveNamespace(namespace);
    window.ACTIVE_SESSION = namespace;
    try { localStorage.setItem('atlasActiveSession', namespace); } catch (_) {}
    try {
      window.dispatchEvent(new CustomEvent('atlas-session-switched', {
        detail: { sessionId: owner, namespace, ip, workflow: wf },
      }));
    } catch (_) {}
    if (prev !== namespace && window.backend) {
      if (typeof window.backend.switchSession === 'function') {
        window.backend.switchSession(namespace);
      } else if (typeof window.backend.connect === 'function') {
        window.backend.connect(namespace);
      }
    }
    if (window.atlasData && typeof window.atlasData.setUserSessionId === 'function') {
      window.atlasData.setUserSessionId(owner);
    } else {
      window.ATLAS_USER_SESSION_ID = owner;
      try { localStorage.setItem('atlasUserSessionId', owner); } catch (_) {}
    }
    (window as any).ATLAS_WORKSPACE_SESSION_ID = workspaceSession;
    try { localStorage.setItem('atlasWorkspaceSessionId', workspaceSession); } catch (_) {}
    if (window.atlasData && typeof window.atlasData.setScopePath === 'function') {
      window.atlasData.setScopePath(ip);
    }
    if (window.atlasData && typeof window.atlasData.setActiveSession === 'function') {
      window.atlasData.setActiveSession(namespace);
    }
    // Push the canonical triple to the backend so its env vars
    // (ATLAS_ACTIVE_SESSION / ATLAS_ACTIVE_IP / ATLAS_DEFAULT_*) match
    // what the frontend is showing. /api/session/activate also loads the
    // workflow synchronously now; the older `/wf` WebSocket dispatch is a
    // fallback only because stale queued slash prompts can land late during
    // fast dropdown sweeps and split active_workflow from ACTIVE_WORKSPACE.
    const _activateAndDispatch = async () => {
      let activated = false;
      try {
        const res = await fetch('/api/session/activate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            owner: owner || 'default',
            workspace_session: workspaceSession || 'default',
            ip: ip || 'default',
            workflow: wf || 'default',
            preserve_running: preserveRunning,
          }),
        });
        activated = !!(res && res.ok);
        if (activated) {
          let payload: any = {};
          try { payload = await res.json(); } catch (_) { payload = {}; }
          applySessionMeta(payload, namespace);
        }
      } catch (_) {}
      if (syncWorkflow && !activated) activateBackendWorkflow(wf, namespace);
      if (workflowChanged) {
        if (!preserveRunning) setAgentRunningState(false);
        setWfSwitching((cur: any) => (
          cur && cur.to === wf && cur.ip === ip ? null : cur
        ));
      }
    };
    _activateAndDispatch();
    return namespace;
  }, [activateBackendWorkflow, applySessionMeta, loggedInOwner, namespaceFor, normalizeSession, setAgentRunningState, splitSessionNamespace, syncNamespaceUrl, workflowForExecMode]);

  useEffect(() => {
    window.activateAtlasNamespace = activateNamespace;
    return () => {
      if (window.activateAtlasNamespace === activateNamespace) {
        delete window.activateAtlasNamespace;
      }
    };
  }, [activateNamespace]);

  useEffect(() => {
    if (authState !== 'authed' || execMode !== 'orchestrator') return;
    const parsed = splitActiveNamespace();
    const parsedWf = normalizeSession(parsed.workflow || '');
    if (parsedWf && parsedWf !== WORKFLOW_DEFAULT) return;
    const owner = loggedInOwner() || parsed.sessionId || activeSessionId || 'default';
    const ip = (parsed.ipId === 'soc' ? WORKFLOW_DEFAULT : parsed.ipId) || activeIp || WORKFLOW_DEFAULT;
    activateNamespace(owner, ip, 'orchestrator', true, { preserveRunning: true });
  }, [authState, execMode, activeNamespace, activeIp, activeSessionId, activateNamespace, loggedInOwner, normalizeSession, splitActiveNamespace]);

  useEffect(() => {
    if (authState !== 'authed' || execMode === 'orchestrator') return;
    const parsed = splitActiveNamespace();
    const parsedWf = normalizeSession(parsed.workflow || '');
    if (parsedWf !== 'orchestrator') return;
    const owner = loggedInOwner() || parsed.sessionId || activeSessionId || 'default';
    const ip = (parsed.ipId === 'soc' ? WORKFLOW_DEFAULT : parsed.ipId) || activeIp || WORKFLOW_DEFAULT;
    activateNamespace(owner, ip, WORKFLOW_DEFAULT, true);
  }, [authState, execMode, activeNamespace, activeIp, activeSessionId, activateNamespace, loggedInOwner, normalizeSession, splitActiveNamespace]);

  // Synthetic / reserved namespace segments that should never show
  // up in the ip_id dropdown. 'soc' is the SoC architect placeholder,
  // 'user' is the legacy ip-less sentinel (still in the wild on disk
  // from older runs), and any workflow name (ssot-gen, rtl-gen, …)
  // that slipped into the IP slot from `${owner}/${wf}` namespaces
  // gets filtered too. 'default' stays selectable as the explicit
  // default IP_ID.
  // Session-roster + namespace-sync cluster (refreshTopTargets, the
  // /healthz-tick syncCurrent listener, the URL/localStorage handshake, and
  // the atlas-session-switched listener) — extracted to app-session-hook.tsx.
  // The window.IP_OPTIONS / ACTIVE_SESSION / ACTIVE_IP bridges live there now.
  const { refreshTopTargets } = useAtlasSessionSync({
    WORKFLOW_DEFAULT, TOP_WORKFLOWS, authState, activeIp, activeNamespace, activeSessionId,
    initialUrlNamespaceRef, userPickAtRef,
    loggedInOwner, normalizeSession, splitSessionNamespace, namespaceFor,
    currentWorkflow, workflowForExecMode, applySessionMeta, syncNamespaceUrl, activateNamespace,
    setSessionIdOptions, setIpOptions, setActiveSessionId, setActiveNamespace, setActiveIp,
  });

  // Screen routing + screen-driven side effects (open_evidence / workflow
  // workspace listeners, opt-in workflow auto-switch, data-* attribute sync,
  // page-load stop guard, activateDashboardSession) — extracted to
  // app-screen-hook.tsx. setScreen is returned so createIp() can flip to
  // Workspace after scaffolding a new IP.
  const { screen, setScreen, activateDashboardSession } = useAtlasScreen({
    dir, theme, fontMode, fontScale, uiLang, execMode, WORKFLOW_DEFAULT,
    activeIp, activeNamespace, activeSessionId, activateNamespace,
    confirmStopForWorkflowSwitch, currentWorkflow, loggedInOwner,
    normalizeSession, splitSessionNamespace,
  });

  const selectSessionId = (rawSessionId: string) => {
    const authOwner = loggedInOwner();
    const workspaceSession = normalizeSession(rawSessionId) || 'default';
    if (!authOwner) {
      showNotice('Login is required before switching sessions.');
      return;
    }
    const owner = `${authOwner}/${workspaceSession}`;
    (window as any).ATLAS_WORKSPACE_SESSION_ID = workspaceSession;
    try { localStorage.setItem('atlasWorkspaceSessionId', workspaceSession); } catch (_) {}
    const parsed = splitActiveNamespace();
    const ip = (parsed.ipId === 'soc' ? WORKFLOW_DEFAULT : parsed.ipId) || activeIp || WORKFLOW_DEFAULT;
    const wf = parsed.workflow || currentWorkflow() || WORKFLOW_DEFAULT;
    activateNamespace(owner, ip, wf, true);
  };

  const selectIp = (rawIp: string) => {
    const ip = normalizeSession(rawIp) || WORKFLOW_DEFAULT;
    // Workflow / ip / session changes are user-driven only — picking
    // an IP keeps whatever workflow segment was already active. Use
    // the workflow dropdown explicitly to change it.
    const parsed = splitActiveNamespace();
    const cur = workflowForExecMode(parsed.workflow || currentWorkflow());
    const wf = isWorkflowSegment(cur) ? cur : WORKFLOW_DEFAULT;
    const ownerBase = loggedInOwner() || parsed.sessionId || activeSessionId || 'default';
    const owner = parsed.workspaceSession ? `${ownerBase}/${parsed.workspaceSession}` : ownerBase;
    activateNamespace(owner, ip, wf, true);
  };

  // Let the chat command plane (`/ip <name>` / `/use <name>` in workspace.jsx)
  // drive the same frontend IP switch the dropdown uses, so changing IP from
  // chat moves the feed / IP indicator / file tree, not just the backend.
  const selectIpRef = useRef(selectIp);
  selectIpRef.current = selectIp;
  useEffect(() => {
    const onSelectIp = (e: any) => {
      const ip = e && e.detail && e.detail.ip;
      if (ip) { try { selectIpRef.current(ip); } catch (_) {} }
    };
    window.addEventListener('atlas:select-ip', onSelectIp);
    return () => window.removeEventListener('atlas:select-ip', onSelectIp);
  }, []);

  // Switch workflow segment of the active namespace. default is an
  // explicit workflow segment; /api/session/activate loads the matching
  // backend prompt, TODO file and workspace config.
  const selectWorkflow = (rawWf: string) => {
    let wf = normalizeSession(rawWf) || WORKFLOW_DEFAULT;
    if (execMode === 'orchestrator' && wf === WORKFLOW_DEFAULT) wf = 'orchestrator';
    const parsed = splitActiveNamespace();
    const parsedWf = parsed.workflow || WORKFLOW_DEFAULT;
    if (wf === (currentWorkflow() || WORKFLOW_DEFAULT) && !(wf === 'orchestrator' && parsedWf !== 'orchestrator')) return;
    const preserveRunning = execMode === 'orchestrator';
    if (preserveRunning && wf !== 'orchestrator') {
      try {
        window.dispatchEvent(new CustomEvent('atlas-workflow-view-request', {
          detail: { workflow: wf },
        }));
      } catch (_) {}
      showNotice(`Viewing ${wf}; orchestrator remains active.`);
      return;
    }
    const ok = preserveRunning || confirmStopForWorkflowSwitch(wf);
    if (!ok) return;
    const ownerBase = loggedInOwner() || parsed.sessionId || activeSessionId || 'default';
    const owner = parsed.workspaceSession ? `${ownerBase}/${parsed.workspaceSession}` : ownerBase;
    const ip = (parsed.ipId === 'soc' ? WORKFLOW_DEFAULT : parsed.ipId) || activeIp || WORKFLOW_DEFAULT;
    if (screen === 'workspace') {
      try {
        window.dispatchEvent(new CustomEvent('atlas-workflow-view-request', {
          detail: { workflow: wf, owner, ip, preserveRunning },
        }));
      } catch (_) {}
      return;
    }
    activateNamespace(owner, ip, wf, true, { preserveRunning });
  };

  const beginNameEntry = (kind: string) => {
    setTopNotice('');
    setNameEntryBusy(false);
    setNameEntry({ kind, value: '' });
  };

  const commitNewSessionId = (raw: string) => {
    if (!raw) return;
    const workspaceSession = normalizeSession(raw);
    if (!workspaceSession) {
      showNotice('Invalid session. Use only [A-Za-z0-9_.-].');
      return false;
    }
    const authOwner = loggedInOwner();
    if (!authOwner) {
      showNotice('Login is required before creating a session.');
      return false;
    }
    (window as any).ATLAS_WORKSPACE_SESSION_ID = workspaceSession;
    try { localStorage.setItem('atlasWorkspaceSessionId', workspaceSession); } catch (_) {}
    setSessionIdOptions(prev => Array.from(new Set([workspaceSession].concat(prev || []))));
    const parsed = splitActiveNamespace();
    const ip = (parsed.ipId === 'soc' ? WORKFLOW_DEFAULT : parsed.ipId) || activeIp || WORKFLOW_DEFAULT;
    const wf = parsed.workflow || currentWorkflow() || WORKFLOW_DEFAULT;
    activateNamespace(`${authOwner}/${workspaceSession}`, ip, wf, true);
    return true;
  };

  const newSessionId = () => beginNameEntry('session');

  // Create a brand-new IP under the current user_session and switch
  // to it. IP creation must first scaffold <PROJECT_ROOT>/<ip>/...;
  // otherwise the UI can show a session namespace that the file tree
  // cannot read.
  const createIp = async (raw: string) => {
    if (!raw) return;
    const ip = normalizeSession(raw);
    if (!ip) {
      showNotice('Invalid IP name. Use only [A-Za-z0-9_.-].');
      return false;
    }
    const authedOwner = normalizeSession(
      (window.ATLAS_USER && window.ATLAS_USER.username)
      || window.ATLAS_USER_SESSION_ID
      || ''
    );
    const me = authedOwner
      || activeSessionId
      || 'default';
    const requestedWorkflow = newIpInitialWorkflow();
    const requestedExecMode = normalizeAtlasExecMode(execMode);
    let createPayload: any = {};
    try {
      const createResponse = await fetch('/api/ip/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: ip,
          kind: 'TBD',
          exec_mode: requestedExecMode,
          workflow: requestedWorkflow,
        }),
      });
      try { createPayload = await createResponse.json(); } catch (_) { createPayload = {}; }
      if (!createResponse.ok) {
        let message = createResponse.statusText || `HTTP ${createResponse.status}`;
        message = createPayload.error || createPayload.detail || message;
        showNotice(`Failed to create IP "${ip}": ${message}`);
        return false;
      }
      mergeAtlasPolicyResponse(createPayload);
    } catch (e: any) {
      showNotice(`Failed to create IP "${ip}": ${String(e && e.message || e)}`);
      return false;
    }
    const createdNamespace = normalizeSession(createPayload.session || '');
    const createdParts = splitSessionNamespace(createdNamespace);
    const payloadWorkflow = normalizeSession(createPayload.workflow || createdParts.workflow || requestedWorkflow) || requestedWorkflow;
    const workflow = requestedExecMode === 'orchestrator' ? 'orchestrator' : payloadWorkflow;
    // Local state first so the dropdown and scope reflect the new IP
    // immediately after the scaffold exists.
    setIpOptions(prev => Array.from(new Set([ip].concat(prev || []))));
    try { setScreen('workspace'); localStorage.atlasScreen = 'workspace'; } catch (_) {}
    activateNamespace(me, ip, workflow, true, { preserveRunning: preserveRunningForCurrentMode() });
    setTimeout(() => {
      try { window.atlasData && window.atlasData.refreshFileTree && window.atlasData.refreshFileTree(ip, { recursive: true }); } catch (_) {}
      try { refreshTopTargets(); } catch (_) {}
    }, 1500);
    return true;
  };

  const commitNameEntry = async () => {
    if (!nameEntry || nameEntryBusy) return;
    const raw = String(nameEntry.value || '').trim();
    if (!raw) {
      setNameEntry(null);
      return;
    }
    let ok: any = false;
    if (nameEntry.kind === 'session') {
      ok = commitNewSessionId(raw);
    } else {
      setNameEntryBusy(true);
      try {
        ok = await createIp(raw);
      } finally {
        setNameEntryBusy(false);
      }
    }
    if (ok) setNameEntry(null);
  };

  // Top-level screen — 'workspace' is the default landing surface because
  // Chat is the primary Atlas interaction. The dashboard remains available
  // as an explicit screen.
  //
  // 'dashboard' (user landing), 'workspace' (live
  // agent + chat + sidebar), or 'pipeline' (stage dispatcher).
  // Old 'architect' value (mock-data SoC view) migrates to 'pipeline'
  // on first load so existing sessions don't get stranded on a screen
  // that no longer exists.
  const sendControl = useCallback((type: string) => {
    if (!type) return;
    try { if (window.backend) window.backend.send({ type }); } catch (_) {}
    try {
      if (type === 'stop' && window.backend && window.backend._emit) {
        window.backend._emit('agent_state', { running: false });
      }
      if (type === 'shutdown' && window.backend && window.backend._emit) {
        window.backend._emit('connection', { state: 'closed' });
      }
    } catch (_) {}
    try {
      fetch(`/api/control/${type}`, {
        method: 'POST',
        cache: 'no-store',
        keepalive: true,
      }).catch(() => {});
    } catch (_) {}
  }, []);

  // Bump on every atlas-data-changed so the TitleBar (which reads
  // window.CONTEXT.cwd / .workspace) re-renders when /healthz lands
  // or the user runs /wf.
  const [, bump] = useReducer((x: number) => x + 1, 0);
  useEffect(() => {
    const h = () => bump();
    window.addEventListener('atlas-data-changed', h);
    return () => window.removeEventListener('atlas-data-changed', h);
  }, []);

  // Global Esc → tell the agent to abort the current iteration. We
  // skip the binding when an open ask_user card has focus, since Esc
  // there should cancel the card (handled inside that component).
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      // Ctrl+Q (or Cmd+Q) → ask to terminate the current session worker.
      if ((e.ctrlKey || e.metaKey) && (e.key === 'q' || e.key === 'Q')) {
        e.preventDefault();
        if (!confirm('Terminate this session worker? Atlas UI will stay open.')) return;
        sendControl('shutdown');
        return;
      }
      // Esc → tell the agent to abort the current iteration.
      if (e.key === 'Escape') {
        const active = document.activeElement as HTMLElement | null;
        const ownsEsc = !!document.querySelector('.slash-menu')
          || !!(active && active.closest && active.closest('.ask-prompt, [data-esc-local="true"]'));
        if (ownsEsc) return;
        e.preventDefault();
        sendControl('stop');
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [sendControl]);

  const stopAgent = () => {
    sendControl('stop');
  };
  const exitAll = () => {
    sendControl('shutdown');
  };

  // Auth gate must short-circuit before any workspace state touches
  // window.ATLAS_USER / .session/<owner>/. A page reload after login
  // keeps the boot sequence deterministic.
  if (authState === 'checking') {
    return <div className="app" data-dir={dir} data-theme={theme} />;
  }
  if (authState === 'unauth') {
    const Lg = window.LoginScreen as any;
    return Lg
      ? <div className="app" data-dir={dir} data-theme={theme}>
          <Lg onAuth={() => window.location.reload()} />
        </div>
      : <div className="app" data-dir={dir} data-theme={theme} />;
  }

  const ownerEditable = !loggedInOwner();
  // NOTE: activeDbSessionLabel / activeDbSessionTitle were computed here but
  // never rendered — same as the app.jsx reference, which also computes them
  // and never uses them. Dropped to match the working reference exactly and
  // avoid dead code (and an unused-local in strict TS).

  return (
    <AppShell
      dir={dir}
      theme={theme}
      setTheme={setTheme}
      topNotice={topNotice}
      setTopNotice={setTopNotice}
      wfSwitching={wfSwitching}
      bootHidden={bootHidden}
      setBootHidden={setBootHidden}
      bootSteps={bootSteps}
      bootFailed={bootFailed}
      bootDisplayDone={bootDisplayDone}
      nameEntry={nameEntry}
      setNameEntry={setNameEntry}
      nameEntryBusy={nameEntryBusy}
      nameEntryInputRef={nameEntryInputRef}
      commitNameEntry={commitNameEntry}
      newIpInitialWorkflow={newIpInitialWorkflow}
      normalizeSession={normalizeSession}
      activeNamespace={activeNamespace}
      ownerEditable={ownerEditable}
      activeSessionId={activeSessionId}
      sessionIdOptions={sessionIdOptions}
      selectSessionId={selectSessionId}
      newSessionId={newSessionId}
      activeIp={activeIp}
      WORKFLOW_DEFAULT={WORKFLOW_DEFAULT}
      selectIp={selectIp}
      ipOptions={ipOptions}
      authState={authState}
      beginNameEntry={beginNameEntry}
      execMode={execMode}
      currentWorkflow={currentWorkflow}
      fontMode={fontMode}
      setFontMode={setFontMode}
      fontScale={fontScale}
      setFontScale={setFontScale}
      resolution={resolution}
      setResolution={setResolution}
      uiLang={uiLang}
      chooseUiLang={chooseUiLang}
      stopAgent={stopAgent}
      exitAll={exitAll}
      screen={screen}
      setScreen={setScreen}
      runMode={runMode}
      saveRunPolicy={saveRunPolicy}
      WORKFLOW_OPTIONS={WORKFLOW_OPTIONS}
      selectWorkflow={selectWorkflow}
      activateDashboardSession={activateDashboardSession}
    />
  );
};

(window.ReactDOM as any).createRoot(document.getElementById('root')).render(<App />);
