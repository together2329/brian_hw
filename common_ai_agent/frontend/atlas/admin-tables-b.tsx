// admin-tables-b.tsx — TypeScript migration of the AdminPage data-table tabs
// (todos / flow / trace / tools / rtl / versions / run-sets / human / inputs /
// memory), extracted verbatim from admin.jsx (strangler-fig split, sub-1000).
//
// Presentational: the parent (admin.tsx) owns state and passes filtered rows
// down. Styles + pure helpers come from admin-styles/admin-helpers modules.
//
// Cross-file: owns no window globals. Consumes only the typed props below.
import {
  tableWrapStyle, tableStyle, thStyle, tdStyle, emptyStateStyle,
} from './admin-styles';
import {
  fmt, usd, formatDate, shortId, sessionDisplay, rowKey, payloadText,
  versionText, versionTagText, type AdminRow,
} from './admin-helpers';

// ── Todos tab ────────────────────────────────────────────────────────────────
export function AdminTodosTab({ filteredTodoUsage }: { filteredTodoUsage: AdminRow[] }) {
  return (
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
  );
}

// ── Flow tab ─────────────────────────────────────────────────────────────────
export function AdminFlowTab({ filteredTodoFlow }: { filteredTodoFlow: AdminRow[] }) {
  return (
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
  );
}

// ── Trace tab ────────────────────────────────────────────────────────────────
export function AdminTraceTab({ filteredTraceEvents }: { filteredTraceEvents: AdminRow[] }) {
  return (
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
  );
}

// ── Tools tab ────────────────────────────────────────────────────────────────
export function AdminToolsTab({ filteredToolUsage }: { filteredToolUsage: AdminRow[] }) {
  return (
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
  );
}

// ── RTL Runs tab ─────────────────────────────────────────────────────────────
export function AdminRtlTab({ filteredRtlRunHistory }: { filteredRtlRunHistory: AdminRow[] }) {
  return (
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
  );
}

// ── Versions tab ─────────────────────────────────────────────────────────────
export function AdminVersionsTab({ filteredArtifactVersions }: { filteredArtifactVersions: AdminRow[] }) {
  return (
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
  );
}

// ── Run Sets tab ─────────────────────────────────────────────────────────────
export function AdminRunSetsTab({ filteredRunArtifactSets }: { filteredRunArtifactSets: AdminRow[] }) {
  return (
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
  );
}

// ── Human tab ────────────────────────────────────────────────────────────────
export function AdminHumanTab({ filteredInterventions }: { filteredInterventions: AdminRow[] }) {
  return (
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
  );
}

// ── Inputs tab ───────────────────────────────────────────────────────────────
export function AdminInputsTab({ filteredInputHistory }: { filteredInputHistory: AdminRow[] }) {
  return (
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
  );
}

// ── Memory tab ───────────────────────────────────────────────────────────────
export function AdminMemoryTab({ filteredMemoryRules }: { filteredMemoryRules: AdminRow[] }) {
  return (
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
  );
}
