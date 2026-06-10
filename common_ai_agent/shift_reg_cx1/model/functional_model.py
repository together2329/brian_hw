#!/usr/bin/env python3
"""Executable SSOT functional model for shift_reg_cx1.

Generated from yaml/shift_reg_cx1.ssot.yaml.
This model is independent from RTL and is imported by cocotb scoreboards.
"""
from __future__ import annotations

from typing import Any

SSOT_MODEL = {
    "ip": "shift_reg_cx1",
    "parameters": {"WIDTH": 8},
    "function_model": {
        "state_variables": [
            {"name": "shift_reg", "width": 8, "reset": 0}
        ],
        "transactions": [
            {
                "id": "TR_RESET",
                "name": "synchronous_reset",
                "required_fields": ["rst_n"],
                "preconditions": ["rst_n == 0"],
                "output_rules": [{"name": "po", "port": "po", "expr": "0", "width": 8}],
                "state_updates": [{"name": "shift_reg", "expr": "0", "width": 8}],
            },
            {
                "id": "TR_SHIFT",
                "name": "shift_in_serial_bit",
                "required_fields": ["si"],
                "preconditions": ["rst_n == 1"],
                "output_rules": [
                    {"name": "po", "port": "po", "expr": "((shift_reg << 1) | (si & 1)) & 0xFF", "width": 8}
                ],
                "state_updates": [
                    {"name": "shift_reg", "expr": "((shift_reg << 1) | (si & 1)) & 0xFF", "width": 8}
                ],
            },
        ],
    },
}


class FunctionalModel:
    """Behavioral oracle for shift_reg_cx1."""

    def __init__(self, params: dict[str, Any] | None = None) -> None:
        self.params = dict(SSOT_MODEL.get("parameters") or {})
        if params:
            self.params.update(params)
        self.state: dict[str, int] = {"shift_reg": 0}
        self.trace: list[dict[str, Any]] = []

    def reset(self) -> None:
        self.state = {"shift_reg": 0}
        self.trace.clear()

    def _transactions(self) -> list[dict[str, Any]]:
        fm = SSOT_MODEL.get("function_model") or {}
        return [tx for tx in fm.get("transactions") or [] if isinstance(tx, dict)]

    def apply(self, txn: dict[str, Any]) -> dict[str, Any]:
        """Apply one stimulus transaction, update state, return expected outputs."""
        kind = str(txn.get("kind") or txn.get("id") or "").strip().lower()
        rst_n = int(txn.get("rst_n", 1))
        si = int(txn.get("si", 0)) & 1
        shift_reg = self.state["shift_reg"]

        if rst_n == 0:
            next_po = 0
            tx_id = "TR_RESET"
        else:
            next_po = ((shift_reg << 1) | si) & 0xFF
            tx_id = "TR_SHIFT"

        self.state["shift_reg"] = next_po
        result = {
            "po": next_po,
            "transaction_id": tx_id,
            "state": dict(self.state),
        }
        self.trace.append({"kind": kind or tx_id, "txn": txn, "result": result})
        return result
