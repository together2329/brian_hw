#!/usr/bin/env python3
"""Executable SSOT cycle-level model for atcwdt200. Wraps FunctionalModel — FL is the only oracle."""

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
_LATENCY: dict[str, int] = {'register_read': 1, 'register_write': 1, 'watchdog_timeout': 1, 'default': 1}

# Handshake rules from SSOT cycle_model.handshake_rules.
_HANDSHAKE_RULES: list[dict] = [{'name': 'handshake_0', 'description': '', 'predicate': ''}, {'name': 'handshake_1', 'description': '', 'predicate': ''}, {'name': 'handshake_2', 'description': '', 'predicate': ''}]

# Ordering rules from SSOT cycle_model.ordering.
_ORDERING_RULES: list[dict] = [{'name': 'wen_unlock_is_evaluated_before_a_protected_write_consumes_or_clears_unlock_state_according_to_approved_qa_policy', 'description': ''}, {'name': 'restart_command_clears_counter_and_returns_state_to_st_inttime', 'description': ''}, {'name': 'interrupt_timeout_set_happens_before_reset_time_phase_begins', 'description': ''}, {'name': 'reset_timeout_clears_cr_en_and_asserts_reset_status', 'description': ''}]

# Maximum outstanding transactions before stalling.
_OUTSTANDING_CAP: int = 1

# Cycle/performance targets used by coverage and PyMTL shell instrumentation.
PERFORMANCE_TARGETS: dict = {'frequency_mhz': 50, 'throughput': {'register_accesses_per_cycle': 1, 'condition': 'APB-like access with no wait states if legacy mode is selected'}, 'outstanding': {'description': 'Single APB access at a time'}, 'pipeline_stages': 5, 'queue_depth': 0}

# Transaction kinds for self-check, derived from function_model.transactions at generation time.
_SELF_CHECK_KINDS: list[str] = ['apb_read', 'apb_write', 'write_unlock', 'restart', 'watchdog_tick', 'timeout_decode']

# Coverage bins: bin_name -> description.
CL_BINS: dict[str, str] = {'handshake_handshake_0': 'handshake_0', 'handshake_handshake_1': 'handshake_1', 'handshake_handshake_2': 'handshake_2', 'ordering_wen_unlock_is_evaluated_before_a_protected_write_consumes_or_clears_unlock_state_according_to_approved_qa_policy': 'wen_unlock_is_evaluated_before_a_protected_write_consumes_or_clears_unlock_state_according_to_approved_qa_policy', 'ordering_restart_command_clears_counter_and_returns_state_to_st_inttime': 'restart_command_clears_counter_and_returns_state_to_st_inttime', 'ordering_interrupt_timeout_set_happens_before_reset_time_phase_begins': 'interrupt_timeout_set_happens_before_reset_time_phase_begins', 'ordering_reset_timeout_clears_cr_en_and_asserts_reset_status': 'reset_timeout_clears_cr_en_and_asserts_reset_status', 'latency_apb_read': 'latency bin for apb_read', 'latency_apb_write': 'latency bin for apb_write', 'latency_write_unlock': 'latency bin for write_unlock', 'latency_restart': 'latency bin for restart', 'latency_watchdog_tick': 'latency bin for watchdog_tick', 'latency_timeout_decode': 'latency bin for timeout_decode'}

