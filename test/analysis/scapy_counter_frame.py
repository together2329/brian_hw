#!/usr/bin/env python3
"""
scapy Counter Frame — Encapsulation / Decapsulation Test
========================================================
Serializes counter module state (count_out, overflow, up_down, en, load, data_in)
into a structured binary payload, encapsulates it within Ether/IP/UDP frames,
then decapsulates and parses it back for verification.

Frame Structure:
  ┌──────────┬──────────┬──────────┬──────────────────────────────────┐
  │ Ethernet │   IPv4   │   UDP    │  Counter Payload (structured)   │
  │  14 B    │  20 B    │   8 B    │  8 B (fixed)                    │
  └──────────┴──────────┴──────────┴──────────────────────────────────┘

Counter Payload Format (9 bytes, big-endian):
  ┌───────────┬───────────┬──────┬────────┬────────┬──────┬───────┐
  │ count_out │  data_in  | flags|   rsv  │ width  |magic │  CRC  │
  │  2 bytes  │  2 bytes  │1 byte│ 1 byte │1 byte  │1 byte│ 1 byte│
  └───────────┴───────────┴──────┴────────┴────────┴──────┴───────┘
  flags[7:4] = overflow
  flags[3]   = up_down
  flags[2]   = en
  flags[1]   = load
  flags[0]   = reserved
  magic = 0xA5 (frame integrity marker)
  CRC   = XOR of all preceding bytes (simple integrity check)

Test Categories:
  1. Encapsulation:    CounterState → Ether/IP/UDP/payload frame
  2. Decapsulation:    Raw frame bytes → parsed CounterState
  3. Round-trip:       encapsulate → serialize → parse → decapsulate → compare
  4. Integrity:        CRC validation detects bit-flips in payload
  5. Frame structure:  Verify Ethernet/IP/UDP header correctness
  6. Multi-state:      Array of counter states all pass round-trip

Usage:
    python3 analysis/scapy_counter_frame.py [--json] [--markdown]
"""

import sys
import os
import json
import struct
import argparse
import random
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Tuple, Optional

# ── Paths ──────────────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

try:
    from scapy.all import Ether, IP, UDP, Raw, checksum, bytes_hex, mac2str
except ImportError:
    print("ERROR: scapy not installed.  Run: pip3 install scapy")
    sys.exit(1)


# ======================================================================
# Constants
# ======================================================================

MAGIC_BYTE    = 0xA5        # Frame integrity marker
PAYLOAD_HDR   = ">HHBBB"    # count_out(2) data_in(2) flags(1) rsv(1) width(1) = 7 bytes
PAYLOAD_SIZE  = struct.calcsize(PAYLOAD_HDR) + 2  # 7 + magic(1) + crc(1) = 9 bytes
SRC_MAC       = "00:aa:bb:cc:dd:01"
DST_MAC       = "00:aa:bb:cc:dd:02"
SRC_IP        = "192.168.1.10"
DST_IP        = "192.168.1.20"
UDP_SPORT     = 0xC0DE      # 49374
UDP_DPORT     = 0xBA5E      # 47710


# ======================================================================
# Counter State
# ======================================================================

@dataclass
class CounterState:
    """Snapshot of counter module's input/output signals."""
    count_out: int   # [WIDTH-1:0] counter output value
    overflow:  int   # 1-bit overflow flag
    up_down:   int   # 1-bit direction control
    en:        int   # 1-bit enable
    load:      int   # 1-bit load control
    data_in:   int   # [WIDTH-1:0] load data input
    width:     int   # Parameter WIDTH (8 or 16)

    def validate(self) -> List[str]:
        """Validate signal ranges. Returns list of error strings."""
        errors = []
        max_val = (1 << self.width) - 1
        if not (0 <= self.count_out <= max_val):
            errors.append(f"count_out={self.count_out} out of range [0, {max_val}]")
        if not (0 <= self.data_in <= max_val):
            errors.append(f"data_in={self.data_in} out of range [0, {max_val}]")
        if self.overflow not in (0, 1):
            errors.append(f"overflow={self.overflow} not 0/1")
        if self.up_down not in (0, 1):
            errors.append(f"up_down={self.up_down} not 0/1")
        if self.en not in (0, 1):
            errors.append(f"en={self.en} not 0/1")
        if self.load not in (0, 1):
            errors.append(f"load={self.load} not 0/1")
        return errors


