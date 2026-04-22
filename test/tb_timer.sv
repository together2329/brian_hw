// ============================================================================
// Testbench: tb_timer
// Description: Self-checking testbench for parameterized timer module.
//              DUT instantiated with WIDTH=8, PRESCALER_W=4.
//              Uses timer_env_pkg scoreboard for reference model comparison.
//
// Test Coverage:
//   1. Reset verification
//   2. Periodic mode — timeout + auto-reload
//   3. One-shot mode — timeout + auto-stop
//   4. Prescaler — slowed counting
//   5. Stop/restart — disable mid-count, re-enable
//   6. Back-to-back timeouts — periodic with multiple reloads
// ============================================================================

`timescale 1ns / 1ps

module tb_timer;

    // -------------------------------------------------------------------------
    // Parameters
    // -------------------------------------------------------------------------
    parameter int WIDTH       = 8;
    parameter int PRESCALER_W = 4;

    // -------------------------------------------------------------------------
    // Import verification environment
    // -------------------------------------------------------------------------
    import timer_env_pkg::*;

    // -------------------------------------------------------------------------
    // Interface and clock
    // -------------------------------------------------------------------------
    timer_if #(
        .WIDTH(WIDTH),
        .PRESCALER_W(PRESCALER_W)
    ) if0 ();

    // Clock generation — 10 ns period (5 ns half-period)
    initial begin
        if0.clk = 1'b0;
        forever #5 if0.clk = ~if0.clk;
    end

    // -------------------------------------------------------------------------
    // DUT instantiation
    // -------------------------------------------------------------------------
    timer #(
        .WIDTH(WIDTH),
        .PRESCALER_W(PRESCALER_W)
    ) dut (
        .clk        (if0.clk),
        .rst_n      (if0.rst_n),
        .timer_en   (if0.timer_en),
        .mode       (if0.mode),
        .prescaler  (if0.prescaler),
        .compare_val(if0.compare_val),
        .count      (if0.count),
        .timeout    (if0.timeout),
        .running    (if0.running)
    );

    // -------------------------------------------------------------------------
    // Scoreboard
    // -------------------------------------------------------------------------
    timer_scoreboard sb;

    int cycle_count;
    int total_pass;
    int total_fail;

    // -------------------------------------------------------------------------
    // Helper task: tick — wait one posedge, then sample
    // -------------------------------------------------------------------------
    task tick;
        begin
            @(posedge if0.clk);
            #1;
            cycle_count = cycle_count + 1;
        end
    endtask

    // -------------------------------------------------------------------------
    // Helper task: apply_config — set control inputs and update scoreboard
    // -------------------------------------------------------------------------
    task apply_config(input bit en, input bit md,
                      input int unsigned ps, input int unsigned cmp,
                      input string label);
        begin
            if0.timer_en    = en;
            if0.mode        = md;
            if0.prescaler   = ps[PRESCALER_W-1:0];
            if0.compare_val = cmp[WIDTH-1:0];
            sb.set_inputs(en, md, ps, cmp);
            $display("  [DRV] %s: en=%0b mode=%0s ps=%0d cmp=%0d",
                     label, en, md ? "PERIODIC" : "ONESHOT", ps, cmp);
        end
    endtask

    // -------------------------------------------------------------------------
    // Helper task: tick_and_check — advance one cycle, check DUT vs reference
    // -------------------------------------------------------------------------
    task tick_and_check(input string label);
        begin
            tick();
            sb.ref_tick();
            sb.compare(if0.count, if0.timeout, if0.running,
                       cycle_count, label);
        end
    endtask

    // -------------------------------------------------------------------------
    // Helper task: clear_inputs — disable timer, clear controls
    // -------------------------------------------------------------------------
    task clear_inputs;
        begin
            if0.timer_en    = 1'b0;
            if0.mode        = 1'b0;
            if0.prescaler   = '0;
            if0.compare_val = '0;
            sb.set_inputs(1'b0, 1'b0, 0, 0);
        end
    endtask

    // -------------------------------------------------------------------------
    // Helper task: wait_n_ticks — advance N cycles with checking
    // -------------------------------------------------------------------------
    task wait_n_ticks(input int n, input string label);
        begin
            for (int i = 0; i < n; i = i + 1) begin
                tick_and_check(label);
            end
        end
    endtask

    // -------------------------------------------------------------------------
    // Main stimulus
    // -------------------------------------------------------------------------
    initial begin
        $display("========================================");
        $display("  Timer Testbench — WIDTH=%0d PS_W=%0d", WIDTH, PRESCALER_W);
        $display("========================================");

        // Initialize
        sb = new;
        cycle_count = 0;
        total_pass  = 0;
        total_fail  = 0;
        clear_inputs();
        if0.rst_n = 1'b0;

        // =====================================================================
        // Test 1: Reset verification
        // =====================================================================
        $display("\n--- Test 1: Reset ---");
        tick();
        if (if0.count === '0 && if0.timeout === 1'b0 && if0.running === 1'b0) begin
            total_pass = total_pass + 1;
            $display("  [CHK] PASS: After reset — count=0 timeout=0 running=0");
        end else begin
            total_fail = total_fail + 1;
            $display("  [CHK] FAIL: After reset — count=%0d timeout=%0b running=%0b",
                     if0.count, if0.timeout, if0.running);
        end

        // Release reset
        if0.rst_n = 1'b1;
        tick();
        if (if0.count === '0 && if0.timeout === 1'b0 && if0.running === 1'b0) begin
            total_pass = total_pass + 1;
            $display("  [CHK] PASS: After reset released — count=0 timeout=0 running=0");
        end else begin
            total_fail = total_fail + 1;
            $display("  [CHK] FAIL: After reset released — count=%0d timeout=%0b running=%0b",
                     if0.count, if0.timeout, if0.running);
        end

        // =====================================================================
        // Test 2: Periodic mode — count to 5, timeout, auto-reload, timeout again
        // =====================================================================
        $display("\n--- Test 2: Periodic mode (cmp=5) ---");
        apply_config(1'b1, 1'b1, 0, 5, "Periodic");

        // count: 0→1→2→3→4→5(timeout)→0→1→2→3→4→5(timeout)→0→1
        // With prescaler=0, every clock is a tick
        for (int i = 0; i < 14; i = i + 1) begin
            tick_and_check("Periodic");
        end

        // =====================================================================
        // Test 3: One-shot mode — count to 4, timeout, timer stops
        // =====================================================================
        $display("\n--- Test 3: One-shot mode (cmp=4) ---");

        // First disable to reset timer state
        clear_inputs();
        tick_and_check("One-shot disable");

        apply_config(1'b1, 1'b0, 0, 4, "One-shot");

        // count: 0→1→2→3→4(timeout,stop)→4(hold)→4(hold)
        for (int i = 0; i < 7; i = i + 1) begin
            tick_and_check("One-shot");
        end

        // =====================================================================
        // Test 4: Prescaler test — prescaler=3, count with slowed ticks
        // =====================================================================
        $display("\n--- Test 4: Prescaler (ps=3, cmp=2) ---");

        // Disable first to reset prescaler
        clear_inputs();
        tick_and_check("Prescaler disable");

        apply_config(1'b1, 1'b1, 3, 2, "Prescaler ps=3");

        // With ps=3: tick every 4 clocks (0,1,2,3 → tick at ps_counter==3)
        // Need 4 clocks per count increment
        // count 0→1: 4 clks; 1→2(timeout): 4 clks; 2→0(reload): 4 clks; 0→1: 4 clks
        // Total: ~16 clocks for full cycle, let's run 20
        for (int i = 0; i < 20; i = i + 1) begin
            tick_and_check("Prescaler");
        end

        // =====================================================================
        // Test 5: Stop/restart — disable mid-count, re-enable, verify resume
        // =====================================================================
        $display("\n--- Test 5: Stop/restart ---");

        // Disable first
        clear_inputs();
        tick_and_check("Stop-start disable");

        // Start periodic, count to 2, stop
        apply_config(1'b1, 1'b1, 0, 7, "Stop-start phase1");
        wait_n_ticks(3, "Stop-start counting");  // count: 0→1→2→3

        // Stop mid-count
        $display("  [DRV] Stopping at count=%0d", if0.count);
        clear_inputs();
        wait_n_ticks(3, "Stop-start stopped");  // count should hold

        // Restart
        apply_config(1'b1, 1'b1, 0, 7, "Stop-start restart");
        wait_n_ticks(5, "Stop-start resumed");  // count continues from where it stopped

        // =====================================================================
        // Test 6: Back-to-back timeouts — periodic with small compare value
        // =====================================================================
        $display("\n--- Test 6: Back-to-back timeouts (cmp=2) ---");

        clear_inputs();
        tick_and_check("Back2back disable");

        apply_config(1'b1, 1'b1, 0, 2, "Back2back");

        // count: 0→1→2(timeout)→0→1→2(timeout)→0→1→2(timeout)→0
        // Each cycle increments, timeout every 3rd tick
        for (int i = 0; i < 12; i = i + 1) begin
            tick_and_check("Back2back");
        end

        // =====================================================================
        // Disable timer
        // =====================================================================
        $display("\n--- Cleanup: Disable ---");
        clear_inputs();
        wait_n_ticks(3, "Cleanup");

        // =====================================================================
        // Summary
        // =====================================================================
        sb.report;

        $display("\n========================================");
        $display("  TB Direct Checks  PASS: %0d", total_pass);
        $display("  TB Direct Checks  FAIL: %0d", total_fail);
        $display("  SB Checks         PASS: %0d", sb.pass_count);
        $display("  SB Checks         FAIL: %0d", sb.fail_count);
        $display("========================================");

        if (total_fail == 0 && sb.fail_count == 0) begin
            $display("  *** ALL TESTS PASSED ***");
        end else begin
            $display("  *** SOME TESTS FAILED ***");
        end

        $display("========================================");
        $finish;
    end

endmodule
