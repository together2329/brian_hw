"""Group 6: Direction switch tests (6.1–6.3).

Tests:
    6.1  test_switch_up_to_down   — Count up, switch to down, verify seamless
    6.2  test_switch_down_to_up   — Count down, switch to up, verify seamless
    6.3  test_switch_mid_cycle    — Switch direction at boundary values (near 0 & MAX_VAL)
"""

import cocotb

from counter_env import CounterEnv
from counter_txn import CounterTxn


# ======================================================================
# Test 6.1 — Switch from up to down
# ======================================================================
@cocotb.test()
async def test_switch_up_to_down(dut):
    """Count up 6 cycles (0→6), then switch to counting down (6→0)."""
    env = CounterEnv(dut, width=8)
    await env.setup(reset_cycles=2)

    txns = [
        # Count up: 0 → 1 → 2 → 3 → 4 → 5 → 6
        CounterTxn(en=1, load=0, up_down=0),  # up → 1
        CounterTxn(en=1, load=0, up_down=0),  # up → 2
        CounterTxn(en=1, load=0, up_down=0),  # up → 3
        CounterTxn(en=1, load=0, up_down=0),  # up → 4
        CounterTxn(en=1, load=0, up_down=0),  # up → 5
        CounterTxn(en=1, load=0, up_down=0),  # up → 6
        # Switch: count down 6 → 5 → 4 → 3 → 2 → 1 → 0
        CounterTxn(en=1, load=0, up_down=1),  # down → 5
        CounterTxn(en=1, load=0, up_down=1),  # down → 4
        CounterTxn(en=1, load=0, up_down=1),  # down → 3
        CounterTxn(en=1, load=0, up_down=1),  # down → 2
        CounterTxn(en=1, load=0, up_down=1),  # down → 1
        CounterTxn(en=1, load=0, up_down=1),  # down → 0
    ]

    all_pass = await env.run_sequence(txns, test_name="6.1_up_to_down")
    assert all_pass, "Direction switch up→down produced mismatches"

    # Verify final state
    assert env.ref_model.count == 0, (
        f"Expected 0 after down-count, got {env.ref_model.count}"
    )
    assert env.ref_model.overflow == 0, "Unexpected overflow at end"

    assert env.scoreboard.report(), "Scoreboard reported failures"
    dut._log.info("test_switch_up_to_down PASSED")


# ======================================================================
# Test 6.2 — Switch from down to up
# ======================================================================
@cocotb.test()
async def test_switch_down_to_up(dut):
    """Load 100, count down 4 (100→96), then switch to up (96→102)."""
    env = CounterEnv(dut, width=8)
    await env.setup(reset_cycles=2)

    txns = [
        # Load 100
        CounterTxn(en=1, load=1, up_down=0, data_in=100),  # load → 100
        # Count down: 100 → 99 → 98 → 97 → 96
        CounterTxn(en=1, load=0, up_down=1),  # down → 99
        CounterTxn(en=1, load=0, up_down=1),  # down → 98
        CounterTxn(en=1, load=0, up_down=1),  # down → 97
        CounterTxn(en=1, load=0, up_down=1),  # down → 96
        # Switch: count up 96 → 97 → 98 → 99 → 100 → 101 → 102
        CounterTxn(en=1, load=0, up_down=0),  # up → 97
        CounterTxn(en=1, load=0, up_down=0),  # up → 98
        CounterTxn(en=1, load=0, up_down=0),  # up → 99
        CounterTxn(en=1, load=0, up_down=0),  # up → 100
        CounterTxn(en=1, load=0, up_down=0),  # up → 101
        CounterTxn(en=1, load=0, up_down=0),  # up → 102
    ]

    all_pass = await env.run_sequence(txns, test_name="6.2_down_to_up")
    assert all_pass, "Direction switch down→up produced mismatches"

    assert env.ref_model.count == 102, (
        f"Expected 102 after up-count, got {env.ref_model.count}"
    )
    assert env.ref_model.overflow == 0, "Unexpected overflow"

    assert env.scoreboard.report(), "Scoreboard reported failures"
    dut._log.info("test_switch_down_to_up PASSED")


# ======================================================================
# Test 6.3 — Switch direction at boundary values
# ======================================================================
@cocotb.test()
async def test_switch_mid_cycle(dut):
    """Switch direction near boundaries: up to 254→down, down to 1→up."""
    env = CounterEnv(dut, width=8)
    await env.setup(reset_cycles=2)

    txns = [
        # Load 250, count up towards MAX_VAL
        CounterTxn(en=1, load=1, up_down=0, data_in=250),  # load → 250
        CounterTxn(en=1, load=0, up_down=0),  # up → 251
        CounterTxn(en=1, load=0, up_down=0),  # up → 252
        CounterTxn(en=1, load=0, up_down=0),  # up → 253
        CounterTxn(en=1, load=0, up_down=0),  # up → 254
        # Switch to down just before overflow — no spurious overflow
        CounterTxn(en=1, load=0, up_down=1),  # down → 253
        CounterTxn(en=1, load=0, up_down=1),  # down → 252
        CounterTxn(en=1, load=0, up_down=1),  # down → 251

        # Load 3, count down towards 0
        CounterTxn(en=1, load=1, up_down=0, data_in=3),   # load → 3
        CounterTxn(en=1, load=0, up_down=1),  # down → 2
        CounterTxn(en=1, load=0, up_down=1),  # down → 1
        # Switch to up just before underflow — no spurious underflow
        CounterTxn(en=1, load=0, up_down=0),  # up → 2
        CounterTxn(en=1, load=0, up_down=0),  # up → 3
        CounterTxn(en=1, load=0, up_down=0),  # up → 4
    ]

    all_pass = await env.run_sequence(txns, test_name="6.3_boundary_switch")
    assert all_pass, "Boundary direction switch produced mismatches"

    assert env.ref_model.count == 4, (
        f"Expected 4 at end, got {env.ref_model.count}"
    )
    assert env.ref_model.overflow == 0, (
        "Spurious overflow/underflow detected during boundary switch"
    )

    assert env.scoreboard.report(), "Scoreboard reported failures"
    dut._log.info("test_switch_mid_cycle PASSED")
