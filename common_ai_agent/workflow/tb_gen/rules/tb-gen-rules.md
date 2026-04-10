# TB Generation Rules

## File Structure Template

```systemverilog
// tb_<module>.sv
`timescale 1ns/1ps
`include "tc_<module>.sv"

module tb_<module>;
    // Parameters
    parameter CLK_PERIOD = 10;

    // DUT signals
    logic clk, rst_n;
    logic [W-1:0] in_data;
    logic [W-1:0] out_data;

    // DUT instance
    <module> #(.PARAM(VAL)) dut (
        .clk(clk), .rst_n(rst_n),
        .in_data(in_data),
        .out_data(out_data)
    );

    // Clock
    initial clk = 0;
    always #(CLK_PERIOD/2) clk = ~clk;

    // Waveform dump
    initial begin
        $dumpfile("<module>_wave.vcd");
        $dumpvars(0, tb_<module>);
    end

    // Test sequence
    integer pass_cnt = 0, fail_cnt = 0;
    initial begin
        tc_reset(clk, rst_n, pass_cnt, fail_cnt);
        tc_normal_op(clk, rst_n, in_data, out_data, pass_cnt, fail_cnt);
        tc_edge_cases(clk, rst_n, in_data, out_data, pass_cnt, fail_cnt);
        $display("Result: %0d/%0d tests passed", pass_cnt, pass_cnt+fail_cnt);
        if (fail_cnt == 0) $display("0 errors, 0 warnings");
        $finish;
    end
endmodule
```

```systemverilog
// tc_<module>.sv — test case tasks
task automatic tc_reset(
    ref logic clk, rst_n,
    ref integer pass_cnt, fail_cnt
);
    rst_n = 0;
    repeat(3) @(posedge clk);
    rst_n = 1;
    @(posedge clk);
    // Assert expected reset values
    if (out_data === '0) begin
        $display("[PASS] tc_reset"); pass_cnt++;
    end else begin
        $display("[FAIL] tc_reset: out_data=%h (expected 0)", out_data); fail_cnt++;
    end
endtask
```

## Escalation Protocol

If simulation fails due to suspected DUT bug:
```
[MAS ESCALATE] → rtl_gen
Bug     : <description>
Signal  : <signal_name>
Expected: <value>
Got     : <value>
TB line : <tc_*.sv line number>
```
