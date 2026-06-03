from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import threading
from pathlib import Path

import pytest
import yaml

from src.headless_workflow import (
    FakeLLMProvider,
    HeadlessWorkflowRunner,
    LLMResponse,
    RealLLMProvider,
    StageResult,
    _stable_json_sha256,
    _structured_ssot_yaml,
)
from src.workflow_stage_engine import StageEngineResult


FULL_STAGES = [
    "ssot-gen",
    "fl-model-gen",
    "cl-model-gen",
    "dual-fcov",
    "equiv-goals",
    "rtl-gen",
    "lint",
    "tb-gen",
    "sim",
    "coverage",
    "sim-debug",
    "contract-check",
    "goal-audit",
]


def _write_req(tmp_path: Path, ip: str, *, ambiguous: bool = False) -> Path:
    req = tmp_path / f"{ip}_req.md"
    base = (
        f"{ip} accepts a valid ready-style transaction after reset release. "
        "The input value is sampled only when valid is asserted, and the output "
        "result must equal twice the sampled input value on the next observable "
        "cycle. The ready output remains asserted after reset. The result_valid "
        "signal marks the result cycle. Invalid transactions report a deterministic "
        "error response without changing accepted_count. The functional model is "
        "the expected-behavior oracle for scoreboard rows, while the cycle model "
        "defines the sample and observation timing. DUT-only compile and lint "
        "evidence must pass before simulation evidence is accepted. Functional "
        "coverage must include the accepted datapath case, reset behavior, and "
        "the declared error behavior. FL-vs-RTL comparison must classify every "
        "mismatch to SSOT, FL model, RTL, TB, coverage, tool, or human gate. "
    )
    if ambiguous:
        base = (
            f"{ip} accepts transactions and has some error behavior that is not "
            "defined yet. A human must decide the invalid transaction response "
            "before SSOT signoff can proceed. "
        ) * 8
    req.write_text("# Requirement\n\n" + base * 5 + "\n", encoding="utf-8")
    return req


def _needs_sim_tools() -> None:
    if not shutil.which("iverilog"):
        pytest.skip("iverilog is required for generated cocotb simulation")
    pytest.importorskip("cocotb_test")


def test_rtl_packet_needs_llm_skips_locked_truth_only_packets(tmp_path: Path):
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="fake-contract-model",
        llm_provider=FakeLLMProvider(),
    )

    assert runner._rtl_packet_needs_llm(
        {
            "summary": {"open_required_count": 3},
            "execution_policy": {
                "llm_actionable_open_count": 0,
                "human_locked_open_count": 3,
            },
        }
    ) is False
    assert runner._rtl_packet_needs_llm(
        {
            "summary": {"open_required_count": 3},
            "execution_policy": {
                "llm_actionable_open_count": 1,
                "human_locked_open_count": 2,
            },
        }
    ) is True
    assert runner._rtl_packet_needs_llm(
        {
            "summary": {"open_required_count": 2},
            "execution_policy": {
                "llm_actionable_open_count": 0,
                "tool_evidence_open_count": 2,
            },
        }
    ) is False
    assert runner._rtl_packet_needs_llm(
        {
            "summary": {"open_required_count": 2},
            "execution_policy": {
                "llm_actionable_open_count": 0,
                "tool_evidence_open_count": 2,
                "blocked_by_tool_evidence": [
                    {"gate_kind": "dut_lint", "reason": "DUT lint artifact is not clean."}
                ],
            },
        }
    ) is True


def test_pipeline_continues_failed_sim_to_sim_debug_for_owner_routing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    ip = "sim_fail_owner_route_ip"
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="fake-contract-model",
        llm_provider=FakeLLMProvider(),
    )
    (runner.root / ip / "logs").mkdir(parents=True, exist_ok=True)
    calls: list[str] = []

    monkeypatch.setenv("ATLAS_HEADLESS_PIPELINE_MAX_ITERS", "1")
    monkeypatch.setattr(
        runner,
        "_pipeline_stage_list",
        lambda _ip, _context: ["sim", "coverage", "sim-debug"],
    )
    monkeypatch.setattr(
        runner,
        "_pipeline_repair_request",
        lambda _ip: {
            "owner": "fl-model-gen",
            "signature": "stale-oracle-signature",
            "items": [
                {
                    "classification": "stale_oracle",
                    "owner": "fl-model-gen",
                    "llm_loop_allowed": True,
                }
            ],
        },
    )

    def fake_execute(canonical: str, _ip: str, _context: dict) -> StageResult:
        calls.append(canonical)
        if canonical == "coverage":
            raise AssertionError("coverage should wait until sim-debug classifies failed sim evidence")
        if canonical == "sim":
            return StageResult("sim", "fail", "scoreboard failed", returncode=1)
        if canonical == "sim-debug":
            return StageResult("sim-debug", "fail", "owner classification ready", returncode=1)
        return StageResult(canonical, "pass", "pass")

    monkeypatch.setattr(runner, "_execute_canonical_stage", fake_execute)

    result = runner._stage_pipeline_converge(ip, {})

    assert calls == ["sim", "sim-debug"]
    assert result.stage == "pipeline"
    assert result.status == "blocked"
    assert "repair loop budget exhausted" in result.message
    review_files = list((runner.root / ip / "review").glob("decision_needed_pipeline_*.json"))
    assert review_files


def test_pipeline_repair_sequence_keeps_owner_when_stage_filter_excludes_it(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="fake-contract-model",
        llm_provider=FakeLLMProvider(),
    )

    monkeypatch.setenv("ATLAS_HEADLESS_PIPELINE_STAGES", "tb-gen,sim,sim-debug")

    assert runner._pipeline_repair_sequence("rtl-gen") == [
        "rtl-gen",
        "lint",
        "tb-gen",
        "sim",
        "sim-debug",
    ]


def test_rtl_packet_work_batch_respects_max_per_pass(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="fake-contract-model",
        llm_provider=FakeLLMProvider(),
    )
    plan = {
        "packets": [
            {"json": "rtl/authoring_packets/a.json", "execution_policy": {"llm_actionable_open_count": 1}},
            {"json": "rtl/authoring_packets/b.json", "execution_policy": {"llm_actionable_open_count": 2}},
            {"json": "rtl/authoring_packets/c.json", "execution_policy": {"llm_actionable_open_count": 0}},
        ]
    }

    monkeypatch.setenv("ATLAS_HEADLESS_RTL_PACKET_MAX_PER_PASS", "1")
    selected, batch = runner._rtl_packet_work_batch(plan)

    assert [packet["json"] for packet in selected] == ["rtl/authoring_packets/a.json"]
    assert batch["work_packets"] == 2
    assert batch["selected_packets"] == 1
    assert batch["deferred_work_packets"] == 1
    assert batch["packet_batch_limit"] == 1


def test_rtl_packet_work_batch_defaults_to_small_ui_batch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="fake-contract-model",
        llm_provider=FakeLLMProvider(),
    )
    monkeypatch.delenv("ATLAS_HEADLESS_RTL_PACKET_MAX_PER_PASS", raising=False)
    plan = {
        "packets": [
            {"json": f"rtl/authoring_packets/{idx}.json", "execution_policy": {"llm_actionable_open_count": 1}}
            for idx in range(6)
        ]
    }

    selected, batch = runner._rtl_packet_work_batch(plan)

    assert [packet["json"] for packet in selected] == [
        "rtl/authoring_packets/0.json",
        "rtl/authoring_packets/1.json",
        "rtl/authoring_packets/2.json",
        "rtl/authoring_packets/3.json",
    ]
    assert batch["work_packets"] == 6
    assert batch["selected_packets"] == 4
    assert batch["deferred_work_packets"] == 2
    assert batch["packet_batch_limit"] == 4


def test_rtl_packet_work_batch_mixes_missing_top_core_packets(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    ip = "missing_owner_packet_ip"
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="deepseek-v4-pro",
        llm_provider=FakeLLMProvider(),
    )
    ip_dir = tmp_path / "work" / ip
    (ip_dir / "rtl").mkdir(parents=True)
    (ip_dir / "rtl" / f"{ip}_regs.sv").write_text("module regs; endmodule\n", encoding="utf-8")
    monkeypatch.setenv("ATLAS_HEADLESS_RTL_PACKET_MAX_PER_PASS", "4")

    def packet(packet_id: str, owner_file: str, owner_module: str) -> dict:
        return {
            "packet_id": packet_id,
            "json": f"rtl/authoring_packets/{packet_id}.json",
            "kind": "module",
            "owner_file": owner_file,
            "owner_module": owner_module,
            "execution_policy": {"llm_actionable_open_count": 1},
        }

    plan = {
        "ip": ip,
        "summary": {
            "next_llm_packets": [
                "regs_a",
                "regs_b",
                "regs_c",
                "regs_d",
                f"module__{ip}_core",
                f"module__{ip}",
            ]
        },
        "packets": [
            packet("regs_a", f"rtl/{ip}_regs.sv", f"{ip}_regs"),
            packet("regs_b", f"rtl/{ip}_regs.sv", f"{ip}_regs"),
            packet("regs_c", f"rtl/{ip}_regs.sv", f"{ip}_regs"),
            packet("regs_d", f"rtl/{ip}_regs.sv", f"{ip}_regs"),
            packet(f"module__{ip}_core", f"rtl/{ip}_core.sv", f"{ip}_core"),
            packet(f"module__{ip}", f"rtl/{ip}.sv", ip),
        ],
    }

    selected, batch = runner._rtl_packet_work_batch(plan)

    assert [packet["packet_id"] for packet in selected] == [
        "regs_a",
        "regs_b",
        f"module__{ip}",
        f"module__{ip}_core",
    ]
    assert batch["selected_packets"] == 4
    assert batch["deferred_work_packets"] == 2


