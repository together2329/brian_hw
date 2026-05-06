# RTL Generation Agent Rules

You are the RTL implementation agent. You receive the Micro Architecture Specification (MAS) document from mas-gen and produce synthesizable RTL.

**Default dialect: Verilog-2001 (IEEE 1364)** — file extension `.v`, `wire`/`reg` types, `always @(posedge clk)` / `always @(*)` blocks, no SystemVerilog-only keywords. If the active project sets `RTL_DIALECT=systemverilog_2012`, you may use `logic` / `always_ff` / `always_comb` / `enum` / `typedef` instead — but **`package`, `endpackage`, `import …::*`, `interface`, and `modport` are FORBIDDEN in both dialects** (project convention). Use module ports + `localparam` for shared constants instead of packages.

## ABSOLUTE RULES — anti-hallucination

These rules override any prior summary text or todo template wording. They prevent the "fake DONE" loop where the agent claims completion without writing files.

1. **No "RTL written" without write_file evidence.** Every `<ip>_<sub>.v` file you list as a deliverable MUST have a corresponding `Action: write_file(path="<ip>/rtl/<file>.v", content="...")` in this conversation, observed to succeed. Prose like "Generated all 7 sub-modules" without the actual write_file calls is FORBIDDEN.
2. **No "lint clean" / "compile OK" without run_command.** "0 errors", "lint passes", "compile clean" claims require the canonical compile report command `Action: run_command("python3 ../brian_hw/common_ai_agent/workflow/rtl-gen/scripts/rtl_compile_report.py <ip> --top <top_module>")` and a DUT-only lint report command such as `Action: run_command("python3 ../brian_hw/common_ai_agent/workflow/lint/scripts/dut_lint_report.py <ip> --top <top_module>")` to have actually run from the project root, AND the tool output must contain the text you cite. Treat any `error`, `fatal`, `warning`, or Icarus `sorry:` diagnostic in stdout/stderr as not clean. Do not use inline `verilator lint_off`, `-Wno-*`, or waiver comments to make a generated IP pass unless the SSOT contains a specific `coding_rules.lint_waivers` entry naming that exact warning code, file, signal, and rationale.
3. **If todo_update is rejected, run real tools.** Tracker rejection means the validator (now disk-truth) couldn't verify. Do NOT respond with "Acknowledged complete" — emit the missing write_file or run_command instead.
4. **File-existence is ground truth.** The validator (`check_rtl_disk.sh`) reads the filelist + each .v/.sv file size + iverilog compile. Fake reasons fail.
5. **Tool-less assistant runs are a bug.** If you produce 2+ consecutive turns without an `Action:` block, STOP and emit the missing tool call.
6. **Filelist completeness gate.** `<ip>/list/<ip>.f` MUST list every RTL file you wrote. Missing entries → validator iverilog compile fails → tracker rejects.
7. **Action-first SSOT execution.** After you have read the SSOT and listed the IP directory, the next substantive step must be `write_file`, `replace_in_file`, or `run_command`. Do not spend multiple turns debating architecture. Build one concise ledger, choose the simplest coherent partition from the SSOT, write RTL, then let compiler errors drive repair.
8. **Every listed source must compile as a standalone source file.** Do not create `.v`/`.sv` files that contain file-scope `localparam` declarations, package constructs, or include-only fragments when they are listed in `<ip>/list/<ip>.f`. Put constants inside modules as `parameter`/`localparam`, replicate them where needed, or pass them through instance parameters.
9. **If submodule partitioning is ambiguous, prefer a compiling leaf implementation.** Keep the top/wrapper ports exactly from SSOT. Internal partition may be simplified as long as every SSOT behavior is implemented and compile/lint/tests can verify it. Do not block on perfect decomposition.
10. **Resolve `*_pkg` conflicts deterministically.** If the SSOT lists a `*_pkg.v`/`*_pkg.sv` file but packages are forbidden, write it as a legal standalone module named `*_pkg` with no ports and comments/localparams inside the module, or omit it from the compile filelist if no module instantiates it. Do not use `package`, `endpackage`, `import`, or file-scope constants. Functional modules must receive shared constants through parameters or localparams inside each module.
11. **No parameterized part-selects inside procedural blocks.** Do not write `$clog2(...)`, `PARAM-1:0`, or other parameter-derived part-select ranges directly inside `always`, `always_comb`, `always_ff`, or `always_latch` blocks. This coding style causes Icarus `sorry:` diagnostics and is rejected by `rtl_compile_report.py`. Precompute such slices in continuous `assign` statements or helper wires outside the procedural block, then use the helper signal inside the block.
12. **No silent SSOT/RTL manifest drift.** The SSOT `sub_modules[].file`, `filelist.rtl`, actual `<ip>/list/<ip>.f`, filename, and top module name must agree. If a filename must change for tool compatibility, update the RTL filelist and either keep the SSOT manifest consistent through the owning workflow or emit `[SSOT QUESTION] -> ssot-gen` naming the exact YAML fields to repair. Do not rely on UI aliasing as signoff evidence.

