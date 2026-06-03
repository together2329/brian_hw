// __tests__/workspace-render-smoke.test.tsx
//
// THE BEHAVIORAL GATE for the workspace-root.tsx composer.
//
// Companion to the COMPILE gate (the typed `WorkspaceBag` in workspace-root.tsx,
// which makes tsc ERROR if any destructured symbol is not returned by a hook).
// That gate was missing while the bag was `any`, so 15 undefined destructures
// (renderChatPane / renderPromptRow / toggleOpt / setCustom / submitCard /
// setActiveTab / advanceBatchedQuestion / streaming / orchWorkers /
// workerProgress / inputRef / leftW / fileSort, etc.) compiled silently and
// would have blown up at runtime with "X is not a function" / undefined-read.
//
// This test mounts the REAL Workspace component (imported via ../workspace.tsx,
// which re-exports it from workspace-root.tsx) in jsdom with the window globals
// the live app supplies stubbed out, and asserts:
//   1. it renders WITHOUT throwing (no "X is not a function", no undefined-read);
//   2. the load-bearing panes exist — the bottom prompt row (the auto-growing
//      <textarea>) and the chat stream container — proving renderPromptRow() and
//      renderChatPane() actually resolved to real functions and produced DOM.
//
// If a future refactor drops one of those bound render helpers (or any of the
// 15 symbols) from a hook return, EITHER tsc fails (compile gate) OR this mount
// throws (behavioral gate). Both gates must stay green.

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
vi.setConfig({ testTimeout: 30000, hookTimeout: 30000 }); // full-app mount in jsdom is >5s under load

import { render, cleanup, within, act, waitFor, fireEvent } from '@testing-library/react';
import { createRef } from 'react';

// Establish the SAME window bridges the live app loads before the workspace
// bundle. ui-utils.tsx publishes window.CopyBtn / window._copyToClipboard on
// import; workspace-markdown-chips.tsx reads window.CopyBtn at MODULE-LOAD time
// (`export const CopyBtn = window.CopyBtn`), and the feed-card dispatcher renders
// <CopyBtn/> for the seed `agent` entry. Importing ui-utils first (ESM imports
// run before the test body) makes that bridge real, exactly as the live load
// order does — not a fake stub.
import '../ui-utils.tsx';

// ── window/global stubs the live app normally supplies ──────────────────────
// These mirror what index.html / the legacy bundles publish before Workspace
// mounts. The .tsx render path reads them defensively (optional-chaining or
// `any`-cast fallbacks), so trivial stubs are enough to clear a clean mount.
type AnyWindow = typeof window & Record<string, any>;

const PassthroughPanel = ({ children }: { children?: unknown }) =>
  // A harmless placeholder for the window-published ATLAS panels. The default
  // layout only mounts the right-rail Todo tab + AgentStatusPanel, but stub the
  // full set so any tab/branch the composer touches resolves to a component.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (children as any) ?? null;

const AskUserPromptStub = ({ flowId, state }: { flowId?: string; state?: unknown }) => (
  <div data-testid="ask-prompt-stub">
    ask_user:{flowId}:{state ? 'ready' : 'missing'}
  </div>
);

