RTL-GEN PACKET MODE for atciic100_real. Packet attempt 0.

Return exactly one JSON object and nothing else. Do not wrap it in markdown.
Success schema:
{
  "files": [
    {"path": "atciic100_real/rtl/<module>.sv", "kind": "rtl", "content": "<SystemVerilog>"},
    {"path": "atciic100_real/rtl/rtl_contract.json", "kind": "rtl_contract", "content": "<optional JSON>"},
    {"path": "atciic100_real/rtl/rtl_authoring_notes/<packet>.md", "kind": "rtl_notes", "content": "<optional notes>"}
  ]
}

If this packet exposes a missing locked-truth decision, return a human_gate object instead of inventing SSOT, FL, coverage, interface, or performance semantics.

Packet execution rules:
- Author only RTL-owned artifacts for the current packet, plus local notes/contract metadata when useful.
- Do not edit SSOT YAML, FunctionalModel, coverage goals, protocol assertions, performance targets, or requirements.
- Do not emit placeholder, heartbeat-only, alive-only, or tie-off-only RTL to satisfy a manifest.
- For production-profile packets, add real SSOT-scaled implementation depth: state/control/data movement, nonconstant logic, and child wiring must be proportional to the packet tasks.
- For a module packet, focus on owner_file and every task content/detail/criteria/source_ref in the packet.
- If current owner_file content is provided, preserve prior slice logic and merge the new behavior; do not replace the file with a partial slice-only module.
- For mixed packets with locked-truth blockers, keep authoring LLM-actionable RTL/test/evidence work and leave the locked-truth tasks open.
- Return human_gate only when no LLM-actionable open work remains or the missing locked-truth decision blocks correct RTL authoring.
- For rtl_gate_evidence_closure, repair only LLM-actionable evidence gaps revealed by compile/lint/audit output; do not claim PASS.
- If rtl_gate_evidence_closure includes pending connection_contract_suggestions, you may use them as draft RTL wiring candidates to instantiate child modules and close hierarchy/signal-flow evidence, but they remain pending QA and must not be treated as SSOT authority.
- For rtl_gate_tool_evidence, do not fabricate compile/lint/sim/coverage artifacts; the runner should skip this packet until tools create evidence.
- For rtl_gate_contract_blocked, return human_gate only; missing SSOT connection contracts block correct top integration semantics.
- For rtl_gate_human_closure, return human_gate only; do not invent or edit human-locked authority.
- The headless runner will refresh filelist/provenance from LLM-authored artifacts after each packet.

Current packet: module__atciic100_apbslv
kind: module
work queue: 1/4 active packets (2 closed packets skipped from 14 total)
batch limit: 4; deferred active packets after this batch: 8
owner_module: atciic100_apbslv
owner_file: rtl/atciic100_apbslv.v

Base rtl-gen contract:
Prepare rtl-gen for atciic100_real using only atciic100_real/yaml/atciic100_real.ssot.yaml and atciic100_real/rtl/rtl_todo_plan.json, atciic100_real/rtl/rtl_authoring_plan.json, and packets under atciic100_real/rtl/authoring_packets. The script derives the TODO ledger from SSOT; the LLM must generate real RTL-owned artifacts that satisfy every TODO content/detail/criteria item and record provenance. Process one authoring packet at a time, module packets first, then unowned tasks if present, then rtl_gate_evidence_closure; skip rtl_gate_tool_evidence, rtl_gate_contract_blocked, and rtl_gate_human_closure until tool evidence or human-locked authority is available. Respect rtl_authoring_plan.execution_policy and each packet execution_policy: draft RTL may be authored while deferred_human_qa_allowed is true, but rtl-gen PASS/signoff is forbidden when pass_allowed is false. On repair attempts, use packet status_counts, open_required_count, Status, and Current reason fields to patch only the RTL-owned artifacts needed to close open TODOs. Use todo_plan_sha256=80d90eab12a41558550a46753666dc7718d4ebd3f45786f7c28471fa33c1b209. Repair only RTL-owned artifacts when validators fail. Do not change SSOT semantics, do not use fixed IP templates, and keep prompts focused on DUT-only compile/lint and FL-vs-RTL evidence. Production-profile RTL must also satisfy the SSOT-scaled rtl_implementation_depth_evidence gate; do not emit shallow shell modules that only name ports, instantiate children, or tie off outputs. If rtl_reference_profile is present, treat it as calibration-only scale evidence, never as source RTL or a clone template. If a missing locked-truth artifact, human authority approval, or SSOT connection contract prevents correct RTL authoring, return a human_gate JSON object instead of inventing semantics.

