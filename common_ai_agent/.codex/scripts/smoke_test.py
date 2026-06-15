#!/usr/bin/env python3
"""Smoke test for the .codex ontology IP agent pack."""

from __future__ import annotations

import json
import os
import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OAG = ROOT / "scripts" / "oag_cli.py"
GRAPH = ROOT / "scripts" / "oag_graph.py"
MCP = ROOT / "scripts" / "oag_mcp_server.py"
EVAL = ROOT / "scripts" / "oag_eval.py"
STOP_GATE = ROOT / "hooks" / "codex_stop_gate.py"
CONTEXT_HOOK = ROOT / "hooks" / "codex_context_inject.py"
DRAFT_HOOK = ROOT / "hooks" / "codex_draft_pressure.py"
HOOKS_JSON = ROOT / "hooks.json"


def call(payload: dict) -> dict:
    env = {**os.environ, "OAG_DISABLE_BACKEND": "1"}
    proc = subprocess.run(
        [sys.executable, str(OAG), "call", "--json", json.dumps(payload)],
        text=True,
        capture_output=True,
        check=False,
        cwd=ROOT,
        env=env,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout)
    return json.loads(proc.stdout)


def call_process(payload: dict) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "OAG_DISABLE_BACKEND": "1"}
    return subprocess.run(
        [sys.executable, str(OAG), "call", "--json", json.dumps(payload)],
        text=True,
        capture_output=True,
        check=False,
        cwd=ROOT,
        env=env,
    )


def stop_gate(payload: dict) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "OAG_DISABLE_BACKEND": "1"}
    return subprocess.run(
        [sys.executable, str(STOP_GATE)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
        cwd=ROOT.parent,
        env=env,
    )


def context_hook(payload: dict) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "OAG_DISABLE_BACKEND": "1"}
    return subprocess.run(
        [sys.executable, str(CONTEXT_HOOK)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
        cwd=ROOT.parent,
        env=env,
    )


def hook_context(proc: subprocess.CompletedProcess[str]) -> str:
    if not proc.stdout.strip():
        return ""
    payload = json.loads(proc.stdout)
    output = payload.get("hookSpecificOutput") if isinstance(payload, dict) else {}
    return str(output.get("additionalContext") or "") if isinstance(output, dict) else ""


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_ip(root: Path) -> Path:
    ip = root / "demo_counter_cx1"
    scaffold = call({"tool": "oag.scaffold", "arguments": {"ip_dir": str(ip), "owner": "smoke"}})
    assert scaffold["ok"] is True, scaffold
    assert scaffold["result"]["schema_version"] == "oag_scaffold_result.v1", scaffold
    assert (ip / "ontology" / "ip.yaml").is_file()
    assert (ip / "ontology" / "requirements.yaml").is_file()
    assert (ip / "ontology" / "obligations.yaml").is_file()
    assert (ip / "ontology" / "contracts.yaml").is_file()
    assert (ip / "ontology" / "structure.yaml").is_file()
    assert (ip / "ontology" / "decomposition.yaml").is_file()
    assert (ip / "ontology" / "design_rules.yaml").is_file()
    assert (ip / "ontology" / "drafts").is_dir()
    assert (ip / "ontology" / "stages.yaml").is_file()
    assert (ip / "ontology" / "policies.yaml").is_file()
    assert (ip / "ontology" / "protection.yaml").is_file()
    assert (ip / "ontology" / "evidence" / "scoreboard_rows.v1.yaml").is_file()
    assert (ip / "ontology" / "evidence" / "stage_run_receipt.v1.yaml").is_file()
    assert (ip / "ontology" / "decision_receipt.v1.yaml").is_file()
    assert (ip / "ontology" / "run_state.v1.yaml").is_file()
    assert (ip / "ontology" / "gates" / "gate_self_test_registry.yaml").is_file()
    assert (ip / "knowledge" / "_index.json").is_file()
    assert (ip / "knowledge" / "ledger.jsonl").is_file()
    assert (ip / "list" / "rtl.f").is_file()
    (ip / "rtl" / "rtl_compile.json").write_text(json.dumps({"status": "pass"}), encoding="utf-8")
    (ip / "lint" / "dut_lint.json").write_text(json.dumps({"status": "pass"}), encoding="utf-8")
    (ip / "sim" / "results.xml").write_text('<testsuite failures="0"/>\n', encoding="utf-8")
    rows = [
        {
            "goal_id": "GOAL_COUNTER_INC",
            "scenario_id": "SC_INC_001",
            "cycle": 1,
            "stimulus": {"valid": 1},
            "expected": {"count": 1},
            "expected_source": {"kind": "manual_spec", "ref": "req/locked_truth.md"},
            "observed": {"count": 1},
            "observed_source": {"kind": "dut_signal", "path": "dut.count"},
            "passed": True,
            "mismatch": "",
            "coverage_refs": ["COV_INC"],
        },
        {
            "goal_id": "GOAL_COUNTER_INC",
            "scenario_id": "SC_INC_002",
            "cycle": 2,
            "stimulus": {"valid": 1},
            "expected": {"count": 2},
            "expected_source": {"kind": "manual_spec", "ref": "req/locked_truth.md"},
            "observed": {"count": 2},
            "observed_source": {"kind": "monitor", "path": "counter_monitor.count"},
            "passed": True,
            "mismatch": "",
            "coverage_refs": ["COV_INC"],
        },
    ]
    (ip / "sim" / "scoreboard_events.jsonl").write_text(
        "\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n",
        encoding="utf-8",
    )
    (ip / "cov" / "coverage.json").write_text(json.dumps({"status": "pass"}), encoding="utf-8")
    (ip / "signoff" / "truth_coverage.json").write_text(json.dumps({"status": "pass"}), encoding="utf-8")
    return ip


def write_stage_receipt(ip: Path, stage: str) -> None:
    receipt = {
        "schema_version": "stage_run_receipt.v1",
        "stage": stage,
        "owner": stage,
        "status": "pass",
        "command": "smoke-test",
        "actor": {"kind": "tool", "id": "smoke_test"},
        "started_at": "2026-01-01T00:00:00Z",
        "completed_at": "2026-01-01T00:00:01Z",
        "input_fingerprints": [
            {"path": "rtl/rtl_compile.json", "sha256": sha256(ip / "rtl" / "rtl_compile.json")},
            {"path": "lint/dut_lint.json", "sha256": sha256(ip / "lint" / "dut_lint.json")},
        ],
        "output_fingerprints": [
            {"path": "sim/results.xml", "sha256": sha256(ip / "sim" / "results.xml")},
            {"path": "sim/scoreboard_events.jsonl", "sha256": sha256(ip / "sim" / "scoreboard_events.jsonl")},
        ],
    }
    out = ip / "ontology" / "evidence" / "stage_runs" / f"{stage}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")


