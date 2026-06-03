import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
vi.setConfig({ testTimeout: 30000, hookTimeout: 30000 });

import { act, cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import type { ReactElement } from 'react';

type AnyWindow = typeof window & Record<string, any>;

const jsonResponse = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });

const normalize = (value: unknown): string => String(value || '').trim();

function installRuntimeStubs() {
  const w = window as AnyWindow;
  const backendSubscribers: Record<string, Array<(payload: unknown) => void>> = {};

  w.React = {};
  w.Workspace = ({ activeNamespace, activeWorkflow }: { activeNamespace?: string; activeWorkflow?: string }) => (
    <div
      data-testid="workspace-stub"
      data-active-namespace={activeNamespace || ''}
      data-active-workflow={activeWorkflow || ''}
    />
  );
  w.backend = {
    state: 'open',
    getConnectionState: () => 'open',
    switchSession: vi.fn(),
    connect: vi.fn(),
    send: vi.fn(),
    subscribe: vi.fn((event: string, cb: (payload: unknown) => void) => {
      (backendSubscribers[event] || (backendSubscribers[event] = [])).push(cb);
      return () => {
        backendSubscribers[event] = (backendSubscribers[event] || []).filter((handler) => handler !== cb);
      };
    }),
    on: vi.fn(),
    off: vi.fn(),
  };
  w.normalizeAtlasSessionName = normalize;
  w.ATLAS_USER = { username: 'alice' };
  w.ATLAS_USER_SESSION_ID = 'alice';
  w.ATLAS_WORKSPACE_SESSION_ID = 's1';
  w.ACTIVE_SESSION = 'alice/s1/ip_alpha/rtl-gen';
  w.ACTIVE_IP = 'ip_alpha';
  w.IP_OPTIONS = ['default', 'ip_alpha'];
  w.CONTEXT = {};
  w.FLOW_STAGES = [];
  w.TODOS = [];
  w.ATLAS_AGENT_RUNNING = false;
  w.atlasData = {
    normalizeSessionName: normalize,
    sessionFor: (ip: string, workflow: string) => {
      const parts = normalize(w.ACTIVE_SESSION).split('/').filter(Boolean);
      const owner = parts[0] || 'alice';
      const workspaceSession = (
        (parts.length >= 4 && parts[0] === owner ? parts[1] : '')
        || normalize(w.ATLAS_WORKSPACE_SESSION_ID)
        || 'default'
      );
      return `${owner}/${workspaceSession}/${normalize(ip) || 'default'}/${normalize(workflow) || 'default'}`;
    },
    setUserSessionId: vi.fn((owner: string) => {
      w.ATLAS_USER_SESSION_ID = owner;
    }),
    setScopePath: vi.fn(),
    setActiveSession: vi.fn((session: string) => {
      w.ACTIVE_SESSION = session;
    }),
    refreshHealth: vi.fn(),
  };
  delete w.ATLAS_BOOT_CONFIG;
  delete w.ATLAS_DEFAULT_EXEC_MODE;
}

