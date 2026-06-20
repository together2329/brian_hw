// workspace-subagent-lanes.tsx — compact agent selector rendered INSIDE the
// left WORKFLOW panel. "Main" (the default agent) sits on top; codex /subagent
// threads are listed indented below it. Clicking a row makes the MAIN chat pane
// render that agent's transcript (handled by the workspace hook) — there is no
// inline transcript here, this is a pure selector. Renders null until a subagent
// exists. Presentational only; the workspace hook owns lane data + selection.
import { type ReactNode, type CSSProperties } from 'react';

export interface SubagentLaneItem {
  kind: string;   // spawn | message | reasoning | tool | tool_result | status | result
  text: string;
  ts: number;
}
export interface SubagentLane {
  agentId: string;   // codex thread id (uuid) — lane key
  label: string;     // "RTL Implementation [oag-rtl-implementation-agent]" / "Main"
  status: string;    // spawning | running | waiting | completed | failed | closed
  items: SubagentLaneItem[];
  isMain?: boolean;
}
export interface SubagentLanesProps {
  lanes: SubagentLane[];        // ordered: main first, then subagents
  selectedId?: string;
  onSelect?: (agentId: string) => void;
}

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

const dot: CSSProperties = {
  display: 'inline-block', width: 7, height: 7, borderRadius: '50%', flexShrink: 0,
};

export const SubagentLanes = ({ lanes, selectedId, onSelect }: SubagentLanesProps): ReactNode => {
  const subCount = lanes.filter((l) => !l.isMain).length;
  if (subCount === 0) return null;   // only surface once a subagent exists
  const firstSubIdx = lanes.findIndex((l) => !l.isMain);

  return (
    <div className="subagent-lanes" style={{ borderTop: '1px solid var(--line)', paddingTop: 3 }}>
      {lanes.map((lane, i) => {
        // Main is the selected/active view when nothing else is chosen.
        const sel = selectedId === lane.agentId || (!!lane.isMain && !selectedId);
        const gap = !lane.isMain && i === firstSubIdx;   // one-line gap under Main
        return (
          <button
            key={lane.agentId}
            type="button"
            title={lane.agentId}
            onClick={() => onSelect?.(lane.agentId)}
            style={{
              display: 'flex', alignItems: 'center', gap: 6, width: '100%',
              border: 'none', cursor: 'pointer', textAlign: 'left',
              background: sel ? 'var(--bg-2)' : 'none',
              padding: '3px 8px',
              paddingLeft: lane.isMain ? 8 : 24,   // indent subagents under Main
              marginTop: gap ? 6 : 0,
              borderLeft: '2px solid ' + (sel ? 'var(--accent)' : 'transparent'),
            }}
          >
            <span style={{ width: 8, flexShrink: 0, color: 'var(--accent)', fontSize: 11 }}>{sel ? '▸' : ''}</span>
            <span style={{ ...dot, backgroundColor: dotColor(lane.status) }} />
            <span style={{
              flex: 1, minWidth: 0, fontSize: 11, fontWeight: sel ? 600 : 500,
              color: sel ? 'var(--accent)' : 'var(--fg)',
              overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
            }}>
              {lane.isMain ? 'Main' : (lane.label || lane.agentId.slice(0, 13))}
              {lane.isMain ? <span style={{ color: 'var(--fg-mute)', fontWeight: 400 }}> [default]</span> : null}
            </span>
            {!lane.isMain && (
              <span style={{ fontSize: 10, color: 'var(--fg-mute)', flexShrink: 0 }}>{statusText(lane.status)}</span>
            )}
          </button>
        );
      })}
    </div>
  );
};

export default SubagentLanes;
