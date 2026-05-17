from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
IP_DIR = PROJECT_ROOT / "mini_axi_slave_wrapper"


def test_mini_axi_slave_wrapper_supports_four_outstanding(tmp_path: Path) -> None:
    if not shutil.which("iverilog") or not shutil.which("vvp"):
        pytest.skip("iverilog and vvp are required for RTL simulation")

    simv = tmp_path / "mini_axi_slave_wrapper.vvp"
    compile_cmd = [
        "iverilog",
        "-g2012",
        "-Wall",
        "-I",
        str(IP_DIR / "rtl"),
        "-o",
        str(simv),
        str(IP_DIR / "rtl" / "mini_axi_slave_wrapper.sv"),
        str(IP_DIR / "tb" / "tb_mini_axi_slave_wrapper.sv"),
    ]
    compiled = subprocess.run(
        compile_cmd,
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert compiled.returncode == 0, compiled.stderr + compiled.stdout

    ran = subprocess.run(
        ["vvp", str(simv)],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert ran.returncode == 0, ran.stderr + ran.stdout
    assert "supports pipelined four outstanding reads and writes" in ran.stdout
