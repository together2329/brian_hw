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

Current packet: module__pl330_target_mfifo__fsm
kind: module
work queue: 1/4 active packets (24 closed packets skipped from 30 total)
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

    localparam [3:0] CH_IDLE       = 4'd0;
    localparam [3:0] CH_RUNNING    = 4'd1;
    localparam [3:0] CH_WAIT_READ  = 4'd2;
    localparam [3:0] CH_WAIT_WRITE = 4'd3;
    localparam [3:0] CH_FAULT      = 4'd15;

    localparam [7:0] OP_DMAEND = 8'h00;
    localparam [7:0] OP_DMALD  = 8'h04;
    localparam [7:0] OP_DMAST  = 8'h08;
    localparam [7:0] OP_DMALDP = 8'h25;
    localparam [7:0] OP_DMASTP = 8'h29;
    localparam [7:0] OP_DMASEV = 8'h34;
    localparam [7:0] OP_DMAGO  = 8'ha0;
    localparam [7:0] OP_FAULT  = 8'hff;

    localparam [4:0] FIFO_DEPTH_COUNT = 5'd16;
    localparam [4:0] FIFO_ALMOST_FULL_COUNT = 5'd15;

    logic [3:0]        channel_state;
    logic [ADDR_W-1:0] channel_pc;
    logic [3:0]        outstanding_reads;
    logic [3:0]        outstanding_writes;
    logic [4:0]        mfifo_count;
    logic [31:0]       irq_status;
    logic [31:0]       fault_status;

    logic [DATA_W-1:0] fifo_mem [0:FIFO_DEPTH-1];
    logic [3:0]        wr_ptr;
    logic [3:0]        rd_ptr;

    integer fifo_i;

    wire cmd_is_dmaend = (cmd_opcode_i == OP_DMAEND);
    wire cmd_is_dmald  = (cmd_opcode_i == OP_DMALD);
    wire cmd_is_dmast  = (cmd_opcode_i == OP_DMAST);
    wire cmd_is_dmaldp = (cmd_opcode_i == OP_DMALDP);
    wire cmd_is_dmastp = (cmd_opcode_i == OP_DMASTP);
    wire cmd_is_dmasev = (cmd_opcode_i == OP_DMASEV);
    wire cmd_is_dmago  = (cmd_opcode_i == OP_DMAGO);
    wire cmd_is_fault  = (cmd_opcode_i == OP_FAULT);
    wire cmd_is_known  = cmd_is_dmaend | cmd_is_dmald | cmd_is_dmast | cmd_is_dmaldp | cmd_is_dmastp | cmd_is_dmasev | cmd_is_dmago | cmd_is_fault;

    wire cmd_is_load   = cmd_is_dmald | cmd_is_dmaldp;
    wire cmd_is_store  = cmd_is_dmast | cmd_is_dmastp;
    wire channel_idle  = (channel_state == CH_IDLE);
    wire channel_live  = (channel_state == CH_RUNNING) | (channel_state == CH_WAIT_READ) | (channel_state == CH_WAIT_WRITE);
    wire fifo_full     = (mfifo_count == FIFO_DEPTH_COUNT);
    wire fifo_empty    = (mfifo_count == 5'd0);

    wire fifo_pop_store_pre = cmd_valid_i & cmd_is_store & channel_live & ~fifo_empty & (outstanding_writes != 4'd15) & st_req_ready_i;
    wire fifo_pop_ext_pre   = mfifo_pop_valid_i & ~fifo_empty & ~fifo_pop_store_pre;
    wire fifo_space_avail   = ~fifo_full | fifo_pop_store_pre | fifo_pop_ext_pre;

    wire load_backpressure  = (outstanding_reads == 4'd15) | (mfifo_count >= FIFO_ALMOST_FULL_COUNT) | ~ld_req_ready_i;
    wire store_backpressure = fifo_empty | (outstanding_writes == 4'd15) | ~st_req_ready_i;

    assign cmd_ready_o = ~(cmd_valid_i & ((cmd_is_load & load_backpressure) | (cmd_is_store & store_backpressure)));

    wire cmd_accept = cmd_valid_i & cmd_ready_o;
    wire secure_violation = cmd_accept & ~cmd_secure_i & ~cfg_nonsecure_allowed_i;

    wire dmago_pre_ok = channel_idle & dbginst_write_i & cmd_manager_i;
    wire dmago_accept = cmd_accept & cmd_is_dmago & dmago_pre_ok & ~secure_violation;
    wire dmago_fault  = cmd_accept & cmd_is_dmago & (~dmago_pre_ok | secure_violation);

    wire load_pre_ok  = channel_live & ~load_backpressure;
    wire dmald_accept = cmd_accept & cmd_is_dmald  & load_pre_ok & ~secure_violation;
    wire dmaldp_accept= cmd_accept & cmd_is_dmaldp & load_pre_ok & ~secure_violation;
    wire load_fault   = cmd_accept & cmd_is_load & (~load_pre_ok | secure_violation);

    wire store_pre_ok = channel_live & ~store_backpressure;
    wire dmast_accept = cmd_accept & cmd_is_dmast  & store_pre_ok & ~secure_violation;
    wire dmastp_accept= cmd_accept & cmd_is_dmastp & store_pre_ok & ~secure_violation;
    wire store_fault  = cmd_accept & cmd_is_store & (~store_pre_ok | secure_violation);

    wire dmasev_pre_ok = channel_live;
    wire dmasev_accept = cmd_accept & cmd_is_dmasev & dmasev_pre_ok & ~secure_violation;
    wire dmasev_fault  = cmd_accept & cmd_is_dmasev & (~dmasev_pre_ok | secure_violation);

    wire dmaend_accept = cmd_accept & cmd_is_dmaend & channel_live & ~secure_violation;
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

    wire fifo_push_rsp = ld_rsp_valid_i & ld_rsp_ready_o & ~ld_rsp_error_i;
    assign mfifo_push_ready_o = fifo_space_avail & ~(ld_rsp_valid_i & ~ld_rsp_error_i);
    wire fifo_push_ext = mfifo_push_valid_i & mfifo_push_ready_o;
    wire fifo_push = fifo_push_rsp | fifo_push_ext;
    wire [DATA_W-1:0] fifo_push_data = fifo_push_rsp ? ld_rsp_data_i : mfifo_push_data_i;

    wire fifo_pop_store = st_req_fire;
    assign mfifo_pop_ready_o = ~fifo_empty & ~fifo_pop_store;
    wire fifo_pop_ext = mfifo_pop_valid_i & mfifo_pop_ready_o;
    wire fifo_pop = fifo_pop_store | fifo_pop_ext;

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
            channel_state <= CH_IDLE;
            channel_pc <= {ADDR_W{1'b0}};
            outstanding_reads <= 4'd0;
            outstanding_writes <= 4'd0;
            mfifo_count <= 5'd0;
            irq_status <= 32'h00000000;
            fault_status <= 32'h00000000;
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
                // Trace: function_model.transactions.FM_RESET and precondition accepted under cycle_model rules.
                // Trace: function_model.transactions.FM_RESET.outputs.output_0 all state -> reset values.
                channel_state <= CH_IDLE;
                channel_pc <= {ADDR_W{1'b0}};
                outstanding_reads <= 4'd0;
                outstanding_writes <= 4'd0;
                mfifo_count <= 5'd0;
                irq_status <= 32'h00000000;
                fault_status <= 32'h00000000;
                wr_ptr <= 4'd0;
                rd_ptr <= 4'd0;
                reset_accepted_o <= 1'b1;
                for (fifo_i = 0; fifo_i < FIFO_DEPTH; fifo_i = fifo_i + 1) begin
                    fifo_mem[fifo_i] <= {DATA_W{1'b0}};
                end
            end else begin
                // Trace: function_model.state_variables.outstanding_reads and outstanding_writes update at request and response acceptance.
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
                    if ((fault_status & ~fault_clear_i) == 32'h00000000 && channel_state == CH_FAULT) begin
                        channel_state <= CH_IDLE;
                    end
                end

                if (cmd_accept) begin
                    cmd_accept_o <= 1'b1;
                end

                if (dmago_accept) begin
                    // Trace: function_model.transactions.FM_DMAGO preconditions channel_state==0 and manager APB write to DBGINST.
                    // Trace: function_model.transactions.FM_DMAGO.outputs channel_state=1 and channel_pc=arg_addr.
                    channel_state <= CH_RUNNING;
                    channel_pc <= cmd_arg_addr_i;
                end

                if (dmald_accept | dmaldp_accept) begin
                    // Trace: function_model.transactions.FM_DMALD and FM_DMALDP issue one load request when channel is active and MFIFO has space.
                    channel_state <= CH_WAIT_READ;
                    channel_pc <= next_pc_value;
                end

                if (dmast_accept | dmastp_accept) begin
                    // Trace: function_model.transactions.FM_DMAST and FM_DMASTP issue one store request and consume one MFIFO entry.
                    channel_state <= CH_WAIT_WRITE;
                    channel_pc <= next_pc_value;
                end

                if (dmasev_accept) begin
                    // Trace: function_model.transactions.FM_DMASEV sets irq_status[event] once per accepted command.
                    channel_state <= CH_RUNNING;
                    irq_status[cmd_event_i] <= 1'b1;
                    channel_pc <= next_pc_value;
                end

                if (dmaend_accept) begin
                    channel_state <= CH_IDLE;
                    channel_pc <= next_pc_value;
                end

                if (ld_rsp_fire && !ld_rsp_error_i && channel_state == CH_WAIT_READ) begin
                    if (outstanding_reads <= 4'd1) begin
                        channel_state <= CH_RUNNING;
                    end
                end

                if (st_rsp_fire && !st_rsp_error_i && channel_state == CH_WAIT_WRITE) begin
                    if (outstanding_writes <= 4'd1) begin
                        channel_state <= CH_RUNNING;
                    end
                end

                if (dmago_fault) begin
                    // Trace: function_model.transactions.FM_DMAGO.error_cases.error_case_0 secure violation is reported in RTL control logic.
                    channel_state <= CH_FAULT;
                    fault_status[0] <= secure_violation;
                    fault_status[1] <= ~dmago_pre_ok;
                    cmd_error_o <= 1'b1;
                    cmd_fault_code_o <= secure_violation ? 8'h10 : 8'h11;
                    fault_valid_o <= 1'b1;
                end

                if (load_fault) begin
                    channel_state <= CH_FAULT;
                    fault_status[2] <= secure_violation;
                    fault_status[3] <= ~load_pre_ok;
                    cmd_error_o <= 1'b1;
                    cmd_fault_code_o <= secure_violation ? 8'h10 : 8'h21;
                    fault_valid_o <= 1'b1;
                end

                if (store_fault) begin
                    channel_state <= CH_FAULT;
                    fault_status[4] <= secure_violation;
                    fault_status[5] <= ~store_pre_ok;
                    cmd_error_o <= 1'b1;
                    cmd_fault_code_o <= secure_violation ? 8'h10 : 8'h31;
                    fault_valid_o <= 1'b1;
                end

                if (dmasev_fault) begin
                    channel_state <= CH_FAULT;
                    fault_status[6] <= secure_violation;
                    fault_status[7] <= ~dmasev_pre_ok;
                    cmd_error_o <= 1'b1;
                    cmd_fault_code_o <= secure_violation ? 8'h10 : 8'h41;
                    fault_valid_o <= 1'b1;
                end

                if (explicit_fault_accept) begin
                    channel_state <= CH_FAULT;
                    fault_status[8] <= 1'b1;
                    fault_status[15:8] <= cmd_arg_data_i[7:0];
                    cmd_error_o <= 1'b1;
                    cmd_fault_code_o <= cmd_arg_data_i[7:0];
                    fault_valid_o <= 1'b1;
                end

                if (illegal_fault_accept) begin
                    channel_state <= CH_FAULT;
                    fault_status[9] <= 1'b1;
                    cmd_error_o <= 1'b1;
                    cmd_fault_code_o <= 8'hf0;
                    fault_valid_o <= 1'b1;
                end

                if (ld_rsp_fire && ld_rsp_error_i) begin
                    channel_state <= CH_FAULT;
                    fault_status[10] <= 1'b1;
                    cmd_error_o <= 1'b1;
                    cmd_fault_code_o <= 8'h52;
                    fault_valid_o <= 1'b1;
                end

                if (st_rsp_fire && st_rsp_error_i) begin
                    channel_state <= CH_FAULT;
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


Current packet JSON (rtl/authoring_packets/module__pl330_target_mfifo__fsm.json):
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
      "index": 4,
      "key": "fsm",
      "module_task_count": 140,
      "rule": "Owner module pl330_target_mfifo is split into 11 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.",
      "section": "fsm",
      "section_chunk_count": 1,
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
    "llm_actionable_open_count": 24,
    "open_required_count": 24,
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
  "packet_id": "module__pl330_target_mfifo__fsm",
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
      "fsm.state": 10,
      "fsm.transition": 14
    },
    "module_slice": {
      "count": 11,
      "enabled": true,
      "index": 4,
      "key": "fsm",
      "module_task_count": 140,
      "rule": "Owner module pl330_target_mfifo is split into 11 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.",
      "section": "fsm",
      "section_chunk_count": 1,
      "section_chunk_index": 1,
      "task_limit": 48
    },
    "open_required_count": 24,
    "required_count": 24,
    "source_refs": [
      "fsm.channel_state.states.state_0",
      "fsm.channel_state.states.state_1",
      "fsm.channel_state.states.state_2",
      "fsm.channel_state.states.state_3",
      "fsm.channel_state.states.state_4",
      "fsm.channel_state.states.state_5",
      "fsm.channel_state.states.state_6",
      "fsm.channel_state.states.state_7",
      "fsm.channel_state.states.state_8",
      "fsm.channel_state.states.state_9",
      "fsm.channel_state.transitions.transition_0",
      "fsm.channel_state.transitions.transition_1",
      "fsm.channel_state.transitions.transition_2",
      "fsm.channel_state.transitions.transition_3",
      "fsm.channel_state.transitions.transition_4",
      "fsm.channel_state.transitions.transition_5",
      "fsm.channel_state.transitions.transition_6",
      "fsm.channel_state.transitions.transition_7",
      "fsm.channel_state.transitions.transition_8",
      "fsm.channel_state.transitions.transition_9",
      "fsm.channel_state.transitions.transition_10",
      "fsm.channel_state.transitions.transition_11",
      "fsm.channel_state.transitions.transition_12",
      "fsm.channel_state.transitions.transition_13"
    ],
    "status_counts": {
      "open": 24
    },
    "task_count": 24
  },
  "tasks": [
    {
      "category": "fsm.state",
      "content": "Implement FSM state channel_state.state_0",
      "criteria": [
        "State is encoded/reachable or explicitly replaced by equivalent logic",
        "Reset/entry/exit behavior matches SSOT",
        "Coverage can observe the state or equivalent condition",
        "Traceability keeps source_ref fsm.channel_state.states.state_0",
        "Primary implementation evidence is in rtl/pl330_target_mfifo.sv"
      ],
      "detail": "Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation.\nSSOT ref: fsm.channel_state.states.state_0.\nOwner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.\nSSOT item context: value=STOPPED.",
      "evidence_terms": [
        "STOPPED"
      ],
      "id": "RTL-0215",
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "priority": "high",
      "required": true,
      "source_ref": "fsm.channel_state.states.state_0",
      "ssot_context": {
        "value": "STOPPED"
      },
      "ssot_refs": [
        "fsm.channel_state.states.state_0"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 1,
        "required_terms": [
          "STOPPED"
        ],
        "source_scope": "rtl/pl330_target_mfifo.sv",
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
      "category": "fsm.state",
      "content": "Implement FSM state channel_state.state_1",
      "criteria": [
        "State is encoded/reachable or explicitly replaced by equivalent logic",
        "Reset/entry/exit behavior matches SSOT",
        "Coverage can observe the state or equivalent condition",
        "Traceability keeps source_ref fsm.channel_state.states.state_1",
        "Primary implementation evidence is in rtl/pl330_target_mfifo.sv"
      ],
      "detail": "Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation.\nSSOT ref: fsm.channel_state.states.state_1.\nOwner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.\nSSOT item context: value=EXECUTING.",
      "evidence_terms": [
        "EXECUTING"
      ],
      "id": "RTL-0216",
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "priority": "high",
      "required": true,
      "source_ref": "fsm.channel_state.states.state_1",
      "ssot_context": {
        "value": "EXECUTING"
      },
      "ssot_refs": [
        "fsm.channel_state.states.state_1"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 1,
        "required_terms": [
          "EXECUTING"
        ],
        "source_scope": "rtl/pl330_target_mfifo.sv",
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
      "category": "fsm.state",
      "content": "Implement FSM state channel_state.state_2",
      "criteria": [
        "State is encoded/reachable or explicitly replaced by equivalent logic",
        "Reset/entry/exit behavior matches SSOT",
        "Coverage can observe the state or equivalent condition",
        "Traceability keeps source_ref fsm.channel_state.states.state_2",
        "Primary implementation evidence is in rtl/pl330_target_mfifo.sv"
      ],
      "detail": "Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation.\nSSOT ref: fsm.channel_state.states.state_2.\nOwner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.\nSSOT item context: value=CACHE_MISS.",
      "evidence_terms": [
        "CACHE_MISS"
      ],
      "id": "RTL-0217",
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "priority": "high",
      "required": true,
      "source_ref": "fsm.channel_state.states.state_2",
      "ssot_context": {
        "value": "CACHE_MISS"
      },
      "ssot_refs": [
        "fsm.channel_state.states.state_2"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 1,
        "required_terms": [
          "CACHE_MISS"
        ],
        "source_scope": "rtl/pl330_target_mfifo.sv",
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
      "category": "fsm.state",
      "content": "Implement FSM state channel_state.state_3",
      "criteria": [
        "State is encoded/reachable or explicitly replaced by equivalent logic",
        "Reset/entry/exit behavior matches SSOT",
        "Coverage can observe the state or equivalent condition",
        "Traceability keeps source_ref fsm.channel_state.states.state_3",
        "Primary implementation evidence is in rtl/pl330_target_mfifo.sv"
      ],
      "detail": "Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation.\nSSOT ref: fsm.channel_state.states.state_3.\nOwner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.\nSSOT item context: value=UPDATING_PC.",
      "evidence_terms": [
        "UPDATING_PC"
      ],
      "id": "RTL-0218",
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "priority": "high",
      "required": true,
      "source_ref": "fsm.channel_state.states.state_3",
      "ssot_context": {
        "value": "UPDATING_PC"
      },
      "ssot_refs": [
        "fsm.channel_state.states.state_3"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 1,
        "required_terms": [
          "UPDATING_PC"
        ],
        "source_scope": "rtl/pl330_target_mfifo.sv",
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
      "category": "fsm.state",
      "content": "Implement FSM state channel_state.state_4",
      "criteria": [
        "State is encoded/reachable or explicitly replaced by equivalent logic",
        "Reset/entry/exit behavior matches SSOT",
        "Coverage can observe the state or equivalent condition",
        "Traceability keeps source_ref fsm.channel_state.states.state_4",
        "Primary implementation evidence is in rtl/pl330_target_mfifo.sv"
      ],
      "detail": "Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation.\nSSOT ref: fsm.channel_state.states.state_4.\nOwner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.\nSSOT item context: value=WAITING_FOR_EVENT.",
      "evidence_terms": [
        "WAITING_FOR_EVENT"
      ],
      "id": "RTL-0219",
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "priority": "high",
      "required": true,
      "source_ref": "fsm.channel_state.states.state_4",
      "ssot_context": {
        "value": "WAITING_FOR_EVENT"
      },
      "ssot_refs": [
        "fsm.channel_state.states.state_4"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 1,
        "required_terms": [
          "WAITING_FOR_EVENT"
        ],
        "source_scope": "rtl/pl330_target_mfifo.sv",
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
      "category": "fsm.state",
      "content": "Implement FSM state channel_state.state_5",
      "criteria": [
        "State is encoded/reachable or explicitly replaced by equivalent logic",
        "Reset/entry/exit behavior matches SSOT",
        "Coverage can observe the state or equivalent condition",
        "Traceability keeps source_ref fsm.channel_state.states.state_5",
        "Primary implementation evidence is in rtl/pl330_target_mfifo.sv"
      ],
      "detail": "Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation.\nSSOT ref: fsm.channel_state.states.state_5.\nOwner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.\nSSOT item context: value=AT_BARRIER.",
      "evidence_terms": [
        "AT_BARRIER"
      ],
      "id": "RTL-0220",
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "priority": "high",
      "required": true,
      "source_ref": "fsm.channel_state.states.state_5",
      "ssot_context": {
        "value": "AT_BARRIER"
      },
      "ssot_refs": [
        "fsm.channel_state.states.state_5"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 1,
        "required_terms": [
          "AT_BARRIER"
        ],
        "source_scope": "rtl/pl330_target_mfifo.sv",
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
      "category": "fsm.state",
      "content": "Implement FSM state channel_state.state_6",
      "criteria": [
        "State is encoded/reachable or explicitly replaced by equivalent logic",
        "Reset/entry/exit behavior matches SSOT",
        "Coverage can observe the state or equivalent condition",
        "Traceability keeps source_ref fsm.channel_state.states.state_6",
        "Primary implementation evidence is in rtl/pl330_target_mfifo.sv"
      ],
      "detail": "Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation.\nSSOT ref: fsm.channel_state.states.state_6.\nOwner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.\nSSOT item context: value=KILLING.",
      "evidence_terms": [
        "KILLING"
      ],
      "id": "RTL-0221",
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "priority": "high",
      "required": true,
      "source_ref": "fsm.channel_state.states.state_6",
      "ssot_context": {
        "value": "KILLING"
      },
      "ssot_refs": [
        "fsm.channel_state.states.state_6"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 1,
        "required_terms": [
          "KILLING"
        ],
        "source_scope": "rtl/pl330_target_mfifo.sv",
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
      "category": "fsm.state",
      "content": "Implement FSM state channel_state.state_7",
      "criteria": [
        "State is encoded/reachable or explicitly replaced by equivalent logic",
        "Reset/entry/exit behavior matches SSOT",
        "Coverage can observe the state or equivalent condition",
        "Traceability keeps source_ref fsm.channel_state.states.state_7",
        "Primary implementation evidence is in rtl/pl330_target_mfifo.sv"
      ],
      "detail": "Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation.\nSSOT ref: fsm.channel_state.states.state_7.\nOwner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.\nSSOT item context: value=COMPLETING.",
      "evidence_terms": [
        "COMPLETING"
      ],
      "id": "RTL-0222",
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "priority": "high",
      "required": true,
      "source_ref": "fsm.channel_state.states.state_7",
      "ssot_context": {
        "value": "COMPLETING"
      },
      "ssot_refs": [
        "fsm.channel_state.states.state_7"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 1,
        "required_terms": [
          "COMPLETING"
        ],
        "source_scope": "rtl/pl330_target_mfifo.sv",
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
      "category": "fsm.state",
      "content": "Implement FSM state channel_state.state_8",
      "criteria": [
        "State is encoded/reachable or explicitly replaced by equivalent logic",
        "Reset/entry/exit behavior matches SSOT",
        "Coverage can observe the state or equivalent condition",
        "Traceability keeps source_ref fsm.channel_state.states.state_8",
        "Primary implementation evidence is in rtl/pl330_target_mfifo.sv"
      ],
      "detail": "Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation.\nSSOT ref: fsm.channel_state.states.state_8.\nOwner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.\nSSOT item context: value=FAULTING.",
      "evidence_terms": [
        "FAULTING"
      ],
      "id": "RTL-0223",
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "priority": "high",
      "required": true,
      "source_ref": "fsm.channel_state.states.state_8",
      "ssot_context": {
        "value": "FAULTING"
      },
      "ssot_refs": [
        "fsm.channel_state.states.state_8"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 1,
        "required_terms": [
          "FAULTING"
        ],
        "source_scope": "rtl/pl330_target_mfifo.sv",
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
      "category": "fsm.state",
      "content": "Implement FSM state channel_state.state_9",
      "criteria": [
        "State is encoded/reachable or explicitly replaced by equivalent logic",
        "Reset/entry/exit behavior matches SSOT",
        "Coverage can observe the state or equivalent condition",
        "Traceability keeps source_ref fsm.channel_state.states.state_9",
        "Primary implementation evidence is in rtl/pl330_target_mfifo.sv"
      ],
      "detail": "Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation.\nSSOT ref: fsm.channel_state.states.state_9.\nOwner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.\nSSOT item context: value=FAULTING_COMPLETING.",
      "evidence_terms": [
        "FAULTING_COMPLETING"
      ],
      "id": "RTL-0224",
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "priority": "high",
      "required": true,
      "source_ref": "fsm.channel_state.states.state_9",
      "ssot_context": {
        "value": "FAULTING_COMPLETING"
      },
      "ssot_refs": [
        "fsm.channel_state.states.state_9"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 1,
        "required_terms": [
          "FAULTING_COMPLETING"
        ],
        "source_scope": "rtl/pl330_target_mfifo.sv",
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
      "category": "fsm.transition",
      "content": "Implement FSM transition channel_state.transition_0",
      "criteria": [
        "Transition condition is present in RTL control logic",
        "Transition action/state update is implemented",
        "Illegal/missing transition behavior is handled per SSOT",
        "Traceability keeps source_ref fsm.channel_state.transitions.transition_0",
        "Primary implementation evidence is in rtl/pl330_target_mfifo.sv",
        "fsm.channel_state.transitions.transition_0 condition is implemented as RTL control logic: DMAGO + secure check pass",
        "fsm.channel_state.transitions.transition_0 transition path STOPPED -> EXECUTING is encoded or explicitly proven equivalent"
      ],
      "detail": "Transition condition, action, and timing must be implemented in RTL and covered downstream.\nSSOT ref: fsm.channel_state.transitions.transition_0.\nOwner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.\nSSOT item context: from=STOPPED; to=EXECUTING; condition=DMAGO + secure check pass.",
      "evidence_terms": [
        "DMAGO",
        "EXECUTING",
        "STOPPED"
      ],
      "id": "RTL-0225",
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "priority": "high",
      "required": true,
      "source_ref": "fsm.channel_state.transitions.transition_0",
      "ssot_context": {
        "condition": "DMAGO + secure check pass",
        "from": "STOPPED",
        "to": "EXECUTING"
      },
      "ssot_refs": [
        "fsm.channel_state.transitions.transition_0"
      ],
      "static_evidence": {
        "matched_count": 1,
        "matched_terms": [
          "DMAGO"
        ],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "DMAGO",
          "EXECUTING",
          "STOPPED"
        ],
        "source_scope": "rtl/pl330_target_mfifo.sv",
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
        "reason": "Required RTL static evidence is missing.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "fsm.transition",
      "content": "Implement FSM transition channel_state.transition_1",
      "criteria": [
        "Transition condition is present in RTL control logic",
        "Transition action/state update is implemented",
        "Illegal/missing transition behavior is handled per SSOT",
        "Traceability keeps source_ref fsm.channel_state.transitions.transition_1",
        "Primary implementation evidence is in rtl/pl330_target_mfifo.sv",
        "fsm.channel_state.transitions.transition_1 condition is implemented as RTL control logic: icache miss",
        "fsm.channel_state.transitions.transition_1 transition path EXECUTING -> CACHE_MISS is encoded or explicitly proven equivalent"
      ],
      "detail": "Transition condition, action, and timing must be implemented in RTL and covered downstream.\nSSOT ref: fsm.channel_state.transitions.transition_1.\nOwner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.\nSSOT item context: from=EXECUTING; to=CACHE_MISS; condition=icache miss.",
      "evidence_terms": [
        "CACHE_MISS",
        "EXECUTING"
      ],
      "id": "RTL-0226",
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "priority": "high",
      "required": true,
      "source_ref": "fsm.channel_state.transitions.transition_1",
      "ssot_context": {
        "condition": "icache miss",
        "from": "EXECUTING",
        "to": "CACHE_MISS"
      },
      "ssot_refs": [
        "fsm.channel_state.transitions.transition_1"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "CACHE_MISS",
          "EXECUTING"
        ],
        "source_scope": "rtl/pl330_target_mfifo.sv",
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
        "reason": "Required RTL static evidence is missing.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "fsm.transition",
      "content": "Implement FSM transition channel_state.transition_2",
      "criteria": [
        "Transition condition is present in RTL control logic",
        "Transition action/state update is implemented",
        "Illegal/missing transition behavior is handled per SSOT",
        "Traceability keeps source_ref fsm.channel_state.transitions.transition_2",
        "Primary implementation evidence is in rtl/pl330_target_mfifo.sv",
        "fsm.channel_state.transitions.transition_2 condition is implemented as RTL control logic: fill complete",
        "fsm.channel_state.transitions.transition_2 transition path CACHE_MISS -> EXECUTING is encoded or explicitly proven equivalent"
      ],
      "detail": "Transition condition, action, and timing must be implemented in RTL and covered downstream.\nSSOT ref: fsm.channel_state.transitions.transition_2.\nOwner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.\nSSOT item context: from=CACHE_MISS; to=EXECUTING; condition=fill complete.",
      "evidence_terms": [
        "CACHE_MISS",
        "EXECUTING"
      ],
      "id": "RTL-0227",
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "priority": "high",
      "required": true,
      "source_ref": "fsm.channel_state.transitions.transition_2",
      "ssot_context": {
        "condition": "fill complete",
        "from": "CACHE_MISS",
        "to": "EXECUTING"
      },
      "ssot_refs": [
        "fsm.channel_state.transitions.transition_2"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "CACHE_MISS",
          "EXECUTING"
        ],
        "source_scope": "rtl/pl330_target_mfifo.sv",
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
        "reason": "Required RTL static evidence is missing.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "fsm.transition",
      "content": "Implement FSM transition channel_state.transition_3",
      "criteria": [
        "Transition condition is present in RTL control logic",
        "Transition action/state update is implemented",
        "Illegal/missing transition behavior is handled per SSOT",
        "Traceability keeps source_ref fsm.channel_state.transitions.transition_3",
        "Primary implementation evidence is in rtl/pl330_target_mfifo.sv",
        "fsm.channel_state.transitions.transition_3 condition is implemented as RTL control logic: DMAWFE",
        "fsm.channel_state.transitions.transition_3 transition path EXECUTING -> WAITING_FOR_EVENT is encoded or explicitly proven equivalent"
      ],
      "detail": "Transition condition, action, and timing must be implemented in RTL and covered downstream.\nSSOT ref: fsm.channel_state.transitions.transition_3.\nOwner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.\nSSOT item context: from=EXECUTING; to=WAITING_FOR_EVENT; condition=DMAWFE.",
      "evidence_terms": [
        "DMAWFE",
        "EXECUTING",
        "WAITING_FOR_EVENT"
      ],
      "id": "RTL-0228",
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "priority": "high",
      "required": true,
      "source_ref": "fsm.channel_state.transitions.transition_3",
      "ssot_context": {
        "condition": "DMAWFE",
        "from": "EXECUTING",
        "to": "WAITING_FOR_EVENT"
      },
      "ssot_refs": [
        "fsm.channel_state.transitions.transition_3"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "DMAWFE",
          "EXECUTING",
          "WAITING_FOR_EVENT"
        ],
        "source_scope": "rtl/pl330_target_mfifo.sv",
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
        "reason": "Required RTL static evidence is missing.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "fsm.transition",
      "content": "Implement FSM transition channel_state.transition_4",
      "criteria": [
        "Transition condition is present in RTL control logic",
        "Transition action/state update is implemented",
        "Illegal/missing transition behavior is handled per SSOT",
        "Traceability keeps source_ref fsm.channel_state.transitions.transition_4",
        "Primary implementation evidence is in rtl/pl330_target_mfifo.sv",
        "fsm.channel_state.transitions.transition_4 condition is implemented as RTL control logic: event signaled",
        "fsm.channel_state.transitions.transition_4 transition path WAITING_FOR_EVENT -> EXECUTING is encoded or explicitly proven equivalent"
      ],
      "detail": "Transition condition, action, and timing must be implemented in RTL and covered downstream.\nSSOT ref: fsm.channel_state.transitions.transition_4.\nOwner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.\nSSOT item context: from=WAITING_FOR_EVENT; to=EXECUTING; condition=event signaled.",
      "evidence_terms": [
        "EXECUTING",
        "WAITING_FOR_EVENT"
      ],
      "id": "RTL-0229",
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "priority": "high",
      "required": true,
      "source_ref": "fsm.channel_state.transitions.transition_4",
      "ssot_context": {
        "condition": "event signaled",
        "from": "WAITING_FOR_EVENT",
        "to": "EXECUTING"
      },
      "ssot_refs": [
        "fsm.channel_state.transitions.transition_4"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "EXECUTING",
          "WAITING_FOR_EVENT"
        ],
        "source_scope": "rtl/pl330_target_mfifo.sv",
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
        "reason": "Required RTL static evidence is missing.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "fsm.transition",
      "content": "Implement FSM transition channel_state.transition_5",
      "criteria": [
        "Transition condition is present in RTL control logic",
        "Transition action/state update is implemented",
        "Illegal/missing transition behavior is handled per SSOT",
        "Traceability keeps source_ref fsm.channel_state.transitions.transition_5",
        "Primary implementation evidence is in rtl/pl330_target_mfifo.sv",
        "fsm.channel_state.transitions.transition_5 condition is implemented as RTL control logic: DMAWFP barrier",
        "fsm.channel_state.transitions.transition_5 transition path EXECUTING -> AT_BARRIER is encoded or explicitly proven equivalent"
      ],
      "detail": "Transition condition, action, and timing must be implemented in RTL and covered downstream.\nSSOT ref: fsm.channel_state.transitions.transition_5.\nOwner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.\nSSOT item context: from=EXECUTING; to=AT_BARRIER; condition=DMAWFP barrier.",
      "evidence_terms": [
        "AT_BARRIER",
        "DMAWFP",
        "EXECUTING"
      ],
      "id": "RTL-0230",
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "priority": "high",
      "required": true,
      "source_ref": "fsm.channel_state.transitions.transition_5",
      "ssot_context": {
        "condition": "DMAWFP barrier",
        "from": "EXECUTING",
        "to": "AT_BARRIER"
      },
      "ssot_refs": [
        "fsm.channel_state.transitions.transition_5"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "AT_BARRIER",
          "DMAWFP",
          "EXECUTING"
        ],
        "source_scope": "rtl/pl330_target_mfifo.sv",
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
        "reason": "Required RTL static evidence is missing.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "fsm.transition",
      "content": "Implement FSM transition channel_state.transition_6",
      "criteria": [
        "Transition condition is present in RTL control logic",
        "Transition action/state update is implemented",
        "Illegal/missing transition behavior is handled per SSOT",
        "Traceability keeps source_ref fsm.channel_state.transitions.transition_6",
        "Primary implementation evidence is in rtl/pl330_target_mfifo.sv",
        "fsm.channel_state.transitions.transition_6 condition is implemented as RTL control logic: barrier cleared",
        "fsm.channel_state.transitions.transition_6 transition path AT_BARRIER -> EXECUTING is encoded or explicitly proven equivalent"
      ],
      "detail": "Transition condition, action, and timing must be implemented in RTL and covered downstream.\nSSOT ref: fsm.channel_state.transitions.transition_6.\nOwner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.\nSSOT item context: from=AT_BARRIER; to=EXECUTING; condition=barrier cleared.",
      "evidence_terms": [
        "AT_BARRIER",
        "EXECUTING"
      ],
      "id": "RTL-0231",
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "priority": "high",
      "required": true,
      "source_ref": "fsm.channel_state.transitions.transition_6",
      "ssot_context": {
        "condition": "barrier cleared",
        "from": "AT_BARRIER",
        "to": "EXECUTING"
      },
      "ssot_refs": [
        "fsm.channel_state.transitions.transition_6"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "AT_BARRIER",
          "EXECUTING"
        ],
        "source_scope": "rtl/pl330_target_mfifo.sv",
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
        "reason": "Required RTL static evidence is missing.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "fsm.transition",
      "content": "Implement FSM transition channel_state.transition_7",
      "criteria": [
        "Transition condition is present in RTL control logic",
        "Transition action/state update is implemented",
        "Illegal/missing transition behavior is handled per SSOT",
        "Traceability keeps source_ref fsm.channel_state.transitions.transition_7",
        "Primary implementation evidence is in rtl/pl330_target_mfifo.sv",
        "fsm.channel_state.transitions.transition_7 condition is implemented as RTL control logic: DMAEND issued",
        "fsm.channel_state.transitions.transition_7 transition path EXECUTING -> COMPLETING is encoded or explicitly proven equivalent"
      ],
      "detail": "Transition condition, action, and timing must be implemented in RTL and covered downstream.\nSSOT ref: fsm.channel_state.transitions.transition_7.\nOwner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.\nSSOT item context: from=EXECUTING; to=COMPLETING; condition=DMAEND issued.",
      "evidence_terms": [
        "COMPLETING",
        "DMAEND",
        "EXECUTING"
      ],
      "id": "RTL-0232",
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "priority": "high",
      "required": true,
      "source_ref": "fsm.channel_state.transitions.transition_7",
      "ssot_context": {
        "condition": "DMAEND issued",
        "from": "EXECUTING",
        "to": "COMPLETING"
      },
      "ssot_refs": [
        "fsm.channel_state.transitions.transition_7"
      ],
      "static_evidence": {
        "matched_count": 1,
        "matched_terms": [
          "DMAEND"
        ],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "COMPLETING",
          "DMAEND",
          "EXECUTING"
        ],
        "source_scope": "rtl/pl330_target_mfifo.sv",
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
        "reason": "Required RTL static evidence is missing.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "fsm.transition",
      "content": "Implement FSM transition channel_state.transition_8",
      "criteria": [
        "Transition condition is present in RTL control logic",
        "Transition action/state update is implemented",
        "Illegal/missing transition behavior is handled per SSOT",
        "Traceability keeps source_ref fsm.channel_state.transitions.transition_8",
        "Primary implementation evidence is in rtl/pl330_target_mfifo.sv",
        "fsm.channel_state.transitions.transition_8 condition is implemented as RTL control logic: all outstanding drained",
        "fsm.channel_state.transitions.transition_8 transition path COMPLETING -> STOPPED is encoded or explicitly proven equivalent"
      ],
      "detail": "Transition condition, action, and timing must be implemented in RTL and covered downstream.\nSSOT ref: fsm.channel_state.transitions.transition_8.\nOwner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.\nSSOT item context: from=COMPLETING; to=STOPPED; condition=all outstanding drained.",
      "evidence_terms": [
        "COMPLETING",
        "STOPPED"
      ],
      "id": "RTL-0233",
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "priority": "high",
      "required": true,
      "source_ref": "fsm.channel_state.transitions.transition_8",
      "ssot_context": {
        "condition": "all outstanding drained",
        "from": "COMPLETING",
        "to": "STOPPED"
      },
      "ssot_refs": [
        "fsm.channel_state.transitions.transition_8"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "COMPLETING",
          "STOPPED"
        ],
        "source_scope": "rtl/pl330_target_mfifo.sv",
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
        "reason": "Required RTL static evidence is missing.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "fsm.transition",
      "content": "Implement FSM transition channel_state.transition_9",
      "criteria": [
        "Transition condition is present in RTL control logic",
        "Transition action/state update is implemented",
        "Illegal/missing transition behavior is handled per SSOT",
        "Traceability keeps source_ref fsm.channel_state.transitions.transition_9",
        "Primary implementation evidence is in rtl/pl330_target_mfifo.sv",
        "fsm.channel_state.transitions.transition_9 condition is implemented as RTL control logic: DMAKILL via DBGCMD",
        "fsm.channel_state.transitions.transition_9 transition path any -> KILLING is encoded or explicitly proven equivalent"
      ],
      "detail": "Transition condition, action, and timing must be implemented in RTL and covered downstream.\nSSOT ref: fsm.channel_state.transitions.transition_9.\nOwner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.\nSSOT item context: from=any; to=KILLING; condition=DMAKILL via DBGCMD.",
      "evidence_terms": [
        "DBGCMD",
        "DMAKILL",
        "KILLING"
      ],
      "id": "RTL-0234",
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "priority": "high",
      "required": true,
      "source_ref": "fsm.channel_state.transitions.transition_9",
      "ssot_context": {
        "condition": "DMAKILL via DBGCMD",
        "from": "any",
        "to": "KILLING"
      },
      "ssot_refs": [
        "fsm.channel_state.transitions.transition_9"
      ],
      "static_evidence": {
        "matched_count": 0,
        "matched_terms": [],
        "owner_file_scoped": true,
        "required": true,
        "required_match_count": 2,
        "required_terms": [
          "DBGCMD",
          "DMAKILL",
          "KILLING"
        ],
        "source_scope": "rtl/pl330_target_mfifo.sv",
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
        "reason": "Required RTL static evidence is missing.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "fsm.transition",
      "content": "Implement FSM transition channel_state.transition_10",
      "criteria": [
        "Transition condition is present in RTL control logic",
        "Transition action/st
... <truncated 9566 chars>

Current packet Markdown (rtl/authoring_packets/module__pl330_target_mfifo__fsm.md):
# RTL Authoring Packet: module__pl330_target_mfifo__fsm

- Kind: module
- Owner module: pl330_target_mfifo
- Owner file: rtl/pl330_target_mfifo.sv
- Task count: 24
- Required tasks: 24

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
- LLM-actionable open tasks: 24
- Human-locked open tasks: 0
- Owner refs: cycle_model.backpressure.mfifo_full, dataflow, features, fsm, function_model.state_variables, function_model.state_variables.mfifo, function_model.transactions.FM_DMAEND, function_model.transactions.FM_DMAGO, function_model.transactions.FM_DMALD, function_model.transactions.FM_DMALDP, function_model.transactions.FM_DMASEV, function_model.transactions.FM_DMAST, function_model.transactions.FM_DMASTP, function_model.transactions.FM_FAULT, function_model.transactions.FM_RESET, registers
- Module slice: 4/11 section=fsm task_limit=48
- Slice rule: Owner module pl330_target_mfifo is split into 11 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- Connection contract gap: Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.

## Tasks

### RTL-0215: Implement FSM state channel_state.state_0

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.channel_state.states.state_0
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation.
SSOT ref: fsm.channel_state.states.state_0.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.
SSOT item context: value=STOPPED.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.channel_state.states.state_0
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: fsm.channel_state.states.state_0

### RTL-0216: Implement FSM state channel_state.state_1

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.channel_state.states.state_1
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation.
SSOT ref: fsm.channel_state.states.state_1.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.
SSOT item context: value=EXECUTING.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.channel_state.states.state_1
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: fsm.channel_state.states.state_1

### RTL-0217: Implement FSM state channel_state.state_2

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.channel_state.states.state_2
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation.
SSOT ref: fsm.channel_state.states.state_2.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.
SSOT item context: value=CACHE_MISS.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.channel_state.states.state_2
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: fsm.channel_state.states.state_2

### RTL-0218: Implement FSM state channel_state.state_3

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.channel_state.states.state_3
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation.
SSOT ref: fsm.channel_state.states.state_3.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.
SSOT item context: value=UPDATING_PC.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.channel_state.states.state_3
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: fsm.channel_state.states.state_3

### RTL-0219: Implement FSM state channel_state.state_4

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.channel_state.states.state_4
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation.
SSOT ref: fsm.channel_state.states.state_4.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.
SSOT item context: value=WAITING_FOR_EVENT.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.channel_state.states.state_4
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: fsm.channel_state.states.state_4

### RTL-0220: Implement FSM state channel_state.state_5

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.channel_state.states.state_5
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation.
SSOT ref: fsm.channel_state.states.state_5.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.
SSOT item context: value=AT_BARRIER.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.channel_state.states.state_5
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: fsm.channel_state.states.state_5

### RTL-0221: Implement FSM state channel_state.state_6

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.channel_state.states.state_6
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation.
SSOT ref: fsm.channel_state.states.state_6.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.
SSOT item context: value=KILLING.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.channel_state.states.state_6
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: fsm.channel_state.states.state_6

### RTL-0222: Implement FSM state channel_state.state_7

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.channel_state.states.state_7
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation.
SSOT ref: fsm.channel_state.states.state_7.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.
SSOT item context: value=COMPLETING.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.channel_state.states.state_7
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: fsm.channel_state.states.state_7

### RTL-0223: Implement FSM state channel_state.state_8

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.channel_state.states.state_8
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation.
SSOT ref: fsm.channel_state.states.state_8.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.
SSOT item context: value=FAULTING.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.channel_state.states.state_8
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: fsm.channel_state.states.state_8

### RTL-0224: Implement FSM state channel_state.state_9

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.channel_state.states.state_9
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation.
SSOT ref: fsm.channel_state.states.state_9.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.
SSOT item context: value=FAULTING_COMPLETING.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.channel_state.states.state_9
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: fsm.channel_state.states.state_9

### RTL-0225: Implement FSM transition channel_state.transition_0

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.channel_state.transitions.transition_0
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream.
SSOT ref: fsm.channel_state.transitions.transition_0.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.
SSOT item context: from=STOPPED; to=EXECUTING; condition=DMAGO + secure check pass.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.channel_state.transitions.transition_0
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - fsm.channel_state.transitions.transition_0 condition is implemented as RTL control logic: DMAGO + secure check pass
  - fsm.channel_state.transitions.transition_0 transition path STOPPED -> EXECUTING is encoded or explicitly proven equivalent
- SSOT refs: fsm.channel_state.transitions.transition_0

### RTL-0226: Implement FSM transition channel_state.transition_1

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.channel_state.transitions.transition_1
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream.
SSOT ref: fsm.channel_state.transitions.transition_1.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.
SSOT item context: from=EXECUTING; to=CACHE_MISS; condition=icache miss.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.channel_state.transitions.transition_1
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - fsm.channel_state.transitions.transition_1 condition is implemented as RTL control logic: icache miss
  - fsm.channel_state.transitions.transition_1 transition path EXECUTING -> CACHE_MISS is encoded or explicitly proven equivalent
- SSOT refs: fsm.channel_state.transitions.transition_1

### RTL-0227: Implement FSM transition channel_state.transition_2

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.channel_state.transitions.transition_2
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream.
SSOT ref: fsm.channel_state.transitions.transition_2.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.
SSOT item context: from=CACHE_MISS; to=EXECUTING; condition=fill complete.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.channel_state.transitions.transition_2
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - fsm.channel_state.transitions.transition_2 condition is implemented as RTL control logic: fill complete
  - fsm.channel_state.transitions.transition_2 transition path CACHE_MISS -> EXECUTING is encoded or explicitly proven equivalent
- SSOT refs: fsm.channel_state.transitions.transition_2

### RTL-0228: Implement FSM transition channel_state.transition_3

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.channel_state.transitions.transition_3
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream.
SSOT ref: fsm.channel_state.transitions.transition_3.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.
SSOT item context: from=EXECUTING; to=WAITING_FOR_EVENT; condition=DMAWFE.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.channel_state.transitions.transition_3
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - fsm.channel_state.transitions.transition_3 condition is implemented as RTL control logic: DMAWFE
  - fsm.channel_state.transitions.transition_3 transition path EXECUTING -> WAITING_FOR_EVENT is encoded or explicitly proven equivalent
- SSOT refs: fsm.channel_state.transitions.transition_3

### RTL-0229: Implement FSM transition channel_state.transition_4

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.channel_state.transitions.transition_4
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream.
SSOT ref: fsm.channel_state.transitions.transition_4.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via fsm.
SSOT item context: from=WAITING_FOR_EVENT; to=EXECUTING; condition=event signaled.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.channel_state.transitions.transition_4
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - fsm.channel_state.transitions.transition_4 condition is implemented as RTL control logic: event signaled
  - fsm.chan
... <truncated 10808 chars>