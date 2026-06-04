// workspace-orchestrator-chat.tsx — OrchestratorChatPanel (orchestrator-mode
// side chat).
//
// Extracted from workspace-panels.tsx (Phase 13g cluster split) to keep every
// file under 1000 lines. Shared types + the cross-file `w` cast live in
// workspace-panel-shared.tsx. Still bridges window.OrchestratorChatPanel at
// the bottom for not-yet-migrated .jsx consumers (workspace.jsx aliases it
// back).
import {
  useState,
  useEffect,
  useCallback,
  type ReactNode,
  type KeyboardEvent,
} from 'react';
import {
  w,
  type ChatRoom,
  type ChatMessage,
} from './workspace-panel-shared';
import { useStickyChatScroll } from './use-sticky-chat-scroll';

export interface OrchestratorChatPanelProps {
  activeIp?: string;
}

export const OrchestratorChatPanel = ({ activeIp: activeIpProp = '' }: OrchestratorChatPanelProps = {}) => {
  const [rooms, setRooms]       = useState<ChatRoom[]>([]);
  const [room, setRoom]         = useState('_global');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [context, setContext]   = useState<any>(null);
  const [contextOpen, setContextOpen] = useState(true);
  const [draft, setDraft]       = useState('');
  const [busy, setBusy]         = useState(false);
  const [error, setError]       = useState('');
  const {
    scrollRef: threadRef,
    onScroll: onThreadScroll,
    scrollToBottom: scrollThreadToBottom,
  } = useStickyChatScroll<HTMLDivElement>([messages.length]);

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

  const submit = async () => {
    const text = draft.trim();
    if (!text || busy) return;
    setBusy(true);
    scrollThreadToBottom();
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
           onScroll={onThreadScroll}
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

(window as unknown as { OrchestratorChatPanel: typeof OrchestratorChatPanel }).OrchestratorChatPanel = OrchestratorChatPanel;
