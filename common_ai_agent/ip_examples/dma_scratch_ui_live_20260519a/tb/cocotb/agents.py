"""Protocol agents for the DMA scratch UI — CSR, memory read/write, and IRQ.

SSOT traceability:
  - io_list.interfaces.csr_if          → CsrAgent
  - io_list.interfaces.mem_read_addr_if → ReadAddrMonitor
  - io_list.interfaces.mem_read_data_if → ReadDataDriver
  - io_list.interfaces.mem_write_if     → WriteMonitor
  - io_list.interfaces.interrupt_if     → IrqMonitor
"""

import random
import cocotb
from cocotb.triggers import (ClockCycles, RisingEdge, FallingEdge,
                              ReadOnly, Timer)
from cocotb.log import SimLog
from transactions import (CsrTransaction, CsrResponse, ReadBeat, WriteBeat,
                          CSR_CTRL, CSR_STATUS, CSR_SRC_ADDR, CSR_DST_ADDR,
                          CSR_LENGTH, CSR_PROGRESS, VALID_CSR_OFFSETS)


class CsrAgent:
    """Drives CSR requests on the valid/ready interface and collects responses.

    Protocol (from SSOT):
      - csr_valid && csr_ready → one accepted request per cycle
      - csr_addr/csr_write/csr_wdata stable while csr_valid=1 and csr_ready=0
      - csr_rdata/csr_error valid in the same cycle as acceptance
    """

    def __init__(self, dut, log=None):
        self.dut = dut
        self.log = log or SimLog("CsrAgent")

    async def reset(self):
        self.dut.csr_valid.value = 0
        self.dut.csr_write.value = 0
        self.dut.csr_addr.value = 0
        self.dut.csr_wdata.value = 0

    async def drive_request(self, txn: CsrTransaction, allow_stall: bool = False):
        """Drive one CSR request and return the response sampled at acceptance.

        If allow_stall is True, randomly inject up to 3 cycles of backpressure
        by pausing csr_valid.
        """
        self.dut.csr_valid.value = 1
        self.dut.csr_write.value = 1 if txn.is_write else 0
        self.dut.csr_addr.value = txn.addr
        self.dut.csr_wdata.value = txn.wdata

        stall_cycles = random.randint(0, 3) if allow_stall else 0

        while True:
            await RisingEdge(self.dut.clk)
            await ReadOnly()

            if stall_cycles > 0:
                # Insert stall: deassert valid for a cycle
                self.dut.csr_valid.value = 0
                stall_cycles -= 1
                continue

            self.dut.csr_valid.value = 1  # re-assert if it was deasserted
            if int(self.dut.csr_ready.value) == 1:
                # Accepted
                resp = CsrResponse(
                    rdata=int(self.dut.csr_rdata.value),
                    error=bool(int(self.dut.csr_error.value)),
                )
                self.dut.csr_valid.value = 0
                self.dut.csr_write.value = 0
                self.dut.csr_addr.value = 0
                self.dut.csr_wdata.value = 0
                return resp

    async def drive_write(self, addr: int, wdata: int, allow_stall: bool = False) -> CsrResponse:
        return await self.drive_request(CsrTransaction(addr, True, wdata), allow_stall)

    async def drive_read(self, addr: int, allow_stall: bool = False) -> CsrResponse:
        return await self.drive_request(CsrTransaction(addr, False, 0), allow_stall)


class ReadAddrMonitor:
    """Monitors read-address channel (mem_rd_valid/mem_rd_ready/mem_rd_addr).

    Records every accepted read address for scoreboard consumption.
    """

    def __init__(self, dut, log=None):
        self.dut = dut
        self.log = log or SimLog("ReadAddrMonitor")
        self.addresses = []  # list of (cycle, addr)

    async def run(self, stop_event):
        """Monitor loop; runs until stop_event is set."""
        while not stop_event.is_set():
            await RisingEdge(self.dut.clk)
            await ReadOnly()
            if int(self.dut.mem_rd_valid.value) and int(self.dut.mem_rd_ready.value):
                cycle = cocotb.utils.get_sim_time(units="ns") // 10  # 10 ns clock
                addr = int(self.dut.mem_rd_addr.value)
                self.addresses.append((cycle, addr))
                self.log.info(f"[CYC={cycle}] Read addr accepted: 0x{addr:08X}")


