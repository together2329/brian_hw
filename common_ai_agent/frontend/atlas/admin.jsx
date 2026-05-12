function AdminPage() {
  const [users, setUsers] = React.useState([]);
  const [sessions, setSessions] = React.useState([]);
  const [usage, setUsage] = React.useState([]);
  const [costContexts, setCostContexts] = React.useState([]);
  const [dateCosts, setDateCosts] = React.useState([]);
  const [feedback, setFeedback] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);
  const [activeTab, setActiveTab] = React.useState('users');
  const [deleting, setDeleting] = React.useState(null);
  const [expandedUsage, setExpandedUsage] = React.useState(null);
  const [resolving, setResolving] = React.useState(null);
  const [authState, setAuthState] = React.useState('checking');
  const [loginUsername, setLoginUsername] = React.useState('admin');
  const [loginPassword, setLoginPassword] = React.useState('');
  const [loginError, setLoginError] = React.useState(null);
  const [loginPending, setLoginPending] = React.useState(false);

  async function reloadFeedback() {
    try {
      const r = await fetch('/api/admin/feedback');
      if (!r.ok) return;
      const d = await r.json();
      setFeedback(d.feedback || []);
    } catch (_) {}
  }

  const loadAdminData = React.useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [usersResp, sessionsResp, usageResp, fbResp] = await Promise.all([
        fetch('/api/admin/users'),
        fetch('/api/admin/sessions'),
        fetch('/api/admin/usage'),
        fetch('/api/admin/feedback'),
      ]);
      if ([usersResp, sessionsResp, usageResp, fbResp].some((r) => r.status === 401)) {
        setAuthState('unauthenticated');
        return;
      }
      if ([usersResp, sessionsResp, usageResp, fbResp].some((r) => r.status === 403)) {
        setAuthState('forbidden');
        setError('Admin access required');
        return;
      }
      if (!usersResp.ok || !sessionsResp.ok) {
        const bad = !usersResp.ok ? usersResp : sessionsResp;
        let detail = `HTTP ${bad.status}`;
        try {
          const body = await bad.json();
          detail = body.error || body.detail || detail;
        } catch (_) {}
        throw new Error(detail);
      }
      const usersData = await usersResp.json();
      const sessionsData = await sessionsResp.json();
      const usageData = usageResp.ok ? await usageResp.json() : { users: [] };
      const fbData = fbResp.ok ? await fbResp.json() : { feedback: [] };
      setUsers(usersData.users || []);
      setSessions(sessionsData.sessions || []);
      setUsage(usageData.users || []);
      setCostContexts(usageData.cost_by_context || []);
      setDateCosts(usageData.cost_by_date || []);
      setFeedback(fbData.feedback || []);
      setAuthState('authorized');
      setLoginError(null);
    } catch (e) {
      setAuthState('error');
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    loadAdminData();
  }, [loadAdminData]);

  const handleLogin = async (ev) => {
    ev.preventDefault();
    setLoginPending(true);
    setLoginError(null);
    try {
      const resp = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: loginUsername, password: loginPassword }),
      });
      if (!resp.ok) {
        let detail = `Login failed (HTTP ${resp.status})`;
        try {
          const body = await resp.json();
          detail = body.detail || body.error || detail;
        } catch (_) {}
        throw new Error(detail);
      }
      await loadAdminData();
    } catch (e) {
      setLoginError(String(e).replace(/^Error:\s*/, ''));
    } finally {
      setLoginPending(false);
    }
  };

  const handleResolveFeedback = async (fid) => {
    setResolving(fid);
    try {
      const r = await fetch(`/api/admin/feedback/${encodeURIComponent(fid)}/resolve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ notes: '' }),
      });
      if (r.ok) await reloadFeedback();
    } catch (_) {} finally {
      setResolving(null);
    }
  };

  const handleDeleteSession = async (sessionId) => {
    if (!window.confirm('Force-delete this session?')) return;
    setDeleting(sessionId);
    try {
      const resp = await fetch('/api/admin/sessions/' + encodeURIComponent(sessionId), {
        method: 'DELETE',
      });
      if (resp.status === 403) {
        setError('Admin access required');
        return;
      }
      const data = await resp.json();
      if (!resp.ok) {
        throw new Error(data.error || 'Delete failed');
      }
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
    } catch (e) {
      alert('Failed to delete session: ' + e);
    } finally {
      setDeleting(null);
    }
  };

  const pageStyle = {
    width: '100%',
    height: '100%',
    background: '#11161c',
    color: '#d6dde6',
    fontFamily: "var(--mono, 'Inter', 'Noto Sans KR', system-ui, sans-serif)",
    fontSize: 14,
    lineHeight: 1.5,
    overflow: 'auto',
    display: 'flex',
    flexDirection: 'column',
  };

  const headerStyle = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '20px 32px',
    borderBottom: '1px solid #2a3540',
    background: '#141a21',
  };

  const logoStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    fontSize: 22,
    fontWeight: 700,
    letterSpacing: '0.04em',
    color: '#f0c674',
  };

  const badgeStyle = {
    fontSize: 10,
    fontWeight: 600,
    textTransform: 'uppercase',
    letterSpacing: '0.08em',
    padding: '3px 8px',
    borderRadius: 4,
    background: '#2a3a4a',
    color: '#f0c674',
    border: '1px solid #3a4756',
  };

  const mainStyle = {
    flex: 1,
    padding: '24px 32px 40px',
    display: 'flex',
    flexDirection: 'column',
    gap: 24,
    maxWidth: 1200,
    margin: '0 auto',
    width: '100%',
  };

  const tabRowStyle = {
    display: 'flex',
    gap: 4,
    background: '#161d25',
    borderRadius: 6,
    padding: 3,
    border: '1px solid #2a3540',
    width: 'fit-content',
  };

  const tabStyle = (active) => ({
    padding: '6px 14px',
    fontSize: 12,
    fontWeight: 600,
    borderRadius: 4,
    border: 'none',
    cursor: 'pointer',
    fontFamily: "inherit",
    background: active ? '#2a3a4a' : 'transparent',
    color: active ? '#f0c674' : '#8893a3',
    transition: 'background 0.2s ease, color 0.2s ease',
  });

  const tableWrapStyle = {
    background: '#161d25',
    border: '1px solid #2a3540',
    borderRadius: 10,
    overflow: 'hidden',
    overflowX: 'auto',
  };

  const tableStyle = {
    width: '100%',
    borderCollapse: 'collapse',
    fontSize: 13,
  };

  const thStyle = {
    textAlign: 'left',
    padding: '10px 14px',
    background: '#1c252f',
    color: '#a3aebb',
    fontWeight: 600,
    fontSize: 11,
    textTransform: 'uppercase',
    letterSpacing: '0.06em',
    borderBottom: '1px solid #2a3540',
  };

  const tdStyle = {
    padding: '10px 14px',
    borderBottom: '1px solid #2a3540',
    color: '#d6dde6',
  };

  const btnDangerStyle = {
    background: 'transparent',
    color: '#e06c75',
    border: '1px solid #e06c75',
    borderRadius: 4,
    padding: '5px 10px',
    fontSize: 11,
    fontWeight: 600,
    fontFamily: "inherit",
    cursor: 'pointer',
    opacity: deleting ? 0.6 : 1,
    pointerEvents: deleting ? 'none' : 'auto',
  };

  const emptyStateStyle = {
    color: '#8893a3',
    fontSize: 13,
    textAlign: 'center',
    padding: '32px 0',
  };

  const errorStateStyle = {
    color: '#e06c75',
    fontSize: 14,
    textAlign: 'center',
    padding: '40px 0',
    border: '1px dashed #e06c75',
    borderRadius: 10,
    background: 'rgba(224,108,117,0.08)',
  };

  const loginPanelStyle = {
    width: 360,
    maxWidth: '100%',
    margin: '80px auto 0',
    background: '#161d25',
    border: '1px solid #2a3540',
    borderRadius: 8,
    padding: 22,
    boxShadow: '0 18px 50px rgba(0,0,0,0.32)',
  };

  const labelStyle = {
    display: 'block',
    fontSize: 11,
    fontWeight: 600,
    color: '#a3aebb',
    marginBottom: 6,
  };

  const inputStyle = {
    width: '100%',
    boxSizing: 'border-box',
    background: '#10161d',
    color: '#e6edf3',
    border: '1px solid #2f3c49',
    borderRadius: 4,
    padding: '9px 10px',
    fontFamily: 'inherit',
    fontSize: 13,
    outline: 'none',
  };

  const loginButtonStyle = {
    width: '100%',
    marginTop: 14,
    background: '#a35f22',
    color: '#fff7ed',
    border: '1px solid #b87333',
    borderRadius: 4,
    padding: '9px 12px',
    fontSize: 13,
    fontWeight: 700,
    fontFamily: 'inherit',
    cursor: loginPending ? 'wait' : 'pointer',
    opacity: loginPending ? 0.7 : 1,
  };

  const formatDate = (ts) => {
    if (!ts) return '—';
    try {
      return new Date(ts * 1000).toLocaleString();
    } catch (_) {
      return String(ts);
    }
  };

  const fmt = (n) => (n == null ? '—' : Number(n).toLocaleString());
  const usd = (n) => (n == null ? '—' : `$${Number(n).toFixed(4)}`);
  const shortId = (value) => String(value || '').slice(0, 8) || '—';

  return (
    <div style={pageStyle}>
      <header style={headerStyle}>
        <div style={logoStyle}>
          <span style={{ fontSize: 26 }}>◈</span>
          <span>ATLAS Admin</span>
        </div>
        <span style={badgeStyle}>Admin</span>
      </header>

      <main style={mainStyle}>
        {loading && (
          <div style={{ textAlign: 'center', padding: '40px 0', color: '#8893a3' }}>
            Loading…
          </div>
        )}

        {!loading && error && (
          <div style={errorStateStyle}>
            {error}
          </div>
        )}

        {!loading && authState === 'unauthenticated' && (
          <form style={loginPanelStyle} onSubmit={handleLogin}>
            <div style={{ fontSize: 18, fontWeight: 700, color: '#f0c674', marginBottom: 4 }}>
              Admin Login
            </div>
            <div style={{ fontSize: 12, color: '#8893a3', marginBottom: 18 }}>
              Sign in with an Atlas admin account.
            </div>
            <label style={labelStyle} htmlFor="atlas-admin-username">Username</label>
            <input
              id="atlas-admin-username"
              style={inputStyle}
              value={loginUsername}
              autoComplete="username"
              onChange={(ev) => setLoginUsername(ev.target.value)}
            />
            <label style={{ ...labelStyle, marginTop: 12 }} htmlFor="atlas-admin-password">Password</label>
            <input
              id="atlas-admin-password"
              style={inputStyle}
              value={loginPassword}
              type="password"
              autoComplete="current-password"
              onChange={(ev) => setLoginPassword(ev.target.value)}
            />
            {loginError && (
              <div style={{ color: '#e06c75', fontSize: 12, marginTop: 10 }}>
                {loginError}
              </div>
            )}
            <button style={loginButtonStyle} disabled={loginPending} type="submit">
              {loginPending ? 'Signing in...' : 'Login'}
            </button>
          </form>
        )}

        {!loading && !error && authState === 'authorized' && (
          <>
            <div style={tabRowStyle}>
              <button style={tabStyle(activeTab === 'users')} onClick={() => setActiveTab('users')}>
                Users ({users.length})
              </button>
              <button style={tabStyle(activeTab === 'sessions')} onClick={() => setActiveTab('sessions')}>
                Sessions ({sessions.length})
              </button>
              <button style={tabStyle(activeTab === 'usage')} onClick={() => setActiveTab('usage')}>
                Usage ({usage.length})
              </button>
              <button style={tabStyle(activeTab === 'costs')} onClick={() => setActiveTab('costs')}>
                Costs ({costContexts.length})
              </button>
              <button style={tabStyle(activeTab === 'feedback')} onClick={() => setActiveTab('feedback')}>
                Feedback ({feedback.filter(f => f.status !== 'resolved').length}/{feedback.length})
              </button>
            </div>

            {activeTab === 'users' && (
              <div style={tableWrapStyle}>
                <table style={tableStyle}>
                  <thead>
                    <tr>
                      <th style={thStyle}>Username</th>
                      <th style={thStyle}>Display Name</th>
                      <th style={thStyle}>Role</th>
                      <th style={thStyle}>Sessions</th>
                      <th style={thStyle}>Created</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.length === 0 ? (
                      <tr>
                        <td colSpan={5} style={{ ...tdStyle, ...emptyStateStyle }}>No users found.</td>
                      </tr>
                    ) : (
                      users.map((u) => (
                        <tr key={u.id}>
                          <td style={tdStyle}>{u.username}</td>
                          <td style={tdStyle}>{u.display_name || '—'}</td>
                          <td style={tdStyle}>
                            <span style={{
                              fontSize: 10,
                              fontWeight: 600,
                              textTransform: 'uppercase',
                              padding: '2px 6px',
                              borderRadius: 3,
                              background: u.role === 'admin' ? '#2a3a4a' : '#1c252f',
                              color: u.role === 'admin' ? '#f0c674' : '#a3aebb',
                              border: '1px solid #2a3540',
                            }}>
                              {u.role}
                            </span>
                          </td>
                          <td style={tdStyle}>{u.session_count ?? 0}</td>
                          <td style={tdStyle}>{formatDate(u.created_at)}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            )}

            {activeTab === 'sessions' && (
              <div style={tableWrapStyle}>
                <table style={tableStyle}>
                  <thead>
                    <tr>
                      <th style={thStyle}>Title</th>
                      <th style={thStyle}>Project</th>
                      <th style={thStyle}>Status</th>
                      <th style={thStyle}>Owner</th>
                      <th style={thStyle}>Created</th>
                      <th style={thStyle}>Updated</th>
                      <th style={thStyle}></th>
                    </tr>
                  </thead>
                  <tbody>
                    {sessions.length === 0 ? (
                      <tr>
                        <td colSpan={7} style={{ ...tdStyle, ...emptyStateStyle }}>No sessions found.</td>
                      </tr>
                    ) : (
                      sessions.map((s) => (
                        <tr key={s.id}>
                          <td style={tdStyle}>{s.title || '—'}</td>
                          <td style={tdStyle}>{s.project_id || '—'}</td>
                          <td style={tdStyle}>
                            <span style={{
                              fontSize: 10,
                              fontWeight: 600,
                              textTransform: 'uppercase',
                              padding: '2px 6px',
                              borderRadius: 3,
                              background: s.status === 'active' ? '#1c2f25' : '#1c252f',
                              color: s.status === 'active' ? '#7dc9a0' : '#a3aebb',
                              border: '1px solid #2a3540',
                            }}>
                              {s.status}
                            </span>
                          </td>
                          <td style={tdStyle}>{s.owner_username || s.user_id || '—'}</td>
                          <td style={tdStyle}>{formatDate(s.created_at)}</td>
                          <td style={tdStyle}>{formatDate(s.updated_at)}</td>
                          <td style={tdStyle}>
                            <button
                              style={btnDangerStyle}
                              onClick={() => handleDeleteSession(s.id)}
                              disabled={deleting === s.id}
                            >
                              {deleting === s.id ? 'Deleting…' : 'Delete'}
                            </button>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            )}

            {activeTab === 'usage' && (
              <div style={tableWrapStyle}>
                <table style={tableStyle}>
                  <thead>
                    <tr>
                      <th style={thStyle}>Username</th>
                      <th style={thStyle}>Role</th>
                      <th style={thStyle}>Sessions</th>
                      <th style={thStyle}>Messages</th>
                      <th style={thStyle}>Tokens In</th>
                      <th style={thStyle}>Tokens Out</th>
                      <th style={thStyle}>Reasoning</th>
                      <th style={thStyle}>Cost (USD)</th>
                      <th style={thStyle}>Last Activity</th>
                    </tr>
                  </thead>
                  <tbody>
                    {usage.length === 0 ? (
                      <tr>
                        <td colSpan={9} style={{ ...tdStyle, ...emptyStateStyle }}>No usage data yet.</td>
                      </tr>
                    ) : (
                      usage.flatMap((u) => {
                        const expanded = expandedUsage === u.user_id;
                        const rows = [
                          <tr key={u.user_id}
                              style={{ cursor: 'pointer' }}
                              onClick={() => setExpandedUsage(expanded ? null : u.user_id)}
                              title={expanded ? 'click to collapse' : 'click to see model + tool breakdown'}>
                            <td style={tdStyle}>
                              <span style={{ marginRight: 6, opacity: 0.6 }}>{expanded ? '▾' : '▸'}</span>
                              {u.username}
                            </td>
                            <td style={tdStyle}>{u.role}</td>
                            <td style={tdStyle}>{fmt(u.session_count)}</td>
                            <td style={tdStyle}>{fmt(u.message_count)}</td>
                            <td style={tdStyle}>{fmt(u.tokens_in)}</td>
                            <td style={tdStyle}>{fmt(u.tokens_out)}</td>
                            <td style={tdStyle}>{fmt(u.tokens_reasoning)}</td>
                            <td style={tdStyle}>{usd(u.total_cost_usd)}</td>
                            <td style={tdStyle}>{formatDate(u.last_message_at)}</td>
                          </tr>,
                        ];
                        if (expanded) {
                          rows.push(
                            <tr key={u.user_id + '-detail'}>
                              <td colSpan={9} style={{ ...tdStyle, background: '#10141a', padding: '12px 16px' }}>
                                <div style={{ display: 'flex', gap: 28, flexWrap: 'wrap' }}>
                                  <div style={{ minWidth: 260 }}>
                                    <div style={{ fontSize: 11, opacity: 0.7, marginBottom: 6,
                                                  textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                                      Models
                                    </div>
                                    {(u.models || []).length === 0 ? (
                                      <div style={{ opacity: 0.5, fontSize: 12 }}>no model usage</div>
                                    ) : (
                                      <table style={{ fontSize: 12, borderCollapse: 'collapse' }}>
                                        <tbody>
                                          {u.models.slice(0, 8).map(m => (
                                            <tr key={m.model_id}>
                                              <td style={{ padding: '2px 10px 2px 0' }}>{m.model_id}</td>
                                              <td style={{ padding: '2px 10px', textAlign: 'right', opacity: 0.7 }}>{fmt(m.calls)} calls</td>
                                              <td style={{ padding: '2px 10px', textAlign: 'right', opacity: 0.7 }}>{fmt(m.tokens)} tok</td>
                                              <td style={{ padding: '2px 0',    textAlign: 'right', opacity: 0.7 }}>{usd(m.cost)}</td>
                                            </tr>
                                          ))}
                                        </tbody>
                                      </table>
                                    )}
                                  </div>
                                  <div style={{ minWidth: 220 }}>
                                    <div style={{ fontSize: 11, opacity: 0.7, marginBottom: 6,
                                                  textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                                      Top Tools
                                    </div>
                                    {(u.tools || []).length === 0 ? (
                                      <div style={{ opacity: 0.5, fontSize: 12 }}>no tool calls</div>
                                    ) : (
                                      <table style={{ fontSize: 12, borderCollapse: 'collapse' }}>
                                        <tbody>
                                          {u.tools.slice(0, 10).map(t => (
                                            <tr key={t.tool_name}>
                                              <td style={{ padding: '2px 12px 2px 0' }}>{t.tool_name}</td>
                                              <td style={{ padding: '2px 0', textAlign: 'right', opacity: 0.7 }}>{fmt(t.calls)}</td>
                                            </tr>
                                          ))}
                                        </tbody>
                                      </table>
                                    )}
                                  </div>
                                </div>
                              </td>
                            </tr>
                          );
                        }
                        return rows;
                      })
                    )}
                  </tbody>
                </table>
              </div>
            )}

            {activeTab === 'costs' && (
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 420px), 1fr))',
                gap: 18,
                alignItems: 'start',
              }}>
                <div style={tableWrapStyle}>
                  <div style={{ padding: '12px 14px', borderBottom: '1px solid #2a3540',
                                background: '#1c252f', color: '#f0c674',
                                fontSize: 12, fontWeight: 700, textTransform: 'uppercase',
                                letterSpacing: '0.06em' }}>
                    Cost by IP / Workspace
                  </div>
                  <table style={tableStyle}>
                    <thead>
                      <tr>
                        <th style={thStyle}>IP / Project</th>
                        <th style={thStyle}>Workspace</th>
                        <th style={thStyle}>Session</th>
                        <th style={thStyle}>User</th>
                        <th style={thStyle}>Calls</th>
                        <th style={thStyle}>Tokens</th>
                        <th style={thStyle}>Cost</th>
                        <th style={thStyle}>Last</th>
                      </tr>
                    </thead>
                    <tbody>
                      {costContexts.length === 0 ? (
                        <tr>
                          <td colSpan={8} style={{ ...tdStyle, ...emptyStateStyle }}>No cost data yet.</td>
                        </tr>
                      ) : (
                        costContexts.map((row) => (
                          <tr key={`${row.session_id || ''}-${row.ip}-${row.workspace}`}>
                            <td style={tdStyle}>{row.ip || 'unknown'}</td>
                            <td style={tdStyle}>{row.workspace || 'default'}</td>
                            <td style={tdStyle} title={row.session_id || ''}>
                              {row.session || shortId(row.session_id)}
                            </td>
                            <td style={tdStyle}>{row.username || 'unknown'}</td>
                            <td style={tdStyle}>{fmt(row.calls)}</td>
                            <td style={tdStyle}>{fmt(row.tokens)}</td>
                            <td style={tdStyle}>{usd(row.cost)}</td>
                            <td style={tdStyle}>{formatDate(row.last_message_at)}</td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>

                <div style={tableWrapStyle}>
                  <div style={{ padding: '12px 14px', borderBottom: '1px solid #2a3540',
                                background: '#1c252f', color: '#f0c674',
                                fontSize: 12, fontWeight: 700, textTransform: 'uppercase',
                                letterSpacing: '0.06em' }}>
                    Cost by Date
                  </div>
                  <table style={tableStyle}>
                    <thead>
                      <tr>
                        <th style={thStyle}>Date</th>
                        <th style={thStyle}>IP / Project</th>
                        <th style={thStyle}>Workspace</th>
                        <th style={thStyle}>Calls</th>
                        <th style={thStyle}>Tokens</th>
                        <th style={thStyle}>Cost</th>
                      </tr>
                    </thead>
                    <tbody>
                      {dateCosts.length === 0 ? (
                        <tr>
                          <td colSpan={6} style={{ ...tdStyle, ...emptyStateStyle }}>No daily cost data yet.</td>
                        </tr>
                      ) : (
                        dateCosts.map((row) => (
                          <tr key={`${row.day}-${row.session_id || ''}-${row.ip}-${row.workspace}`}>
                            <td style={tdStyle}>{row.day || 'unknown'}</td>
                            <td style={tdStyle}>{row.ip || 'unknown'}</td>
                            <td style={tdStyle}>{row.workspace || 'default'}</td>
                            <td style={tdStyle}>{fmt(row.calls)}</td>
                            <td style={tdStyle}>{fmt(row.tokens)}</td>
                            <td style={tdStyle}>{usd(row.cost)}</td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {activeTab === 'feedback' && (
              <div style={tableWrapStyle}>
                <table style={tableStyle}>
                  <thead>
                    <tr>
                      <th style={thStyle}>When</th>
                      <th style={thStyle}>User</th>
                      <th style={thStyle}>Status</th>
                      <th style={{ ...thStyle, width: '50%' }}>Message</th>
                      <th style={thStyle}>Resolved By</th>
                      <th style={thStyle}>Resolved At</th>
                      <th style={thStyle}></th>
                    </tr>
                  </thead>
                  <tbody>
                    {feedback.length === 0 ? (
                      <tr>
                        <td colSpan={7} style={{ ...tdStyle, ...emptyStateStyle }}>
                          No feedback yet. Users can submit with <code>/feedback &lt;message&gt;</code> in the chat.
                        </td>
                      </tr>
                    ) : (
                      feedback.map((f) => {
                        const open = f.status !== 'resolved';
                        return (
                          <tr key={f.id} style={open ? { background: '#191c22' } : { opacity: 0.65 }}>
                            <td style={tdStyle}>{formatDate(f.created_at)}</td>
                            <td style={tdStyle}>{f.username || f.user_id.slice(0, 8)}</td>
                            <td style={tdStyle}>
                              <span style={{
                                fontSize: 10,
                                fontWeight: 600,
                                textTransform: 'uppercase',
                                padding: '2px 6px',
                                borderRadius: 3,
                                background: open ? '#2a3a4a' : '#1c252f',
                                color: open ? '#f0c674' : '#7d8590',
                                border: '1px solid #2a3540',
                              }}>{f.status}</span>
                            </td>
                            <td style={{ ...tdStyle, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                              {f.content}
                            </td>
                            <td style={tdStyle}>{f.resolved_by || '—'}</td>
                            <td style={tdStyle}>{f.resolved_at ? formatDate(f.resolved_at) : '—'}</td>
                            <td style={tdStyle}>
                              {open && (
                                <button
                                  onClick={() => handleResolveFeedback(f.id)}
                                  disabled={resolving === f.id}
                                  style={{
                                    padding: '4px 10px',
                                    background: '#2a3540',
                                    color: '#e6edf3',
                                    border: '1px solid #3a4550',
                                    borderRadius: 3,
                                    cursor: resolving === f.id ? 'wait' : 'pointer',
                                    fontSize: 11,
                                  }}>
                                  {resolving === f.id ? '…' : '✓ Resolve'}
                                </button>
                              )}
                            </td>
                          </tr>
                        );
                      })
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}

window.AdminPage = AdminPage;

if (typeof document !== 'undefined' && document.getElementById('root')) {
  ReactDOM.createRoot(document.getElementById('root')).render(<AdminPage />);
}
