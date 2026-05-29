// admin-overview.tsx — TypeScript migration of the AdminPage "overview" tab,
// extracted verbatim from admin.jsx (strangler-fig split, sub-1000 lines).
//
// This is a presentational component: the parent (admin.tsx) computes all the
// derived rows/metrics and passes them down. Styles + pure helpers are imported
// from the admin-styles/admin-helpers modules. JSX is identical to the original
// `activeTab === 'overview'` block.
//
// Cross-file: owns no window globals. Consumes only the typed props below.
import {
  overviewGridStyle, metricCardStyle, metricLabelStyle, metricValueStyle,
  tableWrapStyle, dashboardGridStyle, dashboardWideStyle, widgetHeaderStyle,
  widgetTitleStyle, widgetMetaStyle, barTrackStyle, barFillStyle, mutedSmallStyle,
  tableStyle, thStyle, tdStyle, emptyStateStyle, panelTitleStyle, statusPillStyle,
} from './admin-styles';
import {
  fmt, usd, formatDate, durationMs, shortId, sessionDisplay, rowKey, workloadScore,
  type AdminRow,
} from './admin-helpers';

export interface AdminOverviewTabProps {
  overview: Record<string, number>;
  activeUserRows: AdminRow[];
  ipWorkloadRows: AdminRow[];
  workflowWorkloadRows: AdminRow[];
  maxIpScore: number;
  maxWorkflowScore: number;
  recentSessionRows: AdminRow[];
  recentStageRows: AdminRow[];
  topCostRows: AdminRow[];
  topToolRows: AdminRow[];
  topRejectedTodos: AdminRow[];
  topHumanRows: AdminRow[];
}

export function AdminOverviewTab({
  overview,
  activeUserRows,
  ipWorkloadRows,
  workflowWorkloadRows,
  maxIpScore,
  maxWorkflowScore,
  recentSessionRows,
  recentStageRows,
  topCostRows,
  topToolRows,
  topRejectedTodos,
  topHumanRows,
}: AdminOverviewTabProps) {
  return (
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
  );
}
