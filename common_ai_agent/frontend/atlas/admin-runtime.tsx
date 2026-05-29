// admin-runtime.tsx — TypeScript migration of the AdminPage runtime / feedback /
// admin-chat tabs, extracted verbatim from admin.jsx (strangler-fig split).
//
// Presentational: the parent (admin.tsx) owns state + handlers and passes them
// down. Styles + pure helpers come from admin-styles/admin-helpers modules.
//
// Cross-file: owns no window globals. Consumes only the typed props below.
import type { FormEvent } from 'react';
import {
  overviewGridStyle, metricCardStyle, metricLabelStyle, metricValueStyle,
  tableWrapStyle, tableStyle, thStyle, tdStyle, emptyStateStyle,
  widgetHeaderStyle, widgetTitleStyle, widgetMetaStyle, statusPillStyle,
  headerButtonStyle,
} from './admin-styles';
import { fmt, formatDate, shortId, rowKey, type AdminRow } from './admin-helpers';

// ── Runtime tab ──────────────────────────────────────────────────────────────
export interface AdminRuntimeTabProps {
  runtime: AdminRow | null;
  runtimeTransport: unknown;
  ipcRuntime: AdminRow;
  ipcLimits: AdminRow;
  ipcJobs: AdminRow[];
  runtimeScm: AdminRow;
  runtimeAtlas: AdminRow;
}

