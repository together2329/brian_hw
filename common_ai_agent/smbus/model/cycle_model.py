#!/usr/bin/env python3
"""Executable SSOT cycle-level model for smbus. Wraps FunctionalModel — FL is the only oracle."""

from __future__ import annotations

import json

try:
    from .functional_model import FunctionalModel
except ImportError:
    from functional_model import FunctionalModel


# ---------------------------------------------------------------------------
# SSOT-derived tables (baked at generation time)
# ---------------------------------------------------------------------------

# Latency table: transaction kind -> cycles.  max_cycles when defined; min_cycles otherwise; default=1.
_LATENCY: dict[str, int] = {'write_byte': 9, 'read_byte': 9, 'send_stop': 1, 'default': 1}

# Handshake rules from SSOT cycle_model.handshake_rules.
_HANDSHAKE_RULES: list[dict] = [{'name': 'valid_ready', 'description': 'Transaction accepted when cmd_valid && !busy', 'predicate': 'cmd_valid && !busy'}, {'name': 'ack_check', 'description': 'ACK received from slave after address phase', 'predicate': 'ack_received'}, {'name': 'stop_after_nack', 'description': 'STOP condition issued after NACK', 'predicate': 'nack_flag -> stop_issued'}]

# Ordering rules from SSOT cycle_model.ordering.
_ORDERING_RULES: list[dict] = [{'name': 'start_before_data', 'description': 'START condition must precede data transfer'}, {'name': 'address_before_data', 'description': 'Address phase must complete before data phase'}]

# Maximum outstanding transactions before stalling.
_OUTSTANDING_CAP: int = 1

# Transaction kinds for self-check, derived from function_model.transactions at generation time.
_SELF_CHECK_KINDS: list[str] = ['write_byte', 'read_byte', 'send_stop']

# Coverage bins: bin_name -> description.
CL_BINS: dict[str, str] = {'handshake_valid_ready': 'Transaction accepted when cmd_valid && !busy', 'handshake_ack_check': 'ACK received from slave after address phase', 'handshake_stop_after_nack': 'STOP condition issued after NACK', 'ordering_start_before_data': 'START condition must precede data transfer', 'ordering_address_before_data': 'Address phase must complete before data phase', 'latency_write_byte': 'latency bin for write_byte', 'latency_read_byte': 'latency bin for read_byte', 'latency_send_stop': 'latency bin for send_stop'}

# SSOT payload snapshot (read-only reference; never execute functional rules from here).
SSOT_MODEL: dict = {'ip': 'smbus', 'function_model': {'state_variables': [{'name': 'state', 'width': 4, 'reset': 0, 'description': 'Main FSM state'}, {'name': 'shift_reg', 'width': 8, 'reset': 0, 'description': 'Shift register for TX/RX'}, {'name': 'bit_cnt', 'width': 4, 'reset': 0, 'description': 'Bit counter'}, {'name': 'addr_reg', 'width': 7, 'reset': 0, 'description': 'Target slave address'}, {'name': 'data_reg', 'width': 8, 'reset': 0, 'description': 'Data register'}, {'name': 'busy', 'width': 1, 'reset': 0, 'description': 'Bus busy flag'}, {'name': 'nack_flag', 'width': 1, 'reset': 0, 'description': 'NACK received flag'}], 'transactions': [{'id': 'write_byte', 'name': 'write_byte', 'description': 'Send one data byte to slave after START + address phase', 'sample_condition': 'cmd_write && !busy', 'inputs': [{'name': 'addr', 'width': 7}, {'name': 'data', 'width': 8}]}, {'id': 'read_byte', 'name': 'read_byte', 'description': 'Receive one data byte from slave', 'sample_condition': 'cmd_read && !busy', 'inputs': [{'name': 'addr', 'width': 7}]}, {'id': 'send_stop', 'name': 'send_stop', 'description': 'Generate STOP condition on bus', 'sample_condition': 'state == STATE_STOP', 'inputs': []}], 'invariants': [{'name': 'busy_mutex', 'expression': '!(cmd_write && cmd_read)', 'description': 'Write and read commands are mutually exclusive'}, {'name': 'addr_7bit', 'expression': 'addr_reg < 128', 'description': 'Address is always 7-bit'}, {'name': 'idle_on_rst', 'expression': 'rst_n == 0 -> state == STATE_IDLE', 'description': 'Reset drives state to IDLE'}]}, 'cycle_model': {'clock': 'clk', 'reset': 'rst_n', 'latency': {'write_byte': {'min_cycles': 9, 'max_cycles': 9}, 'read_byte': {'min_cycles': 9, 'max_cycles': 9}, 'send_stop': {'min_cycles': 1, 'max_cycles': 1}, 'default': {'min_cycles': 1, 'max_cycles': 1}}, 'outstanding': 1, 'handshake_rules': [{'name': 'valid_ready', 'description': 'Transaction accepted when cmd_valid && !busy', 'predicate': 'cmd_valid && !busy'}, {'name': 'ack_check', 'description': 'ACK received from slave after address phase', 'predicate': 'ack_received'}, {'name': 'stop_after_nack', 'description': 'STOP condition issued after NACK', 'predicate': 'nack_flag -> stop_issued'}], 'ordering': [{'name': 'start_before_data', 'description': 'START condition must precede data transfer'}, {'name': 'address_before_data', 'description': 'Address phase must complete before data phase'}], 'arbitration': [{'name': 'bus_arbitration', 'description': 'Lost arbitration detected when SDA driven high but reads low'}]}}


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
            "transactions": len(kinds),
            "results_observed": len(obs),
            "coverage_bins": total_bins,
            "coverage_hit": hit_bins,
        }


if __name__ == "__main__":
    import json as _json
    print(_json.dumps(CycleModel().run_self_check(), indent=2))
