# RTL Authoring Status: edge_detector

## Status

- Top: edge_detector
- Packets: 20
- LLM-actionable tasks: 111
- Human-locked tasks: 2
- Tool-evidence tasks: 7
- Deferred human QA allowed: True
- PASS allowed: False
- Target scale locked: True
- Pending connection-contract suggestions: 0
- Recommended packet batch limit: 4

## Next LLM Packets

- module__edge_detector__function_model: rtl/authoring_packets/module__edge_detector__function_model.json (llm_open=20, human_locked=0)
- module__edge_detector__io_list: rtl/authoring_packets/module__edge_detector__io_list.json (llm_open=14, human_locked=0)
- module__edge_detector__cycle_model: rtl/authoring_packets/module__edge_detector__cycle_model.json (llm_open=13, human_locked=0)
- module__edge_detector__registers: rtl/authoring_packets/module__edge_detector__registers.json (llm_open=12, human_locked=0)
- module__edge_detector__test_requirements: rtl/authoring_packets/module__edge_detector__test_requirements.json (llm_open=12, human_locked=0)
- module__edge_detector__integration: rtl/authoring_packets/module__edge_detector__integration.json (llm_open=8, human_locked=0)
- module__edge_detector__synthesis: rtl/authoring_packets/module__edge_detector__synthesis.json (llm_open=7, human_locked=0)
- module__edge_detector__parameters: rtl/authoring_packets/module__edge_detector__parameters.json (llm_open=5, human_locked=0)

## Tool Evidence Queue

- rtl_gate_tool_evidence: tool_evidence=7, next_tool=ssot-rtl, json=rtl/authoring_packets/rtl_gate_tool_evidence.json

## Human-Locked Queue

- rtl_gate_human_closure: human_locked=2, json=rtl/authoring_packets/rtl_gate_human_closure.json

## Rules

- Use rtl_todo_plan.json as the complete ledger and rtl_authoring_plan.json as the LLM work queue.
- Process one authoring packet at a time: module packets first, then unowned tasks if any, then rtl_gate_evidence_closure; leave rtl_gate_tool_evidence to tools and rtl_gate_contract_blocked/rtl_gate_human_closure to human-locked authority gaps.
- Generate real RTL; do not instantiate a fixed IP template or copy boilerplate as the implementation.
- Do not close static RTL evidence with comments: derive_rtl_todos.py strips comments before matching, so evidence_terms must be preserved in live lint-clean RTL identifiers/logic.
- Do not close static RTL evidence with evidence-only alias/dummy wires; the matched identifiers must participate in real RTL behavior.
- If reference_profile is present, use it only to understand implementation scale and decomposition gaps; never copy or clone reference RTL.
- After the top RTL exists, prioritize missing manifest child RTL packets before residual top-module slices.
- Keep locked authority artifacts unchanged unless a human approves a change request.
- Rerun rtl_todo_plan audit, compile, lint, sim, and coverage evidence until required TODOs pass.
