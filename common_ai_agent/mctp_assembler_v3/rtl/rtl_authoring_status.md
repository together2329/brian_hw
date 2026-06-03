# RTL Authoring Status: mctp_assembler_v3

## Status

- Top: mctp_assembler_v3
- Packets: 34
- LLM-actionable tasks: 329
- Human-locked tasks: 1
- Tool-evidence tasks: 7
- Deferred human QA allowed: True
- PASS allowed: False
- Target scale locked: False
- Pending connection-contract suggestions: 0
- Recommended packet batch limit: 4

## Next LLM Packets

- module__mctp_assembler_v3_pcie_vdm_parser: rtl/authoring_packets/module__mctp_assembler_v3_pcie_vdm_parser.json (llm_open=24, human_locked=0)
- module__mctp_assembler_v3_mctp_decoder: rtl/authoring_packets/module__mctp_assembler_v3_mctp_decoder.json (llm_open=27, human_locked=0)
- module__mctp_assembler_v3_context_table__function_model: rtl/authoring_packets/module__mctp_assembler_v3_context_table__function_model.json (llm_open=46, human_locked=0)
- module__mctp_assembler_v3_context_table__fsm: rtl/authoring_packets/module__mctp_assembler_v3_context_table__fsm.json (llm_open=25, human_locked=0)
- module__mctp_assembler_v3_context_table__equivalence: rtl/authoring_packets/module__mctp_assembler_v3_context_table__equivalence.json (llm_open=1, human_locked=0)
- module__mctp_assembler_v3_context_table__parameters: rtl/authoring_packets/module__mctp_assembler_v3_context_table__parameters.json (llm_open=1, human_locked=0)
- module__mctp_assembler_v3_sram_packer: rtl/authoring_packets/module__mctp_assembler_v3_sram_packer.json (llm_open=24, human_locked=0)
- module__mctp_assembler_v3_descriptor_queue: rtl/authoring_packets/module__mctp_assembler_v3_descriptor_queue.json (llm_open=24, human_locked=0)

## Tool Evidence Queue

- rtl_gate_tool_evidence: tool_evidence=7, next_tool=ssot-rtl, json=rtl/authoring_packets/rtl_gate_tool_evidence.json

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
