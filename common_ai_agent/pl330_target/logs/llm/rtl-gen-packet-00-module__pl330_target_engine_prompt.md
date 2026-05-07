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

Current packet: module__pl330_target_engine
kind: module
work queue: 1/1 active packets (8 closed packets skipped from 30 total)
batch limit: 1; deferred active packets after this batch: 21
owner_module: pl330_target_engine
owner_file: rtl/pl330_target_engine.sv

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
    "llm_actionable_packets": 22,
    "llm_actionable_tasks": 195,
    "max_packet_required_tasks": 48,
    "module_packets": 28,
    "next_llm_packets": [
      "module__pl330_target_engine",
      "module__pl330_target_pipeline",
      "module__pl330_target_lsq",
      "module__pl330_target_mfifo__function_model_01",
      "module__pl330_target_mfifo__fsm",
      "module__pl330_target_mfifo__registers",
      "module__pl330_target_mfifo__function_model_02",
      "module__pl330_target_mfifo__test_requirements"
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

Current owner RTL file (rtl/pl330_target_engine.sv):
<missing or not authored yet>

Current packet JSON (rtl/authoring_packets/module__pl330_target_engine.json):
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
      "module_task_count": 8,
      "task_limit": 48
    },
    "owner": {
      "file": "rtl/pl330_target_engine.sv",
      "name": "pl330_target_engine",
      "refs": [
        "cycle_model.pipeline",
        "fsm.engine",
        "function_model.transactions.decode",
        "function_model.transactions.execute",
        "function_model.transactions.fetch"
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
    "llm_actionable_open_count": 8,
    "open_required_count": 8,
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
  "owner_file": "rtl/pl330_target_engine.sv",
  "owner_module": "pl330_target_engine",
  "packet_id": "module__pl330_target_engine",
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
      "cycle_model.pipeline": 3,
      "equivalence.module": 1,
      "function_model.invariant": 3,
      "workflow_todo.rtl_gen": 1
    },
    "module_slice": {
      "count": 1,
      "enabled": false,
      "index": 1,
      "key": "all",
      "module_task_count": 8,
      "task_limit": 48
    },
    "open_required_count": 8,
    "required_count": 8,
    "source_refs": [
      "workflow_todos.rtl-gen[1]",
      "function_model.invariants.invariant_0",
      "function_model.invariants.invariant_1",
      "function_model.invariants.invariant_3",
      "cycle_model.pipeline.S0_ACCEPT",
      "cycle_model.pipeline.S1_EVALUATE",
      "cycle_model.pipeline.S2_OBSERVE",
      "sub_modules.pl330_target_engine.module_equivalence"
    ],
    "status_counts": {
      "open": 8
    },
    "task_count": 8
  },
  "tasks": [
    {
      "category": "workflow_todo.rtl_gen",
      "content": "Implement or account for SSOT module slice `pl330_target_engine`",
      "criteria": [
        "Owned SSOT refs are implemented in the owner RTL file or explicitly mapped to the top integration module",
        "Module slice has traceability evidence in rtl_todo_plan.json",
        "No function/cycle/register/dataflow/FSM task owned by this slice remains orphaned",
        "SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json",
        "RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets",
        "Traceability keeps source_ref workflow_todos.rtl-gen[1]",
        "Primary implementation evidence is in rtl/pl330_target_engine.sv",
        "Semantic source_refs covered: sub_modules[0]"
      ],
      "detail": "name=pl330_target_engine\nSSOT ref: workflow_todos.rtl-gen[1].\nOwner: pl330_target_engine in rtl/pl330_target_engine.sv via workflow_todos.owner.\nSSOT item context: id=RTL_MODULE_PL330_TARGET_ENGINE.",
      "evidence_terms": [
        "ENGINE",
        "PL330",
        "RTL_MODULE_PL330_TARGET_ENGINE",
        "TARGET",
        "engine",
        "modules",
        "pl330",
        "pl330_target_engine",
        "plan",
        "rtl_todo_plan",
        "sub",
        "sub_modules",
        "target",
        "todo"
      ],
      "id": "RTL-0028",
      "owner_file": "rtl/pl330_target_engine.sv",
      "owner_module": "pl330_target_engine",
      "priority": "high",
      "required": true,
      "source_ref": "workflow_todos.rtl-gen[1]",
      "ssot_context": {
        "id": "RTL_MODULE_PL330_TARGET_ENGINE"
      },
      "ssot_refs": [
        "sub_modules[0]",
        "workflow_todos.rtl-gen[1]"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 3,
        "required_terms": [
          "ENGINE",
          "PL330",
          "RTL_MODULE_PL330_TARGET_ENGINE",
          "TARGET",
          "engine",
          "modules",
          "pl330",
          "pl330_target_engine",
          "plan",
          "rtl_todo_plan",
          "sub",
          "sub_modules",
          "target",
          "todo"
        ],
        "source_scope": "rtl/pl330_target_engine.sv",
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
        "reason": "Owner RTL file is missing: rtl/pl330_target_engine.sv.",
        "required": true,
        "status": "open"
      },
      "workflow_todo": {
        "id": "RTL_MODULE_PL330_TARGET_ENGINE",
        "source_refs": [
          "sub_modules[0]"
        ],
        "stage": "rtl-gen",
        "user_category": ""
      }
    },
    {
      "category": "function_model.invariant",
      "content": "Preserve FL invariant invariant_0",
      "criteria": [
        "RTL behavior cannot violate the invariant in normal operation",
        "If the invariant is verification-only, the SSOT names that evidence owner",
        "Coverage/equivalence references this invariant when observable",
        "Traceability keeps source_ref function_model.invariants.invariant_0",
        "Primary implementation evidence is in rtl/pl330_target_engine.sv"
      ],
      "detail": "Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.\nSSOT ref: function_model.invariants.invariant_0.\nOwner: pl330_target_engine in rtl/pl330_target_engine.sv via control_owner_fallback.\nSSOT item context: value=outstanding_reads >= 0 && outstanding_reads <= 2*NUM_CHANNELS.",
      "evidence_terms": [
        "CHANNELS",
        "NUM",
        "NUM_CHANNELS",
        "outstanding",
        "outstanding_reads",
        "reads"
      ],
      "id": "RTL-0172",
      "owner_file": "rtl/pl330_target_engine.sv",
      "owner_module": "pl330_target_engine",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.invariants.invariant_0",
      "ssot_context": {
        "value": "outstanding_reads >= 0 && outstanding_reads <= 2*NUM_CHANNELS"
      },
      "ssot_refs": [
        "function_model.invariants.invariant_0"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "CHANNELS",
          "NUM",
          "NUM_CHANNELS",
          "outstanding",
          "outstanding_reads",
          "reads"
        ],
        "source_scope": "rtl/pl330_target_engine.sv",
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
        "reason": "Owner RTL file is missing: rtl/pl330_target_engine.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "function_model.invariant",
      "content": "Preserve FL invariant invariant_1",
      "criteria": [
        "RTL behavior cannot violate the invariant in normal operation",
        "If the invariant is verification-only, the SSOT names that evidence owner",
        "Coverage/equivalence references this invariant when observable",
        "Traceability keeps source_ref function_model.invariants.invariant_1",
        "Primary implementation evidence is in rtl/pl330_target_engine.sv"
      ],
      "detail": "Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.\nSSOT ref: function_model.invariants.invariant_1.\nOwner: pl330_target_engine in rtl/pl330_target_engine.sv via control_owner_fallback.\nSSOT item context: value=outstanding_writes >= 0 && outstanding_writes <= 2*NUM_CHANNELS.",
      "evidence_terms": [
        "CHANNELS",
        "NUM",
        "NUM_CHANNELS",
        "outstanding",
        "outstanding_writes",
        "writes"
      ],
      "id": "RTL-0173",
      "owner_file": "rtl/pl330_target_engine.sv",
      "owner_module": "pl330_target_engine",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.invariants.invariant_1",
      "ssot_context": {
        "value": "outstanding_writes >= 0 && outstanding_writes <= 2*NUM_CHANNELS"
      },
      "ssot_refs": [
        "function_model.invariants.invariant_1"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "CHANNELS",
          "NUM",
          "NUM_CHANNELS",
          "outstanding",
          "outstanding_writes",
          "writes"
        ],
        "source_scope": "rtl/pl330_target_engine.sv",
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
        "reason": "Owner RTL file is missing: rtl/pl330_target_engine.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "function_model.invariant",
      "content": "Preserve FL invariant invariant_3",
      "criteria": [
        "RTL behavior cannot violate the invariant in normal operation",
        "If the invariant is verification-only, the SSOT names that evidence owner",
        "Coverage/equivalence references this invariant when observable",
        "Traceability keeps source_ref function_model.invariants.invariant_3",
        "Primary implementation evidence is in rtl/pl330_target_engine.sv"
      ],
      "detail": "Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.\nSSOT ref: function_model.invariants.invariant_3.\nOwner: pl330_target_engine in rtl/pl330_target_engine.sv via control_owner_fallback.\nSSOT item context: value=channel_state != 1 -> outstanding_reads == 0 && outstanding_writes == 0.",
      "evidence_terms": [
        "channel",
        "channel_state",
        "outstanding",
        "outstanding_reads",
        "outstanding_writes",
        "reads",
        "writes"
      ],
      "id": "RTL-0175",
      "owner_file": "rtl/pl330_target_engine.sv",
      "owner_module": "pl330_target_engine",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.invariants.invariant_3",
      "ssot_context": {
        "value": "channel_state != 1 -> outstanding_reads == 0 && outstanding_writes == 0"
      },
      "ssot_refs": [
        "function_model.invariants.invariant_3"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "channel",
          "channel_state",
          "outstanding",
          "outstanding_reads",
          "outstanding_writes",
          "reads",
          "writes"
        ],
        "source_scope": "rtl/pl330_target_engine.sv",
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
        "reason": "Owner RTL file is missing: rtl/pl330_target_engine.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "cycle_model.pipeline",
      "content": "Implement pipeline stage: S0_ACCEPT",
      "criteria": [
        "RTL contains the control/state/handshake logic for this cycle rule",
        "Rule timing is reflected in sample/hold/ready/valid or FSM behavior",
        "TB scoreboard/coverage can observe the rule at the declared phase",
        "Traceability keeps source_ref cycle_model.pipeline.S0_ACCEPT",
        "Primary implementation evidence is in rtl/pl330_target_engine.sv",
        "cycle_model.pipeline.S0_ACCEPT timing uses SSOT cycle/latency 0..N",
        "cycle_model.pipeline.S0_ACCEPT appears in RTL sample/hold/FSM/ready-valid timing, not only in TB"
      ],
      "detail": "Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.\nSSOT ref: cycle_model.pipeline.S0_ACCEPT.\nOwner: pl330_target_engine in rtl/pl330_target_engine.sv via cycle_model.pipeline.\nSSOT item context: stage=S0_ACCEPT; cycle=0..N.",
      "evidence_terms": [
        "ACCEPT",
        "S0",
        "S0_ACCEPT"
      ],
      "id": "RTL-0182",
      "owner_file": "rtl/pl330_target_engine.sv",
      "owner_module": "pl330_target_engine",
      "priority": "high",
      "required": true,
      "source_ref": "cycle_model.pipeline.S0_ACCEPT",
      "ssot_context": {
        "cycle": "0..N",
        "stage": "S0_ACCEPT"
      },
      "ssot_refs": [
        "cycle_model.pipeline.S0_ACCEPT"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "ACCEPT",
          "S0",
          "S0_ACCEPT"
        ],
        "source_scope": "rtl/pl330_target_engine.sv",
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
        "reason": "Owner RTL file is missing: rtl/pl330_target_engine.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "cycle_model.pipeline",
      "content": "Implement pipeline stage: S1_EVALUATE",
      "criteria": [
        "RTL contains the control/state/handshake logic for this cycle rule",
        "Rule timing is reflected in sample/hold/ready/valid or FSM behavior",
        "TB scoreboard/coverage can observe the rule at the declared phase",
        "Traceability keeps source_ref cycle_model.pipeline.S1_EVALUATE",
        "Primary implementation evidence is in rtl/pl330_target_engine.sv",
        "cycle_model.pipeline.S1_EVALUATE timing uses SSOT cycle/latency N..M",
        "cycle_model.pipeline.S1_EVALUATE appears in RTL sample/hold/FSM/ready-valid timing, not only in TB"
      ],
      "detail": "Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.\nSSOT ref: cycle_model.pipeline.S1_EVALUATE.\nOwner: pl330_target_engine in rtl/pl330_target_engine.sv via cycle_model.pipeline.\nSSOT item context: stage=S1_EVALUATE; cycle=N..M.",
      "evidence_terms": [
        "EVALUATE",
        "S1",
        "S1_EVALUATE"
      ],
      "id": "RTL-0183",
      "owner_file": "rtl/pl330_target_engine.sv",
      "owner_module": "pl330_target_engine",
      "priority": "high",
      "required": true,
      "source_ref": "cycle_model.pipeline.S1_EVALUATE",
      "ssot_context": {
        "cycle": "N..M",
        "stage": "S1_EVALUATE"
      },
      "ssot_refs": [
        "cycle_model.pipeline.S1_EVALUATE"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "EVALUATE",
          "S1",
          "S1_EVALUATE"
        ],
        "source_scope": "rtl/pl330_target_engine.sv",
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
        "reason": "Owner RTL file is missing: rtl/pl330_target_engine.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "cycle_model.pipeline",
      "content": "Implement pipeline stage: S2_OBSERVE",
      "criteria": [
        "RTL contains the control/state/handshake logic for this cycle rule",
        "Rule timing is reflected in sample/hold/ready/valid or FSM behavior",
        "TB scoreboard/coverage can observe the rule at the declared phase",
        "Traceability keeps source_ref cycle_model.pipeline.S2_OBSERVE",
        "Primary implementation evidence is in rtl/pl330_target_engine.sv",
        "cycle_model.pipeline.S2_OBSERVE timing uses SSOT cycle/latency M..K",
        "cycle_model.pipeline.S2_OBSERVE appears in RTL sample/hold/FSM/ready-valid timing, not only in TB"
      ],
      "detail": "Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.\nSSOT ref: cycle_model.pipeline.S2_OBSERVE.\nOwner: pl330_target_engine in rtl/pl330_target_engine.sv via cycle_model.pipeline.\nSSOT item context: stage=S2_OBSERVE; cycle=M..K.",
      "evidence_terms": [
        "OBSERVE",
        "S2",
        "S2_OBSERVE"
      ],
      "id": "RTL-0184",
      "owner_file": "rtl/pl330_target_engine.sv",
      "owner_module": "pl330_target_engine",
      "priority": "high",
      "required": true,
      "source_ref": "cycle_model.pipeline.S2_OBSERVE",
      "ssot_context": {
        "cycle": "M..K",
        "stage": "S2_OBSERVE"
      },
      "ssot_refs": [
        "cycle_model.pipeline.S2_OBSERVE"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "OBSERVE",
          "S2",
          "S2_OBSERVE"
        ],
        "source_scope": "rtl/pl330_target_engine.sv",
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
        "reason": "Owner RTL file is missing: rtl/pl330_target_engine.sv.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "equivalence.module",
      "content": "Prove module pl330_target_engine is functionally equivalent to FL",
      "criteria": [
        "verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module",
        "cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff",
        "scoreboard row fl_expected.model_api is FunctionalModel.apply",
        "scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data",
        "Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong",
        "Traceability keeps source_ref sub_modules.pl330_target_engine.module_equivalence",
        "Primary implementation evidence is in rtl/pl330_target_engine.sv"
      ],
      "detail": "This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.\nSSOT ref: sub_modules.pl330_target_engine.module_equivalence.\nOwner: pl330_target_engine in rtl/pl330_target_engine.sv via module_equivalence.",
      "evidence_terms": [],
      "id": "RTL-0261",
      "owner_file": "rtl/pl330_target_engine.sv",
      "owner_module": "pl330_target_engine",
      "priority": "high",
      "required": true,
      "source_ref": "sub_modules.pl330_target_engine.module_equivalence",
      "ssot_context": {},
      "ssot_refs": [
        "sub_modules.pl330_target_engine.module_equivalence"
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
        "reason": "Owner RTL file is missing: rtl/pl330_target_engine.sv.",
        "required": true,
        "status": "open"
      }
    }
  ],
  "todo_plan_sha256": "67f1ff9bf1c0231e8ac6b228f14bf8866bb926d7596a6c36deeabfbcb3a528fc",
  "top": "pl330_target",
  "type": "rtl_authoring_packet"
}


