//------------------------------------------------------------
// Testbench for Simple 128-bit Up Counter
//------------------------------------------------------------
// Verifies:
//   1. Synchronous reset clears count to 0
//   2. Count increments by 1 each clock cycle
//   3. Upper bits remain 0 during short counting
//   4. Reset re-sync works correctly
//------------------------------------------------------------
// Note: Full wrap-around test (2^128 cycles) is infeasible.
// Only counting behavior and reset are verified.

`timescale 1ns / 1ps

module counter_tb;

    // Signals
    reg           clk;
    reg           rst;
    wire [127:0]  count;

    // Instantiate DUT
    counter uut (
        .clk   (clk),
        .rst   (rst),
        .count (count)
    );

    // Clock generation: 10ns period (100 MHz)
    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    // Stimulus
    initial begin
        // Init
        rst = 1;

        // Monitor
        $monitor("time=%0t  rst=%b  count=%0d", $time, rst, count);

        // Hold reset for 2 cycles
        #20 rst = 0;

        // Wait for count to reach a few values (10 cycles)
        #100;

        // Check 1: Verify count is incrementing (should be 10)
        if (count != 128'd10) begin
            $display("FAIL: expected count=10, got count=%0d", count);
        end else begin
            $display("PASS: count=%0d at expected time", count);
        end

        // Check 2: Verify upper bits [127:8] are all zero
        if (count[127:8] != 120'd0) begin
            $display("FAIL: upper bits non-zero, count[127:8]=%0d", count[127:8]);
        end else begin
            $display("PASS: upper bits [127:8] are zero");
        end

        // Check 3: Reset re-sync
        rst = 1;
        #10 rst = 0;

        // Wait 5 cycles
        #50;

        // count should be 5 after reset and 5 increments
        if (count != 128'd5) begin
            $display("FAIL: expected count=5 after re-sync, got count=%0d", count);
        end else begin
            $display("PASS: count=%0d after reset re-sync", count);
        end

        // Check 4: Verify upper bits still zero after re-sync
        if (count[127:8] != 120'd0) begin
            $display("FAIL: upper bits non-zero after re-sync, count[127:8]=%0d", count[127:8]);
        end else begin
            $display("PASS: upper bits [127:8] still zero after re-sync");
        end

        $display("--- All tests done ---");
        $finish;
    end

endmodule
