# RTL Coding Rules (rtl-gen)

**RTL syntax policy: Verilog-2001 (IEEE 1364) in `.sv` files** — use `wire`/`reg`, `localparam` state encoding, and `always @(…)` blocks. SystemVerilog RTL constructs are not part of generated RTL.

## Always Banned

| Banned construct | Use instead |
|---|---|
| `package` / `endpackage` / `import …::*` | A `localparam` block at the top of the consuming module. Replicate per-module if shared. |
| `interface` / `modport` | Plain module ports. |
| `function` / `endfunction` / `task` / `endtask` | Inline wires, continuous assigns, always blocks, and case statements. |
| `for` / `while` | Explicit unrolled logic or SSOT-derived static structure. |
| `assert` / `assume` / `cover` properties | Move to formal-only files outside the synthesizable RTL. |
| `initial` blocks (in synthesizable RTL) | Sim-only — keep out of `<ip>/rtl/`. |

## Verilog-2001 Mode

### Mandatory Patterns

```verilog
`default_nettype none

module my_ip #(
    parameter integer DATA_W = 32
) (
    input  wire              clk,
    input  wire              rst_n,
    input  wire [DATA_W-1:0] d,
    output reg  [DATA_W-1:0] q
);

    // FSM states via localparam (NO enum, NO typedef)
    localparam [1:0] IDLE = 2'd0,
                     RUN  = 2'd1,
                     DONE = 2'd2;

    reg [1:0] state, next_state;

    // Sequential — nonblocking only
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) q <= {DATA_W{1'b0}};
        else        q <= d;
    end

    // Combinational — blocking, default to prevent latch
    always @(*) begin
        next_state = state;       // default: hold
        case (state)
            IDLE: if (start) next_state = RUN;
            RUN:  if (done)  next_state = DONE;
            DONE:            next_state = IDLE;
            default:         next_state = IDLE;
        endcase
    end

endmodule

`default_nettype wire
```

### Banned SystemVerilog Constructs

```verilog
// NEVER: SystemVerilog-only types
logic [7:0] data;          // use: reg [7:0] data;  or  wire [7:0] data;
bit / byte / int / longint / shortint   // use Verilog primitives

// NEVER: SystemVerilog blocks
always_ff @(posedge clk) ...     // use: always @(posedge clk …)
always_comb / always_latch       // use: always @(*)

// NEVER: enum / typedef
enum {IDLE, RUN} state;          // use: localparam IDLE = 1'd0, RUN = 1'd1;
typedef logic [7:0] byte_t;      // not allowed

// NEVER: SystemVerilog literals
q <= '0;                         // use: q <= {N{1'b0}};
q <= '1;                         // use: q <= {N{1'b1}};
'{a, b, c}                       // not allowed in V2K

// NEVER: case extensions
case (sel) inside ...            // use plain `case`
priority case / unique case      // not in V2K

// NEVER: mixed blocking/nonblocking
always @(posedge clk) begin
    a = b;     // WRONG — blocking in sequential block
    c <= d;
end

// NEVER: latch (missing else / default)
always @(*) begin
    if (en) out = data;          // no else → latch inferred
end

// NEVER: initial in RTL
initial begin reg_val = 0; end   // not synthesizable
```

## Width Rules

- Explicit width on all constants: `8'h00`, `1'b0`. In V2K use `{N{1'b0}}` for all-zeros (no `'0`).
- Check width match in assignments — no implicit truncation.
- Use `$clog2(N)` for address-width calculation.

## Parameterization Rules

- Expose user-tunable input/output shape as `parameter integer` values when the SSOT permits configurability: data width, address width, input/output channel count, lane count, FIFO depth, burst length, and similar interface dimensions.
- Use clear parameter names such as `DATA_W`, `ADDR_W`, `IN_CH`, `OUT_CH`, `LANES`, and `DEPTH`; derive internal helper widths with named `localparam` values.
- Do not scatter magic numeric widths through port declarations, regs/wires, masks, counters, or slices. Reference the parameter/localparam instead.
- If the SSOT fixes an external interface width, keep that public contract exact but centralize the literal in one named parameter/localparam so a future SSOT-approved change is easy.
- Add a short comment beside each user-facing parameter explaining what changes when the user overrides it.

## Arithmetic Rules

- Prefer exact shift-based arithmetic over inferred multiplier/divider hardware.
- Multiplication or division by powers of two must use `<<` / `>>` with explicit width handling.
- Constant scale factors may use shift-add or shift-subtract forms when the transform is mathematically exact and preserves SSOT behavior. Example: `x * 10` may become `(x << 3) + (x << 1)`.
- Use `*` or `/` only when the SSOT explicitly requires a general multiplier/divider, or when no exact shift-based implementation preserves timing, overflow, rounding, signedness, and saturation semantics.
- Never replace non-power-of-two division with a shift approximation unless the SSOT explicitly names that approximation.
- For every optimized arithmetic expression, add a short comment explaining the equivalence and any width, rounding, truncation, signedness, or saturation decision.

## Commenting Rules

- Comment the meaning and intent of non-obvious hardware, not the Verilog syntax.
- Add clean, concise comments for FSM transition groups, CSR side effects, error/security handling, clock/reset assumptions, user-facing parameters, and datapath arithmetic.
- When a block maps directly to an SSOT feature, name that feature or behavior in the comment so reviewers can trace the RTL back to the spec.
- For shift-add arithmetic, explain the exact equivalence in one short comment, including any rounding, truncation, signedness, or saturation choice that matters.
- Avoid noisy comments that only say what the next token already says, such as "assign output", "reset register", or "case statement".
- Keep comments accurate and local; update or remove stale comments during repair.

## Reset Convention

- Active-low async reset (default): `always @(posedge clk or negedge rst_n)`
- Active-high sync reset: `always @(posedge clk)` with `if (rst)`
- Pick ONE per project — document in spec.
