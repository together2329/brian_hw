#!/usr/bin/env python3
"""Executable SSOT functional model for watchdog_cx1.

Generated from yaml/watchdog_cx1.ssot.yaml.
This model is imported by cocotb scoreboards for FL-vs-RTL comparison.
"""
from __future__ import annotations

from typing import Any

SSOT_MODEL = {
    "ip": "watchdog_cx1",
    "parameters": {"COUNTER_WIDTH": 8},
    "function_model": {
        "state_variables": [
            {"name": "count_q",  "width": 8, "reset": 255},
            {"name": "period_q", "width": 8, "reset": 255},
            {"name": "enable_q", "width": 1, "reset": 1},
        ],
        "transactions": [
            {
                "id": "FM_KICK",
                "name": "watchdog_kick",
                "preconditions": ["psel == 1", "penable == 1", "pwrite == 1", "paddr == 4"],
                "output_rules": [
                    {"name": "timeout_pulse", "port": "timeout_pulse", "expr": "0", "width": 1},
                ],
                "state_updates": [
                    {"name": "count_q", "expr": "period_q", "width": 8},
                ],
            },
            {
                "id": "FM_TICK",
                "name": "counter_tick",
                "preconditions": ["enable_q == 1"],
                "output_rules": [
                    {"name": "timeout_pulse", "port": "timeout_pulse",
                     "expr": "1 if count_q == 1 else 0", "width": 1},
                ],
                "state_updates": [
                    {"name": "count_q",
                     "expr": "period_q if count_q == 1 else (count_q - 1) & 0xFF",
                     "width": 8},
                ],
            },
            {
                "id": "FM_IDLE",
                "name": "watchdog_idle",
                "preconditions": ["enable_q == 0"],
                "output_rules": [
                    {"name": "timeout_pulse", "port": "timeout_pulse", "expr": "0", "width": 1},
                ],
                "state_updates": [
                    {"name": "count_q", "expr": "count_q", "width": 8},
                ],
            },
        ],
    },
}


class FunctionalModel:
    """Behavioral oracle for watchdog_cx1."""

    def __init__(self, params: dict[str, Any] | None = None) -> None:
        self.params = dict(SSOT_MODEL.get("parameters") or {})
        if params:
            self.params.update(params)
        self.state: dict[str, int] = {
            "count_q":  255,
            "period_q": 255,
            "enable_q": 1,
        }
        self.trace: list[dict[str, Any]] = []

    def reset(self) -> None:
        self.state = {"count_q": 255, "period_q": 255, "enable_q": 1}
        self.trace.clear()

    def apply(self, txn: dict[str, Any]) -> dict[str, Any]:
        """Apply one stimulus cycle, update state, return expected outputs.

        txn keys: psel, penable, pwrite, paddr, pwdata, preset_n (optional)
        Returns: dict with timeout_pulse, transaction_id, state
        """
        psel    = int(txn.get("psel", 0))
        penable = int(txn.get("penable", 0))
        pwrite  = int(txn.get("pwrite", 0))
        paddr   = int(txn.get("paddr", 0))
        pwdata  = int(txn.get("pwdata", 0))

        count_q  = self.state["count_q"]
        period_q = self.state["period_q"]
        enable_q = self.state["enable_q"]

        is_kick   = (psel == 1 and penable == 1 and pwrite == 1 and paddr == 4)
        is_ctrl   = (psel == 1 and penable == 1 and pwrite == 1 and paddr == 0)
        is_period = (psel == 1 and penable == 1 and pwrite == 1 and paddr == 8)

        # Update CTRL/PERIOD registers first (combinational view)
        if is_ctrl:
            enable_q = pwdata & 1
        if is_period:
            period_q = pwdata & 0xFF

        # Determine outputs and state updates
        if is_kick:
            timeout_pulse = 0
            next_count = period_q
            tx_id = "FM_KICK"
        elif enable_q == 1:
            timeout_pulse = 1 if count_q == 1 else 0
            next_count = period_q if count_q == 1 else (count_q - 1) & 0xFF
            tx_id = "FM_TICK"
        else:
            timeout_pulse = 0
            next_count = count_q
            tx_id = "FM_IDLE"

        self.state["count_q"]  = next_count
        self.state["period_q"] = period_q
        self.state["enable_q"] = enable_q

        result = {
            "timeout_pulse":  timeout_pulse,
            "transaction_id": tx_id,
            "state":          dict(self.state),
        }
        self.trace.append({"txn": txn, "result": result})
        return result
