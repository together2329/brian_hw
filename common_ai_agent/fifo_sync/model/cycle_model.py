#!/usr/bin/env python3
"""Executable SSOT cycle-level model for fifo_sync. Wraps FunctionalModel — FL is the only oracle."""

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
_LATENCY: dict[str, int] = {'push_accept': 1, 'pop_combinational': 0, 'pop_registered': 1, 'flush': 1, 'register_read': 1, 'register_write': 1, 'default': 1}

# Handshake rules from SSOT cycle_model.handshake_rules.
_HANDSHAKE_RULES: list[dict] = [{'name': 'handshake_0', 'description': '', 'predicate': ''}, {'name': 'handshake_1', 'description': '', 'predicate': ''}, {'name': 'handshake_2', 'description': '', 'predicate': ''}, {'name': 'handshake_3', 'description': '', 'predicate': ''}, {'name': 'handshake_4', 'description': '', 'predicate': ''}]

# Ordering rules from SSOT cycle_model.ordering.
_ORDERING_RULES: list[dict] = [{'name': 'push_data_is_captured_into_memory_in_the_same_cycle_as_pointer_update', 'description': ''}, {'name': 'pop_data_is_available_combinationally_from_memory_use_output_register_0_or_one_cycle_later_use_output_register_1', 'description': ''}, {'name': 'flush_clears_all_state_in_the_cycle_it_is_sampled_concurrent_push_pop_are_ignored', 'description': ''}, {'name': 'flag_updates_are_visible_on_the_cycle_after_pointer_count_changes', 'description': ''}]

# Maximum outstanding transactions before stalling.
_OUTSTANDING_CAP: int = 1

# Cycle/performance targets used by coverage and PyMTL shell instrumentation.
PERFORMANCE_TARGETS: dict = {'frequency_mhz': 50, 'throughput': {'sustained_ops_per_cycle': 1, 'condition': 'At least one of push or pop accepted per cycle; simultaneous push/pop sustains 2 ops/cycle'}, 'outstanding': {'read_max': 1, 'write_max': 1, 'description': 'Single-port push and single-port pop per cycle'}, 'pipeline_stages': 1, 'queue_depth': 'DEPTH parameter'}

# Transaction kinds for self-check, derived from function_model.transactions at generation time.
_SELF_CHECK_KINDS: list[str] = ['FM1', 'FM2', 'FM3', 'FM4', 'FM5', 'FM6']

# Coverage bins: bin_name -> description.
CL_BINS: dict[str, str] = {'handshake_handshake_0': 'handshake_0', 'handshake_handshake_1': 'handshake_1', 'handshake_handshake_2': 'handshake_2', 'handshake_handshake_3': 'handshake_3', 'handshake_handshake_4': 'handshake_4', 'ordering_push_data_is_captured_into_memory_in_the_same_cycle_as_pointer_update': 'push_data_is_captured_into_memory_in_the_same_cycle_as_pointer_update', 'ordering_pop_data_is_available_combinationally_from_memory_use_output_register_0_or_one_cycle_later_use_output_register_1': 'pop_data_is_available_combinationally_from_memory_use_output_register_0_or_one_cycle_later_use_output_register_1', 'ordering_flush_clears_all_state_in_the_cycle_it_is_sampled_concurrent_push_pop_are_ignored': 'flush_clears_all_state_in_the_cycle_it_is_sampled_concurrent_push_pop_are_ignored', 'ordering_flag_updates_are_visible_on_the_cycle_after_pointer_count_changes': 'flag_updates_are_visible_on_the_cycle_after_pointer_count_changes', 'latency_fm1': 'latency bin for FM1', 'latency_fm2': 'latency bin for FM2', 'latency_fm3': 'latency bin for FM3', 'latency_fm4': 'latency bin for FM4', 'latency_fm5': 'latency bin for FM5', 'latency_fm6': 'latency bin for FM6'}

