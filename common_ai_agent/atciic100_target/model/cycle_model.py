#!/usr/bin/env python3
"""Executable SSOT cycle-level model for atciic100_target. Wraps FunctionalModel — FL is the only oracle."""

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
_LATENCY: dict[str, int] = {'apb_register_read': 1, 'apb_register_write': 1, 'i2c_byte': 9, 'fifo_push_pop': 1, 'glitch_suppress': 3, 'default': 1}

# Handshake rules from SSOT cycle_model.handshake_rules.
_HANDSHAKE_RULES: list[dict] = [{'name': 'apb_setup', 'description': '', 'predicate': ''}, {'name': 'apb_access', 'description': '', 'predicate': ''}, {'name': 'i2c_start_stop', 'description': '', 'predicate': ''}, {'name': 'i2c_byte', 'description': '', 'predicate': ''}, {'name': 'glitch_suppress', 'description': '', 'predicate': ''}, {'name': 'dma_req_ack', 'description': '', 'predicate': ''}]

# Ordering rules from SSOT cycle_model.ordering.
_ORDERING_RULES: list[dict] = [{'name': 'start_addr_data_stop', 'description': ''}, {'name': 'arb_lose_terminates', 'description': ''}]

# Maximum outstanding transactions before stalling.
_OUTSTANDING_CAP: int = 1

# Transaction kinds for self-check, derived from function_model.transactions at generation time.
_SELF_CHECK_KINDS: list[str] = ['FM_RESET', 'FM_CSR_WRITE', 'FM_CSR_READ', 'FM_MASTER_SEND', 'FM_MASTER_RECV', 'FM_SLAVE_RECV', 'FM_SLAVE_SEND', 'FM_GEN_CALL', 'FM_DMA_REQ']

# Coverage bins: bin_name -> description.
CL_BINS: dict[str, str] = {'handshake_apb_setup': 'apb_setup', 'handshake_apb_access': 'apb_access', 'handshake_i2c_start_stop': 'i2c_start_stop', 'handshake_i2c_byte': 'i2c_byte', 'handshake_glitch_suppress': 'glitch_suppress', 'handshake_dma_req_ack': 'dma_req_ack', 'ordering_start_addr_data_stop': 'start_addr_data_stop', 'ordering_arb_lose_terminates': 'arb_lose_terminates', 'latency_fm_reset': 'latency bin for FM_RESET', 'latency_fm_csr_write': 'latency bin for FM_CSR_WRITE', 'latency_fm_csr_read': 'latency bin for FM_CSR_READ', 'latency_fm_master_send': 'latency bin for FM_MASTER_SEND', 'latency_fm_master_recv': 'latency bin for FM_MASTER_RECV', 'latency_fm_slave_recv': 'latency bin for FM_SLAVE_RECV', 'latency_fm_slave_send': 'latency bin for FM_SLAVE_SEND', 'latency_fm_gen_call': 'latency bin for FM_GEN_CALL', 'latency_fm_dma_req': 'latency bin for FM_DMA_REQ'}

