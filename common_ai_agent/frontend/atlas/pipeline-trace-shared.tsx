// pipeline-trace-shared.tsx — shared scaffolding for the pipeline-trace.tsx
// family (Phase: sub-1000 split of pipeline-trace.tsx, originally 1065L).
//
// This module owns the cross-cutting pieces every pipeline-trace sibling needs:
//   - the narrow `win` cast + PipelineTraceWindow surface,
//   - the shared data-shape interfaces,
//   - the window-sourced data constants (ENH_*),
//   - the forward-ref lambdas (enhSubText / EnhancedDetailCards / HierarchyList /
//     StageCard) that route call-sites through window at render time.
//
// House style matches pipeline-helpers.tsx / the original pipeline-trace.tsx:
// cross-file globals owned by not-yet-migrated .jsx are reached through a
// locally-typed view of `window`; window-sourced values are typed permissively
// (the original used a mix of `as` casts + `any`-ish lambdas) on purpose.
import { type ReactNode } from 'react';

// ── Narrow cast for undeclared cross-file + own globals ───────────────
// types/atlas-window.d.ts does not (yet) declare the pipeline surface, so
// reference it through a locally-typed view of window. This preserves the
// exact runtime reads/writes without spraying `any` across call sites.
export interface PipelineTraceWindow {
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

  // This file's OWN public globals (bridged at the bottom of each sibling).
  EnhancedFlowCanvas?: (props: EnhancedFlowCanvasProps) => ReactNode;
  WorkerOrchestraBar?: (props: WorkerOrchestraBarProps) => ReactNode;
  OrchestratorTraceStrip?: (props: OrchestratorTraceStripProps) => ReactNode;
  MiniScoresheet?: (props: MiniScoresheetProps) => ReactNode;
  DispatchRail?: (props: DispatchRailProps) => ReactNode;
  FlowInspector?: (props: FlowInspectorProps) => ReactNode;
  PipelineFlowControl?: (props: PipelineFlowControlProps) => ReactNode;
}

export const win = window as unknown as PipelineTraceWindow & Window;

// ── Shared data shapes ────────────────────────────────────────────────
export interface EnhRouteEdge {
  id: string;
  from: string;
  to: string;
  d: string;
  bidir?: boolean;
  reverseD?: string;
}

export interface EnhStagePos {
  lane: number;
  row: number;
}

export interface PipelineFlowDef {
  id: string;
  name: string;
  summary?: string;
  stages?: string[];
}

export interface PipelineVirtualNode {
  label: string;
  sub: string;
  state?: string;
}

export interface StageInfo {
  state?: string;
  top?: string;
  secondary?: string;
  locked_reason?: string;
  [key: string]: unknown;
}

export interface PipelineState {
  stages?: Record<string, StageInfo>;
  orchestrator?: {
    enabled?: boolean;
    active_target?: string;
    pending_handoffs?: number;
    [key: string]: unknown;
  };
  [key: string]: unknown;
}

export interface StageCardProps {
  stageId: string;
  info: StageInfo;
  ip?: string;
  onChain?: (stageId: string) => void;
}

// ── Worker / trace data shapes (shared by the workers + canvas siblings) ──
export interface WorkerSnapshotOpts {
  ip?: string;
  activeOnly?: boolean;
  [key: string]: unknown;
}

export interface TraceEvent {
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

export interface WorkerInfo {
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

export interface WorkerSnapshot {
  orchestrator?: {
    enabled?: boolean;
    active_target?: string;
    [key: string]: unknown;
  };
  workers?: WorkerInfo[];
  [key: string]: unknown;
}

// ── Component prop shapes (declared centrally so PipelineTraceWindow can
// reference them and each sibling can import the ones it owns) ──────────
export interface EnhancedFlowCanvasProps {
  pipelineState?: PipelineState;
  ip?: string;
  onSelectStage?: (stageId: string) => void;
  selectedStage?: string;
  selectedFlowId?: string;
  onChain?: (stageId: string) => void;
}

export interface WorkerOrchestraBarProps {
  ip?: string;
  onSelectTarget?: (workflow: string) => void;
  currentTarget?: string;
}

export interface OrchestratorTraceStripProps {
  ip?: string;
}

export interface ScoresheetDot {
  state?: string;
  label?: string;
  evidence_path?: string;
}

export interface MiniScoresheetProps {
  scoresheet?: Array<ScoresheetDot | string>;
  evidencePaths?: string[];
}

export interface DispatchRailProps {
  ip?: string;
  chain: string[];
  onClearChain?: () => void;
  onRemove?: (stage: string) => void;
}

export interface FlowInspectorProps {
  ip?: string;
  state?: PipelineState;
  selectedFlowId?: string;
  onSelectFlow?: (id: string) => void;
  selectedStage?: string;
  onSelectStage?: (id: string) => void;
  onChain?: (stageId: string) => void;
}

export interface PipelineFlowControlProps {
  ip?: string;
  state?: PipelineState;
  selectedFlowId?: string;
  onSelectFlow?: (id: string) => void;
  selectedStage?: string;
  onSelectStage?: (id: string) => void;
}

// Data constants (accessed as `ENH_LANE_NAMES[k]` — must be the real object,
// not a lambda; pipeline.jsx exposed them before this module runs):
export const ENH_LANE_HINTS = win.ENH_LANE_HINTS as Record<number, string>;
export const ENH_LANE_NAMES = win.ENH_LANE_NAMES as Record<number, string>;
export const ENH_LANE_X = win.ENH_LANE_X as Record<number, number>;
export const ENH_NODE_H = win.ENH_NODE_H as number;
export const ENH_NODE_W = win.ENH_NODE_W as number;
export const ENH_PILL_LABEL = win.ENH_PILL_LABEL as Record<string, string>;
export const ENH_ROUTE_EDGES = win.ENH_ROUTE_EDGES as EnhRouteEdge[];
export const ENH_ROW_Y = win.ENH_ROW_Y as Record<number, number>;
export const ENH_STAGE_LAYOUT = win.ENH_STAGE_LAYOUT as Record<string, EnhStagePos>;

// Function / component deps (lambda forward-ref so call-site lookups go through window):
export const enhSubText = (...a: Parameters<NonNullable<PipelineTraceWindow['enhSubText']>>) => win.enhSubText!(...a);
export const EnhancedDetailCards = (...a: unknown[]) => win.EnhancedDetailCards!(...a);
export const HierarchyList = (...a: unknown[]) => win.HierarchyList!(...a);

// StageCard is owned by pipeline-flow-stage.jsx. The original rendered it as
// `<window.StageCard ...>` (resolved at render time); a forward-ref lambda
// preserves that exact lazy lookup while giving JSX a non-optional component.
export const StageCard = (props: StageCardProps) => win.StageCard!(props);
