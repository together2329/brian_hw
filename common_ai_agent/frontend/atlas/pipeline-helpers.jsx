// pipeline-helpers.jsx — Phase 27 refactor: pipelineInitialIp + readPipeWidth
// extracted from pipeline.jsx so the latter drops further toward <1000.
//
// Same IIFE + 2-tier dep wiring as pipeline-trace.jsx (Phase 20).

(() => {

// Data deps (direct bind — pipeline.jsx exposed before this loads):
const ENH_LANE_HINTS = window.ENH_LANE_HINTS;
const ENH_LANE_NAMES = window.ENH_LANE_NAMES;
const ENH_LANE_X = window.ENH_LANE_X;
const ENH_NODE_H = window.ENH_NODE_H;
const ENH_NODE_W = window.ENH_NODE_W;
const ENH_PILL_LABEL = window.ENH_PILL_LABEL;
const ENH_ROUTE_EDGES = window.ENH_ROUTE_EDGES;
const ENH_ROW_Y = window.ENH_ROW_Y;
const ENH_STAGE_LAYOUT = window.ENH_STAGE_LAYOUT;
const PIPE_LAYOUT_VERSION = window.PIPE_LAYOUT_VERSION;
const PIPE_LEFT_DEFAULT = window.PIPE_LEFT_DEFAULT;
const PIPE_LEFT_MAX = window.PIPE_LEFT_MAX;
const PIPE_LEFT_MIN = window.PIPE_LEFT_MIN;
const PIPE_RIGHT_DEFAULT = window.PIPE_RIGHT_DEFAULT;
const PIPE_RIGHT_MAX = window.PIPE_RIGHT_MAX;
const PIPE_RIGHT_MIN = window.PIPE_RIGHT_MIN;

// Function deps (lambda forward-ref):
const EnhancedDetailCards = (...a) => window.EnhancedDetailCards(...a);
const EnhancedFlowCanvas = (...a) => window.EnhancedFlowCanvas(...a);
const HierarchyList = (...a) => window.HierarchyList(...a);
const OrchestratorAskUserBanner = (...a) => window.OrchestratorAskUserBanner(...a);
const OrchestratorTraceStrip = (...a) => window.OrchestratorTraceStrip(...a);
const PendingQABanner = (...a) => window.PendingQABanner(...a);
const PipelineOrchestratorChatPanel = (...a) => window.PipelineOrchestratorChatPanel(...a);
const StageStatusRail = (...a) => window.StageStatusRail(...a);
const WorkerOrchestraBar = (...a) => window.WorkerOrchestraBar(...a);
const clampPipeWidth = (...a) => window.clampPipeWidth(...a);
const pipelineIpFromActiveNamespace = (...a) => window.pipelineIpFromActiveNamespace(...a);


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
    return window.readPipeWidth('atlasPipeLeftW', PIPE_LEFT_DEFAULT, PIPE_LEFT_MIN, PIPE_LEFT_MAX);
  });
  const [rightW, setRightW] = React.useState(() => {
    return window.readPipeWidth('atlasPipeRightW', PIPE_RIGHT_DEFAULT, PIPE_RIGHT_MIN, PIPE_RIGHT_MAX);
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
        const w = clampPipeWidth(startLeft + dx, PIPE_LEFT_DEFAULT, PIPE_LEFT_MIN, PIPE_LEFT_MAX);
        setLeftW(w);
      } else if (edge === 'right') {
        const w = clampPipeWidth(startRight - dx, PIPE_RIGHT_DEFAULT, PIPE_RIGHT_MIN, PIPE_RIGHT_MAX);
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
  React.useEffect(() => {
    try { localStorage.setItem('atlasPipeLayoutVersion', PIPE_LAYOUT_VERSION); } catch (_) {}
  }, []);
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
    const ownerId = ((window.ATLAS_USER && window.ATLAS_USER.username) || '')
      || (typeof window.ATLAS_USER_SESSION_ID === 'string' && window.ATLAS_USER_SESSION_ID)
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
      if (window.backend) {
        if (typeof window.backend.switchSession === 'function') {
          window.backend.switchSession(namespace);
        } else if (typeof window.backend.connect === 'function') {
          window.backend.connect(namespace);
        }
      }
      window.dispatchEvent(new CustomEvent('atlas-session-switched', {
        detail: { sessionId: ownerId, namespace, ip: ip || 'default', workflow: 'orchestrator' },
      }));
    } catch (_) {}
    fetch('/api/session/activate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        owner: ownerId,
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
              const ownerId = ((window.ATLAS_USER && window.ATLAS_USER.username) || '')
                || (typeof window.ATLAS_USER_SESSION_ID === 'string' && window.ATLAS_USER_SESSION_ID)
                || (() => { try { return localStorage.getItem('atlasUserSessionId') || ''; } catch (_) { return ''; } })()
                || 'default';
              fetch('/api/session/activate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  owner: ownerId,
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
          <PipelineOrchestratorChatPanel ip={ip} pipelineState={pipelineState} />
        </div>
      </div>}
    </div>
  );
};

// Phase 20: expose pipeline-trace.jsx deps + receive components back.
window.ENH_LANE_HINTS = ENH_LANE_HINTS;
window.ENH_LANE_NAMES = ENH_LANE_NAMES;
window.ENH_LANE_X = ENH_LANE_X;
window.ENH_NODE_H = ENH_NODE_H;
window.ENH_NODE_W = ENH_NODE_W;
window.ENH_PILL_LABEL = ENH_PILL_LABEL;
window.ENH_ROUTE_EDGES = ENH_ROUTE_EDGES;
window.ENH_ROW_Y = ENH_ROW_Y;
window.ENH_STAGE_LAYOUT = ENH_STAGE_LAYOUT;


// Phase 27 window exports:
// readPipeWidth extracted to pipe-width.jsx in Phase 31.
window.pipelineInitialIp = pipelineInitialIp;

})();
