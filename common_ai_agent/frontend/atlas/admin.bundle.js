var AtlasAdminDashboard = (() => {
  // admin.jsx
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
    const [runtime, setRuntime] = React.useState(null);
    const [adminChatMessages, setAdminChatMessages] = React.useState([
      {
        role: "assistant",
        content: "Ask about feedback, user inputs, tool calls, cost, daily usage, models, workflows, IPs, or memory rules."
      }
    ]);
    const [adminChatDraft, setAdminChatDraft] = React.useState("");
    const [adminChatLoading, setAdminChatLoading] = React.useState(false);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState(null);
    const [authStatus, setAuthStatus] = React.useState(null);
    const [authChecked, setAuthChecked] = React.useState(false);
    const [authUser, setAuthUser] = React.useState(null);
    const [authError, setAuthError] = React.useState(null);
    const [loginSubmitting, setLoginSubmitting] = React.useState(false);
    const [loginForm, setLoginForm] = React.useState({
      username: "admin",
      email: "",
      password: "",
      displayName: "Admin"
    });
    const [activeTab, setActiveTab] = React.useState("overview");
    const [filters, setFilters] = React.useState({
      range: "7d",
      ip: "",
      workspace: "",
      workflow: "",
      user: ""
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
        const r = await fetch("/api/admin/feedback");
        if (!r.ok) return;
        const d = await r.json();
        setFeedback(d.feedback || []);
      } catch (_) {
      }
    }
    async function fetchAdminStatus() {
      const r = await fetch("/api/admin/auth/status");
      if (!r.ok) {
        throw new Error(`Admin auth status failed: HTTP ${r.status}`);
      }
      return r.json();
    }
    const loadAdminData = React.useCallback(async () => {
      try {
        setLoading(true);
        setError(null);
        const [usersResp, sessionsResp, usageResp, fbResp, runtimeResp] = await Promise.all([
          fetch("/api/admin/users"),
          fetch("/api/admin/sessions"),
          fetch("/api/admin/usage"),
          fetch("/api/admin/feedback"),
          fetch("/api/admin/runtime")
        ]);
        if ([usersResp, sessionsResp, usageResp, fbResp, runtimeResp].some((r) => r.status === 401)) {
          setAuthUser(null);
          setAuthStatus((prev) => ({ ...prev || {}, login_required: true, authenticated: false }));
          setAuthError("Admin login required");
          return;
        }
        if ([usersResp, sessionsResp, usageResp, fbResp, runtimeResp].some((r) => r.status === 403)) {
          setError("Admin role required");
          return;
        }
        if (!usersResp.ok || !sessionsResp.ok) {
          const bad = !usersResp.ok ? usersResp : sessionsResp;
          let detail = `HTTP ${bad.status}`;
          try {
            const body = await bad.json();
            detail = body.error || body.detail || detail;
          } catch (_) {
          }
          throw new Error(detail);
        }
        const usersData = await usersResp.json();
        const sessionsData = await sessionsResp.json();
        const usageData = usageResp.ok ? await usageResp.json() : { users: [] };
        const fbData = fbResp.ok ? await fbResp.json() : { feedback: [] };
        const runtimeData = runtimeResp.ok ? await runtimeResp.json() : null;
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
        setRuntime(runtimeData);
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
      return () => {
        alive = false;
      };
    }, [loadAdminData]);
    const handleAdminLogin = async (ev) => {
      ev.preventDefault();
      setAuthError(null);
      setLoginSubmitting(true);
      try {
        const username = String(loginForm.username || "").trim();
        const password = String(loginForm.password || "");
        if (!username || !password) {
          throw new Error("Username and password required");
        }
        const createFirstAdmin = authStatus && authStatus.login_required && !authStatus.admin_user_exists;
        const email = String(loginForm.email || "").trim();
        if (createFirstAdmin && authStatus.email_required && !email) {
          throw new Error("Email required");
        }
        const payload = {
          username,
          password,
          display_name: String(loginForm.displayName || "").trim() || username
        };
        if (createFirstAdmin && email) {
          payload.email = email;
        }
        let r = await fetch(createFirstAdmin ? "/api/auth/register" : "/api/auth/login", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        if (!r.ok && createFirstAdmin && r.status === 409) {
          r = await fetch("/api/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
          });
        }
        if (!r.ok) {
          let detail = `HTTP ${r.status}`;
          try {
            const body = await r.json();
            detail = body.detail || body.error || detail;
          } catch (_) {
          }
          throw new Error(detail);
        }
        const status = await fetchAdminStatus();
        setAuthStatus(status);
        setAuthChecked(true);
        if (!status.authenticated) {
          throw new Error("Admin role required");
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
        await fetch("/api/auth/logout", { method: "POST" });
      } catch (_) {
      }
      try {
        const status = await fetchAdminStatus();
        setAuthStatus(status);
      } catch (_) {
        setAuthStatus({ login_required: true, authenticated: false, admin_user_exists: true, mode: "db" });
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
      setRuntime(null);
      setLoading(false);
    };
    const loadDbTables = React.useCallback(async () => {
      setDbError(null);
      try {
        const r = await fetch("/api/admin/db/tables");
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
          try {
            const b = await r.json();
            detail = b.error || detail;
          } catch (_) {
          }
          throw new Error(detail);
        }
        const d = await r.json();
        setDbPage({
          columns: d.columns || [],
          rows: d.rows || [],
          total: d.total || 0,
          limit: d.limit || limit,
          offset: d.offset || offset
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
        const r = await fetch("/api/admin/db/preview?per_table=3");
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
      if (activeTab !== "raw-db" || !authUser) return;
      if (dbTables.length === 0) loadDbTables();
      if (dbOverview.length === 0 && !dbSelectedTable) loadDbOverview();
    }, [activeTab, authUser, dbTables.length, dbOverview.length, dbSelectedTable, loadDbTables, loadDbOverview]);
    React.useEffect(() => {
      if (activeTab !== "raw-db" || !dbSelectedTable) return;
      loadDbTable(dbSelectedTable, 0, dbPage.limit || 50);
    }, [dbSelectedTable, activeTab]);
    const handleResolveFeedback = async (fid) => {
      setResolving(fid);
      try {
        const r = await fetch(`/api/admin/feedback/${encodeURIComponent(fid)}/resolve`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ notes: "" })
        });
        if (r.ok) await reloadFeedback();
      } catch (_) {
      } finally {
        setResolving(null);
      }
    };
    const handleDeleteSession = async (sessionId) => {
      if (!window.confirm("Force-delete this session?")) return;
      setDeleting(sessionId);
      try {
        const resp = await fetch("/api/admin/sessions/" + encodeURIComponent(sessionId), {
          method: "DELETE"
        });
        if (resp.status === 403) {
          setError("Admin access required");
          return;
        }
        const data = await resp.json();
        if (!resp.ok) {
          throw new Error(data.error || "Delete failed");
        }
        setSessions((prev) => prev.filter((s) => s.id !== sessionId));
      } catch (e) {
        alert("Failed to delete session: " + e);
      } finally {
        setDeleting(null);
      }
    };
    const handleAdminChatSubmit = async (ev) => {
      ev.preventDefault();
      const text = String(adminChatDraft || "").trim();
      if (!text || adminChatLoading) return;
      setAdminChatDraft("");
      setAdminChatMessages((prev) => [...prev, { role: "user", content: text }]);
      setAdminChatLoading(true);
      try {
        const r = await fetch("/api/admin/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: text })
        });
        let body = {};
        try {
          body = await r.json();
        } catch (_) {
        }
        if (!r.ok) throw new Error(body.error || `HTTP ${r.status}`);
        setAdminChatMessages((prev) => [...prev, {
          role: "assistant",
          content: body.answer || "No matching DB rows.",
          sections: body.sections || []
        }]);
      } catch (e) {
        setAdminChatMessages((prev) => [...prev, { role: "assistant", content: `Error: ${String(e)}` }]);
      } finally {
        setAdminChatLoading(false);
      }
    };
    const pageStyle = {
      width: "100%",
      height: "100%",
      background: "#11161c",
      color: "#d6dde6",
      fontFamily: "var(--mono, 'Inter', 'Noto Sans KR', system-ui, sans-serif)",
      fontSize: 14,
      lineHeight: 1.5,
      overflow: "auto",
      display: "flex",
      flexDirection: "column"
    };
    const headerStyle = {
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      padding: "20px 32px",
      borderBottom: "1px solid #2a3540",
      background: "#141a21"
    };
    const logoStyle = {
      display: "flex",
      alignItems: "center",
      gap: 12,
      fontSize: 22,
      fontWeight: 700,
      letterSpacing: "0.04em",
      color: "#f0c674"
    };
    const badgeStyle = {
      fontSize: 10,
      fontWeight: 600,
      textTransform: "uppercase",
      letterSpacing: "0.08em",
      padding: "3px 8px",
      borderRadius: 4,
      background: "#2a3a4a",
      color: "#f0c674",
      border: "1px solid #3a4756"
    };
    const headerRightStyle = {
      display: "flex",
      alignItems: "center",
      gap: 8
    };
    const headerButtonStyle = {
      minHeight: 28,
      padding: "4px 9px",
      borderRadius: 4,
      border: "1px solid #3a4756",
      background: "#10161d",
      color: "#d6dde6",
      cursor: "pointer",
      fontFamily: "inherit",
      fontSize: 11
    };
    const mainStyle = {
      flex: 1,
      padding: "24px 32px 40px",
      display: "flex",
      flexDirection: "column",
      gap: 24,
      maxWidth: 1200,
      margin: "0 auto",
      width: "100%"
    };
    const tabRowStyle = {
      display: "flex",
      flexWrap: "wrap",
      gap: 4,
      background: "#161d25",
      borderRadius: 6,
      padding: 3,
      border: "1px solid #2a3540",
      width: "fit-content"
    };
    const tabStyle = (active) => ({
      padding: "6px 14px",
      fontSize: 12,
      fontWeight: 600,
      borderRadius: 4,
      border: "none",
      cursor: "pointer",
      fontFamily: "inherit",
      background: active ? "#2a3a4a" : "transparent",
      color: active ? "#f0c674" : "#8893a3",
      transition: "background 0.2s ease, color 0.2s ease"
    });
    const filterBarStyle = {
      display: "grid",
      gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
      gap: 10,
      padding: 12,
      background: "#161d25",
      border: "1px solid #2a3540",
      borderRadius: 10
    };
    const filterLabelStyle = {
      display: "flex",
      flexDirection: "column",
      gap: 5,
      color: "#8893a3",
      fontSize: 11,
      fontWeight: 700,
      textTransform: "uppercase",
      letterSpacing: "0.04em"
    };
    const selectStyle = {
      minHeight: 32,
      background: "#10161d",
      color: "#d6dde6",
      border: "1px solid #2a3540",
      borderRadius: 5,
      padding: "5px 8px",
      fontFamily: "inherit",
      fontSize: 12
    };
    const loginShellStyle = {
      width: "min(100%, 420px)",
      margin: "78px auto 0",
      padding: 24,
      background: "#161d25",
      border: "1px solid #2a3540",
      borderRadius: 8,
      boxShadow: "0 20px 50px rgba(0,0,0,0.35)"
    };
    const loginTitleStyle = {
      margin: "0 0 18px",
      color: "#f0c674",
      fontSize: 18,
      fontWeight: 700
    };
    const loginFieldStyle = {
      display: "flex",
      flexDirection: "column",
      gap: 6,
      marginBottom: 12,
      color: "#8893a3",
      fontSize: 11,
      fontWeight: 700,
      textTransform: "uppercase",
      letterSpacing: "0.04em"
    };
    const loginInputStyle = {
      minHeight: 38,
      background: "#10161d",
      color: "#e6edf3",
      border: "1px solid #2a3540",
      borderRadius: 5,
      padding: "7px 10px",
      fontFamily: "inherit",
      fontSize: 14
    };
    const loginButtonStyle = {
      width: "100%",
      minHeight: 40,
      marginTop: 6,
      borderRadius: 5,
      border: "1px solid #4a5b6e",
      background: "#2a3a4a",
      color: "#f0c674",
      cursor: loginSubmitting ? "wait" : "pointer",
      fontFamily: "inherit",
      fontSize: 13,
      fontWeight: 700
    };
    const overviewGridStyle = {
      display: "grid",
      gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 170px), 1fr))",
      gap: 12
    };
    const metricCardStyle = (tone = "default") => ({
      background: tone === "danger" ? "rgba(224,108,117,0.10)" : "#161d25",
      border: tone === "danger" ? "1px solid rgba(224,108,117,0.45)" : "1px solid #2a3540",
      borderRadius: 8,
      padding: "14px 15px",
      minHeight: 82
    });
    const metricLabelStyle = {
      color: "#8893a3",
      fontSize: 11,
      fontWeight: 700,
      textTransform: "uppercase",
      letterSpacing: "0.05em",
      marginBottom: 7
    };
    const metricValueStyle = {
      color: "#f0c674",
      fontSize: 24,
      fontWeight: 750,
      lineHeight: 1.1
    };
    const panelTitleStyle = {
      padding: "12px 14px",
      borderBottom: "1px solid #2a3540",
      background: "#1c252f",
      color: "#f0c674",
      fontSize: 12,
      fontWeight: 700,
      textTransform: "uppercase",
      letterSpacing: "0.06em"
    };
    const tableWrapStyle = {
      background: "#161d25",
      border: "1px solid #2a3540",
      borderRadius: 10,
      overflow: "hidden",
      overflowX: "auto"
    };
    const dashboardGridStyle = {
      display: "grid",
      gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 420px), 1fr))",
      gap: 14
    };
    const dashboardWideStyle = {
      gridColumn: "1 / -1"
    };
    const widgetHeaderStyle = {
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center",
      gap: 12,
      padding: "11px 14px",
      borderBottom: "1px solid #2a3540",
      background: "#1c252f"
    };
    const widgetTitleStyle = {
      color: "#f0c674",
      fontSize: 12,
      fontWeight: 700,
      textTransform: "uppercase",
      letterSpacing: "0.06em"
    };
    const widgetMetaStyle = {
      color: "#8893a3",
      fontSize: 11,
      whiteSpace: "nowrap"
    };
    const barTrackStyle = {
      height: 8,
      borderRadius: 4,
      background: "#0f151b",
      border: "1px solid #2a3540",
      overflow: "hidden"
    };
    const barFillStyle = (width, tone = "default") => ({
      height: "100%",
      width,
      minWidth: width === "0%" ? 0 : 4,
      background: tone === "cost" ? "#f0c674" : "#7dc9a0"
    });
    const mutedSmallStyle = {
      color: "#8893a3",
      fontSize: 11
    };
    const tableStyle = {
      width: "100%",
      borderCollapse: "collapse",
      fontSize: 13
    };
    const thStyle = {
      textAlign: "left",
      padding: "10px 14px",
      background: "#1c252f",
      color: "#a3aebb",
      fontWeight: 600,
      fontSize: 11,
      textTransform: "uppercase",
      letterSpacing: "0.06em",
      borderBottom: "1px solid #2a3540"
    };
    const tdStyle = {
      padding: "10px 14px",
      borderBottom: "1px solid #2a3540",
      color: "#d6dde6"
    };
    const btnDangerStyle = {
      background: "transparent",
      color: "#e06c75",
      border: "1px solid #e06c75",
      borderRadius: 4,
      padding: "5px 10px",
      fontSize: 11,
      fontWeight: 600,
      fontFamily: "inherit",
      cursor: "pointer",
      opacity: deleting ? 0.6 : 1,
      pointerEvents: deleting ? "none" : "auto"
    };
    const emptyStateStyle = {
      color: "#8893a3",
      fontSize: 13,
      textAlign: "center",
      padding: "32px 0"
    };
    const errorStateStyle = {
      color: "#e06c75",
      fontSize: 14,
      textAlign: "center",
      padding: "40px 0",
      border: "1px dashed #e06c75",
      borderRadius: 10,
      background: "rgba(224,108,117,0.08)"
    };
    const formatDate = (ts) => {
      if (!ts) return "\u2014";
      try {
        return new Date(ts * 1e3).toLocaleString();
      } catch (_) {
        return String(ts);
      }
    };
    const fmt = (n) => n == null ? "\u2014" : Number(n).toLocaleString();
    const usd = (n) => n == null ? "\u2014" : `$${Number(n).toFixed(4)}`;
    const durationMs = (n) => {
      const value = Number(n || 0);
      if (!value) return "\u2014";
      if (value < 1e3) return `${value.toFixed(0)} ms`;
      return `${(value / 1e3).toFixed(1)} s`;
    };
    const shortId = (value) => String(value || "").slice(0, 8) || "\u2014";
    const sessionDisplay = (rowOrId) => {
      const row = rowOrId && typeof rowOrId === "object" ? rowOrId : { session_id: rowOrId };
      const sessionId = String(row.session_id || row.id || "").trim();
      if (sessionId.includes("/")) return sessionId;
      const label = String(row.session || "").trim();
      return label || shortId(sessionId);
    };
    const keyPart = (value) => {
      if (value === null || value === void 0 || value === "") return "empty";
      try {
        const text = typeof value === "object" ? JSON.stringify(value) : String(value);
        return text.replace(/\s+/g, " ").slice(0, 120) || "empty";
      } catch (_) {
        return "value";
      }
    };
    const rowKey = (scope, index, ...parts) => [scope, ...parts.map(keyPart), index].join(":");
    const firstVersion = (row, type) => {
      const items = row.artifact_versions && row.artifact_versions[type] || [];
      return items.length ? items[0] : null;
    };
    const versionText = (row, type) => {
      const item = firstVersion(row, type);
      return item ? item.version || shortId(item.artifact_version_id) : "\u2014";
    };
    const versionTagText = (row, type) => {
      const item = firstVersion(row, type);
      return item ? item.git_tag || item.sha256_tree || shortId(item.artifact_version_id) : "\u2014";
    };
    const payloadText = (value) => {
      if (value == null || value === "") return "\u2014";
      try {
        const text = typeof value === "string" ? value : JSON.stringify(value);
        return text.length > 180 ? text.slice(0, 177) + "\u2026" : text;
      } catch (_) {
        return String(value);
      }
    };
    const statusPillStyle = (status) => {
      const value = String(status || "").toLowerCase();
      const tone = value === "passed" || value === "completed" || value === "success" ? "ok" : value === "failed" || value === "error" ? "bad" : value === "running" ? "run" : value === "blocked" ? "warn" : "idle";
      const palette = {
        ok: ["#1c2f25", "#7dc9a0"],
        bad: ["#3a1f24", "#e06c75"],
        run: ["#1f2a3a", "#82aaff"],
        warn: ["#3a3120", "#f0c674"],
        idle: ["#1c252f", "#a3aebb"]
      }[tone];
      return {
        fontSize: 10,
        fontWeight: 600,
        textTransform: "uppercase",
        padding: "2px 6px",
        borderRadius: 3,
        background: palette[0],
        color: palette[1],
        border: "1px solid #2a3540"
      };
    };
    const sum = (rows, key) => rows.reduce((acc, row) => acc + Number(row[key] || 0), 0);
    const rowTimestamp = (row) => {
      const direct = row.active_session_updated_at || row.last_message_at || row.last_event_at || row.last_tool_at || row.last_intervention_at || row.started_at || row.ended_at || row.created_at || row.updated_at || row.first_intervention_at;
      if (direct) return Number(direct) || 0;
      if (row.day) {
        const parsed = Date.parse(`${row.day}T23:59:59`);
        return Number.isNaN(parsed) ? 0 : parsed / 1e3;
      }
      return 0;
    };
    const inRange = (row) => {
      if (!filters.range || filters.range === "all") return true;
      const days = { "24h": 1, "7d": 7, "30d": 30 }[filters.range] || 7;
      const ts = rowTimestamp(row);
      if (!ts) return true;
      return ts >= Date.now() / 1e3 - days * 86400;
    };
    const valueMatches = (selected, value) => !selected || String(value || "") === selected;
    const rowMatches = (row) => inRange(row) && valueMatches(filters.ip, row.ip) && valueMatches(filters.workspace, row.workspace) && valueMatches(filters.workflow, row.workflow) && valueMatches(filters.user, row.username || row.owner_username);
    const uniqueOptions = (rows, key) => Array.from(new Set(
      rows.map((row) => String(row[key] || "").trim()).filter(Boolean)
    )).sort((a, b) => a.localeCompare(b));
    const sessionContextRows = sessions.map((s) => ({
      username: s.owner_username || s.user_id,
      ip: s.ip || s.project_id || "",
      workflow: s.workflow || s.latest_workflow || "",
      created_at: s.created_at,
      updated_at: s.updated_at
    }));
    const userFocusContextRows = users.map((u) => ({
      username: u.username,
      ip: u.active_ip || "",
      workflow: u.active_workflow || "",
      updated_at: u.active_session_updated_at
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
      ...userFocusContextRows
    ];
    const filterOptions = {
      ips: uniqueOptions(allContextRows, "ip"),
      workspaces: uniqueOptions(allContextRows, "workspace"),
      workflows: uniqueOptions(allContextRows, "workflow"),
      users: uniqueOptions([
        ...allContextRows,
        ...usage,
        ...feedback,
        ...memoryRules,
        ...inputHistory
      ], "username")
    };
    const filteredUsers = users.filter((row) => valueMatches(filters.user, row.username) && valueMatches(filters.ip, row.active_ip) && !filters.workspace && valueMatches(filters.workflow, row.active_workflow));
    const filteredUsage = usage.filter((row) => inRange(row) && valueMatches(filters.user, row.username) && !filters.ip && !filters.workspace && !filters.workflow);
    const filteredSessions = sessions.filter((row) => inRange(row) && valueMatches(filters.user, row.owner_username || row.user_id) && valueMatches(filters.ip, row.ip || row.project_id || row.title) && !filters.workspace && valueMatches(filters.workflow, row.workflow || row.latest_workflow));
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
    const filteredMemoryRules = memoryRules.filter((row) => inRange(row) && valueMatches(filters.user, row.username) && !filters.ip && !filters.workspace && valueMatches(filters.workflow, row.workflow));
    const filteredInputHistory = inputHistory.filter(rowMatches);
    const filteredFeedback = feedback.filter((row) => inRange(row) && valueMatches(filters.user, row.username) && !filters.ip && !filters.workspace && !filters.workflow);
    const sessionWorkloadRows = filteredSessions.map((s) => ({
      username: s.owner_username || s.user_id || "unknown",
      ip: s.ip || s.project_id || s.title || "unknown",
      workflow: s.workflow || s.latest_workflow || "",
      session_id: s.id,
      calls: 0,
      tokens: 0,
      cost: 0,
      updated_at: s.updated_at
    }));
    const workloadContextRows = [...filteredCostContexts, ...sessionWorkloadRows];
    const workloadScore = (row) => Number(row.cost || 0) || Number(row.calls || 0) || Number(row.sessionCount || 0);
    const aggregateWorkload = (rows, key, fallback) => {
      const grouped = /* @__PURE__ */ new Map();
      rows.forEach((row) => {
        const name = String(row[key] || "").trim() || fallback;
        if (!grouped.has(name)) {
          grouped.set(name, {
            name,
            calls: 0,
            tokens: 0,
            cost: 0,
            sessionIds: /* @__PURE__ */ new Set(),
            users: /* @__PURE__ */ new Set(),
            lastAt: 0
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
      return Array.from(grouped.values()).map((row) => ({
        ...row,
        sessionCount: row.sessionIds.size,
        userCount: row.users.size,
        userList: Array.from(row.users).sort()
      })).sort((a, b) => workloadScore(b) - workloadScore(a) || b.lastAt - a.lastAt || a.name.localeCompare(b.name));
    };
    const activeUserRows = [...filteredUsers].filter((row) => (row.active_ip || row.active_workflow) && inRange(row)).sort((a, b) => rowTimestamp(b) - rowTimestamp(a) || String(a.username || "").localeCompare(String(b.username || ""))).slice(0, 8);
    const recentSessionRows = [...filteredSessions].sort((a, b) => rowTimestamp(b) - rowTimestamp(a)).slice(0, 8);
    const ipWorkloadRows = aggregateWorkload(workloadContextRows, "ip", "unknown").slice(0, 8);
    const workflowWorkloadRows = aggregateWorkload(workloadContextRows, "workflow", "unassigned").slice(0, 8);
    const maxIpScore = Math.max(1, ...ipWorkloadRows.map(workloadScore));
    const maxWorkflowScore = Math.max(1, ...workflowWorkloadRows.map(workloadScore));
    const topCostRows = [...filteredCostContexts].sort((a, b) => Number(b.cost || 0) - Number(a.cost || 0)).slice(0, 5);
    const topRejectedTodos = [...filteredTodoUsage].filter((row) => Number(row.rejected_count || 0) > 0).sort((a, b) => Number(b.rejected_count || 0) - Number(a.rejected_count || 0)).slice(0, 5);
    const topToolRows = [...filteredToolUsage].sort((a, b) => Number(b.failed_calls || 0) - Number(a.failed_calls || 0) || Number(b.observation_tokens_est || 0) - Number(a.observation_tokens_est || 0)).slice(0, 5);
    const recentStageRows = [...filteredWorkflowStages].sort((a, b) => rowTimestamp(b) - rowTimestamp(a)).slice(0, 8);
    const topHumanRows = [...filteredInterventions].sort((a, b) => Number(b.intervention_count || 0) - Number(a.intervention_count || 0)).slice(0, 5);
    const askUserOpened = new Set(filteredTraceEvents.filter((row) => row.event_type === "ask_user.opened").map((row) => row.payload && row.payload.flow_id || row.event_id).filter(Boolean));
    const askUserAnswered = new Set(filteredTraceEvents.filter((row) => row.event_type === "ask_user.answered").map((row) => row.payload && row.payload.flow_id || row.event_id).filter(Boolean));
    const overview = {
      activeUsers: filteredUsers.filter((row) => (row.active_ip || row.active_workflow) && inRange(row)).length,
      activeSessions: filteredSessions.filter((row) => String(row.status || "").toLowerCase() === "active").length,
      workflowStages: filteredWorkflowStages.length,
      activeIps: new Set(filteredSessions.filter((row) => String(row.status || "").toLowerCase() === "active").map((row) => row.ip || row.project_id || row.title).filter(Boolean)).size,
      cost: sum(filteredCostContexts, "cost"),
      llmCalls: sum(filteredCostContexts, "calls"),
      toolCalls: sum(filteredToolUsage, "calls"),
      toolFailures: sum(filteredToolUsage, "failed_calls"),
      obsTokens: sum(filteredToolUsage, "observation_tokens_est"),
      rejectedTodos: sum(filteredTodoUsage, "rejected_count"),
      openTodos: filteredTodoUsage.filter((row) => !["approved", "completed"].includes(String(row.status || "").toLowerCase())).length,
      humanInputs: sum(filteredInterventions, "intervention_count"),
      inputRows: filteredInputHistory.length,
      memoryRules: filteredMemoryRules.length,
      rtlRuns: filteredRtlRunHistory.length,
      artifactVersions: filteredArtifactVersions.length,
      runArtifactSets: filteredRunArtifactSets.length,
      pendingHuman: Array.from(askUserOpened).filter((flow) => !askUserAnswered.has(flow)).length,
      pendingFeedback: filteredFeedback.filter((row) => row.status !== "resolved").length
    };
    const workerRuntime = runtime && runtime.worker_runtime || {};
    const ipcRuntime = workerRuntime.ipc || {};
    const ipcLimits = ipcRuntime.limits || {};
    const ipcJobs = Array.isArray(ipcRuntime.jobs) ? ipcRuntime.jobs : [];
    const runtimeScm = runtime && runtime.scm || {};
    const runtimeAtlas = runtime && runtime.atlas || {};
    const runtimeTransport = workerRuntime.transport || "unknown";
    const setFilter = (key, value) => setFilters((prev) => ({ ...prev, [key]: value }));
    const clearFilters = () => setFilters({ range: "all", ip: "", workspace: "", workflow: "", user: "" });
    const loginRequired = authChecked && authStatus && authStatus.login_required && !authStatus.authenticated;
    const loginButtonText = authStatus && authStatus.admin_user_exists ? "Log in" : "Create admin account";
    return /* @__PURE__ */ React.createElement("div", { style: pageStyle }, /* @__PURE__ */ React.createElement("header", { style: headerStyle }, /* @__PURE__ */ React.createElement("div", { style: logoStyle }, /* @__PURE__ */ React.createElement("span", { style: { fontSize: 26 } }, "\u25C8"), /* @__PURE__ */ React.createElement("span", null, "ATLAS Admin")), /* @__PURE__ */ React.createElement("div", { style: headerRightStyle }, authUser && /* @__PURE__ */ React.createElement("span", { style: badgeStyle }, authUser.username), /* @__PURE__ */ React.createElement("span", { style: badgeStyle }, authStatus && authStatus.mode === "local" ? "Local Admin" : "Admin"), authUser && authStatus && authStatus.login_required && /* @__PURE__ */ React.createElement("button", { type: "button", style: headerButtonStyle, onClick: handleLogout }, "Logout"))), /* @__PURE__ */ React.createElement("main", { style: mainStyle }, loading && /* @__PURE__ */ React.createElement("div", { style: { textAlign: "center", padding: "40px 0", color: "#8893a3" } }, "Loading\u2026"), !loading && loginRequired && /* @__PURE__ */ React.createElement("form", { style: loginShellStyle, onSubmit: handleAdminLogin }, /* @__PURE__ */ React.createElement("h1", { style: loginTitleStyle }, "Admin Login"), authError && /* @__PURE__ */ React.createElement("div", { style: { ...errorStateStyle, marginBottom: 14 } }, authError), /* @__PURE__ */ React.createElement("label", { style: loginFieldStyle }, "Username", /* @__PURE__ */ React.createElement(
      "input",
      {
        style: loginInputStyle,
        value: loginForm.username,
        autoComplete: "username",
        onChange: (ev) => setLoginForm((prev) => ({ ...prev, username: ev.target.value }))
      }
    )), !authStatus.admin_user_exists && /* @__PURE__ */ React.createElement("label", { style: loginFieldStyle }, "Display Name", /* @__PURE__ */ React.createElement(
      "input",
      {
        style: loginInputStyle,
        value: loginForm.displayName,
        autoComplete: "name",
        onChange: (ev) => setLoginForm((prev) => ({ ...prev, displayName: ev.target.value }))
      }
    )), !authStatus.admin_user_exists && /* @__PURE__ */ React.createElement("label", { style: loginFieldStyle }, "Email", authStatus.email_required ? "" : " (optional)", /* @__PURE__ */ React.createElement(
      "input",
      {
        style: loginInputStyle,
        type: "email",
        value: loginForm.email,
        autoComplete: "email",
        onChange: (ev) => setLoginForm((prev) => ({ ...prev, email: ev.target.value }))
      }
    )), /* @__PURE__ */ React.createElement("label", { style: loginFieldStyle }, "Password", /* @__PURE__ */ React.createElement(
      "input",
      {
        style: loginInputStyle,
        type: "password",
        value: loginForm.password,
        autoComplete: authStatus.admin_user_exists ? "current-password" : "new-password",
        onChange: (ev) => setLoginForm((prev) => ({ ...prev, password: ev.target.value }))
      }
    )), /* @__PURE__ */ React.createElement("button", { type: "submit", style: loginButtonStyle, disabled: loginSubmitting }, loginSubmitting ? "Working\u2026" : loginButtonText)), !loading && !loginRequired && error && /* @__PURE__ */ React.createElement("div", { style: errorStateStyle }, error), !loading && !loginRequired && !error && /* @__PURE__ */ React.createElement(React.Fragment, null, /* @__PURE__ */ React.createElement("div", { style: tabRowStyle }, /* @__PURE__ */ React.createElement("button", { style: tabStyle(activeTab === "overview"), onClick: () => setActiveTab("overview") }, "Overview"), /* @__PURE__ */ React.createElement("button", { style: tabStyle(activeTab === "users"), onClick: () => setActiveTab("users") }, "Users (", filteredUsers.length, ")"), /* @__PURE__ */ React.createElement("button", { style: tabStyle(activeTab === "sessions"), onClick: () => setActiveTab("sessions") }, "Sessions (", filteredSessions.length, ")"), /* @__PURE__ */ React.createElement("button", { style: tabStyle(activeTab === "stages"), onClick: () => setActiveTab("stages") }, "Stages (", filteredWorkflowStages.length, ")"), /* @__PURE__ */ React.createElement("button", { style: tabStyle(activeTab === "usage"), onClick: () => setActiveTab("usage") }, "Usage (", filteredUsage.length, ")"), /* @__PURE__ */ React.createElement("button", { style: tabStyle(activeTab === "costs"), onClick: () => setActiveTab("costs") }, "Costs (", filteredCostContexts.length, ")"), /* @__PURE__ */ React.createElement("button", { style: tabStyle(activeTab === "todos"), onClick: () => setActiveTab("todos") }, "Todos (", filteredTodoUsage.length, ")"), /* @__PURE__ */ React.createElement("button", { style: tabStyle(activeTab === "flow"), onClick: () => setActiveTab("flow") }, "Flow (", filteredTodoFlow.length, ")"), /* @__PURE__ */ React.createElement("button", { style: tabStyle(activeTab === "trace"), onClick: () => setActiveTab("trace") }, "Trace (", filteredTraceEvents.length, ")"), /* @__PURE__ */ React.createElement("button", { style: tabStyle(activeTab === "tools"), onClick: () => setActiveTab("tools") }, "Tools (", filteredToolUsage.length, ")"), /* @__PURE__ */ React.createElement("button", { style: tabStyle(activeTab === "rtl"), onClick: () => setActiveTab("rtl") }, "RTL Runs (", filteredRtlRunHistory.length, ")"), /* @__PURE__ */ React.createElement("button", { style: tabStyle(activeTab === "versions"), onClick: () => setActiveTab("versions") }, "Versions (", filteredArtifactVersions.length, ")"), /* @__PURE__ */ React.createElement("button", { style: tabStyle(activeTab === "run-sets"), onClick: () => setActiveTab("run-sets") }, "Run Sets (", filteredRunArtifactSets.length, ")"), /* @__PURE__ */ React.createElement("button", { style: tabStyle(activeTab === "human"), onClick: () => setActiveTab("human") }, "Human (", filteredInterventions.length, ")"), /* @__PURE__ */ React.createElement("button", { style: tabStyle(activeTab === "inputs"), onClick: () => setActiveTab("inputs") }, "Inputs (", filteredInputHistory.length, ")"), /* @__PURE__ */ React.createElement("button", { style: tabStyle(activeTab === "memory"), onClick: () => setActiveTab("memory") }, "Memory (", filteredMemoryRules.length, ")"), /* @__PURE__ */ React.createElement("button", { style: tabStyle(activeTab === "runtime"), onClick: () => setActiveTab("runtime") }, "Runtime"), /* @__PURE__ */ React.createElement("button", { style: tabStyle(activeTab === "feedback"), onClick: () => setActiveTab("feedback") }, "Feedback (", filteredFeedback.filter((f) => f.status !== "resolved").length, "/", filteredFeedback.length, ")"), /* @__PURE__ */ React.createElement("button", { style: tabStyle(activeTab === "admin-chat"), onClick: () => setActiveTab("admin-chat") }, "Admin Chat"), /* @__PURE__ */ React.createElement("button", { style: tabStyle(activeTab === "raw-db"), onClick: () => setActiveTab("raw-db") }, "Raw DB")), /* @__PURE__ */ React.createElement("div", { style: filterBarStyle }, /* @__PURE__ */ React.createElement("label", { style: filterLabelStyle, htmlFor: "admin-filter-range" }, "Range", /* @__PURE__ */ React.createElement(
      "select",
      {
        id: "admin-filter-range",
        "aria-label": "Range",
        style: selectStyle,
        value: filters.range,
        onChange: (e) => setFilter("range", e.target.value)
      },
      /* @__PURE__ */ React.createElement("option", { value: "24h" }, "Last 24h"),
      /* @__PURE__ */ React.createElement("option", { value: "7d" }, "Last 7d"),
      /* @__PURE__ */ React.createElement("option", { value: "30d" }, "Last 30d"),
      /* @__PURE__ */ React.createElement("option", { value: "all" }, "All time")
    )), /* @__PURE__ */ React.createElement("label", { style: filterLabelStyle, htmlFor: "admin-filter-ip" }, "IP", /* @__PURE__ */ React.createElement(
      "select",
      {
        id: "admin-filter-ip",
        "aria-label": "IP",
        style: selectStyle,
        value: filters.ip,
        onChange: (e) => setFilter("ip", e.target.value)
      },
      /* @__PURE__ */ React.createElement("option", { value: "" }, "All IPs"),
      filterOptions.ips.map((value) => /* @__PURE__ */ React.createElement("option", { key: value, value }, value))
    )), /* @__PURE__ */ React.createElement("label", { style: filterLabelStyle, htmlFor: "admin-filter-workspace" }, "Workspace", /* @__PURE__ */ React.createElement(
      "select",
      {
        id: "admin-filter-workspace",
        "aria-label": "Workspace",
        style: selectStyle,
        value: filters.workspace,
        onChange: (e) => setFilter("workspace", e.target.value)
      },
      /* @__PURE__ */ React.createElement("option", { value: "" }, "All workspaces"),
      filterOptions.workspaces.map((value) => /* @__PURE__ */ React.createElement("option", { key: value, value }, value))
    )), /* @__PURE__ */ React.createElement("label", { style: filterLabelStyle, htmlFor: "admin-filter-workflow" }, "Workflow", /* @__PURE__ */ React.createElement(
      "select",
      {
        id: "admin-filter-workflow",
        "aria-label": "Workflow",
        style: selectStyle,
        value: filters.workflow,
        onChange: (e) => setFilter("workflow", e.target.value)
      },
      /* @__PURE__ */ React.createElement("option", { value: "" }, "All workflows"),
      filterOptions.workflows.map((value) => /* @__PURE__ */ React.createElement("option", { key: value, value }, value))
    )), /* @__PURE__ */ React.createElement("label", { style: filterLabelStyle, htmlFor: "admin-filter-user" }, "User", /* @__PURE__ */ React.createElement(
      "select",
      {
        id: "admin-filter-user",
        "aria-label": "User",
        style: selectStyle,
        value: filters.user,
        onChange: (e) => setFilter("user", e.target.value)
      },
      /* @__PURE__ */ React.createElement("option", { value: "" }, "All users"),
      filterOptions.users.map((value) => /* @__PURE__ */ React.createElement("option", { key: value, value }, value))
    )), /* @__PURE__ */ React.createElement("label", { style: filterLabelStyle }, "Reset", /* @__PURE__ */ React.createElement("button", { type: "button", style: { ...selectStyle, cursor: "pointer", color: "#f0c674" }, onClick: clearFilters }, "Clear filters"))), activeTab === "overview" && /* @__PURE__ */ React.createElement(React.Fragment, null, /* @__PURE__ */ React.createElement("div", { style: overviewGridStyle }, /* @__PURE__ */ React.createElement("div", { style: metricCardStyle() }, /* @__PURE__ */ React.createElement("div", { style: metricLabelStyle }, "Active Users"), /* @__PURE__ */ React.createElement("div", { style: metricValueStyle }, fmt(overview.activeUsers))), /* @__PURE__ */ React.createElement("div", { style: metricCardStyle() }, /* @__PURE__ */ React.createElement("div", { style: metricLabelStyle }, "Active IPs"), /* @__PURE__ */ React.createElement("div", { style: metricValueStyle }, fmt(overview.activeIps))), /* @__PURE__ */ React.createElement("div", { style: metricCardStyle() }, /* @__PURE__ */ React.createElement("div", { style: metricLabelStyle }, "Active Sessions"), /* @__PURE__ */ React.createElement("div", { style: metricValueStyle }, fmt(overview.activeSessions))), /* @__PURE__ */ React.createElement("div", { style: metricCardStyle() }, /* @__PURE__ */ React.createElement("div", { style: metricLabelStyle }, "Workflow Stages"), /* @__PURE__ */ React.createElement("div", { style: metricValueStyle }, fmt(overview.workflowStages))), /* @__PURE__ */ React.createElement("div", { style: metricCardStyle() }, /* @__PURE__ */ React.createElement("div", { style: metricLabelStyle }, "Cost"), /* @__PURE__ */ React.createElement("div", { style: metricValueStyle }, usd(overview.cost))), /* @__PURE__ */ React.createElement("div", { style: metricCardStyle() }, /* @__PURE__ */ React.createElement("div", { style: metricLabelStyle }, "LLM Calls"), /* @__PURE__ */ React.createElement("div", { style: metricValueStyle }, fmt(overview.llmCalls))), /* @__PURE__ */ React.createElement("div", { style: metricCardStyle() }, /* @__PURE__ */ React.createElement("div", { style: metricLabelStyle }, "Tool Calls"), /* @__PURE__ */ React.createElement("div", { style: metricValueStyle }, fmt(overview.toolCalls))), /* @__PURE__ */ React.createElement("div", { style: metricCardStyle(overview.toolFailures ? "danger" : "default") }, /* @__PURE__ */ React.createElement("div", { style: metricLabelStyle }, "Tool Failures"), /* @__PURE__ */ React.createElement("div", { style: metricValueStyle }, fmt(overview.toolFailures))), /* @__PURE__ */ React.createElement("div", { style: metricCardStyle() }, /* @__PURE__ */ React.createElement("div", { style: metricLabelStyle }, "Obs Tokens Est"), /* @__PURE__ */ React.createElement("div", { style: metricValueStyle }, fmt(overview.obsTokens))), /* @__PURE__ */ React.createElement("div", { style: metricCardStyle(overview.rejectedTodos ? "danger" : "default") }, /* @__PURE__ */ React.createElement("div", { style: metricLabelStyle }, "Rejected Todos"), /* @__PURE__ */ React.createElement("div", { style: metricValueStyle }, fmt(overview.rejectedTodos))), /* @__PURE__ */ React.createElement("div", { style: metricCardStyle(overview.openTodos ? "danger" : "default") }, /* @__PURE__ */ React.createElement("div", { style: metricLabelStyle }, "Open Todos"), /* @__PURE__ */ React.createElement("div", { style: metricValueStyle }, fmt(overview.openTodos))), /* @__PURE__ */ React.createElement("div", { style: metricCardStyle() }, /* @__PURE__ */ React.createElement("div", { style: metricLabelStyle }, "RTL Runs"), /* @__PURE__ */ React.createElement("div", { style: metricValueStyle }, fmt(overview.rtlRuns))), /* @__PURE__ */ React.createElement("div", { style: metricCardStyle() }, /* @__PURE__ */ React.createElement("div", { style: metricLabelStyle }, "Artifact Versions"), /* @__PURE__ */ React.createElement("div", { style: metricValueStyle }, fmt(overview.artifactVersions))), /* @__PURE__ */ React.createElement("div", { style: metricCardStyle() }, /* @__PURE__ */ React.createElement("div", { style: metricLabelStyle }, "Run Artifact Sets"), /* @__PURE__ */ React.createElement("div", { style: metricValueStyle }, fmt(overview.runArtifactSets))), /* @__PURE__ */ React.createElement("div", { style: metricCardStyle() }, /* @__PURE__ */ React.createElement("div", { style: metricLabelStyle }, "Human Inputs"), /* @__PURE__ */ React.createElement("div", { style: metricValueStyle }, fmt(overview.humanInputs))), /* @__PURE__ */ React.createElement("div", { style: metricCardStyle() }, /* @__PURE__ */ React.createElement("div", { style: metricLabelStyle }, "Input History"), /* @__PURE__ */ React.createElement("div", { style: metricValueStyle }, fmt(overview.inputRows))), /* @__PURE__ */ React.createElement("div", { style: metricCardStyle() }, /* @__PURE__ */ React.createElement("div", { style: metricLabelStyle }, "Memory Rules"), /* @__PURE__ */ React.createElement("div", { style: metricValueStyle }, fmt(overview.memoryRules))), /* @__PURE__ */ React.createElement("div", { style: metricCardStyle(overview.pendingHuman ? "danger" : "default") }, /* @__PURE__ */ React.createElement("div", { style: metricLabelStyle }, "Ask User Pending"), /* @__PURE__ */ React.createElement("div", { style: metricValueStyle }, fmt(overview.pendingHuman))), /* @__PURE__ */ React.createElement("div", { style: metricCardStyle(overview.pendingFeedback ? "danger" : "default") }, /* @__PURE__ */ React.createElement("div", { style: metricLabelStyle }, "Open Feedback"), /* @__PURE__ */ React.createElement("div", { style: metricValueStyle }, fmt(overview.pendingFeedback)))), /* @__PURE__ */ React.createElement("div", { style: dashboardGridStyle }, /* @__PURE__ */ React.createElement("div", { style: { ...tableWrapStyle, ...dashboardWideStyle } }, /* @__PURE__ */ React.createElement("div", { style: widgetHeaderStyle }, /* @__PURE__ */ React.createElement("div", { style: widgetTitleStyle }, "Active User Focus"), /* @__PURE__ */ React.createElement("div", { style: widgetMetaStyle }, "User \xB7 IP \xB7 Workflow \xB7 session")), /* @__PURE__ */ React.createElement("table", { style: tableStyle }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", { style: thStyle }, "User"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Active IP"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Active Workflow"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Sessions"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Status"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Updated"))), /* @__PURE__ */ React.createElement("tbody", null, activeUserRows.length === 0 ? /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", { colSpan: 6, style: { ...tdStyle, ...emptyStateStyle } }, "No active user focus in filter.")) : activeUserRows.map((row, index) => /* @__PURE__ */ React.createElement("tr", { key: rowKey("active-user", index, row.id, row.username) }, /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.username || "unknown"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.active_ip || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.active_workflow || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.session_count || 0)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.active_workflow_status || "active"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, formatDate(row.active_session_updated_at))))))), /* @__PURE__ */ React.createElement("div", { style: tableWrapStyle }, /* @__PURE__ */ React.createElement("div", { style: widgetHeaderStyle }, /* @__PURE__ */ React.createElement("div", { style: widgetTitleStyle }, "IP Workload"), /* @__PURE__ */ React.createElement("div", { style: widgetMetaStyle }, "cost weighted")), /* @__PURE__ */ React.createElement("table", { style: tableStyle }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", { style: thStyle }, "IP"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Load"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Calls"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Cost"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Users"))), /* @__PURE__ */ React.createElement("tbody", null, ipWorkloadRows.length === 0 ? /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", { colSpan: 5, style: { ...tdStyle, ...emptyStateStyle } }, "No IP workload in filter.")) : ipWorkloadRows.map((row, index) => {
      const width = `${Math.round(workloadScore(row) / maxIpScore * 100)}%`;
      return /* @__PURE__ */ React.createElement("tr", { key: rowKey("ip-workload", index, row.name) }, /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.name), /* @__PURE__ */ React.createElement("td", { style: { ...tdStyle, minWidth: 120 } }, /* @__PURE__ */ React.createElement("div", { style: barTrackStyle }, /* @__PURE__ */ React.createElement("div", { style: barFillStyle(width, "cost") })), /* @__PURE__ */ React.createElement("div", { style: mutedSmallStyle }, fmt(row.sessionCount), " sessions \xB7 ", fmt(row.tokens), " tokens")), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.calls)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, usd(row.cost)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.userCount)));
    })))), /* @__PURE__ */ React.createElement("div", { style: tableWrapStyle }, /* @__PURE__ */ React.createElement("div", { style: widgetHeaderStyle }, /* @__PURE__ */ React.createElement("div", { style: widgetTitleStyle }, "Workflow Load"), /* @__PURE__ */ React.createElement("div", { style: widgetMetaStyle }, "single/orchestrator aware")), /* @__PURE__ */ React.createElement("table", { style: tableStyle }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Workflow"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Load"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Calls"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Cost"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Sessions"))), /* @__PURE__ */ React.createElement("tbody", null, workflowWorkloadRows.length === 0 ? /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", { colSpan: 5, style: { ...tdStyle, ...emptyStateStyle } }, "No workflow load in filter.")) : workflowWorkloadRows.map((row, index) => {
      const width = `${Math.round(workloadScore(row) / maxWorkflowScore * 100)}%`;
      return /* @__PURE__ */ React.createElement("tr", { key: rowKey("workflow-workload", index, row.name) }, /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.name), /* @__PURE__ */ React.createElement("td", { style: { ...tdStyle, minWidth: 120 } }, /* @__PURE__ */ React.createElement("div", { style: barTrackStyle }, /* @__PURE__ */ React.createElement("div", { style: barFillStyle(width) })), /* @__PURE__ */ React.createElement("div", { style: mutedSmallStyle }, fmt(row.userCount), " users \xB7 ", fmt(row.tokens), " tokens")), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.calls)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, usd(row.cost)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.sessionCount)));
    })))), /* @__PURE__ */ React.createElement("div", { style: { ...tableWrapStyle, ...dashboardWideStyle } }, /* @__PURE__ */ React.createElement("div", { style: widgetHeaderStyle }, /* @__PURE__ */ React.createElement("div", { style: widgetTitleStyle }, "Recent Sessions"), /* @__PURE__ */ React.createElement("div", { style: widgetMetaStyle }, "latest active context")), /* @__PURE__ */ React.createElement("table", { style: tableStyle }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Owner"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "IP"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Workflow"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Status"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Session"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Updated"))), /* @__PURE__ */ React.createElement("tbody", null, recentSessionRows.length === 0 ? /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", { colSpan: 6, style: { ...tdStyle, ...emptyStateStyle } }, "No sessions in filter.")) : recentSessionRows.map((row, index) => /* @__PURE__ */ React.createElement("tr", { key: rowKey("recent-session", index, row.id, row.owner_username, row.ip, row.workflow) }, /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.owner_username || row.user_id || "unknown"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.ip || row.project_id || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.workflow || row.latest_workflow || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.status || "\u2014"), /* @__PURE__ */ React.createElement(
      "td",
      {
        style: { ...tdStyle, fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace", fontSize: 11, maxWidth: 260, wordBreak: "break-word" },
        title: row.id || ""
      },
      sessionDisplay(row)
    ), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, formatDate(row.updated_at))))))), /* @__PURE__ */ React.createElement("div", { style: { ...tableWrapStyle, ...dashboardWideStyle } }, /* @__PURE__ */ React.createElement("div", { style: widgetHeaderStyle }, /* @__PURE__ */ React.createElement("div", { style: widgetTitleStyle }, "Recent Stages"), /* @__PURE__ */ React.createElement("div", { style: widgetMetaStyle }, "run stage status by IP/workflow")), /* @__PURE__ */ React.createElement("table", { style: tableStyle }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", { style: thStyle }, "IP"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Workflow"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Stage"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Status"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Attempt"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Duration"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Updated"))), /* @__PURE__ */ React.createElement("tbody", null, recentStageRows.length === 0 ? /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", { colSpan: 7, style: { ...tdStyle, ...emptyStateStyle } }, "No workflow stage rows in filter.")) : recentStageRows.map((row, index) => /* @__PURE__ */ React.createElement("tr", { key: rowKey("recent-stage", index, row.stage_id, row.run_id, row.stage_name) }, /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.ip || "unknown"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.workflow || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.stage_name || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, /* @__PURE__ */ React.createElement("span", { style: statusPillStyle(row.status) }, row.status || "unknown")), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.attempt)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, durationMs(row.duration_ms)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, formatDate(row.updated_at || row.ended_at || row.started_at)))))))), /* @__PURE__ */ React.createElement("div", { style: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 430px), 1fr))", gap: 18 } }, /* @__PURE__ */ React.createElement("div", { style: tableWrapStyle }, /* @__PURE__ */ React.createElement("div", { style: panelTitleStyle }, "Top Cost Contexts"), /* @__PURE__ */ React.createElement("table", { style: tableStyle }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", { style: thStyle }, "IP"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Workspace"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Workflow"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Calls"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Cost"))), /* @__PURE__ */ React.createElement("tbody", null, topCostRows.length === 0 ? /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", { colSpan: 5, style: { ...tdStyle, ...emptyStateStyle } }, "No cost data in filter.")) : topCostRows.map((row, index) => /* @__PURE__ */ React.createElement("tr", { key: rowKey("top-cost", index, row.session_id, row.ip, row.workflow, row.workspace) }, /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.ip || "unknown"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.workspace || "default"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.workflow || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.calls)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, usd(row.cost))))))), /* @__PURE__ */ React.createElement("div", { style: tableWrapStyle }, /* @__PURE__ */ React.createElement("div", { style: panelTitleStyle }, "Tool Pressure"), /* @__PURE__ */ React.createElement("table", { style: tableStyle }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Tool"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "IP"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Failures"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Obs Tokens"))), /* @__PURE__ */ React.createElement("tbody", null, topToolRows.length === 0 ? /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", { colSpan: 4, style: { ...tdStyle, ...emptyStateStyle } }, "No tool data in filter.")) : topToolRows.map((row, index) => /* @__PURE__ */ React.createElement("tr", { key: rowKey("top-tool", index, row.session_id, row.ip, row.workflow, row.tool_name) }, /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.tool_name || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.ip || "unknown"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.failed_calls)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.observation_tokens_est))))))), /* @__PURE__ */ React.createElement("div", { style: tableWrapStyle }, /* @__PURE__ */ React.createElement("div", { style: panelTitleStyle }, "Rejected Todo Hotspots"), /* @__PURE__ */ React.createElement("table", { style: tableStyle }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Todo"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "IP"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Rejects"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Last Reason"))), /* @__PURE__ */ React.createElement("tbody", null, topRejectedTodos.length === 0 ? /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", { colSpan: 4, style: { ...tdStyle, ...emptyStateStyle } }, "No rejected todos in filter.")) : topRejectedTodos.map((row, index) => /* @__PURE__ */ React.createElement("tr", { key: rowKey("top-rejected-todo", index, row.todo_id, row.ip, row.workflow) }, /* @__PURE__ */ React.createElement("td", { style: { ...tdStyle, maxWidth: 260, whiteSpace: "normal" } }, row.content || shortId(row.todo_id)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.ip || "unknown"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.rejected_count)), /* @__PURE__ */ React.createElement("td", { style: { ...tdStyle, maxWidth: 320, whiteSpace: "normal" } }, row.last_rejected_reason || row.last_event_reason || "\u2014")))))), /* @__PURE__ */ React.createElement("div", { style: tableWrapStyle }, /* @__PURE__ */ React.createElement("div", { style: panelTitleStyle }, "Human Intervention Hotspots"), /* @__PURE__ */ React.createElement("table", { style: tableStyle }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", { style: thStyle }, "User"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "IP"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Workflow"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Inputs"))), /* @__PURE__ */ React.createElement("tbody", null, topHumanRows.length === 0 ? /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", { colSpan: 4, style: { ...tdStyle, ...emptyStateStyle } }, "No human input in filter.")) : topHumanRows.map((row, index) => /* @__PURE__ */ React.createElement("tr", { key: rowKey("top-human", index, row.session_id, row.ip, row.workflow, row.username) }, /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.username || "unknown"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.ip || "unknown"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.workflow || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.intervention_count))))))))), activeTab === "users" && /* @__PURE__ */ React.createElement("div", { style: tableWrapStyle }, /* @__PURE__ */ React.createElement("table", { style: tableStyle }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Username"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Email"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Display Name"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Role"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Active IP"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Active Workflow"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Sessions"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Active Updated"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Created"))), /* @__PURE__ */ React.createElement("tbody", null, filteredUsers.length === 0 ? /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", { colSpan: 9, style: { ...tdStyle, ...emptyStateStyle } }, "No users found.")) : filteredUsers.map((u, index) => /* @__PURE__ */ React.createElement("tr", { key: rowKey("user", index, u.id, u.username) }, /* @__PURE__ */ React.createElement("td", { style: tdStyle }, u.username), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, u.email || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, u.display_name || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, /* @__PURE__ */ React.createElement("span", { style: {
      fontSize: 10,
      fontWeight: 600,
      textTransform: "uppercase",
      padding: "2px 6px",
      borderRadius: 3,
      background: u.role === "admin" ? "#2a3a4a" : "#1c252f",
      color: u.role === "admin" ? "#f0c674" : "#a3aebb",
      border: "1px solid #2a3540"
    } }, u.role)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, u.active_ip || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, u.active_workflow || "\u2014", u.active_workflow_status ? /* @__PURE__ */ React.createElement("div", { style: { opacity: 0.65, fontSize: 11 } }, u.active_workflow_status) : null), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, u.session_count ?? 0), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, formatDate(u.active_session_updated_at)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, formatDate(u.created_at))))))), activeTab === "sessions" && /* @__PURE__ */ React.createElement("div", { style: tableWrapStyle }, /* @__PURE__ */ React.createElement("table", { style: tableStyle }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Title"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "IP"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Workflow"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Status"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Owner"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Session"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Latest Run"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Updated"), /* @__PURE__ */ React.createElement("th", { style: thStyle }))), /* @__PURE__ */ React.createElement("tbody", null, filteredSessions.length === 0 ? /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", { colSpan: 9, style: { ...tdStyle, ...emptyStateStyle } }, "No sessions found.")) : filteredSessions.map((s, index) => /* @__PURE__ */ React.createElement("tr", { key: rowKey("session", index, s.id, s.user_id, s.ip, s.workflow) }, /* @__PURE__ */ React.createElement("td", { style: tdStyle }, s.title || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, s.ip || s.project_id || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, s.workflow || s.latest_workflow || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, /* @__PURE__ */ React.createElement("span", { style: {
      fontSize: 10,
      fontWeight: 600,
      textTransform: "uppercase",
      padding: "2px 6px",
      borderRadius: 3,
      background: s.status === "active" ? "#1c2f25" : "#1c252f",
      color: s.status === "active" ? "#7dc9a0" : "#a3aebb",
      border: "1px solid #2a3540"
    } }, s.status)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, s.owner_username || s.user_id || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: { ...tdStyle, fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace", fontSize: 11 } }, s.id || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, s.pipeline_run_id || s.latest_workflow_run_id || "\u2014", s.latest_workflow_status ? /* @__PURE__ */ React.createElement("div", { style: { opacity: 0.65, fontSize: 11 } }, s.latest_workflow_status) : null), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, formatDate(s.updated_at)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, /* @__PURE__ */ React.createElement(
      "button",
      {
        style: btnDangerStyle,
        onClick: () => handleDeleteSession(s.id),
        disabled: deleting === s.id
      },
      deleting === s.id ? "Deleting\u2026" : "Delete"
    ))))))), activeTab === "stages" && /* @__PURE__ */ React.createElement("div", { style: tableWrapStyle }, /* @__PURE__ */ React.createElement("table", { style: tableStyle }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", { style: thStyle }, "When"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "User"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "IP"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Workspace"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Workflow"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Stage"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Status"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Attempt"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Duration"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Run"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "LLM"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Cost"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Error"))), /* @__PURE__ */ React.createElement("tbody", null, filteredWorkflowStages.length === 0 ? /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", { colSpan: 13, style: { ...tdStyle, ...emptyStateStyle } }, "No workflow stage rows yet.")) : filteredWorkflowStages.map((row, index) => /* @__PURE__ */ React.createElement("tr", { key: rowKey("workflow-stage", index, row.stage_id, row.run_id, row.stage_name) }, /* @__PURE__ */ React.createElement("td", { style: tdStyle }, formatDate(row.started_at || row.created_at)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.username || "unknown"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.ip || "unknown"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.workspace || "default"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.workflow || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, /* @__PURE__ */ React.createElement("div", null, row.stage_name || "\u2014"), row.trigger_source && /* @__PURE__ */ React.createElement("div", { style: { color: "#8893a3", fontSize: 11, marginTop: 3 } }, row.trigger_source)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, /* @__PURE__ */ React.createElement("span", { style: statusPillStyle(row.status) }, row.status || "unknown")), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.attempt)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, durationMs(row.duration_ms)), /* @__PURE__ */ React.createElement("td", { style: tdStyle, title: row.run_id || "" }, shortId(row.run_id)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.llm_calls)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, usd(row.cost)), /* @__PURE__ */ React.createElement("td", { style: { ...tdStyle, maxWidth: 300, whiteSpace: "normal" } }, row.error_summary || "\u2014")))))), activeTab === "usage" && /* @__PURE__ */ React.createElement("div", { style: tableWrapStyle }, /* @__PURE__ */ React.createElement("table", { style: tableStyle }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Username"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Role"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Sessions"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Messages"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Tokens In"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Tokens Out"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Reasoning"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Cost (USD)"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Last Activity"))), /* @__PURE__ */ React.createElement("tbody", null, filteredUsage.length === 0 ? /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", { colSpan: 9, style: { ...tdStyle, ...emptyStateStyle } }, "No usage data yet.")) : filteredUsage.flatMap((u, index) => {
      const expanded = expandedUsage === u.user_id;
      const rows = [
        /* @__PURE__ */ React.createElement(
          "tr",
          {
            key: rowKey("usage", index, u.user_id, u.username),
            style: { cursor: "pointer" },
            onClick: () => setExpandedUsage(expanded ? null : u.user_id),
            title: expanded ? "click to collapse" : "click to see model + tool breakdown"
          },
          /* @__PURE__ */ React.createElement("td", { style: tdStyle }, /* @__PURE__ */ React.createElement("span", { style: { marginRight: 6, opacity: 0.6 } }, expanded ? "\u25BE" : "\u25B8"), u.username),
          /* @__PURE__ */ React.createElement("td", { style: tdStyle }, u.role),
          /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(u.session_count)),
          /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(u.message_count)),
          /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(u.tokens_in)),
          /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(u.tokens_out)),
          /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(u.tokens_reasoning)),
          /* @__PURE__ */ React.createElement("td", { style: tdStyle }, usd(u.total_cost_usd)),
          /* @__PURE__ */ React.createElement("td", { style: tdStyle }, formatDate(u.last_message_at))
        )
      ];
      if (expanded) {
        rows.push(
          /* @__PURE__ */ React.createElement("tr", { key: rowKey("usage-detail", index, u.user_id, u.username) }, /* @__PURE__ */ React.createElement("td", { colSpan: 9, style: { ...tdStyle, background: "#10141a", padding: "12px 16px" } }, /* @__PURE__ */ React.createElement("div", { style: { display: "flex", gap: 28, flexWrap: "wrap" } }, /* @__PURE__ */ React.createElement("div", { style: { minWidth: 260 } }, /* @__PURE__ */ React.createElement("div", { style: {
            fontSize: 11,
            opacity: 0.7,
            marginBottom: 6,
            textTransform: "uppercase",
            letterSpacing: "0.06em"
          } }, "Models"), (u.models || []).length === 0 ? /* @__PURE__ */ React.createElement("div", { style: { opacity: 0.5, fontSize: 12 } }, "no model usage") : /* @__PURE__ */ React.createElement("table", { style: { fontSize: 12, borderCollapse: "collapse" } }, /* @__PURE__ */ React.createElement("tbody", null, u.models.slice(0, 8).map((m, modelIndex) => /* @__PURE__ */ React.createElement("tr", { key: rowKey("usage-model", modelIndex, u.user_id, m.model_id) }, /* @__PURE__ */ React.createElement("td", { style: { padding: "2px 10px 2px 0" } }, m.model_id), /* @__PURE__ */ React.createElement("td", { style: { padding: "2px 10px", textAlign: "right", opacity: 0.7 } }, fmt(m.calls), " calls"), /* @__PURE__ */ React.createElement("td", { style: { padding: "2px 10px", textAlign: "right", opacity: 0.7 } }, fmt(m.tokens), " tok"), /* @__PURE__ */ React.createElement("td", { style: { padding: "2px 0", textAlign: "right", opacity: 0.7 } }, usd(m.cost))))))), /* @__PURE__ */ React.createElement("div", { style: { minWidth: 220 } }, /* @__PURE__ */ React.createElement("div", { style: {
            fontSize: 11,
            opacity: 0.7,
            marginBottom: 6,
            textTransform: "uppercase",
            letterSpacing: "0.06em"
          } }, "Top Tools"), (u.tools || []).length === 0 ? /* @__PURE__ */ React.createElement("div", { style: { opacity: 0.5, fontSize: 12 } }, "no tool calls") : /* @__PURE__ */ React.createElement("table", { style: { fontSize: 12, borderCollapse: "collapse" } }, /* @__PURE__ */ React.createElement("tbody", null, u.tools.slice(0, 10).map((t, toolIndex) => /* @__PURE__ */ React.createElement("tr", { key: rowKey("usage-tool", toolIndex, u.user_id, t.tool_name) }, /* @__PURE__ */ React.createElement("td", { style: { padding: "2px 12px 2px 0" } }, t.tool_name), /* @__PURE__ */ React.createElement("td", { style: { padding: "2px 0", textAlign: "right", opacity: 0.7 } }, fmt(t.calls))))))))))
        );
      }
      return rows;
    })))), activeTab === "costs" && /* @__PURE__ */ React.createElement("div", { style: {
      display: "grid",
      gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 420px), 1fr))",
      gap: 18,
      alignItems: "start"
    } }, /* @__PURE__ */ React.createElement("div", { style: tableWrapStyle }, /* @__PURE__ */ React.createElement("div", { style: {
      padding: "12px 14px",
      borderBottom: "1px solid #2a3540",
      background: "#1c252f",
      color: "#f0c674",
      fontSize: 12,
      fontWeight: 700,
      textTransform: "uppercase",
      letterSpacing: "0.06em"
    } }, "Cost by IP / Workspace"), /* @__PURE__ */ React.createElement("table", { style: tableStyle }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", { style: thStyle }, "IP / Project"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Workspace"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Session"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "User"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Calls"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Tokens"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Cost"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Last"))), /* @__PURE__ */ React.createElement("tbody", null, filteredCostContexts.length === 0 ? /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", { colSpan: 8, style: { ...tdStyle, ...emptyStateStyle } }, "No cost data yet.")) : filteredCostContexts.map((row, index) => /* @__PURE__ */ React.createElement("tr", { key: rowKey("cost-context", index, row.session_id, row.ip, row.workspace, row.username) }, /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.ip || "unknown"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.workspace || "default"), /* @__PURE__ */ React.createElement("td", { style: tdStyle, title: row.session_id || "" }, sessionDisplay(row)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.username || "unknown"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.calls)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.tokens)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, usd(row.cost)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, formatDate(row.last_message_at))))))), /* @__PURE__ */ React.createElement("div", { style: tableWrapStyle }, /* @__PURE__ */ React.createElement("div", { style: {
      padding: "12px 14px",
      borderBottom: "1px solid #2a3540",
      background: "#1c252f",
      color: "#f0c674",
      fontSize: 12,
      fontWeight: 700,
      textTransform: "uppercase",
      letterSpacing: "0.06em"
    } }, "Cost by Date"), /* @__PURE__ */ React.createElement("table", { style: tableStyle }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Date"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "IP / Project"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Workspace"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Calls"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Tokens"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Cost"))), /* @__PURE__ */ React.createElement("tbody", null, filteredDateCosts.length === 0 ? /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", { colSpan: 6, style: { ...tdStyle, ...emptyStateStyle } }, "No daily cost data yet.")) : filteredDateCosts.map((row, index) => /* @__PURE__ */ React.createElement("tr", { key: rowKey("date-cost", index, row.day, row.session_id, row.ip, row.workspace) }, /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.day || "unknown"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.ip || "unknown"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.workspace || "default"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.calls)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.tokens)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, usd(row.cost)))))))), activeTab === "todos" && /* @__PURE__ */ React.createElement("div", { style: tableWrapStyle }, /* @__PURE__ */ React.createElement("table", { style: tableStyle }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", { style: thStyle }, "IP"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Workspace"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Workflow"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Todo"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Status"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Rejects"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "LLM Calls"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Tokens"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Cost"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Last Reason"))), /* @__PURE__ */ React.createElement("tbody", null, filteredTodoUsage.length === 0 ? /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", { colSpan: 10, style: { ...tdStyle, ...emptyStateStyle } }, "No todo usage data yet.")) : filteredTodoUsage.map((row, index) => /* @__PURE__ */ React.createElement("tr", { key: rowKey("todo-usage", index, row.todo_id, row.ip, row.workflow) }, /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.ip || "unknown"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.workspace || "default"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.workflow || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: { ...tdStyle, minWidth: 240 } }, /* @__PURE__ */ React.createElement("div", null, row.content || "\u2014"), /* @__PURE__ */ React.createElement("div", { style: { color: "#8893a3", fontSize: 11, marginTop: 4 } }, row.detail || row.criteria || "\u2014")), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.status || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.rejected_count)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.llm_calls)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.tokens)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, usd(row.cost)), /* @__PURE__ */ React.createElement("td", { style: { ...tdStyle, maxWidth: 260, whiteSpace: "normal" } }, row.last_event_reason || row.last_rejected_reason || "\u2014")))))), activeTab === "flow" && /* @__PURE__ */ React.createElement("div", { style: tableWrapStyle }, /* @__PURE__ */ React.createElement("table", { style: tableStyle }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", { style: thStyle }, "When"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "IP"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Workflow"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Todo"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Event"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Reason"))), /* @__PURE__ */ React.createElement("tbody", null, filteredTodoFlow.length === 0 ? /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", { colSpan: 6, style: { ...tdStyle, ...emptyStateStyle } }, "No todo flow events yet.")) : filteredTodoFlow.map((row, index) => /* @__PURE__ */ React.createElement("tr", { key: rowKey("todo-flow", index, row.event_id, row.todo_id, row.event_type) }, /* @__PURE__ */ React.createElement("td", { style: tdStyle }, formatDate(row.created_at)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.ip || "unknown"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.workflow || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: { ...tdStyle, maxWidth: 300, whiteSpace: "normal" } }, row.content || shortId(row.todo_id)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.event_type || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: { ...tdStyle, maxWidth: 360, whiteSpace: "normal" } }, row.reason || "\u2014")))))), activeTab === "trace" && /* @__PURE__ */ React.createElement("div", { style: tableWrapStyle }, /* @__PURE__ */ React.createElement("table", { style: tableStyle }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", { style: thStyle }, "When"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Event"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "IP"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Workspace"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Workflow"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "User"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Run"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Todo"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Correlation"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Payload"))), /* @__PURE__ */ React.createElement("tbody", null, filteredTraceEvents.length === 0 ? /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", { colSpan: 10, style: { ...tdStyle, ...emptyStateStyle } }, "No trace events yet.")) : filteredTraceEvents.map((row, index) => /* @__PURE__ */ React.createElement("tr", { key: rowKey("trace-event", index, row.event_id, row.correlation_id, row.event_type) }, /* @__PURE__ */ React.createElement("td", { style: tdStyle }, formatDate(row.created_at)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.event_type || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.ip || "unknown"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.workspace || "default"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.workflow || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.username || shortId(row.actor_user_id)), /* @__PURE__ */ React.createElement("td", { style: tdStyle, title: row.run_id || "" }, shortId(row.run_id)), /* @__PURE__ */ React.createElement("td", { style: tdStyle, title: row.todo_id || "" }, shortId(row.todo_id)), /* @__PURE__ */ React.createElement("td", { style: tdStyle, title: row.correlation_id || "" }, shortId(row.correlation_id)), /* @__PURE__ */ React.createElement("td", { style: { ...tdStyle, maxWidth: 360, whiteSpace: "normal", wordBreak: "break-word" } }, payloadText(row.payload))))))), activeTab === "tools" && /* @__PURE__ */ React.createElement("div", { style: tableWrapStyle }, /* @__PURE__ */ React.createElement("table", { style: tableStyle }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Tool"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Calls"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Failures"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Obs Tokens (est)"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Obs Chars"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Avg Latency"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "IP"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Workspace"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Workflow"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Session"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "User"))), /* @__PURE__ */ React.createElement("tbody", null, filteredToolUsage.length === 0 ? /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", { colSpan: 11, style: { ...tdStyle, ...emptyStateStyle } }, "No tool usage data yet.")) : filteredToolUsage.map((row, index) => /* @__PURE__ */ React.createElement("tr", { key: rowKey("tool-usage", index, row.session_id, row.ip, row.workflow, row.tool_name) }, /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.tool_name || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.calls)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.failed_calls)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.observation_tokens_est)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.observation_chars)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.avg_latency_ms == null ? "\u2014" : `${Number(row.avg_latency_ms).toFixed(0)} ms`), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.ip || "unknown"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.workspace || "default"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.workflow || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle, title: row.session_id || "" }, sessionDisplay(row)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.username || "unknown")))))), activeTab === "rtl" && /* @__PURE__ */ React.createElement("div", { style: tableWrapStyle }, /* @__PURE__ */ React.createElement("table", { style: tableStyle }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", { style: thStyle }, "When"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "IP"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Workspace"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Workflow"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Status"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "RTL Version"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Git Tag"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Tree Hash"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Top"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "LLM Calls"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Cost"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Error"))), /* @__PURE__ */ React.createElement("tbody", null, filteredRtlRunHistory.length === 0 ? /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", { colSpan: 12, style: { ...tdStyle, ...emptyStateStyle } }, "No RTL-versioned downstream runs yet.")) : filteredRtlRunHistory.map((row, index) => /* @__PURE__ */ React.createElement("tr", { key: rowKey("rtl-run", index, row.run_id, row.rtl_version_id, row.ip, row.workflow) }, /* @__PURE__ */ React.createElement("td", { style: tdStyle }, formatDate(row.started_at || row.created_at)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.ip || "unknown"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.workspace || "default"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.workflow || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.status || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle, title: row.rtl_version_id || "" }, /* @__PURE__ */ React.createElement("div", null, row.rtl_version || shortId(row.rtl_version_id)), row.rtl_label && /* @__PURE__ */ React.createElement("div", { style: { color: "#8893a3", fontSize: 11, marginTop: 3 } }, row.rtl_label)), /* @__PURE__ */ React.createElement("td", { style: { ...tdStyle, maxWidth: 220, wordBreak: "break-word" } }, row.rtl_git_tag || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle, title: row.rtl_sha256_tree || "" }, shortId(row.rtl_sha256_tree)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.rtl_top_module || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.llm_calls)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, usd(row.cost)), /* @__PURE__ */ React.createElement("td", { style: { ...tdStyle, maxWidth: 280, whiteSpace: "normal" } }, row.error_summary || "\u2014")))))), activeTab === "versions" && /* @__PURE__ */ React.createElement("div", { style: tableWrapStyle }, /* @__PURE__ */ React.createElement("table", { style: tableStyle }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Created"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "IP"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Workspace"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Type"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Version"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Status"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Git Tag"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Tree Hash"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Primary Path"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Source Run"))), /* @__PURE__ */ React.createElement("tbody", null, filteredArtifactVersions.length === 0 ? /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", { colSpan: 10, style: { ...tdStyle, ...emptyStateStyle } }, "No artifact versions yet.")) : filteredArtifactVersions.map((row, index) => /* @__PURE__ */ React.createElement("tr", { key: rowKey("artifact-version", index, row.artifact_version_id, row.artifact_type, row.ip) }, /* @__PURE__ */ React.createElement("td", { style: tdStyle }, formatDate(row.created_at)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.ip || "unknown"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.workspace || "default"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.artifact_type || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle, title: row.artifact_version_id || "" }, row.version || shortId(row.artifact_version_id)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.status || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: { ...tdStyle, maxWidth: 220, wordBreak: "break-word" } }, row.git_tag || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle, title: row.sha256_tree || "" }, shortId(row.sha256_tree)), /* @__PURE__ */ React.createElement("td", { style: { ...tdStyle, maxWidth: 280, wordBreak: "break-word" } }, row.primary_path || row.root_path || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle, title: row.source_run_id || "" }, shortId(row.source_run_id))))))), activeTab === "run-sets" && /* @__PURE__ */ React.createElement("div", { style: tableWrapStyle }, /* @__PURE__ */ React.createElement("table", { style: tableStyle }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", { style: thStyle }, "When"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "IP"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Workspace"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Workflow"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Status"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "SSOT"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "RTL"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "TB"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "SSOT Anchor"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "RTL Anchor"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "TB Anchor"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "LLM Calls"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Cost"))), /* @__PURE__ */ React.createElement("tbody", null, filteredRunArtifactSets.length === 0 ? /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", { colSpan: 13, style: { ...tdStyle, ...emptyStateStyle } }, "No run artifact sets yet.")) : filteredRunArtifactSets.map((row, index) => /* @__PURE__ */ React.createElement("tr", { key: rowKey("run-artifact-set", index, row.run_id, row.ip, row.workflow) }, /* @__PURE__ */ React.createElement("td", { style: tdStyle }, formatDate(row.started_at || row.created_at)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.ip || "unknown"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.workspace || "default"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.workflow || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.status || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, versionText(row, "ssot")), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, versionText(row, "rtl")), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, versionText(row, "tb")), /* @__PURE__ */ React.createElement("td", { style: { ...tdStyle, maxWidth: 220, wordBreak: "break-word" } }, versionTagText(row, "ssot")), /* @__PURE__ */ React.createElement("td", { style: { ...tdStyle, maxWidth: 220, wordBreak: "break-word" } }, versionTagText(row, "rtl")), /* @__PURE__ */ React.createElement("td", { style: { ...tdStyle, maxWidth: 220, wordBreak: "break-word" } }, versionTagText(row, "tb")), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.llm_calls)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, usd(row.cost))))))), activeTab === "human" && /* @__PURE__ */ React.createElement("div", { style: tableWrapStyle }, /* @__PURE__ */ React.createElement("table", { style: tableStyle }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", { style: thStyle }, "User"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Session"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "IP"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Workspace"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Workflow"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Total"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Prompts"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Chat"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Ask User"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "SSOT QA"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Last"))), /* @__PURE__ */ React.createElement("tbody", null, filteredInterventions.length === 0 ? /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", { colSpan: 11, style: { ...tdStyle, ...emptyStateStyle } }, "No human intervention data yet.")) : filteredInterventions.map((row, index) => /* @__PURE__ */ React.createElement("tr", { key: rowKey("intervention", index, row.session_id, row.ip, row.workflow, row.username) }, /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.username || "unknown"), /* @__PURE__ */ React.createElement("td", { style: tdStyle, title: row.session_id || "" }, sessionDisplay(row)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.ip || "unknown"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.workspace || "default"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.workflow || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.intervention_count)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.user_messages)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.chat_messages)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.ask_user_answers)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.ssot_qa_answers)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, formatDate(row.last_intervention_at))))))), activeTab === "inputs" && /* @__PURE__ */ React.createElement("div", { style: tableWrapStyle }, /* @__PURE__ */ React.createElement("table", { style: tableStyle }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", { style: thStyle }, "When"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "User"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Source"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "IP"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Workflow"), /* @__PURE__ */ React.createElement("th", { style: { ...thStyle, width: "46%" } }, "Input"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Session"))), /* @__PURE__ */ React.createElement("tbody", null, filteredInputHistory.length === 0 ? /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", { colSpan: 7, style: { ...tdStyle, ...emptyStateStyle } }, "No user input history yet.")) : filteredInputHistory.map((row, index) => /* @__PURE__ */ React.createElement("tr", { key: rowKey("input-history", index, row.input_id, row.session_id, row.created_at) }, /* @__PURE__ */ React.createElement("td", { style: tdStyle }, formatDate(row.created_at)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.username || "unknown"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.source || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.ip || "unknown"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.workflow || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: { ...tdStyle, whiteSpace: "pre-wrap", wordBreak: "break-word" } }, row.content || payloadText(row.payload)), /* @__PURE__ */ React.createElement("td", { style: tdStyle, title: row.session_id || "" }, sessionDisplay(row))))))), activeTab === "memory" && /* @__PURE__ */ React.createElement("div", { style: tableWrapStyle }, /* @__PURE__ */ React.createElement("table", { style: tableStyle }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Updated"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "User"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Scope"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Workflow"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "#"), /* @__PURE__ */ React.createElement("th", { style: { ...thStyle, width: "54%" } }, "Rule"))), /* @__PURE__ */ React.createElement("tbody", null, filteredMemoryRules.length === 0 ? /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", { colSpan: 6, style: { ...tdStyle, ...emptyStateStyle } }, "No memory rules yet.")) : filteredMemoryRules.map((row, index) => /* @__PURE__ */ React.createElement("tr", { key: rowKey("memory-rule", index, row.id, row.user_id, row.position) }, /* @__PURE__ */ React.createElement("td", { style: tdStyle }, formatDate(row.updated_at || row.created_at)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.username || "unknown"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.scope || "global"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.workflow || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.position || index + 1), /* @__PURE__ */ React.createElement("td", { style: { ...tdStyle, whiteSpace: "pre-wrap", wordBreak: "break-word" } }, row.rule || "\u2014")))))), activeTab === "runtime" && /* @__PURE__ */ React.createElement("div", { style: { display: "flex", flexDirection: "column", gap: 16 } }, /* @__PURE__ */ React.createElement("div", { style: overviewGridStyle }, /* @__PURE__ */ React.createElement("div", { style: metricCardStyle() }, /* @__PURE__ */ React.createElement("div", { style: metricLabelStyle }, "Worker Transport"), /* @__PURE__ */ React.createElement("div", { style: metricValueStyle }, runtimeTransport)), /* @__PURE__ */ React.createElement("div", { style: metricCardStyle() }, /* @__PURE__ */ React.createElement("div", { style: metricLabelStyle }, "IPC Running"), /* @__PURE__ */ React.createElement("div", { style: metricValueStyle }, fmt(ipcRuntime.running_count || 0))), /* @__PURE__ */ React.createElement("div", { style: metricCardStyle(ipcRuntime.queued_count || 0 ? "danger" : "default") }, /* @__PURE__ */ React.createElement("div", { style: metricLabelStyle }, "IPC Queued"), /* @__PURE__ */ React.createElement("div", { style: metricValueStyle }, fmt(ipcRuntime.queued_count || 0))), /* @__PURE__ */ React.createElement("div", { style: metricCardStyle() }, /* @__PURE__ */ React.createElement("div", { style: metricLabelStyle }, "IPC Slots"), /* @__PURE__ */ React.createElement("div", { style: metricValueStyle }, fmt(ipcRuntime.available_slots || 0))), /* @__PURE__ */ React.createElement("div", { style: metricCardStyle() }, /* @__PURE__ */ React.createElement("div", { style: metricLabelStyle }, "SCM Provider"), /* @__PURE__ */ React.createElement("div", { style: metricValueStyle }, runtimeScm.provider || "auto")), /* @__PURE__ */ React.createElement("div", { style: metricCardStyle(runtimeScm.ui_override && runtimeScm.ui_override.enabled ? "default" : "danger") }, /* @__PURE__ */ React.createElement("div", { style: metricLabelStyle }, "SCM UI Override"), /* @__PURE__ */ React.createElement("div", { style: metricValueStyle }, runtimeScm.ui_override && runtimeScm.ui_override.enabled ? "on" : "off"))), /* @__PURE__ */ React.createElement("div", { style: tableWrapStyle }, /* @__PURE__ */ React.createElement("div", { style: widgetHeaderStyle }, /* @__PURE__ */ React.createElement("div", { style: widgetTitleStyle }, "Runtime Settings"), /* @__PURE__ */ React.createElement("div", { style: widgetMetaStyle }, runtimeAtlas.exec_mode || "mode unknown")), /* @__PURE__ */ React.createElement("table", { style: tableStyle }, /* @__PURE__ */ React.createElement("tbody", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Run Mode"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, runtimeAtlas.run_mode || "\u2014"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Exec Mode"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, runtimeAtlas.exec_mode || "\u2014")), /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", { style: thStyle }, "IPC Max"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(ipcLimits.max_concurrent), " total \xB7 ", fmt(ipcLimits.max_per_user), " per user \xB7 ", fmt(ipcLimits.max_per_workflow), " per workflow"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Queue / Timeout"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(ipcLimits.queue_limit), " queue \xB7 ", fmt(ipcLimits.timeout_sec), "s \xB7 ", fmt(ipcLimits.max_attempts), " attempts")), /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", { style: thStyle }, "SCM Override"), /* @__PURE__ */ React.createElement("td", { style: { ...tdStyle, wordBreak: "break-word" } }, runtimeScm.ui_override && runtimeScm.ui_override.ref ? runtimeScm.ui_override.ref : "\u2014"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Override File"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, runtimeScm.ui_override && runtimeScm.ui_override.kind ? `${runtimeScm.ui_override.kind}${runtimeScm.ui_override.exists === false ? " missing" : ""}` : "\u2014")))), runtime && runtime.note ? /* @__PURE__ */ React.createElement("div", { style: { ...tdStyle, color: "#8893a3" } }, runtime.note) : null), /* @__PURE__ */ React.createElement("div", { style: tableWrapStyle }, /* @__PURE__ */ React.createElement("div", { style: widgetHeaderStyle }, /* @__PURE__ */ React.createElement("div", { style: widgetTitleStyle }, "IPC Jobs"), /* @__PURE__ */ React.createElement("div", { style: widgetMetaStyle }, "live queue and retry state")), /* @__PURE__ */ React.createElement("table", { style: tableStyle }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Job"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Workflow"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "IP"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Status"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Queue"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Attempt"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Owner"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Worker"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Error"))), /* @__PURE__ */ React.createElement("tbody", null, ipcJobs.length === 0 ? /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", { colSpan: 9, style: { ...tdStyle, ...emptyStateStyle } }, "No IPC worker jobs in this process.")) : ipcJobs.map((job, index) => /* @__PURE__ */ React.createElement("tr", { key: rowKey("runtime-ipc-job", index, job.job_id, job.run_id) }, /* @__PURE__ */ React.createElement("td", { style: tdStyle, title: job.job_id || "" }, shortId(job.job_id)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, job.workflow || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, job.ip || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, /* @__PURE__ */ React.createElement("span", { style: statusPillStyle(job.status) }, job.status || "unknown")), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, job.queue_reason || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(job.attempt || 1), " / ", fmt(job.max_attempts || 1)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, job.user_id || job.db_user_id || job.worker_owner || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: { ...tdStyle, maxWidth: 280, wordBreak: "break-word" } }, job.worker || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: { ...tdStyle, maxWidth: 320, whiteSpace: "normal" } }, job.last_retry_reason || job.error || "\u2014"))))))), activeTab === "feedback" && /* @__PURE__ */ React.createElement("div", { style: tableWrapStyle }, /* @__PURE__ */ React.createElement("table", { style: tableStyle }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", { style: thStyle }, "When"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "User"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Status"), /* @__PURE__ */ React.createElement("th", { style: { ...thStyle, width: "50%" } }, "Message"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Resolved By"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Resolved At"), /* @__PURE__ */ React.createElement("th", { style: thStyle }))), /* @__PURE__ */ React.createElement("tbody", null, filteredFeedback.length === 0 ? /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", { colSpan: 7, style: { ...tdStyle, ...emptyStateStyle } }, "No feedback yet. Users can submit with ", /* @__PURE__ */ React.createElement("code", null, "/feedback <message>"), " in the chat.")) : filteredFeedback.map((f, index) => {
      const open = f.status !== "resolved";
      return /* @__PURE__ */ React.createElement("tr", { key: rowKey("feedback", index, f.id, f.user_id, f.created_at), style: open ? { background: "#191c22" } : { opacity: 0.65 } }, /* @__PURE__ */ React.createElement("td", { style: tdStyle }, formatDate(f.created_at)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, f.username || f.user_id.slice(0, 8)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, /* @__PURE__ */ React.createElement("span", { style: {
        fontSize: 10,
        fontWeight: 600,
        textTransform: "uppercase",
        padding: "2px 6px",
        borderRadius: 3,
        background: open ? "#2a3a4a" : "#1c252f",
        color: open ? "#f0c674" : "#7d8590",
        border: "1px solid #2a3540"
      } }, f.status)), /* @__PURE__ */ React.createElement("td", { style: { ...tdStyle, whiteSpace: "pre-wrap", wordBreak: "break-word" } }, f.content), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, f.resolved_by || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, f.resolved_at ? formatDate(f.resolved_at) : "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, open && /* @__PURE__ */ React.createElement(
        "button",
        {
          onClick: () => handleResolveFeedback(f.id),
          disabled: resolving === f.id,
          style: {
            padding: "4px 10px",
            background: "#2a3540",
            color: "#e6edf3",
            border: "1px solid #3a4550",
            borderRadius: 3,
            cursor: resolving === f.id ? "wait" : "pointer",
            fontSize: 11
          }
        },
        resolving === f.id ? "\u2026" : "\u2713 Resolve"
      )));
    })))), activeTab === "admin-chat" && /* @__PURE__ */ React.createElement("div", { style: { ...tableWrapStyle, padding: 0, overflow: "hidden" } }, /* @__PURE__ */ React.createElement("div", { style: {
      padding: "12px 14px",
      borderBottom: "1px solid #2a3540",
      background: "#1c252f",
      color: "#f0c674",
      fontSize: 12,
      fontWeight: 700,
      textTransform: "uppercase",
      letterSpacing: "0.06em"
    } }, "Admin Chat \xB7 DB-backed activity Q&A"), /* @__PURE__ */ React.createElement("div", { style: {
      minHeight: 360,
      maxHeight: 560,
      overflowY: "auto",
      padding: 14,
      display: "flex",
      flexDirection: "column",
      gap: 10
    } }, adminChatMessages.map((msg, index) => /* @__PURE__ */ React.createElement(
      "div",
      {
        key: rowKey("admin-chat", index, msg.role, msg.content),
        style: {
          alignSelf: msg.role === "user" ? "flex-end" : "stretch",
          maxWidth: msg.role === "user" ? "74%" : "100%",
          background: msg.role === "user" ? "#22303d" : "#141a21",
          color: "#d6dde6",
          border: "1px solid #2a3540",
          borderRadius: 6,
          padding: "10px 12px",
          whiteSpace: "pre-wrap",
          wordBreak: "break-word"
        }
      },
      /* @__PURE__ */ React.createElement("div", { style: { fontSize: 10, textTransform: "uppercase", color: "#8893a3", marginBottom: 5 } }, msg.role === "user" ? "Admin" : "Atlas DB"),
      /* @__PURE__ */ React.createElement("div", null, msg.content),
      (msg.sections || []).length > 0 && /* @__PURE__ */ React.createElement("div", { style: { marginTop: 10, display: "grid", gap: 8 } }, msg.sections.map((section, sectionIndex) => /* @__PURE__ */ React.createElement("details", { key: rowKey("admin-chat-section", sectionIndex, section.title), style: { borderTop: "1px solid #2a3540", paddingTop: 8 } }, /* @__PURE__ */ React.createElement("summary", { style: { cursor: "pointer", color: "#f0c674", fontSize: 12 } }, section.title, " (", (section.rows || []).length, ")"), /* @__PURE__ */ React.createElement("pre", { style: {
        margin: "8px 0 0",
        padding: 10,
        background: "#0f141a",
        color: "#a3aebb",
        overflowX: "auto",
        fontSize: 11
      } }, JSON.stringify(section.rows || [], null, 2)))))
    )), adminChatLoading && /* @__PURE__ */ React.createElement("div", { style: { color: "#8893a3", fontSize: 12 } }, "Querying atlas.db\u2026")), /* @__PURE__ */ React.createElement("form", { onSubmit: handleAdminChatSubmit, style: {
      display: "flex",
      gap: 8,
      padding: 12,
      borderTop: "1px solid #2a3540",
      background: "#141a21"
    } }, /* @__PURE__ */ React.createElement(
      "input",
      {
        value: adminChatDraft,
        onChange: (e) => setAdminChatDraft(e.target.value),
        placeholder: "Ask: daily usage, model usage, workflow/IP usage, feedback, memory, input history\u2026",
        style: {
          flex: 1,
          minWidth: 0,
          background: "#0f141a",
          border: "1px solid #2a3540",
          color: "#d6dde6",
          borderRadius: 4,
          padding: "8px 10px",
          fontFamily: "inherit",
          fontSize: 13
        }
      }
    ), /* @__PURE__ */ React.createElement(
      "button",
      {
        type: "submit",
        disabled: adminChatLoading || !String(adminChatDraft || "").trim(),
        style: {
          ...headerButtonStyle,
          minWidth: 72,
          opacity: adminChatLoading || !String(adminChatDraft || "").trim() ? 0.55 : 1
        }
      },
      "Ask"
    ))), activeTab === "raw-db" && /* @__PURE__ */ React.createElement("div", { style: { display: "grid", gridTemplateColumns: "260px 1fr", gap: 16 } }, /* @__PURE__ */ React.createElement("div", { style: { ...tableWrapStyle, maxHeight: 600, overflowY: "auto" } }, /* @__PURE__ */ React.createElement("div", { style: {
      padding: "8px 12px",
      background: "#1c252f",
      borderBottom: "1px solid #2a3540",
      fontSize: 11,
      textTransform: "uppercase",
      letterSpacing: "0.06em",
      color: "#a3aebb",
      display: "flex",
      justifyContent: "space-between",
      alignItems: "center"
    } }, /* @__PURE__ */ React.createElement("span", null, "Tables (", dbTables.length, ")"), /* @__PURE__ */ React.createElement(
      "button",
      {
        onClick: loadDbTables,
        style: { ...headerButtonStyle, padding: "2px 6px", fontSize: 10 },
        title: "Refresh"
      },
      "\u21BB"
    )), dbTables.length === 0 ? /* @__PURE__ */ React.createElement("div", { style: { padding: 16, color: "#8893a3", fontSize: 12 } }, dbError ? `Error: ${dbError}` : "Loading\u2026") : dbTables.map((t, index) => {
      const active = dbSelectedTable === t.name;
      return /* @__PURE__ */ React.createElement(
        "button",
        {
          key: rowKey("db-table", index, t.name),
          onClick: () => setDbSelectedTable(t.name),
          style: {
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            width: "100%",
            padding: "8px 12px",
            background: active ? "#22303d" : "transparent",
            color: active ? "#f0c674" : "#d6dde6",
            border: "none",
            borderLeft: active ? "3px solid #f0c674" : "3px solid transparent",
            borderBottom: "1px solid #20272f",
            cursor: "pointer",
            fontFamily: "inherit",
            fontSize: 12,
            textAlign: "left"
          }
        },
        /* @__PURE__ */ React.createElement("span", { style: { fontWeight: active ? 600 : 400 } }, t.name),
        /* @__PURE__ */ React.createElement("span", { style: {
          fontSize: 10,
          color: active ? "#f0c674" : "#7d8590",
          background: "#11161c",
          padding: "2px 6px",
          borderRadius: 3
        } }, t.row_count)
      );
    })), /* @__PURE__ */ React.createElement("div", { style: { display: "flex", flexDirection: "column", gap: 12 } }, !dbSelectedTable ? /* @__PURE__ */ React.createElement(React.Fragment, null, /* @__PURE__ */ React.createElement("div", { style: {
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      gap: 12,
      flexWrap: "wrap"
    } }, /* @__PURE__ */ React.createElement("div", { style: { fontSize: 14, fontWeight: 600, color: "#f0c674" } }, "All tables overview", /* @__PURE__ */ React.createElement("span", { style: { color: "#7d8590", fontWeight: 400, marginLeft: 8, fontSize: 12 } }, "(3 most-recent rows per table \xB7 click a table name to drill in)")), /* @__PURE__ */ React.createElement("div", { style: { display: "flex", gap: 6, alignItems: "center" } }, /* @__PURE__ */ React.createElement("label", { style: { fontSize: 11, color: "#a3aebb", display: "flex", alignItems: "center", gap: 4 } }, /* @__PURE__ */ React.createElement(
      "input",
      {
        type: "checkbox",
        checked: dbHideEmpty,
        onChange: (e) => setDbHideEmpty(e.target.checked)
      }
    ), "Hide empty"), /* @__PURE__ */ React.createElement("button", { onClick: loadDbOverview, disabled: dbOverviewLoading, style: headerButtonStyle }, dbOverviewLoading ? "\u2026" : "\u21BB Refresh"))), dbError && /* @__PURE__ */ React.createElement("div", { style: { ...tableWrapStyle, padding: 16, color: "#e06c75" } }, dbError), /* @__PURE__ */ React.createElement("div", { style: { display: "flex", flexDirection: "column", gap: 12 } }, dbOverview.length === 0 ? /* @__PURE__ */ React.createElement("div", { style: { ...tableWrapStyle, padding: 24, textAlign: "center", color: "#8893a3" } }, dbOverviewLoading ? "Loading all tables\u2026" : "No data.") : dbOverview.filter((t) => !dbHideEmpty || t.total && t.total > 0).map((t, index) => /* @__PURE__ */ React.createElement("div", { key: rowKey("db-overview", index, t.name), style: tableWrapStyle }, /* @__PURE__ */ React.createElement("div", { style: {
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      padding: "8px 14px",
      background: "#1c252f",
      borderBottom: "1px solid #2a3540"
    } }, /* @__PURE__ */ React.createElement(
      "button",
      {
        onClick: () => setDbSelectedTable(t.name),
        style: {
          background: "transparent",
          border: "none",
          padding: 0,
          color: "#f0c674",
          fontWeight: 600,
          fontSize: 13,
          cursor: "pointer",
          fontFamily: "inherit"
        }
      },
      t.name
    ), /* @__PURE__ */ React.createElement("div", { style: { display: "flex", gap: 10, fontSize: 11, color: "#7d8590" } }, /* @__PURE__ */ React.createElement("span", null, /* @__PURE__ */ React.createElement("b", { style: { color: "#d6dde6" } }, t.total), " rows"), /* @__PURE__ */ React.createElement("span", null, t.columns.length, " cols"))), t.total === 0 ? /* @__PURE__ */ React.createElement("div", { style: { padding: "8px 14px", fontSize: 11, color: "#5a6470", fontStyle: "italic" } }, "empty") : t.rows.length === 0 ? /* @__PURE__ */ React.createElement("div", { style: { padding: "8px 14px", fontSize: 11, color: "#e06c75" } }, t.error || "no preview rows available") : /* @__PURE__ */ React.createElement("div", { style: { overflowX: "auto" } }, /* @__PURE__ */ React.createElement("table", { style: { ...tableStyle, fontSize: 11, fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace" } }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, t.columns.slice(0, 8).map((c) => /* @__PURE__ */ React.createElement("th", { key: c.name, style: { ...thStyle, padding: "6px 10px", fontSize: 10, whiteSpace: "nowrap" } }, c.name, c.pk ? /* @__PURE__ */ React.createElement("span", { style: { color: "#f0c674", marginLeft: 3 } }, "*") : null)), t.columns.length > 8 && /* @__PURE__ */ React.createElement("th", { style: { ...thStyle, padding: "6px 10px", fontSize: 10, color: "#7d8590" } }, "+", t.columns.length - 8, " more"))), /* @__PURE__ */ React.createElement("tbody", null, t.rows.map((row, i) => /* @__PURE__ */ React.createElement("tr", { key: i }, t.columns.slice(0, 8).map((c) => {
      const v = row[c.name];
      let text;
      if (v === null || v === void 0) text = "\u2205";
      else if (typeof v === "object") text = JSON.stringify(v);
      else if (typeof v === "number" && c.name.endsWith("_at") && v > 1e9) {
        try {
          text = new Date(v * 1e3).toISOString().replace("T", " ").slice(0, 19);
        } catch (_) {
          text = String(v);
        }
      } else text = String(v);
      const truncated = text.length > 40 ? text.slice(0, 40) + "\u2026" : text;
      return /* @__PURE__ */ React.createElement(
        "td",
        {
          key: c.name,
          style: {
            ...tdStyle,
            padding: "5px 10px",
            maxWidth: 180,
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
            color: v === null ? "#5a6470" : tdStyle.color
          },
          title: text
        },
        truncated
      );
    }), t.columns.length > 8 && /* @__PURE__ */ React.createElement("td", { style: { ...tdStyle, padding: "5px 10px", color: "#5a6470", fontStyle: "italic" } }, "\u2026")))))))))) : /* @__PURE__ */ React.createElement(React.Fragment, null, /* @__PURE__ */ React.createElement("div", { style: {
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      gap: 12,
      flexWrap: "wrap"
    } }, /* @__PURE__ */ React.createElement("div", { style: { fontSize: 14, fontWeight: 600, color: "#f0c674", display: "flex", alignItems: "center", gap: 8 } }, /* @__PURE__ */ React.createElement(
      "button",
      {
        onClick: () => setDbSelectedTable(null),
        style: { ...headerButtonStyle, fontSize: 11, padding: "3px 8px" },
        title: "Back to all-tables overview"
      },
      "\u2190 Overview"
    ), dbSelectedTable, /* @__PURE__ */ React.createElement("span", { style: { color: "#7d8590", fontWeight: 400, fontSize: 12 } }, "(", dbPage.total, " rows \xB7 showing ", dbPage.offset + 1, "-", Math.min(dbPage.offset + dbPage.rows.length, dbPage.total), ")")), /* @__PURE__ */ React.createElement("div", { style: { display: "flex", gap: 6 } }, /* @__PURE__ */ React.createElement(
      "button",
      {
        onClick: () => loadDbTable(dbSelectedTable, Math.max(0, dbPage.offset - dbPage.limit), dbPage.limit),
        disabled: dbPage.offset === 0 || dbLoading,
        style: headerButtonStyle
      },
      "\u2039 Prev"
    ), /* @__PURE__ */ React.createElement(
      "button",
      {
        onClick: () => loadDbTable(dbSelectedTable, dbPage.offset + dbPage.limit, dbPage.limit),
        disabled: dbPage.offset + dbPage.rows.length >= dbPage.total || dbLoading,
        style: headerButtonStyle
      },
      "Next \u203A"
    ), /* @__PURE__ */ React.createElement(
      "select",
      {
        value: dbPage.limit,
        onChange: (e) => loadDbTable(dbSelectedTable, 0, Number(e.target.value)),
        style: { ...headerButtonStyle, padding: "4px 6px" }
      },
      /* @__PURE__ */ React.createElement("option", { value: 25 }, "25"),
      /* @__PURE__ */ React.createElement("option", { value: 50 }, "50"),
      /* @__PURE__ */ React.createElement("option", { value: 100 }, "100"),
      /* @__PURE__ */ React.createElement("option", { value: 200 }, "200")
    ), /* @__PURE__ */ React.createElement(
      "button",
      {
        onClick: () => loadDbTable(dbSelectedTable, dbPage.offset, dbPage.limit),
        disabled: dbLoading,
        style: headerButtonStyle
      },
      "\u21BB"
    ))), dbError ? /* @__PURE__ */ React.createElement("div", { style: { ...tableWrapStyle, padding: 16, color: "#e06c75" } }, dbError) : /* @__PURE__ */ React.createElement("div", { style: { ...tableWrapStyle, maxHeight: 600, overflowY: "auto" } }, /* @__PURE__ */ React.createElement("table", { style: { ...tableStyle, fontSize: 11.5, fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace" } }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, dbPage.columns.map((c) => /* @__PURE__ */ React.createElement("th", { key: c.name, style: { ...thStyle, fontSize: 10, whiteSpace: "nowrap" } }, c.name, c.pk ? /* @__PURE__ */ React.createElement("span", { style: { color: "#f0c674", marginLeft: 4 } }, "PK") : null, /* @__PURE__ */ React.createElement("div", { style: { fontSize: 9, color: "#7d8590", fontWeight: 400, textTransform: "none", letterSpacing: 0 } }, c.type || "ANY", c.notnull ? " \xB7 NN" : ""))))), /* @__PURE__ */ React.createElement("tbody", null, dbPage.rows.length === 0 ? /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", { colSpan: dbPage.columns.length, style: { ...tdStyle, ...emptyStateStyle } }, dbLoading ? "Loading\u2026" : "Table is empty.")) : dbPage.rows.map((row, i) => {
      const rowKey2 = `${dbPage.offset}-${i}`;
      const expanded = dbExpandedRow === rowKey2;
      return /* @__PURE__ */ React.createElement(React.Fragment, { key: rowKey2 }, /* @__PURE__ */ React.createElement(
        "tr",
        {
          onClick: () => setDbExpandedRow(expanded ? null : rowKey2),
          style: { cursor: "pointer", background: expanded ? "#191c22" : "transparent" }
        },
        dbPage.columns.map((c) => {
          const v = row[c.name];
          let text;
          if (v === null || v === void 0) text = "\u2205";
          else if (typeof v === "object") text = JSON.stringify(v);
          else if (typeof v === "number" && c.name.endsWith("_at") && v > 1e9) {
            try {
              text = new Date(v * 1e3).toISOString().replace("T", " ").slice(0, 19);
            } catch (_) {
              text = String(v);
            }
          } else text = String(v);
          const truncated = text.length > 60 ? text.slice(0, 60) + "\u2026" : text;
          return /* @__PURE__ */ React.createElement(
            "td",
            {
              key: c.name,
              style: {
                ...tdStyle,
                padding: "6px 10px",
                maxWidth: 240,
                whiteSpace: "nowrap",
                overflow: "hidden",
                textOverflow: "ellipsis",
                color: v === null ? "#5a6470" : tdStyle.color
              },
              title: text
            },
            truncated
          );
        })
      ), expanded && /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", { colSpan: dbPage.columns.length, style: { ...tdStyle, background: "#0f1419", padding: 12 } }, /* @__PURE__ */ React.createElement("pre", { style: {
        margin: 0,
        fontSize: 11,
        color: "#a3aebb",
        whiteSpace: "pre-wrap",
        wordBreak: "break-word"
      } }, JSON.stringify(row, null, 2)))));
    }))))))))));
  }
  window.AdminPage = AdminPage;
  if (typeof document !== "undefined" && document.getElementById("root")) {
    ReactDOM.createRoot(document.getElementById("root")).render(/* @__PURE__ */ React.createElement(AdminPage, null));
  }
})();
