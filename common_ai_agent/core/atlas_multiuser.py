"""Multi-user Atlas bridge with per-session isolation."""

from __future__ import annotations

import asyncio
import collections
import contextvars
import os
import queue
import re
import threading
import time
import weakref
from typing import Any, Callable

from core.session_process_manager import SessionProcessManager  # pyright: ignore[reportMissingImports]
from core.session_worker_policy import SessionWorkerPolicy  # pyright: ignore[reportMissingImports]
from core.session_names import normalize_session_name

try:  # The defined non-silent absent-cursor signal (plan §2.4 / R5).
    from core.atlas_db import QueueCursorNotFound as _QueueCursorNotFound
except Exception:  # pragma: no cover - defensive: keep poll path importable.
    class _QueueCursorNotFound(Exception):
        """Fallback so the poll path imports even if atlas_db is unavailable."""


from dataclasses import dataclass as _dataclass


@_dataclass(frozen=True)
class PromptDeliveryResult:
    """Structured result of a prompt-delivery attempt (Wave-3 C2).

    The historical ``submit_prompt_for_session`` / ``_send_process_input_for_session``
    keep returning ``bool`` (8+ ``assert delivered is True/False`` callers depend on
    identity). This object is the PARALLEL surface used only by the websocket ack
    path so ``capacity_wait`` can travel to
    ``agent_accepted{ok:false,error:"capacity_wait"}`` with no ``agent_received``.

    ``status`` is one of: ``delivered``, ``capacity_wait``, ``not_delivered``,
    ``no_manager``. ``ok`` is True only for ``delivered``. ``spawn_result`` carries
    the underlying :class:`SpawnResult` when admission was evaluated (capacity case),
    else None. ``reason`` is a short machine token; ``error`` is the human string the
    websocket surfaces (``"capacity_wait"`` for the capacity case so the frontend
    retry/hold path stays armed; a worker-unavailable string otherwise).
    """

    ok: bool
    status: str
    reason: str = ""
    session_id: str = ""
    owner_slot: str = ""
    msg_id: str = ""
    spawn_result: object = None
    error: str = ""


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
    # Single-active owner-slot lifecycle (Task 3 / Task 7). These are strictly
    # per-session: a switch or eviction for owner A's slot must NEVER fan out to
    # owner B (Wave-3 H12). They route through emit() to the owning session only.
    "worker_evicted",
    "worker_exited",
    "worker_started",
    "worker_stopped",
    "worker_switching",
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


