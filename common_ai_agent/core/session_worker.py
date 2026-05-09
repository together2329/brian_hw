"""SQLite-backed Atlas worker entry point.

This module runs the existing Atlas agent loop from ``src/main.py`` in a
subprocess-friendly worker mode. Instead of reading from stdin or emitting to a
TUI/WebSocket bridge directly, all input and output flows through the
``session_queue`` table managed by :class:`core.atlas_db.AtlasDB`.

The worker mirrors the callback wiring used by ``src/textual_main.py``: import
``main`` as ``_agent``, assign the ``_textual_*`` callback globals, then call
``_agent.chat_loop()``. A parent process can drive the worker by enqueueing
``direction='in'`` messages and consuming ``direction='out'`` messages.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import signal
import sys
import time
import uuid
from pathlib import Path
from typing import Any, Iterable


# ── Path setup ──────────────────────────────────────────────────────────────
try:
    _script_dir = os.path.dirname(os.path.abspath(__file__))
except (OSError, FileNotFoundError):
    _script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
_project_root = os.path.dirname(_script_dir)
_src_dir = os.path.join(_project_root, "src")

sys.path.insert(0, _src_dir)
sys.path.insert(0, _project_root)

from core.atlas_db import AtlasDB  # noqa: E402

_agent: Any = importlib.import_module("main")


DEFAULT_DB_PATH = "~/.common_ai_agent/atlas.db"
POLL_INTERVAL = 0.05
ASK_USER_TIMEOUT = 900.0

_shutdown_requested = False


def _json_payload(payload: Any) -> str:
    """Serialize queue payloads consistently for AtlasDB."""

    return json.dumps(payload, ensure_ascii=False)


def _decode_payload(raw: Any) -> Any:
    """Return a decoded payload from AtlasDB rows, tolerating plain strings."""

    if raw is None:
        return {}
    if isinstance(raw, (dict, list)):
        return raw
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", errors="replace")
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw
    return raw


def _message_id(msg: dict[str, Any]) -> str | None:
    """Extract a queue message id across likely AtlasDB row shapes."""

    for key in ("id", "msg_id", "message_id"):
        val = msg.get(key)
        if val is not None:
            return str(val)
    return None


def _message_type(msg: dict[str, Any]) -> str:
    return str(msg.get("msg_type") or msg.get("type") or "")


def _message_text(msg: dict[str, Any]) -> str:
    payload = _decode_payload(msg.get("payload"))
    if isinstance(payload, dict):
        for key in ("text", "prompt", "answer", "value", "content"):
            if key in payload and payload[key] is not None:
                return str(payload[key])
        return json.dumps(payload, ensure_ascii=False)
    if payload is None:
        return ""
    return str(payload)


class SessionWorker:
    """Bridge ``main.chat_loop`` callbacks to the SQLite session queue."""

    def __init__(self, session_id: str, db_path: str) -> None:
        self.session_id = session_id
        self.db = AtlasDB(os.path.expanduser(db_path))
        self.db.init_db()
        self._agent_running = False
        self._closed_ask_flows: set[str] = set()

    def emit(self, msg_type: str, payload: Any | None = None) -> str:
        return self.db.enqueue_message(
            self.session_id,
            "out",
            msg_type,
            _json_payload({} if payload is None else payload),
        )

    def acknowledge(self, msg: dict[str, Any]) -> None:
        msg_id = _message_id(msg)
        if msg_id is not None:
            self.db.acknowledge_message(msg_id)

    def poll_matching(self, msg_types: Iterable[str]) -> dict[str, Any] | None:
        wanted = set(msg_types)
        msgs = self.db.poll_messages(self.session_id, "in", since_id=None, limit=100)
        for msg in msgs or []:
            if _message_type(msg) in wanted:
                self.acknowledge(msg)
                return msg
        return None

    def wait_matching(
        self,
        msg_types: Iterable[str],
        *,
        timeout: float | None = None,
        flow_id: str | None = None,
    ) -> dict[str, Any] | None:
        deadline = None if timeout is None else time.monotonic() + timeout
        wanted = set(msg_types)
        while not _shutdown_requested:
            msgs = self.db.poll_messages(self.session_id, "in", since_id=None, limit=100)
            for msg in msgs or []:
                msg_type = _message_type(msg)
                if msg_type not in wanted:
                    continue
                payload = _decode_payload(msg.get("payload"))
                if flow_id and isinstance(payload, dict) and payload.get("flow_id") not in (None, flow_id):
                    continue
                self.acknowledge(msg)
                return msg
            if deadline is not None and time.monotonic() >= deadline:
                return None
            time.sleep(POLL_INTERVAL)
        raise KeyboardInterrupt

    def input(self, prompt: str = "") -> str:
        if prompt:
            self.emit("input_prompt", {"text": prompt})
        msg = self.wait_matching(("prompt", "interrupt"), timeout=None)
        if msg is None:
            raise KeyboardInterrupt
        return _message_text(msg)

    def emit_content(self, text: str, cls: str = "") -> None:
        payload: dict[str, Any] = {"text": text}
        if cls:
            payload["cls"] = cls
        self.emit("content", payload)

    def emit_reasoning(self, text: str, blank: bool = False) -> None:
        self.emit("reasoning", {"text": text, "blank": bool(blank)})

    def emit_todo(self, text: str) -> None:
        self.emit("todo", {"text": text})

    def emit_flush(self) -> None:
        self.emit("flush", {})

    def emit_token_usage(self, in_tok: int, cache_tok: int, out_tok: int) -> None:
        self.emit(
            "token_usage",
            {"input": in_tok, "cached": cache_tok, "output": out_tok},
        )

    def check_stop(self) -> bool:
        msg = self.poll_matching(("stop",))
        return msg is not None

    def poll_interrupt(self) -> str | None:
        msg = self.poll_matching(("interrupt",))
        if msg is None:
            return None
        return _message_text(msg)

    def set_agent_running(self, value: bool) -> None:
        self._agent_running = bool(value)
        self.emit("agent_state", {"running": self._agent_running})

    def ask_user(
        self,
        question: str,
        options: list[dict[str, Any]] | None,
        kind: str,
        subtitle: str,
        questions: list[dict[str, Any]] | None = None,
    ) -> str:
        flow_id = "qa_" + uuid.uuid4().hex[:10]
        payload: dict[str, Any] = {"flow_id": flow_id}
        if questions:
            payload["questions"] = questions
        else:
            payload.update({
                "question": question,
                "kind": kind,
                "subtitle": subtitle or "",
                "options": options or [],
            })

        self.emit("ask_user", payload)
        msg = self.wait_matching(("answer", "ask_user_closed"), timeout=ASK_USER_TIMEOUT, flow_id=flow_id)
        if msg is None:
            self.emit("ask_user_closed", {"flow_id": flow_id, "reason": "timeout"})
            return "[ask_user: no answer received within 15 min]"

        payload = _decode_payload(msg.get("payload"))
        if _message_type(msg) == "ask_user_closed":
            self._closed_ask_flows.add(flow_id)
            return "User declined to answer questions"
        if isinstance(payload, dict) and payload.get("type") == "cancel":
            self.emit("ask_user_closed", {"flow_id": flow_id, "reason": "cancel"})
            return "User declined to answer questions"

        self.emit("ask_user_answered", {"flow_id": flow_id})
        self.emit("ask_user_closed", {"flow_id": flow_id})
        return self.format_answer(payload, options or [], questions)

    @staticmethod
    def format_answer(
        answer: Any,
        options: list[dict[str, Any]],
        questions: list[dict[str, Any]] | None = None,
    ) -> str:
        if isinstance(answer, str):
            return answer
        if not isinstance(answer, dict):
            return str(answer)
        if "answer" in answer and answer["answer"] is not None:
            return str(answer["answer"])
        if "text" in answer and answer["text"] is not None:
            return str(answer["text"])
        if questions and "answers" in answer:
            blocks = []
            for question, item in zip(questions, answer.get("answers") or []):
                label = str(question.get("subtitle") or question.get("question") or "")[:40]
                blocks.append(f"  • {label}\n    {SessionWorker.format_answer(item, question.get('options') or [])}")
            return "Batched answers:\n" + "\n".join(blocks) if blocks else "(no answers)"

        selected = answer.get("selected") or []
        custom = str(answer.get("custom") or "").strip()
        label_by_id = {opt.get("id"): opt.get("label", opt.get("id")) for opt in options}
        labels = [str(label_by_id.get(item, item)) for item in selected]
        parts = []
        if labels:
            parts.append("selected: " + ", ".join(labels))
        if custom:
            parts.append("note: " + custom)
        return " · ".join(parts) if parts else "(user submitted with no selection)"

    def close(self) -> None:
        close = getattr(self.db, "close", None)
        if callable(close):
            close()


def _install_signal_handlers() -> None:
    def _handle_signal(signum: int, _frame: Any) -> None:
        global _shutdown_requested
        _shutdown_requested = True
        raise KeyboardInterrupt(f"received signal {signum}")

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)


def run_worker(session_id: str, db_path: str) -> int:
    worker = SessionWorker(session_id=session_id, db_path=db_path)
    _install_signal_handlers()

    _agent._textual_input_fn = worker.input
    _agent._textual_emit_content_fn = worker.emit_content
    _agent._textual_emit_reasoning_fn = worker.emit_reasoning
    _agent._textual_emit_todo_fn = worker.emit_todo
    _agent._textual_emit_flush_fn = worker.emit_flush
    _agent._textual_emit_token_fn = worker.emit_token_usage
    _agent._textual_esc_check_fn = worker.check_stop
    _agent._textual_poll_human_input_fn = worker.poll_interrupt
    _agent._textual_set_agent_running_fn = worker.set_agent_running

    try:
        from core import tools as _tools

        if hasattr(_tools, "set_ask_user_callback"):
            _tools.set_ask_user_callback(worker.ask_user)
    except Exception as exc:
        worker.emit("error", {"message": f"ask_user callback registration failed: {exc}"})

    try:
        worker.emit("worker_started", {"pid": os.getpid()})
        _agent.chat_loop()
        return 0
    except KeyboardInterrupt:
        worker.emit("worker_stopped", {"reason": "signal"})
        return 0
    except Exception as exc:
        worker.emit("error", {"message": str(exc), "type": type(exc).__name__})
        raise
    finally:
        worker.set_agent_running(False)
        worker.emit("worker_exited", {})
        worker.close()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Atlas agent loop as a SQLite queue worker.")
    parser.add_argument("--session-id", required=True, help="Atlas session id to bind to.")
    parser.add_argument(
        "--db-path",
        default=DEFAULT_DB_PATH,
        help=f"Path to Atlas SQLite DB (default: {DEFAULT_DB_PATH}).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    db_path = str(Path(os.path.expanduser(args.db_path)))
    return run_worker(args.session_id, db_path)


if __name__ == "__main__":
    raise SystemExit(main())
