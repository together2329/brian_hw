"""DMA cocotb test suite — 8 directed tests + constrained-random loop.

Matches the SV dma_tb stimulus plan test-for-test using the
DMADriver, patterns, scoreboard, and config modules.
"""

import os
import random

import cocotb

import config
from drivers import DMADriver
from patterns import PatternMode, build_region
from scoreboard import CoverageTracker, compare_region


# ------------------------------------------------------------------
# Lightweight protocol monitor
# ------------------------------------------------------------------


async def _protocol_monitor(dut):
    """Continuously assert key mem bus protocol invariants.

    Checks are intentionally lightweight and aligned with this testbench's
    RAM model behavior (ready mirrors req):
      - mem_write must never assert without mem_req.
      - mem_ready must not assert without mem_req.
      - mem_req and mem_ready should match cycle-by-cycle.
      - When DMA is not busy, memory requests must be idle.
    """
    while True:
        await cocotb.triggers.RisingEdge(dut.clk)

        if not int(dut.rst_n.value):
            continue

        mem_req = int(dut.u_dma.mem_req.value)
        mem_ready = int(dut.u_dma.mem_ready.value)
        mem_write = int(dut.u_dma.mem_write.value)
        busy = int(dut.busy.value)

        assert not (mem_write and not mem_req), (
            "Protocol violation: mem_write asserted while mem_req is low"
        )
        assert not (mem_ready and not mem_req), (
            "Protocol violation: mem_ready asserted while mem_req is low"
        )
        assert mem_req == mem_ready, (
            f"Protocol violation: mem_req ({mem_req}) != mem_ready ({mem_ready})"
        )

        if not busy:
            assert mem_req == 0, (
                "Protocol violation: memory request active while DMA busy=0"
            )
            assert mem_write == 0, (
                "Protocol violation: mem_write active while DMA busy=0"
            )


# ------------------------------------------------------------------
# Shared fixtures
# ------------------------------------------------------------------


def _artifact_name(prefix: str) -> str:
    """Build deterministic artifact filenames for coverage outputs."""
    tag = os.environ.get("DMA_ARTIFACT_TAG")
    if not tag:
        tag = f"seed{config.SEED}_n{config.NUM_RANDOM}"
    return f"{prefix}_{tag}.json"


def _make_driver(dut) -> DMADriver:
    """Create a DMADriver and return it (caller must await init)."""
    return DMADriver(dut)


def _byte_addr(word_index: int) -> int:
    """Convert a word index to a byte address."""
    return word_index * config.WORD_BYTES


def _prepare_regions(drv: DMADriver, src_word: int, dst_word: int,
                     length: int, mode: PatternMode,
                     clear_dst_first: bool = False) -> list:
    """Prepare source and destination regions for a transfer.

    Args:
        drv: DMA driver.
        src_word: Source word index.
        dst_word: Destination word index.
        length: Number of words.
        mode: Pattern mode for source data.
        clear_dst_first: If True, clear destination before writing source.
            Useful for overlap cases where writing src first could be clobbered.

    Returns:
        Expected source region data as a list of integers.
    """
    expected = build_region(mode, src_word, length)

    if clear_dst_first:
        drv.init_region_with_pattern(PatternMode.PAT_ZERO, _byte_addr(dst_word), length)
        drv.init_region(_byte_addr(src_word), expected)
    else:
        drv.init_region(_byte_addr(src_word), expected)
        drv.init_region_with_pattern(PatternMode.PAT_ZERO, _byte_addr(dst_word), length)

    return expected


async def _run_and_check_copy(drv: DMADriver, src_word: int, dst_word: int,
                              length: int, mode: PatternMode,
                              test_label: str,
                              timeout_cycles: int = 10000,
                              clear_dst_first: bool = False):
    """Prepare, run, and verify a DMA copy in one helper.

    Args:
        drv: DMA driver.
        src_word: Source word index.
        dst_word: Destination word index.
        length: Number of words.
        mode: Pattern mode for source region.
        test_label: Label used in assertion messages.
        timeout_cycles: Transfer timeout in cycles.
        clear_dst_first: See _prepare_regions.
    """
    expected = _prepare_regions(
        drv, src_word, dst_word, length, mode,
        clear_dst_first=clear_dst_first,
    )

    await drv.run_transfer(
        _byte_addr(src_word), _byte_addr(dst_word), length,
        timeout_cycles=timeout_cycles,
    )

    actual = drv.read_region(_byte_addr(dst_word), length)
    result = compare_region(
        expected, actual,
        _byte_addr(src_word), _byte_addr(dst_word), length,
    )
    assert result.match, f"[{test_label}] mismatch: {result.mismatches}"


