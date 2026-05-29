// __tests__/pipeline-render-smoke.test.tsx
//
// THE BEHAVIORAL GATE for the AtlasPipeline screen (the LIVE vite component
// app-shell.tsx mounts when screen === 'pipeline', via window.AtlasPipeline).
//
// Companion gate to workspace-render-smoke / guide-render-smoke. The motivating
// bug class: a lossy .jsx → .tsx migration can drop a symbol the screen reads
// at render time (a hook return, a window-published helper/component, a
// re-exported symbol), so it COMPILES but blows up at runtime with
// "X is not a function" / undefined-read — exactly the 33-symbol gap just found
// in workspace.tsx.
//
// The pipeline screen is assembled across a CHAIN of .tsx modules whose live
// load order (main.tsx) matters because each registers globals later modules
// read at MODULE-LOAD time and at RENDER time:
//
//   pipeline.tsx            — PIPE_* width consts + forward-ref lambdas
//                             (EnhancedFlowCanvas / WorkerOrchestraBar /
//                             OrchestratorTraceStrip) + window.* bridges.
//   pipe-width.tsx          — PIPELINE_STAGE_DEPS / PHASES / SWIMLANES /
//                             FLOW_DEFS + pipelineActualStages /
//                             pipelinePolicyPayload / pipelineStateMeta /
//                             readPipeWidth.
//   pipeline-helpers.tsx    — DEFINES AtlasPipeline (the screen) + registers
//                             window.AtlasPipeline. Reads PIPE_* consts at
//                             module-load via const = w.PIPE_LEFT_DEFAULT etc.
//   pipeline-trace.tsx      — real EnhancedFlowCanvas / WorkerOrchestraBar /
//                             OrchestratorTraceStrip / DispatchRail /
//                             PipelineFlowControl (overwrite the forward-refs).
//   pipeline-flow-stage.tsx — real PipelineFlowMap + StageCard.
//
// soc-architect-pipeline.tsx supplies PIPELINE_STAGES / PIPELINE_LABEL (the
// stage roster the whole screen iterates). Importing the REAL chain (instead of
// stubbing the children) is deliberate: it makes THIS test catch a lossy gap
// ANYWHERE in the pipeline screen, not just in pipeline.tsx — the children are
// the screen.
//
// We assert:
//   1. window.AtlasPipeline is a function after the chain imports (the
//      app-shell mount bridge resolved — pipeline-helpers ran its bridge).
//   2. AtlasPipeline mounts WITHOUT throwing (no "X is not a function",
//      no undefined-read across the whole assembled screen).
//   3. load-bearing DOM exists — the screen root (.pipe-screen) and the run bar
//      (.run-bar.pipe-runbar). The default ip resolves to 'arm_m0_min' (the
//      pipelineInitialIp fallback), so the full .pipe-board mounts too, which is
//      what exercises <w.PipelineFlowControl/> / <w.PipelineFlowMap/> /
//      <w.DispatchRail/> and the EnhancedFlowCanvas / WorkerOrchestraBar /
//      OrchestratorTraceStrip forward-refs end-to-end.

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
vi.setConfig({ testTimeout: 30000, hookTimeout: 30000 }); // full-app mount in jsdom is >5s under load

import { render, cleanup } from '@testing-library/react';

type AnyWindow = typeof window & Record<string, any>;

