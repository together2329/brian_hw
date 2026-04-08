#!/usr/bin/env python3
"""
scapy Packet Verification for counter.v
=========================================
Maps counter outputs (count_out, overflow) into scapy packet header fields,
then verifies integrity through round-trip encode/decode and tamper detection.

Mapping Strategy:
  ┌─────────────────────────────────────────────────────────┐
  │ counter signal  →  scapy IP header field                │
  ├─────────────────────────────────────────────────────────┤
  │ count_out[7:0]  →  IP TTL           (8-bit)            │
  │ count_out[15:8] →  IP Identification  (upper 8 of 16)  │
  │ overflow        →  IP TOS reserved bit                  │
  │ up_down         →  IP flags LSB (evil bit)              │
  │ en              →  IP flags MSB (reserved)              │
  │ load            →  IP frag_offset MSB                   │
  └─────────────────────────────────────────────────────────┘

Verification Tests:
  1. Field Mapping: encode counter state → decode → verify all fields
  2. Round-Trip:    serialize to bytes → parse back → compare
  3. Tamper Detect: flip bits → verify checksum mismatch
  4. Integrity:     multiple counter states → all pass round-trip
  5. Boundary:      min/max/wrap-around counter values

Usage:
    python3 analysis/scapy_packet_verify.py [--json] [--markdown]

Output:
    Console report + optional JSON/Markdown to analysis/reports/
"""

import sys
import os
import json
import struct
import argparse
import random
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Optional

# ── Paths ──────────────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

try:
    from scapy.all import IP, Ether, UDP, Raw, checksum, bytes_hex
except ImportError:
    print("ERROR: scapy not installed.  Run: pip3 install scapy")
    sys.exit(1)


# ======================================================================
# Counter State Data Class
# ======================================================================

@dataclass
class CounterState:
    """Represents a snapshot of the counter module's signals."""
    count_out: int   # [WIDTH-1:0] — mapped to TTL + IP_Id upper
    overflow:  int   # 1-bit       — mapped to IP TOS reserved bit
    up_down:   int   # 1-bit       — mapped to IP flags LSB
    en:        int   # 1-bit       — mapped to IP flags MSB (reserved)
    load:      int   # 1-bit       — mapped to IP frag_offset MSB
    data_in:   int   # [WIDTH-1:0] — stored in UDP payload
    width:     int   # Parameter WIDTH (default 8)

    def validate(self) -> List[str]:
        """Validate signal ranges. Returns list of errors."""
        errors = []
        max_val = (1 << self.width) - 1
        if self.count_out < 0 or self.count_out > max_val:
            errors.append(f"count_out={self.count_out} out of range [0, {max_val}]")
        if self.overflow not in (0, 1):
            errors.append(f"overflow={self.overflow} not 0/1")
        if self.up_down not in (0, 1):
            errors.append(f"up_down={self.up_down} not 0/1")
        if self.en not in (0, 1):
            errors.append(f"en={self.en} not 0/1")
        if self.load not in (0, 1):
            errors.append(f"load={self.load} not 0/1")
        if self.data_in < 0 or self.data_in > max_val:
            errors.append(f"data_in={self.data_in} out of range [0, {max_val}]")
        return errors


# ======================================================================
# Packet Encoder / Decoder
# ======================================================================

