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

## Clock-Domain Synchronization Rule

Every TB input drive, output monitor, checker, and scoreboard sample must be synchronized to the signal's declared clock domain from SSOT (`io_list.clock_domains`, `cycle_model.clock`, or the RTL contract).

- Drive DUT inputs only after the corresponding clock domain's active edge, or in an SSOT/protocol-defined setup window for the next active edge. Do not free-run input changes on unrelated edges, arbitrary delays, or wall-clock time.
- Sample DUT outputs only after the corresponding active clock edge and the simulator read-only/sample phase required for stable observations.
- For multi-clock IPs, bind every input and output to its declared clock domain. Cross-domain signals require an SSOT-declared CDC or handshake rule; if it is missing, report `[SSOT TBD REPORT] -> ssot-gen` instead of guessing.

## Layered Transaction TB Rule

For any non-trivial protocol, pipeline, memory, bus, accelerator, interrupt, backpressure, multi-beat, or multi-clock IP, generate a layered transaction testbench instead of a flat pin-poke script.

- Define transaction models from SSOT scenario fields, payloads, addresses, channels, IDs, side effects, and expected response metadata.
- Generate scenario sequences that emit transactions, not direct DUT pin writes, except for reset/default or explicitly trivial combinational/CSR smoke checks.
- Implement clock-bound drivers and monitors for every declared clock domain. Drivers translate transactions to DUT pins; monitors translate sampled DUT pins back to observed transactions.
- Implement a latency-aware scoreboard with pending queues or match tables keyed by SSOT ordering, response ID, channel, and multi-beat packet rules.
- Enqueue expected transactions at the SSOT-defined accept/sample point and compare only when `cycle_model` says the response is observable. Same-cycle comparisons are forbidden unless SSOT declares the output combinational in the same cycle.
- If SSOT lacks the latency, handshake, ordering, response matching, or CDC facts needed to build that structure, report `[SSOT TBD REPORT] -> ssot-gen` instead of guessing.

## Escalation Protocol

If simulation fails due to suspected DUT bug:
```
[MAS ESCALATE] → rtl-gen
Bug     : <description>
Signal  : <signal_name>
Expected: <value>
Got     : <value>
TB line : <tc_*.sv line number>
```
