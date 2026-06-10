// TODO flow — interactive React Flow graph of a session's todo chain:
// command gates, success/reject loops, conditions and dependencies.
// Same props/exports as before ({todos, openId, setOpenId}); only the renderer
// moved from hand-rolled SVG to React Flow (dagre LR layout, pan/zoom/minimap).
import { useMemo } from 'react';
import type { ReactNode } from 'react';
import { atlasStatusMeta } from './workspace-report-status';
import {
  todoCommandText,
  todoDeps,
  todoDetail,
  todoId,
  todoState,
  todoTitle,
  type TodoRecord,
} from './workspace-todo-model';
import {
  GraphCanvas,
  layoutGridSnake,
  flowArrow,
  type FlowNode,
  type FlowEdge,
  type FlowCardData,
} from './workspace-graph-flow';

type TodoGraphProps = {
  readonly todos: readonly TodoRecord[];
  readonly openId: string | null;
  readonly setOpenId: (id: string | null) => void;
};

type GraphNode = {
  readonly id: string;
  readonly index: number;
  readonly todo: TodoRecord;
};

type GraphEdge = {
  readonly from: string;
  readonly to: string;
  readonly label: string;
  readonly kind: 'next' | 'success' | 'reject' | 'condition' | 'dep';
};

const EDGE_COLOR: Record<GraphEdge['kind'], string> = {
  next: 'var(--line, #555)',
  success: 'var(--ok, #4caf78)',
  reject: 'var(--err, #e05a5a)',
  condition: 'var(--warn, #d9a13b)',
  dep: 'var(--accent, #6aa0ff)',
};

const stateConfig = (state: string): { readonly color: string; readonly glyph: string } => {
  const meta = atlasStatusMeta(state);
  return { color: meta.color, glyph: meta.glyph };
};

// Pure builder (exported for tests): todos → laid-out React Flow nodes + edges.
export function buildTodoFlow(todos: readonly TodoRecord[]): { nodes: FlowNode[]; edges: FlowEdge[]; nodeIds: string[] } {
  const items: GraphNode[] = todos.map((todo, index) => ({ id: todoId(todo, index), index, todo }));
  const nodeById = new Map(items.map((node) => [node.id, node]));
  const nodeIdForTask = (target: unknown): string => {
    const taskNumber = Number(target);
    if (!Number.isInteger(taskNumber) || taskNumber < 1 || taskNumber > items.length) return '';
    return items[taskNumber - 1]?.id ?? '';
  };
  const graphEdges: GraphEdge[] = items.flatMap((node): readonly GraphEdge[] => {
    const next = items[node.index + 1]?.id ?? '';
    const onSuccess = nodeIdForTask(node.todo.onSuccess);
    const onReject = nodeIdForTask(node.todo.onReject);
    const conditionEdges = Array.isArray(node.todo.onCondition)
      ? node.todo.onCondition.flatMap((condition): readonly GraphEdge[] => {
        if (!condition || typeof condition !== 'object') return [];
        const target = nodeIdForTask((condition as { readonly goto?: unknown }).goto);
        return target ? [{ from: node.id, to: target, label: 'cond', kind: 'condition' }] : [];
      })
      : [];
    const depEdges = todoDeps(node.todo).flatMap((dep): readonly GraphEdge[] => (
      nodeById.has(dep) ? [{ from: dep, to: node.id, label: 'dep', kind: 'dep' }] : []
    ));
    return [
      ...(next ? [{ from: node.id, to: onSuccess || next, label: onSuccess ? 'success' : 'next', kind: onSuccess ? 'success' : 'next' } satisfies GraphEdge] : []),
      ...(onReject ? [{ from: node.id, to: onReject, label: 'reject', kind: 'reject' } satisfies GraphEdge] : []),
      ...conditionEdges,
      ...depEdges,
    ];
  });

  const rfNodes: FlowNode[] = items.map((node) => {
    const cfg = stateConfig(todoState(node.todo));
    const title = todoTitle(node.todo);
    const cmd = todoCommandText(node.todo) ? ' · CMD' : '';
    return {
      id: node.id,
      type: 'card',
      position: { x: 0, y: 0 },
      data: {
        title: `#${node.index + 1} ${title}`,
        subtitle: `${node.todo.section ?? ''} ${cfg.glyph}${cmd}`.trim(),
        color: cfg.color,
      } satisfies FlowCardData as unknown as Record<string, unknown>,
    };
  });

  const rfEdges: FlowEdge[] = graphEdges.map((e, i) => ({
    id: `${e.kind}-${e.from}-${e.to}-${i}`,
    source: e.from,
    target: e.to,
    label: e.label,
    type: 'smoothstep',
    markerEnd: flowArrow,
    animated: e.kind === 'reject',
    style: { stroke: EDGE_COLOR[e.kind], strokeWidth: 1.25 },
    labelStyle: { fill: EDGE_COLOR[e.kind], fontSize: 8, fontFamily: 'var(--mono, monospace)', fontWeight: 700 },
    labelBgStyle: { fill: 'var(--bg-2, #181818)' },
  }));

  // A todo chain is mostly linear → a dagre LR layout becomes one hair-thin
  // row. Wrap it row-major (every row reads left→right, so forward arrows are
  // consistently rightward) into a compact grid that fits a single screen.
  return { nodes: layoutGridSnake(rfNodes), edges: rfEdges, nodeIds: items.map((n) => n.id) };
}

