// pipeline-trace.tsx — TypeScript migration of pipeline-trace.jsx.
//
// pipeline-trace.jsx — Phase 20 refactor: orchestrator trace + flow canvas
// extracted from pipeline.jsx (was 3272L, just over the 2000-line target).
//
//   1. EnhancedFlowCanvas       (182L)  flow visualization canvas
//   2. WorkerOrchestraBar       (140L)  per-worker status bar
//   3. OrchestratorTraceStrip  (1066L)  trace timeline + run inspector
//
// Total: ~1388L extracted. pipeline.jsx drops to ~1901 (under 2000).
//
// Load order (index.html): pipeline.jsx loads FIRST (exposes deps via
// `window.X = X` at end), then this file loads + binds them directly.
// pipeline.jsx's end-of-file aliases-back for our 3 components use
// lambda forward-refs so they survive the chicken-and-egg load order.
//
// Migration notes (vs pipeline-trace.jsx):
//   - Proper ES module: the original `(() => { ... })()` IIFE is unwrapped to
//     module scope (ES modules have their own scope). Statement order is
//     preserved so every `window.X = X` bridge still runs at the same point.
//   - `React.useState`/`useEffect`/`useMemo` rewritten to named hook imports.
//   - Cross-file globals OWNED BY OTHER FILES (pipeline.jsx data + components,
//     soc-architect.jsx PIPELINE_*, pipe-width.jsx helpers, pipeline-flow-
//     stage.jsx StageCard) are kept as window.* reads — runtime is identical.
//     They are not yet declared in types/atlas-window.d.ts, so a narrow `win`
//     cast (matching pipe-width.tsx) is used. The lambda forward-refs the
//     original used for enhSubText / EnhancedDetailCards / HierarchyList are
//     preserved verbatim (they route call-sites through window).
//   - This file's OWN public globals (EnhancedFlowCanvas, WorkerOrchestraBar,
//     OrchestratorTraceStrip, MiniScoresheet, DispatchRail, FlowInspector,
//     PipelineFlowControl) become real exports plus transitional window.*
//     bridges for not-yet-migrated .jsx consumers.
import { useState, useEffect, useMemo, type ReactNode, type ChangeEvent, type MouseEvent } from 'react';

// ── Narrow cast for undeclared cross-file + own globals ───────────────
// types/atlas-window.d.ts does not (yet) declare the pipeline surface, so
// reference it through a locally-typed view of window. This preserves the
// exact runtime reads/writes without spraying `any` across call sites.
interface PipelineTraceWindow {
  // Data constants owned by pipeline.jsx (the enhanced flow canvas layout).
  ENH_LANE_HINTS?: Record<number, string>;
  ENH_LANE_NAMES?: Record<number, string>;
  ENH_LANE_X?: Record<number, number>;
  ENH_NODE_H?: number;
  ENH_NODE_W?: number;
  ENH_PILL_LABEL?: Record<string, string>;
  ENH_ROUTE_EDGES?: EnhRouteEdge[];
  ENH_ROW_Y?: Record<number, number>;
  ENH_STAGE_LAYOUT?: Record<string, EnhStagePos>;

  // Function / component deps owned by pipeline.jsx.
  enhSubText?: (stageId: string, info: unknown) => string;
  EnhancedDetailCards?: (...args: unknown[]) => ReactNode;
  HierarchyList?: (...args: unknown[]) => ReactNode;

  // Pipeline data + helpers owned by pipe-width.jsx / soc-architect.jsx.
  PIPELINE_FLOW_DEFS?: PipelineFlowDef[];
  PIPELINE_WORKSPACE_WORKFLOWS?: Set<string>;
  PIPELINE_LABEL?: Record<string, string>;
  PIPELINE_STAGES?: string[];
  PIPELINE_VIRTUAL_NODES?: Record<string, PipelineVirtualNode>;
  pipelineActualStages?: (stages?: string[]) => string[];
  pipelinePolicyPayload?: () => Record<string, unknown>;
  pipelineFetchWorkerSnapshot?: (opts?: WorkerSnapshotOpts) => Promise<WorkerSnapshot>;
  openPipelineWorkflowWorkspace?: (opts?: { ip?: string; workflow?: string }) => void;

  // StageCard owned by pipeline-flow-stage.jsx.
  StageCard?: (props: StageCardProps) => ReactNode;

