// pipeline-cards.tsx — TypeScript migration slice of pipeline.tsx.
//
// Extracted from pipeline.tsx (was 1208L) so it drops under 1000. Holds the
// enhanced-flow layout constants + the card/strip presentation cluster:
//   - ENH_* layout constants (lanes / rows / node sizing / route edges / pill
//     + subtext + card-title lookup tables) — owned here, re-bridged to window
//     by pipeline.tsx in the original order.
//   - enhSubText / enhCardTitle / enhCardMeta — per-stage label helpers.
//   - EnhancedDetailCards — running / last-passed / next-ready KPI card grid.
//   - PhaseStrip (+ PHASE_BANDS) — horizontal 6-phase summary strip.
//
// Same permissive house style as the other pipeline-* siblings: cross-file
// window globals are reached through a locally-typed `AtlasGlue` view of window
// so the access type-checks without editing the shared types/atlas-window.d.ts.
import {
  createElement,
  type ReactNode,
  type MouseEvent,
} from 'react';

// ── Local typed view of the legacy window-glue surface this file touches ──
interface PipelineStageInfo {
  state?: string;
  status?: string;
  top?: string;
  secondary?: string;
  locked_reason?: string;
  latest_evidence?: string;
  live_tail?: string;
  iter?: number | string;
  elapsed_seconds?: number;
  model?: string;
  progress?: number;
  [key: string]: unknown;
}
interface PipelineState {
  stages?: Record<string, PipelineStageInfo>;
  orchestrator?: {
    active?: boolean;
    [key: string]: unknown;
  };
  [key: string]: unknown;
}
interface AtlasGlue {
  PIPELINE_STAGES?: string[];
}
const w = window as unknown as AtlasGlue;

// ── PhaseStrip ────────────────────────────────────────────────────────────────
// Horizontal 6-phase summary strip above the flow map.
// Derives done/running/failed counts from stagesState (pipelineState.stages).
interface PhaseBand {
  num: number;
  name: string;
  stages: string[];
}
const PHASE_BANDS: PhaseBand[] = [
  { num: 1, name: 'SSOT',       stages: ['ssot'] },
  { num: 2, name: 'MODELS',     stages: ['fl-model', 'cl-model', 'equivalence'] },
  { num: 3, name: 'RTL',        stages: ['rtl'] },
  { num: 4, name: 'BRANCH',     stages: ['lint', 'tb', 'sim', 'coverage', 'sim-debug'] },
  { num: 5, name: 'VERIFY·EDA', stages: ['syn', 'sta', 'pnr', 'sta-post'] },
  { num: 6, name: 'SIGNOFF',    stages: ['goal-audit'] },
];

