---
name: atlas-tb-gen
description: Work with tb-gen for SSOT-derived cocotb/pyuvm testbench generation, scoreboards, TB manifests, and TB repair. Use for tb-gen, ssot-tb-cocotb, scoreboard, or testbench generation tasks.
---

# Atlas TB Gen

`tb-gen` owns SSOT-derived testbench artifacts, cocotb/pyuvm structure, goal-driven scoreboards, and TB todo ledgers.

## Runtime Workspace

- Workspace: `workflow/tb-gen/workspace.json`
- Command: `workflow/tb-gen/commands/ssot-tb-cocotb.json`
- Scripts: `workflow/tb-gen/scripts/*`
- Runtime skills: `verilog-expert`, `testbench-expert` when needed

Common-engine stage:

```text
ssot-tb-cocotb -> WorkflowStageEngine.run_stage("ssot-tb-cocotb", ip)
```

Evidence:

- `tb/cocotb/tb_manifest.json`
- `tb/cocotb/tb_generation.json`
- `tb/tb_todo_plan.json`
- `logs/stage_engine/ssot-tb-cocotb.json`
- `tb/cocotb/tb_blocked.json` for human/SSOT blockers

## Cursor Use

```bash
python3 .cursor/skills/rtl-to-signoff/scripts/rtl_to_signoff.py <ip> --profile dv --execute --from-stage ssot-tb-cocotb --until ssot-tb-cocotb
```

TB must compare RTL observations against FunctionalModel/equivalence goals. Do not use fixed-IP templates or mock pass rows.
