"""Group 3: Down-count tests (3.1–3.3).

Tests:
    3.1  test_down_count_basic     — Decrement from loaded value
    3.2  test_down_count_rollover  — Count 0→MAX (underflow wrap)
    3.3  test_down_overflow        — Verify underflow pulse at 0→MAX transition
"""

import cocotb
from cocotb.triggers import RisingEdge, ReadOnly

from counter_env import CounterEnv
from counter_txn import CounterTxn, CounterOutput


# ======================================================================
# Test 3.1 — Basic down-count decrements
# ======================================================================
@cocotb.test()
async def test_down_count_basic(dut):
    """Load 10, count down 10 times; verify count matches golden model."""
    env = CounterEnv(dut, width=8)
    await env.setup(reset_cycles=2)

    # Load starting value
    load_txn = CounterTxn(en=1, load=1, up_down=1, data_in=10)
    await env.run_one(load_txn, cycle=0, test_name="3.1_load_10")

    # Count down for 10 cycles: 10→9→8→...→0
    txns = [CounterTxn(en=1, load=0, up_down=1, data_in=0) for _ in range(10)]
    all_pass = await env.run_sequence(txns, test_name="3.1_down_basic")

    assert all_pass, "Basic down-count mismatches detected"
    assert env.scoreboard.report(), "Scoreboard reported failures"

    # Verify final state is 0
    assert env.ref_model.count == 0, (
        f"Expected count=0 after counting down from 10, got {env.ref_model.count}"
    )
    dut._log.info("test_down_count_basic PASSED")


# ======================================================================
# Test 3.2 — Down-count rollover (0→255)
# ======================================================================
@cocotb.test()
async def test_down_count_rollover(dut):
    """Load 1, count down twice: 1→0 (no overflow), then 0→255 (overflow)."""
    env = CounterEnv(dut, width=8)
    await env.setup(reset_cycles=2)

    # Load 1
    load_txn = CounterTxn(en=1, load=1, up_down=1, data_in=1)
    await env.run_one(load_txn, cycle=0, test_name="3.2_load_1")

    # Count down: 1→0 (no overflow)
    txn_down = CounterTxn(en=1, load=0, up_down=1)
    passed = await env.run_one(txn_down, cycle=1, test_name="3.2_to_0")
    assert passed, "Count down to 0 failed"
    assert env.ref_model.count == 0, f"Expected 0, got {env.ref_model.count}"

    # Count down: 0→255 (UNDERFLOW — wraps to MAX_VAL)
    passed = await env.run_one(txn_down, cycle=2, test_name="3.2_underflow")
    assert passed, "Underflow transition 0→255 failed"
    assert env.ref_model.count == 255, (
        f"Expected 255 after underflow, got {env.ref_model.count}"
    )

    assert env.scoreboard.report(), "Scoreboard reported failures"
    dut._log.info("test_down_count_rollover PASSED")


# ======================================================================
# Test 3.3 — Down-count overflow pulse
# ======================================================================
@cocotb.test()
async def test_down_overflow(dut):
    """Load 3, count down 4 times; verify overflow=1 pulse at 0→255."""
    env = CounterEnv(dut, width=8)
    await env.setup(reset_cycles=2)

    # Load 3
    load_txn = CounterTxn(en=1, load=1, up_down=1, data_in=3)
    await env.run_one(load_txn, cycle=0, test_name="3.3_load_3")

    # Count down: 3→2 (no overflow)
    txn_down = CounterTxn(en=1, load=0, up_down=1)
    passed = await env.run_one(txn_down, cycle=1, test_name="3.3_to_2")
    assert passed, "Count down 3→2 failed"

    # Count down: 2→1 (no overflow)
    passed = await env.run_one(txn_down, cycle=2, test_name="3.3_to_1")
    assert passed, "Count down 2→1 failed"

    # Count down: 1→0 (no overflow)
    passed = await env.run_one(txn_down, cycle=3, test_name="3.3_to_0")
    assert passed, "Count down 1→0 failed"
    assert env.ref_model.count == 0

    # Count down: 0→255 (UNDERFLOW! overflow=1 for one cycle)
    passed = await env.run_one(txn_down, cycle=4, test_name="3.3_underflow")
    assert passed, "Underflow 0→255 failed"

    # Verify ref model state
    out = env.ref_model.get_output()
    assert out.count_out == 255, f"Expected 255, got {out.count_out}"
    # overflow=0 because get_output returns current stable state;
    # the scoreboard already verified overflow=1 at the transition

    assert env.scoreboard.report(), "Scoreboard reported failures"
    dut._log.info("test_down_overflow PASSED")
