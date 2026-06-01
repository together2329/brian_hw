import { useEffect, useState, type CSSProperties, type ReactNode } from 'react';
import { atlasStatusMeta } from './workspace-report-status';
import {
  TODO_EDITOR_STATES,
  todoNotes,
  todoState,
  todoTitle,
  type TodoRecord,
  type TodoSaveFields,
} from './workspace-todo-model';

type TodoEditorRowProps = {
  readonly index: number;
  readonly todo: TodoRecord;
  readonly busy: boolean;
  readonly criteriaText: string;
  readonly fieldLabel: CSSProperties;
  readonly inputStyle: CSSProperties;
  readonly planLocked: boolean;
  readonly onSave: (fields: TodoSaveFields) => void;
  readonly onRemove: () => void;
  readonly onInsertAbove: () => void;
};

export const TodoEditorRow = ({
  index,
  todo,
  busy,
  criteriaText,
  fieldLabel,
  inputStyle,
  planLocked,
  onSave,
  onRemove,
  onInsertAbove,
}: TodoEditorRowProps): ReactNode => {
  const [content, setContent] = useState(todoTitle(todo));
  const [detail, setDetail] = useState(todo.detail || '');
  const [criteria, setCriteria] = useState(criteriaText);
  const [state, setState] = useState(todoState(todo));
  const [approvedReason, setApprovedReason] = useState(todo.approvedReason || '');
  const [rejectionReason, setRejectionReason] = useState(todo.rejectionReason || '');

  useEffect(() => { setContent(todoTitle(todo)); }, [todo]);
  useEffect(() => { setDetail(todo.detail || ''); }, [todo.detail]);
  useEffect(() => { setCriteria(criteriaText); }, [criteriaText]);
  useEffect(() => { setState(todoState(todo)); }, [todo]);
  useEffect(() => { setApprovedReason(todo.approvedReason || ''); }, [todo.approvedReason]);
  useEffect(() => { setRejectionReason(todo.rejectionReason || ''); }, [todo.rejectionReason]);

  const currentState = todoState(todo);
  const dirty = (
    content !== todoTitle(todo)
    || detail !== (todo.detail || '')
    || criteria !== criteriaText
    || state !== currentState
    || approvedReason !== (todo.approvedReason || '')
    || rejectionReason !== (todo.rejectionReason || '')
  );
  const meta = atlasStatusMeta(state);
  const stateOptions = TODO_EDITOR_STATES.some(option => option === state)
    ? TODO_EDITOR_STATES
    : [state, ...TODO_EDITOR_STATES];
  const notes = todoNotes(todo);
  const reasonMissing = (state === 'approved' && !approvedReason.trim())
    || (state === 'rejected' && !rejectionReason.trim());
  const blockedPlanState = planLocked && state !== currentState && state !== 'pending';
  const saveDisabled = busy || !dirty || !content.trim() || reasonMissing || blockedPlanState;

  return (
    <div className="digest-card" style={{
      border: '1px solid var(--line)', borderRadius: 4, padding: 12,
      display: 'grid', gap: 8,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <button
          type="button"
          className="mini-btn"
          disabled={busy}
          title="Insert a new todo above this one (add in the middle)"
          onClick={onInsertAbove}
          style={{ fontFamily: 'var(--mono)', fontSize: 11, padding: '1px 5px', cursor: busy ? 'wait' : 'pointer' }}
        >⊕↑</button>
        <span style={{ color: 'var(--fg-mute)', fontFamily: 'var(--mono)' }}>#{index + 1}</span>
        <span style={{ color: meta.color }}>{meta.glyph}</span>
        <select
          style={{ ...inputStyle, width: 'auto' }}
          value={state}
          disabled={busy}
          onChange={event => setState(event.target.value)}
        >
          {stateOptions.map(option => (
            <option key={option} value={option} disabled={planLocked && option !== 'pending'}>
              {option}
            </option>
          ))}
        </select>
        <span style={{ flex: 1 }} />
        <button
          className="btn"
          disabled={saveDisabled}
          title={blockedPlanState
            ? 'Plan mode keeps todos pending until approval.'
            : reasonMissing ? 'Reason is required for approved/rejected todos.' : 'Save todo changes'}
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
        <input style={inputStyle} value={content} disabled={busy} onChange={event => setContent(event.target.value)} />
      </div>
      <div>
        <div style={fieldLabel}>Detail</div>
        <textarea
          style={{ ...inputStyle, minHeight: 52, resize: 'vertical' }}
          value={detail}
          disabled={busy}
          onChange={event => setDetail(event.target.value)}
        />
      </div>
      <div>
        <div style={fieldLabel}>Criteria (one per line)</div>
        <textarea
          style={{ ...inputStyle, minHeight: 52, resize: 'vertical' }}
          value={criteria}
          disabled={busy}
          onChange={event => setCriteria(event.target.value)}
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
            onChange={event => setApprovedReason(event.target.value)}
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
            onChange={event => setRejectionReason(event.target.value)}
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
