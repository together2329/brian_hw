# common_ai_agent Map

## Purpose

common_ai_agent turns an IP idea into traceable implementation and verification
evidence. The system is not a free-form coding assistant; it is a workflow
factory controlled by SSOT, TodoTracker, validators, and human review.

## Mental Model

```text
SSOT = contract
Workflow = factory line
LLM = worker
TodoTracker = work state machine
Validator/Audit = judge
Human review = product/spec authority
```

## Authority Stack

1. User-approved requirement and review decisions.
2. SSOT YAML and locked source-of-truth sections.
3. FunctionalModel and CycleModel generated from approved SSOT.
4. Stage ledgers and evidence artifacts.
5. LLM-authored downstream files.
6. Chat prose and model reasoning.

If lower authority conflicts with higher authority, fix or escalate the lower
authority. Do not silently rewrite higher authority to make downstream evidence pass.

## Main Pages

- [[workflow-ownership-and-boundaries]] defines edit ownership.
- [[full-flow-pipeline]] defines stage order.
- [[golden-todo-evidence]] defines approval and todo states.
- [[provider-and-llm-call-accounting]] defines model/provider normalization.
- [[human-review-and-escalation]] defines human gates.

## Canonical Source Docs

- [doc/ai_driven_ip_development_guide.md](../ai_driven_ip_development_guide.md)
- [workflow/COMMON_ENGINE_FLOW.md](../../workflow/COMMON_ENGINE_FLOW.md)
- [doc/golden_todo_evidence_flow.md](../golden_todo_evidence_flow.md)

## Stop Condition

An IP is complete only when the cross-stage ledger has approved evidence for
required stages and the human review queue is empty or explicitly accepted.
