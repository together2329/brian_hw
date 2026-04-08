"""Top-level cocotb environment connecting agent, reference model, and scoreboard.

Provides a single entry-point to drive stimulus, predict expected outputs,
sample DUT outputs, and compare them automatically.
"""

import cocotb
from cocotb.triggers import RisingEdge, NextTimeStep
from cocotb.clock import Clock

from counter_txn import CounterTxn, CounterOutput
from counter_agent import CounterDriver, CounterMonitor, CounterSequencer
from counter_ref_model import CounterRefModel
from counter_scoreboard import CounterScoreboard


class CounterEnv:
    """Cocotb testbench environment for the parameterized up/down counter.

    Wires together:
        - CounterDriver   (stimulus)
        - CounterMonitor  (output observation)
        - CounterRefModel (golden prediction)
        - CounterScoreboard (comparison)

    Usage:
        env = CounterEnv(dut, width=8)
        await env.setup()                # start clock, reset
        await env.run_sequence(txn_list) # drive & check
        assert env.scoreboard.report()   # verify all passed
    """

    def __init__(self, dut, width: int = 8):
        self.dut = dut
        self.width = width

        # Sub-components
        self.driver    = CounterDriver(dut)
        self.monitor   = CounterMonitor(dut)
        self.ref_model = CounterRefModel(width=width)
        self.scoreboard = CounterScoreboard()
        self.sequencer = CounterSequencer()

        self._log = dut._log

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    async def setup(self, reset_cycles: int = 2) -> None:
        """Start the clock, apply reset, and initialize the ref model.

        Must be called before any run_* method.
        """
        # Start clock (10 ns period → 100 MHz)
        cocotb.start_soon(Clock(self.dut.clk, 10, units="ns").start())

        # Drive initial inputs to safe defaults before reset
        self.dut.en.value      = 0
        self.dut.load.value    = 0
        self.dut.up_down.value = 0
        self.dut.data_in.value = 0
        await RisingEdge(self.dut.clk)

        # Apply synchronous reset
        await self.driver.apply_reset(cycles=reset_cycles)

        # Sync ref model to post-reset state
        self.ref_model.reset()
        self._log.info(f"CounterEnv setup complete (width={self.width})")

    # ------------------------------------------------------------------
    # Single-cycle operations
    # ------------------------------------------------------------------

    async def run_one(self, txn: CounterTxn, cycle: int = 0,
                      test_name: str = "") -> bool:
        """Drive one transaction through DUT and check against ref model.

        Steps:
            1. Apply inputs to DUT pins (combinational).
            2. Wait for rising edge — DUT registers inputs.
            3. Sample DUT outputs (ReadOnly phase).
            4. Predict expected outputs via ref model.
            5. Compare via scoreboard.

        Safe for back-to-back calls: no stale-input edge between invocations.

        Returns True if check passed.
        """
        # Apply inputs before the edge
        await self.driver._set_signals(txn)

        # Rising edge: DUT samples inputs and produces new outputs
        await RisingEdge(self.dut.clk)

        # Sample actual DUT output in ReadOnly phase
        actual = await self.monitor.sample_now()

        # Escape ReadOnly phase so next _set_signals can write
        await NextTimeStep()

        # Predict expected output (ref model advances one step)
        expected = self.ref_model.step(txn, rst_n=1)

        # Compare
        return self.scoreboard.compare(expected, actual, cycle, test_name)

    # ------------------------------------------------------------------
    # Multi-cycle sequences
    # ------------------------------------------------------------------

    async def run_sequence(self, txns: list, test_name: str = "") -> bool:
        """Drive a list of transactions, checking each cycle.

        Returns True if every cycle matched.
        """
        all_pass = True
        for i, txn in enumerate(txns):
            passed = await self.run_one(txn, cycle=i, test_name=test_name)
            if not passed:
                all_pass = False
        return all_pass

    async def run_random(self, n: int, test_name: str = "random") -> bool:
        """Drive N random transactions and check each cycle.

        Returns True if every cycle matched.
        """
        txns = self.sequencer.random(n, width=self.width)
        return await self.run_sequence(txns, test_name=test_name)

    # ------------------------------------------------------------------
    # Convenience operations
    # ------------------------------------------------------------------

    async def load_and_check(self, value: int, cycle: int = 0,
                             test_name: str = "load") -> bool:
        """Load a value and verify the DUT reflects it."""
        txn = self.sequencer.load_value(value)
        return await self.run_one(txn, cycle=cycle, test_name=test_name)

    async def count_up_and_check(self, n: int, test_name: str = "count_up") -> bool:
        """Count up N cycles and check each."""
        txns = self.sequencer.count_up(n)
        return await self.run_sequence(txns, test_name=test_name)

    async def count_down_and_check(self, n: int,
                                   test_name: str = "count_down") -> bool:
        """Count down N cycles and check each."""
        txns = self.sequencer.count_down(n)
        return await self.run_sequence(txns, test_name=test_name)

    async def hold_and_check(self, n: int, test_name: str = "hold") -> bool:
        """Hold for N cycles and check each."""
        txns = self.sequencer.hold(n)
        return await self.run_sequence(txns, test_name=test_name)

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------

    def report(self) -> bool:
        """Print scoreboard summary. Returns True if all checks passed."""
        return self.scoreboard.report()
