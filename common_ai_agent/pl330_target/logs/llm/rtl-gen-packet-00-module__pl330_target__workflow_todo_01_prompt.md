RTL-GEN PACKET MODE for pl330_target. Packet attempt 0.

Return exactly one JSON object and nothing else. Do not wrap it in markdown.
Success schema:
{
  "files": [
    {"path": "pl330_target/rtl/<module>.sv", "kind": "rtl", "content": "<SystemVerilog>"},
    {"path": "pl330_target/rtl/rtl_contract.json", "kind": "rtl_contract", "content": "<optional JSON>"},
    {"path": "pl330_target/rtl/rtl_authoring_notes/<packet>.md", "kind": "rtl_notes", "content": "<optional notes>"}
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
- For rtl_gate_closure, repair only LLM-actionable evidence gaps revealed by compile/lint/audit output; do not claim PASS.
- The headless runner will refresh filelist/provenance from LLM-authored artifacts after each packet.

Current packet: module__pl330_target__workflow_todo_01
kind: module
work queue: 1/1 active packets (8 closed packets skipped from 30 total)
batch limit: 1; deferred active packets after this batch: 21
owner_module: pl330_target
owner_file: rtl/pl330_target.sv

Base rtl-gen contract:
Prepare rtl-gen for pl330_target using only pl330_target/yaml/pl330_target.ssot.yaml and pl330_target/rtl/rtl_todo_plan.json, pl330_target/rtl/rtl_authoring_plan.json, and packets under pl330_target/rtl/authoring_packets. The script derives the TODO ledger from SSOT; the LLM must generate real RTL-owned artifacts that satisfy every TODO content/detail/criteria item and record provenance. Process one authoring packet at a time, module packets first, then unowned tasks if present, then rtl_gate_closure. Respect rtl_authoring_plan.execution_policy and each packet execution_policy: draft RTL may be authored while deferred_human_qa_allowed is true, but rtl-gen PASS/signoff is forbidden when pass_allowed is false. On repair attempts, use packet status_counts, open_required_count, Status, and Current reason fields to patch only the RTL-owned artifacts needed to close open TODOs. Use todo_plan_sha256=67f1ff9bf1c0231e8ac6b228f14bf8866bb926d7596a6c36deeabfbcb3a528fc. Repair only RTL-owned artifacts when validators fail. Do not change SSOT semantics, do not use fixed IP templates, and keep prompts focused on DUT-only compile/lint and FL-vs-RTL evidence. Production-profile RTL must also satisfy the SSOT-scaled rtl_implementation_depth_evidence gate; do not emit shallow shell modules that only name ports, instantiate children, or tie off outputs. If rtl_reference_profile is present, treat it as calibration-only scale evidence, never as source RTL or a clone template. If a missing locked-truth artifact, human authority approval, or SSOT connection contract prevents correct RTL authoring, return a human_gate JSON object instead of inventing semantics.

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
        "gate_kind": "common_ai_agent_authoring",
        "owner_module": "pl330_target",
        "reason": "RTL authoring provenance is incomplete: rtl_files_missing_manifest:rtl/pl330_target_apb_regs.sv,rtl/pl330_target_axi.sv,rtl/pl330_target_engine.sv,rtl/pl330_target_icache.sv,rtl/pl330_target_lsq.sv,rtl/pl330_target_merge_buffer.sv",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.common_ai_agent_authoring",
        "status": "open",
        "task_id": "RTL-0006"
      },
      {
        "gate_kind": "static_rtl_evidence",
        "owner_module": "pl330_target",
        "reason": "79 static-evidence-required task(s) still lack DUT RTL evidence.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.static_rtl_evidence",
        "status": "open",
        "task_id": "RTL-0007"
      },
      {
        "gate_kind": "owner_logic_structure_evidence",
        "owner_module": "pl330_target",
        "reason": "9 owner logic structure issue(s) remain. pl330_target_engine: Behavior-owner module is not declared in its owner file; pl330_target_pipeline: Behavior-owner module is not declared in its owner file; pl330_target_lsq: Behavior-owner module is not declared in its owner file",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.owner_logic_structure_evidence",
        "status": "open",
        "task_id": "RTL-0008"
      },
      {
        "gate_kind": "manifest_hierarchy_integration",
        "owner_module": "pl330_target",
        "reason": "9 manifest hierarchy integration issue(s) remain. pl330_target_engine: SSOT manifest child module is not declared in listed RTL sources; pl330_target_pipeline: SSOT manifest child module is not declared in listed RTL sources; pl330_target_lsq: SSOT manifest child module is not declared in listed RTL sources",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.manifest_hierarchy_integration",
        "status": "open",
        "task_id": "RTL-0013"
      },
      {
        "gate_kind": "manifest_signal_flow_evidence",
        "owner_module": "pl330_target",
        "reason": "1 manifest signal-flow issue(s) remain. pl330_target: None: No reachable manifest child port flow evidence was found",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.manifest_signal_flow_evidence",
        "status": "open",
        "task_id": "RTL-0015"
      },
      {
        "gate_kind": "dut_compile",
        "owner_module": "pl330_target",
        "reason": "Missing canonical DUT compile artifact: rtl/rtl_compile.json.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.dut_compile",
        "status": "open",
        "task_id": "RTL-0017"
      },
      {
        "gate_kind": "dut_lint",
        "owner_module": "pl330_target",
        "reason": "Missing canonical DUT lint artifact: lint/dut_lint.json.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.dut_lint",
        "status": "open",
        "task_id": "RTL-0018"
      },
      {
        "gate_kind": "dynamic_todo_closure",
        "owner_module": "pl330_target",
        "reason": "200 required non-closure TODO(s) remain open.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.dynamic_todo_closure",
        "status": "open",
        "task_id": "RTL-0019"
      },
      {
        "gate_kind": "rtl_implementation_depth_evidence",
        "owner_module": "pl330_target",
        "reason": "2 production RTL implementation-depth issue(s) remain. Too few RTL modules contain implementation structure for the SSOT behavior complexity: actual=1 required=9; Too few SSOT behavior-owner modules contain implementation-depth evidence: actual=0 required=9",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.rtl_implementation_depth_evidence",
        "status": "open",
        "task_id": "RTL-0022"
      }
    ],
    "blocked_by_locked_truth": [
      {
        "gate_kind": "manifest_connection_contract_evidence",
        "reason": "Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.",
        "source": "ssot_connection_contracts",
        "status": "missing"
      },
      {
        "gate_kind": "manifest_connection_contract_evidence",
        "owner_module": "pl330_target",
        "reason": "1 SSOT connection contract issue(s) remain. connection: Production-profile multi-module RTL has no machine-readable SSOT connection contracts",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.manifest_connection_contract_evidence",
        "status": "open",
        "task_id": "RTL-0016"
      },
      {
        "gate_kind": "golden_authority_artifacts",
        "owner_module": "pl330_target",
        "reason": "Human authority gate(s) required before production RTL-GEN are not approved: G1=pending",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.golden_authority_artifacts",
        "status": "open",
        "task_id": "RTL-0020"
      },
      {
        "gate_kind": "target_scale_policy",
        "owner_module": "pl330_target",
        "reason": "Reference profile provides suggested_ssot_target_scale, but SSOT target_scale is not locked and no approved waiver is present.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.target_scale",
        "status": "open",
        "task_id": "RTL-0021"
      },
      {
        "gate_kind": "protocol_assertion_evidence",
        "owner_module": "pl330_target",
        "reason": "Missing protocol assertion simulation evidence: sim/assertion_failures.jsonl.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.protocol_assertion_evidence",
        "status": "open",
        "task_id": "RTL-0024"
      },
      {
        "gate_kind": "fl_rtl_goal_audit",
        "owner_module": "pl330_target",
        "reason": "Missing FL-vs-RTL goal audit artifact: sim/fl_rtl_goal_audit.json.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.fl_rtl_goal_audit",
        "status": "open",
        "task_id": "RTL-0025"
      },
      {
        "gate_kind": "coverage_closure",
        "owner_module": "pl330_target",
        "reason": "Missing coverage closure artifact: cov/coverage.json.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.coverage_closure",
        "status": "open",
        "task_id": "RTL-0026"
      }
    ],
    "connection_contract_gap": {
      "machine_readable_contract_count": 0,
      "reason": "Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.",
      "required_for_profile": true,
      "status": "missing"
    },
    "deferred_human_qa_allowed": true,
    "draft_allowed": true,
    "gate_status": "fail",
    "hard_blockers": [],
    "open_required_todos": 201,
    "pass_allowed": false,
    "pass_rule": "rtl-gen may claim PASS only when every required TODO and every locked-truth gate has pass status.",
    "stop_conditions": [
      "Do not edit SSOT/FL/coverage/interface/performance authority artifacts without human approval.",
      "Do not claim rtl-gen PASS while pass_allowed is false.",
      "Do not sign off top integration while required connection contracts are missing."
    ]
  },
  "ip": "pl330_target",
  "packets": [
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__pl330_target__rtl_flow.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "packet_id": "module__pl330_target__rtl_flow",
      "required_count": 2,
      "status_counts": {
        "pass": 2
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__pl330_target__io_list.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "packet_id": "module__pl330_target__io_list",
      "required_count": 9,
      "status_counts": {
        "pass": 9
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__pl330_target__parameters.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "packet_id": "module__pl330_target__parameters",
      "required_count": 3,
      "status_counts": {
        "pass": 3
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__pl330_target__integration.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "packet_id": "module__pl330_target__integration",
      "required_count": 3,
      "status_counts": {
        "pass": 3
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__pl330_target__interrupts.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "packet_id": "module__pl330_target__interrupts",
      "required_count": 2,
      "status_counts": {
        "pass": 2
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__pl330_target__security.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "packet_id": "module__pl330_target__security",
      "required_count": 4,
      "status_counts": {
        "pass": 4
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__pl330_target__synthesis.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "packet_id": "module__pl330_target__synthesis",
      "required_count": 7,
      "status_counts": {
        "pass": 7
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__pl330_target__workflow_todo_01.json",
      "kind": "module",
      "llm_actionable_open_count": 2,
      "open_required_count": 2,
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "packet_id": "module__pl330_target__workflow_todo_01",
      "required_count": 48,
      "status_counts": {
        "open": 2,
        "pass": 46
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__pl330_target__workflow_todo_02.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "packet_id": "module__pl330_target__workflow_todo_02",
      "required_count": 1,
      "status_counts": {
        "pass": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__pl330_target_apb_regs.json",
      "kind": "module",
      "llm_actionable_open_count": 4,
      "open_required_count": 4,
      "owner_file": "rtl/pl330_target_apb_regs.sv",
      "owner_module": "pl330_target_apb_regs",
      "packet_id": "module__pl330_target_apb_regs",
      "required_count": 4,
      "status_counts": {
        "open": 4
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__pl330_target_axi.json",
      "kind": "module",
      "llm_actionable_open_count": 5,
      "open_required_count": 5,
      "owner_file": "rtl/pl330_target_axi.sv",
      "owner_module": "pl330_target_axi",
      "packet_id": "module__pl330_target_axi",
      "required_count": 5,
      "status_counts": {
        "open": 5
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__pl330_target_engine.json",
      "kind": "module",
      "llm_actionable_open_count": 8,
      "open_required_count": 8,
      "owner_file": "rtl/pl330_target_engine.sv",
      "owner_module": "pl330_target_engine",
      "packet_id": "module__pl330_target_engine",
      "required_count": 8,
      "status_counts": {
        "open": 8
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__pl330_target_icache.json",
      "kind": "module",
      "llm_actionable_open_count": 4,
      "open_required_count": 4,
      "owner_file": "rtl/pl330_target_icache.sv",
      "owner_module": "pl330_target_icache",
      "packet_id": "module__pl330_target_icache",
      "required_count": 4,
      "status_counts": {
        "open": 4
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__pl330_target_lsq.json",
      "kind": "module",
      "llm_actionable_open_count": 2,
      "open_required_count": 2,
      "owner_file": "rtl/pl330_target_lsq.sv",
      "owner_module": "pl330_target_lsq",
      "packet_id": "module__pl330_target_lsq",
      "required_count": 2,
      "status_counts": {
        "open": 2
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__pl330_target_merge_buffer.json",
      "kind": "module",
      "llm_actionable_open_count": 4,
      "open_required_count": 4,
      "owner_file": "rtl/pl330_target_merge_buffer.sv",
      "owner_module": "pl330_target_merge_buffer",
      "packet_id": "module__pl330_target_merge_buffer",
      "required_count": 4,
      "status_counts": {
        "open": 4
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__pl330_target_mfifo__parameters.json",
      "kind": "module",
      "llm_actionable_open_count": 1,
      "open_required_count": 1,
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "packet_id": "module__pl330_target_mfifo__parameters",
      "required_count": 1,
      "status_counts": {
        "open": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__pl330_target_mfifo__function_model_01.json",
      "kind": "module",
      "llm_actionable_open_count": 48,
      "open_required_count": 48,
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "packet_id": "module__pl330_target_mfifo__function_model_01",
      "required_count": 48,
      "status_counts": {
        "open": 48
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__pl330_target_mfifo__function_model_02.json",
      "kind": "module",
      "llm_actionable_open_count": 15,
      "open_required_count": 15,
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "packet_id": "module__pl330_target_mfifo__function_model_02",
      "required_count": 15,
      "status_counts": {
        "open": 15
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__pl330_target_mfifo__fsm.json",
      "kind": "module",
      "llm_actionable_open_count": 24,
      "open_required_count": 24,
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "packet_id": "module__pl330_target_mfifo__fsm",
      "required_count": 24,
      "status_counts": {
        "open": 24
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__pl330_target_mfifo__registers.json",
      "kind": "module",
      "llm_actionable_open_count": 19,
      "open_required_count": 19,
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "packet_id": "module__pl330_target_mfifo__registers",
      "required_count": 19,
      "status_counts": {
        "open": 19
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__pl330_target_mfifo__memory.json",
      "kind": "module",
      "llm_actionable_open_count": 1,
      "open_required_count": 1,
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "packet_id": "module__pl330_target_mfifo__memory",
      "required_count": 1,
      "status_counts": {
        "open": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__pl330_target_mfifo__features.json",
      "kind": "module",
      "llm_actionable_open_count": 7,
      "open_required_count": 7,
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "packet_id": "module__pl330_target_mfifo__features",
      "required_count": 7,
      "status_counts": {
        "open": 7
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__pl330_target_mfifo__test_requirements.json",
      "kind": "module",
      "llm_actionable_open_count": 12,
      "open_required_count": 12,
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "packet_id": "module__pl330_target_mfifo__test_requirements",
      "required_count": 12,
      "status_counts": {
        "open": 12
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__pl330_target_mfifo__coverage.json",
      "kind": "module",
      "llm_actionable_open_count": 6,
      "open_required_count": 6,
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "packet_id": "module__pl330_target_mfifo__coverage",
      "required_count": 6,
      "status_counts": {
        "open": 6
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__pl330_target_mfifo__equivalence.json",
      "kind": "module",
      "llm_actionable_open_count": 1,
      "open_required_count": 1,
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "packet_id": "module__pl330_target_mfifo__equivalence",
      "required_count": 1,
      "status_counts": {
        "open": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__pl330_target_mfifo__workflow_todo.json",
      "kind": "module",
      "llm_actionable_open_count": 6,
      "open_required_count": 6,
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "packet_id": "module__pl330_target_mfifo__workflow_todo",
      "required_count": 6,
      "status_counts": {
        "open": 6
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__pl330_target_periph.json",
      "kind": "module",
      "llm_actionable_open_count": 3,
      "open_required_count": 3,
      "owner_file": "rtl/pl330_target_periph.sv",
      "owner_module": "pl330_target_periph",
      "packet_id": "module__pl330_target_periph",
      "required_count": 3,
      "status_counts": {
        "open": 3
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__pl330_target_pipeline.json",
      "kind": "module",
      "llm_actionable_open_count": 13,
      "open_required_count": 13,
      "owner_file": "rtl/pl330_target_pipeline.sv",
      "owner_module": "pl330_target_pipeline",
      "packet_id": "module__pl330_target_pipeline",
      "required_count": 13,
      "status_counts": {
        "open": 13
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/unowned_tasks.json",
      "kind": "unowned",
      "llm_actionable_open_count": 1,
      "open_required_count": 1,
      "owner_file": "",
      "owner_module": "",
      "packet_id": "unowned_tasks",
      "required_count": 1,
      "status_counts": {
        "open": 1
      }
    },
    {
      "human_locked_open_count": 7,
      "json": "rtl/authoring_packets/rtl_gate_closure.json",
      "kind": "gate",
      "llm_actionable_open_count": 9,
      "open_required_count": 15,
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "packet_id": "rtl_gate_closure",
      "required_count": 24,
      "status_counts": {
        "open": 15,
        "pass": 9
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
  "summary": {
    "deferred_human_qa_allowed": true,
    "gate_packets": 1,
    "human_locked_packets": 1,
    "human_locked_tasks": 7,
    "llm_actionable_packets": 22,
    "llm_actionable_tasks": 195,
    "max_packet_required_tasks": 48,
    "module_packets": 28,
    "next_llm_packets": [
      "module__pl330_target__workflow_todo_01",
      "module__pl330_target_apb_regs",
      "module__pl330_target_axi",
      "module__pl330_target_engine",
      "module__pl330_target_icache",
      "module__pl330_target_lsq",
      "module__pl330_target_merge_buffer",
      "module__pl330_target_mfifo__parameters"
    ],
    "packet_task_limit": 48,
    "packets": 30,
    "pass_allowed": false,
    "recommended_packet_batch_limit": 4,
    "reference_profile_present": true,
    "required_tasks": 287,
    "sliced_module_packets": 20,
    "target_scale_present": false,
    "total_tasks": 287,
    "unowned_packets": 1
  },
  "target_scale": {},
  "todo_plan_sha256": "67f1ff9bf1c0231e8ac6b228f14bf8866bb926d7596a6c36deeabfbcb3a528fc",
  "top": "pl330_target",
  "type": "rtl_authoring_plan"
}

Current owner RTL file (rtl/pl330_target.sv):
`default_nettype none

module pl330_target #(
    parameter int DATA_WIDTH  = 32,
    parameter int ADDR_WIDTH  = 32,
    parameter int MFIFO_DEPTH = 16
) (
    input  logic                  aclk,
    input  logic                  aresetn,
    input  logic                  clk,
    input  logic                  rst_n,
    input  logic                  req_valid,
    output logic                  req_ready,
    input  logic [DATA_WIDTH-1:0] req_data,
    output logic                  rsp_valid,
    input  logic                  rsp_ready,
    output logic [DATA_WIDTH-1:0] rsp_data,
    output logic                  error
);

    localparam logic [3:0] RESET_SETTLE_MAX       = 4'hf;
    localparam logic [3:0] SECURITY_OPCODE        = 4'hb;
    localparam logic [3:0] SECURITY_SUB_MANAGER   = 4'h0;
    localparam logic [3:0] SECURITY_SUB_IRQ       = 4'h1;
    localparam logic [3:0] SECURITY_SUB_PERIPH    = 4'h2;
    localparam logic [3:0] SECURITY_SUB_STATUS    = 4'h3;
    localparam logic [7:0] SECURITY_STATUS_TAG    = 8'ha5;
    localparam logic [15:0] SECURITY_BOOT_UNLOCK  = 16'h3305;
    localparam int SECURITY_IRQ_NS_WIDTH          = 16;
    localparam int SECURITY_PERIPH_NS_WIDTH       = 16;

    logic                  aux_reset_released_q;
    logic                  aux_activity_q;
    logic                  aux_reset_sync1_q;
    logic                  aux_reset_sync2_q;
    logic                  aux_activity_sync1_q;
    logic                  aux_activity_sync2_q;
    logic                  link_ready_q;
    logic [3:0]            reset_settle_q;
    logic                  reset_fault_q;
    logic                  protocol_error_q;
    logic                  pending_q;
    logic [DATA_WIDTH-1:0] rsp_data_q;
    logic [DATA_WIDTH-1:0] flow_count_q;

    logic                  boot_manager_ns_q;
    logic [SECURITY_IRQ_NS_WIDTH-1:0] boot_irq_ns_q;
    logic [SECURITY_PERIPH_NS_WIDTH-1:0] boot_periph_ns_q;
    logic                  boot_security_locked_q;
    logic                  security_protocol_error_q;
    logic [DATA_WIDTH-1:0] security_status_w;
    logic [DATA_WIDTH-1:0] security_mix_w;

    wire                   link_ready_w;
    wire                   accept_req_w;
    wire                   consume_rsp_w;
    wire                   reset_settle_done_w;
    wire [DATA_WIDTH-1:0]  flow_increment_w;
    wire [DATA_WIDTH-1:0]  response_mix_w;
    wire                   security_req_w;
    wire                   security_access_w;
    wire                   security_write_w;
    wire                   security_read_w;
    wire                   security_lock_w;
    wire                   security_unlock_ok_w;
    wire                   security_write_allowed_w;
    wire                   non_security_accept_w;
    wire [3:0]             security_subcmd_w;
    wire                   boot_manager_ns_update_w;
    wire [SECURITY_IRQ_NS_WIDTH-1:0] boot_irq_ns_update_w;
    wire [SECURITY_PERIPH_NS_WIDTH-1:0] boot_periph_ns_update_w;

    assign flow_increment_w          = {{(DATA_WIDTH-1){1'b0}}, 1'b1};
    assign link_ready_w              = link_ready_q & (~reset_fault_q);
    assign accept_req_w              = req_valid & req_ready;
    assign consume_rsp_w             = rsp_valid & rsp_ready;
    assign reset_settle_done_w       = (reset_settle_q == RESET_SETTLE_MAX);
    assign response_mix_w            = req_data ^ flow_count_q ^ {DATA_WIDTH{aux_activity_sync2_q}};

    assign security_req_w            = req_valid & (req_data[31:28] == SECURITY_OPCODE);
    assign security_access_w         = accept_req_w & (req_data[31:28] == SECURITY_OPCODE);
    assign security_subcmd_w         = req_data[27:24];
    assign security_write_w          = req_data[23];
    assign security_read_w           = req_data[22];
    assign security_lock_w           = req_data[21];
    assign security_unlock_ok_w      = (req_data[15:0] == SECURITY_BOOT_UNLOCK);
    assign security_write_allowed_w  = security_access_w & security_write_w & security_unlock_ok_w & (~boot_security_locked_q);
    assign non_security_accept_w     = accept_req_w & (~security_req_w);
    assign boot_manager_ns_update_w  = req_data[0];
    assign boot_irq_ns_update_w      = req_data[SECURITY_IRQ_NS_WIDTH-1:0];
    assign boot_periph_ns_update_w   = req_data[SECURITY_PERIPH_NS_WIDTH-1:0];

    assign req_ready = link_ready_w & (~pending_q);
    assign rsp_valid = pending_q;
    assign rsp_data  = rsp_data_q;
    assign error     = reset_fault_q | protocol_error_q | security_protocol_error_q | (req_valid & (~link_ready_w));

    always_comb begin
        security_status_w = {DATA_WIDTH{1'b0}};
        security_status_w[31:24] = SECURITY_STATUS_TAG;
        security_status_w[23]    = boot_security_locked_q;
        security_status_w[22]    = boot_manager_ns_q;
        security_status_w[21]    = security_protocol_error_q;
        security_status_w[20]    = security_unlock_ok_w;
        security_status_w[19:16] = security_subcmd_w;
        security_status_w[15:8]  = boot_irq_ns_q[7:0];
        security_status_w[7:0]   = boot_periph_ns_q[7:0];
    end

    always_comb begin
        security_mix_w = {DATA_WIDTH{1'b0}};
        security_mix_w[0]     = boot_manager_ns_q;
        security_mix_w[16:1]  = boot_irq_ns_q;
        security_mix_w[31:17] = boot_periph_ns_q[14:0];
    end

    always_ff @(posedge aclk or negedge aresetn) begin
        if (!aresetn) begin
            aux_reset_released_q <= 1'b0;
            aux_activity_q       <= 1'b0;
        end else begin
            aux_reset_released_q <= 1'b1;
            aux_activity_q       <= ~aux_activity_q;
        end
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            aux_reset_sync1_q    <= 1'b0;
            aux_reset_sync2_q    <= 1'b0;
            aux_activity_sync1_q <= 1'b0;
            aux_activity_sync2_q <= 1'b0;
        end else begin
            aux_reset_sync1_q    <= aux_reset_released_q;
            aux_reset_sync2_q    <= aux_reset_sync1_q;
            aux_activity_sync1_q <= aux_activity_q;
            aux_activity_sync2_q <= aux_activity_sync1_q;
        end
    end

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            link_ready_q              <= 1'b0;
            reset_settle_q            <= 4'h0;
            reset_fault_q             <= 1'b0;
            protocol_error_q          <= 1'b0;
            pending_q                 <= 1'b0;
            rsp_data_q                <= {DATA_WIDTH{1'b0}};
            flow_count_q              <= {DATA_WIDTH{1'b0}};
            boot_manager_ns_q         <= 1'b0;
            boot_irq_ns_q             <= {SECURITY_IRQ_NS_WIDTH{1'b0}};
            boot_periph_ns_q          <= {SECURITY_PERIPH_NS_WIDTH{1'b0}};
            boot_security_locked_q    <= 1'b0;
            security_protocol_error_q <= 1'b0;
        end else begin
            if (aux_reset_sync2_q) begin
                link_ready_q   <= 1'b1;
                reset_settle_q <= 4'h0;
            end else begin
                link_ready_q <= 1'b0;
                if (!reset_settle_done_w) begin
                    reset_settle_q <= reset_settle_q + 4'h1;
                end else begin
                    reset_fault_q <= 1'b1;
                end
            end

            if (req_valid && !link_ready_w) begin
                protocol_error_q <= 1'b1;
            end

            if (security_access_w) begin
                if (security_write_w && (!security_unlock_ok_w || boot_security_locked_q)) begin
                    security_protocol_error_q <= 1'b1;
                end

                if (security_write_allowed_w) begin
                    case (security_subcmd_w)
                        SECURITY_SUB_MANAGER: begin
                            boot_manager_ns_q <= boot_manager_ns_update_w;
                        end
                        SECURITY_SUB_IRQ: begin
                            boot_irq_ns_q <= boot_irq_ns_update_w;
                        end
                        SECURITY_SUB_PERIPH: begin
                            boot_periph_ns_q <= boot_periph_ns_update_w;
                        end
                        SECURITY_SUB_STATUS: begin
                            boot_security_locked_q <= security_lock_w | boot_security_locked_q;
                        end
                        default: begin
                            security_protocol_error_q <= 1'b1;
                        end
                    endcase
                end

                if (security_lock_w) begin
                    boot_security_locked_q <= 1'b1;
                end
            end else if (non_security_accept_w && !boot_security_locked_q) begin
                boot_security_locked_q <= 1'b1;
            end

            if (accept_req_w) begin
                pending_q    <= 1'b1;
                flow_count_q <= flow_count_q + flow_increment_w;
                if (security_access_w && (security_read_w || !security_write_w)) begin
                    rsp_data_q <= security_status_w;
                end else if (security_access_w) begin
                    rsp_data_q <= security_status_w ^ security_mix_w;
                end else begin
                    rsp_data_q <= response_mix_w ^ security_mix_w;
                end
            end else if (consume_rsp_w) begin
                pending_q <= 1'b0;
            end
        end
    end

endmodule

`default_nettype wire


Current packet JSON (rtl/authoring_packets/module__pl330_target__workflow_todo_01.json):
{
  "context": {
    "connection_contract_gap": {
      "machine_readable_contract_count": 0,
      "reason": "Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.",
      "required_for_profile": true,
      "status": "missing"
    },
    "module_slice": {
      "count": 9,
      "enabled": true,
      "index": 8,
      "key": "workflow_todo_01",
      "module_task_count": 79,
      "rule": "Owner module pl330_target is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.",
      "section": "workflow_todo",
      "section_chunk_count": 2,
      "section_chunk_index": 1,
      "task_limit": 48
    },
    "owner": {
      "file": "rtl/pl330_target.sv",
      "name": "pl330_target",
      "refs": [],
      "wiring_only": false
    },
    "peer_modules": [
      {
        "file": "rtl/pl330_target_engine.sv",
        "name": "pl330_target_engine",
        "wiring_only": false
      },
      {
        "file": "rtl/pl330_target_pipeline.sv",
        "name": "pl330_target_pipeline",
        "wiring_only": false
      },
      {
        "file": "rtl/pl330_target_lsq.sv",
        "name": "pl330_target_lsq",
        "wiring_only": false
      },
      {
        "file": "rtl/pl330_target_mfifo.sv",
        "name": "pl330_target_mfifo",
        "wiring_only": false
      },
      {
        "file": "rtl/pl330_target_merge_buffer.sv",
        "name": "pl330_target_merge_buffer",
        "wiring_only": false
      },
      {
        "file": "rtl/pl330_target_icache.sv",
        "name": "pl330_target_icache",
        "wiring_only": false
      },
      {
        "file": "rtl/pl330_target_axi.sv",
        "name": "pl330_target_axi",
        "wiring_only": false
      },
      {
        "file": "rtl/pl330_target_periph.sv",
        "name": "pl330_target_periph",
        "wiring_only": false
      },
      {
        "file": "rtl/pl330_target_apb_regs.sv",
        "name": "pl330_target_apb_regs",
        "wiring_only": false
      },
      {
        "file": "rtl/pl330_target.sv",
        "name": "pl330_target",
        "wiring_only": false
      }
    ],
    "quality_profile": "production",
    "reference_profile": {
      "generated_at": "2026-05-06T19:33:36Z",
      "guidance": {
        "calibration_only": true,
        "do_not_copy_reference_rtl": true
      },
      "label": "pl330_reference",
      "path": "reports/rtl_reference_profile.json",
      "suggested_ssot_target_scale": {
        "basis": "candidate structural scale from rtl_reference_profile; review and lock in SSOT before enforcement",
        "control_flow_min": 260,
        "depth_score_min": 10416,
        "instances_min": 1049,
        "modules_min": 210,
        "nonconstant_assigns_min": 2890,
        "procedural_blocks_min": 910,
        "source_files_min": 143,
        "state_updates_min": 1219
      },
      "summary": {
        "always_blocks": 910,
        "assigns": 3049,
        "case_blocks": 260,
        "file_count": 143,
        "instance_candidates": 1049,
        "lines": 130568,
        "modules": 210,
        "state_updates": 1219
      },
      "top_by_lines": [
        {
          "lines": 8178,
          "path": "validation/pl301_a3bm_BM_5x7_1/verilog/axibm_master_interface_BM_5x7_1.v"
        },
        {
          "lines": 4714,
          "path": "validation/pl301_a3bm_BM_5x7_1/verilog/axibm_slave_interface_BM_5x7_1.v"
        },
        {
          "lines": 4498,
          "path": "validation/pl301_a3bm_BM_5x7_1/verilog/axibm_core_BM_5x7_1.v"
        },
        {
          "lines": 3800,
          "path": "BP062-VL-70002/AxiPC.v"
        },
        {
          "lines": 3800,
          "path": "pl330_dma/verilog/BP062-VL-70002/AxiPC.v"
        },
        {
          "lines": 3713,
          "path": "BP062-VL-70004/AxiPC.sv"
        },
        {
          "lines": 3605,
          "path": "pl330_dma/validation/verilog/pl330_subsystem.v.xsl"
        },
        {
          "lines": 3412,
          "path": "pl330_axi/verilog/pl330_axi_xmlcfg.v.xsl"
        },
        {
          "lines": 3258,
          "path": "validation/pl301_a3bm_BM_5x7_1/verilog/pl301_a3bm_protocol_conv_BM_5x7_1.v"
        },
        {
          "lines": 3235,
          "path": "validation/pl301_a3bm_BM_5x7_1/verilog/axibm_master_int_fwd_ctrl_a_BM_5x7_1.v"
        }
      ]
    },
    "ssot_connection_contracts": [],
    "ssot_top_io_contracts": [
      {
        "aliases": [
          "aclk"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "input",
        "name": "aclk",
        "source_ref": "clocks[0]",
        "width": "1"
      },
      {
        "aliases": [
          "aresetn"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "input",
        "name": "aresetn",
        "source_ref": "resets[0]",
        "width": "1"
      },
      {
        "aliases": [
          "clk"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "input",
        "name": "clk",
        "source_ref": "io_list.clock_domains[0].ports[0]",
        "width": "1"
      },
      {
        "aliases": [
          "rst_n"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "input",
        "name": "rst_n",
        "source_ref": "io_list.resets[0].ports[0]",
        "width": "1"
      },
      {
        "aliases": [
          "control_data_req_valid",
          "req_valid"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "input",
        "name": "req_valid",
        "source_ref": "io_list.interfaces[0].ports[0]",
        "width": "1"
      },
      {
        "aliases": [
          "control_data_req_ready",
          "req_ready"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "output",
        "name": "req_ready",
        "source_ref": "io_list.interfaces[0].ports[1]",
        "width": "1"
      },
      {
        "aliases": [
          "control_data_req_data",
          "req_data"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "input",
        "name": "req_data",
        "source_ref": "io_list.interfaces[0].ports[2]",
        "width": "DATA_WIDTH"
      },
      {
        "aliases": [
          "control_data_rsp_valid",
          "rsp_valid"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "output",
        "name": "rsp_valid",
        "source_ref": "io_list.interfaces[0].ports[3]",
        "width": "1"
      },
      {
        "aliases": [
          "control_data_rsp_ready",
          "rsp_ready"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "input",
        "name": "rsp_ready",
        "source_ref": "io_list.interfaces[0].ports[4]",
        "width": "1"
      },
      {
        "aliases": [
          "control_data_rsp_data",
          "rsp_data"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "output",
        "name": "rsp_data",
        "source_ref": "io_list.interfaces[0].ports[5]",
        "width": "DATA_WIDTH"
      },
      {
        "aliases": [
          "control_data_error",
          "error"
        ],
        "allow_constant": false,
        "allow_unused": false,
        "direction": "output",
        "name": "error",
        "source_ref": "io_list.interfaces[0].ports[6]",
        "width": "1"
      }
    ],
    "target_scale": {}
  },
  "execution_policy": {
    "blocked_by_locked_truth": [],
    "deferred_human_qa_allowed": true,
    "draft_allowed": true,
    "evidence_closure_allowed": false,
    "human_locked_open_count": 0,
    "integration_signoff_allowed": false,
    "llm_actionable": true,
    "llm_actionable_open_count": 2,
    "open_required_count": 2,
    "pass_allowed": false,
    "stop_conditions": [
      "Close this packet only after every required task in the packet has pass status.",
      "Return human_gate/change-request JSON when locked truth is missing instead of inventing semantics.",
      "Never use a fixed RTL template as the implementation."
    ],
    "work_allowed": true
  },
  "ip": "pl330_target",
  "kind": "module",
  "owner_file": "rtl/pl330_target.sv",
  "owner_module": "pl330_target",
  "packet_id": "module__pl330_target__workflow_todo_01",
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
      "workflow_todo.rtl_gen": 48
    },
    "module_slice": {
      "count": 9,
      "enabled": true,
      "index": 8,
      "key": "workflow_todo_01",
      "module_task_count": 79,
      "rule": "Owner module pl330_target is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.",
      "section": "workflow_todo",
      "section_chunk_count": 2,
      "section_chunk_index": 1,
      "task_limit": 48
    },
    "open_required_count": 2,
    "required_count": 48,
    "source_refs": [
      "workflow_todos.rtl-gen[0]",
      "workflow_todos.rtl-gen[10]",
      "workflow_todos.rtl-gen[16]",
      "workflow_todos.rtl-gen[17]",
      "workflow_todos.rtl-gen[18]",
      "workflow_todos.rtl-gen[19]",
      "workflow_todos.rtl-gen[20]",
      "workflow_todos.rtl-gen[21]",
      "workflow_todos.rtl-gen[22]",
      "workflow_todos.rtl-gen[23]",
      "workflow_todos.rtl-gen[24]",
      "workflow_todos.rtl-gen[25]",
      "workflow_todos.rtl-gen[26]",
      "workflow_todos.rtl-gen[27]",
      "workflow_todos.rtl-gen[28]",
      "workflow_todos.rtl-gen[29]",
      "workflow_todos.rtl-gen[30]",
      "workflow_todos.rtl-gen[31]",
      "workflow_todos.rtl-gen[32]",
      "workflow_todos.rtl-gen[33]",
      "workflow_todos.rtl-gen[34]",
      "workflow_todos.rtl-gen[35]",
      "workflow_todos.rtl-gen[36]",
      "workflow_todos.rtl-gen[37]"
    ],
    "status_counts": {
      "open": 2,
      "pass": 46
    },
    "task_count": 48
  },
  "tasks": [
    {
      "category": "workflow_todo.rtl_gen",
      "content": "Implement the complete SSOT RTL contract without fixed-template fallback behavior",
      "criteria": [
        "Generated RTL drives only SSOT-approved externally visible behavior",
        "No placeholder heartbeat, tie-off, alive-only, or comment-only implementation is used as evidence",
        "derive_rtl_todos.py --audit-rtl reports every required TODO as pass",
        "SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json",
        "RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets",
        "Traceability keeps source_ref workflow_todos.rtl-gen[0]",
        "Primary implementation evidence is in rtl/pl330_target.sv",
        "Semantic source_refs covered: cycle_model, function_model, quality_gates.rtl, quality_gates.rtl_gen, top_module"
      ],
      "detail": "Use the current SSOT as the only source for ports, parameters, function_model, cycle_model, registers, dataflow, error/security/debug behavior, decomposition ownership, and quality gates.\nSSOT ref: workflow_todos.rtl-gen[0].\nOwner: pl330_target in rtl/pl330_target.sv via workflow_todos.owner.\nSSOT item context: id=RTL_IMPLEMENT_SSOT_CONTRACT.",
      "evidence_terms": [
        "CONTRACT",
        "RTL_IMPLEMENT_SSOT_CONTRACT",
        "SSOT",
        "derive",
        "derive_rtl_todos",
        "gates",
        "pl330",
        "pl330_target",
        "quality",
        "quality_gates",
        "rtl_gen",
        "target",
        "todos",
        "top",
        "top_module"
      ],
      "id": "RTL-0027",
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "priority": "high",
      "required": true,
      "source_ref": "workflow_todos.rtl-gen[0]",
      "ssot_context": {
        "id": "RTL_IMPLEMENT_SSOT_CONTRACT"
      },
      "ssot_refs": [
        "cycle_model",
        "function_model",
        "quality_gates.rtl",
        "quality_gates.rtl_gen",
        "top_module",
        "workflow_todos.rtl-gen[0]"
      ],
      "static_evidence": {
        "matched_count": 3,
        "matched_terms": [
          "pl330",
          "pl330_target",
          "target"
        ],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 3,
        "required_terms": [
          "CONTRACT",
          "RTL_IMPLEMENT_SSOT_CONTRACT",
          "SSOT",
          "derive",
          "derive_rtl_todos",
          "gates",
          "pl330",
          "pl330_target",
          "quality",
          "quality_gates",
          "rtl_gen",
          "target",
          "todos",
          "top",
          "top_module"
        ],
        "source_scope": "rtl/pl330_target.sv",
        "status": "pass"
      },
      "todo_completion": {
        "criteria_total": 8,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.",
        "required": true,
        "status": "pass"
      },
      "workflow_todo": {
        "id": "RTL_IMPLEMENT_SSOT_CONTRACT",
        "source_refs": [
          "cycle_model",
          "function_model",
          "quality_gates.rtl",
          "quality_gates.rtl_gen",
          "top_module"
        ],
        "stage": "rtl-gen",
        "user_category": ""
      }
    },
    {
      "category": "workflow_todo.rtl_gen",
      "content": "Implement or account for SSOT module slice `pl330_target`",
      "criteria": [
        "Owned SSOT refs are implemented in the owner RTL file or explicitly mapped to the top integration module",
        "Module slice has traceability evidence in rtl_todo_plan.json",
        "No function/cycle/register/dataflow/FSM task owned by this slice remains orphaned",
        "SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json",
        "RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets",
        "Traceability keeps source_ref workflow_todos.rtl-gen[10]",
        "Primary implementation evidence is in rtl/pl330_target.sv",
        "Semantic source_refs covered: sub_modules[9]"
      ],
      "detail": "Top-level integration module matching SSOT top_module\nSSOT ref: workflow_todos.rtl-gen[10].\nOwner: pl330_target in rtl/pl330_target.sv via workflow_todos.owner.\nSSOT item context: id=RTL_MODULE_PL330_TARGET.",
      "evidence_terms": [
        "PL330",
        "RTL_MODULE_PL330_TARGET",
        "TARGET",
        "modules",
        "pl330",
        "pl330_target",
        "plan",
        "rtl_todo_plan",
        "sub",
        "sub_modules",
        "target",
        "todo",
        "top",
        "top_module"
      ],
      "id": "RTL-0037",
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "priority": "high",
      "required": true,
      "source_ref": "workflow_todos.rtl-gen[10]",
      "ssot_context": {
        "id": "RTL_MODULE_PL330_TARGET"
      },
      "ssot_refs": [
        "sub_modules[9]",
        "workflow_todos.rtl-gen[10]"
      ],
      "static_evidence": {
        "matched_count": 3,
        "matched_terms": [
          "pl330",
          "pl330_target",
          "target"
        ],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 3,
        "required_terms": [
          "PL330",
          "RTL_MODULE_PL330_TARGET",
          "TARGET",
          "modules",
          "pl330",
          "pl330_target",
          "plan",
          "rtl_todo_plan",
          "sub",
          "sub_modules",
          "target",
          "todo",
          "top",
          "top_module"
        ],
        "source_scope": "rtl/pl330_target.sv",
        "status": "pass"
      },
      "todo_completion": {
        "criteria_total": 8,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.",
        "required": true,
        "status": "pass"
      },
      "workflow_todo": {
        "id": "RTL_MODULE_PL330_TARGET",
        "source_refs": [
          "sub_modules[9]"
        ],
        "stage": "rtl-gen",
        "user_category": ""
      }
    },
    {
      "category": "workflow_todo.rtl_gen",
      "content": "Implement FunctionalModel transaction `FM_DMASTP` in RTL",
      "criteria": [
        "RTL samples the transaction only under the approved preconditions",
        "All listed outputs are driven with machine-checkable behavior or SSOT-approved status/error mapping",
        "All side effects and error cases have observable state, status, or handoff evidence",
        "SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json",
        "RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets",
        "Traceability keeps source_ref workflow_todos.rtl-gen[16]",
        "Primary implementation evidence is in rtl/pl330_target.sv",
        "Semantic source_refs covered: function_model.transactions.FM_DMASTP, function_model.transactions[5]"
      ],
      "detail": "Preconditions: channel_state==1; periph davalid acknowledged. Outputs: outstanding_writes += 1. Side effects: daready asserted; AXI AW+W issued. Error cases: .\nSSOT ref: workflow_todos.rtl-gen[16].\nOwner: pl330_target in rtl/pl330_target.sv via workflow_todos.owner.\nSSOT item context: id=RTL_FM_TX_FM_DMASTP.",
      "evidence_terms": [
        "DMASTP",
        "FM",
        "FM_DMASTP",
        "RTL_FM_TX_FM_DMASTP",
        "TX",
        "channel",
        "channel_state",
        "outstanding",
        "outstanding_writes",
        "pl330",
        "pl330_target",
        "target",
        "writes"
      ],
      "id": "RTL-0043",
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "priority": "high",
      "required": true,
      "source_ref": "workflow_todos.rtl-gen[16]",
      "ssot_context": {
        "id": "RTL_FM_TX_FM_DMASTP"
      },
      "ssot_refs": [
        "function_model.transactions.FM_DMASTP",
        "function_model.transactions[5]",
        "workflow_todos.rtl-gen[16]"
      ],
      "static_evidence": {
        "matched_count": 3,
        "matched_terms": [
          "pl330",
          "pl330_target",
          "target"
        ],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 3,
        "required_terms": [
          "DMASTP",
          "FM",
          "FM_DMASTP",
          "RTL_FM_TX_FM_DMASTP",
          "TX",
          "channel",
          "channel_state",
          "outstanding",
          "outstanding_writes",
          "pl330",
          "pl330_target",
          "target",
          "writes"
        ],
        "source_scope": "rtl/pl330_target.sv",
        "status": "pass"
      },
      "todo_completion": {
        "criteria_total": 8,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.",
        "required": true,
        "status": "pass"
      },
      "workflow_todo": {
        "id": "RTL_FM_TX_FM_DMASTP",
        "source_refs": [
          "function_model.transactions.FM_DMASTP",
          "function_model.transactions[5]"
        ],
        "stage": "rtl-gen",
        "user_category": ""
      }
    },
    {
      "category": "workflow_todo.rtl_gen",
      "content": "Implement FunctionalModel transaction `FM_DMASEV` in RTL",
      "criteria": [
        "RTL samples the transaction only under the approved preconditions",
        "All listed outputs are driven with machine-checkable behavior or SSOT-approved status/error mapping",
        "All side effects and error cases have observable state, status, or handoff evidence",
        "SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json",
        "RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets",
        "Traceability keeps source_ref workflow_todos.rtl-gen[17]",
        "Primary implementation evidence is in rtl/pl330_target.sv",
        "Semantic source_refs covered: function_model.transactions.FM_DMASEV, function_model.transactions[6]"
      ],
      "detail": "Preconditions: channel_state==1; event index < NUM_IRQS. Outputs: irq_status |= 1<<event_idx. Side effects: irq[event_idx] pulse. Error cases: .\nSSOT ref: workflow_todos.rtl-gen[17].\nOwner: pl330_target in rtl/pl330_target.sv via workflow_todos.owner.\nSSOT item context: id=RTL_FM_TX_FM_DMASEV.",
      "evidence_terms": [
        "DMASEV",
        "FM",
        "FM_DMASEV",
        "IRQS",
        "NUM",
        "NUM_IRQS",
        "RTL_FM_TX_FM_DMASEV",
        "TX",
        "channel",
        "channel_state",
        "event_idx",
        "idx",
        "irq",
        "irq_status",
        "pl330",
        "pl330_target"
      ],
      "id": "RTL-0044",
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "priority": "high",
      "required": true,
      "source_ref": "workflow_todos.rtl-gen[17]",
      "ssot_context": {
        "id": "RTL_FM_TX_FM_DMASEV"
      },
      "ssot_refs": [
        "function_model.transactions.FM_DMASEV",
        "function_model.transactions[6]",
        "workflow_todos.rtl-gen[17]"
      ],
      "static_evidence": {
        "matched_count": 3,
        "matched_terms": [
          "irq",
          "pl330",
          "pl330_target"
        ],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 3,
        "required_terms": [
          "DMASEV",
          "FM",
          "FM_DMASEV",
          "IRQS",
          "NUM",
          "NUM_IRQS",
          "RTL_FM_TX_FM_DMASEV",
          "TX",
          "channel",
          "channel_state",
          "event_idx",
          "idx",
          "irq",
          "irq_status",
          "pl330",
          "pl330_target"
        ],
        "source_scope": "rtl/pl330_target.sv",
        "status": "pass"
      },
      "todo_completion": {
        "criteria_total": 8,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.",
        "required": true,
        "status": "pass"
      },
      "workflow_todo": {
        "id": "RTL_FM_TX_FM_DMASEV",
        "source_refs": [
          "function_model.transactions.FM_DMASEV",
          "function_model.transactions[6]"
        ],
        "stage": "rtl-gen",
        "user_category": ""
      }
    },
    {
      "category": "workflow_todo.rtl_gen",
      "content": "Implement FunctionalModel transaction `FM_DMAEND` in RTL",
      "criteria": [
        "RTL samples the transaction only under the approved preconditions",
        "All listed outputs are driven with machine-checkable behavior or SSOT-approved status/error mapping",
        "All side effects and error cases have observable state, status, or handoff evidence",
        "SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json",
        "RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets",
        "Traceability keeps source_ref workflow_todos.rtl-gen[18]",
        "Primary implementation evidence is in rtl/pl330_target.sv",
        "Semantic source_refs covered: function_model.transactions.FM_DMAEND, function_model.transactions[7]"
      ],
      "detail": "Preconditions: channel_state==1; no outstanding. Outputs: channel_state=0. Side effects: . Error cases: condition=outstanding > 0.\nSSOT ref: workflow_todos.rtl-gen[18].\nOwner: pl330_target in rtl/pl330_target.sv via workflow_todos.owner.\nSSOT item context: id=RTL_FM_TX_FM_DMAEND.",
      "evidence_terms": [
        "DMAEND",
        "FM",
        "FM_DMAEND",
        "RTL_FM_TX_FM_DMAEND",
        "TX",
        "channel",
        "channel_state",
        "pl330",
        "pl330_target",
        "target"
      ],
      "id": "RTL-0045",
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "priority": "high",
      "required": true,
      "source_ref": "workflow_todos.rtl-gen[18]",
      "ssot_context": {
        "id": "RTL_FM_TX_FM_DMAEND"
      },
      "ssot_refs": [
        "function_model.transactions.FM_DMAEND",
        "function_model.transactions[7]",
        "workflow_todos.rtl-gen[18]"
      ],
      "static_evidence": {
        "matched_count": 3,
        "matched_terms": [
          "pl330",
          "pl330_target",
          "target"
        ],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 3,
        "required_terms": [
          "DMAEND",
          "FM",
          "FM_DMAEND",
          "RTL_FM_TX_FM_DMAEND",
          "TX",
          "channel",
          "channel_state",
          "pl330",
          "pl330_target",
          "target"
        ],
        "source_scope": "rtl/pl330_target.sv",
        "status": "pass"
      },
      "todo_completion": {
        "criteria_total": 8,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.",
        "required": true,
        "status": "pass"
      },
      "workflow_todo": {
        "id": "RTL_FM_TX_FM_DMAEND",
        "source_refs": [
          "function_model.transactions.FM_DMAEND",
          "function_model.transactions[7]"
        ],
        "stage": "rtl-gen",
        "user_category": ""
      }
    },
    {
      "category": "workflow_todo.rtl_gen",
      "content": "Implement FunctionalModel transaction `FM_FAULT` in RTL",
      "criteria": [
        "RTL samples the transaction only under the approved preconditions",
        "All listed outputs are driven with machine-checkable behavior or SSOT-approved status/error mapping",
        "All side effects and error cases have observable state, status, or handoff evidence",
        "SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json",
        "RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets",
        "Traceability keeps source_ref workflow_todos.rtl-gen[19]",
        "Primary implementation evidence is in rtl/pl330_target.sv",
        "Semantic source_refs covered: function_model.transactions.FM_FAULT, function_model.transactions[8]"
      ],
      "detail": "Preconditions: any error_case fired. Outputs: channel_state=8; irq_abort pulse. Side effects: fault_status updated. Error cases: .\nSSOT ref: workflow_todos.rtl-gen[19].\nOwner: pl330_target in rtl/pl330_target.sv via workflow_todos.owner.\nSSOT item context: id=RTL_FM_TX_FM_FAULT.",
      "evidence_terms": [
        "FAULT",
        "FM",
        "FM_FAULT",
        "RTL_FM_TX_FM_FAULT",
        "TX",
        "abort",
        "case",
        "channel",
        "channel_state",
        "error_case",
        "fault",
        "fault_status",
        "irq",
        "irq_abort",
        "pl330",
        "pl330_target"
      ],
      "id": "RTL-0046",
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "priority": "high",
      "required": true,
      "source_ref": "workflow_todos.rtl-gen[19]",
      "ssot_context": {
        "id": "RTL_FM_TX_FM_FAULT"
      },
      "ssot_refs": [
        "function_model.transactions.FM_FAULT",
        "function_model.transactions[8]",
        "workflow_todos.rtl-gen[19]"
      ],
      "static_evidence": {
        "matched_count": 5,
        "matched_terms": [
          "case",
          "fault",
          "irq",
          "pl330",
          "pl330_target"
        ],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 3,
        "required_terms": [
          "FAULT",
          "FM",
          "FM_FAULT",
          "RTL_FM_TX_FM_FAULT",
          "TX",
          "abort",
          "case",
          "channel",
          "channel_state",
          "error_case",
          "fault",
          "fault_status",
          "irq",
          "irq_abort",
          "pl330",
          "pl330_target"
        ],
        "source_scope": "rtl/pl330_target.sv",
        "status": "pass"
      },
      "todo_completion": {
        "criteria_total": 8,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.",
        "required": true,
        "status": "pass"
      },
      "workflow_todo": {
        "id": "RTL_FM_TX_FM_FAULT",
        "source_refs": [
          "function_model.transactions.FM_FAULT",
          "function_model.transactions[8]"
        ],
        "stage": "rtl-gen",
        "user_category": ""
      }
    },
    {
      "category": "workflow_todo.rtl_gen",
      "content": "Implement cycle_model handshake rule 0",
      "criteria": [
        "RTL timing/handshake behavior follows this cycle_model entry",
        "Signals remain stable or advance only under the approved protocol phase",
        "The behavior is visible to waveform/sim-debug or scoreboard checks",
        "SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json",
        "RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets",
        "Traceability keeps source_ref workflow_todos.rtl-gen[20]",
        "Primary implementation evidence is in rtl/pl330_target.sv",
        "Semantic source_refs covered: cycle_model.handshake_rules[0]"
      ],
      "detail": "rule=req_valid payload remains stable until req_ready is sampled asserted on control_data.\nSSOT ref: workflow_todos.rtl-gen[20].\nOwner: pl330_target in rtl/pl330_target.sv via workflow_todos.owner.\nSSOT item context: id=RTL_CYCLE_handshake_rules_ITEM_0.",
      "evidence_terms": [
        "control_data",
        "data",
        "pl330",
        "pl330_target",
        "ready",
        "req",
        "req_ready",
        "req_valid",
        "target",
        "valid"
      ],
      "id": "RTL-0047",
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "priority": "high",
      "required": true,
      "source_ref": "workflow_todos.rtl-gen[20]",
      "ssot_context": {
        "id": "RTL_CYCLE_handshake_rules_ITEM_0"
      },
      "ssot_refs": [
        "cycle_model.handshake_rules[0]",
        "workflow_todos.rtl-gen[20]"
      ],
      "static_evidence": {
        "matched_count": 9,
        "matched_terms": [
          "data",
          "pl330",
          "pl330_target",
          "ready",
          "req",
          "req_ready",
          "req_valid",
          "target",
          "valid"
        ],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 3,
        "required_terms": [
          "control_data",
          "data",
          "pl330",
          "pl330_target",
          "ready",
          "req",
          "req_ready",
          "req_valid",
          "target",
          "valid"
        ],
        "source_scope": "rtl/pl330_target.sv",
        "status": "pass"
      },
      "todo_completion": {
        "criteria_total": 8,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.",
        "required": true,
        "status": "pass"
      },
      "workflow_todo": {
        "id": "RTL_CYCLE_handshake_rules_ITEM_0",
        "source_refs": [
          "cycle_model.handshake_rules[0]"
        ],
        "stage": "rtl-gen",
        "user_category": ""
      }
    },
    {
      "category": "workflow_todo.rtl_gen",
      "content": "Implement cycle_model handshake rule 1",
      "criteria": [
        "RTL timing/handshake behavior follows this cycle_model entry",
        "Signals remain stable or advance only under the approved protocol phase",
        "The behavior is visible to waveform/sim-debug or scoreboard checks",
        "SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json",
        "RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets",
        "Traceability keeps source_ref workflow_todos.rtl-gen[21]",
        "Primary implementation evidence is in rtl/pl330_target.sv",
        "Semantic source_refs covered: cycle_model.handshake_rules[1]"
      ],
      "detail": "rule=rsp_valid payload remains stable until rsp_ready is sampled asserted on control_data.\nSSOT ref: workflow_todos.rtl-gen[21].\nOwner: pl330_target in rtl/pl330_target.sv via workflow_todos.owner.\nSSOT item context: id=RTL_CYCLE_handshake_rules_1.",
      "evidence_terms": [
        "control_data",
        "data",
        "pl330",
        "pl330_target",
        "ready",
        "rsp",
        "rsp_ready",
        "rsp_valid",
        "target",
        "valid"
      ],
      "id": "RTL-0048",
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "priority": "high",
      "required": true,
      "source_ref": "workflow_todos.rtl-gen[21]",
      "ssot_context": {
        "id": "RTL_CYCLE_handshake_rules_1"
      },
      "ssot_refs": [
        "cycle_model.handshake_rules[1]",
        "workflow_todos.rtl-gen[21]"
      ],
      "static_evidence": {
        "matched_count": 9,
        "matched_terms": [
          "data",
          "pl330",
          "pl330_target",
          "ready",
          "rsp",
          "rsp_ready",
          "rsp_valid",
          "target",
          "valid"
        ],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 3,
        "required_terms": [
          "control_data",
          "data",
          "pl330",
          "pl330_target",
          "ready",
          "rsp",
          "rsp_ready",
          "rsp_valid",
          "target",
          "valid"
        ],
        "source_scope": "rtl/pl330_target.sv",
        "status": "pass"
      },
      "todo_completion": {
        "criteria_total": 8,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.",
        "required": true,
        "status": "pass"
      },
      "workflow_todo": {
        "id": "RTL_CYCLE_handshake_rules_1",
        "source_refs": [
          "cycle_model.handshake_rules[1]"
        ],
        "stage": "rtl-gen",
        "user_category": ""
      }
    },
    {
      "category": "workflow_todo.rtl_gen",
      "content": "Implement cycle_model pipeline stage 0",
      "criteria": [
        "RTL timing/handshake behavior follows this cycle_model entry",
        "Signals remain stable or advance only under the approved protocol phase",
        "The behavior is visible to waveform/sim-debug or scoreboard checks",
        "SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json",
        "RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets",
        "Traceability keeps source_ref workflow_todos.rtl-gen[22]",
        "Primary implementation evidence is in rtl/pl330_target.sv",
        "Semantic source_refs covered: cycle_model.pipeline[0]"
      ],
      "detail": "action=Accept legal request/command/packet/control work under declared handshake rules.\nSSOT ref: workflow_todos.rtl-gen[22].\nOwner: pl330_target in rtl/pl330_target.sv via workflow_todos.owner.\nSSOT item context: id=RTL_CYCLE_pipeline_ITEM_0.",
      "evidence_terms": [
        "pl330",
        "pl330_target",
        "target"
      ],
      "id": "RTL-0049",
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "priority": "high",
      "required": true,
      "source_ref": "workflow_todos.rtl-gen[22]",
      "ssot_context": {
        "id": "RTL_CYCLE_pipeline_ITEM_0"
      },
      "ssot_refs": [
        "cycle_model.pipeline[0]",
        "workflow_todos.rtl-gen[22]"
      ],
      "static_evidence": {
        "matched_count": 3,
        "matched_terms": [
          "pl330",
          "pl330_target",
          "target"
        ],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 3,
        "required_terms": [
          "pl330",
          "pl330_target",
          "target"
        ],
        "source_scope": "rtl/pl330_target.sv",
        "status": "pass"
      },
      "todo_completion": {
        "criteria_total": 8,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.",
        "required": true,
        "status": "pass"
      },
      "workflow_todo": {
        "id": "RTL_CYCLE_pipeline_ITEM_0",
        "source_refs": [
          "cycle_model.pipeline[0]"
        ],
        "stage": "rtl-gen",
        "user_category": ""
      }
    },
    {
      "category": "workflow_todo.rtl_gen",
      "content": "Implement cycle_model pipeline stage 1",
      "criteria": [
        "RTL timing/handshake behavior follows this cycle_model entry",
        "Signals remain stable or advance only under the approved protocol phase",
        "The behavior is visible to waveform/sim-debug or scoreboard checks",
        "SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json",
        "RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets",
        "Traceability keeps source_ref workflow_todos.rtl-gen[23]",
        "Primary implementation evidence is in rtl/pl330_target.sv",
        "Semantic source_refs covered: cycle_model.pipeline[1]"
      ],
      "detail": "action=Evaluate function_model transaction and update only declared state.\nSSOT ref: workflow_todos.rtl-gen[23].\nOwner: pl330_target in rtl/pl330_target.sv via workflow_todos.owner.\nSSOT item context: id=RTL_CYCLE_pipeline_1.",
      "evidence_terms": [
        "pl330",
        "pl330_target",
        "target"
      ],
      "id": "RTL-0050",
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "priority": "high",
      "required": true,
      "source_ref": "workflow_todos.rtl-gen[23]",
      "ssot_context": {
        "id": "RTL_CYCLE_pipeline_1"
      },
      "ssot_refs": [
        "cycle_model.pipeline[1]",
        "workflow_todos.rtl-gen[23]"
      ],
      "static_evidence": {
        "matched_count": 3,
        "matched_terms": [
          "pl330",
          "pl330_target",
          "target"
        ],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 3,
        "required_terms": [
          "pl330",
          "pl330_target",
          "target"
        ],
        "source_scope": "rtl/pl330_target.sv",
        "status": "pass"
      },
      "todo_completion": {
        "criteria_total": 8,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.",
        "required": true,
        "status": "pass"
      },
      "workflow_todo": {
        "id": "RTL_CYCLE_pipeline_1",
        "source_refs": [
          "cycle_model.pipeline[1]"
        ],
        "stage": "rtl-gen",
        "user_category": ""
      }
    },
    {
      "category": "workflow_todo.rtl_gen",
      "content": "Implement cycle_model pipeline stage 2",
      "criteria": [
        "RTL timing/handshake behavior follows this cycle_model entry",
        "Signals remain stable or advance only under the approved protocol phase",
        "The behavior is visible to waveform/sim-debug or scoreboard checks",
        "SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json",
        "RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets",
        "Traceability keeps source_ref workflow_todos.rtl-gen[24]",
        "Primary implementation evidence is in rtl/pl330_target.sv",
        "Semantic source_refs covered: cycle_model.pipeline[2]"
      ],
      "detail": "action=Publish response/status/output/debug event and hold it stable until accepted.\nSSOT ref: workflow_todos.rtl-gen[24].\nOwner: pl330_target in rtl/pl330_target.sv via workflow_todos.owner.\nSSOT item context: id=RTL_CYCLE_pipeline_2.",
      "evidence_terms": [
        "pl330",
        "pl330_target",
        "target"
      ],
      "id": "RTL-0051",
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "priority": "high",
      "required": true,
      "source_ref": "workflow_todos.rtl-gen[24]",
      "ssot_context": {
        "id": "RTL_CYCLE_pipeline_2"
      },
      "ssot_refs": [
        "cycle_model.pipeline[2]",
        "workflow_todos.rtl-gen[24]"
      ],
      "static_evidence": {
        "matched_count": 3,
        "matched_terms": [
          "pl330",
          "pl330_target",
          "target"
        ],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 3,
        "required_terms": [
          "pl330",
          "pl330_target",
          "target"
        ],
        "source_scope": "rtl/pl330_target.sv",
        "status": "pass"
      },
      "todo_completion": {
        "criteria_total": 8,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.",
        "required": true,
        "status": "pass"
      },
      "workflow_todo": {
        "id": "RTL_CYCLE_pipeline_2",
        "source_refs": [
          "cycle_model.pipeline[2]"
        ],
        "stage": "rtl-gen",
        "user_category": ""
      }
    },
    {
      "category": "workflow_todo.rtl_gen",
      "content": "Implement cycle_model ordering rule 0",
      "criteria": [
        "RTL timing/handshake behavior follows this cycle_model entry",
        "Signals remain stable or advance only under the approved protocol phase",
        "The behavior is visible to waveform/sim-debug or scoreboard checks",
        "SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json",
        "RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets",
        "Traceability keeps source_ref workflow_todos.rtl-gen[25]",
        "Primary implementation evidence is in rtl/pl330_target.sv",
        "Semantic source_refs covered: cycle_model.ordering[0]"
      ],
      "detail": "Accepted requests update architectural state only on clock edges.\nSSOT ref: workflow_todos.rtl-gen[25].\nOwner: pl330_target in rtl/pl330_target.sv via workflow_todos.owner.\nSSOT item context: id=RTL_CYCLE_ordering_ITEM_0.",
      "evidence_terms": [
        "pl330",
        "pl330_target",
        "target"
      ],
      "id": "RTL-0052",
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "priority": "high",
      "required": true,
      "source_ref": "workflow_todos.rtl-gen[25]",
      "ssot_context": {
        "id": "RTL_CYCLE_ordering_ITEM_0"
      },
      "ssot_refs": [
        "cycle_model.ordering[0]",
        "workflow_todos.rtl-gen[25]"
      ],
      "static_evidence": {
        "matched_count": 3,
        "matched_terms": [
          "pl330",
          "pl330_target",
          "target"
        ],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 3,
        "required_terms": [
          "pl330",
          "pl330_target",
          "target"
        ],
        "source_scope": "rtl/pl330_target.sv",
        "status": "pass"
      },
      "todo_completion": {
        "criteria_total": 8,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.",
        "required": true,
        "status": "pass"
      },
      "workflow_todo": {
        "id": "RTL_CYCLE_ordering_ITEM_0",
        "source_refs": [
          "cycle_model.ordering[0]"
        ],
        "stage": "rtl-gen",
        "user_category": ""
      }
    },
    {
      "category": "workflow_todo.rtl_gen",
      "content": "Implement cycle_model ordering rule 1",
      "criteria": [
        "RTL timing/handshake behavior follows this cycle_model entry",
        "Signals remain stable or advance only under the approved protocol phase",
        "The behavior is visible to waveform/sim-debug or scoreboard checks",
        "SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json",
        "RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets",
        "Traceability keeps source_ref workflow_todos.rtl-gen[26]",
        "Primary implementation evidence is in rtl/pl330_target.sv",
        "Semantic source_refs covered: cycle_model.ordering[1]"
      ],
      "detail": "Completion/status/interrupt updates occur after the operation reaches its terminal FSM state.\nSSOT ref: workflow_todos.rtl-gen[26].\nOwner: pl330_target in rtl/pl330_target.sv via workflow_todos.owner.\nSSOT item context: id=RTL_CYCLE_ordering_1.",
      "evidence_terms": [
        "pl330",
        "pl330_target",
        "target"
      ],
      "id": "RTL-0053",
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "priority": "high",
      "required": true,
      "source_ref": "workflow_todos.rtl-gen[26]",
      "ssot_context": {
        "id": "RTL_CYCLE_ordering_1"
      },
      "ssot_refs": [
        "cycle_model.ordering[1]",
        "workflow_todos.rtl-gen[26]"
      ],
      "static_evidence": {
        "matched_count": 3,
        "matched_terms": [
          "pl330",
          "pl330_target",
       
... <truncated 107255 chars>

Current packet Markdown (rtl/authoring_packets/module__pl330_target__workflow_todo_01.md):
# RTL Authoring Packet: module__pl330_target__workflow_todo_01

- Kind: module
- Owner module: pl330_target
- Owner file: rtl/pl330_target.sv
- Task count: 48
- Required tasks: 48

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
- Record generated RTL files and todo_plan_sha256 in rtl_authoring_provenance.json.

## Context

- Quality profile: production
- Draft allowed: True
- PASS allowed: False
- Integration signoff allowed: False
- LLM-actionable open tasks: 2
- Human-locked open tasks: 0
- Module slice: 8/9 section=workflow_todo task_limit=48
- Slice rule: Owner module pl330_target is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- Reference scale profile: reports/rtl_reference_profile.json (calibration-only, files=143, modules=210, lines=130568)
- Reference target-scale candidate present; SSOT target_scale is not locked yet
- Connection contract gap: Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.
- SSOT top IO contracts: 11

## Tasks

### RTL-0027: Implement the complete SSOT RTL contract without fixed-template fallback behavior

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[0]
- Detail: Use the current SSOT as the only source for ports, parameters, function_model, cycle_model, registers, dataflow, error/security/debug behavior, decomposition ownership, and quality gates.
SSOT ref: workflow_todos.rtl-gen[0].
Owner: pl330_target in rtl/pl330_target.sv via workflow_todos.owner.
SSOT item context: id=RTL_IMPLEMENT_SSOT_CONTRACT.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Generated RTL drives only SSOT-approved externally visible behavior
  - No placeholder heartbeat, tie-off, alive-only, or comment-only implementation is used as evidence
  - derive_rtl_todos.py --audit-rtl reports every required TODO as pass
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[0]
  - Primary implementation evidence is in rtl/pl330_target.sv
  - Semantic source_refs covered: cycle_model, function_model, quality_gates.rtl, quality_gates.rtl_gen, top_module
- SSOT refs: cycle_model, function_model, quality_gates.rtl, quality_gates.rtl_gen, top_module, workflow_todos.rtl-gen[0]

### RTL-0037: Implement or account for SSOT module slice `pl330_target`

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[10]
- Detail: Top-level integration module matching SSOT top_module
SSOT ref: workflow_todos.rtl-gen[10].
Owner: pl330_target in rtl/pl330_target.sv via workflow_todos.owner.
SSOT item context: id=RTL_MODULE_PL330_TARGET.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Owned SSOT refs are implemented in the owner RTL file or explicitly mapped to the top integration module
  - Module slice has traceability evidence in rtl_todo_plan.json
  - No function/cycle/register/dataflow/FSM task owned by this slice remains orphaned
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[10]
  - Primary implementation evidence is in rtl/pl330_target.sv
  - Semantic source_refs covered: sub_modules[9]
- SSOT refs: sub_modules[9], workflow_todos.rtl-gen[10]

### RTL-0043: Implement FunctionalModel transaction `FM_DMASTP` in RTL

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[16]
- Detail: Preconditions: channel_state==1; periph davalid acknowledged. Outputs: outstanding_writes += 1. Side effects: daready asserted; AXI AW+W issued. Error cases: .
SSOT ref: workflow_todos.rtl-gen[16].
Owner: pl330_target in rtl/pl330_target.sv via workflow_todos.owner.
SSOT item context: id=RTL_FM_TX_FM_DMASTP.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL samples the transaction only under the approved preconditions
  - All listed outputs are driven with machine-checkable behavior or SSOT-approved status/error mapping
  - All side effects and error cases have observable state, status, or handoff evidence
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[16]
  - Primary implementation evidence is in rtl/pl330_target.sv
  - Semantic source_refs covered: function_model.transactions.FM_DMASTP, function_model.transactions[5]
- SSOT refs: function_model.transactions.FM_DMASTP, function_model.transactions[5], workflow_todos.rtl-gen[16]

### RTL-0044: Implement FunctionalModel transaction `FM_DMASEV` in RTL

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[17]
- Detail: Preconditions: channel_state==1; event index < NUM_IRQS. Outputs: irq_status |= 1<<event_idx. Side effects: irq[event_idx] pulse. Error cases: .
SSOT ref: workflow_todos.rtl-gen[17].
Owner: pl330_target in rtl/pl330_target.sv via workflow_todos.owner.
SSOT item context: id=RTL_FM_TX_FM_DMASEV.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL samples the transaction only under the approved preconditions
  - All listed outputs are driven with machine-checkable behavior or SSOT-approved status/error mapping
  - All side effects and error cases have observable state, status, or handoff evidence
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[17]
  - Primary implementation evidence is in rtl/pl330_target.sv
  - Semantic source_refs covered: function_model.transactions.FM_DMASEV, function_model.transactions[6]
- SSOT refs: function_model.transactions.FM_DMASEV, function_model.transactions[6], workflow_todos.rtl-gen[17]

### RTL-0045: Implement FunctionalModel transaction `FM_DMAEND` in RTL

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[18]
- Detail: Preconditions: channel_state==1; no outstanding. Outputs: channel_state=0. Side effects: . Error cases: condition=outstanding > 0.
SSOT ref: workflow_todos.rtl-gen[18].
Owner: pl330_target in rtl/pl330_target.sv via workflow_todos.owner.
SSOT item context: id=RTL_FM_TX_FM_DMAEND.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL samples the transaction only under the approved preconditions
  - All listed outputs are driven with machine-checkable behavior or SSOT-approved status/error mapping
  - All side effects and error cases have observable state, status, or handoff evidence
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[18]
  - Primary implementation evidence is in rtl/pl330_target.sv
  - Semantic source_refs covered: function_model.transactions.FM_DMAEND, function_model.transactions[7]
- SSOT refs: function_model.transactions.FM_DMAEND, function_model.transactions[7], workflow_todos.rtl-gen[18]

### RTL-0046: Implement FunctionalModel transaction `FM_FAULT` in RTL

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[19]
- Detail: Preconditions: any error_case fired. Outputs: channel_state=8; irq_abort pulse. Side effects: fault_status updated. Error cases: .
SSOT ref: workflow_todos.rtl-gen[19].
Owner: pl330_target in rtl/pl330_target.sv via workflow_todos.owner.
SSOT item context: id=RTL_FM_TX_FM_FAULT.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL samples the transaction only under the approved preconditions
  - All listed outputs are driven with machine-checkable behavior or SSOT-approved status/error mapping
  - All side effects and error cases have observable state, status, or handoff evidence
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[19]
  - Primary implementation evidence is in rtl/pl330_target.sv
  - Semantic source_refs covered: function_model.transactions.FM_FAULT, function_model.transactions[8]
- SSOT refs: function_model.transactions.FM_FAULT, function_model.transactions[8], workflow_todos.rtl-gen[19]

### RTL-0047: Implement cycle_model handshake rule 0

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[20]
- Detail: rule=req_valid payload remains stable until req_ready is sampled asserted on control_data.
SSOT ref: workflow_todos.rtl-gen[20].
Owner: pl330_target in rtl/pl330_target.sv via workflow_todos.owner.
SSOT item context: id=RTL_CYCLE_handshake_rules_ITEM_0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL timing/handshake behavior follows this cycle_model entry
  - Signals remain stable or advance only under the approved protocol phase
  - The behavior is visible to waveform/sim-debug or scoreboard checks
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[20]
  - Primary implementation evidence is in rtl/pl330_target.sv
  - Semantic source_refs covered: cycle_model.handshake_rules[0]
- SSOT refs: cycle_model.handshake_rules[0], workflow_todos.rtl-gen[20]

### RTL-0048: Implement cycle_model handshake rule 1

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[21]
- Detail: rule=rsp_valid payload remains stable until rsp_ready is sampled asserted on control_data.
SSOT ref: workflow_todos.rtl-gen[21].
Owner: pl330_target in rtl/pl330_target.sv via workflow_todos.owner.
SSOT item context: id=RTL_CYCLE_handshake_rules_1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL timing/handshake behavior follows this cycle_model entry
  - Signals remain stable or advance only under the approved protocol phase
  - The behavior is visible to waveform/sim-debug or scoreboard checks
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[21]
  - Primary implementation evidence is in rtl/pl330_target.sv
  - Semantic source_refs covered: cycle_model.handshake_rules[1]
- SSOT refs: cycle_model.handshake_rules[1], workflow_todos.rtl-gen[21]

### RTL-0049: Implement cycle_model pipeline stage 0

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[22]
- Detail: action=Accept legal request/command/packet/control work under declared handshake rules.
SSOT ref: workflow_todos.rtl-gen[22].
Owner: pl330_target in rtl/pl330_target.sv via workflow_todos.owner.
SSOT item context: id=RTL_CYCLE_pipeline_ITEM_0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL timing/handshake behavior follows this cycle_model entry
  - Signals remain stable or advance only under the approved protocol phase
  - The behavior is visible to waveform/sim-debug or scoreboard checks
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[22]
  - Primary implementation evidence is in rtl/pl330_target.sv
  - Semantic source_refs covered: cycle_model.pipeline[0]
- SSOT refs: cycle_model.pipeline[0], workflow_todos.rtl-gen[22]

### RTL-0050: Implement cycle_model pipeline stage 1

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[23]
- Detail: action=Evaluate function_model transaction and update only declared state.
SSOT ref: workflow_todos.rtl-gen[23].
Owner: pl330_target in rtl/pl330_target.sv via workflow_todos.owner.
SSOT item context: id=RTL_CYCLE_pipeline_1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL timing/handshake behavior follows this cycle_model entry
  - Signals remain stable or advance only under the approved protocol phase
  - The behavior is visible to waveform/sim-debug or scoreboard checks
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[23]
  - Primary implementation evidence is in rtl/pl330_target.sv
  - Semantic source_refs covered: cycle_model.pipeline[1]
- SSOT refs: cycle_model.pipeline[1], workflow_todos.rtl-gen[23]

### RTL-0051: Implement cycle_model pipeline stage 2

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[24]
- Detail: action=Publish response/status/output/debug event and hold it stable until accepted.
SSOT ref: workflow_todos.rtl-gen[24].
Owner: pl330_target in rtl/pl330_target.sv via workflow_todos.owner.
SSOT item context: id=RTL_CYCLE_pipeline_2.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL timing/handshake behavior follows this cycle_model entry
  - Signals remain stable or advance only under the approved protocol phase
  - The behavior is visible to waveform/sim-debug or scoreboard checks
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisf
... <truncated 48366 chars>