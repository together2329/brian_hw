"""Campaign findings 33-35 — generic TB stimulus fidelity to the goal contract.

The generated cocotb TB derives each goal's input vector from name heuristics
plus the goal's stimulus_contract. Two masking defects lived in that path and
only surfaced once the TB actually drove the reset pin (finding 33):

  * finding 34 — the reset pin defaulted to a polarity-blind ``0``. For an
    active-LOW ``rst_n`` that is ASSERTED, so every functional goal silently ran
    with the DUT held in reset (count stuck at 0) while the FL oracle ignored the
    spurious field. A non-reset functional goal must present reset DEASSERTED.

  * finding 35 — ``_constraint_field_value`` only honored a fixed
    reset/valid/enable/hready/hresp vocabulary, so a locked goal constraint like
    ``clr==1 at rising clk`` was dropped and the CLEAR path never asserted. Any
    scalar control field's explicit ``<field>==<int>`` constraint must be honored.

These functions live inside the emitter's TEST_PY template (they are emitted into
the generated TB), so the test execs that template in a cocotb-stubbed namespace
and exercises the pure helpers directly.
"""
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EMIT = REPO / "workflow" / "tb-gen" / "scripts" / "emit_goal_scoreboard_cocotb.py"


def _emit_module():
    spec = importlib.util.spec_from_file_location("emit_goal_scoreboard_cocotb", EMIT)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def _tb_namespace():
    """Exec the emitted TEST_PY template with cocotb stubbed and return its
    namespace, so the pure stimulus helpers can be exercised in isolation."""
    test_py = _emit_module().TEST_PY
    cocotb = types.ModuleType("cocotb")
    cocotb.test = lambda *a, **k: (lambda fn: fn)
    binary = types.ModuleType("cocotb.binary")
    binary.BinaryValue = object
    clock = types.ModuleType("cocotb.clock")
    clock.Clock = object
    triggers = types.ModuleType("cocotb.triggers")
    for name in ("ReadOnly", "RisingEdge", "Timer"):
        setattr(triggers, name, object)
    saved = {k: sys.modules.get(k) for k in
             ("cocotb", "cocotb.binary", "cocotb.clock", "cocotb.triggers")}
    sys.modules.update({"cocotb": cocotb, "cocotb.binary": binary,
                        "cocotb.clock": clock, "cocotb.triggers": triggers})
    try:
        ns: dict = {}
        exec(compile(test_py, "<TEST_PY>", "exec"), ns)
        return ns
    finally:
        for k, v in saved.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v


_MANIFEST = {
    "ip": "cnt8_en_v1",
    "clock": "clk",
    "reset": "rst_n",
    "reset_active": "low",
    "input_map": {"rst_n": "rst_n", "en": "en", "clr": "clr"},
    "input_ports": ["clk", "rst_n", "en", "clr"],
    "sample_inputs": [],
    "outputs": [],
}


def _goal(constraints):
    return {"goal_id": "G", "kind": "transaction",
            "stimulus_contract": {"constraints": list(constraints)}}


def test_reset_field_defaults_to_deasserted_for_active_low():
    ns = _tb_namespace()
    fn = ns["_stimulus_value_for_field"]
    # COUNT goal: constrains en/clr, says nothing about rst_n -> reset must be
    # DEASSERTED (1 for active-low), never the polarity-blind 0 (asserted).
    goal = _goal(["en==1 && clr==0 at rising clk per BC."])
    assert fn(_MANIFEST, "rst_n", 0, goal) == 1


def test_reset_field_deasserted_is_zero_for_active_high():
    ns = _tb_namespace()
    fn = ns["_stimulus_value_for_field"]
    manifest = dict(_MANIFEST, reset="rst", reset_active="high",
                    input_map={"rst": "rst", "en": "en"})
    goal = _goal(["en==1"])
    assert fn(manifest, "rst", 0, goal) == 0


def test_clear_constraint_asserts_clr():
    ns = _tb_namespace()
    cval = ns["_constraint_field_value"]
    goal = _goal(["clr==1 at rising clk, any en per BC-CNT8_EN_V1-CLR."])
    assert cval(_MANIFEST, goal, "clr") == 1


def test_count_constraint_holds_clr_low():
    ns = _tb_namespace()
    cval = ns["_constraint_field_value"]
    goal = _goal(["en==1 && clr==0 at rising clk per BC."])
    assert cval(_MANIFEST, goal, "clr") == 0
    assert cval(_MANIFEST, goal, "en") == 1


def test_generic_constraint_does_not_overmatch_substring_field():
    ns = _tb_namespace()
    cval = ns["_constraint_field_value"]
    # "len==5" must NOT be read as field "en" == ... ; en is unconstrained here.
    goal = _goal(["len==5 and clr==1"])
    assert cval(_MANIFEST, goal, "en") is None
    assert cval(_MANIFEST, goal, "clr") == 1
