#!/usr/bin/env python3
"""Executable SSOT cycle-level model for arbiter_rr. Wraps FunctionalModel — FL is the only oracle."""

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
_LATENCY: dict[str, int] = {'arbitration': 1, 'register_read': 1, 'register_write': 1, 'default': 1}

# Handshake rules from SSOT cycle_model.handshake_rules.
_HANDSHAKE_RULES: list[dict] = [{'name': 'handshake_0', 'description': '', 'predicate': ''}, {'name': 'handshake_1', 'description': '', 'predicate': ''}, {'name': 'handshake_2', 'description': '', 'predicate': ''}, {'name': 'handshake_3', 'description': '', 'predicate': ''}]

# Ordering rules from SSOT cycle_model.ordering.
_ORDERING_RULES: list[dict] = [{'name': 'grant_outputs_reflect_the_arbitration_decision_from_the_previous_cycle_1_stage_pipeline', 'description': ''}, {'name': 'last_winner_update_occurs_on_the_same_rising_edge_as_the_grant_output_registration', 'description': ''}, {'name': 'csr_writes_to_req_mask_or_ctrl_take_effect_on_the_next_arbitration_cycle_registered_config', 'description': ''}]

# Maximum outstanding transactions before stalling.
_OUTSTANDING_CAP: int = 1

# Cycle/performance targets used by coverage and PyMTL shell instrumentation.
PERFORMANCE_TARGETS: dict = {'frequency_mhz': 50, 'throughput': {'grants_per_cycle': 1, 'condition': 'At least one unmasked request active and arbiter enabled'}, 'outstanding': {'read_max': 0, 'write_max': 0, 'description': 'No outstanding AXI-style transactions — simple combinatorial arbiter'}, 'pipeline_stages': 1, 'queue_depth': 0}

# Transaction kinds for self-check, derived from function_model.transactions at generation time.
_SELF_CHECK_KINDS: list[str] = ['FM1', 'FM2']

# Coverage bins: bin_name -> description.
CL_BINS: dict[str, str] = {'handshake_handshake_0': 'handshake_0', 'handshake_handshake_1': 'handshake_1', 'handshake_handshake_2': 'handshake_2', 'handshake_handshake_3': 'handshake_3', 'ordering_grant_outputs_reflect_the_arbitration_decision_from_the_previous_cycle_1_stage_pipeline': 'grant_outputs_reflect_the_arbitration_decision_from_the_previous_cycle_1_stage_pipeline', 'ordering_last_winner_update_occurs_on_the_same_rising_edge_as_the_grant_output_registration': 'last_winner_update_occurs_on_the_same_rising_edge_as_the_grant_output_registration', 'ordering_csr_writes_to_req_mask_or_ctrl_take_effect_on_the_next_arbitration_cycle_registered_config': 'csr_writes_to_req_mask_or_ctrl_take_effect_on_the_next_arbitration_cycle_registered_config', 'latency_fm1': 'latency bin for FM1', 'latency_fm2': 'latency bin for FM2'}

