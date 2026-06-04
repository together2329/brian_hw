// admin-session-flow.tsx — the Session Flow admin tab (Task 6 full dashboard).
//
// Renders the /api/admin/session-flow read-model as a dense operational
// dashboard: a Needs Attention count band, an independent-per-stage funnel, a
// triage table (left/center) + detail panel (right), and an IP provenance/flow
// section. A client-side lens toggle (builder / team_lead / executive) changes
// which FIELDS and sections are visible WITHOUT refetching the API — admin.tsx
// owns the lens state and never sends it to the server.
//
// Funnel labeling (review MINOR-4): the funnel entries are INDEPENDENT per-stage
// tallies (how many sessions reached each stage), NOT a strict monotonic
// drop-off. They are rendered as independent stage counts and never imply that
// each stage is a subset of the prior one.
//
// Privacy: no raw prompt content is rendered — only counts/ids/reason-codes from
// the sanitized payload. Styles come from admin-styles; formatters from
// admin-helpers. No nested cards, no marketing hero.
//
// Cross-file: owns no window globals. Consumes only the typed props below.
import { useMemo, useState, type ReactNode } from 'react';
import {
  tableWrapStyle, tableStyle, thStyle, tdStyle, emptyStateStyle, errorStateStyle,
  statusPillStyle, overviewGridStyle, metricCardStyle, metricLabelStyle,
  metricValueStyle, panelTitleStyle, tabStyle, mutedSmallStyle,
} from './admin-styles';
import {
  fmt, usd, shortId, rowKey, formatDate, type AdminRow,
} from './admin-helpers';

export type SessionFlowLens = 'builder' | 'team_lead' | 'executive';

export interface AdminSessionFlowTabProps {
  data: AdminRow | null;
  loading: boolean;
  error: string | null;
  lens: string;
  onLensChange: (lens: SessionFlowLens) => void;
}

const LENS_OPTIONS: { id: SessionFlowLens; label: string }[] = [
  { id: 'builder', label: 'Builder' },
  { id: 'team_lead', label: 'Team Lead' },
  { id: 'executive', label: 'Executive' },
];

// Friendly stage labels for the independent-per-stage funnel.
const FUNNEL_LABELS: Record<string, string> = {
  created: 'Created',
  input: 'Input',
  worker: 'Worker',
  llm: 'LLM',
  artifact: 'Artifact',
  verified: 'Verified',
  completed: 'Completed',
};

// Compact worker-status summary from the per-session counters.
function workerStatusText(row: AdminRow): string {
  const total = Number(row.worker_runs || 0);
  if (!total) return 'none';
  const active = Number(row.active_workers || 0);
  const failed = Number(row.failed_workers || 0);
  const parts: string[] = [`${total} run${total === 1 ? '' : 's'}`];
  if (active) parts.push(`${active} active`);
  if (failed) parts.push(`${failed} failed`);
  return parts.join(' · ');
}

// Human-friendly age from a stale_age_s counter (the rollup's idle seconds).
function ageText(row: AdminRow): string {
  const secs = Number(row.stale_age_s || 0);
  if (!secs || secs < 0) return '—';
  if (secs < 60) return `${Math.round(secs)}s`;
  if (secs < 3600) return `${Math.round(secs / 60)}m`;
  if (secs < 86400) return `${(secs / 3600).toFixed(1)}h`;
  return `${(secs / 86400).toFixed(1)}d`;
}

// Normalize the funnel into an ordered [{stage,count}] list.
// The payload contract is always a list (core/session_flow_usage._funnel);
// a non-array value yields an empty list so a shape regression fails loud.
function funnelStages(funnel: unknown): { stage: string; count: number }[] {
  if (Array.isArray(funnel)) {
    return funnel.map((f: AdminRow) => ({
      stage: String(f.stage || ''),
      count: Number(f.count || 0),
    }));
  }
  return [];
}

// One labeled cell in the detail panel's metric grids.
function DetailMetric({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div style={metricCardStyle('default')}>
      <div style={metricLabelStyle}>{label}</div>
      <div style={{ ...metricValueStyle, fontSize: 18 }}>{value}</div>
    </div>
  );
}

// A small section header inside the detail panel (no nested cards).
function DetailSection({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      <div style={{ ...panelTitleStyle, padding: '8px 0', background: 'transparent', borderBottom: '1px solid #2a3540' }}>
        {title}
      </div>
      {children}
    </div>
  );
}

