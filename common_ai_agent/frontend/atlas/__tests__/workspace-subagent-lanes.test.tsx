// __tests__/workspace-subagent-lanes.test.tsx
//
// Behavioral gate for SubagentLanes: pure presentational component that renders
// subagent lane status in the left workflow panel.
//
// Asserts:
//   1. Renders nothing (null) when lanes=[].
//   2. With two lanes, both labels and the "Subagents" title + count badge appear.
//   3. Clicking a lane row expands it and reveals that lane's item text.

import { afterEach, describe, expect, it } from 'vitest';
import { cleanup, fireEvent, render } from '@testing-library/react';

import {
  SubagentLanes,
  type SubagentLane,
} from '../workspace-subagent-lanes';

afterEach(() => {
  cleanup();
});

describe('SubagentLanes', () => {
  it('renders nothing when lanes is empty', () => {
    const { container } = render(<SubagentLanes lanes={[]} />);
    // The component returns null — nothing should be in the container.
    expect(container.firstChild).toBeNull();
  });

  it('shows the Subagents title, count badge, and both lane labels with two lanes', () => {
    const lanes: SubagentLane[] = [
      {
        agentId: 'agent-1',
        label: 'Lint Worker',
        status: 'running',
        items: [],
      },
      {
        agentId: 'agent-2',
        label: 'RTL Gen Worker',
        status: 'completed',
        items: [],
      },
    ];

    const { getByText } = render(<SubagentLanes lanes={lanes} />);

    // Section title
    expect(getByText('Subagents')).toBeTruthy();
    // Count badge — two lanes
    expect(getByText('2')).toBeTruthy();
    // Both lane labels
    expect(getByText('Lint Worker')).toBeTruthy();
    expect(getByText('RTL Gen Worker')).toBeTruthy();
  });

  it('clicking a lane row reveals its item text (expand toggle)', () => {
    const lanes: SubagentLane[] = [
      {
        agentId: 'agent-a',
        label: 'Planner',
        status: 'running',
        items: [
          { kind: 'reasoning', text: 'Thinking about the plan…', ts: 1000 },
          { kind: 'tool', text: 'run_linter(target="rtl")', ts: 2000 },
        ],
      },
    ];

    const { getByText, queryByText } = render(<SubagentLanes lanes={lanes} />);

    // Items should not be visible before expansion.
    expect(queryByText('Thinking about the plan…')).toBeNull();
    expect(queryByText('run_linter(target="rtl")')).toBeNull();

    // Click the lane row button (identified by the label text inside it).
    fireEvent.click(getByText('Planner'));

    // Both items now visible.
    expect(queryByText('Thinking about the plan…')).toBeTruthy();
    expect(queryByText('run_linter(target="rtl")')).toBeTruthy();
  });

  it('renders null when only the Main lane is present (no subagents yet)', () => {
    const lanes: SubagentLane[] = [
      { agentId: 'main-thread', label: 'Main', status: 'running', items: [], isMain: true },
    ];
    const { container } = render(<SubagentLanes lanes={lanes} />);
    expect(container.firstChild).toBeNull();
  });

  it('puts Main on top with [default], shows thread ids, and counts subagents only', () => {
    const lanes: SubagentLane[] = [
      { agentId: 'main-thread', label: 'Main', status: 'running', items: [], isMain: true },
      {
        agentId: '019ee3e9-fbb5-79e3',
        label: 'RTL Implementation [oag-rtl-implementation-agent]',
        status: 'running',
        items: [],
        isMain: false,
      },
    ];
    const { getByText } = render(<SubagentLanes lanes={lanes} />);
    // Main row marked as the default agent.
    expect(getByText(/\[default\]/)).toBeTruthy();
    // Subagent label and its thread id are both shown.
    expect(getByText('RTL Implementation [oag-rtl-implementation-agent]')).toBeTruthy();
    expect(getByText('019ee3e9-fbb5-79e3')).toBeTruthy();
    // Count badge reflects subagents only (1), not the Main row.
    expect(getByText('1')).toBeTruthy();
  });

  it('calls onSelect with the agent id when a row is clicked', () => {
    const picked: string[] = [];
    const lanes: SubagentLane[] = [
      { agentId: 'main-thread', label: 'Main', status: 'running', items: [], isMain: true },
      {
        agentId: 'sub-7',
        label: 'TB Implementation [oag-tb-implementation-agent]',
        status: 'completed',
        items: [],
        isMain: false,
      },
    ];
    const { getByText } = render(
      <SubagentLanes lanes={lanes} selectedId="" onSelect={(id) => picked.push(id)} />,
    );
    fireEvent.click(getByText('TB Implementation [oag-tb-implementation-agent]'));
    expect(picked).toContain('sub-7');
  });
});
