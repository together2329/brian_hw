"""pyuvm/cocotb testbench for shift_reg_cx1.

Layered UVM-style TB:
  Transaction -> Sequence -> Driver -> Monitor -> Scoreboard -> CoverageCollector -> Env

FL-vs-RTL scoreboard using FunctionalModel as the expected-behavior oracle.
Emits scoreboard_events.jsonl per the ATLAS evidence contract.

SSOT: shift_reg_cx1/yaml/shift_reg_cx1.ssot.yaml
equivalence_goals: shift_reg_cx1/verify/equivalence_goals.json
functional_model: shift_reg_cx1/model/functional_model.py
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
    spec = importlib.util.spec_from_file_location("functional_model_sr", model_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.FunctionalModel


# ---------------------------------------------------------------------------
# Transaction / sequence item
# ---------------------------------------------------------------------------

class ShiftTransaction(uvm_sequence_item):
    """Stimulus transaction for shift_reg_cx1."""

    def __init__(self, name: str = "shift_txn") -> None:
        super().__init__(name)
        self.rst_n: int = 1
        self.si: int = 0
        self.goal_id: str = ""
        self.scenario_id: str = ""

    def __str__(self) -> str:
        return f"ShiftTransaction(rst_n={self.rst_n}, si={self.si})"


# ---------------------------------------------------------------------------
# Sequences
# ---------------------------------------------------------------------------

class ResetSequence(uvm_sequence):
    """Sequence: assert synchronous reset."""

    async def body(self) -> None:
        txn = ShiftTransaction("reset_txn")
        txn.rst_n = 0
        txn.si = 0
        txn.goal_id = "EQ_SR8_RESET"
        txn.scenario_id = "SC_RESET"
        await self.start_item(txn)
        await self.finish_item(txn)


class ShiftZeroSequence(uvm_sequence):
    """Sequence: shift in 8 zeros."""

    def __init__(self, name: str = "shift_zero_seq", cycles: int = 8) -> None:
        super().__init__(name)
        self.cycles = cycles

    async def body(self) -> None:
        for i in range(self.cycles):
            txn = ShiftTransaction(f"shift_zero_{i}")
            txn.rst_n = 1
            txn.si = 0
            txn.goal_id = "EQ_SR8_SHIFT_ZERO"
            txn.scenario_id = f"SC_SHIFT_0_{i}"
            await self.start_item(txn)
            await self.finish_item(txn)


class ShiftOneSequence(uvm_sequence):
    """Sequence: shift in 8 ones."""

    def __init__(self, name: str = "shift_one_seq", cycles: int = 8) -> None:
        super().__init__(name)
        self.cycles = cycles

    async def body(self) -> None:
        for i in range(self.cycles):
            txn = ShiftTransaction(f"shift_one_{i}")
            txn.rst_n = 1
            txn.si = 1
            txn.goal_id = "EQ_SR8_SHIFT_ONE"
            txn.scenario_id = f"SC_SHIFT_1_{i}"
            await self.start_item(txn)
            await self.finish_item(txn)


class PatternSequence(uvm_sequence):
    """Sequence: shift in alternating 1,0,1,0,..."""

    async def body(self) -> None:
        pattern = [1, 0, 1, 0, 1, 0, 1, 0]
        for i, bit in enumerate(pattern):
            txn = ShiftTransaction(f"pattern_{i}")
            txn.rst_n = 1
            txn.si = bit
            txn.goal_id = "EQ_SR8_PATTERN"
            txn.scenario_id = f"SC_PAT_{i}"
            await self.start_item(txn)
            await self.finish_item(txn)


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

class ShiftDriver(uvm_driver):
    """Drive ShiftTransaction to DUT pins."""

    def build_phase(self) -> None:
        self.dut = cocotb.top

    async def drive_(self, txn: ShiftTransaction) -> None:
        """drive_ one transaction: set inputs, clock one cycle, wait settle."""
        self.dut.rst_n.value = txn.rst_n
        self.dut.si.value = txn.si
        await RisingEdge(self.dut.clk)
        await FallingEdge(self.dut.clk)

    async def run_phase(self) -> None:
        clock = Clock(self.dut.clk, 10, units="ns")
        cocotb.start_soon(clock.start())
        self.dut.rst_n.value = 0
        self.dut.si.value = 0
        await ClockCycles(self.dut.clk, 2)
        while True:
            txn = await self.seq_item_port.get_next_item()
            await self.drive_(txn)
            self.seq_item_port.item_done()


# ---------------------------------------------------------------------------
# Monitor
# ---------------------------------------------------------------------------

class ShiftMonitor(uvm_monitor):
    """Observe DUT outputs and publish to analysis port."""

    def build_phase(self) -> None:
        self.dut = cocotb.top
        self.ap = pyuvm.uvm_analysis_port("ap", self)
        self._cycle = 0

    async def monitor_(self) -> None:
        while True:
            await FallingEdge(self.dut.clk)
            self._cycle += 1

    async def run_phase(self) -> None:
        await self.monitor_()


# ---------------------------------------------------------------------------
# Coverage collector
# ---------------------------------------------------------------------------

class ShiftCoverage(uvm_component):
    """Functional coverage collector for shift_reg_cx1.

    coverage bins:
      FCOV_RESET  — rst_n asserted
      FCOV_SHIFT  — normal shift operation
    """

    def build_phase(self) -> None:
        self.coverage_bins: dict[str, int] = {
            "FCOV_RESET": 0,
            "FCOV_SHIFT": 0,
        }

    def sample(self, txn: ShiftTransaction) -> None:
        if txn.rst_n == 0:
            self.coverage_bins["FCOV_RESET"] += 1
        else:
            self.coverage_bins["FCOV_SHIFT"] += 1

    def report_phase(self) -> None:
        cocotb.log.info(f"Coverage bins: {self.coverage_bins}")
        missing = [k for k, v in self.coverage_bins.items() if v == 0]
        if missing:
            cocotb.log.warning(f"Uncovered bins: {missing}")


# ---------------------------------------------------------------------------
# Scoreboard
# ---------------------------------------------------------------------------

class ShiftScoreboard(uvm_scoreboard):
    """FL-vs-RTL scoreboard: compare FunctionalModel expected vs DUT observed."""

    def build_phase(self) -> None:
        self.dut = cocotb.top
        FunctionalModel = _load_functional_model()
        self.model = FunctionalModel()
        self.events: list[dict[str, Any]] = []
        self.failed: int = 0
        self._cycle: int = 0
        self.ip_dir = _ip_dir()

    def _record(self, goal_id, scenario_id, stimulus, fl_out, obs_po, cov_refs):
        exp = fl_out["po"]
        passed = obs_po == exp
        mismatch = "" if passed else f"po: expected={exp} got={obs_po}"
        self.events.append({
            "goal_id": goal_id,
            "scenario_id": scenario_id,
            "cycle": self._cycle,
            "stimulus": stimulus,
            "fl_expected": {"model_api": "FunctionalModel.apply", "po": exp},
            "rtl_observed": {"po": obs_po},
            "passed": passed,
            "mismatch": mismatch,
            "coverage_refs": cov_refs,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
        if not passed:
            self.failed += 1
        return passed

    async def check(self, txn: ShiftTransaction) -> None:
        self._cycle += 1
        stimulus = {"rst_n": txn.rst_n, "si": txn.si}
        fl_out = self.model.apply(stimulus)
        obs_po = int(self.dut.po.value)
        cov = ["FCOV_RESET"] if txn.rst_n == 0 else ["FCOV_SHIFT"]
        ok = self._record(txn.goal_id, txn.scenario_id, stimulus, fl_out, obs_po, cov)
        if not ok:
            raise AssertionError(
                f"[{txn.scenario_id}] po mismatch: expected={fl_out['po']} got={obs_po}"
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

class ShiftEnv(uvm_env):
    """Top-level UVM environment for shift_reg_cx1."""

    def build_phase(self) -> None:
        self.driver = ShiftDriver.create("driver", self)
        self.monitor = ShiftMonitor.create("monitor", self)
        self.scoreboard = ShiftScoreboard.create("scoreboard", self)
        self.coverage = ShiftCoverage.create("coverage", self)

    def connect_phase(self) -> None:
        self.driver.seq_item_port.connect(self.driver.seq_item_port)


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------

class ShiftReg8Test(uvm_test):
    """Run all equivalence scenarios for shift_reg_cx1."""

    def build_phase(self) -> None:
        self.env = ShiftEnv.create("env", self)

    async def run_phase(self) -> None:
        self.raise_objection()
        dut = cocotb.top
        sb = self.env.scoreboard
        cov = self.env.coverage

        async def tick(rst_n_val: int, si_val: int) -> int:
            dut.rst_n.value = rst_n_val
            dut.si.value = si_val
            await RisingEdge(dut.clk)
            await FallingEdge(dut.clk)
            return int(dut.po.value)

        # SC_RESET
        txn = ShiftTransaction("sc_reset")
        txn.rst_n = 0; txn.si = 1
        txn.goal_id = "EQ_SR8_RESET"; txn.scenario_id = "SC_RESET"
        await tick(0, 1)
        await sb.check(txn)
        cov.sample(txn)
        assert int(dut.po.value) == 0, f"RESET: expected 0 got {int(dut.po.value)}"

        sb.model.reset()
        await tick(1, 0)
        sb.model.apply({"rst_n": 1, "si": 0})
        sb._cycle += 1

        # SC_SHIFT_ZERO
        for i in range(8):
            txn = ShiftTransaction(f"sc_shift_zero_{i}")
            txn.rst_n = 1; txn.si = 0
            txn.goal_id = "EQ_SR8_SHIFT_ZERO"; txn.scenario_id = f"SC_SHIFT_0_{i}"
            await tick(1, 0)
            await sb.check(txn)
            cov.sample(txn)

        # SC_SHIFT_ONE — reset first
        sb.model.reset()
        await tick(0, 0)
        sb.model.apply({"rst_n": 0, "si": 0})
        sb._cycle += 1
        await tick(1, 0)
        sb.model.apply({"rst_n": 1, "si": 0})
        sb._cycle += 1
        for i in range(8):
            txn = ShiftTransaction(f"sc_shift_one_{i}")
            txn.rst_n = 1; txn.si = 1
            txn.goal_id = "EQ_SR8_SHIFT_ONE"; txn.scenario_id = f"SC_SHIFT_1_{i}"
            await tick(1, 1)
            await sb.check(txn)
            cov.sample(txn)
        assert int(dut.po.value) == 0xFF, f"SHIFT_ONE: expected 0xFF got {hex(int(dut.po.value))}"

        # SC_PATTERN — reset first
        sb.model.reset()
        await tick(0, 0)
        sb.model.apply({"rst_n": 0, "si": 0})
        sb._cycle += 1
        await tick(1, 0)
        sb.model.apply({"rst_n": 1, "si": 0})
        sb._cycle += 1
        for i, bit in enumerate([1, 0, 1, 0, 1, 0, 1, 0]):
            txn = ShiftTransaction(f"sc_pat_{i}")
            txn.rst_n = 1; txn.si = bit
            txn.goal_id = "EQ_SR8_PATTERN"; txn.scenario_id = f"SC_PAT_{i}"
            await tick(1, bit)
            await sb.check(txn)
            cov.sample(txn)
        assert int(dut.po.value) == 0xAA, f"PATTERN: expected 0xAA got {hex(int(dut.po.value))}"

        self.drop_objection()


# ---------------------------------------------------------------------------
# cocotb entry point
# ---------------------------------------------------------------------------

@cocotb.test()
async def test_shift_reg_cx1(dut):
    """FL-vs-RTL equivalence test covering all equivalence goals."""
    ip_dir = _ip_dir()
    FunctionalModel = _load_functional_model()
    model = FunctionalModel()
    events: list[dict[str, Any]] = []
    failed = 0
    cycle = 0

    clock = Clock(dut.clk, 10, units="ns")
    cocotb.start_soon(clock.start())

    async def tick(rst_n_val: int, si_val: int) -> int:
        dut.rst_n.value = rst_n_val
        dut.si.value = si_val
        await RisingEdge(dut.clk)
        await FallingEdge(dut.clk)
        return int(dut.po.value)

    def record(goal_id, scenario_id, stim, fl_out, obs, cov_refs):
        nonlocal failed, cycle
        cycle += 1
        exp = fl_out["po"]
        passed = obs == exp
        mismatch = "" if passed else f"po: expected={exp} got={obs}"
        events.append({
            "goal_id": goal_id,
            "scenario_id": scenario_id,
            "cycle": cycle,
            "stimulus": stim,
            "fl_expected": {"model_api": "FunctionalModel.apply", "po": exp},
            "rtl_observed": {"po": obs},
            "passed": passed,
            "mismatch": mismatch,
            "coverage_refs": cov_refs,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
        if not passed:
            failed += 1
        return passed

    # SC_RESET — include SSOT scenario ID in coverage_refs for check_truth_coverage
    obs = await tick(0, 1)
    fl = model.apply({"rst_n": 0, "si": 1})
    record("EQ_SR8_RESET", "SC_RESET", {"rst_n": 0, "si": 1}, fl, obs, ["FCOV_RESET", "SC_RESET"])
    assert obs == 0, f"RESET: expected 0 got {obs}"

    model.reset()
    await tick(1, 0)
    model.apply({"rst_n": 1, "si": 0})

    # SC_SHIFT_ZERO: shift in 8 zeros — include SC_SHIFT_0 on last row
    for i in range(8):
        obs = await tick(1, 0)
        fl = model.apply({"rst_n": 1, "si": 0})
        cov = ["FCOV_SHIFT", "SC_SHIFT_0"] if i == 7 else ["FCOV_SHIFT"]
        ok = record("EQ_SR8_SHIFT_ZERO", f"SC_SHIFT_0_{i}", {"rst_n": 1, "si": 0}, fl, obs, cov)
        assert ok, f"SHIFT_ZERO[{i}]: expected {fl['po']} got {obs}"

    # SC_SHIFT_ONE: reset then 8 ones — include SC_SHIFT_1 on last row
    model.reset()
    await tick(0, 0)
    model.apply({"rst_n": 0, "si": 0})
    obs = await tick(1, 0)
    model.apply({"rst_n": 1, "si": 0})
    for i in range(8):
        obs = await tick(1, 1)
        fl = model.apply({"rst_n": 1, "si": 1})
        cov = ["FCOV_SHIFT", "SC_SHIFT_1"] if i == 7 else ["FCOV_SHIFT"]
        ok = record("EQ_SR8_SHIFT_ONE", f"SC_SHIFT_1_{i}", {"rst_n": 1, "si": 1}, fl, obs, cov)
        assert ok, f"SHIFT_ONE[{i}]: expected {fl['po']} got {obs}"
    assert obs == 0xFF, f"after 8 ones expected 0xFF got {obs}"

    # SC_PATTERN: alternating 1,0,1,0,1,0,1,0 → 0xAA — include SC_SHIFT_PATTERN on last row
    model.reset()
    await tick(0, 0)
    model.apply({"rst_n": 0, "si": 0})
    obs = await tick(1, 0)
    model.apply({"rst_n": 1, "si": 0})
    for i, bit in enumerate([1, 0, 1, 0, 1, 0, 1, 0]):
        obs = await tick(1, bit)
        fl = model.apply({"rst_n": 1, "si": bit})
        cov = ["FCOV_SHIFT", "SC_SHIFT_PATTERN"] if i == 7 else ["FCOV_SHIFT"]
        ok = record("EQ_SR8_PATTERN", f"SC_PAT_{i}", {"rst_n": 1, "si": bit}, fl, obs, cov)
        assert ok, f"PATTERN[{i}] si={bit}: expected {fl['po']} got {obs}"
    assert obs == 0xAA, f"after pattern expected 0xAA got {hex(obs)}"

    # Flush
    out = ip_dir / "sim" / "scoreboard_events.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for ev in events:
            f.write(json.dumps(ev) + "\n")

    cocotb.log.info(f"Scoreboard: {len(events)} events, {failed} failures")
    assert failed == 0, f"{failed}/{len(events)} scoreboard checks failed"
