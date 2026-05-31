# RTL Authoring Status: mctp_assembler_scratch

## Status

- Top: mctp_assembler_scratch
- Packets: 28
- LLM-actionable tasks: 21
- Human-locked tasks: 1
- Tool-evidence tasks: 1
- Deferred human QA allowed: True
- PASS allowed: False
- Target scale locked: False
- Pending connection-contract suggestions: 0
- Recommended packet batch limit: 4

## Next LLM Packets

- module__mctp_assembler_scratch_axi_write_ingress__dataflow: rtl/authoring_packets/module__mctp_assembler_scratch_axi_write_ingress__dataflow.json (llm_open=6, human_locked=0)
- module__mctp_assembler_scratch_context_table: rtl/authoring_packets/module__mctp_assembler_scratch_context_table.json (llm_open=1, human_locked=0)
- module__mctp_assembler_scratch_descriptor_queue: rtl/authoring_packets/module__mctp_assembler_scratch_descriptor_queue.json (llm_open=1, human_locked=0)
- module__mctp_assembler_scratch_apb_regfile__registers_01: rtl/authoring_packets/module__mctp_assembler_scratch_apb_regfile__registers_01.json (llm_open=9, human_locked=0)
- module__mctp_assembler_scratch_apb_regfile__features: rtl/authoring_packets/module__mctp_assembler_scratch_apb_regfile__features.json (llm_open=1, human_locked=0)
- module__mctp_assembler_scratch: rtl/authoring_packets/module__mctp_assembler_scratch.json (llm_open=1, human_locked=0)
- rtl_gate_evidence_closure: rtl/authoring_packets/rtl_gate_evidence_closure.json (llm_open=2, human_locked=0)

## Tool Evidence Queue

- rtl_gate_tool_evidence: tool_evidence=1, next_tool=audit-rtl, json=rtl/authoring_packets/rtl_gate_tool_evidence.json

## Human-Locked Queue

- rtl_gate_human_closure: human_locked=1, json=rtl/authoring_packets/rtl_gate_human_closure.json

## Rules

- Use rtl_todo_plan.json as the complete ledger and rtl_authoring_plan.json as the LLM work queue.
- Process one authoring packet at a time: module packets first, then unowned tasks if any, then rtl_gate_evidence_closure; leave rtl_gate_tool_evidence to tools and rtl_gate_contract_blocked/rtl_gate_human_closure to human-locked authority gaps.
- Generate real RTL; do not instantiate a fixed IP template or copy boilerplate as the implementation.
- Do not close static RTL evidence with comments: derive_rtl_todos.py strips comments before matching, so evidence_terms must be preserved in live lint-clean RTL identifiers/logic.
- Do not close static RTL evidence with evidence-only alias wires or marker-only helper wires; the matched identifiers must participate in real RTL behavior.
- Repair-generated FunctionModel fm*_observed markers are advisory schema-repair traceability only; do not create RTL ports, wires, or state solely for tasks tagged repair_generated_fm_marker.
- If reference_profile is present, use it only to understand implementation scale and decomposition gaps; never copy or clone reference RTL.
- After the top RTL exists, prioritize missing manifest child RTL packets before residual top-module slices.
- Keep locked authority artifacts unchanged unless a human approves a change request.
- Rerun rtl_todo_plan audit, compile, lint, sim, and coverage evidence until required TODOs pass.
