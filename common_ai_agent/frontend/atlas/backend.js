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
  const lastPayload = Object.create(null);
  const replayablePayloads = new Set(['hello', 'connection']);
  function subscribe(type, cb) {
    (handlers[type] = handlers[type] || new Set()).add(cb);
    if (replayablePayloads.has(type) && Object.prototype.hasOwnProperty.call(lastPayload, type)) {
      setTimeout(() => {
        try { cb(lastPayload[type]); }
        catch (e) { console.error('[backend]', type, e); }
      }, 0);
    }
    return () => handlers[type] && handlers[type].delete(cb);
  }
  function emit(type, payload) {
    lastPayload[type] = payload;
    const set = handlers[type];
    if (set) set.forEach((cb) => { try { cb(payload); } catch (e) { console.error('[backend]', type, e); } });
    const all = handlers['*'];
    if (all) all.forEach((cb) => { try { cb({ type, ...payload }); } catch (e) { console.error('[backend] *', e); } });
  }

  // ── live (WebSocket) implementation ────────────────────────
  let ws = null;
  let reconnectTimer = null;
  let liveQueue = [];
  let connectionState = 'connecting';
  // Outbound prompts awaiting an `agent_received` ack from the backend.
  // Map<msg_id, { msg, retries, timer }>. If the ack doesn't arrive
  // within ACK_TIMEOUT_MS we re-send the same payload once. The backend
  // dedupes by msg_id, so a duplicate that races the first delivery is
  // safe — only the first copy actually runs.
  const pendingAcks = new Map();
  const ACK_TIMEOUT_MS = 3000;
  const MAX_RETRIES = 1;

  function _rawSend(msg) {
    if (ws && ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(msg));
    else liveQueue.push(msg);
  }
  function _scheduleAckTimer(msg_id) {
    const entry = pendingAcks.get(msg_id);
    if (!entry) return;
    clearTimeout(entry.timer);
    entry.timer = setTimeout(() => {
      const cur = pendingAcks.get(msg_id);
      if (!cur) return;
      if (cur.retries >= MAX_RETRIES) {
        pendingAcks.delete(msg_id);
        return;
      }
      cur.retries += 1;
      _rawSend(cur.msg);
      _scheduleAckTimer(msg_id);
    }, ACK_TIMEOUT_MS);
  }

  function liveConnect(sessionId) {
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) return;
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const url   = sessionId
        ? `${proto}//${location.host}/ws/agent?session_id=${encodeURIComponent(sessionId)}`
        : `${proto}//${location.host}/ws/agent`;
    try {
      ws = new WebSocket(url);
    } catch (e) {
      console.warn('[backend] WS construct failed', e);
      scheduleReconnect();
      return;
    }
    ws.onopen = () => {
      connectionState = 'open';
      emit('connection', { state: 'open' });
      while (liveQueue.length) ws.send(JSON.stringify(liveQueue.shift()));
    };
    ws.onmessage = (ev) => {
      let msg;
      try { msg = JSON.parse(ev.data); } catch (_) { return; }
      if (!msg || !msg.type) return;
      // Backend ack — clear the pending retransmit timer.
      if (msg.type === 'agent_received' && msg.msg_id && pendingAcks.has(msg.msg_id)) {
        const entry = pendingAcks.get(msg.msg_id);
        clearTimeout(entry.timer);
        pendingAcks.delete(msg.msg_id);
      }
      emit(msg.type, msg);
    };
    ws.onclose = () => {
      connectionState = 'closed';
      emit('connection', { state: 'closed' });
      scheduleReconnect();
    };
    ws.onerror = (e) => {
      connectionState = 'error';
      emit('connection', { state: 'error', error: String(e) });
    };
  }
  function scheduleReconnect() {
    clearTimeout(reconnectTimer);
    reconnectTimer = setTimeout(liveConnect, 1500);
  }
  function liveSend(msg) {
    // Track prompts (or any send carrying msg_id) for ack-based retry.
    if (msg && msg.type === 'prompt' && msg.msg_id) {
      pendingAcks.set(msg.msg_id, { msg, retries: 0, timer: null });
      _scheduleAckTimer(msg.msg_id);
    }
    _rawSend(msg);
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
    getConnectionState: () => connectionState,
    // Test/debug hook — lets UI code synthesize events in tests.
    _emit: emit,
  };

  liveConnect();

  window.backend = api;
  console.info('[atlas] backend ready · mode=live');
})();
