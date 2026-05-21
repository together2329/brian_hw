"""PoC: cycle-accurate FL/CL ↔ RTL co-simulation for arbiter_rr.

Drives the DUT and the cl_arbiter_rr.ArbiterRR_CL model in lock-step; samples
every cycle and asserts the registered outputs (gnt_o, gnt_valid_o, gnt_idx_o)
agree at the next rising edge.

Goal: prove that adding a cycle-accurate CL model eliminates the last_winner
mismatch that drove arbiter_rr's previous 24+ grant_index fails — the same
fails the heuristic stimulus and single-shot FunctionalModel.apply path could
not resolve.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import FallingEdge, ReadOnly, RisingEdge

_HERE = Path(__file__).resolve()
_MODEL_DIR = _HERE.parents[2] / "model"
if str(_MODEL_DIR) not in sys.path:
    sys.path.insert(0, str(_MODEL_DIR))

from cl_arbiter_rr import ArbiterRR_CL  # noqa: E402


async def _reset(dut, cycles: int = 3) -> None:
    dut.PRESETn.value = 0
    dut.PSEL.value = 0
    dut.PENABLE.value = 0
    dut.PWRITE.value = 0
    dut.PADDR.value = 0
    dut.PWDATA.value = 0
    dut.req_i.value = 0
    await FallingEdge(dut.PCLK)
    for _ in range(cycles):
        await RisingEdge(dut.PCLK)
    dut.PRESETn.value = 1
    await RisingEdge(dut.PCLK)


@cocotb.test()
async def cl_cosim_round_robin(dut):
    """Drive a deterministic req_i sequence and check CL = RTL every cycle."""
    cocotb.start_soon(Clock(dut.PCLK, 10, units="ns").start())
    await _reset(dut)
    cl = ArbiterRR_CL()

    # Sequence of req_i patterns; each value held for one cycle, then sampled.
    patterns = [
        0b0100, 0b1111, 0b1111, 0b1111, 0b1111,  # one-hot then 4-cycle rotation
        0b0000,                                  # idle
        0b0101, 0b0101, 0b0101, 0b0101,          # alternating 0/2
        0b1010, 0b1010,                          # alternating 1/3
        0b1000, 0b0001, 0b0010, 0b0100,          # walk
    ]

    mismatches: list[str] = []
    matches = 0
    for cycle_idx, req in enumerate(patterns):
        # Drive next req_i on falling edge so it's stable for next rising edge.
        await FallingEdge(dut.PCLK)
        dut.req_i.value = req
        await RisingEdge(dut.PCLK)
        # Both CL and RTL register outputs on this rising edge.
        cl_out = cl.step(req)
        await ReadOnly()
        rtl_gnt_o = int(dut.gnt_o.value)
        rtl_gnt_valid = int(dut.gnt_valid_o.value)
        rtl_gnt_idx = int(dut.gnt_idx_o.value)
        if (
            rtl_gnt_o == cl_out["gnt_o"]
            and rtl_gnt_valid == cl_out["gnt_valid_o"]
            and rtl_gnt_idx == cl_out["gnt_idx_o"]
        ):
            matches += 1
        else:
            mismatches.append(
                f"cycle {cycle_idx} req={req:#06b} "
                f"CL=(o={cl_out['gnt_o']:#06b}, v={cl_out['gnt_valid_o']}, idx={cl_out['gnt_idx_o']}) "
                f"RTL=(o={rtl_gnt_o:#06b}, v={rtl_gnt_valid}, idx={rtl_gnt_idx})"
            )

    print(f"[CL_COSIM] matches={matches}/{len(patterns)} mismatches={len(mismatches)}")
    for line in mismatches[:8]:
        print("  MISMATCH", line)
    assert not mismatches, f"{len(mismatches)} CL/RTL mismatches across {len(patterns)} cycles"
