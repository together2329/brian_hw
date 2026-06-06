import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, cleanup, render, screen, waitFor } from '@testing-library/react';
import { useRef, useState } from 'react';
import { useAtlasAuthGate } from '../app-auth-hook';
import { useAtlasSessionSync } from '../app-session-hook';

type AnyWindow = typeof window & Record<string, any>;

const WORKFLOW_DEFAULT = 'default';
const TOP_WORKFLOWS = new Set(['orchestrator', 'rtl-gen', 'ssot-gen', 'tb-gen']);

const jsonResponse = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });

const normalizeSession = (value: unknown): string => String(value || '').trim();

function splitSessionNamespace(session: unknown): any {
  const parts = normalizeSession(session).split('/').filter(Boolean);
  if (parts.length >= 4) {
    return { sessionId: parts[0], workspaceSession: parts[1], ipId: parts[2], workflow: parts[3] };
  }
  if (parts.length === 3) {
    return { sessionId: parts[0], workspaceSession: WORKFLOW_DEFAULT, ipId: parts[1], workflow: parts[2] };
  }
  if (parts.length === 2) {
    return { sessionId: parts[0], workspaceSession: parts[1], ipId: '', workflow: '' };
  }
  if (parts.length === 1) {
    return { sessionId: parts[0], workspaceSession: WORKFLOW_DEFAULT, ipId: '', workflow: '' };
  }
  return { sessionId: '', workspaceSession: '', ipId: '', workflow: '' };
}

function namespaceFor(sessionId: unknown, ipId: unknown, workflow: unknown): string {
  const parts = normalizeSession(sessionId).split('/').filter(Boolean);
  const owner = parts[0] || WORKFLOW_DEFAULT;
  const workspaceSession = parts[1] || WORKFLOW_DEFAULT;
  return `${owner}/${workspaceSession}/${normalizeSession(ipId) || WORKFLOW_DEFAULT}/${normalizeSession(workflow) || WORKFLOW_DEFAULT}`;
}

function deferredJsonResponse(body: unknown) {
  let resolveResponse: (() => void) | null = null;
  const response = new Promise<Response>((resolve) => {
    resolveResponse = () => resolve(jsonResponse(body));
  });
  return {
    resolve: () => {
      if (resolveResponse) resolveResponse();
    },
    response,
  };
}

function installWindowState(owner = 'alice', workspaceSession = 's1', ip = 'ip_alpha') {
  const w = window as AnyWindow;
  w.ATLAS_USER = { username: owner };
  w.ATLAS_USER_SESSION_ID = owner;
  w.ATLAS_WORKSPACE_SESSION_ID = workspaceSession;
  w.ACTIVE_SESSION = `${owner}/${workspaceSession}/${ip}/rtl-gen`;
  w.ACTIVE_IP = ip;
  w.IP_OPTIONS = [WORKFLOW_DEFAULT, ip];
  w.CONTEXT = {};
  w.backend = { switchSession: vi.fn(), connect: vi.fn() };
  w.atlasData = { refreshHealth: vi.fn() };
}

function SessionSyncHarness() {
  const initialUrlNamespaceRef = useRef('');
  const userPickAtRef = useRef(0);
  const [activeIp, setActiveIp] = useState('ip_alpha');
  const [activeNamespace, setActiveNamespace] = useState('alice/s1/ip_alpha/rtl-gen');
  const [activeSessionId, setActiveSessionId] = useState('alice');
  const [sessionIdOptions, setSessionIdOptions] = useState<string[]>([]);
  const [ipOptions, setIpOptions] = useState<string[]>([WORKFLOW_DEFAULT, 'ip_alpha']);

  useAtlasSessionSync({
    WORKFLOW_DEFAULT,
    TOP_WORKFLOWS,
    authState: 'authed',
    activeIp,
    activeNamespace,
    activeSessionId,
    initialUrlNamespaceRef,
    userPickAtRef,
    loggedInOwner: () => 'alice',
    normalizeSession,
    splitSessionNamespace,
    namespaceFor,
    currentWorkflow: () => 'rtl-gen',
    workflowForExecMode: (workflow: unknown) => normalizeSession(workflow) || WORKFLOW_DEFAULT,
    applySessionMeta: () => ({}),
    syncNamespaceUrl: () => {},
    activateNamespace: () => '',
    setSessionIdOptions,
    setIpOptions,
    setActiveSessionId,
    setActiveNamespace,
    setActiveIp,
  });

  return (
    <>
      <output data-testid="ip-options">{JSON.stringify(ipOptions)}</output>
      <output data-testid="session-options">{JSON.stringify(sessionIdOptions)}</output>
    </>
  );
}

