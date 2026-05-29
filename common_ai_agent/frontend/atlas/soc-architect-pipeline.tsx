// soc-architect-pipeline.tsx — pipeline-strip + module-progress helpers for the
// soc-architect.tsx family (TypeScript migration of soc-architect.jsx).
//
// Holds the verification-pipeline globals (PIPELINE_STAGES, PIPELINE_LABEL,
// fullPipeline, PipelineStrip) and ModuleProgressPanel. These were registered
// on `window.*` in soc-architect.jsx and are consumed by the run bar + the
// status grid in the main file (and by other legacy .jsx via window).
//
// Transitional: every `window.X = X` side-effect from the original is preserved
// here in the same order, so legacy .jsx consumers still resolve them.

const g = window as unknown as Record<string, any>;

// Pipeline strip shared by V6 grid + V7 diagram. Same logic as the
// upstream zip; lives here because soc-shared.jsx doesn't ship it.
export const PIPELINE_STAGES = [
  'ssot', 'fl-model', 'cl-model', 'equivalence', 'rtl', 'lint', 'tb',
  'sim', 'coverage', 'sim-debug', 'syn', 'sta', 'pnr', 'sta-post', 'goal-audit',
];
export const PIPELINE_LABEL: Record<string, string> = {
  ssot: 'SSOT',
  'fl-model': 'FL',
  'cl-model': 'CL',
  equivalence: 'EQUIV',
  rtl: 'RTL',
  lint: 'LINT',
  tb: 'TB',
  sim: 'SIM',
  coverage: 'COV',
  'sim-debug': 'DBG',
  syn: 'SYN',
  sta: 'STA',
  pnr: 'PNR',
  'sta-post': 'PSTA',
  'goal-audit': 'AUDIT',
};
export function fullPipeline(status: any, modId: string): Record<string, string> {
  const s = status || {};
  const full: Record<string, string> = {
    ssot: s.ssot || 'pending',
    'fl-model': s.fl_model || s.functional_model || 'pending',
    'cl-model': s.cl_model || s.cycle_model || 'pending',
    equivalence: s.equivalence_goals || 'pending',
    rtl: s.rtl || 'pending',
    lint: s.lint || 'pending',
    tb: s.tb || 'pending',
    sim: s.sim || 'pending',
    coverage: s.coverage || 'pending',
    'sim-debug': s['sim-debug'] || s.sim_debug || (s.sim === 'ok' ? 'ok' : 'pending'),
    syn: s.syn || 'pending',
    sta: s.sta || 'pending',
    pnr: s.pnr || 'pending',
    'sta-post': s['sta-post'] || s.sta_post || s.signoff || 'pending',
    'goal-audit': s.goal_audit || 'pending',
  };
  const jobs = Array.isArray(window.ATLAS_JOBS) ? window.ATLAS_JOBS : [];
  const stageForWorkflow: Record<string, string> = {
    'ssot-gen': 'ssot',
    'fl-model-gen': 'fl-model',
    'rtl-gen': 'rtl',
    lint: 'lint',
    'tb-gen': 'tb',
    sim: 'sim',
    coverage: 'coverage',
    sim_debug: 'sim-debug',
    syn: 'syn',
    sta: 'sta',
    pnr: 'pnr',
    'sta-post': 'sta-post',
  };
  for (const j of jobs) {
    if (!j || j.ip !== modId) continue;
    const stage = j.stage_id || stageForWorkflow[j.workflow];
    if (!stage || !(stage in full)) continue;
    if (j.status === 'running' || j.status === 'pending') full[stage] = 'run';
    else if (j.status === 'queued') full[stage] = full[stage] === 'pending' ? 'partial' : full[stage];
    else if (j.status === 'completed') full[stage] = 'ok';
    else if (j.status === 'error' || j.status === 'blocked' || j.status === 'cancelled') full[stage] = 'err';
  }
  return full;
}

interface PipelineStripProps {
  status: any;
  modId?: string;
  big?: boolean;
}
export function PipelineStrip({ status, modId, big = false }: PipelineStripProps) {
  const full = g.fullPipeline(status, modId || '');
  return (
    <span className={`pl-strip ${big ? 'pl-strip-lg' : ''}`}>
      {PIPELINE_STAGES.map((s) => (
        <span key={s} className={`pl-dot ${full[s]}`}
              title={`${PIPELINE_LABEL[s]} · ${full[s]}`} />
      ))}
    </span>
  );
}