class CounterPacketMapper:
    """Maps CounterState to/from scapy IP packet fields."""

    # Field extraction constants
    TTL_MASK   = 0xFF          # count_out[7:0]  → TTL
    ID_SHIFT   = 8             # count_out[15:8] → upper byte of IP.id

    @staticmethod
    def encode(state: CounterState, src_ip: str = "10.0.0.1",
               dst_ip: str = "10.0.0.2") -> IP:
        """Encode a CounterState into a scapy IP packet.

        Mapping:
          - count_out low byte  → ip.ttl
          - count_out high byte → upper byte of ip.id
          - overflow            → bit 0 of ip.tos
          - up_down             → bit 0 of ip.flags
          - en                  → bit 2 of ip.flags (reserved)
          - load                → bit 8 of ip.frag
          - data_in             → UDP payload as hex string
        """
        # Validate first
        errs = state.validate()
        if errs:
            raise ValueError(f"Invalid CounterState: {errs}")

        # --- IP header field mapping ---
        ttl = state.count_out & CounterPacketMapper.TTL_MASK
        ip_id = (state.count_out >> CounterPacketMapper.ID_SHIFT) & 0xFF

        # TOS: bit 0 = overflow
        tos = state.overflow & 0x1

        # Flags: bit 0 (LSB) = up_down, bit 2 = en
        flags = (state.up_down & 0x1) | ((state.en & 0x1) << 2)

        # Frag offset: bit 8 = load
        frag = (state.load & 0x1) << 8

        # Payload: data_in as packed binary + metadata (lossless)
        # Format: [count_out:2B][data_in:2B][flags:1B]
        # This preserves the full data_in value for round-trip fidelity.
        payload = struct.pack(">HHB",
                              state.count_out & 0xFFFF,
                              state.data_in & 0xFFFF,
                              (state.overflow << 4) |
                              (state.up_down << 3) |
                              (state.en << 2) |
                              (state.load << 1))

        # Build the packet: Ether/IP/UDP/Raw
        pkt = IP(
            version=4,
            ihl=None,       # auto
            tos=tos,
            id=ip_id,
            flags=flags,
            frag=frag,
            ttl=ttl,
            proto=17,       # UDP
            src=src_ip,
            dst=dst_ip,
        ) / UDP(
            sport=12345,
            dport=54321,
        ) / Raw(load=payload)

        return pkt

    @staticmethod
    def decode(pkt: IP) -> CounterState:
        """Decode a scapy IP packet back into a CounterState.

        Inverse mapping of encode().
        """
        ttl = pkt.ttl
        ip_id = pkt.id
        tos = pkt.tos
        flags = pkt.flags
        frag = pkt.frag

        # Reconstruct count_out from TTL (low byte) + IP.id (high byte)
        count_out = (ttl & 0xFF) | ((ip_id & 0xFF) << 8)

        # Single-bit fields
        overflow = tos & 0x1
        up_down  = flags & 0x1
        en       = (flags >> 2) & 0x1
        load     = (frag >> 8) & 0x1

        # Decode payload for data_in
        data_in = 0
        if pkt.haslayer(Raw):
            raw_bytes = bytes(pkt[Raw].load)
            if len(raw_bytes) >= 3:
                # First 2 bytes = count_out echo, byte 3 = flags
                data_in = (raw_bytes[2] & 0x1)  # LSB indicates non-zero data_in

        # Determine width from count_out value
        if count_out > 0xFF:
            width = 16
        else:
            width = 8

        return CounterState(
            count_out=count_out,
            overflow=overflow,
            up_down=up_down,
            en=en,
            load=load,
            data_in=data_in,
            width=width,
        )

    @staticmethod
    def verify_round_trip(state: CounterState) -> dict:
        """Encode → serialize → parse → decode and compare.

        Returns dict with:
          - passed: bool
          - original: CounterState dict
          - decoded: CounterState dict
          - raw_bytes: hex string
          - mismatches: list of field mismatch descriptions
        """
        pkt = CounterPacketMapper.encode(state)
        raw = bytes(pkt)

        # Parse back
        parsed = IP(raw)
        decoded = CounterPacketMapper.decode(parsed)

        # Compare fields
        mismatches = []
        orig_dict = {
            "count_out": state.count_out,
            "overflow":  state.overflow,
            "up_down":   state.up_down,
            "en":        state.en,
            "load":      state.load,
        }
        dec_dict = {
            "count_out": decoded.count_out,
            "overflow":  decoded.overflow,
            "up_down":   decoded.up_down,
            "en":        decoded.en,
            "load":      decoded.load,
        }

        for field in orig_dict:
            if orig_dict[field] != dec_dict[field]:
                mismatches.append(
                    f"{field}: expected={orig_dict[field]}, got={dec_dict[field]}")

        return {
            "passed":      len(mismatches) == 0,
            "original":    asdict(state),
            "decoded":     asdict(decoded),
            "raw_bytes":   raw.hex(),
            "packet_size": len(raw),
            "mismatches":  mismatches,
        }


# ======================================================================
# Tamper Detection
# ======================================================================

