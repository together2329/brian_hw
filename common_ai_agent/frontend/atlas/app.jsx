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
        <div style={{ color: 'var(--fg-mute)', fontSize: 11, marginBottom: 12, lineHeight: 1.6 }}>
          The shell stays alive — pick a different screen, or hit Reset to try mounting again.
        </div>
        <pre style={{ background: 'var(--bg-2)', border: '1px solid var(--line)',
                      padding: 12, fontSize: 11, color: 'var(--err)',
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

const App = () => {
  const [dir, setDir] = React.useState('A');     // 'A' = Console, 'B' = Workbench
  const [theme, setTheme] = React.useState('dark');
  const [uiLang, setUiLang] = React.useState(() => {
    try { return localStorage.getItem('atlasUiLang') === 'en' ? 'en' : 'ko'; }
    catch (_) { return 'ko'; }
  });
  React.useEffect(() => {
    window.ATLAS_UI_LANG = uiLang;
    try { localStorage.setItem('atlasUiLang', uiLang); } catch (_) {}
    window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'UI_LANG' }));
  }, [uiLang]);
  const TOP_WORKFLOWS = React.useMemo(() => new Set([
    'architect', 'coverage', 'fl-model-gen', 'goal-audit', 'lint',
    'mas-gen', 'rtl-gen', 'signoff', 'sim', 'sim_debug', 'ssot-gen', 'tb-gen',
  ]), []);

  const normalizeSession = React.useCallback((value) => {
    const norm = window.atlasData && window.atlasData.normalizeSessionName;
    try { return (norm && norm(value || '')) || ''; }
    catch (_) { return ''; }
  }, []);

  const splitSessionNamespace = React.useCallback((session) => {
    const sid = normalizeSession(session);
    const parts = sid.split('/').filter(Boolean);
    if (!parts.length) return { sessionId: 'default', ipId: '', workflow: '' };
    const last = parts[parts.length - 1];
    if (parts.length >= 3 && TOP_WORKFLOWS.has(last)) {
      return {
        sessionId: parts[0],
        ipId: parts[parts.length - 2],
        workflow: last,
      };
    }
    if (parts.length === 2 && TOP_WORKFLOWS.has(last)) {
      return { sessionId: 'default', ipId: parts[0], workflow: last };
    }
    if (parts.length >= 2 && parts[1] === 'default') {
      return { sessionId: parts[0], ipId: '', workflow: '' };
    }
    return { sessionId: parts[0] || 'default', ipId: '', workflow: '' };
  }, [TOP_WORKFLOWS, normalizeSession]);

  const initialSplit = splitSessionNamespace(window.ACTIVE_SESSION || localStorage.getItem('atlasActiveSession') || '');
  const [activeSessionId, setActiveSessionId] = React.useState(
    normalizeSession(window.ATLAS_USER_SESSION_ID || initialSplit.sessionId) || 'default'
  );
  const [activeNamespace, setActiveNamespace] = React.useState(
    normalizeSession(window.ACTIVE_SESSION || localStorage.getItem('atlasActiveSession'))
      || `${activeSessionId}/default`
  );
  const [activeIp, setActiveIp] = React.useState(initialSplit.ipId || '');
  const [sessionIdOptions, setSessionIdOptions] = React.useState([]);
  const [ipOptions, setIpOptions] = React.useState([]);

  const currentWorkflow = React.useCallback(() => {
    return splitSessionNamespace(window.ACTIVE_SESSION || activeNamespace).workflow
      || normalizeSession(window.CONTEXT && window.CONTEXT.workspace)
      || 'ssot-gen';
  }, [activeNamespace, normalizeSession, splitSessionNamespace]);

  const namespaceFor = React.useCallback((sessionId, ipId, workflow) => {
    const owner = normalizeSession(sessionId) || normalizeSession(window.ATLAS_USER_SESSION_ID || '') || 'default';
    const ip = normalizeSession(ipId || '');
    const wf = normalizeSession(workflow || '');
    if (ip && wf) return `${owner}/${ip}/${wf}`;
    if (ip) return `${owner}/${ip}/user`;
    if (wf) return `${owner}/soc/${wf}`;
    return `${owner}/default`;
  }, [normalizeSession]);

  const activateBackendWorkflow = React.useCallback((workflow, session) => {
    const wf = normalizeSession(workflow);
    if (!wf || wf === 'default' || wf === 'user') return;
    if (window.backend && typeof window.backend.send === 'function') {
      window.backend.send({ type: 'prompt', text: `/wf ${wf}`, session: session || window.ACTIVE_SESSION || 'default', ui_lang: window.ATLAS_UI_LANG || uiLang });
    }
  }, [normalizeSession, uiLang]);

  const activateNamespace = React.useCallback((sessionId, ipId, workflow, syncWorkflow = true) => {
    const owner = normalizeSession(sessionId) || 'default';
    const ip = normalizeSession(ipId || '');
    const wf = normalizeSession(workflow || '');
    const namespace = namespaceFor(owner, ip, wf);
    setActiveSessionId(owner);
    setActiveIp(ip);
    setActiveNamespace(namespace);
    window.ACTIVE_SESSION = namespace;
    try { localStorage.setItem('atlasActiveSession', namespace); } catch (_) {}
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
    if (syncWorkflow && wf) activateBackendWorkflow(wf, namespace);
    return namespace;
  }, [activateBackendWorkflow, namespaceFor, normalizeSession]);

  const refreshTopTargets = React.useCallback(async () => {
    const nextSessionIds = new Set(['default']);
    const currentUserSession = normalizeSession(window.ATLAS_USER_SESSION_ID || activeSessionId);
    if (currentUserSession) nextSessionIds.add(currentUserSession);
    const nextIps = new Set();
    try {
      const r = await fetch('/api/session/list', { cache: 'no-store' });
      if (r.ok) {
        const d = await r.json();
        for (const row of (Array.isArray(d.sessions) ? d.sessions : [])) {
          const parsed = splitSessionNamespace(row && row.session);
          if (parsed.sessionId) nextSessionIds.add(parsed.sessionId);
          if (parsed.ipId && parsed.ipId !== 'soc') nextIps.add(parsed.ipId);
        }
      }
    } catch (_) {}
    try {
      const r = await fetch('/api/soc', { cache: 'no-store' });
      if (r.ok) {
        const d = await r.json();
        for (const c of (Array.isArray(d.clusters) ? d.clusters : [])) {
          for (const m of (Array.isArray(c.modules) ? c.modules : [])) {
            const ip = normalizeSession(m && (m.ip_dir || m.id || m.name));
            if (ip && !ip.includes('/')) nextIps.add(ip);
          }
        }
      }
    } catch (_) {}

    const liveNamespace = normalizeSession(window.ACTIVE_SESSION || activeNamespace) || namespaceFor(currentUserSession, activeIp, currentWorkflow());
    const parsedLive = splitSessionNamespace(liveNamespace);
    if (parsedLive.sessionId) nextSessionIds.add(parsedLive.sessionId);
    if (parsedLive.ipId && parsedLive.ipId !== 'soc') nextIps.add(parsedLive.ipId);
    setSessionIdOptions(Array.from(nextSessionIds).sort((a, b) => {
      if (a === currentUserSession) return -1;
      if (b === currentUserSession) return 1;
      if (a === 'default') return -1;
      if (b === 'default') return 1;
      return a.localeCompare(b);
    }));
    setIpOptions(Array.from(nextIps).sort((a, b) => a.localeCompare(b)));
    setActiveSessionId(parsedLive.sessionId || currentUserSession || 'default');
    setActiveNamespace(liveNamespace);
    setActiveIp(parsedLive.ipId === 'soc' ? '' : (parsedLive.ipId || ''));
  }, [activeIp, activeNamespace, activeSessionId, currentWorkflow, namespaceFor, normalizeSession, splitSessionNamespace]);

  React.useEffect(() => {
    let timer = null;
    const syncCurrent = (ev) => {
      const namespace = normalizeSession((ev && ev.detail && ev.detail.session) || window.ACTIVE_SESSION || activeNamespace);
      const parsed = splitSessionNamespace(namespace);
      setActiveNamespace(namespace || namespaceFor(activeSessionId, activeIp, currentWorkflow()));
      setActiveSessionId(parsed.sessionId || activeSessionId);
      setActiveIp(parsed.ipId === 'soc' ? '' : (parsed.ipId || activeIp || ''));
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

  const selectSessionId = (rawSessionId) => {
    const owner = normalizeSession(rawSessionId) || 'default';
    const wf = activeIp ? currentWorkflow() : '';
    activateNamespace(owner, activeIp, wf, !!wf);
  };

  const selectIp = (rawIp) => {
    const ip = normalizeSession(rawIp);
    const wf = ip ? currentWorkflow() : '';
    activateNamespace(activeSessionId, ip, wf, !!wf);
  };

  const newSessionId = () => {
    const owner = `u-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
    setSessionIdOptions(prev => Array.from(new Set([owner].concat(prev || []))));
    const wf = activeIp ? currentWorkflow() : '';
    activateNamespace(owner, activeIp, wf, !!wf);
  };

  // Top-level screen — 'workspace' (live agent + chat + sidebar) or
  // 'architect' (SoC block-diagram + status grid + chat, mock data).
  const [screen, setScreen] = React.useState(() => {
    try { return localStorage.atlasScreen === 'architect' ? 'architect' : 'workspace'; }
    catch (_) { return 'workspace'; }
  });
  React.useEffect(() => {
    try { localStorage.atlasScreen = screen; } catch (_) {}
  }, [screen]);

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
    if (screen === 'architect') {
      // Disable via localStorage if user finds it disruptive.
      const optOut = (() => { try { return localStorage.getItem('atlasArchAutoSwitch') === 'off'; }
                              catch (_) { return false; } })();
      if (!optOut) window.backend.send({ type: 'prompt', text: '/workflow architect', ui_lang: window.ATLAS_UI_LANG || uiLang });
    } else if (prev === 'architect') {
      // Leaving architect → fall back to default (could be smarter and
      // restore the prior workflow, but default keeps things simple).
      const optOut = (() => { try { return localStorage.getItem('atlasArchAutoSwitch') === 'off'; }
                              catch (_) { return false; } })();
      if (!optOut) window.backend.send({ type: 'prompt', text: '/workflow default', ui_lang: window.ATLAS_UI_LANG || uiLang });
    }
  }, [screen, uiLang]);

  React.useEffect(() => {
    document.documentElement.setAttribute('data-dir', dir);
    document.documentElement.setAttribute('data-theme', theme);
  }, [dir, theme]);

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
      // Ctrl+Q (or Cmd+Q) → ask to shut down the server + close tab.
      if ((e.ctrlKey || e.metaKey) && (e.key === 'q' || e.key === 'Q')) {
        e.preventDefault();
        if (!confirm('Shut down the server and close this tab?')) return;
        if (window.backend) window.backend.send({ type: 'shutdown' });
        setTimeout(() => { try { window.close(); } catch (_) {} }, 600);
        return;
      }
      // Esc → tell the agent to abort the current iteration.
      if (e.key === 'Escape') {
        const tag = (document.activeElement?.tagName || '').toLowerCase();
        // Don't hijack Esc when an inline ask_user / slash dropdown
        // owns the input — those handle their own Esc.
        if (tag === 'input' || tag === 'textarea') return;
        if (window.backend) window.backend.send({ type: 'stop' });
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  const stopAgent = () => {
    if (window.backend) window.backend.send({ type: 'stop' });
  };
  const exitAll = () => {
    if (!confirm('Shut down the server and close this tab?')) return;
    if (window.backend) window.backend.send({ type: 'shutdown' });
    setTimeout(() => { try { window.close(); } catch (_) {} }, 600);
  };

  const hints = [
    { k: '⌘ K', l: 'cmd' },
    { k: '⌘ /', l: 'help' },
    { k: 'shift+tab', l: 'normal/plan' },
    { k: '⌘ \\', l: 'sidebar' },
  ];

  return (
    <div className="app" data-dir={dir} data-theme={theme}>
      <div className="dir-switcher">
        <label className="dir-select-wrap" title={`Select user/browser session_id. Active namespace: .session/${activeNamespace || 'default'}`}>
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
        <label className="dir-select-wrap" title="Select ip_id. The current workflow is appended to session_id/ip_id/workflow.">
          <span>ip_id</span>
          <select
            className="dir-select ip"
            value={activeIp || ''}
            onChange={e => selectIp(e.currentTarget.value)}>
            <option value="">default</option>
            {ipOptions.map(ip => <option key={ip} value={ip}>{ip}</option>)}
          </select>
        </label>
        <span style={{ width: 12 }} />
        <button className={`dir-btn ${screen === 'workspace' ? 'active' : ''}`}
                title="Live agent · chat · sidebar (sim/lint/scope)"
                onClick={() => setScreen('workspace')}>⌂ Workspace</button>
        <button className={`dir-btn ${screen === 'architect' ? 'active' : ''}`}
                title="SoC block diagram + status grid · mock data"
                onClick={() => setScreen('architect')}>◫ Architect</button>
        <span style={{ width: 12 }} />
        <button className={`dir-btn ${uiLang === 'ko' ? 'active' : ''}`}
                title="Prefer Korean for visible agent output"
                onClick={() => setUiLang('ko')}>한국어</button>
        <button className={`dir-btn ${uiLang === 'en' ? 'active' : ''}`}
                title="Prefer English for visible agent output"
                onClick={() => setUiLang('en')}>English</button>
        <span style={{ width: 12 }} />
        <button className={`dir-btn ${dir === 'A' ? 'active' : ''}`}
                onClick={() => setDir('A')}>A · Console</button>
        <button className={`dir-btn ${dir === 'B' ? 'active' : ''}`}
                onClick={() => setDir('B')}>B · Workbench</button>
        <span style={{ width: 12 }} />
        <button className={`dir-btn ${theme === 'dark' ? 'active' : ''}`}
                onClick={() => setTheme('dark')}>Dark</button>
        <button className={`dir-btn ${theme === 'light' ? 'active' : ''}`}
                onClick={() => setTheme('light')}>Light</button>
        <span style={{ width: 12 }} />
        <button className="dir-btn"
                title="Abort the agent's current iteration  (Esc)"
                onClick={stopAgent}>■ Stop · Esc</button>
        <button className="dir-btn"
                title="Shut down the Python server and close this tab  (Ctrl/⌘+Q)"
                onClick={exitAll}
                style={{ borderColor: '#f85149', color: '#f85149' }}>✕ Exit · ⌃Q</button>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        <TitleBar ip="" screen={screen} onScreen={setScreen} />
        <div style={{ flex: 1, overflow: 'hidden' }}>
          {screen === 'architect' && window.SocArchitect
            ? <ErrorBoundary label="Architect"><window.SocArchitect /></ErrorBoundary>
            : <ErrorBoundary label="Workspace"><Workspace dir={dir} uiLang={uiLang} /></ErrorBoundary>}
        </div>
        <StatusBar ctx={window.CONTEXT} hints={hints} />
      </div>
    </div>
  );
};

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