function AuthGateHarness() {
  const authRequiredProbeRef = useRef(0);
  const [authState, setAuthState] = useState('checking');
  const [activeNamespace, setActiveNamespace] = useState('bob/s1/ip_alpha/rtl-gen');
  const [activeIp, setActiveIp] = useState('ip_alpha');
  const [ipOptions, setIpOptions] = useState<string[]>([WORKFLOW_DEFAULT, 'ip_alpha']);

  useAtlasAuthGate({
    WORKFLOW_DEFAULT,
    authState,
    execMode: 'single-worker',
    authRequiredProbeRef,
    normalizeSession,
    splitSessionNamespace,
    setBootSteps: () => {},
    setAuthState,
    setActiveSessionId: () => {},
    setActiveNamespace,
    setActiveIp,
    setIpOptions,
    setRunMode: () => {},
    setExecMode: () => {},
  });

  return (
    <>
      <output data-testid="auth-state">{authState}</output>
      <output data-testid="active-namespace">{activeNamespace}</output>
      <output data-testid="active-ip">{activeIp}</output>
      <output data-testid="ip-options">{JSON.stringify(ipOptions)}</output>
    </>
  );
}

describe('App IP roster isolation guards', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
    window.history.replaceState(null, '', '/');
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it('ignores an old workspace IP roster response after backend context switches scope', async () => {
    installWindowState('alice', 's1', 'ip_alpha');
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
    const ipListScopes: string[] = [];
    global.fetch = vi.fn(async (input: RequestInfo | URL) => {
      const url = new URL(String(input), 'http://localhost');
      if (url.pathname === '/api/session/list') {
        return jsonResponse({
          sessions: [
            { session: 'alice/s1/ip_alpha/rtl-gen' },
            { session: 'alice/s2/ip_beta/default' },
          ],
        });
      }
      if (url.pathname === '/api/ip/list') {
        const scope = normalizeSession(url.searchParams.get('session_id') || '');
        ipListScopes.push(scope);
        if (scope === 'alice/s1') return s1IpList.response;
        if (scope === 'alice/s2') {
          return s2IpList.response;
        }
      }
      return jsonResponse({});
    }) as unknown as typeof fetch;

    render(<SessionSyncHarness />);
    await waitFor(() => expect(ipListScopes).toContain('alice/s1'), { timeout: 1000 });

    await act(async () => {
      (window as AnyWindow).CONTEXT = { active_session: 'alice/s2/ip_beta/default' };
      window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'CONTEXT' }));
      await Promise.resolve();
    });

    await act(async () => {
      s1IpList.resolve();
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(JSON.parse(screen.getByTestId('ip-options').textContent || '[]')).toEqual([WORKFLOW_DEFAULT]);
    expect((window as AnyWindow).IP_OPTIONS).toEqual([WORKFLOW_DEFAULT]);

    await waitFor(() => expect(ipListScopes).toContain('alice/s2'));
    await act(async () => {
      s2IpList.resolve();
      await Promise.resolve();
      await Promise.resolve();
    });
  });

  it('clears stale IP roster options when auth rebinds to a different owner', async () => {
    installWindowState('bob', 's1', 'ip_alpha');
    localStorage.setItem('atlasActiveSession', 'bob/s1/ip_alpha/rtl-gen');
    global.fetch = vi.fn(async (input: RequestInfo | URL) => {
      const url = new URL(String(input), 'http://localhost');
      if (url.pathname === '/api/users/me') return jsonResponse({ user: { username: 'alice' } });
      if (url.pathname === '/api/session/activate') return jsonResponse({ ok: true });
      if (url.pathname === '/api/pipeline/run_policy') {
        return jsonResponse({ run_mode: 'engineering', exec_mode: 'single-worker' });
      }
      return jsonResponse({});
    }) as unknown as typeof fetch;

    render(<AuthGateHarness />);

    await waitFor(() => expect(screen.getByTestId('auth-state')).toHaveTextContent('authed'));
    expect(JSON.parse(screen.getByTestId('ip-options').textContent || '[]')).toEqual([WORKFLOW_DEFAULT]);
    expect((window as AnyWindow).IP_OPTIONS).toEqual([WORKFLOW_DEFAULT]);
    expect(screen.getByTestId('active-namespace')).toHaveTextContent('alice/s1/default/default');
    expect(screen.getByTestId('active-ip')).toHaveTextContent(WORKFLOW_DEFAULT);
  });
});
