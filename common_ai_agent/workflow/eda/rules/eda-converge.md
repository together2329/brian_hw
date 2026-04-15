# EDA Converge Loop — Customization Guide

## Overview

The converge loop is configured entirely through `converge.yaml` in this directory.
You can customize stages, criteria, classifiers, and feedback routing without
touching any Python code.

## Quick Customization

### Adding a New Stage

Add to the `stages:` list in `converge.yaml`:

```yaml
  - id: coverage
    workspace: tb-gen
    agent: execute
    prompt: |
      Run coverage analysis on {module}.
      RTL: {rtl_path}
      TB: {tb_path}
      Report: line, toggle, FSM, branch coverage.
    depends_on:
      - sim
```

### Changing Convergence Criteria

Edit the `criteria:` section:

```yaml
criteria:
  hard_stop:
    - metric: lint.errors
      operator: "=="
      value: 0
    - metric: sim.fail
      operator: "=="
      value: 0
    - metric: coverage_pct     # new criterion
      operator: ">="
      value: 90.0
  score_threshold: 15.0        # raise target
  max_total_iterations: 20     # allow more retries
```

### Adding a New Classifier

Add to the `classifiers:` list:

```yaml
  - id: reset_bug
    patterns:
      - "reset not working"
      - "x-prop after reset"
      - "initial values wrong"
    label: reset_bug
```

Then add a corresponding feedback graph edge:

```yaml
  - trigger:
      stage: sim
      classifier: reset_bug
    fix:
      workspace: rtl-gen
      prompt: |
        [RESET BUG FIX] Reset logic issue detected:
        {sim_result}
        Fix reset logic in {rtl_path}. Check async/sync reset, initial values.
      retry_from: lint
      max_retries: 3
```

### Adjusting Score Weights

Edit `score_function.weights`:

```yaml
score_function:
  weights:
    lint.errors: -15.0         # increase penalty
    lint.warnings: -5.0
    sim.pass_ratio: 10.0
    sim.has_failures: -20.0
    coverage_pct: 5.0          # new weight
```

### Adding Synthesis Stage (Phase 2)

Append to stages:

```yaml
  - id: synth
    workspace: synth
    agent: execute
    prompt: |
      Synthesize {module}. RTL: {rtl_path}
      Generate QoR report: WNS, TNS, area, power.
    depends_on:
      - sim

  - id: sta
    workspace: sta
    agent: execute
    prompt: |
      Run STA on {module}. Check setup/hold violations.
      Report WNS, TNS.
    depends_on:
      - synth
```

Add criteria:
```yaml
    - metric: synth.wns
      operator: ">="
      value: 0
```

Add parser:
```yaml
  synth:
    type: regex_groups
    fields:
      wns:
        regex: "(?i)wns[:\\s]+(-?\\d+\\.?\\d*)"
        cast: "float"
      tns:
        regex: "(?i)tns[:\\s]+(-?\\d+\\.?\\d*)"
        cast: "float"
      area:
        regex: "(?i)area[:\\s]+(\\d+)"
        cast: "int"
```

## Template Variables

Available in prompt templates:

| Variable | Source | Example |
|----------|--------|---------|
| `{module}` | Always set | `counter` |
| `{mas_path}` | From spec stage `produces` | `counter/mas/counter_mas.md` |
| `{rtl_path}` | From rtl stage `produces` | `counter/rtl/counter.sv` |
| `{tb_path}` | From tb stage `produces` | `counter/tb/tb_counter.sv` |
| `{lint_context}` | From previous lint output | Previous error messages |
| `{lint_result}` | From feedback graph trigger | Raw lint output |
| `{sim_result}` | From feedback graph trigger | Raw sim output |

## File Structure

```
workflow/eda/
├── workspace.json          # Workspace config (name, skills, env)
├── converge.yaml           # THE loop configuration (edit this!)
├── system_prompt.md        # Agent rules for converge mode
├── rules/
│   └── eda-converge.md     # This documentation
├── scripts/
│   ├── check_lint_pass.sh  # Lint pass validator
│   └── check_sim_pass.sh   # Sim pass validator
└── todo_templates/
    └── eda-full-loop.json  # Full loop todo template
```
