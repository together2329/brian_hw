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
