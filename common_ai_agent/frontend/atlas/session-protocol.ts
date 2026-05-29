// session-protocol.ts
//
// Pure type protocol for the switch-gate. No React / DOM / window / ws / timers.
//
// KEY INVARIANT: a "send" is ONLY representable when route.status === "ready".
// The "switching" variant of Route carries only a `pending` FIFO queue — there is
// no field through which a send could be expressed — so "send while switching" is a
// compile-time impossibility AND unreachable at runtime.

/** A single user message flowing through the gate. */
export interface Msg {
  readonly text: string;
  readonly meta?: Readonly<Record<string, unknown>>;
}

/** The session the gate is switching toward. */
export type SwitchTarget = string;

/**
 * Discriminated-union snapshot of the gate.
 *
 * - "switching": carries the target plus an append-only FIFO of held messages.
 *   It has NO send-bearing field, so sending cannot be expressed here.
 * - "ready": input flows; submit() may return action:"send".
 */
export type Route =
  | { readonly status: 'switching'; readonly target: SwitchTarget; readonly pending: readonly Msg[] }
  | { readonly status: 'ready' };

/**
 * The synchronous decision returned by submit().
 *
 * - "send": the caller must perform the send (only reachable when route is ready).
 * - "held": the message was enqueued FIFO; `queued` is the new queue depth.
 */
export type SubmitOutcome =
  | { readonly action: 'send'; readonly msg: Msg }
  | { readonly action: 'held'; readonly queued: number };

/** The ready route singleton. */
export const READY: Route = { status: 'ready' };
