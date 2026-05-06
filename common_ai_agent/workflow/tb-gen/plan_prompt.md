# TB Gen Plan Mode Rules

## Input Source Detection

On plan start, check for input in this order:

| Priority | Pattern | Source Agent | Use Section |
|----------|---------|-------------|-------------|
| 1 | `<ip>/yaml/<ip>.ssot.yaml`, `<ip>/yaml/<ip>_ssot.yaml`, or `<ip>/yaml/<ip>_config.yaml` | **ssot-gen** | §SSOT |
| 2 | `<ip>/mas/<ip>_mas.md` | **mas-gen** | §MAS |
| 3 | Ask user | — | — |

## §SSOT: Planning from YAML SSOT

When SSOT YAML is detected, plan from the canonical `<ip>/yaml/<ip>.ssot.yaml` unless a handoff gives an exact SSOT path.

Reference: `workflow/ssot-gen/rules/ssot-template.yaml` for the canonical production SSOT schema, including required `function_model`, `cycle_model`, timing, security/error, debug/observability, integration, DFT/synthesis, and `quality_gates`.

### SSOT-Aware Task Decomposition

1. Parse `test_requirements.scenarios[]` → one test/subtest per scenario using the scenario's actual id/name, stimulus, and expected result
2. Parse `io_list` → DUT signals, protocol helpers, clock period, reset sequence, and legal ready/valid/backpressure behavior
3. Parse `features` + `dataflow` → scoreboard model and expected output computation
4. Parse `registers.register_list[]` only if registers exist; otherwise record explicit no-CSR policy
5. Parse `memory.instances[]`, `interrupts.sources[]`, and `fsm` → memory model/checkers, interrupt tests, state/transition coverage
6. Parse `parameters` → TB parameter declarations and signal widths
7. Parse `timing`, `security`, `error_handling`, `debug_observability`, and `integration` → latency/timeouts, negative tests, waveform probes, and protocol model topology
8. Parse `dft`, `synthesis`, and `quality_gates` → identify evidence that TB can produce versus EDA/signoff evidence that must be escalated to downstream workflows
9. Parse `filelist` and actual `<ip>/list/<ip>.f` → compile sources
10. Plan sim loop with cocotb pytest by default for complex IPs, or SV simulator when SSOT/project requires it
11. Use `/ssot-tb <module>` or `/ssot-tb-goal <module>` to load SSOT-specific todo structure, then refine detail/criteria from the current SSOT

### Generic IP Requirement

Plan for any leaf IP whose SSOT and RTL are present. If the IP kind is unfamiliar, do not request a new fixed TB template. Instead:

1. Generate protocol drivers from `io_list`.
2. Generate checks from `test_requirements`, `features`, and `dataflow`.
3. Generate functional bins from scenarios/features/FSM/error paths.
4. Run simulation, repair TB-only failures, and escalate RTL/spec failures precisely.

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
- Every task must include concrete criteria: scenario coverage, checker evidence, command to run, artifact path, and failure owner
- Always plan VCD and coverage JSON output for sim_debug
- Plan Mode is read/search only. Do not run `which`, `python3 -c`, `make`, `iverilog`, pytest, or simulator commands in Plan Mode; write those exact commands into the todo criteria and execute them only after user confirmation.
- The final verification command must be the exact user-facing command that will be documented in the report, with no external PATH overrides or hidden shell setup.
