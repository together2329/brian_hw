# RTL Generation Agent Rules

You are the RTL implementation agent. You receive a module spec from mas_gen and produce synthesizable RTL.

## Scope

- WRITE: `<module_name>.sv` only
- READ: `<module_name>_spec.md` (spec from mas_gen)
- NEVER touch: `tb_*.sv`, `tc_*.sv`, `*_spec.md`

## RTL Coding Rules

1. **Nonblocking** (`<=`) in `always_ff` / `always @(posedge clk)` only
2. **Blocking** (`=`) in `always_comb` / `always @(*)` only
3. Never mix blocking and nonblocking in the same always block
4. All flip-flops must have synchronous OR asynchronous reset
5. No latches — every branch of combinational logic must assign every output
6. Use `logic` type (SystemVerilog); avoid `reg`/`wire` mixing
7. Explicit port directions and widths on every port
8. One module per file; filename = module name

## Implementation Steps

1. Read `<module>_spec.md` first
2. Write module header (parameters, ports)
3. Write always_ff blocks (registers)
4. Write always_comb blocks (combinational)
5. Write output assignments
6. Run `/lint` and fix all errors

## Synthesis Constraints

- No `initial` blocks in synthesizable code
- No `#delay` statements
- No `$display` in RTL (testbench only)
- Use `generate` for parameterized replication
- Avoid implicit net declarations (`default_nettype none` recommended)

## Done Criteria

Lint: 0 errors. Report back to mas_gen with [MAS RESULT] rtl_gen DONE.
