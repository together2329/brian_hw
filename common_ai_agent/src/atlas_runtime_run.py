"""ATLAS runtime — the full CLI / server bootstrap (Phase 28 of
refactor/atlas-modular). atlas_runtime.py is now a pure re-export
shim importing from here so existing import paths
(`from src.atlas_runtime import run_atlas_ui`,
 `from src.atlas_runtime import main` etc.) keep working.

Bundling main() + run_atlas_ui + all helpers + _hydrate_atlas_ui_globals
into ONE module avoids the cross-module globals() mismatch that broke
the earlier extraction attempts (hydration writes to the defining
module's __globals__, so the bare-name lookups in the moved bodies
need the helper to live alongside them).
"""
from __future__ import annotations

from __future__ import annotations
import argparse
import asyncio
import errno
import io
import json
import logging
import multiprocessing
import os
import contextvars
import re
import signal
import socket
import subprocess
import sys
import time
import threading
import traceback
import uuid
from pathlib import Path
from typing import Any, Optional
from core.atlas_exec_policy import (
    EXEC_MODE_ORCHESTRATOR,
    apply_exec_mode_env,
    current_exec_mode,
    normalize_exec_mode,
)
from core.atlas_context import AtlasContext, default_atlas_root


def _subprocess_env_with_pythonpath() -> dict[str, str]:
    env = os.environ.copy()
    paths = [str(path) for path in sys.path if path]
    existing = env.get("PYTHONPATH", "").strip()
    if existing:
        paths.append(existing)
    if paths:
        env["PYTHONPATH"] = os.pathsep.join(dict.fromkeys(paths))
    return env


def _hydrate_atlas_ui_globals() -> None:
    """One-time backport of the symbols Phase 4 extracted-but-didn't-import.

    Phase 4b moved run_atlas_ui / _launch_admin_server / main into this
    module from src/atlas_ui.py, but their bodies use bare-name references
    to ~20 atlas_ui module globals (PROJECT_ROOT, WORKFLOW_ROOT, create_app,
    _assert_bind_target_available, contextvars, helper functions, …). Bare
    names resolve against the function's defining-module globals, which is
    THIS module — and those names live in atlas_ui.py's namespace, not
    here. Without hydration the functions raise NameError on first call.

    Lazy import (inside the function) sidesteps the top-level circular
    import — atlas_ui imports `run_atlas_ui` from us at its line 415, so
    we can't import atlas_ui at module load. By the time anything
    actually CALLS run_atlas_ui / main / _launch_admin_server, atlas_ui
    is fully imported and every symbol is available.
    """
    g = globals()
    if g.get("_AUI_HYDRATED"):
        return
    from src import atlas_ui as _aui
    # Wholesale hydration: every non-dunder atlas_ui module-level name lands
    # in this module's globals so bare-name lookups inside run_atlas_ui /
    # _launch_admin_server / main resolve correctly. A hand-curated list
    # kept missing symbols (Phase 4b extracted ~1060 lines of nested-fn
    # bodies that reference ~50+ atlas_ui symbols; enumerating them one by
    # one is fragile, and every new extraction surface exposes more —
    # subprocess, normalize_exec_mode, _set_runtime_model, etc.). Wholesale
    # copy is bulletproof: any atlas_ui name the bodies reference at runtime
    # finds the live atlas_ui binding. We only skip dunders and names that
    # already exist locally (don't shadow this module's own definitions).
    for name in dir(_aui):
        if name.startswith("__") and name.endswith("__"):
            continue
        if name in g:
            continue  # don't shadow locals like `Path`, `run_atlas_ui`, etc.
        g[name] = getattr(_aui, name)
    g["_AUI_HYDRATED"] = True

