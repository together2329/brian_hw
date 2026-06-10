---
name: coverage-workflow
description: Work with the coverage workflow for SSOT functional coverage summaries, coverage limitations, and coverage evidence. Use for coverage, ssot-coverage, coverage.json, or coverage gap closure tasks.
---

# Atlas Coverage Workflow

`coverage` owns SSOT coverage approval. In the common-engine path, coverage is based on scoreboard rows and SSOT coverage goals, not just raw Verilator line/toggle data.

## Runtime Workspace

- Workspace: `workflow/coverage/workspace.json`
- Command: `workflow/coverage/commands/ssot-coverage.json`
- Scripts: `workflow/coverage/scripts/*`

Common-engine stage:

```text
coverage -> WorkflowStageEngine.run_stage("coverage", ip)
```

Evidence:

- `cov/coverage_functional.json`
- `cov/coverage.json`
- `cov/coverage_ssot.json`
- `sim/coverage_report.md`
- `logs/stage_engine/coverage.json`

## Cursor Use

```bash
python3 .cursor/skills/rtl-to-signoff/scripts/rtl_to_signoff.py <ip> --profile dv --execute --from-stage coverage --until coverage
```

Do not lower coverage goals to pass. Add stimulus, repair scoreboard evidence, or record explicit limitations/human review.
