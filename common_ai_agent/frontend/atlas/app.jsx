// app.jsx — top-level shell, routes between screens, owns dir + theme

const App = () => {
  const [dir, setDir] = React.useState('A'); // 'A' = Console, 'B' = Workbench
  const [theme, setTheme] = React.useState('dark');
  const [screen, setScreen] = React.useState('workspace'); // launcher | pipeline | workspace
  const [ip, setIp] = React.useState('spi_master');
  const [stage, setStage] = React.useState('ssot'); // ssot | rtl_gen | tb_gen

  // wire body data attrs
  React.useEffect(() => {
    document.documentElement.setAttribute('data-dir', dir);
    document.documentElement.setAttribute('data-theme', theme);
  }, [dir, theme]);

  // Listen for external stage changes (from launcher)
  React.useEffect(() => {
    const h = () => { if (window.__qaStage) setStage(window.__qaStage); };
    window.addEventListener('qa-stage-change', h);
    return () => window.removeEventListener('qa-stage-change', h);
  }, []);

  const hints = [
    { k: '⌘ K', l: 'cmd' },
    { k: '⌘ /', l: 'help' },
    { k: 'shift+tab', l: intent_for_hints() },
    { k: '⌘ \\', l: 'sidebar' },
  ];
  function intent_for_hints() { return 'normal/plan'; }

  return (
    <div className="app" data-dir={dir} data-theme={theme}>
      {/* top-right switcher */}
      <div className="dir-switcher">
        <button className={`dir-btn ${dir === 'A' ? 'active' : ''}`} onClick={() => setDir('A')}>A · Console</button>
        <button className={`dir-btn ${dir === 'B' ? 'active' : ''}`} onClick={() => setDir('B')}>B · Workbench</button>
        <span style={{ width: 12 }} />
        <button className={`dir-btn ${theme === 'dark' ? 'active' : ''}`} onClick={() => setTheme('dark')}>Dark</button>
        <button className={`dir-btn ${theme === 'light' ? 'active' : ''}`} onClick={() => setTheme('light')}>Light</button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        <TitleBar ip={ip} screen={screen} onScreen={setScreen} />
        <div style={{ flex: 1, overflow: 'hidden' }}>
          {screen === 'launcher' && <Launcher dir={dir} onScreen={setScreen} onPickIp={setIp} />}
          {screen === 'pipeline' && <Pipeline dir={dir} onScreen={setScreen} ip={ip} />}
          {screen === 'workspace' && <Workspace dir={dir} onScreen={setScreen} />}
        </div>
        <StatusBar ctx={window.CONTEXT} hints={hints} />
      </div>
    </div>
  );
};

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
