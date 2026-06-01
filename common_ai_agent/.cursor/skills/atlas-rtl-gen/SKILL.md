---
name: atlas-rtl-gen
description: Work with rtl-gen for SSOT-derived RTL implementation, dynamic RTL todo ledgers, compile/lint gates, and RTL repair. Use for rtl-gen, ssot-rtl, RTL blockers, or rtl_todo_plan tasks.
---

# Atlas RTL Gen

`rtl-gen` owns RTL source, filelists, RTL todo ledgers, compile evidence, and DUT lint evidence produced by `/ssot-rtl`.

## Runtime Workspace

- Workspace: `workflow/rtl-gen/workspace.json`
- Command: `workflow/rtl-gen/commands/ssot-rtl.json`
- Scripts: `workflow/rtl-gen/scripts/*`
- Forced runtime skill: `skills/verilog-expert/SKILL.md`

Common-engine stage:

```text
ssot-rtl -> WorkflowStageEngine.run_stage("ssot-rtl", ip)
```

Evidence:

- `rtl/rtl_todo_plan.json`
- `rtl/rtl_todo_tracker.json`
- `rtl/rtl_compile.json`
- `lint/dut_lint.json`
- `logs/stage_engine/ssot-rtl.json`
- `rtl/rtl_blocked.json` for human/SSOT blockers

## Cursor Use

```bash
python3 .cursor/skills/rtl-to-signoff/scripts/rtl_to_signoff.py <ip> --profile dv --execute --from-stage ssot-rtl --until ssot-rtl
```

If blocked, route to `ssot-gen` or human review. Do not patch SSOT, coverage goals, or generated evidence to force RTL PASS.