function installFetchStub() {
  const ipListScopes: string[] = [];
  const activateBodies: unknown[] = [];
  const fetchSpy = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = new URL(String(input), 'http://localhost');
    if (url.pathname === '/api/users/me') {
      return jsonResponse({ user: { username: 'alice' } });
    }
    if (url.pathname === '/api/session/activate') {
      const rawBody = typeof init?.body === 'string' ? init.body : '{}';
      const body = JSON.parse(rawBody) as {
        owner?: string;
        workspace_session?: string;
        ip?: string;
        workflow?: string;
      };
      activateBodies.push(body);
      const owner = normalize(body.owner) || 'alice';
      const workspaceSession = normalize(body.workspace_session) || 'default';
      const ip = normalize(body.ip) || 'default';
      const workflow = normalize(body.workflow) || 'default';
      return jsonResponse({
        namespace: `${owner}/${workspaceSession}/${ip}/${workflow}`,
        db_session_id: `${owner}:${workspaceSession}:${ip}:${workflow}`,
        session_uid: `${workspaceSession}-${ip}-${workflow}`,
      });
    }
    if (url.pathname === '/api/session/list') {
      return jsonResponse({
        sessions: [
          { session: 'alice/s1/ip_alpha/rtl-gen', namespace: 'alice/s1/ip_alpha/rtl-gen' },
          { session: 'alice/s2/ip_beta/default', namespace: 'alice/s2/ip_beta/default' },
        ],
      });
    }
    if (url.pathname === '/api/ip/list') {
      const scope = normalize(url.searchParams.get('session_id') || '');
      ipListScopes.push(scope);
      if (scope === 'alice/s1') {
        return jsonResponse({ items: [{ name: 'ip_alpha' }], count: 1, workspace_session: 's1' });
      }
      if (scope === 'alice/s2') {
        return jsonResponse({ items: [{ name: 'ip_beta' }], count: 1, workspace_session: 's2' });
      }
      return jsonResponse({ items: [], count: 0 });
    }
    if (url.pathname === '/api/pipeline/run_policy') {
      return jsonResponse({ run_mode: 'engineering', exec_mode: 'single-worker' });
    }
    if (url.pathname === '/api/llm/ping') {
      return jsonResponse({ ok: true });
    }
    if (url.pathname === '/healthz') {
      return jsonResponse({ active_session: (window as AnyWindow).ACTIVE_SESSION });
    }
    return jsonResponse({});
  });
  global.fetch = fetchSpy as unknown as typeof fetch;
  return { fetchSpy, ipListScopes, activateBodies };
}

function deferredJsonResponse(body: unknown) {
  let resolveResponse: (() => void) | null = null;
  const gate = new Promise<void>((resolve) => {
    resolveResponse = resolve;
  });
  return {
    resolve: () => {
      if (resolveResponse) resolveResponse();
    },
    response: gate.then(() => jsonResponse(body)),
  };
}

function installDeferredSessionSwitchFetchStub() {
  const ipListScopes: string[] = [];
  const s2IpList = deferredJsonResponse({
    items: [{ name: 'ip_beta' }],
    count: 1,
    workspace_session: 's2',
  });
  const fetchSpy = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = new URL(String(input), 'http://localhost');
    if (url.pathname === '/api/users/me') {
      return jsonResponse({ user: { username: 'alice' } });
    }
    if (url.pathname === '/api/session/activate') {
      const rawBody = typeof init?.body === 'string' ? init.body : '{}';
      const body = JSON.parse(rawBody) as {
        owner?: string;
        workspace_session?: string;
        ip?: string;
        workflow?: string;
      };
      const owner = normalize(body.owner) || 'alice';
      const workspaceSession = normalize(body.workspace_session) || 'default';
      const ip = normalize(body.ip) || 'default';
      const workflow = normalize(body.workflow) || 'default';
      return jsonResponse({
        namespace: `${owner}/${workspaceSession}/${ip}/${workflow}`,
        db_session_id: `${owner}:${workspaceSession}:${ip}:${workflow}`,
      });
    }
    if (url.pathname === '/api/session/list') {
      return jsonResponse({
        sessions: [
          { session: 'alice/s1/ip_alpha/rtl-gen', namespace: 'alice/s1/ip_alpha/rtl-gen' },
          { session: 'alice/s2/ip_beta/default', namespace: 'alice/s2/ip_beta/default' },
        ],
      });
    }
    if (url.pathname === '/api/ip/list') {
      const scope = normalize(url.searchParams.get('session_id') || '');
      ipListScopes.push(scope);
      if (scope === 'alice/s1') {
        return jsonResponse({ items: [{ name: 'ip_alpha' }], count: 1, workspace_session: 's1' });
      }
      if (scope === 'alice/s2') {
        return s2IpList.response;
      }
      return jsonResponse({ items: [], count: 0 });
    }
    if (url.pathname === '/api/pipeline/run_policy') {
      return jsonResponse({ run_mode: 'engineering', exec_mode: 'single-worker' });
    }
    if (url.pathname === '/api/llm/ping') {
      return jsonResponse({ ok: true });
    }
    if (url.pathname === '/healthz') {
      return jsonResponse({ active_session: (window as AnyWindow).ACTIVE_SESSION });
    }
    return jsonResponse({});
  });
  global.fetch = fetchSpy as unknown as typeof fetch;
  return { fetchSpy, ipListScopes, s2IpList };
}

