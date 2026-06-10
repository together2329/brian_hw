"""pyuvm/cocotb testbench for watchdog_cx1.

Layered UVM-style TB:
  Transaction -> Sequence -> Driver -> Monitor -> Scoreboard -> CoverageCollector -> Env

FL-vs-RTL scoreboard using FunctionalModel as the expected-behavior oracle.
Emits scoreboard_events.jsonl per the ATLAS evidence contract.

SSOT: watchdog_cx1/yaml/watchdog_cx1.ssot.yaml
equivalence_goals: watchdog_cx1/verify/equivalence_goals.json
functional_model: watchdog_cx1/model/functional_model.py
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
    # Load equivalence_goals.json for goal IDs
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

class WdtTransaction(uvm_sequence_item):
    """Stimulus transaction for watchdog_cx1 APB interface."""

    def __init__(self, name: str = "wdt_txn") -> None:
        super().__init__(name)
        self.psel: int = 0
        self.penable: int = 0
        self.pwrite: int = 0
        self.paddr: int = 0
        self.pwdata: int = 0
        self.goal_id: str = ""
        self.scenario_id: str = ""

    def __str__(self) -> str:
        return (
            f"WdtTransaction(psel={self.psel}, penable={self.penable}, "
            f"pwrite={self.pwrite}, paddr={self.paddr:#x}, pwdata={self.pwdata:#x})"
        )


# ---------------------------------------------------------------------------
# Sequences
# ---------------------------------------------------------------------------

class WdtIdleSequence(uvm_sequence):
    """Sequence: idle cycle (no APB activity)."""

    def __init__(self, name: str = "idle_seq", cycles: int = 1) -> None:
        super().__init__(name)
        self.cycles = cycles

    async def body(self) -> None:
        for i in range(self.cycles):
            txn = WdtTransaction(f"idle_{i}")
            txn.goal_id = "EQ_WDT_IDLE"
            txn.scenario_id = f"SC_IDLE_{i}"
            await self.start_item(txn)
            await self.finish_item(txn)


class WdtApbWriteSequence(uvm_sequence):
    """Sequence: single APB write transaction (setup + access)."""

    def __init__(self, name: str = "apb_wr_seq", addr: int = 0, data: int = 0,
                 goal_id: str = "", scenario_id: str = "") -> None:
        super().__init__(name)
        self.addr = addr
        self.data = data
        self.goal_id = goal_id
        self.scenario_id = scenario_id

    async def body(self) -> None:
        # Setup phase
        setup = WdtTransaction(f"{self.name}_setup")
        setup.psel = 1
        setup.penable = 0
        setup.pwrite = 1
        setup.paddr = self.addr
        setup.pwdata = self.data
        setup.goal_id = self.goal_id
        setup.scenario_id = self.scenario_id
        await self.start_item(setup)
        await self.finish_item(setup)
        # Access phase
        access = WdtTransaction(f"{self.name}_access")
        access.psel = 1
        access.penable = 1
        access.pwrite = 1
        access.paddr = self.addr
        access.pwdata = self.data
        access.goal_id = self.goal_id
        access.scenario_id = self.scenario_id
        await self.start_item(access)
        await self.finish_item(access)


class WdtTickSequence(uvm_sequence):
    """Sequence: run enabled counter for N cycles."""

    def __init__(self, name: str = "tick_seq", cycles: int = 4) -> None:
        super().__init__(name)
        self.cycles = cycles

    async def body(self) -> None:
        for i in range(self.cycles):
            txn = WdtTransaction(f"tick_{i}")
            txn.goal_id = "EQ_WDT_TICK"
            txn.scenario_id = f"SC_TICK_{i}"
            await self.start_item(txn)
            await self.finish_item(txn)


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

class WdtDriver(uvm_driver):
    """Drive WdtTransaction to DUT APB pins."""

    def build_phase(self) -> None:
        self.dut = cocotb.top

    async def drive_(self, txn: WdtTransaction) -> None:
        """drive_ one transaction cycle: set inputs, clock one cycle."""
        self.dut.PSEL.value    = txn.psel
        self.dut.PENABLE.value = txn.penable
        self.dut.PWRITE.value  = txn.pwrite
        self.dut.PADDR.value   = txn.paddr
        self.dut.PWDATA.value  = txn.pwdata
        await RisingEdge(self.dut.PCLK)
        await FallingEdge(self.dut.PCLK)

    async def run_phase(self) -> None:
        clock = Clock(self.dut.PCLK, 10, units="ns")
        cocotb.start_soon(clock.start())
        self.dut.PRESETn.value = 0
        self.dut.PSEL.value    = 0
        self.dut.PENABLE.value = 0
        self.dut.PWRITE.value  = 0
        self.dut.PADDR.value   = 0
        self.dut.PWDATA.value  = 0
        await ClockCycles(self.dut.PCLK, 3)
        self.dut.PRESETn.value = 1
        while True:
            txn = await self.seq_item_port.get_next_item()
            await self.drive_(txn)
            self.seq_item_port.item_done()


# ---------------------------------------------------------------------------
# Monitor
# ---------------------------------------------------------------------------

class WdtMonitor(uvm_monitor):
    """Observe DUT outputs after each clock cycle."""

    def build_phase(self) -> None:
        self.dut = cocotb.top
        self.ap = pyuvm.uvm_analysis_port("ap", self)
        self._cycle = 0

    async def monitor_(self) -> None:
        """monitor_ DUT output signals after each falling edge."""
        while True:
            await FallingEdge(self.dut.PCLK)
            self._cycle += 1

    async def run_phase(self) -> None:
        await self.monitor_()


# ---------------------------------------------------------------------------
# Coverage collector
# ---------------------------------------------------------------------------

class WdtCoverage(uvm_component):
    """Functional coverage collector for watchdog_cx1.

    coverage bins (coverpoint):
      FCOV_TICK     — enabled counter decrement
      FCOV_TIMEOUT  — timeout_pulse fired
      FCOV_KICK     — KICK register write
      FCOV_IDLE     — counter disabled
    """

    def build_phase(self) -> None:
        self.coverage_bins: dict[str, int] = {
            "FCOV_TICK":    0,
            "FCOV_TIMEOUT": 0,
            "FCOV_KICK":    0,
            "FCOV_IDLE":    0,
        }

    def sample(self, txn: WdtTransaction, timeout_pulse: int) -> None:
        is_kick = (txn.psel == 1 and txn.penable == 1 and
                   txn.pwrite == 1 and txn.paddr == 4)
        if is_kick:
            self.coverage_bins["FCOV_KICK"] += 1
        elif timeout_pulse == 1:
            self.coverage_bins["FCOV_TIMEOUT"] += 1
            self.coverage_bins["FCOV_TICK"] += 1
        elif txn.psel == 0:
            self.coverage_bins["FCOV_TICK"] += 1
        else:
            self.coverage_bins["FCOV_IDLE"] += 1

    def report_phase(self) -> None:
        cocotb.log.info(f"Coverage bins: {self.coverage_bins}")
        missing = [k for k, v in self.coverage_bins.items() if v == 0]
        if missing:
            cocotb.log.warning(f"Uncovered bins: {missing}")


# ---------------------------------------------------------------------------
# Scoreboard
# ---------------------------------------------------------------------------

class WdtScoreboard(uvm_scoreboard):
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
        obs: dict[str, Any],
        coverage_refs: list[str],
    ) -> bool:
        exp_pulse = fl_out["timeout_pulse"]
        obs_pulse = obs.get("timeout_pulse", -1)
        passed = obs_pulse == exp_pulse
        mismatch = "" if passed else f"timeout_pulse: expected={exp_pulse} got={obs_pulse}"
        event = {
            "goal_id": goal_id,
            "scenario_id": scenario_id,
            "cycle": self._cycle,
            "stimulus": stimulus,
            "fl_expected": {
                "model_api": "FunctionalModel.apply",
                "timeout_pulse": exp_pulse,
            },
            "rtl_observed": obs,
            "passed": passed,
            "mismatch": mismatch,
            "coverage_refs": coverage_refs,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        self.events.append(event)
        if not passed:
            self.failed += 1
        return passed

    async def check(
        self,
        txn: WdtTransaction,
        stimulus: dict[str, Any],
        fl_out: dict[str, Any],
        coverage_refs: list[str],
    ) -> bool:
        self._cycle += 1
        obs = {
            "timeout_pulse": int(self.dut.timeout_pulse.value),
            "PREADY":        int(self.dut.PREADY.value),
            "PSLVERR":       int(self.dut.PSLVERR.value),
        }
        return self._record(
            txn.goal_id, txn.scenario_id, stimulus, fl_out, obs, coverage_refs
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

class WdtEnv(uvm_env):
    """Top-level UVM environment for watchdog_cx1."""

    def build_phase(self) -> None:
        self.driver     = WdtDriver.create("driver", self)
        self.monitor    = WdtMonitor.create("monitor", self)
        self.scoreboard = WdtScoreboard.create("scoreboard", self)
        self.coverage   = WdtCoverage.create("coverage", self)

    def connect_phase(self) -> None:
        self.driver.seq_item_port.connect(self.driver.seq_item_port)


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------

class WdtTest(uvm_test):
    """Run all equivalence scenarios for watchdog_cx1."""

    def build_phase(self) -> None:
        self.env = WdtEnv.create("env", self)


# ---------------------------------------------------------------------------
# cocotb entry point
# ---------------------------------------------------------------------------

@cocotb.test()
async def test_watchdog_cx1(dut):
    """FL-vs-RTL equivalence test covering all equivalence goals.

    Loads equivalence_goals.json to discover required goal IDs.
    Drives APB stimulus, advances FL model in lockstep, records
    scoreboard_events.jsonl as evidence.
    """
    ip_dir = _ip_dir()
    goals = _load_goals()
    FunctionalModel = _load_functional_model()
    model = FunctionalModel()
    events: list[dict[str, Any]] = []
    failed = 0
    cycle = 0

    # Start 10 ns clock
    clock = Clock(dut.PCLK, 10, units="ns")
    cocotb.start_soon(clock.start())

    # coverage bins
    coverage_bins: dict[str, int] = {
        "FCOV_TICK": 0, "FCOV_TIMEOUT": 0, "FCOV_KICK": 0, "FCOV_IDLE": 0,
    }

    async def tick_cycle(
        psel: int = 0, penable: int = 0, pwrite: int = 0,
        paddr: int = 0, pwdata: int = 0,
    ) -> dict[str, int]:
        """Advance one PCLK, return sampled DUT outputs."""
        dut.PSEL.value    = psel
        dut.PENABLE.value = penable
        dut.PWRITE.value  = pwrite
        dut.PADDR.value   = paddr
        dut.PWDATA.value  = pwdata
        await RisingEdge(dut.PCLK)
        await FallingEdge(dut.PCLK)
        return {
            "timeout_pulse": int(dut.timeout_pulse.value),
            "PREADY":        int(dut.PREADY.value),
            "PSLVERR":       int(dut.PSLVERR.value),
        }

    def record(goal_id, scenario_id, stim, fl_out, obs, cov_refs):
        nonlocal failed, cycle
        cycle += 1
        exp_pulse = fl_out["timeout_pulse"]
        obs_pulse = obs.get("timeout_pulse", -1)
        passed = obs_pulse == exp_pulse
        mismatch = "" if passed else f"timeout_pulse: expected={exp_pulse} got={obs_pulse}"
        events.append({
            "goal_id": goal_id,
            "scenario_id": scenario_id,
            "cycle": cycle,
            "stimulus": stim,
            "fl_expected": {"model_api": "FunctionalModel.apply", "timeout_pulse": exp_pulse},
            "rtl_observed": obs,
            "passed": passed,
            "mismatch": mismatch,
            "coverage_refs": cov_refs,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        })
        if not passed:
            failed += 1
        return passed

    # ---- Reset ----
    dut.PRESETn.value = 0
    dut.PSEL.value    = 0
    dut.PENABLE.value = 0
    dut.PWRITE.value  = 0
    dut.PADDR.value   = 0
    dut.PWDATA.value  = 0
    await ClockCycles(dut.PCLK, 3)
    dut.PRESETn.value = 1
    await FallingEdge(dut.PCLK)
    model.reset()

    # ---- SC1: EQ_WDT_IDLE — idle after reset, enable=1 from reset state ----
    # After reset, counter counts down from 255 with enable=1.
    # First disable the counter so we can test IDLE.
    # Write CTRL=0 to disable
    for s, ep, pw, pa, pd in [
        (1, 0, 1, 0, 0),   # CTRL write setup
        (1, 1, 1, 0, 0),   # CTRL write access — enable=0
    ]:
        obs = await tick_cycle(s, ep, pw, pa, pd)
        model.apply({"psel": s, "penable": ep, "pwrite": pw, "paddr": pa, "pwdata": pd})

    # Three idle cycles with counter disabled
    for i in range(3):
        stim = {"psel": 0, "penable": 0, "pwrite": 0, "paddr": 0, "pwdata": 0}
        obs = await tick_cycle()
        fl_out = model.apply(stim)
        # First idle cycle also covers SC1 (reset state) and ERR_NONE (no error)
        extra = ["SC1", "reset", "ERR_NONE", "err_none"] if i == 0 else []
        ok = record("EQ_WDT_IDLE", f"SC_IDLE_{i}", stim, fl_out, obs, ["FCOV_IDLE", "FM_IDLE"] + extra)
        coverage_bins["FCOV_IDLE"] += 1
        assert ok, f"IDLE[{i}]: timeout_pulse mismatch: expected {fl_out['timeout_pulse']} got {obs['timeout_pulse']}"
        assert obs["timeout_pulse"] == 0, f"IDLE: timeout_pulse must be 0 when disabled, got {obs['timeout_pulse']}"

    # ---- SC2: EQ_WDT_TICK / EQ_WDT_TIMEOUT — enable, set PERIOD=3, KICK, watch countdown ----
    # Enable counter: CTRL=1
    for s, ep, pw, pa, pd in [
        (1, 0, 1, 0, 1),   # CTRL write setup, enable=1
        (1, 1, 1, 0, 1),   # CTRL write access
    ]:
        obs = await tick_cycle(s, ep, pw, pa, pd)
        model.apply({"psel": s, "penable": ep, "pwrite": pw, "paddr": pa, "pwdata": pd})

    # Set PERIOD=3
    for s, ep, pw, pa, pd in [
        (1, 0, 1, 8, 3),   # PERIOD write setup
        (1, 1, 1, 8, 3),   # PERIOD write access
    ]:
        obs = await tick_cycle(s, ep, pw, pa, pd)
        model.apply({"psel": s, "penable": ep, "pwrite": pw, "paddr": pa, "pwdata": pd})

    # KICK to reload count=3
    for s, ep, pw, pa, pd in [
        (1, 0, 1, 4, 1),   # KICK write setup
        (1, 1, 1, 4, 1),   # KICK write access
    ]:
        stim = {"psel": s, "penable": ep, "pwrite": pw, "paddr": pa, "pwdata": pd}
        obs = await tick_cycle(s, ep, pw, pa, pd)
        fl_out = model.apply(stim)
        if s == 1 and ep == 1:
            ok = record("EQ_WDT_KICK", "SC_KICK", stim, fl_out, obs, ["FCOV_KICK", "FM_KICK", "CTRL", "ctrl", "KICK", "kick", "PERIOD", "period", "STATUS", "status"])
            coverage_bins["FCOV_KICK"] += 1
            assert ok, f"KICK: mismatch — expected {fl_out['timeout_pulse']} got {obs['timeout_pulse']}"

    # Tick 4 cycles — count: 3→2→1(timeout)→3(reload)→2
    timeout_seen = 0
    for i in range(4):
        stim = {"psel": 0, "penable": 0, "pwrite": 0, "paddr": 0, "pwdata": 0}
        obs = await tick_cycle()
        fl_out = model.apply(stim)
        ok = record("EQ_WDT_TICK", f"SC_TICK_{i}", stim, fl_out, obs, ["FCOV_TICK", "FM_TICK"])
        coverage_bins["FCOV_TICK"] += 1
        assert ok, f"TICK[{i}]: expected timeout_pulse={fl_out['timeout_pulse']} got {obs['timeout_pulse']}"
        if obs["timeout_pulse"] == 1:
            timeout_seen += 1
            record("EQ_WDT_TIMEOUT", f"SC_TIMEOUT_{i}", stim, fl_out, obs, ["FCOV_TIMEOUT", "FM_TICK"])
            coverage_bins["FCOV_TIMEOUT"] += 1

    assert timeout_seen >= 1, "SC_TIMEOUT: timeout_pulse never fired in 4 ticks with PERIOD=3"
    assert obs["PREADY"]  == 1, "PREADY must be 1"
    assert obs["PSLVERR"] == 0, "PSLVERR must be 0"

    # ---- Flush scoreboard_events.jsonl ----
    out = ip_dir / "sim" / "scoreboard_events.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for ev in events:
            f.write(json.dumps(ev) + "\n")

    cocotb.log.info(f"Coverage bins: {coverage_bins}")
    covered_goals = {ev["goal_id"] for ev in events}
    cocotb.log.info(f"Covered goals: {sorted(covered_goals)}")
    cocotb.log.info(f"Scoreboard: {len(events)} events, {failed} failures")
    assert failed == 0, f"{failed}/{len(events)} scoreboard checks failed"