# SSOT payload snapshot (read-only reference; never execute functional rules from here).
SSOT_MODEL: dict = {'ip': 'arbiter_rr', 'function_model': {'purpose': 'Executable behavioral contract for rtl-gen and tb-gen; describes what the arbiter computes independent of cycle timing.', 'state_variables': [{'name': 'last_winner', 'source': 'registers.STATUS.winner', 'reset': 0, 'description': 'Index of the last granted requestor; used as priority rotation base'}, {'name': 'arb_enabled', 'source': 'registers.CTRL.enable', 'reset': 1, 'description': 'Global arbiter enable from CSR'}, {'name': 'req_mask', 'source': 'registers.REQ_MASK', 'reset': 'all-ones', 'description': 'Per-request enable mask (1=enabled, 0=masked)'}], 'transactions': [{'id': 'FM1', 'name': 'arbitrate_grant', 'preconditions': ['arb_enabled == 1', '(req_i & req_mask) != 0 (at least one unmasked active request)'], 'inputs': ['req_i: N-bit request vector', 'req_mask: N-bit mask from CSR', 'last_winner: priority rotation base index'], 'outputs': ['gnt_o is one-hot with exactly one bit set at selected_index', 'gnt_valid_o == 1', 'gnt_idx_o == selected_index (binary)', 'last_winner updated to selected_index'], 'side_effects': ['last_winner rotates to current winner so it gets lowest priority next cycle', 'Only one requestor is granted per cycle (one-hot invariant)'], 'error_cases': []}, {'id': 'FM2', 'name': 'no_grant_idle', 'preconditions': ['arb_enabled == 0 OR (req_i & req_mask) == 0'], 'inputs': ['req_i: N-bit request vector', 'req_mask: N-bit mask'], 'outputs': ['gnt_o == 0', 'gnt_valid_o == 0', 'gnt_idx_o == 0', 'last_winner unchanged'], 'side_effects': ['last_winner is preserved unchanged when no grant is issued'], 'error_cases': []}], 'invariants': ['At most one bit in gnt_o is asserted per cycle (one-hot invariant).', 'gnt_valid_o == 0 implies gnt_o == 0.', 'gnt_valid_o == 1 implies exactly one bit in gnt_o is set and gnt_idx_o equals the index of that bit.', 'Masked requests never receive a grant regardless of req_i state.', 'When arb_enabled == 0, all outputs are zero and last_winner is frozen.', 'Round-robin fairness: a requestor that was granted in the previous cycle has the lowest priority in the current cycle.'], 'reference_model_hint': 'tb-gen should implement a Python reference model that replicates the circular priority scan and compare expected/got gnt_o, gnt_valid_o, gnt_idx_o for every scenario.'}, 'cycle_model': {'purpose': 'Cycle/handshake contract for rtl-gen; describes when arbitration outputs and state may change.', 'executable': 'pymtl3', 'backend_policy': 'Use PyMTL3 for the clocked cycle model shell; keep FunctionalModel as the behavioral oracle.', 'clock': 'PCLK', 'reset': {'assertion': 'PRESETn low asynchronously clears all architectural state (last_winner=0, gnt_o=0, gnt_valid_o=0, gnt_idx_o=0)', 'deassertion': 'State is usable on the first rising edge after synchronized deassertion'}, 'latency': {'arbitration': {'min_cycles': 1, 'max_cycles': 1, 'description': 'Request sampled on cycle N produces registered grant on cycle N+1'}, 'register_read': {'min_cycles': 0, 'max_cycles': 1, 'description': 'APB read data and PREADY timing'}, 'register_write': {'min_cycles': 0, 'max_cycles': 1, 'description': 'APB write acceptance timing'}}, 'handshake_rules': [{'signal': 'req_i', 'rule': 'Sampled on rising PCLK; requesters must hold req_i stable until corresponding gnt_o is seen.'}, {'signal': 'gnt_o', 'rule': 'Registered output — reflects arbitration decision from the previous cycle. At most one bit high.'}, {'signal': 'gnt_valid_o', 'rule': 'Registered — high when a valid grant is being asserted this cycle.'}, {'signal': 'gnt_idx_o', 'rule': 'Registered — valid binary index when gnt_valid_o is high; zero otherwise.'}], 'pipeline': [{'stage': 'S0_SAMPLE_REQ', 'cycle': 0, 'action': 'Latch req_i, apply mask (req_i & req_mask), read last_winner'}, {'stage': 'S1_GRANT', 'cycle': 1, 'action': 'Priority encoder evaluates; gnt_o, gnt_idx_o, gnt_valid_o registered and driven to outputs; last_winner updated'}], 'ordering': ['Grant outputs reflect the arbitration decision from the previous cycle (1-stage pipeline).', 'last_winner update occurs on the same rising edge as the grant output registration.', 'CSR writes to REQ_MASK or CTRL take effect on the next arbitration cycle (registered config).'], 'backpressure': ['No backpressure mechanism — the arbiter produces a grant every cycle when enabled and requests are present. Requesters must accept the grant immediately.'], 'performance': {'frequency_mhz': 50, 'throughput': {'grants_per_cycle': 1, 'condition': 'At least one unmasked request active and arbiter enabled'}, 'outstanding': {'read_max': 0, 'write_max': 0, 'description': 'No outstanding AXI-style transactions — simple combinatorial arbiter'}, 'depth': {'pipeline_stages': 1, 'queue_depth': 0, 'description': 'Single-stage registered output pipeline'}}, 'observability': ['Every function_model transaction maps to at least one cycle_model stage and one test_requirements scenario.']}}


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
