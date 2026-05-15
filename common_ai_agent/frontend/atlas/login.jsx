// ATLAS login screen — username+password gate that mounts before the
// workspace when /api/users/me returns 401. Registers
// window.LoginScreen so app.jsx can conditionally render it.

(function () {
  const { useState, useRef, useEffect } = React;

  const modeCopy = {
    login: { subtitle: 'Sign in', action: 'Login' },
    register: { subtitle: 'Create account', action: 'Register' },
    'find-id': { subtitle: 'Find ID', action: 'Find ID' },
    'reset-request': { subtitle: 'Reset password', action: 'Send reset' },
    'reset-confirm': { subtitle: 'Set new password', action: 'Update password' },
  };

  function LoginScreen({ onAuth }) {
    const [mode, setMode] = useState('login');
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [identifier, setIdentifier] = useState('');
    const [password, setPassword] = useState('');
    const [resetToken, setResetToken] = useState('');
    const [authStatus, setAuthStatus] = useState({
      recovery_enabled: false,
      email_required: false,
    });
    const [busy, setBusy] = useState(false);
    const [err, setErr] = useState(null);
    const [notice, setNotice] = useState(null);
    const userRef = useRef(null);

    useEffect(() => {
      userRef.current && userRef.current.focus();
      let alive = true;
      fetch('/api/auth/status')
        .then((r) => (r.ok ? r.json() : null))
        .then((data) => {
          if (alive && data) setAuthStatus(data);
        })
        .catch(() => {});
      try {
        const params = new URLSearchParams(window.location.search || '');
        const token = params.get('reset_token') || params.get('token');
        if (token) {
          setResetToken(token);
          setMode('reset-confirm');
        }
      } catch (_) {}
      return () => { alive = false; };
    }, []);

    function switchMode(nextMode) {
      setMode(nextMode);
      setErr(null);
      setNotice(null);
    }

    async function readDetail(response) {
      let detail = `HTTP ${response.status}`;
      try {
        const body = await response.json();
        detail = body.detail || body.error || detail;
      } catch (_) {}
      return detail;
    }

    async function postJSON(path, payload) {
      const r = await fetch(path, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!r.ok) throw new Error(await readDetail(r));
      return r.json();
    }

    async function submit(e) {
      if (e) e.preventDefault();
      setBusy(true);
      setErr(null);
      setNotice(null);
      try {
        if (mode === 'login' || mode === 'register') {
          if (!username.trim() || !password) {
            throw new Error('username and password required');
          }
          if (mode === 'register' && authStatus.email_required && !email.trim()) {
            throw new Error('email required');
          }
          const payload = {
            username: username.trim(),
            password,
            display_name: username.trim(),
          };
          if (mode === 'register' && email.trim()) payload.email = email.trim();
          await postJSON(`/api/auth/${mode}`, payload);
          onAuth && onAuth();
          return;
        }

        if (mode === 'find-id') {
          if (!email.trim()) throw new Error('email required');
          const data = await postJSON('/api/auth/recover/id', { email: email.trim() });
          if (Array.isArray(data.usernames) && data.usernames.length) {
            setNotice(`User ID: ${data.usernames.join(', ')}`);
          } else {
            setNotice(data.email_sent ? 'Check your email for the user ID.' : 'If the email exists, the ID recovery request was prepared.');
          }
          return;
        }

        if (mode === 'reset-request') {
          if (!identifier.trim()) throw new Error('username or email required');
          const data = await postJSON('/api/auth/recover/password', { identifier: identifier.trim() });
          if (data.reset_token) {
            setResetToken(data.reset_token);
            switchMode('reset-confirm');
            setNotice('Debug reset token loaded. Set a new password.');
          } else {
            setNotice(data.email_sent ? 'Check your email for the reset link.' : 'If the account exists, the password reset request was prepared.');
          }
          return;
        }

        if (mode === 'reset-confirm') {
          if (!resetToken.trim() || !password) {
            throw new Error('token and password required');
          }
          await postJSON('/api/auth/reset/password', {
            token: resetToken.trim(),
            password,
          });
          setPassword('');
          setResetToken('');
          switchMode('login');
          setNotice('Password updated. Login with the new password.');
        }
      } catch (ex) {
        setErr(String(ex && ex.message || ex));
      } finally {
        setBusy(false);
      }
    }

    const recoveryEnabled = !!authStatus.recovery_enabled;
    const emailRequired = !!authStatus.email_required;
    const accent = mode === 'register' ? 'var(--green, #22c55e)' : 'var(--accent)';
    const copy = modeCopy[mode] || modeCopy.login;

    return (
      <div role="dialog" aria-modal="true" aria-label="ATLAS login" style={{
        position: 'fixed', inset: 0, zIndex: 9998,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: 'var(--bg)',
        color: 'var(--fg)',
        fontFamily: 'var(--mono)',
      }}>
        <form onSubmit={submit} style={{
          width: 'min(420px, calc(100vw - 32px))',
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
              {copy.subtitle}
            </span>
          </div>

          {(mode === 'login' || mode === 'register') && (
            <label style={fieldStyle}>
              <span style={labelTextStyle}>Username</span>
              <input ref={userRef}
                     type="text" autoComplete="username"
                     value={username}
                     onChange={e => setUsername(e.target.value)}
                     disabled={busy}
                     style={inputStyle} />
            </label>
          )}

          {mode === 'register' && (
            <label style={fieldStyle}>
              <span style={labelTextStyle}>Email{emailRequired ? '' : ' (optional)'}</span>
              <input type="email" autoComplete="email"
                     value={email}
                     onChange={e => setEmail(e.target.value)}
                     disabled={busy}
                     style={inputStyle} />
            </label>
          )}

          {mode === 'find-id' && (
            <label style={fieldStyle}>
              <span style={labelTextStyle}>Email</span>
              <input ref={userRef}
                     type="email" autoComplete="email"
                     value={email}
                     onChange={e => setEmail(e.target.value)}
                     disabled={busy}
                     style={inputStyle} />
            </label>
          )}

          {mode === 'reset-request' && (
            <label style={fieldStyle}>
              <span style={labelTextStyle}>Username or Email</span>
              <input ref={userRef}
                     type="text" autoComplete="username"
                     value={identifier}
                     onChange={e => setIdentifier(e.target.value)}
                     disabled={busy}
                     style={inputStyle} />
            </label>
          )}

          {mode === 'reset-confirm' && (
            <label style={fieldStyle}>
              <span style={labelTextStyle}>Reset Token</span>
              <input ref={userRef}
                     type="text" autoComplete="one-time-code"
                     value={resetToken}
                     onChange={e => setResetToken(e.target.value)}
                     disabled={busy}
                     style={inputStyle} />
            </label>
          )}

          {(mode === 'login' || mode === 'register' || mode === 'reset-confirm') && (
            <label style={fieldStyle}>
              <span style={labelTextStyle}>{mode === 'reset-confirm' ? 'New Password' : 'Password'}</span>
              <input type="password"
                     autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                     value={password}
                     onChange={e => setPassword(e.target.value)}
                     disabled={busy}
                     style={inputStyle} />
            </label>
          )}

          {err && (
            <div role="alert" style={alertStyle}>{err}</div>
          )}

          {notice && !err && (
            <div role="status" style={noticeStyle}>{notice}</div>
          )}

          <button type="submit" disabled={busy} style={{
            ...btnStyle,
            background: accent, color: 'var(--bg-2)',
            opacity: busy ? 0.6 : 1, cursor: busy ? 'wait' : 'pointer',
          }}>
            {busy ? 'Working...' : copy.action}
          </button>

          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap', fontSize: 11, opacity: 0.75 }}>
            <button type="button"
                    onClick={() => switchMode(mode === 'login' ? 'register' : 'login')}
                    disabled={busy}
                    style={{ ...linkBtnStyle }}>
              {mode === 'login' ? 'Register' : 'Login'}
            </button>
            {recoveryEnabled && (
              <span style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                <button type="button" onClick={() => switchMode('find-id')} disabled={busy} style={{ ...linkBtnStyle }}>
                  Find ID
                </button>
                <button type="button" onClick={() => switchMode('reset-request')} disabled={busy} style={{ ...linkBtnStyle }}>
                  Forgot PW
                </button>
              </span>
            )}
          </div>
        </form>
      </div>
    );
  }

  const fieldStyle = { display: 'flex', flexDirection: 'column', gap: 4 };
  const labelTextStyle = { fontSize: 11, opacity: 0.7 };
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
  const alertStyle = {
    fontSize: 12, color: 'var(--red, #ef4444)',
    background: 'color-mix(in oklch, var(--red, #ef4444) 12%, transparent)',
    border: '1px solid color-mix(in oklch, var(--red, #ef4444) 40%, transparent)',
    borderRadius: 6, padding: '6px 10px',
  };
  const noticeStyle = {
    fontSize: 12, color: 'var(--green, #22c55e)',
    background: 'color-mix(in oklch, var(--green, #22c55e) 12%, transparent)',
    border: '1px solid color-mix(in oklch, var(--green, #22c55e) 35%, transparent)',
    borderRadius: 6, padding: '6px 10px',
  };

  window.LoginScreen = LoginScreen;
})();
