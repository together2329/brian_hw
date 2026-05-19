// pipeline.jsx — ATLAS Pipeline top-level screen.
//
// Live, full-screen stage dispatcher and situation board.
// Replaces the mock-data Architect screen as the primary "what is the
// pipeline doing right now?" surface. Wires GET /api/pipeline/state
// (2 s poll + WS push) and POST /api/pipeline/dispatch.
//
// Components attached to window:
//   window.AtlasPipeline   — top-level 3-column screen
//   window.DagMap          — top-down 15-stage SVG flow
//   window.StageCard       — per-stage situation card
//   window.MiniScoresheet  — 3-5 KPI dot row
//   window.DispatchRail    — chained-stage primary dispatch
//
// Reuses window.PIPELINE_STAGES / PIPELINE_LABEL / fullPipeline /
// ArchitectChat from soc-architect.jsx (loaded earlier in index.html).
//
// React via in-browser Babel — no imports, no ES modules, no TS.

(function injectPipelineHelpers() {
  // Hard-coded copy of _PIPELINE_STAGE_DEPS from src/atlas_api_jobs.py.
  // The frontend can't introspect Python; refresh by hand if the
  // backend graph ever changes (it has been stable for months).
  window.PIPELINE_STAGE_DEPS = {
    'ssot': [],
    'fl-model': ['ssot'],
    'cl-model': ['ssot'],
    'equivalence': ['fl-model', 'cl-model'],
    'rtl': ['equivalence'],
    'lint': ['rtl'],
    'tb': ['rtl'],
    'syn': ['rtl'],
    'sim': ['tb'],
    'coverage': ['sim'],
    'sim-debug': ['sim'],
    'goal-audit': ['sim'],
    'sta': ['syn'],
    'pnr': ['syn'],
    'sta-post': ['pnr'],
  };
  window.PIPELINE_STAGE_WORKFLOW = {
    ssot: 'ssot-gen',
    'fl-model': 'fl-model-gen',
    'cl-model': 'fl-model-gen',
    equivalence: 'fl-model-gen',
    rtl: 'rtl-gen',
    lint: 'lint',
    tb: 'tb-gen',
    sim: 'sim',
    coverage: 'coverage',
    'sim-debug': 'sim_debug',
    syn: 'syn',
    sta: 'sta',
    pnr: 'pnr',
    'sta-post': 'sta-post',
    'goal-audit': 'goal-audit',
  };
  window.PIPELINE_WORKFLOW_PRIMARY_STAGE = {
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
    'goal-audit': 'goal-audit',
  };
  window.PIPELINE_WORKSPACE_WORKFLOWS = new Set(Object.keys(window.PIPELINE_WORKFLOW_PRIMARY_STAGE));
  window.pipelineWorkflowForStage = function pipelineWorkflowForStage(stageId) {
    return (window.PIPELINE_STAGE_WORKFLOW || {})[stageId] || stageId || '';
  };
  window.pipelineDefaultWorkspacePath = function pipelineDefaultWorkspacePath(ip, workflow, stageId, evidencePaths) {
    const paths = Array.isArray(evidencePaths) ? evidencePaths.filter(Boolean) : [];
    const wf = String(workflow || '').trim();
    const id = String(stageId || '').trim();
    if (paths.length && paths[0] !== `${ip}/tb/cocotb/`) return paths[0];
    if (!ip) return '';
    if (wf === 'ssot-gen' || id === 'ssot') return `${ip}/yaml/${ip}.ssot.yaml`;
    if (wf === 'fl-model-gen' || id === 'fl-model' || id === 'cl-model' || id === 'equivalence') return `${ip}/model/functional_model.py`;
    if (wf === 'rtl-gen' || id === 'rtl') return `${ip}/rtl/rtl_authoring_status.md`;
    if (wf === 'lint' || id === 'lint') return `${ip}/lint/lint_report.txt`;
    if (wf === 'tb-gen' || id === 'tb') return `${ip}/tb/cocotb/test_${ip}.py`;
    if (wf === 'sim' || id === 'sim') return `${ip}/sim/sim_summary.json`;
    if (wf === 'coverage' || id === 'coverage') return `${ip}/sim/coverage_report.md`;
    if (wf === 'sim_debug' || id === 'sim-debug') return `${ip}/sim/sim_debug_report.md`;
    if (wf === 'syn' || id === 'syn') return `${ip}/syn/syn_report.md`;
    if (wf === 'sta' || id === 'sta') return `${ip}/sta/sta_report.md`;
    if (wf === 'pnr' || id === 'pnr') return `${ip}/pnr/pnr_report.md`;
    if (wf === 'sta-post' || id === 'sta-post') return `${ip}/sta/sta_post_report.md`;
    if (wf === 'goal-audit' || id === 'goal-audit') return `${ip}/sim/fl_rtl_goal_audit.json`;
    return paths[0] || '';
  };
  window.openPipelineWorkflowWorkspace = function openPipelineWorkflowWorkspace({ ip, workflow, stageId, path } = {}) {
    const wf = String(workflow || window.pipelineWorkflowForStage(stageId) || '').trim();
    const targetIp = String(ip || '').trim();
    if (!targetIp || !wf) return;
    const stage = stageId || (window.PIPELINE_WORKFLOW_PRIMARY_STAGE || {})[wf] || '';
    const resolvedPath = path || (
      window.pipelineDefaultWorkspacePath
        ? window.pipelineDefaultWorkspacePath(targetIp, wf, stage, [])
        : ''
    );
    try {
      window.dispatchEvent(new CustomEvent('atlas:open_workflow_workspace', {
        detail: { ip: targetIp, workflow: wf, stage, path: resolvedPath, source: 'pipeline' },
      }));
    } catch (_) {}
  };

  // Phase bands used to group stage cards. Mirrors the layout sketch in
  // /Users/brian/.claude/plans/i-need-team-chat-magical-koala.md §Layout.
  // Phase taxonomy matches ATLAS_UI_ENHANCEMENT/Pipeline Image.html mockup:
  // 6 phases — SSOT, MODELS, RTL, BRANCH, VERIFY·EDA, SIGNOFF.
  window.PIPELINE_PHASES = [
    { id: 'SSOT',       stages: ['ssot'] },
    { id: 'MODELS',     stages: ['fl-model', 'cl-model', 'equivalence'] },
    { id: 'RTL',        stages: ['rtl'] },
    { id: 'BRANCH',     stages: ['lint', 'tb', 'sim'] },
    { id: 'VERIFY·EDA', stages: ['sim-debug', 'coverage', 'syn', 'sta'] },
    { id: 'SIGNOFF',    stages: ['pnr', 'sta-post', 'goal-audit'] },
  ];

  // Graph-first Pipeline layout. Coordinates are SVG viewBox units for a
  // 1200×620 map; CSS scales the whole map to the available viewport.
  window.PIPELINE_SWIMLANES = [
    { id: 'req',    title: 'REQUIREMENTS / SSOT', x: 55,   width: 170 },
    { id: 'model',  title: 'MODELS / GOALS',      x: 250,  width: 185 },
    { id: 'build',  title: 'RTL / TB AUTHORING',  x: 462,  width: 200 },
    { id: 'verify', title: 'VERIFY / DEBUG',      x: 696,  width: 210 },
    { id: 'eda',    title: 'EDA SIGNOFF',         x: 938,  width: 150 },
    { id: 'orch',   title: 'ORCHESTRATOR',        x: 1106, width: 150 },
  ];
  window.PIPELINE_VIRTUAL_NODES = {
    orchestrator: { label: 'Orchestrator', sub: 'route / retry / stale', state: 'virtual' },
    handoff:      { label: 'Handoff JSON', sub: 'pending / claimed', state: 'virtual' },
    take:         { label: '/take',        sub: 'workspace claim', state: 'virtual' },
    worker:       { label: 'Worker',       sub: 'workflow lease', state: 'virtual' },
  };
  window.PIPELINE_NODE_LAYOUT = {
    ssot:         { lane: 'req',    y: 276 },
    'fl-model':  { lane: 'model',  y: 178 },
    'cl-model':  { lane: 'model',  y: 276 },
    equivalence: { lane: 'model',  y: 374 },
    rtl:          { lane: 'build',  y: 276 },
    lint:         { lane: 'build',  y: 168 },
    tb:           { lane: 'build',  y: 384 },
    sim:          { lane: 'verify', y: 276 },
    coverage:     { lane: 'verify', y: 168 },
    'sim-debug':  { lane: 'verify', y: 384 },
    'goal-audit': { lane: 'verify', y: 492 },
    syn:          { lane: 'eda',    y: 150 },
    sta:          { lane: 'eda',    y: 250 },
    pnr:          { lane: 'eda',    y: 350 },
    'sta-post':   { lane: 'eda',    y: 450 },
    orchestrator: { lane: 'orch',   y: 178 },
    handoff:      { lane: 'orch',   y: 278 },
    take:         { lane: 'orch',   y: 378 },
    worker:       { lane: 'orch',   y: 478 },
  };
  window.PIPELINE_FLOW_DEFS = [
    {
      id: 'full',
      name: 'Full IP pipeline',
      summary: 'SSOT through model, RTL, verification, coverage, and signoff audit.',
      stages: ['ssot', 'fl-model', 'cl-model', 'equivalence', 'rtl', 'lint', 'tb', 'sim', 'coverage', 'sim-debug', 'syn', 'sta', 'pnr', 'sta-post', 'goal-audit'],
    },
    {
      id: 'rtl-repair',
      name: 'RTL repair loop',
      summary: 'Owner-classified sim-debug mismatch returns to RTL and revalidates downstream evidence.',
      stages: ['sim-debug', 'orchestrator', 'handoff', 'worker', 'rtl', 'lint', 'tb', 'sim', 'coverage', 'sim-debug'],
    },
    {
      id: 'tb-sim',
      name: 'TB / sim loop',
      summary: 'Scoreboard or testbench repair loop without changing RTL authority.',
      stages: ['sim-debug', 'orchestrator', 'handoff', 'worker', 'tb', 'sim', 'coverage', 'sim-debug'],
    },
    {
      id: 'coverage',
      name: 'Coverage closure',
      summary: 'Coverage gap drives model/goal/TB updates, then reruns sim and coverage.',
      stages: ['coverage', 'orchestrator', 'handoff', 'tb', 'sim', 'coverage', 'goal-audit'],
    },
    {
      id: 'ppa',
      name: 'PPA signoff',
      summary: 'RTL implementation enters synthesis, timing, place-route, and post-route STA.',
      stages: ['rtl', 'syn', 'sta', 'pnr', 'sta-post'],
    },
    {
      id: 'json-take',
      name: 'JSON handoff / take',
      summary: 'No live worker: save durable handoff, then a workspace claims it later.',
      stages: ['sim-debug', 'orchestrator', 'handoff', 'take', 'worker', 'rtl'],
    },
  ];
  window.pipelineActualStages = function pipelineActualStages(stages) {
    const real = new Set(window.PIPELINE_STAGES || []);
    return (stages || []).filter(s => real.has(s));
  };
  window.pipelinePolicyPayload = function pipelinePolicyPayload() {
    const normRun = (value) => {
      const v = String(value || '').trim().toLowerCase().replace(/_/g, '-');
      if (v === 'eng') return 'engineering';
      if (v === 'sign-off') return 'signoff';
      return ['starter', 'engineering', 'signoff'].indexOf(v) >= 0 ? v : 'engineering';
    };
    const normExec = (value) => {
      const v = String(value || '').trim().toLowerCase().replace(/_/g, '-');
      if (v === 'single' || v === 'worker' || v === 'serial') return 'single-worker';
      if (v === 'orch' || v === 'multi-worker') return 'orchestrator';
      return ['single-worker', 'orchestrator'].indexOf(v) >= 0 ? v : 'orchestrator';
    };
    let savedRun = '';
    let savedExec = '';
    try {
      savedRun = localStorage.getItem('atlasRunMode') || '';
      savedExec = localStorage.getItem('atlasExecMode') || '';
    } catch (_) {}
    return {
      run_mode: normRun(window.ATLAS_RUN_MODE || savedRun),
      exec_mode: normExec(window.ATLAS_EXEC_MODE || savedExec),
    };
  };

  // ── Color / glyph map for state badges ──────────────────────────
  // Backend states from /api/pipeline/state contract (see plan).
  // Falls back to generic 'idle' if the value isn't recognised.
  window.PIPELINE_STATE_META = {
    passed:  { color: 'var(--ok)',     glyph: '✓', label: 'passed'  },
    ok:      { color: 'var(--ok)',     glyph: '✓', label: 'passed'  },
    running: { color: 'var(--cyan)',   glyph: '▶', label: 'running' },
    run:     { color: 'var(--cyan)',   glyph: '▶', label: 'running' },
    failed:  { color: 'var(--err)',    glyph: '!', label: 'failed'  },
    err:     { color: 'var(--err)',    glyph: '!', label: 'failed'  },
    blocked: { color: 'var(--warn)',   glyph: '⏸', label: 'blocked' },
    stale:   { color: 'var(--warn)',   glyph: '⊘', label: 'stale'   },
    locked:  { color: 'var(--fg-mute)',glyph: '◌', label: 'locked'  },
    ready:   { color: 'var(--fg-mute)',glyph: '◯', label: 'ready'   },
    idle:    { color: 'var(--fg-mute)',glyph: '◯', label: 'idle'    },
    pending: { color: 'var(--fg-mute)',glyph: '◯', label: 'pending' },
  };
  window.pipelineStateMeta = function pipelineStateMeta(state) {
    return window.PIPELINE_STATE_META[state] || window.PIPELINE_STATE_META.idle;
  };
})();

// ─── DagMap ────────────────────────────────────────────────────────
//
// Top-down SVG flow of all 15 pipeline stages. Edges from the hard-coded
// PIPELINE_STAGE_DEPS. Layout is deterministic by topological rank
// (root nodes are rank 0, every dependent is max(parent.rank)+1) so
// the diagram is stable across renders. Each node is a 28×28 token
// with a 2-letter glyph (PIPELINE_LABEL truncated). Running nodes
// pulse via .pipe-node-running CSS class. Running edges show an
// SVG <animateMotion> token traveling along the path.
//
// Click a node → scroll the matching StageCard into view (smooth).
window.DagMap = function DagMap({ state, onNodeClick }) {
  const stages = window.PIPELINE_STAGES || [];
  const labels = window.PIPELINE_LABEL  || {};
  const deps   = window.PIPELINE_STAGE_DEPS || {};
  const stagesState = (state && state.stages) || {};

  // Topological ranks → which row each node sits on.
  const rank = React.useMemo(() => {
    const r = {};
    const visit = (id, seen) => {
      if (id in r) return r[id];
      if (seen.has(id)) return 0;
      seen.add(id);
      const parents = deps[id] || [];
      const maxParent = parents.length
        ? Math.max(...parents.map(p => visit(p, seen)))
        : -1;
      r[id] = maxParent + 1;
      seen.delete(id);
      return r[id];
    };
    stages.forEach(s => visit(s, new Set()));
    return r;
  }, [stages, deps]);

  // Group stages per row. Order within a row is the canonical
  // PIPELINE_STAGES order (so cl-model sits beside fl-model, etc.).
  const rows = React.useMemo(() => {
    const acc = {};
    stages.forEach(s => {
      const row = rank[s] || 0;
      (acc[row] = acc[row] || []).push(s);
    });
    return acc;
  }, [stages, rank]);

  const rowKeys = Object.keys(rows).map(Number).sort((a, b) => a - b);
  const NODE_W = 28, NODE_H = 28, COL_GAP = 18, ROW_GAP = 32;
  const maxCols = Math.max(...rowKeys.map(r => rows[r].length), 1);
  const SVG_W = Math.max(560, maxCols * (NODE_W + COL_GAP) + COL_GAP);
  const SVG_H = (rowKeys.length || 1) * (NODE_H + ROW_GAP) + ROW_GAP;

  // Compute (x,y) center for every node so edges line up exactly.
  const positions = {};
  rowKeys.forEach(r => {
    const row = rows[r];
    const rowW = row.length * NODE_W + (row.length - 1) * COL_GAP;
    const startX = (SVG_W - rowW) / 2 + NODE_W / 2;
    row.forEach((s, i) => {
      positions[s] = {
        x: startX + i * (NODE_W + COL_GAP),
        y: ROW_GAP / 2 + r * (NODE_H + ROW_GAP) + NODE_H / 2,
      };
    });
  });

  const handleNodeClick = (stageId) => {
    if (typeof onNodeClick === 'function') onNodeClick(stageId);
  };

  // Edges: one path per (parent → child) where parent has a position.
  // Running edges (parent state === running) get an animated 4 px
  // token via <animateMotion mpath/>.
  const edges = [];
  stages.forEach(child => {
    (deps[child] || []).forEach(parent => {
      if (!positions[parent] || !positions[child]) return;
      const a = positions[parent], b = positions[child];
      // Slight S-curve so crossings stay readable.
      const midY = (a.y + b.y) / 2;
      const d = `M ${a.x} ${a.y + NODE_H/2} C ${a.x} ${midY}, ${b.x} ${midY}, ${b.x} ${b.y - NODE_H/2}`;
      const parentState = (stagesState[parent] && stagesState[parent].state) || 'idle';
      const isRunning = parentState === 'running' || parentState === 'run';
      edges.push({ key: `${parent}->${child}`, d, parent, child, running: isRunning });
    });
  });

  return (
    <div className="pipe-dagmap">
      <svg width={SVG_W} height={SVG_H} viewBox={`0 0 ${SVG_W} ${SVG_H}`}
           style={{ display: 'block', maxWidth: '100%', height: 'auto' }}>
        <defs>
          <marker id="pipe-arrow" viewBox="0 0 6 6" refX="5" refY="3"
                  markerWidth="5" markerHeight="5" orient="auto-start-reverse">
            <path d="M 0 0 L 6 3 L 0 6 z" fill="var(--fg-mute)" />
          </marker>
        </defs>
        {edges.map(e => (
          <g key={e.key}>
            <path d={e.d} fill="none" stroke="var(--line-2)" strokeWidth="1"
                  markerEnd="url(#pipe-arrow)" id={`pipe-edge-${e.key}`} />
            {e.running && (
              <circle r="3" fill="var(--cyan)">
                <animateMotion dur="1.6s" repeatCount="indefinite">
                  <mpath xlinkHref={`#pipe-edge-${e.key}`} />
                </animateMotion>
              </circle>
            )}
          </g>
        ))}
        {stages.map(s => {
          const p = positions[s];
          if (!p) return null;
          const stageState = (stagesState[s] && stagesState[s].state) || 'idle';
          const meta = window.pipelineStateMeta(stageState);
          const label = (labels[s] || s).slice(0, 2).toUpperCase();
          const isRunning = stageState === 'running' || stageState === 'run';
          return (
            <g key={s} className="pipe-node-g"
               transform={`translate(${p.x - NODE_W/2}, ${p.y - NODE_H/2})`}
               onClick={() => handleNodeClick(s)}
               style={{ cursor: 'pointer' }}>
              <rect width={NODE_W} height={NODE_H} rx="4" ry="4"
                    className={`pipe-node ${isRunning ? 'pipe-node-running' : ''}`}
                    data-state={stageState} />
              <text x={NODE_W / 2} y={NODE_H / 2 + 4}
                    textAnchor="middle"
                    fontFamily="var(--mono)"
                    fontSize="10"
                    className="pipe-node-glyph"
                    data-state={stageState}>
                {label}
              </text>
              <title>{`${labels[s] || s} · ${meta.label}`}</title>
            </g>
          );
        })}
      </svg>
    </div>
  );
};

