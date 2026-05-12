from __future__ import annotations

from pyuvm import uvm_env

from agents import GoalDriver, GoalMonitor
from scoreboard import GoalScoreboard
from tb_coverage import FunctionalCoverageCollector


class GoalEnv(uvm_env):
    def __init__(self, name: str, ip: str, root, parent=None):
        super().__init__(name, parent)
        self.driver = GoalDriver("driver", self)
        self.monitor = GoalMonitor("monitor", self)
        self.scoreboard = GoalScoreboard("scoreboard", ip, root, self)
        self.coverage = FunctionalCoverageCollector("coverage", self)
