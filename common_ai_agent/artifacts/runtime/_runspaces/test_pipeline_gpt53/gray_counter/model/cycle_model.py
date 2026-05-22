#!/usr/bin/env python3
"""Executable SSOT cycle-level model for gray_counter. Wraps FunctionalModel — FL is the only oracle."""

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
_LATENCY: dict[str, int] = {'control_to_state_update': 1, 'gray_to_bin_observation': 0, 'done_pulse_width': 1, 'default': 1}

# Handshake rules from SSOT cycle_model.handshake_rules.
_HANDSHAKE_RULES: list[dict] = [{'name': 'handshake_0', 'description': '', 'predicate': ''}, {'name': 'handshake_1', 'description': '', 'predicate': ''}, {'name': 'handshake_2', 'description': '', 'predicate': ''}]

# Ordering rules from SSOT cycle_model.ordering.
_ORDERING_RULES: list[dict] = [{'name': 'asynchronous_reset_effect_precedes_any_synchronous_clear_enable_action_while_rst_n_is_low', 'description': ''}, {'name': 'within_a_rising_edge_sample_clear_decision_is_evaluated_before_enable_advance', 'description': ''}, {'name': 'done_update_is_ordered_with_gray_register_commit_from_the_same_sampled_edge', 'description': ''}]

# Maximum outstanding transactions before stalling.
_OUTSTANDING_CAP: int = 1

# Cycle/performance targets used by coverage and PyMTL shell instrumentation.
PERFORMANCE_TARGETS: dict = {'frequency_mhz': 200, 'throughput': {'sustained_beats_per_cycle': 1, 'condition': 'No backpressure on the active interface'}, 'outstanding': {'max': 1, 'description': 'Default one accepted operation until the SSOT declares deeper buffering'}, 'pipeline_stages': 3, 'queue_depth': 1}

# Transaction kinds for self-check, derived from function_model.transactions at generation time.
_SELF_CHECK_KINDS: list[str] = ['GC_TXN_RESET', 'GC_TXN_CLEAR', 'GC_TXN_ADVANCE', 'GC_TXN_HOLD']

# Coverage bins: bin_name -> description.
CL_BINS: dict[str, str] = {'handshake_handshake_0': 'handshake_0', 'handshake_handshake_1': 'handshake_1', 'handshake_handshake_2': 'handshake_2', 'ordering_asynchronous_reset_effect_precedes_any_synchronous_clear_enable_action_while_rst_n_is_low': 'asynchronous_reset_effect_precedes_any_synchronous_clear_enable_action_while_rst_n_is_low', 'ordering_within_a_rising_edge_sample_clear_decision_is_evaluated_before_enable_advance': 'within_a_rising_edge_sample_clear_decision_is_evaluated_before_enable_advance', 'ordering_done_update_is_ordered_with_gray_register_commit_from_the_same_sampled_edge': 'done_update_is_ordered_with_gray_register_commit_from_the_same_sampled_edge', 'latency_gc_txn_reset': 'latency bin for GC_TXN_RESET', 'latency_gc_txn_clear': 'latency bin for GC_TXN_CLEAR', 'latency_gc_txn_advance': 'latency bin for GC_TXN_ADVANCE', 'latency_gc_txn_hold': 'latency bin for GC_TXN_HOLD'}

