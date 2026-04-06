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

    // Stimulus — all sampling done @(posedge clk) + #1 for correct sync
    initial begin
        // Assert reset, verify count = 0
        rst = 1;
        @(posedge clk); #1;
        if (count !== 8'd0) $display("FAIL: during reset, count = %0d (expected 0)", count);
        else                $display("PASS: during reset, count = 0");

        // Release reset between edges
        rst = 0;

        // First posedge after reset release: 0 → 1
        @(posedge clk); #1;
        if (count !== 8'd1) $display("FAIL: count = %0d (expected 1)", count);
        else                $display("PASS: count = 1");

        // Second posedge: 1 → 2
        @(posedge clk); #1;
        if (count !== 8'd2) $display("FAIL: count = %0d (expected 2)", count);
        else                $display("PASS: count = 2");

        // Third posedge: 2 → 3
        @(posedge clk); #1;
        if (count !== 8'd3) $display("FAIL: count = %0d (expected 3)", count);
        else                $display("PASS: count = 3");

        // Re-sync: reset to get a known starting point for wrap-around test
        rst = 1;
        @(posedge clk); #1;  // count = 0
        rst = 0;

        // count = 0; after N posedges count = N; 254 edges → count = 254
        repeat (254) @(posedge clk);
        #1;
        if (count !== 8'd254) $display("FAIL: count = %0d (expected 254)", count);
        else                  $display("PASS: count = 254");

        // 254 → 255
        @(posedge clk); #1;
        if (count !== 8'd255) $display("FAIL: count = %0d (expected 255)", count);
        else                  $display("PASS: count = 255");

        // 255 → 0 (wrap-around)
        @(posedge clk); #1;
        if (count !== 8'd0) $display("FAIL: wrap-around count = %0d (expected 0)", count);
        else                $display("PASS: wrap-around count = 0");

        // Verify count continues after wrap: 0 → 1
        @(posedge clk); #1;
        if (count !== 8'd1) $display("FAIL: post-wrap count = %0d (expected 1)", count);
        else                $display("PASS: post-wrap count = 1");

        // Mid-operation reset test
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