def mcp_tools_list() -> dict:
    initialize = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
    tools = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    proc = subprocess.run(
        [sys.executable, str(MCP)],
        input=json.dumps(initialize) + "\n" + json.dumps(tools) + "\n",
        text=True,
        capture_output=True,
        check=False,
        cwd=ROOT,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout)
    lines = [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]
    return lines[-1]


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        hooks = json.loads(HOOKS_JSON.read_text(encoding="utf-8"))
        user_hooks = hooks["hooks"]["UserPromptSubmit"][0]["hooks"]
        assert user_hooks[0]["command"] == "python3 .codex/hooks/codex_context_inject.py", hooks
        assert user_hooks[1]["command"] == "python3 .codex/hooks/codex_draft_pressure.py", hooks
        stop_hooks = hooks["hooks"]["Stop"][0]["hooks"]
        assert stop_hooks[0]["command"] == "python3 .codex/hooks/codex_stop_gate.py", hooks
        post_compact_hooks = hooks["hooks"]["PostCompact"][0]["hooks"]
        assert post_compact_hooks[0]["command"] == "python3 .codex/hooks/codex_context_inject.py", hooks
        assert STOP_GATE.is_file(), STOP_GATE
        assert CONTEXT_HOOK.is_file(), CONTEXT_HOOK
        assert DRAFT_HOOK.is_file(), DRAFT_HOOK
        assert EVAL.is_file(), EVAL

        ip = make_ip(Path(tmp))
        compiled = call({"tool": "oag.compile", "arguments": {"ip_dir": str(ip)}})
        assert compiled["result"]["status"] == "pass", compiled
        assert compiled["result"]["stats"]["design_rules"] >= 13, compiled
        assert compiled["result"]["stats"]["modules"] >= 1, compiled
        assert compiled["result"]["stats"]["design_facts_modules"] == 0, compiled
        assert compiled["result"]["stats"]["authoring_packets"] >= 1, compiled
        assert (ip / "ontology" / "generated" / "design_truth_graph.json").is_file()
        assert (ip / "ontology" / "generated" / "design_spec.json").is_file()
        design_facts_path = ip / "ontology" / "generated" / "design_facts_graph.json"
        assert design_facts_path.is_file()
        design_facts = json.loads(design_facts_path.read_text(encoding="utf-8"))
        assert design_facts["schema_version"] == "oag_design_facts_graph.v1", design_facts
        assert design_facts["status"] == "pass", design_facts
        assert design_facts["stats"]["rtl_source_files"] == 0, design_facts
        assert (ip / "ontology" / "generated" / "authoring_packets" / "module__demo_counter_cx1.json").is_file()
        assert (ip / "ontology" / "runs").is_dir()
        inspect = call({"tool": "oag.inspect", "arguments": {"ip_dir": str(ip), "stage": "sim"}})
        assert inspect["result"]["validation"] == "partial", inspect
        assert "closure matrix has open obligations" in inspect["result"]["gaps"], inspect
        assert inspect["result"]["evidence"]["truth_graph"]["status"] == "pass", inspect
        assert inspect["result"]["evidence"]["design_facts_graph"]["status"] == "pass", inspect
        assert inspect["result"]["evidence"]["design_rules"]["count"] >= 13, inspect
        assert inspect["result"]["evidence"]["structure"]["profile"] == "small_leaf_single_file", inspect
        assert inspect["result"]["evidence"]["decomposition"]["modules"] >= 1, inspect
        assert inspect["result"]["evidence"]["authoring_packets"]["count"] >= 1, inspect
        scoreboard = inspect["result"]["evidence"]["scoreboard"]["summary"]
        assert scoreboard["schema"] == "scoreboard_rows.v1", scoreboard
        assert scoreboard["standard_rows"] == 2, scoreboard
        assert scoreboard["schema_failed"] == 0, scoreboard
        init = call({"tool": "oag.init", "arguments": {"ip_dir": str(ip)}})
        assert init["ok"] is True, init
        run_start = call(
            {
                "tool": "oag.run.start",
                "arguments": {
                    "ip_dir": str(ip),
                    "stage": "sim",
                    "intent": "smoke close reset scoreboard obligation",
                    "actor": {"kind": "ai", "id": "codex", "surface": "smoke"},
                },
            }
        )
        assert run_start["result"]["schema_version"] == "oag_run_start.v1", run_start
        run_id = run_start["result"]["run_id"]
        assert run_start["result"]["status"] == "in_progress", run_start
        assert run_start["result"]["next_action"]["active_obligation"] == "OBL_DEMO_COUNTER_CX1_RESET_KNOWN", run_start
        assert "OAG NEXT ACTION" in run_start["result"]["next_action"]["prompt_block"], run_start
        assert (ip / "ontology" / "runs" / run_id / "run_state.json").is_file(), run_start
        assert (ip / "ontology" / "runs" / run_id / "next_action.json").is_file(), run_start
        assert (ip / "ontology" / "runs" / run_id / "checkpoint_history.jsonl").is_file(), run_start
        stop_before = call({"tool": "oag.stop_check", "arguments": {"ip_dir": str(ip), "run_id": run_id}})
        assert stop_before["result"]["should_continue"] is True, stop_before
        assert "OAG NEXT ACTION" in stop_before["result"]["prompt_block"], stop_before
        stop_hook_before = stop_gate({"ip_dir": str(ip), "run_id": run_id})
        assert stop_hook_before.returncode == 0, stop_hook_before.stderr or stop_hook_before.stdout
        stop_hook_block = json.loads(stop_hook_before.stdout)
        assert stop_hook_block["decision"] == "block", stop_hook_block
        assert "OAG NEXT ACTION" in stop_hook_block["reason"], stop_hook_block
        assert "run incomplete" in stop_hook_block["reason"], stop_hook_block
        run_loop_record = call(
            {
                "tool": "oag.run.record",
                "arguments": {
                    "ip_dir": str(ip),
                    "run_id": run_id,
                    "stage": "sim",
                    "summary": "run-loop smoke scoreboard evidence closes the reset obligation",
                    "actor": {"kind": "ai", "id": "codex", "surface": "smoke"},
                },
            }
        )
        assert run_loop_record["result"]["record"]["status"] == "closed", run_loop_record
        assert run_loop_record["result"]["status"] == "checkpoint_ready", run_loop_record
        run_checkpoint = call(
            {
                "tool": "oag.run.checkpoint",
                "arguments": {
                    "ip_dir": str(ip),
                    "run_id": run_id,
                    "stage": "sim",
                    "intent": "smoke close reset scoreboard obligation",
                    "actor": {"kind": "ai", "id": "codex", "surface": "smoke"},
                },
            }
        )
        assert run_checkpoint["result"]["allowed"] is True, run_checkpoint
        assert run_checkpoint["result"]["status"] == "complete", run_checkpoint
        assert run_checkpoint["result"]["decision"]["decision_receipt"], run_checkpoint
        stop_after = call({"tool": "oag.stop_check", "arguments": {"ip_dir": str(ip), "run_id": run_id}})
        assert stop_after["result"]["should_continue"] is False, stop_after
        assert stop_after["result"]["reason"] == "run_complete", stop_after
        stop_hook_after = stop_gate({"ip_dir": str(ip), "run_id": run_id})
        assert stop_hook_after.returncode == 0, stop_hook_after.stderr or stop_hook_after.stdout
        assert stop_hook_after.stdout == "", stop_hook_after.stdout
        record = call(
            {
                "tool": "oag.record",
                "arguments": {
                    "ip_dir": str(ip),
                    "stage": "sim",
                    "type": "finding",
                    "claim": "counter scoreboard closed",
                    "summary": "scoreboard rows are clean",
                    "actor": {"kind": "ai", "id": "codex", "surface": "smoke"},
                    "rocev": {
                        "obligation": {"id": "OBL_DEMO_COUNTER_CX1_RESET_KNOWN", "text": "scoreboard has no mismatches"},
                        "contract": {
                            "id": "CONTRACT_DEMO_COUNTER_CX1_SIM_SCOREBOARD",
                            "method": "scoreboard",
                            "pass_condition": "mismatch count is zero",
                        },
                        "evidence": {"files": ["sim/results.xml", "sim/scoreboard_events.jsonl"], "tests": [], "commit": ""},
                        "validation": {"status": "closed", "verdict": "pass", "rationale": "all scoreboard rows have mismatch=false"},
                    },
                },
            }
        )
        assert record["result"]["status"] == "closed", record
        assert len(record["result"]["record"]["evidence"]["file_hashes"]) == 2, record
        assert record["result"]["ledger_event"], record
        assert (ip / "knowledge" / "ledger.jsonl").read_text(encoding="utf-8").strip(), record
        draft = call(
            {
                "tool": "oag.draft",
                "arguments": {
                    "ip_dir": str(ip),
                    "stage": "req",
                    "title": "counter requirement interview round 1",
                    "summary": "Captured draft requirement facts before locked-truth promotion.",
                    "facts": ["AXI data width is 256 bits"],
                    "open_questions": ["Which reset value is architecturally locked?"],
                    "actor": {"kind": "ai", "id": "codex", "surface": "smoke"},
                },
            }
        )
        assert draft["result"]["status"] == "draft", draft
        assert Path(draft["result"]["draft_path"]).is_file(), draft
        assert Path(draft["result"]["markdown_path"]).is_file(), draft
        context = call({"tool": "oag.context", "arguments": {"ip_dir": str(ip), "stage": "sim", "intent": "scoreboard"}})
        assert "IP KNOWLEDGE LEDGER" in context["result"]["prompt_block"], context
        cache_path = ROOT / ".cache" / "context_inject.json"
        cache_path.unlink(missing_ok=True)
        context_payload = {"ip_dir": str(ip), "stage": "sim", "prompt": f"Continue sim work for {ip.name}"}
        context_first = context_hook(context_payload)
        assert context_first.returncode == 0, context_first.stderr or context_first.stdout
        assert "OAG CONTEXT INJECTION" in hook_context(context_first), context_first.stdout
        context_duplicate = context_hook(context_payload)
        assert context_duplicate.returncode == 0, context_duplicate.stderr or context_duplicate.stdout
        assert context_duplicate.stdout == "", context_duplicate.stdout
        context_high_pressure = context_hook({**context_payload, "context_pressure": "high"})
        assert context_high_pressure.returncode == 0, context_high_pressure.stderr or context_high_pressure.stdout
        assert context_high_pressure.stdout == "", context_high_pressure.stdout
        context_post_compact = context_hook({**context_payload, "hook_event_name": "PostCompact"})
        assert context_post_compact.returncode == 0, context_post_compact.stderr or context_post_compact.stdout
        assert context_post_compact.stdout == "", context_post_compact.stdout
        context_recovery = context_hook(context_payload)
        assert context_recovery.returncode == 0, context_recovery.stderr or context_recovery.stdout
        recovery_payload = json.loads(context_recovery.stdout)
        assert recovery_payload["hookSpecificOutput"]["hookEventName"] == "UserPromptSubmit", recovery_payload
        assert "OAG CONTEXT INJECTION" in hook_context(context_recovery), context_recovery.stdout
        undecided = call({"tool": "oag.decide", "arguments": {"ip_dir": str(ip), "action": "claim_complete", "stage": "sim"}})
        assert undecided["result"]["allowed"] is False, undecided
        assert undecided["result"]["reason"] == "decision_receipt_required", undecided
        decide = call(
            {
                "tool": "oag.decide",
                "arguments": {
                    "ip_dir": str(ip),
                    "action": "claim_complete",
                    "stage": "sim",
                    "record_decision": True,
                    "actor": {"kind": "ai", "id": "codex", "surface": "smoke"},
                },
            }
        )
        assert decide["result"]["allowed"] is True, decide
        assert Path(decide["result"]["decision_receipt"]["path"]).is_file(), decide
        signoff_blocked = call({"tool": "oag.decide", "arguments": {"ip_dir": str(ip), "action": "signoff", "stage": "signoff"}})
        assert signoff_blocked["result"]["allowed"] is False, signoff_blocked
        assert signoff_blocked["result"]["reason"] == "closure_profile_not_signoff", signoff_blocked
        policies = ip / "ontology" / "policies.yaml"
        policies.write_text(policies.read_text(encoding="utf-8").replace("closure_profile: development", "closure_profile: signoff"), encoding="utf-8")
        approval = call(
            {
                "tool": "oag.record",
                "arguments": {
                    "ip_dir": str(ip),
                    "stage": "signoff",
                    "type": "decision",
                    "claim": "human approval to enter signoff closure profile",
                    "summary": "Human owner approved the protected policy transition to signoff.",
                    "actor": {"kind": "human", "id": "smoke-owner", "surface": "smoke"},
                    "approval": {"kind": "human", "approved": True, "reason": "smoke signoff path"},
                    "status": "open",
                },
            }
        )
        assert approval["result"]["ledger_event"], approval
        compiled = call({"tool": "oag.compile", "arguments": {"ip_dir": str(ip)}})
        assert compiled["result"]["status"] == "pass", compiled
        write_stage_receipt(ip, "sim")
        signoff_without_review = call({"tool": "oag.decide", "arguments": {"ip_dir": str(ip), "action": "signoff", "stage": "signoff"}})
        assert signoff_without_review["result"]["allowed"] is False, signoff_without_review
        assert signoff_without_review["result"]["reason"] == "reviewer_receipt_required", signoff_without_review
        fake_review_path = ip / "ontology" / "validations" / "REV_SELF_ALLOWED.json"
        fake_review_path.write_text(
            json.dumps(
                {
                    "schema_version": "oag_reviewer_receipt.v1",
                    "id": "REV_SELF_ALLOWED",
                    "ip": ip.name,
                    "action": "signoff",
                    "allowed": True,
                    "reason": "allowed",
                    "verdict": "pass",
                    "actor": {"kind": "ai", "id": "codex", "surface": "smoke"},
                    "producer_actor": {"kind": "ai", "id": "codex", "surface": "smoke"},
                    "independent": False,
                    "findings": [],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        signoff_with_non_independent_review = call({"tool": "oag.decide", "arguments": {"ip_dir": str(ip), "action": "signoff", "stage": "signoff"}})
        assert signoff_with_non_independent_review["result"]["allowed"] is False, signoff_with_non_independent_review
        assert signoff_with_non_independent_review["result"]["reason"] == "reviewer_receipt_required", signoff_with_non_independent_review
        review = call(
            {
                "tool": "oag.review",
                "arguments": {
                    "ip_dir": str(ip),
                    "action": "signoff",
                    "stage": "signoff",
                    "verdict": "pass",
                    "actor": {"kind": "ai", "id": "smoke-reviewer", "surface": "smoke"},
                    "producer_actor": {"kind": "ai", "id": "codex", "surface": "smoke"},
                    "findings": [],
                },
            }
        )
        assert review["result"]["allowed"] is True, review
        assert Path(review["result"]["reviewer_receipt"]["path"]).is_file(), review
        signoff = call(
            {
                "tool": "oag.decide",
                "arguments": {
                    "ip_dir": str(ip),
                    "action": "signoff",
                    "stage": "signoff",
                    "record_decision": True,
                    "actor": {"kind": "human", "id": "smoke-owner", "surface": "smoke"},
                },
            }
        )
        assert signoff["result"]["allowed"] is True, signoff
        assert Path(signoff["result"]["decision_receipt"]["path"]).is_file(), signoff
        ticket = call(
            {
                "tool": "oag.ticket",
                "arguments": {
                    "ip_dir": str(ip),
                    "stage": "sim",
                    "reason": "scoreboard mismatch example",
                    "failing_contract": {"id": "CONTRACT_SIM_SCOREBOARD"},
                    "expected": {"count": 3},
                    "observed": {"count": 2},
                    "evidence": {"files": ["sim/scoreboard_events.jsonl"]},
                    "editable_files": ["rtl/demo_counter_cx1.sv"],
                    "required_evidence_after_patch": ["sim/results.xml", "sim/scoreboard_events.jsonl"],
                },
            }
        )
        assert ticket["result"]["owner_workflow"] == "tb", ticket
        assert Path(ticket["result"]["path"]).is_file(), ticket
        graph_json = Path(tmp) / "ontology_graph.json"
        graph_html = Path(tmp) / "ontology_graph.html"
        graph_proc = subprocess.run(
            [
                sys.executable,
                str(GRAPH),
                "build",
                "--ip-dir",
                str(ip),
                "--stage",
                "sim",
                "--intent",
                "scoreboard",
                "--json-out",
                str(graph_json),
                "--html-out",
                str(graph_html),
            ],
            text=True,
            capture_output=True,
            check=False,
            cwd=ROOT,
            env={**os.environ, "OAG_DISABLE_BACKEND": "1"},
        )
        assert graph_proc.returncode == 0, graph_proc.stderr or graph_proc.stdout
        graph_data = json.loads(graph_json.read_text(encoding="utf-8"))
        assert graph_data["schema_version"] == "oag_ontology_graph.v1", graph_data
        assert graph_data["stats"]["record_count"] >= 1, graph_data
        assert any(node["type"] == "obligation" for node in graph_data["graph"]["nodes"]), graph_data
        assert any(node["type"] == "structure" for node in graph_data["graph"]["nodes"]), graph_data
        assert any(node["type"] == "module" for node in graph_data["graph"]["nodes"]), graph_data
        assert any(node["type"] == "authoring_packet" for node in graph_data["graph"]["nodes"]), graph_data
        assert any(node["type"] == "rule" for node in graph_data["graph"]["nodes"]), graph_data
        assert any(node["type"] == "rule_instance" for node in graph_data["graph"]["nodes"]), graph_data
        assert any(node["type"] == "draft" for node in graph_data["graph"]["nodes"]), graph_data
        assert any(node["type"] == "protection" for node in graph_data["graph"]["nodes"]), graph_data
        assert any(node["type"] == "ledger" for node in graph_data["graph"]["nodes"]), graph_data
        assert any(node["type"] == "stage" for node in graph_data["graph"]["nodes"]), graph_data
        assert any(node["type"] == "decision" for node in graph_data["graph"]["nodes"]), graph_data
        assert any(node["type"] == "run" for node in graph_data["graph"]["nodes"]), graph_data
        assert any(node["type"] == "ticket" for node in graph_data["graph"]["nodes"]), graph_data
        assert "OAG Ontology Graph" in graph_html.read_text(encoding="utf-8")
        tools = mcp_tools_list()
        assert len(tools["result"]["tools"]) >= 10, tools
        eval_proc = subprocess.run(
            [sys.executable, str(EVAL), "--json"],
            text=True,
            capture_output=True,
            check=False,
            cwd=ROOT.parent,
            env={**os.environ, "OAG_DISABLE_BACKEND": "1"},
        )
        assert eval_proc.returncode == 0, eval_proc.stderr or eval_proc.stdout
        eval_report = json.loads(eval_proc.stdout)
        assert eval_report["schema_version"] == "oag_evaluation_report.v1", eval_report
        assert eval_report["ok"] is True, eval_report
        assert eval_report["passed"] == eval_report["total"], eval_report
        assert eval_report["total"] >= 14, eval_report
        needs_human_ip = make_ip(Path(tmp) / "needs_human_run")
        needs_human_run = call(
            {
                "tool": "oag.run.start",
                "arguments": {
                    "ip_dir": str(needs_human_ip),
                    "stage": "sim",
                    "intent": "smoke repeated blocker",
                    "actor": {"kind": "ai", "id": "codex", "surface": "smoke"},
                },
            }
        )
        needs_human_run_id = needs_human_run["result"]["run_id"]
        needs_human_checkpoint = call(
            {
                "tool": "oag.run.checkpoint",
                "arguments": {
                    "ip_dir": str(needs_human_ip),
                    "run_id": needs_human_run_id,
                    "stage": "sim",
                    "intent": "smoke repeated blocker",
                    "max_blocker_repeats": 1,
                    "actor": {"kind": "ai", "id": "codex", "surface": "smoke"},
                },
            }
        )
        assert needs_human_checkpoint["result"]["status"] == "needs_human", needs_human_checkpoint
        stop_hook_human = stop_gate({"ip_dir": str(needs_human_ip), "run_id": needs_human_run_id})
        assert stop_hook_human.returncode == 0, stop_hook_human.stderr or stop_hook_human.stdout
        human_block = json.loads(stop_hook_human.stdout)
        assert human_block["decision"] == "block", human_block
        assert "human decision" in human_block["reason"], human_block
        explicit_ip = make_ip(Path(tmp) / "bad_explicit_validation")
        draftish = call(
            {
                "tool": "oag.record",
                "arguments": {
                    "ip_dir": str(explicit_ip),
                    "stage": "sim",
                    "claim": "evidence without explicit validation status",
                    "actor": {"kind": "ai", "id": "codex", "surface": "smoke"},
                    "rocev": {
                        "obligation": {"id": "OBL_DEMO_COUNTER_CX1_RESET_KNOWN"},
                        "contract": {"id": "CONTRACT_DEMO_COUNTER_CX1_SIM_SCOREBOARD", "method": "scoreboard"},
                        "evidence": {"files": ["sim/results.xml"], "tests": [], "commit": ""},
                        "validation": {"verdict": "pass", "rationale": "missing explicit status"},
                    },
                },
            }
        )
        assert draftish["result"]["status"] == "open", draftish
        explicit_check = call({"tool": "oag.check", "arguments": {"ip_dir": str(explicit_ip)}})
        assert explicit_check["result"]["ok"] is False, explicit_check
        assert any("no closed validation record linking obligation to contract" in issue for issue in explicit_check["result"]["issues"]), explicit_check
        rejected_closed = call_process(
            {
                "tool": "oag.record",
                "arguments": {
                    "ip_dir": str(explicit_ip),
                    "stage": "sim",
                    "status": "closed",
                    "claim": "top-level closed without validation status",
                    "actor": {"kind": "ai", "id": "codex", "surface": "smoke"},
                    "rocev": {
                        "obligation": {"id": "OBL_DEMO_COUNTER_CX1_RESET_KNOWN"},
                        "contract": {"id": "CONTRACT_DEMO_COUNTER_CX1_SIM_SCOREBOARD", "method": "scoreboard"},
                        "evidence": {"files": ["sim/results.xml"], "tests": [], "commit": ""},
                        "validation": {"verdict": "pass", "rationale": "top-level close only"},
                    },
                },
            }
        )
        assert rejected_closed.returncode != 0, rejected_closed.stdout
        assert "closed records require explicit rocev.validation.status" in json.loads(rejected_closed.stdout)["errors"][0], rejected_closed.stdout
        freshness_ip = make_ip(Path(tmp) / "bad_freshness")
        fresh_record = call(
            {
                "tool": "oag.record",
                "arguments": {
                    "ip_dir": str(freshness_ip),
                    "stage": "sim",
                    "claim": "fresh evidence baseline",
                    "actor": {"kind": "ai", "id": "codex", "surface": "smoke"},
                    "rocev": {
                        "obligation": {"id": "OBL_DEMO_COUNTER_CX1_RESET_KNOWN"},
                        "contract": {"id": "CONTRACT_DEMO_COUNTER_CX1_SIM_SCOREBOARD", "method": "scoreboard"},
                        "evidence": {"files": ["sim/results.xml"], "tests": [], "commit": ""},
                        "validation": {"status": "closed", "verdict": "pass", "rationale": "hash baseline"},
                    },
                },
            }
        )
        assert fresh_record["result"]["status"] == "closed", fresh_record
        (freshness_ip / "sim" / "results.xml").write_text('<testsuite failures="1"/>\n', encoding="utf-8")
        freshness_check = call({"tool": "oag.check", "arguments": {"ip_dir": str(freshness_ip)}})
        assert freshness_check["result"]["ok"] is False, freshness_check
        assert any("evidence file stale: sim/results.xml" in issue for issue in freshness_check["result"]["issues"]), freshness_check
        bad_ip = make_ip(Path(tmp) / "bad")
        bad_row = {
            "goal_id": "GOAL_BAD",
            "scenario_id": "SC_BAD",
            "cycle": 1,
            "stimulus": {},
            "expected": {"count": 1},
            "observed": {"count": 1},
            "passed": True,
            "mismatch": "",
            "coverage_refs": [],
        }
        (bad_ip / "sim" / "scoreboard_events.jsonl").write_text(json.dumps(bad_row) + "\n", encoding="utf-8")
        bad_inspect = call({"tool": "oag.inspect", "arguments": {"ip_dir": str(bad_ip), "stage": "sim"}})
        assert bad_inspect["result"]["validation"] == "partial", bad_inspect
        assert "scoreboard schema has invalid rows" in bad_inspect["result"]["gaps"], bad_inspect
        empty_ip = Path(tmp) / "empty_vacuous"
        empty_ip.mkdir()
        empty_compile = call({"tool": "oag.compile", "arguments": {"ip_dir": str(empty_ip)}})
        assert empty_compile["result"]["status"] == "fail", empty_compile
        assert "no requirements in ontology/requirements.yaml" in empty_compile["result"]["issues"], empty_compile
        bad_rules_ip = make_ip(Path(tmp) / "bad_rules")
        (bad_rules_ip / "ontology" / "design_rules.yaml").write_text(
            "\n".join(
                [
                    "schema: oag_design_rules.v1",
                    f"ip: {bad_rules_ip.name}",
                    "rules:",
                    "  - id: RULE_ONLY_SCOREBOARD",
                    "    kind: scoreboard_evidence_schema",
                    "    status: active",
                    "instances: []",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        bad_rules_compile = call({"tool": "oag.compile", "arguments": {"ip_dir": str(bad_rules_ip)}})
        assert bad_rules_compile["result"]["status"] == "fail", bad_rules_compile
        assert "missing required design rule kind: same_cycle_priority_declared" in bad_rules_compile["result"]["issues"], bad_rules_compile
        bad_lang_ip = make_ip(Path(tmp) / "bad_language_policy")
        bad_lang_rules = (bad_lang_ip / "ontology" / "design_rules.yaml").read_text(encoding="utf-8")
        bad_lang_rules = bad_lang_rules.replace(
            "    allowed_constructs: [logic, generate, genvar, generate_for]",
            "    allowed_constructs: [logic]",
            1,
        )
        bad_lang_rules = bad_lang_rules.replace(
            "    forbidden_constructs: [procedural_for, procedural_while, procedural_repeat, procedural_forever, package, import, interface, modport, typedef, enum, always_ff, always_comb, always_latch]",
            "    forbidden_constructs: [procedural_for, procedural_while, generate_for]",
            1,
        )
        (bad_lang_ip / "ontology" / "design_rules.yaml").write_text(bad_lang_rules, encoding="utf-8")
        bad_lang_compile = call({"tool": "oag.compile", "arguments": {"ip_dir": str(bad_lang_ip)}})
        assert bad_lang_compile["result"]["status"] == "fail", bad_lang_compile
        assert "RULE_RTL_LANGUAGE_SUBSET: rtl language subset must allow generate" in bad_lang_compile["result"]["issues"], bad_lang_compile
        assert "RULE_RTL_LANGUAGE_SUBSET: rtl language subset must not forbid generate constructs" in bad_lang_compile["result"]["issues"], bad_lang_compile
        formal_ip = make_ip(Path(tmp) / "bad_formal")
        contract_text = (formal_ip / "ontology" / "contracts.yaml").read_text(encoding="utf-8")
        contract_text += "\n".join(
            [
                "  - id: CONTRACT_BAD_FORMAL",
                "    obligation: OBL_DEMO_COUNTER_CX1_RESET_KNOWN",
                "    method: formal",
                "    pass_condition: register map is proven",
                "    evidence_kinds: [formal]",
                "",
            ]
        )
        (formal_ip / "ontology" / "contracts.yaml").write_text(contract_text, encoding="utf-8")
        formal_compile = call({"tool": "oag.compile", "arguments": {"ip_dir": str(formal_ip)}})
        assert formal_compile["result"]["status"] == "fail", formal_compile
        assert "CONTRACT_BAD_FORMAL: formal/assertion contract missing assertion/proof reference" in formal_compile["result"]["issues"], formal_compile
        bad_decomp_ip = make_ip(Path(tmp) / "bad_decomposition")
        (bad_decomp_ip / "ontology" / "decomposition.yaml").write_text(
            "\n".join(
                [
                    "schema: oag_decomposition.v1",
                    f"ip: {bad_decomp_ip.name}",
                    "profile:",
                    "  mode: greenfield_modular",
                    "  rationale: one module is intentionally invalid for this negative test",
                    "modules:",
                    f"  - id: {bad_decomp_ip.name}",
                    "    ownership: current_ip",
                    f"    file: rtl/{bad_decomp_ip.name}.sv",
                    "    owned_obligations: [OBL_DEMO_COUNTER_CX1_RESET_KNOWN]",
                    "    owned_contracts: [CONTRACT_DEMO_COUNTER_CX1_SIM_SCOREBOARD]",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        bad_decomp_compile = call({"tool": "oag.compile", "arguments": {"ip_dir": str(bad_decomp_ip)}})
        assert bad_decomp_compile["result"]["status"] == "fail", bad_decomp_compile
        assert "greenfield_modular profile requires at least two current_ip modules or use small_leaf_single_file" in bad_decomp_compile["result"]["issues"], bad_decomp_compile
        bad_file_boundary_ip = make_ip(Path(tmp) / "bad_file_boundary")
        (bad_file_boundary_ip / "ontology" / "decomposition.yaml").write_text(
            "\n".join(
                [
                    "schema: oag_decomposition.v1",
                    f"ip: {bad_file_boundary_ip.name}",
                    "profile:",
                    "  mode: greenfield_modular",
                    "  rationale: duplicate physical files are intentionally invalid for this negative test",
                    "modules:",
                    f"  - id: {bad_file_boundary_ip.name}_top",
                    "    ownership: current_ip",
                    f"    file: rtl/{bad_file_boundary_ip.name}.sv",
                    "    role: top",
                    "    owned_obligations: [OBL_DEMO_COUNTER_CX1_RESET_KNOWN]",
                    "    owned_contracts: [CONTRACT_DEMO_COUNTER_CX1_SIM_SCOREBOARD]",
                    f"  - id: {bad_file_boundary_ip.name}_core",
                    "    ownership: current_ip",
                    f"    file: rtl/{bad_file_boundary_ip.name}.sv",
                    "    role: core",
                    "    owned_obligations: []",
                    "    owned_contracts: []",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        bad_file_boundary_compile = call({"tool": "oag.compile", "arguments": {"ip_dir": str(bad_file_boundary_ip)}})
        assert bad_file_boundary_compile["result"]["status"] == "fail", bad_file_boundary_compile
        assert any(
            "greenfield_modular module file boundary requires unique file per current_ip module" in issue
            for issue in bad_file_boundary_compile["result"]["issues"]
        ), bad_file_boundary_compile
        priority_ip = make_ip(Path(tmp) / "bad_priority")
        rules_path = priority_ip / "ontology" / "design_rules.yaml"
        rules_text = rules_path.read_text(encoding="utf-8").replace(
            "instances:\n",
            "\n".join(
                [
                    "instances:",
                    "  - id: BAD_PRIORITY_INSTANCE",
                    "    rule: RULE_SAME_CYCLE_PRIORITY_DECLARED",
                    "    status: active",
                    "    conflict: [ctrl_disable_write, terminal_tick]",
                    "    requirement: REQ_DEMO_COUNTER_CX1_001",
                    "    obligation: OBL_DEMO_COUNTER_CX1_RESET_KNOWN",
                    "    contract: CONTRACT_DEMO_COUNTER_CX1_SIM_SCOREBOARD",
                    "",
                ]
            ),
            1,
        )
        rules_path.write_text(rules_text, encoding="utf-8")
        priority_compile = call({"tool": "oag.compile", "arguments": {"ip_dir": str(priority_ip)}})
        assert priority_compile["result"]["status"] == "fail", priority_compile
        assert "BAD_PRIORITY_INSTANCE: same-cycle priority rule missing priority" in priority_compile["result"]["issues"], priority_compile
        protection_ip = make_ip(Path(tmp) / "bad_protection")
        baseline = call(
            {
                "tool": "oag.record",
                "arguments": {
                    "ip_dir": str(protection_ip),
                    "stage": "req",
                    "type": "decision",
                    "claim": "baseline protected truth snapshot",
                    "summary": "Establish protected field snapshot before edits.",
                    "actor": {"kind": "ai", "id": "codex", "surface": "smoke"},
                    "status": "open",
                },
            }
        )
        assert baseline["result"]["ledger_event"], baseline
        locked_truth = protection_ip / "req" / "locked_truth.md"
        locked_truth.write_text(locked_truth.read_text(encoding="utf-8") + "\n- Unauthorized semantic edit.\n", encoding="utf-8")
        before_records = sorted((protection_ip / "knowledge" / "records").glob("*.json"))
        rejected = call_process(
            {
                "tool": "oag.record",
                "arguments": {
                    "ip_dir": str(protection_ip),
                    "stage": "req",
                    "claim": "unauthorized protected edit record",
                    "actor": {"kind": "ai", "id": "codex", "surface": "smoke"},
                    "status": "open",
                },
            }
        )
        assert rejected.returncode != 0, rejected.stdout
        rejected_response = json.loads(rejected.stdout)
        assert "protected fields changed without human approval" in rejected_response["errors"][0], rejected_response
        after_records = sorted((protection_ip / "knowledge" / "records").glob("*.json"))
        assert after_records == before_records, [before_records, after_records]
        protection_check = call({"tool": "oag.check", "arguments": {"ip_dir": str(protection_ip)}})
        assert protection_check["result"]["ok"] is False, protection_check
        assert any("protected fields changed without ledger approval" in issue for issue in protection_check["result"]["issues"]), protection_check
        ledger_ip = make_ip(Path(tmp) / "bad_ledger")
        ledger_record = call(
            {
                "tool": "oag.record",
                "arguments": {
                    "ip_dir": str(ledger_ip),
                    "stage": "sim",
                    "claim": "ledger tamper baseline",
                    "actor": {"kind": "ai", "id": "codex", "surface": "smoke"},
                    "status": "open",
                },
            }
        )
        assert ledger_record["result"]["ledger_event"], ledger_record
        ledger_path = ledger_ip / "knowledge" / "ledger.jsonl"
        ledger_path.write_text(ledger_path.read_text(encoding="utf-8").replace('"action": "log"', '"action": "tampered"', 1), encoding="utf-8")
        ledger_check = call({"tool": "oag.check", "arguments": {"ip_dir": str(ledger_ip)}})
        assert ledger_check["result"]["ok"] is False, ledger_check
        assert any("event_hash mismatch" in issue for issue in ledger_check["result"]["issues"]), ledger_check
        monotonic_ip = make_ip(Path(tmp) / "bad_monotonic")
        closed = call(
            {
                "tool": "oag.record",
                "arguments": {
                    "ip_dir": str(monotonic_ip),
                    "stage": "sim",
                    "claim": "monotonic obligation closed",
                    "actor": {"kind": "ai", "id": "codex", "surface": "smoke"},
                    "rocev": {
                        "obligation": {"id": "OBL_MONO_SCOREBOARD", "text": "closed once"},
                        "contract": {"id": "CONTRACT_MONO_SCOREBOARD", "method": "scoreboard"},
                        "evidence": {"files": ["sim/results.xml"], "tests": [], "commit": ""},
                        "validation": {"status": "closed", "verdict": "pass", "rationale": "baseline close"},
                    },
                },
            }
        )
        assert closed["result"]["status"] == "closed", closed
        reopened = call(
            {
                "tool": "oag.record",
                "arguments": {
                    "ip_dir": str(monotonic_ip),
                    "stage": "sim",
                    "claim": "monotonic obligation silently reopened",
                    "actor": {"kind": "ai", "id": "codex", "surface": "smoke"},
                    "status": "open",
                    "rocev": {
                        "obligation": {"id": "OBL_MONO_SCOREBOARD", "text": "reopened without decision", "status": "open"},
                        "contract": {"id": "CONTRACT_MONO_SCOREBOARD", "method": "scoreboard", "status": "open"},
                        "validation": {"status": "open", "verdict": "pending", "rationale": "silent downgrade"},
                    },
                },
            }
        )
        assert reopened["result"]["status"] == "open", reopened
        monotonic_check = call({"tool": "oag.check", "arguments": {"ip_dir": str(monotonic_ip)}})
        assert monotonic_check["result"]["ok"] is False, monotonic_check
        assert any("monotonic closure violation" in issue for issue in monotonic_check["result"]["issues"]), monotonic_check
        print(json.dumps({"ok": True, "ip": str(ip), "mcp_tools": len(tools["result"]["tools"])}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
