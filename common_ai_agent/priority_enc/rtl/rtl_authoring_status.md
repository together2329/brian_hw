# RTL Authoring Status: priority_enc

## Status

- Top: priority_enc
- Packets: 8
- LLM-actionable tasks: 94
- Human-locked tasks: 9
- Tool-evidence tasks: 7
- Deferred human QA allowed: False
- PASS allowed: False
- Target scale locked: True
- Pending connection-contract suggestions: 23
- Recommended packet batch limit: 4

## Next LLM Packets

- module__priority_enc_regs: rtl/authoring_packets/module__priority_enc_regs.json (llm_open=12, human_locked=0)
- module__priority_enc_core: rtl/authoring_packets/module__priority_enc_core.json (llm_open=29, human_locked=0)
- module__priority_enc: rtl/authoring_packets/module__priority_enc.json (llm_open=39, human_locked=0)
- unowned_tasks: rtl/authoring_packets/unowned_tasks.json (llm_open=4, human_locked=0)
- rtl_gate_evidence_closure: rtl/authoring_packets/rtl_gate_evidence_closure.json (llm_open=10, human_locked=0)

## Tool Evidence Queue

- rtl_gate_tool_evidence: tool_evidence=7, next_tool=ssot-rtl, json=rtl/authoring_packets/rtl_gate_tool_evidence.json

## Human-Locked Queue

- rtl_gate_contract_blocked: human_locked=2, json=rtl/authoring_packets/rtl_gate_contract_blocked.json
- rtl_gate_human_closure: human_locked=7, json=rtl/authoring_packets/rtl_gate_human_closure.json

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