def run_atlas_ui(port: int = 8765, host: str = "127.0.0.1") -> None:
    """Start the Atlas web UI server and run the agent in a worker thread.

    Wires brian_hw/common_ai_agent/src/main.py's _textual_* callbacks so the
    existing ReAct loop streams to all connected WS clients.
    """
    _hydrate_atlas_ui_globals()
    _assert_bind_target_available(host, port, "ATLAS UI")

    import uvicorn
    import main as _main  # noqa: WPS433  (intentional runtime import)
    from core.atlas_multiuser import changed_paths_from_tool_result

    app = create_app()
    bridge = app.state.bridge

    # Rebind SSOT-QA helpers from create_app's closure (exposed via
    # app.state) so the nested _ask_user_cb / _record_ssot_qa_cb defined
    # below can reference them by their original local names without
    # raising NameError. See create_app return block for the export side.
    _active_ssot_qa_context = app.state.active_ssot_qa_context
    _ssot_q_pairs_from_questions = app.state.ssot_q_pairs_from_questions
    _upsert_ssot_qa_items = app.state.upsert_ssot_qa_items
    _load_ssot_state = app.state.load_ssot_state
    _valid_ip_name = app.state.valid_ip_name
    _status_group = app.state.status_group
    _answer_text = app.state.answer_text

    # ── Wire main.py callbacks → bridge.emit ───────────────────────
    _main._textual_input_fn = bridge.get_input
    # Esc from the UI sets bridge._stop_flag; react_loop polls this
    # via esc_check_fn and aborts the current iteration cleanly.
    _main._textual_esc_check_fn = bridge.check_stop
    _main._textual_poll_human_input_fn = bridge.poll_interrupt
    # Per-thread active-session reader. main.py used to read
    # os.environ["ATLAS_ACTIVE_SESSION"] directly which races between
    # concurrent users in multi-user mode. By exposing the contextvar
    # via a callback, main.py can resolve the per-thread value first.
    _main._textual_active_session_fn = _active_session_value
    _main._textual_active_ip_fn      = _active_ip_value

    # Strip ANSI escape sequences from ANY text destined for the browser.
    # The terminal-targeting Color class wraps lines in \x1b[2m … \x1b[0m;
    # the browser renders the ESC byte invisibly but happily prints the
    # leftover "[2m" / "[0m" markers, which leaked into the chat as visible
    # garbage. Doing the strip once here covers every emit path.
    import re as _re_ansi
    # First branch: full CSI/OSC sequences w/ the leading ESC byte.
    # Last branch: ORPHAN SGR codes whose ESC was stripped upstream
    # (common on Windows when the console host or codec drops 0x1b),
    # leaving visible garbage like `[2m 187 [0m` in the chat. Match
    # them only when they look like real SGR — `[<digits[;digits]*>m`.
    _ANSI_RE = _re_ansi.compile(
        r"\x1b\[[0-9;?]*[a-zA-Z]"
        r"|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)"
        r"|\[(?:\d{1,3};)*\d{0,3}m"
    )
    def _clean(s):
        return _ANSI_RE.sub("", s) if isinstance(s, str) else s

    def _emit_session_id() -> str:
        return _atlas_emit_session_id()

    def _emit_agent_event(msg_type: str, **payload: Any) -> None:
        sess_id = _emit_session_id()
        if sess_id:
            payload.setdefault("session_id", sess_id)
        bridge.emit(msg_type, **payload)

    def _set_session_agent_state(
        running: bool | None = None,
        alive: bool | None = None,
    ) -> None:
        sess_id = _emit_session_id()
        if sess_id:
            session = bridge._ensure_session(sess_id)
            if running is not None:
                session.agent_running = bool(running)
            if alive is not None:
                session.agent_alive = bool(alive)
            return
        if running is not None:
            bridge.agent_running = bool(running)
        if alive is not None:
            bridge.agent_alive = bool(alive)

    def _current_todo_state() -> dict[str, Any]:
        """Return the freshest structured todo state for browser rendering."""
        try:
            tt = getattr(_main, "todo_tracker", None)
            if tt is not None and hasattr(tt, "to_dict"):
                state = tt.to_dict()
                if isinstance(state, dict) and isinstance(state.get("todos"), list) and state.get("todos"):
                    return state
        except Exception:
            pass
        try:
            import config as _cfg
            from lib.todo_tracker import TodoTracker
            todo_path = Path(str(getattr(_cfg, "TODO_FILE", "current_todos.json")))
            if not todo_path.is_absolute():
                todo_path = PROJECT_ROOT / todo_path
            if todo_path.exists():
                state = TodoTracker.load(todo_path).to_dict()
                if isinstance(state, dict) and isinstance(state.get("todos"), list):
                    return state
        except Exception:
            pass
        return {"todos": []}

    def _emit_todo_line(text: str) -> None:
        state = {"todos": []} if not str(text or "").strip() else _current_todo_state()
        _emit_agent_event(
            "todo_line",
            text=_clean(text),
            todo_state=state,
            todos=state.get("todos", []),
        )

    _main._textual_emit_content_fn   = lambda text, cls="": _emit_agent_event("token", text=_clean(text), cls=cls)

    def _atlas_emit_reasoning(text, blank=False):
        cleaned = _clean(text)
        # Browser side via the live WS bridge (chat feed renders this
        # as a CollapsibleThought block — see workspace.jsx).
        _emit_agent_event("reasoning", text=cleaned)
        # Server-console mirror: an operator running textual_main.py
        # in a terminal needs to see what the model is thinking too,
        # not just the tool calls. Mirror to stderr with a CYAN ┃
        # prefix so reasoning lines are scannable amid debug output.
        if cleaned:
            try:
                import sys as _sys_re
                if blank:
                    _sys_re.stderr.write("\n")
                else:
                    _sys_re.stderr.write(
                        f"  \033[36m┃\033[0m \033[2m{cleaned}\033[0m\n"
                    )
                _sys_re.stderr.flush()
            except Exception:
                pass

    _main._textual_emit_reasoning_fn = _atlas_emit_reasoning
    _main._textual_emit_todo_fn      = _emit_todo_line
    _main._textual_emit_flush_fn     = lambda: (
        _emit_agent_event("flush"),
        # Workspace switches happen behind a slash command and re-register
        # the slash registry. Nudge the UI to re-fetch /api/commands so the
        # autocomplete dropdown picks up new workspace commands.
        _emit_agent_event("commands_changed"),
    )
    def _emit_tool_line(text: str) -> None:
        # Route from per-agent bridge context first; process-global env is
        # only a legacy fallback inside _atlas_emit_session_id().
        _emit_agent_event("tool", text=_clean(text))
    _main._textual_emit_tool_fn      = _emit_tool_line
    # Browser-side tool_result cap. Display-only — LLM still gets the
    # full obs upstream; this just trims what we ship over the WS so a
    # multi-MB grep / sim log doesn't drown the chat. Configurable via
    # WS_TOOL_RESULT_MAX_CHARS. Default raised to 128 KB so a typical
    # SSOT YAML (≈ 60-100 KB) renders end-to-end without the previous
    # 8 KB ceiling chopping the file at the registers section.
    _ws_tool_max = 128000
    try:
        try: import src.config as _cfg2  # type: ignore  # noqa: WPS433
        except Exception:
            try: import config as _cfg2  # type: ignore  # noqa: WPS433
            except Exception: _cfg2 = None
        if _cfg2 is not None:
            _ws_tool_max = int(getattr(_cfg2, "WS_TOOL_RESULT_MAX_CHARS", 128000))
    except Exception:
        _ws_tool_max = 128000
    # Strip the `[Step N/M: ...] ... → Interpret the result below in
    # context of the current goal` block that react_loop prepends to
    # observations for the LLM. That header is useful in the LLM
    # message stream but pollutes the user-facing tool_result card —
    # without this defensive strip a write/replace tool_result body
    # opens with the entire todo header instead of the actual diff.
    _STEP_HEADER_RE = re.compile(
        r"^\[Step\s+\d+/\d+:[^\n]*\]\n"
        r"(?:[^\n]*\n)*?"
        r"→ Interpret the result below in context of the current goal\n+",
        re.MULTILINE,
    )

    def _emit_tool_result(obs, tool=""):
        cleaned = _clean(obs)
        cleaned = _STEP_HEADER_RE.sub("", cleaned, count=1)
        _emit_agent_event(
            "tool_result",
            text=cleaned[:_ws_tool_max],
            tool=tool,
            truncated=len(cleaned) > _ws_tool_max,
        )
        # Auto-commit for write/replace/edit tools — capture the
        # operated-on path from the tool result body and snapshot the
        # change into the per-IP .git so each agent edit becomes a
        # discrete commit. Best-effort: any parse miss or git failure
        # is silent (Atlas should never refuse to display a result
        # because the optional commit failed).
        try:
            for _path_hit in changed_paths_from_tool_result(tool, cleaned):
                _auto_commit_for_path(_path_hit, tool=tool)
                # Push a file_changed event so the frontend can
                # auto-reload preview / SSOT / file-tree without
                # waiting for the next tool_result coalesce window.
                try:
                    _emit_agent_event("file_changed", path=str(_path_hit), tool=tool)
                except Exception:
                    pass
        except Exception:
            pass
    _main._textual_emit_tool_result_fn = _emit_tool_result

    def _ctx_update(tokens, max_tok, **runtime):
        payload = {"used": tokens, "max": max_tok}
        model = str(runtime.get("model") or "").strip()
        effort = str(runtime.get("reasoning_effort") or runtime.get("effort") or "").strip()
        if model:
            payload["model"] = model
        if effort:
            payload["reasoning_effort"] = effort
        _emit_agent_event("context", **payload)
    _main._textual_emit_context_fn = _ctx_update
    def _emit_token(in_tok, cache_tok, out_tok):
        # Resolve display/runtime model first; pricing then tries this exact
        # value before falling back to LLM_BASE_NAME for opaque deployments.
        try:
            import os as _os_cost
            _model_now = (
                _os_cost.getenv("LLM_ACTIVE_MODEL_NAME", "").strip()
                or _os_cost.getenv("MODEL_NAME", "").strip()
                or _os_cost.getenv("LLM_MODEL_NAME", "").strip()
                or _os_cost.getenv("LLM_ACTIVE_BASE_NAME", "").strip()
                or _os_cost.getenv("LLM_BASE_NAME", "").strip()
            )
            if not _model_now:
                try:
                    from src.llm_client import get_active_model as _gam
                    _model_now = _gam() or ""
                except Exception:
                    _model_now = ""
        except Exception:
            _model_now = ""
        # Resolve pricing at LLM-call time so the rate matches the model
        # actually used for THIS call (LLM_ACTIVE_BASE_NAME / LLM_BASE_NAME
        # can pin the base model; otherwise fall back to MODEL_NAME /
        # LLM_MODEL_NAME).
        # Computing the USD delta on the backend keeps frontend math simple
        # and avoids drift between page-load /healthz pricing and the
        # current call's model.
        try:
            from lib.model_pricing import get_active_pricing
            p = get_active_pricing(_model_now)
        except Exception:
            p = None
        cost_delta = 0.0
        if p is not None:
            # in_tok from react_loop is the FULL prompt_tokens (includes
            # the cached subset). cache_tok is that cached subset only.
            # Charging both `in_tok * input` and `cache_tok * cache` would
            # bill the cached portion twice — once at the input rate and
            # once at the cache rate. Subtract the cache slice first so
            # billable_input = prompt − cached.
            _in = max(0, (in_tok or 0) - (cache_tok or 0))
            cost_delta = (
                _in              * p.input  +
                (cache_tok or 0) * p.cache  +
                (out_tok or 0)   * p.output
            ) / 1_000_000.0
        # Persist cumulative cost to disk so /healthz re-reads after
        # reload AND so the figure survives a backend restart. textual_ui
        # writes the same schema (in_tok / cache_tok / out_tok / sum_tok)
        # but only in the textual app — the web path was emitting WS
        # frames without ever touching .session/<sess>/cost.json, so the
        # ledger reset to $0.0000 every page load.
        sess_id = _emit_session_id()
        try:
            _sess_str = str(sess_id or "").strip("/")
            if _sess_str:
                cost_path = PROJECT_ROOT / ".session" / _sess_str / "cost.json"
                cost_path.parent.mkdir(parents=True, exist_ok=True)
                existing = {}
                if cost_path.exists():
                    try:
                        existing = json.loads(cost_path.read_text(encoding="utf-8", errors="replace"))
                    except Exception:
                        existing = {}
                cumulative_in = int(existing.get("in_tok", 0) or 0) + int(in_tok or 0)
                cumulative_cache = int(existing.get("cache_tok", 0) or 0) + int(cache_tok or 0)
                cumulative_out = int(existing.get("out_tok", 0) or 0) + int(out_tok or 0)
                cumulative_cost = float(existing.get("cost_usd", 0) or 0) + float(cost_delta or 0)
                cost_path.write_text(
                    json.dumps({
                        "in_tok": cumulative_in,
                        "cache_tok": cumulative_cache,
                        "out_tok": cumulative_out,
                        "sum_tok": cumulative_in + cumulative_out,
                        "cost_usd": cumulative_cost,
                        # Last-call input tokens snapshot for the
                        # "Context X / max" sidebar widget — without this
                        # the widget can only see cumulative tokens and
                        # the % bar stays at 0 forever.
                        "last_in_tok": int(in_tok or 0),
                        "last_cache_tok": int(cache_tok or 0),
                        "last_out_tok": int(out_tok or 0),
                        "last_at": time.time(),
                        "model": _model_now,
                        "updated_at": time.time(),
                    }, indent=2, ensure_ascii=False),
                    encoding="utf-8",
                )
        except Exception:
            pass
        _emit_agent_event(
            "cost",
            input=in_tok, cached=cache_tok, output=out_tok,
            context_used=in_tok,
            cost_usd_delta=cost_delta,
            pricing={"input": p.input, "cache": p.cache, "output": p.output} if p else None,
            model=_model_now,
        )
    _main._textual_emit_token_fn = _emit_token

    def _set_running(val: bool):
        _set_session_agent_state(running=val)
        _emit_agent_event("agent_state", running=val)
    _main._textual_set_agent_running_fn = _set_running

    # Safety-net emit for slash command output. The token+flush pipeline has
    # shown intermittent delivery for slash payloads (frontend gets the
    # subsequent agent_state but no token frame), leaving the user with a
    # missing /context / /help / /skills response. This event lands the
    # payload directly in the feed via workspace.jsx's slash_output handler.
    _main._textual_emit_slash_output_fn = lambda text: _emit_agent_event(
        "slash_output", text=_clean(text)
    )

    # Mode-change notification — chat_loop auto-promotes plan_q→normal when
    # the user types "y" to confirm. Without this signal the React mode pill
    # stays on PLAN even though the agent is now executing.
    _main._textual_emit_mode_fn = lambda mode: _emit_agent_event("mode_change", mode=mode)

    # ── ask_user → emit qcard event, block on answer queue ────────
    import uuid
    try:
        from core import tools as _tools
    except ImportError:
        _tools = None

    # Helpers are defined as closures inside create_app(); pull them off
    # app.state so this module-level function can reach them.
    _active_ssot_qa_context = app.state.active_ssot_qa_context
    _valid_ip_name = app.state.valid_ip_name
    _ssot_q_pairs_from_questions = app.state.ssot_q_pairs_from_questions
    _load_ssot_state = app.state.load_ssot_state
    _upsert_ssot_qa_items = app.state.upsert_ssot_qa_items
    _status_group = app.state.status_group

    def _record_ssot_qa_cb(questions=None, ip=None, session=None, kind="",
                           source="llm-ssot-qna", status="pending"):
        """Record deferred SSOT QA without blocking the agent thread."""
        ctx_ip, ctx_session = _active_ssot_qa_context()
        target_ip = str(ip or ctx_ip or "").strip()
        if not _valid_ip_name(target_ip):
            return "[record_ssot_qa: no active valid SSOT IP]"
        target_session = normalize_session_name(str(session or ctx_session or f"{target_ip}/ssot-gen"))
        flow_id = "qa_backlog_" + uuid.uuid4().hex[:10]
        q_pairs = _ssot_q_pairs_from_questions(questions or [])
        if not q_pairs:
            return "[record_ssot_qa: no valid QA items to record]"
        state = _load_ssot_state(target_ip) or {}
        ip_kind = str(kind or "").strip()
        if ip_kind.lower() in {"single", "multi", "input"}:
            ip_kind = ""
        _upsert_ssot_qa_items(
            target_ip,
            flow_id=flow_id,
            kind=str(ip_kind or state.get("kind") or "general IP"),
            q_pairs=q_pairs,
            status=str(status or "pending"),
            session=target_session,
            source=str(source or "llm-ssot-qna"),
        )
        bridge.emit(
            "ssot_qa_updated",
            ip=target_ip,
            workflow="ssot-gen",
            flow_id=flow_id,
            session=target_session,
            session_id=target_session,
        )
        return (
            f"[record_ssot_qa] recorded {len(q_pairs)} "
            f"{_status_group(str(status or 'pending'))} SSOT QA item(s) "
            f"for {target_session}"
        )

    def _ask_user_cb(question, options, kind, subtitle, questions=None):
        """ask_user UI bridge.

        Single-question mode: pass `question/options/kind/subtitle`.
        Batched mode (mirrors textual UI): pass `questions=[{...}, ...]`
        and the frontend renders a tab strip — one breadcrumb per
        question, ☐/☒ answered marker, plus a final 'Submit' tab — so
        the user fills N answers in one round-trip.
        """
        flow_id = "qa_" + uuid.uuid4().hex[:10]
        ssot_ip, ssot_session = _active_ssot_qa_context()
        ssot_q_pairs: list[tuple[str, str, dict[str, Any]]] = []
        if ssot_ip:
            if questions:
                ssot_q_pairs = _ssot_q_pairs_from_questions(questions)
            elif question:
                ssot_q_pairs = _ssot_q_pairs_from_questions([{
                    "id": "question",
                    "decision_key": "question",
                    "decision_label": subtitle or question,
                    "question": question,
                    "kind": kind,
                    "subtitle": subtitle or "",
                    "options": options or [],
                }])
            if ssot_q_pairs:
                _upsert_ssot_qa_items(
                    ssot_ip,
                    flow_id=flow_id,
                    kind=str((_load_ssot_state(ssot_ip) or {}).get("kind") or "general IP"),
                    q_pairs=ssot_q_pairs,
                    status="pending",
                    session=ssot_session,
                )
                bridge.emit(
                    "ssot_qa_updated",
                    ip=ssot_ip,
                    workflow="ssot-gen",
                    flow_id=flow_id,
                    session=ssot_session,
                    session_id=ssot_session,
                )
        ssot_emit = (
            {
                "session": ssot_session,
                "session_id": ssot_session,
                "ip": ssot_ip,
                "workflow": "ssot-gen",
                "source": "llm-ssot-qna",
            }
            if ssot_ip else {}
        )
        # ssot-gen disables ask_user popups: questions are already
        # written to the SsotQaBoard above, and the user answers them
        # at their own pace from the Q&A Session tab. Returning a
        # short instructional string unblocks the agent without
        # forcing a 15-min wait or surfacing a modal qcard.
        _active_session_str = str(_active_session_value() or "")
        if _active_session_str.rstrip("/").endswith("/ssot-gen"):
            n_qs = len(questions) if questions else 1
            return (
                f"[ssot-gen] ask_user disabled in this workflow. "
                f"{n_qs} question(s) were recorded to the Web Q&A board "
                f"for the user to answer asynchronously via the Q&A "
                f"Session tab. Skip blocking on this and continue with "
                f"the next non-blocking step (e.g. import evidence, "
                f"draft SSOT sections from disk truth)."
            )
        auto_mode = bool(
            _tools
            and hasattr(_tools, "_ask_user_exec_mode")
            and _tools._ask_user_exec_mode() == "auto-select"
            and hasattr(_tools, "auto_select_ask_user_answer")
        )
        if auto_mode:
            ans = _tools.auto_select_ask_user_answer(
                question=question,
                options=options or [],
                kind=kind,
                subtitle=subtitle or "",
                questions=questions,
            )
            if ssot_ip and ssot_q_pairs and isinstance(ans, dict):
                qa_answers: dict[str, dict[str, Any]] = {}
                if questions and isinstance(ans.get("answers"), list):
                    for (key, _label, q), qa in zip(ssot_q_pairs, ans.get("answers") or []):
                        qa_dict = qa if isinstance(qa, dict) else {}
                        qa_answers[key] = {
                            "answer": _answer_text(qa_dict, q),
                            "selected": qa_dict.get("selected") or [],
                            "custom": str(qa_dict.get("custom") or "").strip(),
                        }
                else:
                    key, _label, q = ssot_q_pairs[0]
                    qa_answers[key] = {
                        "answer": _answer_text(ans, q),
                        "selected": ans.get("selected") or [],
                        "custom": str(ans.get("custom") or "").strip(),
                    }
                _upsert_ssot_qa_items(
                    ssot_ip,
                    flow_id=flow_id,
                    kind=str((_load_ssot_state(ssot_ip) or {}).get("kind") or "general IP"),
                    q_pairs=ssot_q_pairs,
                    status="approved",
                    answers=qa_answers,
                    session=ssot_session,
                    source="llm-ssot-qna.auto_select",
                )
                bridge.emit(
                    "ssot_qa_updated",
                    ip=ssot_ip,
                    workflow="ssot-gen",
                    flow_id=flow_id,
                    session=ssot_session,
                    session_id=ssot_session,
                )
            bridge.emit("ask_user_auto_selected", flow_id=flow_id, **ssot_emit)
            if questions and isinstance(ans, dict) and "answers" in ans:
                blocks = []
                for q, qa in zip(questions, ans.get("answers") or []):
                    label = (q.get("subtitle") or q.get("question", ""))[:40]
                    blocks.append(f"  • {label}\n    {_format_answer(qa, q.get('options') or [])}")
                return "Auto-selected answers:\n" + "\n".join(blocks) if blocks else "(no answers)"
            return "Auto-selected answer: " + _format_answer(ans, options or [])
        bridge.open_question(flow_id)
        if questions:
            # Batched payload — frontend (workspace.jsx) detects the
            # `questions` array and switches to tabbed render.
            bridge.emit(
                "ask_user",
                flow_id=flow_id,
                questions=questions,
                **ssot_emit,
            )
        else:
            bridge.emit(
                "ask_user",
                flow_id=flow_id,
                question=question,
                kind=kind,
                subtitle=subtitle or "",
                options=options or [],
                **ssot_emit,
            )
        try:
            ans = bridge.wait_answer(flow_id, timeout=900)  # 15 min ceiling
        finally:
            bridge.close_question(flow_id)
        if ans is None:
            return "[ask_user: no answer received within 15 min]"
        # Cancel-all from the user — match textual UI wording.
        if isinstance(ans, dict) and ans.get("type") == "cancel":
            return "User declined to answer questions"
        # Batched answer format: {"answers": [{...}, ...]} aligned with questions.
        if questions and isinstance(ans, dict) and "answers" in ans:
            blocks = []
            qa_answers: dict[str, dict[str, Any]] = {}
            for q, qa in zip(questions, ans.get("answers") or []):
                label = (q.get("subtitle") or q.get("question", ""))[:40]
                blocks.append(
                    f"  • {label}\n    {_format_answer(qa, q.get('options'))}"
                )
            if ssot_ip and ssot_q_pairs:
                for (key, _label, q), qa in zip(ssot_q_pairs, ans.get("answers") or []):
                    qa_dict = qa if isinstance(qa, dict) else {}
                    qa_answers[key] = {
                        "answer": _answer_text(qa_dict, q),
                        "selected": qa_dict.get("selected") or [],
                        "custom": str(qa_dict.get("custom") or "").strip(),
                    }
                _upsert_ssot_qa_items(
                    ssot_ip,
                    flow_id=flow_id,
                    kind=str((_load_ssot_state(ssot_ip) or {}).get("kind") or "general IP"),
                    q_pairs=ssot_q_pairs,
                    status="approved",
                    answers=qa_answers,
                    session=ssot_session,
                )
                bridge.emit(
                    "ssot_qa_updated",
                    ip=ssot_ip,
                    workflow="ssot-gen",
                    flow_id=flow_id,
                    session=ssot_session,
                    session_id=ssot_session,
                )
            return "Batched answers:\n" + "\n".join(blocks) if blocks else "(no answers)"
        if ssot_ip and ssot_q_pairs and isinstance(ans, dict):
            key, _label, q = ssot_q_pairs[0]
            _upsert_ssot_qa_items(
                ssot_ip,
                flow_id=flow_id,
                kind=str((_load_ssot_state(ssot_ip) or {}).get("kind") or "general IP"),
                q_pairs=ssot_q_pairs,
                status="approved",
                answers={
                    key: {
                        "answer": _answer_text(ans, q),
                        "selected": ans.get("selected") or [],
                        "custom": str(ans.get("custom") or "").strip(),
                    }
                },
                session=ssot_session,
            )
            bridge.emit(
                "ssot_qa_updated",
                ip=ssot_ip,
                workflow="ssot-gen",
                flow_id=flow_id,
                session=ssot_session,
                session_id=ssot_session,
            )
        return _format_answer(ans, options or [])

    if _tools and hasattr(_tools, "set_ask_user_callback"):
        _tools.set_ask_user_callback(_ask_user_cb)
    if _tools and hasattr(_tools, "set_record_ssot_qa_callback"):
        _tools.set_record_ssot_qa_callback(_record_ssot_qa_cb)

    def _run_agent():
        _sync_env_to_context()
        try:
            _main.chat_loop()
        except Exception as e:
            _emit_agent_event("error", message=str(e))
        finally:
            _set_session_agent_state(running=False, alive=False)
            _emit_agent_event("agent_state", running=False)
            _emit_agent_event("done")

    def _start_agent_thread():
        ctx = contextvars.copy_context()
        threading.Thread(target=ctx.run, args=(_run_agent,), daemon=True).start()

    bridge.set_agent_starter(_start_agent_thread)
    # Process-per-session mode is lazy by design: the selected worker
    # should start when that workspace receives chat input, not as an
    # unrelated default worker during shared backend boot.
    _autostart_default = "0" if bridge._using_processes() else "1"
    if os.environ.get("ATLAS_AGENT_AUTOSTART", _autostart_default).strip().lower() not in {"0", "false", "off", "no"}:
        bridge.ensure_agent_alive()

    os.environ["ATLAS_SOURCE_ROOT"] = str(_source_root())
    os.environ["ATLAS_WORKFLOW_ROOT"] = str(WORKFLOW_ROOT)
    os.environ["ATLAS_PROJECT_ROOT"] = str(PROJECT_ROOT)
    _root_note = (
        f"\n\n[Atlas Runtime] You are running with cwd = {PROJECT_ROOT}. "
        f"All file reads/writes default to ATLAS_PROJECT_ROOT={PROJECT_ROOT}. "
        f"The active workflow scripts live under the active IP at "
        f"ATLAS_WORKFLOW_ROOT={WORKFLOW_ROOT}; the common_ai_agent source root "
        f"is ATLAS_SOURCE_ROOT={_source_root()} for bootstrap imports only. "
        f"Use `$ATLAS_WORKFLOW_ROOT/<workflow>/scripts/...` for deterministic "
        f"workflow tooling and pass `--root $ATLAS_PROJECT_ROOT` for IP/project "
        f"artifacts. Keep generated IP artifacts under PROJECT_ROOT/IP_ROOT."
    )
    try:
        # Append to whatever the existing system prompt builder produces
        # so the hint is part of every system-prompt rebuild (workspace
        # switches included).
        _orig_builder = getattr(_main, "_build_system_prompt_str", None)
        if callable(_orig_builder):
            def _patched_builder(*a, _orig=_orig_builder, _note=_root_note, **kw):
                return _orig(*a, **kw) + _note
            _main._build_system_prompt_str = _patched_builder
    except Exception:
        pass

    print(f"\n  ATLAS UI → {_access_url(host, port)}\n")
    print(
        "  [stdin] commands: 'status' (snapshot), 'heal' "
        "(force agent_running=False + drain inbox), 'sessions' "
        "(list .session/), 'help', 'quit'"
    )

    # ── Operator stdin command lane ───────────────────────────────────
    # Lets the user inspect / unstuck the running backend without
    # restarting. Reads one line at a time off stdin in a daemon
    # thread; each command prints its result to stdout. Designed for
    # the common case where a stuck chat_loop / hung WS leaves the
    # browser blank — operator types `heal`, gets the agent unstuck,
    # carries on. The xterm focus-event noise (`^[[O^[[I`) the user
    # was seeing in the terminal is also suppressed here because the
    # readline loop consumes those bytes silently.
    def _stdin_command_loop() -> None:
        import threading as _t
        while True:
            try:
                raw = sys.stdin.readline()
            except Exception:
                return
            if raw == "":
                return  # EOF — terminal closed
            cmd = raw.strip()
            # Suppress xterm focus / mouse escape sequences silently —
            # they show up as the literal text "[O" / "[I" / "[?1004h"
            # when the terminal sends ESC-prefixed bytes that python's
            # readline echoes through. Anything entirely non-alphanumeric
            # at the head is treated as terminal control noise.
            if not cmd or not cmd[0].isalnum():
                continue
            head = cmd.split(None, 1)[0].lower()
            if head in ("status", "stat"):
                try:
                    print(f"  [status] active_session={_active_session_value()!r} "
                          f"active_ip={_active_ip_value()!r} "
                          f"agent_running={bridge.agent_running} "
                          f"agent_alive={bridge.agent_alive} "
                          f"threads={len(_t.enumerate())}")
                except Exception as e:
                    print(f"  [status] error: {e}")
                try:
                    from src.atlas_api_jobs import lazy_worker_snapshot
                    snap = lazy_worker_snapshot()
                    if not snap:
                        print("  [workers] no lazy worker spawned yet")
                    else:
                        for w in snap:
                            tag = "alive" if w["alive"] else f"dead(rc={w['returncode']})"
                            print(f"  [workers] pid={w['pid']} {tag} url={w['url']}")
                except Exception as e:
                    print(f"  [workers] snapshot error: {e}")
            elif head in ("heal", "unstuck"):
                try:
                    bridge.agent_running = False
                    bridge.request_stop()
                    print("  [heal] agent_running=False, _inbox preserved (slash items dropped, user prompts kept)")
                except Exception as e:
                    print(f"  [heal] error: {e}")
            elif head == "sessions":
                try:
                    sroot = PROJECT_ROOT / ".session"
                    if not sroot.is_dir():
                        print("  [sessions] no .session/ tree")
                        continue
                    print(f"  [sessions] root={sroot}")
                    for entry in sorted(sroot.rglob("conversation.json")):
                        rel = entry.parent.relative_to(sroot).as_posix()
                        size = entry.stat().st_size
                        print(f"    - {rel:60s} {size//1024}KB")
                except Exception as e:
                    print(f"  [sessions] error: {e}")
            elif head in ("help", "?"):
                print("  [help] status | heal | sessions | help | quit")
            elif head in ("quit", "exit"):
                print("  [quit] shutting down…")
                os._exit(0)
            else:
                print(f"  [?] unknown: {cmd!r} — try 'help'")

    try:
        threading.Thread(target=_stdin_command_loop, name="atlas-stdin",
                         daemon=True).start()
    except Exception:
        pass

    # ── Single-worker mode: spawn one main-loop worker on port 5601 ──────
    _single_worker_proc: "subprocess.Popen[bytes] | None" = None
    _single_worker_mode = (
        os.environ.get("ATLAS_SINGLE_MAIN_LOOP", "").strip().lower() not in ("", "0", "false", "no", "off")
        or os.environ.get("ATLAS_EXEC_MODE", "").strip().lower() == "single-worker"
    )
    _single_worker_eager = (
        os.environ.get("ATLAS_SINGLE_WORKER_EAGER", "").strip().lower()
        in ("1", "true", "yes", "on")
    )
    if not (
        os.environ.get("ATLAS_WORKER_TRANSPORT", "").strip()
        or os.environ.get("ATLAS_WORKER_DISPATCH_TRANSPORT", "").strip()
        or os.environ.get("ATLAS_WORKER_DISPATCH_MODE", "").strip()
    ):
        os.environ["ATLAS_WORKER_TRANSPORT"] = "ipc"
    _worker_transport_mode = (
        os.environ.get("ATLAS_WORKER_TRANSPORT", "").strip().lower().replace("_", "-")
        or os.environ.get("ATLAS_WORKER_DISPATCH_TRANSPORT", "").strip().lower().replace("_", "-")
        or os.environ.get("ATLAS_WORKER_DISPATCH_MODE", "").strip().lower().replace("_", "-")
    )
    _worker_transport_ipc = _worker_transport_mode in ("ipc", "process", "subprocess", "portless")
    if _single_worker_mode and _single_worker_eager and not _worker_transport_ipc:
        os.environ["ATLAS_LAZY_WORKERS"] = "0"
        import urllib.request as _urllib_req
        _sw_port = 5601
        _sw_env = {**os.environ}
        _sw_db = os.environ.get("ATLAS_DB_PATH", "")
        if _sw_db:
            _sw_env["ATLAS_DB_PATH"] = _sw_db
        _main_py = str(HERE / "main.py")
        _single_worker_proc = subprocess.Popen(
            [sys.executable, _main_py, "--serve", "--host", "127.0.0.1",
             "--port", str(_sw_port), "--all-workflows"],
            env=_sw_env,
        )
        print(f"[single-worker] spawned main-loop worker on port {_sw_port} (pid={_single_worker_proc.pid})")
        # Health probe: wait up to 10 s for the worker to become ready.
        _sw_ready = False
        _sw_deadline = 10.0
        _sw_start = __import__("time").monotonic()
        while __import__("time").monotonic() - _sw_start < _sw_deadline:
            try:
                with _urllib_req.urlopen(f"http://127.0.0.1:{_sw_port}/health", timeout=1) as _r:
                    if _r.status == 200:
                        _sw_ready = True
                        break
            except Exception:
                pass
            __import__("time").sleep(0.5)
        if _sw_ready:
            print(f"[single-worker] worker on port {_sw_port} is healthy")
        else:
            print(f"[single-worker] WARNING: worker on port {_sw_port} did not respond within {_sw_deadline}s")

        import atexit as _atexit

        def _terminate_single_worker(_proc=_single_worker_proc) -> None:
            if _proc and _proc.poll() is None:
                print(f"[single-worker] sending SIGTERM to pid={_proc.pid}")
                import signal as _signal
                try:
                    _proc.send_signal(_signal.SIGTERM)
                except Exception:
                    pass

        _atexit.register(_terminate_single_worker)
    elif _single_worker_mode:
        if _worker_transport_ipc:
            os.environ["ATLAS_LAZY_WORKERS"] = "0"
            print(
                "[single-worker] portless process dispatch enabled; "
                "workflow jobs run as IPC subprocesses without worker HTTP port 5601 "
                "(set ATLAS_WORKER_TRANSPORT=http to use the legacy worker port)"
            )
        else:
            # Lazy single-worker: defer the main.py worker spawn until the first
            # job dispatch. WORKER_URL_DEFAULT is pinned to 5601 so that
            # _worker_url_is_shared_default() returns True and the lazy
            # spawn picks up --all-workflows, matching the eager path.
            os.environ["ATLAS_LAZY_WORKERS"] = "1"
            os.environ.setdefault("WORKER_URL_DEFAULT", "http://127.0.0.1:5601")
            print(
                "[single-worker] lazy mode: worker on port 5601 will spawn on "
                "first job dispatch (set ATLAS_SINGLE_WORKER_EAGER=1 to spawn "
                "at server startup like before)"
            )
    else:
        if _worker_transport_ipc:
            os.environ["ATLAS_LAZY_WORKERS"] = "0"
            os.environ["ATLAS_WORKER_WARM_POOL"] = "0"
            print(
                "[orchestrator-mode] portless process dispatch enabled; "
                "workflow jobs run as IPC subprocesses behind the Atlas port "
                "(set ATLAS_WORKER_TRANSPORT=http for the legacy internal worker ports)"
            )
        else:
            os.environ.setdefault("ATLAS_LAZY_WORKERS", "1")
            os.environ.setdefault("ATLAS_WORKER_WARM_POOL", "1")
            print(
                "[orchestrator-mode] lazy worker start enabled; "
                "workflow workers launch on first dispatch "
                "(set ATLAS_LAZY_WORKERS=0 to require an external fleet); "
                "warm pool keeps frequent workers ready "
                "(set ATLAS_WORKER_WARM_POOL=0 to disable)"
            )

    uvicorn.run(app, host=host, port=port, log_level="warning", loop="asyncio", http="h11")

