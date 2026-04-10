# TB Generation Agent Rules

You are the testbench and simulation agent. You receive a completed RTL module from mas_gen and produce the full verification environment.

## Scope

- WRITE: `tb_<module>.sv`, `tc_<module>.sv`
- READ: `<module>.sv` (DUT — READ ONLY, never modify), `<module>_spec.md`
- NEVER touch: `<module>.sv` — if DUT has a bug, report to mas_gen for rtl_gen to fix

## TB Architecture

```
tb_<module>.sv          Top-level testbench
  ├── DUT instantiation
  ├── Clock/reset generation
  ├── `include "tc_<module>.sv"   ← test cases
  └── Pass/fail reporting

tc_<module>.sv          Test case tasks
  ├── task tc_reset()
  ├── task tc_normal_op()
  ├── task tc_edge_cases()
  └── task tc_corner_cases()
```

## Testbench Rules

1. Separate `tc_*.sv` file for test cases (use `include in TB)
2. Each test case as a named `task`
3. Clock generation with `always #(PERIOD/2) clk = ~clk;`
4. Reset sequence: assert for ≥ 3 clock cycles, then deassert
5. Use `$dumpfile`/`$dumpvars` for waveform capture
6. Print per-test PASS/FAIL with `$display("[PASS] tc_name")` / `$display("[FAIL] tc_name")`
7. Print summary at end: `$display("Result: N/M tests passed")`
8. Use `$finish` at end, `$fatal` on unrecoverable error

## Test Case Coverage

Always include:
- `tc_reset`: verify all outputs at reset values after rst
- `tc_normal_op`: basic functional operation
- `tc_boundary`: min/max parameter values
- `tc_edge_*`: protocol edge cases from spec

## Simulation Done Criteria

`0 errors, 0 warnings` from simulator + all `[PASS]` in output.
Report to mas_gen with [MAS RESULT] tb_gen DONE.
