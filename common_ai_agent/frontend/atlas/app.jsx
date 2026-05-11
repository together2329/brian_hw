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
  const [dir, setDir] = React.useState('B');     // 'B' = Workbench (default)
  const [theme, setTheme] = React.useState('light');
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
    'mas-gen', 'pnr', 'rtl-gen', 'signoff', 'sim', 'sim_debug',
    'ssot-gen', 'sta', 'syn', 'tb-gen',
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
  // Inline notice for + IP / + SESSION errors. window.alert/prompt
  // wedges the cmux WKWebView (native dialogs hang every browser RPC),
  // so route validation feedback through a transient banner instead.
  const [topNotice, setTopNotice] = React.useState('');
  const showNotice = React.useCallback((msg) => {
    setTopNotice(String(msg || ''));
    setTimeout(() => setTopNotice(''), 5000);
  }, []);

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
      subs.push(window.backend.subscribe('workspace_changed', () => {
        setWfSwitching(null);
      }));
    } catch (_) {}
    return () => { subs.forEach(u => { try { u && u(); } catch (_) {} }); };
  }, []);

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
          const currentNs = normalizeSession(window.ACTIVE_SESSION || localStorage.getItem('atlasActiveSession') || '');
          const currentOwner = (currentNs.split('/').filter(Boolean)[0] || '');
          localStorage.setItem('atlasUserSessionId', username);
          if (!currentNs || currentNs === 'default' || (currentOwner && currentOwner !== username)) {
            const nextNs = `${username}/default`;
            window.ACTIVE_SESSION = nextNs;
            localStorage.setItem('atlasActiveSession', nextNs);
            setActiveSessionId(username);
            setActiveNamespace(nextNs);
            setActiveIp('');
            const url = new URL(window.location.href);
            url.searchParams.set('session', nextNs);
            url.searchParams.set('session_id', username);
            url.searchParams.delete('ip');
            url.searchParams.delete('ip_id');
            url.searchParams.delete('workflow');
            url.searchParams.delete('wf');
            window.history.replaceState(null, '', url);
            if (window.backend && typeof window.backend.disconnect === 'function' && typeof window.backend.connect === 'function') {
              window.backend.disconnect();
              setTimeout(() => window.backend.connect(username), 0);
            }
          }
          const activeForBackend = normalizeSession(window.ACTIVE_SESSION || localStorage.getItem('atlasActiveSession') || `${username}/default`) || `${username}/default`;
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
    const mark = (k, v) => setBootSteps(s => (s[k] === v ? s : { ...s, [k]: v }));
    const runProbes = () => {
      // Reset HTTP-side legs to pending so the user sees the rerun.
      setBootSteps(s => ({
        ...s,
        health: 'pending', sessions: 'pending', llm: 'pending',
      }));
      setBootHidden(false);
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
  const bootDone = Object.values(bootSteps).every(v => v === 'done');
  const bootFailed = Object.values(bootSteps).some(v => v === 'fail');
  React.useEffect(() => {
    if (bootDone) {
      const t = setTimeout(() => setBootHidden(true), 1200);
      return () => clearTimeout(t);
    }
  }, [bootDone]);

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

  const activateNamespace = React.useCallback((sessionId, ipId, workflow, syncWorkflow = true) => {
    const owner = normalizeSession(sessionId) || 'default';
    const ip = normalizeSession(ipId || '');
    const wf = normalizeSession(workflow || '');
    const namespace = namespaceFor(owner, ip, wf);
    // Stop the running agent BEFORE flipping the workspace whenever any
    // of the triple changes. Without this, in-flight tool calls keep
    // running against the old IP/workflow even after the UI has pivoted,
    // which produces "wrote to wrong workspace" surprises that are hard
    // to back out of. Fire-and-forget — `/api/control/stop` is idempotent
    // and the activate POST below doesn't wait on it. Only triggers on
    // an actual change (no-op activates from re-renders won't bother
    // the bridge).
    const prev = window.ACTIVE_SESSION || '';
    if (prev && prev !== namespace) {
      try {
        fetch('/api/control/stop', { method: 'POST' }).catch(() => {});
      } catch (_) {}
    }
    syncNamespaceUrl(namespace, owner, ip, wf);
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
    // Push the canonical triple to the backend so its env vars
    // (ATLAS_ACTIVE_SESSION / ATLAS_ACTIVE_IP / ATLAS_DEFAULT_*) match
    // what the frontend is showing. Without this round-trip, a fresh
    // restart would inherit only the CLI defaults and the chat / QA /
    // preview panes would silently target the wrong IP.
    // Awaiting the activate POST before firing /wf eliminates the race
    // that previously let an in-flight react_loop keep reading the OLD
    // IP's files (the activate handler halts the agent + drains the
    // inbox on a triple change, so by the time /wf lands the bridge
    // is quiescent and the env vars already point at the new IP).
    const _activateAndDispatch = async () => {
      try {
        await fetch('/api/session/activate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_id: owner || 'default',
            ip: ip || 'default',
            workflow: wf || 'default',
          }),
        });
      } catch (_) {}
      // No `&& wf` guard — picking 'default' from the workflow
      // dropdown sends an empty wf string, but activateBackendWorkflow
      // resolves it to /wf default so the agent's workspace actually
      // flips. Skipping here would leave the backend pinned.
      if (syncWorkflow) activateBackendWorkflow(wf, namespace);
    };
    _activateAndDispatch();
    return namespace;
  }, [activateBackendWorkflow, namespaceFor, normalizeSession, syncNamespaceUrl]);

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
    const sortedIps = Array.from(nextIps).sort((a, b) => a.localeCompare(b));
    setIpOptions(sortedIps);
    // Expose for inline-code-chip click validation in workspace.jsx so
    // only IPs that actually exist on disk become clickable.
    window.IP_OPTIONS = sortedIps;
    setActiveSessionId(parsedLive.sessionId || currentUserSession || 'default');
    setActiveNamespace(liveNamespace);
    setActiveIp(parsedLive.ipId === 'soc' ? '' : (parsedLive.ipId || ''));
  }, [activeIp, activeNamespace, activeSessionId, currentWorkflow, namespaceFor, normalizeSession, splitSessionNamespace]);

  React.useEffect(() => {
    let timer = null;
    const syncCurrent = (ev) => {
      const ctx = window.CONTEXT || {};
      const ctxSession = normalizeSession(ctx.active_session || '');
      // refreshHealth periodic poll → backend is the ground truth.
      // Snap UI dropdowns to whatever the backend reports as the active
      // (sid, ip, wf), except when backend is still at the boot
      // "default/default/default" placeholder — let the user's
      // localStorage / URL hint own that brief window.
      const isHealthTick = ev && ev.type === 'atlas-data-changed' && ev.detail === 'CONTEXT';
      let namespace;
      if (isHealthTick && ctxSession && ctxSession !== 'default/default/default') {
        namespace = ctxSession;
        if (namespace !== window.ACTIVE_SESSION) {
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
      setActiveNamespace(namespace || namespaceFor(activeSessionId, activeIp, currentWorkflow()));
      setActiveSessionId(parsed.sessionId || activeSessionId);
      setActiveIp(parsed.ipId === 'soc' ? '' : (parsed.ipId || activeIp || ''));
      // Push the canonical triple into the URL so the address bar
      // never silently disagrees with what the server reports.
      // Without this, reloading after a triple flip kept the OLD
      // ?ip=…&workflow=… params visible even though dropdowns / file
      // tree had pivoted to the new triple.
      try {
        const owner = parsed.sessionId || activeSessionId || 'default';
        const ipSeg = parsed.ipId === 'soc' ? '' : (parsed.ipId || '');
        const wfSeg = parsed.workflow || '';
        if (namespace) syncNamespaceUrl(namespace, owner, ipSeg, wfSeg);
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
    const parsed = splitSessionNamespace(window.ACTIVE_SESSION || activeNamespace || '');
    if (!parsed.ipId && !parsed.workflow) return;
    activateNamespace(parsed.sessionId || activeSessionId || 'default', parsed.ipId || '', parsed.workflow || '', !!parsed.workflow);
    // Run once on mount: this is the URL/localStorage → backend handshake.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  React.useEffect(() => {
    const onSwitch = (ev) => {
      const sessionId = ev?.detail?.sessionId;
      const namespace = ev?.detail?.namespace;
      if (!sessionId) return;
      const parsed = splitSessionNamespace(namespace || window.ACTIVE_SESSION || '');
      const owner = normalizeSession(parsed.sessionId || sessionId);
      setActiveSessionId(owner);
      setActiveNamespace(namespace || window.ACTIVE_SESSION || namespaceFor(owner, activeIp, currentWorkflow()));
      setActiveIp(parsed.ipId === 'soc' ? '' : (parsed.ipId || activeIp || ''));
      syncNamespaceUrl(namespace || window.ACTIVE_SESSION || '', owner, parsed.ipId === 'soc' ? '' : (parsed.ipId || ''), parsed.workflow || '');
      refreshTopTargets();
    };
    window.addEventListener('atlas-session-switched', onSwitch);
    return () => window.removeEventListener('atlas-session-switched', onSwitch);
  }, [activeIp, currentWorkflow, namespaceFor, normalizeSession, refreshTopTargets, splitSessionNamespace, syncNamespaceUrl]);

  const selectSessionId = (rawSessionId) => {
    const owner = normalizeSession(rawSessionId) || 'default';
    const wf = activeIp ? currentWorkflow() : '';
    activateNamespace(owner, activeIp, wf, !!wf);
  };

  const selectIp = (rawIp) => {
    const ip = normalizeSession(rawIp);
    // Picking an IP also re-anchors the workflow: ssot-gen by default
    // (the natural starting workflow for any IP), or whatever the user
    // already had if it's a valid workflow. Clearing the IP also
    // clears the workflow.
    let wf = '';
    if (ip) {
      const cur = currentWorkflow();
      wf = cur && TOP_WORKFLOWS.has(cur) ? cur : 'ssot-gen';
    }
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
      showNotice('Invalid session_id. Use only [A-Za-z0-9_.-].');
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
  const createIp = async () => {
    const raw = window.prompt(
      'New IP name (letters/digits/_-, e.g. axi_dma):',
      ''
    );
    if (!raw) return;
    const ip = normalizeSession(raw);
    if (!ip) {
      showNotice('Invalid IP name. Use only [A-Za-z0-9_.-].');
      return;
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
          return;
        }
      }
    } catch (_) {}
    // Actually create <PROJECT_ROOT>/<ip>/ on disk so the scope panel
    // shows an empty folder for the new IP instead of stale tree
    // contents from the previously-active IP. The endpoint refuses to
    // clobber an existing directory.
    try {
      const r = await fetch('/api/ip/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: ip }),
      });
      if (!r.ok) {
        const d = await r.json().catch(() => ({}));
        if (r.status === 409) {
          showNotice(`IP folder "${ip}/" already exists on disk.`);
          return;
        }
        showNotice(`Failed to create IP folder: ${d.error || r.status}`);
        return;
      }
    } catch (e) {
      showNotice(`Failed to create IP folder: ${e}`);
      return;
    }
    const me = activeSessionId
      || normalizeSession(window.ATLAS_USER_SESSION_ID || '')
      || 'default';
    const namespace = `${me}/${ip}/ssot-gen`;
    // Local state first so the dropdown and scope reflect the new IP
    // immediately while the WS round-trips run.
    setIpOptions(prev => Array.from(new Set([ip].concat(prev || []))));
    setActiveIp(ip);
    setActiveSessionId(me);
    setActiveNamespace(namespace);
    window.ACTIVE_SESSION = namespace;
    try { localStorage.setItem('atlasActiveSession', namespace); } catch (_) {}
    syncNamespaceUrl(namespace, me, ip, 'ssot-gen');
    if (window.atlasData && typeof window.atlasData.setUserSessionId === 'function') {
      window.atlasData.setUserSessionId(me);
    }
    if (window.atlasData && typeof window.atlasData.setScopePath === 'function') {
      window.atlasData.setScopePath(ip);
    }
    // Explicit await chain so /wf lands before /new-ip on the backend.
    // The previous code relied on activateNamespace which fires /wf
    // AFTER an awaited /api/session/activate POST, but /new-ip ran
    // immediately after that call returned and so reached the WS
    // ~700 ms before /wf — backend processed /new-ip in the wrong
    // workflow.
    try {
      await fetch('/api/session/activate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: me, ip, workflow: 'ssot-gen' }),
      });
    } catch (_) {}
    if (window.backend && typeof window.backend.send === 'function') {
      try {
        window.backend.send({
          type: 'prompt', text: '/wf ssot-gen', session: namespace,
          ui_lang: window.ATLAS_UI_LANG || uiLang,
        });
        window.backend.send({
          type: 'prompt', text: `/new-ip ${ip}`, session: namespace,
          ui_lang: window.ATLAS_UI_LANG || uiLang,
        });
      } catch (_) {}
    }
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
      // Ctrl+Q (or Cmd+Q) → ask to shut down the server + close tab.
      if ((e.ctrlKey || e.metaKey) && (e.key === 'q' || e.key === 'Q')) {
        e.preventDefault();
        if (!confirm('Shut down the server and close this tab?')) return;
        sendControl('shutdown');
        setTimeout(() => { try { window.close(); } catch (_) {} }, 600);
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
    setTimeout(() => { try { window.close(); } catch (_) {} }, 600);
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
          padding: '6px 12px', fontSize: 12, fontFamily: 'var(--mono)',
          background: 'color-mix(in oklch, var(--accent) 12%, transparent)',
          color: 'var(--accent)', borderBottom: '1px solid var(--accent)',
          display: 'flex', alignItems: 'center', gap: 10,
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
            Switching workspace <code>{wfSwitching.from || '∅'}</code> → <code>{wfSwitching.to}</code>
            {wfSwitching.ip ? <> · ip=<code>{wfSwitching.ip}</code></> : null}
            <span style={{ marginLeft: 8, opacity: 0.7 }}>(reloading prompts / skills / hooks…)</span>
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
          border: '1px solid ' + (bootFailed ? 'var(--red, #ef4444)' : (bootDone ? 'var(--green, #22c55e)' : 'var(--accent)')),
          borderRadius: 8,
          boxShadow: '0 8px 32px color-mix(in oklch, var(--fg) 25%, transparent)',
          color: 'var(--fg)',
          display: 'flex', flexDirection: 'column', gap: 12,
          transition: 'opacity 250ms ease',
          opacity: bootDone ? 0.94 : 1,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            {!bootDone && !bootFailed && (
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
            {bootDone && <span style={{ fontSize: 20, fontWeight: 700 }}>✓</span>}
            {bootFailed && <span style={{ fontSize: 20, fontWeight: 700 }}>⚠</span>}
            <span style={{ fontWeight: 600 }}>
              {bootDone ? 'Backend connected'
                : bootFailed ? 'Connection problem'
                : 'Connecting to backend…'}
            </span>
            <span style={{ flex: 1 }} />
            {bootDone && (
              <button onClick={() => setBootHidden(true)}
                      style={{ background: 'transparent', border: 'none',
                               color: 'currentColor', cursor: 'pointer',
                               fontSize: 18, lineHeight: 1, padding: 0 }}
                      title="dismiss">×</button>
            )}
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
        <label className="dir-select-wrap" title="Select ip_id. The current workflow is appended to session_id/ip_id/workflow.">
          <span>ip_id</span>
          <select
            className="dir-select ip"
            value={activeIp || ''}
            onChange={e => selectIp(e.currentTarget.value)}>
            <option value="">None</option>
            {/* `value=` of the <select> must exist as an <option>; otherwise
                React renders the first option (label "default") even though
                state holds a real IP like "PL330", which makes the dropdown
                disagree with the URL/session it is supposed to mirror. */}
            {activeIp && !ipOptions.includes(activeIp) && (
              <option key={activeIp} value={activeIp}>{activeIp}</option>
            )}
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
