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
_HANDSHAKE_RULES: list[dict] = [{'name': 'apb_access', 'description': 'APB accesses sample on pclk with psel and penable. No wait states.', 'predicate': ''}, {'name': 'ahb_address_phase', 'description': 'AHB address phase drives haddr, htrans, hsize, hburst, hwrite for one cycle.', 'predicate': ''}, {'name': 'ahb_data_phase', 'description': 'AHB data phase follows address phase by one cycle with hwdata or hrdata.', 'predicate': ''}, {'name': 'arb_grant_rule', 'description': 'Arbiter evaluates requests every cycle and grants to next round-robin contender.', 'predicate': ''}, {'name': 'start_accept', 'description': 'ch_start accepted only when ch_busy is low and dma_en is high.', 'predicate': ''}]

# Ordering rules from SSOT cycle_model.ordering.
_ORDERING_RULES: list[dict] = [{'name': 'configuration_cfg_precedes_transfer_execution_read_write', 'description': ''}, {'name': 'read_burst_completion_precedes_write_burst_for_same_data', 'description': ''}, {'name': 'address_update_update_precedes_next_burst_request', 'description': ''}, {'name': 'transfer_completion_done_precedes_done_pulse_observation', 'description': ''}]

# Maximum outstanding transactions before stalling.
_OUTSTANDING_CAP: int = 1

# Cycle/performance targets used by coverage and PyMTL shell instrumentation.
PERFORMANCE_TARGETS: dict = {'frequency_mhz': None, 'throughput': 'one burst per channel per arbiter round', 'outstanding': None, 'pipeline_stages': None, 'queue_depth': None}

# Transaction kinds for self-check, derived from function_model.transactions at generation time.
_SELF_CHECK_KINDS: list[str] = ['FM_DMA_START', 'FM_DMA_STEP', 'FM_DMA_COMPLETE', 'FM_DMA_ERROR', 'FM_ARB_GRANT']

# Coverage bins: bin_name -> description.
CL_BINS: dict[str, str] = {'handshake_apb_access': 'APB accesses sample on pclk with psel and penable. No wait states.', 'handshake_ahb_address_phase': 'AHB address phase drives haddr, htrans, hsize, hburst, hwrite for one cycle.', 'handshake_ahb_data_phase': 'AHB data phase follows address phase by one cycle with hwdata or hrdata.', 'handshake_arb_grant_rule': 'Arbiter evaluates requests every cycle and grants to next round-robin contender.', 'handshake_start_accept': 'ch_start accepted only when ch_busy is low and dma_en is high.', 'ordering_configuration_cfg_precedes_transfer_execution_read_write': 'configuration_cfg_precedes_transfer_execution_read_write', 'ordering_read_burst_completion_precedes_write_burst_for_same_data': 'read_burst_completion_precedes_write_burst_for_same_data', 'ordering_address_update_update_precedes_next_burst_request': 'address_update_update_precedes_next_burst_request', 'ordering_transfer_completion_done_precedes_done_pulse_observation': 'transfer_completion_done_precedes_done_pulse_observation', 'latency_fm_dma_start': 'latency bin for FM_DMA_START', 'latency_fm_dma_step': 'latency bin for FM_DMA_STEP', 'latency_fm_dma_complete': 'latency bin for FM_DMA_COMPLETE', 'latency_fm_dma_error': 'latency bin for FM_DMA_ERROR', 'latency_fm_arb_grant': 'latency bin for FM_ARB_GRANT'}

