# RTL Gen Plan Mode Rules

## Input Source Detection

On plan start, check for input in this order:

| Priority | Pattern | Source | Use Section |
|----------|---------|--------|-------------|
| 1 | `<ip>/yaml/<ip>.ssot.yaml` or legacy `<ip>/yaml/<ip>_ssot.yaml` / `<ip>/yaml/<ip>_config.yaml` | ssot-gen | §SSOT |
| 2 | no canonical SSOT | ssot-gen | stop with `[SSOT REQUIRED] -> ssot-gen` |

Production ATLAS planning is SSOT-only. Do not plan from MAS unless the user explicitly requests a legacy MAS-only flow outside SSOT signoff.

## §SSOT: Planning from YAML SSOT

When SSOT YAML is detected, plan from the structured data in `<ip>/yaml/<ip>.ssot.yaml`. If a `[SSOT HANDOFF]` message provides an explicit `SSOT:` path, use that exact file.

Reference: `workflow/ssot-gen/rules/ssot-template.yaml` for the canonical production SSOT schema, including required `function_model`, `cycle_model`, timing, power, security, error handling, debug observability, integration, DFT, synthesis, and quality gates.

### SSOT-Aware Task Decomposition

1. Parse `sub_modules` and `filelist.rtl` to determine output files. Do not assume fixed names such as regs/decoder/fifo/core unless the SSOT uses them.
2. Build a ledger that maps each output file to the SSOT sections it implements: ports, parameters, registers, memories, FSMs, features, dataflow, interrupts, function_model/cycle_model, timing, power, security, error behavior, debug observability, integration, DFT, synthesis, quality gates, and test requirements.
3. For every ledger row, classify the source as `SSOT-backed`, `TBD (missing in SSOT)`, or `not applicable by SSOT`. Plan RTL implementation only for `SSOT-backed` rows. A `TBD` row is a blocker and must become an SSOT enrichment request, not guessed RTL.
4. `ssot_gen` is only a complexity hint. It does not mean "use a fixed template"; it means the block might be mechanically derived if the SSOT is explicit enough.
5. Tasks must be derived from the actual YAML content. Example task shapes: "implement AXI4-Lite slave handshake from io_list + dataflow", "implement encrypted memory transform from features + memory", "implement CSR W1C fields from registers", "implement wrapper-only child_ssot instantiation".
6. Use `/gen-rtl <module>` to load the SSOT-specific RTL contract ledger and single visible TodoTracker item, then refine task detail/criteria from the current SSOT.
7. Keep planning bounded. One implementation ledger and one task split are enough; do not loop on architecture alternatives. If the split is ambiguous, choose the simplest compiling partition that preserves the SSOT top-level ports and behavior, then rely on compile/test repair.

### SSOT Gap Output Requirement

Plans and blocked execution reports must include a dedicated SSOT enrichment list whenever any required RTL fact is absent:

```
[SSOT TBD REPORT] -> ssot-gen
Module  : <ip_name>
Missing :
- yaml_path: <exact SSOT field path>
  needed_for: <rtl file/module/signal/task>
  question: <specific value/behavior/timing/side effect to add>
  current_rtl_action: TBD — not implemented
```

If there are no missing fields, include `SSOT TBD REPORT: none` in the plan/result.

### Generic IP Requirement

Plan for any leaf IP whose SSOT is complete. If the IP kind is unfamiliar, do not ask to add a Python generator template. Instead:

1. Identify behavioral primitives from SSOT: protocol endpoints, storage, transformations, FSMs, register side effects, error/response policy, and observability.
2. Create direct RTL writing tasks for those primitives.
3. Compile early, repair by reading errors, and iterate.
4. Ask ssot-gen only for missing SSOT facts, not for a fixed implementation template.
5. Do not add fixed Python/Jinja generator support for an IP kind. The immediate deliverable is RTL written from the current SSOT plus compile evidence.

### SSOT Directory Structure

```
[CODE_FENCE(22 chars)]
```

## §MAS: Planning from MAS Document (Legacy)

Legacy-only. If the user asked for SSOT-driven generation or a canonical SSOT should exist, do not use this path; emit `[SSOT REQUIRED] -> ssot-gen` instead.

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
- Never plan implementation for behavior not explicitly present in SSOT; mark it `TBD (missing in SSOT)` and list the exact SSOT field to add
- Final task MUST compile + lint with 0 errors and 0 unwaived warnings/diagnostics; Icarus `sorry:` counts as a diagnostic even when exit code is 0 unless SSOT `coding_rules.lint_waivers` explicitly waives it
- Plans must forbid parameterized part-selects inside procedural blocks. For any parameter-derived slice, plan a helper wire plus continuous assign outside `always`, `always_comb`, `always_ff`, or `always_latch`.
- Plans must keep SSOT manifest paths, actual RTL filenames, top module name, and `<ip>/list/<ip>.f` consistent. If the SSOT manifest is wrong, plan a precise ssot-gen escalation instead of silently relying on aliases.
- Never plan to modify files owned by other agents (tb/, sim/, lint/)
- Never plan to modify common workflow generator scripts just to support a new IP kind
- Every task must include concrete done criteria: file path, SSOT sections covered, compile/lint evidence, and no-placeholder check
