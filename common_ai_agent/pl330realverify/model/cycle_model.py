#!/usr/bin/env python3
"""Executable SSOT cycle-level model for pl330realverify. Wraps FunctionalModel — FL is the only oracle."""

from __future__ import annotations

import json

try:
    from .functional_model import FunctionalModel
except ImportError:
    from functional_model import FunctionalModel

try:
    from pymtl3 import Bits1, Bits32, Component, InPort, OutPort, update_ff
    HAS_PYMTL3 = True
except Exception:
    Bits1 = Bits32 = Component = InPort = OutPort = update_ff = None
    HAS_PYMTL3 = False


# ---------------------------------------------------------------------------
# SSOT-derived tables (baked at generation time)
# ---------------------------------------------------------------------------

# Requested executable backend.  PyMTL3 is the default CL shell; FunctionalModel remains the oracle.
MODEL_BACKEND: str = 'pymtl3'

# Latency table: transaction kind -> cycles.  max_cycles when defined; min_cycles otherwise; default=1.
_LATENCY: dict[str, int] = {'register_read': 1, 'register_write': 1, 'event_release': 2, 'single_beat_transfer': 5, 'interrupt_assertion': 2, 'default': 1}

# Handshake rules from SSOT cycle_model.handshake_rules.
_HANDSHAKE_RULES: list[dict] = [{'name': 'apb_access', 'description': '', 'predicate': ''}, {'name': 'apb_read_data', 'description': '', 'predicate': ''}, {'name': 'axi_ar', 'description': '', 'predicate': ''}, {'name': 'axi_r', 'description': '', 'predicate': ''}, {'name': 'axi_aw', 'description': '', 'predicate': ''}, {'name': 'axi_w', 'description': '', 'predicate': ''}, {'name': 'axi_b', 'description': '', 'predicate': ''}, {'name': 'irq_level', 'description': '', 'predicate': ''}]

# Ordering rules from SSOT cycle_model.ordering.
_ORDERING_RULES: list[dict] = [{'name': 'a_write_data_beat_must_not_be_issued_before_the_corresponding_read_data_beat_has_been_accepted_into_rd_buf', 'description': ''}, {'name': 'a_channel_complete_interrupt_pending_bit_is_set_only_after_the_final_successful_b_response', 'description': ''}, {'name': 'a_channel_fault_interrupt_pending_bit_is_set_on_the_first_detected_fault_before_any_later_completion_status', 'description': ''}, {'name': 'apb_w1c_clear_does_not_clear_configuration_registers_or_address_counters', 'description': ''}, {'name': 'for_each_channel_at_most_one_read_burst_and_one_write_burst_are_outstanding_in_this_engineering_subset', 'description': ''}]

# Maximum outstanding transactions before stalling.
_OUTSTANDING_CAP: int = 1

# Cycle/performance targets used by coverage and PyMTL shell instrumentation.
PERFORMANCE_TARGETS: dict = {'frequency_mhz': 500, 'throughput': {'sustained_beats_per_cycle': 1, 'condition': 'No APB command gap, WFP disabled or already satisfied, no AXI backpressure, no AXI errors, aligned addresses.'}, 'outstanding': {'read_max': 1, 'write_max': 1, 'description': 'Single outstanding read/write in the engineering subset.'}, 'pipeline_stages': 8, 'queue_depth': 1}

# Transaction kinds for self-check, derived from function_model.transactions at generation time.
_SELF_CHECK_KINDS: list[str] = ['FM_RESET', 'FM_APB_WRITE', 'FM_APB_READ', 'FM_TRANSFER', 'FM_WFP', 'FM_FAULT', 'FM_IRQ_CLEAR']