interface ModuleProgressPanelProps {
  module: any;
}
export function ModuleProgressPanel({ module }: ModuleProgressPanelProps) {
  const p = module?.progress || {};
  const ssot = p.ssot || {};
  const rtl = p.rtl || {};
  const equiv = p.equivalence_goals || {};
  const goalAudit = p.goal_audit || {};
  const lint = p.lint || {};
  const sim = p.sim || {};
  const chipColor = (state: string): string => {
    if (state === 'approved' || state === 'pass') return 'var(--ok)';
    if (state === 'missing' || state === 'fail') return 'var(--err)';
    if (state === 'partial' || state === 'incomplete' || state === 'unknown' || state === 'blocked' || state === 'escalated' || state === 'stale') return 'var(--warn)';
    return 'var(--fg-mute)';
  };
  const Bar = ({ value }: { value: number }) => (
    <span style={{
      display: 'inline-block', width: 78, height: 5, border: '1px solid var(--line)',
      background: 'var(--bg-2)', verticalAlign: 'middle', marginLeft: 6,
    }}>
      <span style={{
        display: 'block', height: '100%', width: `${Math.max(0, Math.min(100, value || 0))}%`,
        background: value >= 100 ? 'var(--ok)' : 'var(--warn)',
      }} />
    </span>
  );
  const Section = ({ title, right, children }: { title: any; right?: any; children?: any }) => (
    <div style={{ borderBottom: '1px solid var(--line)', padding: '8px 10px' }}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6,
        fontFamily: 'var(--mono)', fontSize: 10, letterSpacing: '0.08em',
        textTransform: 'uppercase',
      }}>
        <b>{title}</b>
        <span style={{ flex: 1 }} />
        <span className="mute">{right}</span>
      </div>
      {children}
    </div>
  );
  const ssotSections = Array.isArray(ssot.sections) ? ssot.sections : [];
  const ssotMetrics = ssot.metrics || {};
  const rtlModules = Array.isArray(rtl.modules) ? rtl.modules : [];
  const dv = sim.dv_plan || {};
  const res = sim.results || {};
  const cov = sim.coverage || {};
  const covStatic = cov.static && typeof cov.static === 'object' ? cov.static : {};
  const metricLabel = (m: any): string => {
    if (!m || typeof m !== 'object') return '—';
    const pct = m.pct ?? m.percent;
    const hit = m.hit ?? m.covered;
    const total = m.total ?? m.found;
    if (pct != null) return `${pct}%`;
    if (hit != null && total != null) return `${hit}/${total}`;
    return '—';
  };
  const scenarioRows = Array.isArray(dv.scenario_rows) ? dv.scenario_rows : [];
  const escalations = Array.isArray(sim.escalations) ? sim.escalations : [];
  const covCriteria = cov.criteria && typeof cov.criteria === 'object' ? Object.entries(cov.criteria) : [];
  const covLimitations = cov.limitations && typeof cov.limitations === 'object' ? Object.entries(cov.limitations) : [];
  const resultRight = res.check_total != null
    ? `${res.check_pass ?? 0}/${res.check_total} checks · ${res.check_fail ?? 0} fail`
    : `${res.pass || 0}/${res.total || 0} pass · ${res.fail || 0} fail`;
  return (
    <div style={{ background: 'var(--panel)', borderBottom: '1px solid var(--line)' }}>
      <Section title="SSOT" right={`${ssot.approved || 0}/${ssot.total || 0} approved`}>
        <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--fg-mute)', marginBottom: 5 }}>
          {ssot.pct || 0}%<Bar value={ssot.pct || 0} />
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, fontFamily: 'var(--mono)', fontSize: 10, marginBottom: 6 }}>
          <span className="pill">submods {ssotMetrics.submodules ?? 0}</span>
          <span className="pill">params {ssotMetrics.parameters ?? 0}</span>
          <span className="pill">if {ssotMetrics.interfaces ?? 0}</span>
          <span className="pill">ports {ssotMetrics.ports ?? 0}</span>
          <span className="pill">regs {ssotMetrics.registers ?? 0}</span>
          <span className="pill">fsm {ssotMetrics.fsm_states ?? 0}/{ssotMetrics.fsm_transitions ?? 0}</span>
          <span className="pill">dv {ssotMetrics.dv_scenarios ?? 0}</span>
          <span className="pill">cov {ssotMetrics.coverage_goals ?? 0}</span>
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
          {ssotSections.map((s: any) => (
            <span key={s.key} title={`${s.key} · ${s.status}`} style={{
              border: `1px solid ${chipColor(s.status)}`, color: chipColor(s.status),
              padding: '1px 5px', fontSize: 9, fontFamily: 'var(--mono)', borderRadius: 2,
            }}>{s.label}</span>
          ))}
        </div>
      </Section>
      <Section title="FL-vs-RTL Goals" right={`${equiv.passed || 0}/${equiv.total || 0} pass`}>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, fontFamily: 'var(--mono)', fontSize: 10 }}>
          <span style={{ color: chipColor(equiv.status), border: `1px solid ${chipColor(equiv.status)}`, padding: '1px 6px' }}>{equiv.status || 'pending'}</span>
          <span className="pill">generated {equiv.generated || 0}</span>
          <span className="pill">checked {equiv.checked || 0}</span>
          <span className="pill">failed {equiv.failed || 0}</span>
          <span className="pill">blocked {equiv.blocked || 0}</span>
          <span className="pill">untested {equiv.untested || 0}</span>
        </div>
        <div className="mute" style={{ marginTop: 5, fontFamily: 'var(--mono)', fontSize: 10, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {equiv.compare_evidence || equiv.evidence || 'no equivalence goal evidence'}
        </div>
        {equiv.classification_counts && Object.keys(equiv.classification_counts).length > 0 && (
          <div className="mute" style={{ marginTop: 5, fontFamily: 'var(--mono)', fontSize: 10 }}>
            class: {Object.entries(equiv.classification_counts).map(([k, v]) => `${k}:${v}`).join(' · ')}
          </div>
        )}
        {equiv.owner_counts && Object.keys(equiv.owner_counts).length > 0 && (
          <div className="mute" style={{ marginTop: 5, fontFamily: 'var(--mono)', fontSize: 10 }}>
            owner: {Object.entries(equiv.owner_counts).map(([k, v]) => `${k}:${v}`).join(' · ')}
          </div>
        )}
        {Array.isArray(equiv.missing_evidence) && equiv.missing_evidence.length > 0 && (
          <div className="mute" style={{ marginTop: 5, fontFamily: 'var(--mono)', fontSize: 10 }}>
            missing: {equiv.missing_evidence.slice(0, 3).join(', ')}
          </div>
        )}
        {Array.isArray(equiv.stale_evidence) && equiv.stale_evidence.length > 0 && (
          <div className="mute" style={{ marginTop: 5, fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--warn)' }}>
            stale: {equiv.stale_evidence.slice(0, 3).join(', ')}
          </div>
        )}
        {Array.isArray(equiv.failed_goal_ids) && equiv.failed_goal_ids.length > 0 && (
          <div className="mute" style={{ marginTop: 5, fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--warn)' }}>
            failed: {equiv.failed_goal_ids.join(', ')}
          </div>
        )}
        {Array.isArray(equiv.blocked_goal_ids) && equiv.blocked_goal_ids.length > 0 && (
          <div className="mute" style={{ marginTop: 5, fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--warn)' }}>
            blocked: {equiv.blocked_goal_ids.join(', ')}
          </div>
        )}
        {Array.isArray(equiv.untested_goal_ids) && equiv.untested_goal_ids.length > 0 && (
          <div className="mute" style={{ marginTop: 5, fontFamily: 'var(--mono)', fontSize: 10 }}>
            untested: {equiv.untested_goal_ids.join(', ')}
          </div>
        )}
        <div className="mute" style={{ marginTop: 7, fontFamily: 'var(--mono)', fontSize: 10 }}>
          audit <span style={{ color: chipColor(goalAudit.status) }}>{goalAudit.status || 'pending'}</span>
          {' '}· {goalAudit.passed_checks || 0}/{goalAudit.total_checks || 0} checks
          {goalAudit.source ? ` · ${goalAudit.source}` : ' · run /goal-audit'}
        </div>
        {Array.isArray(goalAudit.blockers) && goalAudit.blockers.length > 0 && (
          <div className="mute" style={{ marginTop: 5, fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--warn)' }}>
            audit blockers: {goalAudit.blockers.slice(0, 8).join(', ')}
          </div>
        )}
        {Array.isArray(goalAudit.stale_evidence) && goalAudit.stale_evidence.length > 0 && (
          <div className="mute" style={{ marginTop: 5, fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--warn)' }}>
            audit stale: {goalAudit.stale_evidence.slice(0, 3).join(', ')}
          </div>
        )}
      </Section>
      <Section title="RTL" right={`${rtl.approved || 0}/${rtl.total || 0} modules`}>
        <div style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--fg-mute)', marginBottom: 5 }}>
          {rtl.pct || 0}% · {rtl.filelist || 'no filelist'}<Bar value={rtl.pct || 0} />
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: 4 }}>
          {rtlModules.map((m: any) => (
            <span key={m.file} title={`${m.file}\nlisted=${m.listed} bytes=${m.bytes} placeholder=${m.placeholder}`} style={{
              borderLeft: `2px solid ${chipColor(m.status)}`, background: 'var(--bg-2)',
              padding: '3px 5px', fontSize: 10, fontFamily: 'var(--mono)',
              color: m.status === 'approved' ? 'var(--fg)' : chipColor(m.status),
              overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
            }}>{m.status === 'approved' ? '✓' : m.status === 'missing' ? '✕' : '◐'} {m.name}</span>
          ))}
        </div>
      </Section>
      <Section title="Lint" right={`${lint.errors ?? 0} errors · ${lint.warnings ?? 0} warnings`}>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center', fontFamily: 'var(--mono)', fontSize: 11 }}>
          <span style={{ color: chipColor(lint.status), border: `1px solid ${chipColor(lint.status)}`, padding: '1px 6px' }}>{lint.status || 'unknown'}</span>
          <span className="err">E {lint.errors ?? 0}</span>
          <span className="warn">W {lint.warnings ?? 0}</span>
          <span className="mute">waive {lint.warning_budget ?? 0}</span>
          <span className="mute" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{lint.source || 'no lint log'}</span>
        </div>
      </Section>
      <Section title="SIM · DV" right={resultRight}>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, fontFamily: 'var(--mono)', fontSize: 10 }}>
          <span className="pill">SSOT scenarios {dv.scenarios || 0}</span>
          <span className="pill">scoreboard {dv.scoreboard_checks ?? '—'}</span>
          <span className="pill">coverage goals {dv.coverage_goals || 0}</span>
          <span className="pill">TB tests {sim.implemented_tests || 0}</span>
          <span className="pill">xunit {res.pass || 0}/{res.total || 0}</span>
          <span style={{ color: chipColor(cov.status), border: `1px solid ${chipColor(cov.status)}`, padding: '1px 6px' }}>coverage {cov.status || 'unknown'}</span>
          <span className="pill">functional cov {cov.functional_pct ?? '—'}%</span>
          <span className="pill">line {metricLabel(covStatic.lines)}</span>
          <span className="pill">branch {metricLabel(covStatic.branches)}</span>
          <span className="pill">fsm {metricLabel(covStatic.fsm_state)}</span>
        </div>
        {scenarioRows.length > 0 && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 6 }}>
            {scenarioRows.map((r: any) => {
              const esc = r.escalation && typeof r.escalation === 'object' ? r.escalation : null;
              const title = [
                `${r.id || ''} ${r.name || ''}`.trim(),
                `status=${r.status || 'pending'}`,
                r.expected ? `expected=${r.expected}` : '',
                esc ? `escalation=${esc.file || esc.module || ''} ${esc.hypothesis || esc.fix || esc.expected || ''}` : '',
              ].filter(Boolean).join('\n');
              return (
                <span key={r.id || r.name} title={title} style={{
                  border: `1px solid ${chipColor(r.status)}`, color: chipColor(r.status),
                  padding: '1px 5px', fontSize: 9, fontFamily: 'var(--mono)', borderRadius: 2,
                }}>{r.id || r.name}: {r.status || 'pending'}</span>
              );
            })}
          </div>
        )}
        {escalations.length > 0 && (
          <div style={{ marginTop: 6, fontSize: 10, color: 'var(--warn)', lineHeight: 1.4 }}>
            {escalations.slice(0, 3).map((e: any, idx: number) => (
              <div key={`${e.test_id || e.scenario || idx}`}>[{e.test_id || e.scenario || `E${idx + 1}`}] {e.module || e.file || 'escalated'}: {e.expected || e.fix || e.hypothesis || 'see coverage.json'}</div>
            ))}
            {escalations.length > 3 && <div className="mute">+{escalations.length - 3} more escalations</div>}
          </div>
        )}
        {covCriteria.length > 0 && (
          <div style={{ marginTop: 5, fontSize: 10, color: 'var(--fg-mute)', lineHeight: 1.4 }}>
            {covCriteria.map(([k, v]) => <div key={k}><b>{k}</b>: {String(v)}</div>)}
          </div>
        )}
        {covLimitations.length > 0 && (
          <div style={{ marginTop: 5, fontSize: 10, color: 'var(--warn)', lineHeight: 1.4 }}>
            {covLimitations.map(([k, v]) => <div key={k}><b>{k}</b>: {String(v)}</div>)}
          </div>
        )}
      </Section>
    </div>
  );
}

// ── Transitional bridge: same window.* registrations as soc-architect.jsx,
// in the same order, so legacy .jsx + the rest of this family resolve them. ──
window.PIPELINE_STAGES = PIPELINE_STAGES;
g.PIPELINE_LABEL = PIPELINE_LABEL;
g.fullPipeline = fullPipeline;
g.PipelineStrip = PipelineStrip;
g.ModuleProgressPanel = ModuleProgressPanel;
