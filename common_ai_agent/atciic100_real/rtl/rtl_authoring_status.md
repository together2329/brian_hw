# RTL Authoring Status: atciic100_real

## Status

- Top: atciic100_real
- Packets: 14
- LLM-actionable tasks: 230
- Human-locked tasks: 2
- Tool-evidence tasks: 7
- Deferred human QA allowed: True
- PASS allowed: False
- Target scale locked: False
- Pending connection-contract suggestions: 0
- Recommended packet batch limit: 4

## Next LLM Packets

- module__atciic100_apbslv: rtl/authoring_packets/module__atciic100_apbslv.json (llm_open=27, human_locked=0)
- module__atciic100_ctrl__function_model_01: rtl/authoring_packets/module__atciic100_ctrl__function_model_01.json (llm_open=48, human_locked=0)
- module__atciic100_ctrl__function_model_02: rtl/authoring_packets/module__atciic100_ctrl__function_model_02.json (llm_open=48, human_locked=0)
- module__atciic100_ctrl__cycle_model: rtl/authoring_packets/module__atciic100_ctrl__cycle_model.json (llm_open=22, human_locked=0)
- module__atciic100_ctrl__fsm: rtl/authoring_packets/module__atciic100_ctrl__fsm.json (llm_open=18, human_locked=0)
- module__atciic100_ctrl__function_model_03: rtl/authoring_packets/module__atciic100_ctrl__function_model_03.json (llm_open=2, human_locked=0)
- module__atciic100_ctrl__equivalence: rtl/authoring_packets/module__atciic100_ctrl__equivalence.json (llm_open=1, human_locked=0)
- module__atciic100_ctrl__workflow_todo: rtl/authoring_packets/module__atciic100_ctrl__workflow_todo.json (llm_open=1, human_locked=0)

## Tool Evidence Queue

- rtl_gate_tool_evidence: tool_evidence=7, next_tool=ssot-rtl, json=rtl/authoring_packets/rtl_gate_tool_evidence.json

## Human-Locked Queue

- rtl_gate_human_closure: human_locked=2, json=rtl/authoring_packets/rtl_gate_human_closure.json

## Rules

- Use rtl_todo_plan.json as the complete ledger and rtl_authoring_plan.json as the LLM work queue.
- Process one authoring packet at a time: module packets first, then unowned tasks if any, then rtl_gate_evidence_closure; leave rtl_gate_tool_evidence to tools and rtl_gate_contract_blocked/rtl_gate_human_closure to human-locked authority gaps.
- Generate real RTL; do not instantiate a fixed IP template or copy boilerplate as the implementation.
- If reference_profile is present, use it only to understand implementation scale and decomposition gaps; never copy or clone reference RTL.
- After the top RTL exists, prioritize missing manifest child RTL packets before residual top-module slices.
- Keep locked authority artifacts unchanged unless a human approves a change request.
- Rerun rtl_todo_plan audit, compile, lint, sim, and coverage evidence until required TODOs pass.
