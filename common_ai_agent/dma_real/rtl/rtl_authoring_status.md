# RTL Authoring Status: dma_real

## Status

- Top: dma_real_top
- Packets: 25
- LLM-actionable tasks: 73
- Human-locked tasks: 0
- Tool-evidence tasks: 4
- Deferred human QA allowed: True
- PASS allowed: False
- Target scale locked: False
- Pending connection-contract suggestions: 0
- Recommended packet batch limit: 4

## Next LLM Packets

- module__dma_real_engine: rtl/authoring_packets/module__dma_real_engine.json (llm_open=1, human_locked=0)
- module__dma_real_apb_cfg__registers_02: rtl/authoring_packets/module__dma_real_apb_cfg__registers_02.json (llm_open=16, human_locked=0)
- module__dma_real_apb_cfg__registers_01: rtl/authoring_packets/module__dma_real_apb_cfg__registers_01.json (llm_open=14, human_locked=0)
- module__dma_real_apb_cfg__function_model: rtl/authoring_packets/module__dma_real_apb_cfg__function_model.json (llm_open=7, human_locked=0)
- module__dma_real_apb_cfg__registers_03: rtl/authoring_packets/module__dma_real_apb_cfg__registers_03.json (llm_open=5, human_locked=0)
- module__dma_real_apb_cfg__workflow_todo: rtl/authoring_packets/module__dma_real_apb_cfg__workflow_todo.json (llm_open=1, human_locked=0)
- module__dma_real_arbiter: rtl/authoring_packets/module__dma_real_arbiter.json (llm_open=7, human_locked=0)
- module__dma_real_channel__dataflow: rtl/authoring_packets/module__dma_real_channel__dataflow.json (llm_open=2, human_locked=0)

## Tool Evidence Queue

- rtl_gate_tool_evidence: tool_evidence=4, next_tool=ssot-rtl, json=rtl/authoring_packets/rtl_gate_tool_evidence.json

## Rules

- Use rtl_todo_plan.json as the complete ledger and rtl_authoring_plan.json as the LLM work queue.
- Process one authoring packet at a time: module packets first, then unowned tasks if any, then rtl_gate_evidence_closure; leave rtl_gate_tool_evidence to tools and rtl_gate_contract_blocked/rtl_gate_human_closure to human-locked authority gaps.
- Generate real RTL; do not instantiate a fixed IP template or copy boilerplate as the implementation.
- Do not close static RTL evidence with comments: derive_rtl_todos.py strips comments before matching, so evidence_terms must be preserved in live lint-clean RTL identifiers/logic.
- Do not close static RTL evidence with evidence-only alias wires or marker-only helper wires; the matched identifiers must participate in real RTL behavior.
- If reference_profile is present, use it only to understand implementation scale and decomposition gaps; never copy or clone reference RTL.
- After the top RTL exists, prioritize missing manifest child RTL packets before residual top-module slices.
- Keep locked authority artifacts unchanged unless a human approves a change request.
- Rerun rtl_todo_plan audit, compile, lint, sim, and coverage evidence until required TODOs pass.
