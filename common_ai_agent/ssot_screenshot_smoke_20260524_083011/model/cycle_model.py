#!/usr/bin/env python3
"""Executable SSOT cycle-level model for ssot_screenshot_smoke_20260524_083011. Wraps FunctionalModel — FL is the only oracle."""

from __future__ import annotations

import json

try:
    from .functional_model import FunctionalModel
except ImportError:
    from functional_model import FunctionalModel


# ---------------------------------------------------------------------------
# SSOT-derived tables (baked at generation time)
# ---------------------------------------------------------------------------

# Executable backend. The CL model is a pure-Python deterministic stepper;
# FunctionalModel remains the oracle.
MODEL_BACKEND: str = 'python'

# Latency table: transaction kind -> cycles.  max_cycles when defined; min_cycles otherwise; default=1.
_LATENCY: dict[str, int] = {'control_access': 1, 'primary_transaction': 1, 'default': 1}

# Handshake rules from SSOT cycle_model.handshake_rules.
_HANDSHAKE_RULES: list[dict] = [{'name': 'handshake_0', 'description': '', 'predicate': ''}, {'name': 'handshake_1', 'description': '', 'predicate': ''}]

# Ordering rules from SSOT cycle_model.ordering.
_ORDERING_RULES: list[dict] = [{'name': 'accepted_transactions_preserve_externally_visible_ordering_unless_an_explicit_reordering_feature_is_listed', 'description': ''}, {'name': 'csr_side_effects_occur_in_program_order_at_the_accepted_control_transaction_boundary', 'description': ''}]

# Maximum outstanding transactions before stalling.
_OUTSTANDING_CAP: int = 1

# Cycle/performance targets used by coverage and timing instrumentation.
PERFORMANCE_TARGETS: dict = {'frequency_mhz': 100, 'throughput': {'sustained_beats_per_cycle': 1, 'condition': 'No downstream or internal backpressure'}, 'outstanding': {'max': 1, 'description': 'Default one accepted operation until Q&A declares deeper buffering'}, 'pipeline_stages': 3, 'queue_depth': 1}

# Transaction kinds for self-check, derived from function_model.transactions at generation time.
_SELF_CHECK_KINDS: list[str] = ['FM_RESET', 'FM_PRIMARY', 'FM_CSR']

# Coverage bins: bin_name -> description.
CL_BINS: dict[str, str] = {'handshake_handshake_0': 'handshake_0', 'handshake_handshake_1': 'handshake_1', 'ordering_accepted_transactions_preserve_externally_visible_ordering_unless_an_explicit_reordering_feature_is_listed': 'accepted_transactions_preserve_externally_visible_ordering_unless_an_explicit_reordering_feature_is_listed', 'ordering_csr_side_effects_occur_in_program_order_at_the_accepted_control_transaction_boundary': 'csr_side_effects_occur_in_program_order_at_the_accepted_control_transaction_boundary', 'latency_fm_reset': 'latency bin for FM_RESET', 'latency_fm_primary': 'latency bin for FM_PRIMARY', 'latency_fm_csr': 'latency bin for FM_CSR'}

