from __future__ import annotations

import json
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "workflow" / "tb-gen" / "scripts" / "check_tb_python_compile.py"


def test_tb_python_compile_gate_passes_and_writes_artifact(tmp_path: Path) -> None:
    ip_dir = tmp_path / "ok_ip"
    tb_dir = ip_dir / "tb" / "cocotb"
    tb_dir.mkdir(parents=True)
    (tb_dir / "test_ok_ip.py").write_text("def test_helper():\n    return 1\n", encoding="utf-8")

    result = subprocess.run(
        ["python3", str(SCRIPT), "ok_ip", "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 0, result.stdout
    report = json.loads((tb_dir / "tb_py_compile.json").read_text(encoding="utf-8"))
    assert report["passed"] is True
    assert report["errors"] == []
    assert report["files"] == ["ok_ip/tb/cocotb/test_ok_ip.py"]


def test_tb_python_compile_gate_fails_before_sim_on_syntax_error(tmp_path: Path) -> None:
    ip_dir = tmp_path / "bad_ip"
    tb_dir = ip_dir / "tb" / "cocotb"
    tb_dir.mkdir(parents=True)
    (tb_dir / "test_bad_ip.py").write_text("def broken(:\n", encoding="utf-8")

    result = subprocess.run(
        ["python3", str(SCRIPT), "bad_ip", "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 1
    report = json.loads((tb_dir / "tb_py_compile.json").read_text(encoding="utf-8"))
    assert report["passed"] is False
    assert len(report["errors"]) == 1
    assert "SyntaxError" in report["errors"][0]["error"]