export function AdminSessionFlowTab({
  data, loading, error, lens, onLensChange,
}: AdminSessionFlowTabProps) {
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const activeLens: SessionFlowLens = (
    lens === 'builder' || lens === 'executive' ? lens : 'team_lead'
  );
  const showRawIds = activeLens === 'builder';
  const showAttribution = activeLens === 'builder';
  const showExecRollup = activeLens === 'executive';

  const summary: AdminRow = data?.summary || {};
  const needsAttention: AdminRow[] = Array.isArray(data?.needs_attention) ? data!.needs_attention : [];
  const sessions: AdminRow[] = Array.isArray(data?.sessions) ? data!.sessions : [];
  const ipFlow: AdminRow[] = Array.isArray(data?.ip_flow) ? data!.ip_flow : [];
  const attributionGaps: AdminRow[] = Array.isArray(data?.attribution_gaps) ? data!.attribution_gaps : [];
  const stages = useMemo(() => funnelStages(data?.funnel), [data?.funnel]);

  // Resolve the selected session row from the current payload (selection is by
  // id so it survives lens toggles, which never refetch).
  const selected: AdminRow | null = useMemo(() => {
    if (!selectedId) return null;
    return sessions.find(
      (s) => String(s.session_id) === selectedId || String(s.session_uid) === selectedId,
    ) || null;
  }, [selectedId, sessions]);

  // The lens toggle renders even in loading/error/empty states so switching the
  // lens never depends on a fetch having completed.
  const lensToggle = (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <span style={mutedSmallStyle}>Lens</span>
      <div style={{ display: 'flex', gap: 4 }}>
        {LENS_OPTIONS.map((opt) => (
          <button
            key={opt.id}
            type="button"
            style={tabStyle(activeLens === opt.id)}
            aria-pressed={activeLens === opt.id}
            onClick={() => onLensChange(opt.id)}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );

  if (loading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>{lensToggle}</div>
        <div style={{ textAlign: 'center', padding: '40px 0', color: '#8893a3' }}>
          Loading session flow…
        </div>
      </div>
    );
  }
  if (error) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>{lensToggle}</div>
        <div style={errorStateStyle}>{error}</div>
      </div>
    );
  }
  if (!data) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>{lensToggle}</div>
        <div style={emptyStateStyle}>No session flow data yet.</div>
      </div>
    );
  }

  const criticalCount = Number(summary.critical || 0);
  const warningCount = Number(summary.warning || 0);
  const okCount = Number(summary.ok || 0);
  const staleWorkerCount = sessions.reduce(
    (acc, s) => acc + (Number(s.failed_workers || 0) > 0 ? 1 : 0), 0,
  );
  const unmatchedCost = Number(summary.unmatched_cost_usd || 0);
  const totalCost = Number(summary.total_cost_usd || 0);
  const totalInputs = Number(summary.total_inputs || 0);
  const totalArtifacts = Number(summary.total_artifacts || 0);
  const totalLlm = Number(summary.total_llm_attempts || 0);

  const isEmpty = sessions.length === 0 && ipFlow.length === 0 && attributionGaps.length === 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Header row: range/runtime meta on the left, client-side lens toggle on the right. */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
        <div style={mutedSmallStyle}>
          {data.runtime_mode ? 'runtime mode (rollups)' : 'central mode'} · range {String(data.range || '7d')}
          {' · '}generated {formatDate(data.generated_at)}
        </div>
        {lensToggle}
      </div>

      {/* Top band — Needs Attention. Executive lens swaps in adoption/spend tiles. */}
      <div style={panelTitleStyle}>Needs Attention</div>
      <div style={overviewGridStyle}>
        {showExecRollup ? (
          <>
            <div style={metricCardStyle(criticalCount ? 'danger' : 'default')}>
              <div style={metricLabelStyle}>Risk (crit/warn/ok)</div>
              <div style={metricValueStyle}>{`${fmt(criticalCount)} / ${fmt(warningCount)} / ${fmt(okCount)}`}</div>
            </div>
            <div style={metricCardStyle('default')}>
              <div style={metricLabelStyle}>Total Cost</div>
              <div style={metricValueStyle}>{usd(totalCost)}</div>
            </div>
            <div style={metricCardStyle('default')}>
              <div style={metricLabelStyle}>Outputs (artifacts)</div>
              <div style={metricValueStyle}>{fmt(totalArtifacts)}</div>
            </div>
            <div style={metricCardStyle('default')}>
              <div style={metricLabelStyle}>Adoption (inputs / LLM)</div>
              <div style={metricValueStyle}>{`${fmt(totalInputs)} / ${fmt(totalLlm)}`}</div>
            </div>
            <div style={metricCardStyle(unmatchedCost ? 'danger' : 'default')}>
              <div style={metricLabelStyle}>Unmatched Cost</div>
              <div style={metricValueStyle}>{usd(unmatchedCost)}</div>
            </div>
          </>
        ) : (
          <>
            <div style={metricCardStyle(criticalCount ? 'danger' : 'default')}>
              <div style={metricLabelStyle}>Critical Sessions</div>
              <div style={metricValueStyle}>{fmt(criticalCount)}</div>
            </div>
            <div style={metricCardStyle(warningCount ? 'danger' : 'default')}>
              <div style={metricLabelStyle}>Warning Sessions</div>
              <div style={metricValueStyle}>{fmt(warningCount)}</div>
            </div>
            <div style={metricCardStyle(staleWorkerCount ? 'danger' : 'default')}>
              <div style={metricLabelStyle}>Failed Workers</div>
              <div style={metricValueStyle}>{fmt(staleWorkerCount)}</div>
            </div>
            <div style={metricCardStyle(unmatchedCost ? 'danger' : 'default')}>
              <div style={metricLabelStyle}>Unmatched Cost</div>
              <div style={metricValueStyle}>{usd(unmatchedCost)}</div>
            </div>
            <div style={metricCardStyle(attributionGaps.length ? 'danger' : 'default')}>
              <div style={metricLabelStyle}>Attribution Gaps</div>
              <div style={metricValueStyle}>{fmt(attributionGaps.length)}</div>
            </div>
          </>
        )}
      </div>

      {/* Funnel — INDEPENDENT per-stage tallies (NOT a monotonic drop-off). */}
      <div style={tableWrapStyle}>
        <div style={panelTitleStyle}>Flow Stages (independent per-stage tallies)</div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 1, padding: 12 }}>
          {stages.length === 0 ? (
            <div style={emptyStateStyle}>No stage data.</div>
          ) : (
            stages.map((st, index) => (
              <div
                key={rowKey('funnel-stage', index, st.stage)}
                style={{
                  flex: '1 1 110px',
                  minWidth: 100,
                  padding: '10px 12px',
                  borderRight: index < stages.length - 1 ? '1px solid #2a3540' : 'none',
                  textAlign: 'center',
                }}
              >
                <div style={metricLabelStyle}>{FUNNEL_LABELS[st.stage] || st.stage}</div>
                <div style={{ ...metricValueStyle, fontSize: 20 }}>{fmt(st.count)}</div>
              </div>
            ))
          )}
        </div>
      </div>

      {isEmpty ? (
        <div style={emptyStateStyle}>
          No sessions, IP flow, or attribution gaps in range. Nothing needs action.
        </div>
      ) : (
        <>
          {/* Main split: triage table (left/center) + detail panel (right). */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: selected ? 'minmax(0, 1.7fr) minmax(280px, 1fr)' : 'minmax(0, 1fr)',
              gap: 14,
              alignItems: 'start',
            }}
          >
            <div style={tableWrapStyle}>
              <div style={panelTitleStyle}>Sessions ({sessions.length})</div>
              <table style={tableStyle}>
                <thead>
                  <tr>
                    <th style={thStyle}>Risk</th>
                    <th style={thStyle}>Session</th>
                    <th style={thStyle}>User</th>
                    <th style={thStyle}>IP</th>
                    <th style={thStyle}>Workflow</th>
                    <th style={thStyle}>Flow State</th>
                    <th style={thStyle}>Inputs</th>
                    <th style={thStyle}>LLM / Cost</th>
                    <th style={thStyle}>Worker Status</th>
                    <th style={thStyle}>Artifacts</th>
                    <th style={thStyle}>Age</th>
                    <th style={thStyle}>Next Action</th>
                    {showAttribution ? <th style={thStyle}>Attribution</th> : null}
                  </tr>
                </thead>
                <tbody>
                  {sessions.length === 0 ? (
                    <tr>
                      <td colSpan={showAttribution ? 13 : 12} style={{ ...tdStyle, ...emptyStateStyle }}>
                        No sessions in range.
                      </td>
                    </tr>
                  ) : (
                    sessions.map((s, index) => {
                      const sid = String(s.session_id || s.session_uid || '');
                      const isSel = selectedId !== null && (
                        String(s.session_id) === selectedId || String(s.session_uid) === selectedId
                      );
                      return (
                        <tr
                          key={rowKey('session-flow', index, s.session_id, s.session_uid)}
                          onClick={() => setSelectedId(sid)}
                          style={{ cursor: 'pointer', background: isSel ? 'rgba(130,170,255,0.10)' : undefined }}
                        >
                          <td style={tdStyle}>
                            <span style={statusPillStyle(s.risk_level)}>{s.risk_level || '—'}</span>
                          </td>
                          <td style={tdStyle}>
                            {s.title || shortId(s.session_uid || s.session_id)}
                            {s.namespace ? (
                              <div style={{ opacity: 0.65, fontSize: 11 }}>{s.namespace}</div>
                            ) : null}
                            {showRawIds ? (
                              <div style={{ opacity: 0.5, fontSize: 10 }}>{s.session_uid || s.session_id}</div>
                            ) : null}
                          </td>
                          <td style={tdStyle}>{s.username || (showRawIds ? s.user_id : null) || '—'}</td>
                          <td style={tdStyle}>{s.ip || '—'}</td>
                          <td style={tdStyle}>{s.workflow || '—'}</td>
                          <td style={tdStyle}>{s.flow_state || '—'}</td>
                          <td style={tdStyle}>{fmt(s.input_count)}</td>
                          <td style={tdStyle}>{`${fmt(s.llm_attempts)} · ${usd(s.cost_usd)}`}</td>
                          <td style={tdStyle}>{workerStatusText(s)}</td>
                          <td style={tdStyle}>{fmt(s.artifact_count)}</td>
                          <td style={tdStyle}>{ageText(s)}</td>
                          <td style={tdStyle}>{s.next_action || '—'}</td>
                          {showAttribution ? (
                            <td style={tdStyle}>
                              {s.attribution_confidence || '—'}
                              {s.missing_reason ? (
                                <div style={{ opacity: 0.65, fontSize: 11 }}>{s.missing_reason}</div>
                              ) : null}
                              {s.risk_reason ? (
                                <div style={{ opacity: 0.5, fontSize: 10 }}>{s.risk_reason}</div>
                              ) : null}
                            </td>
                          ) : null}
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>

            {selected ? (
              <div style={tableWrapStyle}>
                <div style={{ ...panelTitleStyle, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span>Session Detail</span>
                  <button
                    type="button"
                    style={{ ...tabStyle(false), padding: '2px 8px' }}
                    onClick={() => setSelectedId(null)}
                  >
                    Close
                  </button>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 14, padding: 14 }}>
                  <DetailSection title="Session Identity">
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                      <div>
                        <span style={statusPillStyle(selected.risk_level)}>{selected.risk_level || '—'}</span>
                        {' '}
                        {selected.title || shortId(selected.session_uid || selected.session_id)}
                      </div>
                      <div style={mutedSmallStyle}>namespace: {selected.namespace || '—'}</div>
                      <div style={mutedSmallStyle}>
                        user: {selected.username || selected.user_id || '—'} · ip: {selected.ip || '—'} · workflow: {selected.workflow || '—'}
                      </div>
                      <div style={mutedSmallStyle}>flow state: {selected.flow_state || '—'} · age: {ageText(selected)}</div>
                      {selected.next_action ? (
                        <div style={mutedSmallStyle}>next action: {selected.next_action}</div>
                      ) : null}
                      {showRawIds ? (
                        <div style={mutedSmallStyle}>
                          session_id: {selected.session_id || '—'} · session_uid: {selected.session_uid || '—'} · ip_id: {selected.ip_id || '—'}
                        </div>
                      ) : null}
                    </div>
                  </DetailSection>

                  <DetailSection title="Input Metrics">
                    <div style={overviewGridStyle}>
                      <DetailMetric label="Inputs" value={fmt(selected.input_count)} />
                      <DetailMetric label="Chars" value={fmt(selected.input_chars)} />
                      <DetailMetric label="Tokens (est)" value={fmt(selected.input_tokens_est)} />
                    </div>
                  </DetailSection>

                  <DetailSection title="LLM Metrics">
                    <div style={overviewGridStyle}>
                      <DetailMetric label="Attempts" value={fmt(selected.llm_attempts)} />
                      <DetailMetric label="Success" value={fmt(selected.llm_success)} />
                      <DetailMetric label="Errors" value={fmt(selected.llm_errors)} />
                      <DetailMetric label="Cost" value={usd(selected.cost_usd)} />
                      <DetailMetric label="Tokens in/out" value={`${fmt(selected.tokens_input)} / ${fmt(selected.tokens_output)}`} />
                      <DetailMetric label="Tokens reasoning" value={fmt(selected.tokens_reasoning)} />
                    </div>
                  </DetailSection>

                  <DetailSection title="Worker Timeline">
                    <div style={overviewGridStyle}>
                      <DetailMetric label="Worker runs" value={fmt(selected.worker_runs)} />
                      <DetailMetric label="Active" value={fmt(selected.active_workers)} />
                      <DetailMetric label="Failed" value={fmt(selected.failed_workers)} />
                      <DetailMetric label="Workflow runs" value={fmt(selected.workflow_runs)} />
                      <DetailMetric label="Workflow errors" value={fmt(selected.workflow_errors)} />
                    </div>
                    <div style={mutedSmallStyle}>{workerStatusText(selected)}</div>
                  </DetailSection>

                  <DetailSection title="IP Provenance">
                    {(() => {
                      const ipRow = ipFlow.find(
                        (r) => String(r.ip_id) === String(selected.ip_id)
                          || (selected.ip && String(r.ip) === String(selected.ip)),
                      );
                      if (!ipRow) return <div style={mutedSmallStyle}>No IP provenance for this session.</div>;
                      return (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                          <div style={mutedSmallStyle}>ip: {ipRow.ip || '—'} ({ipRow.source_confidence || '—'})</div>
                          <div style={mutedSmallStyle}>created by: {ipRow.created_by_user_id || '—'} · source: {ipRow.source_type || '—'}</div>
                          <div style={mutedSmallStyle}>created at: {formatDate(ipRow.ip_created_at)}</div>
                          {showRawIds ? (
                            <div style={mutedSmallStyle}>source session: {ipRow.source_session_id || '—'}</div>
                          ) : null}
                        </div>
                      );
                    })()}
                  </DetailSection>

                  <DetailSection title="Artifacts / Outcomes">
                    <div style={overviewGridStyle}>
                      <DetailMetric label="Artifacts" value={fmt(selected.artifact_count)} />
                      <DetailMetric label="Flow state" value={selected.flow_state || '—'} />
                    </div>
                  </DetailSection>

                  <DetailSection title="Attribution / Confidence">
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                      <div style={mutedSmallStyle}>
                        confidence: {selected.attribution_confidence || '—'}
                        {selected.missing_reason ? ` · reason: ${selected.missing_reason}` : ''}
                      </div>
                      {selected.risk_reason ? (
                        <div style={mutedSmallStyle}>risk reason: {selected.risk_reason}</div>
                      ) : null}
                      {attributionGaps.length ? (
                        <div style={mutedSmallStyle}>{attributionGaps.length} fleet-level gap(s) — see IP / gaps below.</div>
                      ) : (
                        <div style={mutedSmallStyle}>No fleet-level attribution gaps.</div>
                      )}
                    </div>
                  </DetailSection>
                </div>
              </div>
            ) : null}
          </div>

          {/* IP section: creation/provenance + per-IP worker/cost/outcome. */}
          <div style={tableWrapStyle}>
            <div style={panelTitleStyle}>IP Flow ({ipFlow.length})</div>
            <table style={tableStyle}>
              <thead>
                <tr>
                  <th style={thStyle}>Risk</th>
                  <th style={thStyle}>IP</th>
                  <th style={thStyle}>Created By / Source</th>
                  <th style={thStyle}>Created At</th>
                  <th style={thStyle}>Sessions</th>
                  <th style={thStyle}>Workflows</th>
                  <th style={thStyle}>Workers</th>
                  <th style={thStyle}>LLM / Cost</th>
                  <th style={thStyle}>Artifacts</th>
                  <th style={thStyle}>Problems</th>
                  {showAttribution ? <th style={thStyle}>Provenance</th> : null}
                </tr>
              </thead>
              <tbody>
                {ipFlow.length === 0 ? (
                  <tr>
                    <td colSpan={showAttribution ? 11 : 10} style={{ ...tdStyle, ...emptyStateStyle }}>
                      No IP flow in range.
                    </td>
                  </tr>
                ) : (
                  ipFlow.map((r, index) => (
                    <tr key={rowKey('ip-flow', index, r.ip_id, r.ip)}>
                      <td style={tdStyle}>
                        <span style={statusPillStyle(r.risk_level)}>{r.risk_level || '—'}</span>
                      </td>
                      <td style={tdStyle}>
                        {r.ip || shortId(r.ip_id)}
                        {showRawIds ? <div style={{ opacity: 0.5, fontSize: 10 }}>{r.ip_id}</div> : null}
                      </td>
                      <td style={tdStyle}>
                        {r.created_by_user_id || '—'}
                        {r.source_type ? <div style={{ opacity: 0.65, fontSize: 11 }}>{r.source_type}</div> : null}
                      </td>
                      <td style={tdStyle}>{formatDate(r.ip_created_at)}</td>
                      <td style={tdStyle}>{`${fmt(r.sessions)} (${fmt(r.active_sessions)} active)`}</td>
                      <td style={tdStyle}>{fmt(r.workflows)}</td>
                      <td style={tdStyle}>{fmt(r.worker_runs)}</td>
                      <td style={tdStyle}>{`${fmt(r.llm_attempts)} · ${usd(r.cost_usd)}`}</td>
                      <td style={tdStyle}>{fmt(r.artifact_count)}</td>
                      <td style={tdStyle}>{fmt(r.problem_count)}</td>
                      {showAttribution ? <td style={tdStyle}>{r.source_confidence || '—'}</td> : null}
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Attribution gaps — visible in builder/team_lead; executive hides raw gap rows. */}
          {!showExecRollup && attributionGaps.length ? (
            <div style={tableWrapStyle}>
              <div style={panelTitleStyle}>Attribution Gaps ({attributionGaps.length})</div>
              <table style={tableStyle}>
                <thead>
                  <tr>
                    <th style={thStyle}>Kind</th>
                    {showRawIds ? <th style={thStyle}>Session ID</th> : null}
                    <th style={thStyle}>LLM Attempts</th>
                    <th style={thStyle}>Cost</th>
                    <th style={thStyle}>Confidence</th>
                    <th style={thStyle}>Reason</th>
                  </tr>
                </thead>
                <tbody>
                  {attributionGaps.map((g, index) => (
                    <tr key={rowKey('attr-gap', index, g.session_id, g.kind)}>
                      <td style={tdStyle}>{g.kind || g.category || '—'}</td>
                      {showRawIds ? <td style={tdStyle}>{g.session_id || '—'}</td> : null}
                      <td style={tdStyle}>{fmt(g.llm_attempts ?? g.count)}</td>
                      <td style={tdStyle}>{usd(g.cost_usd)}</td>
                      <td style={tdStyle}>{g.confidence || '—'}</td>
                      <td style={tdStyle}>{g.missing_reason || '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}

          {/* Builder-only diagnostics: needs_attention raw entries + rollup lag / route source. */}
          {showAttribution && needsAttention.length ? (
            <div style={tableWrapStyle}>
              <div style={panelTitleStyle}>Needs Attention — raw entries ({needsAttention.length})</div>
              <table style={tableStyle}>
                <thead>
                  <tr>
                    <th style={thStyle}>Session / Category</th>
                    <th style={thStyle}>Risk / Kind</th>
                    <th style={thStyle}>Reason</th>
                    <th style={thStyle}>Cost</th>
                  </tr>
                </thead>
                <tbody>
                  {needsAttention.map((n, index) => (
                    <tr key={rowKey('needs-attn', index, n.session_id, n.category)}>
                      <td style={tdStyle}>{n.session_id || n.category || '—'}</td>
                      <td style={tdStyle}>{n.risk_level || n.kind || '—'}</td>
                      <td style={tdStyle}>{n.risk_reason || n.missing_reason || '—'}</td>
                      <td style={tdStyle}>{n.cost_usd != null ? usd(n.cost_usd) : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </>
      )}
    </div>
  );
}