  // This file's OWN public globals (bridged at the bottom).
  EnhancedFlowCanvas?: (props: EnhancedFlowCanvasProps) => ReactNode;
  WorkerOrchestraBar?: (props: WorkerOrchestraBarProps) => ReactNode;
  OrchestratorTraceStrip?: (props: OrchestratorTraceStripProps) => ReactNode;
  MiniScoresheet?: (props: MiniScoresheetProps) => ReactNode;
  DispatchRail?: (props: DispatchRailProps) => ReactNode;
  FlowInspector?: (props: FlowInspectorProps) => ReactNode;
  PipelineFlowControl?: (props: PipelineFlowControlProps) => ReactNode;
}

const win = window as unknown as PipelineTraceWindow & Window;

// ── Shared data shapes ────────────────────────────────────────────────
interface EnhRouteEdge {
  id: string;
  from: string;
  to: string;
  d: string;
  bidir?: boolean;
  reverseD?: string;
}

interface EnhStagePos {
  lane: number;
  row: number;
}

interface PipelineFlowDef {
  id: string;
  name: string;
  summary?: string;
  stages?: string[];
}

interface PipelineVirtualNode {
  label: string;
  sub: string;
  state?: string;
}

interface StageInfo {
  state?: string;
  top?: string;
  secondary?: string;
  locked_reason?: string;
  [key: string]: unknown;
}

interface PipelineState {
  stages?: Record<string, StageInfo>;
  orchestrator?: {
    enabled?: boolean;
    active_target?: string;
    pending_handoffs?: number;
    [key: string]: unknown;
  };
  [key: string]: unknown;
}

interface StageCardProps {
  stageId: string;
  info: StageInfo;
  ip?: string;
  onChain?: (stageId: string) => void;
}

// Data constants (accessed as `ENH_LANE_NAMES[k]` — must be the real object,
// not a lambda; pipeline.jsx exposed them before this IIFE runs):
const ENH_LANE_HINTS = win.ENH_LANE_HINTS as Record<number, string>;
const ENH_LANE_NAMES = win.ENH_LANE_NAMES as Record<number, string>;
const ENH_LANE_X = win.ENH_LANE_X as Record<number, number>;
const ENH_NODE_H = win.ENH_NODE_H as number;
const ENH_NODE_W = win.ENH_NODE_W as number;
const ENH_PILL_LABEL = win.ENH_PILL_LABEL as Record<string, string>;
const ENH_ROUTE_EDGES = win.ENH_ROUTE_EDGES as EnhRouteEdge[];
const ENH_ROW_Y = win.ENH_ROW_Y as Record<number, number>;
const ENH_STAGE_LAYOUT = win.ENH_STAGE_LAYOUT as Record<string, EnhStagePos>;

// Function / component deps (lambda forward-ref so call-site lookups go through window):
const enhSubText = (...a: Parameters<NonNullable<PipelineTraceWindow['enhSubText']>>) => win.enhSubText!(...a);
const EnhancedDetailCards = (...a: unknown[]) => win.EnhancedDetailCards!(...a);
const HierarchyList = (...a: unknown[]) => win.HierarchyList!(...a);

// StageCard is owned by pipeline-flow-stage.jsx. The original rendered it as
// `<window.StageCard ...>` (resolved at render time); a forward-ref lambda
// preserves that exact lazy lookup while giving JSX a non-optional component.
const StageCard = (props: StageCardProps) => win.StageCard!(props);


interface EnhancedFlowCanvasProps {
  pipelineState?: PipelineState;
  ip?: string;
  onSelectStage?: (stageId: string) => void;
  selectedStage?: string;
  selectedFlowId?: string;
  onChain?: (stageId: string) => void;
}

