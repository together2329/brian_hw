import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

type AnyWindow = typeof window & Record<string, any>;

const jsonResponse = (body: Record<string, unknown>) =>
  new Response(JSON.stringify(body), { status: 200, headers: { 'Content-Type': 'application/json' } });

describe('worker snapshot workspace scoping', () => {
  beforeEach(() => {
    const w = window as AnyWindow;
    w.ACTIVE_SESSION = 'alice/alt/demo_ip/orchestrator';
    w.ATLAS_WORKSPACE_SESSION_ID = '';
    w.atlasData = {};
    global.fetch = vi.fn(async () => jsonResponse({ workers: [] })) as unknown as typeof fetch;
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.resetModules();
  });

  it('adds workspace_session in data loader worker snapshots', async () => {
    const { createDataLoaders } = await import('../data-loaders.tsx');
    const loaders = createDataLoaders({
      CHAT_RECENT_LIMIT: 20,
      CHAT_SWITCH_LIMIT: 20,
      SESSION_STATE_CACHE_MS: 1,
      URL_ACTIVE_SESSION: '',
      WORKER_SNAPSHOT_CACHE_MS: 1,
      sessionStateCache: new Map(),
      workerSnapshotCache: new Map(),
    });

    await loaders.fetchWorkerSnapshot({ ip: 'demo_ip' });

    const fetchMock = global.fetch as unknown as ReturnType<typeof vi.fn>;
    expect(String(fetchMock.mock.calls[0]?.[0] || '')).toBe('/api/orchestrator/workers?active_only=1&ip=demo_ip&workspace_session=alt');
  });

  it('adds workspace_session in pipeline worker snapshots', async () => {
    const { pipelineFetchWorkerSnapshot } = await import('../pipe-width.tsx');

    await pipelineFetchWorkerSnapshot({ ip: 'demo_ip' });

    const fetchMock = global.fetch as unknown as ReturnType<typeof vi.fn>;
    expect(String(fetchMock.mock.calls[0]?.[0] || '')).toBe('/api/orchestrator/workers?active_only=1&ip=demo_ip&workspace_session=alt');
  });

  it('adds workspace_session in workspace worker snapshots', async () => {
    const { workspaceFetchWorkerSnapshot } = await import('../workspace-tool-theme.tsx');

    await workspaceFetchWorkerSnapshot({ ip: 'demo_ip' });

    const fetchMock = global.fetch as unknown as ReturnType<typeof vi.fn>;
    expect(String(fetchMock.mock.calls[0]?.[0] || '')).toBe('/api/orchestrator/workers?active_only=1&ip=demo_ip&workspace_session=alt');
  });
});
