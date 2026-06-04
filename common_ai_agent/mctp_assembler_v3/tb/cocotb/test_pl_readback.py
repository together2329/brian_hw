"""Write→readback FULL-CONTENT oracle for mctp_assembler_v3 (PAYLOAD_STREAM §7).

The FL/goal scoreboard only ever proved the *count* of assembled payload bytes
(`ctx_payload_count_sel >= N`) and that a SRAM write *happened* — never that the
real payload BYTES landed in SRAM with no holes. Pre-fix, the parser forwarded
exactly one 256-bit beat per TLP, so any payload >32 B left SRAM mostly zero
while the logical count still read 64..4096. A count-only scoreboard cannot see
that bug. This test is the content-level oracle that closes the gap.

For each case it:
  1. drives a known MCTP payload as a real VDM-TLP AXI write burst, letting the
     DUT's REAL multi-beat pack engine write SRAM (captured into `sram_mem` by
     the existing DatapathMonitor SRAM model),
  2. reads the payload back through the DUT's own AXI read path (`axi_read`),
  3. compares the FULL readback bytes to a golden vector built the §7 way:
         golden = concat over the message's packets of
                  build_vdm_tlp(pkt)[16 : 16 + expected_payload_bytes(pkt)]
     and asserts byte-exact match + rresp==OKAY + exactly one rlast,
  4. asserts the sram_packer ≤32 B/word invariant never tripped
     (`u_sram_packer.pack_bytes_overflow` sticky flag stays 0).

Four cases (PAYLOAD_STREAM_CONTRACT.md §7.3):
  * SC_RB_SINGLE  — ≤32 B single write (the ≤32-B regression / equivalence guard)
  * SC_RB_64      — 64 B / 2 payload-bearing beats
  * SC_RB_FRAG    — ≥2 fragments, non-32-aligned tail (no-hole ACROSS a fragment
                    boundary)
  * SC_RB_4096    — full 4096 B / 128 words: the real multi-beat proof

TB-ONLY. No assertion here is weakened: the bytes MUST match exactly. A byte
mismatch is a real RTL bug, surfaced with the exact offset, not masked.

Address mapping (§7.1): sram_base=0, a fresh context after reset allocates
ctx_payload_base = sram_alloc_ptr = sram_base = 0, so message byte i lands at
sram_mem[i] and is read back from araddr=0. Each case resets first so its base
is a clean 0.
"""

from __future__ import annotations

from math import ceil

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, with_timeout

import mctp_stimulus as S


# Base address of the first context allocated after reset. sram_base is
# configured to 0 below, and the bump allocator hands the first fresh context
# ctx_payload_base = sram_alloc_ptr = sram_base (§7.1).
RB_BASE = 0


async def _setup(dut):
    cocotb.start_soon(Clock(dut.axi_aclk, 10, units="ns").start())
    cocotb.start_soon(Clock(dut.pclk, 10, units="ns").start())
    await S.reset_dut(dut)


def _golden(packets: list[S.Packet]) -> bytes:
    """§7.2 golden: each packet's message-payload bytes = TLP[16 : 16+plen],
    concatenated in arrival order (no-hole, byte i of the message at base+i)."""
    out = bytearray()
    for pkt in packets:
        tlp = S.build_vdm_tlp(pkt)
        plen = S.expected_payload_bytes(pkt)
        out += tlp[16:16 + plen]
    return bytes(out)


def _packer_overflow(dut) -> int:
    """Read the sram_packer ≤32-B/word sticky overflow flag.

    `pack_bytes_overflow` is an internal sticky reg in the sram_packer instance
    (`u_sram_packer`), set if any pack-write ever requested >32 bytes — which the
    multi-beat engine must never do (§4.3 ≤32 B invariant). Reachable in Icarus
    via the hierarchical handle. If for some reason it is not visible, fail loud
    rather than silently skip the invariant check.
    """
    try:
        return int(dut.u_sram_packer.pack_bytes_overflow.value)
    except (AttributeError, ValueError) as exc:  # pragma: no cover - env guard
        raise AssertionError(
            "cannot read u_sram_packer.pack_bytes_overflow (the ≤32B-per-word "
            f"invariant sentinel): {exc}"
        )


