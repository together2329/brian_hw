"""Multi-user Atlas bridge with per-session isolation."""

from __future__ import annotations

import asyncio
import collections
import contextvars
import queue
import re
import threading
import time
import weakref
from typing import Any, Callable

from core.session_process_manager import SessionProcessManager  # pyright: ignore[reportMissingImports]
from core.session_names import normalize_session_name


_SESSION_PRIVATE_BROADCAST_TYPES = {
    "agent",
    "agent_received",
    "agent_state",
    "ask_user",
    "ask_user_answered",
    "ask_user_closed",
    "context",
    "cost",
    "done",
    "error",
    "file_changed",
    "flush",
    "mode_change",
    "reasoning",
    "slash_output",
    "ssot_qa_updated",
    "todo",
    "todo_line",
    "token",
    "token_usage",
    "tool",
    "tool_result",
    "worker_exited",
    "worker_started",
    "worker_stopped",
}


_atlas_bridge_session_id_cv = contextvars.ContextVar("atlas_bridge_session_id", default="")
_WRITE_TOOL_RE = re.compile(
    r"^(?:write_file|write_to_file|replace_in_file|replace_lines|replace_file_content|multi_replace_file_content|edit_file|patch_file|apply_patch|patch|update_file)\b",
    re.IGNORECASE,
)


def changed_paths_from_tool_result(tool: str, text: str) -> list[str]:
    """Best-effort extraction of files changed by write/replace/patch tools."""
    tool_s = str(tool or "")
    text_s = str(text or "")
    if not tool_s or not _WRITE_TOOL_RE.match(tool_s):
        return []

    candidates: list[str] = []

    def add(value: Any) -> None:
        path = str(value or "").strip().strip("'\"`")
        path = re.sub(r"[\s,;:]+$", "", path)
        if not path or "\n" in path or path in {".", ".."}:
            return
        if path not in candidates:
            candidates.append(path)

    for m in re.finditer(
        r"(?:"
        r"wrote to|wrote|updated|created|deleted|"
        r"(?:successfully\s+)?replaced\s+(?:in|to)|"
        r"replaced\s+\d+\s+occurrence(?:\(s\)|s)?\s+in"
        r")\s+['\"`]([^'\"`]+)['\"`]",
        text_s,
        re.IGNORECASE,
    ):
        add(m.group(1))
    for m in re.finditer(
        r"(?:wrote file|updated file|created file|deleted file|target_file|file_path|path)\s*[:=]\s*['\"`]?([^\s,'\"`)]+)",
        tool_s + "\n" + text_s,
        re.IGNORECASE,
    ):
        add(m.group(1))
    for m in re.finditer(
        r"^\*\*\*\s+(?:Update|Add|Delete)\s+File:\s+(.+?)\s*$",
        text_s,
        re.MULTILINE,
    ):
        add(m.group(1))
    for m in re.finditer(
        r"^(?:[MADRCU]|\?\?)\s+(.+?)\s*$",
        text_s,
        re.MULTILINE,
    ):
        add(m.group(1))
    for m in re.finditer(
        r"^Update\(([^)]+)\)",
        text_s,
        re.MULTILINE,
    ):
        add(m.group(1))
    for m in re.finditer(
        r"(?:in|to)\s+([\w./_-]+\.(?:sv|v|vh|svh|yaml|yml|md|f|txt|log|json|py|sdc|upf|tcl|css|js|jsx|ts|tsx|html))",
        text_s,
        re.IGNORECASE | re.MULTILINE,
    ):
        add(m.group(1))
    return candidates


def set_atlas_bridge_session_id(session_id: str | None):
    return _atlas_bridge_session_id_cv.set(normalize_session_name(str(session_id or "")))


def reset_atlas_bridge_session_id(token) -> None:
    _atlas_bridge_session_id_cv.reset(token)


def get_atlas_bridge_session_id() -> str:
    return _atlas_bridge_session_id_cv.get()


