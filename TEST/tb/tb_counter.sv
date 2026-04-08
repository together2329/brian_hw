// ============================================================================
// Testbench: tb_counter
// Description: Self-checking testbench for the parameterized up/down counter.
//              Covers: reset, count up, count down, load, overflow/underflow,
//              enable/disable, and zero flag.
// ============================================================================

`timescale 1ns/1ps

module tb_counter;

    // ------------------------------------------------------------------
    // Parameters
    // ------------------------------------------------------------------
    parameter int WIDTH = 8;
    parameter int CLK_PERIOD = 10;  // 10 ns → 100 MHz

    // ------------------------------------------------------------------
    // Signals
    // ------------------------------------------------------------------
    logic             clk;
    logic             rst_n;
    logic             enable;
    logic             up_down;
    logic             load;
    logic [WIDTH-1:0] data_in;
    logic [WIDTH-1:0] count;
    logic             zero;
    logic             overflow;

    // ------------------------------------------------------------------
    // Scoreboard
    // ------------------------------------------------------------------
    int num_tests   = 0;
    int num_passed  = 0;
    int num_failed  = 0;

    // ------------------------------------------------------------------
    // Clock generation
    // ------------------------------------------------------------------
    initial begin
        clk = 1'b0;
        forever #(CLK_PERIOD/2) clk = ~clk;
    end

    // ------------------------------------------------------------------
    // DUT instantiation
    // ------------------------------------------------------------------
    counter #(
        .WIDTH(WIDTH)
    ) dut (
        .clk      (clk),
        .rst_n    (rst_n),
        .enable   (enable),
        .up_down  (up_down),
        .load     (load),
        .data_in  (data_in),
        .count    (count),
        .zero     (zero),
        .overflow (overflow)
    );

    // ------------------------------------------------------------------
    // Helper tasks
    // ------------------------------------------------------------------
    task apply_reset;
        begin
            rst_n = 1'b0;
            enable = 1'b0;
            up_down = 1'b0;
            load = 1'b0;
            data_in = '0;
            repeat(4) @(posedge clk);
            rst_n = 1'b1;
            @(posedge clk);
            #1; // End safely between edges (posedge + 1ns)
        end
    endtask

    task check_value(
        input logic [WIDTH-1:0] expected_count,
        input logic             expected_zero,
        input logic             expected_overflow,
        input string            test_name
    );
        begin
            num_tests++;
            if (count !== expected_count) begin
                $display("[FAIL] %0s: count=%0d (expected %0d)", test_name, count, expected_count);
                num_failed++;
            end else if (zero !== expected_zero) begin
                $display("[FAIL] %0s: zero=%0b (expected %0b)", test_name, zero, expected_zero);
                num_failed++;
            end else if (overflow !== expected_overflow) begin
                $display("[FAIL] %0s: overflow=%0b (expected %0b)", test_name, overflow, expected_overflow);
                num_failed++;
            end else begin
                $display("[PASS] %0s: count=%0d, zero=%0b, overflow=%0b", test_name, count, zero, overflow);
                num_passed++;
            end
        end
    endtask

    // ------------------------------------------------------------------
    // Helper: drive inputs after the clock edge, then wait N cycles
    //         so inputs are cleanly captured on subsequent edges.
    // ------------------------------------------------------------------
    task wait_n_cycles(input int n);
        repeat(n) begin
            @(posedge clk);
            #1;
        end
    endtask

    // ------------------------------------------------------------------
    // Main stimulus
    //
    // Timing convention:
    //   apply_reset() and wait_n_cycles() both leave us at posedge + 1ns,
    //   safely between clock edges. Signals can be set immediately
    //   and will be captured on the NEXT rising edge.
    // ------------------------------------------------------------------
    initial begin
        $dumpfile("tb_counter.vcd");
        $dumpvars(0, tb_counter);

        $display("==========================================================");
        $display("  Counter Testbench - WIDTH=%0d", WIDTH);
        $display("==========================================================");

        // ---- Test 1: Reset ----
        $display("\n--- Test 1: Reset ---");
        apply_reset();  // ends at posedge + 1ns, count=0
        check_value('0, 1'b1, 1'b0, "After reset");

        // ---- Test 2: Count up ----
        $display("\n--- Test 2: Count up ---");
        enable  = 1'b1;
        up_down = 1'b1;
        wait_n_cycles(5);  // 5 rising edges: count → 1,2,3,4,5
        check_value(5, 1'b0, 1'b0, "Count up to 5");

        // ---- Test 3: Count down ----
        $display("\n--- Test 3: Count down ---");
        up_down = 1'b0;
        wait_n_cycles(3);  // 3 rising edges: count → 4,3,2
        check_value(2, 1'b0, 1'b0, "Count down to 2");

        // ---- Test 4: Count down to zero (underflow) ----
        $display("\n--- Test 4: Underflow detection ---");
        wait_n_cycles(2);  // count → 1,0
        check_value(0, 1'b1, 1'b0, "Count down to 0");
        wait_n_cycles(1);  // count → 255 (underflow), overflow pulse
        check_value({WIDTH{1'b1}}, 1'b0, 1'b1, "Underflow wrap (0-1 = max), overflow=1");

        // ---- Test 5: Load value ----
        $display("\n--- Test 5: Load ---");
        load    = 1'b1;
        data_in = 8'hA5;
        wait_n_cycles(1);  // load captured → count = 0xA5
        load = 1'b0;
        check_value(8'hA5, 1'b0, 1'b0, "Load 0xA5");

        // ---- Test 6: Load overrides enable ----
        $display("\n--- Test 6: Load overrides enable ---");
        load    = 1'b1;
        data_in = 8'h10;
        enable  = 1'b1;
        up_down = 1'b1;
        wait_n_cycles(1);  // load wins over enable → count = 0x10
        load = 1'b0;
        check_value(8'h10, 1'b0, 1'b0, "Load overrides count-up");

        // ---- Test 7: Disable counting ----
        $display("\n--- Test 7: Disable ---");
        enable = 1'b0;
        wait_n_cycles(5);  // should hold at 0x10
        check_value(8'h10, 1'b0, 1'b0, "Hold at 0x10 with enable=0");

        // ---- Test 8: Overflow at max value ----
        $display("\n--- Test 8: Overflow at max ---");
        load    = 1'b1;
        data_in = {WIDTH{1'b1}};  // Load max value
        enable  = 1'b1;
        wait_n_cycles(1);  // load captured → count = 255
        load = 1'b0;
        check_value({WIDTH{1'b1}}, 1'b0, 1'b0, "Loaded max value");
        wait_n_cycles(1);  // count wraps: 255+1 → 0, overflow pulse
        check_value('0, 1'b1, 1'b1, "Overflow: max+1 = 0, overflow=1");

        // ---- Test 9: Enable toggling ----
        $display("\n--- Test 9: Enable toggling ---");
        apply_reset();  // count = 0, at posedge + 1ns
        enable  = 1'b1;
        up_down = 1'b1;
        wait_n_cycles(1);  // count → 1
        check_value(1, 1'b0, 1'b0, "Enabled: count=1");
        enable = 1'b0;
        wait_n_cycles(1);  // hold at 1
        check_value(1, 1'b0, 1'b0, "Disabled: hold at 1");
        enable = 1'b1;
        wait_n_cycles(1);  // count → 2
        check_value(2, 1'b0, 1'b0, "Re-enabled: count=2");

        // ---- Test 10: Zero flag with load ----
        $display("\n--- Test 10: Zero flag with load ---");
        load    = 1'b1;
        data_in = '0;
        wait_n_cycles(1);  // load 0
        load = 1'b0;
        check_value('0, 1'b1, 1'b0, "Load zero, zero flag=1");

        // ------------------------------------------------------------------
        // Final report
        // ------------------------------------------------------------------
        wait_n_cycles(4);
        $display("\n==========================================================");
        $display("  TEST SUMMARY");
        $display("  Total : %0d", num_tests);
        $display("  Passed: %0d", num_passed);
        $display("  Failed: %0d", num_failed);
        if (num_failed == 0)
            $display("  *** ALL TESTS PASSED ***");
        else
            $display("  *** SOME TESTS FAILED ***");
        $display("==========================================================");

        $finish;
    end

    // ------------------------------------------------------------------
    // Timeout watchdog
    // ------------------------------------------------------------------
    initial begin
        #100us;
        $display("[ERROR] Simulation timed out!");
        $finish;
    end

endmodule
