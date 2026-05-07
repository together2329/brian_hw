// shared.jsx — small reusable bits

const Pill = ({ kind = '', children }) => (
  <span className={`pill ${kind}`}>{children}</span>
);

const Kbd = ({ children }) => <span className="kbd">{children}</span>;

const StateGlyph = ({ state }) => {
  const map = {
    done:    { ch: '●', cls: 'ok' },
    active:  { ch: '◉', cls: 'acc' },
    pending: { ch: '○', cls: 'mute' },
    warn:    { ch: '◐', cls: 'warn' },
    err:     { ch: '✕', cls: 'err' },
    fail:    { ch: '✕', cls: 'err' },
  };
  const x = map[state] || map.pending;
  return <span className={x.cls}>{x.ch}</span>;
};

const StateLabel = ({ state }) => {
  const map = {
    done: 'OK', active: 'RUN', pending: '—', warn: 'WARN', err: 'ERR', fail: 'FAIL',
    complete: 'OK', sim_fail: 'FAIL', paused: 'PAUSE',
  };
  return <span className={`pill ${state === 'done' || state === 'complete' ? 'ok' : state === 'active' ? 'run' : state === 'warn' ? 'warn' : (state === 'err' || state === 'fail' || state === 'sim_fail') ? 'err' : ''}`}>{map[state] || state}</span>;
};

const StatusBar = ({ ctx, hints }) => (
  <div className="statusbar">
    <span className="sb-tag">{ctx.model}</span>
    <span>tokens <b style={{ color: 'var(--fg)' }}>{ctx.tokens.toLocaleString()}</b><span className="mute"> / {(ctx.tokensMax/1000).toFixed(0)}k</span></span>
    <span>iter <b style={{ color: 'var(--fg)' }}>{ctx.iter}</b><span className="mute"> / {ctx.iterMax}</span></span>
    <span>rate <b style={{ color: 'var(--fg)' }}>{ctx.rate}</b></span>
    <span className={ctx.safe ? 'ok' : 'err'}>{ctx.safe ? 'SAFE' : 'UNSAFE'}</span>
    <span className="sb-spacer" />
    {hints?.map((h, i) => (
      <span key={i} className="mute">
        <Kbd>{h.k}</Kbd> <span style={{ marginLeft: 4 }}>{h.l}</span>
      </span>
    ))}
  </div>
);

const TitleBar = ({ ip, screen, onScreen }) => {
  // Minimal title bar: just the live-status dot + product name.
  // workspace/ip id, cwd, screen toggle all live in .dir-switcher.
  return (
    <div className="titlebar">
      <span className="tb-dot" />
      <span><b>ATLAS</b></span>
      <span className="tb-spacer" />
    </div>
  );
};

const NavTab = ({ id, cur, onScreen, children }) => (
  <span
    onClick={() => onScreen(id)}
    style={{
      cursor: 'pointer',
      padding: '4px 10px',
      fontSize: 11,
      letterSpacing: '0.04em',
      textTransform: 'uppercase',
      color: cur === id ? 'var(--bg)' : 'var(--fg-dim)',
      background: cur === id ? 'var(--accent)' : 'transparent',
      borderRadius: 2,
    }}
  >{children}</span>
);

window.Pill = Pill;
window.Kbd = Kbd;
window.StateGlyph = StateGlyph;
window.StateLabel = StateLabel;
window.StatusBar = StatusBar;
window.TitleBar = TitleBar;
window.NavTab = NavTab;