// ─── PipelineFlowMap ──────────────────────────────────────────────
//
// Graph-first replacement for the old small DAG strip. This renders the
// IP pipeline as a full canvas with swimlanes, muted global context, and
// an amber selected route with numbered handoff/order badges.
function PendingQABanner({ ip }) {
  const [pending, setPending] = React.useState(0);
  const [items, setItems] = React.useState([]);
  React.useEffect(() => {
    if (!ip) { setPending(0); setItems([]); return; }
    let dead = false;
    const fetchQA = async () => {
      try {
        const r = await fetch(`/api/ssot/qa?ip=${encodeURIComponent(ip)}`);
        if (!r.ok) return;
        const j = await r.json();
        if (dead) return;
        const list = Array.isArray(j.items) ? j.items
                   : Array.isArray(j.pending) ? j.pending
                   : Array.isArray(j.cards) ? j.cards
                   : [];
        const openOnly = list.filter(x => {
          const s = String(x.status || x.state || '').toLowerCase();
          return s === '' || s === 'pending' || s === 'open' || s === 'unanswered';
        });
        setPending(Number(j.pending_count || openOnly.length || 0));
        setItems(openOnly.slice(0, 3));
      } catch (_) {}
    };
    fetchQA();
    const t = setInterval(fetchQA, 5000);
    return () => { dead = true; clearInterval(t); };
  }, [ip]);
  if (!pending) return null;
  return (
    <div className="pipe-qa-banner" role="alert">
      <span className="pipe-qa-icon">⚠</span>
      <span className="pipe-qa-text">
        <b>{pending}</b> QA card{pending > 1 ? 's' : ''} pending — orchestrator paused.{' '}
        Answer to resume.
      </span>
      <a className="pipe-qa-link" href={`/ssot/${encodeURIComponent(ip)}/qa`}
         target="_blank" rel="noreferrer">Answer QA →</a>
      {items.length > 0 && (
        <div className="pipe-qa-items">
          {items.map((it, i) => (
            <span key={i} className="pipe-qa-chip" title={it.detail || it.question || ''}>
              {String(it.topic || it.question || `Q${i+1}`).slice(0, 36)}
            </span>
          ))}
          {pending > items.length && (
            <span className="pipe-qa-more">+{pending - items.length} more</span>
          )}
        </div>
      )}
    </div>
  );
}

// Phase 3: surface the orchestrator's `ask_user` pause as a visible banner.
// The orchestrator loop persists run.status="paused" and the latest step's
// verdict="awaiting_user" with decision_json.args.question. Until the user
// replies via the right-side chat the run stays paused, so we poll the
// active_run endpoint and render the question prominently.
function OrchestratorAskUserBanner({ ip }) {
  const [question, setQuestion] = React.useState('');
  const [runId, setRunId] = React.useState('');
  React.useEffect(() => {
    if (!ip) { setQuestion(''); setRunId(''); return; }
    let dead = false;
    const fetchActive = async () => {
      try {
        const r = await fetch(`/api/orchestrator/active_run?ip=${encodeURIComponent(ip)}`);
        if (!r.ok) return;
        const j = await r.json();
        if (dead) return;
        const run = j.run || null;
        const step = j.latest_step || null;
        const paused = run && run.status === 'paused';
        const awaiting = step && step.verdict === 'awaiting_user';
        if (paused && awaiting) {
          const args = (step.decision_json && step.decision_json.args) || {};
          setQuestion(String(args.question || '').trim());
          setRunId(run.id || '');
        } else {
          setQuestion('');
          setRunId('');
        }
      } catch (_) {}
    };
    fetchActive();
    const t = setInterval(fetchActive, 3000);
    return () => { dead = true; clearInterval(t); };
  }, [ip]);
  if (!question) return null;
  return (
    <div className="pipe-qa-banner" role="alert" data-source="orchestrator-ask-user">
      <span className="pipe-qa-icon">⏸</span>
      <span className="pipe-qa-text">
        <b>Human decision waiting</b> — orchestrator paused: {question}{' '}
        Answer in the right-side chat to resume.
      </span>
      <span className="pipe-qa-more" title={`run=${runId}`}>run {runId.slice(0, 8)}</span>
    </div>
  );
}

// ── PhaseStrip ────────────────────────────────────────────────────────────────
// Horizontal 6-phase summary strip above the flow map.
// Derives done/running/failed counts from stagesState (pipelineState.stages).
const PHASE_BANDS = [
  { num: 1, name: 'SSOT',       stages: ['ssot'] },
  { num: 2, name: 'MODELS',     stages: ['fl-model', 'cl-model', 'equivalence'] },
  { num: 3, name: 'RTL',        stages: ['rtl'] },
  { num: 4, name: 'BRANCH',     stages: ['lint', 'tb', 'sim', 'coverage', 'sim-debug'] },
  { num: 5, name: 'VERIFY·EDA', stages: ['syn', 'sta', 'pnr', 'sta-post'] },
  { num: 6, name: 'SIGNOFF',    stages: ['goal-audit'] },
];

function PhaseStrip({ stagesState }) {
  const ss = stagesState || {};
  const stateOf = (stageId) => {
    const raw = ss[stageId];
    if (!raw) return 'idle';
    if (typeof raw === 'string') return raw;
    return raw.state || raw.status || 'idle';
  };
  const phases = PHASE_BANDS.map((band) => {
    const known = (window.PIPELINE_STAGES || band.stages).length
      ? band.stages.filter(s => !(window.PIPELINE_STAGES) || (window.PIPELINE_STAGES || []).indexOf(s) >= 0)
      : band.stages;
    const n_total   = known.length;
    const n_done    = known.filter(s => ['passed', 'ok'].includes(stateOf(s))).length;
    const n_running = known.filter(s => ['running', 'run'].includes(stateOf(s))).length;
    const n_failed  = known.filter(s => ['failed','err','blocked','stale','locked'].includes(stateOf(s))).length;

    let phaseClass = '';
    if (n_running > 0)                          phaseClass = 'phase-running';
    else if (n_failed > 0)                      phaseClass = 'phase-blocked';
    else if (n_done === n_total && n_total > 0) phaseClass = 'phase-passed';

    let meta;
    if (n_running > 0) {
      meta = `▶ ${n_running} running · ${n_done}/${n_total} done`;
    } else {
      meta = `${n_done}/${n_total} done`;
    }

    return { ...band, phaseClass, meta };
  });

  const nodes = [];
  phases.forEach((ph, i) => {
    nodes.push(
      React.createElement('div', {
        key: ph.num,
        className: `pipe-flow-phase${ph.phaseClass ? ' ' + ph.phaseClass : ''}`,
      },
        React.createElement('span', { className: 'pipe-flow-phase-num' }, ph.num),
        React.createElement('span', { className: 'pipe-flow-phase-body' },
          React.createElement('span', { className: 'pipe-flow-phase-name' }, ph.name),
          React.createElement('span', { className: 'pipe-flow-phase-meta' }, ph.meta),
        ),
      )
    );
    if (i < phases.length - 1) {
      nodes.push(
        React.createElement('span', { key: `arrow-${i}`, className: 'pipe-flow-phase-arrow' }, '›')
      );
    }
  });

  return React.createElement('div', { className: 'pipe-flow-phases', role: 'navigation' }, ...nodes);
}
// ── /PhaseStrip ───────────────────────────────────────────────────────────────

