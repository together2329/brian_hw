// Pipeline flow map — React Flow (@xyflow/react) replacement for the hand-rolled
// hardcoded-coordinate SVG canvases (pipeline-trace-canvas.tsx EnhancedFlowCanvas
// + pipeline-flow-stage.tsx PipelineFlowMap). Follows the VCM-graph pattern
// (workspace-vcm-graph.tsx): build {title, subtitle, color, dim, dashed} card
// nodes + dep edges, then layoutDagre(LR) so the 6 phases (SSOT → MODELS → RTL →
// BRANCH → VERIFY·EDA → SIGNOFF) flow left→right automatically.
//
// Why this exists: the SVG canvases positioned every node from a hand-maintained
// coordinate table (ENH_ROW_Y / PIPELINE_NODE_LAYOUT). A missing row entry (e.g.
// ENH_ROW_Y[5] for goal-audit) silently dropped the node to the top-left corner.
// Dagre derives all positions from the DAG, killing that whole bug class.
import { useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import {
  GraphCanvas,
  flowArrow,
  GRAPH_NODE_W,
  GRAPH_NODE_H,
  type FlowNode,
  type FlowEdge,
  type FlowCardData,
} from './workspace-graph-flow';

// The 6 pipeline phases (columns), each listing its stages top→bottom. This is
// the "lane" reading the old SVG canvas had — but as a derived layout, so a
// missing entry can't drop a node to (0,0) the way the hand-kept ENH_ROW_Y
// table did (goal-audit bug). Laying out by phase keeps the whole 16-stage DAG
// to 6 columns / ≤4 rows so it reads at a glance without zooming, instead of
// dagre LR's ~10-rank-wide hair-thin row.
const PIPELINE_PHASES: readonly (readonly string[])[] = [
  ['ssot'],                                                   // SSOT
  ['fl-model', 'cl-model', 'equivalence'],                   // MODELS
  ['rtl'],                                                    // RTL
  ['lint', 'tb', 'syn'],                                      // BRANCH
  ['sim-debug', 'sim', 'sta', 'pnr'],                        // VERIFY · EDA
  ['coverage', 'contract-check', 'goal-audit', 'sta-post'],  // SIGNOFF
];

// Position each node by its phase column + row, vertically centering shorter
// columns. Pure; nodes not in the phase map fall back to a trailing column.
function layoutPhaseColumns(nodes: readonly FlowNode[]): FlowNode[] {
  const pos = new Map<string, { col: number; row: number }>();
  const maxRows = Math.max(...PIPELINE_PHASES.map((p) => p.length));
  PIPELINE_PHASES.forEach((stages, col) => {
    const offset = (maxRows - stages.length) / 2; // center the column
    stages.forEach((id, row) => pos.set(id, { col, row: row + offset }));
  });
  const pitchX = GRAPH_NODE_W + 56;
  const pitchY = GRAPH_NODE_H + 26;
  let trailing = PIPELINE_PHASES.length;
  return nodes.map((n) => {
    const p = pos.get(n.id) ?? { col: trailing++, row: 0 };
    return { ...n, position: { x: p.col * pitchX, y: p.row * pitchY } };
  });
}

// ── Window surface: stage DAG + label/state helpers owned by pipe-width.tsx /
// pipeline-cards.tsx (registered on window before this component renders). ──
interface PipelineFlowWindow {
  PIPELINE_STAGE_DEPS?: Record<string, string[]>;
  PIPELINE_LABEL?: Record<string, string>;
  enhSubText?: (stageId: string, info: unknown) => string;
}
const win = window as unknown as PipelineFlowWindow & Window;

// Canonical 16 pipeline stages, in declaration order (matches pipe-width.tsx
// PIPELINE_STAGE_DEPS). layoutDagre derives x/y from the edges; this list only
// fixes which stages exist and the within-rank ordering hint.
const PIPELINE_STAGES = [
  'ssot', 'fl-model', 'cl-model', 'equivalence', 'rtl', 'lint', 'tb', 'syn',
  'sim', 'coverage', 'sim-debug', 'contract-check', 'goal-audit', 'sta', 'pnr', 'sta-post',
] as const;

// Fallback DAG, identical to win.PIPELINE_STAGE_DEPS (pipe-width.tsx ~line 155).
// Used when the window bridge has not registered yet (e.g. isolated render).
const FALLBACK_DEPS: Record<string, string[]> = {
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
  'contract-check': ['sim-debug'],
  'goal-audit': ['contract-check'],
  'sta': ['syn'],
  'pnr': ['syn'],
  'sta-post': ['pnr'],
};

// State → CSS-var color. Mirrors PIPELINE_STATE_META (pipe-width.tsx) so the
// React Flow map and the legacy badges read identically: passed→ok, failed/
// blocked→err, running→cyan(running accent), stale→warn, locked/ready/idle→mute.
const STATE_COLOR: Record<string, string> = {
  passed: 'var(--ok)',
  ok: 'var(--ok)',
  running: 'var(--cyan)',
  run: 'var(--cyan)',
  failed: 'var(--err)',
  err: 'var(--err)',
  blocked: 'var(--err)',
  stale: 'var(--warn)',
  locked: 'var(--fg-mute)',
  ready: 'var(--fg-mute)',
  idle: 'var(--fg-mute)',
  pending: 'var(--fg-mute)',
};
const stateColor = (state: string): string => STATE_COLOR[state] ?? 'var(--fg-mute)';

// Locked / ready / idle stages render dashed + dimmed (not yet runnable), the
// same visual the card node applies via {dashed, dim}.
const LOCKED_STATES = new Set(['locked', 'ready', 'idle', 'pending']);

type StageInfo = { state?: string; [key: string]: unknown };
type PipelineState = {
  stages?: Record<string, StageInfo>;
  orchestrator?: { enabled?: boolean; active_target?: string; pending_handoffs?: number; [key: string]: unknown };
  [key: string]: unknown;
};

// Per-stage subtitle. Reuses enhSubText (pipeline-cards.tsx) when the window
// bridge is present so live `info.live_tail` / `info.model` / locked_reason text
// matches the legacy cards; falls back to the bare state otherwise.
function stageSubtitle(stageId: string, info: StageInfo): string {
  if (typeof win.enhSubText === 'function') {
    const t = win.enhSubText(stageId, info);
    if (t) return t;
  }
  return info.state || 'idle';
}

// Pure builder (exported for tests): pipelineState → laid-out React Flow card
// nodes (dagre LR) + dep edges. No selection/focus applied yet.
export function buildPipelineElements(state: PipelineState | null | undefined): { nodes: FlowNode[]; edges: FlowEdge[] } {
  const stagesState = state?.stages ?? {};
  const deps = win.PIPELINE_STAGE_DEPS ?? FALLBACK_DEPS;
  const labels = win.PIPELINE_LABEL ?? {};

  const baseNodes: FlowNode[] = PIPELINE_STAGES.map((id) => {
    const info: StageInfo = stagesState[id] ?? {};
    const state = info.state ?? 'idle';
    const locked = LOCKED_STATES.has(state);
    return {
      id,
      type: 'card',
      position: { x: 0, y: 0 },
      data: {
        title: labels[id] || id,
        subtitle: stageSubtitle(id, info),
        color: stateColor(state),
        dim: locked,
        dashed: locked,
      } satisfies FlowCardData as unknown as Record<string, unknown>,
    };
  });

  // Edges = the stage DAG: for each `stage: [deps]`, emit dep → stage.
  const edges: FlowEdge[] = [];
  for (const stage of PIPELINE_STAGES) {
    for (const dep of deps[stage] ?? []) {
      edges.push({
        id: `e-${dep}-${stage}`,
        source: dep,
        target: stage,
        markerEnd: flowArrow,
        style: { stroke: 'var(--fg-mute, #888)' },
      });
    }
  }
  return { nodes: layoutPhaseColumns(baseNodes), edges };
}

export interface PipelineFlowGraphProps {
  pipelineState?: PipelineState | null;
  ip?: string;
  selectedStage?: string;
  onSelectStage?: (stageId: string) => void;
  // ORCHESTRATOR canvas shows the 🎯 on/off header; the Pipeline "IP Flow Map"
  // view (which already has its own flow-control strip) hides it.
  showOrchestratorHead?: boolean;
}

// React Flow pipeline map. Renders the auto-laid-out 16-stage DAG (and, when
// showOrchestratorHead, the orchestrator on/off header). Drop-in for both the
// ORCHESTRATOR canvas and the Pipeline "IP Flow Map" view.
export function PipelineFlowGraph({
  pipelineState,
  selectedStage,
  onSelectStage,
  showOrchestratorHead = true,
}: PipelineFlowGraphProps): ReactNode {
  const [openId, setOpenId] = useState<string | null>(selectedStage ?? null);

  const built = useMemo(() => buildPipelineElements(pipelineState), [pipelineState]);

  const selId = selectedStage ?? openId;
  const displayNodes = useMemo<FlowNode[]>(() => built.nodes.map((rn) => ({
    ...rn,
    selected: selId === rn.id,
  })), [built.nodes, selId]);

  const onSelect = (id: string | null): void => {
    setOpenId(id);
    if (id && onSelectStage) onSelectStage(id);
  };

  const orch = pipelineState?.orchestrator ?? {};
  const orchOn = orch.enabled !== false;
  const target = orch.active_target || 'orchestrator';
  const pending = orch.pending_handoffs != null ? orch.pending_handoffs : 0;

  return (
    <div className="enh-canvas-wrap" style={{ display: 'flex', flexDirection: 'column', minHeight: 320, flex: 1 }}>
      {showOrchestratorHead ? (
        <div
          className="pipe-flow-orch-head"
          style={{
            display: 'flex', gap: 12, alignItems: 'center', padding: '6px 12px',
            borderBottom: '1px solid var(--line)', fontFamily: 'var(--mono)', fontSize: 11,
          }}
        >
          <span style={{ color: orchOn ? 'var(--enh-accent, #f2b632)' : 'var(--fg-mute)' }}>
            🎯 ORCHESTRATOR · {orchOn ? 'ON' : 'OFF'}
          </span>
          <span className="mute" style={{ fontSize: 10 }}>
            TO {target} · pending {pending}
          </span>
        </div>
      ) : null}
      <div style={{ flex: 1, minHeight: 280, background: 'var(--bg-2)' }}>
        <GraphCanvas nodes={displayNodes} edges={built.edges} onSelect={onSelect} minimap />
      </div>
    </div>
  );
}

export default PipelineFlowGraph;
