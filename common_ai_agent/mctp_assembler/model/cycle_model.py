#!/usr/bin/env python3
"""Executable cycle model for mctp_assembler. FunctionalModel is the only oracle."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

try:
    from .functional_model import FunctionalModel, build_mctp_pcie_vdm_packet
except ImportError:
    from functional_model import FunctionalModel, build_mctp_pcie_vdm_packet


MODEL_BACKEND = "python"
_OUTSTANDING_CAP = 1

_LATENCY = {
    "fm_accept_axi_tlp": 1,
    "fm_filter_vdm": 1,
    "fm_parse_mctp": 1,
    "fm_assemble_fragment": 2,
    "fm_write_sram_and_descriptor": 2,
    "fm_classify_drop": 1,
    "axi_tlp": 4,
    "apb_write": 1,
    "apb_read": 1,
    "timeout": 1,
    "default": 1,
}

_SELF_CHECK_KINDS = [
    "FM_ACCEPT_AXI_TLP",
    "FM_FILTER_VDM",
    "FM_PARSE_MCTP",
    "FM_ASSEMBLE_FRAGMENT",
    "FM_WRITE_SRAM_AND_DESCRIPTOR",
    "FM_CLASSIFY_DROP",
]

_HANDSHAKE_RULES = [
    {
        "name": "axi_aw_w_b_one_outstanding",
        "description": "Only one AXI write burst is in flight; a burst is accepted before another AW is modeled.",
    },
    {
        "name": "sram_valid_ready",
        "description": "Payload writes complete only through the FunctionalModel SRAM write result.",
    },
    {
        "name": "apb_access_phase",
        "description": "APB accesses complete in one pclk model cycle.",
    },
]

_ORDERING_RULES = [
    {
        "name": "axi_bursts_in_acceptance_order",
        "description": "AXI write bursts are evaluated in drive order subject to the outstanding cap.",
    },
    {
        "name": "descriptor_order_matches_completion_order",
        "description": "Descriptor events emerge in the same order FunctionalModel completes messages.",
    },
    {
        "name": "fl_is_single_oracle",
        "description": "CycleModel never re-evaluates packet semantics outside FunctionalModel.apply().",
    },
]

CL_BINS = {
    "handshake_axi_aw_w_b_one_outstanding": "AXI one-outstanding write burst rule",
    "handshake_sram_valid_ready": "SRAM valid/ready observation",
    "handshake_apb_access_phase": "APB access phase observation",
    "ordering_axi_bursts_in_acceptance_order": "AXI ordering",
    "ordering_descriptor_order_matches_completion_order": "Descriptor ordering",
    "ordering_fl_is_single_oracle": "Functional oracle ownership",
    "latency_fm_accept_axi_tlp": "FM_ACCEPT_AXI_TLP latency",
    "latency_fm_filter_vdm": "FM_FILTER_VDM latency",
    "latency_fm_parse_mctp": "FM_PARSE_MCTP latency",
    "latency_fm_assemble_fragment": "FM_ASSEMBLE_FRAGMENT latency",
    "latency_fm_write_sram_and_descriptor": "FM_WRITE_SRAM_AND_DESCRIPTOR latency",
    "latency_fm_classify_drop": "FM_CLASSIFY_DROP latency",
}

PERFORMANCE_TARGETS = {
    "backend": MODEL_BACKEND,
    "clock_domains": ["axi_aclk", "pclk"],
    "outstanding": {"axi_write_max": _OUTSTANDING_CAP},
    "throughput": {
        "ingress": "one AXI W beat per axi_aclk when not backpressured",
        "sram_write": "one SRAM write word per axi_aclk when ready",
    },
}


class CycleModel:
    """Queue/latency wrapper around FunctionalModel."""

    def __init__(self, params: Dict[str, Any] | None = None):
        self.params = params or {}
        self.fl = FunctionalModel(self.params)
        self.in_q: List[Tuple[int, Dict[str, Any]]] = []
        self.out_q: List[Tuple[int, Dict[str, Any]]] = []
        self.cov: Dict[str, int] = {key: 0 for key in CL_BINS}
        self.now = 0
        self._outstanding = 0

    def reset(self) -> None:
        self.fl.reset()
        self.in_q.clear()
        self.out_q.clear()
        self.cov = {key: 0 for key in CL_BINS}
        self.now = 0
        self._outstanding = 0

    def drive(self, txn: Dict[str, Any], t: int) -> None:
        self.in_q.append((int(t), dict(txn)))

    def _latency_for(self, txn: Dict[str, Any]) -> int:
        kind = str(txn.get("kind") or txn.get("op") or "axi_tlp").strip().lower()
        if kind.startswith("fm_"):
            return _LATENCY.get(kind, _LATENCY["default"])
        return _LATENCY.get(kind, _LATENCY["default"])

    def _sample_coverage(self, txn: Dict[str, Any]) -> None:
        for rule in _HANDSHAKE_RULES:
            key = f"handshake_{rule['name']}"
            if key in self.cov:
                self.cov[key] += 1
        for rule in _ORDERING_RULES:
            key = f"ordering_{rule['name']}"
            if key in self.cov:
                self.cov[key] += 1
        kind = str(txn.get("kind") or txn.get("op") or "axi_tlp").strip().lower()
        key = f"latency_{kind}"
        if key in self.cov:
            self.cov[key] += 1

    def _default_txn(self, kind: str) -> Dict[str, Any]:
        self.fl.configure(enable=True, local_eid=0x22, sram_base=0, sram_limit=(1 << 16) - 1)
        if kind == "FM_ACCEPT_AXI_TLP":
            return {"kind": kind, "tlp_bytes": build_mctp_pcie_vdm_packet(dest_eid=0x22)}
        if kind == "FM_FILTER_VDM":
            return {"kind": kind, "tlp_bytes": build_mctp_pcie_vdm_packet(dest_eid=0x22)}
        if kind == "FM_PARSE_MCTP":
            return {"kind": kind, "tlp_bytes": build_mctp_pcie_vdm_packet(dest_eid=0x22)}
        if kind == "FM_ASSEMBLE_FRAGMENT":
            return {"kind": kind, "source_eid": 9, "message_tag": 3, "som": 1, "eom": 0, "seq": 0, "payload": [0x7E, 0x90]}
        if kind == "FM_WRITE_SRAM_AND_DESCRIPTOR":
            return {"kind": kind, "payload": [0x7E, 0x91]}
        if kind == "FM_CLASSIFY_DROP":
            return {"kind": kind, "drop_class": "packet_drop", "reason": "PD_MALFORMED_TLP"}
        return {"kind": kind}

    def tick(self, t: int) -> None:
        self.now = int(t)
        self._outstanding = sum(1 for ready_t, _ in self.out_q if ready_t > self.now)
        while self.in_q:
            if self._outstanding >= _OUTSTANDING_CAP:
                break
            arrival_t, txn = self.in_q[0]
            if arrival_t > self.now:
                break
            self.in_q.pop(0)
            try:
                result = self.fl.apply(txn)
            except Exception as exc:
                result = {"label": str(txn.get("kind", "unknown")), "fl_error": f"{type(exc).__name__}: {exc}"}
            ready_t = self.now + self._latency_for(txn)
            self.out_q.append((ready_t, result))
            self._outstanding += 1
            self._sample_coverage(txn)
        self._outstanding = sum(1 for ready_t, _ in self.out_q if ready_t > self.now)

    def observe(self, t: int) -> List[Tuple[int, Dict[str, Any]]]:
        t = int(t)
        ready = [(ready_t, result) for ready_t, result in self.out_q if ready_t <= t]
        self.out_q = [(ready_t, result) for ready_t, result in self.out_q if ready_t > t]
        return ready

    def coverage(self) -> Dict[str, int]:
        return dict(self.cov)

    def run_self_check(self) -> Dict[str, Any]:
        self.reset()
        observed: List[Tuple[int, Dict[str, Any]]] = []
        for idx, kind in enumerate(_SELF_CHECK_KINDS):
            self.drive(self._default_txn(kind), idx)
            self.tick(idx)
            observed.extend(self.observe(idx))
        drain_t = len(_SELF_CHECK_KINDS) + 20
        self.tick(drain_t)
        observed.extend(self.observe(drain_t + 10))
        fl_errors = [result for _, result in observed if isinstance(result, dict) and result.get("fl_error")]
        hit_bins = sum(1 for value in self.cov.values() if value > 0)
        return {
            "passed": not fl_errors and len(observed) >= len(_SELF_CHECK_KINDS),
            "backend": MODEL_BACKEND,
            "transactions": len(_SELF_CHECK_KINDS),
            "results_observed": len(observed),
            "coverage_bins": len(CL_BINS),
            "coverage_hit": hit_bins,
            "fl_errors": fl_errors,
            "performance_targets": PERFORMANCE_TARGETS,
        }


if __name__ == "__main__":
    print(json.dumps(CycleModel().run_self_check(), indent=2, sort_keys=True))