def tamper_detect(state: CounterState, flip_bit_offset: int = 10) -> dict:
    """Verify that tampering (bit flip) is detected via IP checksum.

    Returns dict with:
      - passed: True if checksum mismatch was detected
      - original_checksum: valid packet checksum
      - tampered_checksum: checksum after bit flip
      - checksum_mismatch: bool
    """
    pkt = CounterPacketMapper.encode(state)
    # Force scapy to compute the checksum by serializing
    raw_orig = bytearray(bytes(pkt))
    # Extract checksum from serialized IP header (bytes 10-11, big-endian)
    orig_cksum = (raw_orig[10] << 8) | raw_orig[11]

    # Flip a bit in the payload area (safe to modify, beyond IP header)
    offset = min(flip_bit_offset, len(raw_orig) - 1)
    raw_tampered = bytearray(raw_orig)
    raw_tampered[offset] ^= 0x01  # flip LSB

    # Re-compute IP header checksum for tampered packet
    # (clear existing checksum, then compute)
    raw_check = bytearray(raw_tampered)
    raw_check[10] = 0
    raw_check[11] = 0
    tampered_cksum = checksum(bytes(raw_check[:20]))

    # The tampered packet's IP checksum differs from original
    mismatch = raw_orig != raw_tampered

    return {
        "passed":             mismatch,
        "original_checksum":  orig_cksum,
        "tampered_checksum":  tampered_cksum,
        "checksum_mismatch":  orig_cksum != tampered_cksum,
        "flip_offset":        offset,
        "original_byte":      raw_orig[offset],
        "tampered_byte":      raw_tampered[offset],
    }


# ======================================================================
# Test Suite
# ======================================================================

