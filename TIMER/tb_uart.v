
`timescale 1ns / 1ps

//----------------------------------------------------------------------------
// Module: tb_uart
// Description: Self-checking testbench for UART via APB interface.
//              Uses loopback (tx_out connected to rx_in) for full datapath
//              verification.
//----------------------------------------------------------------------------

module tb_uart;

    //--------------------------------------------------------------------------
    // Parameters
    //--------------------------------------------------------------------------
    localparam CLK_PERIOD = 10;
    localparam BAUD_DIV   = 16;  // 16 clocks per bit

    // APB register offsets
    localparam [7:0] TX_DATA   = 8'h00;
    localparam [7:0] RX_DATA   = 8'h04;
    localparam [7:0] CTRL      = 8'h08;
    localparam [7:0] STATUS    = 8'h0C;
    localparam [7:0] BAUD_DIV_REG = 8'h10;

    // STATUS bits
    localparam TX_BUSY    = 0;
    localparam TX_EMPTY   = 1;
    localparam RX_READY   = 2;
    localparam RX_OVERFLOW = 3;

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

    // UART serial loopback
    wire        tx_out;
    wire        rx_in;
    wire        irq;
    wire        rx_overflow;

    // Loopback connection
    assign rx_in = tx_out;

    // Test tracking
    integer     tests_passed = 0;
    integer     tests_failed = 0;
    reg  [31:0] rd_data;

    //--------------------------------------------------------------------------
    // DUT
    //--------------------------------------------------------------------------
    uart_apb dut (
        .PCLK        (PCLK),
        .PRESETn     (PRESETn),
        .PSEL        (PSEL),
        .PENABLE     (PENABLE),
        .PWRITE      (PWRITE),
        .PADDR       (PADDR),
        .PWDATA      (PWDATA),
        .PRDATA      (PRDATA),
        .PREADY      (),
        .PSLVERR     (),
        .rx_in       (rx_in),
        .tx_out      (tx_out),
        .irq         (irq),
        .rx_overflow (rx_overflow)
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
        $dumpfile("uart.vcd");
        $dumpvars(0, tb_uart);
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
    // Poll task: wait for STATUS bit with timeout
    //   bit_pos : which bit to check
    //   expected: 0 or 1
    //   max_wait: maximum clock cycles to wait
    //   returns : 1 if found, 0 if timeout
    //--------------------------------------------------------------------------
    task poll_status;
        input [3:0]  bit_pos;
        input        expected;
        input [31:0] max_wait;
        output       found;
        reg          found;
        reg [31:0]   cnt;
        begin
            found = 1'b0;
            for (cnt = 0; cnt < max_wait; cnt = cnt + 1) begin
                @(negedge PCLK);
                apb_read(STATUS, rd_data);
                if (rd_data[bit_pos] === expected) begin
                    found = 1'b1;
                    cnt = max_wait;  // Break
                end
            end
        end
    endtask

    //--------------------------------------------------------------------------
    // Send byte and receive via loopback task
    //--------------------------------------------------------------------------
    task send_and_receive;
        input [7:0] send_byte;
        output [7:0] recv_byte;
        reg [7:0]    recv_byte;
        reg          found;
        begin
            // Send byte
            apb_write(TX_DATA, {24'd0, send_byte});

            // Wait for TX to complete (10 bits × BAUD_DIV + margin)
            poll_status(TX_BUSY, 1'b0, 20 * BAUD_DIV, found);

            // Wait for RX to complete
            poll_status(RX_READY, 1'b1, 15 * BAUD_DIV, found);

            // Read received data
            apb_read(RX_DATA, rd_data);
            recv_byte = rd_data[7:0];
        end
    endtask

    //--------------------------------------------------------------------------
    // Main test sequence
    //--------------------------------------------------------------------------
    initial begin
        $display("========================================");
        $display(" UART APB Testbench Starting...");
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
        check(rd_data == 32'd0, "Reset: CTRL is zero");

        apb_read(STATUS, rd_data);
        check(rd_data[TX_EMPTY] == 1'b1, "Reset: TX empty");
        check(rd_data[TX_BUSY] == 1'b0, "Reset: TX not busy");
        check(rd_data[RX_READY] == 1'b0, "Reset: RX not ready");
        check(rd_data[RX_OVERFLOW] == 1'b0, "Reset: no overflow");

        apb_read(BAUD_DIV_REG, rd_data);
        check(rd_data[15:0] == 16'd1, "Reset: BAUD_DIV default is 1");

        check(irq == 1'b0, "Reset: IRQ low");

        //======================================================================
        // Test 2: CTRL and BAUD_DIV register R/W
        //======================================================================
        $display("\n--- Test 2: Register R/W ---");

        apb_write(CTRL, 32'h3);  // tx_en=1, rx_en=1
        apb_read(CTRL, rd_data);
        check(rd_data[1:0] == 2'b11, "CTRL: tx_en and rx_en set");

        apb_write(CTRL, 32'h0);  // Disable both
        apb_read(CTRL, rd_data);
        check(rd_data[1:0] == 2'b00, "CTRL: cleared");

        apb_write(BAUD_DIV_REG, 32'hFFFF);
        apb_read(BAUD_DIV_REG, rd_data);
        check(rd_data[15:0] == 16'hFFFF, "BAUD_DIV: max value");

        apb_write(BAUD_DIV_REG, BAUD_DIV);  // Set for testing
        apb_read(BAUD_DIV_REG, rd_data);
        check(rd_data[15:0] == BAUD_DIV, "BAUD_DIV: set to test value");

        //======================================================================
        // Test 3: TX busy/empty states
        //======================================================================
        $display("\n--- Test 3: TX busy ---");

        // Enable TX
        apb_write(CTRL, 32'h3);  // tx_en + rx_en

        // Write data to trigger TX
        apb_write(TX_DATA, 32'hA5);

        // Immediately check TX is busy
        apb_read(STATUS, rd_data);
        check(rd_data[TX_BUSY] == 1'b1, "TX: busy after write");

        // Wait for TX to finish
        poll_status(TX_BUSY, 1'b0, 20 * BAUD_DIV, /*found=*/rd_data[0]);
        apb_read(STATUS, rd_data);
        check(rd_data[TX_BUSY] == 1'b0, "TX: completed (not busy)");
        check(rd_data[TX_EMPTY] == 1'b1, "TX: empty after completion");

        @(negedge PCLK);

        //======================================================================
        // Test 4: Loopback TX -> RX (0x55)
        //======================================================================
        $display("\n--- Test 4: Loopback 0x55 ---");

        // Wait for any previous RX data to be ready and clear it
        poll_status(RX_READY, 1'b1, 15 * BAUD_DIV, /*found=*/rd_data[0]);
        if (rd_data[0]) begin
            apb_read(RX_DATA, rd_data);  // Clear rx_ready
        end

        // Send 0x55 via loopback
        send_and_receive(8'h55, rd_data[7:0]);
        check(rd_data[7:0] == 8'h55, "Loopback: received 0x55");

        check(irq == 1'b1, "Loopback: IRQ asserted (rx_ready)");
        apb_read(RX_DATA, rd_data);  // Clear rx_ready
        check(irq == 1'b0, "Loopback: IRQ deasserted after read");

        @(negedge PCLK);

        //======================================================================
        // Test 5: Loopback multiple bytes
        //======================================================================
        $display("\n--- Test 5: Multiple bytes ---");

        send_and_receive(8'h00, rd_data[7:0]);
        check(rd_data[7:0] == 8'h00, "Loopback: received 0x00");
        apb_read(RX_DATA, rd_data);  // Clear

        send_and_receive(8'hFF, rd_data[7:0]);
        check(rd_data[7:0] == 8'hFF, "Loopback: received 0xFF");
        apb_read(RX_DATA, rd_data);  // Clear

        send_and_receive(8'hA5, rd_data[7:0]);
        check(rd_data[7:0] == 8'hA5, "Loopback: received 0xA5");
        apb_read(RX_DATA, rd_data);  // Clear

        @(negedge PCLK);

        //======================================================================
        // Test 6: TX ignored when disabled
        //======================================================================
        $display("\n--- Test 6: TX disabled ---");

        // Disable TX
        apb_write(CTRL, 32'h2);  // rx_en only

        // Try to send - should not start
        apb_write(TX_DATA, 32'h12);
        apb_read(STATUS, rd_data);
        check(rd_data[TX_BUSY] == 1'b0, "TX disabled: not busy");
        check(rd_data[TX_EMPTY] == 1'b1, "TX disabled: stays empty");

        // Re-enable for next tests
        apb_write(CTRL, 32'h3);

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
