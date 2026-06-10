#!/usr/bin/env python3
"""Executable SSOT functional model for uart_tx_lite_cx1.

Generated from yaml/uart_tx_lite_cx1.ssot.yaml.
This model is imported by cocotb scoreboards for FL-vs-RTL comparison.

Note: The FL model tracks frame-level behaviour (byte written, busy signal,
tx_out at each baud period). The scoreboard checks tx_busy and frame shape.
"""
from __future__ import annotations

from typing import Any

SSOT_MODEL = {
    "ip": "uart_tx_lite_cx1",
    "parameters": {"BAUD_DIV": 434},
    "function_model": {
        "state_variables": [
            {"name": "tx_busy_q", "width": 1, "reset": 0},
            {"name": "shift_reg", "width": 8, "reset": 0},
            {"name": "tx_state",  "width": 2, "reset": 0},  # 0=IDLE,1=START,2=DATA,3=STOP
        ],
        "transactions": [
            {
                "id": "FM_TX_BYTE",
                "name": "uart_tx_byte",
                "preconditions": ["psel==1", "penable==1", "pwrite==1", "paddr==0", "tx_busy_q==0"],
                "output_rules": [
                    {"name": "tx_busy", "port": "tx_busy", "expr": "1", "width": 1},
                    {"name": "tx_out",  "port": "tx_out",  "expr": "1", "width": 1},
                ],
                "state_updates": [
                    {"name": "tx_busy_q", "expr": "1", "width": 1},
                    {"name": "shift_reg", "expr": "pwdata & 0xFF", "width": 8},
                    {"name": "tx_state",  "expr": "1", "width": 2},
                ],
            },
            {
                "id": "FM_IDLE",
                "name": "uart_tx_idle",
                "preconditions": ["tx_busy_q == 0"],
                "output_rules": [
                    {"name": "tx_busy", "port": "tx_busy", "expr": "0", "width": 1},
                    {"name": "tx_out",  "port": "tx_out",  "expr": "1", "width": 1},
                ],
                "state_updates": [
                    {"name": "tx_busy_q", "expr": "0", "width": 1},
                ],
            },
        ],
    },
}


class FunctionalModel:
    """Behavioral oracle for uart_tx_lite_cx1.

    Tracks tx_busy and the expected 8N1 bit sequence at the baud level.
    """

    TX_IDLE  = 0
    TX_START = 1
    TX_DATA  = 2
    TX_STOP  = 3

    def __init__(self, params: dict[str, Any] | None = None) -> None:
        self.params = dict(SSOT_MODEL.get("parameters") or {})
        if params:
            self.params.update(params)
        self.baud_div: int = int(self.params.get("BAUD_DIV", 434))
        self.state: dict[str, int] = {
            "tx_busy_q": 0,
            "shift_reg": 0,
            "tx_state":  self.TX_IDLE,
            "bit_cnt":   0,
            "baud_cnt":  0,
        }
        self.trace: list[dict[str, Any]] = []

    def reset(self) -> None:
        self.state = {
            "tx_busy_q": 0,
            "shift_reg": 0,
            "tx_state":  self.TX_IDLE,
            "bit_cnt":   0,
            "baud_cnt":  0,
        }
        self.trace.clear()

    def apply(self, txn: dict[str, Any]) -> dict[str, Any]:
        """Apply one PCLK cycle stimulus, return expected outputs.

        txn keys: psel, penable, pwrite, paddr, pwdata
        Returns: dict with tx_busy, tx_out, transaction_id, state
        """
        psel    = int(txn.get("psel", 0))
        penable = int(txn.get("penable", 0))
        pwrite  = int(txn.get("pwrite", 0))
        paddr   = int(txn.get("paddr", 0))
        pwdata  = int(txn.get("pwdata", 0))

        tx_state  = self.state["tx_state"]
        tx_busy_q = self.state["tx_busy_q"]
        shift_reg = self.state["shift_reg"]
        bit_cnt   = self.state["bit_cnt"]
        baud_cnt  = self.state["baud_cnt"]

        is_tx_write = (psel == 1 and penable == 1 and pwrite == 1 and
                       paddr == 0 and tx_busy_q == 0)
        baud_tick = (tx_state != self.TX_IDLE and
                     baud_cnt == self.baud_div - 1)

        # Default outputs
        tx_out  = 1
        tx_busy = tx_busy_q
        tx_id   = "FM_IDLE"

        if tx_state == self.TX_IDLE:
            tx_out  = 1
            tx_busy = 0
            if is_tx_write:
                shift_reg = pwdata & 0xFF
                tx_state  = self.TX_START
                tx_busy   = 1
                bit_cnt   = 0
                baud_cnt  = 0
                tx_id     = "FM_TX_BYTE"
        elif tx_state == self.TX_START:
            tx_out  = 0
            tx_busy = 1
            tx_id   = "FM_TX_BYTE"
            if baud_tick:
                tx_state = self.TX_DATA
                bit_cnt  = 0
                baud_cnt = 0
            else:
                baud_cnt = (baud_cnt + 1) % self.baud_div
        elif tx_state == self.TX_DATA:
            tx_out  = (shift_reg >> bit_cnt) & 1
            tx_busy = 1
            tx_id   = "FM_TX_BYTE"
            if baud_tick:
                if bit_cnt == 7:
                    tx_state = self.TX_STOP
                    bit_cnt  = 0
                else:
                    bit_cnt += 1
                baud_cnt = 0
            else:
                baud_cnt = (baud_cnt + 1) % self.baud_div
        elif tx_state == self.TX_STOP:
            tx_out  = 1
            tx_busy = 1
            tx_id   = "FM_TX_BYTE"
            if baud_tick:
                tx_state  = self.TX_IDLE
                tx_busy   = 0
                baud_cnt  = 0
            else:
                baud_cnt = (baud_cnt + 1) % self.baud_div

        self.state["tx_state"]  = tx_state
        self.state["tx_busy_q"] = tx_busy
        self.state["shift_reg"] = shift_reg
        self.state["bit_cnt"]   = bit_cnt
        self.state["baud_cnt"]  = baud_cnt

        result = {
            "tx_busy":        tx_busy,
            "tx_out":         tx_out,
            "transaction_id": tx_id,
            "state":          dict(self.state),
        }
        self.trace.append({"txn": txn, "result": result})
        return result
