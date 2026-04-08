"""Group 1: Reset tests (1.1–1.3).

Tests:
    1.1  test_sync_reset                — Reset clears count and overflow
    1.2  test_reset_while_counting      — Reset mid-count forces count to 0
    1.3  test_reset_priority_over_load  — Reset overrides simultaneous load
"""

import cocotb
from cocotb.triggers import RisingEdge, ReadOnly, NextTimeStep
from cocotb.clock import Clock

from counter_env import CounterEnv
from counter_txn import CounterTxn, CounterOutput


async def _reset_check_loop(dut, env, stimulus_txns, rst_cycle_idx,
                            test_name: str) -> None:
    """Drive stimulus, insert reset at rst_cycle_idx, check every cycle.

    Handles ref model manually because reset overrides rst_n.
    """
    env.ref_model.reset()  # start from known state

    for i, txn in enumerate(stimulus_txns):
        if i == rst_cycle_idx:
            # ---- Apply reset this cycle ----
            dut.rst_n.value = 0
            # Drive inputs anyway (they should be ignored)
            dut.en.value      = txn.en
            dut.load.value    = txn.load
            dut.up_down.value = txn.up_down
            dut.data_in.value = txn.data_in

            await RisingEdge(dut.clk)  # DUT registers reset
            dut.rst_n.value = 1

            await ReadOnly()
            actual = CounterOutput(
                count_out=int(dut.count_out.value),
                overflow=int(dut.overflow.value),
            )
            expected = env.ref_model.step(txn, rst_n=0)  # ref model reset
            env.scoreboard.compare(expected, actual, cycle=i,
                                   test_name=test_name)
        else:
            # ---- Normal cycle ----
            dut.en.value      = txn.en
            dut.load.value    = txn.load
            dut.up_down.value = txn.up_down
            dut.data_in.value = txn.data_in

            await RisingEdge(dut.clk)  # DUT registers inputs

            await ReadOnly()
            actual = CounterOutput(
                count_out=int(dut.count_out.value),
                overflow=int(dut.overflow.value),
            )
            expected = env.ref_model.step(txn, rst_n=1)
            env.scoreboard.compare(expected, actual, cycle=i,
                                   test_name=test_name)


# ======================================================================
# Test 1.1 — Synchronous reset clears count and overflow
# ======================================================================
@cocotb.test()
async def test_sync_reset(dut):
    """Verify rst_n=0 clears count_out to 0 and overflow to 0."""
    env = CounterEnv(dut, width=8)
    await env.setup(reset_cycles=2)

    # Load a known non-zero value first
    load_txn = CounterTxn(en=1, load=1, up_down=0, data_in=0xAB)
    await env.run_one(load_txn, cycle=0, test_name="1.1_load")

    # Verify the load took effect
    expected_after_load = CounterOutput(count_out=0xAB, overflow=0)
    actual_after_load = await env.monitor.sample_now()
    assert actual_after_load == expected_after_load, (
        f"Load failed: expected {expected_after_load}, got {actual_after_load}"
    )

    # Now apply reset
    dut.rst_n.value = 0
    await RisingEdge(dut.clk)   # DUT sees reset
    dut.rst_n.value = 1

    # Check outputs after reset
    await ReadOnly()
    actual = CounterOutput(
        count_out=int(dut.count_out.value),
        overflow=int(dut.overflow.value),
    )
    expected = CounterOutput(count_out=0, overflow=0)
    assert actual == expected, (
        f"Reset failed: expected {expected}, got {actual}"
    )

    # Sync ref model and verify scoreboard
    env.ref_model.reset()
    env.scoreboard.compare(expected, actual, cycle=1, test_name="1.1_reset")

    dut._log.info("test_sync_reset PASSED")
    assert env.scoreboard.report(), "Scoreboard reported failures"


# ======================================================================
# Test 1.2 — Reset while counting
# ======================================================================
@cocotb.test()
async def test_reset_while_counting(dut):
    """Count up several cycles, assert reset mid-stream, verify count=0."""
    env = CounterEnv(dut, width=8)
    await env.setup(reset_cycles=2)

    # Sequence: count up for 5 cycles, reset on cycle 3, then count up 2 more
    txns = [
        CounterTxn(en=1, load=0, up_down=0, data_in=0),  # cycle 0: up
        CounterTxn(en=1, load=0, up_down=0, data_in=0),  # cycle 1: up
        CounterTxn(en=1, load=0, up_down=0, data_in=0),  # cycle 2: up (reset here)
        CounterTxn(en=1, load=0, up_down=0, data_in=0),  # cycle 3: up
        CounterTxn(en=1, load=0, up_down=0, data_in=0),  # cycle 4: up
    ]

    await _reset_check_loop(dut, env, txns, rst_cycle_idx=2,
                            test_name="1.2")

    dut._log.info("test_reset_while_counting PASSED")
    assert env.scoreboard.report(), "Scoreboard reported failures"


# ======================================================================
# Test 1.3 — Reset has priority over simultaneous load
# ======================================================================
@cocotb.test()
async def test_reset_priority_over_load(dut):
    """Assert reset and load together; verify reset wins (count=0)."""
    env = CounterEnv(dut, width=8)
    await env.setup(reset_cycles=2)

    # First load a non-zero value to ensure we can observe the override
    load_txn = CounterTxn(en=1, load=1, up_down=0, data_in=0xCC)
    await env.run_one(load_txn, cycle=0, test_name="1.3_preload")

    # Now drive load=1 with data=0xDD AND rst_n=0 simultaneously
    # Reset should take priority — count should go to 0, not 0xDD
    dut.rst_n.value     = 0
    dut.en.value         = 1
    dut.load.value       = 1
    dut.up_down.value    = 0
    dut.data_in.value    = 0xDD

    await RisingEdge(dut.clk)  # DUT registers
    dut.rst_n.value = 1

    await ReadOnly()
    actual = CounterOutput(
        count_out=int(dut.count_out.value),
        overflow=int(dut.overflow.value),
    )
    expected = CounterOutput(count_out=0, overflow=0)
    assert actual == expected, (
        f"Reset-over-load failed: expected {expected}, got {actual}"
    )

    # Update ref model to match
    env.ref_model.step(CounterTxn(en=1, load=1, data_in=0xDD), rst_n=0)
    env.scoreboard.compare(expected, actual, cycle=1,
                           test_name="1.3_reset_over_load")

    dut._log.info("test_reset_priority_over_load PASSED")
    assert env.scoreboard.report(), "Scoreboard reported failures"
