"""cocotb test runner for shift_reg_cx1 using cocotb.runner (Icarus backend)."""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", category=UserWarning)


def _ip_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def run() -> int:
    ip_dir = _ip_dir()
    rtl_sv = ip_dir / "rtl" / "shift_reg_cx1.sv"
    sim_dir = ip_dir / "sim"
    sim_dir.mkdir(parents=True, exist_ok=True)
    build_dir = sim_dir / "sim_build"

    tb_dir = ip_dir / "tb" / "cocotb"
    if str(tb_dir) not in sys.path:
        sys.path.insert(0, str(tb_dir))

    from cocotb.runner import get_runner

    runner = get_runner("icarus")

    runner.build(
        verilog_sources=[rtl_sv],
        hdl_toplevel="shift_reg_cx1",
        build_dir=build_dir,
        always=True,
        verbose=True,
    )

    results = runner.test(
        test_module="test_shift_reg_cx1",
        hdl_toplevel="shift_reg_cx1",
        hdl_toplevel_lang="verilog",
        build_dir=build_dir,
        test_dir=sim_dir,
        results_xml="results.xml",
        extra_env={
            "PROJECT_ROOT": str(ip_dir.parent),
            "PYTHONPATH": str(tb_dir),
        },
        verbose=True,
    )

    print("Results XML:", results)
    return 0 if results else 1


if __name__ == "__main__":
    sys.exit(run())
