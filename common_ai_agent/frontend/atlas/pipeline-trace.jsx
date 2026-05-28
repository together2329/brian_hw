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

(() => {

// Data constants (accessed as `ENH_LANE_NAMES[k]` — must be the real object,
// not a lambda; pipeline.jsx exposed them before this IIFE runs):
const ENH_LANE_HINTS = window.ENH_LANE_HINTS;
const ENH_LANE_NAMES = window.ENH_LANE_NAMES;
const ENH_LANE_X = window.ENH_LANE_X;
const ENH_NODE_H = window.ENH_NODE_H;
const ENH_NODE_W = window.ENH_NODE_W;
const ENH_PILL_LABEL = window.ENH_PILL_LABEL;
const ENH_ROUTE_EDGES = window.ENH_ROUTE_EDGES;
const ENH_ROW_Y = window.ENH_ROW_Y;
const ENH_STAGE_LAYOUT = window.ENH_STAGE_LAYOUT;

// Function / component deps (lambda forward-ref so call-site lookups go through window):
const enhSubText = (...a) => window.enhSubText(...a);
const EnhancedDetailCards = (...a) => window.EnhancedDetailCards(...a);
const HierarchyList = (...a) => window.HierarchyList(...a);


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


function WorkerOrchestraBar({ ip, onSelectTarget, currentTarget }) {
  const [data, setData] = React.useState({ orchestrator: {}, workers: [] });
  const [traceMap, setTraceMap] = React.useState({}); // worker -> latest event
  React.useEffect(() => {
    let dead = false;
    const fetchAll = async () => {
      try {
        const j = await pipelineFetchWorkerSnapshot({ ip, activeOnly: true });
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
    if (w.status === 'mismatch') return 'down';
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
    if (w.status === 'mismatch') return 'mismatch';
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
          const mismatch = w.status === 'mismatch';
          const sel = currentTarget === w.workflow;
          const flow = dataFlow(w, ev);
          const opensWorkspace = window.PIPELINE_WORKSPACE_WORKFLOWS
            && window.PIPELINE_WORKSPACE_WORKFLOWS.has(w.workflow);
          return (
            <button key={w.workflow}
                    className="pipe-orchestra-worker worker-card"
                    data-flow={flow}
                    data-state={mismatch ? 'mismatch' : (reachable ? (live ? 'running' : 'idle') : 'down')}
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


// Phase 20 window exports — pipeline.jsx aliases these back via forward-ref lambdas.
window.EnhancedFlowCanvas = EnhancedFlowCanvas;
window.WorkerOrchestraBar = WorkerOrchestraBar;
window.OrchestratorTraceStrip = OrchestratorTraceStrip;

})();
