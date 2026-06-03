import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import {
  AgentWorkerStatus,
  summarizeInteractiveWorker,
  summarizeWorkerLive,
  type InteractiveWorkerStatus,
  type WorkerSnapshot,
} from '../agent-worker-status';

describe('AgentWorkerStatus', () => {
  it('summarizes live workflow workers with active queue counts', () => {
    const workers: readonly WorkerSnapshot[] = [
      { workflow: 'lint', transport: 'ipc', status: 'ok', running_count: 1 },
      { workflow: 'coverage', transport: 'ipc', status: 'ok', queued_count: 2 },
    ];

    const summary = summarizeWorkerLive({
      workers,
      workersError: '',
      agentAlive: false,
      agentRunning: false,
      execMode: 'orchestrator',
    });

    expect(summary.modeLabel).toBe('ipc');
    expect(summary.stateLabel).toBe('2/2 alive');
    expect(summary.detailLabel).toBe('1 running · 2 queued');
    expect(summary.tone).toBe('active');
  });

  it('renders the live worker strip above the detailed grid', () => {
    const workers: readonly WorkerSnapshot[] = [
      {
        workflow: 'rtl-gen',
        transport: 'ipc',
        status: 'ok',
        running_count: 1,
        active_jobs: [{ job_id: 'job-1', workflow: 'rtl-gen', status: 'running', worker_pid: 1234 }],
      },
    ];

    render(
      <AgentWorkerStatus
        workers={workers}
        workersError=""
        activeIp="uart_tx"
        agentAlive={false}
        agentRunning={false}
        execMode="orchestrator"
      />,
    );

    expect(screen.getByText('Worker Live')).toBeInTheDocument();
    expect(screen.getByTestId('worker-live-state')).toHaveTextContent('1/1 alive');
    expect(screen.getByTestId('worker-live-detail')).toHaveTextContent('1 running');
    expect(screen.getByText('rtl-gen')).toBeInTheDocument();
  });

  it('renders the interactive agent row from the typed status, separate from workflow workers', () => {
    const interactiveWorker: InteractiveWorkerStatus = {
      policy: 'single-active-owner', single_active_owner: true, max_active: 30,
      active_count: 1, owner: 'alice', state: 'ready', alive: true, running: false,
    };
    render(
      <AgentWorkerStatus
        workers={[]}
        workersError=""
        agentAlive
        agentRunning={false}
        execMode="single-worker"
        interactiveWorker={interactiveWorker}
      />,
    );
    // The 'agent' row reflects the typed interactive status...
    expect(screen.getByTestId('agent-state')).toHaveTextContent('ready');
    expect(screen.getByTestId('agent-detail')).toHaveTextContent('session worker hot');
    // ...and the workflow-workers section is its own, explicitly-empty concept.
    expect(screen.getByTestId('workflow-workers-empty')).toHaveTextContent('no active workflow workers');
  });

  it('shows agent ready AND no active workflow workers in orchestrator mode with a live agent', () => {
    const interactiveWorker: InteractiveWorkerStatus = {
      policy: 'single-active-owner', single_active_owner: true, max_active: 30,
      active_count: 1, state: 'ready', alive: true, running: false,
    };
    render(
      <AgentWorkerStatus
        workers={[]}
        workersError=""
        agentAlive
        agentRunning={false}
        execMode="orchestrator"
        interactiveWorker={interactiveWorker}
      />,
    );
    expect(screen.getByTestId('agent-state')).toHaveTextContent('ready');
    expect(screen.getByTestId('workflow-workers-empty')).toHaveTextContent('no active workflow workers');
  });

  it('maps capacity_wait to a visible warn, not a disconnect-looking error', () => {
    const line = summarizeInteractiveWorker({
      policy: 'single-active-owner', single_active_owner: true, max_active: 1,
      active_count: 1, state: 'capacity_wait', alive: false, running: false,
    });
    expect(line.tone).toBe('warn');
    expect(line.stateLabel).toBe('capacity wait');
    expect(line.detailLabel).toContain('1/1');
  });

  it('keeps agent-status errors separate from orchestrator worker errors', () => {
    const line = summarizeInteractiveWorker(null, 'boom');
    expect(line.tone).toBe('err');
    expect(line.detailLabel).toBe('boom');
  });
});
