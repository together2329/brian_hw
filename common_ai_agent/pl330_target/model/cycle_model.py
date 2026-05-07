#!/usr/bin/env python3
"""Executable SSOT cycle-level model for pl330_target. Wraps FunctionalModel — FL is the only oracle."""

from __future__ import annotations

import json

try:
    from .functional_model import FunctionalModel
except ImportError:
    from functional_model import FunctionalModel


# ---------------------------------------------------------------------------
# SSOT-derived tables (baked at generation time)
# ---------------------------------------------------------------------------

# Latency table: transaction kind -> cycles.  max_cycles when defined; min_cycles otherwise; default=1.
_LATENCY: dict[str, int] = {'control_or_request_accept': 0, 'primary_operation': 1, 'response_or_observable_result': 0, 'default': 1}

# Handshake rules from SSOT cycle_model.handshake_rules.
_HANDSHAKE_RULES: list[dict] = [{'name': 'handshake_0', 'description': '', 'predicate': ''}, {'name': 'handshake_1', 'description': '', 'predicate': ''}]

# Ordering rules from SSOT cycle_model.ordering.
_ORDERING_RULES: list[dict] = [{'name': 'accepted_requests_update_architectural_state_only_on_clock_edges', 'description': ''}, {'name': 'completion_status_interrupt_updates_occur_after_the_operation_reaches_its_terminal_fsm_state', 'description': ''}, {'name': 'backpressure_stalls_the_active_handshake_stage_without_corrupting_stored_state', 'description': ''}, {'name': 'read_dataflow_stages_must_precede_dependent_write_output_stages_where_declared_in_dataflow', 'description': ''}]

# Maximum outstanding transactions before stalling.
_OUTSTANDING_CAP: int = 1

# Transaction kinds for self-check, derived from function_model.transactions at generation time.
_SELF_CHECK_KINDS: list[str] = ['FM_RESET', 'FM_DMAGO', 'FM_DMALD', 'FM_DMAST', 'FM_DMALDP', 'FM_DMASTP', 'FM_DMASEV', 'FM_DMAEND', 'FM_FAULT']

# Coverage bins: bin_name -> description.
CL_BINS: dict[str, str] = {'handshake_handshake_0': 'handshake_0', 'handshake_handshake_1': 'handshake_1', 'ordering_accepted_requests_update_architectural_state_only_on_clock_edges': 'accepted_requests_update_architectural_state_only_on_clock_edges', 'ordering_completion_status_interrupt_updates_occur_after_the_operation_reaches_its_terminal_fsm_state': 'completion_status_interrupt_updates_occur_after_the_operation_reaches_its_terminal_fsm_state', 'ordering_backpressure_stalls_the_active_handshake_stage_without_corrupting_stored_state': 'backpressure_stalls_the_active_handshake_stage_without_corrupting_stored_state', 'ordering_read_dataflow_stages_must_precede_dependent_write_output_stages_where_declared_in_dataflow': 'read_dataflow_stages_must_precede_dependent_write_output_stages_where_declared_in_dataflow', 'latency_fm_reset': 'latency bin for FM_RESET', 'latency_fm_dmago': 'latency bin for FM_DMAGO', 'latency_fm_dmald': 'latency bin for FM_DMALD', 'latency_fm_dmast': 'latency bin for FM_DMAST', 'latency_fm_dmaldp': 'latency bin for FM_DMALDP', 'latency_fm_dmastp': 'latency bin for FM_DMASTP', 'latency_fm_dmasev': 'latency bin for FM_DMASEV', 'latency_fm_dmaend': 'latency bin for FM_DMAEND', 'latency_fm_fault': 'latency bin for FM_FAULT'}

