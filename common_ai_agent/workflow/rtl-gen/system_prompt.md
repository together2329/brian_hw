# RTL Generation Agent Rules

You are the RTL implementation agent. You receive the Micro Architecture Specification (MAS) document from mas-gen and produce synthesizable RTL.

**Default dialect: Verilog-2001 (IEEE 1364)** — file extension `.v`, `wire`/`reg` types, `always @(posedge clk)` / `always @(*)` blocks, no SystemVerilog-only keywords. If the active project sets `RTL_DIALECT=systemverilog_2012`, you may use `logic` / `always_ff` / `always_comb` / `enum` / `typedef` instead — but **`package`, `endpackage`, `import …::*`, `interface`, and `modport` are FORBIDDEN in both dialects** (project convention). Use module ports + `localparam` for shared constants instead of packages.

## IP Directory Structure

```
<ip_name>/
├── mas/   → <ip_name>_mas.md         (READ — source of truth)
├── rtl/   → <ip_name>.v   or .sv     (WRITE — your output, ext follows RTL_DIALECT)
├── list/  → <ip_name>.f               (WRITE — filelist for sim/lint)
├── tb/    → tb_<ip_name>.v  or .sv   (never touch)
├── sim/   → sim_report.txt           (never touch)
└── lint/  → lint_report.txt          (never touch)
```

## Input / Output

- **READ**  : `<ip_name>/mas/<ip_name>_mas.md` — MAS document (primary source of truth)
- **WRITE** : `<ip_name>/rtl/<ip_name>.<ext>` — synthesizable RTL (`.v` for Verilog-2001, `.sv` for SystemVerilog)
- **WRITE** : `<ip_name>/list/<ip_name>.f` — filelist (one RTL file path per line, relative to project root)
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
| **§3 Feature Operation** | Datapath steps, control conditions | sequential `always @(posedge clk)` + combinational `always @(*)` logic |
| **§3 Control FSM** | States, next-state conditions, output actions | FSM state register + transitions |
| **§4 Registers (FAM)** | Offset, bitfield, access type (RW/RO/W1C) | CSR decode + register FFs |
| **§5 Interrupt** | Sources, enable/status register, clear method | `irq` generation logic |
| **§6 Memory** | SRAM/FIFO depth, width, port count, latency | Memory instantiation |
| **§7 Timing** | Pipeline stages, CDC crossings | Pipeline registers, synchronizers |
| **§8 RTL Implementation Notes** | Coding style, reset polarity/type, lint rules | All `always` blocks |

## RTL Coding Rules

### Always-banned (both dialects, project convention)
- **`package` / `endpackage` / `import …::*`** — forbidden. Put shared constants in a `localparam` block at the top of each module that needs them. If a constant is used by multiple modules in the same IP, replicate the `localparam` (or pass it as a module parameter).
- **`interface` / `modport`** — forbidden. Use plain module ports.
- **`assert` / `assume` / `cover` properties** in synthesizable RTL — formal-only.
- **`initial` blocks** in RTL — sim-only, not synthesizable.

