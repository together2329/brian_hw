# EDA Converge Loop Rules

You are running in the EDA converge loop workspace. This workspace manages
a self-converging spec→rtl→lint→tb→sim pipeline.

## Converge Loop Behavior

1. **Loop is driven by converge.yaml** — all stages, criteria, classifiers are configured there
2. **Each stage runs as a sub-agent** with workspace-specific prompts
3. **Sub-agents MUST output METRICS lines** — e.g., `METRICS: lint.errors=0, lint.warnings=5`
4. **Output is parsed and scored** using METRICS lines (primary) and fallback regex patterns
5. **Failures are classified** and routed to fix steps via the feedback graph
6. **Loop continues** until convergence criteria are met or max iterations reached

## METRICS Output Format

Every stage sub-agent MUST output a summary line before completing:
```
METRICS: <stage>.<field>=<value>, <stage>.<field>=<value>
```

Examples:
- Spec: `METRICS: spec.complete=1, spec.sections=9`
- RTL: `METRICS: rtl.complete=1, rtl.files=3, rtl.compile_errors=0`
- Lint: `METRICS: lint.errors=0, lint.warnings=0`
- TB: `METRICS: tb.complete=1, tb.tests=12, tb.compile_errors=0`
- Sim: `METRICS: sim.pass=12, sim.fail=0, sim.total=12`

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
| `{module}/list/` | rtl/tb stage | File lists (.f files) |
| `{module}/tb/` | tb stage | Testbench code |
| `{module}/sim/` | sim stage | Simulation results |
| `{module}/lint/` | lint stage | Lint reports |

## Quality Gates

- **Lint gate**: TB generation cannot start until lint shows 0 errors
- **Sim gate**: Convergence requires 0 sim failures
- **Score gate**: Target score is 10.0 (configurable in converge.yaml)

## Score Computation

```
score = -10 * lint_errors
        - 5 * lint_warnings
        - 15 * rtl_compile_errors
        - 10 * tb_compile_errors
        + 10 * (sim_pass / sim_total)   [sim.pass_ratio]
        - 20 * (if sim has failures)
        - 5 * sim_fail_count
        + 2 * sim_pass_count
```

## Convergence Criteria

Hard stop (ALL must be met):
- `lint.errors == 0`
- `sim.fail == 0`

Soft targets:
- Score >= 10.0
- No improvement for 5 iterations → stalled

## Fallback Metric Extraction

If a sub-agent does not output a METRICS: line, the engine falls back to:
- **Lint stage**: Count `%Error` and `%Warning` patterns from verilator output
- **Sim stage**: Count `[PASS]` and `[FAIL]` patterns from simulation output
- **RTL/TB stage**: Count `error:` patterns from iverilog output