def test_rtl_packet_parallel_mode_runs_independent_module_packets_concurrently(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    ip = "parallel_packet_ip"
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="fake-contract-model",
        llm_provider=FakeLLMProvider(),
    )
    packets = [
        {
            "packet_id": "module__parallel_packet_ip_core",
            "kind": "module",
            "json": "rtl/authoring_packets/module__parallel_packet_ip_core.json",
            "owner_file": f"rtl/{ip}_core.sv",
            "summary": {"open_required_count": 1},
            "execution_policy": {"llm_actionable_open_count": 1},
        },
        {
            "packet_id": "module__parallel_packet_ip_irq",
            "kind": "module",
            "json": "rtl/authoring_packets/module__parallel_packet_ip_irq.json",
            "owner_file": f"rtl/{ip}_irq.sv",
            "summary": {"open_required_count": 1},
            "execution_policy": {"llm_actionable_open_count": 1},
        },
    ]
    barrier = threading.Barrier(2, timeout=2)
    refreshed: list[str] = []

    def fake_call(stage, ip_arg, context, **_kwargs):
        barrier.wait()
        packet_id = context["rtl_packet_id"]
        owner_file = context["rtl_packet_owner_file"]
        return LLMResponse(
            stage=stage,
            model="fake-contract-model",
            raw_response=json.dumps({"files": [{"path": f"{ip_arg}/{owner_file}", "content": f"// {packet_id}\n"}]}),
            parsed_artifacts=[{"path": f"{ip_arg}/{owner_file}", "content": f"// {packet_id}\n", "kind": "rtl"}],
        )

    monkeypatch.setenv("ATLAS_HEADLESS_RTL_PACKET_PARALLEL", "1")
    monkeypatch.setenv("ATLAS_HEADLESS_RTL_PACKET_PARALLEL_WORKERS", "2")
    monkeypatch.setattr(runner, "_rtl_authoring_plan", lambda _ip: {"packets": packets})
    monkeypatch.setattr(runner, "_rtl_packet_prompt", lambda *_args, **_kwargs: ("system", "prompt"))
    monkeypatch.setattr(runner, "_call_llm", fake_call)
    monkeypatch.setattr(runner, "_refresh_rtl_filelist_and_provenance", lambda _ip, packet_id="": refreshed.append(packet_id) or False)

    result = runner._run_rtl_packet_llm_pass(ip, {}, attempt=0)

    assert result is None
    assert refreshed == ["module__parallel_packet_ip_core", "module__parallel_packet_ip_irq"]
    assert (tmp_path / "work" / ip / "rtl" / f"{ip}_core.sv").read_text(encoding="utf-8") == "// module__parallel_packet_ip_core\n"
    assert (tmp_path / "work" / ip / "rtl" / f"{ip}_irq.sv").read_text(encoding="utf-8") == "// module__parallel_packet_ip_irq\n"
    progress = (tmp_path / "work" / ip / "logs" / "run_progress.jsonl").read_text(encoding="utf-8")
    assert "rtl_packet_parallel_start" in progress
    assert "rtl_packet_parallel_end" in progress


def test_rtl_packet_parallel_mode_rejects_shared_owner_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="fake-contract-model",
        llm_provider=FakeLLMProvider(),
    )
    monkeypatch.setenv("ATLAS_HEADLESS_RTL_PACKET_PARALLEL", "1")
    packets = [
        {"packet_id": "a", "kind": "module", "owner_file": "rtl/shared.sv"},
        {"packet_id": "b", "kind": "module", "owner_file": "rtl/shared.sv"},
    ]

    assert runner._rtl_packet_parallel_enabled(packets) is True
    assert runner._rtl_packets_parallel_safe(packets) is False


def test_ensure_generic_rtl_contract_recovers_noncanonical_llm_contract(tmp_path: Path):
    ip = "gpio_like"
    ip_dir = tmp_path / "work" / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "rtl").mkdir()
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        """
top_module:
  name: gpio_like
io_list:
  clock_domains:
    - name: clk
      ports:
        - {name: clk, direction: input, width: 1}
  resets:
    - name: rst_n
      ports:
        - {name: rst_n, direction: input, width: 1}
  interfaces:
    - name: bus
      ports:
        - {name: psel, direction: input, width: 1}
        - {name: prdata, direction: output, width: 32}
        - {name: pready, direction: output, width: 1}
function_model:
  state_variables:
    - {name: reg0, reset: 0, width: 32}
  transactions:
    - id: FM1
      outputs: ["prdata reflects selected register"]
cycle_model: {}
""",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / "rtl_contract.json").write_text(
        json.dumps({"ip": ip, "note": "LLM-authored noncanonical contract"}),
        encoding="utf-8",
    )
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="fake-contract-model",
        llm_provider=FakeLLMProvider(),
    )

    assert runner._ensure_generic_rtl_contract(ip) is True

    contract = json.loads((ip_dir / "rtl" / "rtl_contract.json").read_text(encoding="utf-8"))
    assert contract["type"] == "generic_ssot_rule_rtl_contract"
    assert contract["contract"]["clock"] == "clk"
    assert contract["contract"]["reset"] == "rst_n"
    assert contract["contract"]["reset_active"] == "low"
    assert {row["port"] for row in contract["contract"]["outputs"]} == {"prdata", "pready"}


def test_rtl_packet_work_batch_defers_evidence_closure_until_module_work_is_audited(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="fake-contract-model",
        llm_provider=FakeLLMProvider(),
    )
    monkeypatch.setenv("ATLAS_HEADLESS_RTL_PACKET_MAX_PER_PASS", "4")
    plan = {
        "packets": [
            {
                "packet_id": "module__demo__fsm",
                "json": "rtl/authoring_packets/module__demo__fsm.json",
                "execution_policy": {"llm_actionable_open_count": 1},
            },
            {
                "packet_id": "rtl_gate_evidence_closure",
                "json": "rtl/authoring_packets/rtl_gate_evidence_closure.json",
                "execution_policy": {"llm_actionable_open_count": 1},
            },
        ]
    }

    selected, batch = runner._rtl_packet_work_batch(plan)

    assert [packet["packet_id"] for packet in selected] == ["module__demo__fsm"]
    assert batch["work_packets"] == 2
    assert batch["selected_packets"] == 1
    assert batch["deferred_work_packets"] == 1


def test_rtl_packet_work_batch_allows_evidence_closure_when_it_is_the_only_work(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="fake-contract-model",
        llm_provider=FakeLLMProvider(),
    )
    monkeypatch.setenv("ATLAS_HEADLESS_RTL_PACKET_MAX_PER_PASS", "4")
    plan = {
        "packets": [
            {
                "packet_id": "rtl_gate_evidence_closure",
                "json": "rtl/authoring_packets/rtl_gate_evidence_closure.json",
                "execution_policy": {"llm_actionable_open_count": 1},
            }
        ]
    }

    selected, batch = runner._rtl_packet_work_batch(plan)

    assert [packet["packet_id"] for packet in selected] == ["rtl_gate_evidence_closure"]
    assert batch["work_packets"] == 1
    assert batch["selected_packets"] == 1
    assert batch["deferred_work_packets"] == 0


def test_rtl_packet_pass_budget_covers_large_deferred_queue(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="fake-contract-model",
        llm_provider=FakeLLMProvider(),
    )
    monkeypatch.setenv("ATLAS_HEADLESS_RTL_PACKET_MAX_PER_PASS", "4")
    monkeypatch.delenv("ATLAS_HEADLESS_RTL_PACKET_MAX_PASSES", raising=False)
    plan = {
        "packets": [
            {"json": f"rtl/authoring_packets/{idx}.json", "execution_policy": {"llm_actionable_open_count": 1}}
            for idx in range(13)
        ]
    }

    assert runner._rtl_packet_pass_budget(plan) == 6

    monkeypatch.setenv("ATLAS_HEADLESS_RTL_PACKET_MAX_PASSES", "9")
    assert runner._rtl_packet_pass_budget(plan) == 9


