
`timescale 1ns / 1ps

//----------------------------------------------------------------------------
// Module: tb_dma
// Description: Self-checking testbench for DMA controller.
//
// Architecture:
//   Testbench (APB) → DMA → AHB Master → SRAM (direct, no decoder)
//   HGRANT follows HBUSREQ with 1-cycle delay (simple arbiter model)
//
// Uses backdoor access (hierarchical) to preload/verify SRAM contents.
//
// Tests:
//   1. Register reset values and read/write
//   2. Single-word DMA transfer
//   3. Multi-word (4-word) DMA transfer
//   4. Interrupt assertion and clearing
//----------------------------------------------------------------------------

module tb_dma;

    //--------------------------------------------------------------------------
    // Parameters
    //--------------------------------------------------------------------------
    localparam CLK_PERIOD = 10;

    //--------------------------------------------------------------------------
    // Signals
    //--------------------------------------------------------------------------
    reg         HCLK;
    reg         HRESETn;

    // APB slave interface (testbench drives)
    reg         PSEL;
    reg         PENABLE;
    reg         PWRITE;
    reg  [7:0]  PADDR;
    reg  [31:0] PWDATA;
    wire [31:0] PRDATA;
    wire        PREADY;
    wire        PSLVERR;

    // AHB master interface (DMA drives)
    wire [31:0] dma_haddr;
    wire [31:0] dma_hwdata;
    wire        dma_hwrite;
    wire [1:0]  dma_htrans;
    wire [2:0]  dma_hsize;
    wire        dma_hbusreq;
    reg         dma_hgrant;
    wire [31:0] dma_hrdata;
    wire        dma_hready;

    // SRAM signals
    wire [31:0] sram_hrdata;
    wire        sram_hreadyout;

    // Interrupt
    wire        dma_irq;

    // Test tracking
    integer     tests_passed = 0;
    integer     tests_failed = 0;
    reg  [31:0] rd_data;

    //--------------------------------------------------------------------------
    // DUT: DMA Controller
    //--------------------------------------------------------------------------
    dma u_dma (
        .HCLK      (HCLK),
        .HRESETn   (HRESETn),

        .PSEL      (PSEL),
        .PENABLE   (PENABLE),
        .PWRITE    (PWRITE),
        .PADDR     (PADDR),
        .PWDATA    (PWDATA),
        .PRDATA    (PRDATA),
        .PREADY    (PREADY),
        .PSLVERR   (PSLVERR),

        .HADDR     (dma_haddr),
        .HWDATA    (dma_hwdata),
        .HRDATA    (dma_hrdata),
        .HWRITE    (dma_hwrite),
        .HTRANS    (dma_htrans),
        .HSIZE     (dma_hsize),
        .HBUSREQ   (dma_hbusreq),
        .HGRANT    (dma_hgrant),
        .HREADY    (dma_hready),

        .dma_irq   (dma_irq)
    );

    //--------------------------------------------------------------------------
    // SRAM (only AHB slave in this test)
    //--------------------------------------------------------------------------
    sram u_sram (
        .HCLK      (HCLK),
        .HRESETn   (HRESETn),
        .HSEL      (dma_htrans[1]),    // Selected during valid transfers
        .HADDR     (dma_haddr),
        .HWDATA    (dma_hwdata),
        .HRDATA    (sram_hrdata),
        .HWRITE    (dma_hwrite),
        .HTRANS    (dma_htrans),
        .HSIZE     (dma_hsize),
        .HREADYOUT (sram_hreadyout),
        .HRESP     (),
        .HREADY    (1'b1)              // Always ready (single slave)
    );

    // Connect SRAM response back to DMA
    assign dma_hrdata = sram_hrdata;
    assign dma_hready = sram_hreadyout;  // Always 1

    //--------------------------------------------------------------------------
    // Simple arbiter model: HGRANT follows HBUSREQ with 1-cycle delay
    //--------------------------------------------------------------------------
    always @(posedge HCLK) begin
        if (!HRESETn)
            dma_hgrant <= 1'b0;
        else
            dma_hgrant <= dma_hbusreq;
    end

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
        $dumpfile("dma.vcd");
        $dumpvars(0, tb_dma);
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
    // APB Write task
    //--------------------------------------------------------------------------
    task apb_write;
        input [7:0]  addr;
        input [31:0] data;
        begin
            @(negedge HCLK);
            PADDR   = addr;
            PWDATA  = data;
            PWRITE  = 1'b1;
            PSEL    = 1'b1;
            PENABLE = 1'b0;     // SETUP phase
            @(negedge HCLK);
            PENABLE = 1'b1;     // ACCESS phase
            @(negedge HCLK);
            PSEL    = 1'b0;     // IDLE
            PENABLE = 1'b0;
            PWRITE  = 1'b0;
        end
    endtask

    //--------------------------------------------------------------------------
    // APB Read task
    //--------------------------------------------------------------------------
    task apb_read;
        input  [7:0]  addr;
        output [31:0] data;
        begin
            @(negedge HCLK);
            PADDR   = addr;
            PWRITE  = 1'b0;
            PSEL    = 1'b1;
            PENABLE = 1'b0;     // SETUP phase
            @(negedge HCLK);
            PENABLE = 1'b1;     // ACCESS phase
            @(negedge HCLK);
            data    = PRDATA;   // Capture read data
            PSEL    = 1'b0;
            PENABLE = 1'b0;
        end
    endtask

    //--------------------------------------------------------------------------
    // SRAM backdoor write (hierarchical, simulation only)
    //--------------------------------------------------------------------------
    task sram_poke;
        input [13:0] word_addr;
        input [31:0] data;
        begin
            u_sram.mem[word_addr] = data;
        end
    endtask

    //--------------------------------------------------------------------------
    // SRAM backdoor read (hierarchical, simulation only)
    //--------------------------------------------------------------------------
    task sram_peek;
        input  [13:0] word_addr;
        output [31:0] data;
        begin
            data = u_sram.mem[word_addr];
        end
    endtask

    //--------------------------------------------------------------------------
    // Wait for DMA completion via interrupt
    //--------------------------------------------------------------------------
    task wait_dma_done;
        integer timeout;
        begin
            timeout = 0;
            while (!dma_irq && timeout < 200) begin
                @(negedge HCLK);
                timeout = timeout + 1;
            end
            check(dma_irq, "DMA completed within timeout");
        end
    endtask

    //--------------------------------------------------------------------------
    // Reset helper
    //--------------------------------------------------------------------------
    task do_reset;
        begin
            HRESETn = 1'b0;
            PSEL = 1'b0;
            PENABLE = 1'b0;
            PWRITE = 1'b0;
            repeat(3) @(negedge HCLK);
            HRESETn = 1'b1;
            repeat(2) @(negedge HCLK);
        end
    endtask

    //--------------------------------------------------------------------------
    // Main test sequence
    //--------------------------------------------------------------------------
    initial begin
        $display("========================================");
        $display(" DMA Testbench Starting...");
        $display("========================================");

        do_reset();

        //======================================================================
        // Test 1: Register reset values
        //======================================================================
        $display("\n--- Test 1: Register reset values ---");

        apb_read(8'h00, rd_data);  // SRC_ADDR
        check(rd_data == 32'd0, "Reset: SRC_ADDR = 0");

        apb_read(8'h04, rd_data);  // DST_ADDR
        check(rd_data == 32'd0, "Reset: DST_ADDR = 0");

        apb_read(8'h08, rd_data);  // COUNT
        check(rd_data == 32'd0, "Reset: COUNT = 0");

        apb_read(8'h0C, rd_data);  // CONTROL
        check(rd_data == 32'd0, "Reset: CONTROL = 0");

        apb_read(8'h10, rd_data);  // STATUS
        check(rd_data[0] == 1'b0, "Reset: STATUS.busy = 0");
        check(rd_data[1] == 1'b0, "Reset: STATUS.done = 0");

        check(PREADY == 1'b1, "Reset: PREADY = 1");
        check(PSLVERR == 1'b0, "Reset: PSLVERR = 0");
        check(dma_irq == 1'b0, "Reset: dma_irq = 0");

        //======================================================================
        // Test 2: Register write/read
        //======================================================================
        $display("\n--- Test 2: Register write/read ---");

        apb_write(8'h00, 32'h0000_1000);
        apb_read(8'h00, rd_data);
        check(rd_data == 32'h0000_1000, "R/W: SRC_ADDR = 0x0000_1000");

        apb_write(8'h04, 32'h0000_2000);
        apb_read(8'h04, rd_data);
        check(rd_data == 32'h0000_2000, "R/W: DST_ADDR = 0x0000_2000");

        apb_write(8'h08, 32'd4);
        apb_read(8'h08, rd_data);
        check(rd_data == 32'd4, "R/W: COUNT = 4");

        //======================================================================
        // Test 3: Single-word DMA transfer
        //======================================================================
        $display("\n--- Test 3: Single-word DMA transfer ---");

        do_reset();

        // Preload SRAM word 0
        sram_poke(14'd0, 32'hDEAD_BEEF);

        // Configure and start DMA
        apb_write(8'h00, 32'h0000_0000);  // SRC: word 0 (addr 0x00)
        apb_write(8'h04, 32'h0000_0100);  // DST: word 64 (addr 0x100)
        apb_write(8'h08, 32'd1);           // COUNT: 1
        apb_write(8'h0C, 32'h03);          // CONTROL: start + irq_en

        // Wait for completion
        wait_dma_done();

        // Verify destination via backdoor
        sram_peek(14'd64, rd_data);
        check(rd_data == 32'hDEAD_BEEF, "Single: dst[64] = 0xDEAD_BEEF");

        // Verify source unchanged
        sram_peek(14'd0, rd_data);
        check(rd_data == 32'hDEAD_BEEF, "Single: src[0] unchanged");

        // Clear interrupt via STATUS read
        apb_read(8'h10, rd_data);
        check(rd_data[0] == 1'b0, "Single: STATUS.busy = 0 after done");

        @(negedge HCLK);
        check(dma_irq == 1'b0, "Single: irq cleared after STATUS read");

        //======================================================================
        // Test 4: Multi-word DMA transfer (4 words)
        //======================================================================
        $display("\n--- Test 4: Multi-word DMA transfer ---");

        do_reset();

        // Preload SRAM words 0-3
        sram_poke(14'd0, 32'h1111_1111);
        sram_poke(14'd1, 32'h2222_2222);
        sram_poke(14'd2, 32'h3333_3333);
        sram_poke(14'd3, 32'h4444_4444);

        // Configure and start DMA
        apb_write(8'h00, 32'h0000_0000);  // SRC: word 0
        apb_write(8'h04, 32'h0000_0200);  // DST: word 128 (addr 0x200)
        apb_write(8'h08, 32'd4);           // COUNT: 4
        apb_write(8'h0C, 32'h03);          // CONTROL: start + irq_en

        // Wait for completion
        wait_dma_done();

        // Verify all 4 destination words
        sram_peek(14'd128, rd_data);
        check(rd_data == 32'h1111_1111, "Multi: dst[128] = 0x1111_1111");
        sram_peek(14'd129, rd_data);
        check(rd_data == 32'h2222_2222, "Multi: dst[129] = 0x2222_2222");
        sram_peek(14'd130, rd_data);
        check(rd_data == 32'h3333_3333, "Multi: dst[130] = 0x3333_3333");
        sram_peek(14'd131, rd_data);
        check(rd_data == 32'h4444_4444, "Multi: dst[131] = 0x4444_4444");

        // Verify source unchanged
        sram_peek(14'd0, rd_data);
        check(rd_data == 32'h1111_1111, "Multi: src[0] unchanged");

        //======================================================================
        // Test 5: Interrupt behavior
        //======================================================================
        $display("\n--- Test 5: Interrupt behavior ---");

        // IRQ should still be asserted from test 4
        check(dma_irq == 1'b1, "IRQ: asserted after multi-word transfer");

        // Read STATUS to clear done
        apb_read(8'h10, rd_data);
        check(rd_data[0] == 1'b0, "IRQ: STATUS.busy = 0");
        // Note: done bit was 1 but cleared by this read

        @(negedge HCLK);
        check(dma_irq == 1'b0, "IRQ: deasserted after STATUS read");

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
