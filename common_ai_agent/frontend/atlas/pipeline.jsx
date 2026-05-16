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

  // Phase bands used to group stage cards. Mirrors the layout sketch in
  // /Users/brian/.claude/plans/i-need-team-chat-magical-koala.md §Layout.
  window.PIPELINE_PHASES = [
    { id: 'AUTHOR',        stages: ['ssot'] },
    { id: 'DETERMINISTIC', stages: ['fl-model', 'cl-model', 'equivalence'] },
    { id: 'IMPLEMENT',     stages: ['rtl', 'lint', 'tb'] },
    { id: 'VERIFY',        stages: ['sim', 'coverage', 'sim-debug', 'goal-audit'] },
    { id: 'SIGN-OFF',      stages: ['syn', 'sta', 'pnr', 'sta-post'] },
  ];

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
                    data-state={stageState}
                    fill="var(--bg-2)"
                    stroke={meta.color}
                    strokeWidth="1.5" />
              <text x={NODE_W / 2} y={NODE_H / 2 + 4}
                    textAnchor="middle"
                    fontFamily="var(--mono)"
                    fontSize="10"
                    fontWeight="600"
                    fill={meta.color}>
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

// ─── MiniScoresheet ────────────────────────────────────────────────
//
// Render a 3–5 dot row from the backend's `scoresheet[]` array.
// Each value is one of 'pass' | 'warn' | 'fail' | 'idle'. Clicking a
// dot broadcasts an `open_evidence` custom event with the matching
// path from `evidence_paths[i]` so the existing FileViewer can pick
// it up (workspace.jsx wires the listener).
window.MiniScoresheet = function MiniScoresheet({ scoresheet, evidencePaths }) {
  const dots = Array.isArray(scoresheet) ? scoresheet : [];
  const paths = Array.isArray(evidencePaths) ? evidencePaths : [];
  if (!dots.length) return null;
  return (
    <div className="pipe-scoresheet">
      {dots.map((kpi, i) => {
        const path = paths[i] || paths[0] || '';
        return (
          <span key={i}
                className="pipe-dot"
                data-kpi={kpi || 'idle'}
                title={`${kpi || 'idle'}${path ? ` · ${path}` : ''}`}
                onClick={() => {
                  if (!path) return;
                  try {
                    window.dispatchEvent(new CustomEvent('atlas:open_evidence', {
                      detail: { path, kpi, source: 'pipeline' },
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
  const effort = data.effort || '';
  const top = data.top || '';
  const secondary = data.secondary || '';
  const liveTail = data.live_tail || '';
  const progress = data.progress;
  const evidencePaths = data.evidence_paths || [];

  return (
    <div className="pipe-stage-card"
         data-state={stageState}
         data-stage={stageId}
         ref={cardRef}
         onClick={onCardClick}
         title={isLocked ? 'Upstream not satisfied — locked' : undefined}>
      <div className="pipe-stage-row1">
        <span className="pipe-stage-glyph" style={{ color: meta.color }}>{glyph}</span>
        <span className="pipe-stage-label">{label}</span>
        <span className="pipe-stage-state" data-state={stageState}>{meta.label}</span>
        <span className="pipe-stage-spacer" />
        {iter && <span className="pipe-stage-meta">{iter}</span>}
        {dur && <span className="pipe-stage-meta">{dur}</span>}
        {model && <span className="pipe-stage-meta" title={effort ? `effort ${effort}` : ''}>{model}</span>}
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
        <button className="pipe-stage-run rb-btn"
                disabled={isLocked || isRunning || !ip}
                onClick={(e) => { e.stopPropagation(); dispatchOne(); }}>
          {isRunning ? '⏹ running' : '▶ run'}
        </button>
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

// ─── Internal: HierarchyList ───────────────────────────────────────
//
// Left column lists every IP discovered via /api/workspace/list. Selecting
// one updates the AtlasPipeline `ip` state. Falls back to a single-row
// list with the active IP if the workspace endpoint is missing.
function HierarchyList({ activeIp, onSelect }) {
  const [ips, setIps] = React.useState([]);
  React.useEffect(() => {
    let dead = false;
    (async () => {
      try {
        const r = await fetch('/api/workspace/list');
        const j = await r.json().catch(() => ({}));
        if (dead) return;
        const list = Array.isArray(j.ips) ? j.ips
                   : Array.isArray(j.workspaces) ? j.workspaces
                   : [];
        setIps(list.map(x => typeof x === 'string' ? x : (x.ip || x.name || '')).filter(Boolean));
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
window.AtlasPipeline = function AtlasPipeline() {
  const [pipelineState, setPipelineState] = React.useState(null);
  const [fetchError, setFetchError]   = React.useState('');
  const initialIp = (typeof window.ACTIVE_IP === 'string' && window.ACTIVE_IP.trim())
    || (() => { try { return localStorage.getItem('atlasActiveIp') || ''; } catch (_) { return ''; } })()
    || 'arm_m0_min';
  const [ip, setIp] = React.useState(initialIp);
  const [chain, setChain] = React.useState([]);

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

    return () => {
      dead = true;
      if (timer) clearInterval(timer);
      try { if (unsub) unsub(); } catch (_) {}
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

  // Collapse SIGN-OFF when every back-end stage is idle/locked.
  const signoffStages = ['syn', 'sta', 'pnr', 'sta-post'];
  const signoffCollapsed = signoffStages.every(s => {
    const st = (stagesState[s] && stagesState[s].state) || 'idle';
    return st === 'idle' || st === 'locked' || st === 'pending' || st === 'ready';
  });

  return (
    <div className="pipe-screen arch-screen">
      <div className="run-bar pipe-runbar">
        <div className="grp">
          <span className="rb-btn" title="active IP">ip <b>{ip || '—'}</b></span>
          <span className="rb-btn" title="dispatch mode">● pipeline</span>
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
      {!ip && (
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

      <div className="pipe-board">
        <div className="pipe-col-left">
          <HierarchyList activeIp={ip} onSelect={setIp} />
        </div>
        <div className="pipe-col-center">
          <window.DagMap state={pipelineState}
                          onNodeClick={(stageId) => {
                            try {
                              window.dispatchEvent(new CustomEvent('atlas:pipeline-focus-stage', {
                                detail: { stage: stageId },
                              }));
                            } catch (_) {}
                          }} />
          <div className="pipe-stage-grid-wrap">
            {window.PIPELINE_PHASES.map(phase => (
              <PhaseGroup key={phase.id}
                          phase={phase}
                          stagesState={stagesState}
                          ip={ip}
                          onChain={addToChain}
                          defaultCollapsed={phase.id === 'SIGN-OFF' && signoffCollapsed} />
            ))}
          </div>
          <window.DispatchRail ip={ip}
                                chain={chain}
                                onClearChain={() => setChain([])}
                                onRemove={removeFromChain} />
        </div>
        <div className="pipe-col-right">
          {window.ArchitectChat
            ? <window.ArchitectChat view="pipeline" selModule={null} selCluster={null} />
            : <div className="mute" style={{ padding: 12 }}>chat panel unavailable</div>}
        </div>
      </div>
    </div>
  );
};
