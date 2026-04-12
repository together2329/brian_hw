# RTL Coding Rules (rtl-gen)

## Mandatory Patterns

```systemverilog
// FF block — always nonblocking
always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) q <= '0;
    else        q <= d;
end

// Comb block — always blocking
always_comb begin
    out = '0;          // default assignment (prevents latch)
    case (sel)
        2'b00: out = a;
        2'b01: out = b;
        default: out = '0;
    endcase
end
```

## Forbidden Patterns

```systemverilog
// NEVER: mixed blocking/nonblocking
always_ff @(posedge clk) begin
    a = b;    // WRONG — blocking in FF block
    c <= d;
end

// NEVER: latch (missing else)
always_comb begin
    if (en) out = data;  // WRONG — no else → latch
end

// NEVER: initial in RTL
initial begin  // WRONG — not synthesizable
    reg_val = 0;
end
```

## Width Rules

- Explicit width on all constants: `8'h00`, `1'b0`, `'0` (all zeros)
- Check width match in assignments — no implicit truncation
- Use `$clog2(N)` for address width calculation

## Reset Convention

- Active-low async reset: `always_ff @(posedge clk or negedge rst_n)`
- Active-high sync reset: `always_ff @(posedge clk)` with `if (rst)`
- Pick ONE per project — document in spec