def _owner_slot_with_model(owner: str) -> str:
    """Apply the SAME idempotent per-model owner scoping the API layer uses.

    Mirror of ``_session_owner_with_model`` in src/atlas_ui.py /
    src/atlas_api_sessions.py: when ``ATLAS_SESSION_PER_MODEL`` is enabled the
    owner slot becomes ``<owner>__<model_slug>``. Kept here (not imported) so the
    bridge has no import dependency on the FastAPI app module, and idempotent so
    re-applying it to an already-scoped segment[0] is a no-op. This is what lets
    ``owner_slot_key`` honor ATLAS_SESSION_PER_MODEL while staying byte-identical
    to the keys ``_owner_active_sessions`` is already populated with.
    """
    base = str(owner or "default").strip() or "default"
    enabled = os.environ.get("ATLAS_SESSION_PER_MODEL", "0").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    if not enabled:
        return base
    raw_model = (
        os.environ.get("LLM_ACTIVE_MODEL_NAME")
        or os.environ.get("MODEL_NAME")
        or os.environ.get("LLM_MODEL_NAME")
        or ""
    ).strip()
    if not raw_model:
        return base
    model_slug = re.sub(r"[^A-Za-z0-9_-]+", "_", raw_model).strip("_")
    if not model_slug:
        return base
    if base.endswith(f"__{model_slug}"):
        return base
    return f"{base}__{model_slug}"


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
        # Task 2: resolve the interactive session-worker policy once. Built from
        # the environment, with the legacy single_worker_per_owner constructor
        # flag as the fallback when ATLAS_SESSION_WORKER_POLICY is unset (the new
        # policy env always wins). _is_strict_single_active() reads self._policy;
        # self.policy is the public alias used by the status endpoint + harness.
        self._policy = SessionWorkerPolicy.from_env(
            single_worker_per_owner=single_worker_per_owner
        )
        self.policy = self._policy
        self._owner_active_sessions = {}
        # Per-owner-slot serialization for activation / warmup / prompt-spawn so a
        # same owner slot does a deterministic terminate-then-spawn switch with no
        # handoff overlap. SEPARATE from _sessions_lock on purpose: switching may
        # block on process termination (stop-ack + kill grace), and that MUST NOT
        # be held under _sessions_lock or _active_lock (Wave-3 F5 / plan Locking
        # And Switch Semantics). RLock so a strict switch can re-enter bridge
        # helpers (e.g. _ensure_session, _clear_owner_slot) on the same thread.
        # LOCK ORDER (never inverted): _owner_slot_lock -> _sessions_lock /
        # _active_lock. No sleep ever happens while _sessions_lock/_active_lock is
        # held; only _owner_slot_lock is held across termination, and it is held
        # PER OWNER SLOT semantically (one RLock instance, but contention is only
        # between operations on the same owner — unrelated owners interleave their
        # critical sections since each acquires-uses-releases quickly except the
        # rare same-owner switch).
        self._owner_slot_lock = threading.RLock()
        self._active_session_id = "default"
        self._active_lock = threading.Lock()
        self._agent_starter = None
        self._process_manager = SessionProcessManager() if (use_processes and not single_user) else None
        self._process_output_cursors = {}
        # Idle-reaper throttle clock (Task 7 / Wave-3 C1). The reaper runs on the
        # next_event() executor thread (off the asyncio broadcaster loop) and is
        # rate-limited to at most once per policy.reaper_interval_sec via this
        # monotonic stamp. Guarded by _sessions_lock when read/written.
        self._last_reap_at = 0.0
        self._default_session = self._ensure_session("default")

    def _using_processes(self) -> bool:
        return self._process_manager is not None

    @staticmethod
    def _poll_session_outputs(manager: Any, session_id: str, since_id: Any) -> list:
        """Poll a session's outputs, surfacing the absent-cursor signal (R5).

        Passes ``on_absent_cursor='raise'`` to the real SessionProcessManager so
        a recreated/swapped runtime DB raises :class:`QueueCursorNotFound` rather
        than silently returning 0 rows. Test/legacy managers whose ``poll_output``
        does not accept the keyword fall back to the 2-arg call (they never swap
        the DB underneath the cursor, so the silent path is acceptable there).
        """
        try:
            return list(
                manager.poll_output(
                    session_id, since_id=since_id, on_absent_cursor="raise"
                )
            )
        except TypeError:
            return list(manager.poll_output(session_id, since_id=since_id))

    @staticmethod
    def _reseed_output_cursor(manager: Any, session_id: str) -> Any:
        """Ask the manager to re-seed the cursor; None if unsupported/no rows."""
        reseed = getattr(manager, "reseed_output_cursor", None)
        if not callable(reseed):
            return None
        try:
            return reseed(session_id)
        except Exception:
            return None

    @staticmethod
    def _mark_outputs_delivered(manager: Any, session_id: str, up_to_id: Any) -> None:
        """Durably mark a delivered out-row BATCH after the outbox put succeeds.

        Called once per poll batch per session (NOT per token): ``up_to_id`` is
        the highest out-row id just pushed to this session's outbox. Marking
        ``delivered_at`` durably is what gives ``reseed_output_cursor`` a real
        resume point after a runtime-DB swap and lets ``cleanup_old_messages``
        purge old delivered out-rows so runtime DBs don't grow unbounded (plan
        §2.4/§2.12 / R5/R22). One UPDATE per batch keeps write amplification low.

        Prefers a manager-level ``mark_outputs_delivered`` if present; otherwise
        reaches the session's runtime DB handle (``_get_runtime_db``) — the SAME
        file ``poll_output`` read from — and marks there. Best-effort: a failure
        here must not break the deliver loop (the in-memory cursor already
        advanced; the next batch's mark re-covers any rows missed)."""
        if not up_to_id:
            return
        marker = getattr(manager, "mark_outputs_delivered", None)
        if callable(marker):
            try:
                marker(session_id, up_to_id)
                return
            except Exception:
                return
        get_runtime_db = getattr(manager, "_get_runtime_db", None)
        if not callable(get_runtime_db):
            return
        try:
            db = get_runtime_db(session_id)
            db.mark_outputs_delivered(session_id, up_to_id, "out")
        except Exception:
            return

    def _emit_runtime_db_recovery(self, session_id: str, *, reason: str) -> None:
        """Emit a non-silent recovery signal so a DB swap is observable (R5/R13).

        Surfaces as a per-session ``runtime_db_recreated`` event (never silent).
        The browser ignores unknown event types, so this is safe to broadcast;
        its value is the audit/metric trail proving the stall-recovery fired.
        """
        try:
            session = self._ensure_session(session_id)
            session.emit("runtime_db_recreated", reason=str(reason))
        except Exception:
            pass

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
            try:
                outputs = self._poll_session_outputs(manager, session_id, since_id)
            except _QueueCursorNotFound:
                # Non-silent recoverable signal (plan §2.4 / R5): the cursor id is
                # absent from the (recreated/swapped) runtime DB. Re-seed the
                # cursor ATOMICALLY from the runtime DB's current state — the
                # newest already-delivered out-row — then re-poll from there.
                # This avoids BOTH a silent permanent stall (0 rows forever) and
                # restarting from the top (which would re-deliver). If nothing
                # was delivered yet, the re-seed is None -> poll from the top is
                # correct (no client has seen the buffered output).
                reseeded = self._reseed_output_cursor(manager, session_id)
                if reseeded is None:
                    self._process_output_cursors.pop(session_id, None)
                else:
                    self._process_output_cursors[session_id] = reseeded
                self._emit_runtime_db_recovery(session_id, reason="cursor_reseeded")
                try:
                    outputs = self._poll_session_outputs(manager, session_id, reseeded)
                except _QueueCursorNotFound:
                    outputs = []
            # Highest out-row id pushed to each session's outbox this batch.
            # After the put succeeds we mark those rows delivered DURABLY in ONE
            # UPDATE per session (not per token), so reseed has a resume point and
            # cleanup can purge them (plan §2.4/§2.12 / R5/R22).
            delivered_up_to: dict[str, Any] = {}
            for msg in outputs:
                msg_session_id = str(msg.get("session_id") or session_id)
                session = self._ensure_session(msg_session_id)
                # SINGLE expansion point (plan §2.8 / Task 5): a coalesced
                # ``token_batch``/``reasoning_batch`` row carries N chunks; re-
                # expand it here into N ordered individual ``token``/``reasoning``
                # events so the browser (no ``*_batch`` subscriber exists) is
                # unchanged. Normal rows expand to a single event. Expansion runs
                # BEFORE the Task-4 delivery-marking below (which keys off the
                # ROW id, once per row) and preserves order. Per-row bookkeeping
                # (cursor advance, delivered_up_to) still happens once per row.
                events = self._expand_outbox_events(msg)
                for event in events:
                    self._deliver_outbox_event(session, msg_session_id, event)
                self._process_output_cursors[msg_session_id] = msg.get("id")
                if str(msg.get("direction") or "out") == "out":
                    delivered_up_to[msg_session_id] = msg.get("id")
                # NOTE: lifecycle-end tracking is set inside _deliver_outbox_event
                # via the shared flag below; we read it back here.
                if any(
                    e.get("type") in {"worker_exited", "worker_stopped"}
                    for e in events
                ):
                    saw_lifecycle_end = True
            # One durable delivery UPDATE per session for the whole batch.
            for marked_session_id, up_to_id in delivered_up_to.items():
                self._mark_outputs_delivered(manager, marked_session_id, up_to_id)
            if session_id in dead_sessions and not saw_lifecycle_end:
                session = self._ensure_session(session_id)
                if session.agent_alive or session.agent_running:
                    self._emit_process_dead(
                        session,
                        reason="process exited before producing worker_exited",
                    )
                else:
                    # Already-quiet dead worker (clean worker_exited seen on a
                    # prior poll): _emit_process_dead won't fire, so release the
                    # owner slot here too (Wave-3 H1). Guarded: no-op if the slot
                    # was already re-pointed at a newer session by a switch.
                    self._clear_owner_slot(session_id)

    @staticmethod
    def _expand_outbox_events(msg: dict[str, Any]) -> list[dict[str, Any]]:
        """Turn ONE queue out-row into the ordered list of browser events.

        Normal rows → exactly one event ``{**payload, "type": msg_type}``.
        Coalesced ``token_batch``/``reasoning_batch`` rows → one event per chunk
        (plan §2.8 / Task 5), preserving chunk order, so a re-expanded
        ``token_batch`` is byte-for-byte the same per-event shape the browser
        already consumes for un-coalesced ``token``/``reasoning`` rows.
        """
        msg_type = str(msg.get("msg_type") or "")
        payload = msg.get("payload")
        body = dict(payload) if isinstance(payload, dict) else {}
        if msg_type in ("token_batch", "reasoning_batch"):
            target = "token" if msg_type == "token_batch" else "reasoning"
            chunks = body.get("chunks")
            events: list[dict[str, Any]] = []
            for chunk in chunks or []:
                if not isinstance(chunk, dict):
                    continue
                event = dict(chunk)
                event["type"] = target
                # Carry any session_id stamped on the batch row onto each
                # expanded event so per-session routing below is unchanged.
                if "session_id" in body and "session_id" not in event:
                    event["session_id"] = body["session_id"]
                events.append(event)
            return events
        body["type"] = msg_type
        return [body]

    def _deliver_outbox_event(
        self,
        session: "_SessionBridge",
        msg_session_id: str,
        event: dict[str, Any],
    ) -> None:
        """Apply the per-event side effects and push it to the session outbox.

        Identical to the historical inline body; factored out so the batch
        expansion can feed N events through the SAME delivery path (lifecycle
        state, ask_user bookkeeping, session_id stamping, file_changed). The
        caller detects lifecycle-end by inspecting the expanded events, so this
        helper no longer owns the ``saw_lifecycle_end`` flag."""
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

    def _is_strict_single_active(self) -> bool:
        """True iff strict single-active-owner mode is in effect.

        Prefers the Task-2 policy object (``self._policy.is_strict``) when present;
        falls back to the legacy ``self._single_worker_per_owner`` constructor flag
        so this module is correct whether or not Task 2 has wired ``self._policy``
        yet. Defensive: any attribute/type error fails to the legacy flag.
        """
        policy = getattr(self, "_policy", None)
        if policy is not None:
            try:
                return bool(policy.is_strict)
            except Exception:
                pass
        return bool(self._single_worker_per_owner)

    def owner_slot_key(self, session_id: str | None) -> str:
        """Normalized OWNER SLOT for *session_id* (not the raw username).

        The slot is segment[0] of the normalized session id, which already carries
        the ``__<model_slug>`` suffix when ``ATLAS_SESSION_PER_MODEL`` is on,
        because ``_session_owner_with_model()`` (src/atlas_ui.py,
        src/atlas_api_sessions.py) is applied to the owner segment BEFORE the id
        reaches the bridge. We re-apply the SAME idempotent model-scoping here so
        the key is correct even if a caller hands us a bare owner; idempotency is
        guaranteed by ``_session_owner_with_model`` (no-op when the suffix is
        already present). The result is byte-identical to the keys
        ``_owner_active_sessions`` already uses via ``_owner_from_session_id``.
        """
        base = self._owner_from_session_id(session_id)
        return _owner_slot_with_model(base)

    def owner_active_session(self, owner: str | None) -> str:
        """Canonical session id currently holding *owner*'s slot, or "".

        ``owner`` may be a raw owner, an owner slot, or a full session id; it is
        reduced to the same slot key used for storage. Thin read alias kept next
        to ``active_session_for_owner`` (the historical name) so Task-3 call sites
        read consistently; both resolve through ``owner_slot_key``.
        """
        slot = self.owner_slot_key(owner)
        if not slot:
            return ""
        with self._sessions_lock:
            return str(self._owner_active_sessions.get(slot) or "")

    def _prepare_owner_slot_for_session(
        self, session_id: str | None, reason: str
    ) -> dict[str, Any]:
        """Make *session_id* the sole holder of its owner slot before warm/spawn.

        Returns a structured switch result so API responses can expose
        ``switch_status`` / ``previous_session`` / ``terminated_session`` without
        parsing emitted events (plan Task 3 "Return or store a structured switch
        result"). Possible ``switch_status`` values: ``noop`` (not strict, or slot
        already points here / nothing to displace), ``switched`` (old worker
        terminated and slot reserved for the incoming session), and
        ``termination_failed`` (old worker would not die — caller MUST NOT spawn a
        sibling; surface the error).

        Concurrency: the whole transition runs under ``_owner_slot_lock`` so two
        operations on the SAME owner slot serialize. ``_sessions_lock`` /
        ``_active_lock`` are taken only for the brief map reads/writes and are
        NEVER held across termination (Wave-3 F5). Unrelated owner slots make
        progress throughout (they take the same RLock but only the same-owner
        contender ever waits on the in-flight switch).
        """
        canonical = self._normalize_session_id(session_id)
        slot = self.owner_slot_key(canonical)
        result: dict[str, Any] = {
            "switch_status": "noop",
            "owner_slot": slot,
            "session_id": canonical,
            "previous_session": "",
            "terminated_session": "",
        }
        manager = self._process_manager
        # Thread-mode (no process manager): keep current behavior but still keep
        # the owner->active mapping coherent so status/activation read correctly.
        if manager is None:
            with self._sessions_lock:
                self._owner_active_sessions[slot] = canonical
            return result
        if not self._is_strict_single_active():
            # Session-scoped: do NOT displace siblings; just record the mapping.
            with self._sessions_lock:
                self._owner_active_sessions[slot] = canonical
            return result

        with self._owner_slot_lock:
            with self._sessions_lock:
                prev = str(self._owner_active_sessions.get(slot) or "")
            result["previous_session"] = prev
            # Slot already points at us AND the worker is the live one: idempotent.
            if prev == canonical:
                with self._sessions_lock:
                    self._owner_active_sessions[slot] = canonical
                return result
            # Find the live displaced worker for this slot. Prefer the recorded
            # prev; also defend against a stale map by scanning manager.list_active
            # for any same-slot id (covers a prev that died without clearing).
            displaced = ""
            if prev and prev != canonical and manager.is_alive(prev):
                displaced = prev
            else:
                for active_id in list(manager.list_active()):
                    if active_id == canonical:
                        continue
                    if self.owner_slot_key(active_id) == slot:
                        displaced = active_id
                        break
            if not displaced:
                # Nothing live to displace -> just (re)claim the slot. This is the
                # genuinely net-new path; capacity is the manager's job at spawn.
                with self._sessions_lock:
                    self._owner_active_sessions[slot] = canonical
                return result

            old_session = self._ensure_session(displaced)
            # 1) PRIVATE worker_switching on BOTH old and new (H12: never
            #    broadcast_all). old shows it is being replaced; new shows it is
            #    taking the slot.
            old_session.emit(
                "worker_switching",
                session_id=old_session.session_id,
                owner_slot=slot,
                to_session=canonical,
                reason=str(reason),
            )
            self._ensure_session(canonical).emit(
                "worker_switching",
                session_id=canonical,
                owner_slot=slot,
                from_session=old_session.session_id,
                reason=str(reason),
            )
            # 2) Terminate the old worker AND reserve the freed slot for the
            #    incoming session in ONE manager critical section (Wave-3 H2/H3:
            #    a same-owner-slot replacement is slot-preserving, must NEVER be
            #    cap-refused, and no other owner can steal the slot in the gap).
            #    No bridge lock is held across this call except _owner_slot_lock,
            #    which is per-owner-slot (F5). See Task-4 interface below.
            terminated_ok = self._terminate_and_reserve_slot(
                manager, old_session.session_id, canonical, reason
            )
            if not terminated_ok:
                # H/plan: do NOT silently spawn a sibling on failed termination.
                # Slot mapping is NOT advanced; surface a visible error + status.
                result["switch_status"] = "termination_failed"
                old_session.emit(
                    "error",
                    message=(
                        "could not terminate previous owner-slot worker; "
                        "refusing to start a sibling"
                    ),
                    session_id=old_session.session_id,
                )
                return result
            # 3) Old worker is gone: mark its session not-alive/not-running.
            old_session.agent_running = False
            old_session.agent_alive = False
            # 4) Final lifecycle for the old session: agent_state + worker_exited
            #    + done (all PRIVATE to the old session).
            old_session.emit("agent_state", running=False, alive=False)
            old_session.emit(
                "worker_exited",
                session_id=old_session.session_id,
                reason=f"owner_slot_switch:{reason}",
            )
            old_session.emit("done")
            # 5) Drain the old worker's FINAL out rows (worker_stopped/
            #    worker_exited/trailing tokens) and only THEN drop its output
            #    cursor (Wave-3 H5: flush before cursor pop, never pop right after
            #    kill). _poll_process_outputs reads/clears _process_output_cursors,
            #    so the final drain happens off this thread via the broadcaster;
            #    we pop AFTER asking for that final flush so no trailing row is
            #    orphaned. Done as a helper so the ordering is explicit.
            self._flush_then_drop_output_cursor(manager, old_session.session_id)
            # 6) Slot now belongs to the incoming session (the reservation in step
            #    2 already guards the manager counter; this records the bridge map).
            with self._sessions_lock:
                self._owner_active_sessions[slot] = canonical
            result["switch_status"] = "switched"
            result["terminated_session"] = old_session.session_id
            return result

    def _terminate_and_reserve_slot(
        self, manager: Any, old_session_id: str, new_session_id: str, reason: str
    ) -> bool:
        """Terminate *old_session_id* and reserve its freed slot for
        *new_session_id* atomically over the manager's admission counter.

        Wave-3 H2/H3 reserve-on-terminate. REQUIRED Task-4 interface (see
        depends_on): the process manager exposes a single primitive that, under
        its own counter lock, terminates the old worker and hands the freed slot
        to the incoming session so a same-owner replacement is never cap-refused
        and no other owner can take the slot in between. Preferred name:
        ``manager.terminate_and_reserve_slot(old_session_id, new_session_id,
        reason=..., stop_timeout_sec=..., kill_grace_sec=...) -> bool``.

        Fallback (only until Task 4 lands the combined primitive): call
        ``manager.terminate_session(old_session_id, reason=..., ...) -> bool``;
        the reservation degenerates to the existing behavior (acceptable for a
        same-owner switch because the freed slot is reclaimed before any net-new
        owner is admitted on this thread). Stop/kill timing comes from the policy
        (Task 2): ``self._policy.stop_ack_sec`` / ``self._policy.kill_grace_sec``
        when present, else conservative defaults.
        """
        policy = getattr(self, "_policy", None)
        stop_ack = float(getattr(policy, "stop_ack_sec", 3.0) or 0.0)
        kill_grace = float(getattr(policy, "kill_grace_sec", 5.0) or 0.0)
        combined = getattr(manager, "terminate_and_reserve_slot", None)
        if callable(combined):
            try:
                return bool(
                    combined(
                        old_session_id,
                        new_session_id,
                        reason=str(reason),
                        stop_timeout_sec=stop_ack,
                        kill_grace_sec=kill_grace,
                    )
                )
            except Exception:
                return False
        terminate = getattr(manager, "terminate_session", None)
        if callable(terminate):
            try:
                return bool(
                    terminate(
                        old_session_id,
                        reason=str(reason),
                        stop_timeout_sec=stop_ack,
                        kill_grace_sec=kill_grace,
                    )
                )
            except Exception:
                return False
        # Last-resort legacy path (pre-Task-4 managers / test fakes): hard kill.
        try:
            return bool(manager.kill(old_session_id))
        except Exception:
            return False

    def _flush_then_drop_output_cursor(self, manager: Any, session_id: str) -> None:
        """Drain a terminated worker's final out rows, THEN drop its cursor (H5).

        Pull any remaining out rows for *session_id* through the SAME delivery
        path the broadcaster uses (so worker_stopped/worker_exited/trailing
        tokens reach the client) and only after that remove the in-memory output
        cursor. Best-effort: a drain error must not strand the switch; the cursor
        is still dropped so a future spawn re-seeds cleanly.
        """
        try:
            since_id = self._process_output_cursors.get(session_id)
            outputs = self._poll_session_outputs(manager, session_id, since_id)
            delivered_up_to = None
            for msg in outputs:
                msg_session_id = str(msg.get("session_id") or session_id)
                session = self._ensure_session(msg_session_id)
                for event in self._expand_outbox_events(msg):
                    self._deliver_outbox_event(session, msg_session_id, event)
                self._process_output_cursors[msg_session_id] = msg.get("id")
                if str(msg.get("direction") or "out") == "out":
                    delivered_up_to = msg.get("id")
            if delivered_up_to:
                self._mark_outputs_delivered(manager, session_id, delivered_up_to)
        except Exception:
            pass
        finally:
            self._process_output_cursors.pop(session_id, None)

    def _clear_owner_slot(self, session_id: str | None) -> None:
        """Release *session_id*'s owner slot — ONLY if it still holds it.

        Idempotent and safe to call from any death/exit/delete/eviction site.
        Guard (Wave-3 H1): clear only when ``_owner_active_sessions[slot]`` still
        equals this canonical session, so a slot already re-pointed at a newer
        session by a concurrent switch is left intact.
        """
        canonical = self._normalize_session_id(session_id)
        slot = self.owner_slot_key(canonical)
        if not slot:
            return
        with self._sessions_lock:
            if self._owner_active_sessions.get(slot) == canonical:
                self._owner_active_sessions.pop(slot, None)

    def _spawn_process_session(
        self,
        session: "_SessionBridge",
        *,
        running: bool = False,
    ) -> bool:
        manager = self._process_manager
        if manager is None:
            return False
        # Owner-slot enforcement replaces the legacy spawn-time sibling kill
        # (_kill_owner_siblings_for_process_spawn). In strict mode this performs a
        # deterministic reserve-on-terminate switch (Wave-3 H2/H3) so no Alice
        # sibling process survives before this spawn returns; in session-scoped
        # mode it only records the owner->active mapping. It NEVER touches another
        # owner's worker. Callers that front-load the switch (warm_session /
        # activate_session / the prompt path) make this idempotent here.
        slot_result = self._prepare_owner_slot_for_session(
            session.session_id, reason="spawn"
        )
        if slot_result.get("switch_status") == "termination_failed":
            # Previous owner-slot worker would not terminate: refuse to start a
            # sibling (no handoff overlap). The error was already surfaced on the
            # old session by _prepare_owner_slot_for_session.
            return False
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

    def _resolve_worker_policy(self):
        """Return the active SessionWorkerPolicy (delegates to the public accessor).

        ``session_worker_policy()`` returns ``self._policy`` (wired in __init__)
        or derives one from the env, so this never needs its own fallback copy.
        Returns None only if policy resolution itself raises.
        """
        try:
            return self.session_worker_policy()
        except Exception:
            return None

    def _worker_idle_age_sec(self, manager: Any, session_id: str, now: float) -> float:
        """Best-effort idle age for a worker, in seconds.

        Prefers manager-supplied per-worker activity timestamps from Task 4's
        ``list_active_metadata`` (``last_output_at``/``last_input_at``/
        ``last_active_at``/``started_at``); falls back to the session bridge's
        ``last_active`` clock, which ``_deliver_outbox_event`` advances on every
        delivered out-event — so a truly idle warm worker's age grows.
        """
        meta_fn = getattr(manager, "list_active_metadata", None)
        if callable(meta_fn):
            try:
                for entry in meta_fn():
                    if str(entry.get("session_id") or "") != session_id:
                        continue
                    last = (
                        entry.get("last_output_at")
                        or entry.get("last_input_at")
                        or entry.get("last_active_at")
                        or entry.get("started_at")
                    )
                    if last:
                        return max(0.0, now - float(last))
            except Exception:
                pass
        session = self._ensure_session(session_id)
        return max(0.0, now - float(getattr(session, "last_active", now) or now))

    def _evict_idle_worker(self, manager: Any, session_id: str, *, idle_age: float) -> bool:
        """Terminate ONE idle warm worker and clear its owner slot (private).

        TOCTOU-safe: the caller snapshotted ``agent_running`` under
        ``_sessions_lock``; we re-confirm the process is still alive and NOT
        running here before killing so a prompt that started between scan and
        evict is never killed. Termination runs WITHOUT holding ``_sessions_lock``.
        """
        session = self._ensure_session(session_id)
        # Final guard: a prompt may have started since the scan snapshot.
        if bool(getattr(session, "agent_running", False)):
            return False
        if not manager.is_alive(session_id):
            return False
        # Graceful Task-4 terminator; H4 makes it skip the stop-ack wait for an
        # idle worker (no running turn) since we do not pass has_running_prompt.
        policy = self._resolve_worker_policy()
        try:
            manager.terminate_session(
                session_id,
                reason="idle_ttl",
                stop_timeout_sec=0.0,
                kill_grace_sec=(getattr(policy, "kill_grace_sec", 5.0) if policy else 5.0),
            )
        except Exception:
            return False
        # H5: drain any final out rows (worker_exited/tokens) BEFORE dropping the
        # output cursor.
        self._flush_then_drop_output_cursor(manager, session_id)
        session.agent_running = False
        session.agent_alive = False
        session.emit("agent_state", running=False, alive=False)
        # H12: PRIVATE eviction signal — emitted only on the evicted session.
        session.emit(
            "worker_evicted",
            session_id=session_id,
            reason="idle_ttl",
            idle_age_sec=round(float(idle_age), 3),
        )
        session.emit("done")
        # H1: clear the owner slot only if it still points at this session.
        self._clear_owner_slot(session_id)
        return True

    def reap_idle_session_workers(self, now: float | None = None) -> dict[str, Any]:
        """Reap idle warm interactive session workers (strict mode only).

        Runs OFF the asyncio broadcaster loop — the only caller is the
        ``next_event`` executor thread (Wave-3 C1), so a blocking graceful stop
        never stalls websocket fan-out.

        Reaps a worker iff ALL hold: policy is strict single-active-owner, the
        process is alive, its session ``agent_running`` is False (idle warm), and
        idle age > ``policy.idle_ttl_sec``. Returns ``{"reaped":[...],
        "scanned":int, "skipped_running":int}``; callers may ignore it.
        """
        result: dict[str, Any] = {"reaped": [], "scanned": 0, "skipped_running": 0}
        manager = self._process_manager
        if manager is None:
            return result
        policy = self._resolve_worker_policy()
        if policy is None or not getattr(policy, "is_strict", False):
            return result
        if not getattr(policy, "reaper_enabled", True):
            return result
        ttl = float(getattr(policy, "idle_ttl_sec", 0.0) or 0.0)
        # Snapshot candidates under the lock (cheap): alive + idle. Do NOT kill
        # under the lock (plan: never kill/sleep holding _sessions_lock).
        try:
            active = [str(s) for s in manager.list_active()]
        except Exception:
            active = []
        candidates: list[str] = []
        with self._sessions_lock:
            for session_id in active:
                result["scanned"] += 1
                session = self._sessions.get(session_id)
                if session is not None and bool(getattr(session, "agent_running", False)):
                    result["skipped_running"] += 1
                    continue
                candidates.append(session_id)
        wall = time.time() if now is None else float(now)
        for session_id in candidates:
            idle_age = self._worker_idle_age_sec(manager, session_id, wall)
            if ttl > 0 and idle_age <= ttl:
                continue
            if self._evict_idle_worker(manager, session_id, idle_age=idle_age):
                result["reaped"].append(session_id)
        return result

    def reap_idle_session_workers_throttled(self, now: float | None = None) -> bool:
        """Throttled wrapper called from the next_event executor thread.

        Returns True iff a reap pass actually ran. Rate-limited to once per
        ``policy.reaper_interval_sec`` using the monotonic ``_last_reap_at`` stamp
        so the executor thread can call it on every poll cheaply.
        """
        manager = self._process_manager
        if manager is None:
            return False
        policy = self._resolve_worker_policy()
        if policy is None or not getattr(policy, "is_strict", False):
            return False
        if not getattr(policy, "reaper_enabled", True):
            return False
        interval = float(getattr(policy, "reaper_interval_sec", 0.0) or 0.0)
        clock = time.monotonic()
        with self._sessions_lock:
            # _last_reap_at == 0.0 is the "never reaped" sentinel: always allow the
            # first pass regardless of the monotonic clock's magnitude (a fresh
            # boot/container can have monotonic() < interval).
            if interval > 0 and self._last_reap_at and (clock - self._last_reap_at) < interval:
                return False
            self._last_reap_at = clock
        self.reap_idle_session_workers(now=now)
        return True

    def _emit_process_dead(self, session: "_SessionBridge", *, reason: str) -> None:
        session.agent_running = False
        session.agent_alive = False
        # Owner-slot release on death (Wave-3 H1): clear only if this session
        # still holds its slot, so a slot already re-pointed at a newer session
        # by a concurrent switch is untouched. Both death sites converge here
        # (the _poll_process_outputs dead_sessions branch and the prompt-undelivered
        # branch in _send_process_input_for_session).
        self._clear_owner_slot(session.session_id)
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
        # Release the owner slot (H1) via the shared guarded helper so the
        # 'clear only if it still equals this session' rule is identical to every
        # other clear site and uses the model-scoped slot key. Replaces the prior
        # inline pop that keyed off the raw _owner_from_session_id segment.
        self._clear_owner_slot(session_id)
        if removed is None:
            return False
        removed.request_stop()
        with self._active_lock:
            if self._active_session_id == session_id:
                self._active_session_id = "default"
        return True

    def activate_session(self, session_id: str | None, *, warm: bool = False) -> None:
        session = self._ensure_session(session_id)
        # Strict single-active: claim the owner slot (terminating any sibling that
        # holds it) BEFORE flipping focus or warming, so activation is a clean
        # switch with no handoff overlap. In session-scoped mode this only records
        # the mapping (no displacement). Runs OUTSIDE _active_lock so termination
        # never blocks the focus lock (F5).
        slot_result = self._prepare_owner_slot_for_session(
            session.session_id, reason="activate"
        )
        if slot_result.get("switch_status") == "termination_failed":
            # Previous owner-slot worker would not terminate: do NOT advance focus
            # or warm a sibling; the slot stays with the previous session and the
            # error was already surfaced on it. (Skips _mark_owner_active so the
            # slot mapping is not wrongly advanced past the still-live old worker.)
            return
        with self._active_lock:
            self._active_session_id = session.session_id
        self._mark_owner_active(session.session_id)
        session.touch()
        if warm:
            self.warm_session(session.session_id)

    def warm_session(self, session_id: str | None = None) -> dict[str, Any]:
        session = self._ensure_session(session_id)
        if self._process_manager is not None:
            # Owner-slot switch BEFORE warmup so a warm never spawns a sibling for
            # an owner slot that another session still holds (plan Task 3:
            # 'Warmup cannot spawn a sibling after activation already switched the
            # owner slot'). Idempotent when activate already switched the slot.
            self._prepare_owner_slot_for_session(
                session.session_id, reason="warm"
            )
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
            # Owner-slot switch BEFORE the prompt-driven spawn so a prompt for a
            # session that is taking over an owner slot first terminates the old
            # holder (plan Task 3: prepare before _send_process_input_for_session
            # when spawn=True). Idempotent if activation already switched. NOTE:
            # capacity refusal (Wave-3 H6) is handled in Task 4/Task 6 BEFORE the
            # respawn-retry safety net and _emit_process_dead below; this Task-3
            # call only performs the same-owner switch and never cap-refuses a
            # same-owner replacement (reserve-on-terminate, H2/H3).
            self._prepare_owner_slot_for_session(
                session.session_id, reason=str(msg_type)
            )
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

    def session_worker_policy(self):
        """Return the resolved SessionWorkerPolicy (Task 2 wiring).

        Falls back to a lazily-derived policy from the legacy
        ``single_worker_per_owner`` flag when create_app() did not inject one, so
        this accessor is safe even before Task 2's ``policy=`` kwarg lands.
        """
        policy = getattr(self, "_policy", None)
        if policy is not None:
            return policy
        from core.session_worker_policy import SessionWorkerPolicy
        policy = SessionWorkerPolicy.from_env(
            single_worker_per_owner=bool(self._single_worker_per_owner)
        )
        self._policy = policy
        return policy

    def submit_prompt_result_for_session(
        self, session_id: str | None, text: str
    ) -> PromptDeliveryResult:
        """Prompt delivery that surfaces capacity_wait as a structured result.

        Mirrors the ``spawn()/spawn_result()`` split: ``submit_prompt_for_session``
        keeps its ``bool`` contract; this is the parallel surface the websocket ack
        path calls. In strict single-active mode an over-cap NET-NEW owner slot is
        refused with ``status="capacity_wait"`` BEFORE any Popen, BEFORE the
        ``_send_process_input_for_session`` respawn-retry safety net, and BEFORE
        ``_emit_process_dead`` (Wave-3 H6): no ``worker_exited``/``done`` is emitted
        on a capacity refusal, so the prompt is never marked dead.
        """
        session = self._ensure_session(session_id)
        owner_slot = self._owner_from_session_id(session.session_id)
        manager = self._process_manager
        # Thread mode keeps the historical always-deliver behavior.
        if manager is None:
            delivered = self.submit_prompt_for_session(session.session_id, text)
            return PromptDeliveryResult(
                ok=bool(delivered),
                status="delivered" if delivered else "not_delivered",
                reason="thread_mode",
                session_id=session.session_id,
                owner_slot=owner_slot,
                error="" if delivered else "input was not delivered to the agent worker",
            )
        # Strict-mode capacity admission for a genuinely net-new owner slot.
        # An already-live tracked process is ready and consumes no new slot, and a
        # same-owner-slot replacement reserves the freed slot (H2/H3) — both are
        # handled by _prepare_owner_slot_for_session + spawn_result, so we only
        # refuse here when admission for a NET-NEW slot is over the cap.
        policy = self.session_worker_policy()
        if policy.is_strict and not manager.is_alive(session.session_id):
            try:
                self._prepare_owner_slot_for_session(
                    session.session_id, reason="prompt"
                )
            except Exception:
                pass
            spawn_result = None
            try:
                spawn_result = manager.spawn_result(
                    session.session_id, policy=policy
                )
            except AttributeError:
                spawn_result = None
            if spawn_result is not None and getattr(
                spawn_result, "status", ""
            ) == "capacity_wait":
                # H6: short-circuit. Do NOT enter _send_process_input_for_session
                # (no respawn retry) and do NOT _emit_process_dead.
                session.touch()
                return PromptDeliveryResult(
                    ok=False,
                    status="capacity_wait",
                    reason=getattr(spawn_result, "reason", "max_active"),
                    session_id=session.session_id,
                    owner_slot=owner_slot,
                    spawn_result=spawn_result,
                    error="capacity_wait",
                )
        # Normal path: reuse the bool delivery (spawn=True), which now finds the
        # worker already admitted/spawned above in the strict net-new case.
        delivered = self._send_process_input_for_session(
            session.session_id, "prompt", {"text": text}, spawn=True
        )
        return PromptDeliveryResult(
            ok=bool(delivered),
            status="delivered" if delivered else "not_delivered",
            reason="" if delivered else "send_failed",
            session_id=session.session_id,
            owner_slot=owner_slot,
            error="" if delivered else "input was not delivered to the agent worker",
        )

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
        # Release the owner slot if this session still holds it (H1). Safe in
        # both process and thread mode; no-op if a concurrent switch already
        # re-pointed the slot at a newer session.
        self._clear_owner_slot(session.session_id)
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
                    # Wave-3 C1: run the idle reaper here, on the next_event
                    # EXECUTOR thread (off the asyncio broadcaster loop), so a
                    # blocking graceful stop never stalls websocket fan-out.
                    # Self-throttled to <= once per reaper_interval_sec and a
                    # no-op outside strict single-active mode.
                    try:
                        self.reap_idle_session_workers_throttled()
                    except Exception:
                        pass
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
