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
  const [workflowStages, setWorkflowStages] = React.useState([]);
  const [interventions, setInterventions] = React.useState([]);
  const [rtlRunHistory, setRtlRunHistory] = React.useState([]);
  const [artifactVersions, setArtifactVersions] = React.useState([]);
  const [runArtifactSets, setRunArtifactSets] = React.useState([]);
  const [feedback, setFeedback] = React.useState([]);
  const [memoryRules, setMemoryRules] = React.useState([]);
  const [inputHistory, setInputHistory] = React.useState([]);
  const [adminChatMessages, setAdminChatMessages] = React.useState([
    {
      role: 'assistant',
      content: 'Ask about feedback, user inputs, tool calls, cost, daily usage, models, workflows, IPs, or memory rules.',
    },
  ]);
  const [adminChatDraft, setAdminChatDraft] = React.useState('');
  const [adminChatLoading, setAdminChatLoading] = React.useState(false);
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
  const [dbTables, setDbTables] = React.useState([]);
  const [dbSelectedTable, setDbSelectedTable] = React.useState(null);
  const [dbPage, setDbPage] = React.useState({ columns: [], rows: [], total: 0, limit: 50, offset: 0 });
  const [dbLoading, setDbLoading] = React.useState(false);
  const [dbError, setDbError] = React.useState(null);
  const [dbExpandedRow, setDbExpandedRow] = React.useState(null);
  const [dbOverview, setDbOverview] = React.useState([]);
  const [dbOverviewLoading, setDbOverviewLoading] = React.useState(false);
  const [dbHideEmpty, setDbHideEmpty] = React.useState(true);

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
      setWorkflowStages(usageData.workflow_stages || []);
      setInterventions(usageData.interventions || []);
      setRtlRunHistory(usageData.rtl_run_history || []);
      setArtifactVersions(usageData.artifact_versions || []);
      setRunArtifactSets(usageData.run_artifact_sets || []);
      setMemoryRules(usageData.memory_rules || []);
      setInputHistory(usageData.input_history || []);
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
    setMemoryRules([]);
    setInputHistory([]);
    setLoading(false);
  };

  const loadDbTables = React.useCallback(async () => {
    setDbError(null);
    try {
      const r = await fetch('/api/admin/db/tables');
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const d = await r.json();
      setDbTables(d.tables || []);
    } catch (e) {
      setDbError(String(e));
    }
  }, []);

  const loadDbTable = React.useCallback(async (name, offset = 0, limit = 50) => {
    if (!name) return;
    setDbLoading(true);
    setDbError(null);
    setDbExpandedRow(null);
    try {
      const url = `/api/admin/db/table/${encodeURIComponent(name)}?limit=${limit}&offset=${offset}`;
      const r = await fetch(url);
      if (!r.ok) {
        let detail = `HTTP ${r.status}`;
        try { const b = await r.json(); detail = b.error || detail; } catch (_) {}
        throw new Error(detail);
      }
      const d = await r.json();
      setDbPage({
        columns: d.columns || [],
        rows: d.rows || [],
        total: d.total || 0,
        limit: d.limit || limit,
        offset: d.offset || offset,
      });
    } catch (e) {
      setDbError(String(e));
    } finally {
      setDbLoading(false);
    }
  }, []);

  const loadDbOverview = React.useCallback(async () => {
    setDbOverviewLoading(true);
    setDbError(null);
    try {
      const r = await fetch('/api/admin/db/preview?per_table=3');
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const d = await r.json();
      setDbOverview(d.tables || []);
    } catch (e) {
      setDbError(String(e));
    } finally {
      setDbOverviewLoading(false);
    }
  }, []);

  React.useEffect(() => {
    if (activeTab !== 'raw-db' || !authUser) return;
    if (dbTables.length === 0) loadDbTables();
    if (dbOverview.length === 0 && !dbSelectedTable) loadDbOverview();
  }, [activeTab, authUser, dbTables.length, dbOverview.length, dbSelectedTable, loadDbTables, loadDbOverview]);

  React.useEffect(() => {
    if (activeTab !== 'raw-db' || !dbSelectedTable) return;
    loadDbTable(dbSelectedTable, 0, dbPage.limit || 50);
    // dbPage.limit captured intentionally on table-change only
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dbSelectedTable, activeTab]);

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

  const handleAdminChatSubmit = async (ev) => {
    ev.preventDefault();
    const text = String(adminChatDraft || '').trim();
    if (!text || adminChatLoading) return;
    setAdminChatDraft('');
    setAdminChatMessages((prev) => [...prev, { role: 'user', content: text }]);
    setAdminChatLoading(true);
    try {
      const r = await fetch('/api/admin/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text }),
      });
      let body = {};
      try { body = await r.json(); } catch (_) {}
      if (!r.ok) throw new Error(body.error || `HTTP ${r.status}`);
      setAdminChatMessages((prev) => [...prev, {
        role: 'assistant',
        content: body.answer || 'No matching DB rows.',
        sections: body.sections || [],
      }]);
    } catch (e) {
      setAdminChatMessages((prev) => [...prev, { role: 'assistant', content: `Error: ${String(e)}` }]);
    } finally {
      setAdminChatLoading(false);
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

  const dashboardGridStyle = {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 420px), 1fr))',
    gap: 14,
  };

  const dashboardWideStyle = {
    gridColumn: '1 / -1',
  };

  const widgetHeaderStyle = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: 12,
    padding: '11px 14px',
    borderBottom: '1px solid #2a3540',
    background: '#1c252f',
  };

  const widgetTitleStyle = {
    color: '#f0c674',
    fontSize: 12,
    fontWeight: 700,
    textTransform: 'uppercase',
    letterSpacing: '0.06em',
  };

  const widgetMetaStyle = {
    color: '#8893a3',
    fontSize: 11,
    whiteSpace: 'nowrap',
  };

  const barTrackStyle = {
    height: 8,
    borderRadius: 4,
    background: '#0f151b',
    border: '1px solid #2a3540',
    overflow: 'hidden',
  };

  const barFillStyle = (width, tone = 'default') => ({
    height: '100%',
    width,
    minWidth: width === '0%' ? 0 : 4,
    background: tone === 'cost' ? '#f0c674' : '#7dc9a0',
  });

  const mutedSmallStyle = {
    color: '#8893a3',
    fontSize: 11,
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
  const durationMs = (n) => {
    const value = Number(n || 0);
    if (!value) return '—';
    if (value < 1000) return `${value.toFixed(0)} ms`;
    return `${(value / 1000).toFixed(1)} s`;
  };
  const shortId = (value) => String(value || '').slice(0, 8) || '—';
  const sessionDisplay = (rowOrId) => {
    const row = rowOrId && typeof rowOrId === 'object' ? rowOrId : { session_id: rowOrId };
    const sessionId = String(row.session_id || row.id || '').trim();
    if (sessionId.includes('/')) return sessionId;
    const label = String(row.session || '').trim();
    return label || shortId(sessionId);
  };
  const keyPart = (value) => {
    if (value === null || value === undefined || value === '') return 'empty';
    try {
      const text = typeof value === 'object' ? JSON.stringify(value) : String(value);
      return text.replace(/\s+/g, ' ').slice(0, 120) || 'empty';
    } catch (_) {
      return 'value';
    }
  };
  const rowKey = (scope, index, ...parts) => (
    [scope, ...parts.map(keyPart), index].join(':')
  );
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
  const statusPillStyle = (status) => {
    const value = String(status || '').toLowerCase();
    const tone = (
      value === 'passed' || value === 'completed' || value === 'success' ? 'ok'
        : value === 'failed' || value === 'error' ? 'bad'
          : value === 'running' ? 'run'
            : value === 'blocked' ? 'warn'
              : 'idle'
    );
    const palette = {
      ok: ['#1c2f25', '#7dc9a0'],
      bad: ['#3a1f24', '#e06c75'],
      run: ['#1f2a3a', '#82aaff'],
      warn: ['#3a3120', '#f0c674'],
      idle: ['#1c252f', '#a3aebb'],
    }[tone];
    return {
      fontSize: 10,
      fontWeight: 600,
      textTransform: 'uppercase',
      padding: '2px 6px',
      borderRadius: 3,
      background: palette[0],
      color: palette[1],
      border: '1px solid #2a3540',
    };
  };
  const sum = (rows, key) => rows.reduce((acc, row) => acc + Number(row[key] || 0), 0);
  const rowTimestamp = (row) => {
    const direct = row.active_session_updated_at || row.last_message_at || row.last_event_at || row.last_tool_at
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
  const sessionContextRows = sessions.map((s) => ({
    username: s.owner_username || s.user_id,
    ip: s.ip || s.project_id || '',
    workflow: s.workflow || s.latest_workflow || '',
    created_at: s.created_at,
    updated_at: s.updated_at,
  }));
  const userFocusContextRows = users.map((u) => ({
    username: u.username,
    ip: u.active_ip || '',
    workflow: u.active_workflow || '',
    updated_at: u.active_session_updated_at,
  }));
  const allContextRows = [
    ...costContexts,
    ...dateCosts,
    ...todoUsage,
    ...todoFlow,
    ...traceEvents,
    ...toolUsage,
    ...workflowStages,
    ...interventions,
    ...rtlRunHistory,
    ...artifactVersions,
    ...runArtifactSets,
    ...memoryRules,
    ...inputHistory,
    ...sessionContextRows,
    ...userFocusContextRows,
  ];
  const filterOptions = {
    ips: uniqueOptions(allContextRows, 'ip'),
    workspaces: uniqueOptions(allContextRows, 'workspace'),
    workflows: uniqueOptions(allContextRows, 'workflow'),
    users: uniqueOptions([
      ...allContextRows,
      ...usage,
      ...feedback,
      ...memoryRules,
      ...inputHistory,
    ], 'username'),
  };
  const filteredUsers = users.filter((row) => (
    valueMatches(filters.user, row.username)
    && valueMatches(filters.ip, row.active_ip)
    && !filters.workspace
    && valueMatches(filters.workflow, row.active_workflow)
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
    && valueMatches(filters.ip, row.ip || row.project_id || row.title)
    && !filters.workspace
    && valueMatches(filters.workflow, row.workflow || row.latest_workflow)
  ));
  const filteredCostContexts = costContexts.filter(rowMatches);
  const filteredDateCosts = dateCosts.filter(rowMatches);
  const filteredTodoUsage = todoUsage.filter(rowMatches);
  const filteredTodoFlow = todoFlow.filter(rowMatches);
  const filteredTraceEvents = traceEvents.filter(rowMatches);
  const filteredToolUsage = toolUsage.filter(rowMatches);
  const filteredWorkflowStages = workflowStages.filter(rowMatches);
  const filteredInterventions = interventions.filter(rowMatches);
  const filteredRtlRunHistory = rtlRunHistory.filter(rowMatches);
  const filteredArtifactVersions = artifactVersions.filter(rowMatches);
  const filteredRunArtifactSets = runArtifactSets.filter(rowMatches);
  const filteredMemoryRules = memoryRules.filter((row) => (
    inRange(row)
    && valueMatches(filters.user, row.username)
    && !filters.ip
    && !filters.workspace
    && valueMatches(filters.workflow, row.workflow)
  ));
  const filteredInputHistory = inputHistory.filter(rowMatches);
  const filteredFeedback = feedback.filter((row) => (
    inRange(row)
    && valueMatches(filters.user, row.username)
    && !filters.ip
    && !filters.workspace
    && !filters.workflow
  ));
  const sessionWorkloadRows = filteredSessions.map((s) => ({
    username: s.owner_username || s.user_id || 'unknown',
    ip: s.ip || s.project_id || s.title || 'unknown',
    workflow: s.workflow || s.latest_workflow || '',
    session_id: s.id,
    calls: 0,
    tokens: 0,
    cost: 0,
    updated_at: s.updated_at,
  }));
  const workloadContextRows = [...filteredCostContexts, ...sessionWorkloadRows];
  const workloadScore = (row) => Number(row.cost || 0) || Number(row.calls || 0) || Number(row.sessionCount || 0);
  const aggregateWorkload = (rows, key, fallback) => {
    const grouped = new Map();
    rows.forEach((row) => {
      const name = String(row[key] || '').trim() || fallback;
      if (!grouped.has(name)) {
        grouped.set(name, {
          name,
          calls: 0,
          tokens: 0,
          cost: 0,
          sessionIds: new Set(),
          users: new Set(),
          lastAt: 0,
        });
      }
      const item = grouped.get(name);
      item.calls += Number(row.calls || 0);
      item.tokens += Number(row.tokens || 0);
      item.cost += Number(row.cost || 0);
      if (row.session_id) item.sessionIds.add(row.session_id);
      if (row.username || row.owner_username) item.users.add(row.username || row.owner_username);
      item.lastAt = Math.max(item.lastAt, rowTimestamp(row));
    });
    return Array.from(grouped.values())
      .map((row) => ({
        ...row,
        sessionCount: row.sessionIds.size,
        userCount: row.users.size,
        userList: Array.from(row.users).sort(),
      }))
      .sort((a, b) => workloadScore(b) - workloadScore(a) || b.lastAt - a.lastAt || a.name.localeCompare(b.name));
  };
  const activeUserRows = [...filteredUsers]
    .filter((row) => (row.active_ip || row.active_workflow) && inRange(row))
    .sort((a, b) => rowTimestamp(b) - rowTimestamp(a) || String(a.username || '').localeCompare(String(b.username || '')))
    .slice(0, 8);
  const recentSessionRows = [...filteredSessions]
    .sort((a, b) => rowTimestamp(b) - rowTimestamp(a))
    .slice(0, 8);
  const ipWorkloadRows = aggregateWorkload(workloadContextRows, 'ip', 'unknown').slice(0, 8);
  const workflowWorkloadRows = aggregateWorkload(workloadContextRows, 'workflow', 'unassigned').slice(0, 8);
  const maxIpScore = Math.max(1, ...ipWorkloadRows.map(workloadScore));
  const maxWorkflowScore = Math.max(1, ...workflowWorkloadRows.map(workloadScore));
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
  const recentStageRows = [...filteredWorkflowStages]
    .sort((a, b) => rowTimestamp(b) - rowTimestamp(a))
    .slice(0, 8);
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
    activeUsers: filteredUsers.filter((row) => (row.active_ip || row.active_workflow) && inRange(row)).length,
    activeSessions: filteredSessions.filter((row) => String(row.status || '').toLowerCase() === 'active').length,
    workflowStages: filteredWorkflowStages.length,
    activeIps: new Set(filteredSessions
      .filter((row) => String(row.status || '').toLowerCase() === 'active')
      .map((row) => row.ip || row.project_id || row.title)
      .filter(Boolean)).size,
    cost: sum(filteredCostContexts, 'cost'),
    llmCalls: sum(filteredCostContexts, 'calls'),
    toolCalls: sum(filteredToolUsage, 'calls'),
    toolFailures: sum(filteredToolUsage, 'failed_calls'),
    obsTokens: sum(filteredToolUsage, 'observation_tokens_est'),
    rejectedTodos: sum(filteredTodoUsage, 'rejected_count'),
    openTodos: filteredTodoUsage.filter((row) => !['approved', 'completed'].includes(String(row.status || '').toLowerCase())).length,
    humanInputs: sum(filteredInterventions, 'intervention_count'),
    inputRows: filteredInputHistory.length,
    memoryRules: filteredMemoryRules.length,
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
              <button style={tabStyle(activeTab === 'stages')} onClick={() => setActiveTab('stages')}>
                Stages ({filteredWorkflowStages.length})
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
              <button style={tabStyle(activeTab === 'inputs')} onClick={() => setActiveTab('inputs')}>
                Inputs ({filteredInputHistory.length})
              </button>
              <button style={tabStyle(activeTab === 'memory')} onClick={() => setActiveTab('memory')}>
                Memory ({filteredMemoryRules.length})
              </button>
              <button style={tabStyle(activeTab === 'feedback')} onClick={() => setActiveTab('feedback')}>
                Feedback ({filteredFeedback.filter(f => f.status !== 'resolved').length}/{filteredFeedback.length})
              </button>
              <button style={tabStyle(activeTab === 'admin-chat')} onClick={() => setActiveTab('admin-chat')}>
                Admin Chat
              </button>
              <button style={tabStyle(activeTab === 'raw-db')} onClick={() => setActiveTab('raw-db')}>
                Raw DB
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
                    <div style={metricLabelStyle}>Active Users</div>
                    <div style={metricValueStyle}>{fmt(overview.activeUsers)}</div>
                  </div>
                  <div style={metricCardStyle()}>
                    <div style={metricLabelStyle}>Active IPs</div>
                    <div style={metricValueStyle}>{fmt(overview.activeIps)}</div>
                  </div>
                  <div style={metricCardStyle()}>
                    <div style={metricLabelStyle}>Active Sessions</div>
                    <div style={metricValueStyle}>{fmt(overview.activeSessions)}</div>
                  </div>
                  <div style={metricCardStyle()}>
                    <div style={metricLabelStyle}>Workflow Stages</div>
                    <div style={metricValueStyle}>{fmt(overview.workflowStages)}</div>
                  </div>
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
                  <div style={metricCardStyle()}>
                    <div style={metricLabelStyle}>Input History</div>
                    <div style={metricValueStyle}>{fmt(overview.inputRows)}</div>
                  </div>
                  <div style={metricCardStyle()}>
                    <div style={metricLabelStyle}>Memory Rules</div>
                    <div style={metricValueStyle}>{fmt(overview.memoryRules)}</div>
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

                <div style={dashboardGridStyle}>
                  <div style={{ ...tableWrapStyle, ...dashboardWideStyle }}>
                    <div style={widgetHeaderStyle}>
                      <div style={widgetTitleStyle}>Active User Focus</div>
                      <div style={widgetMetaStyle}>User · IP · Workflow · session</div>
                    </div>
                    <table style={tableStyle}>
                      <thead>
                        <tr>
                          <th style={thStyle}>User</th>
                          <th style={thStyle}>Active IP</th>
                          <th style={thStyle}>Active Workflow</th>
                          <th style={thStyle}>Sessions</th>
                          <th style={thStyle}>Status</th>
                          <th style={thStyle}>Updated</th>
                        </tr>
                      </thead>
                      <tbody>
                        {activeUserRows.length === 0 ? (
                          <tr><td colSpan={6} style={{ ...tdStyle, ...emptyStateStyle }}>No active user focus in filter.</td></tr>
                        ) : activeUserRows.map((row, index) => (
                          <tr key={rowKey('active-user', index, row.id, row.username)}>
                            <td style={tdStyle}>{row.username || 'unknown'}</td>
                            <td style={tdStyle}>{row.active_ip || '—'}</td>
                            <td style={tdStyle}>{row.active_workflow || '—'}</td>
                            <td style={tdStyle}>{fmt(row.session_count || 0)}</td>
                            <td style={tdStyle}>{row.active_workflow_status || 'active'}</td>
                            <td style={tdStyle}>{formatDate(row.active_session_updated_at)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  <div style={tableWrapStyle}>
                    <div style={widgetHeaderStyle}>
                      <div style={widgetTitleStyle}>IP Workload</div>
                      <div style={widgetMetaStyle}>cost weighted</div>
                    </div>
                    <table style={tableStyle}>
                      <thead>
                        <tr>
                          <th style={thStyle}>IP</th>
                          <th style={thStyle}>Load</th>
                          <th style={thStyle}>Calls</th>
                          <th style={thStyle}>Cost</th>
                          <th style={thStyle}>Users</th>
                        </tr>
                      </thead>
                      <tbody>
                        {ipWorkloadRows.length === 0 ? (
                          <tr><td colSpan={5} style={{ ...tdStyle, ...emptyStateStyle }}>No IP workload in filter.</td></tr>
                        ) : ipWorkloadRows.map((row, index) => {
                          const width = `${Math.round((workloadScore(row) / maxIpScore) * 100)}%`;
                          return (
                            <tr key={rowKey('ip-workload', index, row.name)}>
                              <td style={tdStyle}>{row.name}</td>
                              <td style={{ ...tdStyle, minWidth: 120 }}>
                                <div style={barTrackStyle}><div style={barFillStyle(width, 'cost')} /></div>
                                <div style={mutedSmallStyle}>{fmt(row.sessionCount)} sessions · {fmt(row.tokens)} tokens</div>
                              </td>
                              <td style={tdStyle}>{fmt(row.calls)}</td>
                              <td style={tdStyle}>{usd(row.cost)}</td>
                              <td style={tdStyle}>{fmt(row.userCount)}</td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>

                  <div style={tableWrapStyle}>
                    <div style={widgetHeaderStyle}>
                      <div style={widgetTitleStyle}>Workflow Load</div>
                      <div style={widgetMetaStyle}>single/orchestrator aware</div>
                    </div>
                    <table style={tableStyle}>
                      <thead>
                        <tr>
                          <th style={thStyle}>Workflow</th>
                          <th style={thStyle}>Load</th>
                          <th style={thStyle}>Calls</th>
                          <th style={thStyle}>Cost</th>
                          <th style={thStyle}>Sessions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {workflowWorkloadRows.length === 0 ? (
                          <tr><td colSpan={5} style={{ ...tdStyle, ...emptyStateStyle }}>No workflow load in filter.</td></tr>
                        ) : workflowWorkloadRows.map((row, index) => {
                          const width = `${Math.round((workloadScore(row) / maxWorkflowScore) * 100)}%`;
                          return (
                            <tr key={rowKey('workflow-workload', index, row.name)}>
                              <td style={tdStyle}>{row.name}</td>
                              <td style={{ ...tdStyle, minWidth: 120 }}>
                                <div style={barTrackStyle}><div style={barFillStyle(width)} /></div>
                                <div style={mutedSmallStyle}>{fmt(row.userCount)} users · {fmt(row.tokens)} tokens</div>
                              </td>
                              <td style={tdStyle}>{fmt(row.calls)}</td>
                              <td style={tdStyle}>{usd(row.cost)}</td>
                              <td style={tdStyle}>{fmt(row.sessionCount)}</td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>

                  <div style={{ ...tableWrapStyle, ...dashboardWideStyle }}>
                    <div style={widgetHeaderStyle}>
                      <div style={widgetTitleStyle}>Recent Sessions</div>
                      <div style={widgetMetaStyle}>latest active context</div>
                    </div>
                    <table style={tableStyle}>
                      <thead>
                        <tr>
                          <th style={thStyle}>Owner</th>
                          <th style={thStyle}>IP</th>
                          <th style={thStyle}>Workflow</th>
                          <th style={thStyle}>Status</th>
                          <th style={thStyle}>Session</th>
                          <th style={thStyle}>Updated</th>
                        </tr>
                      </thead>
                      <tbody>
                        {recentSessionRows.length === 0 ? (
                          <tr><td colSpan={6} style={{ ...tdStyle, ...emptyStateStyle }}>No sessions in filter.</td></tr>
                        ) : recentSessionRows.map((row, index) => (
                          <tr key={rowKey('recent-session', index, row.id, row.owner_username, row.ip, row.workflow)}>
                            <td style={tdStyle}>{row.owner_username || row.user_id || 'unknown'}</td>
                            <td style={tdStyle}>{row.ip || row.project_id || '—'}</td>
                            <td style={tdStyle}>{row.workflow || row.latest_workflow || '—'}</td>
                            <td style={tdStyle}>{row.status || '—'}</td>
                            <td
                              style={{ ...tdStyle, fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace', fontSize: 11, maxWidth: 260, wordBreak: 'break-word' }}
                              title={row.id || ''}
                            >
                              {sessionDisplay(row)}
                            </td>
                            <td style={tdStyle}>{formatDate(row.updated_at)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  <div style={{ ...tableWrapStyle, ...dashboardWideStyle }}>
                    <div style={widgetHeaderStyle}>
                      <div style={widgetTitleStyle}>Recent Stages</div>
                      <div style={widgetMetaStyle}>run stage status by IP/workflow</div>
                    </div>
                    <table style={tableStyle}>
                      <thead>
                        <tr>
                          <th style={thStyle}>IP</th>
                          <th style={thStyle}>Workflow</th>
                          <th style={thStyle}>Stage</th>
                          <th style={thStyle}>Status</th>
                          <th style={thStyle}>Attempt</th>
                          <th style={thStyle}>Duration</th>
                          <th style={thStyle}>Updated</th>
                        </tr>
                      </thead>
                      <tbody>
                        {recentStageRows.length === 0 ? (
                          <tr><td colSpan={7} style={{ ...tdStyle, ...emptyStateStyle }}>No workflow stage rows in filter.</td></tr>
                        ) : recentStageRows.map((row, index) => (
                          <tr key={rowKey('recent-stage', index, row.stage_id, row.run_id, row.stage_name)}>
                            <td style={tdStyle}>{row.ip || 'unknown'}</td>
                            <td style={tdStyle}>{row.workflow || '—'}</td>
                            <td style={tdStyle}>{row.stage_name || '—'}</td>
                            <td style={tdStyle}><span style={statusPillStyle(row.status)}>{row.status || 'unknown'}</span></td>
                            <td style={tdStyle}>{fmt(row.attempt)}</td>
                            <td style={tdStyle}>{durationMs(row.duration_ms)}</td>
                            <td style={tdStyle}>{formatDate(row.updated_at || row.ended_at || row.started_at)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
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
                        ) : topCostRows.map((row, index) => (
                          <tr key={rowKey('top-cost', index, row.session_id, row.ip, row.workflow, row.workspace)}>
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
                        ) : topToolRows.map((row, index) => (
                          <tr key={rowKey('top-tool', index, row.session_id, row.ip, row.workflow, row.tool_name)}>
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
                        ) : topRejectedTodos.map((row, index) => (
                          <tr key={rowKey('top-rejected-todo', index, row.todo_id, row.ip, row.workflow)}>
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
                        ) : topHumanRows.map((row, index) => (
                          <tr key={rowKey('top-human', index, row.session_id, row.ip, row.workflow, row.username)}>
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
                      <th style={thStyle}>Active IP</th>
                      <th style={thStyle}>Active Workflow</th>
                      <th style={thStyle}>Sessions</th>
                      <th style={thStyle}>Active Updated</th>
                      <th style={thStyle}>Created</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredUsers.length === 0 ? (
                      <tr>
                        <td colSpan={9} style={{ ...tdStyle, ...emptyStateStyle }}>No users found.</td>
                      </tr>
                    ) : (
                      filteredUsers.map((u, index) => (
                        <tr key={rowKey('user', index, u.id, u.username)}>
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
                          <td style={tdStyle}>{u.active_ip || '—'}</td>
                          <td style={tdStyle}>
                            {u.active_workflow || '—'}
                            {u.active_workflow_status ? (
                              <div style={{ opacity: 0.65, fontSize: 11 }}>{u.active_workflow_status}</div>
                            ) : null}
                          </td>
                          <td style={tdStyle}>{u.session_count ?? 0}</td>
                          <td style={tdStyle}>{formatDate(u.active_session_updated_at)}</td>
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
                      <th style={thStyle}>IP</th>
                      <th style={thStyle}>Workflow</th>
                      <th style={thStyle}>Status</th>
                      <th style={thStyle}>Owner</th>
                      <th style={thStyle}>Session</th>
                      <th style={thStyle}>Latest Run</th>
                      <th style={thStyle}>Updated</th>
                      <th style={thStyle}></th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredSessions.length === 0 ? (
                      <tr>
                        <td colSpan={9} style={{ ...tdStyle, ...emptyStateStyle }}>No sessions found.</td>
                      </tr>
                    ) : (
                      filteredSessions.map((s, index) => (
                        <tr key={rowKey('session', index, s.id, s.user_id, s.ip, s.workflow)}>
                          <td style={tdStyle}>{s.title || '—'}</td>
                          <td style={tdStyle}>{s.ip || s.project_id || '—'}</td>
                          <td style={tdStyle}>{s.workflow || s.latest_workflow || '—'}</td>
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
                          <td style={{ ...tdStyle, fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace', fontSize: 11 }}>
                            {s.id || '—'}
                          </td>
                          <td style={tdStyle}>
                            {s.pipeline_run_id || s.latest_workflow_run_id || '—'}
                            {s.latest_workflow_status ? (
                              <div style={{ opacity: 0.65, fontSize: 11 }}>{s.latest_workflow_status}</div>
                            ) : null}
                          </td>
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

            {activeTab === 'stages' && (
              <div style={tableWrapStyle}>
                <table style={tableStyle}>
                  <thead>
                    <tr>
                      <th style={thStyle}>When</th>
                      <th style={thStyle}>User</th>
                      <th style={thStyle}>IP</th>
                      <th style={thStyle}>Workspace</th>
                      <th style={thStyle}>Workflow</th>
                      <th style={thStyle}>Stage</th>
                      <th style={thStyle}>Status</th>
                      <th style={thStyle}>Attempt</th>
                      <th style={thStyle}>Duration</th>
                      <th style={thStyle}>Run</th>
                      <th style={thStyle}>LLM</th>
                      <th style={thStyle}>Cost</th>
                      <th style={thStyle}>Error</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredWorkflowStages.length === 0 ? (
                      <tr>
                        <td colSpan={13} style={{ ...tdStyle, ...emptyStateStyle }}>No workflow stage rows yet.</td>
                      </tr>
                    ) : (
                      filteredWorkflowStages.map((row, index) => (
                        <tr key={rowKey('workflow-stage', index, row.stage_id, row.run_id, row.stage_name)}>
                          <td style={tdStyle}>{formatDate(row.started_at || row.created_at)}</td>
                          <td style={tdStyle}>{row.username || 'unknown'}</td>
                          <td style={tdStyle}>{row.ip || 'unknown'}</td>
                          <td style={tdStyle}>{row.workspace || 'default'}</td>
                          <td style={tdStyle}>{row.workflow || '—'}</td>
                          <td style={tdStyle}>
                            <div>{row.stage_name || '—'}</div>
                            {row.trigger_source && (
                              <div style={{ color: '#8893a3', fontSize: 11, marginTop: 3 }}>
                                {row.trigger_source}
                              </div>
                            )}
                          </td>
                          <td style={tdStyle}><span style={statusPillStyle(row.status)}>{row.status || 'unknown'}</span></td>
                          <td style={tdStyle}>{fmt(row.attempt)}</td>
                          <td style={tdStyle}>{durationMs(row.duration_ms)}</td>
                          <td style={tdStyle} title={row.run_id || ''}>{shortId(row.run_id)}</td>
                          <td style={tdStyle}>{fmt(row.llm_calls)}</td>
                          <td style={tdStyle}>{usd(row.cost)}</td>
                          <td style={{ ...tdStyle, maxWidth: 300, whiteSpace: 'normal' }}>
                            {row.error_summary || '—'}
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
                      filteredUsage.flatMap((u, index) => {
                        const expanded = expandedUsage === u.user_id;
                        const rows = [
                          <tr key={rowKey('usage', index, u.user_id, u.username)}
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
                            <tr key={rowKey('usage-detail', index, u.user_id, u.username)}>
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
                                          {u.models.slice(0, 8).map((m, modelIndex) => (
                                            <tr key={rowKey('usage-model', modelIndex, u.user_id, m.model_id)}>
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
                                          {u.tools.slice(0, 10).map((t, toolIndex) => (
                                            <tr key={rowKey('usage-tool', toolIndex, u.user_id, t.tool_name)}>
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
                        filteredCostContexts.map((row, index) => (
                          <tr key={rowKey('cost-context', index, row.session_id, row.ip, row.workspace, row.username)}>
                            <td style={tdStyle}>{row.ip || 'unknown'}</td>
                            <td style={tdStyle}>{row.workspace || 'default'}</td>
                            <td style={tdStyle} title={row.session_id || ''}>
                              {sessionDisplay(row)}
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
                        filteredDateCosts.map((row, index) => (
                          <tr key={rowKey('date-cost', index, row.day, row.session_id, row.ip, row.workspace)}>
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
                      filteredTodoUsage.map((row, index) => (
                        <tr key={rowKey('todo-usage', index, row.todo_id, row.ip, row.workflow)}>
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
                      filteredTodoFlow.map((row, index) => (
                        <tr key={rowKey('todo-flow', index, row.event_id, row.todo_id, row.event_type)}>
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
                      filteredTraceEvents.map((row, index) => (
                        <tr key={rowKey('trace-event', index, row.event_id, row.correlation_id, row.event_type)}>
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
                      filteredToolUsage.map((row, index) => (
                        <tr key={rowKey('tool-usage', index, row.session_id, row.ip, row.workflow, row.tool_name)}>
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
                          <td style={tdStyle} title={row.session_id || ''}>{sessionDisplay(row)}</td>
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
                      filteredRtlRunHistory.map((row, index) => (
                        <tr key={rowKey('rtl-run', index, row.run_id, row.rtl_version_id, row.ip, row.workflow)}>
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
                      filteredArtifactVersions.map((row, index) => (
                        <tr key={rowKey('artifact-version', index, row.artifact_version_id, row.artifact_type, row.ip)}>
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
                      filteredRunArtifactSets.map((row, index) => (
                        <tr key={rowKey('run-artifact-set', index, row.run_id, row.ip, row.workflow)}>
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
                      filteredInterventions.map((row, index) => (
                        <tr key={rowKey('intervention', index, row.session_id, row.ip, row.workflow, row.username)}>
                          <td style={tdStyle}>{row.username || 'unknown'}</td>
                          <td style={tdStyle} title={row.session_id || ''}>{sessionDisplay(row)}</td>
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

            {activeTab === 'inputs' && (
              <div style={tableWrapStyle}>
                <table style={tableStyle}>
                  <thead>
                    <tr>
                      <th style={thStyle}>When</th>
                      <th style={thStyle}>User</th>
                      <th style={thStyle}>Source</th>
                      <th style={thStyle}>IP</th>
                      <th style={thStyle}>Workflow</th>
                      <th style={{ ...thStyle, width: '46%' }}>Input</th>
                      <th style={thStyle}>Session</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredInputHistory.length === 0 ? (
                      <tr>
                        <td colSpan={7} style={{ ...tdStyle, ...emptyStateStyle }}>No user input history yet.</td>
                      </tr>
                    ) : (
                      filteredInputHistory.map((row, index) => (
                        <tr key={rowKey('input-history', index, row.input_id, row.session_id, row.created_at)}>
                          <td style={tdStyle}>{formatDate(row.created_at)}</td>
                          <td style={tdStyle}>{row.username || 'unknown'}</td>
                          <td style={tdStyle}>{row.source || '—'}</td>
                          <td style={tdStyle}>{row.ip || 'unknown'}</td>
                          <td style={tdStyle}>{row.workflow || '—'}</td>
                          <td style={{ ...tdStyle, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                            {row.content || payloadText(row.payload)}
                          </td>
                          <td style={tdStyle} title={row.session_id || ''}>{sessionDisplay(row)}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            )}

            {activeTab === 'memory' && (
              <div style={tableWrapStyle}>
                <table style={tableStyle}>
                  <thead>
                    <tr>
                      <th style={thStyle}>Updated</th>
                      <th style={thStyle}>User</th>
                      <th style={thStyle}>Scope</th>
                      <th style={thStyle}>Workflow</th>
                      <th style={thStyle}>#</th>
                      <th style={{ ...thStyle, width: '54%' }}>Rule</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredMemoryRules.length === 0 ? (
                      <tr>
                        <td colSpan={6} style={{ ...tdStyle, ...emptyStateStyle }}>No memory rules yet.</td>
                      </tr>
                    ) : (
                      filteredMemoryRules.map((row, index) => (
                        <tr key={rowKey('memory-rule', index, row.id, row.user_id, row.position)}>
                          <td style={tdStyle}>{formatDate(row.updated_at || row.created_at)}</td>
                          <td style={tdStyle}>{row.username || 'unknown'}</td>
                          <td style={tdStyle}>{row.scope || 'global'}</td>
                          <td style={tdStyle}>{row.workflow || '—'}</td>
                          <td style={tdStyle}>{row.position || index + 1}</td>
                          <td style={{ ...tdStyle, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                            {row.rule || '—'}
                          </td>
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
                      filteredFeedback.map((f, index) => {
                        const open = f.status !== 'resolved';
                        return (
                          <tr key={rowKey('feedback', index, f.id, f.user_id, f.created_at)} style={open ? { background: '#191c22' } : { opacity: 0.65 }}>
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

            {activeTab === 'admin-chat' && (
              <div style={{ ...tableWrapStyle, padding: 0, overflow: 'hidden' }}>
                <div style={{
                  padding: '12px 14px',
                  borderBottom: '1px solid #2a3540',
                  background: '#1c252f',
                  color: '#f0c674',
                  fontSize: 12,
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  letterSpacing: '0.06em',
                }}>
                  Admin Chat · DB-backed activity Q&A
                </div>
                <div style={{
                  minHeight: 360,
                  maxHeight: 560,
                  overflowY: 'auto',
                  padding: 14,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 10,
                }}>
                  {adminChatMessages.map((msg, index) => (
                    <div
                      key={rowKey('admin-chat', index, msg.role, msg.content)}
                      style={{
                        alignSelf: msg.role === 'user' ? 'flex-end' : 'stretch',
                        maxWidth: msg.role === 'user' ? '74%' : '100%',
                        background: msg.role === 'user' ? '#22303d' : '#141a21',
                        color: '#d6dde6',
                        border: '1px solid #2a3540',
                        borderRadius: 6,
                        padding: '10px 12px',
                        whiteSpace: 'pre-wrap',
                        wordBreak: 'break-word',
                      }}
                    >
                      <div style={{ fontSize: 10, textTransform: 'uppercase', color: '#8893a3', marginBottom: 5 }}>
                        {msg.role === 'user' ? 'Admin' : 'Atlas DB'}
                      </div>
                      <div>{msg.content}</div>
                      {(msg.sections || []).length > 0 && (
                        <div style={{ marginTop: 10, display: 'grid', gap: 8 }}>
                          {msg.sections.map((section, sectionIndex) => (
                            <details key={rowKey('admin-chat-section', sectionIndex, section.title)} style={{ borderTop: '1px solid #2a3540', paddingTop: 8 }}>
                              <summary style={{ cursor: 'pointer', color: '#f0c674', fontSize: 12 }}>
                                {section.title} ({(section.rows || []).length})
                              </summary>
                              <pre style={{
                                margin: '8px 0 0',
                                padding: 10,
                                background: '#0f141a',
                                color: '#a3aebb',
                                overflowX: 'auto',
                                fontSize: 11,
                              }}>{JSON.stringify(section.rows || [], null, 2)}</pre>
                            </details>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                  {adminChatLoading && (
                    <div style={{ color: '#8893a3', fontSize: 12 }}>Querying atlas.db…</div>
                  )}
                </div>
                <form onSubmit={handleAdminChatSubmit} style={{
                  display: 'flex',
                  gap: 8,
                  padding: 12,
                  borderTop: '1px solid #2a3540',
                  background: '#141a21',
                }}>
                  <input
                    value={adminChatDraft}
                    onChange={(e) => setAdminChatDraft(e.target.value)}
                    placeholder="Ask: daily usage, model usage, workflow/IP usage, feedback, memory, input history…"
                    style={{
                      flex: 1,
                      minWidth: 0,
                      background: '#0f141a',
                      border: '1px solid #2a3540',
                      color: '#d6dde6',
                      borderRadius: 4,
                      padding: '8px 10px',
                      fontFamily: 'inherit',
                      fontSize: 13,
                    }}
                  />
                  <button
                    type="submit"
                    disabled={adminChatLoading || !String(adminChatDraft || '').trim()}
                    style={{
                      ...headerButtonStyle,
                      minWidth: 72,
                      opacity: adminChatLoading || !String(adminChatDraft || '').trim() ? 0.55 : 1,
                    }}
                  >
                    Ask
                  </button>
                </form>
              </div>
            )}

            {activeTab === 'raw-db' && (
              <div style={{ display: 'grid', gridTemplateColumns: '260px 1fr', gap: 16 }}>
                <div style={{ ...tableWrapStyle, maxHeight: 600, overflowY: 'auto' }}>
                  <div style={{
                    padding: '8px 12px', background: '#1c252f', borderBottom: '1px solid #2a3540',
                    fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.06em', color: '#a3aebb',
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  }}>
                    <span>Tables ({dbTables.length})</span>
                    <button
                      onClick={loadDbTables}
                      style={{ ...headerButtonStyle, padding: '2px 6px', fontSize: 10 }}
                      title="Refresh"
                    >↻</button>
                  </div>
                  {dbTables.length === 0 ? (
                    <div style={{ padding: 16, color: '#8893a3', fontSize: 12 }}>
                      {dbError ? `Error: ${dbError}` : 'Loading…'}
                    </div>
                  ) : (
                    dbTables.map((t, index) => {
                      const active = dbSelectedTable === t.name;
                      return (
                        <button
                          key={rowKey('db-table', index, t.name)}
                          onClick={() => setDbSelectedTable(t.name)}
                          style={{
                            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                            width: '100%',
                            padding: '8px 12px',
                            background: active ? '#22303d' : 'transparent',
                            color: active ? '#f0c674' : '#d6dde6',
                            border: 'none',
                            borderLeft: active ? '3px solid #f0c674' : '3px solid transparent',
                            borderBottom: '1px solid #20272f',
                            cursor: 'pointer',
                            fontFamily: 'inherit',
                            fontSize: 12,
                            textAlign: 'left',
                          }}
                        >
                          <span style={{ fontWeight: active ? 600 : 400 }}>{t.name}</span>
                          <span style={{
                            fontSize: 10, color: active ? '#f0c674' : '#7d8590',
                            background: '#11161c', padding: '2px 6px', borderRadius: 3,
                          }}>{t.row_count}</span>
                        </button>
                      );
                    })
                  )}
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                  {!dbSelectedTable ? (
                    <>
                      <div style={{
                        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                        gap: 12, flexWrap: 'wrap',
                      }}>
                        <div style={{ fontSize: 14, fontWeight: 600, color: '#f0c674' }}>
                          All tables overview
                          <span style={{ color: '#7d8590', fontWeight: 400, marginLeft: 8, fontSize: 12 }}>
                            (3 most-recent rows per table · click a table name to drill in)
                          </span>
                        </div>
                        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                          <label style={{ fontSize: 11, color: '#a3aebb', display: 'flex', alignItems: 'center', gap: 4 }}>
                            <input
                              type="checkbox"
                              checked={dbHideEmpty}
                              onChange={(e) => setDbHideEmpty(e.target.checked)}
                            />
                            Hide empty
                          </label>
                          <button onClick={loadDbOverview} disabled={dbOverviewLoading} style={headerButtonStyle}>
                            {dbOverviewLoading ? '…' : '↻ Refresh'}
                          </button>
                        </div>
                      </div>

                      {dbError && (
                        <div style={{ ...tableWrapStyle, padding: 16, color: '#e06c75' }}>{dbError}</div>
                      )}

                      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                        {dbOverview.length === 0 ? (
                          <div style={{ ...tableWrapStyle, padding: 24, textAlign: 'center', color: '#8893a3' }}>
                            {dbOverviewLoading ? 'Loading all tables…' : 'No data.'}
                          </div>
                        ) : (
                          dbOverview
                            .filter((t) => !dbHideEmpty || (t.total && t.total > 0))
                            .map((t, index) => (
                              <div key={rowKey('db-overview', index, t.name)} style={tableWrapStyle}>
                                <div style={{
                                  display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                                  padding: '8px 14px', background: '#1c252f',
                                  borderBottom: '1px solid #2a3540',
                                }}>
                                  <button
                                    onClick={() => setDbSelectedTable(t.name)}
                                    style={{
                                      background: 'transparent', border: 'none', padding: 0,
                                      color: '#f0c674', fontWeight: 600, fontSize: 13,
                                      cursor: 'pointer', fontFamily: 'inherit',
                                    }}
                                  >
                                    {t.name}
                                  </button>
                                  <div style={{ display: 'flex', gap: 10, fontSize: 11, color: '#7d8590' }}>
                                    <span><b style={{ color: '#d6dde6' }}>{t.total}</b> rows</span>
                                    <span>{t.columns.length} cols</span>
                                  </div>
                                </div>
                                {t.total === 0 ? (
                                  <div style={{ padding: '8px 14px', fontSize: 11, color: '#5a6470', fontStyle: 'italic' }}>
                                    empty
                                  </div>
                                ) : t.rows.length === 0 ? (
                                  <div style={{ padding: '8px 14px', fontSize: 11, color: '#e06c75' }}>
                                    {t.error || 'no preview rows available'}
                                  </div>
                                ) : (
                                  <div style={{ overflowX: 'auto' }}>
                                    <table style={{ ...tableStyle, fontSize: 11, fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace' }}>
                                      <thead>
                                        <tr>
                                          {t.columns.slice(0, 8).map((c) => (
                                            <th key={c.name} style={{ ...thStyle, padding: '6px 10px', fontSize: 10, whiteSpace: 'nowrap' }}>
                                              {c.name}{c.pk ? <span style={{ color: '#f0c674', marginLeft: 3 }}>*</span> : null}
                                            </th>
                                          ))}
                                          {t.columns.length > 8 && (
                                            <th style={{ ...thStyle, padding: '6px 10px', fontSize: 10, color: '#7d8590' }}>
                                              +{t.columns.length - 8} more
                                            </th>
                                          )}
                                        </tr>
                                      </thead>
                                      <tbody>
                                        {t.rows.map((row, i) => (
                                          <tr key={i}>
                                            {t.columns.slice(0, 8).map((c) => {
                                              const v = row[c.name];
                                              let text;
                                              if (v === null || v === undefined) text = '∅';
                                              else if (typeof v === 'object') text = JSON.stringify(v);
                                              else if (typeof v === 'number' && c.name.endsWith('_at') && v > 1e9) {
                                                try { text = new Date(v * 1000).toISOString().replace('T', ' ').slice(0, 19); }
                                                catch (_) { text = String(v); }
                                              } else text = String(v);
                                              const truncated = text.length > 40 ? text.slice(0, 40) + '…' : text;
                                              return (
                                                <td
                                                  key={c.name}
                                                  style={{
                                                    ...tdStyle, padding: '5px 10px', maxWidth: 180,
                                                    whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
                                                    color: v === null ? '#5a6470' : tdStyle.color,
                                                  }}
                                                  title={text}
                                                >{truncated}</td>
                                              );
                                            })}
                                            {t.columns.length > 8 && (
                                              <td style={{ ...tdStyle, padding: '5px 10px', color: '#5a6470', fontStyle: 'italic' }}>…</td>
                                            )}
                                          </tr>
                                        ))}
                                      </tbody>
                                    </table>
                                  </div>
                                )}
                              </div>
                            ))
                        )}
                      </div>
                    </>
                  ) : (
                    <>
                      <div style={{
                        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                        gap: 12, flexWrap: 'wrap',
                      }}>
                        <div style={{ fontSize: 14, fontWeight: 600, color: '#f0c674', display: 'flex', alignItems: 'center', gap: 8 }}>
                          <button
                            onClick={() => setDbSelectedTable(null)}
                            style={{ ...headerButtonStyle, fontSize: 11, padding: '3px 8px' }}
                            title="Back to all-tables overview"
                          >← Overview</button>
                          {dbSelectedTable}
                          <span style={{ color: '#7d8590', fontWeight: 400, fontSize: 12 }}>
                            ({dbPage.total} rows · showing {dbPage.offset + 1}-{Math.min(dbPage.offset + dbPage.rows.length, dbPage.total)})
                          </span>
                        </div>
                        <div style={{ display: 'flex', gap: 6 }}>
                          <button
                            onClick={() => loadDbTable(dbSelectedTable, Math.max(0, dbPage.offset - dbPage.limit), dbPage.limit)}
                            disabled={dbPage.offset === 0 || dbLoading}
                            style={headerButtonStyle}
                          >‹ Prev</button>
                          <button
                            onClick={() => loadDbTable(dbSelectedTable, dbPage.offset + dbPage.limit, dbPage.limit)}
                            disabled={dbPage.offset + dbPage.rows.length >= dbPage.total || dbLoading}
                            style={headerButtonStyle}
                          >Next ›</button>
                          <select
                            value={dbPage.limit}
                            onChange={(e) => loadDbTable(dbSelectedTable, 0, Number(e.target.value))}
                            style={{ ...headerButtonStyle, padding: '4px 6px' }}
                          >
                            <option value={25}>25</option>
                            <option value={50}>50</option>
                            <option value={100}>100</option>
                            <option value={200}>200</option>
                          </select>
                          <button
                            onClick={() => loadDbTable(dbSelectedTable, dbPage.offset, dbPage.limit)}
                            disabled={dbLoading}
                            style={headerButtonStyle}
                          >↻</button>
                        </div>
                      </div>

                      {dbError ? (
                        <div style={{ ...tableWrapStyle, padding: 16, color: '#e06c75' }}>{dbError}</div>
                      ) : (
                        <div style={{ ...tableWrapStyle, maxHeight: 600, overflowY: 'auto' }}>
                          <table style={{ ...tableStyle, fontSize: 11.5, fontFamily: 'ui-monospace, SFMono-Regular, Menlo, monospace' }}>
                            <thead>
                              <tr>
                                {dbPage.columns.map((c) => (
                                  <th key={c.name} style={{ ...thStyle, fontSize: 10, whiteSpace: 'nowrap' }}>
                                    {c.name}
                                    {c.pk ? <span style={{ color: '#f0c674', marginLeft: 4 }}>PK</span> : null}
                                    <div style={{ fontSize: 9, color: '#7d8590', fontWeight: 400, textTransform: 'none', letterSpacing: 0 }}>
                                      {c.type || 'ANY'}{c.notnull ? ' · NN' : ''}
                                    </div>
                                  </th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {dbPage.rows.length === 0 ? (
                                <tr>
                                  <td colSpan={dbPage.columns.length} style={{ ...tdStyle, ...emptyStateStyle }}>
                                    {dbLoading ? 'Loading…' : 'Table is empty.'}
                                  </td>
                                </tr>
                              ) : (
                                dbPage.rows.map((row, i) => {
                                  const rowKey = `${dbPage.offset}-${i}`;
                                  const expanded = dbExpandedRow === rowKey;
                                  return (
                                    <React.Fragment key={rowKey}>
                                      <tr
                                        onClick={() => setDbExpandedRow(expanded ? null : rowKey)}
                                        style={{ cursor: 'pointer', background: expanded ? '#191c22' : 'transparent' }}
                                      >
                                        {dbPage.columns.map((c) => {
                                          const v = row[c.name];
                                          let text;
                                          if (v === null || v === undefined) text = '∅';
                                          else if (typeof v === 'object') text = JSON.stringify(v);
                                          else if (typeof v === 'number' && c.name.endsWith('_at') && v > 1e9) {
                                            try { text = new Date(v * 1000).toISOString().replace('T', ' ').slice(0, 19); }
                                            catch (_) { text = String(v); }
                                          } else text = String(v);
                                          const truncated = text.length > 60 ? text.slice(0, 60) + '…' : text;
                                          return (
                                            <td
                                              key={c.name}
                                              style={{
                                                ...tdStyle, padding: '6px 10px', maxWidth: 240,
                                                whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
                                                color: v === null ? '#5a6470' : tdStyle.color,
                                              }}
                                              title={text}
                                            >{truncated}</td>
                                          );
                                        })}
                                      </tr>
                                      {expanded && (
                                        <tr>
                                          <td colSpan={dbPage.columns.length} style={{ ...tdStyle, background: '#0f1419', padding: 12 }}>
                                            <pre style={{
                                              margin: 0, fontSize: 11, color: '#a3aebb', whiteSpace: 'pre-wrap',
                                              wordBreak: 'break-word',
                                            }}>{JSON.stringify(row, null, 2)}</pre>
                                          </td>
                                        </tr>
                                      )}
                                    </React.Fragment>
                                  );
                                })
                              )}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </>
                  )}
                </div>
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
