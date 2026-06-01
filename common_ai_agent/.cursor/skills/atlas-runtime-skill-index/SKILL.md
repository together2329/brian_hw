---
name: atlas-runtime-skill-index
description: Locate and reuse common_ai_agent runtime skills. Use when the user mentions Verilog expertise, testbench expertise, external RTL DB reuse, spec building, or existing in-app agent skills.
---

# Atlas Runtime Skill Index

Cursor project skills are wrappers. The runtime agent already has domain skills under `skills/`; read those files directly when the task needs that expertise.

## Existing Runtime Skills

- `skills/verilog-expert/SKILL.md`
- `skills/testbench-expert/SKILL.md`
- `skills/spec-builder/SKILL.md`
- `skills/external-db/SKILL.md`
- `skills/git/SKILL.md`
- `skills/large-file-analyst/SKILL.md`
- `skills/code-analysis-expert/SKILL.md`
- `skills/pcie-expert/SKILL.md`
- `skills/nvme-expert/SKILL.md`
- `skills/ucie-expert/SKILL.md`

Do not duplicate these into Cursor unless a task needs a Cursor-specific wrapper. Prefer reading the runtime skill and following it.
