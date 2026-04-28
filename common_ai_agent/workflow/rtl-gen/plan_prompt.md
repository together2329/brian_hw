# RTL Gen Plan Mode Rules

## Input Source Detection

On plan start, check for input in this order:

| Priority | Pattern | Source | Use Section |
|----------|---------|--------|-------------|
| 1 | `<ip>/yaml/<ip>_ssot.yaml` or `<ip>/yaml/<ip>_config.yaml` | ssot-gen | §SSOT |
| 2 | `<ip>/mas/<ip>_mas.md` | mas-gen | §MAS |
| 3 | Ask user | — | — |

## §SSOT: Planning from YAML SSOT

When SSOT YAML is detected, plan from the structured data in `<ip>/yaml/<ip>_ssot.yaml`.

Reference: `workflow/ssot-gen/rules/ssot-template.yaml` for the 20-section schema.

### SSOT-Aware Task Decomposition

1. Parse `sub_modules` to determine output files (one file per sub_module)
2. `ssot_gen: true` → simpler template-based task
3. `ssot_gen: false` → complex LLM task (typically `<ip>_core.sv`)
4. Tasks from YAML sections: parameters → registers → decoder → fsm → axi_rd/wr → mfifo → core → wrapper → filelist → lint
5. Use `/ssot-rtl <module>` to load SSOT-specific todo template

### SSOT Directory Structure

```
[CODE_FENCE(22 chars)]
```

## §MAS: Planning from MAS Document (Legacy)

Task 1 is ALWAYS **"Read `<ip>/mas/<ip>_mas.md`"** — the Micro Architecture Specification from mas-gen.

### MAS Task Decomposition Rules

1. Split tasks by MAS section: §2 ports/params → §3 FSM → §3 datapath → §4 registers → §5 interrupt → §6 memory → filelist → lint
2. Each task targets ONE always block or ONE output group — never mix
3. Include expected signal names (from MAS §2 port table) in every task detail
4. Reference the MAS section explicitly in each task
5. Write `<ip>/list/<ip>.f` after RTL is complete
6. Final task MUST be lint check

## Common Rules (Both Sources)

- Verify completeness before planning RTL tasks
- Each task maps to a single output file
- Include file paths in every task detail
- Final task MUST compile + lint with 0 errors, 0 warnings
- Never plan to modify files owned by other agents (tb/, sim/, lint/)