class ReadDataDriver:
    """Drives read-data responses (mem_rd_data_valid/mem_rd_data/mem_rd_data_ready).

    Used by the TB to inject synthetic read data into the DUT.
    Supports backpressure: randomly deasserts mem_rd_data_valid to test stall behavior.
    """

    def __init__(self, dut, log=None):
        self.dut = dut
        self.log = log or SimLog("ReadDataDriver")

    async def reset(self):
        self.dut.mem_rd_data_valid.value = 0
        self.dut.mem_rd_data.value = 0

    async def drive_beat(self, data: int, backpressure: bool = False,
                         stall_cycles: int = 0):
        """Drive one read-data beat. Wait for ready from DUT.

        If backpressure is True, may randomly stall mem_rd_data_valid.
        stall_cycles: explicit number of stall cycles (overrides random).
        """
        self.dut.mem_rd_data.value = data
        self.dut.mem_rd_data_valid.value = 1

        stalls_remaining = stall_cycles if stall_cycles > 0 else (
            random.randint(1, 5) if backpressure else 0
        )

        while True:
            await RisingEdge(self.dut.clk)
            await ReadOnly()

            if stalls_remaining > 0:
                self.dut.mem_rd_data_valid.value = 0
                stalls_remaining -= 1
                continue

            self.dut.mem_rd_data_valid.value = 1
            if int(self.dut.mem_rd_data_ready.value):
                self.dut.mem_rd_data_valid.value = 0
                return


class WriteMonitor:
    """Monitors write channel (mem_wr_valid/mem_wr_ready/mem_wr_addr/mem_wr_data/mem_wr_strb).

    Records every accepted write beat for scoreboard comparison.
    """

    def __init__(self, dut, log=None):
        self.dut = dut
        self.log = log or SimLog("WriteMonitor")
        self.writes = []  # list of (cycle, WriteBeat)

    async def run(self, stop_event):
        while not stop_event.is_set():
            await RisingEdge(self.dut.clk)
            await ReadOnly()
            if int(self.dut.mem_wr_valid.value) and int(self.dut.mem_wr_ready.value):
                cycle = cocotb.utils.get_sim_time(units="ns") // 10
                beat = WriteBeat(
                    addr=int(self.dut.mem_wr_addr.value),
                    data=int(self.dut.mem_wr_data.value),
                    strb=int(self.dut.mem_wr_strb.value),
                )
                self.writes.append((cycle, beat))
                self.log.info(f"[CYC={cycle}] Write accepted: {beat}")


class WriteBackpressure:
    """Controls mem_wr_ready to inject write-side backpressure."""

    def __init__(self, dut, log=None):
        self.dut = dut
        self.log = log or SimLog("WriteBackpressure")
        self._ready = True  # default: always ready

    def set_ready(self, val: bool):
        self._ready = bool(val)

    async def drive(self, stop_event):
        """Continuously drive mem_wr_ready."""
        while not stop_event.is_set():
            await RisingEdge(self.dut.clk)
            self.dut.mem_wr_ready.value = 1 if self._ready else 0


class ReadBackpressure:
    """Controls mem_rd_ready to inject read-address-side backpressure."""

    def __init__(self, dut, log=None):
        self.dut = dut
        self.log = log or SimLog("ReadBackpressure")
        self._ready = True

    def set_ready(self, val: bool):
        self._ready = bool(val)

    async def drive(self, stop_event):
        while not stop_event.is_set():
            await RisingEdge(self.dut.clk)
            self.dut.mem_rd_ready.value = 1 if self._ready else 0


class IrqMonitor:
    """Samples irq_done and irq_error every cycle."""

    def __init__(self, dut, log=None):
        self.dut = dut
        self.log = log or SimLog("IrqMonitor")
        self.irq_done_val = 0
        self.irq_error_val = 0

    async def sample(self):
        await ReadOnly()
        self.irq_done_val = int(self.dut.irq_done.value)
        self.irq_error_val = int(self.dut.irq_error.value)
        return self.irq_done_val, self.irq_error_val
