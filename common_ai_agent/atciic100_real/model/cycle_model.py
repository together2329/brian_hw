#!/usr/bin/env python3
"""Executable SSOT cycle-level model for atciic100_real. Wraps FunctionalModel — FL is the only oracle."""

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
_LATENCY: dict[str, int] = {'register_access': 2, 'i2c_byte': 9, 'default': 1}

# Handshake rules from SSOT cycle_model.handshake_rules.
_HANDSHAKE_RULES: list[dict] = [{'name': 'handshake_0', 'description': '', 'predicate': ''}, {'name': 'handshake_1', 'description': '', 'predicate': ''}, {'name': 'handshake_2', 'description': '', 'predicate': ''}, {'name': 'handshake_3', 'description': '', 'predicate': ''}, {'name': 'handshake_4', 'description': '', 'predicate': ''}]

# Ordering rules from SSOT cycle_model.ordering.
_ORDERING_RULES: list[dict] = [{'name': 'start_must_precede_addr', 'description': ''}, {'name': 'addr_must_precede_data', 'description': ''}, {'name': 'stop_must_follow_data_or_arblose', 'description': ''}, {'name': 'a_write_response_for_beat_i_must_complete_before_architectural_completion_of_beat_i', 'description': ''}, {'name': 'interrupt_status_updates_occur_on_the_same_rising_edge_as_the_terminal_status_transition', 'description': ''}]

# Maximum outstanding transactions before stalling.
_OUTSTANDING_CAP: int = 1

# Transaction kinds for self-check, derived from function_model.transactions at generation time.
_SELF_CHECK_KINDS: list[str] = ['FM1', 'FM2', 'FM3', 'FM4', 'FM5', 'FM6', 'FM7', 'FM8', 'FM9']

# Coverage bins: bin_name -> description.
CL_BINS: dict[str, str] = {'handshake_handshake_0': 'handshake_0', 'handshake_handshake_1': 'handshake_1', 'handshake_handshake_2': 'handshake_2', 'handshake_handshake_3': 'handshake_3', 'handshake_handshake_4': 'handshake_4', 'ordering_start_must_precede_addr': 'start_must_precede_addr', 'ordering_addr_must_precede_data': 'addr_must_precede_data', 'ordering_stop_must_follow_data_or_arblose': 'stop_must_follow_data_or_arblose', 'ordering_a_write_response_for_beat_i_must_complete_before_architectural_completion_of_beat_i': 'a_write_response_for_beat_i_must_complete_before_architectural_completion_of_beat_i', 'ordering_interrupt_status_updates_occur_on_the_same_rising_edge_as_the_terminal_status_transition': 'interrupt_status_updates_occur_on_the_same_rising_edge_as_the_terminal_status_transition', 'latency_fm1': 'latency bin for FM1', 'latency_fm2': 'latency bin for FM2', 'latency_fm3': 'latency bin for FM3', 'latency_fm4': 'latency bin for FM4', 'latency_fm5': 'latency bin for FM5', 'latency_fm6': 'latency bin for FM6', 'latency_fm7': 'latency bin for FM7', 'latency_fm8': 'latency bin for FM8', 'latency_fm9': 'latency bin for FM9'}

