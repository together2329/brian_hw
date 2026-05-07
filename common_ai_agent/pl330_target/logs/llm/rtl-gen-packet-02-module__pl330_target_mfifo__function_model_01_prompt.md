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

Current packet: module__pl330_target_mfifo__function_model_01
kind: module
work queue: 3/4 active packets (24 closed packets skipped from 30 total)
batch limit: 4; deferred active packets after this batch: 2
owner_module: pl330_target_mfifo
owner_file: rtl/pl330_target_mfifo.sv

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
        "gate_kind": "static_rtl_evidence",
        "owner_module": "pl330_target",
        "reason": "33 static-evidence-required task(s) still lack DUT RTL evidence.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.static_rtl_evidence",
        "status": "open",
        "task_id": "RTL-0007"
      },
      {
        "gate_kind": "manifest_hierarchy_integration",
        "owner_module": "pl330_target",
        "reason": "9 manifest hierarchy integration issue(s) remain. pl330_target_engine: SSOT manifest child module is declared but not reachable from the top RTL hierarchy; pl330_target_pipeline: SSOT manifest child module is declared but not reachable from the top RTL hierarchy; pl330_target_lsq: SSOT manifest child module is declared but not reachable from the top RTL hierarchy",
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
        "reason": "45 required non-closure TODO(s) remain open.",
        "source": "gate_todo",
        "source_ref": "quality_gates.rtl_gen.dynamic_todo_closure",
        "status": "open",
        "task_id": "RTL-0019"
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
    "open_required_todos": 46,
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
      "json": "rtl/authoring_packets/module__pl330_target_mfifo__function_model_02.json",
      "kind": "module",
      "llm_actionable_open_count": 5,
      "open_required_count": 5,
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "packet_id": "module__pl330_target_mfifo__function_model_02",
      "required_count": 15,
      "status_counts": {
        "open": 5,
        "pass": 10
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__pl330_target_mfifo__function_model_01.json",
      "kind": "module",
      "llm_actionable_open_count": 2,
      "open_required_count": 2,
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "packet_id": "module__pl330_target_mfifo__function_model_01",
      "required_count": 48,
      "status_counts": {
        "open": 2,
        "pass": 46
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
      "llm_actionable_open_count": 6,
      "open_required_count": 12,
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "packet_id": "rtl_gate_closure",
      "required_count": 24,
      "status_counts": {
        "open": 12,
        "pass": 12
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
      "json": "rtl/authoring_packets/module__pl330_target_pipeline.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/pl330_target_pipeline.sv",
      "owner_module": "pl330_target_pipeline",
      "packet_id": "module__pl330_target_pipeline",
      "required_count": 13,
      "status_counts": {
        "pass": 13
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__pl330_target_lsq.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/pl330_target_lsq.sv",
      "owner_module": "pl330_target_lsq",
      "packet_id": "module__pl330_target_lsq",
      "required_count": 2,
      "status_counts": {
        "pass": 2
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__pl330_target_mfifo__coverage.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "packet_id": "module__pl330_target_mfifo__coverage",
      "required_count": 6,
      "status_counts": {
        "pass": 6
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__pl330_target_mfifo__equivalence.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "packet_id": "module__pl330_target_mfifo__equivalence",
      "required_count": 1,
      "status_counts": {
        "pass": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__pl330_target_mfifo__features.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "packet_id": "module__pl330_target_mfifo__features",
      "required_count": 7,
      "status_counts": {
        "pass": 7
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__pl330_target_mfifo__memory.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "packet_id": "module__pl330_target_mfifo__memory",
      "required_count": 1,
      "status_counts": {
        "pass": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__pl330_target_mfifo__parameters.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "packet_id": "module__pl330_target_mfifo__parameters",
      "required_count": 1,
      "status_counts": {
        "pass": 1
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__pl330_target_mfifo__registers.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "packet_id": "module__pl330_target_mfifo__registers",
      "required_count": 19,
      "status_counts": {
        "pass": 19
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__pl330_target_mfifo__test_requirements.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "packet_id": "module__pl330_target_mfifo__test_requirements",
      "required_count": 12,
      "status_counts": {
        "pass": 12
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__pl330_target_mfifo__workflow_todo.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "packet_id": "module__pl330_target_mfifo__workflow_todo",
      "required_count": 6,
      "status_counts": {
        "pass": 6
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__pl330_target_merge_buffer.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/pl330_target_merge_buffer.sv",
      "owner_module": "pl330_target_merge_buffer",
      "packet_id": "module__pl330_target_merge_buffer",
      "required_count": 4,
      "status_counts": {
        "pass": 4
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__pl330_target_icache.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/pl330_target_icache.sv",
      "owner_module": "pl330_target_icache",
      "packet_id": "module__pl330_target_icache",
      "required_count": 4,
      "status_counts": {
        "pass": 4
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__pl330_target_axi.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/pl330_target_axi.sv",
      "owner_module": "pl330_target_axi",
      "packet_id": "module__pl330_target_axi",
      "required_count": 5,
      "status_counts": {
        "pass": 5
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__pl330_target_periph.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/pl330_target_periph.sv",
      "owner_module": "pl330_target_periph",
      "packet_id": "module__pl330_target_periph",
      "required_count": 3,
      "status_counts": {
        "pass": 3
      }
    },
    {
      "human_locked_open_count": 0,
      "json": "rtl/authoring_packets/module__pl330_target_apb_regs.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/pl330_target_apb_regs.sv",
      "owner_module": "pl330_target_apb_regs",
      "packet_id": "module__pl330_target_apb_regs",
      "required_count": 4,
      "status_counts": {
        "pass": 4
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
    "llm_actionable_packets": 6,
    "llm_actionable_tasks": 40,
    "max_packet_required_tasks": 48,
    "module_packets": 28,
    "next_llm_packets": [
      "module__pl330_target_mfifo__fsm",
      "module__pl330_target_mfifo__function_model_02",
      "module__pl330_target_mfifo__function_model_01",
      "module__pl330_target__workflow_todo_01",
      "unowned_tasks",
      "rtl_gate_closure"
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

Current owner RTL file (rtl/pl330_target_mfifo.sv):
`default_nettype none

module pl330_target_mfifo #(
    parameter integer FIFO_DEPTH = 16,
    parameter integer DATA_W = 32,
    parameter integer ADDR_W = 32
) (
    input  wire                  clk,
    input  wire                  rst_n,

    input  wire                  soft_reset_i,
    input  wire [31:0]           irq_clear_i,
    input  wire [31:0]           fault_clear_i,

    input  wire                  cmd_valid_i,
    output wire                  cmd_ready_o,
    input  wire [7:0]            cmd_opcode_i,
    input  wire [ADDR_W-1:0]     cmd_arg_addr_i,
    input  wire [31:0]           cmd_arg_data_i,
    input  wire [4:0]            cmd_event_i,
    input  wire                  cmd_manager_i,
    input  wire                  cmd_secure_i,
    input  wire                  dbginst_write_i,
    input  wire                  cfg_nonsecure_allowed_i,
    input  wire [ADDR_W-1:0]     cmd_next_pc_i,

    output logic                 cmd_accept_o,
    output logic                 cmd_error_o,
    output logic [7:0]           cmd_fault_code_o,

    output wire                  ld_req_valid_o,
    input  wire                  ld_req_ready_i,
    output wire [ADDR_W-1:0]     ld_req_addr_o,
    input  wire                  ld_rsp_valid_i,
    output wire                  ld_rsp_ready_o,
    input  wire [DATA_W-1:0]     ld_rsp_data_i,
    input  wire                  ld_rsp_error_i,

    output wire                  st_req_valid_o,
    input  wire                  st_req_ready_i,
    output wire [ADDR_W-1:0]     st_req_addr_o,
    output wire [DATA_W-1:0]     st_req_data_o,
    input  wire                  st_rsp_valid_i,
    output wire                  st_rsp_ready_o,
    input  wire                  st_rsp_error_i,

    input  wire                  mfifo_push_valid_i,
    output wire                  mfifo_push_ready_o,
    input  wire [DATA_W-1:0]     mfifo_push_data_i,
    input  wire                  mfifo_pop_valid_i,
    output wire                  mfifo_pop_ready_o,
    output wire [DATA_W-1:0]     mfifo_pop_data_o,

    output wire                  mfifo_full_o,
    output wire                  mfifo_empty_o,
    output wire [4:0]            mfifo_count_o,
    output wire [3:0]            channel_state_o,
    output wire [ADDR_W-1:0]     channel_pc_o,
    output wire [3:0]            outstanding_reads_o,
    output wire [3:0]            outstanding_writes_o,
    output wire [31:0]           irq_status_o,
    output wire [31:0]           fault_status_o,
    output logic                 reset_accepted_o,
    output logic                 fault_valid_o
);

    // FSM traceability for packet module__pl330_target_mfifo__fsm.
    // fsm.channel_state.states.state_0 value=STOPPED.
    // fsm.channel_state.states.state_1 value=EXECUTING.
    // fsm.channel_state.states.state_2 value=CACHE_MISS.
    // fsm.channel_state.states.state_3 value=UPDATING_PC.
    // fsm.channel_state.states.state_4 value=WAITING_FOR_EVENT.
    // fsm.channel_state.states.state_5 value=AT_BARRIER.
    // fsm.channel_state.states.state_6 value=KILLING.
    // fsm.channel_state.states.state_7 value=COMPLETING.
    // fsm.channel_state.states.state_8 value=FAULTING.
    // fsm.channel_state.states.state_9 value=FAULTING_COMPLETING.
    localparam [3:0] CH_STOPPED            = 4'd0;
    localparam [3:0] CH_EXECUTING          = 4'd1;
    localparam [3:0] CH_CACHE_MISS         = 4'd2;
    localparam [3:0] CH_UPDATING_PC        = 4'd3;
    localparam [3:0] CH_WAITING_FOR_EVENT  = 4'd4;
    localparam [3:0] CH_AT_BARRIER         = 4'd5;
    localparam [3:0] CH_KILLING            = 4'd6;
    localparam [3:0] CH_COMPLETING         = 4'd7;
    localparam [3:0] CH_FAULTING           = 4'd8;
    localparam [3:0] CH_FAULTING_COMPLETING= 4'd9;

    localparam [7:0] OP_DMAEND  = 8'h00;
    localparam [7:0] OP_DMAKILL = 8'h01;
    localparam [7:0] OP_DMALD   = 8'h04;
    localparam [7:0] OP_DMAST   = 8'h08;
    localparam [7:0] OP_DMAWFP  = 8'h30;
    localparam [7:0] OP_DMASEV  = 8'h34;
    localparam [7:0] OP_DMAWFE  = 8'h36;
    localparam [7:0] OP_DMALDP  = 8'h25;
    localparam [7:0] OP_DMASTP  = 8'h29;
    localparam [7:0] OP_DMAGO   = 8'ha0;
    localparam [7:0] OP_FAULT   = 8'hff;

    localparam [4:0] FIFO_DEPTH_COUNT = 5'd16;
    localparam [4:0] FIFO_ALMOST_FULL_COUNT = 5'd15;

    // function_model.transactions.FM_DMASEV.preconditions.precondition_1:
    // NUM_IRQS bounds the event_idx used to update irq_status[event_idx].
    localparam integer NUM_IRQS = 32;
    localparam [5:0] NUM_IRQS_LIMIT = 6'd32;
    localparam [4:0] IRQ_ABORT_IDX = 5'd31;

    logic [3:0]        channel_state;
    logic [ADDR_W-1:0] channel_pc;
    logic [3:0]        outstanding_reads;
    logic [3:0]        outstanding_writes;
    logic [4:0]        mfifo_count;
    logic [31:0]       irq_status;
    logic [31:0]       fault_status;
    logic [4:0]        wait_event_id;

    logic [DATA_W-1:0] fifo_mem [0:FIFO_DEPTH-1];
    logic [3:0]        wr_ptr;
    logic [3:0]        rd_ptr;

    integer fifo_i;

    wire cmd_is_dmaend  = (cmd_opcode_i == OP_DMAEND);
    wire cmd_is_dmakill = (cmd_opcode_i == OP_DMAKILL);
    wire cmd_is_dmald   = (cmd_opcode_i == OP_DMALD);
    wire cmd_is_dmast   = (cmd_opcode_i == OP_DMAST);
    wire cmd_is_dmaldp  = (cmd_opcode_i == OP_DMALDP);
    wire cmd_is_dmastp  = (cmd_opcode_i == OP_DMASTP);
    wire cmd_is_dmasev  = (cmd_opcode_i == OP_DMASEV);
    wire cmd_is_dmawfe  = (cmd_opcode_i == OP_DMAWFE);
    wire cmd_is_dmawfp  = (cmd_opcode_i == OP_DMAWFP);
    wire cmd_is_dmago   = (cmd_opcode_i == OP_DMAGO);
    wire cmd_is_fault   = (cmd_opcode_i == OP_FAULT);
    wire cmd_is_known   = cmd_is_dmaend | cmd_is_dmakill | cmd_is_dmald | cmd_is_dmast | cmd_is_dmaldp | cmd_is_dmastp | cmd_is_dmasev | cmd_is_dmawfe | cmd_is_dmawfp | cmd_is_dmago | cmd_is_fault;

    wire cmd_is_load  = cmd_is_dmald | cmd_is_dmaldp;
    wire cmd_is_store = cmd_is_dmast | cmd_is_dmastp;

    wire channel_stopped             = (channel_state == CH_STOPPED);
    wire channel_executing           = (channel_state == CH_EXECUTING);
    wire channel_cache_miss          = (channel_state == CH_CACHE_MISS);
    wire channel_updating_pc         = (channel_state == CH_UPDATING_PC);
    wire channel_waiting_for_event   = (channel_state == CH_WAITING_FOR_EVENT);
    wire channel_at_barrier          = (channel_state == CH_AT_BARRIER);
    wire channel_killing             = (channel_state == CH_KILLING);
    wire channel_completing          = (channel_state == CH_COMPLETING);
    wire channel_faulting            = (channel_state == CH_FAULTING);
    wire channel_faulting_completing = (channel_state == CH_FAULTING_COMPLETING);
    wire channel_live = channel_executing | channel_cache_miss | channel_updating_pc | channel_waiting_for_event | channel_at_barrier | channel_completing;

    wire fifo_full  = (mfifo_count == FIFO_DEPTH_COUNT);
    wire fifo_empty = (mfifo_count == 5'd0);

    wire fifo_pop_store_pre = cmd_valid_i & cmd_is_store & channel_executing & ~fifo_empty & (outstanding_writes != 4'd15) & st_req_ready_i;
    wire fifo_pop_ext_pre   = mfifo_pop_valid_i & ~fifo_empty & ~fifo_pop_store_pre;
    wire fifo_space_avail   = ~fifo_full | fifo_pop_store_pre | fifo_pop_ext_pre;

    wire load_backpressure  = (outstanding_reads == 4'd15) | (mfifo_count >= FIFO_ALMOST_FULL_COUNT) | ~ld_req_ready_i;
    wire store_backpressure = fifo_empty | (outstanding_writes == 4'd15) | ~st_req_ready_i;
    wire command_blocked    = (channel_completing | channel_faulting | channel_faulting_completing | channel_killing) & ~(cmd_is_dmakill & dbginst_write_i & cmd_manager_i);

    assign cmd_ready_o = ~command_blocked & ~(cmd_valid_i & ((cmd_is_load & load_backpressure) | (cmd_is_store & store_backpressure)));

    wire cmd_accept = cmd_valid_i & cmd_ready_o;
    wire secure_violation = cmd_accept & ~cmd_secure_i & ~cfg_nonsecure_allowed_i;

    wire [4:0] event_idx = cmd_event_i;
    wire [5:0] event_idx_ext = {1'b0, event_idx};
    wire event_idx_in_range = (event_idx_ext < NUM_IRQS_LIMIT);

    wire dmago_pre_ok = channel_stopped & dbginst_write_i & cmd_manager_i;
    wire dmago_accept = cmd_accept & cmd_is_dmago & dmago_pre_ok & ~secure_violation;
    wire dmago_fault  = cmd_accept & cmd_is_dmago & (~dmago_pre_ok | secure_violation);

    wire load_pre_ok  = channel_executing & ~load_backpressure;
    wire dmald_accept = cmd_accept & cmd_is_dmald  & load_pre_ok & ~secure_violation;
    wire dmaldp_accept= cmd_accept & cmd_is_dmaldp & load_pre_ok & ~secure_violation;
    wire load_fault   = cmd_accept & cmd_is_load & (~load_pre_ok | secure_violation);

    wire store_pre_ok = channel_executing & ~store_backpressure;
    wire dmast_accept = cmd_accept & cmd_is_dmast  & store_pre_ok & ~secure_violation;
    wire dmastp_accept= cmd_accept & cmd_is_dmastp & store_pre_ok & ~secure_violation;
    wire store_fault  = cmd_accept & cmd_is_store & (~store_pre_ok | secure_violation);

    wire dmasev_state_pre_ok = channel_executing | channel_waiting_for_event;
    wire dmasev_pre_ok = dmasev_state_pre_ok & event_idx_in_range;
    wire dmasev_accept = cmd_accept & cmd_is_dmasev & dmasev_pre_ok & ~secure_violation;
    wire dmasev_fault  = cmd_accept & cmd_is_dmasev & (~dmasev_pre_ok | secure_violation);

    wire dmawfe_pre_ok = channel_executing;
    wire dmawfe_accept = cmd_accept & cmd_is_dmawfe & dmawfe_pre_ok & ~secure_violation;
    wire dmawfe_fault  = cmd_accept & cmd_is_dmawfe & (~dmawfe_pre_ok | secure_violation);

    wire dmawfp_pre_ok = channel_executing;
    wire dmawfp_accept = cmd_accept & cmd_is_dmawfp & dmawfp_pre_ok & ~secure_violation;
    wire dmawfp_fault  = cmd_accept & cmd_is_dmawfp & (~dmawfp_pre_ok | secure_violation);

    wire dmaend_accept = cmd_accept & cmd_is_dmaend & channel_executing & ~secure_violation;
    wire dmaend_fault  = cmd_accept & cmd_is_dmaend & (~channel_executing | secure_violation);

    wire dmakill_pre_ok = dbginst_write_i & cmd_manager_i;
    wire dmakill_accept = cmd_accept & cmd_is_dmakill & dmakill_pre_ok & ~secure_violation;
    wire dmakill_fault  = cmd_accept & cmd_is_dmakill & (~dmakill_pre_ok | secure_violation);

    wire explicit_fault_accept = cmd_accept & cmd_is_fault;
    wire illegal_fault_accept  = cmd_accept & ~cmd_is_known;

    wire [ADDR_W-1:0] pc_plus_four = channel_pc + {{(ADDR_W-3){1'b0}}, 3'd4};
    wire [ADDR_W-1:0] next_pc_value = (cmd_next_pc_i != {ADDR_W{1'b0}}) ? cmd_next_pc_i : pc_plus_four;

    assign ld_req_valid_o = dmald_accept | dmaldp_accept;
    assign ld_req_addr_o  = channel_pc;
    assign ld_rsp_ready_o = fifo_space_avail;

    assign st_req_valid_o = dmast_accept | dmastp_accept;
    assign st_req_addr_o  = channel_pc;
    assign st_req_data_o  = fifo_mem[rd_ptr];
    assign st_rsp_ready_o = 1'b1;

    wire ld_req_fire = ld_req_valid_o & ld_req_ready_i;
    wire st_req_fire = st_req_valid_o & st_req_ready_i;
    wire ld_rsp_fire = ld_rsp_valid_i & ld_rsp_ready_o;
    wire st_rsp_fire = st_rsp_valid_i & st_rsp_ready_o;

    // function_model.transactions.FM_FAULT.preconditions.precondition_0:
    // any error_case fired produces a same-cycle irq_abort_pulse and FAULTING state update.
    wire fm_fault_error_case_fired = dmago_fault |
                                      load_fault |
                                      store_fault |
                                      dmasev_fault |
                                      dmaend_fault |
                                      dmawfe_fault |
                                      dmawfp_fault |
                                      dmakill_fault |
                                      explicit_fault_accept |
                                      illegal_fault_accept |
                                      (ld_rsp_fire & ld_rsp_error_i) |
                                      (st_rsp_fire & st_rsp_error_i);
    wire irq_abort_pulse = fm_fault_error_case_fired;

    wire fifo_push_rsp = ld_rsp_valid_i & ld_rsp_ready_o & ~ld_rsp_error_i;
    assign mfifo_push_ready_o = fifo_space_avail & ~(ld_rsp_valid_i & ~ld_rsp_error_i);
    wire fifo_push_ext = mfifo_push_valid_i & mfifo_push_ready_o;
    wire fifo_push = fifo_push_rsp | fifo_push_ext;
    wire [DATA_W-1:0] fifo_push_data = fifo_push_rsp ? ld_rsp_data_i : mfifo_push_data_i;

    wire fifo_pop_store = st_req_fire;
    assign mfifo_pop_ready_o = ~fifo_empty & ~fifo_pop_store;
    wire fifo_pop_ext = mfifo_pop_valid_i & mfifo_pop_ready_o;
    wire fifo_pop = fifo_pop_store | fifo_pop_ext;

    wire event_signaled = channel_waiting_for_event & (irq_status[wait_event_id] | (dmasev_accept & (event_idx == wait_event_id)));
    wire barrier_cleared = channel_at_barrier & (outstanding_reads == 4'd0) & (outstanding_writes == 4'd0);
    wire all_outstanding_drained = (outstanding_reads == 4'd0) & (outstanding_writes == 4'd0);
    wire kill_complete = channel_killing & all_outstanding_drained;
    wire fault_drain_complete = channel_faulting & all_outstanding_drained;
    wire fault_clear_to_stopped = channel_faulting_completing & (|fault_clear_i) & ((fault_status & ~fault_clear_i) == 32'h00000000);

    assign mfifo_pop_data_o = fifo_mem[rd_ptr];
    assign mfifo_full_o = fifo_full;
    assign mfifo_empty_o = fifo_empty;
    assign mfifo_count_o = mfifo_count;
    assign channel_state_o = channel_state;
    assign channel_pc_o = channel_pc;
    assign outstanding_reads_o = outstanding_reads;
    assign outstanding_writes_o = outstanding_writes;
    assign irq_status_o = irq_status;
    assign fault_status_o = fault_status;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            channel_state <= CH_STOPPED;
            channel_pc <= {ADDR_W{1'b0}};
            outstanding_reads <= 4'd0;
            outstanding_writes <= 4'd0;
            mfifo_count <= 5'd0;
            irq_status <= 32'h00000000;
            fault_status <= 32'h00000000;
            wait_event_id <= 5'd0;
            wr_ptr <= 4'd0;
            rd_ptr <= 4'd0;
            cmd_accept_o <= 1'b0;
            cmd_error_o <= 1'b0;
            cmd_fault_code_o <= 8'h00;
            reset_accepted_o <= 1'b0;
            fault_valid_o <= 1'b0;
            for (fifo_i = 0; fifo_i < FIFO_DEPTH; fifo_i = fifo_i + 1) begin
                fifo_mem[fifo_i] <= {DATA_W{1'b0}};
            end
        end else begin
            cmd_accept_o <= 1'b0;
            cmd_error_o <= 1'b0;
            cmd_fault_code_o <= 8'h00;
            reset_accepted_o <= 1'b0;
            fault_valid_o <= 1'b0;

            if (soft_reset_i) begin
                // Trace: function_model.transactions.FM_RESET and fsm.channel_state.states.state_0 STOPPED reset entry.
                channel_state <= CH_STOPPED;
                channel_pc <= {ADDR_W{1'b0}};
                outstanding_reads <= 4'd0;
                outstanding_writes <= 4'd0;
                mfifo_count <= 5'd0;
                irq_status <= 32'h00000000;
                fault_status <= 32'h00000000;
                wait_event_id <= 5'd0;
                wr_ptr <= 4'd0;
                rd_ptr <= 4'd0;
                reset_accepted_o <= 1'b1;
                for (fifo_i = 0; fifo_i < FIFO_DEPTH; fifo_i = fifo_i + 1) begin
                    fifo_mem[fifo_i] <= {DATA_W{1'b0}};
                end
            end else begin
                case ({ld_req_fire, ld_rsp_fire})
                    2'b10: begin
                        if (outstanding_reads != 4'd15) begin
                            outstanding_reads <= outstanding_reads + 4'd1;
                        end
                    end
                    2'b01: begin
                        if (outstanding_reads != 4'd0) begin
                            outstanding_reads <= outstanding_reads - 4'd1;
                        end
                    end
                    default: begin
                        outstanding_reads <= outstanding_reads;
                    end
                endcase

                case ({st_req_fire, st_rsp_fire})
                    2'b10: begin
                        if (outstanding_writes != 4'd15) begin
                            outstanding_writes <= outstanding_writes + 4'd1;
                        end
                    end
                    2'b01: begin
                        if (outstanding_writes != 4'd0) begin
                            outstanding_writes <= outstanding_writes - 4'd1;
                        end
                    end
                    default: begin
                        outstanding_writes <= outstanding_writes;
                    end
                endcase

                if (fifo_push) begin
                    fifo_mem[wr_ptr] <= fifo_push_data;
                    wr_ptr <= wr_ptr + 4'd1;
                end
                if (fifo_pop) begin
                    rd_ptr <= rd_ptr + 4'd1;
                end
                case ({fifo_push, fifo_pop})
                    2'b10: begin
                        if (mfifo_count != FIFO_DEPTH_COUNT) begin
                            mfifo_count <= mfifo_count + 5'd1;
                        end
                    end
                    2'b01: begin
                        if (mfifo_count != 5'd0) begin
                            mfifo_count <= mfifo_count - 5'd1;
                        end
                    end
                    default: begin
                        mfifo_count <= mfifo_count;
                    end
                endcase

                if (|irq_clear_i) begin
                    irq_status <= irq_status & ~irq_clear_i;
                end
                if (|fault_clear_i) begin
                    fault_status <= fault_status & ~fault_clear_i;
                end

                if (irq_abort_pulse) begin
                    // function_model.transactions.FM_FAULT.outputs.output_1 and invariant_4:
                    // fault triggers irq_abort within 4 cycles; this implementation raises it in the fault cycle.
                    irq_status[IRQ_ABORT_IDX] <= 1'b1;
                end

                if (cmd_accept) begin
                    cmd_accept_o <= 1'b1;
                end

                if (dmago_accept) begin
                    // fsm.channel_state.transitions.transition_0: DMAGO + secure check pass, STOPPED -> EXECUTING.
                    channel_state <= CH_EXECUTING;
                    channel_pc <= cmd_arg_addr_i;
                end

                if (dmald_accept | dmaldp_accept) begin
                    // fsm.channel_state.transitions.transition_1: DMALD/DMALDP request models icache miss/data fill, EXECUTING -> CACHE_MISS.
                    channel_state <= CH_CACHE_MISS;
                    channel_pc <= next_pc_value;
                end

                if (dmast_accept | dmastp_accept) begin
                    // fsm.channel_state.states.state_3: UPDATING_PC while an accepted DMAST/DMASTP waits for store response.
                    channel_state <= CH_UPDATING_PC;
                    channel_pc <= next_pc_value;
                end

                if (dmasev_accept) begin
                    // Trace: function_model.transactions.FM_DMASEV sets irq_status[event_idx] once per accepted command.
                    // Side effect: irq[event_idx] pulse is observable through the irq_status bit set in this cycle.
                    irq_status[event_idx] <= 1'b1;
                    channel_pc <= next_pc_value;
                    if (channel_executing) begin
                        channel_state <= CH_EXECUTING;
                    end
                end

                if (dmawfe_accept) begin
                    // fsm.channel_state.transitions.transition_3: DMAWFE, EXECUTING -> WAITING_FOR_EVENT.
                    wait_event_id <= event_idx;
                    channel_state <= CH_WAITING_FOR_EVENT;
                    channel_pc <= next_pc_value;
                end

                if (event_signaled) begin
                    // fsm.channel_state.transitions.transition_4: event signaled, WAITING_FOR_EVENT -> EXECUTING.
                    channel_state <= CH_EXECUTING;
                end

                if (dmawfp_accept) begin
                    // fsm.channel_state.transitions.transition_5: DMAWFP barrier, EXECUTING -> AT_BARRIER.
                    channel_state <= CH_AT_BARRIER;
                    channel_pc <= next_pc_value;
                end

                if (barrier_cleared) begin
                    // fsm.channel_state.transitions.transition_6: barrier cleared, AT_BARRIER -> EXECUTING.
                    channel_state <= CH_EXECUTING;
                end

                if (dmaend_accept) begin
                    // fsm.channel_state.transitions.transition_7: DMAEND issued, EXECUTING -> COMPLETING.
                    channel_state <= CH_COMPLETING;
                    channel_pc <= next_pc_value;
                end

                if (channel_completing && all_outstanding_drained) begin
                    // fsm.channel_state.transitions.transition_8: all outstanding drained, COMPLETING -> STOPPED.
                    channel_state <= CH_STOPPED;
                end

                if (dmakill_accept) begin
                    // fsm.channel_state.transitions.transition_9: DMAKILL via DBGCMD, any -> KILLING.
                    channel_state <= CH_KILLING;
                    fault_status[19] <= 1'b0;
                end

                if (kill_complete) begin
                    // fsm.channel_state.transitions.transition_10: kill complete, KILLING -> STOPPED.
                    channel_state <= CH_STOPPED;
                    channel_pc <= {ADDR_W{1'b0}};
                    mfifo_count <= 5'd0;
                    wr_ptr <= 4'd0;
                    rd_ptr <= 4'd0;
                end

                if (ld_rsp_fire && !ld_rsp_error_i && channel_cache_miss) begin
                    // fsm.channel_state.transitions.transition_2: fill complete, CACHE_MISS -> EXECUTING.
                    if (outstanding_reads <= 4'd1) begin
                        channel_state <= CH_EXECUTING;
                    end
                end

                if (st_rsp_fire && !st_rsp_error_i && channel_updating_pc) begin
                    channel_state <= CH_EXECUTING;
                end

                if (channel_updating_pc && (outstanding_writes == 4'd0)) begin
                    channel_state <= CH_EXECUTING;
                end

                if (fault_drain_complete) begin
                    // fsm.channel_state.transitions.transition_12: fault drain complete, FAULTING -> FAULTING_COMPLETING.
                    channel_state <= CH_FAULTING_COMPLETING;
                end

                if (fault_clear_to_stopped) begin
                    // fsm.channel_state.transitions.transition_13: fault cleared, FAULTING_COMPLETING -> STOPPED.
                    channel_state <= CH_STOPPED;
                end

                if (dmago_fault) begin
                    // fsm.channel_state.transitions.transition_11: secure/decode/precondition fault, any -> FAULTING.
                    channel_state <= CH_FAULTING;
                    fault_status[0] <= secure_violation;
                    fault_status[1] <= ~dmago_pre_ok;
                    cmd_error_o <= 1'b1;
                    cmd_fault_code_o <= secure_violation ? 8'h10 : 8'h11;
                    fault_valid_o <= 1'b1;
                end

                if (load_fault) begin
                    channel_state <= CH_FAULTING;
                    fault_status[2] <= secure_violation;
                    fault_status[3] <= ~load_pre_ok;
                    cmd_error_o <= 1'b1;
                    cmd_fault_code_o <= secure_violation ? 8'h10 : 8'h21;
                    fault_valid_o <= 1'b1;
                end

                if (store_fault) begin
                    channel_state <= CH_FAULTING;
                    fault_status[4] <= secure_violation;
                    fault_status[5] <= ~store_pre_ok;
                    cmd_error_o <= 1'b1;
                    cmd_fault_code_o <= secure_violation ? 8'h10 : 8'h31;
                    fault_valid_o <= 1'b1;
                end

                if (dmasev_fault) begin
                    channel_state <= CH_FAULTING;
                    fault_status[6] <= secure_violation;
                    fault_status[7] <= ~dmasev_state_pre_ok;
                    fault_status[12] <= ~event_idx_in_range;
                    cmd_error_o <= 1'b1;
                    cmd_fault_code_o <= secure_violation ? 8'h10 : ((!event_idx_in_range) ? 8'h42 : 8'h41);
                    fault_valid_o <= 1'b1;
                end

                if (dmaend_fault) begin
                    channel_state <= CH_FAULTING;
                    fault_status[18] <= 1'b1;
                    cmd_error_o <= 1'b1;
                    cmd_fault_code_o <= secure_violation ? 8'h10 : 8'h61;
                    fault_valid_o <= 1'b1;
                end

                if (dmawfe_fault) begin
                    channel_state <= CH_FAULTING;
                    fault_status[20] <= secure_violation;
                    fault_status[21] <= ~dmawfe_pre_ok;
                    cmd_error_o <= 1'b1;
                    cmd_fault_code_o <= secure_violation ? 8'h10 : 8'h71;
                    fault_valid_o <= 1'b1;
                end

                if (dmawfp_fault) begin
                    channel_state <= CH_FAULTING;
                    fault_status[22] <= secure_violation;
                    fault_status[23] <= ~dmawfp_pre_ok;
                    cmd_error_o <= 1'b1;
                    cmd_fault_code_o <= secure_violation ? 8'h10 : 8'h72;
                    fault_valid_o <= 1'b1;
                end

                if (dmakill_fault) begin
                    channel_state <= CH_FAULTING;
                    fault_status[24] <= secure_violation;
                    fault_status[25] <= ~dmakill_pre_ok;
                    cmd_error_o <= 1'b1;
                    cmd_fault_code_o <= secure_violation ? 8'h10 : 8'h73;
                    fault_valid_o <= 1'b1;
                end

                if (explicit_fault_accept) begin
                    channel_state <= CH_FAULTING;
                    fault_status[8] <= 1'b1;
                    fault_status[15:8] <= cmd_arg_data_i[7:0];
                    cmd_error_o <= 1'b1;
                    cmd_fault_code_o <= cmd_arg_data_i[7:0];
                    fault_valid_o <= 1'b1;
                end

                if (illegal_fault_accept) begin
                    channel_state <= CH_FAULTING;
                    fault_status[9] <= 1'b1;
                    cmd_error_o <= 1'b1;
                    cmd_fault_code_o <= 8'hf0;
                    fault_valid_o <= 1'b1;
                end

                if (ld_rsp_fire && ld_rsp_error_i) begin
                    channel_state <= CH_FAULTING;
                    fault_status[10] <= 1'b1;
                    cmd_error_o <= 1'b1;
                    cmd_fault_code_o <= 8'h52;
                    fault_valid_o <= 1'b1;
                end

                if (st_rsp_fire && st_rsp_error_i) begin
                    channel_state <= CH_FAULTING;
                    fault_status[11] <= 1'b1;
                    cmd_error_o <= 1'b1;
                    cmd_fault_code_o <= 8'h62;
                    fault_valid_o <= 1'b1;
                end
            end
        end
    end

endmodule

`default_nettype wire


Current packet JSON (rtl/authoring_packets/module__pl330_target_mfifo__function_model_01.json):
{
  "context": {
    "connection_contract_gap": {
      "machine_readable_contract_count": 0,
      "reason": "Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.",
      "required_for_profile": true,
      "status": "missing"
    },
    "module_slice": {
      "count": 11,
      "enabled": true,
      "index": 2,
      "key": "function_model_01",
      "module_task_count": 140,
      "rule": "Owner module pl330_target_mfifo is split into 11 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.",
      "section": "function_model",
      "section_chunk_count": 2,
      "section_chunk_index": 1,
      "task_limit": 48
    },
    "owner": {
      "file": "rtl/pl330_target_mfifo.sv",
      "name": "pl330_target_mfifo",
      "refs": [
        "cycle_model.backpressure.mfifo_full",
        "dataflow",
        "features",
        "fsm",
        "function_model.state_variables",
        "function_model.state_variables.mfifo",
        "function_model.transactions.FM_DMAEND",
        "function_model.transactions.FM_DMAGO",
        "function_model.transactions.FM_DMALD",
        "function_model.transactions.FM_DMALDP",
        "function_model.transactions.FM_DMASEV",
        "function_model.transactions.FM_DMAST",
        "function_model.transactions.FM_DMASTP",
        "function_model.transactions.FM_FAULT",
        "function_model.transactions.FM_RESET",
        "registers",
        "registers.register_list",
        "test_requirements"
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
  "owner_file": "rtl/pl330_target_mfifo.sv",
  "owner_module": "pl330_target_mfifo",
  "packet_id": "module__pl330_target_mfifo__function_model_01",
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
      "function_model.error_case": 3,
      "function_model.output": 9,
      "function_model.precondition": 12,
      "function_model.side_effect": 10,
      "function_model.state_variable": 7,
      "function_model.transaction": 7
    },
    "module_slice": {
      "count": 11,
      "enabled": true,
      "index": 2,
      "key": "function_model_01",
      "module_task_count": 140,
      "rule": "Owner module pl330_target_mfifo is split into 11 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.",
      "section": "function_model",
      "section_chunk_count": 2,
      "section_chunk_index": 1,
      "task_limit": 48
    },
    "open_required_count": 2,
    "required_count": 48,
    "source_refs": [
      "function_model.state_variables.channel_state",
      "function_model.state_variables.channel_pc",
      "function_model.state_variables.outstanding_reads",
      "function_model.state_variables.outstanding_writes",
      "function_model.state_variables.mfifo_count",
      "function_model.state_variables.irq_status",
      "function_model.state_variables.fault_status",
      "function_model.transactions.FM_RESET",
      "function_model.transactions.FM_RESET.preconditions.precondition_0",
      "function_model.transactions.FM_RESET.outputs.output_0",
      "function_model.transactions.FM_RESET.side_effects.side_effect_0",
      "function_model.transactions.FM_RESET.side_effects.side_effect_1",
      "function_model.transactions.FM_RESET.side_effects.side_effect_2",
      "function_model.transactions.FM_RESET.side_effects.side_effect_3",
      "function_model.transactions.FM_DMAGO",
      "function_model.transactions.FM_DMAGO.preconditions.precondition_0",
      "function_model.transactions.FM_DMAGO.preconditions.precondition_1",
      "function_model.transactions.FM_DMAGO.outputs.output_0",
      "function_model.transactions.FM_DMAGO.outputs.output_1",
      "function_model.transactions.FM_DMAGO.error_cases.error_case_0",
      "function_model.transactions.FM_DMALD",
      "function_model.transactions.FM_DMALD.preconditions.precondition_0",
      "function_model.transactions.FM_DMALD.preconditions.precondition_1",
      "function_model.transactions.FM_DMALD.outputs.output_0"
    ],
    "status_counts": {
      "open": 2,
      "pass": 46
    },
    "task_count": 48
  },
  "tasks": [
    {
      "category": "function_model.state_variable",
      "content": "Implement RTL state owner for FL state channel_state",
      "criteria": [
        "State has a flop/register/memory owner in RTL",
        "Reset value matches SSOT",
        "Every transaction update occurs at the SSOT-defined acceptance/cycle point",
        "Traceability keeps source_ref function_model.state_variables.channel_state",
        "Primary implementation evidence is in rtl/pl330_target_mfifo.sv",
        "channel_state width matches SSOT value 4",
        "channel_state reset behavior matches SSOT value 0"
      ],
      "detail": "Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.\nSSOT ref: function_model.state_variables.channel_state.\nOwner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.state_variables.\nSSOT item context: name=channel_state; width=4; reset=0.",
      "evidence_terms": [],
      "id": "RTL-0111",
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.state_variables.channel_state",
      "ssot_context": {
        "name": "channel_state",
        "reset": "0",
        "width": "4"
      },
      "ssot_refs": [
        "function_model.state_variables.channel_state"
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
        "reason": "Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.",
        "required": true,
        "status": "pass"
      }
    },
    {
      "category": "function_model.state_variable",
      "content": "Implement RTL state owner for FL state channel_pc",
      "criteria": [
        "State has a flop/register/memory owner in RTL",
        "Reset value matches SSOT",
        "Every transaction update occurs at the SSOT-defined acceptance/cycle point",
        "Traceability keeps source_ref function_model.state_variables.channel_pc",
        "Primary implementation evidence is in rtl/pl330_target_mfifo.sv",
        "channel_pc width matches SSOT value 32",
        "channel_pc reset behavior matches SSOT value 0"
      ],
      "detail": "Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.\nSSOT ref: function_model.state_variables.channel_pc.\nOwner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.state_variables.\nSSOT item context: name=channel_pc; width=32; reset=0.",
      "evidence_terms": [],
      "id": "RTL-0112",
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.state_variables.channel_pc",
      "ssot_context": {
        "name": "channel_pc",
        "reset": "0",
        "width": "32"
      },
      "ssot_refs": [
        "function_model.state_variables.channel_pc"
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
        "reason": "Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.",
        "required": true,
        "status": "pass"
      }
    },
    {
      "category": "function_model.state_variable",
      "content": "Implement RTL state owner for FL state outstanding_reads",
      "criteria": [
        "State has a flop/register/memory owner in RTL",
        "Reset value matches SSOT",
        "Every transaction update occurs at the SSOT-defined acceptance/cycle point",
        "Traceability keeps source_ref function_model.state_variables.outstanding_reads",
        "Primary implementation evidence is in rtl/pl330_target_mfifo.sv",
        "outstanding_reads width matches SSOT value 4",
        "outstanding_reads reset behavior matches SSOT value 0"
      ],
      "detail": "Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.\nSSOT ref: function_model.state_variables.outstanding_reads.\nOwner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.state_variables.\nSSOT item context: name=outstanding_reads; width=4; reset=0.",
      "evidence_terms": [],
      "id": "RTL-0113",
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.state_variables.outstanding_reads",
      "ssot_context": {
        "name": "outstanding_reads",
        "reset": "0",
        "width": "4"
      },
      "ssot_refs": [
        "function_model.state_variables.outstanding_reads"
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
        "reason": "Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.",
        "required": true,
        "status": "pass"
      }
    },
    {
      "category": "function_model.state_variable",
      "content": "Implement RTL state owner for FL state outstanding_writes",
      "criteria": [
        "State has a flop/register/memory owner in RTL",
        "Reset value matches SSOT",
        "Every transaction update occurs at the SSOT-defined acceptance/cycle point",
        "Traceability keeps source_ref function_model.state_variables.outstanding_writes",
        "Primary implementation evidence is in rtl/pl330_target_mfifo.sv",
        "outstanding_writes width matches SSOT value 4",
        "outstanding_writes reset behavior matches SSOT value 0"
      ],
      "detail": "Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.\nSSOT ref: function_model.state_variables.outstanding_writes.\nOwner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.state_variables.\nSSOT item context: name=outstanding_writes; width=4; reset=0.",
      "evidence_terms": [],
      "id": "RTL-0114",
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.state_variables.outstanding_writes",
      "ssot_context": {
        "name": "outstanding_writes",
        "reset": "0",
        "width": "4"
      },
      "ssot_refs": [
        "function_model.state_variables.outstanding_writes"
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
        "reason": "Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.",
        "required": true,
        "status": "pass"
      }
    },
    {
      "category": "function_model.state_variable",
      "content": "Implement RTL state owner for FL state mfifo_count",
      "criteria": [
        "State has a flop/register/memory owner in RTL",
        "Reset value matches SSOT",
        "Every transaction update occurs at the SSOT-defined acceptance/cycle point",
        "Traceability keeps source_ref function_model.state_variables.mfifo_count",
        "Primary implementation evidence is in rtl/pl330_target_mfifo.sv",
        "mfifo_count width matches SSOT value 5",
        "mfifo_count reset behavior matches SSOT value 0"
      ],
      "detail": "Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.\nSSOT ref: function_model.state_variables.mfifo_count.\nOwner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.state_variables.\nSSOT item context: name=mfifo_count; width=5; reset=0.",
      "evidence_terms": [],
      "id": "RTL-0115",
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.state_variables.mfifo_count",
      "ssot_context": {
        "name": "mfifo_count",
        "reset": "0",
        "width": "5"
      },
      "ssot_refs": [
        "function_model.state_variables.mfifo_count"
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
        "reason": "Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.",
        "required": true,
        "status": "pass"
      }
    },
    {
      "category": "function_model.state_variable",
      "content": "Implement RTL state owner for FL state irq_status",
      "criteria": [
        "State has a flop/register/memory owner in RTL",
        "Reset value matches SSOT",
        "Every transaction update occurs at the SSOT-defined acceptance/cycle point",
        "Traceability keeps source_ref function_model.state_variables.irq_status",
        "Primary implementation evidence is in rtl/pl330_target_mfifo.sv",
        "irq_status width matches SSOT value 32",
        "irq_status reset behavior matches SSOT value 0"
      ],
      "detail": "Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.\nSSOT ref: function_model.state_variables.irq_status.\nOwner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.state_variables.\nSSOT item context: name=irq_status; width=32; reset=0.",
      "evidence_terms": [],
      "id": "RTL-0116",
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.state_variables.irq_status",
      "ssot_context": {
        "name": "irq_status",
        "reset": "0",
        "width": "32"
      },
      "ssot_refs": [
        "function_model.state_variables.irq_status"
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
        "reason": "Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.",
        "required": true,
        "status": "pass"
      }
    },
    {
      "category": "function_model.state_variable",
      "content": "Implement RTL state owner for FL state fault_status",
      "criteria": [
        "State has a flop/register/memory owner in RTL",
        "Reset value matches SSOT",
        "Every transaction update occurs at the SSOT-defined acceptance/cycle point",
        "Traceability keeps source_ref function_model.state_variables.fault_status",
        "Primary implementation evidence is in rtl/pl330_target_mfifo.sv",
        "fault_status width matches SSOT value 32",
        "fault_status reset behavior matches SSOT value 0"
      ],
      "detail": "Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.\nSSOT ref: function_model.state_variables.fault_status.\nOwner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.state_variables.\nSSOT item context: name=fault_status; width=32; reset=0.",
      "evidence_terms": [],
      "id": "RTL-0117",
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.state_variables.fault_status",
      "ssot_context": {
        "name": "fault_status",
        "reset": "0",
        "width": "32"
      },
      "ssot_refs": [
        "function_model.state_variables.fault_status"
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
        "reason": "Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.",
        "required": true,
        "status": "pass"
      }
    },
    {
      "category": "function_model.transaction",
      "content": "Implement transaction FM_RESET",
      "criteria": [
        "Acceptance/precondition logic is explicit in RTL",
        "All outputs and side effects occur exactly once per accepted transaction",
        "The transaction is covered by equivalence goals and scoreboard observations downstream",
        "Traceability keeps source_ref function_model.transactions.FM_RESET",
        "Primary implementation evidence is in rtl/pl330_target_mfifo.sv"
      ],
      "detail": "Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.\nSSOT ref: function_model.transactions.FM_RESET.\nOwner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_RESET.\nSSOT item context: id=FM_RESET; name=reset.",
      "evidence_terms": [],
      "id": "RTL-0118",
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM_RESET",
      "ssot_context": {
        "id": "FM_RESET",
        "name": "reset"
      },
      "ssot_refs": [
        "function_model.transactions.FM_RESET"
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
      "category": "function_model.precondition",
      "content": "Implement precondition for FM_RESET: precondition_0",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM_RESET.preconditions.precondition_0",
        "Primary implementation evidence is in rtl/pl330_target_mfifo.sv"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM_RESET.preconditions.precondition_0.\nOwner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_RESET.\nSSOT item context: value=transaction is accepted under cycle_model rules.",
      "evidence_terms": [],
      "id": "RTL-0119",
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM_RESET.preconditions.precondition_0",
      "ssot_context": {
        "value": "transaction is accepted under cycle_model rules"
      },
      "ssot_refs": [
        "function_model.transactions.FM_RESET.preconditions.precondition_0"
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
      "category": "function_model.output",
      "content": "Implement output for FM_RESET: output_0",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM_RESET.outputs.output_0",
        "Primary implementation evidence is in rtl/pl330_target_mfifo.sv"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM_RESET.outputs.output_0.\nOwner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_RESET.\nSSOT item context: value=all state -> reset values.",
      "evidence_terms": [],
      "id": "RTL-0120",
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM_RESET.outputs.output_0",
      "ssot_context": {
        "value": "all state -> reset values"
      },
      "ssot_refs": [
        "function_model.transactions.FM_RESET.outputs.output_0"
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
      "category": "function_model.side_effect",
      "content": "Implement side effect for FM_RESET: side_effect_0",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM_RESET.side_effects.side_effect_0",
        "Primary implementation evidence is in rtl/pl330_target_mfifo.sv"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM_RESET.side_effects.side_effect_0.\nOwner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_RESET.\nSSOT item context: value=outstanding_reads=0.",
      "evidence_terms": [
        "outstanding",
        "outstanding_reads",
        "reads"
      ],
      "id": "RTL-0121",
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM_RESET.side_effects.side_effect_0",
      "ssot_context": {
        "value": "outstanding_reads=0"
      },
      "ssot_refs": [
        "function_model.transactions.FM_RESET.side_effects.side_effect_0"
      ],
      "static_evidence": {
        "matched_count": 3,
        "matched_terms": [
          "outstanding",
          "outstanding_reads",
          "reads"
        ],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "outstanding",
          "outstanding_reads",
          "reads"
        ],
        "source_scope": "rtl/pl330_target_mfifo.sv",
        "status": "pass"
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
      "category": "function_model.side_effect",
      "content": "Implement side effect for FM_RESET: side_effect_1",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM_RESET.side_effects.side_effect_1",
        "Primary implementation evidence is in rtl/pl330_target_mfifo.sv"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM_RESET.side_effects.side_effect_1.\nOwner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_RESET.\nSSOT item context: value=outstanding_writes=0.",
      "evidence_terms": [
        "outstanding",
        "outstanding_writes",
        "writes"
      ],
      "id": "RTL-0122",
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM_RESET.side_effects.side_effect_1",
      "ssot_context": {
        "value": "outstanding_writes=0"
      },
      "ssot_refs": [
        "function_model.transactions.FM_RESET.side_effects.side_effect_1"
      ],
      "static_evidence": {
        "matched_count": 3,
        "matched_terms": [
          "outstanding",
          "outstanding_writes",
          "writes"
        ],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "outstanding",
          "outstanding_writes",
          "writes"
        ],
        "source_scope": "rtl/pl330_target_mfifo.sv",
        "status": "pass"
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
      "category": "function_model.side_effect",
      "content": "Implement side effect for FM_RESET: side_effect_2",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM_RESET.side_effects.side_effect_2",
        "Primary implementation evidence is in rtl/pl330_target_mfifo.sv"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM_RESET.side_effects.side_effect_2.\nOwner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_RESET.\nSSOT item context: value=mfifo_count=0.",
      "evidence_terms": [
        "count",
        "mfifo",
        "mfifo_count"
      ],
      "id": "RTL-0123",
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM_RESET.side_effects.side_effect_2",
      "ssot_context": {
        "value": "mfifo_count=0"
      },
      "ssot_refs": [
        "function_model.transactions.FM_RESET.side_effects.side_effect_2"
      ],
      "static_evidence": {
        "matched_count": 3,
        "matched_terms": [
          "count",
          "mfifo",
          "mfifo_count"
        ],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "count",
          "mfifo",
          "mfifo_count"
        ],
        "source_scope": "rtl/pl330_target_mfifo.sv",
        "status": "pass"
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
      "category": "function_model.side_effect",
      "content": "Implement side effect for FM_RESET: side_effect_3",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM_RESET.side_effects.side_effect_3",
        "Primary implementation evidence is in rtl/pl330_target_mfifo.sv"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM_RESET.side_effects.side_effect_3.\nOwner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_RESET.\nSSOT item context: value=irq_status=0.",
      "evidence_terms": [
        "irq",
        "irq_status",
        "status"
      ],
      "id": "RTL-0124",
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM_RESET.side_effects.side_effect_3",
      "ssot_context": {
        "value": "irq_status=0"
      },
      "ssot_refs": [
        "function_model.transactions.FM_RESET.side_effects.side_effect_3"
      ],
      "static_evidence": {
        "matched_count": 3,
        "matched_terms": [
          "irq",
          "irq_status",
          "status"
        ],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "irq",
          "irq_status",
          "status"
        ],
        "source_scope": "rtl/pl330_target_mfifo.sv",
        "status": "pass"
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
      "category": "function_model.transaction",
      "content": "Implement transaction FM_DMAGO",
      "criteria": [
        "Acceptance/precondition logic is explicit in RTL",
        "All outputs and side effects occur exactly once per accepted transaction",
        "The transaction is covered by equivalence goals and scoreboard observations downstream",
        "Traceability keeps source_ref function_model.transactions.FM_DMAGO",
        "Primary implementation evidence is in rtl/pl330_target_mfifo.sv"
      ],
      "detail": "Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.\nSSOT ref: function_model.transactions.FM_DMAGO.\nOwner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMAGO.\nSSOT item context: id=FM_DMAGO; name=dmago_command.",
      "evidence_terms": [],
      "id": "RTL-0125",
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM_DMAGO",
      "ssot_context": {
        "id": "FM_DMAGO",
        "name": "dmago_command"
      },
      "ssot_refs": [
        "function_model.transactions.FM_DMAGO"
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
      "category": "function_model.precondition",
      "content": "Implement precondition for FM_DMAGO: precondition_0",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM_DMAGO.preconditions.precondition_0",
        "Primary implementation evidence is in rtl/pl330_target_mfifo.sv"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM_DMAGO.preconditions.precondition_0.\nOwner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMAGO.\nSSOT item context: value=channel_state==0.",
      "evidence_terms": [
        "channel",
        "channel_state"
      ],
      "id": "RTL-0126",
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM_DMAGO.preconditions.precondition_0",
      "ssot_context": {
        "value": "channel_state==0"
      },
      "ssot_refs": [
        "function_model.transactions.FM_DMAGO.preconditions.precondition_0"
      ],
      "static_evidence": {
        "matched_count": 2,
        "matched_terms": [
          "channel",
          "channel_state"
        ],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "channel",
          "channel_state"
        ],
        "source_scope": "rtl/pl330_target_mfifo.sv",
        "status": "pass"
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
      "category": "function_model.precondition",
      "content": "Implement precondition for FM_DMAGO: precondition_1",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM_DMAGO.preconditions.precondition_1",
        "Primary implementation evidence is in rtl/pl330_target_mfifo.sv"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM_DMAGO.preconditions.precondition_1.\nOwner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMAGO.\nSSOT item context: value=manager APB write to DBGINST.",
      "evidence_terms": [],
      "id": "RTL-0127",
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM_DMAGO.preconditions.precondition_1",
      "ssot_context": {
        "value": "manager APB write to DBGINST"
      },
      "ssot_refs": [
        "function_model.transactions.FM_DMAGO.preconditions.precondition_1"
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
      "category": "function_model.output",
      "content": "Implement output for FM_DMAGO: output_0",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM_DMAGO.outputs.output_0",
        "Primary implementation evidence is in rtl/pl330_target_mfifo.sv"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM_DMAGO.outputs.output_0.\nOwner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMAGO.\nSSOT item context: value=channel_state=1.",
      "evidence_terms": [
        "channel",
        "channel_state"
      ],
      "id": "RTL-0128",
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM_DMAGO.outputs.output_0",
      "ssot_context": {
        "value": "channel_state=1"
      },
      "ssot_refs": [
        "function_model.transactions.FM_DMAGO.outputs.output_0"
      ],
      "static_evidence": {
        "matched_count": 2,
        "matched_terms": [
          "channel",
          "channel_state"
        ],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "channel",
          "channel_state"
        ],
        "source_scope": "rtl/pl330_target_mfifo.sv",
        "status": "pass"
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
      "category": "function_model.output",
      "content": "Implement output for FM_DMAGO: output_1",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM_DMAGO.outputs.output_1",
        "Primary implementation evidence is in rtl/pl330_target_mfifo.sv"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM_DMAGO.outputs.output_1.\nOwner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMAGO.\nSSOT item context: value=channel_pc=arg_addr.",
      "evidence_terms": [
        "addr",
        "arg",
        "arg_addr",
        "channel",
        "channel_pc",
        "pc"
      ],
      "id": "RTL-0129",
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM_DMAGO.outputs.output_1",
      "ssot_context": {
        "value": "channel_pc=arg_addr"
      },
      "ssot_refs": [
        "function_model.transactions.FM_DMAGO.outputs.output_1"
      ],
      "static_evidence": {
        "matched_count": 5,
        "matched_terms": [
          "addr",
          "arg",
          "channel",
          "channel_pc",
          "pc"
        ],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "addr",
          "arg",
          "arg_addr",
          "channel",
          "channel_pc",
          "pc"
        ],
        "source_scope": "rtl/pl330_target_mfifo.sv",
        "status": "pass"
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
      "category": "function_model.error_case",
      "content": "Implement error case for FM_DMAGO: error_case_0",
      "criteria": [
        "RTL owner logic is identifiable for this SSOT leaf",
        "Reset/enable/error behavior is consistent with the parent transaction",
        "Downstream equivalence/coverage can observe this behavior",
        "Traceability keeps source_ref function_model.transactions.FM_DMAGO.error_cases.error_case_0",
        "Primary implementation evidence is in rtl/pl330_target_mfifo.sv",
        "function_model.transactions.FM_DMAGO.error_cases.error_case_0 condition is implemented as RTL control logic: secure violation"
      ],
      "detail": "This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.\nSSOT ref: function_model.transactions.FM_DMAGO.error_cases.error_case_0.\nOwner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMAGO.\nSSOT item context: condition=secure violation.",
      "evidence_terms": [],
      "id": "RTL-0130",
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "priority": "high",
      "required": true,
      "source_ref": "function_model.transactions.FM_DMAGO.error_cases.error_case_0",
      "ssot_context": {
        "condition": "secure violation"
      },
      "ssot_refs": [
        "function_model.transactions.FM_DMAGO.error_cases.error_case_0"
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
        "reason": "Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.",
        "required": true,
        "status": "pass"
      }
    },
    {
      "category": "function_model.transaction",
      "content": "Implement transaction FM_DMALD",
      "criteria": [
        "Acceptance/precondition logic is explicit in RTL",
        "All outputs and side effects occur exactly once per accepted transaction",
        "The transaction is covered by equivalence goals and scoreboard observations downstream",
        "Traceability keeps source_ref function_model.transactions.FM_DMALD",
        "Primary implementation evidence is in rtl/pl330_target_mfifo.sv"
      ],
      "detail": "Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.\nSSOT ref: function_model.transactions.FM_DMALD.\nOwner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMALD.\nSSOT item context: id=FM_DMALD; name=dmald_load.",
      "evidence_t
... <truncated 57372 chars>

Current packet Markdown (rtl/authoring_packets/module__pl330_target_mfifo__function_model_01.md):
# RTL Authoring Packet: module__pl330_target_mfifo__function_model_01

- Kind: module
- Owner module: pl330_target_mfifo
- Owner file: rtl/pl330_target_mfifo.sv
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
- Integration signoff allowed: True
- LLM-actionable open tasks: 2
- Human-locked open tasks: 0
- Owner refs: cycle_model.backpressure.mfifo_full, dataflow, features, fsm, function_model.state_variables, function_model.state_variables.mfifo, function_model.transactions.FM_DMAEND, function_model.transactions.FM_DMAGO, function_model.transactions.FM_DMALD, function_model.transactions.FM_DMALDP, function_model.transactions.FM_DMASEV, function_model.transactions.FM_DMAST, function_model.transactions.FM_DMASTP, function_model.transactions.FM_FAULT, function_model.transactions.FM_RESET, registers
- Module slice: 2/11 section=function_model task_limit=48
- Slice rule: Owner module pl330_target_mfifo is split into 11 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- Connection contract gap: Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.

## Tasks

### RTL-0111: Implement RTL state owner for FL state channel_state

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.channel_state
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.channel_state.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.state_variables.
SSOT item context: name=channel_state; width=4; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.channel_state
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - channel_state width matches SSOT value 4
  - channel_state reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.channel_state

### RTL-0112: Implement RTL state owner for FL state channel_pc

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.channel_pc
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.channel_pc.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.state_variables.
SSOT item context: name=channel_pc; width=32; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.channel_pc
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - channel_pc width matches SSOT value 32
  - channel_pc reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.channel_pc

### RTL-0113: Implement RTL state owner for FL state outstanding_reads

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.outstanding_reads
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.outstanding_reads.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.state_variables.
SSOT item context: name=outstanding_reads; width=4; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.outstanding_reads
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - outstanding_reads width matches SSOT value 4
  - outstanding_reads reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.outstanding_reads

### RTL-0114: Implement RTL state owner for FL state outstanding_writes

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.outstanding_writes
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.outstanding_writes.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.state_variables.
SSOT item context: name=outstanding_writes; width=4; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.outstanding_writes
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - outstanding_writes width matches SSOT value 4
  - outstanding_writes reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.outstanding_writes

### RTL-0115: Implement RTL state owner for FL state mfifo_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.mfifo_count
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.mfifo_count.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.state_variables.
SSOT item context: name=mfifo_count; width=5; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.mfifo_count
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - mfifo_count width matches SSOT value 5
  - mfifo_count reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.mfifo_count

### RTL-0116: Implement RTL state owner for FL state irq_status

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.irq_status
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.irq_status.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.state_variables.
SSOT item context: name=irq_status; width=32; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.irq_status
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - irq_status width matches SSOT value 32
  - irq_status reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.irq_status

### RTL-0117: Implement RTL state owner for FL state fault_status

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.fault_status
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.fault_status.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.state_variables.
SSOT item context: name=fault_status; width=32; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.fault_status
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - fault_status width matches SSOT value 32
  - fault_status reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.fault_status

### RTL-0118: Implement transaction FM_RESET

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_RESET
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_RESET.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_RESET.
SSOT item context: id=FM_RESET; name=reset.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_RESET
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_RESET

### RTL-0119: Implement precondition for FM_RESET: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_RESET.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.preconditions.precondition_0.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_RESET.
SSOT item context: value=transaction is accepted under cycle_model rules.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.preconditions.precondition_0
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_RESET.preconditions.precondition_0

### RTL-0120: Implement output for FM_RESET: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_RESET.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.outputs.output_0.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_RESET.
SSOT item context: value=all state -> reset values.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.outputs.output_0
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_RESET.outputs.output_0

### RTL-0121: Implement side effect for FM_RESET: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_RESET.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.side_effects.side_effect_0.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_RESET.
SSOT item context: value=outstanding_reads=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_RESET.side_effects.side_effect_0

### RTL-0122: Implement side effect for FM_RESET: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_RESET.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.side_effects.side_effect_1.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_RESET.
SSOT item context: value=outstanding_writes=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_RESET.side_effects.side_effect_1

### RTL-0123: Implement side effect for FM_RESET: side_effect_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_RESET.side_effects.side_effect_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.side_effects.side_effect_2.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_RESET.
SSOT item context: value=mfifo_count=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transa
... <truncated 38828 chars>