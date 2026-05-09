# Session Bridge Interface Specification

## _SessionBridge

Per-session state container. Not thread-safe by default — callers must hold locks when mutating from multiple threads.

### State Fields

| Field | Type | Description |
|-------|------|-------------|
| `session_id` | `str` | Canonical session identifier |
| `_inbox` | `queue.Queue[str]` | User prompts waiting for agent |
| `_interrupts` | `queue.Queue[str]` | Mid-loop conversational interrupts |
| `_outbox` | `queue.Queue[dict]` | Agent events to broadcast |
| `_answer_qs` | `dict[str, queue.Queue]` | `flow_id → Queue` for ask_user answers |
| `_pending_ask_user` | `dict[str, dict]` | `flow_id → event dict` for pending questions |
| `agent_running` | `bool` | True while agent is inside react_loop |
| `agent_alive` | `bool` | True while agent thread exists |
| `_agent_starter` | `Callable[[], None] \| None` | Spins up the agent thread |
| `_stop_flag` | `bool` | Esc/stop request flag |
| `clients` | `weakref.WeakSet[Any]` | WebSocket clients bound to this session |

### Methods

#### Agent-side (sync, called by agent thread)

```python
def get_input(self, prompt: str = "") -> str
```
> Block until a prompt arrives in `_inbox`. Return the prompt text.

```python
def poll_interrupt(self) -> str | None
```
> Non-blocking check of `_interrupts`. Return text or None.

```python
def emit(self, msg_type: str, **payload: Any) -> None
```
> Build `{"type": msg_type, **payload}`, optionally tag with session_id, put into `_outbox`.

```python
def pending_ask_user_events(self) -> list[dict[str, Any]]
```
> Return snapshot of all pending ask_user events for rehydration on new client connect.

#### ask_user lifecycle

```python
def open_question(self, flow_id: str) -> queue.Queue[Any]
```
> Create and store a new answer queue for `flow_id`. Return the queue.

```python
def close_question(self, flow_id: str) -> None
```
> Remove the answer queue for `flow_id` and emit `ask_user_closed`.

```python
def wait_answer(self, flow_id: str, timeout: float | None = None) -> Any | None
```
> Block on the answer queue for `flow_id`. Return answer or None on timeout.

#### WS-side (called by async WebSocket handler)

```python
def set_agent_starter(self, fn: Callable[[], None]) -> None
```
> Store the callable that starts the agent thread.

```python
def ensure_agent_alive(self) -> None
```
> If not `agent_alive`, call `_agent_starter()` and set flags.

```python
def submit_prompt(self, text: str) -> None
```
Reset `_stop_flag`, ensure the agent is alive, then route `text`:
- Slash-prefixed text (`/wf`, `/clear`, etc.) always goes to `_inbox`.
- Non-slash text goes to `_interrupts` if `agent_running` else `_inbox`.

```python
def msg_id_seen(self, msg_id: str) -> bool
```
Idempotency check for WebSocket-delivered prompts. Returns `True` if `msg_id` was already seen in this session's LRU. If new, inserts it and evicts the oldest entry when the limit is exceeded.

```python
def queue_prompt(self, text: str) -> None
```
Force a prompt into `_inbox` (never `_interrupts`) and ensure the agent is alive. Used for slash/workflow commands that must run at the next turn boundary.

```python
def submit_answer(self, flow_id: str, payload: dict[str, Any]) -> bool
```
Put `payload` into the answer queue for `flow_id`. Return False if queue not found.

```python
def request_stop(self) -> None
```
Set `_stop_flag = True`, drain slash commands from `_inbox`, re-queue non-slash entries.

```python
def check_stop(self) -> bool
```
Read-and-clear `_stop_flag`. Return True if it was set.

## _MultiUserBridge

Public interface used by the FastAPI app. Thread-safe via internal locks.

### State Fields

| Field | Type | Description |
|-------|------|-------------|
| `_sessions` | `dict[str, _SessionBridge]` | All known sessions |
| `_sessions_lock` | `threading.RLock` | Protects `_sessions` mutations |
| `_active_session_id` | `str` | Which session the agent thread reads from |
| `_active_lock` | `threading.RLock` | Protects `_active_session_id` |
| `_single_user` | `bool` | Backward-compat mode flag |

### Methods

#### Session lifecycle

```python
def _ensure_session(self, session_id: str) -> _SessionBridge
```
> Get existing session or create new one. Thread-safe.

```python
def get_session(self, session_id: str) -> _SessionBridge
```
> Get existing session or raise KeyError. Thread-safe.

```python
def list_sessions(self) -> list[_SessionBridge]
```
> Return all active sessions. Thread-safe.

```python
def delete_session(self, session_id: str) -> bool
```
> Remove session, drain queues, clear state. Return False for "default" or missing. Thread-safe.

```python
def activate_session(self, session_id: str) -> None
```
> Switch `_active_session_id`. Next `get_input()` blocks on new session. Thread-safe.

#### Client management

```python
def bind_client(self, client: Any, session_id: str | None = None) -> str
```
> Add client to session's `clients` WeakSet. Return resolved session_id. Thread-safe.

