// __tests__/pipeline-stage-blocked.test.tsx
//
// Task 6 (UI Blocked/Failed Owner Visibility) gate for the pipeline StageCard.
//
// The motivating gaps (plan Task 6):
//   (a) StageCard's blame route text (row5) + the 📬 save-handoff action button
//       were gated on isFailed ONLY — a BLOCKED stage with an owner showed
//       neither, so the owner was invisible and unrepairable from the card.
//   (b) The backend /api/pipeline/state emits `blame` as a BARE STRING workflow
//       name for sim failures, while the orchestrator/handoff path emits the
//       richer { owner_workflow, feedback_packet } OBJECT. StageCard read
//       data.blame.owner_workflow only, so the live string payload never fired
//       the blame UI. StageCard must tolerate BOTH shapes.
//
// We assert, by rendering the REAL StageCard (imported via the same module
// chain pipeline-render-smoke uses, so window.pipelineStateMeta /
// PIPELINE_LABEL / PIPELINE_STAGES / pipelinePolicyPayload are all registered):
//   1. state=blocked renders DISTINCTLY from state=failed (glyph + label + the
//      data-state attribute the strip/CSS key on).
//   2. owner route text + 📬 save-handoff button are present for BOTH a failed
//      and a blocked owner-routed stage (object-shape blame).
//   3. the SAME owner route + save-handoff fire when blame is a BARE STRING
//      (the live backend shape).
//   4. NO blame UI when the stage has no owner (idle / failed-without-blame).

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
vi.setConfig({ testTimeout: 30000, hookTimeout: 30000 });

import { render, cleanup, within } from '@testing-library/react';

type AnyWindow = typeof window & Record<string, any>;

function installWindowStubs() {
  const w = window as AnyWindow;
  w.CONTEXT = w.CONTEXT || {};
  w.ATLAS_UI_LANG = 'ko';
  w.ATLAS_EXEC_MODE = 'orchestrator';
  w.ATLAS_RUN_MODE = 'engineering';
  global.fetch = vi.fn(async () =>
    new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } }),
  ) as unknown as typeof fetch;
}

// Import the pipeline chain in main.tsx order so every module-load + render-time
// window read sees a fully-registered surface (PIPELINE_STATE_META /
// pipelineStateMeta / PIPELINE_LABEL / PIPELINE_STAGES / pipelinePolicyPayload).
async function importStageCard() {
  await import('../soc-architect-pipeline.tsx'); // PIPELINE_STAGES / PIPELINE_LABEL
  await import('../pipeline.tsx');               // PIPE_* consts + forward-ref bridges
  await import('../pipe-width.tsx');             // PIPELINE_STATE_META + pipelineStateMeta + flow defs
  await import('../pipeline-helpers.tsx');       // AtlasPipeline + window.AtlasPipeline
  await import('../pipeline-trace.tsx');         // real canvas / workers / dispatch / flow-control
  const mod = await import('../pipeline-flow-stage.tsx'); // real PipelineFlowMap + StageCard
  return mod.StageCard as (props: any) => JSX.Element;
}

