//--------------------------------------------------------------
// Testbench for 8-Bit Synchronous Up-Counter
//--------------------------------------------------------------
`timescale 1ns / 1ps

module counter_tb;

    // Signals
    reg        clk;
    reg        rst;
    wire [7:0] count;

    // Instantiate DUT
    counter uut (
        .clk   (clk),
        .rst   (rst),
        .count (count)
    );

    // Clock generation: 10 ns period (100 MHz)
    initial clk = 0;
    always #5 clk = ~clk;

    // Stimulus
    initial begin
        // Init
        rst = 1;
        #20;

        // Release reset, check count = 0
        rst = 0;
        #10;
        if (count !== 8'd0) $display("FAIL: after reset, count = %0d (expected 0)", count);
        else                $display("PASS: after reset, count = 0");

        // Count up for a few cycles
        #10; // count should be 1
        if (count !== 8'd1) $display("FAIL: count = %0d (expected 1)", count);
        else                $display("PASS: count = 1");

        #10; // count should be 2
        if (count !== 8'd2) $display("FAIL: count = %0d (expected 2)", count);
        else                $display("PASS: count = 2");

        // Fast-forward to near wrap-around: count is 2, need 253 more edges
        rst = 1;          // reset to sync known state
        #10;
        rst = 0;
        #10;              // count = 0 after reset release

        repeat (254) @(posedge clk);  // count should now be 254
        #1; // slight offset past edge
        if (count !== 8'd254) $display("FAIL: count = %0d (expected 254)", count);
        else                  $display("PASS: count = 254");

        // Next edge: 254 -> 255
        @(posedge clk); #1;
        if (count !== 8'd255) $display("FAIL: count = %0d (expected 255)", count);
        else                  $display("PASS: count = 255");

        // Next edge: 255 -> 0 (wrap-around)
        @(posedge clk); #1;
        if (count !== 8'd0) $display("FAIL: wrap-around count = %0d (expected 0)", count);
        else                $display("PASS: wrap-around count = 0");

        // Mid-operation reset test
        @(posedge clk); #1;  // count = 1
        rst = 1;
        @(posedge clk); #1;
        if (count !== 8'd0) $display("FAIL: mid-op reset, count = %0d (expected 0)", count);
        else                $display("PASS: mid-op reset, count = 0");

        $display("--- All checks complete ---");
        $finish;
    end

    // Timeout watchdog
    initial begin
        #10000;
        $display("FAIL: simulation timed out");
        $finish;
    end

endmodule
