class CountToTargetSequence:
    def __init__(self, target):
        self.target = target

    async def run(self, env, dut):
        env.scoreboard.expected.append(self.target)
        await env.driver.drive_start(dut)