Authoring plan overview:
{
  "execution_policy": {
    "allowed_draft_work": [
      "Author module RTL from SSOT-derived TODO packets.",
      "Add tests, vectors, assertions, reports, and repair RTL under LLM-editable surfaces.",
      "Leave unresolved locked-truth decisions as human_gate/change-request records instead of changing SSOT authority."
    ],
    "blocked_by_llm_work": [
      {
        "gate_kind": "static_rtl_evidence",
        "owner_module": "atciic100_real",
        "reason": "50 static-evidence-required task(s) still lack DUT RTL evidence.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.static_rtl_evidence",
        "status": "open",
        "task_id": "RTL-0007"
      },
      {
        "gate_kind": "owner_logic_structure_evidence",
        "owner_module": "atciic100_real",
        "reason": "5 owner logic structure issue(s) remain. atciic100_apbslv: Behavior-owner module is not declared in its owner file; atciic100_ctrl: Behavior-owner module is not declared in its owner file; atciic100_fifo: Behavior-owner module is not declared in its owner file",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.owner_logic_structure_evidence",
        "status": "open",
        "task_id": "RTL-0008"
      },
      {
        "gate_kind": "rtl_placeholder_free_evidence",
        "owner_module": "atciic100_real",
        "reason": "1 RTL placeholder marker(s) remain. None:None: None",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.rtl_placeholder_free_evidence",
        "status": "open",
        "task_id": "RTL-0009"
      },
      {
        "gate_kind": "top_io_contract_evidence",
        "owner_module": "atciic100_real",
        "reason": "1 top IO contract issue(s) remain. atciic100_real: SSOT top module is not declared in listed RTL sources",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.top_io_contract_evidence",
        "status": "open",
        "task_id": "RTL-0010"
      },
      {
        "gate_kind": "top_output_drive_evidence",
        "owner_module": "atciic100_real",
        "reason": "1 top output drive issue(s) remain. atciic100_real: SSOT top module is not declared, so output drive evidence cannot be checked",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.top_output_drive_evidence",
        "status": "open",
        "task_id": "RTL-0011"
      },
      {
        "gate_kind": "top_input_consumption_evidence",
        "owner_module": "atciic100_real",
        "reason": "1 top input consumption issue(s) remain. atciic100_real: SSOT top module is not declared, so input consumption evidence cannot be checked",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.top_input_consumption_evidence",
        "status": "open",
        "task_id": "RTL-0012"
      },
      {
        "gate_kind": "manifest_hierarchy_integration",
        "owner_module": "atciic100_real",
        "reason": "5 manifest hierarchy integration issue(s) remain. atciic100_real: SSOT top module is not declared in listed RTL sources; atciic100_apbslv: SSOT manifest child module is not declared in listed RTL sources; atciic100_ctrl: SSOT manifest child module is not declared in listed RTL sources",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.manifest_hierarchy_integration",
        "status": "open",
        "task_id": "RTL-0013"
      },
      {
        "gate_kind": "manifest_signal_flow_evidence",
        "owner_module": "atciic100_real",
        "reason": "1 manifest signal-flow issue(s) remain. atciic100_real: None: SSOT top module is not declared, so manifest signal-flow evidence cannot be checked",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.manifest_signal_flow_evidence",
        "status": "open",
        "task_id": "RTL-0015"
      },
      {
        "gate_kind": "rtl_implementation_depth_evidence",
        "owner_module": "atciic100_real",
        "reason": "4 production RTL implementation-depth issue(s) remain. No listed DUT RTL sources are available for production implementation-depth audit; Production RTL implementation depth score is below the SSOT-derived or target-scale threshold: actual=0 required=92; Too few RTL modules contain implementation structure for the SSOT behavior complexity: actual=0 required=5",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.rtl_implementation_depth_evidence",
        "status": "open",
        "task_id": "RTL-0022"
      }
    ],
    "blocked_by_locked_truth": [
      {
        "gate_kind": "manifest_connection_contract_evidence",
        "owner_module": "atciic100_real",
        "reason": "9 SSOT connection contract issue(s) remain. atciic100_ctrl: SSOT connection contract targets a module not declared in RTL; atciic100_ctrl: SSOT connection contract targets a module not declared in RTL; atciic100_fifo: SSOT connection contract targets a module not declared in RTL",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.manifest_connection_contract_evidence",
        "status": "open",
        "task_id": "RTL-0016"
      },
      {
        "gate_kind": "golden_authority_artifacts",
        "owner_module": "atciic100_real",
        "reason": "model_signature.json drift at ssot_hash: expected current SSOT-derived value.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.golden_authority_artifacts",
        "status": "open",
        "task_id": "RTL-0020"
      }
    ],
    "blocked_by_tool_evidence": [
      {
        "gate_kind": "common_ai_agent_authoring",
        "owner_module": "atciic100_real",
        "reason": "Missing common_ai_agent RTL authoring provenance.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.common_ai_agent_authoring",
        "status": "open",
        "task_id": "RTL-0006"
      },
      {
        "gate_kind": "dut_compile",
        "owner_module": "atciic100_real",
        "reason": "Missing canonical DUT compile artifact: rtl/rtl_compile.json.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.dut_compile",
        "status": "open",
        "task_id": "RTL-0017"
      },
      {
        "gate_kind": "dut_lint",
        "owner_module": "atciic100_real",
        "reason": "Missing canonical DUT lint artifact: lint/dut_lint.json.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.dut_lint",
        "status": "open",
        "task_id": "RTL-0018"
      },
      {
        "gate_kind": "dynamic_todo_closure",
        "owner_module": "atciic100_real",
        "reason": "238 required non-closure TODO(s) remain open.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.dynamic_todo_closure",
        "status": "open",
        "task_id": "RTL-0019"
      },
      {
        "gate_kind": "protocol_assertion_evidence",
        "owner_module": "atciic100_real",
        "reason": "Missing protocol assertion simulation evidence: sim/assertion_failures.jsonl.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.protocol_assertion_evidence",
        "status": "open",
        "task_id": "RTL-0024"
      },
      {
        "gate_kind": "fl_rtl_goal_audit",
        "owner_module": "atciic100_real",
        "reason": "Missing FL-vs-RTL goal audit artifact: sim/fl_rtl_goal_audit.json.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.fl_rtl_goal_audit",
        "status": "open",
        "task_id": "RTL-0025"
      },
      {
        "gate_kind": "coverage_closure",
        "owner_module": "atciic100_real",
        "reason": "Missing coverage closure artifact: cov/coverage.json.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.coverage_closure",
        "status": "open",
        "task_id": "RTL-0026"
      }
    ],
    "connection_contract_gap": {
      "machine_readable_contract_count": 9,
      "reason": "Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.",
      "required_for_profile": true,
      "status": "ok"
    },
    "connection_contract_suggestions": {
      "path": "rtl/connection_contract_suggestions.json",
      "rule": "Suggestions are emitted only when production connection contracts are missing.",
      "sample_rows": [],
      "summary": {
        "applied_to_ssot": false,
        "pending_review": 0,
        "status": "not_required",
        "suggested_rows": 0
      }
    },
    "deferred_human_qa_allowed": true,
    "draft_allowed": true,
    "gate_status": "fail",
    "hard_blockers": [],
    "open_required_todos": 239,
    "pass_allowed": false,
    "pass_rule": "rtl-gen may claim PASS only when every required TODO and every locked-truth gate has pass status.",
    "stop_conditions": [
      "Do not edit SSOT/FL/coverage/interface/performance authority artifacts without human approval.",
      "Do not claim rtl-gen PASS while pass_allowed is false.",
      "Do not sign off top integration while required connection contracts are missing."
    ],
    "tool_evidence_plan": [
      {
        "artifact": "rtl/rtl_authoring_provenance.json",
        "artifacts": [
          "atciic100_real/rtl/rtl_authoring_provenance.json",
          "atciic100_real/rtl/rtl_todo_plan.json"
        ],
        "closure_rule": "Refresh common_ai_agent_authoring provenance against the current rtl_todo_plan hash.",
        "commands": [
          "python3 src/headless_workflow.py --root . --ip atciic100_real --stages rtl-gen",
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py atciic100_real --root . --audit-rtl"
        ],
        "gate_kind": "common_ai_agent_authoring",
        "prerequisites": [
          "An LLM authoring pass emitted or repaired DUT RTL files."
        ],
        "reason": "Missing common_ai_agent RTL authoring provenance.",
        "source_ref": "quality_gates.rtl_gen.common_ai_agent_authoring",
        "stage_sequence": [
          "ssot-rtl"
        ],
        "status": "open",
        "task_id": "RTL-0006"
      },
      {
        "artifact": "rtl/rtl_compile.json",
        "artifacts": [
          "atciic100_real/rtl/rtl_compile.json",
          "atciic100_real/rtl/rtl_compile.log"
        ],
        "closure_rule": "rtl_compile.json must be DUT-only, fresh, passed, and cover every current DUT RTL file.",
        "commands": [
          "python3 workflow/rtl-gen/scripts/rtl_compile_report.py atciic100_real --top atciic100_real --project-root .",
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py atciic100_real --root . --audit-rtl"
        ],
        "gate_kind": "dut_compile",
        "prerequisites": [
          "atciic100_real/list/atciic100_real.f covers the current DUT RTL sources."
        ],
        "reason": "Missing canonical DUT compile artifact: rtl/rtl_compile.json.",
        "source_ref": "quality_gates.rtl_gen.dut_compile",
        "stage_sequence": [
          "ssot-rtl",
          "dut_compile"
        ],
        "status": "open",
        "task_id": "RTL-0017"
      },
      {
        "artifact": "lint/dut_lint.json",
        "artifacts": [
          "atciic100_real/lint/dut_lint.json"
        ],
        "closure_rule": "dut_lint.json must be DUT-only, fresh, passed, and report zero warnings/errors.",
        "commands": [
          "python3 workflow/lint/scripts/dut_lint_report.py atciic100_real --top atciic100_real",
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py atciic100_real --root . --audit-rtl"
        ],
        "gate_kind": "dut_lint",
        "prerequisites": [
          "atciic100_real/list/atciic100_real.f covers the current DUT RTL/header sources."
        ],
        "reason": "Missing canonical DUT lint artifact: lint/dut_lint.json.",
        "source_ref": "quality_gates.rtl_gen.dut_lint",
        "stage_sequence": [
          "lint",
          "dut_lint"
        ],
        "status": "open",
        "task_id": "RTL-0018"
      },
      {
        "artifact": "rtl/rtl_todo_plan.json",
        "artifacts": [
          "atciic100_real/rtl/rtl_todo_plan.json",
          "atciic100_real/rtl/rtl_authoring_status.md"
        ],
        "closure_rule": "dynamic_todo_closure passes only when every required non-closure TODO is already pass.",
        "commands": [
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py atciic100_real --root . --audit-rtl"
        ],
        "gate_kind": "dynamic_todo_closure",
        "prerequisites": [
          "All non-closure required TODOs have pass status."
        ],
        "reason": "238 required non-closure TODO(s) remain open.",
        "source_ref": "quality_gates.rtl_gen.dynamic_todo_closure",
        "stage_sequence": [
          "audit-rtl"
        ],
        "status": "open",
        "task_id": "RTL-0019"
      },
      {
        "artifact": "verify/protocol_assertions.sva",
        "artifacts": [
          "atciic100_real/verify/protocol_assertions.sva",
          "atciic100_real/verify/protocol_assertions.summary.json",
          "atciic100_real/sim/assertion_failures.jsonl"
        ],
        "closure_rule": "Generated assertions exist and latest simulation has zero assertion failure records.",
        "commands": [
          "python3 workflow/fl-model-gen/scripts/emit_protocol_assertions.py atciic100_real --root .",
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py atciic100_real --root . --audit-rtl"
        ],
        "gate_kind": "protocol_assertion_evidence",
        "prerequisites": [
          "SSOT cycle_model/protocol rules are machine-checkable.",
          "Simulation has run after RTL edits."
        ],
        "reason": "Missing protocol assertion simulation evidence: sim/assertion_failures.jsonl.",
        "source_ref": "quality_gates.rtl_gen.protocol_assertion_evidence",
        "stage_sequence": [
          "ssot-protocol-assertions",
          "sim"
        ],
        "status": "open",
        "task_id": "RTL-0024"
      },
      {
        "artifact": "sim/fl_rtl_goal_audit.json",
        "artifacts": [
          "atciic100_real/sim/fl_rtl_goal_audit.json"
        ],
        "closure_rule": "fl_rtl_goal_audit.json must be fresh and status=pass.",
        "commands": [
          "python3 workflow/sim_debug/scripts/audit_fl_rtl_equivalence_goal.py atciic100_real --root .",
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py atciic100_real --root . --audit-rtl"
        ],
        "gate_kind": "fl_rtl_goal_audit",
        "prerequisites": [
          "FL model, equivalence goals, TB, and simulation evidence are current."
        ],
        "reason": "Missing FL-vs-RTL goal audit artifact: sim/fl_rtl_goal_audit.json.",
        "source_ref": "quality_gates.rtl_gen.fl_rtl_goal_audit",
        "stage_sequence": [
          "ssot-fl-model",
          "ssot-equiv-goals",
          "ssot-tb-cocotb",
          "sim",
          "goal-audit"
        ],
        "status": "open",
        "task_id": "RTL-0025"
      },
      {
        "artifact": "cov/coverage.json",
        "artifacts": [
          "atciic100_real/cov/coverage.json"
        ],
        "closure_rule": "coverage.json must be fresh, come from ssot_coverage_summary, and close every planned required bin.",
        "commands": [
          "python3 workflow/coverage/scripts/ssot_coverage_summary.py atciic100_real",
          "python3 workflow/rtl-gen/scripts/derive_rtl_todos.py atciic100_real --root . --audit-rtl"
        ],
        "gate_kind": "coverage_closure",
        "prerequisites": [
          "Simulation evidence exists and planned coverage bins are observable."
        ],
        "reason": "Missing coverage closure artifact: cov/coverage.json.",
        "source_ref": "quality_gates.rtl_gen.coverage_closure",
        "stage_sequence": [
          "sim",
          "coverage"
        ],
        "status": "open",
        "task_id": "RTL-0026"
      }
    ]
  },
  "ip": "atciic100_real",
  "packets": [
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__atciic100_apbslv.json",
      "kind": "module",
      "llm_actionable_open_count": 27,
      "open_required_count": 27,
      "owner_file": "rtl/atciic100_apbslv.v",
      "owner_module": "atciic100_apbslv",
      "packet_id": "module__atciic100_apbslv",
      "required_count": 27,
      "status_counts": {
        "open": 27
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__atciic100_ctrl__function_model_01.json",
      "kind": "module",
      "llm_actionable_open_count": 48,
      "open_required_count": 48,
      "owner_file": "rtl/atciic100_ctrl.v",
      "owner_module": "atciic100_ctrl",
      "packet_id": "module__atciic100_ctrl__function_model_01",
      "required_count": 48,
      "status_counts": {
        "open": 48
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__atciic100_ctrl__function_model_02.json",
      "kind": "module",
      "llm_actionable_open_count": 48,
      "open_required_count": 48,
      "owner_file": "rtl/atciic100_ctrl.v",
      "owner_module": "atciic100_ctrl",
      "packet_id": "module__atciic100_ctrl__function_model_02",
      "required_count": 48,
      "status_counts": {
        "open": 48
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__atciic100_ctrl__cycle_model.json",
      "kind": "module",
      "llm_actionable_open_count": 22,
      "open_required_count": 22,
      "owner_file": "rtl/atciic100_ctrl.v",
      "owner_module": "atciic100_ctrl",
      "packet_id": "module__atciic100_ctrl__cycle_model",
      "required_count": 22,
      "status_counts": {
        "open": 22
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__atciic100_ctrl__fsm.json",
      "kind": "module",
      "llm_actionable_open_count": 18,
      "open_required_count": 18,
      "owner_file": "rtl/atciic100_ctrl.v",
      "owner_module": "atciic100_ctrl",
      "packet_id": "module__atciic100_ctrl__fsm",
      "required_count": 18,
      "status_counts": {
        "open": 18
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__atciic100_ctrl__function_model_03.json",
      "kind": "module",
      "llm_actionable_open_count": 2,
      "open_required_count": 2,
      "owner_file": "rtl/atciic100_ctrl.v",
      "owner_module": "atciic100_ctrl",
      "packet_id": "module__atciic100_ctrl__function_model_03",
      "required_count": 2,
      "status_counts": {
        "open": 2
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__atciic100_ctrl__equivalence.json",
      "kind": "module",
      "llm_actionable_open_count": 1,
      "open_required_count": 1,
      "owner_file": "rtl/atciic100_ctrl.v",
      "owner_module": "atciic100_ctrl",
      "packet_id": "module__atciic100_ctrl__equivalence",
      "required_count": 1,
      "status_counts": {
        "open": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__atciic100_ctrl__workflow_todo.json",
      "kind": "module",
      "llm_actionable_open_count": 1,
      "open_required_count": 1,
      "owner_file": "rtl/atciic100_ctrl.v",
      "owner_module": "atciic100_ctrl",
      "packet_id": "module__atciic100_ctrl__workflow_todo",
      "required_count": 1,
      "status_counts": {
        "open": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__atciic100_fifo.json",
      "kind": "module",
      "llm_actionable_open_count": 3,
      "open_required_count": 3,
      "owner_file": "rtl/atciic100_fifo.v",
      "owner_module": "atciic100_fifo",
      "packet_id": "module__atciic100_fifo",
      "required_count": 3,
      "status_counts": {
        "open": 3
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__atciic100_gsf.json",
      "kind": "module",
      "llm_actionable_open_count": 9,
      "open_required_count": 9,
      "owner_file": "rtl/atciic100_gsf.v",
      "owner_module": "atciic100_gsf",
      "packet_id": "module__atciic100_gsf",
      "required_count": 9,
      "status_counts": {
        "open": 9
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__atciic100_real.json",
      "kind": "module",
      "llm_actionable_open_count": 42,
      "open_required_count": 42,
      "owner_file": "rtl/atciic100_real.sv",
      "owner_module": "atciic100_real",
      "packet_id": "module__atciic100_real",
      "required_count": 43,
      "status_counts": {
        "open": 42,
        "pass": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/rtl_gate_evidence_closure.json",
      "kind": "gate",
      "llm_actionable_open_count": 9,
      "open_required_count": 9,
      "owner_file": "rtl/atciic100_real.sv",
      "owner_module": "atciic100_real",
      "packet_id": "rtl_gate_evidence_closure",
      "required_count": 10,
      "status_counts": {
        "open": 9,
        "pass": 1
      }
    },
    {
      "human_locked_open_count": 2,
      "json": "rtl/authoring_packets/rtl_gate_human_closure.json",
      "kind": "gate",
      "llm_actionable_open_count": 0,
      "open_required_count": 2,
      "owner_file": "rtl/atciic100_real.sv",
      "owner_module": "atciic100_real",
      "packet_id": "rtl_gate_human_closure",
      "required_count": 7,
      "status_counts": {
        "open": 2,
        "pass": 5
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/rtl_gate_tool_evidence.json",
      "kind": "gate",
      "llm_actionable_open_count": 0,
      "open_required_count": 7,
      "owner_file": "rtl/atciic100_real.sv",
      "owner_module": "atciic100_real",
      "packet_id": "rtl_gate_tool_evidence",
      "required_count": 7,
      "status_counts": {
        "open": 7
      }
    }
  ],
  "policy": {
    "dynamic_task_rule": "Use every required task in this file as the active RTL implementation checklist; add as many UI todos as this plan requires.",
    "fixed_template_role": "seed_only",
    "no_orphan_function_level": true,
    "reference_profile_rule": "Optional rtl_reference_profile artifacts are calibration-only scale reports; they must not be copied, transformed, or used as fixed RTL templates.",
    "rtl_gate_todo_rule": "RTL-gen quality gates are first-class rtl_gate.rtl_gen TODOs; compile/lint/static/ownership/owner-logic/placeholder-free/implementation-depth/top-io/top-output-drive/top-input-consumption/hierarchy/port-connection/signal-flow/connection-contract gates must close as TODOs before PASS.",
    "rtl_quality_profile": "production",
    "rtl_target_scale": {},
    "rtl_target_scale_waiver": {},
    "single_source_of_truth": "SSOT YAML is the only authority for function_model, cycle_model, RTL ownership, DV plan, and coverage.",
    "ssot_workflow_todo_rule": "workflow_todos.rtl-gen[] entries are first-class downstream tasks; content/detail/criteria must be preserved and satisfied by RTL evidence.",
    "target_scale_rule": "Optional quality_gates.rtl_gen.target_scale is SSOT-locked human policy. It can be calibrated from a reference profile, but it is enforced as generic structural depth evidence, not as copied reference RTL."
  },
  "reference_profile": {},
  "summary": {
    "connection_contract_suggestions_present": false,
    "deferred_human_qa_allowed": true,
    "gate_packets": 3,
    "human_locked_packets": 1,
    "human_locked_tasks": 2,
    "llm_actionable_packets": 12,
    "llm_actionable_tasks": 230,
    "max_packet_required_tasks": 48,
    "module_packets": 11,
    "next_llm_packets": [
      "module__atciic100_apbslv",
      "module__atciic100_ctrl__function_model_01",
      "module__atciic100_ctrl__function_model_02",
      "module__atciic100_ctrl__cycle_model",
      "module__atciic100_ctrl__fsm",
      "module__atciic100_ctrl__function_model_03",
      "module__atciic100_ctrl__equivalence",
      "module__atciic100_ctrl__workflow_todo"
    ],
    "packet_task_limit": 48,
    "packets": 14,
    "pass_allowed": false,
    "pending_connection_contract_suggestions": 0,
    "recommended_packet_batch_limit": 4,
    "reference_profile_present": false,
    "reference_scale_gap_present": false,
    "required_tasks": 246,
    "sliced_module_packets": 7,
    "target_scale_present": false,
    "tool_evidence_packets": 1,
    "tool_evidence_tasks": 7,
    "total_tasks": 246,
    "unowned_packets": 0
  },
  "target_scale": {},
  "todo_plan_sha256": "80d90eab12a41558550a46753666dc7718d4ebd3f45786f7c28471fa33c1b209",
  "top": "atciic100_real",
  "type": "rtl_authoring_plan"
}

Current owner RTL file (rtl/atciic100_apbslv.v):
<missing or not authored yet>

Current packet JSON (rtl/authoring_packets/module__atciic100_apbslv.json):
{
  "context": {
    "connection_contract_gap": {
      "machine_readable_contract_count": 9,
      "reason": "Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.",
      "required_for_profile": true,
      "status": "ok"
    },
    "connection_contract_suggestions": {},
    "module_slice": {
      "count": 1,
      "enabled": false,
      "index": 1,
      "key": "all",
      "module_task_count": 27,
      "task_limit": 48
    },
    "owner": {
      "file": "rtl/atciic100_apbslv.v",
      "name": "atciic100_apbslv",
      "refs": [
        "io_list",
        "io_list.interfaces.apb_slave",
        "registers",
        "registers.register_list"
      ],
      "wiring_only": false
    },
    "peer_modules": [
      {
        "file": "rtl/atciic100_apbslv.v",
        "name": "atciic100_apbslv",
        "wiring_only": false
      },
      {
        "file": "rtl/atciic100_ctrl.v",
        "name": "atciic100_ctrl",
        "wiring_only": false
      },
      {
        "file": "rtl/atciic100_fifo.v",
        "name": "atciic100_fifo",
        "wiring_only": false
      },
      {
        "file": "rtl/atciic100_gsf.v",
        "name": "atciic100_gsf",
        "wiring_only": false
      },
      {
        "file": "rtl/atciic100_real.sv",
        "name": "atciic100_real",
        "wiring_only": false
      }
    ],
    "quality_profile": "production",
    "reference_profile": null,
    "ssot_connection_contracts": [
      {
        "instance": "",
        "machine_readable": true,
        "module": "atciic100_apbslv",
        "port": "cmd_reg",
        "signal": "cmd",
        "signal_terms": [
          "cmd"
        ],
        "source_ref": "sub_modules[1].connections[0]"
      },
      {
        "instance": "",
        "machine_readable": true,
        "module": "atciic100_apbslv",
        "port": "data_in",
        "signal": "pwdata",
        "signal_terms": [
          "pwdata"
        ],
        "source_ref": "sub_modules[2].connections[0]"
      }
    ],
    "ssot_top_io_contracts": [],
    "target_scale": null
  },
  "execution_policy": {
    "blocked_by_locked_truth": [],
    "blocked_by_tool_evidence": [],
    "contract_blocked_open_count": 0,
    "deferred_human_qa_allowed": true,
    "draft_allowed": true,
    "evidence_closure_allowed": false,
    "human_locked_open_count": 0,
    "integration_signoff_allowed": true,
    "llm_actionable": true,
    "llm_actionable_open_count": 27,
    "open_required_count": 27,
    "pass_allowed": false,
    "stop_conditions": [
      "Close this packet only after every required task in the packet has pass status.",
      "Return human_gate/change-request JSON when locked truth is missing instead of inventing semantics.",
      "Never use a fixed RTL template as the implementation."
    ],
    "tool_evidence_open_count": 0,
    "tool_evidence_plan": [],
    "work_allowed": true
  },
  "ip": "atciic100_real",
  "kind": "module",
  "owner_file": "rtl/atciic100_apbslv.v",
  "owner_module": "atciic100_apbslv",
  "packet_id": "module__atciic100_apbslv",
  "rules": [
    "No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.",
    "Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.",
    "Every task must satisfy content, detail, and criteria before the packet is closed.",
    "For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.",
    "Record generated RTL files and todo_plan_sha256 in rtl_authoring_provenance.json."
  ],
  "schema_version": 1,
  "source_plan": "rtl/rtl_todo_plan.json",
  "summary": {
    "categories": {
      "equivalence.module": 1,
      "io_list.port": 15,
      "registers.register": 10,
      "workflow_todo.rtl_gen": 1
    },
    "module_slice": {
      "count": 1,
      "enabled": false,
      "index": 1,
      "key": "all",
      "module_task_count": 27,
      "task_limit": 48
    },
    "open_required_count": 27,
    "required_count": 27,
    "source_refs": [
      "workflow_todos.rtl-gen[0]",
      "registers.register_list.ID",
      "registers.register_list.REV",
      "registers.register_list.CFG",
      "registers.register_list.INT_EN",
      "registers.register_list.INT_ST",
      "registers.register_list.ADDR",
      "registers.register_list.DATA",
      "registers.register_list.CMD",
      "registers.register_list.CTRL",
      "registers.register_list.SETUP",
      "sub_modules.atciic100_apbslv.module_equivalence",
      "io_list.clock_domains.pclk.ports.pclk",
      "io_list.resets.presetn.ports.presetn",
      "io_list.interfaces.apb_slave.ports.psel",
      "io_list.interfaces.apb_slave.ports.penable",
      "io_list.interfaces.apb_slave.ports.pwrite",
      "io_list.interfaces.apb_slave.ports.paddr",
      "io_list.interfaces.apb_slave.ports.pwdata",
      "io_list.interfaces.apb_slave.ports.prdata",
      "io_list.interfaces.i2c_bus.ports.scl_i",
      "io_list.interfaces.i2c_bus.ports.sda_i",
      "io_list.interfaces.i2c_bus.ports.scl_o",
      "io_list.interfaces.i2c_bus.ports.sda_o"
    ],
    "status_counts": {
      "open": 27
    },
    "task_count": 27
  },
  "tasks": [
    {
      "category": "workflow_todo.rtl_gen",
      "content": "Implement APB Slave Logic",
      "criteria": [
        "APB R/W functional",
        "All register fields readable/writable per spec",
        "SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json",
        "RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets",
        "Traceability keeps source_ref workflow_todos.rtl-gen[0]",
        "Primary implementation evidence is in rtl/atciic100_apbslv.v",
        "Semantic source_refs covered: registers"
      ],
      "detail": "Decode paddr[5:2] to specific registers. Implement read data mux and write decode.\nSSOT ref: workflow_todos.rtl-gen[0].\nOwner: atciic100_apbslv in rtl/atciic100_apbslv.v via workflow_todos.owner.\nSSOT item context: id=RTL_TODO_APB.",
      "evidence_terms": [
        "APB",
        "RTL_TODO_APB",
        "TODO",
        "apbslv",
        "atciic100",
        "atciic100_apbslv"
      ],
      "id": "RTL-0027",
      "owner_file": "rtl/atciic100_apbslv.v",
      "owner_module": "atciic100_apbslv",
      "priority": "high",
      "required": true,
      "source_ref": "workflow_todos.rtl-gen[0]",
      "ssot_context": {
        "id": "RTL_TODO_APB"
      },
      "ssot_refs": [
        "registers",
        "workflow_todos.rtl-gen[0]"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 3,
        "required_terms": [
          "APB",
          "RTL_TODO_APB",
          "TODO",
          "apbslv",
          "atciic100",
          "atciic100_apbslv"
        ],
        "source_scope": "rtl/atciic100_apbslv.v",
        "status": "missing"
      },
      "todo_completion": {
        "criteria_total": 7,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/atciic100_apbslv.v.",
        "required": true,
        "status": "open"
      },
      "workflow_todo": {
        "id": "RTL_TODO_APB",
        "source_refs": [
          "registers"
        ],
        "stage": "rtl-gen",
        "user_category": ""
      }
    },
    {
      "category": "registers.register",
      "content": "Implement CSR/register ID",
      "criteria": [
        "Address/decode behavior matches SSOT",
        "Readable fields return RTL state, not a constant placeholder",
        "Write semantics and illegal access response match SSOT",
        "Traceability keeps source_ref registers.register_list.ID",
        "Primary implementation evidence is in rtl/atciic100_apbslv.v",
        "ID width matches SSOT value 32",
        "ID reset behavior matches SSOT value 514",
        "ID access policy ro is implemented without read/write shortcuts",
        "ID decode uses SSOT address/offset 0"
      ],
      "detail": "Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.\nSSOT ref: registers.register_list.ID.\nOwner: atciic100_apbslv in rtl/atciic100_apbslv.v via registers.\nSSOT item context: name=ID; width=32; reset=514; access=ro; offset=0.",
      "evidence_terms": [],
      "id": "RTL-0173",
      "owner_file": "rtl/atciic100_apbslv.v",
      "owner_module": "atciic100_apbslv",
      "priority": "high",
      "required": true,
      "source_ref": "registers.register_list.ID",
      "ssot_context": {
        "access": "ro",
        "name": "ID",
        "offset": "0",
        "reset": "514",
        "width": "32"
      },
      "ssot_refs": [
        "registers.register_list.ID"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 9,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/atciic100_apbslv.v.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "registers.register",
      "content": "Implement CSR/register REV",
      "criteria": [
        "Address/decode behavior matches SSOT",
        "Readable fields return RTL state, not a constant placeholder",
        "Write semantics and illegal access response match SSOT",
        "Traceability keeps source_ref registers.register_list.REV",
        "Primary implementation evidence is in rtl/atciic100_apbslv.v",
        "REV width matches SSOT value 32",
        "REV reset behavior matches SSOT value 4098",
        "REV access policy ro is implemented without read/write shortcuts",
        "REV decode uses SSOT address/offset 4"
      ],
      "detail": "Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.\nSSOT ref: registers.register_list.REV.\nOwner: atciic100_apbslv in rtl/atciic100_apbslv.v via registers.\nSSOT item context: name=REV; width=32; reset=4098; access=ro; offset=4.",
      "evidence_terms": [],
      "id": "RTL-0174",
      "owner_file": "rtl/atciic100_apbslv.v",
      "owner_module": "atciic100_apbslv",
      "priority": "high",
      "required": true,
      "source_ref": "registers.register_list.REV",
      "ssot_context": {
        "access": "ro",
        "name": "REV",
        "offset": "4",
        "reset": "4098",
        "width": "32"
      },
      "ssot_refs": [
        "registers.register_list.REV"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 9,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/atciic100_apbslv.v.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "registers.register",
      "content": "Implement CSR/register CFG",
      "criteria": [
        "Address/decode behavior matches SSOT",
        "Readable fields return RTL state, not a constant placeholder",
        "Write semantics and illegal access response match SSOT",
        "Traceability keeps source_ref registers.register_list.CFG",
        "Primary implementation evidence is in rtl/atciic100_apbslv.v",
        "CFG width matches SSOT value 32",
        "CFG reset behavior matches SSOT value 0",
        "CFG access policy ro is implemented without read/write shortcuts",
        "CFG decode uses SSOT address/offset 8"
      ],
      "detail": "Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.\nSSOT ref: registers.register_list.CFG.\nOwner: atciic100_apbslv in rtl/atciic100_apbslv.v via registers.\nSSOT item context: name=CFG; width=32; reset=0; access=ro; offset=8.",
      "evidence_terms": [],
      "id": "RTL-0175",
      "owner_file": "rtl/atciic100_apbslv.v",
      "owner_module": "atciic100_apbslv",
      "priority": "high",
      "required": true,
      "source_ref": "registers.register_list.CFG",
      "ssot_context": {
        "access": "ro",
        "name": "CFG",
        "offset": "8",
        "reset": "0",
        "width": "32"
      },
      "ssot_refs": [
        "registers.register_list.CFG"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 9,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/atciic100_apbslv.v.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "registers.register",
      "content": "Implement CSR/register INT_EN",
      "criteria": [
        "Address/decode behavior matches SSOT",
        "Readable fields return RTL state, not a constant placeholder",
        "Write semantics and illegal access response match SSOT",
        "Traceability keeps source_ref registers.register_list.INT_EN",
        "Primary implementation evidence is in rtl/atciic100_apbslv.v",
        "INT_EN width matches SSOT value 32",
        "INT_EN reset behavior matches SSOT value 0",
        "INT_EN access policy rw is implemented without read/write shortcuts",
        "INT_EN decode uses SSOT address/offset 12"
      ],
      "detail": "Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.\nSSOT ref: registers.register_list.INT_EN.\nOwner: atciic100_apbslv in rtl/atciic100_apbslv.v via registers.\nSSOT item context: name=INT_EN; width=32; reset=0; access=rw; offset=12.",
      "evidence_terms": [],
      "id": "RTL-0176",
      "owner_file": "rtl/atciic100_apbslv.v",
      "owner_module": "atciic100_apbslv",
      "priority": "high",
      "required": true,
      "source_ref": "registers.register_list.INT_EN",
      "ssot_context": {
        "access": "rw",
        "name": "INT_EN",
        "offset": "12",
        "reset": "0",
        "width": "32"
      },
      "ssot_refs": [
        "registers.register_list.INT_EN"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 9,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/atciic100_apbslv.v.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "registers.register",
      "content": "Implement CSR/register INT_ST",
      "criteria": [
        "Address/decode behavior matches SSOT",
        "Readable fields return RTL state, not a constant placeholder",
        "Write semantics and illegal access response match SSOT",
        "Traceability keeps source_ref registers.register_list.INT_ST",
        "Primary implementation evidence is in rtl/atciic100_apbslv.v",
        "INT_ST width matches SSOT value 32",
        "INT_ST reset behavior matches SSOT value 1",
        "INT_ST access policy rw1c is implemented without read/write shortcuts",
        "INT_ST decode uses SSOT address/offset 16"
      ],
      "detail": "Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.\nSSOT ref: registers.register_list.INT_ST.\nOwner: atciic100_apbslv in rtl/atciic100_apbslv.v via registers.\nSSOT item context: name=INT_ST; width=32; reset=1; access=rw1c; offset=16.",
      "evidence_terms": [],
      "id": "RTL-0177",
      "owner_file": "rtl/atciic100_apbslv.v",
      "owner_module": "atciic100_apbslv",
      "priority": "high",
      "required": true,
      "source_ref": "registers.register_list.INT_ST",
      "ssot_context": {
        "access": "rw1c",
        "name": "INT_ST",
        "offset": "16",
        "reset": "1",
        "width": "32"
      },
      "ssot_refs": [
        "registers.register_list.INT_ST"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 9,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/atciic100_apbslv.v.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "registers.register",
      "content": "Implement CSR/register ADDR",
      "criteria": [
        "Address/decode behavior matches SSOT",
        "Readable fields return RTL state, not a constant placeholder",
        "Write semantics and illegal access response match SSOT",
        "Traceability keeps source_ref registers.register_list.ADDR",
        "Primary implementation evidence is in rtl/atciic100_apbslv.v",
        "ADDR width matches SSOT value 32",
        "ADDR reset behavior matches SSOT value 0",
        "ADDR access policy rw is implemented without read/write shortcuts",
        "ADDR decode uses SSOT address/offset 20"
      ],
      "detail": "Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.\nSSOT ref: registers.register_list.ADDR.\nOwner: atciic100_apbslv in rtl/atciic100_apbslv.v via registers.\nSSOT item context: name=ADDR; width=32; reset=0; access=rw; offset=20.",
      "evidence_terms": [],
      "id": "RTL-0178",
      "owner_file": "rtl/atciic100_apbslv.v",
      "owner_module": "atciic100_apbslv",
      "priority": "high",
      "required": true,
      "source_ref": "registers.register_list.ADDR",
      "ssot_context": {
        "access": "rw",
        "name": "ADDR",
        "offset": "20",
        "reset": "0",
        "width": "32"
      },
      "ssot_refs": [
        "registers.register_list.ADDR"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 9,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/atciic100_apbslv.v.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "registers.register",
      "content": "Implement CSR/register DATA",
      "criteria": [
        "Address/decode behavior matches SSOT",
        "Readable fields return RTL state, not a constant placeholder",
        "Write semantics and illegal access response match SSOT",
        "Traceability keeps source_ref registers.register_list.DATA",
        "Primary implementation evidence is in rtl/atciic100_apbslv.v",
        "DATA width matches SSOT value 32",
        "DATA reset behavior matches SSOT value 0",
        "DATA access policy rw is implemented without read/write shortcuts",
        "DATA decode uses SSOT address/offset 24"
      ],
      "detail": "Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.\nSSOT ref: registers.register_list.DATA.\nOwner: atciic100_apbslv in rtl/atciic100_apbslv.v via registers.\nSSOT item context: name=DATA; width=32; reset=0; access=rw; offset=24.",
      "evidence_terms": [],
      "id": "RTL-0179",
      "owner_file": "rtl/atciic100_apbslv.v",
      "owner_module": "atciic100_apbslv",
      "priority": "high",
      "required": true,
      "source_ref": "registers.register_list.DATA",
      "ssot_context": {
        "access": "rw",
        "name": "DATA",
        "offset": "24",
        "reset": "0",
        "width": "32"
      },
      "ssot_refs": [
        "registers.register_list.DATA"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 9,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/atciic100_apbslv.v.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "registers.register",
      "content": "Implement CSR/register CMD",
      "criteria": [
        "Address/decode behavior matches SSOT",
        "Readable fields return RTL state, not a constant placeholder",
        "Write semantics and illegal access response match SSOT",
        "Traceability keeps source_ref registers.register_list.CMD",
        "Primary implementation evidence is in rtl/atciic100_apbslv.v",
        "CMD width matches SSOT value 32",
        "CMD reset behavior matches SSOT value 0",
        "CMD access policy rw is implemented without read/write shortcuts",
        "CMD decode uses SSOT address/offset 28"
      ],
      "detail": "Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.\nSSOT ref: registers.register_list.CMD.\nOwner: atciic100_apbslv in rtl/atciic100_apbslv.v via registers.\nSSOT item context: name=CMD; width=32; reset=0; access=rw; offset=28.",
      "evidence_terms": [],
      "id": "RTL-0180",
      "owner_file": "rtl/atciic100_apbslv.v",
      "owner_module": "atciic100_apbslv",
      "priority": "high",
      "required": true,
      "source_ref": "registers.register_list.CMD",
      "ssot_context": {
        "access": "rw",
        "name": "CMD",
        "offset": "28",
        "reset": "0",
        "width": "32"
      },
      "ssot_refs": [
        "registers.register_list.CMD"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 9,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/atciic100_apbslv.v.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "registers.register",
      "content": "Implement CSR/register CTRL",
      "criteria": [
        "Address/decode behavior matches SSOT",
        "Readable fields return RTL state, not a constant placeholder",
        "Write semantics and illegal access response match SSOT",
        "Traceability keeps source_ref registers.register_list.CTRL",
        "Primary implementation evidence is in rtl/atciic100_apbslv.v",
        "CTRL width matches SSOT value 32",
        "CTRL reset behavior matches SSOT value 7936",
        "CTRL access policy rw is implemented without read/write shortcuts",
        "CTRL decode uses SSOT address/offset 32"
      ],
      "detail": "Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.\nSSOT ref: registers.register_list.CTRL.\nOwner: atciic100_apbslv in rtl/atciic100_apbslv.v via registers.\nSSOT item context: name=CTRL; width=32; reset=7936; access=rw; offset=32.",
      "evidence_terms": [],
      "id": "RTL-0181",
      "owner_file": "rtl/atciic100_apbslv.v",
      "owner_module": "atciic100_apbslv",
      "priority": "high",
      "required": true,
      "source_ref": "registers.register_list.CTRL",
      "ssot_context": {
        "access": "rw",
        "name": "CTRL",
        "offset": "32",
        "reset": "7936",
        "width": "32"
      },
      "ssot_refs": [
        "registers.register_list.CTRL"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 9,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/atciic100_apbslv.v.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "registers.register",
      "content": "Implement CSR/register SETUP",
      "criteria": [
        "Address/decode behavior matches SSOT",
        "Readable fields return RTL state, not a constant placeholder",
        "Write semantics and illegal access response match SSOT",
        "Traceability keeps source_ref registers.register_list.SETUP",
        "Primary implementation evidence is in rtl/atciic100_apbslv.v",
        "SETUP width matches SSOT value 32",
        "SETUP reset behavior matches SSOT value 0",
        "SETUP access policy rw is implemented without read/write shortcuts",
        "SETUP decode uses SSOT address/offset 36"
      ],
      "detail": "Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.\nSSOT ref: registers.register_list.SETUP.\nOwner: atciic100_apbslv in rtl/atciic100_apbslv.v via registers.\nSSOT item context: name=SETUP; width=32; reset=0; access=rw; offset=36.",
      "evidence_terms": [],
      "id": "RTL-0182",
      "owner_file": "rtl/atciic100_apbslv.v",
      "owner_module": "atciic100_apbslv",
      "priority": "high",
      "required": true,
      "source_ref": "registers.register_list.SETUP",
      "ssot_context": {
        "access": "rw",
        "name": "SETUP",
        "offset": "36",
        "reset": "0",
        "width": "32"
      },
      "ssot_refs": [
        "registers.register_list.SETUP"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 9,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/atciic100_apbslv.v.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "equivalence.module",
      "content": "Prove module atciic100_apbslv is functionally equivalent to FL",
      "criteria": [
        "verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module",
        "cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff",
        "scoreboard row fl_expected.model_api is FunctionalModel.apply",
        "scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data",
        "Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong",
        "Traceability keeps source_ref sub_modules.atciic100_apbslv.module_equivalence",
        "Primary implementation evidence is in rtl/atciic100_apbslv.v"
      ],
      "detail": "This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.\nSSOT ref: sub_modules.atciic100_apbslv.module_equivalence.\nOwner: atciic100_apbslv in rtl/atciic100_apbslv.v via module_equivalence.",
      "evidence_terms": [],
      "id": "RTL-0218",
      "owner_file": "rtl/atciic100_apbslv.v",
      "owner_module": "atciic100_apbslv",
      "priority": "high",
      "required": true,
      "source_ref": "sub_modules.atciic100_apbslv.module_equivalence",
      "ssot_context": {},
      "ssot_refs": [
        "sub_modules.atciic100_apbslv.module_equivalence"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 7,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/atciic100_apbslv.v.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "io_list.port",
      "content": "Implement and connect port pclk",
      "criteria": [
        "RTL declaration matches SSOT direction and width",
        "Active input controls are consumed by behavior or explicitly justified",
        "Active outputs are driven by implemented logic, not placeholder constants",
        "Traceability keeps source_ref io_list.clock_domains.pclk.ports.pclk",
        "Primary implementation evidence is in rtl/atciic100_apbslv.v",
        "pclk width matches SSOT value 1",
        "pclk port direction remains input"
      ],
      "detail": "The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.\nSSOT ref: io_list.clock_domains.pclk.ports.pclk.\nOwner: atciic100_apbslv in rtl/atciic100_apbslv.v via io_list.\nSSOT item context: name=pclk; width=1; direction=input.",
      "evidence_terms": [],
      "id": "RTL-0038",
      "owner_file": "rtl/atciic100_apbslv.v",
      "owner_module": "atciic100_apbslv",
      "priority": "normal",
      "required": true,
      "source_ref": "io_list.clock_domains.pclk.ports.pclk",
      "ssot_context": {
        "direction": "input",
        "name": "pclk",
        "width": "1"
      },
      "ssot_refs": [
        "io_list.clock_domains.pclk.ports.pclk"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 7,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/atciic100_apbslv.v.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "io_list.port",
      "content": "Implement and connect port presetn",
      "criteria": [
        "RTL declaration matches SSOT direction and width",
        "Active input controls are consumed by behavior or explicitly justified",
        "Active outputs are driven by implemented logic, not placeholder constants",
        "Traceability keeps source_ref io_list.resets.presetn.ports.presetn",
        "Primary implementation evidence is in rtl/atciic100_apbslv.v",
        "presetn width matches SSOT value 1",
        "presetn port direction remains input"
      ],
      "detail": "The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.\nSSOT ref: io_list.resets.presetn.ports.presetn.\nOwner: atciic100_apbslv in rtl/atciic100_apbslv.v via io_list.\nSSOT item context: name=presetn; width=1; direction=input.",
      "evidence_terms": [],
      "id": "RTL-0039",
      "owner_file": "rtl/atciic100_apbslv.v",
      "owner_module": "atciic100_apbslv",
      "priority": "normal",
      "required": true,
      "source_ref": "io_list.resets.presetn.ports.presetn",
      "ssot_context": {
        "direction": "input",
        "name": "presetn",
        "width": "1"
      },
      "ssot_refs": [
        "io_list.resets.presetn.ports.presetn"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 7,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/atciic100_apbslv.v.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "io_list.port",
      "content": "Implement and connect port psel",
      "criteria": [
        "RTL declaration matches SSOT direction and width",
        "Active input controls are consumed by behavior or explicitly justified",
        "Active outputs are driven by implemented logic, not placeholder constants",
        "Traceability keeps source_ref io_list.interfaces.apb_slave.ports.psel",
        "Primary implementation evidence is in rtl/atciic100_apbslv.v",
        "psel width matches SSOT value 1",
        "psel port direction remains input"
      ],
      "detail": "The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.\nSSOT ref: io_list.interfaces.apb_slave.ports.psel.\nOwner: atciic100_apbslv in rtl/atciic100_apbslv.v via io_list.\nSSOT item context: name=psel; width=1; direction=input.",
      "evidence_terms": [],
      "id": "RTL-0040",
      "owner_file": "rtl/atciic100_apbslv.v",
      "owner_module": "atciic100_apbslv",
      "priority": "normal",
      "required": true,
      "source_ref": "io_list.interfaces.apb_slave.ports.psel",
      "ssot_context": {
        "direction": "input",
        "name": "psel",
        "width": "1"
      },
      "ssot_refs": [
        "io_list.interfaces.apb_slave.ports.psel"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 7,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/atciic100_apbslv.v.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "io_list.port",
      "content": "Implement and connect port penable",
      "criteria": [
        "RTL declaration matches SSOT direction and width",
        "Active input controls are consumed by behavior or explicitly justified",
        "Active outputs are driven by implemented logic, not placeholder constants",
        "Traceability keeps source_ref io_list.interfaces.apb_slave.ports.penable",
        "Primary implementation evidence is in rtl/atciic100_apbslv.v",
        "penable width matches SSOT value 1",
        "penable port direction remains input"
      ],
      "detail": "The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.\nSSOT ref: io_list.interfaces.apb_slave.ports.penable.\nOwner: atciic100_apbslv in rtl/atciic100_apbslv.v via io_list.\nSSOT item context: name=penable; width=1; direction=input.",
      "evidence_terms": [],
      "id": "RTL-0041",
      "owner_file": "rtl/atciic100_apbslv.v",
      "owner_module": "atciic100_apbslv",
      "priority": "normal",
      "required": true,
      "source_ref": "io_list.interfaces.apb_slave.ports.penable",
      "ssot_context": {
        "direction": "input",
        "name": "penable",
        "width": "1"
      },
      "ssot_refs": [
        "io_list.interfaces.apb_slave.ports.penable"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 7,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/atciic100_apbslv.v.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "io_list.port",
      "content": "Implement and connect port pwrite",
      "criteria": [
        "RTL declaration matches SSOT direction and width",
        "Active input controls are consumed by behavior or explicitly justified",
        "Active outputs are driven by implemented logic, not placeholder constants",
        "Traceability keeps source_ref io_list.interfaces.apb_slave.ports.pwrite",
        "Primary implementation evidence is in rtl/atciic100_apbslv.v",
        "pwrite width matches SSOT value 1",
        "pwrite port direction remains input"
      ],
      "detail": "The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.\nSSOT ref: io_list.interfaces.apb_slave.ports.pwrite.\nOwner: atciic100_apbslv in rtl/atciic100_apbslv.v via io_list.\nSSOT item context: name=pwrite; width=1; direction=input.",
      "evidence_terms": [],
      "id": "RTL-0042",
      "owner_file": "rtl/atciic100_apbslv.v",
      "owner_module": "atciic100_apbslv",
      "priority": "normal",
      "required": true,
      "source_ref": "io_list.interfaces.apb_slave.ports.pwrite",
      "ssot_context": {
        "direction": "input",
        "name": "pwrite",
        "width": "1"
      },
      "ssot_refs": [
        "io_list.interfaces.apb_slave.ports.pwrite"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 7,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/atciic100_apbslv.v.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "io_list.port",
      "content": "Implement and connect port paddr",
      "criteria": [
        "RTL declaration matches SSOT direction and width",
        "Active input controls are consumed by behavior or explicitly justified",
        "Active outputs are driven by implemented logic, not placeholder constants",
        "Traceability keeps source_ref io_list.interfaces.apb_slave.ports.paddr",
        "Primary implementation evidence is in rtl/atciic100_apbslv.v",
        "paddr width matches SSOT value 4",
        "paddr port direction remains input"
      ],
      "detail": "The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.\nSSOT ref: io_list.interfaces.apb_slave.ports.paddr.\nOwner: atciic100_apbslv in rtl/atciic100_apbslv.v via io_list.\nSSOT item context: name=paddr; width=4; direction=input.",
      "evidence_terms": [],
      "id": "RTL-0043",
      "owner_file": "rtl/atciic100_apbslv.v",
      "owner_module": "atciic100_apbslv",
      "priority": "normal",
      "required": true,
      "source_ref": "io_list.interfaces.apb_slave.ports.paddr",
      "ssot_context": {
        "direction": "input",
        "name": "paddr",
        "width": "4"
      },
      "ssot_refs": [
        "io_list.interfaces.apb_slave.ports.paddr"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 7,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/atciic100_apbslv.v.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "io_list.port",
      "content": "Implement and connect port pwdata",
      "criteria": [
        "RTL declaration matches SSOT direction and width",
        "Active input controls are consumed by behavior or explicitly justified",
        "Active outputs are driven by implemented logic, not placeholder constants",
        "Traceability keeps source_ref io_list.interfaces.apb_slave.ports.pwdata",
        "Primary implementation evidence is in rtl/atciic100_apbslv.v",
        "pwdata width matches SSOT value 32",
        "pwdata port direction remains input"
      ],
      "detail": "The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.\nSSOT ref: io_list.interfaces.apb_slave.ports.pwdata.\nOwner: atciic100_apbslv in rtl/atciic100_apbslv.v via io_list.\nSSOT item context: name=pwdata; width=32; direction=input.",
      "evidence_terms": [],
      "id": "RTL-0044",
      "owner_file": "rtl/atciic100_apbslv.v",
      "owner_module": "atciic100_apbslv",
      "priority": "normal",
      "required": true,
      "source_ref": "io_list.interfaces.apb_slave.ports.pwdata",
      "ssot_context": {
        "direction": "input",
        "name": "pwdata",
        "width": "32"
      },
      "ssot_refs": [
        "io_list.interfaces.apb_slave.ports.pwdata"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 7,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/atciic100_apbslv.v.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "io_list.port",
      "content": "Implement and connect port prdata",
      "criteria": [
        "RTL declaration matches SSOT direction and width",
        "Active input controls are consumed by behavior or explicitly justified",
        "Active outputs are driven by implemented logic, not placeholder constants",
        "Traceability keeps source_ref io_list.interfaces.apb_slave.ports.prdata",
        "Primary implementation evidence is in rtl/atciic100_apbslv.v",
        "prdata width matches SSOT value 32",
        "prdata port direction remains output"
      ],
      "detail": "The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.\nSSOT ref: io_list.interfaces.apb_slave.ports.prdata.\nOwner: atciic100_apbslv in rtl/atciic100_apbslv.v via io_list.\nSSOT item context: name=prdata; width=32; direction=output.",
      "evidence_terms": [],
      "id": "RTL-0045",
      "owner_file": "rtl/atciic100_apbslv.v",
      "owner_module": "atciic100_apbslv",
      "priority": "normal",
      "required": true,
      "source_ref": "io_list.interfaces.apb_slave.ports.prdata",
      "ssot_context": {
        "direction": "output",
        "name": "prdata",
        "width": "32"
      },
      "ssot_refs": [
        "io_list.interfaces.apb_slave.ports.prdata"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 7,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/atciic100_apbslv.v.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "io_list.port",
      "content": "Implement and connect port scl_i",
      "criteria": [
        "RTL declaration matches SSOT direction and width",
        "Active input controls are consumed by behavior or explicitly justified",
        "Active outputs are driven by implemented logic, not placeholder constants",
        "Traceability keeps source_ref io_list.interfaces.i2c_bus.ports.scl_i",
        "Primary implementation evidence is in rtl/atciic100_apbslv.v",
        "scl_i width matches SSOT value 1",
        "scl_i port direction remains input"
      ],
      "detail": "The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.\nSSOT ref: io_list.interfaces.i2c_bus.ports.scl_i.\nOwner: atciic100_apbslv in rtl/atciic100_apbslv.v via io_list.\nSSOT item context: name=scl_i; width=1; direction=input.",
      "evidence_terms": [],
      "id": "RTL-0046",
      "owner_file": "rtl/atciic100_apbslv.v",
      "owner_module": "atciic100_apbslv",
      "priority": "normal",
      "required": true,
      "source_ref": "io_list.interfaces.i2c_bus.ports.scl_i",
      "ssot_context": {
        "direction": "input",
        "name": "scl_i",
        "width": "1"
      },
      "ssot_refs": [
        "io_list.interfaces.i2c_bus.ports.scl_i"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 7,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/atciic100_apbslv.v.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "io_list.port",
      "content": "Implement and connect port sda_i",
      "criteria": [
        "RTL declaration matches SSOT direction and width",
        "Active input controls are consumed by behavior or explicitly justified",
        "Active outputs are driven by implemented logic, not placeholder constants",
        "Traceability keeps source_ref io_list.interfaces.i2c_bus.ports.sda_i",
        "Primary implementation evidence is in rtl/atciic100_apbslv.v",
        "sda_i width matches SSOT value 1",
        "sda_i port direction remains input"
      ],
      "detail": "The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.\nSSOT ref: io_list.interfaces.i2c_bus.ports.sda_i.\nOwner: atciic100_apbslv in rtl/atciic100_apbslv.v via io_list.\nSSOT item context: name=sda_i; width=1; direction=input.",
      "evidence_terms": [],
      "id": "RTL-0047",
      "owner_file": "rtl/atciic100_apbslv.v",
      "owner_module": "atciic100_apbslv",
      "priority": "normal",
      "required": true,
      "source_ref": "io_list.interfaces.i2c_bus.ports.sda_i",
      "ssot_context": {
        "direction": "input",
        "name": "sda_i",
        "width": "1"
      },
      "ssot_refs": [
        "io_list.interfaces.i2c_bus.ports.sda_i"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 7,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/atciic100_apbslv.v.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "io_list.port",
      "content": "Implement and connect port scl_o",
      "criteria": [
        "RTL declaration matches SSOT direction and width",
        "Active input controls are consumed by behavior or explicitly justified",
        "Active outputs are driven by implemented logic, not placeholder constants",
        "Traceability keeps source_ref io_list.interfaces.i2c_bus.ports.scl_o",
        "Primary implementation evidence is in rtl/atciic100_apbslv.v",
        "scl_o width matches SSOT value 1",
        "scl_o port direction remains output"
      ],
      "detail": "The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.\nSSOT ref: io_list.interfaces.i2c_bus.ports.scl_o.\nOwner: atciic100_apbslv in rtl/atciic100_apbslv.v via io_list.\nSSOT item context: name=scl_o; width=1; direction=output.",
      "evidence_terms": [],
      "id": "RTL-0048",
      "owner_file": "rtl/atciic100_apbslv.v",
      "owner_module": "atciic100_apbslv",
      "priority"
... <truncated 8674 chars>

Current packet Markdown (rtl/authoring_packets/module__atciic100_apbslv.md):
# RTL Authoring Packet: module__atciic100_apbslv

- Kind: module
- Owner module: atciic100_apbslv
- Owner file: rtl/atciic100_apbslv.v
- Task count: 27
- Required tasks: 27

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
- Record generated RTL files and todo_plan_sha256 in rtl_authoring_provenance.json.

## Context

- Quality profile: production
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 27
- Human-locked open tasks: 0
- Owner refs: io_list, io_list.interfaces.apb_slave, registers, registers.register_list
- SSOT connection contracts:
  - atciic100_apbslv.cmd_reg <= cmd (sub_modules[1].connections[0])
  - atciic100_apbslv.data_in <= pwdata (sub_modules[2].connections[0])

## Tasks

### RTL-0027: Implement APB Slave Logic

- Priority: high
- Required: True
- Status: open
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[0]
- Detail: Decode paddr[5:2] to specific registers. Implement read data mux and write decode.
SSOT ref: workflow_todos.rtl-gen[0].
Owner: atciic100_apbslv in rtl/atciic100_apbslv.v via workflow_todos.owner.
SSOT item context: id=RTL_TODO_APB.
- Current reason: Owner RTL file is missing: rtl/atciic100_apbslv.v.
- Criteria:
  - APB R/W functional
  - All register fields readable/writable per spec
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[0]
  - Primary implementation evidence is in rtl/atciic100_apbslv.v
  - Semantic source_refs covered: registers
- SSOT refs: registers, workflow_todos.rtl-gen[0]

### RTL-0173: Implement CSR/register ID

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.ID
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.ID.
Owner: atciic100_apbslv in rtl/atciic100_apbslv.v via registers.
SSOT item context: name=ID; width=32; reset=514; access=ro; offset=0.
- Current reason: Owner RTL file is missing: rtl/atciic100_apbslv.v.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.ID
  - Primary implementation evidence is in rtl/atciic100_apbslv.v
  - ID width matches SSOT value 32
  - ID reset behavior matches SSOT value 514
  - ID access policy ro is implemented without read/write shortcuts
  - ID decode uses SSOT address/offset 0
- SSOT refs: registers.register_list.ID

### RTL-0174: Implement CSR/register REV

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.REV
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.REV.
Owner: atciic100_apbslv in rtl/atciic100_apbslv.v via registers.
SSOT item context: name=REV; width=32; reset=4098; access=ro; offset=4.
- Current reason: Owner RTL file is missing: rtl/atciic100_apbslv.v.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.REV
  - Primary implementation evidence is in rtl/atciic100_apbslv.v
  - REV width matches SSOT value 32
  - REV reset behavior matches SSOT value 4098
  - REV access policy ro is implemented without read/write shortcuts
  - REV decode uses SSOT address/offset 4
- SSOT refs: registers.register_list.REV

### RTL-0175: Implement CSR/register CFG

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.CFG
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CFG.
Owner: atciic100_apbslv in rtl/atciic100_apbslv.v via registers.
SSOT item context: name=CFG; width=32; reset=0; access=ro; offset=8.
- Current reason: Owner RTL file is missing: rtl/atciic100_apbslv.v.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CFG
  - Primary implementation evidence is in rtl/atciic100_apbslv.v
  - CFG width matches SSOT value 32
  - CFG reset behavior matches SSOT value 0
  - CFG access policy ro is implemented without read/write shortcuts
  - CFG decode uses SSOT address/offset 8
- SSOT refs: registers.register_list.CFG

### RTL-0176: Implement CSR/register INT_EN

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.INT_EN
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.INT_EN.
Owner: atciic100_apbslv in rtl/atciic100_apbslv.v via registers.
SSOT item context: name=INT_EN; width=32; reset=0; access=rw; offset=12.
- Current reason: Owner RTL file is missing: rtl/atciic100_apbslv.v.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.INT_EN
  - Primary implementation evidence is in rtl/atciic100_apbslv.v
  - INT_EN width matches SSOT value 32
  - INT_EN reset behavior matches SSOT value 0
  - INT_EN access policy rw is implemented without read/write shortcuts
  - INT_EN decode uses SSOT address/offset 12
- SSOT refs: registers.register_list.INT_EN

### RTL-0177: Implement CSR/register INT_ST

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.INT_ST
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.INT_ST.
Owner: atciic100_apbslv in rtl/atciic100_apbslv.v via registers.
SSOT item context: name=INT_ST; width=32; reset=1; access=rw1c; offset=16.
- Current reason: Owner RTL file is missing: rtl/atciic100_apbslv.v.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.INT_ST
  - Primary implementation evidence is in rtl/atciic100_apbslv.v
  - INT_ST width matches SSOT value 32
  - INT_ST reset behavior matches SSOT value 1
  - INT_ST access policy rw1c is implemented without read/write shortcuts
  - INT_ST decode uses SSOT address/offset 16
- SSOT refs: registers.register_list.INT_ST

### RTL-0178: Implement CSR/register ADDR

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.ADDR
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.ADDR.
Owner: atciic100_apbslv in rtl/atciic100_apbslv.v via registers.
SSOT item context: name=ADDR; width=32; reset=0; access=rw; offset=20.
- Current reason: Owner RTL file is missing: rtl/atciic100_apbslv.v.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.ADDR
  - Primary implementation evidence is in rtl/atciic100_apbslv.v
  - ADDR width matches SSOT value 32
  - ADDR reset behavior matches SSOT value 0
  - ADDR access policy rw is implemented without read/write shortcuts
  - ADDR decode uses SSOT address/offset 20
- SSOT refs: registers.register_list.ADDR

### RTL-0179: Implement CSR/register DATA

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.DATA
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.DATA.
Owner: atciic100_apbslv in rtl/atciic100_apbslv.v via registers.
SSOT item context: name=DATA; width=32; reset=0; access=rw; offset=24.
- Current reason: Owner RTL file is missing: rtl/atciic100_apbslv.v.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.DATA
  - Primary implementation evidence is in rtl/atciic100_apbslv.v
  - DATA width matches SSOT value 32
  - DATA reset behavior matches SSOT value 0
  - DATA access policy rw is implemented without read/write shortcuts
  - DATA decode uses SSOT address/offset 24
- SSOT refs: registers.register_list.DATA

### RTL-0180: Implement CSR/register CMD

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.CMD
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CMD.
Owner: atciic100_apbslv in rtl/atciic100_apbslv.v via registers.
SSOT item context: name=CMD; width=32; reset=0; access=rw; offset=28.
- Current reason: Owner RTL file is missing: rtl/atciic100_apbslv.v.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CMD
  - Primary implementation evidence is in rtl/atciic100_apbslv.v
  - CMD width matches SSOT value 32
  - CMD reset behavior matches SSOT value 0
  - CMD access policy rw is implemented without read/write shortcuts
  - CMD decode uses SSOT address/offset 28
- SSOT refs: registers.register_list.CMD

### RTL-0181: Implement CSR/register CTRL

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.CTRL
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CTRL.
Owner: atciic100_apbslv in rtl/atciic100_apbslv.v via registers.
SSOT item context: name=CTRL; width=32; reset=7936; access=rw; offset=32.
- Current reason: Owner RTL file is missing: rtl/atciic100_apbslv.v.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CTRL
  - Primary implementation evidence is in rtl/atciic100_apbslv.v
  - CTRL width matches SSOT value 32
  - CTRL reset behavior matches SSOT value 7936
  - CTRL access policy rw is implemented without read/write shortcuts
  - CTRL decode uses SSOT address/offset 32
- SSOT refs: registers.register_list.CTRL

### RTL-0182: Implement CSR/register SETUP

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.SETUP
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.SETUP.
Owner: atciic100_apbslv in rtl/atciic100_apbslv.v via registers.
SSOT item context: name=SETUP; width=32; reset=0; access=rw; offset=36.
- Current reason: Owner RTL file is missing: rtl/atciic100_apbslv.v.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.SETUP
  - Primary implementation evidence is in rtl/atciic100_apbslv.v
  - SETUP width matches SSOT value 32
  - SETUP reset behavior matches SSOT value 0
  - SETUP access policy rw is implemented without read/write shortcuts
  - SETUP decode uses SSOT address/offset 36
- SSOT refs: registers.register_list.SETUP

### RTL-0218: Prove module atciic100_apbslv is functionally equivalent to FL

- Priority: high
- Required: True
- Status: open
- Category: equivalence.module
- Source ref: sub_modules.atciic100_apbslv.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.atciic100_apbslv.module_equivalence.
Owner: atciic100_apbslv in rtl/atciic100_apbslv.v via module_equivalence.
- Current reason: Owner RTL file is missing: rtl/atciic100_apbslv.v.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.atciic100_apbslv.module_equivalence
  - Primary implementation evidence is in rtl/atciic100_apbslv.v
- SSOT refs: sub_modules.atciic100_apbslv.module_equivalence

### RTL-0038: Implement and connect port pclk

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.clock_domains.pclk.ports.pclk
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.clock_domains.pclk.ports.pclk.
Owner: atciic100_apbslv in rtl/atciic100_apbslv.v via io_list.
SSOT item context: name=pclk; width=1; direction=input.
- Current reason: Owner RTL file is missing: rtl/atciic100_apbslv.v.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.clock_domains.pclk.ports.pclk
  - Primary implementation evidence is in rtl/atciic100_apbslv.v
  - pclk width matches SSOT value 1
  - pclk port direction remains input
- SSOT refs: io_list.clock_domains.pclk.ports.pclk

### RTL-0039: Implement and connect port presetn

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.resets.presetn.ports.presetn
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.resets.presetn.ports.presetn.
Owner: atciic100_apbslv in rtl/atciic100_apbslv.v via io_list.
SSOT item context: name=presetn; width=1; direction=input.
- Current reason: Owner RTL file is missing: rtl/atciic100_apbslv.v.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceabili
... <truncated 13836 chars>