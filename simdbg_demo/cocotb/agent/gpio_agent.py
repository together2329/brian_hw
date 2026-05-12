class SimdbgDriver:
    async def drive_start(self, dut):
        dut.start.value = 1


class SimdbgMonitor:
    async def sample_count(self, dut):
        return int(dut.count.value)
