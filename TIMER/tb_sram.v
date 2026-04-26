
`timescale 1ns / 1ps

//----------------------------------------------------------------------------
// Module: tb_sram
// Description: Self-checking testbench for SRAM AHB-Lite slave.
//
// Tests:
//   1. Reset state - HRDATA is 0
//   2. Single write and readback
//   3. Multiple locations (first, middle, last)
//   4. Distinct data patterns
//   5. Overwrite test
//   6. Sequential write-read sweep
//----------------------------------------------------------------------------

module tb_sram;

    //--------------------------------------------------------------------------
    // Parameters
    //--------------------------------------------------------------------------
    localparam CLK_PERIOD = 10;

    //--------------------------------------------------------------------------
    // Signals
    //--------------------------------------------------------------------------
    reg         HCLK;
    reg         HRESETn;
    reg         HSEL;
    reg  [31:0] HADDR;
    reg  [31:0] HWDATA;
    wire [31:0] HRDATA;
    reg         HWRITE;
    reg  [1:0]  HTRANS;
    reg  [2:0]  HSIZE;
    wire        HREADYOUT;
    wire        HRESP;
    reg         HREADY;

    // Test tracking
    integer     tests_passed = 0;
    integer     tests_failed = 0;
    reg  [31:0] rd_data;

    //--------------------------------------------------------------------------
    // DUT
    //--------------------------------------------------------------------------
    sram dut (
        .HCLK      (HCLK),
        .HRESETn   (HRESETn),
        .HSEL      (HSEL),
        .HADDR     (HADDR),
        .HWDATA    (HWDATA),
        .HRDATA    (HRDATA),
        .HWRITE    (HWRITE),
        .HTRANS    (HTRANS),
        .HSIZE     (HSIZE),
        .HREADYOUT (HREADYOUT),
        .HRESP     (HRESP),
        .HREADY    (HREADY)
    );

    //--------------------------------------------------------------------------
    // Clock generator
    //--------------------------------------------------------------------------
    initial begin
        HCLK = 1'b0;
        forever #(CLK_PERIOD/2) HCLK = ~HCLK;
    end

    //--------------------------------------------------------------------------
    // Waveform dump
    //--------------------------------------------------------------------------
    initial begin
        $dumpfile("sram.vcd");
        $dumpvars(0, tb_sram);
    end

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
                $display("       Time: %0t", $time);
                tests_failed = tests_failed + 1;
            end
        end
    endtask

    //--------------------------------------------------------------------------
    // AHB Write task (single-cycle, direct to SRAM)
    //--------------------------------------------------------------------------
    task sram_write;
        input [31:0] addr;
        input [31:0] data;
        begin
            @(negedge HCLK);
            HADDR  = addr;
            HWDATA = data;
            HWRITE = 1'b1;
            HTRANS = 2'b10;   // NONSEQ
            HSEL   = 1'b1;
            @(negedge HCLK);  // SRAM samples at intervening posedge
            HTRANS = 2'b00;   // IDLE
            HWRITE = 1'b0;
            HSEL   = 1'b0;
        end
    endtask

    //--------------------------------------------------------------------------
    // AHB Read task (single-cycle, direct to SRAM)
    //--------------------------------------------------------------------------
    task sram_read;
        input  [31:0] addr;
        output [31:0] data;
        begin
            @(negedge HCLK);
            HADDR  = addr;
            HWRITE = 1'b0;
            HTRANS = 2'b10;   // NONSEQ
            HSEL   = 1'b1;
            @(negedge HCLK);  // SRAM captures data at intervening posedge
            data   = HRDATA;  // Read data is now valid
            HTRANS = 2'b00;   // IDLE
            HSEL   = 1'b0;
        end
    endtask

    //--------------------------------------------------------------------------
    // Main test sequence
    //--------------------------------------------------------------------------
    initial begin
        $display("========================================");
        $display(" SRAM Testbench Starting...");
        $display("========================================");

        // Initialize
        HRESETn = 1'b0;
        HSEL    = 1'b0;
        HADDR   = 32'd0;
        HWDATA  = 32'd0;
        HWRITE  = 1'b0;
        HTRANS  = 2'b00;
        HSIZE   = 3'b010;
        HREADY  = 1'b1;

        repeat(5) @(negedge HCLK);
        HRESETn = 1'b1;
        repeat(2) @(negedge HCLK);

        //======================================================================
        // Test 1: Reset state - HRDATA should be 0
        //======================================================================
        $display("\n--- Test 1: Reset state ---");

        check(HRDATA == 32'd0, "Reset: HRDATA is 0");
        check(HREADYOUT == 1'b1, "Reset: HREADYOUT is 1");
        check(HRESP == 1'b0, "Reset: HRESP is 0");

        //======================================================================
        // Test 2: Single write and readback
        //======================================================================
        $display("\n--- Test 2: Single write/read ---");

        sram_write(32'h0000_0000, 32'hDEADBEEF);
        sram_read(32'h0000_0000, rd_data);
        check(rd_data == 32'hDEADBEEF, "Single write/read: data matches 0xDEADBEEF");

        //======================================================================
        // Test 3: Multiple locations
        //======================================================================
        $display("\n--- Test 3: Multiple locations ---");

        // Write to first, middle, and last addresses
        sram_write(32'h0000_0000, 32'hAAAA_0001);   // Word 0
        sram_write(32'h0000_8000, 32'hAAAA_0002);   // Word 8192 (middle)
        sram_write(32'h0000_FFFC, 32'hAAAA_0003);   // Word 16383 (last)

        sram_read(32'h0000_0000, rd_data);
        check(rd_data == 32'hAAAA_0001, "Multi-location: addr 0x0000 = 0xAAAA_0001");

        sram_read(32'h0000_8000, rd_data);
        check(rd_data == 32'hAAAA_0002, "Multi-location: addr 0x8000 = 0xAAAA_0002");

        sram_read(32'h0000_FFFC, rd_data);
        check(rd_data == 32'hAAAA_0003, "Multi-location: addr 0xFFFC = 0xAAAA_0003");

        //======================================================================
        // Test 4: Distinct data patterns
        //======================================================================
        $display("\n--- Test 4: Data patterns ---");

        sram_write(32'h0000_0100, 32'h1234_5678);
        sram_write(32'h0000_0104, 32'hFFFF_FFFF);
        sram_write(32'h0000_0108, 32'h0000_0000);
        sram_write(32'h0000_010C, 32'h8000_0001);

        sram_read(32'h0000_0100, rd_data);
        check(rd_data == 32'h1234_5678, "Patterns: 0x1234_5678");

        sram_read(32'h0000_0104, rd_data);
        check(rd_data == 32'hFFFF_FFFF, "Patterns: 0xFFFF_FFFF (all ones)");

        sram_read(32'h0000_0108, rd_data);
        check(rd_data == 32'h0000_0000, "Patterns: 0x0000_0000 (all zeros)");

        sram_read(32'h0000_010C, rd_data);
        check(rd_data == 32'h8000_0001, "Patterns: 0x8000_0001 (MSB set)");

        //======================================================================
        // Test 5: Overwrite test
        //======================================================================
        $display("\n--- Test 5: Overwrite ---");

        sram_write(32'h0000_0200, 32'hAAAA_AAAA);
        sram_write(32'h0000_0200, 32'h5555_5555);
        sram_read(32'h0000_0200, rd_data);
        check(rd_data == 32'h5555_5555, "Overwrite: second write wins");

        //======================================================================
        // Test 6: Sequential sweep (8 words)
        //======================================================================
        $display("\n--- Test 6: Sequential sweep ---");

        // Write 8 consecutive words
        sram_write(32'h0000_0400, 32'd10);
        sram_write(32'h0000_0404, 32'd20);
        sram_write(32'h0000_0408, 32'd30);
        sram_write(32'h0000_040C, 32'd40);
        sram_write(32'h0000_0410, 32'd50);
        sram_write(32'h0000_0414, 32'd60);
        sram_write(32'h0000_0418, 32'd70);
        sram_write(32'h0000_041C, 32'd80);

        // Read back and verify
        sram_read(32'h0000_0400, rd_data);
        check(rd_data == 32'd10, "Sweep: word 0 = 10");
        sram_read(32'h0000_0404, rd_data);
        check(rd_data == 32'd20, "Sweep: word 1 = 20");
        sram_read(32'h0000_0408, rd_data);
        check(rd_data == 32'd30, "Sweep: word 2 = 30");
        sram_read(32'h0000_040C, rd_data);
        check(rd_data == 32'd40, "Sweep: word 3 = 40");
        sram_read(32'h0000_0410, rd_data);
        check(rd_data == 32'd50, "Sweep: word 4 = 50");
        sram_read(32'h0000_0414, rd_data);
        check(rd_data == 32'd60, "Sweep: word 5 = 60");
        sram_read(32'h0000_0418, rd_data);
        check(rd_data == 32'd70, "Sweep: word 6 = 70");
        sram_read(32'h0000_041C, rd_data);
        check(rd_data == 32'd80, "Sweep: word 7 = 80");

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
