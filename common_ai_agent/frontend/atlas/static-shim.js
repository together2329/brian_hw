/* static-shim.js — make ATLAS render without a live backend.
 *
 * Loaded BEFORE backend.js. Intercepts every fetch() and WebSocket the
 * frontend uses, returns canned-but-shaped responses, and emits a
 * synthetic `hello` so the auth gate + boot handshake both complete.
 *
 * Keeps the real app code untouched — pull this script out (or load
 * index.html directly) to talk to the actual atlas_ui.py server.
 */
(function () {
  'use strict';

  const NOW = Date.now() / 1000;
  const USER = { username: 'brian', email: 'brian@local', is_admin: true };

  // ── fetch stub ───────────────────────────────────────────────
  const realFetch = window.fetch.bind(window);

  function jsonResp(body, status) {
    return new Response(JSON.stringify(body), {
      status: status || 200,
      headers: { 'content-type': 'application/json' },
    });
  }

  const ROUTES = [
    [/^\/api\/users\/me/, () => ({ user: USER })],
    [/^\/api\/version/,   () => ({ mtime: NOW, started: NOW })],
    [/^\/healthz/,        () => ({
      ok: true,
      frontend: 'atlas',
      model: 'mock-haiku-4.5',
      iterMax: 200,
      workspace: 'ssot-gen',
      active: 'brian/default',
      user_session: 'brian',
      session_id: 'brian',
      cwd: '/projects/atlas',
      project_root: '/projects/atlas',
      ip_id: '',
      chat_feed_summary: '',
    })],
    [/^\/api\/llm\/ping/, () => ({ ok: true, provider: 'mock', model: 'mock-haiku' })],
    [/^\/api\/session\/list/, () => ({
      sessions: [
        { session: 'brian/default',         updated: NOW, todos: 0 },
        { session: 'brian/axi_dma/rtl-gen', updated: NOW - 3600, todos: 4 },
        { session: 'brian/gpio_pad/ssot-gen', updated: NOW - 86400, todos: 2 },
      ],
    })],
    [/^\/api\/ip\/list/, () => ({
      items: [
        { name: 'axi_dma',  has_yaml: true, has_rtl: true,  has_tb: true,  has_sim: false },
        { name: 'gpio_pad', has_yaml: true, has_rtl: true,  has_tb: false, has_sim: false },
        { name: 'pl330',    has_yaml: true, has_rtl: false, has_tb: false, has_sim: false },
      ],
    })],
    [/^\/api\/session\/state/, () => ({
      conversation: [], todos: [], cost: { input: 0, cached: 0, output: 0 }, job: null,
    })],
    [/^\/api\/session\/activate/, () => ({ ok: true })],
    [/^\/api\/control\//,         () => ({ ok: true })],
    [/^\/api\/commands/,          () => ({
      commands: [
        { cmd: '/help',    alias: 'h',  hint: 'show available commands' },
        { cmd: '/clear',   alias: 'cl', hint: 'reset conversation' },
        { cmd: '/compact', alias: 'co', hint: 'compress history' },
        { cmd: '/todo',    alias: 't',  hint: 'show / manage todos' },
        { cmd: '/wf',      alias: 'w',  hint: 'switch workflow: /wf rtl-gen' },
        { cmd: '/scope',   alias: 'sc', hint: 'confine agent to a directory' },
      ],
    })],
    [/^\/api\/workspaces/, () => ({
      workspaces: [
        'default','ssot-gen','fl-model-gen','rtl-gen','tb-gen','sim_debug',
        'lint','coverage','syn','sta','pnr','architect',
      ],
    })],
    [/^\/api\/files/,   () => ({ tree: [] })],
    [/^\/api\/todos/,   () => ({ todos: [] })],
    [/^\/api\/ssot/,    () => ({ files: [] })],
    [/^\/api\/git\//,   () => ({ commits: [] })],
    [/^\/api\/soc/,     () => ({ blocks: [], links: [] })],
  ];

  window.fetch = function (input, init) {
    const url = typeof input === 'string' ? input : (input && input.url) || '';
    // Only intercept same-origin /api/* and /healthz, /ws/* (won't fetch ws).
    let path;
    try {
      path = new URL(url, location.href).pathname;
    } catch (_) {
      return realFetch(input, init);
    }
    for (const [pat, mk] of ROUTES) {
      if (pat.test(path)) {
        const body = mk();
        return Promise.resolve(jsonResp(body));
      }
    }
    if (path.startsWith('/api/') || path === '/healthz') {
      // Unknown /api/* path — return empty object so .then(j => j.something) is safe-ish.
      return Promise.resolve(jsonResp({ ok: true }));
    }
    return realFetch(input, init);
  };

  // ── WebSocket stub ───────────────────────────────────────────
  const RealWS = window.WebSocket;
  class FakeWS {
    constructor(url) {
      this.url = url;
      this.readyState = 0;
      this.onopen = null;
      this.onmessage = null;
      this.onclose = null;
      this.onerror = null;
      // Open + greet on the next tick so subscribers wire up first.
      setTimeout(() => {
        this.readyState = 1;
        try { this.onopen && this.onopen({ type: 'open' }); } catch (_) {}
        const emit = (obj) => {
          try { this.onmessage && this.onmessage({ data: JSON.stringify(obj) }); } catch (_) {}
        };
        emit({ type: 'hello',       frontend: 'atlas', running: false });
        emit({ type: 'agent_state', running: false });
        emit({ type: 'context',     used: 0, max: 200000 });
      }, 30);
    }
    send(_msg) { /* swallow */ }
    close() {
      this.readyState = 3;
      try { this.onclose && this.onclose({ type: 'close', code: 1000 }); } catch (_) {}
    }
    addEventListener(type, cb) { this['on' + type] = cb; }
    removeEventListener(type)  { this['on' + type] = null; }
  }
  FakeWS.OPEN = 1; FakeWS.CONNECTING = 0; FakeWS.CLOSING = 2; FakeWS.CLOSED = 3;
  window.WebSocket = FakeWS;

  // Restore the real WS if the user ever wants to debug live.
  window.__realWebSocket = RealWS;

  console.info('[atlas-shim] static preview shim active — backend calls are mocked');
})();
