# RTL Development Rules

You are working in an RTL (Register Transfer Level) design environment. Apply the following rules strictly.

## Coding Style

1. **Nonblocking assignments** (`<=`) in always_ff / always @(posedge clk) blocks only
2. **Blocking assignments** (`=`) in always_comb / always @(*) blocks only
3. Never mix blocking and nonblocking in the same always block
4. Use `logic` type for SystemVerilog; use `reg`/`wire` only when targeting pure Verilog-2001
5. Declare all ports explicitly with direction and type

## Synthesis Safety

6. All flip-flops must have a synchronous or asynchronous reset
7. No latches — every combinational output must be driven in every branch
8. No multi-driven nets — one driver per signal
9. Avoid `initial` blocks in synthesizable RTL (use only in testbenches)
10. Use generate blocks for parameterized replication

## Simulation

11. Run simulation after every significant change
12. Check for X-propagation (undefined values) in simulation output
13. Treat any "Warning" from the simulator as a potential bug
14. Use `$display` / `$monitor` sparingly — prefer waveform dumps for debugging

## File Organization

15. One module per file; filename matches module name
16. Interface definitions in separate `_pkg.sv` or `_if.sv` files
17. Testbenches in `tb_<module_name>.sv` files

## Workflow

18. Plan first — define module interface before writing internals
19. Write testbench before or alongside the DUT
20. Lint after writing; simulate after linting; fix in order: errors → warnings → style
