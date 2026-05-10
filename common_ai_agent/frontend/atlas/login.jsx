// ATLAS login screen — username+password gate that mounts before the
// workspace when /api/users/me returns 401. Registers
// window.LoginScreen so app.jsx can conditionally render it.

(function () {
  const { useState, useRef, useEffect } = React;

  function LoginScreen({ onAuth }) {
    const [mode, setMode] = useState('login');
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [busy, setBusy] = useState(false);
    const [err, setErr] = useState(null);
    const userRef = useRef(null);

    useEffect(() => { userRef.current && userRef.current.focus(); }, []);

    async function submit(e) {
      if (e) e.preventDefault();
      if (!username.trim() || !password) {
        setErr('username and password required');
        return;
      }
      setBusy(true);
      setErr(null);
      try {
        const r = await fetch(`/api/auth/${mode}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: username.trim(), password }),
        });
        if (!r.ok) {
          let detail = `HTTP ${r.status}`;
          try { detail = (await r.json()).detail || detail; } catch (_) {}
          setErr(detail);
          return;
        }
        onAuth && onAuth();
      } catch (ex) {
        setErr(String(ex && ex.message || ex));
      } finally {
        setBusy(false);
      }
    }

    const accent = mode === 'register' ? 'var(--green, #22c55e)' : 'var(--accent)';
    const otherMode = mode === 'login' ? 'register' : 'login';

    return (
      <div role="dialog" aria-modal="true" aria-label="ATLAS login" style={{
        position: 'fixed', inset: 0, zIndex: 9998,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: 'var(--bg)',
        color: 'var(--fg)',
        fontFamily: 'var(--mono)',
      }}>
        <form onSubmit={submit} style={{
          minWidth: 360, maxWidth: 420,
          padding: '24px 28px',
          background: 'var(--bg-2)',
          border: `1px solid ${accent}`,
          borderRadius: 10,
          boxShadow: '0 8px 32px color-mix(in oklch, var(--fg) 25%, transparent)',
          display: 'flex', flexDirection: 'column', gap: 14,
        }}>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 10 }}>
            <span style={{ fontSize: 18, fontWeight: 700, letterSpacing: 0.5 }}>ATLAS</span>
            <span style={{ fontSize: 12, opacity: 0.7 }}>
              {mode === 'login' ? 'Sign in' : 'Create account'}
            </span>
          </div>

          <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span style={{ fontSize: 11, opacity: 0.7 }}>Username</span>
            <input ref={userRef}
                   type="text" autoComplete="username"
                   value={username}
                   onChange={e => setUsername(e.target.value)}
                   disabled={busy}
                   style={inputStyle} />
          </label>

          <label style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <span style={{ fontSize: 11, opacity: 0.7 }}>Password</span>
            <input type="password"
                   autoComplete={mode === 'register' ? 'new-password' : 'current-password'}
                   value={password}
                   onChange={e => setPassword(e.target.value)}
                   disabled={busy}
                   style={inputStyle} />
          </label>

          {err && (
            <div role="alert" style={{
              fontSize: 12, color: 'var(--red, #ef4444)',
              background: 'color-mix(in oklch, var(--red, #ef4444) 12%, transparent)',
              border: '1px solid color-mix(in oklch, var(--red, #ef4444) 40%, transparent)',
              borderRadius: 6, padding: '6px 10px',
            }}>{err}</div>
          )}

          <button type="submit" disabled={busy} style={{
            ...btnStyle,
            background: accent, color: 'var(--bg-2)',
            opacity: busy ? 0.6 : 1, cursor: busy ? 'wait' : 'pointer',
          }}>
            {busy ? '…' : (mode === 'login' ? 'Login' : 'Register')}
          </button>

          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, opacity: 0.7 }}>
            <span>
              {mode === 'login' ? 'no account?' : 'have an account?'}
            </span>
            <button type="button" onClick={() => { setErr(null); setMode(otherMode); }}
                    disabled={busy}
                    style={{ ...linkBtnStyle }}>
              {mode === 'login' ? 'Register →' : '← Login'}
            </button>
          </div>
        </form>
      </div>
    );
  }

  const inputStyle = {
    background: 'var(--bg)',
    color: 'var(--fg)',
    border: '1px solid var(--line)',
    borderRadius: 6,
    padding: '8px 10px',
    fontFamily: 'inherit',
    fontSize: 13,
    outline: 'none',
  };
  const btnStyle = {
    border: 'none', borderRadius: 6,
    padding: '9px 14px',
    fontFamily: 'inherit', fontSize: 13, fontWeight: 600,
    letterSpacing: 0.3,
  };
  const linkBtnStyle = {
    background: 'transparent',
    color: 'var(--accent)',
    border: 'none', padding: 0, cursor: 'pointer',
    fontFamily: 'inherit', fontSize: 11, fontWeight: 600,
  };

  window.LoginScreen = LoginScreen;
})();
