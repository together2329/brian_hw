import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, cleanup, render } from '@testing-library/react';
import { useRef, useState } from 'react';
import { useAtlasSessionSync } from '../app-session-hook';

type AnyWindow = typeof window & Record<string, any>;

const WORKFLOW_DEFAULT = 'default';
const TOP_WORKFLOWS = new Set(['orchestrator', 'rtl-gen', 'ssot-gen', 'tb-gen']);

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

const jsonResponse = (body: unknown) =>
  new Response(JSON.stringify(body), { status: 200, headers: { 'Content-Type': 'application/json' } });

let backendHandlers: Record<string, Array<(m: any) => void>> = {};

function installWorkerBackend(owner = 'alice', namespace = 'alice/s1/mctp/default') {
  const w = window as AnyWindow;
  backendHandlers = {};
  w.ATLAS_USER = { username: owner };
  w.ATLAS_USER_SESSION_ID = owner;
  w.ATLAS_WORKSPACE_SESSION_ID = 's1';
  w.ACTIVE_SESSION = namespace;
  w.CONTEXT = {};
  w.backend = {
    subscribe: (type: string, fn: (m: any) => void) => {
      (backendHandlers[type] = backendHandlers[type] || []).push(fn);
      // Real unsubscribe semantics — the hook re-subscribes when its deps
      // change during mount, so a no-op here would accumulate stale handlers
      // and fire the follow path once per accumulated copy.
      return () => {
        backendHandlers[type] = (backendHandlers[type] || []).filter((h) => h !== fn);
      };
    },
    switchSession: vi.fn(),
  };
}

const fireWorkspaceChanged = async (payload: any) => {
  await act(async () => {
    (backendHandlers['workspace_changed'] || []).forEach((fn) => fn(payload));
    await Promise.resolve();
  });
};

// The hook fires the existing one-shot URL/localStorage→backend handshake on
// mount (it calls activateNamespace once for the CURRENT namespace). Flush and
// discard that call so assertions below isolate the worker-follow path.
const settleMount = async (activateSpy: ReturnType<typeof vi.fn>) => {
  await act(async () => { await Promise.resolve(); });
  activateSpy.mockClear();
};

function FollowHarness({ activateSpy }: { activateSpy: (...args: any[]) => any }) {
  const initialUrlNamespaceRef = useRef('');
  const userPickAtRef = useRef(0);
  const [activeIp, setActiveIp] = useState('mctp');
  const [activeNamespace, setActiveNamespace] = useState('alice/s1/mctp/default');
  const [activeSessionId, setActiveSessionId] = useState('alice');
  const [, setSessionIdOptions] = useState<string[]>([]);
  const [, setIpOptions] = useState<string[]>([WORKFLOW_DEFAULT, 'mctp']);

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
    currentWorkflow: () => 'default',
    workflowForExecMode: (workflow: unknown) => normalizeSession(workflow) || WORKFLOW_DEFAULT,
    applySessionMeta: () => ({}),
    syncNamespaceUrl: () => {},
    activateNamespace: activateSpy,
    setSessionIdOptions,
    setIpOptions,
    setActiveSessionId,
    setActiveNamespace,
    setActiveIp,
  });

  return null;
}

describe('worker-initiated workflow switch follows via activate', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();
    window.history.replaceState(null, '', '/');
    // The roster guard collapses an IP the backend roster doesn't confirm —
    // return the harness IP so refreshTopTargets keeps ACTIVE_SESSION intact.
    global.fetch = vi.fn(async (input: RequestInfo | URL) => {
      const url = new URL(String(input), 'http://localhost');
      if (url.pathname === '/api/ip/list') {
        return jsonResponse({ items: [{ name: 'mctp' }], count: 1 });
      }
      if (url.pathname === '/api/session/list') {
        return jsonResponse({ sessions: [] });
      }
      return jsonResponse({});
    }) as unknown as typeof fetch;
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it('follows a worker workspace_changed announcing a new session key', async () => {
    installWorkerBackend();
    const activateSpy = vi.fn();
    render(<FollowHarness activateSpy={activateSpy} />);
    await settleMount(activateSpy);

    await fireWorkspaceChanged({
      workspace: 'ssot-gen',
      prev: 'default',
      ip: 'mctp',
      session: 'alice/s1/mctp/ssot-gen',
      source: 'worker/workflow-switch',
    });

    expect(activateSpy).toHaveBeenCalledWith(
      'alice/s1', 'mctp', 'ssot-gen', true, { preserveRunning: true }
    );
  });

  it('ignores UI-initiated (non-worker) workspace_changed events', async () => {
    installWorkerBackend();
    const activateSpy = vi.fn();
    render(<FollowHarness activateSpy={activateSpy} />);
    await settleMount(activateSpy);

    await fireWorkspaceChanged({
      workspace: 'ssot-gen',
      ip: 'mctp',
      session: 'alice/s1/mctp/ssot-gen',
      source: 'api/session/activate',
    });

    expect(activateSpy).not.toHaveBeenCalled();
  });

  it('does not re-activate when the announced key matches the live one', async () => {
    installWorkerBackend('alice', 'alice/s1/mctp/ssot-gen');
    const activateSpy = vi.fn();
    render(<FollowHarness activateSpy={activateSpy} />);
    await settleMount(activateSpy);

    await fireWorkspaceChanged({
      workspace: 'ssot-gen',
      ip: 'mctp',
      session: 'alice/s1/mctp/ssot-gen',
      source: 'worker/workflow-switch',
    });

    expect(activateSpy).not.toHaveBeenCalled();
  });

  it('never follows a cross-owner session key', async () => {
    installWorkerBackend();
    const activateSpy = vi.fn();
    render(<FollowHarness activateSpy={activateSpy} />);
    await settleMount(activateSpy);

    await fireWorkspaceChanged({
      workspace: 'ssot-gen',
      ip: 'stolen',
      session: 'bob/s1/stolen/ssot-gen',
      source: 'worker/workflow-switch',
    });

    expect(activateSpy).not.toHaveBeenCalled();
  });
});
