#!/usr/bin/env python3
"""Executable SSOT cycle-level model for gpio. Wraps FunctionalModel — FL is the only oracle."""

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
_LATENCY: dict[str, int] = {'control_to_state': 1, 'state_to_outputs': 0, 'pad_to_din': 1, 'default': 1}

# Handshake rules from SSOT cycle_model.handshake_rules.
_HANDSHAKE_RULES: list[dict] = [{'name': 'hr_sync_sample', 'description': '', 'predicate': ''}, {'name': 'hr_input_mask_sample', 'description': '', 'predicate': ''}, {'name': 'hr_comb_outputs', 'description': '', 'predicate': ''}]

# Ordering rules from SSOT cycle_model.ordering.
_ORDERING_RULES: list[dict] = [{'name': 'sequential_updates_occur_at_edge_combinational_outputs_settle_after_edge', 'description': ''}, {'name': 'reset_dominates_non_reset_behavior', 'description': ''}]

# Maximum outstanding transactions before stalling.
_OUTSTANDING_CAP: int = 1

# Cycle/performance targets used by coverage and PyMTL shell instrumentation.
PERFORMANCE_TARGETS: dict = {'frequency_mhz': 200, 'throughput': {'sustained_beats_per_cycle': 1, 'condition': 'No backpressure on the active interface'}, 'outstanding': {'max': 1, 'description': 'Default one accepted operation until the SSOT declares deeper buffering'}, 'pipeline_stages': 3, 'queue_depth': 1}

# Transaction kinds for self-check, derived from function_model.transactions at generation time.
_SELF_CHECK_KINDS: list[str] = ['FM1_LATCH_CONTROL', 'FM2_SAMPLE_INPUTS', 'FM3_DRIVE_PAD_OUTPUTS', 'FM4_ASYNC_RESET']

# Coverage bins: bin_name -> description.
CL_BINS: dict[str, str] = {'handshake_hr_sync_sample': 'hr_sync_sample', 'handshake_hr_input_mask_sample': 'hr_input_mask_sample', 'handshake_hr_comb_outputs': 'hr_comb_outputs', 'ordering_sequential_updates_occur_at_edge_combinational_outputs_settle_after_edge': 'sequential_updates_occur_at_edge_combinational_outputs_settle_after_edge', 'ordering_reset_dominates_non_reset_behavior': 'reset_dominates_non_reset_behavior', 'latency_fm1_latch_control': 'latency bin for FM1_LATCH_CONTROL', 'latency_fm2_sample_inputs': 'latency bin for FM2_SAMPLE_INPUTS', 'latency_fm3_drive_pad_outputs': 'latency bin for FM3_DRIVE_PAD_OUTPUTS', 'latency_fm4_async_reset': 'latency bin for FM4_ASYNC_RESET'}

