// session-machine.ts
//
// PURE switch-gate factory. No React / DOM / window / ws / timers — just a closure
// over a tiny internal state. When held in a useRef it is the SYNCHRONOUS mirror of
// the React `workflowReady` state, and submit() is read synchronously inside
// submitMsg. That synchronous read is what closes the one-frame "send while
// switching" race that React's async commit would otherwise open.
//
// Discriminated-union design (see session-protocol.ts): the "switching" Route variant
// carries only a `pending` FIFO and has NO send-bearing field, so "send while
// switching" is unrepresentable in the types and unreachable at runtime — submit()
// can only return action:"send" when route.status === "ready".

import type { Msg, Route, SubmitOutcome, SwitchTarget } from './session-protocol';
import { READY } from './session-protocol';

export interface SwitchGate {
  /**
   * Enter "switching" toward `target`. From this synchronous instant submit() holds.
   * A re-switch (beginSwitch while already switching) preserves already-held pending
   * messages — no loss, no duplication — and just retargets.
   */
  beginSwitch(target: SwitchTarget): void;

  /** Switch succeeded: route -> ready. Held msgs remain queued for drain(). */
  markReady(): void;

  /** Switch failed: route -> ready (input flows again). Held msgs preserved (no data loss). */
  markFailed(): void;

  /**
   * SYNCHRONOUS decision. Returns {action:"send", msg} iff route is "ready"; else
   * enqueues FIFO and returns {action:"held", queued:n}. This read closes the race.
   */
  submit(msg: Msg): SubmitOutcome;

  /** Returns queued msgs FIFO and clears the queue. Feeds the EXISTING held-input replay. */
  drain(): Msg[];

  /** Discriminated-union snapshot of the gate. */
  route(): Route;

  /** Convenience: true iff currently switching. */
  isSwitching(): boolean;
}

export function createSwitchGate(initial: Route = READY): SwitchGate {
  // Internal mutable state. `switching` is the discriminant; `target` is meaningful
  // only while switching; `pending` is the append-only FIFO of held messages and
  // persists across markReady/markFailed (drain is the only thing that clears it).
  let switching: boolean = initial.status === 'switching';
  let target: SwitchTarget = initial.status === 'switching' ? initial.target : '';
  // Copy any seeded pending so callers can't mutate internal state through `initial`.
  let pending: Msg[] = initial.status === 'switching' ? [...initial.pending] : [];

  return {
    beginSwitch(nextTarget: SwitchTarget): void {
      // Preserve already-held pending across a re-switch; just (re)enter switching.
      switching = true;
      target = nextTarget;
    },

    markReady(): void {
      // Succeeded: input flows again. Held msgs remain queued for the post-ready drain.
      switching = false;
      target = '';
    },

    markFailed(): void {
      // Failed: input flows again. Held msgs preserved (no data loss on failure).
      switching = false;
      target = '';
    },

    submit(msg: Msg): SubmitOutcome {
      if (switching) {
        pending.push(msg);
        return { action: 'held', queued: pending.length };
      }
      return { action: 'send', msg };
    },

    drain(): Msg[] {
      const out = pending;
      pending = [];
      return out;
    },

    route(): Route {
      if (switching) {
        // Return a defensive copy of pending so the snapshot can't mutate internal state.
        return { status: 'switching', target, pending: [...pending] };
      }
      return READY;
    },

    isSwitching(): boolean {
      return switching;
    },
  };
}
