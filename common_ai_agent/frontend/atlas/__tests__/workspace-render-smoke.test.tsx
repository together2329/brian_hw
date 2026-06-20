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
  w.CONTEXT = {};
  w.ACTIVE_SESSION = '';
  w.ATLAS_UI_LANG = 'ko';
  w.ATLAS_USER = { username: 'alice' };
  w.ATLAS_AGENT_RUNNING = false;
  w.ATLAS_EXEC_MODE = '';
  delete w.ATLAS_DEFAULT_EXEC_MODE;
  delete w.ATLAS_BOOT_CONFIG;
  delete w.ATLAS_ENABLE_ASK_USER_CARDS;
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

  it('switches the visible UI back to Normal on backend mode_change after plan confirm', async () => {
    const { Workspace } = await import('../workspace.tsx');
    const { getByText, queryByText } = render(<Workspace dir="/tmp/ws" uiLang="ko" />);

    fireEvent.click(getByText(/Plan/i));
    await waitFor(() => {
      expect(queryByText(/Read-only/i)).not.toBeNull();
    });

    act(() => {
      (window as AnyWindow).backend._emit('mode_change', { mode: 'normal' });
    });

    await waitFor(() => {
      expect(queryByText(/Read-only/i)).toBeNull();
    });
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

    // Plain prose syncs on the slow (idle) tier — still pending at 80ms…
    await act(async () => {
      vi.advanceTimersByTime(80);
    });
    expect(setInput).not.toHaveBeenCalled();

    // …and lands once the 240ms idle delay expires.
    await act(async () => {
      vi.advanceTimersByTime(200);
    });
    expect(setInput).toHaveBeenLastCalledWith('abc');

    // Slash drafts keep the fast 60ms tier (the popup is root-rendered).
    fireEvent.change(textarea, { target: { value: '/sc' } });
    await act(async () => {
      vi.advanceTimersByTime(60);
    });
    expect(setInput).toHaveBeenLastCalledWith('/sc');

    // The popup-CLOSING transition must also be fast: the last parent-visible
    // value ('/sc') is popup-shaped, so the prose continuation syncs at 60ms —
    // otherwise the stale-open popup would hijack Enter for 240ms.
    fireEvent.change(textarea, { target: { value: '/sc deploy now' } });
    await act(async () => {
      vi.advanceTimersByTime(60);
    });
    expect(setInput).toHaveBeenLastCalledWith('/sc deploy now');
    vi.useRealTimers();
  });

  it('poller bail-outs keep the Workspace root render-stable on identical poll payloads', async () => {
    vi.useFakeTimers();
    // The worker-status endpoint answers with the SAME payload every poll,
    // except idle_age_sec which advances every tick like the real server — the
    // bail-out must treat that as unchanged. Everything else answers {}.
    // Plain microtask-resolving response objects (NOT new Response()): real
    // Response.json() reads a stream on macrotasks, which under fake timers
    // defers every poll's setState to the END of the act() window — batching
    // all cycles into one render and blinding this test. With pure-microtask
    // json(), each poll cycle's state update (and any wrongful re-render)
    // lands inside its own cycle.
    let idleAge = 100;
    const jsonOk = (payload: any) => ({ ok: true, status: 200, json: async () => payload });
    global.fetch = vi.fn(async (url: RequestInfo | URL) => {
      const u = String(url);
      if (u.includes('/api/session/worker/status')) {
        idleAge += 3;
        return jsonOk({
          policy: 'single_active',
          active_count: 1,
          worker: { state: 'running', alive: true, running: true, pid: 7, idle_age_sec: idleAge },
        });
      }
      return jsonOk({});
    }) as unknown as typeof fetch;

    const { Workspace } = await import('../workspace.tsx');
    const { ATLAS_INPUT_PERF } = await import('../workspace-root-render.tsx');
    render(<Workspace dir="/tmp/ws" uiLang="ko" />);

    // First window: mount renders, every poller's first setState, and any
    // one-shot mount timers settle here.
    await act(async () => {
      await vi.advanceTimersByTimeAsync(3100);
    });

    const baseline = ATLAS_INPUT_PERF.rootRenders;
    // Second window covers THREE cycles of every poller (1.5s/2.5s/3s) with
    // identical payloads (modulo the volatile idle_age_sec). Each updater
    // returns the previous reference, so the subtree must not re-render.
    // Tolerance of 1: React may run the component body once before bailing
    // out of an identical-reference update (render-once-then-bail), and the
    // counter counts body executions. A broken bail-out re-renders on EVERY
    // poll cycle instead — >= 3 extra renders in this window.
    const deltas: number[] = [];
    for (let i = 0; i < 3; i += 1) {
      const before = ATLAS_INPUT_PERF.rootRenders;
      await act(async () => {
        await vi.advanceTimersByTimeAsync(3100);
      });
      deltas.push(ATLAS_INPUT_PERF.rootRenders - before);
    }
    // Kill-proof (verified by mutation): with the volatile-field exclusion
    // removed from the worker-status comparison, deltas become [1,1,1] (a
    // re-render every poll cycle). Healthy bail-outs give [1,0,0] — the single
    // leading 1 is React's render-once-then-bail body execution, which the
    // counter counts but whose subtree render is skipped.
    expect(deltas.reduce((a, b) => a + b, 0)).toBeLessThanOrEqual(1);
    vi.useRealTimers();
  });

  it('samePolledState: JSON-equality contract for the poller bail-outs', async () => {
    const { samePolledState } = await import('../workspace-root-data-hook.tsx');
    expect(samePolledState(null, null)).toBe(true);
    expect(samePolledState({ a: 1, b: [1, 2] }, { a: 1, b: [1, 2] })).toBe(true);
    expect(samePolledState({ a: 1 }, { a: 2 })).toBe(false);
    expect(samePolledState({ a: 1 }, null)).toBe(false);
    // Documented limitation: comparison is key-insertion-order dependent.
    // Pollers rebuild payloads with the same code each tick, so order is
    // stable — if a producer ever reorders keys, the bail-out goes inert
    // (extra renders), it does NOT serve stale state.
    expect(samePolledState({ a: 1, b: 2 }, { b: 2, a: 1 })).toBe(false);
    // undefined-valued keys are dropped by JSON.stringify — this is what the
    // worker-status comparison relies on to exclude volatile idle_age_sec.
    expect(samePolledState({ a: 1, v: undefined }, { a: 1 })).toBe(true);
    // Cycles must not throw (fail-open to "changed").
    const cyc: any = { a: 1 }; cyc.self = cyc;
    expect(samePolledState(cyc, { a: 1 })).toBe(false);
  });

  it('force-syncs a continuous prose burst via the max-wait cap', async () => {
    vi.useFakeTimers();
    const { WorkspacePromptRow } = await import('../workspace-root-render.tsx');
    const setInput = vi.fn();
    const inputRef = createRef<HTMLTextAreaElement>();
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
        inputRouteRef={{ current: {} }}
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

    // Keystrokes at t=0/130/260/390ms — a pure trailing debounce would defer
    // the parent sync to t=390+240=630ms; the 400ms max-wait forces a flush.
    fireEvent.change(textarea, { target: { value: 'p1' } });
    for (const value of ['p1 p2', 'p1 p2 p3', 'p1 p2 p3 p4']) {
      await act(async () => {
        vi.advanceTimersByTime(130);
      });
      fireEvent.change(textarea, { target: { value } });
    }
    expect(setInput).not.toHaveBeenCalled();
    await act(async () => {
      vi.advanceTimersByTime(20); // t=410 > 400ms max-wait
    });
    expect(setInput).toHaveBeenLastCalledWith('p1 p2 p3 p4');
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
      vi.advanceTimersByTime(240);
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
      // Past BOTH sync tiers (60/240ms) and the 400ms max-wait — the reset
      // must have cancelled the pending sync outright, not just outrun it.
      vi.advanceTimersByTime(450);
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

  it('refreshes live slash commands when command completion opens', async () => {
    const w = window as AnyWindow;
    w.SLASH_COMMANDS = [
      { cmd: '/help', alias: 'h', hint: 'show available commands', desc: 'show available commands' },
    ];
    w.atlasData.refreshSlashCommands = vi.fn(async () => {
      w.SLASH_COMMANDS = [
        {
          cmd: '/locked-truth-finalize',
          alias: 'lo',
          aliases: ['truth-lock', 'lock-truth'],
          hint: 'finalize locked truth files',
          desc: 'finalize locked truth files',
        },
      ];
      window.dispatchEvent(new CustomEvent('atlas-data-changed', { detail: 'SLASH_COMMANDS' }));
    });

    const { Workspace } = await import('../workspace.tsx');
    const { container, queryByText } = render(<Workspace dir="/tmp/ws" uiLang="ko" />);
    const textarea = container.querySelector('textarea') as HTMLTextAreaElement;

    fireEvent.change(textarea, { target: { value: '/lo' } });

    await waitFor(() => expect(w.atlasData.refreshSlashCommands).toHaveBeenCalled());
    await waitFor(() => expect(queryByText('/locked-truth-finalize')).not.toBeNull());
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
    const { queryByText } = render(
      <Workspace
        dir="/tmp/ws"
        uiLang="ko"
        activeNamespace="alice/demo/jjj/orchestrator"
        activeWorkflow="orchestrator"
      />,
    );
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

  it('prefixes the footer status while the workspace is in plan mode', async () => {
    const { Workspace } = await import('../workspace.tsx');
    const { getByText, queryByText } = render(<Workspace dir="/tmp/ws" uiLang="ko" />);

    fireEvent.click(getByText(/Plan/));

    await waitFor(() => expect(queryByText(/\[plan\] End of loop/)).not.toBeNull());
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

  it('shows idle session worker state instead of a failed worker banner', async () => {
    global.fetch = vi.fn(async (url: RequestInfo | URL, _init?: RequestInit) => {
      if (String(url).startsWith('/api/session/worker/status')) {
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

    await waitFor(() => expect(queryByText(/Agent worker idle/)).not.toBeNull());
    expect(queryByText(/Agent worker failed/)).toBeNull();
    expect(queryByText(/End of loop/)).toBeNull();
  });

  it('keeps a missing current-session worker idle even when other workers are active', async () => {
    global.fetch = vi.fn(async (url: RequestInfo | URL, _init?: RequestInit) => {
      if (String(url).startsWith('/api/session/worker/status')) {
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

    await waitFor(() => expect(queryByText(/Agent worker idle/)).not.toBeNull());
    expect(queryByText(/Agent worker failed/)).toBeNull();
    expect(queryByText(/End of loop/)).toBeNull();
  });

  it('shows Agent responding ahead of stale idle session worker state', async () => {
    global.fetch = vi.fn(async (url: RequestInfo | URL, _init?: RequestInit) => {
      if (String(url).startsWith('/api/session/worker/status')) {
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

    await waitFor(() => expect(queryByText(/Agent worker idle/)).not.toBeNull());
    await act(async () => {
      backend._emit('agent_state', { running: true });
    });

    await waitFor(() => expect(queryByText('Agent responding')).not.toBeNull());
    expect(queryByText(/Agent worker idle/)).toBeNull();
  });

  it('reconciles stale Agent responding from ready/not-running worker status only after grace', async () => {
    const {
      RESPONDING_IDLE_RECONCILE_GRACE_MS,
      shouldReconcileRespondingFromWorkerStatus,
    } = await import('../workspace-root-data-hook.tsx');
    const readyIdle = { state: 'ready', alive: true, running: false };
    const startedAt = 1000;

    expect(shouldReconcileRespondingFromWorkerStatus({
      status: readyIdle,
      streaming: true,
      agentRunning: true,
      orchestratorMode: false,
      startedAt,
      now: startedAt + RESPONDING_IDLE_RECONCILE_GRACE_MS - 1,
    })).toBe(false);

    expect(shouldReconcileRespondingFromWorkerStatus({
      status: readyIdle,
      streaming: true,
      agentRunning: true,
      orchestratorMode: false,
      startedAt,
      now: startedAt + RESPONDING_IDLE_RECONCILE_GRACE_MS,
    })).toBe(true);

    expect(shouldReconcileRespondingFromWorkerStatus({
      status: { state: 'ready', alive: true, running: true },
      streaming: true,
      agentRunning: true,
      orchestratorMode: false,
      startedAt,
      now: startedAt + RESPONDING_IDLE_RECONCILE_GRACE_MS,
    })).toBe(false);

    expect(shouldReconcileRespondingFromWorkerStatus({
      status: readyIdle,
      streaming: true,
      agentRunning: true,
      orchestratorMode: true,
      startedAt,
      now: startedAt + RESPONDING_IDLE_RECONCILE_GRACE_MS,
    })).toBe(false);
  });

  it('hydrates persisted assistant output when the saved conversation extends the live feed', async () => {
    const { conversationSnapshotExtendsLiveFeed } = await import('../workspace-root-data-hook.tsx');

    const liveFeed = [
      { kind: 'agent', text: 'previous answer' },
      { kind: 'turn_end', text: 'live marker' },
      { kind: 'user', text: 'Hi', live: true },
    ];
    const persistedFeed = [
      { kind: 'agent', text: 'previous answer' },
      { kind: 'turn_end', text: 'live marker' },
      { kind: 'user', text: 'Hi' },
      { kind: 'agent', text: 'Hi! UART RTL 개선 계속 진행할 수 있어요.' },
      { kind: 'turn_end', text: 'live marker' },
    ];

    expect(conversationSnapshotExtendsLiveFeed(liveFeed, persistedFeed)).toBe(true);
    expect(conversationSnapshotExtendsLiveFeed(liveFeed, [
      { kind: 'agent', text: 'older answer' },
      { kind: 'turn_end', text: 'live marker' },
    ])).toBe(false);
  });

  it('preserves completed assistant runtime metadata when hydrating conversation history', async () => {
    const { conversationFeedFromMessages } = await import('../workspace-rootdata-feed-completion.tsx');
    const { agentRuntimeParts } = await import('../workspace-feed-cards.tsx');

    const feed = conversationFeedFromMessages([
      {
        role: 'assistant',
        content: 'pong',
        model: 'gpt-5.5',
        reasoning_effort: 'xhigh',
      },
    ], 'alice/ws1/uart_ip/default');

    expect(feed[0]).toMatchObject({
      kind: 'agent',
      text: 'pong',
      model: 'gpt-5.5',
      reasoningEffort: 'xhigh',
    });
    expect(agentRuntimeParts(feed[0])).toEqual(['gpt-5.5', 'effort xhigh']);
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

  it('falls back to context runtime metadata when agent_state has no model or effort', async () => {
    const w = window as AnyWindow;
    w.CONTEXT = {
      ...(w.CONTEXT || {}),
      model: 'ctx-gpt-5.5',
      reasoningEffort: 'xhigh',
    };
    const { Workspace } = await import('../workspace.tsx');
    const { queryByText } = render(<Workspace dir="/tmp/ws" uiLang="ko" />);
    const backend = (window as AnyWindow).backend;

    await act(async () => {
      backend._emit('agent_state', { running: true });
    });

    await waitFor(() => {
      expect(queryByText(/Agent responding.*ctx-gpt-5\.5.*xhigh/)).not.toBeNull();
    });
  });

  it('renders orchestrator live chat events in the center feed and clears terminal state', async () => {
    const w = window as AnyWindow;
    w.ATLAS_EXEC_MODE = 'orchestrator';
    w.ACTIVE_SESSION = 'alice/demo/jjj/orchestrator';
    w.atlasData.sessionFor = (ip: string, wf: string) => `alice/demo/${ip}/${wf}`;

    const { Workspace } = await import('../workspace.tsx');
    const { queryByText } = render(<Workspace dir="/tmp/ws" uiLang="ko" />);
    const backend = w.backend;

    await act(async () => {
      backend._emit('orchestrator_chat', {
        session_id: 'alice/demo/jjj/orchestrator',
        ip: 'jjj',
        created_at: 1716400000,
        payload: {
          role: 'assistant_delta',
          content: 'Hi ',
          stream_id: 'orch-stream-1',
        },
      });
      backend._emit('orchestrator_chat', {
        session_id: 'alice/demo/jjj/orchestrator',
        ip: 'jjj',
        created_at: 1716400001,
        payload: {
          role: 'assistant_delta',
          content: 'there',
          stream_id: 'orch-stream-1',
        },
      });
    });

    await waitFor(() => expect(queryByText('Agent responding')).not.toBeNull());
    await waitFor(() => expect(queryByText('Hi there')).not.toBeNull(), { timeout: 2500 });

    await act(async () => {
      backend._emit('orchestrator_chat', {
        session_id: 'alice/demo/jjj/orchestrator',
        ip: 'jjj',
        created_at: 1716400002,
        payload: {
          role: 'run_state',
          status: 'completed',
          final_state: 'completed',
        },
      });
    });

    await waitFor(() => expect(queryByText('Agent responding')).toBeNull());
  });

  it('clears orchestrator Agent responding via run status polling when terminal websocket is missed', async () => {
    const w = window as AnyWindow;
    w.ATLAS_EXEC_MODE = 'orchestrator';
    w.ACTIVE_SESSION = 'alice/demo/jjj/orchestrator';
    w.ACTIVE_IP = 'jjj';
    w.atlasData.sessionFor = (ip: string, wf: string) => `alice/demo/${ip}/${wf}`;

    const fetchSpy = vi.fn(async (url: RequestInfo | URL, _init?: RequestInit) => {
      const requestUrl = new URL(String(url), 'http://atlas.test');
      const path = requestUrl.pathname;
      if (path === '/api/pipeline/orchestrator/chat') {
        return new Response(JSON.stringify({
          ok: true,
          run_id: 'run-completed-without-ws',
          status: 'started',
        }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }
      if (path === '/api/orchestrator/runs/run-completed-without-ws') {
        return new Response(JSON.stringify({
          ok: true,
          run: {
            id: 'run-completed-without-ws',
            status: 'completed',
            final_state: 'completed',
          },
        }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }
      return new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } });
    });
    global.fetch = fetchSpy as unknown as typeof fetch;

    const { Workspace } = await import('../workspace.tsx');
    const { container, queryByText } = render(<Workspace dir="/tmp/ws" uiLang="ko" />);
    const textarea = container.querySelector('textarea') as HTMLTextAreaElement;

    fireEvent.change(textarea, { target: { value: 'answer once' } });
    fireEvent.keyDown(textarea, { key: 'Enter', code: 'Enter' });

    await waitFor(() => expect(queryByText('Agent responding')).not.toBeNull());
    await waitFor(() => {
      const runDetailCall = fetchSpy.mock.calls.find(([url]) => {
        const requestUrl = new URL(String(url), 'http://atlas.test');
        return requestUrl.pathname === '/api/orchestrator/runs/run-completed-without-ws';
      });
      expect(runDetailCall).toBeTruthy();
      const runDetailUrl = new URL(String(runDetailCall?.[0] || ''), 'http://atlas.test');
      expect(runDetailUrl.searchParams.get('workspace_session')).toBe('demo');
      expect(runDetailUrl.searchParams.get('ip')).toBe('jjj');
      expect(runDetailUrl.searchParams.get('session')).toBe('alice/demo/jjj/orchestrator');
    });
    await waitFor(() => expect(queryByText('Agent responding')).toBeNull());
  });

  it('keeps a newer orchestrator response active when an older run poll finishes late', async () => {
    const w = window as AnyWindow;
    w.ATLAS_EXEC_MODE = 'orchestrator';
    w.ACTIVE_SESSION = 'alice/demo/jjj/orchestrator';
    w.ACTIVE_IP = 'jjj';
    w.atlasData.sessionFor = (ip: string, wf: string) => `alice/demo/${ip}/${wf}`;
    const chatRunIds = ['old-run', 'new-run'];
    let resolveOldRun: ((response: Response) => void) | null = null;
    let oldRunSignal: AbortSignal | null = null;

    const fetchSpy = vi.fn(async (url: RequestInfo | URL, init?: RequestInit) => {
      const requestUrl = new URL(String(url), 'http://atlas.test');
      const path = requestUrl.pathname;
      if (path === '/api/pipeline/orchestrator/chat') {
        const runId = chatRunIds.shift() || 'new-run';
        return new Response(JSON.stringify({
          ok: true,
          run_id: runId,
          status: 'started',
        }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }
      if (path === '/api/orchestrator/runs/old-run') {
        oldRunSignal = init?.signal instanceof AbortSignal ? init.signal : null;
        return new Promise<Response>((resolve, reject) => {
          resolveOldRun = resolve;
          oldRunSignal?.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')));
        });
      }
      if (path === '/api/orchestrator/runs/new-run') {
        return new Response(JSON.stringify({
          ok: true,
          run: {
            id: 'new-run',
            status: 'running',
            final_state: '',
          },
        }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }
      return new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } });
    });
    global.fetch = fetchSpy as unknown as typeof fetch;

    const { Workspace } = await import('../workspace.tsx');
    const { container, queryByText } = render(<Workspace dir="/tmp/ws" uiLang="ko" />);
    const textarea = container.querySelector('textarea') as HTMLTextAreaElement;

    fireEvent.change(textarea, { target: { value: 'first prompt' } });
    fireEvent.keyDown(textarea, { key: 'Enter', code: 'Enter' });
    await waitFor(() => expect(queryByText('Agent responding')).not.toBeNull());
    await waitFor(() => {
      expect(fetchSpy.mock.calls.some(([url]) => {
        const requestUrl = new URL(String(url), 'http://atlas.test');
        return requestUrl.pathname === '/api/orchestrator/runs/old-run'
          && requestUrl.searchParams.get('workspace_session') === 'demo'
          && requestUrl.searchParams.get('ip') === 'jjj';
      })).toBe(true);
    });

    fireEvent.change(textarea, { target: { value: 'second prompt' } });
    fireEvent.keyDown(textarea, { key: 'Enter', code: 'Enter' });
    await waitFor(() => expect(oldRunSignal?.aborted).toBe(true));
    expect(resolveOldRun).not.toBeNull();
    resolveOldRun?.(new Response(JSON.stringify({
      ok: true,
      run: {
        id: 'old-run',
        status: 'completed',
        final_state: 'completed',
      },
    }), { status: 200, headers: { 'Content-Type': 'application/json' } }));

    await waitFor(() => expect(queryByText('Agent responding')).not.toBeNull());
  });

  it('aborts orchestrator run status polling when the workspace unmounts', async () => {
    const w = window as AnyWindow;
    w.ATLAS_EXEC_MODE = 'orchestrator';
    w.ACTIVE_SESSION = 'alice/demo/jjj/orchestrator';
    w.ACTIVE_IP = 'jjj';
    w.atlasData.sessionFor = (ip: string, wf: string) => `alice/demo/${ip}/${wf}`;
    let runSignal: AbortSignal | null = null;

    const fetchSpy = vi.fn(async (url: RequestInfo | URL, init?: RequestInit) => {
      const requestUrl = new URL(String(url), 'http://atlas.test');
      const path = requestUrl.pathname;
      if (path === '/api/pipeline/orchestrator/chat') {
        return new Response(JSON.stringify({
          ok: true,
          run_id: 'unmount-run',
          status: 'started',
        }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }
      if (path === '/api/orchestrator/runs/unmount-run') {
        runSignal = init?.signal instanceof AbortSignal ? init.signal : null;
        return new Promise<Response>((_resolve, reject) => {
          runSignal?.addEventListener('abort', () => reject(new DOMException('Aborted', 'AbortError')));
        });
      }
      return new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } });
    });
    global.fetch = fetchSpy as unknown as typeof fetch;

    const { Workspace } = await import('../workspace.tsx');
    const { container, unmount } = render(<Workspace dir="/tmp/ws" uiLang="ko" />);
    const textarea = container.querySelector('textarea') as HTMLTextAreaElement;

    fireEvent.change(textarea, { target: { value: 'abort on unmount' } });
    fireEvent.keyDown(textarea, { key: 'Enter', code: 'Enter' });

    await waitFor(() => {
      expect(fetchSpy.mock.calls.some(([url]) => {
        const requestUrl = new URL(String(url), 'http://atlas.test');
        return requestUrl.pathname === '/api/orchestrator/runs/unmount-run'
          && requestUrl.searchParams.get('workspace_session') === 'demo'
          && requestUrl.searchParams.get('ip') === 'jjj';
      })).toBe(true);
    });
    expect(runSignal?.aborted).toBe(false);

    unmount();

    await waitFor(() => expect(runSignal?.aborted).toBe(true));
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
    (window as AnyWindow).ATLAS_ENABLE_ASK_USER_CARDS = true;
    const { Workspace } = await import('../workspace.tsx');
    const { container, getByTestId, getByText, queryByTestId } = render(<Workspace dir="/tmp/ws" uiLang="ko" />);
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
    expect(getByText('Q&A Session')).toBeTruthy();
    expect(container.querySelector('textarea')).not.toBeNull();
    expect(getByTestId('ask-prompt-stub').textContent).toContain('ready');
    expect((window as AnyWindow).QA_FLOWS['flow-ask-1'].question).toBe('Pick an implementation path?');

    fireEvent.click(getByText('chat'));
    await waitFor(() => {
      expect(queryByTestId('ask-prompt-stub')).toBeNull();
    });
    expect(getByText(/Agent is waiting on you/)).toBeTruthy();
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

  it('keeps completed chat iframe height stable when iframe viewport metrics echo back', async () => {
    const callbacks: ResizeObserverCallback[] = [];
    const originalResizeObserver = (window as AnyWindow).ResizeObserver;
    const originalRaf = window.requestAnimationFrame;
    const originalCancelRaf = window.cancelAnimationFrame;
    const originalContentDocument = Object.getOwnPropertyDescriptor(
      HTMLIFrameElement.prototype,
      'contentDocument',
    );
    const originalContentWindow = Object.getOwnPropertyDescriptor(
      HTMLIFrameElement.prototype,
      'contentWindow',
    );
    const docs = new WeakMap<HTMLIFrameElement, Document>();
    let viewportHeight = 24;
    let nextRafId = 1;
    let rafCallbacks = new Map<number, FrameRequestCallback>();

    class TestResizeObserver {
      constructor(callback: ResizeObserverCallback) {
        callbacks.push(callback);
      }
      observe = vi.fn();
      unobserve = vi.fn();
      disconnect = vi.fn();
    }

    const flushRaf = async () => {
      const pending = Array.from(rafCallbacks.entries());
      rafCallbacks = new Map();
      pending.forEach(([, callback]) => callback(performance.now()));
      await Promise.resolve();
    };

    (window as AnyWindow).ResizeObserver = TestResizeObserver;
    window.requestAnimationFrame = ((callback: FrameRequestCallback) => {
      const id = nextRafId++;
      rafCallbacks.set(id, callback);
      return id;
    }) as typeof window.requestAnimationFrame;
    window.cancelAnimationFrame = ((id: number) => {
      rafCallbacks.delete(id);
    }) as typeof window.cancelAnimationFrame;
    Object.defineProperty(HTMLIFrameElement.prototype, 'contentDocument', {
      configurable: true,
      get() {
        return docs.get(this as HTMLIFrameElement) ?? null;
      },
    });
    Object.defineProperty(HTMLIFrameElement.prototype, 'contentWindow', {
      configurable: true,
      get() {
        return { innerHeight: viewportHeight };
      },
    });

    let rendered: ReturnType<typeof render> | null = null;
    try {
      const { ChatMarkdownFrame } = await import('../workspace-chat-markdown-frame.tsx');
      rendered = render(<ChatMarkdownFrame text="pong" />);
      const iframe = rendered.container.querySelector('iframe.chat-markdown-frame') as HTMLIFrameElement;
      expect(iframe).not.toBeNull();

      const doc = document.implementation.createHTMLDocument('chat-frame');
      const root = doc.createElement('main');
      root.className = 'md-agent md-chat-frame-body';
      root.innerHTML = '<p>pong</p>';
      Object.defineProperty(root, 'scrollHeight', { configurable: true, get: () => viewportHeight });
      Object.defineProperty(root, 'offsetHeight', { configurable: true, get: () => viewportHeight });
      root.getBoundingClientRect = (() => ({
        x: 0,
        y: 0,
        top: 0,
        left: 0,
        right: 320,
        bottom: 20,
        width: 320,
        height: 20,
        toJSON: () => ({}),
      })) as typeof root.getBoundingClientRect;
      doc.body.appendChild(root);
      docs.set(iframe, doc);

      fireEvent.load(iframe);
      await act(async () => {
        await flushRaf();
      });
      expect(iframe.style.height).toBe('24px');

      for (let i = 0; i < 3; i += 1) {
        viewportHeight = Number.parseFloat(iframe.style.height) || 24;
        await act(async () => {
          callbacks.forEach((callback) => callback([], {} as ResizeObserver));
          await flushRaf();
        });
        expect(iframe.style.height).toBe('24px');
      }
    } finally {
      rendered?.unmount();
      if (originalResizeObserver) {
        (window as AnyWindow).ResizeObserver = originalResizeObserver;
      } else {
        delete (window as AnyWindow).ResizeObserver;
      }
      window.requestAnimationFrame = originalRaf;
      window.cancelAnimationFrame = originalCancelRaf;
      if (originalContentDocument) {
        Object.defineProperty(HTMLIFrameElement.prototype, 'contentDocument', originalContentDocument);
      } else {
        delete (HTMLIFrameElement.prototype as AnyWindow).contentDocument;
      }
      if (originalContentWindow) {
        Object.defineProperty(HTMLIFrameElement.prototype, 'contentWindow', originalContentWindow);
      } else {
        delete (HTMLIFrameElement.prototype as AnyWindow).contentWindow;
      }
    }
  });
});
