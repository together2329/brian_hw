# SSOT Orchestration Rules

## Workflow Model

ssot-gen is the **Single Source of Truth authoring agent**. It writes production leaf IP YAML files that drive downstream RTL, testbench, simulation, coverage, and EDA workflows.

1. Scaffold a new `<ip>/` directory when needed
2. Write exactly one canonical leaf SSOT: `<ip>/yaml/<ip>.ssot.yaml`
3. Fill all production canonical sections, including `sub_modules`, `function_model`, `cycle_model`, `timing`, `power`, `security`, `error_handling`, `debug_observability`, `integration`, `dft`, `synthesis`, `test_requirements`, and `quality_gates`
4. Mark simple internal blocks as `ownership: manifest`
5. Promote reusable or independently verified children as `ownership: child_ssot`
6. Validate the YAML on disk
7. Output `[SSOT HANDOFF]` blocks for downstream agents

## Handoff Protocol

When SSOT is complete and validated:

```
[CODE_FENCE(23 chars)]
```

## Quality Gates

| Gate | Condition | Next Agent |
|------|-----------|------------|
| REQ -> SSOT | Requirements gathered, IP name confirmed | ssot-gen starts YAML authoring |
| SSOT -> VALIDATE | `<ip>/yaml/<ip>.ssot.yaml` written | YAML parse + production SSOT disk checks |
| VALIDATE -> HANDOFF | Leaf SSOT passes checks | rtl-gen or tb-gen agent |
| HANDOFF -> RTL | `[SSOT HANDOFF]` names path and constraints | rtl-gen |

## File Ownership

| Agent | Writes | Never modifies |
|-------|--------|----------------|
| `req-gen` | `<ip>/req/<ip>_requirements.md` | YAML, RTL, TB |
| `ssot-gen` | `<ip>/yaml/<ip>.ssot.yaml` | RTL, TB, sim outputs |
| `rtl-gen` | `<ip>/rtl/<ip>.sv`, `<ip>/list/<ip>.f` | YAML, TB |
| `tb-gen`  | `<ip>/tb/cocotb/*` or selected TB backend files | YAML, RTL |
| `sim`     | `<ip>/sim/sim_report.txt` | YAML, source |
| `lint`    | `<ip>/lint/lint_report.txt` | YAML, source |

## Leaf IP Hierarchy Rules

- `soc.ssot.yaml` owns top-level SoC instances and connections.
- A leaf IP YAML owns its internal `sub_modules`.
- Use `ownership: manifest` for normal internal files generated or written as part of the IP.
- Use `ownership: child_ssot` only when that submodule needs its own ssot-gen/rtl-gen/tb-gen/sim session.

## Error Recovery

- YAML validation fail -> edit `<ip>/yaml/<ip>.ssot.yaml`, rerun validation
- Missing or weak `sub_modules` -> update manifest vs child_ssot ownership before handoff
- RTL/lint/sim issues -> hand off to rtl-gen/tb-gen/sim; do not fix them inside ssot-gen unless the YAML contract is wrong
