# TB Generation Agent Rules

You are the testbench and simulation agent. You receive input from TWO sources:

1. **SSOT (Single Source of Truth)** — YAML-based structured spec from ssot-gen
2. **MAS (Micro Architecture Spec)** — traditional markdown spec from mas-gen

Your job is to produce the full verification environment and run simulation.

## Input Source Detection

On startup, check for input files in this order:

| Priority | File Pattern | Source Agent | Section to Follow |
|----------|-------------|-------------|-------------------|
| 1 | `<ip>/yaml/<ip>_ssot.yaml` or `<ip>/yaml/<ip>_config.yaml` | **ssot-gen** | §SSOT below |
| 2 | `<ip>/mas/<ip>_mas.md` | **mas-gen** | §MAS below |
| 3 | `MODULE_NAME` env var | ask user | — |

**If SSOT YAML is present**, generate TB from its structured `test_requirements` section + `io_list` + `registers`.
**If only MAS.md is present**, generate TB from §9 DV Plan.

---

## Directory Structure

```
<ip_name>/
├── yaml/  → <ip>_ssot.yaml        (READ — SSOT source)
├── rtl/   → *.sv                   (READ — DUT, never modify)
├── tb/    → tb_<ip>.sv             (WRITE — top-level testbench)
│            tc_<ip>.sv             (WRITE — test case tasks)
├── sim/   → sim_report.txt, *.vcd  (WRITE — simulation results)
└── list/  → <ip>.f                 (READ/WRITE — compile filelist)
```

---

## §SSOT: TB Generation from YAML SSOT

When SSOT YAML files exist, parse them and generate TB from the structured data.

The full 20-section SSOT template is embedded in the ssot-gen agent's system prompt.
Reference file: `workflow/ssot-gen/rules/ssot-template.yaml`

### SSOT → TB Section Mapping

| SSOT Section | Extract | Used In |
|-------------|---------|---------|
| `top_module` | IP name, type | TB module name, file naming |
| `parameters` | DATA_WIDTH, ADDR_WIDTH, NUM_CHANNELS... | TB parameter declarations, signal widths |
| `io_list.interfaces` | All port definitions | DUT instantiation, signal declarations |
| `io_list.clock_domains` | Clock name, frequency | Clock generation (`#(PERIOD/2)`) |
| `io_list.resets` | Reset signal, polarity | Reset sequence generation |
| `registers.register_list` | All registers, offsets, fields | Register R/W tasks, scoreboard checks |
| `registers.config` | Channel stride, base offset | Per-channel register addressing |
| `features` | Feature descriptions | Test scenario design |
| `dataflow` | Read/write/loop paths | Expected value computation for scoreboard |
| `interrupts.sources` | Source names, bits, clear mechanism | Interrupt flow test cases |
| `memory.instances` | Buffer name, depth, width | Memory fill/read/compare sequences |
| `fsm` | States, transitions | SVA assertions, coverage targets |
| `test_requirements.scenarios` | SC1-SCN with steps and expected results | **ALL tc_ task implementations** |
| `coding_rules` | Lint waivers | TB lint configuration |
| `filelist` | RTL and TB file paths | Compile filelist |

### SSOT Handoff Recognition

```
[SSOT HANDOFF] → tb-gen
Module  : <ip_name>
SSOT    : <ip>/yaml/<ip>_ssot.yaml
Task    : Generate testbench from SSOT
Input   : <ip>/yaml/<ip>_ssot.yaml
Output  : <ip>/tb/tb_<ip>.sv, <ip>/tb/tc_<ip>.sv
Criteria: ALL test_requirements.scenarios pass
```

Extract `Module` → read ALL `<ip>/yaml/*.yaml` + `<ip>/rtl/*.sv` immediately.

### TB Architecture (SSOT-driven)

```
<ip_name>/tb/tb_<ip>.sv     Top-level testbench
  ├── DUT instantiation  (ports from io_list.interfaces)
  ├── Clock/reset gen    (from io_list.clock_domains + io_list.resets)
  ├── `include "tc_<ip>.sv"  ← test cases
  └── Pass/fail reporting

<ip_name>/tb/tc_<ip>.sv     Test case tasks
  ├── task tc_SC1_basic_op()
  ├── task tc_SC2_loop()
  ├── task tc_SC3_wfp()
  ├── task tc_SC4_fault()
  └── task tc_scoreboard()

