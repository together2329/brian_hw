import type { ReactNode } from 'react';
import { atlasStatusMeta, normalizeAtlasStatus } from './workspace-report-status';
import { todoDeps, todoDetail, todoId, todoState, todoTitle, type TodoRecord } from './workspace-todo-model';

type TodoGraphProps = {
  readonly todos: readonly TodoRecord[];
  readonly openId: unknown;
  readonly setOpenId: (id: unknown) => void;
};

type GraphNode = {
  readonly id: string;
  readonly deps: readonly string[];
  readonly todo: TodoRecord;
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
    deps: todoDeps(todo),
    todo,
  }));
  const levelOf: Record<string, number> = {};
  nodes.forEach(node => {
    levelOf[node.id] = node.deps.reduce((level, dep) => Math.max(level, (levelOf[dep] ?? 0) + 1), 0);
  });
  const levels: Record<number, readonly GraphNode[]> = {};
  nodes.forEach(node => {
    const level = levelOf[node.id] ?? 0;
    levels[level] = [...(levels[level] ?? []), node];
  });
  const levelKeys = Object.keys(levels).map(Number).sort((a, b) => a - b);

  const NODE_W = 80;
  const NODE_H = 32;
  const gapY = 10;
  const gapX = 22;
  const padX = 10;
  const padY = 10;
  const colW = NODE_W + gapX;
  const totalW = padX * 2 + colW * levelKeys.length - gapX;
  const maxRow = Math.max(1, ...levelKeys.map(key => levels[key]?.length ?? 0));
  const totalH = padY * 2 + maxRow * (NODE_H + gapY) - gapY;
  const pos: Record<string, { readonly x: number; readonly y: number }> = {};

  levelKeys.forEach((level, columnIndex) => {
    const col = levels[level] ?? [];
    const colH = col.length * (NODE_H + gapY) - gapY;
    const yStart = padY + (totalH - padY * 2 - colH) / 2;
    col.forEach((node, rowIndex) => {
      pos[node.id] = {
        x: padX + columnIndex * colW,
        y: yStart + rowIndex * (NODE_H + gapY),
      };
    });
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
        ── DAG · {levelKeys.length} levels · click a node · ↔ scroll
      </div>
      <div style={{ overflowX: 'auto', overflowY: 'hidden', border: '1px solid var(--line)', borderRadius: 2, background: 'var(--bg-2)' }}>
        <svg width={totalW} height={totalH} style={{ display: 'block' }}>
          <defs>
            <marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
              <path d="M0,0 L10,5 L0,10 z" fill="var(--fg-mute)" />
            </marker>
          </defs>
          {nodes.flatMap(node => node.deps.map(dep => {
            const a = pos[dep];
            const b = pos[node.id];
            if (!a || !b) return null;
            const x1 = a.x + NODE_W;
            const y1 = a.y + NODE_H / 2;
            const x2 = b.x;
            const y2 = b.y + NODE_H / 2;
            const mx = (x1 + x2) / 2;
            return (
              <path
                key={`${dep}->${node.id}`}
                d={`M${x1},${y1} C${mx},${y1} ${mx},${y2} ${x2},${y2}`}
                fill="none"
                stroke="var(--line)"
                strokeWidth="1"
                markerEnd="url(#arr)"
              />
            );
          }))}
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
                  {node.todo.section}
                </text>
                <text x={p.x + NODE_W - 6} y={p.y + 12} fontSize="9" textAnchor="end" fill={cfg.color} fontFamily="var(--mono)" fontWeight="700">
                  {cfg.glyph}
                </text>
                <text x={p.x + 6} y={p.y + 24} fontSize="9" fill="var(--fg)" fontFamily="var(--mono)">
                  {title.length > 11 ? `${title.slice(0, 10)}…` : title}
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
            return (
              <>
                <div>
                  <span style={{ color: cfg.color, fontWeight: 700 }}>{cfg.glyph}</span>{' '}
                  <span className="mute">{selected.todo.section}</span>{' '}
                  <span style={{ color: 'var(--fg)' }}>{todoTitle(selected.todo)}</span>
                </div>
                <div className="mute" style={{ marginTop: 4 }}>{todoDetail(selected.todo)}</div>
                <div style={{ marginTop: 4, fontSize: 10 }}>
                  <span className="mute">deps:</span>{' '}
                  {selected.deps.length ? selected.deps.map(dep => <span key={dep} className="acc">§{dep} </span>) : <span className="mute">(none)</span>}
                </div>
              </>
            );
          })()}
        </div>
      ) : null}
    </div>
  );
};
