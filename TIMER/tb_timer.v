`timescale 1ns / 1ps

//----------------------------------------------------------------------------
// Module: tb_timer
// Description: Self-checking testbench for timer_apb (APB3 timer wrapper).
//
// Note: Each APB transaction (read/write) takes 3 PCLK cycles. During
// those cycles the timer may still be counting. Tests use large period
// values and range checks to tolerate APB overhead.
//
// Tests:
//   1. Reset behavior
//   2. APB register read/write
//   3. One-shot countdown
//   4. Auto-reload mode
//   5. Prescaler=2 division
//   6. Pause/resume
//   7. STATUS register (running bit)
//   8. IRQ output
//   9. Invalid address returns 0
//  10. Write to read-only registers ignored
//----------------------------------------------------------------------------

module tb_timer;

    //--------------------------------------------------------------------------
    // Parameters
    //--------------------------------------------------------------------------
    localparam CLK_PERIOD = 10;

    // Register addresses
    localparam [7:0] ADDR_CTRL      = 8'h00;
    localparam [7:0] ADDR_PERIOD    = 8'h04;
    localparam [7:0] ADDR_PRESCALER = 8'h08;
    localparam [7:0] ADDR_VALUE     = 8'h0C;
    localparam [7:0] ADDR_STATUS    = 8'h10;

    // CTRL bit fields
    localparam [31:0] CTRL_ENABLE      = 32'h1;
    localparam [31:0] CTRL_AUTO_RELOAD = 32'h2;
    localparam [31:0] CTRL_LOAD        = 32'h4;

    //--------------------------------------------------------------------------
    // APB Signals
    //--------------------------------------------------------------------------
    reg         PCLK;
    reg         PRESETn;
    reg         PSEL;
    reg         PENABLE;
    reg         PWRITE;
    reg  [7:0]  PADDR;
    reg  [31:0] PWDATA;
    wire [31:0] PRDATA;
    wire        PREADY;
    wire        PSLVERR;
    wire        irq;

    // Test tracking
    integer     tests_passed = 0;
    integer     tests_failed = 0;
    reg  [31:0] rd_data;

    //--------------------------------------------------------------------------
    // Device Under Test
    //--------------------------------------------------------------------------
    timer_apb dut (
        .PCLK    (PCLK),
        .PRESETn (PRESETn),
        .PSEL    (PSEL),
        .PENABLE (PENABLE),
        .PWRITE  (PWRITE),
        .PADDR   (PADDR),
        .PWDATA  (PWDATA),
        .PRDATA  (PRDATA),
        .PREADY  (PREADY),
        .PSLVERR (PSLVERR),
        .irq     (irq)
    );

    //--------------------------------------------------------------------------
    // Clock generator
    //--------------------------------------------------------------------------
    initial begin
        PCLK = 1'b0;
        forever #(CLK_PERIOD/2) PCLK = ~PCLK;
    end

    //--------------------------------------------------------------------------
    // Waveform dump
    //--------------------------------------------------------------------------
    initial begin
        $dumpfile("timer.vcd");
        $dumpvars(0, tb_timer);
    end

    //--------------------------------------------------------------------------
    // APB bus tasks
    //--------------------------------------------------------------------------
    `include "apb_tasks.vh"

    //--------------------------------------------------------------------------
    // Check task
    //--------------------------------------------------------------------------
    task check;
        input expected_pass;
        input [512*8-1:0] msg;
        begin
            if (expected_pass) begin
                $display("[PASS] %0s", msg);
                tests_passed = tests_passed + 1;
            end else begin
                $display("[FAIL] %0s", msg);
                tests_failed = tests_failed + 1;
            end
        end
    endtask

    //--------------------------------------------------------------------------
    // Helper: stop timer and read VALUE
    //--------------------------------------------------------------------------
    task stop_and_read_value;
        output [31:0] val;
        begin
            apb_write(ADDR_CTRL, 32'd0);
            apb_read(ADDR_VALUE, val);
        end
    endtask

    //--------------------------------------------------------------------------
    // Main test sequence
    //--------------------------------------------------------------------------
    initial begin
        $display("========================================");
        $display(" APB Timer Testbench Starting...");
        $display("========================================");

        // Initialize APB bus
        PRESETn = 1'b0;
        PSEL    = 1'b0;
        PENABLE = 1'b0;
        PWRITE  = 1'b0;
        PADDR   = 8'd0;
        PWDATA  = 32'd0;

        //======================================================================
        // Test 1: Reset behavior
        //======================================================================
        $display("\n--- Test 1: Reset ---");
        @(negedge PCLK);
        PRESETn = 1'b0;
        @(negedge PCLK);
        @(negedge PCLK);

        apb_read(ADDR_CTRL, rd_data);
        check(rd_data == 32'd0, "Reset: CTRL is zero");

        apb_read(ADDR_VALUE, rd_data);
        check(rd_data == 32'd0, "Reset: VALUE is zero");

        apb_read(ADDR_STATUS, rd_data);
        check(rd_data == 32'd0, "Reset: STATUS is zero");

        check(irq == 1'b0, "Reset: irq is low");

        PRESETn = 1'b1;
        @(negedge PCLK);

        //======================================================================
        // Test 2: APB register read/write
        //======================================================================
        $display("\n--- Test 2: Register R/W ---");

        apb_write(ADDR_PERIOD, 32'd100);
        apb_read(ADDR_PERIOD, rd_data);
        check(rd_data == 32'd100, "R/W: PERIOD written and read back");

        apb_write(ADDR_PRESCALER, 32'd5);
        apb_read(ADDR_PRESCALER, rd_data);
        check(rd_data[15:0] == 16'd5, "R/W: PRESCALER written and read back");

        apb_write(ADDR_CTRL, CTRL_ENABLE);
        apb_read(ADDR_CTRL, rd_data);
        check(rd_data[0] == 1'b1, "R/W: CTRL enable bit set");

        apb_write(ADDR_CTRL, 32'd0);
        apb_read(ADDR_CTRL, rd_data);
        check(rd_data[0] == 1'b0, "R/W: CTRL enable bit cleared");

        //======================================================================
        // Test 3: One-shot countdown
        // With psr=1 and period=1000, wait 100 ticks then stop.
        // APB overhead ~= 6 clocks (3 for disable + 3 for read), so
        // expected value is around 894 (1000 - 100 - 6). Use range check.
        //======================================================================
        $display("\n--- Test 3: One-shot countdown (psr=1) ---");

        apb_write(ADDR_PRESCALER, 32'd1);
        apb_write(ADDR_PERIOD, 32'd1000);

        // Load the period into counter
        apb_write(ADDR_CTRL, CTRL_LOAD);
        @(negedge PCLK);

        apb_read(ADDR_VALUE, rd_data);
        check(rd_data == 32'd1000, "One-shot: loaded period value 1000");

        // Enable for 100 ticks
        apb_write(ADDR_CTRL, CTRL_ENABLE);
        repeat(100) @(negedge PCLK);

        // Stop and read (APB overhead ~6 extra ticks)
        stop_and_read_value(rd_data);
        check(rd_data >= 32'd890 && rd_data <= 32'd900,
              "One-shot: value near 894 after ~100 ticks");

        // Run to completion: re-enable and wait for done
        apb_write(ADDR_PERIOD, 32'd10);
        apb_write(ADDR_CTRL, CTRL_LOAD);
        @(negedge PCLK);
        apb_write(ADDR_CTRL, CTRL_ENABLE);
        repeat(20) @(negedge PCLK);

        stop_and_read_value(rd_data);
        check(rd_data == 32'd0, "One-shot: counter reached 0");

        // Check done_sticky
        apb_read(ADDR_STATUS, rd_data);
        check(rd_data[1] == 1'b1, "One-shot: done_sticky set in STATUS");

        @(negedge PCLK);

        //======================================================================
        // Test 4: Auto-reload mode
        // Period=10, psr=1. After 10 ticks, counter should reload.
        // Use done_sticky as the primary indicator.
        //======================================================================
        $display("\n--- Test 4: Auto-reload (psr=1) ---");

        // Clear sticky
        apb_read(ADDR_STATUS, rd_data);

        apb_write(ADDR_PRESCALER, 32'd1);
        apb_write(ADDR_PERIOD, 32'd10);

        // Load + auto_reload
        apb_write(ADDR_CTRL, CTRL_LOAD | CTRL_AUTO_RELOAD);
        @(negedge PCLK);

        // Enable with auto_reload - wait for first done
        apb_write(ADDR_CTRL, CTRL_ENABLE | CTRL_AUTO_RELOAD);
        repeat(20) @(negedge PCLK);

        // Stop and check: counter should have reloaded (non-zero if reloaded)
        stop_and_read_value(rd_data);
        check(rd_data != 32'd0, "Reload: counter is non-zero after reload");

        // done_sticky should be set
        apb_read(ADDR_STATUS, rd_data);
        check(rd_data[1] == 1'b1, "Reload: done_sticky set after first cycle");

        // Clear sticky and run another cycle
        apb_read(ADDR_STATUS, rd_data);
        apb_write(ADDR_CTRL, CTRL_ENABLE | CTRL_AUTO_RELOAD);
        repeat(20) @(negedge PCLK);

        // Stop and check again
        stop_and_read_value(rd_data);
        check(rd_data != 32'd0, "Reload: counter non-zero after second reload");

        apb_read(ADDR_STATUS, rd_data);
        check(rd_data[1] == 1'b1, "Reload: done_sticky set after second cycle");

        // Clear sticky
        apb_read(ADDR_STATUS, rd_data);
        @(negedge PCLK);

        //======================================================================
        // Test 5: Prescaler=2
        // With psr=2 and period=10, counter decrements every 2 PCLKs.
        // After 20 PCLKs, counter should be at 0 or very close.
        //======================================================================
        $display("\n--- Test 5: Prescaler=2 ---");

        // Clear sticky
        apb_read(ADDR_STATUS, rd_data);

        apb_write(ADDR_PRESCALER, 32'd2);
        apb_write(ADDR_PERIOD, 32'd10);

        // Load
        apb_write(ADDR_CTRL, CTRL_LOAD);
        @(negedge PCLK);

        // Enable for 20 PCLKs (= 10 prescaler ticks)
        apb_write(ADDR_CTRL, CTRL_ENABLE);
        repeat(20) @(negedge PCLK);

        // Stop and check
        stop_and_read_value(rd_data);
        check(rd_data <= 32'd2, "Psr2: counter near 0 after 20 PCLKs");

        // Check done_sticky
        apb_read(ADDR_STATUS, rd_data);
        check(rd_data[1] == 1'b1, "Psr2: done_sticky set");

        @(negedge PCLK);

        //======================================================================
        // Test 6: Pause/resume
        //======================================================================
        $display("\n--- Test 6: Pause/resume ---");

        apb_write(ADDR_PRESCALER, 32'd1);
        apb_write(ADDR_PERIOD, 32'd1000);

        // Load
        apb_write(ADDR_CTRL, CTRL_LOAD);
        @(negedge PCLK);

        // Enable for 50 ticks
        apb_write(ADDR_CTRL, CTRL_ENABLE);
        repeat(50) @(negedge PCLK);

        // Pause and read
        stop_and_read_value(rd_data);
        check(rd_data >= 32'd940 && rd_data <= 32'd955,
              "Pause: value near 944 after ~50 ticks");

        // Wait idle clocks (timer stopped)
        repeat(10) @(negedge PCLK);
        apb_read(ADDR_VALUE, rd_data);
        check(rd_data >= 32'd940 && rd_data <= 32'd955,
              "Pause: value unchanged during idle");

        // Resume for 50 more ticks
        apb_write(ADDR_CTRL, CTRL_ENABLE);
        repeat(50) @(negedge PCLK);

        // Stop and read
        stop_and_read_value(rd_data);
        check(rd_data >= 32'd885 && rd_data <= 32'd905,
              "Resume: value near 888 after ~100 total ticks");

        @(negedge PCLK);

        //======================================================================
        // Test 7: STATUS running bit
        //======================================================================
        $display("\n--- Test 7: STATUS running bit ---");

        // Clear sticky
        apb_read(ADDR_STATUS, rd_data);

        apb_write(ADDR_PRESCALER, 32'd1);
        apb_write(ADDR_PERIOD, 32'd1000);

        // Load (not enabled yet)
        apb_write(ADDR_CTRL, CTRL_LOAD);
        @(negedge PCLK);

        // Read STATUS - running should be 0
        apb_read(ADDR_STATUS, rd_data);
        check(rd_data[0] == 1'b0, "Status: not running before enable");

        // Enable
        apb_write(ADDR_CTRL, CTRL_ENABLE);
        @(negedge PCLK);

        // Read STATUS - running should be 1
        apb_read(ADDR_STATUS, rd_data);
        check(rd_data[0] == 1'b1, "Status: running after enable");

        // Disable
        apb_write(ADDR_CTRL, 32'd0);
        @(negedge PCLK);

        //======================================================================
        // Test 8: IRQ output
        //======================================================================
        $display("\n--- Test 8: IRQ output ---");

        // Clear sticky
        apb_read(ADDR_STATUS, rd_data);

        apb_write(ADDR_PRESCALER, 32'd1);
        apb_write(ADDR_PERIOD, 32'd5);

        // Load + enable + auto_reload
        apb_write(ADDR_CTRL, CTRL_LOAD | CTRL_AUTO_RELOAD);
        @(negedge PCLK);
        apb_write(ADDR_CTRL, CTRL_ENABLE | CTRL_AUTO_RELOAD);

        // Wait for done (5 ticks + APB overhead)
        repeat(10) @(negedge PCLK);

        // IRQ should be asserted (done_sticky)
        check(irq == 1'b1, "IRQ: asserted after done");

        // Verify done_sticky in STATUS before clearing
        apb_read(ADDR_STATUS, rd_data);
        check(rd_data[1] == 1'b1, "IRQ: done_sticky in STATUS before clear");

        // After read, irq should deassert
        check(irq == 1'b0, "IRQ: deasserted after STATUS read");

        // Disable
        apb_write(ADDR_CTRL, 32'd0);
        @(negedge PCLK);

        //======================================================================
        // Test 9: Invalid address returns 0
        //======================================================================
        $display("\n--- Test 9: Invalid address ---");
        apb_read(8'h18, rd_data);
        check(rd_data == 32'd0, "BadAddr: unmapped address returns 0");

        apb_read(8'hFC, rd_data);
        check(rd_data == 32'd0, "BadAddr: high address returns 0");

        //======================================================================
        // Test 10: Write to read-only registers ignored
        //======================================================================
        $display("\n--- Test 10: Write to RO registers ---");

        // Clear any pending done_sticky
        apb_read(ADDR_STATUS, rd_data);

        // Configure and load a known value
        apb_write(ADDR_PRESCALER, 32'd1);
        apb_write(ADDR_PERIOD, 32'd50);
        apb_write(ADDR_CTRL, CTRL_LOAD);
        @(negedge PCLK);

        // Read current VALUE
        apb_read(ADDR_VALUE, rd_data);

        // Write to VALUE (read-only) - should be ignored
        apb_write(ADDR_VALUE, 32'hDEADBEEF);

        // Read back VALUE - should not be DEADBEEF
        apb_read(ADDR_VALUE, rd_data);
        check(rd_data != 32'hDEADBEEF, "RO: write to VALUE ignored");

        // Confirm done_sticky is 0
        apb_read(ADDR_STATUS, rd_data);
        check(rd_data[1] == 1'b0, "RO: done_sticky is 0 before STATUS write");

        // Try to set STATUS via write
        apb_write(ADDR_STATUS, 32'hFFFFFFFF);

        // Read back - done_sticky should still be 0
        apb_read(ADDR_STATUS, rd_data);
        check(rd_data[1] == 1'b0, "RO: write to STATUS ignored");

        //======================================================================
        // Summary
        //======================================================================
        $display("\n========================================");
        $display(" Tests Passed: %0d", tests_passed);
        $display(" Tests Failed: %0d", tests_failed);
        if (tests_failed == 0)
            $display(" RESULT: ALL TESTS PASSED");
        else
            $display(" RESULT: SOME TESTS FAILED");
        $display("========================================");

        $finish;
    end

endmodule
