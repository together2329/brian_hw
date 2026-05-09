# Session Bridge Architecture

## Overview

The Session Bridge replaces the single-user `_AtlasBridge` with a two-layer design that supports per-session isolation while keeping backward compatibility for legacy single-user deployments.

- **`_SessionBridge`** — per-session state container. Holds the inbox, outbox, interrupt queue, ask_user queues, and the set of WebSocket clients bound to that session.
- **`_MultiUserBridge`** — session manager. Owns a dictionary of `_SessionBridge` instances, tracks which session is active, and routes events between the async WebSocket layer and the correct session.

In single-user mode (`_single_user = True`), `_MultiUserBridge` behaves like the old `_AtlasBridge`: one default session, all clients see all events. In multi-user mode, each client is bound to a specific session, and events only flow to clients attached to that session.

## Class Interface Definitions

### _SessionBridge

A `_SessionBridge` is the narrow waist between one agent thread and the WebSocket clients that belong to one session. It is **not** thread-safe by default; callers must hold the appropriate locks when mutating shared state from multiple threads.

Key responsibilities:
- Queue user prompts (`_inbox`) and mid-loop interrupts (`_interrupts`).
- Broadcast agent events (`_outbox`) to bound clients.
- Track pending `ask_user` questions and their answer queues (`_answer_qs`, `_pending_ask_user`).
- Manage agent lifecycle flags (`agent_running`, `agent_alive`, `_stop_flag`).
- Hold a weak reference set of bound WebSocket clients (`clients`).

### _MultiUserBridge

The `_MultiUserBridge` is the public interface used by the FastAPI app. It:
- Creates and destroys sessions on demand.
- Binds/unbinds WebSocket clients to sessions.
- Switches the active session (which session the legacy single-user agent thread talks to).
- Polls all session outboxes and returns the next event together with its owning session id.

## Session Lifecycle

```
┌─────────┐    bind client     ┌─────────┐    agent starts    ┌─────────┐
│  CREATED│ ─────────────────> │  ACTIVE │ ─────────────────> │ RUNNING │
│         │                    │         │                    │         │
└─────────┘                    └─────────┘                    └─────────┘
      │                              │                              │
      │ delete_session               │ unbind last client           │ agent exits
      │                              │                              │
      ▼                              ▼                              ▼
┌─────────┐                    ┌─────────┐                    ┌─────────┐
│ DELETED │                    │ ARCHIVED│                    │  ACTIVE │
│         │                    │         │                    │         │
└─────────┘                    └─────────┘                    └─────────┘
```

1. **Created** — `_MultiUserBridge._ensure_session(session_id)` instantiates a new `_SessionBridge` and stores it in `_sessions`.
2. **Bind client** — A WebSocket handshake calls `bind_client(client, session_id)`. The client is added to `session.clients`.
3. **Active** — The session exists and has at least one bound client (or is the active session in single-user mode).
4. **Running** — `ensure_agent_alive()` spins up the agent thread. `agent_alive` becomes `True`. `agent_running` becomes `True` while the agent is inside its react loop.
5. **Archive** — When the last client unbinds, the session moves to an archived state. It is kept in `_sessions` but is no longer the active session.
6. **Delete** — `delete_session(session_id)` removes the session from `_sessions`. Any queued prompts are dropped. The agent thread, if running, sees `check_stop()` or the session going away and exits cleanly.

## Event Routing

### Agent → Outbox → Session Clients

```
Agent thread (sync)
       │
       │ emit(msg_type="text_delta", text="...")
       ▼
+-------------+
| _outbox     |  queue.Queue[dict]
+-------------+
       │
       │ async broadcaster task polls next_event()
       ▼
+-------------+
|_MultiUser   |
|Bridge       |
+-------------+
       │
       │ (msg, session_id)
       ▼
+-------------+
| _SessionBridge for session_id
| .clients    |  WeakSet[WebSocket]
+-------------+
       │
       ├───> WS client A  (session scope)
       ├───> WS client B  (session scope)
       └───> WS client C  (different session, NOT reached)
```

The agent calls `session.emit(...)` which puts a dict into that session's `_outbox`. The async broadcaster loop calls `multi_bridge.next_event(timeout)`, which polls every session's `_outbox`. When a message is found, the loop iterates over `session.clients` and sends the JSON to each bound WebSocket.

### Client → Session → Agent

```
WS client A
       │
       │ {type:"prompt", text:"hello"}
       ▼
+-------------+
|_MultiUser   |
|Bridge       |  bind_client(client, "sess-1")
+-------------+
       │
       ▼
+-------------+
|_SessionBridge "sess-1"
| submit_prompt|
+-------------+
       │
       ├───> _inbox  (if agent not running, or slash command)
       └───> _interrupts (if agent running and free-form text)
```

