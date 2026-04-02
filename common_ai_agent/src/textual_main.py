"""
src/textual_main.py — Textual TUI entry point for common_ai_agent

Usage:
    python src/textual_main.py

Terminal mode (unchanged):
    python src/main.py
"""

import os
import sys

# ── Path setup (identical to main.py) ──────────────────────────────────────
_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_script_dir)
sys.path.insert(0, _script_dir)
sys.path.insert(0, _project_root)

_vendor_dir = os.path.join(_project_root, "vendor")
if _vendor_dir not in sys.path:
    sys.path.insert(0, _vendor_dir)

# ── Textual availability check ──────────────────────────────────────────────
try:
    import textual  # noqa: F401
except ImportError:
    print("ERROR: Textual is not installed.  Run:  pip install textual")
    sys.exit(1)

# ── Import agent ────────────────────────────────────────────────────────────
import config
import main as _agent

from lib.textual_ui import AgentTUI


# ---------------------------------------------------------------------------
# Agent runner — called in AgentTUI worker thread
# ---------------------------------------------------------------------------

def _run_agent(input_fn, emit_content_fn, emit_reasoning_fn, emit_todo_fn):
    """Wire Textual callbacks into main.py and start chat_loop()."""
    # Disable prompt_toolkit (conflicts with Textual)
    config.ENABLE_MULTILINE_INPUT = False

    # Set module-level callbacks — picked up when chat_loop() creates _loop_deps
    # and when run_react_agent() creates ReactLoopDeps
    _agent._textual_input_fn = input_fn
    _agent._textual_emit_content_fn = emit_content_fn
    _agent._textual_emit_reasoning_fn = emit_reasoning_fn
    _agent._textual_emit_todo_fn = emit_todo_fn

    _agent.chat_loop()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    AgentTUI(_run_agent).run()
