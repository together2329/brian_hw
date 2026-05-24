#!/usr/bin/env python3
"""Executable SSOT cycle-level model for real_llm_counter_demo. Wraps FunctionalModel — FL is the only oracle."""

from __future__ import annotations

import json

try:
    from . import functional_model as _functional_model_mod
except ImportError:
    import functional_model as _functional_model_mod

FunctionalModel = _functional_model_mod.FunctionalModel
Transaction = getattr(_functional_model_mod, "Transaction", None)


# ---------------------------------------------------------------------------
# SSOT-derived tables (baked at generation time)
# ---------------------------------------------------------------------------

# Executable backend. The CL model is a pure-Python deterministic stepper;
# FunctionalModel remains the oracle.
MODEL_BACKEND: str = 'python'

# Latency table: transaction kind -> cycles.  max_cycles when defined; min_cycles otherwise; default=1.
_LATENCY: dict[str, int] = {'command_accept': 0, 'command_effect': 1, 'flag_update': 0, 'default': 1}

# Handshake rules from SSOT cycle_model.handshake_rules.
_HANDSHAKE_RULES: list[dict] = [{'name': 'cmd_valid_cmd_ready', 'signal': 'cmd_valid/cmd_ready', 'description': 'cmd_valid asserts the command; cmd_ready is always 1 so the command is always accepted on the same rising edge. cmd and load_value must be stable when cmd_valid is high.', 'predicate': 'cmd_valid asserts the command; cmd_ready is always 1 so the command is always accepted on the same rising edge. cmd and load_value must be stable when cmd_valid is high.'}]

# Ordering rules from SSOT cycle_model.ordering.
_ORDERING_RULES: list[dict] = [{'name': 'accepted_commands_update_architectural_state_count_last_cmd_accepted_count_only_on_clock_edges', 'description': ''}, {'name': 'zero_and_max_are_combinational_functions_of_count_and_reflect_updates_in_the_same_cycle', 'description': ''}, {'name': 'no_backpressure_cmd_ready_is_always_1', 'description': ''}]

# Maximum outstanding transactions before stalling.
_OUTSTANDING_CAP: int = 1

# Cycle/performance targets used by coverage and timing instrumentation.
PERFORMANCE_TARGETS: dict = {'frequency_mhz': 100, 'throughput': {'sustained_beats_per_cycle': 1, 'condition': 'One command per clock cycle when cmd_valid is high.'}, 'outstanding': {'max': 1, 'description': 'Single-cycle acceptance, single-cycle effect.'}, 'pipeline_stages': 2, 'queue_depth': 0}

# Transaction kinds for self-check, derived from function_model.transactions at generation time.
_SELF_CHECK_KINDS: list[str] = ['FM_CLEAR', 'FM_LOAD', 'FM_INC', 'FM_DEC', 'FM_HOLD', 'FM_INVALID']

# Coverage bins: bin_name -> description.
CL_BINS: dict[str, str] = {'handshake_cmd_valid_cmd_ready': 'cmd_valid asserts the command; cmd_ready is always 1 so the command is always accepted on the same rising edge. cmd and load_value must be stable when cmd_valid is high.', 'ordering_accepted_commands_update_architectural_state_count_last_cmd_accepted_count_only_on_clock_edges': 'accepted_commands_update_architectural_state_count_last_cmd_accepted_count_only_on_clock_edges', 'ordering_zero_and_max_are_combinational_functions_of_count_and_reflect_updates_in_the_same_cycle': 'zero_and_max_are_combinational_functions_of_count_and_reflect_updates_in_the_same_cycle', 'ordering_no_backpressure_cmd_ready_is_always_1': 'no_backpressure_cmd_ready_is_always_1', 'latency_fm_clear': 'latency bin for FM_CLEAR', 'latency_fm_load': 'latency bin for FM_LOAD', 'latency_fm_inc': 'latency bin for FM_INC', 'latency_fm_dec': 'latency bin for FM_DEC', 'latency_fm_hold': 'latency bin for FM_HOLD', 'latency_fm_invalid': 'latency bin for FM_INVALID'}

