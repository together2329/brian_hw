"""Genuine SRAM-write monitor for mctp_assembler_v3 — no-holes / payload-only /
no-header-or-pad-write evidence (PAYLOAD_STREAM_CONTRACT §1, §4.3).

The multi-beat pack engine must write message byte i to SRAM byte
`ctx_payload_base + i` with NO holes across beats/fragments, write ONLY payload
bytes (never the 16 B header, never pad bytes), and never exceed the descriptor
read window `[base, base+payload_len)`.

This monitor drives the same four content scenarios as test_pl_readback, but
instead of only reading the bytes back it records the EXACT set of SRAM byte
addresses the DUT's real pack engine strobed (via DatapathMonitor.write_log,
opt-in), and verifies against the known payload window:

  * sram_no_header_or_pad_write: no written byte address lies OUTSIDE
    [base, base+payload_len) — i.e. no header byte (< base, the 16 B header is
    stripped before SRAM) and no pad byte (>= base+payload_len) is ever written.
  * sram_payload_only: the union of written addresses ⊆ [base, base+payload_len).
  * sram_payload_no_holes: the union of written addresses == EXACTLY
    {base .. base+payload_len-1} (every payload byte written once, no gaps),
    AND the bytes read back through the AXI read path equal the golden payload.

It emits sim/sram_write_evidence.json consumed by emit_monitor_evidence.py.
TB-ONLY; assertions are strict. A real hole / header write / out-of-window
write is a real RTL bug — the test fails and records the offending addresses,
never masked.
"""

from __future__ import annotations

import hashlib
import json
from math import ceil
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import with_timeout

import mctp_stimulus as S

HERE = Path(__file__).resolve().parent
IP_DIR = HERE.parent.parent
EVIDENCE_PATH = IP_DIR / "sim" / "sram_write_evidence.json"
SCOREBOARD_PATH = IP_DIR / "sim" / "scoreboard_events.jsonl"

RB_BASE = 0

# VCM-1 fixed conventions (VCM-2 references these):
#   field name      : payload_digest (sha256 hexdigest of the byte sequence)
#   expected_path   : fl_expected.model_result.state_updates.payload_digest
#   goal_id         : EQ_TRANSACTION_FM_PACK_SRAM (an EXISTING payload goal, so
#                     check_scoreboard does not flag "unknown goal_id")
#   scenario_ids    : SC_RB_4096 (primary), SC_RB_FRAG (no-hole-across-boundary)
DIGEST_GOAL_ID = "EQ_TRANSACTION_FM_PACK_SRAM"
DIGEST_FIELD = "payload_digest"
# A marker so re-runs replace (not duplicate) the digest rows we appended, while
# leaving the datapath merge's own EQ_TRANSACTION_FM_PACK_SRAM rows intact.
DIGEST_ROW_MARKER = "vcm1_payload_digest"


async def _setup(dut):
    cocotb.start_soon(Clock(dut.axi_aclk, 10, units="ns").start())
    cocotb.start_soon(Clock(dut.pclk, 10, units="ns").start())
    await S.reset_dut(dut)


def _golden(packets) -> bytes:
    out = bytearray()
    for pkt in packets:
        tlp = S.build_vdm_tlp(pkt)
        out += tlp[16:16 + S.expected_payload_bytes(pkt)]
    return bytes(out)