# ======================================================================
# Payload Encoder / Decoder
# ======================================================================

def _pack_flags(state: CounterState) -> int:
    """Pack single-bit flags into one byte."""
    return (
        ((state.overflow & 0x1) << 4) |
        ((state.up_down  & 0x1) << 3) |
        ((state.en       & 0x1) << 2) |
        ((state.load     & 0x1) << 1)
    )


def _unpack_flags(flags_byte: int) -> Tuple[int, int, int, int]:
    """Unpack byte → (overflow, up_down, en, load)."""
    return (
        (flags_byte >> 4) & 0x1,
        (flags_byte >> 3) & 0x1,
        (flags_byte >> 2) & 0x1,
        (flags_byte >> 1) & 0x1,
    )


def _compute_crc(payload_bytes: bytes) -> int:
    """XOR all bytes → single-byte CRC."""
    crc = 0
    for b in payload_bytes:
        crc ^= b
    return crc & 0xFF


def encode_payload(state: CounterState) -> bytes:
    """Serialize CounterState into structured payload."""
    errs = state.validate()
    if errs:
        raise ValueError(f"Invalid CounterState: {errs}")

    flags = _pack_flags(state)
    # Pack structured header (7 bytes)
    header = struct.pack(
        PAYLOAD_HDR,
        state.count_out & 0xFFFF,
        state.data_in   & 0xFFFF,
        flags,
        0,                  # reserved byte
        state.width,
    )
    # Append magic + CRC
    pre_crc = header + bytes([MAGIC_BYTE])
    crc = _compute_crc(pre_crc)
    return pre_crc + bytes([crc])


def decode_payload(raw: bytes) -> Tuple[Optional[CounterState], List[str]]:
    """Deserialize payload back into CounterState.
    
    Layout: [count_out:2B][data_in:2B][flags:1B][rsv:1B][width:1B][magic:1B][crc:1B] = 9B
    
    Returns (CounterState or None, list of warning strings).
    """
    warnings = []
    if len(raw) < PAYLOAD_SIZE:
        return None, [f"Payload too short: {len(raw)} < {PAYLOAD_SIZE}"]

    # Check CRC (XOR of all bytes before last)
    pre_crc = raw[:PAYLOAD_SIZE - 1]
    expected_crc = raw[PAYLOAD_SIZE - 1]
    computed_crc = _compute_crc(pre_crc)
    if computed_crc != expected_crc:
        return None, [f"CRC mismatch: expected=0x{expected_crc:02x}, "
                      f"computed=0x{computed_crc:02x}"]

    # Check magic byte (at offset 7)
    magic = raw[7]
    if magic != MAGIC_BYTE:
        return None, [f"Magic byte wrong: 0x{magic:02x} != 0x{MAGIC_BYTE:02x}"]

    # Unpack header (first 5 fields, 7 bytes)
    count_out, data_in, flags, rsv, width = struct.unpack(PAYLOAD_HDR, raw[:7])

    overflow, up_down, en, load = _unpack_flags(flags)

    state = CounterState(
        count_out=count_out,
        overflow=overflow,
        up_down=up_down,
        en=en,
        load=load,
        data_in=data_in,
        width=width if width in (8, 16) else 8,
    )

    validate_errs = state.validate()
    if validate_errs:
        warnings.extend(validate_errs)

    return state, warnings


# ======================================================================
# Frame Encapsulation / Decapsulation
# ======================================================================

def encapsulate(state: CounterState) -> bytes:
    """Encapsulate CounterState into complete Ether/IP/UDP frame.

    Returns raw bytes of the complete frame.
    """
    payload = encode_payload(state)

    frame = (
        Ether(src=SRC_MAC, dst=DST_MAC) /
        IP(version=4, src=SRC_IP, dst=DST_IP, proto=17, ttl=64) /
        UDP(sport=UDP_SPORT, dport=UDP_DPORT) /
        Raw(load=payload)
    )
    return bytes(frame)


