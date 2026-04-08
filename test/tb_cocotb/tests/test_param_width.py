"""Group 8: Parameterized width tests (8.1–8.3).

Tests:
    8.1  test_width_4   — Boundary wrap-around for small width (WIDTH=4)
    8.2  test_width_8   — Standard load/count/overflow for WIDTH=8
    8.3  test_width_16  — Large-range counting for WIDTH=16

Each test auto-detects the DUT's actual width from the data_in port and
adapts its stimulus accordingly.  Run with the DUT compiled at the
target WIDTH (e.g. via plusarg or recompilation).
"""

import cocotb

from counter_env import CounterEnv
from counter_txn import CounterTxn


def _detect_width(dut) -> int:
    """Return the counter WIDTH from the DUT's data_in port."""
    return len(dut.data_in)


# ======================================================================
# Test 8.1 — WIDTH=4: rapid overflow / underflow at small boundary
# ======================================================================
@cocotb.test()
async def test_width_4(dut):
    """Exercise wrap-around at MAX_VAL=15 (WIDTH=4) boundary."""
    width = _detect_width(dut)
    max_val = (1 << width) - 1

    env = CounterEnv(dut, width=width)
    await env.setup(reset_cycles=2)

    # Load MAX_VAL, count up → overflow wrap to 0
    txns = [
        CounterTxn(en=1, load=1, up_down=0, data_in=max_val),  # load → MAX
        CounterTxn(en=1, load=0, up_down=0),                   # up → 0 (overflow)
        CounterTxn(en=1, load=0, up_down=1),                   # down → MAX (underflow)
        CounterTxn(en=1, load=0, up_down=0),                   # up → 0 (overflow)
    ]
    all_pass = await env.run_sequence(txns, test_name="8.1_wrap_boundary")
    assert all_pass, "WIDTH=4 wrap boundary mismatches"

    # Full up-cycle: load 0, count up (max_val+1) times → back to 0
    full_cycle = max_val + 1  # 16 for WIDTH=4
    txns2 = [
        CounterTxn(en=1, load=1, up_down=0, data_in=0),  # load → 0
    ] + [CounterTxn(en=1, load=0, up_down=0) for _ in range(full_cycle)]

    all_pass2 = await env.run_sequence(txns2, test_name="8.1_full_cycle_up")
    assert all_pass2, "WIDTH=4 full cycle up mismatches"
    assert env.ref_model.count == 0, (
        f"Expected 0 after full cycle, got {env.ref_model.count}"
    )

    assert env.scoreboard.report(), "Scoreboard reported failures"
    dut._log.info(f"test_width_4 PASSED (detected WIDTH={width})")


# ======================================================================
# Test 8.2 — WIDTH=8: standard load/count/overflow operations
# ======================================================================
@cocotb.test()
async def test_width_8(dut):
    """Load, count up, overflow, count down, underflow for WIDTH=8."""
    width = _detect_width(dut)
    max_val = (1 << width) - 1

    env = CounterEnv(dut, width=width)
    await env.setup(reset_cycles=2)

    txns = [
        # Load a mid-range value and count up
        CounterTxn(en=1, load=1, up_down=0, data_in=max_val - 3),  # load → MAX-3
        CounterTxn(en=1, load=0, up_down=0),  # up → MAX-2
        CounterTxn(en=1, load=0, up_down=0),  # up → MAX-1
        CounterTxn(en=1, load=0, up_down=0),  # up → MAX
        CounterTxn(en=1, load=0, up_down=0),  # up → 0 (overflow)
        # Count down through underflow
        CounterTxn(en=1, load=0, up_down=1),  # down → MAX (underflow)
        CounterTxn(en=1, load=0, up_down=1),  # down → MAX-1
        # Load 0 and count down → underflow
        CounterTxn(en=1, load=1, up_down=0, data_in=0),  # load → 0
        CounterTxn(en=1, load=0, up_down=1),  # down → MAX (underflow)
        CounterTxn(en=1, load=0, up_down=0),  # up → 0 (overflow)
    ]
    all_pass = await env.run_sequence(txns, test_name="8.2_width8_ops")
    assert all_pass, "WIDTH=8 standard ops mismatches"

    assert env.ref_model.count == 0, (
        f"Expected 0, got {env.ref_model.count}"
    )
    assert env.scoreboard.report(), "Scoreboard reported failures"
    dut._log.info(f"test_width_8 PASSED (detected WIDTH={width})")


# ======================================================================
# Test 8.3 — WIDTH=16: large-range counting
# ======================================================================
@cocotb.test()
async def test_width_16(dut):
    """Load large values and count across a wide range for WIDTH=16."""
    width = _detect_width(dut)
    max_val = (1 << width) - 1

    env = CounterEnv(dut, width=width)
    await env.setup(reset_cycles=2)

    # Load a high value near the top of the range
    high_val = max_val - 10
    txns = [
        CounterTxn(en=1, load=1, up_down=0, data_in=high_val),  # load → MAX-10
    ]
    # Count up 10 to reach MAX
    txns += [CounterTxn(en=1, load=0, up_down=0) for _ in range(10)]
    # One more → overflow to 0
    txns.append(CounterTxn(en=1, load=0, up_down=0))  # overflow → 0
    # Count up 5 more
    txns += [CounterTxn(en=1, load=0, up_down=0) for _ in range(5)]

    all_pass = await env.run_sequence(txns, test_name="8.3_width16_large_range")
    assert all_pass, "WIDTH=16 large range mismatches"

    expected = 5  # 0 + 5 after overflow
    assert env.ref_model.count == expected, (
        f"Expected {expected}, got {env.ref_model.count}"
    )

    # Now count down 5 to get back to 0, then underflow to MAX
    txns2 = [CounterTxn(en=1, load=0, up_down=1) for _ in range(6)]
    all_pass2 = await env.run_sequence(txns2, test_name="8.3_width16_down")
    assert all_pass2, "WIDTH=16 count down mismatches"

    expected2 = max_val  # 0 - 1 = MAX (underflow)
    assert env.ref_model.count == expected2, (
        f"Expected {expected2}, got {env.ref_model.count}"
    )

    assert env.scoreboard.report(), "Scoreboard reported failures"
    dut._log.info(f"test_width_16 PASSED (detected WIDTH={width})")
