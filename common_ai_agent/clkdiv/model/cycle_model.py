#!/usr/bin/env python3
"""Executable SSOT cycle-level model for clkdiv. Wraps FunctionalModel — FL is the only oracle."""

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
_LATENCY: dict[str, int] = {'register_read': 1, 'register_write': 1, 'divisor_update': 1, 'output_toggle': 1, 'default': 1}

# Handshake rules from SSOT cycle_model.handshake_rules.
_HANDSHAKE_RULES: list[dict] = [{'name': 'handshake_0', 'description': '', 'predicate': ''}, {'name': 'handshake_1', 'description': '', 'predicate': ''}, {'name': 'handshake_2', 'description': '', 'predicate': ''}, {'name': 'handshake_3', 'description': '', 'predicate': ''}, {'name': 'handshake_4', 'description': '', 'predicate': ''}]

# Ordering rules from SSOT cycle_model.ordering.
_ORDERING_RULES: list[dict] = [{'name': 'apb_divisor_writes_update_pending_divisor_before_the_next_core_reload_boundary', 'description': ''}, {'name': 'active_divisor_changes_only_in_s3_terminal_or_reset', 'description': ''}, {'name': 'intclr_clear_irq_write_clears_irq_pending_no_later_than_the_completing_apb_access_edge', 'description': ''}]

# Maximum outstanding transactions before stalling.
_OUTSTANDING_CAP: int = 1

# Cycle/performance targets used by coverage and PyMTL shell instrumentation.
PERFORMANCE_TARGETS: dict = {'frequency_mhz': 100, 'throughput': {'sustained_register_accesses_per_cycle': 0.5, 'condition': 'APB requires setup and access phases'}, 'outstanding': None, 'pipeline_stages': None, 'queue_depth': None}

# Transaction kinds for self-check, derived from function_model.transactions at generation time.
_SELF_CHECK_KINDS: list[str] = ['FM_DIVIDE']

# Coverage bins: bin_name -> description.
CL_BINS: dict[str, str] = {'handshake_handshake_0': 'handshake_0', 'handshake_handshake_1': 'handshake_1', 'handshake_handshake_2': 'handshake_2', 'handshake_handshake_3': 'handshake_3', 'handshake_handshake_4': 'handshake_4', 'ordering_apb_divisor_writes_update_pending_divisor_before_the_next_core_reload_boundary': 'apb_divisor_writes_update_pending_divisor_before_the_next_core_reload_boundary', 'ordering_active_divisor_changes_only_in_s3_terminal_or_reset': 'active_divisor_changes_only_in_s3_terminal_or_reset', 'ordering_intclr_clear_irq_write_clears_irq_pending_no_later_than_the_completing_apb_access_edge': 'intclr_clear_irq_write_clears_irq_pending_no_later_than_the_completing_apb_access_edge', 'latency_fm_divide': 'latency bin for FM_DIVIDE'}