def _launch_admin_server(admin_port: str, admin_host: str) -> subprocess.Popen:
    """Launch the standalone admin server next to the main Atlas UI."""
    _hydrate_atlas_ui_globals()
    import atexit

    port_text = str(admin_port or "3002").strip() or "3002"
    try:
        port = int(port_text)
    except ValueError:
        sys.exit(f"--admin: expected optional port number, got {admin_port!r}")

    bind_host = str(admin_host or "127.0.0.1")
    _assert_bind_target_available(bind_host, port, "ATLAS admin")

    admin_script = Path(__file__).resolve().with_name("atlas_admin.py")
    proc = subprocess.Popen(
        [
            sys.executable,
            str(admin_script),
            "--port",
            str(port),
            "--host",
            bind_host,
            "--root",
            str(_source_root()),
        ],
        cwd=str(_source_root()),
        env=_subprocess_env_with_pythonpath(),
    )
    atexit.register(lambda p=proc: (p.terminate() if p.poll() is None else None))
    print(
        f"\n  [admin] launched standalone admin server -> "
        f"{_access_url(bind_host, port, '/admin')}",
        flush=True,
    )
    return proc

def main() -> None:
    # NB: main() mutates PROJECT_ROOT / WORKFLOW_ROOT via `global` further
    # below. Because hydration copies the current atlas_ui values into THIS
    # module, those mutations stay local to atlas_runtime — atlas_ui's own
    # PROJECT_ROOT does NOT pick them up. That mismatch is harmless today
    # because the canonical launch path is `from src.atlas_ui import
    # run_atlas_ui; run_atlas_ui(...)` (textual_main.py:391), which never
    # routes through main(). If someone ever wires `python -m atlas_runtime`
    # back to production, change the `global ... = X` writes here to
    # `_aui.X = ...` so atlas_ui sees the new roots too.
    _hydrate_atlas_ui_globals()
    ap = argparse.ArgumentParser(prog="atlas_ui",
                                  description="Atlas frontend for common_ai_agent")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--admin", nargs="?", const="3002", default=None,
                    metavar="PORT",
                    help="Also launch the standalone admin server "
                         "(default port: 3002).")
    ap.add_argument("--admin-host", default=None,
                    help="Bind host for --admin. Defaults to --host. "
                         "Use 0.0.0.0 only when admin should be LAN-reachable.")
    ap.add_argument("--root", default=None,
                    help="Project root directory the backend serves "
                         "(.session/, IPs, file tree, …). Defaults to "
                         "ATLAS_ROOT or ~/ATLAS.")
    ap.add_argument("--workflow-root", "--workflow_root", dest="workflow_root", default=None,
                    help="Directory containing workflow families such as "
                         "ssot-gen/ and rtl-gen/. Defaults to "
                         "ATLAS_WORKFLOW_ROOT or common_ai_agent/workflow.")
    ap.add_argument("--ip-root", "--ip_root", dest="ip_root", default=None,
                    help="Optional active IP directory. When --root is omitted, "
                         "PROJECT_ROOT becomes this directory's parent and "
                         "ATLAS_IP_ROOT points at this directory.")
    # Canonical 3-part session path: <session_id>/<ip>/<workflow>
    # All three default to "default" so the directory layout is uniform.
    ap.add_argument("-s", "--session", dest="session_id", default="default",
                    help="session_id segment (default: 'default')")
    ap.add_argument("--workspace-session", "--ws-session", dest="workspace_session",
                    default=None,
                    help="workspace session segment between user/session owner and IP "
                         "(default: ATLAS_WORKSPACE_SESSION or 'default')")
    ap.add_argument("-ip", "--ip", dest="ip", default="default",
                    help="ip segment (default: 'default')")
    ap.add_argument("-w", "--workflow", dest="workflow", default="default",
                    help="workflow segment (default: 'default')")
    ap.add_argument("--model", default="",
                    help="Runtime model/profile for the Atlas orchestrator "
                         "(e.g. gpt-5.5, deepseek, glm).")
    ap.add_argument("--effort", default="",
                    help="Runtime reasoning effort for the Atlas orchestrator "
                         "(none, low, medium, high, xhigh).")
    ap.add_argument("--exec", "--exec-mode", dest="exec_mode",
                    default=None,
                    help="Execution topology. Accepted values:\n"
                         "  s | single | single-worker  → spawn one child "
                         "main.py worker on port 5601 (local single-user).\n"
                         "  o | orch | orchestrator      → dispatch through "
                         "workflow workers; local workers are lazy-started "
                         "on first use unless ATLAS_LAZY_WORKERS=0.\n"
                         "Falls back to ATLAS_EXEC_MODE / "
                         "ATLAS_SINGLE_MAIN_LOOP / ATLAS_ORCHESTRATOR_MODE "
                         "env vars when omitted; final fallback is "
                         "'orchestrator'.")
    args = ap.parse_args()
    # Normalize the exec_mode shorthand (--exec s / --exec o) and pin
    # into env BEFORE any boot-config / worker-spawn code reads it so
    # the CLI flag wins over inherited env.
    _exec_raw = (args.exec_mode or "").strip().lower()
    if _exec_raw:
        _exec_resolved = normalize_exec_mode(_exec_raw)
        if not _exec_resolved:
            sys.exit(f"--exec: unknown value {args.exec_mode!r}. "
                     f"Use s|single|single-worker or o|orch|orchestrator.")
        apply_exec_mode_env(_exec_resolved, os.environ)
    # Re-anchor PROJECT_ROOT before any request handler runs. Module-level
    # PROJECT_ROOT was computed from the import-time cwd; chdir + rebind
    # so /api/files, .session/, and friends all serve from --root.
    global PROJECT_ROOT, WORKFLOW_ROOT
    # Always resolve + bind WORKFLOW_ROOT: this module has no module-level
    # WORKFLOW_ROOT (unlike atlas_ui.py:289), so the `global` declaration
    # only creates an unbound name. Without an unconditional assignment,
    # line 1028's `setdefault("ATLAS_WORKFLOW_ROOT", str(WORKFLOW_ROOT))`
    # raises NameError when `--workflow-root` isn't passed. The resolver
    # already honors $ATLAS_WORKFLOW_ROOT and the canonical
    # `_source_root()/workflow` default — same behavior as atlas_ui.py
    # uses at module init.
    workflow_target = _resolve_workflow_root(args.workflow_root)
    if args.workflow_root and not workflow_target.is_dir():
        sys.exit(f"--workflow-root not found: {workflow_target}")
    WORKFLOW_ROOT = workflow_target
    os.environ["ATLAS_WORKFLOW_ROOT"] = str(WORKFLOW_ROOT)

    ip_root_target: Path | None = None
    ip_root_is_active_ip = False
    if args.ip_root:
        ip_root_target = Path(args.ip_root).expanduser().resolve()
        if not ip_root_target.is_dir():
            sys.exit(f"--ip-root not found: {ip_root_target}")
        os.environ["ATLAS_IP_ROOT"] = str(ip_root_target)
        ip_root_is_active_ip = (ip_root_target / "yaml").is_dir()
        if ip_root_is_active_ip and args.ip == "default" and _ssot_export_valid_ip(ip_root_target.name):
            args.ip = ip_root_target.name

    # Propagate PROJECT_ROOT mutations BOTH ways: locally (so any
    # remaining atlas_runtime body refs see the new root) AND into atlas_ui
    # (where every route handler / module global / `_safe()` resolver
    # reads PROJECT_ROOT from). Without the _aui.PROJECT_ROOT = … write,
    # `--root` is silently ignored by /api/files, /api/soc, etc. because
    # those routes were registered in create_app() — they bind to
    # atlas_ui.PROJECT_ROOT, not this module's hydrated copy.
    from src import atlas_ui as _aui
    if args.root:
        target = Path(args.root).expanduser().resolve()
        if not target.is_dir():
            sys.exit(f"--root not found: {target}")
        os.chdir(str(target))
        PROJECT_ROOT = target
        _aui.PROJECT_ROOT = target
    elif ip_root_target is not None:
        if ip_root_is_active_ip:
            os.chdir(str(ip_root_target.parent))
            PROJECT_ROOT = ip_root_target.parent
            _aui.PROJECT_ROOT = ip_root_target.parent
        else:
            os.chdir(str(ip_root_target))
            PROJECT_ROOT = ip_root_target
            _aui.PROJECT_ROOT = ip_root_target
    else:
        target = default_atlas_root(os.environ)
        target.mkdir(parents=True, exist_ok=True)
        os.chdir(str(target))
        PROJECT_ROOT = target
        _aui.PROJECT_ROOT = target
    # Same back-write for WORKFLOW_ROOT (mutated earlier in this function).
    _aui.WORKFLOW_ROOT = WORKFLOW_ROOT
    # Always export PROJECT_ROOT to the env so workers, sub-agents, and
    # the system-prompt header injector resolve to the same path the UI
    # serves files from — even when the user launches without --root and
    # relies on the cwd default.
    os.environ["ATLAS_ROOT"] = str(PROJECT_ROOT)
    os.environ["ATLAS_PROJECT_ROOT"] = str(PROJECT_ROOT)
    os.environ.setdefault("ATLAS_WORKFLOW_ROOT", str(WORKFLOW_ROOT))
    workspace_session = (
        str(args.workspace_session or "").strip()
        or os.environ.get("ATLAS_WORKSPACE_SESSION", "").strip()
        or os.environ.get("ATLAS_SESSION_ID", "").strip()
        or "default"
    )
    new_session = f"{args.session_id}/{workspace_session}/{args.ip}/{args.workflow}"
    initial_context = AtlasContext(
        user_name=args.session_id,
        workspace_session=workspace_session,
        ip_name=args.ip,
        workflow=args.workflow,
        atlas_root=PROJECT_ROOT,
    )
    ip_workflow_root = initial_context.workflow_root
    if ip_workflow_root.is_dir():
        WORKFLOW_ROOT = ip_workflow_root
        _aui.WORKFLOW_ROOT = WORKFLOW_ROOT
        os.environ["ATLAS_WORKFLOW_ROOT"] = str(WORKFLOW_ROOT)
    os.environ["ATLAS_IP_ROOT"] = str(initial_context.ip_root)
    _atlas_active_session_cv.set(new_session)
    _atlas_active_ip_cv.set(args.ip)
    os.environ["ATLAS_CONTEXT_KEY"] = new_session
    os.environ["ATLAS_WORKSPACE_SESSION"] = workspace_session
    os.environ["ATLAS_SESSION_ID"] = workspace_session
    _sync_env_to_context()
    os.environ.setdefault("ATLAS_DEFAULT_SESSION_ID", args.session_id)
    os.environ.setdefault("ATLAS_DEFAULT_WORKFLOW", args.workflow)
    if current_exec_mode(os.environ) == EXEC_MODE_ORCHESTRATOR:
        from src.orchestrator.profile import (
            ORCHESTRATOR_MODEL,
            ORCHESTRATOR_REASONING_EFFORT,
            orchestrator_env,
        )

        os.environ.update(orchestrator_env())
        _set_runtime_model(ORCHESTRATOR_MODEL)
        _set_runtime_reasoning_effort(ORCHESTRATOR_REASONING_EFFORT)
        if args.model and args.model.strip() != ORCHESTRATOR_MODEL:
            print(
                f"[atlas_ui] orchestrator model is fixed at {ORCHESTRATOR_MODEL}; "
                f"ignoring --model {args.model!r}",
                file=sys.stderr,
            )
        try:
            _arg_effort_norm = _normalize_reasoning_effort(args.effort) if args.effort else ""
        except ValueError:
            _arg_effort_norm = (args.effort or "").strip()
        if args.effort and _arg_effort_norm != ORCHESTRATOR_REASONING_EFFORT:
            print(
                f"[atlas_ui] orchestrator reasoning effort is fixed at "
                f"{ORCHESTRATOR_REASONING_EFFORT}; ignoring --effort {args.effort!r}",
                file=sys.stderr,
            )
    else:
        orchestrator_model = (
            (args.model or "").strip()
            or os.environ.get("ATLAS_ORCHESTRATOR_MODEL", "").strip()
            or os.environ.get("ATLAS_MODEL", "").strip()
        )
        if orchestrator_model:
            _set_runtime_model(orchestrator_model)
        orchestrator_effort = (
            (args.effort or "").strip()
            or os.environ.get("ATLAS_ORCHESTRATOR_REASONING_EFFORT", "").strip()
            or os.environ.get("ATLAS_REASONING_EFFORT", "").strip()
        )
        if orchestrator_effort:
            try:
                _set_runtime_reasoning_effort(_normalize_reasoning_effort(orchestrator_effort))
            except ValueError:
                print(f"[atlas_ui] ignoring unknown reasoning effort: {orchestrator_effort}", file=sys.stderr)
    _assert_bind_target_available(args.host, args.port, "ATLAS UI")
    if args.admin:
        _launch_admin_server(args.admin, args.admin_host or args.host)
    run_atlas_ui(port=args.port, host=args.host)

def _source_root() -> Path:
    """Read _source_root() from atlas_ui dynamically (deferred, avoids circular)."""
    try:
        from src.atlas_ui import SOURCE_ROOT
        return SOURCE_ROOT
    except Exception:
        return Path(__file__).resolve().parent.parent

def _resolve_workflow_root(raw: str | Path | None = None) -> Path:
    """Resolve the directory that contains workflow families.

    Accept either the workflow directory itself (`.../workflow`) or the
    common_ai_agent source root (`.../common_ai_agent`). This lets CLI/env
    callers pass the most obvious path without making every script guess.
    """
    value = str(raw or os.environ.get("ATLAS_WORKFLOW_ROOT") or "").strip()
    base = Path(os.path.expandvars(value)).expanduser() if value else _source_root() / "workflow"
    if not base.is_absolute():
        base = _source_root() / base
    if (base / "ssot-gen").exists() or base.name == "workflow":
        return base.resolve()
    nested = base / "workflow"
    if (nested / "ssot-gen").exists():
        return nested.resolve()
    return base.resolve()


if __name__ == "__main__":
    main()
