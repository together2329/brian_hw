# RTL Authoring Status: pl330realverify

## Status

- Top: pl330realverify
- Packets: 31
- LLM-actionable tasks: 75
- Human-locked tasks: 2
- Tool-evidence tasks: 4
- Deferred human QA allowed: True
- PASS allowed: False
- Target scale locked: True
- Pending connection-contract suggestions: 0
- Recommended packet batch limit: 4

## Next LLM Packets

- module__pl330realverify_axi_rd_pl330realverify_axi_wr: rtl/authoring_packets/module__pl330realverify_axi_rd_pl330realverify_axi_wr.json (llm_open=1, human_locked=0)
- module__pl330realverify_datapath_pl330realverify_event_irq: rtl/authoring_packets/module__pl330realverify_datapath_pl330realverify_event_irq.json (llm_open=1, human_locked=0)
- module__pl330realverify_regs__interrupts: rtl/authoring_packets/module__pl330realverify_regs__interrupts.json (llm_open=7, human_locked=0)
- module__pl330realverify_regs__function_model: rtl/authoring_packets/module__pl330realverify_regs__function_model.json (llm_open=5, human_locked=0)
- module__pl330realverify_regs__registers: rtl/authoring_packets/module__pl330realverify_regs__registers.json (llm_open=5, human_locked=0)
- module__pl330realverify_channel_fsm__function_model: rtl/authoring_packets/module__pl330realverify_channel_fsm__function_model.json (llm_open=20, human_locked=0)
- module__pl330realverify_channel_fsm__fsm: rtl/authoring_packets/module__pl330realverify_channel_fsm__fsm.json (llm_open=17, human_locked=0)
- module__pl330realverify_channel_fsm__cycle_model: rtl/authoring_packets/module__pl330realverify_channel_fsm__cycle_model.json (llm_open=4, human_locked=0)

## Tool Evidence Queue

- rtl_gate_tool_evidence: tool_evidence=4, next_tool=audit-rtl, json=rtl/authoring_packets/rtl_gate_tool_evidence.json

## Human-Locked Queue

- rtl_gate_human_closure: human_locked=2, json=rtl/authoring_packets/rtl_gate_human_closure.json

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
