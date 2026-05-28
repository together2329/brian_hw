// user-dashboard.tsx - user-scoped Atlas landing dashboard.
//
// TypeScript migration of user-dashboard.jsx (strangler-fig step): ambient
// `React.*` hooks become real `react` imports, the component is a typed export,
// and a transitional `window.AtlasUserDashboard = AtlasUserDashboard` bridge is
// kept at the bottom so not-yet-migrated .jsx consumers keep resolving it.
import {
  useState,
  useCallback,
  useEffect,
  type CSSProperties,
  type MouseEvent,
} from 'react';

// Cross-file global owned by dashboard_helpers (still legacy / not migrated).
// Not declared in types/atlas-window.d.ts, so reference it via a narrow cast
// to keep behavior identical without editing the shared ambient declarations.
type DashboardHelpers = {
  buildOpenIpPayload: (
    row: DashRow,
    workflowValue: (row: DashRow) => string,
  ) => OpenIpPayload;
};

// Rows come straight from the /api/user/dashboard JSON; their shape is dynamic
// and indexed by many optional keys, so model them as a permissive record.
// `any` (not `unknown`) so dynamic field values can flow directly into JSX as
// ReactNode without per-use casts — matches the pre-migration runtime exactly.
type DashValue = any;
interface DashRow {
  [key: string]: DashValue;
}

interface OpenIpPayload {
  id: string;
  ip?: DashValue;
  workflow?: string;
}

interface DashUser {
  username?: string;
  role?: string;
}

interface DashData {
  user?: DashUser;
  current?: DashRow;
  metrics?: DashRow;
  ip_inventory?: DashRow[];
  ip_workload?: DashRow[];
  workflow_progress?: DashRow[];
  recent_sessions?: DashRow[];
  needs_attention?: DashRow[];
  [key: string]: DashValue;
}

export interface AtlasUserDashboardProps {
  activeNamespace?: string;
  activeIp?: string;
  activeWorkflow?: string;
  execMode?: string;
  runMode?: string;
  onOpenScreen?: (screen: string) => void;
  onActivateSession?: (row: DashRow | OpenIpPayload) => void;
}

