// admin-tables-a.tsx — TypeScript migration of the AdminPage data-table tabs
// (users / ips / sessions / stages / usage / costs), extracted verbatim from
// admin.jsx (strangler-fig split, sub-1000 lines).
//
// Presentational: the parent (admin.tsx) owns state + handlers and passes them
// down. Each tab is rendered conditionally by the parent based on `activeTab`.
// Styles + pure helpers come from the admin-styles/admin-helpers modules.
//
// Cross-file: owns no window globals. Consumes only the typed props below.
import {
  tableWrapStyle, tableStyle, thStyle, tdStyle, emptyStateStyle, statusPillStyle,
  btnDangerStyle,
} from './admin-styles';
import {
  fmt, usd, formatDate, durationMs, shortId, sessionDisplay, rowKey,
  type AdminRow,
} from './admin-helpers';

// ── Users tab ──────────────────────────────────────────────────────────────
export interface AdminUsersTabProps {
  filteredUsers: AdminRow[];
  deleting: unknown;
  authUser: AdminRow | null;
  handleDeleteUserPointer: (userId: any) => void;
}

export function AdminUsersTab({ filteredUsers, deleting, authUser, handleDeleteUserPointer }: AdminUsersTabProps) {
  return (
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
            <th style={thStyle}></th>
          </tr>
        </thead>
        <tbody>
          {filteredUsers.length === 0 ? (
            <tr>
              <td colSpan={10} style={{ ...tdStyle, ...emptyStateStyle }}>No users found.</td>
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
                <td style={tdStyle}>
                  <button
                    style={btnDangerStyle(deleting)}
                    onClick={() => handleDeleteUserPointer(u.id)}
                    disabled={deleting === `user:${u.id}` || (!!authUser && authUser.id === u.id)}
                    title={(authUser && authUser.id === u.id) ? 'Signed-in admin cannot remove itself' : 'Remove Atlas DB user pointer only'}
                  >
                    {deleting === `user:${u.id}` ? 'Removing...' : 'Remove pointer'}
                  </button>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

// ── IPs tab ────────────────────────────────────────────────────────────────
export interface AdminIpsTabProps {
  filteredIps: AdminRow[];
  deleting: unknown;
  handleDeleteIpPointer: (ipId: any) => void;
}

export function AdminIpsTab({ filteredIps, deleting, handleDeleteIpPointer }: AdminIpsTabProps) {
  return (
    <div style={tableWrapStyle}>
      <table style={tableStyle}>
        <thead>
          <tr>
            <th style={thStyle}>IP</th>
            <th style={thStyle}>Owner</th>
            <th style={thStyle}>Workspace</th>
            <th style={thStyle}>Status</th>
            <th style={thStyle}>Sessions</th>
            <th style={thStyle}>Permissions</th>
            <th style={thStyle}>Artifacts</th>
            <th style={thStyle}>Runs</th>
            <th style={thStyle}>Updated</th>
            <th style={thStyle}></th>
          </tr>
        </thead>
        <tbody>
          {filteredIps.length === 0 ? (
            <tr>
              <td colSpan={10} style={{ ...tdStyle, ...emptyStateStyle }}>No IP pointers found.</td>
            </tr>
          ) : (
            filteredIps.map((ip, index) => (
              <tr key={rowKey('ip', index, ip.id, ip.ip_name, ip.workspace_id)}>
                <td style={tdStyle}>{ip.ip_name || '—'}</td>
                <td style={tdStyle}>{ip.owner_username || ip.owner_user_id || '—'}</td>
                <td style={tdStyle}>
                  {ip.workspace_name || ip.workspace_id || '—'}
                  {ip.workspace_path ? (
                    <div style={{ opacity: 0.65, fontSize: 11 }}>{ip.workspace_path}</div>
                  ) : null}
                </td>
                <td style={tdStyle}>
                  <span style={{
                    fontSize: 10,
                    fontWeight: 600,
                    textTransform: 'uppercase',
                    padding: '2px 6px',
                    borderRadius: 3,
                    background: ip.status === 'active' ? '#1c2f25' : '#1c252f',
                    color: ip.status === 'active' ? '#7dc9a0' : '#a3aebb',
                    border: '1px solid #2a3540',
                  }}>
                    {ip.status || 'unknown'}
                  </span>
                </td>
                <td style={tdStyle}>{ip.session_count ?? 0}</td>
                <td style={tdStyle}>{ip.permission_count ?? 0}</td>
                <td style={tdStyle}>{ip.artifact_version_count ?? 0}</td>
                <td style={tdStyle}>{ip.workflow_run_count ?? 0}</td>
                <td style={tdStyle}>{formatDate(ip.updated_at || ip.created_at)}</td>
                <td style={tdStyle}>
                  <button
                    style={btnDangerStyle(deleting)}
                    onClick={() => handleDeleteIpPointer(ip.id)}
                    disabled={deleting === `ip:${ip.id}`}
                    title="Remove Atlas DB IP pointer only"
                  >
                    {deleting === `ip:${ip.id}` ? 'Removing...' : 'Remove pointer'}
                  </button>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}

// ── Sessions tab ─────────────────────────────────────────────────────────────
export interface AdminSessionsTabProps {
  filteredSessions: AdminRow[];
  deleting: unknown;
  handleDeleteSession: (sessionId: any) => void;
}

export function AdminSessionsTab({ filteredSessions, deleting, handleDeleteSession }: AdminSessionsTabProps) {
  return (
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
                    style={btnDangerStyle(deleting)}
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
  );
}

// ── Stages tab ───────────────────────────────────────────────────────────────
export interface AdminStagesTabProps {
  filteredWorkflowStages: AdminRow[];
}

export function AdminStagesTab({ filteredWorkflowStages }: AdminStagesTabProps) {
  return (
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
  );
}

// ── Usage tab ────────────────────────────────────────────────────────────────
export interface AdminUsageTabProps {
  filteredUsage: AdminRow[];
  expandedUsage: unknown;
  setExpandedUsage: (v: any) => void;
}

export function AdminUsageTab({ filteredUsage, expandedUsage, setExpandedUsage }: AdminUsageTabProps) {
  return (
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
                                {u.models.slice(0, 8).map((m: AdminRow, modelIndex: number) => (
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
                                {u.tools.slice(0, 10).map((t: AdminRow, toolIndex: number) => (
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
  );
}

// ── Costs tab ────────────────────────────────────────────────────────────────
export interface AdminCostsTabProps {
  filteredCostContexts: AdminRow[];
  filteredDateCosts: AdminRow[];
}

export function AdminCostsTab({ filteredCostContexts, filteredDateCosts }: AdminCostsTabProps) {
  return (
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
  );
}
