// workspace-subagent-lanes.tsx — left workflow-panel "Subagents" selector.
//
// Mirrors codex's `/subagent` agent picker: a numbered list with Main on top
// and each spawned subagent below (nickname [role] + thread id). Clicking a row
// selects/watches that agent; a subagent row expands its streamed transcript
// inline. Pure presentational — the workspace data hook owns the lane data and
// the selection.
import { useState, type ReactNode, type CSSProperties } from 'react';

export interface SubagentLaneItem {
  kind: string;   // spawn | message | reasoning | tool | tool_result | status | result
  text: string;
  ts: number;     // epoch ms
}
export interface SubagentLane {
  agentId: string;   // codex thread id (uuid) — the lane key
  label: string;     // "RTL Implementation [oag-rtl-implementation-agent]" / "Main"
  status: string;    // spawning | running | waiting | completed | failed | closed
  items: SubagentLaneItem[];
  isMain?: boolean;  // the parent/main agent (rendered first, "[default]")
}
export interface SubagentLanesProps {
  lanes: SubagentLane[];                  // ordered: main first, then subagents
  selectedId?: string;
  onSelect?: (agentId: string) => void;
}

const KIND_SHORT: Record<string, string> = {
  spawn: 'spawn', message: 'msg', reasoning: 'reason',
  tool: 'tool', tool_result: 'result', status: 'status', result: 'result',
};
const MAX_ITEM_TEXT = 2000;

function dotColor(status: string): string {
  if (status === 'completed') return '#22c55e';
  if (status === 'failed') return '#ef4444';
  if (status === 'closed') return 'var(--fg-mute)';
  return 'var(--accent)';   // spawning / running / waiting
}
function statusText(status: string): string {
  return (({
    spawning: 'spawning…', running: 'running', waiting: 'waiting',
    completed: 'done', failed: 'failed', closed: 'closed',
  } as Record<string, string>)[status]) || status;
}

const headerStyle: CSSProperties = {
  display: 'flex', alignItems: 'center', gap: 6, width: '100%', background: 'none',
  border: 'none', padding: '5px 8px', cursor: 'pointer', color: 'var(--fg)',
  fontSize: 11, fontWeight: 600, letterSpacing: '0.03em', textTransform: 'uppercase',
};
const countBadge: CSSProperties = {
  marginLeft: 4, background: 'var(--bg-2)', color: 'var(--fg-mute)', borderRadius: 8,
  padding: '0 5px', fontSize: 10, fontWeight: 500,
};
const subtitle: CSSProperties = {
  padding: '0 10px 4px', fontSize: 10, color: 'var(--fg-mute)', opacity: 0.8,
};
const dot: CSSProperties = {
  display: 'inline-block', width: 7, height: 7, borderRadius: '50%',
  flexShrink: 0,
};
const uuidStyle: CSSProperties = {
  fontFamily: 'monospace', fontSize: 10, color: 'var(--fg-mute)', opacity: 0.7,
  flexShrink: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis',
  whiteSpace: 'nowrap', marginLeft: 6,
};
const kindTag: CSSProperties = {
  fontSize: 9, color: 'var(--fg-mute)', background: 'var(--bg-2)', borderRadius: 3,
  padding: '1px 3px', flexShrink: 0, fontFamily: 'monospace', lineHeight: '1.4',
};
const empty: CSSProperties = { fontSize: 11, color: 'var(--fg-mute)', fontStyle: 'italic' };

function rowStyle(selected: boolean, isMain: boolean): CSSProperties {
  return {
    display: 'flex', alignItems: 'center', gap: 4, width: '100%',
    background: selected ? 'var(--bg-2)' : 'none', border: 'none',
    padding: '4px 8px',
    paddingLeft: isMain ? 8 : 24,   // indent subagents under Main
    cursor: 'pointer', textAlign: 'left',
  };
}
function labelStyle(selected: boolean): CSSProperties {
  return {
    flex: '0 1 auto', fontSize: 11, fontWeight: selected ? 600 : 500,
    color: selected ? 'var(--accent)' : 'var(--fg)', overflow: 'hidden',
    textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginLeft: 4,
  };
}

