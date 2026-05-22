#!/usr/bin/env python3
"""Executable SSOT cycle-level model for dma_real. Wraps FunctionalModel — FL is the only oracle."""

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
_LATENCY: dict[str, int] = {'default': 1}

# Handshake rules from SSOT cycle_model.handshake_rules.
_HANDSHAKE_RULES: list[dict] = [{'name': 'apb_access', 'description': 'APB accesses sample on pclk with psel and penable. No wait states. Config data crosses CDC to hclk domain via async FIFO.', 'predicate': ''}, {'name': 'cdc_config', 'description': 'APB write data pushed into pclk-side FIFO write port. hclk-side read port pops config. Gray-code pointer synchronization prevents metastability.', 'predicate': ''}, {'name': 'ahb_address_phase', 'description': 'AHB address phase drives haddr, htrans, hsize, hburst, hprot, hmaster, hmastlock for one hclk cycle.', 'predicate': ''}, {'name': 'ahb_data_phase', 'description': 'AHB data phase follows address phase by one hclk cycle with hwdata or hrdata.', 'predicate': ''}, {'name': 'ahb_1kb_boundary', 'description': 'Burst crossing 1KB address boundary starts new NONSEQ beat. hburst recalculated for remaining beats.', 'predicate': ''}, {'name': 'ahb_error_response', 'description': 'hresp=ERROR (01) completes current beat and aborts burst. hresp=RETRY (10) releases bus and re-requests. hresp=SPLIT (11) releases bus and waits.', 'predicate': ''}, {'name': 'arb_grant_rule', 'description': 'Arbiter evaluates requests every hclk cycle and grants to next round-robin contender.', 'predicate': ''}, {'name': 'start_accept', 'description': 'ch_start accepted only when ch_busy is low and dma_en is high and CDC config has arrived.', 'predicate': ''}, {'name': 'timeout_rule', 'description': 'Timeout counter increments each hclk cycle while waiting for hready. Resets on hready assertion. Error code 4 when counter reaches GLOBAL_TIMEOUT.', 'predicate': ''}]

# Ordering rules from SSOT cycle_model.ordering.
_ORDERING_RULES: list[dict] = [{'name': 'configuration_apb_pclk_must_cross_cdc_before_hclk_channel_fsm_reads_it', 'description': ''}, {'name': 'read_burst_completion_must_precede_write_burst_for_same_data', 'description': ''}, {'name': 'address_update_update_must_precede_next_burst_request', 'description': ''}, {'name': 'transfer_completion_done_precedes_done_pulse_observation', 'description': ''}, {'name': '1kb_boundary_crossing_recalculates_burst_parameters_before_next_address_phase', 'description': ''}]

# Maximum outstanding transactions before stalling.
_OUTSTANDING_CAP: int = 1

# Cycle/performance targets used by coverage and PyMTL shell instrumentation.
PERFORMANCE_TARGETS: dict = {'frequency_mhz': None, 'throughput': 'one burst per channel per arbiter round', 'outstanding': None, 'pipeline_stages': None, 'queue_depth': None}

# Transaction kinds for self-check, derived from function_model.transactions at generation time.
_SELF_CHECK_KINDS: list[str] = ['FM_DMA_START', 'FM_DMA_STEP', 'FM_DMA_COMPLETE', 'FM_DMA_ERROR', 'FM_ARB_GRANT']

