"""Unit tests for workflow/sim_debug/elab.py::enclosing_conditions — the
condition-aware structural annotation behind `sim_debug trace` (find where a
signal is assigned UNDER which condition). The eval is concrete: a canonical
timer always-block must yield the exact condition path for each count_q driver.
"""
from __future__ import annotations

import importlib.util as ilu
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
_spec = ilu.spec_from_file_location(
    "sim_debug_elab_under_test", REPO / "workflow" / "sim_debug" / "elab.py")
elab = ilu.module_from_spec(_spec)
_spec.loader.exec_module(elab)  # type: ignore[union-attr]


TIMER_BLOCK = """always_ff @(posedge clk or negedge presetn) begin
  if (!presetn) begin
    count_q <= '0;
  end else begin
    wrap_o <= 1'b0;
    if (!enable_i || (period_i == {DATA_WIDTH{1'b0}})) begin
      count_q <= count_q;
    end else begin
      if (tick) begin
        if (wrap_next) begin
          count_q <= {DATA_WIDTH{1'b0}};
        end else begin
          count_q <= count_q + 1;
        end
      end
    end
  end
end"""


def _conds_for(block, needle):
    cmap = elab.enclosing_conditions(block)
    for off, ln in enumerate(block.split("\n")):
        if needle in ln:
            return cmap[off]
    raise AssertionError(f"line not found: {needle}")


def test_enclosing_conditions_timer_core_count_q():
    enable_cond = "!enable_i || (period_i == {DATA_WIDTH{1'b0}})"
    # reset branch
    assert _conds_for(TIMER_BLOCK, "count_q <= '0") == ["!presetn"]
    # hold branch (else of reset, then the enable/period guard)
    assert _conds_for(TIMER_BLOCK, "count_q <= count_q;") == ["!(!presetn)", enable_cond]
    # wrap branch: not-reset, not-guard, tick, wrap_next
    assert _conds_for(TIMER_BLOCK, "count_q <= {DATA_WIDTH{1'b0}}") == [
        "!(!presetn)", f"!({enable_cond})", "tick", "wrap_next"]
    # increment branch: not-reset, not-guard, tick, NOT wrap_next
    assert _conds_for(TIMER_BLOCK, "count_q <= count_q + 1") == [
        "!(!presetn)", f"!({enable_cond})", "tick", "!(wrap_next)"]


def test_enclosing_conditions_one_line_if():
    block = "always_comb begin\n  if (sel) y = a;\n  else y = b;\nend"
    assert _conds_for(block, "y = a;") == ["sel"]
    assert _conds_for(block, "y = b;") == ["!(sel)"]


def test_enclosing_conditions_case_item():
    block = (
        "always_comb begin\n"
        "  case (state)\n"
        "    IDLE: out = 0;\n"
        "  endcase\n"
        "end"
    )
    # the case item is captured as `sel == LABEL` (FSM state → its body)
    assert _conds_for(block, "out = 0") == ["state == IDLE"]


def test_enclosing_conditions_unconditional():
    block = "always_comb begin\n  y = a & b;\nend"
    assert _conds_for(block, "y = a & b") == []
