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
    contract-reflection 2
    goal-audit   1

Stages not in the table get a generous default of 4 retries.
"""

from __future__ import annotations

import os
import threading
from dataclasses import dataclass, field
from typing import Dict


def _env_budget_overrides() -> Dict[str, int]:
    """Per-stage budget overrides from env: ATLAS_ORCH_BUDGET_<WORKFLOW>=<n>.

    e.g. ATLAS_ORCH_BUDGET_SIM_DEBUG=4 raises sim_debug's retry budget. The
    name is matched in both dashed and underscored forms so 'sim-debug' and
    'sim_debug' both resolve.
    """
    out: Dict[str, int] = {}
    prefix = "ATLAS_ORCH_BUDGET_"
    for key, val in os.environ.items():
        if not key.startswith(prefix):
            continue
        wf = key[len(prefix):].strip().lower()
        if not wf:
            continue
        try:
            n = int(str(val).strip())
        except (TypeError, ValueError):
            continue
        out[wf] = n
        out[wf.replace("_", "-")] = n
        out[wf.replace("-", "_")] = n
    return out


_DEFAULT_BUDGETS: Dict[str, int] = {
    "ssot-gen": 3,
    "rtl-gen": 5,
    "tb-gen": 3,
    "sim": 2,
    "sim_debug": 1,
    "coverage": 2,
    "goal-audit": 1,
    "contract-reflection": 2,
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

    overrides: Dict[str, int] = field(default_factory=_env_budget_overrides)
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