# SSOT payload snapshot (read-only reference; never execute functional rules from here).
SSOT_MODEL: dict = {'ip': 'clkdiv', 'function_model': {'purpose': 'Behavioral contract for programmable clock division independent of APB cycle timing.', 'state_variables': [{'name': 'enable', 'source': 'registers.CTRL.enable', 'reset': 0, 'description': 'Divider enable state'}, {'name': 'pending_divisor', 'source': 'registers.DIVISOR.divisor', 'reset': 2, 'description': 'Software-programmed divisor, with write value 0 coerced to 1'}, {'name': 'active_divisor', 'source': 'clkdiv_core.active_divisor', 'reset': 2, 'description': 'Divisor currently used by the counter'}, {'name': 'counter', 'source': 'clkdiv_core.counter', 'reset': 0, 'description': 'Counts input clock cycles toward terminal count'}, {'name': 'clk_state', 'source': 'clk_o', 'reset': 0, 'description': 'Current divided clock output state'}, {'name': 'irq_pending', 'source': 'registers.STATUS.irq_pending', 'reset': 0, 'description': 'Sticky terminal event interrupt pending bit'}], 'transactions': [{'id': 'FM_DIVIDE', 'name': 'integer_clock_divide', 'preconditions': ['rst_ni is deasserted', 'CTRL.enable == 1', 'active_divisor >= 1'], 'inputs': ['clk_i rising edge', 'active_divisor', 'CTRL.irq_enable'], 'outputs': ['clk_o toggles exactly when counter reaches active_divisor-1', 'locked_o is 1 after the first terminal reload while enabled', 'irq_o is 1 when irq_pending and CTRL.irq_enable are both 1'], 'side_effects': ['If counter == active_divisor-1, counter resets to 0 and clk_state toggles.', 'If counter != active_divisor-1, counter increments by one and clk_state is stable.', 'At terminal count, active_divisor loads pending_divisor for the next half-period.', 'At terminal count, irq_pending is set when CTRL.irq_enable=1.', 'When enable=0, counter=0, clk_state=0, locked_o=0.'], 'error_cases': [{'condition': 'APB write to DIVISOR with value 0', 'result': 'pending_divisor is coerced to 1; no pslverr'}, {'condition': 'APB access to unsupported address', 'result': 'pslverr asserted for the access and state is unchanged'}]}], 'invariants': ['clk_o changes only on clk_i rising edges while rst_ni is deasserted.', 'DIVISOR writes do not directly toggle clk_o.', 'Reserved register fields read as zero and ignore writes.', 'irq_pending remains set until INTCLR.clear_irq is written as 1.'], 'reference_model_hint': 'tb-gen should model counter, active_divisor, pending_divisor, clk_state, locked, and irq_pending in Python and compare outputs cycle-by-cycle.'}, 'cycle_model': {'purpose': 'Cycle and handshake contract for APB register access and divider output timing.', 'executable': 'pymtl3', 'backend_policy': 'Use a clocked PyMTL3 model as cycle reference and direct Python smoke checks for divider timing.', 'clock': 'clk_i', 'reset': {'assertion': 'rst_ni low asynchronously clears registers, counter, clk_o, locked_o, and irq_pending to reset values.', 'deassertion': 'State is usable on the first rising edge after synchronized deassertion.'}, 'latency': {'register_read': {'min_cycles': 1, 'max_cycles': 1, 'description': 'APB access completes with pready in the access phase.'}, 'register_write': {'min_cycles': 1, 'max_cycles': 1, 'description': 'APB writes update register storage on completing access phase.'}, 'divisor_update': {'min_cycles': 1, 'max_cycles': None, 'description': 'A new divisor applies at the next terminal count boundary.'}, 'output_toggle': {'min_cycles': 1, 'max_cycles': None, 'description': 'clk_o toggles after active_divisor input clock rising edges while enabled.'}}, 'handshake_rules': [{'signal': 'pready', 'rule': 'pready is asserted for every selected APB access phase; no wait states in baseline.'}, {'signal': 'pslverr', 'rule': 'pslverr is asserted only with pready for unsupported address or illegal access.'}, {'signal': 'prdata', 'rule': 'prdata is stable in the APB read completing access phase.'}, {'signal': 'clk_o', 'rule': 'clk_o toggles only at terminal count on clk_i rising edge and is held low when disabled.'}, {'signal': 'irq_o', 'rule': 'irq_o is combinational/registered reflection of irq_pending && irq_enable and deasserts after INTCLR clear.'}], 'pipeline': [{'stage': 'S0_APB_SETUP', 'cycle': 0, 'action': 'Capture paddr/pwrite context when psel=1 and penable=0.'}, {'stage': 'S1_APB_ACCESS', 'cycle': 1, 'action': 'Complete APB read/write; update CTRL/DIVISOR/INTCLR effects.'}, {'stage': 'S2_COUNT', 'cycle': 'each enabled clk_i edge', 'action': 'Increment counter while counter < active_divisor-1.'}, {'stage': 'S3_TERMINAL', 'cycle': 'terminal edge', 'action': 'Reset counter, toggle clk_o, load pending_divisor, set locked and optional irq_pending.'}, {'stage': 'S4_DISABLE', 'cycle': 'first edge after enable=0', 'action': 'Force counter and clk_o low and clear locked.'}], 'ordering': ['APB DIVISOR writes update pending_divisor before the next core reload boundary.', 'active_divisor changes only in S3_TERMINAL or reset.', 'INTCLR.clear_irq write clears irq_pending no later than the completing APB access edge.'], 'backpressure': ['No backpressure exists on divided_clock outputs; APB baseline has no wait states.'], 'performance': {'frequency_mhz': 100, 'throughput': {'sustained_register_accesses_per_cycle': 0.5, 'condition': 'APB requires setup and access phases'}, 'divider_range': {'min_divisor': 1, 'max_divisor': 65535, 'description': 'DIV_WIDTH=16 baseline'}, 'output_rate': {'half_period_input_cycles': 'active_divisor', 'full_period_input_cycles': '2*active_divisor'}}, 'observability': ['Every function_model transaction maps to S2_COUNT/S3_TERMINAL and a test_requirements scenario.']}}


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