When a WebSocket message arrives, the handler looks up the client's session via `get_client_session(client)`. It then calls `session.submit_prompt(text)`, which routes the text to `_inbox` or `_interrupts` depending on whether the agent is currently running.

## Active Session Switching

In multi-user mode, only one session is "active" at a time. The active session is the one that the legacy single-user agent thread reads from and writes to.

```
+-----------+     activate_session("sess-B")     +-----------+
|  sess-A   │ <────────────────────────────────> │  sess-B   │
│ (active)  │                                    │ (active)  │
+-----------+                                    +-----------+
      │                                                │
      │ agent thread reads get_input() from here       │
      ▼                                                ▼
   _inbox A                                         _inbox B
```

`activate_session(session_id)` acquires `_active_lock`, updates `_active_session_id`, and returns. The agent thread's next call to `multi_bridge.get_input()` will block on the new session's `_inbox`.

Switching is non-preemptive. The current agent turn runs to completion (or until `check_stop()` returns True). The switch takes effect at the next top-level turn boundary when the agent calls `get_input()` again.

## Backward Compatibility

When `_single_user = True`, `_MultiUserBridge` creates a single default session on first use. All clients are bound to this session. Legacy code that calls `bridge.get_input()`, `bridge.emit(...)`, etc. continues to work because `_MultiUserBridge` forwards those calls to the active (and only) session.

## ASCII Diagram: Single-User Mode

```
┌─────────────────────────────────────────────────────────────┐
│                     Single-User Mode                        │
│                    (_single_user = True)                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   WS clients A, B, C                                        │
│        │                                                    │
│        │ all connected                                       │
│        ▼                                                    │
│   ┌─────────────┐                                           │
│   │ _MultiUser  │  one default session                       │
│   │   Bridge    │  ┌──────────────────┐                     │
│   │             │──>│ _SessionBridge    │                     │
│   │             │  │  (default)         │                     │
│   └─────────────┘  │                    │                     │
│        │           │  _inbox            │                     │
│        │           │  _interrupts       │                     │
│        │           │  _outbox  ────────┼──> broadcast to A,B,C│
│        │           │  clients = {A,B,C} │                     │
│        │           └──────────────────┘                     │
│        │                                                    │
│        └────────────────────────────────────────────────────│
│                          agent thread reads/writes here     │
└─────────────────────────────────────────────────────────────┘
```

## ASCII Diagram: Multi-User Mode

```
┌─────────────────────────────────────────────────────────────┐
│                      Multi-User Mode                        │
│                   (_single_user = False)                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────────────────────────────────────────────────┐   │
│   │              _MultiUserBridge                      │   │
│   │                                                     │   │
│   │   _sessions = {                                     │   │
│   │     "sess-1": _SessionBridge,  <── active          │   │
│   │     "sess-2": _SessionBridge                       │   │
│   │   }                                                 │   │
│   │   _active_session_id = "sess-1"                     │   │
│   └─────────────────────────────────────────────────────┘   │
│            │                    │                           │
│      ┌─────┘                    └─────┐                     │
│      ▼                                ▼                     │
│  ┌─────────────┐              ┌─────────────┐              │
│  │ sess-1      │              │ sess-2      │              │
│  │             │              │             │              │
│  │ _inbox      │              │ _inbox      │              │
│  │ _outbox ────┼──> WS A,B    │ _outbox ────┼──> WS C,D   │
│  │ clients={A,B}│             │ clients={C,D}│             │
│  └─────────────┘              └─────────────┘              │
│        ▲                            │                      │
│        │                            │                      │
│        └──── agent thread ──────────┘                      │
│              (reads from active session only)              │
│                                                             │
│   activate_session("sess-2") switches active pointer        │
│   to sess-2. Next get_input() reads from sess-2._inbox.   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Design Invariants

1. **One agent thread per active session.** The agent thread is started by `ensure_agent_alive()` on the active session. If the active session switches, the existing agent thread either exits (via stop flag) or completes its current turn and then the new session's starter is invoked.
2. **Clients only receive events from their bound session.** The `clients` WeakSet on each `_SessionBridge` ensures that `emit()` is scoped.
3. **Prompt deduplication is per-session.** `_seen_msg_ids` lives inside `_SessionBridge`, so a retry on one session does not suppress the same message id on another session.
4. **ask_user questions are per-session.** A `flow_id` collision across sessions is impossible because each session owns its own `_answer_qs` and `_pending_ask_user` dicts.
