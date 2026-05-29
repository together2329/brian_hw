// pipeline.tsx — TypeScript migration of pipeline.jsx.
//
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
// Phase 34 refactor: this file dropped under 1000 lines by extracting cohesive
// presentation groups into siblings (definitions move there; this file re-imports
// + re-exports + keeps every window.* bridge in the original order):
//   - pipeline-banners.tsx — PendingQABanner, OrchestratorAskUserBanner
//   - pipeline-cards.tsx   — ENH_* layout constants, enhSubText,
//                            EnhancedDetailCards, PhaseStrip
//   - pipeline-rail.tsx    — HierarchyList, deriveStageReadiness, RunToGreenCard,
//                            StageStatusRail, PipelineOrchestratorChatPanel,
//                            PhaseGroup
//
// What changed vs pipeline.jsx:
//   - Proper ES module: ambient `React.useState` / `React.useEffect` /
//     `React.useRef` / `React.createElement` become imported hooks +
//     `createElement` (automatic JSX runtime, so no `import React` for JSX
//     itself). Every call site is rewritten to the bare imported name.
//   - Cross-file globals OWNED BY OTHER FILES are kept as window.* references
//     (their owners may be unmigrated). They are not yet in
//     types/atlas-window.d.ts, so a locally-typed `w` view of window is used so
//     the access type-checks under strict mode without editing the shared
//     ambient .d.ts. Behaviour is identical.
//   - This file's OWN public globals become real exports plus a transitional
//     window.* bridge at the bottom for not-yet-migrated .jsx consumers; the
//     bridge lines still run in the original order.
import { type ReactNode } from 'react';

import { PendingQABanner, OrchestratorAskUserBanner } from './pipeline-banners';
import {
  PhaseStrip,
  EnhancedDetailCards,
  enhSubText,
  ENH_LANE_HINTS,
  ENH_LANE_NAMES,
  ENH_LANE_X,
  ENH_NODE_H,
  ENH_NODE_W,
  ENH_PILL_LABEL,
  ENH_ROUTE_EDGES,
  ENH_ROW_Y,
  ENH_STAGE_LAYOUT,
} from './pipeline-cards';
import {
  HierarchyList,
  deriveStageReadiness,
  RunToGreenCard,
  StageStatusRail,
  PipelineOrchestratorChatPanel,
  PhaseGroup,
} from './pipeline-rail';

// ── Local typed view of the legacy window-glue surface this file touches ──
// (cross-file deps owned by other not-yet-migrated .jsx files, plus this file's
// own globals re-read/re-bridged below). This is a behavior-neutral cast
// target: it does not change runtime, it only lets the undeclared globals
// type-check under strict mode without editing the shared
// types/atlas-window.d.ts (out of scope for this migration).
type AnyComponent = (...a: unknown[]) => ReactNode;
interface AtlasGlue {
  // cross-file component globals consumed via forward-ref lambdas
  EnhancedFlowCanvas: AnyComponent;
  WorkerOrchestraBar: AnyComponent;
  OrchestratorTraceStrip: AnyComponent;
  // session / context globals (owned by other files)
  ACTIVE_SESSION?: string;
  // this file's own exports (bridged at bottom)
  enhSubText: typeof enhSubText;
  ENH_LANE_HINTS: unknown;
  ENH_LANE_NAMES: unknown;
  ENH_LANE_X: unknown;
  ENH_NODE_H: unknown;
  ENH_NODE_W: unknown;
  ENH_PILL_LABEL: unknown;
  ENH_ROUTE_EDGES: unknown;
  ENH_ROW_Y: unknown;
  ENH_STAGE_LAYOUT: unknown;
  PIPE_LAYOUT_VERSION: string;
  PIPE_LEFT_DEFAULT: number;
  PIPE_LEFT_MAX: number;
  PIPE_LEFT_MIN: number;
  PIPE_RIGHT_DEFAULT: number;
  PIPE_RIGHT_MAX: number;
  PIPE_RIGHT_MIN: number;
  EnhancedDetailCards: AnyComponent;
  HierarchyList: AnyComponent;
  OrchestratorAskUserBanner: AnyComponent;
  PendingQABanner: AnyComponent;
  PipelineOrchestratorChatPanel: AnyComponent;
  StageStatusRail: AnyComponent;
  clampPipeWidth: (value: number, fallback: number, min: number, max: number) => number;
  pipelineIpFromActiveNamespace: () => string;
}
const w = window as unknown as AtlasGlue;

