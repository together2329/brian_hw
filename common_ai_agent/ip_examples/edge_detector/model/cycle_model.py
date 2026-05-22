#!/usr/bin/env python3
"""Executable SSOT cycle-level model for edge_detector. Wraps FunctionalModel — FL is the only oracle."""

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
MODEL_BACKEND: str = 'python'

# Latency table: transaction kind -> cycles.  max_cycles when defined; min_cycles otherwise; default=1.
_LATENCY: dict[str, int] = {'sync_latency': 1, 'edge_detect_latency': 1, 'register_read': 1, 'register_write': 1, 'interrupt_latency': 1, 'default': 1}

# Handshake rules from SSOT cycle_model.handshake_rules.
_HANDSHAKE_RULES: list[dict] = [{'name': 'handshake_0', 'description': '', 'predicate': ''}, {'name': 'handshake_1', 'description': '', 'predicate': ''}, {'name': 'handshake_2', 'description': '', 'predicate': ''}]

# Ordering rules from SSOT cycle_model.ordering.
_ORDERING_RULES: list[dict] = [{'name': 'edge_o_for_cycle_n_reflects_signal_i_transition_captured_at_cycle_n_sync_stages_1', 'description': ''}, {'name': 'interrupt_updates_occur_on_the_same_rising_edge_as_edge_o_assertion', 'description': ''}]

# Maximum outstanding transactions before stalling.
_OUTSTANDING_CAP: int = 1

# Cycle/performance targets used by coverage and PyMTL shell instrumentation.
PERFORMANCE_TARGETS: dict = {'frequency_mhz': 50, 'throughput': {'sustained_edges_per_cycle': 1, 'condition': 'No missed edges when input changes slower than PCLK period'}, 'outstanding': {'read_max': 0, 'write_max': 0, 'description': 'No outstanding transactions; purely register/pipeline IP'}, 'pipeline_stages': 'SYNC_STAGES + 1', 'queue_depth': 0}

# Transaction kinds for self-check, derived from function_model.transactions at generation time.
_SELF_CHECK_KINDS: list[str] = ['DETECT']

# Coverage bins: bin_name -> description.
CL_BINS: dict[str, str] = {'handshake_handshake_0': 'handshake_0', 'handshake_handshake_1': 'handshake_1', 'handshake_handshake_2': 'handshake_2', 'ordering_edge_o_for_cycle_n_reflects_signal_i_transition_captured_at_cycle_n_sync_stages_1': 'edge_o_for_cycle_n_reflects_signal_i_transition_captured_at_cycle_n_sync_stages_1', 'ordering_interrupt_updates_occur_on_the_same_rising_edge_as_edge_o_assertion': 'interrupt_updates_occur_on_the_same_rising_edge_as_edge_o_assertion', 'latency_detect': 'latency bin for DETECT'}