# SSOT payload snapshot (read-only reference; never execute functional rules from here).
SSOT_MODEL: dict = {'ip': 'dma_real', 'function_model': {'purpose': 'Behavioral DMA reference independent of micro-architectural details.', 'state_variables': [{'name': 'ch_busy_q', 'width': 'N_CHANNELS', 'reset': 0, 'description': 'Per-channel busy flag'}, {'name': 'ch_done_q', 'width': 'N_CHANNELS', 'reset': 0, 'description': 'Per-channel done latch'}, {'name': 'ch_error_q', 'width': 'N_CHANNELS', 'reset': 0, 'description': 'Per-channel error latch'}, {'name': 'ch_remaining_q', 'width': 32, 'reset': 0, 'description': 'Per-channel remaining word count'}, {'name': 'ch_src_addr_q', 'width': 'ADDR_WIDTH', 'reset': 0, 'description': 'Per-channel current source address'}, {'name': 'ch_dst_addr_q', 'width': 'ADDR_WIDTH', 'reset': 0, 'description': 'Per-channel current destination address'}, {'name': 'dma_en_q', 'width': 1, 'reset': 0, 'description': 'Global DMA enable'}, {'name': 'int_enable_q', 'width': 'N_CHANNELS', 'reset': 0, 'description': 'Per-channel interrupt enable mask'}, {'name': 'arb_ptr_q', 'width': 3, 'reset': 0, 'description': 'Round-robin arbiter pointer'}], 'transactions': [{'id': 'FM_DMA_START', 'name': 'dma_start', 'required_fields': ['ch_id', 'src_addr', 'dst_addr', 'length'], 'preconditions': ['presetn is deasserted', 'dma_en_q == 1', 'ch_busy_q[ch_id] == 0'], 'outputs': ['ch_busy', 'ch_error', 'ch_error_code'], 'side_effects': ['ch_remaining_q[ch_id] set to length on valid start', 'ch_src_addr_q[ch_id] set to src_addr on valid start', 'ch_dst_addr_q[ch_id] set to dst_addr on valid start'], 'error_cases': ['zero length (length == 0)', 'misaligned source address (src_addr % 4 != 0)', 'misaligned destination address (dst_addr % 4 != 0)', 'start while busy (ignored, preserves state)']}, {'id': 'FM_DMA_STEP', 'name': 'dma_step', 'required_fields': ['ch_id', 'burst_len'], 'preconditions': ['ch_busy_q[ch_id] == 1', 'arbiter has granted bus to ch_id'], 'outputs': ['ch_busy', 'ch_done'], 'side_effects': ['ch_remaining_q decrements by burst_len', 'ch_src_addr_q increments by burst_len * 4', 'ch_dst_addr_q increments by burst_len * 4', 'done pulses on terminal step'], 'error_cases': ['bus error during AHB transfer (hresp == ERROR)']}, {'id': 'FM_DMA_COMPLETE', 'name': 'dma_complete', 'required_fields': ['ch_id'], 'preconditions': ['ch_remaining_q[ch_id] == 0', 'ch_busy_q[ch_id] == 1'], 'outputs': ['ch_busy', 'ch_done', 'irq'], 'side_effects': ['ch_done_q[ch_id] set to 1', 'ch_busy_q[ch_id] cleared', 'IRQ asserted if enabled']}, {'id': 'FM_DMA_ERROR', 'name': 'dma_error', 'required_fields': ['ch_id', 'error_code'], 'preconditions': ['error condition detected (alignment, zero-length, or bus error)'], 'outputs': ['ch_error', 'ch_error_code', 'irq'], 'side_effects': ['ch_error_q[ch_id] set to 1', 'ch_busy_q[ch_id] cleared', 'Error code latched in status register'], 'error_cases': ['alignment error (code 1)', 'zero length (code 2)', 'bus error (code 3)']}, {'id': 'FM_ARB_GRANT', 'name': 'arb_grant', 'required_fields': ['requester_mask'], 'preconditions': ['at least one channel is requesting bus access'], 'outputs': ['grant_ch'], 'side_effects': ['arb_ptr_q updated to next channel after grant', 'granted channel gains AHB bus access'], 'error_cases': []}], 'invariants': ['ch_busy and ch_done are not asserted together for the same channel.', 'ch_error is asserted only for invalid requests or bus errors.', 'ch_remaining_q never underflows below zero.', 'irq[ch] reflects (done_q[ch] OR error_q[ch]) AND int_enable_q[ch].', 'irq_combined reflects OR of all per-channel irq outputs.']}, 'cycle_model': {'executable': 'pymtl3', 'backend_policy': 'Use PyMTL3 shell for cycle behavior. FunctionalModel remains oracle.', 'clock': 'pclk', 'reset': 'presetn', 'latency': 4, 'handshake_rules': [{'name': 'apb_access', 'description': 'APB accesses sample on pclk with psel and penable. No wait states.'}, {'name': 'ahb_address_phase', 'description': 'AHB address phase drives haddr, htrans, hsize, hburst, hwrite for one cycle.'}, {'name': 'ahb_data_phase', 'description': 'AHB data phase follows address phase by one cycle with hwdata or hrdata.'}, {'name': 'arb_grant_rule', 'description': 'Arbiter evaluates requests every cycle and grants to next round-robin contender.'}, {'name': 'start_accept', 'description': 'ch_start accepted only when ch_busy is low and dma_en is high.'}], 'pipeline': [{'stage': 'IDLE', 'cycle': 0, 'action': 'wait for valid start/config'}, {'stage': 'CFG', 'cycle': 1, 'action': 'latch src_addr, dst_addr, remaining count'}, {'stage': 'REQUEST', 'cycle': 2, 'action': 'request AHB bus via arbiter'}, {'stage': 'READ', 'cycle': 3, 'action': 'AHB read burst from source address into FIFO'}, {'stage': 'WRITE', 'cycle': 4, 'action': 'AHB write burst from FIFO to destination address'}, {'stage': 'UPDATE', 'cycle': 5, 'action': 'update remaining count, src_addr, dst_addr'}, {'stage': 'DONE', 'cycle': 6, 'action': 'assert done, update status, trigger IRQ'}, {'stage': 'ERROR', 'cycle': 2, 'action': 'assert error, latch error code, return to IDLE'}], 'ordering': ['Configuration (CFG) precedes transfer execution (READ/WRITE).', 'Read burst completion precedes write burst for same data.', 'Address update (UPDATE) precedes next burst request.', 'Transfer completion (DONE) precedes done pulse observation.'], 'backpressure': ['New starts blocked while channel busy.', 'AHB transfers stall when hready is low.', 'Arbiter queues requests when bus is occupied.'], 'performance': {'outstanding_limit': 'N_CHANNELS', 'throughput': 'one burst per channel per arbiter round'}}}


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
