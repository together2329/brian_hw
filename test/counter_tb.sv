//============================================================================
// Testbench: counter_tb
// Description: Comprehensive testbench for parameterized N-bit up/down counter
//              Covers: reset, up-count, down-count, enable, load, direction
//              switch, edge cases, random stimulus, and parameterization.
//============================================================================

`timescale 1ns/1ps

module counter_tb;

    // ----------------------------------------------------------------
    // Parameters
    // ----------------------------------------------------------------
    parameter WIDTH = 8;
    parameter CLK_PERIOD = 10;

    // ----------------------------------------------------------------
    // Signals
    // ----------------------------------------------------------------
    logic             clk;
    logic             rst_n;
    logic             en;
    logic             load;
    logic             up_down;
    logic [WIDTH-1:0] data_in;
    logic [WIDTH-1:0] count_out;
    logic             overflow;

    // ----------------------------------------------------------------
    // DUT Instantiation
    // ----------------------------------------------------------------
    counter #(
        .WIDTH(WIDTH)
    ) uut (
        .clk       (clk),
        .rst_n     (rst_n),
        .en        (en),
        .load      (load),
        .up_down   (up_down),
        .data_in   (data_in),
        .count_out (count_out),
        .overflow  (overflow)
    );

    // ----------------------------------------------------------------
    // Clock Generation
    // ----------------------------------------------------------------
    initial clk = 0;
    always #(CLK_PERIOD/2) clk = ~clk;

    // ----------------------------------------------------------------
    // Test Statistics
    // ----------------------------------------------------------------
    int test_count  = 0;
    int pass_count  = 0;
    int fail_count  = 0;

    // ----------------------------------------------------------------
    // Helper Tasks
    // ----------------------------------------------------------------
    task apply_reset;
        begin
            rst_n = 0;
            @(posedge clk);
            @(negedge clk); // Sample after posedge
            rst_n = 1;
        end
    endtask

    task tick(input int n);
        begin
            repeat(n) @(posedge clk);
            #1; // Small delay to let outputs settle after clock edge
        end
    endtask

    task check_value(
        input [WIDTH-1:0] expected,
        input string      test_name
    );
        begin
            test_count++;
            if (count_out !== expected) begin
                $display("  [FAIL] %s: expected count_out=%0d (0x%0h), got %0d (0x%0h)",
                         test_name, expected, expected, count_out, count_out);
                fail_count++;
            end else begin
                $display("  [PASS] %s: count_out=%0d", test_name, count_out);
                pass_count++;
            end
        end
    endtask

    task check_overflow(
        input logic  expected,
        input string test_name
    );
        begin
            test_count++;
            if (overflow !== expected) begin
                $display("  [FAIL] %s: expected overflow=%0b, got %0b",
                         test_name, expected, overflow);
                fail_count++;
            end else begin
                $display("  [PASS] %s: overflow=%0b", test_name, overflow);
                pass_count++;
            end
        end
    endtask

    task check_both(
        input [WIDTH-1:0] exp_count,
        input logic       exp_overflow,
        input string      test_name
    );
        begin
            test_count += 2;
            if (count_out !== exp_count || overflow !== exp_overflow) begin
                $display("  [FAIL] %s: expected count=%0d overflow=%0b, got count=%0d overflow=%0b",
                         test_name, exp_count, exp_overflow, count_out, overflow);
                fail_count++;
            end else begin
                $display("  [PASS] %s: count=%0d overflow=%0b", test_name, count_out, overflow);
                pass_count += 2;
            end
        end
    endtask

    // ----------------------------------------------------------------
    // Reference Model (for random stimulus check)
    // ----------------------------------------------------------------
    logic [WIDTH-1:0] ref_count;
    logic             ref_overflow;

    task update_ref;
        begin
            if (!rst_n) begin
                ref_count   = '0;
                ref_overflow = 1'b0;
            end else if (load) begin
                ref_count    = data_in;
                ref_overflow = 1'b0;
            end else if (en) begin
                if (!up_down) begin
                    if (ref_count == {WIDTH{1'b1}}) begin
                        ref_count    = '0;
                        ref_overflow = 1'b1;
                    end else begin
                        ref_count    = ref_count + 1'b1;
                        ref_overflow = 1'b0;
                    end
                end else begin
                    if (ref_count == '0) begin
                        ref_count    = {WIDTH{1'b1}};
                        ref_overflow = 1'b1;
                    end else begin
                        ref_count    = ref_count - 1'b1;
                        ref_overflow = 1'b0;
                    end
                end
            end else begin
                ref_overflow = 1'b0;
            end
        end
    endtask

    // ----------------------------------------------------------------
    // Main Test Sequence
    // ----------------------------------------------------------------
    initial begin
        // Initialize all inputs
        clk     = 0;
        rst_n   = 1;
        en      = 0;
        load    = 0;
        up_down = 0;
        data_in = '0;

        $display("============================================================");
        $display("  Counter Testbench — WIDTH=%0d", WIDTH);
        $display("============================================================");

        // Wait a few cycles for stability
        tick(5);

        // ============================================================
        // GROUP 1: Reset Tests
        // ============================================================
        $display("");
        $display("--- Group 1: Reset Tests ---");

        // Test 1.1: Sync reset
        $display("[Test 1.1] Sync reset");
        apply_reset;
        check_both('0, 1'b0, "Test 1.1: After reset");

        // Test 1.2: Reset while counting
        $display("[Test 1.2] Reset while counting");
        apply_reset;
        en = 1; up_down = 0;
        tick(5);
        rst_n = 0;
        tick(1);
        check_both('0, 1'b0, "Test 1.2: Reset mid-count");
        rst_n = 1;
        tick(1);

        // Test 1.3: Reset priority over load
        $display("[Test 1.3] Reset priority over load");
        apply_reset;
        rst_n   = 0;
        load    = 1;
        data_in = {WIDTH{1'b1}};
        tick(1);
        check_both('0, 1'b0, "Test 1.3: Reset overrides load");
        rst_n = 1;
        load  = 0;
        tick(1);

        // ============================================================
        // GROUP 2: Up-Count Tests
        // ============================================================
        $display("");
        $display("--- Group 2: Up-Count Tests ---");

        // Test 2.1: Up-count basic
        $display("[Test 2.1] Up-count basic");
        apply_reset;
        en = 1; up_down = 0; load = 0;
        tick(1);
        check_value('d1, "Test 2.1: After 1 tick");
        tick(1);
        check_value('d2, "Test 2.1: After 2 ticks");
        tick(1);
        check_value('d3, "Test 2.1: After 3 ticks");

        // Test 2.2: Up-count full rollover (use small count for speed)
        $display("[Test 2.2] Up-count full rollover");
        apply_reset;
        en = 1; up_down = 0;
        tick((1 << WIDTH)); // Count 2^WIDTH cycles — wraps from MAX to 0
        check_both('0, 1'b1, "Test 2.2: At wrap point, overflow=1");
        tick(1); // One more tick — overflow clears, count increments
        check_both('d1, 1'b0, "Test 2.2: Overflow cleared, count=1");

        // Test 2.3: Up overflow
        $display("[Test 2.3] Up overflow pulse");
        apply_reset;
        en = 1; up_down = 0;
        // Load max value - 2 to get close quickly
        load = 1; data_in = {WIDTH{1'b1}} - 2;
        tick(1);
        load = 0;
        // Now at MAX-2
        check_value({WIDTH{1'b1}} - 2, "Test 2.3: Loaded MAX-2");
        tick(1); // MAX-1
        check_value({WIDTH{1'b1}} - 1, "Test 2.3: At MAX-1");
        tick(1); // At MAX — no overflow yet
        check_both({WIDTH{1'b1}}, 1'b0, "Test 2.3: At MAX (overflow=0, will fire next)");
        tick(1); // Wraps to 0, overflow pulses
        check_both('0, 1'b1, "Test 2.3: Overflow pulse at wrap");
        tick(1); // Overflow should clear
        check_both('d1, 1'b0, "Test 2.3: Overflow cleared next cycle");

        // ============================================================
        // GROUP 3: Down-Count Tests
        // ============================================================
        $display("");
        $display("--- Group 3: Down-Count Tests ---");

        // Test 3.1: Down-count basic
        $display("[Test 3.1] Down-count basic");
        apply_reset;
        load = 1; data_in = 10; up_down = 1;
        tick(1);
        load = 0; en = 1;
        tick(1);
        check_value('d9, "Test 3.1: After 1 down tick");
        tick(1);
        check_value('d8, "Test 3.1: After 2 down ticks");
        tick(1);
        check_value('d7, "Test 3.1: After 3 down ticks");

        // Test 3.2: Down-count rollover from 0
        $display("[Test 3.2] Down-count rollover");
        apply_reset;
        en = 1; up_down = 1; load = 0;
        // Already at 0, count down should wrap
        tick(1);
        check_both({WIDTH{1'b1}}, 1'b1, "Test 3.2: Wrapped from 0 to MAX, overflow=1");

        // Test 3.3: Down overflow from value 1
        $display("[Test 3.3] Down overflow pulse");
        apply_reset;
        load = 1; data_in = 1; up_down = 1;
        tick(1);
        load = 0; en = 1;
        tick(1); // Now at 0, no overflow yet
        check_both('d0, 1'b0, "Test 3.3: At 0 (overflow=0)");
        tick(1); // Wraps to MAX, overflow pulses
        check_both({WIDTH{1'b1}}, 1'b1, "Test 3.3: Underflow wrap, overflow=1");

        // ============================================================
        // GROUP 4: Enable Control Tests
        // ============================================================
        $display("");
        $display("--- Group 4: Enable Control Tests ---");

        // Test 4.1: Enable disable — count holds
        $display("[Test 4.1] Enable disable");
        apply_reset;
        en = 1; up_down = 0;
        tick(3);
        check_value('d3, "Test 4.1: Counted to 3");
        en = 0;
        tick(5);
        check_value('d3, "Test 4.1: Held at 3 with en=0");

        // Test 4.2: Enable toggle
        $display("[Test 4.2] Enable toggle");
        apply_reset;
        en = 1; up_down = 0;
        tick(1); // count=1
        en = 0;
        tick(1); // count=1 (hold)
        en = 1;
        tick(1); // count=2
        en = 0;
        tick(1); // count=2 (hold)
        check_value('d2, "Test 4.2: Toggle en, count=2");
        en = 1;
        tick(1); // count=3
        check_value('d3, "Test 4.2: Re-enabled, count=3");

        // Test 4.3: Load with en=0
        $display("[Test 4.3] Load with en=0");
        apply_reset;
        en = 0; load = 1; data_in = 42;
        tick(1);
        check_value('d42, "Test 4.3: Load works with en=0");
        load = 0;
        tick(1);
        check_value('d42, "Test 4.3: Value held after load release");

        // ============================================================
        // GROUP 5: Parallel Load Tests
        // ============================================================
        $display("");
        $display("--- Group 5: Parallel Load Tests ---");

        // Test 5.1: Load basic random value
        $display("[Test 5.1] Load basic random value");
        apply_reset;
        load = 1; data_in = 8'hA5;
        tick(1);
        check_value('hA5, "Test 5.1: Loaded 0xA5");
        load = 0;
        tick(1);

        // Test 5.2: Load all zeros
        $display("[Test 5.2] Load all zeros");
        apply_reset;
        en = 1; up_down = 0;
        tick(5); // Count to 5
        load = 1; data_in = '0;
        tick(1);
        check_both('0, 1'b0, "Test 5.2: Loaded 0");
        load = 0;
        tick(1);

        // Test 5.3: Load all ones (max)
        $display("[Test 5.3] Load all ones");
        apply_reset;
        load = 1; data_in = {WIDTH{1'b1}};
        tick(1);
        check_both({WIDTH{1'b1}}, 1'b0, "Test 5.3: Loaded MAX");
        load = 0;
        tick(1);

        // Test 5.4: Load overrides count increment
        $display("[Test 5.4] Load overrides count");
        apply_reset;
        en = 1; up_down = 0;
        tick(3); // count=3
        load = 1; data_in = 99;
        tick(1); // load takes priority over count
        check_value('d99, "Test 5.4: Load overrode count");
        load = 0;
        tick(1);

        // Test 5.5: Load then count resumes
        $display("[Test 5.5] Load then count resumes");
        apply_reset;
        en = 1; up_down = 0;
        load = 1; data_in = 50;
        tick(1);
        load = 0;
        tick(1); // Should count to 51
        check_value('d51, "Test 5.5: Count resumed from loaded value");
        tick(1);
        check_value('d52, "Test 5.5: Continuing to 52");

        // ============================================================
        // GROUP 6: Direction Switch Tests
        // ============================================================
        $display("");
        $display("--- Group 6: Direction Switch Tests ---");

        // Test 6.1: Switch up to down
        $display("[Test 6.1] Switch up to down");
        apply_reset;
        en = 1; up_down = 0;
        tick(5); // count=5
        check_value('d5, "Test 6.1: Counted up to 5");
        up_down = 1;
        tick(1);
        check_value('d4, "Test 6.1: Counting down to 4");
        tick(1);
        check_value('d3, "Test 6.1: Counting down to 3");

        // Test 6.2: Switch down to up
        $display("[Test 6.2] Switch down to up");
        apply_reset;
        load = 1; data_in = 20; up_down = 1;
        tick(1);
        load = 0; en = 1;
        tick(3); // count=17
        check_value('d17, "Test 6.2: Counted down to 17");
        up_down = 0;
        tick(1);
        check_value('d18, "Test 6.2: Counting up to 18");
        tick(1);
        check_value('d19, "Test 6.2: Counting up to 19");

        // Test 6.3: Switch direction mid-cycle
        $display("[Test 6.3] Switch direction mid-cycle");
        apply_reset;
        load = 1; data_in = 10; en = 1;
        tick(1);
        load = 0; up_down = 1; // Switch at same time as counting
        tick(1);
        check_value('d9, "Test 6.3: Direction switch took effect");
        tick(1);
        check_value('d8, "Test 6.3: Continuing down");

        // ============================================================
        // GROUP 7: Edge & Stress Tests
        // ============================================================
        $display("");
        $display("--- Group 7: Edge & Stress Tests ---");

        // Test 7.1: Rapid load-count alternation
        $display("[Test 7.1] Rapid load-count");
        apply_reset;
        en = 1; up_down = 0;
        load = 1; data_in = 10;
        tick(1); // load 10
        load = 0;
        tick(1); // count to 11
        check_value('d11, "Test 7.1: After load+count cycle 1");
        load = 1; data_in = 20;
        tick(1); // load 20
        load = 0;
        tick(1); // count to 21
        check_value('d21, "Test 7.1: After load+count cycle 2");
        load = 1; data_in = 5;
        tick(1); // load 5
        load = 0;
        tick(1); // count to 6
        check_value('d6, "Test 7.1: After load+count cycle 3");

        // Test 7.2: Random stimulus with reference model
        $display("[Test 7.2] Random stimulus — 500 cycles");
        begin
            int rand_fails = 0;
            apply_reset;
            ref_count    = '0;
            ref_overflow = 1'b0;

            for (int i = 0; i < 500; i++) begin
                // Constrained random stimulus
                en      = $urandom_range(0, 1);
                load    = $urandom_range(0, 1);
                up_down = $urandom_range(0, 1);
                data_in = $urandom_range(0, (1 << WIDTH) - 1);

                // Update reference model
                update_ref;

                tick(1);

                // Check every cycle
                test_count++;
                if (count_out !== ref_count || overflow !== ref_overflow) begin
                    $display("  [FAIL] Random cycle %0d: DUT count=%0d overflow=%0b | REF count=%0d overflow=%0b",
                             i, count_out, overflow, ref_count, ref_overflow);
                    fail_count++;
                    rand_fails++;
                end else begin
                    pass_count++;
                end
            end
            $display("  [INFO] Random stimulus: 500 cycles completed, %0d fails", rand_fails);
        end

        // ============================================================
        // GROUP 7 continued: Full cycle 4-bit (only if WIDTH=4 or we use a local approach)
        // Since we're parameterized at WIDTH=8, we'll test the full cycle
        // by counting through all values for WIDTH=8
        // ============================================================
        // Test 7.3: Full cycle test
        $display("[Test 7.3] Full up-cycle 0→MAX→0");
        begin
            logic [WIDTH-1:0] expected_val;
            apply_reset;
            en = 1; up_down = 0;
            
            // Count from 0 to MAX
            expected_val = 0;
            for (int i = 0; i <= (1 << WIDTH); i++) begin
                if (i < (1 << WIDTH)) begin
                    if (count_out !== expected_val) begin
                        $display("  [FAIL] Full cycle up step %0d: expected %0d, got %0d",
                                 i, expected_val, count_out);
                        fail_count++;
                    end else begin
                        pass_count++;
                    end
                    test_count++;
                end
                tick(1);
                expected_val = expected_val + 1;
            end
            // After wrap, should be back at 0 (or 1 after one more tick)
            $display("  [INFO] Full up-cycle completed, count_out=%0d", count_out);
        end

        // ============================================================
        // GROUP 8: Parameterization Tests
        // Note: These are covered implicitly by the WIDTH parameter.
        // For explicit multi-width testing, separate testbenches would
        // be needed. We verify WIDTH=8 works here.
        // ============================================================
        $display("");
        $display("--- Group 8: Parameterization Tests ---");

        // Test 8.1: WIDTH=8 (already running — verify basic operation)
        $display("[Test 8.1] WIDTH=%0d basic verification", WIDTH);
        apply_reset;
        en = 1; up_down = 0;
        tick(1);
        check_value('d1, "Test 8.1: WIDTH=8 count=1");
        tick(1);
        check_value('d2, "Test 8.1: WIDTH=8 count=2");
        $display("  [INFO] WIDTH=%0d parameter verified in this testbench", WIDTH);
        $display("  [INFO] For WIDTH=4 and WIDTH=16, re-run with different parameter overrides");

        // ============================================================
        // Final Summary
        // ============================================================
        $display("");
        $display("============================================================");
        $display("  TEST SUMMARY");
        $display("  Total checks: %0d", test_count);
        $display("  Passed:       %0d", pass_count);
        $display("  Failed:       %0d", fail_count);
        if (fail_count == 0)
            $display("  *** ALL TESTS PASSED ***");
        else
            $display("  *** SOME TESTS FAILED ***");
        $display("============================================================");

        $finish;
    end

    // ----------------------------------------------------------------
    // Waveform Dump
    // ----------------------------------------------------------------
    initial begin
        $dumpfile("counter_tb.vcd");
        $dumpvars(0, counter_tb);
    end

    // ----------------------------------------------------------------
    // Watchdog Timer
    // ----------------------------------------------------------------
    initial begin
        #100000;
        $display("[ERROR] Watchdog timeout — simulation exceeded 100000ns");
        $finish;
    end

endmodule