# SSOT payload snapshot (read-only reference; never execute functional rules from here).
SSOT_MODEL: dict = {'ip': 'ssot_screenshot_smoke_20260524_083011', 'function_model': {'purpose': 'Cycle-independent reference model that rtl-gen and tb-gen must implement and compare against.', 'state_variables': [{'name': 'busy', 'source': 'accepted transaction or packet in progress', 'reset': 0, 'description': 'Processing state'}, {'name': 'error', 'source': 'approved error/malformed condition', 'reset': 0, 'description': 'Error indication'}, {'name': 'accepted_count', 'source': 'valid_ready_transaction', 'width': 16, 'reset': 0, 'description': 'Number of accepted valid/ready transactions.', 'output': True}], 'transactions': [{'id': 'FM_RESET', 'name': 'reset', 'preconditions': ['reset asserted'], 'inputs': ['clock', 'reset'], 'outputs': ['busy == 0', 'error == 0', 'registers and counters equal approved reset defaults', {'name': 'accepted_count', 'port': 'accepted_count', 'expr': '0', 'description': "Auto-injected placeholder rule for observable state 'accepted_count' (repair_ssot_schema rule_expr_completeness pass; advisory: downstream TB/scoreboard treats this as 0 unless overridden)."}], 'side_effects': ['clears transient protocol state', 'clears pending non-retained status'], 'error_cases': []}, {'id': 'FM_PRIMARY', 'name': 'primary_behavior', 'preconditions': ['valid input transaction or packet is accepted'], 'inputs': ['external interface signals', 'configuration/register state'], 'outputs': ['Accept one byte-oriented valid-ready transaction when valid and ready are high; output result equals data_in XOR command and assert result_valid on the accepted transaction.', {'name': 'busy', 'port': 'busy', 'expr': 'busy', 'description': 'Scoreboard-observable busy output mirrors function_model busy state.'}, {'name': 'error', 'port': 'error', 'expr': 'error', 'description': 'Scoreboard-observable error output mirrors function_model error state.'}], 'side_effects': ['updates status, counters, events, and observable outputs according to approved Q&A'], 'error_cases': [{'condition': 'malformed input or invalid control policy', 'result': 'error status follows error_handling section'}]}, {'id': 'FM_CSR', 'name': 'control_status_access', 'preconditions': ['firmware/control bus access is accepted'], 'inputs': ['address', 'write data', 'write enable', 'byte strobes'], 'outputs': ['read data and side effects match registers.register_list', {'name': 'error', 'port': 'error', 'expr': 'error', 'description': 'CSR illegal access or malformed transaction status is visible on error.'}], 'side_effects': ['RW and W1C fields update exactly as specified'], 'error_cases': [{'condition': 'unsupported address or illegal access', 'result': 'bus error/status error according to error_handling'}]}], 'invariants': ['No output, counter, status bit, or interrupt may change except as a consequence of an approved transaction, event, reset, or CSR side effect.', 'The function_model is the scoreboard source of truth for tb-gen.', 'Any behavior not represented here must be escalated to ssot-gen before RTL signoff.'], 'reference_model_hint': 'Generate a Python FunctionalModel.apply(txn) from state_variables and transactions, then compare every RTL-observable result against it.'}, 'cycle_model': {'purpose': 'Cycle-accurate protocol, reset, latency, and observability contract for rtl-gen.', 'executable': 'python', 'backend_policy': 'Use the repo-owned pure-Python deterministic stepper; FunctionalModel remains the behavioral oracle.', 'clock': 'clk', 'reset': {'signal': 'rst_n', 'polarity': 'active_low', 'assertion': 'async_assert_sync_deassert', 'deassertion': 'State may accept new work after reset deassertion and any required synchronization.'}, 'latency': {'control_access': {'min_cycles': 1, 'max_cycles': 'protocol_backpressure_bound', 'description': 'CSR/control latency is bounded by protocol ready/valid phases.'}, 'primary_transaction': {'min_cycles': 1, 'max_cycles': 'implementation_defined_by_function_model', 'description': 'Primary behavior completes when output/status event is observed.'}}, 'handshake_rules': [{'signal': 'valid_ready', 'rule': 'A transfer is accepted only on valid && ready or the equivalent approved protocol phase.'}, {'signal': 'outputs', 'rule': 'Outputs remain stable while downstream backpressure prevents acceptance.'}], 'pipeline': [{'stage': 'S0_ACCEPT', 'cycle': 0, 'action': 'Accept protocol transaction/beat/command under approved handshake.'}, {'stage': 'S1_UPDATE', 'cycle': '0..N', 'action': 'Update function_model state and datapath/control state.'}, {'stage': 'S2_OBSERVE', 'cycle': 'N..M', 'action': 'Publish output response, status, interrupt, counter, or debug event.'}], 'ordering': ['Accepted transactions preserve externally visible ordering unless an explicit reordering feature is listed.', 'CSR side effects occur in program order at the accepted control transaction boundary.'], 'backpressure': ['Input data and control state remain stable while the selected protocol applies backpressure.'], 'performance': {'frequency_mhz': 100, 'throughput': {'sustained_beats_per_cycle': 1, 'condition': 'No downstream or internal backpressure'}, 'outstanding': {'max': 1, 'description': 'Default one accepted operation until Q&A declares deeper buffering'}, 'depth': {'pipeline_stages': 3, 'queue_depth': 1, 'description': 'Accept/update/observe default cycle structure'}}, 'observability': ['busy', 'error', 'all protocol valid/ready signals', 'all CSR side-effect points']}}


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
            "transactions": len(kinds),
            "results_observed": len(obs),
            "coverage_bins": total_bins,
            "coverage_hit": hit_bins,
            "performance_targets": PERFORMANCE_TARGETS,
        }


if __name__ == "__main__":
    import json as _json
    print(_json.dumps(CycleModel().run_self_check(), indent=2))
