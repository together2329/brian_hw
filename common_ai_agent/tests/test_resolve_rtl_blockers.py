from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import yaml


def _load_resolver():
    root = Path(__file__).resolve().parents[1]
    path = root / "workflow" / "ssot-gen" / "scripts" / "resolve_rtl_blockers.py"
    spec = importlib.util.spec_from_file_location("resolve_rtl_blockers_module", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_rtl_contract_blocker_answers_project_into_rtl_contract():
    resolver = _load_resolver()
    doc = {
        "io_list": {
            "clock_domains": [{"ports": [{"name": "clock", "direction": "input"}]}],
            "resets": [{"ports": [{"name": "rst_n", "direction": "input"}]}],
            "interfaces": [
                {"ports": [{"name": "cfg_valid", "direction": "input"}, {"name": "status_data", "direction": "output"}]}
            ],
        }
    }
    blocker = {
        "questions": [
            {"id": "RTL_CLOCK_PORT", "decision_needed": "clock"},
            {"id": "RTL_RESET_PORT", "decision_needed": "reset"},
            {"id": "RTL_OUTPUT_MAP_OUTPUT_0", "decision_needed": "output map"},
        ]
    }
    answers = [
        {"id": "RTL_CLOCK_PORT", "answer": "Use clock as rtl_contract.clock."},
        {"id": "RTL_RESET_PORT", "answer": "Use rst_n as active-low reset."},
        {"id": "RTL_OUTPUT_MAP_OUTPUT_0", "answer": "Map output_0 to status_data."},
    ]

    out = resolver.apply_answers(doc, blocker, answers)
    contract = out["rtl_contract"]

    assert contract["clock"] == "clock"
    assert contract["reset"] == "rst_n"
    assert contract["reset_active"] == "low"
    assert contract["output_map"]["output_0"] == "status_data"


def test_target_scale_blocker_answer_locks_or_waives_quality_gate():
    resolver = _load_resolver()
    blocker = {
        "questions": [
            {
                "id": "RTL_TARGET_SCALE_POLICY",
                "suggested_ssot_target_scale": {
                    "source_files_min": 4,
                    "modules_min": 8,
                    "depth_score_min": 120,
                },
            }
        ]
    }

    locked = resolver.apply_answers(
        {"quality_gates": {"rtl_gen": {"profile": "production"}}},
        blocker,
        [{"id": "RTL_TARGET_SCALE_POLICY", "answer": "Use the suggested candidate after human architecture review."}],
    )

    scale = locked["quality_gates"]["rtl_gen"]["target_scale"]
    assert scale["source_files_min"] == 4
    assert scale["modules_min"] == 8
    assert scale["depth_score_min"] == 120
    assert "target_scale_waiver" not in locked["quality_gates"]["rtl_gen"]

    waived = resolver.apply_answers(
        {"quality_gates": {"rtl_gen": {"profile": "production"}}},
        blocker,
        [
            {
                "id": "RTL_TARGET_SCALE_POLICY",
                "custom": """
target_scale_waiver:
  approved: true
  reason: smaller validated IP variant
  owner: arch
""",
            }
        ],
    )

    waiver = waived["quality_gates"]["rtl_gen"]["target_scale_waiver"]
    assert waiver["approved"] is True
    assert waiver["reason"] == "smaller validated IP variant"
    assert waiver["owner"] == "arch"


def test_resolver_cli_can_lock_suggested_target_scale(tmp_path: Path):
    root = Path(__file__).resolve().parents[1]
    script = root / "workflow" / "ssot-gen" / "scripts" / "resolve_rtl_blockers.py"
    ip = "target_scale_cli"
    ip_dir = tmp_path / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "rtl").mkdir(parents=True)
    ssot_path = ip_dir / "yaml" / f"{ip}.ssot.yaml"
    ssot_path.write_text(
        yaml.safe_dump({"quality_gates": {"rtl_gen": {"profile": "production"}}}, sort_keys=False),
        encoding="utf-8",
    )
    (ip_dir / "rtl" / "rtl_blocked.json").write_text(
        json.dumps(
            {
                "questions": [
                    {
                        "id": "RTL_TARGET_SCALE_POLICY",
                        "suggested_ssot_target_scale": {
                            "source_files_min": 4,
                            "modules_min": 8,
                            "nonconstant_assigns_min": 16,
                            "depth_score_min": 120,
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, str(script), ip, "--root", str(tmp_path), "--use-suggested-target-scale"],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    doc = yaml.safe_load(ssot_path.read_text(encoding="utf-8"))
    scale = doc["quality_gates"]["rtl_gen"]["target_scale"]
    assert scale["source_files_min"] == 4
    assert scale["modules_min"] == 8
    assert scale["nonconstant_assigns_min"] == 16
    assert scale["depth_score_min"] == 120
    assert (ip_dir / "rtl" / "rtl_blocked_resolved.json").is_file()


def test_valid_ready_sample_condition_answer_updates_contract_and_fm():
    resolver = _load_resolver()
    doc = {
        "function_model": {
            "transactions": [{"id": "FM_PRIMARY", "name": "primary_behavior"}]
        },
        "rtl_contract": {"sample_condition": "valid"},
    }
    blocker = {
        "questions": [
            {
                "id": "RTL_VALID_READY_SAMPLE_CONDITION",
                "current_sample_condition": "valid",
                "ready_port": "ready",
            }
        ]
    }
    answers = [{"id": "RTL_VALID_READY_SAMPLE_CONDITION", "answer": "Use the recommended valid/ready acceptance."}]

    out = resolver.apply_answers(doc, blocker, answers)

    assert out["rtl_contract"]["sample_condition"] == "(valid) and ready"
    assert out["function_model"]["transactions"][0]["sample_condition"] == "(valid) and ready"
    assert any("sample_condition=(valid) and ready" in row["rule"] for row in out["cycle_model"]["handshake_rules"])


def test_observable_state_rule_answer_projects_machine_rules():
    resolver = _load_resolver()
    doc = {
        "function_model": {
            "transactions": [{"id": "FM_PRIMARY", "name": "primary_behavior"}]
        },
        "rtl_contract": {},
    }
    blocker = {
        "questions": [
            {
                "id": "RTL_OBSERVABLE_STATE_RULES",
                "missing_observable_state": ["busy", "error"],
            }
        ]
    }
    answers = [
        {
            "id": "RTL_OBSERVABLE_STATE_RULES",
            "custom": """
observable_state_rules:
  - name: busy
    port: busy
    expr: valid and ready
    width: 1
  - name: error
    port: error
    expr: not packet_ok
    width: 1
""",
        }
    ]

    out = resolver.apply_answers(doc, blocker, answers)
    txn = out["function_model"]["transactions"][0]

    assert {row["name"] for row in txn["output_rules"]} == {"busy", "error"}
    assert out["rtl_contract"]["output_map"]["busy"] == "busy"
    assert out["rtl_contract"]["output_map"]["error"] == "error"
    assert out["custom"]["rtl_observable_state_resolution_history"][-1]["unresolved"] == []


def test_rtl_module_contract_answer_projects_into_submodules():
    resolver = _load_resolver()
    doc = {
        "sub_modules": [
            {
                "name": "demo_fetch",
                "file": "rtl/demo_fetch.sv",
                "ownership": "manifest",
                "description": "fetch block",
            },
            {
                "name": "demo_top",
                "file": "rtl/demo_top.sv",
                "ownership": "manifest",
            },
        ]
    }
    blocker = {
        "questions": [
            {
                "id": "RTL_MODULE_CONTRACTS",
                "missing_modules": [{"name": "demo_fetch", "file": "rtl/demo_fetch.sv"}],
                "required_fields": ["implements", "source_sections", "function_model_refs"],
            }
        ]
    }
    answers = [
        {
            "id": "RTL_MODULE_CONTRACTS",
            "custom": """
module_contracts:
  - name: demo_fetch
    implements:
      - fetches next instruction address and captures imem response
    source_sections: [features, function_model, cycle_model]
    function_model_refs: [function_model.transactions.FM_PRIMARY.state_updates]
    decomposition_refs: [decomposition.units.fetch]
    cycle_model_refs: [cycle_model.pipeline.S0_ACCEPT]
    feature_refs: [approved_primary_behavior]
    dataflow_refs: [dataflow.sequence]
    ports: [clock, rst_n, imem_addr, imem_valid, imem_ready, imem_rdata]
    connections:
      clock: io_list.clock_domains.primary_clk
""",
        }
    ]

    out = resolver.apply_answers(doc, blocker, answers)
    fetch = out["sub_modules"][0]

    assert fetch["implements"] == ["fetches next instruction address and captures imem response"]
    assert fetch["source_sections"] == ["features", "function_model", "cycle_model"]
    assert fetch["function_model_refs"] == ["function_model.transactions.FM_PRIMARY.state_updates"]
    assert fetch["decomposition_refs"] == ["decomposition.units.fetch"]
    assert fetch["ports"] == ["clock", "rst_n", "imem_addr", "imem_valid", "imem_ready", "imem_rdata"]
    assert fetch["connections"] == {"clock": "io_list.clock_domains.primary_clk"}
    assert fetch["contract_status"] == "approved_by_rtl_blocker_answer"
    history = out["custom"]["rtl_module_contract_resolution_history"]
    assert history[-1]["applied"][0]["name"] == "demo_fetch"
    assert history[-1]["unresolved"] == []


def test_connection_contract_answer_projects_into_integration_and_submodules():
    resolver = _load_resolver()
    doc = {
        "integration": {"connections": []},
        "sub_modules": [
            {
                "name": "demo_engine",
                "file": "rtl/demo_engine.sv",
                "ownership": "manifest",
            },
            {
                "name": "demo_top",
                "file": "rtl/demo_top.sv",
                "ownership": "manifest",
            },
        ],
    }
    blocker = {
        "questions": [
            {
                "id": "RTL_RESOLVE_CONNECTION_CONTRACTS",
                "decision_needed": "approve machine-readable module/port/signal wiring contracts",
                "required_fields": ["module", "port", "signal"],
            }
        ]
    }
    answers = [
        {
            "id": "RTL_RESOLVE_CONNECTION_CONTRACTS",
            "custom": """
connection_contracts:
  - module: demo_engine
    instance: u_engine
    port: engine_done
    signal: done
    source_ref: integration.connections.engine_done
  - module: demo_engine
    port: clk
    signal: clk
""",
        }
    ]

    out = resolver.apply_answers(doc, blocker, answers)

    connections = out["integration"]["connections"]
    assert connections == [
        {
            "module": "demo_engine",
            "port": "engine_done",
            "signal": "done",
            "machine_readable": True,
            "instance": "u_engine",
            "source_ref": "integration.connections.engine_done",
        },
        {
            "module": "demo_engine",
            "port": "clk",
            "signal": "clk",
            "machine_readable": True,
        },
    ]
    assert out["integration"]["connection_contract_status"] == "approved_by_rtl_blocker_answer"
    assert out["sub_modules"][0]["connections"] == {"engine_done": "done", "clk": "clk"}
    assert out["sub_modules"][0]["connection_contract_status"] == "approved_by_rtl_blocker_answer"
    history = out["custom"]["rtl_connection_contract_resolution_history"]
    assert history[-1]["applied"] == [
        {"module": "demo_engine", "port": "engine_done", "signal": "done"},
        {"module": "demo_engine", "port": "clk", "signal": "clk"},
    ]
    assert history[-1]["submodule_updates"] == [
        {"module": "demo_engine", "port": "engine_done", "signal": "done"},
        {"module": "demo_engine", "port": "clk", "signal": "clk"},
    ]
    assert history[-1]["unresolved"] == []
    trace_fields = out["traceability"]["rtl_blocker_to_ssot"][-1]["ssot_fields"]
    assert "integration.connections" in trace_fields


def test_connection_contract_option_click_does_not_fabricate_wiring():
    resolver = _load_resolver()
    doc = {
        "integration": {"connections": []},
        "sub_modules": [
            {
                "name": "demo_engine",
                "file": "rtl/demo_engine.sv",
                "ownership": "manifest",
            }
        ],
    }
    blocker = {
        "questions": [
            {
                "id": "RTL_RESOLVE_CONNECTION_CONTRACTS",
                "required_fields": ["module", "port", "signal"],
            }
        ]
    }
    answers = [
        {
            "id": "RTL_RESOLVE_CONNECTION_CONTRACTS",
            "selected": ["recommended"],
            "answer": "Have ssot-gen repair integration.connections from approved wiring contracts.",
        }
    ]

    out = resolver.apply_answers(doc, blocker, answers)

    assert out["integration"]["connections"] == []
    assert "connections" not in out["sub_modules"][0]
    history = out["custom"]["rtl_connection_contract_resolution_history"]
    assert history[-1]["applied"] == []
    assert history[-1]["submodule_updates"] == []
    assert history[-1]["unresolved"] == []


def test_ssot_behavior_ownership_answer_projects_module_refs():
    resolver = _load_resolver()
    doc = {
        "sub_modules": [
            {
                "name": "demo_core",
                "file": "rtl/demo_core.sv",
                "ownership": "manifest",
                "implements": ["function_model"],
                "source_sections": ["function_model"],
                "function_model_refs": ["function_model.transactions.FM_PRIMARY"],
            }
        ]
    }
    blocker = {
        "questions": [
            {
                "id": "SSOT_BEHAVIOR_OWNERSHIP",
                "orphan_refs": ["decomposition.units.execute"],
                "candidate_modules": [{"name": "demo_core", "file": "rtl/demo_core.sv"}],
            }
        ]
    }
    answers = [
        {
            "id": "SSOT_BEHAVIOR_OWNERSHIP",
            "custom": """
module_contracts:
  - name: demo_core
    decomposition_refs: [decomposition.units.execute]
""",
        }
    ]

    out = resolver.apply_answers(doc, blocker, answers)
    core = out["sub_modules"][0]

    assert core["decomposition_refs"] == ["decomposition.units.execute"]
    history = out["custom"]["rtl_module_contract_resolution_history"]
    assert history[-1]["blocker_id"] == "SSOT_BEHAVIOR_OWNERSHIP"
    assert history[-1]["applied"][0]["fields"] == ["decomposition_refs"]


def test_dynamic_todo_ownership_answer_projects_module_refs():
    resolver = _load_resolver()
    doc = {
        "sub_modules": [
            {
                "name": "dma_engine",
                "file": "rtl/dma_engine.sv",
                "ownership": "manifest",
            }
        ]
    }
    blocker = {
        "questions": [
            {
                "id": "RTL_DYNAMIC_TODO_OWNERSHIP",
                "orphan_refs": ["function_model.transactions.FM_DMAGO"],
                "candidate_modules": [{"name": "dma_engine", "file": "rtl/dma_engine.sv"}],
                "required_fields": ["sub_modules[].function_model_refs"],
            }
        ]
    }
    answers = [
        {
            "id": "RTL_DYNAMIC_TODO_OWNERSHIP",
            "custom": """
module_contracts:
  - name: dma_engine
    function_model_refs: [function_model.transactions.FM_DMAGO]
    cycle_model_refs: [cycle_model.pipeline]
""",
        }
    ]

    out = resolver.apply_answers(doc, blocker, answers)
    engine = out["sub_modules"][0]

    assert engine["function_model_refs"] == ["function_model.transactions.FM_DMAGO"]
    assert engine["cycle_model_refs"] == ["cycle_model.pipeline"]
    history = out["custom"]["rtl_module_contract_resolution_history"]
    assert history[-1]["blocker_id"] == "RTL_DYNAMIC_TODO_OWNERSHIP"
    assert history[-1]["applied"][0]["name"] == "dma_engine"


def test_rtl_module_contract_option_click_does_not_fabricate_contracts():
    resolver = _load_resolver()
    doc = {
        "sub_modules": [
            {
                "name": "demo_decode",
                "file": "rtl/demo_decode.sv",
                "ownership": "manifest",
                "description": "decode block",
            }
        ]
    }
    blocker = {
        "questions": [
            {
                "id": "RTL_MODULE_CONTRACTS",
                "missing_modules": [{"name": "demo_decode", "file": "rtl/demo_decode.sv"}],
            }
        ]
    }
    answers = [
        {
            "id": "RTL_MODULE_CONTRACTS",
            "selected": ["recommended"],
            "answer": "Have ssot-gen repair sub_modules into a module contract ledger.",
        }
    ]

    out = resolver.apply_answers(doc, blocker, answers)

    assert "implements" not in out["sub_modules"][0]
    history = out["custom"]["rtl_module_contract_resolution_history"]
    assert history[-1]["applied"] == []
    assert history[-1]["unresolved"] == [
        {"name": "demo_decode", "reason": "no structured contract answer"}
    ]
