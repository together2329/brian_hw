---
name: atlas-eda-signoff
description: Handle EDA signoff stages for lint, synthesis, STA, PnR, STA-post, and DFT. Use when working on backend hardware quality gates or PDK/OpenROAD/OpenSTA flows.
---

# Atlas EDA Signoff

## Read First

- `workflow/COMMON_ENGINE_FLOW.md`
- `workflow/PLATFORM.md`
- `doc/wiki/workflow-ownership-and-boundaries.md`
- `.env.example` for PDK and tool environment variables.

## Stage Scripts

Reference these in place:

- `workflow/lint/scripts/auto_lint.sh`
- `workflow/lint/scripts/run_full_lint.sh`
- `workflow/syn/scripts/auto_syn.sh`
- `workflow/sta/scripts/auto_sta.sh`
- `workflow/pnr/scripts/auto_pnr.sh`
- `workflow/sta-post/scripts/auto_sta_post.sh`
- `workflow/dft/scripts/auto_dft.sh`
- `workflow/scripts/pdk_env.sh`

Full EDA chains may need Linux, WSL2, Docker, and local PDK/tool paths. On macOS, expect partial validation unless the required tools are installed.

Do not edit EDA reports to pass gates. Fix inputs, rerun the owning stage, and preserve evidence.
