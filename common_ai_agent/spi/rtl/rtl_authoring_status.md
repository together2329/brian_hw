# RTL Authoring Status: spi

## Status

- Top: spi
- Packets: 20
- LLM-actionable tasks: 242
- Human-locked tasks: 3
- Tool-evidence tasks: 7
- Deferred human QA allowed: True
- PASS allowed: False
- Target scale locked: True
- Pending connection-contract suggestions: 0
- Recommended packet batch limit: 4

## Next LLM Packets

- module__spi_regs__registers: rtl/authoring_packets/module__spi_regs__registers.json (llm_open=37, human_locked=0)
- module__spi_regs__io_list: rtl/authoring_packets/module__spi_regs__io_list.json (llm_open=16, human_locked=0)
- module__spi_regs__interrupts: rtl/authoring_packets/module__spi_regs__interrupts.json (llm_open=8, human_locked=0)
- module__spi_regs__error_handling: rtl/authoring_packets/module__spi_regs__error_handling.json (llm_open=2, human_locked=0)
- module__spi_regs__equivalence: rtl/authoring_packets/module__spi_regs__equivalence.json (llm_open=1, human_locked=0)
- module__spi_regs__workflow_todo: rtl/authoring_packets/module__spi_regs__workflow_todo.json (llm_open=1, human_locked=0)
- module__spi_fifo: rtl/authoring_packets/module__spi_fifo.json (llm_open=9, human_locked=0)
- module__spi_clkgen: rtl/authoring_packets/module__spi_clkgen.json (llm_open=21, human_locked=0)

## Tool Evidence Queue

- rtl_gate_tool_evidence: tool_evidence=7, next_tool=ssot-rtl, json=rtl/authoring_packets/rtl_gate_tool_evidence.json

## Human-Locked Queue

- rtl_gate_human_closure: human_locked=3, json=rtl/authoring_packets/rtl_gate_human_closure.json

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