describe('StageCard — Task 6 blocked/failed owner visibility', () => {
  let StageCard: (props: any) => JSX.Element;

  beforeEach(async () => {
    installWindowStubs();
    StageCard = await importStageCard();
  });

  afterEach(() => {
    cleanup();
    vi.restoreAllMocks();
  });

  it('renders state=blocked DISTINCTLY from state=failed (glyph + label + data-state)', () => {
    const { container: blockedC } = render(
      <StageCard stageId="lint" ip="uart_tx" info={{ state: 'blocked' }} />,
    );
    const { container: failedC } = render(
      <StageCard stageId="lint" ip="uart_tx" info={{ state: 'failed' }} />,
    );

    const blockedCard = blockedC.querySelector('.pipe-stage-card') as HTMLElement;
    const failedCard = failedC.querySelector('.pipe-stage-card') as HTMLElement;

    // The card root + the inline state chip both carry data-state, distinct per
    // state. The DAG strip / CSS key on this attribute.
    expect(blockedCard.getAttribute('data-state')).toBe('blocked');
    expect(failedCard.getAttribute('data-state')).toBe('failed');

    const blockedChip = blockedCard.querySelector('.pipe-stage-state') as HTMLElement;
    const failedChip = failedCard.querySelector('.pipe-stage-state') as HTMLElement;
    expect(blockedChip.getAttribute('data-state')).toBe('blocked');
    expect(failedChip.getAttribute('data-state')).toBe('failed');

    // Label + glyph differ: blocked -> '⏸ blocked', failed -> '! failed'
    // (PIPELINE_STATE_META in pipe-width.tsx).
    expect(blockedChip.textContent).toBe('blocked');
    expect(failedChip.textContent).toBe('failed');
    const blockedGlyph = blockedCard.querySelector('.pipe-stage-glyph') as HTMLElement;
    const failedGlyph = failedCard.querySelector('.pipe-stage-glyph') as HTMLElement;
    expect(blockedGlyph.textContent).toBe('⏸');
    expect(failedGlyph.textContent).toBe('!');
  });

  it('FAILED owner-routed stage (object blame) shows the blame route + 📬 save handoff', () => {
    const { container } = render(
      <StageCard
        stageId="sim"
        ip="uart_tx"
        info={{ state: 'failed', blame: { owner_workflow: 'rtl-gen', feedback_packet: 'fix the FSM' } }}
      />,
    );
    const blame = container.querySelector('.pipe-blame') as HTMLElement;
    expect(blame).not.toBeNull();
    expect(blame.getAttribute('data-route-state')).toBe('failed');
    // failed uses the 'blame →' label and names the owner.
    expect(blame.textContent).toContain('blame →');
    expect(within(blame).getByText('rtl-gen')).toBeInTheDocument();
    expect(within(blame).getByText('[ go fix rtl-gen ]')).toBeInTheDocument();
    // save-handoff action present.
    expect(container.querySelector('.pipe-stage-save')).not.toBeNull();
  });

  it('BLOCKED owner-routed stage (object blame) ALSO shows the owner route + 📬 save handoff', () => {
    const { container } = render(
      <StageCard
        stageId="sim"
        ip="uart_tx"
        info={{ state: 'blocked', blame: { owner_workflow: 'rtl-gen', feedback_packet: 'unblock me' } }}
      />,
    );
    const blame = container.querySelector('.pipe-blame') as HTMLElement;
    expect(blame).not.toBeNull();
    expect(blame.getAttribute('data-route-state')).toBe('blocked');
    // blocked prefers the 'owner →' label (it is not a failure, it is routed).
    expect(blame.textContent).toContain('owner →');
    expect(blame.textContent).not.toContain('blame →');
    expect(within(blame).getByText('rtl-gen')).toBeInTheDocument();
    expect(within(blame).getByText('[ go fix rtl-gen ]')).toBeInTheDocument();
    // The save-handoff action is exposed for blocked owner-routed stages too.
    expect(container.querySelector('.pipe-stage-save')).not.toBeNull();
  });

  it('tolerates the BACKEND bare-STRING blame shape (live /api/pipeline/state)', () => {
    // atlas_api_jobs emits stage_blame as a plain workflow-name string.
    const { container: failedC } = render(
      <StageCard stageId="sim" ip="uart_tx" info={{ state: 'failed', blame: 'rtl-gen' }} />,
    );
    const failedBlame = failedC.querySelector('.pipe-blame') as HTMLElement;
    expect(failedBlame).not.toBeNull();
    expect(within(failedBlame).getByText('rtl-gen')).toBeInTheDocument();
    expect(failedC.querySelector('.pipe-stage-save')).not.toBeNull();

    const { container: blockedC } = render(
      <StageCard stageId="sim" ip="uart_tx" info={{ state: 'blocked', blame: 'rtl-gen' }} />,
    );
    const blockedBlame = blockedC.querySelector('.pipe-blame') as HTMLElement;
    expect(blockedBlame).not.toBeNull();
    expect(within(blockedBlame).getByText('rtl-gen')).toBeInTheDocument();
    expect(blockedC.querySelector('.pipe-stage-save')).not.toBeNull();
  });

  it('go-fix POSTs the normalized owner workflow for a bare-string blame', async () => {
    const fetchMock = global.fetch as unknown as ReturnType<typeof vi.fn>;
    const { container } = render(
      <StageCard stageId="sim" ip="uart_tx" info={{ state: 'blocked', blame: 'rtl-gen' }} />,
    );
    const goFix = within(container.querySelector('.pipe-blame') as HTMLElement)
      .getByText('[ go fix rtl-gen ]') as HTMLButtonElement;
    goFix.click();
    await Promise.resolve();
    // The dispatch POST went out (owner resolved from the bare string, not undefined).
    const dispatched = fetchMock.mock.calls.some(([url]) => String(url) === '/api/pipeline/dispatch');
    expect(dispatched).toBe(true);
  });

  it('shows NO blame UI when there is no owner (failed-without-blame and idle)', () => {
    const { container: noBlameC } = render(
      <StageCard stageId="sim" ip="uart_tx" info={{ state: 'failed' }} />,
    );
    expect(noBlameC.querySelector('.pipe-blame')).toBeNull();
    expect(noBlameC.querySelector('.pipe-stage-save')).toBeNull();

    const { container: idleC } = render(
      <StageCard stageId="sim" ip="uart_tx" info={{ state: 'idle' }} />,
    );
    expect(idleC.querySelector('.pipe-blame')).toBeNull();
    expect(idleC.querySelector('.pipe-stage-save')).toBeNull();

    // An empty-string blame is treated as no-owner.
    const { container: emptyC } = render(
      <StageCard stageId="sim" ip="uart_tx" info={{ state: 'blocked', blame: '' }} />,
    );
    expect(emptyC.querySelector('.pipe-blame')).toBeNull();
    expect(emptyC.querySelector('.pipe-stage-save')).toBeNull();
  });
});
