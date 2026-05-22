from __future__ import annotations

from typing import Iterable

from pyuvm import uvm_sequence

from transactions import GoalTransaction


class GoalSequence(uvm_sequence):
    def __init__(self, name: str, items: Iterable[GoalTransaction]):
        super().__init__(name)
        self.items = list(items)

    async def body(self) -> None:
        for item in self.items:
            await self.start_item(item)
            await self.finish_item(item)

    def __iter__(self):
        return iter(self.items)
