"""Multi-user Atlas bridge with per-session isolation."""

from __future__ import annotations

import asyncio
import collections
import contextvars
import queue
import threading
import time
import weakref
from typing import Any, Callable

from core.session_process_manager import SessionProcessManager  # pyright: ignore[reportMissingImports]
from core.session_names import normalize_session_name


_atlas_bridge_session_id_cv = contextvars.ContextVar("atlas_bridge_session_id", default="")


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
            self._seen_msg_ids[msg_id] = time.monotonic()
            while len(self._seen_msg_ids) > self._SEEN_MSG_LIMIT:
                self._seen_msg_ids.popitem(last=False)
            return False


class _MultiUserBridge:
    """Manage multiple isolated session bridges with legacy delegation."""

    def __init__(self, single_user: bool = False, use_processes: bool = False):
        self._sessions = {}
        self._sessions_lock = threading.RLock()
        self._single_user = single_user
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
        for session_id in manager.list_active():
            since_id = self._process_output_cursors.get(session_id)
            for msg in manager.poll_output(session_id, since_id=since_id):
                msg_session_id = str(msg.get("session_id") or session_id)
                session = self._ensure_session(msg_session_id)
                payload = msg.get("payload")
                event = dict(payload) if isinstance(payload, dict) else {}
                event["type"] = str(msg.get("msg_type") or "")
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
                self._process_output_cursors[msg_session_id] = msg.get("id")

    def _normalize_session_id(self, session_id: str | None) -> str:
        if self._single_user:
            return "default"
        normalized = normalize_session_name(str(session_id or ""))
        return normalized or "default"

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

    def delete_session(self, session_id: str | None) -> bool:
        session_id = self._normalize_session_id(session_id)
        if session_id == "default":
            return False
        with self._sessions_lock:
            removed = self._sessions.pop(session_id, None)
        if removed is None:
            return False
        removed.request_stop()
        with self._active_lock:
            if self._active_session_id == session_id:
                self._active_session_id = "default"
        return True

    def activate_session(self, session_id: str | None) -> None:
        session = self._ensure_session(session_id)
        with self._active_lock:
            self._active_session_id = session.session_id
        session.touch()

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

    def get_input(self, prompt: str = "") -> str:
        return self._active_session().get_input(prompt)

    def poll_interrupt(self) -> str | None:
        return self._active_session().poll_interrupt()

    def emit(self, msg_type: str, **payload: Any) -> None:
        session_id = payload.get("session_id")
        if session_id is None:
            session_id = get_atlas_bridge_session_id() or None
        if session_id is not None:
            self._ensure_session(str(session_id)).emit(msg_type, **payload)
            return
        self._active_session().emit(msg_type, **payload)

    def pending_ask_user_events(self) -> list[dict[str, Any]]:
        return self._active_session().pending_ask_user_events()

    def session_pending_ask_user_events(self, session_id: str | None) -> list[dict[str, Any]]:
        return self._ensure_session(session_id).pending_ask_user_events()

    def open_question(self, flow_id: str) -> queue.Queue[Any]:
        return self._active_session().open_question(flow_id)

    def close_question(self, flow_id: str) -> None:
        self._active_session().close_question(flow_id)

    def wait_answer(self, flow_id: str, timeout: float | None = None) -> Any | None:
        return self._active_session().wait_answer(flow_id, timeout=timeout)

    def set_agent_starter(self, fn: Callable[[], None]) -> None:
        self._agent_starter = fn
        with self._sessions_lock:
            for session in self._sessions.values():
                session.set_agent_starter(fn)

    def ensure_agent_alive(self) -> None:
        if self._process_manager is not None:
            session = self._active_session()
            self._process_manager.spawn(session.session_id)
            session.agent_alive = True
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
            manager.spawn(session.session_id)
            session.agent_alive = True
            session.agent_running = True
        msg_id = manager.send_input(session.session_id, msg_type, payload or {})
        session.touch()
        return msg_id is not None

    def queue_prompt_for_session(self, session_id: str | None, text: str) -> None:
        if self._process_manager is not None:
            self._send_process_input_for_session(
                session_id, "prompt", {"text": text}, spawn=True
            )
            return
        self._ensure_session(session_id).queue_prompt(text)

    def submit_prompt_for_session(self, session_id: str | None, text: str) -> None:
        if self._process_manager is not None:
            self._send_process_input_for_session(
                session_id, "prompt", {"text": text}, spawn=True
            )
            return
        session = self._ensure_session(session_id)
        session._stop_flag = False
        if self._agent_starter is not None:
            session.set_agent_starter(self._agent_starter)
        session.ensure_agent_alive()
        session.touch()
        session._inbox.put(text)

    def submit_interrupt_for_session(self, session_id: str | None, text: str) -> None:
        if self._process_manager is not None:
            self._send_process_input_for_session(
                session_id, "interrupt", {"text": text}, spawn=True
            )
            return
        self._ensure_session(session_id)._interrupts.put(text)

    def submit_answer_for_session(self, session_id: str | None, flow_id: str, payload: dict[str, Any]) -> bool:
        if self._process_manager is not None:
            body = dict(payload or {})
            body.setdefault("flow_id", flow_id)
            return self._send_process_input_for_session(
                session_id, "answer", body, spawn=False
            )
        return self._ensure_session(session_id).submit_answer(flow_id, payload)

    def request_stop_for_session(self, session_id: str | None) -> None:
        if self._process_manager is not None:
            self._send_process_input_for_session(session_id, "stop", {}, spawn=False)
            return
        self._ensure_session(session_id).request_stop()

    def submit_answer(self, flow_id: str, payload: dict[str, Any]) -> bool:
        return self._active_session().submit_answer(flow_id, payload)

    def request_stop(self) -> None:
        if self._process_manager is not None:
            session = self._active_session()
            self._process_manager.send_input(session.session_id, "stop")
            return
        self._active_session().request_stop()

    def check_stop(self) -> bool:
        return self._active_session().check_stop()

    def msg_id_seen(self, msg_id: str) -> bool:
        return self._active_session().msg_id_seen(msg_id)

    async def next_event(self, timeout: float = 0.25) -> tuple[dict[str, Any] | None, str | None]:
        loop = asyncio.get_event_loop()

        def _poll():
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
            try:
                return self._default_session._outbox.get(timeout=timeout), "default"
            except queue.Empty:
                return None, None

        return await loop.run_in_executor(None, _poll)

    @property
    def agent_running(self) -> bool:
        if self._single_user:
            return self._default_session.agent_running
        if self._process_manager is not None:
            with self._active_lock:
                session_id = self._active_session_id
            return self._process_manager.is_alive(session_id)
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
