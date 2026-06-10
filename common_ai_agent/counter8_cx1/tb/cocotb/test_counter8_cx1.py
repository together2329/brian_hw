"""pyuvm/cocotb testbench for counter8_cx1.

Layered UVM-style TB:
  Transaction -> Sequence -> Driver -> Monitor -> Scoreboard -> CoverageCollector -> Env

FL-vs-RTL scoreboard using FunctionalModel as the expected-behavior oracle.
Emits scoreboard_events.jsonl per the ATLAS evidence contract.

SSOT: counter8_cx1/yaml/counter8_cx1.ssot.yaml
equivalence_goals: counter8_cx1/verify/equivalence_goals.json
functional_model: counter8_cx1/model/functional_model.py
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import cocotb
import pyuvm
from cocotb.clock import Clock
from cocotb.queue import Queue
from cocotb.triggers import ClockCycles, FallingEdge, RisingEdge
from pyuvm import (
    uvm_component,
    uvm_driver,
    uvm_env,
    uvm_monitor,
    uvm_scoreboard,
    uvm_sequence,
    uvm_sequence_item,
    uvm_test,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def _ip_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_goals() -> list[dict[str, Any]]:
    path = _ip_dir() / "verify" / "equivalence_goals.json"
    doc = json.loads(path.read_text(encoding="utf-8"))
    return [g for g in doc.get("goals", []) if isinstance(g, dict) and not g.get("blocked")]


def _load_functional_model():
    model_path = _ip_dir() / "model" / "functional_model.py"
    spec = importlib.util.spec_from_file_location("functional_model", model_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.FunctionalModel


# ---------------------------------------------------------------------------
# Transaction / sequence item
# ---------------------------------------------------------------------------

class CounterTransaction(uvm_sequence_item):
    """Stimulus transaction for counter8_cx1."""

    def __init__(self, name: str = "counter_txn") -> None:
        super().__init__(name)
        self.rst_n: int = 1
        self.en: int = 0
        self.goal_id: str = ""
        self.scenario_id: str = ""

    def __str__(self) -> str:
        return f"CounterTransaction(rst_n={self.rst_n}, en={self.en})"


# ---------------------------------------------------------------------------
# Sequences
# ---------------------------------------------------------------------------

class ResetSequence(uvm_sequence):
    """Sequence: assert synchronous reset."""

    async def body(self) -> None:
        txn = CounterTransaction("reset_txn")
        txn.rst_n = 0
        txn.en = 1
        txn.goal_id = "EQ_CNT8_RESET"
        txn.scenario_id = "SC_RESET"
        await self.start_item(txn)
        await self.finish_item(txn)


class CountSequence(uvm_sequence):
    """Sequence: enable counter for N cycles."""

    def __init__(self, name: str = "count_seq", cycles: int = 10) -> None:
        super().__init__(name)
        self.cycles = cycles

    async def body(self) -> None:
        for i in range(self.cycles):
            txn = CounterTransaction(f"count_{i}")
            txn.rst_n = 1
            txn.en = 1
            txn.goal_id = "EQ_CNT8_COUNT"
            txn.scenario_id = f"SC_COUNT_{i}"
            await self.start_item(txn)
            await self.finish_item(txn)


class HoldSequence(uvm_sequence):
    """Sequence: disable enable for N cycles."""

    def __init__(self, name: str = "hold_seq", cycles: int = 3) -> None:
        super().__init__(name)
        self.cycles = cycles

    async def body(self) -> None:
        for i in range(self.cycles):
            txn = CounterTransaction(f"hold_{i}")
            txn.rst_n = 1
            txn.en = 0
            txn.goal_id = "EQ_CNT8_HOLD"
            txn.scenario_id = f"SC_HOLD_{i}"
            await self.start_item(txn)
            await self.finish_item(txn)


class WrapSequence(uvm_sequence):
    """Sequence: count 256 times to verify wrap-around."""

    async def body(self) -> None:
        # Reset first
        rst = CounterTransaction("wrap_reset")
        rst.rst_n = 0
        rst.en = 0
        rst.goal_id = "EQ_CNT8_WRAP"
        rst.scenario_id = "SC_WRAP_RESET"
        await self.start_item(rst)
        await self.finish_item(rst)
        # Count 256 times: 255 setup + 1 wrap
        for i in range(256):
            txn = CounterTransaction(f"wrap_{i}")
            txn.rst_n = 1
            txn.en = 1
            txn.goal_id = "EQ_CNT8_WRAP"
            txn.scenario_id = "SC_WRAP" if i == 255 else f"SC_WRAP_SETUP_{i}"
            await self.start_item(txn)
            await self.finish_item(txn)


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

class CounterDriver(uvm_driver):
    """Drive CounterTransaction to DUT pins."""

    def build_phase(self) -> None:
        self.dut = cocotb.top

    async def drive_(self, txn: CounterTransaction) -> None:
        """drive_ one transaction: set inputs, clock one cycle, wait settle."""
        self.dut.rst_n.value = txn.rst_n
        self.dut.en.value = txn.en
        await RisingEdge(self.dut.clk)
        await FallingEdge(self.dut.clk)

    async def run_phase(self) -> None:
        clock = Clock(self.dut.clk, 10, units="ns")
        cocotb.start_soon(clock.start())
        # Initial state
        self.dut.rst_n.value = 0
        self.dut.en.value = 0
        await ClockCycles(self.dut.clk, 2)
        while True:
            txn = await self.seq_item_port.get_next_item()
            await self.drive_(txn)
            self.seq_item_port.item_done()


# ---------------------------------------------------------------------------
# Monitor
# ---------------------------------------------------------------------------

class CounterMonitor(uvm_monitor):
    """Observe DUT outputs and publish to analysis port."""

    def build_phase(self) -> None:
        self.dut = cocotb.top
        self.ap = pyuvm.uvm_analysis_port("ap", self)
        self._cycle = 0

    async def monitor_(self) -> None:
        """Monitor DUT outputs after each falling edge."""
        while True:
            await FallingEdge(self.dut.clk)
            self._cycle += 1

    async def run_phase(self) -> None:
        await self.monitor_()


# ---------------------------------------------------------------------------
# Coverage collector
# ---------------------------------------------------------------------------

class CounterCoverage(uvm_component):
    """Functional coverage collector for counter8_cx1.

    coverage bins:
      FCOV_RESET  — rst_n asserted
      FCOV_COUNT  — en=1 increment
      FCOV_HOLD   — en=0 hold
    """

    def build_phase(self) -> None:
        self.coverage_bins: dict[str, int] = {
            "FCOV_RESET": 0,
            "FCOV_COUNT": 0,
            "FCOV_HOLD": 0,
        }

    def sample(self, txn: CounterTransaction) -> None:
        if txn.rst_n == 0:
            self.coverage_bins["FCOV_RESET"] += 1
        elif txn.en == 1:
            self.coverage_bins["FCOV_COUNT"] += 1
        else:
            self.coverage_bins["FCOV_HOLD"] += 1

    def report_phase(self) -> None:
        cocotb.log.info(f"Coverage bins: {self.coverage_bins}")
        missing = [k for k, v in self.coverage_bins.items() if v == 0]
        if missing:
            cocotb.log.warning(f"Uncovered bins: {missing}")


# ---------------------------------------------------------------------------
# Scoreboard
# ---------------------------------------------------------------------------

class CounterScoreboard(uvm_scoreboard):
    """FL-vs-RTL scoreboard: compare FunctionalModel expected vs DUT observed."""

    def build_phase(self) -> None:
        self.dut = cocotb.top
        FunctionalModel = _load_functional_model()
        self.model = FunctionalModel()
        self.events: list[dict[str, Any]] = []
        self.failed: int = 0
        self._cycle: int = 0
        self.ip_dir = _ip_dir()

    def _record(
        self,
        goal_id: str,
        scenario_id: str,
        stimulus: dict[str, Any],
        fl_out: dict[str, Any],
        obs_count: int,
        coverage_refs: list[str],
    ) -> bool:
        exp_count = fl_out["count"]
        passed = obs_count == exp_count
        mismatch = "" if passed else f"count: expected={exp_count} got={obs_count}"
        event = {
            "goal_id": goal_id,
            "scenario_id": scenario_id,
            "cycle": self._cycle,
            "stimulus": stimulus,
            "fl_expected": {
                "model_api": "FunctionalModel.apply",
                "count": exp_count,
            },
            "rtl_observed": {"count": obs_count},
            "passed": passed,
            "mismatch": mismatch,
            "coverage_refs": coverage_refs,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        self.events.append(event)
        if not passed:
            self.failed += 1
        return passed

    async def check(self, txn: CounterTransaction) -> None:
        self._cycle += 1
        stimulus = {"rst_n": txn.rst_n, "en": txn.en}
        fl_out = self.model.apply(stimulus)
        obs_count = int(self.dut.count.value)
        cov = ["FCOV_RESET"] if txn.rst_n == 0 else (["FCOV_COUNT"] if txn.en else ["FCOV_HOLD"])
        ok = self._record(txn.goal_id, txn.scenario_id, stimulus, fl_out, obs_count, cov)
        if not ok:
            raise AssertionError(
                f"[{txn.scenario_id}] count mismatch: expected={fl_out['count']} got={obs_count}"
            )

    def report_phase(self) -> None:
        out = self.ip_dir / "sim" / "scoreboard_events.jsonl"
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("w", encoding="utf-8") as f:
            for ev in self.events:
                f.write(json.dumps(ev) + "\n")
        cocotb.log.info(f"Scoreboard: {len(self.events)} events, {self.failed} failures")
        if self.failed:
            raise AssertionError(f"{self.failed}/{len(self.events)} scoreboard checks failed")


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

class CounterEnv(uvm_env):
    """Top-level UVM environment for counter8_cx1."""

    def build_phase(self) -> None:
        self.driver = CounterDriver.create("driver", self)
        self.monitor = CounterMonitor.create("monitor", self)
        self.scoreboard = CounterScoreboard.create("scoreboard", self)
        self.coverage = CounterCoverage.create("coverage", self)

    def connect_phase(self) -> None:
        self.driver.seq_item_port.connect(self.driver.seq_item_port)


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------

class Counter8Test(uvm_test):
    """Run all equivalence scenarios for counter8_cx1."""

    def build_phase(self) -> None:
        self.env = CounterEnv.create("env", self)

    async def run_phase(self) -> None:
        self.raise_objection()
        dut = cocotb.top
        sb = self.env.scoreboard
        cov = self.env.coverage

        async def tick(rst_n_val: int, en_val: int) -> int:
            dut.rst_n.value = rst_n_val
            dut.en.value = en_val
            await RisingEdge(dut.clk)
            await FallingEdge(dut.clk)
            return int(dut.count.value)

        # SC_RESET
        txn = CounterTransaction("sc_reset")
        txn.rst_n = 0; txn.en = 1
        txn.goal_id = "EQ_CNT8_RESET"; txn.scenario_id = "SC_RESET"
        await tick(0, 1)
        await sb.check(txn)
        cov.sample(txn)

        # Release reset, sync model
        sb.model.reset()
        await tick(1, 0)
        sb.model.apply({"rst_n": 1, "en": 0})
        sb._cycle += 1

        # SC_COUNT: 10 increments
        for i in range(10):
            txn = CounterTransaction(f"sc_count_{i}")
            txn.rst_n = 1; txn.en = 1
            txn.goal_id = "EQ_CNT8_COUNT"; txn.scenario_id = f"SC_COUNT_{i}"
            await tick(1, 1)
            await sb.check(txn)
            cov.sample(txn)

        # SC_HOLD: 3 hold cycles
        hold_start = int(dut.count.value)
        for i in range(3):
            txn = CounterTransaction(f"sc_hold_{i}")
            txn.rst_n = 1; txn.en = 0
            txn.goal_id = "EQ_CNT8_HOLD"; txn.scenario_id = f"SC_HOLD_{i}"
            await tick(1, 0)
            await sb.check(txn)
            cov.sample(txn)

        # SC_WRAP: reset, count 256 cycles
        sb.model.reset()
        await tick(0, 0)
        sb.model.apply({"rst_n": 0, "en": 0})
        sb._cycle += 1
        await tick(1, 0)
        sb.model.apply({"rst_n": 1, "en": 0})
        sb._cycle += 1

        for j in range(255):
            await tick(1, 1)
            sb.model.apply({"rst_n": 1, "en": 1})
            sb._cycle += 1

        txn = CounterTransaction("sc_wrap")
        txn.rst_n = 1; txn.en = 1
        txn.goal_id = "EQ_CNT8_WRAP"; txn.scenario_id = "SC_WRAP"
        await tick(1, 1)
        await sb.check(txn)
        cov.sample(txn)
        assert int(dut.count.value) == 0, f"WRAP: expected 0 got {int(dut.count.value)}"

        self.drop_objection()


# ---------------------------------------------------------------------------
# cocotb entry point
# ---------------------------------------------------------------------------

@cocotb.test()
async def test_counter8_cx1(dut):
    """FL-vs-RTL equivalence test covering all equivalence goals."""
    ip_dir = _ip_dir()
    FunctionalModel = _load_functional_model()
    model = FunctionalModel()
    events: list[dict[str, Any]] = []
    failed = 0
    cycle = 0

    # Start clock
    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    async def tick(rst_n_val: int, en_val: int) -> int:
        dut.rst_n.value = rst_n_val
        dut.en.value = en_val
        await RisingEdge(dut.clk)
        await FallingEdge(dut.clk)
        return int(dut.count.value)

    def record(goal_id, scenario_id, stim, fl_out, obs, cov_refs):
        nonlocal failed, cycle
        cycle += 1
        exp = fl_out["count"]
        passed = obs == exp
        mismatch = "" if passed else f"count: expected={exp} got={obs}"
        events.append({
            "goal_id": goal_id,
            "scenario_id": scenario_id,
            "cycle": cycle,
            "stimulus": stim,
            "fl_expected": {"model_api": "FunctionalModel.apply", "count": exp},
            "rtl_observed": {"count": obs},
            "passed": passed,
            "mismatch": mismatch,
            "coverage_refs": cov_refs,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
        if not passed:
            failed += 1
        return passed

    # SC_RESET — coverage_refs include SSOT scenario ID so check_truth_coverage can match
    obs = await tick(0, 1)
    fl = model.apply({"rst_n": 0, "en": 1})
    record("EQ_CNT8_RESET", "SC_RESET", {"rst_n": 0, "en": 1}, fl, obs, ["FCOV_RESET", "SC_RESET"])
    assert obs == 0, f"RESET: expected 0 got {obs}"

    model.reset()
    await tick(1, 0)
    model.apply({"rst_n": 1, "en": 0})

    # SC_COUNT — include SC_COUNT in coverage_refs on last row for scenario coverage
    for i in range(10):
        obs = await tick(1, 1)
        fl = model.apply({"rst_n": 1, "en": 1})
        cov = ["FCOV_COUNT", "SC_COUNT"] if i == 9 else ["FCOV_COUNT"]
        ok = record("EQ_CNT8_COUNT", f"SC_COUNT_{i}", {"rst_n": 1, "en": 1}, fl, obs, cov)
        assert ok, f"COUNT[{i}]: expected {fl['count']} got {obs}"

    # SC_HOLD — include SC_HOLD in coverage_refs on last row
    hold_val = obs
    for i in range(3):
        obs = await tick(1, 0)
        fl = model.apply({"rst_n": 1, "en": 0})
        cov = ["FCOV_HOLD", "SC_HOLD"] if i == 2 else ["FCOV_HOLD"]
        ok = record("EQ_CNT8_HOLD", f"SC_HOLD_{i}", {"rst_n": 1, "en": 0}, fl, obs, cov)
        assert ok, f"HOLD[{i}]: expected {fl['count']} got {obs}"

    # SC_WRAP
    model.reset()
    await tick(0, 0)
    model.apply({"rst_n": 0, "en": 0})
    await tick(1, 0)
    model.apply({"rst_n": 1, "en": 0})
    for _ in range(255):
        await tick(1, 1)
        model.apply({"rst_n": 1, "en": 1})
    obs = await tick(1, 1)
    fl = model.apply({"rst_n": 1, "en": 1})
    ok = record("EQ_CNT8_WRAP", "SC_WRAP", {"rst_n": 1, "en": 1}, fl, obs, ["FCOV_COUNT", "SC_WRAP"])
    assert ok, f"WRAP: expected {fl['count']} got {obs}"
    assert obs == 0, f"WRAP: expected 0 got {obs}"

    # Flush
    out = ip_dir / "sim" / "scoreboard_events.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for ev in events:
            f.write(json.dumps(ev) + "\n")

    cocotb.log.info(f"Scoreboard: {len(events)} events, {failed} failures")
    assert failed == 0, f"{failed}/{len(events)} scoreboard checks failed"
