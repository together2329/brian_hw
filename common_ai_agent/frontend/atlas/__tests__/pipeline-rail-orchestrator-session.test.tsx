import { cleanup, fireEvent, render, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { PipelineOrchestratorChatPanel } from '../pipeline-rail';

type AtlasTestWindow = typeof window & {
  ACTIVE_SESSION?: string;
  ATLAS_WORKSPACE_SESSION_ID?: string;
  ATLAS_DB_SESSION_ID?: string;
};

describe('PipelineOrchestratorChatPanel session scoping', () => {
  afterEach(() => {
    cleanup();
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
});
