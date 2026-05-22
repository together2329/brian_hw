#!/usr/bin/env python3
"""Executable SSOT cycle model for quad_spi_ctrl.

Generated from yaml/quad_spi_ctrl.ssot.yaml cycle_model section.
Deterministic emit — NO LLM.
"""

from __future__ import annotations
import json

CLOCK = "PCLK"
RESET_SIGNAL = "PRESETn"
RESET_POLARITY = "active_low"
RESET_TYPE = "async_assert_sync_deassert"

PIPELINE = [
    {"stage": "S0_IDLE",     "description": "Wait for START with tx_fifo non-empty"},
    {"stage": "S1_CMD",      "description": "Shift out CMD byte from TX FIFO via IO lanes"},
    {"stage": "S2_ADDR",     "description": "Shift out ADDR_LEN address bytes"},
    {"stage": "S3_DATA",     "description": "Shift out DATA_LEN data bytes / receive data"},
    {"stage": "S4_WAIT_CS",  "description": "Hold CS_N idle for CS_IDLE.HOLD half-cycles"},
    {"stage": "S5_DONE",     "description": "Set STATUS.DONE, update FIFOs, deassert busy"},
]

HANDSHAKE_RULES = {
    "apb": "Transfer when PSEL and PENABLE and PREADY; PSLVERR valid in same transfer",
    "ctrl_start": "Sampled as pulse; auto-clears after acceptance",
    "launch_gate": "FSM leaves IDLE only when START and not busy and tx_fifo_not_empty",
    "sclk_o": "Half-period equals PRESCALE+1 PCLK cycles; CPOL controls idle level",
    "sample_edge": "CPHA selects first edge: 0=sample on first edge, 1=sample on second edge",
}

LATENCY = {
    "apb_read":        {"min_cycles": 0, "max_cycles": 1},
    "apb_write":       {"min_cycles": 0, "max_cycles": 1},
    "sclk_half_period": {"min_cycles": 1, "max_cycles": None,
                         "formula": "PRESCALE.DIV + 1"},
    "frame_total":     {"min_cycles": 2, "max_cycles": None,
                        "formula": "(1 + ADDR_LEN + DATA_LEN) * 8 / pins_per_lane * sclk_half_period"},
}

ORDERING = [
    "CMD byte always shifts first before ADDR bytes",
    "ADDR bytes shift before DATA bytes",
    "Final DATA shift precedes DONE event",
]

BACKPRESSURE = {
    "tx": "Writes to TXDATA dropped when tx_fifo full",
    "rx": "Received byte dropped when rx_fifo full at frame completion",
}

OBSERVABILITY_PROBES = [
    "fsm_state", "bit_count", "byte_count", "sclk_toggle",
    "cs_active", "tx_fifo_count", "rx_fifo_count", "irq_pending",
]


def run_self_check():
    """Validate internal consistency of cycle_model."""
    results = []
    errors = []

    # Check pipeline has all 6 stages
    stage_names = [s["stage"] for s in PIPELINE]
    expected = ["S0_IDLE", "S1_CMD", "S2_ADDR", "S3_DATA", "S4_WAIT_CS", "S5_DONE"]
    if stage_names != expected:
        errors.append(f"Pipeline stages mismatch: {stage_names} != {expected}")
    results.append({"check": "pipeline_stages", "passed": stage_names == expected})

    # Check handshake_rules has all required keys
    required_handshakes = {"apb", "ctrl_start", "launch_gate", "sclk_o", "sample_edge"}
    actual_handshakes = set(HANDSHAKE_RULES.keys())
    results.append({"check": "handshake_rules", "passed": required_handshakes == actual_handshakes})

    # Check latency has all entries
    required_latency = {"apb_read", "apb_write", "sclk_half_period", "frame_total"}
    actual_latency = set(LATENCY.keys())
    results.append({"check": "latency_entries", "passed": required_latency == actual_latency})

    # Check backpressure has tx and rx
    results.append({"check": "backpressure_entries", "passed": set(BACKPRESSURE.keys()) == {"tx", "rx"}})

    # Check probes non-empty
    results.append({"check": "observability_probes", "passed": len(OBSERVABILITY_PROBES) >= 6})

    passed = all(r["passed"] for r in results)
    return {
        "passed": passed,
        "checks": len(results),
        "failed": sum(1 for r in results if not r["passed"]),
        "results": results,
        "errors": errors,
    }


def coverage_seed_bins():
    """Return cycle coverage bins seeded as not-yet-hit."""
    bins = []
    for stage in PIPELINE:
        bins.append({"id": f"CCOV_{stage['stage']}", "class": "pipeline_stage",
                       "coverage_domain": "cycle", "source_ref": stage["stage"],
                       "description": stage["description"]})
    for name in HANDSHAKE_RULES:
        bins.append({"id": f"CCOV_HS_{name}", "class": "handshake",
                       "coverage_domain": "cycle", "source_ref": name,
                       "description": HANDSHAKE_RULES[name][:60]})
    for rule in ORDERING:
        short = rule[:60]
        bins.append({"id": f"CCOV_ORDERING_{hash(short) & 0xFFFF:04x}",
                       "class": "ordering", "coverage_domain": "cycle",
                       "source_ref": "ordering", "description": short})
    return {b["id"]: False for b in bins}


if __name__ == "__main__":
    check_result = run_self_check()
    print(json.dumps(check_result, indent=2))
    bins = coverage_seed_bins()
    print(f"\nCoverage bins: {len(bins)}")