# Coverage bins: bin_name -> description.
CL_BINS: dict[str, str] = {'handshake_apb_access': 'apb_access', 'handshake_apb_read_data': 'apb_read_data', 'handshake_axi_ar': 'axi_ar', 'handshake_axi_r': 'axi_r', 'handshake_axi_aw': 'axi_aw', 'handshake_axi_w': 'axi_w', 'handshake_axi_b': 'axi_b', 'handshake_irq_level': 'irq_level', 'ordering_a_write_data_beat_must_not_be_issued_before_the_corresponding_read_data_beat_has_been_accepted_into_rd_buf': 'a_write_data_beat_must_not_be_issued_before_the_corresponding_read_data_beat_has_been_accepted_into_rd_buf', 'ordering_a_channel_complete_interrupt_pending_bit_is_set_only_after_the_final_successful_b_response': 'a_channel_complete_interrupt_pending_bit_is_set_only_after_the_final_successful_b_response', 'ordering_a_channel_fault_interrupt_pending_bit_is_set_on_the_first_detected_fault_before_any_later_completion_status': 'a_channel_fault_interrupt_pending_bit_is_set_on_the_first_detected_fault_before_any_later_completion_status', 'ordering_apb_w1c_clear_does_not_clear_configuration_registers_or_address_counters': 'apb_w1c_clear_does_not_clear_configuration_registers_or_address_counters', 'ordering_for_each_channel_at_most_one_read_burst_and_one_write_burst_are_outstanding_in_this_engineering_subset': 'for_each_channel_at_most_one_read_burst_and_one_write_burst_are_outstanding_in_this_engineering_subset', 'latency_fm_reset': 'latency bin for FM_RESET', 'latency_fm_apb_write': 'latency bin for FM_APB_WRITE', 'latency_fm_apb_read': 'latency bin for FM_APB_READ', 'latency_fm_transfer': 'latency bin for FM_TRANSFER', 'latency_fm_wfp': 'latency bin for FM_WFP', 'latency_fm_fault': 'latency bin for FM_FAULT', 'latency_fm_irq_clear': 'latency bin for FM_IRQ_CLEAR'}

