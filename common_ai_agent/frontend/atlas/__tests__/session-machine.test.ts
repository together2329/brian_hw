// __tests__/session-machine.test.ts
//
// TDD spec for the PURE switch-gate (createSwitchGate). Written FIRST; the stub
// in session-machine.ts must make these FAIL for the right reason, then the real
// implementation must make them GREEN.
//
// The gate is the synchronous mirror of the React `workflowReady` state: when held
// in a ref it is read synchronously inside submitMsg, which is what closes the
// one-frame "send while switching" race that React's async commit would otherwise
// open.

import { describe, it, expect } from 'vitest';
import { createSwitchGate } from '../session-machine';
import type { Msg, Route, SubmitOutcome } from '../session-protocol';

const msg = (text: string, meta?: Record<string, unknown>): Msg =>
  meta ? { text, meta } : { text };

describe('createSwitchGate — initial state', () => {
  it("starts ready: route().status === 'ready'", () => {
    const gate = createSwitchGate();
    expect(gate.route().status).toBe('ready');
    expect(gate.isSwitching()).toBe(false);
  });
});

describe('createSwitchGate — submit() while ready', () => {
  it("submit() in ready returns {action:'send', msg}", () => {
    const gate = createSwitchGate();
    const m = msg('hello');
    const outcome = gate.submit(m);
    expect(outcome.action).toBe('send');
    if (outcome.action === 'send') {
      expect(outcome.msg).toEqual(m);
    }
  });

  it('submit() in ready does NOT enqueue (drain() === [])', () => {
    const gate = createSwitchGate();
    gate.submit(msg('hello'));
    expect(gate.drain()).toEqual([]);
  });
});

describe('createSwitchGate — beginSwitch()', () => {
  it("beginSwitch(t) sets route to {status:'switching', target:t, pending:[]}", () => {
    const gate = createSwitchGate();
    gate.beginSwitch('sess-1');
    const r = gate.route();
    expect(r.status).toBe('switching');
    if (r.status === 'switching') {
      expect(r.target).toBe('sess-1');
      expect(r.pending).toEqual([]);
    }
    expect(gate.isSwitching()).toBe(true);
  });
});

describe('createSwitchGate — submit() while switching (the hold)', () => {
  it("submit() while switching returns {action:'held', queued:1} and does NOT send", () => {
    const gate = createSwitchGate();
    gate.beginSwitch('sess-1');
    const outcome = gate.submit(msg('held-1'));
    expect(outcome.action).toBe('held');
    if (outcome.action === 'held') {
      expect(outcome.queued).toBe(1);
    }
    // It must NOT have produced a send.
    expect(outcome.action).not.toBe('send');
  });

  it('multiple submits while switching accumulate FIFO (queued increments 1,2,3)', () => {
    const gate = createSwitchGate();
    gate.beginSwitch('sess-1');
    const o1 = gate.submit(msg('a'));
    const o2 = gate.submit(msg('b'));
    const o3 = gate.submit(msg('c'));
    expect(o1).toEqual({ action: 'held', queued: 1 });
    expect(o2).toEqual({ action: 'held', queued: 2 });
    expect(o3).toEqual({ action: 'held', queued: 3 });
    const r = gate.route();
    if (r.status === 'switching') {
      expect(r.pending.map((m) => m.text)).toEqual(['a', 'b', 'c']);
    } else {
      throw new Error('expected switching route');
    }
  });
});

describe('createSwitchGate — drain()', () => {
  it('drain() returns held msgs in FIFO order', () => {
    const gate = createSwitchGate();
    gate.beginSwitch('sess-1');
    gate.submit(msg('a'));
    gate.submit(msg('b'));
    gate.submit(msg('c'));
    expect(gate.drain().map((m) => m.text)).toEqual(['a', 'b', 'c']);
  });

  it('drain() empties the queue (second drain() === [])', () => {
    const gate = createSwitchGate();
    gate.beginSwitch('sess-1');
    gate.submit(msg('a'));
    gate.submit(msg('b'));
    expect(gate.drain().length).toBe(2);
    // EXACTLY ONCE: a second drain yields nothing.
    expect(gate.drain()).toEqual([]);
  });
});

describe('createSwitchGate — pendingCount()', () => {
  it('pendingCount() reflects held depth without consuming the FIFO', () => {
    const gate = createSwitchGate();
    expect(gate.pendingCount()).toBe(0);
    gate.beginSwitch('sess-1');
    gate.submit(msg('a'));
    gate.submit(msg('b'));
    expect(gate.pendingCount()).toBe(2);
    // Non-consuming: a peek must not empty the queue.
    expect(gate.pendingCount()).toBe(2);
    expect(gate.drain().map((m) => m.text)).toEqual(['a', 'b']);
    expect(gate.pendingCount()).toBe(0);
  });

  it('pendingCount() stays accurate AFTER markReady()/markFailed() (route() would hide it)', () => {
    const ready = createSwitchGate();
    ready.beginSwitch('sess-1');
    ready.submit(msg('held-ready'));
    ready.markReady();
    // route() now reports the ready singleton (no pending field), but the FIFO
    // still holds the switch-time prompt — pendingCount() is the live-replay's
    // only way to see it.
    expect(ready.route().status).toBe('ready');
    expect(ready.pendingCount()).toBe(1);
    expect(ready.drain().map((m) => m.text)).toEqual(['held-ready']);

    const failed = createSwitchGate();
    failed.beginSwitch('sess-2');
    failed.submit(msg('held-failed'));
    failed.markFailed();
    expect(failed.route().status).toBe('ready');
    expect(failed.pendingCount()).toBe(1);
    expect(failed.drain().map((m) => m.text)).toEqual(['held-failed']);
  });
});