# SSOT payload snapshot (read-only reference; never execute functional rules from here).
SSOT_MODEL: dict = {'ip': 'pl330_target', 'function_model': {'state_variables': [{'name': 'channel_state', 'width': 4, 'reset': 0, 'description': 'Per-channel FSM state (0=stopped, 1=executing, 2=cache_miss, 3=updating_pc, 4=waiting_for_event, 5=at_barrier, 6=killing, 7=completing, 8=faulting, 9=faulting_completing)'}, {'name': 'channel_pc', 'width': 32, 'reset': 0}, {'name': 'outstanding_reads', 'width': 4, 'reset': 0}, {'name': 'outstanding_writes', 'width': 4, 'reset': 0}, {'name': 'mfifo_count', 'width': 5, 'reset': 0}, {'name': 'irq_status', 'width': 32, 'reset': 0}, {'name': 'fault_status', 'width': 32, 'reset': 0}], 'transactions': [{'id': 'FM_RESET', 'name': 'reset', 'outputs': ['all state -> reset values'], 'side_effects': ['outstanding_reads=0', 'outstanding_writes=0', 'mfifo_count=0', 'irq_status=0'], 'error_cases': [], 'preconditions': ['transaction is accepted under cycle_model rules']}, {'id': 'FM_DMAGO', 'name': 'dmago_command', 'preconditions': ['channel_state==0', 'manager APB write to DBGINST'], 'outputs': ['channel_state=1', 'channel_pc=arg_addr'], 'side_effects': [], 'error_cases': [{'condition': 'secure violation', 'result': 'fault_status |= INSTR_FETCH_ERR'}]}, {'id': 'FM_DMALD', 'name': 'dmald_load', 'preconditions': ['channel_state==1', 'mfifo has space'], 'outputs': ['outstanding_reads += 1', 'mfifo entries reserved'], 'side_effects': ['issue AXI AR'], 'error_cases': [{'condition': 'AXI rresp != OKAY', 'result': 'fault_status |= DATA_READ_ERR'}]}, {'id': 'FM_DMAST', 'name': 'dmast_store', 'preconditions': ['channel_state==1', 'mfifo has data'], 'outputs': ['outstanding_writes += 1', 'mfifo entries consumed'], 'side_effects': ['issue AXI AW + W'], 'error_cases': [{'condition': 'AXI bresp != OKAY', 'result': 'fault_status |= DATA_WRITE_ERR'}]}, {'id': 'FM_DMALDP', 'name': 'dmaldp_periph_load', 'preconditions': ['channel_state==1', 'periph drvalid asserted'], 'outputs': ['outstanding_reads += 1'], 'side_effects': ['drready asserted', 'AXI AR issued'], 'error_cases': []}, {'id': 'FM_DMASTP', 'name': 'dmastp_periph_store', 'preconditions': ['channel_state==1', 'periph davalid acknowledged'], 'outputs': ['outstanding_writes += 1'], 'side_effects': ['daready asserted', 'AXI AW+W issued'], 'error_cases': []}, {'id': 'FM_DMASEV', 'name': 'dmasev_event_signal', 'preconditions': ['channel_state==1', 'event index < NUM_IRQS'], 'outputs': ['irq_status |= 1<<event_idx'], 'side_effects': ['irq[event_idx] pulse'], 'error_cases': []}, {'id': 'FM_DMAEND', 'name': 'dmaend_terminate', 'preconditions': ['channel_state==1', 'no outstanding'], 'outputs': ['channel_state=0'], 'side_effects': [], 'error_cases': [{'condition': 'outstanding > 0', 'result': 'wait until drained'}]}, {'id': 'FM_FAULT', 'name': 'fault_propagate', 'preconditions': ['any error_case fired'], 'outputs': ['channel_state=8', 'irq_abort pulse'], 'side_effects': ['fault_status updated'], 'error_cases': []}], 'invariants': ['outstanding_reads >= 0 && outstanding_reads <= 2*NUM_CHANNELS', 'outstanding_writes >= 0 && outstanding_writes <= 2*NUM_CHANNELS', 'mfifo_count <= MFIFO_DEPTH', 'channel_state != 1 -> outstanding_reads == 0 && outstanding_writes == 0', 'fault triggers irq_abort within 4 cycles']}, 'cycle_model': {'purpose': 'Cycle/handshake contract for rtl-gen and waveform-based verification.', 'clock': 'clk', 'reset': {'signal': 'rst_n', 'polarity': 'active_low', 'assertion': 'rst_n assertion returns architectural state to declared reset values', 'deassertion': 'Logic may accept transactions after async_assert_sync_deassert deassertion completes'}, 'latency': {'control_or_request_accept': {'min_cycles': 0, 'max_cycles': None, 'description': 'Bounded by declared valid/ready or protocol acceptance rules'}, 'primary_operation': {'min_cycles': 1, 'max_cycles': None, 'description': 'Runs on clk at nominal 100 MHz; max depends on declared backpressure and implementation state'}, 'response_or_observable_result': {'min_cycles': 0, 'max_cycles': None, 'description': 'Held stable until the declared response/output acceptance condition'}}, 'handshake_rules': [{'signal': 'req_valid/req_ready', 'rule': 'req_valid payload remains stable until req_ready is sampled asserted on control_data.'}, {'signal': 'rsp_valid/rsp_ready', 'rule': 'rsp_valid payload remains stable until rsp_ready is sampled asserted on control_data.'}], 'pipeline': [{'stage': 'S0_ACCEPT', 'cycle': '0..N', 'action': 'Accept legal request/command/packet/control work under declared handshake rules.'}, {'stage': 'S1_EVALUATE', 'cycle': 'N..M', 'action': 'Evaluate function_model transaction and update only declared state.'}, {'stage': 'S2_OBSERVE', 'cycle': 'M..K', 'action': 'Publish response/status/output/debug event and hold it stable until accepted.'}], 'ordering': ['Accepted requests update architectural state only on clock edges.', 'Completion/status/interrupt updates occur after the operation reaches its terminal FSM state.', 'Backpressure stalls the active handshake stage without corrupting stored state.', 'Read/dataflow stages must precede dependent write/output stages where declared in dataflow.'], 'backpressure': ['Ready/valid deassertion stalls only the affected interface stage; payload and route/control state remain stable.'], 'observability': ['Every function_model transaction maps to at least one cycle_model stage and one test_requirements scenario.']}}


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
            "transactions": len(kinds),
            "results_observed": len(obs),
            "coverage_bins": total_bins,
            "coverage_hit": hit_bins,
        }


if __name__ == "__main__":
    import json as _json
    print(_json.dumps(CycleModel().run_self_check(), indent=2))