def decapsulate(frame_bytes: bytes) -> Tuple[Optional[CounterState], dict, List[str]]:
    """Decapsulate raw frame bytes → CounterState + frame metadata.

    Returns (CounterState or None, metadata dict, list of warnings).
    """
    warnings = []
    meta = {}

    # Parse outer layers
    pkt = Ether(frame_bytes)

    # --- Ethernet layer ---
    if not pkt.haslayer(Ether):
        return None, meta, ["No Ethernet layer found"]
    meta["eth_src"]   = pkt[Ether].src
    meta["eth_dst"]   = pkt[Ether].dst
    meta["eth_type"]  = pkt[Ether].type

    # --- IP layer ---
    if not pkt.haslayer(IP):
        return None, meta, ["No IP layer found"]
    meta["ip_src"]    = pkt[IP].src
    meta["ip_dst"]    = pkt[IP].dst
    meta["ip_ttl"]    = int(pkt[IP].ttl)
    meta["ip_proto"]  = int(pkt[IP].proto)
    meta["ip_id"]     = int(pkt[IP].id)

    # Verify IP header checksum
    ip_raw = bytes(pkt[IP])
    ip_hdr_bytes = ip_raw[:20]
    stored_cksum = (ip_hdr_bytes[10] << 8) | ip_hdr_bytes[11]
    zeroed = bytearray(ip_hdr_bytes)
    zeroed[10] = 0
    zeroed[11] = 0
    computed_cksum = checksum(bytes(zeroed))
    meta["ip_checksum_valid"] = (stored_cksum == computed_cksum)
    if not meta["ip_checksum_valid"]:
        warnings.append(f"IP checksum invalid: stored=0x{stored_cksum:04x}, "
                        f"computed=0x{computed_cksum:04x}")

    # --- UDP layer ---
    if pkt.haslayer(UDP):
        meta["udp_sport"] = int(pkt[UDP].sport)
        meta["udp_dport"] = int(pkt[UDP].dport)
        raw_payload = bytes(pkt[Raw].load) if pkt.haslayer(Raw) else b""
    elif pkt.haslayer(Raw):
        # scapy may not parse UDP on re-import; skip 8-byte UDP header
        udp_and_payload = bytes(pkt[Raw].load)
        if len(udp_and_payload) >= 8:
            meta["udp_sport"] = struct.unpack("!H", udp_and_payload[0:2])[0]
            meta["udp_dport"] = struct.unpack("!H", udp_and_payload[2:4])[0]
            raw_payload = udp_and_payload[8:]
        else:
            return None, meta, ["Frame too short — no UDP/payload data"]
    else:
        return None, meta, ["No UDP or Raw layer found"]

    # --- Counter payload ---
    state, payload_warnings = decode_payload(raw_payload)
    warnings.extend(payload_warnings)
    meta["payload_size"] = len(raw_payload)

    return state, meta, warnings


# ======================================================================
# Test Suite
# ======================================================================

def generate_test_states(width: int = 8) -> List[CounterState]:
    """Generate comprehensive counter states for testing."""
    max_val = (1 << width) - 1
    states = []

    # Named states
    named = [
        ("Reset",         CounterState(0, 0, 0, 0, 0, 0, width)),
        ("Count up mid",  CounterState(42, 0, 0, 1, 0, 0, width)),
        ("Count up max",  CounterState(max_val, 0, 0, 1, 0, 0, width)),
        ("Overflow",      CounterState(0, 1, 0, 1, 0, 0, width)),
        ("Count down",    CounterState(100, 0, 1, 1, 0, 0, width)),
        ("Underflow",     CounterState(max_val, 1, 1, 1, 0, 0, width)),
        ("Load 0x5A",     CounterState(0, 0, 0, 0, 1, 0x5A, width)),
        ("Disabled hold", CounterState(77, 0, 0, 0, 0, 0, width)),
        ("All flags max", CounterState(max_val, 1, 1, 1, 1, max_val, width)),
        ("Load 0xFF",     CounterState(200, 0, 0, 0, 1, 0xFF, width)),
    ]
    for name, s in named:
        states.append(s)

    # Random states
    random.seed(0xCAFE)
    for _ in range(5):
        states.append(CounterState(
            count_out=random.randint(0, max_val),
            overflow=random.randint(0, 1),
            up_down=random.randint(0, 1),
            en=random.randint(0, 1),
            load=random.randint(0, 1),
            data_in=random.randint(0, max_val),
            width=width,
        ))

    return states


