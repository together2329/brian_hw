//-----------------------------------------------------------------------------
// Testbench: counter_tb
// Description: SystemVerilog testbench for parameterizable counter module.
//              Covers: reset, count up, count down, overflow, underflow,
//              parallel load, enable/disable, and hold functionality.
//
// Usage (with Icarus Verilog):
//   iverilog -g2012 -o counter_tb rtl/counter.v tb/counter_tb.sv
//   vvp counter_tb
//-----------------------------------------------------------------------------

`timescale 1ns / 1ps

module counter_tb;

    // -------------------------------------------------------------------------
    // Parameters
    // -------------------------------------------------------------------------
    parameter WIDTH = 8;
    parameter CLK_PERIOD = 10;  // 10ns => 100 MHz

    // -------------------------------------------------------------------------
    // Signals
    // -------------------------------------------------------------------------
    logic             clk;
    logic             rst_n;
    logic             en;
    logic             up_down;
    logic             load;
    logic [WIDTH-1:0] data_in;
    logic [WIDTH-1:0] count;
    logic             overflow;
    logic             underflow;

    // -------------------------------------------------------------------------
    // DUT Instantiation
    // -------------------------------------------------------------------------
    counter #(
        .WIDTH(WIDTH)
    ) dut (
        .clk       (clk),
        .rst_n     (rst_n),
        .en        (en),
        .up_down   (up_down),
        .load      (load),
        .data_in   (data_in),
        .count     (count),
        .overflow  (overflow),
        .underflow (underflow)
    );

    // -------------------------------------------------------------------------
    // Clock Generation
    // -------------------------------------------------------------------------
    initial begin
        clk = 1'b0;
        forever #(CLK_PERIOD / 2) clk = ~clk;
    end

    // -------------------------------------------------------------------------
    // Test Scoreboard
    // -------------------------------------------------------------------------
    int pass_count = 0;
    int fail_count = 0;

    task automatic check(input string test_name, input logic [WIDTH-1:0] expected_count,
                         input logic expected_overflow, input logic expected_underflow);
        if (count !== expected_count || overflow !== expected_overflow || underflow !== expected_underflow) begin
            $display("  [FAIL] %0t | %s | count=%0d (exp=%0d) ovf=%0b (exp=%0b) udf=%0b (exp=%0b)",
                     $time, test_name, count, expected_count, overflow, expected_overflow,
                     underflow, expected_underflow);
            fail_count++;
        end else begin
            $display("  [PASS] %0t | %s | count=%0d ovf=%0b udf=%0b",
                     $time, test_name, count, overflow, underflow);
            pass_count++;
        end
    endtask

    // -------------------------------------------------------------------------
    // Helper Tasks
    // -------------------------------------------------------------------------
    task automatic apply_reset();
        rst_n = 1'b0;
        en    = 1'b0;
        load  = 1'b0;
        up_down = 1'b0;
        data_in = '0;
        @(posedge clk);
        @(negedge clk);
        rst_n = 1'b1;
        $display("--- Reset released at %0t ---", $time);
    endtask

    task automatic tick(input int n = 1);
        repeat(n) @(posedge clk);
        #1; // Small delay to let outputs settle after clock edge
    endtask

    // -------------------------------------------------------------------------
    // Main Stimulus
    // -------------------------------------------------------------------------
    initial begin
        $display("=========================================================");
        $display("  Counter Module Testbench  (WIDTH=%0d)", WIDTH);
        $display("=========================================================");

        // Initialize
        clk     = 1'b0;
        rst_n   = 1'b0;
        en      = 1'b0;
        load    = 1'b0;
        up_down = 1'b0;
        data_in = '0;

        // =====================================================================
        // TEST 1: Reset behavior
        // =====================================================================
        $display("\n--- TEST 1: Reset ---");
        apply_reset();
        tick(1);
        check("after reset", '0, 1'b0, 1'b0);

        // =====================================================================
        // TEST 2: Count up (0 -> 5)
        // =====================================================================
        $display("\n--- TEST 2: Count Up 0->5 ---");
        en      = 1'b1;
        up_down = 1'b1;
        tick(1);
        check("count=1", 1, 1'b0, 1'b0);
        tick(1);
        check("count=2", 2, 1'b0, 1'b0);
        tick(1);
        check("count=3", 3, 1'b0, 1'b0);
        tick(1);
        check("count=4", 4, 1'b0, 1'b0);
        tick(1);
        check("count=5", 5, 1'b0, 1'b0);

        // =====================================================================
        // TEST 3: Count down (5 -> 2)
        // =====================================================================
        $display("\n--- TEST 3: Count Down 5->2 ---");
        up_down = 1'b0;
        tick(1);
        check("count=4", 4, 1'b0, 1'b0);
        tick(1);
        check("count=3", 3, 1'b0, 1'b0);
        tick(1);
        check("count=2", 2, 1'b0, 1'b0);

        // =====================================================================
        // TEST 4: Disable — hold value
        // =====================================================================
        $display("\n--- TEST 4: Enable OFF (hold) ---");
        en = 1'b0;
        tick(3);
        check("hold count=2", 2, 1'b0, 1'b0);

        // =====================================================================
        // TEST 5: Parallel load
        // =====================================================================
        $display("\n--- TEST 5: Parallel Load ---");
        load    = 1'b1;
        data_in = 8'hAA;
        tick(1);
        check("loaded 0xAA", 8'hAA, 1'b0, 1'b0);
        load = 1'b0;
        data_in = '0;
        tick(1);
        check("after load hold", 8'hAA, 1'b0, 1'b0);

        // =====================================================================
        // TEST 6: Load overrides count enable
        // =====================================================================
        $display("\n--- TEST 6: Load overrides Enable ---");
        en      = 1'b1;
        up_down = 1'b1;
        load    = 1'b1;
        data_in = 8'h10;
        tick(1);
        check("load wins over en", 8'h10, 1'b0, 1'b0);
        load    = 1'b0;
        data_in = '0;

        // =====================================================================
        // TEST 7: Overflow detection
        // =====================================================================
        $display("\n--- TEST 7: Overflow ---");
        // Load max value
        load    = 1'b1;
        data_in = {WIDTH{1'b1}}; // 0xFF
        tick(1);
        check("loaded MAX", {WIDTH{1'b1}}, 1'b0, 1'b0);
        load = 1'b0;
        // Next count should wrap to 0 and assert overflow
        tick(1);
        check("overflow wrap", '0, 1'b1, 1'b0);
        // Overflow should clear on next cycle
        tick(1);
        check("overflow cleared", 1, 1'b0, 1'b0);

        // =====================================================================
        // TEST 8: Underflow detection
        // =====================================================================
        $display("\n--- TEST 8: Underflow ---");
        up_down = 1'b0;
        // Load zero
        load    = 1'b1;
        data_in = '0;
        tick(1);
        check("loaded ZERO", '0, 1'b0, 1'b0);
        load = 1'b0;
        // Next count should wrap to MAX and assert underflow
        tick(1);
        check("underflow wrap", {WIDTH{1'b1}}, 1'b0, 1'b1);
        // Underflow should clear on next cycle
        tick(1);
        check("underflow cleared", {WIDTH{1'b1}} - 1'b1, 1'b0, 1'b0);

        // =====================================================================
        // TEST 9: Reset during operation
        // =====================================================================
        $display("\n--- TEST 9: Reset during operation ---");
        en      = 1'b1;
        up_down = 1'b1;
        tick(2);
        $display("  count before reset = %0d", count);
        rst_n = 1'b0;
        tick(1);
        check("reset asserted", '0, 1'b0, 1'b0);
        rst_n = 1'b1;
        tick(1);
        check("reset released", 1, 1'b0, 1'b0);

        // =====================================================================
        // TEST 10: Multi-cycle continuous count up
        // =====================================================================
        $display("\n--- TEST 10: Continuous count up (10 cycles) ---");
        apply_reset();
        en      = 1'b1;
        up_down = 1'b1;
        tick(10);
        check("count=10", 10, 1'b0, 1'b0);

        // =====================================================================
        // Final Summary
        // =====================================================================
        en   = 1'b0;
        tick(2);
        $display("\n=========================================================");
        $display("  TEST SUMMARY: %0d PASSED, %0d FAILED", pass_count, fail_count);
        if (fail_count == 0)
            $display("  *** ALL TESTS PASSED ***");
        else
            $display("  *** SOME TESTS FAILED ***");
        $display("=========================================================");

        $finish;
    end

    // -------------------------------------------------------------------------
    // Timeout watchdog
    // -------------------------------------------------------------------------
    initial begin
        #10000;
        $display("\n[ERROR] Simulation timeout at %0t!", $time);
        $finish;
    end

    // -------------------------------------------------------------------------
    // Waveform dump (for debugging)
    // -------------------------------------------------------------------------
    initial begin
        $dumpfile("counter_tb.vcd");
        $dumpvars(0, counter_tb);
    end

endmodule