class _SessionBridge:
    """Per-session bridge state between the agent loop and WS clients."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self._inbox = queue.Queue()
        self._interrupts = queue.Queue()
        self._outbox = queue.Queue()
        self._answer_qs = {}
        self._answer_lock = threading.Lock()
        self._pending_ask_user = {}
        self._pending_ask_user_lock = threading.Lock()
        self.agent_running = False
        self.agent_alive = False
        self._agent_lock = threading.Lock()
        self._agent_starter = None
        self._stop_flag = False
        self.clients = weakref.WeakSet()
        self.created_at = time.time()
        self.last_active = time.time()
        self._seen_msg_ids: collections.OrderedDict[str, float] = collections.OrderedDict()
        self._seen_msg_ids_lock = threading.Lock()
        self._SEEN_MSG_LIMIT = 256
        # Orchestrator chat watermark — the last chat_message.id this session
        # already injected as feedback into the agent. Seeded lazily from the
        # DB on first read so a restarted agent does not re-replay history.
        self.last_chat_seen_id: str = ""

    def touch(self):
        self.last_active = time.time()

    def get_input(self, prompt: str = "") -> str:
        self.touch()
        return self._inbox.get()

    def poll_interrupt(self) -> str | None:
        try:
            value = self._interrupts.get_nowait()
        except queue.Empty:
            return None
        self.touch()
        return value

    def emit(self, msg_type: str, **payload: Any) -> None:
        msg = {"type": msg_type, **payload}
        if self.session_id != "default":
            msg.setdefault("session_id", self.session_id)
        if msg_type == "ask_user":
            session = normalize_session_name(str(msg.get("session") or self.session_id or ""))
            if session:
                msg.setdefault("session", session)
        flow_id = str(payload.get("flow_id") or "")
        if flow_id:
            with self._pending_ask_user_lock:
                if msg_type == "ask_user":
                    self._pending_ask_user[flow_id] = dict(msg)
                elif msg_type in {"ask_user_answered", "ask_user_closed"}:
                    self._pending_ask_user.pop(flow_id, None)
        self.touch()
        self._outbox.put_nowait(msg)

    def pending_ask_user_events(self) -> list[dict[str, Any]]:
        with self._pending_ask_user_lock:
            return [dict(event) for event in self._pending_ask_user.values()]

    def open_question(self, flow_id: str) -> queue.Queue[Any]:
        q = queue.Queue()
        with self._answer_lock:
            self._answer_qs[flow_id] = q
        self.touch()
        return q

    def close_question(self, flow_id: str) -> None:
        with self._answer_lock:
            self._answer_qs.pop(flow_id, None)
        self.emit("ask_user_closed", flow_id=flow_id)

    def wait_answer(self, flow_id: str, timeout: float | None = None) -> Any | None:
        with self._answer_lock:
            q = self._answer_qs.get(flow_id)
        if q is None:
            return None
        try:
            answer = q.get(timeout=timeout)
        except queue.Empty:
            return None
        self.touch()
        return answer

    def set_agent_starter(self, fn: Callable[[], None]) -> None:
        self._agent_starter = fn

    def ensure_agent_alive(self) -> None:
        starter = self._agent_starter
        if starter is None:
            return
        with self._agent_lock:
            if self.agent_alive:
                return
            self.agent_alive = True
            self._stop_flag = False
        token = set_atlas_bridge_session_id(self.session_id)
        try:
            starter()
        finally:
            reset_atlas_bridge_session_id(token)

    def queue_prompt(self, text: str) -> None:
        self._inbox.put(text)

    def submit_prompt(self, text: str) -> None:
        self._stop_flag = False
        self.ensure_agent_alive()
        self.touch()
        # Route every prompt — slash or not — into _inbox. The previous
        # branch shoved non-slash text into _interrupts whenever
        # agent_running was True, on the theory that react_loop polls
        # interrupts mid-iteration. But mid-iteration polling only
        # happens between LLM turns; if an LLM HTTP call blocks
        # (OAuth expired, network stall, provider timeout) the
        # interrupt queue accumulates and never drains, and the user
        # sees their submissions go to the void. _inbox is the queue
        # the agent input loop always consumes between turns, so
        # routing here guarantees forward progress whenever the LLM
        # call eventually returns or is reset by the watchdog.
        self._inbox.put(text)

    def submit_answer(self, flow_id: str, payload: dict[str, Any]) -> bool:
        with self._answer_lock:
            q = self._answer_qs.get(flow_id)
        if q is None:
            return False
        q.put(payload)
        self.emit("ask_user_answered", flow_id=flow_id)
        return True

    def has_answer_flow(self, flow_id: str) -> bool:
        with self._answer_lock:
            return flow_id in self._answer_qs

    def request_stop(self) -> None:
        self._stop_flag = True
        user_kept = []
        try:
            while True:
                item = self._inbox.get_nowait()
                if not str(item or "").lstrip().startswith("/"):
                    user_kept.append(item)
        except queue.Empty:
            pass
        for item in user_kept:
            self._inbox.put(item)
        self.touch()

    def check_stop(self) -> bool:
        if self._stop_flag:
            self._stop_flag = False
            self.touch()
            return True
        return False

    def msg_id_seen(self, msg_id: str) -> bool:
        if not msg_id:
            return False
        with self._seen_msg_ids_lock:
            if msg_id in self._seen_msg_ids:
                self._seen_msg_ids.move_to_end(msg_id)
                return True
            self._remember_msg_id_locked(msg_id)
            return False

    def has_msg_id(self, msg_id: str) -> bool:
        if not msg_id:
            return False
        with self._seen_msg_ids_lock:
            found = msg_id in self._seen_msg_ids
            if found:
                self._seen_msg_ids.move_to_end(msg_id)
            return found

    def mark_msg_id_seen(self, msg_id: str) -> None:
        if not msg_id:
            return
        with self._seen_msg_ids_lock:
            self._remember_msg_id_locked(msg_id)

    def _remember_msg_id_locked(self, msg_id: str) -> None:
        self._seen_msg_ids[msg_id] = time.monotonic()
        self._seen_msg_ids.move_to_end(msg_id)
        while len(self._seen_msg_ids) > self._SEEN_MSG_LIMIT:
            self._seen_msg_ids.popitem(last=False)


class _MultiUserBridge:
    """Manage multiple isolated session bridges with legacy delegation."""

    def __init__(
        self,
        single_user: bool = False,
        use_processes: bool = False,
        strict_session_routing: bool = False,
        single_worker_per_owner: bool = False,
    ):
        self._sessions = {}
        self._sessions_lock = threading.RLock()
        self._single_user = single_user
        self._strict_session_routing = strict_session_routing
        self._single_worker_per_owner = single_worker_per_owner
        self._owner_active_sessions = {}
        self._active_session_id = "default"
        self._active_lock = threading.Lock()
        self._agent_starter = None
        self._process_manager = SessionProcessManager() if (use_processes and not single_user) else None
        self._process_output_cursors = {}
        self._default_session = self._ensure_session("default")

    def _using_processes(self) -> bool:
        return self._process_manager is not None

    def _poll_process_outputs(self) -> None:
        manager = self._process_manager
        if manager is None:
            return
        dead_sessions: list[str] = []
        cleanup = getattr(manager, "cleanup_zombies", None)
        if callable(cleanup):
            try:
                dead_sessions = [str(session_id) for session_id in cleanup()]
            except Exception:
                dead_sessions = []
        for session_id in list(dict.fromkeys([*manager.list_active(), *dead_sessions])):
            since_id = self._process_output_cursors.get(session_id)
            saw_lifecycle_end = False
            for msg in manager.poll_output(session_id, since_id=since_id):
                msg_session_id = str(msg.get("session_id") or session_id)
                session = self._ensure_session(msg_session_id)
                payload = msg.get("payload")
                event = dict(payload) if isinstance(payload, dict) else {}
                event["type"] = str(msg.get("msg_type") or "")
                if event["type"] == "agent_state" and isinstance(event.get("running"), bool):
                    session.agent_running = bool(event["running"])
                    if session.agent_running:
                        session.agent_alive = True
                    event.setdefault("alive", session.agent_alive)
                elif event["type"] == "worker_started":
                    session.agent_alive = True
                    event.setdefault("alive", True)
                elif event["type"] in {"worker_exited", "worker_stopped"}:
                    session.agent_alive = False
                    session.agent_running = False
                    event.setdefault("alive", False)
                    saw_lifecycle_end = True
                if session.session_id != "default":
                    event.setdefault("session_id", session.session_id)
                if event["type"] == "ask_user":
                    normalized = normalize_session_name(str(event.get("session") or session.session_id or ""))
                    if normalized:
                        event.setdefault("session", normalized)
                flow_id = str(event.get("flow_id") or "")
                if flow_id:
                    with session._pending_ask_user_lock:
                        if event["type"] == "ask_user":
                            session._pending_ask_user[flow_id] = dict(event)
                        elif event["type"] in {"ask_user_answered", "ask_user_closed"}:
                            session._pending_ask_user.pop(flow_id, None)
                session.touch()
                session._outbox.put_nowait(event)
                # Mirror atlas_ui._emit_tool_result's file_changed emit
                # for process-mode worker writes. The main process's
                # _textual_emit_tool_result_fn never fires here (workers
                # generate tool_result rows themselves), so without this
                # the open SSOT preview / file tree wouldn't auto-reload
                # when an agent in a subprocess wrote a yaml/rtl file.
                if event["type"] == "tool_result":
                    self._maybe_emit_file_changed(session, event)
                self._process_output_cursors[msg_session_id] = msg.get("id")
            if session_id in dead_sessions and not saw_lifecycle_end:
                session = self._ensure_session(session_id)
                if session.agent_alive or session.agent_running:
                    self._emit_process_dead(
                        session,
                        reason="process exited before producing worker_exited",
                    )

    def _maybe_emit_file_changed(self, session: "_SessionBridge", event: dict) -> None:
        tool = str(event.get("tool") or "")
        text = str(event.get("text") or event.get("content") or "")
        for path in changed_paths_from_tool_result(tool, text):
            session.emit("file_changed", path=path, tool=tool)

    def _normalize_session_id(self, session_id: str | None) -> str:
        if self._single_user:
            return "default"
        normalized = normalize_session_name(str(session_id or ""))
        return normalized or "default"

    def _owner_from_session_id(self, session_id: str | None) -> str:
        normalized = self._normalize_session_id(session_id)
        parts = [part for part in normalized.split("/") if part]
        return parts[0] if parts else "default"

    def _mark_owner_active(self, session_id: str | None) -> None:
        normalized = self._normalize_session_id(session_id)
        owner = self._owner_from_session_id(normalized)
        with self._sessions_lock:
            self._owner_active_sessions[owner] = normalized

    def active_session_for_owner(self, owner: str | None) -> str:
        normalized_owner = normalize_session_name(str(owner or "")).split("/", 1)[0]
        if not normalized_owner:
            return ""
        with self._sessions_lock:
            return str(self._owner_active_sessions.get(normalized_owner) or "")

    def is_session_running(self, session_id: str | None) -> bool:
        normalized = self._normalize_session_id(session_id)
        session = self._ensure_session(normalized)
        if self._process_manager is not None and self._process_manager.is_alive(normalized):
            return True
        return bool(session.agent_running)

    def _kill_owner_siblings_for_process_spawn(self, session_id: str) -> None:
        manager = self._process_manager
        if manager is None or not self._single_worker_per_owner:
            return
        owner = self._owner_from_session_id(session_id)
        for active_session_id in list(manager.list_active()):
            if active_session_id == session_id:
                continue
            if self._owner_from_session_id(active_session_id) != owner:
                continue
            manager.kill(active_session_id)
            sibling = self._ensure_session(active_session_id)
            sibling.agent_running = False
            sibling.agent_alive = False
            sibling.emit("agent_state", running=False, alive=False)
            sibling.emit("worker_exited", session_id=sibling.session_id)
            sibling.emit("done")
            self._process_output_cursors.pop(active_session_id, None)

    def _spawn_process_session(
        self,
        session: "_SessionBridge",
        *,
        running: bool = False,
    ) -> bool:
        manager = self._process_manager
        if manager is None:
            return False
        self._kill_owner_siblings_for_process_spawn(session.session_id)
        if not manager.is_alive(session.session_id):
            latest_output_id = manager.latest_output_id(session.session_id)
            if latest_output_id:
                self._process_output_cursors[session.session_id] = latest_output_id
            else:
                self._process_output_cursors.pop(session.session_id, None)
        spawned = bool(manager.spawn(session.session_id))
        self._mark_owner_active(session.session_id)
        alive = bool(manager.is_alive(session.session_id)) if spawned else False
        session.agent_alive = alive
        if running:
            session.agent_running = True
        session.emit("agent_state", running=bool(session.agent_running), alive=alive)
        return alive

    def _emit_process_dead(self, session: "_SessionBridge", *, reason: str) -> None:
        session.agent_running = False
        session.agent_alive = False
        session.emit("agent_state", running=False, alive=False)
        session.emit("worker_exited", session_id=session.session_id, reason=reason)
        session.emit("done")

    def _ensure_session(self, session_id: str | None) -> _SessionBridge:
        session_id = self._normalize_session_id(session_id)
        with self._sessions_lock:
            session = self._sessions.get(session_id)
            if session is None:
                session = _SessionBridge(session_id)
                if self._agent_starter is not None:
                    session.set_agent_starter(self._agent_starter)
                self._sessions[session_id] = session
            return session

    def get_session(self, session_id: str | None) -> _SessionBridge:
        session_id = self._normalize_session_id(session_id)
        with self._sessions_lock:
            return self._sessions[session_id]

    def list_sessions(self) -> list[_SessionBridge]:
        with self._sessions_lock:
            return list(self._sessions.values())

    def broadcast_all(self, msg_type: str, **payload: Any) -> None:
        """Fan-out a single message to every active session's outbox.

        Per-session emit() routes to one session's WS clients only; chat
        rooms cross session boundaries (user on uart_lite session must see
        a global-room post from a user on a dma session), so chat events
        emit through this path instead. Each session keeps the same msg_id
        bookkeeping on the receiving WS leg."""
        if str(msg_type or "") in _SESSION_PRIVATE_BROADCAST_TYPES:
            self.emit(msg_type, **payload)
            return
        with self._sessions_lock:
            sessions = list(self._sessions.values())
        for session in sessions:
            session.emit(msg_type, **payload)

    def delete_session(self, session_id: str | None) -> bool:
        session_id = self._normalize_session_id(session_id)
        if session_id == "default":
            return False
        with self._sessions_lock:
            removed = self._sessions.pop(session_id, None)
            owner = self._owner_from_session_id(session_id)
            if self._owner_active_sessions.get(owner) == session_id:
                self._owner_active_sessions.pop(owner, None)
        if removed is None:
            return False
        removed.request_stop()
        with self._active_lock:
            if self._active_session_id == session_id:
                self._active_session_id = "default"
        return True

    def activate_session(self, session_id: str | None, *, warm: bool = False) -> None:
        session = self._ensure_session(session_id)
        with self._active_lock:
            self._active_session_id = session.session_id
        self._mark_owner_active(session.session_id)
        session.touch()
        if warm:
            self.warm_session(session.session_id)

    def warm_session(self, session_id: str | None = None) -> dict[str, Any]:
        session = self._ensure_session(session_id)
        if self._process_manager is not None:
            was_alive = self._process_manager.is_alive(session.session_id)
            alive = self._spawn_process_session(session, running=False)
            pid = None
            try:
                pid = self._process_manager.get_pid(session.session_id)
            except Exception:
                pid = None
            return {
                "enabled": True,
                "mode": "process",
                "session_id": session.session_id,
                "status": "ready" if was_alive else ("started" if alive else "error"),
                "alive": alive,
                "pid": pid or 0,
            }
        if self._agent_starter is None:
            return {
                "enabled": False,
                "mode": "thread",
                "session_id": session.session_id,
                "reason": "missing_agent_starter",
            }
        was_alive = bool(session.agent_alive)
        session.ensure_agent_alive()
        return {
            "enabled": True,
            "mode": "thread",
            "session_id": session.session_id,
            "status": "ready" if was_alive else ("started" if session.agent_alive else "error"),
            "alive": bool(session.agent_alive),
        }


    def bind_client(self, client: Any, session_id: str | None) -> str:
        session = self._ensure_session(session_id)
        with self._sessions_lock:
            for existing in self._sessions.values():
                existing.clients.discard(client)
            session.clients.add(client)
            peers = len(session.clients)
        session.touch()
        # Latest bound client wins the active session — without this the
        # main-process chat_loop keeps polling the 'default' inbox and
        # a logged-in user's prompts queue up unread.
        with self._active_lock:
            self._active_session_id = session.session_id
        self._mark_owner_active(session.session_id)
        # Keep WebSocket bind/session switches cheap. In process-per-session
        # mode, prompt/interrupt dispatch already spawns the worker lazily with
        # spawn=True; eager warming here made IP switches wait on process start.
        if peers > 1:
            session.emit("peer_joined", peers=peers, session_id=session.session_id)
        return session.session_id

    def unbind_client(self, client: Any) -> None:
        affected_session = None
        remaining = 0
        with self._sessions_lock:
            for session in self._sessions.values():
                if client in session.clients:
                    affected_session = session
                    break
            if affected_session is not None:
                affected_session.clients.discard(client)
                remaining = len(affected_session.clients)
        if affected_session is not None and remaining > 0:
            affected_session.emit("peer_left", peers=remaining, session_id=affected_session.session_id)

    def get_client_session(self, client: Any) -> _SessionBridge | None:
        with self._sessions_lock:
            for session in self._sessions.values():
                if client in session.clients:
                    return session
        return None

    def _active_session(self) -> _SessionBridge:
        with self._active_lock:
            session_id = self._active_session_id
        return self._ensure_session(session_id)

    def _context_session(self) -> _SessionBridge:
        session_id = get_atlas_bridge_session_id() or None
        if session_id is not None:
            return self._ensure_session(session_id)
        if self._strict_session_routing:
            raise RuntimeError("strict session routing requires an explicit session context")
        return self._active_session()

    def get_input(self, prompt: str = "") -> str:
        return self._context_session().get_input(prompt)

    def poll_interrupt(self) -> str | None:
        return self._context_session().poll_interrupt()

    def emit(self, msg_type: str, **payload: Any) -> None:
        session_id = payload.get("session_id")
        if session_id is None:
            session_id = get_atlas_bridge_session_id() or None
        if session_id is not None:
            self._ensure_session(str(session_id)).emit(msg_type, **payload)
            return
        self._context_session().emit(msg_type, **payload)

    def pending_ask_user_events(self) -> list[dict[str, Any]]:
        return self._context_session().pending_ask_user_events()

    def session_pending_ask_user_events(self, session_id: str | None) -> list[dict[str, Any]]:
        return self._ensure_session(session_id).pending_ask_user_events()

    @property
    def _pending_ask_user(self) -> dict[str, dict[str, Any]]:
        """Legacy aggregate view used by older tests and UI helpers."""
        pending: dict[str, dict[str, Any]] = {}
        with self._sessions_lock:
            sessions = list(self._sessions.values())
        for session in sessions:
            with session._pending_ask_user_lock:
                pending.update({flow_id: dict(event) for flow_id, event in session._pending_ask_user.items()})
        return pending

    def open_question(self, flow_id: str) -> queue.Queue[Any]:
        return self._context_session().open_question(flow_id)

    def close_question(self, flow_id: str) -> None:
        self._context_session().close_question(flow_id)

    def wait_answer(self, flow_id: str, timeout: float | None = None) -> Any | None:
        return self._context_session().wait_answer(flow_id, timeout=timeout)

    def set_agent_starter(self, fn: Callable[[], None]) -> None:
        self._agent_starter = fn
        with self._sessions_lock:
            for session in self._sessions.values():
                session.set_agent_starter(fn)

    def ensure_agent_alive(self) -> None:
        if self._process_manager is not None:
            session = self._active_session()
            self._spawn_process_session(session, running=False)
            return
        with self._sessions_lock:
            if any(session.agent_alive for session in self._sessions.values()):
                return
        session = self._active_session()
        if self._agent_starter is not None:
            session.set_agent_starter(self._agent_starter)
        session.ensure_agent_alive()

    def queue_prompt(self, text: str) -> None:
        if self._process_manager is not None:
            session = self._active_session()
            self.queue_prompt_for_session(session.session_id, text)
            return
        self._active_session().queue_prompt(text)

    def submit_prompt(self, text: str) -> None:
        if self._process_manager is not None:
            session = self._active_session()
            self.submit_prompt_for_session(session.session_id, text)
            return
        session = self._active_session()
        session._stop_flag = False
        self.ensure_agent_alive()
        session.touch()
        # Always route to _inbox (see SessionBridge.submit_prompt for
        # rationale): the _interrupts queue only drains mid-iteration,
        # so a stuck LLM HTTP call would otherwise strand user input
        # forever. _inbox is consumed between turns, guaranteed.
        session._inbox.put(text)

    def _send_process_input_for_session(
        self,
        session_id: str | None,
        msg_type: str,
        payload: dict[str, Any] | None = None,
        *,
        spawn: bool = False,
    ) -> bool:
        manager = self._process_manager
        if manager is None:
            return False
        session = self._ensure_session(session_id)
        if spawn:
            self._spawn_process_session(session, running=True)
        msg_id = manager.send_input(session.session_id, msg_type, payload or {})
        # Crash-at-startup / spawn-fail safety net: send_input returns None
        # when the worker process is not alive at the is_alive() gate
        # (session_process_manager.py:408-409), so the message was never
        # enqueued into the durable DB session_queue. For real user inputs
        # (prompt/interrupt) this is silent loss because the frontend
        # retransmit layer has already been disarmed. Respawn once and retry
        # the enqueue so a single startup crash converts to success without a
        # client round trip. msg_id dedup at the WS layer still guards against
        # a retried duplicate that races the first delivery.
        if (
            msg_id is None
            and spawn
            and msg_type in {"prompt", "interrupt"}
        ):
            cleanup = getattr(manager, "cleanup_zombies", None)
            if callable(cleanup):
                try:
                    cleanup()
                except Exception:
                    pass
            self._spawn_process_session(session, running=True)
            msg_id = manager.send_input(session.session_id, msg_type, payload or {})
        session.touch()
        if msg_id is None:
            cleanup = getattr(manager, "cleanup_zombies", None)
            if callable(cleanup):
                try:
                    cleanup()
                except Exception:
                    pass
            if spawn and msg_type in {"prompt", "interrupt"}:
                self._emit_process_dead(
                    session,
                    reason=f"{msg_type} input was not delivered",
                )
                session.emit(
                    "error",
                    message=(
                        "session worker is not available; "
                        "input was not delivered"
                    ),
                )
        return msg_id is not None

    def queue_prompt_for_session(self, session_id: str | None, text: str) -> bool:
        if self._process_manager is not None:
            return self._send_process_input_for_session(
                session_id, "prompt", {"text": text}, spawn=True
            )
        self._ensure_session(session_id).queue_prompt(text)
        return True

    def submit_prompt_for_session(self, session_id: str | None, text: str) -> bool:
        if self._process_manager is not None:
            return self._send_process_input_for_session(
                session_id, "prompt", {"text": text}, spawn=True
            )
        session = self._ensure_session(session_id)
        session._stop_flag = False
        if self._agent_starter is not None:
            session.set_agent_starter(self._agent_starter)
        session.ensure_agent_alive()
        session.touch()
        session._inbox.put(text)
        return True

    def submit_interrupt_for_session(self, session_id: str | None, text: str) -> None:
        if self._process_manager is not None:
            self._send_process_input_for_session(
                session_id, "interrupt", {"text": text}, spawn=True
            )
            return
        self._ensure_session(session_id)._interrupts.put(text)

    def submit_answer_for_session(self, session_id: str | None, flow_id: str, payload: dict[str, Any]) -> bool:
        session = self._ensure_session(session_id)
        # Slash handlers such as /sim-debug can open human-gate questions in
        # the main process even when process-per-session mode is enabled for
        # normal agent turns. Prefer that local queue when it exists; otherwise
        # forward to the child session process that emitted the question.
        if session.has_answer_flow(flow_id):
            return session.submit_answer(flow_id, payload)
        if self._process_manager is not None:
            body = dict(payload or {})
            body.setdefault("flow_id", flow_id)
            return self._send_process_input_for_session(
                session_id, "answer", body, spawn=False
            )
        return session.submit_answer(flow_id, payload)

    def request_stop_for_session(self, session_id: str | None) -> None:
        if self._process_manager is not None:
            self._send_process_input_for_session(session_id, "stop", {}, spawn=False)
            return
        self._ensure_session(session_id).request_stop()

    def exit_session(self, session_id: str | None) -> None:
        session = self._ensure_session(session_id)
        if self._process_manager is not None:
            self._process_manager.kill(session.session_id)
            self._process_output_cursors.pop(session.session_id, None)
        else:
            session.request_stop()
        session.agent_running = False
        session.agent_alive = False
        session.emit("agent_state", running=False, alive=False)
        session.emit("worker_exited", session_id=session.session_id)
        session.emit("done")

    def stop_all_processes(self) -> None:
        if self._process_manager is None:
            return
        self._process_manager.stop_all()
        with self._sessions_lock:
            sessions = list(self._sessions.values())
        for session in sessions:
            session.agent_running = False
            session.agent_alive = False

    def exit_active_session(self) -> None:
        session = self._active_session()
        self.exit_session(session.session_id)

    def submit_answer(self, flow_id: str, payload: dict[str, Any]) -> bool:
        return self._active_session().submit_answer(flow_id, payload)

    def request_stop(self) -> None:
        if self._process_manager is not None:
            session = self._active_session()
            self._process_manager.send_input(session.session_id, "stop")
            return
        self._active_session().request_stop()

    def check_stop(self) -> bool:
        return self._context_session().check_stop()

    def msg_id_seen(self, msg_id: str) -> bool:
        return self._context_session().msg_id_seen(msg_id)

    async def next_event(self, timeout: float = 0.05) -> tuple[dict[str, Any] | None, str | None]:
        loop = asyncio.get_event_loop()

        def _poll():
            deadline = time.monotonic() + max(float(timeout or 0), 0.0)
            while True:
                if self._process_manager is not None:
                    self._poll_process_outputs()
                with self._sessions_lock:
                    sessions = list(self._sessions.values())
                for sess in sessions:
                    try:
                        evt = sess._outbox.get_nowait()
                        return evt, sess.session_id
                    except queue.Empty:
                        continue
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return None, None
                time.sleep(min(0.01, remaining))

        return await loop.run_in_executor(None, _poll)

    @property
    def agent_running(self) -> bool:
        if self._single_user:
            return self._default_session.agent_running
        if self._process_manager is not None:
            with self._sessions_lock:
                return any(session.agent_running for session in self._sessions.values())
        with self._sessions_lock:
            return any(session.agent_running for session in self._sessions.values())

    @agent_running.setter
    def agent_running(self, value: bool) -> None:
        with self._sessions_lock:
            if not value:
                for session in self._sessions.values():
                    session.agent_running = False
                return
        self._active_session().agent_running = True

    @property
    def agent_alive(self) -> bool:
        if self._single_user:
            return self._default_session.agent_alive
        if self._process_manager is not None:
            with self._active_lock:
                session_id = self._active_session_id
            return self._process_manager.is_alive(session_id)
        with self._sessions_lock:
            return any(session.agent_alive for session in self._sessions.values())

    @agent_alive.setter
    def agent_alive(self, value: bool) -> None:
        with self._sessions_lock:
            if not value:
                for session in self._sessions.values():
                    session.agent_alive = False
                return
        self._active_session().agent_alive = True
