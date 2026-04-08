#!/usr/bin/env python3
"""
scapy Communication Integrity Verification for counter.v
=========================================================
Applies FCS/CRC checksum protection to counter output values and verifies
that intentional bit-flips are reliably detected.

Integrity Mechanisms:
  1. IP Header Checksum — standard IPv4 header integrity
  2. CRC-32 (Ethernet FCS) — full-frame integrity check
  3. Counter Payload CRC-8 — XOR-based payload checksum
  4. Multi-bit burst error detection
  5. Cross-layer validation (header + payload independently)

Test Categories:
  1. Single-bit flip detection in IP header
  2. Single-bit flip detection in UDP/payload
  3. Multi-bit burst error detection
  4. CRC-32 FCS protection of full frame
  5. Correct frames pass all checks (no false positives)
  6. Cross-layer: header intact + payload tampered, and vice versa

Usage:
    python3 analysis/scapy_integrity.py [--json] [--markdown]
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
    from scapy.all import Ether, IP, UDP, Raw, checksum
except ImportError:
    print("ERROR: scapy not installed.  Run: pip3 install scapy")
    sys.exit(1)


# ======================================================================
# Constants
# ======================================================================

MAGIC_BYTE = 0xA5
SRC_MAC    = "00:aa:bb:cc:dd:01"
DST_MAC    = "00:aa:bb:cc:dd:02"
SRC_IP     = "192.168.1.10"
DST_IP     = "192.168.1.20"
UDP_SPORT  = 0xC0DE
UDP_DPORT  = 0xBA5E


# ======================================================================
# Counter State
# ======================================================================

@dataclass
class CounterState:
    """Snapshot of counter module signals."""
    count_out: int
    overflow:  int
    up_down:   int
    en:        int
    load:      int
    data_in:   int
    width:     int

    def validate(self) -> List[str]:
        errors = []
        max_val = (1 << self.width) - 1
        if not (0 <= self.count_out <= max_val):
            errors.append(f"count_out={self.count_out} out of range")
        if not (0 <= self.data_in <= max_val):
            errors.append(f"data_in={self.data_in} out of range")
        for name, val in [("overflow", self.overflow), ("up_down", self.up_down),
                          ("en", self.en), ("load", self.load)]:
            if val not in (0, 1):
                errors.append(f"{name}={val} not 0/1")
        return errors


# ======================================================================
# Checksum / CRC Functions
# ======================================================================

def ip_header_checksum(ip_hdr_bytes: bytes) -> int:
    """Compute standard IP header checksum (RFC 1071)."""
    zeroed = bytearray(ip_hdr_bytes[:20])
    zeroed[10] = 0
    zeroed[11] = 0
    return checksum(bytes(zeroed))


def crc32(data: bytes) -> int:
    """Compute CRC-32 (Ethernet FCS polynomial)."""
    crc = 0xFFFFFFFF
    poly = 0xEDB88320  # Reversed polynomial for CRC-32
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ poly
            else:
                crc >>= 1
    return crc ^ 0xFFFFFFFF


def payload_crc8(data: bytes) -> int:
    """CRC-8/SMBUS (polynomial 0x07, init 0x00) for counter payload.
    
    Proper polynomial CRC-8 instead of simple XOR, so that multi-byte
    burst errors (e.g. 0xFF ^ 0xFF = 0x00 cancellation) are reliably
    detected.
    """
    crc = 0x00
    for b in data:
        crc ^= b
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ 0x07) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc


# ======================================================================
# Frame Builder
# ======================================================================

def build_frame(state: CounterState) -> Tuple[bytes, dict]:
    """Build complete Ether/IP/UDP frame with counter payload.
    
    Returns (frame_bytes, metadata_dict).
    """
    errs = state.validate()
    if errs:
        raise ValueError(f"Invalid CounterState: {errs}")

    # Build 9-byte payload: [count_out:2][data_in:2][flags:1][rsv:1][width:1][magic:1][crc8:1]
    flags = ((state.overflow & 0x1) << 4) | ((state.up_down & 0x1) << 3) | \
            ((state.en & 0x1) << 2) | ((state.load & 0x1) << 1)
    header = struct.pack(">HHBBB",
                         state.count_out & 0xFFFF,
                         state.data_in & 0xFFFF,
                         flags, 0, state.width)
    pre_crc = header + bytes([MAGIC_BYTE])
    crc8 = payload_crc8(pre_crc)
    payload = pre_crc + bytes([crc8])

    # Build frame
    frame = (
        Ether(src=SRC_MAC, dst=DST_MAC) /
        IP(version=4, src=SRC_IP, dst=DST_IP, proto=17, ttl=64) /
        UDP(sport=UDP_SPORT, dport=UDP_DPORT) /
        Raw(load=payload)
    )
    raw = bytes(frame)

    # Compute FCS (CRC-32 over entire frame)
    fcs = crc32(raw)

    meta = {
        "frame_size": len(raw),
        "payload_size": len(payload),
        "payload_crc8": crc8,
        "fcs_crc32": fcs,
        "ip_checksum": ip_header_checksum(raw[:20]),
    }

    return raw, meta


def parse_frame(frame_bytes: bytes) -> dict:
    """Parse frame and return integrity check results.
    
    Returns dict with:
      - ip_checksum_valid: bool
      - stored_ip_checksum: int
      - computed_ip_checksum: int
      - payload_crc8_valid: bool
      - fcs_valid: bool (if FCS appended)
      - layers: list of layer names
      - payload_decoded: CounterState or None
      - warnings: list of integrity warning strings
    """
    result = {
        "ip_checksum_valid": False,
        "stored_ip_checksum": 0,
        "computed_ip_checksum": 0,
        "payload_crc8_valid": False,
        "fcs_valid": False,
        "payload_decoded": None,
        "warnings": [],
    }

    if len(frame_bytes) < 20:
        result["warnings"].append("Frame too short for IP header")
        return result

    # --- IP Header Checksum (IP header starts at byte 14 after Ethernet) ---
    if len(frame_bytes) < 34:  # Need at least 14 (Ether) + 20 (IP)
        result["warnings"].append("Frame too short for IP header")
        return result

    ip_hdr = frame_bytes[14:34]  # IP header = bytes 14..33
    stored = (ip_hdr[10] << 8) | ip_hdr[11]
    computed = ip_header_checksum(ip_hdr)
    result["stored_ip_checksum"] = stored
    result["computed_ip_checksum"] = computed
    result["ip_checksum_valid"] = (stored == computed)
    if not result["ip_checksum_valid"]:
        result["warnings"].append(
            f"IP checksum mismatch: stored=0x{stored:04x}, computed=0x{computed:04x}")

    # --- Parse with scapy ---
    pkt = Ether(frame_bytes)
    result["layers"] = [l.__class__.__name__ for l in pkt]

    # --- Get raw payload ---
    if pkt.haslayer(UDP) and pkt.haslayer(Raw):
        raw_payload = bytes(pkt[Raw].load)
    elif pkt.haslayer(Raw):
        raw_all = bytes(pkt[Raw].load)
        raw_payload = raw_all[8:] if len(raw_all) > 8 else b""
    else:
        result["warnings"].append("No payload layer found")
        return result

    # --- Payload CRC-8 ---
    if len(raw_payload) >= 9:
        pre_crc = raw_payload[:8]
        stored_crc8 = raw_payload[8]
        computed_crc8 = payload_crc8(pre_crc)
        result["payload_crc8_valid"] = (stored_crc8 == computed_crc8)
        result["stored_payload_crc8"] = stored_crc8
        result["computed_payload_crc8"] = computed_crc8
        if not result["payload_crc8_valid"]:
            result["warnings"].append(
                f"Payload CRC-8 mismatch: stored=0x{stored_crc8:02x}, "
                f"computed=0x{computed_crc8:02x}")

        # Decode payload
        if result["payload_crc8_valid"]:
            magic = raw_payload[7]
            if magic != MAGIC_BYTE:
                result["warnings"].append(f"Magic byte wrong: 0x{magic:02x}")
            else:
                co, di, fl, rsv, w = struct.unpack(">HHBBB", raw_payload[:7])
                result["payload_decoded"] = CounterState(
                    count_out=co,
                    overflow=(fl >> 4) & 0x1,
                    up_down=(fl >> 3) & 0x1,
                    en=(fl >> 2) & 0x1,
                    load=(fl >> 1) & 0x1,
                    data_in=di,
                    width=w if w in (8, 16) else 8,
                )

    return result


# ======================================================================
# Integrity Test Functions
# ======================================================================

def test_single_bit_ip_header(state: CounterState, flip_byte: int = 20) -> dict:
    """Test: single bit-flip in IP header is detected by IP checksum.
    
    flip_byte is offset within the full frame (IP header = bytes 14..33).
    """
    raw, meta = build_frame(state)
    tampered = bytearray(raw)
    tampered[flip_byte] ^= 0x01

    result = parse_frame(bytes(tampered))
    return {
        "passed": not result["ip_checksum_valid"],
        "ip_checksum_valid": result["ip_checksum_valid"],
        "warning_count": len(result["warnings"]),
        "warnings": result["warnings"],
        "flip_byte": flip_byte,
        "region": "ip_header",
    }


def test_single_bit_payload(state: CounterState, flip_byte: int = 44) -> dict:
    """Test: single bit-flip in payload is detected by payload CRC-8."""
    raw, meta = build_frame(state)
    tampered = bytearray(raw)
    tampered[flip_byte] ^= 0x01

    result = parse_frame(bytes(tampered))
    return {
        "passed": not result["payload_crc8_valid"],
        "payload_crc8_valid": result["payload_crc8_valid"],
        "ip_checksum_valid": result["ip_checksum_valid"],
        "warning_count": len(result["warnings"]),
        "warnings": result["warnings"],
        "flip_byte": flip_byte,
        "region": "payload",
    }


def test_multi_bit_burst(state: CounterState, start_byte: int = 42,
                         burst_len: int = 3) -> dict:
    """Test: multi-bit burst error is detected."""
    raw, meta = build_frame(state)
    tampered = bytearray(raw)
    for i in range(burst_len):
        idx = min(start_byte + i, len(tampered) - 1)
        tampered[idx] ^= 0xFF  # flip all bits in each byte

    result = parse_frame(bytes(tampered))
    detected = not result["ip_checksum_valid"] or not result["payload_crc8_valid"]
    return {
        "passed": detected,
        "ip_checksum_valid": result["ip_checksum_valid"],
        "payload_crc8_valid": result["payload_crc8_valid"],
        "start_byte": start_byte,
        "burst_len": burst_len,
        "region": "payload" if start_byte >= 42 else "ip_header",
        "warnings": result["warnings"],
    }


def test_fcs_protection(state: CounterState, flip_byte: int = 30) -> dict:
    """Test: CRC-32 FCS detects frame tampering."""
    raw, meta = build_frame(state)
    original_fcs = crc32(raw)

    tampered = bytearray(raw)
    tampered[flip_byte] ^= 0x01
    tampered_fcs = crc32(bytes(tampered))

    return {
        "passed": original_fcs != tampered_fcs,
        "original_fcs": original_fcs,
        "tampered_fcs": tampered_fcs,
        "fcs_changed": original_fcs != tampered_fcs,
        "flip_byte": flip_byte,
    }


def test_clean_frame(state: CounterState) -> dict:
    """Test: unmodified frame passes all integrity checks (no false positives)."""
    raw, meta = build_frame(state)
    result = parse_frame(raw)

    all_valid = result["ip_checksum_valid"] and result["payload_crc8_valid"]
    decoded = result["payload_decoded"]

    field_match = (decoded is not None and
                   asdict(state) == asdict(decoded))

    return {
        "passed": all_valid and field_match and len(result["warnings"]) == 0,
        "ip_checksum_valid": result["ip_checksum_valid"],
        "payload_crc8_valid": result["payload_crc8_valid"],
        "field_match": field_match,
        "warnings": result["warnings"],
    }


def test_cross_layer(state: CounterState) -> dict:
    """Test: IP header intact but payload tampered → IP ok, payload CRC fails."""
    raw, meta = build_frame(state)

    # Tamper only payload (byte 46 = inside counter payload, past IP+UDP headers)
    tampered = bytearray(raw)
    tampered[46] ^= 0x01

    result = parse_frame(bytes(tampered))
    return {
        "passed": (result["ip_checksum_valid"] and
                   not result["payload_crc8_valid"]),
        "ip_intact": result["ip_checksum_valid"],
        "payload_corrupt": not result["payload_crc8_valid"],
        "description": "IP header intact, payload corrupted",
        "warnings": result["warnings"],
    }


# ======================================================================
# Test Suite Runner
# ======================================================================

def generate_test_states(width: int = 8) -> List[CounterState]:
    """Generate test counter states."""
    max_val = (1 << width) - 1
    states = [
        CounterState(0, 0, 0, 0, 0, 0, width),
        CounterState(42, 0, 0, 1, 0, 0, width),
        CounterState(max_val, 0, 0, 1, 0, 0, width),
        CounterState(0, 1, 0, 1, 0, 0, width),
        CounterState(100, 0, 1, 1, 0, 0, width),
        CounterState(0, 0, 0, 0, 1, 0x5A, width),
        CounterState(77, 0, 0, 0, 0, 0, width),
        CounterState(max_val, 1, 1, 1, 1, max_val, width),
    ]
    random.seed(0xBEEF)
    for _ in range(4):
        states.append(CounterState(
            random.randint(0, max_val), random.randint(0, 1),
            random.randint(0, 1), random.randint(0, 1),
            random.randint(0, 1), random.randint(0, max_val), width))
    return states


def run_all_tests(width: int = 8) -> dict:
    """Run the complete integrity verification test suite."""
    states = generate_test_states(width)

    # ── Test 1: Single-bit IP header ──
    print("\n[TEST 1] Single-bit flip detection — IP header checksum")
    t1_results, t1p, t1f = [], 0, 0
    for i, st in enumerate(states[:5]):
        for byte_off in [16, 22, 28]:  # IP header = bytes 14..33
            r = test_single_bit_ip_header(st, flip_byte=byte_off)
            r["test_index"] = i
            t1_results.append(r)
            if r["passed"]:
                t1p += 1
                print(f"  ✅ State#{i} flip@byte{byte_off}: IP checksum detected")
            else:
                t1f += 1
                print(f"  ❌ State#{i} flip@byte{byte_off}: MISSED")

    # ── Test 2: Single-bit payload ──
    print("\n[TEST 2] Single-bit flip detection — Payload CRC-8")
    t2_results, t2p, t2f = [], 0, 0
    for i, st in enumerate(states[:5]):
        for byte_off in [42, 44, 46, 49]:  # Payload = bytes 42..50 (9 bytes)
            r = test_single_bit_payload(st, flip_byte=byte_off)
            r["test_index"] = i
            t2_results.append(r)
            if r["passed"]:
                t2p += 1
                print(f"  ✅ State#{i} flip@byte{byte_off}: Payload CRC-8 detected")
            else:
                t2f += 1
                print(f"  ❌ State#{i} flip@byte{byte_off}: MISSED")

    # ── Test 3: Multi-bit burst ──
    print("\n[TEST 3] Multi-bit burst error detection")
    t3_results, t3p, t3f = [], 0, 0
    for i, st in enumerate(states[:5]):
        for start, blen in [(42, 2), (44, 3), (42, 5)]:
            r = test_multi_bit_burst(st, start_byte=start, burst_len=blen)
            r["test_index"] = i
            t3_results.append(r)
            if r["passed"]:
                t3p += 1
                print(f"  ✅ State#{i} burst@{start}+{blen}B: Detected")
            else:
                t3f += 1
                print(f"  ❌ State#{i} burst@{start}+{blen}B: MISSED")

    # ── Test 4: FCS CRC-32 ──
    print("\n[TEST 4] CRC-32 FCS protection")
    t4_results, t4p, t4f = [], 0, 0
    for i, st in enumerate(states[:5]):
        for flip in [20, 30, 46]:  # Various positions across frame
            r = test_fcs_protection(st, flip_byte=flip)
            r["test_index"] = i
            t4_results.append(r)
            if r["passed"]:
                t4p += 1
                print(f"  ✅ State#{i} flip@{flip}: FCS 0x{r['original_fcs']:08x} → "
                      f"0x{r['tampered_fcs']:08x}")
            else:
                t4f += 1
                print(f"  ❌ State#{i} flip@{flip}: FCS unchanged (BAD)")

    # ── Test 5: Clean frame (no false positives) ──
    print("\n[TEST 5] Clean frame — no false positives")
    t5_results, t5p, t5f = [], 0, 0
    for i, st in enumerate(states):
        r = test_clean_frame(st)
        r["test_index"] = i
        t5_results.append(r)
        if r["passed"]:
            t5p += 1
        else:
            t5f += 1
            print(f"  ❌ State#{i}: FALSE POSITIVE — {r['warnings']}")
    print(f"  ✅ All {t5p} clean frames passed (0 false positives)")

    # ── Test 6: Cross-layer validation ──
    print("\n[TEST 6] Cross-layer validation (header vs payload)")
    t6_results, t6p, t6f = [], 0, 0
    for i, st in enumerate(states[:5]):
        r = test_cross_layer(st)
        r["test_index"] = i
        t6_results.append(r)
        if r["passed"]:
            t6p += 1
            print(f"  ✅ State#{i}: IP intact={r['ip_intact']}, "
                  f"payload corrupt={r['payload_corrupt']}")
        else:
            t6f += 1
            print(f"  ❌ State#{i}: IP intact={r['ip_intinct']}, "
                  f"payload corrupt={r['payload_corrupt']}")

    # ── Summary ──
    total_tests = t1p+t1f + t2p+t2f + t3p+t3f + t4p+t4f + t5p+t5f + t6p+t6f
    total_passed = t1p + t2p + t3p + t4p + t5p + t6p
    total_failed = t1f + t2f + t3f + t4f + t5f + t6f

    summary = {
        "width": width,
        "total_test_states": len(states),
        "ip_header_single_bit": {"pass": t1p, "fail": t1f},
        "payload_single_bit":   {"pass": t2p, "fail": t2f},
        "multi_bit_burst":      {"pass": t3p, "fail": t3f},
        "fcs_crc32":            {"pass": t4p, "fail": t4f},
        "clean_no_false_pos":   {"pass": t5p, "fail": t5f},
        "cross_layer":          {"pass": t6p, "fail": t6f},
        "total_tests":          total_tests,
        "total_passed":         total_passed,
        "total_failed":         total_failed,
        "all_passed":           total_failed == 0,
    }

    results = {
        "module": "counter",
        "integrity_mechanisms": {
            "ip_header_checksum": "RFC 1071 — detects IP header corruption",
            "payload_crc8":       "CRC-8/SMBUS (poly 0x07) — detects payload corruption",
            "fcs_crc32":          "Ethernet CRC-32 — full frame integrity",
        },
        "summary": summary,
        "ip_header_results": t1_results,
        "payload_results":   t2_results,
        "burst_results":     t3_results,
        "fcs_results":       t4_results,
        "clean_results":     t5_results,
        "cross_layer_results": t6_results,
    }

    return results


# ======================================================================
# Report Formatters
# ======================================================================

def print_console_report(results: dict):
    """Print integrity verification results."""
    summary = results["summary"]
    mechs = results["integrity_mechanisms"]

    print("\n" + "=" * 72)
    print("  SCAPY INTEGRITY VERIFICATION — Module: counter")
    print("=" * 72)

    print("\n  Integrity Mechanisms:")
    for name, desc in mechs.items():
        print(f"    {name:<22s} — {desc}")

    print(f"\n  WIDTH: {summary['width']}    Test states: {summary['total_test_states']}")

    cats = [
        ("ip_header_single_bit", "IP Header Single-Bit"),
        ("payload_single_bit",   "Payload Single-Bit"),
        ("multi_bit_burst",      "Multi-Bit Burst"),
        ("fcs_crc32",            "FCS CRC-32"),
        ("clean_no_false_pos",   "Clean (No False Pos)"),
        ("cross_layer",          "Cross-Layer"),
    ]

    print(f"\n  ┌──────────────────────┬──────┬──────┬──────────┐")
    print(f"  │ Test Category        │ Pass │ Fail │ Status   │")
    print(f"  ├──────────────────────┼──────┼──────┼──────────┤")
    for key, name in cats:
        s = summary[key]
        status = "✅" if s["fail"] == 0 else "❌"
        print(f"  │ {name:<20s} │ {s['pass']:>4} │ {s['fail']:>4} │ {status}       │")
    print(f"  ├──────────────────────┼──────┼──────┼──────────┤")
    print(f"  │ {'TOTAL':<20s} │ {summary['total_passed']:>4} │ "
          f"{summary['total_failed']:>4} │ "
          f"{'✅' if summary['all_passed'] else '❌'}       │")
    print(f"  └──────────────────────┴──────┴──────┴──────────┘")

    if summary["all_passed"]:
        print(f"\n  ✅ VERDICT: All {summary['total_tests']} integrity tests PASSED.")
    else:
        print(f"\n  ❌ VERDICT: {summary['total_failed']} test(s) FAILED!")

    print()


def generate_markdown_report(results: dict) -> str:
    """Generate Markdown report."""
    summary = results["summary"]
    mechs = results["integrity_mechanisms"]

    lines = [
        "# scapy Integrity Verification Report\n",
        f"**Module**: `counter`  ",
        f"**Counter WIDTH**: {summary['width']}\n",
        "## Integrity Mechanisms\n",
        "| Mechanism | Description |",
        "|-----------|-------------|",
    ]
    for name, desc in mechs.items():
        lines.append(f"| `{name}` | {desc} |")

    lines.extend([
        "",
        "## Test Results\n",
        "| Category | Passed | Failed | Status |",
        "|----------|--------|--------|--------|",
    ])

    cats = [
        ("ip_header_single_bit", "IP Header Single-Bit"),
        ("payload_single_bit",   "Payload Single-Bit"),
        ("multi_bit_burst",      "Multi-Bit Burst"),
        ("fcs_crc32",            "FCS CRC-32"),
        ("clean_no_false_pos",   "Clean (No False Pos)"),
        ("cross_layer",          "Cross-Layer"),
    ]
    for key, name in cats:
        s = summary[key]
        status = "✅ PASS" if s["fail"] == 0 else "❌ FAIL"
        lines.append(f"| {name} | {s['pass']} | {s['fail']} | {status} |")

    lines.extend([
        f"| **Total** | **{summary['total_passed']}** | "
        f"**{summary['total_failed']}** | "
        f"**{'✅ ALL PASS' if summary['all_passed'] else '❌ FAILURES'}** |",
        "",
    ])

    if summary["all_passed"]:
        lines.append(f"> ✅ **All {summary['total_tests']} integrity tests passed.** "
                     "Counter values are protected by multi-layer checksum verification.\n")

    # FCS details
    lines.append("## FCS CRC-32 Details\n")
    lines.append("| # | Flip Byte | Original FCS | Tampered FCS | Detected |")
    lines.append("|---|-----------|-------------|-------------|----------|")
    for r in results["fcs_results"]:
        det = "✅" if r["passed"] else "❌"
        lines.append(f"| {r['test_index']} | byte {r['flip_byte']} | "
                     f"0x{r['original_fcs']:08x} | 0x{r['tampered_fcs']:08x} | {det} |")

    return "\n".join(lines)


# ======================================================================
# Main
# ======================================================================

def main():
    parser = argparse.ArgumentParser(
        description="scapy integrity verification for counter.v")
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
        json_path = report_dir / "scapy_integrity.json"
        with open(json_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"[INFO] JSON report saved: {json_path}")

    if args.markdown:
        report_dir = SCRIPT_DIR / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        md_path = report_dir / "scapy_integrity.md"
        md_text = generate_markdown_report(results)
        with open(md_path, 'w') as f:
            f.write(md_text)
        print(f"[INFO] Markdown report saved: {md_path}")

    sys.exit(0 if results["summary"]["all_passed"] else 1)


if __name__ == "__main__":
    main()
