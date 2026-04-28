# SSOT → RTL Orchestration Rules

## When to Use SSOT Mode

SSOT mode activates when `<ip>/yaml/<ip>_config.yaml` (or `<ip>_ssot.yaml`) exists.

## SSOT YAML → RTL File Mapping

Parse the `sub_modules` section to determine which files to generate:

| sub_module.name | sub_module.file | ssot_gen | Method |
|-----------------|-----------------|----------|--------|
| `<ip>_pkg` | `<ip>_pkg.sv` | true | Template: {% for param in parameters %} → localparam |
| `<ip>_regs` | `<ip>_regs.sv` | true | Template: {% for reg in registers %} → APB decode + FFs |
| `<ip>_decoder` | `<ip>_decoder.sv` | true | Template: {% for instr in instructions %} → casez |
| `<ip>_fsm` | `<ip>_fsm.sv` | true | Template: state enum + always blocks |
| `<ip>_axi_rd` | `<ip>_axi_rd.sv` | true | Template: AXI read master FSM |
| `<ip>_axi_wr` | `<ip>_axi_wr.sv` | true | Template: AXI write master FSM |
| `<ip>_mfifo` | `<ip>_mfifo.sv` | true | Template: parameterized FIFO |
| `<ip>_core` | `<ip>_core.sv` | false | LLM: complex FSM + AXI control timing |
| `<ip>_wrapper` | `<ip>_wrapper.sv` | true | Template: instantiate all sub-modules |

## SSOT Section Processing Order

1. `top_module` → module name for all files
2. `parameters` → `<ip>_pkg.sv` (localparam)
3. `io_list.interfaces` → `<ip>_wrapper.sv` port declarations
4. `io_list.clock_domains` → clock/reset ports
5. `registers.register_list` → `<ip>_regs.sv` (APB decode + register FFs)
6. `registers.config` → channel stride/base offset constants
7. `fsm` → `<ip>_fsm.sv` state machine (if ssot_gen: true)
8. `features` + `dataflow` → `<ip>_core.sv` (LLM-written)
9. `memory.instances` → `<ip>_mfifo.sv` buffer instantiation
10. `interrupts` → `<ip>_regs.sv` irq logic
11. `filelist` → `<ip>_core.f` filelist
12. `coding_rules` → lint waivers, style enforcement

## LLM vs Jinja2 Division

| Jinja2 Template (ssot_gen: true) | LLM Direct Write (ssot_gen: false) |
|----------------------------------|-------------------------------------|
| Parameter definitions | Core FSM logic |
| Register APB decode (for loops) | AXI handshake timing |
| AXI signal wiring | Datapath control |
| MFIFO read/write pointers | Fault handling |
| Port instantiation (wrapper) | Performance optimization |

## Handoff Recognition

```
[CODE_FENCE(22 chars)]
```

Extract `Module` → read ALL `<ip>/yaml/*.yaml` files immediately.

## Multi-File Generation

Unlike MAS mode (single .sv), SSOT mode produces multiple files:

```
[CODE_FENCE(22 chars)]
```

## Filelist Generation

Write `<ip>/list/<ip>_core.f` from `filelist.rtl` section:
```
[CODE_FENCE(22 chars)]
```

## Quality Gates

| Gate | Condition | Action |
|------|-----------|--------|
| YAML parsed | All SSOT sections read | Begin generation |
| Per-file generation | Each sub_module processed | Continue |
| Compile check | iverilog -c `<ip>_core.f` | Fix errors |
| Lint | verilator --lint-only | Fix warnings |
| Done | 0 errors, 0 warnings | Output SSOT RESULT |

## Error Recovery

- Missing YAML section → report to ssot-gen, skip that file
- Template generation fails → fall back to LLM direct write
- Compile error in generated file → fix template or manually patch .sv
- Lint warning → add waiver or fix source