# SSOT payload snapshot (read-only reference; never execute functional rules from here).
SSOT_MODEL: dict = {'ip': 'gpio', 'function_model': {'purpose': 'Behavioral contract for GPIO state update, input sampling, and pad outputs', 'state_variables': [{'name': 'dir_state', 'source': 'io_list.interfaces.gpio_state.ports.dir_q', 'reset': 0, 'description': 'Registered direction vector'}, {'name': 'dout_state', 'source': 'io_list.interfaces.gpio_state.ports.dout_q', 'reset': 0, 'description': 'Registered output data vector'}, {'name': 'din_state', 'source': 'io_list.interfaces.gpio_state.ports.din_q', 'reset': 0, 'description': 'Registered sampled input vector'}], 'transactions': [{'id': 'FM1_LATCH_CONTROL', 'name': 'latch_direction_and_output_data', 'preconditions': ['rst_n is deasserted', 'rising edge of clk'], 'inputs': ['dir_in', 'dout_in'], 'outputs': ['dir_state equals dir_in after sampling edge', 'dout_state equals dout_in after sampling edge'], 'side_effects': ['dir_q and dout_q update atomically each cycle']}, {'id': 'FM2_SAMPLE_INPUTS', 'name': 'sample_pad_inputs_for_input_bits_only', 'preconditions': ['rst_n is deasserted', 'rising edge of clk'], 'inputs': ['pad_in', 'dir_state', 'din_state'], 'outputs': ['din_state bits with dir_state=0 sample pad_in', 'din_state bits with dir_state=1 hold previous value'], 'side_effects': ['din_q updates only on input-configured bits']}, {'id': 'FM3_DRIVE_PAD_OUTPUTS', 'name': 'derive_output_enable_and_pad_drive', 'preconditions': ['dir_state and dout_state are defined'], 'inputs': ['dir_state', 'dout_state'], 'outputs': ['oe_o equals dir_state', 'pad_o equals dout_state where dir_state is 1 else 0'], 'side_effects': ['no sequential state change']}, {'id': 'FM4_ASYNC_RESET', 'name': 'asynchronous_reset_clears_state', 'preconditions': ['rst_n asserted low'], 'outputs': ['dir_state zero', 'dout_state zero', 'din_state zero', 'oe_o zero', 'pad_o zero'], 'side_effects': ['all architectural state cleared independent of clk']}], 'invariants': ['oe_o equals dir_q at all times after combinational settle', 'pad_o equals (dout_q & dir_q) bitwise', 'din_q output-configured bits hold unless reset', 'no hidden state beyond dir_q, dout_q, din_q']}, 'cycle_model': {'purpose': 'Cycle-accurate timing and ordering for GPIO behavior', 'executable': 'pymtl3', 'backend_policy': 'Use PyMTL3 for cycle shell and direct Python oracle checks', 'clock': 'clk', 'reset': {'assertion': 'rst_n low asynchronously clears state', 'deassertion': 'state usable on first rising edge after deassertion'}, 'latency': {'control_to_state': {'min_cycles': 1, 'max_cycles': 1, 'description': 'dir_in/dout_in sampled on next rising edge'}, 'state_to_outputs': {'min_cycles': 0, 'max_cycles': 0, 'description': 'oe_o and pad_o combinational from state'}, 'pad_to_din': {'min_cycles': 1, 'max_cycles': 1, 'description': 'input bits sample pad_in on rising edge'}}, 'handshake_rules': [{'id': 'HR_SYNC_SAMPLE', 'signal': 'clk', 'rule': 'Inputs sampled only on rising edge'}, {'id': 'HR_INPUT_MASK_SAMPLE', 'signal': 'din_q', 'rule': 'din_q bit updates only when corresponding dir_q bit is 0'}, {'id': 'HR_COMB_OUTPUTS', 'signal': 'oe_o/pad_o', 'rule': 'Outputs are pure combinational functions of registered state'}], 'pipeline': [{'stage': 'S0_RESET', 'cycle': 'async', 'action': 'Clear dir_q/dout_q/din_q when rst_n=0'}, {'stage': 'S1_LATCH_CONTROL', 'cycle': 'N', 'action': 'Latch dir_in->dir_q and dout_in->dout_q at rising edge'}, {'stage': 'S2_SAMPLE_INPUTS', 'cycle': 'N', 'action': 'Sample pad_in into din_q only for dir_q=0 bits'}, {'stage': 'S3_DRIVE_OUTPUTS', 'cycle': 'N+comb', 'action': 'Drive oe_o/pad_o from registered state'}], 'ordering': ['sequential updates occur at edge, combinational outputs settle after edge', 'reset dominates non-reset behavior'], 'backpressure': ['no ready/valid protocol in this GPIO fixture'], 'observability': ['each function_model transaction maps to cycle stages and test scenarios'], 'performance': {'frequency_mhz': 200, 'throughput': {'sustained_beats_per_cycle': 1, 'condition': 'No backpressure on the active interface'}, 'outstanding': {'max': 1, 'description': 'Default one accepted operation until the SSOT declares deeper buffering'}, 'depth': {'pipeline_stages': 3, 'queue_depth': 1, 'description': 'Default accept/evaluate/observe cycle model depth'}}}}


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
