"""cocotb testbench for mctp_assembler_v3_axi_wr_ingress.

Drives real AXI4 write bursts into the DUT and scoreboards the DUT's
BRESP / tlp_accept / tlp_byte_count against the golden FunctionalModel
transaction FM_INGEST_TLP (the FL oracle). This is the L1 equivalence
check for the AXI write-ingress slice of the MCTP assembler.
"""
import sys
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, ClockCycles

# Make the golden FunctionalModel importable as the scoreboard oracle.
HERE = Path(__file__).resolve().parent
MODEL_DIR = HERE.parent.parent / "model"
sys.path.insert(0, str(MODEL_DIR))
from functional_model import FunctionalModel  # noqa: E402


async def reset_dut(dut):
    dut.axi_aresetn.value = 0
    dut.s_axi_awaddr.value = 0
    dut.s_axi_awlen.value = 0
    dut.s_axi_awsize.value = 0
    dut.s_axi_awburst.value = 0
    dut.s_axi_awvalid.value = 0
    dut.s_axi_wdata.value = 0
    dut.s_axi_wstrb.value = 0
    dut.s_axi_wlast.value = 0
    dut.s_axi_wvalid.value = 0
    dut.s_axi_bready.value = 0
    await ClockCycles(dut.axi_aclk, 5)
    dut.axi_aresetn.value = 1
    await ClockCycles(dut.axi_aclk, 2)


async def axi_write_burst(dut, n_beats, awsize=5, awburst=1, bytes_per_beat=32):
    """Issue one AXI4 write burst; return (bresp, tlp_accept, tlp_byte_count)."""
    # ---- AW phase ----
    dut.s_axi_awaddr.value = 0
    dut.s_axi_awlen.value = n_beats - 1
    dut.s_axi_awsize.value = awsize
    dut.s_axi_awburst.value = awburst
    dut.s_axi_awvalid.value = 1
    while True:
        await FallingEdge(dut.axi_aclk)        # sample registered ready mid-cycle
        if dut.s_axi_awready.value == 1:
            break
    await RisingEdge(dut.axi_aclk)             # AW handshake consummated here
    dut.s_axi_awvalid.value = 0

    # ---- W phase ---- (contiguous LSB-aligned strobe => wstrb_contiguous=1)
    strb = (1 << bytes_per_beat) - 1
    for i in range(n_beats):
        dut.s_axi_wdata.value = 0xDEADBEEF + i
        dut.s_axi_wstrb.value = strb
        dut.s_axi_wlast.value = 1 if i == n_beats - 1 else 0
        dut.s_axi_wvalid.value = 1
        while True:
            await FallingEdge(dut.axi_aclk)
            if dut.s_axi_wready.value == 1:
                break
        await RisingEdge(dut.axi_aclk)         # W beat handshake consummated
    dut.s_axi_wvalid.value = 0
    dut.s_axi_wlast.value = 0

    # ---- B phase ----
    dut.s_axi_bready.value = 1
    while True:
        await FallingEdge(dut.axi_aclk)
        if dut.s_axi_bvalid.value == 1:
            break
    bresp = int(dut.s_axi_bresp.value)
    await RisingEdge(dut.axi_aclk)             # B handshake consummated here
    dut.s_axi_bready.value = 0
    await FallingEdge(dut.axi_aclk)            # tlp_accept pulses the cycle after B
    accept = int(dut.tlp_accept.value)
    byte_count = int(dut.tlp_byte_count.value)
    return bresp, accept, byte_count


def fl_expect(awsize, awburst, total_bytes):
    """Golden expectation from the FunctionalModel FM_INGEST_TLP transaction."""
    fl = FunctionalModel()
    txn = {
        "kind": "FM_INGEST_TLP",
        "wlast_seen": 1,
        "awsize": awsize,
        "awburst": awburst,
        "wstrb_contiguous": 1,
        "tlp_byte_count": total_bytes,
    }
    r = fl.apply(txn)
    return int(r.get("bresp_next", 0)), int(r.get("state_updates", {}).get("tlp_accept", 0))


