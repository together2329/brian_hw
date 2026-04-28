# SSOT Orchestration Rules

## Workflow Model

ssot-gen is the **Single Source of Truth authoring agent**. It writes YAML files that drive automated Jinja2 + Python code generation.

1. Writing YAML SSOT files (7 domains + 1 schema)
2. Validating YAML against Cerberus schema
3. Authoring Jinja2 templates
4. Writing Python generator scripts
5. Running `make all` (validate -> generate -> lint -> sim)
6. Outputting `[SSOT HANDOFF]` blocks for downstream agents

## Handoff Protocol

When SSOT is complete and validated:

```
[CODE_FENCE(23 chars)]
```

## Quality Gates

| Gate | Condition | Next Agent |
|------|-----------|------------|
| REQ -> SSOT | Requirements gathered, IP name confirmed | ssot-gen starts YAML authoring |
| SSOT -> VALIDATE | All 8 YAML files written | Cerberus schema validation |
| VALIDATE -> GENERATE | All YAML pass schema | Jinja2 template rendering |
| GENERATE -> LINT | RTL files generated | verilator --lint-only |
| LINT -> SIM | 0 warnings | iverilog simulation |
| SIM -> HANDOFF | 17/17 scoreboard checks | rtl-gen or tb-gen agent |

## File Ownership

| Agent | Writes | Never modifies |
|-------|--------|----------------|
| `req-gen` | `<ip>/req/<ip>_requirements.md` | YAML, RTL, TB |
| `ssot-gen` | `<ip>/yaml/*.yaml`, `<ip>/templates/**`, `<ip>/generators/**` | req file |
| `rtl-gen` | `<ip>/rtl/<ip>.sv`, `<ip>/list/<ip>.f` | YAML, TB |
| `tb-gen`  | `<ip>/tb/tb_<ip>.sv`, `<ip>/tb/tc_<ip>.sv` | YAML, RTL |
| `sim`     | `<ip>/sim/sim_report.txt` | YAML, source |
| `lint`    | `<ip>/lint/lint_report.txt` | YAML, source |

## LLM + Jinja2 Division of Labor

| Jinja2 (frame) | LLM (detail) |
|----------------|--------------|
| `always_ff` blocks with `{% for %}` loops | YAML authoring: register meanings, FSM edge cases |
| APB decode `case` statements | Core FSM logic, AXI timing |
| AXI signal width parameterization | Test scenario design |
| Markdown table generation from YAML | Documentation explanations |
| Scoreboard check loops | Architecture decisions |

## Error Recovery

- YAML validation fail -> edit YAML, re-run `make yaml-validate`
- Template rendering error -> edit `.sv.j2`, re-run `make rtl`
- Lint warning -> edit template or YAML, re-generate
- Sim failure -> check YAML FSM, RTL logic; iterate
