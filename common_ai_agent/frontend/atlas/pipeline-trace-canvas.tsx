// pipeline-trace-canvas.tsx — EnhancedFlowCanvas extracted from
// pipeline-trace.tsx (Phase: sub-1000 split). The flow visualization canvas:
// renders the orchestrator hub, 6 lanes, bus-bar arrows, stage nodes and the
// active route edges as an SVG. Owns its own `win.EnhancedFlowCanvas` bridge.
import { type EnhancedFlowCanvasProps } from './pipeline-trace-shared';
import {
  win,
  ENH_LANE_HINTS,
  ENH_LANE_NAMES,
  ENH_LANE_X,
  ENH_NODE_H,
  ENH_NODE_W,
  ENH_PILL_LABEL,
  ENH_ROUTE_EDGES,
  ENH_ROW_Y,
  ENH_STAGE_LAYOUT,
  enhSubText,
} from './pipeline-trace-shared';

export function EnhancedFlowCanvas({ pipelineState, ip, onSelectStage, selectedStage, selectedFlowId, onChain }: EnhancedFlowCanvasProps) {
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
    const order = ['ssot', 'fl-model', 'cl-model', 'equivalence', 'rtl', 'lint', 'tb', 'sim', 'syn', 'sim-debug', 'coverage', 'sta', 'pnr', 'sta-post', 'contract-check', 'goal-audit'];
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

// Phase 20 window export — pipeline.jsx aliases this back via forward-ref lambda.
win.EnhancedFlowCanvas = EnhancedFlowCanvas;