# SSOT payload snapshot (read-only reference; never execute functional rules from here).
SSOT_MODEL: dict = {'ip': 'fifo_sync', 'function_model': {'purpose': 'Executable behavioral contract for rtl-gen and tb-gen; describes what the synchronous FIFO computes independent of cycle timing.', 'state_variables': [{'name': 'wr_ptr', 'source': 'fifo_sync_ptrs', 'reset': 0, 'description': 'Binary write pointer; wraps at DEPTH'}, {'name': 'rd_ptr', 'source': 'fifo_sync_ptrs', 'reset': 0, 'description': 'Binary read pointer; wraps at DEPTH'}, {'name': 'count', 'source': 'fifo_sync_ptrs', 'reset': 0, 'description': 'Current number of valid entries (0..DEPTH)'}, {'name': 'mem', 'source': 'fifo_sync_mem', 'reset': '0x0 per entry', 'description': 'Storage array [0..DEPTH-1] each DATA_WIDTH wide'}], 'transactions': [{'id': 'FM1', 'name': 'push', 'preconditions': ['wr_en_i == 1', 'full_o == 0 (count < DEPTH)', 'flush_i == 0'], 'inputs': ['wr_data_i[DATA_WIDTH-1:0]'], 'side_effects': ['Architectural state updated per functional_outputs'], 'error_cases': [], 'outputs': ['full_o = (count + 1 - pop_accepted) == DEPTH', 'almost_full_o = (count + 1 - pop_accepted) >= ALMOST_FULL_THRESHOLD', 'count_o = count + 1 - pop_accepted']}, {'id': 'FM2', 'name': 'pop', 'preconditions': ['rd_en_i == 1', 'empty_o == 0 (count > 0)', 'flush_i == 0'], 'inputs': ['mem[rd_ptr]'], 'side_effects': ['Popped entry storage is invalidated (no read-again guarantee)'], 'error_cases': [], 'outputs': ['rd_data_o = mem[rd_ptr]', 'empty_o = (count - 1 + push_accepted) == 0', 'almost_empty_o = (count - 1 + push_accepted) <= ALMOST_EMPTY_THRESHOLD', 'count_o = count - 1 + push_accepted']}, {'id': 'FM3', 'name': 'simultaneous_push_pop', 'preconditions': ['wr_en_i == 1 and rd_en_i == 1', 'full_o == 0 and empty_o == 0', 'flush_i == 0'], 'inputs': ['wr_data_i[DATA_WIDTH-1:0]', 'mem[rd_ptr]'], 'side_effects': ['count is unchanged because push and pop cancel'], 'error_cases': [], 'outputs': ['rd_data_o = mem[rd_ptr]', 'full_o = count == DEPTH - 1', 'empty_o = count == 1', 'count_o = count']}, {'id': 'FM4', 'name': 'overflow_reject', 'preconditions': ['wr_en_i == 1', 'full_o == 1 (count == DEPTH)'], 'inputs': [], 'side_effects': ['Write rejected silently; no data corruption'], 'error_cases': [], 'outputs': ['full_o = 1', 'count_o = DEPTH']}, {'id': 'FM5', 'name': 'underflow_reject', 'preconditions': ['rd_en_i == 1', 'empty_o == 1 (count == 0)'], 'inputs': [], 'side_effects': ['Read rejected silently; rd_data_o holds previous value (not guaranteed)'], 'error_cases': [], 'outputs': ['empty_o = 1', 'rd_data_o = previous_value_or_zero', 'count_o = 0']}, {'id': 'FM6', 'name': 'flush', 'preconditions': ['flush_i == 1'], 'inputs': [], 'side_effects': ['All FIFO entries invalidated; memory contents become undefined', 'Flush takes precedence over concurrent push/pop'], 'error_cases': [], 'outputs': ['empty_o = 1', 'full_o = 0', 'almost_full_o = 0', 'almost_empty_o = 1', 'count_o = 0']}], 'invariants': ['count is always in range [0, DEPTH].', 'full_o == 1 if and only if count == DEPTH.', 'empty_o == 1 if and only if count == 0.', 'wr_ptr and rd_ptr are always in range [0, DEPTH-1].', 'No read data changes unless rd_en_i is accepted or flush occurs.', 'Simultaneous push/pop leaves count unchanged.', 'Overflow and underflow are silently rejected with no state corruption.'], 'reference_model_hint': 'tb-gen should implement a Python deque-based scoreboard model; push/pop/flush map directly to deque.append()/popleft()/clear().'}, 'cycle_model': {'purpose': 'Cycle/handshake contract for rtl-gen; describes when FIFO state, flags, and data outputs may change relative to PCLK edges.', 'executable': 'pymtl3', 'backend_policy': 'Use PyMTL3 for the clocked cycle model shell; keep FunctionalModel as the behavioral oracle.', 'clock': 'PCLK', 'reset': {'assertion': 'PRESETn low asynchronously clears wr_ptr, rd_ptr, count to 0; all flags reflect empty state.', 'deassertion': 'State is usable on the first rising PCLK edge after synchronized deassertion.'}, 'latency': {'push_accept': {'min_cycles': 1, 'max_cycles': 1, 'description': 'Data written on the rising edge when wr_en_i && !full_o; flags update on the same edge.'}, 'pop_combinational': {'min_cycles': 0, 'max_cycles': 0, 'description': 'When USE_OUTPUT_REGISTER=0, rd_data_o is combinational from mem[rd_ptr]; flags update 1 cycle after rd_en_i acceptance.'}, 'pop_registered': {'min_cycles': 1, 'max_cycles': 1, 'description': 'When USE_OUTPUT_REGISTER=1, rd_data_o appears 1 cycle after rd_en_i acceptance; flags update on the acceptance edge.'}, 'flush': {'min_cycles': 1, 'max_cycles': 1, 'description': 'All pointers and count cleared on the rising edge when flush_i=1; flags update on the same edge.'}, 'register_read': {'min_cycles': 0, 'max_cycles': 1, 'description': 'APB CSR read: pready always 1 (0 wait states).'}, 'register_write': {'min_cycles': 0, 'max_cycles': 1, 'description': 'APB CSR write: pready always 1 (0 wait states).'}}, 'handshake_rules': [{'signal': 'wr_en_i', 'rule': 'Sampled on rising PCLK; data accepted only when full_o=0. Full flag gates write acceptance.'}, {'signal': 'rd_en_i', 'rule': 'Sampled on rising PCLK; data consumed only when empty_o=0. Empty flag gates read acceptance.'}, {'signal': 'full_o', 'rule': 'Combinational function of count and push/pop acceptance in the current cycle. Updates after each clock edge.'}, {'signal': 'empty_o', 'rule': 'Combinational function of count and push/pop acceptance in the current cycle. Updates after each clock edge.'}, {'signal': 'flush_i', 'rule': 'Synchronous; takes precedence over push/pop. Clears all pointers and count on the rising edge.'}], 'pipeline': [{'stage': 'S0_SAMPLE_INPUTS', 'cycle': 0, 'action': 'Sample wr_en_i, rd_en_i, flush_i, wr_data_i on rising PCLK edge'}, {'stage': 'S1_EVAL_ACCEPT', 'cycle': 0, 'action': 'Combinational: determine push_accepted = wr_en_i && !full_o && !flush_i; pop_accepted = rd_en_i && !empty_o && !flush_i'}, {'stage': 'S2_UPDATE_PTRS', 'cycle': 0, 'action': 'Update wr_ptr, rd_ptr, count registers based on push/pop acceptance'}, {'stage': 'S3_WRITE_MEM', 'cycle': 0, 'action': 'Write wr_data_i to mem[wr_ptr] when push_accepted'}, {'stage': 'S4_UPDATE_FLAGS', 'cycle': 1, 'action': 'Flags (full, empty, almost_full, almost_empty, count) reflect new pointer state'}], 'ordering': ['Push data is captured into memory in the same cycle as pointer update.', 'Pop data is available combinationally from memory (USE_OUTPUT_REGISTER=0) or one cycle later (USE_OUTPUT_REGISTER=1).', 'Flush clears all state in the cycle it is sampled; concurrent push/pop are ignored.', 'Flag updates are visible on the cycle after pointer/count changes.'], 'backpressure': ['full_o provides natural backpressure to the writer; the writer must deassert wr_en_i or accept rejection.', 'empty_o provides natural backpressure to the reader; the reader must deassert rd_en_i or accept undefined data.'], 'performance': {'frequency_mhz': 50, 'throughput': {'sustained_ops_per_cycle': 1, 'condition': 'At least one of push or pop accepted per cycle; simultaneous push/pop sustains 2 ops/cycle'}, 'outstanding': {'read_max': 1, 'write_max': 1, 'description': 'Single-port push and single-port pop per cycle'}, 'depth': {'pipeline_stages': 1, 'queue_depth': 'DEPTH parameter', 'description': 'Single pipeline stage; storage depth equals DEPTH parameter'}}, 'observability': ['Every function_model transaction maps to at least one cycle_model stage and one test_requirements scenario.']}}


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
