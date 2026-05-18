"""Per-stage retry budget tracker for the orchestrator.

Phase 4: the orchestrator can fan out repeated dispatches to a worker (e.g.
``rtl-gen`` after sim mismatch routes to it). Without a budget the LLM can
ride the hard caps (50 steps / 30 min) and never produce a clean blocked
state. The per-stage budgets here let ``dispatch_workflow`` refuse the
(N+1)th call to a stage and surface a clean signal to the LLM so it routes
to ``ask_user`` or escalates.

Defaults mirror ``workflow/orchestrator/system_prompt.md:65-73``:

    ssot-gen     3
    rtl-gen      5
    tb-gen       3
    sim          2
    sim_debug    1
    coverage     2
    goal-audit   1

Stages not in the table get a generous default of 4 retries.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Dict


_DEFAULT_BUDGETS: Dict[str, int] = {
    "ssot-gen": 3,
    "rtl-gen": 5,
    "tb-gen": 3,
    "sim": 2,
    "sim_debug": 1,
    "coverage": 2,
    "goal-audit": 1,
    # Synthesis / timing / place-and-route: conservative defaults.
    "syn": 3,
    "sta": 2,
    "pnr": 2,
    "sta-post": 2,
    # Stages not in this table get the fallback below.
}
_FALLBACK_BUDGET = 4


def default_budget_for(workflow: str) -> int:
    return _DEFAULT_BUDGETS.get(workflow, _FALLBACK_BUDGET)


@dataclass
class BudgetTracker:
    """Thread-safe per-stage retry counter scoped to one orchestrator_run.

    ``attempt(workflow)`` records one attempt and returns whether it's
    allowed. After exhaustion subsequent calls return ``allowed=False`` until
    ``reset(workflow)`` is called (e.g. when the stage finally passes).
    """

    overrides: Dict[str, int] = field(default_factory=dict)
    _counts: Dict[str, int] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def budget_for(self, workflow: str) -> int:
        if workflow in self.overrides:
            return int(self.overrides[workflow])
        return default_budget_for(workflow)

    def attempts(self, workflow: str) -> int:
        with self._lock:
            return int(self._counts.get(workflow, 0))

    def attempt(self, workflow: str) -> Dict[str, object]:
        """Record one dispatch attempt for ``workflow``.

        Returns a dict ``{allowed, attempts, budget, workflow}`` where
        ``allowed`` is False once the attempt count exceeds the budget.
        """
        if not workflow:
            return {"allowed": True, "attempts": 0, "budget": 0, "workflow": ""}
        budget = self.budget_for(workflow)
        with self._lock:
            new_count = self._counts.get(workflow, 0) + 1
            self._counts[workflow] = new_count
        return {
            "allowed": new_count <= budget,
            "attempts": new_count,
            "budget": budget,
            "workflow": workflow,
        }

    def reset(self, workflow: str) -> None:
        """Reset the counter for one workflow (e.g. on successful evidence)."""
        with self._lock:
            self._counts.pop(workflow, None)

    def snapshot(self) -> Dict[str, int]:
        with self._lock:
            return dict(self._counts)