Current packet Markdown (rtl/authoring_packets/module__pl330_target_engine.md):
# RTL Authoring Packet: module__pl330_target_engine

- Kind: module
- Owner module: pl330_target_engine
- Owner file: rtl/pl330_target_engine.sv
- Task count: 8
- Required tasks: 8

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
- LLM-actionable open tasks: 8
- Human-locked open tasks: 0
- Owner refs: cycle_model.pipeline, fsm.engine, function_model.transactions.decode, function_model.transactions.execute, function_model.transactions.fetch
- Connection contract gap: Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.

## Tasks

### RTL-0028: Implement or account for SSOT module slice `pl330_target_engine`

- Priority: high
- Required: True
- Status: open
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[1]
- Detail: name=pl330_target_engine
SSOT ref: workflow_todos.rtl-gen[1].
Owner: pl330_target_engine in rtl/pl330_target_engine.sv via workflow_todos.owner.
SSOT item context: id=RTL_MODULE_PL330_TARGET_ENGINE.
- Current reason: Owner RTL file is missing: rtl/pl330_target_engine.sv.
- Criteria:
  - Owned SSOT refs are implemented in the owner RTL file or explicitly mapped to the top integration module
  - Module slice has traceability evidence in rtl_todo_plan.json
  - No function/cycle/register/dataflow/FSM task owned by this slice remains orphaned
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[1]
  - Primary implementation evidence is in rtl/pl330_target_engine.sv
  - Semantic source_refs covered: sub_modules[0]
