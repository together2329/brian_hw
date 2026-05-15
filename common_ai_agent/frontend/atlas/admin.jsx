function AdminPage() {
  const [users, setUsers] = React.useState([]);
  const [sessions, setSessions] = React.useState([]);
  const [usage, setUsage] = React.useState([]);
  const [costContexts, setCostContexts] = React.useState([]);
  const [dateCosts, setDateCosts] = React.useState([]);
  const [todoUsage, setTodoUsage] = React.useState([]);
  const [todoFlow, setTodoFlow] = React.useState([]);
  const [traceEvents, setTraceEvents] = React.useState([]);
  const [toolUsage, setToolUsage] = React.useState([]);
  const [interventions, setInterventions] = React.useState([]);
  const [rtlRunHistory, setRtlRunHistory] = React.useState([]);
  const [artifactVersions, setArtifactVersions] = React.useState([]);
  const [runArtifactSets, setRunArtifactSets] = React.useState([]);
  const [feedback, setFeedback] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState(null);
  const [authStatus, setAuthStatus] = React.useState(null);
  const [authChecked, setAuthChecked] = React.useState(false);
  const [authUser, setAuthUser] = React.useState(null);
  const [authError, setAuthError] = React.useState(null);
  const [loginSubmitting, setLoginSubmitting] = React.useState(false);
  const [loginForm, setLoginForm] = React.useState({
    username: 'admin',
    email: '',
    password: '',
    displayName: 'Admin',
  });
  const [activeTab, setActiveTab] = React.useState('overview');
  const [filters, setFilters] = React.useState({
    range: '7d',
    ip: '',
    workspace: '',
    workflow: '',
    user: '',
  });
  const [deleting, setDeleting] = React.useState(null);
  const [expandedUsage, setExpandedUsage] = React.useState(null);
  const [resolving, setResolving] = React.useState(null);

  async function reloadFeedback() {
    try {
      const r = await fetch('/api/admin/feedback');
      if (!r.ok) return;
      const d = await r.json();
      setFeedback(d.feedback || []);
    } catch (_) {}
  }

  async function fetchAdminStatus() {
    const r = await fetch('/api/admin/auth/status');
    if (!r.ok) {
      throw new Error(`Admin auth status failed: HTTP ${r.status}`);
    }
    return r.json();
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
        setAuthUser(null);
        setAuthStatus((prev) => ({ ...(prev || {}), login_required: true, authenticated: false }));
        setAuthError('Admin login required');
        return;
      }
      if ([usersResp, sessionsResp, usageResp, fbResp].some((r) => r.status === 403)) {
        setError('Admin role required');
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
      setTodoUsage(usageData.todo_usage || []);
      setTodoFlow(usageData.todo_flow || []);
      setTraceEvents(usageData.trace_events || []);
      setToolUsage(usageData.tool_usage || []);
      setInterventions(usageData.interventions || []);
      setRtlRunHistory(usageData.rtl_run_history || []);
      setArtifactVersions(usageData.artifact_versions || []);
      setRunArtifactSets(usageData.run_artifact_sets || []);
      setFeedback(fbData.feedback || []);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    let alive = true;
    (async () => {
      try {
        setLoading(true);
        const status = await fetchAdminStatus();
        if (!alive) return;
        setAuthStatus(status);
        setAuthChecked(true);
        if (!status.login_required || status.authenticated) {
          setAuthUser(status.user || null);
          await loadAdminData();
        } else {
          setLoading(false);
        }
      } catch (e) {
        if (!alive) return;
        setAuthChecked(true);
        setError(String(e));
        setLoading(false);
      }
    })();
    return () => { alive = false; };
  }, [loadAdminData]);

  const handleAdminLogin = async (ev) => {
    ev.preventDefault();
    setAuthError(null);
    setLoginSubmitting(true);
    try {
      const username = String(loginForm.username || '').trim();
      const password = String(loginForm.password || '');
      if (!username || !password) {
        throw new Error('Username and password required');
      }
      const createFirstAdmin = authStatus && authStatus.login_required && !authStatus.admin_user_exists;
      const email = String(loginForm.email || '').trim();
      if (createFirstAdmin && authStatus.email_required && !email) {
        throw new Error('Email required');
      }
      const payload = {
        username,
        password,
        display_name: String(loginForm.displayName || '').trim() || username,
      };
      if (createFirstAdmin && email) {
        payload.email = email;
      }
      let r = await fetch(createFirstAdmin ? '/api/auth/register' : '/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!r.ok && createFirstAdmin && r.status === 409) {
        r = await fetch('/api/auth/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, password }),
        });
      }
      if (!r.ok) {
        let detail = `HTTP ${r.status}`;
        try {
          const body = await r.json();
          detail = body.detail || body.error || detail;
        } catch (_) {}
        throw new Error(detail);
      }
      const status = await fetchAdminStatus();
      setAuthStatus(status);
      setAuthChecked(true);
      if (!status.authenticated) {
        throw new Error('Admin role required');
      }
      setAuthUser(status.user || null);
      await loadAdminData();
    } catch (e) {
      setAuthError(String(e));
      setLoading(false);
    } finally {
      setLoginSubmitting(false);
    }
  };

  const handleLogout = async () => {
    try {
      await fetch('/api/auth/logout', { method: 'POST' });
    } catch (_) {}
    try {
      const status = await fetchAdminStatus();
      setAuthStatus(status);
    } catch (_) {
      setAuthStatus({ login_required: true, authenticated: false, admin_user_exists: true, mode: 'db' });
    }
    setAuthUser(null);
    setUsers([]);
    setSessions([]);
    setUsage([]);
    setCostContexts([]);
    setDateCosts([]);
    setTodoUsage([]);
    setTodoFlow([]);
    setTraceEvents([]);
    setToolUsage([]);
    setInterventions([]);
    setRtlRunHistory([]);
    setArtifactVersions([]);
    setRunArtifactSets([]);
    setFeedback([]);
    setLoading(false);
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

  const headerRightStyle = {
    display: 'flex',
    alignItems: 'center',
    gap: 8,
  };

  const headerButtonStyle = {
    minHeight: 28,
    padding: '4px 9px',
    borderRadius: 4,
    border: '1px solid #3a4756',
    background: '#10161d',
    color: '#d6dde6',
    cursor: 'pointer',
    fontFamily: 'inherit',
    fontSize: 11,
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
    flexWrap: 'wrap',
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

  const filterBarStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
    gap: 10,
    padding: 12,
    background: '#161d25',
    border: '1px solid #2a3540',
    borderRadius: 10,
  };

  const filterLabelStyle = {
    display: 'flex',
    flexDirection: 'column',
    gap: 5,
    color: '#8893a3',
    fontSize: 11,
    fontWeight: 700,
    textTransform: 'uppercase',
    letterSpacing: '0.04em',
  };

  const selectStyle = {
    minHeight: 32,
    background: '#10161d',
    color: '#d6dde6',
    border: '1px solid #2a3540',
    borderRadius: 5,
    padding: '5px 8px',
    fontFamily: 'inherit',
    fontSize: 12,
  };

  const loginShellStyle = {
    width: 'min(100%, 420px)',
    margin: '78px auto 0',
    padding: 24,
    background: '#161d25',
    border: '1px solid #2a3540',
    borderRadius: 8,
    boxShadow: '0 20px 50px rgba(0,0,0,0.35)',
  };

  const loginTitleStyle = {
    margin: '0 0 18px',
    color: '#f0c674',
    fontSize: 18,
    fontWeight: 700,
  };

  const loginFieldStyle = {
    display: 'flex',
    flexDirection: 'column',
    gap: 6,
    marginBottom: 12,
    color: '#8893a3',
    fontSize: 11,
    fontWeight: 700,
    textTransform: 'uppercase',
    letterSpacing: '0.04em',
  };

  const loginInputStyle = {
    minHeight: 38,
    background: '#10161d',
    color: '#e6edf3',
    border: '1px solid #2a3540',
    borderRadius: 5,
    padding: '7px 10px',
    fontFamily: 'inherit',
    fontSize: 14,
  };

  const loginButtonStyle = {
    width: '100%',
    minHeight: 40,
    marginTop: 6,
    borderRadius: 5,
    border: '1px solid #4a5b6e',
    background: '#2a3a4a',
    color: '#f0c674',
    cursor: loginSubmitting ? 'wait' : 'pointer',
    fontFamily: 'inherit',
    fontSize: 13,
    fontWeight: 700,
  };

  const overviewGridStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 170px), 1fr))',
    gap: 12,
  };

  const metricCardStyle = (tone = 'default') => ({
    background: tone === 'danger' ? 'rgba(224,108,117,0.10)' : '#161d25',
    border: tone === 'danger' ? '1px solid rgba(224,108,117,0.45)' : '1px solid #2a3540',
    borderRadius: 8,
    padding: '14px 15px',
    minHeight: 82,
  });

  const metricLabelStyle = {
    color: '#8893a3',
    fontSize: 11,
    fontWeight: 700,
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    marginBottom: 7,
  };

  const metricValueStyle = {
    color: '#f0c674',
    fontSize: 24,
    fontWeight: 750,
    lineHeight: 1.1,
  };

  const panelTitleStyle = {
    padding: '12px 14px',
    borderBottom: '1px solid #2a3540',
    background: '#1c252f',
    color: '#f0c674',
    fontSize: 12,
    fontWeight: 700,
    textTransform: 'uppercase',
    letterSpacing: '0.06em',
  };

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
  const firstVersion = (row, type) => {
    const items = (row.artifact_versions && row.artifact_versions[type]) || [];
    return items.length ? items[0] : null;
  };
  const versionText = (row, type) => {
    const item = firstVersion(row, type);
    return item ? item.version || shortId(item.artifact_version_id) : '—';
  };
  const versionTagText = (row, type) => {
    const item = firstVersion(row, type);
    return item ? item.git_tag || item.sha256_tree || shortId(item.artifact_version_id) : '—';
  };
  const payloadText = (value) => {
    if (value == null || value === '') return '—';
    try {
      const text = typeof value === 'string' ? value : JSON.stringify(value);
      return text.length > 180 ? text.slice(0, 177) + '…' : text;
    } catch (_) {
      return String(value);
    }
  };
  const sum = (rows, key) => rows.reduce((acc, row) => acc + Number(row[key] || 0), 0);
  const rowTimestamp = (row) => {
    const direct = row.last_message_at || row.last_event_at || row.last_tool_at
      || row.last_intervention_at || row.started_at || row.ended_at
      || row.created_at || row.updated_at || row.first_intervention_at;
    if (direct) return Number(direct) || 0;
    if (row.day) {
      const parsed = Date.parse(`${row.day}T23:59:59`);
      return Number.isNaN(parsed) ? 0 : parsed / 1000;
    }
    return 0;
  };
  const inRange = (row) => {
    if (!filters.range || filters.range === 'all') return true;
    const days = { '24h': 1, '7d': 7, '30d': 30 }[filters.range] || 7;
    const ts = rowTimestamp(row);
    if (!ts) return true;
    return ts >= ((Date.now() / 1000) - days * 86400);
  };
  const valueMatches = (selected, value) => !selected || String(value || '') === selected;
  const rowMatches = (row) => (
    inRange(row)
    && valueMatches(filters.ip, row.ip)
    && valueMatches(filters.workspace, row.workspace)
    && valueMatches(filters.workflow, row.workflow)
    && valueMatches(filters.user, row.username || row.owner_username)
  );
  const uniqueOptions = (rows, key) => Array.from(new Set(
    rows.map((row) => String(row[key] || '').trim()).filter(Boolean)
  )).sort((a, b) => a.localeCompare(b));
  const allContextRows = [
    ...costContexts,
    ...dateCosts,
    ...todoUsage,
    ...todoFlow,
    ...traceEvents,
    ...toolUsage,
    ...interventions,
    ...rtlRunHistory,
    ...artifactVersions,
    ...runArtifactSets,
  ];
  const filterOptions = {
    ips: uniqueOptions(allContextRows, 'ip'),
    workspaces: uniqueOptions(allContextRows, 'workspace'),
    workflows: uniqueOptions(allContextRows, 'workflow'),
    users: uniqueOptions([
      ...allContextRows,
      ...usage,
      ...sessions.map((s) => ({ username: s.owner_username || s.user_id })),
      ...feedback,
    ], 'username'),
  };
  const filteredUsers = users.filter((row) => (
    valueMatches(filters.user, row.username)
    && !filters.ip
    && !filters.workspace
    && !filters.workflow
  ));
  const filteredUsage = usage.filter((row) => (
    inRange(row)
    && valueMatches(filters.user, row.username)
    && !filters.ip
    && !filters.workspace
    && !filters.workflow
  ));
  const filteredSessions = sessions.filter((row) => (
    inRange(row)
    && valueMatches(filters.user, row.owner_username || row.user_id)
    && (!filters.ip || String(row.project_id || row.title || '') === filters.ip)
    && !filters.workspace
    && !filters.workflow
  ));
  const filteredCostContexts = costContexts.filter(rowMatches);
  const filteredDateCosts = dateCosts.filter(rowMatches);
  const filteredTodoUsage = todoUsage.filter(rowMatches);
  const filteredTodoFlow = todoFlow.filter(rowMatches);
  const filteredTraceEvents = traceEvents.filter(rowMatches);
  const filteredToolUsage = toolUsage.filter(rowMatches);
  const filteredInterventions = interventions.filter(rowMatches);
  const filteredRtlRunHistory = rtlRunHistory.filter(rowMatches);
  const filteredArtifactVersions = artifactVersions.filter(rowMatches);
  const filteredRunArtifactSets = runArtifactSets.filter(rowMatches);
  const filteredFeedback = feedback.filter((row) => (
    inRange(row)
    && valueMatches(filters.user, row.username)
    && !filters.ip
    && !filters.workspace
    && !filters.workflow
  ));
  const topCostRows = [...filteredCostContexts].sort((a, b) => Number(b.cost || 0) - Number(a.cost || 0)).slice(0, 5);
  const topRejectedTodos = [...filteredTodoUsage]
    .filter((row) => Number(row.rejected_count || 0) > 0)
    .sort((a, b) => Number(b.rejected_count || 0) - Number(a.rejected_count || 0))
    .slice(0, 5);
  const topToolRows = [...filteredToolUsage]
    .sort((a, b) => (
      Number(b.failed_calls || 0) - Number(a.failed_calls || 0)
      || Number(b.observation_tokens_est || 0) - Number(a.observation_tokens_est || 0)
    ))
    .slice(0, 5);
  const topHumanRows = [...filteredInterventions]
    .sort((a, b) => Number(b.intervention_count || 0) - Number(a.intervention_count || 0))
    .slice(0, 5);
  const askUserOpened = new Set(filteredTraceEvents
    .filter((row) => row.event_type === 'ask_user.opened')
    .map((row) => (row.payload && row.payload.flow_id) || row.event_id)
    .filter(Boolean));
  const askUserAnswered = new Set(filteredTraceEvents
    .filter((row) => row.event_type === 'ask_user.answered')
    .map((row) => (row.payload && row.payload.flow_id) || row.event_id)
    .filter(Boolean));
  const overview = {
    cost: sum(filteredCostContexts, 'cost'),
    llmCalls: sum(filteredCostContexts, 'calls'),
    toolCalls: sum(filteredToolUsage, 'calls'),
    toolFailures: sum(filteredToolUsage, 'failed_calls'),
    obsTokens: sum(filteredToolUsage, 'observation_tokens_est'),
    rejectedTodos: sum(filteredTodoUsage, 'rejected_count'),
    openTodos: filteredTodoUsage.filter((row) => !['approved', 'completed'].includes(String(row.status || '').toLowerCase())).length,
    humanInputs: sum(filteredInterventions, 'intervention_count'),
    rtlRuns: filteredRtlRunHistory.length,
    artifactVersions: filteredArtifactVersions.length,
    runArtifactSets: filteredRunArtifactSets.length,
    pendingHuman: Array.from(askUserOpened).filter((flow) => !askUserAnswered.has(flow)).length,
    pendingFeedback: filteredFeedback.filter((row) => row.status !== 'resolved').length,
  };
  const setFilter = (key, value) => setFilters((prev) => ({ ...prev, [key]: value }));
  const clearFilters = () => setFilters({ range: 'all', ip: '', workspace: '', workflow: '', user: '' });
  const loginRequired = authChecked && authStatus && authStatus.login_required && !authStatus.authenticated;
  const loginButtonText = authStatus && authStatus.admin_user_exists ? 'Log in' : 'Create admin account';

  return (
    <div style={pageStyle}>
      <header style={headerStyle}>
        <div style={logoStyle}>
          <span style={{ fontSize: 26 }}>◈</span>
          <span>ATLAS Admin</span>
        </div>
        <div style={headerRightStyle}>
          {authUser && <span style={badgeStyle}>{authUser.username}</span>}
          <span style={badgeStyle}>{authStatus && authStatus.mode === 'local' ? 'Local Admin' : 'Admin'}</span>
          {authUser && authStatus && authStatus.login_required && (
            <button type="button" style={headerButtonStyle} onClick={handleLogout}>
              Logout
            </button>
          )}
        </div>
      </header>

      <main style={mainStyle}>
        {loading && (
          <div style={{ textAlign: 'center', padding: '40px 0', color: '#8893a3' }}>
            Loading…
          </div>
        )}

        {!loading && loginRequired && (
          <form style={loginShellStyle} onSubmit={handleAdminLogin}>
            <h1 style={loginTitleStyle}>Admin Login</h1>
            {authError && (
              <div style={{ ...errorStateStyle, marginBottom: 14 }}>
                {authError}
              </div>
            )}
            <label style={loginFieldStyle}>
              Username
              <input
                style={loginInputStyle}
                value={loginForm.username}
                autoComplete="username"
                onChange={(ev) => setLoginForm((prev) => ({ ...prev, username: ev.target.value }))}
              />
            </label>
            {!authStatus.admin_user_exists && (
              <label style={loginFieldStyle}>
                Display Name
                <input
                  style={loginInputStyle}
                  value={loginForm.displayName}
                  autoComplete="name"
                  onChange={(ev) => setLoginForm((prev) => ({ ...prev, displayName: ev.target.value }))}
                />
              </label>
            )}
            {!authStatus.admin_user_exists && (
              <label style={loginFieldStyle}>
                Email{authStatus.email_required ? '' : ' (optional)'}
                <input
                  style={loginInputStyle}
                  type="email"
                  value={loginForm.email}
                  autoComplete="email"
                  onChange={(ev) => setLoginForm((prev) => ({ ...prev, email: ev.target.value }))}
                />
              </label>
            )}
            <label style={loginFieldStyle}>
              Password
              <input
                style={loginInputStyle}
                type="password"
                value={loginForm.password}
                autoComplete={authStatus.admin_user_exists ? 'current-password' : 'new-password'}
                onChange={(ev) => setLoginForm((prev) => ({ ...prev, password: ev.target.value }))}
              />
            </label>
            <button type="submit" style={loginButtonStyle} disabled={loginSubmitting}>
              {loginSubmitting ? 'Working…' : loginButtonText}
            </button>
          </form>
        )}

        {!loading && !loginRequired && error && (
          <div style={errorStateStyle}>
            {error}
          </div>
        )}

        {!loading && !loginRequired && !error && (
          <>
            <div style={tabRowStyle}>
              <button style={tabStyle(activeTab === 'overview')} onClick={() => setActiveTab('overview')}>
                Overview
              </button>
              <button style={tabStyle(activeTab === 'users')} onClick={() => setActiveTab('users')}>
                Users ({filteredUsers.length})
              </button>
              <button style={tabStyle(activeTab === 'sessions')} onClick={() => setActiveTab('sessions')}>
                Sessions ({filteredSessions.length})
              </button>
              <button style={tabStyle(activeTab === 'usage')} onClick={() => setActiveTab('usage')}>
                Usage ({filteredUsage.length})
              </button>
              <button style={tabStyle(activeTab === 'costs')} onClick={() => setActiveTab('costs')}>
                Costs ({filteredCostContexts.length})
              </button>
              <button style={tabStyle(activeTab === 'todos')} onClick={() => setActiveTab('todos')}>
                Todos ({filteredTodoUsage.length})
              </button>
              <button style={tabStyle(activeTab === 'flow')} onClick={() => setActiveTab('flow')}>
                Flow ({filteredTodoFlow.length})
              </button>
              <button style={tabStyle(activeTab === 'trace')} onClick={() => setActiveTab('trace')}>
                Trace ({filteredTraceEvents.length})
              </button>
              <button style={tabStyle(activeTab === 'tools')} onClick={() => setActiveTab('tools')}>
                Tools ({filteredToolUsage.length})
              </button>
              <button style={tabStyle(activeTab === 'rtl')} onClick={() => setActiveTab('rtl')}>
                RTL Runs ({filteredRtlRunHistory.length})
              </button>
              <button style={tabStyle(activeTab === 'versions')} onClick={() => setActiveTab('versions')}>
                Versions ({filteredArtifactVersions.length})
              </button>
              <button style={tabStyle(activeTab === 'run-sets')} onClick={() => setActiveTab('run-sets')}>
                Run Sets ({filteredRunArtifactSets.length})
              </button>
              <button style={tabStyle(activeTab === 'human')} onClick={() => setActiveTab('human')}>
                Human ({filteredInterventions.length})
              </button>
              <button style={tabStyle(activeTab === 'feedback')} onClick={() => setActiveTab('feedback')}>
                Feedback ({filteredFeedback.filter(f => f.status !== 'resolved').length}/{filteredFeedback.length})
              </button>
            </div>

            <div style={filterBarStyle}>
              <label style={filterLabelStyle} htmlFor="admin-filter-range">
                Range
                <select
                  id="admin-filter-range"
                  aria-label="Range"
                  style={selectStyle}
                  value={filters.range}
                  onChange={(e) => setFilter('range', e.target.value)}
                >
                  <option value="24h">Last 24h</option>
                  <option value="7d">Last 7d</option>
                  <option value="30d">Last 30d</option>
                  <option value="all">All time</option>
                </select>
              </label>
              <label style={filterLabelStyle} htmlFor="admin-filter-ip">
                IP
                <select
                  id="admin-filter-ip"
                  aria-label="IP"
                  style={selectStyle}
                  value={filters.ip}
                  onChange={(e) => setFilter('ip', e.target.value)}
                >
                  <option value="">All IPs</option>
                  {filterOptions.ips.map((value) => <option key={value} value={value}>{value}</option>)}
                </select>
              </label>
              <label style={filterLabelStyle} htmlFor="admin-filter-workspace">
                Workspace
                <select
                  id="admin-filter-workspace"
                  aria-label="Workspace"
                  style={selectStyle}
                  value={filters.workspace}
                  onChange={(e) => setFilter('workspace', e.target.value)}
                >
                  <option value="">All workspaces</option>
                  {filterOptions.workspaces.map((value) => <option key={value} value={value}>{value}</option>)}
                </select>
              </label>
              <label style={filterLabelStyle} htmlFor="admin-filter-workflow">
                Workflow
                <select
                  id="admin-filter-workflow"
                  aria-label="Workflow"
                  style={selectStyle}
                  value={filters.workflow}
                  onChange={(e) => setFilter('workflow', e.target.value)}
                >
                  <option value="">All workflows</option>
                  {filterOptions.workflows.map((value) => <option key={value} value={value}>{value}</option>)}
                </select>
              </label>
              <label style={filterLabelStyle} htmlFor="admin-filter-user">
                User
                <select
                  id="admin-filter-user"
                  aria-label="User"
                  style={selectStyle}
                  value={filters.user}
                  onChange={(e) => setFilter('user', e.target.value)}
                >
                  <option value="">All users</option>
                  {filterOptions.users.map((value) => <option key={value} value={value}>{value}</option>)}
                </select>
              </label>
              <label style={filterLabelStyle}>
                Reset
                <button type="button" style={{ ...selectStyle, cursor: 'pointer', color: '#f0c674' }} onClick={clearFilters}>
                  Clear filters
                </button>
              </label>
            </div>

            {activeTab === 'overview' && (
              <>
                <div style={overviewGridStyle}>
                  <div style={metricCardStyle()}>
                    <div style={metricLabelStyle}>Cost</div>
                    <div style={metricValueStyle}>{usd(overview.cost)}</div>
                  </div>
                  <div style={metricCardStyle()}>
                    <div style={metricLabelStyle}>LLM Calls</div>
                    <div style={metricValueStyle}>{fmt(overview.llmCalls)}</div>
                  </div>
                  <div style={metricCardStyle()}>
                    <div style={metricLabelStyle}>Tool Calls</div>
                    <div style={metricValueStyle}>{fmt(overview.toolCalls)}</div>
                  </div>
                  <div style={metricCardStyle(overview.toolFailures ? 'danger' : 'default')}>
                    <div style={metricLabelStyle}>Tool Failures</div>
                    <div style={metricValueStyle}>{fmt(overview.toolFailures)}</div>
                  </div>
                  <div style={metricCardStyle()}>
                    <div style={metricLabelStyle}>Obs Tokens Est</div>
                    <div style={metricValueStyle}>{fmt(overview.obsTokens)}</div>
                  </div>
                  <div style={metricCardStyle(overview.rejectedTodos ? 'danger' : 'default')}>
                    <div style={metricLabelStyle}>Rejected Todos</div>
                    <div style={metricValueStyle}>{fmt(overview.rejectedTodos)}</div>
                  </div>
                  <div style={metricCardStyle(overview.openTodos ? 'danger' : 'default')}>
                    <div style={metricLabelStyle}>Open Todos</div>
                    <div style={metricValueStyle}>{fmt(overview.openTodos)}</div>
                  </div>
                  <div style={metricCardStyle()}>
                    <div style={metricLabelStyle}>RTL Runs</div>
                    <div style={metricValueStyle}>{fmt(overview.rtlRuns)}</div>
                  </div>
                  <div style={metricCardStyle()}>
                    <div style={metricLabelStyle}>Artifact Versions</div>
                    <div style={metricValueStyle}>{fmt(overview.artifactVersions)}</div>
                  </div>
                  <div style={metricCardStyle()}>
                    <div style={metricLabelStyle}>Run Artifact Sets</div>
                    <div style={metricValueStyle}>{fmt(overview.runArtifactSets)}</div>
                  </div>
                  <div style={metricCardStyle()}>
                    <div style={metricLabelStyle}>Human Inputs</div>
                    <div style={metricValueStyle}>{fmt(overview.humanInputs)}</div>
                  </div>
                  <div style={metricCardStyle(overview.pendingHuman ? 'danger' : 'default')}>
                    <div style={metricLabelStyle}>Ask User Pending</div>
                    <div style={metricValueStyle}>{fmt(overview.pendingHuman)}</div>
                  </div>
                  <div style={metricCardStyle(overview.pendingFeedback ? 'danger' : 'default')}>
                    <div style={metricLabelStyle}>Open Feedback</div>
                    <div style={metricValueStyle}>{fmt(overview.pendingFeedback)}</div>
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 430px), 1fr))', gap: 18 }}>
                  <div style={tableWrapStyle}>
                    <div style={panelTitleStyle}>Top Cost Contexts</div>
                    <table style={tableStyle}>
                      <thead>
                        <tr>
                          <th style={thStyle}>IP</th>
                          <th style={thStyle}>Workspace</th>
                          <th style={thStyle}>Workflow</th>
                          <th style={thStyle}>Calls</th>
                          <th style={thStyle}>Cost</th>
                        </tr>
                      </thead>
                      <tbody>
                        {topCostRows.length === 0 ? (
                          <tr><td colSpan={5} style={{ ...tdStyle, ...emptyStateStyle }}>No cost data in filter.</td></tr>
                        ) : topCostRows.map((row) => (
                          <tr key={`${row.session_id}-${row.ip}-${row.workflow}-${row.workspace}`}>
                            <td style={tdStyle}>{row.ip || 'unknown'}</td>
                            <td style={tdStyle}>{row.workspace || 'default'}</td>
                            <td style={tdStyle}>{row.workflow || '—'}</td>
                            <td style={tdStyle}>{fmt(row.calls)}</td>
                            <td style={tdStyle}>{usd(row.cost)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  <div style={tableWrapStyle}>
                    <div style={panelTitleStyle}>Tool Pressure</div>
                    <table style={tableStyle}>
                      <thead>
                        <tr>
                          <th style={thStyle}>Tool</th>
                          <th style={thStyle}>IP</th>
                          <th style={thStyle}>Failures</th>
                          <th style={thStyle}>Obs Tokens</th>
                        </tr>
                      </thead>
                      <tbody>
                        {topToolRows.length === 0 ? (
                          <tr><td colSpan={4} style={{ ...tdStyle, ...emptyStateStyle }}>No tool data in filter.</td></tr>
                        ) : topToolRows.map((row) => (
                          <tr key={`${row.session_id}-${row.ip}-${row.workflow}-${row.tool_name}`}>
                            <td style={tdStyle}>{row.tool_name || '—'}</td>
                            <td style={tdStyle}>{row.ip || 'unknown'}</td>
                            <td style={tdStyle}>{fmt(row.failed_calls)}</td>
                            <td style={tdStyle}>{fmt(row.observation_tokens_est)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  <div style={tableWrapStyle}>
                    <div style={panelTitleStyle}>Rejected Todo Hotspots</div>
                    <table style={tableStyle}>
                      <thead>
                        <tr>
                          <th style={thStyle}>Todo</th>
                          <th style={thStyle}>IP</th>
                          <th style={thStyle}>Rejects</th>
                          <th style={thStyle}>Last Reason</th>
                        </tr>
                      </thead>
                      <tbody>
                        {topRejectedTodos.length === 0 ? (
                          <tr><td colSpan={4} style={{ ...tdStyle, ...emptyStateStyle }}>No rejected todos in filter.</td></tr>
                        ) : topRejectedTodos.map((row) => (
                          <tr key={row.todo_id}>
                            <td style={{ ...tdStyle, maxWidth: 260, whiteSpace: 'normal' }}>{row.content || shortId(row.todo_id)}</td>
                            <td style={tdStyle}>{row.ip || 'unknown'}</td>
                            <td style={tdStyle}>{fmt(row.rejected_count)}</td>
                            <td style={{ ...tdStyle, maxWidth: 320, whiteSpace: 'normal' }}>{row.last_rejected_reason || row.last_event_reason || '—'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  <div style={tableWrapStyle}>
                    <div style={panelTitleStyle}>Human Intervention Hotspots</div>
                    <table style={tableStyle}>
                      <thead>
                        <tr>
                          <th style={thStyle}>User</th>
                          <th style={thStyle}>IP</th>
                          <th style={thStyle}>Workflow</th>
                          <th style={thStyle}>Inputs</th>
                        </tr>
                      </thead>
                      <tbody>
                        {topHumanRows.length === 0 ? (
                          <tr><td colSpan={4} style={{ ...tdStyle, ...emptyStateStyle }}>No human input in filter.</td></tr>
                        ) : topHumanRows.map((row) => (
                          <tr key={`${row.session_id}-${row.ip}-${row.workflow}-${row.username}`}>
                            <td style={tdStyle}>{row.username || 'unknown'}</td>
                            <td style={tdStyle}>{row.ip || 'unknown'}</td>
                            <td style={tdStyle}>{row.workflow || '—'}</td>
                            <td style={tdStyle}>{fmt(row.intervention_count)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </>
            )}

            {activeTab === 'users' && (
              <div style={tableWrapStyle}>
                <table style={tableStyle}>
                  <thead>
                    <tr>
                      <th style={thStyle}>Username</th>
                      <th style={thStyle}>Email</th>
                      <th style={thStyle}>Display Name</th>
                      <th style={thStyle}>Role</th>
                      <th style={thStyle}>Sessions</th>
                      <th style={thStyle}>Created</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredUsers.length === 0 ? (
                      <tr>
                        <td colSpan={6} style={{ ...tdStyle, ...emptyStateStyle }}>No users found.</td>
                      </tr>
                    ) : (
                      filteredUsers.map((u) => (
                        <tr key={u.id}>
                          <td style={tdStyle}>{u.username}</td>
                          <td style={tdStyle}>{u.email || '—'}</td>
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
                    {filteredSessions.length === 0 ? (
                      <tr>
                        <td colSpan={7} style={{ ...tdStyle, ...emptyStateStyle }}>No sessions found.</td>
                      </tr>
                    ) : (
                      filteredSessions.map((s) => (
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
                    {filteredUsage.length === 0 ? (
                      <tr>
                        <td colSpan={9} style={{ ...tdStyle, ...emptyStateStyle }}>No usage data yet.</td>
                      </tr>
                    ) : (
                      filteredUsage.flatMap((u) => {
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
                      {filteredCostContexts.length === 0 ? (
                        <tr>
                          <td colSpan={8} style={{ ...tdStyle, ...emptyStateStyle }}>No cost data yet.</td>
                        </tr>
                      ) : (
                        filteredCostContexts.map((row) => (
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
                      {filteredDateCosts.length === 0 ? (
                        <tr>
                          <td colSpan={6} style={{ ...tdStyle, ...emptyStateStyle }}>No daily cost data yet.</td>
                        </tr>
                      ) : (
                        filteredDateCosts.map((row) => (
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

            {activeTab === 'todos' && (
              <div style={tableWrapStyle}>
                <table style={tableStyle}>
                  <thead>
                    <tr>
                      <th style={thStyle}>IP</th>
                      <th style={thStyle}>Workspace</th>
                      <th style={thStyle}>Workflow</th>
                      <th style={thStyle}>Todo</th>
                      <th style={thStyle}>Status</th>
                      <th style={thStyle}>Rejects</th>
                      <th style={thStyle}>LLM Calls</th>
                      <th style={thStyle}>Tokens</th>
                      <th style={thStyle}>Cost</th>
                      <th style={thStyle}>Last Reason</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredTodoUsage.length === 0 ? (
                      <tr>
                        <td colSpan={10} style={{ ...tdStyle, ...emptyStateStyle }}>No todo usage data yet.</td>
                      </tr>
                    ) : (
                      filteredTodoUsage.map((row) => (
                        <tr key={row.todo_id}>
                          <td style={tdStyle}>{row.ip || 'unknown'}</td>
                          <td style={tdStyle}>{row.workspace || 'default'}</td>
                          <td style={tdStyle}>{row.workflow || '—'}</td>
                          <td style={{ ...tdStyle, minWidth: 240 }}>
                            <div>{row.content || '—'}</div>
                            <div style={{ color: '#8893a3', fontSize: 11, marginTop: 4 }}>
                              {row.detail || row.criteria || '—'}
                            </div>
                          </td>
                          <td style={tdStyle}>{row.status || '—'}</td>
                          <td style={tdStyle}>{fmt(row.rejected_count)}</td>
                          <td style={tdStyle}>{fmt(row.llm_calls)}</td>
                          <td style={tdStyle}>{fmt(row.tokens)}</td>
                          <td style={tdStyle}>{usd(row.cost)}</td>
                          <td style={{ ...tdStyle, maxWidth: 260, whiteSpace: 'normal' }}>
                            {row.last_event_reason || row.last_rejected_reason || '—'}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            )}

            {activeTab === 'flow' && (
              <div style={tableWrapStyle}>
                <table style={tableStyle}>
                  <thead>
                    <tr>
                      <th style={thStyle}>When</th>
                      <th style={thStyle}>IP</th>
                      <th style={thStyle}>Workflow</th>
                      <th style={thStyle}>Todo</th>
                      <th style={thStyle}>Event</th>
                      <th style={thStyle}>Reason</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredTodoFlow.length === 0 ? (
                      <tr>
                        <td colSpan={6} style={{ ...tdStyle, ...emptyStateStyle }}>No todo flow events yet.</td>
                      </tr>
                    ) : (
                      filteredTodoFlow.map((row) => (
                        <tr key={row.event_id}>
                          <td style={tdStyle}>{formatDate(row.created_at)}</td>
                          <td style={tdStyle}>{row.ip || 'unknown'}</td>
                          <td style={tdStyle}>{row.workflow || '—'}</td>
                          <td style={{ ...tdStyle, maxWidth: 300, whiteSpace: 'normal' }}>
                            {row.content || shortId(row.todo_id)}
                          </td>
                          <td style={tdStyle}>{row.event_type || '—'}</td>
                          <td style={{ ...tdStyle, maxWidth: 360, whiteSpace: 'normal' }}>
                            {row.reason || '—'}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            )}

            {activeTab === 'trace' && (
              <div style={tableWrapStyle}>
                <table style={tableStyle}>
                  <thead>
                    <tr>
                      <th style={thStyle}>When</th>
                      <th style={thStyle}>Event</th>
                      <th style={thStyle}>IP</th>
                      <th style={thStyle}>Workspace</th>
                      <th style={thStyle}>Workflow</th>
                      <th style={thStyle}>User</th>
                      <th style={thStyle}>Run</th>
                      <th style={thStyle}>Todo</th>
                      <th style={thStyle}>Correlation</th>
                      <th style={thStyle}>Payload</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredTraceEvents.length === 0 ? (
                      <tr>
                        <td colSpan={10} style={{ ...tdStyle, ...emptyStateStyle }}>No trace events yet.</td>
                      </tr>
                    ) : (
                      filteredTraceEvents.map((row) => (
                        <tr key={row.event_id}>
                          <td style={tdStyle}>{formatDate(row.created_at)}</td>
                          <td style={tdStyle}>{row.event_type || '—'}</td>
                          <td style={tdStyle}>{row.ip || 'unknown'}</td>
                          <td style={tdStyle}>{row.workspace || 'default'}</td>
                          <td style={tdStyle}>{row.workflow || '—'}</td>
                          <td style={tdStyle}>{row.username || shortId(row.actor_user_id)}</td>
                          <td style={tdStyle} title={row.run_id || ''}>{shortId(row.run_id)}</td>
                          <td style={tdStyle} title={row.todo_id || ''}>{shortId(row.todo_id)}</td>
                          <td style={tdStyle} title={row.correlation_id || ''}>{shortId(row.correlation_id)}</td>
                          <td style={{ ...tdStyle, maxWidth: 360, whiteSpace: 'normal', wordBreak: 'break-word' }}>
                            {payloadText(row.payload)}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            )}

            {activeTab === 'tools' && (
              <div style={tableWrapStyle}>
                <table style={tableStyle}>
                  <thead>
                    <tr>
                      <th style={thStyle}>Tool</th>
                      <th style={thStyle}>Calls</th>
                      <th style={thStyle}>Failures</th>
                      <th style={thStyle}>Obs Tokens (est)</th>
                      <th style={thStyle}>Obs Chars</th>
                      <th style={thStyle}>Avg Latency</th>
                      <th style={thStyle}>IP</th>
                      <th style={thStyle}>Workspace</th>
                      <th style={thStyle}>Workflow</th>
                      <th style={thStyle}>Session</th>
                      <th style={thStyle}>User</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredToolUsage.length === 0 ? (
                      <tr>
                        <td colSpan={11} style={{ ...tdStyle, ...emptyStateStyle }}>No tool usage data yet.</td>
                      </tr>
                    ) : (
                      filteredToolUsage.map((row) => (
                        <tr key={`${row.session_id}-${row.ip}-${row.workflow}-${row.tool_name}`}>
                          <td style={tdStyle}>{row.tool_name || '—'}</td>
                          <td style={tdStyle}>{fmt(row.calls)}</td>
                          <td style={tdStyle}>{fmt(row.failed_calls)}</td>
                          <td style={tdStyle}>{fmt(row.observation_tokens_est)}</td>
                          <td style={tdStyle}>{fmt(row.observation_chars)}</td>
                          <td style={tdStyle}>
                            {row.avg_latency_ms == null ? '—' : `${Number(row.avg_latency_ms).toFixed(0)} ms`}
                          </td>
                          <td style={tdStyle}>{row.ip || 'unknown'}</td>
                          <td style={tdStyle}>{row.workspace || 'default'}</td>
                          <td style={tdStyle}>{row.workflow || '—'}</td>
                          <td style={tdStyle} title={row.session_id || ''}>{row.session || shortId(row.session_id)}</td>
                          <td style={tdStyle}>{row.username || 'unknown'}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            )}

            {activeTab === 'rtl' && (
              <div style={tableWrapStyle}>
                <table style={tableStyle}>
                  <thead>
                    <tr>
                      <th style={thStyle}>When</th>
                      <th style={thStyle}>IP</th>
                      <th style={thStyle}>Workspace</th>
                      <th style={thStyle}>Workflow</th>
                      <th style={thStyle}>Status</th>
                      <th style={thStyle}>RTL Version</th>
                      <th style={thStyle}>Git Tag</th>
                      <th style={thStyle}>Tree Hash</th>
                      <th style={thStyle}>Top</th>
                      <th style={thStyle}>LLM Calls</th>
                      <th style={thStyle}>Cost</th>
                      <th style={thStyle}>Error</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredRtlRunHistory.length === 0 ? (
                      <tr>
                        <td colSpan={12} style={{ ...tdStyle, ...emptyStateStyle }}>
                          No RTL-versioned downstream runs yet.
                        </td>
                      </tr>
                    ) : (
                      filteredRtlRunHistory.map((row) => (
                        <tr key={`${row.run_id}-${row.rtl_version_id}`}>
                          <td style={tdStyle}>{formatDate(row.started_at || row.created_at)}</td>
                          <td style={tdStyle}>{row.ip || 'unknown'}</td>
                          <td style={tdStyle}>{row.workspace || 'default'}</td>
                          <td style={tdStyle}>{row.workflow || '—'}</td>
                          <td style={tdStyle}>{row.status || '—'}</td>
                          <td style={tdStyle} title={row.rtl_version_id || ''}>
                            <div>{row.rtl_version || shortId(row.rtl_version_id)}</div>
                            {row.rtl_label && (
                              <div style={{ color: '#8893a3', fontSize: 11, marginTop: 3 }}>
                                {row.rtl_label}
                              </div>
                            )}
                          </td>
                          <td style={{ ...tdStyle, maxWidth: 220, wordBreak: 'break-word' }}>
                            {row.rtl_git_tag || '—'}
                          </td>
                          <td style={tdStyle} title={row.rtl_sha256_tree || ''}>
                            {shortId(row.rtl_sha256_tree)}
                          </td>
                          <td style={tdStyle}>{row.rtl_top_module || '—'}</td>
                          <td style={tdStyle}>{fmt(row.llm_calls)}</td>
                          <td style={tdStyle}>{usd(row.cost)}</td>
                          <td style={{ ...tdStyle, maxWidth: 280, whiteSpace: 'normal' }}>
                            {row.error_summary || '—'}
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            )}

            {activeTab === 'versions' && (
              <div style={tableWrapStyle}>
                <table style={tableStyle}>
                  <thead>
                    <tr>
                      <th style={thStyle}>Created</th>
                      <th style={thStyle}>IP</th>
                      <th style={thStyle}>Workspace</th>
                      <th style={thStyle}>Type</th>
                      <th style={thStyle}>Version</th>
                      <th style={thStyle}>Status</th>
                      <th style={thStyle}>Git Tag</th>
                      <th style={thStyle}>Tree Hash</th>
                      <th style={thStyle}>Primary Path</th>
                      <th style={thStyle}>Source Run</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredArtifactVersions.length === 0 ? (
                      <tr>
                        <td colSpan={10} style={{ ...tdStyle, ...emptyStateStyle }}>
                          No artifact versions yet.
                        </td>
                      </tr>
                    ) : (
                      filteredArtifactVersions.map((row) => (
                        <tr key={row.artifact_version_id}>
                          <td style={tdStyle}>{formatDate(row.created_at)}</td>
                          <td style={tdStyle}>{row.ip || 'unknown'}</td>
                          <td style={tdStyle}>{row.workspace || 'default'}</td>
                          <td style={tdStyle}>{row.artifact_type || '—'}</td>
                          <td style={tdStyle} title={row.artifact_version_id || ''}>{row.version || shortId(row.artifact_version_id)}</td>
                          <td style={tdStyle}>{row.status || '—'}</td>
                          <td style={{ ...tdStyle, maxWidth: 220, wordBreak: 'break-word' }}>{row.git_tag || '—'}</td>
                          <td style={tdStyle} title={row.sha256_tree || ''}>{shortId(row.sha256_tree)}</td>
                          <td style={{ ...tdStyle, maxWidth: 280, wordBreak: 'break-word' }}>
                            {row.primary_path || row.root_path || '—'}
                          </td>
                          <td style={tdStyle} title={row.source_run_id || ''}>{shortId(row.source_run_id)}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            )}

            {activeTab === 'run-sets' && (
              <div style={tableWrapStyle}>
                <table style={tableStyle}>
                  <thead>
                    <tr>
                      <th style={thStyle}>When</th>
                      <th style={thStyle}>IP</th>
                      <th style={thStyle}>Workspace</th>
                      <th style={thStyle}>Workflow</th>
                      <th style={thStyle}>Status</th>
                      <th style={thStyle}>SSOT</th>
                      <th style={thStyle}>RTL</th>
                      <th style={thStyle}>TB</th>
                      <th style={thStyle}>SSOT Anchor</th>
                      <th style={thStyle}>RTL Anchor</th>
                      <th style={thStyle}>TB Anchor</th>
                      <th style={thStyle}>LLM Calls</th>
                      <th style={thStyle}>Cost</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredRunArtifactSets.length === 0 ? (
                      <tr>
                        <td colSpan={13} style={{ ...tdStyle, ...emptyStateStyle }}>
                          No run artifact sets yet.
                        </td>
                      </tr>
                    ) : (
                      filteredRunArtifactSets.map((row) => (
                        <tr key={row.run_id}>
                          <td style={tdStyle}>{formatDate(row.started_at || row.created_at)}</td>
                          <td style={tdStyle}>{row.ip || 'unknown'}</td>
                          <td style={tdStyle}>{row.workspace || 'default'}</td>
                          <td style={tdStyle}>{row.workflow || '—'}</td>
                          <td style={tdStyle}>{row.status || '—'}</td>
                          <td style={tdStyle}>{versionText(row, 'ssot')}</td>
                          <td style={tdStyle}>{versionText(row, 'rtl')}</td>
                          <td style={tdStyle}>{versionText(row, 'tb')}</td>
                          <td style={{ ...tdStyle, maxWidth: 220, wordBreak: 'break-word' }}>{versionTagText(row, 'ssot')}</td>
                          <td style={{ ...tdStyle, maxWidth: 220, wordBreak: 'break-word' }}>{versionTagText(row, 'rtl')}</td>
                          <td style={{ ...tdStyle, maxWidth: 220, wordBreak: 'break-word' }}>{versionTagText(row, 'tb')}</td>
                          <td style={tdStyle}>{fmt(row.llm_calls)}</td>
                          <td style={tdStyle}>{usd(row.cost)}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            )}

            {activeTab === 'human' && (
              <div style={tableWrapStyle}>
                <table style={tableStyle}>
                  <thead>
                    <tr>
                      <th style={thStyle}>User</th>
                      <th style={thStyle}>Session</th>
                      <th style={thStyle}>IP</th>
                      <th style={thStyle}>Workspace</th>
                      <th style={thStyle}>Workflow</th>
                      <th style={thStyle}>Total</th>
                      <th style={thStyle}>Prompts</th>
                      <th style={thStyle}>Chat</th>
                      <th style={thStyle}>Ask User</th>
                      <th style={thStyle}>SSOT QA</th>
                      <th style={thStyle}>Last</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredInterventions.length === 0 ? (
                      <tr>
                        <td colSpan={11} style={{ ...tdStyle, ...emptyStateStyle }}>No human intervention data yet.</td>
                      </tr>
                    ) : (
                      filteredInterventions.map((row) => (
                        <tr key={`${row.session_id}-${row.ip}-${row.workflow}-${row.username}`}>
                          <td style={tdStyle}>{row.username || 'unknown'}</td>
                          <td style={tdStyle} title={row.session_id || ''}>{row.session || shortId(row.session_id)}</td>
                          <td style={tdStyle}>{row.ip || 'unknown'}</td>
                          <td style={tdStyle}>{row.workspace || 'default'}</td>
                          <td style={tdStyle}>{row.workflow || '—'}</td>
                          <td style={tdStyle}>{fmt(row.intervention_count)}</td>
                          <td style={tdStyle}>{fmt(row.user_messages)}</td>
                          <td style={tdStyle}>{fmt(row.chat_messages)}</td>
                          <td style={tdStyle}>{fmt(row.ask_user_answers)}</td>
                          <td style={tdStyle}>{fmt(row.ssot_qa_answers)}</td>
                          <td style={tdStyle}>{formatDate(row.last_intervention_at)}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
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
                    {filteredFeedback.length === 0 ? (
                      <tr>
                        <td colSpan={7} style={{ ...tdStyle, ...emptyStateStyle }}>
                          No feedback yet. Users can submit with <code>/feedback &lt;message&gt;</code> in the chat.
                        </td>
                      </tr>
                    ) : (
                      filteredFeedback.map((f) => {
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
