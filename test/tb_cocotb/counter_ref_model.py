"""Reference model for the parameterized up/down counter.

Mirrors the RTL priority: rst_n → load → en → hold.
Maintains golden count and overflow state in Python.
"""

from counter_txn import CounterTxn, CounterOutput


class CounterRefModel:
    """Golden reference model matching counter.v RTL behavior.

    Usage:
        model = CounterRefModel(width=8)
        model.reset()
        output = model.step(txn)   # advance one cycle, return expected output
    """

    def __init__(self, width: int = 8):
        self.width = width
        self.max_val = (1 << width) - 1
        self.count = 0
        self.overflow = 0

    def reset(self) -> CounterOutput:
        """Synchronous reset — sets count=0, overflow=0."""
        self.count = 0
        self.overflow = 0
        return CounterOutput(count_out=0, overflow=0)

    def step(self, txn: CounterTxn, rst_n: int = 1) -> CounterOutput:
        """Advance the reference model by one clock cycle.

        Args:
            txn:   Input transaction for this cycle.
            rst_n: Reset signal (1=active, 0=reset). If 0, reset takes priority.

        Returns:
            Expected CounterOutput after this clock edge.
        """
        if not rst_n:
            return self.reset()

        if txn.load:
            self.count = txn.data_in & self.max_val
            self.overflow = 0
        elif txn.en:
            if not txn.up_down:
                # Count up
                if self.count == self.max_val:
                    self.count = 0
                    self.overflow = 1
                else:
                    self.count += 1
                    self.overflow = 0
            else:
                # Count down
                if self.count == 0:
                    self.count = self.max_val
                    self.overflow = 1
                else:
                    self.count -= 1
                    self.overflow = 0
        else:
            # Disabled — hold value, clear overflow
            self.overflow = 0

        return CounterOutput(count_out=self.count, overflow=self.overflow)

    def get_output(self) -> CounterOutput:
        """Return current state without advancing."""
        return CounterOutput(count_out=self.count, overflow=self.overflow)