@cocotb.test()
async def test_ingress_fl_equivalence(dut):
    cocotb.start_soon(Clock(dut.axi_aclk, 2, units="ns").start())
    await reset_dut(dut)

    # (name, n_beats, awsize, awburst, bytes_per_beat)
    scenarios = [
        ("legal_64B_2beat",       2, 5, 1, 32),
        ("legal_min_32B_1beat",   1, 5, 1, 32),
        ("legal_128B_4beat",      4, 5, 1, 32),
        ("illegal_awsize_8B",     2, 3, 1, 32),
        ("illegal_burst_fixed",   2, 5, 0, 32),
        ("too_small_8B_1beat",    1, 5, 1, 8),
    ]

    mismatches = 0
    for name, n, sz, bu, bpb in scenarios:
        bresp, accept, byte_count = await axi_write_burst(dut, n, sz, bu, bpb)
        total = n * bpb
        exp_bresp, exp_accept = fl_expect(sz, bu, total)
        bytes_ok = (byte_count == total) if accept else True
        ok = (bresp == exp_bresp) and (accept == exp_accept) and bytes_ok
        dut._log.info(
            f"[{name}] DUT(bresp={bresp}, accept={accept}, bytes={byte_count}) "
            f"FL(bresp={exp_bresp}, accept={exp_accept}, bytes={total}) -> "
            f"{'PASS' if ok else 'MISMATCH'}"
        )
        if not ok:
            mismatches += 1
        await ClockCycles(dut.axi_aclk, 3)

    assert mismatches == 0, f"{mismatches} FL/RTL scoreboard mismatch(es)"
    dut._log.info(f"all {len(scenarios)} ingress scenarios match the FL oracle")


async def axi_write_explicit_strb(dut, strbs, awsize=5, awburst=1):
    """Drive a burst with caller-specified per-beat WSTRB patterns."""
    dut.s_axi_awaddr.value = 0
    dut.s_axi_awlen.value = len(strbs) - 1
    dut.s_axi_awsize.value = awsize
    dut.s_axi_awburst.value = awburst
    dut.s_axi_awvalid.value = 1
    while True:
        await FallingEdge(dut.axi_aclk)
        if dut.s_axi_awready.value == 1:
            break
    await RisingEdge(dut.axi_aclk)
    dut.s_axi_awvalid.value = 0
    for i, strb in enumerate(strbs):
        dut.s_axi_wdata.value = 0xA5A50000 + i
        dut.s_axi_wstrb.value = strb
        dut.s_axi_wlast.value = 1 if i == len(strbs) - 1 else 0
        dut.s_axi_wvalid.value = 1
        while True:
            await FallingEdge(dut.axi_aclk)
            if dut.s_axi_wready.value == 1:
                break
        await RisingEdge(dut.axi_aclk)
    dut.s_axi_wvalid.value = 0
    dut.s_axi_wlast.value = 0
    dut.s_axi_bready.value = 1
    while True:
        await FallingEdge(dut.axi_aclk)
        if dut.s_axi_bvalid.value == 1:
            break
    bresp = int(dut.s_axi_bresp.value)
    await RisingEdge(dut.axi_aclk)
    dut.s_axi_bready.value = 0
    await FallingEdge(dut.axi_aclk)
    return bresp, int(dut.tlp_accept.value), int(dut.tlp_byte_count.value)


def strb_is_contiguous(strb, width=32):
    if strb == 0:
        return True
    ones = [i for i in range(width) if (strb >> i) & 1]
    return (max(ones) - min(ones) + 1) == len(ones)


@cocotb.test()
async def test_ingress_contiguity_gap(dut):
    """Adversarial probe: a legal-size/burst TLP whose WSTRB is NON-contiguous.

    The FL oracle requires wstrb_contiguous; the authored RTL does NOT check it.
    This deliberately exercises the case the 6-scenario suite avoided, to show
    whether ingress equivalence is actually closed.
    """
    cocotb.start_soon(Clock(dut.axi_aclk, 2, units="ns").start())
    await reset_dut(dut)

    strb = 0x00FF00FF                      # 16 set bits with an interior gap
    n_bytes = bin(strb).count("1")
    contig = strb_is_contiguous(strb)
    bresp, dut_accept, byte_count = await axi_write_explicit_strb(dut, [strb])

    fl = FunctionalModel()
    r = fl.apply({
        "kind": "FM_INGEST_TLP", "wlast_seen": 1, "awsize": 5, "awburst": 1,
        "wstrb_contiguous": 1 if contig else 0, "tlp_byte_count": n_bytes,
    })
    fl_accept = int(r.get("state_updates", {}).get("tlp_accept", 0))

    dut._log.info(
        f"non-contiguous WSTRB=0x{strb:08X} (contig={contig}, bytes={n_bytes}): "
        f"DUT accept={dut_accept}, FL accept={fl_accept}"
    )
    assert dut_accept == fl_accept, (
        f"FL/RTL DIVERGENCE: DUT accept={dut_accept} but FL accept={fl_accept} — "
        "RTL ingress does not implement the wstrb_contiguous check the oracle requires; "
        "ingress equivalence is NOT closed."
    )