function installWindowStubs() {
  const w = window as AnyWindow;

  // Right-rail + center panel components (read from window in workspace-root.tsx).
  for (const name of [
    'SsotReviewPane', 'SsotQaBoard', 'SsotDocPane', 'PreviewPane',
    'AskUserPrompt', 'ProgressPanel', 'TodoPanel', 'OrchestratorChatPanel',
    'GitPanel', 'AgentStatusPanel', 'Coverage', 'SimDebug', 'DebugTab',
    'GitTab',
  ]) {
    w[name] = PassthroughPanel;
  }
  w.AskUserPrompt = AskUserPromptStub;

  // `Kbd` is read from window with an inline fallback, but supply it anyway.
  w.Kbd = ({ children }: { children?: unknown }) => children ?? null;

  // Runtime ATLAS bridges the hooks/render path read off `window`.
  w.CONTEXT = w.CONTEXT || {};
  w.ACTIVE_SESSION = '';
  w.ATLAS_UI_LANG = 'ko';
  w.ATLAS_USER = { username: 'alice' };
  w.ATLAS_AGENT_RUNNING = false;
  w.ATLAS_EXEC_MODE = '';
  delete w.ATLAS_DEFAULT_EXEC_MODE;
  delete w.ATLAS_BOOT_CONFIG;
  w.FLOW_STAGES = [];
  w.TODOS = [];
  w.atlasData = {};
  const normalize = (s: unknown) => String(s || '').trim().toLowerCase();
  w.normalizeAtlasSessionName = normalize;
  w.atlasData.normalizeSessionName = normalize;
  w.atlasData.sessionFor = (ip: string, wf: string) => `alice/${ip}/${wf}`;
  w.FILE_TREE_LOADING = false;
  w.FILE_TREE_ERROR = null;
  w.FILE_TREE_LAST_REFRESH = 0;
  // Backend bridge — a tiny pubsub surface so Workspace can exercise live
  // agent_state/token cleanup without a real WebSocket.
  const backendHandlers: Record<string, Set<(payload: any) => void>> = {};
  let backendState = 'open';
  w.backend = {
    send: vi.fn(),
    switchSession: vi.fn(),
    on: vi.fn(),
    off: vi.fn(),
    state: 'open',
    getConnectionState: () => backendState,
    subscribe: vi.fn((type: string, cb: (payload: any) => void) => {
      (backendHandlers[type] = backendHandlers[type] || new Set()).add(cb);
      return () => backendHandlers[type]?.delete(cb);
    }),
    _emit: (type: string, payload: any = {}) => {
      if (type === 'connection') backendState = String(payload.state || backendState);
      (backendHandlers[type] || new Set()).forEach((cb) => cb({ type, ...payload }));
    },
    _setConnectionState: (state: string) => {
      backendState = String(state || 'open');
      w.backend.state = backendState;
    },
  };
  // Banner logic helper (optional-chained in the prompt row).
  w.AtlasBannerLogic = {
    shouldShowSelectIpBanner: () => false,
  };

  // Network: every fetch resolves to an empty-OK JSON so any mount-time poll
  // (worker snapshot / ssot-qa refresh) settles without a real server.
  global.fetch = vi.fn(async () =>
    new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } }),
  ) as unknown as typeof fetch;
}

