# RTL Coding Rules (rtl-gen)

**Default dialect: Verilog-2001 (IEEE 1364)** — `.v` files, `wire`/`reg`, `always @(…)` blocks. SystemVerilog-2012 is reachable via `RTL_DIALECT=systemverilog_2012` (`.sv`, `logic`, `always_ff`/`always_comb`). Project convention applies to BOTH dialects.

## Always-banned (both dialects, project convention)

| Banned construct | Use instead |
|---|---|
| `package` / `endpackage` / `import …::*` | A `localparam` block at the top of the consuming module. Replicate per-module if shared. |
| `interface` / `modport` | Plain module ports. |
| `assert` / `assume` / `cover` properties | Move to formal-only files outside the synthesizable RTL. |
| `initial` blocks (in synthesizable RTL) | Sim-only — keep out of `<ip>/rtl/`. |

## Verilog-2001 mode (default)

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

### Banned in Verilog-2001 mode (additional to always-banned)

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

## SystemVerilog-2012 mode (only when `RTL_DIALECT=systemverilog_2012`)

When this mode is active, you MAY use:
- `logic` instead of `wire`/`reg`
- `always_ff` / `always_comb` blocks
- `enum logic [N-1:0] { IDLE, RUN, … }` for state encoding
- `typedef` for local type aliases
- `'0` / `'1` literals
- `.sv` file extension

You MAY NOT use (always-banned list still applies):
- `package` / `endpackage` / `import`
- `interface` / `modport`
- `assert` / `cover` properties (in synthesizable RTL)
- `initial` (in synthesizable RTL)

## Width Rules (both dialects)

- Explicit width on all constants: `8'h00`, `1'b0`. In V2K use `{N{1'b0}}` for all-zeros (no `'0`).
- Check width match in assignments — no implicit truncation.
- Use `$clog2(N)` for address-width calculation.

## Reset Convention (both dialects)

- Active-low async reset (default): `always @(posedge clk or negedge rst_n)` (V2K) / `always_ff @(posedge clk or negedge rst_n)` (SV)
- Active-high sync reset: `always @(posedge clk)` (V2K) / `always_ff @(posedge clk)` (SV) with `if (rst)`
- Pick ONE per project — document in spec.
