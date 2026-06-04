// __tests__/soc-architect-render-smoke.test.tsx
//
// THE BEHAVIORAL GATE for the soc-architect.tsx screen (the LIVE vite root),
// the companion to workspace-render-smoke.test.tsx.
//
// workspace.tsx had a lossy-migration class of bug: 33 symbols were
// destructured-but-never-returned by a hook, so they compiled silently (the
// bag was `any`) and would blow up at runtime with "X is not a function" /
// undefined-read. The SocArchitect family is the SAME shape — a 4210-line .jsx
// mega-root strangler-fig split into a root .tsx + 9 sibling .tsx modules, each
// fed an in-scope `ctx` bag and resolving cross-file components through
// `window.*` forward-refs at render time. Any forward-ref that a sibling
// registers-on-import but the root forgot to trigger, or any window global the
// render path reads without a guard, is invisible to tsc and only surfaces when
// the component actually mounts.
//
// This test mounts the REAL SocArchitect component (imported via
// ../soc-architect.tsx, which registers window.SocArchitect and pulls in every
// sibling for its window.* registration side-effects) in jsdom, with the same
// window globals the live app supplies stubbed out, and asserts:
//   1. the landing "My IPs" card grid mounts WITHOUT throwing;
//   2. opening an IP card drives selectedIp -> the FULL screen (run bar +
//      hierarchy tree + diagram canvas + status grid + JobTracker +
//      ArchitectChat) mounts WITHOUT throwing — this is the path that exercises
//      window.PIPELINE_STAGES.map(...), g.MOD_ICON[...], g.JobTracker(...),
//      g.ArchitectChat(...), g.IpxactImportBtn(...), every cross-file
//      forward-ref the .jsx used to resolve;
//   3. window.SocArchitect was registered on import (legacy app-shell bridge).
//
// If a future refactor drops a sibling import (so a forward-ref's window global
// is never registered) or drops a render-path window read's guard, this mount
// throws and the gate goes red — before the .jsx reference is retired.

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
vi.setConfig({ testTimeout: 30000, hookTimeout: 30000 }); // full-app mount in jsdom is >5s under load

import { render, cleanup, fireEvent, waitFor, within, act } from '@testing-library/react';

// Establish the SAME window bridges the live app loads BEFORE the soc-architect
// bundle. These publish window globals at MODULE-LOAD time that the render path
// reads (not import-time of soc-architect itself): soc-shared.tsx publishes
// window.MOD_ICON / window.MOD_KIND_LABEL / window.StatusTrio (read as
// g.MOD_ICON[m.kind] etc. in the tree/diagram/status siblings); soc-data.tsx
// publishes window.SOC / window.SOC_LOOKUP; ui-utils.tsx publishes
// window.CopyBtn. Importing them first (ESM imports run before the test body)
// makes those bridges real, exactly as the live load order does — not fakes.
import '../soc-shared.tsx';
import '../soc-data.tsx';
import '../ui-utils.tsx';

type AnyWindow = typeof window & Record<string, any>;

function installWindowStubs() {
  const w = window as AnyWindow;

  // Runtime ATLAS bridges the hooks/render path read off `window`.
  w.CONTEXT = w.CONTEXT || {};
  w.ACTIVE_SESSION = '';
  w.ATLAS_UI_LANG = 'ko';
  w.SCOPE_PATH = '';
  w.ATLAS_JOBS = [];
  // atlasData.setScopePath is optional-chained in the scope-follow effect, but
  // supply a no-op so the live-mode branch (if it ever fires) resolves.
  w.atlasData = { setScopePath: vi.fn() };

  // IP seed for the landing card grid (props.ipOptions falls back to this).
  w.IP_OPTIONS = ['demo_ip'];

  // Backend bridge — the chat + tool_result watcher use `subscribe`, which must
  // return an unsubscribe fn (the cleanup calls it). send is a no-op.
  w.backend = {
    send: vi.fn(),
    subscribe: vi.fn(() => () => {}),
    state: 'open',
  };

  // Network: every fetch resolves to an empty-OK JSON so the mount-time polls
  // (/api/jobs, /api/catalog/models, /api/workspace/tree, /api/ip/list,
  // /api/soc) settle without a real server. /api/soc returning {} makes
  // `live=false` -> soc=EMPTY_SOC (empty clusters), a clean, deterministic
  // mount that still exercises the full render shell.
  global.fetch = vi.fn(async () =>
    new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } }),
  ) as unknown as typeof fetch;
}