const PIPE_LAYOUT_VERSION = 'center-wide-compact-chat-v2';
const PIPE_LEFT_DEFAULT = 280;
const PIPE_LEFT_MIN = 200;
const PIPE_LEFT_MAX = 560;
const PIPE_RIGHT_DEFAULT = 340;
const PIPE_RIGHT_MIN = 240;
const PIPE_RIGHT_MAX = 620;

function clampPipeWidth(value: number, fallback: number, min: number, max: number): number {
  const n = Number(value);
  const safe = Number.isFinite(n) && n > 0 ? n : fallback;
  return Math.max(min, Math.min(max, safe));
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
function pipelineIpFromActiveNamespace(): string {
  const parts = String(w.ACTIVE_SESSION || '').split('/').filter(Boolean);
  if (parts.length >= 3) return parts[parts.length - 2] || '';
  return '';
}

w.enhSubText = enhSubText;
const EnhancedFlowCanvas = (...a: unknown[]) => w.EnhancedFlowCanvas(...a);
const WorkerOrchestraBar = (...a: unknown[]) => w.WorkerOrchestraBar(...a);
const OrchestratorTraceStrip = (...a: unknown[]) => w.OrchestratorTraceStrip(...a);

// Phase 27: expose pipeline-helpers.jsx deps + receive helpers back.
w.ENH_LANE_HINTS = ENH_LANE_HINTS;
w.ENH_LANE_NAMES = ENH_LANE_NAMES;
w.ENH_LANE_X = ENH_LANE_X;
w.ENH_NODE_H = ENH_NODE_H;
w.ENH_NODE_W = ENH_NODE_W;
w.ENH_PILL_LABEL = ENH_PILL_LABEL;
w.ENH_ROUTE_EDGES = ENH_ROUTE_EDGES;
w.ENH_ROW_Y = ENH_ROW_Y;
w.ENH_STAGE_LAYOUT = ENH_STAGE_LAYOUT;
w.PIPE_LAYOUT_VERSION = PIPE_LAYOUT_VERSION;
w.PIPE_LEFT_DEFAULT = PIPE_LEFT_DEFAULT;
w.PIPE_LEFT_MAX = PIPE_LEFT_MAX;
w.PIPE_LEFT_MIN = PIPE_LEFT_MIN;
w.PIPE_RIGHT_DEFAULT = PIPE_RIGHT_DEFAULT;
w.PIPE_RIGHT_MAX = PIPE_RIGHT_MAX;
w.PIPE_RIGHT_MIN = PIPE_RIGHT_MIN;
w.EnhancedDetailCards = EnhancedDetailCards as unknown as AnyComponent;
w.EnhancedFlowCanvas = EnhancedFlowCanvas as unknown as AnyComponent;
w.HierarchyList = HierarchyList as unknown as AnyComponent;
w.OrchestratorAskUserBanner = OrchestratorAskUserBanner as unknown as AnyComponent;
w.OrchestratorTraceStrip = OrchestratorTraceStrip as unknown as AnyComponent;
w.PendingQABanner = PendingQABanner as unknown as AnyComponent;
w.PipelineOrchestratorChatPanel = PipelineOrchestratorChatPanel as unknown as AnyComponent;
w.StageStatusRail = StageStatusRail as unknown as AnyComponent;
w.WorkerOrchestraBar = WorkerOrchestraBar as unknown as AnyComponent;
w.clampPipeWidth = clampPipeWidth;
w.pipelineIpFromActiveNamespace = pipelineIpFromActiveNamespace;

// ── Typed exports of this file's own public surface (real ES exports so
// migrated consumers can import directly; window.* bridges above keep the
// not-yet-migrated .jsx consumers resolving). ──
export {
  clampPipeWidth,
  enhSubText,
  PendingQABanner,
  OrchestratorAskUserBanner,
  PhaseStrip,
  EnhancedDetailCards,
  HierarchyList,
  deriveStageReadiness,
  RunToGreenCard,
  StageStatusRail,
  PipelineOrchestratorChatPanel,
  PhaseGroup,
  pipelineIpFromActiveNamespace,
};
