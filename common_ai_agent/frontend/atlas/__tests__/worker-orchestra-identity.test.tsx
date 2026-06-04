import { cleanup, render, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { OrchestratorTraceStrip, WorkerOrchestraBar } from '../pipeline-trace-workers';
import { win } from '../pipeline-trace-shared';

describe('WorkerOrchestraBar worker identity', () => {
  beforeEach(() => {
    win.PIPELINE_WORKSPACE_WORKFLOWS = new Set();
    win.ATLAS_WORKSPACE_SESSION_ID = 'alt';
    win.ACTIVE_SESSION = '';
    win.pipelineFetchWorkerSnapshot = vi.fn(async () => ({
      orchestrator: { enabled: true },
      workers: [
        {
          workflow: 'rtl-gen',
          status: 'ok',
          running_count: 1,
          worker_owner: 'u',
          workspace_session: 'alt',
          worker_session: 'u/alt/pl330/rtl-gen',
          running: [{ run_id: 'run-active' }],
        },
      ],
    }));
    global.fetch = vi.fn(async () =>
      new Response(JSON.stringify({ events: [] }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    ) as unknown as typeof fetch;
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it('renders request owner and workspace on workflow worker cards', async () => {
    const { container } = render(<WorkerOrchestraBar ip="pl330" />);

    await waitFor(() => expect(container.textContent || '').toContain('u/alt'));
    expect(container.textContent || '').toContain('rtl-gen');
    await waitFor(() => {
      expect(String((global.fetch as ReturnType<typeof vi.fn>).mock.calls[0]?.[0] || '')).toBe(
        '/api/orchestrator/trace?ip=pl330&limit=30&workspace_session=alt',
      );
    });
  });

  it('does not infer an owner label from single-user default worker sessions', async () => {
    win.ATLAS_WORKSPACE_SESSION_ID = '';
    win.pipelineFetchWorkerSnapshot = vi.fn(async () => ({
      orchestrator: { enabled: true },
      workers: [
        {
          workflow: 'rtl-gen',
          status: 'ok',
          running_count: 0,
          worker_session: 'pl330/rtl-gen',
        },
      ],
    }));

    const { container } = render(<WorkerOrchestraBar ip="pl330" />);

    await waitFor(() => expect(container.textContent || '').toContain('rtl-gen'));
    expect(container.querySelector('.pipe-orchestra-worker-owner')).toBeNull();
    expect(container.querySelector('button')?.getAttribute('title') || '').not.toContain('scope:');
  });

  it('does not infer an owner label from worker session without explicit owner fields', async () => {
    win.pipelineFetchWorkerSnapshot = vi.fn(async () => ({
      orchestrator: { enabled: true },
      workers: [
        {
          workflow: 'rtl-gen',
          status: 'ok',
          running_count: 0,
          workspace_session: 'alt',
          worker_session: 'u/alt/pl330/rtl-gen',
        },
      ],
    }));

    const { container } = render(<WorkerOrchestraBar ip="pl330" />);

    await waitFor(() => expect(container.textContent || '').toContain('rtl-gen'));
    expect(container.querySelector('.pipe-orchestra-worker-owner')).toBeNull();
    expect(container.querySelector('button')?.getAttribute('title') || '').not.toContain('scope:');
  });

  it('scopes orchestrator trace strip fetches by active workspace session', async () => {
    win.ATLAS_WORKSPACE_SESSION_ID = '';
    win.ACTIVE_SESSION = 'u/branch2/pl330/rtl-gen';

    render(<OrchestratorTraceStrip ip="pl330" />);

    await waitFor(() => {
      expect(String((global.fetch as ReturnType<typeof vi.fn>).mock.calls[0]?.[0] || '')).toBe(
        '/api/orchestrator/trace?ip=pl330&limit=20&workspace_session=branch2',
      );
    });
  });
});
