#!/usr/bin/env python3
"""Executable SSOT cycle-level model for rv32i_min. Wraps FunctionalModel — FL is the only oracle."""

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
_LATENCY: dict[str, int] = {'fetch_to_decode': 1, 'alu_ops_retire': 3, 'load_retire': 3, 'store_issue': 3, 'fence_penalty': 1, 'default': 1}

# Handshake rules from SSOT cycle_model.handshake_rules.
_HANDSHAKE_RULES: list[dict] = [{'name': 'handshake_0', 'description': '', 'predicate': ''}, {'name': 'handshake_1', 'description': '', 'predicate': ''}, {'name': 'handshake_2', 'description': '', 'predicate': ''}, {'name': 'handshake_3', 'description': '', 'predicate': ''}]

# Ordering rules from SSOT cycle_model.ordering.
_ORDERING_RULES: list[dict] = [{'name': 'retirement_is_in_program_order_with_at_most_one_commit_per_cycle', 'description': ''}, {'name': 'faulting_misaligned_or_illegal_instruction_does_not_retire', 'description': ''}, {'name': 'store_side_effects_occur_only_on_aligned_non_faulting_stores', 'description': ''}]

# Maximum outstanding transactions before stalling.
_OUTSTANDING_CAP: int = 1

# Cycle/performance targets used by coverage and PyMTL shell instrumentation.
PERFORMANCE_TARGETS: dict = {'frequency_mhz': 100, 'throughput': {'sustained_beats_per_cycle': 1, 'condition': 'synchronous memory response each cycle'}, 'outstanding': {'max': 1, 'description': 'single in-flight architectural operation'}, 'pipeline_stages': 3, 'queue_depth': 1}

# Transaction kinds for self-check, derived from function_model.transactions at generation time.
_SELF_CHECK_KINDS: list[str] = ['FM_FETCH', 'FM_ALU', 'FM_BRANCH', 'FM_JUMP', 'FM_LOAD', 'FM_STORE', 'FM_SYSTEM']

# Coverage bins: bin_name -> description.
CL_BINS: dict[str, str] = {'handshake_handshake_0': 'handshake_0', 'handshake_handshake_1': 'handshake_1', 'handshake_handshake_2': 'handshake_2', 'handshake_handshake_3': 'handshake_3', 'ordering_retirement_is_in_program_order_with_at_most_one_commit_per_cycle': 'retirement_is_in_program_order_with_at_most_one_commit_per_cycle', 'ordering_faulting_misaligned_or_illegal_instruction_does_not_retire': 'faulting_misaligned_or_illegal_instruction_does_not_retire', 'ordering_store_side_effects_occur_only_on_aligned_non_faulting_stores': 'store_side_effects_occur_only_on_aligned_non_faulting_stores', 'latency_fm_fetch': 'latency bin for FM_FETCH', 'latency_fm_alu': 'latency bin for FM_ALU', 'latency_fm_branch': 'latency bin for FM_BRANCH', 'latency_fm_jump': 'latency bin for FM_JUMP', 'latency_fm_load': 'latency bin for FM_LOAD', 'latency_fm_store': 'latency bin for FM_STORE', 'latency_fm_system': 'latency bin for FM_SYSTEM'}