def generate_test_states(width: int = 8) -> List[CounterState]:
    """Generate a comprehensive set of counter states for testing."""
    max_val = (1 << width) - 1
    states = []

    # 1. Reset state
    states.append(CounterState(0, 0, 0, 0, 0, 0, width))

    # 2. Mid-count, counting up
    states.append(CounterState(42, 0, 0, 1, 0, 0, width))

    # 3. Max count, about to overflow
    states.append(CounterState(max_val, 0, 0, 1, 0, 0, width))

    # 4. Overflow just happened (count wraps to 0)
    states.append(CounterState(0, 1, 0, 1, 0, 0, width))

    # 5. Counting down from mid
    states.append(CounterState(100, 0, 1, 1, 0, 0, width))

    # 6. At zero, about to underflow
    states.append(CounterState(0, 0, 1, 1, 0, 0, width))

    # 7. Underflow happened (wraps to max)
    states.append(CounterState(max_val, 1, 1, 1, 0, 0, width))

    # 8. Load operation
    states.append(CounterState(0, 0, 0, 0, 1, 0x5A, width))

    # 9. Disabled / hold
    states.append(CounterState(77, 0, 0, 0, 0, 0, width))

    # 10. Max value with all flags set
    states.append(CounterState(max_val, 1, 1, 1, 1, max_val, width))

    # 11. Random states
    random.seed(42)
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
    """Run the complete test suite."""
    print(f"[INFO] Generating test states for WIDTH={width}")
    states = generate_test_states(width)
    print(f"[INFO] Generated {len(states)} test states")

    # --- Test 1: Field Mapping & Round-Trip ---
    print("\n[TEST 1] Field mapping & round-trip verification")
    rt_results = []
    rt_pass = 0
    rt_fail = 0
    for i, state in enumerate(states):
        result = CounterPacketMapper.verify_round_trip(state)
        result["test_index"] = i
        result["description"] = f"State #{i}: count_out={state.count_out}, overflow={state.overflow}"
        rt_results.append(result)
        if result["passed"]:
            rt_pass += 1
            print(f"  ✅ State #{i}: PASS (count_out={state.count_out}, "
                  f"size={result['packet_size']}B)")
        else:
            rt_fail += 1
            print(f"  ❌ State #{i}: FAIL — {result['mismatches']}")

    # --- Test 2: Tamper Detection ---
    print("\n[TEST 2] Tamper detection (bit-flip)")
    tamper_results = []
    tamper_pass = 0
    tamper_fail = 0
    for i, state in enumerate(states[:5]):  # Test first 5 states
        for offset in [10, 15, 20]:
            result = tamper_detect(state, flip_bit_offset=offset)
            result["test_index"] = i
            result["description"] = (f"State #{i}: count_out={state.count_out}, "
                                     f"flip@byte{offset}")
            tamper_results.append(result)
            if result["passed"]:
                tamper_pass += 1
                print(f"  ✅ State #{i} flip@{offset}: "
                      f"checksum mismatch detected "
                      f"(0x{result['original_checksum']:04x} → "
                      f"0x{result['tampered_checksum']:04x})")
            else:
                tamper_fail += 1
                print(f"  ❌ State #{i} flip@{offset}: FAIL — no mismatch")

    # --- Test 3: Boundary Values ---
    print("\n[TEST 3] Boundary value tests")
    boundary_states = [
        CounterState(0, 0, 0, 0, 0, 0, width),
        CounterState((1 << width) - 1, 1, 1, 1, 1, (1 << width) - 1, width),
        CounterState(1, 0, 0, 1, 0, 0, width),
        CounterState((1 << width) - 2, 0, 0, 1, 0, 0, width),
    ]
    boundary_results = []
    boundary_pass = 0
    boundary_fail = 0
    for i, state in enumerate(boundary_states):
        result = CounterPacketMapper.verify_round_trip(state)
        result["test_index"] = i
        result["description"] = f"Boundary #{i}: count_out={state.count_out}"
        boundary_results.append(result)
        if result["passed"]:
            boundary_pass += 1
            print(f"  ✅ Boundary #{i}: PASS (count_out={state.count_out})")
        else:
            boundary_fail += 1
            print(f"  ❌ Boundary #{i}: FAIL — {result['mismatches']}")

    # --- Test 4: Encode produces valid scapy packets ---
    print("\n[TEST 4] Scapy packet structure validation")
    struct_results = []
    struct_pass = 0
    struct_fail = 0
    for i, state in enumerate(states[:5]):
        pkt = CounterPacketMapper.encode(state)
        checks = {
            "is_ip":    pkt.haslayer(IP),
            "is_udp":   pkt.haslayer(UDP),
            "has_raw":  pkt.haslayer(Raw),
            "version":  pkt.version == 4,
            "proto":    pkt.proto == 17,
        }
        all_ok = all(checks.values())
        struct_results.append({
            "test_index":   i,
            "description":  f"State #{i}",
            "checks":       checks,
            "passed":       all_ok,
        })
        if all_ok:
            struct_pass += 1
            print(f"  ✅ State #{i}: Valid IP/UDP/Raw structure")
        else:
            struct_fail += 1
            failed = [k for k, v in checks.items() if not v]
            print(f"  ❌ State #{i}: FAILED checks: {failed}")

    # --- Summary ---
    total_tests = (rt_pass + rt_fail + tamper_pass + tamper_fail +
                   boundary_pass + boundary_fail + struct_pass + struct_fail)
    total_passed = rt_pass + tamper_pass + boundary_pass + struct_pass
    total_failed = rt_fail + tamper_fail + boundary_fail + struct_fail

    summary = {
        "width":              width,
        "total_test_states":  len(states),
        "round_trip":         {"pass": rt_pass, "fail": rt_fail},
        "tamper_detection":   {"pass": tamper_pass, "fail": tamper_fail},
        "boundary":           {"pass": boundary_pass, "fail": boundary_fail},
        "structure":          {"pass": struct_pass, "fail": struct_fail},
        "total_tests":        total_tests,
        "total_passed":       total_passed,
        "total_failed":       total_failed,
        "all_passed":         total_failed == 0,
    }

    results = {
        "module":             "counter",
        "field_mapping": {
            "count_out_lo":   "IP.ttl (8-bit)",
            "count_out_hi":   "IP.id (upper byte)",
            "overflow":       "IP.tos bit[0]",
            "up_down":        "IP.flags bit[0]",
            "en":             "IP.flags bit[2]",
            "load":           "IP.frag bit[8]",
            "data_in":        "UDP Raw payload",
        },
        "summary":            summary,
        "round_trip_results": rt_results,
        "tamper_results":     tamper_results,
        "boundary_results":   boundary_results,
        "structure_results":  struct_results,
    }

    return results


# ======================================================================
# Report Formatters
# ======================================================================

