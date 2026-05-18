"""Orchestrator loop data types.

Phase 3.5 deletion (2026-05-18): the custom ``OrchestratorLoop`` scaffold
that lived here is gone — production runs through
``src/orchestrator/react_bridge.py::OrchestratorReactLoop`` on top of
``core/react_loop.py::run_react_agent_impl``. Parity is asserted by
``tests/test_orchestrator_react_loop_parity.py``. What remains in this
module is the small set of data types other modules import:

- ``OrchestratorContext`` — per-run identity (run_id / user_id / ip_id /
  ip_name / session_id / project_root / runner).
- ``RunOutcome`` — what ``OrchestratorReactLoop.run()`` returns.
- ``FINAL_WORKFLOW`` — the ``"__final__"`` sentinel the system prompt
  instructs the LLM to emit via ``dispatch_workflow`` to declare terminal
  state.

The file deliberately has no methods/logic of its own.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


FINAL_WORKFLOW = "__final__"


@dataclass
class OrchestratorContext:
    run_id: str
    user_id: str
    ip_id: str
    ip_name: str
    session_id: str = ""
    project_root: Optional[Path] = None
    runner: Any = None  # OrchestratorRunner — opt-in waker provider


@dataclass
class RunOutcome:
    status: str
    final_state: Optional[str]
    steps_taken: int
    error: Optional[str] = None
