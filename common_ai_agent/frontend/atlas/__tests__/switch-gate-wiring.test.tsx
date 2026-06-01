// __tests__/switch-gate-wiring.test.tsx
//
// Wiring guard for the AC-1 switch-gate mirror in the LIVE (.tsx) frontend.
//
// The PURE gate is exhaustively covered by session-machine.test.ts (16 green).
// THIS test pins the WIRING CONTRACT that workspace-root-session-hook.tsx +
// workspace-root-data-hook.tsx depend on: it reproduces, against the real
// imported factory, the exact begin/submit/finish/fail sequence the hooks drive
// and asserts the load-bearing invariant — a prompt submitted in the one-frame
// window AFTER a switch starts is HELD, never sent. If a refactor changes the
// gate's method names or hold semantics, the hook wiring breaks and this fails.

import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import { createSwitchGate } from '../session-machine';

// Mirror of the hook's submitMsg gate-consult: returns 'held' iff the gate is
// switching at the synchronous instant of submit (the race the fix closes).
const consult = (gate: ReturnType<typeof createSwitchGate>, text: string) =>
  gate.isSwitching()
    ? { kind: 'held' as const, outcome: gate.submit({ text }) }
    : { kind: 'send' as const, outcome: gate.submit({ text }) };

describe('switch-gate wiring (the .tsx live-app contract)', () => {
  it('beginWorkflowReady -> submit in the same tick HOLDS (never sends)', () => {
    // beginWorkflowReady sets the gate switching in the SAME tick as
    // setWorkflowReady — so even though React state lags, submit reads switching.
    const gate = createSwitchGate();
    gate.beginSwitch('owner/ip/rtl_gen'); // beginWorkflowReady wiring
    const r = consult(gate, 'first input after switch');
    expect(r.kind).toBe('held');
    expect(r.outcome.action).toBe('held');
    if (r.outcome.action === 'held') expect(r.outcome.queued).toBe(1);
  });

  it('before any switch, submit SENDS (ready passthrough)', () => {
    const gate = createSwitchGate();
    const r = consult(gate, 'normal message');
    expect(r.kind).toBe('send');
    expect(r.outcome.action).toBe('send');
  });

  it('finishWorkflowReady (markReady) reopens the gate; held msg is drainable for replay', () => {
    const gate = createSwitchGate();
    gate.beginSwitch('owner/ip/rtl_gen');
    consult(gate, 'held while switching');
    gate.markReady(); // dismissWorkflowReady settle wiring
    expect(gate.isSwitching()).toBe(false);
    // The EXISTING held-input replay flushes via the same heldSubmitRef path; the
    // gate preserves the queued msg until drained (no data loss, no duplication).
    expect(gate.drain().map((m) => m.text)).toEqual(['held while switching']);
    // Reopened gate now sends.
    expect(consult(gate, 'after ready').kind).toBe('send');
  });

  it('failWorkflowReady (markFailed) reopens the gate but PRESERVES held input', () => {
    const gate = createSwitchGate();
    gate.beginSwitch('owner/ip/rtl_gen');
    consult(gate, 'typed during failed switch');
    gate.markFailed(); // failWorkflowReady wiring
    expect(gate.isSwitching()).toBe(false);
    expect(gate.drain().map((m) => m.text)).toEqual(['typed during failed switch']);
  });

  it('re-switch before settle keeps earlier held input (begin preserves pending)', () => {
    const gate = createSwitchGate();
    gate.beginSwitch('owner/ip/a');
    consult(gate, 'held for a');
    gate.beginSwitch('owner/ip/b'); // fast workflow sweep re-targets
    consult(gate, 'held for b');
    expect(gate.isSwitching()).toBe(true);
    gate.markReady();
    expect(gate.drain().map((m) => m.text)).toEqual(['held for a', 'held for b']);
  });

  // ── CRITICAL #2: server-driven workflow switch reopens the gate ──────────
  // Reproduces the onSessionSwitched reopening logic added to
  // workspace-root-data-hook.tsx / workspace.jsx. A server-announced switch
  // reaches the Workspace via the atlas-session-switched handler ONLY; the
  // client beginWorkflowReady->finishWorkflowReady lifecycle does NOT run, so
  // without this reopen the gate stays 'switching' and the first prompt after
  // the switch is held forever.
  const onServerSwitchReopen = (gate: ReturnType<typeof createSwitchGate>) => {
    // Mirror of the handler: only reopen if the gate is still switching, and
    // fire markReady() exactly once.
    if (gate.isSwitching()) gate.markReady();
  };

  it('server-driven switch (no client finish) reopens the gate so route() is ready', () => {
    const gate = createSwitchGate();
    // A CLIENT beginSwitch is in flight (gate switching) and the user types a
    // prompt in the one-frame window — it is HELD.
    gate.beginSwitch('owner/ip/rtl_gen');
    const held = consult(gate, 'first command after the switch');
    expect(held.kind).toBe('held');
    expect(gate.route().status).toBe('switching');

    // The SERVER confirms the switch (atlas-session-switched). The client
    // finishWorkflowReady never ran — only this server-driven reopen does.
    onServerSwitchReopen(gate);

    // Gate is READY again (route() reports the ready singleton, not switching).
    expect(gate.route().status).toBe('ready');
    expect(gate.isSwitching()).toBe(false);
    // The held prompt is drainable for the FIFO replay (not eaten).
    expect(gate.drain().map((m) => m.text)).toEqual(['first command after the switch']);
    // Reopened gate now sends the next prompt straight through.
    expect(consult(gate, 'next prompt').kind).toBe('send');
  });

  it('server reopen fires markReady exactly once and is a no-op when already ready', () => {
    const gate = createSwitchGate();
    gate.beginSwitch('owner/ip/lint');
    consult(gate, 'held during server switch');
    // First server confirmation reopens.
    onServerSwitchReopen(gate);
    expect(gate.isSwitching()).toBe(false);
    // A second/late server event (or a duplicated dispatch) must NOT re-disturb
    // the gate or drop the still-undrained held prompt.
    onServerSwitchReopen(gate);
    expect(gate.isSwitching()).toBe(false);
    expect(gate.drain().map((m) => m.text)).toEqual(['held during server switch']);
  });

  it('Ready phase opens the live gate immediately instead of waiting for overlay dismissal', () => {
    const sessionHook = readFileSync(`${process.cwd()}/workspace-root-session-hook.tsx`, 'utf8');
    const finishStart = sessionHook.indexOf('const finishWorkflowReady');
    const finishBody = sessionHook.slice(finishStart, sessionHook.indexOf('const failWorkflowReady', finishStart));
    expect(finishBody).toContain('switchGateRef.current.markReady();');
    expect(finishBody.indexOf('switchGateRef.current.markReady();')).toBeLessThan(
      finishBody.indexOf("updateWorkflowReady(seq, { phase: 'ready'"),
    );

    const dataHook = readFileSync(`${process.cwd()}/workspace-root-data-hook.tsx`, 'utf8');
    expect(dataHook).toContain("workflowReady && workflowReady.phase !== 'ready'");

    const renderPath = readFileSync(`${process.cwd()}/workspace-root-render.tsx`, 'utf8');
    expect(renderPath).toContain("workflowReady && workflowReady.phase !== 'ready'");
    expect(renderPath).toContain('disabled={workflowReadyBlocking}');
  });
});
