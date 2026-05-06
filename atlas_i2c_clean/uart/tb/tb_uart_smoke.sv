// =============================================================================
// tb_uart_smoke.sv — UART APB4 wrapper smoke test
// =============================================================================
// Covers:
//   1. Reset releases cleanly (pready=1, pslverr=0, tx=1)
//   2. APB write/read CTRL register
//   3. APB write TX_DATA accepted with pready behavior
//   4. Loopback: tx wired to rx, transmit a byte and verify RX_DATA readback
// =============================================================================

`timescale 1ns/1ps

module tb_uart_smoke;

    // ========================================================================
    // Parameters
    // ========================================================================
    localparam integer DATA_WIDTH     = 8;
    localparam integer BAUD_DIV       = 16;
    localparam integer FIFO_DEPTH     = 16;
    localparam integer APB_ADDR_WIDTH = 4;
    localparam integer CLOCK_FREQ_MHZ = 100;
    localparam integer CLK_PERIOD     = 10;  // 10 ns = 100 MHz

    // ========================================================================
    // Signals
    // ========================================================================
    logic                          clk;
    logic                          rst_n;
    logic [APB_ADDR_WIDTH-1:0]     paddr;
    logic                          psel;
    logic                          penable;
    logic                          pwrite;
    logic [31:0]                   pwdata;
    logic [31:0]                   prdata;
    logic                          pready;
    logic                          pslverr;
    logic                          tx;
    logic                          rx;
    logic                          irq;

    // ========================================================================
    // DUT instantiation
    // ========================================================================
    uart_wrapper #(
        .DATA_WIDTH     (DATA_WIDTH),
        .BAUD_DIV       (BAUD_DIV),
        .FIFO_DEPTH     (FIFO_DEPTH),
        .APB_ADDR_WIDTH (APB_ADDR_WIDTH),
        .CLOCK_FREQ_MHZ (CLOCK_FREQ_MHZ),
        .HAS_IRQ        (1'b1)
    ) u_dut (
        .clk     (clk),
        .rst_n   (rst_n),
        .paddr   (paddr),
        .psel    (psel),
        .penable (penable),
        .pwrite  (pwrite),
        .pwdata  (pwdata),
        .prdata  (prdata),
        .pready  (pready),
        .pslverr (pslverr),
        .tx      (tx),
        .rx      (rx),
        .irq     (irq)
    );

    // ========================================================================
    // Loopback: connect TX output to RX input for echo test
    // ========================================================================
    assign rx = tx;

    // ========================================================================
    // Clock generation
    // ========================================================================
    initial clk = 1'b0;
    always #(CLK_PERIOD/2) clk = ~clk;

    // ========================================================================
    // Test bookkeeping
    // ========================================================================
    integer test_count;
    integer pass_count;
    integer fail_count;

    // ========================================================================
    // APB tasks
    // ========================================================================

    // APB write — 2-phase (setup + access)
    task apb_write;
        input [APB_ADDR_WIDTH-1:0] addr;
        input [31:0]               data;
    begin
        @(posedge clk);
        // Setup phase
        paddr   <= addr;
        psel    <= 1'b1;
        pwrite  <= 1'b1;
        pwdata  <= data;
        penable <= 1'b0;
        @(posedge clk);
        // Access phase
        penable <= 1'b1;
        // Wait for pready
        while (!pready) @(posedge clk);
        @(posedge clk);
        // Idle
        psel    <= 1'b0;
        penable <= 1'b0;
        pwrite  <= 1'b0;
    end
    endtask

    // APB read — 2-phase (setup + access)
    task apb_read;
        input  [APB_ADDR_WIDTH-1:0] addr;
        output [31:0]               data;
    begin
        @(posedge clk);
        // Setup phase
        paddr   <= addr;
        psel    <= 1'b1;
        pwrite  <= 1'b0;
        pwdata  <= 32'h0;
        penable <= 1'b0;
        @(posedge clk);
        // Access phase
        penable <= 1'b1;
        // Wait for pready
        while (!pready) @(posedge clk);
        data <= prdata;
        @(posedge clk);
        // Idle
        psel    <= 1'b0;
        penable <= 1'b0;
    end
    endtask

    // ========================================================================
    // Checker macro
    // ========================================================================
    task check;
        input string  name;
        input         condition;
    begin
        test_count = test_count + 1;
        if (condition) begin
            pass_count = pass_count + 1;
            $display("[PASS] %0t: %0s", $time, name);
        end else begin
            fail_count = fail_count + 1;
            $display("[FAIL] %0t: %0s", $time, name);
        end
    end
    endtask

    // ========================================================================
    // Main test sequence
    // ========================================================================
    logic [31:0] rdata;
    integer drain_iter;

    initial begin
        // Init
        rst_n   <= 1'b0;
        paddr   <= {APB_ADDR_WIDTH{1'b0}};
        psel    <= 1'b0;
        penable <= 1'b0;
        pwrite  <= 1'b0;
        pwdata  <= 32'h0;
        test_count = 0;
        pass_count = 0;
        fail_count = 0;

        $display("=============================================================");
        $display(" UART APB4 Wrapper Smoke Test");
        $display("=============================================================");

        // ====================================================================
        // T1: Reset release
        // ====================================================================
        repeat(20) @(posedge clk);
        rst_n <= 1'b1;
        repeat(5) @(posedge clk);

        check("T1_reset: pready=1 after reset release",
              pready === 1'b1);
        check("T1_reset: pslverr=0 after reset release",
              pslverr === 1'b0);
        check("T1_reset: tx=1 (idle high) after reset release",
              tx === 1'b1);

        // ====================================================================
        // T2: Read CTRL register after reset
        // ====================================================================
        apb_read(4'h0, rdata);
        // Default: baud_div[15:8] = 0x10 = 16, rest zero
        check("T2_ctrl_read: CTRL reset value = 0x00001000",
              rdata == 32'h0000_1000);

        // ====================================================================
        // T3: Write CTRL register, readback
        // ====================================================================
        // Enable TX, RX, FIFO, set baud_div=16 (keep default)
        // CTRL = tx_en(1) | rx_en(1) | fifo_en(1) | baud_div=16<<8
        // = 0x07 | (16 << 8) = 0x00001007
        apb_write(4'h0, 32'h0000_1007);
        apb_read(4'h0, rdata);
        check("T3_ctrl_write: CTRL readback = 0x00001007",
              rdata == 32'h0000_1007);

        // ====================================================================
        // T4: Read STATUS register after reset, before any TX/RX activity
        // ====================================================================
        apb_read(4'h4, rdata);
        // Expected: tx_empty=1(bit0), rx_empty=1(bit2), others 0
        // => bit[0]=1, bit[2]=1 => 0x05
        check("T4_status: STATUS after reset shows tx_empty=1, rx_empty=1",
              rdata[0] === 1'b1 && rdata[2] === 1'b1);

        // ====================================================================
        // T5: APB write TX_DATA — should accept with pready=1
        // ====================================================================
        // Write byte 0x55 to TX_DATA
        apb_write(4'h8, 32'h0000_0055);
        // pready should have been 1 (FIFO not full)
        // Check STATUS: tx_empty should now be 0, tx_busy should become 1
        // Wait a few baud ticks for TX FSM to pick up data
        repeat(BAUD_DIV * 2) @(posedge clk);
        apb_read(4'h4, rdata);
        check("T5_tx_data: STATUS shows tx_busy=1 or tx_empty=0 after TX_DATA write",
              rdata[4] === 1'b1 || rdata[0] === 1'b0);

        // ====================================================================
        // T6: Wait for TX to finish transmitting the byte
        // ====================================================================
        // At baud_div=16, one bit = 16 clk cycles
        // Frame: start(1) + 8 data + stop(1) = 10 bits = 160 clk cycles
        // Wait generously
        repeat(BAUD_DIV * 20) @(posedge clk);

        apb_read(4'h4, rdata);
        check("T6_tx_complete: STATUS shows tx_empty=1 and tx_busy=0",
              rdata[0] === 1'b1 && rdata[4] === 1'b0);

        // ====================================================================
        // T7: Loopback RX — byte should be available in RX FIFO
        //     Since tx is wired to rx, the transmitted byte 0x55 should
        //     arrive in the RX FIFO after the full frame time.
        //     The TX already completed, so wait for RX to finish.
        // ====================================================================
        // RX needs extra time: it has a 2-stage synchronizer + mid-bit sampling
        // Allow generous wait
        repeat(BAUD_DIV * 20) @(posedge clk);

        apb_read(4'h4, rdata);
        if (rdata[2] === 1'b0) begin
            // rx_empty=0, data available
            apb_read(4'hC, rdata);
            check("T7_loopback_rx: RX_DATA = 0x55 (loopback from TX)",
                  rdata[8] === 1'b1 && rdata[7:0] === 8'h55);
        end else begin
            // RX might still be processing — wait more
            repeat(BAUD_DIV * 20) @(posedge clk);
            apb_read(4'h4, rdata);
            if (rdata[2] === 1'b0) begin
                apb_read(4'hC, rdata);
                check("T7_loopback_rx: RX_DATA = 0x55 (loopback from TX, extended wait)",
                      rdata[8] === 1'b1 && rdata[7:0] === 8'h55);
            end else begin
                check("T7_loopback_rx: RX_DATA available in FIFO",
                      1'b0);  // explicit fail if no data
                $display("  NOTE: Loopback RX data not available. This may be a timing");
                $display("  limitation of the testbench. TX-to-RX loopback requires exact");
                $display("  baud tick alignment between TX and RX state machines.");
            end
        end

        // ====================================================================
        // T8: Second TX byte — 0xAA
        // ====================================================================
        apb_write(4'h8, 32'h0000_00AA);
        repeat(BAUD_DIV * 25) @(posedge clk);

        apb_read(4'h4, rdata);
        check("T8_second_tx: STATUS shows tx_empty=1 after 0xAA transmit",
              rdata[0] === 1'b1);

        // Check for second loopback byte
        repeat(BAUD_DIV * 20) @(posedge clk);
        apb_read(4'h4, rdata);
        if (rdata[2] === 1'b0) begin
            apb_read(4'hC, rdata);
            check("T8_loopback_rx: RX_DATA = 0xAA (second loopback byte)",
                  rdata[8] === 1'b1 && rdata[7:0] === 8'hAA);
        end else begin
            repeat(BAUD_DIV * 20) @(posedge clk);
            apb_read(4'h4, rdata);
            if (rdata[2] === 1'b0) begin
                apb_read(4'hC, rdata);
                check("T8_loopback_rx: RX_DATA = 0xAA (extended wait)",
                      rdata[8] === 1'b1 && rdata[7:0] === 8'hAA);
            end else begin
                check("T8_loopback_rx: RX second byte available",
                      1'b0);
            end
        end

        // ====================================================================
        // T9: IRQ behavior — after clearing RX FIFO, IRQ should be 0
        // ====================================================================
        // Read all remaining RX data to drain FIFO
        for (drain_iter = 0; drain_iter < 32 && rdata[2] !== 1'b1; drain_iter = drain_iter + 1) begin
            apb_read(4'h4, rdata);
            if (rdata[2] !== 1'b1) begin
                apb_read(4'hC, rdata);
            end
        end
        // After draining, irq should be 0 (no framing/overrun errors expected)
        check("T9_irq: IRQ=0 after RX FIFO drained (no errors)",
              irq === 1'b0);

        // ====================================================================
        // T10: Write CTRL with TX disabled — verify readback
        // ====================================================================
        apb_write(4'h0, 32'h0000_1002);  // only rx_en, no tx_en
        apb_read(4'h0, rdata);
        check("T10_ctrl_rx_only: CTRL = 0x00001002 (rx_en only)",
              rdata == 32'h0000_1002);

        // Restore full enable
        apb_write(4'h0, 32'h0000_1007);

        // ====================================================================
        // Summary
        // ====================================================================
        repeat(100) @(posedge clk);
        $display("");
        $display("=============================================================");
        $display(" SIMULATION SUMMARY");
        $display("   Total tests : %0d", test_count);
        $display("   Passed      : %0d", pass_count);
        $display("   Failed      : %0d", fail_count);
        if (fail_count == 0) begin
            $display("   Result      : *** ALL PASS ***");
        end else begin
            $display("   Result      : *** SOME FAILURES ***");
        end
        $display("=============================================================");
        $display("");

        // Write summary to log
        $display("SIM_DONE: pass=%0d fail=%0d total=%0d", pass_count, fail_count, test_count);

        if (fail_count > 0) begin
            $finish;
        end else begin
            $finish;
        end
    end

    // ========================================================================
    // Watchdog — timeout after 500 us
    // ========================================================================
    initial begin
        #500000;
        $display("[ERROR] Watchdog timeout — simulation hung!");
        $finish;
    end

endmodule
