// __tests__/lobby-render-smoke.test.tsx
//
// THE BEHAVIORAL GATE for the lobby.tsx screen (the LIVE vite component).
//
// Companion to the workspace-render-smoke gate. That test caught a class of
// lossy-migration bug where a .jsx → .tsx migration silently drops a symbol
// (e.g. a hook returns fewer things than the component destructures), which
// compiles when the bag is `any` and then blows up at runtime with
// "X is not a function" / undefined-read.
//
// lobby.tsx is self-contained (no hook-split siblings, no window-published
// panel components), but it still:
//   - reads window-global bridges (window.location, fetch),
//   - kicks off a fetch() chain in a mount-time useEffect (guest auth + session
//     list), and
//   - registers window.LobbyPage + self-mounts onto #root on import.
//
// This test mounts the REAL LobbyPage component (imported via ../lobby.tsx) in
// jsdom with the window globals the live app supplies stubbed out, and asserts:
//   1. it renders WITHOUT throwing (no "X is not a function", no undefined-read);
//   2. the load-bearing chrome exists — the ATLAS header, the username/login
//      controls, the session search box, and the "+" new-session FAB — proving
//      the component assembled end-to-end without a symbol resolving to
//      undefined;
//   3. it registered window.LobbyPage on import (the transitional bridge the
//      not-yet-retired .jsx boot HTML still resolves).
//
// If a future refactor / further split drops one of those bound symbols from
// the migrated module, this mount throws (behavioral gate) and CI goes red
// BEFORE the .jsx reference is retired.

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
vi.setConfig({ testTimeout: 30000, hookTimeout: 30000 }); // full-app mount in jsdom is >5s under load

import { render, cleanup, within, act } from '@testing-library/react';

// ── window/global stubs the live app normally supplies ──────────────────────
// lobby.tsx reads `fetch` (mount-time guest-auth + session-list poll) and, at
// MODULE-LOAD time, calls createRoot(#root) IF a #root element exists. jsdom's
// default document has no #root, so the self-mount branch is naturally skipped
// and the import is a clean side-effect (it only registers window.LobbyPage).
// The fetch stub keeps the mount-time useEffect chain from hitting a real
// server or rejecting.
type AnyWindow = typeof window & Record<string, any>;

function installWindowStubs() {
  // Network: every fetch resolves to an empty-OK JSON so the mount-time
  // guest-auth POST + the /api/sessions GET settle without a real server.
  // `{ sessions: [] }` matches the shape the component reads (data.sessions).
  global.fetch = vi.fn(async () =>
    new Response('{"sessions":[]}', {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    }),
  ) as unknown as typeof fetch;

  // alert() is invoked by the guest/login/create handlers; jsdom does not
  // implement it. Not exercised on a clean mount, but stub it defensively so
  // any branch that fires it never throws "alert is not a function".
  (window as AnyWindow).alert = vi.fn();
}

describe('Lobby render smoke (the behavioral gate)', () => {
  beforeEach(() => {
    installWindowStubs();
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it('mounts the real LobbyPage without throwing (no undefined-symbol break)', async () => {
    // Import AFTER stubs are installed so the module-load window reads in
    // lobby.tsx see the stubbed globals.
    const { LobbyPage } = await import('../lobby.tsx');
    expect(typeof LobbyPage).toBe('function');

    expect(() => {
      render(<LobbyPage />);
    }).not.toThrow();
  });

  it('renders the ATLAS lobby chrome (header + login + search + FAB resolved)', async () => {
    const { LobbyPage } = await import('../lobby.tsx');
    const { container, getByText, getByPlaceholderText } = render(<LobbyPage />);

    // The brand header — proves the top-level layout rendered.
    expect(getByText('ATLAS')).toBeTruthy();
    expect(getByText('Multi-User')).toBeTruthy();

    // The username field + login controls (the login section assembled).
    expect(getByPlaceholderText('Enter username or continue as guest')).toBeTruthy();
    expect(getByText('Continue as Guest')).toBeTruthy();
    expect(getByText('Login')).toBeTruthy();

    // The session toolbar — search box + Active/Archived tabs.
    expect(getByPlaceholderText('Search sessions…')).toBeTruthy();
    expect(getByText('Active')).toBeTruthy();
    expect(getByText('Archived')).toBeTruthy();

    // The new-session FAB (aria-labelled) — proves setShowModal binding exists.
    const fab = container.querySelector('button[aria-label="New Session"]');
    expect(fab).not.toBeNull();
    expect(fab?.textContent).toContain('+');
  });

  it('opens the New Session modal (setShowModal + PROJECT_OPTIONS resolved)', async () => {
    const { LobbyPage } = await import('../lobby.tsx');
    const { container, getByText, getByPlaceholderText } = render(<LobbyPage />);

    const fab = container.querySelector(
      'button[aria-label="New Session"]',
    ) as HTMLButtonElement;
    expect(fab).not.toBeNull();

    // Clicking the FAB flips showModal → the modal dialog mounts with its
    // title-input + the project <select> populated from PROJECT_OPTIONS.
    // Wrap in act() so React flushes the setShowModal re-render before we query.
    expect(() => act(() => fab.click())).not.toThrow();

    const dialog = container.querySelector('div[role="dialog"]');
    expect(dialog).not.toBeNull();
    const d = dialog as HTMLElement;
    expect(within(d).getByText('New Session')).toBeTruthy();
    expect(getByPlaceholderText('e.g., AXI DMA Controller')).toBeTruthy();
    // PROJECT_OPTIONS rendered as <option> rows inside the select.
    const options = d.querySelectorAll('select option');
    expect(options.length).toBeGreaterThan(0);
    expect(getByText('Create')).toBeTruthy();
  });

  it('registered window.LobbyPage on import (boot-HTML mount bridge)', async () => {
    await import('../lobby.tsx');
    expect(typeof (window as AnyWindow).LobbyPage).toBe('function');
  });
});