export interface PhaseStripProps {
  stagesState?: Record<string, PipelineStageInfo | string> | null;
}
export function PhaseStrip({ stagesState }: PhaseStripProps) {
  const ss = stagesState || {};
  const stateOf = (stageId: string): string => {
    const raw = ss[stageId];
    if (!raw) return 'idle';
    if (typeof raw === 'string') return raw;
    return raw.state || raw.status || 'idle';
  };
  const phases = PHASE_BANDS.map((band) => {
    const known = (w.PIPELINE_STAGES || band.stages).length
      ? band.stages.filter(s => !(w.PIPELINE_STAGES) || (w.PIPELINE_STAGES || []).indexOf(s) >= 0)
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

  const nodes: ReactNode[] = [];
  phases.forEach((ph, i) => {
    nodes.push(
      createElement('div', {
        key: ph.num,
        className: `pipe-flow-phase${ph.phaseClass ? ' ' + ph.phaseClass : ''}`,
      },
        createElement('span', { className: 'pipe-flow-phase-num' }, ph.num),
        createElement('span', { className: 'pipe-flow-phase-body' },
          createElement('span', { className: 'pipe-flow-phase-name' }, ph.name),
          createElement('span', { className: 'pipe-flow-phase-meta' }, ph.meta),
        ),
      )
    );
    if (i < phases.length - 1) {
      nodes.push(
        createElement('span', { key: `arrow-${i}`, className: 'pipe-flow-phase-arrow' }, '›')
      );
    }
  });

  return createElement('div', { className: 'pipe-flow-phases', role: 'navigation' }, ...nodes);
}
// ── /PhaseStrip ───────────────────────────────────────────────────────────────

// ── EnhancedFlowCanvas layout constants ───────────────────────────────────────
// SVG flow canvas matching artifacts/runtime/ATLAS_UI_ENHANCEMENT/Pipeline Image.html: orchestrator
// bus bar on top, 6 vertical lanes (SSOT / MODELS / RTL / BRANCH / VERIFY·EDA /
// SIGNOFF), per-stage node boxes with state pills. Wired to pipelineState.stages
// so it reflects real run progress instead of static mockup data.
export const ENH_LANE_X = { 1: 30, 2: 230, 3: 430, 4: 630, 5: 830, 6: 1030 };
export const ENH_LANE_NAMES = { 1: 'SSOT', 2: 'MODELS', 3: 'RTL', 4: 'BRANCH', 5: 'VERIFY · EDA', 6: 'SIGNOFF' };
export const ENH_LANE_HINTS = { 6: 'post-route' };
export const ENH_ROW_Y = { 1: 140, 2: 220, 3: 300, 4: 380 };
export const ENH_NODE_W = 168;
export const ENH_NODE_H = 58;
export const ENH_STAGE_LAYOUT = {
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
export const ENH_PILL_LABEL = { passed: 'passed', running: 'running', locked: 'locked', ready: 'ready', failed: 'failed', blocked: 'blocked', stale: 'stale' };
// Stage-specific default subtext for each state (canonical Pipeline Image
// rendering). Overridden by real `info.live_tail` / `info.locked_reason` when
// available so mock and live data both look right.
const ENH_SUBTEXT_DEFAULT: Record<string, Record<string, string>> = {
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
export function enhSubText(stageId: string, info?: PipelineStageInfo | null): string {
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
  if (def && info.state && def[info.state]) return def[info.state];
  if (info.locked_reason) return info.locked_reason;
  if (info.state === 'passed') return info.model ? info.model : 'passed';
  if (info.state === 'ready') return 'awaiting handoff';
  if (info.state === 'locked' || info.state === 'blocked') return 'awaiting upstream';
  if (info.state === 'failed') return 'failed — see evidence';
  return '';
}
// Canonical active-route paths from the Pipeline Image mockup, indexed by
// (fromStage, toStage). Same SVG paths as Pipeline Image.html lines 762-806.
export const ENH_ROUTE_EDGES = [
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
const ENH_CARD_GLYPH: Record<string, string> = { running: '▶', passed: '✓', ready: '○', failed: '✗', locked: '·', blocked: '·' };
const ENH_CARD_TITLE_TEXT: Record<string, Record<string, string>> = {
  ssot:         { passed: 'yaml/<ip>.ssot.yaml',                 ready: 'authoring SSOT' },
  'fl-model':   { passed: 'fl/fl_model.json — packets verified', ready: 'awaiting ssot' },
  'cl-model':   { passed: 'cl/cl_model.json — cycle-acc',        ready: 'awaiting ssot' },
  equivalence:  { passed: 'FL ≡ CL across 8 192 stimulus vectors', ready: 'awaiting fl-model + cl-model' },
  rtl:          { passed: 'rtl/axi_dma_top.sv — emitted',        running: 'rtl/axi_dma_top.sv — synthesizing channel arbiter', ready: 'awaiting equivalence' },
  lint:         { passed: 'lint clean - pyslang + verilator',    ready: 'awaiting rtl handoff' },
  tb:           { passed: 'tb/cocotb — emitted',                 ready: 'awaiting rtl' },
  sim:          { passed: 'sim — all tests passed',              running: 'sim driver scoreboarding test vector', ready: 'awaiting tb' },
  syn:          { passed: 'netlist emitted',                     ready: 'awaiting rtl-gen' },
  'sim-debug':  { passed: 'no escapes',                          ready: 'awaiting sim' },
  sta:          { passed: 'timing clean',                        ready: 'awaiting syn · leaf' },
  pnr:          { passed: 'routed',                              ready: 'awaiting syn' },
  coverage:     { passed: 'goals met',                           ready: 'awaiting sim' },
  'sta-post':   { passed: 'post-route timing clean',             ready: 'awaiting pnr' },
};
function enhCardTitle(stageId: string, info?: PipelineStageInfo | null): string {
  if (info && info.live_tail) return info.live_tail;
  const def = ENH_CARD_TITLE_TEXT[stageId];
  return (def && info && info.state && def[info.state]) || (info && info.state) || '';
}
function enhCardMeta(stageId: string, info?: PipelineStageInfo | null): string {
  if (!info) return '';
  const parts: string[] = [];
  if (info.iter) parts.push(`${info.iter} it`);
  if (info.elapsed_seconds) parts.push(`${info.elapsed_seconds}s`);
  if (info.model) parts.push(info.model);
  return parts.join(' · ');
}
export interface EnhancedDetailCardsProps {
  pipelineState?: PipelineState | null;
  ip?: string;
  onSelectStage?: (stageId: string) => void;
  onChain?: (stageId: string) => void;
}
export function EnhancedDetailCards({ pipelineState, ip, onSelectStage, onChain }: EnhancedDetailCardsProps) {
  const stagesState = (pipelineState && pipelineState.stages) || {};
  // Surface every active stage in canonical order
  const ORDER = ['ssot', 'fl-model', 'cl-model', 'equivalence', 'rtl', 'lint', 'tb', 'sim', 'syn', 'sim-debug', 'coverage', 'sta', 'pnr', 'sta-post', 'goal-audit'];
  // 1 currently-running, 1 most-recently-passed, 1 next-ready, max 4.
  const running: Array<{ stageId: string; info: PipelineStageInfo }> = [];
  let lastPassed: { stageId: string; info: PipelineStageInfo } | null = null;
  let nextReady: { stageId: string; info: PipelineStageInfo } | null = null;
  for (const sid of ORDER) {
    const info = stagesState[sid];
    if (!info) continue;
    if (info.state === 'running') running.push({ stageId: sid, info });
    else if (info.state === 'passed') lastPassed = { stageId: sid, info };
    else if (info.state === 'ready' && !nextReady) nextReady = { stageId: sid, info };
  }
  const cards: Array<{ stageId: string; info: PipelineStageInfo }> = [];
  running.forEach(c => cards.push(c));
  if (lastPassed) cards.push(lastPassed);
  if (nextReady) cards.push(nextReady);
  if (!cards.length) return null;

  const renderCard = ({ stageId, info }: { stageId: string; info: PipelineStageInfo }) => {
    const state = info.state;
    const progress = state === 'running' ? Math.min(0.95, Math.max(0.1, info.progress || 0.5)) : null;
    const glyph = (state && ENH_CARD_GLYPH[state]) || '·';
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
           onClick={(ev: MouseEvent<HTMLDivElement>) => {
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
