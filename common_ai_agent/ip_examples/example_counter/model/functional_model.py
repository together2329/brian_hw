"""Functional Model for example_counter — 4-bit up-counter with sync reset, enable, load, overflow."""

from typing import Dict, Any


class ExampleCounterFM:
    """Golden reference model for example_counter.
    
    Implements the SSOT function_model contract:
    - state: count (WIDTH bits)
    - transactions: FM_COUNT_UP, FM_LOAD, FM_HOLD, FM_RESET
    - invariants: count in [0, 2^WIDTH-1], overflow on MAX->0 wrap
    """

    def __init__(self, width: int = 4):
        self.width = width
        self.mask = (1 << width) - 1
        self.max_val = self.mask
        self.count = 0
        self.overflow = 0

    def reset(self):
        """FM_RESET: synchronous reset clears count and overflow."""
        self.count = 0
        self.overflow = 0

    def step(self, rst_n: int, en: int, load: int, data_in: int) -> Dict[str, int]:
        """Advance one clock cycle.
        
        Priority: load > en > hold.
        Returns dict with 'count' and 'overflow' after the step.
        """
        # Detect overflow BEFORE update (combinational from current state)
        overflow_det = 1 if (self.count == self.max_val and en and not load) else 0

        if not rst_n:
            # Synchronous reset
            self.count = 0
            self.overflow = 0
        elif load:
            # FM_LOAD: parallel load
            self.count = data_in & self.mask
            self.overflow = 0
        elif en:
            # FM_COUNT_UP: increment
            self.count = (self.count + 1) & self.mask
            self.overflow = overflow_det
        else:
            # FM_HOLD: hold
            self.overflow = 0

        return {"count": self.count, "overflow": self.overflow}

    def get_state(self) -> Dict[str, Any]:
        return {"count": self.count, "overflow": self.overflow}
