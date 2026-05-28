// workspace-panels.jsx — Phase 13g refactor: 6 sidebar/panel components
// extracted from workspace.jsx as one cohesive cluster:
//
//   1. AskUserPrompt         (251 lines)  — chat-input ask_user prompt block
//   2. ProgressPanel         (461 lines)  — workflow progress card
//   3. TodoPanel             (426 lines)  — todo tracker sidebar
//   4. OrchestratorChatPanel (277 lines)  — orchestrator-mode side chat
//   5. GitPanel              (269 lines)  — per-IP git status + commits
//   6. AgentStatusPanel      (613 lines)  — right-rail agent status pane
//
// Total: ~2297 lines. workspace.jsx shrinks accordingly (-15% this phase /
// -38% cumulative since branch start). Same IIFE + lambda forward-ref
// pattern as Phase 13c/13d/13f. Only 13 unique workspace.jsx-scope deps
// (smaller per-line-extracted than any prior phase — these panels are
// closer to leaf components in the dependency graph).
//
// Load order (index.html): AFTER ssot-qa-board.jsx, BEFORE workspace.jsx.
// workspace.jsx exposes the 13 deps + aliases the 6 components back at
// end-of-file (TDZ-safe — every dep declared earlier in the file).

(() => {

// Forward-ref to workspace.jsx helpers (resolved at call time):
const AskUserQuestionBlock = (...a) => window.AskUserQuestionBlock(...a);
const AtlasStatusBadge = (...a) => window.AtlasStatusBadge(...a);
const TodoGraph = (...a) => window.TodoGraph(...a);
const _limitAtlasLines = (...a) => window._limitAtlasLines(...a);
const _statusGlyph = (...a) => window._statusGlyph(...a);
const atlasStatusMeta = (...a) => window.atlasStatusMeta(...a);
const atlasUiExecMode = (...a) => window.atlasUiExecMode(...a);
const healthMatchesCurrentUser = (...a) => window.healthMatchesCurrentUser(...a);
const normalizeUiSession = (...a) => window.normalizeUiSession(...a);
const uiEffectiveHealthSession = (...a) => window.uiEffectiveHealthSession(...a);
const uiHealthCountersMatchBrowserRoute = (...a) => window.uiHealthCountersMatchBrowserRoute(...a);
const uiSessionRoute = (...a) => window.uiSessionRoute(...a);
const workspaceFetchWorkerSnapshot = (...a) => window.workspaceFetchWorkerSnapshot(...a);


const AskUserPrompt = ({ flowId, state, sel, intent, fullHeight = false, onToggle, onCustom, onSubmit, onChat, onSel, onSetTab, onAdvance }) => {
  const flow = window.QA_FLOWS[flowId];
  if (!flow || !state) return null;

  // Batched flow virtualization — derive the "view" for the active tab
  // and reuse all the existing single-question rendering below.
  const isBatched = !!state.batched;
  const tabCount = isBatched ? (flow.questions || []).length : 0;
  const active = isBatched ? (state.active || 0) : 0;
  const isSubmitTab = isBatched && active === tabCount;
  // Active tab view (used by the option/custom widgets below)
  const tabState = isBatched
    ? (state.states && state.states[active]) || { opts: [], custom: '' }
    : state;
  const tabFlowKind = isBatched && !isSubmitTab ? flow.questions[active].kind : flow.kind;
  const tabFlowMultiline = !!(isBatched && !isSubmitTab ? flow.questions[active].multiline : flow.multiline);
  const tabAnswered = (i) => {
    const ts = state.states && state.states[i];
    if (!ts) return false;
    return (ts.opts || []).some(o => o.selected) || (ts.custom || '').trim().length > 0;
  };
  const allAnswered = isBatched
    ? (state.states || []).every((_, i) => tabAnswered(i))
    : true;

  const goNextBatchedStep = () => {
    if (!isBatched) return false;
    if (isSubmitTab) {
      if (allAnswered) onSubmit(flowId);
      return true;
    }
    if (active < tabCount - 1) {
      onAdvance ? onAdvance(flowId) : onSetTab && onSetTab(flowId, active + 1);
      return true;
    }
    if (allAnswered) {
      onSubmit(flowId);
    } else {
      onSetTab && onSetTab(flowId, tabCount);
    }
    return true;
  };

  const opts = tabState.opts || [];
  const customIdx = opts.length;       // row index for custom-text line
  const submitIdx = opts.length + 1;   // Submit menu line
  const chatIdx   = opts.length + 2;   // "Chat about this" menu line
  const lastIdx   = chatIdx;

  const onKey = (e) => {
    // Batched flow: ⌘/⌃ + ←/→ moves the keyboard cursor between
    // question blocks (each Q renders its own block; the active block
    // is highlighted and owns the option/custom cursor).
    if (isBatched) {
      if (e.key === 'ArrowLeft' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault(); onSetTab && onSetTab(flowId, Math.max(0, active - 1)); return;
      }
      if (e.key === 'ArrowRight' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault(); onSetTab && onSetTab(flowId, Math.min(tabCount - 1, active + 1)); return;
      }
    }
    if (e.key === 'ArrowDown' || (e.key === 'j' && !e.metaKey && !e.ctrlKey && document.activeElement?.tagName !== 'INPUT')) {
      e.preventDefault(); onSel(Math.min(sel + 1, lastIdx)); return;
    }
    if (e.key === 'ArrowUp' || (e.key === 'k' && !e.metaKey && !e.ctrlKey && document.activeElement?.tagName !== 'INPUT')) {
      e.preventDefault(); onSel(Math.max(sel - 1, 0)); return;
    }
    if (e.key === ' ' && sel < opts.length) {
      // When focus is in the custom-answer input/textarea, space must
      // pass through to the field. Without this guard the parent
      // div's keydown intercepts and toggles the selected option
      // instead, swallowing every space the user types.
      const ae = document.activeElement;
      const aeTag = ae && ae.tagName;
      if (aeTag === 'INPUT' || aeTag === 'TEXTAREA' || (ae && ae.isContentEditable)) return;
      e.preventDefault(); onToggle(flowId, opts[sel].id); return;
    }
    if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
      const activeEl = document.activeElement;
      const isCustomInput = activeEl && activeEl.classList && activeEl.classList.contains('askcustom');
      if (isCustomInput && tabFlowMultiline && !e.metaKey && !e.ctrlKey) return;
      e.preventDefault();
      // Custom-input Enter: in batched, advance to next question (or
      // submit-all on the last); in single, submit immediately when the
      // text isn't empty so a one-shot QA can be answered with Enter.
      if (isCustomInput) {
        if (isBatched) { goNextBatchedStep(); return; }
        if ((tabState.custom || '').trim() || opts.some(o => o.selected)) {
          onSubmit(flowId);
        }
        return;
      }
      if (sel < opts.length) {
        onToggle(flowId, opts[sel].id);
        // Batched + single-kind: advance to next question (or submit
        // when on the last one and everything else is answered).
        if (isBatched && tabFlowKind !== 'multi') { goNextBatchedStep(); return; }
        // Non-batched + single-kind (one-question flow): Enter
        // immediately submits — the user just picked their answer.
        if (!isBatched && tabFlowKind === 'single') { onSubmit(flowId); return; }
        return;
      }
      if (sel === customIdx) {
        if (isBatched && (tabState.custom || '').trim()) { goNextBatchedStep(); return; }
        const el = e.currentTarget.querySelector('input.askcustom, textarea.askcustom'); el?.focus(); return;
      }
      if (sel === submitIdx) {
        if (isBatched) { if (allAnswered) onSubmit(flowId); return; }
        onSubmit(flowId);
        return;
      }
      if (sel === chatIdx)   { onChat(flowId); return; }
    }
    if (e.key === 'Escape') { e.preventDefault(); onSel(0); }
  };

  const renderQuestionBlock = (i, block, bs, kind) => (
    <AskUserQuestionBlock
      key={i}
      index={i}
      block={block}
      blockState={bs}
      kind={kind}
      isBatched={isBatched}
      isActive={!isBatched || i === active}
      answered={tabAnswered(i)}
      selectedIndex={sel}
      onEnsureActive={(idx) => {
        if (isBatched && idx !== active && onSetTab) onSetTab(flowId, idx);
      }}
      onSelectIndex={onSel}
      onToggleOption={(optionId) => onToggle(flowId, optionId)}
      onCustom={(value) => onCustom(flowId, value)}
      onSelectAll={(blockOpts) => {
        blockOpts.forEach(o => { if (!o.selected && !o.locked) onToggle(flowId, o.id); });
      }}
      onClearAll={(blockOpts) => {
        blockOpts.forEach(o => { if (o.selected && !o.locked) onToggle(flowId, o.id); });
      }}
    />
  );

  return (
    <div
      className="ask-prompt fade-in"
      tabIndex={0}
      onKeyDown={onKey}
      style={{
        border: `1px solid var(--accent)`,
        borderLeftWidth: 3,
        background: 'var(--bg-2)',
        padding: '10px 14px 8px',
        outline: 'none',
        boxShadow: '0 -2px 0 0 color-mix(in oklch, var(--accent) 25%, transparent)',
        height: fullHeight ? '100%' : undefined,
        minHeight: fullHeight ? 0 : undefined,
        overflow: fullHeight ? 'auto' : undefined,
      }}
    >
      {/* header — mimics the screenshot: "▸ ask_user · ✓ Submit" */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8,
        fontSize: 'var(--ui-control-font-size)', letterSpacing: '0.06em', textTransform: 'uppercase',
      }}>
        <span className="acc" style={{ fontWeight: 700 }}>▸ ask_user</span>
        <span className="mute">·</span>
        <span className="ok" style={{ fontWeight: 600, opacity: sel === submitIdx ? 1 : 0.6 }}>✓ Submit</span>
        <span className="mute">·</span>
        <span className="mute">{flow.stage} · step {flow.step}/{flow.total}</span>
        <span style={{ flex: 1 }} />
        {intent === 'plan' && (
          <span className="warn" style={{ fontSize: 10, fontWeight: 700 }}>◐ plan mode · still asks</span>
        )}
        <span className="mute" style={{ textTransform: 'none', letterSpacing: 0, fontSize: 10 }}>
          {tabFlowKind === 'multi' ? 'multi-select' : tabFlowKind === 'input' ? 'text' : 'single-select'}
        </span>
        {isBatched && (
          <span
            className={allAnswered ? 'ok' : 'mute'}
            style={{ textTransform: 'none', letterSpacing: 0, fontSize: 10, marginLeft: 6, fontWeight: 600 }}
          >
            · {(state.states || []).filter((_, i) => tabAnswered(i)).length}/{tabCount} answered
          </span>
        )}
      </div>

      {/* questions — single block when not batched, stacked blocks when batched */}
      {isBatched
        ? (flow.questions || []).map((q, i) => {
            const ts = (state.states || [])[i] || { opts: [], custom: '' };
            const k = q.kind === 'multi' ? 'multi' : q.kind === 'input' ? 'input' : 'single';
            return renderQuestionBlock(i, q, ts, k);
          })
        : renderQuestionBlock(0, flow, state, tabFlowKind)}

      {/* submit row — for batched, gates on allAnswered and submits all */}
      <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 0 }}>
        <div
          onClick={() => {
            if (isBatched) { if (allAnswered) onSubmit(flowId); }
            else onSubmit(flowId);
          }}
          style={{
            padding: '4px 8px',
            background: sel === submitIdx ? 'color-mix(in oklch, var(--ok) 18%, transparent)' : 'transparent',
            borderLeft: `2px solid ${sel === submitIdx ? 'var(--ok)' : 'transparent'}`,
            cursor: (isBatched && !allAnswered) ? 'not-allowed' : 'pointer',
            fontFamily: 'var(--mono)', fontSize: 13,
            color: sel === submitIdx ? 'var(--ok)' : 'var(--fg)',
            fontWeight: sel === submitIdx ? 600 : 400,
            opacity: (isBatched && !allAnswered) ? 0.6 : 1,
          }}
        >
          <span className="mute" style={{ marginRight: 6 }}>›</span>
          {isBatched ? `Submit all (${(state.states || []).filter((_, i) => tabAnswered(i)).length}/${tabCount})` : 'Submit'}
          {!isBatched && (
            <span className="mute" style={{ marginLeft: 8, fontSize: 11 }}>
              ({(opts.filter(o => o.selected) || []).length}{tabState.custom ? '+1' : ''} reply)
            </span>
          )}
        </div>
        <div
          onClick={() => { onSel(chatIdx); onChat(flowId); }}
          style={{
            padding: '4px 8px',
            background: sel === chatIdx ? 'color-mix(in oklch, var(--accent) 14%, transparent)' : 'transparent',
            borderLeft: `2px solid ${sel === chatIdx ? 'var(--accent)' : 'transparent'}`,
            cursor: 'pointer',
            fontFamily: 'var(--mono)', fontSize: 13,
          }}
        >
          <span className="mute" style={{ marginRight: 6 }}>›</span>Chat about this
          <span className="mute" style={{ marginLeft: 8, fontSize: 11 }}>(send a free-form message instead)</span>
        </div>
      </div>

      {/* hint footer — terminal-style */}
      <div className="mute" style={{
        marginTop: 8, paddingTop: 6, borderTop: '1px dashed var(--line)',
        fontSize: 'var(--ui-control-font-size)', display: 'flex', gap: 14, flexWrap: 'wrap',
      }}>
        <span><Kbd>↵</Kbd> {isBatched ? 'select & next' : 'select & submit'}</span>
        <span><Kbd>↑↓</Kbd>/<Kbd>j k</Kbd> navigate</span>
        <span><Kbd>Space</Kbd> toggle</span>
        <span><Kbd>Tab</Kbd> next field</span>
        {isBatched && <span><Kbd>⌘/⌃ ←→</Kbd> switch question</span>}
        <span><Kbd>Esc</Kbd> top</span>
      </div>
    </div>
  );
};


