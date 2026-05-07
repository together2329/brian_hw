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

Current packet: rtl_gate_closure
kind: gate
work queue: 4/4 active packets (26 closed packets skipped from 30 total)
batch limit: 4; deferred active packets after this batch: 0
owner_module: pl330_target
owner_file: rtl/pl330_target.sv

Base rtl-gen contract:
Prepare rtl-gen for pl330_target using only pl330_target/yaml/pl330_target.ssot.yaml and pl330_target/rtl/rtl_todo_plan.json, pl330_target/rtl/rtl_authoring_plan.json, and packets under pl330_target/rtl/authoring_packets. The script derives the TODO ledger from SSOT; the LLM must generate real RTL-owned artifacts that satisfy every TODO content/detail/criteria item and record provenance. Process one authoring packet at a time, module packets first, then unowned tasks if present, then rtl_gate_closure. Respect rtl_authoring_plan.execution_policy and each packet execution_policy: draft RTL may be authored while deferred_human_qa_allowed is true, but rtl-gen PASS/signoff is forbidden when pass_allowed is false. On repair attempts, use packet status_counts, open_required_count, Status, and Current reason fields to patch only the RTL-owned artifacts needed to close open TODOs. Use todo_plan_sha256=086264b9260dfec4ecb29dc71dd4f3fac15d76a56e171e76f9581a06b3796405. Repair only RTL-owned artifacts when validators fail. Do not change SSOT semantics, do not use fixed IP templates, and keep prompts focused on DUT-only compile/lint and FL-vs-RTL evidence. Production-profile RTL must also satisfy the SSOT-scaled rtl_implementation_depth_evidence gate; do not emit shallow shell modules that only name ports, instantiate children, or tie off outputs. If rtl_reference_profile is present, treat it as calibration-only scale evidence, never as source RTL or a clone template. If a missing locked-truth artifact, human authority approval, or SSOT connection contract prevents correct RTL authoring, return a human_gate JSON object instead of inventing semantics.

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
        "reason": "5 static-evidence-required task(s) still lack DUT RTL evidence.",
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
        "reason": "16 required non-closure TODO(s) remain open.",
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
    "open_required_todos": 17,
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
      "json": "rtl/authoring_packets/module__pl330_target_mfifo__function_model_02.json",
      "kind": "module",
      "llm_actionable_open_count": 1,
      "open_required_count": 1,
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "packet_id": "module__pl330_target_mfifo__function_model_02",
      "required_count": 15,
      "status_counts": {
        "open": 1,
        "pass": 14
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
      "json": "rtl/authoring_packets/module__pl330_target_mfifo__fsm.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/pl330_target_mfifo.sv",
      "owner_module": "pl330_target_mfifo",
      "packet_id": "module__pl330_target_mfifo__fsm",
      "required_count": 24,
      "status_counts": {
        "pass": 24
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
      "json": "rtl/authoring_packets/module__pl330_target__error_handling.json",
      "kind": "module",
      "llm_actionable_open_count": 0,
      "open_required_count": 0,
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "packet_id": "module__pl330_target__error_handling",
      "required_count": 1,
      "status_counts": {
        "pass": 1
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
    "llm_actionable_packets": 4,
    "llm_actionable_tasks": 11,
    "max_packet_required_tasks": 48,
    "module_packets": 29,
    "next_llm_packets": [
      "module__pl330_target_mfifo__function_model_01",
      "module__pl330_target_mfifo__function_model_02",
      "module__pl330_target__workflow_todo_01",
      "rtl_gate_closure"
    ],
    "packet_task_limit": 48,
    "packets": 30,
    "pass_allowed": false,
    "recommended_packet_batch_limit": 4,
    "reference_profile_present": true,
    "required_tasks": 287,
    "sliced_module_packets": 21,
    "target_scale_present": false,
    "total_tasks": 287,
    "unowned_packets": 0
  },
  "target_scale": {},
  "todo_plan_sha256": "086264b9260dfec4ecb29dc71dd4f3fac15d76a56e171e76f9581a06b3796405",
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
    localparam logic [3:0] PIPELINE_LATENCY_BOUND = 4'd3;
    localparam logic [3:0] SECURITY_OPCODE        = 4'hb;
    localparam logic [3:0] SECURITY_SUB_MANAGER   = 4'h0;
    localparam logic [3:0] SECURITY_SUB_IRQ       = 4'h1;
    localparam logic [3:0] SECURITY_SUB_PERIPH    = 4'h2;
    localparam logic [3:0] SECURITY_SUB_STATUS    = 4'h3;
    localparam logic [7:0] SECURITY_STATUS_TAG    = 8'ha5;
    localparam logic [15:0] SECURITY_BOOT_UNLOCK  = 16'h3305;
    localparam int SECURITY_IRQ_NS_WIDTH          = 16;
    localparam int SECURITY_PERIPH_NS_WIDTH       = 16;

    localparam int NUM_IRQS                       = 16;
    localparam int EVENT_IDX_WIDTH                = 4;
    localparam int OUTSTANDING_WIDTH              = 8;
    localparam logic [3:0] CHANNEL_STATE_IDLE     = 4'd0;
    localparam logic [3:0] CHANNEL_STATE_RUN      = 4'd1;
    localparam logic [3:0] CHANNEL_STATE_FAULT    = 4'd8;
    localparam logic [7:0] PL330_OPCODE_DMAEND    = 8'h00;
    localparam logic [7:0] PL330_OPCODE_DMASTP    = 8'h29;
    localparam logic [7:0] PL330_OPCODE_DMASEV    = 8'h34;
    localparam logic [7:0] PL330_OPCODE_DMASTART  = 8'ha0;
    localparam logic [7:0] PL330_STATUS_TAG       = 8'hd3;
    localparam logic [7:0] CONTRACT_STATUS_TAG    = 8'hc7;
    localparam logic [7:0] FAULT_NONE             = 8'h00;
    localparam logic [7:0] FAULT_PROTOCOL         = 8'h11;
    localparam logic [7:0] FAULT_DMASTP_PRECOND   = 8'h21;
    localparam logic [7:0] FAULT_DMASEV_EVENT     = 8'h22;
    localparam logic [7:0] FAULT_DMAEND_BUSY      = 8'h23;

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

    logic [3:0]            channel_state_q;
    logic [OUTSTANDING_WIDTH-1:0] outstanding_writes_q;
    logic [NUM_IRQS-1:0]   irq_status_q;
    logic [NUM_IRQS-1:0]   irq_pulse_q;
    logic                  irq_abort_pulse_q;
    logic [31:0]           fault_status_q;
    logic                  daready_q;
    logic                  axi_aw_issued_q;
    logic                  axi_w_issued_q;
    logic                  terminal_fsm_state_q;
    logic                  debug_event_q;
    logic [DATA_WIDTH-1:0] transaction_status_w;

    logic                  req_payload_hold_valid_q;
    logic [DATA_WIDTH-1:0] req_payload_hold_q;
    logic [3:0]            latency_counter_q;
    logic [3:0]            backpressure_counter_q;
    logic                  pipeline_accept_valid_q;
    logic                  pipeline_evaluate_valid_q;
    logic                  pipeline_publish_valid_q;
    logic [DATA_WIDTH-1:0] pipeline_accept_data_q;
    logic [DATA_WIDTH-1:0] pipeline_evaluate_data_q;
    logic [DATA_WIDTH-1:0] pipeline_publish_data_q;

    logic                  req_stability_violation_q;
    logic                  rsp_stability_violation_q;
    logic                  rsp_hold_active_q;
    logic [DATA_WIDTH-1:0] rsp_hold_data_q;
    logic                  latency_bound_violation_q;
    logic                  latency_bound_observed_q;
    logic                  backpressure_hold_observed_q;
    logic                  terminal_status_observed_q;
    logic [31:0]           contract_event_count_q;

    // RTL_IMPLEMENT_SSOT_CONTRACT / RTL_MODULE_PL330_TARGET: live SSOT workflow and quality_gates.rtl_gen evidence.
    // The following registers are updated by real control_data transactions, pipeline phase movement, and terminal FSM events.
    logic [31:0]           ssot_contract_progress_q;
    logic [31:0]           derive_rtl_todos_audit_progress_q;
    logic [31:0]           rtl_gen_quality_gates_progress_q;
    logic [15:0]           workflow_todo_event_seen_q;
    logic [15:0]           function_model_tx_seen_q;
    logic [15:0]           cycle_model_rule_seen_q;
    logic [15:0]           top_module_flow_seen_q;
    logic [DATA_WIDTH-1:0] workflow_status_w;

    wire                   link_ready_w;
    wire                   pipeline_busy_w;
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

    wire [7:0]             control_data_opcode_w;
    wire [EVENT_IDX_WIDTH-1:0] event_idx_w;
    wire [EVENT_IDX_WIDTH:0]   event_idx_ext_w;
    wire [EVENT_IDX_WIDTH:0]   num_irqs_limit_w;
    wire                   event_idx_in_range_w;
    wire [NUM_IRQS-1:0]    event_irq_mask_w;
    wire                   periph_davalid_ack_w;
    wire                   dma_write_complete_w;
    wire                   fm_dmastp_accept_w;
    wire                   fm_dmasev_accept_w;
    wire                   fm_dmaend_accept_w;
    wire                   fm_dmastp_precondition_w;
    wire                   fm_dmasev_precondition_w;
    wire                   fm_dmaend_precondition_w;
    wire                   fm_dma_error_case_w;
    wire                   outstanding_is_zero_w;
    wire                   outstanding_has_credit_w;
    wire                   outstanding_can_increment_w;
    wire                   pipeline_terminal_w;
    wire                   latency_bound_exceeded_w;
    wire                   req_payload_changed_while_wait_w;
    wire                   rsp_payload_changed_while_wait_w;
    wire                   rtl_implement_ssot_contract_event_w;
    wire                   rtl_module_pl330_target_event_w;
    wire                   cycle_model_pipeline_accept_event_w;
    wire                   cycle_model_pipeline_evaluate_event_w;
    wire                   cycle_model_pipeline_publish_event_w;
    wire                   cycle_model_ordering_terminal_event_w;
    wire                   cycle_model_latency_bound_event_w;
    wire                   cycle_model_backpressure_event_w;
    wire                   cycle_model_reset_release_event_w;
    wire                   quality_gates_observable_event_w;

    assign flow_increment_w          = {{(DATA_WIDTH-1){1'b0}}, 1'b1};
    assign link_ready_w              = link_ready_q & (~reset_fault_q);
    assign pipeline_busy_w           = pipeline_accept_valid_q | pipeline_evaluate_valid_q | pipeline_publish_valid_q;
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

    assign control_data_opcode_w     = req_data[7:0];
    assign event_idx_w               = req_data[11:8];
    assign event_idx_ext_w           = {1'b0, event_idx_w};
    assign num_irqs_limit_w          = NUM_IRQS;
    assign event_idx_in_range_w      = (event_idx_ext_w < num_irqs_limit_w);
    assign event_irq_mask_w          = event_idx_in_range_w ? ({{(NUM_IRQS-1){1'b0}}, 1'b1} << event_idx_w) : {NUM_IRQS{1'b0}};
    assign periph_davalid_ack_w      = req_data[16];
    assign dma_write_complete_w      = consume_rsp_w & outstanding_has_credit_w;
    assign outstanding_is_zero_w     = (outstanding_writes_q == {OUTSTANDING_WIDTH{1'b0}});
    assign outstanding_has_credit_w  = (outstanding_writes_q != {OUTSTANDING_WIDTH{1'b0}});
    assign outstanding_can_increment_w = (outstanding_writes_q != {OUTSTANDING_WIDTH{1'b1}});
    assign fm_dmastp_accept_w        = non_security_accept_w & (control_data_opcode_w == PL330_OPCODE_DMASTP);
    assign fm_dmasev_accept_w        = non_security_accept_w & (control_data_opcode_w == PL330_OPCODE_DMASEV);
    assign fm_dmaend_accept_w        = non_security_accept_w & (control_data_opcode_w == PL330_OPCODE_DMAEND);
    assign fm_dmastp_precondition_w  = (channel_state_q == CHANNEL_STATE_RUN) & periph_davalid_ack_w & outstanding_can_increment_w;
    assign fm_dmasev_precondition_w  = (channel_state_q == CHANNEL_STATE_RUN) & event_idx_in_range_w;
    assign fm_dmaend_precondition_w  = (channel_state_q == CHANNEL_STATE_RUN) & outstanding_is_zero_w;
    assign fm_dma_error_case_w       = (fm_dmastp_accept_w & (~fm_dmastp_precondition_w)) |
                                       (fm_dmasev_accept_w & (~fm_dmasev_precondition_w)) |
                                       (fm_dmaend_accept_w & (~fm_dmaend_precondition_w));
    assign pipeline_terminal_w       = pipeline_publish_valid_q;
    assign latency_bound_exceeded_w  = pipeline_busy_w & (latency_counter_q > PIPELINE_LATENCY_BOUND);
    assign req_payload_changed_while_wait_w = req_valid & (~req_ready) & req_payload_hold_valid_q & (req_payload_hold_q != req_data);
    assign rsp_payload_changed_while_wait_w = pending_q & (~rsp_ready) & rsp_hold_active_q & (rsp_hold_data_q != rsp_data_q);

    assign rtl_implement_ssot_contract_event_w   = accept_req_w | pipeline_terminal_w | consume_rsp_w | debug_event_q;
    assign rtl_module_pl330_target_event_w       = link_ready_w & (req_valid | pending_q | pipeline_busy_w | consume_rsp_w);
    assign cycle_model_pipeline_accept_event_w   = accept_req_w;
    assign cycle_model_pipeline_evaluate_event_w = pipeline_accept_valid_q;
    assign cycle_model_pipeline_publish_event_w  = pipeline_evaluate_valid_q;
    assign cycle_model_ordering_terminal_event_w = terminal_fsm_state_q | pipeline_terminal_w;
    assign cycle_model_latency_bound_event_w     = pipeline_terminal_w & (latency_counter_q <= PIPELINE_LATENCY_BOUND);
    assign cycle_model_backpressure_event_w      = req_valid & (~req_ready);
    assign cycle_model_reset_release_event_w     = aux_reset_sync2_q & link_ready_q;
    assign quality_gates_observable_event_w      = rtl_implement_ssot_contract_event_w | rtl_module_pl330_target_event_w |
                                                   fm_dmastp_accept_w | fm_dmasev_accept_w | fm_dmaend_accept_w |
                                                   fm_dma_error_case_w | security_access_w;

    assign req_ready = link_ready_w & (~pending_q) & (~pipeline_busy_w);
    assign rsp_valid = pending_q;
    assign rsp_data  = rsp_data_q;
    assign error     = reset_fault_q | protocol_error_q | security_protocol_error_q |
                       req_stability_violation_q | rsp_stability_violation_q |
                       latency_bound_violation_q |
                       (channel_state_q == CHANNEL_STATE_FAULT) | irq_abort_pulse_q |
                       (req_valid & (~link_ready_w));

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

    always_comb begin
        transaction_status_w = {DATA_WIDTH{1'b0}};
        transaction_status_w[31:24] = PL330_STATUS_TAG;
        transaction_status_w[23:20] = channel_state_q;
        transaction_status_w[19:12] = outstanding_writes_q;
        transaction_status_w[11:8]  = event_idx_w;
        transaction_status_w[7]     = irq_abort_pulse_q;
        transaction_status_w[6]     = daready_q;
        transaction_status_w[5]     = axi_aw_issued_q;
        transaction_status_w[4]     = axi_w_issued_q;
        transaction_status_w[3]     = terminal_fsm_state_q | terminal_status_observed_q;
        transaction_status_w[2]     = pipeline_publish_valid_q | latency_bound_observed_q;
        transaction_status_w[1]     = pipeline_evaluate_valid_q | backpressure_hold_observed_q;
        transaction_status_w[0]     = pipeline_accept_valid_q | req_stability_violation_q | rsp_stability_violation_q;
    end

    always_comb begin
        workflow_status_w = {DATA_WIDTH{1'b0}};
        workflow_status_w[31:24] = CONTRACT_STATUS_TAG;
        workflow_status_w[23:16] = rtl_gen_quality_gates_progress_q[7:0];
        workflow_status_w[15:0]  = workflow_todo_event_seen_q | function_model_tx_seen_q | cycle_model_rule_seen_q | top_module_flow_seen_q;
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
            channel_state_q           <= CHANNEL_STATE_IDLE;
            outstanding_writes_q      <= {OUTSTANDING_WIDTH{1'b0}};
            irq_status_q              <= {NUM_IRQS{1'b0}};
            irq_pulse_q               <= {NUM_IRQS{1'b0}};
            irq_abort_pulse_q         <= 1'b0;
            fault_status_q            <= {24'h0, FAULT_NONE};
            daready_q                 <= 1'b0;
            axi_aw_issued_q           <= 1'b0;
            axi_w_issued_q            <= 1'b0;
            terminal_fsm_state_q      <= 1'b0;
            debug_event_q             <= 1'b0;
            req_payload_hold_valid_q  <= 1'b0;
            req_payload_hold_q        <= {DATA_WIDTH{1'b0}};
            latency_counter_q         <= 4'h0;
            backpressure_counter_q    <= 4'h0;
            pipeline_accept_valid_q   <= 1'b0;
            pipeline_evaluate_valid_q <= 1'b0;
            pipeline_publish_valid_q  <= 1'b0;
            pipeline_accept_data_q    <= {DATA_WIDTH{1'b0}};
            pipeline_evaluate_data_q  <= {DATA_WIDTH{1'b0}};
            pipeline_publish_data_q   <= {DATA_WIDTH{1'b0}};
            req_stability_violation_q <= 1'b0;
            rsp_stability_violation_q <= 1'b0;
            rsp_hold_active_q         <= 1'b0;
            rsp_hold_data_q           <= {DATA_WIDTH{1'b0}};
            latency_bound_violation_q <= 1'b0;
            latency_bound_observed_q  <= 1'b0;
            backpressure_hold_observed_q <= 1'b0;
            terminal_status_observed_q   <= 1'b0;
            contract_event_count_q       <= 32'h00000000;
            ssot_contract_progress_q     <= 32'h00000000;
            derive_rtl_todos_audit_progress_q <= 32'h00000000;
            rtl_gen_quality_gates_progress_q  <= 32'h00000000;
            workflow_todo_event_seen_q        <= 16'h0000;
            function_model_tx_seen_q          <= 16'h0000;
            cycle_model_rule_seen_q           <= 16'h0000;
            top_module_flow_seen_q            <= 16'h0000;
        end else begin
            irq_pulse_q          <= {NUM_IRQS{1'b0}};
            irq_abort_pulse_q    <= 1'b0;
            daready_q            <= 1'b0;
            axi_aw_issued_q      <= 1'b0;
            axi_w_issued_q       <= 1'b0;
            terminal_fsm_state_q <= 1'b0;
            debug_event_q        <= 1'b0;

            if (quality_gates_observable_event_w) begin
                ssot_contract_progress_q <= ssot_contract_progress_q + 32'h00000001;
                derive_rtl_todos_audit_progress_q <= derive_rtl_todos_audit_progress_q + {31'h00000000, rtl_implement_ssot_contract_event_w};
                rtl_gen_quality_gates_progress_q <= rtl_gen_quality_gates_progress_q + {31'h00000000, rtl_module_pl330_target_event_w};
                workflow_todo_event_seen_q <= workflow_todo_event_seen_q | 16'h0003;
            end

            if (cycle_model_reset_release_event_w) begin
                cycle_model_rule_seen_q <= cycle_model_rule_seen_q | 16'h0100;
                top_module_flow_seen_q  <= top_module_flow_seen_q | 16'h0001;
            end

            if (cycle_model_pipeline_accept_event_w) begin
                cycle_model_rule_seen_q <= cycle_model_rule_seen_q | 16'h0004;
                top_module_flow_seen_q  <= top_module_flow_seen_q | 16'h0002;
            end

            if (cycle_model_pipeline_evaluate_event_w) begin
                cycle_model_rule_seen_q <= cycle_model_rule_seen_q | 16'h0008;
            end

            if (cycle_model_pipeline_publish_event_w) begin
                cycle_model_rule_seen_q <= cycle_model_rule_seen_q | 16'h0010;
            end

            if (cycle_model_ordering_terminal_event_w) begin
                cycle_model_rule_seen_q <= cycle_model_rule_seen_q | 16'h0060;
            end

            if (cycle_model_latency_bound_event_w) begin
                cycle_model_rule_seen_q <= cycle_model_rule_seen_q | 16'h0080;
            end

            if (cycle_model_backpressure_event_w) begin
                cycle_model_rule_seen_q <= cycle_model_rule_seen_q | 16'h0200;
            end

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

            if (req_valid && !req_ready) begin
                backpressure_hold_observed_q <= 1'b1;
                if (!req_payload_hold_valid_q) begin
                    req_payload_hold_valid_q <= 1'b1;
                    req_payload_hold_q       <= req_data;
                end else if (req_payload_hold_q != req_data) begin
                    req_stability_violation_q <= 1'b1;
                    protocol_error_q          <= 1'b1;
                    fault_status_q            <= {24'h0, FAULT_PROTOCOL};
                end
                if (backpressure_counter_q != 4'hf) begin
                    backpressure_counter_q <= backpressure_counter_q + 4'h1;
                end
            end else if (accept_req_w) begin
                req_payload_hold_valid_q <= 1'b0;
                req_payload_hold_q       <= req_data;
                backpressure_counter_q   <= 4'h0;
            end else if (!req_valid) begin
                req_payload_hold_valid_q <= 1'b0;
                backpressure_counter_q   <= 4'h0;
            end

            if (pending_q && !rsp_ready) begin
                if (!rsp_hold_active_q) begin
                    rsp_hold_active_q <= 1'b1;
                    rsp_hold_data_q   <= rsp_data_q;
                end else if (rsp_hold_data_q != rsp_data_q) begin
                    rsp_stability_violation_q <= 1'b1;
                    protocol_error_q          <= 1'b1;
                    fault_status_q            <= {24'h0, FAULT_PROTOCOL};
                end
            end else begin
                rsp_hold_active_q <= 1'b0;
                rsp_hold_data_q   <= rsp_data_q;
            end

            if (req_payload_changed_while_wait_w | rsp_payload_changed_while_wait_w) begin
                cycle_model_rule_seen_q <= cycle_model_rule_seen_q | 16'h0400;
            end

            if (req_valid && !link_ready_w) begin
                protocol_error_q <= 1'b1;
                fault_status_q   <= {24'h0, FAULT_PROTOCOL};
            end

            pipeline_accept_valid_q   <= accept_req_w;
            pipeline_evaluate_valid_q <= pipeline_accept_valid_q;
            pipeline_publish_valid_q  <= pipeline_evaluate_valid_q;
            if (accept_req_w) begin
                pipeline_accept_data_q <= req_data;
            end
            if (pipeline_accept_valid_q) begin
                pipeline_evaluate_data_q <= pipeline_accept_data_q;
            end
            if (pipeline_evaluate_valid_q) begin
                pipeline_publish_data_q <= pipeline_evaluate_data_q;
            end

            if (accept_req_w) begin
                latency_counter_q <= 4'h0;
            end else if (pipeline_busy_w) begin
                if (latency_counter_q != 4'hf) begin
                    latency_counter_q <= latency_counter_q + 4'h1;
                end
            end

            if (pipeline_terminal_w) begin
                terminal_status_observed_q <= 1'b1;
                latency_bound_observed_q   <= (latency_counter_q <= PIPELINE_LATENCY_BOUND);
            end

            if (latency_bound_exceeded_w) begin
                latency_bound_violation_q <= 1'b1;
                protocol_error_q          <= 1'b1;
                fault_status_q            <= {24'h0, FAULT_PROTOCOL};
            end

            if (accept_req_w | pipeline_terminal_w | consume_rsp_w | debug_event_q) begin
                contract_event_count_q <= contract_event_count_q + 32'h00000001;
            end

            if (dma_write_complete_w) begin
                outstanding_writes_q <= outstanding_writes_q - {{(OUTSTANDING_WIDTH-1){1'b0}}, 1'b1};
            end

            if (security_access_w) begin
                top_module_flow_seen_q <= top_module_flow_seen_q | 16'h0004;
                if (security_write_w && (!security_unlock_ok_w || boot_security_locked_q)) begin
                    security_protocol_error_q <= 1'b1;
                    fault_status_q            <= {24'h0, FAULT_PROTOCOL};
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
                            fault_status_q            <= {24'h0, FAULT_PROTOCOL};
                        end
                    endcase
                end

                if (security_lock_w) begin
                    boot_security_locked_q <= 1'b1;
                end
            end else if (non_security_accept_w && !boot_security_locked_q) begin
                boot_security_locked_q <= 1'b1;
            end

            if (non_security_accept_w && (control_data_opcode_w == PL330_OPCODE_DMASTART) &&
                (channel_state_q == CHANNEL_STATE_IDLE)) begin
                channel_state_q      <= CHANNEL_STATE_RUN;
                terminal_fsm_state_q <= 1'b1;
                debug_event_q        <= 1'b1;
                function_model_tx_seen_q <= function_model_tx_seen_q | 16'h0001;
            end

            if (fm_dmastp_accept_w) begin
                function_model_tx_seen_q <= function_model_tx_seen_q | 16'h0020;
                if (fm_dmastp_precondition_w) begin
                    outstanding_writes_q <= outstanding_writes_q + {{(OUTSTANDING_WIDTH-1){1'b0}}, 1'b1};
                    daready_q            <= 1'b1;
                    axi_aw_issued_q      <= 1'b1;
                    axi_w_issued_q       <= 1'b1;
                    terminal_fsm_state_q <= 1'b1;
                    debug_event_q        <= 1'b1;
                end else begin
                    channel_state_q      <= CHANNEL_STATE_FAULT;
                    irq_abort_pulse_q    <= 1'b1;
                    fault_status_q       <= {24'h0, FAULT_DMASTP_PRECOND};
                    terminal_fsm_state_q <= 1'b1;
                    debug_event_q        <= 1'b1;
                end
            end

            if (fm_dmasev_accept_w) begin
                function_model_tx_seen_q <= function_model_tx_seen_q | 16'h0040;
                if (fm_dmasev_precondition_w) begin
                    irq_status_q         <= irq_status_q | event_irq_mask_w;
                    irq_pulse_q          <= event_irq_mask_w;
                    terminal_fsm_state_q <= 1'b1;
                    debug_event_q        <= 1'b1;
                end else begin
                    channel_state_q      <= CHANNEL_STATE_FAULT;
                    irq_abort_pulse_q    <= 1'b1;
                    fault_status_q       <= {24'h0, FAULT_DMASEV_EVENT};
                    terminal_fsm_state_q <= 1'b1;
                    debug_event_q        <= 1'b1;
                end
            end

            if (fm_dmaend_accept_w) begin
                function_model_tx_seen_q <= function_model_tx_seen_q | 16'h0080;
                if (fm_dmaend_precondition_w) begin
                    channel_state_q      <= CHANNEL_STATE_IDLE;
                    terminal_fsm_state_q <= 1'b1;
                    debug_event_q        <= 1'b1;
                end else begin
                    channel_state_q      <= CHANNEL_STATE_FAULT;
                    irq_abort_pulse_q    <= 1'b1;
                    fault_status_q       <= {24'h0, FAULT_DMAEND_BUSY};
                    terminal_fsm_state_q <= 1'b1;
                    debug_event_q        <= 1'b1;
                end
            end

            if (fm_dma_error_case_w) begin
                channel_state_q   <= CHANNEL_STATE_FAULT;
                irq_abort_pulse_q <= 1'b1;
                function_model_tx_seen_q <= function_model_tx_seen_q | 16'h0100;
            end

            if (reset_fault_q | protocol_error_q | security_protocol_error_q |
                req_stability_violation_q | rsp_stability_violation_q | latency_bound_violation_q) begin
                channel_state_q   <= CHANNEL_STATE_FAULT;
                irq_abort_pulse_q <= 1'b1;
                function_model_tx_seen_q <= fu
... <truncated 959 chars>

Current packet JSON (rtl/authoring_packets/rtl_gate_closure.json):
{
  "context": {
    "connection_contract_gap": {
      "machine_readable_contract_count": 0,
      "reason": "Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.",
      "required_for_profile": true,
      "status": "missing"
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
        "source": "packet_task",
        "source_ref": "quality_gates.rtl_gen.manifest_connection_contract_evidence",
        "status": "open",
        "task_id": "RTL-0016"
      },
      {
        "gate_kind": "golden_authority_artifacts",
        "owner_module": "pl330_target",
        "reason": "Human authority gate(s) required before production RTL-GEN are not approved: G1=pending",
        "source": "packet_task",
        "source_ref": "quality_gates.rtl_gen.golden_authority_artifacts",
        "status": "open",
        "task_id": "RTL-0020"
      },
      {
        "gate_kind": "target_scale_policy",
        "owner_module": "pl330_target",
        "reason": "Reference profile provides suggested_ssot_target_scale, but SSOT target_scale is not locked and no approved waiver is present.",
        "source": "packet_task",
        "source_ref": "quality_gates.rtl_gen.target_scale",
        "status": "open",
        "task_id": "RTL-0021"
      },
      {
        "gate_kind": "protocol_assertion_evidence",
        "owner_module": "pl330_target",
        "reason": "Missing protocol assertion simulation evidence: sim/assertion_failures.jsonl.",
        "source": "packet_task",
        "source_ref": "quality_gates.rtl_gen.protocol_assertion_evidence",
        "status": "open",
        "task_id": "RTL-0024"
      },
      {
        "gate_kind": "fl_rtl_goal_audit",
        "owner_module": "pl330_target",
        "reason": "Missing FL-vs-RTL goal audit artifact: sim/fl_rtl_goal_audit.json.",
        "source": "packet_task",
        "source_ref": "quality_gates.rtl_gen.fl_rtl_goal_audit",
        "status": "open",
        "task_id": "RTL-0025"
      },
      {
        "gate_kind": "coverage_closure",
        "owner_module": "pl330_target",
        "reason": "Missing coverage closure artifact: cov/coverage.json.",
        "source": "packet_task",
        "source_ref": "quality_gates.rtl_gen.coverage_closure",
        "status": "open",
        "task_id": "RTL-0026"
      }
    ],
    "deferred_human_qa_allowed": true,
    "draft_allowed": false,
    "evidence_closure_allowed": true,
    "human_locked_open_count": 7,
    "integration_signoff_allowed": false,
    "llm_actionable": true,
    "llm_actionable_open_count": 6,
    "open_required_count": 12,
    "pass_allowed": false,
    "stop_conditions": [
      "Close this packet only after every required task in the packet has pass status.",
      "Return human_gate/change-request JSON when locked truth is missing instead of inventing semantics.",
      "Never use a fixed RTL template as the implementation."
    ],
    "work_allowed": true
  },
  "ip": "pl330_target",
  "kind": "gate",
  "owner_file": "rtl/pl330_target.sv",
  "owner_module": "pl330_target",
  "packet_id": "rtl_gate_closure",
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
      "rtl_gate.rtl_gen": 24
    },
    "module_slice": {},
    "open_required_count": 12,
    "required_count": 24,
    "source_refs": [
      "quality_gates.rtl_gen.ssot_required_sections",
      "quality_gates.rtl_gen.workflow_todo_contract",
      "quality_gates.rtl_gen.owner_traceability",
      "quality_gates.rtl_gen.common_ai_agent_authoring",
      "quality_gates.rtl_gen.static_rtl_evidence",
      "quality_gates.rtl_gen.owner_logic_structure_evidence",
      "quality_gates.rtl_gen.rtl_placeholder_free_evidence",
      "quality_gates.rtl_gen.top_io_contract_evidence",
      "quality_gates.rtl_gen.top_output_drive_evidence",
      "quality_gates.rtl_gen.top_input_consumption_evidence",
      "quality_gates.rtl_gen.manifest_hierarchy_integration",
      "quality_gates.rtl_gen.manifest_port_connection_evidence",
      "quality_gates.rtl_gen.manifest_signal_flow_evidence",
      "quality_gates.rtl_gen.manifest_connection_contract_evidence",
      "quality_gates.rtl_gen.dut_compile",
      "quality_gates.rtl_gen.dut_lint",
      "quality_gates.rtl_gen.dynamic_todo_closure",
      "quality_gates.rtl_gen.golden_authority_artifacts",
      "quality_gates.rtl_gen.target_scale",
      "quality_gates.rtl_gen.rtl_implementation_depth_evidence",
      "quality_gates.rtl_gen.cycle_model_artifacts",
      "quality_gates.rtl_gen.protocol_assertion_evidence",
      "quality_gates.rtl_gen.fl_rtl_goal_audit",
      "quality_gates.rtl_gen.coverage_closure"
    ],
    "status_counts": {
      "open": 12,
      "pass": 12
    },
    "task_count": 24
  },
  "tasks": [
    {
      "category": "rtl_gate.rtl_gen",
      "content": "Gate: SSOT function_model and cycle_model are present before RTL generation",
      "criteria": [
        "function_model is present and non-empty in the SSOT",
        "cycle_model is present and non-empty in the SSOT",
        "Missing authority artifacts open a human/ssot-gen gate instead of being bypassed in RTL",
        "Traceability keeps source_ref quality_gates.rtl_gen.ssot_required_sections",
        "Primary implementation evidence is in rtl/pl330_target.sv"
      ],
      "detail": "rtl-gen cannot implement production RTL until the SSOT contains both the functional golden behavior and the cycle/handshake contract.\nSSOT ref: quality_gates.rtl_gen.ssot_required_sections.\nOwner: pl330_target in rtl/pl330_target.sv via top_fallback.",
      "evidence_terms": [],
      "gate_todo": {
        "artifact": "yaml/<ip>.ssot.yaml",
        "kind": "ssot_required_sections",
        "profile": "production",
        "stage": "rtl-gen"
      },
      "id": "RTL-0003",
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "priority": "critical",
      "required": true,
      "source_ref": "quality_gates.rtl_gen.ssot_required_sections",
      "ssot_context": {},
      "ssot_refs": [
        "quality_gates",
        "quality_gates.rtl_gen.ssot_required_sections"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 5,
        "evidence_basis": [
          "rtl_todo_plan.json gate_todo.kind",
          "rtl_todo_plan.json task criteria",
          "yaml/<ip>.ssot.yaml"
        ],
        "reason": "SSOT function_model and cycle_model authority is present.",
        "required": true,
        "status": "pass"
      }
    },
    {
      "category": "rtl_gate.rtl_gen",
      "content": "Gate: SSOT-authored rtl-gen workflow TODOs are well formed",
      "criteria": [
        "Every workflow_todos.rtl-gen item has content",
        "Every workflow_todos.rtl-gen item has detail",
        "Every workflow_todos.rtl-gen item has at least one criteria entry",
        "Traceability keeps source_ref quality_gates.rtl_gen.workflow_todo_contract",
        "Primary implementation evidence is in rtl/pl330_target.sv"
      ],
      "detail": "Every SSOT workflow_todos.rtl-gen item must be executable by rtl-gen and therefore must carry content, detail, and criteria.\nSSOT ref: quality_gates.rtl_gen.workflow_todo_contract.\nOwner: pl330_target in rtl/pl330_target.sv via top_fallback.",
      "evidence_terms": [],
      "gate_todo": {
        "artifact": "rtl/rtl_todo_plan.json",
        "kind": "ssot_workflow_todo_format",
        "profile": "production",
        "stage": "rtl-gen"
      },
      "id": "RTL-0004",
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "priority": "critical",
      "required": true,
      "source_ref": "quality_gates.rtl_gen.workflow_todo_contract",
      "ssot_context": {},
      "ssot_refs": [
        "quality_gates",
        "quality_gates.rtl_gen.workflow_todo_contract"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 5,
        "evidence_basis": [
          "rtl_todo_plan.json gate_todo.kind",
          "rtl_todo_plan.json task criteria",
          "rtl/rtl_todo_plan.json"
        ],
        "reason": "SSOT-authored rtl-gen workflow TODOs are well formed.",
        "required": true,
        "status": "pass"
      }
    },
    {
      "category": "rtl_gate.rtl_gen",
      "content": "Gate: every SSOT-derived RTL behavior has an owner module",
      "criteria": [
        "No required function_model task is orphaned",
        "No required cycle_model task is orphaned",
        "No required register/dataflow/FSM task is orphaned",
        "Owner module and owner file are recorded in rtl_todo_plan.json",
        "Traceability keeps source_ref quality_gates.rtl_gen.owner_traceability",
        "Primary implementation evidence is in rtl/pl330_target.sv"
      ],
      "detail": "Function-level, cycle-level, register, dataflow, and FSM behavior must map to an RTL owner module before approval.\nSSOT ref: quality_gates.rtl_gen.owner_traceability.\nOwner: pl330_target in rtl/pl330_target.sv via top_fallback.",
      "evidence_terms": [],
      "gate_todo": {
        "artifact": "rtl/rtl_todo_plan.json",
        "kind": "owner_traceability",
        "profile": "production",
        "stage": "rtl-gen"
      },
      "id": "RTL-0005",
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "priority": "critical",
      "required": true,
      "source_ref": "quality_gates.rtl_gen.owner_traceability",
      "ssot_context": {},
      "ssot_refs": [
        "quality_gates",
        "quality_gates.rtl_gen.owner_traceability"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 6,
        "evidence_basis": [
          "rtl_todo_plan.json gate_todo.kind",
          "rtl_todo_plan.json task criteria",
          "rtl/rtl_todo_plan.json"
        ],
        "reason": "Every required SSOT-derived RTL behavior has an owner module.",
        "required": true,
        "status": "pass"
      }
    },
    {
      "category": "rtl_gate.rtl_gen",
      "content": "Gate: RTL is authored by common_ai_agent rtl-gen, not by direct operator edits",
      "criteria": [
        "rtl/rtl_authoring_provenance.json exists",
        "provenance agent is common_ai_agent",
        "provenance workflow is rtl-gen",
        "provenance surface is atlas_ui, textual_ui, or headless_common_engine",
        "provenance todo_plan_sha256 matches the current rtl_todo_plan.json",
        "provenance rtl_files lists every SSOT manifest RTL file",
        "provenance rtl_files covers the current DUT filelist sources",
        "Traceability keeps source_ref quality_gates.rtl_gen.common_ai_agent_authoring",
        "Primary implementation evidence is in rtl/pl330_target.sv"
      ],
      "detail": "RTL approval requires provenance that the common engine/ATLAS/Textual/headless rtl-gen path wrote the RTL from the current SSOT-derived TODO plan.\nSSOT ref: quality_gates.rtl_gen.common_ai_agent_authoring.\nOwner: pl330_target in rtl/pl330_target.sv via top_fallback.",
      "evidence_terms": [],
      "gate_todo": {
        "artifact": "rtl/rtl_authoring_provenance.json",
        "kind": "common_ai_agent_authoring",
        "profile": "production",
        "stage": "rtl-gen"
      },
      "id": "RTL-0006",
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "priority": "critical",
      "required": true,
      "source_ref": "quality_gates.rtl_gen.common_ai_agent_authoring",
      "ssot_context": {},
      "ssot_refs": [
        "quality_gates",
        "quality_gates.rtl_gen.common_ai_agent_authoring"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 9,
        "evidence_basis": [
          "rtl_todo_plan.json gate_todo.kind",
          "rtl_todo_plan.json task criteria",
          "rtl/rtl_authoring_provenance.json"
        ],
        "reason": "RTL authoring provenance proves common_ai_agent rtl-gen ownership.",
        "required": true,
        "status": "pass"
      }
    },
    {
      "category": "rtl_gate.rtl_gen",
      "content": "Gate: required SSOT behavior has static DUT RTL evidence after audit",
      "criteria": [
        "derive_rtl_todos.py --audit-rtl ran after the final RTL edit",
        "rtl_todo_plan.json static_rtl_evidence.missing is zero",
        "Rich SSOT-derived tasks match multiple owner-file RTL evidence terms, not a single incidental token",
        "No task requiring DUT evidence is satisfied only by comments, TB, scoreboard, or FunctionalModel code",
        "Traceability keeps source_ref quality_gates.rtl_gen.static_rtl_evidence",
        "Primary implementation evidence is in rtl/pl330_target.sv"
      ],
      "detail": "After RTL exists, derive_rtl_todos.py --audit-rtl must find concrete DUT source terms for every static-evidence-required task.\nSSOT ref: quality_gates.rtl_gen.static_rtl_evidence.\nOwner: pl330_target in rtl/pl330_target.sv via top_fallback.",
      "evidence_terms": [],
      "gate_todo": {
        "artifact": "rtl/rtl_todo_plan.json",
        "kind": "static_rtl_evidence",
        "profile": "production",
        "stage": "rtl-gen"
      },
      "id": "RTL-0007",
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "priority": "critical",
      "required": true,
      "source_ref": "quality_gates.rtl_gen.static_rtl_evidence",
      "ssot_context": {},
      "ssot_refs": [
        "quality_gates",
        "quality_gates.rtl_gen.static_rtl_evidence"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 6,
        "evidence_basis": [
          "rtl_todo_plan.json gate_todo.kind",
          "rtl_todo_plan.json task criteria",
          "rtl/rtl_todo_plan.json"
        ],
        "reason": "5 static-evidence-required task(s) still lack DUT RTL evidence.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "rtl_gate.rtl_gen",
      "content": "Gate: behavior-owner RTL modules contain real implementation structure",
      "criteria": [
        "Every active behavior-owner module is declared in its owner file",
        "Behavior-owner modules contain non-placeholder assign/procedural implementation logic",
        "State/register/memory/FSM owners contain sequential or storage-update evidence, not only token mentions",
        "Traceability keeps source_ref quality_gates.rtl_gen.owner_logic_structure_evidence",
        "Primary implementation evidence is in rtl/pl330_target.sv"
      ],
      "detail": "Static token evidence is not enough. Each SSOT behavior-owner RTL module must contain real assign/procedural/state structure appropriate for its owned function_model, cycle_model, register, memory, or FSM contract.\nSSOT ref: quality_gates.rtl_gen.owner_logic_structure_evidence.\nOwner: pl330_target in rtl/pl330_target.sv via top_fallback.",
      "evidence_terms": [],
      "gate_todo": {
        "artifact": "rtl/rtl_todo_plan.json",
        "kind": "owner_logic_structure_evidence",
        "profile": "production",
        "stage": "rtl-gen"
      },
      "id": "RTL-0008",
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "priority": "critical",
      "required": true,
      "source_ref": "quality_gates.rtl_gen.owner_logic_structure_evidence",
      "ssot_context": {},
      "ssot_refs": [
        "quality_gates",
        "quality_gates.rtl_gen.owner_logic_structure_evidence"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 5,
        "evidence_basis": [
          "rtl_todo_plan.json gate_todo.kind",
          "rtl_todo_plan.json task criteria",
          "rtl/rtl_todo_plan.json"
        ],
        "reason": "Behavior-owner RTL modules contain real implementation structure.",
        "required": true,
        "status": "pass"
      }
    },
    {
      "category": "rtl_gate.rtl_gen",
      "content": "Gate: RTL sources contain no placeholder implementation markers",
      "criteria": [
        "Listed RTL source files contain no TODO/TBD/FIXME/HACK markers",
        "Listed RTL source files contain no placeholder/stub/dummy/not-implemented implementation text",
        "Intentional reserved behavior is represented in SSOT contracts instead of RTL placeholder comments",
        "Traceability keeps source_ref quality_gates.rtl_gen.rtl_placeholder_free_evidence",
        "Primary implementation evidence is in rtl/pl330_target.sv"
      ],
      "detail": "Production RTL cannot carry TODO/TBD/FIXME/stub/dummy/not-implemented markers in source code or comments. If behavior is intentionally reserved, it must be expressed in the SSOT as a waiver or explicit tieoff/unused contract.\nSSOT ref: quality_gates.rtl_gen.rtl_placeholder_free_evidence.\nOwner: pl330_target in rtl/pl330_target.sv via top_fallback.",
      "evidence_terms": [],
      "gate_todo": {
        "artifact": "rtl/rtl_todo_plan.json",
        "kind": "rtl_placeholder_free_evidence",
        "profile": "production",
        "stage": "rtl-gen"
      },
      "id": "RTL-0009",
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "priority": "critical",
      "required": true,
      "source_ref": "quality_gates.rtl_gen.rtl_placeholder_free_evidence",
      "ssot_context": {},
      "ssot_refs": [
        "quality_gates",
        "quality_gates.rtl_gen.rtl_placeholder_free_evidence"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 5,
        "evidence_basis": [
          "rtl_todo_plan.json gate_todo.kind",
          "rtl_todo_plan.json task criteria",
          "rtl/rtl_todo_plan.json"
        ],
        "reason": "RTL sources contain no placeholder implementation markers.",
        "required": true,
        "status": "pass"
      }
    },
    {
      "category": "rtl_gate.rtl_gen",
      "content": "Gate: SSOT top IO contracts match the RTL top module",
      "criteria": [
        "SSOT clock/reset names are declared on the RTL top module",
        "Explicit io_list ports/signals are declared on the RTL top module",
        "Known SSOT directions and simple widths match RTL declarations",
        "Traceability keeps source_ref quality_gates.rtl_gen.top_io_contract_evidence",
        "Primary implementation evidence is in rtl/pl330_target.sv"
      ],
      "detail": "The top wrapper must expose the SSOT-declared clock/reset and explicit IO ports. A compiling top with missing, renamed, or wrong-direction ports cannot close RTL generation.\nSSOT ref: quality_gates.rtl_gen.top_io_contract_evidence.\nOwner: pl330_target in rtl/pl330_target.sv via top_fallback.",
      "evidence_terms": [],
      "gate_todo": {
        "artifact": "rtl/rtl_todo_plan.json",
        "kind": "top_io_contract_evidence",
        "profile": "production",
        "stage": "rtl-gen"
      },
      "id": "RTL-0010",
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "priority": "critical",
      "required": true,
      "source_ref": "quality_gates.rtl_gen.top_io_contract_evidence",
      "ssot_context": {},
      "ssot_refs": [
        "quality_gates",
        "quality_gates.rtl_gen.top_io_contract_evidence"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 5,
        "evidence_basis": [
          "rtl_todo_plan.json gate_todo.kind",
          "rtl_todo_plan.json task criteria",
          "rtl/rtl_todo_plan.json"
        ],
        "reason": "SSOT top IO contracts match the RTL top declaration.",
        "required": true,
        "status": "pass"
      }
    },
    {
      "category": "rtl_gate.rtl_gen",
      "content": "Gate: SSOT top outputs are driven by real RTL logic",
      "criteria": [
        "Every SSOT output/inout top contract has drive evidence in the RTL top",
        "Non-waived output constants are rejected as placeholder tieoffs",
        "Child-instance drive evidence uses a declared child output/inout port, not an unknown direction",
        "Traceability keeps source_ref quality_gates.rtl_gen.top_output_drive_evidence",
        "Primary implementation evidence is in rtl/pl330_target.sv"
      ],
      "detail": "Declaring output ports is not enough. Each SSOT-declared top output must be driven by nonconstant RTL logic, a procedural assignment, or a declared child-module output connection. Constant tieoffs require an explicit SSOT constant/tieoff allowance.\nSSOT ref: quality_gates.rtl_gen.top_output_drive_evidence.\nOwner: pl330_target in rtl/pl330_target.sv via top_fallback.",
      "evidence_terms": [],
      "gate_todo": {
        "artifact": "rtl/rtl_todo_plan.json",
        "kind": "top_output_drive_evidence",
        "profile": "production",
        "stage": "rtl-gen"
      },
      "id": "RTL-0011",
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "priority": "critical",
      "required": true,
      "source_ref": "quality_gates.rtl_gen.top_output_drive_evidence",
      "ssot_context": {},
      "ssot_refs": [
        "quality_gates",
        "quality_gates.rtl_gen.top_output_drive_evidence"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 5,
        "evidence_basis": [
          "rtl_todo_plan.json gate_todo.kind",
          "rtl_todo_plan.json task criteria",
          "rtl/rtl_todo_plan.json"
        ],
        "reason": "SSOT top outputs have non-placeholder RTL drive evidence.",
        "required": true,
        "status": "pass"
      }
    },
    {
      "category": "rtl_gate.rtl_gen",
      "content": "Gate: SSOT top inputs are consumed by RTL logic or child inputs",
      "criteria": [
        "Every non-clock/reset SSOT input/inout top contract has consumption evidence in the RTL top",
        "Child-instance consumption evidence uses a declared child input/inout port, not an unknown direction",
        "Unused or reserved inputs are accepted only when explicitly waived by SSOT",
        "Traceability keeps source_ref quality_gates.rtl_gen.top_input_consumption_evidence",
        "Primary implementation evidence is in rtl/pl330_target.sv"
      ],
      "detail": "Declaring input ports is not enough. Each SSOT-declared non-clock/reset top input must feed real RTL logic, a procedural/control expression, or a declared child-module input/inout connection. Unused inputs require an explicit SSOT unused/reserved allowance.\nSSOT ref: quality_gates.rtl_gen.top_input_consumption_evidence.\nOwner: pl330_target in rtl/pl330_target.sv via top_fallback.",
      "evidence_terms": [],
      "gate_todo": {
        "artifact": "rtl/rtl_todo_plan.json",
        "kind": "top_input_consumption_evidence",
        "profile": "production",
        "stage": "rtl-gen"
      },
      "id": "RTL-0012",
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "priority": "critical",
      "required": true,
      "source_ref": "quality_gates.rtl_gen.top_input_consumption_evidence",
      "ssot_context": {},
      "ssot_refs": [
        "quality_gates",
        "quality_gates.rtl_gen.top_input_consumption_evidence"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 5,
        "evidence_basis": [
          "rtl_todo_plan.json gate_todo.kind",
          "rtl_todo_plan.json task criteria",
          "rtl/rtl_todo_plan.json"
        ],
        "reason": "SSOT top inputs have RTL consumption evidence.",
        "required": true,
        "status": "pass"
      }
    },
    {
      "category": "rtl_gate.rtl_gen",
      "content": "Gate: manifest-owned RTL modules are integrated into the top hierarchy",
      "criteria": [
        "Every manifest-owned non-top submodule is declared in listed DUT RTL sources",
        "Each child module is reachable from the SSOT top module through SystemVerilog instantiation",
        "A disconnected child file or flattened top cannot close the manifest hierarchy gate",
        "Traceability keeps source_ref quality_gates.rtl_gen.manifest_hierarchy_integration",
        "Primary implementation evidence is in rtl/pl330_target.sv"
      ],
      "detail": "File existence is not enough for general IP RTL. Every SSOT manifest-owned non-top RTL module must be declared and reachable from the SSOT top through real module instantiation.\nSSOT ref: quality_gates.rtl_gen.manifest_hierarchy_integration.\nOwner: pl330_target in rtl/pl330_target.sv via top_fallback.",
      "evidence_terms": [],
      "gate_todo": {
        "artifact": "rtl/rtl_todo_plan.json",
        "kind": "manifest_hierarchy_integration",
        "profile": "production",
        "stage": "rtl-gen"
      },
      "id": "RTL-0013",
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "priority": "critical",
      "required": true,
      "source_ref": "quality_gates.rtl_gen.manifest_hierarchy_integration",
      "ssot_context": {},
      "ssot_refs": [
        "quality_gates",
        "quality_gates.rtl_gen.manifest_hierarchy_integration"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 5,
        "evidence_basis": [
          "rtl_todo_plan.json gate_todo.kind",
          "rtl_todo_plan.json task criteria",
          "rtl/rtl_todo_plan.json"
        ],
        "reason": "9 manifest hierarchy integration issue(s) remain. pl330_target_engine: SSOT manifest child module is declared but not reachable from the top RTL hierarchy; pl330_target_pipeline: SSOT manifest child module is declared but not reachable from the top RTL hierarchy; pl330_target_lsq: SSOT manifest child module is declared but not reachable from the top RTL hierarchy",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "rtl_gate.rtl_gen",
      "content": "Gate: manifest-owned child instances have machine-checkable port connections",
      "criteria": [
        "Each reachable manifest child instance uses named port mapping",
        "Every declared child port is connected by name on at least one reachable instance",
        "No child port connection is empty unless represented by an explicit SSOT waiver",
        "Traceability keeps source_ref quality_gates.rtl_gen.manifest_port_connection_evidence",
        "Primary implementation evidence is in rtl/pl330_target.sv"
      ],
      "detail": "Reachability alone is not enough. Every reachable SSOT manifest-owned child module with declared ports must be instantiated with named, non-empty port connections so ATLAS can audit wrapper wiring for general IPs.\nSSOT ref: quality_gates.rtl_gen.manifest_port_connection_evidence.\nOwner: pl330_target in rtl/pl330_target.sv via top_fallback.",
      "evidence_terms": [],
      "gate_todo": {
        "artifact": "rtl/rtl_todo_plan.json",
        "kind": "manifest_port_connection_evidence",
        "profile": "production",
        "stage": "rtl-gen"
      },
      "id": "RTL-0014",
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "priority": "critical",
      "required": true,
      "source_ref": "quality_gates.rtl_gen.manifest_port_connection_evidence",
      "ssot_context": {},
      "ssot_refs": [
        "quality_gates",
        "quality_gates.rtl_gen.manifest_port_connection_evidence"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 5,
        "evidence_basis": [
          "rtl_todo_plan.json gate_todo.kind",
          "rtl_todo_plan.json task criteria",
          "rtl/rtl_todo_plan.json"
        ],
        "reason": "Every reachable manifest child instance has named, non-empty port connections.",
        "required": true,
        "status": "pass"
      }
    },
    {
      "category": "rtl_gate.rtl_gen",
      "content": "Gate: manifest child port connections carry live RTL signal flow",
      "criteria": [
        "Reachable manifest child input/inout ports are not tied to constants without an SSOT connection/tieoff allowance",
        "Reachable manifest child output/inout ports are consumed by top outputs, parent RTL logic, or declared child inputs/inouts",
        "Named port-map entries reference ports declared by the child module",
        "Traceability keeps source_ref quality_gates.rtl_gen.manifest_signal_flow_evidence",
        "Primary implementation evidence is in rtl/pl330_target.sv"
      ],
      "detail": "Named port maps prove that ports are connected, but not that the connected signals are useful. Child inputs must not be placeholder constants unless SSOT explicitly allows the tieoff, and child outputs must feed a top output, parent logic, or another declared child input/inout.\nSSOT ref: quality_gates.rtl_gen.manifest_signal_flow_evidence.\nOwner: pl330_target in rtl/pl330_target.sv via top_fallback.",
      "evidence_terms": [],
      "gate_todo": {
        "artifact": "rtl/rtl_todo_plan.json",
        "kind": "manifest_signal_flow_evidence",
        "profile": "production",
        "stage": "rtl-gen"
      },
      "id": "RTL-0015",
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "priority": "critical",
      "required": true,
      "source_ref": "quality_gates.rtl_gen.manifest_signal_flow_evidence",
      "ssot_context": {},
      "ssot_refs": [
        "quality_gates",
        "quality_gates.rtl_gen.manifest_signal_flow_evidence"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 5,
        "evidence_basis": [
          "rtl_todo_plan.json gate_todo.kind",
          "rtl_todo_plan.json task criteria",
          "rtl/rtl_todo_plan.json"
        ],
        "reason": "1 manifest signal-flow issue(s) remain. pl330_target: None: No reachable manifest child port flow evidence was found",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "rtl_gate.rtl_gen",
      "content": "Gate: SSOT connection contracts match RTL child port maps",
      "criteria": [
        "Production-profile multi-module IPs provide machine-readable integration.connections or sub_modules[].connections",
        "Each SSOT connection contract resolves to a reachable manifest child module and port",
        "RTL named port-map expressions match the SSOT-intended signal terms or carry an explicit SSOT waiver",
        "Traceability keeps source_ref quality_gates.rtl_gen.manifest_connection_contract_evidence",
        "Primary implementation evidence is in rtl/pl330_target.sv"
      ],
      "detail": "Named port maps prove that child instances are wired, but not that they are wired to the SSOT-intended signals. When the SSOT provides integration.connections or sub_modules[].connections, rtl-gen must satisfy those machine-readable connection contracts. Production-profile multi-module RTL must provide such contracts.\nSSOT ref: quality_gates.rtl_gen.manifest_connection_contract_evidence.\nOwner: pl330_target in rtl/pl330_target.sv via top_fallback.",
      "evidence_terms": [],
      "gate_todo": {
        "artifact": "rtl/rtl_todo_plan.json",
        "kind": "manifest_connection_contract_evidence",
        "profile": "production",
        "stage": "rtl-gen"
      },
      "id": "RTL-0016",
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "priority": "critical",
      "required": true,
      "source_ref": "quality_gates.rtl_gen.manifest_connection_contract_evidence",
      "ssot_context": {},
      "ssot_refs": [
        "quality_gates",
        "quality_gates.rtl_gen.manifest_connection_contract_evidence"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 5,
        "evidence_basis": [
          "rtl_todo_plan.json gate_todo.kind",
          "rtl_todo_plan.json task criteria",
          "rtl/rtl_todo_plan.json"
        ],
        "reason": "1 SSOT connection contract issue(s) remain. connection: Production-profile multi-module RTL has no machine-readable SSOT connection contracts",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "rtl_gate.rtl_gen",
      "content": "Gate: DUT-only RTL compile report passes after the final RTL edit",
      "criteria": [
        "rtl/rtl_compile.json exists",
        "rtl_compile.json reports dut_only=true",
        "rtl_compile.json passed=true with zero errors, diagnostics, and style violations",
        "rtl_compile.json is newer than or equal to every listed DUT RTL source",
        "rtl_compile.json rtl_files covers the current DUT filelist Verilog/SystemVerilog sources",
        "Traceability keeps source_ref quality_gates.rtl_gen.dut_compile",
        "Primary implementation evidence is in rtl/pl330_target.sv"
      ],
      "detail": "Compile approval must come from the canonical rtl_compile_report.py artifact generated after RTL generation or repair.\nSSOT ref: quality_gates.rtl_gen.dut_compile.\nOwner: pl330_target in rtl/pl330_target.sv via top_fallback.",
      "evidence_terms": [],
      "gate_todo": {
        "artifact": "rtl/rtl_compile.json",
        "kind": "dut_compile",
        "profile": "production",
        "stage": "rtl-gen"
      },
      "id": "RTL-0017",
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "priority": "critical",
      "required": true,
      "source_ref": "quality_gates.rtl_gen.dut_compile",
      "ssot_context": {},
      "ssot_refs": [
        "quality_gates",
        "quality_gates.rtl_gen.dut_compile"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 7,
        "evidence_basis": [
          "rtl_todo_plan.json gate_todo.kind",
          "rtl_todo_plan.json task criteria",
          "rtl/rtl_compile.json"
        ],
        "reason": "Missing canonical DUT compile artifact: rtl/rtl_compile.json.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "rtl_gate.rtl_gen",
      "content": "Gate: DUT-only lint report passes after the final RTL edit",
      "criteria": [
        "lint/dut_lint.json exists",
        "dut_lint.json reports dut_only=true",
        "dut_lint.json passed=true with zero errors and zero warnings",
        "dut_lint.json is newer than or equal to every listed DUT RTL source",
        "dut_lint.json rtl_files covers the current DUT filelist RTL/header sources",
        "No ad-hoc lint suppression violation remains unless represented by an exact SSOT waiver",
        "Traceability keeps source_ref quality_gates.rtl_gen.dut_lint",
        "Primary implementation evidence is in rtl/pl330_target.sv"
      ],
      "detail": "Lint approval must come from the canonical dut_lint_report.py artifact and must not rely on ad-hoc suppressions.\nSSOT ref: quality_gates.rtl_gen.dut_lint.\nOwner: pl330_target in rtl/pl330_target.sv via top_fallback.",
      "evidence_terms": [],
      "gate_todo": {
        "artifact": "lint/dut_lint.json",
        "kind": "dut_lint",
        "profile": "production",
        "stage": "rtl-gen"
      },
      "id": "RTL-0018",
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "priority": "critical",
      "required": true,
      "source_ref": "quality_gates.rtl_gen.dut_lint",
      "ssot_context": {},
      "ssot_refs": [
        "quality_gates",
        "quality_gates.rtl_gen.dut_lint"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 8,
        "evidence_basis": [
          "rtl_todo_plan.json gate_todo.kind",
          "rtl_todo_plan.json task criteria",
          "lint/dut_lint.json"
        ],
        "reason": "Missing canonical DUT lint artifact: lint/dut_lint.json.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "rtl_gate.rtl_gen",
      "content": "Gate: every required rtl_todo_plan item is closed before rtl-gen PASS",
      "criteria": [
        "Every required non-closure task has todo_completion.status=pass",
        "open_required_todos is zero",
        "all_required_todos_pass is true",
        "Traceability keeps source_ref quality_gates.rtl_gen.dynamic_todo_closure",
        "Primary implementation evidence is in rtl/pl330_target.sv"
      ],
      "detail": "rtl-gen PASS is forbidden until all required implementation, SSOT workflow, and RTL gate TODOs have pass status.\nSSOT ref: quality_gates.rtl_gen.dynamic_todo_closure.\nOwner: pl330_target in rtl/pl330_target.sv via top_fallback.",
      "evidence_terms": [],
      "gate_todo": {
        "artifact": "rtl/rtl_todo_plan.json",
        "kind": "dynamic_todo_closure",
        "profile": "production",
        "stage": "rtl-gen"
      },
      "id": "RTL-0019",
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "priority": "critical",
      "required": true,
      "source_ref": "quality_gates.rtl_gen.dynamic_todo_closure",
      "ssot_context": {},
      "ssot_refs": [
        "quality_gates",
        "quality_gates.rtl_gen.dynamic_todo_closure"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 5,
        "evidence_basis": [
          "rtl_todo_plan.json gate_todo.kind",
          "rtl_todo_plan.json task criteria",
          "rtl/rtl_todo_plan.json"
        ],
        "reason": "16 required non-closure TODO(s) remain open.",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "rtl_gate.rtl_gen",
      "content": "Gate: production RTL uses locked SSOT/FL/coverage authority artifacts",
      "criteria": [
        "governance/authority.json exists",
        "authority.json is the current IP human_llm_authority_manifest",
        "authority operating rules R1..R6 and LLM loops L1..L9 are present",
        "human authority gates G1..G7 are approved before production RTL-GEN",
        "repo_layout separates locked SSOT/model/coverage truth from LLM-editable rtl/tb/sim/report work",
        "model/functional_model.py exists",
        "model/fl_model_check.json passed=true",
        "model/model_signature.json matches the current SSOT-derived golden model signature",
        "model/decomposition.json complete=true with unblocked implementation units",
        "cov/fcov_plan.json has planned bins before RTL signoff",
        "verify/equivalence_goals.json has required, unblocked goals",
        "Traceability keeps source_ref quality_gates.rtl_gen.golden_authority_artifacts",
        "Primary implementation evidence is in rtl/pl330_target.sv"
      ],
      "detail": "PL330-level RTL cannot proceed from prose alone. It must carry machine-readable authority artifacts that separate human-owned truth from LLM-editable implementation.\nSSOT ref: quality_gates.rtl_gen.golden_authority_artifacts.\nOwner: pl330_target in rtl/pl330_target.sv via top_fallback.",
      "evidence_terms": [],
      "gate_todo": {
        "artifact": "governance/authority.json",
        "kind": "golden_authority_artifacts",
        "profile": "production",
        "stage": "rtl-gen"
      },
      "id": "RTL-0020",
      "owner_file": "rtl/pl330_target.sv",
      "owner_module": "pl330_target",
      "priority": "critical",
      "required": true,
      "source_ref": "quality_gates.rtl_gen.golden_authority_artifacts",
      "ssot_context": {},
      "ssot_refs": [
        "quality_gates",
        "quality_gates.rtl_gen.golden_authority_artifacts"
      ],
      "static_evidence": {
        "required": false,
        "status": "not_required"
      },
      "todo_completion": {
        "criteria_total": 13,
        "evidence_basis": [
          "rtl_todo_plan.json gate_todo.kind",
          "rtl_todo_plan.json task criteria",
          "governance/authority.json"
        ],
        "reason": "Human authority gate(s) required before production RTL-GEN are not approved: G1=pending",
        "required": true,
        "status": "open"
      }
    },
    {
      "category": "rtl_gate.rtl_gen",
      "content": "Gate: production RTL scale target is locked or explicitly waived",
      "criteria": [
        "Reference-derived suggested_ssot_target_scale candidates are review inputs only",
        "SSOT quality_gates.rtl_gen.target_scale contains human-locked structural depth minima before PL330-level PASS claims",
        "If target scale is intentionally not enforced, SSOT contains target_scale_waiver.approved=true with a rationale",
        "Traceability keeps source_ref quality_gates.rtl_gen.target_scale",
        "Primary implementation evidence is 
... <truncated 12035 chars>

Current packet Markdown (rtl/authoring_packets/rtl_gate_closure.md):
# RTL Authoring Packet: rtl_gate_closure

- Kind: gate
- Owner module: pl330_target
- Owner file: rtl/pl330_target.sv
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
- Draft allowed: False
- PASS allowed: False
- Integration signoff allowed: False
- LLM-actionable open tasks: 6
- Human-locked open tasks: 7
- Reference scale profile: reports/rtl_reference_profile.json (calibration-only, files=143, modules=210, lines=130568)
- Reference target-scale candidate present; SSOT target_scale is not locked yet
- Connection contract gap: Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.
- Locked-truth blockers:
  - manifest_connection_contract_evidence: Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.
  - manifest_connection_contract_evidence: 1 SSOT connection contract issue(s) remain. connection: Production-profile multi-module RTL has no machine-readable SSOT connection contracts
  - golden_authority_artifacts: Human authority gate(s) required before production RTL-GEN are not approved: G1=pending
  - target_scale_policy: Reference profile provides suggested_ssot_target_scale, but SSOT target_scale is not locked and no approved waiver is present.
  - protocol_assertion_evidence: Missing protocol assertion simulation evidence: sim/assertion_failures.jsonl.
  - fl_rtl_goal_audit: Missing FL-vs-RTL goal audit artifact: sim/fl_rtl_goal_audit.json.
  - coverage_closure: Missing coverage closure artifact: cov/coverage.json.
- SSOT top IO contracts: 11

## Tasks

### RTL-0003: Gate: SSOT function_model and cycle_model are present before RTL generation

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.ssot_required_sections
- Detail: rtl-gen cannot implement production RTL until the SSOT contains both the functional golden behavior and the cycle/handshake contract.
SSOT ref: quality_gates.rtl_gen.ssot_required_sections.
Owner: pl330_target in rtl/pl330_target.sv via top_fallback.
- Current reason: SSOT function_model and cycle_model authority is present.
- Criteria:
  - function_model is present and non-empty in the SSOT
  - cycle_model is present and non-empty in the SSOT
  - Missing authority artifacts open a human/ssot-gen gate instead of being bypassed in RTL
  - Traceability keeps source_ref quality_gates.rtl_gen.ssot_required_sections
  - Primary implementation evidence is in rtl/pl330_target.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.ssot_required_sections

### RTL-0004: Gate: SSOT-authored rtl-gen workflow TODOs are well formed

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.workflow_todo_contract
- Detail: Every SSOT workflow_todos.rtl-gen item must be executable by rtl-gen and therefore must carry content, detail, and criteria.
SSOT ref: quality_gates.rtl_gen.workflow_todo_contract.
Owner: pl330_target in rtl/pl330_target.sv via top_fallback.
- Current reason: SSOT-authored rtl-gen workflow TODOs are well formed.
- Criteria:
  - Every workflow_todos.rtl-gen item has content
  - Every workflow_todos.rtl-gen item has detail
  - Every workflow_todos.rtl-gen item has at least one criteria entry
  - Traceability keeps source_ref quality_gates.rtl_gen.workflow_todo_contract
  - Primary implementation evidence is in rtl/pl330_target.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.workflow_todo_contract

### RTL-0005: Gate: every SSOT-derived RTL behavior has an owner module

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.owner_traceability
- Detail: Function-level, cycle-level, register, dataflow, and FSM behavior must map to an RTL owner module before approval.
SSOT ref: quality_gates.rtl_gen.owner_traceability.
Owner: pl330_target in rtl/pl330_target.sv via top_fallback.
- Current reason: Every required SSOT-derived RTL behavior has an owner module.
- Criteria:
  - No required function_model task is orphaned
  - No required cycle_model task is orphaned
  - No required register/dataflow/FSM task is orphaned
  - Owner module and owner file are recorded in rtl_todo_plan.json
  - Traceability keeps source_ref quality_gates.rtl_gen.owner_traceability
  - Primary implementation evidence is in rtl/pl330_target.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.owner_traceability

### RTL-0006: Gate: RTL is authored by common_ai_agent rtl-gen, not by direct operator edits

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.common_ai_agent_authoring
- Detail: RTL approval requires provenance that the common engine/ATLAS/Textual/headless rtl-gen path wrote the RTL from the current SSOT-derived TODO plan.
SSOT ref: quality_gates.rtl_gen.common_ai_agent_authoring.
Owner: pl330_target in rtl/pl330_target.sv via top_fallback.
- Current reason: RTL authoring provenance proves common_ai_agent rtl-gen ownership.
- Criteria:
  - rtl/rtl_authoring_provenance.json exists
  - provenance agent is common_ai_agent
  - provenance workflow is rtl-gen
  - provenance surface is atlas_ui, textual_ui, or headless_common_engine
  - provenance todo_plan_sha256 matches the current rtl_todo_plan.json
  - provenance rtl_files lists every SSOT manifest RTL file
  - provenance rtl_files covers the current DUT filelist sources
  - Traceability keeps source_ref quality_gates.rtl_gen.common_ai_agent_authoring
  - Primary implementation evidence is in rtl/pl330_target.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.common_ai_agent_authoring

### RTL-0007: Gate: required SSOT behavior has static DUT RTL evidence after audit

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.static_rtl_evidence
- Detail: After RTL exists, derive_rtl_todos.py --audit-rtl must find concrete DUT source terms for every static-evidence-required task.
SSOT ref: quality_gates.rtl_gen.static_rtl_evidence.
Owner: pl330_target in rtl/pl330_target.sv via top_fallback.
- Current reason: 5 static-evidence-required task(s) still lack DUT RTL evidence.
- Criteria:
  - derive_rtl_todos.py --audit-rtl ran after the final RTL edit
  - rtl_todo_plan.json static_rtl_evidence.missing is zero
  - Rich SSOT-derived tasks match multiple owner-file RTL evidence terms, not a single incidental token
  - No task requiring DUT evidence is satisfied only by comments, TB, scoreboard, or FunctionalModel code
  - Traceability keeps source_ref quality_gates.rtl_gen.static_rtl_evidence
  - Primary implementation evidence is in rtl/pl330_target.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.static_rtl_evidence

### RTL-0008: Gate: behavior-owner RTL modules contain real implementation structure

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.owner_logic_structure_evidence
- Detail: Static token evidence is not enough. Each SSOT behavior-owner RTL module must contain real assign/procedural/state structure appropriate for its owned function_model, cycle_model, register, memory, or FSM contract.
SSOT ref: quality_gates.rtl_gen.owner_logic_structure_evidence.
Owner: pl330_target in rtl/pl330_target.sv via top_fallback.
- Current reason: Behavior-owner RTL modules contain real implementation structure.
- Criteria:
  - Every active behavior-owner module is declared in its owner file
  - Behavior-owner modules contain non-placeholder assign/procedural implementation logic
  - State/register/memory/FSM owners contain sequential or storage-update evidence, not only token mentions
  - Traceability keeps source_ref quality_gates.rtl_gen.owner_logic_structure_evidence
  - Primary implementation evidence is in rtl/pl330_target.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.owner_logic_structure_evidence

### RTL-0009: Gate: RTL sources contain no placeholder implementation markers

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.rtl_placeholder_free_evidence
- Detail: Production RTL cannot carry TODO/TBD/FIXME/stub/dummy/not-implemented markers in source code or comments. If behavior is intentionally reserved, it must be expressed in the SSOT as a waiver or explicit tieoff/unused contract.
SSOT ref: quality_gates.rtl_gen.rtl_placeholder_free_evidence.
Owner: pl330_target in rtl/pl330_target.sv via top_fallback.
- Current reason: RTL sources contain no placeholder implementation markers.
- Criteria:
  - Listed RTL source files contain no TODO/TBD/FIXME/HACK markers
  - Listed RTL source files contain no placeholder/stub/dummy/not-implemented implementation text
  - Intentional reserved behavior is represented in SSOT contracts instead of RTL placeholder comments
  - Traceability keeps source_ref quality_gates.rtl_gen.rtl_placeholder_free_evidence
  - Primary implementation evidence is in rtl/pl330_target.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.rtl_placeholder_free_evidence

### RTL-0010: Gate: SSOT top IO contracts match the RTL top module

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.top_io_contract_evidence
- Detail: The top wrapper must expose the SSOT-declared clock/reset and explicit IO ports. A compiling top with missing, renamed, or wrong-direction ports cannot close RTL generation.
SSOT ref: quality_gates.rtl_gen.top_io_contract_evidence.
Owner: pl330_target in rtl/pl330_target.sv via top_fallback.
- Current reason: SSOT top IO contracts match the RTL top declaration.
- Criteria:
  - SSOT clock/reset names are declared on the RTL top module
  - Explicit io_list ports/signals are declared on the RTL top module
  - Known SSOT directions and simple widths match RTL declarations
  - Traceability keeps source_ref quality_gates.rtl_gen.top_io_contract_evidence
  - Primary implementation evidence is in rtl/pl330_target.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.top_io_contract_evidence

### RTL-0011: Gate: SSOT top outputs are driven by real RTL logic

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.top_output_drive_evidence
- Detail: Declaring output ports is not enough. Each SSOT-declared top output must be driven by nonconstant RTL logic, a procedural assignment, or a declared child-module output connection. Constant tieoffs require an explicit SSOT constant/tieoff allowance.
SSOT ref: quality_gates.rtl_gen.top_output_drive_evidence.
Owner: pl330_target in rtl/pl330_target.sv via top_fallback.
- Current reason: SSOT top outputs have non-placeholder RTL drive evidence.
- Criteria:
  - Every SSOT output/inout top contract has drive evidence in the RTL top
  - Non-waived output constants are rejected as placeholder tieoffs
  - Child-instance drive evidence uses a declared child output/inout port, not an unknown direction
  - Traceability keeps source_ref quality_gates.rtl_gen.top_output_drive_evidence
  - Primary implementation evidence is in rtl/pl330_target.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.top_output_drive_evidence

### RTL-0012: Gate: SSOT top inputs are consumed by RTL logic or child inputs

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.top_input_consumption_evidence
- Detail: Declaring input ports is not enough. Each SSOT-declared non-clock/reset top input must feed real RTL logic, a procedural/control expression, or a declared child-module input/inout connection. Unused inputs require an explicit SSOT unused/reserved allowance.
SSOT ref: quality_gates.rtl_gen.top_input_consumption_evidence.
Owner: pl330_target in rtl/pl330_target.sv via top_fallback.
- Current reason: SSOT top inputs have RTL consumption evidence.
- Criteria:
  - Every non-clock/reset SSOT input/inout top contract has consumption evidence in the RTL top
  - Child-instance consumption evidence uses a declared child input/inout port, not an unknown direction
  - Unused or reserved inputs are accepted only when explicitly waived by SSOT
  - Traceability keeps source_ref quality_gates.rtl_gen.top_input_consumption_evidence
  - Primary implementation evidence is in rtl/pl330_target.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.top_input_consumption_evidence

### RTL-0013: Gate: manifest-owned RTL modules are integrated into the top hierarchy

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.manifest_hierarchy_integration
- Detail: File existence is not enough for general IP RTL. Every SSOT manifest-owned non-top RTL module must be declared and reachable from the SSOT top through real module instantiation.
SSOT ref: quality_gates.rtl_gen.manifest_hierarchy_integration.
Owner: pl330_target in rtl/pl330_target.sv via top_fallback.
- Current reason: 9 manifest hierarchy integration issue(s) remain. pl330_target_engine: SSOT manifest child module is declared but not reachable from the top RTL hierarchy; pl330_target_pipeline: SSOT manifest child module is declared but not reachable from the top RTL hierarchy; pl330_target_lsq: SSOT manifest child module is declared but not reachable from the top RTL hierarchy
- Criteria:
  - Every manifest-owned non-top submodule is declared in listed DUT RTL sources
  - Each child module is reachable from the SSOT top module through SystemVerilog instantiation
  - A disconnected child file or flattened top cannot close the manifest hierarchy gate
  - Traceability keeps source_ref quality_gates.rtl_gen.manifest_hierarchy_integration
  - Primary implementation evidence is in rtl/pl330_target.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.manifest_hierarchy_integration

### RTL-0014: Gate: manifest-owned child instances have machine-checkable port connections

- Priority: critical
- Required: True
- Status: pass
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.manifest_port_connection_evidence
- Detail: Reachability alone is not enough. Every reachable SSOT manifest-owned child module with declared ports must be instantiated with named, non-empty port connections so ATLAS can audit wrapper wiring for general IPs.
SSOT ref: quality_gates.rtl_gen.manifest_port_connection_evidence.
Owner: pl330_target in rtl/pl330_target.sv via top_fallback.
- Current reason: Every reachable manifest child instance has named, non-empty port connections.
- Criteria:
  - Each reachable manifest child instance uses named port mapping
  - Every declared child port is connected by name on at least one reachable instance
  - No child port connection is empty unless represented by an explicit SSOT waiver
  - Traceability keeps source_ref quality_gates.rtl_gen.manifest_port_connection_evidence
  - Primary implementation evidence is in rtl/pl330_target.sv
- SSOT refs: quality_gates, quality_gates.rtl_gen.manifest_port_connection_evidence

### RTL-0015: Gate: manifest child port connections carry live RTL signal flow

- Priority: critical
- Required: True
- Status: open
- Category: rtl_gate.rtl_gen
- Source ref: quality_gates.rtl_gen.manifest_signal_flow_evidence
- Detail:
... <truncated 14395 chars>