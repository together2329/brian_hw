// workspace-panels.tsx — TypeScript migration of workspace-panels.jsx
// (Phase 13g refactor: 6 sidebar/panel components extracted from
// workspace.jsx as one cohesive cluster). Two of the original six panels
// (ProgressPanel/TodoPanel → progress-todo-panels.jsx in Phase 23) and one
// (AgentStatusPanel → agent-status-panel.jsx in Phase 19) have since been
// re-extracted, so this file now owns three:
//
//   1. AskUserPrompt          — chat-input ask_user prompt block
//   2. OrchestratorChatPanel  — orchestrator-mode side chat
//   3. GitPanel               — per-IP git status + commits
//
// TS migration: converted from the ambient global React + IIFE + lambda
// forward-ref pattern to a typed ES module (automatic JSX runtime). Cross-file
// window globals owned by unmigrated .jsx (window.QA_FLOWS, window.backend,
// window.dispatchEvent, and the workspace.jsx helpers) are read through a
// narrow cast since their owners are still .jsx and they are not yet declared
// in types/atlas-window.d.ts. Still bridges window.AskUserPrompt /
// window.OrchestratorChatPanel / window.GitPanel at the bottom for the
// not-yet-migrated .jsx consumers (workspace.jsx aliases these back).
//
// Load order (index.html): AFTER ssot-qa-board.jsx, BEFORE workspace.jsx.
import {
  useState,
  useEffect,
  useRef,
  useCallback,
  type ReactNode,
  type KeyboardEvent,
} from 'react';

// ── Loose data shapes flowing through these panels (kept loose where the .jsx
// was loose). ──
interface AskOption {
  id: string;
  selected?: boolean;
  locked?: boolean;
}

interface AskTabState {
  opts?: AskOption[];
  custom?: string;
}

interface AskFlowQuestion {
  kind?: string;
  multiline?: boolean;
}

interface AskFlow {
  kind?: string;
  multiline?: boolean;
  questions?: AskFlowQuestion[];
  stage?: ReactNode;
  step?: ReactNode;
  total?: ReactNode;
}

interface AskFlowState {
  batched?: boolean;
  active?: number;
  states?: AskTabState[];
  opts?: AskOption[];
  custom?: string;
}

interface ChatRoom {
  name: string;
  scope?: string;
}

interface ChatMessage {
  id: string | number;
  ip_id?: unknown;
  user_id?: unknown;
  display_name?: unknown;
  content?: unknown;
  created_at?: number;
}

interface GitFile {
  path: string;
  status?: string;
  staged?: boolean;
  unstaged?: boolean;
  added?: number | null;
  removed?: number | null;
}

interface GitCommit {
  sha: string;
  short?: string;
  subject?: string;
  author?: string;
  date?: string;
  added?: number | null;
  removed?: number | null;
  files?: number;
}

interface GitOpResult {
  kind?: string;
  ok?: boolean;
  stdout?: string;
  stderr?: string;
  error?: string;
}

interface StatusGlyphCell {
  ch: string;
  color: string;
}

interface StatusGlyph {
  staged: StatusGlyphCell;
  work: StatusGlyphCell;
}

// WS-bus payload for the 'chat_message' signal — the broadcast carries a
// `room` field (used for the active-room filter) on top of the message fields.
interface ChatMessagePayload extends ChatMessage {
  room?: string | null;
}

interface AtlasBackend {
  subscribe?: (ev: string, cb: (m: ChatMessagePayload) => void) => (() => void) | void;
}

// ── Cross-file window globals owned by unmigrated .jsx, reached via a narrow
// typed view of `window` (not yet in types/atlas-window.d.ts). ──
const w = window as unknown as {
  QA_FLOWS: Record<string, AskFlow | undefined>;
  backend?: AtlasBackend;
  AskUserQuestionBlock: (...a: any[]) => any;
  AtlasStatusBadge: (...a: unknown[]) => unknown;
  TodoGraph: (...a: unknown[]) => unknown;
  _limitAtlasLines: (...a: unknown[]) => unknown;
  _statusGlyph: (...a: unknown[]) => StatusGlyph;
  atlasStatusMeta: (...a: unknown[]) => unknown;
  atlasUiExecMode: (...a: unknown[]) => unknown;
  healthMatchesCurrentUser: (...a: unknown[]) => unknown;
  normalizeUiSession: (...a: unknown[]) => unknown;
  uiEffectiveHealthSession: (...a: unknown[]) => unknown;
  uiHealthCountersMatchBrowserRoute: (...a: unknown[]) => unknown;
  uiSessionRoute: (...a: unknown[]) => unknown;
  workspaceFetchWorkerSnapshot: (...a: unknown[]) => unknown;
  Kbd: (props: { children?: ReactNode }) => ReactNode;
};

