"""Protocol-assertion simulation evidence for mctp_assembler_v3.

This test is the runtime companion to verify/protocol_assertions.sva. iverilog's
concurrent-SVA support does not cover the cross-domain / pseudo-syntax stubs the
SSOT emitter produces, so the same handshake-stability contracts are checked here
as live per-cycle procedural assertions against the REAL DUT signals while the
datapath runs representative traffic — including deliberate backpressure episodes
so the "hold stable while valid && !ready" contracts are genuinely exercised
rather than vacuously satisfied.

Every contract maps to an SSOT cycle_model.handshake_rules / interface obligation
(the same rules listed in protocol_assertions.sva):
  - p_axi_b      : s_axi_bvalid/bresp held stable while bvalid && !bready
  - p_axi_r      : s_axi_rvalid/rdata/rlast/rresp held stable while rvalid && !rready
  - p_sram_wr    : sram_wr_addr/data/strb held stable while sram_wr_valid && !sram_wr_ready
  - p_sram_rdreq : sram_rd_req_addr held stable while sram_rd_req_valid && !sram_rd_req_ready
  - p_apb        : pslverr only asserted together with pready (access-phase completion)

Any violation is appended to sim/assertion_failures.jsonl. A clean run leaves the
file empty (zero failure records), which is the evidence the rtl-gen
protocol_assertion_evidence gate consumes.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ClockCycles, with_timeout

TB_DIR = Path(__file__).resolve().parent
if str(TB_DIR) not in sys.path:
    sys.path.insert(0, str(TB_DIR))

import mctp_stimulus as S  # noqa: E402

SIM_DIR = TB_DIR.parent.parent / "sim"
FAILURES_PATH = SIM_DIR / "assertion_failures.jsonl"


def _int(sig) -> int:
    """Resolved integer value of a handle, or -1 if it carries x/z."""
    try:
        return int(sig.value)
    except Exception:
        return -1


class ProtocolChecker:
    """Per-cycle procedural checker for DUT handshake-stability contracts."""

    def __init__(self, dut):
        self.dut = dut
        self.failures: list[dict] = []
        self.cycles = 0
        # Previous-cycle holds for the *_valid && !*_ready stability checks.
        self._prev = {}

    def _record(self, rule: str, detail: str) -> None:
        self.failures.append({
            "type": "protocol_assertion_failure",
            "rule": rule,
            "cycle": self.cycles,
            "detail": detail,
        })

    def _check_hold(self, rule: str, valid, ready, fields: dict) -> None:
        """Assert payload fields are stable while valid && !ready (no withdrawal)."""
        v = _int(valid)
        r = _int(ready)
        cur = {name: _int(sig) for name, sig in fields.items()}
        prev = self._prev.get(rule)
        # Stalled last cycle (valid high, ready low): this cycle valid must still
        # be high and every payload field must be unchanged.
        if prev is not None and prev["valid"] == 1 and prev["ready"] == 0:
            if v != 1:
                self._record(rule, f"{rule}: valid dropped during backpressure stall")
            for name, val in cur.items():
                if val != prev["fields"][name]:
                    self._record(
                        rule,
                        f"{rule}: {name} changed under backpressure "
                        f"({prev['fields'][name]} -> {val})",
                    )
        self._prev[rule] = {"valid": v, "ready": r, "fields": cur}

    def sample(self) -> None:
        d = self.dut
        self.cycles += 1
        # AXI write B channel: bvalid/bresp stable until bready.
        self._check_hold("p_axi_b", d.s_axi_bvalid, d.s_axi_bready,
                         {"s_axi_bresp": d.s_axi_bresp})
        # AXI read R channel: rvalid/rdata/rlast/rresp stable until rready.
        self._check_hold("p_axi_r", d.s_axi_rvalid, d.s_axi_rready,
                         {"s_axi_rdata": d.s_axi_rdata, "s_axi_rlast": d.s_axi_rlast,
                          "s_axi_rresp": d.s_axi_rresp})
        # SRAM write: addr/data/strb stable while sram_wr_valid && !sram_wr_ready.
        self._check_hold("p_sram_wr", d.sram_wr_valid, d.sram_wr_ready,
                         {"sram_wr_addr": d.sram_wr_addr, "sram_wr_data": d.sram_wr_data,
                          "sram_wr_strb": d.sram_wr_strb})
        # SRAM read request: addr stable while sram_rd_req_valid && !sram_rd_req_ready.
        self._check_hold("p_sram_rdreq", d.sram_rd_req_valid, d.sram_rd_req_ready,
                         {"sram_rd_req_addr": d.sram_rd_req_addr})
        # APB access phase: pslverr may only assert together with pready.
        if _int(d.pslverr) == 1 and _int(d.pready) != 1:
            self._record("p_apb", "p_apb: pslverr asserted without pready")

    async def run(self) -> None:
        while True:
            await RisingEdge(self.dut.axi_aclk)
            self.sample()


async def _drive_with_backpressure(dut, monitor):
    """Run representative traffic, injecting ready-stalls so the hold contracts fire."""
    sram = bytearray(0x10000)

    # 1) One clean SOM+EOM packet to assemble a descriptor (write path + SRAM wr).
    pkt = S.Packet(source_eid=0x41, message_tag=1, som=1, eom=1, packet_seq=0,
                   payload=S._payload(31))
    await with_timeout(S.send_packet(dut, pkt, monitor=monitor, cycles=80), 60, "us")

    # 2) AXI read back (read BFM owns s_axi_rready); exercises the R / SRAM-rd-req
    #    handshakes through a full firmware read.
    await with_timeout(S.axi_read(dut, araddr=0, n_beats=1, sram_mem=sram), 60, "us")
    await ClockCycles(dut.axi_aclk, 4)

    # 3) SRAM-write backpressure: hold sram_wr_ready low across the next packet's
    #    pack writes so the p_sram_wr "hold stable while valid && !ready" contract
    #    is genuinely exercised, then release and let it drain.
    dut.sram_wr_ready.value = 0
    cocotb.start_soon(S.send_packet(dut, S.Packet(
        source_eid=0x42, message_tag=2, som=1, eom=1, packet_seq=0,
        payload=S._payload(31)), monitor=monitor, cycles=80))
    await ClockCycles(dut.axi_aclk, 8)
    dut.sram_wr_ready.value = 1
    await ClockCycles(dut.axi_aclk, 40)


@cocotb.test()
async def protocol_assertions(dut):
    """Run the DUT under traffic + backpressure and capture handshake violations."""
    cocotb.start_soon(Clock(dut.axi_aclk, 10, units="ns").start())
    cocotb.start_soon(Clock(dut.pclk, 10, units="ns").start())
    await S.reset_dut(dut)
    await with_timeout(S.configure(dut, enable=1, tu_bytes=64, sram_limit=0xFFFF), 50, "us")

    checker = ProtocolChecker(dut)
    cocotb.start_soon(checker.run())

    monitor = S.DatapathMonitor(dut)
    cocotb.start_soon(monitor.run())

    await _drive_with_backpressure(dut, monitor)
    await ClockCycles(dut.axi_aclk, 10)

    SIM_DIR.mkdir(parents=True, exist_ok=True)
    with open(FAILURES_PATH, "w", encoding="utf-8") as fh:
        for rec in checker.failures:
            fh.write(json.dumps(rec) + "\n")

    dut._log.info(
        f"PROTOCOL_ASSERTIONS cycles={checker.cycles} "
        f"failures={len(checker.failures)} -> {FAILURES_PATH}"
    )
    assert not checker.failures, (
        f"protocol assertion failures: {checker.failures[:8]}"
    )
