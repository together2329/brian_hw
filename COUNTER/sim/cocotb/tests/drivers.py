"""DMADriver: cocotb driver for the dma_cocotb_top wrapper."""

from __future__ import annotations

from typing import Sequence

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, RisingEdge

import config
from patterns import PatternMode, build_region


class DMADriver:
    """Cocotb driver for the DMA + RAM testbench wrapper (dma_cocotb_top).

    Provides methods for clock/reset setup, initiating DMA transfers,
    waiting for completion, and initializing / reading back the RAM model
    through VPI hierarchical access to ``u_ram.mem``.
    """

    def __init__(self, dut):
        self.dut = dut
        self._clock = None
        self._max_len_words = (1 << config.LEN_WIDTH) - 1
        self._word_mask = (1 << config.DATA_WIDTH) - 1

    # ----------------------------------------------------------------
    # Validation helpers
    # ----------------------------------------------------------------

    @staticmethod
    def _require_non_negative(value: int, name: str):
        if value < 0:
            raise ValueError(f"{name} must be >= 0, got {value}")

    @staticmethod
    def _require_aligned(byte_addr: int, name: str):
        if byte_addr % config.WORD_BYTES != 0:
            raise ValueError(
                f"{name} must be {config.WORD_BYTES}-byte aligned, got 0x{byte_addr:x}"
            )

    def _word_index(self, byte_addr: int) -> int:
        self._require_non_negative(byte_addr, "byte_addr")
        self._require_aligned(byte_addr, "byte_addr")
        return byte_addr >> config.ADDR_LSB

    def _validate_word_range(self, base_byte_addr: int, num_words: int, label: str):
        self._require_non_negative(num_words, f"{label}.num_words")
        base_idx = self._word_index(base_byte_addr)
        end_idx = base_idx + num_words
        if end_idx > config.DEPTH:
            raise ValueError(
                f"{label} out of bounds: base_idx={base_idx}, num_words={num_words}, "
                f"DEPTH={config.DEPTH}"
            )

    def _validate_transfer(self, src_addr: int, dst_addr: int, length: int):
        self._require_non_negative(length, "length")
        if length > self._max_len_words:
            raise ValueError(
                f"length={length} exceeds LEN_WIDTH limit ({self._max_len_words})"
            )
        self._validate_word_range(src_addr, length, "src")
        self._validate_word_range(dst_addr, length, "dst")

    # ----------------------------------------------------------------
    # Clock and Reset
    # ----------------------------------------------------------------

    def start_clock(self):
        """Start the clock with period from config."""
        self._clock = Clock(self.dut.clk, config.CLK_PERIOD_NS, units="ns")
        cocotb.start_soon(self._clock.start())

    async def assert_reset(self):
        """Assert reset for the configured number of cycles, then release."""
        self.dut.rst_n.value = 0
        self.dut.start.value = 0
        self.dut.src_addr.value = 0
        self.dut.dst_addr.value = 0
        self.dut.length.value = 0
        await ClockCycles(self.dut.clk, config.RESET_CYCLES)
        self.dut.rst_n.value = 1
        await RisingEdge(self.dut.clk)

    async def init(self):
        """Full initialization: start clock and apply reset."""
        self.start_clock()
        await self.assert_reset()

    # ----------------------------------------------------------------
    # Transfer Control
    # ----------------------------------------------------------------

    async def start_transfer(self, src_addr: int, dst_addr: int, length: int):
        """Start a DMA transfer (non-blocking)."""
        self._validate_transfer(src_addr, dst_addr, length)

        self.dut.src_addr.value = src_addr
        self.dut.dst_addr.value = dst_addr
        self.dut.length.value = length
        self.dut.start.value = 1
        await RisingEdge(self.dut.clk)
        self.dut.start.value = 0

    async def wait_for_done(self, timeout_cycles: int = 10000):
        """Wait for the DMA *done* signal to pulse high."""
        self._require_non_negative(timeout_cycles, "timeout_cycles")
        for _ in range(timeout_cycles):
            await RisingEdge(self.dut.clk)
            if self.dut.done.value:
                return
        raise TimeoutError(f"DMA did not complete within {timeout_cycles} cycles")

    async def run_transfer(
        self,
        src_addr: int,
        dst_addr: int,
        length: int,
        timeout_cycles: int = 10000,
    ):
        """Start a transfer and wait for completion (convenience wrapper)."""
        await self.start_transfer(src_addr, dst_addr, length)
        await self.wait_for_done(timeout_cycles)

    # ----------------------------------------------------------------
    # Memory Access via VPI
    # ----------------------------------------------------------------

    def _mem_array(self):
        """Return the cocotb handle for the RAM model's memory array."""
        return self.dut.u_ram.mem

    def init_region(self, base_byte_addr: int, data_words: Sequence[int]):
        """Write a list of word values into the RAM model via VPI."""
        words = list(data_words)
        self._validate_word_range(base_byte_addr, len(words), "init_region")

        mem = self._mem_array()
        base_idx = self._word_index(base_byte_addr)
        for i, word in enumerate(words):
            mem[base_idx + i].value = int(word) & self._word_mask

    def read_region(self, base_byte_addr: int, num_words: int) -> list[int]:
        """Read a range of words from the RAM model via VPI."""
        self._validate_word_range(base_byte_addr, num_words, "read_region")

        mem = self._mem_array()
        base_idx = self._word_index(base_byte_addr)
        return [int(mem[base_idx + i].value) for i in range(num_words)]

    # ----------------------------------------------------------------
    # Convenience: Pattern-based Memory Initialization
    # ----------------------------------------------------------------

    def init_region_with_pattern(
        self,
        mode: PatternMode,
        base_byte_addr: int,
        num_words: int,
    ):
        """Initialize a RAM region with a generated pattern."""
        self._validate_word_range(base_byte_addr, num_words, "init_region_with_pattern")
        base_word = self._word_index(base_byte_addr)
        region = build_region(mode, base_word, num_words)
        self.init_region(base_byte_addr, region)
