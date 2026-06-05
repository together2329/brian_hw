from __future__ import annotations

import json
import importlib.util
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
EMIT_CYCLE_MODEL = REPO / "workflow" / "fl-model-gen" / "scripts" / "emit_cycle_model.py"


def test_emit_cycle_model_generates_pure_python_stepper(tmp_path: Path) -> None:
    ip = "python_cycle_ip"
    ip_dir = tmp_path / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "model").mkdir(parents=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        """
top_module:
  name: python_cycle_ip
function_model:
  transactions:
    - id: primary_behavior
      name: primary_behavior
cycle_model:
  executable: python
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
    assert "MODEL_BACKEND: str = 'python'" in source
    retired_backend = "pym" + "tl"
    assert f"class CycleModel{retired_backend.upper()}3" not in source
    assert f"def make_{retired_backend}_cycle_model" not in source
    assert retired_backend not in source.lower()
    for forbidden in ("output_rules", "state_updates", "_eval_rule_expr"):
        assert forbidden not in source

    report = json.loads((ip_dir / "model" / "cl_model_check.json").read_text(encoding="utf-8"))
    assert report["passed"] is True
    assert report["backend"] == "python"
    assert report["performance_targets"]["frequency_mhz"] == 250
    assert report["performance_targets"]["pipeline_stages"] == 3

    sys.path.insert(0, str(model_path.parent))
    try:
        spec = importlib.util.spec_from_file_location("generated_cycle_model", model_path)
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        result = module.CycleModel().run_self_check()
        assert result["backend"] == "python"
    finally:
        sys.path.remove(str(model_path.parent))


def test_emit_cycle_model_sanitizes_function_rule_metadata_from_source(tmp_path: Path) -> None:
    ip = "python_cycle_rule_text_ip"
    ip_dir = tmp_path / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "model").mkdir(parents=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        """
top_module:
  name: python_cycle_rule_text_ip
function_model:
  transactions:
    - id: primary_behavior
      name: primary_behavior
      required_fields: [value]
      output_rules:
        - {name: result, expr: value + 1, width: 8, port: result}
      state_updates:
        - {name: accepted_count, expr: accepted_count + 1}
  invariants:
    - CL metadata may mention output_rules in prose without owning evaluation.
cycle_model:
  executable: python
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


def test_emit_cycle_model_blocks_undeclared_fl_cl_symbols(tmp_path: Path) -> None:
    ip = "python_cycle_symbol_block_ip"
    ip_dir = tmp_path / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "model").mkdir(parents=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        """
top_module:
  name: python_cycle_symbol_block_ip
function_model:
  state_variables:
    - {name: payload_byte_count_q, reset: 0}
  transactions:
    - id: FM_ACCEPT_SOM
      name: accept_start_packet
      required_fields: [payload_valid_bytes]
      output_rules:
        - {name: sram_wr_valid_next, expr: "1 if bytes_to_store > 0 else 0"}
      state_updates:
        - {name: payload_byte_count_q, expr: "payload_byte_count_q + bytes_to_store"}
cycle_model:
  executable: python
  latency:
    FM_ACCEPT_SOM: {min_cycles: 1, max_cycles: 1}
  handshake_rules:
    - {name: sram_write, description: valid/ready write beat}
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
        if "bytes_to_store" not in txn:
            raise KeyError("unknown rule name bytes_to_store")
        return {"kind": txn.get("kind", "FM_ACCEPT_SOM"), "resp": 0}
""".lstrip(),
        encoding="utf-8",
    )

    run = subprocess.run(
        [sys.executable, str(EMIT_CYCLE_MODEL), ip, "--root", str(tmp_path)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert run.returncode == 1
    report = json.loads((ip_dir / "model" / "cl_model_check.json").read_text(encoding="utf-8"))
    assert report["passed"] is False
    symbol_contract = report["symbol_contract"]
    assert symbol_contract["status"] == "blocked"
    assert symbol_contract["failure_owner"] == "fl-model-gen"
    assert symbol_contract["stage"] == "cl-model"
    assert symbol_contract["required_rerun"] == [
        "cl-model",
        "equivalence",
        "rtl",
        "lint",
        "tb",
        "sim",
        "contract-check",
    ]
    assert symbol_contract["unknown_symbols"] == ["bytes_to_store"]
    assert symbol_contract["transactions"][0]["missing_symbols"] == ["bytes_to_store"]


def test_emit_cycle_model_accepts_declared_derived_symbols(tmp_path: Path) -> None:
    ip = "python_cycle_symbol_contract_ip"
    ip_dir = tmp_path / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "model").mkdir(parents=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        """
top_module:
  name: python_cycle_symbol_contract_ip
function_model:
  state_variables:
    - {name: payload_byte_count_q, reset: 0}
  derived_signals:
    - {name: bytes_to_store, expr: "max(payload_valid_bytes - 1, 0)"}
  transactions:
    - id: FM_ACCEPT_SOM
      name: accept_start_packet
      required_fields: [payload_valid_bytes]
      output_rules:
        - {name: sram_wr_valid_next, expr: "1 if bytes_to_store > 0 else 0"}
      state_updates:
        - {name: payload_byte_count_q, expr: "payload_byte_count_q + bytes_to_store"}
cycle_model:
  executable: python
  latency:
    FM_ACCEPT_SOM: {min_cycles: 1, max_cycles: 1}
  handshake_rules:
    - {name: sram_write, description: valid/ready write beat}
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
        return {"kind": txn.get("kind", "FM_ACCEPT_SOM"), "resp": 0}
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
    report = json.loads((ip_dir / "model" / "cl_model_check.json").read_text(encoding="utf-8"))
    assert report["passed"] is True
    symbol_contract = report["symbol_contract"]
    assert symbol_contract["status"] == "pass"
    assert symbol_contract["unknown_symbols"] == []
    assert symbol_contract["transactions"][0]["used_symbols"] == [
        "bytes_to_store",
        "payload_byte_count_q",
        "payload_valid_bytes",
    ]


def test_emit_cycle_model_accepts_list_form_parameter_symbols(tmp_path: Path) -> None:
    ip = "python_cycle_parameter_symbol_contract_ip"
    ip_dir = tmp_path / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "model").mkdir(parents=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        """
top_module:
  name: python_cycle_parameter_symbol_contract_ip
parameters:
  - {name: MAX_TLP_BYTES, default: 4096}
function_model:
  transactions:
    - id: primary_behavior
      name: primary_behavior
      required_fields: [tlp_byte_count]
      output_rules:
        - {name: legal_len, expr: "tlp_byte_count <= MAX_TLP_BYTES"}
cycle_model:
  executable: python
  latency:
    primary_behavior: {min_cycles: 1, max_cycles: 1}
  handshake_rules:
    - {name: valid_ready, description: valid-ready beat}
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
    report = json.loads((ip_dir / "model" / "cl_model_check.json").read_text(encoding="utf-8"))
    symbol_contract = report["symbol_contract"]
    assert symbol_contract["status"] == "pass"
    assert symbol_contract["unknown_symbols"] == []
    assert "MAX_TLP_BYTES" in symbol_contract["transactions"][0]["declared_symbols"]


def test_emit_cycle_model_accepts_register_path_symbols(tmp_path: Path) -> None:
    ip = "python_cycle_register_path_symbol_contract_ip"
    ip_dir = tmp_path / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "model").mkdir(parents=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        """
top_module:
  name: python_cycle_register_path_symbol_contract_ip
registers:
  register_list:
    - name: CMP
      fields:
        - {name: compare_value, width: 32}
function_model:
  state_variables:
    - {name: counter, reset: 0}
  transactions:
    - id: primary_behavior
      name: primary_behavior
      output_rules:
        - {name: match, expr: "1 if counter == registers.CMP.data else 0"}
cycle_model:
  executable: python
  latency:
    primary_behavior: {min_cycles: 1, max_cycles: 1}
  handshake_rules:
    - {name: valid_ready, description: valid-ready beat}
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
    report = json.loads((ip_dir / "model" / "cl_model_check.json").read_text(encoding="utf-8"))
    symbol_contract = report["symbol_contract"]
    assert symbol_contract["status"] == "pass"
    assert symbol_contract["unknown_symbols"] == []
    assert "registers.CMP.data" in symbol_contract["transactions"][0]["declared_symbols"]
    assert "registers.CMP.data" in symbol_contract["transactions"][0]["used_symbols"]


def test_emit_cycle_model_accepts_transaction_inputs_and_input_map_aliases(tmp_path: Path) -> None:
    ip = "python_cycle_apb_alias_symbol_contract_ip"
    ip_dir = tmp_path / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "model").mkdir(parents=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        """
top_module:
  name: python_cycle_apb_alias_symbol_contract_ip
rtl_contract:
  input_map:
    psel: PSEL
    penable: PENABLE
    pwrite: PWRITE
    paddr: PADDR
    pwdata: PWDATA
function_model:
  state_variables:
    - {name: opa_q, reset: 0}
    - {name: opb_q, reset: 0}
  transactions:
    - id: FM_WRITE
      name: apb_write
      preconditions_expr: psel == 1 and penable == 1 and pwrite == 1
      inputs: [pwdata, paddr]
      output_rules:
        - {name: add_rule, expr: "((pwdata if paddr == 0 else opa_q) + opb_q) & 0xff"}
      state_updates:
        - {name: opa_q, expr: "pwdata if paddr == 0 else opa_q"}
cycle_model:
  executable: python
  latency:
    FM_WRITE: {min_cycles: 1, max_cycles: 1}
  handshake_rules:
    - {name: valid_ready, description: valid-ready beat}
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
        return {"kind": txn.get("kind", "FM_WRITE"), "resp": 0}
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
    report = json.loads((ip_dir / "model" / "cl_model_check.json").read_text(encoding="utf-8"))
    symbol_contract = report["symbol_contract"]
    assert symbol_contract["status"] == "pass"
    assert symbol_contract["unknown_symbols"] == []
    declared = symbol_contract["transactions"][0]["declared_symbols"]
    for name in ("psel", "penable", "pwrite", "paddr", "pwdata"):
        assert name in declared


def test_emit_cycle_model_ignores_transaction_precondition_prose(tmp_path: Path) -> None:
    ip = "python_cycle_precondition_prose_ip"
    ip_dir = tmp_path / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "model").mkdir(parents=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        """
top_module:
  name: python_cycle_precondition_prose_ip
rtl_contract:
  input_map:
    valid: valid
    value: data_in
function_model:
  transactions:
    - id: FM_PRIMARY
      name: primary_behavior
      required_fields: [value]
      preconditions:
        - rst_n is deasserted
        - valid is high
        - AWSIZE==5 and AWBURST==INCR
      output_rules:
        - {name: result, expr: "value * 2"}
cycle_model:
  executable: python
  latency:
    FM_PRIMARY: {min_cycles: 1, max_cycles: 1}
  handshake_rules:
    - {name: valid_ready, description: valid-ready beat}
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
        return {"kind": txn.get("kind", "FM_PRIMARY"), "resp": 0}
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
    report = json.loads((ip_dir / "model" / "cl_model_check.json").read_text(encoding="utf-8"))
    symbol_contract = report["symbol_contract"]
    assert symbol_contract["status"] == "pass"
    assert symbol_contract["unknown_symbols"] == []


def test_emit_cycle_model_blocks_undeclared_cycle_rule_symbols(tmp_path: Path) -> None:
    ip = "python_cycle_rule_symbol_block_ip"
    ip_dir = tmp_path / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "model").mkdir(parents=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        """
top_module:
  name: python_cycle_rule_symbol_block_ip
function_model:
  transactions:
    - id: primary_behavior
      name: primary_behavior
cycle_model:
  executable: python
  latency:
    primary_behavior: {min_cycles: 1, max_cycles: 1}
  handshake_rules:
    - name: sram_write_hold
      predicate: sram_wr_valid and sram_wr_ready
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

    assert run.returncode == 1
    report = json.loads((ip_dir / "model" / "cl_model_check.json").read_text(encoding="utf-8"))
    symbol_contract = report["symbol_contract"]
    assert symbol_contract["status"] == "blocked"
    assert symbol_contract["unknown_symbols"] == ["sram_wr_ready", "sram_wr_valid"]
    assert symbol_contract["cycle_rules"][0]["missing_symbols"] == ["sram_wr_ready", "sram_wr_valid"]


def test_emit_cycle_model_blocks_non_python_operator_symbols(tmp_path: Path) -> None:
    ip = "python_cycle_dsl_operator_symbol_block_ip"
    ip_dir = tmp_path / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "model").mkdir(parents=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        """
top_module:
  name: python_cycle_dsl_operator_symbol_block_ip
function_model:
  transactions:
    - id: primary_behavior
      name: primary_behavior
      required_fields: [req_valid]
      output_rules:
        - {name: accepted, expr: "req_valid && invented_ready"}
cycle_model:
  executable: python
  latency:
    primary_behavior: {min_cycles: 1, max_cycles: 1}
  handshake_rules:
    - {name: valid_ready, description: valid-ready beat}
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

    assert run.returncode == 1
    report = json.loads((ip_dir / "model" / "cl_model_check.json").read_text(encoding="utf-8"))
    symbol_contract = report["symbol_contract"]
    assert symbol_contract["status"] == "blocked"
    assert symbol_contract["unknown_symbols"] == ["invented_ready"]
    assert symbol_contract["transactions"][0]["missing_symbols"] == ["invented_ready"]


def test_emit_cycle_model_blocks_transitive_derived_symbol_dependencies_by_leaf_order(tmp_path: Path) -> None:
    for suffix, derived_signals in {
        "leaf_first": """
  derived_signals:
    - {name: leaf_bytes, expr: "missing_leaf + 1"}
    - {name: bytes_to_store, expr: "leaf_bytes + payload_valid_bytes"}
""",
        "leaf_last": """
  derived_signals:
    - {name: bytes_to_store, expr: "leaf_bytes + payload_valid_bytes"}
    - {name: leaf_bytes, expr: "missing_leaf + 1"}
""",
    }.items():
        ip = f"python_cycle_transitive_symbol_block_{suffix}"
        ip_dir = tmp_path / ip
        (ip_dir / "yaml").mkdir(parents=True)
        (ip_dir / "model").mkdir(parents=True)
        (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
            f"""
top_module:
  name: {ip}
function_model:
  state_variables:
    - {{name: payload_byte_count_q, reset: 0}}
{derived_signals.rstrip()}
  transactions:
    - id: FM_ACCEPT_SOM
      name: accept_start_packet
      required_fields: [payload_valid_bytes]
      output_rules:
        - {{name: sram_wr_valid_next, expr: "1 if bytes_to_store > 0 else 0"}}
      state_updates:
        - {{name: payload_byte_count_q, expr: "payload_byte_count_q + bytes_to_store"}}
cycle_model:
  executable: python
  latency:
    FM_ACCEPT_SOM: {{min_cycles: 1, max_cycles: 1}}
  handshake_rules:
    - {{name: sram_write, description: valid/ready write beat}}
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
        return {"kind": txn.get("kind", "FM_ACCEPT_SOM"), "resp": 0}
""".lstrip(),
            encoding="utf-8",
        )

        run = subprocess.run(
            [sys.executable, str(EMIT_CYCLE_MODEL), ip, "--root", str(tmp_path)],
            text=True,
            capture_output=True,
            check=False,
        )

        assert run.returncode == 1
        report = json.loads((ip_dir / "model" / "cl_model_check.json").read_text(encoding="utf-8"))
        symbol_contract = report["symbol_contract"]
        assert symbol_contract["status"] == "blocked"
        assert symbol_contract["unknown_symbols"] == ["missing_leaf"]
        assert symbol_contract["transactions"][0]["missing_symbols"] == ["missing_leaf"]


def test_emit_cycle_model_blocks_undeclared_pipeline_rule_symbols(tmp_path: Path) -> None:
    ip = "python_cycle_pipeline_rule_symbol_block_ip"
    ip_dir = tmp_path / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "model").mkdir(parents=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        """
top_module:
  name: python_cycle_pipeline_rule_symbol_block_ip
function_model:
  input_symbols: [valid]
  transactions:
    - id: primary_behavior
      name: primary_behavior
cycle_model:
  executable: python
  latency:
    primary_behavior: {min_cycles: 1, max_cycles: 1}
  pipeline:
    - stage: response_hold
      output_rules:
        - {name: response_valid, expr: "valid and invented_cl_symbol"}
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

    assert run.returncode == 1
    report = json.loads((ip_dir / "model" / "cl_model_check.json").read_text(encoding="utf-8"))
    symbol_contract = report["symbol_contract"]
    assert symbol_contract["status"] == "blocked"
    assert symbol_contract["unknown_symbols"] == ["invented_cl_symbol"]
    assert symbol_contract["cycle_rules"][0]["missing_symbols"] == ["invented_cl_symbol"]


def test_emit_cycle_model_accepts_declared_cycle_io_signal_symbols(tmp_path: Path) -> None:
    ip = "python_cycle_rule_declared_io_ip"
    ip_dir = tmp_path / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "model").mkdir(parents=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        """
top_module:
  name: python_cycle_rule_declared_io_ip
io_list:
  interfaces:
    - name: sram
      ports:
        - {name: sram_wr_valid, direction: output, width: 1}
        - {name: sram_wr_ready, direction: input, width: 1}
function_model:
  transactions:
    - id: primary_behavior
      name: primary_behavior
cycle_model:
  executable: python
  latency:
    primary_behavior: {min_cycles: 1, max_cycles: 1}
  handshake_rules:
    - name: sram_write_hold
      signal: sram_wr_valid/sram_wr_ready
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
    report = json.loads((ip_dir / "model" / "cl_model_check.json").read_text(encoding="utf-8"))
    symbol_contract = report["symbol_contract"]
    assert symbol_contract["status"] == "pass"
    assert symbol_contract["unknown_symbols"] == []
    assert symbol_contract["cycle_rules"][0]["field"] == "signal"
    assert symbol_contract["cycle_rules"][0]["used_symbols"] == ["sram_wr_ready", "sram_wr_valid"]


def test_emit_cycle_model_ignores_cycle_rule_prose_metadata(tmp_path: Path) -> None:
    ip = "python_cycle_rule_prose_metadata_ip"
    ip_dir = tmp_path / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "model").mkdir(parents=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        """
top_module:
  name: python_cycle_rule_prose_metadata_ip
function_model:
  transactions:
    - id: primary_behavior
      name: primary_behavior
cycle_model:
  executable: python
  latency:
    primary_behavior: {min_cycles: 1, max_cycles: 1}
  handshake_rules:
    - name: valid_ready_prose
      signal: valid/ready write beat
      rule: Always 1 (0-wait-state)
      condition: no backpressure
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
    report = json.loads((ip_dir / "model" / "cl_model_check.json").read_text(encoding="utf-8"))
    symbol_contract = report["symbol_contract"]
    assert symbol_contract["status"] == "pass"
    assert symbol_contract["unknown_symbols"] == []


def test_emit_cycle_model_blocks_pipeline_rules_with_dsl_symbols(tmp_path: Path) -> None:
    ip = "python_cycle_pipeline_symbol_block_ip"
    ip_dir = tmp_path / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "model").mkdir(parents=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        """
top_module:
  name: python_cycle_pipeline_symbol_block_ip
function_model:
  input_symbols: [pipe_enable]
  transactions:
    - id: primary_behavior
      name: primary_behavior
cycle_model:
  executable: python
  latency:
    primary_behavior: {min_cycles: 1, max_cycles: 1}
  handshake_rules:
    - {name: valid_ready, description: trigger CL}
  pipeline:
    - name: ingress_pipe
      output_rules:
        - name: advance
          expr: pipe_enable && invented_cl_symbol
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

    assert run.returncode == 1
    report = json.loads((ip_dir / "model" / "cl_model_check.json").read_text(encoding="utf-8"))
    symbol_contract = report["symbol_contract"]
    assert symbol_contract["status"] == "blocked"
    assert symbol_contract["unknown_symbols"] == ["invented_cl_symbol"]
    assert symbol_contract["cycle_rules"][0]["section"] == "pipeline"
    assert symbol_contract["cycle_rules"][0]["field"] == "expr"
    assert symbol_contract["cycle_rules"][0]["missing_symbols"] == ["invented_cl_symbol"]


def test_emit_cycle_model_blocks_nested_cycle_rule_condition_symbols(tmp_path: Path) -> None:
    ip = "python_cycle_nested_condition_symbol_block_ip"
    ip_dir = tmp_path / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "model").mkdir(parents=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        """
top_module:
  name: python_cycle_nested_condition_symbol_block_ip
function_model:
  input_symbols: [sram_wr_valid]
  transactions:
    - id: primary_behavior
      name: primary_behavior
cycle_model:
  executable: python
  latency:
    primary_behavior: {min_cycles: 1, max_cycles: 1}
  handshake_rules:
    - name: nested_condition
      condition:
        ready: sram_wr_valid && invented_ready
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

    assert run.returncode == 1
    report = json.loads((ip_dir / "model" / "cl_model_check.json").read_text(encoding="utf-8"))
    symbol_contract = report["symbol_contract"]
    assert symbol_contract["status"] == "blocked"
    assert symbol_contract["unknown_symbols"] == ["invented_ready"]
    assert symbol_contract["cycle_rules"][0]["field"] == "ready"
    assert symbol_contract["cycle_rules"][0]["missing_symbols"] == ["invented_ready"]


def test_emit_cycle_model_blocks_transitive_derived_symbol_dependencies(tmp_path: Path) -> None:
    for suffix, derived_yaml in {
        "forward": """
  derived_signals:
    - {name: derived_a, expr: "derived_b + payload_valid_bytes"}
    - {name: derived_b, expr: "missing_leaf + 1"}
""",
        "reverse": """
  derived_signals:
    - {name: derived_b, expr: "missing_leaf + 1"}
    - {name: derived_a, expr: "derived_b + payload_valid_bytes"}
""",
    }.items():
        ip = f"python_cycle_derived_{suffix}_ip"
        ip_dir = tmp_path / ip
        (ip_dir / "yaml").mkdir(parents=True)
        (ip_dir / "model").mkdir(parents=True)
        (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
            f"""
top_module:
  name: {ip}
function_model:
{derived_yaml}  transactions:
    - id: FM_ACCEPT
      name: accept_packet
      required_fields: [payload_valid_bytes]
      output_rules:
        - {{name: result, expr: "derived_a + 1"}}
cycle_model:
  executable: python
  latency:
    FM_ACCEPT: {{min_cycles: 1, max_cycles: 1}}
  handshake_rules:
    - {{name: valid_ready, description: trigger CL}}
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
        return {"kind": txn.get("kind", "FM_ACCEPT"), "resp": 0}
""".lstrip(),
            encoding="utf-8",
        )

        run = subprocess.run(
            [sys.executable, str(EMIT_CYCLE_MODEL), ip, "--root", str(tmp_path)],
            text=True,
            capture_output=True,
            check=False,
        )

        assert run.returncode == 1
        report = json.loads((ip_dir / "model" / "cl_model_check.json").read_text(encoding="utf-8"))
        symbol_contract = report["symbol_contract"]
        assert symbol_contract["status"] == "blocked"
        assert symbol_contract["unknown_symbols"] == ["missing_leaf"]
        assert symbol_contract["transactions"][0]["missing_symbols"] == ["missing_leaf"]


def test_emit_cycle_model_blocks_dict_form_derived_symbol_dependencies(tmp_path: Path) -> None:
    ip = "python_cycle_dict_derived_symbol_block_ip"
    ip_dir = tmp_path / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "model").mkdir(parents=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        """
top_module:
  name: python_cycle_dict_derived_symbol_block_ip
function_model:
  derived_signals:
    derived_a:
      expr: missing_leaf + payload_valid_bytes
  transactions:
    - id: FM_ACCEPT
      name: accept_packet
      required_fields: [payload_valid_bytes]
      output_rules:
        - {name: result, expr: "derived_a + 1"}
cycle_model:
  executable: python
  latency:
    FM_ACCEPT: {min_cycles: 1, max_cycles: 1}
  handshake_rules:
    - {name: valid_ready, description: trigger CL}
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
        return {"kind": txn.get("kind", "FM_ACCEPT"), "resp": 0}
""".lstrip(),
        encoding="utf-8",
    )

    run = subprocess.run(
        [sys.executable, str(EMIT_CYCLE_MODEL), ip, "--root", str(tmp_path)],
        text=True,
        capture_output=True,
        check=False,
    )

    assert run.returncode == 1
    report = json.loads((ip_dir / "model" / "cl_model_check.json").read_text(encoding="utf-8"))
    symbol_contract = report["symbol_contract"]
    assert symbol_contract["status"] == "blocked"
    assert symbol_contract["unknown_symbols"] == ["missing_leaf"]
    assert symbol_contract["transactions"][0]["missing_symbols"] == ["missing_leaf"]
