---
name: fl-model-gen
description: Work with fl-model-gen for SSOT-derived functional models, cycle models, functional coverage plans, and equivalence goals. Use for fl-model-gen, cl-model, ssot-fl-model, ssot-cycle-model, or ssot-equiv-goals tasks.
---

# Atlas FL Model Gen

`fl-model-gen` owns deterministic model and equivalence artifacts derived from SSOT.

## Runtime Workspace

- Workspace: `workflow/fl-model-gen/workspace.json`
- Commands: `workflow/fl-model-gen/commands/*.json`
- Scripts: `workflow/fl-model-gen/scripts/*`

Common-engine stages:

- `ssot-fl-model` → `/ssot-fl-model <ip>`
- `ssot-cycle-model` → `/ssot-cycle-model <ip>`
- `ssot-equiv-goals` → `/ssot-equiv-goals <ip>`
- `ssot-dual-fcov` when dual functional/cycle coverage evidence is needed

## Cursor Use

Plan:

```bash
python3 .cursor/skills/rtl-to-signoff/scripts/rtl_to_signoff.py <ip> --profile dv --plan --until ssot-equiv-goals
```

Execute through equivalence goals:

```bash
python3 .cursor/skills/rtl-to-signoff/scripts/rtl_to_signoff.py <ip> --profile dv --execute --until ssot-equiv-goals
```

Artifacts are SSOT-derived. Do not hand-edit model outputs to fit RTL.