const ProgressPanel = () => {
  const [, bump] = React.useReducer(x => x + 1, 0);
  const [moduleId, setModuleId] = React.useState('');

  React.useEffect(() => {
    const h = (ev) => {
      if (!ev.detail || ['PROGRESS', 'SCOPE_PATH', 'SSOT_FILES', 'TODOS'].includes(ev.detail)) bump();
    };
    window.addEventListener('atlas-data-changed', h);
    if (window.atlasData && window.atlasData.refreshProgress) window.atlasData.refreshProgress();
    return () => window.removeEventListener('atlas-data-changed', h);
  }, []);

  const data = window.ATLAS_PROGRESS || {};
  const modules = Array.isArray(data.modules) ? data.modules : [];
  // Active IP comes from the top-bar selector (single source of truth).
  // We derive it from ACTIVE_SESSION and pivot the panel onto that
  // module — no internal IP picker, since the user explicitly asked
  // for "IP는 맨 위에서 선택, 다른 곳에선 표시만".
  const _activeIp = (() => {
    const ns = String(window.ACTIVE_SESSION || '').split('/').filter(Boolean);
    if (ns.length >= 2) return ns[1];
    return '';
  })();
  const selected = modules.find(m => (m.id || m.name) === _activeIp)
    || modules.find(m => m.id === moduleId)
    || data.selected
    || modules[0]
    || null;

  React.useEffect(() => {
    if (selected && selected.id && selected.id !== moduleId) setModuleId(selected.id);
  }, [selected && selected.id]);

  const progress = (selected && selected.progress) || {};
  const status = (selected && selected.status) || {};
  const details = (selected && selected.status_detail) || {};
  const signoff = (selected && selected.signoff) || {};
  const blockers = Array.isArray(signoff.blockers) ? signoff.blockers : [];
  const ownership = signoff.ownership || {};
  const artifact = (selected && selected.artifact_status) || {};
  const artifactDetails = (selected && selected.artifact_detail) || {};
  const req = progress.req || {};
  const ssot = progress.ssot || {};
  const flModel = progress.fl_model || {};
  const flDecomp = progress.fl_decomp || {};
  const fcovPlan = progress.fcov_plan || {};
  const equiv = progress.equivalence_goals || {};
  const goalAudit = progress.goal_audit || {};
  const rtl = progress.rtl || {};
  const compile = progress.compile || {};
  const lint = progress.lint || {};
  const sim = progress.sim || {};
  const dv = sim.dv_plan || {};
  const results = sim.results || {};
  const coverage = sim.coverage || {};

  const pct = (obj) => Math.max(0, Math.min(100, Number(obj && obj.pct) || 0));
  const stateColor = (s) => {
    const v = String(s || '').toLowerCase();
    if (['ok', 'pass', 'approved', 'done'].includes(v)) return 'var(--ok)';
    if (['fail', 'err', 'error', 'rejected'].includes(v)) return 'var(--err)';
    if (['partial', 'planned', 'active', 'blocked', 'stale'].includes(v)) return 'var(--warn)';
    return 'var(--fg-mute)';
  };
  const pill = (label, value) => (
    <span style={{
      border: `1px solid ${stateColor(value)}`,
      color: stateColor(value),
      borderRadius: 2,
      padding: '1px 6px',
      fontSize: 10,
      fontFamily: 'var(--mono)',
      whiteSpace: 'nowrap',
    }}>{label}: {value || 'pending'}</span>
  );
  const Bar = ({ label, done, total, value, color = 'var(--ok)' }) => {
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
  const Section = ({ title, right, children }) => (
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
    if (!ip || !window.backend) return;
    window.backend.send({ type: 'prompt', text: `/repair-rtl ${ip}` });
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
  const criteria = coverage.criteria && typeof coverage.criteria === 'object' ? coverage.criteria : {};
  const limitations = coverage.limitations && typeof coverage.limitations === 'object' ? coverage.limitations : {};
  const staticCov = coverage.static && typeof coverage.static === 'object' ? coverage.static : {};
  const ownershipRows = [
    'req', 'ssot', 'fl_model', 'fl_decomp', 'fcov_plan', 'equivalence_goals',
    'goal_audit', 'rtl', 'lint', 'tb', 'sim_debug', 'coverage', 'signoff',
  ].map(k => ownership[k]).filter(Boolean);

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
          <span className="mute">req</span><span className="trunc" title={artifactDetails.req || ''}>{artifactDetails.req || 'no requirement evidence'}</span>
          <span className="mute">ssot</span><span className="trunc" title={artifactDetails.ssot || ''}>{artifactDetails.ssot || 'no artifact evidence'}</span>
          <span className="mute">fl</span><span className="trunc" title={artifactDetails.fl_model || ''}>{artifactDetails.fl_model || 'no executable FL model'}</span>
          <span className="mute">decomp</span><span className="trunc" title={artifactDetails.fl_decomp || ''}>{artifactDetails.fl_decomp || 'no FL decomposition'}</span>
          <span className="mute">fcov</span><span className="trunc" title={artifactDetails.fcov_plan || ''}>{artifactDetails.fcov_plan || 'no FCOV plan'}</span>
          <span className="mute">equiv</span><span className="trunc" title={artifactDetails.equivalence_goals || ''}>{artifactDetails.equivalence_goals || 'no equivalence goals'}</span>
          <span className="mute">audit</span><span className="trunc" title={artifactDetails.goal_audit || ''}>{artifactDetails.goal_audit || 'no goal audit'}</span>
          <span className="mute">rtl</span><span className="trunc" title={artifactDetails.rtl || ''}>{artifactDetails.rtl || 'no artifact evidence'}</span>
          <span className="mute">tb</span><span className="trunc" title={artifactDetails.tb || ''}>{artifactDetails.tb || 'no artifact evidence'}</span>
          <span className="mute">simdbg</span><span className="trunc" title={artifactDetails.sim_debug || ''}>{artifactDetails.sim_debug || 'no artifact evidence'}</span>
        </div>
      </Section>

      <Section title="Loop Owner & Next Action" right="LLM loop / human gate">
        {ownershipRows.length ? (
          <div style={{ display: 'grid', gridTemplateColumns: '58px 68px 1fr', rowGap: 5, columnGap: 8, fontFamily: 'var(--mono)', fontSize: 10 }}>
            {ownershipRows.map(row => (
              <React.Fragment key={row.stage}>
                <span className="mute">{String(row.stage || '').replace('_', ' ')}</span>
                <span style={{ color: row.owner === 'human gate' ? 'var(--warn)' : stateColor(row.status) }}>
                  {row.owner || 'LLM loop'}
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
                  {row.next_action || 'inspect stage evidence'}
                </span>
              </React.Fragment>
            ))}
          </div>
        ) : (
          <div className="mute" style={{ fontFamily: 'var(--mono)', fontSize: 10 }}>
            ownership data missing from ATLAS progress response
          </div>
        )}
      </Section>

      <Section title="SSOT Sections" right={selected.ssot_path}>
        <Bar label="approved sections" done={ssot.approved || 0} total={ssot.total || 0} value={pct(ssot)} />
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 4 }}>
          {sections.map(s => (
            <div key={s.key} title={s.key} style={{
              display: 'flex', alignItems: 'center', gap: 5, minWidth: 0,
              color: s.status === 'approved' ? 'var(--fg)' : 'var(--fg-mute)',
              fontFamily: 'var(--mono)', fontSize: 10,
            }}>
              <span style={{ color: stateColor(s.status), width: 10 }}>{s.status === 'approved' ? '✓' : '○'}</span>
              <span className="trunc">{s.label || s.key}</span>
            </div>
          ))}
        </div>
        {ssot.metrics && (
          <div className="mute" style={{ marginTop: 8, lineHeight: 1.5, fontFamily: 'var(--mono)' }}>
            submods {ssot.metrics.submodules || 0} · ports {ssot.metrics.ports || 0} · regs {ssot.metrics.registers || 0} · scenarios {ssot.metrics.dv_scenarios || 0}
          </div>
        )}
      </Section>

      <Section title="FL Model & Coverage Plan" right={flModel.source || details.fl_model}>
        <div style={{ display: 'grid', gridTemplateColumns: '86px 1fr', rowGap: 4, columnGap: 8, fontFamily: 'var(--mono)', marginBottom: 8 }}>
          <span className="mute">req</span><span style={{ color: stateColor(req.status) }}>{req.status || 'pending'} · {(req.files || []).length || 0} file(s)</span>
          <span className="mute">model</span><span style={{ color: stateColor(flModel.status) }}>{flModel.status || 'pending'} · {flModel.bytes || 0}B</span>
          <span className="mute">self-check</span><span style={{ color: flModel.self_check && flModel.self_check.passed ? 'var(--ok)' : 'var(--fg-mute)' }}>{flModel.self_check && flModel.self_check.passed ? 'pass' : 'missing'}</span>
          <span className="mute">decomp</span><span style={{ color: stateColor(flDecomp.status) }}>{flDecomp.status || 'pending'} · {flDecomp.units || 0} unit(s)</span>
          <span className="mute">fcov plan</span><span style={{ color: stateColor(fcovPlan.status) }}>{fcovPlan.status || 'pending'} · {fcovPlan.bins || 0} bin(s)</span>
          <span className="mute">equiv</span><span style={{ color: stateColor(equiv.status) }}>{equiv.status || 'pending'} · {equiv.passed || 0}/{equiv.total || 0} pass · {equiv.blocked || 0} blocked · {equiv.untested || 0} untested</span>
        </div>
        {Array.isArray(flDecomp.kinds) && flDecomp.kinds.length > 0 && (
          <div className="mute" style={{ fontFamily: 'var(--mono)', fontSize: 10 }}>
            model slices: {flDecomp.kinds.join(', ')}
          </div>
        )}
        {fcovPlan.summary && (
          <div className="mute" style={{ marginTop: 5, fontFamily: 'var(--mono)', fontSize: 10 }}>
            bins: scenario {fcovPlan.summary.scenario_bins || 0} · transaction {fcovPlan.summary.transaction_bins || 0} · protocol {fcovPlan.summary.protocol_bins || 0} · state {fcovPlan.summary.state_transition_bins || 0} · error {fcovPlan.summary.error_bins || 0}
          </div>
        )}
        <div style={{ marginTop: 8 }}>
          <Bar
            label="equivalence goals"
            done={equiv.passed || 0}
            total={equiv.total || 0}
            color={stateColor(equiv.status)}
          />
          <div className="mute" style={{ fontFamily: 'var(--mono)', fontSize: 10, lineHeight: 1.45 }}>
            checked {equiv.checked || 0} · failed {equiv.failed || 0} · classifications {equiv.classifications || 0}
            {equiv.compare_evidence ? ` · ${equiv.compare_evidence}` : (equiv.evidence ? ` · ${equiv.evidence}` : '')}
          </div>
          {equiv.classification_counts && Object.keys(equiv.classification_counts).length > 0 && (
            <div className="mute" style={{ marginTop: 4, fontFamily: 'var(--mono)', fontSize: 10 }}>
              class: {Object.entries(equiv.classification_counts).map(([k, v]) => `${k}:${v}`).join(' · ')}
            </div>
          )}
          {equiv.owner_counts && Object.keys(equiv.owner_counts).length > 0 && (
            <div className="mute" style={{ marginTop: 4, fontFamily: 'var(--mono)', fontSize: 10 }}>
              owner: {Object.entries(equiv.owner_counts).map(([k, v]) => `${k}:${v}`).join(' · ')}
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
              {goalAudit.status || 'pending'} · {goalAudit.passed_checks || 0}/{goalAudit.total_checks || 0} checks · {goalAudit.failed_checks || 0} failed
            </span>
            <span className="mute">evidence</span>
            <span className="trunc" title={goalAudit.source || ''}>{goalAudit.source || 'run /goal-audit <ip>'}</span>
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

      <Section title="RTL Modules" right={rtl.filelist || details.rtl}>
        <Bar label="approved RTL files" done={rtl.approved || 0} total={rtl.total || 0} value={pct(rtl)} color="var(--accent)" />
        {rtlModules.length ? rtlModules.map(m => (
          <div key={m.file || m.name} style={{
            display: 'grid', gridTemplateColumns: '14px 1fr auto', gap: 6,
            alignItems: 'baseline', padding: '3px 0', fontFamily: 'var(--mono)', fontSize: 10,
          }}>
            <span style={{ color: stateColor(m.status) }}>{m.status === 'approved' ? '✓' : m.status === 'partial' ? '◐' : '○'}</span>
            <span className="trunc" title={m.resolved_file && m.resolved_file !== m.file ? `${m.file} -> ${m.resolved_file}` : m.file}>
              {m.name || m.file}
              {m.manifest_mismatch ? <span style={{ color: 'var(--warn)' }}> · manifest</span> : null}
            </span>
            <span className="mute">{m.listed ? 'listed' : 'unlisted'} · {m.bytes || 0}B</span>
          </div>
        )) : <div className="mute">No expected RTL modules found in SSOT/filelist yet.</div>}
        {(rtl.manifest_mismatches || 0) > 0 && (
          <div style={{ marginTop: 6, color: 'var(--warn)', fontFamily: 'var(--mono)', fontSize: 10 }}>
            SSOT/RTL manifest mismatch: {rtl.manifest_mismatches}
          </div>
        )}
      </Section>

      <Section title="Compile Gate" right={compile.source || ''}>
        <div style={{ display: 'grid', gridTemplateColumns: '82px 1fr', rowGap: 4, columnGap: 8, fontFamily: 'var(--mono)' }}>
          <span className="mute">status</span><span style={{ color: stateColor(compile.status) }}>{compile.status || 'unknown'}</span>
          <span className="mute">errors</span><span style={{ color: (compile.errors || 0) ? 'var(--err)' : 'var(--ok)' }}>{compile.errors ?? 0}</span>
          <span className="mute">diagnostics</span><span style={{ color: (compile.diagnostics || 0) ? 'var(--warn)' : 'var(--ok)' }}>{compile.diagnostics ?? 0}</span>
          <span className="mute">style</span><span style={{ color: (compile.style_violations || 0) ? 'var(--warn)' : 'var(--ok)' }}>{compile.style_violations ?? 0}</span>
        </div>
        {Array.isArray(compile.style_violation_details) && compile.style_violation_details.slice(0, 4).map((v, idx) => (
          <div key={idx} className="mute" style={{ marginTop: 5, fontFamily: 'var(--mono)', fontSize: 10, lineHeight: 1.35 }}>
            <span style={{ color: 'var(--warn)' }}>{v.file}:{v.line}</span> {v.rule}
          </div>
        ))}
      </Section>

      <Section title="Lint Gate" right={lint.source || ''}>
        <div style={{ display: 'grid', gridTemplateColumns: '70px 1fr', rowGap: 4, columnGap: 8, fontFamily: 'var(--mono)' }}>
          <span className="mute">status</span><span style={{ color: stateColor(lint.status) }}>{lint.status || 'unknown'}</span>
          <span className="mute">errors</span><span style={{ color: (lint.errors || 0) ? 'var(--err)' : 'var(--ok)' }}>{lint.errors ?? 0}</span>
          <span className="mute">warnings</span><span style={{ color: (lint.warnings || 0) > (lint.warning_budget || 0) ? 'var(--warn)' : 'var(--ok)' }}>{lint.warnings ?? 0} / budget {lint.warning_budget || 0}</span>
        </div>
      </Section>

      <Section title="Simulation & DV Plan" right={(results.sources || []).join(', ')}>
        <div style={{ display: 'grid', gridTemplateColumns: '90px 1fr', rowGap: 4, columnGap: 8, fontFamily: 'var(--mono)', marginBottom: 8 }}>
          <span className="mute">scenarios</span><span>{dv.scenarios || 0}</span>
          <span className="mute">scoreboard</span><span>{dv.scoreboard_checks ?? 'derive from SSOT'}</span>
          <span className="mute">tests</span><span>{results.pass || 0} pass / {results.fail || 0} fail / {results.total || 0} total</span>
          <span className="mute">checks</span><span>{results.check_pass ?? 0} pass / {results.check_fail ?? 0} fail / {results.check_total ?? 0} total</span>
        </div>
        {scenarios.slice(0, 12).map(sc => (
          <div key={sc.id || sc.name} style={{
            display: 'grid', gridTemplateColumns: '42px 1fr 70px', gap: 6,
            fontFamily: 'var(--mono)', fontSize: 10, padding: '2px 0',
          }}>
            <span className="mute">{sc.id || '-'}</span>
            <span className="trunc" title={sc.expected || sc.name}>{sc.name || sc.expected || 'scenario'}</span>
            <span style={{ color: stateColor(sc.status), textAlign: 'right' }}>{sc.status || 'pending'}</span>
          </div>
        ))}
      </Section>

      <Section title="Coverage Criteria" right={coverage.status || 'unknown'}>
        <div style={{ display: 'grid', gridTemplateColumns: '90px 1fr', rowGap: 4, columnGap: 8, fontFamily: 'var(--mono)', marginBottom: 8 }}>
          <span className="mute">functional</span><span style={{ color: coverage.functional_pct == null ? 'var(--fg-mute)' : 'var(--ok)' }}>{coverage.functional_pct == null ? 'unknown' : coverage.functional_pct + '%'}</span>
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

// Editable TODO tab — full-column pane that mirrors the session todo.json
// (.session/<session>/todo.json) and supports add / modify / remove / clear
// via the /api/todos/{add,update,remove,clear} endpoints. Source of truth is


const TodoPanel = () => {
  const [view, setView] = React.useState('compact'); // compact | detail | graph
  const [openId, setOpenId] = React.useState(null);
  // Per-group collapse state in compact view: {approved: true, ...}
  // means that group is collapsed. Defaults set via collapsedDefault
  // inside the render so they're not duplicated.
  const [collapsedTodoGroups, setCollapsedTodoGroups] = React.useState({});
  const todos = Array.isArray(window.TODOS) ? window.TODOS : [];
  // "Done" counter spans every terminal state (done/approved/completed)
  // — without this, the counter showed 0/7 for tasks the agent had
  // explicitly approved because raw 'approved' status now flows
  // through unchanged from data.jsx.
  const done = todos.filter(t => ['done', 'approved', 'completed'].includes(t.state)).length;

  // Map every status to a glyph + color so the right panel reads at a
  // glance. data.jsx normalizes TodoTracker statuses
  // (pending/in_progress/completed/approved/rejected) into the simpler
  // pending/active/done used by this UI; the renderer below also keeps
  // explicit cases for the raw statuses so live updates render right.
  const stateCfg = (s) => {
    const meta = atlasStatusMeta(s);
    switch (s) {
      // Auto-finished by the agent (no explicit human nod)
      case 'done':        return { glyph: meta.glyph, color: meta.color, label: meta.label };
      case 'completed':   return { glyph: meta.glyph, color: meta.color, label: meta.label };
      // Explicitly approved by a human — distinct glyph + accent
      // colour so the pending/approved distinction reads at a glance
      case 'approved':    return { glyph: meta.glyph, color: meta.color, label: meta.label };
      case 'active':      return { glyph: meta.glyph, color: meta.color, label: 'in-progress' };
      case 'in_progress': return { glyph: meta.glyph, color: meta.color, label: meta.label };
      case 'rejected':    return { glyph: meta.glyph, color: meta.color, label: meta.label };
      // Hollow square + warm warn-yellow so it never reads as "done"
      case 'pending':     return { glyph: meta.glyph, color: meta.color, label: meta.label };
      default:            return { glyph: '☐', color: 'var(--fg-mute)', label: s || '?' };
    }
  };

  const todoLines = (value, { splitCommas = false } = {}) => {
    if (Array.isArray(value)) {
      return value.flatMap(v => todoLines(v, { splitCommas }));
    }
    if (value && typeof value === 'object') {
      return Object.entries(value).flatMap(([k, v]) => {
        const vv = String(v ?? '').trim();
        return vv ? [`${k}: ${vv}`] : [String(k)];
      }).filter(Boolean);
    }
    const raw = String(value ?? '').trim();
    if (!raw) return [];
    const prepared = raw.replace(/\s+(Each\s+TODO\s+gets:)/gi, '\n$1');
    return prepared
      .split(/\r?\n+/)
      .map(line => line.trim())
      .filter(Boolean)
      .flatMap((line) => {
        const clean = line.replace(/^[-*•]\s*/, '').trim();
        if (!clean) return [];
        if (!splitCommas) return [clean];
        const m = clean.match(/^([^:]{2,48}):\s*(.+)$/);
        if (m) return [clean];
        const items = clean.split(/\s*,\s*/).map(s => s.trim()).filter(Boolean);
        if (items.length >= 4 && clean.length > 120) return items;
        return [clean];
      });
  };

  const todoDetailBlocks = (detail) => {
    const blocks = [];
    todoLines(detail, { splitCommas: false }).forEach((line) => {
      const parts = line.length > 180
        ? line.split(/(?<=\.)\s+|;\s+/).map(s => s.trim()).filter(Boolean)
        : [line];
      parts.forEach((part) => {
        const listMatch = part.match(/^([^:]{2,48}):\s*(.+)$/);
        if (listMatch && listMatch[2].includes(',')) {
          const items = listMatch[2].split(/\s*,\s*/).map(s => s.trim()).filter(Boolean);
          if (items.length >= 3) {
            blocks.push({ type: 'list', label: listMatch[1], items });
            return;
          }
        }
        blocks.push({ type: 'text', text: part });
      });
    });
    return blocks;
  };

  const TodoField = ({ label, children }) => (
    <div style={{ display: 'grid', gap: 3 }}>
      <div style={{
        color: 'var(--cyan)',
        fontSize: 10,
        letterSpacing: '0.08em',
        textTransform: 'uppercase',
        fontWeight: 700,
      }}>{label}</div>
      <div style={{ color: 'var(--fg-dim)', lineHeight: 1.62 }}>{children}</div>
    </div>
  );

  const TodoBulletList = ({ items }) => (
    <div style={{ display: 'grid', gap: 2 }}>
      {items.map((item, idx) => (
        <div key={`${item}-${idx}`} style={{ display: 'flex', alignItems: 'flex-start', gap: 6 }}>
          <span className="mute" style={{ lineHeight: 1.6 }}>•</span>
          <span style={{ flex: 1 }}>{item}</span>
        </div>
      ))}
    </div>
  );

  const TodoStructuredBody = ({ todo }) => {
    const detail = todoDetailBlocks(todo.detail);
    const criteria = todoLines(todo.criteria, { splitCommas: true });
    const sourceRefs = todoLines(todo.sourceRefs, { splitCommas: true });
    const owner = [String(todo.ownerModule || '').trim(), String(todo.ownerFile || '').trim()].filter(Boolean);
    const required = typeof todo.required === 'boolean'
      ? (todo.required ? 'yes' : 'no')
      : (todo.required == null ? '' : String(todo.required).trim());
    return (
      <div style={{ display: 'grid', gap: 8, overflowWrap: 'anywhere' }}>
        {detail.length > 0 && (
          <TodoField label="Detail">
            <div style={{ display: 'grid', gap: 4 }}>
              {detail.map((blk, idx) => (
                blk.type === 'list' ? (
                  <div key={`dlist-${idx}`} style={{ display: 'grid', gap: 3 }}>
                    <span style={{ color: 'var(--fg)' }}>{blk.label}</span>
                    <TodoBulletList items={blk.items} />
                  </div>
                ) : (
                  <div key={`dtext-${idx}`}>{blk.text}</div>
                )
              ))}
            </div>
          </TodoField>
        )}
        {criteria.length > 0 && (
          <TodoField label="Criteria">
            <TodoBulletList items={criteria} />
          </TodoField>
        )}
        {sourceRefs.length > 0 && (
          <TodoField label="Source Refs">
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {sourceRefs.map((ref, idx) => (
                <span key={`src-${idx}`} style={{
                  border: '1px solid var(--line)',
                  borderRadius: 2,
                  padding: '1px 6px',
                  color: 'var(--fg)',
                }}>{ref}</span>
              ))}
            </div>
          </TodoField>
        )}
        {owner.length > 0 && (
          <TodoField label="Owner">{owner.join(' · ')}</TodoField>
        )}
        {required && (
          <TodoField label="Required">{required}</TodoField>
        )}
      </div>
    );
  };

  const TodoReason = ({ todo }) => {
    const approved = todo.state === 'approved' || todo.state === 'done';
    const rejected = todo.state === 'rejected';
    const reason = approved ? todo.approvedReason : rejected ? todo.rejectionReason : '';
    if (!reason) return null;
    const label = approved ? 'Approved' : 'Rejected';
    const color = approved ? 'var(--ok)' : 'var(--err)';
    return (
      <div style={{
        marginTop: 5,
        fontFamily: 'var(--mono)',
        fontSize: 'var(--ui-font-size)',
        lineHeight: 1.55,
        whiteSpace: 'pre-wrap',
      }}>
        <span style={{ color, fontWeight: 700 }}>{label}</span>
        <span className="mute"> : </span>
        <span style={{ color: 'var(--fg-dim)' }}>{_limitAtlasLines(reason, 5)}</span>
      </div>
    );
  };

  const TodoNotes = ({ todo }) => {
    const notes = Array.isArray(todo.notes) ? todo.notes.filter(n => String(n || '').trim()) : [];
    if (!notes.length) return null;
    const lastIndex = notes.length;
    const last = String(notes[notes.length - 1] || '');
    return (
      <div style={{
        marginTop: 5,
        fontFamily: 'var(--mono)',
        fontSize: 'var(--ui-font-size)',
        lineHeight: 1.55,
        whiteSpace: 'pre-wrap',
      }}>
        <span style={{ color: 'var(--cyan)', fontWeight: 700 }}>Notes</span>
        <span className="mute"> : </span>
        <span style={{ color: 'var(--fg-dim)' }}>[{lastIndex}] {_limitAtlasLines(last, 5)}</span>
        {notes.length > 1 && (
          <span className="mute" style={{ marginLeft: 6 }}>+{notes.length - 1} earlier</span>
        )}
      </div>
    );
  };

  // Counts per state for the header summary
  const counts = todos.reduce((acc, t) => {
    const cfg = stateCfg(t.state);
    acc[cfg.label] = (acc[cfg.label] || 0) + 1;
    return acc;
  }, {});

  // ── header tab strip
  const Tab = ({ id, label }) => (
    <span onClick={() => setView(id)} style={{
      cursor: 'pointer', padding: '4px 10px', fontSize: 10, letterSpacing: '0.06em',
      textTransform: 'uppercase', fontFamily: 'var(--mono)',
      color: view === id ? 'var(--fg)' : 'var(--fg-mute)',
      background: view === id ? 'var(--bg-2)' : 'transparent',
      border: `1px solid ${view === id ? 'var(--accent)' : 'var(--line)'}`,
      borderRadius: 2,
    }}>{label}</span>
  );

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <div style={{
        padding: '8px 12px', borderBottom: '1px solid var(--line)',
        display: 'flex', alignItems: 'center', gap: 6, fontSize: 'var(--ui-control-font-size)', flexWrap: 'wrap',
      }}>
        <span className="mute" style={{ fontFamily: 'var(--mono)' }}>{done}/{todos.length}</span>
        {/* color-coded count chips per state */}
        {['in-progress','pending','done','approved','completed','rejected'].filter(k => counts[k]).map(k => {
          const c = stateCfg(k === 'done' ? 'done' : k.replace('-', '_'));
          return (
            <AtlasStatusBadge key={k} status={k} label={c.label} count={counts[k]} compact soft />
          );
        })}
        <span style={{ flex: 1 }} />
        <span title="Clear all todos"
          onClick={() => { if (confirm('Clear all todos?')) window.atlasData.clearTodos(); }}
          style={{
            cursor: 'pointer', fontSize: 10, padding: '2px 8px',
            border: '1px solid var(--line)', color: 'var(--fg-mute)',
            borderRadius: 2,
          }}>✕ clear</span>
        <span className="mute" style={{ fontSize: 10, letterSpacing: '0.06em', textTransform: 'uppercase' }}>view</span>
        <Tab id="compact" label="list" />
        <Tab id="detail" label="detail" />
        <Tab id="graph" label="graph" />
      </div>

      {/* Progress bar — at-a-glance "X / Y approved" with green fill */}
      {todos.length > 0 && (
        <div style={{ padding: '6px 12px 4px', borderBottom: '1px solid var(--line)',
                       background: 'var(--bg-2)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between',
                         fontSize: 10, fontFamily: 'var(--mono)',
                         color: 'var(--fg-mute)', marginBottom: 3 }}>
            <span>progress</span>
            <span><b style={{ color: 'var(--ok)' }}>{done}</b> / {todos.length} approved</span>
          </div>
          <div style={{ height: 4, background: 'var(--bg-3)',
                         border: '1px solid var(--line)', borderRadius: 2,
                         overflow: 'hidden' }}>
            <div style={{
              height: '100%',
              width: `${todos.length ? Math.round(100 * done / todos.length) : 0}%`,
              background: '#3fb950',
              transition: 'width 240ms ease-out',
            }} />
          </div>
        </div>
      )}

      <div style={{ flex: 1, overflow: 'auto' }}>
        {view === 'compact' && (() => {
          // Group by status order: in_progress → pending → completed →
          // rejected → approved (approved collapsed by default since it's
          // usually the long tail of "done" todos that the user no longer
          // needs to scan).
          const groupOf = (t) => {
            const s = t.state;
            if (s === 'active' || s === 'in_progress') return 'in_progress';
            if (s === 'completed') return 'completed';
            if (s === 'approved' || s === 'done') return 'approved';
            if (s === 'rejected') return 'rejected';
            return 'pending';
          };
          const groups = { in_progress: [], pending: [], completed: [], rejected: [], approved: [] };
          todos.forEach(t => groups[groupOf(t)].push(t));
          const order = ['in_progress', 'pending', 'completed', 'rejected', 'approved'];
          const labels = {
            in_progress: 'IN PROGRESS', pending: 'PENDING',
            completed: 'COMPLETED',     rejected: 'REJECTED', approved: 'APPROVED',
          };
          // approved + rejected default-collapsed; in-progress/pending/completed default-open
          const collapsedDefault = { approved: true, rejected: true };
          const isCollapsed = (g) => collapsedTodoGroups[g] !== undefined
            ? collapsedTodoGroups[g] : (collapsedDefault[g] || false);
          const toggleGroup = (g) => setCollapsedTodoGroups(prev =>
            ({ ...prev, [g]: !isCollapsed(g) }));
          return (
            <div style={{ padding: '4px 0' }}>
              {order.map(g => {
                const items = groups[g];
                if (!items.length) return null;
                const collapsed = isCollapsed(g);
                const cfg = stateCfg(g === 'in_progress' ? 'in_progress' : g);
                return (
                  <div key={g}>
                    {/* Group divider — uppercase label, click to toggle */}
                    <div
                      onClick={() => toggleGroup(g)}
                      style={{
                        display: 'flex', alignItems: 'center', gap: 6,
                        padding: '4px 12px 2px', cursor: 'pointer',
                        fontFamily: 'var(--mono)', fontSize: 10,
                        letterSpacing: '0.1em', textTransform: 'uppercase',
                        color: cfg.color, userSelect: 'none',
                      }}
                    >
                      <span>{collapsed ? '▸' : '▾'}</span>
                      <AtlasStatusBadge status={g} label={labels[g]} count={items.length} compact />
                      <span style={{ flex: 1, height: 1, background: 'var(--line)',
                                      opacity: 0.5, marginLeft: 6 }} />
                    </div>
                    {!collapsed && items.map(t => {
                      const open = openId === t.id;
                      return (
                        <div key={t.id}>
                          <div
                            onClick={() => setOpenId(open ? null : t.id)}
                            style={{
                              display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 16px',
                              alignItems: 'baseline', gap: 8, padding: '6px 12px',
                              cursor: 'pointer', fontFamily: 'var(--mono)', fontSize: 13,
                              background: t.state === 'active' || t.state === 'in_progress'
                                ? 'color-mix(in oklch, var(--accent) 8%, transparent)'
                                : 'transparent',
                              borderLeft: (t.state === 'active' || t.state === 'in_progress')
                                ? '2px solid var(--accent)' : '2px solid transparent',
                            }}
                          >
                            <span style={{ color: t.state === 'pending' ? 'var(--fg-dim)' : 'var(--fg)' }}>{t.title}</span>
                            <span className="mute" style={{ fontSize: 10 }}>{open ? '▾' : '▸'}</span>
                          </div>
                          {open && (
                            <div className="fade-in" style={{
                              padding: '10px 14px 12px 64px',
                              fontSize: 13,
                              lineHeight: 1.68,
                              color: 'var(--fg-dim)',
                              borderLeft: '2px solid var(--line-2)',
                              borderTop: '1px solid var(--line)',
                              marginLeft: 12,
                              marginRight: 12,
                              background: 'color-mix(in oklch, var(--bg-2) 92%, var(--fg) 8%)',
                            }}>
                              <TodoStructuredBody todo={t} />
                              <TodoNotes todo={t} />
                              <TodoReason todo={t} />
                              {t.deps && t.deps.length > 0 && (
                                <div style={{ marginTop: 6, fontSize: 'var(--ui-control-font-size)', lineHeight: 1.5 }}>
                                  <span className="mute">deps:</span>{' '}
                                  {t.deps.map(d => <span key={d} className="acc">§{d} </span>)}
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                );
              })}
            </div>
          );
        })()}

        {view === 'detail' && (
          <div>
            {todos.map(t => {
              const cfg = stateCfg(t.state);
              return (
                <div key={t.id} style={{
                  padding: '10px 14px', borderBottom: '1px solid var(--line)',
                  background: t.state === 'active' ? 'var(--bg-2)' : 'transparent',
                  borderLeft: t.state === 'active' ? '2px solid var(--accent)' : '2px solid transparent',
                }}>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
                    <AtlasStatusBadge status={t.state} label={cfg.label} compact soft />
                    <span className="mute" style={{ fontSize: 11 }}>{t.section}</span>
                    <span style={{ fontWeight: t.state === 'active' ? 600 : 500, flex: 1, fontSize: 13, color: 'var(--fg)' }}>{t.title}</span>
                  </div>
                  <div style={{
                    color: 'var(--fg-dim)',
                    fontSize: 13,
                    marginTop: 6,
                    marginLeft: 22,
                    lineHeight: 1.62,
                  }}>
                    <TodoStructuredBody todo={t} />
                  </div>
                  <div style={{ marginLeft: 22 }}>
                    <TodoNotes todo={t} />
                    <TodoReason todo={t} />
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {view === 'graph' && <TodoGraph todos={todos} openId={openId} setOpenId={setOpenId} />}
      </div>
    </div>
  );
};


const OrchestratorChatPanel = ({ activeIp: activeIpProp = '' } = {}) => {
  const [rooms, setRooms]       = React.useState([]);
  const [room, setRoom]         = React.useState('_global');
  const [messages, setMessages] = React.useState([]);
  const [context, setContext]   = React.useState(null);
  const [contextOpen, setContextOpen] = React.useState(true);
  const [draft, setDraft]       = React.useState('');
  const [busy, setBusy]         = React.useState(false);
  const [error, setError]       = React.useState('');
  const threadRef               = React.useRef(null);

  const fetchRooms = React.useCallback(async () => {
    try {
      const r = await fetch('/api/chat/rooms', { credentials: 'include' });
      if (!r.ok) { setError(`rooms: ${r.status}`); return; }
      const data = await r.json();
      setRooms(data.rooms || []);
    } catch (e) { setError(String(e)); }
  }, []);

  const fetchMessages = React.useCallback(async (rm) => {
    try {
      const r = await fetch(`/api/chat/${encodeURIComponent(rm)}/messages?limit=100`,
                            { credentials: 'include' });
      if (!r.ok) { setError(`messages: ${r.status}`); setMessages([]); return; }
      const data = await r.json();
      // API returns newest-first; reverse for chronological render.
      setMessages((data.messages || []).slice().reverse());
      setError('');
    } catch (e) { setError(String(e)); }
  }, []);

  const fetchContext = React.useCallback(async (rm) => {
    try {
      const r = await fetch(`/api/chat/${encodeURIComponent(rm)}/context`,
                            { credentials: 'include' });
      if (!r.ok) { setContext(null); return; }
      setContext(await r.json());
    } catch (_) { setContext(null); }
  }, []);

  // Initial + room-change loads.
  React.useEffect(() => { fetchRooms(); }, [fetchRooms]);
  React.useEffect(() => {
    fetchMessages(room);
    fetchContext(room);
  }, [room, fetchMessages, fetchContext]);

  // Default room: prefer the workspace's active IP, fall back to _global.
  React.useEffect(() => {
    if (!rooms.length) return;
    const names = new Set(rooms.map((r) => r.name));
    if (activeIpProp && names.has(activeIpProp)) { setRoom(activeIpProp); return; }
    if (names.has(room)) return;
    setRoom(names.has('_global') ? '_global' : rooms[0].name);
  }, [rooms, activeIpProp, room]);

  // Live updates over the existing WS bus.
  React.useEffect(() => {
    if (!window.backend || typeof window.backend.subscribe !== 'function') {
      return undefined;
    }
    const off = window.backend.subscribe('chat_message', (m) => {
      if (!m || m.room == null) return;
      if (m.room !== room) {
        // Could bump unread badge here; left to a follow-up.
        return;
      }
      setMessages((prev) => {
        // Dedup by id — broadcast_all fans out to every session, so the
        // sender's own client may see its own POST echo.
        if (prev.some((x) => x.id === m.id)) return prev;
        return prev.concat([{
          id: m.id,
          ip_id: m.ip_id,
          user_id: m.user_id,
          display_name: m.display_name,
          content: m.content,
          created_at: m.created_at,
        }]);
      });
    });
    return off;
  }, [room]);

  // Auto-scroll thread on new message.
  React.useEffect(() => {
    const el = threadRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  const submit = async () => {
    const text = draft.trim();
    if (!text || busy) return;
    setBusy(true);
    try {
      const r = await fetch(`/api/chat/${encodeURIComponent(room)}/send`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: text }),
      });
      if (!r.ok) {
        const body = await r.json().catch(() => ({}));
        setError(body.error || `POST ${r.status}`);
      } else {
        setDraft('');
        setError('');
      }
    } catch (e) { setError(String(e)); }
    finally { setBusy(false); }
  };

  const onKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit(); }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0,
                  padding: '8px 10px', gap: 8 }}>
      {/* Room switcher */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <span style={{ fontSize: 'var(--ui-control-font-size)', color: 'var(--fg-mute)' }}>Room:</span>
        <select
          value={room}
          onChange={(e) => setRoom(e.target.value)}
          style={{ flex: 1, fontSize: 12, padding: '2px 4px',
                   background: 'var(--bg-soft)', color: 'var(--fg)',
                   border: '1px solid var(--border)' }}>
          {rooms.length === 0 && <option value="">(no accessible rooms)</option>}
          {rooms.map((r) => (
            <option key={r.name} value={r.name}>
              {r.scope === 'global' ? 'all IPs (_global)' : r.name}
            </option>
          ))}
        </select>
        <button onClick={() => { fetchRooms(); fetchContext(room); fetchMessages(room); }}
                title="refresh"
                style={{ fontSize: 'var(--ui-control-font-size)', padding: '2px 6px' }}>⟳</button>
      </div>

      {/* Context card */}
      {context && (
        <div className="orchestrator-card"
             style={{ border: '1px solid var(--border)', borderRadius: 4,
                      padding: 6, fontSize: 'var(--ui-control-font-size)', background: 'var(--bg-soft)' }}>
          <div onClick={() => setContextOpen((v) => !v)}
               style={{ cursor: 'pointer', display: 'flex', justifyContent: 'space-between' }}>
            <strong>Orchestrator · {room}</strong>
            <span style={{ color: 'var(--fg-mute)' }}>{contextOpen ? '▾' : '▸'}</span>
          </div>
          {contextOpen && (
            <div style={{ marginTop: 6, lineHeight: 1.4 }}>
              {room === '_global' ? (
                <div>
                  <div style={{ color: 'var(--fg-mute)' }}>IPs in workspace:</div>
                  {(context.ips || []).map((ip) => (
                    <div key={ip.id || ip.name} style={{ marginLeft: 6 }}>
                      <code>{ip.name}</code>
                      {' · '}
                      <span>{ip.latest_workflow || '—'}/{ip.run_status || '—'}</span>
                      {' · open='}{ip.open_blockers}
                      {' · done='}{ip.completed}
                    </div>
                  ))}
                </div>
              ) : (
                <div>
                  <div>
                    <code>{(context.ip || {}).name}</code>
                    {' · '}
                    <span style={{ color: 'var(--fg-mute)' }}>
                      {(context.workflow || {}).latest_run
                        ? `${context.workflow.latest_run.workflow}/${context.workflow.latest_run.status}`
                        : 'no run yet'}
                    </span>
                  </div>
                  {(context.todos && context.todos.counts) && (
                    <div style={{ marginTop: 4 }}>
                      <span style={{ color: 'var(--fg-mute)' }}>todos:</span>{' '}
                      {Object.entries(context.todos.counts).map(([k, v]) => (
                        <span key={k} style={{ marginRight: 6 }}>{k}={v}</span>
                      ))}
                    </div>
                  )}
                  {(context.todos && context.todos.top_blockers || []).slice(0, 3).map((b) => (
                    <div key={b.id} style={{ marginLeft: 6, color: 'var(--warn)' }}>
                      blocker[{b.status}]: {b.title}
                    </div>
                  ))}
                  {(context.recent_events || []).slice(0, 4).map((e, i) => (
                    <div key={i} style={{ marginLeft: 6, color: 'var(--fg-mute)' }}>
                      {e.kind === 'llm'
                        ? `llm · ${e.model} · $${(e.cost_usd || 0).toFixed(3)}`
                        : `· ${e.event_type || e.kind}`}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Message thread */}
      <div ref={threadRef}
           style={{ flex: 1, minHeight: 100, overflowY: 'auto',
                    border: '1px solid var(--border)', borderRadius: 4,
                    padding: 6, fontSize: 12, background: 'var(--bg-soft)' }}>
        {messages.length === 0 ? (
          <div style={{ color: 'var(--fg-mute)', fontStyle: 'italic' }}>
            No messages in this room yet. Posts are sent to the running agent on its next iteration.
          </div>
        ) : (
          messages.map((m) => {
            // Agent messages are identified by the 🤖 prefix in display_name
            // set by core/chat_responder.py. Same author would never start a
            // human message with that emoji (auth flow rejects display names
            // containing 🤖 — see record_chat_message). Visual cue: left-rail
            // accent + slightly different background so the thread reads as
            // a real conversation.
            const isAgent = typeof m.display_name === 'string'
              && m.display_name.startsWith('🤖');
            return (
              <div
                key={m.id}
                className={isAgent ? 'chat-bubble chat-bubble-agent' : 'chat-bubble'}
                style={{
                  marginBottom: 6,
                  padding: '4px 6px',
                  borderRadius: 4,
                  background: isAgent ? 'var(--bg-elevated, var(--bg))' : 'var(--bg)',
                  borderLeft: isAgent ? '3px solid var(--accent, #4a9eff)' : 'none',
                }}>
                <div style={{ display: 'flex', justifyContent: 'space-between',
                              fontSize: 10,
                              color: isAgent ? 'var(--accent, #4a9eff)' : 'var(--fg-mute)' }}>
                  <strong>{m.display_name || m.user_id || 'user'}</strong>
                  <span>{m.created_at ? new Date(m.created_at * 1000).toLocaleTimeString() : ''}</span>
                </div>
                <div style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                  {m.content}
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Composer */}
      <div style={{ display: 'flex', gap: 4 }}>
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={onKey}
          rows={2}
          placeholder={
            rooms.length === 0
              ? 'No rooms available'
              : `Type feedback for ${room}…  (Enter to send, Shift+Enter newline)`
          }
          disabled={rooms.length === 0 || busy}
          style={{ flex: 1, fontSize: 12, padding: '4px 6px', resize: 'vertical',
                   background: 'var(--bg-soft)', color: 'var(--fg)',
                   border: '1px solid var(--border)' }}/>
        <button onClick={submit} disabled={busy || !draft.trim() || rooms.length === 0}
                style={{ fontSize: 12, padding: '4px 10px' }}>
          {busy ? '…' : 'Send'}
        </button>
      </div>

      {error && (
        <div style={{ fontSize: 10, color: 'var(--err)' }}>{error}</div>
      )}
    </div>
  );
};


const GitPanel = ({ activeIp: activeIpProp = '' } = {}) => {
  const [branch, setBranch] = React.useState('');
  const [ahead, setAhead]   = React.useState(0);
  const [behind, setBehind] = React.useState(0);
  const [files, setFiles]   = React.useState([]);
  const [commits, setCommits] = React.useState([]);
  const [error, setError]   = React.useState('');
  const [selected, setSelected] = React.useState(null);
  const [diff, setDiff]     = React.useState('');
  const [diffLoading, setDiffLoading] = React.useState(false);
  const [message, setMessage] = React.useState('');
  const [busy, setBusy]     = React.useState('');   // '' | 'commit' | 'push'
  const [lastResult, setLastResult] = React.useState(null);

  const [activeIp, setActiveIp] = React.useState(activeIpProp || '');

  React.useEffect(() => {
    setActiveIp(activeIpProp || '');
    setSelected(null);
    setDiff('');
  }, [activeIpProp]);

  const refresh = React.useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (activeIp) params.set('ip', activeIp);
      const qs = params.toString();
      const r = await fetch('/api/git/status' + (qs ? `?${qs}` : ''));
      const d = await r.json();
      setBranch(d.branch || ''); setAhead(d.ahead || 0); setBehind(d.behind || 0);
      setFiles(d.files || []); setError(d.error || '');
    } catch (e) { setError(String(e)); }
    try {
      const params = new URLSearchParams({ limit: '80' });
      if (activeIp) params.set('ip', activeIp);
      const r = await fetch('/api/git/log?' + params.toString());
      const d = await r.json();
      setCommits(Array.isArray(d.commits) ? d.commits : []);
    } catch (_) {}
  }, [activeIp]);

  React.useEffect(() => { refresh(); const id = setInterval(refresh, 5000); return () => clearInterval(id); }, [refresh]);

  // When user clicks a file, fetch its diff (cached as `selected`)
  React.useEffect(() => {
    if (!selected) { setDiff(''); return; }
    let cancelled = false;
    setDiffLoading(true);
    const params = new URLSearchParams({ path: selected });
    if (activeIp) params.set('ip', activeIp);
    fetch('/api/git/diff?' + params.toString())
      .then(r => r.json())
      .then(d => { if (!cancelled) { setDiff(d.diff || d.error || ''); setDiffLoading(false); } })
      .catch(e => { if (!cancelled) { setDiff(String(e)); setDiffLoading(false); } });
    return () => { cancelled = true; };
  }, [selected, files.length, activeIp]);

  const doCommit = async () => {
    if (!message.trim()) { alert('Commit message required.'); return; }
    setBusy('commit');
    try {
      const r = await fetch('/api/git/commit', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, add_all: true, ip: activeIp }),
      });
      const d = await r.json();
      setLastResult({ kind: 'commit', ...d });
      if (d.ok) setMessage('');
      refresh();
    } finally { setBusy(''); }
  };

  const doPush = async () => {
    if (!confirm('Push branch "' + (branch || '?') + '" to origin?')) return;
    setBusy('push');
    try {
      const r = await fetch('/api/git/push', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ip: activeIp }),
      });
      const d = await r.json();
      setLastResult({ kind: 'push', ...d });
      refresh();
    } finally { setBusy(''); }
  };

  const stagedCount   = files.filter(f => f.staged).length;
  const unstagedCount = files.filter(f => f.unstaged).length;

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0, fontSize: 12 }}>
      {/* Branch / ahead-behind / refresh */}
      <div style={{
        padding: '6px 10px', borderBottom: '1px solid var(--line)',
        display: 'flex', alignItems: 'center', gap: 8, fontFamily: 'var(--mono)',
      }}>
        <span className="mute" style={{ fontSize: 10 }}>branch</span>
        <span className="acc" style={{ fontWeight: 600 }}>{branch || '(none)'}</span>
        {ahead  > 0 && <span className="ok"  style={{ fontSize: 10 }}>↑{ahead}</span>}
        {behind > 0 && <span className="warn" style={{ fontSize: 10 }}>↓{behind}</span>}
        <span style={{ flex: 1 }} />
        <span onClick={refresh} title="refresh git status"
              style={{ cursor: 'pointer', color: 'var(--accent)', fontSize: 13, padding: '0 6px' }}>↻</span>
      </div>

      {/* Commit history — clickable; emits atlas-git-show so the
          center pane can render the unified diff for the chosen
          commit (matches "branch / changes / commit msg + click =
          show diff in center" UX request). */}
      {commits.length ? (
        <div style={{
          borderBottom: '1px solid var(--line)',
          maxHeight: 220,
          overflow: 'auto',
          background: 'var(--bg-2)',
        }}>
          <div className="mute" style={{
            padding: '4px 10px', fontSize: 10,
            textTransform: 'uppercase', letterSpacing: '0.08em',
            borderBottom: '1px solid var(--line)',
          }}>history · {commits.length}</div>
          {commits.map(c => (
            <div
              key={c.sha}
              onClick={() => {
                window.dispatchEvent(new CustomEvent('atlas-git-show', {
                  detail: { sha: c.sha, ip: activeIp, subject: c.subject },
                }));
              }}
              title={`${c.short} · ${c.author} · ${c.date}\n${c.subject}\n+${c.added || 0} −${c.removed || 0} across ${c.files || 0} file(s)`}
              style={{
                display: 'grid',
                gridTemplateColumns: 'auto 1fr auto',
                gap: 6,
                padding: '3px 10px',
                cursor: 'pointer',
                fontFamily: 'var(--mono)',
                fontSize: 'var(--ui-control-font-size)',
                borderLeft: '2px solid transparent',
              }}
              onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-3)'}
              onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
            >
              <span style={{ color: 'var(--accent)', fontWeight: 600 }}>{c.short}</span>
              <span className="trunc" style={{ color: 'var(--fg)' }}>{c.subject}</span>
              <span style={{ fontSize: 10, color: 'var(--fg-mute)' }}>
                {c.added != null && <span className="ok"  style={{ marginRight: 2 }}>+{c.added}</span>}
                {c.removed != null && <span className="err">−{c.removed}</span>}
              </span>
            </div>
          ))}
        </div>
      ) : null}

      {/* File list */}
      <div style={{ borderBottom: '1px solid var(--line)', maxHeight: 200, overflow: 'auto' }}>
        {error && <div className="warn" style={{ padding: '8px 10px', fontSize: 11 }}>{error}</div>}
        {!error && files.length === 0 && (
          <div className="mute" style={{ padding: '10px', fontSize: 11 }}>
            (working tree clean)
          </div>
        )}
        {files.map((f, i) => {
          const sg = _statusGlyph(f.status || '  ');
          const isSel = selected === f.path;
          return (
            <div key={i}
              onClick={() => setSelected(f.path)}
              title={f.path + ' · ' + (f.status || '')}
              style={{
                display: 'grid', gridTemplateColumns: '20px 1fr auto', gap: 6,
                padding: '3px 10px', cursor: 'pointer', fontFamily: 'var(--mono)',
                background: isSel ? 'color-mix(in oklch, var(--accent) 14%, transparent)' : 'transparent',
                borderLeft: isSel ? '2px solid var(--accent)' : '2px solid transparent',
              }}>
              <span style={{ color: sg.staged.color, fontWeight: 700 }}>{sg.staged.ch}{sg.work.ch}</span>
              <span className="trunc" style={{ color: 'var(--fg)' }}>{f.path}</span>
              <span style={{ fontSize: 10 }}>
                {f.added != null && <span className="ok"  style={{ marginRight: 2 }}>+{f.added}</span>}
                {f.removed != null && <span className="err">−{f.removed}</span>}
              </span>
            </div>
          );
        })}
      </div>

      {/* Diff viewer for selected file */}
      <div style={{ flex: 1, overflow: 'auto', borderBottom: '1px solid var(--line)' }}>
        {!selected && (
          <div className="mute" style={{ padding: '10px', fontSize: 11 }}>
            Click a file above to view its diff.
          </div>
        )}
        {selected && (
          <pre className="code" style={{
            margin: 0, padding: '8px 10px', fontSize: 'var(--ui-control-font-size)', lineHeight: 1.5,
            whiteSpace: 'pre', fontFamily: 'var(--mono)',
          }}>
            {diffLoading ? 'loading…' :
              (diff || '').split('\n').map((line, i) => {
                let color = 'var(--fg)';
                let bg = 'transparent';
                if (line.startsWith('+++') || line.startsWith('---') || line.startsWith('diff ') || line.startsWith('@@') || line.startsWith('index ')) {
                  color = 'var(--accent)';
                } else if (line.startsWith('+')) {
                  color = '#7ee787'; bg = 'color-mix(in oklch, #3fb950 12%, transparent)';
                } else if (line.startsWith('-')) {
                  color = '#ffa198'; bg = 'color-mix(in oklch, #f85149 12%, transparent)';
                }
                return <div key={i} style={{ color, background: bg }}>{line || ' '}</div>;
              })
            }
          </pre>
        )}
      </div>

      {/* Commit composer */}
      <div style={{ padding: '8px 10px', display: 'flex', flexDirection: 'column', gap: 6 }}>
        <div className="mute" style={{ fontSize: 10, letterSpacing: '0.06em', textTransform: 'uppercase' }}>
          {files.length} change{files.length === 1 ? '' : 's'}
          {stagedCount   > 0 && <span className="ok"   style={{ marginLeft: 6 }}>{stagedCount} staged</span>}
          {unstagedCount > 0 && <span className="warn" style={{ marginLeft: 6 }}>{unstagedCount} unstaged</span>}
        </div>
        <textarea
          value={message}
          onChange={e => setMessage(e.target.value)}
          placeholder="Commit message — first line = summary, blank line + body for details"
          rows={3}
          style={{
            background: 'var(--bg-3)', border: '1px solid var(--line)',
            borderRadius: 2, padding: '6px 8px', fontSize: 12,
            fontFamily: 'var(--mono)', color: 'var(--fg)', resize: 'vertical',
            outline: 'none', minHeight: 50,
          }}
        />
        <div style={{ display: 'flex', gap: 6 }}>
          <button
            className="btn primary"
            disabled={busy !== '' || !message.trim() || files.length === 0}
            onClick={doCommit}
            style={{ flex: 1 }}>
            {busy === 'commit' ? 'committing…' : 'commit ↵'}
          </button>
          <button
            className="btn"
            disabled={busy !== '' || !branch}
            onClick={doPush}>
            {busy === 'push' ? 'pushing…' : ('push ↑' + (ahead ? ahead : ''))}
          </button>
        </div>
        {lastResult && (
          <div style={{
            fontSize: 10, padding: '4px 6px', borderRadius: 2,
            background: lastResult.ok ? 'color-mix(in oklch, var(--ok) 12%, transparent)'
                                       : 'color-mix(in oklch, var(--warn) 12%, transparent)',
            color: lastResult.ok ? 'var(--ok)' : 'var(--warn)',
            fontFamily: 'var(--mono)', whiteSpace: 'pre-wrap', wordBreak: 'break-word',
            maxHeight: 80, overflow: 'auto',
          }}>
            <b>{lastResult.kind}{lastResult.ok ? ' ✓' : ' ✗'}</b>
            {lastResult.stdout && '\n' + lastResult.stdout.trim()}
            {lastResult.stderr && '\n' + lastResult.stderr.trim()}
            {lastResult.error && '\n' + lastResult.error}
          </div>
        )}
      </div>
    </div>
  );
};


// Phase 13g window exports — workspace.jsx aliases these back.
window.AskUserPrompt = AskUserPrompt;
window.ProgressPanel = ProgressPanel;
window.TodoPanel = TodoPanel;
window.OrchestratorChatPanel = OrchestratorChatPanel;
window.GitPanel = GitPanel;
// AgentStatusPanel extracted to agent-status-panel.jsx in Phase 19.

})();