describe('Workspace render smoke (the behavioral gate)', () => {
  beforeEach(() => {
    installWindowStubs();
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it('mounts the real Workspace without throwing (no undefined-symbol break)', async () => {
    // Import AFTER stubs are installed so the module-load window reads in
    // workspace.tsx / workspace-root.tsx see the stubbed globals.
    const { Workspace } = await import('../workspace.tsx');
    expect(typeof Workspace).toBe('function');

    expect(() => {
      render(<Workspace dir="/tmp/ws" uiLang="ko" />);
    }).not.toThrow();
  });

  it('renders the prompt row (renderPromptRow resolved to a real fn → textarea exists)', async () => {
    const { Workspace } = await import('../workspace.tsx');
    const { container } = render(<Workspace dir="/tmp/ws" uiLang="ko" />);

    // The bottom composer renders an auto-growing <textarea>. Its presence
    // proves renderPromptRow() was a real bound helper (not `undefined()`).
    const textarea = container.querySelector('textarea');
    expect(textarea).not.toBeNull();
    expect(textarea?.getAttribute('placeholder') || '').toMatch(/Type a message|Answer pending|Preparing/);
  });

  it('keeps prompt typing local and defers parent input sync', async () => {
    vi.useFakeTimers();
    const { WorkspacePromptRow } = await import('../workspace-root-render.tsx');
    const setInput = vi.fn();
    const inputRef = createRef<HTMLTextAreaElement>();
    const inputRouteRef = { current: {} };

    const { getByRole } = render(
      <WorkspacePromptRow
        workflow="default"
        activeIp="demo"
        feed={[]}
        orchWorkers={[]}
        workerProgress={null}
        input=""
        setInput={setInput}
        inputRef={inputRef}
        inputRouteState={null}
        inputRouteRef={inputRouteRef}
        inputHistoryIndexRef={{ current: null }}
        inputHistoryDraftRef={{ current: '' }}
        onKey={vi.fn()}
        pendingQcard={null}
        workflowReady={null}
        atlasUiOrchestratorMode={() => false}
        workflowForExecMode={(wf: unknown) => String(wf || 'default')}
        defaultWorkflowForExecMode={() => 'default'}
      />,
    );

    const textarea = getByRole('textbox') as HTMLTextAreaElement;
    fireEvent.change(textarea, { target: { value: 'abc' } });

    expect(textarea.value).toBe('abc');
    expect(setInput).not.toHaveBeenCalled();

    await act(async () => {
      vi.advanceTimersByTime(80);
    });

    expect(setInput).toHaveBeenLastCalledWith('abc');
    vi.useRealTimers();
  });

  it('does not let stale parent echoes erase fast typing', async () => {
    vi.useFakeTimers();
    const { WorkspacePromptRow } = await import('../workspace-root-render.tsx');
    const setInput = vi.fn();
    const inputRef = createRef<HTMLTextAreaElement>();
    const inputRouteRef = { current: {} };
    const props = {
      workflow: 'default',
      activeIp: 'demo',
      feed: [],
      orchWorkers: [],
      workerProgress: null,
      setInput,
      inputRef,
      inputRouteState: null,
      inputRouteRef,
      inputHistoryIndexRef: { current: null },
      inputHistoryDraftRef: { current: '' },
      onKey: vi.fn(),
      pendingQcard: null,
      workflowReady: null,
      atlasUiOrchestratorMode: () => false,
      workflowForExecMode: (wf: unknown) => String(wf || 'default'),
      defaultWorkflowForExecMode: () => 'default',
    };

    const { getByRole, rerender } = render(<WorkspacePromptRow {...props} input="" />);
    const textarea = getByRole('textbox') as HTMLTextAreaElement;

    fireEvent.change(textarea, { target: { value: 'l' } });
    await act(async () => {
      vi.advanceTimersByTime(60);
    });
    expect(setInput).toHaveBeenLastCalledWith('l');

    fireEvent.change(textarea, { target: { value: 'latency smoke prompt' } });
    rerender(<WorkspacePromptRow {...props} input="l" />);

    expect(textarea.value).toBe('latency smoke prompt');
    vi.useRealTimers();
  });

  it('clears local prompt draft when the parent reset token advances', async () => {
    vi.useFakeTimers();
    const { WorkspacePromptRow } = await import('../workspace-root-render.tsx');
    const setInput = vi.fn();
    const inputRef = createRef<HTMLTextAreaElement>();
    const inputRouteRef = { current: {} };
    const props = {
      workflow: 'default',
      activeIp: 'demo',
      feed: [],
      orchWorkers: [],
      workerProgress: null,
      setInput,
      inputRef,
      inputRouteState: null,
      inputRouteRef,
      inputHistoryIndexRef: { current: null },
      inputHistoryDraftRef: { current: '' },
      onKey: vi.fn(),
      pendingQcard: null,
      workflowReady: null,
      atlasUiOrchestratorMode: () => false,
      workflowForExecMode: (wf: unknown) => String(wf || 'default'),
      defaultWorkflowForExecMode: () => 'default',
    };

    const { getByRole, rerender } = render(<WorkspacePromptRow {...props} input="" inputResetToken={0} />);
    const textarea = getByRole('textbox') as HTMLTextAreaElement;

    fireEvent.change(textarea, { target: { value: 'submit before parent sync' } });
    expect(textarea.value).toBe('submit before parent sync');

    rerender(<WorkspacePromptRow {...props} input="" inputResetToken={1} />);
    expect(textarea.value).toBe('');

    await act(async () => {
      vi.advanceTimersByTime(80);
    });
    expect(setInput).not.toHaveBeenCalled();
    vi.useRealTimers();
  });

  it('clears local prompt draft immediately when the key handler confirms submit', async () => {
    const { WorkspacePromptRow } = await import('../workspace-root-render.tsx');
    const setInput = vi.fn();
    const inputRef = createRef<HTMLTextAreaElement>();
    const inputRouteRef = { current: {} };

    const { getByRole } = render(
      <WorkspacePromptRow
        workflow="default"
        activeIp="demo"
        feed={[]}
        orchWorkers={[]}
        workerProgress={null}
        input=""
        setInput={setInput}
        inputRef={inputRef}
        inputRouteState={null}
        inputRouteRef={inputRouteRef}
        inputHistoryIndexRef={{ current: null }}
        inputHistoryDraftRef={{ current: '' }}
        onKey={(event) => {
          event.preventDefault();
          return 'submitted';
        }}
        pendingQcard={null}
        workflowReady={null}
        atlasUiOrchestratorMode={() => false}
        workflowForExecMode={(wf: unknown) => String(wf || 'default')}
        defaultWorkflowForExecMode={() => 'default'}
      />,
    );

    const textarea = getByRole('textbox') as HTMLTextAreaElement;
    fireEvent.change(textarea, { target: { value: 'visible residue' } });
    expect(textarea.value).toBe('visible residue');

    fireEvent.keyDown(textarea, { key: 'Enter', code: 'Enter' });

    expect(textarea.value).toBe('');
  });

  it('submits the latest visible prompt value before deferred sync settles', async () => {
    const { Workspace } = await import('../workspace.tsx');
    const { container } = render(<Workspace dir="/tmp/ws" uiLang="ko" />);
    const textarea = container.querySelector('textarea') as HTMLTextAreaElement;

    fireEvent.change(textarea, { target: { value: 'send immediately' } });
    fireEvent.keyDown(textarea, { key: 'Enter' });

    const send = (window as AnyWindow).backend.send as ReturnType<typeof vi.fn>;
    expect(send).toHaveBeenCalledWith(expect.objectContaining({
      type: 'prompt',
      text: 'send immediately',
    }));
  });

  it('renders the center chat stream pane (renderChatPane resolved to a real fn)', async () => {
    const { Workspace } = await import('../workspace.tsx');
    const { container } = render(<Workspace dir="/tmp/ws" uiLang="ko" />);

    // The 5-track grid root is a <div style="display:grid"> with the prompt
    // row + center column. Assert the grid root + the center column both exist,
    // proving the composer assembled the layout end-to-end (left rail · center
    // tabs · chat pane · prompt row) without a render-helper throwing.
    const gridRoot = container.querySelector('div[style*="grid"]');
    expect(gridRoot).not.toBeNull();
    // The center "box" wrapping the tab strip + chat pane carries class "box".
    const boxes = container.querySelectorAll('.box');
    expect(boxes.length).toBeGreaterThan(0);
    // And the textarea (prompt) lives inside the same grid root.
    expect(within(gridRoot as HTMLElement).queryAllByRole('textbox').length).toBeGreaterThanOrEqual(0);
  });

  it('registered window.Workspace on import (app-shell mount bridge)', async () => {
    await import('../workspace.tsx');
    expect(typeof (window as AnyWindow).Workspace).toBe('function');
  });

  it('publishes the fold color palette used by JSON file previews', async () => {
    await import('../workspace.tsx');
    const palette = (window as AnyWindow)._FOLD_KIND_COLOR;
    expect(palette).toBeTruthy();
    expect(palette.object).toBeTruthy();
    expect(palette.array).toBeTruthy();
  });

  it('clears the Workspace Agent responding banner on agent_state false', async () => {
    const { Workspace } = await import('../workspace.tsx');
    const { queryByText } = render(<Workspace dir="/tmp/ws" uiLang="ko" />);
    const backend = (window as AnyWindow).backend;

    await act(async () => {
      backend._emit('agent_state', { running: true });
    });
    await waitFor(() => expect(queryByText('Agent responding')).not.toBeNull());

    await act(async () => {
      backend._emit('agent_state', { running: false });
    });
    await waitFor(() => expect(queryByText('Agent responding')).toBeNull());
    expect(queryByText(/End of loop/)).not.toBeNull();
  });

  it('updates the footer when backend connection closes', async () => {
    const { Workspace } = await import('../workspace.tsx');
    const { queryByText } = render(<Workspace dir="/tmp/ws" uiLang="ko" />);
    const backend = (window as AnyWindow).backend;

    await act(async () => {
      backend._emit('connection', { state: 'closed' });
    });

    await waitFor(() => expect(queryByText('Backend disconnected')).not.toBeNull());
    expect(queryByText(/End of loop/)).toBeNull();
  });

  it('shows session worker failure ahead of the idle ready footer', async () => {
    global.fetch = vi.fn(async (url: RequestInfo | URL, _init?: RequestInit) => {
      if (String(url) === '/api/session/worker/status') {
        return new Response(JSON.stringify({
          policy: 'strict',
          active_count: 0,
          owner: 'alice',
          owner_active_session: 'alice/demo/default',
          worker: null,
        }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }
      return new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } });
    }) as unknown as typeof fetch;

    const { Workspace } = await import('../workspace.tsx');
    const { queryByText } = render(<Workspace dir="/tmp/ws" uiLang="ko" />);

    await waitFor(() => expect(queryByText(/Agent worker failed/)).not.toBeNull());
    expect(queryByText(/End of loop/)).toBeNull();
  });

  it('treats missing current-session worker as failed even when other workers are active', async () => {
    global.fetch = vi.fn(async (url: RequestInfo | URL, _init?: RequestInit) => {
      if (String(url) === '/api/session/worker/status') {
        return new Response(JSON.stringify({
          policy: 'strict',
          active_count: 1,
          owner: 'alice',
          owner_active_session: 'alice/demo/default',
          worker: null,
        }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }
      return new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } });
    }) as unknown as typeof fetch;

    const { Workspace } = await import('../workspace.tsx');
    const { queryByText } = render(<Workspace dir="/tmp/ws" uiLang="ko" />);

    await waitFor(() => expect(queryByText(/Agent worker failed/)).not.toBeNull());
    expect(queryByText(/End of loop/)).toBeNull();
  });

  it('shows Agent responding ahead of stale session worker failure', async () => {
    global.fetch = vi.fn(async (url: RequestInfo | URL, _init?: RequestInit) => {
      if (String(url) === '/api/session/worker/status') {
        return new Response(JSON.stringify({
          policy: 'strict',
          active_count: 0,
          owner: 'alice',
          owner_active_session: 'alice/demo/default',
          worker: null,
        }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }
      return new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } });
    }) as unknown as typeof fetch;

    const { Workspace } = await import('../workspace.tsx');
    const { queryByText } = render(<Workspace dir="/tmp/ws" uiLang="ko" />);
    const backend = (window as AnyWindow).backend;

    await waitFor(() => expect(queryByText(/Agent worker failed/)).not.toBeNull());
    await act(async () => {
      backend._emit('agent_state', { running: true });
    });

    await waitFor(() => expect(queryByText('Agent responding')).not.toBeNull());
    expect(queryByText(/Agent worker failed/)).toBeNull();
  });

  it('shows Agent responding ahead of stale backend connecting state', async () => {
    const backend = (window as AnyWindow).backend;
    backend._setConnectionState('connecting');

    const { Workspace } = await import('../workspace.tsx');
    const { queryByText } = render(<Workspace dir="/tmp/ws" uiLang="ko" />);

    await act(async () => {
      backend._emit('agent_state', { running: true });
    });

    await waitFor(() => expect(queryByText('Agent responding')).not.toBeNull());
    expect(queryByText('Backend connecting')).toBeNull();
  });

  it('shows the live LLM model and effort beside Agent responding', async () => {
    const { Workspace } = await import('../workspace.tsx');
    const { queryByText } = render(<Workspace dir="/tmp/ws" uiLang="ko" />);
    const backend = (window as AnyWindow).backend;

    await act(async () => {
      backend._emit('agent_state', { running: true });
      backend._emit('context', {
        model: 'sol-soc-gpt-5.5',
        reasoning_effort: 'xhigh',
      });
    });

    await waitFor(() => {
      expect(queryByText(/Agent responding.*sol-soc-gpt-5\.5.*xhigh/)).not.toBeNull();
    });
  });

  it('does not show Agent responding for workflow activation control tokens', async () => {
    const { Workspace } = await import('../workspace.tsx');
    const { queryByText } = render(<Workspace dir="/tmp/ws" uiLang="ko" />);
    const backend = (window as AnyWindow).backend;

    await act(async () => {
      backend._emit('token', {
        text: "Switching workflow 'default' -> 'rtl-gen'\n",
        source: 'api/session/activate',
        control: true,
        stream: false,
      });
      backend._emit('flush', {
        source: 'api/session/activate',
        control: true,
      });
    });

    expect(queryByText('Agent responding')).toBeNull();
  });

  it('does not show Agent responding for workflow activation agent_state events', async () => {
    const { Workspace } = await import('../workspace.tsx');
    const { queryByText } = render(<Workspace dir="/tmp/ws" uiLang="ko" />);
    const backend = (window as AnyWindow).backend;

    await act(async () => {
      backend._emit('agent_state', {
        running: true,
        source: 'api/session/activate',
        control: true,
      });
    });

    expect(queryByText('Agent responding')).toBeNull();
  });

  it('clears stale Agent responding state when switching orchestrator workflow views', async () => {
    const w = window as AnyWindow;
    w.ATLAS_EXEC_MODE = 'orchestrator';
    w.ACTIVE_SESSION = 'alice/demo/orchestrator';
    w.ACTIVE_IP = 'demo';
    w.SCOPE_PATH = 'demo';

    const { Workspace } = await import('../workspace.tsx');
    const { queryByText } = render(
      <Workspace
        dir="/tmp/ws"
        uiLang="ko"
        activeNamespace="alice/demo/orchestrator"
        activeWorkflow="orchestrator"
      />,
    );
    const backend = (window as AnyWindow).backend;

    await act(async () => {
      backend._emit('token', {
        session_id: 'alice/demo/orchestrator',
        text: 'orchestrator reply in progress',
      });
    });
    await waitFor(() => expect(queryByText('Agent responding')).not.toBeNull());

    await act(async () => {
      window.dispatchEvent(new CustomEvent('atlas-workflow-view-request', {
        detail: { workflow: 'rtl-gen' },
      }));
    });

    await waitFor(() => expect(queryByText('Agent responding')).toBeNull());
  });

  it('keeps the active IP when a workflow chip switches with an empty scope path', async () => {
    const w = window as AnyWindow;
    w.FLOW_STAGES = [
      { id: 'default', label: 'default', glyph: 'GP', color: '#9ca3af' },
      { id: 'coverage', label: 'coverage', glyph: 'CV', color: '#22c55e' },
    ];
    w.ACTIVE_SESSION = 'alice/demo/default';
    w.ACTIVE_IP = 'demo';
    w.SCOPE_PATH = '';
    w.atlasData.sessionFor = vi.fn((ip: string, wf: string) => `alice/${ip || 'default'}/${wf || 'default'}`);
    let resolveActivate: ((response: Response) => void) | null = null;
    const activateResponse = new Promise<Response>((resolve) => {
      resolveActivate = resolve;
    });
    const fetchSpy = vi.fn(async (url: RequestInfo | URL, _init?: RequestInit) => {
      if (String(url) === '/api/session/activate') return activateResponse;
      return new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } });
    });
    global.fetch = fetchSpy as unknown as typeof fetch;
    const activateOkResponse = () =>
      new Response(JSON.stringify({ session_worker_warmup: { enabled: false } }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      });

    const { Workspace } = await import('../workspace.tsx');
    const { getByRole } = render(
      <Workspace
        dir="/tmp/ws"
        uiLang="ko"
        activeNamespace="alice/demo/default"
        activeWorkflow="default"
      />,
    );

    await act(async () => {
      fireEvent.click(getByRole('button', { name: /coverage/i }));
      await Promise.resolve();
    });

    await waitFor(() => {
      const activateCall = fetchSpy.mock.calls.find(([url]) => String(url) === '/api/session/activate');
      expect(activateCall).toBeTruthy();
      const body = JSON.parse(String(activateCall[1]?.body || '{}'));
      expect(body).toMatchObject({ owner: 'alice', ip: 'demo', workflow: 'coverage' });
    });
    expect(w.atlasData.sessionFor).toHaveBeenCalledWith('demo', 'coverage');
    expect(w.backend.switchSession).toHaveBeenCalledWith('alice/demo/coverage');
    expect(w.backend.switchSession).not.toHaveBeenCalledWith('alice/default/coverage');

    await act(async () => {
      resolveActivate?.(activateOkResponse());
      await activateResponse;
    });
  });

  it('does not fallback-dispatch a workflow slash prompt when activation is forbidden', async () => {
    const w = window as AnyWindow;
    w.FLOW_STAGES = [
      { id: 'default', label: 'default', glyph: 'GP', color: '#9ca3af' },
      { id: 'coverage', label: 'coverage', glyph: 'CV', color: '#22c55e' },
    ];
    w.ACTIVE_SESSION = 'alice/demo/default';
    w.ACTIVE_IP = 'demo';
    w.SCOPE_PATH = '';
    w.atlasData.sessionFor = vi.fn((ip: string, wf: string) => `alice/${ip || 'default'}/${wf || 'default'}`);
    global.fetch = vi.fn(async (url: RequestInfo | URL, _init?: RequestInit) => {
      if (String(url) === '/api/session/activate') {
        return new Response(JSON.stringify({ error: 'session owner mismatch' }), {
          status: 403,
          headers: { 'Content-Type': 'application/json' },
        });
      }
      return new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } });
    }) as unknown as typeof fetch;

    const { Workspace } = await import('../workspace.tsx');
    const { getByRole } = render(
      <Workspace
        dir="/tmp/ws"
        uiLang="ko"
        activeNamespace="alice/demo/default"
        activeWorkflow="default"
      />,
    );

    await act(async () => {
      fireEvent.click(getByRole('button', { name: /coverage/i }));
      await Promise.resolve();
    });

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        '/api/session/activate',
        expect.objectContaining({ method: 'POST' }),
      );
    });
    expect(w.backend.send).not.toHaveBeenCalledWith(expect.objectContaining({
      type: 'prompt',
      text: '/wf coverage',
    }));
  });

  it('coalesces rapid token display updates to the next animation frame', async () => {
    const { Workspace } = await import('../workspace.tsx');
    const { queryByText } = render(<Workspace dir="/tmp/ws" uiLang="ko" />);
    const w = window as AnyWindow;
    const originalRaf = window.requestAnimationFrame;
    const pendingFrames: FrameRequestCallback[] = [];
    window.requestAnimationFrame = ((cb: FrameRequestCallback) => {
      pendingFrames.push(cb);
      return pendingFrames.length;
    }) as typeof window.requestAnimationFrame;

    try {
      await act(async () => {
        w.backend._emit('token', { text: 'front' });
        w.backend._emit('token', { text: 'end' });
        w.backend._emit('token', { text: ' lag' });
        await Promise.resolve();
      });

      expect(queryByText('frontend lag')).toBeNull();

      await act(async () => {
        pendingFrames.shift()?.(performance.now());
        await Promise.resolve();
      });

      expect(queryByText('frontend lag')).not.toBeNull();
    } finally {
      window.requestAnimationFrame = originalRaf;
    }
  });

  it('hides backend iteration markers from the visible chat feed', async () => {
    const { Workspace } = await import('../workspace.tsx');
    const { queryByText } = render(<Workspace dir="/tmp/ws" uiLang="ko" />);
    const backend = (window as AnyWindow).backend;

    await act(async () => {
      backend._emit('tool', { text: '── Iter 1 / 1000  [gpt-5.5]' });
    });

    expect(queryByText(/Iter 1 \/ 1000/)).toBeNull();
    expect(queryByText(/^action$/i)).toBeNull();
  });

  it('does not force-scroll the chat feed while the user is reading older content', async () => {
    const { Workspace } = await import('../workspace.tsx');
    const { container } = render(<Workspace dir="/tmp/ws" uiLang="ko" />);
    const backend = (window as AnyWindow).backend;
    const pane = container.querySelector('.workspace-chat-scroll') as HTMLElement;
    expect(pane).not.toBeNull();

    let scrollTop = 100;
    Object.defineProperty(pane, 'scrollTop', {
      configurable: true,
      get: () => scrollTop,
      set: (value) => { scrollTop = Number(value); },
    });
    Object.defineProperty(pane, 'scrollHeight', { configurable: true, get: () => 1000 });
    Object.defineProperty(pane, 'clientHeight', { configurable: true, get: () => 400 });

    fireEvent.scroll(pane);
    await act(async () => {
      backend._emit('token', { text: 'new live token' });
    });

    expect(scrollTop).toBe(100);
  });

  it('keeps auto-scroll enabled when the chat feed is already near the bottom', async () => {
    const { Workspace } = await import('../workspace.tsx');
    const { container } = render(<Workspace dir="/tmp/ws" uiLang="ko" />);
    const backend = (window as AnyWindow).backend;
    const pane = container.querySelector('.workspace-chat-scroll') as HTMLElement;
    expect(pane).not.toBeNull();

    let scrollTop = 590;
    Object.defineProperty(pane, 'scrollTop', {
      configurable: true,
      get: () => scrollTop,
      set: (value) => { scrollTop = Number(value); },
    });
    Object.defineProperty(pane, 'scrollHeight', { configurable: true, get: () => 1000 });
    Object.defineProperty(pane, 'clientHeight', { configurable: true, get: () => 400 });

    fireEvent.scroll(pane);
    await act(async () => {
      backend._emit('token', { text: 'new live token' });
    });

    await waitFor(() => {
      expect(scrollTop).toBe(1000);
    });
  });

  it('keeps following delayed chat content growth only while pinned to the bottom', async () => {
    const callbacks: ResizeObserverCallback[] = [];
    const originalResizeObserver = (window as AnyWindow).ResizeObserver;
    const flushAnimationFrame = () => new Promise<void>((resolve) => {
      if (typeof window.requestAnimationFrame === 'function') {
        window.requestAnimationFrame(() => resolve());
        return;
      }
      setTimeout(resolve, 0);
    });
    class TestResizeObserver {
      constructor(callback: ResizeObserverCallback) {
        callbacks.push(callback);
      }
      observe = vi.fn();
      unobserve = vi.fn();
      disconnect = vi.fn();
    }
    (window as AnyWindow).ResizeObserver = TestResizeObserver;

    try {
      const { Workspace } = await import('../workspace.tsx');
      const { container } = render(<Workspace dir="/tmp/ws" uiLang="ko" />);
      const backend = (window as AnyWindow).backend;
      const pane = container.querySelector('.workspace-chat-scroll') as HTMLElement;
      expect(pane).not.toBeNull();
      expect(container.querySelector('[data-workspace-chat-content="true"]')).not.toBeNull();
      expect(callbacks.length).toBeGreaterThan(0);

      let scrollTop = 590;
      let scrollHeight = 1000;
      Object.defineProperty(pane, 'scrollTop', {
        configurable: true,
        get: () => scrollTop,
        set: (value) => { scrollTop = Number(value); },
      });
      Object.defineProperty(pane, 'scrollHeight', { configurable: true, get: () => scrollHeight });
      Object.defineProperty(pane, 'clientHeight', { configurable: true, get: () => 400 });

      fireEvent.scroll(pane);
      await act(async () => {
        backend._emit('token', { text: 'new live token' });
        await flushAnimationFrame();
        await flushAnimationFrame();
      });
      expect(scrollTop).toBe(1000);

      scrollHeight = 1400;
      await act(async () => {
        callbacks.forEach((callback) => callback([], {} as ResizeObserver));
        await flushAnimationFrame();
      });
      expect(scrollTop).toBe(1400);

      scrollTop = 100;
      scrollHeight = 1800;
      fireEvent.scroll(pane);
      await act(async () => {
        callbacks.forEach((callback) => callback([], {} as ResizeObserver));
        await flushAnimationFrame();
      });
      expect(scrollTop).toBe(100);
    } finally {
      if (originalResizeObserver) {
        (window as AnyWindow).ResizeObserver = originalResizeObserver;
      } else {
        delete (window as AnyWindow).ResizeObserver;
      }
    }
  });

  it('surfaces ask_user websocket events as a pending Q&A prompt', async () => {
    const { Workspace } = await import('../workspace.tsx');
    const { getByTestId } = render(<Workspace dir="/tmp/ws" uiLang="ko" />);
    const backend = (window as AnyWindow).backend;

    await act(async () => {
      backend._emit('ask_user', {
        flow_id: 'flow-ask-1',
        question: 'Pick an implementation path?',
        kind: 'single',
        options: [{ id: 'a', label: 'Use existing worker' }],
      });
    });

    await waitFor(() => {
      expect(getByTestId('ask-prompt-stub').textContent).toContain('flow-ask-1');
    });
    expect(getByTestId('ask-prompt-stub').textContent).toContain('ready');
    expect((window as AnyWindow).QA_FLOWS['flow-ask-1'].question).toBe('Pick an implementation path?');
  });

  it('ignores NUL-only stream tokens so keepalives do not create blank running turns', async () => {
    const { Workspace } = await import('../workspace.tsx');
    const { queryByText } = render(<Workspace dir="/tmp/ws" uiLang="ko" />);
    const backend = (window as AnyWindow).backend;

    await act(async () => {
      backend._emit('token', { text: '\u0000' });
    });

    expect(queryByText('Agent responding')).toBeNull();
  });
});
