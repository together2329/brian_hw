"""Counter transaction / sequence item for UVM-style cocotb testbench."""

from dataclasses import dataclass, field
from typing import Optional
import random


@dataclass
class CounterTxn:
    """Represents a single counter operation.

    Attributes:
        en:      Count enable (1=active).
        load:    Parallel load enable (overrides count when 1).
        up_down: Direction — 0=up, 1=down.
        data_in: Parallel load data value.
    """
    en:      int = 0
    load:    int = 0
    up_down: int = 0
    data_in: int = 0

    def randomize(self, width: int = 8) -> "CounterTxn":
        """Fill with constrained random values for the given counter WIDTH."""
        self.en      = random.randint(0, 1)
        self.load    = random.randint(0, 1)
        self.up_down = random.randint(0, 1)
        self.data_in = random.randint(0, (1 << width) - 1)
        return self

    def __repr__(self) -> str:
        return (f"CounterTxn(en={self.en}, load={self.load}, "
                f"up_down={self.up_down}, data_in={self.data_in})")


@dataclass
class CounterOutput:
    """Represents counter outputs sampled in a single cycle.

    Attributes:
        count_out: Current count value.
        overflow:  Overflow/underflow pulse (1 cycle).
    """
    count_out: int = 0
    overflow:  int = 0

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CounterOutput):
            return NotImplemented
        return self.count_out == other.count_out and self.overflow == other.overflow

    def __repr__(self) -> str:
        return f"CounterOutput(count_out={self.count_out}, overflow={self.overflow})"
