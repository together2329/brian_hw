"""SQLite-backed Atlas worker entry point.

This module runs the existing Atlas agent loop from ``src/main.py`` in a
subprocess-friendly worker mode. Instead of reading from stdin or emitting to a
TUI/WebSocket bridge directly, all input and output flows through the
``session_queue`` table managed by :class:`core.atlas_db.AtlasDB`.

The worker mirrors the callback wiring used by ``src/textual_main.py``: bind
the session/workflow environment first, import ``main`` as ``_agent``, assign
the ``_textual_*`` callback globals, then call ``_agent.chat_loop()``. A parent
process can drive the worker by enqueueing ``direction='in'`` messages and
consuming ``direction='out'`` messages.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import re
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

_agent: Any = None


DEFAULT_DB_PATH = os.environ.get("ATLAS_DB_PATH") or "~/.common_ai_agent/atlas.db"
POLL_INTERVAL = 0.05
ASK_USER_TIMEOUT = 900.0

_shutdown_requested = False


def _load_agent() -> Any:
    """Import the main agent after the worker session/workflow env is bound."""

    global _agent
    if _agent is None:
        _agent = importlib.import_module("main")
    return _agent


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


def _runtime_db_mode() -> bool:
    """True when this worker is running against a per-session RUNTIME db.

    The manager binds the worker's queue DB via ``--db-path`` and, in session
    mode (plan §2.1/§2.9), that file is the per-session runtime ``.db`` — which
    must materialize ONLY the 5-table IPC/trace subset, NOT the ~24 control
    tables. The signals ``build_worker_env`` sets:

    * ``ATLAS_RUNTIME_DB_MODE=session`` — the explicit mode flag (authoritative),
      OR
    * ``ATLAS_RUNTIME_DB_PATH`` DIFFERS from ``ATLAS_CONTROL_DB_PATH`` — the true
      shape signal. CRITICAL: ``build_worker_env`` sets ``ATLAS_RUNTIME_DB_PATH``
      in BOTH modes; in CENTRAL mode it EQUALS the control path. So a non-empty
      ``ATLAS_RUNTIME_DB_PATH`` alone does NOT imply session mode — opening the
      CONTROL DB with the runtime 5-table subset would be wrong (the control DB
      needs the full schema). We therefore require the runtime path to be
      DISTINCT from the control path.

    Defaulting to the FULL schema when neither holds keeps the historical
    single-DB (central) behavior byte-identical.
    """
    mode = str(os.environ.get("ATLAS_RUNTIME_DB_MODE") or "").strip().lower()
    if mode == "session":
        return True
    runtime_path = str(os.environ.get("ATLAS_RUNTIME_DB_PATH") or "").strip()
    control_path = str(os.environ.get("ATLAS_CONTROL_DB_PATH") or "").strip()
    if not runtime_path:
        return False
    # Runtime distinct from control => sharded per-session file => runtime subset.
    return bool(control_path) and not _same_path(runtime_path, control_path)


def _same_path(left: str, right: str) -> bool:
    try:
        from pathlib import Path as _Path

        return (
            _Path(os.path.expanduser(left)).resolve()
            == _Path(os.path.expanduser(right)).resolve()
        )
    except Exception:
        return left == right


def _worker_schema_set() -> str:
    return "runtime" if _runtime_db_mode() else "full"


class SessionWorker:
    """Bridge ``main.chat_loop`` callbacks to the SQLite session queue."""

    def __init__(self, session_id: str, db_path: str) -> None:
        self.session_id = session_id
        # In session mode the worker's queue DB IS the per-session runtime file;
        # open it with the runtime-only 5-table schema so it does not bootstrap
        # ~24 unused control tables (defeats plan §2.9). In central mode this
        # stays the FULL schema == today's single-DB behavior. The worker still
        # reads/writes session_queue, messages, trace_events and llm_calls —
        # every one of those tables is in the runtime subset (RUNTIME_SCHEMA_SQL).
        self._schema_set = _worker_schema_set()
        self.db = AtlasDB(os.path.expanduser(db_path), schema_set=self._schema_set)
        self.db.init_db()
        self._agent_running = False
        self._closed_ask_flows: set[str] = set()

    @staticmethod
    def _normalize_session(value: str | None) -> str:
        clean = str(value or "").strip().strip("/")
        clean = re.sub(r"/+", "/", clean)
        clean = re.sub(r"[^A-Za-z0-9_.\-/]+", "_", clean)
        return clean or "default"

    @staticmethod
    def _valid_ip_name(value: str | None) -> bool:
        return bool(re.match(r"^[A-Za-z][A-Za-z0-9_]*$", str(value or "")))

    @staticmethod
    def _qa_slug(value: str, fallback: str) -> str:
        slug = re.sub(r"[^a-z0-9_]+", "_", str(value or "").strip().lower())
        slug = re.sub(r"_+", "_", slug).strip("_")
        return (slug[:72] or fallback)

    @staticmethod
    def _status_group(status: str) -> str:
        return "approved" if str(status or "").lower() in {"approved", "answered", "resolved"} else "pending"

    @staticmethod
    def _ssot_qa_section(decision_key: str) -> tuple[str, str]:
        sections = {
            "purpose": ("00_overview", "0. Overview / Intent"),
            "parameters": ("01_parameters", "1. Parameters"),
            "clock_reset": ("02_clock_reset", "2. Clock / Reset"),
            "bus_interface": ("03_interface", "3. Interface"),
            "submodule_structure": ("04_architecture", "4. Architecture / Decomposition"),
            "memory_map": ("05_memory", "5. Memory / Buffering"),
            "register_map": ("06_registers", "6. Register Map"),
            "interrupt": ("07_interrupt_error", "7. Interrupt / Error Policy"),
            "test_expectation": ("18_verification", "18. Verification / Gates"),
        }
        return sections.get(decision_key, ("99_other", "99. Other / Open Decisions"))

    def _project_root(self) -> Path:
        return Path(os.environ.get("ATLAS_PROJECT_ROOT") or os.getcwd()).resolve()

    def _ssot_context(self, ip: str | None = None, session: str | None = None) -> tuple[str, str]:
        raw_session = self._normalize_session(session or self.session_id)
        parts = [p for p in raw_session.split("/") if p]
        if ip and self._valid_ip_name(ip):
            owner = parts[0] if parts else os.environ.get("ATLAS_DEFAULT_SESSION_ID", "default")
            if len(parts) >= 3 and parts[-2] == ip and parts[-1] == "ssot-gen":
                return ip, raw_session
            return ip, self._normalize_session(f"{owner}/{ip}/ssot-gen")
        if len(parts) >= 3 and parts[-1] == "ssot-gen" and self._valid_ip_name(parts[-2]):
            return parts[-2], raw_session
        env_ip = os.environ.get("ATLAS_ACTIVE_IP", "")
        env_wf = os.environ.get("ACTIVE_WORKSPACE") or os.environ.get("ATLAS_DEFAULT_WORKFLOW", "")
        if self._valid_ip_name(env_ip) and env_wf == "ssot-gen":
            owner = parts[0] if parts else os.environ.get("ATLAS_DEFAULT_SESSION_ID", "default")
            return env_ip, self._normalize_session(f"{owner}/{env_ip}/ssot-gen")
        return "", ""

    def _ssot_qa_path(self, ip: str, session: str) -> Path:
        clean = self._normalize_session(session)
        parts = [p for p in clean.split("/") if p]
        if len(parts) >= 3 and parts[-2] == ip and parts[-1] == "ssot-gen":
            return self._project_root() / ".session" / clean / "qa.json"
        owner = parts[0] if parts else "default"
        return self._project_root() / ".session" / owner / ip / "ssot-gen" / "qa.json"

    def _load_ssot_qa_items(self, ip: str, session: str) -> list[dict[str, Any]]:
        path = self._ssot_qa_path(ip, session)
        if not path.is_file():
            return []
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return []
        items = raw.get("items") if isinstance(raw, dict) else raw
        return [dict(item) for item in items or [] if isinstance(item, dict)]

    def _save_ssot_qa_items(self, ip: str, session: str, items: list[dict[str, Any]]) -> None:
        path = self._ssot_qa_path(ip, session)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({
            "ip": ip,
            "workflow": "ssot-gen",
            "updated_at": time.time(),
            "items": items,
        }, ensure_ascii=False, indent=2), encoding="utf-8")

    def _ssot_q_pairs_from_questions(
        self,
        questions: list[dict[str, Any]] | None,
    ) -> list[tuple[str, str, dict[str, Any]]]:
        pairs: list[tuple[str, str, dict[str, Any]]] = []
        for idx, raw in enumerate(questions or []):
            if not isinstance(raw, dict):
                continue
            question = dict(raw)
            key_src = (
                question.get("decision_key")
                or question.get("id")
                or question.get("field_path")
                or question.get("section_id")
                or question.get("question")
            )
            key = self._qa_slug(str(key_src or ""), f"qa_{idx + 1}")
            label = str(
                question.get("decision_label")
                or question.get("field_path")
                or question.get("subtitle")
                or question.get("question")
                or key
            ).strip()
            pairs.append((key, label[:240] or key, question))
        return pairs

    @staticmethod
    def _answer_text(answer: dict[str, Any], question: dict[str, Any]) -> str:
        custom = str(answer.get("custom") or "").strip()
        if custom:
            return custom
        selected = answer.get("selected") or []
        by_id = {
            str(opt.get("id")): str(opt.get("label") or opt.get("id"))
            for opt in (question.get("options") or [])
            if isinstance(opt, dict)
        }
        labels = [by_id.get(str(item), str(item)) for item in selected]
        return ", ".join([label for label in labels if label]).strip()

    def _upsert_ssot_qa_items(
        self,
        ip: str,
        session: str,
        *,
        flow_id: str,
        kind: str,
        q_pairs: list[tuple[str, str, dict[str, Any]]],
        status: str,
        answers: dict[str, dict[str, Any]] | None = None,
        source: str = "ssot-qna",
    ) -> None:
        items = self._load_ssot_qa_items(ip, session)
        index = {
            (str(item.get("flow_id") or ""), str(item.get("decision_key") or "")): idx
            for idx, item in enumerate(items)
        }
        now = time.time()
        answers = answers or {}
        for order, (key, label, question) in enumerate(q_pairs):
            default_section_id, default_section_title = self._ssot_qa_section(key)
            answer = answers.get(key) if isinstance(answers.get(key), dict) else {}
            answer_text = str(answer.get("answer") or "").strip()
            existing_idx = index.get((flow_id, key))
            prior = items[existing_idx] if existing_idx is not None else {}
            prior_answer_text = str(prior.get("answer") or "").strip()
            item_status = "approved" if answer_text or prior_answer_text else status
            item = {
                **prior,
                "ip": ip,
                "workflow": "ssot-gen",
                "kind": kind or "general IP",
                "flow_id": flow_id,
                "source": source or "ssot-qna",
                "section_id": str(question.get("section_id") or question.get("section") or default_section_id).strip(),
                "section_title": str(
                    question.get("section_title")
                    or question.get("section_name")
                    or question.get("section")
                    or default_section_title
                ).strip(),
                "decision_key": key,
                "decision_label": label,
                "question": str(question.get("question") or ""),
                "subtitle": str(question.get("subtitle") or ""),
                "question_kind": str(question.get("kind") or "single"),
                "options": question.get("options") or [],
                "qa_type": str(question.get("qa_type") or question.get("type") or "human_decision"),
                "content": question.get("content") or "",
                "detail": question.get("detail") or "",
                "criteria": question.get("criteria") or [],
                "source_refs": question.get("source_refs") or question.get("sources") or [],
                "field_path": question.get("field_path") or "",
                "order": order,
                "status": item_status,
                "status_group": self._status_group(item_status),
                "answer": answer_text or str(prior.get("answer") or ""),
                "selected": answer.get("selected") or prior.get("selected") or [],
                "custom": answer.get("custom") or prior.get("custom") or "",
                "updated_at": now,
                "created_at": prior.get("created_at") or now,
            }
            if existing_idx is None:
                items.append(item)
            else:
                items[existing_idx] = item
        self._save_ssot_qa_items(ip, session, items)

    def _emit_ssot_qa_updated(self, ip: str, session: str, flow_id: str) -> None:
        self.emit("ssot_qa_updated", {
            "ip": ip,
            "workflow": "ssot-gen",
            "flow_id": flow_id,
            "session": session,
        })

    def record_ssot_qa(
        self,
        questions: list[dict[str, Any]] | None = None,
        ip: str | None = None,
        session: str | None = None,
        kind: str = "",
        source: str = "llm-ssot-qna",
        status: str = "pending",
    ) -> str:
        target_ip, target_session = self._ssot_context(ip=ip, session=session)
        if not target_ip:
            return "[record_ssot_qa: no active valid SSOT IP]"
        q_pairs = self._ssot_q_pairs_from_questions(questions or [])
        if not q_pairs:
            return "[record_ssot_qa: no valid QA items to record]"
        flow_id = "qa_backlog_" + uuid.uuid4().hex[:10]
        self._upsert_ssot_qa_items(
            target_ip,
            target_session,
            flow_id=flow_id,
            kind=kind or "general IP",
            q_pairs=q_pairs,
            status=status or "pending",
            source=source,
        )
        self._emit_ssot_qa_updated(target_ip, target_session, flow_id)
        return (
            f"[record_ssot_qa] recorded {len(q_pairs)} "
            f"{self._status_group(status or 'pending')} SSOT QA item(s) "
            f"for {target_session}"
        )

    def emit(self, msg_type: str, payload: Any | None = None) -> str:
        return self.db.enqueue_message(
            self.session_id,
            "out",
            msg_type,
            {} if payload is None else payload,
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

    def drain_idle_stops(self) -> int:
        """Discard STOP messages that arrived while no turn was running.

        A STOP is only meaningful for the currently executing turn. If the
        user hits stop while the worker is idle, leaving that queue item around
        causes the next prompt to start, immediately consume the stale STOP via
        ``check_stop()``, and end with no visible assistant response.
        """

        drained = 0
        while True:
            found_stop = False
            for msg in self.db.poll_messages(self.session_id, "in", since_id=None, limit=100) or []:
                if _message_type(msg) != "stop":
                    continue
                self.acknowledge(msg)
                drained += 1
                found_stop = True
            if not found_stop:
                return drained

    def input(self, prompt: str = "") -> str:
        if prompt:
            self.emit("input_prompt", {"text": prompt})
        self.drain_idle_stops()
        msg = self.wait_matching(("prompt", "interrupt"), timeout=None)
        if msg is None:
            raise KeyboardInterrupt
        return _message_text(msg)

    def emit_content(self, text: str, cls: str = "") -> None:
        payload: dict[str, Any] = {"text": text}
        if cls:
            payload["cls"] = cls
        self.emit("token", payload)

    def emit_reasoning(self, text: str, blank: bool = False) -> None:
        self.emit("reasoning", {"text": text, "blank": bool(blank)})

    def emit_todo(self, text: str) -> None:
        self.emit("todo", {"text": text})

    def emit_flush(self) -> None:
        self.emit("flush", {})

    def emit_context(self, tokens: int, max_tok: int, **runtime: Any) -> None:
        payload: dict[str, Any] = {
            "session_id": self.session_id,
            "used": int(tokens or 0),
            "max": int(max_tok or 0),
        }
        model = str(runtime.get("model") or self._active_model_name()).strip()
        effort = str(
            runtime.get("reasoning_effort")
            or runtime.get("effort")
            or self._active_reasoning_effort()
        ).strip()
        if model:
            payload["model"] = model
        if effort:
            payload["reasoning_effort"] = effort
        self.emit("context", payload)

    def _active_model_name(self) -> str:
        try:
            import config as _cfg  # type: ignore
            model = str(getattr(_cfg, "MODEL_NAME", "") or "").strip()
            if model:
                return model
        except Exception:
            pass
        return (
            os.environ.get("LLM_ACTIVE_MODEL_NAME", "").strip()
            or os.environ.get("MODEL_NAME", "").strip()
            or os.environ.get("LLM_MODEL_NAME", "").strip()
            or os.environ.get("LLM_ACTIVE_BASE_NAME", "").strip()
            or os.environ.get("LLM_BASE_NAME", "").strip()
        )

    def _active_reasoning_effort(self) -> str:
        try:
            import config as _cfg  # type: ignore
            effort = str(
                getattr(_cfg, "REASONING_EFFORT", "")
                or getattr(_cfg, "REASONING_MODE", "")
            ).strip()
            if effort:
                return effort
        except Exception:
            pass
        return (
            os.environ.get("REASONING_EFFORT", "").strip()
            or os.environ.get("REASONING_MODE", "").strip()
            or os.environ.get("ATLAS_REASONING_EFFORT", "").strip()
        )

    def _persist_cost_ledger(
        self,
        *,
        in_tok: int,
        cache_tok: int,
        out_tok: int,
        cost_usd_delta: float,
        model: str,
    ) -> None:
        session = self._normalize_session(self.session_id)
        if not session:
            return
        try:
            root = Path(os.environ.get("ATLAS_PROJECT_ROOT") or os.getcwd()).resolve()
            cost_path = root / ".session" / session / "cost.json"
            cost_path.parent.mkdir(parents=True, exist_ok=True)
            existing: dict[str, Any] = {}
            if cost_path.exists():
                try:
                    existing = json.loads(cost_path.read_text(encoding="utf-8", errors="replace"))
                except Exception:
                    existing = {}
            cumulative_in = int(existing.get("in_tok", 0) or 0) + int(in_tok or 0)
            cumulative_cache = int(existing.get("cache_tok", 0) or 0) + int(cache_tok or 0)
            cumulative_out = int(existing.get("out_tok", 0) or 0) + int(out_tok or 0)
            cumulative_cost = float(existing.get("cost_usd", 0) or 0) + float(cost_usd_delta or 0)
            cost_path.write_text(
                json.dumps({
                    "in_tok": cumulative_in,
                    "cache_tok": cumulative_cache,
                    "out_tok": cumulative_out,
                    "sum_tok": cumulative_in + cumulative_out,
                    "cost_usd": cumulative_cost,
                    "last_in_tok": int(in_tok or 0),
                    "last_cache_tok": int(cache_tok or 0),
                    "last_out_tok": int(out_tok or 0),
                    "last_at": time.time(),
                    "model": model,
                    "updated_at": time.time(),
                }, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception:
            pass

    def emit_tool(self, text: str) -> None:
        self.emit("tool", {"text": str(text or "")})

    def emit_tool_result(self, obs: str, tool: str = "") -> None:
        text = str(obs or "")
        try:
            max_chars = int(os.environ.get("WS_TOOL_RESULT_MAX_CHARS", "128000") or 128000)
        except Exception:
            max_chars = 128000
        self.emit(
            "tool_result",
            {
                "text": text[:max_chars],
                "tool": str(tool or ""),
                "truncated": len(text) > max_chars,
            },
        )

    def emit_token_usage(self, in_tok: int, cache_tok: int, out_tok: int) -> None:
        model = self._active_model_name()
        pricing_payload = None
        cost_delta = 0.0
        try:
            from lib.model_pricing import get_active_pricing
            price = get_active_pricing(model)
        except Exception:
            price = None
        if price is not None:
            billable_in = max(0, int(in_tok or 0) - int(cache_tok or 0))
            cost_delta = (
                billable_in * float(price.input)
                + int(cache_tok or 0) * float(price.cache)
                + int(out_tok or 0) * float(price.output)
            ) / 1_000_000.0
            pricing_payload = {
                "input": float(price.input),
                "cache": float(price.cache),
                "output": float(price.output),
            }
        self._persist_cost_ledger(
            in_tok=int(in_tok or 0),
            cache_tok=int(cache_tok or 0),
            out_tok=int(out_tok or 0),
            cost_usd_delta=cost_delta,
            model=model,
        )
        cost_payload = {
            "session_id": self.session_id,
            "input": int(in_tok or 0),
            "cached": int(cache_tok or 0),
            "output": int(out_tok or 0),
            "cost_usd_delta": cost_delta,
            "pricing": pricing_payload,
            "model": model,
        }
        self.emit("cost", cost_payload)
        self.emit(
            "token_usage",
            cost_payload,
        )

    def check_stop(self) -> bool:
        msg = self.poll_matching(("stop",))
        if msg is None:
            return False
        # A consumed STOP means the user intentionally paused the active
        # execution loop. Keep that state until the next explicit resume-like
        # prompt so casual chat does not get reinterpreted as TODO execution.
        os.environ["ATLAS_EXECUTION_PAUSED_AFTER_STOP"] = "1"
        os.environ["ATLAS_EXECUTION_PAUSED_SESSION"] = self.session_id
        return True

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
        ssot_ip, ssot_session = self._ssot_context()
        ssot_q_pairs: list[tuple[str, str, dict[str, Any]]] = []
        if ssot_ip:
            if questions:
                ssot_q_pairs = self._ssot_q_pairs_from_questions(questions)
            else:
                ssot_q_pairs = self._ssot_q_pairs_from_questions([{
                    "id": "question",
                    "decision_key": "question",
                    "decision_label": subtitle or question,
                    "question": question,
                    "kind": kind,
                    "subtitle": subtitle or "",
                    "options": options or [],
                }])
            if ssot_q_pairs:
                self._upsert_ssot_qa_items(
                    ssot_ip,
                    ssot_session,
                    flow_id=flow_id,
                    kind="general IP",
                    q_pairs=ssot_q_pairs,
                    status="pending",
                    source="llm-ssot-qna",
                )
                self._emit_ssot_qa_updated(ssot_ip, ssot_session, flow_id)
        if questions:
            payload["questions"] = questions
        else:
            payload.update({
                "question": question,
                "kind": kind,
                "subtitle": subtitle or "",
                "options": options or [],
            })
        if ssot_ip:
            payload.update({
                "session": ssot_session,
                "ip": ssot_ip,
                "workflow": "ssot-gen",
                "source": "llm-ssot-qna",
            })

        try:
            from core import tools as _tools
        except Exception:
            _tools = None
        auto_mode = bool(
            _tools
            and hasattr(_tools, "_ask_user_exec_mode")
            and _tools._ask_user_exec_mode() == "auto-select"
            and hasattr(_tools, "auto_select_ask_user_answer")
        )
        if auto_mode:
            answer_payload = _tools.auto_select_ask_user_answer(
                question=question,
                options=options or [],
                kind=kind,
                subtitle=subtitle or "",
                questions=questions,
            )
            if ssot_ip and ssot_q_pairs and isinstance(answer_payload, dict):
                qa_answers: dict[str, dict[str, Any]] = {}
                if questions and isinstance(answer_payload.get("answers"), list):
                    for (key, _label, q), raw_answer in zip(ssot_q_pairs, answer_payload.get("answers") or []):
                        answer = raw_answer if isinstance(raw_answer, dict) else {}
                        qa_answers[key] = {
                            "answer": self._answer_text(answer, q),
                            "selected": answer.get("selected") or [],
                            "custom": str(answer.get("custom") or "").strip(),
                        }
                elif ssot_q_pairs:
                    key, _label, q = ssot_q_pairs[0]
                    qa_answers[key] = {
                        "answer": self._answer_text(answer_payload, q),
                        "selected": answer_payload.get("selected") or [],
                        "custom": str(answer_payload.get("custom") or "").strip(),
                    }
                if qa_answers:
                    self._upsert_ssot_qa_items(
                        ssot_ip,
                        ssot_session,
                        flow_id=flow_id,
                        kind="general IP",
                        q_pairs=ssot_q_pairs,
                        status="approved",
                        answers=qa_answers,
                        source="llm-ssot-qna.auto_select",
                    )
                    self._emit_ssot_qa_updated(ssot_ip, ssot_session, flow_id)
            self.emit("ask_user_auto_selected", payload)
            return self.format_answer(answer_payload, options or [], questions)

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

        if ssot_ip and ssot_q_pairs and isinstance(payload, dict):
            qa_answers: dict[str, dict[str, Any]] = {}
            if questions and isinstance(payload.get("answers"), list):
                for (key, _label, q), raw_answer in zip(ssot_q_pairs, payload.get("answers") or []):
                    answer = raw_answer if isinstance(raw_answer, dict) else {}
                    qa_answers[key] = {
                        "answer": self._answer_text(answer, q),
                        "selected": answer.get("selected") or [],
                        "custom": str(answer.get("custom") or "").strip(),
                    }
            elif ssot_q_pairs:
                key, _label, q = ssot_q_pairs[0]
                qa_answers[key] = {
                    "answer": self._answer_text(payload, q),
                    "selected": payload.get("selected") or [],
                    "custom": str(payload.get("custom") or "").strip(),
                }
            if qa_answers:
                self._upsert_ssot_qa_items(
                    ssot_ip,
                    ssot_session,
                    flow_id=flow_id,
                    kind="general IP",
                    q_pairs=ssot_q_pairs,
                    status="approved",
                    answers=qa_answers,
                    source="llm-ssot-qna",
                )
                self._emit_ssot_qa_updated(ssot_ip, ssot_session, flow_id)
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
    parts = [p for p in str(session_id or "").split("/") if p]
    owner = parts[0] if parts else "default"
    ip = parts[1] if len(parts) >= 2 else "default"
    workflow = parts[2] if len(parts) >= 3 else "default"
    os.environ["ATLAS_ACTIVE_SESSION"] = session_id
    os.environ["ATLAS_DEFAULT_SESSION_ID"] = owner
    os.environ["ATLAS_ACTIVE_IP"] = ip
    os.environ["ATLAS_DEFAULT_WORKFLOW"] = workflow
    os.environ["ACTIVE_WORKSPACE"] = workflow
    worker = SessionWorker(session_id=session_id, db_path=db_path)
    _install_signal_handlers()

    agent = _load_agent()
    setup_session = getattr(agent, "_setup_session", None)
    if callable(setup_session):
        setup_session(session_id)
        os.environ["ATLAS_SESSION_APPLIED"] = session_id
    setup_workspace = getattr(agent, "_setup_workspace", None)
    if callable(setup_workspace) and workflow and workflow != "default":
        setup_workspace(workflow)
        os.environ["ACTIVE_WORKSPACE"] = workflow

    agent._textual_input_fn = worker.input
    agent._textual_emit_content_fn = worker.emit_content
    agent._textual_emit_reasoning_fn = worker.emit_reasoning
    agent._textual_emit_todo_fn = worker.emit_todo
    agent._textual_emit_flush_fn = worker.emit_flush
    agent._textual_emit_context_fn = worker.emit_context
    agent._textual_emit_token_fn = worker.emit_token_usage
    agent._textual_emit_tool_fn = worker.emit_tool
    agent._textual_emit_tool_result_fn = worker.emit_tool_result
    agent._textual_esc_check_fn = worker.check_stop
    agent._textual_poll_human_input_fn = worker.poll_interrupt
    agent._textual_set_agent_running_fn = worker.set_agent_running

    try:
        from core import tools as _tools

        if hasattr(_tools, "set_ask_user_callback"):
            _tools.set_ask_user_callback(worker.ask_user)
        if hasattr(_tools, "set_record_ssot_qa_callback"):
            _tools.set_record_ssot_qa_callback(worker.record_ssot_qa)
    except Exception as exc:
        worker.emit("error", {"message": f"QA callback registration failed: {exc}"})

    try:
        worker.emit("worker_started", {"pid": os.getpid()})
        agent.chat_loop()
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