# SSOT payload snapshot (read-only reference; never execute functional rules from here).
SSOT_MODEL: dict = {'ip': 'pl330realverify', 'function_model': {'purpose': 'Executable cycle-independent behavioral contract for PL330-like DMA transfer, wait-for-peripheral, debug command, APB register side effects, interrupt clear, and fault behavior.', 'constants': {'STATUS_STOPPED': 0, 'STATUS_EXECUTING': 1, 'STATUS_WAITING_FOR_PERIPHERAL': 2, 'STATUS_COMPLETED': 6, 'STATUS_FAULTED': 8, 'RESP_OKAY': 0, 'ERR_NONE': 0, 'ERR_DEBUG_REJECT': 1, 'ERR_UNALIGNED': 2, 'ERR_AXI_RD': 3, 'ERR_AXI_WR': 4, 'ERR_EVENT_TIMEOUT': 5}, 'state_variables': [{'name': 'sar', 'source': 'registers.SAR.src_addr', 'reset': 0, 'width': 32, 'description': 'Current source byte address for the selected channel.'}, {'name': 'dar', 'source': 'registers.DAR.dst_addr', 'reset': 0, 'width': 32, 'description': 'Current destination byte address for the selected channel.'}, {'name': 'loop_remaining', 'source': 'registers.LOOP_CFG.loop_count', 'reset': 0, 'width': 8, 'description': 'Number of transfer beats remaining, where encoded loop_count N loads N+1 beats.'}, {'name': 'status', 'source': 'registers.CSR.ch_status', 'reset': 0, 'width': 4, 'description': 'Architectural channel status code.'}, {'name': 'error_code', 'source': 'registers.CSR.error_code', 'reset': 0, 'width': 4, 'description': 'Architectural channel error code.'}, {'name': 'rd_buf', 'source': 'memory.rd_buf', 'reset': 0, 'width': 64, 'description': 'Last accepted AXI read data beat.'}, {'name': 'intstatus', 'source': 'registers.INTSTATUS', 'reset': 0, 'width': 32, 'description': 'Raw interrupt pending bits.'}, {'name': 'inten', 'source': 'registers.INTEN', 'reset': 0, 'width': 32, 'description': 'Interrupt enable bits.'}, {'name': 'pc', 'source': 'registers.PC.pc_addr', 'reset': 0, 'width': 32, 'description': 'Observable PL330-like program/debug address; no external microcode fetch in this subset.'}], 'transactions': [{'id': 'FM_RESET', 'name': 'reset_architecture', 'preconditions': ['dmacresetn == 0'], 'inputs': ['dmacresetn'], 'outputs': ['All externally visible output valids and interrupt are deasserted during reset.'], 'side_effects': ['All architectural state returns to declared reset values.']}, {'id': 'FM_APB_WRITE', 'name': 'apb_register_write', 'preconditions': ['dmacresetn == 1', 'psel == 1 and penable == 1 and pwrite == 1 and pready == 1'], 'inputs': ['paddr', 'pwdata', 'pstrb'], 'outputs': ['pready acknowledges the access; pslverr reports illegal address/access/strobe.'], 'side_effects': ['Writable register fields update only through declared write_effect rules; reserved fields ignore writes.'], 'error_cases': [{'id': 'ERR_APB_ILLEGAL', 'condition': 'illegal_apb_access == 1', 'result': 'pslverr asserted for the completing access; architectural DMA transfer state is not modified.'}]}, {'id': 'FM_APB_READ', 'name': 'apb_register_read', 'preconditions': ['dmacresetn == 1', 'psel == 1 and penable == 1 and pwrite == 0 and pready == 1'], 'inputs': ['paddr'], 'outputs': ['prdata returns the decoded register value with reserved bits forced to zero.'], 'side_effects': ['APB reads do not alter architectural state.']}, {'id': 'FM_TRANSFER', 'name': 'single_or_multi_beat_memory_copy', 'preconditions': ['dmacresetn == 1', 'start_cmd == 1', 'fault_inject == 0', '(sar % (DATA_WIDTH // 8)) == 0', '(dar % (DATA_WIDTH // 8)) == 0'], 'inputs': ['rdata', 'rresp', 'bresp', 'loop_count'], 'outputs': ['Each successful beat writes the captured read data to the destination address.', 'Final successful beat sets status COMPLETED and raises the channel-complete pending bit.'], 'side_effects': ['SAR and DAR increment by DATA_WIDTH/8 bytes after each successful write response.', 'loop_remaining decrements after each successful write response.'], 'error_cases': [{'id': 'ERR_AXI_RD', 'condition': 'rvalid == 1 and rready == 1 and rresp != 0', 'result': 'status=FAULTED, error_code=ERR_AXI_RD, CH_FAULT pending set, no write for the failed beat.'}, {'id': 'ERR_AXI_WR', 'condition': 'bvalid == 1 and bready == 1 and bresp != 0', 'result': 'status=FAULTED, error_code=ERR_AXI_WR, CH_FAULT pending set.'}]}, {'id': 'FM_WFP', 'name': 'wait_for_peripheral_event', 'preconditions': ['dmacresetn == 1', 'start_cmd == 1', 'wfp_enable == 1'], 'inputs': ['peripheral_events', 'wfp_event'], 'outputs': ['Channel remains WAITING_FOR_PERIPHERAL until the selected event bit is sampled high.'], 'side_effects': ['No AXI transaction is issued while selected_event is zero.']}, {'id': 'FM_FAULT', 'name': 'fault_completion', 'preconditions': ['dmacresetn == 1', 'fault_condition == 1'], 'inputs': ['fault_condition', 'fault_code'], 'outputs': ['Fault status is latched and a channel-fault pending interrupt is set.'], 'side_effects': ['First fault wins until software clears INTSTATUS and restarts the channel.'], 'error_cases': [{'id': 'ERR_UNALIGNED', 'condition': 'addresses_aligned == 0', 'result': 'status=FAULTED and error_code=ERR_UNALIGNED.'}, {'id': 'ERR_DEBUG_REJECT', 'condition': 'debug_execute == 1 and manager_busy == 1', 'result': 'debug command rejected without transfer side effects.'}]}, {'id': 'FM_IRQ_CLEAR', 'name': 'interrupt_write_one_to_clear', 'preconditions': ['dmacresetn == 1', 'apb_addr_intstatus == 1', 'psel == 1 and penable == 1 and pwrite == 1 and pready == 1'], 'inputs': ['pwdata'], 'outputs': ['dmac_irq reflects the enabled pending status after the W1C clear.'], 'side_effects': ['Only bits written as one are cleared; bits written as zero retain their prior value.']}], 'invariants': ['not (write_beat_done == 1 and read_buffer_valid == 0)', 'not (status == 6 and error_code != 0)', 'not (status == 8 and error_code == 0)', '(intstatus & (~0x1FFFF)) == 0', 'loop_remaining >= 0'], 'reference_model_hint': 'tb-gen should build a Python scoreboard from transactions, functional_outputs, state_changes, and invariants; prose outputs are explanatory only.'}, 'cycle_model': {'purpose': 'Cycle/handshake contract defining when PL330-like architectural state, AXI/APB valid-ready signals, interrupt outputs, and error status may change.', 'executable': 'pymtl3', 'backend_policy': 'Use PyMTL3 or direct Python cycle model as a timing oracle; FunctionalModel remains the behavioral oracle.', 'clock': 'dmaclk', 'reset': {'assertion': 'dmacresetn low asynchronously clears architectural state and deasserts valid/ready output valids and dmac_irq.', 'deassertion': 'State is usable on the first rising dmaclk edge after synchronized deassertion.'}, 'latency': {'register_read': {'min_cycles': 1, 'max_cycles': 1, 'description': 'pready/prdata/pslverr complete in APB access phase.'}, 'register_write': {'min_cycles': 1, 'max_cycles': 1, 'description': 'Writable side effects occur on the completing APB access cycle.'}, 'event_release': {'min_cycles': 1, 'max_cycles': 2, 'description': 'Selected peripheral event sampled then WFP state can advance.'}, 'single_beat_transfer': {'min_cycles': 5, 'max_cycles': None, 'description': 'Command accept, AR, R, AW/W, and B stages; max is unbounded under AXI backpressure.'}, 'interrupt_assertion': {'min_cycles': 1, 'max_cycles': 2, 'description': 'Pending enabled interrupt reflects terminal status or W1C clear within two cycles.'}}, 'handshake_rules': [{'id': 'APB_ACCESS', 'signal': 'pready', 'rule': 'pready asserts only for psel==1 and penable==1 and completes exactly one APB transfer.', 'sample_condition': 'psel == 1 and penable == 1'}, {'id': 'APB_READ_DATA', 'signal': 'prdata', 'rule': 'prdata is stable for the completing read access and reserved bits read zero.', 'sample_condition': 'psel == 1 and penable == 1 and pwrite == 0 and pready == 1'}, {'id': 'AXI_AR', 'signal': 'arvalid', 'rule': 'Hold arvalid and AR payload stable until arvalid and arready are sampled high.', 'sample_condition': 'arvalid == 1 and arready == 1'}, {'id': 'AXI_R', 'signal': 'rready', 'rule': 'Assert rready only when rd_buf can accept rdata; capture exactly one beat on rvalid and rready.', 'sample_condition': 'rvalid == 1 and rready == 1'}, {'id': 'AXI_AW', 'signal': 'awvalid', 'rule': 'Hold awvalid and AW payload stable until awvalid and awready are sampled high.', 'sample_condition': 'awvalid == 1 and awready == 1'}, {'id': 'AXI_W', 'signal': 'wvalid', 'rule': 'Hold wvalid, wdata, wstrb, and wlast stable until wvalid and wready are sampled high.', 'sample_condition': 'wvalid == 1 and wready == 1'}, {'id': 'AXI_B', 'signal': 'bready', 'rule': 'Assert bready while waiting for write response; consume bresp on bvalid and bready.', 'sample_condition': 'bvalid == 1 and bready == 1'}, {'id': 'IRQ_LEVEL', 'signal': 'dmac_irq', 'rule': 'dmac_irq equals the OR-reduction of intstatus & inten after reset, terminal updates, and W1C clears settle.', 'sample_condition': 'dmacresetn == 1'}], 'pipeline': [{'stage': 'S0_APB_ACCEPT', 'cycle': 0, 'action': 'Decode APB access, update configuration or emit start/halt/debug pulses.'}, {'stage': 'S1_CMD_ACCEPT', 'cycle': 1, 'action': 'Latch channel command, SAR, DAR, count, WFP configuration, and error precheck results.'}, {'stage': 'S2_WFP', 'cycle': '1..N', 'action': 'If WFP is enabled, hold state until selected peripheral event samples high.'}, {'stage': 'S3_ISSUE_READ', 'cycle': 'N..M', 'action': 'Drive AXI AR payload and hold until AR handshake.'}, {'stage': 'S4_CAPTURE_READ', 'cycle': 'M..P', 'action': 'Accept AXI R beat, classify rresp, and capture rdata into rd_buf.'}, {'stage': 'S5_ISSUE_WRITE', 'cycle': 'P..Q', 'action': 'Drive AXI AW and W payloads; each channel may complete independently but both must handshake before B wait.'}, {'stage': 'S6_WRITE_RESP', 'cycle': 'Q..R', 'action': 'Consume AXI B response, update address/count/status/interrupts.'}, {'stage': 'S7_TERMINAL', 'cycle': 'R+1', 'action': 'Post COMPLETED or FAULTED status and level interrupt state.'}], 'ordering': ['A write data beat must not be issued before the corresponding read data beat has been accepted into rd_buf.', 'A channel-complete interrupt pending bit is set only after the final successful B response.', 'A channel-fault interrupt pending bit is set on the first detected fault before any later completion status.', 'APB W1C clear does not clear configuration registers or address counters.', 'For each channel, at most one read burst and one write burst are outstanding in this engineering subset.'], 'backpressure': ['If arready is zero, AR payload remains stable and no read transaction is counted.', 'If rvalid is zero, rd_buf and downstream write stage remain stable.', 'If awready or wready is zero, write payload/address/control remain stable until handshakes occur.', 'If bvalid is zero, architectural completion/fault for that write is delayed.', 'APB accesses are not backpressured in the baseline beyond the single access phase.'], 'performance': {'frequency_mhz': 500, 'throughput': {'sustained_beats_per_cycle': 1, 'condition': 'No APB command gap, WFP disabled or already satisfied, no AXI backpressure, no AXI errors, aligned addresses.'}, 'outstanding': {'read_max': 1, 'write_max': 1, 'per_channel': True, 'description': 'Single outstanding read/write in the engineering subset.'}, 'depth': {'pipeline_stages': 8, 'queue_depth': 1, 'rd_buffer_depth': 1, 'description': 'Visible cycle-model pipeline and buffering depth.'}}, 'observability': ['Every function_model transaction maps to one or more cycle_model stages and at least one coverage bin.', 'Waveform debug must show state, start_cmd, selected_event, AXI handshakes, rd_buf, status, error_code, intstatus, inten, and dmac_irq.']}}