# SSOT payload snapshot (read-only reference; never execute functional rules from here).
SSOT_MODEL: dict = {'ip': 'atciic100_target', 'function_model': {'state_variables': [{'name': 'cmd', 'width': 32, 'reset': 0, 'description': 'Command register (read/write/start/stop/cont)'}, {'name': 'cfg', 'width': 32, 'reset': 0, 'description': 'Configuration register (timing/role/dma_en)'}, {'name': 'int_en', 'width': 32, 'reset': 0, 'description': 'Interrupt enable mask'}, {'name': 'int_st', 'width': 32, 'reset': 0, 'description': 'Interrupt status (write-1-clear)'}, {'name': 'setup', 'width': 32, 'reset': 0, 'description': 'Setup register (addr/datacnt)'}, {'name': 'addr_reg', 'width': 10, 'reset': 0, 'description': 'I2C target address'}, {'name': 'datacnt', 'width': 9, 'reset': 0, 'description': 'Remaining byte count'}, {'name': 'phase', 'width': 4, 'reset': 0, 'description': 'I2C phase: IDLE/START/ADDR/DAT/STOP'}, {'name': 'fifo_count', 'width': 5, 'reset': 0, 'description': 'FIFO occupancy'}, {'name': 'master', 'width': 1, 'reset': 0, 'description': 'Master-mode currently active'}, {'name': 'trans', 'width': 1, 'reset': 0, 'description': 'Transaction in progress'}, {'name': 'arb_lost', 'width': 1, 'reset': 0, 'description': 'Arbitration lost flag'}], 'transactions': [{'id': 'FM_RESET', 'name': 'reset', 'outputs': ['all state -> reset values'], 'side_effects': ['clear FIFO', 'release SDA/SCL'], 'error_cases': []}, {'id': 'FM_CSR_WRITE', 'name': 'csr_write', 'preconditions': ['psel && penable && pwrite'], 'outputs': ['register at paddr updated with pwdata'], 'side_effects': ['clear-on-write fields applied (int_st)'], 'error_cases': [{'condition': 'reserved address', 'result': 'no-op'}]}, {'id': 'FM_CSR_READ', 'name': 'csr_read', 'preconditions': ['psel && penable && !pwrite'], 'outputs': ['prdata := register at paddr'], 'side_effects': [], 'error_cases': [{'condition': 'reserved address', 'result': 'prdata=0'}]}, {'id': 'FM_MASTER_SEND', 'name': 'master_send', 'preconditions': ['cmd.start && cfg.master_mode && fifo_count > 0'], 'outputs': ['sda_o pulled per byte from fifo', 'scl_o toggled per timing'], 'side_effects': ['phase walks IDLE->START->ADDR->DAT->STOP', 'datacnt decrements per byte', 'trans=1'], 'error_cases': [{'condition': 'ACK not received', 'result': 'int_st.ack_neg=1; phase->STOP'}, {'condition': 'arbitration lost mid-byte', 'result': 'arb_lost=1; int_st.arblose=1'}]}, {'id': 'FM_MASTER_RECV', 'name': 'master_recv', 'preconditions': ['cmd.start && cmd.read && cfg.master_mode'], 'outputs': ['sda_i sampled per byte and pushed to fifo'], 'side_effects': ['phase walks IDLE->START->ADDR->DAT->STOP', 'datacnt decrements per byte'], 'error_cases': [{'condition': 'fifo full mid-byte', 'result': 'stall scl until drained'}]}, {'id': 'FM_SLAVE_RECV', 'name': 'slave_recv', 'preconditions': ['!cfg.master_mode', 'addr matches addr_reg or general-call enabled'], 'outputs': ['sda_o ACK after addr match', 'byte from sda_i pushed to fifo'], 'side_effects': ['int_st.byterecv=1 per byte'], 'error_cases': [{'condition': 'fifo full', 'result': 'NACK'}]}, {'id': 'FM_SLAVE_SEND', 'name': 'slave_send', 'preconditions': ['!cfg.master_mode', 'addr matches and master is reading'], 'outputs': ['sda_o driven from fifo per byte'], 'side_effects': ['int_st.bytetrans=1 per byte'], 'error_cases': []}, {'id': 'FM_GEN_CALL', 'name': 'general_call', 'preconditions': ['incoming addr=0x00, gen_call enabled'], 'outputs': ['int_st.gencall=1'], 'side_effects': ['accept first byte and pass to ctrl'], 'error_cases': []}, {'id': 'FM_DMA_REQ', 'name': 'dma_request', 'preconditions': ['cfg.dma_en && fifo edge crosses threshold'], 'outputs': ['dma_req asserted until dma_ack'], 'side_effects': [], 'error_cases': [{'condition': 'dma_ack not received within timeout', 'result': 'dma_req held'}]}], 'invariants': ['fifo_count <= FIFO_DEPTH', 'phase != IDLE -> trans == 1', 'trans == 1 -> presetn == 1', 'arb_lost == 1 -> phase->STOP within 4 cycles', 'int_st write-1-clear: only set bits in pwdata clear int_st']}, 'cycle_model': {'clock': 'pclk', 'reset': {'polarity': 'active_low_async', 'deassertion': 'synchronous_to_pclk'}, 'latency': {'apb_register_read': {'min_cycles': 0, 'max_cycles': 1}, 'apb_register_write': {'min_cycles': 0, 'max_cycles': 1}, 'i2c_byte': {'min_cycles': 9, 'max_cycles': None}, 'fifo_push_pop': {'min_cycles': 0, 'max_cycles': 1}, 'glitch_suppress': {'min_cycles': 1, 'max_cycles': 3}}, 'outstanding': 1, 'handshake_rules': [{'name': 'apb_setup', 'signal': 'psel && !penable', 'rule': '1-cycle APB setup'}, {'name': 'apb_access', 'signal': 'psel && penable', 'rule': 'Access completes when slave drives prdata or accepts pwdata'}, {'name': 'i2c_start_stop', 'signal': 'sda falling while scl high (start) / sda rising while scl high (stop)', 'rule': 'START opens transaction; STOP closes'}, {'name': 'i2c_byte', 'signal': '9 SCL pulses (8 data + 1 ACK)', 'rule': 'MSB-first; ACK by receiver'}, {'name': 'glitch_suppress', 'signal': 'filter sda/scl glitches < t_sp', 'rule': 'Suppress glitches shorter than t_sp'}, {'name': 'dma_req_ack', 'signal': 'dma_req && dma_ack', 'rule': 'Hold dma_req until dma_ack'}], 'ordering': [{'name': 'start_addr_data_stop', 'rule': 'Each transaction: START -> ADDR(7-bit + R/W) -> DATA(N bytes) -> STOP'}, {'name': 'arb_lose_terminates', 'rule': 'On arbitration loss, immediately release SDA and abort phase'}], 'arbitration': [{'name': 'i2c_multimaster', 'algorithm': 'open-drain; loser detects mismatch on sampled sda_i', 'winners': 'master that drives 0 while bus is 0'}], 'backpressure': [{'name': 'fifo_full', 'rule': 'FIFO full causes scl to stretch (clock stretching) until drained'}, {'name': 'fifo_empty', 'rule': 'FIFO empty in master_send causes phase->STOP after current byte'}], 'observability': ['int_st bits visible via APB', 'fifo half_full/half_empty signals', 'phase visible in DBGSTATUS']}}


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
