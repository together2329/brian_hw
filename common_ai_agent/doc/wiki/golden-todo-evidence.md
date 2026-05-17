# Golden Todo Evidence

## Principle

The todo list is not a prompt checklist. It is a contract between SSOT,
generated artifacts, and evidence.

```text
LLM says done        -> completed / approval_requested
validator proves it  -> approved
validator disproves  -> rejected
human must decide    -> human_review_needed
missing input        -> blocked
```

## Required Todo Fields

- `id`
- `content`
- `detail`
- `criteria`
- `source_refs`
- `owner_workflow`
- `owner_file` or `owner_module` when applicable
- `approval_policy`
- `required_evidence`
- `fallback_if_no_evidence`
- `todo_completion`

## Approval Policy

Default policy is `evidence_required`.

Use `human_review_required` for product/spec decisions, waivers, architecture
tradeoffs, security/safety policy, unreachable coverage, and any proposal to
change locked authority.

For requirement approval, `human_review_required` must resolve to an approved
artifact plus manifest, not just prose:

- `<ip>/req/*.md`
- `<ip>/req/approval_manifest.json`
- matching source/target SHA256 values
- resolved review decision when a review queue item exists

Use `llm_reason_allowed` only for low-risk docs, comments, explanation, or
non-behavioral cleanup.

## Evidence Examples

- `rtl_compile.json` passes.
- `dut_lint.json` has zero unwaived errors/warnings.
- `scoreboard_events.jsonl` covers every required equivalence goal.
- `coverage.json` meets function and cycle targets.
- `sim/fl_rtl_compare.json` has no unresolved mismatch.

## Related

- [[workflow-ownership-and-boundaries]]
- [[full-flow-pipeline]]
- [doc/golden_todo_evidence_flow.md](../golden_todo_evidence_flow.md)
