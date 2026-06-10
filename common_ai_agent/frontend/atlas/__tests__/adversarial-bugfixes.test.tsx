// __tests__/adversarial-bugfixes.test.tsx
//
// Regression gates for three CONFIRMED adversarial-review bugs:
//
//   BUG A (double execution) — when sendPrompt's ack resolves ok:false (worker
//     warming → agent_accepted{ok:false}), the held-input replay MUST re-fire
//     under the ORIGINAL msg_id, never mint a NEW distinct one. A second distinct
//     msg_id slips past the backend's per-session has_msg_id dedup and, if the
//     worker is warm by replay time, executes the prompt TWICE.
//
//   BUG B (switch-gate stranded 'switching' forever) — beginWorkflowReady's 7s
//     safety-net timeout must give the LIVE switch a seq-guarded, direct gate
//     reopen (markReady), so an overlapping switch whose shared-slot timer was
//     clobbered AND whose continuation never settles still reopens the gate.
//
//   BUG C is covered in workspace-root.tsx's onSubmitPending path; the QA-board
//     warning-on-miss is asserted by source presence here (the board component is
//     window-stubbed in the mount harness, so the wired-callback behavior is
//     pinned via source so a refactor that drops the !sent.ok check fails).

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

vi.setConfig({ testTimeout: 30000, hookTimeout: 30000 });

import { render, cleanup, fireEvent, act } from '@testing-library/react';
import { createSwitchGate } from '../session-machine';

import '../ui-utils.tsx';

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoFile = (name: string) => readFileSync(join(__dirname, '..', name), 'utf8');

type AnyWindow = typeof window & Record<string, any>;

const PassthroughPanel = ({ children }: { children?: unknown }) =>
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (children as any) ?? null;

// Backend double with PER-SEND ack control. Unlike the shared makeBackend in
// submitmsg-dispatch.test.tsx (single global ackMode), this lets a test fail the
// FIRST send (accepted-drop) while AUTO-ACCEPTING every later send (the replay),
// which is exactly the BUG A scenario.
function makeBackend() {
  const subs: Record<string, Array<(m: any) => void>> = {};
  const sent: any[] = [];
  // Per-send policy keyed by send index: 'accept' | 'drop' (accepted ok:false).
  let policyFor: (index: number) => 'accept' | 'drop' = () => 'accept';
  const emit = (event: string, m: any) => {
    (subs[event] || []).forEach((cb) => { try { cb(m); } catch (_) {} });
  };
  const backend = {
    state: 'open',
    getConnectionState: () => 'open',
    send: vi.fn((msg: any) => {
      const index = sent.length;
      sent.push(msg);
      const policy = policyFor(index);
      Promise.resolve().then(() => {
        // Always emit agent_received first (mirrors the real backend: receipt
        // precedes acceptance; backend.js clears its retry on agent_received).
        emit('agent_received', { msg_id: msg.msg_id });
        if (policy === 'drop') {
          emit('agent_accepted', { msg_id: msg.msg_id, ok: false, error: 'worker warming (test)' });
        } else {
          emit('agent_accepted', { msg_id: msg.msg_id, ok: true });
        }
      });
    }),
    subscribe: vi.fn((event: string, cb: (m: any) => void) => {
      (subs[event] || (subs[event] = [])).push(cb);
      return () => { subs[event] = (subs[event] || []).filter((x) => x !== cb); };
    }),
    on: vi.fn(),
    off: vi.fn(),
    switchSession: vi.fn(),
    connect: vi.fn(),
  };
  return {
    backend,
    sent,
    setPolicy: (fn: (index: number) => 'accept' | 'drop') => { policyFor = fn; },
  };
}

let bk: ReturnType<typeof makeBackend>;

function installWindowStubs() {
  const w = window as AnyWindow;
  for (const name of [
    'SsotReviewPane', 'SsotQaBoard', 'SsotDocPane', 'PreviewPane',
    'AskUserPrompt', 'ProgressPanel', 'TodoPanel', 'OrchestratorChatPanel',
    'GitPanel', 'AgentStatusPanel', 'Coverage', 'SimDebug', 'DebugTab', 'GitTab',
  ]) {
    w[name] = PassthroughPanel;
  }
  w.Kbd = ({ children }: { children?: unknown }) => children ?? null;
  const normalize = (s: any) => String(s || '').trim().toLowerCase();
  w.normalizeAtlasSessionName = normalize;
  w.CONTEXT = {};
  w.ACTIVE_SESSION = '';
  w.ACTIVE_IP = '';
  w.ATLAS_UI_LANG = 'ko';
  w.ATLAS_USER = { username: 'alice' };
  w.FLOW_STAGES = [];
  w.TODOS = [];
  w.SCOPE_PATH = '';
  w.FILE_TREE_LOADING = false;
  w.FILE_TREE_ERROR = null;
  w.FILE_TREE_LAST_REFRESH = 0;
  w.ATLAS_EXEC_MODE = '';
  delete w.ATLAS_DEFAULT_EXEC_MODE;
  delete w.ATLAS_BOOT_CONFIG;
  w.atlasData = {
    setScopePath: vi.fn(),
    sessionFor: (ip: string, wf: string) => `alice/${ip}/${wf}`,
    normalizeSessionName: normalize,
    refreshFileTree: vi.fn(),
  };
  bk = makeBackend();
  w.backend = bk.backend;
  w.AtlasBannerLogic = { shouldShowSelectIpBanner: () => false };
  global.fetch = vi.fn(async () =>
    new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } }),
  ) as unknown as typeof fetch;
}

