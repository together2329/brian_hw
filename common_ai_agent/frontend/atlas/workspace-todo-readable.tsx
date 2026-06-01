import type { ReactNode } from 'react';
import { atlasStatusMeta } from './workspace-report-status';
import {
  todoCriteriaLines,
  todoDetail,
  todoId,
  todoNotes,
  todoState,
  todoTitle,
  type TodoRecord,
} from './workspace-todo-model';

export type TodoViewMode = 'list' | 'detail' | 'edit';

type TodoViewTabsProps = {
  readonly view: TodoViewMode;
  readonly onChange: (view: TodoViewMode) => void;
};

type TodoReadableListProps = {
  readonly todos: readonly TodoRecord[];
  readonly openId: string | null;
  readonly onOpenIdChange: (id: string | null) => void;
};

type TodoReadableDetailProps = {
  readonly todos: readonly TodoRecord[];
};

const viewModes: readonly TodoViewMode[] = ['list', 'detail', 'edit'];

export const TodoViewTabs = ({ view, onChange }: TodoViewTabsProps): ReactNode => (
  <div style={{ display: 'inline-flex', border: '1px solid var(--line)', borderRadius: 3, overflow: 'hidden' }}>
    {viewModes.map(mode => (
      <button
        key={mode}
        type="button"
        aria-pressed={view === mode}
        onClick={() => onChange(mode)}
        style={{
          border: 0,
          borderRight: mode === 'edit' ? 0 : '1px solid var(--line)',
          background: view === mode ? 'var(--accent)' : 'var(--bg)',
          color: view === mode ? 'var(--bg)' : 'var(--fg-mute)',
          fontFamily: 'var(--mono)',
          fontSize: 'var(--ui-control-font-size)',
          fontWeight: 800,
          lineHeight: 1,
          minWidth: 62,
          padding: '7px 10px',
          textTransform: 'uppercase',
          cursor: 'pointer',
        }}
      >
        {mode}
      </button>
    ))}
  </div>
);

export const TodoReadableList = ({ todos, openId, onOpenIdChange }: TodoReadableListProps): ReactNode => {
  if (!todos.length) return <TodoEmptyState text="No todos for this session yet." />;
  return (
    <div style={{ display: 'grid', gap: 8 }}>
      {todos.map((todo, index) => {
        const id = todoId(todo, index);
        const expanded = openId === id;
        return (
          <section key={id} className="digest-card" style={{
            border: `1px solid ${expanded ? atlasStatusMeta(todoState(todo)).color : 'var(--line)'}`,
            borderRadius: 4,
            background: expanded ? 'var(--bg-2)' : 'transparent',
            overflow: 'hidden',
          }}>
            <button
              type="button"
              aria-expanded={expanded}
              onClick={() => onOpenIdChange(expanded ? null : id)}
              style={{
                width: '100%',
                border: 0,
                background: 'transparent',
                color: 'var(--fg)',
                cursor: 'pointer',
                display: 'grid',
                gridTemplateColumns: 'auto auto minmax(0, 1fr) auto',
                alignItems: 'center',
                gap: 9,
                padding: '10px 12px',
                textAlign: 'left',
              }}
            >
              <TodoIndex index={index} />
              <TodoStatus status={todoState(todo)} />
              <span style={{ minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontWeight: 700 }}>
                {todoTitle(todo)}
              </span>
              <span className="mute" style={{ fontFamily: 'var(--mono)', fontSize: 'var(--ui-control-font-size)' }}>
                {String(todo.priority || '').toUpperCase()}
              </span>
            </button>
            {expanded ? (
              <div style={{ borderTop: '1px solid var(--line)', padding: '12px 14px 14px' }}>
                <TodoReadableBody todo={todo} />
              </div>
            ) : null}
          </section>
        );
      })}
    </div>
  );
};