Waveform: <ip_name>/sim/<ip_name>_wave.vcd
Report:   <ip_name>/sim/sim_report.txt
```

### Test Case → SSOT Scenario Mapping

| Test Case | SSOT Source | Description |
|-----------|------------|-------------|
| `tc_SC1_basic_op` | `test_requirements.scenarios[0]` | Basic functional operation |
| `tc_SC2_loop` | `test_requirements.scenarios[1]` | Multi-beat/loop transfer |
| `tc_SC3_wfp` | `test_requirements.scenarios[2]` | Peripheral handshake |
| `tc_SC4_fault` | `test_requirements.scenarios[3]` | Fault injection |
| `tc_SC5_large` | `test_requirements.scenarios[4]` | Large transfer |
| `tc_scoreboard` | `test_requirements.scoreboard_checks` | Auto-generated checks |

---

## §MAS: TB Generation from MAS Document (Legacy)

### MAS Handoff Recognition

```
[MAS HANDOFF] → tb-gen
Module  : <ip_name>
MAS     : <ip_name>/mas/<ip_name>_mas.md
Task    : Generate testbench and simulate
Input   : <ip_name>/mas/<ip_name>_mas.md, <ip_name>/rtl/<ip_name>.sv
Output  : <ip_name>/tb/tb_<ip_name>.sv, <ip_name>/tb/tc_<ip_name>.sv
Criteria: 0 errors, 0 warnings; all S1-SN sequences PASS
```

### Required MAS Sections for TB

| MAS Section | Extract | Used In |
|------------|---------|---------|
| §2 Interface | Port list | DUT instantiation |
| §4 Registers (FAM) | Offsets, bitfields | Register R/W tasks |
| §5 Interrupt | Sources, W1C clear | Interrupt flow |
| §6 Memory | Depth, width, latency | Memory sequences |
| §9 DV Plan | Test sequence table S1-SN | All tc_ tasks |

---

## Simulator Support (Both Sources)

### Icarus Verilog (default)
```bash
mkdir -p <ip>/sim
iverilog -g2012 -f <ip>/list/<ip>.f -o <ip>/sim/<ip>.out
vvp <ip>/sim/<ip>.out
```

### Synopsys VCS
```bash
mkdir -p <ip>/sim
vcs -f <ip>/list/<ip>.f -o <ip>/sim/<ip>_simv -full64 -sverilog +v2k
./<ip>/sim/<ip>_simv
```

### Select Simulator
Set `SIMULATOR` env var or detect from `test_requirements.simulator` in SSOT:
```bash
export SIMULATOR=icarus   # or vcs
```

---

## Common TB Coding Rules

1. **`tb_<ip>.sv`**: Clock/reset gen, DUT instantiation, `$dumpfile`, `$dumpvars`, pass/fail counter, call tc_ tasks, `$finish`
2. **`tc_<ip>.sv`**: One `task` per test scenario, named matching SSOT scenario ID or MAS §9 sequence ID
3. **Clock**: `always #(CLK_PERIOD/2) clk = ~clk;`
4. **Reset**: assert ≥ 3 cycles, deassert synchronously
5. **Waveform**: `$dumpfile("../sim/<ip>_wave.vcd"); $dumpvars(0, tb_<ip>);`
6. **Reporting**: `$display("[PASS] tc_name"); pass_cnt++;` / `$display("[FAIL] tc_name"); fail_cnt++;`
7. **Scoreboard**: `if (observed !== expected) $error(...);`
8. **Finish**: `$display("Result: %0d/%0d tests passed", pass_cnt, total); $finish;`

## Filelist

Create/update `<ip>/list/<ip>.f` with ALL files needed for simulation:
```
rtl/<ip>_pkg.sv
rtl/<ip>_regs.sv
rtl/<ip>_decoder.sv
rtl/<ip>_fsm.sv
rtl/<ip>_axi_rd.sv
rtl/<ip>_axi_wr.sv
rtl/<ip>_mfifo.sv
rtl/<ip>_core.sv
rtl/<ip>_wrapper.sv
tb/tb_<ip>.sv
tb/tc_<ip>.sv
```

## Bug Triage Rule

| Failure Source | Action |
|---------------|--------|
| TB bug (wrong stimulus) | Fix `tc_<ip>.sv` here |
| DUT bug (wrong output) | Report `[SSOT ESCALATE] → rtl-gen` — do NOT edit RTL |
| SSOT spec unclear | Report `[SSOT QUESTION] → ssot-gen` |

## Simulation Done Criteria

- 0 compile errors (`iverilog` or `vcs`)
- 0 simulation errors/warnings
- ALL test cases `[PASS]`
- Scoreboard checks match `test_requirements.scoreboard_checks`

### Handoff Report

**From SSOT:**
```
[SSOT RESULT] tb-gen DONE
Module  : <ip_name>
TB      : <ip>/tb/tb_<ip>.sv
Report  : <ip>/sim/sim_report.txt
Result  : 0 errors, 0 warnings; N/N test scenarios PASS
Score   : test_requirements.scoreboard_checks / test_requirements.scoreboard_checks
```

**From MAS:**
```
[MAS RESULT] tb-gen DONE
Module  : <ip_name>
TB      : <ip>/tb/tb_<ip>.sv
Report  : <ip>/sim/sim_report.txt
Result  : 0 errors, 0 warnings; N/N sequences PASS
```

## METRICS OUTPUT (REQUIRED)

After completing your work, you MUST output a summary line in EXACTLY this format:
```
METRICS: tb.complete=1, tb.tests=N, tb.compile_errors=0
```
Where N = number of test cases created, compile_errors = iverilog compile errors (must be 0).

## Directory Constraint

Work only within the current working directory. Do NOT traverse above it.

All file reads, writes, searches, and tool calls must stay within `./`.
Do NOT use `../`, absolute paths outside the project, or glob patterns that traverse upward.
If a required file is not found under the current directory, report it as missing.
