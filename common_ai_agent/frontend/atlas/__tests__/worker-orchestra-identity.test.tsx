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
        '/api/orchestrator/runs/latest/trace?ip=pl330&limit=50&workspace_session=branch2',
      );
    });
  });

  it('renders latest decision trace before falling back to legacy trace events', async () => {
    win.ATLAS_WORKSPACE_SESSION_ID = 'alt';
    global.fetch = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.startsWith('/api/orchestrator/runs/latest/trace')) {
        return new Response(JSON.stringify({
          ok: true,
          run_id: 'run-abc123456',
          run: {
            effective_final_state: 'tool_failed',
            terminal_anomaly: 'run recorded completed after tool_failed at step 0',
          },
          steps: [
            {
              step: 0,
              time: '10:00:00',
              tool: 'dispatch_workflow',
              status: 'failed',
              detail: 'dispatch tb-gen [FAILED]',
              error: 'bridge timed out',
            },
          ],
        }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        });
      }
      return new Response(JSON.stringify({ events: [{ kind: 'legacy' }] }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      });
    }) as unknown as typeof fetch;

    const { container } = render(<OrchestratorTraceStrip ip="pl330" />);

    await waitFor(() => expect(container.textContent || '').toContain('dispatch tb-gen [FAILED]'));
    expect(container.textContent || '').toContain('tool_failed');
    expect(container.textContent || '').toContain('bridge timed out');
    expect(String((global.fetch as ReturnType<typeof vi.fn>).mock.calls[0]?.[0] || '')).toContain('/api/orchestrator/runs/latest/trace');
    expect((global.fetch as ReturnType<typeof vi.fn>).mock.calls).toHaveLength(1);
  });
});
