"""Cycle-accurate FL/CL model for arbiter_rr (PoC).

Per-cycle round-robin priority encoder that mirrors RTL's last_winner state.
cocotb drives RTL and this CL in lock-step, comparing outputs every cycle.

This is the canonical SSOT.cycle_model.pipeline.S0_SAMPLE_REQ + S1_GRANT
materialized as executable Python — what PyMTL3 CL Component would do, just
expressed plainly so the PoC isn't framework-coupled.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

NUM_REQ = 4
IDX_WIDTH = 2


def _rr_select(active: int, last_winner: int, n: int = NUM_REQ) -> int:
    """Round-robin priority encoder: pick lowest-priority-rotated set bit.

    Priority order starts from (last_winner + 1) mod N, wraps around.
    Returns the index of the chosen requestor, or -1 if active == 0.
    """
    if active == 0:
        return -1
    for offset in range(1, n + 1):
        idx = (last_winner + offset) % n
        if (active >> idx) & 1:
            return idx
    return -1


class ArbiterRR_CL:
    """Cycle-accurate model mirroring arbiter_rr_core.sv timing.

    Pipeline:
      S0 (combinational): sample req_i, apply mask, evaluate priority
      S1 (registered):    gnt_o / gnt_idx_o / gnt_valid_o / last_winner update
    """

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.last_winner: int = 0
        self.arb_enabled: int = 1
        self.req_mask: int = (1 << NUM_REQ) - 1
        # Registered outputs (S1).
        self.gnt_o: int = 0
        self.gnt_valid_o: int = 0
        self.gnt_idx_o: int = 0
        # Combinational shadow of next outputs (S0 evaluation result).
        self._next_gnt_o: int = 0
        self._next_gnt_valid_o: int = 0
        self._next_gnt_idx_o: int = 0
        self._next_last_winner: int = 0

    def csr_write(self, offset: int, data: int) -> None:
        """Apply an APB CSR write side-effect (one cycle delay vs RTL is
        modelled by the caller — write here, sample outputs next tick)."""
        if offset == 0x00:
            self.arb_enabled = data & 0x1
        elif offset == 0x04:
            self.req_mask = data & ((1 << NUM_REQ) - 1)

    def step(self, req_i: int) -> dict:
        """Advance one clock cycle.

        S0 (this call):   evaluate combinational arbitration from inputs.
        S1 (this call):   register outputs and last_winner update.
        Returns the registered outputs visible on the bus this cycle
        (matches what cocotb sees in rtl_observed after RisingEdge).
        """
        # S0 — combinational evaluation
        if self.arb_enabled:
            active = req_i & self.req_mask
            chosen = _rr_select(active, self.last_winner)
            if chosen >= 0:
                self._next_gnt_o = 1 << chosen
                self._next_gnt_valid_o = 1
                self._next_gnt_idx_o = chosen
                self._next_last_winner = chosen
            else:
                self._next_gnt_o = 0
                self._next_gnt_valid_o = 0
                self._next_gnt_idx_o = 0
                self._next_last_winner = self.last_winner
        else:
            self._next_gnt_o = 0
            self._next_gnt_valid_o = 0
            self._next_gnt_idx_o = 0
            self._next_last_winner = self.last_winner

        # S1 — register update
        self.gnt_o = self._next_gnt_o
        self.gnt_valid_o = self._next_gnt_valid_o
        self.gnt_idx_o = self._next_gnt_idx_o
        self.last_winner = self._next_last_winner

        return {
            "gnt_o": self.gnt_o,
            "gnt_valid_o": self.gnt_valid_o,
            "gnt_idx_o": self.gnt_idx_o,
            "last_winner": self.last_winner,
        }
