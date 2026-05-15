# common_ai_agent Wiki

This wiki is the cross-linked operating map for common_ai_agent. It is optimized
for long-context LLMs and agent handoffs: read the linked pages in order, then
follow the source docs for implementation detail.

## LLM Reading Order

1. [[common-ai-agent-map]] — mental model and source-of-truth hierarchy.
2. [[workflow-ownership-and-boundaries]] — who owns each artifact and what must not be edited directly.
3. [[full-flow-pipeline]] — SSOT to signoff stage order and commands.
4. [[rtl-gen-ssot-contract]] — why rtl-gen must follow SSOT exactly before downstream stages run.
5. [[workflow-feedback-and-scheduling]] — worker-aware serial/DAG scheduling and workflow repair feedback.
6. [[rtl-version-run-history]] — SSOT/RTL/TB artifact version anchors for workflow evidence.
7. [[golden-todo-evidence]] — TodoTracker, evidence approval, and human review states.
8. [[provider-and-llm-call-accounting]] — provider normalization and how to count one LLM call.
9. [[human-review-and-escalation]] — when to stop automation and ask for product/spec authority.

## Hard Rules

- Use the common engine and workflow commands for IP generation and repair.
- Do not manually patch generated IP artifacts to make a test pass.
- Do not change SSOT, FunctionalModel, CycleModel, coverage goals, timing targets, waivers, or interface contracts to hide downstream failures.
- RTL-gen must implement the current SSOT contract; existing RTL is evidence, not authority.
- Sim evidence must name SSOT/RTL/TB versions; lint/syn/sta/pnr evidence must name the RTL version it ran against.
- If evidence fails, classify the owner first, then route the fix to the owner workflow.
- Approval comes from deterministic evidence or human authority, not from LLM prose.

## Source Docs

- [AI-Driven IP Development Guide](../ai_driven_ip_development_guide.md)
- [Golden Todo Evidence Flow](../golden_todo_evidence_flow.md)
- [Common Engine IP Flow](../../workflow/COMMON_ENGINE_FLOW.md)
- [Workflow Long-Term Improvements](../workflow_long_term_improvements.md)
- [RTL Gen Flow](../../workflow/rtl-gen/RTL_GEN_FLOW.md)

## Maintenance

- Add a wiki page when a concept is reused across multiple docs or workflows.
- Keep wiki pages short and cross-linked.
- Put implementation details in source docs and scripts; put navigation and authority rules here.
- When a workflow rule changes, update the source doc first, then update the wiki link map.