async def _drive_and_readback(dut, monitor, sram, packets, *, tu_bytes,
                              max_cycles=600, send_cycles=120):
    """Drive every packet of one message, then read the whole payload back and
    return (golden, rd). Caller asserts the byte-exact compare + rresp + rlast.
    """
    await S.reset_dut(dut)
    sram[:] = bytearray(len(sram))           # clear any prior message's bytes
    monitor.clear()
    await with_timeout(
        S.configure(dut, enable=1, tu_bytes=tu_bytes, max_message_bytes=4096,
                    sram_base=RB_BASE, sram_limit=0xFFFF,
                    timeout_cycles=0xFFFFFF),
        80, "us")

    # Drive each fragment in arrival order. The last packet (EOM) completes the
    # message and publishes the descriptor.
    last_obs = None
    for i, pkt in enumerate(packets):
        # Give the final (EOM) packet extra settle cycles so the full multi-beat
        # pack engine drains every beat before we read back.
        cyc = send_cycles if i == len(packets) - 1 else max(40, send_cycles // 2)
        last_obs = await with_timeout(
            S.send_packet(dut, pkt, monitor=monitor, cycles=cyc), 100, "us")

    assert last_obs is not None
    assert last_obs["descriptor_valid"] == 1, (
        f"no descriptor published after assembly — cannot read back: {last_obs}")
    assert _packer_overflow(dut) == 0, (
        "sram_packer pack_bytes_overflow fired during assembly: a pack-write "
        "requested >32 B (≤32-B-per-word invariant violated)")

    golden = _golden(packets)
    n_beats = ceil(len(golden) / S.AXI_BYTES)
    rd = await with_timeout(
        S.axi_read(dut, araddr=RB_BASE, n_beats=n_beats, sram_mem=sram,
                   max_cycles=max_cycles),
        200, "us")
    return golden, rd, n_beats


def _assert_byte_exact(dut, scenario, golden, rd, n_beats):
    """Byte-exact readback compare + rresp OKAY + exactly one rlast. On a byte
    mismatch, report the FIRST differing offset (this is the real-RTL-bug
    signal — never weaken the compare to make it pass)."""
    data = rd["data"]
    assert len(data) >= len(golden), (
        f"{scenario}: readback returned {len(data)} B, expected >= {len(golden)} "
        f"(rvalid_beats={rd['rvalid_beats']}, n_beats={n_beats}): {rd}")

    got = data[:len(golden)]
    if got != golden:
        # Locate the exact byte/offset mismatch for the bug report.
        first = next(i for i in range(len(golden)) if got[i] != golden[i])
        ctx = 8
        lo = max(0, first - ctx)
        raise AssertionError(
            f"{scenario}: READBACK BYTE MISMATCH at offset {first} "
            f"(of {len(golden)} payload bytes). "
            f"golden[{lo}:{first + ctx}]={golden[lo:first + ctx].hex()} "
            f"got[{lo}:{first + ctx}]={got[lo:first + ctx].hex()}. "
            f"This is a real assembly/pack/readback bug — bytes must match exactly.")

    assert rd["rresp"] == 0, f"{scenario}: rresp != OKAY (got {rd['rresp']}): {rd}"
    assert rd["rlast_count"] == 1, (
        f"{scenario}: expected exactly one rlast, got {rd['rlast_count']}: {rd}")
    assert rd["rlast_on_final"], (
        f"{scenario}: rlast not on the final beat: {rd}")
    assert _packer_overflow(dut) == 0, (
        f"{scenario}: pack_bytes_overflow set after readback")
    cocotb.log.info(
        f"{scenario}: BYTE-EXACT readback of {len(golden)} payload bytes "
        f"over {n_beats} beat(s) — OK (rresp=OKAY, 1 rlast).")


# ===========================================================================
# SC_RB_SINGLE — ≤32 B single write (regression / ≤32-B equivalence guard, §6).
# _payload(31) + SOM body byte = 32 message bytes. Readback one 32-B beat.
# ===========================================================================
@cocotb.test()
async def sc_rb_single(dut):
    await _setup(dut)
    sram = bytearray(0x10000)
    monitor = S.DatapathMonitor(dut, sram_mem=sram)
    cocotb.start_soon(monitor.run())

    pkts = [S.Packet(source_eid=0x20, message_tag=1, som=1, eom=1, packet_seq=0,
                     payload=S._payload(31))]
    golden, rd, n_beats = await _drive_and_readback(
        dut, monitor, sram, pkts, tu_bytes=64)
    assert len(golden) == 32, f"SC_RB_SINGLE expected 32 payload bytes, got {len(golden)}"
    _assert_byte_exact(dut, "SC_RB_SINGLE", golden, rd, n_beats)


# ===========================================================================
# SC_RB_64 — 64 B single packet, 2 payload-bearing beats. _payload(63) + SOM
# body byte = 64 message bytes; TLP = 16+64 = 80 B = 3 AXI write beats. Pre-fix
# this readback FAILS (bytes 32..63 are zero); post-fix it must be byte-exact.
# ===========================================================================
@cocotb.test()
async def sc_rb_64(dut):
    await _setup(dut)
    sram = bytearray(0x10000)
    monitor = S.DatapathMonitor(dut, sram_mem=sram)
    cocotb.start_soon(monitor.run())

    pkts = [S.Packet(source_eid=0x21, message_tag=1, som=1, eom=1, packet_seq=0,
                     payload=S._payload(63))]
    golden, rd, n_beats = await _drive_and_readback(
        dut, monitor, sram, pkts, tu_bytes=4096)
    assert len(golden) == 64, f"SC_RB_64 expected 64 payload bytes, got {len(golden)}"
    assert n_beats == 2, f"SC_RB_64 expected 2 readback beats, got {n_beats}"
    _assert_byte_exact(dut, "SC_RB_64", golden, rd, n_beats)


# ===========================================================================
# SC_RB_FRAG — two fragments, non-32-aligned tail: proves no-hole packing ACROSS
# a fragment boundary. SOM frag payload_len = 41 (ends at lane 41%32 = 9); EOM
# frag payload_len = 23; total 64 B. The EOM fragment's first byte MUST land at
# base+41 (lane 9 of word 1) with no hole — only a byte-exact compare proves it.
# ===========================================================================
@cocotb.test()
async def sc_rb_frag(dut):
    await _setup(dut)
    sram = bytearray(0x10000)
    monitor = S.DatapathMonitor(dut, sram_mem=sram)
    cocotb.start_soon(monitor.run())

    # SOM: _payload(40) -> payload_len = 1+40 = 41 (tail lane 9).
    # EOM: _payload(22, seed=5) -> payload_len = 1+22 = 23. Total 64 B.
    f0 = S.Packet(source_eid=0x22, message_tag=2, som=1, eom=0, packet_seq=0,
                  payload=S._payload(40))
    f1 = S.Packet(source_eid=0x22, message_tag=2, som=0, eom=1, packet_seq=1,
                  payload=S._payload(22, 5))
    pkts = [f0, f1]
    # tu_bytes large enough that each fragment's payload is accepted (the parser
    # checks payload <= TU per fragment): 41 and 23 both <= 64.
    golden, rd, n_beats = await _drive_and_readback(
        dut, monitor, sram, pkts, tu_bytes=64)
    assert len(golden) == 64, f"SC_RB_FRAG expected 64 payload bytes, got {len(golden)}"
    # Explicit boundary witness: byte 41 of the message is the EOM fragment's
    # first payload byte; it must read back as the EOM SOM-body byte, not zero.
    eom_first = S.build_vdm_tlp(f1)[16]
    assert golden[41] == eom_first, "golden self-check: byte 41 != EOM body byte"
    _assert_byte_exact(dut, "SC_RB_FRAG", golden, rd, n_beats)
    # Direct no-hole-across-boundary assertion on the readback bytes.
    assert rd["data"][41] == eom_first, (
        f"SC_RB_FRAG: hole across fragment boundary — byte 41 read back "
        f"{rd['data'][41]:#04x}, expected EOM first payload byte {eom_first:#04x}")


# ===========================================================================
# SC_RB_4096 — full 4096 B / 128 words: the real multi-beat proof. _payload(4095)
# + SOM body byte = 4096 message bytes in one max-size TLP. Read 128 beats from
# base=0 and assert all 4096 bytes match. The count-only scoreboard could only
# ever check ctx_payload_count_sel >= 4096; THIS proves the actual bytes.
# ===========================================================================
@cocotb.test()
async def sc_rb_4096(dut):
    await _setup(dut)
    sram = bytearray(0x10000)
    monitor = S.DatapathMonitor(dut, sram_mem=sram)
    cocotb.start_soon(monitor.run())

    pkts = [S.Packet(source_eid=0x48, message_tag=1, som=1, eom=1, packet_seq=0,
                     payload=S._payload(4095))]
    # The 128-beat readback needs many cycles (each beat is a SRAM round-trip);
    # give axi_read a generous budget and the write a long settle.
    golden, rd, n_beats = await _drive_and_readback(
        dut, monitor, sram, pkts, tu_bytes=4096,
        max_cycles=4000, send_cycles=600)
    assert len(golden) == 4096, f"SC_RB_4096 expected 4096 payload bytes, got {len(golden)}"
    assert n_beats == 128, f"SC_RB_4096 expected 128 readback beats, got {n_beats}"
    _assert_byte_exact(dut, "SC_RB_4096", golden, rd, n_beats)
