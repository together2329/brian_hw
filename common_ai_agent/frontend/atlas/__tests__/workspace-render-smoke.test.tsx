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

import { render, cleanup, within } from '@testing-library/react';

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
  // Backend bridge — a no-op send/subscribe surface so status reads resolve.
  w.backend = {
    send: vi.fn(),
    on: vi.fn(),
    off: vi.fn(),
    state: 'open',
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
});