def run_all_tests(width: int = 8) -> dict:
    """Run the full encapsulation/decapsulation test suite."""
    states = generate_test_states(width)

    # ── Test 1: Payload round-trip (encode → decode) ──
    print("\n[TEST 1] Payload serialization round-trip")
    payload_results = []
    payload_pass = payload_fail = 0
    for i, state in enumerate(states):
        raw = encode_payload(state)
        decoded, warns = decode_payload(raw)
        passed = (decoded is not None and len(warns) == 0 and
                  asdict(state) == asdict(decoded))
        payload_results.append({
            "test_index": i,
            "passed": passed,
            "original": asdict(state),
            "decoded": asdict(decoded) if decoded else None,
            "warnings": warns,
            "raw_hex": raw.hex(),
        })
        if passed:
            payload_pass += 1
            print(f"  ✅ State #{i}: PASS ({len(raw)}B payload)")
        else:
            payload_fail += 1
            print(f"  ❌ State #{i}: FAIL — warns={warns}")

    # ── Test 2: Frame encapsulation → decapsulation ──
    print("\n[TEST 2] Ether/IP/UDP frame encapsulation → decapsulation")
    frame_results = []
    frame_pass = frame_fail = 0
    for i, state in enumerate(states):
        frame_bytes = encapsulate(state)
        decoded_state, meta, warns = decapsulate(frame_bytes)

        field_match = (decoded_state is not None and
                       asdict(state) == asdict(decoded_state))
        ip_ck_ok = meta.get("ip_checksum_valid", False)
        passed = field_match and ip_ck_ok and len(warns) == 0

        frame_results.append({
            "test_index": i,
            "passed": passed,
            "original": asdict(state),
            "decoded": asdict(decoded_state) if decoded_state else None,
            "frame_size": len(frame_bytes),
            "meta": {k: v for k, v in meta.items()
                     if k not in ("ip_checksum_valid",)},
            "ip_checksum_valid": ip_ck_ok,
            "warnings": warns,
        })
        if passed:
            frame_pass += 1
            print(f"  ✅ State #{i}: PASS (frame={len(frame_bytes)}B, "
                  f"IP cksum OK)")
        else:
            frame_fail += 1
            reasons = []
            if not field_match:
                reasons.append("field mismatch")
            if not ip_ck_ok:
                reasons.append("IP checksum bad")
            reasons.extend(warns)
            print(f"  ❌ State #{i}: FAIL — {reasons}")

    # ── Test 3: Frame structure validation ──
    print("\n[TEST 3] Frame structure verification")
    struct_results = []
    struct_pass = struct_fail = 0
    sample_state = states[0]
    frame_bytes = encapsulate(sample_state)
    pkt = Ether(frame_bytes)

    checks = {
        "has_ether":    pkt.haslayer(Ether),
        "has_ip":       pkt.haslayer(IP),
        "has_udp":      pkt.haslayer(UDP),
        "has_raw":      pkt.haslayer(Raw),
        "eth_type_ipv4": (pkt[Ether].type == 0x0800 if pkt.haslayer(Ether) else False),
        "ip_version":   (int(pkt[IP].version) == 4 if pkt.haslayer(IP) else False),
        "ip_proto_udp": (int(pkt[IP].proto) == 17 if pkt.haslayer(IP) else False),
        "eth_src_mac":  (pkt[Ether].src == SRC_MAC if pkt.haslayer(Ether) else False),
        "eth_dst_mac":  (pkt[Ether].dst == DST_MAC if pkt.haslayer(Ether) else False),
        "ip_src":       (pkt[IP].src == SRC_IP if pkt.haslayer(IP) else False),
        "ip_dst":       (pkt[IP].dst == DST_IP if pkt.haslayer(IP) else False),
    }

    all_ok = all(checks.values())
    struct_results.append({
        "test_index": 0,
        "passed": all_ok,
        "checks": checks,
        "frame_size": len(frame_bytes),
    })
    if all_ok:
        struct_pass += 1
        print(f"  ✅ Frame structure: All 11 checks PASS")
    else:
        struct_fail += 1
        failed = [k for k, v in checks.items() if not v]
        print(f"  ❌ Frame structure: Failed checks: {failed}")

    # ── Test 4: CRC integrity / tamper detection ──
    print("\n[TEST 4] CRC integrity check (tamper detection)")
    crc_results = []
    crc_pass = crc_fail = 0
    for i, state in enumerate(states[:5]):
        payload = bytearray(encode_payload(state))
        # Flip a bit in each of several payload positions
        for flip_pos in [0, 2, 4, 6]:
            tampered = bytearray(payload)
            tampered[flip_pos] ^= 0x01  # flip LSB
            decoded, warns = decode_payload(bytes(tampered))
            # CRC should detect the tampering
            detected = (decoded is None and
                        any("CRC mismatch" in w for w in warns))
            passed = detected
            crc_results.append({
                "test_index": i,
                "flip_pos": flip_pos,
                "passed": passed,
                "original_byte": payload[flip_pos],
                "tampered_byte": tampered[flip_pos],
            })
            if passed:
                crc_pass += 1
                print(f"  ✅ State #{i} flip@{flip_pos}: CRC mismatch detected "
                      f"(0x{payload[flip_pos]:02x}→0x{tampered[flip_pos]:02x})")
            else:
                crc_fail += 1
                print(f"  ❌ State #{i} flip@{flip_pos}: CRC FAILED to detect tamper")

    # ── Test 5: Boundary values ──
    print("\n[TEST 5] Boundary value round-trip")
    boundary_states = [
        CounterState(0, 0, 0, 0, 0, 0, width),
        CounterState((1 << width) - 1, 1, 1, 1, 1, (1 << width) - 1, width),
        CounterState(1, 0, 0, 1, 0, 1, width),
        CounterState((1 << width) - 2, 0, 0, 1, 0, (1 << width) - 2, width),
    ]
    boundary_results = []
    boundary_pass = boundary_fail = 0
    for i, state in enumerate(boundary_states):
        frame_bytes = encapsulate(state)
        decoded, meta, warns = decapsulate(frame_bytes)
        passed = (decoded is not None and
                  asdict(state) == asdict(decoded) and
                  len(warns) == 0)
        boundary_results.append({
            "test_index": i,
            "passed": passed,
            "count_out": state.count_out,
            "data_in": state.data_in,
        })
        if passed:
            boundary_pass += 1
            print(f"  ✅ Boundary #{i}: PASS (count_out={state.count_out}, "
                  f"data_in={state.data_in})")
        else:
            boundary_fail += 1
            print(f"  ❌ Boundary #{i}: FAIL")

    # ── Test 6: WIDTH=16 extended range ──
    print("\n[TEST 6] WIDTH=16 extended range")
    w16_states = [
        CounterState(0x0000, 0, 0, 0, 0, 0x0000, 16),
        CounterState(0xFFFF, 1, 1, 1, 1, 0xFFFF, 16),
        CounterState(0x1234, 0, 1, 1, 0, 0xABCD, 16),
        CounterState(0x00FF, 1, 0, 0, 1, 0x0F0F, 16),
    ]
    w16_results = []
    w16_pass = w16_fail = 0
    for i, state in enumerate(w16_states):
        errs = state.validate()
        if errs:
            print(f"  ⚠️  W16 #{i}: validation errors: {errs}")
            w16_fail += 1
            continue
        frame_bytes = encapsulate(state)
        decoded, meta, warns = decapsulate(frame_bytes)
        passed = (decoded is not None and
                  asdict(state) == asdict(decoded) and
                  len(warns) == 0)
        w16_results.append({
            "test_index": i,
            "passed": passed,
            "count_out": state.count_out,
            "data_in": state.data_in,
        })
        if passed:
            w16_pass += 1
            print(f"  ✅ W16 #{i}: PASS (count_out=0x{state.count_out:04x}, "
                  f"data_in=0x{state.data_in:04x})")
        else:
            w16_fail += 1
            print(f"  ❌ W16 #{i}: FAIL (decoded={decoded})")

    # ── Summary ──
    total_tests = (payload_pass + payload_fail + frame_pass + frame_fail +
                   struct_pass + struct_fail + crc_pass + crc_fail +
                   boundary_pass + boundary_fail + w16_pass + w16_fail)
    total_passed = (payload_pass + frame_pass + struct_pass +
                    crc_pass + boundary_pass + w16_pass)
    total_failed = (payload_fail + frame_fail + struct_fail +
                    crc_fail + boundary_fail + w16_fail)

    summary = {
        "width": width,
        "total_test_states": len(states),
        "payload_roundtrip":  {"pass": payload_pass,  "fail": payload_fail},
        "frame_encap_decap":  {"pass": frame_pass,    "fail": frame_fail},
        "frame_structure":    {"pass": struct_pass,   "fail": struct_fail},
        "crc_integrity":      {"pass": crc_pass,      "fail": crc_fail},
        "boundary":           {"pass": boundary_pass, "fail": boundary_fail},
        "width16":            {"pass": w16_pass,      "fail": w16_fail},
        "total_tests":        total_tests,
        "total_passed":       total_passed,
        "total_failed":       total_failed,
        "all_passed":         total_failed == 0,
    }

    results = {
        "module": "counter",
        "frame_format": {
            "layers": "Ether(14B) / IP(20B) / UDP(8B) / Payload(8B)",
            "payload_layout": "[count_out:2B][data_in:2B][flags:1B][rsv:1B]"
                              "[width:1B][magic:1B][crc:1B] = 9B",
            "magic": f"0x{MAGIC_BYTE:02X}",
            "total_frame_size": "51 bytes",
        },
        "summary": summary,
        "payload_results": payload_results,
        "frame_results": frame_results,
        "structure_results": struct_results,
        "crc_results": crc_results,
        "boundary_results": boundary_results,
        "width16_results": w16_results,
    }

    return results