function installWindowStubs() {
  const w = window as AnyWindow;

  // Runtime ATLAS bridges the hooks/render path read off window. The pipeline
  // chain optional-chains / `any`-casts these, so trivial stubs clear a mount.
  w.CONTEXT = w.CONTEXT || {};
  w.ACTIVE_SESSION = '';
  w.ACTIVE_IP = '';
  w.ATLAS_UI_LANG = 'ko';
  w.ATLAS_EXEC_MODE = 'orchestrator';
  w.ATLAS_RUN_MODE = 'engineering';
  w.ATLAS_USER = {};
  w.IP_OPTIONS = [];
  w.FLOW_STAGES = [];
  w.atlasData = {
    setUserSessionId: vi.fn(),
    setScopePath: vi.fn(),
    setActiveSession: vi.fn(),
  };

  // activateAtlasNamespace is owned by an unmigrated .jsx; AtlasPipeline calls
  // it on mount if present, else falls back to the manual session-switch path.
  // A no-op keeps the mount on the simplest branch.
  w.activateAtlasNamespace = vi.fn();

  // Backend bridge — a no-op send/subscribe surface so the poll loop's
  // backend.subscribe('pipeline_state_changed', …) resolves to undefined (which
  // the code tolerates) rather than throwing on an undefined read.
  w.backend = {
    send: vi.fn(),
    on: vi.fn(),
    off: vi.fn(),
    subscribe: vi.fn(() => () => {}),
    switchSession: vi.fn(),
    connect: vi.fn(),
    state: 'open',
  };

  // Network: every fetch resolves to an empty-OK JSON so any mount-time poll
  // (pipeline/state, progress, ip/list, orchestrator chat) settles without a
  // real server. AtlasPipeline tolerates {} (empty stages → idle screen).
  global.fetch = vi.fn(async () =>
    new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } }),
  ) as unknown as typeof fetch;
}

// Import the REAL pipeline module chain in the SAME order main.tsx loads it, so
// every module-load + render-time window read sees a fully-registered surface
// (PIPE_* consts, PIPELINE_* data, the helpers, and the real child components).
// Done inside a helper (not top-level ESM imports) so the stubs above are
// installed FIRST — pipeline-helpers binds PIPE_* consts at module-load time.
async function importPipelineChain() {
  await import('../soc-architect-pipeline.tsx'); // PIPELINE_STAGES / PIPELINE_LABEL
  await import('../pipeline.tsx');               // PIPE_* consts + forward-ref bridges
  await import('../pipe-width.tsx');             // helpers + flow defs + state meta
  await import('../pipeline-helpers.tsx');       // AtlasPipeline + window.AtlasPipeline
  await import('../pipeline-trace.tsx');         // real canvas / workers / dispatch / flow-control
  await import('../pipeline-flow-stage.tsx');    // real PipelineFlowMap + StageCard
  const mod = await import('../pipeline-helpers.tsx');
  return mod.AtlasPipeline as () => unknown;
}

describe('AtlasPipeline render smoke (the behavioral gate)', () => {
  beforeEach(() => {
    installWindowStubs();
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it('registered window.AtlasPipeline on import (app-shell mount bridge)', async () => {
    await importPipelineChain();
    expect(typeof (window as AnyWindow).AtlasPipeline).toBe('function');
  });

  it('mounts the real AtlasPipeline without throwing (no undefined-symbol break)', async () => {
    const AtlasPipeline = await importPipelineChain();
    expect(typeof AtlasPipeline).toBe('function');

    const Screen = AtlasPipeline as unknown as () => JSX.Element;
    expect(() => {
      render(<Screen />);
    }).not.toThrow();
  });

  it('renders the screen root + run bar, and (default ip) the full board with all child components', async () => {
    const AtlasPipeline = await importPipelineChain();
    const Screen = AtlasPipeline as unknown as () => JSX.Element;
    const { container } = render(<Screen />);

    // The screen root carries class "pipe-screen" (always rendered, any state).
    const root = container.querySelector('.pipe-screen');
    expect(root).not.toBeNull();

    // The run bar is always present (proves the top-level shell rendered, not a
    // throw before first paint).
    const runBar = container.querySelector('.run-bar.pipe-runbar');
    expect(runBar).not.toBeNull();

    // pipelineInitialIp() falls back to 'arm_m0_min', so the full 3-column board
    // mounts — which is what actually drives <w.PipelineFlowControl/>,
    // <w.PipelineFlowMap/>, <w.DispatchRail/>, and the EnhancedFlowCanvas /
    // WorkerOrchestraBar / OrchestratorTraceStrip forward-refs. Its presence
    // proves those window-published components all resolved to real functions
    // (a dropped one would have thrown "X is not a function" during render).
    const board = container.querySelector('.pipe-board');
    expect(board).not.toBeNull();
  });
});