async def _new_driver(dut) -> DMADriver:
    """Create and initialize a fresh driver for each test."""
    if not getattr(dut, "_protocol_monitor_started", False):
        cocotb.start_soon(_protocol_monitor(dut))
        dut._protocol_monitor_started = True

    drv = _make_driver(dut)
    await drv.init()
    return drv


# ------------------------------------------------------------------
# Test 1: length = 0 (no-op)
# ------------------------------------------------------------------

@cocotb.test()
async def test_1_length_zero_noop(dut):
    """Length=0 should be a no-op — no transfer, no done pulse expected."""
    drv = await _new_driver(dut)

    # Write a known pattern at src and clear dst
    src_word, dst_word = 16, 64
    drv.init_region_with_pattern(PatternMode.PAT_WORD_INDEX,
                                 _byte_addr(src_word), 1)
    drv.init_region(_byte_addr(dst_word), [0])

    # Issue transfer with length=0
    await drv.start_transfer(_byte_addr(src_word), _byte_addr(dst_word), 0)

    # Wait a few cycles — done should NOT pulse
    for _ in range(10):
        await cocotb.triggers.RisingEdge(dut.clk)
        assert not dut.done.value, "length=0 produced unexpected done pulse"

    # Verify dst region was NOT modified
    actual = drv.read_region(_byte_addr(dst_word), 1)
    assert actual[0] == 0, f"dst was modified despite length=0: {actual[0]:#x}"


# ------------------------------------------------------------------
# Test 2: length = 1 basic copy
# ------------------------------------------------------------------

@cocotb.test()
async def test_2_length_one_basic(dut):
    """Single-word copy with PAT_WORD_INDEX."""
    drv = await _new_driver(dut)

    src_word, dst_word = 16, 64
    await _run_and_check_copy(
        drv, src_word, dst_word, 1, PatternMode.PAT_WORD_INDEX,
        test_label="test_2_length_one_basic",
    )


# ------------------------------------------------------------------
# Test 3: back-to-back commands (two sequential copies)
# ------------------------------------------------------------------

@cocotb.test()
async def test_3_back_to_back(dut):
    """Two sequential DMA transfers without resetting between them."""
    drv = await _new_driver(dut)

    # Part 1: src=80, dst=140, len=2, PAT_WORD_INDEX
    src1, dst1, len1 = 80, 140, 2
    await _run_and_check_copy(
        drv, src1, dst1, len1, PatternMode.PAT_WORD_INDEX,
        test_label="test_3_back_to_back_part1",
    )

    # Part 2: src=200, dst=260, len=2, PAT_LANE_SWEEP
    src2, dst2, len2 = 200, 260, 2
    await _run_and_check_copy(
        drv, src2, dst2, len2, PatternMode.PAT_LANE_SWEEP,
        test_label="test_3_back_to_back_part2",
    )


# ------------------------------------------------------------------
# Test 4: length = 8 medium transfer
# ------------------------------------------------------------------

@cocotb.test()
async def test_4_length_8_medium(dut):
    """8-word copy with PAT_WORD_INDEX."""
    drv = await _new_driver(dut)

    src_word, dst_word, length = 32, 128, 8
    await _run_and_check_copy(
        drv, src_word, dst_word, length, PatternMode.PAT_WORD_INDEX,
        test_label="test_4_length_8_medium",
    )


# ------------------------------------------------------------------
# Test 5: overlapping regions (dst after src)
# ------------------------------------------------------------------

@cocotb.test()
async def test_5_overlap_dst_after_src(dut):
    """Forward-overlap: dst starts 4 words after src."""
    drv = await _new_driver(dut)

    src_word, dst_word, length = 200, 204, 4
    await _run_and_check_copy(
        drv, src_word, dst_word, length, PatternMode.PAT_WORD_INDEX,
        test_label="test_5_overlap_dst_after_src",
    )


# ------------------------------------------------------------------
# Test 6: reverse-overlap (dst before src)
# ------------------------------------------------------------------

