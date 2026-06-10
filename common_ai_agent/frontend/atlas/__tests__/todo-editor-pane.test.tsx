import { cleanup, fireEvent, render, screen, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { TodoEditorPane } from '../workspace-todo';

const todos = [
  {
    id: 'todo-1',
    title: 'Plan DMA coverage mapping',
    state: 'pending',
    priority: 'high',
    detail: 'Map toggle and static coverage holes back to RTL signals.',
    criteria: ['Shows uncovered signal', 'Links report row to RTL line'],
    approvedReason: '',
    rejectionReason: '',
    notes: ['Need VCD selection support.'],
  },
  {
    id: 'todo-2',
    title: 'Review workflow switch timing',
    state: 'approved',
    priority: 'medium',
    detail: 'Confirm frontend switch is visible before backend activation finishes.',
    criteria: 'Switch session first\nNo stale Agent Responding',
    approvedReason: 'Browser QA confirmed immediate switch.',
    rejectionReason: '',
    notes: [],
    command: 'python3 workflow/req-gen/scripts/check_locked_truth_bundle.py timer_new_concept',
    onReject: 1,
    commandLogs: [{
      cmd: 'python3 workflow/req-gen/scripts/check_locked_truth_bundle.py timer_new_concept',
      ok: true,
      tail: 'locked truth bundle valid',
      log_file: 'command_logs/task_2_gate_1.log',
      lines: 12,
      elapsed: 0.42,
    }],
  },
];

describe('TodoEditorPane readable modes', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.stubGlobal('confirm', vi.fn(() => true));
    (window as unknown as { TODOS: unknown[] }).TODOS = todos;
    (window as unknown as { atlasData: Record<string, unknown> }).atlasData = {
      refreshTodos: vi.fn(),
      addTodo: vi.fn(),
      updateTodo: vi.fn(),
      removeTodo: vi.fn(),
      clearTodos: vi.fn(),
    };
  });

  afterEach(() => {
    cleanup();
  });

  it('opens in readable list mode, expands one todo, and keeps editing behind the edit view', () => {
    render(<TodoEditorPane />);

    expect(screen.getByRole('button', { name: /^list$/i })).toHaveAttribute('aria-pressed', 'true');
    expect(screen.queryByPlaceholderText(/content \(required\)/i)).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Plan DMA coverage mapping/i }));

    expect(screen.getByText('Detail')).toBeVisible();
    expect(screen.getByText(/Map toggle and static coverage holes/i)).toBeVisible();
    expect(screen.getByText('Criteria')).toBeVisible();
    expect(screen.getByText('Shows uncovered signal')).toBeVisible();

    fireEvent.click(screen.getByRole('button', { name: /^detail$/i }));

    expect(screen.getByText(/Confirm frontend switch is visible/i)).toBeVisible();
    expect(screen.getByText(/Browser QA confirmed immediate switch/i)).toBeVisible();
    expect(screen.getByText('Command Gate')).toBeVisible();
    expect(screen.getByText(/check_locked_truth_bundle.py timer_new_concept/i)).toBeVisible();
    expect(screen.getByText(/On Reject: Task #1/i)).toBeVisible();
    expect(screen.getByText(/locked truth bundle valid/i)).toBeVisible();

    fireEvent.click(screen.getByRole('button', { name: /^graph$/i }));

    expect(screen.getByText(/TODO FLOW/i)).toBeVisible();
    // The flow now renders via React Flow; the next/reject/dep/condition edges
    // and CMD markers are asserted on the data in workspace-todo-graph.test.tsx
    // (buildTodoFlow). Here we just prove graph mode mounts the canvas.
    expect(document.querySelector('.react-flow')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: /^edit$/i }));

    expect(screen.getByPlaceholderText(/content \(required\)/i)).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: /^Save$/i })).toHaveLength(2);
  });

  it('does not offer execution-only status transitions while the workspace is in plan mode', () => {
    render(<TodoEditorPane intent="plan" />);

    fireEvent.click(screen.getByRole('button', { name: /^edit$/i }));

    const firstCard = screen.getByText('#1').closest('.digest-card');
    if (!firstCard) throw new Error('first todo card not found');
    const stateSelect = within(firstCard).getByDisplayValue('pending') as HTMLSelectElement;
    const inProgressOption = Array.from(stateSelect.options).find(option => option.value === 'in_progress');
    const approvedOption = Array.from(stateSelect.options).find(option => option.value === 'approved');

    expect(inProgressOption).toBeDefined();
    expect(inProgressOption?.disabled).toBe(true);
    expect(approvedOption).toBeDefined();
    expect(approvedOption?.disabled).toBe(true);
  });
});
