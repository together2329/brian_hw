# Simulation Debug Rules

## Compile Error → Fix

```
error: Unknown module type: <module>
→ Check include path or add DUT file to iverilog command

error: Port connection error
→ grep_file tb for port names vs DUT port list — fix mismatch

error: syntax error near 'endmodule'
→ Missing semicolon, mismatched begin/end above — scan upward
```

## Runtime Fail → Fix

```
[FAIL] tc_reset: out=ff expected=00
→ Reset value wrong in DUT → check: if(!rst_n) out <= '0;

[FAIL] tc_normal_op: got=0 expected=5
→ Logic error in DUT → trace: what drives out? check always_comb conditions

X in output
→ 1. Check always_comb has default assignment
→ 2. Check always_ff resets all outputs
→ 3. Check TB drives all inputs (no floating Z)
```

## Escalation

```
[SIM ESCALATE] rtl-gen
Signal  : out_data
Expected: 8'h05 after 3 cycles
Got     : 8'hxx (X)
Root    : reset not clearing reg_val in <module>.sv line N
```
