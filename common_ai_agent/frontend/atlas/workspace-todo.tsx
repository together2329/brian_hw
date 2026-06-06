import { useEffect, useReducer, useState, type CSSProperties, type ReactNode } from 'react';
import { TodoEditorRow } from './workspace-todo-edit-row';
import { TodoGraph } from './workspace-todo-graph';
import {
  TODO_EDITOR_STATES,
  isTodoRecord,
  todoCriteriaText,
  todoState,
  type TodoMutationApi,
  type TodoRecord,
  type TodoSaveFields,
} from './workspace-todo-model';
import {
  TodoReadableDetail,
  TodoReadableList,
  TodoViewTabs,
  type TodoViewMode,
} from './workspace-todo-readable';

export { TodoGraph } from './workspace-todo-graph';
export { TODO_EDITOR_STATES };

const isPlanIntent = (intent: string): boolean => intent === 'plan' || intent === 'plan_q';

export const TodoEditorPane = ({ intent = 'normal' }: { readonly intent?: string } = {}): ReactNode => {
  const [, bump] = useReducer((x: number) => x + 1, 0);
  useEffect(() => {
    const handler = (event: Event) => {
      const detail = event instanceof CustomEvent ? event.detail : undefined;
      if (!detail || detail === 'TODOS' || detail === 'SESSION_STATE') bump();
    };
    window.addEventListener('atlas-data-changed', handler);
    const api: TodoMutationApi = window.atlasData || {};
    void api.refreshTodos?.({ force: true });
    return () => window.removeEventListener('atlas-data-changed', handler);
  }, []);

  const rawTodos: unknown = window.TODOS;
  const todos: readonly TodoRecord[] = Array.isArray(rawTodos) ? rawTodos.filter(isTodoRecord) : [];
  const api: TodoMutationApi = window.atlasData || {};
  const planLocked = isPlanIntent(intent);
  const [view, setView] = useState<TodoViewMode>('list');
  const [openId, setOpenId] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState('');
  const [newContent, setNewContent] = useState('');
  const [newDetail, setNewDetail] = useState('');
  const [newCriteria, setNewCriteria] = useState('');
  const [newPriority, setNewPriority] = useState('medium');
  const canAddTodo = Boolean(newContent.trim() && newDetail.trim() && newCriteria.trim());

  const runMutation = async (fn: () => Promise<void>) => {
    setBusy(true);
    setErr('');
    try {
      await fn();
    } catch (error) {
      setErr(error instanceof Error ? error.message : String(error));
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
    void runMutation(async () => {
      if (!api.addTodo) throw new Error('addTodo unavailable');
      await api.addTodo({ content, detail, criteria, priority: newPriority });
      setNewContent('');
      setNewDetail('');
      setNewCriteria('');
      setNewPriority('medium');
    });
  };

  const handleSaveRow = (index: number, fields: TodoSaveFields) => {
    const currentState = todoState(todos[index] || {});
    if (planLocked && fields.state !== currentState && fields.state !== 'pending') {
      setErr('Plan mode keeps todos pending until the plan is approved.');
      return;
    }
    void runMutation(async () => {
      if (!api.updateTodo) throw new Error('updateTodo unavailable');
      await api.updateTodo(index, fields);
    });
  };

  const handleRemove = (index: number) => {
    if (!window.confirm('Remove this todo?')) return;
    void runMutation(async () => {
      if (!api.removeTodo) throw new Error('removeTodo unavailable');
      await api.removeTodo(index);
    });
  };

  const handleInsertAbove = (index: number) => {
    setErr(`Use the add form with content, detail, and criteria before inserting above item ${index + 1}.`);
  };

  const handleClearAll = () => {
    if (!todos.length) return;
    if (!window.confirm('Clear ALL todos for this session? This cannot be undone.')) return;
    void runMutation(async () => {
      if (!api.clearTodos) throw new Error('clearTodos unavailable');
      await api.clearTodos();
    });
  };

  const fieldLabel: CSSProperties = {
    color: 'var(--cyan)',
    fontSize: 10,
    letterSpacing: '0.08em',
    textTransform: 'uppercase',
    fontWeight: 700,
    marginBottom: 3,
  };
  const inputStyle: CSSProperties = {
    width: '100%',
    boxSizing: 'border-box',
    padding: '5px 8px',
    background: 'var(--bg)',
    color: 'var(--fg)',
    border: '1px solid var(--line)',
    borderRadius: 3,
    fontFamily: 'var(--mono)',
    fontSize: 'var(--ui-font-size)',
  };

  return (
    <div style={{ flex: 1, minHeight: 0, overflow: 'auto', padding: '14px 18px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
        <div style={{ fontWeight: 700, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--fg)' }}>
          Todos ({todos.length})
        </div>
        <TodoViewTabs view={view} onChange={setView} />
        {planLocked ? (
          <span style={{ color: 'var(--accent)', fontFamily: 'var(--mono)', fontSize: 'var(--ui-control-font-size)' }}>
            PLAN MODE · pending until approval
          </span>
        ) : null}
        <span style={{ flex: 1 }} />
        {view === 'edit' ? (
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
        ) : null}
      </div>

      {err ? (
        <div style={{
          marginBottom: 10, padding: '6px 10px', borderRadius: 3,
          border: '1px solid var(--err)', color: 'var(--err)',
          fontFamily: 'var(--mono)', fontSize: 'var(--ui-font-size)',
        }}>{err}</div>
      ) : null}

      {view === 'list' ? (
        <TodoReadableList todos={todos} openId={openId} onOpenIdChange={setOpenId} />
      ) : view === 'detail' ? (
        <TodoReadableDetail todos={todos} />
      ) : view === 'graph' ? (
        <TodoGraph todos={todos} openId={openId} setOpenId={setOpenId} />
      ) : (
        <div style={{ display: 'grid', gap: 16 }}>
          <div className="digest-card" style={{
            border: '1px solid var(--line)', borderRadius: 4, padding: 12,
            display: 'grid', gap: 8,
          }}>
            <div style={fieldLabel}>+ Add todo</div>
            <input
              style={inputStyle}
              placeholder="content (required)"
              value={newContent}
              disabled={busy}
              onChange={event => setNewContent(event.target.value)}
            />
            <textarea
              style={{ ...inputStyle, minHeight: 48, resize: 'vertical' }}
              placeholder="detail (required)"
              value={newDetail}
              disabled={busy}
              onChange={event => setNewDetail(event.target.value)}
            />
            <textarea
              style={{ ...inputStyle, minHeight: 48, resize: 'vertical' }}
              placeholder="criteria — one per line (required)"
              value={newCriteria}
              disabled={busy}
              onChange={event => setNewCriteria(event.target.value)}
            />
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <select
                style={{ ...inputStyle, width: 'auto' }}
                value={newPriority}
                disabled={busy}
                onChange={event => setNewPriority(event.target.value)}
              >
                {['high', 'medium', 'low'].map(priority => <option key={priority} value={priority}>{priority}</option>)}
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
                  opacity: (busy || !canAddTodo) ? 0.5 : 1,
                }}
              >+ Add todo</button>
            </div>
          </div>

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
                  criteriaText={todoCriteriaText(todo.criteria)}
                  fieldLabel={fieldLabel}
                  inputStyle={inputStyle}
                  planLocked={planLocked}
                  onSave={fields => handleSaveRow(index, fields)}
                  onRemove={() => handleRemove(index)}
                  onInsertAbove={() => handleInsertAbove(index)}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