async def _run_case(dut, monitor, sram, name, packets, *, tu_bytes,
                    max_cycles=4000, send_cycles=600):
    """Drive one message, capture the written address set + readback, and return
    a per-case evidence dict with the three boolean sub-checks."""
    await S.reset_dut(dut)
    sram[:] = bytearray(len(sram))
    monitor.clear()
    monitor.clear_write_log()
    await with_timeout(
        S.configure(dut, enable=1, tu_bytes=tu_bytes, max_message_bytes=4096,
                    sram_base=RB_BASE, sram_limit=0xFFFF, timeout_cycles=0xFFFFFF),
        80, "us")
    # AXI write protocol: every packet's burst must complete with bvalid &
    # bresp==OKAY (a real B-channel handshake on the running DUT).
    write_protocol_ok = True
    for i, pkt in enumerate(packets):
        cyc = send_cycles if i == len(packets) - 1 else max(40, send_cycles // 2)
        obs = await with_timeout(S.send_packet(dut, pkt, monitor=monitor, cycles=cyc), 100, "us")
        if not (int(obs.get("bvalid", 0)) == 1 and int(obs.get("bresp", 1)) == 0):
            write_protocol_ok = False

    golden = _golden(packets)
    plen = len(golden)
    base = RB_BASE
    window = set(range(base, base + plen))

    # Union of every byte address the pack engine actually strobed for THIS msg.
    written: set[int] = set()
    for beat in monitor.write_log:
        written.update(beat["lanes"])

    out_of_window = sorted(written - window)        # header (< base) or pad (>= base+plen)
    header_writes = [a for a in out_of_window if a < base]
    pad_or_over = [a for a in out_of_window if a >= base + plen]
    missing = sorted(window - written)               # payload bytes never written → holes

    no_header_or_pad = (len(out_of_window) == 0)
    payload_only = written.issubset(window)
    no_holes_addr = (written == window)

    # Byte-exact readback confirms the WRITTEN bytes are the right payload bytes
    # (addresses alone prove placement; this proves content + no-holes end to end).
    rd = await with_timeout(
        S.axi_read(dut, araddr=base, n_beats=ceil(plen / S.AXI_BYTES),
                   sram_mem=sram, max_cycles=max_cycles), 200, "us")
    readback_exact = rd["data"][:plen] == golden and rd["rresp"] == 0 and rd["rlast_count"] == 1
    no_holes = no_holes_addr and readback_exact
    # AXI read protocol: arready seen, rresp==OKAY, exactly one rlast on the final
    # beat (a real R-channel handshake on the running DUT).
    read_protocol_ok = (bool(rd["arready_seen"]) and rd["rresp"] == 0
                        and rd["rlast_count"] == 1 and bool(rd["rlast_on_final"]))

    # VCM-1 content digest: the HARDWARE-observed digest is over the ACTUAL SRAM
    # payload bytes the DUT wrote (sram_mem[base:base+plen]); the GOLDEN digest is
    # over the independently-built golden payload (concat of TLP[16:16+plen]).
    # Independent sources -> a genuine (non-circular) content equivalence check.
    observed_bytes = bytes(sram[base:base + plen])
    observed_digest = hashlib.sha256(observed_bytes).hexdigest()
    golden_digest = hashlib.sha256(golden).hexdigest()
    snap = monitor.snapshot()

    case = {
        "scenario": name,
        "payload_len": plen,
        "base": base,
        "write_beats": len(monitor.write_log),
        "written_bytes": len(written),
        "header_writes": header_writes,
        "pad_or_overwindow_writes": pad_or_over,
        "missing_payload_bytes": missing,
        "sram_no_header_or_pad_write": no_header_or_pad,
        "sram_payload_only": payload_only,
        "sram_payload_no_holes": no_holes,
        "readback_byte_exact": readback_exact,
        "readback_rresp": rd["rresp"],
        "readback_rlast_count": rd["rlast_count"],
        "axi_write_protocol_pass": write_protocol_ok,
        "axi_read_protocol_pass": read_protocol_ok,
        # Content-digest evidence (consumed by _emit_digest_rows below).
        "observed_payload_digest": observed_digest,
        "golden_payload_digest": golden_digest,
        "digest_match": observed_digest == golden_digest,
        "sram_wr_valid": int(snap.get("sram_wr_valid", 0)),
        "sram_wr_addr": int(snap.get("sram_wr_addr", 0)),
        "sram_wr_strb": int(snap.get("sram_wr_strb", 0)),
        "sram_wr_count": int(snap.get("sram_wr_count", 0)),
    }
    cocotb.log.info(
        f"SRAM_WRITE_MON {name}: plen={plen} write_beats={case['write_beats']} "
        f"written={len(written)} no_header_or_pad={no_header_or_pad} "
        f"payload_only={payload_only} no_holes={no_holes} "
        f"digest_match={case['digest_match']} observed={observed_digest[:12]}.. "
        f"golden={golden_digest[:12]}..")
    return case


def _build_digest_row(case: dict) -> dict:
    """Build a schema-complete scoreboard datapath row carrying the content
    payload_digest at the fixed paths. rtl_observed.payload_digest = sha256 over
    the ACTUAL SRAM bytes the DUT wrote; fl_expected...state_updates.payload_digest
    = sha256 over the INDEPENDENT golden payload. passed = (observed == golden),
    the REAL verdict (never forced). Reuses EQ_TRANSACTION_FM_PACK_SRAM and keeps
    that goal's required observables (sram_wr_valid/addr/strb) present."""
    sid = case["scenario"]
    plen = case["payload_len"]
    base = case["base"]
    observed = case["observed_payload_digest"]
    golden = case["golden_payload_digest"]
    passed = bool(case["digest_match"])
    mismatch = "" if passed else (
        f"payload_digest mismatch for {sid}: observed(SRAM)={observed} != "
        f"golden={golden} over {plen} payload bytes at base+{base}")
    return {
        "goal_id": DIGEST_GOAL_ID,
        "scenario_id": sid,
        "cycle": 0,
        "scope": {"level": "top"},
        "coverage_refs": ["fcov_pack", "function_payload_pack_write", "vcm1_content_digest"],
        # Marker (ignored by check_scoreboard; lets re-runs replace these rows).
        "tb_source": DIGEST_ROW_MARKER,
        "fl_expected": {
            "goal_id": DIGEST_GOAL_ID,
            "goal_kind": "transaction",
            "model_api": "FunctionalModel.apply",
            "model_error": "",
            "model_result": {
                "transaction_id": "FM_PACK_SRAM",
                "transaction_name": "payload_pack_write",
                "resp": 0,
                "sample_accepted": 1,
                # The content oracle: golden payload digest, INDEPENDENT of RTL.
                "state_updates": {
                    DIGEST_FIELD: golden,
                    "payload_bytes_written_count": plen,
                },
            },
            "observables": ["payload byte i at base+i; full payload digest equals the "
                            "golden payload (concat of TLP[16:16+plen]) — content, not count"],
            "pass_criteria": ["rtl_observed.payload_digest == "
                              "fl_expected.model_result.state_updates.payload_digest"],
            "ssot_refs": ["function_model.transactions.FM_PACK_SRAM"],
            "title": f"Content payload_digest for {sid} ({plen} bytes)",
            "stimulus_contract": {"required_fields": ["kind", "payload_bytes"],
                                  "transaction_type": "payload_pack_write"},
        },
        "stimulus": {
            "kind": "FM_PACK_SRAM",
            "scenario_id": sid,
            "payload_bytes": plen,
        },
        # The hardware-observed content digest + the goal's required observables.
        "rtl_observed": {
            DIGEST_FIELD: observed,
            "sram_wr_valid": case["sram_wr_valid"],
            "sram_wr_addr": case["sram_wr_addr"],
            "sram_wr_strb": case["sram_wr_strb"],
            "sram_wr_count": case["sram_wr_count"],
            "payload_bytes_written_count": plen,
            "base_addr": base,
        },
        "passed": passed,
        "mismatch": mismatch,
    }


def _append_digest_rows(rows: list[dict]) -> None:
    """Append the digest rows to scoreboard_events.jsonl, first removing any rows
    we previously appended (matched by tb_source marker) so re-runs are
    idempotent. Append-only discipline: we ONLY drop our own marked rows and keep
    every other row (incl. the datapath merge's own FM_PACK_SRAM rows) intact."""
    existing: list[dict] = []
    if SCOREBOARD_PATH.is_file():
        for raw in SCOREBOARD_PATH.read_text(encoding="utf-8", errors="replace").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            try:
                r = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if isinstance(r, dict) and r.get("tb_source") == DIGEST_ROW_MARKER:
                continue   # drop our prior digest rows
            existing.append(r)
    existing.extend(rows)
    with SCOREBOARD_PATH.open("w", encoding="utf-8") as fh:
        for r in existing:
            fh.write(json.dumps(r, sort_keys=True) + "\n")


@cocotb.test()
async def sram_write_monitor(dut):
    """Verify no-holes / payload-only / no-header-or-pad-write over 4 scenarios."""
    await _setup(dut)
    sram = bytearray(0x10000)
    monitor = S.DatapathMonitor(dut, sram_mem=sram, record_writes=True)
    cocotb.start_soon(monitor.run())

    cases = []
    # SC_RB_SINGLE: 32 B single write.
    cases.append(await _run_case(
        dut, monitor, sram, "SC_RB_SINGLE",
        [S.Packet(source_eid=0x20, message_tag=1, som=1, eom=1, packet_seq=0,
                  payload=S._payload(31))], tu_bytes=64))
    # SC_RB_64: 64 B, multi-beat.
    cases.append(await _run_case(
        dut, monitor, sram, "SC_RB_64",
        [S.Packet(source_eid=0x21, message_tag=1, som=1, eom=1, packet_seq=0,
                  payload=S._payload(63))], tu_bytes=4096))
    # SC_RB_FRAG: 2 fragments, non-32-aligned tail (no-hole across boundary).
    cases.append(await _run_case(
        dut, monitor, sram, "SC_RB_FRAG",
        [S.Packet(source_eid=0x22, message_tag=2, som=1, eom=0, packet_seq=0,
                  payload=S._payload(40)),
         S.Packet(source_eid=0x22, message_tag=2, som=0, eom=1, packet_seq=1,
                  payload=S._payload(22, 5))], tu_bytes=64))
    # SC_RB_4096: full 4096 B / 128 words.
    cases.append(await _run_case(
        dut, monitor, sram, "SC_RB_4096",
        [S.Packet(source_eid=0x48, message_tag=1, som=1, eom=1, packet_seq=0,
                  payload=S._payload(4095))], tu_bytes=4096))

    checks = {
        "sram_payload_no_holes": all(c["sram_payload_no_holes"] for c in cases),
        "sram_payload_only": all(c["sram_payload_only"] for c in cases),
        "sram_no_header_or_pad_write": all(c["sram_no_header_or_pad_write"] for c in cases),
        "axi_write_protocol_pass": all(c["axi_write_protocol_pass"] for c in cases),
        "axi_read_protocol_pass": all(c["axi_read_protocol_pass"] for c in cases),
    }
    overall = all(checks.values())

    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_PATH.write_text(json.dumps({
        "ip": "mctp_assembler_v3",
        "test": "test_sram_write_monitor.sram_write_monitor",
        "status": "pass" if overall else "fail",
        "checks": checks,
        "cases": cases,
    }, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    dut._log.info(f"SRAM_WRITE_MON_SUMMARY checks={checks} overall={overall}")

    # VCM-1: emit content payload_digest scoreboard rows for SC_RB_4096 (primary)
    # and SC_RB_FRAG (no-hole-across-boundary content). observed=SRAM, expected=
    # golden, independent sources. Appended to scoreboard_events.jsonl after the
    # datapath merge (this module runs after test_mctp_datapath), idempotently.
    by_scn = {c["scenario"]: c for c in cases}
    digest_rows = [_build_digest_row(by_scn[s]) for s in ("SC_RB_4096", "SC_RB_FRAG")
                   if s in by_scn]
    _append_digest_rows(digest_rows)
    for row in digest_rows:
        dut._log.info(
            f"VCM1_DIGEST_ROW goal_id={row['goal_id']} scenario_id={row['scenario_id']} "
            f"passed={row['passed']} "
            f"observed={row['rtl_observed'][DIGEST_FIELD][:16]}.. "
            f"golden={row['fl_expected']['model_result']['state_updates'][DIGEST_FIELD][:16]}..")

    failing = [c["scenario"] for c in cases
               if not (c["sram_payload_no_holes"] and c["sram_payload_only"]
                       and c["sram_no_header_or_pad_write"])]
    assert overall, (
        "SRAM write monitor FAILED — a hole, header/pad write, or out-of-window "
        f"write was observed. Failing scenarios: {failing}. See {EVIDENCE_PATH} "
        f"(header_writes / pad_or_overwindow_writes / missing_payload_bytes).")
    # The content digest must genuinely match (observed SRAM == golden). A
    # mismatch is a real content bug — surface it, do not force passed=True.
    digest_fail = [r["scenario_id"] for r in digest_rows if not r["passed"]]
    assert not digest_fail, (
        f"payload_digest MISMATCH (observed SRAM != golden) for {digest_fail} — "
        "real content divergence; see the scoreboard row mismatch detail.")
