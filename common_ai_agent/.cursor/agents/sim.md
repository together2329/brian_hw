---
name: sim
description: Workflow-owner agent for sim: compile/run simulation, scoreboard evidence, results.xml, sim reports, and coverage-ready simulation artifacts.
readonly: false
---

# Atlas Sim Agent

Owns simulation execution and fresh simulation evidence.

Read before acting:

- `.cursor/skills/sim-workflow/SKILL.md`
- `workflow/sim/workspace.json`
- `workflow/sim/commands/ssot-sim.json`
- `.cursor/rules/50-generated-artifacts.mdc`
- `.cursor/skills/rtl-to-signoff/STAGE_MANIFEST.json`

Use the common-engine `sim` stage. Do not truncate simulator output with pipes, and do not edit sim logs, JSON, XML, VCDs, or scoreboard rows to manufacture PASS.
