// Shared React Flow (@xyflow/react) primitives for the ATLAS graph tabs:
// the VCM spine (workspace-vcm-graph.tsx) and the TODO flow
// (workspace-todo-graph.tsx). Provides a dagre auto-layout helper, a themed
// card node, and a canvas wrapper (pan / zoom / minimap / controls) so both
// graphs share one look and one layout engine instead of hand-rolled SVG.
import type { ReactNode } from 'react';
import dagre from '@dagrejs/dagre';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Handle,
  Position,
  MarkerType,
  type Node,
  type Edge,
  type NodeProps,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

export const GRAPH_NODE_W = 158;
export const GRAPH_NODE_H = 42;

export type FlowCardData = {
  readonly title: string;
  readonly subtitle?: string;
  readonly color: string;
  readonly dim?: boolean;
  readonly dashed?: boolean;
};

const HANDLE_STYLE = { opacity: 0, width: 1, height: 1, border: 'none', background: 'transparent' } as const;

// Themed card node — both graphs feed it {title, subtitle, color, dim, dashed}.
function GraphCardNode({ data, selected }: NodeProps): ReactNode {
  const d = data as unknown as FlowCardData;
  return (
    <div
      title={d.subtitle ? `${d.title}\n${d.subtitle}` : d.title}
      style={{
        width: GRAPH_NODE_W,
        height: GRAPH_NODE_H,
        boxSizing: 'border-box',
        borderRadius: 4,
        padding: '4px 8px 4px 12px',
        overflow: 'hidden',
        fontFamily: 'var(--mono, monospace)',
        background: `color-mix(in oklch, ${d.color} ${selected ? 26 : 12}%, var(--bg-2, #181818))`,
        border: `1px solid ${selected ? d.color : 'var(--line, #333)'}`,
        borderStyle: d.dashed ? 'dashed' : 'solid',
        // status color as a left stripe so state reads at a glance even when zoomed out
        boxShadow: `inset 4px 0 0 ${d.color}`,
        opacity: d.dim ? 0.28 : 1,
        cursor: 'pointer',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        gap: 2,
      }}
    >
      <Handle type="target" position={Position.Left} style={HANDLE_STYLE} />
      <div style={{ fontSize: 10, color: 'var(--fg, #ddd)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
        {d.title}
      </div>
      {d.subtitle ? (
        <div style={{ fontSize: 9, color: d.color, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
          {d.subtitle}
        </div>
      ) : null}
      <Handle type="source" position={Position.Right} style={HANDLE_STYLE} />
    </div>
  );
}

export const graphNodeTypes = { card: GraphCardNode };

export const flowArrow = { type: MarkerType.ArrowClosed, width: 14, height: 14 } as const;

// Dagre layered layout. Returns new nodes with .position set; pure, so callers
// can memoize on the (nodes, edges) identity. Positions are top-left corners.
export function layoutDagre(
  nodes: readonly Node[],
  edges: readonly Edge[],
  opts: {
    readonly direction?: 'LR' | 'TB';
    readonly nodeW?: number;
    readonly nodeH?: number;
    readonly ranksep?: number;
    readonly nodesep?: number;
  } = {},
): Node[] {
  const direction = opts.direction ?? 'LR';
  const nodeW = opts.nodeW ?? GRAPH_NODE_W;
  const nodeH = opts.nodeH ?? GRAPH_NODE_H;
  const g = new dagre.graphlib.Graph();
  g.setDefaultEdgeLabel(() => ({}));
  g.setGraph({ rankdir: direction, ranksep: opts.ranksep ?? 80, nodesep: opts.nodesep ?? 22 });
  for (const n of nodes) g.setNode(n.id, { width: nodeW, height: nodeH });
  for (const e of edges) {
    if (e.source && e.target) g.setEdge(e.source, e.target);
  }
  dagre.layout(g);
  return nodes.map((n) => {
    const p = g.node(n.id);
    if (!p) return n;
    return { ...n, position: { x: p.x - nodeW / 2, y: p.y - nodeH / 2 } };
  });
}

// Compact snake (boustrophedon) grid: a long mostly-linear chain wraps into
// rows that read left→right, right→left, … so the whole thing fits one screen
// instead of a single hair-thin row. Columns auto-pick a wide-ish aspect.
export function layoutGridSnake(
  nodes: readonly Node[],
  opts: { readonly nodeW?: number; readonly nodeH?: number; readonly gapX?: number; readonly gapY?: number; readonly cols?: number; readonly snake?: boolean } = {},
): Node[] {
  const nodeW = opts.nodeW ?? GRAPH_NODE_W;
  const nodeH = opts.nodeH ?? GRAPH_NODE_H;
  const gapX = opts.gapX ?? 36;
  const gapY = opts.gapY ?? 64;
  const snake = opts.snake ?? false; // row-major by default → forward always reads left→right
  const n = nodes.length;
  const cols = opts.cols ?? Math.min(12, Math.max(4, Math.ceil(Math.sqrt(n * 3))));
  return nodes.map((node, i) => {
    const row = Math.floor(i / cols);
    const colInRow = i % cols;
    const col = snake && row % 2 === 1 ? (cols - 1 - colInRow) : colInRow;
    return { ...node, position: { x: col * (nodeW + gapX), y: row * (nodeH + gapY) } };
  });
}

// Themed React Flow canvas. onSelect is called with a node id (or null when the
// pane is clicked) so callers keep their own selection state.
export function GraphCanvas({
  nodes,
  edges,
  onSelect,
  minimap = false,
}: {
  readonly nodes: readonly Node[];
  readonly edges: readonly Edge[];
  readonly onSelect?: (id: string | null) => void;
  readonly minimap?: boolean;
}): ReactNode {
  return (
    <ReactFlow
      nodes={nodes as Node[]}
      edges={edges as Edge[]}
      nodeTypes={graphNodeTypes}
      onNodeClick={(_, n) => onSelect?.(n.id)}
      onPaneClick={() => onSelect?.(null)}
      fitView
      fitViewOptions={{ padding: 0.08, maxZoom: 1.1 }}
      minZoom={0.15}
      maxZoom={1.75}
      nodesDraggable
      nodesConnectable={false}
      elementsSelectable
      proOptions={{ hideAttribution: true }}
    >
      <Background gap={18} color="var(--line, #2a2a2a)" />
      <Controls showInteractive={false} />
      {minimap ? (
        <MiniMap pannable zoomable style={{ background: 'var(--bg-2, #181818)' }} maskColor="color-mix(in oklch, var(--bg, #111) 70%, transparent)" />
      ) : null}
    </ReactFlow>
  );
}

export type { Node as FlowNode, Edge as FlowEdge };
