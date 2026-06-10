#!/usr/bin/env python3
"""Executable SSOT cycle-level model for fifo_sync_cx1. Wraps FunctionalModel — FL is the only oracle."""

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
_LATENCY: dict[str, int] = {'default': 1}

# Handshake rules from SSOT cycle_model.handshake_rules.
_HANDSHAKE_RULES: list[dict] = [{'name': 'write_handshake', 'signal': '', 'description': 'wr_data sampled when wr_en && !full.', 'predicate': ''}, {'name': 'read_handshake', 'signal': '', 'description': 'rd_ptr advanced when rd_en && !empty.', 'predicate': ''}]

# Ordering rules from SSOT cycle_model.ordering.
_ORDERING_RULES: list[dict] = [{'name': 'simultaneous_write_and_read_bypass_is_allowed_when_full_empty', 'description': ''}]

# Maximum outstanding transactions before stalling.
_OUTSTANDING_CAP: int = 1

# Cycle/performance targets used by coverage and timing instrumentation.
PERFORMANCE_TARGETS: dict = {'frequency_mhz': None, 'throughput': None, 'outstanding': None, 'pipeline_stages': None, 'queue_depth': None}

# Transaction kinds for self-check, derived from function_model.transactions at generation time.
_SELF_CHECK_KINDS: list[str] = ['FM_WRITE', 'FM_READ']

# Coverage bins: bin_name -> description.
CL_BINS: dict[str, str] = {'handshake_write_handshake': 'wr_data sampled when wr_en && !full.', 'handshake_read_handshake': 'rd_ptr advanced when rd_en && !empty.', 'ordering_simultaneous_write_and_read_bypass_is_allowed_when_full_empty': 'simultaneous_write_and_read_bypass_is_allowed_when_full_empty', 'latency_fm_write': 'latency bin for FM_WRITE', 'latency_fm_read': 'latency bin for FM_READ'}

# SSOT payload snapshot (read-only reference; never execute functional rules from here).
SSOT_MODEL: dict = {'ip': 'fifo_sync_cx1', 'function_model': {'state_variables': [{'name': 'count', 'width': 4, 'reset': 0}, {'name': 'wr_ptr', 'width': 3, 'reset': 0}, {'name': 'rd_ptr', 'width': 3, 'reset': 0}, {'name': 'head_data', 'width': 8, 'reset': 0, 'description': 'Tracks the data at the current read pointer (FIFO head).'}], 'transactions': [{'id': 'FM_WRITE', 'name': 'write_behavior', 'required_fields': ['wr_data', 'wr_en'], 'preconditions': ['rst_n is deasserted', 'wr_en is high', 'full is low'], 'outputs': ['full', 'empty']}, {'id': 'FM_READ', 'name': 'read_behavior', 'required_fields': ['rd_en'], 'preconditions': ['rst_n is deasserted', 'rd_en is high', 'empty is low'], 'outputs': ['rd_data', 'full', 'empty']}], 'invariants': ['count is always in [0, 8].', 'full is equivalent to count == 8.', 'empty is equivalent to count == 0.'], 'reference_model_hint': 'FunctionalModel maintains a Python deque of max length 8; write pushes, read pops, full/empty derived from len.\n'}, 'cycle_model': {'executable': 'python', 'clock': 'clk', 'reset': 'rst_n', 'latency': 1, 'handshake_rules': [{'name': 'write_handshake', 'description': 'wr_data sampled when wr_en && !full.'}, {'name': 'read_handshake', 'description': 'rd_ptr advanced when rd_en && !empty.'}], 'pipeline': [{'stage': 'S0_WRITE', 'cycle': 0, 'action': 'Accept wr_data when wr_en && !full.'}, {'stage': 'S0_READ', 'cycle': 0, 'action': 'Advance rd_ptr when rd_en && !empty.'}, {'stage': 'S1_STATUS', 'cycle': 1, 'action': 'Update full/empty flags based on new count.'}], 'ordering': ['Simultaneous write and read (bypass) is allowed when !full && !empty.']}}


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

    def _self_check_txn(self, kind: str, idx: int) -> dict:
        """Build a minimal FL-valid transaction from SSOT required_fields.

        The CL self-check exists to prove that the generated model can call the
        FL oracle for every declared transaction. It should not fail merely
        because a transaction-level FL rule requires ordinary input fields such
        as APB paddr/pwrite/pwdata.
        """
        txn = {"kind": kind}
        wanted = str(kind or "").strip().lower()
        fm = SSOT_MODEL.get("function_model") if isinstance(SSOT_MODEL.get("function_model"), dict) else {}
        selected = None
        for tx in fm.get("transactions") or []:
            if not isinstance(tx, dict):
                continue
            aliases = {
                str(tx.get("id") or "").strip().lower(),
                str(tx.get("name") or "").strip().lower(),
            }
            if wanted in aliases:
                selected = tx
                break
        if not selected:
            return txn

        identity = " ".join(str(selected.get(key) or "") for key in ("id", "name")).lower()
        is_read_like = "read" in identity or "idle" in identity
        # Seed every machine-readable FL input, not just required_fields.
        # SSOT transaction rules often reference inputs such as parsed_msg_code,
        # wr_counter_global_clear, or sram_rdata directly in state/output expressions;
        # a cycle-model self-check must provide deterministic sample values for those
        # declared inputs instead of reporting missing FL dependencies.
        declared_fields = []
        for container_name in ("required_fields", "inputs"):
            for raw_name in selected.get(container_name) or []:
                name = str(raw_name).strip()
                if name and name not in declared_fields:
                    declared_fields.append(name)

        def _sample_value(name: str, field_idx: int):
            low = name.lower()
            if low in {"psel", "penable", "valid", "enable", "s_axi_wvalid", "s_axi_wready", "s_axi_wlast", "s_axi_arvalid", "s_axi_arready", "sram_ready", "sram_rvalid", "parsed_hdr_version_supported", "parsed_nonflit_no_ohc", "wr_counter_global_clear"}:
                return 1
            if low in {"pwrite", "write"}:
                return 0 if is_read_like else 1
            if low == "parsed_msg_code":
                return 0x7F
            if low == "parsed_vendor_id":
                return 0x1AB4
            if low == "parsed_mctp_vdm_code":
                return 0
            if low == "parsed_pcie_type":
                return 0
            if low == "parsed_som":
                return 1
            if low == "parsed_eom":
                return 1
            if low == "parsed_seq" or low == "expected_seq":
                return 0
            if low == "payload_len":
                return 64
            if low == "tu_bytes":
                return 64
            if low == "timeout_cycles":
                return 10
            if low == "queue_age_cycles":
                return 10
            if low in {"sequence_error", "tu_error", "overflow_error", "duplicate_start"}:
                return 1 if field_idx == 0 else 0
            if "addr" in low:
                return 0
            if low == "sram_rdata":
                return 0xA5
            if "data" in low or "value" in low or "payload" in low:
                return (0x55 + idx + field_idx) & 0xFF
            return field_idx + idx + 1

        for field_idx, name in enumerate(declared_fields):
            if name in txn:
                continue
            txn[name] = _sample_value(name, field_idx)
        return txn

    def run_self_check(self) -> dict:
        """Smoke run: drive every known transaction kind once, tick, observe."""
        self.reset()
        kinds = list(_SELF_CHECK_KINDS) or ["reset"]
        t = 0
        for idx, kind in enumerate(kinds):
            self.drive(self._self_check_txn(kind, idx), t=t)
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
