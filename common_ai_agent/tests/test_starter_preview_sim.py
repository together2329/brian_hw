from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil

import pytest


def _load_script(rel: str, name: str):
    root = Path(__file__).resolve().parents[1]
    path = root / rel
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_starter_preview_runs_rtl_to_sim(tmp_path: Path):
    if not shutil.which("iverilog") or not shutil.which("vvp"):
        pytest.skip("iverilog and vvp are required for Starter preview simulation")
    rtl_gen = _load_script("workflow/rtl-gen/scripts/ssot_to_rtl.py", "starter_rtl_gen_under_test")
    sim = _load_script("workflow/sim/scripts/starter_preview_sim.py", "starter_preview_sim_under_test")
    ip = "tiny_starter_and"
    ip_dir = tmp_path / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        """
top_module:
  name: tiny_starter_and
io_list:
  interfaces:
    - name: pins
      type: raw
      ports:
        - {name: a_i, direction: input, width: 1}
        - {name: b_i, direction: input, width: 1}
        - {name: y_o, direction: output, width: 1}
function_model:
  description: y_o is asserted when both inputs are asserted.
  output_rules:
    - {name: y_o, expr: a_i and b_i}
""".strip()
        + "\n",
        encoding="utf-8",
    )

    rtl_gen.generate(ip, tmp_path, mode="starter")
    payload = sim.run(ip, tmp_path)

    report = json.loads((ip_dir / "sim" / "starter_preview_sim.json").read_text(encoding="utf-8"))
    assert payload["status"] == "PASS"
    assert report["tests"] == 4
    assert report["pass"] == 4
    assert report["fail"] == 0
    assert (ip_dir / "tb" / f"tb_{ip}.sv").is_file()
    assert (ip_dir / "sim" / f"{ip}.out").is_file()
    assert (ip_dir / "sim" / "results.xml").is_file()
    assert "TESTS=4 PASS=4 FAIL=0" in (ip_dir / "sim" / "sim_report.txt").read_text(encoding="utf-8")