// Forward-ref to workspace.jsx helpers (resolved at call time):
const AskUserQuestionBlock = (...a: any[]) => w.AskUserQuestionBlock(...a);
const AtlasStatusBadge = (...a: unknown[]) => w.AtlasStatusBadge(...a);
const TodoGraph = (...a: unknown[]) => w.TodoGraph(...a);
const _limitAtlasLines = (...a: unknown[]) => w._limitAtlasLines(...a);
const _statusGlyph = (...a: unknown[]) => w._statusGlyph(...a);
const atlasStatusMeta = (...a: unknown[]) => w.atlasStatusMeta(...a);
const atlasUiExecMode = (...a: unknown[]) => w.atlasUiExecMode(...a);
const healthMatchesCurrentUser = (...a: unknown[]) => w.healthMatchesCurrentUser(...a);
const normalizeUiSession = (...a: unknown[]) => w.normalizeUiSession(...a);
const uiEffectiveHealthSession = (...a: unknown[]) => w.uiEffectiveHealthSession(...a);
const uiHealthCountersMatchBrowserRoute = (...a: unknown[]) => w.uiHealthCountersMatchBrowserRoute(...a);
const uiSessionRoute = (...a: unknown[]) => w.uiSessionRoute(...a);
const workspaceFetchWorkerSnapshot = (...a: unknown[]) => w.workspaceFetchWorkerSnapshot(...a);

// Kbd is owned by shared.(jsx|tsx); reached as a cross-file global like the
// helpers above (resolved at call time so an unmigrated owner still works).
const Kbd = (props: { children?: ReactNode }) => w.Kbd(props);


interface AskUserPromptProps {
  flowId: string;
  state?: AskFlowState | null;
  sel: number;
  intent?: string;
  fullHeight?: boolean;
  onToggle: (flowId: string, optionId: string) => void;
  onCustom: (flowId: string, value: string) => void;
  onSubmit: (flowId: string) => void;
  onChat: (flowId: string) => void;
  onSel: (index: number) => void;
  onSetTab?: (flowId: string, index: number) => void;
  onAdvance?: (flowId: string) => void;
}

