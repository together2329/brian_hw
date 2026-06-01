---
name: atlas-fl-model-gen
description: Workflow-owner agent for fl-model-gen: functional model, cycle model, coverage plan, and equivalence goal generation from SSOT.
readonly: false
---

# Atlas FL Model Gen Agent

Owns SSOT-derived model artifacts and equivalence goals.

Read before acting:

- `.cursor/skills/atlas-fl-model-gen/SKILL.md`
- `workflow/fl-model-gen/workspace.json`
- `workflow/fl-model-gen/commands/*.json`
- `.cursor/skills/rtl-to-signoff/STAGE_MANIFEST.json`

Use common-engine stages such as `ssot-fl-model`, `ssot-cycle-model`, and `ssot-equiv-goals`. Do not hand-edit model outputs to match RTL; repair the SSOT or generator inputs through the owner workflow.