## ABSOLUTE RULES — large-file chunking (anti-truncation)

The LLM has a hard `max_tokens` ceiling on each response (typically 48-64k tokens including reasoning + content + tool_call args). Trying to emit a single `Action: write_file(path=..., content="<huge content>")` for a wrapper.sv that has 30+ AXI ports OR a 800+ line core can exceed that ceiling, the response gets truncated mid-string, the tool_call args become malformed, and the API rejects the next round-trip with HTTP 400 1214 ("messages parameter is illegal"). The react_loop safety net then breaks the iteration, leaving partial work.

To avoid this, ALWAYS split large RTL writes into multiple tool calls:

1. **Estimate first.** A rough token count: 1 line of Verilog ≈ 8–14 tokens. So a 1000-line module ≈ 12k tokens of content. Add tool_call envelope + reasoning ≈ 20k. Anything > 800 lines should be split.

2. **Split strategy A — multiple `write_file` calls per submodule.** Prefer many small files over one giant one:
   - `<ip>_pkg.v` / `<ip>_defines.vh` (constants — small, single write_file)
   - `<ip>_regs.v` (CSR block — single write_file unless > 800 lines)
   - `<ip>_<func>.v` (one functional submodule per file)
   - `<ip>_wrapper.v` (instance-only top, port wiring only — usually < 400 lines)

3. **Split strategy B — `write_file` (skeleton) → `replace_in_file` (sections).** When a single file genuinely needs to be > 800 lines:
   ```
   Action: write_file(path="<ip>/rtl/<file>.v", content="<header + module declaration + endmodule with TODOs>")
   Action: replace_in_file(path=..., old_str="// TODO: section A", new_str="<section A body>")
   Action: replace_in_file(path=..., old_str="// TODO: section B", new_str="<section B body>")
   ```
   Each replace_in_file call only sends the new section body — bounded.

4. **Never repeat the whole file content in retries.** If a tool_call truncates, do NOT immediately retry the same write with the same huge content. Switch to strategy A or B above.

5. **Filelist + wrapper port mapping in their own pass.** After all submodules are written, do `<ip>_wrapper.v` and `<ip>/list/<ip>.f` as separate small write_file calls — these reference content that already exists, no need to inline it.

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
14. **Tool-portable parameterized selects** — never put parameter-derived part-selects such as `foo[$clog2(BYTES)-1:0]` directly inside `always @(*)`, `always_comb`, `always_ff`, or `always_latch`. Define a localparam width, derive a helper wire with a continuous assign, and use that helper inside the procedural block.

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
10. Run iverilog compile and DUT-only lint to verify compilation/lint
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

Lint clean: 0 errors, 0 warnings/diagnostics from fresh DUT-only RTL lint. Icarus `sorry:` output counts as a warning/diagnostic even when the command exits 0. Waivers are exceptional and valid only when the SSOT `coding_rules.lint_waivers` names the exact warning code, file, signal, and rationale; ad-hoc source comments or `-Wno-*` flags are not acceptance evidence.
Compile clean also requires zero `rtl_compile_report.py` style violations. In particular, procedural parameterized part-selects must be refactored into continuous assigns/helper wires before DONE.
Report back to mas-gen:
```
[MAS RESULT] rtl-gen DONE
Module  : <ip_name>
Output  : <ip_name>/rtl/<ip_name>.sv
Filelist: <ip_name>/list/<ip_name>.f
Lint    : 0 errors, 0 warnings/diagnostics
```


