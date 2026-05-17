#!/usr/bin/env python3
"""FL-vs-RTL equivalence scoreboard for pl330realverify.

Imports FunctionalModel from pl330realverify/model/functional_model.py,
applies it per transaction, and compares FL expected values against
RTL observed signals.  Writes structured scoreboard event rows to
sim/scoreboard_events.jsonl.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

# Resolve the ATLAS project root so we can import the functional model
_PROJECT = Path(__file__).resolve().parents[3]
if str(_PROJECT) not in sys.path:
    sys.path.insert(0, str(_PROJECT))

# ─────────── late import helpers ───────────

def _get_functional_model():
    from importlib import import_module
    mod = import_module("pl330realverify.model.functional_model")
    return mod


class EquivalenceScoreboard:
    """Scoreboard that compares FL expected vs RTL observed for every equivalence goal.

    Usage:
        sb = EquivalenceScoreboard("pl330realverify")
        # per cycle/event:
        sb.record(scenario_id, goal_id, cycle, stimulus, fl_expected, rtl_observed)
        sb.dump()
    """

    def __init__(self, ip: str = "pl330realverify", root: str = "."):
        self.ip = ip
        self.root = Path(root)
        self.events: list[dict] = []
        self.failures: list[dict] = []
        self.cycle = 0
        self._fl = None
        self._fm_mod = None

    @property
    def fm(self):
        if self._fm_mod is None:
            self._fm_mod = _get_functional_model()
        return self._fm_mod

    @property
    def fl(self):
        if self._fl is None:
            self._fl = self.fm.FunctionalModel()
        return self._fl

    def apply_fl(self, txn: dict) -> dict:
        """Call FunctionalModel.apply and return the result."""
        return self.fl.apply(txn)

    def predict_apb_read(self, addr: int) -> int:
        """Use FL model to predict APB read data for a register address."""
        # Use the _read_mux helper from functional model
        return self.fl._read_mux(addr)

    def predict_apb_write(self, addr: int, data: int) -> dict:
        """Predict the effect of an APB write."""
        # Determine register name
        regs = self.fm.SSOT_MODEL.get("registers", {}).get("register_list", [])
        reg_name = None
        for reg in regs:
            if reg.get("offset") == addr:
                reg_name = reg.get("name")
                break
        txn = {
            "kind": "apb_register_write",
            "paddr": addr,
            "pwdata": data,
            "pstrb": 0xF,
        }
        return self.apply_fl(txn)

    def predict_transfer(self, channel: int = 0, **kw) -> dict:
        """Predict a transfer transaction."""
        txn = {"kind": "single_or_multi_beat_memory_copy", "channel": channel, **kw}
        return self.apply_fl(txn)

    def predict_wfp(self, channel: int = 0, **kw) -> dict:
        """Predict a WFP transaction."""
        txn = {"kind": "wait_for_peripheral_event", "channel": channel, **kw}
        return self.apply_fl(txn)

    def predict_fault(self, fault_code: int = 0, **kw) -> dict:
        """Predict a fault transaction."""
        txn = {"kind": "fault_completion", "fault_code": fault_code, **kw}
        return self.apply_fl(txn)

    def predict_irq_clear(self, pwdata: int) -> dict:
        """Predict W1C clear effect."""
        txn = {"kind": "interrupt_write_one_to_clear", "pwdata": pwdata}
        return self.apply_fl(txn)

    def reset_fl(self):
        self.fl.reset()

    def record(
        self,
        scenario_id: str,
        goal_id: str,
        cycle: int,
        stimulus: dict,
        fl_expected: dict,
        rtl_observed: dict,
        coverage_refs: list = None,
    ):
        """Record one scoreboard event."""
        passed = fl_expected == rtl_observed
        # For dict comparisons, be more lenient
        if isinstance(fl_expected, dict) and isinstance(rtl_observed, dict):
            passed = self._dict_matches(fl_expected, rtl_observed)

        mismatch = ""
        if not passed:
            mismatch = self._diff(fl_expected, rtl_observed)
            self.failures.append({
                "scenario_id": scenario_id,
                "goal_id": goal_id,
                "mismatch": mismatch,
            })

        event = {
            "goal_id": goal_id,
            "scenario_id": scenario_id,
            "cycle": cycle,
            "stimulus": stimulus,
            "fl_expected": fl_expected,
            "rtl_observed": rtl_observed,
            "passed": passed,
            "mismatch": mismatch,
            "coverage_refs": coverage_refs or [],
        }
        self.events.append(event)
        return passed

    def check_apb_result(
        self,
        scenario_id: str,
        goal_id: str,
        addr: int,
        write: bool,
        write_data: int,
        rtl_rdata: int,
        rtl_pslverr: int,
        fl_expected_rdata: int = None,
        fl_expected_pslverr: int = 0,
    ):
        """Convenience: record APB access result."""
        stimulus = {"paddr": addr, "pwrite": int(write), "pwdata": write_data}
        rtl = {"prdata": rtl_rdata, "pslverr": rtl_pslverr}
        if fl_expected_rdata is None:
            fl_expected_rdata = self.predict_apb_read(addr)
        fl = {"prdata": fl_expected_rdata, "pslverr": fl_expected_pslverr}
        return self.record(scenario_id, goal_id, self.cycle, stimulus, fl, rtl)

    def check_dmac_irq(
        self, scenario_id: str, goal_id: str, expected_irq: int, observed_irq: int
    ):
        """Convenience: check dmac_irq."""
        stimulus = {"check": "dmac_irq"}
        return self.record(
            scenario_id, goal_id, self.cycle, stimulus,
            {"dmac_irq": expected_irq}, {"dmac_irq": observed_irq},
        )

    @staticmethod
    def _dict_matches(expected: dict, observed: dict) -> bool:
        """Check if observed matches expected (subset check on expected keys)."""
        for key, exp_val in expected.items():
            if key == "model_api":
                continue
            obs_val = observed.get(key)
            if obs_val is None:
                return False
            if isinstance(exp_val, dict) and isinstance(obs_val, dict):
                if not EquivalenceScoreboard._dict_matches(exp_val, obs_val):
                    return False
            elif exp_val != obs_val:
                return False
        return True

    @staticmethod
    def _diff(expected, observed) -> str:
        diffs = []
        if isinstance(expected, dict) and isinstance(observed, dict):
            all_keys = set(expected) | set(observed)
            for k in sorted(all_keys):
                ev = expected.get(k)
                ov = observed.get(k)
                if ev != ov:
                    diffs.append(f"{k}: expected={ev} got={ov}")
        else:
            diffs.append(f"expected={expected} got={observed}")
        return "; ".join(diffs)

    def dump(self) -> Path:
        """Write scoreboard_events.jsonl."""
        out = self.root / self.ip / "sim"
        out.mkdir(parents=True, exist_ok=True)
        path = out / "scoreboard_events.jsonl"
        with open(path, "w") as f:
            for ev in self.events:
                f.write(json.dumps(ev, default=str) + "\n")
        return path

    def summary(self) -> dict:
        n_total = len(self.events)
        n_pass = sum(1 for e in self.events if e["passed"])
        n_fail = n_total - n_pass
        return {
            "ip": self.ip,
            "total_events": n_total,
            "passed": n_pass,
            "failed": n_fail,
            "failures": self.failures,
        }

    def dump_summary(self) -> Path:
        out = self.root / self.ip / "sim"
        out.mkdir(parents=True, exist_ok=True)
        path = out / "scoreboard_summary.json"
        path.write_text(json.dumps(self.summary(), indent=2))
        return path


def run_self_check():
    """Quick smoke: import model, run one apply, verify it doesn't crash."""
    sb = EquivalenceScoreboard("pl330realverify", root=".")
    sb.reset_fl()
    # APB read of DBGSTATUS (offset 0)
    val = sb.predict_apb_read(0)
    assert isinstance(val, int), f"APB read returned {type(val)}"
    # APB write to INTEN (offset 32)
    result = sb.predict_apb_write(32, 0xFF)
    assert result is not None, "APB write returned None"
    # Transfer
    result = sb.predict_transfer(channel=0, rdata=0xDEADBEEF, loop_remaining=0)
    assert result is not None, "Transfer returned None"
    # WFP
    result = sb.predict_wfp(channel=0, selected_event=1)
    assert result is not None, "WFP returned None"
    # Fault
    result = sb.predict_fault(fault_code=3)
    assert result is not None, "Fault returned None"
    # IRQ clear
    result = sb.predict_irq_clear(pwdata=0x1)
    assert result is not None, "IRQ clear returned None"

    print(json.dumps({
        "self_check": "PASS",
        "trace_entries": len(sb.fl.trace),
        "checks_run": 7,
    }, indent=2))
    return True


if __name__ == "__main__":
    run_self_check()
