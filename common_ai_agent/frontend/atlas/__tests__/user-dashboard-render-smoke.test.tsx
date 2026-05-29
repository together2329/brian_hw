// __tests__/user-dashboard-render-smoke.test.tsx
//
// THE BEHAVIORAL GATE for the AtlasUserDashboard screen (user-dashboard.tsx,
// the LIVE vite component), modeled after workspace-render-smoke.test.tsx.
//
// Companion to the COMPILE path: user-dashboard.tsx is a self-contained, typed
// export (no hook-bag destructure, no split siblings), so a lossy migration
// would surface as either a tsc error OR an undefined-symbol runtime break at
// mount ("X is not a function" / undefined-read). The same class of bug just
// hit workspace.tsx (33 symbols destructured-but-never-returned), so we mount
// the REAL component in jsdom with the live window globals stubbed and assert:
//   1. it renders WITHOUT throwing (no "X is not a function", no undefined-read);
//   2. a load-bearing element exists — the "User Dashboard" header + the IP
//      Inventory table — proving the component body resolved end-to-end (every
//      style/helper/handler it references was a real value, not `undefined`);
//   3. importing the module registers window.AtlasUserDashboard (the app-shell
//      mount bridge the not-yet-migrated .jsx consumers still resolve).
//
// If a future refactor drops a symbol the screen reads, EITHER tsc fails OR this
// mount throws. Both gates must stay green before the .jsx is retired.

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
vi.setConfig({ testTimeout: 30000, hookTimeout: 30000 }); // full-app mount in jsdom is >5s under load

import { render, cleanup, screen, within, act } from '@testing-library/react';

// ── window/global stubs the live app normally supplies ──────────────────────
// The .tsx render path reads `window` very defensively: only
// `window.AtlasDashboardHelpers` (optional, behind a JS fallback inside openIp)
// and `window.location.href` (set on the Admin button click) are touched, plus
// `fetch` (polled in a useEffect + setInterval). Trivial stubs clear a clean
// mount, mirroring index.html / the legacy bundles' load order.
type AnyWindow = typeof window & Record<string, any>;

function installWindowStubs() {
  const w = window as AnyWindow;

  // dashboard_helpers bridge — read (optional) inside openIp(). Supply a real
  // builder so the click path resolves, exactly like the live UMD shim
  // (window.AtlasDashboardHelpers) does. The component also has a JS fallback,
  // but stubbing it matches the live order rather than relying on the fallback.
  w.AtlasDashboardHelpers = {
    buildOpenIpPayload: (row: any, workflowValue: (r: any) => string) => {
      const wf = workflowValue(row);
      const payload: { id: string; ip?: unknown; workflow?: string } = {
        id: (row.session_id as string) || '',
        ip: row.ip,
      };
      if (wf) payload.workflow = wf;
      return payload;
    },
  };

  // Network: every fetch resolves to an empty-OK JSON so the mount-time poll
  // (/api/user/dashboard) settles without a real server. The component reads
  // `r.ok` then `r.json()`, so a real Response satisfies both branches.
  global.fetch = vi.fn(async () =>
    new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } }),
  ) as unknown as typeof fetch;
}

describe('AtlasUserDashboard render smoke (the behavioral gate)', () => {
  beforeEach(() => {
    installWindowStubs();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.runOnlyPendingTimers();
    vi.useRealTimers();
    cleanup();
    vi.restoreAllMocks();
  });

  it('mounts the real AtlasUserDashboard without throwing (no undefined-symbol break)', async () => {
    // Import AFTER stubs are installed so any module-load window read sees them.
    const { AtlasUserDashboard } = await import('../user-dashboard.tsx');
    expect(typeof AtlasUserDashboard).toBe('function');

    expect(() => {
      render(
        <AtlasUserDashboard
          activeNamespace="demo"
          activeIp="uart_v2"
          activeWorkflow="ssot-gen"
          execMode="auto"
          runMode="engineering"
          onOpenScreen={vi.fn()}
          onActivateSession={vi.fn()}
        />,
      );
    }).not.toThrow();
  });

  it('renders the dashboard shell (header + IP Inventory panel resolved to real DOM)', async () => {
    const { AtlasUserDashboard } = await import('../user-dashboard.tsx');

    // Initial render shows the loading placeholder; flush the mount-time
    // fetch + state update so the full dashboard body (all the styled panels +
    // helpers) actually renders. If any symbol the body reads were undefined,
    // this commit phase would throw.
    const { container } = render(
      <AtlasUserDashboard onOpenScreen={vi.fn()} onActivateSession={vi.fn()} />,
    );
    // Flush the mount-time fetch + state commit inside act() so the full
    // dashboard body (not just the loading stub) renders deterministically.
    await act(async () => {
      await vi.runOnlyPendingTimersAsync();
    });

    // The load-bearing title proves the full body (not just the loading stub)
    // committed without a render-helper throwing.
    expect(screen.getByText('User Dashboard')).toBeInTheDocument();
    // The IP Inventory panel + its empty-state row prove the table-building
    // path (statusBadgeStyle / workspaceText / workflowText / fmt / usd / ts)
    // all resolved to real functions on an empty dataset.
    expect(screen.getByText('IP Inventory')).toBeInTheDocument();
    expect(screen.getByText('No visible IPs yet.')).toBeInTheDocument();
    // The action buttons (Enter Workspace / Refresh) prove the header handlers
    // wired up — a <button> living in the rendered tree.
    const buttons = within(container).getAllByRole('button');
    expect(buttons.length).toBeGreaterThan(0);
    expect(screen.getByText('Enter Workspace')).toBeInTheDocument();
  });

  it('registered window.AtlasUserDashboard on import (app-shell mount bridge)', async () => {
    await import('../user-dashboard.tsx');
    expect(typeof (window as AnyWindow).AtlasUserDashboard).toBe('function');
  });
});