describe('createSwitchGate — markReady() / markFailed()', () => {
  it('markReady() after switching returns route to ready; subsequent submit() sends', () => {
    const gate = createSwitchGate();
    gate.beginSwitch('sess-1');
    gate.markReady();
    expect(gate.route().status).toBe('ready');
    const outcome = gate.submit(msg('after-ready'));
    expect(outcome.action).toBe('send');
  });

  it('markFailed() after switching returns route to ready; subsequent submit() sends', () => {
    const gate = createSwitchGate();
    gate.beginSwitch('sess-1');
    gate.markFailed();
    expect(gate.route().status).toBe('ready');
    const outcome = gate.submit(msg('after-fail'));
    expect(outcome.action).toBe('send');
  });

  it('markFailed() preserves already-held msgs for drain() (no data loss on failure)', () => {
    const gate = createSwitchGate();
    gate.beginSwitch('sess-1');
    gate.submit(msg('a'));
    gate.submit(msg('b'));
    gate.markFailed();
    // Per design: markFailed preserves held msgs (no data loss).
    expect(gate.drain().map((m) => m.text)).toEqual(['a', 'b']);
  });
});

describe('createSwitchGate — re-switch keeps held input', () => {
  it('beginSwitch -> submit(a) -> beginSwitch(newTarget) preserves a in pending (re-switch keeps held input)', () => {
    const gate = createSwitchGate();
    gate.beginSwitch('sess-1');
    gate.submit(msg('a'));
    gate.beginSwitch('sess-2');
    const r = gate.route();
    expect(r.status).toBe('switching');
    if (r.status === 'switching') {
      expect(r.target).toBe('sess-2');
      // 'a' is preserved across the re-switch (no loss, no duplicate).
      expect(r.pending.map((m) => m.text)).toEqual(['a']);
    }
    // And a fresh submit on the new target still accumulates without losing 'a'.
    const o = gate.submit(msg('b'));
    expect(o).toEqual({ action: 'held', queued: 2 });
    expect(gate.drain().map((m) => m.text)).toEqual(['a', 'b']);
  });
});

describe('createSwitchGate — REGRESSION: the one-frame race', () => {
  it("REGRESSION (the race): beginSwitch(t) THEN submit(m) in same tick yields action:'held', never 'send'", () => {
    const gate = createSwitchGate();
    // Simulate the React-commit race: beginSwitch and submit happen synchronously,
    // back-to-back, in the same tick. Because submit() reads the gate synchronously,
    // the message MUST be held — it can never escape as a send.
    gate.beginSwitch('sess-race');
    const outcome: SubmitOutcome = gate.submit(msg('would-have-leaked'));
    expect(outcome.action).toBe('held');
    expect(outcome.action).not.toBe('send');
  });
});

describe('createSwitchGate — purity', () => {
  it('purity: gate methods touch no globals (runs with window/document/WebSocket undefined, no throw)', () => {
    const g = globalThis as unknown as Record<string, unknown>;
    const saved = {
      window: g.window,
      document: g.document,
      WebSocket: g.WebSocket,
    };
    try {
      delete g.window;
      delete g.document;
      delete g.WebSocket;
      const gate = createSwitchGate();
      expect(() => {
        gate.route();
        gate.isSwitching();
        gate.submit(msg('a'));
        gate.beginSwitch('s');
        gate.submit(msg('b'));
        gate.pendingCount();
        gate.markReady();
        gate.pendingCount();
        gate.drain();
        gate.markFailed();
      }).not.toThrow();
    } finally {
      if (saved.window !== undefined) g.window = saved.window;
      if (saved.document !== undefined) g.document = saved.document;
      if (saved.WebSocket !== undefined) g.WebSocket = saved.WebSocket;
    }
  });
});

describe('createSwitchGate — protocol type-test (compile-time)', () => {
  it("protocol type-test: 'switching' Route has no send-bearing field (// @ts-expect-error compiled assertion)", () => {
    const switching: Route = { status: 'switching', target: 't', pending: [] };
    if (switching.status === 'switching') {
      // @ts-expect-error — the 'switching' variant has no `msg` / send-bearing field.
      const leak = switching.msg;
      void leak;
    }
    // Runtime side of the assertion: there is genuinely no such field.
    expect((switching as Record<string, unknown>).msg).toBeUndefined();

    // A SubmitOutcome 'send' is only constructible with a msg payload; a 'held'
    // outcome has no msg. This narrows correctly at compile time.
    const held: SubmitOutcome = { action: 'held', queued: 1 };
    if (held.action === 'held') {
      // @ts-expect-error — 'held' outcome has no `msg` field to send.
      const m = held.msg;
      void m;
    }
    expect(true).toBe(true);
  });
});

describe('createSwitchGate — replay flushes AFTER ready', () => {
  it('drain() after markReady still returns previously-held msgs (replay flushes AFTER ready)', () => {
    const gate = createSwitchGate();
    gate.beginSwitch('sess-1');
    gate.submit(msg('a'));
    gate.submit(msg('b'));
    gate.markReady();
    // markReady does NOT clear the queue; held msgs remain for the post-ready drain.
    expect(gate.route().status).toBe('ready');
    expect(gate.drain().map((m) => m.text)).toEqual(['a', 'b']);
    // And exactly once.
    expect(gate.drain()).toEqual([]);
  });
});
