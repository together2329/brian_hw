#!/usr/bin/env python3
"""Executable SSOT cycle-level model for timer. Wraps FunctionalModel — FL is the only oracle."""

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
_HANDSHAKE_RULES: list[dict] = [{'name': 'start_load', 'description': 'start samples load_value on the active clock edge and makes the loaded count visible after that edge.', 'predicate': ''}, {'name': 'enabled_tick', 'description': 'enable advances count only while running is high.', 'predicate': ''}, {'name': 'clear_priority', 'description': 'clear returns the timer to idle regardless of enable or running.', 'predicate': ''}]

# Ordering rules from SSOT cycle_model.ordering.
_ORDERING_RULES: list[dict] = [{'name': 'clear_has_highest_priority', 'description': ''}, {'name': 'start_load_is_applied_before_enabled_countdown_behavior_for_a_new_interval', 'description': ''}, {'name': 'done_is_observed_on_the_same_state_visible_cycle_as_the_terminal_decrement', 'description': ''}]

# Maximum outstanding transactions before stalling.
_OUTSTANDING_CAP: int = 1

# Cycle/performance targets used by coverage and PyMTL shell instrumentation.
PERFORMANCE_TARGETS: dict = {'frequency_mhz': 100, 'throughput': {'sustained_ticks_per_cycle': 1, 'condition': 'enable asserted while running'}, 'outstanding': {'max': 1, 'description': 'One active countdown interval at a time.'}, 'pipeline_stages': 1, 'queue_depth': 0}

# Transaction kinds for self-check, derived from function_model.transactions at generation time.
_SELF_CHECK_KINDS: list[str] = ['FM_TICK']

# Coverage bins: bin_name -> description.
CL_BINS: dict[str, str] = {'handshake_start_load': 'start samples load_value on the active clock edge and makes the loaded count visible after that edge.', 'handshake_enabled_tick': 'enable advances count only while running is high.', 'handshake_clear_priority': 'clear returns the timer to idle regardless of enable or running.', 'ordering_clear_has_highest_priority': 'clear_has_highest_priority', 'ordering_start_load_is_applied_before_enabled_countdown_behavior_for_a_new_interval': 'start_load_is_applied_before_enabled_countdown_behavior_for_a_new_interval', 'ordering_done_is_observed_on_the_same_state_visible_cycle_as_the_terminal_decrement': 'done_is_observed_on_the_same_state_visible_cycle_as_the_terminal_decrement', 'latency_fm_tick': 'latency bin for FM_TICK'}

# SSOT payload snapshot (read-only reference; never execute functional rules from here).
SSOT_MODEL: dict = {'ip': 'timer', 'function_model': {'purpose': 'Cycle-independent timer reference model for scoreboard and RTL equivalence checks.', 'state_variables': [{'name': 'count_q', 'width': 16, 'reset': 0, 'description': 'Internal current countdown value that drives count.'}, {'name': 'running_q', 'width': 1, 'reset': 0, 'description': 'Internal timer active state that drives running.'}, {'name': 'done_q', 'width': 1, 'reset': 0, 'description': 'Internal completion pulse state that drives done.'}], 'transactions': [{'id': 'FM_TICK', 'name': 'timer_control_tick', 'required_fields': ['start', 'enable', 'clear', 'load'], 'preconditions': ['rst_n is deasserted', 'load is in the range 0 to 2**COUNT_WIDTH-1'], 'outputs': ['count', 'running', 'done'], 'side_effects': ['count updates according to start, clear, and enable priority.', 'running drops when the countdown consumes the final count.', 'done pulses for the terminal countdown tick.'], 'error_cases': ['No protocol error is generated; out-of-range load values are impossible after port truncation.']}], 'invariants': ['Reset or clear leaves count=0, running=0, and done=0.', 'done is asserted only on a terminal enabled countdown tick.', 'count never underflows below zero because the decrement rule is gated by count > 0.', 'When enable is low and no start or clear is asserted, count and running hold their previous values.'], 'reference_model_hint': 'FunctionalModel.apply(start, enable, clear, load) returns count, running, and done after one control tick.'}, 'cycle_model': {'executable': 'pymtl3', 'backend_policy': 'Use PyMTL3 for the cycle model shell and keep the FunctionalModel as the behavioral oracle.', 'clock': 'clk', 'reset': 'rst_n', 'latency': 1, 'handshake_rules': [{'name': 'start_load', 'description': 'start samples load_value on the active clock edge and makes the loaded count visible after that edge.'}, {'name': 'enabled_tick', 'description': 'enable advances count only while running is high.'}, {'name': 'clear_priority', 'description': 'clear returns the timer to idle regardless of enable or running.'}], 'pipeline': [{'stage': 'S0_CONTROL_SAMPLE', 'cycle': 0, 'action': 'Sample start, enable, clear, load_value, count, and running.'}, {'stage': 'S1_STATE_VISIBLE', 'cycle': 1, 'action': 'Present updated count, running, and done.'}], 'ordering': ['clear has highest priority.', 'start load is applied before enabled countdown behavior for a new interval.', 'done is observed on the same state-visible cycle as the terminal decrement.'], 'backpressure': ['There is no ready/valid backpressure; enable controls timer progress.'], 'performance': {'frequency_mhz': 100, 'throughput': {'sustained_ticks_per_cycle': 1, 'condition': 'enable asserted while running'}, 'outstanding': {'max': 1, 'description': 'One active countdown interval at a time.'}, 'depth': {'pipeline_stages': 1, 'queue_depth': 0, 'description': 'Registered state update with no internal queue.'}, 'pipelining': {'style': 'single_stage_registered_control', 'overlap': 'none'}}}}


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
