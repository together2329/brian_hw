# coverage / rules

Coverage closure policies enforced by `workflow/coverage/scripts/ssot_coverage_summary.py`.

## Default policy (applied when SSOT has no `quality_gates.coverage_threshold`)

| Metric | Floor | Source channel |
|---|---|---|
| Line coverage | 90% | instrumented (`coverage.dat`) |
| Branch coverage | 80% | instrumented |
| Toggle coverage | 70% | VCD post-process |
| Functional bin hit ratio | 95% | SSOT `cov/fcov_plan.json` planned vs hit |

Any unmet metric blocks signoff. The check is run by
`workflow/coverage/scripts/coverage_gaps.sh` and surfaced through
`ssot_coverage_summary.py`'s `passed=` field.

## SSOT override

An IP may raise (or, with documented reason, lower) any threshold via
`<ip>/yaml/<ip>.ssot.yaml`:

```yaml
quality_gates:
  coverage_threshold:
    line: 95
    branch: 90
    toggle: 80
    functional_bins: 98
    waiver_required: ["unreachable_dead_code"]
```

The summary script reads SSOT first, then falls back to the floors above.

## Why this directory exists

Earlier versions left `rules/` empty and let `coverage_iter.json` describe
floors inline in its `detail` text. That made the contract invisible to
non-coverage workflows (lint, sim, sta) that needed to know which metrics
gate the pipeline. Centralising the floors here keeps the policy
greppable and version-controlled.
