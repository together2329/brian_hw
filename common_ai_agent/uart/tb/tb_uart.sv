// =============================================================================
// tb_uart.sv — UART Top-Level Testbench (SSOT-driven)
// =============================================================================
// Generated from: uart/yaml/uart_ssot.yaml
// DUT: uart_wrapper (APB4 slave + UART TX/RX)
// Simulator: iverilog -g2012
// =============================================================================

`timescale 1ns/1ps

module tb_uart;

    // -------------------------------------------------------------------------
    // Parameters (from SSOT: clock_domains.frequency = 100MHz)
    // -------------------------------------------------------------------------
    parameter CLK_PERIOD = 10;  // 100 MHz → 10 ns period

    // -------------------------------------------------------------------------
    // DUT Signal Declarations (from SSOT io_list → uart_wrapper ports)
    // -------------------------------------------------------------------------
    logic        uartclk;
    logic        uartresetn;
    logic [11:0] paddr;
    logic        psel;
    logic        penable;
    logic        pwrite;
    logic [31:0] pwdata;
    logic [3:0]  pstrb;
    logic [31:0] prdata;
    logic        pready;
    logic        pslverr;
    logic        tx;
    logic        rx;
    logic        rts_n;
    logic        cts_n;
    logic        uart_irq;

    // -------------------------------------------------------------------------
    // Pass/Fail Counters
    // -------------------------------------------------------------------------
    integer pass_cnt = 0;
    integer fail_cnt = 0;
    integer total;

    // -------------------------------------------------------------------------
    // Include test case tasks (inside module for scope access)
    // -------------------------------------------------------------------------
    `include "tc_uart.sv"

    // -------------------------------------------------------------------------
    // DUT Instantiation: uart_wrapper
    // -------------------------------------------------------------------------
    uart_wrapper dut (
        .uartclk    (uartclk),
        .uartresetn (uartresetn),
        .paddr      (paddr),
        .psel       (psel),
        .penable    (penable),
        .pwrite     (pwrite),
        .pwdata     (pwdata),
        .pstrb      (pstrb),
        .prdata     (prdata),
        .pready     (pready),
        .pslverr    (pslverr),
        .tx         (tx),
        .rx         (rx),
        .rts_n      (rts_n),
        .cts_n      (cts_n),
        .uart_irq   (uart_irq)
    );

    // -------------------------------------------------------------------------
    // Clock Generation: 100 MHz (from SSOT clock_domains)
    // -------------------------------------------------------------------------
    initial uartclk = 0;
    always #(CLK_PERIOD/2) uartclk = ~uartclk;

    // -------------------------------------------------------------------------
    // Waveform Dump
    // -------------------------------------------------------------------------
    initial begin
        $dumpfile("sim/uart_wave.vcd");
        $dumpvars(0, tb_uart);
    end

    // -------------------------------------------------------------------------
    // Reset Task: assert active-low reset for ≥ 3 cycles, then deassert
    // -------------------------------------------------------------------------
    task do_reset;
        begin
            uartresetn = 1'b0;
            paddr      = 12'h000;
            psel       = 1'b0;
            penable    = 1'b0;
            pwrite     = 1'b0;
            pwdata     = 32'h0;
            pstrb      = 4'h0;
            rx         = 1'b1;   // idle high
            cts_n      = 1'b0;   // assert CTS (active low)
            repeat(5) @(posedge uartclk);
            uartresetn = 1'b1;
            @(posedge uartclk);
        end
    endtask

    // -------------------------------------------------------------------------
    // Test Sequence — all 17 SSOT-derived scenarios
    // -------------------------------------------------------------------------
    initial begin
        $display("========================================");
        $display("  UART Testbench — SSOT-driven");
        $display("  DUT: uart_wrapper");
        $display("  Scenarios: 17");
        $display("========================================");

        // Phase 0: Reset
        do_reset();

        // SC17 — Reset Values (verify before any config)
        tc_SC17_reset_values();

        // SC16 — Status Register Polling
        tc_SC16_status_poll();

        // SC1 — APB Register Read/Write
        tc_SC1_basic_op();

        do_reset();

        // SC2 — TX Single Byte
        tc_SC2_tx_single();

        do_reset();

        // SC3 — RX Single Byte
        tc_SC3_rx_single();

        do_reset();

        // SC4 — Loopback TX→RX
        tc_SC4_loopback();

        do_reset();

        // SC5 — Parity Even (loopback)
        tc_SC5_parity_even();

        do_reset();

        // SC6 — Parity Odd (loopback)
        tc_SC6_parity_odd();

        do_reset();

        // SC7 — 2 Stop Bits (loopback)
        tc_SC7_two_stop();

        do_reset();

        // SC8 — TX FIFO Full
        tc_SC8_tx_fifo_full();

        do_reset();

        // SC9 — RX FIFO Overrun
        tc_SC9_rx_overrun();

        do_reset();

        // SC10 — Baud Rate Divisor Change
        tc_SC10_baud_change();

        do_reset();

        // SC11 — TX Empty Interrupt
        tc_SC11_int_tx_empty();

        do_reset();

        // SC12 — RX Ready Interrupt
        tc_SC12_int_rx_ready();

        do_reset();

        // SC13 — RX Overrun Interrupt
        tc_SC13_int_rx_overrun();

        do_reset();

        // SC14 — Parity Error Interrupt
        tc_SC14_int_parity_err();

        do_reset();

        // SC15 — Framing Error Interrupt
        tc_SC15_int_frame_err();

        // -----------------------------------------------------------------
        // Final Report
        // -----------------------------------------------------------------
        total = pass_cnt + fail_cnt;
        $display("");
        $display("========================================");
        $display("  UART Testbench Results");
        $display("========================================");
        $display("Result: %0d/%0d checks passed", pass_cnt, total);
        if (fail_cnt == 0) begin
            $display("Status: 0 errors, 0 warnings");
            $display("ALL TESTS PASSED");
        end else begin
            $display("Status: %0d FAILURES detected", fail_cnt);
        end
        $display("========================================");

        $finish;
    end

endmodule