const AskUserPrompt = ({ flowId, state, sel, intent, fullHeight = false, onToggle, onCustom, onSubmit, onChat, onSel, onSetTab, onAdvance }: AskUserPromptProps) => {
  const flow = w.QA_FLOWS[flowId];
  if (!flow || !state) return null;

  // Batched flow virtualization — derive the "view" for the active tab
  // and reuse all the existing single-question rendering below.
  const isBatched = !!state.batched;
  const tabCount = isBatched ? (flow.questions || []).length : 0;
  const active = isBatched ? (state.active || 0) : 0;
  const isSubmitTab = isBatched && active === tabCount;
  // Active tab view (used by the option/custom widgets below)
  const tabState: AskTabState = isBatched
    ? (state.states && state.states[active]) || { opts: [], custom: '' }
    : state;
  const tabFlowKind = isBatched && !isSubmitTab ? flow.questions![active].kind : flow.kind;
  const tabFlowMultiline = !!(isBatched && !isSubmitTab ? flow.questions![active].multiline : flow.multiline);
  const tabAnswered = (i: number): boolean => {
    const ts = state.states && state.states[i];
    if (!ts) return false;
    return (ts.opts || []).some(o => o.selected) || (ts.custom || '').trim().length > 0;
  };
  const allAnswered = isBatched
    ? (state.states || []).every((_, i) => tabAnswered(i))
    : true;

  const goNextBatchedStep = (): boolean => {
    if (!isBatched) return false;
    if (isSubmitTab) {
      if (allAnswered) onSubmit(flowId);
      return true;
    }
    if (active < tabCount - 1) {
      onAdvance ? onAdvance(flowId) : onSetTab && onSetTab(flowId, active + 1);
      return true;
    }
    if (allAnswered) {
      onSubmit(flowId);
    } else {
      onSetTab && onSetTab(flowId, tabCount);
    }
    return true;
  };

  const opts = tabState.opts || [];
  const customIdx = opts.length;       // row index for custom-text line
  const submitIdx = opts.length + 1;   // Submit menu line
  const chatIdx   = opts.length + 2;   // "Chat about this" menu line
  const lastIdx   = chatIdx;

  const onKey = (e: KeyboardEvent<HTMLDivElement>) => {
    // Batched flow: ⌘/⌃ + ←/→ moves the keyboard cursor between
    // question blocks (each Q renders its own block; the active block
    // is highlighted and owns the option/custom cursor).
    if (isBatched) {
      if (e.key === 'ArrowLeft' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault(); onSetTab && onSetTab(flowId, Math.max(0, active - 1)); return;
      }
      if (e.key === 'ArrowRight' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault(); onSetTab && onSetTab(flowId, Math.min(tabCount - 1, active + 1)); return;
      }
    }
    if (e.key === 'ArrowDown' || (e.key === 'j' && !e.metaKey && !e.ctrlKey && document.activeElement?.tagName !== 'INPUT')) {
      e.preventDefault(); onSel(Math.min(sel + 1, lastIdx)); return;
    }
    if (e.key === 'ArrowUp' || (e.key === 'k' && !e.metaKey && !e.ctrlKey && document.activeElement?.tagName !== 'INPUT')) {
      e.preventDefault(); onSel(Math.max(sel - 1, 0)); return;
    }
    if (e.key === ' ' && sel < opts.length) {
      // When focus is in the custom-answer input/textarea, space must
      // pass through to the field. Without this guard the parent
      // div's keydown intercepts and toggles the selected option
      // instead, swallowing every space the user types.
      const ae = document.activeElement;
      const aeTag = ae && ae.tagName;
      if (aeTag === 'INPUT' || aeTag === 'TEXTAREA' || (ae && (ae as HTMLElement).isContentEditable)) return;
      e.preventDefault(); onToggle(flowId, opts[sel].id); return;
    }
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
      const activeEl = document.activeElement;
      const isCustomInput = activeEl && activeEl.classList && activeEl.classList.contains('askcustom');
      if (isCustomInput && tabFlowMultiline && !e.metaKey && !e.ctrlKey) return;
      e.preventDefault();
      // Custom-input Enter: in batched, advance to next question (or
      // submit-all on the last); in single, submit immediately when the
      // text isn't empty so a one-shot QA can be answered with Enter.
      if (isCustomInput) {
        if (isBatched) { goNextBatchedStep(); return; }
        if ((tabState.custom || '').trim() || opts.some(o => o.selected)) {
          onSubmit(flowId);
        }
        return;
      }
      if (sel < opts.length) {
        onToggle(flowId, opts[sel].id);
        // Batched + single-kind: advance to next question (or submit
        // when on the last one and everything else is answered).
        if (isBatched && tabFlowKind !== 'multi') { goNextBatchedStep(); return; }
        // Non-batched + single-kind (one-question flow): Enter
        // immediately submits — the user just picked their answer.
        if (!isBatched && tabFlowKind === 'single') { onSubmit(flowId); return; }
        return;
      }
      if (sel === customIdx) {
        if (isBatched && (tabState.custom || '').trim()) { goNextBatchedStep(); return; }
        const el = e.currentTarget.querySelector('input.askcustom, textarea.askcustom') as HTMLElement | null; el?.focus(); return;
      }
      if (sel === submitIdx) {
        if (isBatched) { if (allAnswered) onSubmit(flowId); return; }
        onSubmit(flowId);
        return;
      }
      if (sel === chatIdx)   { onChat(flowId); return; }
    }
    if (e.key === 'Escape') { e.preventDefault(); onSel(0); }
  };

  const renderQuestionBlock = (i: number, block: AskFlow | AskFlowQuestion, bs: AskTabState, kind: string | undefined) => (
    <AskUserQuestionBlock
      key={i}
      index={i}
      block={block}
      blockState={bs}
      kind={kind}
      isBatched={isBatched}
      isActive={!isBatched || i === active}
      answered={tabAnswered(i)}
      selectedIndex={sel}
      onEnsureActive={(idx: number) => {
        if (isBatched && idx !== active && onSetTab) onSetTab(flowId, idx);
      }}
      onSelectIndex={onSel}
      onToggleOption={(optionId: string) => onToggle(flowId, optionId)}
      onCustom={(value: string) => onCustom(flowId, value)}
      onSelectAll={(blockOpts: AskOption[]) => {
        blockOpts.forEach(o => { if (!o.selected && !o.locked) onToggle(flowId, o.id); });
      }}
      onClearAll={(blockOpts: AskOption[]) => {
        blockOpts.forEach(o => { if (o.selected && !o.locked) onToggle(flowId, o.id); });
      }}
    />
  );

  return (
    <div
      className="ask-prompt fade-in"
      tabIndex={0}
      onKeyDown={onKey}
      style={{
        border: `1px solid var(--accent)`,
        borderLeftWidth: 3,
        background: 'var(--bg-2)',
        padding: '10px 14px 8px',
        outline: 'none',
        boxShadow: '0 -2px 0 0 color-mix(in oklch, var(--accent) 25%, transparent)',
        height: fullHeight ? '100%' : undefined,
        minHeight: fullHeight ? 0 : undefined,
        overflow: fullHeight ? 'auto' : undefined,
      }}
    >
      {/* header — mimics the screenshot: "▸ ask_user · ✓ Submit" */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8,
        fontSize: 'var(--ui-control-font-size)', letterSpacing: '0.06em', textTransform: 'uppercase',
      }}>
        <span className="acc" style={{ fontWeight: 700 }}>▸ ask_user</span>
        <span className="mute">·</span>
        <span className="ok" style={{ fontWeight: 600, opacity: sel === submitIdx ? 1 : 0.6 }}>✓ Submit</span>
        <span className="mute">·</span>
        <span className="mute">{flow.stage} · step {flow.step}/{flow.total}</span>
        <span style={{ flex: 1 }} />
        {intent === 'plan' && (
          <span className="warn" style={{ fontSize: 10, fontWeight: 700 }}>◐ plan mode · still asks</span>
        )}
        <span className="mute" style={{ textTransform: 'none', letterSpacing: 0, fontSize: 10 }}>
          {tabFlowKind === 'multi' ? 'multi-select' : tabFlowKind === 'input' ? 'text' : 'single-select'}
        </span>
        {isBatched && (
          <span
            className={allAnswered ? 'ok' : 'mute'}
            style={{ textTransform: 'none', letterSpacing: 0, fontSize: 10, marginLeft: 6, fontWeight: 600 }}
          >
            · {(state.states || []).filter((_, i) => tabAnswered(i)).length}/{tabCount} answered
          </span>
        )}
      </div>

      {/* questions — single block when not batched, stacked blocks when batched */}
      {isBatched
        ? (flow.questions || []).map((q, i) => {
            const ts = (state.states || [])[i] || { opts: [], custom: '' };
            const k = q.kind === 'multi' ? 'multi' : q.kind === 'input' ? 'input' : 'single';
            return renderQuestionBlock(i, q, ts, k);
          })
        : renderQuestionBlock(0, flow, state, tabFlowKind)}

      {/* submit row — for batched, gates on allAnswered and submits all */}
      <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 0 }}>
        <div
          onClick={() => {
            if (isBatched) { if (allAnswered) onSubmit(flowId); }
            else onSubmit(flowId);
          }}
          style={{
            padding: '4px 8px',
            background: sel === submitIdx ? 'color-mix(in oklch, var(--ok) 18%, transparent)' : 'transparent',
            borderLeft: `2px solid ${sel === submitIdx ? 'var(--ok)' : 'transparent'}`,
            cursor: (isBatched && !allAnswered) ? 'not-allowed' : 'pointer',
            fontFamily: 'var(--mono)', fontSize: 13,
            color: sel === submitIdx ? 'var(--ok)' : 'var(--fg)',
            fontWeight: sel === submitIdx ? 600 : 400,
            opacity: (isBatched && !allAnswered) ? 0.6 : 1,
          }}
        >
          <span className="mute" style={{ marginRight: 6 }}>›</span>
          {isBatched ? `Submit all (${(state.states || []).filter((_, i) => tabAnswered(i)).length}/${tabCount})` : 'Submit'}
          {!isBatched && (
            <span className="mute" style={{ marginLeft: 8, fontSize: 11 }}>
              ({(opts.filter(o => o.selected) || []).length}{tabState.custom ? '+1' : ''} reply)
            </span>
          )}
        </div>
        <div
          onClick={() => { onSel(chatIdx); onChat(flowId); }}
          style={{
            padding: '4px 8px',
            background: sel === chatIdx ? 'color-mix(in oklch, var(--accent) 14%, transparent)' : 'transparent',
            borderLeft: `2px solid ${sel === chatIdx ? 'var(--accent)' : 'transparent'}`,
            cursor: 'pointer',
            fontFamily: 'var(--mono)', fontSize: 13,
          }}
        >
          <span className="mute" style={{ marginRight: 6 }}>›</span>Chat about this
          <span className="mute" style={{ marginLeft: 8, fontSize: 11 }}>(send a free-form message instead)</span>
        </div>
      </div>

      {/* hint footer — terminal-style */}
      <div className="mute" style={{
        marginTop: 8, paddingTop: 6, borderTop: '1px dashed var(--line)',
        fontSize: 'var(--ui-control-font-size)', display: 'flex', gap: 14, flexWrap: 'wrap',
      }}>
        <span><Kbd>↵</Kbd> {isBatched ? 'select & next' : 'select & submit'}</span>
        <span><Kbd>↑↓</Kbd>/<Kbd>j k</Kbd> navigate</span>
        <span><Kbd>Space</Kbd> toggle</span>
        <span><Kbd>Tab</Kbd> next field</span>
        {isBatched && <span><Kbd>⌘/⌃ ←→</Kbd> switch question</span>}
        <span><Kbd>Esc</Kbd> top</span>
      </div>
    </div>
  );
};