function typeAndSubmit(container: HTMLElement, text: string) {
  const textarea = container.querySelector('textarea') as HTMLTextAreaElement;
  expect(textarea).not.toBeNull();
  expect(textarea.disabled).toBe(false);
  fireEvent.change(textarea, { target: { value: text } });
  fireEvent.keyDown(textarea, { key: 'Enter', code: 'Enter' });
  return textarea;
}

async function mountWorkspace() {
  const { Workspace } = await import('../workspace.tsx');
  let utils: ReturnType<typeof render>;
  await act(async () => {
    utils = render(<Workspace dir="/tmp/ws" uiLang="ko" />);
  });
  // @ts-expect-error assigned inside act
  return utils;
}

const flush = (ms: number) => new Promise((r) => setTimeout(r, ms));

describe('BUG A — dropped-prompt replay reuses the ORIGINAL msg_id (no double execution)', () => {
  beforeEach(() => { installWindowStubs(); });
  afterEach(() => { cleanup(); vi.restoreAllMocks(); });

  it('an agent_accepted{ok:false} drop does NOT produce two DISTINCT msg_id sends', async () => {
    const w = window as AnyWindow;
    w.ATLAS_EXEC_MODE = '';
    w.ACTIVE_SESSION = 'alice/myip/rtl_gen';
    w.ACTIVE_IP = 'myip';
    // First send is dropped (worker warming); every later send (the replay) is
    // accepted so the held state settles and the test terminates deterministically.
    bk.setPolicy((index) => (index === 0 ? 'drop' : 'accept'));

    const { container } = await mountWorkspace();
    const textarea = container.querySelector('textarea') as HTMLTextAreaElement;

    await act(async () => {
      typeAndSubmit(container, 'implement the FIFO');
      // Let the ack microtasks resolve (agent_received → agent_accepted{ok:false}).
      // This drives waitForPromptAck → onMiss → holdUnacknowledgedInput, which
      // arms the single-slot held entry carrying the ORIGINAL msg_id.
      await Promise.resolve();
      await Promise.resolve();
    });

    // The held-input replay effect only re-runs when one of its deps changes.
    // Nudge `input` (trailing space → trims back to the held text, so the
    // box-unchanged guard still matches) to re-run the effect; this is the
    // realistic trigger by which the replay later re-fires the held prompt.
    await act(async () => {
      fireEvent.change(textarea, { target: { value: 'implement the FIFO ' } });
      // The nudged box syncs to the parent on the 240ms prose tier, THEN the
      // replay fires on an 80ms timer; wait past both, then let the replay
      // send's own ack settle.
      await flush(420);
      await Promise.resolve();
      await Promise.resolve();
    });

    const promptSends = bk.sent.filter((m) => m && m.type === 'prompt');
    // The prompt was attempted at least once...
    expect(promptSends.length).toBeGreaterThanOrEqual(1);
    // ...and CRITICAL: every prompt send carries the SAME msg_id. A replay that
    // minted a fresh id would yield >1 distinct id — the double-execution race.
    const distinctIds = new Set(promptSends.map((m) => m.msg_id));
    expect(distinctIds.size).toBe(1);
    // The text round-tripped intact across the replay.
    expect(promptSends.every((m) => m.text === 'implement the FIFO')).toBe(true);
  });

  it('an ack-miss replay is capped after one automatic retry', async () => {
    const w = window as AnyWindow;
    w.ATLAS_EXEC_MODE = '';
    w.ACTIVE_SESSION = 'alice/myip/rtl-gen';
    w.ACTIVE_IP = 'myip';
    w.FLOW_STAGES = [{ id: 'rtl-gen' }];
    bk.setPolicy(() => 'drop');

    const { container } = await mountWorkspace();
    const textarea = container.querySelector('textarea') as HTMLTextAreaElement;

    await act(async () => {
      typeAndSubmit(container, 'implement the FIFO');
      await Promise.resolve();
      await Promise.resolve();
    });

    await act(async () => {
      fireEvent.change(textarea, { target: { value: 'implement the FIFO ' } });
      await flush(420);
      await Promise.resolve();
      await Promise.resolve();
    });

    let promptSends = bk.sent.filter((m) => m && m.type === 'prompt');
    expect(promptSends.length).toBe(2);
    expect(new Set(promptSends.map((m) => m.msg_id)).size).toBe(1);

    await act(async () => {
      fireEvent.change(textarea, { target: { value: 'implement the FIFO  ' } });
      await flush(420);
      await Promise.resolve();
      await Promise.resolve();
    });

    promptSends = bk.sent.filter((m) => m && m.type === 'prompt');
    expect(promptSends.length).toBe(2);
    expect(textarea.value.trim()).toBe('implement the FIFO');
    expect(container.textContent || '').toMatch(/Input not confirmed after retry/i);
    expect(container.textContent || '').toMatch(/session=.*alice\/myip\/rtl-gen.*ip=.*myip.*workflow=.*rtl-gen.*msg_id=/i);
  });

  it('a normal accepted send mints exactly one id and is never replayed', async () => {
    const w = window as AnyWindow;
    w.ATLAS_EXEC_MODE = '';
    w.ACTIVE_SESSION = 'alice/myip/rtl_gen';
    w.ACTIVE_IP = 'myip';
    bk.setPolicy(() => 'accept');

    const { container } = await mountWorkspace();
    await act(async () => {
      typeAndSubmit(container, 'design the bus');
      await Promise.resolve();
      await Promise.resolve();
      await flush(140);
      await Promise.resolve();
    });

    const promptSends = bk.sent.filter((m) => m && m.type === 'prompt');
    // Happy path: a single send, a single id, no spurious replay.
    expect(promptSends.length).toBe(1);
  });
});

