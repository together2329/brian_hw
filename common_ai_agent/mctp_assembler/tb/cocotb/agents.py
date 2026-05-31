from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from cocotb.triggers import FallingEdge, ReadOnly, RisingEdge
from pyuvm import uvm_driver, uvm_monitor

_MODEL_DIR = Path(__file__).resolve().parents[2] / "model"
if str(_MODEL_DIR) not in sys.path:
    sys.path.insert(0, str(_MODEL_DIR))
from functional_model import AXI_DATA_BYTES  # noqa: E402


class ApbMaster(uvm_driver):
    """APB master driver on pclk."""

    def __init__(self, name: str = "apb_master", parent=None):
        super().__init__(name, parent)
        self.dut = None
        self.clock_name = "pclk"

    def bind(self, dut, clock_name: str = "pclk") -> None:
        self.dut = dut
        self.clock_name = clock_name

    def _clk(self):
        return getattr(self.dut, self.clock_name)

    async def reset_bus(self) -> None:
        dut = self.dut
        dut.psel.value = 0
        dut.penable.value = 0
        dut.pwrite.value = 0
        dut.paddr.value = 0
        dut.pwdata.value = 0
        dut.pstrb.value = 0

    async def write(self, addr: int, data: int, strobe: int = 0xF) -> None:
        dut = self.dut
        clk = self._clk()
        await FallingEdge(clk)
        dut.paddr.value = int(addr)
        dut.pwdata.value = int(data)
        dut.pwrite.value = 1
        dut.pstrb.value = int(strobe) & 0xF
        dut.psel.value = 1
        dut.penable.value = 0
        await RisingEdge(clk)
        await FallingEdge(clk)
        dut.penable.value = 1
        for _ in range(16):
            await RisingEdge(clk)
            await ReadOnly()
            if int(dut.pready.value) == 1:
                break
        await FallingEdge(clk)
        dut.psel.value = 0
        dut.penable.value = 0
        dut.pwrite.value = 0

    async def read(self, addr: int) -> int:
        dut = self.dut
        clk = self._clk()
        await FallingEdge(clk)
        dut.paddr.value = int(addr)
        dut.pwrite.value = 0
        dut.psel.value = 1
        dut.penable.value = 0
        await RisingEdge(clk)
        await FallingEdge(clk)
        dut.penable.value = 1
        for _ in range(16):
            await RisingEdge(clk)
            await ReadOnly()
            if int(dut.pready.value) == 1:
                break
        await ReadOnly()
        data = int(dut.prdata.value)
        await FallingEdge(clk)
        dut.psel.value = 0
        dut.penable.value = 0
        return data


class ApbMonitor(uvm_monitor):
    def __init__(self, name: str = "apb_monitor", parent=None):
        super().__init__(name, parent)
        self.observed: list[dict[str, Any]] = []

    def record(self, kind: str, addr: int, data: int) -> None:
        self.observed.append({"kind": kind, "addr": addr, "data": data})


class AxiWriteMaster(uvm_driver):
    """AXI4 write-only master for one-burst-one-TLP ingress."""

    def __init__(self, name: str = "axi_master", parent=None):
        super().__init__(name, parent)
        self.dut = None
        self.clock_name = "axi_aclk"

    def bind(self, dut, clock_name: str = "axi_aclk") -> None:
        self.dut = dut
        self.clock_name = clock_name

    def _clk(self):
        return getattr(self.dut, self.clock_name)

    async def reset_bus(self) -> None:
        dut = self.dut
        dut.s_axi_awaddr.value = 0
        dut.s_axi_awlen.value = 0
        dut.s_axi_awsize.value = 5  # 256-bit
        dut.s_axi_awburst.value = 1  # INCR
        dut.s_axi_awvalid.value = 0
        dut.s_axi_wdata.value = 0
        dut.s_axi_wstrb.value = 0
        dut.s_axi_wlast.value = 0
        dut.s_axi_wvalid.value = 0
        dut.s_axi_bready.value = 0

    async def write_burst(self, awaddr: int, beats: list, timeout: int = 5000) -> int:
        dut = self.dut
        clk = self._clk()
        awlen = max(len(beats) - 1, 0)
        dut.s_axi_awaddr.value = int(awaddr)
        dut.s_axi_awlen.value = awlen
        dut.s_axi_awsize.value = 5
        dut.s_axi_awburst.value = 1
        dut.s_axi_awvalid.value = 1
        dut.s_axi_bready.value = 1
        for _ in range(timeout):
            await RisingEdge(clk)
            if int(dut.s_axi_awready.value):
                break
        else:
            raise TimeoutError(f"AXI awready timeout after {timeout} cycles")
        dut.s_axi_awvalid.value = 0

        for beat in beats:
            data = beat.data if hasattr(beat, "data") else beat["data"]
            wstrb = beat.wstrb if hasattr(beat, "wstrb") else beat["wstrb"]
            wlast = beat.wlast if hasattr(beat, "wlast") else beat["wlast"]
            dut.s_axi_wdata.value = int(data)
            dut.s_axi_wstrb.value = int(wstrb)
            dut.s_axi_wlast.value = 1 if wlast else 0
            dut.s_axi_wvalid.value = 1
            for _ in range(timeout):
                await RisingEdge(clk)
                if int(dut.s_axi_wready.value):
                    break
            else:
                raise TimeoutError(f"AXI wready timeout after {timeout} cycles")
            dut.s_axi_wvalid.value = 0
            dut.s_axi_wlast.value = 0

        bresp = 0
        for _ in range(timeout):
            await RisingEdge(clk)
            if int(dut.s_axi_bvalid.value):
                bresp = int(dut.s_axi_bresp.value)
                break
        else:
            raise TimeoutError(f"AXI bvalid timeout after {timeout} cycles")
        await RisingEdge(clk)
        dut.s_axi_bready.value = 0
        return bresp


