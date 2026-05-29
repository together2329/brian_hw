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
//
// ── Sub-1000 split (this file was 1065L) ──────────────────────────────
// To keep every file under 1000 lines, the cohesive component groups were
// extracted into sibling modules. The PUBLIC CONTRACT is unchanged: every
// symbol once exported here is re-exported below, and every `window.X = X`
// bridge still runs (each moved into the sibling that now owns the symbol;
// importing the sibling re-runs its bridge as a module side-effect):
//   - pipeline-trace-shared.tsx    — win cast, shared types, ENH_* data
//                                     constants, enhSubText/EnhancedDetailCards/
//                                     HierarchyList/StageCard forward-refs.
//   - pipeline-trace-canvas.tsx    — EnhancedFlowCanvas (+ its bridge).
//   - pipeline-trace-workers.tsx   — WorkerOrchestraBar + OrchestratorTraceStrip
//                                     (+ their bridges).
//   - pipeline-trace-inspector.tsx — FlowInspector + PipelineFlowControl
//                                     (+ their bridges).
// This file retains MiniScoresheet + DispatchRail (+ their bridges).
import { useState } from 'react';
import {
  type MiniScoresheetProps,
  type DispatchRailProps,
} from './pipeline-trace-shared';
import { win } from './pipeline-trace-shared';

// Re-export the extracted public symbols so they stay importable from
// pipeline-trace.tsx. Importing these siblings also re-runs the `win.X = X`
// bridge each declares as a module-init side-effect (Phase 20 / transitional
// bridges), so the SET of window globals assigned is identical to before.
export { EnhancedFlowCanvas } from './pipeline-trace-canvas';
export { WorkerOrchestraBar, OrchestratorTraceStrip } from './pipeline-trace-workers';
export { FlowInspector, PipelineFlowControl } from './pipeline-trace-inspector';

// Re-export shared interfaces/constants that were previously module-local here,
// in case future migrated consumers import them from this entry point.
export type {
  EnhRouteEdge,
  EnhStagePos,
  PipelineFlowDef,
  PipelineVirtualNode,
  StageInfo,
  PipelineState,
  StageCardProps,
  EnhancedFlowCanvasProps,
  WorkerOrchestraBarProps,
  OrchestratorTraceStripProps,
  WorkerSnapshotOpts,
  TraceEvent,
  WorkerInfo,
  WorkerSnapshot,
  ScoresheetDot,
  MiniScoresheetProps,
  DispatchRailProps,
  FlowInspectorProps,
  PipelineFlowControlProps,
} from './pipeline-trace-shared';

// ── EnhancedDetailCards ──────────────────────────────────────────────────────
// Footer detail cards (Pipeline Image phase 2). Shows only ACTIVE stages
// (running / passed / ready) — count varies with state, not forced to 3.
// Cards mirror the mockup at lines 477-548 of Pipeline Image.html: state
// pill, KPI dots, optional progress bar, title, meta line, optional live tail,

// it up (workspace.jsx wires the listener).
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

// ─── Internal: HierarchyList ───────────────────────────────────────
//
// Left column lists every IP discovered via /api/ip/list. Selecting
// one updates the AtlasPipeline `ip` state. Falls back to a single-row


// Phase 20 window exports — pipeline.jsx aliases these back via forward-ref lambdas.
// (EnhancedFlowCanvas / WorkerOrchestraBar / OrchestratorTraceStrip bridges now
// live in their owning siblings, re-run via the re-export imports above.)

// Phase 30: PipelineFlowMap + StageCard extracted to pipeline-flow-stage.jsx.

// ── Transitional bridges for the module-scope window globals ──
// (MiniScoresheet / DispatchRail were `window.X = function...` definitions in
// the .jsx; keep them resolvable for not-yet-migrated .jsx consumers while
// exposing real exports above. FlowInspector / PipelineFlowControl bridges now
// live in pipeline-trace-inspector.tsx, re-run via the re-export import above.)
win.MiniScoresheet = MiniScoresheet;
win.DispatchRail = DispatchRail;