describe('BUG B — overlapping switch whose continuation never settles still reopens via the safety net', () => {
  // Faithful reproduction of beginWorkflowReady's 7s safety-net timeout BODY. The
  // shared workflowReadyTimeoutRef can be clobbered by an overlapping switch, so
  // the deferred dismissWorkflowReady→markReady may never run; the fix adds a
  // direct, seq-guarded markReady() in the timeout body itself.
  const runSafetyNet = (
    gate: ReturnType<typeof createSwitchGate>,
    seq: number,
    workflowReadySeqRef: { current: number },
  ) => {
    // Mirror of the patched timeout body's gate reopen (session-hook L216-218):
    if (workflowReadySeqRef.current === seq && gate) gate.markReady();
  };

  it('the live switch reopens even when its shared-slot timer was clobbered and the fetch never settles', () => {
    const gate = createSwitchGate();
    const seqRef = { current: 0 };

    // Switch A begins, arms its net (seq 1, owns the shared ref).
    const seqA = (seqRef.current = 1);
    gate.beginSwitch('owner/ip/a');

    // Switch B begins before A settled — B bumps the seq and is now the LIVE owner.
    // (re-switch preserves A's held pending; B clobbers the shared timer slot.)
    const seqB = (seqRef.current = 2);
    gate.beginSwitch('owner/ip/b');
    const held = gate.submit({ text: 'typed during the live switch' });
    expect(held.action).toBe('held');

    // A's late finish clears the shared timer (the clobber): B's deferred
    // markReady can no longer fire. B's awaited continuation NEVER settles.
    // Without the fix the gate is stuck 'switching' forever.

    // B's OWN safety-net body fires at the 7s deadline. It is the live owner
    // (seqRef.current === seqB), so its seq-guarded markReady reopens the gate.
    runSafetyNet(gate, seqB, seqRef);

    expect(gate.isSwitching()).toBe(false);
    // The held prompt survived for the FIFO replay (no data loss).
    expect(gate.drain().map((m) => m.text)).toEqual(['typed during the live switch']);
    // A STALE switch's net (seqA, no longer the owner) must NOT reopen the gate.
    const gate2 = createSwitchGate();
    const seqRef2 = { current: 5 }; // a newer switch already owns it
    gate2.beginSwitch('owner/ip/x');
    runSafetyNet(gate2, 1, seqRef2); // stale seq 1 != 5 → suppressed
    expect(gate2.isSwitching()).toBe(true);
  });

  it('source guard: beginWorkflowReady\'s safety-net timeout contains the seq-guarded gate reopen', () => {
    const src = repoFile('workspace-root-session-hook.tsx');
    // The reproduction above mirrors this exact line; pin it so the two can't drift.
    expect(src).toContain('if (workflowReadySeqRef.current === seq && switchGateRef.current) {');
    expect(src).toMatch(/switchGateRef\.current\.markReady\(\);/);
  });
});

describe('BUG C — QA-board onSubmitPending surfaces a warning when the send misses', () => {
  it('source guard: onSubmitPending captures sendPrompt\'s return and warns on !sent.ok', () => {
    const src = repoFile('workspace-root.tsx');
    // The send return is captured (not discarded into a bare try/catch).
    expect(src).toContain('sent = sendPrompt(payload, sessionName);');
    // And a miss appends a feed warning rather than silently dropping the answer.
    expect(src).toContain('if (!sent || sent.ok === false) {');
    expect(src).toMatch(/Answer not delivered/);
  });
});
