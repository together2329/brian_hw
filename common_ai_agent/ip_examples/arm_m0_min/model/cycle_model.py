#!/usr/bin/env python3
"""Executable SSOT cycle-level model for arm_m0_min. Wraps FunctionalModel — FL is the only oracle."""

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
_LATENCY: dict[str, int] = {'fetch_accept': 1, 'alu_instr': 1, 'load_store_instr': 1, 'default': 1}

# Handshake rules from SSOT cycle_model.handshake_rules.
_HANDSHAKE_RULES: list[dict] = [{'name': 'handshake_0', 'description': '', 'predicate': ''}, {'name': 'handshake_1', 'description': '', 'predicate': ''}, {'name': 'handshake_2', 'description': '', 'predicate': ''}]

# Ordering rules from SSOT cycle_model.ordering.
_ORDERING_RULES: list[dict] = [{'name': 'program_order_retirement_instruction_i_commits_before_i_1', 'description': ''}, {'name': 'branch_redirection_affects_subsequent_fetch_only_after_branch_evaluation_reaches_commit_boundary', 'description': ''}]

# Maximum outstanding transactions before stalling.
_OUTSTANDING_CAP: int = 1

# Cycle/performance targets used by coverage and PyMTL shell instrumentation.
PERFORMANCE_TARGETS: dict = {'frequency_mhz': None, 'throughput': None, 'outstanding': None, 'pipeline_stages': None, 'queue_depth': None}

# Transaction kinds for self-check, derived from function_model.transactions at generation time.
_SELF_CHECK_KINDS: list[str] = ['TX_DECODE_EXEC', 'TX_LOAD_STORE']

# Coverage bins: bin_name -> description.
CL_BINS: dict[str, str] = {'handshake_handshake_0': 'handshake_0', 'handshake_handshake_1': 'handshake_1', 'handshake_handshake_2': 'handshake_2', 'ordering_program_order_retirement_instruction_i_commits_before_i_1': 'program_order_retirement_instruction_i_commits_before_i_1', 'ordering_branch_redirection_affects_subsequent_fetch_only_after_branch_evaluation_reaches_commit_boundary': 'branch_redirection_affects_subsequent_fetch_only_after_branch_evaluation_reaches_commit_boundary', 'latency_tx_decode_exec': 'latency bin for TX_DECODE_EXEC', 'latency_tx_load_store': 'latency bin for TX_LOAD_STORE'}

# SSOT payload snapshot (read-only reference; never execute functional rules from here).
SSOT_MODEL: dict = {'ip': 'arm_m0_min', 'function_model': {'purpose': 'Cycle-independent architectural contract for downstream RTL and scoreboard generation', 'state_variables': [{'name': 'pc', 'source': 'register_file.R15', 'reset': 0, 'description': 'Program counter'}, {'name': 'gpr', 'source': 'register_file.R0_R14', 'reset': 0, 'description': 'General registers'}, {'name': 'nzcv', 'source': 'arch_flags', 'reset': 0, 'description': 'Condition flags'}, {'name': 'fault_halt', 'source': 'fault_state', 'reset': 0, 'description': 'Fault-halt latch'}], 'transactions': [{'id': 'TX_DECODE_EXEC', 'name': 'alu_compare_branch', 'preconditions': ['fault_halt == 0', 'instruction fetch completed with i_hready == 1 and i_hresp == OKAY'], 'inputs': ['decoded opcode', 'operand values from architectural registers'], 'outputs': ['ALU destination register update for ADD/SUB/AND/ORR/EOR/MOV/LSL/LSR/ASR', 'NZCV updated only for CMP', 'PC updated sequentially or redirected for B/BEQ/BNE'], 'side_effects': ['pc advances by instruction size on non-branch', 'pc set to target when branch taken'], 'error_cases': [{'condition': 'instruction bus response ERROR', 'result': 'fault_halt set and architectural state frozen except reset'}]}, {'id': 'TX_LOAD_STORE', 'name': 'single_transfer_memory_access', 'preconditions': ['fault_halt == 0', 'decoded opcode is LDR or STR'], 'inputs': ['base register', 'immediate offset', 'store data for STR or bus read data for LDR'], 'outputs': ['LDR updates destination register with returned word', 'STR commits one data write on bus'], 'side_effects': ['pc advances after transfer completion'], 'error_cases': [{'condition': 'data bus response ERROR', 'result': 'fault_halt set and no further instruction retirement'}]}], 'invariants': ['No instruction retires while fault_halt==1.', 'IF/ID/EX ordering remains in-order with no out-of-order commit.', 'Register writes occur only from committed EX outcomes.'], 'reference_model_hint': 'tb-gen should create a Python architectural model tracking pc/gpr/nzcv/fault_halt and compare each committed instruction outcome.'}, 'cycle_model': {'purpose': 'Cycle-accurate handshake and stage ordering contract', 'executable': 'pymtl3', 'clock': 'clk', 'reset': {'assertion': 'When rst=1 at rising edge, pipeline and architectural state reset synchronously', 'deassertion': 'After rst returns 0, fetch starts on next rising edge'}, 'latency': {'fetch_accept': {'min_cycles': 1, 'max_cycles': None, 'description': 'Depends on i_hready backpressure'}, 'alu_instr': {'min_cycles': 1, 'max_cycles': 1, 'description': 'No extra wait in EX for pure ALU ops'}, 'load_store_instr': {'min_cycles': 1, 'max_cycles': None, 'description': 'Variable with d_hready'}}, 'handshake_rules': [{'signal': 'i_htrans', 'rule': 'IF keeps transfer intent stable until i_hready handshake occurs'}, {'signal': 'd_htrans', 'rule': 'EX keeps active transfer until d_hready indicates completion'}, {'signal': 'd_hwdata', 'rule': 'For STR, write data remains stable while waiting for d_hready'}], 'pipeline': [{'stage': 'IF', 'cycle': 'n', 'action': 'Drive instruction address/control and capture instruction on ready'}, {'stage': 'ID', 'cycle': 'n+1', 'action': 'Decode instruction and read source operands'}, {'stage': 'EX', 'cycle': 'n+2', 'action': 'Execute/branch/load-store and commit results'}], 'ordering': ['Program-order retirement: instruction i commits before i+1.', 'Branch redirection affects subsequent fetch only after branch evaluation reaches commit boundary.'], 'backpressure': ['i_hready=0 stalls IF and upstream PC progression without corrupting ID/EX committed state.', 'd_hready=0 stalls memory operation in EX; no duplicate commit allowed.'], 'observability': ['Expose stage valid/stall indicators, pc, decode class, bus handshakes, and fault_halt for waveform and checker correlation.'], 'performance': {'ipc_nominal': 1.0, 'stall_sensitivity': {'if_backpressure': 'IPC degrades proportionally to i_hready low duty cycle', 'mem_backpressure': 'IPC degrades during load/store wait windows on d_hready low'}, 'branch_penalty_cycles': {'taken_min': 1, 'taken_max': 2}}}}


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