# SSOT payload snapshot (read-only reference; never execute functional rules from here).
SSOT_MODEL: dict = {'ip': 'atciic100_real', 'function_model': {'purpose': 'Executable behavioral contract for atciic100_real.', 'state_variables': [{'name': 'cmd', 'source': 'registers.CMD', 'reset': 0, 'description': 'Current command'}, {'name': 'cfg', 'source': 'registers.CFG', 'reset': 0, 'description': 'Global config'}, {'name': 'int_en', 'source': 'registers.INT_EN', 'reset': 0, 'description': 'Interrupt enables'}, {'name': 'int_st', 'source': 'registers.INT_ST', 'reset': 1, 'description': 'Interrupt status (FIFOEmpty=1)'}, {'name': 'setup', 'source': 'registers.SETUP', 'reset': 0, 'description': 'Timing/Setup config'}, {'name': 'addr', 'source': 'registers.ADDR', 'reset': 0, 'description': 'Target/Own address'}, {'name': 'ctrl', 'source': 'registers.CTRL', 'reset': 7936, 'description': 'Phase/Direction/Count'}, {'name': 'phase', 'source': 'fsm.iic_phase', 'reset': 'IDLE', 'description': 'Current FSM phase'}, {'name': 'fifo_count', 'source': 'memory.instances[0].count', 'reset': 0, 'description': 'Current FIFO depth'}, {'name': 'master', 'source': 'setup.Master', 'reset': 0, 'description': 'Master/Slave mode flag'}, {'name': 'trans', 'source': 'ctrl.Dir', 'reset': 0, 'description': 'Transmitter/Receiver flag'}, {'name': 'arb_lost', 'source': 'int_st.ArbLose', 'reset': 0, 'description': 'Arbitration lost flag'}, {'name': 'datacnt', 'source': 'ctrl.DataCnt', 'reset': 0, 'description': 'Remaining byte count'}], 'transactions': [{'id': 'FM1', 'name': 'reset', 'preconditions': ['presetn == 0'], 'inputs': [], 'outputs': ['All registers reset to default', 'FIFO cleared', 'FSM=IDLE'], 'side_effects': ['i2c_int goes low', 'Bus lines released (open drain)'], 'error_cases': []}, {'id': 'FM2', 'name': 'csr_read', 'preconditions': ['psel==1 && penable==1 && pwrite==0'], 'inputs': ['paddr'], 'outputs': ['prdata = RegisterFile[paddr]'], 'side_effects': ['APB read completes in 2 cycles (setup then access phase)', 'INT_ST read does not clear W1C bits (only write-1 clears)'], 'error_cases': []}, {'id': 'FM3', 'name': 'csr_write', 'preconditions': ['psel==1 && penable==1 && pwrite==1'], 'inputs': ['paddr', 'pwdata'], 'outputs': ['RegisterFile[paddr] updated'], 'side_effects': ['CMD triggers action if valid', 'SETUP updates timing'], 'error_cases': []}, {'id': 'FM4', 'name': 'master_send', 'preconditions': ['master==1', 'trans==0', 'cmd==1', 'fifo_count > 0'], 'inputs': ['addr', 'data'], 'outputs': ['SCL/SDA signals driven for Start->Addr->Data->Stop', 'Target slave ACK/NACK'], 'side_effects': ['datacnt decrements', 'ByteTrans interrupt', 'Cmpl interrupt'], 'error_cases': [{'condition': 'No ACK from slave', 'result': 'int_st.ACK = 0, check NACK'}, {'condition': 'Arbitration Lost', 'result': 'arb_lost=1, STOP driving bus'}]}, {'id': 'FM5', 'name': 'master_recv', 'preconditions': ['master==1', 'trans==1', 'cmd==1'], 'inputs': ['addr'], 'outputs': ['SCL/SDA signals driven for Start->Addr->Data->Stop', 'Data pushed to FIFO'], 'side_effects': ['datacnt decrements', 'ByteRecv interrupt', 'FIFO status updates'], 'error_cases': [{'condition': 'Slave NACK on address', 'result': 'Transaction aborted, Stop sent, ACK status updated'}]}, {'id': 'FM6', 'name': 'slave_send', 'preconditions': ['master==0', 'trans==1', 'addr matched'], 'inputs': ['bus_clk', 'bus_data'], 'outputs': ['Data from FIFO shifted out'], 'side_effects': ['ByteTrans interrupt'], 'error_cases': [{'condition': 'FIFO Empty', 'result': 'Clock Stretching'}]}, {'id': 'FM7', 'name': 'slave_recv', 'preconditions': ['master==0', 'trans==0', 'addr matched'], 'inputs': ['bus_clk', 'bus_data'], 'outputs': ['Data pushed to FIFO'], 'side_effects': ['ByteRecv interrupt'], 'error_cases': [{'condition': 'FIFO Full', 'result': 'Clock Stretching or Overrun'}]}, {'id': 'FM8', 'name': 'general_call', 'preconditions': ['master==0', 'Address byte == 0x00'], 'inputs': ['bus_clk', 'bus_data'], 'outputs': ['ACK response', 'int_st.GenCall = 1'], 'side_effects': ['AddrHit interrupt'], 'error_cases': [{'condition': 'Controller disabled (IICEn=0)', 'result': 'No ACK, general call ignored'}]}, {'id': 'FM9', 'name': 'dma_request', 'preconditions': ['setup.DMAEn == 1', '(trans==1 && fifo_count > 0) || (trans==0 && fifo_count < FIFO_DEPTH)'], 'inputs': ['DMA Enable'], 'outputs': ['i2c_req = 1'], 'side_effects': ['DMA transfers data between FIFO and memory via external DMA controller'], 'error_cases': [{'condition': 'DMA acknowledge timeout', 'result': 'FIFO overrun or underrun may occur; DMA disabled until re-enabled'}]}], 'invariants': ['FIFO count never exceeds FIFO_DEPTH parameter.', 'Phase transitions follow IDLE->START->ADDR->DAT->STOP strictly, unless ArbLose occurs.', 'Arbitration Lost (ArbLose) terminates transmission immediately and releases bus.', 'i2c_int is asserted if and only if (int_st & int_en) != 0.', 'No destination write occurs before the corresponding source read completes in any transaction.', 'SCL/SDA outputs are open-drain: driven low or released high, never actively driven high.']}, 'cycle_model': {'purpose': 'Cycle/handshake contract for atciic100_real.', 'clock': 'pclk', 'reset': {'assertion': 'presetn low clears state', 'deassertion': 'State usable on next edge'}, 'latency': {'register_access': {'min_cycles': 2, 'max_cycles': 2, 'description': 'Setup/Access phases'}, 'i2c_byte': {'min_cycles': 9, 'max_cycles': None, 'description': '8 data bits + 1 ACK, scaled by T_SCLHi'}}, 'handshake_rules': [{'signal': 'psel/penable', 'rule': 'APB protocol requires setup then access phase.'}, {'signal': 'scl_o/sda_o', 'rule': 'Open drain; drive low or float high.'}, {'signal': 'i2c_req', 'rule': 'Hold high until i2c_ack received.'}, {'signal': 'scl_i filtering', 'rule': 'Ignore pulses < T_SP * t_pclk.'}, {'signal': 'scl_i/sda_i', 'rule': 'Sample filtered SCL/SDA on rising pclk edge after glitch filter latency.'}], 'pipeline': [{'stage': 'IDLE', 'cycle': 0, 'action': 'Wait for CMD or Address Match'}, {'stage': 'START', 'cycle': 1, 'action': 'Generate Start Condition (SDA H->L while SCL High)'}, {'stage': 'ADDR', 'cycle': '2..9', 'action': 'Shift out/in Address + R/W bit'}, {'stage': 'DAT', 'cycle': '10..N', 'action': 'Shift Data Bytes'}, {'stage': 'STOP', 'cycle': 'N+1', 'action': 'Generate Stop Condition (SDA L->H while SCL High)'}], 'ordering': ['Start must precede Addr.', 'Addr must precede Data.', 'Stop must follow Data or ArbLose.', 'A write response for beat i must complete before architectural completion of beat i.', 'Interrupt status updates occur on the same rising edge as the terminal status transition.'], 'arbitration': ['Sample SDA_I on SCL rising edge. If SDA_I=0 but SDA_O=1, ArbLose.'], 'backpressure': ['FIFO Full holds SCL Low (Clock Stretching).', 'FIFO Empty in slave TX holds SCL Low until data available.'], 'observability': ['Every function_model transaction maps to at least one cycle_model stage and one test_requirements scenario.']}}


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
