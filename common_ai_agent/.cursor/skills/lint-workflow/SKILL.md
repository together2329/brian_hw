---
name: lint-workflow
description: Work with the lint workflow for DUT-only lint reports, lint todo plans, Verilator/pyslang diagnostics, and lint repair. Use for lint, lint-ip, dut_lint.json, or lint clean gates.
---

# Atlas Lint Workflow

`lint` owns DUT-only lint evidence. The common-engine lint stage uses `workflow/lint/scripts/dut_lint_report.py`.

## Runtime Workspace

- Workspace: `workflow/lint/workspace.json`
- Command: `workflow/lint/commands/lint-ip.json`
- Scripts: `workflow/lint/scripts/*`

Common-engine stage:

```text
lint -> WorkflowStageEngine.run_stage("lint", ip)
```

Evidence:

- `lint/dut_lint.json`
- `lint/dut_lint.log`
- `lint/lint_todo_plan.json`
- `logs/stage_engine/lint.json`

## Cursor Use

```bash
python3 .cursor/skills/rtl-to-signoff/scripts/rtl_to_signoff.py <ip> --profile dv --execute --from-stage lint --until lint
```

Do not waive warnings casually. Generated RTL should root-cause lint warnings unless a higher-level SSOT/human waiver exists.
