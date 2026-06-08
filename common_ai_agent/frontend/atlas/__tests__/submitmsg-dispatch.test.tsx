// __tests__/submitmsg-dispatch.test.tsx
//
// THE MISSING DISPATCH GATE for the ported workspace submitMsg (the ~510-line
// dispatch hub faithfully ported from workspace.jsx submitMsg L3801-L4356 into
// workspace-root-data-hook.tsx, L1366-1895).
//
// WHY THIS EXISTS — the render-smoke gate (workspace-render-smoke.test.tsx) only
// MOUNTS the Workspace. It proves renderPromptRow/renderChatPane resolved to real
// functions and a <textarea> exists, but it NEVER presses Enter — so submitMsg's
// branch routing is never exercised. That is exactly how a happy-path stub passed
// "green-while-broken": a 46-line stub that just shipped everything to the agent
// would also mount fine and render a textarea. Mounting != dispatching.
//
// THIS test mounts the REAL Workspace (same self-wired path as the smoke gate),
// types into the live composer textarea, presses Enter, and asserts WHERE the
// input went. It exercises the four load-bearing routing contracts of the hub:
//
//   (a) a CLIENT-side slash command (`/scope x`) is handled IN-BROWSER —
//       window scope is set, NOTHING is shipped via sendPrompt/agent-prompt.
//   (b) in ORCHESTRATOR mode a plain prompt POSTs /api/pipeline/orchestrator/chat
//       (NOT sendPrompt — the orchestrator routes through HTTP, not the WS agent).
//   (c) a plain prompt in NORMAL mode calls sendPrompt (the WS agent path).
//   (d) when sendPrompt's ack never confirms (no agent_received/agent_accepted),
//       the input is HELD (heldSubmitRef populated + restored to the box), NOT
//       silently cleared — the anti-data-loss contract.
//
// WOULD-HAVE-CAUGHT-THE-STUB (noted per assertion below): the old happy-path stub
// unconditionally called sendPrompt(raw) and cleared the box. Against it:
//   (a) FAILS — stub ships "/scope x" to sendPrompt instead of handling locally.
//   (b) FAILS — stub calls sendPrompt, never fetches the orchestrator endpoint.
//   (d) FAILS — stub clears the input on send; heldSubmitRef stays null.
//   (c) is the only assertion the stub would have *passed* (both call sendPrompt),
//       which is precisely why a sendPrompt-only smoke check could not tell the
//       full hub from the stub. (a)/(b)/(d) are the discriminating gates.

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
// A full-app mount + a fireEvent dispatch cycle in jsdom can exceed the 5s
// default under load; widen the budget (mirrors the render-smoke gate).
vi.setConfig({ testTimeout: 30000, hookTimeout: 30000 });

import { render, cleanup, fireEvent, act, waitFor } from '@testing-library/react';

// Same load-order bridge the live app + the render-smoke gate rely on:
// ui-utils.tsx publishes window.CopyBtn / window._copyToClipboard on import, and
// workspace-markdown-chips.tsx binds window.CopyBtn at MODULE-LOAD time. Import
// it first so the bridge is real before the workspace bundle evaluates.
import '../ui-utils.tsx';

type AnyWindow = typeof window & Record<string, any>;

// Passthrough placeholder for the window-published ATLAS panels.
const PassthroughPanel = ({ children }: { children?: unknown }) =>
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  (children as any) ?? null;

