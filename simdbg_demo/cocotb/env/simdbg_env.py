from simdbg_demo.cocotb.agent.gpio_agent import SimdbgDriver, SimdbgMonitor


class SimdbgScoreboard:
    def __init__(self):
        self.expected = []
        self.observed = []

    def check(self):
        return self.expected == self.observed


class SimdbgEnv:
    def __init__(self):
        self.driver = SimdbgDriver()
        self.monitor = SimdbgMonitor()
        self.scoreboard = SimdbgScoreboard()
