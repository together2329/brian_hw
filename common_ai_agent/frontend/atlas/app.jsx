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
