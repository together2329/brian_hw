
`timescale 1ns / 1ps

//----------------------------------------------------------------------------
// Module: tb_spi
// Description: Self-checking testbench for SPI master via APB interface.
//              Uses loopback (mosi connected to miso) for full datapath
//              verification.
//----------------------------------------------------------------------------

module tb_spi;

    //--------------------------------------------------------------------------
    // Parameters
    //--------------------------------------------------------------------------
    localparam CLK_PERIOD = 10;
    localparam CLK_DIV    = 4;   // 4 system clocks per SCK half-period

    // APB register offsets
    localparam [7:0] TX_DATA  = 8'h00;
    localparam [7:0] RX_DATA  = 8'h04;
    localparam [7:0] CTRL     = 8'h08;
    localparam [7:0] STATUS   = 8'h0C;
    localparam [7:0] CLK_DIV_REG = 8'h10;

    //--------------------------------------------------------------------------
    // Signals
    //--------------------------------------------------------------------------
    reg         PCLK;
    reg         PRESETn;
    reg  [7:0]  PADDR;
    reg  [31:0] PWDATA;
    wire [31:0] PRDATA;
    reg         PSEL;
    reg         PENABLE;
    reg         PWRITE;

    // SPI pins with loopback
    wire        mosi;
    wire        sck;
    wire        cs_n;
    wire        irq;
    wire        miso;

    // Loopback: MOSI feeds back to MISO
    assign miso = mosi;

    // Test tracking
    integer     tests_passed = 0;
    integer     tests_failed = 0;
    reg  [31:0] rd_data;

    //--------------------------------------------------------------------------
    // DUT
    //--------------------------------------------------------------------------
    spi_apb dut (
        .PCLK    (PCLK),
        .PRESETn (PRESETn),
        .PSEL    (PSEL),
        .PENABLE (PENABLE),
        .PWRITE  (PWRITE),
        .PADDR   (PADDR),
        .PWDATA  (PWDATA),
        .PRDATA  (PRDATA),
        .PREADY  (),
        .PSLVERR (),
        .miso    (miso),
        .mosi    (mosi),
        .sck     (sck),
        .cs_n    (cs_n),
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
        $dumpfile("spi.vcd");
        $dumpvars(0, tb_spi);
    end

    //--------------------------------------------------------------------------
    // Include APB bus tasks
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
                $display("       Time: %0t, Value: 0x%08h", $time, rd_data);
                tests_failed = tests_failed + 1;
            end
        end
    endtask

    //--------------------------------------------------------------------------
    // Wait for transfer complete task
    //   Waits for busy to clear (with timeout)
    //   Returns 1 if transfer completed, 0 if timeout
    //--------------------------------------------------------------------------
    task wait_not_busy;
        output       ok;
        reg          ok;
        reg [31:0]   cnt;
        begin
            ok = 1'b0;
            for (cnt = 0; cnt < 20 * CLK_DIV; cnt = cnt + 1) begin
                @(negedge PCLK);
                apb_read(STATUS, rd_data);
                if (rd_data[0] == 1'b0) begin
                    ok = 1'b1;
                    cnt = 32'hFFFFFFFE;  // Break
                end
            end
        end
    endtask

    //--------------------------------------------------------------------------
    // Send byte and verify loopback
    //--------------------------------------------------------------------------
    task send_and_check;
        input [7:0] send_byte;
        reg         ok;
        begin
            apb_write(TX_DATA, {24'd0, send_byte});
            wait_not_busy(ok);
            apb_read(STATUS, rd_data);
            check(rd_data[1] == 1'b1, "SPI loopback: rx_ready");
            apb_read(RX_DATA, rd_data);
            check(rd_data[7:0] == send_byte, "SPI loopback: data match");
            apb_read(RX_DATA, rd_data);  // Clear rx_ready
        end
    endtask

    //--------------------------------------------------------------------------
    // Main test sequence
    //--------------------------------------------------------------------------
    initial begin
        $display("========================================");
        $display(" SPI APB Testbench Starting...");
        $display("========================================");

        // Initialize
        PRESETn = 1'b0;
        PADDR   = 8'd0;
        PWDATA  = 32'd0;
        PSEL    = 1'b0;
        PENABLE = 1'b0;
        PWRITE  = 1'b0;

        repeat(5) @(negedge PCLK);
        PRESETn = 1'b1;
        repeat(2) @(negedge PCLK);

        //======================================================================
        // Test 1: Reset verification
        //======================================================================
        $display("\n--- Test 1: Reset ---");

        apb_read(CTRL, rd_data);
        check(rd_data[2:0] == 3'b000, "Reset: CTRL is zero");

        apb_read(STATUS, rd_data);
        check(rd_data[0] == 1'b0, "Reset: not busy");
        check(rd_data[1] == 1'b0, "Reset: rx not ready");

        apb_read(CLK_DIV_REG, rd_data);
        check(rd_data[15:0] == 16'd2, "Reset: CLK_DIV default is 2");

        check(irq == 1'b0, "Reset: IRQ low");
        check(cs_n == 1'b1, "Reset: CS_n high (deselected)");

        //======================================================================
        // Test 2: Register R/W
        //======================================================================
        $display("\n--- Test 2: Register R/W ---");

        // Set CLK_DIV
        apb_write(CLK_DIV_REG, CLK_DIV);
        apb_read(CLK_DIV_REG, rd_data);
        check(rd_data[15:0] == CLK_DIV, "CLK_DIV: set to test value");

        // Set CTRL: enable=1, cpol=0, cpha=0 (mode 0)
        apb_write(CTRL, 32'h1);  // enable only
        apb_read(CTRL, rd_data);
        check(rd_data[2:0] == 3'b001, "CTRL: enable set");

        // Set mode 0 with enable
        apb_write(CTRL, 32'h1);  // enable, cpol=0, cpha=0
        apb_read(CTRL, rd_data);
        check(rd_data[2:0] == 3'b001, "CTRL: mode 0 (cpol=0, cpha=0)");

        @(negedge PCLK);

        //======================================================================
        // Test 3: SPI Mode 0 loopback
        //======================================================================
        $display("\n--- Test 3: Mode 0 loopback ---");

        send_and_check(8'h55);
        send_and_check(8'hA5);
        send_and_check(8'h00);
        send_and_check(8'hFF);

        //======================================================================
        // Test 4: Busy and done status
        //======================================================================
        $display("\n--- Test 4: Busy/done status ---");

        apb_write(TX_DATA, 32'hC3);

        // Immediately check busy
        apb_read(STATUS, rd_data);
        check(rd_data[0] == 1'b1, "SPI: busy after TX_DATA write");

        // Wait for completion
        wait_not_busy(/*ok=*/rd_data[0]);
        apb_read(STATUS, rd_data);
        check(rd_data[0] == 1'b0, "SPI: not busy after transfer");
        check(rd_data[1] == 1'b1, "SPI: rx_ready after transfer");
        check(irq == 1'b1, "SPI: IRQ asserted");

        apb_read(RX_DATA, rd_data);
        check(rd_data[7:0] == 8'hC3, "SPI: received 0xC3");
        check(irq == 1'b0, "SPI: IRQ cleared after RX read");

        @(negedge PCLK);

        //======================================================================
        // Test 5: SPI Mode 1 (CPOL=0, CPHA=1)
        //======================================================================
        $display("\n--- Test 5: Mode 1 loopback ---");

        apb_write(CTRL, 32'h5);  // enable + cpha=1
        apb_read(CTRL, rd_data);
        check(rd_data[2:0] == 3'b101, "CTRL: mode 1 (cpol=0, cpha=1)");

        send_and_check(8'h55);
        send_and_check(8'hAA);

        //======================================================================
        // Test 6: SPI Mode 2 (CPOL=1, CPHA=0)
        //======================================================================
        $display("\n--- Test 6: Mode 2 loopback ---");

        apb_write(CTRL, 32'h3);  // enable + cpol=1
        apb_read(CTRL, rd_data);
        check(rd_data[2:0] == 3'b011, "CTRL: mode 2 (cpol=1, cpha=0)");

        send_and_check(8'h42);

        //======================================================================
        // Test 7: SPI Mode 3 (CPOL=1, CPHA=1)
        //======================================================================
        $display("\n--- Test 7: Mode 3 loopback ---");

        apb_write(CTRL, 32'h7);  // enable + cpol=1 + cpha=1
        apb_read(CTRL, rd_data);
        check(rd_data[2:0] == 3'b111, "CTRL: mode 3 (cpol=1, cpha=1)");

        send_and_check(8'h81);

        //======================================================================
        // Test 8: TX disabled
        //======================================================================
        $display("\n--- Test 8: TX disabled ---");

        // Disable SPI
        apb_write(CTRL, 32'h0);
        apb_write(TX_DATA, 32'h12);

        repeat(10) @(negedge PCLK);
        apb_read(STATUS, rd_data);
        check(rd_data[0] == 1'b0, "SPI disabled: not busy");
        check(rd_data[1] == 1'b0, "SPI disabled: no rx_ready");

        // Re-enable
        apb_write(CTRL, 32'h1);

        @(negedge PCLK);

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
