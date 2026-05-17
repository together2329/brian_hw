# Human Review And Escalation

## Human Review Is Not Failure

Use `human_review_needed` when the system lacks authority to decide product or
spec truth. Do not hide these items inside ordinary rejected todo rows.

## Human-Owned Decisions

- Requirement intent and acceptance criteria.
- Undefined behavior and protocol policy.
- Interface contract changes.
- Coverage goal changes or waivers.
- Target frequency, area, power, and PDK assumptions.
- Security or safety tradeoffs.
- Any change to SSOT, FL, CL, coverage goals, or constraints made to resolve a downstream mismatch.

## Requirement Approval Contract

Requirement signoff is stronger than "a markdown file exists". A final audit
must require all of the following before `req_ok=true`:

- approved requirement markdown under `<ip>/req/`
- `<ip>/req/approval_manifest.json`
- non-empty `approved_by` and `approved_at_utc`
- manifest `target_sha256` matching the approved requirement markdown
- manifest `source_sha256` matching the reviewed packet under `<ip>/doc/`
- if a review decision pins `evidence.approval_target`, promotion must reject
  mismatched `path` or `sha256` before writing `<ip>/req/`
- if a review decision pins `evidence.machine_evidence_snapshot`, promotion
  must reject mismatched machine-evidence hashes before writing `<ip>/req/`
- any `<ip>/review/decision_needed_req_requirement_approval.json` item is
  `resolved`
- promotion removes review-only pending-status text from the approved
  requirement body while preserving source traceability through the manifest

This prevents pass-for-pass behavior where an agent writes a long `req/*.md`
file and treats it as human approval. The approved requirement artifact must be
traceable to the reviewed packet and to a human approver.

## UI Visibility

Human review items must be visible from the Pipeline control plane, not only
from filesystem inspection. `/api/pipeline/state` should expose compact
`orchestrator.decision_items[]` entries with the review record path and, when
available, `evidence.human_facing_request`.

The Pipeline review chip should open the human-facing request in Workspace
preview. The record JSON remains the machine-readable source, but the user
should see the short approval/reject page first.

## Escalation Format

Use explicit owner routing:

```text
[ESCALATE: ssot-gen] yaml_path=<path> reason=<concrete> required_change=<concrete>
[ESCALATE: tool-fix] tool=<script_path> pattern=<observed false pos/neg> example=<minimal repro>
[ESCALATE: human] decision=<one-line> options=[a, b, c] recommended=<a|b|c> reason=<why>
```

## Repair Loop Rule

If FL expected and RTL actual disagree:

1. Keep SSOT/FL/CL locked.
2. Classify owner using sim-debug evidence.
3. Repair RTL or TB only when that owner is proven.
4. If the expected behavior itself is disputed, escalate to human review.

## Related

- [[workflow-ownership-and-boundaries]]
- [[golden-todo-evidence]]
- [[full-flow-pipeline]]
