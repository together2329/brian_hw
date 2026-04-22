// ============================================================================
// Testbench: tb_counter
// Description: Self-checking testbench for parameterized up/down counter.
//              DUT instantiated with WIDTH=4 (max=15) for easy overflow testing.
//              Covers: reset, up-count, down-count, load, overflow, underflow,
//              priority, simultaneous up/down, and hold.
// ============================================================================

`timescale 1ns / 1ps

module tb_counter;

    // -------------------------------------------------------------------------
    // Parameters
    // -------------------------------------------------------------------------
    parameter int WIDTH = 4;

    // -------------------------------------------------------------------------
    // Signals
    // -------------------------------------------------------------------------
    logic             clk;
    logic             rst_n;
    logic             up_en;
    logic             down_en;
    logic             load_en;
    logic [WIDTH-1:0] load_data;
    logic [WIDTH-1:0] count;
    logic             overflow;
    logic             underflow;

    // -------------------------------------------------------------------------
    // Scoreboard
    // -------------------------------------------------------------------------
    int pass_count = 0;
    int fail_count = 0;

    // -------------------------------------------------------------------------
    // Clock generation — 10 ns period (5 ns half-period)
    // -------------------------------------------------------------------------
    initial begin
        clk = 1'b0;
        forever #5 clk = ~clk;
    end

    // -------------------------------------------------------------------------
    // DUT instantiation
    // -------------------------------------------------------------------------
    counter #(
        .WIDTH(WIDTH)
    ) dut (
        .clk       (clk),
        .rst_n     (rst_n),
        .up_en     (up_en),
        .down_en   (down_en),
        .load_en   (load_en),
        .load_data (load_data),
        .count     (count),
        .overflow  (overflow),
        .underflow (underflow)
    );

    // -------------------------------------------------------------------------
    // Helper task: wait one clock edge (positive)
    // -------------------------------------------------------------------------
    task tick;
        begin
            @(posedge clk);
            #1; // Small delay to sample after outputs settle
        end
    endtask

    // -------------------------------------------------------------------------
    // Helper task: check a signal against expected value
    // -------------------------------------------------------------------------
    task check(input string label, input logic [WIDTH-1:0] expected_count,
               input logic expected_overflow, input logic expected_underflow);
        begin
            if (count === expected_count &&
                overflow === expected_overflow &&
                underflow === expected_underflow) begin
                pass_count++;
            end else begin
                fail_count++;
                $display("  [FAIL] %-35s | count=%0d (exp=%0d) ovf=%0b (exp=%0b) unf=%0b (exp=%0b)",
                         label, count, expected_count,
                         overflow, expected_overflow,
                         underflow, expected_underflow);
            end
        end
    endtask

    // -------------------------------------------------------------------------
    // Helper: clear all control inputs
    // -------------------------------------------------------------------------
    task clear_inputs;
        begin
            up_en    = 1'b0;
            down_en  = 1'b0;
            load_en  = 1'b0;
            load_data = '0;
        end
    endtask

    // -------------------------------------------------------------------------
    // Main stimulus
    // -------------------------------------------------------------------------
    initial begin
        $display("========================================");
        $display("  Counter Testbench — WIDTH=%0d", WIDTH);
        $display("========================================");

        // --- Initialize ---
        clear_inputs();
        rst_n = 1'b0;

        // =====================================================================
        // Test 1: Reset verification
        // =====================================================================
        $display("\n--- Test 1: Reset ---");
        tick();
        check("After reset (rst_n=0)", '0, 1'b0, 1'b0);

        // Release reset
        rst_n = 1'b1;
        tick();
        check("After reset released", '0, 1'b0, 1'b0);

        // =====================================================================
        // Test 2: Up-count sequence (0 → 1 → 2 → 3)
        // =====================================================================
        $display("\n--- Test 2: Up-count ---");
        clear_inputs();
        up_en = 1'b1;
        tick(); check("Up: 0 → 1", 4'd1, 1'b0, 1'b0);
        tick(); check("Up: 1 → 2", 4'd2, 1'b0, 1'b0);
        tick(); check("Up: 2 → 3", 4'd3, 1'b0, 1'b0);
        tick(); check("Up: 3 → 4", 4'd4, 1'b0, 1'b0);

        // =====================================================================
        // Test 3: Down-count sequence (4 → 3 → 2 → 1)
        // =====================================================================
        $display("\n--- Test 3: Down-count ---");
        clear_inputs();
        down_en = 1'b1;
        tick(); check("Down: 4 → 3", 4'd3, 1'b0, 1'b0);
        tick(); check("Down: 3 → 2", 4'd2, 1'b0, 1'b0);
        tick(); check("Down: 2 → 1", 4'd1, 1'b0, 1'b0);
        tick(); check("Down: 1 → 0", 4'd0, 1'b0, 1'b0);

        // =====================================================================
        // Test 4: Load functionality
        // =====================================================================
        $display("\n--- Test 4: Load ---");
        clear_inputs();
        load_en  = 1'b1;
        load_data = 4'd10;
        tick(); check("Load 10", 4'd10, 1'b0, 1'b0);

        // Load another value
        load_data = 4'd7;
        tick(); check("Load 7", 4'd7, 1'b0, 1'b0);
        clear_inputs();

        // =====================================================================
        // Test 5: Overflow wrap-around (count up to max, then wrap to 0)
        // =====================================================================
        $display("\n--- Test 5: Overflow wrap ---");
        clear_inputs();
        // Load max value - 2 = 13
        load_en   = 1'b1;
        load_data = 4'd13;
        tick(); check("Load 13", 4'd13, 1'b0, 1'b0);

        // Count up: 13 → 14 → 15 → 0 (overflow)
        clear_inputs();
        up_en = 1'b1;
        tick(); check("Up: 13 → 14", 4'd14, 1'b0, 1'b0);
        tick(); check("Up: 14 → 15", 4'd15, 1'b0, 1'b0);
        tick(); check("Up: 15 → 0  (overflow)", 4'd0, 1'b1, 1'b0);

        // Overflow flag should clear on next cycle
        tick(); check("After overflow, flag clears", 4'd1, 1'b0, 1'b0);

        // =====================================================================
        // Test 6: Underflow wrap-around (count down from 0, wrap to max)
        // =====================================================================
        $display("\n--- Test 6: Underflow wrap ---");
        clear_inputs();
        // Load 0
        load_en   = 1'b1;
        load_data = 4'd0;
        tick(); check("Load 0", 4'd0, 1'b0, 1'b0);

        // Count down: 0 → 15 (underflow)
        clear_inputs();
        down_en = 1'b1;
        tick(); check("Down: 0 → 15 (underflow)", 4'd15, 1'b0, 1'b1);

        // Underflow flag should clear on next cycle
        tick(); check("After underflow, flag clears", 4'd14, 1'b0, 1'b0);

        // =====================================================================
        // Test 7: Priority test — load > up > down
        // =====================================================================
        $display("\n--- Test 7: Priority (load > up > down) ---");
        // Load to known state
        clear_inputs();
        load_en   = 1'b1;
        load_data = 4'd5;
        tick(); check("Setup: Load 5", 4'd5, 1'b0, 1'b0);

        // All enables active: load should win
        load_en   = 1'b1;
        load_data = 4'd12;
        up_en     = 1'b1;
        down_en   = 1'b1;
        tick(); check("load+up+down: load wins", 4'd12, 1'b0, 1'b0);

        // =====================================================================
        // Test 8: Up/down simultaneous (up wins, no down)
        // =====================================================================
        $display("\n--- Test 8: Up+down → up wins ---");
        clear_inputs();
        // Load known value
        load_en   = 1'b1;
        load_data = 4'd8;
        tick(); check("Setup: Load 8", 4'd8, 1'b0, 1'b0);

        // Up and down both asserted: up should win
        clear_inputs();
        up_en   = 1'b1;
        down_en = 1'b1;
        tick(); check("Up+down: up wins (8→9)", 4'd9, 1'b0, 1'b0);

        // =====================================================================
        // Test 9: Hold — no enable, count should not change
        // =====================================================================
        $display("\n--- Test 9: Hold ---");
        clear_inputs();
        tick(); check("Hold: 9 → 9", 4'd9, 1'b0, 1'b0);
        tick(); check("Hold: 9 → 9 (2nd cycle)", 4'd9, 1'b0, 1'b0);

        // =====================================================================
        // Summary
        // =====================================================================
        $display("\n========================================");
        $display("  Simulation Complete");
        $display("  PASS : %0d", pass_count);
        $display("  FAIL : %0d", fail_count);
        $display("  Total: %0d", pass_count + fail_count);
        $display("========================================");

        if (fail_count == 0)
            $display("  *** ALL TESTS PASSED ***");
        else
            $display("  *** SOME TESTS FAILED ***");

        $display("========================================");
        $finish;
    end

endmodule