function EnhancedFlowCanvas({ pipelineState, ip, onSelectStage, selectedStage, selectedFlowId, onChain }: EnhancedFlowCanvasProps) {
  const stagesState = (pipelineState && pipelineState.stages) || {};
  const orch = (pipelineState && pipelineState.orchestrator) || {};
  const runningEntry = Object.entries(stagesState).find(([, s]) => s && s.state === 'running');
  const runningStageId = runningEntry ? runningEntry[0] : '';
  const runningLane = runningStageId ? (ENH_STAGE_LAYOUT[runningStageId] || {}).lane : 0;
  const targetWorker = runningStageId ? `${runningStageId}-worker` : (orch.active_target || 'orchestrator');
  const pendingHandoffs = orch.pending_handoffs != null ? orch.pending_handoffs : 0;

  // Compute the flow set: stages that belong to the currently-selected flow.
  // Used to dim stages not in flow + filter route edges.
  const flowDefs = (typeof window !== 'undefined' && win.PIPELINE_FLOW_DEFS) || [];
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


interface WorkerSnapshotOpts {
  ip?: string;
  activeOnly?: boolean;
  [key: string]: unknown;
}

interface TraceEvent {
  actor?: string;
  peer?: string;
  kind?: string;
  step?: number;
  corr?: string;
  lens?: string;
  status?: string;
  requested_workflow?: string;
  run_id?: string;
  detail?: string;
  gate?: string;
  reason?: string;
  [key: string]: unknown;
}

interface WorkerInfo {
  workflow: string;
  status?: string;
  running_count?: number;
  running?: Array<{ run_id?: string }>;
  model?: string;
  profile?: string;
  reasoning_effort?: string;
  toolchain?: string;
  mismatch_reasons?: string[];
  [key: string]: unknown;
}

interface WorkerSnapshot {
  orchestrator?: {
    enabled?: boolean;
    active_target?: string;
    [key: string]: unknown;
  };
  workers?: WorkerInfo[];
  [key: string]: unknown;
}

interface WorkerOrchestraBarProps {
  ip?: string;
  onSelectTarget?: (workflow: string) => void;
  currentTarget?: string;
}

function WorkerOrchestraBar({ ip, onSelectTarget, currentTarget }: WorkerOrchestraBarProps) {
  const [data, setData] = useState<WorkerSnapshot>({ orchestrator: {}, workers: [] });
  const [traceMap, setTraceMap] = useState<Record<string, TraceEvent>>({}); // worker -> latest event
  useEffect(() => {
    let dead = false;
    const fetchAll = async () => {
      try {
        const j = await win.pipelineFetchWorkerSnapshot!({ ip, activeOnly: true });
        if (!dead) setData(j || { workers: [] });
      } catch (_) {}
      try {
        if (!ip) return;
        const r2 = await fetch(`/api/orchestrator/trace?ip=${encodeURIComponent(ip)}&limit=30`);
        if (!r2.ok) return;
        const j2 = await r2.json();
        if (dead) return;
        const m: Record<string, TraceEvent> = {};
        const evs: TraceEvent[] = (j2 && j2.events) || [];
        for (const e of evs) {
          const a = e.actor || '';
          if (!a.endsWith('-worker')) continue;
          const wf = a.replace(/-worker$/, '');
          if (!m[wf] || (m[wf].step as number) < (e.step as number)) m[wf] = e;
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
  const kindArrow = (k?: string) => {
    if (!k) return { dir: 'none', color: 'muted', label: '' };
    if (k === 'http_send' || k === 'http_recv') return { dir: 'down', color: 'amber', label: 'dispatch' };
    if (k === 'http_accepted') return { dir: 'down', color: 'green', label: 'accepted' };
    if (k === 'http_rejected') return { dir: 'down', color: 'red', label: 'rejected' };
    if (k === 'run_completed') return { dir: 'up', color: 'cyan', label: 'completed' };
    if (k === 'gate_verdict') return { dir: 'up', color: 'purple', label: 'gate' };
    return { dir: 'none', color: 'muted', label: k };
  };
  const dataFlow = (w: WorkerInfo, ev?: TraceEvent) => {
    if (w.status === 'mismatch') return 'down';
    if (w.status !== 'ok') return 'down';
    if ((w.running_count as number) > 0) return 'dispatch';
    if (ev && ev.kind === 'run_completed') return 'return';
    return 'idle';
  };
  const flowArrow = (flow: string) => {
    if (flow === 'dispatch') return '↓';
    if (flow === 'return') return '↑';
    if (flow === 'down') return '✗';
    return '·';
  };
  const stateLabel = (w: WorkerInfo) => {
    if (w.status === 'mismatch') return 'mismatch';
    if (w.status !== 'ok') return 'unreachable';
    if ((w.running_count as number) > 0) return `run #${w.running && w.running[0] && w.running[0].run_id ? w.running[0].run_id.slice(-6) : '?'}`;
    return 'idle';
  };
  const runningTotal = workers.filter(w => (w.running_count as number) > 0).length;
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
          const live = (w.running_count as number) > 0;
          const reachable = w.status === 'ok';
          const mismatch = w.status === 'mismatch';
          const sel = currentTarget === w.workflow;
          const flow = dataFlow(w, ev);
          const opensWorkspace = win.PIPELINE_WORKSPACE_WORKFLOWS
            && win.PIPELINE_WORKSPACE_WORKFLOWS.has(w.workflow);
          return (
            <button key={w.workflow}
                    className="pipe-orchestra-worker worker-card"
                    data-flow={flow}
                    data-state={mismatch ? 'mismatch' : (reachable ? (live ? 'running' : 'idle') : 'down')}
                    data-selected={sel ? 'yes' : 'no'}
                    onClick={() => {
                      if (opensWorkspace && win.openPipelineWorkflowWorkspace) {
                        win.openPipelineWorkflowWorkspace({ ip, workflow: w.workflow });
                        return;
                      }
                      if (onSelectTarget) onSelectTarget(w.workflow);
                    }}
                    title={opensWorkspace
                      ? `Open ${w.workflow} workspace and history`
                      : (mismatch && w.mismatch_reasons && w.mismatch_reasons.length
                          ? w.mismatch_reasons.join('\n')
                          : `Click to set chat target to ${w.workflow}`)}>
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


interface OrchestratorTraceStripProps {
  ip?: string;
}

function OrchestratorTraceStrip({ ip }: OrchestratorTraceStripProps) {
  const [events, setEvents] = useState<TraceEvent[]>([]);
  const [open, setOpen] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);
  useEffect(() => {
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
  const corrGroups = useMemo(() => {
    const grouped = new Map<string, TraceEvent[]>();
    for (const e of events) {
      const c = e.corr || 'no_corr';
      if (!grouped.has(c)) grouped.set(c, []);
      grouped.get(c)!.push(e);
    }
    return [...grouped.entries()].slice(0, 6);
  }, [events]);
  const lensGlyph: Record<string, string> = { interaction: '⇄', intermediate: '◐', result: '✓' };
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
                  <span className="pipe-trace-glyph">{lensGlyph[e.lens as string] || '·'}</span>
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

// it up (workspace.jsx wires the listener).
interface ScoresheetDot {
  state?: string;
  label?: string;
  evidence_path?: string;
}

interface MiniScoresheetProps {
  scoresheet?: Array<ScoresheetDot | string>;
  evidencePaths?: string[];
}

export function MiniScoresheet({ scoresheet, evidencePaths }: MiniScoresheetProps) {
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
}

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
// with the chained stages so the backend resolves dep order itself.
interface DispatchRailProps {
  ip?: string;
  chain: string[];
  onClearChain?: () => void;
  onRemove?: (stage: string) => void;
}

export function DispatchRail({ ip, chain, onClearChain, onRemove }: DispatchRailProps) {
  const [schedule, setSchedule] = useState('auto');
  const [busy, setBusy] = useState(false);
  const labels = win.PIPELINE_LABEL || {};
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
          ...win.pipelinePolicyPayload!(),
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
}

// ─── FlowInspector ────────────────────────────────────────────────
//
// Right-side panel inspired by the reference screenshots: selectable flows on
// top, numbered steps below, and a focused stage detail/action area.
interface FlowInspectorProps {
  ip?: string;
  state?: PipelineState;
  selectedFlowId?: string;
  onSelectFlow?: (id: string) => void;
  selectedStage?: string;
  onSelectStage?: (id: string) => void;
  onChain?: (stageId: string) => void;
}

export function FlowInspector({
  ip,
  state,
  selectedFlowId,
  onSelectFlow,
  selectedStage,
  onSelectStage,
  onChain,
}: FlowInspectorProps) {
  const [busyFlow, setBusyFlow] = useState('');
  const flows = win.PIPELINE_FLOW_DEFS || [];
  const labels = win.PIPELINE_LABEL || {};
  const actualSet = new Set(win.PIPELINE_STAGES || []);
  const stagesState = (state && state.stages) || {};
  const flow = flows.find(f => f.id === selectedFlowId) || flows[0] || { stages: [] } as unknown as PipelineFlowDef;
  const selectedInfo = actualSet.has(selectedStage as string) ? stagesState[selectedStage as string] : null;

  const dispatchFlow = async () => {
    const stages = win.pipelineActualStages!(flow.stages || []);
    if (!ip || !stages.length || busyFlow) return;
    setBusyFlow(flow.id);
    try {
      const r = await fetch('/api/pipeline/dispatch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ip, stages, schedule: 'auto', prompt: '', ...win.pipelinePolicyPayload!() }),
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

  const flowCounts = (stages?: string[]) => {
    const real = win.pipelineActualStages!(stages || []);
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

  const stepLabel = (id: string) => {
    if ((win.PIPELINE_VIRTUAL_NODES || {})[id]) return win.PIPELINE_VIRTUAL_NODES![id].label;
    return labels[id] || id;
  };
  const stepState = (id: string) => {
    if ((win.PIPELINE_VIRTUAL_NODES || {})[id]) return 'handoff';
    return (stagesState[id] && stagesState[id].state) || 'idle';
  };
  const stepDetail = (id: string) => {
    const virtual = (win.PIPELINE_VIRTUAL_NODES || {})[id];
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
                        const firstActual = win.pipelineActualStages!(f.stages || [])[0];
                        if (firstActual && typeof onSelectStage === 'function') onSelectStage(firstActual);
                      }}>
                <span className="pipe-flow-choice-name">{f.name}</span>
                <span className="pipe-flow-choice-summary">{f.summary}</span>
                <span className="pipe-flow-choice-meta">
                  {counts.running ? `running ${counts.running} · ` : ''}
                  {counts.failed ? `failed ${counts.failed} · ` : ''}
                  {counts.blocked ? `blocked ${counts.blocked} · ` : ''}
                  passed {counts.passed}/{win.pipelineActualStages!(f.stages || []).length}
                </span>
              </button>
            );
          })}
        </div>
        <button className="rb-btn primary pipe-flow-run"
                disabled={!ip || !!busyFlow || !win.pipelineActualStages!(flow.stages || []).length}
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
          // StageCard is owned by pipeline-flow-stage.jsx; resolved off window
          // at render time exactly as the original `<window.StageCard ...>`.
          <StageCard
            stageId={selectedStage as string}
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
}

// ─── PipelineFlowControl ──────────────────────────────────────────
//
// Top-center flow selector. The user asked for flow/step controls not to sit
// under the graph; keep them in the center header so the map remains primary.
interface PipelineFlowControlProps {
  ip?: string;
  state?: PipelineState;
  selectedFlowId?: string;
  onSelectFlow?: (id: string) => void;
  selectedStage?: string;
  onSelectStage?: (id: string) => void;
}

export function PipelineFlowControl({
  ip,
  state,
  selectedFlowId,
  onSelectFlow,
  selectedStage,
  onSelectStage,
}: PipelineFlowControlProps) {
  const [busyFlow, setBusyFlow] = useState('');
  const flows = win.PIPELINE_FLOW_DEFS || [];
  const labels = win.PIPELINE_LABEL || {};
  const stagesState = (state && state.stages) || {};
  const flow = flows.find(f => f.id === selectedFlowId) || flows[0] || { stages: [] } as unknown as PipelineFlowDef;

  const flowCounts = (stages?: string[]) => {
    const real = win.pipelineActualStages!(stages || []);
    const counts: { running: number; passed: number; failed: number; blocked: number; total?: number } = { running: 0, passed: 0, failed: 0, blocked: 0 };
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

  const stepLabel = (id: string) => {
    if ((win.PIPELINE_VIRTUAL_NODES || {})[id]) return win.PIPELINE_VIRTUAL_NODES![id].label;
    return labels[id] || id;
  };
  const stepState = (id: string) => {
    if ((win.PIPELINE_VIRTUAL_NODES || {})[id]) return 'handoff';
    return (stagesState[id] && stagesState[id].state) || 'idle';
  };

  const dispatchFlow = async () => {
    const stages = win.pipelineActualStages!(flow.stages || []);
    if (!ip || !stages.length || busyFlow) return;
    setBusyFlow(flow.id);
    try {
      const r = await fetch('/api/pipeline/dispatch', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ip, stages, schedule: 'auto', prompt: '', ...win.pipelinePolicyPayload!() }),
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
                disabled={!ip || !!busyFlow || !win.pipelineActualStages!(flow.stages || []).length}
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
                      const firstActual = win.pipelineActualStages!(f.stages || [])[0];
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
}

// ─── Internal: HierarchyList ───────────────────────────────────────
//
// Left column lists every IP discovered via /api/ip/list. Selecting
// one updates the AtlasPipeline `ip` state. Falls back to a single-row


// Phase 20 window exports — pipeline.jsx aliases these back via forward-ref lambdas.
win.EnhancedFlowCanvas = EnhancedFlowCanvas;
win.WorkerOrchestraBar = WorkerOrchestraBar;
win.OrchestratorTraceStrip = OrchestratorTraceStrip;

// Phase 30: PipelineFlowMap + StageCard extracted to pipeline-flow-stage.jsx.

// ── Transitional bridges for the module-scope window globals ──
// (MiniScoresheet / DispatchRail / FlowInspector / PipelineFlowControl were
// `window.X = function...` definitions in the .jsx; keep them resolvable for
// not-yet-migrated .jsx consumers while exposing real exports above.)
win.MiniScoresheet = MiniScoresheet;
win.DispatchRail = DispatchRail;
win.FlowInspector = FlowInspector;
win.PipelineFlowControl = PipelineFlowControl;
