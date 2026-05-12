try:
    import cocotb
except ImportError:
    class _CocotbStub:
        @staticmethod
        def test():
            def _decorator(fn):
                return fn
            return _decorator

    cocotb = _CocotbStub()

from simdbg_demo.cocotb.env.simdbg_env import SimdbgEnv
from simdbg_demo.cocotb.sequences.basic_sequence import CountToTargetSequence


@cocotb.test()
async def count_reaches_target(dut):
    env = SimdbgEnv()
    seq = CountToTargetSequence(target=3)
    await seq.run(env, dut)
