"""Group 4: Enable tests (4.1–4.3).

Tests:
    4.1  test_enable_disable       — Counting stops when en=0 (hold)
    4.2  test_enable_toggle        — Toggle en on/off, verify count only advances when en=1
    4.3  test_enable_off_during_load — Load works independently of en value
"""

import cocotb

from counter_env import CounterEnv
from counter_txn import CounterTxn


# ======================================================================
# Test 4.1 — Enable/disable: counting stops when en=0
# ======================================================================
@cocotb.test()
async def test_enable_disable(dut):
    """Count up, disable en, verify count holds. Re-enable, verify resume."""
    env = CounterEnv(dut, width=8)
    await env.setup(reset_cycles=2)

    txns = [
        CounterTxn(en=1, load=0, up_down=0),  # cycle 0: up → 1
        CounterTxn(en=1, load=0, up_down=0),  # cycle 1: up → 2
        CounterTxn(en=1, load=0, up_down=0),  # cycle 2: up → 3
        CounterTxn(en=0, load=0, up_down=0),  # cycle 3: hold → 3 (overflow=0)
        CounterTxn(en=0, load=0, up_down=0),  # cycle 4: hold → 3
        CounterTxn(en=0, load=0, up_down=0),  # cycle 5: hold → 3
        CounterTxn(en=1, load=0, up_down=0),  # cycle 6: up → 4
        CounterTxn(en=1, load=0, up_down=0),  # cycle 7: up → 5
    ]
    all_pass = await env.run_sequence(txns, test_name="4.1_en_disable")

    assert all_pass, "Enable/disable mismatches detected"
    assert env.ref_model.count == 5, (
        f"Expected count=5, got {env.ref_model.count}"
    )
    assert env.scoreboard.report(), "Scoreboard reported failures"
    dut._log.info("test_enable_disable PASSED")


# ======================================================================
# Test 4.2 — Toggle enable on/off
# ======================================================================
@cocotb.test()
async def test_enable_toggle(dut):
    """Alternate en=1/en=0 every cycle; count only advances when en=1."""
    env = CounterEnv(dut, width=8)
    await env.setup(reset_cycles=2)

    # Pattern: up, hold, up, hold, up, hold, up, hold
    # Expected: 1, 1, 2, 2, 3, 3, 4, 4
    txns = [
        CounterTxn(en=1, load=0, up_down=0),  # → 1
        CounterTxn(en=0, load=0, up_down=0),  # hold → 1
        CounterTxn(en=1, load=0, up_down=0),  # → 2
        CounterTxn(en=0, load=0, up_down=0),  # hold → 2
        CounterTxn(en=1, load=0, up_down=0),  # → 3
        CounterTxn(en=0, load=0, up_down=0),  # hold → 3
        CounterTxn(en=1, load=0, up_down=0),  # → 4
        CounterTxn(en=0, load=0, up_down=0),  # hold → 4
    ]
    all_pass = await env.run_sequence(txns, test_name="4.2_en_toggle")

    assert all_pass, "Enable toggle mismatches detected"
    assert env.ref_model.count == 4, (
        f"Expected count=4, got {env.ref_model.count}"
    )
    assert env.scoreboard.report(), "Scoreboard reported failures"
    dut._log.info("test_enable_toggle PASSED")


# ======================================================================
# Test 4.3 — Load works regardless of en value
# ======================================================================
@cocotb.test()
async def test_enable_off_during_load(dut):
    """Load with en=0 should still load the value (load has higher priority)."""
    env = CounterEnv(dut, width=8)
    await env.setup(reset_cycles=2)

    # Load with en=1 (normal)
    load_en1 = CounterTxn(en=1, load=1, up_down=0, data_in=0x55)
    passed = await env.run_one(load_en1, cycle=0, test_name="4.3_load_en1")
    assert passed, "Load with en=1 failed"
    assert env.ref_model.count == 0x55

    # Load with en=0 — load takes priority in RTL (load is checked before en)
    load_en0 = CounterTxn(en=0, load=1, up_down=0, data_in=0xAA)
    passed = await env.run_one(load_en0, cycle=1, test_name="4.3_load_en0")
    assert passed, "Load with en=0 failed"
    assert env.ref_model.count == 0xAA, (
        f"Expected 0xAA, got {env.ref_model.count:#x}"
    )

    assert env.scoreboard.report(), "Scoreboard reported failures"
    dut._log.info("test_enable_off_during_load PASSED")