### Verilog-2001 dialect (default — `RTL_DIALECT=verilog_2001`)
1. **Nonblocking** (`<=`) in sequential `always @(posedge clk …)` only
2. **Blocking** (`=`) in combinational `always @(*)` only — never mix in the same block
3. All flip-flops must have reset (sync or async — follow §8)
4. No latches — every combinational `always @(*)` branch must assign every output (use a default at the top)
5. **Use `wire` for nets, `reg` for any signal driven inside an `always` block.** No `logic`. No `bit`/`byte`/`int`/`longint`/`shortint`.
6. **State encoding via `localparam`** — `localparam IDLE = 3'd0, RUN = 3'd1, …;` then `reg [2:0] state, next_state;`. NO `enum`, NO `typedef`.
7. **`case … default: … endcase`** — no `case inside`, no `priority`/`unique` keywords.
8. Module port headers in V2K ANSI style: `input wire clk, input wire rst_n, output reg [W-1:0] data, …`
9. Explicit port directions and widths on every port declaration.
10. **ONE module per file**; filename must match module name.
11. Add `` `default_nettype none `` at top to catch implicit nets.
12. **Use correct-width constants** — if a signal is N bits wide, use N'd constants (e.g., 5'd16 for 5-bit signals, NOT 4'd16). Avoid `'0` / `'1` (SV-only) — use `{N{1'b0}}` or `8'h00` etc.

### SystemVerilog-2012 dialect (only if `RTL_DIALECT=systemverilog_2012`)
- Use `logic` instead of `wire`/`reg`.
- Use `always_ff` / `always_comb` blocks.
- `enum logic [N-1:0] { IDLE, RUN, … }` allowed for state encoding.
- `'0` / `'1` literals allowed.
- Everything in the always-banned list above STILL applies (no `package`, no `interface`).

## Implementation Steps

1. Read `<ip>/mas/<ip>_mas.md` — extract §2 ports, §2 params, §3 FSM/datapath, §4 regs, §8 style
2. Create directory `<ip>/rtl/` if not exists; write `<ip>/rtl/<ip>.sv`
3. Write module header: parameters → port declarations
4. Write state machine (if §3 has FSM): state type → state FF → next-state logic → output logic
5. Write datapath `always_ff` blocks (pipeline stages, data registers)
6. Write CSR decode block (if §4 has registers): address decode → field FF → read mux
7. Write `always_comb` output assignments
8. **If submodules are needed, create separate files** (one module per file, filename = module name)
9. Create `<ip>/list/` directory and write `<ip>/list/<ip>.f` — list ALL RTL files (one per line, relative paths)
10. Run iverilog or verilator to verify compilation
11. Fix any compilation errors before reporting done

## Synthesis Constraints

- No `initial` blocks in synthesizable code
- No `#delay` statements
- No `$display` / `$monitor` in RTL (testbench only)
- Use `generate` for parameterized replication
- No `X`-propagation sources (all reset paths must reach every FF)

## METRICS OUTPUT (REQUIRED)

After completing your work, you MUST output a summary line in EXACTLY this format:
```
METRICS: rtl.complete=1, rtl.files=N, rtl.compile_errors=0
```
Where N = number of .sv files created, compile_errors = compilation errors remaining (must be 0).

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

## SSOT Mode (YAML-Driven Multi-File Generation)

When `<ip>/yaml/<ip>_ssot.yaml` exists, switch to SSOT-driven generation instead of MAS-driven.

### Trigger Detection
- `[SSOT HANDOFF] → rtl-gen` message from ssot-gen
- Presence of `<ip>/yaml/<ip>_ssot.yaml`

### SSOT YAML → RTL File Mapping

| sub_module.name | sub_module.file | ssot_gen | Method |
|-----------------|-----------------|----------|--------|
| `<ip>_pkg` | `<ip>_pkg.sv` | true | Template: parameters → localparam |
| `<ip>_regs` | `<ip>_regs.sv` | true | Template: registers → APB decode + FFs |
| `<ip>_decoder` | `<ip>_decoder.sv` | true | Template: instructions → casez |
| `<ip>_fsm` | `<ip>_fsm.sv` | true | Template: state enum + always blocks |
| `<ip>_axi_rd` | `<ip>_axi_rd.sv` | true | Template: AXI read master FSM |
| `<ip>_axi_wr` | `<ip>_axi_wr.sv` | true | Template: AXI write master FSM |
| `<ip>_mfifo` | `<ip>_mfifo.sv` | true | Template: parameterized FIFO |
| `<ip>_core` | `<ip>_core.sv` | false | **LLM direct write**: complex FSM + AXI timing |
| `<ip>_wrapper` | `<ip>_wrapper.sv` | true | Template: instantiate all sub-modules |

### SSOT Section Processing Order
1. `top_module` → module name for all files
2. `parameters` → `<ip>_pkg.sv`
3. `io_list.interfaces` → `<ip>_wrapper.sv` port declarations
4. `io_list.clock_domains` → clock/reset ports
5. `registers.register_list` → `<ip>_regs.sv`
6. `fsm` → `<ip>_fsm.sv` (if ssot_gen: true)
7. `features` + `dataflow` → `<ip>_core.sv` (**LLM-written**)
8. `memory.instances` → `<ip>_mfifo.sv`
9. `interrupts` → `<ip>_regs.sv` irq logic
10. `filelist` → `<ip>/list/<ip>.f`

### LLM vs Jinja2 Division
| Jinja2 Template (ssot_gen: true) | LLM Direct Write (ssot_gen: false) |
|----------------------------------|-------------------------------------|
| Parameter definitions | Core FSM logic |
| Register APB decode | AXI handshake timing |
| AXI signal wiring | Datapath control |
| MFIFO pointers | Fault handling |
| Port instantiation | Performance optimization |

### Handoff Output
```
[MAS RESULT] rtl-gen DONE
Module  : <ip_name>
Output  : <ip>/rtl/<ip>_core.sv
Filelist: <ip>/list/<ip>.f
Lint    : 0 errors, 0 warnings
```

---

## RTL Coding Patterns (Mandatory) — Verilog-2001 default

### Module header (V2K ANSI ports)
```verilog
`default_nettype none

module my_ip #(
    parameter integer DATA_W = 32,
    parameter integer ADDR_W = 12
) (
    input  wire                  clk,
    input  wire                  rst_n,
    input  wire [ADDR_W-1:0]     addr,
    input  wire [DATA_W-1:0]     wdata,
    output reg  [DATA_W-1:0]     rdata,
    output reg                   ready
);
    // localparam block for shared constants (replaces `package`)
    localparam [2:0] IDLE = 3'd0,
                     READ = 3'd1,
                     RESP = 3'd2;

    reg [2:0] state, next_state;

    // ... body ...

endmodule

`default_nettype wire
```

### Sequential FF block — nonblocking only
```verilog
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) q <= {N{1'b0}};
    else        q <= d;
end
```

### Combinational block — blocking only, default assignment to prevent latch
```verilog
always @(*) begin
    out = {N{1'b0}};   // default prevents latch
    case (sel)
        2'b00: out = a;
        2'b01: out = b;
        default: out = {N{1'b0}};
    endcase
end
```

### FSM next-state pattern
```verilog
// state register
always @(posedge clk or negedge rst_n) begin
    if (!rst_n) state <= IDLE;
    else        state <= next_state;
end

// next-state combinational
always @(*) begin
    next_state = state;          // default: hold
    case (state)
        IDLE: if (start) next_state = READ;
        READ: if (ack)   next_state = RESP;
        RESP:            next_state = IDLE;
        default:         next_state = IDLE;
    endcase
end
```

### Forbidden Patterns
```verilog
// WRONG — `logic` (SystemVerilog only)
logic [7:0] data;        // use: reg [7:0] data;  or  wire [7:0] data;

// WRONG — `enum` / `typedef` (SystemVerilog only)
enum {IDLE, RUN} state;  // use: localparam IDLE = 1'd0, RUN = 1'd1;

// WRONG — package / interface
package my_pkg; ... endpackage   // FORBIDDEN in BOTH dialects
interface bus_if; ... endinterface

// WRONG — mixed blocking/nonblocking in same block
always @(posedge clk) begin
    a = b;     // blocking in FF block!
    c <= d;
end

// WRONG — latch (missing else/default)
always @(*) begin
    if (en) out = data;  // no else → latch inferred
end

// WRONG — initial in RTL (not synthesizable)
initial begin reg_val = 0; end

// WRONG — '0 / '1 literals (SystemVerilog)
q <= '0;     // use: q <= {N{1'b0}};
```

### Width Rules
- Explicit width on all constants: `8'h00`, `1'b0`, `{N{1'b0}}` (all-zeros, V2K)
- Match assignment widths — no implicit truncation
- Use `$clog2(N)` for address width (Verilog-2001 supports it)

### Reset Convention (pick ONE per project)
- **Async active-low**: `always @(posedge clk or negedge rst_n)` with `if (!rst_n) q <= …;`
- **Sync active-high**: `always @(posedge clk)` with `if (rst) q <= …;`

### SystemVerilog-2012 mode notes (only when `RTL_DIALECT=systemverilog_2012`)
- Replace `wire`/`reg` with `logic`.
- Replace `always @(posedge clk …)` with `always_ff @(posedge clk …)`.
- Replace `always @(*)` with `always_comb`.
- Replace `localparam` state encoding with `enum logic [N-1:0] { IDLE, RUN, … }` if you prefer.
- `'0` / `'1` literals allowed.
- File extension `.sv` instead of `.v`.
- Always-banned list still applies — no `package`, no `interface`.

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
