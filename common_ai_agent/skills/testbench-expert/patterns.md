# Testbench Patterns

## Basic Structure
```verilog
`timescale 1ns/1ps
module dut_tb;
    reg clk = 0;
    reg reset = 1;
    // DUT instantiation
    dut u_dut (.clk(clk), .reset(reset), ...);
    // Clock
    always #5 clk = ~clk;  // 100MHz
    // Stimulus
    initial begin
        #100 reset = 0;
        // test cases
        #1000 $finish;
    end
endmodule
```

## AXI Testbench
Use tasks for reusable sequences: SEND_WRITE, READ_AND_CHECK.
Include handshake (VALID/READY) and timeout protection.

## Self-Checking Pattern
```verilog
reg [7:0] expected[$];
task write_and_check;
    // push expected, execute, compare
    if (actual !== expected) $error("Mismatch");
endtask
```

## Waveform Dump
```verilog
initial begin $dumpfile("wave.vcd"); $dumpvars(0, dut_tb); end
```
