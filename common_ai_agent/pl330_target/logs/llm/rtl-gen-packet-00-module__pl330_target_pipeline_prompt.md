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

Current packet: module__pl330_target_pipeline
kind: module
work queue: 1/1 active packets (9 closed packets skipped from 30 total)
batch limit: 1; deferred active packets after this batch: 20
owner_module: pl330_target_pipeline
owner_file: rtl/pl330_target_pipeline.sv

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
        "reason": "RTL authoring provenance is incomplete: rtl_files_missing_manifest:rtl/pl330_target_apb_regs.sv,rtl/pl330_target_axi.sv,rtl/pl330_target_icache.sv,rtl/pl330_target_lsq.sv,rtl/pl330_target_merge_buffer.sv,rtl/pl330_target_mfifo.sv",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.common_ai_agent_authoring",
        "status": "open",
        "task_id": "RTL-0006"
      },
      {
        "gate_kind": "static_rtl_evidence",
        "owner_module": "pl330_target",
        "reason": "72 static-evidence-required task(s) still lack DUT RTL evidence.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.static_rtl_evidence",
        "status": "open",
        "task_id": "RTL-0007"
      },
      {
        "gate_kind": "owner_logic_structure_evidence",
        "owner_module": "pl330_target",
        "reason": "8 owner logic structure issue(s) remain. pl330_target_pipeline: Behavior-owner module is not declared in its owner file; pl330_target_lsq: Behavior-owner module is not declared in its owner file; pl330_target_mfifo: Behavior-owner module is not declared in its owner file",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.owner_logic_structure_evidence",
        "status": "open",
        "task_id": "RTL-0008"
      },
      {
        "gate_kind": "manifest_hierarchy_integration",
        "owner_module": "pl330_target",
        "reason": "9 manifest hierarchy integration issue(s) remain. pl330_target_engine: SSOT manifest child module is declared but not reachable from the top RTL hierarchy; pl330_target_pipeline: SSOT manifest child module is not declared in listed RTL sources; pl330_target_lsq: SSOT manifest child module is not declared in listed RTL sources",
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
        "reason": "192 required non-closure TODO(s) remain open.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.dynamic_todo_closure",
        "status": "open",
        "task_id": "RTL-0019"
      },
      {
        "gate_kind": "rtl_implementation_depth_evidence",
        "owner_module": "pl330_target",
        "reason": "2 production RTL implementation-depth issue(s) remain. Too few RTL modules contain implementation structure for the SSOT behavior complexity: actual=2 required=9; Too few SSOT behavior-owner modules contain implementation-depth evidence: actual=1 required=9",
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
    "open_required_todos": 193,
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
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__pl330_target_engine.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/pl330_target_engine.sv",
      "owner_module": "pl330_target_engine",
      "packet_id": "module__pl330_target_engine",
      "required_count": 8,
      "status_counts": {
        "pass": 8
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
    "llm_actionable_packets": 21,
    "llm_actionable_tasks": 187,
    "max_packet_required_tasks": 48,
    "module_packets": 28,
    "next_llm_packets": [
      "module__pl330_target_pipeline",
      "module__pl330_target_lsq",
      "module__pl330_target_mfifo__function_model_01",
      "module__pl330_target_mfifo__fsm",
      "module__pl330_target_mfifo__registers",
      "module__pl330_target_mfifo__function_model_02",
      "module__pl330_target_mfifo__test_requirements",
      "module__pl330_target_mfifo__features"
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

Current owner RTL file (rtl/pl330_target_pipeline.sv):
<missing or not authored yet>

Current packet JSON (rtl/authoring_packets/module__pl330_target_pipeline.json):
{
  "context": {
    "connection_contract_gap": {
      "machine_readable_contract_count": 0,
      "reason": "Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.",
      "required_for_profile": true,
      "status": "missing"
    },
    "module_slice": {
      "count": 1,
      "enabled": false,
      "index": 1,
      "key": "all",
      "module_task_count": 13,
      "task_limit": 48
    },
    "owner": {
      "file": "rtl/pl330_target_pipeline.sv",
      "name": "pl330_target_pipeline",
      "refs": [
        "cycle_model",
        "cycle_model.handshake_rules.engine_pipeline",
        "cycle_model.pipeline"
      ],
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
    "reference_profile": null,
    "ssot_connection_contracts": [],
    "ssot_top_io_contracts": [],
    "target_scale": null
  },
  "execution_policy": {
    "blocked_by_locked_truth": [],
    "deferred_human_qa_allowed": true,
    "draft_allowed": true,
    "evidence_closure_allowed": false,
    "human_locked_open_count": 0,
    "integration_signoff_allowed": true,
    "llm_actionable": true,
    "llm_actionable_open_count": 13,
    "open_required_count": 13,
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
  "owner_file": "rtl/pl330_target_pipeline.sv",
  "owner_module": "pl330_target_pipeline",
  "packet_id": "module__pl330_target_pipeline",
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
      "cycle_model.backpressure": 1,
      "cycle_model.clock": 1,
      "cycle_model.handshake_rules": 2,
      "cycle_model.latency": 1,
      "cycle_model.observability": 1,
      "cycle_model.ordering": 4,
      "cycle_model.reset": 1,
      "equivalence.module": 1,
      "workflow_todo.rtl_gen": 1
    },
    "module_slice": {
      "count": 1,
      "enabled": false,
      "index": 1,
      "key": "all",
      "module_task_count": 13,
      "task_limit": 48
    },
    "open_required_count": 13,
    "required_count": 13,
    "source_refs": [
      "workflow_todos.rtl-gen[2]",
      "cycle_model.clock",
      "cycle_model.reset",
      "cycle_model.latency",
      "cycle_model.handshake_rules.req_valid_req_ready",
      "cycle_model.handshake_rules.rsp_valid_rsp_ready",
      "cycle_model.ordering.ordering_rule_0",
      "cycle_model.ordering.ordering_rule_1",
      "cycle_model.ordering.ordering_rule_2",
      "cycle_model.ordering.ordering_rule_3",
      "cycle_model.backpressure.backpressure_rule_0",
      "cycle_model.observability.observability_signal_0",
      "sub_modules.pl330_target_pipeline.module_equivalence"
    ],
    "status_counts": {
      "open": 13
    },
    "task_count": 13
  },
  "tasks": [
    {
      "category": "workflow_todo.rtl_gen",
      "content": "Implement or account for SSOT module slice `pl330_target_pipeline`",
      "criteria": [
        "Owned SSOT refs are implemented in the owner RTL file or explicitly mapped to the top integration module",
        "Module slice has traceability evidence in rtl_todo_plan.json",
        "No function/cycle/register/dataflow/FSM task owned by this slice remains orphaned",
        "SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json",
        "RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets",
        "Traceability keeps source_ref workflow_todos.rtl-gen[2]",
        "Primary implementation evidence is in rtl/pl330_target_pipeline.sv",
        "Semantic source_refs covered: cycle_model"
      ],
      "detail": "name=pl330_target_pipeline\nSSOT ref: workflow_todos.rtl-gen[2].\nOwner: pl330_target_pipeline in rtl/pl330_target_pipeline.sv via workflow_todos.owner.\nSSOT item context: id=RTL_MODULE_PL330_TARGET_PIPELINE.",
      "evidence_terms": [
        "PL330",
        "RTL_MODULE_PL330_TARGET_PIPELINE",
        "TARGET",
        "pl330",
        "pl330_target_pipeline",
        "plan",
        "rtl_todo_plan",
        "target",
        "todo"
      ],
      "id": "RTL-0029",
      "owner_file": "rtl/pl330_target_pipeline.sv",
      "owner_module": "pl330_target_pipeline",
      "priority": "high",
      "required": true,
      "source_ref": "workflow_todos.rtl-gen[2]",
      "ssot_context": {
        "id": "RTL_MODULE_PL330_TARGET_PIPELINE"
      },
      "ssot_refs": [
        "cycle_model",
        "workflow_todos.rtl-gen[2]"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 3,
        "required_terms": [
          "PL330",
          "RTL_MODULE_PL330_TARGET_PIPELINE",
          "TARGET",
          "pl330",
          "pl330_target_pipeline",
          "plan",
          "rtl_todo_plan",
          "target",
          "todo"
        ],
        "source_scope": "rtl/pl330_target_pipeline.sv",
        "status": "missing"
      },
      "todo_completion": {
        "criteria_total": 8,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/pl330_target_pipeline.sv.",
        "required": true,
        "status": "open"
      },
      "workflow_todo": {
        "id": "RTL_MODULE_PL330_TARGET_PIPELINE",
        "source_refs": [
          "cycle_model"
        ],
        "stage": "rtl-gen",
        "user_category": ""
      }
    },
    {
      "category": "cycle_model.clock",
      "content": "Implement cycle-model clock",
      "criteria": [
        "RTL sequential logic uses the SSOT clock/reset phase",
        "Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence",
        "Downstream scoreboard samples the same acceptance/result phase",
        "Traceability keeps source_ref cycle_model.clock",
        "Primary implementation evidence is in rtl/pl330_target_pipeline.sv",
        "cycle_model.clock appears in RTL sample/hold/FSM/ready-valid timing, not only in TB"
      ],
      "detail": "Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.\nSSOT ref: cycle_model.clock.\nOwner: pl330_target_pipeline in rtl/pl330_target_pipeline.sv via cycle_model.\nSSOT item context: value=clk.",
      "evidence_terms": [],
      "id": "RTL-0177",
      "owner_file": "rtl/pl330_target_pipeline.sv",
      "owner_module": "pl330_target_pipeline",
      "priority": "high",
      "required": true,
      "source_ref": "cycle_model.clock",
      "ssot_context": {
        "value": "clk"
      },
      "ssot_refs": [
        "cycle_model.clock"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 6,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/pl330_target_pipeline.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "cycle_model.reset",
      "content": "Implement cycle-model reset",
      "criteria": [
        "RTL sequential logic uses the SSOT clock/reset phase",
        "Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence",
        "Downstream scoreboard samples the same acceptance/result phase",
        "Traceability keeps source_ref cycle_model.reset",
        "Primary implementation evidence is in rtl/pl330_target_pipeline.sv",
        "cycle_model.reset appears in RTL sample/hold/FSM/ready-valid timing, not only in TB"
      ],
      "detail": "Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.\nSSOT ref: cycle_model.reset.\nOwner: pl330_target_pipeline in rtl/pl330_target_pipeline.sv via cycle_model.\nSSOT item context: signal=rst_n.",
      "evidence_terms": [
        "rst",
        "rst_n"
      ],
      "id": "RTL-0178",
      "owner_file": "rtl/pl330_target_pipeline.sv",
      "owner_module": "pl330_target_pipeline",
      "priority": "high",
      "required": true,
      "source_ref": "cycle_model.reset",
      "ssot_context": {
        "signal": "rst_n"
      },
      "ssot_refs": [
        "cycle_model.reset"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 1,
        "required_terms": [
          "rst",
          "rst_n"
        ],
        "source_scope": "rtl/pl330_target_pipeline.sv",
        "status": "missing"
      },
      "todo_completion": {
        "criteria_total": 6,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/pl330_target_pipeline.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "cycle_model.latency",
      "content": "Implement cycle-model latency",
      "criteria": [
        "RTL sequential logic uses the SSOT clock/reset phase",
        "Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence",
        "Downstream scoreboard samples the same acceptance/result phase",
        "Traceability keeps source_ref cycle_model.latency",
        "Primary implementation evidence is in rtl/pl330_target_pipeline.sv",
        "cycle_model.latency appears in RTL sample/hold/FSM/ready-valid timing, not only in TB"
      ],
      "detail": "Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.\nSSOT ref: cycle_model.latency.\nOwner: pl330_target_pipeline in rtl/pl330_target_pipeline.sv via cycle_model.",
      "evidence_terms": [],
      "id": "RTL-0179",
      "owner_file": "rtl/pl330_target_pipeline.sv",
      "owner_module": "pl330_target_pipeline",
      "priority": "high",
      "required": true,
      "source_ref": "cycle_model.latency",
      "ssot_context": {},
      "ssot_refs": [
        "cycle_model.latency"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 6,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/pl330_target_pipeline.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "cycle_model.handshake_rules",
      "content": "Implement handshake rule: req_valid/req_ready",
      "criteria": [
        "RTL contains the control/state/handshake logic for this cycle rule",
        "Rule timing is reflected in sample/hold/ready/valid or FSM behavior",
        "TB scoreboard/coverage can observe the rule at the declared phase",
        "Traceability keeps source_ref cycle_model.handshake_rules.req_valid_req_ready",
        "Primary implementation evidence is in rtl/pl330_target_pipeline.sv",
        "cycle_model.handshake_rules.req_valid_req_ready appears in RTL sample/hold/FSM/ready-valid timing, not only in TB"
      ],
      "detail": "Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.\nSSOT ref: cycle_model.handshake_rules.req_valid_req_ready.\nOwner: pl330_target_pipeline in rtl/pl330_target_pipeline.sv via cycle_model.\nSSOT item context: signal=req_valid/req_ready.",
      "evidence_terms": [
        "ready",
        "req",
        "req_ready",
        "req_valid",
        "valid"
      ],
      "id": "RTL-0180",
      "owner_file": "rtl/pl330_target_pipeline.sv",
      "owner_module": "pl330_target_pipeline",
      "priority": "high",
      "required": true,
      "source_ref": "cycle_model.handshake_rules.req_valid_req_ready",
      "ssot_context": {
        "signal": "req_valid/req_ready"
      },
      "ssot_refs": [
        "cycle_model.handshake_rules.req_valid_req_ready"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "ready",
          "req",
          "req_ready",
          "req_valid",
          "valid"
        ],
        "source_scope": "rtl/pl330_target_pipeline.sv",
        "status": "missing"
      },
      "todo_completion": {
        "criteria_total": 6,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/pl330_target_pipeline.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "cycle_model.handshake_rules",
      "content": "Implement handshake rule: rsp_valid/rsp_ready",
      "criteria": [
        "RTL contains the control/state/handshake logic for this cycle rule",
        "Rule timing is reflected in sample/hold/ready/valid or FSM behavior",
        "TB scoreboard/coverage can observe the rule at the declared phase",
        "Traceability keeps source_ref cycle_model.handshake_rules.rsp_valid_rsp_ready",
        "Primary implementation evidence is in rtl/pl330_target_pipeline.sv",
        "cycle_model.handshake_rules.rsp_valid_rsp_ready appears in RTL sample/hold/FSM/ready-valid timing, not only in TB"
      ],
      "detail": "Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.\nSSOT ref: cycle_model.handshake_rules.rsp_valid_rsp_ready.\nOwner: pl330_target_pipeline in rtl/pl330_target_pipeline.sv via cycle_model.\nSSOT item context: signal=rsp_valid/rsp_ready.",
      "evidence_terms": [
        "ready",
        "rsp",
        "rsp_ready",
        "rsp_valid",
        "valid"
      ],
      "id": "RTL-0181",
      "owner_file": "rtl/pl330_target_pipeline.sv",
      "owner_module": "pl330_target_pipeline",
      "priority": "high",
      "required": true,
      "source_ref": "cycle_model.handshake_rules.rsp_valid_rsp_ready",
      "ssot_context": {
        "signal": "rsp_valid/rsp_ready"
      },
      "ssot_refs": [
        "cycle_model.handshake_rules.rsp_valid_rsp_ready"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "ready",
          "rsp",
          "rsp_ready",
          "rsp_valid",
          "valid"
        ],
        "source_scope": "rtl/pl330_target_pipeline.sv",
        "status": "missing"
      },
      "todo_completion": {
        "criteria_total": 6,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/pl330_target_pipeline.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "cycle_model.ordering",
      "content": "Implement ordering rule: ordering_rule_0",
      "criteria": [
        "RTL contains the control/state/handshake logic for this cycle rule",
        "Rule timing is reflected in sample/hold/ready/valid or FSM behavior",
        "TB scoreboard/coverage can observe the rule at the declared phase",
        "Traceability keeps source_ref cycle_model.ordering.ordering_rule_0",
        "Primary implementation evidence is in rtl/pl330_target_pipeline.sv",
        "cycle_model.ordering.ordering_rule_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB"
      ],
      "detail": "Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.\nSSOT ref: cycle_model.ordering.ordering_rule_0.\nOwner: pl330_target_pipeline in rtl/pl330_target_pipeline.sv via cycle_model.\nSSOT item context: value=Accepted requests update architectural state only on clock edges..",
      "evidence_terms": [],
      "id": "RTL-0185",
      "owner_file": "rtl/pl330_target_pipeline.sv",
      "owner_module": "pl330_target_pipeline",
      "priority": "high",
      "required": true,
      "source_ref": "cycle_model.ordering.ordering_rule_0",
      "ssot_context": {
        "value": "Accepted requests update architectural state only on clock edges."
      },
      "ssot_refs": [
        "cycle_model.ordering.ordering_rule_0"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 6,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/pl330_target_pipeline.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "cycle_model.ordering",
      "content": "Implement ordering rule: ordering_rule_1",
      "criteria": [
        "RTL contains the control/state/handshake logic for this cycle rule",
        "Rule timing is reflected in sample/hold/ready/valid or FSM behavior",
        "TB scoreboard/coverage can observe the rule at the declared phase",
        "Traceability keeps source_ref cycle_model.ordering.ordering_rule_1",
        "Primary implementation evidence is in rtl/pl330_target_pipeline.sv",
        "cycle_model.ordering.ordering_rule_1 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB"
      ],
      "detail": "Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.\nSSOT ref: cycle_model.ordering.ordering_rule_1.\nOwner: pl330_target_pipeline in rtl/pl330_target_pipeline.sv via cycle_model.\nSSOT item context: value=Completion/status/interrupt updates occur after the operation reaches its terminal FSM state..",
      "evidence_terms": [],
      "id": "RTL-0186",
      "owner_file": "rtl/pl330_target_pipeline.sv",
      "owner_module": "pl330_target_pipeline",
      "priority": "high",
      "required": true,
      "source_ref": "cycle_model.ordering.ordering_rule_1",
      "ssot_context": {
        "value": "Completion/status/interrupt updates occur after the operation reaches its terminal FSM state."
      },
      "ssot_refs": [
        "cycle_model.ordering.ordering_rule_1"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 6,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/pl330_target_pipeline.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "cycle_model.ordering",
      "content": "Implement ordering rule: ordering_rule_2",
      "criteria": [
        "RTL contains the control/state/handshake logic for this cycle rule",
        "Rule timing is reflected in sample/hold/ready/valid or FSM behavior",
        "TB scoreboard/coverage can observe the rule at the declared phase",
        "Traceability keeps source_ref cycle_model.ordering.ordering_rule_2",
        "Primary implementation evidence is in rtl/pl330_target_pipeline.sv",
        "cycle_model.ordering.ordering_rule_2 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB"
      ],
      "detail": "Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.\nSSOT ref: cycle_model.ordering.ordering_rule_2.\nOwner: pl330_target_pipeline in rtl/pl330_target_pipeline.sv via cycle_model.\nSSOT item context: value=Backpressure stalls the active handshake stage without corrupting stored state..",
      "evidence_terms": [],
      "id": "RTL-0187",
      "owner_file": "rtl/pl330_target_pipeline.sv",
      "owner_module": "pl330_target_pipeline",
      "priority": "high",
      "required": true,
      "source_ref": "cycle_model.ordering.ordering_rule_2",
      "ssot_context": {
        "value": "Backpressure stalls the active handshake stage without corrupting stored state."
      },
      "ssot_refs": [
        "cycle_model.ordering.ordering_rule_2"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 6,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/pl330_target_pipeline.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "cycle_model.ordering",
      "content": "Implement ordering rule: ordering_rule_3",
      "criteria": [
        "RTL contains the control/state/handshake logic for this cycle rule",
        "Rule timing is reflected in sample/hold/ready/valid or FSM behavior",
        "TB scoreboard/coverage can observe the rule at the declared phase",
        "Traceability keeps source_ref cycle_model.ordering.ordering_rule_3",
        "Primary implementation evidence is in rtl/pl330_target_pipeline.sv",
        "cycle_model.ordering.ordering_rule_3 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB"
      ],
      "detail": "Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.\nSSOT ref: cycle_model.ordering.ordering_rule_3.\nOwner: pl330_target_pipeline in rtl/pl330_target_pipeline.sv via cycle_model.\nSSOT item context: value=Read/dataflow stages must precede dependent write/output stages where declared in dataflow..",
      "evidence_terms": [],
      "id": "RTL-0188",
      "owner_file": "rtl/pl330_target_pipeline.sv",
      "owner_module": "pl330_target_pipeline",
      "priority": "high",
      "required": true,
      "source_ref": "cycle_model.ordering.ordering_rule_3",
      "ssot_context": {
        "value": "Read/dataflow stages must precede dependent write/output stages where declared in dataflow."
      },
      "ssot_refs": [
        "cycle_model.ordering.ordering_rule_3"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 6,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/pl330_target_pipeline.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "cycle_model.backpressure",
      "content": "Implement backpressure rule: backpressure_rule_0",
      "criteria": [
        "RTL contains the control/state/handshake logic for this cycle rule",
        "Rule timing is reflected in sample/hold/ready/valid or FSM behavior",
        "TB scoreboard/coverage can observe the rule at the declared phase",
        "Traceability keeps source_ref cycle_model.backpressure.backpressure_rule_0",
        "Primary implementation evidence is in rtl/pl330_target_pipeline.sv",
        "cycle_model.backpressure.backpressure_rule_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB"
      ],
      "detail": "Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.\nSSOT ref: cycle_model.backpressure.backpressure_rule_0.\nOwner: pl330_target_pipeline in rtl/pl330_target_pipeline.sv via cycle_model.\nSSOT item context: value=Ready/valid deassertion stalls only the affected interface stage; payload and route/control state remain stable..",
      "evidence_terms": [],
      "id": "RTL-0189",
      "owner_file": "rtl/pl330_target_pipeline.sv",
      "owner_module": "pl330_target_pipeline",
      "priority": "high",
      "required": true,
      "source_ref": "cycle_model.backpressure.backpressure_rule_0",
      "ssot_context": {
        "value": "Ready/valid deassertion stalls only the affected interface stage; payload and route/control state remain stable."
      },
      "ssot_refs": [
        "cycle_model.backpressure.backpressure_rule_0"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 6,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/pl330_target_pipeline.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "cycle_model.observability",
      "content": "Implement observability signal: observability_signal_0",
      "criteria": [
        "RTL contains the control/state/handshake logic for this cycle rule",
        "Rule timing is reflected in sample/hold/ready/valid or FSM behavior",
        "TB scoreboard/coverage can observe the rule at the declared phase",
        "Traceability keeps source_ref cycle_model.observability.observability_signal_0",
        "Primary implementation evidence is in rtl/pl330_target_pipeline.sv",
        "cycle_model.observability.observability_signal_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB"
      ],
      "detail": "Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.\nSSOT ref: cycle_model.observability.observability_signal_0.\nOwner: pl330_target_pipeline in rtl/pl330_target_pipeline.sv via cycle_model.\nSSOT item context: value=Every function_model transaction maps to at least one cycle_model stage and one test_requirements scenario..",
      "evidence_terms": [
        "Every",
        "at",
        "least",
        "maps",
        "one",
        "scenario",
        "stage"
      ],
      "id": "RTL-0190",
      "owner_file": "rtl/pl330_target_pipeline.sv",
      "owner_module": "pl330_target_pipeline",
      "priority": "high",
      "required": true,
      "source_ref": "cycle_model.observability.observability_signal_0",
      "ssot_context": {
        "value": "Every function_model transaction maps to at least one cycle_model stage and one test_requirements scenario."
      },
      "ssot_refs": [
        "cycle_model.observability.observability_signal_0"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 1,
        "required_terms": [
          "Every",
          "at",
          "least",
          "maps",
          "one",
          "scenario",
          "stage"
        ],
        "source_scope": "rtl/pl330_target_pipeline.sv",
        "status": "missing"
      },
      "todo_completion": {
        "criteria_total": 6,
        "evidence_basis": [
          "rtl_todo_plan.json task criteria",
          "rtl_traceability.json source_ref mapping",
          "owner RTL file/module declaration evidence",
          "static RTL evidence audit when evidence_terms are required"
        ],
        "reason": "Owner RTL file is missing: rtl/pl330_target_pipeline.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "equivalence.module",
      "content": "Prove module pl330_target_pipeline is functionally equivalent to FL",
      "criteria": [
        "verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module",
        "cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff",
        "scoreboard row fl_expected.model_api is FunctionalModel.apply",
        "scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data",
        "Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong",
        "Traceability keeps source_ref sub_modules.pl330_target_pipeline.module_equivalence",
        "Primary implementation evidence is in rtl/pl330_target_pipeline.sv"
      ],
      "detail": "This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.\nSSOT ref: sub_modules.pl330_target_pipeline.module_equivalence.\nOwner: pl330_target_pipeline in rtl/pl330_target_pipeline.sv via module_equivalence.",
      "evidence_terms": [],
      "id": "RTL-0262",
      "owner_file": "rtl/pl330_target_pipeline.sv",
      "owner_module": "pl330_target_pipeline",
      "priority": "high",
      "required": true,
      "source_ref": "sub_modules.pl330_target_pipeline.module_equivalence",
      "ssot_context": {},
      "ssot_refs": [
        "sub_modules.pl330_target_pipeline.module_equivalence"
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
        "reason": "Owner RTL file is missing: rtl/pl330_target_pipeline.sv.",
        "required": true,
        "status": "open"
      }
    }
  ],
  "todo_plan_sha256": "67f1ff9bf1c0231e8ac6b228f14bf8866bb926d7596a6c36deeabfbcb3a528fc",
  "top": "pl330_target",
  "type": "rtl_authoring_packet"
}


Current packet Markdown (rtl/authoring_packets/module__pl330_target_pipeline.md):
# RTL Authoring Packet: module__pl330_target_pipeline

- Kind: module
- Owner module: pl330_target_pipeline
- Owner file: rtl/pl330_target_pipeline.sv
- Task count: 13
- Required tasks: 13

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
- Integration signoff allowed: True
- LLM-actionable open tasks: 13
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.handshake_rules.engine_pipeline, cycle_model.pipeline
- Connection contract gap: Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.

## Tasks

### RTL-0029: Implement or account for SSOT module slice `pl330_target_pipeline`

- Priority: high
- Required: True
- Status: open
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[2]
- Detail: name=pl330_target_pipeline
SSOT ref: workflow_todos.rtl-gen[2].
Owner: pl330_target_pipeline in rtl/pl330_target_pipeline.sv via workflow_todos.owner.
SSOT item context: id=RTL_MODULE_PL330_TARGET_PIPELINE.
- Current reason: Owner RTL file is missing: rtl/pl330_target_pipeline.sv.
- Criteria:
  - Owned SSOT refs are implemented in the owner RTL file or explicitly mapped to the top integration module
  - Module slice has traceability evidence in rtl_todo_plan.json
  - No function/cycle/register/dataflow/FSM task owned by this slice remains orphaned
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[2]
  - Primary implementation evidence is in rtl/pl330_target_pipeline.sv
  - Semantic source_refs covered: cycle_model
- SSOT refs: cycle_model, workflow_todos.rtl-gen[2]

### RTL-0177: Implement cycle-model clock

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.clock
- Source ref: cycle_model.clock
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.clock.
Owner: pl330_target_pipeline in rtl/pl330_target_pipeline.sv via cycle_model.
SSOT item context: value=clk.
- Current reason: Owner RTL file is missing: rtl/pl330_target_pipeline.sv.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.clock
  - Primary implementation evidence is in rtl/pl330_target_pipeline.sv
  - cycle_model.clock appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.clock

### RTL-0178: Implement cycle-model reset

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.reset
- Source ref: cycle_model.reset
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.reset.
Owner: pl330_target_pipeline in rtl/pl330_target_pipeline.sv via cycle_model.
SSOT item context: signal=rst_n.
- Current reason: Owner RTL file is missing: rtl/pl330_target_pipeline.sv.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.reset
  - Primary implementation evidence is in rtl/pl330_target_pipeline.sv
  - cycle_model.reset appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.reset

### RTL-0179: Implement cycle-model latency

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.latency
- Source ref: cycle_model.latency
- Detail: Clock/reset/latency semantics must be realized in sequential RTL and observable by the TB where applicable.
SSOT ref: cycle_model.latency.
Owner: pl330_target_pipeline in rtl/pl330_target_pipeline.sv via cycle_model.
- Current reason: Owner RTL file is missing: rtl/pl330_target_pipeline.sv.
- Criteria:
  - RTL sequential logic uses the SSOT clock/reset phase
  - Latency/phase behavior is encoded in flops, counters, FSM, or explicit zero-latency evidence
  - Downstream scoreboard samples the same acceptance/result phase
  - Traceability keeps source_ref cycle_model.latency
  - Primary implementation evidence is in rtl/pl330_target_pipeline.sv
  - cycle_model.latency appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.latency

### RTL-0180: Implement handshake rule: req_valid/req_ready

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.req_valid_req_ready
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.req_valid_req_ready.
Owner: pl330_target_pipeline in rtl/pl330_target_pipeline.sv via cycle_model.
SSOT item context: signal=req_valid/req_ready.
- Current reason: Owner RTL file is missing: rtl/pl330_target_pipeline.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.req_valid_req_ready
  - Primary implementation evidence is in rtl/pl330_target_pipeline.sv
  - cycle_model.handshake_rules.req_valid_req_ready appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.req_valid_req_ready

### RTL-0181: Implement handshake rule: rsp_valid/rsp_ready

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.rsp_valid_rsp_ready
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.rsp_valid_rsp_ready.
Owner: pl330_target_pipeline in rtl/pl330_target_pipeline.sv via cycle_model.
SSOT item context: signal=rsp_valid/rsp_ready.
- Current reason: Owner RTL file is missing: rtl/pl330_target_pipeline.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.rsp_valid_rsp_ready
  - Primary implementation evidence is in rtl/pl330_target_pipeline.sv
  - cycle_model.handshake_rules.rsp_valid_rsp_ready appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.rsp_valid_rsp_ready

### RTL-0185: Implement ordering rule: ordering_rule_0

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_0.
Owner: pl330_target_pipeline in rtl/pl330_target_pipeline.sv via cycle_model.
SSOT item context: value=Accepted requests update architectural state only on clock edges..
- Current reason: Owner RTL file is missing: rtl/pl330_target_pipeline.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_0
  - Primary implementation evidence is in rtl/pl330_target_pipeline.sv
  - cycle_model.ordering.ordering_rule_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_0

### RTL-0186: Implement ordering rule: ordering_rule_1

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_1
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_1.
Owner: pl330_target_pipeline in rtl/pl330_target_pipeline.sv via cycle_model.
SSOT item context: value=Completion/status/interrupt updates occur after the operation reaches its terminal FSM state..
- Current reason: Owner RTL file is missing: rtl/pl330_target_pipeline.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_1
  - Primary implementation evidence is in rtl/pl330_target_pipeline.sv
  - cycle_model.ordering.ordering_rule_1 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_1

### RTL-0187: Implement ordering rule: ordering_rule_2

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_2
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_2.
Owner: pl330_target_pipeline in rtl/pl330_target_pipeline.sv via cycle_model.
SSOT item context: value=Backpressure stalls the active handshake stage without corrupting stored state..
- Current reason: Owner RTL file is missing: rtl/pl330_target_pipeline.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_2
  - Primary implementation evidence is in rtl/pl330_target_pipeline.sv
  - cycle_model.ordering.ordering_rule_2 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_2

### RTL-0188: Implement ordering rule: ordering_rule_3

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_3
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_3.
Owner: pl330_target_pipeline in rtl/pl330_target_pipeline.sv via cycle_model.
SSOT item context: value=Read/dataflow stages must precede dependent write/output stages where declared in dataflow..
- Current reason: Owner RTL file is missing: rtl/pl330_target_pipeline.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_3
  - Primary implementation evidence is in rtl/pl330_target_pipeline.sv
  - cycle_model.ordering.ordering_rule_3 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_3

### RTL-0189: Implement backpressure rule: backpressure_rule_0

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.backpressure
- Source ref: cycle_model.backpressure.backpressure_rule_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.backpressure.backpressure_rule_0.
Owner: pl330_target_pipeline in rtl/pl330_target_pipeline.sv via cycle_model.
SSOT item context: value=Ready/valid deassertion stalls only the affected interface stage; payload and route/control state remain stable..
- Current reason: Owner RTL file is missing: rtl/pl330_target_pipeline.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.backpressure.backpressure_rule_0
  - Primary implementation evidence is in rtl/pl330_target_pipeline.sv
  - cycle_model.backpressure.backpressure_rule_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.backpressure.backpressure_rule_0

### RTL-0190: Implement observability signal: observability_signal_0

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.observability
- Source ref: cycle_model.observability.observability_signal_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.observability.observability_signal_0.
Owner: pl330_target_pipeline in rtl/pl330_target_pipeline.sv via cycle_model.
SSOT item context: value=Every function_model transaction maps to at least one cycle_model stage and one test_requirements scenario..
- Current reason: Owner RTL file is missing: rtl/pl330_target_pipeline.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.observability.observability_signal_0
  - Primary implementation evidence is in rtl/pl330_target_pipeline.sv
  - cycle_model.observability.observability_signal_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.observability.observability_signal_0

### RTL-0262: Prove module pl330_target_pipeline is functionally equivalent to FL

- Priority: high
- Required: True
- Status: open
- Category: equivalence.module
- Source ref: sub_modules.pl330_target_pipeline.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.pl330_target_pipeline.module_equivalence.
Owner: pl330_target_pipeline in rtl/pl330_target_pipeline.sv via module_equivalence.
- Current reason: Owner RTL file is missing: rtl/pl330_target_pipeline.sv.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.pl330_target_pipeline.module_equivalence
  - Primary implementation evidence is in rtl/pl330_target_pipeline.sv
- SSOT refs: sub_modules.pl330_target_pipeline.module_equivalence
