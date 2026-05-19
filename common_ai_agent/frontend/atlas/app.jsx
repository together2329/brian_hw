// app.jsx — top-level shell. Renders Workspace only. Owns dir + theme.
//
// Launcher and Pipeline screens were design-time mocks and have been
// removed; the live agent UI lives entirely inside Workspace.

// ── ErrorBoundary ─────────────────────────────────────────────────
// Without this, any throw inside Workspace / SocArchitect / a deep
// child component unmounts the *whole* app and shows a blank black
// page. The Atlas test agent caught one of these (a TDZ ReferenceError
// in soc-architect.jsx). Catching at the shell level keeps the user
// in business + surfaces the error inline so we get a screenshot we
// can act on instead of a silent blank.
class ErrorBoundary extends React.Component {
  constructor(p) { super(p); this.state = { error: null, info: null }; }
  static getDerivedStateFromError(error) { return { error }; }
  componentDidCatch(error, info) { this.setState({ info }); console.error('[atlas] component crashed:', error, info); }
  reset = () => this.setState({ error: null, info: null });
  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div style={{ padding: 24, fontFamily: 'var(--mono)', color: 'var(--fg)',
                    background: 'var(--bg)', height: '100%', overflow: 'auto' }}>
        <div style={{ color: 'var(--err)', fontSize: 14, fontWeight: 600, marginBottom: 8 }}>
          ✗ {this.props.label || 'Component'} crashed
        </div>
        <div style={{ color: 'var(--fg-mute)', fontSize: 'var(--ui-control-font-size)', marginBottom: 12, lineHeight: 1.6 }}>
          The shell stays alive — pick a different screen, or hit Reset to try mounting again.
        </div>
        <pre style={{ background: 'var(--bg-2)', border: '1px solid var(--line)',
                      padding: 12, fontSize: 'var(--ui-control-font-size)', color: 'var(--err)',
                      maxHeight: 200, overflow: 'auto', whiteSpace: 'pre-wrap' }}>
          {String(this.state.error && this.state.error.message || this.state.error)}
        </pre>
        {this.state.info && this.state.info.componentStack && (
          <pre style={{ background: 'var(--bg-2)', border: '1px solid var(--line)',
                        padding: 12, fontSize: 10.5, color: 'var(--fg-dim)',
                        maxHeight: 280, overflow: 'auto', whiteSpace: 'pre-wrap' }}>
            {this.state.info.componentStack}
          </pre>
        )}
        <button onClick={this.reset}
                style={{ marginTop: 12, padding: '6px 14px',
                         background: 'var(--accent)', color: 'var(--bg)',
                         border: 0, fontFamily: 'var(--mono)', fontSize: 12,
                         cursor: 'pointer' }}>
          Reset
        </button>
      </div>
    );
  }
}

const ATLAS_UI_RESOLUTION_PRESETS = [
  { key: '1366x768', label: '1366x768', width: 1366, height: 768 },
  { key: '1600x900', label: '1600x900', width: 1600, height: 900 },
  { key: '1920x1080', label: '1920x1080', width: 1920, height: 1080 },
  { key: '2560x1440', label: '2560x1440', width: 2560, height: 1440 },
  { key: '3840x2160', label: '3840x2160', width: 3840, height: 2160 },
];
const DEFAULT_ATLAS_RESOLUTION = '1920x1080';
const atlasResolutionPreset = (key) =>
  ATLAS_UI_RESOLUTION_PRESETS.find(p => p.key === key) ||
  ATLAS_UI_RESOLUTION_PRESETS.find(p => p.key === DEFAULT_ATLAS_RESOLUTION) ||
  ATLAS_UI_RESOLUTION_PRESETS[0];
const ATLAS_RUN_MODE_OPTIONS = [
  { key: 'starter', label: 'Starter' },
  { key: 'engineering', label: 'Engineering' },
  { key: 'signoff', label: 'Signoff' },
];
const ATLAS_EXEC_MODE_OPTIONS = [
  { key: 'single-worker', label: 'Single Worker' },
  { key: 'orchestrator', label: 'Orchestrator' },
];
const DEFAULT_ATLAS_EXEC_MODE = 'orchestrator';
const normalizeAtlasRunMode = (value) => {
  const v = String(value || '').trim().toLowerCase().replace(/_/g, '-');
  if (v === 'eng') return 'engineering';
  if (v === 'sign-off') return 'signoff';
  return ATLAS_RUN_MODE_OPTIONS.some(o => o.key === v) ? v : 'engineering';
};
const normalizeAtlasExecMode = (value) => {
  const v = String(value || '').trim().toLowerCase().replace(/_/g, '-');
  if (v === 'single' || v === 'worker' || v === 'serial') return 'single-worker';
  if (v === 'orch' || v === 'multi-worker') return 'orchestrator';
  return ATLAS_EXEC_MODE_OPTIONS.some(o => o.key === v) ? v : DEFAULT_ATLAS_EXEC_MODE;
};
const atlasBootConfig = () => {
  try { return window.ATLAS_BOOT_CONFIG || {}; }
  catch (_) { return {}; }
};

// ── PipelineRunningChip ───────────────────────────────────────────
// Top-bar "[▶ N running]" chip. Reads window.ATLAS_PIPELINE_RUNNING
// (set by AtlasPipeline's poll loop) and listens to the corresponding
// custom event so the chip stays accurate even when the user is on
// the Workspace screen. Visible only when count > 0.
const PipelineRunningChip = ({ onClick }) => {
  const [count, setCount] = React.useState(
    typeof window.ATLAS_PIPELINE_RUNNING === 'number' ? window.ATLAS_PIPELINE_RUNNING : 0
  );
  React.useEffect(() => {
    const onChange = (ev) => {
      setCount((ev && ev.detail && typeof ev.detail.count === 'number') ? ev.detail.count : 0);
    };
    window.addEventListener('atlas:pipeline-running-changed', onChange);
    return () => window.removeEventListener('atlas:pipeline-running-changed', onChange);
  }, []);
  if (!count) return null;
  return (
    <button className="dir-btn pipe-running-chip"
            title={`${count} pipeline stage(s) running — click to open Pipeline`}
            onClick={onClick}>
      ▶ {count} running
    </button>
  );
};

const OrchInlineStatus = ({ activeIp }) => {
  const [status, setStatus] = React.useState(null);

  React.useEffect(() => {
    let cancelled = false;
    const poll = async () => {
      if (!activeIp || activeIp === 'default') { setStatus(null); return; }
      try {
        const [runRes, traceRes] = await Promise.all([
          fetch(`/api/orchestrator/active_run?ip=${encodeURIComponent(activeIp)}`),
          fetch(`/api/orchestrator/trace?ip=${encodeURIComponent(activeIp)}&limit=1`),
        ]);
        if (cancelled) return;
        const runData = runRes.ok ? await runRes.json() : null;
        const traceData = traceRes.ok ? await traceRes.json() : null;
        if (cancelled) return;
        const lastEvent = traceData && Array.isArray(traceData.events) && traceData.events.length
          ? traceData.events[0] : null;
        setStatus({ run: runData, lastEvent });
      } catch (_) {
        if (!cancelled) setStatus(null);
      }
    };
    poll();
    const id = setInterval(poll, 1500);
    return () => { cancelled = true; clearInterval(id); };
  }, [activeIp]);

  const execMode = window.ATLAS_EXEC_MODE || window.ATLAS_DEFAULT_EXEC_MODE || 'single';
  const isOrch = execMode === 'orchestrator';
  const workerCount = status && status.run && typeof status.run.running_count === 'number'
    ? status.run.running_count : 0;
  const lastKind = status && status.lastEvent
    ? (status.lastEvent.kind || status.lastEvent.type || '') : '';

  return (
    <span className="orch-inline">
      <span className="osk">orch:</span>
      <span className={`osv ${isOrch ? 'on' : 'off'}`}>{isOrch ? 'on' : 'off'}</span>
      <span className="os-sep"> │ </span>
      <span className="osk">workers:</span>
      <span className="osv">{workerCount}</span>
      {lastKind ? (
        <>
          <span className="os-sep"> │ </span>
          <span className="osk">last:</span>
          <span className="osv">{lastKind}</span>
        </>
      ) : null}
    </span>
  );
};

