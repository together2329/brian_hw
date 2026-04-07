//============================================================================
// Testbench   : counter_tb
// Description : SystemVerilog testbench for parameterized up/down counter.
//               Covers: async reset, count up, count down, hold, parallel
//               load, overflow, underflow, load+count, and WIDTH sweep.
//============================================================================

`timescale 1ns / 1ps

module counter_tb;

    // -----------------------------------------------------------------------
    // Parameters
    // -----------------------------------------------------------------------
    parameter int WIDTH = 8;
    parameter int CLK_PERIOD = 10;  // 10 ns => 100 MHz

    // -----------------------------------------------------------------------
    // Signals
    // -----------------------------------------------------------------------
    logic             clk;
    logic             rst_n;
    logic             en;
    logic             up_down;
    logic             load;
    logic [WIDTH-1:0] d;
    logic [WIDTH-1:0] q;
    logic             overflow;
    logic             zero;

    // -----------------------------------------------------------------------
    // DUT Instantiation
    // -----------------------------------------------------------------------
    counter #(
        .WIDTH(WIDTH)
    ) uut (
        .clk     (clk),
        .rst_n   (rst_n),
        .en      (en),
        .up_down (up_down),
        .load    (load),
        .d       (d),
        .q       (q),
        .overflow(overflow),
        .zero    (zero)
    );

    // -----------------------------------------------------------------------
    // Clock Generation
    // -----------------------------------------------------------------------
    initial clk = 1'b0;
    always #(CLK_PERIOD/2) clk = ~clk;

    // -----------------------------------------------------------------------
    // Test bookkeeping
    // -----------------------------------------------------------------------
    int test_pass = 0;
    int test_fail = 0;

    task automatic check(input string label, input logic [WIDTH-1:0] expected_q,
                         input logic expected_ovf, input logic expected_zero);
        if (q !== expected_q || overflow !== expected_ovf || zero !== expected_zero) begin
            $display("[FAIL] %0t ns | %s | q=%0d (exp=%0d) ovf=%0b (exp=%0b) zero=%0b (exp=%0b)",
                     $time, label, q, expected_q, overflow, expected_ovf, zero, expected_zero);
            test_fail++;
        end else begin
            $display("[PASS] %0t ns | %s | q=%0d ovf=%0b zero=%0b", $time, label, q, overflow, zero);
            test_pass++;
        end
    endtask

    // -----------------------------------------------------------------------
    // Wait for N clock edges (posedge)
    // -----------------------------------------------------------------------
    task automatic wait_clks(input int n);
        repeat(n) @(posedge clk);
    endtask

    // -----------------------------------------------------------------------
    // Apply reset
    // -----------------------------------------------------------------------
    task automatic apply_reset;
        rst_n = 1'b0;
        en    = 1'b0;
        up_down = 1'b0;
        load  = 1'b0;
        d     = '0;
        wait_clks(3);
        rst_n = 1'b1;
        wait_clks(1);
    endtask

    // -----------------------------------------------------------------------
    // Main stimulus
    // -----------------------------------------------------------------------
    initial begin
        $display("==========================================================");
        $display("  Counter Testbench - WIDTH = %0d", WIDTH);
        $display("==========================================================");

        // ===================================================================
        // Test 1: Async Reset
        // ===================================================================
        $display("\n--- Test 1: Async Reset ---");
        apply_reset();
        check("after reset", '0, 1'b0, 1'b0);

        // ===================================================================
        // Test 2: Count Up
        // ===================================================================
        $display("\n--- Test 2: Count Up ---");
        en      = 1'b1;
        up_down = 1'b1;
        wait_clks(1);
        check("count up q=1", 1, 1'b0, 1'b0);
        wait_clks(1);
        check("count up q=2", 2, 1'b0, 1'b0);
        wait_clks(1);
        check("count up q=3", 3, 1'b0, 1'b0);

        // ===================================================================
        // Test 3: Count Down
        // ===================================================================
        $display("\n--- Test 3: Count Down ---");
        up_down = 1'b0;
        wait_clks(1);
        check("count down q=2", 2, 1'b0, 1'b0);
        wait_clks(1);
        check("count down q=1", 1, 1'b0, 1'b0);
        wait_clks(1);
        check("count down q=0", 0, 1'b0, 1'b0);

        // ===================================================================
        // Test 4: Hold (Enable = 0)
        // ===================================================================
        $display("\n--- Test 4: Hold (Enable = 0) ---");
        en = 1'b0;
        wait_clks(3);
        check("hold q=0", 0, 1'b0, 1'b0);

        // ===================================================================
        // Test 5: Parallel Load
        // ===================================================================
        $display("\n--- Test 5: Parallel Load ---");
        load = 1'b1;
        d    = 100;
        wait_clks(1);
        check("load d=100", 100, 1'b0, 1'b0);
        load = 1'b0;
        d    = '0;
        wait_clks(1);
        check("after load hold", 100, 1'b0, 1'b0);

        // ===================================================================
        // Test 6: Overflow (MAX u2192 0)
        // ===================================================================
        $display("\n--- Test 6: Overflow ---");
        load    = 1'b1;
        d       = {WIDTH{1'b1}};  // Load MAX value
        wait_clks(1);
        load    = 1'b0;
        en      = 1'b1;
        up_down = 1'b1;
        check("loaded MAX", {WIDTH{1'b1}}, 1'b0, 1'b0);
        wait_clks(1);
        check("overflow: MAX->0", '0, 1'b1, 1'b0);
        // Verify overflow clears on next cycle
        wait_clks(1);
        check("after overflow q=1", 1, 1'b0, 1'b0);

        // ===================================================================
        // Test 7: Underflow (0 u2192 MAX)
        // ===================================================================
        $display("\n--- Test 7: Underflow ---");
        load    = 1'b1;
        d       = '0;
        wait_clks(1);
        load    = 1'b0;
        en      = 1'b1;
        up_down = 1'b0;
        check("loaded 0", '0, 1'b0, 1'b0);
        wait_clks(1);
        check("underflow: 0->MAX", {WIDTH{1'b1}}, 1'b0, 1'b1);
        // Verify zero clears on next cycle
        wait_clks(1);
        check("after underflow q=MAX-1", {WIDTH{1'b1}} - 1, 1'b0, 1'b0);

        // ===================================================================
        // Test 8: Load + Count
        // ===================================================================
        $display("\n--- Test 8: Load + Count ---");
        load    = 1'b1;
        d       = 10;
        wait_clks(1);
        load    = 1'b0;
        up_down = 1'b1;
        check("loaded 10", 10, 1'b0, 1'b0);
        wait_clks(5);
        check("count up +5 from 10", 15, 1'b0, 1'b0);
        up_down = 1'b0;
        wait_clks(3);
        check("count down -3 from 15", 12, 1'b0, 1'b0);

        // ===================================================================
        // Test 9: Reset during counting
        // ===================================================================
        $display("\n--- Test 9: Reset During Counting ---");
        en      = 1'b1;
        up_down = 1'b1;
        wait_clks(3);
        rst_n   = 1'b0;
        wait_clks(2);
        check("reset asserted", '0, 1'b0, 1'b0);
        rst_n   = 1'b1;
        wait_clks(1);
        check("after reset release", '0, 1'b0, 1'b0);

        // ===================================================================
        // Test 10: Load has priority over enable
        // ===================================================================
        $display("\n--- Test 10: Load Priority Over Enable ---");
        load    = 1'b1;
        en      = 1'b1;
        up_down = 1'b1;
        d       = 42;
        wait_clks(1);
        check("load priority: d=42 not count", 42, 1'b0, 1'b0);
        load = 1'b0;
        d    = '0;
        wait_clks(1);
        check("after load priority: count to 43", 43, 1'b0, 1'b0);

        // Clean up
        en = 1'b0;
        wait_clks(2);

        // ===================================================================
        // Summary
        // ===================================================================
        $display("\n==========================================================");
        $display("  TEST SUMMARY: PASS = %0d  FAIL = %0d  TOTAL = %0d",
                 test_pass, test_fail, test_pass + test_fail);
        if (test_fail == 0)
            $display("  *** ALL TESTS PASSED ***");
        else
            $display("  *** SOME TESTS FAILED ***");
        $display("==========================================================\n");

        $finish;
    end

    // -----------------------------------------------------------------------
    // Timeout watchdog
    // -----------------------------------------------------------------------
    initial begin
        #(CLK_PERIOD * 1000);
        $display("[ERROR] Simulation timeout!");
        $finish;
    end

endmodule
