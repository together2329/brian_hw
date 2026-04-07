//----------------------------------------------------------------------------
// Testbench:    tb_counter.sv
// Description:  Self-checking SystemVerilog testbench for the parametric
//               up/down counter. Uses task-based stimulus with a scoreboard
//               that tracks expected vs actual count and overflow values.
//
// Test Cases:
//   TC1 - Async reset verification
//   TC2 - Count up (0 to max)
//   TC3 - Count down (max to 0)
//   TC4 - Enable/disable control
//   TC5 - Up/down direction switching mid-count
//   TC6 - Parallel load
//   TC7 - Overflow / underflow detection
//   TC8 - Rollover (wrap-around) up and down
//   TC9 - Back-to-back load then count
//----------------------------------------------------------------------------

`timescale 1ns / 1ps

module tb_counter;

    //--------------------------------------------------------------------------
    // Parameters
    //--------------------------------------------------------------------------
    parameter int WIDTH = 8;
    parameter int CLK_PERIOD = 10;  // 10 ns u2192 100 MHz

    // Derived constants
    localparam [WIDTH-1:0] MAX_VAL = {WIDTH{1'b1}};
    localparam [WIDTH-1:0] MIN_VAL = {WIDTH{1'b0}};

    //--------------------------------------------------------------------------
    // Signals
    //--------------------------------------------------------------------------
    logic                 clk;
    logic                 rst_n;
    logic                 en;
    logic                 up_dn;
    logic                 load;
    logic  [WIDTH-1:0]   din;
    wire  [WIDTH-1:0]    count;
    wire                  overflow;

    //--------------------------------------------------------------------------
    // Scoreboard variables
    //--------------------------------------------------------------------------
    int                   pass_count = 0;
    int                   fail_count = 0;
    int                   test_num   = 0;

    //--------------------------------------------------------------------------
    // DUT instantiation
    //--------------------------------------------------------------------------
    counter #(
        .WIDTH(WIDTH)
    ) uut (
        .clk      (clk),
        .rst_n    (rst_n),
        .en       (en),
        .up_dn    (up_dn),
        .load     (load),
        .din      (din),
        .count    (count),
        .overflow (overflow)
    );

    //--------------------------------------------------------------------------
    // Clock generation
    //--------------------------------------------------------------------------
    initial begin
        clk = 1'b0;
        forever #(CLK_PERIOD/2) clk = ~clk;
    end

    //--------------------------------------------------------------------------
    // Helper tasks
    //--------------------------------------------------------------------------

    // Apply async reset for 3 clock cycles
    task apply_reset;
        begin
            rst_n = 1'b0;
            #(CLK_PERIOD * 3);
            rst_n = 1'b1;
            #(CLK_PERIOD);
        end
    endtask

    // Wait N clock cycles (rising edge aligned)
    task wait_cycles(input int n);
        begin
            repeat (n) @(posedge clk);
            #1; // small delay to sample after outputs settle
        end
    endtask

    // Apply inputs and advance one clock cycle
    task apply_inputs(input logic i_en, input logic i_up_dn,
                      input logic i_load, input logic [WIDTH-1:0] i_din);
        begin
            @(negedge clk);
            en    = i_en;
            up_dn = i_up_dn;
            load  = i_load;
            din   = i_din;
        end
    endtask

    // Single-step check: compare actual count and overflow against expected
    task check(input string       tc_name,
               input logic [WIDTH-1:0] expected_count,
               input logic       expected_overflow);
        begin
            if (count !== expected_count || overflow !== expected_overflow) begin
                $display("[FAIL] %s: count=%0d (exp=%0d), overflow=%0b (exp=%0b) @ time=%0t",
                         tc_name, count, expected_count, overflow, expected_overflow, $time);
                fail_count++;
            end else begin
                $display("[PASS] %s: count=%0d, overflow=%0b @ time=%0t",
                         tc_name, count, overflow, $time);
                pass_count++;
            end
        end
    endtask

    // Print test header
    task test_header(input int    tc_id,
                     input string tc_desc);
        begin
            test_num++;
            $display("");
            $display("=========================================================");
            $display("  TC%0d: %s", tc_id, tc_desc);
            $display("=========================================================");
        end
    endtask

    //--------------------------------------------------------------------------
    // Main stimulus
    //--------------------------------------------------------------------------
    initial begin
        // Initialize all inputs
        clk   = 1'b0;
        rst_n = 1'b1;
        en    = 1'b0;
        up_dn = 1'b0;
        load  = 1'b0;
        din   = '0;

        $display("=========================================================");
        $display("  Counter Testbench - WIDTH=%0d, MAX_VAL=%0d", WIDTH, MAX_VAL);
        $display("=========================================================");

        //----------------------------------------------------------------------
        // TC1: Async reset verification
        //----------------------------------------------------------------------
        test_header(1, "Async reset verification");
        // Drive some values first
        apply_inputs(1'b1, 1'b1, 1'b0, '0);
        wait_cycles(5);
        // Apply reset
        apply_reset();
        check("TC1_after_reset", MIN_VAL, 1'b0);

        //----------------------------------------------------------------------
        // TC2: Count up from 0 to MAX_VAL
        //----------------------------------------------------------------------
        test_header(2, "Count up (0 to MAX_VAL)");
        apply_reset();
        apply_inputs(1'b1, 1'b1, 1'b0, '0);  // en=1, up
        for (int i = 0; i <= MAX_VAL; i++) begin
            // Expected value: on the NEXT rising edge after setting en, count increments
            // After reset count=0, so check before increment
            if (i > 0) begin
                wait_cycles(1);
            end
            check("TC2_count_up", i, 1'b0);
        end
        // One more clock: should roll over to 0 with overflow
        wait_cycles(1);
        check("TC2_overflow", MIN_VAL, 1'b1);

        //----------------------------------------------------------------------
        // TC3: Count down from MAX_VAL to 0
        //----------------------------------------------------------------------
        test_header(3, "Count down (MAX_VAL to 0)");
        apply_reset();
        // Load MAX_VAL first
        apply_inputs(1'b0, 1'b0, 1'b1, MAX_VAL);  // load MAX_VAL
        wait_cycles(1);
        check("TC3_after_load", MAX_VAL, 1'b0);
        // Now count down
        apply_inputs(1'b1, 1'b0, 1'b0, '0);  // en=1, down
        for (int i = MAX_VAL - 1; i >= 0; i--) begin
            wait_cycles(1);
            check("TC3_count_down", i, 1'b0);
        end
        // One more clock: should roll under to MAX_VAL with overflow
        wait_cycles(1);
        check("TC3_underflow", MAX_VAL, 1'b1);

        //----------------------------------------------------------------------
        // TC4: Enable/disable control
        //----------------------------------------------------------------------
        test_header(4, "Enable/disable control");
        apply_reset();
        // Count up 3 cycles
        apply_inputs(1'b1, 1'b1, 1'b0, '0);
        wait_cycles(1); check("TC4_en_count=1", 1, 1'b0);
        wait_cycles(1); check("TC4_en_count=2", 2, 1'b0);
        wait_cycles(1); check("TC4_en_count=3", 3, 1'b0);
        // Disable: count should hold
        apply_inputs(1'b0, 1'b1, 1'b0, '0);
        wait_cycles(1); check("TC4_dis_hold=3", 3, 1'b0);
        wait_cycles(1); check("TC4_dis_hold=3", 3, 1'b0);
        // Re-enable: should resume from 3
        apply_inputs(1'b1, 1'b1, 1'b0, '0);
        wait_cycles(1); check("TC4_reen_count=4", 4, 1'b0);
        wait_cycles(1); check("TC4_reen_count=5", 5, 1'b0);

        //----------------------------------------------------------------------
        // TC5: Up/down direction switching mid-count
        //----------------------------------------------------------------------
        test_header(5, "Up/down direction switching");
        apply_reset();
        // Count up to 5
        apply_inputs(1'b1, 1'b1, 1'b0, '0);
        repeat (5) wait_cycles(1);
        check("TC5_up_to_5", 5, 1'b0);
        // Switch to down
        apply_inputs(1'b1, 1'b0, 1'b0, '0);
        wait_cycles(1); check("TC5_dn_to_4", 4, 1'b0);
        wait_cycles(1); check("TC5_dn_to_3", 3, 1'b0);
        // Switch back to up
        apply_inputs(1'b1, 1'b1, 1'b0, '0);
        wait_cycles(1); check("TC5_up_to_4", 4, 1'b0);
        wait_cycles(1); check("TC5_up_to_5", 5, 1'b0);

        //----------------------------------------------------------------------
        // TC6: Parallel load
        //----------------------------------------------------------------------
        test_header(6, "Parallel load");
        apply_reset();
        // Load specific value
        apply_inputs(1'b0, 1'b0, 1'b1, 8'hA5);
        wait_cycles(1);
        check("TC6_load_A5", 8'hA5, 1'b0);
        // Load another value
        apply_inputs(1'b0, 1'b0, 1'b1, 8'h00);
        wait_cycles(1);
        check("TC6_load_00", 8'h00, 1'b0);
        // Load MAX_VAL
        apply_inputs(1'b0, 1'b0, 1'b1, MAX_VAL);
        wait_cycles(1);
        check("TC6_load_MAX", MAX_VAL, 1'b0);
        // Load with en=1 but load has priority
        apply_inputs(1'b1, 1'b1, 1'b1, 8'h33);
        wait_cycles(1);
        check("TC6_load_priority", 8'h33, 1'b0);

        //----------------------------------------------------------------------
        // TC7: Overflow detection (count up at MAX, underflow at 0)
        //----------------------------------------------------------------------
        test_header(7, "Overflow/underflow detection");
        apply_reset();
        // Load MAX_VAL - 1, count up to overflow
        apply_inputs(1'b0, 1'b0, 1'b1, MAX_VAL - 1);
        wait_cycles(1);
        check("TC7_pre_oflow", MAX_VAL - 1, 1'b0);
        apply_inputs(1'b1, 1'b1, 1'b0, '0);
        wait_cycles(1);
        check("TC7_at_max", MAX_VAL, 1'b0);
        wait_cycles(1);
        check("TC7_overflow", MIN_VAL, 1'b1);
        // Verify overflow clears on next cycle
        wait_cycles(1);
        check("TC7_oflow_clear", 1, 1'b0);
        // Underflow: load 1, count down to 0 then underflow
        apply_inputs(1'b0, 1'b0, 1'b1, 8'h01);
        wait_cycles(1);
        check("TC7_pre_uflow", 8'h01, 1'b0);
        apply_inputs(1'b1, 1'b0, 1'b0, '0);
        wait_cycles(1);
        check("TC7_at_zero", MIN_VAL, 1'b0);
        wait_cycles(1);
        check("TC7_underflow", MAX_VAL, 1'b1);

        //----------------------------------------------------------------------
        // TC8: Rollover (wrap-around) up and down
        //----------------------------------------------------------------------
        test_header(8, "Rollover wrap-around continuous");
        apply_reset();
        apply_inputs(1'b1, 1'b1, 1'b0, '0);
        // Count through full range twice (2 * MAX_VAL + 2 cycles)
        for (int cycle = 0; cycle < (2 * MAX_VAL + 2); cycle++) begin
            wait_cycles(1);
        end
        // After 2*(MAX_VAL+1) cycles from 0, we should be back at 1
        // (rolled over twice, then one more)
        check("TC8_wrap_done", 2, 1'b0);

        //----------------------------------------------------------------------
        // TC9: Back-to-back load then count
        //----------------------------------------------------------------------
        test_header(9, "Back-to-back load then count");
        apply_reset();
        // Load then immediately count up
        apply_inputs(1'b0, 1'b0, 1'b1, 8'h80);
        wait_cycles(1);
        check("TC9_load_80", 8'h80, 1'b0);
        apply_inputs(1'b1, 1'b1, 1'b0, '0);
        wait_cycles(1);
        check("TC9_count_81", 8'h81, 1'b0);
        // Load then immediately count down
        apply_inputs(1'b0, 1'b0, 1'b1, 8'h10);
        wait_cycles(1);
        check("TC9_load_10", 8'h10, 1'b0);
        apply_inputs(1'b1, 1'b0, 1'b0, '0);
        wait_cycles(1);
        check("TC9_count_0F", 8'h0F, 1'b0);
        // Back-to-back loads (no count between)
        apply_inputs(1'b0, 1'b0, 1'b1, 8'hAA);
        wait_cycles(1);
        check("TC9_load_AA", 8'hAA, 1'b0);
        apply_inputs(1'b0, 1'b0, 1'b1, 8'h55);
        wait_cycles(1);
        check("TC9_load_55", 8'h55, 1'b0);

        //----------------------------------------------------------------------
        // Final report
        //----------------------------------------------------------------------
        $display("");
        $display("=========================================================");
        $display("  SIMULATION SUMMARY");
        $display("=========================================================");
        $display("  Total checks : %0d", pass_count + fail_count);
        $display("  Passed       : %0d", pass_count);
        $display("  Failed       : %0d", fail_count);
        $display("=========================================================");

        if (fail_count == 0) begin
            $display("  *** ALL TESTS PASSED ***");
        end else begin
            $display("  *** SOME TESTS FAILED ***");
        end
        $display("=========================================================");

        $finish;
    end

    //--------------------------------------------------------------------------
    // Watchdog timer u2014 abort if simulation runs too long
    //--------------------------------------------------------------------------
    initial begin
        #(CLK_PERIOD * 2000);
        $display("[ERROR] Watchdog timeout u2014 simulation exceeded maximum runtime.");
        $finish;
    end

    //--------------------------------------------------------------------------
    // Waveform dump (VCD format for open-source tools)
    //--------------------------------------------------------------------------
    initial begin
        $dumpfile("tb_counter.vcd");
        $dumpvars(0, tb_counter);
    end

endmodule
