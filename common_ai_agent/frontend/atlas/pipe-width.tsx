// pipe-width.tsx — TypeScript migration of pipe-width.jsx.
//
// pipe-width.jsx — Phase 31 refactor: readPipeWidth extracted from
// pipeline-helpers.jsx (was 1010L → drops under 1000).
//
// Migration notes (vs pipe-width.jsx):
//   - Proper ES module: no in-browser-babel IIFE wrapper; statements run at
//     module scope (preserving original order so every window.X bridge still
//     executes). The original was wrapped in `(() => { ... })()`.
//   - Cross-file globals OWNED BY OTHER FILES are kept as window.* references.
//     The originals were bare identifiers resolved off the shared global scope
//     (PIPE_LAYOUT_VERSION / clampPipeWidth from pipeline.jsx, PIPELINE_STAGES
//     from soc-architect.jsx). In a real module those don't resolve, so they
//     are read via window.* — runtime behaviour is identical. These globals are
//     not yet in types/atlas-window.d.ts, so a narrow `win` cast is used.
//   - This file's OWN public globals become real exports plus a transitional
//     window.* bridge at the bottom for not-yet-migrated .jsx consumers.

// ── Narrow cast for undeclared cross-file + own globals ───────────────
// types/atlas-window.d.ts does not (yet) declare the pipeline surface, so
// reference it through a locally-typed view of window. This preserves the
// exact runtime reads/writes without spraying `any` across call sites.
interface PipelineWindow {
  PIPE_LAYOUT_VERSION?: string;
  clampPipeWidth?: (value: unknown, fallback: number, min: number, max: number) => number;
  PIPELINE_STAGES?: string[];
  atlasData?: { fetchWorkerSnapshot?: (opts: WorkerSnapshotOpts) => Promise<unknown> } & Record<string, unknown>;
  ATLAS_RUN_MODE?: string;
  ATLAS_EXEC_MODE?: string;
  ATLAS_WORKSPACE_SESSION_ID?: unknown;
  ACTIVE_SESSION?: string;

  PIPELINE_STAGE_DEPS?: Record<string, string[]>;
  PIPELINE_STAGE_WORKFLOW?: Record<string, string>;
  PIPELINE_WORKFLOW_PRIMARY_STAGE?: Record<string, string>;
  PIPELINE_WORKSPACE_WORKFLOWS?: Set<string>;
  pipelineWorkflowForStage?: (stageId?: string) => string;
  pipelineDefaultWorkspacePath?: (
    ip?: string,
    workflow?: string,
    stageId?: string,
    evidencePaths?: unknown[],
  ) => string;
  openPipelineWorkflowWorkspace?: (opts?: OpenWorkspaceOpts) => void;
  PIPELINE_PHASES?: PipelinePhase[];
  PIPELINE_SWIMLANES?: PipelineSwimlane[];
  PIPELINE_VIRTUAL_NODES?: Record<string, PipelineVirtualNode>;
  PIPELINE_NODE_LAYOUT?: Record<string, PipelineNodeLayout>;
  PIPELINE_FLOW_DEFS?: PipelineFlowDef[];
  pipelineActualStages?: (stages?: string[]) => string[];
  pipelinePolicyPayload?: () => PipelinePolicyPayload;
  PIPELINE_STATE_META?: Record<string, PipelineStateMeta>;
  pipelineStateMeta?: (state?: string) => PipelineStateMeta;
  readPipeWidth?: (key: string, fallback: number, min: number, max: number) => number;
  pipelineFetchWorkerSnapshot?: (opts?: WorkerSnapshotOpts) => Promise<unknown>;
}

const win = window as unknown as PipelineWindow & Window;

// ── Types for this file's data + helper shapes ────────────────────────
export interface WorkerSnapshotOpts {
  activeOnly?: boolean;
  active_only?: boolean;
  ip?: string;
  [key: string]: unknown;
}

export interface OpenWorkspaceOpts {
  ip?: string;
  workflow?: string;
  stageId?: string;
  path?: string;
}

export interface PipelinePhase {
  id: string;
  stages: string[];
}

export interface PipelineSwimlane {
  id: string;
  title: string;
  x: number;
  width: number;
}

export interface PipelineVirtualNode {
  label: string;
  sub: string;
  state: string;
}

export interface PipelineNodeLayout {
  lane: string;
  y: number;
}

export interface PipelineFlowDef {
  id: string;
  name: string;
  summary: string;
  stages: string[];
}

export interface PipelinePolicyPayload {
  run_mode: string;
  exec_mode: string;
  workspace_session?: string;
}

export interface PipelineStateMeta {
  color: string;
  glyph: string;
  label: string;
}

export function readPipeWidth(key: string, fallback: number, min: number, max: number): number {
  try {
    if (localStorage.getItem('atlasPipeLayoutVersion') !== win.PIPE_LAYOUT_VERSION) return fallback;
    return win.clampPipeWidth!(localStorage.getItem(key), fallback, min, max);
  } catch (_) {
    return fallback;
  }
}

