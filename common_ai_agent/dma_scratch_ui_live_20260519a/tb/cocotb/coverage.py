"""Functional coverage collector driven by SSOT coverage_goals and fcov_plan.

SSOT traceability:
  - test_requirements.coverage_goals → functional and cycle bins
  - cov/fcov_plan.json              → bin definitions
  - function_model.transactions     → transaction-type bins
  - cycle_model                     → handshake / pipeline / ordering bins
"""

import json
from collections import OrderedDict
from pathlib import Path


# ── Default bin set mirrors SSOT coverage_goals ───────────────────────
DEFAULT_BINS = OrderedDict([
    # Scenario execution bins
    ("SC01_executed",         "Scenario SC01: reset_defaults"),
    ("SC02_executed",         "Scenario SC02: csr_programming_readback"),
    ("SC03_executed",         "Scenario SC03: illegal_csr_access"),
    ("SC04_executed",         "Scenario SC04: zero_length_transfer"),
    ("SC05_executed",         "Scenario SC05: single_beat_copy"),
    ("SC06_executed",         "Scenario SC06: multi_beat_copy"),
    ("SC07_executed",         "Scenario SC07: partial_final_beat"),
    ("SC08_executed",         "Scenario SC08: read_backpressure"),
    ("SC09_executed",         "Scenario SC09: write_backpressure"),
    ("SC10_executed",         "Scenario SC10: soft_reset_abort"),
    ("SC11_executed",         "Scenario SC11: status_w1c_irq_clear"),

    # Transaction-type bins
    ("function_reset",                "FM_RESET transaction"),
    ("function_csr_write_config",     "FM_CSR_WRITE_CONFIG transaction"),
    ("function_start_transfer",       "FM_START_TRANSFER transaction"),
    ("function_csr_read_status",      "FM_CSR_READ_STATUS transaction"),
    ("function_memory_read_request",  "FM_READ_REQUEST transaction"),
    ("function_capture_read_data",    "FM_CAPTURE_READ_DATA transaction"),
    ("function_memory_write_request", "FM_WRITE_REQUEST transaction"),
    ("function_memory_write_accept",  "FM_WRITE_ACCEPT transaction"),
    ("function_clear_or_abort",       "FM_CLEAR_ABORT transaction"),
    ("function_illegal_csr_or_start", "FM_ILLEGAL_CSR_OR_START transaction"),

    # Error path bins
    ("fcov_error",   "Illegal CSR and start-while-busy errors observed"),
    ("fcov_strobe",  "Full and partial write strobes observed"),

    # Handshake bins
    ("ccov_handshakes",   "CSR, read address, read data, and write handshakes observed"),
    ("ccov_pipeline",     "All declared pipeline stages observed"),
    ("ccov_backpressure", "Read and write stall cases observed"),
])


class FunctionalCoverage:
    """SSOT-driven functional coverage collector.

    Bins are flat for simplicity; a future pass can add cross-coverage.
    """

    def __init__(self, bin_map=None):
        if bin_map is None:
            bin_map = dict(DEFAULT_BINS)
        self._bin_map = dict(bin_map)
        self._hits = {bid: False for bid in self._bin_map}

    def hit(self, bin_id: str):
        """Mark a bin as hit."""
        if bin_id in self._hits:
            self._hits[bin_id] = True

    def hit_many(self, bin_ids):
        """Mark multiple bins as hit."""
        for bid in bin_ids:
            self.hit(bid)

    def is_hit(self, bin_id: str) -> bool:
        return self._hits.get(bin_id, False)

    def coverage_pct(self) -> float:
        total = len(self._hits)
        if total == 0:
            return 100.0
        hit_count = sum(1 for v in self._hits.values() if v)
        return 100.0 * hit_count / total

    def missing_bins(self):
        return sorted(bid for bid, hit in self._hits.items() if not hit)

    def summary(self) -> dict:
        return {
            "total_bins": len(self._hits),
            "hit_bins": sum(1 for v in self._hits.values() if v),
            "coverage_pct": round(self.coverage_pct(), 1),
            "missing": self.missing_bins(),
        }

    def export_json(self, path: str):
        data = {
            "coverage_pct": round(self.coverage_pct(), 1),
            "total_bins": len(self._hits),
            "hit_bins": sum(1 for v in self._hits.values() if v),
            "bins": {bid: {"hit": hit, "desc": self._bin_map.get(bid, "")}
                     for bid, hit in self._hits.items()},
        }
        Path(path).write_text(json.dumps(data, indent=2))
