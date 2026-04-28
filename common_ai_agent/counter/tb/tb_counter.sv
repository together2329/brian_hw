`timescale 1ns / 1ps

module tb_counter;

    logic        clk;
    logic        rst_n;
    logic        enable;
    logic [7:0]  count;

    // DUT instantiation
    counter dut (
        .clk    (clk),
        .rst_n  (rst_n),
        .enable (enable),
        .count  (count)
    );

    // 10 ns clock period (100 MHz)
    always #5 clk = ~clk;

    initial begin
        clk    = 0;
        rst_n  = 0;
        enable = 0;

        // Dump VCD
        $dumpfile("sim/tb_counter.vcd");
        $dumpvars(0, tb_counter);

        // ==================================================
        // Test 1: Reset test — count must stay at 0 during reset
        // ==================================================
        $display("\n=== Test 1: Reset Test ===");
        repeat(5) @(posedge clk);
        assert (count === 8'd0) else $error("Reset failed: count = %0d", count);
        $display("  Reset test PASS");

        // Release reset
        rst_n = 1;
        repeat(2) @(posedge clk);

        // ==================================================
        // Test 2: Enable gating — count must NOT increment when enable=0
        // ==================================================
        $display("\n=== Test 2: Enable Gating Test ===");
        enable = 0;
        repeat(5) @(posedge clk);
        assert (count === 8'd0) else $error("Gating failed: count = %0d (expected 0)", count);
        $display("  Enable gating test PASS");

        // ==================================================
        // Test 3: Count up with enable=1
        // ==================================================
        $display("\n=== Test 3: Count Up Test ===");
        enable = 1;
        repeat(10) @(posedge clk);
        assert (count === 8'd10) else $error("Count up failed: count = %0d (expected 10)", count);
        $display("  Count up test PASS");

        // ==================================================
        // Test 4: Wrap test — count from 255 back to 0
        // ==================================================
        $display("\n=== Test 4: Wrap Test ===");
        // Force count near max, then release so it can increment
        force dut.count = 8'd253;
        @(posedge clk);
        release dut.count;
        @(posedge clk);  // count increments 253->254
        @(posedge clk);  // count increments 254->255
        assert (count === 8'd255) else $error("Wrap setup failed: count = %0d (expected 255)", count);
        @(posedge clk);  // count wraps 255->0
        assert (count === 8'd0) else $error("Wrap failed: count = %0d (expected 0)", count);
        $display("  Wrap test PASS");

        // ==================================================
        // Test 5: Reset again mid-operation
        // ==================================================
        $display("\n=== Test 5: Mid-op Reset Test ===");
        repeat(5) @(posedge clk);
        rst_n = 0;
        repeat(3) @(posedge clk);
        assert (count === 8'd0) else $error("Mid-op reset failed: count = %0d", count);
        rst_n = 1;
        $display("  Mid-op reset test PASS");

        $display("\n========================================");
        $display("=== ALL TESTS COMPLETE ===");
        $display("========================================\n");

        #20 $finish;
    end

endmodule