function installDeferredOwnerRebindFetchStub() {
  const ipListScopes: string[] = [];
  const usersMe = deferredJsonResponse({ user: { username: 'bob' } });
  const bobIpList = deferredJsonResponse({
    items: [{ name: 'ip_bob' }],
    count: 1,
    workspace_session: 'default',
  });
  const fetchSpy = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = new URL(String(input), 'http://localhost');
    if (url.pathname === '/api/users/me') {
      return usersMe.response;
    }
    if (url.pathname === '/api/session/activate') {
      const rawBody = typeof init?.body === 'string' ? init.body : '{}';
      const body = JSON.parse(rawBody) as {
        owner?: string;
        workspace_session?: string;
        ip?: string;
        workflow?: string;
      };
      const owner = normalize(body.owner) || 'bob';
      const workspaceSession = normalize(body.workspace_session) || 'default';
      const ip = normalize(body.ip) || 'default';
      const workflow = normalize(body.workflow) || 'default';
      return jsonResponse({
        namespace: `${owner}/${workspaceSession}/${ip}/${workflow}`,
        db_session_id: `${owner}:${workspaceSession}:${ip}:${workflow}`,
      });
    }
    if (url.pathname === '/api/session/list') {
      return jsonResponse({
        sessions: [
          { session: 'alice/s1/ip_alpha/rtl-gen', namespace: 'alice/s1/ip_alpha/rtl-gen' },
          { session: 'bob/default/ip_bob/default', namespace: 'bob/default/ip_bob/default' },
        ],
      });
    }
    if (url.pathname === '/api/ip/list') {
      const scope = normalize(url.searchParams.get('session_id') || '');
      ipListScopes.push(scope);
      if (scope === 'alice/s1') {
        return jsonResponse({ items: [{ name: 'ip_alpha' }], count: 1, workspace_session: 's1' });
      }
      if (scope === 'bob/default') {
        return bobIpList.response;
      }
      return jsonResponse({ items: [], count: 0 });
    }
    if (url.pathname === '/api/pipeline/run_policy') {
      return jsonResponse({ run_mode: 'engineering', exec_mode: 'single-worker' });
    }
    if (url.pathname === '/api/llm/ping') {
      return jsonResponse({ ok: true });
    }
    if (url.pathname === '/healthz') {
      return jsonResponse({ active_session: (window as AnyWindow).ACTIVE_SESSION });
    }
    return jsonResponse({});
  });
  global.fetch = fetchSpy as unknown as typeof fetch;
  return { fetchSpy, ipListScopes, usersMe, bobIpList };
}

