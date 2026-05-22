# RTL Authoring Status: cortex_m0lite

## Status

- Top: cortex_m0lite
- Packets: 25
- LLM-actionable tasks: 175
- Human-locked tasks: 7
- Tool-evidence tasks: 7
- Deferred human QA allowed: True
- PASS allowed: False
- Target scale locked: True
- Pending connection-contract suggestions: 0
- Recommended packet batch limit: 4

## Next LLM Packets

- module__cortex_m0lite__io_list: rtl/authoring_packets/module__cortex_m0lite__io_list.json (llm_open=27, human_locked=0)
- module__cortex_m0lite__integration: rtl/authoring_packets/module__cortex_m0lite__integration.json (llm_open=10, human_locked=0)
- module__cortex_m0lite__synthesis: rtl/authoring_packets/module__cortex_m0lite__synthesis.json (llm_open=8, human_locked=0)
- module__cortex_m0lite__test_requirements: rtl/authoring_packets/module__cortex_m0lite__test_requirements.json (llm_open=6, human_locked=0)
- module__cortex_m0lite__features: rtl/authoring_packets/module__cortex_m0lite__features.json (llm_open=4, human_locked=0)
- module__cortex_m0lite__rtl_flow: rtl/authoring_packets/module__cortex_m0lite__rtl_flow.json (llm_open=2, human_locked=0)
- module__cortex_m0lite__security: rtl/authoring_packets/module__cortex_m0lite__security.json (llm_open=1, human_locked=0)
- module__cortex_m0lite_core__function_model: rtl/authoring_packets/module__cortex_m0lite_core__function_model.json (llm_open=28, human_locked=0)

## Tool Evidence Queue

- rtl_gate_tool_evidence: tool_evidence=7, next_tool=ssot-rtl, json=rtl/authoring_packets/rtl_gate_tool_evidence.json

## Human-Locked Queue

- rtl_gate_human_closure: human_locked=7, json=rtl/authoring_packets/rtl_gate_human_closure.json

## Rules

- Use rtl_todo_plan.json as the complete ledger and rtl_authoring_plan.json as the LLM work queue.
- Process one authoring packet at a time: module packets first, then unowned tasks if any, then rtl_gate_evidence_closure; leave rtl_gate_tool_evidence to tools and rtl_gate_contract_blocked/rtl_gate_human_closure to human-locked authority gaps.
- Generate real RTL; do not instantiate a fixed IP template or copy boilerplate as the implementation.
- If reference_profile is present, use it only to understand implementation scale and decomposition gaps; never copy or clone reference RTL.
- After the top RTL exists, prioritize missing manifest child RTL packets before residual top-module slices.
- Keep locked authority artifacts unchanged unless a human approves a change request.
- Rerun rtl_todo_plan audit, compile, lint, sim, and coverage evidence until required TODOs pass.
