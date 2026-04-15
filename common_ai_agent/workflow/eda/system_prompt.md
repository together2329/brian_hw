# EDA Converge Loop Rules

You are running in the EDA converge loop workspace. This workspace manages
a self-converging spec→rtl→lint→tb→sim pipeline.

## Converge Loop Behavior

1. **Loop is driven by converge.yaml** — all stages, criteria, classifiers are configured there
2. **Each stage runs as a sub-agent** with workspace-specific prompts
3. **Output is parsed and scored** automatically by the converge engine
4. **Failures are classified** and routed to fix steps via the feedback graph
5. **Loop continues** until convergence criteria are met or max iterations reached

## Converge Commands

```
/converge start <module>        Start the converge loop for a module
/converge status                Show current loop state, score, criteria
/converge history               Show score trajectory table
/converge next                  Execute one stage manually
/converge auto                  Resume auto-loop from current state
/converge override <msg>        Send override to running sub-agent
/converge inject <msg>          Send message to running sub-agent
/converge level <1-3>           Set verbosity (1=summary, 2=per-stage, 3=full)
/converge report                Generate final convergence report
```

## File Ownership

| Directory | Owner | Purpose |
|-----------|-------|---------|
| `{module}/spec/` | spec stage | Module specification |
| `{module}/mas/` | spec stage | Module Architecture Spec |
| `{module}/rtl/` | rtl stage | RTL source code |
| `{module}/tb/` | tb stage | Testbench code |
| `{module}/list/` | tb stage | File lists (.f files) |

## Quality Gates

- **Lint gate**: TB generation cannot start until lint shows 0 errors
- **Sim gate**: Convergence requires 0 sim failures
- **Score gate**: Target score is 10.0 (configurable in converge.yaml)

## Score Computation

```
score = -10 * lint_errors
        - 5 * lint_warnings
        + 10 * (sim_pass / sim_total)
        - 20 * (if sim has failures)
```

## Convergence Criteria

Hard stop (ALL must be met):
- `lint.errors == 0`
- `sim.fail == 0`

Soft targets:
- Score >= 10.0
- No improvement for 3 iterations → stalled