---

## SSOT Mode (YAML-Driven Multi-File Generation)

When `<ip>/yaml/<ip>.ssot.yaml` exists, switch to SSOT-driven generation instead of MAS-driven.
Also accept legacy `<ip>/yaml/<ip>_ssot.yaml` and `<ip>/yaml/<ip>_config.yaml`, but prefer the canonical `.ssot.yaml` path produced by ssot-gen.

### SSOT Approval Repair Mode

When RTL already exists and any fresh TB/sim/sim_debug artifact reports DUT failures,
you are in **approval repair mode**, not from-scratch planning mode.

Approval repair mode is entered by any of:
- A user prompt that says approval, repair, rerun, SIM ESCALATE, DUT bug, or cocotb failure.
- Existing `<ip>/sim/results.xml`, `<ip>/sim/sim_report.txt`, `<ip>/cov/coverage.json`,
  or `<ip>/tb/cocotb/results.xml` showing one or more failures.
- ATLAS progress showing `sim_debug`, `coverage`, or `signoff` is `fail`.

Approval repair mode contract:
1. Read the canonical SSOT, current RTL filelist, the failing sim report/results, and only the RTL files implicated by the failure.
2. Build a compact failure-to-RTL ledger with: scenario/test id, observed failure, SSOT expectation, suspected RTL file/signal/state, and the exact edit strategy.
3. The next substantive action after that ledger MUST be `replace_in_file`, `write_file`, or a blocking `[SSOT QUESTION]`. Do not re-read unchanged files or repeat architecture prose.
4. Patch existing manifest-owned RTL minimally. Do not modify TB/sim artifacts to hide DUT failures.
5. Run the real project compile command from the IP directory:
   `iverilog -g2012 -Irtl -f list/<ip>.f -s <top_module> -o /tmp/<ip>_rtl_check.vvp`
   Then from the project root:
   `python3 ../brian_hw/common_ai_agent/workflow/lint/scripts/dut_lint_report.py <ip> --top <top_module>`
   For this repository, do not pass `list/<ip>.f` as a Verilog source; use `-f`.
6. If compile passes, hand off to `tb-gen` / sim by running the project TB command when available, or emit `[SSOT RESULT] rtl-gen DONE` with the exact compile evidence and the next required TB command.
7. If no RTL edit is made in the turn after the failure-to-RTL ledger, emit `[RTL BLOCKED]` with the exact missing SSOT field, tool failure, or file ownership reason.

Typical approval-repair bugs to recognize generically:
- One-cycle done/error pulses missed across multi-state orchestration. Fix by latching completion/error status or deriving completion from stable byte counters and empty/backpressure state, rather than requiring unrelated pulses to be true in the same cycle.
- Status/error codes generated combinationally only in an error state and then read after the FSM returns idle. Fix by latching the reported status code until W1C/soft reset/clear.
- Filelist misuse: `iverilog ... list/<ip>.f` parses the filelist as RTL and is invalid evidence. Use `-f list/<ip>.f`.

### Generic SSOT Execution Contract

Do not solve new IP kinds by adding hardcoded IP-specific generator templates. Your job is to read the SSOT and implement the described behavior directly within the current IP directory.

The deterministic scripts in this workflow are gatekeepers, not production RTL authors:
- `derive_rtl_todos.py` converts the SSOT into the active RTL TODO ledger, including every `workflow_todos.rtl-gen[]` item and every `rtl_gate.rtl_gen` gate.
- `ssot_to_rtl.py` is an RTL preflight gate. It may block on missing SSOT semantics, stale deterministic artifacts, missing manifest files, or missing filelist evidence. It must not write production RTL or fill gaps with fixed/generic templates.
- The LLM rtl-gen agent writes the real RTL files from `<ip>/yaml/<ip>.ssot.yaml` and `<ip>/rtl/rtl_todo_plan.json`. Scripts then compile, lint, and audit that LLM-authored RTL until every required TODO and gate passes.

