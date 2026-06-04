"""Datapath safety-property simulation evidence for mctp_assembler_v3 (C1).

Runtime companion to verify/safety_properties.sva. iverilog's concurrent-SVA
support does not cover the stateful cross-stage datapath properties below (it only
handles the simple handshake-stability stubs the SSOT emitter produces; see
test_protocol_assertions.py), so the GENUINE enforcement is this per-cycle
procedural checker run against the REAL DUT signals while representative traffic —
clean packets, fragmented assembly, a max-size (4096B) payload, context-table
drops, and SRAM/AXI backpressure — exercises every property non-vacuously.

Properties (each maps to verify/safety_properties.sva and to an SSOT obligation):
  P1 no_sram_write_on_drop      : a context-table-dropped packet's payload never
                                  reaches a pack/SRAM write (the pack engine drains
                                  it; stream_write=0). [function_model drop path]
  P2 sram_payload_no_holes      : within a message, the per-context byte write
                                  pointer is strictly contiguous
                                  (addr_n == addr_{n-1} + bytes_{n-1}); no gaps.
                                  [FM_PACK_SRAM no-hole packing]
  P3 descriptor_after_assembly  : descriptor_push only fires when the pack engine
                                  is idle (no pack write outstanding) and an EOM
                                  was reached for the message. [FM_PUBLISH_DESCRIPTOR]
  P4 pack_word_le_32B           : every pack write requests <= AXI_STRB_WIDTH(=32)
                                  bytes (the sram_packer <=32B/word invariant).
  P5 tlp_accept_after_bresp     : ingress tlp_accept pulses only AFTER the B
                                  handshake (bvalid && bready) completed the prior
                                  cycle; it never leads the response. [ingress fsm]

Each property is also independently proven NON-VACUOUS by a negative control: a
synthetic per-cycle sample that violates exactly that property is fed to the same
check method, and the test asserts the checker FIRES (records a failure) for it.
A clean DUT run (zero real failures) plus all five negative controls firing is the
evidence written to sim/safety_assertions_evidence.json.
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
EVIDENCE_PATH = SIM_DIR / "safety_assertions_evidence.json"

AXI_STRB_WIDTH = 32  # bytes per 256-bit SRAM word (sram_packer invariant)


def _int(sig) -> int:
    """Resolved integer value of a handle, or -1 if it carries x/z."""
    try:
        return int(sig.value)
    except Exception:
        return -1


class SafetyChecker:
    """Per-cycle procedural checker for the five datapath safety properties.

    Each property is a discrete method over a sampled-signal dict `s`, so the same
    logic that runs against the real DUT can be unit-fired with a synthetic
    violating sample for the non-vacuity (negative-control) proofs.
    """

    PROPS = (
        "P1_no_sram_write_on_drop",
        "P2_sram_payload_no_holes",
        "P3_descriptor_after_assembly",
        "P4_pack_word_le_32B",
        "P5_tlp_accept_after_bresp",
    )

    def __init__(self, dut=None):
        self.dut = dut
        self.failures: list[dict] = []
        self.cycles = 0
        # Cross-cycle state.
        self._prev = None                 # previous-cycle sample (for P5 ordering)
        self._exp_next_addr = None        # P2: expected contiguous next byte addr
        self._msg_pack_writes = 0         # P2/P3: pack writes since last desc_push
        self._eom_seen = False            # P3: an EOM fragment seen for the message
        # P1: a drop pulse opens a window where the dropped payload must not be
        # written. We count pack writes that occur while the most recent decoded
        # fragment was a drop and no accept is in flight.
        self._drop_window = 0
        # Antecedent-coverage counters: how many times each property's PRECONDITION
        # actually occurred on the real DUT. A property whose antecedent never
        # fires is vacuously satisfied; the test asserts every count > 0 so each
        # property is genuinely exercised (not just non-vacuous in the unit sense).
        self.cov = {
            "P1_drop_windows": 0,       # drop pulses that opened a no-write window
            "P2_continuation_writes": 0,  # in-message writes checked for contiguity
            "P3_descriptor_pushes": 0,  # descriptor_push events checked
            "P4_pack_writes": 0,        # pack writes checked for <=32B
            "P5_tlp_accepts": 0,        # tlp_accept pulses checked for B-handshake order
        }

    # ---- recording -------------------------------------------------------
    def _record(self, prop: str, detail: str, cycle: int | None = None) -> None:
        self.failures.append({
            "type": "safety_property_failure",
            "property": prop,
            "cycle": self.cycles if cycle is None else cycle,
            "detail": detail,
        })

    # ---- individual property checks (pure over sample `s` + self state) ---
    def _check_p4(self, s) -> None:
        """P4: pack_wr_bytes <= 32 on every requested pack write."""
        if s["pack_wr_valid"] == 1:
            self.cov["P4_pack_writes"] += 1
            if s["pack_wr_bytes"] > AXI_STRB_WIDTH:
                self._record(
                    "P4_pack_word_le_32B",
                    f"pack_wr_bytes={s['pack_wr_bytes']} exceeds {AXI_STRB_WIDTH}",
                )

    def _check_p5(self, s) -> None:
        """P5: tlp_accept this cycle ⟹ B handshake (bvalid&bready) the prior cycle."""
        if s["tlp_accept"] == 1:
            self.cov["P5_tlp_accepts"] += 1
            prev = self._prev
            b_done = prev is not None and prev["s_axi_bvalid"] == 1 and prev["s_axi_bready"] == 1
            if not b_done:
                self._record(
                    "P5_tlp_accept_after_bresp",
                    "tlp_accept pulsed without a completed B handshake on the prior cycle",
                )

    def _check_p3(self, s) -> None:
        """P3: descriptor_push ⟹ pack engine idle (no write outstanding) AND EOM seen."""
        if s["descriptor_push"] == 1:
            self.cov["P3_descriptor_pushes"] += 1
            if s["pack_wr_valid"] == 1:
                self._record(
                    "P3_descriptor_after_assembly",
                    "descriptor_push asserted while a pack write is still outstanding",
                )
            if not self._eom_seen:
                self._record(
                    "P3_descriptor_after_assembly",
                    "descriptor_push asserted before an EOM fragment was seen",
                )

    def _check_p2(self, s, accepted_write: bool) -> None:
        """P2: within a message, accepted pack writes are byte-contiguous."""
        if not accepted_write:
            return
        first_of_msg = self._msg_pack_writes == 0
        if (not first_of_msg) and self._exp_next_addr is not None:
            # A continuation write inside a message — the contiguity check applies.
            self.cov["P2_continuation_writes"] += 1
            if s["pack_wr_addr"] != self._exp_next_addr:
                self._record(
                    "P2_sram_payload_no_holes",
                    f"non-contiguous payload write: addr={s['pack_wr_addr']} "
                    f"expected={self._exp_next_addr} (hole/gap)",
                )

    def _check_p1(self, s, accepted_write: bool) -> None:
        """P1: while only a dropped packet is in flight, no payload write occurs."""
        if self._drop_window > 0:
            self.cov["P1_drop_windows"] += 1
            if accepted_write:
                self._record(
                    "P1_no_sram_write_on_drop",
                    "pack/SRAM write occurred for a packet whose payload was dropped",
                )

    # ---- sample assembly + state advance ---------------------------------
    @staticmethod
    def _sample(d) -> dict:
        return {
            "packet_drop_pulse": _int(d.packet_drop_pulse),
            "assembly_drop_pulse": _int(d.assembly_drop_pulse),
            "frag_valid": _int(d.frag_valid),
            "frag_som": _int(d.frag_som),
            "frag_eom": _int(d.frag_eom),
            "pack_wr_valid": _int(d.pack_wr_valid),
            "pack_wr_ready": _int(d.pack_wr_ready),
            "pack_wr_addr": _int(d.pack_wr_addr),
            "pack_wr_bytes": _int(d.pack_wr_bytes),
            "descriptor_push": _int(d.descriptor_push),
            "tlp_accept": _int(d.tlp_accept),
            "s_axi_bvalid": _int(d.s_axi_bvalid),
            "s_axi_bready": _int(d.s_axi_bready),
        }

    def evaluate(self, s) -> None:
        """Run all five property checks against sample `s` and advance state."""
        accepted_write = (s["pack_wr_valid"] == 1 and s["pack_wr_ready"] == 1)

        # P1 drop window: a context-table drop pulse this cycle (no accepted
        # fragment write path opened) means the in-flight decoded packet's payload
        # must be drained, not written. Open a short window covering its beats.
        if s["packet_drop_pulse"] == 1 or s["assembly_drop_pulse"] == 1:
            # A drop and an accept cannot both be the same fragment; if a write is
            # already streaming for an accepted prior packet we must not falsely
            # flag it, so only open the window when no write is mid-flight.
            if s["pack_wr_valid"] == 0:
                self._drop_window = 12  # cover the dropped packet's drained beats

        # Order matters: evaluate before advancing the running pointers.
        self._check_p4(s)
        self._check_p5(s)
        self._check_p3(s)
        self._check_p2(s, accepted_write)
        self._check_p1(s, accepted_write)

        # ---- advance cross-cycle state ----
        if s["frag_valid"] == 1 and s["frag_eom"] == 1:
            self._eom_seen = True
        if accepted_write:
            self._exp_next_addr = s["pack_wr_addr"] + s["pack_wr_bytes"]
            self._msg_pack_writes += 1
            if self._drop_window > 0:
                self._drop_window -= 1  # consumed by the (erroneous) write above
        elif self._drop_window > 0:
            self._drop_window -= 1
        # Message-boundary reset: the per-context byte pointer is only contiguous
        # WITHIN one message. The contiguity run therefore restarts at every
        # boundary — a successful publish (descriptor_push), an aborted message
        # (packet/assembly drop), or a fresh allocation (SOM-accepted fragment) —
        # since each begins a new, separately bump-allocated SRAM region. A genuine
        # hole is a non-contiguous write with NO intervening boundary (the run is
        # still open), which is exactly what _check_p2 flags.
        som_alloc = (s["frag_valid"] == 1 and s["frag_som"] == 1)
        boundary = (s["descriptor_push"] == 1 or s["packet_drop_pulse"] == 1
                    or s["assembly_drop_pulse"] == 1 or som_alloc)
        if boundary:
            self._msg_pack_writes = 0
            self._exp_next_addr = None
            if s["descriptor_push"] == 1:
                self._eom_seen = False
        self._prev = s

    def sample(self) -> None:
        self.cycles += 1
        self.evaluate(self._sample(self.dut))

    async def run(self) -> None:
        while True:
            await RisingEdge(self.dut.axi_aclk)
            self.sample()


# ---------------------------------------------------------------------------
# Representative traffic that exercises every property non-vacuously.
# ---------------------------------------------------------------------------
async def _drive(dut, monitor):
    sram = bytearray(0x10000)

    # 1) Clean single packet (32B) -> SRAM write + descriptor (P2/P3/P4/P5).
    await with_timeout(S.send_packet(dut, S.Packet(
        source_eid=0x41, message_tag=1, som=1, eom=1, packet_seq=0,
        payload=S._payload(31)), monitor=monitor, cycles=80), 60, "us")
    await with_timeout(S.axi_read(dut, araddr=0, n_beats=1, sram_mem=sram), 60, "us")
    await S.pop_descriptor(dut)

    # 2) Fragmented assembly across a partial-word boundary (P2 no-holes,
    #    multi-beat pack writes, descriptor only after EOM drains).
    await with_timeout(S.send_packet(dut, S.Packet(
        source_eid=0x42, message_tag=2, som=1, eom=0, packet_seq=0,
        payload=S._payload(40)), monitor=monitor, cycles=80), 60, "us")
    await with_timeout(S.send_packet(dut, S.Packet(
        source_eid=0x42, message_tag=2, som=0, eom=1, packet_seq=1,
        payload=S._payload(22, seed=5)), monitor=monitor, cycles=120), 60, "us")
    await S.pop_descriptor(dut)

    # 3) Max-size payload (4096B) -> 128 contiguous pack writes (P2/P4 at scale).
    await with_timeout(S.send_packet(dut, S.Packet(
        source_eid=0x48, message_tag=1, som=1, eom=1, packet_seq=0,
        payload=S._payload(4095)), monitor=monitor, cycles=500), 90, "us")
    await S.pop_descriptor(dut)

    # 4) Context-table drop with payload: SOM=0 middle packet, no active context
    #    -> PD_UNEXPECTED_MIDDLE_END. Its payload MUST be drained (P1).
    await with_timeout(S.send_packet(dut, S.Packet(
        source_eid=0x59, message_tag=4, som=0, eom=0, packet_seq=1,
        payload=S._payload(31)), monitor=monitor, cycles=80), 60, "us")

    # 5) Duplicate-SOM assembly drop (AD_DUPLICATE_SOM): first SOM streams, second
    #    SOM for the same key is dropped and its payload drained (P1 again).
    await with_timeout(S.send_packet(dut, S.Packet(
        source_eid=0x52, message_tag=1, som=1, eom=0, packet_seq=0,
        payload=S._payload(63)), monitor=monitor, cycles=80), 60, "us")
    await with_timeout(S.send_packet(dut, S.Packet(
        source_eid=0x52, message_tag=1, som=1, eom=0, packet_seq=0,
        payload=S._payload(63)), monitor=monitor, cycles=80), 60, "us")

    # 6) SRAM-write backpressure across a packet's pack writes (P2/P3 under stall:
    #    descriptor must still wait for the drained writes; pointer stays contiguous).
    dut.sram_wr_ready.value = 0
    cocotb.start_soon(S.send_packet(dut, S.Packet(
        source_eid=0x43, message_tag=3, som=1, eom=1, packet_seq=0,
        payload=S._payload(63)), monitor=monitor, cycles=120))
    await ClockCycles(dut.axi_aclk, 10)
    dut.sram_wr_ready.value = 1
    await ClockCycles(dut.axi_aclk, 60)


# ---------------------------------------------------------------------------
# Negative controls: prove each property is non-vacuous by feeding the SAME
# check method a synthetic sample that violates exactly that property and
# asserting the checker fires. No RTL/SSOT is touched.
# ---------------------------------------------------------------------------
def _negative_controls() -> list[dict]:
    results = []

    def base():
        return {
            "packet_drop_pulse": 0, "assembly_drop_pulse": 0, "frag_valid": 0,
            "frag_som": 0, "frag_eom": 0, "pack_wr_valid": 0, "pack_wr_ready": 0,
            "pack_wr_addr": 0, "pack_wr_bytes": 0, "descriptor_push": 0,
            "tlp_accept": 0, "s_axi_bvalid": 0, "s_axi_bready": 0,
        }

    # P4: a pack write of 33 bytes must fire P4.
    c = SafetyChecker()
    s = base(); s.update(pack_wr_valid=1, pack_wr_ready=1, pack_wr_bytes=33)
    c.evaluate(s)
    fired = any(f["property"] == "P4_pack_word_le_32B" for f in c.failures)
    results.append({"property": "P4_pack_word_le_32B", "fired": fired,
                    "injection": "pack_wr_valid=1, pack_wr_bytes=33 (>32)",
                    "failure": next((f for f in c.failures if f["property"] == "P4_pack_word_le_32B"), None)})

    # P5: tlp_accept with NO prior-cycle B handshake must fire P5.
    c = SafetyChecker()
    c.evaluate(base())                       # prior cycle: no B handshake
    s = base(); s.update(tlp_accept=1)
    c.evaluate(s)
    fired = any(f["property"] == "P5_tlp_accept_after_bresp" for f in c.failures)
    results.append({"property": "P5_tlp_accept_after_bresp", "fired": fired,
                    "injection": "tlp_accept=1 with no bvalid&bready on the prior cycle",
                    "failure": next((f for f in c.failures if f["property"] == "P5_tlp_accept_after_bresp"), None)})

    # P3: descriptor_push while a pack write is outstanding (engine busy) AND no
    # EOM seen must fire P3.
    c = SafetyChecker()
    s = base(); s.update(descriptor_push=1, pack_wr_valid=1)
    c.evaluate(s)
    fired = any(f["property"] == "P3_descriptor_after_assembly" for f in c.failures)
    results.append({"property": "P3_descriptor_after_assembly", "fired": fired,
                    "injection": "descriptor_push=1 while pack_wr_valid=1 and no EOM seen",
                    "failure": next((f for f in c.failures if f["property"] == "P3_descriptor_after_assembly"), None)})

    # P2: two accepted writes with a GAP (addr jumps past expected) must fire P2.
    c = SafetyChecker()
    s1 = base(); s1.update(frag_valid=1, frag_eom=1, pack_wr_valid=1, pack_wr_ready=1,
                           pack_wr_addr=0, pack_wr_bytes=32)
    c.evaluate(s1)                           # first write of the message: addr 0..31
    s2 = base(); s2.update(pack_wr_valid=1, pack_wr_ready=1,
                           pack_wr_addr=64, pack_wr_bytes=32)  # expected 32, got 64 -> hole
    c.evaluate(s2)
    fired = any(f["property"] == "P2_sram_payload_no_holes" for f in c.failures)
    results.append({"property": "P2_sram_payload_no_holes", "fired": fired,
                    "injection": "consecutive in-message writes addr 0(+32) then 64 (expected 32) -> 32B hole",
                    "failure": next((f for f in c.failures if f["property"] == "P2_sram_payload_no_holes"), None)})

    # P1: a drop pulse opens the window, then a pack write occurs within it -> fire P1.
    c = SafetyChecker()
    sd = base(); sd.update(packet_drop_pulse=1)
    c.evaluate(sd)                           # opens the drop window (no write in flight)
    sw = base(); sw.update(pack_wr_valid=1, pack_wr_ready=1, pack_wr_addr=0, pack_wr_bytes=16)
    c.evaluate(sw)                           # a write for the dropped payload -> violation
    fired = any(f["property"] == "P1_no_sram_write_on_drop" for f in c.failures)
    results.append({"property": "P1_no_sram_write_on_drop", "fired": fired,
                    "injection": "packet_drop_pulse=1 then an accepted pack write within the drop window",
                    "failure": next((f for f in c.failures if f["property"] == "P1_no_sram_write_on_drop"), None)})

    return results


@cocotb.test()
async def safety_properties(dut):
    """Run the five datapath safety properties green on the real DUT, then prove
    each is non-vacuous with a negative control."""
    cocotb.start_soon(Clock(dut.axi_aclk, 10, units="ns").start())
    cocotb.start_soon(Clock(dut.pclk, 10, units="ns").start())
    await S.reset_dut(dut)
    await with_timeout(S.configure(dut, enable=1, tu_bytes=4096,
                                   max_message_bytes=4096, sram_limit=0xFFFF,
                                   timeout_cycles=0xFFFFFF), 50, "us")

    checker = SafetyChecker(dut)
    cocotb.start_soon(checker.run())
    monitor = S.DatapathMonitor(dut)
    cocotb.start_soon(monitor.run())

    await _drive(dut, monitor)
    await ClockCycles(dut.axi_aclk, 10)

    # Negative controls (non-vacuity proof) — pure unit-fires, no DUT mutation.
    neg = _negative_controls()
    all_fired = all(n["fired"] for n in neg)

    # Antecedent coverage: each property's PRECONDITION must have actually occurred
    # on the real DUT, else the green pass is vacuous. Require every count > 0.
    cov = checker.cov
    all_exercised = all(v > 0 for v in cov.values())

    evidence = {
        "schema_version": 1,
        "type": "safety_assertions_evidence",
        "ip": "mctp_assembler_v3",
        "spec": "verify/safety_properties.sva",
        "checker": "tb/cocotb/test_safety_properties.py",
        "cycles": checker.cycles,
        "real_run_failures": checker.failures,
        "antecedent_coverage": cov,
        "status": "pass" if (not checker.failures and all_fired and all_exercised) else "fail",
        "properties": [
            {"id": "P1_no_sram_write_on_drop",
             "desc": "dropped packet payload never written to SRAM (drained)"},
            {"id": "P2_sram_payload_no_holes",
             "desc": "within a message the byte write pointer is strictly contiguous"},
            {"id": "P3_descriptor_after_assembly",
             "desc": "descriptor_push only when pack engine idle and EOM seen"},
            {"id": "P4_pack_word_le_32B",
             "desc": "every pack write requests <=32 bytes"},
            {"id": "P5_tlp_accept_after_bresp",
             "desc": "tlp_accept only after the B handshake completes"},
        ],
        "negative_controls": neg,
    }
    SIM_DIR.mkdir(parents=True, exist_ok=True)
    with open(EVIDENCE_PATH, "w", encoding="utf-8") as fh:
        json.dump(evidence, fh, indent=2)

    dut._log.info(
        f"SAFETY_PROPERTIES cycles={checker.cycles} "
        f"real_failures={len(checker.failures)} neg_controls_fired={sum(n['fired'] for n in neg)}/5 "
        f"coverage={cov} -> {EVIDENCE_PATH}"
    )

    assert not checker.failures, (
        f"safety property failures on real DUT (REAL BUGS — do not mask): "
        f"{checker.failures[:8]}"
    )
    for n in neg:
        assert n["fired"], (
            f"negative control did NOT fire for {n['property']} — the check is "
            f"vacuous and must be fixed: {n}"
        )
    for name, count in cov.items():
        assert count > 0, (
            f"property antecedent never exercised on the real DUT ({name}=0) — "
            f"the green pass would be vacuous; strengthen the traffic: {cov}"
        )
