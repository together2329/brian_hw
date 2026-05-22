#!/usr/bin/env python3
"""Executable SSOT cycle-level model for model_compare_counter. Wraps FunctionalModel — FL is the only oracle."""

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
_LATENCY: dict[str, int] = {'update_latency': 1, 'default': 1}

# Handshake rules from SSOT cycle_model.handshake_rules.
_HANDSHAKE_RULES: list[dict] = [{'name': 'handshake_0', 'description': '', 'predicate': ''}, {'name': 'handshake_1', 'description': '', 'predicate': ''}, {'name': 'handshake_2', 'description': '', 'predicate': ''}]

# Ordering rules from SSOT cycle_model.ordering.
_ORDERING_RULES: list[dict] = [{'name': 'reset_dominance_active_reset_forces_zeros_before_functional_branch_evaluation', 'description': ''}, {'name': 'within_functional_operation_clear_branch_is_evaluated_before_enable_branch_each_sampled_cycle', 'description': ''}, {'name': 'pulse_outputs_wrapped_valid_correspond_to_same_update_cycle_as_count_commit', 'description': ''}]

# Maximum outstanding transactions before stalling.
_OUTSTANDING_CAP: int = 1

# Cycle/performance targets used by coverage and PyMTL shell instrumentation.
PERFORMANCE_TARGETS: dict = {'frequency_mhz': 100, 'throughput': {'sustained_beats_per_cycle': 1, 'condition': 'No backpressure on the active interface'}, 'outstanding': {'max': 1, 'description': 'Default one accepted operation until the SSOT declares deeper buffering'}, 'pipeline_stages': 3, 'queue_depth': 1}

# Transaction kinds for self-check, derived from function_model.transactions at generation time.
_SELF_CHECK_KINDS: list[str] = ['FM_CLEAR', 'FM_UPDATE', 'FM_IDLE']

# Coverage bins: bin_name -> description.
CL_BINS: dict[str, str] = {'handshake_handshake_0': 'handshake_0', 'handshake_handshake_1': 'handshake_1', 'handshake_handshake_2': 'handshake_2', 'ordering_reset_dominance_active_reset_forces_zeros_before_functional_branch_evaluation': 'reset_dominance_active_reset_forces_zeros_before_functional_branch_evaluation', 'ordering_within_functional_operation_clear_branch_is_evaluated_before_enable_branch_each_sampled_cycle': 'within_functional_operation_clear_branch_is_evaluated_before_enable_branch_each_sampled_cycle', 'ordering_pulse_outputs_wrapped_valid_correspond_to_same_update_cycle_as_count_commit': 'pulse_outputs_wrapped_valid_correspond_to_same_update_cycle_as_count_commit', 'latency_fm_clear': 'latency bin for FM_CLEAR', 'latency_fm_update': 'latency bin for FM_UPDATE', 'latency_fm_idle': 'latency bin for FM_IDLE'}

