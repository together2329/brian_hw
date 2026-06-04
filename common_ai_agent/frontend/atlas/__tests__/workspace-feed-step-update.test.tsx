import { afterEach, describe, expect, it } from 'vitest';
import { cleanup, render, screen } from '@testing-library/react';

import '../ui-utils.tsx';
import { _parseTodoStepUpdate } from '../workspace-report-status';
import { ToolCard } from '../workspace-feed-cards';

describe('workspace step update feed cards', () => {
  afterEach(() => cleanup());

  it('parses approved todo updates with transition, reason, next step, and tally', () => {
    const info = _parseTodoStepUpdate(
      [
        '✅ Task 1 approved. [read rtl/top.sv:42 and ran compile — pass]',
        "→ Next: todo_update(index=2, status='in_progress') — Run lint",
        '',
        '── TODO ──',
        '  ✅ 1. [approved] Inspect RTL',
        '  ⏸ 2. [pending] Run lint',
      ].join('\n'),
      'todo_update',
      '#1 completed → approved',
    );

    expect(info).not.toBeNull();
    expect(info).toMatchObject({
      index: '1',
      fromStatus: 'completed',
      toStatus: 'approved',
      reasonLabel: 'Approved',
    });
    expect(info?.reason).toContain('read rtl/top.sv:42');
    expect(info?.next).toContain('index=2');
    expect(info?.tally).toContain('approved');
    expect(info?.tally).toContain('pending');
  });

  it('renders approved updates as a readable status card', () => {
    render(
      <ToolCard
        action={{ kind: 'action', tool: 'todo_update', text: '▶ todo_update  #1 completed → approved', createdAt: Date.now() }}
        obs={{
          kind: 'obs',
          tool: 'todo_update',
          text: '✅ Task 1 approved. [read rtl/top.sv:42 and ran compile — pass]',
          createdAt: Date.now(),
        }}
        summaryMode
      />,
    );

    expect(screen.getByText('step_update')).toBeTruthy();
    expect(screen.getByText('Task #1')).toBeTruthy();
    expect(screen.getByText('completed → approved')).toBeTruthy();
    expect(screen.getByText(/read rtl\/top\.sv:42/i)).toBeTruthy();
  });

  it('renders rejected updates with the rejection reason emphasized', () => {
    render(
      <ToolCard
        action={{ kind: 'action', tool: 'todo_update', text: '▶ todo_update  #2 completed → rejected', createdAt: Date.now() }}
        obs={{
          kind: 'obs',
          tool: 'todo_update',
          text: '❌ Task 2 rejected: missing compile evidence for rtl/dma.sv',
          createdAt: Date.now(),
        }}
        summaryMode
      />,
    );

    expect(screen.getByText('Task #2')).toBeTruthy();
    expect(screen.getByText('completed → rejected')).toBeTruthy();
    expect(screen.getByText(/missing compile evidence/i)).toBeTruthy();
  });

  it('renders plan-mode blocked status changes as blocked step updates', () => {
    render(
      <ToolCard
        action={{ kind: 'action', tool: 'todo_update', text: '▶ todo_update  #1 pending → in_progress [blocked: plan]', createdAt: Date.now() }}
        obs={{
          kind: 'obs',
          tool: 'todo_update',
          text: "[Plan Mode] 'todo_update' is blocked in plan mode. Use todo_write to replace the list.",
          createdAt: Date.now(),
        }}
        summaryMode
      />,
    );

    expect(screen.getByText('Task #1')).toBeTruthy();
    expect(screen.getByText('pending → blocked')).toBeTruthy();
    expect(screen.getByText(/todo_update.*blocked in plan mode/i)).toBeTruthy();
  });

  it('renders action-only plan-mode blocked status attempts as blocked', () => {
    render(
      <ToolCard
        action={{ kind: 'action', tool: 'todo_update', text: '▶ todo_update  #1 pending → in_progress [blocked: plan]', createdAt: Date.now() }}
        summaryMode
      />,
    );

    expect(screen.getByText('Task #1')).toBeTruthy();
    expect(screen.getByText('pending → blocked')).toBeTruthy();
    expect(screen.queryByText('pending → in-progress')).toBeNull();
  });

  it('renders todo status reads as snapshots instead of pending task transitions', () => {
    render(
      <ToolCard
        action={{ kind: 'action', tool: 'todo_status', text: '▶ todo_status', createdAt: Date.now() }}
        obs={{
          kind: 'obs',
          tool: 'todo_status',
          text: [
            '── PLAN & PROGRESS ──',
            '👀 1. [Review] [HIGH]',
            'Draft project outline',
          ].join('\n'),
          createdAt: Date.now(),
        }}
        summaryMode
      />,
    );

    expect(screen.getByText('step_status')).toBeTruthy();
    expect(screen.getByText('snapshot')).toBeTruthy();
    expect(screen.getByText('1 completed')).toBeTruthy();
    expect(screen.queryByText('Task')).toBeNull();
    expect(screen.queryByText('pending')).toBeNull();
  });
});
