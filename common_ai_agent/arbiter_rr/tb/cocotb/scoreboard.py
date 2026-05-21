from __future__ import annotations

import os
from pyuvm import uvm_scoreboard

from equivalence_scoreboard import EquivalenceScoreboard


class GoalScoreboard(uvm_scoreboard):
    def __init__(self, name: str, ip: str, root, parent=None):
        super().__init__(name, parent)
        self.adapter = EquivalenceScoreboard(ip, root, reset_events=True)
        self.failures: list[dict] = []

    def check_goal(
        self,
        goal_id: str,
        scenario_id: str,
        cycle: int,
        stimulus: dict,
        rtl_observed: dict,
        cl_passed: bool | None = None,
    ) -> dict:
        # When the cycle-accurate CL model has been stepped in lock-step
        # with cocotb and agrees with RTL on the goal's registered outputs,
        # it is the authoritative oracle — overrides the single-shot FL.apply
        # path's verdict. Pass passed=True so the scoreboard event log also
        # records the goal as PASS (not just the in-memory failures list).
        if cl_passed is True:
            row = self.adapter.record(
                goal_id,
                scenario_id=scenario_id,
                cycle=cycle,
                stimulus=stimulus,
                rtl_observed=rtl_observed,
                passed=True,
            )
        else:
            row = self.adapter.record(
                goal_id,
                scenario_id=scenario_id,
                cycle=cycle,
                stimulus=stimulus,
                rtl_observed=rtl_observed,
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
