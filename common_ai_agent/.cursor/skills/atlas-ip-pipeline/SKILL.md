---
name: atlas-ip-pipeline
description: Run or reason about the ATLAS SSOT-to-signoff IP pipeline. Use for workflow, RTL generation, TB, sim, coverage, lint, syn, sta, pnr, or signoff tasks.
---

# Atlas IP Pipeline

## Read First

- `workflow/COMMON_ENGINE_FLOW.md`
- `doc/wiki/common-ai-agent-map.md`
- `doc/wiki/workflow-ownership-and-boundaries.md`
- `doc/wiki/full-flow-pipeline.md`
- `doc/wiki/run-mode-and-provenance-policy.md`

For the full script index, read `WORKFLOW_INDEX.md` in this skill directory.

## Stage Order

```text
req -> ssot-gen -> fl-model-gen -> rtl-gen -> tb-gen -> sim -> coverage -> lint -> syn -> sta -> pnr -> sta-post
```

The SSOT is the contract. Do not change requirements, coverage goals, timing targets, or SSOT semantics to match broken downstream artifacts.

## Execution Rule

Use the existing workflow scripts and slash-command contracts. Do not duplicate validators in Cursor skills or hooks.

When a stage fails:

1. Read logs and structured evidence.
2. Classify the owner workflow.
3. Repair through the owner.
4. Rerun the validator.
5. Report fresh evidence and remaining blockers.