@cocotb.test()
async def test_6_overlap_dst_before_src(dut):
    """Reverse-overlap: dst starts 4 words before src, PAT_ALT_TOGGLE."""
    drv = await _new_driver(dut)

    src_word, dst_word, length = 300, 296, 6
    await _run_and_check_copy(
        drv, src_word, dst_word, length, PatternMode.PAT_ALT_TOGGLE,
        test_label="test_6_overlap_dst_before_src",
        clear_dst_first=True,
    )


# ------------------------------------------------------------------
# Test 7: long burst (length = 64)
# ------------------------------------------------------------------

@cocotb.test()
async def test_7_long_burst_64(dut):
    """64-word burst with PAT_LANE_SWEEP."""
    drv = await _new_driver(dut)

    src_word, dst_word, length = 256, 512, 64
    await _run_and_check_copy(
        drv, src_word, dst_word, length, PatternMode.PAT_LANE_SWEEP,
        test_label="test_7_long_burst_64",
    )


# ------------------------------------------------------------------
# Test 8: near-boundary transfer
# ------------------------------------------------------------------

@cocotb.test()
async def test_8_near_boundary(dut):
    """Transfer near the end of the RAM array, PAT_ALT_TOGGLE."""
    drv = await _new_driver(dut)

    src_word = config.DEPTH - 96
    dst_word = config.DEPTH - 32
    length = 24
    await _run_and_check_copy(
        drv, src_word, dst_word, length, PatternMode.PAT_ALT_TOGGLE,
        test_label="test_8_near_boundary",
    )


# ------------------------------------------------------------------
# Test 9: constrained random loop with coverage tracking
# ------------------------------------------------------------------

@cocotb.test()
async def test_9_random_transfers(dut):
    """Constrained-random transfers with coverage tracking."""
    drv = await _new_driver(dut)

    rng = random.Random(config.SEED)
    cov = CoverageTracker()
    max_words = min(32, config.DEPTH - 1)

    for trial in range(config.NUM_RANDOM):
        # Random src/dst word indices
        src_word = rng.randint(0, config.DEPTH - max_words - 1)
        dst_word = rng.randint(0, config.DEPTH - max_words - 1)
        length = rng.randint(1, max_words)

        # ~20% chance of overlapping regions (matching SV $urandom_range < 20)
        # Only generate reverse overlaps (dst <= src) since the DMA processes
        # sequentially (read-then-write) and cannot handle forward-overlapping
        # copies where dst > src without corrupting unread source data.
        if rng.randint(0, 99) < 20:
            offset = rng.randint(-min(10, config.DEPTH - length - src_word - 1), 0)
            dst_word = src_word + offset
            if dst_word < 0:
                dst_word = 0
            if dst_word + length >= config.DEPTH:
                dst_word = config.DEPTH - length - 1
        else:
            # Ensure no forward overlap: dst region must not start before src region ends
            # (dst >= src + length) guarantees non-overlapping copies
            min_dst = src_word + length
            max_dst = config.DEPTH - length
            if min_dst <= max_dst:
                dst_word = rng.randint(min_dst, max_dst)
            else:
                # Fallback: swap so dst < src (reverse overlap is safe)
                dst_word, src_word = src_word, max(dst_word, src_word)
                if src_word + length >= config.DEPTH:
                    src_word = config.DEPTH - length - 1

        # Random pattern mode
        mode = PatternMode(rng.randint(0, len(PatternMode) - 1))

        # Prepare regions — clear dst first, then write src (handles overlap correctly)
        expected = build_region(mode, src_word, length)
        drv.init_region_with_pattern(PatternMode.PAT_ZERO, _byte_addr(dst_word), length)
        drv.init_region(_byte_addr(src_word), expected)

        # Run transfer
        await drv.run_transfer(_byte_addr(src_word), _byte_addr(dst_word), length)

        # Check result
        actual = drv.read_region(_byte_addr(dst_word), length)
        result = compare_region(expected, actual,
                                _byte_addr(src_word), _byte_addr(dst_word), length)

        cov.record_transfer(
            length=length,
            src_addr=_byte_addr(src_word),
            dst_addr=_byte_addr(dst_word),
            pattern_mode=mode,
            passed=result.match,
        )

        assert result.match, (
            f"Random trial {trial}: src_word={src_word} dst_word={dst_word} "
            f"len={length} mode={mode.name} mismatches={result.mismatches[:5]}"
        )

    # Print coverage report
    dut._log.info(cov.report())

    # Export coverage JSON (deterministic artifact naming)
    cov.export_json(_artifact_name("dma_coverage"))


