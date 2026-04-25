`timescale 1ns / 1ps

//----------------------------------------------------------------------------
// Module: tb_counter
// Description: Self-checking testbench for counter_apb (APB3 64-bit counter).
//
// Note: COUNT_LO/COUNT_HI are write-to-shadow + read-from-counter.
// To verify writes, you must load the shadow into the counter then read.
// APB transactions take 3 clocks each; counter may count during them.
//----------------------------------------------------------------------------

module tb_counter;

    //--------------------------------------------------------------------------
    // Parameters
    //--------------------------------------------------------------------------
    localparam CLK_PERIOD = 10;

    // Register addresses
    localparam [7:0] ADDR_CTRL      = 8'h00;
    localparam [7:0] ADDR_COUNT_LO  = 8'h04;
    localparam [7:0] ADDR_COUNT_HI  = 8'h08;
    localparam [7:0] ADDR_TC_STATUS = 8'h0C;

    // CTRL bit fields
    localparam [31:0] CTRL_ENABLE  = 32'h1;
    localparam [31:0] CTRL_LOAD    = 32'h2;
    localparam [31:0] CTRL_UP_DOWN = 32'h4;

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
    counter_apb dut (
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
        $dumpfile("counter.vcd");
        $dumpvars(0, tb_counter);
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
    // Main test sequence
    //--------------------------------------------------------------------------
    initial begin
        $display("========================================");
        $display(" 64-bit Counter APB Testbench Starting...");
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

        apb_read(ADDR_COUNT_LO, rd_data);
        check(rd_data == 32'd0, "Reset: COUNT_LO is zero");

        apb_read(ADDR_COUNT_HI, rd_data);
        check(rd_data == 32'd0, "Reset: COUNT_HI is zero");

        apb_read(ADDR_TC_STATUS, rd_data);
        check(rd_data == 32'd0, "Reset: TC_STATUS is zero");

        check(irq == 1'b0, "Reset: irq is low");

        PRESETn = 1'b1;
        @(negedge PCLK);

        //======================================================================
        // Test 2: APB register R/W via load-and-verify
        // COUNT_LO/HI write to shadow; must load to see in counter.
        //======================================================================
        $display("\n--- Test 2: Register R/W ---");

        // CTRL read/write
        apb_write(ADDR_CTRL, CTRL_ENABLE | CTRL_UP_DOWN);
        apb_read(ADDR_CTRL, rd_data);
        check(rd_data[0] == 1'b1, "R/W: enable bit set");
        check(rd_data[2] == 1'b1, "R/W: up_down bit set");

        apb_write(ADDR_CTRL, 32'd0);
        apb_read(ADDR_CTRL, rd_data);
        check(rd_data == 32'd0, "R/W: CTRL cleared");

        // COUNT_LO/HI: write shadow, load, then verify
        apb_write(ADDR_COUNT_LO, 32'hDEADBEEF);
        apb_write(ADDR_COUNT_HI, 32'hCAFEBABE);
        apb_write(ADDR_CTRL, CTRL_LOAD);
        @(negedge PCLK);

        apb_read(ADDR_COUNT_LO, rd_data);
        check(rd_data == 32'hDEADBEEF, "R/W: COUNT_LO loaded correctly");

        apb_read(ADDR_COUNT_HI, rd_data);
        check(rd_data == 32'hCAFEBABE, "R/W: COUNT_HI loaded correctly");

        //======================================================================
        // Test 3: Load 64-bit value via split registers
        //======================================================================
        $display("\n--- Test 3: 64-bit Load ---");

        apb_write(ADDR_COUNT_LO, 32'h11112222);
        apb_write(ADDR_COUNT_HI, 32'h33334444);
        apb_write(ADDR_CTRL, CTRL_LOAD);
        @(negedge PCLK);

        apb_read(ADDR_COUNT_LO, rd_data);
        check(rd_data == 32'h11112222, "Load: COUNT_LO matches");

        apb_read(ADDR_COUNT_HI, rd_data);
        check(rd_data == 32'h33334444, "Load: COUNT_HI matches");

        @(negedge PCLK);

        //======================================================================
        // Test 4: Count up from 0
        //======================================================================
        $display("\n--- Test 4: Count up ---");

        apb_write(ADDR_COUNT_LO, 32'd0);
        apb_write(ADDR_COUNT_HI, 32'd0);
        apb_write(ADDR_CTRL, CTRL_LOAD);
        @(negedge PCLK);

        apb_write(ADDR_CTRL, CTRL_ENABLE | CTRL_UP_DOWN);
        repeat(10) @(negedge PCLK);

        apb_write(ADDR_CTRL, 32'd0);
        apb_read(ADDR_COUNT_LO, rd_data);
        check(rd_data >= 32'd10 && rd_data <= 32'd16,
              "Count up: low word near expected value");
        apb_read(ADDR_COUNT_HI, rd_data);
        check(rd_data == 32'd0, "Count up: high word still zero");

        @(negedge PCLK);

        //======================================================================
        // Test 5: Count down from 100
        //======================================================================
        $display("\n--- Test 5: Count down ---");

        apb_write(ADDR_COUNT_LO, 32'd100);
        apb_write(ADDR_COUNT_HI, 32'd0);
        apb_write(ADDR_CTRL, CTRL_LOAD);
        @(negedge PCLK);

        apb_write(ADDR_CTRL, CTRL_ENABLE);
        repeat(10) @(negedge PCLK);

        apb_write(ADDR_CTRL, 32'd0);
        apb_read(ADDR_COUNT_LO, rd_data);
        check(rd_data >= 32'd84 && rd_data <= 32'd92,
              "Count down: low word near expected value");
        apb_read(ADDR_COUNT_HI, rd_data);
        check(rd_data == 32'd0, "Count down: high word still zero");

        @(negedge PCLK);

        //======================================================================
        // Test 6: Terminal count on overflow
        //======================================================================
        $display("\n--- Test 6: Overflow TC ---");

        apb_read(ADDR_TC_STATUS, rd_data);

        apb_write(ADDR_COUNT_LO, 32'hFFFFFFFE);
        apb_write(ADDR_COUNT_HI, 32'hFFFFFFFF);
        apb_write(ADDR_CTRL, CTRL_LOAD);
        @(negedge PCLK);

        apb_write(ADDR_CTRL, CTRL_ENABLE | CTRL_UP_DOWN);
        repeat(10) @(negedge PCLK);

        apb_write(ADDR_CTRL, 32'd0);

        apb_read(ADDR_TC_STATUS, rd_data);
        check(rd_data[0] == 1'b1, "Overflow: tc_sticky set");

        // Counter wrapped from 0xFFFE to 0 then counted up ~11 more
        apb_read(ADDR_COUNT_LO, rd_data);
        check(rd_data < 32'd20, "Overflow: low word wrapped to small value");
        apb_read(ADDR_COUNT_HI, rd_data);
        check(rd_data == 32'd0, "Overflow: high word wrapped to zero");

        @(negedge PCLK);

        //======================================================================
        // Test 7: Terminal count on underflow
        //======================================================================
        $display("\n--- Test 7: Underflow TC ---");

        apb_read(ADDR_TC_STATUS, rd_data);

        apb_write(ADDR_COUNT_LO, 32'd1);
        apb_write(ADDR_COUNT_HI, 32'd0);
        apb_write(ADDR_CTRL, CTRL_LOAD);
        @(negedge PCLK);

        apb_write(ADDR_CTRL, CTRL_ENABLE);
        repeat(10) @(negedge PCLK);

        apb_write(ADDR_CTRL, 32'd0);

        apb_read(ADDR_TC_STATUS, rd_data);
        check(rd_data[0] == 1'b1, "Underflow: tc_sticky set");

        apb_read(ADDR_COUNT_LO, rd_data);
        check(rd_data > 32'hFFFFFFF0, "Underflow: low word near max");
        apb_read(ADDR_COUNT_HI, rd_data);
        check(rd_data == 32'hFFFFFFFF, "Underflow: high word is all 1s");

        @(negedge PCLK);

        //======================================================================
        // Test 8: Pause/resume
        //======================================================================
        $display("\n--- Test 8: Pause/resume ---");

        apb_read(ADDR_TC_STATUS, rd_data);

        apb_write(ADDR_COUNT_LO, 32'd0);
        apb_write(ADDR_COUNT_HI, 32'd0);
        apb_write(ADDR_CTRL, CTRL_LOAD);
        @(negedge PCLK);

        apb_write(ADDR_CTRL, CTRL_ENABLE | CTRL_UP_DOWN);
        repeat(20) @(negedge PCLK);

        apb_write(ADDR_CTRL, 32'd0);
        apb_read(ADDR_COUNT_LO, rd_data);
        check(rd_data >= 32'd18 && rd_data <= 32'd26,
              "Pause: count near expected after 20 ticks");

        repeat(10) @(negedge PCLK);
        apb_read(ADDR_COUNT_LO, rd_data);
        check(rd_data >= 32'd18 && rd_data <= 32'd26,
              "Pause: count unchanged during idle");

        apb_write(ADDR_CTRL, CTRL_ENABLE | CTRL_UP_DOWN);
        repeat(20) @(negedge PCLK);

        apb_write(ADDR_CTRL, 32'd0);
        apb_read(ADDR_COUNT_LO, rd_data);
        check(rd_data >= 32'd38 && rd_data <= 32'd52,
              "Resume: count increased after resume");

        @(negedge PCLK);

        //======================================================================
        // Test 9: TC clear-on-read + IRQ
        //======================================================================
        $display("\n--- Test 9: TC clear-on-read + IRQ ---");

        apb_read(ADDR_TC_STATUS, rd_data);

        apb_write(ADDR_COUNT_LO, 32'd1);
        apb_write(ADDR_COUNT_HI, 32'd0);
        apb_write(ADDR_CTRL, CTRL_LOAD);
        @(negedge PCLK);
        apb_write(ADDR_CTRL, CTRL_ENABLE);
        repeat(5) @(negedge PCLK);
        apb_write(ADDR_CTRL, 32'd0);

        check(irq == 1'b1, "IRQ: asserted after underflow");

        apb_read(ADDR_TC_STATUS, rd_data);
        check(rd_data[0] == 1'b1, "IRQ: tc_sticky set before clear");

        check(irq == 1'b0, "IRQ: deasserted after TC_STATUS read");

        apb_read(ADDR_TC_STATUS, rd_data);
        check(rd_data[0] == 1'b0, "IRQ: tc_sticky cleared after read");

        @(negedge PCLK);

        //======================================================================
        // Test 10: Invalid address returns 0
        //======================================================================
        $display("\n--- Test 10: Invalid address ---");
        apb_read(8'h14, rd_data);
        check(rd_data == 32'd0, "BadAddr: unmapped returns 0");

        apb_read(8'hFC, rd_data);
        check(rd_data == 32'd0, "BadAddr: high address returns 0");

        //======================================================================
        // Test 11: Write to read-only TC_STATUS ignored
        //======================================================================
        $display("\n--- Test 11: Write to RO TC_STATUS ---");

        apb_read(ADDR_TC_STATUS, rd_data);
        check(rd_data[0] == 1'b0, "RO: tc_sticky is 0 before write");

        apb_write(ADDR_TC_STATUS, 32'hFFFFFFFF);

        apb_read(ADDR_TC_STATUS, rd_data);
        check(rd_data[0] == 1'b0, "RO: write to TC_STATUS ignored");

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
