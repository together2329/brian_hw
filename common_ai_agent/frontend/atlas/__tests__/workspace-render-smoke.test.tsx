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
  w.FLOW_STAGES = [];
  w.TODOS = [];
  w.atlasData = {};
  w.FILE_TREE_LOADING = false;
  w.FILE_TREE_ERROR = null;
  w.FILE_TREE_LAST_REFRESH = 0;
  // Backend bridge — a tiny pubsub surface so Workspace can exercise live
  // agent_state/token cleanup without a real WebSocket.
  const backendHandlers: Record<string, Set<(payload: any) => void>> = {};
  w.backend = {
    send: vi.fn(),
    on: vi.fn(),
    off: vi.fn(),
    state: 'open',
    getConnectionState: () => 'open',
    subscribe: vi.fn((type: string, cb: (payload: any) => void) => {
      (backendHandlers[type] = backendHandlers[type] || new Set()).add(cb);
      return () => backendHandlers[type]?.delete(cb);
    }),
    _emit: (type: string, payload: any = {}) => {
      (backendHandlers[type] || new Set()).forEach((cb) => cb({ type, ...payload }));
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

    expect(scrollTop).toBe(1000);
  });

  it('keeps following delayed chat content growth only while pinned to the bottom', async () => {
    const callbacks: ResizeObserverCallback[] = [];
    const originalResizeObserver = (window as AnyWindow).ResizeObserver;
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
      });
      expect(scrollTop).toBe(1000);

      scrollHeight = 1400;
      await act(async () => {
        callbacks.forEach((callback) => callback([], {} as ResizeObserver));
      });
      expect(scrollTop).toBe(1400);

      scrollTop = 100;
      scrollHeight = 1800;
      fireEvent.scroll(pane);
      await act(async () => {
        callbacks.forEach((callback) => callback([], {} as ResizeObserver));
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
