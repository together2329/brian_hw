// admin.tsx — TypeScript migration of admin.jsx (strangler-fig migration).
//
// admin.jsx was a single 3246-line `AdminPage` component: ~1100 lines of state,
// effects, fetch handlers and derived values, followed by one ~2100-line JSX
// return that switched on `activeTab`. To get every file under 1000 lines while
// preserving behavior EXACTLY, the per-tab JSX has been moved into sibling
// presentational components (admin-overview / admin-tables-a / admin-tables-b /
// admin-runtime / admin-raw-db), and the style objects + pure helpers into
// admin-styles / admin-helpers. This file keeps the root component: all state,
// effects, handlers and the derived rows, plus the header / login / tab-row /
// filter-bar chrome, and renders the extracted tabs conditionally.
//
// What changed vs admin.jsx (translation-only, no behavior change):
//   - `React.useState` → imported `useState`; same for useEffect/useCallback.
//   - Style objects + pure helpers imported from sibling modules (identical
//     values; the two state-dependent styles are factories taking that state).
//   - Per-tab JSX rendered via imported components with the same data/handlers.
//
// Transitional: still bridges `window.AdminPage = AdminPage` at the bottom and
// mounts via `ReactDOM.createRoot` exactly as the legacy file did, so the live
// .jsx-served app keeps booting until the Vite cutover.
import { useState, useEffect, useCallback } from 'react';
import type { FormEvent } from 'react';
import {
  pageStyle, headerStyle, logoStyle, badgeStyle, headerRightStyle, headerButtonStyle,
  mainStyle,
  loginShellStyle, loginTitleStyle, loginFieldStyle, loginInputStyle, loginButtonStyle,
  errorStateStyle,
} from './admin-styles';
import {
  rowTimestamp, valueMatches, uniqueOptions, aggregateWorkload, workloadScore, sum,
  makeFilterHelpers, type AdminRow, type AdminFilters,
} from './admin-helpers';
import { AdminOverviewTab } from './admin-overview';
import {
  AdminUsersTab, AdminIpsTab, AdminSessionsTab, AdminStagesTab, AdminUsageTab, AdminCostsTab,
} from './admin-tables-a';
import {
  AdminTodosTab, AdminFlowTab, AdminTraceTab, AdminToolsTab, AdminRtlTab, AdminVersionsTab,
  AdminRunSetsTab, AdminHumanTab, AdminInputsTab, AdminMemoryTab,
} from './admin-tables-b';
import { AdminRuntimeTab, AdminFeedbackTab, AdminChatTab } from './admin-runtime';
import { AdminRawDbTab } from './admin-raw-db';
import { AdminTabRow, AdminFilterBar } from './admin-chrome';

// ── Cross-file globals owned by THIS file / by the legacy bootstrap that are
// not yet declared in types/atlas-window.d.ts (the orchestrator maintains that
// file; we must not edit it). We read/write them through a locally typed view
// of `window`, matching the preview-pane.tsx pattern. `ReactDOM` is the global
// UMD build loaded by admin.html before this script.
declare const ReactDOM: { createRoot: (el: Element) => { render: (node: unknown) => void } };
interface AdminWindow {
  AdminPage?: unknown;
  confirm: (message?: string) => boolean;
}
const adminWindow = window as unknown as AdminWindow;