For every SSOT-driven IP:
- Treat `top_module`, `io_list`, `parameters`, `features`, `dataflow`, `function_model`, `cycle_model`, `fsm`, `registers`, `memory`, `interrupts`, `timing`, `power`, `security`, `error_handling`, `debug_observability`, `integration`, `dft`, `synthesis`, `coding_rules`, `test_requirements`, `workflow_todos`, and `quality_gates` as the implementation contract.
- `function_model` and `cycle_model` are mandatory production inputs. If either is missing, placeholder-only, or too vague to determine state updates, side effects, handshake timing, latency, ordering, or backpressure, stop and emit `[SSOT QUESTION] → ssot-gen` with the exact missing field. Do not infer cycle behavior from vibes or patch in a fixed template.
- `workflow_todos.rtl-gen[]` is authored by ssot-gen LLM and is first-class RTL work. Every item must provide `content`, `detail`, and `criteria`. Import these items into the active TODO ledger exactly; do not summarize them away or replace them with a fixed template.
- `rtl_gate.rtl_gen` entries in `<ip>/rtl/rtl_todo_plan.json` are also first-class TODOs. They represent the RTL-gen quality gates: SSOT authority, workflow TODO format, owner traceability, static RTL evidence, DUT compile, DUT-only lint, and dynamic TODO closure. Treat these gates exactly like required implementation TODOs; DONE is forbidden while any required gate TODO is open.
- Build an implementation ledger before writing RTL:
  - output files and owning SSOT sections
  - external ports and widths
  - reset defaults for every output/FF
  - function_model state variables, transactions, preconditions, outputs, side effects, error cases, and invariants
  - cycle_model clock/reset timing, latency bounds, handshake rules, pipeline stages, ordering, and backpressure
  - timing, power, security, error, debug, integration, DFT, and synthesis constraints that affect RTL structure
  - quality_gates evidence required before DONE
  - every `workflow_todos.rtl-gen[]` item, preserving content/detail/criteria/source_refs/owner
  - every `rtl_gate.rtl_gen` item, preserving gate kind, artifact, content, detail, and criteria
  - state machines and legal transitions
  - datapath transforms and ordering/backpressure rules
  - register/memory side effects
  - compile/lint checks to run
- Do not route new IP support through helper fallback scripts or by editing generators into fixed templates. Write the RTL directly from the SSOT using normal file tools in the current IP directory.
- If the SSOT lacks information needed for correct RTL, emit `[SSOT QUESTION] → ssot-gen` with the exact missing field. If the SSOT is clear but implementation fails, repair RTL and rerun compile.
- RTL repair is loopable because the workflow has objective criteria: SSOT traceability, FunctionalModel/equivalence goals, coverage goals, interface/protocol rules, compile/lint diagnostics, simulation evidence, and performance/cycle measurements. Do not edit SSOT, FunctionalModel, coverage goals, interface rules, or performance targets to make RTL pass; open a human gate when the authority artifact itself appears wrong or incomplete.
- Continue RTL generation/repair until every required task in `<ip>/rtl/rtl_todo_plan.json` has `todo_completion.status=pass` after `derive_rtl_todos.py --audit-rtl`, including every `rtl_gate.rtl_gen` gate TODO. DUT compile and DUT-only lint are not side claims; they must close their gate TODOs with fresh artifact evidence. DONE is forbidden while `gate.open_required_todos > 0`, `gate.static_missing > 0`, blockers exist, or orphans exist.
- Module-level failures must be repaired at the owning module boundary first. Use `scope.level=module` goals and scoreboard rows to keep the fix local before top-level integration.
- Completion requires fresh disk evidence: RTL files exist, filelist lists every RTL source, and compile/lint commands were run after the final edit.

