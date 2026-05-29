from __future__ import annotations

from pathlib import Path

from pyuvm import uvm_env

from agents import ApbMaster, ApbMonitor, AxiWriteMaster, SramMonitor
from scoreboard import MctpScoreboard
from tb_coverage import FunctionalCoverageCollector


class MctpEnv(uvm_env):
    def __init__(self, name: str, ip_dir: Path, parent=None):
        super().__init__(name, parent)
        self.ip_dir = ip_dir
        self.apb = ApbMaster("apb_master", self)
        self.axi = AxiWriteMaster("axi_master", self)
        self.apb_monitor = ApbMonitor("apb_monitor", self)
        self.sram_monitor = SramMonitor("sram_monitor", self)
        self.scoreboard = MctpScoreboard("scoreboard", ip_dir, self)
        self.coverage = FunctionalCoverageCollector("coverage", self)

    def bind(self, dut) -> None:
        self.apb.bind(dut, "pclk")
        self.axi.bind(dut, "axi_aclk")
        self.sram_monitor.bind(dut, "axi_aclk")