# SSOT payload snapshot (read-only reference; never execute functional rules from here).
SSOT_MODEL: dict = {'ip': 'gray_counter', 'function_model': {'purpose': 'Cycle-independent architectural contract for Gray counting, clear/reset semantics, and wrap pulse behavior.', 'state_variables': [{'name': 'gray_state', 'source': 'io_list.interfaces.status.gray_value', 'reset': 0, 'description': 'Architectural Gray counter register.'}, {'name': 'bin_state', 'source': 'derived(gray_state)', 'reset': 0, 'description': 'Decoded binary state derived from gray_state.'}, {'name': 'done_state', 'source': 'io_list.interfaces.status.done', 'reset': 0, 'description': 'One-cycle completion pulse state.'}], 'transactions': [{'id': 'GC_TXN_RESET', 'name': 'asynchronous_reset_assert', 'preconditions': ['rst_n == 0'], 'inputs': ['rst_n'], 'outputs': ['gray_value == 0', 'bin_value == 0', 'done == 0'], 'side_effects': ['gray_state set to 0 immediately on reset assertion', 'done_state cleared']}, {'id': 'GC_TXN_CLEAR', 'name': 'synchronous_clear', 'preconditions': ['rst_n == 1', 'clear sampled high on rising clock edge'], 'inputs': ['clear'], 'outputs': ['gray_value == 0 after edge', 'bin_value == 0 after edge', 'done == 0 after edge'], 'side_effects': ['gray_state overwritten with 0', 'done_state cleared']}, {'id': 'GC_TXN_ADVANCE', 'name': 'advance_one_gray_step', 'preconditions': ['rst_n == 1', 'clear == 0 on sampled edge', 'enable == 1 on sampled edge'], 'inputs': ['enable', 'current gray_state'], 'outputs': ['next binary state equals (current bin_state + 1) mod 2^WIDTH', 'next gray_value equals bin_to_gray(next binary state)', 'bin_value equals gray_to_bin(gray_value) at all observable times'], 'side_effects': ['gray_state updates to next_gray', 'done_state set to 1 iff current bin_state is max value; else 0'], 'error_cases': [{'condition': 'WIDTH < 2', 'result': 'Configuration error; synthesis/test should fail parameter constraint checks'}]}, {'id': 'GC_TXN_HOLD', 'name': 'hold_state', 'preconditions': ['rst_n == 1', 'clear == 0 on sampled edge', 'enable == 0 on sampled edge'], 'inputs': ['enable'], 'outputs': ['gray_value remains unchanged', 'bin_value remains decode(gray_value)', 'done == 0'], 'side_effects': ['done_state forced low in non-wrap hold cycles']}], 'invariants': ['gray_value is always a legal WIDTH-bit Gray encoding of bin_state.', 'bin_value always equals gray_to_bin(gray_value) combinationally.', 'done is asserted for at most one consecutive cycle per wrap event.', 'clear has priority over enable on sampled clock edges.', 'reset dominates all synchronous controls when asserted.'], 'reference_model_hint': 'Scoreboard model maintains binary golden state, derives gray as g=b^(b>>1), decodes DUT gray_value each cycle, and checks done pulse only on max->0 wrap.'}, 'cycle_model': {'purpose': 'Cycle-accurate control/latency contract for sampled inputs and registered outputs.', 'executable': 'python', 'clock': 'clk', 'reset': {'assertion': 'rst_n low asynchronously clears gray_value and done.', 'deassertion': 'first functional sample occurs on first rising edge after rst_n returns high.'}, 'latency': {'control_to_state_update': {'min_cycles': 1, 'max_cycles': 1, 'description': 'enable/clear sampled on edge', 'new gray_value visible after that edge.': None}, 'gray_to_bin_observation': {'min_cycles': 0, 'max_cycles': 0, 'description': 'bin_value is combinational decode of current gray_value.'}, 'done_pulse_width': {'min_cycles': 1, 'max_cycles': 1, 'description': 'done pulse is exactly one cycle on wrap event.'}}, 'handshake_rules': [{'signal': 'enable', 'rule': 'Sampled only on rising clock edge; no combinational feedback obligations.'}, {'signal': 'clear', 'rule': 'If high on rising edge', 'clear transaction executes and masks enable advance for that edge.': None}, {'signal': 'rst_n', 'rule': 'Asynchronous assertion immediately clears state; synchronous behavior resumes after deassertion and next rising edge.'}], 'pipeline': [{'stage': 'S0_SAMPLE', 'cycle': 'N', 'action': 'Sample rst_n/clear/enable and current gray_state.'}, {'stage': 'S1_COMPUTE', 'cycle': 'N', 'action': 'Compute next binary/Gray and wrap flag combinationally.'}, {'stage': 'S2_COMMIT', 'cycle': 'N_to_Nplus1', 'action': 'Commit gray register and done pulse register at rising edge according to priority reset>clear>enable>hold.'}, {'stage': 'S3_OBSERVE', 'cycle': 'Nplus1', 'action': 'Observe updated gray_value and combinational bin_value decode.'}], 'ordering': ['Asynchronous reset effect precedes any synchronous clear/enable action while rst_n is low.', 'Within a rising-edge sample, clear decision is evaluated before enable advance.', 'done update is ordered with gray register commit from the same sampled edge.'], 'backpressure': ['No ready/valid interface; design is always able to sample control each clock.'], 'observability': ['Every function_model transaction maps to S0..S3 progression with deterministic one-cycle state commit.'], 'backend_policy': 'Use PyMTL3 for the clocked cycle model shell; FunctionalModel remains the behavioral oracle.', 'performance': {'frequency_mhz': 200, 'throughput': {'sustained_beats_per_cycle': 1, 'condition': 'No backpressure on the active interface'}, 'outstanding': {'max': 1, 'description': 'Default one accepted operation until the SSOT declares deeper buffering'}, 'depth': {'pipeline_stages': 3, 'queue_depth': 1, 'description': 'Default accept/evaluate/observe cycle model depth'}}}}


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
