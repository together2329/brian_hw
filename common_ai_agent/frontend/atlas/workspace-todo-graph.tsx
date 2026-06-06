import type { ReactNode } from 'react';
import { atlasStatusMeta, normalizeAtlasStatus } from './workspace-report-status';
import {
  todoCommandText,
  todoDeps,
  todoDetail,
  todoId,
  todoState,
  todoTitle,
  type TodoRecord,
} from './workspace-todo-model';

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

export const TodoGraph = ({ todos, openId, setOpenId }: TodoGraphProps): ReactNode => {
  if (!todos.length) {
    return (
      <div style={{ color: 'var(--fg-mute)', fontStyle: 'italic', padding: 12 }}>
        No todos for this session yet.
      </div>
    );
  }

  const nodes = todos.map((todo, index): GraphNode => ({
    id: todoId(todo, index),
    index,
    todo,
  }));
  const nodeById = new Map(nodes.map(node => [node.id, node]));
  const nodeIdForTask = (target: unknown): string => {
    const taskNumber = Number(target);
    if (!Number.isInteger(taskNumber) || taskNumber < 1 || taskNumber > nodes.length) return '';
    return nodes[taskNumber - 1]?.id ?? '';
  };
  const edges = nodes.flatMap((node): readonly GraphEdge[] => {
    const next = nodes[node.index + 1]?.id ?? '';
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

  const NODE_W = 150;
  const NODE_H = 48;
  const gapX = 46;
  const padX = 14;
  const padY = 28;
  const totalW = padX * 2 + nodes.length * NODE_W + Math.max(0, nodes.length - 1) * gapX;
  const totalH = 150;
  const pos: Record<string, { readonly x: number; readonly y: number }> = {};

  nodes.forEach((node, index) => {
    pos[node.id] = {
      x: padX + index * (NODE_W + gapX),
      y: padY + 42,
    };
  });

  const stateCfg = (state: string) => {
    const meta = atlasStatusMeta(state);
    const normalized = normalizeAtlasStatus(state);
    const highlighted = ['active', 'in_progress', 'running', 'done', 'completed', 'approved', 'rejected', 'error', 'blocked'].includes(normalized);
    return {
      fill: highlighted ? `color-mix(in oklch, ${meta.color} 14%, transparent)` : 'transparent',
      stroke: highlighted ? meta.color : 'var(--line)',
      glyph: meta.glyph,
      color: meta.color,
    };
  };

  return (
    <div style={{ padding: 12 }}>
      <div className="mute" style={{ fontSize: 10, marginBottom: 8, fontFamily: 'var(--mono)' }}>
        ── TODO FLOW · command gates, reject loops, dependencies · click a node · ↔ scroll
      </div>
      <div style={{ overflowX: 'auto', overflowY: 'hidden', border: '1px solid var(--line)', borderRadius: 2, background: 'var(--bg-2)' }}>
        <svg width={totalW} height={totalH} style={{ display: 'block' }}>
          <defs>
            <marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
              <path d="M0,0 L10,5 L0,10 z" fill="var(--fg-mute)" />
            </marker>
          </defs>
          {edges.map((edge, edgeIndex) => {
            const a = pos[edge.from];
            const b = pos[edge.to];
            if (!a || !b) return null;
            const reverse = b.x < a.x;
            const x1 = reverse ? a.x : a.x + NODE_W;
            const y1 = a.y + NODE_H / 2;
            const x2 = reverse ? b.x + NODE_W : b.x;
            const y2 = b.y + NODE_H / 2;
            const mx = (x1 + x2) / 2;
            const lift = edge.kind === 'reject' ? -34 : edge.kind === 'condition' ? -22 : 0;
            const color = edge.kind === 'reject' ? 'var(--err)' : edge.kind === 'success' ? 'var(--ok)' : 'var(--line)';
            return (
              <g key={`${edge.from}->${edge.to}-${edge.kind}-${edgeIndex}`}>
                <path
                  d={`M${x1},${y1} C${mx},${y1 + lift} ${mx},${y2 + lift} ${x2},${y2}`}
                  fill="none"
                  stroke={color}
                  strokeWidth="1.25"
                  markerEnd="url(#arr)"
                />
                <text x={mx} y={Math.min(y1, y2) + lift - 4} fontSize="9" textAnchor="middle" fill={color} fontFamily="var(--mono)" fontWeight="700">
                  {edge.label}
                </text>
              </g>
            );
          })}
          {nodes.map(node => {
            const p = pos[node.id];
            if (!p) return null;
            const cfg = stateCfg(todoState(node.todo));
            const selected = openId === node.id;
            const title = todoTitle(node.todo);
            return (
              <g
                key={node.id}
                onClick={() => setOpenId(selected ? null : node.id)}
                style={{ cursor: 'pointer' }}
              >
                <rect
                  x={p.x}
                  y={p.y}
                  width={NODE_W}
                  height={NODE_H}
                  rx="2"
                  fill={cfg.fill}
                  stroke={selected ? 'var(--fg)' : cfg.stroke}
                  strokeWidth={selected ? 2 : 1}
                />
                <text x={p.x + 6} y={p.y + 12} fontSize="8" fill="var(--fg-mute)" fontFamily="var(--mono)" letterSpacing="0.04em">
                  #{node.index + 1} {node.todo.section}
                </text>
                <text x={p.x + NODE_W - 6} y={p.y + 12} fontSize="9" textAnchor="end" fill={cfg.color} fontFamily="var(--mono)" fontWeight="700">
                  {cfg.glyph}
                </text>
                {todoCommandText(node.todo) ? (
                  <text x={p.x + NODE_W - 6} y={p.y + NODE_H - 8} fontSize="8" textAnchor="end" fill="var(--accent)" fontFamily="var(--mono)" fontWeight="700">
                    CMD
                  </text>
                ) : null}
                <text x={p.x + 6} y={p.y + 28} fontSize="10" fill="var(--fg)" fontFamily="var(--mono)">
                  {title.length > 22 ? `${title.slice(0, 21)}…` : title}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
      {openId ? (
        <div className="fade-in" style={{
          marginTop: 12, padding: '8px 10px', borderLeft: '2px solid var(--accent)',
          background: 'var(--bg-2)', fontFamily: 'var(--mono)', fontSize: 'var(--ui-control-font-size)', lineHeight: 1.5,
        }}>
          {(() => {
            const selected = nodes.find(node => node.id === openId);
            if (!selected) return null;
            const cfg = stateCfg(todoState(selected.todo));
            const deps = todoDeps(selected.todo);
            return (
              <>
                <div>
                  <span style={{ color: cfg.color, fontWeight: 700 }}>{cfg.glyph}</span>{' '}
                  <span className="mute">{selected.todo.section}</span>{' '}
                  <span style={{ color: 'var(--fg)' }}>{todoTitle(selected.todo)}</span>
                </div>
                <div className="mute" style={{ marginTop: 4 }}>{todoDetail(selected.todo)}</div>
                {todoCommandText(selected.todo) ? (
                  <div style={{ marginTop: 4, color: 'var(--accent)' }}>
                    command: {todoCommandText(selected.todo)}
                  </div>
                ) : null}
                <div style={{ marginTop: 4, fontSize: 10 }}>
                  <span className="mute">deps:</span>{' '}
                  {deps.length ? deps.map(dep => <span key={dep} className="acc">§{dep} </span>) : <span className="mute">(none)</span>}
                </div>
              </>
            );
          })()}
        </div>
      ) : null}
    </div>
  );
};