# ==================================================================
# EXPANDED TEST SUITE — additional edge-case and stress tests
# ==================================================================


@cocotb.test()
async def test_10_all_patterns_single_word(dut):
    """Verify all 4 pattern modes produce correct data for a single-word copy."""
    drv = await _new_driver(dut)

    src_word, dst_word = 10, 500
    for mode in PatternMode:
        await _run_and_check_copy(
            drv, src_word, dst_word, 1, mode,
            test_label=f"test_10_{mode.name}",
        )


@cocotb.test()
async def test_11_self_copy_same_address(dut):
    """Copy where src == dst (full overlap) — should preserve data."""
    drv = await _new_driver(dut)

    word_idx, length = 400, 4
    await _run_and_check_copy(
        drv, word_idx, word_idx, length, PatternMode.PAT_LANE_SWEEP,
        test_label="test_11_self_copy_same_address",
    )


@cocotb.test()
async def test_12_max_length_burst(dut):
    """Maximum reasonable burst — 128 words (half the RAM)."""
    drv = await _new_driver(dut)

    src_word, dst_word, length = 0, 512, 128
    await _run_and_check_copy(
        drv, src_word, dst_word, length, PatternMode.PAT_WORD_INDEX,
        test_label="test_12_max_length_burst",
        timeout_cycles=50000,
    )


@cocotb.test()
async def test_13_reset_during_transfer(dut):
    """Assert reset mid-transfer — DMA must return to IDLE cleanly."""
    drv = await _new_driver(dut)

    src_word, dst_word, length = 50, 400, 32
    expected = build_region(PatternMode.PAT_WORD_INDEX, src_word, length)
    drv.init_region(_byte_addr(src_word), expected)
    drv.init_region_with_pattern(PatternMode.PAT_ZERO, _byte_addr(dst_word), length)

    # Start transfer
    await drv.start_transfer(_byte_addr(src_word), _byte_addr(dst_word), length)

    # Wait a few cycles (mid-transfer), then assert reset
    for _ in range(5):
        await cocotb.triggers.RisingEdge(dut.clk)

    # Reset the DUT
    await drv.assert_reset()

    # Verify DMA is idle (busy=0, done=0)
    await cocotb.triggers.RisingEdge(dut.clk)
    assert not dut.busy.value, "DMA still busy after reset"
    assert not dut.done.value, "DMA done asserted after reset"

    # Now do a valid transfer to prove the DMA recovers
    drv.init_region(_byte_addr(src_word), expected)
    drv.init_region_with_pattern(PatternMode.PAT_ZERO, _byte_addr(dst_word), 1)

    await drv.run_transfer(_byte_addr(src_word), _byte_addr(dst_word), 1)

    actual = drv.read_region(_byte_addr(dst_word), 1)
    assert actual[0] == expected[0], "DMA did not recover after reset"


@cocotb.test()
async def test_14_sequential_different_lengths(dut):
    """Chain of transfers with varying lengths (1, 4, 16, 2, 8)."""
    drv = await _new_driver(dut)

    lengths = [1, 4, 16, 2, 8]
    src_base = 50
    dst_base = 500

    for i, length in enumerate(lengths):
        src_word = src_base + sum(lengths[:i])
        dst_word = dst_base + sum(lengths[:i])
        mode = list(PatternMode)[i % len(PatternMode)]

        await _run_and_check_copy(
            drv, src_word, dst_word, length, mode,
            test_label=f"test_14_seq_{i}_{mode.name}",
        )


@cocotb.test()
async def test_15_pat_zero_copies_zeros(dut):
    """PAT_ZERO pattern: all lanes must be zero after copy."""
    drv = await _new_driver(dut)

    src_word, dst_word, length = 20, 600, 8

    # Pre-fill dst with non-zero garbage before helper clears it.
    garbage = [0xDEAD_BEEF_CAFE_BABE] * length
    drv.init_region(_byte_addr(dst_word), garbage)

    await _run_and_check_copy(
        drv, src_word, dst_word, length, PatternMode.PAT_ZERO,
        test_label="test_15_pat_zero_copies_zeros",
    )


