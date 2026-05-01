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
      if (!optOut) window.backend.send({ type: 'prompt', text: '/workflow architect' });
    } else if (prev === 'architect') {
      // Leaving architect → fall back to default (could be smarter and
      // restore the prior workflow, but default keeps things simple).
      const optOut = (() => { try { return localStorage.getItem('atlasArchAutoSwitch') === 'off'; }
                              catch (_) { return false; } })();
      if (!optOut) window.backend.send({ type: 'prompt', text: '/workflow default' });
    }
  }, [screen]);

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
        <button className={`dir-btn ${screen === 'workspace' ? 'active' : ''}`}
                title="Live agent · chat · sidebar (sim/lint/scope)"
                onClick={() => setScreen('workspace')}>⌂ Workspace</button>
        <button className={`dir-btn ${screen === 'architect' ? 'active' : ''}`}
                title="SoC block diagram + status grid · mock data"
                onClick={() => setScreen('architect')}>◫ Architect</button>
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
        <TitleBar ip="" screen={screen} />
        <div style={{ flex: 1, overflow: 'hidden' }}>
          {screen === 'architect' && window.SocArchitect
            ? <ErrorBoundary label="Architect"><window.SocArchitect /></ErrorBoundary>
            : <ErrorBoundary label="Workspace"><Workspace dir={dir} /></ErrorBoundary>}
        </div>
        <StatusBar ctx={window.CONTEXT} hints={hints} />
      </div>
    </div>
  );
};

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
