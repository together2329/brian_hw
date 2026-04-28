/* backend.js — Atlas frontend ↔ Python backend adapter
 *
 * Exposes window.backend with a uniform API:
 *   backend.mode                     'mock' | 'live'
 *   backend.subscribe(type, cb)      → unsubscribe()
 *   backend.send(obj)                publish a message to backend
 *   backend.connect() / disconnect()
 *
 * In 'mock' mode (default for static-file dev), all sends are echoed locally
 * with synthetic responses so the UI is fully interactive without a server.
 *
 * In 'live' mode, it opens a WebSocket to /ws/agent (relative to current host)
 * and forwards messages both ways. Switch via:
 *   - URL flag:        ?backend=live
 *   - localStorage:    localStorage.atlasBackend = 'live'
 *   - meta tag:        <meta name="atlas-backend" content="live">
 *   - or DOM script tag: data-backend="live"
 */
(function () {
  'use strict';

  // ── pick mode ──────────────────────────────────────────────
  const params = new URLSearchParams(location.search);
  const meta   = document.querySelector('meta[name="atlas-backend"]');
  const ls     = (() => { try { return localStorage.getItem('atlasBackend'); } catch (_) { return null; } })();
  const mode   = params.get('backend') || ls || (meta && meta.content) || 'mock';

  // ── pubsub primitive ───────────────────────────────────────
  const handlers = Object.create(null);
  function subscribe(type, cb) {
    (handlers[type] = handlers[type] || new Set()).add(cb);
    return () => handlers[type] && handlers[type].delete(cb);
  }
  function emit(type, payload) {
    const set = handlers[type];
    if (set) set.forEach((cb) => { try { cb(payload); } catch (e) { console.error('[backend]', type, e); } });
    const all = handlers['*'];
    if (all) all.forEach((cb) => { try { cb({ type, ...payload }); } catch (e) { console.error('[backend] *', e); } });
  }

  // ── live (WebSocket) implementation ────────────────────────
  let ws = null;
  let reconnectTimer = null;
  let liveQueue = [];

  function liveConnect() {
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) return;
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const url   = `${proto}//${location.host}/ws/agent`;
    try {
      ws = new WebSocket(url);
    } catch (e) {
      console.warn('[backend] WS construct failed', e);
      scheduleReconnect();
      return;
    }
    ws.onopen = () => {
      emit('connection', { state: 'open' });
      while (liveQueue.length) ws.send(JSON.stringify(liveQueue.shift()));
    };
    ws.onmessage = (ev) => {
      let msg;
      try { msg = JSON.parse(ev.data); } catch (_) { return; }
      if (msg && msg.type) emit(msg.type, msg);
    };
    ws.onclose = () => {
      emit('connection', { state: 'closed' });
      scheduleReconnect();
    };
    ws.onerror = (e) => emit('connection', { state: 'error', error: String(e) });
  }
  function scheduleReconnect() {
    clearTimeout(reconnectTimer);
    reconnectTimer = setTimeout(liveConnect, 1500);
  }
  function liveSend(msg) {
    if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(msg));
    else liveQueue.push(msg);
  }
  function liveDisconnect() {
    clearTimeout(reconnectTimer);
    if (ws) { try { ws.close(); } catch (_) {} ws = null; }
  }

  // ── mock implementation ────────────────────────────────────
  // Replays simple synthetic streams so the UI feels alive without a server.
  const mockReplies = [
    "Looking at §5 FSM — bit_cnt is 4 bits, transfer length is 8 bits, ",
    "so wraparound at bit 7→0 won't pull in stale state. ",
    "No hazards I'd flag. Want me to write a covergroup for the IDLE→LOAD→SHIFT→COMPLETE arcs?",
  ];
  function mockSend(msg) {
    // Echo prompts as token stream
    if (msg.type === 'prompt' || msg.type === 'send') {
      let i = 0;
      const tick = () => {
        if (i >= mockReplies.length) {
          emit('done', { ok: true });
          return;
        }
        emit('token', { text: mockReplies[i++] });
        setTimeout(tick, 280);
      };
      setTimeout(tick, 120);
      return;
    }
    // Stage progress nudges
    if (msg.type === 'run_stage') {
      emit('stage', { stage: msg.stage, state: 'active' });
      setTimeout(() => emit('stage', { stage: msg.stage, state: 'done' }), 1200);
      return;
    }
    // Tool calls
    if (msg.type === 'tool_call') {
      emit('tool_event', { tool: msg.name, phase: 'start' });
      setTimeout(() => emit('tool_event', { tool: msg.name, phase: 'done', result: 'ok' }), 600);
      return;
    }
  }

  // ── public surface ─────────────────────────────────────────
  const api = {
    mode,
    subscribe,
    send: mode === 'live' ? liveSend : mockSend,
    connect:    mode === 'live' ? liveConnect    : () => {},
    disconnect: mode === 'live' ? liveDisconnect : () => {},
    setMode(next) {
      try { localStorage.setItem('atlasBackend', next); } catch (_) {}
      // Reload so the right transport gets wired cleanly
      location.reload();
    },
    // Test/debug: lets UI code synthesize events in mock dev
    _emit: emit,
  };

  if (mode === 'live') liveConnect();

  window.backend = api;
  console.info(`[atlas] backend ready · mode=${mode}`);
})();
