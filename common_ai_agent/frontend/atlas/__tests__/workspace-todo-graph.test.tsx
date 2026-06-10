// Tests for the TODO React Flow graph builder (workspace-todo-graph.tsx).
// buildTodoFlow turns a session's todos into laid-out React Flow nodes + the
// success / reject / dependency / condition edges that drive the flow view.
import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';

import { buildTodoFlow, TodoGraph } from '../workspace-todo-graph';
import type { TodoRecord } from '../workspace-todo-model';

const TODOS: readonly TodoRecord[] = [
  { id: 't1', title: 'first', state: 'approved', section: 'A', onSuccess: 2, command: 'echo hi' },
  { id: 't2', title: 'second', state: 'pending', section: 'B', onReject: 1 },
  { id: 't3', title: 'third', state: 'in_progress', section: 'C', deps: ['t1'], onCondition: [{ goto: 1 }] },
];

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe('buildTodoFlow', () => {
  it('builds one laid-out node per todo, with index titles and command markers', () => {
    const { nodes, nodeIds } = buildTodoFlow(TODOS);
    expect(nodeIds).toEqual(['t1', 't2', 't3']);
    expect(nodes).toHaveLength(3);
    const byId = new Map(nodes.map(n => [n.id, n.data as Record<string, unknown>]));
    expect(byId.get('t1')?.title).toBe('#1 first');
    expect(String(byId.get('t1')?.subtitle)).toContain('CMD');     // has a command gate
    expect(String(byId.get('t2')?.subtitle)).not.toContain('CMD');
    // dagre assigned real positions (not all at origin)
    expect(nodes.some(n => n.position.x !== 0 || n.position.y !== 0)).toBe(true);
  });

  it('derives success / reject / dependency / condition edges from the todo chain', () => {
    const { edges } = buildTodoFlow(TODOS);
    const shaped = edges.map(e => ({ from: e.source, to: e.target, label: e.label }));
    expect(shaped).toContainEqual({ from: 't1', to: 't2', label: 'success' }); // t1.onSuccess = 2
    expect(shaped).toContainEqual({ from: 't2', to: 't1', label: 'reject' });   // t2.onReject = 1
    expect(shaped).toContainEqual({ from: 't1', to: 't3', label: 'dep' });      // t3.deps = [t1]
    expect(shaped).toContainEqual({ from: 't3', to: 't1', label: 'cond' });     // t3.onCondition goto 1
  });
});

describe('TodoGraph', () => {
  it('renders the flow header and empty state without throwing', () => {
    const { rerender } = render(<TodoGraph todos={[]} openId={null} setOpenId={() => {}} />);
    expect(screen.getByText(/No todos for this session yet/)).toBeTruthy();
    rerender(<TodoGraph todos={TODOS} openId={null} setOpenId={() => {}} />);
    expect(screen.getByText(/TODO FLOW/)).toBeTruthy();
  });
});
