import { act, cleanup, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

type AnyWindow = typeof window & Record<string, any>;

const jsonResponse = (body: Record<string, unknown>) =>
  new Response(JSON.stringify(body), { status: 200, headers: { 'Content-Type': 'application/json' } });

const normalize = (value: unknown) => String(value || '').trim();

const routeFor = (session: unknown) => {
  const parts = normalize(session).split('/').filter(Boolean);
  return {
    owner: parts[0] || '',
    ip: parts.length >= 3 ? parts[parts.length - 2] : '',
    workflow: parts.length >= 3 ? parts[parts.length - 1] : '',
  };
};

function installContextStubs() {
  const w = window as AnyWindow;
  w.ACTIVE_SESSION = 'alice/ws/demo_ip/default';
  w.ATLAS_USER = { username: 'alice' };
  w.SCOPE_PATH = 'demo_ip';
  w.FLOW_STAGES = [{ id: 'default', label: 'Default' }];
  w.CONTEXT = {
    activeSession: 'alice/ws/demo_ip/default',
    tokens: 13_000,
    maxTokens: 200_000,
    tokensIn: 42_000,
    tokensCache: 0,
    tokensOut: 1_000,
    costUsd: 0.1,
    costScope: 'user_ip',
    costUser: 'alice',
    costIp: 'demo_ip',
  };
  w.normalizeUiSession = normalize;
  w.healthMatchesCurrentUser = () => true;
  w.uiEffectiveHealthSession = (payload: any) => normalize(payload && payload.active_session);
  w.uiHealthCountersMatchBrowserRoute = () => true;
  w.uiSessionRoute = routeFor;
  w.atlasUiExecMode = () => 'single-worker';
  w.atlasStatusMeta = () => ({ glyph: '·', color: 'var(--fg-mute)', label: 'status' });
  w.AtlasStatusBadge = () => null;
  w.workspaceFetchWorkerSnapshot = vi.fn(async () => ({ workers: [] }));
  w.AtlasWorkersLogic = {};
  global.fetch = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    if (url.startsWith('/healthz')) {
      return jsonResponse({
        ok: true,
        user_session: 'alice',
        active_session: 'alice/ws/demo_ip/default',
        active_ip: 'demo_ip',
        active_workflow: 'default',
        workspace: 'ws',
        model: 'gpt-test',
        max_context: 200_000,
        tokens: 0,
        tokens_in: 0,
        tokens_cache: 0,
        tokens_out: 0,
        cost_usd: 0,
        cost_scope: 'user_ip',
        cost_user: 'alice',
        cost_ip: 'demo_ip',
        cost_calls: 0,
        model_options: [],
      });
    }
    if (url.startsWith('/api/session/worker/status')) {
      return jsonResponse({ state: 'ready', alive: true, running: false });
    }
    if (url.startsWith('/api/soc')) return jsonResponse({ clusters: [] });
    return jsonResponse({});
  }) as unknown as typeof fetch;
}

function loaderDeps() {
  return {
    sessionStateCache: new Map<string, any>(),
    workerSnapshotCache: new Map<string, any>(),
    URL_ACTIVE_SESSION: '',
    SESSION_STATE_CACHE_MS: 1,
    CHAT_RECENT_LIMIT: 10,
    CHAT_SWITCH_LIMIT: 10,
    WORKER_SNAPSHOT_CACHE_MS: 1,
  };
}

describe('Atlas context token stability', () => {
  beforeEach(() => {
    installContextStubs();
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
    vi.resetModules();
  });

  it('does not let same-session /healthz tokens=0 erase the current context value', async () => {
    const { createDataLoaders } = await import('../data-loaders');
    const loaders = createDataLoaders(loaderDeps());

    await loaders.refreshHealth();

    expect((window as AnyWindow).CONTEXT.tokens).toBe(13_000);
    expect((window as AnyWindow).CONTEXT.maxTokens).toBe(200_000);
  });

  it('keeps AgentStatusPanel on the previous nonzero context during zero refresh noise', async () => {
    const { AgentStatusPanel } = await import('../agent-status-panel');

    render(<AgentStatusPanel intent="normal" workflow="default" activeIp="demo_ip" />);

    await waitFor(() => {
      expect(screen.getByText('13.0K')).toBeInTheDocument();
    });

    await act(async () => {
      const w = window as AnyWindow;
      w.CONTEXT = { ...w.CONTEXT, tokens: 0, maxTokens: 0 };
      window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'CONTEXT' }));
    });

    expect(screen.getByText('13.0K')).toBeInTheDocument();
    expect(screen.queryByText('0.0K')).not.toBeInTheDocument();
  });
});