def test_rtl_packet_prompt_includes_reference_profile_digest(tmp_path: Path):
    ip = "packet_reference_profile_ip"
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="glm-5.1",
        llm_provider=FakeLLMProvider(),
    )
    ip_dir = tmp_path / "work" / ip
    packet_rel = "rtl/authoring_packets/module__core.json"
    packet_md_rel = "rtl/authoring_packets/module__core.md"
    (ip_dir / "rtl" / "authoring_packets").mkdir(parents=True, exist_ok=True)
    (ip_dir / packet_rel).write_text(
        json.dumps(
            {
                "packet_id": "module__core",
                "kind": "module",
                "owner_module": f"{ip}_core",
                "owner_file": f"rtl/{ip}.sv",
                "tasks": [],
            }
        ),
        encoding="utf-8",
    )
    (ip_dir / packet_md_rel).write_text("# Packet\n", encoding="utf-8")
    plan = {
        "type": "rtl_authoring_plan",
        "ip": ip,
        "top": ip,
        "summary": {"required_tasks": 120},
        "policy": {"rtl_quality_profile": "production"},
        "target_scale": {},
        "execution_policy": {"pass_allowed": False},
        "reference_profile": {
            "path": "reports/rtl_reference_profile.json",
            "summary": {"file_count": 143, "modules": 210, "lines": 130568},
            "target_candidate_basis": "design_candidate",
            "target_candidate_summary": {"file_count": 57, "modules": 52, "lines": 52338},
            "suggested_ssot_target_scale": {"source_files_min": 57, "modules_min": 52, "lines_min": 52338},
            "guidance": {
                "calibration_only": True,
                "do_not_copy_reference_rtl": True,
                "target_candidate_rule": "design candidate only",
            },
        },
        "packets": [
            {
                "packet_id": "module__core",
                "kind": "module",
                "owner_module": f"{ip}_core",
                "owner_file": f"rtl/{ip}.sv",
                "json": packet_rel,
                "markdown": packet_md_rel,
                "summary": {"required_count": 12, "open_required_count": 12},
                "execution_policy": {"llm_actionable_open_count": 12, "human_locked_open_count": 0},
            }
        ],
    }

    _, prompt = runner._rtl_packet_prompt(ip, {}, plan, plan["packets"][0], attempt=0)

    assert '"reference_profile"' in prompt
    assert '"target_candidate_basis": "design_candidate"' in prompt
    assert '"lines": 52338' in prompt
    assert '"source_files_min": 57' in prompt
    assert '"do_not_copy_reference_rtl": true' in prompt
    assert "pending connection_contract_suggestions" in prompt
    assert "draft RTL wiring candidates" in prompt


def test_rtl_packet_prompt_includes_observable_latency_contract(tmp_path: Path):
    ip = "packet_latency_ip"
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="glm-5.1",
        llm_provider=FakeLLMProvider(),
    )
    ip_dir = tmp_path / "work" / ip
    packet_rel = "rtl/authoring_packets/module__core.json"
    packet_md_rel = "rtl/authoring_packets/module__core.md"
    (ip_dir / "yaml").mkdir(parents=True, exist_ok=True)
    (ip_dir / "rtl" / "authoring_packets").mkdir(parents=True, exist_ok=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        _structured_ssot_yaml(ip, "sample data and produce the result after one observable cycle"),
        encoding="utf-8",
    )
    (ip_dir / packet_rel).write_text(
        json.dumps({"packet_id": "module__core", "owner_file": f"rtl/{ip}.sv"}),
        encoding="utf-8",
    )
    (ip_dir / packet_md_rel).write_text("# Packet\n", encoding="utf-8")
    plan = {
        "packets": [
            {
                "packet_id": "module__core",
                "kind": "module",
                "owner_module": ip,
                "owner_file": f"rtl/{ip}.sv",
                "json": packet_rel,
                "markdown": packet_md_rel,
                "summary": {"required_count": 1, "open_required_count": 1},
                "execution_policy": {"llm_actionable_open_count": 1},
            }
        ],
    }

    _, prompt = runner._rtl_packet_prompt(ip, {}, plan, plan["packets"][0], attempt=0)

    assert "SSOT observable latency contract" in prompt
    assert '"cycle_model.latency": 1' in prompt
    assert "latency=1 means" in prompt
    assert "input-register stage followed by a result-register stage is latency=2" in prompt
    assert "latency_1_required_rtl_shape" in prompt
    assert "forbidden latency-2 implementation" in prompt
    assert "Locked SSOT YAML excerpt" in prompt
    assert "You cannot read files from the repo during this turn" in prompt
    assert "do not return requires/missing-file JSON" in prompt
    assert "function_model:" in prompt


def test_rtl_packet_prompt_includes_tool_evidence_artifacts(tmp_path: Path):
    ip = "packet_tool_evidence_ip"
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="glm-5.1",
        llm_provider=FakeLLMProvider(),
    )
    ip_dir = tmp_path / "work" / ip
    packet_rel = "rtl/authoring_packets/rtl_gate_tool_evidence.json"
    packet_md_rel = "rtl/authoring_packets/rtl_gate_tool_evidence.md"
    (ip_dir / "rtl" / "authoring_packets").mkdir(parents=True, exist_ok=True)
    (ip_dir / "lint").mkdir(parents=True, exist_ok=True)
    (ip_dir / "rtl" / f"{ip}.sv").write_text(f"module {ip}; endmodule\n", encoding="utf-8")
    (ip_dir / "lint" / "dut_lint.json").write_text(
        json.dumps({"passed": False, "warnings": 1, "diagnostics": [{"rule": "UNUSEDPARAM"}]}),
        encoding="utf-8",
    )
    packet_doc = {
        "packet_id": "rtl_gate_tool_evidence",
        "kind": "gate",
        "owner_module": ip,
        "owner_file": f"rtl/{ip}.sv",
        "execution_policy": {
            "tool_evidence_plan": [
                {"artifacts": [f"{ip}/lint/dut_lint.json"], "gate_kind": "dut_lint"}
            ]
        },
    }
    (ip_dir / packet_rel).write_text(json.dumps(packet_doc), encoding="utf-8")
    (ip_dir / packet_md_rel).write_text("# Tool Evidence\n", encoding="utf-8")
    plan = {
        "type": "rtl_authoring_plan",
        "ip": ip,
        "top": ip,
        "packets": [
            {
                **packet_doc,
                "json": packet_rel,
                "markdown": packet_md_rel,
                "summary": {"required_count": 2, "open_required_count": 2},
                "execution_policy": {"llm_actionable_open_count": 1},
            }
        ],
    }

    _, prompt = runner._rtl_packet_prompt(ip, {}, plan, plan["packets"][0], attempt=1)

    assert "Current tool evidence artifacts referenced by this packet" in prompt
    assert f"### {ip}/lint/dut_lint.json" in prompt
    assert "UNUSEDPARAM" in prompt


