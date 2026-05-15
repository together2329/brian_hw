# RTL Authoring Status: clkdiv

## Status

- Top: clkdiv
- Packets: 10
- LLM-actionable tasks: 147
- Human-locked tasks: 2
- Tool-evidence tasks: 7
- Deferred human QA allowed: True
- PASS allowed: False
- Target scale locked: False
- Pending connection-contract suggestions: 0
- Recommended packet batch limit: 4

## Next LLM Packets

- module__clkdiv_regs: rtl/authoring_packets/module__clkdiv_regs.json (llm_open=34, human_locked=0)
- module__clkdiv_core__function_model: rtl/authoring_packets/module__clkdiv_core__function_model.json (llm_open=30, human_locked=0)
- module__clkdiv_core__cycle_model: rtl/authoring_packets/module__clkdiv_core__cycle_model.json (llm_open=18, human_locked=0)
- module__clkdiv_core__fsm: rtl/authoring_packets/module__clkdiv_core__fsm.json (llm_open=8, human_locked=0)
- module__clkdiv_core__equivalence: rtl/authoring_packets/module__clkdiv_core__equivalence.json (llm_open=1, human_locked=0)
- module__clkdiv_core__workflow_todo: rtl/authoring_packets/module__clkdiv_core__workflow_todo.json (llm_open=1, human_locked=0)
- module__clkdiv: rtl/authoring_packets/module__clkdiv.json (llm_open=46, human_locked=0)
- rtl_gate_evidence_closure: rtl/authoring_packets/rtl_gate_evidence_closure.json (llm_open=9, human_locked=0)

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
