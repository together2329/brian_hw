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
      return ['mono', 'sans', 'system'].includes(saved) ? saved : 'mono';
    } catch (_) { return 'mono'; }
  });
  const [fontScale, setFontScale] = React.useState(() => {
    try {
      const saved = localStorage.getItem('atlasFontScale');
      return ['compact', 'normal', 'large', 'xl'].includes(saved) ? saved : 'large';
    } catch (_) { return 'large'; }
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
  const chooseUiLang = React.useCallback((next) => {
    setUiLang(next === 'ko' ? 'ko' : 'en');
    try { localStorage.setItem('atlasUiLangUserSet', '1'); } catch (_) {}
  }, []);
  const TOP_WORKFLOWS = React.useMemo(() => new Set([
    'architect', 'coverage', 'fl-model-gen', 'goal-audit', 'lint',
    'mas-gen', 'rtl-gen', 'signoff', 'sim', 'sim_debug', 'ssot-gen', 'tb-gen',
  ]), []);

  const normalizeSession = React.useCallback((value) => {
    const norm = (window.atlasData && window.atlasData.normalizeSessionName) || window.normalizeAtlasSessionName;
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
    // Picking an IP without an explicit workflow → use 'default' as
    // the workflow segment so the namespace stays unambiguous and the
    // splitSessionNamespace round-trip preserves the IP.
    if (ip) return `${owner}/${ip}/default`;
    // Workflow without IP — drop the legacy `${owner}/soc/${wf}`
    // synthesis. It used to plant a `.session/<owner>/soc/<wf>/`
    // tree for plain ssot-gen / rtl-gen runs that aren't SoC-level
    // at all, confusing operators. Use `${owner}/${wf}` so the
    // workflow-only case lands at `.session/<owner>/<wf>/`. SoC
    // Architect runs explicitly set ipId='soc' and keep the
    // legacy three-segment shape via the (ip && wf) branch above.
    if (wf) return `${owner}/${wf}`;
    return `${owner}/default`;
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
    // No `&& wf` guard — picking 'default' from the workflow
    // dropdown sends an empty wf string, but activateBackendWorkflow
    // resolves it to /wf default so the agent's workspace actually
    // flips. Skipping here would leave the backend pinned.
    if (syncWorkflow) activateBackendWorkflow(wf, namespace);
    return namespace;
  }, [activateBackendWorkflow, namespaceFor, normalizeSession]);

  // Synthetic / reserved namespace segments that should never show
  // up in the ip_id dropdown. 'soc' is the SoC architect placeholder,
  // 'default' is the no-IP fallback, 'user' is the legacy ip-less
  // sentinel (still in the wild on disk from older runs), and any
  // workflow name (ssot-gen, rtl-gen, …) that slipped into the IP
  // slot from `${owner}/${wf}` namespaces gets filtered too.
  const RESERVED_IP_NAMES = React.useMemo(
    () => new Set(['soc', 'default', 'user', ...TOP_WORKFLOWS]),
    [TOP_WORKFLOWS]
  );

  const refreshTopTargets = React.useCallback(async () => {
    const nextSessionIds = new Set(['default']);
    const currentUserSession = normalizeSession(window.ATLAS_USER_SESSION_ID || activeSessionId);
    if (currentUserSession) nextSessionIds.add(currentUserSession);
    const nextIps = new Set();
    const acceptIp = (id) => id && !RESERVED_IP_NAMES.has(id);
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
          if (parsed.sessionId !== currentUserSession && parsed.sessionId !== 'default') continue;
          if (acceptIp(parsed.ipId)) nextIps.add(parsed.ipId);
        }
      }
    } catch (_) {}
    // Don't seed ipOptions from /api/soc anymore. /api/soc rglobs the
    // whole project root for `*.ssot.yaml` (Tier 2 fallback) and walks
    // `.session/**/ssot-gen/state.json`, so leftover scaffold dirs like
    // `i2c/yaml/i2c.ssot.yaml` or legacy bare `.session/i2c/` show up
    // forever — even after the user "starts from scratch". The
    // dropdown is for "IPs the current backend's session tree knows
    // about" — let /api/session/list (per-owner namespace walk) be the
    // single source of truth, and let createIp() seed locally for
    // brand-new IPs that don't have a .session/<owner>/<ip>/ tree yet.

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

  // Switch workflow segment of the active namespace. Empty string falls
  // back to 'default' (no /wf dispatch). Anything in TOP_WORKFLOWS fires
  // /wf to swap the agent's workspace just like clicking a chip in the
  // Workspace screen — keeps the dir-switcher source-of-truth.
  const selectWorkflow = (rawWf) => {
    const wf = normalizeSession(rawWf);
    // Always sync to the backend — picking 'default' (empty input)
    // must still dispatch /wf default so the agent's TODO_FILE,
    // system prompt and todo template flip back to the plain
    // workspace. Previously syncWorkflow=!!wf made the call a no-op
    // for default and the backend stayed on the old workflow.
    activateNamespace(activeSessionId, activeIp, wf, true);
  };

  const newSessionId = () => {
    const raw = window.prompt(
      'New session_id (letters/digits/_-, e.g. brian or u-team-a):',
      ''
    );
    if (!raw) return;
    const owner = normalizeSession(raw);
    if (!owner) {
      window.alert('Invalid session_id. Use only [A-Za-z0-9_.-].');
      return;
    }
    setSessionIdOptions(prev => Array.from(new Set([owner].concat(prev || []))));
    const wf = activeIp ? currentWorkflow() : '';
    activateNamespace(owner, activeIp, wf, !!wf);
  };

  // Create a brand-new IP under the current user_session and switch
  // to it. Mirrors the simplicity of `+ Session` but takes a name
  // because IPs are named identifiers rather than disposable scratch
  // owners. The actual on-disk .session/<sid>/<ip>/<wf>/ tree gets
  // created by _setup_session on the next /wf or agent run.
  const createIp = () => {
    const raw = window.prompt(
      'New IP name (letters/digits/_-, e.g. axi_dma):',
      ''
    );
    if (!raw) return;
    const ip = normalizeSession(raw);
    if (!ip) {
      window.alert('Invalid IP name. Use only [A-Za-z0-9_.-].');
      return;
    }
    setIpOptions(prev => Array.from(new Set([ip].concat(prev || []))));
    const me = activeSessionId
      || normalizeSession(window.ATLAS_USER_SESSION_ID || '')
      || 'default';
    activateNamespace(me, ip, 'ssot-gen', true);
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
    document.documentElement.setAttribute('data-font', fontMode);
    document.documentElement.setAttribute('data-font-scale', fontScale);
  }, [dir, theme, fontMode, fontScale]);

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
        <button className="dir-btn"
                title="Create a new IP under the current session and switch to it (ssot-gen workflow)"
                onClick={createIp}>+ IP</button>
        <label className="dir-select-wrap" title="Active workflow segment of the session namespace. Picking one fires /wf and re-pins config.TODO_FILE accordingly.">
          <span>workflow</span>
          <select
            className="dir-select"
            value={currentWorkflow() || ''}
            onChange={e => selectWorkflow(e.currentTarget.value)}>
            <option value="">default</option>
            {Array.from(TOP_WORKFLOWS).sort().map(wf => (
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
        <button className={`dir-btn ${screen === 'workspace' ? 'active' : ''}`}
                title="Live agent · chat · sidebar (sim/lint/scope)"
                onClick={() => setScreen('workspace')}>⌂ Workspace</button>
        <button className={`dir-btn ${screen === 'architect' ? 'active' : ''}`}
                title="SoC block diagram + status grid · mock data"
                onClick={() => setScreen('architect')}>◫ Architect</button>
        <span style={{ width: 12 }} />
        <button className={`dir-btn ${uiLang === 'ko' ? 'active' : ''}`}
                title="Prefer Korean for visible agent output"
                onClick={() => chooseUiLang('ko')}>한국어</button>
        <button className={`dir-btn ${uiLang === 'en' ? 'active' : ''}`}
                title="Prefer English for visible agent output"
                onClick={() => chooseUiLang('en')}>English</button>
        <label className="dir-select-wrap" title="Change UI font family">
          <span>font</span>
          <select
            className="dir-select mini"
            value={fontMode}
            onChange={e => setFontMode(e.currentTarget.value)}>
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
                onClick={stopAgent}>■ Stop</button>
        <button className="dir-btn"
                title="Shut down the Python server and close this tab  (Ctrl/⌘+Q)"
                onClick={exitAll}>✕ Exit</button>
      </div>
      <div className="app-main">
        <TitleBar ip="" screen={screen} onScreen={setScreen} />
        <div style={{ flex: 1, overflow: 'hidden' }}>
          {screen === 'architect' && window.SocArchitect
            ? <ErrorBoundary label="Architect"><window.SocArchitect /></ErrorBoundary>
            : <ErrorBoundary label="Workspace"><Workspace dir={dir} uiLang={uiLang} /></ErrorBoundary>}
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
