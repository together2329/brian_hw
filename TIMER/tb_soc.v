
`timescale 1ns / 1ps

//----------------------------------------------------------------------------
// Module: tb_soc
// Description: End-to-end SoC testbench. Drives AHB bus directly into soc_top.
//----------------------------------------------------------------------------

module tb_soc;

    //--------------------------------------------------------------------------
    // Parameters
    //--------------------------------------------------------------------------
    localparam CLK_PERIOD = 10;
    localparam BAUD_DIV   = 16;

    // Timer addresses (base 0x0000_0000)
    localparam [31:0] TIMER_CTRL      = 32'h00000000;
    localparam [31:0] TIMER_PERIOD    = 32'h00000004;
    localparam [31:0] TIMER_PRESCALER = 32'h00000008;
    localparam [31:0] TIMER_VALUE     = 32'h0000000C;
    localparam [31:0] TIMER_STATUS    = 32'h00000010;

    // Counter addresses (base 0x0000_1000)
    localparam [31:0] COUNTER_CTRL      = 32'h00001000;
    localparam [31:0] COUNTER_COUNT_LO  = 32'h00001004;
    localparam [31:0] COUNTER_COUNT_HI  = 32'h00001008;
    localparam [31:0] COUNTER_TC_STATUS = 32'h0000100C;

    // UART addresses (base 0x0000_2000)
    localparam [31:0] UART_TX_DATA   = 32'h00002000;
    localparam [31:0] UART_RX_DATA   = 32'h00002004;
    localparam [31:0] UART_CTRL      = 32'h00002008;
    localparam [31:0] UART_STATUS    = 32'h0000200C;
    localparam [31:0] UART_BAUD_DIV  = 32'h00002010;

    //--------------------------------------------------------------------------
    // AHB Signals
    //--------------------------------------------------------------------------
    reg         HCLK;
    reg         HRESETn;
    reg  [31:0] HADDR;
    reg  [31:0] HWDATA;
    wire [31:0] HRDATA;
    reg         HWRITE;
    reg  [1:0]  HTRANS;
    reg  [2:0]  HSIZE;
    wire        irq_timer;
    wire        irq_counter;
    wire        irq_uart;
    wire        uart_tx_out;
    wire        uart_rx_in;

    // Test tracking
    integer     tests_passed = 0;
    integer     tests_failed = 0;
    reg  [31:0] rd_data;

    //--------------------------------------------------------------------------
    // DUT
    //--------------------------------------------------------------------------
    soc_top dut (
        .HCLK        (HCLK),
        .HRESETn     (HRESETn),
        .HADDR       (HADDR),
        .HWDATA      (HWDATA),
        .HRDATA      (HRDATA),
        .HWRITE      (HWRITE),
        .HTRANS      (HTRANS),
        .HSIZE       (HSIZE),
        .uart_rx_in  (uart_rx_in),
        .uart_tx_out (uart_tx_out),
        .irq_timer   (irq_timer),
        .irq_counter (irq_counter),
        .irq_uart    (irq_uart)
    );

    // UART loopback: TX output feeds back to RX input
    assign uart_rx_in = uart_tx_out;

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
        $dumpfile("soc.vcd");
        $dumpvars(0, tb_soc);
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
    // AHB Write task
    //--------------------------------------------------------------------------
    task ahb_write;
        input [31:0] addr;
        input [31:0] data;
        begin
            @(negedge HCLK);
            HADDR  = addr;
            HWDATA = data;
            HWRITE = 1'b1;
            HTRANS = 2'b10;  // NONSEQ
            HSIZE  = 3'b010; // WORD
            @(negedge HCLK);  // Bridge: IDLE->SETUP
            HTRANS = 2'b00;
            HWRITE = 1'b0;
            @(negedge HCLK);  // Bridge: SETUP->ACCESS
            @(negedge HCLK);  // Bridge: ACCESS->IDLE
        end
    endtask

    //--------------------------------------------------------------------------
    // AHB Read task
    //--------------------------------------------------------------------------
    task ahb_read;
        input  [31:0] addr;
        output [31:0] data;
        begin
            @(negedge HCLK);
            HADDR  = addr;
            HWRITE = 1'b0;
            HTRANS = 2'b10;  // NONSEQ
            HSIZE  = 3'b010; // WORD
            @(negedge HCLK);  // Bridge: IDLE->SETUP
            HTRANS = 2'b00;
            @(negedge HCLK);  // Bridge: SETUP->ACCESS
            @(negedge HCLK);  // Bridge: ACCESS->IDLE
            data = HRDATA;
        end
    endtask

    //--------------------------------------------------------------------------
    // Main test sequence
    //--------------------------------------------------------------------------
    initial begin
        $display("========================================");
        $display(" SoC End-to-End Testbench Starting...");
        $display("========================================");

        // Initialize
        HRESETn = 1'b0;
        HADDR   = 32'd0;
        HWDATA  = 32'd0;
        HWRITE  = 1'b0;
        HTRANS  = 2'b00;
        HSIZE   = 3'b010;

        repeat(5) @(negedge HCLK);
        HRESETn = 1'b1;
        repeat(2) @(negedge HCLK);

        //======================================================================
        // Test 1: Reset verification
        //======================================================================
        $display("\n--- Test 1: Reset ---");

        ahb_read(TIMER_CTRL, rd_data);
        check(rd_data == 32'd0, "Reset: timer CTRL is zero");

        ahb_read(COUNTER_CTRL, rd_data);
        check(rd_data == 32'd0, "Reset: counter CTRL is zero");

        check(irq_timer == 1'b0, "Reset: timer IRQ low");
        check(irq_counter == 1'b0, "Reset: counter IRQ low");
        check(irq_uart == 1'b0, "Reset: UART IRQ low");

        //======================================================================
        // Test 2: Timer through bridge
        //======================================================================
        $display("\n--- Test 2: Timer via AHB ---");

        ahb_write(TIMER_PRESCALER, 32'd1);
        ahb_write(TIMER_PERIOD, 32'd100);
        ahb_write(TIMER_CTRL, 32'h4);  // load
        @(negedge HCLK);

        ahb_read(TIMER_VALUE, rd_data);
        $display("[DEBUG] Timer VALUE after load: %0d (expected 98-100)", rd_data);
        check(rd_data >= 32'd90 && rd_data <= 32'd100, "Timer: loaded period near 100");

        // Enable and count
        ahb_write(TIMER_CTRL, 32'h1);  // enable
        repeat(20) @(negedge HCLK);
        ahb_write(TIMER_CTRL, 32'd0);  // stop

        ahb_read(TIMER_VALUE, rd_data);
        check(rd_data < 32'd100, "Timer: value decreased");

        @(negedge HCLK);

        //======================================================================
        // Test 3: Counter through bridge
        //======================================================================
        $display("\n--- Test 3: Counter via AHB ---");

        ahb_write(COUNTER_COUNT_LO, 32'd0);
        ahb_write(COUNTER_COUNT_HI, 32'd0);
        ahb_write(COUNTER_CTRL, 32'h2);  // load
        @(negedge HCLK);

        // Count up
        ahb_write(COUNTER_CTRL, 32'h5);  // enable + up_down
        repeat(20) @(negedge HCLK);
        ahb_write(COUNTER_CTRL, 32'd0);  // stop

        ahb_read(COUNTER_COUNT_LO, rd_data);
        check(rd_data >= 32'd5, "Counter: counted up from 0");
        ahb_read(COUNTER_COUNT_HI, rd_data);
        check(rd_data == 32'd0, "Counter: high word still zero");

        @(negedge HCLK);

        //======================================================================
        // Test 4: Counter underflow + IRQ
        //======================================================================
        $display("\n--- Test 4: Counter underflow + IRQ ---");

        ahb_read(COUNTER_TC_STATUS, rd_data);  // clear sticky

        // Load 1, count down
        ahb_write(COUNTER_COUNT_LO, 32'd1);
        ahb_write(COUNTER_COUNT_HI, 32'd0);
        ahb_write(COUNTER_CTRL, 32'h2);  // load
        @(negedge HCLK);
        ahb_write(COUNTER_CTRL, 32'h1);  // enable (count down)
        repeat(10) @(negedge HCLK);
        ahb_write(COUNTER_CTRL, 32'd0);

        check(irq_counter == 1'b1, "Counter IRQ: asserted after underflow");

        ahb_read(COUNTER_TC_STATUS, rd_data);
        check(rd_data[0] == 1'b1, "Counter: tc_sticky set");

        @(negedge HCLK);

        //======================================================================
        // Test 5: UART via AHB - register access
        //======================================================================
        $display("\n--- Test 5: UART register access ---");

        ahb_read(UART_CTRL, rd_data);
        check(rd_data == 32'd0, "UART: CTRL zero after reset");

        ahb_read(UART_STATUS, rd_data);
        check(rd_data[0] == 1'b0, "UART: not busy after reset");
        check(rd_data[1] == 1'b1, "UART: TX empty after reset");
        check(rd_data[2] == 1'b0, "UART: RX not ready after reset");

        // Set baud divisor and enable TX/RX
        ahb_write(UART_BAUD_DIV, BAUD_DIV);
        ahb_read(UART_BAUD_DIV, rd_data);
        check(rd_data[15:0] == BAUD_DIV, "UART: baud divisor set");

        ahb_write(UART_CTRL, 32'h3);  // tx_en + rx_en
        ahb_read(UART_CTRL, rd_data);
        check(rd_data[1:0] == 2'b11, "UART: TX and RX enabled");

        //======================================================================
        // Test 6: UART loopback TX -> RX
        //======================================================================
        $display("\n--- Test 6: UART loopback ---");

        // Send 0x55
        ahb_write(UART_TX_DATA, 32'h55);

        // Wait for TX to complete (10 bits × BAUD_DIV + margin)
        repeat(12 * BAUD_DIV) @(negedge HCLK);

        // Check TX done
        ahb_read(UART_STATUS, rd_data);
        check(rd_data[0] == 1'b0, "UART loopback: TX not busy");
        check(rd_data[1] == 1'b1, "UART loopback: TX empty");

        // Wait for RX to complete (with extra margin for synchronizer + sampling)
        repeat(5 * BAUD_DIV) @(negedge HCLK);

        ahb_read(UART_STATUS, rd_data);
        check(rd_data[2] == 1'b1, "UART loopback: RX ready");
        check(irq_uart == 1'b1, "UART loopback: IRQ asserted");

        // Read received data
        ahb_read(UART_RX_DATA, rd_data);
        check(rd_data[7:0] == 8'h55, "UART loopback: received 0x55");
        repeat(3) @(negedge HCLK);  // Wait for rx_read_pulse to clear rx_ready
        check(irq_uart == 1'b0, "UART loopback: IRQ cleared after read");

        @(negedge HCLK);

        //======================================================================
        // Test 7: UART loopback second byte (0xA5)
        //======================================================================
        $display("\n--- Test 7: UART second byte ---");

        ahb_write(UART_TX_DATA, 32'hA5);
        repeat(15 * BAUD_DIV) @(negedge HCLK);

        ahb_read(UART_RX_DATA, rd_data);
        check(rd_data[7:0] == 8'hA5, "UART loopback: received 0xA5");

        @(negedge HCLK);

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