interface OrchestratorChatPanelProps {
  activeIp?: string;
}

const OrchestratorChatPanel = ({ activeIp: activeIpProp = '' }: OrchestratorChatPanelProps = {}) => {
  const [rooms, setRooms]       = useState<ChatRoom[]>([]);
  const [room, setRoom]         = useState('_global');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [context, setContext]   = useState<any>(null);
  const [contextOpen, setContextOpen] = useState(true);
  const [draft, setDraft]       = useState('');
  const [busy, setBusy]         = useState(false);
  const [error, setError]       = useState('');
  const threadRef               = useRef<HTMLDivElement>(null);

  const fetchRooms = useCallback(async () => {
    try {
      const r = await fetch('/api/chat/rooms', { credentials: 'include' });
      if (!r.ok) { setError(`rooms: ${r.status}`); return; }
      const data = await r.json();
      setRooms(data.rooms || []);
    } catch (e) { setError(String(e)); }
  }, []);

  const fetchMessages = useCallback(async (rm: string) => {
    try {
      const r = await fetch(`/api/chat/${encodeURIComponent(rm)}/messages?limit=100`,
                            { credentials: 'include' });
      if (!r.ok) { setError(`messages: ${r.status}`); setMessages([]); return; }
      const data = await r.json();
      // API returns newest-first; reverse for chronological render.
      setMessages((data.messages || []).slice().reverse());
      setError('');
    } catch (e) { setError(String(e)); }
  }, []);

  const fetchContext = useCallback(async (rm: string) => {
    try {
      const r = await fetch(`/api/chat/${encodeURIComponent(rm)}/context`,
                            { credentials: 'include' });
      if (!r.ok) { setContext(null); return; }
      setContext(await r.json());
    } catch (_) { setContext(null); }
  }, []);

  // Initial + room-change loads.
  useEffect(() => { fetchRooms(); }, [fetchRooms]);
  useEffect(() => {
    fetchMessages(room);
    fetchContext(room);
  }, [room, fetchMessages, fetchContext]);

  // Default room: prefer the workspace's active IP, fall back to _global.
  useEffect(() => {
    if (!rooms.length) return;
    const names = new Set(rooms.map((r) => r.name));
    if (activeIpProp && names.has(activeIpProp)) { setRoom(activeIpProp); return; }
    if (names.has(room)) return;
    setRoom(names.has('_global') ? '_global' : rooms[0].name);
  }, [rooms, activeIpProp, room]);

  // Live updates over the existing WS bus.
  useEffect(() => {
    if (!w.backend || typeof w.backend.subscribe !== 'function') {
      return undefined;
    }
    const off = w.backend.subscribe('chat_message', (m) => {
      if (!m || m.room == null) return;
      if (m.room !== room) {
        // Could bump unread badge here; left to a follow-up.
        return;
      }
      setMessages((prev) => {
        // Dedup by id — broadcast_all fans out to every session, so the
        // sender's own client may see its own POST echo.
        if (prev.some((x) => x.id === m.id)) return prev;
        return prev.concat([{
          id: m.id,
          ip_id: m.ip_id,
          user_id: m.user_id,
          display_name: m.display_name,
          content: m.content,
          created_at: m.created_at,
        }]);
      });
    });
    return off;
  }, [room]);

  // Auto-scroll thread on new message.
  useEffect(() => {
    const el = threadRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages]);

  const submit = async () => {
    const text = draft.trim();
    if (!text || busy) return;
    setBusy(true);
    try {
      const r = await fetch(`/api/chat/${encodeURIComponent(room)}/send`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: text }),
      });
      if (!r.ok) {
        const body = await r.json().catch(() => ({}));
        setError(body.error || `POST ${r.status}`);
      } else {
        setDraft('');
        setError('');
      }
    } catch (e) { setError(String(e)); }
    finally { setBusy(false); }
  };

  const onKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit(); }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minHeight: 0,
                  padding: '8px 10px', gap: 8 }}>
      {/* Room switcher */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <span style={{ fontSize: 'var(--ui-control-font-size)', color: 'var(--fg-mute)' }}>Room:</span>
        <select
          value={room}
          onChange={(e) => setRoom(e.target.value)}
          style={{ flex: 1, fontSize: 12, padding: '2px 4px',
                   background: 'var(--bg-soft)', color: 'var(--fg)',
                   border: '1px solid var(--border)' }}>
          {rooms.length === 0 && <option value="">(no accessible rooms)</option>}
          {rooms.map((r) => (
            <option key={r.name} value={r.name}>
              {r.scope === 'global' ? 'all IPs (_global)' : r.name}
            </option>
          ))}
        </select>
        <button onClick={() => { fetchRooms(); fetchContext(room); fetchMessages(room); }}
                title="refresh"
                style={{ fontSize: 'var(--ui-control-font-size)', padding: '2px 6px' }}>⟳</button>
      </div>

      {/* Context card */}
      {context && (
        <div className="orchestrator-card"
             style={{ border: '1px solid var(--border)', borderRadius: 4,
                      padding: 6, fontSize: 'var(--ui-control-font-size)', background: 'var(--bg-soft)' }}>
          <div onClick={() => setContextOpen((v) => !v)}
               style={{ cursor: 'pointer', display: 'flex', justifyContent: 'space-between' }}>
            <strong>Orchestrator · {room}</strong>
            <span style={{ color: 'var(--fg-mute)' }}>{contextOpen ? '▾' : '▸'}</span>
          </div>
          {contextOpen && (
            <div style={{ marginTop: 6, lineHeight: 1.4 }}>
              {room === '_global' ? (
                <div>
                  <div style={{ color: 'var(--fg-mute)' }}>IPs in workspace:</div>
                  {(context.ips || []).map((ip: any) => (
                    <div key={ip.id || ip.name} style={{ marginLeft: 6 }}>
                      <code>{ip.name}</code>
                      {' · '}
                      <span>{ip.latest_workflow || '—'}/{ip.run_status || '—'}</span>
                      {' · open='}{ip.open_blockers}
                      {' · done='}{ip.completed}
                    </div>
                  ))}
                </div>
              ) : (
                <div>
                  <div>
                    <code>{(context.ip || {}).name}</code>
                    {' · '}
                    <span style={{ color: 'var(--fg-mute)' }}>
                      {(context.workflow || {}).latest_run
                        ? `${context.workflow.latest_run.workflow}/${context.workflow.latest_run.status}`
                        : 'no run yet'}
                    </span>
                  </div>
                  {(context.todos && context.todos.counts) && (
                    <div style={{ marginTop: 4 }}>
                      <span style={{ color: 'var(--fg-mute)' }}>todos:</span>{' '}
                      {Object.entries(context.todos.counts).map(([k, v]) => (
                        <span key={k} style={{ marginRight: 6 }}>{k}={v as ReactNode}</span>
                      ))}
                    </div>
                  )}
                  {(context.todos && context.todos.top_blockers || []).slice(0, 3).map((b: any) => (
                    <div key={b.id} style={{ marginLeft: 6, color: 'var(--warn)' }}>
                      blocker[{b.status}]: {b.title}
                    </div>
                  ))}
                  {(context.recent_events || []).slice(0, 4).map((e: any, i: number) => (
                    <div key={i} style={{ marginLeft: 6, color: 'var(--fg-mute)' }}>
                      {e.kind === 'llm'
                        ? `llm · ${e.model} · $${(e.cost_usd || 0).toFixed(3)}`
                        : `· ${e.event_type || e.kind}`}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Message thread */}
      <div ref={threadRef}
           style={{ flex: 1, minHeight: 100, overflowY: 'auto',
                    border: '1px solid var(--border)', borderRadius: 4,
                    padding: 6, fontSize: 12, background: 'var(--bg-soft)' }}>
        {messages.length === 0 ? (
          <div style={{ color: 'var(--fg-mute)', fontStyle: 'italic' }}>
            No messages in this room yet. Posts are sent to the running agent on its next iteration.
          </div>
        ) : (
          messages.map((m) => {
            // Agent messages are identified by the 🤖 prefix in display_name
            // set by core/chat_responder.py. Same author would never start a
            // human message with that emoji (auth flow rejects display names
            // containing 🤖 — see record_chat_message). Visual cue: left-rail
            // accent + slightly different background so the thread reads as
            // a real conversation.
            const isAgent = typeof m.display_name === 'string'
              && m.display_name.startsWith('🤖');
            return (
              <div
                key={m.id}
                className={isAgent ? 'chat-bubble chat-bubble-agent' : 'chat-bubble'}
                style={{
                  marginBottom: 6,
                  padding: '4px 6px',
                  borderRadius: 4,
                  background: isAgent ? 'var(--bg-elevated, var(--bg))' : 'var(--bg)',
                  borderLeft: isAgent ? '3px solid var(--accent, #4a9eff)' : 'none',
                }}>
                <div style={{ display: 'flex', justifyContent: 'space-between',
                              fontSize: 10,
                              color: isAgent ? 'var(--accent, #4a9eff)' : 'var(--fg-mute)' }}>
                  <strong>{(m.display_name as ReactNode) || (m.user_id as ReactNode) || 'user'}</strong>
                  <span>{m.created_at ? new Date(m.created_at * 1000).toLocaleTimeString() : ''}</span>
                </div>
                <div style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                  {m.content as ReactNode}
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Composer */}
      <div style={{ display: 'flex', gap: 4 }}>
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={onKey}
          rows={2}
          placeholder={
            rooms.length === 0
              ? 'No rooms available'
              : `Type feedback for ${room}…  (Enter to send, Shift+Enter newline)`
          }
          disabled={rooms.length === 0 || busy}
          style={{ flex: 1, fontSize: 12, padding: '4px 6px', resize: 'vertical',
                   background: 'var(--bg-soft)', color: 'var(--fg)',
                   border: '1px solid var(--border)' }}/>
        <button onClick={submit} disabled={busy || !draft.trim() || rooms.length === 0}
                style={{ fontSize: 12, padding: '4px 10px' }}>
          {busy ? '…' : 'Send'}
        </button>
      </div>

      {error && (
        <div style={{ fontSize: 10, color: 'var(--err)' }}>{error}</div>
      )}
    </div>
  );
};


interface GitPanelProps {
  activeIp?: string;
}

const GitPanel = ({ activeIp: activeIpProp = '' }: GitPanelProps = {}) => {
  const [branch, setBranch] = useState('');
  const [ahead, setAhead]   = useState(0);
  const [behind, setBehind] = useState(0);
  const [files, setFiles]   = useState<GitFile[]>([]);
  const [commits, setCommits] = useState<GitCommit[]>([]);
  const [error, setError]   = useState('');
  const [selected, setSelected] = useState<string | null>(null);
  const [diff, setDiff]     = useState('');
  const [diffLoading, setDiffLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [busy, setBusy]     = useState('');   // '' | 'commit' | 'push'
  const [lastResult, setLastResult] = useState<GitOpResult | null>(null);

  const [activeIp, setActiveIp] = useState(activeIpProp || '');

  useEffect(() => {
    setActiveIp(activeIpProp || '');
    setSelected(null);
    setDiff('');
  }, [activeIpProp]);

  const refresh = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (activeIp) params.set('ip', activeIp);
      const qs = params.toString();
      const r = await fetch('/api/git/status' + (qs ? `?${qs}` : ''));
      const d = await r.json();
      setBranch(d.branch || ''); setAhead(d.ahead || 0); setBehind(d.behind || 0);
      setFiles(d.files || []); setError(d.error || '');
    } catch (e) { setError(String(e)); }
    try {
      const params = new URLSearchParams({ limit: '80' });
      if (activeIp) params.set('ip', activeIp);
      const r = await fetch('/api/git/log?' + params.toString());
      const d = await r.json();
      setCommits(Array.isArray(d.commits) ? d.commits : []);
    } catch (_) {}
  }, [activeIp]);

  useEffect(() => { refresh(); const id = setInterval(refresh, 5000); return () => clearInterval(id); }, [refresh]);

  // When user clicks a file, fetch its diff (cached as `selected`)
  useEffect(() => {
    if (!selected) { setDiff(''); return; }
    let cancelled = false;
    setDiffLoading(true);
    const params = new URLSearchParams({ path: selected });
    if (activeIp) params.set('ip', activeIp);
    fetch('/api/git/diff?' + params.toString())
      .then(r => r.json())
      .then(d => { if (!cancelled) { setDiff(d.diff || d.error || ''); setDiffLoading(false); } })
      .catch(e => { if (!cancelled) { setDiff(String(e)); setDiffLoading(false); } });
    return () => { cancelled = true; };
  }, [selected, files.length, activeIp]);

  const doCommit = async () => {
    if (!message.trim()) { alert('Commit message required.'); return; }
    setBusy('commit');
    try {
      const r = await fetch('/api/git/commit', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, add_all: true, ip: activeIp }),
      });
      const d = await r.json();
      setLastResult({ kind: 'commit', ...d });
      if (d.ok) setMessage('');
      refresh();
    } finally { setBusy(''); }
  };

  const doPush = async () => {
    if (!confirm('Push branch "' + (branch || '?') + '" to origin?')) return;
    setBusy('push');
    try {
      const r = await fetch('/api/git/push', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ip: activeIp }),
      });
      const d = await r.json();
      setLastResult({ kind: 'push', ...d });
      refresh();
    } finally { setBusy(''); }
  };

  const stagedCount   = files.filter(f => f.staged).length;
  const unstagedCount = files.filter(f => f.unstaged).length;

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0, fontSize: 12 }}>
      {/* Branch / ahead-behind / refresh */}
      <div style={{
        padding: '6px 10px', borderBottom: '1px solid var(--line)',
        display: 'flex', alignItems: 'center', gap: 8, fontFamily: 'var(--mono)',
      }}>
        <span className="mute" style={{ fontSize: 10 }}>branch</span>
        <span className="acc" style={{ fontWeight: 600 }}>{branch || '(none)'}</span>
        {ahead  > 0 && <span className="ok"  style={{ fontSize: 10 }}>↑{ahead}</span>}
        {behind > 0 && <span className="warn" style={{ fontSize: 10 }}>↓{behind}</span>}
        <span style={{ flex: 1 }} />
        <span onClick={refresh} title="refresh git status"
              style={{ cursor: 'pointer', color: 'var(--accent)', fontSize: 13, padding: '0 6px' }}>↻</span>
      </div>

      {/* Commit history — clickable; emits atlas-git-show so the
          center pane can render the unified diff for the chosen
          commit (matches "branch / changes / commit msg + click =
          show diff in center" UX request). */}
      {commits.length ? (
        <div style={{
          borderBottom: '1px solid var(--line)',
          maxHeight: 220,
          overflow: 'auto',
          background: 'var(--bg-2)',
        }}>
          <div className="mute" style={{
            padding: '4px 10px', fontSize: 10,
            textTransform: 'uppercase', letterSpacing: '0.08em',
            borderBottom: '1px solid var(--line)',
          }}>history · {commits.length}</div>
          {commits.map(c => (
            <div
              key={c.sha}
              onClick={() => {
                window.dispatchEvent(new CustomEvent('atlas-git-show', {
                  detail: { sha: c.sha, ip: activeIp, subject: c.subject },
                }));
              }}
              title={`${c.short} · ${c.author} · ${c.date}\n${c.subject}\n+${c.added || 0} −${c.removed || 0} across ${c.files || 0} file(s)`}
              style={{
                display: 'grid',
                gridTemplateColumns: 'auto 1fr auto',
                gap: 6,
                padding: '3px 10px',
                cursor: 'pointer',
                fontFamily: 'var(--mono)',
                fontSize: 'var(--ui-control-font-size)',
                borderLeft: '2px solid transparent',
              }}
              onMouseEnter={e => e.currentTarget.style.background = 'var(--bg-3)'}
              onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
            >
              <span style={{ color: 'var(--accent)', fontWeight: 600 }}>{c.short}</span>
              <span className="trunc" style={{ color: 'var(--fg)' }}>{c.subject}</span>
              <span style={{ fontSize: 10, color: 'var(--fg-mute)' }}>
                {c.added != null && <span className="ok"  style={{ marginRight: 2 }}>+{c.added}</span>}
                {c.removed != null && <span className="err">−{c.removed}</span>}
              </span>
            </div>
          ))}
        </div>
      ) : null}

      {/* File list */}
      <div style={{ borderBottom: '1px solid var(--line)', maxHeight: 200, overflow: 'auto' }}>
        {error && <div className="warn" style={{ padding: '8px 10px', fontSize: 11 }}>{error}</div>}
        {!error && files.length === 0 && (
          <div className="mute" style={{ padding: '10px', fontSize: 11 }}>
            (working tree clean)
          </div>
        )}
        {files.map((f, i) => {
          const sg = _statusGlyph(f.status || '  ');
          const isSel = selected === f.path;
          return (
            <div key={i}
              onClick={() => setSelected(f.path)}
              title={f.path + ' · ' + (f.status || '')}
              style={{
                display: 'grid', gridTemplateColumns: '20px 1fr auto', gap: 6,
                padding: '3px 10px', cursor: 'pointer', fontFamily: 'var(--mono)',
                background: isSel ? 'color-mix(in oklch, var(--accent) 14%, transparent)' : 'transparent',
                borderLeft: isSel ? '2px solid var(--accent)' : '2px solid transparent',
              }}>
              <span style={{ color: sg.staged.color, fontWeight: 700 }}>{sg.staged.ch}{sg.work.ch}</span>
              <span className="trunc" style={{ color: 'var(--fg)' }}>{f.path}</span>
              <span style={{ fontSize: 10 }}>
                {f.added != null && <span className="ok"  style={{ marginRight: 2 }}>+{f.added}</span>}
                {f.removed != null && <span className="err">−{f.removed}</span>}
              </span>
            </div>
          );
        })}
      </div>

      {/* Diff viewer for selected file */}
      <div style={{ flex: 1, overflow: 'auto', borderBottom: '1px solid var(--line)' }}>
        {!selected && (
          <div className="mute" style={{ padding: '10px', fontSize: 11 }}>
            Click a file above to view its diff.
          </div>
        )}
        {selected && (
          <pre className="code" style={{
            margin: 0, padding: '8px 10px', fontSize: 'var(--ui-control-font-size)', lineHeight: 1.5,
            whiteSpace: 'pre', fontFamily: 'var(--mono)',
          }}>
            {diffLoading ? 'loading…' :
              (diff || '').split('\n').map((line, i) => {
                let color = 'var(--fg)';
                let bg = 'transparent';
                if (line.startsWith('+++') || line.startsWith('---') || line.startsWith('diff ') || line.startsWith('@@') || line.startsWith('index ')) {
                  color = 'var(--accent)';
                } else if (line.startsWith('+')) {
                  color = '#7ee787'; bg = 'color-mix(in oklch, #3fb950 12%, transparent)';
                } else if (line.startsWith('-')) {
                  color = '#ffa198'; bg = 'color-mix(in oklch, #f85149 12%, transparent)';
                }
                return <div key={i} style={{ color, background: bg }}>{line || ' '}</div>;
              })
            }
          </pre>
        )}
      </div>

      {/* Commit composer */}
      <div style={{ padding: '8px 10px', display: 'flex', flexDirection: 'column', gap: 6 }}>
        <div className="mute" style={{ fontSize: 10, letterSpacing: '0.06em', textTransform: 'uppercase' }}>
          {files.length} change{files.length === 1 ? '' : 's'}
          {stagedCount   > 0 && <span className="ok"   style={{ marginLeft: 6 }}>{stagedCount} staged</span>}
          {unstagedCount > 0 && <span className="warn" style={{ marginLeft: 6 }}>{unstagedCount} unstaged</span>}
        </div>
        <textarea
          value={message}
          onChange={e => setMessage(e.target.value)}
          placeholder="Commit message — first line = summary, blank line + body for details"
          rows={3}
          style={{
            background: 'var(--bg-3)', border: '1px solid var(--line)',
            borderRadius: 2, padding: '6px 8px', fontSize: 12,
            fontFamily: 'var(--mono)', color: 'var(--fg)', resize: 'vertical',
            outline: 'none', minHeight: 50,
          }}
        />
        <div style={{ display: 'flex', gap: 6 }}>
          <button
            className="btn primary"
            disabled={busy !== '' || !message.trim() || files.length === 0}
            onClick={doCommit}
            style={{ flex: 1 }}>
            {busy === 'commit' ? 'committing…' : 'commit ↵'}
          </button>
          <button
            className="btn"
            disabled={busy !== '' || !branch}
            onClick={doPush}>
            {busy === 'push' ? 'pushing…' : ('push ↑' + (ahead ? ahead : ''))}
          </button>
        </div>
        {lastResult && (
          <div style={{
            fontSize: 10, padding: '4px 6px', borderRadius: 2,
            background: lastResult.ok ? 'color-mix(in oklch, var(--ok) 12%, transparent)'
                                       : 'color-mix(in oklch, var(--warn) 12%, transparent)',
            color: lastResult.ok ? 'var(--ok)' : 'var(--warn)',
            fontFamily: 'var(--mono)', whiteSpace: 'pre-wrap', wordBreak: 'break-word',
            maxHeight: 80, overflow: 'auto',
          }}>
            <b>{lastResult.kind}{lastResult.ok ? ' ✓' : ' ✗'}</b>
            {lastResult.stdout && '\n' + lastResult.stdout.trim()}
            {lastResult.stderr && '\n' + lastResult.stderr.trim()}
            {lastResult.error && '\n' + lastResult.error}
          </div>
        )}
      </div>
    </div>
  );
};


// Phase 13g window exports — workspace.jsx aliases these back.
// Not yet in types/atlas-window.d.ts, so the assignments go through a narrow
// cast (the owners' consumers are still .jsx).
// ProgressPanel/TodoPanel extracted to progress-todo-panels.jsx in Phase 23.
// ProgressPanel/TodoPanel extracted to progress-todo-panels.jsx in Phase 23.
// AgentStatusPanel extracted to agent-status-panel.jsx in Phase 19.
export { AskUserPrompt, OrchestratorChatPanel, GitPanel };

(window as unknown as { AskUserPrompt: typeof AskUserPrompt }).AskUserPrompt = AskUserPrompt;
(window as unknown as { OrchestratorChatPanel: typeof OrchestratorChatPanel }).OrchestratorChatPanel = OrchestratorChatPanel;
(window as unknown as { GitPanel: typeof GitPanel }).GitPanel = GitPanel;