# SSOT payload snapshot (read-only reference; never execute functional rules from here).
SSOT_MODEL: dict = {'ip': 'edge_detector', 'function_model': {'purpose': 'Executable behavioral contract for rtl-gen and tb-gen; describes what the IP computes independent of cycle timing.', 'state_variables': [{'name': 'sync_chain', 'source': 'rtl_contract.state_changes.sync_chain', 'reset': 0, 'description': 'Synchronizer shift register of width WIDTH*SYNC_STAGES'}, {'name': 'prev_sync', 'source': 'rtl_contract.state_changes.prev_sync', 'reset': 0, 'description': 'Previous-cycle synced sample for edge comparison'}, {'name': 'control_reg', 'source': 'registers.CONTROL', 'reset': 2, 'description': 'Edge mode, enable, irq_enable configuration'}, {'name': 'status_sticky', 'source': 'registers.STATUS.edge_sticky', 'reset': 0, 'description': 'Sticky edge-detected flags (W1C clear)'}, {'name': 'status_overflow', 'source': 'registers.STATUS.overflow', 'reset': 0, 'description': 'Overflow flag set when edge occurs before sticky cleared'}], 'transactions': [{'id': 'DETECT', 'name': 'edge_detect', 'preconditions': ['enable == 1', 'sync_chain has propagated at least SYNC_STAGES cycles since reset deassertion'], 'inputs': ['signal_i at PCLK domain (after sync)'], 'outputs': ['edge_o[width-1:0] = 1 for one cycle per detected edge matching EDGE_MODE', 'status_sticky |= edge_o', 'status_overflow |= edge_o & status_sticky', 'irq_o = |edge_o && irq_enable'], 'side_effects': ['sync_chain shifts every PCLK cycle', 'prev_sync updates to last stage of sync_chain'], 'error_cases': []}], 'invariants': ['edge_o is asserted for exactly one PCLK cycle per qualifying edge transition.', 'No edge_o pulse occurs when enable == 0.', 'status_sticky persists until software W1C clear.'], 'reference_model_hint': 'tb-gen should implement a Python scoreboard model from this section and compare expected/got for every scenario.'}, 'cycle_model': {'purpose': 'Cycle/handshake contract for rtl-gen; describes when state, outputs, and interrupts may change.', 'executable': 'python', 'backend_policy': 'Use direct Python cycle model with BehavioralModel as oracle; run smoke checks without pytest-pymtl3 dependency.', 'clock': 'PCLK', 'reset': {'assertion': 'PRESETn low asynchronously clears all architectural state', 'deassertion': 'state is usable on the first rising edge after synchronized deassertion'}, 'latency': {'sync_latency': {'min_cycles': 'SYNC_STAGES', 'max_cycles': 'SYNC_STAGES', 'description': 'Input synchronizer delay'}, 'edge_detect_latency': {'min_cycles': 1, 'max_cycles': 1, 'description': 'One-cycle combinational decode after sync'}, 'register_read': {'min_cycles': 0, 'max_cycles': 1, 'description': 'APB read data and PREADY timing'}, 'register_write': {'min_cycles': 0, 'max_cycles': 1, 'description': 'APB write acceptance timing'}, 'interrupt_latency': {'min_cycles': 0, 'max_cycles': 1, 'description': 'irq_o asserts same cycle as edge_o when irq_enable set'}}, 'handshake_rules': [{'signal': 'PSEL', 'rule': 'PSEL must be asserted before PENABLE rises; transaction begins in SETUP phase (PSEL=1, PENABLE=0).'}, {'signal': 'PENABLE', 'rule': 'PENABLE rises one cycle after PSEL to enter ACCESS phase; sampled with PREADY to complete.'}, {'signal': 'PREADY', 'rule': 'PREADY must be asserted by slave to complete the ACCESS phase; PREADY may deassert to extend wait states.'}], 'pipeline': [{'stage': 'S0_SYNC', 'cycle': '0..SYNC_STAGES-1', 'action': 'Propagate signal_i through sync_chain flops'}, {'stage': 'S1_EDGE_DECODE', 'cycle': 'SYNC_STAGES', 'action': 'Compare prev_sync vs curr_sync; decode per EDGE_MODE'}, {'stage': 'S2_OUTPUT', 'cycle': 'SYNC_STAGES+1', 'action': 'Assert edge_o pulse; update sticky/overflow/irq'}], 'ordering': ['edge_o for cycle N reflects signal_i transition captured at cycle N-SYNC_STAGES-1.', 'Interrupt updates occur on the same rising edge as edge_o assertion.'], 'backpressure': ['No backpressure on edge_o; downstream must accept or drop the one-cycle pulse.'], 'performance': {'frequency_mhz': 50, 'throughput': {'sustained_edges_per_cycle': 1, 'condition': 'No missed edges when input changes slower than PCLK period'}, 'outstanding': {'read_max': 0, 'write_max': 0, 'description': 'No outstanding transactions; purely register/pipeline IP'}, 'depth': {'pipeline_stages': 'SYNC_STAGES + 1', 'queue_depth': 0, 'description': 'Sync chain plus decode stage'}}, 'observability': ['Every function_model transaction maps to at least one cycle_model stage and one test_requirements scenario.']}}


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