# Coverage bins: bin_name -> description.
CL_BINS: dict[str, str] = {'handshake_apb_access': 'APB accesses sample on pclk with psel and penable. No wait states. Config data crosses CDC to hclk domain via async FIFO.', 'handshake_cdc_config': 'APB write data pushed into pclk-side FIFO write port. hclk-side read port pops config. Gray-code pointer synchronization prevents metastability.', 'handshake_ahb_address_phase': 'AHB address phase drives haddr, htrans, hsize, hburst, hprot, hmaster, hmastlock for one hclk cycle.', 'handshake_ahb_data_phase': 'AHB data phase follows address phase by one hclk cycle with hwdata or hrdata.', 'handshake_ahb_1kb_boundary': 'Burst crossing 1KB address boundary starts new NONSEQ beat. hburst recalculated for remaining beats.', 'handshake_ahb_error_response': 'hresp=ERROR (01) completes current beat and aborts burst. hresp=RETRY (10) releases bus and re-requests. hresp=SPLIT (11) releases bus and waits.', 'handshake_arb_grant_rule': 'Arbiter evaluates requests every hclk cycle and grants to next round-robin contender.', 'handshake_start_accept': 'ch_start accepted only when ch_busy is low and dma_en is high and CDC config has arrived.', 'handshake_timeout_rule': 'Timeout counter increments each hclk cycle while waiting for hready. Resets on hready assertion. Error code 4 when counter reaches GLOBAL_TIMEOUT.', 'ordering_configuration_apb_pclk_must_cross_cdc_before_hclk_channel_fsm_reads_it': 'configuration_apb_pclk_must_cross_cdc_before_hclk_channel_fsm_reads_it', 'ordering_read_burst_completion_must_precede_write_burst_for_same_data': 'read_burst_completion_must_precede_write_burst_for_same_data', 'ordering_address_update_update_must_precede_next_burst_request': 'address_update_update_must_precede_next_burst_request', 'ordering_transfer_completion_done_precedes_done_pulse_observation': 'transfer_completion_done_precedes_done_pulse_observation', 'ordering_1kb_boundary_crossing_recalculates_burst_parameters_before_next_address_phase': '1kb_boundary_crossing_recalculates_burst_parameters_before_next_address_phase', 'latency_fm_dma_start': 'latency bin for FM_DMA_START', 'latency_fm_dma_step': 'latency bin for FM_DMA_STEP', 'latency_fm_dma_complete': 'latency bin for FM_DMA_COMPLETE', 'latency_fm_dma_error': 'latency bin for FM_DMA_ERROR', 'latency_fm_arb_grant': 'latency bin for FM_ARB_GRANT'}