// A controllable backend double. The REAL sendPrompt (session hook) calls
// backend.send(msg) then awaits an ack Promise that resolves only when a
// subscribed 'agent_received'/'agent_accepted' event matching msg.msg_id fires
// (else it times out at 7s). We capture send() calls and let each test decide
// whether to ACK (resolve ok) or WITHHOLD the ack (drive the held path) — without
// ever waiting on the real 7s timer.
function makeBackend() {
  const subs: Record<string, Array<(m: any) => void>> = {};
  const sent: any[] = [];
  let ackMode: 'accept' | 'withhold' | 'receivedOnly' = 'accept';
  const emit = (event: string, m: any) => {
    (subs[event] || []).forEach((cb) => { try { cb(m); } catch (_) {} });
  };
  const backend = {
    state: 'open',
    getConnectionState: () => 'open',
    send: vi.fn((msg: any) => {
      sent.push(msg);
      // Resolve the ack synchronously-ish on the microtask queue: the ack
      // Promise subscribes to these events inside sendPrompt BEFORE send()
      // returns, so emitting right after push lands on the live listeners.
      if (ackMode === 'accept') {
        Promise.resolve().then(() => {
          emit('agent_received', { msg_id: msg.msg_id });
          emit('agent_accepted', { msg_id: msg.msg_id, ok: true });
        });
      } else if (ackMode === 'receivedOnly') {
        Promise.resolve().then(() => {
          emit('agent_received', { msg_id: msg.msg_id });
        });
      }
      // ackMode === 'withhold' → emit nothing; we instead resolve the miss path
      // deterministically below (see withholdAndFailFast) so tests never wait 7s.
    }),
    subscribe: vi.fn((event: string, cb: (m: any) => void) => {
      (subs[event] || (subs[event] = [])).push(cb);
      return () => {
        subs[event] = (subs[event] || []).filter((x) => x !== cb);
      };
    }),
    on: vi.fn(),
    off: vi.fn(),
    switchSession: vi.fn(),
    connect: vi.fn(),
  };
  return {
    backend,
    sent,
    setAckMode: (m: 'accept' | 'withhold' | 'receivedOnly') => { ackMode = m; },
    // For the held-input test: after send(), immediately resolve the ack as a
    // FAILED acceptance for the just-sent msg. This drives waitForPromptAck's
    // onMiss → holdUnacknowledgedInput WITHOUT the 7s real-backend timeout.
    failLastSendFast: () => {
      const last = sent[sent.length - 1];
      if (!last) return;
      emit('agent_accepted', { msg_id: last.msg_id, ok: false, error: 'no ack (test)' });
    },
    acceptLastSendLate: () => {
      const last = sent[sent.length - 1];
      if (!last) return;
      emit('agent_accepted', { msg_id: last.msg_id, ok: true });
    },
  };
}

let bk: ReturnType<typeof makeBackend>;

function installWindowStubs() {
  const w = window as AnyWindow;

  for (const name of [
    'SsotReviewPane', 'SsotQaBoard', 'SsotDocPane', 'PreviewPane',
    'AskUserPrompt', 'ProgressPanel', 'TodoPanel', 'OrchestratorChatPanel',
    'GitPanel', 'AgentStatusPanel', 'Coverage', 'SimDebug', 'DebugTab',
    'GitTab',
  ]) {
    w[name] = PassthroughPanel;
  }
  w.Kbd = ({ children }: { children?: unknown }) => children ?? null;

  // normalizeUiSession() delegates to this; without it every session string
  // normalizes to '' and activeIp can never be derived (orchestrator gate fails
  // to find a real IP). A lowercase-trim identity matches the live normalizer's
  // shape closely enough for routing (owner/ip/workflow → ip).
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
  // Reset exec mode per test; each test opts INTO orchestrator where needed.
  w.ATLAS_EXEC_MODE = '';
  delete w.ATLAS_DEFAULT_EXEC_MODE;
  delete w.ATLAS_BOOT_CONFIG;

  // atlasData surface the submitMsg branches touch. setScopePath is called
  // UNGUARDED in the /scope branch (data-hook L1502), so it MUST exist; sessionFor
  // is optional-chained but provide a sane value for the orchestrator branch;
  // normalizeSessionName is the primary delegate for normalizeUiSession.
  w.atlasData = {
    setScopePath: vi.fn(),
    sessionFor: (ip: string, wf: string) => `alice/${ip}/${wf}`,
    normalizeSessionName: normalize,
    refreshFileTree: vi.fn(),
  };

  bk = makeBackend();
  w.backend = bk.backend;

  w.AtlasBannerLogic = { shouldShowSelectIpBanner: () => false };

  // Default network double: empty-OK JSON so mount-time polls settle. Individual
  // tests REPLACE this with a spy when they need to assert a specific POST.
  globalThis.fetch = vi.fn(async () =>
    new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } }),
  ) as unknown as typeof fetch;
}