class AxiReadMaster(uvm_driver):
    """AXI4 read-only master for SRAM payload readback."""

    def __init__(self, name: str = "axi_read_master", parent=None):
        super().__init__(name, parent)
        self.dut = None
        self.clock_name = "axi_aclk"

    def bind(self, dut, clock_name: str = "axi_aclk") -> None:
        self.dut = dut
        self.clock_name = clock_name

    def _clk(self):
        return getattr(self.dut, self.clock_name)

    async def reset_bus(self) -> None:
        dut = self.dut
        dut.s_axi_araddr.value = 0
        dut.s_axi_arlen.value = 0
        dut.s_axi_arsize.value = 5
        dut.s_axi_arburst.value = 1
        dut.s_axi_arvalid.value = 0
        dut.s_axi_rready.value = 0

    async def read_burst(
        self,
        araddr: int,
        arlen: int = 0,
        arsize: int = 5,
        arburst: int = 1,
        timeout: int = 5000,
    ) -> list[dict[str, int]]:
        dut = self.dut
        clk = self._clk()
        dut.s_axi_araddr.value = int(araddr)
        dut.s_axi_arlen.value = int(arlen)
        dut.s_axi_arsize.value = int(arsize)
        dut.s_axi_arburst.value = int(arburst)
        dut.s_axi_arvalid.value = 1
        dut.s_axi_rready.value = 1
        accepted = False
        for _ in range(timeout):
            await RisingEdge(clk)
            await ReadOnly()
            if int(dut.s_axi_arready.value) and int(dut.s_axi_arvalid.value):
                accepted = True
                break
        if not accepted:
            raise TimeoutError(f"AXI arready timeout after {timeout} cycles")
        await RisingEdge(clk)
        dut.s_axi_arvalid.value = 0

        beats: list[dict[str, int]] = []
        expected = arlen + 1
        while len(beats) < expected:
            for _ in range(timeout):
                await RisingEdge(clk)
                await ReadOnly()
                if int(dut.s_axi_rvalid.value):
                    beats.append(
                        {
                            "data": int(dut.s_axi_rdata.value),
                            "rresp": int(dut.s_axi_rresp.value),
                            "rlast": int(dut.s_axi_rlast.value),
                        }
                    )
                    break
            else:
                raise TimeoutError(f"AXI rvalid timeout after {timeout} cycles")
            if beats[-1]["rlast"]:
                break
        await RisingEdge(clk)
        dut.s_axi_rready.value = 0
        return beats


class SramMonitor(uvm_monitor):
    """Capture SRAM write beats from the DUT payload writer."""

    def __init__(self, name: str = "sram_monitor", parent=None):
        super().__init__(name, parent)
        self.dut = None
        self.clock_name = "axi_aclk"
        self.memory: dict[int, int] = {}
        self.write_log: list[dict[str, Any]] = []
        self._task = None

    def bind(self, dut, clock_name: str = "axi_aclk") -> None:
        self.dut = dut
        self.clock_name = clock_name

    async def run(self) -> None:
        dut = self.dut
        clk = getattr(dut, self.clock_name)
        while True:
            await FallingEdge(clk)
            if int(dut.sram_rd_valid.value):
                addr = int(dut.sram_rd_addr.value)
                packed = 0
                for lane in range(AXI_DATA_BYTES):
                    byte_val = self.memory.get(addr + lane, 0)
                    packed |= byte_val << (8 * lane)
                dut.sram_rd_data.value = packed
            await RisingEdge(clk)
            await ReadOnly()
            if int(dut.sram_wr_valid.value) and int(dut.sram_wr_ready.value):
                addr = int(dut.sram_wr_addr.value)
                data = int(dut.sram_wr_data.value)
                strb = int(dut.sram_wr_strb.value)
                for lane in range(AXI_DATA_BYTES):
                    if (strb >> lane) & 1:
                        byte_addr = addr + lane
                        byte_val = (data >> (8 * lane)) & 0xFF
                        self.memory[byte_addr] = byte_val
                self.write_log.append({"addr": addr, "data": data, "strb": strb})

    def read_bytes(self, start: int, count: int) -> list[int]:
        return [self.memory.get(start + idx, 0) for idx in range(count)]
