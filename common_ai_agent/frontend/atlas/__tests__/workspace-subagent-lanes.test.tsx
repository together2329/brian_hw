// __tests__/workspace-subagent-lanes.test.tsx
//
// SubagentLanes is a PURE SELECTOR rendered inside the left WORKFLOW panel:
// Main (default) on top, codex /subagent threads indented below. Clicking a row
// only calls onSelect — the selected agent's transcript is rendered in the MAIN
// chat pane by the workspace hook, NOT inline here.
//
// Asserts:
//   1. null when there are no subagents (empty, or Main-only).
//   2. Main [default] on top + the subagent label are shown.
//   3. pure selector: clicking does NOT render the transcript inline.
//   4. onSelect fires with the agent id for both a subagent row and Main.

import { afterEach, describe, expect, it } from 'vitest';
import { cleanup, fireEvent, render } from '@testing-library/react';

import { SubagentLanes, type SubagentLane } from '../workspace-subagent-lanes';

afterEach(() => {
  cleanup();
});

const mainLane = (over: Partial<SubagentLane> = {}): SubagentLane => ({
  agentId: 'main-thread', label: 'Main', status: 'running', items: [], isMain: true, ...over,
});
const subLane = (over: Partial<SubagentLane> = {}): SubagentLane => ({
  agentId: 'sub-1',
  label: 'RTL Implementation [oag-rtl-implementation-agent]',
  status: 'running', items: [], isMain: false, ...over,
});

describe('SubagentLanes (selector)', () => {
  it('renders null when there are no subagents (empty or Main-only)', () => {
    expect(render(<SubagentLanes lanes={[]} />).container.firstChild).toBeNull();
    cleanup();
    expect(render(<SubagentLanes lanes={[mainLane()]} />).container.firstChild).toBeNull();
  });

  it('shows Main [default] on top and the subagent label', () => {
    const { getByRole } = render(<SubagentLanes lanes={[mainLane(), subLane()]} />);
    expect(getByRole('button', { name: /Main \[default\]/ })).toBeTruthy();
    expect(getByRole('button', { name: /RTL Implementation/ })).toBeTruthy();
  });

  it('is a pure selector — clicking does NOT render the transcript inline', () => {
    const items = [{ kind: 'message', text: 'SECRET_TRANSCRIPT_LINE', ts: 1 }];
    const { getByRole, queryByText } = render(
      <SubagentLanes lanes={[mainLane(), subLane({ items })]} />,
    );
    fireEvent.click(getByRole('button', { name: /RTL Implementation/ }));
    // transcript belongs in the MAIN chat pane, never inline in the selector.
    expect(queryByText('SECRET_TRANSCRIPT_LINE')).toBeNull();
  });

  it('calls onSelect with the agent id for a subagent row and for Main', () => {
    const picks: string[] = [];
    const { getByRole } = render(
      <SubagentLanes
        lanes={[mainLane(), subLane({ agentId: 'sub-7' })]}
        onSelect={(id) => picks.push(id)}
      />,
    );
    fireEvent.click(getByRole('button', { name: /RTL Implementation/ }));
    fireEvent.click(getByRole('button', { name: /Main \[default\]/ }));
    expect(picks).toEqual(['sub-7', 'main-thread']);
  });
});
