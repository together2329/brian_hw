#!/usr/bin/env python3
"""Executable SSOT functional model for counter8_cx1.

Generated from yaml/counter8_cx1.ssot.yaml.
This model is independent from RTL and is imported by cocotb scoreboards.
"""
from __future__ import annotations

from typing import Any

SSOT_MODEL = {
    "ip": "counter8_cx1",
    "parameters": {"WIDTH": 8},
    "function_model": {
        "state_variables": [
            {"name": "count_reg", "width": 8, "reset": 0}
        ],
        "transactions": [
            {
                "id": "TR_RESET",
                "name": "synchronous_reset",
                "required_fields": ["rst_n"],
                "preconditions": ["rst_n == 0"],
                "output_rules": [{"name": "count", "port": "count", "expr": "0", "width": 8}],
                "state_updates": [{"name": "count_reg", "expr": "0", "width": 8}],
            },
            {
                "id": "TR_COUNT",
                "name": "count_up_when_enabled",
                "required_fields": ["en"],
                "preconditions": ["rst_n == 1", "en == 1"],
                "output_rules": [{"name": "count", "port": "count", "expr": "(count_reg + 1) & 0xFF", "width": 8}],
                "state_updates": [{"name": "count_reg", "expr": "(count_reg + 1) & 0xFF", "width": 8}],
            },
            {
                "id": "TR_HOLD",
                "name": "hold_when_disabled",
                "required_fields": ["en"],
                "preconditions": ["rst_n == 1", "en == 0"],
                "output_rules": [{"name": "count", "port": "count", "expr": "count_reg", "width": 8}],
                "state_updates": [{"name": "count_reg", "expr": "count_reg", "width": 8}],
            },
        ],
    },
}


class FunctionalModel:
    """Behavioral oracle for counter8_cx1."""

    def __init__(self, params: dict[str, Any] | None = None) -> None:
        self.params = dict(SSOT_MODEL.get("parameters") or {})
        if params:
            self.params.update(params)
        self.state: dict[str, int] = {"count_reg": 0}
        self.trace: list[dict[str, Any]] = []

    def reset(self) -> None:
        self.state = {"count_reg": 0}
        self.trace.clear()

    def _transactions(self) -> list[dict[str, Any]]:
        fm = SSOT_MODEL.get("function_model") or {}
        return [tx for tx in fm.get("transactions") or [] if isinstance(tx, dict)]

    def apply(self, txn: dict[str, Any]) -> dict[str, Any]:
        """Apply one stimulus transaction, update state, return expected outputs."""
        kind = str(txn.get("kind") or txn.get("id") or "").strip().lower()
        rst_n = int(txn.get("rst_n", 1))
        en = int(txn.get("en", 0))
        count_reg = self.state["count_reg"]

        if rst_n == 0:
            next_count = 0
            tx_id = "TR_RESET"
        elif en == 1:
            next_count = (count_reg + 1) & 0xFF
            tx_id = "TR_COUNT"
        else:
            next_count = count_reg
            tx_id = "TR_HOLD"

        self.state["count_reg"] = next_count
        result = {
            "count": next_count,
            "transaction_id": tx_id,
            "state": dict(self.state),
        }
        self.trace.append({"kind": kind or tx_id, "txn": txn, "result": result})
        return result
