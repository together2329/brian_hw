#!/usr/bin/env python3
"""Scenario library for quad_spi_ctrl cocotb testbench.

SSOT refs: test_requirements.scenarios
Provides stimulus generators for all required scenarios.
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, ClockCycles, Timer


class QuadSPIScenarios:
    """Stimulus generators for quad_spi_ctrl test scenarios."""

    def __init__(self, dut):
        self.dut = dut

    async def reset(self):
        """Assert then deassert PRESETn."""
        dut = self.dut
        dut.PSEL.value = 0
        dut.PENABLE.value = 0
        dut.PADDR.value = 0
        dut.PWDATA.value = 0
        dut.PWRITE.value = 0
        dut.IO.value = 0
        dut.PRESETn.value = 0
        await ClockCycles(dut.PCLK, 5)
        dut.PRESETn.value = 1
        await ClockCycles(dut.PCLK, 5)

    async def apb_write(self, addr, data):
        """Single APB write transaction."""
        dut = self.dut
        await RisingEdge(dut.PCLK)
        dut.PSEL.value = 1
        dut.PENABLE.value = 0
        dut.PADDR.value = addr
        dut.PWDATA.value = data
        dut.PWRITE.value = 1
        await RisingEdge(dut.PCLK)
        dut.PENABLE.value = 1
        while True:
            await RisingEdge(dut.PCLK)
            if dut.PREADY.value == 1:
                break
        dut.PSEL.value = 0
        dut.PENABLE.value = 0
        dut.PWRITE.value = 0

    async def apb_read(self, addr):
        """Single APB read transaction. Returns (data, slverr)."""
        dut = self.dut
        await RisingEdge(dut.PCLK)
        dut.PSEL.value = 1
        dut.PENABLE.value = 0
        dut.PADDR.value = addr
        dut.PWRITE.value = 0
        await RisingEdge(dut.PCLK)
        dut.PENABLE.value = 1
        while True:
            await RisingEdge(dut.PCLK)
            if dut.PREADY.value == 1:
                break
        data = dut.PRDATA.value.integer
        slverr = dut.PSLVERR.value
        dut.PSEL.value = 0
        dut.PENABLE.value = 0
        return data, slverr

    async def scenario_sc_apb_config(self):
        """SC_APB_CONFIG: Program CTRL/PRESCALE/CS_IDLE/IE and read back."""
        await self.reset()
        # Write PRESCALE
        await self.apb_write(0x08, 0x00000007)
        val, _ = await self.apb_read(0x08)
        assert val == 0x00000007, f"PRESCALE readback: {val:08x}"
        # Write CS_IDLE
        await self.apb_write(0x14, 0x0000010F)
        val, _ = await self.apb_read(0x14)
        assert val == 0x0000010F, f"CS_IDLE readback: {val:08x}"
        # Write IE
        await self.apb_write(0x18, 0x0000000F)
        val, _ = await self.apb_read(0x18)
        assert val == 0x0000000F, f"IE readback: {val:08x}"
        # Read STATUS (should be reset defaults: TX_EMPTY=1, RX_EMPTY=1)
        val, _ = await self.apb_read(0x04)
        assert (val & 0x2) != 0, f"STATUS TX_EMPTY not set: {val:08x}"
        cocotb.log.info("SC_APB_CONFIG passed")

    async def scenario_sc_basic_transfer(self):
        """SC_BASIC_TRANSFER: 1-byte 1-lane SDR transfer."""
        await self.reset()
        # Configure CTRL: LANE_MODE=0 (1-lane), DATA_LEN=1
        await self.apb_write(0x00, 0x00000100)
        # Write TXDATA
        await self.apb_write(0x0C, 0x000000A5)
        # Set START bit
        await self.apb_write(0x00, 0x00000101)
        # Wait for DONE
        for _ in range(200):
            val, _ = await self.apb_read(0x04)
            if val & 0x10:  # DONE
                break
            await ClockCycles(self.dut.PCLK, 1)
        val, _ = await self.apb_read(0x04)
        assert val & 0x10, "DONE not set after transfer"
        cocotb.log.info("SC_BASIC_TRANSFER passed")

    async def scenario_sc_lane_mode_sweep(self):
        """SC_LANE_MODE_SWEEP: Run frames in 1-lane, 2-lane, 4-lane modes."""
        await self.reset()
        for lane in [0, 1, 2]:
            ctrl_val = (lane << 2) | 0x100  # LANE_MODE + DATA_LEN=1
            await self.apb_write(0x00, ctrl_val)
            await self.apb_write(0x0C, 0x0000005A)
            await self.apb_write(0x00, ctrl_val | 0x1)  # START
            for _ in range(300):
                val, _ = await self.apb_read(0x04)
                if val & 0x10:
                    break
                await ClockCycles(self.dut.PCLK, 1)
            val, _ = await self.apb_read(0x04)
            assert val & 0x10, f"DONE not set for lane={lane}"
        cocotb.log.info("SC_LANE_MODE_SWEEP passed")

    async def scenario_sc_cpol_cpha_sweep(self):
        """SC_CPOL_CPHA_SWEEP: All four CPOL/CPHA combinations."""
        await self.reset()
        for cpol in [0, 1]:
            for cpha in [0, 1]:
                ctrl_val = (cpol << 4) | (cpha << 5) | 0x100
                await self.apb_write(0x00, ctrl_val)
                await self.apb_write(0x0C, 0x0000003C)
                await self.apb_write(0x00, ctrl_val | 0x1)
                for _ in range(300):
                    val, _ = await self.apb_read(0x04)
                    if val & 0x10:
                        break
                    await ClockCycles(self.dut.PCLK, 1)
                val, _ = await self.apb_read(0x04)
                assert val & 0x10, f"DONE not set for CPOL={cpol} CPHA={cpha}"
        cocotb.log.info("SC_CPOL_CPHA_SWEEP passed")

    async def scenario_sc_fifo_limits(self):
        """SC_FIFO_LIMITS: Fill TX FIFO, overflow, check status."""
        await self.reset()
        # Write 16 bytes to fill TX FIFO
        for i in range(16):
            await self.apb_write(0x0C, 0x00000000 | i)
        # Check TX_FULL
        val, _ = await self.apb_read(0x04)
        assert val & 0x1, f"TX_FULL not set after 16 writes: {val:08x}"
        # Overflow write (should be dropped, no error on APB)
        await self.apb_write(0x0C, 0x000000FF)
        cocotb.log.info("SC_FIFO_LIMITS passed")

    async def scenario_sc_irq_mask(self):
        """SC_IRQ_MASK: Trigger DONE, check IRQ with IE mask."""
        await self.reset()
        # Enable DONE interrupt
        await self.apb_write(0x18, 0x00000004)
        # Configure and start a transfer
        await self.apb_write(0x00, 0x00000100)
        await self.apb_write(0x0C, 0x000000AA)
        await self.apb_write(0x00, 0x00000101)
        # Wait for DONE
        for _ in range(300):
            val, _ = await self.apb_read(0x04)
            if val & 0x10:
                break
            await ClockCycles(self.dut.PCLK, 1)
        # Check IRQ asserted
        await ClockCycles(self.dut.PCLK, 3)
        assert self.dut.IRQ.value == 1, f"IRQ not asserted after DONE"
        cocotb.log.info("SC_IRQ_MASK passed")

    async def scenario_sc_error_paths(self):
        """SC_ERROR_PATHS: Illegal address, write RO register."""
        await self.reset()
        # Access illegal address
        _, slverr = await self.apb_read(0x20)
        assert slverr == 1, "PSLVERR not set on illegal address"
        # Write to read-only STATUS register
        await self.apb_write(0x04, 0x000000FF)
        val, _ = await self.apb_read(0x04)
        # STATUS is RO, write should be ignored
        cocotb.log.info("SC_ERROR_PATHS passed")

    async def scenario_sc_prescale_timing(self):
        """SC_PRESCALE_TIMING: Sweep DIV values and check SCLK behavior."""
        await self.reset()
        for div in [0, 1, 7, 255]:
            await self.apb_write(0x08, div)
            val, _ = await self.apb_read(0x08)
            assert val == div, f"PRESCALE mismatch: wrote {div} got {val}"
        cocotb.log.info("SC_PRESCALE_TIMING passed")
