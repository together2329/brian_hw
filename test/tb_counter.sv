// tb_counter.sv — Self-checking testbench for counter module

`timescale 1ns / 1ps

module tb_counter;

    // ── Parameters ──────────────────────────────────────────────
    parameter int WIDTH = 8;

    // ── Signals ─────────────────────────────────────────────────
    logic             clk;
    logic             rst_n;
    logic             en;
    logic             up_down;
    logic             load;
    logic [WIDTH-1:0] load_data;
    logic [WIDTH-1:0] count;

    // ── Scoreboard ──────────────────────────────────────────────
    int pass_count = 0;
    int fail_count = 0;

    // ── Clock generation: 10 ns period (5 ns half-period) ──────
    initial clk = 0;
    always #5 clk = ~clk;

    // ── DUT instantiation ──────────────────────────────────────
    counter #(.WIDTH(WIDTH)) dut (
        .clk       (clk),
        .rst_n     (rst_n),
        .en        (en),
        .up_down   (up_down),
        .load      (load),
        .load_data (load_data),
        .count     (count)
    );

    // ── Helper: check and report ────────────────────────────────
    task automatic check(input string label, input [WIDTH-1:0] expected);
        #1; // Wait for DUT's non-blocking assignments to settle
        if (count === expected) begin
            $display("[PASS] %0s: count=%0d (expected %0d)", label, count, expected);
            pass_count++;
        end else begin
            $display("[FAIL] %0s: count=%0d (expected %0d)", label, count, expected);
            fail_count++;
        end
    endtask

    // ── Helper: wait N clock cycles ─────────────────────────────
    task automatic wait_cycles(input int n);
        repeat (n) @(posedge clk);
    endtask

    // ── Main stimulus ───────────────────────────────────────────
    initial begin
        // Initialize all inputs
        clk       = 0;
        rst_n     = 1;
        en        = 0;
        up_down   = 1;
        load      = 0;
        load_data = '0;

        // ============================================================
        // Test 1: Reset
        // ============================================================
        $display("\n--- Test 1: Synchronous Reset ---");
        @(posedge clk);
        rst_n <= 0;
        @(posedge clk);
        check("after reset", 8'd0);

        // Release reset
        rst_n <= 1;
        @(posedge clk);

        // ============================================================
        // Test 2: Count Up
        // ============================================================
        $display("\n--- Test 2: Count Up ---");
        en      <= 1;
        up_down <= 1;
        wait_cycles(1);
        check("up 1", 8'd1);

        wait_cycles(1);
        check("up 2", 8'd2);

        wait_cycles(4);
        check("up 6", 8'd6);

        // ============================================================
        // Test 3: Count Down
        // ============================================================
        $display("\n--- Test 3: Count Down ---");
        up_down <= 0;
        wait_cycles(1);
        check("down 5", 8'd5);

        wait_cycles(1);
        check("down 4", 8'd4);

        wait_cycles(4);
        check("down 0", 8'd0);

        // ============================================================
        // Test 4: Load
        // ============================================================
        $display("\n--- Test 4: Load ---");
        en        <= 0;
        load      <= 1;
        load_data <= 8'hA5;
        wait_cycles(1);
        check("load 0xA5", 8'hA5);

        load      <= 0;
        load_data <= '0;
        wait_cycles(1);
        check("hold after load (en=0)", 8'hA5);

        // ============================================================
        // Test 5: Up Rollover (255 → 0)
        // ============================================================
        $display("\n--- Test 5: Up Rollover ---");
        load      <= 1;
        load_data <= 8'hFE;          // 254
        wait_cycles(1);
        load <= 0;
        en   <= 1;
        up_down <= 1;

        wait_cycles(1);
        check("FE+1=FF", 8'hFF);

        wait_cycles(1);
        check("FF+1=00 (rollover)", 8'h00);

        // ============================================================
        // Test 6: Down Rollover (0 → 255)
        // ============================================================
        $display("\n--- Test 6: Down Rollover ---");
        up_down <= 0;

        wait_cycles(1);
        check("00-1=FF (rollover)", 8'hFF);

        // ============================================================
        // Test 7: Disable (enable = 0 holds count)
        // ============================================================
        $display("\n--- Test 7: Disable ---");
        en <= 0;
        wait_cycles(3);
        check("hold while disabled", 8'hFF);

        // ============================================================
        // Summary
        // ============================================================
        $display("\n========================================");
        $display("  TEST SUMMARY: %0d PASSED, %0d FAILED", pass_count, fail_count);
        $display("========================================\n");

        if (fail_count == 0)
            $display(">>> ALL TESTS PASSED <<<\n");
        else
            $display(">>> SOME TESTS FAILED <<<\n");

        $finish;
    end

    // ── Timeout watchdog ────────────────────────────────────────
    initial begin
        #10000;
        $display("[ERROR] Simulation timed out!");
        $finish;
    end

endmodule
