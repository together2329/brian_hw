# TB Gen Plan Mode Rules

## Input Source Detection

On plan start, check for input in this order:

| Priority | Pattern | Source Agent | Use Section |
|----------|---------|-------------|-------------|
| 1 | `<ip>/yaml/<ip>_ssot.yaml` or `<ip>/yaml/<ip>_config.yaml` | **ssot-gen** | §SSOT |
| 2 | `<ip>/mas/<ip>_mas.md` | **mas-gen** | §MAS |
| 3 | Ask user | — | — |

## §SSOT: Planning from YAML SSOT

When SSOT YAML is detected, plan from `<ip>/yaml/<ip>_ssot.yaml`.

Reference: `workflow/ssot-gen/rules/ssot-template.yaml` for the 20-section schema.

### SSOT-Aware Task Decomposition

1. Parse `test_requirements.scenarios[]` → one tc_ task per scenario (SC1-SCN)
2. Parse `registers.register_list[]` → helper tasks (write_reg, read_reg, poll_csr)
3. Parse `interrupts.sources[]` → interrupt test tasks
4. Parse `io_list` → DUT instantiation signals, clock period
5. Parse `parameters` → TB parameter declarations, signal widths
6. Parse `filelist` → compile filelist
7. Sim loop with `test_requirements.simulator` (iverilog or VCS)
8. Use `/ssot-tb <module>` to load SSOT-specific todo template

### SSOT TB Directory Structure

```
[CODE_FENCE(22 chars)]
```

### Simulator Selection

| SSOT Field | Compile | Run |
|-----------|---------|-----|
| `test_requirements.simulator: "iverilog"` | `iverilog -g2012 -f <ip>.f -o sim/<ip>.out` | `vvp sim/<ip>.out` |
| `test_requirements.simulator: "vcs"` | `vcs -full64 -sverilog -f <ip>.f -o sim/<ip>_simv` | `./sim/<ip>_simv` |

## §MAS: Planning from MAS Document (Legacy)

Task 1 is ALWAYS **"Read `<ip>/mas/<ip>_mas.md` and `<ip>/rtl/<ip>.sv`"** — both required before any TB code.

### MAS Task Decomposition Rules

1. Split: `tc_*.sv` (test cases) before `tb_*.sv` (top level)
2. Name each tc_ task after MAS §9 sequence ID: `tc_S1_reset`, `tc_S2_normal_op`, ...
3. List ALL test case names before writing any code
4. Sim loop task with loop=true, max=15
5. Coverage review at end

## Common Rules (Both Sources)

- Verify DUT RTL exists before planning
- Each task maps to a single output file or task function
- Include file paths in every task detail
- Final task MUST compile + sim with 0 errors, 0 warnings
- Never plan to modify RTL files (escalate bugs to rtl-gen)
