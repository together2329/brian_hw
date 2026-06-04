"""IP-specific MCTP VDM-TLP stimulus layer for mctp_assembler_v3.

The generic goal-scoreboard harness drives field-shaped garbage into the AXI
write slave, so the PCIe-VDM parser correctly rejects every beat (vdm_valid
never pulses) and the whole assembly datapath stays idle. This module lowers
each SSOT scenario into a *real* valid VDM-TLP AXI4 write burst (or read burst)
that exercises the datapath end-to-end, exactly as a firmware/PCIe peer would.

Three layers, mirroring mctp_assembler_scratch/tb/cocotb structurally without
cloning it:

  * a byte-level TLP builder (`build_vdm_tlp`) that emits the 16B Non-Flit PCIe
    VDM header + MCTP transport header + SOM body byte + payload, packed into
    256-bit AXI beats, per the byte map frozen in the parser / decoder RTL;
  * AXI4 BFMs: `axi_write_tlp` (AW->W->B, multi-beat, full WSTRB), `axi_read`
    (AR->R) plus an `sram_model` that services the DUT's external SRAM port;
  * `apb_write` / `apb_read` for CONTROL/CFG_* setup and counter/descriptor
    readback.

Byte map (lane N of the TLP = beat0[8*N +: 8]) — see
rtl/mctp_assembler_v3_pcie_vdm_parser.sv and ..._mctp_decoder.sv:
    tlp[0] {fmt[7:5], type[4:0]}  routing_type = tlp[0][2:0]   (0/2/3 valid)
    tlp[1] {TC[6:4], ...}         traffic_class = tlp[1][6:4]  (must be 0)
    tlp[1],tlp[2]                 requester_id = (tlp[1]<<8)|tlp[2]
    tlp[3] pad_count[1:0]         pad_len                       (0 here)
    tlp[7] message_code           must be 0x7F
    tlp[8],tlp[9] vendor_id       {0x1A, 0xB4} == 0x1AB4
    tlp[10] vdm_code              must be 0x00
    tlp[12][3:0] header_version   must be 1
    tlp[13] dest_eid
    tlp[14] source_eid
    tlp[15] mctp_byte0            {som[7],eom[6],seq[5:4],tag_owner[3],tag[2:0]}
    tlp[16] som_body_byte         {ic[7], message_type[6:0]}   (payload byte 0)

Payload bytes start at offset 16; payload_bytes = tlp_byte_count - 16 - pad_len.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import cocotb
from cocotb.triggers import ClockCycles, FallingEdge, ReadOnly, RisingEdge


# AXI / VDM geometry (mirrors SSOT parameters).
AXI_BYTES = 32           # 256-bit beat
HEADER_BYTES = 16        # Non-Flit PCIe VDM header
SOM_BODY_OFFSET = 16     # SOM body byte (IC + message_type) is payload byte 0

# VDM binding constants.
VDM_MSG_CODE = 0x7F
VDM_VENDOR_HI = 0x1A     # tlp[8]
VDM_VENDOR_LO = 0xB4     # tlp[9]
VDM_CODE = 0x00

# Drop-reason / class encodings (INTEGRATION_CONTRACT §4.2).
DC_NONE, DC_PACKET, DC_ASM = 0, 1, 2
PD_DISABLED_DROP_MODE = 1
PD_MALFORMED_TLP = 2
PD_UNSUPPORTED_VDM = 3
PD_BAD_PAD_OR_ALIGNMENT = 5
PD_BAD_MCTP_HEADER = 4
PD_DEST_EID_REJECT = 6
PD_UNEXPECTED_MIDDLE_END = 7
PD_BAD_OR_EXPIRED_TAG = 8
AD_DUPLICATE_SOM = 9
AD_SEQUENCE_MISMATCH = 10
AD_MESSAGE_OVERFLOW = 11
AD_SRAM_OVERFLOW = 12
AD_DESCRIPTOR_FULL = 13
AD_TIMEOUT = 14

# APB register offsets (SSOT registers.register_list).
REG_CONTROL = 0x0000
REG_CFG_TU = 0x0004
REG_CFG_TIMEOUT = 0x0008
REG_SRAM_BASE = 0x000C
REG_SRAM_LIMIT = 0x0010
REG_STATUS = 0x0020


@dataclass
class Packet:
    """One MCTP transport packet to lower into a VDM-TLP write burst."""

    source_eid: int = 0x22
    dest_eid: int = 0x10
    tag_owner: int = 0
    message_tag: int = 1
    packet_seq: int = 0
    som: int = 1
    eom: int = 1
    message_type: int = 0x7E      # PLDM, arbitrary valid msg type
    ic: int = 0
    payload: bytes = b""          # payload bytes AFTER the SOM body byte
    routing_type: int = 0
    traffic_class: int = 0
    pad_len: int = 0
    header_version: int = 1
    requester_id: int = 0x0102

    def assembly_key(self) -> int:
        return ((self.source_eid & 0xFF) << 4) | ((self.tag_owner & 1) << 3) | (self.message_tag & 0x7)


def _set_byte(buf: bytearray, idx: int, value: int) -> None:
    buf[idx] = value & 0xFF


def build_vdm_tlp(pkt: Packet) -> bytes:
    """Return the ordered raw TLP byte vector for one packet.

    Layout: 16B PCIe/VDM header, then the SOM body byte (IC+message_type) as
    payload byte 0, then the caller's payload bytes. The whole vector is what
    the AXI write driver streams little-endian into 256-bit beats.
    """
    # The IC+message_type "SOM body byte" is part of the message only on SOM
    # packets. A SOM=0 append with no caller payload is a genuine header-only
    # 16-byte TLP (parser payload_bytes = 0): omit the body byte so the
    # zero-payload append path can be exercised without an implicit +1 byte.
    body = bytearray()
    if pkt.som or pkt.payload:
        body.append(((pkt.ic & 1) << 7) | (pkt.message_type & 0x7F))
    body.extend(pkt.payload)

    total = HEADER_BYTES + len(body)
    buf = bytearray(total)

    # --- 16B Non-Flit PCIe VDM header ---
    _set_byte(buf, 0, pkt.routing_type & 0x07)                       # tlp[0] type[2:0]
    _set_byte(buf, 1, ((pkt.traffic_class & 0x7) << 4) |
                       ((pkt.requester_id >> 8) & 0x0F))             # tlp[1] TC[6:4]+req_hi
    _set_byte(buf, 2, pkt.requester_id & 0xFF)                       # tlp[2] req_lo
    _set_byte(buf, 3, pkt.pad_len & 0x03)                            # tlp[3] pad[1:0]
    _set_byte(buf, 7, VDM_MSG_CODE)                                  # tlp[7] message_code
    _set_byte(buf, 8, VDM_VENDOR_HI)                                 # tlp[8] vendor hi
    _set_byte(buf, 9, VDM_VENDOR_LO)                                 # tlp[9] vendor lo
    _set_byte(buf, 10, VDM_CODE)                                     # tlp[10] vdm_code

    # --- MCTP transport header (bytes 12..15) ---
    _set_byte(buf, 12, pkt.header_version & 0x0F)                    # tlp[12] hdr_version[3:0]
    _set_byte(buf, 13, pkt.dest_eid & 0xFF)                          # tlp[13] dest_eid
    _set_byte(buf, 14, pkt.source_eid & 0xFF)                        # tlp[14] source_eid
    mctp_byte0 = (((pkt.som & 1) << 7) | ((pkt.eom & 1) << 6) |
                  ((pkt.packet_seq & 0x3) << 4) | ((pkt.tag_owner & 1) << 3) |
                  (pkt.message_tag & 0x7))
    _set_byte(buf, 15, mctp_byte0)                                   # tlp[15] mctp_byte0

    # --- SOM body byte + payload (bytes 16..) ---
    for i, value in enumerate(body):
        _set_byte(buf, SOM_BODY_OFFSET + i, value)
    return bytes(buf)


def expected_payload_bytes(pkt: Packet) -> int:
    """payload_bytes the parser derives: tlp_byte_count - 16 - pad_len.

    tlp_byte_count is the popcount of the assembled WSTRB, i.e. the total TLP
    length. Here every lane covered by the byte vector is strobed.
    """
    total = HEADER_BYTES + 1 + len(pkt.payload)   # +1 for the SOM body byte
    return total - HEADER_BYTES - (pkt.pad_len & 0x03)


def _word_from_bytes(chunk: bytes) -> int:
    word = 0
    for i, value in enumerate(chunk):
        word |= (value & 0xFF) << (i * 8)
    return word


# ---------------------------------------------------------------------------
# Reset / clocking helpers
# ---------------------------------------------------------------------------
async def reset_dut(dut) -> None:
    """Assert both resets, idle every driven input, then release."""
    dut.axi_aresetn.value = 0
    dut.presetn.value = 0
    # AXI write idle
    dut.s_axi_awaddr.value = 0
    dut.s_axi_awlen.value = 0
    dut.s_axi_awsize.value = 0
    dut.s_axi_awburst.value = 0
    dut.s_axi_awvalid.value = 0
    dut.s_axi_wdata.value = 0
    dut.s_axi_wstrb.value = 0
    dut.s_axi_wlast.value = 0
    dut.s_axi_wvalid.value = 0
    dut.s_axi_bready.value = 1
    # AXI read idle
    dut.s_axi_araddr.value = 0
    dut.s_axi_arlen.value = 0
    dut.s_axi_arsize.value = 0
    dut.s_axi_arburst.value = 0
    dut.s_axi_arvalid.value = 0
    dut.s_axi_rready.value = 1
    # APB idle
    dut.paddr.value = 0
    dut.psel.value = 0
    dut.penable.value = 0
    dut.pwrite.value = 0
    dut.pwdata.value = 0
    dut.pstrb.value = 0xF
    # External SRAM port idle (TB models the SRAM)
    dut.sram_wr_ready.value = 1
    dut.sram_rd_req_ready.value = 1
    dut.sram_rd_rsp_valid.value = 0
    dut.sram_rd_rsp_error.value = 0
    dut.sram_rd_rsp_data.value = 0
    await ClockCycles(dut.axi_aclk, 6)
    dut.axi_aresetn.value = 1
    dut.presetn.value = 1
    await ClockCycles(dut.axi_aclk, 4)


# ---------------------------------------------------------------------------
# APB BFM (pclk domain). CONTROL/CFG live in the regfile; cfg_* cross to the
# axi domain via 2-FF synchronizers, so callers settle a few axi cycles after.
# ---------------------------------------------------------------------------
async def apb_write(dut, addr: int, data: int) -> None:
    await FallingEdge(dut.pclk)
    dut.paddr.value = addr & 0xFFFF
    dut.pwdata.value = data & 0xFFFFFFFF
    dut.pstrb.value = 0xF
    dut.pwrite.value = 1
    dut.psel.value = 1
    dut.penable.value = 0
    await RisingEdge(dut.pclk)
    await FallingEdge(dut.pclk)
    dut.penable.value = 1
    # hold until pready
    for _ in range(8):
        await RisingEdge(dut.pclk)
        await ReadOnly()
        if not hasattr(dut, "pready") or int(dut.pready.value):
            break
        await FallingEdge(dut.pclk)
    await FallingEdge(dut.pclk)
    dut.psel.value = 0
    dut.penable.value = 0
    dut.pwrite.value = 0


async def apb_read(dut, addr: int) -> dict[str, int]:
    await FallingEdge(dut.pclk)
    dut.paddr.value = addr & 0xFFFF
    dut.pwrite.value = 0
    dut.psel.value = 1
    dut.penable.value = 0
    await RisingEdge(dut.pclk)
    await FallingEdge(dut.pclk)
    dut.penable.value = 1
    data = 0
    error = 0
    for _ in range(8):
        await RisingEdge(dut.pclk)
        await ReadOnly()
        ready = int(dut.pready.value) if hasattr(dut, "pready") else 1
        if ready:
            data = int(dut.prdata.value)
            error = int(dut.pslverr.value) if hasattr(dut, "pslverr") else 0
            break
        await FallingEdge(dut.pclk)
    await FallingEdge(dut.pclk)
    dut.psel.value = 0
    dut.penable.value = 0
    return {"addr": addr, "data": data, "error": error}


def control_word(*, enable=1, drop_when_disabled=0, dest_filter_enable=0,
                 accept_broadcast=0, accept_null=0, raw_sram_debug=0,
                 local_eid=0, debug_ctx_select=0, descriptor_pop=0,
                 counter_clear=0, soft_reset=0) -> int:
    """Pack CONTROL per SSOT field map."""
    return (
        (enable & 1)
        | ((drop_when_disabled & 1) << 1)
        | ((soft_reset & 1) << 2)
        | ((dest_filter_enable & 1) << 3)
        | ((accept_broadcast & 1) << 4)
        | ((accept_null & 1) << 5)
        | ((raw_sram_debug & 1) << 6)
        | ((descriptor_pop & 1) << 7)
        | ((counter_clear & 1) << 8)
        | ((local_eid & 0xFF) << 16)
        | ((debug_ctx_select & 0xFF) << 24)
    )


async def configure(dut, *, enable=1, drop_when_disabled=0, dest_filter_enable=0,
                    accept_broadcast=0, accept_null=0, raw_sram_debug=0,
                    local_eid=0, debug_ctx_select=0, tu_bytes=64,
                    max_message_bytes=4096, timeout_cycles=0xFFFFFF,
                    sram_base=0, sram_limit=0xFFFF) -> None:
    """Program CONTROL + CFG_* and let the 2-FF cfg sync settle.

    timeout_cycles defaults to the 24-bit max (effectively no assembly timeout)
    so multi-fragment assembly is not aborted mid-flight. Scenarios that
    exercise the timeout path pass an explicit small value.
    """
    await apb_write(dut, REG_SRAM_BASE, sram_base & 0xFFFF)
    await apb_write(dut, REG_SRAM_LIMIT, sram_limit & 0xFFFF)
    await apb_write(dut, REG_CFG_TU, (tu_bytes & 0x1FFF) | ((max_message_bytes & 0x1FFF) << 16))
    await apb_write(dut, REG_CFG_TIMEOUT, timeout_cycles & 0xFFFFFF)
    await apb_write(dut, REG_CONTROL, control_word(
        enable=enable, drop_when_disabled=drop_when_disabled,
        dest_filter_enable=dest_filter_enable, accept_broadcast=accept_broadcast,
        accept_null=accept_null, raw_sram_debug=raw_sram_debug,
        local_eid=local_eid, debug_ctx_select=debug_ctx_select))
    # Settle the pclk->axi 2-FF config synchronizers before driving traffic.
    await ClockCycles(dut.axi_aclk, 8)


async def pop_descriptor(dut) -> None:
    """Pulse CONTROL.descriptor_pop (self-clearing) to retire the oldest desc."""
    await apb_write(dut, REG_CONTROL, control_word(enable=1, descriptor_pop=1))
    await apb_write(dut, REG_CONTROL, control_word(enable=1))
    await ClockCycles(dut.axi_aclk, 6)


# ---------------------------------------------------------------------------
# AXI4 write-burst BFM. Streams a TLP byte vector into 256-bit beats.
# WSTRB rules (ingress): non-final beats must be all-ones, the final beat a
# contiguous LSB run; the assembled byte count (popcount) must be in
# [16, MAX_TLP_BYTES]. `force_wstrb` overrides the final-beat strobe to
# exercise the malformed-TLP drop path.
# ---------------------------------------------------------------------------
async def axi_write_tlp(dut, tlp: bytes, *, awaddr: int = 0,
                        awsize: int = 5, awburst: int = 1,
                        force_wstrb: int | None = None) -> dict[str, Any]:
    total = len(tlp)
    beats = max(1, (total + AXI_BYTES - 1) // AXI_BYTES)
    stream = tlp.ljust(beats * AXI_BYTES, b"\x00")

    awready_seen = 0
    wready_all = True
    wlast_seen: list[int] = []

    # AW phase. Sample the registered s_axi_awready on the FallingEdge (the
    # cycle BEFORE the consummating RisingEdge), then let the handshake fire on
    # the next RisingEdge. Sampling ready at the consummating edge itself races
    # the FSM, which clears awready in the same delta when aw_fire is taken.
    dut.s_axi_awaddr.value = awaddr & 0xFFFF
    dut.s_axi_awlen.value = beats - 1
    dut.s_axi_awsize.value = awsize
    dut.s_axi_awburst.value = awburst
    dut.s_axi_awvalid.value = 1
    for _ in range(64):
        await FallingEdge(dut.axi_aclk)
        if int(dut.s_axi_awready.value):
            awready_seen = 1
            break
    assert awready_seen, "AW handshake timed out: s_axi_awready never asserted"
    await RisingEdge(dut.axi_aclk)            # AW handshake consummated here
    dut.s_axi_awvalid.value = 0

    # W phase. Present each beat at a FallingEdge, hold until s_axi_wready is
    # sampled high at a FallingEdge, then consummate on the immediately
    # following RisingEdge — exactly one accepting RisingEdge per beat so the
    # ingress byte_acc counts each beat once (no phantom re-accept while wvalid
    # lingers with stale data across an extra edge).
    for beat in range(beats):
        chunk = stream[beat * AXI_BYTES:(beat + 1) * AXI_BYTES]
        valid_bytes = min(AXI_BYTES, max(0, total - beat * AXI_BYTES))
        is_last = beat == beats - 1
        if is_last:
            strb = force_wstrb if force_wstrb is not None else ((1 << valid_bytes) - 1)
        else:
            strb = 0xFFFFFFFF
        await FallingEdge(dut.axi_aclk)
        dut.s_axi_wdata.value = _word_from_bytes(chunk)
        dut.s_axi_wstrb.value = strb & 0xFFFFFFFF
        dut.s_axi_wlast.value = 1 if is_last else 0
        dut.s_axi_wvalid.value = 1
        # wready is registered high through S_DATA; if not yet high, wait.
        fired = bool(int(dut.s_axi_wready.value))
        for _ in range(64):
            if fired:
                break
            await FallingEdge(dut.axi_aclk)
            fired = bool(int(dut.s_axi_wready.value))
            if not fired:
                wready_all = False
        assert fired, f"W handshake timed out on beat {beat}: s_axi_wready never asserted"
        await RisingEdge(dut.axi_aclk)        # this beat accepted here
        dut.s_axi_wvalid.value = 0            # drop wvalid so no phantom re-accept
    dut.s_axi_wlast.value = 0

    # B phase. Sample bvalid on FallingEdge, consummate on RisingEdge.
    dut.s_axi_bready.value = 1
    bresp = 0
    bvalid_seen = 0
    for _ in range(64):
        await FallingEdge(dut.axi_aclk)
        if int(dut.s_axi_bvalid.value):
            bvalid_seen = 1
            bresp = int(dut.s_axi_bresp.value)
            break
    if bvalid_seen:
        await RisingEdge(dut.axi_aclk)        # B handshake consummated here
    wlast_seen.append(1)
    return {
        "beats": beats,
        "awlen": beats - 1,
        "awready_seen": awready_seen,
        "wready_all": wready_all,
        "bvalid": bvalid_seen,
        "bresp": bresp,
    }


# ---------------------------------------------------------------------------
# Continuous datapath monitor. The accept/decode/assemble chain emits ONE-CYCLE
# pulses (tlp_accept, vdm_valid, frag_valid, drop pulses, descriptor_push) that
# a poll-after-the-fact loop misses. This monitor runs as a background coroutine
# started right after reset and samples EVERY axi_aclk cycle, accumulating pulse
# hits and the latest latched aggregates, and servicing the external SRAM write
# port into `sram_mem`. Scenarios snapshot()/clear() it around each packet.
# ---------------------------------------------------------------------------
_PULSE_SIGNALS = ("vdm_valid", "frag_valid", "packet_drop_pulse",
                  "assembly_drop_pulse", "descriptor_push",
                  "vdm_drop_valid", "mctp_drop_valid",
                  "ingress_malformed_valid")
_LEVEL_SIGNALS = ("active_context_count", "ctx_state_sel", "ctx_key_sel",
                  "ctx_payload_count_sel", "ctx_expected_seq_sel",
                  "descriptor_valid", "s_axi_bvalid", "s_axi_bresp")


class DatapathMonitor:
    def __init__(self, dut, sram_mem: bytearray | None = None,
                 record_writes: bool = False):
        self.dut = dut
        self.sram_mem = sram_mem
        # Opt-in (default off, no effect on existing tests): when True, every
        # accepted SRAM write beat is appended to write_log as
        # {"addr", "strb", "lanes"} so a monitor can verify the EXACT set of
        # written byte addresses (no-holes / payload-only / no header-or-pad
        # write). The lane list is the absolute byte addresses this beat strobed.
        self.record_writes = record_writes
        self.write_log: list[dict[str, Any]] = []
        self._reset_acc()

    def _reset_acc(self) -> None:
        self.acc: dict[str, Any] = {k: 0 for k in _PULSE_SIGNALS}
        self.acc.update({k: 0 for k in _LEVEL_SIGNALS})
        self.acc["drop_class_o"] = 0
        self.acc["drop_reason_o"] = 0
        self.acc["vdm_drop_reason"] = 0
        self.acc["mctp_drop_reason"] = 0
        self.acc["ingress_malformed_reason"] = 0
        self.acc["sram_wr_valid"] = 0
        self.acc["sram_wr_count"] = 0
        self.acc["sram_wr_addr"] = 0
        self.acc["sram_wr_data"] = 0
        self.acc["sram_wr_strb"] = 0
        self.acc["bvalid"] = 0
        self.acc["bresp"] = 0

    def clear(self) -> None:
        """Reset accumulated pulses; keep nothing stale between packets."""
        self._reset_acc()

    def clear_write_log(self) -> None:
        """Drop recorded SRAM write beats (used to scope the log to one message)."""
        self.write_log = []

    def snapshot(self) -> dict[str, Any]:
        return dict(self.acc)

    def _rd(self, name: str) -> int:
        try:
            return int(getattr(self.dut, name).value)
        except (AttributeError, TypeError, ValueError):
            return 0

    async def run(self) -> None:
        dut = self.dut
        dut.sram_wr_ready.value = 1
        while True:
            await RisingEdge(dut.axi_aclk)
            await ReadOnly()
            for pulse in _PULSE_SIGNALS:
                if self._rd(pulse):
                    self.acc[pulse] = 1
            if self._rd("packet_drop_pulse") or self._rd("assembly_drop_pulse"):
                self.acc["drop_class_o"] = self._rd("last_drop_class")
                self.acc["drop_reason_o"] = self._rd("drop_reason_o")
            # Parser-level (PD_UNSUPPORTED_VDM / PD_BAD_PAD) and decoder-level
            # (PD_BAD_MCTP_HEADER / PD_DEST_EID_REJECT) drops surface on their
            # own *_drop_valid/*_drop_reason nets, NOT on the context_table
            # packet_drop_pulse (which only fires for accepted MCTP fragments).
            if self._rd("vdm_drop_valid"):
                self.acc["vdm_drop_reason"] = self._rd("vdm_drop_reason")
            if self._rd("mctp_drop_valid"):
                self.acc["mctp_drop_reason"] = self._rd("mctp_drop_reason")
            if self._rd("ingress_malformed_valid"):
                self.acc["ingress_malformed_reason"] = self._rd("ingress_malformed_reason")
            if self._rd("s_axi_bvalid"):
                self.acc["bvalid"] = 1
                self.acc["bresp"] = self._rd("s_axi_bresp")
            if self._rd("sram_wr_valid"):
                self.acc["sram_wr_valid"] = 1
                if int(dut.sram_wr_ready.value):
                    self.acc["sram_wr_count"] += 1
                    addr = self._rd("sram_wr_addr")
                    data = self._rd("sram_wr_data")
                    strb = self._rd("sram_wr_strb")
                    # Retain the most recent accepted SRAM write beat so the
                    # scoreboard row can carry real addr/data/strb evidence.
                    self.acc["sram_wr_addr"] = addr
                    self.acc["sram_wr_data"] = data
                    self.acc["sram_wr_strb"] = strb
                    lanes = [addr + lane for lane in range(AXI_BYTES)
                             if (strb >> lane) & 1]
                    if self.sram_mem is not None:
                        for lane in range(AXI_BYTES):
                            if (strb >> lane) & 1 and addr + lane < len(self.sram_mem):
                                self.sram_mem[addr + lane] = (data >> (lane * 8)) & 0xFF
                    if self.record_writes:
                        # Absolute byte addresses this accepted beat strobed —
                        # the genuine no-holes / payload-only / no-header-write
                        # evidence (verified against the descriptor window).
                        self.write_log.append({"addr": addr, "strb": strb, "lanes": lanes})
            self.acc["active_context_count"] = max(self.acc["active_context_count"],
                                                   self._rd("active_context_count"))
            if self._rd("descriptor_valid"):
                self.acc["descriptor_valid"] = 1
            self.acc["ctx_state_sel"] = self._rd("ctx_state_sel")
            self.acc["ctx_key_sel"] = self._rd("ctx_key_sel")
            self.acc["ctx_payload_count_sel"] = max(self.acc["ctx_payload_count_sel"],
                                                    self._rd("ctx_payload_count_sel"))
            self.acc["ctx_expected_seq_sel"] = self._rd("ctx_expected_seq_sel")


async def send_packet(dut, pkt: Packet, *, monitor: DatapathMonitor,
                      awaddr: int = 0, cycles: int = 80,
                      force_wstrb: int | None = None) -> dict[str, Any]:
    """Drive one packet's TLP, let the datapath settle, return the snapshot."""
    monitor.clear()
    tlp = build_vdm_tlp(pkt)
    await axi_write_tlp(dut, tlp, awaddr=awaddr, force_wstrb=force_wstrb)
    await ClockCycles(dut.axi_aclk, cycles)
    obs = monitor.snapshot()
    obs["beats"] = max(1, (len(tlp) + AXI_BYTES - 1) // AXI_BYTES)
    obs["tlp_bytes"] = len(tlp)
    return obs


# ---------------------------------------------------------------------------
# AXI4 read BFM + SRAM model. The TB owns the external SRAM read port: it
# answers each sram_rd_req with sram_rd_rsp from `sram_mem`, and collects R
# beats. Used for the firmware payload read scenarios.
# ---------------------------------------------------------------------------
async def axi_read(dut, *, araddr: int, n_beats: int, sram_mem: bytearray,
                   arsize: int = 5, arburst: int = 1,
                   force_rsp_error: bool = False, max_cycles: int = 400,
                   debug: bool = False) -> dict[str, Any]:
    received = bytearray()
    rvalid_beats = 0
    rlast_seen: list[int] = []
    rresp_last = 0
    arready_seen = 0
    rd_reqs = 0

    await FallingEdge(dut.axi_aclk)
    dut.s_axi_araddr.value = araddr & 0xFFFF
    dut.s_axi_arlen.value = n_beats - 1
    dut.s_axi_arsize.value = arsize
    dut.s_axi_arburst.value = arburst
    dut.s_axi_arvalid.value = 1
    dut.s_axi_rready.value = 0   # held low; pulsed to consume a captured beat
    dut.sram_rd_req_ready.value = 1
    # arready is registered high in S_IDLE; sample it on this FallingEdge (the
    # cycle BEFORE the consummating RisingEdge) so we observe it before the FSM
    # accepts the AR and clears it. Mirrors the write-side ready handshake.
    if int(dut.s_axi_arready.value):
        arready_seen = 1

    # SRAM read model: when the DUT issues a request (sram_rd_req_valid &
    # sram_rd_req_ready), latch the addressed word and HOLD sram_rd_rsp_valid +
    # data asserted until the DUT consumes it (sram_rd_rsp_valid &
    # sram_rd_rsp_ready). Holding (rather than a 1-cycle pulse) tolerates the
    # FSM's ISSUE->WAIT latency, which a single-cycle response would race.
    rsp_held = False
    captured_last = False
    for _ in range(max_cycles):
        await RisingEdge(dut.axi_aclk)
        await ReadOnly()
        if int(dut.s_axi_arready.value):
            arready_seen = 1
        req_fire = int(dut.sram_rd_req_valid.value) and int(dut.sram_rd_req_ready.value)
        req_addr = int(dut.sram_rd_req_addr.value)
        # The FSM asserts sram_rd_rsp_ready the same cycle it ENTERS WAIT, then
        # consumes rsp on the first cycle rsp_valid is also high. Drop the held
        # response only once the FSM has actually advanced past WAIT (it stops
        # reading rsp there) — detected by s_axi_rvalid rising — so we never
        # retract rsp_valid in the one-cycle window before the FSM samples it.
        rsp_consumed = rsp_held and int(dut.s_axi_rvalid.value)
        if debug:
            _dbg = lambda n: int(getattr(dut, n).value) if hasattr(dut, n) else -1  # noqa: E731
            cocotb.log.info(
                "RDBG rd_st=%s arready=%d rvalid=%d rlast=%d rresp=%d "
                "req_v=%d rsp_v=%d rsp_rdy=%d"
                % (_dbg("axi_rd_state"), _dbg("s_axi_arready"), _dbg("s_axi_rvalid"),
                   _dbg("s_axi_rlast"), _dbg("s_axi_rresp"), _dbg("sram_rd_req_valid"),
                   _dbg("sram_rd_rsp_valid"), _dbg("sram_rd_rsp_ready")))
        await FallingEdge(dut.axi_aclk)
        # arready is registered: also catch it on the falling edge (the AR FSM
        # asserts arready in S_IDLE and clears it the cycle the AR is accepted).
        if int(dut.s_axi_arready.value):
            arready_seen = 1
            dut.s_axi_arvalid.value = 0
        if rsp_consumed:
            rsp_held = False
            dut.sram_rd_rsp_valid.value = 0
        if req_fire and not rsp_held:
            word = _word_from_bytes(bytes(sram_mem[req_addr:req_addr + AXI_BYTES]))
            dut.sram_rd_rsp_data.value = word
            dut.sram_rd_rsp_error.value = 1 if force_rsp_error else 0
            dut.sram_rd_rsp_valid.value = 1
            rsp_held = True
            rd_reqs += 1
        # Decoupled R capture: rready is held LOW so the FSM holds the R beat
        # (rvalid stable) until we explicitly accept it. Sample the held beat on
        # the FallingEdge, capture data, then pulse rready for exactly one rising
        # edge to consummate it. This avoids the registered-rvalid race that a
        # continuously-high rready would create.
        if int(dut.s_axi_rvalid.value):
            rvalid_beats += 1
            word = int(dut.s_axi_rdata.value).to_bytes(AXI_BYTES, "little")
            received.extend(word)
            this_last = int(dut.s_axi_rlast.value)
            rlast_seen.append(this_last)
            rresp_last = int(dut.s_axi_rresp.value)
            dut.s_axi_rready.value = 1          # accept this beat
            await RisingEdge(dut.axi_aclk)      # beat consummated here
            await FallingEdge(dut.axi_aclk)
            dut.s_axi_rready.value = 0
            if this_last:
                captured_last = True
                break
    _ = captured_last
    dut.sram_rd_rsp_valid.value = 0
    dut.s_axi_arvalid.value = 0
    return {
        "arready_seen": arready_seen,
        "rd_reqs": rd_reqs,
        "rvalid_beats": rvalid_beats,
        "rlast_count": sum(rlast_seen),
        "rlast_on_final": bool(rlast_seen and rlast_seen[-1] == 1 and sum(rlast_seen[:-1]) == 0),
        "rresp": rresp_last,
        "data": bytes(received),
    }


# ---------------------------------------------------------------------------
# Per-scenario sequence map. Each entry returns a list of Packets (and options)
# that lower the prose SSOT scenario into real stimulus. The driving test
# interprets `kind` to pick write/read/drop handling.
# ---------------------------------------------------------------------------
@dataclass
class Scenario:
    scenario_id: str
    goal_id: str
    kind: str                       # single|frag|interleave|drop|read|ctxfull|descfull
    packets: list[Packet] = field(default_factory=list)
    opts: dict[str, Any] = field(default_factory=dict)


def _payload(n: int, seed: int = 0) -> bytes:
    return bytes(((i * 7) + 3 + seed) & 0xFF for i in range(n))


def scenario_map() -> list[Scenario]:
    """The 20 SSOT scenarios lowered to byte-level stimulus.

    TU defaults to 64 bytes (BASELINE_MTU). Non-final fragments contribute
    exactly TU payload bytes; the EOM fragment may contribute fewer. payload
    bytes here are the bytes AFTER the SOM body byte; the parser's payload_bytes
    = (16 + 1 + len(payload)) - 16 - pad = 1 + len(payload). To make a fragment
    contribute exactly TU bytes the EOM/non-EOM payload length is chosen with
    that +1 in mind (the SOM body byte counts as a payload byte).
    """
    tu = 64
    scns: list[Scenario] = []

    # SC_SINGLE: one SOM+EOM packet -> alloc, single pack write, descriptor.
    scns.append(Scenario(
        "SC_SINGLE", "EQ_SCENARIO_SC_SINGLE", "single",
        [Packet(source_eid=0x20, message_tag=1, som=1, eom=1, packet_seq=0,
                payload=_payload(31))]))

    # SC_FRAG: two-packet message, same key, seq 0 then 1, EOM on the 2nd.
    scns.append(Scenario(
        "SC_FRAG", "EQ_SCENARIO_SC_FRAG", "frag",
        [Packet(source_eid=0x21, message_tag=2, som=1, eom=0, packet_seq=0, payload=_payload(tu - 1)),
         Packet(source_eid=0x21, message_tag=2, som=0, eom=1, packet_seq=1, payload=_payload(16, 5))]))

    # SC_INTERLEAVE: two distinct keys assembling concurrently.
    scns.append(Scenario(
        "SC_INTERLEAVE", "EQ_SCENARIO_SC_INTERLEAVE", "interleave",
        [Packet(source_eid=0x30, message_tag=1, som=1, eom=0, packet_seq=0, payload=_payload(tu - 1)),
         Packet(source_eid=0x31, message_tag=2, som=1, eom=0, packet_seq=0, payload=_payload(tu - 1, 9)),
         Packet(source_eid=0x30, message_tag=1, som=0, eom=1, packet_seq=1, payload=_payload(24)),
         Packet(source_eid=0x31, message_tag=2, som=0, eom=1, packet_seq=1, payload=_payload(24, 9))]))

    # SC_UNALIGNED_TU: single packet whose payload is not 32B-aligned ->
    # exercises the partial-word packer lane shift (no-hole packing).
    scns.append(Scenario(
        "SC_UNALIGNED_TU", "EQ_SCENARIO_SC_UNALIGNED_TU", "single",
        [Packet(source_eid=0x40, message_tag=3, som=1, eom=1, packet_seq=0, payload=_payload(18))]))

    # SC_PD_VDM: wrong vendor_id -> PD_UNSUPPORTED_VDM packet drop, no SRAM write.
    pd_vdm = Packet(source_eid=0x50, message_tag=1, som=1, eom=1, payload=_payload(31))
    scns.append(Scenario(
        "SC_PD_VDM", "EQ_SCENARIO_SC_PD_VDM", "drop",
        [pd_vdm], opts={"corrupt": "vendor", "drop_class": DC_PACKET, "drop_reason": PD_UNSUPPORTED_VDM}))

    # SC_PD_MIDDLE: SOM=0 packet with no active context -> PD_UNEXPECTED_MIDDLE_END.
    scns.append(Scenario(
        "SC_PD_MIDDLE", "EQ_SCENARIO_SC_PD_MIDDLE", "drop",
        [Packet(source_eid=0x51, message_tag=1, som=0, eom=0, packet_seq=1, payload=_payload(tu - 1))],
        opts={"drop_class": DC_PACKET, "drop_reason": PD_UNEXPECTED_MIDDLE_END}))

    # SC_AD_DUP: SOM for an already-active key -> AD_DUPLICATE_SOM assembly drop.
    scns.append(Scenario(
        "SC_AD_DUP", "EQ_SCENARIO_SC_AD_DUP", "assembly_drop",
        [Packet(source_eid=0x52, message_tag=1, som=1, eom=0, packet_seq=0, payload=_payload(tu - 1)),
         Packet(source_eid=0x52, message_tag=1, som=1, eom=0, packet_seq=0, payload=_payload(tu - 1))],
        opts={"drop_class": DC_ASM, "drop_reason": AD_DUPLICATE_SOM}))

    # SC_AD_SEQ: appended packet with wrong seq -> AD_SEQUENCE_MISMATCH.
    scns.append(Scenario(
        "SC_AD_SEQ", "EQ_SCENARIO_SC_AD_SEQ", "assembly_drop",
        [Packet(source_eid=0x53, message_tag=1, som=1, eom=0, packet_seq=0, payload=_payload(tu - 1)),
         Packet(source_eid=0x53, message_tag=1, som=0, eom=1, packet_seq=3, payload=_payload(16))],
        opts={"drop_class": DC_ASM, "drop_reason": AD_SEQUENCE_MISMATCH}))

    # SC_AD_CTXFULL: allocate all 15 contexts, then a 16th SOM -> table full
    # -> PD_BAD_OR_EXPIRED_TAG packet drop.
    ctxfull_pkts = [
        Packet(source_eid=0x60 + i, message_tag=1, som=1, eom=0, packet_seq=0, payload=_payload(tu - 1))
        for i in range(15)
    ]
    ctxfull_pkts.append(
        Packet(source_eid=0x80, message_tag=1, som=1, eom=0, packet_seq=0, payload=_payload(tu - 1)))
    scns.append(Scenario(
        "SC_AD_CTXFULL", "EQ_SCENARIO_SC_AD_CTXFULL", "ctxfull",
        ctxfull_pkts, opts={"drop_class": DC_PACKET, "drop_reason": PD_BAD_OR_EXPIRED_TAG}))

    # SC_AD_SRAM: tight SRAM window so the bump allocator overflows on the
    # first allocation -> AD_SRAM_OVERFLOW.
    scns.append(Scenario(
        "SC_AD_SRAM", "EQ_SCENARIO_SC_AD_SRAM", "sram_overflow",
        [Packet(source_eid=0x55, message_tag=1, som=1, eom=0, packet_seq=0, payload=_payload(tu - 1))],
        opts={"sram_limit": 0x20, "drop_class": DC_ASM, "drop_reason": AD_SRAM_OVERFLOW}))

    # SC_AD_DESCFULL: fill the 8-deep descriptor FIFO with single packets, then
    # a 9th completion -> AD_DESCRIPTOR_FULL.
    descfull_pkts = [
        Packet(source_eid=0x70 + i, message_tag=1, som=1, eom=1, packet_seq=0, payload=_payload(15))
        for i in range(9)
    ]
    scns.append(Scenario(
        "SC_AD_DESCFULL", "EQ_SCENARIO_SC_AD_DESCFULL", "descfull",
        descfull_pkts, opts={"drop_class": DC_ASM, "drop_reason": AD_DESCRIPTOR_FULL}))

    # SC_AD_TIMEOUT: small timeout; allocate then idle past it, append -> AD_TIMEOUT.
    scns.append(Scenario(
        "SC_AD_TIMEOUT", "EQ_SCENARIO_SC_AD_TIMEOUT", "timeout",
        [Packet(source_eid=0x56, message_tag=1, som=1, eom=0, packet_seq=0, payload=_payload(tu - 1)),
         Packet(source_eid=0x56, message_tag=1, som=0, eom=1, packet_seq=1, payload=_payload(16))],
        opts={"timeout_cycles": 8, "idle_cycles": 60, "drop_class": DC_ASM, "drop_reason": AD_TIMEOUT}))

    # SC_FW_READ: assemble a single packet, then read its payload back OKAY.
    scns.append(Scenario(
        "SC_FW_READ", "EQ_SCENARIO_SC_FW_READ", "read",
        [Packet(source_eid=0x57, message_tag=1, som=1, eom=1, packet_seq=0, payload=_payload(31))],
        opts={"read_beats": 2, "expect_slverr": False}))

    # SC_FW_READ_SLVERR: read with no descriptor / out of window -> SLVERR.
    scns.append(Scenario(
        "SC_FW_READ_SLVERR", "EQ_SCENARIO_SC_FW_READ_SLVERR", "read_slverr",
        [], opts={"read_beats": 1, "expect_slverr": True, "araddr": 0x1000}))

    return scns
