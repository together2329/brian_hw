from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pyuvm import uvm_sequence_item


@dataclass
class GoalTransaction(uvm_sequence_item):
    goal_id: str
    scenario_id: str
    payload: dict[str, Any]

    def __post_init__(self) -> None:
        uvm_sequence_item.__init__(self, self.goal_id)

    @property
    def transaction(self) -> dict[str, Any]:
        data = dict(self.payload)
        data.setdefault("goal_id", self.goal_id)
        data.setdefault("scenario_id", self.scenario_id)
        return data
