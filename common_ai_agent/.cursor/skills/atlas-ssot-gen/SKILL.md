---
name: atlas-ssot-gen
description: Work with the ssot-gen workflow for requirements interview, SSOT YAML authoring, import, grill-me, to-ssot, and SSOT validation. Use when creating or repairing yaml/<ip>.ssot.yaml or requirement approval evidence.
---

# Atlas SSOT Gen

`ssot-gen` is the interactive requirements and SSOT authority workflow. Cursor should treat it as the owner for `req/`, `yaml/<ip>.ssot.yaml`, SSOT Q&A cards, imports, and semantic requirement gaps.

## Runtime Workspace

- Workspace: `workflow/ssot-gen/workspace.json`
- Prompt: `workflow/ssot-gen/system_prompt.md`
- Commands: `workflow/ssot-gen/commands/*.json`
- Scripts: `workflow/ssot-gen/scripts/*`

Important surfaces:

- `/import`
- `/grill-me`
- `/to-ssot`
- `/verify-ssot`
- `/resolve-rtl-blockers`

## Cursor Use

For full greenfield convergence, prefer:

```bash
python3 .cursor/skills/rtl-to-signoff/scripts/rtl_to_signoff.py <ip> --root . --profile ssot-to-signoff --provider fake --execute
```

For validation only:

```bash
bash workflow/ssot-gen/scripts/check_ssot_disk.sh <ip>
python3 workflow/ssot-gen/scripts/verify_ssot.py <ip>
```

Do not change SSOT to match broken RTL/TB/sim evidence. Route semantic gaps to human review or `ssot-gen`.
