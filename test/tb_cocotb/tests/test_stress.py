"""Group 7: Stress tests (7.1–7.3b).

Tests:
    7.1   test_rapid_load_count     — Rapidly interleave loads and counting
    7.2   test_random_stimulus_500  — 500 random transactions with full checking
    7.3a  test_full_cycle_up        — Full up-cycle: 0 → 255 → 0 (overflow wrap)
    7.3b  test_full_cycle_down      — Full down-cycle: 255 → 0 → 255 (underflow wrap)
"""

import cocotb

from counter_env import CounterEnv
from counter_txn import CounterTxn


# ======================================================================
# Test 7.1 — Rapid load / count interleaving
# ======================================================================
@cocotb.test()
async def test_rapid_load_count(dut):
    """Stress-test: alternate load and count in rapid succession."""
    env = CounterEnv(dut, width=8)
    await env.setup(reset_cycles=2)

    txns = [
        CounterTxn(en=1, load=1, up_down=0, data_in=0x80),   # load → 128
        CounterTxn(en=1, load=0, up_down=0),                  # up   → 129
        CounterTxn(en=1, load=1, up_down=0, data_in=0x10),   # load → 16
        CounterTxn(en=1, load=0, up_down=1),                  # down → 15
        CounterTxn(en=1, load=1, up_down=0, data_in=0xFC),   # load → 252
        CounterTxn(en=1, load=0, up_down=0),                  # up   → 253
        CounterTxn(en=1, load=0, up_down=0),                  # up   → 254
        CounterTxn(en=1, load=1, up_down=0, data_in=0x02),   # load → 2
        CounterTxn(en=1, load=0, up_down=1),                  # down → 1
        CounterTxn(en=1, load=0, up_down=1),                  # down → 0
        CounterTxn(en=1, load=1, up_down=0, data_in=0xFF),   # load → 255
        CounterTxn(en=1, load=0, up_down=0),                  # up   → 0 (overflow)
        CounterTxn(en=1, load=1, up_down=0, data_in=0x00),   # load → 0
        CounterTxn(en=1, load=0, up_down=1),                  # down → 255 (underflow)
        CounterTxn(en=1, load=0, up_down=0),                  # up   → 0 (overflow)
        CounterTxn(en=1, load=1, up_down=0, data_in=0x55),   # load → 85
        CounterTxn(en=1, load=0, up_down=0),                  # up   → 86
        CounterTxn(en=1, load=0, up_down=0),                  # up   → 87
        CounterTxn(en=1, load=1, up_down=0, data_in=0xAA),   # load → 170
        CounterTxn(en=1, load=0, up_down=1),                  # down → 169
    ]

    all_pass = await env.run_sequence(txns, test_name="7.1_rapid_load_count")
    assert all_pass, "Rapid load/count interleaving produced mismatches"

    assert env.ref_model.count == 169, (
        f"Expected 169, got {env.ref_model.count}"
    )
    assert env.scoreboard.report(), "Scoreboard reported failures"
    dut._log.info("test_rapid_load_count PASSED")


# ======================================================================
# Test 7.2 — Random stimulus (500 transactions)
# ======================================================================
@cocotb.test()
async def test_random_stimulus_500(dut):
    """Stress-test: 500 fully random transactions with scoreboard checking."""
    env = CounterEnv(dut, width=8)
    await env.setup(reset_cycles=2)

    all_pass = await env.run_random(n=500, test_name="7.2_random_500")
    assert all_pass, "Random stimulus (500 cycles) produced mismatches"

    assert env.scoreboard.report(), "Scoreboard reported failures"
    dut._log.info("test_random_stimulus_500 PASSED")


# ======================================================================
# Test 7.3a — Full up-cycle: 0 → 255 → 0
# ======================================================================
@cocotb.test()
async def test_full_cycle_up(dut):
    """Count up 256 times from 0: 0→1→...→255→0(overflow)→...→9."""
    env = CounterEnv(dut, width=8)
    await env.setup(reset_cycles=2)

    # 256 up-counts = one full wrap + 10 more
    # After 256 counts: 0→1→...→255→0(overflow)→1→...→9→10
    # Actually: 256 counts from 0 lands back at 0, then 10 more → 10
    # Let's do exactly 260 counts: 0+260 mod 256 = 4
    # But we also want to verify the overflow at cycle 255 (count=255→0)
    # So: 260 count-up transactions from post-reset state (count=0)

    # 256 ups: wraps to 0 with overflow at step 255
    # 4 more ups: 0→1→2→3→4
    total = 260
    txns = [CounterTxn(en=1, load=0, up_down=0) for _ in range(total)]

    all_pass = await env.run_sequence(txns, test_name="7.3a_full_up")
    assert all_pass, "Full up-cycle produced mismatches"

    expected_count = total % 256  # 260 % 256 = 4
    assert env.ref_model.count == expected_count, (
        f"Expected {expected_count} after {total} up-counts, "
        f"got {env.ref_model.count}"
    )
    assert env.scoreboard.report(), "Scoreboard reported failures"
    dut._log.info("test_full_cycle_up PASSED")


# ======================================================================
# Test 7.3b — Full down-cycle: 255 → 0 → 255
# ======================================================================
@cocotb.test()
async def test_full_cycle_down(dut):
    """Load 255, count down 260 times: wraps through 0 back to 251."""
    env = CounterEnv(dut, width=8)
    await env.setup(reset_cycles=2)

    txns = [
        # Load 255 as starting point
        CounterTxn(en=1, load=1, up_down=0, data_in=0xFF),  # load → 255
    ]
    # 260 down-counts from 255
    txns += [CounterTxn(en=1, load=0, up_down=1) for _ in range(260)]

    all_pass = await env.run_sequence(txns, test_name="7.3b_full_down")
    assert all_pass, "Full down-cycle produced mismatches"

    # 255 - 260 mod 256 = (255 - 260) mod 256 = -5 mod 256 = 251
    expected_count = (255 - 260) % 256  # = 251
    assert env.ref_model.count == expected_count, (
        f"Expected {expected_count} after 260 down-counts from 255, "
        f"got {env.ref_model.count}"
    )
    assert env.scoreboard.report(), "Scoreboard reported failures"
    dut._log.info("test_full_cycle_down PASSED")