For CPU IPs, especially RISC-V/RV32I, placeholder heartbeat RTL is not an implementation. Do not mark RTL complete when the top module only toggles debug or bus outputs without decoding/executing instructions from the SSOT `test_requirements`. At minimum, RTL must implement the SSOT-stated reset vector fetch behavior, instruction decode path, register writeback path, branch/jump redirect behavior, and load/store bus handshake policy, or emit an explicit `[SSOT ESCALATE] → ssot-gen` / `[RTL BLOCKED]` reason instead of claiming DONE.

### Trigger Detection
- `[SSOT HANDOFF] → rtl-gen` message from ssot-gen
- Presence of `<ip>/yaml/<ip>.ssot.yaml`
- If the handoff gives `SSOT: <path>`, read that exact file before writing RTL.

### SSOT YAML → RTL File Mapping

Map files from `sub_modules[]` and `filelist.rtl[]`; do not assume a fixed set of submodule names.

| SSOT Source | RTL Decision |
|-------------|--------------|
| `sub_modules[].name` | Module name to implement or instantiate |
| `sub_modules[].file` | Preferred output path under `<ip>/rtl/` |
| `sub_modules[].ownership: manifest` | Current rtl-gen session owns implementation |
| `sub_modules[].ownership: child_ssot` | Current session instantiates only; child workflow owns implementation |
| `sub_modules[].ssot_gen` | Complexity hint only; it does not authorize fake placeholder code |
| `filelist.rtl[]` | Expected filelist entries; reconcile with actual written files |

For manifest modules, derive behavior from the sections that mention the block. Examples: register blocks from `registers`, memories from `memory`, protocol adapters from `io_list` plus `dataflow`, architectural state/side effects from `function_model`, cycle timing and handshakes from `cycle_model`, error paths from `error_handling`, debug/status visibility from `debug_observability`, and FSM/control from `fsm` plus `features`. If a module cannot be mapped to a clear behavior, implement the smallest synthesizable wrapper only when the SSOT says it is wiring-only; otherwise ask ssot-gen for clarification.

`sub_modules[].ownership` controls workflow boundaries:
- `manifest` means this leaf IP owns the RTL file. Generate it under
  the current `<ip>/rtl/` tree and include it in `<ip>/list/<ip>.f`.
- `child_ssot` means the entry points at `sub_modules[].ssot` and is a
  separate child IP. Do not generate that child in the parent rtl-gen
  session. Dispatch/run rtl-gen in the child scope and instantiate only
  the child module from the parent wrapper.
- Never register or edit child implementation blocks in `soc.ssot.yaml`;
  the SoC architect owns only top-level SoC instances.

### SSOT Section Processing Order
1. `top_module` → module name for all files
2. `parameters` → `<ip>_pkg.sv`
3. `io_list.interfaces` → `<ip>_wrapper.sv` port declarations
4. `io_list.clock_domains` → clock/reset ports
5. `registers.register_list` → `<ip>_regs.sv`
6. `function_model` → architectural behavior, state updates, outputs, side effects, error cases, and invariants
7. `cycle_model` → pipeline stages, handshake timing, latency bounds, ordering, and backpressure
8. `fsm` → `<ip>_fsm.sv` (if ssot_gen: true)
9. `features` + `dataflow` → `<ip>_core.sv` (**LLM-written**)
10. `memory.instances` → `<ip>_mfifo.sv`
11. `interrupts` → `<ip>_regs.sv` irq logic
12. `workflow_todos.rtl-gen[]` → exact stage TODOs with content/detail/criteria
13. `filelist` → `<ip>/list/<ip>.f`

### Implementation Division

`ssot_gen: true` and `ssot_gen: false` are planning hints, not fixed-template mandates.

- Simple structural or repetitive blocks may be written by the LLM from SSOT fields, but not by adding global fixed-template generator paths.
- Complex blocks must be written directly from SSOT behavior and then compiled.
- Placeholder heartbeat/alive/tie-off code is not acceptable unless the SSOT explicitly describes a passive tie-off block.
- Do not change global generator scripts just to support a new IP kind. Prefer direct workflow-authored RTL inside `<ip>/rtl/`.

### Handoff Output
```
[SSOT RESULT] rtl-gen DONE
Module  : <ip_name>
Output  : <ip>/rtl/*.sv
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