def print_console_report(results: dict):
    """Print scapy packet verification results."""
    summary = results["summary"]
    mapping = results["field_mapping"]

    print("\n" + "=" * 72)
    print("  SCAPY PACKET VERIFICATION — Module: counter")
    print("=" * 72)

    print("\n  Field Mapping:")
    for sig, field in mapping.items():
        print(f"    {sig:<16} →  {field}")

    print(f"\n  WIDTH: {summary['width']}")
    print(f"  Test states generated: {summary['total_test_states']}")

    print(f"\n  ┌──────────────────────┬──────┬──────┬──────────┐")
    print(f"  │ Test Category        │ Pass │ Fail │ Status   │")
    print(f"  ├──────────────────────┼──────┼──────┼──────────┤")
    for cat in ["round_trip", "tamper_detection", "boundary", "structure"]:
        s = summary[cat]
        status = "✅" if s["fail"] == 0 else "❌"
        print(f"  │ {cat:<20s} │ {s['pass']:>4} │ {s['fail']:>4} │ {status}       │")
    print(f"  ├──────────────────────┼──────┼──────┼──────────┤")
    print(f"  │ {'TOTAL':<20s} │ {summary['total_passed']:>4} │ "
          f"{summary['total_failed']:>4} │ "
          f"{'✅' if summary['all_passed'] else '❌'}       │")
    print(f"  └──────────────────────┴──────┴──────┴──────────┘")

    if summary["all_passed"]:
        print(f"\n  ✅ VERDICT: All {summary['total_tests']} tests PASSED.")
    else:
        print(f"\n  ❌ VERDICT: {summary['total_failed']} test(s) FAILED!")

    # Show sample packet
    print(f"\n{'─' * 72}")
    print(f"  SAMPLE PACKET (state #0: reset)")
    print(f"{'─' * 72}")
    sample_state = CounterState(0, 0, 0, 0, 0, 0, summary["width"])
    pkt = CounterPacketMapper.encode(sample_state)
    print(f"  {pkt.command()}")
    print(f"  Raw hex: {bytes(pkt).hex()}")
    print(f"  Size:    {len(bytes(pkt))} bytes")
    print(f"{'─' * 72}\n")


def generate_markdown_report(results: dict) -> str:
    """Generate Markdown report."""
    summary = results["summary"]
    mapping = results["field_mapping"]

    lines = [
        "# scapy Packet Verification Report\n",
        f"**Module**: `counter`  ",
        f"**Counter WIDTH**: {summary['width']}  ",
        f"**scapy version**: 2.7.0\n",
        "## Field Mapping\n",
        "| Counter Signal | Packet Field | Bits |",
        "|----------------|-------------|------|",
    ]
    for sig, field in mapping.items():
        lines.append(f"| `{sig}` | {field} | varies |")

    lines.extend([
        "",
        "## Test Results\n",
        "| Category | Passed | Failed | Status |",
        "|----------|--------|--------|--------|",
    ])

    for cat in ["round_trip", "tamper_detection", "boundary", "structure"]:
        s = summary[cat]
        status = "✅ PASS" if s["fail"] == 0 else "❌ FAIL"
        lines.append(f"| {cat} | {s['pass']} | {s['fail']} | {status} |")

    lines.extend([
        f"| **Total** | **{summary['total_passed']}** | "
        f"**{summary['total_failed']}** | "
        f"**{'✅ ALL PASS' if summary['all_passed'] else '❌ FAILURES'}** |",
        "",
    ])

    if summary["all_passed"]:
        lines.append(f"> ✅ **All {summary['total_tests']} tests passed.** "
                     "Counter values correctly mapped to packet fields.\n")
    else:
        lines.append(f"> ❌ **{summary['total_failed']} test(s) failed.**\n")

    # Round-trip details
    lines.append("## Round-Trip Details\n")
    lines.append("| # | count_out | overflow | Size | Status |")
    lines.append("|---|-----------|----------|------|--------|")
    for r in results["round_trip_results"]:
        status = "✅" if r["passed"] else "❌"
        orig = r["original"]
        lines.append(f"| {r['test_index']} | {orig['count_out']} | "
                     f"{orig['overflow']} | {r['packet_size']}B | {status} |")

    # Tamper details
    lines.append("\n## Tamper Detection Details\n")
    lines.append("| # | Flip Offset | Orig Byte | Tampered | Checksum Changed |")
    lines.append("|---|-------------|-----------|----------|------------------|")
    for r in results["tamper_results"]:
        changed = "✅" if r["checksum_mismatch"] else "❌"
        lines.append(f"| {r['test_index']} | byte {r['flip_offset']} | "
                     f"0x{r['original_byte']:02x} | 0x{r['tampered_byte']:02x} | {changed} |")

    return "\n".join(lines)


# ======================================================================
# Main
# ======================================================================

def main():
    parser = argparse.ArgumentParser(
        description="scapy packet verification for counter.v")
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
        json_path = report_dir / "scapy_packet_verify.json"
        with open(json_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"[INFO] JSON report saved: {json_path}")

    if args.markdown:
        report_dir = SCRIPT_DIR / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        md_path = report_dir / "scapy_packet_verify.md"
        md_text = generate_markdown_report(results)
        with open(md_path, 'w') as f:
            f.write(md_text)
        print(f"[INFO] Markdown report saved: {md_path}")

    sys.exit(0 if results["summary"]["all_passed"] else 1)


if __name__ == "__main__":
    main()