const App = () => {
  const dir = 'B';     // Workbench is the only visible Atlas shell mode.
  const [theme, setTheme] = React.useState('dark');
  const [uiLang, setUiLang] = React.useState(() => {
    try {
      const saved = localStorage.getItem('atlasUiLang');
      const explicit = localStorage.getItem('atlasUiLangUserSet') === '1';
      return explicit && saved === 'ko' ? 'ko' : 'en';
    }
    catch (_) { return 'en'; }
  });
  const [fontMode, setFontMode] = React.useState(() => {
    try {
      const saved = localStorage.getItem('atlasFontMode');
      const userSet = localStorage.getItem('atlasFontModeUserSet') === '1';
      if (saved === 'mono' && !userSet) return 'sans';
      return ['mono', 'sans', 'system'].includes(saved) ? saved : 'sans';
    } catch (_) { return 'sans'; }
  });
  const [fontScale, setFontScale] = React.useState(() => {
    try {
      const saved = localStorage.getItem('atlasFontScale');
      return ['compact', 'normal', 'large', 'xl'].includes(saved) ? saved : 'large';
    } catch (_) { return 'large'; }
  });
  const [resolution, setResolution] = React.useState(() => {
    try {
      return atlasResolutionPreset(localStorage.getItem('atlasResolution')).key;
    } catch (_) { return DEFAULT_ATLAS_RESOLUTION; }
  });
  const [runMode, setRunMode] = React.useState(() => {
    try { return normalizeAtlasRunMode(atlasBootConfig().run_mode || localStorage.getItem('atlasRunMode')); }
    catch (_) { return 'engineering'; }
  });
  const [execMode, setExecMode] = React.useState(() => {
    try { return normalizeAtlasExecMode(atlasBootConfig().exec_mode || localStorage.getItem('atlasExecMode')); }
    catch (_) { return DEFAULT_ATLAS_EXEC_MODE; }
  });
  React.useEffect(() => {
    window.ATLAS_UI_LANG = uiLang;
    try { localStorage.setItem('atlasUiLang', uiLang); } catch (_) {}
    window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'UI_LANG' }));
  }, [uiLang]);
  React.useEffect(() => {
    try { localStorage.setItem('atlasFontMode', fontMode); } catch (_) {}
  }, [fontMode]);
  React.useEffect(() => {
    try { localStorage.setItem('atlasFontScale', fontScale); } catch (_) {}
  }, [fontScale]);
  React.useEffect(() => {
    const preset = atlasResolutionPreset(resolution);
    document.documentElement.setAttribute('data-resolution', preset.key);
    document.documentElement.style.setProperty('--atlas-canvas-w', `${preset.width}px`);
    document.documentElement.style.setProperty('--atlas-canvas-h', `${preset.height}px`);
    window.ATLAS_RESOLUTION = preset;
    try { localStorage.setItem('atlasResolution', preset.key); } catch (_) {}
    window.dispatchEvent(new CustomEvent('atlas-resolution-changed', { detail: preset }));
  }, [resolution]);
  React.useEffect(() => {
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
  const chooseUiLang = React.useCallback((next) => {
    setUiLang(next === 'ko' ? 'ko' : 'en');
    try { localStorage.setItem('atlasUiLangUserSet', '1'); } catch (_) {}
  }, []);
  const TOP_WORKFLOWS = React.useMemo(() => new Set([
    'architect', 'coverage', 'fl-model-gen', 'goal-audit', 'lint',
    'mas-gen', 'orchestrator', 'pnr', 'rtl-gen', 'signoff', 'sim', 'sim_debug',
    'ssot-gen', 'sta', 'sta-post', 'syn', 'tb-gen',
  ]), []);
  const WORKFLOW_DEFAULT = 'default';
  const WORKFLOW_OPTIONS = React.useMemo(
    () => [WORKFLOW_DEFAULT].concat(Array.from(TOP_WORKFLOWS).sort()),
    [TOP_WORKFLOWS]
  );
  const isWorkflowSegment = React.useCallback((value) => {
    const wf = String(value || '');
    return wf === WORKFLOW_DEFAULT || TOP_WORKFLOWS.has(wf);
  }, [TOP_WORKFLOWS]);

  const normalizeSession = React.useCallback((value) => {
    const norm = (window.atlasData && window.atlasData.normalizeSessionName) || window.normalizeAtlasSessionName;
    try { return (norm && norm(value || '')) || ''; }
    catch (_) { return ''; }
  }, []);

  const splitSessionNamespace = React.useCallback((session) => {
    const sid = normalizeSession(session);
    const parts = sid.split('/').filter(Boolean);
    if (!parts.length) return { sessionId: WORKFLOW_DEFAULT, ipId: WORKFLOW_DEFAULT, workflow: WORKFLOW_DEFAULT };
    const last = parts[parts.length - 1];
    if (parts.length >= 3 && isWorkflowSegment(last)) {
      return {
        sessionId: parts[0],
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

  const initialUrlNamespaceRef = React.useRef((() => {
    try {
      const url = new URL(window.location.href);
      const rawSession = normalizeSession(url.searchParams.get('session') || '');
      // splitSessionNamespace('') returns sentinel defaults, so only trust
      // its ipId/workflow when an actual ?session= was provided. Otherwise
      // the literal ?ip= / ?workflow= query params are authoritative for
      // deep links like /?ip=cmux_p0_test.
      const parsed = rawSession ? splitSessionNamespace(rawSession) : { sessionId: '', ipId: '', workflow: '' };
      const owner = normalizeSession(
        parsed.sessionId || url.searchParams.get('session_id') || window.ATLAS_USER_SESSION_ID || ''
      ) || 'default';
      const ipParam = normalizeSession(url.searchParams.get('ip') || url.searchParams.get('ip_id') || '');
      const wfParam = normalizeSession(url.searchParams.get('workflow') || url.searchParams.get('wf') || '');
      const ip = ipParam || normalizeSession(parsed.ipId || '');
      const wf = wfParam || normalizeSession(parsed.workflow || '');
      if (!rawSession && !ip && !wf) return '';
      return `${owner}/${ip || WORKFLOW_DEFAULT}/${wf || WORKFLOW_DEFAULT}`;
    } catch (_) {
      return '';
    }
  })());

  const initialStoredNamespace = (() => {
    try { return normalizeSession(localStorage.getItem('atlasActiveSession') || ''); }
    catch (_) { return ''; }
  })();
  const initialBootstrapNamespace = normalizeSession(initialUrlNamespaceRef.current || '')
    || normalizeSession(window.ACTIVE_SESSION || initialStoredNamespace || '');
  const initialSplit = splitSessionNamespace(initialBootstrapNamespace);
  const [activeSessionId, setActiveSessionId] = React.useState(
    normalizeSession(window.ATLAS_USER_SESSION_ID || initialSplit.sessionId) || 'default'
  );
  const [activeNamespace, setActiveNamespace] = React.useState(
    initialBootstrapNamespace || `${activeSessionId}/default/default`
  );
  const [activeIp, setActiveIp] = React.useState(initialSplit.ipId || WORKFLOW_DEFAULT);
  const [sessionIdOptions, setSessionIdOptions] = React.useState([]);
  const [ipOptions, setIpOptions] = React.useState([]);
  // Inline notice for + IP / + SESSION errors. window.alert/prompt
  // wedges the cmux WKWebView (native dialogs hang every browser RPC),
  // so route validation feedback through a transient banner instead.
  const [topNotice, setTopNotice] = React.useState('');
  const [nameEntry, setNameEntry] = React.useState(null);
  const nameEntryInputRef = React.useRef(null);
  const showNotice = React.useCallback((msg) => {
    setTopNotice(String(msg || ''));
    setTimeout(() => setTopNotice(''), 5000);
  }, []);
  React.useEffect(() => {
    const urlNamespace = normalizeSession(initialUrlNamespaceRef.current || '');
    if (!urlNamespace) return;
    window.ACTIVE_SESSION = urlNamespace;
    try { localStorage.setItem('atlasActiveSession', urlNamespace); } catch (_) {}
  }, [normalizeSession]);
  const makePromptMsgId = React.useCallback(() => {
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
  React.useEffect(() => {
    if (!nameEntry) return undefined;
    const timer = setTimeout(() => {
      try { nameEntryInputRef.current && nameEntryInputRef.current.focus(); } catch (_) {}
    }, 0);
    return () => clearTimeout(timer);
  }, [nameEntry && nameEntry.kind]);
  const saveRunPolicy = React.useCallback(async (nextRunMode, nextExecMode) => {
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
        if (j.run_mode) setRunMode(normalizeAtlasRunMode(j.run_mode));
        if (j.exec_mode) setExecMode(normalizeAtlasExecMode(j.exec_mode));
        try { window.dispatchEvent(new CustomEvent('atlas:pipeline-poll')); } catch (_) {}
      } else if (j.error) {
        showNotice(j.error);
      }
    } catch (e) {
      showNotice(`Run policy update failed: ${e && e.message ? e.message : e}`);
    }
  }, [showNotice]);

  const [agentRunning, _setAgentRunning] = React.useState(false);
  const agentRunningRef = React.useRef(false);
  const setAgentRunningState = React.useCallback((running) => {
    const next = !!running;
    agentRunningRef.current = next;
    try { window.ATLAS_AGENT_RUNNING = next; } catch (_) {}
    _setAgentRunning(next);
  }, []);
  React.useEffect(() => {
    const subs = [];
    const onGlobalRunning = (ev) => {
      setAgentRunningState(!!(ev && ev.detail && ev.detail.running));
    };
    try {
      if (typeof window.ATLAS_AGENT_RUNNING === 'boolean') {
        setAgentRunningState(window.ATLAS_AGENT_RUNNING);
      }
      window.addEventListener('atlas-agent-running', onGlobalRunning);
      if (window.backend?.subscribe) {
        subs.push(window.backend.subscribe('hello', (m) => {
          if (m && typeof m.running === 'boolean') setAgentRunningState(m.running);
        }));
        subs.push(window.backend.subscribe('agent_state', (m) => {
          if (m && typeof m.running === 'boolean') setAgentRunningState(m.running);
        }));
      }
    } catch (_) {}
    return () => {
      try { window.removeEventListener('atlas-agent-running', onGlobalRunning); } catch (_) {}
      subs.forEach(u => { try { u && u(); } catch (_) {} });
    };
  }, [setAgentRunningState]);

  // Workspace switch in-flight indicator. Backend emits
  // `workspace_changing` right before _setup_workspace runs and
  // `workspace_changed` after success. The banner shows a spinner so
  // the user can see the dropdown click hit something, even though
  // setup_workspace usually finishes in < 100 ms.
  const [wfSwitching, setWfSwitching] = React.useState(null);
  React.useEffect(() => {
    if (!window.backend?.subscribe) return undefined;
    const subs = [];
    try {
      subs.push(window.backend.subscribe('workspace_changing', (m) => {
        setWfSwitching({ from: m?.prev || '', to: m?.workspace || '', ip: m?.ip || '' });
      }));
      subs.push(window.backend.subscribe('workspace_changed', (m) => {
        const loaded = m?.workspace || '';
        setTimeout(() => {
          setWfSwitching(cur => (!loaded || (cur && cur.to === loaded)) ? null : cur);
        }, 300);
        setAgentRunningState(false);
      }));
    } catch (_) {}
    return () => { subs.forEach(u => { try { u && u(); } catch (_) {} }); };
  }, [setAgentRunningState]);

  // First-connect handshake indicator. Runs a small protocol on mount:
  //   1) WS connects               → 'ws'
  //   2) Backend hello received    → 'hello'
  //   3) /healthz responds 200     → 'health'
  //   4) /api/session/list resolves → 'sessions'
  //   5) all of the above complete → 'ready' → banner fades after 1.2 s
  // While any step is outstanding the banner shows a spinner with the
  // current step label. Lets the user see the boot is actually doing
  // something instead of staring at a blank chrome.
  const [bootSteps, setBootSteps] = React.useState({
    ws: 'pending', hello: 'pending', health: 'pending', sessions: 'pending',
    llm: 'pending',
  });
  const [bootHidden, setBootHidden] = React.useState(false);
  const bootEverReadyRef = React.useRef(false);

  // Auth gate — mounts LoginScreen until /api/users/me returns 200.
  const [authState, setAuthState] = React.useState('checking');
  React.useEffect(() => {
    let cancelled = false;
    fetch('/api/users/me', { cache: 'no-store' })
      .then(r => r.ok ? r.json() : Promise.reject(r.status))
      .then(j => {
        if (cancelled) return;
        const user = j && j.user;
        if (!user || !user.username) { setAuthState('unauth'); return; }
        window.ATLAS_USER = user;
        window.ATLAS_USER_SESSION_ID = user.username;
        try {
          const username = normalizeSession(user.username) || user.username;
          const url = new URL(window.location.href);
          const urlSession = normalizeSession(url.searchParams.get('session') || '');
          // splitSessionNamespace('') yields {sessionId:'default', ipId:'default',
          // workflow:'default'} — treating those as authoritative would
          // overwrite a real ?ip= deep link with 'default'. Only consult the
          // parsed namespace when ?session= was actually present.
          const urlParts = urlSession
            ? splitSessionNamespace(urlSession)
            : { sessionId: '', ipId: '', workflow: '' };
          const ipParam = normalizeSession(url.searchParams.get('ip') || url.searchParams.get('ip_id') || '');
          const wfParam = normalizeSession(url.searchParams.get('workflow') || url.searchParams.get('wf') || '');
          const requestedIp = ipParam || normalizeSession(urlParts.ipId || '');
          const requestedWf = wfParam || normalizeSession(urlParts.workflow || '');
          const hasUrlContext = !!(urlSession || requestedIp || requestedWf);
          const currentNs = normalizeSession(window.ACTIVE_SESSION || localStorage.getItem('atlasActiveSession') || '');
          const currentOwner = (currentNs.split('/').filter(Boolean)[0] || '');
          localStorage.setItem('atlasUserSessionId', username);
          if (hasUrlContext || !currentNs || currentNs === 'default' || (currentOwner && currentOwner !== username)) {
            const savedScreen = (() => {
              try { return localStorage.getItem('atlasScreen') || ''; }
              catch (_) { return ''; }
            })();
            const screenWf = savedScreen === 'pipeline'
              ? 'orchestrator'
              : savedScreen === 'architect' ? 'architect' : '';
            const currentParts = currentNs
              ? splitSessionNamespace(currentNs)
              : { sessionId: '', ipId: '', workflow: '' };
            const nextIp = requestedIp || currentParts.ipId || WORKFLOW_DEFAULT;
            const nextWf = requestedWf || screenWf || currentParts.workflow || WORKFLOW_DEFAULT;
            const nextNs = `${username}/${nextIp}/${nextWf}`;
            window.ACTIVE_SESSION = nextNs;
            localStorage.setItem('atlasActiveSession', nextNs);
            setActiveSessionId(username);
            setActiveNamespace(nextNs);
            setActiveIp(nextIp);
            url.searchParams.set('session', nextNs);
            url.searchParams.set('session_id', username);
            url.searchParams.set('ip', nextIp);
            url.searchParams.set('workflow', nextWf);
            url.searchParams.delete('ip_id');
            url.searchParams.delete('wf');
            window.history.replaceState(null, '', url);
          }
          const activeForBackend = normalizeSession(window.ACTIVE_SESSION || localStorage.getItem('atlasActiveSession') || `${username}/default/default`) || `${username}/default/default`;
          if (window.backend && typeof window.backend.disconnect === 'function' && typeof window.backend.connect === 'function') {
            window.backend.disconnect();
            setTimeout(() => window.backend.connect(activeForBackend), 0);
          }
          const parsed = splitSessionNamespace(activeForBackend);
          fetch('/api/session/activate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              session_id: parsed.sessionId || username,
              ip: parsed.ipId || 'default',
              workflow: parsed.workflow || 'default',
            }),
          }).then(() => {
            try { return window.atlasData && window.atlasData.refreshHealth && window.atlasData.refreshHealth(); }
            catch (_) { return null; }
          }).catch(() => {});
        } catch (_) {
          try { localStorage.setItem('atlasUserSessionId', user.username); } catch (_) {}
        }
        setAuthState('authed');
      })
      .catch(() => { if (!cancelled) setAuthState('unauth'); });
    return () => { cancelled = true; };
  }, []);
  React.useEffect(() => {
    if (authState !== 'authed') return undefined;
    let dead = false;
    fetch('/api/pipeline/run_policy', { cache: 'no-store' })
      .then(r => r.ok ? r.json() : Promise.reject(r.status))
      .then(j => {
        if (dead || !j) return;
        if (j.run_mode) setRunMode(normalizeAtlasRunMode(j.run_mode));
        if (j.exec_mode) setExecMode(normalizeAtlasExecMode(j.exec_mode));
      })
      .catch(() => {});
    return () => { dead = true; };
  }, [authState]);
  React.useEffect(() => {
    const mark = (k, v) => setBootSteps(s => (s[k] === v ? s : { ...s, [k]: v }));
    const runProbes = () => {
      // Reset HTTP-side legs to pending so the user sees the rerun.
      setBootSteps(s => ({
        ...s,
        health: 'pending', sessions: 'pending', llm: 'pending',
      }));
      if (!bootEverReadyRef.current) setBootHidden(false);
      fetch('/healthz', { cache: 'no-store' })
        .then(r => mark('health', r.ok ? 'done' : 'fail'))
        .catch(() => mark('health', 'fail'));
      fetch('/api/session/list', { cache: 'no-store' })
        .then(r => mark('sessions', r.ok ? 'done' : 'fail'))
        .catch(() => mark('sessions', 'fail'));
      // LLM provider probe — cheap GET /v1/models. Backend now treats
      // 200/400/404 as "reachable" so this lights ✓ on every common
      // provider (deepseek, openai, codex OAuth, azure deployment
      // without /models exposed).
      fetch('/api/llm/ping', { cache: 'no-store' })
        .then(r => r.ok ? r.json() : Promise.reject(r.status))
        .then(j => mark('llm', j && j.ok ? 'done' : 'fail'))
        .catch(() => mark('llm', 'fail'));
    };

    // Initial WS state — backend.js may have already connected by the
    // time this effect runs.
    if (window.backend?.getConnectionState) {
      const s = window.backend.getConnectionState();
      mark('ws', s === 'open' ? 'done' : (s === 'closed' || s === 'error' ? 'fail' : 'pending'));
    }
    const subs = [];
    try {
      subs.push(window.backend.subscribe('connection', (m) => {
        const next = m?.state === 'open' ? 'done' : 'fail';
        mark('ws', next);
        // On a reconnect (e.g. after backend restart), re-fire the
        // HTTP probes — otherwise the panel stays pinned at whatever
        // it captured the first time the page mounted. The boot card
        // is what the user looks at to confirm "yes the new backend
        // is up", so it MUST refresh after a WS reopen.
        if (next === 'done') runProbes();
      }));
      subs.push(window.backend.subscribe('hello', () => mark('hello', 'done')));
    } catch (_) {}
    runProbes();
    return () => { subs.forEach(u => { try { u && u(); } catch (_) {} }); };
  }, []);
  React.useEffect(() => {
    if (authState !== 'authed') return undefined;
    const needsProbe = (
      bootSteps.health !== 'done'
      || bootSteps.sessions !== 'done'
      || bootSteps.llm !== 'done'
    );
    if (!needsProbe) return undefined;
    let cancelled = false;
    const mark = (key, value) => {
      if (cancelled) return;
      setBootSteps(s => (s[key] === value ? s : { ...s, [key]: value }));
    };
    const t = setTimeout(() => {
      fetch('/api/session/list', { cache: 'no-store' })
        .then(r => mark('sessions', r.ok ? 'done' : 'fail'))
        .catch(() => mark('sessions', 'fail'));
      fetch('/healthz', { cache: 'no-store' })
        .then(r => mark('health', r.ok ? 'done' : 'fail'))
        .catch(() => mark('health', 'fail'));
      fetch('/api/llm/ping', { cache: 'no-store' })
        .then(r => r.ok ? r.json() : Promise.reject(r.status))
        .then(j => mark('llm', j && j.ok ? 'done' : 'fail'))
        .catch(() => mark('llm', 'fail'));
    }, 350);
    return () => {
      cancelled = true;
      clearTimeout(t);
    };
  }, [authState, bootSteps.health, bootSteps.sessions, bootSteps.llm]);
  const bootDone = Object.values(bootSteps).every(v => v === 'done');
  const bootUsable = (
    authState === 'authed'
    && bootSteps.ws === 'done'
    && bootSteps.hello === 'done'
    && bootSteps.llm === 'done'
    && bootSteps.health !== 'fail'
    && bootSteps.sessions !== 'fail'
  );
  const bootDisplayDone = bootDone || bootUsable;
  const bootFailed = !bootDisplayDone && Object.values(bootSteps).some(v => v === 'fail');
  React.useEffect(() => {
    if (bootDisplayDone) {
      bootEverReadyRef.current = true;
      setTimeout(() => {
        if (bootEverReadyRef.current) setBootHidden(true);
      }, 1200);
    }
  }, [bootDisplayDone]);

  const currentWorkflow = React.useCallback(() => {
    return splitSessionNamespace(window.ACTIVE_SESSION || activeNamespace).workflow
      || normalizeSession(window.CONTEXT && window.CONTEXT.workspace)
      || WORKFLOW_DEFAULT;
  }, [activeNamespace, normalizeSession, splitSessionNamespace]);

  const namespaceFor = React.useCallback((sessionId, ipId, workflow) => {
    const owner = normalizeSession(sessionId) || normalizeSession(window.ATLAS_USER_SESSION_ID || '') || 'default';
    const ip = normalizeSession(ipId || WORKFLOW_DEFAULT) || WORKFLOW_DEFAULT;
    const wf = normalizeSession(workflow || WORKFLOW_DEFAULT) || WORKFLOW_DEFAULT;
    return `${owner}/${ip}/${wf}`;
  }, [normalizeSession]);

  const activateBackendWorkflow = React.useCallback((workflow, session) => {
    // Empty input is the only true skip — `default` and `user` are
    // legitimate workspace names (`workflow/default/` exists), so
    // we DO fire /wf for them now. Without this, picking `default`
    // from the workflow dropdown left the agent pinned to whatever
    // workflow was active before — config.TODO_FILE / system prompt /
    // todo template all kept the old workspace's wiring.
    const wf = normalizeSession(workflow) || 'default';
    if (window.backend && typeof window.backend.send === 'function') {
      window.backend.send({ type: 'prompt', text: `/wf ${wf}`, session: session || window.ACTIVE_SESSION || 'default', ui_lang: window.ATLAS_UI_LANG || uiLang });
    }
  }, [normalizeSession, uiLang]);

  const stopForWorkflowSwitch = React.useCallback(() => {
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

  const confirmStopForWorkflowSwitch = React.useCallback((workflow) => {
    const running = agentRunningRef.current || agentRunning || window.ATLAS_AGENT_RUNNING === true;
    if (!running) return true;
    const wf = normalizeSession(workflow) || WORKFLOW_DEFAULT;
    const ok = window.confirm(`Agent is running. Stop it and switch workflow to "${wf}"?`);
    if (!ok) return false;
    stopForWorkflowSwitch();
    return true;
  }, [agentRunning, normalizeSession, stopForWorkflowSwitch]);

  const syncNamespaceUrl = React.useCallback((namespace, owner, ip, workflow) => {
    try {
      const url = new URL(window.location.href);
      const sid = normalizeSession(namespace || '');
      if (sid && sid !== 'default') url.searchParams.set('session', sid);
      else url.searchParams.delete('session');
      if (owner && owner !== 'default') url.searchParams.set('session_id', owner);
      else url.searchParams.delete('session_id');
      if (ip) url.searchParams.set('ip', ip);
      else url.searchParams.delete('ip');
      if (workflow) url.searchParams.set('workflow', workflow);
      else url.searchParams.delete('workflow');
      window.history.replaceState(null, '', url);
    } catch (_) {}
  }, [normalizeSession]);

  const activateNamespace = React.useCallback((sessionId, ipId, workflow, syncWorkflow = true, opts = {}) => {
    const owner = normalizeSession(sessionId) || 'default';
    const ip = normalizeSession(ipId || WORKFLOW_DEFAULT) || WORKFLOW_DEFAULT;
    const wf = normalizeSession(workflow || WORKFLOW_DEFAULT) || WORKFLOW_DEFAULT;
    const preserveRunning = !!(opts && opts.preserveRunning);
    const namespace = namespaceFor(owner, ip, wf);
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
    setActiveIp(ip);
    setActiveNamespace(namespace);
    window.ACTIVE_SESSION = namespace;
    try { localStorage.setItem('atlasActiveSession', namespace); } catch (_) {}
    try {
      window.dispatchEvent(new CustomEvent('atlas-session-switched', {
        detail: { sessionId: owner, namespace, ip, workflow: wf },
      }));
    } catch (_) {}
    if (prev !== namespace && window.backend && typeof window.backend.disconnect === 'function' && typeof window.backend.connect === 'function') {
      window.backend.disconnect();
      setTimeout(() => window.backend.connect(namespace), 0);
    }
    if (window.atlasData && typeof window.atlasData.setUserSessionId === 'function') {
      window.atlasData.setUserSessionId(owner);
    } else {
      window.ATLAS_USER_SESSION_ID = owner;
      try { localStorage.setItem('atlasUserSessionId', owner); } catch (_) {}
    }
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
      const loadStartedAt = Date.now();
      let activated = false;
      try {
        const res = await fetch('/api/session/activate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_id: owner || 'default',
            ip: ip || 'default',
            workflow: wf || 'default',
            preserve_running: preserveRunning,
          }),
        });
        activated = !!(res && res.ok);
      } catch (_) {}
      if (syncWorkflow && !activated) activateBackendWorkflow(wf, namespace);
      if (workflowChanged) {
        if (!preserveRunning) setAgentRunningState(false);
        const delay = Math.max(0, 450 - (Date.now() - loadStartedAt));
        setTimeout(() => {
          setWfSwitching(cur => (
            cur && cur.to === wf && cur.ip === ip ? null : cur
          ));
        }, delay);
      }
    };
    _activateAndDispatch();
    return namespace;
  }, [activateBackendWorkflow, namespaceFor, normalizeSession, setAgentRunningState, splitSessionNamespace, syncNamespaceUrl]);

  React.useEffect(() => {
    window.activateAtlasNamespace = activateNamespace;
    return () => {
      if (window.activateAtlasNamespace === activateNamespace) {
        delete window.activateAtlasNamespace;
      }
    };
  }, [activateNamespace]);

  // Synthetic / reserved namespace segments that should never show
  // up in the ip_id dropdown. 'soc' is the SoC architect placeholder,
  // 'user' is the legacy ip-less sentinel (still in the wild on disk
  // from older runs), and any workflow name (ssot-gen, rtl-gen, …)
  // that slipped into the IP slot from `${owner}/${wf}` namespaces
  // gets filtered too. 'default' stays selectable as the explicit
  // default IP_ID.
  const RESERVED_IP_NAMES = React.useMemo(
    () => new Set(['soc', 'user', ...TOP_WORKFLOWS]),
    [TOP_WORKFLOWS]
  );

  const refreshTopTargets = React.useCallback(async () => {
    const nextSessionIds = new Set(['default']);
    const currentUserSession = normalizeSession(window.ATLAS_USER_SESSION_ID || activeSessionId);
    if (currentUserSession) nextSessionIds.add(currentUserSession);
    const nextIps = new Set([WORKFLOW_DEFAULT]);
    const acceptIp = (id) => id && (id === WORKFLOW_DEFAULT || !RESERVED_IP_NAMES.has(id));
    try {
      const r = await fetch('/api/session/list', { cache: 'no-store' });
      if (r.ok) {
        const d = await r.json();
        for (const row of (Array.isArray(d.sessions) ? d.sessions : [])) {
          const raw = (row && row.session) || '';
          const segments = String(raw).split('/').filter(Boolean);
          const parsed = splitSessionNamespace(raw);
          if (parsed.sessionId) nextSessionIds.add(parsed.sessionId);
          // Only surface an IP if the on-disk namespace explicitly
          // names an owner (i.e. 3-segment <owner>/<ip>/<wf>). Legacy
          // 2-segment <ip>/<wf> trees parse to {sessionId:'default'},
          // and pre-owner backends used to drop bare-IP dirs that
          // still linger on disk; we don't want them in *this* user's
          // dropdown. Also require the parsed owner to match the
          // current user_session — backend is per-user (operator runs
          // one process per user), so cross-owner pollution is noise.
          if (segments.length < 3) continue;
          // /api/session/list still feeds SESSION_ID. We deliberately
          // stopped collecting IPs from it because the dropdown should
          // reflect what's literally on disk under PROJECT_ROOT, not
          // every IP that ever showed up in a session namespace.
        }
      }
    } catch (_) {}
    // PROJECT_ROOT scan — the new authoritative source for IP_ID. The
    // backend just enumerates first-level dirs that look like IPs
    // (have yaml/, rtl/, tb/, or sim/) and skips framework dirs. That
    // matches the user's mental model: "IP_ID lists IPs the backend
    // is running over, nothing more."
    try {
      const ipOwner = normalizeSession(activeSessionId || currentUserSession || '');
      const ipUrl = '/api/ip/list' + (ipOwner ? `?session_id=${encodeURIComponent(ipOwner)}` : '');
      const r2 = await fetch(ipUrl, { cache: 'no-store' });
      if (r2.ok) {
        const d2 = await r2.json();
        for (const it of (Array.isArray(d2.items) ? d2.items : [])) {
          if (acceptIp(it.name)) nextIps.add(it.name);
        }
      }
    } catch (_) {}

    const liveNamespace = normalizeSession(window.ACTIVE_SESSION || activeNamespace) || namespaceFor(currentUserSession, activeIp, currentWorkflow());
    const parsedLive = splitSessionNamespace(liveNamespace);
    if (parsedLive.sessionId) nextSessionIds.add(parsedLive.sessionId);
    // Don't auto-include parsedLive.ipId: when the user deletes a
    // session on disk (rm -rf .session/<owner>/<ip>/<wf>) the
    // localStorage cached ACTIVE_SESSION still parses to the dead
    // ip, and this line used to keep adding it to the dropdown
    // forever. Now the dropdown reflects only what /api/session/list
    // and /api/soc actually have, plus whatever createIp() seeded
    // locally (which sticks for one render cycle, then naturally
    // drops if it never lands on disk).
    setSessionIdOptions(Array.from(nextSessionIds).sort((a, b) => {
      if (a === currentUserSession) return -1;
      if (b === currentUserSession) return 1;
      if (a === 'default') return -1;
      if (b === 'default') return 1;
      return a.localeCompare(b);
    }));
    const sortedIps = Array.from(nextIps).sort((a, b) => {
      if (a === WORKFLOW_DEFAULT) return -1;
      if (b === WORKFLOW_DEFAULT) return 1;
      return a.localeCompare(b);
    });
    setIpOptions(sortedIps);
    // Expose for inline-code-chip click validation in workspace.jsx so
    // only IPs that actually exist on disk become clickable.
    window.IP_OPTIONS = sortedIps;
    setActiveSessionId(parsedLive.sessionId || currentUserSession || 'default');
    setActiveNamespace(liveNamespace);
    setActiveIp(parsedLive.ipId === 'soc' ? WORKFLOW_DEFAULT : (parsedLive.ipId || WORKFLOW_DEFAULT));
  }, [activeIp, activeNamespace, activeSessionId, currentWorkflow, namespaceFor, normalizeSession, splitSessionNamespace]);

  React.useEffect(() => {
    let timer = null;
    const syncCurrent = (ev) => {
      const ctx = window.CONTEXT || {};
      const ctxSession = normalizeSession(ctx.active_session || ctx.activeSession || '');
      // refreshHealth periodic poll → backend is the ground truth.
      // Snap UI dropdowns to whatever the backend reports as the active
      // (sid, ip, wf), except when backend is still at the boot
      // "default/default/default" placeholder — let the user's
      // localStorage / URL hint own that brief window.
      const isHealthTick = ev && ev.type === 'atlas-data-changed' && ev.detail === 'CONTEXT';
      let namespace;
      if (isHealthTick && ctxSession && ctxSession !== 'default/default/default') {
        const ctxOwner = (ctxSession.split('/').filter(Boolean)[0] || '');
        const authOwner = normalizeSession(
          (window.ATLAS_USER && window.ATLAS_USER.username) ||
          window.ATLAS_USER_SESSION_ID ||
          activeSessionId ||
          ''
        );
        const initialUrlNamespace = normalizeSession(initialUrlNamespaceRef.current || '');
        const currentNamespace = normalizeSession(window.ACTIVE_SESSION || activeNamespace || '');
        const parsedUrl = splitSessionNamespace(initialUrlNamespace);
        const parsedCtx = splitSessionNamespace(ctxSession);
        const urlStillOwnsBoot = !!(
          initialUrlNamespace &&
          ctxSession !== initialUrlNamespace &&
          (currentNamespace === initialUrlNamespace || activeNamespace === initialUrlNamespace) &&
          (!parsedUrl.sessionId || !parsedCtx.sessionId || parsedUrl.sessionId === parsedCtx.sessionId)
        );
        // During login and fast screen changes, /healthz can briefly report
        // the process bootstrap namespace (often default/<ip>/<wf>). In
        // DB-backed multi-user mode the authenticated user owns the browser
        // namespace, so do not let that stale backend context rewrite the UI
        // back to default and poison the websocket session.
        if (urlStillOwnsBoot) {
          namespace = initialUrlNamespace;
        } else if (authOwner && ctxOwner && ctxOwner !== authOwner && ctxOwner !== 'local-admin') {
          namespace = normalizeSession(window.ACTIVE_SESSION || activeNamespace || '');
        } else {
          namespace = ctxSession;
        }
        if (namespace && namespace !== window.ACTIVE_SESSION) {
          window.ACTIVE_SESSION = namespace;
          try { localStorage.setItem('atlasActiveSession', namespace); } catch (_) {}
        }
      } else {
        const requestedSession = normalizeSession(
          (ev && ev.detail && typeof ev.detail === 'object' && ev.detail.session) ||
          window.ACTIVE_SESSION || activeNamespace
        );
        namespace = requestedSession || ctxSession;
      }
      const parsed = splitSessionNamespace(namespace);
      const owner = parsed.sessionId || activeSessionId || 'default';
      const ipSeg = parsed.ipId === 'soc' ? WORKFLOW_DEFAULT : (parsed.ipId || activeIp || WORKFLOW_DEFAULT);
      const wfSeg = parsed.workflow || WORKFLOW_DEFAULT;
      const canonicalNamespace = namespaceFor(owner, ipSeg, wfSeg);
      if (canonicalNamespace && canonicalNamespace !== window.ACTIVE_SESSION) {
        window.ACTIVE_SESSION = canonicalNamespace;
        try { localStorage.setItem('atlasActiveSession', canonicalNamespace); } catch (_) {}
      }
      if (initialUrlNamespaceRef.current && canonicalNamespace === normalizeSession(initialUrlNamespaceRef.current)) {
        initialUrlNamespaceRef.current = '';
      }
      setActiveNamespace(canonicalNamespace);
      setActiveSessionId(owner);
      setActiveIp(ipSeg);
      // Push the canonical triple into the URL so the address bar
      // never silently disagrees with what the server reports.
      // Without this, reloading after a triple flip kept the OLD
      // ?ip=…&workflow=… params visible even though dropdowns / file
      // tree had pivoted to the new triple.
      try {
        if (canonicalNamespace) syncNamespaceUrl(canonicalNamespace, owner, ipSeg, wfSeg);
      } catch (_) {}
      clearTimeout(timer);
      timer = setTimeout(refreshTopTargets, 150);
    };
    refreshTopTargets();
    window.addEventListener('atlas-session-loaded', syncCurrent);
    window.addEventListener('atlas-conversation-loaded', syncCurrent);
    window.addEventListener('atlas-data-changed', syncCurrent);
    return () => {
      clearTimeout(timer);
      window.removeEventListener('atlas-session-loaded', syncCurrent);
      window.removeEventListener('atlas-conversation-loaded', syncCurrent);
      window.removeEventListener('atlas-data-changed', syncCurrent);
    };
  }, [activeIp, activeNamespace, activeSessionId, currentWorkflow, namespaceFor, normalizeSession, refreshTopTargets, splitSessionNamespace]);

  React.useEffect(() => {
    // Don't fire the URL/localStorage → backend handshake before we
    // know who the logged-in user is. Without this guard a stale
    // localStorage entry like "default/sqa/default" left over from a
    // previous run would post /api/session/activate with owner='default'
    // before the auth gate had a chance to rewrite to <user>/default,
    // producing the surprising "prev='', ip='sqa', owner='default'"
    // backend log on first connection.
    if (!window.ATLAS_USER) return;
    const parsed = splitSessionNamespace(window.ACTIVE_SESSION || activeNamespace || '');
    if (!parsed.ipId && !parsed.workflow) return;
    // Also bail if the parsed owner is not this user — the auth
    // gate will rewrite localStorage and we'll re-fire then.
    const owner = parsed.sessionId || '';
    if (owner && owner !== (window.ATLAS_USER.username || '')) return;
    const savedScreen = (() => {
      try { return localStorage.getItem('atlasScreen') || ''; }
      catch (_) { return ''; }
    })();
    const screenWf = savedScreen === 'pipeline'
      ? 'orchestrator'
      : savedScreen === 'architect' ? 'architect' : '';
    activateNamespace(
      parsed.sessionId || activeSessionId || 'default',
      parsed.ipId || WORKFLOW_DEFAULT,
      screenWf || parsed.workflow || WORKFLOW_DEFAULT,
      true
    );
    // Run once on mount AFTER auth: this is the URL/localStorage → backend handshake.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authState]);

  React.useEffect(() => {
    const onSwitch = (ev) => {
      const sessionId = ev?.detail?.sessionId;
      const namespace = ev?.detail?.namespace;
      if (!sessionId) return;
      const parsed = splitSessionNamespace(namespace || window.ACTIVE_SESSION || '');
      const owner = normalizeSession(parsed.sessionId || sessionId);
      setActiveSessionId(owner);
      setActiveNamespace(namespace || window.ACTIVE_SESSION || namespaceFor(owner, activeIp, currentWorkflow()));
      setActiveIp(parsed.ipId === 'soc' ? WORKFLOW_DEFAULT : (parsed.ipId || activeIp || WORKFLOW_DEFAULT));
      syncNamespaceUrl(
        namespace || window.ACTIVE_SESSION || '',
        owner,
        parsed.ipId === 'soc' ? WORKFLOW_DEFAULT : (parsed.ipId || WORKFLOW_DEFAULT),
        parsed.workflow || WORKFLOW_DEFAULT
      );
      refreshTopTargets();
    };
    window.addEventListener('atlas-session-switched', onSwitch);
    return () => window.removeEventListener('atlas-session-switched', onSwitch);
  }, [activeIp, currentWorkflow, namespaceFor, normalizeSession, refreshTopTargets, splitSessionNamespace, syncNamespaceUrl]);

  const selectSessionId = (rawSessionId) => {
    const owner = normalizeSession(rawSessionId) || 'default';
    const ip = activeIp || WORKFLOW_DEFAULT;
    const wf = currentWorkflow() || WORKFLOW_DEFAULT;
    activateNamespace(owner, ip, wf, true);
  };

  const selectIp = (rawIp) => {
    const ip = normalizeSession(rawIp) || WORKFLOW_DEFAULT;
    // Picking an IP keeps the current workflow when it is valid. The
    // explicit default IP_ID is a real selectable namespace segment, not
    // a request to clear the workflow.
    const cur = currentWorkflow();
    const wf = isWorkflowSegment(cur) ? cur : WORKFLOW_DEFAULT;
    activateNamespace(activeSessionId, ip, wf, true);
  };

  // Switch workflow segment of the active namespace. default is an
  // explicit workflow segment; /api/session/activate loads the matching
  // backend prompt, TODO file and workspace config.
  const selectWorkflow = (rawWf) => {
    const wf = normalizeSession(rawWf) || WORKFLOW_DEFAULT;
    if (wf === (currentWorkflow() || WORKFLOW_DEFAULT)) return;
    const preserveRunning = execMode === 'orchestrator';
    const ok = preserveRunning || confirmStopForWorkflowSwitch(wf);
    if (!ok) return;
    const ip = activeIp || WORKFLOW_DEFAULT;
    activateNamespace(activeSessionId, ip, wf, true, { preserveRunning });
  };

  const beginNameEntry = (kind) => {
    setTopNotice('');
    setNameEntry({ kind, value: '' });
  };

  const commitNewSessionId = (raw) => {
    if (!raw) return;
    const owner = normalizeSession(raw);
    if (!owner) {
      showNotice('Invalid session_id. Use only [A-Za-z0-9_.-].');
      return false;
    }
    setSessionIdOptions(prev => Array.from(new Set([owner].concat(prev || []))));
    const ip = activeIp || WORKFLOW_DEFAULT;
    const wf = currentWorkflow() || WORKFLOW_DEFAULT;
    activateNamespace(owner, ip, wf, true);
    return true;
  };

  const newSessionId = () => beginNameEntry('session');

  // Create a brand-new IP under the current user_session and switch
  // to it. Mirrors the simplicity of `+ Session` but takes a name
  // because IPs are named identifiers rather than disposable scratch
  // owners. The actual on-disk .session/<sid>/<ip>/<wf>/ tree gets
  // created by _setup_session on the next /wf or agent run.
  const createIp = async (raw) => {
    if (!raw) return;
    const ip = normalizeSession(raw);
    if (!ip) {
      showNotice('Invalid IP name. Use only [A-Za-z0-9_.-].');
      return false;
    }
    // IP names are globally unique across all sessions — two different
    // sessions cannot both own an IP called "gpio_pad". /api/session/list
    // is the per-owner namespace walk; aggregate across every row to
    // catch collisions in OTHER sessions even though those won't show
    // up in the current dropdown.
    try {
      const r = await fetch('/api/session/list', { cache: 'no-store' });
      if (r.ok) {
        const d = await r.json();
        const taken = new Set();
        for (const row of (Array.isArray(d.sessions) ? d.sessions : [])) {
          const segs = String((row && row.session) || '').split('/').filter(Boolean);
          if (segs.length >= 3) taken.add(segs[1]);
        }
        if (taken.has(ip)) {
          showNotice(`IP "${ip}" already exists in another session — IP names must be globally unique.`);
          return false;
        }
      }
    } catch (_) {}
    // `/new-ip` is the single source of truth for IP scaffolding. Do not
    // pre-create <PROJECT_ROOT>/<ip>/ here; doing both paths can produce
    // duplicated scope prefixes such as gpio/gpio/...
    const authedOwner = normalizeSession(
      (window.ATLAS_USER && window.ATLAS_USER.username)
      || window.ATLAS_USER_SESSION_ID
      || ''
    );
    const me = authedOwner
      || activeSessionId
      || 'default';
    const namespace = `${me}/${ip}/ssot-gen`;
    // Local state first so the dropdown and scope reflect the new IP
    // immediately while the WS round-trips run.
    setIpOptions(prev => Array.from(new Set([ip].concat(prev || []))));
    setActiveIp(ip);
    setActiveSessionId(me);
    setActiveNamespace(namespace);
    try { setScreen('workspace'); localStorage.atlasScreen = 'workspace'; } catch (_) {}
    window.ACTIVE_SESSION = namespace;
    try { localStorage.setItem('atlasActiveSession', namespace); } catch (_) {}
    syncNamespaceUrl(namespace, me, ip, 'ssot-gen');
    if (window.atlasData && typeof window.atlasData.setUserSessionId === 'function') {
      window.atlasData.setUserSessionId(me);
    }
    if (window.atlasData && typeof window.atlasData.setScopePath === 'function') {
      window.atlasData.setScopePath(ip);
    }
    // /api/session/activate synchronously loads ssot-gen now, so /new-ip
    // can be queued directly without a redundant `/wf ssot-gen` racing
    // behind it.
    try {
      await fetch('/api/session/activate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: me, ip, workflow: 'ssot-gen' }),
      });
    } catch (_) {}
    if (window.backend && typeof window.backend.connect === 'function') {
      try { window.backend.connect(namespace); } catch (_) {}
    }
    if (window.backend && typeof window.backend.send === 'function') {
      try {
        window.backend.send({
          type: 'prompt',
          msg_id: makePromptMsgId(),
          text: `/new-ip ${ip}`,
          session: namespace,
          ui_lang: window.ATLAS_UI_LANG || uiLang,
        });
      } catch (_) {}
    }
    setTimeout(() => {
      try { window.atlasData && window.atlasData.refreshFileTree && window.atlasData.refreshFileTree(ip, { recursive: true }); } catch (_) {}
      try { refreshTopTargets(); } catch (_) {}
    }, 1500);
    return true;
  };

  const commitNameEntry = async () => {
    if (!nameEntry) return;
    const raw = String(nameEntry.value || '').trim();
    if (!raw) {
      setNameEntry(null);
      return;
    }
    const ok = nameEntry.kind === 'session'
      ? commitNewSessionId(raw)
      : await createIp(raw);
    if (ok) setNameEntry(null);
  };

  // Top-level screen — 'workspace' (live agent + chat + sidebar) or
  // 'pipeline' (live stage dispatcher + situation board + chat).
  // Old 'architect' value (mock-data SoC view) migrates to 'pipeline'
  // on first load so existing sessions don't get stranded on a screen
  // that no longer exists.
  const [screen, setScreen] = React.useState(() => {
    try {
      const params = new URLSearchParams(window.location.search || '');
      const urlView = (params.get('view') || '').trim().toLowerCase();
      if (urlView === 'pipeline' || urlView === 'architect') return urlView;
      const urlIp = (params.get('ip') || params.get('ip_id') || '').trim();
      if (urlIp && urlIp !== 'default') return 'pipeline';
      const saved = localStorage.atlasScreen;
      if (saved === 'pipeline' || saved === 'architect') return saved;
      return 'workspace';
    } catch (_) { return 'workspace'; }
  });
  React.useEffect(() => {
    try { localStorage.atlasScreen = screen; } catch (_) {}
  }, [screen]);
  const workflowWorkspaceOpenRef = React.useRef(false);

  React.useEffect(() => {
    const onOpenEvidence = (ev) => {
      const path = String(ev?.detail?.path || '').trim();
      if (!path) return;
      try { localStorage.setItem('atlasPreviewPath', path); } catch (_) {}
      setScreen('workspace');
      setTimeout(() => {
        try {
          window.dispatchEvent(new CustomEvent('atlas-chip-open', {
            detail: { path, source: ev?.detail?.source || 'pipeline' },
          }));
        } catch (_) {}
      }, 0);
    };
    window.addEventListener('atlas:open_evidence', onOpenEvidence);
    return () => window.removeEventListener('atlas:open_evidence', onOpenEvidence);
  }, []);

  React.useEffect(() => {
    const onOpenWorkflowWorkspace = (ev) => {
      const detail = ev?.detail || {};
      const workflow = normalizeSession(detail.workflow || '');
      if (!workflow) return;
      const parsed = splitSessionNamespace(window.ACTIVE_SESSION || activeNamespace || '');
      const owner = normalizeSession(
        detail.sessionId ||
        parsed.sessionId ||
        activeSessionId ||
        window.ATLAS_USER_SESSION_ID ||
        (window.ATLAS_USER && window.ATLAS_USER.username) ||
        'default'
      ) || 'default';
      const ip = normalizeSession(
        detail.ip ||
        parsed.ipId ||
        activeIp ||
        window.SCOPE_PATH ||
        WORKFLOW_DEFAULT
      ) || WORKFLOW_DEFAULT;
      const path = String(detail.path || '').trim();
      const activeWorkflow = normalizeSession(parsed.workflow || currentWorkflow() || WORKFLOW_DEFAULT) || WORKFLOW_DEFAULT;
      // In orchestrator + multi-worker mode, pipeline worker cards are
      // workspace switches, not single-worker stop/restart boundaries.
      const preserveRunning = (
        detail.source === 'pipeline'
        && workflow !== activeWorkflow
        && (activeWorkflow === 'orchestrator' || execMode === 'orchestrator')
      );

      workflowWorkspaceOpenRef.current = true;
      if (!preserveRunning && !confirmStopForWorkflowSwitch(workflow)) return;
      activateNamespace(owner, ip, workflow, true, { preserveRunning });
      setScreen('workspace');
      if (path) {
        try { localStorage.setItem('atlasPreviewPath', path); } catch (_) {}
        setTimeout(() => {
          try {
            window.dispatchEvent(new CustomEvent('atlas-chip-open', {
              detail: { path, source: detail.source || 'pipeline' },
            }));
          } catch (_) {}
        }, 0);
      }
    };
    window.addEventListener('atlas:open_workflow_workspace', onOpenWorkflowWorkspace);
    return () => window.removeEventListener('atlas:open_workflow_workspace', onOpenWorkflowWorkspace);
  }, [
    activeIp,
    activeNamespace,
    activeSessionId,
    activateNamespace,
    confirmStopForWorkflowSwitch,
    currentWorkflow,
    execMode,
    normalizeSession,
    splitSessionNamespace,
  ]);

  // Auto-switch the agent's workflow when entering / leaving Architect.
  // Architect is a SoC-level supervisor (one tier above ssot-gen,
  // rtl-gen, sim, lint, …), so the persona that handles its chat needs
  // to be different. We only fire the switch on *transition* (not on
  // every render) and only after window.backend is ready.
  const prevScreenRef = React.useRef(screen);
  React.useEffect(() => {
    const prev = prevScreenRef.current;
    if (prev === screen) return;
    prevScreenRef.current = screen;
    // Don't fire on initial mount — backend may not be connected yet,
    // and the user's current workflow is whatever the server picked.
    // Only react to genuine user-initiated screen flips.
    if (!window.backend || typeof window.backend.send !== 'function') return;
    if (screen === 'architect' || screen === 'pipeline') {
      // Disable via localStorage if user finds it disruptive.
      const optOut = (() => { try { return localStorage.getItem('atlasArchAutoSwitch') === 'off'; }
                              catch (_) { return false; } })();
      // Pipeline screen routes its chat to the orchestrator workflow
      // (the orchestrator IS the conversation surface that decides
      // which worker to dispatch). Architect screen still gets the
      // architect agent for SoC-level design conversations.
      const targetWorkflow = screen === 'pipeline' ? 'orchestrator' : 'architect';
      if (!optOut) {
        activateNamespace(activeSessionId, activeIp || WORKFLOW_DEFAULT, targetWorkflow, true, {
          preserveRunning: execMode === 'orchestrator' && targetWorkflow === 'orchestrator',
        });
      }
    } else if (prev === 'architect' || prev === 'pipeline') {
      if (workflowWorkspaceOpenRef.current) {
        workflowWorkspaceOpenRef.current = false;
        return;
      }
      if (prev === 'pipeline' && execMode === 'orchestrator') {
        return;
      }
      // Leaving pipeline/architect → fall back to default (could be
      // smarter and restore the prior workflow, but default keeps
      // things simple).
      const optOut = (() => { try { return localStorage.getItem('atlasArchAutoSwitch') === 'off'; }
                              catch (_) { return false; } })();
      if (!optOut) {
        activateNamespace(activeSessionId, activeIp || WORKFLOW_DEFAULT, WORKFLOW_DEFAULT, true, {
          preserveRunning: execMode === 'orchestrator' && prev === 'pipeline',
        });
      }
    }
  }, [activateNamespace, activeIp, activeSessionId, execMode, screen, uiLang]);

  React.useEffect(() => {
    document.documentElement.setAttribute('data-dir', dir);
    document.documentElement.setAttribute('data-theme', theme);
    document.documentElement.setAttribute('data-font', fontMode);
    document.documentElement.setAttribute('data-font-scale', fontScale);
  }, [dir, theme, fontMode, fontScale]);

  // Page-load stop guard. Whenever the App mounts (fresh reload, new
  // tab) we fire /api/control/stop so any agent run left over from a
  // prior session halts immediately, instead of resuming for 1000
  // iterations under the user's nose. The backend handler is
  // idempotent — sending stop when nothing is running is a no-op.
  // Followed by a /healthz refresh so the workspace state visible in
  // the UI matches whatever the backend ended up settling on.
  React.useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        await fetch('/api/control/stop', {
          method: 'POST',
          cache: 'no-store',
          keepalive: true,
        });
      } catch (_) {}
      if (cancelled) return;
      // Immediately re-read /healthz so the UI's session/ip/workflow
      // chips reflect the post-stop server state.
      try {
        if (window.atlasData && typeof window.atlasData.refreshHealth === 'function') {
          await window.atlasData.refreshHealth();
        }
      } catch (_) {}
    })();
    return () => { cancelled = true; };
  }, []);

  const sendControl = React.useCallback((type) => {
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
  const [, bump] = React.useReducer(x => x + 1, 0);
  React.useEffect(() => {
    const h = () => bump();
    window.addEventListener('atlas-data-changed', h);
    return () => window.removeEventListener('atlas-data-changed', h);
  }, []);

  // Global Esc → tell the agent to abort the current iteration. We
  // skip the binding when an open ask_user card has focus, since Esc
  // there should cancel the card (handled inside that component).
  React.useEffect(() => {
    const onKey = (e) => {
      // Ctrl+Q (or Cmd+Q) → ask to terminate the current session worker.
      if ((e.ctrlKey || e.metaKey) && (e.key === 'q' || e.key === 'Q')) {
        e.preventDefault();
        if (!confirm('Terminate this session worker? Atlas UI will stay open.')) return;
        sendControl('shutdown');
        return;
      }
      // Esc → tell the agent to abort the current iteration.
      if (e.key === 'Escape') {
        const active = document.activeElement;
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
    const Lg = window.LoginScreen;
    return Lg
      ? <div className="app" data-dir={dir} data-theme={theme}>
          <Lg onAuth={() => window.location.reload()} />
        </div>
      : <div className="app" data-dir={dir} data-theme={theme} />;
  }

  return (
    <div className="app" data-dir={dir} data-theme={theme}>
      {topNotice && (
        <div role="alert" style={{
          padding: '6px 12px', fontSize: 12, fontFamily: 'var(--mono)',
          background: 'color-mix(in oklch, var(--warn) 14%, transparent)',
          color: 'var(--warn)', borderBottom: '1px solid var(--warn)',
          display: 'flex', alignItems: 'center', gap: 8,
        }}>
          <span>⚠</span>
          <span style={{ flex: 1 }}>{topNotice}</span>
          <button onClick={() => setTopNotice('')}
                  style={{ background: 'transparent', border: 'none', color: 'var(--warn)',
                           cursor: 'pointer', fontSize: 14, lineHeight: 1 }}>×</button>
        </div>
      )}
      {wfSwitching && (
        <div role="status" aria-live="polite" style={{
          position: 'absolute', top: 0, left: 0, right: 0, zIndex: 300,
          padding: '2px 10px', fontSize: 11, fontFamily: 'var(--mono)',
          background: 'color-mix(in oklch, var(--accent) 22%, var(--bg, #000))',
          color: 'var(--accent)', borderBottom: '1px solid var(--accent)',
          display: 'flex', alignItems: 'center', gap: 8,
          height: 20, lineHeight: '16px',
        }}>
          <span style={{
            display: 'inline-block',
            width: 12, height: 12,
            border: '2px solid currentColor',
            borderRightColor: 'transparent',
            borderRadius: '50%',
            animation: 'atlas-spin 0.9s linear infinite',
          }} />
          <span style={{ flex: 1 }}>
            <strong>Workflow Loading ...</strong>{' '}
            <code>{wfSwitching.from || 'default'}</code> → <code>{wfSwitching.to}</code>
            {wfSwitching.ip ? <> · ip=<code>{wfSwitching.ip}</code></> : null}
            <span style={{ marginLeft: 8, opacity: 0.7 }}>
              {wfSwitching.preserveRunning ? '(previous worker kept running)' : '(agent stopped while loading)'}
            </span>
          </span>
          <style>{`@keyframes atlas-spin{to{transform:rotate(360deg)}}`}</style>
        </div>
      )}
      {!bootHidden && (
        <div role="status" aria-live="polite" style={{
          // Centered overlay so the user notices the handshake the
          // moment the page paints. Theme tokens drive bg/fg so dark
          // mode shows dark-on-dark and light mode shows light-on-
          // light; previous hardcoded `var(--bg-1, #14171c)` had a
          // baked-in dark fallback that clashed in light mode because
          // --bg-1 wasn't defined in styles.css.
          position: 'fixed',
          top: '50%', left: '50%',
          transform: 'translate(-50%, -50%)',
          zIndex: 9999,
          minWidth: 360,
          maxWidth: 480,
          padding: '18px 22px',
          fontSize: 13, fontFamily: 'var(--mono)',
          background: 'var(--bg-2)',
          border: '1px solid ' + (bootFailed ? 'var(--red, #ef4444)' : (bootDisplayDone ? 'var(--green, #22c55e)' : 'var(--accent)')),
          borderRadius: 8,
          boxShadow: '0 8px 32px color-mix(in oklch, var(--fg) 25%, transparent)',
          color: 'var(--fg)',
          display: 'flex', flexDirection: 'column', gap: 12,
          transition: 'opacity 250ms ease',
          opacity: bootDisplayDone ? 0.94 : 1,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            {!bootDisplayDone && !bootFailed && (
              <span style={{
                display: 'inline-block',
                width: 18, height: 18,
                border: '2px solid currentColor',
                borderRightColor: 'transparent',
                borderRadius: '50%',
                animation: 'atlas-spin 0.9s linear infinite',
                flexShrink: 0,
              }} />
            )}
            {bootDisplayDone && <span style={{ fontSize: 20, fontWeight: 700 }}>✓</span>}
            {bootFailed && <span style={{ fontSize: 20, fontWeight: 700 }}>⚠</span>}
            <span style={{ fontWeight: 600 }}>
              {bootDisplayDone ? 'Backend connected'
                : bootFailed ? 'Connection problem'
                : 'Connecting to backend…'}
            </span>
            <span style={{ flex: 1 }} />
            <button onClick={() => setBootHidden(true)}
                    style={{ background: 'transparent', border: 'none',
                             color: 'currentColor', cursor: 'pointer',
                             fontSize: 18, lineHeight: 1, padding: 0 }}
                    title="dismiss">×</button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            {Object.entries(bootSteps).map(([k, v]) => {
              const labels = {
                ws: 'WebSocket connection',
                hello: 'Backend handshake (hello)',
                health: '/healthz endpoint',
                sessions: 'Session list hydrated',
                llm: 'LLM provider reachable (/models probe)',
              };
              return (
                <div key={k} style={{
                  display: 'flex', alignItems: 'center', gap: 10,
                  fontSize: 12,
                  opacity: v === 'done' ? 1 : v === 'fail' ? 1 : 0.7,
                  color: v === 'done' ? 'var(--green, #22c55e)' : v === 'fail' ? 'var(--red, #ef4444)' : 'currentColor',
                }}>
                  <span style={{ width: 14, textAlign: 'center', fontWeight: 700 }}>
                    {v === 'done' ? '✓' : v === 'fail' ? '✗' : '○'}
                  </span>
                  <span>{labels[k] || k}</span>
                </div>
              );
            })}
          </div>
          <style>{`@keyframes atlas-spin{to{transform:rotate(360deg)}}`}</style>
        </div>
      )}
      <div className="dir-switcher">
        <label className="dir-select-wrap" title={`Select user/browser session_id. Active namespace: .session/${normalizeSession(activeNamespace) || 'default'}`}>
          <span>session_id</span>
          <select
            className="dir-select"
            value={activeSessionId || 'default'}
            onChange={e => selectSessionId(e.currentTarget.value)}>
            {sessionIdOptions.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </label>
        <button className="dir-btn"
                title="Create a fresh browser/user session_id and keep the selected IP/workflow"
                onClick={newSessionId}>+ Session</button>
        {nameEntry && nameEntry.kind === 'session' && (
          <form className="dir-name-entry"
                data-esc-local="true"
                title="New session_id: letters, digits, underscore, dash, or dot"
                onSubmit={(e) => { e.preventDefault(); commitNameEntry(); }}>
            <input ref={nameEntryInputRef}
                   className="dir-name-input"
                   aria-label="New session_id"
                   placeholder="session_id"
                   value={nameEntry.value}
                   onChange={e => setNameEntry({ kind: 'session', value: e.currentTarget.value })}
                   onKeyDown={e => {
                     if (e.key === 'Escape') {
                       e.preventDefault();
                       setNameEntry(null);
                     }
                   }} />
            <button type="submit" className="dir-name-action">OK</button>
            <button type="button" className="dir-name-action"
                    aria-label="Cancel new session_id"
                    onClick={() => setNameEntry(null)}>×</button>
          </form>
        )}
        <label className="dir-select-wrap" title="Select ip_id. The current workflow is appended to session_id/ip_id/workflow.">
          <span>ip_id</span>
          <select
            className="dir-select ip"
            value={activeIp || WORKFLOW_DEFAULT}
            onChange={e => selectIp(e.currentTarget.value)}>
            <option value={WORKFLOW_DEFAULT}>{WORKFLOW_DEFAULT}</option>
            {/* `value=` of the <select> must exist as an <option>; otherwise
                React renders the first option (label "default") even though
                state holds a real IP like "PL330", which makes the dropdown
                disagree with the URL/session it is supposed to mirror. */}
            {activeIp && activeIp !== WORKFLOW_DEFAULT && !ipOptions.includes(activeIp) && (
              <option key={activeIp} value={activeIp}>{activeIp}</option>
            )}
            {ipOptions.filter(ip => ip !== WORKFLOW_DEFAULT).map(ip => (
              <option key={ip} value={ip}>{ip}</option>
            ))}
          </select>
        </label>
        <button className="dir-btn"
                title="Create a new IP under the current session and switch to it (ssot-gen workflow)"
                onClick={() => beginNameEntry('ip')}>+ IP</button>
        {nameEntry && nameEntry.kind === 'ip' && (
          <form className="dir-name-entry"
                data-esc-local="true"
                title="New IP name: letters, digits, underscore, dash, or dot"
                onSubmit={(e) => { e.preventDefault(); commitNameEntry(); }}>
            <input ref={nameEntryInputRef}
                   className="dir-name-input ip"
                   aria-label="New IP name"
                   placeholder="ip_id"
                   value={nameEntry.value}
                   onChange={e => setNameEntry({ kind: 'ip', value: e.currentTarget.value })}
                   onKeyDown={e => {
                     if (e.key === 'Escape') {
                       e.preventDefault();
                       setNameEntry(null);
                     }
                   }} />
            <button type="submit" className="dir-name-action">OK</button>
            <button type="button" className="dir-name-action"
                    aria-label="Cancel new IP"
                    onClick={() => setNameEntry(null)}>×</button>
          </form>
        )}
        <label className="dir-select-wrap" title="Active workflow segment of the session namespace. Picking one activates the backend workspace and re-pins config.TODO_FILE accordingly.">
          <span>workflow</span>
          <select
            className="dir-select"
            value={currentWorkflow() || WORKFLOW_DEFAULT}
            onChange={e => selectWorkflow(e.currentTarget.value)}>
            {WORKFLOW_OPTIONS.map(wf => (
              <option key={wf} value={wf}>{wf}</option>
            ))}
          </select>
        </label>
        <button className="dir-btn"
                title={activeIp
                  ? `Download ${activeIp}/ as .zip`
                  : "Select an IP first to download just that workspace; "
                    + "leave blank for the whole project (slow)"}
                disabled={false}
                onClick={() => {
                  const sub = activeIp
                    ? `?subpath=${encodeURIComponent(activeIp)}`
                    : '';
                  window.location.href = `/api/workspace/download.zip${sub}`;
                }}>📦 .zip</button>
        <span style={{ width: 12 }} />
        <label className="dir-select-wrap" title="Change UI font family">
          <span>font</span>
          <select
            className="dir-select mini"
            value={fontMode}
            onChange={e => {
              setFontMode(e.currentTarget.value);
              try { localStorage.setItem('atlasFontModeUserSet', '1'); } catch (_) {}
            }}>
            <option value="mono">Mono</option>
            <option value="sans">Sans</option>
            <option value="system">System</option>
          </select>
        </label>
        <label className="dir-select-wrap" title="Change UI text size">
          <span>size</span>
          <select
            className="dir-select mini"
            value={fontScale}
            onChange={e => setFontScale(e.currentTarget.value)}>
            <option value="compact">S</option>
            <option value="normal">M</option>
            <option value="large">L</option>
            <option value="xl">XL</option>
          </select>
        </label>
        <label className="dir-select-wrap" title="Change virtual canvas resolution">
          <span>res</span>
          <select
            className="dir-select res"
            value={resolution}
            onChange={e => setResolution(e.currentTarget.value)}>
            {ATLAS_UI_RESOLUTION_PRESETS.map(p => (
              <option key={p.key} value={p.key}>{p.label}</option>
            ))}
          </select>
        </label>
        <span style={{ width: 12 }} />
        <button className={`dir-btn ${theme === 'dark' ? 'active' : ''}`}
                onClick={() => setTheme('dark')}>Dark</button>
        <button className={`dir-btn ${theme === 'light' ? 'active' : ''}`}
                onClick={() => setTheme('light')}>Light</button>
        <button className={`dir-btn ${uiLang === 'ko' ? 'active' : ''}`}
                title="Prefer Korean for visible agent output"
                onClick={() => chooseUiLang('ko')}>한국어</button>
        <button className={`dir-btn ${uiLang === 'en' ? 'active' : ''}`}
                title="Prefer English for visible agent output"
                onClick={() => chooseUiLang('en')}>English</button>
        <span style={{ width: 12 }} />
        <button className="dir-btn"
                title="Abort the agent's current iteration  (Esc)"
                onClick={stopAgent}>■ Stop</button>
        <button className="dir-btn"
                title="Terminate this session worker; Atlas UI server stays alive  (Ctrl/⌘+Q)"
                onClick={exitAll}>✕ Exit</button>
        <span style={{ width: 12 }} />
        {window.ATLAS_USER && (
          <button className="dir-btn"
                  title={`Logged in as ${window.ATLAS_USER.username}. Click to log out.`}
                  onClick={async () => {
                    try {
                      await fetch('/api/auth/logout', { method: 'POST' });
                    } catch (_) {}
                    try {
                      localStorage.removeItem('atlasUserSessionId');
                      localStorage.removeItem('atlasActiveSession');
                    } catch (_) {}
                    window.location.reload();
                  }}>↩ {window.ATLAS_USER.username}</button>
        )}
        <span data-row-break style={{flex:'0 0 100%',width:'100%',height:0,margin:0,padding:0,border:0}} />
        <button className={`dir-btn ${screen === 'workspace' ? 'active' : ''}`}
                title="Live agent · chat · sidebar (sim/lint/scope)"
                onClick={() => setScreen('workspace')}>⌂ Workspace</button>
        <button className={`dir-btn ${screen === 'pipeline' ? 'active' : ''}`}
                title="Live pipeline dispatcher · stage situation board"
                onClick={() => setScreen('pipeline')}>◫ Pipeline</button>
        <button className={`dir-btn ${screen === 'architect' ? 'active' : ''}`}
                title="SoC structure · per-module status grid · block diagram (rich progress view)"
                onClick={() => setScreen('architect')}>◇ Architect</button>
        <label className="dir-select-wrap run-policy">
          <span>run</span>
          <select
            className="dir-select policy"
            value={runMode}
            onChange={e => saveRunPolicy(e.currentTarget.value, execMode)}
            title="Run Mode controls evidence strictness, not IP size">
            {ATLAS_RUN_MODE_OPTIONS.map(opt => (
              <option key={opt.key} value={opt.key}>{opt.label}</option>
            ))}
          </select>
        </label>
        <label className="dir-select-wrap run-policy">
          <span>exec</span>
          <select
            className="dir-select exec"
            value={execMode}
            onChange={e => saveRunPolicy(runMode, e.currentTarget.value)}
            title="Exec Mode chooses single-worker execution or orchestrator-managed workers">
            {ATLAS_EXEC_MODE_OPTIONS.map(opt => (
              <option key={opt.key} value={opt.key}>{opt.label}</option>
            ))}
          </select>
        </label>
        <span style={{ display: 'contents' }}><PipelineRunningChip onClick={() => setScreen('pipeline')} /></span>
        <OrchInlineStatus activeIp={activeIp} />
      </div>
      <div className="app-main">
        <TitleBar ip="" screen={screen} onScreen={setScreen} />
        <div style={{ flex: 1, overflow: 'hidden' }}>
          {screen === 'pipeline' && window.AtlasPipeline
            ? <ErrorBoundary label="Pipeline"><window.AtlasPipeline /></ErrorBoundary>
            : screen === 'architect' && window.SocArchitect
              ? <ErrorBoundary label="Architect"><window.SocArchitect /></ErrorBoundary>
              : <ErrorBoundary label="Workspace"><Workspace dir={dir} uiLang={uiLang} activeNamespace={activeNamespace} /></ErrorBoundary>}
        </div>
        {/* App-level StatusBar removed — model / tokens / iter / rate /
            SAFE chips were duplicated by the right-side AgentStatusPanel,
            and the row clipped against the bottom of the 1080px canvas
            so most users never saw it anyway. */}
      </div>
    </div>
  );
};

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