export const SubagentLanes = ({ lanes, selectedId, onSelect }: SubagentLanesProps): ReactNode => {
  const [open, setOpen] = useState(true);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  const subCount = lanes.filter((l) => !l.isMain).length;
  if (subCount === 0) return null;   // only surface once a subagent exists
  const firstSubIdx = lanes.findIndex((l) => !l.isMain);

  const toggle = (id: string) => setExpanded((p) => {
    const n = new Set(p);
    if (n.has(id)) n.delete(id); else n.add(id);
    return n;
  });
  const onRow = (lane: SubagentLane) => {
    onSelect?.(lane.agentId);
    if (!lane.isMain) toggle(lane.agentId);
  };

  return (
    <div className="box subagent-lanes-box" style={{ display: 'flex', flexDirection: 'column', minHeight: 0 }}>
      <button type="button" onClick={() => setOpen((o) => !o)} style={headerStyle}>
        <span style={{ opacity: 0.5, fontSize: 10 }}>{open ? '▾' : '▸'}</span>
        <span>Subagents</span>
        <span style={countBadge}>{subCount}</span>
      </button>

      {open && (
        <div style={{ overflowY: 'auto', minHeight: 0 }}>
          <div style={subtitle}>Select an agent to watch.</div>
          {lanes.map((lane, i) => {
            const sel = selectedId === lane.agentId;
            const isOpen = expanded.has(lane.agentId);
            const gap = !lane.isMain && i === firstSubIdx;   // one-line gap under Main
            return (
              <div key={lane.agentId} style={{ borderTop: gap ? 'none' : '1px solid var(--line)', marginTop: gap ? 7 : 0 }}>
                <button type="button" onClick={() => onRow(lane)} title={lane.agentId} style={rowStyle(sel, !!lane.isMain)}>
                  <span style={{ width: 8, flexShrink: 0, color: 'var(--accent)', fontSize: 11 }}>{sel ? '›' : ''}</span>
                  <span style={{ width: 16, flexShrink: 0, color: 'var(--fg-mute)', fontSize: 11 }}>{i + 1}.</span>
                  <span style={{ ...dot, backgroundColor: dotColor(lane.status) }} />
                  <span style={labelStyle(sel)}>
                    {lane.label || lane.agentId.slice(0, 8)}
                    {lane.isMain ? (
                      <span style={{ color: 'var(--fg-mute)', fontWeight: 400 }}>
                        {' [default]'}{sel ? ' (current)' : ''}
                      </span>
                    ) : null}
                  </span>
                  {!lane.isMain && (
                    <span style={{ fontSize: 10, color: 'var(--fg-mute)', flexShrink: 0, marginLeft: 4 }}>
                      {statusText(lane.status)}
                    </span>
                  )}
                  <span style={uuidStyle}>{lane.agentId}</span>
                </button>

                {isOpen && !lane.isMain && (
                  <div style={{ background: 'var(--panel)', padding: '3px 10px 5px 18px' }}>
                    {lane.items.length === 0 ? (
                      <span style={empty}>waiting for activity…</span>
                    ) : (
                      lane.items.map((it, idx) => {
                        const txt = it.text.length > MAX_ITEM_TEXT ? `${it.text.slice(0, MAX_ITEM_TEXT)}…` : it.text;
                        const multi = it.kind === 'reasoning' || it.kind === 'message';
                        return (
                          <div
                            key={idx}
                            style={{
                              display: 'flex', gap: 5, padding: '2px 0',
                              alignItems: multi ? 'flex-start' : 'baseline',
                              borderBottom: idx < lane.items.length - 1 ? '1px solid var(--line)' : 'none',
                            }}
                          >
                            <span style={{ ...kindTag, marginTop: multi ? 2 : 0 }}>{KIND_SHORT[it.kind] || it.kind}</span>
                            <span
                              style={{
                                flex: 1, fontSize: 11, color: 'var(--fg)', lineHeight: 1.5,
                                whiteSpace: multi ? 'pre-wrap' : 'nowrap',
                                overflow: 'hidden', textOverflow: 'ellipsis',
                                wordBreak: multi ? 'break-word' : 'normal',
                              }}
                            >
                              {txt}
                            </span>
                          </div>
                        );
                      })
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default SubagentLanes;