export function AdminRuntimeTab({
  runtime, runtimeTransport, ipcRuntime, ipcLimits, ipcJobs, runtimeScm, runtimeAtlas,
}: AdminRuntimeTabProps) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div style={overviewGridStyle}>
        <div style={metricCardStyle()}>
          <div style={metricLabelStyle}>Worker Transport</div>
          <div style={metricValueStyle}>{runtimeTransport as any}</div>
        </div>
        <div style={metricCardStyle()}>
          <div style={metricLabelStyle}>IPC Running</div>
          <div style={metricValueStyle}>{fmt(ipcRuntime.running_count || 0)}</div>
        </div>
        <div style={metricCardStyle((ipcRuntime.queued_count || 0) ? 'danger' : 'default')}>
          <div style={metricLabelStyle}>IPC Queued</div>
          <div style={metricValueStyle}>{fmt(ipcRuntime.queued_count || 0)}</div>
        </div>
        <div style={metricCardStyle()}>
          <div style={metricLabelStyle}>IPC Slots</div>
          <div style={metricValueStyle}>{fmt(ipcRuntime.available_slots || 0)}</div>
        </div>
        <div style={metricCardStyle()}>
          <div style={metricLabelStyle}>SCM Provider</div>
          <div style={metricValueStyle}>{runtimeScm.provider || 'auto'}</div>
        </div>
        <div style={metricCardStyle((runtimeScm.ui_override && runtimeScm.ui_override.enabled) ? 'default' : 'danger')}>
          <div style={metricLabelStyle}>SCM UI Override</div>
          <div style={metricValueStyle}>{runtimeScm.ui_override && runtimeScm.ui_override.enabled ? 'on' : 'off'}</div>
        </div>
      </div>

      <div style={tableWrapStyle}>
        <div style={widgetHeaderStyle}>
          <div style={widgetTitleStyle}>Runtime Settings</div>
          <div style={widgetMetaStyle}>{runtimeAtlas.exec_mode || 'mode unknown'}</div>
        </div>
        <table style={tableStyle}>
          <tbody>
            <tr>
              <th style={thStyle}>Run Mode</th>
              <td style={tdStyle}>{runtimeAtlas.run_mode || '—'}</td>
              <th style={thStyle}>Exec Mode</th>
              <td style={tdStyle}>{runtimeAtlas.exec_mode || '—'}</td>
            </tr>
            <tr>
              <th style={thStyle}>IPC Max</th>
              <td style={tdStyle}>{fmt(ipcLimits.max_concurrent)} total · {fmt(ipcLimits.max_per_user)} per user · {fmt(ipcLimits.max_per_workflow)} per workflow</td>
              <th style={thStyle}>Queue / Timeout</th>
              <td style={tdStyle}>{fmt(ipcLimits.queue_limit)} queue · {fmt(ipcLimits.timeout_sec)}s · {fmt(ipcLimits.max_attempts)} attempts</td>
            </tr>
            <tr>
              <th style={thStyle}>SCM Override</th>
              <td style={{ ...tdStyle, wordBreak: 'break-word' }}>
                {runtimeScm.ui_override && runtimeScm.ui_override.ref ? runtimeScm.ui_override.ref : '—'}
              </td>
              <th style={thStyle}>Override File</th>
              <td style={tdStyle}>
                {runtimeScm.ui_override && runtimeScm.ui_override.kind
                  ? `${runtimeScm.ui_override.kind}${runtimeScm.ui_override.exists === false ? ' missing' : ''}`
                  : '—'}
              </td>
            </tr>
          </tbody>
        </table>
        {runtime && runtime.note ? (
          <div style={{ ...tdStyle, color: '#8893a3' }}>{runtime.note}</div>
        ) : null}
      </div>

      <div style={tableWrapStyle}>
        <div style={widgetHeaderStyle}>
          <div style={widgetTitleStyle}>IPC Jobs</div>
          <div style={widgetMetaStyle}>live queue and retry state</div>
        </div>
        <table style={tableStyle}>
          <thead>
            <tr>
              <th style={thStyle}>Job</th>
              <th style={thStyle}>Workflow</th>
              <th style={thStyle}>IP</th>
              <th style={thStyle}>Status</th>
              <th style={thStyle}>Queue</th>
              <th style={thStyle}>Attempt</th>
              <th style={thStyle}>Owner</th>
              <th style={thStyle}>Worker</th>
              <th style={thStyle}>Error</th>
            </tr>
          </thead>
          <tbody>
            {ipcJobs.length === 0 ? (
              <tr><td colSpan={9} style={{ ...tdStyle, ...emptyStateStyle }}>No IPC worker jobs in this process.</td></tr>
            ) : ipcJobs.map((job, index) => (
              <tr key={rowKey('runtime-ipc-job', index, job.job_id, job.run_id)}>
                <td style={tdStyle} title={job.job_id || ''}>{shortId(job.job_id)}</td>
                <td style={tdStyle}>{job.workflow || '—'}</td>
                <td style={tdStyle}>{job.ip || '—'}</td>
                <td style={tdStyle}><span style={statusPillStyle(job.status)}>{job.status || 'unknown'}</span></td>
                <td style={tdStyle}>{job.queue_reason || '—'}</td>
                <td style={tdStyle}>{fmt(job.attempt || 1)} / {fmt(job.max_attempts || 1)}</td>
                <td style={tdStyle}>{job.user_id || job.db_user_id || job.worker_owner || '—'}</td>
                <td style={{ ...tdStyle, maxWidth: 280, wordBreak: 'break-word' }}>{job.worker || '—'}</td>
                <td style={{ ...tdStyle, maxWidth: 320, whiteSpace: 'normal' }}>
                  {job.last_retry_reason || job.error || '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── Feedback tab ─────────────────────────────────────────────────────────────
export interface AdminFeedbackTabProps {
  filteredFeedback: AdminRow[];
  resolving: unknown;
  handleResolveFeedback: (fid: any) => void;
}

export function AdminFeedbackTab({ filteredFeedback, resolving, handleResolveFeedback }: AdminFeedbackTabProps) {
  return (
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
  );
}

// ── Admin Chat tab ───────────────────────────────────────────────────────────
export interface AdminChatTabProps {
  adminChatMessages: AdminRow[];
  adminChatLoading: boolean;
  adminChatDraft: string;
  setAdminChatDraft: (v: string) => void;
  handleAdminChatSubmit: (ev: FormEvent<HTMLFormElement>) => void;
}

export function AdminChatTab({
  adminChatMessages, adminChatLoading, adminChatDraft, setAdminChatDraft, handleAdminChatSubmit,
}: AdminChatTabProps) {
  return (
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
                {msg.sections.map((section: AdminRow, sectionIndex: number) => (
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
  );
}