# ======================================================================
# Report Formatters
# ======================================================================

def print_console_report(results: dict):
    """Print encapsulation/decapsulation test results."""
    summary = results["summary"]

    print("\n" + "=" * 72)
    print("  SCAPY COUNTER FRAME — Encapsulation / Decapsulation Test")
    print("=" * 72)

    fmt = results["frame_format"]
    print(f"\n  Frame: {fmt['layers']}")
    print(f"  Payload: {fmt['payload_layout']}")
    print(f"  Magic: {fmt['magic']}    Frame size: {fmt['total_frame_size']}")

    print(f"\n  WIDTH: {summary['width']}    Test states: {summary['total_test_states']}")

    print(f"\n  ┌──────────────────────┬──────┬──────┬──────────┐")
    print(f"  │ Test Category        │ Pass │ Fail │ Status   │")
    print(f"  ├──────────────────────┼──────┼──────┼──────────┤")
    for cat in ["payload_roundtrip", "frame_encap_decap", "frame_structure",
                "crc_integrity", "boundary", "width16"]:
        s = summary[cat]
        status = "✅" if s["fail"] == 0 else "❌"
        name = cat.replace("_", " ").title()
        print(f"  │ {name:<20s} │ {s['pass']:>4} │ {s['fail']:>4} │ {status}       │")
    print(f"  ├──────────────────────┼──────┼──────┼──────────┤")
    print(f"  │ {'TOTAL':<20s} │ {summary['total_passed']:>4} │ "
          f"{summary['total_failed']:>4} │ "
          f"{'✅' if summary['all_passed'] else '❌'}       │")
    print(f"  └──────────────────────┴──────┴──────┴──────────┘")

    if summary["all_passed"]:
        print(f"\n  ✅ VERDICT: All {summary['total_tests']} tests PASSED.")
    else:
        print(f"\n  ❌ VERDICT: {summary['total_failed']} test(s) FAILED!")

    # Sample frame
    print(f"\n{'─' * 72}")
    print(f"  SAMPLE FRAME (reset state)")
    print(f"{'─' * 72}")
    sample = CounterState(0, 0, 0, 0, 0, 0, summary["width"])
    frame_bytes = encapsulate(sample)
    pkt = Ether(frame_bytes)
    print(f"  {pkt.command()}")
    print(f"  Raw hex: {frame_bytes.hex()}")
    print(f"  Size:    {len(frame_bytes)} bytes")
    print(f"{'─' * 72}\n")


