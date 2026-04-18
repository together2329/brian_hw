// -----------------------------------------------------------------------------
// tb_counter.sv — Self-checking testbench for counter.sv
//   Verifies: async reset, reset recovery (hold), count enable, hold when
//   disabled, parallel load, and rollover wrap-around.
// -----------------------------------------------------------------------------

`timescale 1ns/1ps

module tb_counter;

    // ------------------------------------------------------------------ params
    localparam int WIDTH = 128;
    localparam time CLK_PERIOD = 10ns;

    // Width-safe 128-bit constants for stimulus and rollover checks
    localparam logic [WIDTH-1:0] ZERO_VAL      = '0;
    localparam logic [WIDTH-1:0] ONE_VAL       = {{(WIDTH-1){1'b0}}, 1'b1};
    localparam logic [WIDTH-1:0] TWO_VAL       = {{(WIDTH-2){1'b0}}, 2'd2};
    localparam logic [WIDTH-1:0] THREE_VAL     = {{(WIDTH-2){1'b0}}, 2'd3};
    localparam logic [WIDTH-1:0] LOAD_100_VAL  = {{(WIDTH-7){1'b0}}, 7'd100};
    localparam logic [WIDTH-1:0] LOAD_101_VAL  = {{(WIDTH-7){1'b0}}, 7'd101};
    localparam logic [WIDTH-1:0] LOAD_200_VAL  = {{(WIDTH-8){1'b0}}, 8'd200};
    localparam logic [WIDTH-1:0] MAX_VAL       = {WIDTH{1'b1}};
    localparam logic [WIDTH-1:0] MAX_MINUS_1   = MAX_VAL - ONE_VAL;

    // -------------------------------------------------------------- signals
    logic             clk;
    logic             rst_n;
    logic             en;
    logic             load;
    logic [WIDTH-1:0] d;
    logic [WIDTH-1:0] q;

    // --------------------------------------------------------------- DUT
    counter #(
        .WIDTH(WIDTH)
    ) u_dut (
        .clk   (clk),
        .rst_n (rst_n),
        .en    (en),
        .load  (load),
        .d     (d),
        .q     (q)
    );

    // ----------------------------------------------------------- clock gen
    initial clk = 0;
    always #(CLK_PERIOD/2) clk = ~clk;

    // -------------------------------------------------------- test bookkeeping
    int test_count = 0;
    int pass_count = 0;
    int fail_count = 0;

    task automatic check(input string label, input logic [WIDTH-1:0] expected);
        test_count++;
        if (q === expected) begin
            pass_count++;
            $display("  [PASS] %s : q=%0d (expected %0d)", label, q, expected);
        end else begin
            fail_count++;
            $display("  [FAIL] %s : q=%0d (expected %0d)", label, q, expected);
        end
    endtask

    // ----------------------------------------------------------- stimulus
    initial begin
        // Log dump for waveform viewing
        $dumpfile("tb_counter.vcd");
        $dumpvars(0, tb_counter);

        $display("========================================");
        $display("  counter testbench - WIDTH=%0d", WIDTH);
        $display("========================================");

        // --- Initialisation ------------------------------------------------
        en    = 0;
        load  = 0;
        d     = '0;
        rst_n = 1;

        // --- Test 1: Async reset -------------------------------------------
        $display("\n--- Test 1: Async reset ---");
        @(negedge clk);
        rst_n = 0;
        #(1);
        check("async_reset", ZERO_VAL);

        // --- Test 2: Reset recovery / hold without enable -------------------
        $display("\n--- Test 2: Reset recovery (hold at 0) ---");
        @(posedge clk);
        rst_n = 1;
        @(posedge clk);
        check("hold_after_reset", ZERO_VAL);

        // --- Test 3: Count enable - increment each clock -------------------
        $display("\n--- Test 3: Count enable ---");
        en = 1;
        @(posedge clk);
        check("count_to_1", ONE_VAL);

        @(posedge clk);
        check("count_to_2", TWO_VAL);

        @(posedge clk);
        check("count_to_3", THREE_VAL);

        // --- Test 4: Hold when disabled ------------------------------------
        $display("\n--- Test 4: Hold when disabled ---");
        en = 0;
        @(posedge clk);
        check("hold_at_3", THREE_VAL);

        @(posedge clk);
        check("hold_still_at_3", THREE_VAL);

        // --- Test 5: Parallel load -----------------------------------------
        $display("\n--- Test 5: Parallel load ---");
        load = 1;
        d    = LOAD_100_VAL;
        @(posedge clk);
        load = 0;
        #(1);
        check("load_100", LOAD_100_VAL);

        en = 1;
        @(posedge clk);
        check("count_after_load", LOAD_101_VAL);

        // --- Test 6: Load has priority over enable --------------------------
        $display("\n--- Test 6: Load priority over enable ---");
        en   = 1;
        load = 1;
        d    = LOAD_200_VAL;
        @(posedge clk);
        load = 0;
        #(1);
        check("load_over_enable", LOAD_200_VAL);

        // --- Test 7: Rollover - count from MAX_VAL-1 to MAX_VAL, then to 0
        $display("\n--- Test 7: Rollover ---");
        load = 1;
        d    = MAX_MINUS_1;
        @(posedge clk);
        load = 0;
        #(1);
        check("pre_rollover_load", MAX_MINUS_1);

        en = 1;
        @(posedge clk);
        check("at_max", MAX_VAL);

        @(posedge clk);
        check("rollover_to_0", ZERO_VAL);

        // --- Summary -------------------------------------------------------
        $display("\n========================================");
        $display("  SUMMARY: %0d / %0d checks passed", pass_count, test_count);
        if (fail_count == 0)
            $display("  *** ALL TESTS PASSED ***");
        else
            $display("  *** %0d TEST(S) FAILED ***", fail_count);
        $display("========================================");

        $finish;
    end

endmodule
