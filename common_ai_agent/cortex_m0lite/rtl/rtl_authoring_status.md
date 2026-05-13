# RTL Authoring Status: cortex_m0lite

## Status

- Top: cortex_m0lite
- Packets: 25
- LLM-actionable tasks: 20
- Human-locked tasks: 3
- Tool-evidence tasks: 7
- Deferred human QA allowed: True
- PASS allowed: False
- Target scale locked: True
- Pending connection-contract suggestions: 0
- Recommended packet batch limit: 4

## Next LLM Packets

- module__if_stage: rtl/authoring_packets/module__if_stage.json (llm_open=1, human_locked=0)
- module__id_stage: rtl/authoring_packets/module__id_stage.json (llm_open=1, human_locked=0)
- module__ex_stage: rtl/authoring_packets/module__ex_stage.json (llm_open=1, human_locked=0)
- module__wb_stage: rtl/authoring_packets/module__wb_stage.json (llm_open=1, human_locked=0)
- module__regfile: rtl/authoring_packets/module__regfile.json (llm_open=2, human_locked=0)
- module__bus_if: rtl/authoring_packets/module__bus_if.json (llm_open=3, human_locked=0)
- module__cortex_m0lite_core__function_model: rtl/authoring_packets/module__cortex_m0lite_core__function_model.json (llm_open=3, human_locked=0)
- module__cortex_m0lite_core__workflow_todo: rtl/authoring_packets/module__cortex_m0lite_core__workflow_todo.json (llm_open=2, human_locked=0)

## Tool Evidence Queue

- rtl_gate_tool_evidence: tool_evidence=7, next_tool=ssot-rtl, json=rtl/authoring_packets/rtl_gate_tool_evidence.json

## Human-Locked Queue

- rtl_gate_human_closure: human_locked=3, json=rtl/authoring_packets/rtl_gate_human_closure.json

## Rules

- Use rtl_todo_plan.json as the complete ledger and rtl_authoring_plan.json as the LLM work queue.
- Process one authoring packet at a time: module packets first, then unowned tasks if any, then rtl_gate_evidence_closure; leave rtl_gate_tool_evidence to tools and rtl_gate_contract_blocked/rtl_gate_human_closure to human-locked authority gaps.
- Generate real RTL; do not instantiate a fixed IP template or copy boilerplate as the implementation.
- If reference_profile is present, use it only to understand implementation scale and decomposition gaps; never copy or clone reference RTL.
- After the top RTL exists, prioritize missing manifest child RTL packets before residual top-module slices.
- Keep locked authority artifacts unchanged unless a human approves a change request.
- Rerun rtl_todo_plan audit, compile, lint, sim, and coverage evidence until required TODOs pass.
