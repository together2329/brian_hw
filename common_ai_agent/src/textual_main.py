"""
src/textual_main.py — Textual TUI entry point for common_ai_agent

Usage:
    python src/textual_main.py

Terminal mode (unchanged):
    python src/main.py
"""

from __future__ import annotations

import os
import sys

# ── Path setup ──────────────────────────────────────────────────────────────
try:
    _script_dir = os.path.dirname(os.path.abspath(__file__))
except (OSError, FileNotFoundError):
    # CWD no longer exists (e.g. deleted dir) — fall back to argv[0]
    _script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
_project_root = os.path.dirname(_script_dir)
sys.path.insert(0, _script_dir)
sys.path.insert(0, _project_root)

_vendor_dir = os.path.join(_project_root, "vendor")
if _vendor_dir not in sys.path:
    sys.path.insert(0, _vendor_dir)

# ── Python 3.7 compatibility: backport typing helpers via typing_extensions ──
if sys.version_info < (3, 8):
    import typing
    try:
        import typing_extensions as _te
        for _attr in ("get_args", "get_origin", "Literal", "Protocol",
                      "TypedDict", "Final", "Annotated", "get_type_hints"):
            if not hasattr(typing, _attr) and hasattr(_te, _attr):
                setattr(typing, _attr, getattr(_te, _attr))
    except ImportError:
        pass

# Increase escape-sequence timeout to 1000ms (ncurses standard default).
# When moving a cmux tab or terminal window, focus/resize escape sequences
# (\x1b[O, \x1b[8;...t, etc.) can arrive in chunks with >100ms gaps.
# Textual's default 100ms ESCAPE_DELAY fires spurious ESC in those gaps.
# Force-set (not setdefault) so existing env values don't override this.
os.environ["ESCDELAY"] = "300"

try:
    import textual  # noqa: F401
    _TEXTUAL_OK = True
except Exception as e:
    print(f"[warn] Textual unavailable ({e}) - falling back to terminal mode.")
    _TEXTUAL_OK = False

import config
import main as _agent

# Enable Windows Virtual Terminal Processing early for Textual entry point.
# (display.py also auto-enables on import, but this guarantees coverage
# even if import order changes.)
from lib.display import enable_windows_virtual_terminal
enable_windows_virtual_terminal()

if _TEXTUAL_OK:
    from lib.textual_ui import AgentTUI, ContextUpdate


# ── Context info helper ───────────────────────────────────────────────────────

def _emit_context(app: AgentTUI, estimated_tokens: int = 0, max_tok_override: int = 0) -> None:
    """Read current token/skill state from main.py and post ContextUpdate.

    estimated_tokens: pre-computed estimate to use when last_input_tokens == 0
                      (e.g. after /clear or /compact before the next LLM call).
    """
    try:
        _last   = getattr(_agent.llm_client, "last_input_tokens", 0)
        # Use actual API tokens when available; fall back to caller-supplied estimate
        # so /clear and /compact reflect the new token count immediately.
        tokens  = _last if _last > 0 else estimated_tokens
        max_tok = max_tok_override or getattr(config, "MAX_CONTEXT_TOKENS", 128000)
        # Sync active model — use get_active_model() so cursor-agent shows "Cursor (Auto)"
        try:
            from src.llm_client import get_active_model as _get_active_model
            _m = _get_active_model()
        except Exception:
            _m = getattr(config, "MODEL_NAME", "")
        app._active_model = _m or app._active_model
        app._refresh_model_sidebar()
        fn      = getattr(_agent, "load_active_skills", None)
        forced  = getattr(fn, "forced_skills", set()) or set()
        active_list = getattr(fn, "active_skills", []) or []
        auto    = getattr(fn, "_active_skill", None)

        # Priority: active_skills (final merged, set after each LLM call)
        #           > forced_skills (user-explicit)
        #           > _active_skill (auto-routed)
        names: list[str] = []
        if active_list:
            names = list(active_list)
        elif forced:
            names = sorted(forced)
        elif auto:
            names = [auto]

        if len(names) > 2:
            skill = f"{names[0]}, +{len(names)-1}"
        else:
            skill = ", ".join(names)

        mode = "plan" if os.environ.get("PLAN_MODE") == "true" else "normal"

        # Don't overwrite sidebar with 0 — keep _init_sidebar estimate until
        # the first real LLM call provides an actual token count.
        if tokens > 0:
            app.post_message(ContextUpdate(tokens, max_tok, skill, mode))
        elif skill:
            # No token data yet, but skill changed — update skill display only
            app.post_message(ContextUpdate(app._ctx_tokens, max_tok, skill, mode))
        elif mode != getattr(app, "_ctx_mode", "normal"):
            # Mode changed without token/skill update — emit to sync mode display
            app.post_message(ContextUpdate(app._ctx_tokens, max_tok, app._ctx_skill, mode))
    except Exception:
        pass


# ── Agent runner ──────────────────────────────────────────────────────────────