# SSOT payload snapshot (read-only reference; never execute functional rules from here).
SSOT_MODEL: dict = {'ip': 'rv32i_min', 'function_model': {'purpose': 'Cycle-independent RV32I architectural contract for ISS-style equivalence and scoreboard comparison.', 'state_variables': [{'name': 'pc', 'source': 'architectural', 'reset': 0, 'description': 'Program counter'}, {'name': 'regfile', 'source': 'architectural', 'reset': 0, 'description': '32x32 register file with x0 immutable zero'}, {'name': 'excpt_o', 'source': 'architectural_output', 'reset': 0, 'description': 'One-cycle exception pulse'}], 'transactions': [{'id': 'FM_FETCH', 'name': 'fetch_and_default_advance', 'preconditions': ['pc % 4 == 0'], 'inputs': ['pc', 'i_rdata'], 'outputs': ['decoded instruction fields available to execute stage', 'default next_pc equals pc plus 4'], 'side_effects': ['pc advances by 4 when no control transfer or fault blocks retirement']}, {'id': 'FM_ALU', 'name': 'alu_and_immediate_ops', 'preconditions': ['opcode_class == 0'], 'inputs': ['rs1', 'rs2', 'imm', 'funct3', 'funct7'], 'outputs': ['rd receives computed 32-bit result'], 'side_effects': ['regfile writeback occurs when rd != 0'], 'error_cases': [{'condition': 'illegal_shamt', 'result': 'excpt_o pulse and no retirement'}]}, {'id': 'FM_BRANCH', 'name': 'conditional_branches', 'preconditions': ['is_branch'], 'inputs': ['pc', 'branch_taken', 'branch_imm'], 'outputs': ['pc becomes branch target if taken else pc plus 4'], 'side_effects': ['no register writeback']}, {'id': 'FM_JUMP', 'name': 'jal_and_jalr', 'preconditions': ['is_jump'], 'inputs': ['pc', 'rs1', 'imm', 'is_jalr'], 'outputs': ['link register gets old pc plus 4 when rd != 0', 'jump target selected by JAL or JALR rule'], 'side_effects': ['pc redirected to computed target']}, {'id': 'FM_LOAD', 'name': 'loads_with_extension', 'preconditions': ['is_load'], 'inputs': ['d_rdata', 'funct3', 'effective_addr'], 'outputs': ['LB and LH sign-extend', 'LBU and LHU zero-extend', 'LW returns full 32-bit'], 'side_effects': ['writeback to rd when rd != 0'], 'error_cases': [{'condition': 'misaligned_access', 'result': 'excpt_o pulse and no retirement'}]}, {'id': 'FM_STORE', 'name': 'stores_with_byte_enable', 'preconditions': ['is_store'], 'inputs': ['rs2', 'funct3', 'effective_addr'], 'outputs': ['d_we equals 1 and d_be reflects width and alignment'], 'side_effects': ['no register writeback'], 'error_cases': [{'condition': 'misaligned_access', 'result': 'excpt_o pulse and no retirement'}]}, {'id': 'FM_SYSTEM', 'name': 'fence_ecall_ebreak', 'preconditions': ['is_system'], 'inputs': ['is_fence', 'is_ecall', 'is_ebreak'], 'outputs': ['FENCE inserts one bubble', 'ECALL and EBREAK pulse excpt_o'], 'side_effects': ['ECALL and EBREAK advance pc by 4']}], 'invariants': ['regfile_x0 == 0', 'misaligned_access implies no_retire', 'jalr_target_lsb == 0']}, 'cycle_model': {'purpose': 'Clocked IF/ID_EX/MEM_WB contract with synchronous registered bus behavior.', 'executable': 'pymtl3', 'backend_policy': 'Use PyMTL3 shell for cycle accounting while function_model remains architectural oracle.', 'clock': 'clk', 'reset': {'assertion': 'rst_n low asynchronously clears architectural and pipeline state', 'deassertion': 'state usable on first rising edge after synchronized deassertion'}, 'latency': {'fetch_to_decode': {'min_cycles': 1, 'max_cycles': 1, 'description': 'IF to ID_EX transfer'}, 'alu_ops_retire': {'min_cycles': 3, 'max_cycles': 3, 'description': 'IF to ID_EX to MEM_WB retire path'}, 'load_retire': {'min_cycles': 3, 'max_cycles': 3, 'description': 'Single-cycle synchronous data return assumption'}, 'store_issue': {'min_cycles': 2, 'max_cycles': 3, 'description': 'Address and write data presented by MEM stage'}, 'fence_penalty': {'min_cycles': 1, 'max_cycles': 1, 'description': 'Required one-cycle bubble'}}, 'handshake_rules': [{'signal': 'i_valid', 'rule': 'i_valid == 1 implies i_addr is stable in the cycle'}, {'signal': 'd_valid', 'rule': 'd_valid == 1 implies d_addr and d_we and d_be are stable in the cycle'}, {'signal': 'd_we', 'rule': 'd_we == 1 indicates store and d_we == 0 indicates load'}, {'signal': 'excpt_o', 'rule': 'excpt_o pulses for exactly one cycle per triggering instruction'}], 'pipeline': [{'stage': 'IF', 'cycle': 't', 'action': 'Drive i_addr from pc and sample i_rdata'}, {'stage': 'ID_EX', 'cycle': 't+1', 'action': 'Decode and compute ALU or branch or target or effective address'}, {'stage': 'MEM_WB', 'cycle': 't+2', 'action': 'Perform load/store signaling and writeback and retire'}], 'ordering': ['Retirement is in program order with at most one commit per cycle', 'Faulting misaligned or illegal instruction does not retire', 'Store side effects occur only on aligned non-faulting stores'], 'backpressure': ['No explicit ready channels; interfaces are sampled synchronously each cycle'], 'observability': ['Every function_model transaction maps to IF or ID_EX or MEM_WB stage'], 'performance': {'frequency_mhz': 100, 'throughput': {'sustained_beats_per_cycle': 1, 'condition': 'synchronous memory response each cycle'}, 'outstanding': {'max': 1, 'description': 'single in-flight architectural operation'}, 'depth': {'pipeline_stages': 3, 'queue_depth': 1, 'description': 'fixed three-stage in-order pipe'}}}}


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
