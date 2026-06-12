"""Campaign finding 37 — resolve a goal's FL transaction by stimulus guard.

`_best_model_kind` mapped cycle_model rule-name goals (CM_PRIORITY_ENABLE,
CM_NO_VALID_READY) and bare scenario ids (SC04) to a transaction by name/text
heuristics, ignoring the en/clr/rst_n the goal actually drives. That picked the
WRONG transaction (SC04->reset, CM_PRIORITY_ENABLE->reset, CM_NO_VALID_READY->
count) so the FL expected diverged from the RTL the same stimulus produced.

Fix: when the stimulus control inputs satisfy EXACTLY ONE non-reset
transaction's guard, that is the transaction the RTL decodes — authoritative.
Ambiguous (0 or >1) returns None so the heuristics still apply, and reset-context
goals are excluded by the caller (the TB drives them under reset).
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "workflow" / "tb-gen" / "runtime"))
import equivalence_scoreboard as es  # noqa: E402

_TXS = [
    {"id": "reset", "name": "reset", "sample_condition": "rst_n == 0"},
    {"id": "count", "name": "count", "sample_condition": "rst_n == 1 and clr == 0 and en == 1"},
    {"id": "hold", "name": "hold", "sample_condition": "rst_n == 1 and clr == 0 and en == 0"},
    {"id": "clr", "name": "clr", "sample_condition": "rst_n == 1 and clr == 1"},
]


class _StubModel:
    state: dict = {}
    registers: dict = {}

    def _transactions(self):
        return _TXS

    def _eval_precondition(self, expr, env):
        try:
            return bool(eval(expr, {"__builtins__": {}}, dict(env)))
        except Exception:
            # Mirror the FL: an expr that cannot be evaluated (e.g. references a
            # field absent from the stimulus) is treated as True.
            return True


def _holder():
    h = type("H", (), {})()
    h.model = _StubModel()
    h.model_transaction_aliases = {"reset": "reset", "count": "count", "hold": "hold", "clr": "clr"}
    return h


def _resolve(stimulus):
    return es.EquivalenceScoreboard._transaction_by_stimulus_guard(_holder(), stimulus)


def test_guard_resolves_unique_count():
    assert _resolve({"en": 1, "clr": 0, "rst_n": 1}) == "count"


def test_guard_resolves_unique_hold():
    assert _resolve({"en": 0, "clr": 0, "rst_n": 1}) == "hold"


def test_guard_resolves_unique_clear():
    assert _resolve({"en": 1, "clr": 1, "rst_n": 1}) == "clr"


def test_guard_skips_reset_transaction():
    # rst_n==0 satisfies only the reset txn, which is excluded -> no non-reset
    # match -> None (reset-context goals are owned by the caller's heuristic).
    assert _resolve({"en": 0, "clr": 0, "rst_n": 0}) is None


def test_guard_returns_none_on_ambiguous_or_missing_control():
    # No control inputs at all -> cannot decode -> None.
    assert _resolve({}) is None
    # Only rst_n: count/hold/clr guards reference en/clr (absent) -> each evals
    # True under the FL's lenient rule -> >1 match -> ambiguous -> None.
    assert _resolve({"rst_n": 1}) is None