// Type into the live composer textarea and press plain Enter (the wired path:
// onPromptKey → submitMsg() with the current input). fireEvent.change updates the
// controlled value via setInput; the keydown handler closes over the latest
// memoized submitMsg, so Enter dispatches the just-typed text.
function typeAndSubmit(container: HTMLElement, text: string) {
  const textarea = container.querySelector('textarea') as HTMLTextAreaElement;
  expect(textarea).not.toBeNull();
  expect(textarea.disabled).toBe(false); // workflowReady must be null → enabled
  fireEvent.change(textarea, { target: { value: text } });
  fireEvent.keyDown(textarea, { key: 'Enter', code: 'Enter' });
  return textarea;
}

async function mountWorkspace(props: { activeNamespace?: string; activeWorkflow?: string } = {}) {
  // Import AFTER stubs so the module-load window reads see them.
  const { Workspace } = await import('../workspace.tsx');
  let utils: ReturnType<typeof render>;
  await act(async () => {
    utils = render(
      <Workspace
        dir="/tmp/ws"
        uiLang="ko"
        activeNamespace={props.activeNamespace || ''}
        activeWorkflow={props.activeWorkflow || ''}
      />,
    );
  });
  // @ts-expect-error assigned inside act
  return utils;
}

describe('submitMsg dispatch routing (the missing TDD gate)', () => {
  beforeEach(() => {
    installWindowStubs();
  });

  afterEach(() => {
    vi.useRealTimers();
    cleanup();
    vi.restoreAllMocks();
  });

  // (a) CLIENT slash command — handled in-browser, NOT shipped to the agent.
  // CATCHES THE STUB: the happy-path stub would sendPrompt("/scope x") and clear
  // the box. Here we assert window scope was set locally AND sendPrompt was never
  // called with the slash text.
  it('(a) handles a client slash command (/scope) in-browser — never ships it via sendPrompt', async () => {
    const w = window as AnyWindow;
    const { container } = await mountWorkspace();

    await act(async () => {
      typeAndSubmit(container, '/scope subblock');
    });

    // Handled locally: the browser-side scope setter ran with the parsed arg.
    expect(w.atlasData.setScopePath).toHaveBeenCalledWith('subblock');
    // And it was NOT shipped to the agent: backend.send carries {type:'prompt'}.
    const shippedSlash = bk.sent.some(
      (m) => m && m.type === 'prompt' && String(m.text || '').includes('/scope'),
    );
    expect(shippedSlash).toBe(false);
    expect(bk.backend.send).not.toHaveBeenCalled();
  });

  // (b) ORCHESTRATOR mode plain prompt → POST /api/pipeline/orchestrator/chat.
  // CATCHES THE STUB: the stub would sendPrompt(raw) and never touch the
  // orchestrator HTTP endpoint. Here we assert the exact URL was fetched and
  // sendPrompt was NOT used.
  it('(b) in orchestrator mode a plain prompt POSTs /api/pipeline/orchestrator/chat (not sendPrompt)', async () => {
    const w = window as AnyWindow;
    // Opt into orchestrator mode and give it a real (non-default) active IP so
    // the orchestrator HTTP branch (not the held/guard paths) is reached.
    w.ATLAS_EXEC_MODE = 'orchestrator';
    w.ACTIVE_SESSION = 'alice/myip/orchestrator';
    w.ACTIVE_IP = 'myip';

    const fetchSpy = vi.fn(async (_input: RequestInfo | URL, _init?: RequestInit): Promise<Response> =>
      new Response('{"reply":""}', { status: 200, headers: { 'Content-Type': 'application/json' } }),
    );
    globalThis.fetch = fetchSpy as unknown as typeof fetch;

    const { container } = await mountWorkspace();

    await act(async () => {
      typeAndSubmit(container, 'design the AXI bridge');
    });

    const orchestratorChatCalls = fetchSpy.mock.calls.filter(
      ([url]) => String(url) === '/api/pipeline/orchestrator/chat',
    );
    expect(orchestratorChatCalls.length).toBeGreaterThanOrEqual(1);
    // The orchestrator routes through HTTP, NOT the WS agent prompt.
    const shippedPrompt = bk.sent.some((m) => m && m.type === 'prompt');
    expect(shippedPrompt).toBe(false);
    expect(bk.backend.send).not.toHaveBeenCalled();
    // And it did NOT also dispatch a worker job for a plain chat turn.
    const jobDispatchCalls = fetchSpy.mock.calls.filter(
      ([url]) => String(url) === '/api/job/dispatch',
    );
    expect(jobDispatchCalls.length).toBe(0);
  });

  it('(b2) workflow-dispatch prompt POSTs /api/job/dispatch without legacy session', async () => {
    const w = window as AnyWindow;
    w.ATLAS_EXEC_MODE = 'orchestrator';
    w.ACTIVE_SESSION = 'alice/s1/myip/orchestrator';
    w.ACTIVE_IP = 'myip';
    w.ATLAS_WORKSPACE_SESSION_ID = 's1';
    w.FLOW_STAGES = [{ id: 'rtl-gen' }];
    w.atlasData.sessionFor = (ip: string, wf: string) => `alice/s1/${ip}/${wf}`;

    const fetchSpy = vi.fn(async (input: RequestInfo | URL, _init?: RequestInit): Promise<Response> => {
      if (String(input) === '/api/job/dispatch') {
        return new Response('{"ok":true,"job_id":"job-1","workflow":"rtl-gen","session":"alice/s1/myip/rtl-gen","status":"queued"}', {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        });
      }
      return new Response('{}', { status: 200, headers: { 'Content-Type': 'application/json' } });
    });
    globalThis.fetch = fetchSpy as unknown as typeof fetch;

    const { container } = await mountWorkspace({
      activeNamespace: 'alice/s1/myip/orchestrator',
      activeWorkflow: 'orchestrator',
    });

    await act(async () => {
      window.dispatchEvent(new CustomEvent('atlas-session-switched', {
        detail: {
          sessionId: 'alice',
          namespace: 'alice/s1/myip/rtl-gen',
          session: 'alice/s1/myip/rtl-gen',
          ip: 'myip',
          workflow: 'rtl-gen',
        },
      }));
      await Promise.resolve();
      await Promise.resolve();
    });

    await act(async () => {
      typeAndSubmit(container, 'implement rtl');
      await Promise.resolve();
      await Promise.resolve();
    });

    const dispatchCall = fetchSpy.mock.calls.find(([url]) => String(url) === '/api/job/dispatch');
    expect(dispatchCall).toBeTruthy();
    const body = JSON.parse(String((dispatchCall?.[1] as RequestInit).body || '{}'));
    expect(body.workflow).toBe('rtl-gen');
    expect(body.ip).toBe('myip');
    expect(body.workspace_session).toBe('s1');
    expect(body.session).toBeUndefined();
  });

  // (c) NORMAL mode plain prompt → sendPrompt (the WS agent path).
  // NOTE: this is the ONE assertion the old stub would also have passed (both the
  // stub and the full hub call sendPrompt here). It is included to prove the
  // normal-mode path is intact, but it is NOT a stub discriminator on its own —
  // (a)/(b)/(d) are what expose the stub.
  it('(c) a plain prompt in normal mode calls sendPrompt (WS agent path)', async () => {
    const w = window as AnyWindow;
    w.ATLAS_EXEC_MODE = ''; // normal (single-worker) mode
    w.ACTIVE_SESSION = 'alice/myip/rtl_gen';
    w.ACTIVE_IP = 'myip';
    bk.setAckMode('accept'); // confirm the ack so the box clears (happy path)

    const { container } = await mountWorkspace();

    await act(async () => {
      typeAndSubmit(container, 'implement the FIFO');
      // Let the ack microtask + state updates flush.
      await Promise.resolve();
      await Promise.resolve();
    });

    // sendPrompt shipped a {type:'prompt'} message carrying the typed text.
    expect(bk.backend.send).toHaveBeenCalled();
    const promptMsg = bk.sent.find((m) => m && m.type === 'prompt');
    expect(promptMsg).toBeTruthy();
    expect(promptMsg.text).toBe('implement the FIFO');
    // Normal mode does NOT route a plain prompt through the orchestrator endpoint.
    const fetchMock = globalThis.fetch as unknown as { mock: { calls: Array<[unknown, ...unknown[]]> } };
    const usedOrchestrator = fetchMock.mock.calls.some(
      ([url]) => String(url) === '/api/pipeline/orchestrator/chat',
    );
    expect(usedOrchestrator).toBe(false);
  });

  it('(c-image) an image-only paste sends a prompt with image attachments', async () => {
    const w = window as AnyWindow;
    w.ATLAS_EXEC_MODE = '';
    w.ACTIVE_SESSION = 'alice/myip/rtl_gen';
    w.ACTIVE_IP = 'myip';
    bk.setAckMode('accept');

    const { container } = await mountWorkspace();
    const textarea = container.querySelector('textarea') as HTMLTextAreaElement;
    const file = new File([new Uint8Array([137, 80, 78, 71])], 'clip.png', {
      type: 'image/png',
    });

    await act(async () => {
      fireEvent.paste(textarea, {
        clipboardData: {
          items: [{
            kind: 'file',
            type: 'image/png',
            getAsFile: () => file,
          }],
          files: [file],
        },
      });
    });

    await waitFor(() => {
      expect(container.textContent || '').toContain('clip.png');
    });

    await act(async () => {
      fireEvent.keyDown(textarea, { key: 'Enter', code: 'Enter' });
      await Promise.resolve();
      await Promise.resolve();
    });

    const promptMsg = bk.sent.find((m) => m && m.type === 'prompt');
    expect(promptMsg).toBeTruthy();
    expect(promptMsg.text).toBe('');
    expect(promptMsg.images).toHaveLength(1);
    expect(promptMsg.images[0].detail).toBe('high');
    expect(promptMsg.images[0].image_url).toMatch(/^data:image\/png;base64,/);
  });

  it('(c2) keeps the composer empty after a fast submit and deferred parent sync expiry', async () => {
    vi.useFakeTimers();
    const w = window as AnyWindow;
    w.ATLAS_EXEC_MODE = '';
    w.ACTIVE_SESSION = 'alice/myip/rtl_gen';
    w.ACTIVE_IP = 'myip';
    bk.setAckMode('accept');

    const { container } = await mountWorkspace();
    const textarea = container.querySelector('textarea') as HTMLTextAreaElement;

    await act(async () => {
      typeAndSubmit(container, 'fast clear prompt');
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(textarea.value).toBe('');

    await act(async () => {
      await vi.advanceTimersByTimeAsync(120);
      await Promise.resolve();
    });

    expect(textarea.value).toBe('');
  });

  it('(c3) clears a stale parent-synced prefix when submitting a longer visible draft', async () => {
    vi.useFakeTimers();
    const w = window as AnyWindow;
    w.ATLAS_EXEC_MODE = '';
    w.ACTIVE_SESSION = 'alice/myip/rtl_gen';
    w.ACTIVE_IP = 'myip';
    bk.setAckMode('accept');

    const { container } = await mountWorkspace();
    const textarea = container.querySelector('textarea') as HTMLTextAreaElement;

    await act(async () => {
      fireEvent.change(textarea, { target: { value: 'synced prefix' } });
      await vi.advanceTimersByTimeAsync(80);
      await Promise.resolve();
    });
    expect(textarea.value).toBe('synced prefix');

    await act(async () => {
      fireEvent.change(textarea, { target: { value: 'synced prefix plus fresh suffix' } });
      fireEvent.keyDown(textarea, { key: 'Enter', code: 'Enter' });
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(bk.backend.send).toHaveBeenCalled();
    const promptMsg = bk.sent.find((m) => m && m.type === 'prompt');
    expect(promptMsg).toBeTruthy();
    expect(promptMsg.text).toBe('synced prefix plus fresh suffix');
    expect(textarea.value).toBe('');

    await act(async () => {
      await vi.advanceTimersByTimeAsync(120);
      await Promise.resolve();
    });
    expect(textarea.value).toBe('');
  });

  it('(d) preserves input if sendPrompt ack explicitly fails', async () => {
    const w = window as AnyWindow;
    w.ATLAS_EXEC_MODE = '';
    w.ACTIVE_SESSION = 'alice/myip/rtl_gen';
    w.ACTIVE_IP = 'myip';
    bk.setAckMode('withhold'); // backend.send emits NO agent_received/accepted

    const { container } = await mountWorkspace();

    const textarea = container.querySelector('textarea') as HTMLTextAreaElement;
    await act(async () => {
      typeAndSubmit(container, 'unacknowledged prompt');
      await Promise.resolve();
    });

    expect(textarea.value).toBe('');

    await act(async () => {
      bk.failLastSendFast();
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(bk.backend.send).toHaveBeenCalled();
    expect(textarea.value).toBe('unacknowledged prompt');
    expect(container.textContent || '').toMatch(/Input not confirmed|kept it in the input box/i);
  });

  it('(e) keeps the composer draft owned by the React input state only', async () => {
    const { container } = await mountWorkspace();
    const textarea = container.querySelector('textarea') as HTMLTextAreaElement;

    await act(async () => {
      fireEvent.change(textarea, { target: { value: 'stable draft' } });
      await Promise.resolve();
    });

    expect(textarea.value).toBe('stable draft');

    await act(async () => {
      window.dispatchEvent(new CustomEvent('atlas-composer-draft-set', {
        detail: { text: 'external mutation' },
      }));
      await Promise.resolve();
    });

    expect(textarea.value).toBe('stable draft');
  });

  it('(f) keeps transport-confirmed delivery latency pending instead of restoring Input not confirmed', async () => {
    vi.useFakeTimers();
    const w = window as AnyWindow;
    w.ATLAS_EXEC_MODE = '';
    w.ACTIVE_SESSION = 'alice/myip/rtl_gen';
    w.ACTIVE_IP = 'myip';
    bk.setAckMode('receivedOnly');

    const { container } = await mountWorkspace();
    const textarea = container.querySelector('textarea') as HTMLTextAreaElement;

    await act(async () => {
      typeAndSubmit(container, 'slow worker prompt');
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(textarea.value).toBe('');

    await act(async () => {
      await vi.advanceTimersByTimeAsync(7100);
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(textarea.value).toBe('');
    expect(container.textContent || '').not.toMatch(/Input not confirmed/i);
    expect(container.textContent || '').toMatch(/전송 중|worker.*busy|pending/i);

    await act(async () => {
      bk.acceptLastSendLate();
      await Promise.resolve();
      await Promise.resolve();
    });

    expect(container.textContent || '').not.toMatch(/전송 중|worker.*busy|pending/i);
  });

  it('(g) routes prompt input to the newly switched workspace session', async () => {
    const w = window as AnyWindow;
    w.ATLAS_EXEC_MODE = '';
    w.ACTIVE_SESSION = 'alice/s1/ip_alpha/rtl-gen';
    w.ACTIVE_IP = 'ip_alpha';
    w.ATLAS_WORKSPACE_SESSION_ID = 's1';
    w.atlasData.sessionFor = (ip: string, wf: string) => {
      const parts = String(w.ACTIVE_SESSION || '').split('/').filter(Boolean);
      const owner = parts[0] || 'alice';
      const workspaceSession = (
        (parts.length >= 4 && parts[0] === owner ? parts[1] : '')
        || String(w.ATLAS_WORKSPACE_SESSION_ID || '').trim()
        || 'default'
      );
      return `${owner}/${workspaceSession}/${String(ip || 'default').trim()}/${String(wf || 'default').trim()}`;
    };
    bk.setAckMode('accept');

    const { container } = await mountWorkspace({
      activeNamespace: 'alice/s1/ip_alpha/rtl-gen',
      activeWorkflow: 'rtl-gen',
    });

    await act(async () => {
      w.ATLAS_WORKSPACE_SESSION_ID = 's2';
      w.ACTIVE_SESSION = 'alice/s2/default/default';
      w.ACTIVE_IP = 'default';
      window.dispatchEvent(new CustomEvent('atlas-session-switched', {
        detail: {
          sessionId: 'alice',
          namespace: 'alice/s2/default/default',
          session: 'alice/s2/default/default',
          ip: 'default',
          workflow: 'default',
        },
      }));
      await Promise.resolve();
      await Promise.resolve();
    });

    await act(async () => {
      typeAndSubmit(container, 'prompt after session switch');
      await Promise.resolve();
      await Promise.resolve();
    });

    const promptMsg = bk.sent.find((m) => m && m.type === 'prompt' && m.text === 'prompt after session switch');
    expect(promptMsg).toBeTruthy();
    expect(promptMsg.session).toBe('alice/s2/default/default');
    expect(promptMsg.ip).toBe('default');
    expect(promptMsg.workflow).toBe('default');
    const stalePrompt = bk.sent.some(
      (m) => m && m.type === 'prompt' && m.text === 'prompt after session switch' && String(m.session || '').startsWith('alice/s1/'),
    );
    expect(stalePrompt).toBe(false);
  });

  it('(h) normal-mode prompt uses selected IP inside a new workspace session', async () => {
    const w = window as AnyWindow;
    w.ATLAS_EXEC_MODE = '';
    w.ATLAS_USER = { username: 'alice' };
    w.ATLAS_WORKSPACE_SESSION_ID = 'v2_session';
    w.ACTIVE_SESSION = 'alice/v2_session/default/default';
    w.ACTIVE_IP = 'dma_v1_good';
    w.atlasData.sessionFor = (ip: string, wf: string) => {
      const workflow = String(wf || 'default').trim() || 'default';
      const ipName = String(ip || 'default').trim() || 'default';
      return `alice/v2_session/${ipName}/${workflow}`;
    };
    bk.setAckMode('accept');

    const { container } = await mountWorkspace({
      activeNamespace: 'alice/v2_session/default/default',
      activeWorkflow: 'default',
    });

    await act(async () => {
      typeAndSubmit(container, 'continue todo work');
      await Promise.resolve();
      await Promise.resolve();
    });

    const promptMsg = bk.sent.find((m) => m && m.type === 'prompt' && m.text === 'continue todo work');
    expect(promptMsg).toBeTruthy();
    expect(promptMsg.session).toBe('alice/v2_session/dma_v1_good/default');
    expect(promptMsg.ip).toBe('dma_v1_good');
    expect(promptMsg.workflow).toBe('default');
  });
});