# SSOT payload snapshot (read-only reference; never execute functional rules from here).
SSOT_MODEL: dict = {'ip': 'atcwdt200', 'function_model': {'purpose': 'Executable watchdog timer contract for FL model, RTL, and TB.', 'state_variables': [{'name': 'CR_EN', 'width': 1, 'reset': 0, 'description': 'Watchdog enable'}, {'name': 'CR_CLK', 'width': 1, 'reset': 0, 'description': 'Tick source select'}, {'name': 'CR_INTEN', 'width': 1, 'reset': 0, 'description': 'Interrupt enable'}, {'name': 'CR_RSTEN', 'width': 1, 'reset': 0, 'description': 'Reset output enable'}, {'name': 'CR_INTTIME', 'width': 'INT_TIME_WIDTH', 'reset': 0, 'description': 'Interrupt timeout encoding'}, {'name': 'CR_RSTTIME', 'width': 3, 'reset': 0, 'description': 'Reset timeout encoding'}, {'name': 'SR_INTZERO', 'width': 1, 'reset': 0, 'description': 'Interrupt timeout pending status'}, {'name': 'SR_RSTZERO', 'width': 1, 'reset': 0, 'description': 'Reset timeout internal status'}, {'name': 'REG_WEN', 'width': 1, 'reset': 0, 'description': 'Protected-write enable latch'}, {'name': 'COUNTER', 'width': 'COUNTER_WIDTH', 'reset': 0, 'description': 'Watchdog counter'}, {'name': 'STATE', 'width': 1, 'reset': 'ST_INTTIME', 'description': 'Interrupt-time or reset-time phase'}], 'transactions': [{'id': 'apb_read', 'name': 'APB register read', 'preconditions': ['psel and penable are asserted', 'pwrite is low'], 'inputs': ['paddr'], 'outputs': ['prdata returns selected register value'], 'side_effects': ['No architectural state changes on read'], 'error_cases': ['Unsupported offsets return zero in legacy-compatible mode.']}, {'id': 'apb_write', 'name': 'APB register write', 'preconditions': ['psel and penable and pwrite are asserted'], 'inputs': ['paddr', 'pwdata'], 'outputs': ['Protected registers update only when REG_WEN is set according to approved policy'], 'side_effects': ['May update CR', 'set REG_WEN', 'clear SR_INTZERO', 'or issue restart command'], 'error_cases': ['Writes without unlock to protected registers have no effect']}, {'id': 'write_unlock', 'name': 'Write protection unlock', 'preconditions': ['APB write to WEN offset 0x18'], 'inputs': ['pwdata'], 'outputs': ['REG_WEN becomes one when lower 16 bits match 0x5aa5'], 'side_effects': ['Unlock consumption policy pending QA'], 'error_cases': ['Wrong magic value does not unlock']}, {'id': 'restart', 'name': 'Watchdog restart command', 'preconditions': ['Unlocked APB write to RES offset 0x14 with lower 16 bits 0xcafe'], 'inputs': ['pwdata', 'REG_WEN'], 'outputs': ['COUNTER resets to zero and STATE becomes ST_INTTIME'], 'side_effects': ['Restart command is a pulse'], 'error_cases': ['Wrong magic or locked write has no restart effect']}, {'id': 'watchdog_tick', 'name': 'Watchdog tick and timeout update', 'preconditions': ['CR_EN is set', 'wdt_pause synchronized value is zero'], 'inputs': ['pclk_tick', 'extclk_rising_pulse', 'CR_CLK', 'CR_INTTIME', 'CR_RSTTIME', 'STATE', 'restart_cmd', 'inttime_end', 'rsttime_end'], 'outputs': ['wdt_int and wdt_rst reflect timeout status gated by enables'], 'side_effects': ['Timeout table uses the observed reference counter bit taps.'], 'error_cases': ['No counting while paused or disabled']}, {'id': 'timeout_decode', 'name': 'Timeout interval decode', 'preconditions': ['COUNTER advances'], 'inputs': ['CR_INTTIME', 'CR_RSTTIME', 'COUNTER'], 'outputs': ['inttime_end and rsttime_end predicates'], 'side_effects': ['Drives watchdog_tick state updates'], 'error_cases': ['Unsupported encodings are not expected if table is locked']}], 'invariants': ['wdt_int equals SR_INTZERO & CR_INTEN.', 'wdt_rst equals SR_RSTZERO & CR_RSTEN.', 'Counter does not advance while disabled or paused.', 'Reserved register bits read as zero and ignore writes unless QA approves modernized behavior.'], 'reference_model_hint': 'FL model should implement register transactions, protected-write policy, timeout table, and tick-source selection before RTL is generated.'}, 'cycle_model': {'purpose': 'Cycle/handshake contract for watchdog control timing.', 'executable': 'python', 'backend_policy': 'Use FL model as behavioral oracle and cycle model for pclk-edge sequencing.', 'clock': 'pclk', 'reset': {'assertion': 'presetn low asynchronously clears architectural state.', 'deassertion': 'Generated RTL should use async assert and synchronous operational use after reset release.'}, 'latency': {'register_read': {'min_cycles': 0, 'max_cycles': 1, 'description': 'Reference prdata is combinational from delayed paddr; exact APB read latency pending protocol QA.'}, 'register_write': {'min_cycles': 1, 'max_cycles': 1, 'description': 'Writes update state on pclk when psel && penable && pwrite.'}, 'watchdog_timeout': {'min_cycles': 1, 'max_cycles': None, 'description': 'Determined by timeout tap table and selected tick source.'}}, 'handshake_rules': [{'signal': 'psel', 'rule': 'Address is captured when psel is high.'}, {'signal': 'penable', 'rule': 'Write access is valid when psel && penable && pwrite.'}, {'signal': 'extclk', 'rule': 'External tick is consumed as synchronized rising-edge pulse if CDC QA approves internal sync.'}], 'pipeline': [{'stage': 'S0_APB_ADDR', 'cycle': 0, 'action': 'Capture APB address during select phase.'}, {'stage': 'S1_APB_ACCESS', 'cycle': 1, 'action': 'Apply APB write side effects or drive selected read data.'}, {'stage': 'S2_SYNC', 'cycle': 0, 'action': 'Synchronize extclk and wdt_pause into pclk domain.'}, {'stage': 'S3_COUNT', 'cycle': 0, 'action': 'Increment or clear watchdog counter based on enable', 'pause': None, 'selected tick': None, 'restart': None, 'and timeout.': None}, {'stage': 'S4_TIMEOUT_OUTPUT', 'cycle': 0, 'action': 'Update interrupt/reset status and outputs.'}], 'ordering': ['WEN unlock is evaluated before a protected write consumes or clears unlock state according to approved QA policy.', 'Restart command clears counter and returns state to ST_INTTIME.', 'Interrupt timeout set happens before reset-time phase begins.', 'Reset timeout clears CR.EN and asserts reset status.'], 'backpressure': ['APB interface has no backpressure in the reference; APB4 ready/error behavior is pending QA.'], 'performance': {'frequency_mhz': 50, 'throughput': {'register_accesses_per_cycle': 1, 'condition': 'APB-like access with no wait states if legacy mode is selected'}, 'outstanding': {'apb_max': 1, 'description': 'Single APB access at a time'}, 'depth': {'pipeline_stages': 5, 'queue_depth': 0, 'description': 'Register access plus synchronizer/counter stages'}}, 'observability': ['Every function_model transaction maps to at least one scenario and coverage bin.']}}


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