def test_rtl_packet_prompt_includes_manifest_rtl_interface_digest(tmp_path: Path):
    ip = "interface_digest_ip"
    root = tmp_path / "work"
    ip_dir = root / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "rtl" / "authoring_packets").mkdir(parents=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        "\n".join(
                [
                    "top_module:",
                    f"  name: {ip}",
                    "error_handling:",
                    "  error_sources:",
                    "    - id: illegal_byte_access_pattern",
                    "      condition: none",
                    "sub_modules:",
                    f"  - name: {ip}",
                    f"    file: rtl/{ip}.sv",
                "    ownership: manifest",
                f"  - name: {ip}_child",
                f"    file: rtl/{ip}_child.sv",
                "    ownership: manifest",
                "filelist:",
                "  rtl:",
                f"    - rtl/{ip}.sv",
                f"    - rtl/{ip}_child.sv",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}.sv").write_text(
        f"module {ip}(input logic clk); endmodule\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}_child.sv").write_text(
        f"module {ip}_child(input logic clk, output logic done); endmodule\n",
        encoding="utf-8",
    )
    packet_rel = "rtl/authoring_packets/rtl_gate_evidence_closure.json"
    packet_md_rel = "rtl/authoring_packets/rtl_gate_evidence_closure.md"
    (ip_dir / packet_rel).write_text('{"execution_policy":{}}\n', encoding="utf-8")
    (ip_dir / packet_md_rel).write_text("# evidence closure\n", encoding="utf-8")
    packet = {
        "packet_id": "rtl_gate_evidence_closure",
        "kind": "gate",
        "json": packet_rel,
        "markdown": packet_md_rel,
        "owner_file": f"rtl/{ip}.sv",
        "summary": {"open_required_count": 1},
        "execution_policy": {"llm_actionable_open_count": 1},
    }
    runner = HeadlessWorkflowRunner(root=root, model="fake-contract-model", llm_provider=FakeLLMProvider())

    _, prompt = runner._rtl_packet_prompt(ip, {}, {"packets": [packet]}, packet, attempt=1)

    assert "Current RTL module interface digest" in prompt
    assert f"module {ip}_child" in prompt
    assert "output logic done" in prompt


def test_rtl_gate_packet_prompt_includes_audit_digest_and_all_rtl_snapshots(tmp_path: Path):
    ip = "gate_snapshot_ip"
    root = tmp_path / "work"
    ip_dir = root / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "rtl" / "authoring_packets").mkdir(parents=True)
    (ip_dir / "lint").mkdir(parents=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        "\n".join(
            [
                "top_module:",
                f"  name: {ip}",
                "error_handling:",
                "  error_sources:",
                "  - id: illegal_byte_access_pattern",
                "    condition: none",
                "sub_modules:",
                f"  - name: {ip}",
                f"    file: rtl/{ip}.sv",
                "    ownership: manifest",
                f"  - name: {ip}_apb",
                f"    file: rtl/{ip}_apb.sv",
                "    ownership: manifest",
                f"  - name: {ip}_irq",
                f"    file: rtl/{ip}_irq.sv",
                "    ownership: manifest",
                "filelist:",
                "  rtl:",
                f"    - rtl/{ip}.sv",
                f"    - rtl/{ip}_apb.sv",
                f"    - rtl/{ip}_irq.sv",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}.sv").write_text(f"module {ip}; endmodule\n", encoding="utf-8")
    (ip_dir / "rtl" / f"{ip}_apb.sv").write_text(
        f"module {ip}_apb(input logic [31:0] pwdata); always @(posedge pwdata[0]) apb_w1c_mask <= pwdata[GPIO_WIDTH-1:0]; endmodule\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}_irq.sv").write_text(
        f"module {ip}_irq; logic [7:0] reg_irq_status_set_next; endmodule\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / "rtl_compile.json").write_text(
        json.dumps(
            {
                "passed": False,
                "returncode": 0,
                "errors": 0,
                "diagnostics": 0,
                "style_violations": 1,
                "style_violation_details": [
                    {
                        "file": f"rtl/{ip}_apb.sv",
                        "line": 1,
                        "rule": "no_parameterized_part_select_in_procedural_block",
                        "text": "apb_w1c_mask <= pwdata[GPIO_WIDTH-1:0];",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (ip_dir / "lint" / "dut_lint.json").write_text(
        json.dumps(
            {
                "passed": False,
                "returncode": 1,
                "errors": 0,
                "warnings": 1,
                "tool_results": [
                    {
                        "tool": "verilator",
                        "diagnostics": [
                            {
                                "rule": "UNUSEDSIGNAL",
                                "file": f"rtl/{ip}_irq.sv",
                                "message": "Signal is not used: reg_irq_status_set_next",
                            },
                            {
                                "rule": "UNUSEDSIGNAL",
                                "file": f"rtl/{ip}_apb.sv",
                                "line": 22,
                                "message": "Bits of signal are not used: 'reg_data_out_next_word'[31:8]",
                                "source": "logic [31:0] reg_data_out_next_word;",
                            },
                            {
                                "rule": "UNUSEDSIGNAL",
                                "file": f"rtl/{ip}_apb.sv",
                                "line": 12,
                                "message": "Bits of signal are not used: 'pwdata'[31:8]",
                                "source": "input logic [31:0] pwdata,",
                            },
                            {
                                "rule": "UNUSEDSIGNAL",
                                "file": f"rtl/{ip}_apb.sv",
                                "line": 44,
                                "message": "Signal is not used: 'no_apb_backpressure_generated'",
                                "source": "logic no_apb_backpressure_generated;",
                            },
                            {
                                "rule": "UNUSEDSIGNAL",
                                "file": f"rtl/{ip}_top_int.sv",
                                "line": 58,
                                "message": "Bits of signal are not used: 'data_out_reserved_zero'[31:16]",
                                "source": "logic [DATA_WIDTH-1:0] data_out_reserved_zero;",
                            },
                            {
                                "rule": "WIDTHEXPAND",
                                "file": f"rtl/{ip}_top_int.sv",
                                "line": 89,
                                "message": "Output port connection 'data_out_reg' expects 32 bits on the pin connection, but pin connection's VARREF 'data_out_reg_full' generates 16 bits.",
                                "source": ".data_out_reg(data_out_reg_full),",
                            },
                            {
                                "rule": "UNUSEDSIGNAL",
                                "file": f"rtl/{ip}_apb.sv",
                                "line": 45,
                                "message": "Signal is not used: 'every_function_model_transaction_has_cycle_model_stage_mapping'",
                                "source": "logic every_function_model_transaction_has_cycle_model_stage_mapping;",
                            }
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (ip_dir / "rtl" / "rtl_todo_plan.json").write_text(
        json.dumps(
            {
                "gate": {"status": "fail", "open_required_todos": 2, "static_missing": 1},
                "todo_completion": {
                    "open_tasks": [
                        {
                            "task_id": "RTL-0114",
                            "source_ref": "cycle_model.ordering.ordering_rule_0",
                            "reason": "Required RTL static evidence is missing.",
                        }
                    ]
                },
                "static_rtl_evidence": {
                    "missing_tasks": [
                        {
                            "task_id": "RTL-0114",
                            "owner_file": f"rtl/{ip}_irq.sv",
                            "terms": ["set_and_clear_same_bit_same_observation_window_is_set_dominant"],
                        }
                    ]
                },
                "manifest_signal_flow_evidence": {
                    "issues": [
                        {
                            "module": f"{ip}_irq",
                            "port": "irq_status_core",
                            "issue": "output does not feed parent logic",
                        }
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    packet_rel = "rtl/authoring_packets/rtl_gate_tool_evidence.json"
    packet_md_rel = "rtl/authoring_packets/rtl_gate_tool_evidence.md"
    (ip_dir / packet_rel).write_text(
        json.dumps(
            {
                "packet_id": "rtl_gate_tool_evidence",
                "kind": "gate",
                "owner_file": f"rtl/{ip}.sv",
                "execution_policy": {
                    "tool_evidence_plan": [
                        {
                            "gate_kind": "dut_compile",
                            "artifacts": [f"{ip}/rtl/rtl_compile.json", f"{ip}/lint/dut_lint.json"],
                        }
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    (ip_dir / packet_md_rel).write_text("# gate tool evidence\n", encoding="utf-8")
    packet = {
        "packet_id": "rtl_gate_tool_evidence",
        "kind": "gate",
        "json": packet_rel,
        "markdown": packet_md_rel,
        "owner_file": f"rtl/{ip}.sv",
        "summary": {"open_required_count": 2},
        "execution_policy": {"llm_actionable_open_count": 1},
    }
    runner = HeadlessWorkflowRunner(root=root, model="fake-contract-model", llm_provider=FakeLLMProvider())

    _, prompt = runner._rtl_packet_prompt(ip, {}, {"packets": [packet]}, packet, attempt=1)

    assert "Current RTL gate audit digest" in prompt
    assert "Current mandatory lint repair directives" in prompt
    assert "SSOT bus/byte-lane policy" in prompt
    assert '"illegal_byte_access_pattern_condition": "none"' in prompt
    assert "upper byte lanes are not an APB error for legal offsets" in prompt
    assert "Current RTL file snapshots for gate/tool-evidence repair" in prompt
    assert "Gate/tool-evidence packets may edit any declared RTL file" in prompt
    assert f"### rtl/{ip}_apb.sv" in prompt
    assert f"### rtl/{ip}_irq.sv" in prompt
    assert "no_parameterized_part_select_in_procedural_block" in prompt
    assert "UNUSEDSIGNAL" in prompt
    assert "repair_hints" in prompt
    assert "reg_data_out_next_word" in prompt
    assert "narrow the helper to the actual consumed width" in prompt
    assert "Do not narrow an externally defined bus port" in prompt
    assert "Only assert a bus error when" in prompt
    assert "Do not add marker-only reduction wires" in prompt
    assert "mechanical_fix" in prompt
    assert "logic [GPIO_WIDTH-1:0]" in prompt
    assert "completion_condition" in prompt
    assert "Adding a second narrower copy" in prompt
    assert "renaming or copying the signal" in prompt
    assert "producer[GPIO_WIDTH-1:0]" in prompt
    assert "another DATA_WIDTH masked/full helper" in prompt
    assert "WIDTHEXPAND" in prompt
    assert "producer module port declaration" in prompt
    assert "child port still expects the old width" in prompt
    assert "Static evidence terms are search/audit hints, not required signal names" in prompt
    assert "no_apb_backpressure_generated" in prompt
    assert "static-evidence marker signal" in prompt
    assert "Do not declare signals whose only purpose is to match static evidence terms" in prompt
    assert "set_and_clear_same_bit_same_observation_window_is_set_dominant" in prompt
    assert "apb_w1c_mask <= pwdata[GPIO_WIDTH-1:0];" in prompt


def test_rtl_packet_prompt_includes_sim_debug_repair_evidence(tmp_path: Path):
    ip = "packet_repair_evidence_ip"
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="glm-5.1",
        llm_provider=FakeLLMProvider(),
    )
    ip_dir = tmp_path / "work" / ip
    packet_rel = "rtl/authoring_packets/module__core.json"
    packet_md_rel = "rtl/authoring_packets/module__core.md"
    (ip_dir / "rtl" / "authoring_packets").mkdir(parents=True, exist_ok=True)
    (ip_dir / "sim").mkdir(parents=True, exist_ok=True)
    (ip_dir / packet_rel).write_text(
        json.dumps({"packet_id": "module__core", "owner_file": f"rtl/{ip}.sv"}),
        encoding="utf-8",
    )
    (ip_dir / packet_md_rel).write_text("# Packet\n", encoding="utf-8")
    (ip_dir / "sim" / "mismatch_classification.json").write_text(
        json.dumps(
            {
                "type": "mismatch_classification",
                "classifications": [
                    {
                        "goal_id": "EQ_GPIO_READBACK",
                        "classification": "rtl_bug",
                        "owner": "rtl-gen",
                        "llm_loop_allowed": True,
                        "reason": "readback returned zero",
                        "repair_prompt": "Repair RTL for EQ_GPIO_READBACK using expected/observed evidence.",
                        "evidence": {
                            "ssot_refs": ["function_model.transactions.FM_READ.output_rules.prdata"],
                            "fl_expected": {"prdata": 90},
                            "rtl_observed": {"prdata": 0},
                            "scoreboard_rows": [
                                {
                                    "goal_id": "EQ_GPIO_READBACK",
                                    "fl_expected": {"prdata": 90},
                                    "rtl_observed": {"prdata": 0},
                                }
                            ],
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    plan = {
        "packets": [
            {
                "packet_id": "module__core",
                "kind": "module",
                "owner_module": f"{ip}_core",
                "owner_file": f"rtl/{ip}.sv",
                "json": packet_rel,
                "markdown": packet_md_rel,
                "summary": {"required_count": 1, "open_required_count": 1},
                "execution_policy": {"llm_actionable_open_count": 1},
            }
        ],
    }

    _, prompt = runner._rtl_packet_prompt(ip, {}, plan, plan["packets"][0], attempt=1)

    assert "Current sim-debug owner repair evidence" in prompt
    assert f"{ip}/sim/mismatch_classification.json" in prompt
    assert "EQ_GPIO_READBACK" in prompt
    assert "Repair RTL for EQ_GPIO_READBACK" in prompt
    assert '"fl_expected"' in prompt
    assert '"rtl_observed"' in prompt


def test_rtl_packet_work_batch_reopens_closed_module_packets_for_fresh_sim_debug_repair(tmp_path: Path):
    ip = "packet_repair_reopen_ip"
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="gpt-5.3-codex",
        llm_provider=FakeLLMProvider(),
    )
    ip_dir = tmp_path / "work" / ip
    (ip_dir / "rtl").mkdir(parents=True, exist_ok=True)
    (ip_dir / "sim").mkdir(parents=True, exist_ok=True)
    rtl_path = ip_dir / "rtl" / f"{ip}.sv"
    rtl_path.write_text("module packet_repair_reopen_ip; endmodule\n", encoding="utf-8")
    mismatch_path = ip_dir / "sim" / "mismatch_classification.json"
    mismatch_path.write_text(
        json.dumps(
            {
                "classifications": [
                    {
                        "goal_id": "EQ_GPIO_READBACK",
                        "classification": "rtl_bug",
                        "owner": "rtl-gen",
                        "llm_loop_allowed": True,
                        "reason": "readback returned zero",
                        "repair_prompt": "Repair RTL readback from scoreboard evidence.",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    now = rtl_path.stat().st_mtime
    os.utime(mismatch_path, (now + 10, now + 10))
    plan = {
        "ip": ip,
        "packets": [
            {
                "packet_id": "module__core",
                "kind": "module",
                "owner_file": f"rtl/{ip}.sv",
                "json": "rtl/authoring_packets/module__core.json",
                "summary": {"required_count": 4, "open_required_count": 0},
                "execution_policy": {"llm_actionable_open_count": 0},
            }
        ],
    }

    work_packets, batch = runner._rtl_packet_work_batch(plan)

    assert [packet["packet_id"] for packet in work_packets] == ["module__core"]
    assert batch["work_packets"] == 1
    assert batch["skipped_closed_packets"] == 0


def test_headless_runner_regenerates_generic_rtl_contract_from_ssot(tmp_path: Path):
    ip = "contract_restore_ip"
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="fake-contract-model",
        llm_provider=FakeLLMProvider(),
    )
    ip_dir = tmp_path / "work" / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "rtl").mkdir()
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        _structured_ssot_yaml(ip, "double a sampled input after one cycle"),
        encoding="utf-8",
    )
    (ip_dir / "rtl" / "rtl_contract.json").write_text(
        json.dumps({"pipeline": {"stages": ["S0_SAMPLE", "S1_RESULT"]}}),
        encoding="utf-8",
    )

    changed = runner._ensure_generic_rtl_contract(ip)
    restored = json.loads((ip_dir / "rtl" / "rtl_contract.json").read_text(encoding="utf-8"))

    assert changed is True
    assert restored["type"] == "generic_ssot_rule_rtl_contract"
    assert restored["contract"]["sample_condition"] == "valid && ready"
    assert restored["contract"]["input_map"] == {"value": "data_in"}
    assert restored["contract"]["outputs"][0]["port"] == "result"


def test_rtl_packet_mode_uses_rtl_workflow_system_prompt(tmp_path: Path):
    ip = "packet_workflow_prompt_ip"
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="glm-5.1",
        llm_provider=FakeLLMProvider(),
    )
    ip_dir = tmp_path / "work" / ip
    packet_rel = "rtl/authoring_packets/module__core.json"
    packet_md_rel = "rtl/authoring_packets/module__core.md"
    (ip_dir / "rtl" / "authoring_packets").mkdir(parents=True, exist_ok=True)
    (ip_dir / packet_rel).write_text(
        json.dumps({"packet_id": "module__core", "owner_file": f"rtl/{ip}.sv"}),
        encoding="utf-8",
    )
    (ip_dir / packet_md_rel).write_text("# Packet\n", encoding="utf-8")
    plan = {
        "packets": [
            {
                "packet_id": "module__core",
                "kind": "module",
                "owner_module": f"{ip}_core",
                "owner_file": f"rtl/{ip}.sv",
                "json": packet_rel,
                "markdown": packet_md_rel,
                "summary": {"required_count": 1, "open_required_count": 1},
                "execution_policy": {"llm_actionable_open_count": 1},
            }
        ],
    }

    system, prompt = runner._rtl_packet_prompt(ip, {}, plan, plan["packets"][0], attempt=0)

    assert "# RTL Generation Agent Rules" in system
    assert "For production ATLAS flows" in system
    assert "RTL-GEN PACKET MODE" in prompt


def test_headless_llm_stages_use_their_workflow_system_prompts(tmp_path: Path):
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="glm-5.1",
        llm_provider=FakeLLMProvider(),
    )

    ssot_system, ssot_prompt = runner._stage_prompt("ssot-gen", "demo_ip", {"requirement_text": "demo"})
    rtl_system, rtl_prompt = runner._stage_prompt("rtl-gen", "demo_ip", {})
    tb_system, tb_prompt = runner._stage_prompt("tb-gen", "demo_ip", {})

    assert "# SSOT Generator Agent" in ssot_system
    assert "This workflow owns the SSOT contract only." in ssot_system
    assert "Generate canonical SSOT YAML" in ssot_prompt
    assert "# RTL Generation Agent Rules" in rtl_system
    assert "Prepare rtl-gen" in rtl_prompt
    assert "# TB Generation Agent Rules" in tb_system
    assert "Prepare tb-gen" in tb_prompt


def test_rtl_todo_stable_hash_ignores_generated_diagnostics(tmp_path: Path):
    todo_path = tmp_path / "rtl_todo_plan.json"
    base_plan = {
        "type": "rtl_todo_plan",
        "ip": "hash_probe",
        "policy": {"rtl_quality_profile": "production", "rtl_target_scale": {"status": "human_locked"}},
        "tasks": [
            {
                "id": "RTL-0001",
                "content": "Implement the locked datapath contract.",
                "gate_todo": {"kind": "module_logic", "source": "ssot"},
                "todo_completion": {"status": "open", "reason": "initial audit"},
            }
        ],
        "generated_at": "2026-05-07T00:00:00Z",
        "gate": {"status": "fail", "open_required_count": 1},
        "reference_profile": {"summary": {"modules": 52, "lines": 52338}},
        "reference_scale_gap": {"metrics": {"modules": {"actual": 1, "reference": 52}}},
        "connection_contract_suggestions": {"summary": {"pending_review": 399}},
        "static_evidence": {"checked_files": ["rtl/hash_probe.sv"]},
    }
    todo_path.write_text(json.dumps(base_plan, indent=2) + "\n", encoding="utf-8")
    base_hash = _stable_json_sha256(todo_path)

    diagnostics_only = json.loads(json.dumps(base_plan))
    diagnostics_only["generated_at"] = "2026-05-07T00:01:00Z"
    diagnostics_only["gate"] = {"status": "pass", "open_required_count": 0}
    diagnostics_only["reference_profile"] = {"summary": {"modules": 999, "lines": 999999}}
    diagnostics_only["reference_scale_gap"] = {"metrics": {"modules": {"actual": 10, "reference": 52}}}
    diagnostics_only["connection_contract_suggestions"] = {"summary": {"pending_review": 0}}
    diagnostics_only["tasks"][0]["todo_completion"] = {"status": "done", "reason": "diagnostic replay"}
    todo_path.write_text(json.dumps(diagnostics_only, indent=2) + "\n", encoding="utf-8")

    assert _stable_json_sha256(todo_path) == base_hash

    contract_change = json.loads(json.dumps(base_plan))
    contract_change["tasks"][0]["content"] = "Implement a different locked datapath contract."
    todo_path.write_text(json.dumps(contract_change, indent=2) + "\n", encoding="utf-8")

    assert _stable_json_sha256(todo_path) != base_hash


def test_rtl_provenance_refresh_uses_current_todo_hash_and_manifest_files(tmp_path: Path):
    ip = "refresh_probe"
    root = tmp_path / "work"
    ip_dir = root / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "rtl").mkdir(parents=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        "\n".join(
            [
                "top_module:",
                f"  name: {ip}",
                "sub_modules:",
                f"  - name: {ip}",
                f"    file: rtl/{ip}.sv",
                "    ownership: manifest",
                f"  - name: {ip}_engine",
                f"    file: rtl/{ip}_engine.sv",
                "    ownership: manifest",
                "filelist:",
                "  rtl:",
                f"    - rtl/{ip}.sv",
                f"    - rtl/{ip}_engine.sv",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / f"{ip}.sv").write_text(f"module {ip}; endmodule\n", encoding="utf-8")
    (ip_dir / "rtl" / f"{ip}_engine.sv").write_text(f"module {ip}_engine; endmodule\n", encoding="utf-8")
    todo_path = ip_dir / "rtl" / "rtl_todo_plan.json"
    todo_path.write_text('{"type":"rtl_todo_plan","tasks":[{"id":"RTL-0001"}]}\n', encoding="utf-8")
    (ip_dir / "rtl" / "rtl_authoring_plan.json").write_text('{"todo_plan_sha256":"old"}\n', encoding="utf-8")
    (ip_dir / "rtl" / "rtl_authoring_provenance.json").write_text(
        '{"type":"rtl_authoring_provenance","todo_plan_sha256":"stale"}\n',
        encoding="utf-8",
    )
    runner = HeadlessWorkflowRunner(root=root, model="fake-contract-model", llm_provider=FakeLLMProvider())

    assert runner._refresh_rtl_filelist_and_provenance(ip, packet_id="packet_a") is True

    provenance = json.loads((ip_dir / "rtl" / "rtl_authoring_provenance.json").read_text(encoding="utf-8"))
    assert provenance["todo_plan_sha256"] == _stable_json_sha256(todo_path)
    assert provenance["rtl_files"] == [f"rtl/{ip}.sv", f"rtl/{ip}_engine.sv"]
    assert provenance["authoring_packets"] == ["packet_a"]
    assert (ip_dir / "list" / f"{ip}.f").read_text(encoding="utf-8").splitlines() == [
        f"rtl/{ip}.sv",
        f"rtl/{ip}_engine.sv",
    ]


def test_rtl_repairability_allows_target_scale_plus_llm_work(tmp_path: Path):
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="fake-contract-model",
        llm_provider=FakeLLMProvider(),
    )
    result = StageEngineResult(
        stage="ssot-rtl",
        ip="pl330_like",
        status="human_gate",
        headline="[RTL BLOCKED]",
        message="rtl-gen waiting for LLM-authored RTL",
        metadata={
            "rtl_blocked": {
                "questions": [
                    {"id": "LLM_RTL_IMPLEMENTATION_REQUIRED"},
                    {"id": "RTL_TARGET_SCALE_POLICY"},
                ]
            }
        },
    )

    assert runner._rtl_result_repairable_by_llm(result) is True


def test_rtl_repairability_does_not_treat_target_scale_only_as_llm_work(tmp_path: Path):
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="fake-contract-model",
        llm_provider=FakeLLMProvider(),
    )
    result = StageEngineResult(
        stage="ssot-rtl",
        ip="pl330_like",
        status="human_gate",
        headline="[RTL BLOCKED]",
        message="rtl-gen waiting for target scale",
        metadata={"rtl_blocked": {"questions": [{"id": "RTL_TARGET_SCALE_POLICY"}]}},
    )

    assert runner._rtl_result_repairable_by_llm(result) is False


def test_rtl_repairability_continues_target_scale_draft_when_packets_remain(tmp_path: Path):
    ip = "pl330_like"
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="fake-contract-model",
        llm_provider=FakeLLMProvider(),
    )
    rtl_dir = tmp_path / "work" / ip / "rtl"
    rtl_dir.mkdir(parents=True)
    (rtl_dir / "rtl_authoring_plan.json").write_text(
        json.dumps(
            {
                "execution_policy": {
                    "draft_allowed": True,
                    "deferred_human_qa_allowed": True,
                },
                "packets": [
                    {
                        "packet_id": "module__pl330_like_core",
                        "kind": "module",
                        "json": "rtl/authoring_packets/module__pl330_like_core.json",
                        "summary": {"open_required_count": 1},
                        "execution_policy": {"llm_actionable_open_count": 1},
                    }
                ],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    result = StageEngineResult(
        stage="ssot-rtl",
        ip=ip,
        status="human_gate",
        headline="[RTL BLOCKED]",
        message="rtl-gen waiting for target scale",
        metadata={"rtl_blocked": {"questions": [{"id": "RTL_TARGET_SCALE_POLICY"}]}},
    )

    assert runner._rtl_result_repairable_by_llm(result) is True


def test_llm_provider_empty_output_is_retryable_blocker_not_human_gate(tmp_path: Path):
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="fake-contract-model",
        llm_provider=FakeLLMProvider(),
    )
    result = runner._append_llm_gate(
        "packet_ip",
        "rtl-gen",
        LLMResponse(stage="rtl-gen", model="fake-contract-model", raw_response="", error="empty output", status="blocked"),
        topic="packet_module",
    )

    assert result.status == "blocked"
    assert result.blocker == ""
    assert not (tmp_path / "work" / "packet_ip" / "questions" / "rtl_gen_packet_module.json").exists()


def test_pipeline_repair_request_prefers_majority_owner_over_static_priority(tmp_path: Path):
    ip = "mixed_owner_ip"
    root = tmp_path / "work"
    sim_dir = root / ip / "sim"
    sim_dir.mkdir(parents=True)
    classifications = []
    for idx in range(3):
        classifications.append(
            {
                "goal_id": f"EQ_TB_{idx}",
                "classification": "tb_bug",
                "owner": "tb-gen",
                "llm_loop_allowed": True,
                "repair_prompt": "Repair TB stimulus",
                "reason": "missing APB stimulus",
            }
        )
    classifications.append(
        {
            "goal_id": "EQ_RTL_0",
            "classification": "rtl_bug",
            "owner": "rtl-gen",
            "llm_loop_allowed": True,
            "repair_prompt": "Repair RTL",
            "reason": "one RTL mismatch",
        }
    )
    (sim_dir / "mismatch_classification.json").write_text(
        json.dumps({"classifications": classifications}) + "\n",
        encoding="utf-8",
    )
    runner = HeadlessWorkflowRunner(root=root, model="fake-contract-model", llm_provider=FakeLLMProvider())

    request = runner._pipeline_repair_request(ip)

    assert request["owner"] == "tb-gen"
    assert request["goal_ids"] == ["EQ_TB_0", "EQ_TB_1", "EQ_TB_2"]


def test_rtl_packet_pass_without_artifacts_is_retryable_blocker(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    ip = "packet_no_artifact_ip"
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="fake-contract-model",
        llm_provider=FakeLLMProvider(),
    )
    packet = {
        "packet_id": "module__packet_no_artifact_ip_core",
        "kind": "module",
        "json": "rtl/authoring_packets/module__packet_no_artifact_ip_core.json",
        "summary": {"open_required_count": 1},
        "execution_policy": {"llm_actionable_open_count": 1},
    }
    monkeypatch.setattr(runner, "_rtl_authoring_plan", lambda _ip: {"packets": [packet]})
    monkeypatch.setattr(runner, "_rtl_packet_prompt", lambda *_args, **_kwargs: ("system", "prompt"))
    monkeypatch.setattr(
        runner,
        "_call_llm",
        lambda *_args, **_kwargs: LLMResponse(
            stage="rtl-gen",
            model="fake-contract-model",
            raw_response='{"files": [',
            parsed_artifacts=[],
        ),
    )

    result = runner._run_rtl_packet_llm_pass(ip, {}, attempt=0)

    assert result is not None
    assert result.status == "blocked"
    assert "produced no files[] artifacts" in result.message
    assert runner.stages[-1] == result


def test_rtl_packet_empty_files_response_is_noop(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    ip = "packet_empty_files_ip"
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="fake-contract-model",
        llm_provider=FakeLLMProvider(),
    )
    packet = {
        "packet_id": "module__packet_empty_files_ip_core",
        "kind": "module",
        "json": "rtl/authoring_packets/module__packet_empty_files_ip_core.json",
        "summary": {"open_required_count": 1},
        "execution_policy": {"llm_actionable_open_count": 1},
    }
    monkeypatch.setattr(runner, "_rtl_authoring_plan", lambda _ip: {"packets": [packet]})
    monkeypatch.setattr(runner, "_rtl_packet_prompt", lambda *_args, **_kwargs: ("system", "prompt"))
    monkeypatch.setattr(
        runner,
        "_call_llm",
        lambda *_args, **_kwargs: LLMResponse(
            stage="rtl-gen",
            model="fake-contract-model",
            raw_response='{"files": []}',
            parsed_artifacts=[],
            error="model output did not contain expected JSON object with files[] rtl-gen artifact",
            status="blocked",
        ),
    )

    result = runner._run_rtl_packet_llm_pass(ip, {}, attempt=0)

    assert result is None
    assert runner.stages == []


def test_real_llm_rtl_gen_without_artifacts_blocks(monkeypatch: pytest.MonkeyPatch):
    def fake_run(*_args, **_kwargs) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps({"raw": '{"files": ['}) + "\n",
            stderr="",
        )

    monkeypatch.setenv("ATLAS_RUN_REAL_LLM_TDD", "1")
    monkeypatch.setenv("ZAI_API_KEY", "test-key")
    monkeypatch.setattr("src.headless_workflow.subprocess.run", fake_run)

    response = RealLLMProvider().complete(
        stage="rtl-gen",
        model="glm-5.1",
        system_prompt="",
        prompt="",
        context={"ip": "packet_no_artifact_ip"},
    )

    assert response.status == "blocked"
    assert "files[] rtl-gen artifact" in response.error


def test_real_llm_provider_retries_malformed_artifact_response(monkeypatch: pytest.MonkeyPatch):
    calls = {"count": 0}

    def fake_run(*_args, **_kwargs) -> subprocess.CompletedProcess[str]:
        calls["count"] += 1
        if calls["count"] == 1:
            raw = '{"files": [{"path": "retry_ip/rtl/retry_ip.sv", "kind": "rtl", "content": "module retry_ip;'
        else:
            raw = json.dumps(
                {
                    "files": [
                        {
                            "path": "retry_ip/rtl/retry_ip.sv",
                            "kind": "rtl",
                            "content": "module retry_ip; endmodule\n",
                        }
                    ]
                }
            )
        return subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps({"raw": raw, "usage": {}, "cost": {}}) + "\n",
            stderr="",
        )

    monkeypatch.setenv("ATLAS_RUN_REAL_LLM_TDD", "1")
    monkeypatch.setenv("ZAI_API_KEY", "test-key")
    monkeypatch.setenv("ATLAS_HEADLESS_LLM_RETRIES", "1")
    monkeypatch.setenv("ATLAS_HEADLESS_LLM_RETRY_BACKOFF_S", "0")
    monkeypatch.setattr("src.headless_workflow.subprocess.run", fake_run)

    response = RealLLMProvider().complete(
        stage="rtl-gen",
        model="glm-5.1",
        system_prompt="",
        prompt="",
        context={"ip": "retry_ip"},
    )

    assert response.status == "pass"
    assert calls["count"] == 2
    assert response.parsed_artifacts == [
        {"path": "retry_ip/rtl/retry_ip.sv", "content": "module retry_ip; endmodule\n", "kind": "rtl"}
    ]


def test_real_llm_provider_resolves_profile_model(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ATLAS_RUN_REAL_LLM_TDD", "1")
    monkeypatch.setenv("PROFILE_deepseek_BASE_URL", "https://api.deepseek.com")
    monkeypatch.setenv("PROFILE_deepseek_API_KEY", "test-key")
    monkeypatch.setenv("PROFILE_deepseek_MODEL", "deepseek-v4-pro")
    monkeypatch.delenv("LLM_API_KEY", raising=False)

    provider = RealLLMProvider()
    resolved_model, profile_name = provider._activate_requested_model("deepseek")

    assert resolved_model == "deepseek-v4-pro"
    assert profile_name == "deepseek"
    assert provider.available_reason("deepseek") == ""


def test_real_llm_provider_defaults_artifact_reasoning_to_none(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("ATLAS_HEADLESS_LLM_REASONING_EFFORT", raising=False)
    monkeypatch.delenv("ATLAS_HEADLESS_LLM_REASONING_EFFORT_SSOT_GEN", raising=False)
    monkeypatch.delenv("REASONING_EFFORT", raising=False)
    monkeypatch.delenv("REASONING_MODE", raising=False)

    provider = RealLLMProvider()

    assert provider._reasoning_effort_for_stage("ssot-gen") == "none"
    assert provider._reasoning_effort_for_stage("rtl-gen") == "none"
    assert provider._reasoning_effort_for_stage("tb-gen") == "none"

    monkeypatch.setenv("ATLAS_HEADLESS_LLM_REASONING_EFFORT_SSOT_GEN", "high")
    assert provider._reasoning_effort_for_stage("ssot-gen") == "high"


def test_real_llm_provider_resolves_cli_backend_models(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ATLAS_RUN_REAL_LLM_TDD", "1")
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(
        "src.headless_workflow.shutil.which",
        lambda name: f"/usr/bin/{name}" if name in {"claude", "cursor-agent"} else None,
    )

    try:
        provider = RealLLMProvider()
        resolved_model, profile_name = provider._activate_requested_model("claude-cli:sonnet")

        assert resolved_model == "claude-cli"
        assert profile_name == ""
        assert os.environ["CLAUDE_CLI_ENABLE"] == "true"
        assert os.environ["CLAUDE_CLI_MODEL"] == "sonnet"
        assert provider.available_reason("claude-cli:sonnet") == ""

        resolved_model, profile_name = provider._activate_requested_model("cursor-cli")

        assert resolved_model == "cursor-cli"
        assert profile_name == ""
        assert os.environ["CURSOR_AGENT_ENABLE"] == "true"
        assert os.environ["CURSOR_AGENT_MODEL"]
        assert provider.available_reason("cursor-cli") == ""
    finally:
        try:
            from src import config
        except ModuleNotFoundError:
            import config
        config.deactivate_cli_backends()


def test_real_llm_provider_reports_missing_cli_backend(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ATLAS_RUN_REAL_LLM_TDD", "1")
    monkeypatch.setattr("src.headless_workflow.shutil.which", lambda _name: None)

    provider = RealLLMProvider()

    try:
        assert provider.available_reason("claude-cli") == "claude not found in PATH"
        assert provider.available_reason("cursor-cli") == "cursor-agent not found in PATH"
    finally:
        try:
            from src import config
        except ModuleNotFoundError:
            import config
        config.deactivate_cli_backends()


def test_real_llm_provider_sets_inner_claude_timeout_before_outer_timeout(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("ATLAS_RUN_REAL_LLM_TDD", "1")
    monkeypatch.setattr(
        "src.headless_workflow.shutil.which",
        lambda name: f"/usr/bin/{name}" if name == "claude" else None,
    )
    seen: dict[str, object] = {}

    def fake_run(args, **kwargs) -> subprocess.CompletedProcess[str]:
        req = json.loads(Path(args[-1]).read_text(encoding="utf-8"))
        seen.update(req)
        seen["outer_timeout"] = kwargs.get("timeout")
        return subprocess.CompletedProcess(
            args=args,
            returncode=0,
            stdout=json.dumps({"raw": '{"files":[]}', "usage": {}, "cost": {}, "error": ""}) + "\n",
            stderr="",
        )

    monkeypatch.setattr("src.headless_workflow.subprocess.run", fake_run)

    try:
        response = RealLLMProvider(timeout_s=45).complete(
            stage="ssot-gen",
            model="claude-cli",
            system_prompt="",
            prompt="",
            context={"ip": "claude_timeout_ip"},
        )

        assert response.status == "blocked"
        assert seen["model"] == "claude-cli"
        assert seen["outer_timeout"] == 45
        assert seen["claude_cli_timeout_sec"] == 15
    finally:
        try:
            from src import config
        except ModuleNotFoundError:
            import config
        config.deactivate_cli_backends()


def test_rtl_gen_initial_audit_failure_still_drives_llm_packets(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    ip = "resume_packet_ip"
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="fake-contract-model",
        llm_provider=FakeLLMProvider(),
    )
    (tmp_path / "work" / ip / "rtl").mkdir(parents=True)
    (tmp_path / "work" / ip / "rtl" / "rtl_authoring_plan.json").write_text('{"packets":[]}\n', encoding="utf-8")
    prepare_audit_flags: list[bool] = []
    packet_attempts: list[int] = []

    def fake_prepare(_ip: str, *, audit_rtl: bool = False) -> subprocess.CompletedProcess[str]:
        prepare_audit_flags.append(audit_rtl)
        return subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="")

    def fake_stage(_stage: str, _ip: str) -> StageEngineResult:
        return StageEngineResult(
            stage="ssot-rtl",
            ip=_ip,
            status="human_gate",
            headline="[RTL BLOCKED]",
            message="rtl-gen waiting for target scale",
            metadata={"rtl_blocked": {"questions": [{"id": "RTL_TARGET_SCALE_POLICY"}]}},
        )

    monkeypatch.setattr(runner, "_prepare_rtl_todos_for_llm", fake_prepare)
    monkeypatch.setattr(runner, "_update_rtl_context_from_todos", lambda _ip, _ctx: None)
    monkeypatch.setattr(
        runner,
        "_rtl_authoring_plan",
        lambda _ip: {
            "summary": {"required_tasks": 100},
            "packets": [
                {
                    "packet_id": "module__resume_packet_ip_core",
                    "json": "rtl/authoring_packets/module__resume_packet_ip_core.json",
                    "execution_policy": {"llm_actionable_open_count": 1},
                }
            ],
        },
    )
    monkeypatch.setattr(
        runner,
        "_run_rtl_packet_llm_pass",
        lambda _ip, _ctx, *, attempt: packet_attempts.append(attempt) or None,
    )
    runner.stage_engine.run_stage = fake_stage  # type: ignore[method-assign]

    result = runner._stage_rtl_gen(ip, {})

    assert prepare_audit_flags == [True]
    assert packet_attempts == [0]
    assert result.status == "human_gate"


def test_rtl_gen_packet_mode_uses_queue_sized_pass_budget(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    ip = "large_packet_queue_ip"
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="fake-contract-model",
        llm_provider=FakeLLMProvider(),
    )
    ip_dir = tmp_path / "work" / ip / "rtl"
    ip_dir.mkdir(parents=True)
    (ip_dir / "rtl_authoring_plan.json").write_text('{"packets":[]}\n', encoding="utf-8")
    packets = [
        {
            "packet_id": f"module__large_packet_queue_ip_{idx}",
            "json": f"rtl/authoring_packets/module__large_packet_queue_ip_{idx}.json",
            "execution_policy": {"llm_actionable_open_count": 1},
        }
        for idx in range(13)
    ]
    packet_attempts: list[int] = []

    monkeypatch.setenv("ATLAS_HEADLESS_RTL_PACKET_MAX_PER_PASS", "4")
    monkeypatch.delenv("ATLAS_HEADLESS_RTL_PACKET_MAX_PASSES", raising=False)
    monkeypatch.setattr(
        runner,
        "_prepare_rtl_todos_for_llm",
        lambda _ip, *, audit_rtl=False: subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr=""),
    )
    monkeypatch.setattr(runner, "_update_rtl_context_from_todos", lambda _ip, _ctx: None)
    monkeypatch.setattr(
        runner,
        "_rtl_authoring_plan",
        lambda _ip: {"summary": {"required_tasks": 200}, "packets": packets},
    )
    monkeypatch.setattr(
        runner,
        "_run_rtl_packet_llm_pass",
        lambda _ip, _ctx, *, attempt: packet_attempts.append(attempt) or None,
    )
    runner.stage_engine.run_stage = lambda _stage, _ip: StageEngineResult(  # type: ignore[method-assign]
        stage="ssot-rtl",
        ip=_ip,
        status="fail",
        headline="[RTL RESULT] fail",
        message="LLM-authored RTL needs rtl-gen repair",
    )

    result = runner._stage_rtl_gen(ip, {})

    assert packet_attempts == [0, 1, 2, 3, 4, 5]
    assert result.status == "fail"


def test_pipeline_repeats_loopable_mismatch_as_review_decision_not_human_gate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    ip = "pipeline_repair_probe"
    root = tmp_path / "work"
    runner = HeadlessWorkflowRunner(
        root=root,
        model="fake-contract-model",
        llm_provider=FakeLLMProvider(),
    )
    (root / ip / "sim").mkdir(parents=True, exist_ok=True)
    calls: list[str] = []

    def append_pass(stage: str):
        def _impl(_ip: str, *args, **kwargs):
            calls.append(stage)
            return runner._append(stage, "pass", f"{stage} pass")

        return _impl

    def sim_debug(_ip: str):
        calls.append("sim-debug")
        (root / ip / "sim" / "mismatch_classification.json").write_text(
            json.dumps(
                {
                    "type": "mismatch_classification",
                    "status": "action_required",
                    "classifications": [
                        {
                            "goal_id": "EQ_STABLE_FAIL",
                            "classification": "rtl_bug",
                            "owner": "rtl-gen",
                            "llm_loop_allowed": True,
                            "reason": "same expected/observed mismatch",
                            "repair_prompt": "Repair RTL for EQ_STABLE_FAIL.",
                            "evidence": {
                                "fl_expected": {"result": 1},
                                "rtl_observed": {"result": 0},
                                "scoreboard_rows": [
                                    {
                                        "goal_id": "EQ_STABLE_FAIL",
                                        "fl_expected": {"result": 1},
                                        "rtl_observed": {"result": 0},
                                    }
                                ],
                            },
                        }
                    ],
                }
            )
            + "\n",
            encoding="utf-8",
        )
        return runner._append("sim-debug", "fail", "classified rtl-gen mismatch")

    monkeypatch.setenv("ATLAS_HEADLESS_PIPELINE_STAGES", "rtl-gen,lint,tb-gen,sim,sim-debug")
    monkeypatch.setenv("ATLAS_HEADLESS_PIPELINE_MAX_ITERS", "2")
    monkeypatch.setattr(runner, "_stage_rtl_gen", lambda _ip, _ctx: append_pass("rtl-gen")(_ip))
    monkeypatch.setattr(runner, "_stage_lint", append_pass("lint"))
    monkeypatch.setattr(runner, "_stage_tb_gen", lambda _ip, _ctx: append_pass("tb-gen")(_ip))
    monkeypatch.setattr(runner, "_stage_sim", append_pass("sim"))
    monkeypatch.setattr(runner, "_stage_sim_debug", sim_debug)

    result = runner.run(ip=ip, stages=["pipeline"])

    assert result.status == "blocked"
    assert calls == [
        "rtl-gen",
        "lint",
        "tb-gen",
        "sim",
        "sim-debug",
        "rtl-gen",
        "lint",
        "tb-gen",
        "sim",
        "sim-debug",
    ]
    review_path = root / ip / "review" / "decision_needed_pipeline_repeated_rtl_gen_mismatch.json"
    assert review_path.is_file()
    review = json.loads(review_path.read_text(encoding="utf-8"))
    assert review["status"] == "review_decision_needed"
    assert review["evidence"]["owner"] == "rtl-gen"
    assert review["evidence"]["goal_ids"] == ["EQ_STABLE_FAIL"]
    assert not (root / ip / "questions").exists()


def test_headless_cli_allows_downstream_stage_without_req(tmp_path: Path):
    root = Path(__file__).resolve().parents[1]
    script = root / "src" / "headless_workflow.py"

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--root",
            str(tmp_path / "work"),
            "--ip",
            "existing_ip",
            "--stages",
            "lint",
            "--provider",
            "fake",
        ],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["stages"][0]["stage"] == "lint"
    assert "the following arguments are required: --req" not in result.stderr


def test_headless_cli_requires_req_for_ssot_gen(tmp_path: Path):
    root = Path(__file__).resolve().parents[1]
    script = root / "src" / "headless_workflow.py"

    result = subprocess.run(
        [
            sys.executable,
            str(script),
            "--root",
            str(tmp_path / "work"),
            "--ip",
            "new_ip",
            "--stages",
            "ssot-gen",
            "--provider",
            "fake",
        ],
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 2
    assert "--req is required when ssot-gen is requested" in result.stderr


def test_fake_llm_headless_flow_reaches_goal_audit_pass(tmp_path: Path):
    _needs_sim_tools()
    ip = "stream_transform_counter"
    req = _write_req(tmp_path, ip)
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="fake-contract-model",
        llm_provider=FakeLLMProvider(),
    )

    result = runner.run(ip=ip, requirement_path=req, stages=FULL_STAGES)

    assert result.status == "pass", json.dumps(result.to_dict(), indent=2)
    ip_dir = tmp_path / "work" / ip
    audit = json.loads((ip_dir / "sim" / "fl_rtl_goal_audit.json").read_text(encoding="utf-8"))
    assert audit["status"] == "pass"
    assert (ip_dir / "logs" / "llm" / "ssot-gen.json").is_file()
    assert (ip_dir / "logs" / "llm" / "rtl-gen.json").is_file()
    assert (ip_dir / "logs" / "llm" / "tb-gen.json").is_file()
    assert json.loads((ip_dir / "logs" / "headless_run.json").read_text(encoding="utf-8"))["status"] == "pass"
    compare = json.loads((ip_dir / "sim" / "fl_rtl_compare.json").read_text(encoding="utf-8"))
    assert compare["status"] == "pass"
    assert compare["summary"]["goals_untested"] == 0
    coverage = json.loads((ip_dir / "cov" / "coverage.json").read_text(encoding="utf-8"))
    assert coverage["source"] == "ssot_coverage_summary"
    assert coverage["status"] == "pass"


def test_fake_llm_headless_flow_repairs_missing_cycle_model(tmp_path: Path):
    ip = "missing_cycle_model_ip"
    req = _write_req(tmp_path, ip)
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="fake-contract-model",
        llm_provider=FakeLLMProvider(scenario="missing_cycle_model"),
    )

    result = runner.run(ip=ip, requirement_path=req, stages=["ssot-gen", "fl-model-gen"])

    assert result.status == "pass", json.dumps(result.to_dict(), indent=2)
    ip_dir = tmp_path / "work" / ip
    ssot = yaml.safe_load((ip_dir / "yaml" / f"{ip}.ssot.yaml").read_text(encoding="utf-8"))
    assert "cycle_model" in ssot
    assert (ip_dir / "logs" / "validators" / "repair_ssot_schema.log").is_file()
    assert (ip_dir / "model" / "functional_model.py").is_file()


def test_headless_human_gate_artifact_created_for_ambiguous_requirement(tmp_path: Path):
    ip = "ambiguous_error_policy_ip"
    req = _write_req(tmp_path, ip, ambiguous=True)
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="fake-contract-model",
        llm_provider=FakeLLMProvider(scenario="human_gate"),
    )

    result = runner.run(ip=ip, requirement_path=req, stages=["ssot-gen"])

    assert result.status == "blocked"
    question = tmp_path / "work" / ip / "questions" / "ssot_gen_llm.json"
    assert question.is_file()
    gate = json.loads(question.read_text(encoding="utf-8"))
    assert "invalid transaction response" in gate["decision_needed"]
    assert gate["options"]


def test_headless_runner_rejects_non_glm51_when_glm51_requested(tmp_path: Path):
    ip = "glm_reject_ip"
    req = _write_req(tmp_path, ip)
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="deepseek-v3",
        llm_provider=RealLLMProvider(required_model="glm-5.1"),
        require_glm51=True,
    )

    result = runner.run(ip=ip, requirement_path=req, stages=["ssot-gen"])

    assert result.status == "blocked"
    log = json.loads((tmp_path / "work" / ip / "logs" / "llm" / "ssot-gen.json").read_text(encoding="utf-8"))
    assert log["model"] == "deepseek-v3"
    assert "requires model glm-5.1" in log["error"]


def test_headless_runner_default_provider_is_real_not_fake(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    ip = "default_provider_real_ip"
    req = _write_req(tmp_path, ip)
    monkeypatch.delenv("ATLAS_RUN_REAL_LLM_TDD", raising=False)

    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="glm-5.1",
    )

    result = runner.run(ip=ip, requirement_path=req, stages=["ssot-gen"])

    assert result.status == "blocked"
    log = json.loads((tmp_path / "work" / ip / "logs" / "llm" / "ssot-gen.json").read_text(encoding="utf-8"))
    assert "ATLAS_RUN_REAL_LLM_TDD=1 is not set" in log["error"]
    assert not (tmp_path / "work" / ip / "rtl" / f"{ip}.sv").exists()


def test_real_glm51_unavailable_blocks_without_human_question(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    ip = "real_glm_unavailable_ip"
    req = _write_req(tmp_path, ip)
    monkeypatch.setenv("ATLAS_RUN_REAL_LLM_TDD", "1")
    monkeypatch.delenv("ZAI_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("PROFILE_glm_API_KEY", raising=False)

    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="glm-5.1",
        llm_provider=RealLLMProvider(required_model="glm-5.1"),
        require_glm51=True,
    )

    result = runner.run(ip=ip, requirement_path=req, stages=["ssot-gen"])

    assert result.status == "blocked"
    log = json.loads((tmp_path / "work" / ip / "logs" / "llm" / "ssot-gen.json").read_text(encoding="utf-8"))
    assert log["model"] == "glm-5.1"
    assert "no live API key" in log["error"]
    assert result.stages[-1].status == "blocked"
    assert result.stages[-1].blocker == ""
    assert not (tmp_path / "work" / ip / "questions" / "ssot_gen_llm.json").exists()