export const TodoGraph = ({ todos, openId, setOpenId }: TodoGraphProps): ReactNode => {
  const built = useMemo(() => buildTodoFlow(todos), [todos]);
  const selected = useMemo(() => todos.find((todo, index) => todoId(todo, index) === openId) ?? null, [todos, openId]);
  const selectedIndex = useMemo(() => todos.findIndex((todo, index) => todoId(todo, index) === openId), [todos, openId]);

  const displayNodes = useMemo<FlowNode[]>(
    () => built.nodes.map((n) => ({ ...n, selected: n.id === openId })),
    [built.nodes, openId],
  );

  if (!todos.length) {
    return (
      <div style={{ color: 'var(--fg-mute)', fontStyle: 'italic', padding: 12 }}>
        No todos for this session yet.
      </div>
    );
  }

  const cfg = selected ? stateConfig(todoState(selected)) : null;
  const deps = selected ? todoDeps(selected) : [];

  return (
    <div style={{ padding: 12 }}>
      <div className="mute" style={{ fontSize: 10, marginBottom: 8, fontFamily: 'var(--mono)' }}>
        ── TODO FLOW · command gates, reject loops, dependencies · click a node · drag / scroll to pan
      </div>
      <div style={{ height: 440, border: '1px solid var(--line)', borderRadius: 2, background: 'var(--bg-2)' }}>
        <GraphCanvas nodes={displayNodes} edges={built.edges} onSelect={setOpenId} minimap />
      </div>
      {selected && cfg ? (
        <div className="fade-in" style={{
          marginTop: 12, padding: '8px 10px', borderLeft: '2px solid var(--accent)',
          background: 'var(--bg-2)', fontFamily: 'var(--mono)', fontSize: 'var(--ui-control-font-size)', lineHeight: 1.5,
        }}>
          <div>
            <span style={{ color: cfg.color, fontWeight: 700 }}>{cfg.glyph}</span>{' '}
            <span className="mute">#{selectedIndex + 1} {selected.section}</span>{' '}
            <span style={{ color: 'var(--fg)' }}>{todoTitle(selected)}</span>
          </div>
          <div className="mute" style={{ marginTop: 4 }}>{todoDetail(selected)}</div>
          {todoCommandText(selected) ? (
            <div style={{ marginTop: 4, color: 'var(--accent)' }}>
              command: {todoCommandText(selected)}
            </div>
          ) : null}
          <div style={{ marginTop: 4, fontSize: 10 }}>
            <span className="mute">deps:</span>{' '}
            {deps.length ? deps.map((dep) => <span key={dep} className="acc">§{dep} </span>) : <span className="mute">(none)</span>}
          </div>
        </div>
      ) : null}
    </div>
  );
};

export default TodoGraph;
