"""Counter agent — Driver, Monitor, and Sequencer for UVM-style cocotb testbench."""

import cocotb
from cocotb.triggers import RisingEdge, ReadOnly, NextTimeStep
from cocotb.clock import Clock

from counter_txn import CounterTxn, CounterOutput


class CounterDriver:
    """Drives stimulus onto the DUT input signals each clock cycle.

    Usage:
        driver = CounterDriver(dut)
        await driver.send(txn)          # drive one transaction
        await driver.send_seq(txn_list) # drive a sequence of transactions
    """

    def __init__(self, dut):
        self.dut = dut
        self._log = dut._log

    async def _set_signals(self, txn: CounterTxn) -> None:
        """Apply transaction values to DUT inputs (before clock edge)."""
        self.dut.en.value      = txn.en
        self.dut.load.value    = txn.load
        self.dut.up_down.value = txn.up_down
        self.dut.data_in.value = txn.data_in

    async def send(self, txn: CounterTxn) -> None:
        """Drive a single transaction: set signals, wait one clock edge."""
        await RisingEdge(self.dut.clk)
        await self._set_signals(txn)
        await RisingEdge(self.dut.clk)

    async def send_seq(self, txns: list) -> None:
        """Drive a sequence of transactions, one per clock cycle."""
        for txn in txns:
            await RisingEdge(self.dut.clk)
            await self._set_signals(txn)
        # Wait one extra clock so last txn takes effect
        await RisingEdge(self.dut.clk)

    async def idle(self, cycles: int = 1) -> None:
        """Drive idle (en=0, load=0) for N cycles."""
        idle_txn = CounterTxn(en=0, load=0)
        for _ in range(cycles):
            await RisingEdge(self.dut.clk)
            await self._set_signals(idle_txn)
        await RisingEdge(self.dut.clk)

    async def apply_reset(self, cycles: int = 2) -> None:
        """Assert synchronous reset (rst_n=0) for given cycles."""
        self.dut.rst_n.value = 0
        for _ in range(cycles):
            await RisingEdge(self.dut.clk)
        self.dut.rst_n.value = 1
        await RisingEdge(self.dut.clk)
        self._log.info("Reset applied")


class CounterMonitor:
    """Observes DUT output signals after each clock edge.

    Usage:
        monitor = CounterMonitor(dut)
        output = await monitor.sample()  # sample one cycle
    """

    def __init__(self, dut):
        self.dut = dut
        self._log = dut._log

    async def sample(self) -> CounterOutput:
        """Wait for rising edge then read outputs."""
        await RisingEdge(self.dut.clk)
        await ReadOnly()
        return CounterOutput(
            count_out=int(self.dut.count_out.value),
            overflow=int(self.dut.overflow.value),
        )

    async def sample_now(self) -> CounterOutput:
        """Read outputs immediately (no clock wait) — use after RisingEdge."""
        await ReadOnly()
        return CounterOutput(
            count_out=int(self.dut.count_out.value),
            overflow=int(self.dut.overflow.value),
        )


class CounterSequencer:
    """Generates stimulus sequences for the counter.

    Provides factory methods for common test patterns.
    """

    @staticmethod
    def count_up(n: int, data_in: int = 0) -> list:
        """Generate N transactions counting up (en=1, up_down=0)."""
        return [CounterTxn(en=1, load=0, up_down=0, data_in=data_in) for _ in range(n)]

    @staticmethod
    def count_down(n: int, data_in: int = 0) -> list:
        """Generate N transactions counting down (en=1, up_down=1)."""
        return [CounterTxn(en=1, load=0, up_down=1, data_in=data_in) for _ in range(n)]

    @staticmethod
    def load_value(value: int) -> CounterTxn:
        """Generate a single load transaction."""
        return CounterTxn(en=1, load=1, up_down=0, data_in=value)

    @staticmethod
    def hold(n: int = 1) -> list:
        """Generate N hold transactions (en=0, load=0)."""
        return [CounterTxn(en=0, load=0, up_down=0, data_in=0) for _ in range(n)]

    @staticmethod
    def random(n: int, width: int = 8) -> list:
        """Generate N random transactions."""
        return [CounterTxn().randomize(width) for _ in range(n)]
