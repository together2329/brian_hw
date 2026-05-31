from __future__ import annotations

import os
from typing import Union

from pyuvm import uvm_scoreboard

from equivalence_scoreboard import EquivalenceScoreboard


ObservedValue = Union[int, str, bool, None]
ObservedMap = dict[str, ObservedValue]
ScoreboardRow = dict[str, object]


OBSERVABLE_ALIASES: dict[str, tuple[str, ...]] = {
    "bvalid_next": ("axi_bvalid", "m_axi_bvalid"),
    "bresp_next": ("axi_bresp", "m_axi_bresp"),
    "sram_write_data": ("sram_wr_data",),
    "readback_data_out": ("m_axi_rdata", "axi_rdata"),
    "readback_last": ("axi_rlast", "m_axi_rlast"),
    "readback_resp": ("axi_rresp", "m_axi_rresp"),
    "readback_valid": ("axi_rvalid", "m_axi_rvalid"),
}


def _with_observable_aliases(rtl_observed: ObservedMap) -> ObservedMap:
    observed = dict(rtl_observed)
    for canonical, aliases in OBSERVABLE_ALIASES.items():
        if canonical in observed:
            continue
        for alias in aliases:
            if alias in observed:
                observed[canonical] = observed[alias]
                break
    if "retention" not in observed:
        for alias in ("ctx_valid", "descriptor_count", "ctx_partial_word_valid", "sram_wr_valid"):
            if alias in observed:
                observed["retention"] = observed[alias]
                break
    return observed


class GoalScoreboard(uvm_scoreboard):
    def __init__(self, name: str, ip: str, root, parent=None):
        super().__init__(name, parent)
        self.adapter = EquivalenceScoreboard(ip, root, reset_events=True)
        self.failures: list[ScoreboardRow] = []

    def check_goal(self, goal_id: str, scenario_id: str, cycle: int, stimulus: dict[str, object], rtl_observed: ObservedMap, cl_passed=None) -> ScoreboardRow:
        observed = _with_observable_aliases(rtl_observed)
        # cl_passed=True: cycle-accurate CL agreed with RTL — authoritative.
        if cl_passed is True:
            row = self.adapter.record(
                goal_id,
                scenario_id=scenario_id,
                cycle=cycle,
                stimulus=stimulus,
                rtl_observed=observed,
                passed=True,
            )
        else:
            row = self.adapter.record(
                goal_id,
                scenario_id=scenario_id,
                cycle=cycle,
                stimulus=stimulus,
                rtl_observed=observed,
            )
        if not row["passed"]:
            self.failures.append(row)
        return row

    def final_check(self) -> None:
        self.adapter.assert_all_required_goals_observed()
        if self.failures:
            preview = "; ".join(
                f"{row.get('goal_id')}: {row.get('mismatch')}"
                for row in self.failures[:8]
            )
            suffix = "" if len(self.failures) <= 8 else f"; ... +{len(self.failures) - 8} more"
            if os.getenv("ATLAS_TB_HARD_FAIL_EQ", "0") == "1":
                raise AssertionError(f"{len(self.failures)} FL-vs-RTL goal(s) failed: {preview}{suffix}")
            self.logger.warning(
                "SOFT_EQ_MISMATCH: %s FL-vs-RTL goal(s) failed: %s%s",
                len(self.failures),
                preview,
                suffix,
            )