# SSOT payload snapshot (read-only reference; never execute functional rules from here).
SSOT_MODEL: dict = {'ip': 'real_llm_counter_demo', 'function_model': {'purpose': 'Cycle-independent behavioral contract for rtl-gen and tb-gen. Describes what the 8-bit saturating counter computes for each command.', 'state_variables': [{'name': 'count', 'width': 8, 'reset': 0, 'description': 'Current 8-bit counter value.'}, {'name': 'accepted_count', 'width': 32, 'reset': 0, 'description': 'Total accepted commands (wraps at 2^32-1).'}, {'name': 'last_cmd', 'width': 3, 'reset': 0, 'description': 'Last accepted command encoding (mirrored to status output).'}], 'transactions': [{'id': 'FM_CLEAR', 'name': 'clear_counter', 'preconditions': ['cmd_valid == 1', 'cmd == 0'], 'inputs': ['cmd_valid: 1', 'cmd: 0 (CLEAR)'], 'outputs': ['count == 0 on next cycle', 'zero == 1, max == 0', {'name': 'zero', 'port': 'zero', 'expr': '1', 'description': 'count is 0 after clear'}, {'name': 'max', 'port': 'max', 'expr': '0', 'description': 'count is not 255 after clear'}, {'name': 'count', 'port': 'count', 'expr': 'count', 'description': 'Externally observable function_model state is driven from the RTL state register.'}, {'name': 'accepted_count', 'port': 'accepted_count', 'expr': 'accepted_count', 'description': 'Externally observable function_model state is driven from the RTL state register.'}, {'state': 'last_cmd', 'expr': '0', 'description': 'Record CLEAR as last command'}], 'error_cases': [], 'side_effects': ['updates only SSOT-declared architectural state, status, events, or output handoff state']}, {'id': 'FM_LOAD', 'name': 'load_counter', 'preconditions': ['cmd_valid == 1', 'cmd == 1'], 'inputs': ['cmd_valid: 1', 'cmd: 1 (LOAD)', 'load_value: 8-bit value'], 'outputs': ['count == load_value on next cycle', 'zero == (load_value == 0)', 'max == (load_value == 255)', {'name': 'zero', 'port': 'zero', 'expr': '1 if load_value == 0 else 0', 'description': 'zero flag reflects loaded value'}, {'name': 'max', 'port': 'max', 'expr': '1 if load_value == 255 else 0', 'description': 'max flag reflects loaded value'}, {'name': 'count', 'port': 'count', 'expr': 'count', 'description': 'Externally observable function_model state is driven from the RTL state register.'}, {'name': 'accepted_count', 'port': 'accepted_count', 'expr': 'accepted_count', 'description': 'Externally observable function_model state is driven from the RTL state register.'}, {'state': 'last_cmd', 'expr': '1', 'description': 'Record LOAD as last command'}], 'error_cases': [], 'side_effects': ['updates only SSOT-declared architectural state, status, events, or output handoff state']}, {'id': 'FM_INC', 'name': 'increment_counter', 'preconditions': ['cmd_valid == 1', 'cmd == 2'], 'inputs': ['cmd_valid: 1', 'cmd: 2 (INC)'], 'outputs': ['count == min(count + 1, 255) on next cycle', 'zero == (min(count + 1, 255) == 0)', 'max == (min(count + 1, 255) == 255)', {'name': 'zero', 'port': 'zero', 'expr': '1 if min(count + 1, 255) == 0 else 0', 'description': 'zero flag after increment'}, {'name': 'max', 'port': 'max', 'expr': '1 if min(count + 1, 255) == 255 else 0', 'description': 'max flag after increment (set when saturating)'}, {'name': 'count', 'port': 'count', 'expr': 'count', 'description': 'Externally observable function_model state is driven from the RTL state register.'}, {'name': 'accepted_count', 'port': 'accepted_count', 'expr': 'accepted_count', 'description': 'Externally observable function_model state is driven from the RTL state register.'}, {'state': 'last_cmd', 'expr': '2', 'description': 'Record INC as last command'}], 'error_cases': [], 'side_effects': ['updates only SSOT-declared architectural state, status, events, or output handoff state']}, {'id': 'FM_DEC', 'name': 'decrement_counter', 'preconditions': ['cmd_valid == 1', 'cmd == 3'], 'inputs': ['cmd_valid: 1', 'cmd: 3 (DEC)'], 'outputs': ['count == max(count - 1, 0) on next cycle', 'zero == (max(count - 1, 0) == 0)', 'max == (max(count - 1, 0) == 255)', {'name': 'zero', 'port': 'zero', 'expr': '1 if max(count - 1, 0) == 0 else 0', 'description': 'zero flag after decrement'}, {'name': 'max', 'port': 'max', 'expr': '1 if max(count - 1, 0) == 255 else 0', 'description': 'max flag after decrement'}, {'name': 'count', 'port': 'count', 'expr': 'count', 'description': 'Externally observable function_model state is driven from the RTL state register.'}, {'name': 'accepted_count', 'port': 'accepted_count', 'expr': 'accepted_count', 'description': 'Externally observable function_model state is driven from the RTL state register.'}, {'state': 'last_cmd', 'expr': '3', 'description': 'Record DEC as last command'}], 'error_cases': [], 'side_effects': ['updates only SSOT-declared architectural state, status, events, or output handoff state']}, {'id': 'FM_HOLD', 'name': 'hold_counter', 'preconditions': ['cmd_valid == 1', 'cmd == 4'], 'inputs': ['cmd_valid: 1', 'cmd: 4 (HOLD)'], 'outputs': ['count unchanged', 'zero == (count == 0)', 'max == (count == 255)', {'name': 'zero', 'port': 'zero', 'expr': '1 if count == 0 else 0', 'description': 'zero flag unchanged'}, {'name': 'max', 'port': 'max', 'expr': '1 if count == 255 else 0', 'description': 'max flag unchanged'}, {'name': 'accepted_count', 'port': 'accepted_count', 'expr': 'accepted_count', 'description': 'Externally observable function_model state is driven from the RTL state register.'}, {'state': 'last_cmd', 'expr': '4', 'description': 'Record HOLD as last command'}], 'error_cases': [], 'side_effects': ['updates only SSOT-declared architectural state, status, events, or output handoff state']}, {'id': 'FM_INVALID', 'name': 'invalid_command_as_hold', 'preconditions': ['cmd_valid == 1', 'cmd >= 5'], 'inputs': ['cmd_valid: 1', 'cmd: 5, 6, or 7 (reserved)'], 'outputs': ['count unchanged (same as HOLD)', 'zero == (count == 0)', 'max == (count == 255)', {'name': 'zero', 'port': 'zero', 'expr': '1 if count == 0 else 0', 'description': 'zero flag unchanged'}, {'name': 'max', 'port': 'max', 'expr': '1 if count == 255 else 0', 'description': 'max flag unchanged'}, {'name': 'accepted_count', 'port': 'accepted_count', 'expr': 'accepted_count', 'description': 'Externally observable function_model state is driven from the RTL state register.'}, {'state': 'last_cmd', 'expr': 'cmd', 'description': 'Record actual cmd value (5-7) in status'}], 'error_cases': [], 'side_effects': ['updates only SSOT-declared architectural state, status, events, or output handoff state']}], 'invariants': ['count is always in [0, 255].', 'zero == 1 if and only if count == 0.', 'max == 1 if and only if count == 255.', 'cmd_ready is always 1.', 'accepted_count increments on every cmd_valid && cmd_ready edge.', 'status == last_cmd after each accepted command.', 'No bus, no CSR, no memory, no interrupt, no CDC, no multi-clock behavior.'], 'reference_model_hint': 'tb-gen must build a scoreboard/reference model from function_model transactions and compare expected count/zero/max/accepted_count/status versus RTL observed after each accepted command.'}, 'cycle_model': {'purpose': 'Cycle/handshake contract — single-cycle command acceptance with combinational decode and registered update.', 'executable': 'python', 'backend_policy': 'Use the repo-owned pure-Python deterministic stepper; FunctionalModel remains the behavioral oracle.', 'clock': 'clk', 'reset': {'signal': 'rst_n', 'polarity': 'active_low', 'assertion': 'rst_n == 0 asynchronously clears count to 0, accepted_count to 0, last_cmd to 0', 'deassertion': 'Logic may accept commands on the first rising edge after synchronized deassertion'}, 'latency': {'command_accept': {'min_cycles': 0, 'max_cycles': 0, 'description': 'cmd_ready is always 1 — command is accepted on the same edge cmd_valid is asserted.'}, 'command_effect': {'min_cycles': 1, 'max_cycles': 1, 'description': 'Count/status/accepted_count update on the clock edge after acceptance.'}, 'flag_update': {'min_cycles': 0, 'max_cycles': 0, 'description': 'zero and max are combinational — they reflect the new count value in the same cycle.'}}, 'handshake_rules': [{'signal': 'cmd_valid/cmd_ready', 'rule': 'cmd_valid asserts the command; cmd_ready is always 1 so the command is always accepted on the same rising edge. cmd and load_value must be stable when cmd_valid is high.'}], 'pipeline': [{'stage': 'S0_ACCEPT', 'cycle': 0, 'action': 'Sample cmd, load_value when cmd_valid == 1. Command is accepted unconditionally (cmd_ready == 1).'}, {'stage': 'S1_UPDATE', 'cycle': 1, 'action': 'Register new count, last_cmd, accepted_count on the rising clock edge after acceptance.'}, {'stage': 'S2_FLAGS', 'cycle': 1, 'action': 'Combinational zero/max flags reflect the new count value immediately.'}], 'ordering': ['Accepted commands update architectural state (count, last_cmd, accepted_count) only on clock edges.', 'zero and max are combinational functions of count and reflect updates in the same cycle.', 'No backpressure — cmd_ready is always 1.'], 'backpressure': ['No backpressure exists — cmd_ready is hardwired to 1. This is documented as a design decision.'], 'performance': {'frequency_mhz': 100, 'throughput': {'sustained_beats_per_cycle': 1, 'condition': 'One command per clock cycle when cmd_valid is high.'}, 'outstanding': {'max': 1, 'description': 'Single-cycle acceptance, single-cycle effect.'}, 'depth': {'pipeline_stages': 2, 'queue_depth': 0, 'description': 'Accept then update; no buffering.'}}, 'observability': ['Every function_model transaction maps to at least one cycle_model stage and one test_requirements scenario.']}}