function installDeferredBackendSyncFetchStub() {
  const ipListScopes: string[] = [];
  const s1IpList = deferredJsonResponse({
    items: [{ name: 'ip_alpha' }],
    count: 1,
    workspace_session: 's1',
  });
  const s2IpList = deferredJsonResponse({
    items: [{ name: 'ip_beta' }],
    count: 1,
    workspace_session: 's2',
  });
  const fetchSpy = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = new URL(String(input), 'http://localhost');
    if (url.pathname === '/api/users/me') {
      return jsonResponse({ user: { username: 'alice' } });
    }
    if (url.pathname === '/api/session/activate') {
      const rawBody = typeof init?.body === 'string' ? init.body : '{}';
      const body = JSON.parse(rawBody) as {
        owner?: string;
        workspace_session?: string;
        ip?: string;
        workflow?: string;
      };
      const owner = normalize(body.owner) || 'alice';
      const workspaceSession = normalize(body.workspace_session) || 'default';
      const ip = normalize(body.ip) || 'default';
      const workflow = normalize(body.workflow) || 'default';
      return jsonResponse({
        namespace: `${owner}/${workspaceSession}/${ip}/${workflow}`,
        db_session_id: `${owner}:${workspaceSession}:${ip}:${workflow}`,
      });
    }
    if (url.pathname === '/api/session/list') {
      return jsonResponse({
        sessions: [
          { session: 'alice/s1/ip_alpha/rtl-gen', namespace: 'alice/s1/ip_alpha/rtl-gen' },
          { session: 'alice/s2/ip_beta/default', namespace: 'alice/s2/ip_beta/default' },
        ],
      });
    }
    if (url.pathname === '/api/ip/list') {
      const scope = normalize(url.searchParams.get('session_id') || '');
      ipListScopes.push(scope);
      if (scope === 'alice/s1') {
        return s1IpList.response;
      }
      if (scope === 'alice/s2') {
        return s2IpList.response;
      }
      return jsonResponse({ items: [], count: 0 });
    }
    if (url.pathname === '/api/pipeline/run_policy') {
      return jsonResponse({ run_mode: 'engineering', exec_mode: 'single-worker' });
    }
    if (url.pathname === '/api/llm/ping') {
      return jsonResponse({ ok: true });
    }
    if (url.pathname === '/healthz') {
      return jsonResponse({ active_session: (window as AnyWindow).ACTIVE_SESSION });
    }
    return jsonResponse({});
  });
  global.fetch = fetchSpy as unknown as typeof fetch;
  return { fetchSpy, ipListScopes, s1IpList, s2IpList };
}

async function mountApp() {
  let captured: ReactElement | null = null;
  (window as AnyWindow).ReactDOM = {
    createRoot: vi.fn(() => ({
      render: (element: ReactElement) => {
        captured = element;
      },
    })),
  };
  await import('../app.tsx');
  if (!captured) {
    throw new Error('App root was not captured');
  }
  let mounted: ReturnType<typeof render> | null = null;
  await act(async () => {
    mounted = render(captured);
    await Promise.resolve();
    await Promise.resolve();
  });
  if (!mounted) {
    throw new Error('App root did not mount');
  }
  return mounted;
}