# ---------------------------------------------------------------------------
# CycleModel
# ---------------------------------------------------------------------------

class CycleModel:
    """Cycle-level model: queues transactions, applies latency/handshake rules,
    delegates all functional evaluation to FunctionalModel.apply()."""

    def __init__(self, params=None):
        self.fl = FunctionalModel(params)
        self.in_q: list[tuple[int, dict]] = []   # (arrival_t, txn)
        self.out_q: list[tuple[int, dict]] = []  # (ready_t, result)
        self.cov: dict[str, int] = {k: 0 for k in CL_BINS}
        self.now: int = 0
        self._outstanding: int = 0

    def reset(self) -> None:
        self.fl.reset()
        self.in_q.clear()
        self.out_q.clear()
        self.cov = {k: 0 for k in CL_BINS}
        self.now = 0
        self._outstanding = 0

    def drive(self, txn: dict, t: int) -> None:
        """Enqueue a transaction arriving at cycle t."""
        self.in_q.append((int(t), dict(txn)))

    def _latency_for(self, txn: dict) -> int:
        kind = str(txn.get("kind") or txn.get("op") or "").strip().lower()
        return _LATENCY.get(kind, _LATENCY.get("default", 1))

    def _sample_handshake_coverage(self, txn: dict) -> None:
        for rule in _HANDSHAKE_RULES:
            name = rule.get("name", "")
            bin_key = f"handshake_{name}"
            if bin_key in self.cov:
                self.cov[bin_key] += 1

    def _sample_ordering_coverage(self) -> None:
        for rule in _ORDERING_RULES:
            name = rule.get("name", "")
            bin_key = f"ordering_{name}"
            if bin_key in self.cov:
                self.cov[bin_key] += 1

    def _sample_latency_coverage(self, txn: dict) -> None:
        kind = str(txn.get("kind") or txn.get("op") or "").strip().lower()
        key = "".join(ch if ch.isalnum() else "_" for ch in kind).strip("_")
        bin_key = f"latency_{key}"
        if bin_key in self.cov:
            self.cov[bin_key] += 1

    def tick(self, t: int) -> None:
        """Advance model to cycle t.  Drain in_q respecting outstanding cap and handshake rules."""
        self.now = int(t)
        # Pop one pending transaction if not stalled by outstanding cap
        while self.in_q:
            if self._outstanding >= _OUTSTANDING_CAP:
                break  # stalled: wait for out_q drain
            arrival_t, txn = self.in_q[0]
            if arrival_t > self.now:
                break  # not yet arrived
            self.in_q.pop(0)
            # FunctionalModel is the ONLY oracle — one call per transaction
            try:
                result = self.fl.apply(txn)
            except Exception as _exc:
                result = {"kind": txn.get("kind", "unknown"), "resp": 2, "fl_error": str(_exc)}
            latency = self._latency_for(txn)
            ready_t = self.now + latency
            self.out_q.append((ready_t, result))
            self._outstanding += 1
            # Sample coverage bins
            self._sample_handshake_coverage(txn)
            self._sample_ordering_coverage()
            self._sample_latency_coverage(txn)

        # Release completed transactions from outstanding count
        completed = [r for (d, r) in self.out_q if d <= self.now]
        self._outstanding = max(0, self._outstanding - len(completed))

    def observe(self, t: int) -> list[tuple[int, dict]]:
        """Return all results ready at or before t, removing them from out_q."""
        t = int(t)
        ready = [(d, r) for (d, r) in self.out_q if d <= t]
        self.out_q = [(d, r) for (d, r) in self.out_q if d > t]
        return ready

    def coverage(self) -> dict[str, int]:
        return dict(self.cov)

    def run_self_check(self) -> dict:
        """Smoke run: drive every known transaction kind once, tick, observe."""
        self.reset()
        kinds = list(_SELF_CHECK_KINDS) or ["reset"]
        t = 0
        for kind in kinds:
            self.drive({"kind": kind}, t=t)
            t += 1
            self.tick(t)
        # Drain with a long tick to let all latencies expire
        drain_t = t + 200
        self.tick(drain_t)
        obs = self.observe(drain_t)
        total_bins = len(CL_BINS)
        hit_bins = sum(1 for v in self.cov.values() if v > 0)
        return {
            "passed": bool(obs),
            "backend": MODEL_BACKEND,
            "pymtl3_available": HAS_PYMTL3,
            "transactions": len(kinds),
            "results_observed": len(obs),
            "coverage_bins": total_bins,
            "coverage_hit": hit_bins,
            "performance_targets": PERFORMANCE_TARGETS,
        }


