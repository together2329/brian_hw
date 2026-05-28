// shared.tsx — small reusable bits
//
// TypeScript migration of shared.jsx (in-browser-babel + ambient global React
// + window.* glue) to a typed ES module. Behavior-identical translation:
//   - Proper ES module JSX (automatic runtime) instead of ambient `React`.
//   - Real typed exports for each component — consumers will `import` these
//     once they migrate.
// Transitional: still bridges to `window.*` at the bottom so not-yet-migrated
// .jsx files keep resolving `window.Pill` / `window.Kbd` / etc.
import { type ReactNode } from 'react';

export interface PillProps {
  kind?: string;
  children?: ReactNode;
}

export const Pill = ({ kind = '', children }: PillProps) => (
  <span className={`pill ${kind}`}>{children}</span>
);

export interface KbdProps {
  children?: ReactNode;
}

export const Kbd = ({ children }: KbdProps) => <span className="kbd">{children}</span>;

export interface StateGlyphProps {
  state?: string;
}

export const StateGlyph = ({ state }: StateGlyphProps) => {
  const map: Record<string, { ch: string; cls: string }> = {
    done:    { ch: '●', cls: 'ok' },
    active:  { ch: '◉', cls: 'acc' },
    pending: { ch: '○', cls: 'mute' },
    warn:    { ch: '◐', cls: 'warn' },
    err:     { ch: '✕', cls: 'err' },
    fail:    { ch: '✕', cls: 'err' },
  };
  const x = map[state as string] || map.pending;
  return <span className={x.cls}>{x.ch}</span>;
};

export interface StateLabelProps {
  state?: string;
}

export const StateLabel = ({ state }: StateLabelProps) => {
  const map: Record<string, string> = {
    done: 'OK', active: 'RUN', pending: '—', warn: 'WARN', err: 'ERR', fail: 'FAIL',
    complete: 'OK', sim_fail: 'FAIL', paused: 'PAUSE',
  };
  return <span className={`pill ${state === 'done' || state === 'complete' ? 'ok' : state === 'active' ? 'run' : state === 'warn' ? 'warn' : (state === 'err' || state === 'fail' || state === 'sim_fail') ? 'err' : ''}`}>{map[state as string] || state}</span>;
};

export interface StatusBarCtx {
  model: ReactNode;
  tokens: number;
  tokensMax: number;
  iter: ReactNode;
  iterMax: ReactNode;
  rate: ReactNode;
  safe: boolean;
}

export interface StatusBarHint {
  k: ReactNode;
  l: ReactNode;
}

export interface StatusBarProps {
  ctx: StatusBarCtx;
  hints?: StatusBarHint[];
}

export const StatusBar = ({ ctx, hints }: StatusBarProps) => (
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

export interface TitleBarProps {
  ip?: unknown;
  screen?: unknown;
  onScreen?: unknown;
}

export const TitleBar = ({ ip, screen, onScreen }: TitleBarProps) => {
  // Empty bar — kept as a thin top spacer. session_id / ip_id /
  // workflow / screen toggles all live in .dir-switcher above; the
  // green dot + ATLAS label was redundant and crowded the chip row
  // that floats over this bar.
  return <div className="titlebar"><span className="tb-spacer" /></div>;
};

export interface NavTabProps {
  id: string;
  cur?: string;
  onScreen: (id: string) => void;
  children?: ReactNode;
}

export const NavTab = ({ id, cur, onScreen, children }: NavTabProps) => (
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

// ── Transitional bridge: register on window for not-yet-migrated .jsx ──
// Remove each line once all consumers import the symbol directly.
window.Pill = Pill;
window.Kbd = Kbd;
window.StateGlyph = StateGlyph;
window.StateLabel = StateLabel;
window.StatusBar = StatusBar;
window.TitleBar = TitleBar;
window.NavTab = NavTab;
