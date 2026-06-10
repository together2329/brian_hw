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

export const GRAPH_NODE_W = 188;
export const GRAPH_NODE_H = 48;

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
        padding: '5px 9px',
        overflow: 'hidden',
        fontFamily: 'var(--mono, monospace)',
        background: `color-mix(in oklch, ${d.color} ${selected ? 26 : 12}%, var(--bg-2, #181818))`,
        border: `1px solid ${selected ? d.color : 'var(--line, #333)'}`,
        borderStyle: d.dashed ? 'dashed' : 'solid',
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
      fitViewOptions={{ padding: 0.2 }}
      minZoom={0.2}
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
