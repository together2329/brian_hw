from __future__ import annotations

from pyuvm import uvm_driver, uvm_monitor


class GoalDriver(uvm_driver):
    def __init__(self, name: str, parent=None):
        super().__init__(name, parent)
        self.driven = []

    async def drive_item(self, item) -> None:
        self.driven.append(item.transaction)


class GoalMonitor(uvm_monitor):
    def __init__(self, name: str, parent=None):
        super().__init__(name, parent)
        self.observed = []

    def monitor_sample(self, goal_id: str, observed: dict) -> dict:
        row = {"goal_id": goal_id, "rtl_observed": dict(observed)}
        self.observed.append(row)
        return row
