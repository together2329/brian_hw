/* workspace-todo.tsx — Todo editor surface (strangler-fig mirror of workspace.jsx).
 *
 * Owns:
 *   TODO_EDITOR_STATES — allowed lifecycle states for the inline editor.
 *   TodoEditorPane      — container; reads window.TODOS + window.atlasData
 *                         mutation API (addTodo/updateTodo/removeTodo/clearTodos),
 *                         re-renders on the `atlas-data-changed` event.
 *   TodoEditorRow       — per-todo inline editor row.
 *   TodoGraph           — SVG DAG dependency visualization, laid out by
 *                         topological level.
 *
 * Status helpers (atlasStatusMeta / normalizeAtlasStatus) come from the
 * workspace-report-status sibling. TodoGraph is bridged to window.TodoGraph
 * by the legacy workspace.jsx; this mirror only exports the symbol.
 */
import { useState, useEffect, useReducer } from 'react';
import { atlasStatusMeta, normalizeAtlasStatus } from './workspace-report-status';

// ── Cross-file window globals (owned by other, not-yet-migrated .jsx) ──
// These are not declared in types/atlas-window.d.ts, so read them through a
// permissively-typed view of window — behavior is identical to legacy
// `window.X` access.
const _win = window as any;

export const TODO_EDITOR_STATES = ['pending', 'in_progress', 'completed', 'approved', 'rejected'];

