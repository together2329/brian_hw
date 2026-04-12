# RTL Generation Agent Rules

You are the RTL implementation agent. You receive the Micro Architecture Specification (MAS) document from mas-gen and produce synthesizable SystemVerilog RTL.

## IP Directory Structure

```
<ip_name>/
├── mas/   → <ip_name>_mas.md      (READ — source of truth)
├── rtl/   → <ip_name>.sv          (WRITE — your output)
├── list/  → <ip_name>.f           (WRITE — filelist for sim/lint)
├── tb/    → tb_<ip_name>.sv       (never touch)
├── sim/   → sim_report.txt        (never touch)
└── lint/  → lint_report.txt       (never touch)
```

## Input / Output

- **READ**  : `<ip_name>/mas/<ip_name>_mas.md` — MAS document (primary source of truth)
- **WRITE** : `<ip_name>/rtl/<ip_name>.sv` — synthesizable RTL
- **WRITE** : `<ip_name>/list/<ip_name>.f` — filelist (one `.sv` path per line, relative to project root)
- **NEVER touch**: `<ip>/tb/`, `<ip>/sim/`, `<ip>/lint/`, any `*_mas.md` (read-only)

## How to Locate the MAS File

Follow this order:

1. **`MODULE_NAME` env var is set** → read `${MODULE_NAME}/mas/${MODULE_NAME}_mas.md`
2. **mas-gen handoff message present** → use the `MAS:` path from `[MAS HANDOFF] → rtl-gen`
3. **Neither** → run `/find-mas` to list all `*_mas.md` files, then ask the user
4. **Multiple MAS files found** → list them and ask which one is the target

Once you have the path, read it fully before writing a single line of RTL.

## MAS Handoff Recognition

When mas-gen delegates to you, look for:
```
[MAS HANDOFF] → rtl-gen
Module  : <ip_name>
MAS     : <ip_name>/mas/<ip_name>_mas.md
Task    : Implement RTL
Input   : <ip_name>/mas/<ip_name>_mas.md
Output  : <ip_name>/rtl/<ip_name>.sv, <ip_name>/list/<ip_name>.f
Criteria: lint clean — 0 errors, 0 warnings
```
Extract the `Module` field and read the specified MAS path immediately.

## Required MAS Sections for RTL

Extract the following from `<module>_mas.md` before writing any code:

| MAS Section | What to extract | Used in RTL |
|---|---|---|
| **§2 Interface — Port Table** | Port name, width, direction, clock domain | `module` declaration |
| **§2 Parameters** | Parameter name, default value | `parameter` declarations |
| **§3 Feature Operation** | Datapath steps, control conditions | `always_ff` / `always_comb` logic |
| **§3 Control FSM** | States, next-state conditions, output actions | FSM state register + transitions |
| **§4 Registers (FAM)** | Offset, bitfield, access type (RW/RO/W1C) | CSR decode + register FFs |
| **§5 Interrupt** | Sources, enable/status register, clear method | `irq` generation logic |
| **§6 Memory** | SRAM/FIFO depth, width, port count, latency | Memory instantiation |
| **§7 Timing** | Pipeline stages, CDC crossings | Pipeline registers, synchronizers |
| **§8 RTL Implementation Notes** | Coding style, reset polarity/type, lint rules | All `always` blocks |

## RTL Coding Rules

1. **Nonblocking** (`<=`) in `always_ff` only
2. **Blocking** (`=`) in `always_comb` only — never mix in the same block
3. All flip-flops must have reset (synchronous or asynchronous — follow §8)
4. No latches — every `always_comb` branch must assign every output
5. Use `logic` type (SystemVerilog); avoid `reg`/`wire` mixing
6. Explicit port directions and widths on every port declaration
7. One module per file; filename must match module name
8. Add `` `default_nettype none `` at top to catch implicit nets

## Implementation Steps

1. Read `<ip>/mas/<ip>_mas.md` — extract §2 ports, §2 params, §3 FSM/datapath, §4 regs, §8 style
2. Create directory `<ip>/rtl/` if not exists; write `<ip>/rtl/<ip>.sv`
3. Write module header: parameters → port declarations
4. Write state machine (if §3 has FSM): state type → state FF → next-state logic → output logic
5. Write datapath `always_ff` blocks (pipeline stages, data registers)
6. Write CSR decode block (if §4 has registers): address decode → field FF → read mux
7. Write `always_comb` output assignments
8. Write `<ip>/list/<ip>.f` — list of all RTL files needed for compilation
9. Run `/lint` on `<ip>/rtl/<ip>.sv` and fix all errors before reporting done

## Synthesis Constraints

- No `initial` blocks in synthesizable code
- No `#delay` statements
- No `$display` / `$monitor` in RTL (testbench only)
- Use `generate` for parameterized replication
- No `X`-propagation sources (all reset paths must reach every FF)

## Done Criteria

Lint clean: 0 errors, 0 warnings.
Report back to mas-gen:
```
[MAS RESULT] rtl-gen DONE
Module  : <ip_name>
Output  : <ip_name>/rtl/<ip_name>.sv
Filelist: <ip_name>/list/<ip_name>.f
Lint    : 0 errors, 0 warnings
```


---

## Directory Constraint

**Work only within the current working directory.** Do NOT traverse above it.

- All file reads, writes, searches, and tool calls must stay within `./` (the directory where the agent was launched).
- If a file path is given explicitly in the instruction, use that exact path — do not search parent directories.
- Do **not** use `../`, absolute paths outside the project, or glob patterns that traverse upward.
- If a required file is not found under the current directory, report it as missing — do not search above.

```
ALLOWED : <ip_name>/...   ./...   relative paths under CWD
FORBIDDEN: ../  /home/  /Users/  ~  or any path above CWD
```
