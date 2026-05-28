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

const PIPE_LAYOUT_VERSION = 'center-wide-compact-chat-v2';
const PIPE_LEFT_DEFAULT = 280;
const PIPE_LEFT_MIN = 200;
const PIPE_LEFT_MAX = 560;
const PIPE_RIGHT_DEFAULT = 340;
const PIPE_RIGHT_MIN = 240;
const PIPE_RIGHT_MAX = 620;

function clampPipeWidth(value, fallback, min, max) {
  const n = Number(value);
  const safe = Number.isFinite(n) && n > 0 ? n : fallback;
  return Math.max(min, Math.min(max, safe));
}

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
// SVG flow canvas matching artifacts/runtime/ATLAS_UI_ENHANCEMENT/Pipeline Image.html: orchestrator
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



// list with the active IP if the workspace endpoint is missing.
function HierarchyList({ activeIp, onSelect }) {
  const [ips, setIps] = React.useState([]);
  React.useEffect(() => {
    let dead = false;
    (async () => {
      try {
        const sessionId = (window.ATLAS_USER && window.ATLAS_USER.username)
          || window.ATLAS_USER_SESSION_ID
          || (window.ACTIVE_SESSION || '').split('/')[0]
          || '';
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
        const ownerScoped = !!(window.ATLAS_USER && window.ATLAS_USER.username);
        if (!dead && !ownerScoped && activeIp) setIps([activeIp]);
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
        const sessionId = (window.ATLAS_USER && window.ATLAS_USER.username)
          || window.ATLAS_USER_SESSION_ID
          || (window.ACTIVE_SESSION || '').split('/')[0]
          || '';
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
        const ownerScoped = !!(window.ATLAS_USER && window.ATLAS_USER.username);
        if (!dead && !ownerScoped && activeIp) setIps([activeIp]);
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

function PipelineOrchestratorChatPanelImpl({ ip, pipelineState }) {
  const [messages, setMessages] = React.useState([]);
  const [since, setSince] = React.useState(0);
  const [draft, setDraft] = React.useState('');
  const [sending, setSending] = React.useState(false);
  const pollingRef = React.useRef(null);
  const bodyRef = React.useRef(null);

  const isActive = !!(pipelineState && pipelineState.orchestrator && pipelineState.orchestrator.active);
  const hasIp = !!(ip && ip !== 'default');

  React.useEffect(() => {
    if (!hasIp) {
      if (pollingRef.current) { clearInterval(pollingRef.current); pollingRef.current = null; }
      return;
    }
    let dead = false;
    let currentSince = since;
    const fetchOnce = async () => {
      try {
        const url = `/api/orchestrator/chat/messages?ip=${encodeURIComponent(ip)}&since=${currentSince}`;
        const r = await fetch(url);
        if (!r.ok) return;
        const j = await r.json();
        if (!dead && j.ok && Array.isArray(j.messages) && j.messages.length > 0) {
          setMessages(prev => {
            const ids = new Set(prev.map(m => m.id));
            const fresh = j.messages.filter(m => !ids.has(m.id));
            return fresh.length ? [...prev, ...fresh] : prev;
          });
          currentSince = j.next_since || currentSince;
          setSince(currentSince);
        }
      } catch (_) {}
    };
    fetchOnce();
    pollingRef.current = setInterval(fetchOnce, 1500);
    return () => { dead = true; clearInterval(pollingRef.current); pollingRef.current = null; };
  }, [ip, isActive]);

  React.useEffect(() => {
    if (bodyRef.current) bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
  }, [messages]);

  const handleSend = async () => {
    const text = draft.trim();
    if (!text || !hasIp || sending) return;
    setSending(true);
    try {
      await fetch('/api/pipeline/orchestrator/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          ip,
          session: window.ACTIVE_SESSION || '',
          session_id: window.ATLAS_DB_SESSION_ID || window.ACTIVE_SESSION || '',
        }),
      });
      setDraft('');
    } catch (_) {} finally {
      setSending(false);
    }
  };

  const handleKeyDown = e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend(); }
  };

  const roleClass = role => {
    if (role === 'assistant') return 'md-bubble md-agent';
    if (role === 'user') return 'md-bubble md-user md-agent';
    if (role === 'tool') return 'md-bubble md-tool';
    return 'md-bubble md-agent';
  };

  return (
    <div className="pipe-orch-chat-shell orch-chat-panel">
      <div className="orch-chat-header">
        <span className="orch-chat-title">ORCHESTRATOR CHAT</span>
        <span className="orch-chat-status" data-active={isActive ? 'yes' : 'no'}>
          {isActive ? 'live' : 'idle'}
        </span>
      </div>
      <div className="orch-chat-body" ref={bodyRef}>
        {messages.length === 0 ? (
          <div className="orch-chat-empty mute">
            {hasIp
              ? `No orchestrator activity yet for ${ip}. Send a chat message or run a workflow to see logs here.`
              : 'Pick an IP to see orchestrator chat.'}
          </div>
        ) : messages.map((m, i) => (
          <div key={m.id || i} className={roleClass(m.role || (m.payload && m.payload.role))}>
            <span className="orch-chat-role">
              {(m.role || (m.payload && m.payload.role) || 'assistant').toUpperCase()}
            </span>
            <span className="orch-chat-content">
              {m.content || (m.payload && (m.payload.content || m.payload.display_name)) || ''}
            </span>
          </div>
        ))}
      </div>
      <div className="orch-chat-input-row">
        <textarea
          className="orch-chat-input"
          placeholder={hasIp ? `Message orchestrator for ${ip}…` : 'Select an IP first'}
          value={draft}
          disabled={sending}
          rows={1}
          onChange={e => setDraft(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <button
          className="orch-chat-send-btn"
          disabled={!draft.trim() || !hasIp || sending}
          onClick={handleSend}
        >
          {sending ? '…' : '▶'}
        </button>
      </div>
    </div>
  );
}

function PipelineOrchestratorChatPanel({ ip, pipelineState }) {
  return <PipelineOrchestratorChatPanelImpl ip={ip} pipelineState={pipelineState} />;
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

window.enhSubText = enhSubText;
const EnhancedFlowCanvas = (...a) => window.EnhancedFlowCanvas(...a);
const WorkerOrchestraBar = (...a) => window.WorkerOrchestraBar(...a);
const OrchestratorTraceStrip = (...a) => window.OrchestratorTraceStrip(...a);

// Phase 27: expose pipeline-helpers.jsx deps + receive helpers back.
window.ENH_LANE_HINTS = ENH_LANE_HINTS;
window.ENH_LANE_NAMES = ENH_LANE_NAMES;
window.ENH_LANE_X = ENH_LANE_X;
window.ENH_NODE_H = ENH_NODE_H;
window.ENH_NODE_W = ENH_NODE_W;
window.ENH_PILL_LABEL = ENH_PILL_LABEL;
window.ENH_ROUTE_EDGES = ENH_ROUTE_EDGES;
window.ENH_ROW_Y = ENH_ROW_Y;
window.ENH_STAGE_LAYOUT = ENH_STAGE_LAYOUT;
window.PIPE_LAYOUT_VERSION = PIPE_LAYOUT_VERSION;
window.PIPE_LEFT_DEFAULT = PIPE_LEFT_DEFAULT;
window.PIPE_LEFT_MAX = PIPE_LEFT_MAX;
window.PIPE_LEFT_MIN = PIPE_LEFT_MIN;
window.PIPE_RIGHT_DEFAULT = PIPE_RIGHT_DEFAULT;
window.PIPE_RIGHT_MAX = PIPE_RIGHT_MAX;
window.PIPE_RIGHT_MIN = PIPE_RIGHT_MIN;
window.EnhancedDetailCards = EnhancedDetailCards;
window.EnhancedFlowCanvas = EnhancedFlowCanvas;
window.HierarchyList = HierarchyList;
window.OrchestratorAskUserBanner = OrchestratorAskUserBanner;
window.OrchestratorTraceStrip = OrchestratorTraceStrip;
window.PendingQABanner = PendingQABanner;
window.PipelineOrchestratorChatPanel = PipelineOrchestratorChatPanel;
window.StageStatusRail = StageStatusRail;
window.WorkerOrchestraBar = WorkerOrchestraBar;
window.clampPipeWidth = clampPipeWidth;
window.pipelineIpFromActiveNamespace = pipelineIpFromActiveNamespace;
const readPipeWidth = (...a) => window.readPipeWidth(...a);
const pipelineInitialIp = (...a) => window.pipelineInitialIp(...a);