// ── EnhancedFlowCanvas ────────────────────────────────────────────────────────
// SVG flow canvas matching ATLAS_UI_ENHANCEMENT/Pipeline Image.html: orchestrator
// bus bar on top, 6 vertical lanes (SSOT / MODELS / RTL / BRANCH / VERIFY·EDA /
// SIGNOFF), per-stage node boxes with state pills. Wired to pipelineState.stages
// so it reflects real run progress instead of static mockup data.
const ENH_LANE_X = { 1: 30, 2: 230, 3: 430, 4: 630, 5: 830, 6: 1030 };
const ENH_LANE_NAMES = { 1: 'SSOT', 2: 'MODELS', 3: 'RTL', 4: 'BRANCH', 5: 'VERIFY · EDA', 6: 'SIGNOFF' };
const ENH_LANE_HINTS = { 6: 'post-route' };
const ENH_ROW_Y = { 1: 140, 2: 220, 3: 300, 4: 380 };
const ENH_NODE_W = 168;
const ENH_NODE_H = 58;
const ENH_STAGE_LAYOUT = {
  ssot:         { lane: 1, row: 2 },
  'fl-model':   { lane: 2, row: 1 },
  'cl-model':   { lane: 2, row: 2 },
  equivalence:  { lane: 2, row: 3 },
  rtl:          { lane: 3, row: 2 },
  lint:         { lane: 4, row: 1 },
  tb:           { lane: 4, row: 2 },
  syn:          { lane: 4, row: 3 },
  'sim-debug':  { lane: 5, row: 1 },
  sim:          { lane: 5, row: 2 },
  sta:          { lane: 5, row: 3 },
  pnr:          { lane: 5, row: 4 },
  coverage:     { lane: 6, row: 2 },
  'goal-audit': { lane: 6, row: 3 },
  'sta-post':   { lane: 6, row: 4 },
};
const ENH_PILL_LABEL = { passed: 'passed', running: 'running', locked: 'locked', ready: 'ready', failed: 'failed', blocked: 'blocked', stale: 'stale' };
// Stage-specific default subtext for each state (canonical Pipeline Image
// rendering). Overridden by real `info.live_tail` / `info.locked_reason` when
// available so mock and live data both look right.
const ENH_SUBTEXT_DEFAULT = {
  ssot:         { passed: '12 sections · v0.4.1',          locked: 'awaiting source', ready: 'awaiting source' },
  'fl-model':   { passed: '2 174 packets · ✓ goals',       locked: 'awaiting ssot',   ready: 'awaiting ssot' },
  'cl-model':   { passed: 'cycle-acc · 4 ports',           locked: 'awaiting ssot',   ready: 'awaiting ssot' },
  equivalence:  { passed: 'FL ≡ CL · 8 192 vec',           locked: 'awaiting fl-model + cl-model', ready: 'awaiting fl-model + cl-model' },
  rtl:          { passed: 'rtl emitted',                   locked: 'awaiting equivalence',          ready: 'awaiting equivalence' },
  lint:         { passed: 'clean',                         locked: 'awaiting rtl',                  ready: 'awaiting rtl handoff' },
  tb:           { passed: 'tb emitted',                    locked: 'awaiting rtl',                  ready: 'awaiting rtl' },
  syn:          { passed: 'netlist emitted',               locked: 'awaiting rtl-gen',              ready: 'awaiting rtl-gen' },
  sim:          { passed: 'tests passed',                  locked: 'awaiting tb',                   ready: 'awaiting tb' },
  'sim-debug':  { passed: 'no escapes',                    locked: 'awaiting sim',                  ready: 'awaiting sim' },
  sta:          { passed: 'timing clean',                  locked: 'awaiting syn · leaf',           ready: 'awaiting syn · leaf' },
  pnr:          { passed: 'routed',                        locked: 'awaiting syn',                  ready: 'awaiting syn' },
  coverage:     { passed: 'goals met',                     locked: 'awaiting sim',                  ready: 'awaiting sim' },
  'sta-post':   { passed: 'post-route timing clean',       locked: 'awaiting pnr',                  ready: 'awaiting pnr' },
};
function enhSubText(stageId, info) {
  if (!info) {
    const def = ENH_SUBTEXT_DEFAULT[stageId];
    return (def && def.locked) || '';
  }
  if (info.state === 'running') {
    const iter = info.iter ? `iter ${info.iter}` : 'running';
    return info.model ? `${iter} · ${info.model}` : iter;
  }
  if (info.live_tail) return String(info.live_tail).slice(0, 32);
  const def = ENH_SUBTEXT_DEFAULT[stageId];
  if (def && def[info.state]) return def[info.state];
  if (info.locked_reason) return info.locked_reason;
  if (info.state === 'passed') return info.model ? info.model : 'passed';
  if (info.state === 'ready') return 'awaiting handoff';
  if (info.state === 'locked' || info.state === 'blocked') return 'awaiting upstream';
  if (info.state === 'failed') return 'failed — see evidence';
  return '';
}
// Canonical active-route paths from the Pipeline Image mockup, indexed by
// (fromStage, toStage). Same SVG paths as Pipeline Image.html lines 762-806.
const ENH_ROUTE_EDGES = [
  { id: 1,  from: 'ssot',         to: 'fl-model',    d: 'M 204 249 L 212 249 Q 218 249 218 243 L 218 175 Q 218 169 224 169 L 236 169' },
  { id: 2,  from: 'fl-model',     to: 'cl-model',    d: 'M 320 198 L 320 220' },
  { id: 3,  from: 'cl-model',     to: 'equivalence', d: 'M 320 278 L 320 300' },
  { id: 4,  from: 'equivalence',  to: 'rtl',         d: 'M 404 329 L 418 329 Q 425 329 425 323 L 425 255 Q 425 249 430 249 L 436 249' },
  { id: 5,  from: 'rtl',          to: 'lint',        d: 'M 604 249 L 612 249 Q 618 249 618 243 L 618 175 Q 618 169 624 169 L 636 169' },
  { id: 6,  from: 'rtl',          to: 'tb',          d: 'M 604 249 L 636 249' },
  { id: 7,  from: 'rtl',          to: 'syn',         d: 'M 604 249 L 614 249 Q 624 249 624 255 L 624 323 Q 624 329 630 329 L 636 329' },
  { id: 8,  from: 'tb',           to: 'sim',         d: 'M 804 249 L 836 249' },
  { id: 9,  from: 'sim',          to: 'sim-debug',   d: 'M 912 198 L 912 218', bidir: true, reverseD: 'M 928 220 L 928 200' },
  { id: 10, from: 'syn',          to: 'sta',         d: 'M 804 329 L 836 329' },
  { id: 11, from: 'syn',          to: 'pnr',         d: 'M 804 329 L 812 329 Q 818 329 818 335 L 818 403 Q 818 409 826 409 L 836 409' },
  { id: 12, from: 'pnr',          to: 'sta-post',    d: 'M 1004 409 L 1036 409' },
  { id: 13, from: 'sim',          to: 'coverage',    d: 'M 1004 249 L 1036 249' },
];
// Midpoint approximation for edge number badges (cx, cy)
const ENH_EDGE_BADGE_POS = {
  1:  { cx: 218, cy: 209 },
  2:  { cx: 332, cy: 211 },
  3:  { cx: 332, cy: 291 },
  4:  { cx: 425, cy: 289 },
  5:  { cx: 618, cy: 209 },
  6:  { cx: 620, cy: 263 },
  7:  { cx: 624, cy: 291 },
  8:  { cx: 820, cy: 263 },
  9:  { cx: 920, cy: 211 },
  10: { cx: 820, cy: 343 },
  11: { cx: 818, cy: 371 },
  12: { cx: 1020, cy: 423 },
  13: { cx: 1020, cy: 263 },
};
function EnhancedFlowCanvas({ pipelineState, ip, onSelectStage, selectedStage, selectedFlowId, onChain }) {
  const stagesState = (pipelineState && pipelineState.stages) || {};
  const orch = (pipelineState && pipelineState.orchestrator) || {};
  const runningEntry = Object.entries(stagesState).find(([, s]) => s && s.state === 'running');
  const runningStageId = runningEntry ? runningEntry[0] : '';
  const runningLane = runningStageId ? (ENH_STAGE_LAYOUT[runningStageId] || {}).lane : 0;
  const targetWorker = runningStageId ? `${runningStageId}-worker` : (orch.active_target || 'orchestrator');
  const pendingHandoffs = orch.pending_handoffs != null ? orch.pending_handoffs : 0;

  // Compute the flow set: stages that belong to the currently-selected flow.
  // Used to dim stages not in flow + filter route edges.
  const flowDefs = (typeof window !== 'undefined' && window.PIPELINE_FLOW_DEFS) || [];
  const flowDef = flowDefs.find(f => f.id === selectedFlowId) || flowDefs[0];
  const flowSet = new Set((flowDef && flowDef.stages) || []);
  const isAllFlow = !flowDef || flowDef.id === 'full';

  // Find a "ready" or "next" stage for the NEXT badge
  const nextStageId = (() => {
    for (const [sid, info] of Object.entries(stagesState)) {
      if (info && info.state === 'ready') return sid;
    }
    return '';
  })();

  // Find the most-recently-passed stage for "last ✓ from X" in the bus bar
  const lastPassedStageId = (() => {
    const order = ['ssot', 'fl-model', 'cl-model', 'equivalence', 'rtl', 'lint', 'tb', 'sim', 'syn', 'sim-debug', 'coverage', 'sta', 'pnr', 'sta-post'];
    let last = '';
    for (const sid of order) {
      if (stagesState[sid] && stagesState[sid].state === 'passed') last = sid;
    }
    return last;
  })();

  // Route edges: show the full canonical route by default (mockup behavior).
  // When a non-Full flow is selected, restrict edges to those whose both
  // endpoints are in the flow's stage set so the diagram reflects the path
  // the orchestrator would take for that flow.
  const activeEdges = ENH_ROUTE_EDGES.filter(e => {
    if (isAllFlow) return true;
    return flowSet.has(e.from) && flowSet.has(e.to);
  });
  const lastPassedWorker = lastPassedStageId ? `${lastPassedStageId}-worker` : '';

  // Render lanes
  const lanes = [1, 2, 3, 4, 5, 6].map((laneIdx) => {
    const x = ENH_LANE_X[laneIdx];
    return (
      <g key={`lane-${laneIdx}`} className="enh-lane">
        <rect x={x} y={76} width={180} height={382} rx={8} />
        <text x={x + 12} y={100} className="enh-lane-title">
          <tspan className="enh-lane-num">{laneIdx}.</tspan>
          <tspan dx={6}>{ENH_LANE_NAMES[laneIdx]}</tspan>
        </text>
        {ENH_LANE_HINTS[laneIdx] && (
          <text x={x + 12} y={116} className="enh-lane-hint">{ENH_LANE_HINTS[laneIdx]}</text>
        )}
      </g>
    );
  });

  // Bus-bar bidirectional arrows
  const arrows = [1, 2, 3, 4, 5, 6].map((laneIdx) => {
    const cx = ENH_LANE_X[laneIdx] + 82;
    const active = laneIdx === runningLane;
    const cls = `enh-arrow ${active ? 'active' : ''}`;
    return (
      <g key={`arrow-${laneIdx}`}>
        <path className={cls} d={`M ${cx} 46 L ${cx} 74`} markerEnd={active ? 'url(#enh-arr-active)' : 'url(#enh-arr-dispatch)'} />
        <path className={cls} d={`M ${cx + 16} 74 L ${cx + 16} 46`} markerEnd={active ? 'url(#enh-arr-active)' : 'url(#enh-arr-dispatch)'} />
      </g>
    );
  });

  // Stage nodes
  const nodes = Object.entries(ENH_STAGE_LAYOUT).map(([stageId, pos]) => {
    const info = stagesState[stageId] || {};
    const state = info.state || 'idle';
    const x = ENH_LANE_X[pos.lane] + 6;
    const y = ENH_ROW_Y[pos.row];
    const pillLabel = ENH_PILL_LABEL[state];
    const isNext = stageId === nextStageId;
    const isSelected = stageId === selectedStage;
    const inFlow = isAllFlow || flowSet.has(stageId);
    return (
      <g key={stageId}
         className={`enh-node ${isNext ? 'next' : ''} ${isSelected ? 'selected' : ''}`}
         data-state={state}
         data-in-flow={inFlow ? 'yes' : 'no'}
         transform={`translate(${x}, ${y})`}
         style={{ cursor: onSelectStage ? 'pointer' : 'default' }}
         onClick={(ev) => {
           if ((ev.metaKey || ev.ctrlKey) && typeof onChain === 'function') {
             ev.preventDefault();
             onChain(stageId);
           } else {
             onSelectStage && onSelectStage(stageId);
           }
         }}>
        <rect width={ENH_NODE_W} height={ENH_NODE_H} rx={7} />
        <text x={12} y={20} className="enh-node-title">{stageId}</text>
        <text x={12} y={36} className="enh-node-sub">{enhSubText(stageId, info)}</text>
        {pillLabel && (
          <g className="enh-pill" data-state={state} transform="translate(108, 6)">
            <rect width={52} height={15} rx={7.5} />
            <circle cx={8} cy={7.5} r={3} className="enh-pill-dot" />
            <text x={16} y={11}>{pillLabel}</text>
          </g>
        )}
        {isNext && (
          <g className="enh-next-badge" transform="translate(62, -18)">
            <rect width={44} height={14} rx={7} />
            <text x={22} y={10} textAnchor="middle">NEXT ▸</text>
          </g>
        )}
      </g>
    );
  });

  // Route edges (active route) — paths + numbered badges
  const edgePaths = activeEdges.map(e => (
    <g key={`edge-${e.id}`}>
      <path className="enh-edge-active" d={e.d} markerEnd="url(#enh-arr-active-route)" />
      {e.bidir && e.reverseD && (
        <path className="enh-edge-active" d={e.reverseD} markerEnd="url(#enh-arr-active-route)" />
      )}
    </g>
  ));
  const edgeBadges = null;  // edge number badges removed per user request

  // START badge (just left of ssot-gen at lane 1 row 2)
  const startBadge = (
    <g className="enh-start-badge" transform={`translate(${ENH_LANE_X[1] - 32}, ${ENH_ROW_Y[2] + 18})`}>
      <rect width={28} height={22} rx={5} />
      <text x={14} y={15} textAnchor="middle">START</text>
    </g>
  );

  return (
    <div className="enh-canvas-wrap">
      <svg className="enh-canvas-svg" viewBox="0 0 1240 540" role="img" aria-label="ATLAS pipeline flow canvas">
        <defs>
          <marker id="enh-arr-dispatch" viewBox="0 0 10 10" refX={9} refY={5} markerWidth={6} markerHeight={6} orient="auto">
            <path d="M0,0 L10,5 L0,10 z" fill="var(--enh-cyan, #5fc8eb)" />
          </marker>
          <marker id="enh-arr-active" viewBox="0 0 10 10" refX={9} refY={5} markerWidth={6} markerHeight={6} orient="auto">
            <path d="M0,0 L10,5 L0,10 z" fill="var(--enh-accent, #f2b632)" />
          </marker>
          <marker id="enh-arr-active-route" viewBox="0 0 10 10" refX={9} refY={5} markerWidth={6} markerHeight={6} orient="auto">
            <path d="M0,0 L10,5 L0,10 z" fill="var(--enh-accent, #f2b632)" />
          </marker>
        </defs>
        <g className="enh-orch-hub">
          <rect x={30} y={4} width={1180} height={42} rx={10} />
          <circle cx={55} cy={25} r={5} className="enh-orch-dot" />
          <text x={75} y={23} className="enh-orch-title">🎯 ORCHESTRATOR · {orch.enabled === false ? 'OFF' : 'ON'}</text>
          <text x={75} y={40} className="enh-orch-meta">
            TO <tspan className="enh-orch-meta-worker">{targetWorker}</tspan>
            {'  ·  pending '}<tspan className="enh-orch-meta-num">{pendingHandoffs}</tspan>
            {lastPassedWorker ? <tspan>{'  ·  last '}<tspan className="enh-orch-meta-ok">✓ from {lastPassedWorker}</tspan></tspan> : null}
          </text>
          <text x={1195} y={30} className="enh-orch-meta-hint" textAnchor="end">
            {flowDef ? `${flowDef.name} · ${flowDef.stages ? flowDef.stages.length : 0} stages` : '6 lanes · bidirectional control'}
          </text>
        </g>
        {arrows}
        {lanes}
        {startBadge}
        {edgePaths}
        {nodes}
        {edgeBadges}
      </svg>
    </div>
  );
}
// ── /EnhancedFlowCanvas ───────────────────────────────────────────────────────

