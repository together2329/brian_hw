// progress-todo-panels.tsx — TypeScript migration of progress-todo-panels.jsx
// (Phase 23 refactor: ProgressPanel (461L) + TodoPanel (426L) extracted from
// workspace-panels.jsx so the latter drops under 1000. Both are sidebar panels
// rendered by Workspace.)
//
// Sub-1000 split: the shared window-glue + loose data shapes now live in
// ./progress-todo-globals, and TodoPanel now lives in ./progress-todo-todo.
// This file keeps ProgressPanel and re-exports TodoPanel so the public contract
// (importable ProgressPanel + TodoPanel) is unchanged. The window.X = X bridges
// still run (window.ProgressPanel here, window.TodoPanel in ./progress-todo-todo)
// so not-yet-migrated .jsx consumers keep resolving window.ProgressPanel /
// window.TodoPanel.
import { useReducer, useState, useEffect, Fragment, type ReactNode } from 'react';
import {
  w,
  type AtlasProgressData,
  type ProgressModule,
} from './progress-todo-globals';
import { TodoPanel } from './progress-todo-todo';

const ProgressPanel = (): ReactNode => {
  const [, bump] = useReducer((x: number) => x + 1, 0);
  const [moduleId, setModuleId] = useState('');

  useEffect(() => {
    const h = (ev: Event) => {
      const detail = (ev as CustomEvent).detail;
      if (!detail || ['PROGRESS', 'SCOPE_PATH', 'SSOT_FILES', 'TODOS'].includes(detail)) bump();
    };
    window.addEventListener('atlas-data-changed', h);
    if (w.atlasData && w.atlasData.refreshProgress) w.atlasData.refreshProgress();
    return () => window.removeEventListener('atlas-data-changed', h);
  }, []);

  const data: AtlasProgressData = w.ATLAS_PROGRESS || {};
  const modules: ProgressModule[] = Array.isArray(data.modules) ? data.modules : [];
  // Active IP comes from the top-bar selector (single source of truth).
  // We derive it from ACTIVE_SESSION and pivot the panel onto that
  // module — no internal IP picker, since the user explicitly asked
  // for "IP는 맨 위에서 선택, 다른 곳에선 표시만".
  const _activeIp = (() => {
    const ns = String(w.ACTIVE_SESSION || '').split('/').filter(Boolean);
    if (ns.length >= 2) return ns[1];
    return '';
  })();
  const selected = modules.find(m => (m.id || m.name) === _activeIp)
    || modules.find(m => m.id === moduleId)
    || data.selected
    || modules[0]
    || null;

  useEffect(() => {
    if (selected && selected.id && selected.id !== moduleId) setModuleId(selected.id);
  }, [selected && selected.id]);

  const progress = (selected && selected.progress) || {};
  const status = (selected && selected.status) || {};
  const details: Record<string, unknown> = (selected && selected.status_detail) || {};
  const signoff: Record<string, unknown> = (selected && selected.signoff) || {};
  const blockers = Array.isArray(signoff.blockers) ? signoff.blockers : [];
  const ownership: Record<string, unknown> = (signoff.ownership as Record<string, unknown>) || {};
  const artifact: Record<string, unknown> = (selected && selected.artifact_status) || {};
  const artifactDetails: Record<string, unknown> = (selected && selected.artifact_detail) || {};
  const req = (progress.req as Record<string, unknown>) || {};
  const ssot = (progress.ssot as Record<string, unknown>) || {};
  const flModel = (progress.fl_model as Record<string, unknown>) || {};
  const flDecomp = (progress.fl_decomp as Record<string, unknown>) || {};
  const fcovPlan = (progress.fcov_plan as Record<string, unknown>) || {};
  const equiv = (progress.equivalence_goals as Record<string, unknown>) || {};
  const goalAudit = (progress.goal_audit as Record<string, unknown>) || {};
  const rtl = (progress.rtl as Record<string, unknown>) || {};
  const compile = (progress.compile as Record<string, unknown>) || {};
  const lint = (progress.lint as Record<string, unknown>) || {};
  const sim = (progress.sim as Record<string, unknown>) || {};
  const dv = (sim.dv_plan as Record<string, unknown>) || {};
  const results = (sim.results as Record<string, unknown>) || {};
  const coverage = (sim.coverage as Record<string, unknown>) || {};

  const pct = (obj: unknown) => Math.max(0, Math.min(100, Number(obj && (obj as Record<string, unknown>).pct) || 0));
  const stateColor = (s: unknown) => {
    const v = String(s || '').toLowerCase();
    if (['ok', 'pass', 'approved', 'done'].includes(v)) return 'var(--ok)';
    if (['fail', 'err', 'error', 'rejected'].includes(v)) return 'var(--err)';
    if (['partial', 'planned', 'active', 'blocked', 'stale'].includes(v)) return 'var(--warn)';
    return 'var(--fg-mute)';
  };
  const pill = (label: string, value: unknown) => (
    <span style={{
      border: `1px solid ${stateColor(value)}`,
      color: stateColor(value),
      borderRadius: 2,
      padding: '1px 6px',
      fontSize: 10,
      fontFamily: 'var(--mono)',
      whiteSpace: 'nowrap',
    }}>{label}: {(value as ReactNode) || 'pending'}</span>
  );
  const Bar = ({ label, done, total, value, color = 'var(--ok)' }: {
    label?: ReactNode;
    done?: number;
    total?: number;
    value?: number | null;
    color?: string;
  }) => {
    const p = value != null ? Math.max(0, Math.min(100, Number(value) || 0))
      : (total ? Math.round(100 * (done || 0) / total) : 0);
    return (
      <div style={{ marginBottom: 8 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, fontFamily: 'var(--mono)', color: 'var(--fg-mute)', marginBottom: 3 }}>
          <span>{label}</span>
          <span>{done != null && total != null ? `${done}/${total}` : `${p}%`}</span>
        </div>
        <div style={{ height: 5, background: 'var(--bg-3)', border: '1px solid var(--line)', borderRadius: 2, overflow: 'hidden' }}>
          <div style={{ height: '100%', width: `${p}%`, background: color }} />
        </div>
      </div>
    );
  };
  const Section = ({ title, right, children }: {
    title?: ReactNode;
    right?: ReactNode;
    children?: ReactNode;
  }) => (
    <div style={{ borderBottom: '1px solid var(--line)', padding: '10px 12px' }}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8,
        fontSize: 10, fontFamily: 'var(--mono)', letterSpacing: '0.08em',
        textTransform: 'uppercase',
      }}>
        <span style={{ color: 'var(--fg)', fontWeight: 700 }}>{title}</span>
        <span style={{ flex: 1 }} />
        {right && <span className="mute" style={{ letterSpacing: 0, textTransform: 'none' }}>{right}</span>}
      </div>
      {children}
    </div>
  );
  const repairRtl = () => {
    const ip = selected && (selected.id || selected.name || selected.ip_dir || '');
    if (!ip || !w.backend) return;
    w.backend.send({ type: 'prompt', text: `/repair-rtl ${ip}` });
  };

  if (!selected) {
    return (
      <div className="code" style={{ flex: 1, padding: '14px 16px', overflow: 'auto', color: 'var(--fg-mute)', fontSize: 12 }}>
        # No SSOT-backed IP progress found.<br />
        # Create or select a leaf SSOT YAML, then run the ATLAS SSOT → RTL → TB → sim_debug flow.
      </div>
    );
  }

  const sections = Array.isArray(ssot.sections) ? ssot.sections : [];
  const rtlModules = Array.isArray(rtl.modules) ? rtl.modules : [];
  const scenarios = Array.isArray(dv.scenario_rows) ? dv.scenario_rows : [];
  const criteria = coverage.criteria && typeof coverage.criteria === 'object' ? coverage.criteria as Record<string, unknown> : {};
  const limitations = coverage.limitations && typeof coverage.limitations === 'object' ? coverage.limitations as Record<string, unknown> : {};
  const staticCov = coverage.static && typeof coverage.static === 'object' ? coverage.static as Record<string, unknown> : {};
  const ownershipRows = [
    'req', 'ssot', 'fl_model', 'fl_decomp', 'fcov_plan', 'equivalence_goals',
    'goal_audit', 'rtl', 'lint', 'tb', 'sim_debug', 'coverage', 'signoff',
  ].map(k => ownership[k]).filter(Boolean) as Record<string, unknown>[];

  return (
    <div style={{ flex: 1, overflow: 'auto', fontSize: 11 }}>
      <div style={{ padding: '9px 12px', borderBottom: '1px solid var(--line)', background: 'var(--bg-2)' }}>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center', marginBottom: 8 }}>
          {/* Display-only IP label — IP selection happens at the top-bar
              dir-switcher (single source of truth). Showing a duplicate
              picker here lets the panel drift out of sync from the
              actual active IP. Click hint suggests where to switch. */}
          <span
            title={`Active IP — switch from the top-bar IP picker.\n${selected.ssot_path || ''}`}
            style={{
              flex: 1, minWidth: 0,
              padding: '4px 8px',
              background: 'var(--bg-3)',
              color: 'var(--fg)',
              border: '1px solid var(--line)',
              borderRadius: 2,
              fontFamily: 'var(--mono)', fontSize: 'var(--ui-control-font-size)',
              whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
              cursor: 'default', userSelect: 'none',
            }}
          >
            {selected.label || selected.name || selected.id || '(no IP)'}
          </span>
          <span className="mute" title={selected.ssot_path || ''}>{selected.kind || 'ip'}</span>
        </div>
        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap' }}>
          {pill('signoff', status.signoff)}
          {pill('req', status.req)}
          {pill('ssot', status.ssot)}
          {pill('fl', status.fl_model)}
          {pill('decomp', status.fl_decomp)}
          {pill('fcov plan', status.fcov_plan)}
          {pill('equiv', status.equivalence_goals)}
          {pill('audit', status.goal_audit)}
          {pill('rtl', status.rtl)}
          {pill('lint', status.lint)}
          {pill('tb', status.tb)}
          {pill('simdbg', status.sim_debug || status.sim)}
          {pill('cov', status.coverage)}
        </div>
        <div className="mute" style={{ marginTop: 6, fontFamily: 'var(--mono)', fontSize: 10, lineHeight: 1.4 }}>
          strict gate: REQ + SSOT + executable FL model + decomposition + FCOV plan + RTL + lint + FL-vs-RTL sim + coverage + goal audit
        </div>
        {blockers.length > 0 && (
          <div style={{ marginTop: 6, color: 'var(--warn)', fontFamily: 'var(--mono)', fontSize: 10, lineHeight: 1.35 }}>
            blocked by: {blockers.slice(0, 4).join(' · ')}
          </div>
        )}
        <div style={{ marginTop: 8, display: 'flex', gap: 6, alignItems: 'center' }}>
          <button
            onClick={repairRtl}
            disabled={!selected || !selected.id}
            title="Queue rtl-gen repair from current compile/lint/SSOT evidence"
            style={{
              background: 'var(--bg-3)',
              color: 'var(--accent)',
              border: '1px solid var(--accent)',
              borderRadius: 2,
              padding: '3px 7px',
              fontFamily: 'var(--mono)',
              fontSize: 10,
              cursor: 'pointer',
            }}
          >
            repair rtl-gen
          </button>
          <span className="mute" style={{ fontFamily: 'var(--mono)', fontSize: 10 }}>
            uses SSOT + rtl_compile.json + dut_lint.json
          </span>
        </div>
      </div>

      <Section title="Artifact Evidence" right="not signoff">
        <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginBottom: 8 }}>
          {pill('req', artifact.req)}
          {pill('ssot', artifact.ssot)}
          {pill('fl', artifact.fl_model)}
          {pill('decomp', artifact.fl_decomp)}
          {pill('fcov plan', artifact.fcov_plan)}
          {pill('equiv', artifact.equivalence_goals)}
          {pill('audit', artifact.goal_audit)}
          {pill('rtl', artifact.rtl)}
          {pill('tb', artifact.tb)}
          {pill('simdbg', artifact.sim_debug)}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '62px 1fr', rowGap: 4, columnGap: 8, fontFamily: 'var(--mono)' }}>
          <span className="mute">req</span><span className="trunc" title={(artifactDetails.req as string) || ''}>{(artifactDetails.req as ReactNode) || 'no requirement evidence'}</span>
          <span className="mute">ssot</span><span className="trunc" title={(artifactDetails.ssot as string) || ''}>{(artifactDetails.ssot as ReactNode) || 'no artifact evidence'}</span>
          <span className="mute">fl</span><span className="trunc" title={(artifactDetails.fl_model as string) || ''}>{(artifactDetails.fl_model as ReactNode) || 'no executable FL model'}</span>
          <span className="mute">decomp</span><span className="trunc" title={(artifactDetails.fl_decomp as string) || ''}>{(artifactDetails.fl_decomp as ReactNode) || 'no FL decomposition'}</span>
          <span className="mute">fcov</span><span className="trunc" title={(artifactDetails.fcov_plan as string) || ''}>{(artifactDetails.fcov_plan as ReactNode) || 'no FCOV plan'}</span>
          <span className="mute">equiv</span><span className="trunc" title={(artifactDetails.equivalence_goals as string) || ''}>{(artifactDetails.equivalence_goals as ReactNode) || 'no equivalence goals'}</span>
          <span className="mute">audit</span><span className="trunc" title={(artifactDetails.goal_audit as string) || ''}>{(artifactDetails.goal_audit as ReactNode) || 'no goal audit'}</span>
          <span className="mute">rtl</span><span className="trunc" title={(artifactDetails.rtl as string) || ''}>{(artifactDetails.rtl as ReactNode) || 'no artifact evidence'}</span>
          <span className="mute">tb</span><span className="trunc" title={(artifactDetails.tb as string) || ''}>{(artifactDetails.tb as ReactNode) || 'no artifact evidence'}</span>
          <span className="mute">simdbg</span><span className="trunc" title={(artifactDetails.sim_debug as string) || ''}>{(artifactDetails.sim_debug as ReactNode) || 'no artifact evidence'}</span>
        </div>
      </Section>

      <Section title="Loop Owner & Next Action" right="LLM loop / human gate">
        {ownershipRows.length ? (
          <div style={{ display: 'grid', gridTemplateColumns: '58px 68px 1fr', rowGap: 5, columnGap: 8, fontFamily: 'var(--mono)', fontSize: 10 }}>
            {ownershipRows.map(row => (
              <Fragment key={row.stage as string}>
                <span className="mute">{String(row.stage || '').replace('_', ' ')}</span>
                <span style={{ color: row.owner === 'human gate' ? 'var(--warn)' : stateColor(row.status) }}>
                  {(row.owner as ReactNode) || 'LLM loop'}
                </span>
                <span
                  className="trunc"
                  title={[
                    `status: ${row.status || 'pending'}`,
                    `validator: ${row.validator || ''}`,
                    `evidence: ${row.evidence || ''}`,
                    `blocker: ${row.blocker || ''}`,
                    `next: ${row.next_action || ''}`,
                  ].join('\n')}
                >
                  {(row.next_action as ReactNode) || 'inspect stage evidence'}
                </span>
              </Fragment>
            ))}
          </div>
        ) : (
          <div className="mute" style={{ fontFamily: 'var(--mono)', fontSize: 10 }}>
            ownership data missing from ATLAS progress response
          </div>
        )}
      </Section>

      <Section title="SSOT Sections" right={selected.ssot_path as ReactNode}>
        <Bar label="approved sections" done={(ssot.approved as number) || 0} total={(ssot.total as number) || 0} value={pct(ssot)} />
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 4 }}>
          {sections.map((s: Record<string, unknown>) => (
            <div key={s.key as string} title={s.key as string} style={{
              display: 'flex', alignItems: 'center', gap: 5, minWidth: 0,
              color: s.status === 'approved' ? 'var(--fg)' : 'var(--fg-mute)',
              fontFamily: 'var(--mono)', fontSize: 10,
            }}>
              <span style={{ color: stateColor(s.status), width: 10 }}>{s.status === 'approved' ? '✓' : '○'}</span>
              <span className="trunc">{(s.label as ReactNode) || (s.key as ReactNode)}</span>
            </div>
          ))}
        </div>
        {!!ssot.metrics && (
          <div className="mute" style={{ marginTop: 8, lineHeight: 1.5, fontFamily: 'var(--mono)' }}>
            submods {(ssot.metrics as Record<string, unknown>).submodules as ReactNode || 0} · ports {(ssot.metrics as Record<string, unknown>).ports as ReactNode || 0} · regs {(ssot.metrics as Record<string, unknown>).registers as ReactNode || 0} · scenarios {(ssot.metrics as Record<string, unknown>).dv_scenarios as ReactNode || 0}
          </div>
        )}
      </Section>

      <Section title="FL Model & Coverage Plan" right={(flModel.source as ReactNode) || (details.fl_model as ReactNode)}>
        <div style={{ display: 'grid', gridTemplateColumns: '86px 1fr', rowGap: 4, columnGap: 8, fontFamily: 'var(--mono)', marginBottom: 8 }}>
          <span className="mute">req</span><span style={{ color: stateColor(req.status) }}>{(req.status as ReactNode) || 'pending'} · {(req.files as unknown[] || []).length || 0} file(s)</span>
          <span className="mute">model</span><span style={{ color: stateColor(flModel.status) }}>{(flModel.status as ReactNode) || 'pending'} · {(flModel.bytes as ReactNode) || 0}B</span>
          <span className="mute">self-check</span><span style={{ color: flModel.self_check && (flModel.self_check as Record<string, unknown>).passed ? 'var(--ok)' : 'var(--fg-mute)' }}>{flModel.self_check && (flModel.self_check as Record<string, unknown>).passed ? 'pass' : 'missing'}</span>
          <span className="mute">decomp</span><span style={{ color: stateColor(flDecomp.status) }}>{(flDecomp.status as ReactNode) || 'pending'} · {(flDecomp.units as ReactNode) || 0} unit(s)</span>
          <span className="mute">fcov plan</span><span style={{ color: stateColor(fcovPlan.status) }}>{(fcovPlan.status as ReactNode) || 'pending'} · {(fcovPlan.bins as ReactNode) || 0} bin(s)</span>
          <span className="mute">equiv</span><span style={{ color: stateColor(equiv.status) }}>{(equiv.status as ReactNode) || 'pending'} · {(equiv.passed as ReactNode) || 0}/{(equiv.total as ReactNode) || 0} pass · {(equiv.blocked as ReactNode) || 0} blocked · {(equiv.untested as ReactNode) || 0} untested</span>
        </div>
        {Array.isArray(flDecomp.kinds) && flDecomp.kinds.length > 0 && (
          <div className="mute" style={{ fontFamily: 'var(--mono)', fontSize: 10 }}>
            model slices: {flDecomp.kinds.join(', ')}
          </div>
        )}
        {!!fcovPlan.summary && (
          <div className="mute" style={{ marginTop: 5, fontFamily: 'var(--mono)', fontSize: 10 }}>
            bins: scenario {(fcovPlan.summary as Record<string, unknown>).scenario_bins as ReactNode || 0} · transaction {(fcovPlan.summary as Record<string, unknown>).transaction_bins as ReactNode || 0} · protocol {(fcovPlan.summary as Record<string, unknown>).protocol_bins as ReactNode || 0} · state {(fcovPlan.summary as Record<string, unknown>).state_transition_bins as ReactNode || 0} · error {(fcovPlan.summary as Record<string, unknown>).error_bins as ReactNode || 0}
          </div>
        )}
        <div style={{ marginTop: 8 }}>
          <Bar
            label="equivalence goals"
            done={(equiv.passed as number) || 0}
            total={(equiv.total as number) || 0}
            color={stateColor(equiv.status)}
          />
          <div className="mute" style={{ fontFamily: 'var(--mono)', fontSize: 10, lineHeight: 1.45 }}>
            checked {(equiv.checked as ReactNode) || 0} · failed {(equiv.failed as ReactNode) || 0} · classifications {(equiv.classifications as ReactNode) || 0}
            {equiv.compare_evidence ? ` · ${equiv.compare_evidence}` : (equiv.evidence ? ` · ${equiv.evidence}` : '')}
          </div>
          {!!equiv.classification_counts && Object.keys(equiv.classification_counts as Record<string, unknown>).length > 0 && (
            <div className="mute" style={{ marginTop: 4, fontFamily: 'var(--mono)', fontSize: 10 }}>
              class: {Object.entries(equiv.classification_counts as Record<string, unknown>).map(([k, v]) => `${k}:${v}`).join(' · ')}
            </div>
          )}
          {!!equiv.owner_counts && Object.keys(equiv.owner_counts as Record<string, unknown>).length > 0 && (
            <div className="mute" style={{ marginTop: 4, fontFamily: 'var(--mono)', fontSize: 10 }}>
              owner: {Object.entries(equiv.owner_counts as Record<string, unknown>).map(([k, v]) => `${k}:${v}`).join(' · ')}
            </div>
          )}
          {Array.isArray(equiv.missing_evidence) && equiv.missing_evidence.length > 0 && (
            <div className="mute" style={{ marginTop: 4, fontFamily: 'var(--mono)', fontSize: 10 }}>
              missing: {equiv.missing_evidence.slice(0, 3).join(', ')}
            </div>
          )}
          {Array.isArray(equiv.stale_evidence) && equiv.stale_evidence.length > 0 && (
            <div style={{ marginTop: 4, color: 'var(--warn)', fontFamily: 'var(--mono)', fontSize: 10 }}>
              stale: {equiv.stale_evidence.slice(0, 3).join(', ')}
            </div>
          )}
          {Array.isArray(equiv.failed_goal_ids) && equiv.failed_goal_ids.length > 0 && (
            <div style={{ marginTop: 4, color: 'var(--warn)', fontFamily: 'var(--mono)', fontSize: 10 }}>
              failed: {equiv.failed_goal_ids.join(', ')}
            </div>
          )}
          {Array.isArray(equiv.blocked_goal_ids) && equiv.blocked_goal_ids.length > 0 && (
            <div style={{ marginTop: 4, color: 'var(--warn)', fontFamily: 'var(--mono)', fontSize: 10 }}>
              blocked: {equiv.blocked_goal_ids.join(', ')}
            </div>
          )}
          {Array.isArray(equiv.untested_goal_ids) && equiv.untested_goal_ids.length > 0 && (
            <div style={{ marginTop: 4, color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontSize: 10 }}>
              untested: {equiv.untested_goal_ids.join(', ')}
            </div>
          )}
          <div style={{ marginTop: 8, display: 'grid', gridTemplateColumns: '86px 1fr', rowGap: 4, columnGap: 8, fontFamily: 'var(--mono)', fontSize: 10 }}>
            <span className="mute">goal audit</span>
            <span style={{ color: stateColor(goalAudit.status) }}>
              {(goalAudit.status as ReactNode) || 'pending'} · {(goalAudit.passed_checks as ReactNode) || 0}/{(goalAudit.total_checks as ReactNode) || 0} checks · {(goalAudit.failed_checks as ReactNode) || 0} failed
            </span>
            <span className="mute">evidence</span>
            <span className="trunc" title={(goalAudit.source as string) || ''}>{(goalAudit.source as ReactNode) || 'run /goal-audit <ip>'}</span>
          </div>
          {Array.isArray(goalAudit.blockers) && goalAudit.blockers.length > 0 && (
            <div style={{ marginTop: 4, color: 'var(--warn)', fontFamily: 'var(--mono)', fontSize: 10 }}>
              audit blockers: {goalAudit.blockers.slice(0, 8).join(', ')}
            </div>
          )}
          {Array.isArray(goalAudit.stale_evidence) && goalAudit.stale_evidence.length > 0 && (
            <div style={{ marginTop: 4, color: 'var(--warn)', fontFamily: 'var(--mono)', fontSize: 10 }}>
              audit stale: {goalAudit.stale_evidence.slice(0, 3).join(', ')}
            </div>
          )}
        </div>
      </Section>

      <Section title="RTL Modules" right={(rtl.filelist as ReactNode) || (details.rtl as ReactNode)}>
        <Bar label="approved RTL files" done={(rtl.approved as number) || 0} total={(rtl.total as number) || 0} value={pct(rtl)} color="var(--accent)" />
        {rtlModules.length ? rtlModules.map((m: Record<string, unknown>) => (
          <div key={(m.file as string) || (m.name as string)} style={{
            display: 'grid', gridTemplateColumns: '14px 1fr auto', gap: 6,
            alignItems: 'baseline', padding: '3px 0', fontFamily: 'var(--mono)', fontSize: 10,
          }}>
            <span style={{ color: stateColor(m.status) }}>{m.status === 'approved' ? '✓' : m.status === 'partial' ? '◐' : '○'}</span>
            <span className="trunc" title={m.resolved_file && m.resolved_file !== m.file ? `${m.file} -> ${m.resolved_file}` : (m.file as string)}>
              {(m.name as ReactNode) || (m.file as ReactNode)}
              {m.manifest_mismatch ? <span style={{ color: 'var(--warn)' }}> · manifest</span> : null}
            </span>
            <span className="mute">{m.listed ? 'listed' : 'unlisted'} · {(m.bytes as ReactNode) || 0}B</span>
          </div>
        )) : <div className="mute">No expected RTL modules found in SSOT/filelist yet.</div>}
        {((rtl.manifest_mismatches as number) || 0) > 0 && (
          <div style={{ marginTop: 6, color: 'var(--warn)', fontFamily: 'var(--mono)', fontSize: 10 }}>
            SSOT/RTL manifest mismatch: {rtl.manifest_mismatches as ReactNode}
          </div>
        )}
      </Section>

      <Section title="Compile Gate" right={(compile.source as ReactNode) || ''}>
        <div style={{ display: 'grid', gridTemplateColumns: '82px 1fr', rowGap: 4, columnGap: 8, fontFamily: 'var(--mono)' }}>
          <span className="mute">status</span><span style={{ color: stateColor(compile.status) }}>{(compile.status as ReactNode) || 'unknown'}</span>
          <span className="mute">errors</span><span style={{ color: (compile.errors || 0) ? 'var(--err)' : 'var(--ok)' }}>{(compile.errors as ReactNode) ?? 0}</span>
          <span className="mute">diagnostics</span><span style={{ color: (compile.diagnostics || 0) ? 'var(--warn)' : 'var(--ok)' }}>{(compile.diagnostics as ReactNode) ?? 0}</span>
          <span className="mute">style</span><span style={{ color: (compile.style_violations || 0) ? 'var(--warn)' : 'var(--ok)' }}>{(compile.style_violations as ReactNode) ?? 0}</span>
        </div>
        {Array.isArray(compile.style_violation_details) && compile.style_violation_details.slice(0, 4).map((v: Record<string, unknown>, idx: number) => (
          <div key={idx} className="mute" style={{ marginTop: 5, fontFamily: 'var(--mono)', fontSize: 10, lineHeight: 1.35 }}>
            <span style={{ color: 'var(--warn)' }}>{v.file as ReactNode}:{v.line as ReactNode}</span> {v.rule as ReactNode}
          </div>
        ))}
      </Section>

      <Section title="Lint Gate" right={(lint.source as ReactNode) || ''}>
        <div style={{ display: 'grid', gridTemplateColumns: '70px 1fr', rowGap: 4, columnGap: 8, fontFamily: 'var(--mono)' }}>
          <span className="mute">status</span><span style={{ color: stateColor(lint.status) }}>{(lint.status as ReactNode) || 'unknown'}</span>
          <span className="mute">errors</span><span style={{ color: (lint.errors || 0) ? 'var(--err)' : 'var(--ok)' }}>{(lint.errors as ReactNode) ?? 0}</span>
          <span className="mute">warnings</span><span style={{ color: ((lint.warnings as number) || 0) > ((lint.warning_budget as number) || 0) ? 'var(--warn)' : 'var(--ok)' }}>{(lint.warnings as ReactNode) ?? 0} / budget {(lint.warning_budget as ReactNode) || 0}</span>
        </div>
      </Section>

      <Section title="Simulation & DV Plan" right={(results.sources as unknown[] || []).join(', ')}>
        <div style={{ display: 'grid', gridTemplateColumns: '90px 1fr', rowGap: 4, columnGap: 8, fontFamily: 'var(--mono)', marginBottom: 8 }}>
          <span className="mute">scenarios</span><span>{(dv.scenarios as ReactNode) || 0}</span>
          <span className="mute">scoreboard</span><span>{(dv.scoreboard_checks as ReactNode) ?? 'derive from SSOT'}</span>
          <span className="mute">tests</span><span>{(results.pass as ReactNode) || 0} pass / {(results.fail as ReactNode) || 0} fail / {(results.total as ReactNode) || 0} total</span>
          <span className="mute">checks</span><span>{(results.check_pass as ReactNode) ?? 0} pass / {(results.check_fail as ReactNode) ?? 0} fail / {(results.check_total as ReactNode) ?? 0} total</span>
        </div>
        {scenarios.slice(0, 12).map((sc: Record<string, unknown>) => (
          <div key={(sc.id as string) || (sc.name as string)} style={{
            display: 'grid', gridTemplateColumns: '42px 1fr 70px', gap: 6,
            fontFamily: 'var(--mono)', fontSize: 10, padding: '2px 0',
          }}>
            <span className="mute">{(sc.id as ReactNode) || '-'}</span>
            <span className="trunc" title={(sc.expected as string) || (sc.name as string)}>{(sc.name as ReactNode) || (sc.expected as ReactNode) || 'scenario'}</span>
            <span style={{ color: stateColor(sc.status), textAlign: 'right' }}>{(sc.status as ReactNode) || 'pending'}</span>
          </div>
        ))}
      </Section>

      <Section title="Coverage Criteria" right={(coverage.status as ReactNode) || 'unknown'}>
        <div style={{ display: 'grid', gridTemplateColumns: '90px 1fr', rowGap: 4, columnGap: 8, fontFamily: 'var(--mono)', marginBottom: 8 }}>
          <span className="mute">functional</span><span style={{ color: coverage.functional_pct == null ? 'var(--fg-mute)' : 'var(--ok)' }}>{coverage.functional_pct == null ? 'unknown' : (coverage.functional_pct as string | number) + '%'}</span>
          <span className="mute">goals</span><span>{Object.keys(criteria).length}</span>
          <span className="mute">limits</span><span style={{ color: Object.keys(limitations).length ? 'var(--warn)' : 'var(--fg-mute)' }}>{Object.keys(limitations).length || 0}</span>
        </div>
        {Object.entries(criteria).slice(0, 6).map(([k, v]) => (
          <div key={k} className="mute" style={{ fontFamily: 'var(--mono)', fontSize: 10, padding: '2px 0' }}>
            <span style={{ color: 'var(--fg)' }}>{k}</span>: {typeof v === 'object' ? JSON.stringify(v) : String(v)}
          </div>
        ))}
        {Object.entries(staticCov).slice(0, 4).map(([k, v]) => (
          <div key={k} className="mute" style={{ fontFamily: 'var(--mono)', fontSize: 10, padding: '2px 0' }}>
            static {k}: {typeof v === 'object' ? JSON.stringify(v) : String(v)}
          </div>
        ))}
        {Object.keys(limitations).length > 0 && (
          <div style={{ marginTop: 6, color: 'var(--warn)', fontFamily: 'var(--mono)', fontSize: 10 }}>
            coverage capability gap: {Object.keys(limitations).join(', ')}
          </div>
        )}
      </Section>
    </div>
  );
};

// ── Transitional bridge: register on window for not-yet-migrated .jsx ──
// Phase 23 window export (kept so unmigrated .jsx consumers still resolve
// window.ProgressPanel). window.TodoPanel is registered in ./progress-todo-todo.
(window as unknown as { ProgressPanel: typeof ProgressPanel }).ProgressPanel = ProgressPanel;

export { ProgressPanel, TodoPanel };
