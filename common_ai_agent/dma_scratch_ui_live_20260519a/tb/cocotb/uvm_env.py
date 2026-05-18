"""UVM-style environment wiring for DMA scratch UI verification.

SSOT traceability:
  - io_list → DUT signal map
  - test_requirements.scenarios → test dispatch
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge
from cocotb.log import SimLog

from transactions import CsrTransaction
from agents import (CsrAgent, ReadAddrMonitor, ReadDataDriver,
                    WriteMonitor, WriteBackpressure, ReadBackpressure,
                    IrqMonitor)
from scoreboard import DmaScoreboard
from coverage import FunctionalCoverage
from sequences import SCENARIOS


class DmaEnv:
    """Top-level cocotb verification environment.

    Instantiates agents, scoreboard, coverage, and orchestrates
    scenario execution.
    """

    def __init__(self, dut):
        self.dut = dut
        self.log = SimLog("DmaEnv")

        # Agents
        self.csr_agent = CsrAgent(dut, log=SimLog("CsrAgent"))
        self.rd_driver = ReadDataDriver(dut, log=SimLog("ReadDataDriver"))
        self.rd_addr_mon = ReadAddrMonitor(dut, log=SimLog("ReadAddrMon"))
        self.wr_mon = WriteMonitor(dut, log=SimLog("WriteMon"))
        self.wr_bp = WriteBackpressure(dut, log=SimLog("WriteBP"))
        self.rd_bp = ReadBackpressure(dut, log=SimLog("ReadBP"))
        self.irq_mon = IrqMonitor(dut, log=SimLog("IrqMon"))

        # Scoreboard and coverage
        self.sb = DmaScoreboard()
        self.cov = FunctionalCoverage()

        # Results
        self.scenario_results = {}  # scenario_id → bool
        self.dut_errors = 0

    async def setup(self):
        """Initialize the environment: clock, reset, agent defaults."""
        # Start clock
        clock = Clock(self.dut.clk, 10, units="ns")
        cocotb.start_soon(clock.start())

        # Initial reset
        self.dut.rst_n.value = 0
        self.dut.csr_valid.value = 0
        self.dut.csr_write.value = 0
        self.dut.csr_addr.value = 0
        self.dut.csr_wdata.value = 0
        self.dut.mem_rd_ready.value = 1
        self.dut.mem_rd_data_valid.value = 0
        self.dut.mem_rd_data.value = 0
        self.dut.mem_wr_ready.value = 1

        await ClockCycles(self.dut.clk, 5)

    async def run_scenario(self, sc_id: str, sc_func):
        """Run a single scenario and record its pass/fail."""
        self.log.info(f"--- Running {sc_id} ---")
        try:
            result = await sc_func(self.dut, self.csr_agent, self.rd_driver,
                                   self.sb, self.cov, self.log)
            self.scenario_results[sc_id] = bool(result)
        except Exception as e:
            self.log.error(f"[FAIL] {sc_id}: exception: {e}")
            import traceback
            traceback.print_exc()
            self.scenario_results[sc_id] = False
            self.dut_errors += 1

    async def run_all(self):
        """Run all SSOT scenarios in order."""
        await self.setup()

        for sc_id, sc_func in SCENARIOS:
            await self.run_scenario(sc_id, sc_func)

        # Summary
        passed = sum(1 for v in self.scenario_results.values() if v)
        total = len(self.scenario_results)
        self.log.info("=" * 60)
        self.log.info(f"SIMULATION COMPLETE: {passed}/{total} scenarios PASS")
        self.log.info(f"Scoreboard: {self.sb.summary()}")
        self.log.info(f"Coverage: {self.cov.summary()}")

        if self.sb.all_failures:
            self.log.error("FAILURES:")
            for sid, msgs in self.sb.all_failures.items():
                for msg in msgs:
                    self.log.error(f"  {sid}: {msg}")

        return passed, total
