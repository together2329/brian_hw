"""Campaign finding 36 — FL enum state-update silent-PASS hardening.

A FunctionalModel that cannot resolve an enum-named state update such as
``fsm_state = COUNT`` used to score a vacuous PASS. Three sites independently
SEEDED the enum value NAME (``COUNT``) as a stimulus placeholder
(``txn["COUNT"] = 0``), which papered over the model's inability to resolve the
enum: the gate's ``apply()`` no longer raised, and — worse — in the runtime
scoreboard the injected ``COUNT=0`` overrode the model's own enum binding and
silently forced every FSM-state expected back to ``RESET(0)``.

The fix: declared enum value names are CONSTANTS the model must resolve from its
own encodings, never seeded as stimulus placeholders. This file guards that an
enum name is left for the model to resolve at all three sites, so an
unresolvable enum surfaces (apply() raises / FSM expected diverges) instead of
passing hollow.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

_SSOT = {
    "function_model": {
        "state_variables": [
            {"name": "count_reg", "width": 8, "reset": 0},
            {"name": "fsm_state", "width": 2, "reset": "RESET",
             "enum": ["RESET", "HOLD", "CLEAR", "COUNT"]},
        ],
    },
    "registers": {"internal_state_registers": []},
}

_TX = {
    "id": "count",
    "name": "FM_COUNT",
    "sample_condition": "rst_n == 1 and clr == 0 and en == 1",
    "output_rules": [{"name": "count_out", "port": "count", "expr": "(count_reg + 1) & 255"}],
    "state_updates": [
        {"name": "count_count_reg", "state": "count_reg", "expr": "(count_reg + 1) & 255"},
        {"name": "count_fsm_state", "state": "fsm_state", "expr": "COUNT"},
    ],
}


def _load(rel: str, name: str):
    spec = importlib.util.spec_from_file_location(name, REPO / rel)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


class _StubModel:
    """A model whose state does NOT carry the enum names — exactly the case the
    old seeding masked."""

    params: dict = {}
    state = {"fsm_state": "RESET", "count_reg": 0}
    registers: dict = {}


def test_check_fl_contract_declares_enum_names():
    gate = _load("workflow/fl-model-gen/scripts/check_fl_contract.py", "check_fl_contract_gate")
    assert gate._declared_enum_names(_SSOT) == {"RESET", "HOLD", "CLEAR", "COUNT"}
    # no enum block -> empty, never crashes
    assert gate._declared_enum_names({}) == set()


def test_check_fl_contract_self_txn_does_not_seed_enum_names():
    gate = _load("workflow/fl-model-gen/scripts/check_fl_contract.py", "check_fl_contract_gate2")
    enum_names = gate._declared_enum_names(_SSOT)
    txn = gate._self_txn(_TX, 0, _StubModel(), {}, enum_names)
    # The enum value name must be left for the model to resolve, NOT seeded as a
    # placeholder (which would let a non-resolving model pass hollow).
    assert "COUNT" not in txn
    assert "RESET" not in txn


def test_check_fl_contract_self_txn_still_seeds_real_unknown_fields():
    """The hardening must not over-reach: genuine unknown stimulus identifiers
    (not declared enum values) are still seeded so apply() stays runnable."""
    gate = _load("workflow/fl-model-gen/scripts/check_fl_contract.py", "check_fl_contract_gate3")
    tx = {
        "id": "x", "name": "x",
        "state_updates": [{"name": "u", "state": "s", "expr": "some_input_field + 1"}],
    }
    txn = gate._self_txn(tx, 0, _StubModel(), {}, set())
    assert "some_input_field" in txn  # genuine unknown stimulus field is still seeded


def test_equivalence_scoreboard_enum_helper_excludes_from_seed():
    """The runtime adapter's _declared_enum_value_names mirrors the same source
    so transaction_for_goal never injects an enum name over the model binding."""
    sys.path.insert(0, str(REPO / "workflow" / "tb-gen" / "runtime"))
    import equivalence_scoreboard as es  # noqa: E402

    class _StubModule:
        SSOT_MODEL = _SSOT

    # Bind the unbound method to a minimal object carrying model_module.
    holder = type("H", (), {"model_module": _StubModule()})()
    names = es.EquivalenceScoreboard._declared_enum_value_names(holder)
    assert names == {"RESET", "HOLD", "CLEAR", "COUNT"}
