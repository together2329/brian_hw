/* backend.js — Atlas frontend ↔ Python backend adapter (live-only)
 *
 * Exposes window.backend:
 *   backend.mode                     always 'live'
 *   backend.subscribe(type, cb)      → unsubscribe()
 *   backend.send(obj)                publish a message to backend
 *   backend.connect() / disconnect()
 *
 * Opens a WebSocket to /ws/agent (relative to current host) and forwards
 * messages both ways. The mock fallback was removed — Atlas always talks
 * to the live agent via atlas_ui.py.
 */
(function () {
  'use strict';
  const mode = 'live';

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

  // ── public surface ─────────────────────────────────────────
  const api = {
    mode,
    subscribe,
    send: liveSend,
    connect: liveConnect,
    disconnect: liveDisconnect,
    // Test/debug hook — lets UI code synthesize events in tests.
    _emit: emit,
  };

  liveConnect();

  window.backend = api;
  console.info('[atlas] backend ready · mode=live');
})();