export const AtlasUserDashboard = ({
  activeNamespace,
  activeIp,
  activeWorkflow,
  execMode,
  runMode,
  onOpenScreen,
  onActivateSession,
}: AtlasUserDashboardProps) => {
  const [data, setData] = useState<DashData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    try {
      setError('');
      const r = await fetch('/api/user/dashboard', { cache: 'no-store' });
      if (!r.ok) {
        let detail = `HTTP ${r.status}`;
        try {
          const body = await r.json();
          detail = body.error || body.detail || detail;
        } catch (_) {}
        throw new Error(detail);
      }
      const body = await r.json();
      setData(body);
    } catch (e) {
      setError(String((e && (e as Error).message) || e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    const run = async () => {
      if (cancelled) return;
      await load();
    };
    run();
    const id = setInterval(run, 5000);
    return () => { cancelled = true; clearInterval(id); };
  }, [load]);

  const fmt = (n: DashValue) => (n == null ? '-' : Number(n || 0).toLocaleString());
  const usd = (n: DashValue) => (n == null ? '-' : `$${Number(n || 0).toFixed(4)}`);
  const ts = (value: DashValue) => {
    if (!value) return '-';
    try { return new Date(Number(value) * 1000).toLocaleString(); }
    catch (_) { return String(value); }
  };
  const shortSession = (value: DashValue) => {
    const text = String(value || '');
    if (!text) return '-';
    const parts = text.split('/');
    if (parts.length >= 3) return `${parts[0]}/${parts[1]}/${parts[2]}`;
    return text.length > 24 ? `${text.slice(0, 21)}...` : text;
  };
  const score = (row: DashRow) => Number(row.cost || 0) || Number(row.calls || 0) || Number(row.sessions || row.runs || 0);
  const listText = (items: DashValue, fallback: string = '-') => {
    const values = (Array.isArray(items) ? items : []).filter(Boolean);
    if (values.length === 0) return fallback;
    if (values.length <= 2) return values.join(', ');
    return `${values.slice(0, 2).join(', ')} +${values.length - 2}`;
  };
  const workflowValue = (row: DashRow) => {
    const last = String((row && row.last_workflow) || '').trim();
    if (last) return last;
    const values = (Array.isArray(row && row.workflows) ? row.workflows : [])
      .map((value: DashValue) => String(value || '').trim())
      .filter(Boolean);
    return values.find((value: string) => value !== 'default') || values[0] || '';
  };
  const workflowText = (row: DashRow) => workflowValue(row) || '-';
  const workspaceText = (row: DashRow) => listText(row.workspaces, listText(row.workspace_paths));
  const rowHealth = (row: DashRow) => {
    if (Number(row.failed || 0) > 0) return 'failed';
    if (Number(row.running || 0) > 0) return 'running';
    return row.status || 'active';
  };
  const current: DashRow = data && data.current ? data.current : {};
  const metrics: DashRow = data && data.metrics ? data.metrics : {};
  const ipInventoryRows: DashRow[] = data && Array.isArray(data.ip_inventory) ? data.ip_inventory : [];
  const ipRows: DashRow[] = data && Array.isArray(data.ip_workload) ? data.ip_workload : [];
  const workflowRows: DashRow[] = data && Array.isArray(data.workflow_progress) ? data.workflow_progress : [];
  const sessionRows: DashRow[] = data && Array.isArray(data.recent_sessions) ? data.recent_sessions : [];
  const needsRows: DashRow[] = data && Array.isArray(data.needs_attention) ? data.needs_attention : [];
  const totalTokens = Number(metrics.tokens_in || 0) + Number(metrics.tokens_out || 0);
  const maxIpScore = Math.max(1, ...ipRows.map(score));
  const maxWorkflowScore = Math.max(1, ...workflowRows.map(score));

  const pageStyle: CSSProperties = {
    height: '100%',
    overflow: 'auto',
    padding: '22px 26px 34px',
    background: 'var(--bg)',
    color: 'var(--fg)',
    fontFamily: 'var(--mono)',
    boxSizing: 'border-box',
  };
  const headerStyle: CSSProperties = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    gap: 16,
    marginBottom: 16,
  };
  const titleStyle: CSSProperties = {
    margin: 0,
    color: 'var(--fg)',
    fontSize: 24,
    lineHeight: 1.15,
    letterSpacing: 0,
  };
  const subStyle: CSSProperties = {
    marginTop: 6,
    color: 'var(--fg-mute)',
    fontSize: 12,
  };
  const actionRowStyle: CSSProperties = {
    display: 'flex',
    flexWrap: 'wrap',
    justifyContent: 'flex-end',
    gap: 8,
  };
  const buttonStyle: CSSProperties = {
    minHeight: 30,
    padding: '6px 11px',
    borderRadius: 5,
    border: '1px solid var(--line)',
    background: 'var(--bg-2)',
    color: 'var(--fg)',
    fontFamily: 'inherit',
    fontSize: 12,
    cursor: 'pointer',
  };
  const primaryButtonStyle: CSSProperties = {
    ...buttonStyle,
    background: 'var(--accent)',
    color: 'var(--bg)',
    borderColor: 'var(--accent)',
    fontWeight: 700,
  };
  const gridStyle: CSSProperties = {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 260px), 1fr))',
    gap: 12,
    marginBottom: 14,
  };
  const panelGridStyle: CSSProperties = {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 520px), 1fr))',
    gap: 14,
  };
  const panelStyle: CSSProperties = {
    background: 'var(--bg-2)',
    border: '1px solid var(--line)',
    borderRadius: 8,
    overflow: 'hidden',
  };
  const panelWideStyle: CSSProperties = {
    ...panelStyle,
    gridColumn: '1 / -1',
  };
  const panelHeaderStyle: CSSProperties = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: 10,
    padding: '11px 13px',
    borderBottom: '1px solid var(--line)',
    background: 'color-mix(in oklch, var(--bg-2) 78%, var(--fg) 6%)',
  };
  const panelTitleStyle: CSSProperties = {
    color: 'var(--accent)',
    fontSize: 12,
    fontWeight: 700,
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  };
  const metaStyle: CSSProperties = {
    color: 'var(--fg-mute)',
    fontSize: 11,
    whiteSpace: 'nowrap',
  };
  const metricStyle: CSSProperties = {
    ...panelStyle,
    minHeight: 84,
    padding: 13,
    boxSizing: 'border-box',
  };
  const metricLabelStyle: CSSProperties = {
    color: 'var(--fg-mute)',
    fontSize: 11,
    fontWeight: 700,
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    marginBottom: 8,
  };
  const metricValueStyle: CSSProperties = {
    color: 'var(--accent)',
    fontSize: 24,
    fontWeight: 800,
    lineHeight: 1.1,
  };
  const tableStyle: CSSProperties = {
    width: '100%',
    borderCollapse: 'collapse',
    fontSize: 12,
  };
  const tableScrollStyle: CSSProperties = {
    overflowX: 'auto',
  };
  const thStyle: CSSProperties = {
    textAlign: 'left',
    padding: '9px 12px',
    color: 'var(--fg-mute)',
    background: 'color-mix(in oklch, var(--bg-2) 86%, var(--fg) 4%)',
    borderBottom: '1px solid var(--line)',
    fontWeight: 700,
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    fontSize: 10.5,
  };
  const tdStyle: CSSProperties = {
    padding: '9px 12px',
    borderBottom: '1px solid var(--line)',
    color: 'var(--fg)',
    verticalAlign: 'top',
  };
  const emptyStyle: CSSProperties = {
    padding: '28px 12px',
    textAlign: 'center',
    color: 'var(--fg-mute)',
  };
  const barTrackStyle: CSSProperties = {
    height: 8,
    borderRadius: 4,
    border: '1px solid var(--line)',
    background: 'var(--bg)',
    overflow: 'hidden',
  };
  const barFillStyle = (width: string, tone: string = 'accent'): CSSProperties => ({
    height: '100%',
    width,
    minWidth: width === '0%' ? 0 : 4,
    background: tone === 'warn' ? 'var(--warn)' : 'var(--accent)',
  });
  const statusBadgeStyle = (status: DashValue): CSSProperties => {
    const s = String(status || '').toLowerCase();
    const danger = ['failed', 'fail', 'error', 'blocked', 'cancelled', 'canceled'].includes(s);
    const running = ['running', 'in_progress', 'queued', 'active'].includes(s);
    return {
      display: 'inline-block',
      padding: '2px 7px',
      borderRadius: 4,
      border: '1px solid var(--line)',
      color: danger ? 'var(--err)' : running ? 'var(--accent)' : 'var(--fg-mute)',
      background: danger
        ? 'color-mix(in oklch, var(--err) 12%, transparent)'
        : running
          ? 'color-mix(in oklch, var(--accent) 12%, transparent)'
          : 'transparent',
      fontSize: 10.5,
      textTransform: 'uppercase',
      fontWeight: 700,
    };
  };

  const openSession = (row: DashRow) => {
    if (onActivateSession) onActivateSession(row);
    if (onOpenScreen) onOpenScreen('workspace');
  };
  const openIp = (row: DashRow) => {
    if (onActivateSession) {
      const helpers = window.AtlasDashboardHelpers as DashboardHelpers | undefined;
      const payload = helpers
        ? helpers.buildOpenIpPayload(row, workflowValue)
        : (() => {
            const wf = workflowValue(row);
            const p: OpenIpPayload = { id: (row.session_id as string) || '', ip: row.ip };
            if (wf) p.workflow = wf;
            return p;
          })();
      onActivateSession(payload);
    }
    if (onOpenScreen) onOpenScreen('workspace');
  };

  if (loading && !data) {
    return <div style={pageStyle}><div style={emptyStyle}>Loading user dashboard...</div></div>;
  }

  return (
    <div style={pageStyle}>
      <div style={headerStyle}>
        <div>
          <h1 style={titleStyle}>User Dashboard</h1>
          <div style={subStyle}>
            {data && data.user ? data.user.username : 'user'} / {activeNamespace || current.session_id || 'default'}
          </div>
        </div>
        <div style={actionRowStyle}>
          <button type="button" style={primaryButtonStyle} onClick={() => onOpenScreen && onOpenScreen('workspace')}>Enter Workspace</button>
          <button type="button" style={buttonStyle} onClick={() => onOpenScreen && onOpenScreen('pipeline')}>Open Pipeline</button>
          <button type="button" style={buttonStyle} onClick={() => onOpenScreen && onOpenScreen('architect')}>Open Architect</button>
          {data && data.user && data.user.role === 'admin' ? (
            <button type="button" style={buttonStyle} onClick={() => { window.location.href = '/admin'; }}>Admin</button>
          ) : null}
          <button type="button" style={buttonStyle} onClick={load}>Refresh</button>
        </div>
      </div>

      {error ? (
        <div style={{ ...panelStyle, padding: 14, marginBottom: 14, color: 'var(--err)' }}>{error}</div>
      ) : null}

      <div style={gridStyle}>
        <div style={metricStyle}>
          <div style={metricLabelStyle}>Current IP</div>
          <div style={metricValueStyle}>{current.ip || activeIp || '-'}</div>
          <div style={metaStyle}>{current.workflow || activeWorkflow || 'default'} / {current.workflow_status || current.session_status || 'idle'}</div>
        </div>
        <div style={metricStyle}>
          <div style={metricLabelStyle}>Active Sessions</div>
          <div style={metricValueStyle}>{fmt(metrics.active_sessions)}</div>
          <div style={metaStyle}>{fmt(metrics.session_count)} total sessions</div>
        </div>
        <div style={metricStyle}>
          <div style={metricLabelStyle}>LLM Calls</div>
          <div style={metricValueStyle}>{fmt(metrics.llm_calls)}</div>
          <div style={metaStyle}>{fmt(totalTokens)} tokens</div>
        </div>
        <div style={metricStyle}>
          <div style={metricLabelStyle}>Cost</div>
          <div style={metricValueStyle}>{usd(metrics.total_cost_usd)}</div>
          <div style={metaStyle}>{fmt(metrics.tokens_reasoning)} reasoning tokens</div>
        </div>
        <div style={metricStyle}>
          <div style={metricLabelStyle}>Needs Attention</div>
          <div style={metricValueStyle}>{fmt(metrics.needs_attention)}</div>
          <div style={metaStyle}>{fmt(metrics.failed_runs)} failed runs</div>
        </div>
        <div style={metricStyle}>
          <div style={metricLabelStyle}>Execution</div>
          <div style={metricValueStyle}>{current.exec_mode || execMode || '-'}</div>
          <div style={metaStyle}>{current.run_mode || runMode || 'engineering'}</div>
        </div>
      </div>

      <div style={panelGridStyle}>
        <div style={panelWideStyle}>
          <div style={panelHeaderStyle}>
            <div style={panelTitleStyle}>IP Inventory</div>
            <div style={metaStyle}>{fmt(metrics.ip_count)} visible IPs</div>
          </div>
          <div style={tableScrollStyle}>
            <table style={tableStyle}>
              <thead>
                <tr>
                  <th style={thStyle}>IP</th>
                  <th style={thStyle}>Status</th>
                  <th style={thStyle}>Workspace</th>
                  <th style={thStyle}>Workflow</th>
                  <th style={thStyle}>Runs</th>
                  <th style={thStyle}>Cost</th>
                  <th style={thStyle}>Updated</th>
                  <th style={thStyle}></th>
                </tr>
              </thead>
              <tbody>
                {ipInventoryRows.length === 0 ? (
                  <tr><td colSpan={8} style={{ ...tdStyle, ...emptyStyle }}>No visible IPs yet.</td></tr>
                ) : ipInventoryRows.map((row) => {
                  const duplicate = Number(row.workspace_count || 0) > 1 || Number(row.ip_row_count || 0) > 1;
                  return (
                    <tr
                      key={`${row.ip}-${row.workspace_count}-${row.ip_row_count}`}
                      onClick={() => openIp(row)}
                      style={{ cursor: 'pointer' }}
                      title={`Open ${row.ip || ''} workspace`}
                    >
                      <td style={{ ...tdStyle, minWidth: 170, wordBreak: 'break-word' }}>
                        <div style={{ fontWeight: 700, color: 'var(--accent)' }}>{row.ip || '-'}</div>
                        <div style={metaStyle}>
                          {row.ip_type || row.permission || 'ip'}
                          {duplicate ? ` / ${fmt(row.ip_row_count)} rows across ${fmt(row.workspace_count)} workspaces` : ''}
                        </div>
                      </td>
                      <td style={tdStyle}><span style={statusBadgeStyle(rowHealth(row))}>{rowHealth(row)}</span></td>
                      <td style={{ ...tdStyle, minWidth: 160, wordBreak: 'break-word' }}>{workspaceText(row)}</td>
                      <td style={tdStyle}>{workflowText(row)}</td>
                      <td style={tdStyle}>{fmt(row.runs)}<div style={metaStyle}>{fmt(row.sessions)} sessions</div></td>
                      <td style={tdStyle}>{usd(row.cost)}<div style={metaStyle}>{fmt(row.calls)} calls</div></td>
                      <td style={tdStyle}>{ts(row.last_activity)}</td>
                      <td style={tdStyle} onClick={(e: MouseEvent<HTMLTableCellElement>) => e.stopPropagation()}>
                        <button type="button" style={buttonStyle} onClick={() => openIp(row)}>Open</button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        <div style={panelStyle}>
          <div style={panelHeaderStyle}>
            <div style={panelTitleStyle}>Current Focus</div>
            <div style={metaStyle}>{ts(current.updated_at)}</div>
          </div>
          <table style={tableStyle}>
            <tbody>
              <tr><th style={thStyle}>Session</th><td style={tdStyle}>{shortSession(current.session_id)}</td></tr>
              <tr><th style={thStyle}>IP</th><td style={tdStyle}>{current.ip || '-'}</td></tr>
              <tr><th style={thStyle}>Workflow</th><td style={tdStyle}>{current.workflow || '-'}</td></tr>
              <tr><th style={thStyle}>Status</th><td style={tdStyle}><span style={statusBadgeStyle(current.workflow_status || current.session_status)}>{current.workflow_status || current.session_status || 'idle'}</span></td></tr>
            </tbody>
          </table>
        </div>

        <div style={panelStyle}>
          <div style={panelHeaderStyle}>
            <div style={panelTitleStyle}>Needs Attention</div>
            <div style={metaStyle}>{needsRows.length} items</div>
          </div>
          <table style={tableStyle}>
            <thead>
              <tr>
                <th style={thStyle}>Kind</th>
                <th style={thStyle}>IP</th>
                <th style={thStyle}>Workflow</th>
                <th style={thStyle}>Detail</th>
              </tr>
            </thead>
            <tbody>
              {needsRows.length === 0 ? (
                <tr><td colSpan={4} style={{ ...tdStyle, ...emptyStyle }}>No attention items.</td></tr>
              ) : needsRows.map((row, idx) => (
                <tr
                  key={`${row.kind}-${row.session_id}-${idx}`}
                  onClick={() => row.ip && openIp(row)}
                  style={{ cursor: row.ip ? 'pointer' : 'default' }}
                  title={row.ip ? `Open ${row.ip} workspace` : ''}
                >
                  <td style={tdStyle}><span style={statusBadgeStyle(row.severity === 'error' ? 'error' : 'warning')}>{row.kind}</span></td>
                  <td style={tdStyle}><span style={row.ip ? { color: 'var(--accent)', fontWeight: 600 } : {}}>{row.ip || '-'}</span></td>
                  <td style={tdStyle}>{row.workflow || '-'}</td>
                  <td style={{ ...tdStyle, maxWidth: 320, whiteSpace: 'normal' }}>{row.title || row.detail || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div style={panelStyle}>
          <div style={panelHeaderStyle}>
            <div style={panelTitleStyle}>My IP Workload</div>
            <div style={metaStyle}>{fmt(metrics.ip_count)} IPs</div>
          </div>
          <table style={tableStyle}>
            <thead>
              <tr>
                <th style={thStyle}>IP</th>
                <th style={thStyle}>Load</th>
                <th style={thStyle}>Calls</th>
                <th style={thStyle}>Cost</th>
              </tr>
            </thead>
            <tbody>
              {ipRows.length === 0 ? (
                <tr><td colSpan={4} style={{ ...tdStyle, ...emptyStyle }}>No IP workload yet.</td></tr>
              ) : ipRows.map((row) => {
                const width = `${Math.round((score(row) / maxIpScore) * 100)}%`;
                return (
                  <tr
                    key={row.ip as string}
                    onClick={() => row.ip && openIp(row)}
                    style={{ cursor: row.ip ? 'pointer' : 'default' }}
                    title={row.ip ? `Open ${row.ip} workspace` : ''}
                  >
                    <td style={tdStyle}><span style={row.ip ? { color: 'var(--accent)', fontWeight: 600 } : {}}>{row.ip || '-'}</span></td>
                    <td style={{ ...tdStyle, minWidth: 170 }}>
                      <div style={barTrackStyle}><div style={barFillStyle(width)} /></div>
                      <div style={metaStyle}>{fmt(row.sessions)} sessions / {(Array.isArray(row.workflows) ? row.workflows : []).join(', ') || 'default'}</div>
                    </td>
                    <td style={tdStyle}>{fmt(row.calls)}</td>
                    <td style={tdStyle}>{usd(row.cost)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <div style={panelStyle}>
          <div style={panelHeaderStyle}>
            <div style={panelTitleStyle}>Workflow Progress</div>
            <div style={metaStyle}>{fmt(metrics.workflow_count)} workflows</div>
          </div>
          <table style={tableStyle}>
            <thead>
              <tr>
                <th style={thStyle}>Workflow</th>
                <th style={thStyle}>Load</th>
                <th style={thStyle}>Runs</th>
                <th style={thStyle}>Status</th>
              </tr>
            </thead>
            <tbody>
              {workflowRows.length === 0 ? (
                <tr><td colSpan={4} style={{ ...tdStyle, ...emptyStyle }}>No workflow runs yet.</td></tr>
              ) : workflowRows.map((row) => {
                const width = `${Math.round((score(row) / maxWorkflowScore) * 100)}%`;
                return (
                  <tr key={row.workflow as string}>
                    <td style={tdStyle}>{row.workflow || '-'}</td>
                    <td style={{ ...tdStyle, minWidth: 170 }}>
                      <div style={barTrackStyle}><div style={barFillStyle(width, row.failed ? 'warn' : 'accent')} /></div>
                      <div style={metaStyle}>{fmt(row.calls)} calls / {usd(row.cost)}</div>
                    </td>
                    <td style={tdStyle}>{fmt(row.runs)}</td>
                    <td style={tdStyle}>
                      <span style={statusBadgeStyle(row.last_status || (row.running ? 'running' : row.failed ? 'failed' : 'idle'))}>
                        {row.running ? 'running' : row.failed ? 'failed' : row.passed ? 'passed' : row.last_status || 'idle'}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <div style={panelWideStyle}>
          <div style={panelHeaderStyle}>
            <div style={panelTitleStyle}>Recent Sessions</div>
            <div style={metaStyle}>{sessionRows.length} shown</div>
          </div>
          <table style={tableStyle}>
            <thead>
              <tr>
                <th style={thStyle}>Session</th>
                <th style={thStyle}>IP</th>
                <th style={thStyle}>Workflow</th>
                <th style={thStyle}>Status</th>
                <th style={thStyle}>Updated</th>
                <th style={thStyle}></th>
              </tr>
            </thead>
            <tbody>
              {sessionRows.length === 0 ? (
                <tr><td colSpan={6} style={{ ...tdStyle, ...emptyStyle }}>No sessions yet.</td></tr>
              ) : sessionRows.map((row) => (
                <tr key={row.id as string}>
                  <td style={tdStyle}>{shortSession(row.id)}</td>
                  <td style={tdStyle}>{row.ip || '-'}</td>
                  <td style={tdStyle}>{row.workflow || '-'}</td>
                  <td style={tdStyle}><span style={statusBadgeStyle(row.workflow_status || row.status)}>{row.workflow_status || row.status || 'idle'}</span></td>
                  <td style={tdStyle}>{ts(row.updated_at)}</td>
                  <td style={tdStyle}>
                    <button type="button" style={buttonStyle} onClick={() => openSession(row)}>Open</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// ── Transitional bridge: register on window for not-yet-migrated .jsx ──
// AtlasUserDashboard is not (yet) declared in types/atlas-window.d.ts, so the
// assignment goes through a cast to avoid editing the shared ambient file.
(window as unknown as { AtlasUserDashboard: typeof AtlasUserDashboard }).AtlasUserDashboard = AtlasUserDashboard;
