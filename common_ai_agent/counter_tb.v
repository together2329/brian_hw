//------------------------------------------------------------
// Testbench for Simple 256-bit Up Counter (Enhanced)
//------------------------------------------------------------
// Verifies:
//   1. Synchronous reset clears count to 0
//  1b. All 256 bits individually verified zero after reset
//   2. Count increments by 1 each clock cycle
//   3. Upper bits remain 0 during short counting
//   4. Reset re-sync works correctly
//   5. Multiple reset pulses work correctly
//   6. Count increments over a longer period (100 cycles)
//   7. Reset during counting clears correctly
//   8. Counting resumes after multiple resets
//   9. All individual bits [7:0] toggle correctly
//  10. Upper 248 bits [255:8] remain zero throughout
//------------------------------------------------------------
// Note: Full wrap-around test (2^256 cycles) is infeasible.

`timescale 1ns / 1ps

module counter_tb;

    // Signals
    reg           clk;
    reg           rst;
    wire [255:0]  count;

    // Pass/fail counters
    integer pass_count;
    integer fail_count;

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

    // Helper task for checking
    task check_value;
        input [255:0] expected;
        input [255:0] actual;
        input [256*8-1:0] test_name;
    begin
        if (actual !== expected) begin
            $display("FAIL: %s - expected %0d, got %0d", test_name, expected, actual);
            fail_count = fail_count + 1;
        end else begin
            $display("PASS: %s - count=%0d", test_name, actual);
            pass_count = pass_count + 1;
        end
    end
    endtask

    // Stimulus
    initial begin
        pass_count = 0;
        fail_count = 0;

        // Init
        rst = 1;

        $monitor("time=%0t  rst=%b  count=%0d", $time, rst, count);

        //=== Check 1: Reset clears to 0 ===
        #20;
        check_value(256'd0, count, "Reset clears count to 0");

        //=== Check 1b: All 256 bits individually zero after reset ===
        begin : allbits_block
            integer bit_i;
            integer allbits_fail;
            allbits_fail = 0;
            for (bit_i = 0; bit_i < 256; bit_i = bit_i + 1) begin
                if (count[bit_i] !== 1'b0) begin
                    $display("FAIL: bit[%0d] is 1 after reset, expected 0", bit_i);
                    allbits_fail = allbits_fail + 1;
                end
            end
            if (allbits_fail > 0) begin
                $display("FAIL: %0d of 256 bits non-zero after reset", allbits_fail);
                fail_count = fail_count + 1;
            end else begin
                $display("PASS: all 256 bits individually verified zero after reset");
                pass_count = pass_count + 1;
            end
        end

        //=== Check 2: Count increments after reset release ===
        rst = 0;
        #100; // 10 cycles
        check_value(256'd10, count, "Count increments to 10");

        //=== Check 3: Upper bits [255:8] are zero ===
        if (count[255:8] !== 248'd0) begin
            $display("FAIL: upper bits non-zero at count=10, count[255:8]=%0d", count[255:8]);
            fail_count = fail_count + 1;
        end else begin
            $display("PASS: upper bits [255:8] are zero at count=10");
            pass_count = pass_count + 1;
        end

        //=== Check 4: Reset re-sync ===
        rst = 1;
        #10 rst = 0;
        #50; // 5 cycles
        check_value(256'd5, count, "Reset re-sync, count=5");

        //=== Check 5: Multiple reset pulses ===
        rst = 1;
        #10 rst = 0;
        #30; // 3 cycles → count=3
        check_value(256'd3, count, "After 2nd reset, count=3");

        rst = 1;
        #10 rst = 0;
        #70; // 7 cycles → count=7
        check_value(256'd7, count, "After 3rd reset, count=7");

        //=== Check 6: Longer counting period (100 cycles) ===
        rst = 1;
        #10 rst = 0;
        #1000; // 100 cycles
        check_value(256'd100, count, "Long count to 100");

        //=== Check 7: Upper bits still zero after long count ===
        if (count[255:8] !== 248'd0) begin
            $display("FAIL: upper bits non-zero at count=100, count[255:8]=%0d", count[255:8]);
            fail_count = fail_count + 1;
        end else begin
            $display("PASS: upper bits [255:8] still zero at count=100");
            pass_count = pass_count + 1;
        end

        //=== Check 8: Reset during active counting ===
        rst = 1;
        #10 rst = 0;
        #50; // count=5
        rst = 1; // sudden reset mid-count
        #10;
        check_value(256'd0, count, "Mid-count reset clears to 0");

        //=== Check 9: Counting resumes after mid-count reset ===
        rst = 0;
        #30; // 3 cycles
        check_value(256'd3, count, "Counting resumes after mid-count reset");

        //=== Check 10: Individual bit toggle verification ===
        rst = 1;
        #10 rst = 0;
        // Count to 255 (all lower 8 bits set) — 255 cycles
        #2550;
        check_value(256'd255, count, "All lower 8 bits set (count=255)");

        // Verify bit pattern: 255 = 8'b11111111
        if (count[7:0] !== 8'hFF) begin
            $display("FAIL: lower 8 bits not all 1s, got %b", count[7:0]);
            fail_count = fail_count + 1;
        end else begin
            $display("PASS: all lower 8 bits are 1 (8'hFF)");
            pass_count = pass_count + 1;
        end

        // Upper bits still zero
        if (count[255:8] !== 248'd0) begin
            $display("FAIL: upper bits non-zero at count=255, count[255:8]=%0d", count[255:8]);
            fail_count = fail_count + 1;
        end else begin
            $display("PASS: upper bits [255:8] zero at count=255");
            pass_count = pass_count + 1;
        end

        //=== Check 11: Next value rolls to 256 ===
        #10;
        check_value(256'd256, count, "Count=256 (bit 8 sets)");

        // Verify bit 8 is set
        if (count[8] !== 1'b1) begin
            $display("FAIL: bit 8 not set at count=256");
            fail_count = fail_count + 1;
        end else begin
            $display("PASS: bit 8 correctly set at count=256");
            pass_count = pass_count + 1;
        end

        if (count[7:0] !== 8'd0) begin
            $display("FAIL: lower 8 bits not zero at count=256, got %b", count[7:0]);
            fail_count = fail_count + 1;
        end else begin
            $display("PASS: lower 8 bits rolled to 0 at count=256");
            pass_count = pass_count + 1;
        end

        //=== Check 12: Count hold during reset ===
        rst = 1;
        begin : hold_block
            integer hold_i;
            for (hold_i = 0; hold_i < 10; hold_i = hold_i + 1) begin
                #10; // one clock cycle
                if (count !== 256'd0) begin
                    $display("FAIL: count changed during reset at sample %0d, count=%0d", hold_i, count);
                    fail_count = fail_count + 1;
                end
            end
        end
        if (count !== 256'd0) begin
            $display("FAIL: count hold during reset — count=%0d, expected 0", count);
            fail_count = fail_count + 1;
        end else begin
            $display("PASS: count held at 0 during 10-cycle reset");
            pass_count = pass_count + 1;
        end

        //=== Check 13: Monotonicity — count increases by exactly 1 ===
        rst = 1;
        #10 rst = 0;
        begin : mono_block
            reg [255:0] prev_count;
            integer mono_pass, mono_fail, mono_i;
            mono_pass = 0;
            mono_fail = 0;
            prev_count = count; // should be 0
            for (mono_i = 0; mono_i < 50; mono_i = mono_i + 1) begin
                #10; // one clock cycle
                if (count !== prev_count + 256'd1) begin
                    $display("FAIL: monotonicity at sample %0d, expected %0d, got %0d", mono_i, prev_count + 256'd1, count);
                    mono_fail = mono_fail + 1;
                end else begin
                    mono_pass = mono_pass + 1;
                end
                prev_count = count;
            end
            if (mono_fail > 0) begin
                $display("FAIL: monotonicity — %0d of 50 samples failed", mono_fail);
                fail_count = fail_count + 1;
            end else begin
                $display("PASS: monotonicity — all 50 samples incremented by exactly 1");
                pass_count = pass_count + 1;
            end
        end

        //=== Final Summary ===
        $display("");
        $display("========================================");
        $display("  TEST SUMMARY");
        $display("  PASSED: %0d", pass_count);
        $display("  FAILED: %0d", fail_count);
        $display("  TOTAL : %0d", pass_count + fail_count);
        $display("========================================");

        if (fail_count > 0)
            $display("  *** SOME TESTS FAILED ***");
        else
            $display("  *** ALL TESTS PASSED ***");

        $finish;
    end

endmodule