export const TodoEditorPane = () => {
  // Re-render on data-layer refreshes so live agent edits + our mutations show.
  const [, bump] = useReducer((x: number) => x + 1, 0);
  useEffect(() => {
    const h = (ev: any) => { if (!ev.detail || ev.detail === 'TODOS' || ev.detail === 'SESSION_STATE') bump(); };
    window.addEventListener('atlas-data-changed', h);
    if (_win.atlasData && _win.atlasData.refreshTodos) _win.atlasData.refreshTodos({ force: true });
    return () => window.removeEventListener('atlas-data-changed', h);
  }, []);

  const todos: any[] = Array.isArray(_win.TODOS) ? _win.TODOS : [];
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  // Add-form local state
  const [newContent, setNewContent] = useState('');
  const [newDetail, setNewDetail] = useState('');
  const [newCriteria, setNewCriteria] = useState('');
  const [newPriority, setNewPriority] = useState('medium');

  const api: any = _win.atlasData || {};
  const criteriaText = (c: any) => Array.isArray(c) ? c.join('\n') : String(c || '');
  const canAddTodo = Boolean(newContent.trim() && newDetail.trim() && newCriteria.trim());

  const runMutation = async (fn: () => Promise<void>) => {
    setBusy(true);
    setErr('');
    try {
      await fn();
    } catch (e: any) {
      setErr(String(e && e.message ? e.message : e));
    } finally {
      setBusy(false);
    }
  };

  const handleAdd = () => {
    const content = newContent.trim();
    const detail = newDetail.trim();
    const criteria = newCriteria.trim();
    if (!content) { setErr('Content is required to add a todo.'); return; }
    if (!detail) { setErr('Detail is required to add a todo.'); return; }
    if (!criteria) { setErr('Criteria is required to add a todo.'); return; }
    runMutation(async () => {
      if (!api.addTodo) throw new Error('addTodo unavailable');
      await api.addTodo({ content, detail, criteria, priority: newPriority });
      setNewContent(''); setNewDetail(''); setNewCriteria(''); setNewPriority('medium');
    });
  };

  const handleSaveRow = (index: number, fields: any) => {
    runMutation(async () => {
      if (!api.updateTodo) throw new Error('updateTodo unavailable');
      await api.updateTodo(index, fields);
    });
  };

  const handleRemove = (index: number) => {
    if (!window.confirm('Remove this todo?')) return;
    runMutation(async () => {
      if (!api.removeTodo) throw new Error('removeTodo unavailable');
      await api.removeTodo(index);
    });
  };

  // Avoid creating executable placeholder tasks without explicit detail/criteria.
  const handleInsertAbove = (index: number) => {
    setErr(`Use the add form with content, detail, and criteria before inserting above item ${index + 1}.`);
  };

  const handleClearAll = () => {
    if (!todos.length) return;
    if (!window.confirm('Clear ALL todos for this session? This cannot be undone.')) return;
    runMutation(async () => {
      if (!api.clearTodos) throw new Error('clearTodos unavailable');
      await api.clearTodos();
    });
  };

  const fieldLabel = {
    color: 'var(--cyan)', fontSize: 10, letterSpacing: '0.08em',
    textTransform: 'uppercase' as const, fontWeight: 700, marginBottom: 3,
  };
  const inputStyle = {
    width: '100%', boxSizing: 'border-box' as const, padding: '5px 8px',
    background: 'var(--bg)', color: 'var(--fg)',
    border: '1px solid var(--line)', borderRadius: 3,
    fontFamily: 'var(--mono)', fontSize: 'var(--ui-font-size)',
  };

  return (
    <div style={{ flex: 1, minHeight: 0, overflow: 'auto', padding: '14px 18px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
        <div style={{ fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--fg)' }}>
          Todos ({todos.length})
        </div>
        <span style={{ flex: 1 }} />
        <button
          className="btn"
          disabled={busy || !todos.length}
          onClick={handleClearAll}
          style={{
            cursor: (busy || !todos.length) ? 'default' : 'pointer',
            padding: '3px 10px', borderRadius: 3,
            border: '1px solid var(--err)', color: 'var(--err)',
            background: 'transparent', fontSize: 'var(--ui-control-font-size)',
            opacity: (busy || !todos.length) ? 0.5 : 1,
          }}
        >Clear all</button>
      </div>

      {err && (
        <div style={{
          marginBottom: 10, padding: '6px 10px', borderRadius: 3,
          border: '1px solid var(--err)', color: 'var(--err)',
          fontFamily: 'var(--mono)', fontSize: 'var(--ui-font-size)',
        }}>{err}</div>
      )}

      {/* Add-todo form */}
      <div className="digest-card" style={{
        border: '1px solid var(--line)', borderRadius: 4, padding: 12, marginBottom: 16,
        display: 'grid', gap: 8,
      }}>
        <div style={fieldLabel}>+ Add todo</div>
        <input
          style={inputStyle}
          placeholder="content (required)"
          value={newContent}
          disabled={busy}
          onChange={(e) => setNewContent(e.target.value)}
        />
        <textarea
          style={{ ...inputStyle, minHeight: 48, resize: 'vertical' }}
          placeholder="detail (required)"
          value={newDetail}
          disabled={busy}
          onChange={(e) => setNewDetail(e.target.value)}
        />
        <textarea
          style={{ ...inputStyle, minHeight: 48, resize: 'vertical' }}
          placeholder="criteria — one per line (required)"
          value={newCriteria}
          disabled={busy}
          onChange={(e) => setNewCriteria(e.target.value)}
        />
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <select
            style={{ ...inputStyle, width: 'auto' }}
            value={newPriority}
            disabled={busy}
            onChange={(e) => setNewPriority(e.target.value)}
          >
            {['high', 'medium', 'low'].map(p => <option key={p} value={p}>{p}</option>)}
          </select>
          <span style={{ flex: 1 }} />
          <button
            className="btn"
            disabled={busy || !canAddTodo}
            onClick={handleAdd}
            style={{
              cursor: (busy || !canAddTodo) ? 'default' : 'pointer',
              padding: '4px 14px', borderRadius: 3,
              border: '1px solid var(--accent)', color: 'var(--accent)',
              background: 'transparent', fontWeight: 700,
              fontSize: 'var(--ui-control-font-size)',
              opacity: (busy || !newContent.trim()) ? 0.5 : 1,
            }}
          >+ Add todo</button>
        </div>
      </div>

      {/* Per-todo editable rows */}
      {todos.length === 0 ? (
        <div style={{ color: 'var(--fg-mute)', fontStyle: 'italic', padding: '20px 0', textAlign: 'center' }}>
          No todos for this session yet. Add one above.
        </div>
      ) : (
        <div style={{ display: 'grid', gap: 12 }}>
          {todos.map((todo, index) => (
            <TodoEditorRow
              key={todo.id || index}
              index={index}
              todo={todo}
              busy={busy}
              criteriaText={criteriaText(todo.criteria)}
              fieldLabel={fieldLabel}
              inputStyle={inputStyle}
              onSave={(fields: any) => handleSaveRow(index, fields)}
              onRemove={() => handleRemove(index)}
              onInsertAbove={() => handleInsertAbove(index)}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export const TodoEditorRow = ({ index, todo, busy, criteriaText, fieldLabel, inputStyle, onSave, onRemove, onInsertAbove }: any) => {
  const [content, setContent] = useState(todo.title || '');
  const [detail, setDetail] = useState(todo.detail || '');
  const [criteria, setCriteria] = useState(criteriaText);
  const [state, setState] = useState(todo.state || 'pending');
  const [approvedReason, setApprovedReason] = useState(todo.approvedReason || '');
  const [rejectionReason, setRejectionReason] = useState(todo.rejectionReason || '');

  // Re-sync local fields when the underlying todo changes (e.g. live refresh).
  useEffect(() => { setContent(todo.title || ''); }, [todo.title]);
  useEffect(() => { setDetail(todo.detail || ''); }, [todo.detail]);
  useEffect(() => { setCriteria(criteriaText); }, [criteriaText]);
  useEffect(() => { setState(todo.state || 'pending'); }, [todo.state]);
  useEffect(() => { setApprovedReason(todo.approvedReason || ''); }, [todo.approvedReason]);
  useEffect(() => { setRejectionReason(todo.rejectionReason || ''); }, [todo.rejectionReason]);

  const dirty = (
    content !== (todo.title || '')
    || detail !== (todo.detail || '')
    || criteria !== criteriaText
    || state !== (todo.state || 'pending')
    || approvedReason !== (todo.approvedReason || '')
    || rejectionReason !== (todo.rejectionReason || '')
  );

  const meta = atlasStatusMeta(state);
  const stateOptions = TODO_EDITOR_STATES.includes(state)
    ? TODO_EDITOR_STATES
    : [state, ...TODO_EDITOR_STATES];
  const notes: string[] = Array.isArray(todo.notes)
    ? todo.notes.map((n: any) => String(n || '').trim()).filter(Boolean)
    : [];
  const reasonMissing = (state === 'approved' && !approvedReason.trim())
    || (state === 'rejected' && !rejectionReason.trim());
  const saveDisabled = busy || !dirty || !content.trim() || reasonMissing;

  return (
    <div className="digest-card" style={{
      border: '1px solid var(--line)', borderRadius: 4, padding: 12,
      display: 'grid', gap: 8,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        {onInsertAbove ? (
          <button type="button" className="mini-btn" disabled={busy}
            title="Insert a new todo above this one (add in the middle)"
            onClick={onInsertAbove}
            style={{ fontFamily: 'var(--mono)', fontSize: 11, padding: '1px 5px', cursor: busy ? 'wait' : 'pointer' }}
          >⊕↑</button>
        ) : null}
        <span style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)' }}>#{index + 1}</span>
        <span style={{ color: meta.color }}>{meta.glyph}</span>
        <select
          style={{ ...inputStyle, width: 'auto' }}
          value={state}
          disabled={busy}
          onChange={(e) => setState(e.target.value)}
        >
          {stateOptions.map((s: string) => <option key={s} value={s}>{s}</option>)}
        </select>
        <span style={{ flex: 1 }} />
        <button
          className="btn"
          disabled={saveDisabled}
          title={reasonMissing ? 'Reason is required for approved/rejected todos.' : 'Save todo changes'}
          onClick={() => onSave({
            content,
            detail,
            criteria,
            state,
            approved_reason: approvedReason,
            rejection_reason: rejectionReason,
          })}
          style={{
            cursor: saveDisabled ? 'default' : 'pointer',
            padding: '3px 12px', borderRadius: 3,
            border: '1px solid var(--accent)', color: 'var(--accent)',
            background: 'transparent', fontSize: 'var(--ui-control-font-size)',
            opacity: saveDisabled ? 0.5 : 1,
          }}
        >Save</button>
        <button
          className="btn"
          disabled={busy}
          onClick={onRemove}
          style={{
            cursor: busy ? 'default' : 'pointer',
            padding: '3px 12px', borderRadius: 3,
            border: '1px solid var(--err)', color: 'var(--err)',
            background: 'transparent', fontSize: 'var(--ui-control-font-size)',
            opacity: busy ? 0.5 : 1,
          }}
        >Remove</button>
      </div>
      <div>
        <div style={fieldLabel}>Content</div>
        <input style={inputStyle} value={content} disabled={busy} onChange={(e) => setContent(e.target.value)} />
      </div>
      <div>
        <div style={fieldLabel}>Detail</div>
        <textarea
          style={{ ...inputStyle, minHeight: 52, resize: 'vertical' }}
          value={detail}
          disabled={busy}
          onChange={(e) => setDetail(e.target.value)}
        />
      </div>
      <div>
        <div style={fieldLabel}>Criteria (one per line)</div>
        <textarea
          style={{ ...inputStyle, minHeight: 52, resize: 'vertical' }}
          value={criteria}
          disabled={busy}
          onChange={(e) => setCriteria(e.target.value)}
        />
      </div>
      {state === 'approved' && (
        <div>
          <div style={fieldLabel}>Approved Reason</div>
          <textarea
            style={{ ...inputStyle, minHeight: 44, resize: 'vertical' }}
            placeholder="approved reason (required)"
            value={approvedReason}
            disabled={busy}
            onChange={(e) => setApprovedReason(e.target.value)}
          />
        </div>
      )}
      {state === 'rejected' && (
        <div>
          <div style={fieldLabel}>Reject Reason</div>
          <textarea
            style={{ ...inputStyle, minHeight: 44, resize: 'vertical' }}
            placeholder="reject reason (required)"
            value={rejectionReason}
            disabled={busy}
            onChange={(e) => setRejectionReason(e.target.value)}
          />
        </div>
      )}
      {notes.length > 0 && (
        <div>
          <div style={fieldLabel}>To Do Note</div>
          <div style={{
            display: 'grid',
            gap: 4,
            padding: '6px 8px',
            background: 'var(--bg)',
            border: '1px solid var(--line)',
            borderRadius: 3,
            color: 'var(--fg-dim)',
            fontFamily: 'var(--mono)',
            fontSize: 'var(--ui-font-size)',
            lineHeight: 1.55,
            whiteSpace: 'pre-wrap',
          }}>
            {notes.map((note, noteIndex) => (
              <div key={`${noteIndex}-${note}`}>
                <span style={{ color: 'var(--cyan)' }}>[{noteIndex + 1}]</span>{' '}
                <span>{note}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// ── Graph view: SVG DAG laid out by topological level ─────────────
export const TodoGraph = ({ todos, openId, setOpenId }: any) => {
  // assign each node a level = max(level of deps) + 1
  const levelOf: Record<string, number> = {};
  todos.forEach((t: any) => {
    levelOf[t.id] = (t.deps || []).reduce((m: number, d: any) => Math.max(m, (levelOf[d] ?? 0) + 1), 0);
  });
  const levels: Record<number, any[]> = {};
  todos.forEach((t: any) => { (levels[levelOf[t.id]] = levels[levelOf[t.id]] || []).push(t); });
  const levelKeys = Object.keys(levels).map(Number).sort((a, b) => a - b);

  const NODE_W = 80, NODE_H = 32, gapY = 10, gapX = 22, padX = 10, padY = 10;
  const colW = NODE_W + gapX;
  const totalW = padX * 2 + colW * levelKeys.length - gapX;
  const maxRow = Math.max(...levelKeys.map(k => levels[k].length));
  const totalH = padY * 2 + maxRow * (NODE_H + gapY) - gapY;

  const pos: Record<string, { x: number; y: number }> = {};
  levelKeys.forEach((lvl, ci) => {
    const col = levels[lvl];
    const colH = col.length * (NODE_H + gapY) - gapY;
    const yStart = padY + (totalH - padY * 2 - colH) / 2;
    col.forEach((t: any, ri: number) => {
      pos[t.id] = {
        x: padX + ci * colW,
        y: yStart + ri * (NODE_H + gapY),
      };
    });
  });

  const stateCfg = (s: any) => {
    const meta = atlasStatusMeta(s);
    const activeish = ['active', 'in_progress', 'running'].includes(normalizeAtlasStatus(s));
    const doneish = ['done', 'completed', 'approved'].includes(normalizeAtlasStatus(s));
    const errish = ['rejected', 'error', 'blocked'].includes(normalizeAtlasStatus(s));
    return {
      fill: activeish || doneish || errish ? `color-mix(in oklch, ${meta.color} 14%, transparent)` : 'transparent',
      stroke: activeish || doneish || errish ? meta.color : 'var(--line)',
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
        {/* edges */}
        <defs>
          <marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
            <path d="M0,0 L10,5 L0,10 z" fill="var(--fg-mute)" />
          </marker>
        </defs>
        {todos.flatMap((t: any) => (t.deps || []).map((d: any) => {
          const a = pos[d], b = pos[t.id];
          if (!a || !b) return null;
          const x1 = a.x + NODE_W, y1 = a.y + NODE_H / 2;
          const x2 = b.x,           y2 = b.y + NODE_H / 2;
          const mx = (x1 + x2) / 2;
          return (
            <path key={`${d}->${t.id}`}
              d={`M${x1},${y1} C${mx},${y1} ${mx},${y2} ${x2},${y2}`}
              fill="none" stroke="var(--line)" strokeWidth="1"
              markerEnd="url(#arr)"
            />
          );
        }))}
        {/* nodes */}
        {todos.map((t: any) => {
          const p = pos[t.id], cfg = stateCfg(t.state);
          const sel = openId === t.id;
          return (
            <g key={t.id}
              onClick={() => setOpenId(sel ? null : t.id)}
              style={{ cursor: 'pointer' }}
            >
              <rect x={p.x} y={p.y} width={NODE_W} height={NODE_H} rx="2"
                fill={cfg.fill} stroke={sel ? 'var(--fg)' : cfg.stroke}
                strokeWidth={sel ? 2 : 1}
              />
              <text x={p.x + 6} y={p.y + 12} fontSize="8" fill="var(--fg-mute)"
                fontFamily="var(--mono)" letterSpacing="0.04em">{t.section}</text>
              <text x={p.x + NODE_W - 6} y={p.y + 12} fontSize="9" textAnchor="end"
                fill={cfg.color} fontFamily="var(--mono)" fontWeight="700">{cfg.glyph}</text>
              <text x={p.x + 6} y={p.y + 24} fontSize="9" fill="var(--fg)"
                fontFamily="var(--mono)">
                {t.title.length > 11 ? t.title.slice(0, 10) + '…' : t.title}
              </text>
            </g>
          );
        })}
      </svg>
      </div>
      {openId && (
        <div className="fade-in" style={{
          marginTop: 12, padding: '8px 10px', borderLeft: '2px solid var(--accent)',
          background: 'var(--bg-2)', fontFamily: 'var(--mono)', fontSize: 'var(--ui-control-font-size)', lineHeight: 1.5,
        }}>
          {(() => {
            const t = todos.find((x: any) => x.id === openId);
            if (!t) return null;
            const cfg = stateCfg(t.state);
            return (
              <>
                <div>
                  <span style={{ color: cfg.color, fontWeight: 700 }}>{cfg.glyph}</span>{' '}
                  <span className="mute">{t.section}</span>{' '}
                  <span style={{ color: 'var(--fg)' }}>{t.title}</span>
                </div>
                <div className="mute" style={{ marginTop: 4 }}>{t.detail}</div>
                <div style={{ marginTop: 4, fontSize: 10 }}>
                  <span className="mute">deps:</span>{' '}
                  {(t.deps && t.deps.length) ? t.deps.map((d: any) => <span key={d} className="acc">§{d} </span>) : <span className="mute">(none)</span>}
                </div>
              </>
            );
          })()}
        </div>
      )}
    </div>
  );
};
