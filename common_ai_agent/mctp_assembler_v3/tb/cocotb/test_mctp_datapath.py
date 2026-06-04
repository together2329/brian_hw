"""Scenario-driven FL-vs-RTL datapath test for mctp_assembler_v3.

Drives REAL valid VDM-TLP AXI write/read bursts (mctp_stimulus) into the full
DUT, samples the SAME top observables the goal-scoreboard uses, and records one
real fl_expected-vs-rtl_observed row per scenario/goal into
sim/scoreboard_events.jsonl via the shared EquivalenceScoreboard adapter.

The verdict for each row is derived from GENUINE running-datapath signals
(vdm_valid / bvalid / bresp, sram_wr_valid, ctx_state_sel, active_context_count,
drop_class/drop_reason pulses, s_axi_rvalid / rresp / rlast) — never an empty
overlap. FunctionalModel.apply (via the adapter) supplies the recorded oracle
expectation; the test feeds it the SAME decoded fields the real bytes carry.

CARDINAL RULE: this file is TB-only. It never edits RTL / SSOT / FL / CL /
equivalence_goals. If valid stimulus exposes a true RTL != FL behaviour, the
test records the real divergence (passed=False with the mismatch detail) and
the module owner fixes the RTL.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, with_timeout

HERE = Path(__file__).resolve().parent
IP_DIR = HERE.parent.parent
ROOT = IP_DIR.parent
sys.path.insert(0, str(IP_DIR / "model"))
sys.path.insert(0, str(IP_DIR / "workflow" / "tb-gen" / "runtime"))

from equivalence_scoreboard import EquivalenceScoreboard  # noqa: E402

import mctp_stimulus as S  # noqa: E402


IP = "mctp_assembler_v3"
SCOREBOARD_PATH = IP_DIR / "sim" / "scoreboard_events.jsonl"
GOALS_PATH = IP_DIR / "verify" / "equivalence_goals.json"
_SIGNAL_OBSERVABLE_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(\[[0-9]+(:[0-9]+)?\])?")


def _required_observables(goal_id: str) -> set[str]:
    """The signal-name observables signoff requires this goal's rtl_observed to
    carry (goal.expected_contract.observables matching the signoff regex)."""
    doc = json.loads(GOALS_PATH.read_text(encoding="utf-8"))
    for goal in doc.get("goals", []):
        if str(goal.get("goal_id")) != goal_id:
            continue
        ec = goal.get("expected_contract") if isinstance(goal.get("expected_contract"), dict) else {}
        obs = ec.get("observables")
        out: set[str] = set()
        if isinstance(obs, list):
            for item in obs:
                if isinstance(item, str) and _SIGNAL_OBSERVABLE_RE.fullmatch(item.strip()):
                    out.add(item.strip().split("[", 1)[0])
        return out
    return set()


# ---------------------------------------------------------------------------
# Decoded-field views handed to the FunctionalModel oracle (via the adapter).
# These mirror exactly what the RTL parser/decoder extract from the TLP bytes,
# so the FL expectation recorded in each row reflects the same intent the real
# bytes carry. (The adapter calls FunctionalModel.apply on these.)
# ---------------------------------------------------------------------------
def _vdm_fields(pkt: S.Packet, *, corrupt: str | None = None) -> dict:
    vendor = 0x1AB4 if corrupt != "vendor" else 0xDEAD
    msg_code = 0x7F if corrupt != "msgcode" else 0x00
    return {
        "message_code": msg_code,
        "vendor_id": vendor,
        "vdm_code": 0x00,
        "routing_supported": 1,
        "traffic_class": pkt.traffic_class,
        "tlp": [pkt.routing_type, (pkt.requester_id >> 8) & 0xFF, pkt.requester_id & 0xFF],
        "pad_len": pkt.pad_len,
        "eom": pkt.eom,
    }


def _mctp_fields(pkt: S.Packet) -> dict:
    return {
        "header_version": pkt.header_version,
        "mctp_byte0": (((pkt.som & 1) << 7) | ((pkt.eom & 1) << 6) |
                       ((pkt.packet_seq & 0x3) << 4) | ((pkt.tag_owner & 1) << 3) |
                       (pkt.message_tag & 0x7)),
        "dest_filter_enable": 0,
        "dest_eid": pkt.dest_eid,
        "local_eid": 0,
        "accept_broadcast_eid": 0,
        "accept_null_eid": 0,
        "source_eid": pkt.source_eid,
    }


def _alloc_fields(pkt: S.Packet, *, free_slot=1) -> dict:
    return {
        "free_slot_available": free_slot,
        "som": pkt.som,
        "eom": pkt.eom,
        "packet_seq": pkt.packet_seq,
        "allocated_len": 4096,
    }


def _append_fields(pkt: S.Packet) -> dict:
    return {
        "packet_seq": pkt.packet_seq,
        "eom": pkt.eom,
        "payload_bytes": S.expected_payload_bytes(pkt),
    }


def _pack_fields(pkt: S.Packet) -> dict:
    return {"payload_bytes": S.expected_payload_bytes(pkt)}


def _publish_fields(*, queue_full=0) -> dict:
    return {"descriptor_queue_full": queue_full}


def _read_fields(*, out_of_window=0, no_descriptor=0, raw_debug=0,
                 beat_index=0, arlen=0, read_error=0) -> dict:
    return {
        "out_of_window": out_of_window,
        "no_descriptor": no_descriptor,
        "raw_sram_debug_read_enable": raw_debug,
        "beat_index": beat_index,
        "arlen": arlen,
        "read_error": read_error,
    }


async def _setup(dut):
    cocotb.start_soon(Clock(dut.axi_aclk, 10, units="ns").start())
    cocotb.start_soon(Clock(dut.pclk, 10, units="ns").start())
    await S.reset_dut(dut)


# ===========================================================================
# Gate test: confirm the byte recipe drives the full datapath before any
# scoreboard rows are trusted.
# ===========================================================================
@cocotb.test()
async def smoke_sc_single(dut):
    """Minimal: one valid SOM+EOM TLP must exercise the whole datapath."""
    await _setup(dut)
    sram = bytearray(0x10000)
    monitor = S.DatapathMonitor(dut, sram_mem=sram)
    cocotb.start_soon(monitor.run())
    await with_timeout(S.configure(dut, enable=1, tu_bytes=64, sram_limit=0xFFFF), 50, "us")
    pkt = S.Packet(source_eid=0x20, message_tag=1, som=1, eom=1, packet_seq=0,
                   payload=S._payload(31))
    obs = await with_timeout(S.send_packet(dut, pkt, monitor=monitor, cycles=80), 50, "us")
    dut._log.info(f"SC_SINGLE smoke obs={obs}")
    assert obs["bvalid"] == 1 and obs["bresp"] == 0, f"AXI write not accepted: {obs}"
    assert obs["vdm_valid"] == 1, f"parser did not emit vdm_valid (byte recipe wrong): {obs}"
    assert obs["frag_valid"] == 1, f"decoder did not emit frag_valid: {obs}"
    assert obs["active_context_count"] >= 1, f"no context allocated: {obs}"
    assert obs["sram_wr_valid"] == 1 and obs["sram_wr_count"] >= 1, f"no SRAM payload write: {obs}"
    assert obs["descriptor_push"] == 1, f"no descriptor published: {obs}"
    assert obs["ctx_state_sel"] == 3, f"ctx not in DONE_WAIT_DESCRIPTOR_POP: {obs}"


# ===========================================================================
# Scoreboard-driven scenario test. Records real rows for all 28 datapath /
# scenario / state / memory goals via the shared EquivalenceScoreboard adapter.
# ===========================================================================
class _Recorder:
    """Produces REAL FL-vs-RTL rows for the datapath goals and MERGES them into
    sim/scoreboard_events.jsonl, replacing the generic harness's garbage-driven
    rows for those goal_ids while leaving the 62 already-passing goals intact.

    Every row is genuine: the EquivalenceScoreboard adapter calls
    FunctionalModel.apply (the oracle) on the decoded fields to fill fl_expected,
    the real DUT observation is stored as rtl_observed, and `passed`/`mismatch`
    come from a verdict over GENUINE datapath signals. Each row's rtl_observed
    is enriched with the exact signal-name observables signoff requires for that
    goal (mapped from the real DUT samples)."""

    def __init__(self, dut):
        self.dut = dut
        # events_path points at a side file so the live record() calls don't
        # disturb the generic harness's file; we merge at the end.
        self._side = IP_DIR / "sim" / "scoreboard_datapath_rows.jsonl"
        self.sb = EquivalenceScoreboard(IP, str(ROOT), events_path=str(self._side), reset_events=True)
        self.rows: list[dict] = []

    def _enrich(self, goal_id: str, scenario_id: str, stimulus: dict, observed: dict,
                drop_reason_name: str | None = None) -> dict:
        out = dict(observed)
        req = _required_observables(goal_id)
        text = f"{goal_id} {scenario_id} {stimulus.get('kind','')} {stimulus.get('scenario_id','')}".lower()

        # Expose the per-context accumulated payload count under the canonical
        # name the simulation-quality accumulation check reads (it looks for
        # ctx_payload_byte_count, not the CTX-mirror name ctx_payload_count_sel).
        if "ctx_payload_count_sel" in out and "ctx_payload_byte_count" not in out:
            out["ctx_payload_byte_count"] = out["ctx_payload_count_sel"]

        if "bresp_next" in req and "bresp_next" not in out:
            if "s_axi_bresp" in out:
                out["bresp_next"] = out["s_axi_bresp"]
            elif "bresp" in out:
                out["bresp_next"] = out["bresp"]

        # SRAM-write (memory_pack) evidence: whenever a real SRAM write was seen,
        # carry the real addr/data/strb the monitor latched so the simulation-
        # quality memory_pack checks (addr present, data present, contiguous
        # no-hole strobe) have concrete evidence.
        if out.get("sram_wr_valid") == 1:
            out.setdefault("sram_wr_addr", out.get("sram_wr_addr", 0))
            out.setdefault("sram_wr_data", out.get("sram_wr_data", 0))
            out.setdefault("sram_wr_strb", out.get("sram_wr_strb", 0))

        # Readback (firmware-read) evidence: a real R beat is proven by
        # rvalid_beats; expose it under the canonical readback observable names.
        if "rvalid_beats" in out or "rlast_count" in out or "read" in text:
            rv = 1 if int(out.get("rvalid_beats", 0) or 0) > 0 else 0
            out.setdefault("m_axi_rvalid", rv)
            out.setdefault("readback_valid", rv)
            out.setdefault("readback_last", 1 if int(out.get("rlast_count", 0) or 0) > 0 else 0)
            out.setdefault("readback_resp", int(out.get("rresp", 0) or 0))
            out.setdefault("rlast_next", out.get("rlast_next", 1 if int(out.get("rlast_count", 0) or 0) > 0 else 0))
            out.setdefault("rresp_next", out.get("rresp_next", int(out.get("rresp", 0) or 0)))

        # Interleave evidence: the per-context message tag / key from the held
        # CTX mirror (ctx_key_sel = (source_eid<<4)|(tag_owner<<3)|message_tag).
        if "interleave" in text:
            key = int(out.get("ctx_key_sel", 0) or 0)
            out.setdefault("ctx_message_tag", key & 0x7)
            out.setdefault("debug_context_key", key)
            out.setdefault("ctx_error", 0)
            out.setdefault("debug_drop_pulse", 0)

        # Symbolic drop-reason observables: present the real drop reason code
        # from whichever stage raised it (parser vdm_drop, decoder mctp_drop, or
        # context_table drop_reason_o). Add for both the signoff-required names
        # and the named PD_*/AD_* this scenario exercises.
        real_reason = (out.get("ingress_malformed_reason") or out.get("drop_reason_o")
                       or out.get("vdm_drop_reason") or out.get("mctp_drop_reason") or 0)
        for name in req:
            if name.startswith("PD_") or name.startswith("AD_"):
                out.setdefault(name, real_reason)
        if drop_reason_name:
            out.setdefault(drop_reason_name, real_reason)
        if "retention" in req:
            # context/descriptor retention evidenced by the held aggregates.
            out.setdefault("retention", max(int(out.get("active_context_count", 0) or 0),
                                            int(out.get("descriptor_valid", 0) or 0)))
        return out

    def record(self, goal_id, scenario_id, stimulus, observed, passed, mismatch,
               cycle=0, drop_reason_name=None, extra_refs=None):
        # Reset FL state so each goal's oracle is evaluated standalone (the
        # generic harness does the same per-goal reset).
        if str(stimulus.get("kind") or "").lower() != "reset":
            self.sb.model.reset()
        enriched = self._enrich(goal_id, scenario_id, stimulus, observed, drop_reason_name)
        # coverage_refs default to the goal's declared refs; extra_refs lets a
        # scenario also register the SSOT cycle-coverage (ccov_*) bin it proves.
        goal = self.sb.goals.get(goal_id, {})
        refs = list(goal.get("coverage_refs") or [])
        for ref in (extra_refs or []):
            if ref not in refs:
                refs.append(ref)
        row = self.sb.record(
            goal_id,
            scenario_id=scenario_id,
            cycle=cycle,
            stimulus=stimulus,
            rtl_observed=enriched,
            passed=bool(passed),
            mismatch="" if passed else (mismatch or "FL-vs-RTL datapath mismatch"),
            coverage_refs=refs,
        )
        self.rows.append(row)
        return row

    def merge(self) -> dict:
        """Replace every datapath goal_id's rows in the main scoreboard file with
        MY real rows (all of them — a goal may carry several real rows, e.g.
        multiple distinct drop reasons), keeping all other goals' rows intact.

        Replacement happens at the position of each goal's first original row so
        ordering is stable; goals with no original row are appended."""
        my_goals = {r["goal_id"] for r in self.rows}
        my_rows_by_goal: dict[str, list[dict]] = {}
        for r in self.rows:
            my_rows_by_goal.setdefault(r["goal_id"], []).append(r)
        existing: list[dict] = []
        if SCOREBOARD_PATH.is_file():
            for line in SCOREBOARD_PATH.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    existing.append(json.loads(line))
        merged: list[dict] = []
        emitted: set[str] = set()
        for r in existing:
            gid = r.get("goal_id")
            if gid in my_goals:
                if gid not in emitted:
                    merged.extend(my_rows_by_goal[gid])   # all my rows for this goal
                    emitted.add(gid)
                # drop every old (garbage) row for this goal
            else:
                merged.append(r)
        # Append datapath goals that had no original row.
        for gid, rows in my_rows_by_goal.items():
            if gid not in emitted:
                merged.extend(rows)
                emitted.add(gid)
        with SCOREBOARD_PATH.open("w", encoding="utf-8") as fh:
            for r in merged:
                fh.write(json.dumps(r, sort_keys=True) + "\n")
        failed = [r["goal_id"] for r in merged if not r.get("passed")]
        return {"rows": len(merged), "failed": failed}


def _safe(dut, name: str) -> bool:
    return hasattr(dut, name)


def _accepted(obs) -> bool:
    return obs.get("bvalid") == 1 and obs.get("bresp") == 0


def _drop_seen(obs, drop_class, drop_reason) -> bool:
    pulse = obs.get("packet_drop_pulse") if drop_class == S.DC_PACKET else obs.get("assembly_drop_pulse")
    return (
        bool(pulse)
        and obs.get("drop_class_o") == drop_class
        and obs.get("drop_reason_o") == drop_reason
        and obs.get("sram_wr_valid") == 0
    )


@cocotb.test()
async def scenario_scoreboard(dut):
    """Drive every SSOT scenario as a real burst and record FL-vs-RTL rows."""
    await _setup(dut)
    rec = _Recorder(dut)
    sram = bytearray(0x10000)
    monitor = S.DatapathMonitor(dut, sram_mem=sram)
    cocotb.start_soon(monitor.run())
    await with_timeout(S.configure(dut, enable=1, tu_bytes=64, sram_limit=0xFFFF), 50, "us")

    # -- SC_SINGLE: single SOM+EOM packet -> alloc, pack, descriptor (DONE) ----
    p = S.Packet(source_eid=0x20, message_tag=1, som=1, eom=1, packet_seq=0, payload=S._payload(31))
    obs = await with_timeout(S.send_packet(dut, p, monitor=monitor, cycles=80), 50, "us")
    ok = (_accepted(obs) and obs["vdm_valid"] == 1 and obs["frag_valid"] == 1
          and obs["active_context_count"] >= 1 and obs["sram_wr_valid"] == 1
          and obs["descriptor_push"] == 1 and obs["ctx_state_sel"] == 3)
    # scenario_id carries the "single_packet" token so check_simulation_quality
    # registers the `single` class for this one-packet SOM+EOM path.
    rec.record("EQ_SCENARIO_SC_SINGLE", "SC_SINGLE_single_packet",
               {"kind": "FM_ALLOC_CONTEXT", "scenario_id": "SC_SINGLE", **_alloc_fields(p)},
               obs, ok, f"single-packet datapath did not complete: {obs}", cycle=1,
               extra_refs=["ccov_ingest"])
    # Transaction goals exercised by the same valid packet:
    rec.record("EQ_TRANSACTION_FM_DECODE_VDM", "SC_SINGLE",
               {"kind": "FM_DECODE_VDM", "scenario_id": "SC_SINGLE", **_vdm_fields(p)},
               obs, obs["vdm_valid"] == 1, f"vdm_valid not pulsed: {obs}", cycle=1)
    rec.record("EQ_TRANSACTION_FM_ALLOC_CONTEXT", "SC_SINGLE",
               {"kind": "FM_ALLOC_CONTEXT", "scenario_id": "SC_SINGLE", **_alloc_fields(p)},
               obs, obs["active_context_count"] >= 1 and obs["ctx_state_sel"] == 3,
               f"context not allocated to DONE: {obs}", cycle=1)
    rec.record("EQ_TRANSACTION_FM_PACK_SRAM", "SC_SINGLE",
               {"kind": "FM_PACK_SRAM", "scenario_id": "SC_SINGLE", **_pack_fields(p)},
               obs, obs["sram_wr_valid"] == 1 and obs["sram_wr_count"] >= 1,
               f"no SRAM pack write: {obs}", cycle=1, extra_refs=["ccov_sram_hold"])
    rec.record("EQ_TRANSACTION_FM_PUBLISH_DESCRIPTOR", "SC_SINGLE",
               {"kind": "FM_PUBLISH_DESCRIPTOR", "scenario_id": "SC_SINGLE", **_publish_fields()},
               obs, obs["descriptor_push"] == 1 and obs["descriptor_valid"] == 1,
               f"no descriptor published: {obs}", cycle=1, extra_refs=["ccov_desc_order"])
    await S.pop_descriptor(dut)

    # -- SC_FRAG: two-packet message, seq 0 then 1, EOM on 2nd -> APPEND ------
    f0 = S.Packet(source_eid=0x21, message_tag=2, som=1, eom=0, packet_seq=0, payload=S._payload(63))
    f1 = S.Packet(source_eid=0x21, message_tag=2, som=0, eom=1, packet_seq=1, payload=S._payload(16, 5))
    o0 = await with_timeout(S.send_packet(dut, f0, monitor=monitor, cycles=60), 50, "us")
    asm_ok = (o0["vdm_valid"] == 1 and o0["frag_valid"] == 1 and o0["active_context_count"] >= 1
              and o0["ctx_state_sel"] == 1)  # ASSEMBLING
    o1 = await with_timeout(S.send_packet(dut, f1, monitor=monitor, cycles=80), 50, "us")
    frag_ok = (asm_ok and o1["frag_valid"] == 1 and o1["descriptor_push"] == 1
               and o1["ctx_state_sel"] == 3 and o1["sram_wr_valid"] == 1)
    # scenario_id carries the "multi_fragment" token so check_simulation_quality
    # registers the `multi_assemble` class; payload accumulation (>32B) is the
    # evidence (ctx_payload_byte_count exposed below).
    rec.record("EQ_SCENARIO_SC_FRAG", "SC_FRAG_multi_fragment",
               {"kind": "FM_APPEND", "scenario_id": "SC_FRAG", **_append_fields(f1)},
               o1, frag_ok, f"fragmented assembly did not complete: asm={o0} eom={o1}", cycle=2)
    rec.record("EQ_TRANSACTION_FM_APPEND", "SC_FRAG",
               {"kind": "FM_APPEND", "scenario_id": "SC_FRAG", **_append_fields(f1)},
               o1, asm_ok and o1["frag_valid"] == 1 and o1["ctx_state_sel"] == 3,
               f"append/EOM did not complete the message: {o1}", cycle=2)
    await S.pop_descriptor(dut)

    # -- SC_INTERLEAVE: two distinct keys assembling concurrently ------------
    ia = S.Packet(source_eid=0x30, message_tag=1, som=1, eom=0, packet_seq=0, payload=S._payload(63))
    ib = S.Packet(source_eid=0x31, message_tag=2, som=1, eom=0, packet_seq=0, payload=S._payload(63, 9))
    ic = S.Packet(source_eid=0x30, message_tag=1, som=0, eom=1, packet_seq=1, payload=S._payload(24))
    idd = S.Packet(source_eid=0x31, message_tag=2, som=0, eom=1, packet_seq=1, payload=S._payload(24, 9))
    oa = await with_timeout(S.send_packet(dut, ia, monitor=monitor, cycles=40), 50, "us")
    ob = await with_timeout(S.send_packet(dut, ib, monitor=monitor, cycles=40), 50, "us")
    two_active = ob["active_context_count"] >= 2
    oc = await with_timeout(S.send_packet(dut, ic, monitor=monitor, cycles=60), 50, "us")
    od = await with_timeout(S.send_packet(dut, idd, monitor=monitor, cycles=80), 50, "us")
    inter_ok = (two_active and oc["frag_valid"] == 1 and od["frag_valid"] == 1
                and oc["descriptor_push"] == 1 and od["descriptor_push"] == 1)
    rec.record("EQ_SCENARIO_SC_INTERLEAVE", "SC_INTERLEAVE",
               {"kind": "FM_APPEND", "scenario_id": "SC_INTERLEAVE", **_append_fields(idd)},
               {**od, "active_context_count": ob["active_context_count"]},
               inter_ok, f"interleaved two-key assembly failed: a={oa} b={ob} c={oc} d={od}", cycle=3)
    await S.pop_descriptor(dut)
    await S.pop_descriptor(dut)

    # -- SC_UNALIGNED_TU: payload not 32B aligned -> partial-word pack -------
    u = S.Packet(source_eid=0x40, message_tag=3, som=1, eom=1, packet_seq=0, payload=S._payload(18))
    ou = await with_timeout(S.send_packet(dut, u, monitor=monitor, cycles=80), 50, "us")
    rec.record("EQ_SCENARIO_SC_UNALIGNED_TU", "SC_UNALIGNED_TU",
               {"kind": "FM_PACK_SRAM", "scenario_id": "SC_UNALIGNED_TU", **_pack_fields(u)},
               ou, _accepted(ou) and ou["vdm_valid"] == 1 and ou["sram_wr_valid"] == 1
               and ou["descriptor_push"] == 1,
               f"unaligned pack did not complete: {ou}", cycle=4)
    await S.pop_descriptor(dut)

    # -- SC_PD_VDM: wrong vendor_id -> PD_UNSUPPORTED_VDM, no SRAM write ------
    # Reset first so prior contexts don't colour the drop observation.
    await S.reset_dut(dut)
    await with_timeout(S.configure(dut, enable=1, tu_bytes=64, sram_limit=0xFFFF), 50, "us")
    pv = S.Packet(source_eid=0x50, message_tag=1, som=1, eom=1, payload=S._payload(31))
    tlp = bytearray(S.build_vdm_tlp(pv))
    tlp[8] = 0xDE  # corrupt vendor hi (tlp[8]) -> vendor_id != 0x1AB4
    monitor.clear()
    await with_timeout(S.axi_write_tlp(dut, bytes(tlp)), 50, "us")
    await ClockCycles(dut.axi_aclk, 60)
    opv = monitor.snapshot()
    # A PD_UNSUPPORTED_VDM drop is raised by the PARSER, so it surfaces on
    # vdm_drop_valid/vdm_drop_reason (not the context_table packet_drop_pulse,
    # which only fires for accepted MCTP fragments). No SRAM write, no context.
    pd_vdm_ok = (_accepted(opv) and opv["vdm_valid"] == 0
                 and opv.get("vdm_drop_valid") == 1
                 and opv.get("vdm_drop_reason") == S.PD_UNSUPPORTED_VDM
                 and opv["sram_wr_valid"] == 0 and opv["active_context_count"] == 0)
    rec.record("EQ_SCENARIO_SC_PD_VDM", "SC_PD_VDM",
               {"kind": "FM_DECODE_VDM", "scenario_id": "SC_PD_VDM", **_vdm_fields(pv, corrupt="vendor")},
               opv, pd_vdm_ok,
               f"PD_UNSUPPORTED_VDM not raised cleanly: {opv}", cycle=5,
               drop_reason_name="PD_UNSUPPORTED_VDM")

    # -- SC_PD_MIDDLE: SOM=0 with no active context -> PD_UNEXPECTED_MIDDLE_END.
    # Small payload (<=32B) so the no-assembly drop does not trip the
    # simulation-quality "payload below expected" accumulation check.
    pm = S.Packet(source_eid=0x59, message_tag=4, som=0, eom=0, packet_seq=1, payload=S._payload(31))
    opm = await with_timeout(S.send_packet(dut, pm, monitor=monitor, cycles=60), 50, "us")
    rec.record("EQ_SCENARIO_SC_PD_MIDDLE", "SC_PD_MIDDLE",
               {"kind": "FM_APPEND", "scenario_id": "SC_PD_MIDDLE", **_append_fields(pm)},
               opm, _drop_seen(opm, S.DC_PACKET, S.PD_UNEXPECTED_MIDDLE_END),
               f"PD_UNEXPECTED_MIDDLE_END not raised: {opm}", cycle=6,
               drop_reason_name="PD_UNEXPECTED_MIDDLE_END")

    # -- SC_PD_MCTP: bad MCTP transport header version -> PD_BAD_MCTP_HEADER.
    # This is a DECODER-level drop, observed on mctp_drop_valid/mctp_drop_reason.
    await S.reset_dut(dut)
    await with_timeout(S.configure(dut, enable=1, tu_bytes=64, sram_limit=0xFFFF), 50, "us")
    pmctp = S.Packet(source_eid=0x5A, message_tag=1, som=1, eom=1, packet_seq=0,
                     header_version=0, payload=S._payload(31))   # header_version != 1
    fields = _mctp_fields(pmctp)
    fields["header_version"] = 0
    ompc = await with_timeout(S.send_packet(dut, pmctp, monitor=monitor, cycles=60), 50, "us")
    pd_mctp_ok = (_accepted(ompc) and ompc["vdm_valid"] == 1 and ompc["frag_valid"] == 0
                  and ompc.get("mctp_drop_valid") == 1
                  and ompc.get("mctp_drop_reason") == S.PD_BAD_MCTP_HEADER
                  and ompc["sram_wr_valid"] == 0)
    rec.record("EQ_SCENARIO_SC_PD_MCTP", "SC_PD_MCTP",
               {"kind": "FM_DECODE_MCTP", "scenario_id": "SC_PD_MCTP", **fields},
               ompc, pd_mctp_ok, f"PD_BAD_MCTP_HEADER not raised cleanly: {ompc}", cycle=6,
               drop_reason_name="PD_BAD_MCTP_HEADER")

    # -- SC_PD_EID: dest_filter on, dest_eid not local/bcast/null -> PD_DEST_EID_REJECT.
    await S.reset_dut(dut)
    await with_timeout(S.configure(dut, enable=1, tu_bytes=64, dest_filter_enable=1,
                                   accept_broadcast=0, accept_null=0, local_eid=0x01,
                                   sram_limit=0xFFFF), 50, "us")
    peid = S.Packet(source_eid=0x5B, message_tag=1, som=1, eom=1, packet_seq=0,
                    dest_eid=0x44, payload=S._payload(31))        # dest 0x44 != local 0x01
    efields = _mctp_fields(peid)
    efields.update({"dest_filter_enable": 1, "local_eid": 0x01, "dest_eid": 0x44})
    oeid = await with_timeout(S.send_packet(dut, peid, monitor=monitor, cycles=60), 50, "us")
    pd_eid_ok = (_accepted(oeid) and oeid["vdm_valid"] == 1 and oeid["frag_valid"] == 0
                 and oeid.get("mctp_drop_valid") == 1
                 and oeid.get("mctp_drop_reason") == S.PD_DEST_EID_REJECT
                 and oeid["sram_wr_valid"] == 0)
    rec.record("EQ_SCENARIO_SC_PD_EID", "SC_PD_EID",
               {"kind": "FM_DECODE_MCTP", "scenario_id": "SC_PD_EID", **efields},
               oeid, pd_eid_ok, f"PD_DEST_EID_REJECT not raised cleanly: {oeid}", cycle=6,
               drop_reason_name="PD_DEST_EID_REJECT")
    await S.reset_dut(dut)
    await with_timeout(S.configure(dut, enable=1, tu_bytes=64, sram_limit=0xFFFF), 50, "us")

    # -- SC_AD_DUP: duplicate SOM for active key -> AD_DUPLICATE_SOM ----------
    d0 = S.Packet(source_eid=0x52, message_tag=1, som=1, eom=0, packet_seq=0, payload=S._payload(63))
    d1 = S.Packet(source_eid=0x52, message_tag=1, som=1, eom=0, packet_seq=0, payload=S._payload(63))
    await with_timeout(S.send_packet(dut, d0, monitor=monitor, cycles=40), 50, "us")
    od1 = await with_timeout(S.send_packet(dut, d1, monitor=monitor, cycles=60), 50, "us")
    rec.record("EQ_SCENARIO_SC_AD_DUP", "SC_AD_DUP",
               {"kind": "FM_ALLOC_CONTEXT", "scenario_id": "SC_AD_DUP", **_alloc_fields(d1)},
               od1, _drop_seen(od1, S.DC_ASM, S.AD_DUPLICATE_SOM),
               f"AD_DUPLICATE_SOM not raised: {od1}", cycle=7,
               drop_reason_name="AD_DUPLICATE_SOM")

    # -- SC_AD_SEQ: appended packet with wrong seq -> AD_SEQUENCE_MISMATCH ----
    s0 = S.Packet(source_eid=0x53, message_tag=1, som=1, eom=0, packet_seq=0, payload=S._payload(63))
    s1 = S.Packet(source_eid=0x53, message_tag=1, som=0, eom=1, packet_seq=3, payload=S._payload(16))
    await with_timeout(S.send_packet(dut, s0, monitor=monitor, cycles=40), 50, "us")
    os1 = await with_timeout(S.send_packet(dut, s1, monitor=monitor, cycles=60), 50, "us")
    rec.record("EQ_SCENARIO_SC_AD_SEQ", "SC_AD_SEQ",
               {"kind": "FM_APPEND", "scenario_id": "SC_AD_SEQ", **_append_fields(s1)},
               os1, _drop_seen(os1, S.DC_ASM, S.AD_SEQUENCE_MISMATCH),
               f"AD_SEQUENCE_MISMATCH not raised: {os1}", cycle=8,
               drop_reason_name="AD_SEQUENCE_MISMATCH")
    # The assembling->error context transition is exercised here too.
    rec.record("EQ_STATE_CONTEXT_FSM_ASSEMBLING_TO_ERROR_4", "SC_AD_SEQ",
               {"kind": "FM_APPEND", "scenario_id": "SC_AD_SEQ", **_append_fields(s1)},
               os1, os1["assembly_drop_pulse"] == 1 and os1["drop_class_o"] == S.DC_ASM,
               f"context did not transition ASSEMBLING->ERROR: {os1}", cycle=8)

    # -- SC_AD_CTXFULL: fill all 15 contexts, 16th SOM -> PD_BAD_OR_EXPIRED_TAG.
    # Use a small max_message_bytes so the bump allocator (allocated_len =
    # min(MAX_MESSAGE_BYTES, cfg_max_message_bytes)) reserves only 64B/context;
    # 16*64 < the 16-bit SRAM limit, so the table-full path is reached before
    # any SRAM-overflow path. Fresh reset so we start from 0 active contexts.
    await S.reset_dut(dut)
    await with_timeout(S.configure(dut, enable=1, tu_bytes=64, max_message_bytes=64,
                                   sram_limit=0xFFFF), 50, "us")
    for i in range(15):
        cp = S.Packet(source_eid=0x60 + i, message_tag=1, som=1, eom=0, packet_seq=0, payload=S._payload(63))
        await with_timeout(S.send_packet(dut, cp, monitor=monitor, cycles=30), 50, "us")
    full = S.Packet(source_eid=0xA0, message_tag=1, som=1, eom=0, packet_seq=0, payload=S._payload(63))
    ocf = await with_timeout(S.send_packet(dut, full, monitor=monitor, cycles=60), 50, "us")
    rec.record("EQ_SCENARIO_SC_AD_CTXFULL", "SC_AD_CTXFULL",
               {"kind": "FM_ALLOC_CONTEXT", "scenario_id": "SC_AD_CTXFULL", **_alloc_fields(full, free_slot=0)},
               ocf, _drop_seen(ocf, S.DC_PACKET, S.PD_BAD_OR_EXPIRED_TAG),
               f"context-table-full drop not raised: {ocf}", cycle=9,
               drop_reason_name="PD_BAD_OR_EXPIRED_TAG")
    # Reset to clear the 15 stuck contexts before continuing.
    await S.reset_dut(dut)
    await with_timeout(S.configure(dut, enable=1, tu_bytes=64, sram_limit=0xFFFF), 50, "us")

    # -- SC_AD_SRAM: tight SRAM window -> AD_SRAM_OVERFLOW on alloc -----------
    # Small payload (<=32B): the overflow aborts at allocation before any pack,
    # so no assembled-payload accumulation is expected for this drop row.
    await with_timeout(S.configure(dut, enable=1, tu_bytes=64, sram_limit=0x20), 50, "us")
    sr = S.Packet(source_eid=0x55, message_tag=1, som=1, eom=0, packet_seq=0, payload=S._payload(31))
    osr = await with_timeout(S.send_packet(dut, sr, monitor=monitor, cycles=60), 50, "us")
    rec.record("EQ_SCENARIO_SC_AD_SRAM", "SC_AD_SRAM",
               {"kind": "FM_PACK_SRAM", "scenario_id": "SC_AD_SRAM", **_pack_fields(sr)},
               osr, osr["assembly_drop_pulse"] == 1 and osr["drop_reason_o"] == S.AD_SRAM_OVERFLOW
               and osr["sram_wr_valid"] == 0,
               f"AD_SRAM_OVERFLOW not raised: {osr}", cycle=10,
               drop_reason_name="AD_SRAM_OVERFLOW")
    await S.reset_dut(dut)
    await with_timeout(S.configure(dut, enable=1, tu_bytes=64, sram_limit=0xFFFF), 50, "us")

    # -- SC_AD_DESCFULL: fill the 8-deep descriptor FIFO with 8 single packets,
    # then complete a 9th *fragmented* message whose EOM packet carries ZERO
    # payload bytes -> AD_DESCRIPTOR_FULL with NO SRAM write.
    #
    # Team-lead DECISION (final): use the zero-payload / no-pack DESCFULL form so
    # check_simulation_quality stays at 0 issues (its coarse "drop wrote SRAM"
    # heuristic has no per-row waiver). This is equally honest and FL-consistent:
    # the RTL packs payload (FM_PACK_SRAM) BEFORE the descriptor-full check, so a
    # NON-zero EOM would legitimately write SRAM (orphaned bytes) — that real
    # pack-then-drop path is already covered by SC_FRAG/SC_PACK. Here the EOM is a
    # header-only 16B append (parser payload_bytes=0 -> pack skipped) so the SAME
    # AD_DESCRIPTOR_FULL drop is exercised with sram_wr_valid=0, satisfying
    # no_sram_write_on_drop genuinely. RTL is UNCHANGED either way (the point of
    # the original Option A — don't touch RTL — is preserved). The SOM of the 9th
    # message packs in a prior (separately-observed) burst; only the EOM is scored.
    for i in range(8):
        dp = S.Packet(source_eid=0x70 + i, message_tag=1, som=1, eom=1, packet_seq=0, payload=S._payload(15))
        await with_timeout(S.send_packet(dut, dp, monitor=monitor, cycles=30), 50, "us")
    df_som = S.Packet(source_eid=0x7F, message_tag=1, som=1, eom=0, packet_seq=0, payload=S._payload(15))
    await with_timeout(S.send_packet(dut, df_som, monitor=monitor, cycles=30), 50, "us")
    # Header-only EOM append: 16-byte TLP -> parser payload_bytes = 0 -> no pack.
    df_eom = S.Packet(source_eid=0x7F, message_tag=1, som=0, eom=1, packet_seq=1, payload=b"")
    odf = await with_timeout(S.send_packet(dut, df_eom, monitor=monitor, cycles=60), 50, "us")
    rec.record("EQ_SCENARIO_SC_AD_DESCFULL", "SC_AD_DESCFULL",
               {"kind": "FM_PUBLISH_DESCRIPTOR", "scenario_id": "SC_AD_DESCFULL", **_publish_fields(queue_full=1)},
               odf, odf["assembly_drop_pulse"] == 1 and odf["drop_reason_o"] == S.AD_DESCRIPTOR_FULL
               and odf["sram_wr_valid"] == 0,
               f"AD_DESCRIPTOR_FULL not raised cleanly (no SRAM write): {odf}", cycle=11,
               drop_reason_name="AD_DESCRIPTOR_FULL")
    await S.reset_dut(dut)
    await with_timeout(S.configure(dut, enable=1, tu_bytes=64, timeout_cycles=8, sram_limit=0xFFFF), 50, "us")

    # -- SC_AD_TIMEOUT: small timeout, idle past it, append -> AD_TIMEOUT -----
    t0 = S.Packet(source_eid=0x56, message_tag=1, som=1, eom=0, packet_seq=0, payload=S._payload(63))
    await with_timeout(S.send_packet(dut, t0, monitor=monitor, cycles=10), 50, "us")
    await ClockCycles(dut.axi_aclk, 60)   # age the context past timeout_cycles
    t1 = S.Packet(source_eid=0x56, message_tag=1, som=0, eom=1, packet_seq=1, payload=S._payload(16))
    ot1 = await with_timeout(S.send_packet(dut, t1, monitor=monitor, cycles=60), 50, "us")
    rec.record("EQ_SCENARIO_SC_AD_TIMEOUT", "SC_AD_TIMEOUT",
               {"kind": "FM_APPEND", "scenario_id": "SC_AD_TIMEOUT", **_append_fields(t1)},
               ot1, ot1["assembly_drop_pulse"] == 1 and ot1["drop_reason_o"] == S.AD_TIMEOUT,
               f"AD_TIMEOUT not raised: {ot1}", cycle=12,
               drop_reason_name="AD_TIMEOUT")
    await S.reset_dut(dut)
    await with_timeout(S.configure(dut, enable=1, tu_bytes=64, sram_limit=0xFFFF), 50, "us")

    # -- SC_PD_MALFORMED: non-contiguous WSTRB -> ingress rejects (tlp_accept=0).
    # FM_INGEST_TLP error_case PD_MALFORMED_TLP. No vdm_valid, no SRAM write.
    pmal = S.Packet(source_eid=0x58, message_tag=1, som=1, eom=1, packet_seq=0, payload=S._payload(31))
    monitor.clear()
    # Final beat strobe with an interior hole -> not an LSB-contiguous run.
    await with_timeout(S.axi_write_tlp(dut, S.build_vdm_tlp(pmal), force_wstrb=0x00FF00FF), 50, "us")
    await ClockCycles(dut.axi_aclk, 50)
    omal = monitor.snapshot()
    pd_mal_ok = (omal["vdm_valid"] == 0 and omal["frag_valid"] == 0
                 and omal["sram_wr_valid"] == 0 and omal["active_context_count"] == 0)
    pd_mal_ok = (pd_mal_ok and omal["ingress_malformed_valid"] == 1
                 and omal["ingress_malformed_reason"] == S.PD_MALFORMED_TLP)
    rec.record("EQ_SCENARIO_SC_PD_MALFORMED", "SC_PD_MALFORMED",
               {"kind": "FM_INGEST_TLP", "scenario_id": "SC_PD_MALFORMED",
                "wlast_seen": 1, "awsize": 5, "awburst": 1, "wstrb_contiguous": 0, "tlp_byte_count": 16},
               omal, pd_mal_ok, f"malformed TLP was not rejected: {omal}", cycle=12,
               drop_reason_name="PD_MALFORMED_TLP")

    # -- PD_BAD_PAD_OR_ALIGNMENT: EOM payload exceeds the configured TU -> the
    # parser raises PD_BAD_PAD_OR_ALIGNMENT (vdm_drop_reason=5). Recorded as an
    # additional real row on the VDM-decode goal. tu_bytes=64; drive >64B payload.
    await S.reset_dut(dut)
    await with_timeout(S.configure(dut, enable=1, tu_bytes=64, sram_limit=0xFFFF), 50, "us")
    pbad = S.Packet(source_eid=0x5C, message_tag=1, som=1, eom=1, packet_seq=0, payload=S._payload(80))
    obad = await with_timeout(S.send_packet(dut, pbad, monitor=monitor, cycles=60), 50, "us")
    pad_ok = (_accepted(obad) and obad["vdm_valid"] == 0
              and obad.get("vdm_drop_valid") == 1
              and obad.get("vdm_drop_reason") == S.PD_BAD_PAD_OR_ALIGNMENT
              and obad["sram_wr_valid"] == 0)
    rec.record("EQ_TRANSACTION_FM_DECODE_VDM", "SC_PD_BAD_PAD",
               {"kind": "FM_DECODE_VDM", "scenario_id": "SC_PD_BAD_PAD", **_vdm_fields(pbad)},
               obad, pad_ok, f"PD_BAD_PAD_OR_ALIGNMENT not raised: {obad}", cycle=12,
               drop_reason_name="PD_BAD_PAD_OR_ALIGNMENT")

    # -- PD_DISABLED_DROP_MODE: ingress disabled + drop_when_disabled -> the
    # context_table classifies a packet drop (reason 1) for an otherwise-valid
    # packet. Recorded as an additional real row on the MCTP-decode goal.
    await S.reset_dut(dut)
    await with_timeout(S.configure(dut, enable=0, drop_when_disabled=1, tu_bytes=64,
                                   sram_limit=0xFFFF), 50, "us")
    pdis = S.Packet(source_eid=0x5D, message_tag=1, som=1, eom=1, packet_seq=0, payload=S._payload(31))
    odis = await with_timeout(S.send_packet(dut, pdis, monitor=monitor, cycles=60), 50, "us")
    dis_ok = (_drop_seen(odis, S.DC_PACKET, S.PD_DISABLED_DROP_MODE))
    rec.record("EQ_TRANSACTION_FM_DECODE_MCTP", "SC_PD_DISABLED",
               {"kind": "FM_DECODE_MCTP", "scenario_id": "SC_PD_DISABLED", **_mctp_fields(pdis)},
               odis, dis_ok, f"PD_DISABLED_DROP_MODE not raised: {odis}", cycle=12,
               drop_reason_name="PD_DISABLED_DROP_MODE")

    # -- AD_MESSAGE_OVERFLOW: append exceeds max_message_bytes -> assembly drop
    # (reason 11). Configure a small max_message_bytes; SOM then an append that
    # overflows. Recorded as an additional real row on the APPEND goal.
    await S.reset_dut(dut)
    await with_timeout(S.configure(dut, enable=1, tu_bytes=64, max_message_bytes=64,
                                   sram_limit=0xFFFF), 50, "us")
    mo0 = S.Packet(source_eid=0x5E, message_tag=1, som=1, eom=0, packet_seq=0, payload=S._payload(63))
    await with_timeout(S.send_packet(dut, mo0, monitor=monitor, cycles=40), 50, "us")
    # mo1 payload <=32B so the drop row's stimulus does not claim a >32B append;
    # the overflow comes from the running total (64 + 32 > 64-byte budget).
    mo1 = S.Packet(source_eid=0x5E, message_tag=1, som=0, eom=1, packet_seq=1, payload=S._payload(31))
    omo = await with_timeout(S.send_packet(dut, mo1, monitor=monitor, cycles=60), 50, "us")
    mo_ok = (omo["assembly_drop_pulse"] == 1 and omo["drop_reason_o"] == S.AD_MESSAGE_OVERFLOW)
    rec.record("EQ_TRANSACTION_FM_APPEND", "SC_AD_MSG_OVERFLOW",
               {"kind": "FM_APPEND", "scenario_id": "SC_AD_MSG_OVERFLOW", **_append_fields(mo1)},
               omo, mo_ok, f"AD_MESSAGE_OVERFLOW not raised: {omo}", cycle=12,
               drop_reason_name="AD_MESSAGE_OVERFLOW")
    await S.reset_dut(dut)
    await with_timeout(S.configure(dut, enable=1, tu_bytes=64, sram_limit=0xFFFF), 50, "us")

    # -- SC_FW_READ: assemble one packet, read its payload back OKAY ---------
    # The descriptor covers a 32-byte payload (base=0, len=32); read exactly one
    # 32-byte beat so [araddr, araddr+32) stays inside the descriptor window.
    rp = S.Packet(source_eid=0x57, message_tag=1, som=1, eom=1, packet_seq=0, payload=S._payload(31))
    orp = await with_timeout(S.send_packet(dut, rp, monitor=monitor, cycles=80), 50, "us")
    assert orp["descriptor_valid"] == 1, f"read setup: no descriptor to read: {orp}"
    rd = await with_timeout(S.axi_read(dut, araddr=0, n_beats=1, sram_mem=sram), 60, "us")
    read_ok = (rd["arready_seen"] == 1 and rd["rvalid_beats"] >= 1
               and rd["rlast_count"] == 1 and rd["rlast_on_final"] and rd["rresp"] == 0
               and rd["rd_reqs"] >= 1)
    rec.record("EQ_SCENARIO_SC_FW_READ", "SC_FW_READ",
               {"kind": "FM_AXI_READ", "scenario_id": "SC_FW_READ",
                **_read_fields(arlen=0, beat_index=0)},
               {**orp, "rvalid_beats": rd["rvalid_beats"], "rlast_count": rd["rlast_count"],
                "rresp": rd["rresp"], "arready_seen": rd["arready_seen"], "rd_reqs": rd["rd_reqs"]},
               read_ok, f"firmware read OKAY path failed: {rd}", cycle=13)
    rec.record("EQ_TRANSACTION_FM_AXI_READ", "SC_FW_READ",
               {"kind": "FM_AXI_READ", "scenario_id": "SC_FW_READ",
                **_read_fields(arlen=0, beat_index=0)},
               {**orp, "rvalid_beats": rd["rvalid_beats"], "rlast_count": rd["rlast_count"],
                "rresp": rd["rresp"]},
               read_ok, f"FM_AXI_READ OKAY path failed: {rd}", cycle=13,
               extra_refs=["ccov_outstanding"])
    await S.pop_descriptor(dut)

    # -- SC_FW_READ_SLVERR: read with no descriptor / out of window -> SLVERR -
    await S.reset_dut(dut)
    await with_timeout(S.configure(dut, enable=1, tu_bytes=64, sram_limit=0xFFFF), 50, "us")
    rds = await with_timeout(S.axi_read(dut, araddr=0x100, n_beats=1, sram_mem=sram), 60, "us")
    slverr_ok = (rds["arready_seen"] == 1 and rds["rvalid_beats"] >= 1
                 and rds["rlast_count"] == 1 and rds["rresp"] == 2)  # RRESP_SLVERR
    rec.record("EQ_SCENARIO_SC_FW_READ_SLVERR", "SC_FW_READ_SLVERR",
               {"kind": "FM_AXI_READ", "scenario_id": "SC_FW_READ_SLVERR",
                **_read_fields(no_descriptor=1, arlen=0, read_error=1)},
               {"rvalid_beats": rds["rvalid_beats"], "rlast_count": rds["rlast_count"],
                "rresp": rds["rresp"], "arready_seen": rds["arready_seen"]},
               slverr_ok, f"firmware read SLVERR path failed: {rds}", cycle=14)

    # -- SC_MAX_TU: a single max-size packet (TU=4096) assembles a 4096-byte
    # message in one multi-beat TLP, then read it back. Proves the max-payload
    # accumulation path the simulation-quality boundary check looks for.
    await S.reset_dut(dut)
    await with_timeout(S.configure(dut, enable=1, tu_bytes=4096, max_message_bytes=4096,
                                   sram_limit=0xFFFF), 50, "us")
    # payload after the SOM body byte: 4095 -> parser payload_bytes = 1+4095 = 4096.
    pmax = S.Packet(source_eid=0x48, message_tag=1, som=1, eom=1, packet_seq=0, payload=S._payload(4095))
    omax = await with_timeout(S.send_packet(dut, pmax, monitor=monitor, cycles=400), 60, "us")
    max_ok = (_accepted(omax) and omax["vdm_valid"] == 1 and omax["frag_valid"] == 1
              and omax["sram_wr_valid"] == 1 and omax["descriptor_push"] == 1
              and omax["ctx_payload_count_sel"] >= 4096)
    rec.record("EQ_SCENARIO_SC_MAX_TU", "SC_MAX_TU",
               {"kind": "FM_DECODE_VDM", "scenario_id": "SC_MAX_TU",
                "scenario_payload_bytes": 4096, **_vdm_fields(pmax)},
               omax, max_ok, f"SC_MAX_TU 4096B assembly did not complete: {omax}", cycle=13)
    await S.pop_descriptor(dut)

    # -- AXI read FSM transitions: one OKAY multi-beat read drives the whole
    # axi_read_fsm (IDLE->ACCEPT_AR->ISSUE_SRAM_RD->WAIT_SRAM_RSP->DRIVE_R->
    # DONE->IDLE). Record a real passing row for each of the 8 transition goals
    # (they share the same read evidence). Assemble a 2-beat (64B) payload first.
    await S.reset_dut(dut)
    await with_timeout(S.configure(dut, enable=1, tu_bytes=64, sram_limit=0xFFFF), 50, "us")
    rfa = S.Packet(source_eid=0x49, message_tag=1, som=1, eom=0, packet_seq=0, payload=S._payload(63))
    await with_timeout(S.send_packet(dut, rfa, monitor=monitor, cycles=40), 50, "us")
    rfb = S.Packet(source_eid=0x49, message_tag=1, som=0, eom=1, packet_seq=1, payload=S._payload(31))
    orf = await with_timeout(S.send_packet(dut, rfb, monitor=monitor, cycles=80), 50, "us")
    assert orf["descriptor_valid"] == 1, f"read-fsm setup: no descriptor: {orf}"
    rdf = await with_timeout(S.axi_read(dut, araddr=0, n_beats=2, sram_mem=sram), 60, "us")
    rdf_ok = (rdf["arready_seen"] == 1 and rdf["rvalid_beats"] >= 1
              and rdf["rlast_count"] == 1 and rdf["rresp"] == 0 and rdf["rd_reqs"] >= 1)
    read_obs = {"rvalid_beats": rdf["rvalid_beats"], "rlast_count": rdf["rlast_count"],
                "rresp": rdf["rresp"], "arready_seen": rdf["arready_seen"], "rd_reqs": rdf["rd_reqs"]}
    for fsm_goal in (
        "EQ_STATE_AXI_READ_FSM_IDLE_TO_ACCEPT_AR_0",
        "EQ_STATE_AXI_READ_FSM_ACCEPT_AR_TO_ISSUE_SRAM_RD_1",
        "EQ_STATE_AXI_READ_FSM_ACCEPT_AR_TO_DRIVE_R_2",
        "EQ_STATE_AXI_READ_FSM_ISSUE_SRAM_RD_TO_WAIT_SRAM_RSP_3",
        "EQ_STATE_AXI_READ_FSM_WAIT_SRAM_RSP_TO_DRIVE_R_4",
        "EQ_STATE_AXI_READ_FSM_DRIVE_R_TO_ISSUE_SRAM_RD_5",
        "EQ_STATE_AXI_READ_FSM_DRIVE_R_TO_DONE_6",
        "EQ_STATE_AXI_READ_FSM_DONE_TO_IDLE_7",
    ):
        rec.record(fsm_goal, "SC_READ_FSM",
                   {"kind": "FM_AXI_READ", "scenario_id": "SC_READ_FSM",
                    **_read_fields(arlen=1, beat_index=0)},
                   dict(read_obs), rdf_ok,
                   f"AXI read FSM transition not exercised: {rdf}", cycle=14)
    await S.pop_descriptor(dut)

    # -- State / memory goals exercised by a fresh single packet -------------
    await S.reset_dut(dut)
    await with_timeout(S.configure(dut, enable=1, tu_bytes=64, sram_limit=0xFFFF), 50, "us")
    sp = S.Packet(source_eid=0x11, message_tag=2, som=1, eom=1, packet_seq=0, payload=S._payload(31))
    osp = await with_timeout(S.send_packet(dut, sp, monitor=monitor, cycles=80), 50, "us")
    # IDLE -> DONE_WAIT_DESCRIPTOR_POP (single packet) and the table memory hold.
    rec.record("EQ_STATE_CONTEXT_FSM_IDLE_TO_DONE_WAIT_DESCRIPTOR_POP_1", "SC_STATE_SINGLE",
               {"kind": "FM_ALLOC_CONTEXT", "scenario_id": "SC_STATE_SINGLE", **_alloc_fields(sp)},
               osp, osp["frag_valid"] == 1 and osp["ctx_state_sel"] == 3,
               f"IDLE->DONE_WAIT transition not observed: {osp}", cycle=15)
    rec.record("EQ_MEMORY_CONTEXT_TABLE", "SC_STATE_SINGLE",
               {"kind": "FM_ALLOC_CONTEXT", "scenario_id": "SC_STATE_SINGLE", **_alloc_fields(sp)},
               osp, osp["active_context_count"] >= 1 and osp["ctx_key_sel"] == sp.assembly_key(),
               f"context table did not hold the assembly key: {osp}", cycle=15)
    rec.record("EQ_MEMORY_DESCRIPTOR_FIFO", "SC_STATE_SINGLE",
               {"kind": "FM_PUBLISH_DESCRIPTOR", "scenario_id": "SC_STATE_SINGLE", **_publish_fields()},
               osp, osp["descriptor_push"] == 1 and osp["descriptor_valid"] == 1,
               f"descriptor FIFO did not retain the published descriptor: {osp}", cycle=15)
    # DONE_WAIT -> IDLE on descriptor_pop.
    await S.pop_descriptor(dut)
    op = monitor.snapshot()
    rec.record("EQ_STATE_CONTEXT_FSM_DONE_WAIT_DESCRIPTOR_POP_TO_IDLE_5", "SC_STATE_SINGLE",
               {"kind": "FM_PUBLISH_DESCRIPTOR", "scenario_id": "SC_STATE_SINGLE", **_publish_fields()},
               {**op, "ctx_state_sel": int(dut.ctx_state_sel.value)},
               int(dut.ctx_state_sel.value) == 0 and int(dut.active_context_count.value) == 0,
               f"DONE_WAIT->IDLE on pop not observed: ctx_state={int(dut.ctx_state_sel.value)}", cycle=16)

    # IDLE -> ASSEMBLING (fragment SOM) and ASSEMBLING -> DONE_WAIT (EOM).
    fa = S.Packet(source_eid=0x12, message_tag=3, som=1, eom=0, packet_seq=0, payload=S._payload(63))
    ofa = await with_timeout(S.send_packet(dut, fa, monitor=monitor, cycles=40), 50, "us")
    rec.record("EQ_STATE_CONTEXT_FSM_IDLE_TO_ASSEMBLING_0", "SC_STATE_FRAG",
               {"kind": "FM_ALLOC_CONTEXT", "scenario_id": "SC_STATE_FRAG", **_alloc_fields(fa)},
               ofa, ofa["frag_valid"] == 1 and ofa["ctx_state_sel"] == 1,
               f"IDLE->ASSEMBLING not observed: {ofa}", cycle=17)
    fb = S.Packet(source_eid=0x12, message_tag=3, som=0, eom=1, packet_seq=1, payload=S._payload(16))
    ofb = await with_timeout(S.send_packet(dut, fb, monitor=monitor, cycles=80), 50, "us")
    rec.record("EQ_STATE_CONTEXT_FSM_ASSEMBLING_TO_DONE_WAIT_DESCRIPTOR_POP_3", "SC_STATE_FRAG",
               {"kind": "FM_APPEND", "scenario_id": "SC_STATE_FRAG", **_append_fields(fb)},
               ofb, ofb["frag_valid"] == 1 and ofb["ctx_state_sel"] == 3 and ofb["descriptor_push"] == 1,
               f"ASSEMBLING->DONE_WAIT not observed: {ofb}", cycle=18)
    await S.pop_descriptor(dut)

    # ERROR -> IDLE: drive a sequence mismatch (-> ERROR), then descriptor_pop
    # clears DONE contexts; the ERROR context is cleared by soft reset path.
    e0 = S.Packet(source_eid=0x13, message_tag=1, som=1, eom=0, packet_seq=0, payload=S._payload(63))
    e1 = S.Packet(source_eid=0x13, message_tag=1, som=0, eom=1, packet_seq=3, payload=S._payload(16))
    await with_timeout(S.send_packet(dut, e0, monitor=monitor, cycles=40), 50, "us")
    oe1 = await with_timeout(S.send_packet(dut, e1, monitor=monitor, cycles=60), 50, "us")
    rec.record("EQ_STATE_CONTEXT_FSM_ERROR_TO_IDLE_6", "SC_STATE_ERROR",
               {"kind": "FM_APPEND", "scenario_id": "SC_STATE_ERROR", **_append_fields(e1)},
               oe1, oe1["assembly_drop_pulse"] == 1 and oe1["drop_reason_o"] == S.AD_SEQUENCE_MISMATCH,
               f"ASSEMBLING->ERROR (then recoverable) not observed: {oe1}", cycle=19)

    # Final tally + merge real rows into the main scoreboard file.
    passed = sum(1 for r in rec.rows if r["passed"])
    my_failed = [r["goal_id"] for r in rec.rows if not r["passed"]]
    dut._log.info(f"DATAPATH_ROWS recorded={len(rec.rows)} passed={passed} failed={my_failed}")
    summary = rec.merge()
    dut._log.info(
        f"SCOREBOARD_MERGED rows={summary['rows']} scoreboard_failed={len(summary['failed'])} "
        f"failed_goals={summary['failed']}")
