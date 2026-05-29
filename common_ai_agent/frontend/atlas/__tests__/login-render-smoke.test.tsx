// __tests__/login-render-smoke.test.tsx
//
// THE BEHAVIORAL GATE for the login.tsx auth screen.
//
// Companion to the COMPILE gate (the typed LoginScreen in login.tsx). This test
// catches the SAME class of lossy-migration bug just found in workspace.tsx —
// a symbol that the live render path reads but the migrated .tsx never provides
// (a "X is not a function" / undefined-read at mount), which compiles silently
// when an `any` slips through and only blows up at runtime.
//
// It mounts the REAL LoginScreen component (imported via ../login.tsx, which on
// import also registers window.LoginScreen — the bridge app.jsx consumes) in
// jsdom with the window globals the live app supplies stubbed out, and asserts:
//   1. it renders WITHOUT throwing (no "X is not a function", no undefined-read);
//   2. the load-bearing chrome exists — the modal dialog, the ATLAS heading, the
//      submit button, and the username field — proving the component assembled
//      its form end-to-end without a hook/helper resolving to undefined.
//
// If a future refactor drops a state setter, a bound helper (switchMode /
// requestEmailCode / submit), or a style object from the module, EITHER tsc
// fails (compile gate) OR this mount throws (behavioral gate). Both stay green.

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
vi.setConfig({ testTimeout: 30000, hookTimeout: 30000 }); // full-app mount in jsdom is >5s under load

import { render, cleanup, screen, within } from '@testing-library/react';

// ── window/global stubs the live app normally supplies ──────────────────────
// login.tsx is self-contained: on mount its useEffect fires fetch('/api/auth/
// status') and reads window.location.search. Stub fetch so the mount-time poll
// settles to a clean default auth status without a real server; jsdom already
// provides window.location. No panel components, backend bridge, or markdown
// vendors are read by this screen, so nothing else needs stubbing.
type AnyWindow = typeof window & Record<string, any>;

function installWindowStubs() {
  // Network: every fetch resolves to an empty-OK JSON so the /api/auth/status
  // poll (and any postJSON triggered by a future code path) settles cleanly.
  global.fetch = vi.fn(async () =>
    new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } }),
  ) as unknown as typeof fetch;
}

describe('Login render smoke (the behavioral gate)', () => {
  beforeEach(() => {
    installWindowStubs();
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it('mounts the real LoginScreen without throwing (no undefined-symbol break)', async () => {
    // Import AFTER stubs are installed so the module-load window reads in
    // login.tsx see the stubbed globals.
    const { LoginScreen } = await import('../login.tsx');
    expect(typeof LoginScreen).toBe('function');

    expect(() => {
      render(<LoginScreen onAuth={() => {}} />);
    }).not.toThrow();
  });

  it('renders the modal dialog + ATLAS heading (form assembled end-to-end)', async () => {
    const { LoginScreen } = await import('../login.tsx');
    const { container } = render(<LoginScreen />);

    // The root is a fixed-overlay role="dialog" labelled "ATLAS login".
    const dialog = screen.getByRole('dialog');
    expect(dialog).not.toBeNull();
    expect(dialog.getAttribute('aria-label')).toBe('ATLAS login');

    // The ATLAS brand heading is always present in the card header.
    expect(within(dialog).getByText('ATLAS')).toBeInTheDocument();

    // A <form> wraps the fields (its onSubmit binds the `submit` helper, which
    // must have resolved to a real function for the JSX to construct).
    expect(container.querySelector('form')).not.toBeNull();
  });

  it('renders the submit button + username field (state setters resolved)', async () => {
    const { LoginScreen } = await import('../login.tsx');
    render(<LoginScreen />);

    // Default mode is 'login' → the submit button reads "Login" (copy.action).
    // Its presence proves modeCopy lookup + the busy/accent reads all resolved.
    const submitBtn = screen.getByRole('button', { name: 'Login' });
    expect(submitBtn).toBeInTheDocument();
    expect(submitBtn.getAttribute('type')).toBe('submit');

    // The username field (login mode) — its onChange binds setUsername. If that
    // setter were a dropped destructure, constructing the input would throw.
    const userInput = screen.getByRole('textbox');
    expect(userInput).toBeInTheDocument();
    expect(userInput.getAttribute('autocomplete')).toBe('username');

    // The mode-switch link (onClick binds switchMode) is the secondary action.
    expect(screen.getByRole('button', { name: 'Register' })).toBeInTheDocument();
  });

  it('registered window.LoginScreen on import (app.jsx mount bridge)', async () => {
    await import('../login.tsx');
    expect(typeof (window as AnyWindow).LoginScreen).toBe('function');
  });
});
