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
});
