//------------------------------------------------------------
// Testbench for Simple 8-bit Up Counter
//------------------------------------------------------------
// Verifies:
//   1. Synchronous reset clears count to 0
//   2. Count increments by 1 each clock cycle
//   3. Count wraps around from 255 to 0
//------------------------------------------------------------

`timescale 1ns / 1ps

module counter_tb;

    // Signals
    reg         clk;
    reg         rst;
    wire [7:0]  count;

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

        // Wait for count to reach a few values
        #100;

        // Verify count is incrementing (should be ~10 at this point)
        if (count != 8'd10) begin
            $display("FAIL: expected count=10, got count=%0d", count);
        end else begin
            $display("PASS: count=%0d at expected time", count);
        end

        // Fast-forward near wrap-around: jump count to 253
        // We do this by driving reset to re-sync
        // Instead, let's just run long enough — but 256 cycles is a lot.
        // Let's force the counter value by resetting and waiting 253 cycles.
        rst = 1;
        #10 rst = 0;

        // Wait 255 cycles (255 * 10ns = 2550ns)
        #2550;

        // count should be 255 now
        if (count != 8'd255) begin
            $display("FAIL: expected count=255, got count=%0d", count);
        end else begin
            $display("PASS: count=255, about to wrap");
        end

        // Wait one more cycle — should wrap to 0
        #10;
        if (count != 8'd0) begin
            $display("FAIL: expected count=0 (wrap), got count=%0d", count);
        end else begin
            $display("PASS: count wrapped from 255 to 0");
        end

        // A few more cycles to confirm counting resumes
        #30;
        if (count != 8'd3) begin
            $display("FAIL: expected count=3 after wrap, got count=%0d", count);
        end else begin
            $display("PASS: counting resumed after wrap, count=%0d", count);
        end

        $display("--- All tests done ---");
        $finish;
    end

endmodule
