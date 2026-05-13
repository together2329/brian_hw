from __future__ import annotations

import json
import importlib.util
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
EMIT_CYCLE_MODEL = REPO / "workflow" / "fl-model-gen" / "scripts" / "emit_cycle_model.py"


def test_emit_cycle_model_generates_pymtl_shell_without_pytest_plugin(tmp_path: Path) -> None:
    ip = "pymtl_cycle_ip"
    ip_dir = tmp_path / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "model").mkdir(parents=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        """
top_module:
  name: pymtl_cycle_ip
function_model:
  transactions:
    - id: primary_behavior
      name: primary_behavior
cycle_model:
  executable: pymtl3
  latency:
    primary_behavior: {min_cycles: 1, max_cycles: 2}
  handshake_rules:
    - {name: valid_ready, description: sample only on valid and ready}
  ordering:
    - {name: in_order, description: responses follow accepted request order}
  performance:
    frequency_mhz: 250
    throughput: {sustained_beats_per_cycle: 1, condition: no backpressure}
    outstanding: {max: 2, read_max: 2, write_max: 1}
    depth: {pipeline_stages: 3, queue_depth: 2}
sub_modules: []
""".lstrip(),
        encoding="utf-8",
    )
    (ip_dir / "model" / "functional_model.py").write_text(
        """
class FunctionalModel:
    def __init__(self, params=None):
        self.params = params

    def reset(self):
        pass

    def apply(self, txn):
        return {"kind": txn.get("kind", "primary_behavior"), "resp": 0}
""".lstrip(),
        encoding="utf-8",
    )

    run = subprocess.run(
        [sys.executable, str(EMIT_CYCLE_MODEL), ip, "--root", str(tmp_path)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert run.returncode == 0, run.stderr + run.stdout
    model_path = ip_dir / "model" / "cycle_model.py"
    source = model_path.read_text(encoding="utf-8")
    assert "MODEL_BACKEND: str = 'pymtl3'" in source
    assert "class CycleModelPyMTL(Component):" in source
    assert "def make_pymtl_cycle_model()" in source
    assert "pytest-pymtl3" in source
    for forbidden in ("output_rules", "state_updates", "_eval_rule_expr"):
        assert forbidden not in source

    report = json.loads((ip_dir / "model" / "cl_model_check.json").read_text(encoding="utf-8"))
    assert report["passed"] is True
    assert report["backend"] == "pymtl3"
    assert report["performance_targets"]["frequency_mhz"] == 250
    assert report["performance_targets"]["pipeline_stages"] == 3

    sys.path.insert(0, str(model_path.parent))
    try:
        spec = importlib.util.spec_from_file_location("generated_cycle_model", model_path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if module.HAS_PYMTL3:
            assert type(module.make_pymtl_cycle_model()).__name__ == "CycleModelPyMTL"
    finally:
        sys.path.remove(str(model_path.parent))


def test_emit_cycle_model_sanitizes_function_rule_metadata_from_source(tmp_path: Path) -> None:
    ip = "pymtl_cycle_rule_text_ip"
    ip_dir = tmp_path / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "model").mkdir(parents=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        """
top_module:
  name: pymtl_cycle_rule_text_ip
function_model:
  transactions:
    - id: primary_behavior
      name: primary_behavior
      output_rules:
        - {name: result, expr: value + 1, width: 8, port: result}
      state_updates:
        - {name: accepted_count, expr: accepted_count + 1}
  invariants:
    - CL metadata may mention output_rules in prose without owning evaluation.
cycle_model:
  executable: pymtl3
  latency:
    primary_behavior: {min_cycles: 1, max_cycles: 1}
  handshake_rules:
    - {name: valid_ready, description: sample only on valid and ready; do not inspect output_rules}
  ordering:
    - {name: in_order, description: responses follow accepted request order}
sub_modules: []
""".lstrip(),
        encoding="utf-8",
    )
    (ip_dir / "model" / "functional_model.py").write_text(
        """
class FunctionalModel:
    def __init__(self, params=None):
        self.params = params

    def reset(self):
        pass

    def apply(self, txn):
        return {"kind": txn.get("kind", "primary_behavior"), "resp": 0, "result": 1}
""".lstrip(),
        encoding="utf-8",
    )

    run = subprocess.run(
        [sys.executable, str(EMIT_CYCLE_MODEL), ip, "--root", str(tmp_path)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert run.returncode == 0, run.stderr + run.stdout
    source = (ip_dir / "model" / "cycle_model.py").read_text(encoding="utf-8")
    for forbidden in ("output_rules", "state_updates", "_eval_rule_expr"):
        assert forbidden not in source
    assert "functional_outputs" in source
