/* backend.js — Atlas frontend ↔ Python backend adapter (live-only)
 *
 * Exposes window.backend:
 *   backend.mode                     always 'live'
 *   backend.subscribe(type, cb)      → unsubscribe()
 *   backend.send(obj)                publish a message to backend
 *   backend.connect() / disconnect() / switchSession()
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
  const replayablePayloads = new Set(['hello', 'connection', 'agent_state']);
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
  let currentSessionId = '';
  let wsEpoch = 0;
  // Outbound prompts awaiting an `agent_received` ack from the backend.
  // Map<msg_id, { msg, retries, timer }>. If the ack doesn't arrive
  // within ACK_TIMEOUT_MS we re-send the same payload once. The backend
  // dedupes by msg_id, so a duplicate that races the first delivery is
  // safe — only the first copy actually runs.
  const pendingAcks = new Map();
  const ACK_TIMEOUT_MS = 3000;
  const MAX_RETRIES = 1;

  function clearPendingAcks() {
    pendingAcks.forEach((entry) => {
      try { clearTimeout(entry.timer); } catch (_) {}
    });
    pendingAcks.clear();
  }
  function isAuthClose(ev) {
    const code = ev && Number(ev.code);
    const reason = String((ev && ev.reason) || '').toLowerCase();
    return code === 1008 && (reason.includes('unauth') || reason.includes('forbidden'));
  }
  function emitAuthRequired(ev) {
    const detail = {
      state: 'auth_required',
      code: ev && ev.code,
      reason: (ev && ev.reason) || 'login required',
    };
    connectionState = 'auth_required';
    liveQueue = [];
    clearPendingAcks();
    emit('connection', detail);
    try {
      window.dispatchEvent(new CustomEvent('atlas:auth_required', { detail }));
    } catch (_) {}
  }

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
    const targetSessionId = String(sessionId || currentSessionId || '');
    const sessionChanged = targetSessionId !== currentSessionId;
    if (
      sessionChanged &&
      ws &&
      (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING || ws.readyState === WebSocket.CLOSING)
    ) {
      try { ws.onclose = null; ws.onerror = null; ws.onmessage = null; ws.onopen = null; ws.close(); } catch (_) {}
      ws = null;
    }
    if (sessionChanged) {
      clearPendingAcks();
      liveQueue = [];
    }
    currentSessionId = targetSessionId;
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
      if (ws.readyState === WebSocket.OPEN && connectionState !== 'open') {
        connectionState = 'open';
        emit('connection', { state: 'open' });
      }
      return;
    }
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const url   = targetSessionId
        ? `${proto}//${location.host}/ws/agent?session_id=${encodeURIComponent(targetSessionId)}`
        : `${proto}//${location.host}/ws/agent`;
    try {
      ws = new WebSocket(url);
    } catch (e) {
      console.warn('[backend] WS construct failed', e);
      scheduleReconnect();
      return;
    }
    const socket = ws;
    const epoch = ++wsEpoch;
    ws.onopen = () => {
      if (socket !== ws || epoch !== wsEpoch) return;
      connectionState = 'open';
      _reconnectAttempts = 0;  // reset backoff on a successful open
      emit('connection', { state: 'open' });
      while (liveQueue.length && socket === ws && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify(liveQueue.shift()));
      }
    };
    ws.onmessage = (ev) => {
      if (socket !== ws || epoch !== wsEpoch) return;
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
    ws.onclose = (ev) => {
      if (socket !== ws || epoch !== wsEpoch) return;
      if (isAuthClose(ev)) {
        ws = null;
        emitAuthRequired(ev);
        return;
      }
      connectionState = 'closed';
      ws = null;
      emit('connection', { state: 'closed' });
      scheduleReconnect();
    };
    ws.onerror = (e) => {
      if (socket !== ws || epoch !== wsEpoch) return;
      connectionState = 'error';
      emit('connection', { state: 'error', error: String(e) });
    };
  }
  // Exponential backoff for reconnect — fast first retry so a backend
  // restart picks up immediately, capped at 5 s so a truly down server
  // doesn't burn CPU on tight retries. Resets to the floor whenever the
  // socket reaches `open`.
  let _reconnectAttempts = 0;
  const _RECONNECT_MIN_MS = 250;
  const _RECONNECT_MAX_MS = 5000;
  function scheduleReconnect() {
    clearTimeout(reconnectTimer);
    const delay = Math.min(
      _RECONNECT_MAX_MS,
      _RECONNECT_MIN_MS * Math.pow(2, _reconnectAttempts),
    );
    _reconnectAttempts += 1;
    reconnectTimer = setTimeout(() => liveConnect(currentSessionId), delay);
  }
  function liveSend(msg) {
    // Track prompts (or any send carrying msg_id) for ack-based retry.
    if (msg && msg.type === 'prompt' && msg.msg_id) {
      pendingAcks.set(msg.msg_id, { msg, retries: 0, timer: null });
      _scheduleAckTimer(msg.msg_id);
    }
    _rawSend(msg);
  }
  function liveSwitchSession(sessionId) {
    const targetSessionId = String(sessionId || '').trim();
    if (!targetSessionId) return;
    if (targetSessionId !== currentSessionId) {
      liveConnect(targetSessionId);
      return;
    }
    currentSessionId = targetSessionId;
    if (!ws || ws.readyState === WebSocket.CLOSED || ws.readyState === WebSocket.CLOSING) {
      liveConnect(targetSessionId);
      return;
    }
    _rawSend({ type: 'session_switch', session_id: targetSessionId });
  }
  function liveDisconnect() {
    clearTimeout(reconnectTimer);
    wsEpoch += 1;
    liveQueue = [];
    clearPendingAcks();
    const socket = ws;
    ws = null;
    if (socket) {
      try {
        socket.onclose = null;
        socket.onerror = null;
        socket.onmessage = null;
        socket.onopen = null;
        socket.close();
      } catch (_) {}
    }
    connectionState = 'closed';
    emit('connection', { state: 'closed' });
  }

  // ── public surface ─────────────────────────────────────────
  const api = {
    mode,
    subscribe,
    send: liveSend,
    connect: (sessionId) => liveConnect(sessionId || ''),
    switchSession: liveSwitchSession,
    disconnect: liveDisconnect,
    getConnectionState: () => connectionState,
    // Test/debug hook — lets UI code synthesize events in tests.
    _emit: emit,
  };

  // Do not bind the initial browser socket to URL/localStorage session
  // hints. In multi-user mode those hints can belong to a previous login;
  // the backend should default the socket to the authenticated cookie user
  // instead. App.jsx may explicitly reconnect after /api/users/me resolves.
  liveConnect();

  window.backend = api;
  console.info('[atlas] backend ready · mode=live');
})();