describe('App workspace session switching', () => {
  beforeEach(() => {
    vi.resetModules();
    localStorage.clear();
    installRuntimeStubs();
    window.history.replaceState(
      null,
      '',
      '/?session=alice%2Fs1%2Fip_alpha%2Frtl-gen&session_id=alice&workspace_session=s1&ip=ip_alpha&workflow=rtl-gen',
    );
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it('resets IP and workflow to default and refreshes the roster for the selected workspace session', async () => {
    const { ipListScopes, activateBodies } = installFetchStub();
    await mountApp();

    const sessionSelect = await screen.findByLabelText('Workspace session');
    const ipSelect = await screen.findByLabelText('IP ID');
    await waitFor(() => {
      expect(sessionSelect).toHaveValue('s1');
      expect(ipSelect).toHaveValue('ip_alpha');
    });

    await act(async () => {
      fireEvent.change(sessionSelect, { target: { value: 's2' } });
      await Promise.resolve();
    });

    await waitFor(() => {
      expect((window as AnyWindow).ACTIVE_SESSION).toBe('alice/s2/default/default');
      expect((window as AnyWindow).ATLAS_WORKSPACE_SESSION_ID).toBe('s2');
      expect(ipSelect).toHaveValue('default');
      const optionValues = within(ipSelect).getAllByRole('option').map((option) => option.getAttribute('value'));
      expect(optionValues).toEqual(['default', 'ip_beta']);
    });
    expect(ipListScopes).toContain('alice/s2');
    expect(ipListScopes).not.toContain('alice/s2/ip_alpha');
    expect(activateBodies).toContainEqual({
      owner: 'alice',
      workspace_session: 's2',
      ip: 'default',
      workflow: 'default',
      preserve_running: false,
    });
  });

  it('does not keep the previous workspace session IPs while the new scoped roster is loading', async () => {
    const { ipListScopes, s2IpList } = installDeferredSessionSwitchFetchStub();
    await mountApp();

    const sessionSelect = await screen.findByLabelText('Workspace session');
    const ipSelect = await screen.findByLabelText('IP ID');
    await waitFor(() => {
      expect(sessionSelect).toHaveValue('s1');
      expect(ipSelect).toHaveValue('ip_alpha');
    });

    await act(async () => {
      fireEvent.change(sessionSelect, { target: { value: 's2' } });
      await Promise.resolve();
    });

    await waitFor(() => {
      expect(ipListScopes).toContain('alice/s2');
      expect(ipSelect).toHaveValue('default');
      const optionValues = within(ipSelect).getAllByRole('option').map((option) => option.getAttribute('value'));
      expect(optionValues).toEqual(['default']);
    });

    await act(async () => {
      s2IpList.resolve();
      await Promise.resolve();
      await Promise.resolve();
    });

    await waitFor(() => {
      const optionValues = within(ipSelect).getAllByRole('option').map((option) => option.getAttribute('value'));
      expect(optionValues).toEqual(['default', 'ip_beta']);
    });
  });

  it('clears stale owner IP options before the authenticated owner roster resolves', async () => {
    const { usersMe, bobIpList } = installDeferredOwnerRebindFetchStub();
    await mountApp();

    await act(async () => {
      await Promise.resolve();
      await Promise.resolve();
      usersMe.resolve();
      await Promise.resolve();
      await Promise.resolve();
    });

    const ipSelect = await screen.findByLabelText('IP ID');
    await waitFor(() => {
      expect((window as AnyWindow).ATLAS_USER_SESSION_ID).toBe('bob');
      expect((window as AnyWindow).IP_OPTIONS).toEqual(['default']);
      const optionValues = within(ipSelect).getAllByRole('option').map((option) => option.getAttribute('value'));
      expect(optionValues).toEqual(['default']);
    });

    await act(async () => {
      bobIpList.resolve();
      await Promise.resolve();
      await Promise.resolve();
    });
  });

  it('ignores an old roster response after backend context switches workspace scope', async () => {
    let nowMs = 1_000;
    vi.spyOn(Date, 'now').mockImplementation(() => nowMs);
    const { ipListScopes, s1IpList, s2IpList } = installDeferredBackendSyncFetchStub();
    window.history.replaceState(null, '', '/');
    await mountApp();

    const ipSelect = await screen.findByLabelText('IP ID');
    await waitFor(() => {
      expect(ipListScopes).toContain('alice/s1');
    });

    await act(async () => {
      nowMs = 7_000;
      (window as AnyWindow).CONTEXT = { active_session: 'alice/s2/ip_beta/default' };
      window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'CONTEXT' }));
      await Promise.resolve();
      await Promise.resolve();
    });
    expect((window as AnyWindow).ACTIVE_SESSION).toBe('alice/s2/ip_beta/default');

    await act(async () => {
      s1IpList.resolve();
      await Promise.resolve();
      await Promise.resolve();
    });

    const optionValues = within(ipSelect).getAllByRole('option').map((option) => option.getAttribute('value'));
    expect(optionValues).toEqual(['default']);
    expect((window as AnyWindow).IP_OPTIONS).toEqual(['default']);

    await waitFor(() => {
      expect(ipListScopes).toContain('alice/s2');
    });
    await act(async () => {
      s2IpList.resolve();
      await Promise.resolve();
      await Promise.resolve();
    });
    await waitFor(() => {
      const nextOptionValues = within(ipSelect).getAllByRole('option').map((option) => option.getAttribute('value'));
      expect(nextOptionValues).toEqual(['default', 'ip_beta']);
    });
  });
});
