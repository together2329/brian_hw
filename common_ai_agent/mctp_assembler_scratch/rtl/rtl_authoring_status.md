# RTL Authoring Status: mctp_assembler_scratch

## Status

- Top: mctp_assembler_scratch
- Packets: 28
- LLM-actionable tasks: 445
- Human-locked tasks: 4
- Tool-evidence tasks: 4
- Deferred human QA allowed: True
- PASS allowed: False
- Target scale locked: False
- Pending connection-contract suggestions: 0
- Recommended packet batch limit: 4

## Next LLM Packets

- module__mctp_assembler_scratch_axi_write_ingress__io_list: rtl/authoring_packets/module__mctp_assembler_scratch_axi_write_ingress__io_list.json (llm_open=23, human_locked=0)
- module__mctp_assembler_scratch_axi_write_ingress__test_requirements: rtl/authoring_packets/module__mctp_assembler_scratch_axi_write_ingress__test_requirements.json (llm_open=22, human_locked=0)
- module__mctp_assembler_scratch_axi_write_ingress__cycle_model: rtl/authoring_packets/module__mctp_assembler_scratch_axi_write_ingress__cycle_model.json (llm_open=16, human_locked=0)
- module__mctp_assembler_scratch_axi_write_ingress__function_model: rtl/authoring_packets/module__mctp_assembler_scratch_axi_write_ingress__function_model.json (llm_open=13, human_locked=0)
- module__mctp_assembler_scratch_axi_write_ingress__dataflow: rtl/authoring_packets/module__mctp_assembler_scratch_axi_write_ingress__dataflow.json (llm_open=7, human_locked=0)
- module__mctp_assembler_scratch_axi_write_ingress__equivalence: rtl/authoring_packets/module__mctp_assembler_scratch_axi_write_ingress__equivalence.json (llm_open=1, human_locked=0)
- module__mctp_assembler_scratch_pcie_vdm_parser: rtl/authoring_packets/module__mctp_assembler_scratch_pcie_vdm_parser.json (llm_open=34, human_locked=0)
- module__mctp_assembler_scratch_mctp_parser: rtl/authoring_packets/module__mctp_assembler_scratch_mctp_parser.json (llm_open=18, human_locked=0)

## Tool Evidence Queue

- rtl_gate_tool_evidence: tool_evidence=4, next_tool=ssot-rtl, json=rtl/authoring_packets/rtl_gate_tool_evidence.json

## Human-Locked Queue

- rtl_gate_human_closure: human_locked=4, json=rtl/authoring_packets/rtl_gate_human_closure.json

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
