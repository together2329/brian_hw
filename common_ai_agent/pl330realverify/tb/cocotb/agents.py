#!/usr/bin/env python3
"""Protocol agents for pl330realverify cocotb/pyuvm TB.

Provides:
- ApbDriver: APB master driving paddr, psel, penable, pwrite, pwdata, pstrb
- ApbMonitor: observes prdata, pready, pslverr on completing APB transfers
- AxiMemoryModel: AXI4 memory BFM (responder) for read/write channels
- EventDriver: drives peripheral_events
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import (
    ClockCycles,
    FallingEdge,
    ReadOnly,
    RisingEdge,
    Timer,
)

from transactions import ApbTxn, AxiReadTxn, AxiWriteTxn, EventStimulus


# ─────────────────────────── APB Driver ────────────────────────────

class ApbDriver:
    """APB4 master driver — drives set-up and access phases on paddr/psel/penable/pwrite/pwdata/pstrb."""

    def __init__(self, dut, clock_period_ns: float = 2.0):
        self.dut = dut
        self.clock_period_ns = clock_period_ns

    async def reset(self):
        self.dut.paddr.value = 0
        self.dut.psel.value = 0
        self.dut.penable.value = 0
        self.dut.pwrite.value = 0
        self.dut.pwdata.value = 0
        self.dut.pstrb.value = 0

    async def write(self, addr: int, data: int, strb: int = 0xF):
        """Single APB write transaction."""
        # Setup phase
        self.dut.paddr.value = addr
        self.dut.psel.value = 1
        self.dut.penable.value = 0
        self.dut.pwrite.value = 1
        self.dut.pwdata.value = data
        self.dut.pstrb.value = strb
        await RisingEdge(self.dut.dmaclk)

        # Access phase
        self.dut.penable.value = 1
        await RisingEdge(self.dut.dmaclk)
        # Wait for pready
        while not self.dut.pready.value:
            await RisingEdge(self.dut.dmaclk)

        # Capture response then deassert
        pslverr_val = int(self.dut.pslverr.value)
        self.dut.psel.value = 0
        self.dut.penable.value = 0
        self.dut.pwrite.value = 0
        self.dut.paddr.value = 0
        self.dut.pwdata.value = 0
        self.dut.pstrb.value = 0
        return {"pslverr": pslverr_val}

    async def read(self, addr: int) -> dict:
        """Single APB read transaction. Returns {rdata, pslverr}."""
        # Setup phase
        self.dut.paddr.value = addr
        self.dut.psel.value = 1
        self.dut.penable.value = 0
        self.dut.pwrite.value = 0
        self.dut.pwdata.value = 0
        self.dut.pstrb.value = 0
        await RisingEdge(self.dut.dmaclk)

        # Access phase
        self.dut.penable.value = 1
        await RisingEdge(self.dut.dmaclk)
        while not self.dut.pready.value:
            await RisingEdge(self.dut.dmaclk)

        rdata_val = int(self.dut.prdata.value)
        pslverr_val = int(self.dut.pslverr.value)

        self.dut.psel.value = 0
        self.dut.penable.value = 0
        return {"rdata": rdata_val, "pslverr": pslverr_val}


# ─────────────────────────── APB Monitor ────────────────────────────

class ApbMonitor:
    """APB4 monitor — observes completing transfers on prdata/pready/pslverr."""

    def __init__(self, dut):
        self.dut = dut
        self.events: list[dict] = []

    async def run(self):
        """Continuously monitor APB bus for completed transfers."""
        while True:
            await RisingEdge(self.dut.dmaclk)
            if self.dut.psel.value and self.dut.penable.value and self.dut.pready.value:
                event = {
                    "cycle": cocotb.utils.get_sim_time(units="ns") // 2,  # approx cycle
                    "paddr": int(self.dut.paddr.value),
                    "pwrite": int(self.dut.pwrite.value),
                    "pwdata": int(self.dut.pwdata.value),
                    "prdata": int(self.dut.prdata.value),
                    "pready": 1,
                    "pslverr": int(self.dut.pslverr.value),
                }
                self.events.append(event)


# ─────────────────────── AXI Memory Model ────────────────────────────

@dataclass
class AxiMemoryRegion:
    base: int = 0
    size: int = 0x10000
    data: bytearray = field(default_factory=lambda: bytearray(0x10000))

    def read(self, addr: int, nbytes: int) -> bytes:
        off = addr - self.base
        if 0 <= off + nbytes <= len(self.data):
            return bytes(self.data[off : off + nbytes])
        return b"\x00" * nbytes

    def write(self, addr: int, data_bytes: bytes):
        off = addr - self.base
        if 0 <= off + len(data_bytes) <= len(self.data):
            self.data[off : off + len(data_bytes)] = data_bytes


class AxiMemoryModel:
    """AXI4 memory BFM — responds to AR/AW/W with R/B channels.

    Supports single-outstanding reads/writes per channel, configurable
    response latency and error injection.
    """

    def __init__(self, dut, regions: list = None, seed: int = 42):
        self.dut = dut
        self.rng = random.Random(seed)
        self.regions: list[AxiMemoryRegion] = regions or [
            AxiMemoryRegion(base=0, size=0x10000)
        ]
        # Backpressure / random delay controls
        self.ar_delay_min = 0
        self.ar_delay_max = 1
        self.r_delay_min = 0
        self.r_delay_max = 1
        self.aw_delay_min = 0
        self.aw_delay_max = 1
        self.w_delay_min = 0
        self.w_delay_max = 1
        self.b_delay_min = 0
        self.b_delay_max = 1
        # Error injection
        self.inject_rresp: Optional[int] = None  # If set, override rresp
        self.inject_bresp: Optional[int] = None  # If set, override bresp
        # Tracking
        self.read_requests: list[dict] = []
        self.write_requests: list[dict] = []
        self.verbose = False

    def _get_region(self, addr: int) -> AxiMemoryRegion:
        for r in self.regions:
            if r.base <= addr < r.base + r.size:
                return r
        return self.regions[0]

    def reset(self):
        self.dut.arready.value = 0
        self.dut.rid.value = 0
        self.dut.rdata.value = 0
        self.dut.rresp.value = 0
        self.dut.rlast.value = 0
        self.dut.rvalid.value = 0
        self.dut.awready.value = 0
        self.dut.wready.value = 0
        self.dut.bid.value = 0
        self.dut.bresp.value = 0
        self.dut.bvalid.value = 0
        self.read_requests.clear()
        self.write_requests.clear()

    async def run(self):
        """Main BFM loop — forks per-channel responders."""
        cocotb.start_soon(self._ar_responder())
        cocotb.start_soon(self._r_responder_gate())
        cocotb.start_soon(self._aw_responder())
        cocotb.start_soon(self._w_responder())
        cocotb.start_soon(self._b_responder_gate())
        # Run forever
        while True:
            await ClockCycles(self.dut.dmaclk, 1000)

    async def _ar_responder(self):
        """AR channel: accept read address after random delay."""
        while True:
            await RisingEdge(self.dut.dmaclk)
            if self.dut.arvalid.value:
                delay = self.rng.randint(self.ar_delay_min, self.ar_delay_max)
                for _ in range(delay):
                    await RisingEdge(self.dut.dmaclk)
                self.dut.arready.value = 1
                await RisingEdge(self.dut.dmaclk)
                # Capture AR
                req = {
                    "arid": int(self.dut.arid.value),
                    "araddr": int(self.dut.araddr.value),
                    "arlen": int(self.dut.arlen.value),
                    "arsize": int(self.dut.arsize.value),
                }
                self.read_requests.append(req)
                if self.verbose:
                    cocotb.log.info(f"[AXI BFM] AR: addr=0x{req['araddr']:08x} len={req['arlen']}")
                self.dut.arready.value = 0
            else:
                self.dut.arready.value = 0

    async def _r_responder_gate(self):
        """R channel gate: fire R responder per accepted AR request."""
        while True:
            await RisingEdge(self.dut.dmaclk)
            while self.read_requests:
                req = self.read_requests.pop(0)
                await self._r_responder(req)
            await RisingEdge(self.dut.dmaclk)

    async def _r_responder(self, req: dict):
        """R channel: send read data beats per accepted AR."""
        arlen = req["arlen"]
        araddr = req["araddr"]
        arsize = req["arsize"]
        beat_bytes = 1 << arsize  # e.g., 3 → 8 bytes for 64-bit

        for beat_idx in range(arlen + 1):
            addr = araddr + beat_idx * beat_bytes
            region = self._get_region(addr)
            data_bytes = region.read(addr, beat_bytes)
            data_int = int.from_bytes(data_bytes, byteorder="little")

            # Wait until DUT asserts rready, with optional random delay before rvalid
            delay = self.rng.randint(self.r_delay_min, self.r_delay_max)
            for _ in range(delay):
                await RisingEdge(self.dut.dmaclk)

            self.dut.rvalid.value = 1
            self.dut.rid.value = req["arid"]
            self.dut.rdata.value = data_int
            self.dut.rresp.value = self.inject_rresp if self.inject_rresp is not None else 0
            self.dut.rlast.value = 1 if beat_idx == arlen else 0

            if self.verbose:
                cocotb.log.info(
                    f"[AXI BFM] R: addr=0x{addr:08x} data=0x{data_int:016x} "
                    f"last={int(self.dut.rlast.value)} beat={beat_idx}"
                )

            # Wait for handshake
            while not (self.dut.rvalid.value and self.dut.rready.value):
                await RisingEdge(self.dut.dmaclk)
            # Handshake done
            await RisingEdge(self.dut.dmaclk)
            self.dut.rvalid.value = 0
            self.dut.rlast.value = 0

    async def _aw_responder(self):
        """AW channel: accept write address after random delay."""
        while True:
            await RisingEdge(self.dut.dmaclk)
            if self.dut.awvalid.value:
                delay = self.rng.randint(self.aw_delay_min, self.aw_delay_max)
                for _ in range(delay):
                    await RisingEdge(self.dut.dmaclk)
                self.dut.awready.value = 1
                await RisingEdge(self.dut.dmaclk)
                # Capture AW
                req = {
                    "awid": int(self.dut.awid.value),
                    "awaddr": int(self.dut.awaddr.value),
                    "awlen": int(self.dut.awlen.value),
                    "awsize": int(self.dut.awsize.value),
                }
                self.write_requests.append({"aw": req, "w_beats": []})
                if self.verbose:
                    cocotb.log.info(f"[AXI BFM] AW: addr=0x{req['awaddr']:08x} len={req['awlen']}")
                self.dut.awready.value = 0
            else:
                self.dut.awready.value = 0

    async def _w_responder(self):
        """W channel: accept write data. Skips if no outstanding write."""
        while True:
            await RisingEdge(self.dut.dmaclk)
            if self.dut.wvalid.value:
                # Find the pending write that hasn't received all beats
                for wr in self.write_requests:
                    awlen = wr["aw"]["awlen"]
                    if len(wr["w_beats"]) <= awlen:
                        delay = self.rng.randint(self.w_delay_min, self.w_delay_max)
                        for _ in range(delay):
                            await RisingEdge(self.dut.dmaclk)
                        self.dut.wready.value = 1
                        await RisingEdge(self.dut.dmaclk)
                        # Capture W beat
                        wbeat = {
                            "wdata": int(self.dut.wdata.value),
                            "wstrb": int(self.dut.wstrb.value),
                            "wlast": int(self.dut.wlast.value),
                        }
                        wr["w_beats"].append(wbeat)
                        if self.verbose:
                            cocotb.log.info(
                                f"[AXI BFM] W: data=0x{wbeat['wdata']:016x} "
                                f"last={wbeat['wlast']}"
                            )
                        self.dut.wready.value = 0
                        break
            else:
                self.dut.wready.value = 0

    async def _b_responder_gate(self):
        """B channel gate: fire B responder per completed write."""
        while True:
            await RisingEdge(self.dut.dmaclk)
            # Find writes that have received all beats and need B response
            to_remove = []
            for i, wr in enumerate(self.write_requests):
                if wr.get("b_sent"):
                    continue
                awlen = wr["aw"]["awlen"]
                if len(wr["w_beats"]) > awlen:
                    # All beats received, send B
                    await self._b_responder(wr)
                    wr["b_sent"] = True
                    to_remove.append(i)
            # Remove old entries
            for i in reversed(to_remove):
                if i < len(self.write_requests):
                    self.write_requests.pop(i)
            await RisingEdge(self.dut.dmaclk)

    async def _b_responder(self, wr: dict):
        """B channel: send write response."""
        delay = self.rng.randint(self.b_delay_min, self.b_delay_max)
        for _ in range(delay):
            await RisingEdge(self.dut.dmaclk)

        # Write data to memory
        awaddr = wr["aw"]["awaddr"]
        awsize = wr["aw"]["awsize"]
        beat_bytes = 1 << awsize
        region = self._get_region(awaddr)

        for beat_idx, wbeat in enumerate(wr["w_beats"]):
            addr = awaddr + beat_idx * beat_bytes
            data_int = wbeat["wdata"]
            data_bytes = data_int.to_bytes(beat_bytes, byteorder="little")
            # Apply wstrb
            strb = wbeat["wstrb"]
            existing = bytearray(region.read(addr, beat_bytes))
            for b in range(beat_bytes):
                if strb & (1 << b):
                    existing[b] = data_bytes[b] if b < len(data_bytes) else existing[b]
            region.write(addr, existing)

        # Send B response
        self.dut.bvalid.value = 1
        self.dut.bid.value = wr["aw"]["awid"]
        self.dut.bresp.value = self.inject_bresp if self.inject_bresp is not None else 0

        if self.verbose:
            cocotb.log.info(f"[AXI BFM] B: resp={int(self.dut.bresp.value)}")

        # Wait for handshake
        while not (self.dut.bvalid.value and self.dut.bready.value):
            await RisingEdge(self.dut.dmaclk)
        await RisingEdge(self.dut.dmaclk)
        self.dut.bvalid.value = 0


# ─────────────────────── Event Driver ────────────────────────────

class EventDriver:
    """Drives peripheral_events input."""

    def __init__(self, dut):
        self.dut = dut

    def set(self, vector: int):
        self.dut.peripheral_events.value = vector

    async def pulse(self, bit_idx: int, duration_cycles: int = 2):
        """Assert a single event bit for duration_cycles."""
        mask = 1 << bit_idx
        self.dut.peripheral_events.value = mask
        await ClockCycles(self.dut.dmaclk, duration_cycles)
        self.dut.peripheral_events.value = 0