def _run_agent(app: AgentTUI) -> None:
    """Called inside the AgentTUI worker thread."""
    config.ENABLE_MULTILINE_INPUT = False

    from lib.textual_ui import StreamChunk, ReasoningChunk, TodoUpdate, FlushResponse, TokenUsage, AskUserRequest

    def _todo_and_context(text: str) -> None:
        app.post_message(TodoUpdate(text))
        _emit_context(app)

    _agent._textual_input_fn          = app._input_bridge.get_input
    _agent._textual_emit_content_fn   = lambda line: app.post_message(StreamChunk(line))
    _agent._textual_emit_reasoning_fn = lambda line, blank=False: app.post_message(ReasoningChunk(line, blank))
    _agent._textual_emit_todo_fn      = _todo_and_context
    _agent._textual_emit_flush_fn     = lambda: app.post_message(FlushResponse())
    _agent._textual_emit_context_fn   = lambda tok, max_tok: _emit_context(app, tok, max_tok)
    _agent._textual_emit_token_fn     = lambda in_tok, cache_tok, out_tok: app.post_message(TokenUsage(in_tok, cache_tok, out_tok))
    _agent._textual_esc_check_fn          = app.check_and_reset_interrupt
    _agent._textual_poll_human_input_fn   = app._input_bridge.poll_interrupt

    # Set agent_running flag so input routing knows to use interrupt queue
    def _set_agent_running(val: bool):
        app._input_bridge.agent_running = val

    _agent._textual_set_agent_running_fn = _set_agent_running

    # ── ask_user → Textual modal ────────────────────────────────────
    # Each ask_user call pushes an AskUserModal screen; the agent thread
    # blocks on a per-flow queue until the user submits or cancels.
    # Multiple ask_user calls within one agent turn stack naturally —
    # Textual processes push_screen sequentially.
    import queue as _queue
    import uuid as _uuid

    def _format_answer(ans: dict, options: list) -> str:
        selected_ids = ans.get("selected") or []
        custom = (ans.get("custom") or "").strip()
        label_by_id = {o.get("id"): o.get("label", o.get("id")) for o in options or []}
        labels = [label_by_id.get(sid, sid) for sid in selected_ids]
        parts = []
        if labels: parts.append("selected: " + ", ".join(labels))
        if custom: parts.append("note: " + custom)
        return " · ".join(parts) if parts else "(user submitted with no selection)"

    def _ask_user_textual(question, options, kind, subtitle, questions=None):
        flow_id = "qa_" + _uuid.uuid4().hex[:10]
        answer_q: _queue.Queue = _queue.Queue()
        app.post_message(AskUserRequest(
            flow_id=flow_id, question=question, kind=kind,
            subtitle=subtitle or "", options=options or [],
            answer_q=answer_q, questions=questions,
        ))
        try:
            ans = answer_q.get(timeout=900)  # 15 min ceiling
        except _queue.Empty:
            return "[ask_user: no answer received within 15 min]"
        # Cancel-all from the user — match Claude Code's wording so the
        # agent recognizes this consistent signal.
        if ans.get("type") == "cancel":
            return "User declined to answer questions"
        # Batched response: list of per-question answers.
        if questions and "answers" in ans:
            blocks = []
            for q, qa in zip(questions, ans.get("answers") or []):
                label = (q.get("subtitle") or q.get("question", ""))[:40]
                blocks.append(f"  • {label}\n    {_format_answer(qa, q.get('options'))}")
            return "Batched answers:\n" + "\n".join(blocks) if blocks else "(no answers)"
        return _format_answer(ans, options or [])

    try:
        from core import tools as _tools
        if hasattr(_tools, "set_ask_user_callback"):
            _tools.set_ask_user_callback(_ask_user_textual)
    except Exception as _e:
        print(f"[warn] ask_user callback registration failed: {_e}")

    _agent.chat_loop()
    # After chat_loop finishes, the conversation history has been saved.
    # Now signal the app to close cleanly.
    app.exit()


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse as _argparse
    _parser = _argparse.ArgumentParser(
        prog="textual_main",
        description="common_ai_agent launcher — picks textual / atlas / web UI",
        add_help=True,
    )
    _parser.add_argument('-s', '--session', default=None)
    _parser.add_argument('-w', '--workspace', default=None,
                         help='Workspace name (e.g. ssot-gen, rtl-gen, sim, lint)')
    _parser.add_argument('-u', '--ui', default=None,
                         choices=['textual', 'atlas', 'web'],
                         help='UI mode (overrides UI_MODE in .config). '
                              'textual = terminal TUI, atlas = React/WebSocket browser UI, '
                              'web = legacy SSE browser UI')
    _parser.add_argument('--port', type=int, default=None,
                         help='Override port for atlas/web UI '
                              '(defaults to ATLAS_UI_PORT=8765 / WEB_UI_PORT=8080)')
    _args, _ = _parser.parse_known_args()

    _session_name = _args.session or _args.workspace or 'default'
    _agent._setup_session(_session_name)

    # Apply workspace if specified (same as main.py -w)
    if _args.workspace:
        try:
            _agent._setup_workspace(_args.workspace)
        except Exception as _e:
            print(f"[warn] Workspace '{_args.workspace}' failed to load: {_e}")

    # ── UI Mode routing ────────────────────────────────────────────────────
    # Priority: --ui CLI flag > UI_MODE env/config > "textual" default.
    _ui_mode = (_args.ui or getattr(config, "UI_MODE", "textual")).lower()
    _web_port   = _args.port or getattr(config, "WEB_UI_PORT", 8080)
    _atlas_port = _args.port or getattr(config, "ATLAS_UI_PORT", 8765)

    if _ui_mode == "atlas":
        from src.atlas_ui import run_atlas_ui
        run_atlas_ui(port=_atlas_port)
    elif _ui_mode == "web":
        from src.web_ui import run_web_ui
        run_web_ui(port=_web_port)
    elif _TEXTUAL_OK:
        from lib.textual_ui import AgentTUI, ContextUpdate
        AgentTUI(_run_agent).run()
    else:
        print("[fallback] Running in terminal mode (src/main.py).")
        _agent.chat_loop()