function AdminPage() {
  const [users, setUsers] = useState<AdminRow[]>([]);
  const [sessions, setSessions] = useState<AdminRow[]>([]);
  const [ips, setIps] = useState<AdminRow[]>([]);
  const [usage, setUsage] = useState<AdminRow[]>([]);
  const [costContexts, setCostContexts] = useState<AdminRow[]>([]);
  const [dateCosts, setDateCosts] = useState<AdminRow[]>([]);
  const [todoUsage, setTodoUsage] = useState<AdminRow[]>([]);
  const [todoFlow, setTodoFlow] = useState<AdminRow[]>([]);
  const [traceEvents, setTraceEvents] = useState<AdminRow[]>([]);
  const [toolUsage, setToolUsage] = useState<AdminRow[]>([]);
  const [workflowStages, setWorkflowStages] = useState<AdminRow[]>([]);
  const [interventions, setInterventions] = useState<AdminRow[]>([]);
  const [rtlRunHistory, setRtlRunHistory] = useState<AdminRow[]>([]);
  const [artifactVersions, setArtifactVersions] = useState<AdminRow[]>([]);
  const [runArtifactSets, setRunArtifactSets] = useState<AdminRow[]>([]);
  const [feedback, setFeedback] = useState<AdminRow[]>([]);
  const [memoryRules, setMemoryRules] = useState<AdminRow[]>([]);
  const [inputHistory, setInputHistory] = useState<AdminRow[]>([]);
  const [runtime, setRuntime] = useState<AdminRow | null>(null);
  const [adminChatMessages, setAdminChatMessages] = useState<AdminRow[]>([
    {
      role: 'assistant',
      content: 'Ask about feedback, user inputs, tool calls, cost, daily usage, models, workflows, IPs, or memory rules.',
    },
  ]);
  const [adminChatDraft, setAdminChatDraft] = useState('');
  const [adminChatLoading, setAdminChatLoading] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [authStatus, setAuthStatus] = useState<AdminRow | null>(null);
  const [authChecked, setAuthChecked] = useState(false);
  const [authUser, setAuthUser] = useState<AdminRow | null>(null);
  const [authError, setAuthError] = useState<string | null>(null);
  const [loginSubmitting, setLoginSubmitting] = useState(false);
  const [loginForm, setLoginForm] = useState({
    username: 'admin',
    email: '',
    password: '',
    displayName: 'Admin',
  });
  const [activeTab, setActiveTab] = useState('overview');
  const [filters, setFilters] = useState<AdminFilters>({
    range: '7d',
    ip: '',
    workspace: '',
    workflow: '',
    user: '',
  });
  const [deleting, setDeleting] = useState<string | null>(null);
  const [expandedUsage, setExpandedUsage] = useState<unknown>(null);
  const [resolving, setResolving] = useState<unknown>(null);
  const [dbTables, setDbTables] = useState<AdminRow[]>([]);
  const [dbSelectedTable, setDbSelectedTable] = useState<string | null>(null);
  const [dbPage, setDbPage] = useState<{ columns: AdminRow[]; rows: AdminRow[]; total: number; limit: number; offset: number }>({ columns: [], rows: [], total: 0, limit: 50, offset: 0 });
  const [dbLoading, setDbLoading] = useState(false);
  const [dbError, setDbError] = useState<string | null>(null);
  const [dbExpandedRow, setDbExpandedRow] = useState<string | null>(null);
  const [dbOverview, setDbOverview] = useState<AdminRow[]>([]);
  const [dbOverviewLoading, setDbOverviewLoading] = useState(false);
  const [dbHideEmpty, setDbHideEmpty] = useState(true);

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

  const loadAdminData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const [usersResp, sessionsResp, ipsResp, usageResp, fbResp, runtimeResp] = await Promise.all([
        fetch('/api/admin/users'),
        fetch('/api/admin/sessions'),
        fetch('/api/admin/ips'),
        fetch('/api/admin/usage'),
        fetch('/api/admin/feedback'),
        fetch('/api/admin/runtime'),
      ]);
      if ([usersResp, sessionsResp, ipsResp, usageResp, fbResp, runtimeResp].some((r) => r.status === 401)) {
        setAuthUser(null);
        setAuthStatus((prev) => ({ ...(prev || {}), login_required: true, authenticated: false }));
        setAuthError('Admin login required');
        return;
      }
      if ([usersResp, sessionsResp, ipsResp, usageResp, fbResp, runtimeResp].some((r) => r.status === 403)) {
        setError('Admin role required');
        return;
      }
      if (!usersResp.ok || !sessionsResp.ok || !ipsResp.ok) {
        const bad = !usersResp.ok ? usersResp : (!sessionsResp.ok ? sessionsResp : ipsResp);
        let detail = `HTTP ${bad.status}`;
        try {
          const body = await bad.json();
          detail = body.error || body.detail || detail;
        } catch (_) {}
        throw new Error(detail);
      }
      const usersData = await usersResp.json();
      const sessionsData = await sessionsResp.json();
      const ipsData = await ipsResp.json();
      const usageData = usageResp.ok ? await usageResp.json() : { users: [] };
      const fbData = fbResp.ok ? await fbResp.json() : { feedback: [] };
      const runtimeData = runtimeResp.ok ? await runtimeResp.json() : null;
      setUsers(usersData.users || []);
      setSessions(sessionsData.sessions || []);
      setIps(ipsData.ips || []);
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

  useEffect(() => {
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

  const handleAdminLogin = async (ev: FormEvent<HTMLFormElement>) => {
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
      if (createFirstAdmin && authStatus!.email_required && !email) {
        throw new Error('Email required');
      }
      const payload: AdminRow = {
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
    setIps([]);
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

  const loadDbTables = useCallback(async () => {
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

  const loadDbTable = useCallback(async (name: string, offset = 0, limit = 50) => {
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

  const loadDbOverview = useCallback(async () => {
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

  useEffect(() => {
    if (activeTab !== 'raw-db' || !authUser) return;
    if (dbTables.length === 0) loadDbTables();
    if (dbOverview.length === 0 && !dbSelectedTable) loadDbOverview();
  }, [activeTab, authUser, dbTables.length, dbOverview.length, dbSelectedTable, loadDbTables, loadDbOverview]);

  useEffect(() => {
    if (activeTab !== 'raw-db' || !dbSelectedTable) return;
    loadDbTable(dbSelectedTable, 0, dbPage.limit || 50);
    // dbPage.limit captured intentionally on table-change only
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dbSelectedTable, activeTab]);

  const handleResolveFeedback = async (fid: any) => {
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

  const handleDeleteSession = async (sessionId: any) => {
    if (!adminWindow.confirm('Force-delete this session?')) return;
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

  const handleDeleteIpPointer = async (ipId: any) => {
    if (!adminWindow.confirm('Remove this IP pointer from Atlas DB only? Project files and .session data will not be deleted.')) return;
    const deletingKey = `ip:${ipId}`;
    setDeleting(deletingKey);
    try {
      const resp = await fetch('/api/admin/ips/' + encodeURIComponent(ipId), {
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
      await loadAdminData();
    } catch (e) {
      alert('Failed to remove IP pointer: ' + e);
    } finally {
      setDeleting(null);
    }
  };

  const handleDeleteUserPointer = async (userId: any) => {
    if (!adminWindow.confirm('Remove this user pointer from Atlas DB only? Project files and .session data will not be deleted.')) return;
    const deletingKey = `user:${userId}`;
    setDeleting(deletingKey);
    try {
      const resp = await fetch('/api/admin/users/' + encodeURIComponent(userId), {
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
      await loadAdminData();
    } catch (e) {
      alert('Failed to remove user pointer: ' + e);
    } finally {
      setDeleting(null);
    }
  };

  const handleAdminChatSubmit = async (ev: FormEvent<HTMLFormElement>) => {
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
      let body: AdminRow = {};
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

  const { inRange, rowMatches } = makeFilterHelpers(filters);

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
  const ipPointerContextRows = ips.map((ip) => ({
    username: ip.owner_username || ip.owner_user_id || '',
    ip: ip.ip_name || '',
    workspace: ip.workspace_name || ip.workspace_id || '',
    updated_at: ip.updated_at || ip.created_at,
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
    ...ipPointerContextRows,
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
  const filteredIps = ips.filter((row) => (
    inRange(row)
    && valueMatches(filters.user, row.owner_username || row.owner_user_id)
    && valueMatches(filters.ip, row.ip_name)
    && valueMatches(filters.workspace, row.workspace_name || row.workspace_id)
    && !filters.workflow
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
  const overview: Record<string, number> = {
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
  const workerRuntime = (runtime && runtime.worker_runtime) || {};
  const ipcRuntime = workerRuntime.ipc || {};
  const ipcLimits = ipcRuntime.limits || {};
  const ipcJobs: AdminRow[] = Array.isArray(ipcRuntime.jobs) ? ipcRuntime.jobs : [];
  const runtimeScm = (runtime && runtime.scm) || {};
  const runtimeAtlas = (runtime && runtime.atlas) || {};
  const runtimeTransport = workerRuntime.transport || 'unknown';
  const setFilter = (key: keyof AdminFilters, value: string) => setFilters((prev) => ({ ...prev, [key]: value }));
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
            {!authStatus!.admin_user_exists && (
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
            {!authStatus!.admin_user_exists && (
              <label style={loginFieldStyle}>
                Email{authStatus!.email_required ? '' : ' (optional)'}
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
                autoComplete={authStatus!.admin_user_exists ? 'current-password' : 'new-password'}
                onChange={(ev) => setLoginForm((prev) => ({ ...prev, password: ev.target.value }))}
              />
            </label>
            <button type="submit" style={loginButtonStyle(loginSubmitting)} disabled={loginSubmitting}>
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
            <AdminTabRow
              activeTab={activeTab}
              setActiveTab={setActiveTab}
              counts={{
                users: filteredUsers.length,
                ips: filteredIps.length,
                sessions: filteredSessions.length,
                workflowStages: filteredWorkflowStages.length,
                usage: filteredUsage.length,
                costContexts: filteredCostContexts.length,
                todoUsage: filteredTodoUsage.length,
                todoFlow: filteredTodoFlow.length,
                traceEvents: filteredTraceEvents.length,
                toolUsage: filteredToolUsage.length,
                rtlRunHistory: filteredRtlRunHistory.length,
                artifactVersions: filteredArtifactVersions.length,
                runArtifactSets: filteredRunArtifactSets.length,
                interventions: filteredInterventions.length,
                inputHistory: filteredInputHistory.length,
                memoryRules: filteredMemoryRules.length,
                feedbackOpen: filteredFeedback.filter(f => f.status !== 'resolved').length,
                feedbackTotal: filteredFeedback.length,
              }}
            />

            <AdminFilterBar
              filters={filters}
              setFilter={setFilter}
              clearFilters={clearFilters}
              filterOptions={filterOptions}
            />

            {activeTab === 'overview' && (
              <AdminOverviewTab
                overview={overview}
                activeUserRows={activeUserRows}
                ipWorkloadRows={ipWorkloadRows}
                workflowWorkloadRows={workflowWorkloadRows}
                maxIpScore={maxIpScore}
                maxWorkflowScore={maxWorkflowScore}
                recentSessionRows={recentSessionRows}
                recentStageRows={recentStageRows}
                topCostRows={topCostRows}
                topToolRows={topToolRows}
                topRejectedTodos={topRejectedTodos}
                topHumanRows={topHumanRows}
              />
            )}

            {activeTab === 'users' && (
              <AdminUsersTab
                filteredUsers={filteredUsers}
                deleting={deleting}
                authUser={authUser}
                handleDeleteUserPointer={handleDeleteUserPointer}
              />
            )}

            {activeTab === 'ips' && (
              <AdminIpsTab
                filteredIps={filteredIps}
                deleting={deleting}
                handleDeleteIpPointer={handleDeleteIpPointer}
              />
            )}

            {activeTab === 'sessions' && (
              <AdminSessionsTab
                filteredSessions={filteredSessions}
                deleting={deleting}
                handleDeleteSession={handleDeleteSession}
              />
            )}

            {activeTab === 'stages' && (
              <AdminStagesTab filteredWorkflowStages={filteredWorkflowStages} />
            )}

            {activeTab === 'usage' && (
              <AdminUsageTab
                filteredUsage={filteredUsage}
                expandedUsage={expandedUsage}
                setExpandedUsage={setExpandedUsage}
              />
            )}

            {activeTab === 'costs' && (
              <AdminCostsTab
                filteredCostContexts={filteredCostContexts}
                filteredDateCosts={filteredDateCosts}
              />
            )}

            {activeTab === 'todos' && (
              <AdminTodosTab filteredTodoUsage={filteredTodoUsage} />
            )}

            {activeTab === 'flow' && (
              <AdminFlowTab filteredTodoFlow={filteredTodoFlow} />
            )}

            {activeTab === 'trace' && (
              <AdminTraceTab filteredTraceEvents={filteredTraceEvents} />
            )}

            {activeTab === 'tools' && (
              <AdminToolsTab filteredToolUsage={filteredToolUsage} />
            )}

            {activeTab === 'rtl' && (
              <AdminRtlTab filteredRtlRunHistory={filteredRtlRunHistory} />
            )}

            {activeTab === 'versions' && (
              <AdminVersionsTab filteredArtifactVersions={filteredArtifactVersions} />
            )}

            {activeTab === 'run-sets' && (
              <AdminRunSetsTab filteredRunArtifactSets={filteredRunArtifactSets} />
            )}

            {activeTab === 'human' && (
              <AdminHumanTab filteredInterventions={filteredInterventions} />
            )}

            {activeTab === 'inputs' && (
              <AdminInputsTab filteredInputHistory={filteredInputHistory} />
            )}

            {activeTab === 'memory' && (
              <AdminMemoryTab filteredMemoryRules={filteredMemoryRules} />
            )}

            {activeTab === 'runtime' && (
              <AdminRuntimeTab
                runtime={runtime}
                runtimeTransport={runtimeTransport}
                ipcRuntime={ipcRuntime}
                ipcLimits={ipcLimits}
                ipcJobs={ipcJobs}
                runtimeScm={runtimeScm}
                runtimeAtlas={runtimeAtlas}
              />
            )}

            {activeTab === 'feedback' && (
              <AdminFeedbackTab
                filteredFeedback={filteredFeedback}
                resolving={resolving}
                handleResolveFeedback={handleResolveFeedback}
              />
            )}

            {activeTab === 'admin-chat' && (
              <AdminChatTab
                adminChatMessages={adminChatMessages}
                adminChatLoading={adminChatLoading}
                adminChatDraft={adminChatDraft}
                setAdminChatDraft={setAdminChatDraft}
                handleAdminChatSubmit={handleAdminChatSubmit}
              />
            )}

            {activeTab === 'raw-db' && (
              <AdminRawDbTab
                dbTables={dbTables}
                dbSelectedTable={dbSelectedTable}
                setDbSelectedTable={setDbSelectedTable}
                dbPage={dbPage}
                dbLoading={dbLoading}
                dbError={dbError}
                dbExpandedRow={dbExpandedRow}
                setDbExpandedRow={setDbExpandedRow}
                dbOverview={dbOverview}
                dbOverviewLoading={dbOverviewLoading}
                dbHideEmpty={dbHideEmpty}
                setDbHideEmpty={setDbHideEmpty}
                loadDbTables={loadDbTables}
                loadDbTable={loadDbTable}
                loadDbOverview={loadDbOverview}
              />
            )}
          </>
        )}
      </main>
    </div>
  );
}

export { AdminPage };

// ── Transitional bridge + bootstrap: identical to admin.jsx so the legacy
// .jsx-served page keeps resolving `window.AdminPage` and mounting at #root.
adminWindow.AdminPage = AdminPage;

if (typeof document !== 'undefined' && document.getElementById('root')) {
  ReactDOM.createRoot(document.getElementById('root')!).render(<AdminPage />);
}