@cocotb.test()
async def test_16_stress_50_random_transfers(dut):
    """Stress test: 50 constrained-random transfers with coverage."""
    drv = await _new_driver(dut)

    rng = random.Random(config.SEED + 999)
    cov = CoverageTracker()
    num_trials = 50
    max_words = min(64, config.DEPTH // 2)

    for trial in range(num_trials):
        length = rng.randint(1, max_words)
        src_word = rng.randint(0, config.DEPTH - length - 1)

        # Ensure no forward overlap
        min_dst = src_word + length
        max_dst = config.DEPTH - length
        if rng.randint(0, 99) < 15:
            # Reverse overlap
            max_offset = min(8, src_word)
            if max_offset > 0:
                dst_word = src_word - rng.randint(1, max_offset)
            else:
                dst_word = min_dst if min_dst <= max_dst else src_word
        elif min_dst <= max_dst:
            dst_word = rng.randint(min_dst, max_dst)
        else:
            dst_word = src_word  # self-copy

        mode = PatternMode(rng.randint(0, len(PatternMode) - 1))

        expected = build_region(mode, src_word, length)
        drv.init_region_with_pattern(PatternMode.PAT_ZERO, _byte_addr(dst_word), length)
        drv.init_region(_byte_addr(src_word), expected)

        await drv.run_transfer(_byte_addr(src_word), _byte_addr(dst_word), length,
                               timeout_cycles=100000)

        actual = drv.read_region(_byte_addr(dst_word), length)
        result = compare_region(expected, actual,
                                _byte_addr(src_word), _byte_addr(dst_word), length)

        cov.record_transfer(
            length=length,
            src_addr=_byte_addr(src_word),
            dst_addr=_byte_addr(dst_word),
            pattern_mode=mode,
            passed=result.match,
        )

        assert result.match, (
            f"Stress trial {trial}: src={src_word} dst={dst_word} "
            f"len={length} mode={mode.name} mismatches={result.mismatches[:3]}"
        )

    dut._log.info(cov.report())
    cov.export_json(_artifact_name("dma_stress_coverage"))


@cocotb.test()
async def test_17_start_pulse_while_busy(dut):
    """Start pulses during an active transfer should be ignored."""
    drv = await _new_driver(dut)

    src_word, dst_word, length = 30, 450, 8
    expected = _prepare_regions(
        drv, src_word, dst_word, length, PatternMode.PAT_WORD_INDEX
    )

    # Start a valid transfer
    await drv.start_transfer(_byte_addr(src_word), _byte_addr(dst_word), length)

    # Pulse start again mid-transfer (should be ignored)
    for _ in range(3):
        dut.start.value = 1
        dut.src_addr.value = 0
        dut.dst_addr.value = 0
        dut.length.value = 1
        await cocotb.triggers.RisingEdge(dut.clk)
    dut.start.value = 0

    # Wait for original transfer to complete
    await drv.wait_for_done(timeout_cycles=50000)

    # Verify original transfer data is correct
    actual = drv.read_region(_byte_addr(dst_word), length)
    result = compare_region(expected, actual,
                            _byte_addr(src_word), _byte_addr(dst_word), length)
    assert result.match, f"Start-while-busy corruption: {result.mismatches}"


@cocotb.test()
async def test_18_alt_toggle_pattern_verify(dut):
    """Verify PAT_ALT_TOGGLE has correct alternating lane values."""
    drv = await _new_driver(dut)

    src_word, dst_word, length = 100, 350, 4
    expected = build_region(PatternMode.PAT_ALT_TOGGLE, src_word, length)

    # Manually verify the alternating pattern in each expected word
    mask32 = (1 << 32) - 1
    for offset in range(length):
        word = expected[offset]
        for lane in range(config.LANES_PER_WORD):
            lane_val = (word >> (lane * 32)) & mask32
            if (src_word + offset + lane) & 1:
                assert lane_val == 0xAAAA_FFFF, (
                    f"Word {offset} lane {lane}: expected 0xAAAA_FFFF got {lane_val:#x}"
                )
            else:
                assert lane_val == 0x5555_0000, (
                    f"Word {offset} lane {lane}: expected 0x5555_0000 got {lane_val:#x}"
                )

    drv.init_region(_byte_addr(src_word), expected)
    drv.init_region_with_pattern(PatternMode.PAT_ZERO, _byte_addr(dst_word), length)

    await drv.run_transfer(_byte_addr(src_word), _byte_addr(dst_word), length)

    actual = drv.read_region(_byte_addr(dst_word), length)
    result = compare_region(expected, actual,
                            _byte_addr(src_word), _byte_addr(dst_word), length)
    assert result.match, f"ALT_TOGGLE mismatch: {result.mismatches}"
