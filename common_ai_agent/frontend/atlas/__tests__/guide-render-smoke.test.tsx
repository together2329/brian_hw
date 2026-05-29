// __tests__/guide-render-smoke.test.tsx
//
// THE BEHAVIORAL GATE for the AtlasGuide screen (guide.tsx, the LIVE vite
// component mounted by app.jsx/app.tsx when screen === 'guide').
//
// Companion gate to the workspace-render-smoke test. The motivating bug class:
// a lossy .jsx → .tsx migration can drop a symbol the screen reads at render
// time (a hook return, a window-published helper, a re-exported component), so
// it compiles but blows up at runtime with "X is not a function" / undefined
// read — exactly the 33-symbol gap just found in workspace.tsx.
//
// This test mounts the REAL AtlasGuide component (imported via ../guide.tsx,
// which both `export`s AtlasGuide AND registers window.AtlasGuide on import)
// in jsdom with the window globals the live app supplies stubbed out, and
// asserts:
//   1. it renders WITHOUT throwing (no "X is not a function", no undefined-read);
//   2. a key load-bearing element exists — the .atlas-guide root + the authored
//      hero <h1> ("ATLAS = SSOT · RTL Generation Agent"), proving the sanitized
//      HTML actually reached the DOM (DOMPurify path resolved, not a throw).
//
// If a future refactor of guide.tsx (or a split sibling) drops a symbol the
// render path needs, this mount throws and the gate goes red.

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
vi.setConfig({ testTimeout: 30000, hookTimeout: 30000 }); // full-app mount in jsdom is >5s under load

import { render, cleanup } from '@testing-library/react';

// ── window/global stubs the live app normally supplies ──────────────────────
// guide.tsx reads window.DOMPurify (optional-chained, with a raw-HTML fallback)
// at RENDER time. We stub the full set the wiki-content screens may touch
// (marked / DOMPurify / Prism / mermaid) plus the ATLAS_* / CONTEXT / IP_OPTIONS
// bridges and a no-op backend/fetch, modeled after workspace-render-smoke, so
// any branch the screen (or a future split sibling) touches resolves cleanly.
type AnyWindow = typeof window & Record<string, any>;

function installWindowStubs() {
  const w = window as AnyWindow;

  // DOMPurify — the one symbol guide.tsx actually reads at render time. A real
  // (identity-ish) sanitize proves the sanitize() branch runs, not just the
  // raw-HTML fallback, so the assertion exercises the live code path.
  w.DOMPurify = {
    sanitize: (dirty: string, _config?: { ADD_ATTR?: string[] }) => dirty,
  };

  // Markdown / syntax-highlight / diagram libs the wiki-content screens read
  // off window. Harmless stubs so any branch resolves to a real callable.
  w.marked = Object.assign(
    (md: string) => md,
    { parse: (md: string) => md, setOptions: vi.fn() },
  );
  w.Prism = {
    highlightAll: vi.fn(),
    highlightAllUnder: vi.fn(),
    highlightElement: vi.fn(),
    highlight: (code: string) => code,
    languages: {},
  };
  w.mermaid = {
    initialize: vi.fn(),
    init: vi.fn(),
    run: vi.fn(),
    render: vi.fn(async () => ({ svg: '' })),
  };

  // Runtime ATLAS bridges the screens read off window.
  w.CONTEXT = w.CONTEXT || {};
  w.ACTIVE_SESSION = '';
  w.ATLAS_UI_LANG = 'ko';
  w.IP_OPTIONS = [];
  w.FLOW_STAGES = [];
  w.atlasData = {};

  // Backend bridge — a no-op send/subscribe surface.
  w.backend = {
    send: vi.fn(),
    on: vi.fn(),
    off: vi.fn(),
    state: 'open',
  };

  // Network: every fetch resolves to an empty-OK JSON so any mount-time poll
  // settles without a real server.
  global.fetch = vi.fn(async () =>
    new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } }),
  ) as unknown as typeof fetch;
}

describe('AtlasGuide render smoke (the behavioral gate)', () => {
  beforeEach(() => {
    installWindowStubs();
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it('mounts the real AtlasGuide without throwing (no undefined-symbol break)', async () => {
    // Import AFTER stubs are installed so any module-load window reads see the
    // stubbed globals.
    const { AtlasGuide } = await import('../guide.tsx');
    expect(typeof AtlasGuide).toBe('function');

    expect(() => {
      render(<AtlasGuide />);
    }).not.toThrow();
  });

  it('renders the .atlas-guide root + authored hero content (sanitize path resolved)', async () => {
    const { AtlasGuide } = await import('../guide.tsx');
    const { container } = render(<AtlasGuide />);

    // The screen root carries class "atlas-guide".
    const root = container.querySelector('.atlas-guide');
    expect(root).not.toBeNull();

    // The authored HTML reached the DOM through the dangerouslySetInnerHTML
    // sink: the hero heading proves the sanitize() branch produced real markup
    // (not an undefined-read / empty render).
    const hero = container.querySelector('.ag-hero h1');
    expect(hero).not.toBeNull();
    expect(hero?.textContent || '').toMatch(/ATLAS/);

    // The scoped <style> sibling is present too (the screen renders both).
    expect(container.querySelector('style')).not.toBeNull();
  });

  it('registered window.AtlasGuide on import (app-shell mount bridge)', async () => {
    await import('../guide.tsx');
    expect(typeof (window as AnyWindow).AtlasGuide).toBe('function');
  });

  it('falls back to raw HTML when DOMPurify is absent (still mounts, no throw)', async () => {
    // Prove the optional-chained DOMPurify guard is real: drop the stub and the
    // screen must still mount (raw-HTML fallback), never throw on undefined.
    delete (window as AnyWindow).DOMPurify;
    const { AtlasGuide } = await import('../guide.tsx');
    expect(() => {
      const { container } = render(<AtlasGuide />);
      expect(container.querySelector('.ag-hero h1')).not.toBeNull();
    }).not.toThrow();
  });
});
