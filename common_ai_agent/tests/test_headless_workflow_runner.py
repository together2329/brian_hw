from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from src.headless_workflow import (
    FakeLLMProvider,
    HeadlessWorkflowRunner,
    LLMResponse,
    RealLLMProvider,
    _stable_json_sha256,
    _structured_ssot_yaml,
)
from src.workflow_stage_engine import StageEngineResult


FULL_STAGES = [
    "ssot-gen",
    "fl-model-gen",
    "equiv-goals",
    "rtl-gen",
    "lint",
    "tb-gen",
    "sim",
    "coverage",
    "sim-debug",
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


def test_fake_llm_headless_flow_blocks_missing_cycle_model(tmp_path: Path):
    ip = "missing_cycle_model_ip"
    req = _write_req(tmp_path, ip)
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work",
        model="fake-contract-model",
        llm_provider=FakeLLMProvider(scenario="missing_cycle_model"),
    )

    result = runner.run(ip=ip, requirement_path=req, stages=["ssot-gen", "fl-model-gen"])

    assert result.status == "blocked"
    question = tmp_path / "work" / ip / "questions" / "ssot_gen_missing_contract.json"
    assert question.is_file()
    gate = json.loads(question.read_text(encoding="utf-8"))
    assert gate["status"] == "human_gate"
    assert "cycle_model" in gate["decision_needed"]
    assert not (tmp_path / "work" / ip / "model" / "functional_model.py").exists()


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