describe('SocArchitect render smoke (the behavioral gate)', () => {
  beforeEach(() => {
    installWindowStubs();
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it('mounts the landing "My IPs" grid without throwing (no undefined-symbol break)', async () => {
    // Import AFTER stubs are installed so the sibling module-load window reads
    // see the stubbed globals.
    const { SocArchitect } = await import('../soc-architect.tsx');
    expect(typeof SocArchitect).toBe('function');

    let container: HTMLElement | null = null;
    expect(() => {
      ({ container } = render(<SocArchitect ipOptions={['demo_ip']} activeIp="demo_ip" />));
    }).not.toThrow();

    // The landing card grid carries the "My IPs" heading + a clickable card.
    expect(within(container as unknown as HTMLElement).getByText('My IPs')).toBeTruthy();
    expect((container as unknown as HTMLElement).querySelector('button')).not.toBeNull();
  });

  it('opening an IP card mounts the FULL screen (every cross-file forward-ref resolves)', async () => {
    const { SocArchitect } = await import('../soc-architect.tsx');
    const { container } = render(<SocArchitect ipOptions={['demo_ip']} activeIp="demo_ip" />);

    // Click the IP card -> setSelectedIp('demo_ip') -> the landing early-return
    // is bypassed and the full screen renders: run bar (window.PIPELINE_STAGES
    // .map), hierarchy tree (g.MOD_ICON[...]), diagram canvas, status grid,
    // JobTracker (g.JobTracker), ArchitectChat (g.ArchitectChat), IpxactImportBtn
    // (g.IpxactImportBtn). A dropped sibling import or unguarded window read
    // throws HERE.
    const card = container.querySelector('button');
    expect(card).not.toBeNull();
    expect(() => {
      fireEvent.click(card as HTMLButtonElement);
    }).not.toThrow();

    // The run bar is the load-bearing top strip of the full screen. Its presence
    // proves the early-return was bypassed and the screen assembled end-to-end.
    const runBar = container.querySelector('.run-bar');
    expect(runBar).not.toBeNull();
    // The "← All IPs" back button only exists on the full screen, never on the
    // landing grid — a precise proof the IP-selected branch rendered.
    expect((runBar as HTMLElement).textContent || '').toContain('All IPs');
    // The 3-column grid root (left rail · center · chat) carries display:grid.
    expect(container.querySelector('div[style*="grid"]')).not.toBeNull();
  });

  it('registered window.SocArchitect on import (legacy app-shell mount bridge)', async () => {
    await import('../soc-architect.tsx');
    expect(typeof (window as AnyWindow).SocArchitect).toBe('function');
  });

  it('sends workspace_session when dispatching a single workflow from the architect menu', async () => {
    const w = window as AnyWindow;
    w.ATLAS_WORKSPACE_SESSION_ID = 'alt';
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.startsWith('/api/soc')) {
        return new Response(JSON.stringify(w.SOC), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }
      if (url === '/api/job/dispatch') {
        return new Response(JSON.stringify({ ok: true, job_id: 'job-alt' }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }
      if (url.startsWith('/api/jobs')) {
        return new Response(JSON.stringify({ jobs: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }
      return new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } });
    }) as unknown as typeof fetch;
    global.fetch = fetchMock;
    const { SocArchitect } = await import('../soc-architect.tsx');
    const { container } = render(<SocArchitect ipOptions={['demo_ip']} activeIp="demo_ip" />);

    fireEvent.click(container.querySelector('button') as HTMLButtonElement);
    await waitFor(() => expect(container.querySelector('button[title="dispatch ssot-gen on cpu0"]')).not.toBeNull());
    fireEvent.click(container.querySelector('button[title="dispatch ssot-gen on cpu0"]') as HTMLButtonElement);
    await waitFor(() => expect(fetchMock.mock.calls.some(([url]) => String(url) === '/api/job/dispatch')).toBe(true));

    const dispatchCall = fetchMock.mock.calls.find(([url]) => String(url) === '/api/job/dispatch');
    const body = JSON.parse(String((dispatchCall?.[1] as RequestInit | undefined)?.body || '{}'));
    expect(body.workspace_session).toBe('alt');
    expect(body.session).toBeUndefined();
  });

  it('sends ACTIVE_SESSION workspace when dispatching the full pipeline from the architect menu', async () => {
    const w = window as AnyWindow;
    w.ATLAS_WORKSPACE_SESSION_ID = '';
    w.ACTIVE_SESSION = 'u/alt/demo_ip/status';
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.startsWith('/api/soc')) {
        return new Response(JSON.stringify(w.SOC), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }
      if (url === '/api/pipeline/dispatch') {
        return new Response(JSON.stringify({ ok: true, pipeline_id: 'pipe-alt' }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }
      if (url.startsWith('/api/jobs')) {
        return new Response(JSON.stringify({ jobs: [] }), { status: 200, headers: { 'Content-Type': 'application/json' } });
      }
      return new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } });
    }) as unknown as typeof fetch;
    global.fetch = fetchMock;
    const { SocArchitect } = await import('../soc-architect.tsx');
    const { container } = render(<SocArchitect ipOptions={['demo_ip']} activeIp="demo_ip" />);

    fireEvent.click(container.querySelector('button') as HTMLButtonElement);
    await waitFor(() => expect(container.querySelector('.run-bar')).not.toBeNull());
    const pipelineButton = Array.from(container.querySelectorAll('button'))
      .find((button) => button.textContent?.includes('full pipeline')) as HTMLButtonElement;
    expect(pipelineButton).toBeTruthy();
    fireEvent.click(pipelineButton);
    await waitFor(() => expect(fetchMock.mock.calls.some(([url]) => String(url) === '/api/pipeline/dispatch')).toBe(true));

    const dispatchCall = fetchMock.mock.calls.find(([url]) => String(url) === '/api/pipeline/dispatch');
    const body = JSON.parse(String((dispatchCall?.[1] as RequestInit | undefined)?.body || '{}'));
    expect(body.workspace_session).toBe('alt');
  });

  it('sends workspace_session for architect job cancel and clear actions', async () => {
    const w = window as AnyWindow;
    w.ATLAS_WORKSPACE_SESSION_ID = 'alt';
    const fetchMock = vi.fn(async () =>
      new Response(JSON.stringify({ ok: true }), { status: 200, headers: { 'Content-Type': 'application/json' } }),
    ) as unknown as typeof fetch;
    global.fetch = fetchMock;
    const { JobTracker } = await import('../soc-architect-panels.tsx');
    const now = Date.now() / 1000;
    const { container } = render(<JobTracker jobs={[
      { job_id: 'run-job', status: 'running', ip: 'demo_ip', workflow: 'ssot-gen', started_at: now },
      { job_id: 'done-job', status: 'completed', ip: 'demo_ip', workflow: 'rtl-gen', started_at: now - 3 },
    ]} />);

    fireEvent.click(container.querySelector('[title="cancel job"]') as HTMLElement);
    fireEvent.click(container.querySelector('[title="clear completed jobs"]') as HTMLElement);

    await waitFor(() => expect(fetchMock.mock.calls.length).toBeGreaterThanOrEqual(2));
    const urls = fetchMock.mock.calls.map(([url]) => String(url));
    expect(urls).toContain('/api/job/run-job/cancel?workspace_session=alt');
    expect(urls).toContain('/api/jobs/clear?workspace_session=alt');
  });

  it('sends workspace_session when architect chat loads worker logs', async () => {
    const w = window as AnyWindow;
    w.ATLAS_WORKSPACE_SESSION_ID = 'alt';
    const fetchMock = vi.fn(async () =>
      new Response(JSON.stringify({ entries: [], job: { status: 'completed' } }), { status: 200, headers: { 'Content-Type': 'application/json' } }),
    ) as unknown as typeof fetch;
    global.fetch = fetchMock;
    const { ArchitectChat } = await import('../soc-architect-chat.tsx');
    render(<ArchitectChat />);

    await act(async () => {
      window.dispatchEvent(new CustomEvent('atlas:load-job-log', {
        detail: { jobId: 'run-job', live: false },
      }));
    });

    await waitFor(() => expect(fetchMock.mock.calls.some(([url]) => String(url) === '/api/job/run-job/log?workspace_session=alt')).toBe(true));
  });
});
