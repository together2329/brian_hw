#!/usr/bin/env python3
"""Executable SSOT cycle-level model for simple_pwm. Wraps FunctionalModel — FL is the only oracle."""

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
_LATENCY: dict[str, int] = {'counter_update': 1, 'pwm_output': 1, 'default': 1}

# Handshake rules from SSOT cycle_model.handshake_rules.
_HANDSHAKE_RULES: list[dict] = [{'name': 'handshake_0', 'description': '', 'predicate': ''}]

# Ordering rules from SSOT cycle_model.ordering.
_ORDERING_RULES: list[dict] = [{'name': 'counter_update_and_output_comparison_occur_in_the_same_clock_cycle', 'description': ''}]

# Maximum outstanding transactions before stalling.
_OUTSTANDING_CAP: int = 1

# Cycle/performance targets used by coverage and PyMTL shell instrumentation.
PERFORMANCE_TARGETS: dict = {'frequency_mhz': 100, 'throughput': {'sustained_operations_per_cycle': 1, 'condition': 'enable asserted and period > 0'}, 'outstanding': {'max': 1, 'description': 'Single-cycle counter operation'}, 'pipeline_stages': 1, 'queue_depth': None}

# Transaction kinds for self-check, derived from function_model.transactions at generation time.
_SELF_CHECK_KINDS: list[str] = ['FM1', 'FM2', 'FM3']

# Coverage bins: bin_name -> description.
CL_BINS: dict[str, str] = {'handshake_handshake_0': 'handshake_0', 'ordering_counter_update_and_output_comparison_occur_in_the_same_clock_cycle': 'counter_update_and_output_comparison_occur_in_the_same_clock_cycle', 'latency_fm1': 'latency bin for FM1', 'latency_fm2': 'latency bin for FM2', 'latency_fm3': 'latency bin for FM3'}

# SSOT payload snapshot (read-only reference; never execute functional rules from here).
SSOT_MODEL: dict = {'ip': 'simple_pwm', 'function_model': {'purpose': 'Executable behavioral contract for rtl-gen and tb-gen', 'state_variables': [{'name': 'counter', 'source': 'internal', 'reset': 0, 'description': 'Free-running counter, wraps at period'}], 'transactions': [{'id': 'FM1', 'name': 'pwm_active_high', 'preconditions': ['enable == 1', 'counter < duty_cycle'], 'inputs': ['duty_cycle', 'period'], 'outputs': [{'name': 'pwm_out', 'value': 1}], 'side_effects': ['counter increments by 1'], 'error_cases': []}, {'id': 'FM2', 'name': 'pwm_active_low', 'preconditions': ['enable == 1', 'counter >= duty_cycle'], 'inputs': ['duty_cycle', 'period'], 'outputs': [{'name': 'pwm_out', 'value': 0}], 'side_effects': ['counter increments by 1'], 'error_cases': []}, {'id': 'FM3', 'name': 'pwm_idle', 'preconditions': ['enable == 0'], 'inputs': [], 'outputs': [{'name': 'pwm_out', 'value': 0}], 'side_effects': ['counter resets to 0'], 'error_cases': []}], 'invariants': ['pwm_out is 0 whenever enable is 0', 'counter resets to 0 when it reaches period', 'counter is 0 whenever enable is 0']}, 'cycle_model': {'purpose': 'Cycle-accurate contract for rtl-gen', 'executable': 'python', 'clock': 'clk', 'reset': {'assertion': 'rst_n low asynchronously clears counter to 0 and pwm_out to 0', 'deassertion': 'state is usable on the first rising edge after synchronized deassertion'}, 'latency': {'counter_update': {'min_cycles': 1, 'max_cycles': 1, 'description': 'Counter increments or wraps every clock edge when enabled'}, 'pwm_output': {'min_cycles': 1, 'max_cycles': 1, 'description': 'pwm_out reflects counter vs duty_cycle comparison on same edge'}}, 'handshake_rules': [{'signal': 'pwm_out', 'rule': 'Combinational output derived from counter vs duty_cycle comparison; no valid/ready handshake'}], 'pipeline': [{'stage': 'S0_COUNTER_UPDATE', 'cycle': 1, 'action': 'Increment counter or wrap to 0 when enable=1; hold at 0 when enable=0'}, {'stage': 'S1_COMPARE_OUTPUT', 'cycle': 1, 'action': 'Compare counter with duty_cycle; drive pwm_out accordingly'}], 'ordering': ['Counter update and output comparison occur in the same clock cycle.'], 'backpressure': [], 'performance': {'frequency_mhz': 100, 'throughput': {'sustained_operations_per_cycle': 1, 'condition': 'enable asserted and period > 0'}, 'outstanding': {'max': 1, 'description': 'Single-cycle counter operation'}, 'depth': {'pipeline_stages': 1, 'description': 'Single-stage counter and compare'}}, 'observability': ['counter value is observable via internal state', 'pwm_out is the primary observable output']}}


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
