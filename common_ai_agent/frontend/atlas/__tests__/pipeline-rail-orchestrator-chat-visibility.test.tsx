import { act, cleanup, fireEvent, render, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { PipelineOrchestratorChatPanel } from '../pipeline-rail';

type AtlasTestWindow = typeof window & {
  ACTIVE_SESSION?: string;
  ATLAS_WORKSPACE_SESSION_ID?: string;
  backend?: {
    subscribe?: (ev: string, cb: (message: Record<string, unknown>) => void) => () => void;
  };
};

const emptyMessagesResponse = () => new Response(
  JSON.stringify({ ok: true, messages: [], next_since: 0 }),
  { status: 200, headers: { 'Content-Type': 'application/json' } },
);

const pollCallCount = (fetchMock: ReturnType<typeof vi.fn>): number => (
  fetchMock.mock.calls.filter(([url]) => String(url).startsWith('/api/orchestrator/chat/messages')).length
);

describe('PipelineOrchestratorChatPanel output visibility', () => {
  afterEach(() => {
    cleanup();
    vi.useRealTimers();
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
    const w = window as AtlasTestWindow;
    delete w.ACTIVE_SESSION;
    delete w.ATLAS_WORKSPACE_SESSION_ID;
    delete w.backend;
  });

  it('keeps polling /api/orchestrator/chat/messages even when a live WS backend is subscribed', async () => {
    // Regression: the server never emits orchestrator_chat WS events, so a
    // connected backend.subscribe channel must not disable polling — the
    // panel would otherwise stay empty forever after the mount fetch.
    vi.useFakeTimers();
    const fetchMock = vi.fn(async (): Promise<Response> => emptyMessagesResponse());
    vi.stubGlobal('fetch', fetchMock);
    const unsubscribe = vi.fn();
    const subscribe = vi.fn(() => unsubscribe);
    (window as AtlasTestWindow).backend = { subscribe };

    render(
      <PipelineOrchestratorChatPanel
        ip="jjj"
        pipelineState={{ orchestrator: { active: true } }}
      />,
    );

    await act(async () => { await vi.advanceTimersByTimeAsync(20); });
    const initialPolls = pollCallCount(fetchMock);
    expect(initialPolls).toBeGreaterThanOrEqual(1);
    expect(subscribe).toHaveBeenCalledWith('orchestrator_chat', expect.any(Function));

    await act(async () => { await vi.advanceTimersByTimeAsync(5_000); });
    expect(pollCallCount(fetchMock)).toBeGreaterThan(initialPolls);
  });

  it('renders a local failure notice when the send POST is rejected', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
      const url = String(input);
      if (url.startsWith('/api/orchestrator/chat/messages')) return emptyMessagesResponse();
      if (url.startsWith('/api/pipeline/orchestrator/chat') && init?.method === 'POST') {
        return new Response(JSON.stringify({ error: 'forbidden' }), {
          status: 403,
          headers: { 'Content-Type': 'application/json' },
        });
      }
      return emptyMessagesResponse();
    });
    vi.stubGlobal('fetch', fetchMock);

    const { container } = render(
      <PipelineOrchestratorChatPanel
        ip="jjj"
        pipelineState={{ orchestrator: { active: false } }}
      />,
    );

    const textarea = container.querySelector('textarea');
    if (!textarea) throw new Error('orchestrator textarea missing');
    fireEvent.change(textarea, { target: { value: 'do the thing' } });
    fireEvent.keyDown(textarea, { key: 'Enter', code: 'Enter' });

    await waitFor(() => {
      expect(container.textContent).toContain('message not delivered');
      expect(container.textContent).toContain('HTTP 403: forbidden');
    });
  });

  it('refetches messages immediately after a successful send', async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit): Promise<Response> => {
      const url = String(input);
      if (url.startsWith('/api/orchestrator/chat/messages')) return emptyMessagesResponse();
      if (url.startsWith('/api/pipeline/orchestrator/chat') && init?.method === 'POST') {
        return new Response(JSON.stringify({ ok: true, status: 'started' }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        });
      }
      return emptyMessagesResponse();
    });
    vi.stubGlobal('fetch', fetchMock);

    const { container } = render(
      <PipelineOrchestratorChatPanel
        ip="jjj"
        pipelineState={{ orchestrator: { active: false } }}
      />,
    );

    await waitFor(() => {
      expect(pollCallCount(fetchMock)).toBeGreaterThanOrEqual(1);
    });
    const pollsBeforeSend = pollCallCount(fetchMock);

    const textarea = container.querySelector('textarea');
    if (!textarea) throw new Error('orchestrator textarea missing');
    fireEvent.change(textarea, { target: { value: 'run the pipeline' } });
    fireEvent.keyDown(textarea, { key: 'Enter', code: 'Enter' });

    await waitFor(() => {
      expect(pollCallCount(fetchMock)).toBeGreaterThan(pollsBeforeSend);
    });
  });
});
