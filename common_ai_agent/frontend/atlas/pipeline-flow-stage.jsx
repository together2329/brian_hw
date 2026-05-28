// pipeline-flow-stage.jsx — Phase 30 refactor: PipelineFlowMap + StageCard
// extracted from pipeline-trace.jsx (was 1434L) so it drops under 1000.
//
// Same IIFE + 2-tier dep wiring (data via direct, function/component via lambda).

(() => {

const ENH_LANE_HINTS = window.ENH_LANE_HINTS;
const ENH_LANE_NAMES = window.ENH_LANE_NAMES;
const ENH_LANE_X = window.ENH_LANE_X;
const ENH_NODE_H = window.ENH_NODE_H;
const ENH_NODE_W = window.ENH_NODE_W;
const ENH_PILL_LABEL = window.ENH_PILL_LABEL;
const ENH_ROUTE_EDGES = window.ENH_ROUTE_EDGES;
const ENH_ROW_Y = window.ENH_ROW_Y;
const ENH_STAGE_LAYOUT = window.ENH_STAGE_LAYOUT;
const enhSubText = (...a) => window.enhSubText(...a);
const EnhancedDetailCards = (...a) => window.EnhancedDetailCards(...a);
const HierarchyList = (...a) => window.HierarchyList(...a);
const MiniScoresheet = (...a) => window.MiniScoresheet(...a);
const FlowInspector = (...a) => window.FlowInspector(...a);


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




})();
