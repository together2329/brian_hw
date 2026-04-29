// app.jsx — top-level shell. Renders Workspace only. Owns dir + theme.
//
// Launcher and Pipeline screens were design-time mocks and have been
// removed; the live agent UI lives entirely inside Workspace.

const App = () => {
  const [dir, setDir] = React.useState('A');     // 'A' = Console, 'B' = Workbench
  const [theme, setTheme] = React.useState('dark');

  React.useEffect(() => {
    document.documentElement.setAttribute('data-dir', dir);
    document.documentElement.setAttribute('data-theme', theme);
  }, [dir, theme]);

  // Global Esc → tell the agent to abort the current iteration. We
  // skip the binding when an open ask_user card has focus, since Esc
  // there should cancel the card (handled inside that component).
  React.useEffect(() => {
    const onKey = (e) => {
      if (e.key !== 'Escape') return;
      const tag = (document.activeElement?.tagName || '').toLowerCase();
      // Don't hijack Esc when typing into the chat input — let the
      // existing input behaviour win. The UI surfaces a dedicated
      // stop button for that.
      if (tag === 'input' || tag === 'textarea') return;
      if (window.backend) window.backend.send({ type: 'stop' });
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
                title="Abort the agent's current iteration (Esc)"
                onClick={stopAgent}>■ Stop</button>
        <button className="dir-btn"
                title="Shut down the Python server and close this tab"
                onClick={exitAll}
                style={{ borderColor: '#f85149', color: '#f85149' }}>✕ Exit</button>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        <TitleBar ip="" screen="workspace" />
        <div style={{ flex: 1, overflow: 'hidden' }}>
          <Workspace dir={dir} />
        </div>
        <StatusBar ctx={window.CONTEXT} hints={hints} />
      </div>
    </div>
  );
};

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