```python
def unbind_client(self, client: Any) -> None
```
> Remove client from whichever session owns it. Thread-safe.

```python
def get_client_session(self, client: Any) -> _SessionBridge | None
```
> Find which session a client belongs to. Thread-safe.

#### Legacy-compatible agent-side methods

These methods delegate to the **active** session for backward compatibility with `main.py`:

```python
def get_input(self, prompt: str = "") -> str
def poll_interrupt(self) -> str | None
def emit(self, msg_type: str, **payload: Any) -> None
def pending_ask_user_events(self) -> list[dict[str, Any]]
def open_question(self, flow_id: str) -> queue.Queue[Any]
def close_question(self, flow_id: str) -> None
def wait_answer(self, flow_id: str, timeout: float | None = None) -> Any | None
def set_agent_starter(self, fn: Callable[[], None]) -> None
def ensure_agent_alive(self) -> None
def submit_prompt(self, text: str) -> None
def submit_answer(self, flow_id: str, payload: dict[str, Any]) -> bool
def request_stop(self) -> None
def check_stop(self) -> bool
```

#### Async broadcaster method

```python
async def next_event(self, timeout: float = 0.25) -> tuple[dict[str, Any] | None, str | None]
```
> Poll ALL session outboxes. Return `(msg, session_id)` or `(None, None)` on timeout. This is the core method that enables session-scoped broadcast.

#### Properties (backward compatibility)

```python
@property
def agent_running(self) -> bool
```
> In single-user: return default session's flag. In multi-user: return True if ANY session has running agent.

```python
@property
def agent_alive(self) -> bool
```
> Same pattern as `agent_running`.

## Event Types

Events emitted via `emit()` and placed into `_outbox`:

| Type | Payload Fields | Description |
|------|---------------|-------------|
| `hello` | `frontend`, `running`, `center_layout`, `chat_feed_summary` | Greeting on WS connect |
| `token` | `text`, `cls` | Streaming LLM token |
| `reasoning` | `text`, `blank` | Model reasoning/thought |
| `flush` | — | End of streaming batch |
| `tool` | `text` | Tool call display |
| `tool_result` | `text`, `tool`, `truncated` | Tool output |
| `todo_line` | `text`, `todo_state`, `todos` | Todo update |
| `context` | `used`, `max` | Context window usage |
| `cost` | `input`, `cached`, `output`, `cost_usd_delta`, `pricing`, `model` | Token cost |
| `agent_state` | `running` | Agent started/stopped |
| `slash_output` | `text` | Slash command response |
| `mode_change` | `mode` | Plan/normal mode switch |
| `ask_user` | `flow_id`, `session`, `ip`, `options`, `question` | User question card |
| `ask_user_answered` | `flow_id` | Answer received |
| `ask_user_closed` | `flow_id` | Question cancelled |
| `error` | `message` | Error message |
| `done` | — | Agent turn complete |
| `commands_changed` | — | Slash registry updated |
| `peer_joined` | `connection_id` | Another client joined same session |
| `peer_left` | `connection_id` | A client left the session |

## State Machine: Session Status

```
                    create_session()
    ┌─────────────────────────────────────┐
    │                                     ▼
┌─────────┐    bind_client()     ┌─────────────┐    ensure_agent_alive()
│  NONE   │ ───────────────────> │   ACTIVE    │ ─────────────────────────>
│         │                      │             │
└─────────┘                      └─────────────┘
                                        │
           unbind last client           │
           (no timeout)                 │
               │                        │
               ▼                        │
         ┌─────────────┐               │
         │  ARCHIVED   │ <─────────────┘
         │             │      archive_session()
         └─────────────┘
                │
                │ delete_session()
                ▼
           ┌─────────┐
           │ DELETED │
           │         │
           └─────────┘
```

## Thread Safety Guarantees

| Operation | Guarantee |
|-----------|-----------|
| `_ensure_session` / `get_session` / `list_sessions` / `delete_session` | Thread-safe via `_sessions_lock` |
| `activate_session` | Thread-safe via `_active_lock` |
| `bind_client` / `unbind_client` / `get_client_session` | Thread-safe via `_sessions_lock` |
| `next_event` | Thread-safe (read-only on `_sessions`) |
| `_SessionBridge` internal methods | NOT thread-safe; `_MultiUserBridge` callers must not race |

## Backward Compatibility Matrix

| Call Site | Single-User Mode | Multi-User Mode |
|-----------|-----------------|-----------------|
| `bridge.get_input()` | Blocks on default session | Blocks on active session |
| `bridge.emit(...)` | Broadcasts to all clients | Broadcasts to active session's clients |
| `bridge.agent_running` | Default session's flag | ANY session's flag |
| `bridge.submit_prompt(text)` | To default session | To active session |
| `ws_agent` receives msg | All clients share default | Each client bound to own session |

## Migration Path from `_AtlasBridge`

```python
# Before (single-user only)
bridge = _AtlasBridge()

# After (backward compatible)
bridge = _MultiUserBridge(single_user=not os.environ.get("ATLAS_MULTI_USER"))
# All existing code continues to work without modification
```