def generate_markdown_report(results: dict) -> str:
    """Generate Markdown report."""
    summary = results["summary"]
    fmt = results["frame_format"]

    lines = [
        "# scapy Counter Frame — Encapsulation/Decapsulation Report\n",
        f"**Module**: `counter`  ",
        f"**Counter WIDTH**: {summary['width']}  ",
        f"**Frame format**: {fmt['layers']}\n",
        "## Payload Layout\n",
        "| Offset | Size | Field | Description |",
        "|--------|------|-------|-------------|",
        "| 0      | 2 B  | count_out | Counter output value (big-endian) |",
        "| 2      | 2 B  | data_in   | Load data input (big-endian) |",
        "| 4      | 1 B  | flags     | bit[4]=overflow, bit[3]=up_down, bit[2]=en, bit[1]=load |",
        "| 5      | 1 B  | reserved  | Reserved (0) |",
        "| 6      | 1 B  | magic     | Frame marker (0xA5) |",
        "| 7      | 1 B  | crc       | XOR checksum of bytes 0–6 |",
        "",
        "## Test Results\n",
        "| Category | Passed | Failed | Status |",
        "|----------|--------|--------|--------|",
    ]

    for cat in ["payload_roundtrip", "frame_encap_decap", "frame_structure",
                "crc_integrity", "boundary", "width16"]:
        s = summary[cat]
        status = "✅ PASS" if s["fail"] == 0 else "❌ FAIL"
        name = cat.replace("_", " ").title()
        lines.append(f"| {name} | {s['pass']} | {s['fail']} | {status} |")

    lines.extend([
        f"| **Total** | **{summary['total_passed']}** | "
        f"**{summary['total_failed']}** | "
        f"**{'✅ ALL PASS' if summary['all_passed'] else '❌ FAILURES'}** |",
        "",
    ])

    if summary["all_passed"]:
        lines.append(f"> ✅ **All {summary['total_tests']} tests passed.** "
                     "Counter state correctly encapsulated into Ether/IP/UDP frames.\n")

    # Frame details
    lines.append("## Frame Round-Trip Details\n")
    lines.append("| # | count_out | data_in | Frame Size | IP Cksum | Status |")
    lines.append("|---|-----------|---------|------------|----------|--------|")
    for r in results["frame_results"]:
        status = "✅" if r["passed"] else "❌"
        orig = r["original"]
        ck = "OK" if r.get("ip_checksum_valid", False) else "BAD"
        lines.append(f"| {r['test_index']} | {orig['count_out']} | "
                     f"{orig['data_in']} | {r['frame_size']}B | {ck} | {status} |")

    # CRC details
    lines.append("\n## CRC Integrity Check Details\n")
    lines.append("| # | Flip Pos | Orig Byte | Tampered | CRC Detected | Status |")
    lines.append("|---|----------|-----------|----------|---------------|--------|")
    for r in results["crc_results"]:
        status = "✅" if r["passed"] else "❌"
        lines.append(f"| {r['test_index']} | byte {r['flip_pos']} | "
                     f"0x{r['original_byte']:02x} | 0x{r['tampered_byte']:02x} | "
                     f"{'yes' if r['passed'] else 'NO'} | {status} |")

    return "\n".join(lines)


# ======================================================================
# Main
# ======================================================================

def main():
    parser = argparse.ArgumentParser(
        description="scapy counter frame encapsulation/decapsulation test")
    parser.add_argument("--width", type=int, default=8,
                        help="Counter WIDTH parameter (default: 8)")
    parser.add_argument("--json", action="store_true",
                        help="Save results as JSON")
    parser.add_argument("--markdown", action="store_true",
                        help="Save results as Markdown")
    args = parser.parse_args()

    results = run_all_tests(args.width)
    print_console_report(results)

    if args.json:
        report_dir = SCRIPT_DIR / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        json_path = report_dir / "scapy_counter_frame.json"
        with open(json_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"[INFO] JSON report saved: {json_path}")

    if args.markdown:
        report_dir = SCRIPT_DIR / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        md_path = report_dir / "scapy_counter_frame.md"
        md_text = generate_markdown_report(results)
        with open(md_path, 'w') as f:
            f.write(md_text)
        print(f"[INFO] Markdown report saved: {md_path}")

    sys.exit(0 if results["summary"]["all_passed"] else 1)


if __name__ == "__main__":
    main()
