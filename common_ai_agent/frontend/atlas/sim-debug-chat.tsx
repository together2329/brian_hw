// sim-debug-chat.tsx — the chat-feed message renderer extracted from
// sim-debug.tsx (strangler-fig split). Behavior-identical: this is the SAME
// per-entry branch (user / thought / sys / agent + agent_stream) that the
// right-rail feed's `chatFeed.map(...)` produced inline. Each message is
// purely a function of its `ChatEntry`, so it lifts out cleanly as a
// prop-driven presentational component — no root state is closed over.
//
// Load order: imported by sim-debug.tsx. Owns no window bridge.
import type { ReactNode, RefObject } from 'react';
import type { ChatEntry } from './sim-debug-root-shared';

interface ChatFeedMessageProps {
  entry: ChatEntry;
}

export const ChatFeedMessage = ({ entry }: ChatFeedMessageProps): ReactNode => {
  const m = entry;
  if (m.kind === 'user') {
    return (
      <div style={{ marginBottom: 6, color: 'var(--accent)' }}>
        <span style={{
          fontSize: 9, letterSpacing: '0.1em',
          textTransform: 'uppercase', color: 'var(--fg-mute)',
          marginRight: 6,
        }}>YOU</span>
        <span style={{ fontFamily: 'var(--mono)' }}>{m.text}</span>
      </div>
    );
  }
  if (m.kind === 'thought') {
    return (
      <div style={{
        marginBottom: 6, color: 'var(--magenta)',
        fontSize: 10, fontStyle: 'italic',
        borderLeft: '2px solid var(--magenta)',
        paddingLeft: 8, opacity: 0.8,
      }}>
        <span style={{
          fontSize: 9, letterSpacing: '0.1em',
          textTransform: 'uppercase', color: 'var(--fg-mute)',
          marginRight: 6, fontStyle: 'normal',
        }}>THOUGHT</span>
        <span style={{ whiteSpace: 'pre-wrap' }}>{m.text}</span>
      </div>
    );
  }
  if (m.kind === 'sys') {
    return (
      <div style={{ marginBottom: 6, color: 'var(--err)', fontSize: 10 }}>
        {m.text}
      </div>
    );
  }
  // agent / agent_stream
  return (
    <div style={{ marginBottom: 8, color: 'var(--fg)' }}>
      <span style={{
        fontSize: 9, letterSpacing: '0.1em',
        textTransform: 'uppercase', color: 'var(--ok)',
        marginRight: 6,
      }}>AGENT{m.kind === 'agent_stream' ? ' …' : ''}</span>
      <span style={{ whiteSpace: 'pre-wrap', fontFamily: 'var(--mono)', fontSize: 10 }}>
        {m.text}
      </span>
    </div>
  );
};

// ── The right-rail live chat panel extracted from sim-debug.tsx. Behavior-
// identical: this is the SAME `eff.showChat && (...)` subtree — header + clear
// button, focus card, scrollable feed (rendered via ChatFeedMessage), the
// signal-aware quick-prompt chips, and the prompt input. The root closure owns
// chatFeed/chatInput/chatStreaming and the refs/sendChat handler; they are
// passed in as a typed props bundle.
interface ChatRailProps {
  chatStreaming: boolean;
  setChatFeed: (entries: ChatEntry[]) => void;
  streamBufRef: { current: string };
  selectedSig: string;
  ipName: string;
  chatScrollRef: RefObject<HTMLDivElement>;
  chatFeed: ChatEntry[];
  waveCursor: number;
  sendChat: (text?: string) => void;
  chatInput: string;
  setChatInput: (v: string) => void;
}

export const ChatRail = ({
  chatStreaming, setChatFeed, streamBufRef, selectedSig, ipName,
  chatScrollRef, chatFeed, waveCursor, sendChat, chatInput, setChatInput,
}: ChatRailProps): ReactNode => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden', background: 'var(--panel)', borderLeft: '1px solid var(--line)' }}>
      <div className="mini-h" style={{ display: 'flex', alignItems: 'center' }}>
        <b>chat</b>
        <span style={{ color: 'var(--fg-mute)', marginLeft: 8, fontSize: 10 }}>trace · debug · ask</span>
        <span style={{ flex: 1 }} />
        {chatStreaming && (
          <span style={{ color: 'var(--accent)', fontSize: 10, marginRight: 6 }}>● streaming</span>
        )}
        <button
          className="btn"
          onClick={() => { setChatFeed([]); streamBufRef.current = ''; }}
          style={{ padding: '1px 6px', fontSize: 10 }}
        >clear</button>
      </div>

      {/* Focus card — selected signal / current IP */}
      <div style={{
        padding: '6px 10px',
        background: 'var(--bg-2)', borderBottom: '1px solid var(--line)',
        fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--fg-dim)',
      }}>
        focus: <span style={{ color: 'var(--accent)' }}>{selectedSig || '(click a signal)'}</span>
        {ipName && <> · ip: <span style={{ color: 'var(--cyan)' }}>{ipName}</span></>}
      </div>

      {/* Feed */}
      <div ref={chatScrollRef} style={{
        flex: 1, overflow: 'auto', padding: '8px 10px',
        fontSize: 'var(--ui-control-font-size)', lineHeight: 1.5,
      }}>
        {chatFeed.length === 0 && (
          <div style={{ color: 'var(--fg-mute)', fontSize: 10, marginBottom: 8 }}>
            Click a signal in the wave or hierarchy panel to set focus, then
            pick a quick prompt below or type a free question.
          </div>
        )}
        {chatFeed.map((m, i) => (
          <ChatFeedMessage key={i} entry={m} />
        ))}
      </div>

      {/* Quick prompts (signal-aware) */}
      <div style={{
        padding: '6px 10px', borderTop: '1px solid var(--line)',
        background: 'var(--bg-2)', fontSize: 10,
      }}>
        <div style={{ color: 'var(--fg-mute)', fontSize: 9, letterSpacing: '0.08em',
                      textTransform: 'uppercase', marginBottom: 4 }}>quick prompts</div>
        {[
          `/trace ${selectedSig || 'gpio_irq'}${ipName ? ' --ip ' + ipName : ''}`,
          `/hier ${ipName || 'gpio_pad'}`,
          selectedSig ? `Why does ${selectedSig} have unexpected values around t=${waveCursor}ns?` : `Explain the FSM in ${ipName || 'this design'}`,
        ].map((p, i) => (
          <div
            key={i}
            onClick={() => sendChat(p)}
            style={{
              fontFamily: 'var(--mono)', fontSize: 10,
              color: 'var(--fg)', padding: '3px 6px', marginBottom: 2,
              background: 'var(--bg)', border: '1px solid var(--line)',
              borderRadius: 3, cursor: 'pointer',
            }}
            title="click to send"
          >{p}</div>
        ))}
      </div>

      {/* Input */}
      <div className="prompt-row" style={{
        padding: 8, borderTop: '1px solid var(--line)',
        background: 'var(--bg)',
      }}>
        <span className="ps">›</span>
        <input
          value={chatInput}
          onChange={e => setChatInput(e.target.value)}
          onKeyDown={e => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              sendChat();
            }
          }}
          placeholder="ask the debug agent · /trace · /hier · ↵ send"
          disabled={chatStreaming}
          style={{ opacity: chatStreaming ? 0.6 : 1 }}
        />
        <span className="kbd-i">/</span>
        <span className="kbd-i">↵</span>
      </div>
    </div>
  );
};
