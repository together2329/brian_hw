"""
src/textual_main.py — Textual TUI entry point for common_ai_agent

Usage:
    python src/textual_main.py

Terminal mode (unchanged):
    python src/main.py
"""

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
import os as _os
_os.environ["ESCDELAY"] = "1000"

try:
    import textual  # noqa: F401
    _TEXTUAL_OK = True
except Exception as e:
    print(f"[warn] Textual unavailable ({e}) — falling back to terminal mode.")
    _TEXTUAL_OK = False

import config
import main as _agent

if _TEXTUAL_OK:
    from lib.textual_ui import AgentTUI, ContextUpdate


# ── Context info helper ───────────────────────────────────────────────────────

def _emit_context(app: AgentTUI) -> None:
    """Read current token/skill state from main.py and post ContextUpdate."""
    try:
        tokens  = getattr(_agent.llm_client, "last_input_tokens", 0)
        max_tok = getattr(config, "MAX_CONTEXT_TOKENS", 128000)
        # Sync active model from config (may have changed via /model switch)
        app._active_model = getattr(config, "MODEL_NAME", "") or app._active_model
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

    from lib.textual_ui import StreamChunk, ReasoningChunk, TodoUpdate, FlushResponse

    def _todo_and_context(text: str) -> None:
        app.post_message(TodoUpdate(text))
        _emit_context(app)

    _agent._textual_input_fn          = app._input_bridge.get_input
    _agent._textual_emit_content_fn   = lambda line: app.post_message(StreamChunk(line))
    _agent._textual_emit_reasoning_fn = lambda line, blank=False: app.post_message(ReasoningChunk(line, blank))
    _agent._textual_emit_todo_fn      = _todo_and_context
    _agent._textual_emit_flush_fn     = lambda: app.post_message(FlushResponse())
    _agent._textual_emit_context_fn   = lambda tok, max_tok: _emit_context(app)
    _agent._textual_esc_check_fn     = app.check_and_reset_interrupt

    _agent.chat_loop()
    # After chat_loop finishes, the conversation history has been saved.
    # Now signal the app to close cleanly.
    app.exit()


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse as _argparse
    _parser = _argparse.ArgumentParser(add_help=False)
    _parser.add_argument('-s', '--session', default='default')
    _parser.add_argument('-w', '--workspace', default=None,
                         help='Workspace name (e.g. mas_gen, rtl_gen, sim, lint)')
    _args, _ = _parser.parse_known_args()

    _agent._setup_session(_args.session)

    # Apply workspace if specified (same as main.py -w)
    if _args.workspace:
        try:
            _agent._setup_workspace(_args.workspace)
        except Exception as _e:
            print(f"[warn] Workspace '{_args.workspace}' failed to load: {_e}")

    if _TEXTUAL_OK:
        from lib.textual_ui import AgentTUI, ContextUpdate
        AgentTUI(_run_agent).run()
        # Clean exit: history is saved by Agent runner, then app.exit() is called.
    else:
        # Fallback: plain terminal mode
        print("[fallback] Running in terminal mode (src/main.py).")
        _agent.chat_loop()
