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
_script_dir = os.path.dirname(os.path.abspath(__file__))
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
        max_tok = getattr(config, "MAX_CONTEXT_CHARS", 512000) // 4
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

        app.post_message(ContextUpdate(tokens, max_tok, skill))
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

    _agent.chat_loop()


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if _TEXTUAL_OK:
        from lib.textual_ui import AgentTUI, ContextUpdate
        AgentTUI(_run_agent).run()
        # Force-kill all remaining threads (LLM HTTP, tool subprocesses, ThreadPoolExecutor)
        import os as _os
        _os._exit(0)
    else:
        # Fallback: plain terminal mode
        print("[fallback] Running in terminal mode (src/main.py).")
        _agent.chat_loop()
