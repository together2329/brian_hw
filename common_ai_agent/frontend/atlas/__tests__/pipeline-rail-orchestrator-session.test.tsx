import { act, cleanup, fireEvent, render, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { PipelineOrchestratorChatPanel } from '../pipeline-rail';

type AtlasTestWindow = typeof window & {
  ACTIVE_SESSION?: string;
  ATLAS_WORKSPACE_SESSION_ID?: string;
  ATLAS_DB_SESSION_ID?: string;
  backend?: {
    subscribe?: (ev: string, cb: (message: Record<string, unknown>) => void) => () => void;
  };
};

describe('PipelineOrchestratorChatPanel session scoping', () => {
  afterEach(() => {
    cleanup();
    vi.useRealTimers();
    vi.restoreAllMocks();
    const w = window as AtlasTestWindow;
    delete w.ACTIVE_SESSION;
    delete w.ATLAS_WORKSPACE_SESSION_ID;
    delete w.ATLAS_DB_SESSION_ID;
  });

  it('posts canonical orchestrator session and workspace without leaking DB session id', async () => {
    const w = window as AtlasTestWindow;
    w.ACTIVE_SESSION = 'alice/demo/jjj/orchestrator';
    w.ATLAS_WORKSPACE_SESSION_ID = 'demo';
    w.ATLAS_DB_SESSION_ID = 'db-row-id';

    const fetchMock = vi.fn(async (input: RequestInfo | URL, _init?: RequestInit): Promise<Response> => {
      const url = String(input);
      if (url.startsWith('/api/orchestrator/chat/messages')) {
        return new Response(JSON.stringify({ ok: true, messages: [], next_since: 0 }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        });
      }
      return new Response(JSON.stringify({ ok: true, status: 'started' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      });
    });
    vi.stubGlobal('fetch', fetchMock);

    const { container } = render(
      <PipelineOrchestratorChatPanel
        ip="jjj"
        pipelineState={{ orchestrator: { active: true } }}
      />,
    );

    const textarea = container.querySelector('textarea');
    if (!textarea) throw new Error('orchestrator textarea missing');
    fireEvent.change(textarea, { target: { value: 'status' } });
    fireEvent.keyDown(textarea, { key: 'Enter', code: 'Enter' });

    await waitFor(() => {
      const postCall = fetchMock.mock.calls.find(([url, init]) => (
        String(url) === '/api/pipeline/orchestrator/chat'
        && String((init as RequestInit | undefined)?.method || '').toUpperCase() === 'POST'
      ));
      expect(postCall).toBeTruthy();
    });

    const postCall = fetchMock.mock.calls.find(([url, init]) => (
      String(url) === '/api/pipeline/orchestrator/chat'
      && String((init as RequestInit | undefined)?.method || '').toUpperCase() === 'POST'
    ));
    const body = JSON.parse(String((postCall?.[1] as RequestInit | undefined)?.body || '{}')) as Record<string, unknown>;
    expect(body).toMatchObject({
      ip: 'jjj',
      message: 'status',
      session: 'alice/demo/jjj/orchestrator',
      workspace_session: 'demo',
    });
    expect(body.session_id).toBeUndefined();
  });

  it('does not force-scroll incoming orchestrator messages while the user is reading older content', async () => {
    const responses = [
      { ok: true, messages: [], next_since: 0 },
      {
        ok: true,
        messages: [{
          id: 'm1',
          role: 'agent',
          content: 'new orchestrator event',
          created_at: 1,
        }],
        next_since: 1,
      },
    ];
    const fetchMock = vi.fn(async (input: RequestInfo | URL): Promise<Response> => {
      const url = String(input);
      if (url.startsWith('/api/orchestrator/chat/messages')) {
        return new Response(JSON.stringify(responses.shift() || { ok: true, messages: [], next_since: 1 }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        });
      }
      return new Response(JSON.stringify({ ok: true, status: 'started' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      });
    });
    vi.stubGlobal('fetch', fetchMock);

    const { container } = render(
      <PipelineOrchestratorChatPanel
        ip="jjj"
        pipelineState={{ orchestrator: { active: true } }}
      />,
    );

    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    const body = container.querySelector('.orch-chat-body') as HTMLElement | null;
    if (!body) throw new Error('orchestrator chat body missing');
    let scrollTop = 100;
    Object.defineProperty(body, 'scrollTop', {
      configurable: true,
      get: () => scrollTop,
      set: (value) => { scrollTop = Number(value); },
    });
    Object.defineProperty(body, 'scrollHeight', { configurable: true, get: () => 1000 });
    Object.defineProperty(body, 'clientHeight', { configurable: true, get: () => 400 });

    fireEvent.scroll(body);
    await act(async () => { await new Promise((resolve) => setTimeout(resolve, 1600)); });

    await waitFor(() => expect(container.textContent).toContain('new orchestrator event'));
    expect(scrollTop).toBe(100);
  });

  it('streams orchestrator chat rows from backend subscription', async () => {
    let messageSink: ((message: Record<string, unknown>) => void) | null = null;
    const w = window as AtlasTestWindow;
    w.backend = {
      subscribe: (event: string, cb: (message: Record<string, unknown>) => void) => {
        if (event !== 'orchestrator_chat') return () => {};
        messageSink = cb;
        return () => {
          messageSink = null;
        };
      },
    };

    const fetchMock = vi.fn(async (input: RequestInfo | URL): Promise<Response> => {
      const url = String(input);
      if (url.startsWith('/api/orchestrator/chat/messages')) {
        return new Response(JSON.stringify({ ok: true, messages: [], next_since: 0 }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        });
      }
      return new Response(JSON.stringify({ ok: true, status: 'started' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      });
    });
    vi.stubGlobal('fetch', fetchMock);

    const { container } = render(
      <PipelineOrchestratorChatPanel
        ip="jjj"
        pipelineState={{ orchestrator: { active: true } }}
      />,
    );

    const message = {
      id: 'stream-1',
      role: 'tool',
      content: 'inspect_pipeline(args=abc)',
      created_at: 10,
      ip: 'jjj',
    };

    await waitFor(() => expect(messageSink).toBeTruthy());
    await act(async () => {
      messageSink && messageSink(message);
    });

    await waitFor(() => expect(container.textContent).toContain('INSPECT_PIPELINE'));
  });

});