// ── EnhancedDetailCards ──────────────────────────────────────────────────────
// Footer detail cards (Pipeline Image phase 2). Shows only ACTIVE stages
// (running / passed / ready) — count varies with state, not forced to 3.
// Cards mirror the mockup at lines 477-548 of Pipeline Image.html: state
// pill, KPI dots, optional progress bar, title, meta line, optional live tail,
// action buttons.
const ENH_CARD_GLYPH = { running: '▶', passed: '✓', ready: '○', failed: '✗', locked: '·', blocked: '·' };
const ENH_CARD_TITLE_TEXT = {
  ssot:         { passed: 'yaml/<ip>.ssot.yaml',                 ready: 'authoring SSOT' },
  'fl-model':   { passed: 'fl/fl_model.json — packets verified', ready: 'awaiting ssot' },
  'cl-model':   { passed: 'cl/cl_model.json — cycle-acc',        ready: 'awaiting ssot' },
  equivalence:  { passed: 'FL ≡ CL across 8 192 stimulus vectors', ready: 'awaiting fl-model + cl-model' },
  rtl:          { passed: 'rtl/axi_dma_top.sv — emitted',        running: 'rtl/axi_dma_top.sv — synthesizing channel arbiter', ready: 'awaiting equivalence' },
  lint:         { passed: 'lint clean — spyglass + verilator',   ready: 'awaiting rtl handoff' },
  tb:           { passed: 'tb/cocotb — emitted',                 ready: 'awaiting rtl' },
  sim:          { passed: 'sim — all tests passed',              running: 'sim driver scoreboarding test vector', ready: 'awaiting tb' },
  syn:          { passed: 'netlist emitted',                     ready: 'awaiting rtl-gen' },
  'sim-debug':  { passed: 'no escapes',                          ready: 'awaiting sim' },
  sta:          { passed: 'timing clean',                        ready: 'awaiting syn · leaf' },
  pnr:          { passed: 'routed',                              ready: 'awaiting syn' },
  coverage:     { passed: 'goals met',                           ready: 'awaiting sim' },
  'sta-post':   { passed: 'post-route timing clean',             ready: 'awaiting pnr' },
};
function enhCardTitle(stageId, info) {
  if (info && info.live_tail) return info.live_tail;
  const def = ENH_CARD_TITLE_TEXT[stageId];
  return (def && info && def[info.state]) || (info && info.state) || '';
}
function enhCardMeta(stageId, info) {
  if (!info) return '';
  const parts = [];
  if (info.iter) parts.push(`${info.iter} it`);
  if (info.elapsed_seconds) parts.push(`${info.elapsed_seconds}s`);
  if (info.model) parts.push(info.model);
  return parts.join(' · ');
}
function EnhancedDetailCards({ pipelineState, ip, onSelectStage, onChain }) {
  const stagesState = (pipelineState && pipelineState.stages) || {};
  // Surface every active stage in canonical order
  const ORDER = ['ssot', 'fl-model', 'cl-model', 'equivalence', 'rtl', 'lint', 'tb', 'sim', 'syn', 'sim-debug', 'coverage', 'sta', 'pnr', 'sta-post', 'goal-audit'];
  // 1 currently-running, 1 most-recently-passed, 1 next-ready, max 4.
  const running = [];
  let lastPassed = null;
  let nextReady = null;
  for (const sid of ORDER) {
    const info = stagesState[sid];
    if (!info) continue;
    if (info.state === 'running') running.push({ stageId: sid, info });
    else if (info.state === 'passed') lastPassed = { stageId: sid, info };
    else if (info.state === 'ready' && !nextReady) nextReady = { stageId: sid, info };
  }
  const cards = [];
  running.forEach(c => cards.push(c));
  if (lastPassed) cards.push(lastPassed);
  if (nextReady) cards.push(nextReady);
  if (!cards.length) return null;

  const renderCard = ({ stageId, info }) => {
    const state = info.state;
    const progress = state === 'running' ? Math.min(0.95, Math.max(0.1, info.progress || 0.5)) : null;
    const glyph = ENH_CARD_GLYPH[state] || '·';
    const title = enhCardTitle(stageId, info);
    const meta = enhCardMeta(stageId, info);
    const tail = state === 'running' && info.live_tail ? info.live_tail : '';
    const dots = (() => {
      // 5 dot KPI strip — pass for passed/running progress, dim for ready
      if (state === 'passed') return ['pass','pass','pass','pass','pass'];
      if (state === 'running') return ['pass','pass','warn','idle','idle'];
      return ['idle','idle','idle','idle','idle'];
    })();
    return (
      <div key={stageId} className="enh-card" data-state={state}
           onClick={(ev) => {
             if ((ev.metaKey || ev.ctrlKey) && typeof onChain === 'function') {
               ev.preventDefault();
               onChain(stageId);
             } else {
               onSelectStage && onSelectStage(stageId);
             }
           }}
           style={{ cursor: onSelectStage ? 'pointer' : 'default' }}>
        <div className="enh-card-hd">
          <span className="enh-card-glyph">{glyph}</span>
          <span className="enh-card-label">{stageId}</span>
          <span className="enh-card-state" data-s={state}>{state}</span>
        </div>
        <div className="enh-card-dots">
          {dots.map((kpi, i) => <span key={i} className="enh-dot" data-kpi={kpi} />)}
        </div>
        {progress != null && (
          <div className="enh-progress"><div className="enh-progress-fill" style={{ width: `${Math.round(progress * 100)}%` }} /></div>
        )}
        {title && <div className="enh-card-top">{title}</div>}
        {meta && <div className="enh-card-sec">{meta}</div>}
        {tail && <div className="enh-card-tail">~ {tail}</div>}
        <div className="enh-card-actions">
          {state === 'running' && (
            <>
              <button className="enh-btn" disabled>■ running</button>
              <button className="enh-btn ghost" type="button">open tail ↗</button>
            </>
          )}
          {state === 'passed' && (
            <>
              <button className="enh-btn" type="button">[ open evidence ▼ ]</button>
              <button className="enh-btn" type="button">▶ rerun</button>
            </>
          )}
          {state === 'ready' && (
            <>
              <button className="enh-btn" type="button">▶ run</button>
              <button className="enh-btn ghost" type="button">policy ↗</button>
            </>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="enh-cards-grid">
      {cards.map(renderCard)}
    </div>
  );
}
// ── /EnhancedDetailCards ─────────────────────────────────────────────────────


function WorkerOrchestraBar({ ip, onSelectTarget, currentTarget }) {
  const [data, setData] = React.useState({ orchestrator: {}, workers: [] });
  const [traceMap, setTraceMap] = React.useState({}); // worker -> latest event
  React.useEffect(() => {
    let dead = false;
    const fetchAll = async () => {
      try {
        const u = `/api/orchestrator/workers${ip ? `?ip=${encodeURIComponent(ip)}` : ''}`;
        const r = await fetch(u);
        if (!r.ok) return;
        const j = await r.json();
        if (!dead) setData(j || { workers: [] });
      } catch (_) {}
      try {
        if (!ip) return;
        const r2 = await fetch(`/api/orchestrator/trace?ip=${encodeURIComponent(ip)}&limit=30`);
        if (!r2.ok) return;
        const j2 = await r2.json();
        if (dead) return;
        const m = {};
        const evs = (j2 && j2.events) || [];
        for (const e of evs) {
          const a = e.actor || '';
          if (!a.endsWith('-worker')) continue;
          const wf = a.replace(/-worker$/, '');
          if (!m[wf] || m[wf].step < e.step) m[wf] = e;
        }
        setTraceMap(m);
      } catch (_) {}
    };
    fetchAll();
    const t = setInterval(fetchAll, 3000);
    return () => { dead = true; clearInterval(t); };
  }, [ip]);
  const orch = data.orchestrator || {};
  const workers = data.workers || [];
  const activeTarget = orch.active_target || null;
  const kindArrow = (k) => {
    if (!k) return { dir: 'none', color: 'muted', label: '' };
    if (k === 'http_send' || k === 'http_recv') return { dir: 'down', color: 'amber', label: 'dispatch' };
    if (k === 'http_accepted') return { dir: 'down', color: 'green', label: 'accepted' };
    if (k === 'http_rejected') return { dir: 'down', color: 'red', label: 'rejected' };
    if (k === 'run_completed') return { dir: 'up', color: 'cyan', label: 'completed' };
    if (k === 'gate_verdict') return { dir: 'up', color: 'purple', label: 'gate' };
    return { dir: 'none', color: 'muted', label: k };
  };
  const dataFlow = (w, ev) => {
    if (w.status !== 'ok') return 'down';
    if (w.running_count > 0) return 'dispatch';
    if (ev && ev.kind === 'run_completed') return 'return';
    return 'idle';
  };
  const flowArrow = (flow) => {
    if (flow === 'dispatch') return '↓';
    if (flow === 'return') return '↑';
    if (flow === 'down') return '✗';
    return '·';
  };
  const stateLabel = (w) => {
    if (w.status !== 'ok') return 'unreachable';
    if (w.running_count > 0) return `run #${w.running && w.running[0] && w.running[0].run_id ? w.running[0].run_id.slice(-6) : '?'}`;
    return 'idle';
  };
  const runningTotal = workers.filter(w => w.running_count > 0).length;
  return (
    <div className="pipe-orchestra worker-bar" data-on={orch.enabled ? 'yes' : 'no'}>
      <div className="pipe-orchestra-conductor">
        <div className="worker-bar-head">
          <span className="worker-bar-title pipe-orchestra-conductor-name">WORKERS</span>
          <span className="worker-bar-sub pipe-orchestra-conductor-activity">
            {activeTarget
              ? <><b>{runningTotal}</b> dispatched · target <b>{activeTarget}</b></>
              : <><b>{runningTotal}</b> running · orchestrator {orch.enabled ? 'ON' : 'OFF'}</>}
          </span>
          <span className="worker-bar-legend">
            <span className="leg-disp"><i>↓</i> dispatch</span>
            <span className="leg-ret"><i>↑</i> return</span>
            <span className="leg-idle"><i>·</i> idle</span>
            <span className="leg-down"><i>✗</i> down</span>
          </span>
        </div>
      </div>
      <div className="pipe-orchestra-workers worker-grid">
        {workers.map(w => {
          const ev = traceMap[w.workflow];
          const arrow = kindArrow(ev && ev.kind);
          const live = w.running_count > 0;
          const reachable = w.status === 'ok';
          const sel = currentTarget === w.workflow;
          const flow = dataFlow(w, ev);
          const opensWorkspace = window.PIPELINE_WORKSPACE_WORKFLOWS
            && window.PIPELINE_WORKSPACE_WORKFLOWS.has(w.workflow);
          return (
            <button key={w.workflow}
                    className="pipe-orchestra-worker worker-card"
                    data-flow={flow}
                    data-state={reachable ? (live ? 'running' : 'idle') : 'down'}
                    data-selected={sel ? 'yes' : 'no'}
                    onClick={() => {
                      if (opensWorkspace && window.openPipelineWorkflowWorkspace) {
                        window.openPipelineWorkflowWorkspace({ ip, workflow: w.workflow });
                        return;
                      }
                      if (onSelectTarget) onSelectTarget(w.workflow);
                    }}
                    title={opensWorkspace
                      ? `Open ${w.workflow} workspace and history`
                      : `Click to set chat target to ${w.workflow}`}>
              <span className="worker-card-arrow pipe-orchestra-arrow">
                {flowArrow(flow)}
              </span>
              <span className="worker-card-name pipe-orchestra-worker-head">
                <span className="pipe-orchestra-worker-dot" data-live={live ? 'yes' : 'no'} />
                <span className="pipe-orchestra-worker-name">{w.workflow}</span>
                {sel && <span className="to-badge pipe-orchestra-worker-sel">TO</span>}
              </span>
              <span className="worker-card-state pipe-orchestra-worker-state">
                {stateLabel(w)}
              </span>
              <span className="worker-card-model pipe-orchestra-worker-model">
                {w.model || w.profile || '?'}
                {w.reasoning_effort && (
                  <span className="pipe-orchestra-worker-effort"> {w.reasoning_effort}</span>
                )}
                {w.toolchain && (
                  <span className="pipe-orchestra-worker-toolchain"> {w.toolchain}</span>
                )}
              </span>
              <span className="worker-card-trace pipe-orchestra-worker-trace" data-color={arrow.color}>
                {ev ? `${arrow.label} · step #${ev.step}` : '— no recent trace'}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function OrchestratorTraceStrip({ ip }) {
  const [events, setEvents] = React.useState([]);
  const [open, setOpen] = React.useState(true);
  const [autoRefresh, setAutoRefresh] = React.useState(true);
  React.useEffect(() => {
    if (!ip) { setEvents([]); return; }
    let dead = false;
    const fetchOnce = async () => {
      try {
        const r = await fetch(`/api/orchestrator/trace?ip=${encodeURIComponent(ip)}&limit=20`);
        if (!r.ok) return;
        const j = await r.json();
        if (!dead) setEvents(Array.isArray(j.events) ? j.events.slice().reverse() : []);
      } catch (_) {}
    };
    fetchOnce();
    if (!autoRefresh) return () => { dead = true; };
    const t = setInterval(fetchOnce, 3000);
    return () => { dead = true; clearInterval(t); };
  }, [ip, autoRefresh]);
  const corrGroups = React.useMemo(() => {
    const grouped = new Map();
    for (const e of events) {
      const c = e.corr || 'no_corr';
      if (!grouped.has(c)) grouped.set(c, []);
      grouped.get(c).push(e);
    }
    return [...grouped.entries()].slice(0, 6);
  }, [events]);
  const lensGlyph = { interaction: '⇄', intermediate: '◐', result: '✓' };
  return (
    <div className="pipe-trace-strip" data-open={open ? 'yes' : 'no'}>
      <div className="pipe-trace-head">
        <button className="pipe-trace-toggle" onClick={() => setOpen(v => !v)} aria-expanded={open}>
          <span>ORCHESTRATOR TRACE</span>
          <span className="pipe-trace-count">{events.length} events</span>
          <span className="pipe-trace-chev">{open ? '▾' : '▸'}</span>
        </button>
        {open && (
          <label className="pipe-trace-auto">
            <input type="checkbox" checked={autoRefresh}
                   onChange={e => setAutoRefresh(e.currentTarget.checked)} />
            auto-refresh 3s
          </label>
        )}
      </div>
      {open && (
        <div className="pipe-trace-body">
          {events.length === 0 ? (
            <div className="pipe-trace-empty">No trace events yet for <b>{ip}</b>. Dispatch a worker to populate.</div>
          ) : corrGroups.map(([corr, group]) => (
            <div className="pipe-trace-group" key={corr}>
              <div className="pipe-trace-corr">{corr}</div>
              {group.map((e, i) => (
                <div key={`${corr}-${i}`} className="pipe-trace-row" data-lens={e.lens}>
                  <span className="pipe-trace-glyph">{lensGlyph[e.lens] || '·'}</span>
                  <span className="pipe-trace-step">#{e.step}</span>
                  <span className="pipe-trace-kind">{e.kind}</span>
                  <span className="pipe-trace-actor">{e.actor}{e.peer ? ` → ${e.peer}` : ''}</span>
                  <span className="pipe-trace-extra">
                    {e.status ? `${e.status} ` : ''}
                    {e.requested_workflow || e.run_id || e.detail || e.gate || e.reason || ''}
                  </span>
                </div>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

window.PipelineFlowMap = function PipelineFlowMap({
  ip,
  state,
  selectedFlowId,
  selectedStage,
  onSelectFlow,
  onSelectStage,
}) {
  const labels = window.PIPELINE_LABEL || {};
  const deps = window.PIPELINE_STAGE_DEPS || {};
  const stagesState = (state && state.stages) || {};
  const flows = window.PIPELINE_FLOW_DEFS || [];
  const flow = flows.find(f => f.id === selectedFlowId) || flows[0] || { stages: [] };
  const flowStages = flow.stages || [];
  const flowSet = new Set(flowStages);
  const flowEdges = new Set();
  for (let i = 0; i < flowStages.length - 1; i += 1) {
    flowEdges.add(`${flowStages[i]}->${flowStages[i + 1]}`);
  }

  // Hide the synthetic 'orch' lane (Orchestrator/Handoff/take/Worker) from
  // the DAG — those four are system state, not pipeline stages. They are
  // surfaced separately as a status strip above the canvas.
  const allLanes = window.PIPELINE_SWIMLANES || [];
  const visibleLanes = allLanes.filter(l => l.id !== 'orch');
  const laneById = {};
  visibleLanes.forEach(l => { laneById[l.id] = l; });
  const nodeLayout = window.PIPELINE_NODE_LAYOUT || {};
  const virtualNodes = window.PIPELINE_VIRTUAL_NODES || {};
  const actualStages = window.PIPELINE_STAGES || [];
  // Drop virtual nodes from the SVG entirely.
  const nodeIds = actualStages;
  const BOX_W = 168;
  const BOX_H = 58;
  // SVG width tracks the visible lanes (we dropped the synthetic ORCH lane).
  const lastLane = visibleLanes[visibleLanes.length - 1] || { x: 55, width: 170 };
  const W = lastLane.x + lastLane.width + 55;
  const H = 670;

  const pos = {};
  nodeIds.forEach(id => {
    const layout = nodeLayout[id];
    if (!layout) return;
    const lane = laneById[layout.lane];
    if (!lane) return;
    pos[id] = {
      x: lane.x + lane.width / 2,
      y: layout.y,
      lane: layout.lane,
    };
  });

  const baseEdges = [];
  actualStages.forEach(child => {
    (deps[child] || []).forEach(parent => {
      if (pos[parent] && pos[child]) baseEdges.push([parent, child]);
    });
  });
  const selectedEdges = [];
  for (let i = 0; i < flowStages.length - 1; i += 1) {
    const a = flowStages[i], b = flowStages[i + 1];
    if (pos[a] && pos[b]) selectedEdges.push([a, b, i + 1]);
  }

  const pathFor = (aId, bId) => {
    const a = pos[aId], b = pos[bId];
    if (!a || !b) return '';
    const startX = a.x + (b.x >= a.x ? BOX_W / 2 : -BOX_W / 2);
    const endX = b.x - (b.x >= a.x ? BOX_W / 2 : -BOX_W / 2);
    const startY = a.y;
    const endY = b.y;
    const dx = Math.max(55, Math.abs(endX - startX) * 0.45);
    const c1x = startX + (b.x >= a.x ? dx : -dx);
    const c2x = endX - (b.x >= a.x ? dx : -dx);
    return `M ${startX} ${startY} C ${c1x} ${startY}, ${c2x} ${endY}, ${endX} ${endY}`;
  };

  const midpoint = (aId, bId) => {
    const a = pos[aId], b = pos[bId];
    return { x: (a.x + b.x) / 2, y: (a.y + b.y) / 2 };
  };

  const nodeState = (id) => {
    if (virtualNodes[id]) return 'virtual';
    return (stagesState[id] && stagesState[id].state) || 'idle';
  };
  const nodeLabel = (id) => {
    if (virtualNodes[id]) return virtualNodes[id].label;
    return labels[id] || id;
  };
  const nodeSub = (id) => {
    if (virtualNodes[id]) return virtualNodes[id].sub;
    const data = stagesState[id] || {};
    const explicit = data.top || data.locked_reason || data.secondary;
    if (explicit) return explicit;
    const stName = String(data.state || 'idle').toLowerCase();
    const layout = nodeLayout[id] || {};
    if (stName === 'idle' && layout.lane === 'eda') return 'optional · not run';
    if (stName === 'idle' && !flowSet.has(id)) return 'not in selected flow';
    if (stName === 'idle') return 'no evidence yet';
    return id;
  };

  const orch = (state && state.orchestrator) || {};
  const orchOn = !!orch.enabled;
  const orchPending = Number(orch.pending_handoffs || 0);
  const orchClaimed = Number(orch.claimed_handoffs || 0);
  const orchWorker = orch.worker_bound || orch.worker || '';

  // Aggregate per-phase status for the progress strip at the top.
  // Mirrors PIPELINE_PHASES so the strip is always in sync with the lanes.
  const phases = window.PIPELINE_PHASES || [];
  const phaseStatus = phases.map((ph) => {
    const list = ph.stages || [];
    const c = { total: list.length, passed: 0, running: 0, failed: 0, blocked: 0 };
    list.forEach((s) => {
      const st = (stagesState[s] && stagesState[s].state) || 'idle';
      if (st === 'passed' || st === 'ok') c.passed += 1;
      else if (st === 'running' || st === 'run') c.running += 1;
      else if (st === 'failed' || st === 'err') c.failed += 1;
      else if (st === 'blocked' || st === 'stale') c.blocked += 1;
    });
    let phaseState = 'idle';
    if (c.failed) phaseState = 'failed';
    else if (c.running) phaseState = 'running';
    else if (c.total > 0 && c.passed === c.total) phaseState = 'passed';
    else if (c.blocked) phaseState = 'blocked';
    else if (c.passed) phaseState = 'partial';
    return { id: ph.id, state: phaseState, counts: c };
  });
  // Suggest the next idle stage in the selected flow so the user sees
  // exactly which dispatch button is the natural next action.
  const nextSuggested = (() => {
    for (const s of flowStages) {
      if (!pos[s]) continue;
      const st = nodeState(s);
      if (st === 'running' || st === 'run') return null;
      if (st === 'idle' || st === 'ready') return s;
    }
    return null;
  })();

  return (
    <div className="pipe-flow-map">
      <div className="pipe-flow-head">
        <div>
          <div className="pipe-flow-title">ATLAS IP Flow Map</div>
          <div className="pipe-flow-sub">
            Select a flow above. The bright route is what the orchestrator will run, repair, or hand off.
          </div>
        </div>
        <div className="pipe-flow-legend">
          <span><i className="pipe-leg-active" /> selected route</span>
          <span><i className="pipe-leg-running" /> running</span>
          <span><i className="pipe-leg-muted" /> context</span>
        </div>
      </div>
      <div className="pipe-flow-phases" role="navigation" aria-label="pipeline phases">
        {phaseStatus.map((ph, idx) => (
          <React.Fragment key={ph.id}>
            <div className={`pipe-flow-phase phase-${ph.state}`}>
              <span className="pipe-flow-phase-num">{idx + 1}</span>
              <span className="pipe-flow-phase-body">
                <span className="pipe-flow-phase-name">{ph.id}</span>
                <span className="pipe-flow-phase-meta">
                  {ph.counts.running ? `▶ ${ph.counts.running} running · ` : ''}
                  {ph.counts.failed ? `! ${ph.counts.failed} failed · ` : ''}
                  {ph.counts.passed}/{ph.counts.total} done
                </span>
              </span>
            </div>
            {idx < phaseStatus.length - 1 && (
              <span className="pipe-flow-phase-arrow" aria-hidden="true">›</span>
            )}
          </React.Fragment>
        ))}
      </div>
      {nextSuggested && (
        <div className="pipe-flow-next-hint" role="status">
          <span className="pipe-flow-next-icon">▶</span>
          <span>
            Next suggested step:{' '}
            <b>{nodeLabel(nextSuggested)}</b>
            <span className="mute"> — click the box to focus, then Run.</span>
          </span>
        </div>
      )}
      <div className="pipe-flow-orch-strip" data-on={orchOn ? 'yes' : 'no'}>
        <span className="pipe-flow-orch-label">Orchestrator</span>
        <span className="pipe-flow-orch-dot" data-on={orchOn ? 'yes' : 'no'} />
        <span className="pipe-flow-orch-state">{orchOn ? 'ON' : 'OFF'}</span>
        <span className="pipe-flow-orch-sep">·</span>
        <span>Pending handoffs: <b>{orchPending}</b></span>
        {orchClaimed > 0 && (
          <>
            <span className="pipe-flow-orch-sep">·</span>
            <span>Claimed: <b>{orchClaimed}</b></span>
          </>
        )}
        {orchWorker && (
          <>
            <span className="pipe-flow-orch-sep">·</span>
            <span>Worker: <b>{orchWorker}</b></span>
          </>
        )}
        <span className="pipe-flow-orch-hint">system status · not stages</span>
      </div>
      <div className="pipe-flow-canvas">
        <svg className="pipe-flow-svg" viewBox={`0 0 ${W} ${H}`} role="img"
             aria-label="ATLAS pipeline flow graph">
          <defs>
            <marker id="pipe-flow-arrow-muted" viewBox="0 0 8 8" refX="7" refY="4"
                    markerWidth="6" markerHeight="6" orient="auto">
              <path d="M0,0 L8,4 L0,8 z" className="pipe-flow-arrow-muted" />
            </marker>
            <marker id="pipe-flow-arrow-active" viewBox="0 0 8 8" refX="7" refY="4"
                    markerWidth="7" markerHeight="7" orient="auto">
              <path d="M0,0 L8,4 L0,8 z" className="pipe-flow-arrow-active" />
            </marker>
          </defs>

          {visibleLanes.map((lane, laneIdx) => (
            <g key={lane.id} className="pipe-flow-lane" data-lane={lane.id}>
              <rect x={lane.x} y="76" width={lane.width} height="542" rx="8" />
              <text x={lane.x + 12} y="100" className="pipe-flow-lane-title-text">
                <tspan className="pipe-flow-lane-num">{laneIdx + 1}.</tspan>
                <tspan dx="6">{lane.title}</tspan>
              </text>
              {lane.id === 'eda' && (
                <text x={lane.x + 12} y="116" className="pipe-flow-lane-hint">optional</text>
              )}
            </g>
          ))}

          {baseEdges.map(([a, b]) => {
            const key = `${a}->${b}`;
            const active = flowEdges.has(key);
            if (active) return null;
            return (
              <path key={key}
                    d={pathFor(a, b)}
                    className="pipe-flow-edge-muted"
                    markerEnd="url(#pipe-flow-arrow-muted)" />
            );
          })}

          {selectedEdges.map(([a, b, step]) => {
            const key = `${a}->${b}`;
            const mid = midpoint(a, b);
            return (
              <g key={`sel-${key}`}>
                <path d={pathFor(a, b)}
                      className="pipe-flow-edge-active"
                      markerEnd="url(#pipe-flow-arrow-active)" />
                <circle cx={mid.x} cy={mid.y} r="14" className="pipe-flow-step-dot" />
                <text x={mid.x} y={mid.y + 4} className="pipe-flow-step-num">{step}</text>
              </g>
            );
          })}

          {nodeIds.map(id => {
            const p = pos[id];
            if (!p) return null;
            const stateName = nodeState(id);
            const isActual = actualStages.indexOf(id) >= 0;
            const inFlow = flowSet.has(id);
            const selected = selectedStage === id;
            const running = stateName === 'running' || stateName === 'run';
            const isStart = id === 'ssot' && (stateName === 'idle' || stateName === 'ready');
            const isNext = nextSuggested === id;
            const klass = [
              'pipe-flow-node',
              inFlow ? 'in-flow' : 'context',
              selected ? 'selected' : '',
              running ? 'running' : '',
              isNext ? 'next' : '',
            ].filter(Boolean).join(' ');
            // Pick a short, readable label for the inline state chip.
            // Keep it ≤ 7 chars so it never overflows the 56 px pill.
            const pillLabel = (() => {
              if (running) return 'running';
              if (stateName === 'passed' || stateName === 'ok') return 'passed';
              if (stateName === 'failed' || stateName === 'err') return 'failed';
              if (stateName === 'blocked' || stateName === 'stale') return 'blocked';
              if (stateName === 'locked') return 'locked';
              if (stateName === 'ready') return 'ready';
              return 'idle';
            })();
            return (
              <g key={id}
                 className={klass}
                 data-state={stateName}
                 transform={`translate(${p.x - BOX_W / 2}, ${p.y - BOX_H / 2})`}
                 onClick={() => {
                   if (typeof onSelectStage === 'function') onSelectStage(id);
                   if (!inFlow && isActual && typeof onSelectFlow === 'function') onSelectFlow('full');
                 }}>
                <rect width={BOX_W} height={BOX_H} rx="7" />
                <text x="12" y="20" className="pipe-flow-node-title">{nodeLabel(id)}</text>
                <text x="12" y="36" className="pipe-flow-node-sub">{String(nodeSub(id) || '').slice(0, 26)}</text>
                <g className="pipe-flow-node-pill" data-state={stateName} transform={`translate(${BOX_W - 60}, 6)`}>
                  <rect width="52" height="15" rx="7.5" />
                  <circle cx="8" cy="7.5" r="3" className="pipe-flow-node-pill-dot" />
                  <text x="16" y="11" className="pipe-flow-node-pill-text">{pillLabel}</text>
                </g>
                {isStart && (
                  <g className="pipe-flow-start-badge" transform={`translate(-44, ${(BOX_H - 18) / 2})`}>
                    <rect width="42" height="18" rx="9" />
                    <text x="21" y="13" textAnchor="middle">START</text>
                  </g>
                )}
                {isNext && !isStart && (
                  <g className="pipe-flow-next-badge" transform={`translate(${BOX_W / 2 - 22}, ${BOX_H + 4})`}>
                    <rect width="44" height="14" rx="7" />
                    <text x="22" y="10" textAnchor="middle">NEXT ▸</text>
                  </g>
                )}
                <title>{`${nodeLabel(id)} · ${stateName}`}</title>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
};

// ─── MiniScoresheet ────────────────────────────────────────────────
//
// Render a 3–5 dot row from the backend's `scoresheet[]` array.
// Each value is one of 'pass' | 'warn' | 'fail' | 'idle'. Clicking a
// dot broadcasts an `open_evidence` custom event with the matching
// path from `evidence_paths[i]` so the existing FileViewer can pick
// it up (workspace.jsx wires the listener).
window.MiniScoresheet = function MiniScoresheet({ scoresheet, evidencePaths }) {
  const raw = Array.isArray(scoresheet) ? scoresheet : [];
  const fallbackPaths = Array.isArray(evidencePaths) ? evidencePaths : [];
  // Backend now returns labeled dots: {state, label, evidence_path}.
  // Older callers may still pass bare strings — keep both shapes working.
  const dots = raw.map((d, i) => {
    if (typeof d === 'string') {
      return { state: d, label: '', evidence_path: fallbackPaths[i] || fallbackPaths[0] || '' };
    }
    return {
      state: d && d.state ? d.state : 'idle',
      label: d && d.label ? d.label : '',
      evidence_path: (d && d.evidence_path) || fallbackPaths[i] || fallbackPaths[0] || '',
    };
  });
  if (!dots.length) return null;
  return (
    <div className="pipe-scoresheet">
      {dots.map((dot, i) => {
        const tip = `${dot.label || 'kpi ' + (i + 1)}: ${dot.state}` +
                    (dot.evidence_path ? `\n${dot.evidence_path}` : '');
        return (
          <span key={i}
                className="pipe-dot"
                data-kpi={dot.state || 'idle'}
                title={tip}
                onClick={() => {
                  if (!dot.evidence_path) return;
                  try {
                    window.dispatchEvent(new CustomEvent('atlas:open_evidence', {
                      detail: { path: dot.evidence_path, kpi: dot.state, label: dot.label, source: 'pipeline' },
                    }));
                  } catch (_) {}
                }} />
        );
      })}
    </div>
  );
};

// ─── StageCard ─────────────────────────────────────────────────────
//
// 5-row template (per plan §Components → StageCard):
//   1. glyph · label · state badge · iter / dur · model
//   2. mini scoresheet (3-5 KPI dots)
//   3. progress bar (running) | top evidence line (else)
//   4. secondary evidence string (`pkts 18 · tasks 4`)
//   5. live tail (running) | "[ open evidence ▾ ]" (passed) |
//      "blame → owner [ go fix owner ]" (failed)
// Bottom row holds "[▶ run]" → POST /api/pipeline/dispatch.
window.StageCard = function StageCard({ stageId, info, ip, onChain }) {
  const labels = window.PIPELINE_LABEL || {};
  const data = info || {};
  const stageState = data.state || 'idle';
  const meta = window.pipelineStateMeta(stageState);
  const isRunning = stageState === 'running' || stageState === 'run';
  const isFailed  = stageState === 'failed'  || stageState === 'err';
  const isPassed  = stageState === 'passed'  || stageState === 'ok';
  const isLocked  = stageState === 'locked';
  const cardRef = React.useRef(null);

  // Allow the DAG map (or chip click) to scroll/focus this card.
  React.useEffect(() => {
    const onScrollTo = (ev) => {
      if (!ev.detail || ev.detail.stage !== stageId) return;
      const el = cardRef.current;
      if (!el) return;
      try {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        el.classList.add('pipe-stage-card-flash');
        setTimeout(() => el.classList.remove('pipe-stage-card-flash'), 1400);
      } catch (_) {}
    };
    window.addEventListener('atlas:pipeline-focus-stage', onScrollTo);
    return () => window.removeEventListener('atlas:pipeline-focus-stage', onScrollTo);
  }, [stageId]);

  const dispatchOne = async () => {
    if (!ip) return;
    try {
      const r = await fetch('/api/pipeline/dispatch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ip, stages: [stageId], schedule: 'serial',
          model: data.model || '',
          prompt: '',
          ...window.pipelinePolicyPayload(),
        }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) {
        console.error('[pipeline] dispatch failed', j.error || r.status);
      } else {
        window.dispatchEvent(new CustomEvent('atlas:pipeline-dispatched', {
          detail: { stage: stageId, ip, jobs: j.jobs || [] },
        }));
      }
    } catch (e) {
      console.error('[pipeline] dispatch error', e);
    }
  };

  const goFix = async () => {
    const owner = (data.blame && data.blame.owner_workflow) || '';
    if (!owner || !ip) return;
    const ownerStage = (window.PIPELINE_STAGES || []).find(s => {
      // Map workflow id back to stage id heuristically.
      const sid = s.toLowerCase();
      return owner.toLowerCase().includes(sid) || sid.includes(owner.toLowerCase().split('-')[0]);
    }) || owner;
    try {
      const r = await fetch('/api/pipeline/dispatch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ip, stages: [ownerStage], schedule: 'serial',
          prompt: data.blame && data.blame.feedback_packet
            ? `Repair feedback packet: ${data.blame.feedback_packet}`
            : '',
          ...window.pipelinePolicyPayload(),
        }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) console.error('[pipeline] go-fix failed', j.error || r.status);
    } catch (e) {
      console.error('[pipeline] go-fix error', e);
    }
  };

  const onCardClick = (ev) => {
    // Cmd/Ctrl-click → add to chain rail.
    if ((ev.metaKey || ev.ctrlKey) && typeof onChain === 'function') {
      ev.preventDefault();
      onChain(stageId);
    }
  };

  const label = labels[stageId] || stageId;
  const glyph = data.glyph || meta.glyph;
  const iter  = data.iter != null ? `${data.iter} it` : '';
  const dur   = data.duration_s ? `${Math.round(data.duration_s)}s` : '';
  const model = data.model || '';
  const toolchain = data.toolchain || '';
  const effort = data.effort || '';
  const top = data.top || '';
  const secondary = data.secondary || '';
  const liveTail = data.live_tail || '';
  const progress = data.progress;
  const evidencePaths = data.evidence_paths || [];
  const workflow = data.workflow || (window.pipelineWorkflowForStage && window.pipelineWorkflowForStage(stageId)) || stageId;
  const workspacePath = window.pipelineDefaultWorkspacePath
    ? window.pipelineDefaultWorkspacePath(ip, workflow, stageId, evidencePaths)
    : (evidencePaths[0] || '');
  const canOpenWorkspace = !!(
    ip && workflow && window.PIPELINE_WORKSPACE_WORKFLOWS
    && window.PIPELINE_WORKSPACE_WORKFLOWS.has(workflow)
  );
  const openWorkspace = () => {
    if (!canOpenWorkspace || !window.openPipelineWorkflowWorkspace) return;
    window.openPipelineWorkflowWorkspace({
      ip,
      workflow,
      stageId,
      path: workspacePath,
    });
  };

  // "Start here" highlight: SSOT card when nothing has run yet — gives the
  // user an unambiguous entry point on a fresh IP instead of a sea of locked
  // cards.
  const isSsot = stageId === 'ssot' || stageId === 'ssot-gen';
  const noHistory = !Array.isArray(data.history) || data.history.length === 0;
  const isStartHere = isSsot && (stageState === 'idle' || stageState === 'ready') && noHistory;

  return (
    <div className="pipe-stage-card"
         data-state={stageState}
         data-stage={stageId}
         data-start={isStartHere ? 'true' : undefined}
         ref={cardRef}
         onClick={onCardClick}
         title={isLocked && data.locked_reason ? data.locked_reason
               : isLocked ? 'Upstream not satisfied — locked'
               : undefined}>
      <div className="pipe-stage-row1">
        <span className="pipe-stage-glyph" style={{ color: meta.color }}>{glyph}</span>
        <span className="pipe-stage-label">{label}</span>
        <span className="pipe-stage-state" data-state={stageState}>{meta.label}</span>
        {data.trigger_source === 'orchestrator_chat' && (
          <span className="pipe-stage-orch-pill"
                title="Driven by the right-side Orchestrator chat (LLM loop)">
            orch
          </span>
        )}
        {isLocked && data.locked_reason && (
          <span className="pipe-stage-locked-why mute" title={data.locked_reason}>
            ({data.locked_reason})
          </span>
        )}
        <span className="pipe-stage-spacer" />
        {iter && <span className="pipe-stage-meta">{iter}</span>}
        {dur && <span className="pipe-stage-meta">{dur}</span>}
        {model && <span className="pipe-stage-meta" title={effort ? `effort ${effort}` : ''}>{model}</span>}
        {!model && toolchain && <span className="pipe-stage-meta" title="toolchain">{toolchain}</span>}
      </div>
      <div className="pipe-stage-row2">
        <window.MiniScoresheet scoresheet={data.scoresheet}
                                evidencePaths={evidencePaths} />
      </div>
      <div className="pipe-stage-row3">
        {isRunning && progress != null ? (
          <div className="pipe-progress" title={`progress ${Math.round((progress || 0) * 100)}%`}>
            <div className="pipe-progress-fill"
                 style={{ width: `${Math.max(0, Math.min(100, (progress || 0) * 100))}%` }} />
          </div>
        ) : top ? (
          <div className="pipe-stage-top mute">{top}</div>
        ) : (
          <div className="pipe-stage-top mute">—</div>
        )}
      </div>
      <div className="pipe-stage-row4">
        {secondary
          ? <span className="pipe-stage-secondary">{secondary}</span>
          : <span className="pipe-stage-secondary mute">no secondary evidence</span>}
      </div>
      <div className="pipe-stage-row5">
        {isRunning && liveTail && (
          <div className="pipe-live-tail" title={liveTail}>~ {liveTail}</div>
        )}
        {isPassed && evidencePaths.length > 0 && (
          <button className="pipe-stage-link"
                  onClick={(e) => {
                    e.stopPropagation();
                    try {
                      window.dispatchEvent(new CustomEvent('atlas:open_evidence', {
                        detail: { path: evidencePaths[0], source: 'pipeline' },
                      }));
                    } catch (_) {}
                  }}>[ open evidence ▾ ]</button>
        )}
        {isFailed && data.blame && data.blame.owner_workflow && (
          <span className="pipe-blame">
            <span className="mute">blame →</span>{' '}
            <b>{data.blame.owner_workflow}</b>{' '}
            <button className="pipe-stage-link"
                    onClick={(e) => { e.stopPropagation(); goFix(); }}>
              [ go fix {data.blame.owner_workflow} ]
            </button>
          </span>
        )}
      </div>
      <div className="pipe-stage-actions">
        {canOpenWorkspace && (
          <button className="pipe-stage-workspace rb-btn"
                  disabled={!ip}
                  title={`Open ${workflow} workspace, chat history, files, and artifacts`}
                  onClick={(e) => { e.stopPropagation(); openWorkspace(); }}>
            ⌂ workspace
          </button>
        )}
        <button className="pipe-stage-run rb-btn"
                disabled={isLocked || isRunning || !ip}
                onClick={(e) => { e.stopPropagation(); dispatchOne(); }}>
          {isRunning ? '⏹ running' : '▶ run'}
        </button>
        {data.handoffs && data.handoffs.pending > 0 && (
          <button className="pipe-stage-take rb-btn"
                  disabled={!ip}
                  title={`Claim the oldest pending handoff for ${data.workflow}`}
                  onClick={async (e) => {
                    e.stopPropagation();
                    try {
                      const r = await fetch('/api/handoff/take', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ ip, workflow: data.workflow }),
                      });
                      const j = await r.json().catch(() => ({}));
                      if (!r.ok) console.error('[handoff] take failed', j.error || r.status);
                      try { window.dispatchEvent(new CustomEvent('atlas:pipeline-poll')); } catch (_) {}
                    } catch (err) { console.error('[handoff] take error', err); }
                  }}>
            ⇄ take {data.handoffs.pending}
          </button>
        )}
        {isFailed && data.blame && data.blame.owner_workflow && (
          <button className="pipe-stage-save rb-btn"
                  disabled={!ip}
                  title="Write a pending handoff JSON for the owning workflow"
                  onClick={async (e) => {
                    e.stopPropagation();
                    try {
                      const r = await fetch('/api/handoff/save', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                          ip,
                          from_workflow: data.workflow || stageId,
                          to_workflow: data.blame.owner_workflow,
                          reason: data.error_summary || `${stageId} failed; routed to ${data.blame.owner_workflow}`,
                          evidence: { stage: stageId, blame: data.blame },
                        }),
                      });
                      const j = await r.json().catch(() => ({}));
                      if (!r.ok) console.error('[handoff] save failed', j.error || r.status);
                      try { window.dispatchEvent(new CustomEvent('atlas:pipeline-poll')); } catch (_) {}
                    } catch (err) { console.error('[handoff] save error', err); }
                  }}>
            📬 save handoff
          </button>
        )}
      </div>
    </div>
  );
};

// ─── DispatchRail ──────────────────────────────────────────────────
//
// Bottom rail with stage-id chips, schedule toggle and a primary
// "[ DISPATCH N STAGES ▶ ]" button. POSTs once to /api/pipeline/dispatch
// with the chained stages so the backend resolves dep order itself.
window.DispatchRail = function DispatchRail({ ip, chain, onClearChain, onRemove }) {
  const [schedule, setSchedule] = React.useState('auto');
  const [busy, setBusy] = React.useState(false);
  const labels = window.PIPELINE_LABEL || {};
  const count = chain.length;

  const dispatch = async () => {
    if (!ip || !count || busy) return;
    setBusy(true);
    try {
      const r = await fetch('/api/pipeline/dispatch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ip, stages: chain, schedule,
          prompt: '',
          ...window.pipelinePolicyPayload(),
        }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) {
        console.error('[pipeline] chain dispatch failed', j.error || r.status);
      } else {
        if (typeof onClearChain === 'function') onClearChain();
        window.dispatchEvent(new CustomEvent('atlas:pipeline-dispatched', {
          detail: { stage: 'chain', ip, jobs: j.jobs || [] },
        }));
      }
    } catch (e) {
      console.error('[pipeline] chain dispatch error', e);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="pipe-dispatch-rail">
      <span className="pipe-rail-label">chain</span>
      <span className="pipe-rail-chips">
        {count === 0 && <span className="mute">cmd-click cards to chain</span>}
        {chain.map(s => (
          <button key={s} className="pipe-rail-chip"
                  title={`remove ${labels[s] || s}`}
                  onClick={() => onRemove && onRemove(s)}>
            {labels[s] || s} ✕
          </button>
        ))}
      </span>
      <span className="pipe-rail-spacer" />
      <span className="pipe-rail-label">schedule</span>
      <select className="pipe-rail-select"
              value={schedule}
              onChange={e => setSchedule(e.currentTarget.value)}>
        <option value="auto">auto</option>
        <option value="dag">dag</option>
        <option value="serial">serial</option>
      </select>
      <button className="rb-btn primary"
              disabled={!count || !ip || busy}
              onClick={dispatch}>
        {busy ? '… dispatching' : `DISPATCH ${count || 0} STAGES ▶`}
      </button>
    </div>
  );
};

// ─── FlowInspector ────────────────────────────────────────────────
//
// Right-side panel inspired by the reference screenshots: selectable flows on
// top, numbered steps below, and a focused stage detail/action area.
window.FlowInspector = function FlowInspector({
  ip,
  state,
  selectedFlowId,
  onSelectFlow,
  selectedStage,
  onSelectStage,
  onChain,
}) {
  const [busyFlow, setBusyFlow] = React.useState('');
  const flows = window.PIPELINE_FLOW_DEFS || [];
  const labels = window.PIPELINE_LABEL || {};
  const actualSet = new Set(window.PIPELINE_STAGES || []);
  const stagesState = (state && state.stages) || {};
  const flow = flows.find(f => f.id === selectedFlowId) || flows[0] || { stages: [] };
  const selectedInfo = actualSet.has(selectedStage) ? stagesState[selectedStage] : null;

  const dispatchFlow = async () => {
    const stages = window.pipelineActualStages(flow.stages || []);
    if (!ip || !stages.length || busyFlow) return;
    setBusyFlow(flow.id);
    try {
      const r = await fetch('/api/pipeline/dispatch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ip, stages, schedule: 'auto', prompt: '', ...window.pipelinePolicyPayload() }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) {
        console.error('[pipeline] flow dispatch failed', j.error || r.status);
      } else {
        try {
          window.dispatchEvent(new CustomEvent('atlas:pipeline-dispatched', {
            detail: { stage: flow.id, ip, jobs: j.jobs || [] },
          }));
        } catch (_) {}
      }
    } catch (e) {
      console.error('[pipeline] flow dispatch error', e);
    } finally {
      setBusyFlow('');
    }
  };

  const flowCounts = (stages) => {
    const real = window.pipelineActualStages(stages || []);
    const counts = { running: 0, passed: 0, failed: 0, blocked: 0, locked: 0 };
    real.forEach(s => {
      const st = (stagesState[s] && stagesState[s].state) || 'idle';
      if (st === 'running' || st === 'run') counts.running += 1;
      if (st === 'passed' || st === 'ok') counts.passed += 1;
      if (st === 'failed' || st === 'err') counts.failed += 1;
      if (st === 'blocked' || st === 'stale') counts.blocked += 1;
      if (st === 'locked') counts.locked += 1;
    });
    return counts;
  };

  const stepLabel = (id) => {
    if ((window.PIPELINE_VIRTUAL_NODES || {})[id]) return window.PIPELINE_VIRTUAL_NODES[id].label;
    return labels[id] || id;
  };
  const stepState = (id) => {
    if ((window.PIPELINE_VIRTUAL_NODES || {})[id]) return 'handoff';
    return (stagesState[id] && stagesState[id].state) || 'idle';
  };
  const stepDetail = (id) => {
    const virtual = (window.PIPELINE_VIRTUAL_NODES || {})[id];
    if (virtual) return virtual.sub;
    const data = stagesState[id] || {};
    return data.top || data.secondary || data.locked_reason || 'no evidence yet';
  };

  return (
    <div className="pipe-flow-inspector">
      <section className="pipe-inspector-section">
        <div className="pipe-inspector-title">Flows</div>
        <div className="pipe-flow-list">
          {flows.map(f => {
            const counts = flowCounts(f.stages);
            return (
              <button key={f.id}
                      className={`pipe-flow-choice ${f.id === flow.id ? 'sel' : ''}`}
                      onClick={() => {
                        if (typeof onSelectFlow === 'function') onSelectFlow(f.id);
                        const firstActual = window.pipelineActualStages(f.stages || [])[0];
                        if (firstActual && typeof onSelectStage === 'function') onSelectStage(firstActual);
                      }}>
                <span className="pipe-flow-choice-name">{f.name}</span>
                <span className="pipe-flow-choice-summary">{f.summary}</span>
                <span className="pipe-flow-choice-meta">
                  {counts.running ? `running ${counts.running} · ` : ''}
                  {counts.failed ? `failed ${counts.failed} · ` : ''}
                  {counts.blocked ? `blocked ${counts.blocked} · ` : ''}
                  passed {counts.passed}/{window.pipelineActualStages(f.stages || []).length}
                </span>
              </button>
            );
          })}
        </div>
        <button className="rb-btn primary pipe-flow-run"
                disabled={!ip || busyFlow || !window.pipelineActualStages(flow.stages || []).length}
                onClick={dispatchFlow}>
          {busyFlow ? 'dispatching…' : `Run ${flow.name}`}
        </button>
      </section>

      <section className="pipe-inspector-section pipe-steps-section">
        <div className="pipe-inspector-title">Steps</div>
        <div className="pipe-step-list">
          {(flow.stages || []).map((id, idx) => {
            const stateName = stepState(id);
            return (
              <button key={`${id}-${idx}`}
                      className={`pipe-step-card ${selectedStage === id ? 'sel' : ''}`}
                      data-state={stateName}
                      onClick={() => typeof onSelectStage === 'function' && onSelectStage(id)}>
                <span className="pipe-step-index">{idx + 1}</span>
                <span className="pipe-step-body">
                  <span className="pipe-step-name">{stepLabel(id)}</span>
                  <span className="pipe-step-detail">{stepDetail(id)}</span>
                </span>
                <span className="pipe-step-state">{stateName}</span>
              </button>
            );
          })}
        </div>
      </section>

      <section className="pipe-inspector-section">
        <div className="pipe-inspector-title">Selected</div>
        {selectedInfo ? (
          <window.StageCard
            stageId={selectedStage}
            info={selectedInfo}
            ip={ip}
            onChain={onChain} />
        ) : (
          <div className="pipe-virtual-detail">
            <b>{stepLabel(selectedStage || 'orchestrator')}</b>
            <span>{stepDetail(selectedStage || 'orchestrator')}</span>
            <span className="mute">This is an orchestrator control-plane step, not a workflow artifact owner.</span>
          </div>
        )}
      </section>
    </div>
  );
};

// ─── PipelineFlowControl ──────────────────────────────────────────
//
// Top-center flow selector. The user asked for flow/step controls not to sit
// under the graph; keep them in the center header so the map remains primary.
window.PipelineFlowControl = function PipelineFlowControl({
  ip,
  state,
  selectedFlowId,
  onSelectFlow,
  selectedStage,
  onSelectStage,
}) {
  const [busyFlow, setBusyFlow] = React.useState('');
  const flows = window.PIPELINE_FLOW_DEFS || [];
  const labels = window.PIPELINE_LABEL || {};
  const stagesState = (state && state.stages) || {};
  const flow = flows.find(f => f.id === selectedFlowId) || flows[0] || { stages: [] };

  const flowCounts = (stages) => {
    const real = window.pipelineActualStages(stages || []);
    const counts = { running: 0, passed: 0, failed: 0, blocked: 0 };
    real.forEach(s => {
      const st = (stagesState[s] && stagesState[s].state) || 'idle';
      if (st === 'running' || st === 'run') counts.running += 1;
      if (st === 'passed' || st === 'ok') counts.passed += 1;
      if (st === 'failed' || st === 'err') counts.failed += 1;
      if (st === 'blocked' || st === 'stale' || st === 'locked') counts.blocked += 1;
    });
    counts.total = real.length;
    return counts;
  };

  const stepLabel = (id) => {
    if ((window.PIPELINE_VIRTUAL_NODES || {})[id]) return window.PIPELINE_VIRTUAL_NODES[id].label;
    return labels[id] || id;
  };
  const stepState = (id) => {
    if ((window.PIPELINE_VIRTUAL_NODES || {})[id]) return 'handoff';
    return (stagesState[id] && stagesState[id].state) || 'idle';
  };

  const dispatchFlow = async () => {
    const stages = window.pipelineActualStages(flow.stages || []);
    if (!ip || !stages.length || busyFlow) return;
    setBusyFlow(flow.id);
    try {
      const r = await fetch('/api/pipeline/dispatch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ip, stages, schedule: 'auto', prompt: '', ...window.pipelinePolicyPayload() }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) {
        console.error('[pipeline] flow dispatch failed', j.error || r.status);
      } else {
        try {
          window.dispatchEvent(new CustomEvent('atlas:pipeline-dispatched', {
            detail: { stage: flow.id, ip, jobs: j.jobs || [] },
          }));
        } catch (_) {}
      }
    } catch (e) {
      console.error('[pipeline] flow dispatch error', e);
    } finally {
      setBusyFlow('');
    }
  };

  return (
    <div className="pipe-flow-control">
      <div className="pipe-flow-control-top">
        <div>
          <div className="pipe-flow-control-title">Pipeline Flows</div>
          <div className="pipe-flow-control-summary">{flow.summary || ''}</div>
        </div>
        <button className="rb-btn primary pipe-flow-run-inline"
                disabled={!ip || busyFlow || !window.pipelineActualStages(flow.stages || []).length}
                onClick={dispatchFlow}>
          {busyFlow ? 'dispatching...' : `Run ${flow.name || 'flow'}`}
        </button>
      </div>
      <div className="pipe-flow-chip-row">
        {flows.map(f => {
          const counts = flowCounts(f.stages);
          return (
            <button key={f.id}
                    className={`pipe-flow-tab ${f.id === flow.id ? 'sel' : ''}`}
                    onClick={() => {
                      if (typeof onSelectFlow === 'function') onSelectFlow(f.id);
                      const firstActual = window.pipelineActualStages(f.stages || [])[0];
                      if (firstActual && typeof onSelectStage === 'function') onSelectStage(firstActual);
                    }}>
              <span>{f.name}</span>
              <b>{counts.passed}/{counts.total}</b>
            </button>
          );
        })}
      </div>
      <div className="pipe-flow-step-row">
        {(flow.stages || []).map((id, idx) => (
          <button key={`${id}-${idx}`}
                  className={`pipe-flow-step-pill ${selectedStage === id ? 'sel' : ''}`}
                  data-state={stepState(id)}
                  onClick={() => typeof onSelectStage === 'function' && onSelectStage(id)}>
            <span>{idx + 1}</span>
            {stepLabel(id)}
          </button>
        ))}
      </div>
    </div>
  );
};

// ─── Internal: HierarchyList ───────────────────────────────────────
//
// Left column lists every IP discovered via /api/ip/list. Selecting
// one updates the AtlasPipeline `ip` state. Falls back to a single-row
// list with the active IP if the workspace endpoint is missing.
function HierarchyList({ activeIp, onSelect }) {
  const [ips, setIps] = React.useState([]);
  React.useEffect(() => {
    let dead = false;
    (async () => {
      try {
        const sessionId = window.ATLAS_USER_SESSION_ID || (window.ACTIVE_SESSION || '').split('/')[0] || '';
        const url = sessionId ? `/api/ip/list?session_id=${encodeURIComponent(sessionId)}` : '/api/ip/list';
        const r = await fetch(url);
        const j = await r.json().catch(() => ({}));
        if (dead) return;
        const list = Array.isArray(j.items) ? j.items
                   : Array.isArray(j.ips) ? j.ips
                   : Array.isArray(j.workspaces) ? j.workspaces
                   : [];
        setIps(list.map(x => typeof x === 'string' ? x : (x.ip || x.name || x.id || '')).filter(Boolean));
      } catch (_) {
        if (!dead && activeIp) setIps([activeIp]);
      }
    })();
    return () => { dead = true; };
  }, [activeIp]);

  return (
    <div className="pipe-hierarchy">
      <div className="pipe-hierarchy-title">IP HIERARCHY</div>
      <ul className="pipe-hierarchy-list">
        {(ips.length ? ips : (activeIp ? [activeIp] : [])).map(ip => (
          <li key={ip}
              className={`pipe-hierarchy-row ${ip === activeIp ? 'sel' : ''}`}
              onClick={() => onSelect && onSelect(ip)}>
            <span className="pipe-hierarchy-glyph">{ip === activeIp ? '◉' : '○'}</span>
            <span className="pipe-hierarchy-name">{ip}</span>
          </li>
        ))}
        {!ips.length && !activeIp && (
          <li className="pipe-hierarchy-row mute">no IPs yet</li>
        )}
      </ul>
      <div className="pipe-hierarchy-legend mute">
        <div>legend</div>
        <div>✓ passed · ▶ running · ! failed</div>
        <div>⏸ blocked · ⊘ stale · ◯ idle</div>
      </div>
    </div>
  );
}

function deriveStageReadiness(stagesState) {
  const sids = window.PIPELINE_STAGES || [];
  if (!stagesState || !sids.length) return null;
  const labels = window.PIPELINE_LABEL || {};
  let passed = 0, failed = 0, running = 0, blocked = 0, idle = 0;
  let firstNonGreen = null;
  for (const sid of sids) {
    const info = stagesState[sid] || {};
    const st = String(info.state || 'idle').toLowerCase();
    if (st === 'passed' || st === 'pass' || st === 'green') passed++;
    else if (st === 'running' || st === 'run') { running++; if (!firstNonGreen) firstNonGreen = sid; }
    else if (st === 'failed' || st === 'fail' || st === 'error' || st === 'red') { failed++; if (!firstNonGreen) firstNonGreen = sid; }
    else if (st === 'blocked' || st === 'block') { blocked++; if (!firstNonGreen) firstNonGreen = sid; }
    else { idle++; if (!firstNonGreen) firstNonGreen = sid; }
  }
  const total = sids.length;
  const percent = total ? Math.round((passed / total) * 100) : 0;
  const nextLabel = firstNonGreen ? (labels[firstNonGreen] || firstNonGreen) : null;
  let headline, message, nextSteps;
  if (passed === total) {
    headline = 'Pipeline complete';
    message = `All ${total} stages passed. Review evidence and approve sign-off.`;
    nextSteps = [{ stage: 'audit', label: 'Review goal-audit + approve sign-off', owner: 'human',
                   reason: 'Final human approval is the only gate left.', status: 'pending' }];
  } else if (failed) {
    headline = `${failed} stage${failed > 1 ? 's' : ''} failed`;
    message = `Fix ${nextLabel} (or other failed stage), then re-run downstream.`;
    nextSteps = [{ stage: firstNonGreen, label: `Resolve failure in ${nextLabel}`, owner: 'atlas',
                   reason: 'Failure blocks every downstream stage.', status: 'failed' }];
  } else if (blocked) {
    headline = `${blocked} stage${blocked > 1 ? 's' : ''} blocked`;
    message = `Unblock ${nextLabel} (review decision or missing evidence).`;
    nextSteps = [{ stage: firstNonGreen, label: `Unblock ${nextLabel}`, owner: 'human',
                   reason: 'Blocked stages need a review decision or missing evidence.', status: 'blocked' }];
  } else if (running) {
    headline = `${running} stage${running > 1 ? 's' : ''} running`;
    message = `Waiting for ${nextLabel} to finish.`;
    nextSteps = [{ stage: firstNonGreen, label: `Watch ${nextLabel}`, owner: 'atlas',
                   reason: 'Stage in progress.', status: 'running' }];
  } else if (passed > 0) {
    headline = `${passed} / ${total} stages green`;
    message = `Next: run ${nextLabel}.`;
    nextSteps = [{ stage: firstNonGreen, label: `Run ${nextLabel}`, owner: 'atlas',
                   reason: 'Next stage in the canonical pipeline.', status: 'pending' }];
  } else {
    return null;
  }
  return { percent, headline, message, next_stage: firstNonGreen, next_steps: nextSteps,
           state: passed === total ? 'complete' : (failed ? 'failed' : (blocked ? 'blocked' : (running ? 'running' : 'in_progress'))) };
}

function RunToGreenCard({ summary, stages, ip, onSelectStage }) {
  const [busy, setBusy] = React.useState(false);
  const derived = deriveStageReadiness(stages);
  const backend = summary || {};
  const backendPercent = Math.max(0, Math.min(100, Number(backend.percent || 0)));
  const derivedPercent = derived ? derived.percent : 0;
  const useDerived = derived && (derivedPercent > backendPercent || backendPercent === 0);
  const data = useDerived
    ? { ...backend, percent: derivedPercent, headline: derived.headline, message: derived.message,
        next_stage: derived.next_stage, next_steps: derived.next_steps, state: derived.state }
    : backend;
  const state = data.state || 'not_started';
  const percent = Math.max(0, Math.min(100, Number(data.percent || 0)));
  const rawSteps = Array.isArray(data.next_steps) ? data.next_steps : [];
  const nextSteps = rawSteps.length ? rawSteps : [{
    stage: 'ssot',
    label: 'Create or import SSOT',
    owner: 'user',
    reason: 'SSOT is the source of truth for every downstream step.',
    status: 'pending',
  }];
  const stageFor = (stage) => {
    if (stage === 'req') return 'ssot';
    if (stage === 'equivalence_goals') return 'equivalence';
    if (stage === 'goal_audit') return 'goal-audit';
    if (stage === 'sim_debug') return 'sim-debug';
    if (stage === 'fl_model') return 'fl-model';
    if (stage === 'fl_decomp' || stage === 'fcov_plan') return 'fl-model';
    return stage || 'ssot';
  };
  const focusStage = (stage) => {
    const sid = stageFor(stage || data.next_stage);
    if (typeof onSelectStage === 'function') onSelectStage(sid);
    try {
      window.dispatchEvent(new CustomEvent('atlas:pipeline-focus-stage', {
        detail: { stage: sid },
      }));
    } catch (_) {}
  };
  const runToGreen = async () => {
    if (!ip || busy) return;
    const flow = (window.PIPELINE_FLOW_DEFS || []).find(f => f.id === 'full') || { stages: [] };
    const stages = window.pipelineActualStages(flow.stages || []);
    if (!stages.length) return;
    setBusy(true);
    try {
      const r = await fetch('/api/pipeline/dispatch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ip, stages, schedule: 'auto', prompt: '', ...window.pipelinePolicyPayload() }),
      });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) {
        console.error('[pipeline] run-to-green failed', j.error || r.status);
      } else {
        try {
          window.dispatchEvent(new CustomEvent('atlas:pipeline-dispatched', {
            detail: { stage: 'full', ip, jobs: j.jobs || [] },
          }));
          window.dispatchEvent(new CustomEvent('atlas:pipeline-poll'));
        } catch (_) {}
      }
    } catch (e) {
      console.error('[pipeline] run-to-green error', e);
    } finally {
      setBusy(false);
    }
  };
  const primary = data.primary_action || {};
  const primaryKind = primary.kind || 'run_pipeline';
  const primaryLabel = busy ? 'Starting...' : (primary.label || 'Run to Green');
  return (
    <div className="pipe-green-card" data-state={state}>
      <div className="pipe-green-top">
        <span className="pipe-green-kicker">GREEN READINESS</span>
        <span className="pipe-green-percent">{percent}%</span>
      </div>
      <div className="pipe-green-headline">{data.headline || 'Start the IP pipeline'}</div>
      <div className="pipe-green-message">
        {data.message || 'Run the flow and ATLAS will show the next simple action here.'}
      </div>
      <div className="pipe-green-bar" aria-label={`green readiness ${percent}%`}>
        <div className="pipe-green-bar-fill" style={{ width: `${percent}%` }} />
      </div>
      <div className="pipe-green-actions">
        <button className="rb-btn primary pipe-green-primary"
                disabled={!ip || busy}
                onClick={() => primaryKind === 'run_pipeline'
                  ? runToGreen()
                  : focusStage(primary.stage || data.next_stage)}>
          {primaryLabel}
        </button>
        {data.next_stage && (
          <button className="rb-btn pipe-green-secondary"
                  onClick={() => focusStage(data.next_stage)}>
            Open Next
          </button>
        )}
      </div>
      <div className="pipe-green-next">
        {nextSteps.length ? nextSteps.map((step, idx) => (
          <button key={`${step.stage || idx}-${idx}`}
                  className="pipe-green-step"
                  onClick={() => focusStage(step.stage)}>
            <span className="pipe-green-step-index">{idx + 1}</span>
            <span className="pipe-green-step-main">
              <span className="pipe-green-step-label">{step.label || step.stage}</span>
              <span className="pipe-green-step-reason">{step.reason || step.status || ''}</span>
            </span>
            <span className="pipe-green-owner">{step.owner || 'atlas'}</span>
          </button>
        )) : (
          <div className="pipe-green-empty">No open step found.</div>
        )}
      </div>
    </div>
  );
}

// ─── Internal: StageStatusRail ─────────────────────────────────────
//
// Left column: status is now the primary left-hand object. IP selection stays
// compact at the top, then every workflow stage is visible without scrolling
// the graph or opening a bottom inspector.
function StageStatusRail({ activeIp, onSelectIp, state, simpleSummary, selectedStage, onSelectStage }) {
  const labels = window.PIPELINE_LABEL || {};
  const stages = window.PIPELINE_STAGES || [];
  const stagesState = (state && state.stages) || {};
  const [ips, setIps] = React.useState([]);
  const [detailsOpen, setDetailsOpen] = React.useState(false);

  React.useEffect(() => {
    let dead = false;
    (async () => {
      try {
        const sessionId = window.ATLAS_USER_SESSION_ID || (window.ACTIVE_SESSION || '').split('/')[0] || '';
        const url = sessionId ? `/api/ip/list?session_id=${encodeURIComponent(sessionId)}` : '/api/ip/list';
        const r = await fetch(url);
        const j = await r.json().catch(() => ({}));
        if (dead) return;
        const list = Array.isArray(j.items) ? j.items
                   : Array.isArray(j.ips) ? j.ips
                   : Array.isArray(j.workspaces) ? j.workspaces
                   : [];
        setIps(list.map(x => typeof x === 'string' ? x : (x.ip || x.name || x.id || '')).filter(Boolean));
      } catch (_) {
        if (!dead && activeIp) setIps([activeIp]);
      }
    })();
    return () => { dead = true; };
  }, [activeIp]);

  const summarize = (info) => {
    if (!info) return 'no evidence yet';
    return info.top || info.secondary || info.locked_reason || info.latest_evidence || 'no evidence yet';
  };

  return (
    <div className="pipe-stage-rail">
      <div className="pipe-stage-rail-head">
        <div>
          <div className="pipe-stage-rail-kicker">IP</div>
          <div className="pipe-stage-rail-ip">{activeIp || 'no IP'}</div>
        </div>
        <select className="pipe-stage-rail-select"
                value={activeIp || ''}
                onChange={e => onSelectIp && onSelectIp(e.currentTarget.value)}>
          {(ips.length ? ips : (activeIp ? [activeIp] : [])).map(ip => (
            <option key={ip} value={ip}>{ip}</option>
          ))}
        </select>
      </div>
      <RunToGreenCard
        summary={simpleSummary}
        stages={stagesState}
        ip={activeIp}
        onSelectStage={onSelectStage} />
      <button className="pipe-stage-rail-title pipe-stage-rail-toggle"
              onClick={() => setDetailsOpen(v => !v)}
              aria-expanded={detailsOpen}>
        <span>Stage Detail</span>
        <span className="pipe-stage-rail-toggle-hint">{detailsOpen ? '▾ hide' : '▸ show'}</span>
      </button>
      {detailsOpen && (
        <>
          <div className="pipe-stage-rail-hint">Same info as the flow map. Click a row to focus the stage.</div>
          <div className="pipe-stage-rail-list">
            {stages.map(stageId => {
              const info = stagesState[stageId] || {};
              const stateName = info.state || 'idle';
              const meta = window.pipelineStateMeta(stateName);
              return (
                <button key={stageId}
                        className={`pipe-stage-rail-row ${selectedStage === stageId ? 'sel' : ''}`}
                        data-state={stateName}
                        onClick={() => onSelectStage && onSelectStage(stageId)}>
                  <span className="pipe-stage-rail-glyph" style={{ color: meta.color }}>{meta.glyph}</span>
                  <span className="pipe-stage-rail-main">
                    <span className="pipe-stage-rail-name">{labels[stageId] || stageId}</span>
                    <span className="pipe-stage-rail-sub">{summarize(info)}</span>
                  </span>
                  <span className="pipe-stage-rail-state">{meta.label}</span>
                </button>
              );
            })}
          </div>
          <div className="pipe-stage-rail-legend">
            ✓ passed · ▶ running · ! failed · ⏸ blocked · ⊘ stale
          </div>
        </>
      )}
    </div>
  );
}

function PipelineOrchestratorChatPanel({ ip }) {
  if (!window.ArchitectChat) {
    return (
      <div className="pipe-orch-chat-fallback">
        <b>orchestrator chat</b>
        <span className="mute">ArchitectChat is not loaded yet.</span>
      </div>
    );
  }
  return (
    <div className="pipe-orch-chat-shell">
      <window.ArchitectChat
        view="pipeline"
        selModule={ip ? { name: ip } : null}
        selCluster={null}
        onDiagramPlan={null} />
    </div>
  );
}

// ─── Internal: PhaseGroup ──────────────────────────────────────────
//
// Visual grouping of a phase's stage cards into a 2-column grid.
// SIGN-OFF starts collapsed if every stage in the band is idle, since
// most users don't care about the back-end stages until earlier work
// passes. Click the band header to expand/collapse.
function PhaseGroup({ phase, stagesState, ip, onChain, defaultCollapsed }) {
  const [collapsed, setCollapsed] = React.useState(!!defaultCollapsed);
  const stages = phase.stages.filter(s => (window.PIPELINE_STAGES || []).indexOf(s) >= 0);
  return (
    <div className="pipe-phase-group" data-phase={phase.id}>
      <div className="pipe-phase-header" onClick={() => setCollapsed(c => !c)}>
        <span className="pipe-phase-glyph">{collapsed ? '▸' : '▾'}</span>
        <span className="pipe-phase-name">{phase.id}</span>
        <span className="pipe-phase-count mute">({stages.length})</span>
      </div>
      {!collapsed && (
        <div className="pipe-phase-grid">
          {stages.map(s => (
            <window.StageCard
              key={s}
              stageId={s}
              info={stagesState[s]}
              ip={ip}
              onChain={onChain} />
          ))}
        </div>
      )}
    </div>
  );
}

// ─── AtlasPipeline ─────────────────────────────────────────────────
//
// Top-level screen. 3-column flex shell:
//   left   IP hierarchy
//   center DAG map + phase-grouped stage cards + dispatch rail
//   right  ArchitectChat (re-mounted; keeps the agent transcript)
//
// Owns the data fetch loop:
//   - polls /api/pipeline/state?ip=<ip> every 2 s
//   - subscribes to bridge event 'pipeline_state_changed' for instant
//     refresh when the backend pushes
//   - re-fetches when ip changes
//   - sets document.title = '▶ ATLAS — <ip> (<stage>)' while running
//
// Graceful empty state: if /api/pipeline/state 404s the right column
// still mounts ArchitectChat and the center shows "Pipeline state
// unavailable" rather than blowing up the entire screen.
function pipelineIpFromActiveNamespace() {
  const parts = String(window.ACTIVE_SESSION || '').split('/').filter(Boolean);
  if (parts.length >= 3) return parts[parts.length - 2] || '';
  return '';
}

function pipelineInitialIp() {
  const params = new URLSearchParams(window.location.search || '');
  const urlSessionParts = String(params.get('session') || '').split('/').filter(Boolean);
  const urlSessionIp = urlSessionParts.length >= 3 ? (urlSessionParts[urlSessionParts.length - 2] || '') : '';
  return (
    (params.get('ip') || params.get('ip_id') || '').trim() ||
    urlSessionIp.trim() ||
    pipelineIpFromActiveNamespace() ||
    (typeof window.ACTIVE_IP === 'string' && window.ACTIVE_IP.trim()) ||
    ((window.CONTEXT && (window.CONTEXT.active_ip || window.CONTEXT.activeIp)) || '').trim() ||
    (() => { try { return localStorage.getItem('atlasActiveIp') || ''; } catch (_) { return ''; } })() ||
    'arm_m0_min'
  );
}

window.AtlasPipeline = function AtlasPipeline() {
  const [pipelineState, setPipelineState] = React.useState(null);
  const [progressSummary, setProgressSummary] = React.useState(null);
  const [fetchError, setFetchError]   = React.useState('');
  const initialIp = pipelineInitialIp();
  const [ip, setIp] = React.useState(initialIp);
  const [chain, setChain] = React.useState([]);
  const [selectedFlowId, setSelectedFlowId] = React.useState('full');
  const [selectedStage, setSelectedStage] = React.useState('ssot');
  const [chatTarget, setChatTarget] = React.useState('orchestrator');
  const [localPolicy, setLocalPolicy] = React.useState(() => window.pipelinePolicyPayload());
  const [leftW, setLeftW] = React.useState(() => {
    try { return Math.max(200, Math.min(600, Number(localStorage.getItem('atlasPipeLeftW')) || 300)); }
    catch (_) { return 300; }
  });
  const [rightW, setRightW] = React.useState(() => {
    try { return Math.max(280, Math.min(900, Number(localStorage.getItem('atlasPipeRightW')) || 430)); }
    catch (_) { return 430; }
  });
  const dragRef = React.useRef(null);
  const beginDrag = React.useCallback((edge) => (ev) => {
    ev.preventDefault();
    const startX = ev.clientX;
    const startLeft = leftW;
    const startRight = rightW;
    document.body.setAttribute('data-resize-cursor', 'col');
    dragRef.current = edge;
    const onMove = (e) => {
      const dx = e.clientX - startX;
      if (edge === 'left') {
        const w = Math.max(200, Math.min(600, startLeft + dx));
        setLeftW(w);
      } else if (edge === 'right') {
        const w = Math.max(280, Math.min(900, startRight - dx));
        setRightW(w);
      }
    };
    const onUp = () => {
      document.body.removeAttribute('data-resize-cursor');
      dragRef.current = null;
      try {
        localStorage.setItem('atlasPipeLeftW', String(leftW));
        localStorage.setItem('atlasPipeRightW', String(rightW));
      } catch (_) {}
      window.removeEventListener('mousemove', onMove);
      window.removeEventListener('mouseup', onUp);
    };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
  }, [leftW, rightW]);
  // Persist on every change.
  React.useEffect(() => {
    try { localStorage.setItem('atlasPipeLeftW', String(leftW)); } catch (_) {}
  }, [leftW]);
  React.useEffect(() => {
    try { localStorage.setItem('atlasPipeRightW', String(rightW)); } catch (_) {}
  }, [rightW]);

  React.useEffect(() => {
    const onPolicy = (ev) => {
      const detail = (ev && ev.detail) || {};
      setLocalPolicy({
        run_mode: detail.run_mode || window.pipelinePolicyPayload().run_mode,
        exec_mode: detail.exec_mode || window.pipelinePolicyPayload().exec_mode,
      });
    };
    window.addEventListener('atlas-run-policy-changed', onPolicy);
    return () => window.removeEventListener('atlas-run-policy-changed', onPolicy);
  }, []);

  // Pipeline screen is the orchestrator's conversation surface. When this
  // screen mounts, pivot the active session's workflow to `orchestrator`
  // so the right-side chat (ArchitectChat → window.backend.send) targets
  // the orchestrator workflow's system_prompt + commands instead of
  // whatever workflow the user happened to be on previously.
  React.useEffect(() => {
    let dead = false;
    const ownerId = (typeof window.ATLAS_USER_SESSION_ID === 'string' && window.ATLAS_USER_SESSION_ID)
      || (() => { try { return localStorage.getItem('atlasUserSessionId') || ''; } catch (_) { return ''; } })()
      || 'default';
    if (typeof window.activateAtlasNamespace === 'function') {
      window.activateAtlasNamespace(ownerId, ip || 'default', 'orchestrator', true);
      return () => { dead = true; };
    }
    const namespace = `${ownerId}/${ip || 'default'}/orchestrator`;
    window.ACTIVE_SESSION = namespace;
    try { localStorage.setItem('atlasActiveSession', namespace); } catch (_) {}
    try {
      if (window.atlasData && typeof window.atlasData.setUserSessionId === 'function') {
        window.atlasData.setUserSessionId(ownerId);
      }
      if (window.atlasData && typeof window.atlasData.setScopePath === 'function') {
        window.atlasData.setScopePath(ip || 'default');
      }
      if (window.atlasData && typeof window.atlasData.setActiveSession === 'function') {
        window.atlasData.setActiveSession(namespace);
      }
      if (window.backend && typeof window.backend.disconnect === 'function' && typeof window.backend.connect === 'function') {
        window.backend.disconnect();
        setTimeout(() => window.backend.connect(namespace), 0);
      }
      window.dispatchEvent(new CustomEvent('atlas-session-switched', {
        detail: { sessionId: ownerId, namespace, ip: ip || 'default', workflow: 'orchestrator' },
      }));
    } catch (_) {}
    fetch('/api/session/activate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: ownerId,
        ip: ip || 'default',
        workflow: 'orchestrator',
        preserve_running: window.ATLAS_EXEC_MODE === 'orchestrator',
      }),
    })
      .then(r => r.ok ? r.json().catch(() => ({})) : null)
      .then(j => {
        if (dead || !j) return;
        try {
          window.dispatchEvent(new CustomEvent('atlas-workflow-switched', {
            detail: { workflow: 'orchestrator', via: 'pipeline-mount' },
          }));
        } catch (_) {}
      })
      .catch(() => {});
    return () => { dead = true; };
  }, [ip]);

  React.useEffect(() => {
    const syncIpFromNamespace = () => {
      const nextIp = pipelineIpFromActiveNamespace();
      if (nextIp && nextIp !== ip) setIp(nextIp);
    };
    syncIpFromNamespace();
    window.addEventListener('atlas-session-switched', syncIpFromNamespace);
    window.addEventListener('atlas-conversation-loaded', syncIpFromNamespace);
    return () => {
      window.removeEventListener('atlas-session-switched', syncIpFromNamespace);
      window.removeEventListener('atlas-conversation-loaded', syncIpFromNamespace);
    };
  }, [ip]);

  // Poll loop + WS subscription. Re-runs when ip changes.
  React.useEffect(() => {
    let dead = false;
    let timer = null;
    let unsub = null;

    const poll = async () => {
      try {
        const r = await fetch(`/api/pipeline/state?ip=${encodeURIComponent(ip)}`);
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const j = await r.json();
        if (dead) return;
        setPipelineState(j);
        setFetchError('');
      } catch (e) {
        if (dead) return;
        // Don't clobber an existing snapshot on transient failures.
        setFetchError(e && e.message ? e.message : String(e));
      }
    };

    poll();
    timer = setInterval(poll, 2000);

    try {
      if (window.backend && typeof window.backend.subscribe === 'function') {
        unsub = window.backend.subscribe('pipeline_state_changed', () => {
          // Tiny debounce so a burst of events maps to a single fetch.
          clearTimeout(window.__pipelinePushPoll);
          window.__pipelinePushPoll = setTimeout(poll, 200);
        });
      }
    } catch (_) {}

    // UI components (e.g. the orchestrator toggle button) can request an
    // immediate poll after mutating server state. The handler debounces
    // bursts the same way the backend subscription does.
    const onForcePoll = () => {
      clearTimeout(window.__pipelinePushPoll);
      window.__pipelinePushPoll = setTimeout(poll, 50);
    };
    window.addEventListener('atlas:pipeline-poll', onForcePoll);

    return () => {
      dead = true;
      if (timer) clearInterval(timer);
      try { if (unsub) unsub(); } catch (_) {}
      window.removeEventListener('atlas:pipeline-poll', onForcePoll);
    };
  }, [ip]);

  React.useEffect(() => {
    let dead = false;
    let timer = null;

    const pollProgress = async () => {
      if (!ip) {
        if (!dead) setProgressSummary(null);
        return;
      }
      try {
        const r = await fetch(`/api/progress?scope=${encodeURIComponent(ip)}`);
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        const j = await r.json();
        const selected = (j && j.selected) || {};
        const signoff = selected.signoff || {};
        const summary = selected.simple_summary || signoff.simple_summary || null;
        if (!dead) setProgressSummary(summary);
      } catch (_) {
        if (!dead) setProgressSummary(null);
      }
    };

    pollProgress();
    timer = setInterval(pollProgress, 5000);
    const onForcePoll = () => {
      clearTimeout(window.__pipelineProgressPoll);
      window.__pipelineProgressPoll = setTimeout(pollProgress, 120);
    };
    window.addEventListener('atlas:pipeline-poll', onForcePoll);
    return () => {
      dead = true;
      if (timer) clearInterval(timer);
      window.removeEventListener('atlas:pipeline-poll', onForcePoll);
    };
  }, [ip]);

  // Keep window.ATLAS_JOBS-style running count in sync so the top-bar
  // "[▶ N running]" chip in app.jsx can read it without owning its
  // own fetch loop.
  React.useEffect(() => {
    const stages = (pipelineState && pipelineState.stages) || {};
    const running = Object.entries(stages).filter(([_, v]) =>
      (v && (v.state === 'running' || v.state === 'run'))
    );
    window.ATLAS_PIPELINE_RUNNING = running.length;
    try {
      window.dispatchEvent(new CustomEvent('atlas:pipeline-running-changed', {
        detail: { count: running.length, stages: running.map(([k]) => k), ip },
      }));
    } catch (_) {}
    // Tab title indicator.
    if (running.length) {
      const first = running[0][0];
      document.title = `▶ ATLAS — ${ip} (${first})`;
    } else {
      // Reset only if we previously set a running title.
      if (document.title.startsWith('▶ ATLAS')) document.title = `ATLAS — ${ip}`;
    }
  }, [pipelineState, ip]);

  // Cmd-click on a card pushes its stage id into the chain rail.
  const addToChain = React.useCallback((stageId) => {
    setChain(c => c.indexOf(stageId) >= 0 ? c : [...c, stageId]);
  }, []);
  const removeFromChain = React.useCallback((stageId) => {
    setChain(c => c.filter(s => s !== stageId));
  }, []);

  const stagesState = (pipelineState && pipelineState.stages) || {};
  const runningCount = Object.values(stagesState).filter(v =>
    v && (v.state === 'running' || v.state === 'run')).length;
  const effectiveRunMode = (pipelineState && (pipelineState.run_mode || pipelineState.policy?.run_mode)) || localPolicy.run_mode || 'engineering';
  const effectiveExecMode = (pipelineState && (pipelineState.exec_mode || pipelineState.policy?.exec_mode)) || localPolicy.exec_mode || 'orchestrator';
  const provenanceSummary = (pipelineState && (pipelineState.provenance_summary || pipelineState.policy?.provenance_summary)) || {};
  const defaultsCount = Number(provenanceSummary.generated_defaults || 0);
  const reviewCount = Number(provenanceSummary.review_needed || 0);
  const signoffBlocked = !!provenanceSummary.signoff_blocked;
  const titleCase = (v) => String(v || '').split('-').map(s => s ? s[0].toUpperCase() + s.slice(1) : s).join(' ');
  const decisionItems = (pipelineState && pipelineState.orchestrator && Array.isArray(pipelineState.orchestrator.decision_items))
    ? pipelineState.orchestrator.decision_items
    : [];
  const decisionReviewCount = pipelineState && pipelineState.orchestrator
    ? Number(pipelineState.orchestrator.decisions_needed || pipelineState.orchestrator.review_decisions || decisionItems.length || 0)
    : 0;
  const firstDecision = decisionItems[0] || null;
  const firstDecisionEvidence = (firstDecision && firstDecision.evidence) || {};
  const firstDecisionOpenPath = String(firstDecisionEvidence.human_facing_request || (firstDecision && firstDecision.path) || '').trim();
  const firstDecisionReviewAids = Array.isArray(firstDecisionEvidence.review_aids)
    ? firstDecisionEvidence.review_aids.filter(Boolean).slice(0, 4)
    : [];
  const firstDecisionTitle = firstDecision
    ? [
        'Review Decision Needed',
        firstDecision.topic ? `topic: ${firstDecision.topic}` : '',
        firstDecision.status ? `status: ${firstDecision.status}` : '',
        firstDecisionOpenPath ? `open: ${firstDecisionOpenPath}` : '',
        ...firstDecisionReviewAids.map(path => `aid: ${path}`),
        firstDecision.path ? `record: ${firstDecision.path}` : '',
      ].filter(Boolean).join('\n')
    : 'Review Decision Needed records under <ip>/review/';

  return (
    <div className="pipe-screen arch-screen">
      <div className="run-bar pipe-runbar">
        <div className="grp">
          <span className="rb-btn" title="active IP">ip <b>{ip || '—'}</b></span>
          <span className="rb-btn" title="dispatch mode">● pipeline</span>
          <span className="rb-btn pipe-run-mode-chip"
                title="Run Mode controls evidence strictness, not IP size">
            run <b>{titleCase(effectiveRunMode)}</b>
          </span>
          <span className={`rb-btn pipe-exec-mode-chip${effectiveExecMode === 'orchestrator' ? ' pipe-exec-mode-on' : ''}`}
                title="Exec Mode chooses single-worker execution or orchestrator-managed workers">
            exec <b>{titleCase(effectiveExecMode)}</b>
          </span>
          {defaultsCount > 0 && (
            <span className="rb-btn pipe-policy-warn"
                  title="Generated defaults recorded in SSOT provenance sidecar">
              defaults {defaultsCount}
            </span>
          )}
          {reviewCount > 0 && (
            <span className="rb-btn pipe-policy-warn"
                  title="Review-needed fields recorded in SSOT provenance sidecar">
              review {reviewCount}
            </span>
          )}
          {signoffBlocked && (
            <span className="rb-btn pipe-policy-blocked"
                  title="Signoff is blocked by generated_default or review_needed critical fields">
              signoff blocked
            </span>
          )}
          {pipelineState && pipelineState.rtl_version_id && (
            <span className="rb-btn" title="RTL version under test">
              {pipelineState.rtl_version_id}
            </span>
          )}
          {runningCount > 0 && (
            <span className="rb-btn pipe-running-chip" title="running stages">
              ▶ {runningCount} running
            </span>
          )}
          {pipelineState && pipelineState.orchestrator && (
            <button className={`rb-btn pipe-orch-chip${pipelineState.orchestrator.enabled ? ' pipe-orch-chip-on' : ''}`}
                    title={`Toggle orchestrator mode. ON = enable durable JSON handoff queue under <ip>/handoff/.\nCurrently: ${pipelineState.orchestrator.enabled ? pipelineState.orchestrator.mode || 'on' : 'off'}`}
                    onClick={async () => {
                      const target = !pipelineState.orchestrator.enabled;
                      try {
                        const r = await fetch('/api/pipeline/orchestrator_mode', {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify({ enabled: target }),
                        });
                        const j = await r.json().catch(() => ({}));
                        const nextExec = (j && j.enabled) ? 'orchestrator' : 'single-worker';
                        window.ATLAS_EXEC_MODE = nextExec;
                        try { localStorage.setItem('atlasExecMode', nextExec); } catch (_) {}
                        try {
                          window.dispatchEvent(new CustomEvent('atlas-run-policy-changed', {
                            detail: { ...window.pipelinePolicyPayload(), exec_mode: nextExec },
                          }));
                        } catch (_) {}
                      } catch (e) {
                        console.error('[pipeline] orchestrator toggle failed', e);
                      }
                      // The state endpoint micro-cache was cleared server-side;
                      // force an immediate poll instead of waiting up to 2 s.
                      try { window.dispatchEvent(new CustomEvent('atlas:pipeline-poll')); } catch (_) {}
                    }}>
              orchestrator: <b>{pipelineState.orchestrator.enabled
                ? (pipelineState.orchestrator.mode || 'on')
                : 'off'}</b>
            </button>
          )}
          {pipelineState && pipelineState.orchestrator && pipelineState.orchestrator.pending_handoffs > 0 && (
            <span className="rb-btn pipe-handoff-chip"
                  title="Pending JSON handoffs waiting for /take">
              ⇄ {pipelineState.orchestrator.pending_handoffs} pending
              {pipelineState.orchestrator.claimed_handoffs > 0
                ? ` (${pipelineState.orchestrator.claimed_handoffs} claimed)`
                : ''}
            </span>
          )}
          {pipelineState && pipelineState.orchestrator && decisionReviewCount > 0 && (
            <button className="rb-btn pipe-review-chip"
                    disabled={!firstDecisionOpenPath}
                    title={firstDecisionTitle}
                    onClick={() => {
                      if (!firstDecisionOpenPath) return;
                      try {
                        window.dispatchEvent(new CustomEvent('atlas:open_evidence', {
                          detail: {
                            path: firstDecisionOpenPath,
                            source: 'pipeline-review',
                            decision: firstDecision,
                          },
                        }));
                      } catch (_) {}
                    }}>
              △ {decisionReviewCount} review
            </button>
          )}
          {fetchError && !pipelineState && (
            <span className="rb-btn" title={fetchError}>Pipeline state unavailable</span>
          )}
        </div>
        <span className="rb-spacer" />
        <span className="rb-meta">
          <span>stages <b>{Object.keys(stagesState).length || 15}</b></span>
          {ip && (
            <button className="rb-btn"
                    title="Open this IP in the Architect screen for the rich Status / Diagram view"
                    onClick={() => {
                      try {
                        localStorage.setItem('atlasScreen', 'architect');
                        window.location.reload();
                      } catch (_) {}
                    }}>◇ Open in Architect ▸</button>
          )}
        </span>
      </div>
      {(!ip || ip === 'default') && (
        <div className="pipe-empty-state" style={{
          padding: '14px 18px',
          margin: '0 18px',
          marginTop: 10,
          border: '1px dashed var(--line)',
          background: 'var(--bg-2)',
          color: 'var(--fg-mute)',
          fontFamily: 'var(--mono)',
          fontSize: 11.5,
          lineHeight: 1.55,
        }}>
          <div style={{ color: 'var(--fg)', marginBottom: 6 }}>
            <b>No IP selected.</b> Pick one from the IP list on the left to see live per-stage situation.
          </div>
          <div>
            Pipeline boards an IP through 14 canonical stages
            (ssot → fl/cl → equiv → rtl → lint/tb/syn → sim → coverage → sta → pnr).
            Each card will show 3-5 KPI dots, the latest evidence file path, and a <code>[▶ run]</code> button.
            Until you pick an IP, the cards stay idle.
          </div>
          <div style={{ marginTop: 8, color: 'var(--fg-dim)' }}>
            Need the SoC structure / module status grid / block diagram instead? Click <b>◇ Architect</b> at the top.
          </div>
        </div>
      )}

      {ip && ip !== 'default' && <div className="pipe-board"
           style={{ '--pipe-left-w': `${leftW}px`, '--pipe-right-w': `${rightW}px` }}>
        <div className="pipe-col-left">
          <StageStatusRail
            activeIp={ip}
            onSelectIp={setIp}
            state={pipelineState}
            simpleSummary={progressSummary}
            selectedStage={selectedStage}
            onSelectStage={setSelectedStage} />
          <OrchestratorTraceStrip ip={ip} />
        </div>
        <div className="pipe-resize-handle"
             title="Drag to resize left column"
             data-active={dragRef.current === 'left' ? 'yes' : 'no'}
             onMouseDown={beginDrag('left')} />
        <div className="pipe-col-center">
          <window.PipelineFlowControl
            ip={ip}
            state={pipelineState}
            selectedFlowId={selectedFlowId}
            onSelectFlow={setSelectedFlowId}
            selectedStage={selectedStage}
            onSelectStage={setSelectedStage} />
          <PendingQABanner ip={ip} />
          <OrchestratorAskUserBanner ip={ip} />
          <window.PipelineFlowMap
            ip={ip}
            state={pipelineState}
            selectedFlowId={selectedFlowId}
            selectedStage={selectedStage}
            onSelectFlow={setSelectedFlowId}
            onSelectStage={setSelectedStage} />
          <EnhancedFlowCanvas
            pipelineState={pipelineState}
            ip={ip}
            onSelectStage={setSelectedStage}
            selectedStage={selectedStage}
            selectedFlowId={selectedFlowId}
            onChain={addToChain} />
          <EnhancedDetailCards
            pipelineState={pipelineState}
            ip={ip}
            onSelectStage={setSelectedStage}
            onChain={addToChain} />
          <WorkerOrchestraBar
            ip={ip}
            currentTarget={chatTarget}
            onSelectTarget={(wf) => {
              setChatTarget(wf || 'orchestrator');
              const ownerId = (typeof window.ATLAS_USER_SESSION_ID === 'string' && window.ATLAS_USER_SESSION_ID)
                || (() => { try { return localStorage.getItem('atlasUserSessionId') || ''; } catch (_) { return ''; } })()
                || 'default';
              fetch('/api/session/activate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  session_id: ownerId,
                  ip: ip || 'default',
                  workflow: wf || 'orchestrator',
                  preserve_running: window.ATLAS_EXEC_MODE === 'orchestrator',
                }),
              }).catch(() => {});
            }} />
          <window.DispatchRail ip={ip}
                                chain={chain}
                                onClearChain={() => setChain([])}
                                onRemove={removeFromChain} />
        </div>
        <div className="pipe-resize-handle"
             title="Drag to resize chat panel"
             data-active={dragRef.current === 'right' ? 'yes' : 'no'}
             onMouseDown={beginDrag('right')} />
        <div className="pipe-col-right">
          <PipelineOrchestratorChatPanel ip={ip} />
        </div>
      </div>}
    </div>
  );
};
