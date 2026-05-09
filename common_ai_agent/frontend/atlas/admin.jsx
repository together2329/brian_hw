function AdminPage() {
  const [users, setUsers] = React.useState([]);
  const [sessions, setSessions] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);
  const [activeTab, setActiveTab] = React.useState('users');
  const [deleting, setDeleting] = React.useState(null);

  React.useEffect(() => {
    async function init() {
      try {
        setLoading(true);
        const [usersResp, sessionsResp] = await Promise.all([
          fetch('/api/admin/users'),
          fetch('/api/admin/sessions'),
        ]);
        if (usersResp.status === 403 || sessionsResp.status === 403) {
          setError('Admin access required');
          setLoading(false);
          return;
        }
        const usersData = await usersResp.json();
        const sessionsData = await sessionsResp.json();
        setUsers(usersData.users || []);
        setSessions(sessionsData.sessions || []);
        setError(null);
      } catch (e) {
        setError(String(e));
      } finally {
        setLoading(false);
      }
    }
    init();
  }, []);

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

  const formatDate = (ts) => {
    if (!ts) return '—';
    try {
      return new Date(ts * 1000).toLocaleString();
    } catch (_) {
      return String(ts);
    }
  };

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

        {!loading && !error && (
          <>
            <div style={tabRowStyle}>
              <button style={tabStyle(activeTab === 'users')} onClick={() => setActiveTab('users')}>
                Users ({users.length})
              </button>
              <button style={tabStyle(activeTab === 'sessions')} onClick={() => setActiveTab('sessions')}>
                Sessions ({sessions.length})
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
