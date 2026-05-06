# SSOT → RTL Orchestration Rules

## When to Use SSOT Mode

SSOT mode activates when `<ip>/yaml/<ip>.ssot.yaml` exists. Legacy `<ip>/yaml/<ip>_config.yaml` and `<ip>/yaml/<ip>_ssot.yaml` are accepted, but the canonical ssot-gen output is `<ip>.ssot.yaml`.

## SSOT YAML → RTL File Mapping

Parse the `sub_modules` section to determine which files to generate:

| sub_module field | Meaning | RTL action |
|------------------|---------|------------|
| `name` | Module identity | Implement or instantiate this exact module name |
| `file` | Owned RTL path | Write this file under `<ip>/rtl/` when ownership is `manifest` |
| `ownership` | Boundary contract | `manifest` is written here; `child_ssot` is instantiated only |
| `ssot_gen` | Complexity hint | May be mechanically simple, but still derive logic from the current SSOT; do not use a fixed IP-kind template |
| `description` | Intent | Use with `function_model`, `cycle_model`, and constraints to decide behavior |

### Leaf Hierarchy Ownership

Read `sub_modules[].ownership` before writing any RTL:

- `ownership: manifest` — generate the listed `file` inside the current
  IP workspace and include it in `<ip>/list/<ip>.f`.
- `ownership: child_ssot` — this submodule is an independently owned
  child IP. Do not write its RTL in the parent workflow. Its `ssot`
  path is dispatched to a separate child `ssot-gen`/`rtl-gen` session.
  The parent may instantiate the child top module only after that child
  RTL exists on disk.

The SoC-level `soc.ssot.yaml` remains top-instance-only. Internal
implementation hierarchy belongs to leaf IP YAML files.

## SSOT Section Processing Order

1. `top_module` → module name for all files
2. `parameters` → `<ip>_pkg.sv` (localparam)
3. `io_list.interfaces` → `<ip>_wrapper.sv` port declarations
4. `io_list.clock_domains` → clock/reset ports
5. `registers.register_list` → `<ip>_regs.sv` (APB decode + register FFs)
6. `registers.config` → channel stride/base offset constants
7. `function_model` → `<ip>_core.sv` architectural behavior, state updates, side effects, error handling, and reference-model traceability
8. `cycle_model` → `<ip>_core.sv` pipeline stages, handshake timing, latency bounds, ordering, and backpressure behavior
9. `fsm` → `<ip>_fsm.sv` state machine (if ssot_gen: true)
10. `features` + `dataflow` → `<ip>_core.sv` datapath/control implementation details
11. `memory.instances` → `<ip>_mfifo.sv` buffer instantiation
12. `interrupts` → `<ip>_regs.sv` irq logic
13. `timing` → clock targets, latency constraints, and STA-facing assumptions
14. `power` → clock-gating, reset-retention, UPF/no-UPF assumptions
15. `security` → assets, threat mitigations, privilege/safety behavior
16. `error_handling` → response/fault propagation, recovery, and escalation state
17. `debug_observability` → status outputs, waveform probes, and trace events
18. `integration` → bus attachment, address map, dependencies, and SoC contract
19. `dft` → scan/test-mode ports, controllability, and observability
20. `synthesis` → dialect, constraints, PPA targets, required EDA outputs
21. `quality_gates` → required evidence before claiming RTL/signoff success
22. `filelist` → `<ip>/list/<ip>.f` filelist
23. `coding_rules` → lint waivers, style enforcement

`function_model`, `cycle_model`, timing/power/security/error/debug/integration/DFT/synthesis constraints,
and `quality_gates` are mandatory for production RTL. If any required section is
missing or only placeholder text, stop and emit a precise `[SSOT QUESTION] -> ssot-gen`
request instead of guessing the architecture.

## AI-Driven RTL Rule

Do not add or rely on IP-kind fixed Python/Jinja generators to make a new design pass.
RTL-gen writes the current IP's RTL directly from the current SSOT, compiles it,
repairs real diagnostics, and escalates missing SSOT facts back to ssot-gen.
Small repeated structures such as port declarations, parameters, or register fields
may be written mechanically during the RTL edit, but the source of truth remains the
YAML content and the production quality gates.

## Handoff Recognition

```
[CODE_FENCE(22 chars)]
```

Extract `Module` and `SSOT` → read the handoff `SSOT:` path first. If no path is provided, prefer `<ip>/yaml/<ip>.ssot.yaml`.

## Multi-File Generation

Unlike MAS mode (single .sv), SSOT mode produces multiple files:

```
[CODE_FENCE(22 chars)]
```

## Filelist Generation

Write `<ip>/list/<ip>.f` from `filelist.rtl` section:
```
[CODE_FENCE(22 chars)]
```

## Quality Gates

| Gate | Condition | Action |
|------|-----------|--------|
| YAML parsed | All SSOT sections read | Begin generation |
| Per-file generation | Each sub_module processed | Continue |
| Compile check | `python3 ../brian_hw/common_ai_agent/workflow/rtl-gen/scripts/rtl_compile_report.py <ip> --top <top_module>` from project root | Fix errors/warnings/Icarus `sorry:` diagnostics |
| Lint | DUT-only `dut_lint_report.py` from project root | Fix warnings |
| Done | 0 errors, 0 warnings, 0 style violations | Output SSOT RESULT |

## Error Recovery

- Missing YAML section → report to ssot-gen, skip that file
- RTL preflight blocks → run the LLM direct-write loop from SSOT TODOs; do not add a fixed generator/template path.
- Compile error in LLM-authored RTL → repair the owning RTL module and rerun compile.
- Lint warning → fix source. Waivers are valid only when SSOT `coding_rules.lint_waivers` names the exact warning code, file, signal, and rationale; never add ad-hoc `verilator lint_off` comments to LLM-authored RTL.
- Procedural parameterized part-select → fix source. Move `$clog2(...)`, `PARAM-1:0`, and other parameter-derived slices out of `always`/`always_comb`/`always_ff`/`always_latch` into helper wires driven by continuous assigns.
