var AtlasAdminDashboard = (() => {
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
    const [feedback, setFeedback] = React.useState([]);
    const [loading, setLoading] = React.useState(true);
    const [error, setError] = React.useState(null);
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
    async function reloadFeedback() {
      try {
        const r = await fetch("/api/admin/feedback");
        if (!r.ok) return;
        const d = await r.json();
        setFeedback(d.feedback || []);
      } catch (_) {
      }
    }
    const loadAdminData = React.useCallback(async () => {
      try {
        setLoading(true);
        setError(null);
        const [usersResp, sessionsResp, usageResp, fbResp] = await Promise.all([
          fetch("/api/admin/users"),
          fetch("/api/admin/sessions"),
          fetch("/api/admin/usage"),
          fetch("/api/admin/feedback")
        ]);
        if ([usersResp, sessionsResp, usageResp, fbResp].some((r) => r.status === 401)) {
          setError("Admin API returned 401; local admin bypass is not active.");
          return;
        }
        if ([usersResp, sessionsResp, usageResp, fbResp].some((r) => r.status === 403)) {
          setError("Admin API returned 403; local admin bypass is not active.");
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
        setFeedback(fbData.feedback || []);
      } catch (e) {
        setError(String(e));
      } finally {
        setLoading(false);
      }
    }, []);
    React.useEffect(() => {
      loadAdminData();
    }, [loadAdminData]);
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
    const shortId = (value) => String(value || "").slice(0, 8) || "\u2014";
    const payloadText = (value) => {
      if (value == null || value === "") return "\u2014";
      try {
        const text = typeof value === "string" ? value : JSON.stringify(value);
        return text.length > 180 ? text.slice(0, 177) + "\u2026" : text;
      } catch (_) {
        return String(value);
      }
    };
    const sum = (rows, key) => rows.reduce((acc, row) => acc + Number(row[key] || 0), 0);
    const rowTimestamp = (row) => {
      const direct = row.last_message_at || row.last_event_at || row.last_tool_at || row.last_intervention_at || row.created_at || row.updated_at || row.first_intervention_at;
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
    const allContextRows = [
      ...costContexts,
      ...dateCosts,
      ...todoUsage,
      ...todoFlow,
      ...traceEvents,
      ...toolUsage,
      ...interventions
    ];
    const filterOptions = {
      ips: uniqueOptions(allContextRows, "ip"),
      workspaces: uniqueOptions(allContextRows, "workspace"),
      workflows: uniqueOptions(allContextRows, "workflow"),
      users: uniqueOptions([
        ...allContextRows,
        ...usage,
        ...sessions.map((s) => ({ username: s.owner_username || s.user_id })),
        ...feedback
      ], "username")
    };
    const filteredUsers = users.filter((row) => valueMatches(filters.user, row.username) && !filters.ip && !filters.workspace && !filters.workflow);
    const filteredUsage = usage.filter((row) => inRange(row) && valueMatches(filters.user, row.username) && !filters.ip && !filters.workspace && !filters.workflow);
    const filteredSessions = sessions.filter((row) => inRange(row) && valueMatches(filters.user, row.owner_username || row.user_id) && (!filters.ip || String(row.project_id || row.title || "") === filters.ip) && !filters.workspace && !filters.workflow);
    const filteredCostContexts = costContexts.filter(rowMatches);
    const filteredDateCosts = dateCosts.filter(rowMatches);
    const filteredTodoUsage = todoUsage.filter(rowMatches);
    const filteredTodoFlow = todoFlow.filter(rowMatches);
    const filteredTraceEvents = traceEvents.filter(rowMatches);
    const filteredToolUsage = toolUsage.filter(rowMatches);
    const filteredInterventions = interventions.filter(rowMatches);
    const filteredFeedback = feedback.filter((row) => inRange(row) && valueMatches(filters.user, row.username) && !filters.ip && !filters.workspace && !filters.workflow);
    const topCostRows = [...filteredCostContexts].sort((a, b) => Number(b.cost || 0) - Number(a.cost || 0)).slice(0, 5);
    const topRejectedTodos = [...filteredTodoUsage].filter((row) => Number(row.rejected_count || 0) > 0).sort((a, b) => Number(b.rejected_count || 0) - Number(a.rejected_count || 0)).slice(0, 5);
    const topToolRows = [...filteredToolUsage].sort((a, b) => Number(b.failed_calls || 0) - Number(a.failed_calls || 0) || Number(b.observation_tokens_est || 0) - Number(a.observation_tokens_est || 0)).slice(0, 5);
    const topHumanRows = [...filteredInterventions].sort((a, b) => Number(b.intervention_count || 0) - Number(a.intervention_count || 0)).slice(0, 5);
    const askUserOpened = new Set(filteredTraceEvents.filter((row) => row.event_type === "ask_user.opened").map((row) => row.payload && row.payload.flow_id || row.event_id).filter(Boolean));
    const askUserAnswered = new Set(filteredTraceEvents.filter((row) => row.event_type === "ask_user.answered").map((row) => row.payload && row.payload.flow_id || row.event_id).filter(Boolean));
    const overview = {
      cost: sum(filteredCostContexts, "cost"),
      llmCalls: sum(filteredCostContexts, "calls"),
      toolCalls: sum(filteredToolUsage, "calls"),
      toolFailures: sum(filteredToolUsage, "failed_calls"),
      obsTokens: sum(filteredToolUsage, "observation_tokens_est"),
      rejectedTodos: sum(filteredTodoUsage, "rejected_count"),
      openTodos: filteredTodoUsage.filter((row) => !["approved", "completed"].includes(String(row.status || "").toLowerCase())).length,
      humanInputs: sum(filteredInterventions, "intervention_count"),
      pendingHuman: Array.from(askUserOpened).filter((flow) => !askUserAnswered.has(flow)).length,
      pendingFeedback: filteredFeedback.filter((row) => row.status !== "resolved").length
    };
    const setFilter = (key, value) => setFilters((prev) => ({ ...prev, [key]: value }));
    const clearFilters = () => setFilters({ range: "all", ip: "", workspace: "", workflow: "", user: "" });
    return /* @__PURE__ */ React.createElement("div", { style: pageStyle }, /* @__PURE__ */ React.createElement("header", { style: headerStyle }, /* @__PURE__ */ React.createElement("div", { style: logoStyle }, /* @__PURE__ */ React.createElement("span", { style: { fontSize: 26 } }, "\u25C8"), /* @__PURE__ */ React.createElement("span", null, "ATLAS Admin")), /* @__PURE__ */ React.createElement("span", { style: badgeStyle }, "Admin")), /* @__PURE__ */ React.createElement("main", { style: mainStyle }, loading && /* @__PURE__ */ React.createElement("div", { style: { textAlign: "center", padding: "40px 0", color: "#8893a3" } }, "Loading\u2026"), !loading && error && /* @__PURE__ */ React.createElement("div", { style: errorStateStyle }, error), !loading && !error && /* @__PURE__ */ React.createElement(React.Fragment, null, /* @__PURE__ */ React.createElement("div", { style: tabRowStyle }, /* @__PURE__ */ React.createElement("button", { style: tabStyle(activeTab === "overview"), onClick: () => setActiveTab("overview") }, "Overview"), /* @__PURE__ */ React.createElement("button", { style: tabStyle(activeTab === "users"), onClick: () => setActiveTab("users") }, "Users (", filteredUsers.length, ")"), /* @__PURE__ */ React.createElement("button", { style: tabStyle(activeTab === "sessions"), onClick: () => setActiveTab("sessions") }, "Sessions (", filteredSessions.length, ")"), /* @__PURE__ */ React.createElement("button", { style: tabStyle(activeTab === "usage"), onClick: () => setActiveTab("usage") }, "Usage (", filteredUsage.length, ")"), /* @__PURE__ */ React.createElement("button", { style: tabStyle(activeTab === "costs"), onClick: () => setActiveTab("costs") }, "Costs (", filteredCostContexts.length, ")"), /* @__PURE__ */ React.createElement("button", { style: tabStyle(activeTab === "todos"), onClick: () => setActiveTab("todos") }, "Todos (", filteredTodoUsage.length, ")"), /* @__PURE__ */ React.createElement("button", { style: tabStyle(activeTab === "flow"), onClick: () => setActiveTab("flow") }, "Flow (", filteredTodoFlow.length, ")"), /* @__PURE__ */ React.createElement("button", { style: tabStyle(activeTab === "trace"), onClick: () => setActiveTab("trace") }, "Trace (", filteredTraceEvents.length, ")"), /* @__PURE__ */ React.createElement("button", { style: tabStyle(activeTab === "tools"), onClick: () => setActiveTab("tools") }, "Tools (", filteredToolUsage.length, ")"), /* @__PURE__ */ React.createElement("button", { style: tabStyle(activeTab === "human"), onClick: () => setActiveTab("human") }, "Human (", filteredInterventions.length, ")"), /* @__PURE__ */ React.createElement("button", { style: tabStyle(activeTab === "feedback"), onClick: () => setActiveTab("feedback") }, "Feedback (", filteredFeedback.filter((f) => f.status !== "resolved").length, "/", filteredFeedback.length, ")")), /* @__PURE__ */ React.createElement("div", { style: filterBarStyle }, /* @__PURE__ */ React.createElement("label", { style: filterLabelStyle, htmlFor: "admin-filter-range" }, "Range", /* @__PURE__ */ React.createElement(
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
    )), /* @__PURE__ */ React.createElement("label", { style: filterLabelStyle }, "Reset", /* @__PURE__ */ React.createElement("button", { type: "button", style: { ...selectStyle, cursor: "pointer", color: "#f0c674" }, onClick: clearFilters }, "Clear filters"))), activeTab === "overview" && /* @__PURE__ */ React.createElement(React.Fragment, null, /* @__PURE__ */ React.createElement("div", { style: overviewGridStyle }, /* @__PURE__ */ React.createElement("div", { style: metricCardStyle() }, /* @__PURE__ */ React.createElement("div", { style: metricLabelStyle }, "Cost"), /* @__PURE__ */ React.createElement("div", { style: metricValueStyle }, usd(overview.cost))), /* @__PURE__ */ React.createElement("div", { style: metricCardStyle() }, /* @__PURE__ */ React.createElement("div", { style: metricLabelStyle }, "LLM Calls"), /* @__PURE__ */ React.createElement("div", { style: metricValueStyle }, fmt(overview.llmCalls))), /* @__PURE__ */ React.createElement("div", { style: metricCardStyle() }, /* @__PURE__ */ React.createElement("div", { style: metricLabelStyle }, "Tool Calls"), /* @__PURE__ */ React.createElement("div", { style: metricValueStyle }, fmt(overview.toolCalls))), /* @__PURE__ */ React.createElement("div", { style: metricCardStyle(overview.toolFailures ? "danger" : "default") }, /* @__PURE__ */ React.createElement("div", { style: metricLabelStyle }, "Tool Failures"), /* @__PURE__ */ React.createElement("div", { style: metricValueStyle }, fmt(overview.toolFailures))), /* @__PURE__ */ React.createElement("div", { style: metricCardStyle() }, /* @__PURE__ */ React.createElement("div", { style: metricLabelStyle }, "Obs Tokens Est"), /* @__PURE__ */ React.createElement("div", { style: metricValueStyle }, fmt(overview.obsTokens))), /* @__PURE__ */ React.createElement("div", { style: metricCardStyle(overview.rejectedTodos ? "danger" : "default") }, /* @__PURE__ */ React.createElement("div", { style: metricLabelStyle }, "Rejected Todos"), /* @__PURE__ */ React.createElement("div", { style: metricValueStyle }, fmt(overview.rejectedTodos))), /* @__PURE__ */ React.createElement("div", { style: metricCardStyle(overview.openTodos ? "danger" : "default") }, /* @__PURE__ */ React.createElement("div", { style: metricLabelStyle }, "Open Todos"), /* @__PURE__ */ React.createElement("div", { style: metricValueStyle }, fmt(overview.openTodos))), /* @__PURE__ */ React.createElement("div", { style: metricCardStyle() }, /* @__PURE__ */ React.createElement("div", { style: metricLabelStyle }, "Human Inputs"), /* @__PURE__ */ React.createElement("div", { style: metricValueStyle }, fmt(overview.humanInputs))), /* @__PURE__ */ React.createElement("div", { style: metricCardStyle(overview.pendingHuman ? "danger" : "default") }, /* @__PURE__ */ React.createElement("div", { style: metricLabelStyle }, "Ask User Pending"), /* @__PURE__ */ React.createElement("div", { style: metricValueStyle }, fmt(overview.pendingHuman))), /* @__PURE__ */ React.createElement("div", { style: metricCardStyle(overview.pendingFeedback ? "danger" : "default") }, /* @__PURE__ */ React.createElement("div", { style: metricLabelStyle }, "Open Feedback"), /* @__PURE__ */ React.createElement("div", { style: metricValueStyle }, fmt(overview.pendingFeedback)))), /* @__PURE__ */ React.createElement("div", { style: { display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(min(100%, 430px), 1fr))", gap: 18 } }, /* @__PURE__ */ React.createElement("div", { style: tableWrapStyle }, /* @__PURE__ */ React.createElement("div", { style: panelTitleStyle }, "Top Cost Contexts"), /* @__PURE__ */ React.createElement("table", { style: tableStyle }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", { style: thStyle }, "IP"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Workspace"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Workflow"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Calls"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Cost"))), /* @__PURE__ */ React.createElement("tbody", null, topCostRows.length === 0 ? /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", { colSpan: 5, style: { ...tdStyle, ...emptyStateStyle } }, "No cost data in filter.")) : topCostRows.map((row) => /* @__PURE__ */ React.createElement("tr", { key: `${row.session_id}-${row.ip}-${row.workflow}-${row.workspace}` }, /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.ip || "unknown"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.workspace || "default"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.workflow || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.calls)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, usd(row.cost))))))), /* @__PURE__ */ React.createElement("div", { style: tableWrapStyle }, /* @__PURE__ */ React.createElement("div", { style: panelTitleStyle }, "Tool Pressure"), /* @__PURE__ */ React.createElement("table", { style: tableStyle }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Tool"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "IP"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Failures"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Obs Tokens"))), /* @__PURE__ */ React.createElement("tbody", null, topToolRows.length === 0 ? /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", { colSpan: 4, style: { ...tdStyle, ...emptyStateStyle } }, "No tool data in filter.")) : topToolRows.map((row) => /* @__PURE__ */ React.createElement("tr", { key: `${row.session_id}-${row.ip}-${row.workflow}-${row.tool_name}` }, /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.tool_name || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.ip || "unknown"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.failed_calls)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.observation_tokens_est))))))), /* @__PURE__ */ React.createElement("div", { style: tableWrapStyle }, /* @__PURE__ */ React.createElement("div", { style: panelTitleStyle }, "Rejected Todo Hotspots"), /* @__PURE__ */ React.createElement("table", { style: tableStyle }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Todo"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "IP"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Rejects"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Last Reason"))), /* @__PURE__ */ React.createElement("tbody", null, topRejectedTodos.length === 0 ? /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", { colSpan: 4, style: { ...tdStyle, ...emptyStateStyle } }, "No rejected todos in filter.")) : topRejectedTodos.map((row) => /* @__PURE__ */ React.createElement("tr", { key: row.todo_id }, /* @__PURE__ */ React.createElement("td", { style: { ...tdStyle, maxWidth: 260, whiteSpace: "normal" } }, row.content || shortId(row.todo_id)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.ip || "unknown"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.rejected_count)), /* @__PURE__ */ React.createElement("td", { style: { ...tdStyle, maxWidth: 320, whiteSpace: "normal" } }, row.last_rejected_reason || row.last_event_reason || "\u2014")))))), /* @__PURE__ */ React.createElement("div", { style: tableWrapStyle }, /* @__PURE__ */ React.createElement("div", { style: panelTitleStyle }, "Human Intervention Hotspots"), /* @__PURE__ */ React.createElement("table", { style: tableStyle }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", { style: thStyle }, "User"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "IP"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Workflow"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Inputs"))), /* @__PURE__ */ React.createElement("tbody", null, topHumanRows.length === 0 ? /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", { colSpan: 4, style: { ...tdStyle, ...emptyStateStyle } }, "No human input in filter.")) : topHumanRows.map((row) => /* @__PURE__ */ React.createElement("tr", { key: `${row.session_id}-${row.ip}-${row.workflow}-${row.username}` }, /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.username || "unknown"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.ip || "unknown"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.workflow || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.intervention_count))))))))), activeTab === "users" && /* @__PURE__ */ React.createElement("div", { style: tableWrapStyle }, /* @__PURE__ */ React.createElement("table", { style: tableStyle }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Username"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Display Name"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Role"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Sessions"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Created"))), /* @__PURE__ */ React.createElement("tbody", null, filteredUsers.length === 0 ? /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", { colSpan: 5, style: { ...tdStyle, ...emptyStateStyle } }, "No users found.")) : filteredUsers.map((u) => {
      var _a;
      return /* @__PURE__ */ React.createElement("tr", { key: u.id }, /* @__PURE__ */ React.createElement("td", { style: tdStyle }, u.username), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, u.display_name || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, /* @__PURE__ */ React.createElement("span", { style: {
        fontSize: 10,
        fontWeight: 600,
        textTransform: "uppercase",
        padding: "2px 6px",
        borderRadius: 3,
        background: u.role === "admin" ? "#2a3a4a" : "#1c252f",
        color: u.role === "admin" ? "#f0c674" : "#a3aebb",
        border: "1px solid #2a3540"
      } }, u.role)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, (_a = u.session_count) != null ? _a : 0), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, formatDate(u.created_at)));
    })))), activeTab === "sessions" && /* @__PURE__ */ React.createElement("div", { style: tableWrapStyle }, /* @__PURE__ */ React.createElement("table", { style: tableStyle }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Title"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Project"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Status"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Owner"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Created"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Updated"), /* @__PURE__ */ React.createElement("th", { style: thStyle }))), /* @__PURE__ */ React.createElement("tbody", null, filteredSessions.length === 0 ? /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", { colSpan: 7, style: { ...tdStyle, ...emptyStateStyle } }, "No sessions found.")) : filteredSessions.map((s) => /* @__PURE__ */ React.createElement("tr", { key: s.id }, /* @__PURE__ */ React.createElement("td", { style: tdStyle }, s.title || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, s.project_id || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, /* @__PURE__ */ React.createElement("span", { style: {
      fontSize: 10,
      fontWeight: 600,
      textTransform: "uppercase",
      padding: "2px 6px",
      borderRadius: 3,
      background: s.status === "active" ? "#1c2f25" : "#1c252f",
      color: s.status === "active" ? "#7dc9a0" : "#a3aebb",
      border: "1px solid #2a3540"
    } }, s.status)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, s.owner_username || s.user_id || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, formatDate(s.created_at)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, formatDate(s.updated_at)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, /* @__PURE__ */ React.createElement(
      "button",
      {
        style: btnDangerStyle,
        onClick: () => handleDeleteSession(s.id),
        disabled: deleting === s.id
      },
      deleting === s.id ? "Deleting\u2026" : "Delete"
    ))))))), activeTab === "usage" && /* @__PURE__ */ React.createElement("div", { style: tableWrapStyle }, /* @__PURE__ */ React.createElement("table", { style: tableStyle }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Username"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Role"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Sessions"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Messages"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Tokens In"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Tokens Out"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Reasoning"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Cost (USD)"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Last Activity"))), /* @__PURE__ */ React.createElement("tbody", null, filteredUsage.length === 0 ? /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", { colSpan: 9, style: { ...tdStyle, ...emptyStateStyle } }, "No usage data yet.")) : filteredUsage.flatMap((u) => {
      const expanded = expandedUsage === u.user_id;
      const rows = [
        /* @__PURE__ */ React.createElement(
          "tr",
          {
            key: u.user_id,
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
          /* @__PURE__ */ React.createElement("tr", { key: u.user_id + "-detail" }, /* @__PURE__ */ React.createElement("td", { colSpan: 9, style: { ...tdStyle, background: "#10141a", padding: "12px 16px" } }, /* @__PURE__ */ React.createElement("div", { style: { display: "flex", gap: 28, flexWrap: "wrap" } }, /* @__PURE__ */ React.createElement("div", { style: { minWidth: 260 } }, /* @__PURE__ */ React.createElement("div", { style: {
            fontSize: 11,
            opacity: 0.7,
            marginBottom: 6,
            textTransform: "uppercase",
            letterSpacing: "0.06em"
          } }, "Models"), (u.models || []).length === 0 ? /* @__PURE__ */ React.createElement("div", { style: { opacity: 0.5, fontSize: 12 } }, "no model usage") : /* @__PURE__ */ React.createElement("table", { style: { fontSize: 12, borderCollapse: "collapse" } }, /* @__PURE__ */ React.createElement("tbody", null, u.models.slice(0, 8).map((m) => /* @__PURE__ */ React.createElement("tr", { key: m.model_id }, /* @__PURE__ */ React.createElement("td", { style: { padding: "2px 10px 2px 0" } }, m.model_id), /* @__PURE__ */ React.createElement("td", { style: { padding: "2px 10px", textAlign: "right", opacity: 0.7 } }, fmt(m.calls), " calls"), /* @__PURE__ */ React.createElement("td", { style: { padding: "2px 10px", textAlign: "right", opacity: 0.7 } }, fmt(m.tokens), " tok"), /* @__PURE__ */ React.createElement("td", { style: { padding: "2px 0", textAlign: "right", opacity: 0.7 } }, usd(m.cost))))))), /* @__PURE__ */ React.createElement("div", { style: { minWidth: 220 } }, /* @__PURE__ */ React.createElement("div", { style: {
            fontSize: 11,
            opacity: 0.7,
            marginBottom: 6,
            textTransform: "uppercase",
            letterSpacing: "0.06em"
          } }, "Top Tools"), (u.tools || []).length === 0 ? /* @__PURE__ */ React.createElement("div", { style: { opacity: 0.5, fontSize: 12 } }, "no tool calls") : /* @__PURE__ */ React.createElement("table", { style: { fontSize: 12, borderCollapse: "collapse" } }, /* @__PURE__ */ React.createElement("tbody", null, u.tools.slice(0, 10).map((t) => /* @__PURE__ */ React.createElement("tr", { key: t.tool_name }, /* @__PURE__ */ React.createElement("td", { style: { padding: "2px 12px 2px 0" } }, t.tool_name), /* @__PURE__ */ React.createElement("td", { style: { padding: "2px 0", textAlign: "right", opacity: 0.7 } }, fmt(t.calls))))))))))
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
    } }, "Cost by IP / Workspace"), /* @__PURE__ */ React.createElement("table", { style: tableStyle }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", { style: thStyle }, "IP / Project"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Workspace"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Session"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "User"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Calls"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Tokens"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Cost"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Last"))), /* @__PURE__ */ React.createElement("tbody", null, filteredCostContexts.length === 0 ? /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", { colSpan: 8, style: { ...tdStyle, ...emptyStateStyle } }, "No cost data yet.")) : filteredCostContexts.map((row) => /* @__PURE__ */ React.createElement("tr", { key: `${row.session_id || ""}-${row.ip}-${row.workspace}` }, /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.ip || "unknown"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.workspace || "default"), /* @__PURE__ */ React.createElement("td", { style: tdStyle, title: row.session_id || "" }, row.session || shortId(row.session_id)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.username || "unknown"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.calls)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.tokens)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, usd(row.cost)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, formatDate(row.last_message_at))))))), /* @__PURE__ */ React.createElement("div", { style: tableWrapStyle }, /* @__PURE__ */ React.createElement("div", { style: {
      padding: "12px 14px",
      borderBottom: "1px solid #2a3540",
      background: "#1c252f",
      color: "#f0c674",
      fontSize: 12,
      fontWeight: 700,
      textTransform: "uppercase",
      letterSpacing: "0.06em"
    } }, "Cost by Date"), /* @__PURE__ */ React.createElement("table", { style: tableStyle }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Date"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "IP / Project"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Workspace"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Calls"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Tokens"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Cost"))), /* @__PURE__ */ React.createElement("tbody", null, filteredDateCosts.length === 0 ? /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", { colSpan: 6, style: { ...tdStyle, ...emptyStateStyle } }, "No daily cost data yet.")) : filteredDateCosts.map((row) => /* @__PURE__ */ React.createElement("tr", { key: `${row.day}-${row.session_id || ""}-${row.ip}-${row.workspace}` }, /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.day || "unknown"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.ip || "unknown"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.workspace || "default"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.calls)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.tokens)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, usd(row.cost)))))))), activeTab === "todos" && /* @__PURE__ */ React.createElement("div", { style: tableWrapStyle }, /* @__PURE__ */ React.createElement("table", { style: tableStyle }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", { style: thStyle }, "IP"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Workspace"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Workflow"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Todo"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Status"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Rejects"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "LLM Calls"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Tokens"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Cost"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Last Reason"))), /* @__PURE__ */ React.createElement("tbody", null, filteredTodoUsage.length === 0 ? /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", { colSpan: 10, style: { ...tdStyle, ...emptyStateStyle } }, "No todo usage data yet.")) : filteredTodoUsage.map((row) => /* @__PURE__ */ React.createElement("tr", { key: row.todo_id }, /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.ip || "unknown"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.workspace || "default"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.workflow || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: { ...tdStyle, minWidth: 240 } }, /* @__PURE__ */ React.createElement("div", null, row.content || "\u2014"), /* @__PURE__ */ React.createElement("div", { style: { color: "#8893a3", fontSize: 11, marginTop: 4 } }, row.detail || row.criteria || "\u2014")), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.status || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.rejected_count)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.llm_calls)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.tokens)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, usd(row.cost)), /* @__PURE__ */ React.createElement("td", { style: { ...tdStyle, maxWidth: 260, whiteSpace: "normal" } }, row.last_event_reason || row.last_rejected_reason || "\u2014")))))), activeTab === "flow" && /* @__PURE__ */ React.createElement("div", { style: tableWrapStyle }, /* @__PURE__ */ React.createElement("table", { style: tableStyle }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", { style: thStyle }, "When"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "IP"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Workflow"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Todo"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Event"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Reason"))), /* @__PURE__ */ React.createElement("tbody", null, filteredTodoFlow.length === 0 ? /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", { colSpan: 6, style: { ...tdStyle, ...emptyStateStyle } }, "No todo flow events yet.")) : filteredTodoFlow.map((row) => /* @__PURE__ */ React.createElement("tr", { key: row.event_id }, /* @__PURE__ */ React.createElement("td", { style: tdStyle }, formatDate(row.created_at)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.ip || "unknown"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.workflow || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: { ...tdStyle, maxWidth: 300, whiteSpace: "normal" } }, row.content || shortId(row.todo_id)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.event_type || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: { ...tdStyle, maxWidth: 360, whiteSpace: "normal" } }, row.reason || "\u2014")))))), activeTab === "trace" && /* @__PURE__ */ React.createElement("div", { style: tableWrapStyle }, /* @__PURE__ */ React.createElement("table", { style: tableStyle }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", { style: thStyle }, "When"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Event"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "IP"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Workspace"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Workflow"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "User"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Run"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Todo"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Correlation"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Payload"))), /* @__PURE__ */ React.createElement("tbody", null, filteredTraceEvents.length === 0 ? /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", { colSpan: 10, style: { ...tdStyle, ...emptyStateStyle } }, "No trace events yet.")) : filteredTraceEvents.map((row) => /* @__PURE__ */ React.createElement("tr", { key: row.event_id }, /* @__PURE__ */ React.createElement("td", { style: tdStyle }, formatDate(row.created_at)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.event_type || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.ip || "unknown"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.workspace || "default"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.workflow || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.username || shortId(row.actor_user_id)), /* @__PURE__ */ React.createElement("td", { style: tdStyle, title: row.run_id || "" }, shortId(row.run_id)), /* @__PURE__ */ React.createElement("td", { style: tdStyle, title: row.todo_id || "" }, shortId(row.todo_id)), /* @__PURE__ */ React.createElement("td", { style: tdStyle, title: row.correlation_id || "" }, shortId(row.correlation_id)), /* @__PURE__ */ React.createElement("td", { style: { ...tdStyle, maxWidth: 360, whiteSpace: "normal", wordBreak: "break-word" } }, payloadText(row.payload))))))), activeTab === "tools" && /* @__PURE__ */ React.createElement("div", { style: tableWrapStyle }, /* @__PURE__ */ React.createElement("table", { style: tableStyle }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Tool"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Calls"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Failures"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Obs Tokens (est)"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Obs Chars"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Avg Latency"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "IP"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Workspace"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Workflow"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Session"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "User"))), /* @__PURE__ */ React.createElement("tbody", null, filteredToolUsage.length === 0 ? /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", { colSpan: 11, style: { ...tdStyle, ...emptyStateStyle } }, "No tool usage data yet.")) : filteredToolUsage.map((row) => /* @__PURE__ */ React.createElement("tr", { key: `${row.session_id}-${row.ip}-${row.workflow}-${row.tool_name}` }, /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.tool_name || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.calls)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.failed_calls)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.observation_tokens_est)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.observation_chars)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.avg_latency_ms == null ? "\u2014" : `${Number(row.avg_latency_ms).toFixed(0)} ms`), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.ip || "unknown"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.workspace || "default"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.workflow || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle, title: row.session_id || "" }, row.session || shortId(row.session_id)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.username || "unknown")))))), activeTab === "human" && /* @__PURE__ */ React.createElement("div", { style: tableWrapStyle }, /* @__PURE__ */ React.createElement("table", { style: tableStyle }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", { style: thStyle }, "User"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Session"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "IP"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Workspace"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Workflow"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Total"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Prompts"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Chat"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Ask User"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "SSOT QA"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Last"))), /* @__PURE__ */ React.createElement("tbody", null, filteredInterventions.length === 0 ? /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", { colSpan: 11, style: { ...tdStyle, ...emptyStateStyle } }, "No human intervention data yet.")) : filteredInterventions.map((row) => /* @__PURE__ */ React.createElement("tr", { key: `${row.session_id}-${row.ip}-${row.workflow}-${row.username}` }, /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.username || "unknown"), /* @__PURE__ */ React.createElement("td", { style: tdStyle, title: row.session_id || "" }, row.session || shortId(row.session_id)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.ip || "unknown"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.workspace || "default"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, row.workflow || "\u2014"), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.intervention_count)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.user_messages)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.chat_messages)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.ask_user_answers)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, fmt(row.ssot_qa_answers)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, formatDate(row.last_intervention_at))))))), activeTab === "feedback" && /* @__PURE__ */ React.createElement("div", { style: tableWrapStyle }, /* @__PURE__ */ React.createElement("table", { style: tableStyle }, /* @__PURE__ */ React.createElement("thead", null, /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("th", { style: thStyle }, "When"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "User"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Status"), /* @__PURE__ */ React.createElement("th", { style: { ...thStyle, width: "50%" } }, "Message"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Resolved By"), /* @__PURE__ */ React.createElement("th", { style: thStyle }, "Resolved At"), /* @__PURE__ */ React.createElement("th", { style: thStyle }))), /* @__PURE__ */ React.createElement("tbody", null, filteredFeedback.length === 0 ? /* @__PURE__ */ React.createElement("tr", null, /* @__PURE__ */ React.createElement("td", { colSpan: 7, style: { ...tdStyle, ...emptyStateStyle } }, "No feedback yet. Users can submit with ", /* @__PURE__ */ React.createElement("code", null, "/feedback <message>"), " in the chat.")) : filteredFeedback.map((f) => {
      const open = f.status !== "resolved";
      return /* @__PURE__ */ React.createElement("tr", { key: f.id, style: open ? { background: "#191c22" } : { opacity: 0.65 } }, /* @__PURE__ */ React.createElement("td", { style: tdStyle }, formatDate(f.created_at)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, f.username || f.user_id.slice(0, 8)), /* @__PURE__ */ React.createElement("td", { style: tdStyle }, /* @__PURE__ */ React.createElement("span", { style: {
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
    })))))));
  }
  window.AdminPage = AdminPage;
  if (typeof document !== "undefined" && document.getElementById("root")) {
    ReactDOM.createRoot(document.getElementById("root")).render(/* @__PURE__ */ React.createElement(AdminPage, null));
  }
})();