- SSOT refs: sub_modules[0], workflow_todos.rtl-gen[1]

### RTL-0172: Preserve FL invariant invariant_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_0
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_0.
Owner: pl330_target_engine in rtl/pl330_target_engine.sv via control_owner_fallback.
SSOT item context: value=outstanding_reads >= 0 && outstanding_reads <= 2*NUM_CHANNELS.
- Current reason: Owner RTL file is missing: rtl/pl330_target_engine.sv.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_0
  - Primary implementation evidence is in rtl/pl330_target_engine.sv
- SSOT refs: function_model.invariants.invariant_0

### RTL-0173: Preserve FL invariant invariant_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_1
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_1.
Owner: pl330_target_engine in rtl/pl330_target_engine.sv via control_owner_fallback.
SSOT item context: value=outstanding_writes >= 0 && outstanding_writes <= 2*NUM_CHANNELS.
- Current reason: Owner RTL file is missing: rtl/pl330_target_engine.sv.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_1
  - Primary implementation evidence is in rtl/pl330_target_engine.sv
- SSOT refs: function_model.invariants.invariant_1

### RTL-0175: Preserve FL invariant invariant_3

- Priority: high
- Required: True
- Status: open
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_3
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_3.
Owner: pl330_target_engine in rtl/pl330_target_engine.sv via control_owner_fallback.
SSOT item context: value=channel_state != 1 -> outstanding_reads == 0 && outstanding_writes == 0.
- Current reason: Owner RTL file is missing: rtl/pl330_target_engine.sv.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_3
  - Primary implementation evidence is in rtl/pl330_target_engine.sv