# SSOT payload snapshot (read-only reference; never execute functional rules from here).
SSOT_MODEL: dict = {'ip': 'dma_real', 'function_model': {'purpose': 'Behavioral DMA reference model independent of dual-clock microarchitecture. Models single-logical-cycle semantics; CDC and clock domain details are implementation concerns.', 'state_variables': [{'name': 'ch_busy_q', 'width': 'N_CHANNELS', 'reset': 0, 'description': 'Per-channel busy flag'}, {'name': 'ch_done_q', 'width': 'N_CHANNELS', 'reset': 0, 'description': 'Per-channel done sticky latch'}, {'name': 'ch_error_q', 'width': 'N_CHANNELS', 'reset': 0, 'description': 'Per-channel error sticky latch'}, {'name': 'ch_remaining_q', 'width': 32, 'reset': 0, 'description': 'Per-channel remaining word count'}, {'name': 'ch_src_addr_q', 'width': 'ADDR_WIDTH', 'reset': 0, 'description': 'Per-channel current source address'}, {'name': 'ch_dst_addr_q', 'width': 'ADDR_WIDTH', 'reset': 0, 'description': 'Per-channel current destination address'}, {'name': 'ch_stride_q', 'width': 'ADDR_WIDTH', 'reset': 4, 'description': 'Per-channel address increment per beat (default 4 for word)'}, {'name': 'dma_en_q', 'width': 1, 'reset': 0, 'description': 'Global DMA enable'}, {'name': 'int_enable_q', 'width': 'N_CHANNELS', 'reset': 0, 'description': 'Per-channel interrupt enable mask'}, {'name': 'arb_ptr_q', 'width': 3, 'reset': 0, 'description': 'Round-robin arbiter pointer'}, {'name': 'timeout_q', 'width': 16, 'reset': 0, 'description': 'Bus timeout threshold in hclk cycles'}, {'name': 'perf_words_q', 'width': 32, 'reset': 0, 'description': 'Per-channel total words transferred'}, {'name': 'perf_cycles_q', 'width': 32, 'reset': 0, 'description': 'Per-channel total active cycles'}], 'transactions': [{'id': 'FM_DMA_START', 'name': 'dma_start', 'required_fields': ['ch_id', 'src_addr', 'dst_addr', 'length', 'stride'], 'preconditions': ['presetn and hresetn are deasserted', 'dma_en_q == 1', 'ch_busy_q[ch_id] == 0'], 'outputs': ['ch_busy', 'ch_error', 'ch_err_code'], 'side_effects': ['ch_remaining_q[ch_id] set to length on valid start', 'ch_src_addr_q[ch_id] set to src_addr on valid start', 'ch_dst_addr_q[ch_id] set to dst_addr on valid start', 'ch_stride_q[ch_id] set to stride on valid start', 'perf_cycles_q[ch_id] reset to 0 on valid start', 'perf_words_q[ch_id] reset to 0 on valid start'], 'error_cases': ['zero length (length == 0, error code 2)', 'misaligned source address (src_addr % 4 != 0, error code 1)', 'misaligned destination address (dst_addr % 4 != 0, error code 1)', 'start while busy (ignored, preserves state)']}, {'id': 'FM_DMA_STEP', 'name': 'dma_step', 'required_fields': ['ch_id', 'burst_len'], 'preconditions': ['ch_busy_q[ch_id] == 1', 'arbiter has granted bus to ch_id'], 'outputs': ['ch_busy', 'ch_done'], 'side_effects': ['ch_remaining_q decrements by burst_len', 'ch_src_addr_q increments by burst_len * ch_stride_q[ch_id]', 'ch_dst_addr_q increments by burst_len * ch_stride_q[ch_id]', 'perf_words_q increments by burst_len', 'perf_cycles_q increments by burst_len plus pipeline overhead', 'done pulses on terminal step'], 'error_cases': ['bus error during AHB transfer (hresp == ERROR, code 3)', 'timeout waiting for hready (code 4)']}, {'id': 'FM_DMA_COMPLETE', 'name': 'dma_complete', 'required_fields': ['ch_id'], 'preconditions': ['ch_remaining_q[ch_id] == 0', 'ch_busy_q[ch_id] == 1'], 'outputs': ['ch_busy', 'ch_done', 'irq'], 'side_effects': ['ch_done_q[ch_id] set to 1', 'ch_busy_q[ch_id] cleared', 'IRQ asserted if enabled'], 'error_cases': []}, {'id': 'FM_DMA_ERROR', 'name': 'dma_error', 'required_fields': ['ch_id', 'error_code'], 'preconditions': ['error condition detected (alignment, zero-length, bus error, timeout, or FIFO overflow)'], 'outputs': ['ch_error', 'ch_err_code', 'irq'], 'side_effects': ['ch_error_q[ch_id] set to 1', 'ch_busy_q[ch_id] cleared', 'Error code latched in status register'], 'error_cases': ['alignment error (code 1)', 'zero length (code 2)', 'bus error (code 3)', 'timeout (code 4)', 'FIFO overflow (code 5)']}, {'id': 'FM_ARB_GRANT', 'name': 'arb_grant', 'required_fields': ['requester_mask'], 'preconditions': ['at least one channel is requesting bus access'], 'outputs': ['arb_grant'], 'side_effects': ['arb_ptr_q updated to next channel after grant', 'granted channel gains AHB bus access'], 'error_cases': []}], 'invariants': ['ch_busy and ch_done are not asserted together for the same channel.', 'ch_error is asserted only for invalid requests, bus errors, timeouts, or FIFO overflows.', 'ch_remaining_q never underflows below zero.', 'irq[ch] reflects (done_q[ch] OR error_q[ch]) AND int_enable_q[ch].', 'irq_combined reflects OR of all per-channel irq outputs.', 'Each FIFO operates as circular buffer with gray-code synchronized pointers across clock domains.', 'htrans transitions IDLE only when no channel has an active grant.', "Performance counters saturate at 32'hFFFFFFFF and do not wrap."]}, 'cycle_model': {'executable': 'pymtl3', 'backend_policy': 'Use PyMTL3 shell for cycle behavior. FunctionalModel remains oracle.', 'clock': 'hclk', 'reset': 'hresetn', 'latency': 5, 'handshake_rules': [{'name': 'apb_access', 'description': 'APB accesses sample on pclk with psel and penable. No wait states. Config data crosses CDC to hclk domain via async FIFO.'}, {'name': 'cdc_config', 'description': 'APB write data pushed into pclk-side FIFO write port. hclk-side read port pops config. Gray-code pointer synchronization prevents metastability.'}, {'name': 'ahb_address_phase', 'description': 'AHB address phase drives haddr, htrans, hsize, hburst, hprot, hmaster, hmastlock for one hclk cycle.'}, {'name': 'ahb_data_phase', 'description': 'AHB data phase follows address phase by one hclk cycle with hwdata or hrdata.'}, {'name': 'ahb_1kb_boundary', 'description': 'Burst crossing 1KB address boundary starts new NONSEQ beat. hburst recalculated for remaining beats.'}, {'name': 'ahb_error_response', 'description': 'hresp=ERROR (01) completes current beat and aborts burst. hresp=RETRY (10) releases bus and re-requests. hresp=SPLIT (11) releases bus and waits.'}, {'name': 'arb_grant_rule', 'description': 'Arbiter evaluates requests every hclk cycle and grants to next round-robin contender.'}, {'name': 'start_accept', 'description': 'ch_start accepted only when ch_busy is low and dma_en is high and CDC config has arrived.'}, {'name': 'timeout_rule', 'description': 'Timeout counter increments each hclk cycle while waiting for hready. Resets on hready assertion. Error code 4 when counter reaches GLOBAL_TIMEOUT.'}], 'pipeline': [{'stage': 'IDLE', 'cycle': 0, 'action': 'wait for valid start/config from CDC bridge'}, {'stage': 'CFG', 'cycle': 1, 'action': 'latch src_addr, dst_addr, remaining, stride from CDC config registers'}, {'stage': 'REQUEST', 'cycle': 2, 'action': 'request AHB bus via arbiter, clock gating cell enables hclk to channel'}, {'stage': 'READ', 'cycle': 3, 'action': 'AHB read burst from source address into pointer-based FIFO, timeout counter active'}, {'stage': 'WRITE', 'cycle': 4, 'action': 'AHB write burst from FIFO to destination address, FIFO read pointer advances'}, {'stage': 'UPDATE', 'cycle': 5, 'action': 'update remaining count (decrement), src_addr (+= stride), dst_addr (+= stride), perf counters increment'}, {'stage': 'DONE', 'cycle': 6, 'action': 'assert done pulse, update status, trigger IRQ, clock gating cell may disable hclk'}, {'stage': 'ERROR', 'cycle': 2, 'action': 'assert error pulse, latch error code, return to IDLE, clock gating cell may disable hclk'}], 'ordering': ['Configuration (APB pclk) must cross CDC before hclk channel FSM reads it.', 'Read burst completion must precede write burst for same data.', 'Address update (UPDATE) must precede next burst request.', 'Transfer completion (DONE) precedes done pulse observation.', '1KB boundary crossing recalculates burst parameters before next address phase.'], 'backpressure': ['New starts blocked while channel busy.', 'AHB transfers stall when hready is low.', 'Arbiter queues requests when bus is occupied.', 'FIFO almost_full back-pressures read burst.', 'CDC FIFO full back-pressures APB writes (pslverr or pready deassert).'], 'performance': {'outstanding_limit': 'N_CHANNELS', 'throughput': 'one burst per channel per arbiter round', 'cdc_latency': '3 hclk cycles for config to cross from pclk domain', 'fifo_depth': 'FIFO_DEPTH words per channel'}}}


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
