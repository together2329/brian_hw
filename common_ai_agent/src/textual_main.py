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

try:
    import textual  # noqa: F401
except ImportError:
    print("ERROR: Textual is not installed.  Run:  pip install textual")
    sys.exit(1)

import config
import main as _agent

from lib.textual_ui import AgentTUI, ContextUpdate


# ── Context info helper ───────────────────────────────────────────────────────

def _emit_context(app: AgentTUI) -> None:
    """Read current token/skill state from main.py and post ContextUpdate."""
    try:
        tokens  = getattr(_agent.llm_client, "last_input_tokens", 0)
        max_tok = getattr(config, "MAX_CONTEXT_TOKENS", 65536)
        fn = getattr(_agent, "load_active_skills", None)
        active  = getattr(fn, "_active_skill", None)
        forced  = getattr(fn, "forced_skills", set())
        # Show forced skills (set by /skills enable/all) or auto-routed skill
        all_active = sorted(forced) + ([active] if active and active not in forced else [])
        skill = ", ".join(all_active) if all_active else ""
        app.post_message(ContextUpdate(tokens, max_tok, skill))
    except Exception:
        pass


# ── Agent runner ──────────────────────────────────────────────────────────────

def _run_agent(app: AgentTUI) -> None:
    """Called inside the AgentTUI worker thread."""
    config.ENABLE_MULTILINE_INPUT = False

    from lib.textual_ui import StreamChunk, ReasoningChunk, TodoUpdate

    def _todo_and_context(text: str) -> None:
        app.post_message(TodoUpdate(text))
        _emit_context(app)

    _agent._textual_input_fn          = app._input_bridge.get_input
    _agent._textual_emit_content_fn   = lambda line: app.post_message(StreamChunk(line))
    _agent._textual_emit_reasoning_fn = lambda line, blank=False: app.post_message(ReasoningChunk(line, blank))
    _agent._textual_emit_todo_fn      = _todo_and_context

    _agent.chat_loop()


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    AgentTUI(_run_agent).run()
