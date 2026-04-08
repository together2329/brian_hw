"""Group 5: Load tests (5.1–5.5).

Tests:
    5.1  test_load_basic             — Load a value and verify count_out
    5.2  test_load_all_zeros         — Load 0x00
    5.3  test_load_all_ones          — Load 0xFF (MAX_VAL)
    5.4  test_load_overrides_count   — Load during active counting replaces count
    5.5  test_load_then_count        — Load value, then continue counting from it
"""

import cocotb

from counter_env import CounterEnv
from counter_txn import CounterTxn


# ======================================================================
# Test 5.1 — Basic load
# ======================================================================
@cocotb.test()
async def test_load_basic(dut):
    """Load several values and verify count_out reflects each one."""
    env = CounterEnv(dut, width=8)
    await env.setup(reset_cycles=2)

    load_values = [0x42, 0x00, 0xFF, 0x01, 0xFE]
    for i, val in enumerate(load_values):
        txn = CounterTxn(en=1, load=1, up_down=0, data_in=val)
        passed = await env.run_one(txn, cycle=i, test_name="5.1_load_basic")
        assert passed, f"Load {val:#04x} failed at cycle {i}"
        assert env.ref_model.count == val, (
            f"Expected {val:#04x}, got {env.ref_model.count:#04x}"
        )

    assert env.scoreboard.report(), "Scoreboard reported failures"
    dut._log.info("test_load_basic PASSED")


# ======================================================================
# Test 5.2 — Load all zeros
# ======================================================================
@cocotb.test()
async def test_load_all_zeros(dut):
    """Load 0x00 and verify count_out is exactly 0."""
    env = CounterEnv(dut, width=8)
    await env.setup(reset_cycles=2)

    # First load a non-zero value
    preload = CounterTxn(en=1, load=1, up_down=0, data_in=0xAB)
    await env.run_one(preload, cycle=0, test_name="5.2_preload")
    assert env.ref_model.count == 0xAB

    # Load all zeros
    load_zero = CounterTxn(en=1, load=1, up_down=0, data_in=0x00)
    passed = await env.run_one(load_zero, cycle=1, test_name="5.2_load_zero")
    assert passed, "Load 0x00 failed"
    assert env.ref_model.count == 0, f"Expected 0, got {env.ref_model.count}"

    assert env.scoreboard.report(), "Scoreboard reported failures"
    dut._log.info("test_load_all_zeros PASSED")


# ======================================================================
# Test 5.3 — Load all ones (MAX_VAL)
# ======================================================================
@cocotb.test()
async def test_load_all_ones(dut):
    """Load 0xFF and verify count_out is MAX_VAL."""
    env = CounterEnv(dut, width=8)
    await env.setup(reset_cycles=2)

    load_max = CounterTxn(en=1, load=1, up_down=0, data_in=0xFF)
    passed = await env.run_one(load_max, cycle=0, test_name="5.3_load_max")
    assert passed, "Load 0xFF failed"
    assert env.ref_model.count == 0xFF, (
        f"Expected 0xFF, got {env.ref_model.count:#04x}"
    )

    # Verify one more count causes overflow (proves MAX_VAL loaded correctly)
    count_up = CounterTxn(en=1, load=0, up_down=0)
    passed = await env.run_one(count_up, cycle=1, test_name="5.3_overflow_check")
    assert passed, "Count up from 0xFF failed"
    assert env.ref_model.count == 0, (
        f"Expected 0 after overflow, got {env.ref_model.count}"
    )

    assert env.scoreboard.report(), "Scoreboard reported failures"
    dut._log.info("test_load_all_ones PASSED")


# ======================================================================
# Test 5.4 — Load overrides active counting
# ======================================================================
@cocotb.test()
async def test_load_overrides_count(dut):
    """Count up to 5, then load 200 mid-count — load wins."""
    env = CounterEnv(dut, width=8)
    await env.setup(reset_cycles=2)

    txns = [
        CounterTxn(en=1, load=0, up_down=0),            # up → 1
        CounterTxn(en=1, load=0, up_down=0),            # up → 2
        CounterTxn(en=1, load=0, up_down=0),            # up → 3
        CounterTxn(en=1, load=0, up_down=0),            # up → 4
        CounterTxn(en=1, load=0, up_down=0),            # up → 5
        CounterTxn(en=1, load=1, up_down=0, data_in=200),  # load → 200
        CounterTxn(en=1, load=0, up_down=0),            # up → 201
        CounterTxn(en=1, load=0, up_down=0),            # up → 202
    ]
    all_pass = await env.run_sequence(txns, test_name="5.4_load_override")

    assert all_pass, "Load override mismatches detected"
    assert env.ref_model.count == 202, (
        f"Expected 202, got {env.ref_model.count}"
    )
    assert env.scoreboard.report(), "Scoreboard reported failures"
    dut._log.info("test_load_overrides_count PASSED")


# ======================================================================
# Test 5.5 — Load then count from loaded value
# ======================================================================
@cocotb.test()
async def test_load_then_count(dut):
    """Load 250, count up 5, count down 3 — verify seamless transition."""
    env = CounterEnv(dut, width=8)
    await env.setup(reset_cycles=2)

    # Load 250
    load_txn = CounterTxn(en=1, load=1, up_down=0, data_in=250)
    await env.run_one(load_txn, cycle=0, test_name="5.5_load_250")
    assert env.ref_model.count == 250

    # Count up 5: 250→251→252→253→254→255
    up_txns = [CounterTxn(en=1, load=0, up_down=0) for _ in range(5)]
    all_pass = await env.run_sequence(up_txns, test_name="5.5_count_up")
    assert all_pass, "Count up from 250 failed"
    assert env.ref_model.count == 255

    # Count down 3: 255→254→253→252
    down_txns = [CounterTxn(en=1, load=0, up_down=1) for _ in range(3)]
    all_pass = await env.run_sequence(down_txns, test_name="5.5_count_down")
    assert all_pass, "Count down from 255 failed"
    assert env.ref_model.count == 252

    assert env.scoreboard.report(), "Scoreboard reported failures"
    dut._log.info("test_load_then_count PASSED")
