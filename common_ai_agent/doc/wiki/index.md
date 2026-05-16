# common_ai_agent Wiki

This wiki is the cross-linked operating map for common_ai_agent. It is optimized
for long-context LLMs and agent handoffs: read the linked pages in order, then
follow the source docs for implementation detail.

## LLM Reading Order

1. [[common-ai-agent-map]] — mental model and source-of-truth hierarchy.
2. [[workflow-ownership-and-boundaries]] — who owns each artifact and what must not be edited directly.
3. [[ssot-qa-workbench]] — SSOT authoring UX: import, interview, requirement progress, and To SSOT.
4. [[full-flow-pipeline]] — SSOT to signoff stage order and commands.
5. [[rtl-gen-ssot-contract]] — why rtl-gen must follow SSOT exactly before downstream stages run.
6. [[workflow-feedback-and-scheduling]] — worker-aware serial/DAG scheduling and workflow repair feedback.
7. [[orchestrator-worker-handoff]] — orchestrator agent, live worker dispatch, JSON handoff fallback, and `/take` semantics. Spec-vs-shipped gaps tracked in [[orchestrator-worker-handoff-review]]. Concrete shipped realization: [[parallel-todo-sub-agent-workers]] — `parallel_todo_dispatch` fans a TODO batch out to N clean sub-agent workers (auto-picks from claude-cli / cursor-cli / gpt-5.3-codex / glm / deepseek / kimi by available credentials + cheapest cost).
8. [[rtl-version-run-history]] — SSOT/RTL/TB artifact version anchors for workflow evidence.
9. [[golden-todo-evidence]] — TodoTracker, evidence approval, and human review states.
10. [[provider-and-llm-call-accounting]] — provider normalization and how to count one LLM call.
11. [[human-review-and-escalation]] — when to stop automation and ask for product/spec authority.
12. [[deterministic-emit-stages]] — why fl-model-gen and cl-model-gen run without an LLM, and what contract that places on the upstream SSOT.
13. [[karpathy-llm-wiki-pattern]] — reference page for Andrej Karpathy's LLM Wiki concept (3-layer markdown + index + log + schema; no RAG, no vector DB) and how `doc/wiki/` already aligns to it.
14. [[wiki-curation-policy]] — what to capture, when to capture it, and what to deliberately leave out of the wiki. Lives next to the code so the policy evolves with usage.

## UI

- [[atlas-pipeline-screen]] — `◫ Pipeline` top-level screen: click-to-run stage dispatcher, per-stage scoresheet, owner-aware blame routing.
- [[atlas-pipeline-db-state]] — how `/api/pipeline/state` derives state (DB-first, FS-fallback for hand-placed evidence) and the migration plan for moving KPI dots fully into the DB.
- [[ui-design-references]] — external UI checkouts under `external_refs/` (currently `nexu-io/open-design`) and which patterns inform ATLAS.

## Reference Runs (working examples on real IPs)

Reloadable snapshots live in [`ref_ip_flow/`](../../ref_ip_flow/README.md)
— each run is portable (IP artifacts + ATLAS sessions + seeds) so it can
be loaded on a different machine and inspected without recreating the DB.

- [[arm-m0-min-pipeline-run]] — minimal ARMv6-M Thumb CPU, full ssot→lint pipeline with green compile/lint/sim/coverage; first CPU-class run on the new DB operating mode (2026-05-15).
- [[gpio-serial-pipeline-run]] — `simple_gpio_lite` serial smoke run; RTL clean, tb-gen blocks on prose-only FunctionalModel `ssot_question` gaps, and ssot-gen now catches the same missing machine-rule transactions before downstream token spend (2026-05-16).
- [[gpio-orchestrator-multiworker-run]] — `gpio_orch_scratch` Atlas orchestrator plus author/verify worker run; tracks current RTL gate/tool-evidence bugs and UI run-status gaps (2026-05-16).

## Hard Rules

- Use the common engine and workflow commands for IP generation and repair.
- Do not manually patch generated IP artifacts to make a test pass.
- Do not change SSOT, FunctionalModel, CycleModel, coverage goals, timing targets, waivers, or interface contracts to hide downstream failures.
- RTL-gen must implement the current SSOT contract; existing RTL is evidence, not authority.
- Sim evidence must name SSOT/RTL/TB versions; lint/syn/sta/pnr evidence must name the RTL version it ran against.
- If evidence fails, classify the owner first, then route the fix to the owner workflow.
- In worker mode, the orchestrator dispatches owner feedback to live workflow workers; outside worker mode it persists handoff JSON for `/take`.
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