- SSOT refs: function_model.invariants.invariant_3

### RTL-0182: Implement pipeline stage: S0_ACCEPT

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S0_ACCEPT
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S0_ACCEPT.
Owner: pl330_target_engine in rtl/pl330_target_engine.sv via cycle_model.pipeline.
SSOT item context: stage=S0_ACCEPT; cycle=0..N.
- Current reason: Owner RTL file is missing: rtl/pl330_target_engine.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S0_ACCEPT
  - Primary implementation evidence is in rtl/pl330_target_engine.sv
  - cycle_model.pipeline.S0_ACCEPT timing uses SSOT cycle/latency 0..N
  - cycle_model.pipeline.S0_ACCEPT appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S0_ACCEPT

### RTL-0183: Implement pipeline stage: S1_EVALUATE

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S1_EVALUATE
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S1_EVALUATE.
Owner: pl330_target_engine in rtl/pl330_target_engine.sv via cycle_model.pipeline.
SSOT item context: stage=S1_EVALUATE; cycle=N..M.
- Current reason: Owner RTL file is missing: rtl/pl330_target_engine.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S1_EVALUATE
  - Primary implementation evidence is in rtl/pl330_target_engine.sv
  - cycle_model.pipeline.S1_EVALUATE timing uses SSOT cycle/latency N..M
  - cycle_model.pipeline.S1_EVALUATE appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S1_EVALUATE

