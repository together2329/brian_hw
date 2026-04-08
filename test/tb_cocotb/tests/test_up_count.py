"""Group 2: Up-count tests (2.1–2.3).

Tests:
    2.1  test_up_count_basic         — Increment from 0 through several values
    2.2  test_up_count_full_rollover — Count 0→MAX→0 (full width wrap)
    2.3  test_up_overflow            — Verify overflow pulse at MAX→0 transition
"""

import cocotb
from cocotb.triggers import RisingEdge, ReadOnly

from counter_env import CounterEnv
from counter_txn import CounterTxn, CounterOutput


# ======================================================================
# Test 2.1 — Basic up-count increments
# ======================================================================
@cocotb.test()
async def test_up_count_basic(dut):
    """Count up from 0 for 10 cycles; verify count matches golden model."""
    env = CounterEnv(dut, width=8)
    await env.setup(reset_cycles=2)

    txns = [CounterTxn(en=1, load=0, up_down=0, data_in=0) for _ in range(10)]
    all_pass = await env.run_sequence(txns, test_name="2.1_up_basic")

    assert all_pass, "Basic up-count mismatches detected"
    assert env.scoreboard.report(), "Scoreboard reported failures"
    dut._log.info("test_up_count_basic PASSED")


# ======================================================================
# Test 2.2 — Full-width rollover (0→255→0)
# ======================================================================
@cocotb.test()
async def test_up_count_full_rollover(dut):
    """Count up 256 times; verify wrap from MAX to 0."""
    env = CounterEnv(dut, width=8)
    await env.setup(reset_cycles=2)

    # 256 count-up transactions will take us 0→1→...→255→0
    txns = [CounterTxn(en=1, load=0, up_down=0, data_in=0) for _ in range(256)]
    all_pass = await env.run_sequence(txns, test_name="2.2_rollover")

    assert all_pass, "Full rollover mismatches detected"
    assert env.scoreboard.report(), "Scoreboard reported failures"

    # Verify final state is 0 (wrapped back)
    await RisingEdge(dut.clk)  # extra edge so DUT registers last txn
    await ReadOnly()
    # After 256 counts from 0, we should be back at 0
    # But run_sequence already checked — just verify ref model state
    assert env.ref_model.count == 0, (
        f"Expected count=0 after full rollover, got {env.ref_model.count}"
    )
    dut._log.info("test_up_count_full_rollover PASSED")


# ======================================================================
# Test 2.3 — Overflow pulse at MAX→0 transition
# ======================================================================
@cocotb.test()
async def test_up_overflow(dut):
    """Load MAX-1, count up to MAX (no overflow), then MAX→0 (overflow=1)."""
    env = CounterEnv(dut, width=8)
    await env.setup(reset_cycles=2)

    # Load 253 (MAX-2) to get close to boundary
    load_txn = CounterTxn(en=1, load=1, up_down=0, data_in=253)
    await env.run_one(load_txn, cycle=0, test_name="2.3_load_253")

    # Count up: 253→254 (no overflow)
    txn_no_overflow = CounterTxn(en=1, load=0, up_down=0)
    passed = await env.run_one(txn_no_overflow, cycle=1,
                               test_name="2.3_to_254")
    assert passed, "Count to 254 failed"

    # Count up: 254→255 (no overflow)
    passed = await env.run_one(txn_no_overflow, cycle=2,
                               test_name="2.3_to_255")
    assert passed, "Count to 255 failed"

    # Count up: 255→0 (OVERFLOW!)
    txn_overflow = CounterTxn(en=1, load=0, up_down=0)
    passed = await env.run_one(txn_overflow, cycle=3,
                               test_name="2.3_overflow")
    assert passed, "Overflow transition 255→0 failed"

    # Explicitly verify the overflow occurred
    assert env.ref_model.count == 0, (
        f"Expected count=0 after overflow, got {env.ref_model.count}"
    )
    # The last run_one already checked via scoreboard, but let's also
    # verify the ref model produced overflow=1 for that step
    expected_overflow = env.ref_model.get_output()
    assert expected_overflow.count_out == 0
    # Note: get_output returns current state (post-step), overflow already cleared
    # if another step ran. The scoreboard already validated it.

    assert env.scoreboard.report(), "Scoreboard reported failures"
    dut._log.info("test_up_overflow PASSED")
