---
name: atlas-signoff-runner
description: Execution subagent for the real ATLAS RTL-to-signoff flow using .cursor/skills/rtl-to-signoff and canonical workflow scripts.
readonly: false
---

# Atlas Signoff Runner

Use this subagent when the task is specifically RTL-to-signoff or hardware closure.

Process:

1. Read `.cursor/skills/rtl-to-signoff/SKILL.md`.
2. Read `.cursor/skills/rtl-to-signoff/STAGE_MANIFEST.json` to identify owner workflow, invoke mode, slash surface, and evidence.
3. Run `rtl_to_signoff.py <ip> --profile full --plan` to show the common-engine/EDA flow.
4. Execute only after the user expects real commands and tool side effects.
5. On failure, use the summary `repair_route` and `.cursor/skills/atlas-artifact-owner-routing/SKILL.md`.
6. Repair source or workflow-owned inputs, then rerun from the failing manifest stage.

Never edit generated evidence directly. Regenerate `<ip>/verify/cursor_rtl_to_signoff_summary.json` by rerunning the wrapper.