### RTL-0184: Implement pipeline stage: S2_OBSERVE

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S2_OBSERVE
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S2_OBSERVE.
Owner: pl330_target_engine in rtl/pl330_target_engine.sv via cycle_model.pipeline.
SSOT item context: stage=S2_OBSERVE; cycle=M..K.
- Current reason: Owner RTL file is missing: rtl/pl330_target_engine.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S2_OBSERVE
  - Primary implementation evidence is in rtl/pl330_target_engine.sv
  - cycle_model.pipeline.S2_OBSERVE timing uses SSOT cycle/latency M..K
  - cycle_model.pipeline.S2_OBSERVE appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S2_OBSERVE

### RTL-0261: Prove module pl330_target_engine is functionally equivalent to FL

- Priority: high
- Required: True
- Status: open
- Category: equivalence.module
- Source ref: sub_modules.pl330_target_engine.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.pl330_target_engine.module_equivalence.
Owner: pl330_target_engine in rtl/pl330_target_engine.sv via module_equivalence.
- Current reason: Owner RTL file is missing: rtl/pl330_target_engine.sv.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.pl330_target_engine.module_equivalence
  - Primary implementation evidence is in rtl/pl330_target_engine.sv
- SSOT refs: sub_modules.pl330_target_engine.module_equivalence