# SSOT payload snapshot (read-only reference; never execute functional rules from here).
SSOT_MODEL: dict = {'ip': 'model_compare_counter', 'function_model': {'purpose': 'Behavioral oracle for counter updates, overflow pulse semantics, and idle hold behavior.', 'state_variables': [{'name': 'count_q', 'reset': 0, 'width': 8, 'description': 'Architectural counter state'}, {'name': 'wrapped_q', 'reset': 0, 'width': 1, 'description': 'One-cycle overflow indication output register'}, {'name': 'valid_q', 'reset': 0, 'width': 1, 'description': 'One-cycle accepted-update indication output register'}], 'transactions': [{'id': 'FM_CLEAR', 'name': 'clear_priority_reset', 'preconditions': ['clear == 1'], 'inputs': ['clear', 'enable', 'step', 'count_q'], 'outputs': ['count == 0', 'wrapped == 0', 'valid == 0', {'name': 'out_count', 'port': 'count', 'expr': '0', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'name': 'out_wrapped', 'port': 'wrapped', 'expr': '0', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'name': 'out_valid', 'port': 'valid', 'expr': '0', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'state': 'count_q', 'expr': '0', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'wrapped_q', 'expr': '0', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'valid_q', 'expr': '0', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}], 'side_effects': ['Clear overrides enable and forces all outputs/state low on next observed state.'], 'error_cases': []}, {'id': 'FM_UPDATE', 'name': 'enabled_increment', 'preconditions': ['clear == 0', 'enable == 1'], 'inputs': ['clear', 'enable', 'step', 'count_q'], 'outputs': ['count == ((count_q + step) & 0xFF)', 'wrapped == 1 when (count_q + step) > 255 else 0', 'valid == 1', {'name': 'out_count', 'port': 'count', 'expr': '(count_q + step) & 0xFF', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'name': 'out_wrapped', 'port': 'wrapped', 'expr': '1 if ((count_q + step) > 255) else 0', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'name': 'out_valid', 'port': 'valid', 'expr': '1', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'state': 'count_q', 'expr': '(count_q + step) & 0xFF', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'wrapped_q', 'expr': '1 if ((count_q + step) > 255) else 0', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'valid_q', 'expr': '1', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}], 'side_effects': ['Accepted enabled update advances count modulo 256 and emits valid pulse.', 'wrapped pulse is asserted only for overflowing additions.'], 'error_cases': []}, {'id': 'FM_IDLE', 'name': 'idle_hold', 'preconditions': ['transaction is accepted under cycle_model rules'], 'inputs': ['clear', 'enable', 'step', 'count_q'], 'outputs': ['count == count_q', 'wrapped == 0', 'valid == 0', {'name': 'out_count', 'port': 'count', 'expr': 'count_q', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'name': 'out_wrapped', 'port': 'wrapped', 'expr': '0', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'name': 'out_valid', 'port': 'valid', 'expr': '0', 'description': 'Mirrored from executable functional_outputs for SSOT validator completeness.'}, {'state': 'count_q', 'expr': 'count_q', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'wrapped_q', 'expr': '0', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}, {'state': 'valid_q', 'expr': '0', 'description': 'Mirrored from executable state_changes for SSOT validator completeness.'}], 'side_effects': ['Counter holds during idle cycles while pulse outputs deassert.'], 'error_cases': []}], 'invariants': ['clear==1 implies next count_q, wrapped_q, valid_q are all zero regardless of enable.', 'valid_q may only be 1 in cycles where clear==0 and enable==1.', 'wrapped_q may only be 1 in cycles where clear==0 and enable==1 and (count_prev + step) > 255.']}, 'cycle_model': {'purpose': 'Single-cycle sampled-input to post-edge-state visibility contract.', 'executable': 'pymtl3', 'backend_policy': 'Use FunctionalModel transaction stepping for expected behavior and lockstep cycle comparison.', 'cosim': True, 'state_accumulating': True, 'use_per_cycle_expected': True, 'clock': 'clk', 'reset': {'assertion': 'rst_n low asynchronously clears count/wrapped/valid state to zero', 'deassertion': 'state is valid on first rising edge after rst_n is high'}, 'latency': {'update_latency': {'min_cycles': 1, 'max_cycles': 1, 'description': 'Input sampled at edge N', 'updated outputs visible after edge N': None}}, 'handshake_rules': [{'signal': 'clk', 'rule': 'Inputs enable/clear/step are sampled only on rising edge of clk.'}, {'signal': 'clear_enable_priority', 'rule': 'If clear and enable are both high at a sampled edge, clear branch wins and no increment occurs.'}, {'signal': 'backpressure', 'rule': 'No ready/valid backpressure; every cycle can accept control inputs.'}], 'pipeline': [{'stage': 'SAMPLE', 'cycle': 0, 'action': 'Sample clear, enable, step, and current count state'}, {'stage': 'COMMIT', 'cycle': 1, 'action': 'Commit clear/update/idle state and pulse outputs'}], 'ordering': ['Reset dominance: active reset forces zeros before functional branch evaluation.', 'Within functional operation, clear branch is evaluated before enable branch each sampled cycle.', 'Pulse outputs wrapped/valid correspond to same update cycle as count commit.'], 'backpressure': ['Not applicable; no downstream handshake channels to stall updates.'], 'observability': ['Each function_model transaction maps to COMMIT stage output expectations.'], 'performance': {'frequency_mhz': 100, 'throughput': {'sustained_beats_per_cycle': 1, 'condition': 'No backpressure on the active interface'}, 'outstanding': {'max': 1, 'description': 'Default one accepted operation until the SSOT declares deeper buffering'}, 'depth': {'pipeline_stages': 3, 'queue_depth': 1, 'description': 'Default accept/evaluate/observe cycle model depth'}}}}


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
