# SSOT → TB Orchestration Rules

## When to Use SSOT Mode

SSOT mode activates when `<ip>/yaml/<ip>_config.yaml` (or `<ip>_ssot.yaml`) exists.

## SSOT YAML → TB File Mapping

| SSOT Section | Generates | Method |
|-------------|-----------|--------|
| `test_requirements.scenarios` | All `tc_SC*.sv` task bodies | Template: {% for scenario in scenarios %} |
| `io_list.interfaces[].ports[]` | DUT signal declarations | Template: {% for iface in interfaces %}{% for port in iface.ports %} |
| `io_list.clock_domains` | Clock generation block | Template: {% for clk in clock_domains %} |
| `io_list.resets` | Reset sequence task | Direct mapping |
| `registers.register_list[]` | Register write/read helper tasks | Template: {% for reg in register_list %} |
| `registers.config` | Channel stride helper functions | Direct mapping |
| `interrupts.sources[]` | Interrupt check/clear tasks | Template: {% for src in sources %} |
| `memory.instances[]` | Memory fill/verify tasks | Template: {% for mem in instances %} |
| `features[]` | Expected value computation | LLM-written |
| `dataflow` | Scoreboard reference model | LLM-written |
| `top_module` | TB module naming | Direct mapping |

## TB File Structure (SSOT-driven)

```
[CODE_FENCE(22 chars)]
```

## Test Case Generation Order

1. Parse `test_requirements.scenarios[]` → one `tc_<SC_id>()` task per entry
2. Parse `registers.register_list[]` → helper tasks: `write_reg()`, `read_reg()`, `poll_status()`
3. Parse `interrupts.sources[]` → helper tasks: `check_irq()`, `clear_irq()`
4. Parse `dataflow` → expected value computation logic
5. Parse `features[]` → scoreboard self-check
6. Parse `io_list` → DUT instantiation, signal wiring

## Scoreboard Integration

From `test_requirements.scoreboard_checks: 17`:
```systemverilog
[CODE_FENCE(22 chars)]
```

## Simulator Selection

| `test_requirements.simulator` | Compile Command | Run Command |
|------------------------------|-----------------|-------------|
| `"iverilog"` (default) | `iverilog -g2012 -f <ip>.f -o sim/<ip>.out` | `vvp sim/<ip>.out` |
| `"vcs"` | `vcs -full64 -sverilog -f <ip>.f -o sim/<ip>_simv` | `./sim/<ip>_simv` |

## Quality Gates

| Gate | Condition | Action |
|------|-----------|--------|
| YAML parsed | All SSOT sections read | Begin TB generation |
| TB generated | tb_<ip>.sv + tc_<ip>.sv written | Compile |
| Compile clean | 0 errors (iverilog or vcs) | Run simulation |
| Sim PASS | All [PASS], scoreboard checks met | Write sim_report.txt |
| Done | 0 errors, 0 warnings | Output SSOT RESULT |

## Error Recovery

- Missing SSOT `test_requirements` section → ask ssot-gen to add it
- Compile error in TB → fix signal names from io_list
- Sim FAIL → triage: TB bug fix here, DUT bug escalate to rtl-gen
- Scoreboard mismatch → check dataflow section for correct expected values