function pipelineWorkspaceSessionParam(): string {
  const explicit = String(win.ATLAS_WORKSPACE_SESSION_ID || '').trim();
  if (explicit) return explicit;
  const parts = String(win.ACTIVE_SESSION || '').split('/').filter(Boolean);
  return parts.length >= 4 ? parts[1] || '' : '';
}

export async function pipelineFetchWorkerSnapshot(opts: WorkerSnapshotOpts = {}): Promise<unknown> {
  const api = win.atlasData || {};
  if (typeof api.fetchWorkerSnapshot === 'function') {
    return api.fetchWorkerSnapshot(opts);
  }
  const params = new URLSearchParams();
  const activeOnly = opts.activeOnly !== false && opts.active_only !== false;
  if (activeOnly) params.set('active_only', '1');
  const ip = String(opts.ip || '').trim();
  if (ip && ip !== 'default') params.set('ip', ip);
  const workspaceSession = pipelineWorkspaceSessionParam();
  if (workspaceSession) params.set('workspace_session', workspaceSession);
  const query = params.toString();
  const r = await fetch(`/api/orchestrator/workers${query ? `?${query}` : ''}`, { cache: 'no-store' });
  if (!r.ok) throw new Error(`workers ${r.status}`);
  return r.json();
}

(function injectPipelineHelpers() {
  // Hard-coded copy of _PIPELINE_STAGE_DEPS from src/atlas_api_jobs.py.
  // The frontend can't introspect Python; refresh by hand if the
  // backend graph ever changes (it has been stable for months).
  win.PIPELINE_STAGE_DEPS = {
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
    'contract-check': ['sim-debug'],
    'goal-audit': ['contract-check'],
    'sta': ['syn'],
    'pnr': ['syn'],
    'sta-post': ['pnr'],
  };
  win.PIPELINE_STAGE_WORKFLOW = {
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
    'contract-check': 'contract-reflection',
    syn: 'syn',
    sta: 'sta',
    pnr: 'pnr',
    'sta-post': 'sta-post',
    'goal-audit': 'goal-audit',
  };
  win.PIPELINE_WORKFLOW_PRIMARY_STAGE = {
    'ssot-gen': 'ssot',
    'fl-model-gen': 'fl-model',
    'rtl-gen': 'rtl',
    lint: 'lint',
    'tb-gen': 'tb',
    sim: 'sim',
    coverage: 'coverage',
    sim_debug: 'sim-debug',
    'contract-reflection': 'contract-check',
    syn: 'syn',
    sta: 'sta',
    pnr: 'pnr',
    'sta-post': 'sta-post',
    'goal-audit': 'goal-audit',
  };
  win.PIPELINE_WORKSPACE_WORKFLOWS = new Set(Object.keys(win.PIPELINE_WORKFLOW_PRIMARY_STAGE));
  win.pipelineWorkflowForStage = function pipelineWorkflowForStage(stageId?: string): string {
    return (win.PIPELINE_STAGE_WORKFLOW || {})[stageId as string] || stageId || '';
  };
  win.pipelineDefaultWorkspacePath = function pipelineDefaultWorkspacePath(
    ip?: string,
    workflow?: string,
    stageId?: string,
    evidencePaths?: unknown[],
  ): string {
    const paths = (Array.isArray(evidencePaths) ? evidencePaths.filter(Boolean) : []) as string[];
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
    if (wf === 'contract-reflection' || id === 'contract-check') return `${ip}/signoff/contract_check.json`;
    if (wf === 'syn' || id === 'syn') return `${ip}/syn/syn_report.md`;
    if (wf === 'sta' || id === 'sta') return `${ip}/sta/sta_report.md`;
    if (wf === 'pnr' || id === 'pnr') return `${ip}/pnr/pnr_report.md`;
    if (wf === 'sta-post' || id === 'sta-post') return `${ip}/sta/sta_post_report.md`;
    if (wf === 'goal-audit' || id === 'goal-audit') return `${ip}/sim/fl_rtl_goal_audit.json`;
    return paths[0] || '';
  };
  win.openPipelineWorkflowWorkspace = function openPipelineWorkflowWorkspace({ ip, workflow, stageId, path }: OpenWorkspaceOpts = {}): void {
    const wf = String(workflow || win.pipelineWorkflowForStage!(stageId) || '').trim();
    const targetIp = String(ip || '').trim();
    if (!targetIp || !wf) return;
    const stage = stageId || (win.PIPELINE_WORKFLOW_PRIMARY_STAGE || {})[wf] || '';
    const resolvedPath = path || (
      win.pipelineDefaultWorkspacePath
        ? win.pipelineDefaultWorkspacePath(targetIp, wf, stage, [])
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
  // Phase taxonomy matches artifacts/runtime/ATLAS_UI_ENHANCEMENT/Pipeline Image.html mockup:
  // 6 phases — SSOT, MODELS, RTL, BRANCH, VERIFY·EDA, SIGNOFF.
  win.PIPELINE_PHASES = [
    { id: 'SSOT',       stages: ['ssot'] },
    { id: 'MODELS',     stages: ['fl-model', 'cl-model', 'equivalence'] },
    { id: 'RTL',        stages: ['rtl'] },
    { id: 'BRANCH',     stages: ['lint', 'tb', 'sim'] },
    { id: 'VERIFY·EDA', stages: ['sim-debug', 'coverage', 'syn', 'sta'] },
    { id: 'SIGNOFF',    stages: ['pnr', 'sta-post', 'contract-check', 'goal-audit'] },
  ];

  // Graph-first Pipeline layout. Coordinates are SVG viewBox units for a
  // 1200×620 map; CSS scales the whole map to the available viewport.
  win.PIPELINE_SWIMLANES = [
    { id: 'req',    title: 'REQUIREMENTS / SSOT', x: 55,   width: 170 },
    { id: 'model',  title: 'MODELS / GOALS',      x: 250,  width: 185 },
    { id: 'build',  title: 'RTL / TB AUTHORING',  x: 462,  width: 200 },
    { id: 'verify', title: 'VERIFY / DEBUG',      x: 696,  width: 210 },
    { id: 'eda',    title: 'EDA SIGNOFF',         x: 938,  width: 150 },
    { id: 'orch',   title: 'ORCHESTRATOR',        x: 1106, width: 150 },
  ];
  win.PIPELINE_VIRTUAL_NODES = {
    orchestrator: { label: 'Orchestrator', sub: 'route / retry / stale', state: 'virtual' },
    handoff:      { label: 'Handoff JSON', sub: 'pending / claimed', state: 'virtual' },
    take:         { label: '/take',        sub: 'workspace claim', state: 'virtual' },
    worker:       { label: 'Worker',       sub: 'workflow lease', state: 'virtual' },
  };
  win.PIPELINE_NODE_LAYOUT = {
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
    'contract-check': { lane: 'verify', y: 492 },
    'goal-audit': { lane: 'eda',    y: 540 },
    syn:          { lane: 'eda',    y: 150 },
    sta:          { lane: 'eda',    y: 250 },
    pnr:          { lane: 'eda',    y: 350 },
    'sta-post':   { lane: 'eda',    y: 450 },
    orchestrator: { lane: 'orch',   y: 178 },
    handoff:      { lane: 'orch',   y: 278 },
    take:         { lane: 'orch',   y: 378 },
    worker:       { lane: 'orch',   y: 478 },
  };
  win.PIPELINE_FLOW_DEFS = [
    {
      id: 'full',
      name: 'Full IP pipeline',
      summary: 'SSOT through model, RTL, verification, coverage, and signoff audit.',
      stages: ['ssot', 'fl-model', 'cl-model', 'equivalence', 'rtl', 'lint', 'tb', 'sim', 'coverage', 'sim-debug', 'syn', 'sta', 'pnr', 'sta-post', 'contract-check', 'goal-audit'],
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
  win.pipelineActualStages = function pipelineActualStages(stages?: string[]): string[] {
    const real = new Set(win.PIPELINE_STAGES || []);
    return (stages || []).filter(s => real.has(s));
  };
  win.pipelinePolicyPayload = function pipelinePolicyPayload(): PipelinePolicyPayload {
    const normRun = (value: unknown): string => {
      const v = String(value || '').trim().toLowerCase().replace(/_/g, '-');
      if (v === 'eng') return 'engineering';
      if (v === 'sign-off') return 'signoff';
      return ['starter', 'engineering', 'signoff'].indexOf(v) >= 0 ? v : 'engineering';
    };
    const normExec = (value: unknown): string => {
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
    const explicitWorkspace = String(win.ATLAS_WORKSPACE_SESSION_ID || '').trim();
    const activeParts = String(win.ACTIVE_SESSION || '').split('/').filter(Boolean);
    const workspaceSession = explicitWorkspace || (activeParts.length >= 4 ? activeParts[1] || '' : '');
    return {
      run_mode: normRun(win.ATLAS_RUN_MODE || savedRun),
      exec_mode: normExec(win.ATLAS_EXEC_MODE || savedExec),
      ...(workspaceSession ? { workspace_session: workspaceSession } : {}),
    };
  };

  // ── Color / glyph map for state badges ──────────────────────────
  // Backend states from /api/pipeline/state contract (see plan).
  // Falls back to generic 'idle' if the value isn't recognised.
  win.PIPELINE_STATE_META = {
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
  win.pipelineStateMeta = function pipelineStateMeta(state?: string): PipelineStateMeta {
    return win.PIPELINE_STATE_META![state as string] || win.PIPELINE_STATE_META!.idle;
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

// ── Transitional bridge: register on window for not-yet-migrated .jsx ──
// pipeline-trace-workers.tsx resolves pipelineFetchWorkerSnapshot off window at
// render time (the original pipeline-trace.jsx called it as a bare shared-scope
// global). Register it here, where it is defined, so the consumer resolves it.
win.readPipeWidth = readPipeWidth;
win.pipelineFetchWorkerSnapshot = pipelineFetchWorkerSnapshot;
