// progress-todo-todo.tsx — the editable TODO tab (TodoPanel) extracted from
// progress-todo-panels.tsx so the source and each sibling stay under 1000 lines.
//
// Editable TODO tab — full-column pane that mirrors the session todo.json
// (.session/<session>/todo.json) and supports add / modify / remove / clear
// via the /api/todos/{add,update,remove,clear} endpoints. Source of truth is
// window.TODOS (produced by data.jsx). The window.TodoPanel bridge below keeps
// not-yet-migrated .jsx consumers resolving the late-bound global.
import { useState, type ReactNode } from 'react';
import {
  w,
  atlasStatusMeta,
  _limitAtlasLines,
  AtlasStatusBadge,
  TodoGraph,
  type TodoItem,
} from './progress-todo-globals';

const TodoPanel = (): ReactNode => {
  const [view, setView] = useState('compact'); // compact | detail | graph
  const [openId, setOpenId] = useState<unknown>(null);
  // Per-group collapse state in compact view: {approved: true, ...}
  // means that group is collapsed. Defaults set via collapsedDefault
  // inside the render so they're not duplicated.
  const [collapsedTodoGroups, setCollapsedTodoGroups] = useState<Record<string, boolean>>({});
  const todos: TodoItem[] = Array.isArray(w.TODOS) ? w.TODOS as TodoItem[] : [];
  // Keep the progress denominator aligned with the shared TODO state machine:
  // only explicit `approved` closes a task. `completed` and legacy `done`
  // still need review, so they must not fill the "approved / total" bar.
  const approved = todos.filter(t => t.state === 'approved').length;

  // Map every status to a glyph + color so the right panel reads at a
  // glance. data.jsx normalizes TodoTracker statuses
  // (pending/in_progress/completed/approved/rejected) into the simpler
  // pending/active/done used by this UI; the renderer below also keeps
  // explicit cases for the raw statuses so live updates render right.
  const stateCfg = (s: string | undefined): { glyph: string; color: string; label: ReactNode } => {
    const meta = atlasStatusMeta(s);
    switch (s) {
      // Auto-finished by the agent (no explicit human nod)
      case 'done':        return { glyph: meta.glyph, color: meta.color, label: 'completed' };
      case 'completed':   return { glyph: meta.glyph, color: meta.color, label: meta.label };
      // Explicitly approved by a human — distinct glyph + accent
      // colour so the pending/approved distinction reads at a glance
      case 'approved':    return { glyph: meta.glyph, color: meta.color, label: meta.label };
      case 'active':      return { glyph: meta.glyph, color: meta.color, label: 'in-progress' };
      case 'in_progress': return { glyph: meta.glyph, color: meta.color, label: meta.label };
      case 'rejected':    return { glyph: meta.glyph, color: meta.color, label: meta.label };
      // Hollow square + warm warn-yellow so it never reads as "done"
      case 'pending':     return { glyph: meta.glyph, color: meta.color, label: meta.label };
      default:            return { glyph: '☐', color: 'var(--fg-mute)', label: s || '?' };
    }
  };

  const todoLines = (value: unknown, { splitCommas = false }: { splitCommas?: boolean } = {}): string[] => {
    if (Array.isArray(value)) {
      return value.flatMap(v => todoLines(v, { splitCommas }));
    }
    if (value && typeof value === 'object') {
      return Object.entries(value).flatMap(([k, v]) => {
        const vv = String(v ?? '').trim();
        return vv ? [`${k}: ${vv}`] : [String(k)];
      }).filter(Boolean);
    }
    const raw = String(value ?? '').trim();
    if (!raw) return [];
    const prepared = raw.replace(/\s+(Each\s+TODO\s+gets:)/gi, '\n$1');
    return prepared
      .split(/\r?\n+/)
      .map(line => line.trim())
      .filter(Boolean)
      .flatMap((line) => {
        const clean = line.replace(/^[-*•]\s*/, '').trim();
        if (!clean) return [];
        if (!splitCommas) return [clean];
        const m = clean.match(/^([^:]{2,48}):\s*(.+)$/);
        if (m) return [clean];
        const items = clean.split(/\s*,\s*/).map(s => s.trim()).filter(Boolean);
        if (items.length >= 4 && clean.length > 120) return items;
        return [clean];
      });
  };

  const todoDetailBlocks = (detail: unknown): Array<{ type: 'list'; label: string; items: string[] } | { type: 'text'; text: string }> => {
    const blocks: Array<{ type: 'list'; label: string; items: string[] } | { type: 'text'; text: string }> = [];
    todoLines(detail, { splitCommas: false }).forEach((line) => {
      const parts = line.length > 180
        ? line.split(/(?<=\.)\s+|;\s+/).map(s => s.trim()).filter(Boolean)
        : [line];
      parts.forEach((part) => {
        const listMatch = part.match(/^([^:]{2,48}):\s*(.+)$/);
        if (listMatch && listMatch[2].includes(',')) {
          const items = listMatch[2].split(/\s*,\s*/).map(s => s.trim()).filter(Boolean);
          if (items.length >= 3) {
            blocks.push({ type: 'list', label: listMatch[1], items });
            return;
          }
        }
        blocks.push({ type: 'text', text: part });
      });
    });
    return blocks;
  };

  const TodoField = ({ label, children }: { label?: ReactNode; children?: ReactNode }) => (
    <div style={{ display: 'grid', gap: 3 }}>
      <div style={{
        color: 'var(--cyan)',
        fontSize: 10,
        letterSpacing: '0.08em',
        textTransform: 'uppercase',
        fontWeight: 700,
      }}>{label}</div>
      <div style={{ color: 'var(--fg-dim)', lineHeight: 1.62 }}>{children}</div>
    </div>
  );

  const TodoBulletList = ({ items }: { items: string[] }) => (
    <div style={{ display: 'grid', gap: 2 }}>
      {items.map((item, idx) => (
        <div key={`${item}-${idx}`} style={{ display: 'flex', alignItems: 'flex-start', gap: 6 }}>
          <span className="mute" style={{ lineHeight: 1.6 }}>•</span>
          <span style={{ flex: 1 }}>{item}</span>
        </div>
      ))}
    </div>
  );

  const TodoStructuredBody = ({ todo }: { todo: TodoItem }) => {
    const detail = todoDetailBlocks(todo.detail);
    const criteria = todoLines(todo.criteria, { splitCommas: true });
    const sourceRefs = todoLines(todo.sourceRefs, { splitCommas: true });
    const owner = [String(todo.ownerModule || '').trim(), String(todo.ownerFile || '').trim()].filter(Boolean);
    const required = typeof todo.required === 'boolean'
      ? (todo.required ? 'yes' : 'no')
      : (todo.required == null ? '' : String(todo.required).trim());
    return (
      <div style={{ display: 'grid', gap: 8, overflowWrap: 'anywhere' }}>
        {detail.length > 0 && (
          <TodoField label="Detail">
            <div style={{ display: 'grid', gap: 4 }}>
              {detail.map((blk, idx) => (
                blk.type === 'list' ? (
                  <div key={`dlist-${idx}`} style={{ display: 'grid', gap: 3 }}>
                    <span style={{ color: 'var(--fg)' }}>{blk.label}</span>
                    <TodoBulletList items={blk.items} />
                  </div>
                ) : (
                  <div key={`dtext-${idx}`}>{blk.text}</div>
                )
              ))}
            </div>
          </TodoField>
        )}
        {criteria.length > 0 && (
          <TodoField label="Criteria">
            <TodoBulletList items={criteria} />
          </TodoField>
        )}
        {sourceRefs.length > 0 && (
          <TodoField label="Source Refs">
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {sourceRefs.map((ref, idx) => (
                <span key={`src-${idx}`} style={{
                  border: '1px solid var(--line)',
                  borderRadius: 2,
                  padding: '1px 6px',
                  color: 'var(--fg)',
                }}>{ref}</span>
              ))}
            </div>
          </TodoField>
        )}
        {owner.length > 0 && (
          <TodoField label="Owner">{owner.join(' · ')}</TodoField>
        )}
        {required && (
          <TodoField label="Required">{required}</TodoField>
        )}
      </div>
    );
  };

  const TodoReason = ({ todo }: { todo: TodoItem }) => {
    const approved = todo.state === 'approved';
    const rejected = todo.state === 'rejected';
    const reason = approved ? todo.approvedReason : rejected ? todo.rejectionReason : '';
    if (!reason) return null;
    const label = approved ? 'Approved' : 'Rejected';
    const color = approved ? 'var(--ok)' : 'var(--err)';
    return (
      <div style={{
        marginTop: 5,
        fontFamily: 'var(--mono)',
        fontSize: 'var(--ui-font-size)',
        lineHeight: 1.55,
        whiteSpace: 'pre-wrap',
      }}>
        <span style={{ color, fontWeight: 700 }}>{label}</span>
        <span className="mute"> : </span>
        <span style={{ color: 'var(--fg-dim)' }}>{_limitAtlasLines(reason, 5)}</span>
      </div>
    );
  };

  const TodoNotes = ({ todo }: { todo: TodoItem }) => {
    const notes = Array.isArray(todo.notes) ? todo.notes.filter(n => String(n || '').trim()) : [];
    if (!notes.length) return null;
    const lastIndex = notes.length;
    const last = String(notes[notes.length - 1] || '');
    return (
      <div style={{
        marginTop: 5,
        fontFamily: 'var(--mono)',
        fontSize: 'var(--ui-font-size)',
        lineHeight: 1.55,
        whiteSpace: 'pre-wrap',
      }}>
        <span style={{ color: 'var(--cyan)', fontWeight: 700 }}>Notes</span>
        <span className="mute"> : </span>
        <span style={{ color: 'var(--fg-dim)' }}>[{lastIndex}] {_limitAtlasLines(last, 5)}</span>
        {notes.length > 1 && (
          <span className="mute" style={{ marginLeft: 6 }}>+{notes.length - 1} earlier</span>
        )}
      </div>
    );
  };

  // Counts per state for the header summary
  const counts = todos.reduce((acc: Record<string, number>, t) => {
    const cfg = stateCfg(t.state);
    acc[cfg.label as string] = (acc[cfg.label as string] || 0) + 1;
    return acc;
  }, {});

  // ── header tab strip
  const Tab = ({ id, label }: { id: string; label: ReactNode }) => (
    <span onClick={() => setView(id)} style={{
      cursor: 'pointer', padding: '4px 10px', fontSize: 10, letterSpacing: '0.06em',
      textTransform: 'uppercase', fontFamily: 'var(--mono)',
      color: view === id ? 'var(--fg)' : 'var(--fg-mute)',
      background: view === id ? 'var(--bg-2)' : 'transparent',
      border: `1px solid ${view === id ? 'var(--accent)' : 'var(--line)'}`,
      borderRadius: 2,
    }}>{label}</span>
  );

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <div style={{
        padding: '8px 12px', borderBottom: '1px solid var(--line)',
        display: 'flex', alignItems: 'center', gap: 6, fontSize: 'var(--ui-control-font-size)', flexWrap: 'wrap',
      }}>
        <span className="mute" style={{ fontFamily: 'var(--mono)' }}>{approved}/{todos.length}</span>
        {/* color-coded count chips per state */}
        {['in-progress','pending','done','approved','completed','rejected'].filter(k => counts[k]).map(k => {
          const c = stateCfg(k === 'done' ? 'done' : k.replace('-', '_'));
          return (
            <AtlasStatusBadge key={k} status={k} label={c.label} count={counts[k]} compact soft />
          );
        })}
        <span style={{ flex: 1 }} />
        <span title="Clear all todos"
          onClick={() => { if (confirm('Clear all todos?')) w.atlasData!.clearTodos!(); }}
          style={{
            cursor: 'pointer', fontSize: 10, padding: '2px 8px',
            border: '1px solid var(--line)', color: 'var(--fg-mute)',
            borderRadius: 2,
          }}>✕ clear</span>
        <span className="mute" style={{ fontSize: 10, letterSpacing: '0.06em', textTransform: 'uppercase' }}>view</span>
        <Tab id="compact" label="list" />
        <Tab id="detail" label="detail" />
        <Tab id="graph" label="graph" />
      </div>

      {/* Progress bar — at-a-glance "X / Y approved" with green fill */}
      {todos.length > 0 && (
        <div style={{ padding: '6px 12px 4px', borderBottom: '1px solid var(--line)',
                       background: 'var(--bg-2)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between',
                         fontSize: 10, fontFamily: 'var(--mono)',
                         color: 'var(--fg-mute)', marginBottom: 3 }}>
            <span>progress</span>
            <span><b style={{ color: 'var(--ok)' }}>{approved}</b> / {todos.length} approved</span>
          </div>
          <div style={{ height: 4, background: 'var(--bg-3)',
                         border: '1px solid var(--line)', borderRadius: 2,
                         overflow: 'hidden' }}>
            <div style={{
              height: '100%',
              width: `${todos.length ? Math.round(100 * approved / todos.length) : 0}%`,
              background: '#3fb950',
              transition: 'width 240ms ease-out',
            }} />
          </div>
        </div>
      )}

      <div style={{ flex: 1, overflow: 'auto' }}>
        {view === 'compact' && (() => {
          // Group by status order: in_progress → pending → completed →
          // rejected → approved (approved collapsed by default since it's
          // usually the long tail of "done" todos that the user no longer
          // needs to scan).
          const groupOf = (t: TodoItem) => {
            const s = t.state;
            if (s === 'active' || s === 'in_progress') return 'in_progress';
            if (s === 'completed') return 'completed';
            if (s === 'approved') return 'approved';
            if (s === 'done') return 'completed';
            if (s === 'rejected') return 'rejected';
            return 'pending';
          };
          const groups: Record<string, TodoItem[]> = { in_progress: [], pending: [], completed: [], rejected: [], approved: [] };
          todos.forEach(t => groups[groupOf(t)].push(t));
          const order = ['in_progress', 'pending', 'completed', 'rejected', 'approved'];
          const labels: Record<string, string> = {
            in_progress: 'IN PROGRESS', pending: 'PENDING',
            completed: 'COMPLETED',     rejected: 'REJECTED', approved: 'APPROVED',
          };
          // approved + rejected default-collapsed; in-progress/pending/completed default-open
          const collapsedDefault: Record<string, boolean> = { approved: true, rejected: true };
          const isCollapsed = (g: string) => collapsedTodoGroups[g] !== undefined
            ? collapsedTodoGroups[g] : (collapsedDefault[g] || false);
          const toggleGroup = (g: string) => setCollapsedTodoGroups(prev =>
            ({ ...prev, [g]: !isCollapsed(g) }));
          return (
            <div style={{ padding: '4px 0' }}>
              {order.map(g => {
                const items = groups[g];
                if (!items.length) return null;
                const collapsed = isCollapsed(g);
                const cfg = stateCfg(g === 'in_progress' ? 'in_progress' : g);
                return (
                  <div key={g}>
                    {/* Group divider — uppercase label, click to toggle */}
                    <div
                      onClick={() => toggleGroup(g)}
                      style={{
                        display: 'flex', alignItems: 'center', gap: 6,
                        padding: '4px 12px 2px', cursor: 'pointer',
                        fontFamily: 'var(--mono)', fontSize: 10,
                        letterSpacing: '0.1em', textTransform: 'uppercase',
                        color: cfg.color, userSelect: 'none',
                      }}
                    >
                      <span>{collapsed ? '▸' : '▾'}</span>
                      <AtlasStatusBadge status={g} label={labels[g]} count={items.length} compact />
                      <span style={{ flex: 1, height: 1, background: 'var(--line)',
                                      opacity: 0.5, marginLeft: 6 }} />
                    </div>
                    {!collapsed && items.map(t => {
                      const open = openId === t.id;
                      return (
                        <div key={t.id as string}>
                          <div
                            onClick={() => setOpenId(open ? null : t.id)}
                            style={{
                              display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 16px',
                              alignItems: 'baseline', gap: 8, padding: '6px 12px',
                              cursor: 'pointer', fontFamily: 'var(--mono)', fontSize: 13,
                              background: t.state === 'active' || t.state === 'in_progress'
                                ? 'color-mix(in oklch, var(--accent) 8%, transparent)'
                                : 'transparent',
                              borderLeft: (t.state === 'active' || t.state === 'in_progress')
                                ? '2px solid var(--accent)' : '2px solid transparent',
                            }}
                          >
                            <span style={{ color: t.state === 'pending' ? 'var(--fg-dim)' : 'var(--fg)' }}>{t.title}</span>
                            <span className="mute" style={{ fontSize: 10 }}>{open ? '▾' : '▸'}</span>
                          </div>
                          {open && (
                            <div className="fade-in" style={{
                              padding: '10px 14px 12px 64px',
                              fontSize: 13,
                              lineHeight: 1.68,
                              color: 'var(--fg-dim)',
                              borderLeft: '2px solid var(--line-2)',
                              borderTop: '1px solid var(--line)',
                              marginLeft: 12,
                              marginRight: 12,
                              background: 'color-mix(in oklch, var(--bg-2) 92%, var(--fg) 8%)',
                            }}>
                              <TodoStructuredBody todo={t} />
                              <TodoNotes todo={t} />
                              <TodoReason todo={t} />
                              {t.deps && t.deps.length > 0 && (
                                <div style={{ marginTop: 6, fontSize: 'var(--ui-control-font-size)', lineHeight: 1.5 }}>
                                  <span className="mute">deps:</span>{' '}
                                  {t.deps.map(d => <span key={d as string} className="acc">§{d as ReactNode} </span>)}
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                );
              })}
            </div>
          );
        })()}

        {view === 'detail' && (
          <div>
            {todos.map(t => {
              const cfg = stateCfg(t.state);
              return (
                <div key={t.id as string} style={{
                  padding: '10px 14px', borderBottom: '1px solid var(--line)',
                  background: t.state === 'active' ? 'var(--bg-2)' : 'transparent',
                  borderLeft: t.state === 'active' ? '2px solid var(--accent)' : '2px solid transparent',
                }}>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
                    <AtlasStatusBadge status={t.state} label={cfg.label} compact soft />
                    <span className="mute" style={{ fontSize: 11 }}>{t.section}</span>
                    <span style={{ fontWeight: t.state === 'active' ? 600 : 500, flex: 1, fontSize: 13, color: 'var(--fg)' }}>{t.title}</span>
                  </div>
                  <div style={{
                    color: 'var(--fg-dim)',
                    fontSize: 13,
                    marginTop: 6,
                    marginLeft: 22,
                    lineHeight: 1.62,
                  }}>
                    <TodoStructuredBody todo={t} />
                  </div>
                  <div style={{ marginLeft: 22 }}>
                    <TodoNotes todo={t} />
                    <TodoReason todo={t} />
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {view === 'graph' && <TodoGraph todos={todos} openId={openId} setOpenId={setOpenId} />}
      </div>
    </div>
  );
};

// ── Transitional bridge: register on window for not-yet-migrated .jsx ──
// Phase 23 window export (kept so unmigrated .jsx consumers still resolve
// window.TodoPanel).
(window as unknown as { TodoPanel: typeof TodoPanel }).TodoPanel = TodoPanel;

export { TodoPanel };