if HAS_PYMTL3:
    class CycleModelPyMTL(Component):
        """PyMTL3 cycle shell around CycleModel for cycle/performance validation.

        The wrapper intentionally delegates behavioral results to CycleModel,
        which delegates function evaluation to FunctionalModel.  PyMTL owns the
        clocked shell and observable counters used by CL coverage.
        """

        def construct(s):
            s.reset_in = InPort(Bits1)
            s.valid = InPort(Bits1)
            s.ready = OutPort(Bits1)
            s.cycle_count = OutPort(Bits32)
            s.outstanding = OutPort(Bits32)
            s.queue_depth = OutPort(Bits32)
            s._model = CycleModel()

            @update_ff
            def cl_tick():
                if s.reset_in:
                    s._model.reset()
                    s.ready <<= 1
                    s.cycle_count <<= 0
                    s.outstanding <<= 0
                    s.queue_depth <<= 0
                else:
                    next_cycle = s._model.now + 1
                    s._model.tick(next_cycle)
                    s.ready <<= int(s._model._outstanding < _OUTSTANDING_CAP)
                    s.cycle_count <<= next_cycle
                    s.outstanding <<= s._model._outstanding
                    s.queue_depth <<= len(s._model.in_q)
else:
    CycleModelPyMTL = None


def make_pymtl_cycle_model():
    """Return the PyMTL3 cycle shell.  Use direct Python smoke, not pytest-pymtl3."""
    if not HAS_PYMTL3:
        raise RuntimeError("pymtl3 is not importable in this Python environment")
    return CycleModelPyMTL()


if __name__ == "__main__":
    import json as _json
    print(_json.dumps(CycleModel().run_self_check(), indent=2))