export const TodoReadableDetail = ({ todos }: TodoReadableDetailProps): ReactNode => {
  if (!todos.length) return <TodoEmptyState text="No todos for this session yet." />;
  return (
    <div style={{ display: 'grid', gap: 12 }}>
      {todos.map((todo, index) => (
        <section key={todoId(todo, index)} className="digest-card" style={{
          border: '1px solid var(--line)',
          borderLeft: `3px solid ${atlasStatusMeta(todoState(todo)).color}`,
          borderRadius: 4,
          background: 'var(--bg-2)',
          padding: '12px 14px',
        }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'auto auto minmax(0, 1fr)', alignItems: 'center', gap: 9, marginBottom: 12 }}>
            <TodoIndex index={index} />
            <TodoStatus status={todoState(todo)} />
            <strong style={{ color: 'var(--fg)', minWidth: 0, overflowWrap: 'anywhere' }}>{todoTitle(todo)}</strong>
          </div>
          <TodoReadableBody todo={todo} />
        </section>
      ))}
    </div>
  );
};

const TodoIndex = ({ index }: { readonly index: number }): ReactNode => (
  <span style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)', fontWeight: 800 }}>#{index + 1}</span>
);

const TodoStatus = ({ status }: { readonly status: string }): ReactNode => {
  const meta = atlasStatusMeta(status);
  return (
    <span style={{
      border: `1px solid ${meta.color}`,
      borderRadius: 999,
      color: meta.color,
      fontFamily: 'var(--mono)',
      fontSize: 10,
      fontWeight: 800,
      padding: '2px 7px',
      textTransform: 'uppercase',
      whiteSpace: 'nowrap',
    }}>
      {meta.glyph} {status}
    </span>
  );
};

const TodoReadableBody = ({ todo }: { readonly todo: TodoRecord }): ReactNode => {
  const criteria = todoCriteriaLines(todo);
  const notes = todoNotes(todo);
  return (
    <div style={{ display: 'grid', gap: 12, color: 'var(--fg-dim)', lineHeight: 1.6 }}>
      <TodoTextBlock label="Detail" value={todoDetail(todo) || '(no detail)'} />
      <TodoListBlock label="Criteria" lines={criteria.length ? criteria : ['(no criteria)']} />
      {todo.approvedReason ? <TodoTextBlock label="Approved Reason" value={todo.approvedReason} /> : null}
      {todo.rejectionReason ? <TodoTextBlock label="Rejected Reason" value={todo.rejectionReason} /> : null}
      {notes.length ? <TodoListBlock label="To Do Note" lines={notes} accent /> : null}
    </div>
  );
};

const TodoTextBlock = ({ label, value }: { readonly label: string; readonly value: string }): ReactNode => (
  <div>
    <TodoLabel>{label}</TodoLabel>
    <div style={{ color: 'var(--fg)', overflowWrap: 'anywhere', whiteSpace: 'pre-wrap' }}>{value}</div>
  </div>
);

const TodoListBlock = ({ label, lines, accent = false }: {
  readonly label: string;
  readonly lines: readonly string[];
  readonly accent?: boolean;
}): ReactNode => (
  <div>
    <TodoLabel>{label}</TodoLabel>
    <ul style={{ margin: 0, paddingLeft: 20, display: 'grid', gap: 4 }}>
      {lines.map((line, index) => (
        <li key={`${index}-${line}`} style={{ color: accent ? 'var(--cyan)' : 'var(--fg)', overflowWrap: 'anywhere' }}>{line}</li>
      ))}
    </ul>
  </div>
);

const TodoLabel = ({ children }: { readonly children: ReactNode }): ReactNode => (
  <div style={{
    color: 'var(--cyan)',
    fontFamily: 'var(--mono)',
    fontSize: 10,
    fontWeight: 800,
    letterSpacing: '0.08em',
    marginBottom: 4,
    textTransform: 'uppercase',
  }}>
    {children}
  </div>
);

const TodoEmptyState = ({ text }: { readonly text: string }): ReactNode => (
  <div style={{ color: 'var(--fg-mute)', fontStyle: 'italic', padding: '24px 0', textAlign: 'center' }}>
    {text}
  </div>
);
