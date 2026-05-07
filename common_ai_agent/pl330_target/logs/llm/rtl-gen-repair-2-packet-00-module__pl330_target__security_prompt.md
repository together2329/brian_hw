RTL-GEN PACKET MODE for pl330_target. Packet attempt 2.

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

Current packet: module__pl330_target__security
kind: module
work queue: 1/1 active packets (7 closed packets skipped from 30 total)
batch limit: 1; deferred active packets after this batch: 22
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
        "reason": "83 static-evidence-required task(s) still lack DUT RTL evidence.",
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
        "reason": "204 required non-closure TODO(s) remain open.",
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
    "open_required_todos": 205,
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
      "llm_actionable_open_count": 3,
      "open_required_count": 3,
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "packet_id": "module__pl330_target__security",
      "required_count": 4,
      "status_counts": {
        "open": 3,
        "pass": 1
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
      "llm_actionable_open_count": 3,
      "open_required_count": 3,
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "packet_id": "module__pl330_target__workflow_todo_01",
      "required_count": 48,
      "status_counts": {
        "open": 3,
        "pass": 45
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
    "llm_actionable_packets": 23,
    "llm_actionable_tasks": 199,
    "max_packet_required_tasks": 48,
    "module_packets": 28,
    "next_llm_packets": [
      "module__pl330_target__security",
      "module__pl330_target__workflow_todo_01",
      "module__pl330_target_apb_regs",
      "module__pl330_target_axi",
      "module__pl330_target_engine",
      "module__pl330_target_icache",
      "module__pl330_target_lsq",
      "module__pl330_target_merge_buffer"
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

    localparam logic [3:0] RESET_SETTLE_MAX = 4'hf;

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

    wire                   link_ready_w;
    wire                   accept_req_w;
    wire                   consume_rsp_w;
    wire                   reset_settle_done_w;
    wire [DATA_WIDTH-1:0]  flow_increment_w;
    wire [DATA_WIDTH-1:0]  response_mix_w;

    assign flow_increment_w    = {{(DATA_WIDTH-1){1'b0}}, 1'b1};
    assign link_ready_w        = link_ready_q & (~reset_fault_q);
    assign accept_req_w        = req_valid & req_ready;
    assign consume_rsp_w       = rsp_valid & rsp_ready;
    assign reset_settle_done_w = (reset_settle_q == RESET_SETTLE_MAX);
    assign response_mix_w      = req_data ^ flow_count_q ^ {DATA_WIDTH{aux_activity_sync2_q}};

    assign req_ready = link_ready_w & (~pending_q);
    assign rsp_valid = pending_q;
    assign rsp_data  = rsp_data_q;
    assign error     = reset_fault_q | protocol_error_q | (req_valid & (~link_ready_w));

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
            link_ready_q     <= 1'b0;
            reset_settle_q   <= 4'h0;
            reset_fault_q    <= 1'b0;
            protocol_error_q <= 1'b0;
            pending_q        <= 1'b0;
            rsp_data_q       <= {DATA_WIDTH{1'b0}};
            flow_count_q     <= {DATA_WIDTH{1'b0}};
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

            if (accept_req_w) begin
                pending_q    <= 1'b1;
                rsp_data_q   <= response_mix_w;
                flow_count_q <= flow_count_q + flow_increment_w;
            end else if (consume_rsp_w) begin
                pending_q <= 1'b0;
            end
        end
    end

endmodule

`default_nettype wire


Current packet JSON (rtl/authoring_packets/module__pl330_target__security.json):
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
      "index": 6,
      "key": "security",
      "module_task_count": 79,
      "rule": "Owner module pl330_target is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.",
      "section": "security",
      "section_chunk_count": 1,
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
    "llm_actionable_open_count": 3,
    "open_required_count": 3,
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
  "packet_id": "module__pl330_target__security",
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
      "security.assets": 4
    },
    "module_slice": {
      "count": 9,
      "enabled": true,
      "index": 6,
      "key": "security",
      "module_task_count": 79,
      "rule": "Owner module pl330_target is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.",
      "section": "security",
      "section_chunk_count": 1,
      "section_chunk_index": 1,
      "task_limit": 48
    },
    "open_required_count": 3,
    "required_count": 4,
    "source_refs": [
      "security.assets.asset_0",
      "security.assets.asset_1",
      "security.assets.asset_2",
      "security.assets.asset_3"
    ],
    "status_counts": {
      "open": 3,
      "pass": 1
    },
    "task_count": 4
  },
  "tasks": [
    {
      "category": "security.assets",
      "content": "Implement security item asset_0",
      "criteria": [
        "RTL owner/evidence is named for this SSOT item",
        "Behavior is not represented only by comments or TB code",
        "Downstream verification can observe or justify the item",
        "Traceability keeps source_ref security.assets.asset_0",
        "Primary implementation evidence is in rtl/pl330_target.sv"
      ],
      "detail": "This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.\nSSOT ref: security.assets.asset_0.\nOwner: pl330_target in rtl/pl330_target.sv via top_fallback.\nSSOT item context: value=Secure APB register space (sprdata/spwdata).",
      "evidence_terms": [],
      "id": "RTL-0247",
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "priority": "high",
      "required": true,
      "source_ref": "security.assets.asset_0",
      "ssot_context": {
        "value": "Secure APB register space (sprdata/spwdata)"
      },
      "ssot_refs": [
        "security.assets.asset_0"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 5,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.",
        "required": true,
        "status": "pass"
      }
    },
    {
      "category": "security.assets",
      "content": "Implement security item asset_1",
      "criteria": [
        "RTL owner/evidence is named for this SSOT item",
        "Behavior is not represented only by comments or TB code",
        "Downstream verification can observe or justify the item",
        "Traceability keeps source_ref security.assets.asset_1",
        "Primary implementation evidence is in rtl/pl330_target.sv"
      ],
      "detail": "This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.\nSSOT ref: security.assets.asset_1.\nOwner: pl330_target in rtl/pl330_target.sv via top_fallback.\nSSOT item context: value=Manager non-secure indicator (boot_manager_ns).",
      "evidence_terms": [
        "boot",
        "boot_manager_ns",
        "manager",
        "ns"
      ],
      "id": "RTL-0248",
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "priority": "high",
      "required": true,
      "source_ref": "security.assets.asset_1",
      "ssot_context": {
        "value": "Manager non-secure indicator (boot_manager_ns)"
      },
      "ssot_refs": [
        "security.assets.asset_1"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "boot",
          "boot_manager_ns",
          "manager",
          "ns"
        ],
        "source_scope": "rtl/pl330_target.sv",
        "status": "missing"
      },
      "todo_completion": {
        "criteria_total": 5,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Required RTL static evidence is missing.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "security.assets",
      "content": "Implement security item asset_2",
      "criteria": [
        "RTL owner/evidence is named for this SSOT item",
        "Behavior is not represented only by comments or TB code",
        "Downstream verification can observe or justify the item",
        "Traceability keeps source_ref security.assets.asset_2",
        "Primary implementation evidence is in rtl/pl330_target.sv"
      ],
      "detail": "This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.\nSSOT ref: security.assets.asset_2.\nOwner: pl330_target in rtl/pl330_target.sv via top_fallback.\nSSOT item context: value=Per-IRQ non-secure mapping (boot_irq_ns).",
      "evidence_terms": [
        "boot",
        "boot_irq_ns",
        "irq",
        "ns"
      ],
      "id": "RTL-0249",
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "priority": "high",
      "required": true,
      "source_ref": "security.assets.asset_2",
      "ssot_context": {
        "value": "Per-IRQ non-secure mapping (boot_irq_ns)"
      },
      "ssot_refs": [
        "security.assets.asset_2"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "boot",
          "boot_irq_ns",
          "irq",
          "ns"
        ],
        "source_scope": "rtl/pl330_target.sv",
        "status": "missing"
      },
      "todo_completion": {
        "criteria_total": 5,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Required RTL static evidence is missing.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "security.assets",
      "content": "Implement security item asset_3",
      "criteria": [
        "RTL owner/evidence is named for this SSOT item",
        "Behavior is not represented only by comments or TB code",
        "Downstream verification can observe or justify the item",
        "Traceability keeps source_ref security.assets.asset_3",
        "Primary implementation evidence is in rtl/pl330_target.sv"
      ],
      "detail": "This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.\nSSOT ref: security.assets.asset_3.\nOwner: pl330_target in rtl/pl330_target.sv via top_fallback.\nSSOT item context: value=Per-peripheral non-secure mapping (boot_periph_ns).",
      "evidence_terms": [
        "boot",
        "boot_periph_ns",
        "ns",
        "periph"
      ],
      "id": "RTL-0250",
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "priority": "high",
      "required": true,
      "source_ref": "security.assets.asset_3",
      "ssot_context": {
        "value": "Per-peripheral non-secure mapping (boot_periph_ns)"
      },
      "ssot_refs": [
        "security.assets.asset_3"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "boot",
          "boot_periph_ns",
          "ns",
          "periph"
        ],
        "source_scope": "rtl/pl330_target.sv",
        "status": "missing"
      },
      "todo_completion": {
        "criteria_total": 5,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Required RTL static evidence is missing.",
        "required": true,
        "status": "open"
      }
    }
  ],
  "todo_plan_sha256": "67f1ff9bf1c0231e8ac6b228f14bf8866bb926d7596a6c36deeabfbcb3a528fc",
  "top": "pl330_target",
  "type": "rtl_authoring_packet"
}


Current packet Markdown (rtl/authoring_packets/module__pl330_target__security.md):
# RTL Authoring Packet: module__pl330_target__security

- Kind: module
- Owner module: pl330_target
- Owner file: rtl/pl330_target.sv
- Task count: 4
- Required tasks: 4

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
- LLM-actionable open tasks: 3
- Human-locked open tasks: 0
- Module slice: 6/9 section=security task_limit=48
- Slice rule: Owner module pl330_target is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- Reference scale profile: reports/rtl_reference_profile.json (calibration-only, files=143, modules=210, lines=130568)
- Reference target-scale candidate present; SSOT target_scale is not locked yet
- Connection contract gap: Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.
- SSOT top IO contracts: 11

## Tasks

### RTL-0247: Implement security item asset_0

- Priority: high
- Required: True
- Status: pass
- Category: security.assets
- Source ref: security.assets.asset_0
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.asset_0.
Owner: pl330_target in rtl/pl330_target.sv via top_fallback.
SSOT item context: value=Secure APB register space (sprdata/spwdata).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.asset_0
  - Primary implementation evidence is in rtl/pl330_target.sv
- SSOT refs: security.assets.asset_0

### RTL-0248: Implement security item asset_1

- Priority: high
- Required: True
- Status: open
- Category: security.assets
- Source ref: security.assets.asset_1
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.asset_1.
Owner: pl330_target in rtl/pl330_target.sv via top_fallback.
SSOT item context: value=Manager non-secure indicator (boot_manager_ns).
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.asset_1
  - Primary implementation evidence is in rtl/pl330_target.sv
- SSOT refs: security.assets.asset_1

### RTL-0249: Implement security item asset_2

- Priority: high
- Required: True
- Status: open
- Category: security.assets
- Source ref: security.assets.asset_2
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.asset_2.
Owner: pl330_target in rtl/pl330_target.sv via top_fallback.
SSOT item context: value=Per-IRQ non-secure mapping (boot_irq_ns).
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.asset_2
  - Primary implementation evidence is in rtl/pl330_target.sv
- SSOT refs: security.assets.asset_2

### RTL-0250: Implement security item asset_3

- Priority: high
- Required: True
- Status: open
- Category: security.assets
- Source ref: security.assets.asset_3
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.asset_3.
Owner: pl330_target in rtl/pl330_target.sv via top_fallback.
SSOT item context: value=Per-peripheral non-secure mapping (boot_periph_ns).
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.asset_3
  - Primary implementation evidence is in rtl/pl330_target.sv
- SSOT refs: security.assets.asset_3