# ---------------------------------------------------------------------------
# CycleModel
# ---------------------------------------------------------------------------

class CycleModel:
    """Cycle-level model: queues transactions, applies latency/handshake rules,
    delegates all functional evaluation to FunctionalModel.apply()."""

    def __init__(self, params=None):
        self.params = params or {}
        try:
            self.fl = FunctionalModel(self.params)
        except TypeError:
            self.fl = FunctionalModel()
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
        candidates = [kind]
        if kind.startswith("fm_"):
            candidates.append(kind[3:])
        cmd = txn.get("cmd")
        if cmd is not None:
            candidates.append("command_effect")
        candidates.append("default")
        for candidate in candidates:
            if candidate in _LATENCY:
                return _LATENCY[candidate]
        return 1

    def _coerce_txn_for_fl(self, txn: dict):
        if Transaction is None or not isinstance(txn, dict):
            return txn
        if isinstance(txn, Transaction):
            return txn
        if "cmd" in txn:
            return Transaction(
                cmd=int(txn.get("cmd", 0)) & 0x7,
                cmd_valid=int(txn.get("cmd_valid", 1)),
                load_value=int(txn.get("load_value", 0)) & 0xFF,
            )
        kind = str(txn.get("kind") or txn.get("op") or "").strip().lower()
        cmd_by_kind = {
            "fm_clear": 0, "clear": 0, "clear_counter": 0,
            "fm_load": 1, "load": 1, "load_counter": 1,
            "fm_inc": 2, "inc": 2, "increment": 2, "increment_counter": 2,
            "fm_dec": 3, "dec": 3, "decrement": 3, "decrement_counter": 3,
            "fm_hold": 4, "hold": 4,
            "fm_invalid": 5, "invalid": 5,
        }
        cmd = cmd_by_kind.get(kind, 4)
        load_value = int(txn.get("load_value", 0 if cmd != 1 else 0x55)) & 0xFF
        return Transaction(cmd=cmd, cmd_valid=int(txn.get("cmd_valid", 1)), load_value=load_value)

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
        # Ready-but-not-yet-observed responses no longer consume outstanding capacity.
        self._outstanding = sum(1 for (d, _r) in self.out_q if d > self.now)
        # Pop pending transactions if not stalled by outstanding cap.
        while self.in_q:
            if self._outstanding >= _OUTSTANDING_CAP:
                break  # stalled: wait for not-yet-ready out_q entries to mature
            arrival_t, txn = self.in_q[0]
            if arrival_t > self.now:
                break  # not yet arrived
            self.in_q.pop(0)
            # FunctionalModel is the ONLY oracle — one call per transaction
            try:
                result = self.fl.apply(self._coerce_txn_for_fl(txn))
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

        # Keep outstanding equal to responses that are still in flight.
        self._outstanding = sum(1 for (d, _r) in self.out_q if d > self.now)

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
        fl_errors = [r for (_d, r) in obs if isinstance(r, dict) and r.get("fl_error")]
        passed = (len(obs) == len(kinds)) and not fl_errors and (hit_bins == total_bins)
        return {
            "passed": passed,
            "backend": MODEL_BACKEND,
            "transactions": len(kinds),
            "results_observed": len(obs),
            "coverage_bins": total_bins,
            "coverage_hit": hit_bins,
            "fl_errors": fl_errors,
            "performance_targets": PERFORMANCE_TARGETS,
        }


if __name__ == "__main__":
    import json as _json
    print(_json.dumps(CycleModel().run_self_check(), indent=2))
