
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
    localparam UART_BAUD  = 16;
    localparam SPI_CLK_DIV_VAL = 4;

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

    // SPI addresses (base 0x0000_3000)
    localparam [31:0] SPI_TX_DATA    = 32'h00003000;
    localparam [31:0] SPI_RX_DATA    = 32'h00003004;
    localparam [31:0] SPI_CTRL       = 32'h00003008;
    localparam [31:0] SPI_STATUS     = 32'h0000300C;
    localparam [31:0] SPI_CLK_DIV    = 32'h00003010;

    // DMA register addresses (base 0x0000_4000, via bridge)
    localparam [31:0] DMA_SRC_ADDR   = 32'h00004000;
    localparam [31:0] DMA_DST_ADDR   = 32'h00004004;
    localparam [31:0] DMA_COUNT      = 32'h00004008;
    localparam [31:0] DMA_CONTROL    = 32'h0000400C;
    localparam [31:0] DMA_STATUS     = 32'h00004010;

    // SRAM addresses (direct AHB slave at 0x2000_0000)
    localparam [31:0] SRAM_BASE      = 32'h20000000;

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
    wire        irq_spi;
    wire        dma_irq;
    wire        uart_tx_out;
    wire        uart_rx_in;
    wire        spi_mosi;
    wire        spi_miso;
    wire        spi_sck;
    wire        spi_cs_n;

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
        .spi_miso    (spi_miso),
        .spi_mosi    (spi_mosi),
        .spi_sck     (spi_sck),
        .spi_cs_n    (spi_cs_n),
        .irq_timer   (irq_timer),
        .irq_counter (irq_counter),
        .irq_uart    (irq_uart),
        .irq_spi     (irq_spi),
        .dma_irq     (dma_irq)
    );

    // UART loopback
    assign uart_rx_in = uart_tx_out;

    // SPI loopback
    assign spi_miso = spi_mosi;

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
    // AHB Write task (for bridge/peripheral access, 4-cycle timing)
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
    // AHB Read task (for bridge/peripheral access, 4-cycle timing)
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
    // SRAM Write task (direct AHB slave, 2-cycle timing)
    //   SRAM is combinational - write completes in 1 cycle.
    //--------------------------------------------------------------------------
    task sram_write;
        input [31:0] addr;
        input [31:0] data;
        begin
            @(negedge HCLK);
            HADDR  = addr;
            HWDATA = data;
            HWRITE = 1'b1;
            HTRANS = 2'b10;  // NONSEQ
            HSIZE  = 3'b010; // WORD
            @(negedge HCLK);  // SRAM writes at intervening posedge
            HTRANS = 2'b00;
            HWRITE = 1'b0;
        end
    endtask

    //--------------------------------------------------------------------------
    // SRAM Read task (direct AHB slave, 2-cycle timing)
    //   SRAM has combinational HRDATA - capture BEFORE clearing HTRANS.
    //--------------------------------------------------------------------------
    task sram_read;
        input  [31:0] addr;
        output [31:0] data;
        begin
            @(negedge HCLK);
            HADDR  = addr;
            HWRITE = 1'b0;
            HTRANS = 2'b10;  // NONSEQ
            HSIZE  = 3'b010; // WORD
            @(negedge HCLK);  // Data is valid (combinational)
            data   = HRDATA;  // Capture BEFORE clearing HTRANS
            HTRANS = 2'b00;
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
        check(irq_spi == 1'b0, "Reset: SPI IRQ low");
        check(dma_irq == 1'b0, "Reset: DMA IRQ low");

        //======================================================================
        // Test 2: Timer through bridge
        //======================================================================
        $display("\n--- Test 2: Timer via AHB ---");

        ahb_write(TIMER_PRESCALER, 32'd1);
        ahb_write(TIMER_PERIOD, 32'd100);
        ahb_write(TIMER_CTRL, 32'h4);  // load
        @(negedge HCLK);

        ahb_read(TIMER_VALUE, rd_data);
        check(rd_data >= 32'd90 && rd_data <= 32'd100, "Timer: loaded period near 100");

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
        // Test 5: UART register access
        //======================================================================
        $display("\n--- Test 5: UART register access ---");

        ahb_read(UART_CTRL, rd_data);
        check(rd_data == 32'd0, "UART: CTRL zero after reset");

        ahb_read(UART_STATUS, rd_data);
        check(rd_data[0] == 1'b0, "UART: not busy after reset");
        check(rd_data[1] == 1'b1, "UART: TX empty after reset");
        check(rd_data[2] == 1'b0, "UART: RX not ready after reset");

        ahb_write(UART_BAUD_DIV, UART_BAUD);
        ahb_read(UART_BAUD_DIV, rd_data);
        check(rd_data[15:0] == UART_BAUD, "UART: baud divisor set");

        ahb_write(UART_CTRL, 32'h3);  // tx_en + rx_en
        ahb_read(UART_CTRL, rd_data);
        check(rd_data[1:0] == 2'b11, "UART: TX and RX enabled");

        //======================================================================
        // Test 6: UART loopback TX -> RX
        //======================================================================
        $display("\n--- Test 6: UART loopback ---");

        // Send 0x55
        ahb_write(UART_TX_DATA, 32'h55);

        // Wait for TX to complete (10 bits × UART_BAUD + margin)
        repeat(12 * UART_BAUD) @(negedge HCLK);

        // Check TX done
        ahb_read(UART_STATUS, rd_data);
        check(rd_data[0] == 1'b0, "UART loopback: TX not busy");
        check(rd_data[1] == 1'b1, "UART loopback: TX empty");

        // Wait for RX to complete (with extra margin for synchronizer + sampling)
        repeat(5 * UART_BAUD) @(negedge HCLK);

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
        // Test 7: SPI register access
        //======================================================================
        $display("\n--- Test 7: SPI register access ---");

        ahb_read(SPI_CTRL, rd_data);
        check(rd_data[2:0] == 3'b000, "SPI: CTRL zero after reset");

        ahb_read(SPI_STATUS, rd_data);
        check(rd_data[0] == 1'b0, "SPI: not busy after reset");
        check(rd_data[1] == 1'b0, "SPI: rx not ready after reset");

        ahb_write(SPI_CLK_DIV, SPI_CLK_DIV_VAL);
        ahb_read(SPI_CLK_DIV, rd_data);
        check(rd_data[15:0] == SPI_CLK_DIV_VAL, "SPI: CLK_DIV set");

        // Enable SPI mode 0
        ahb_write(SPI_CTRL, 32'h1);  // enable
        ahb_read(SPI_CTRL, rd_data);
        check(rd_data[2:0] == 3'b001, "SPI: enabled, mode 0");

        //======================================================================
        // Test 8: SPI loopback
        //======================================================================
        $display("\n--- Test 8: SPI loopback ---");

        ahb_write(SPI_TX_DATA, 32'hA5);

        // Wait for transfer to complete (16 edges * SPI_CLK_DIV + margin)
        repeat(20 * SPI_CLK_DIV_VAL) @(negedge HCLK);

        ahb_read(SPI_STATUS, rd_data);
        check(rd_data[0] == 1'b0, "SPI loopback: not busy");
        check(rd_data[1] == 1'b1, "SPI loopback: rx_ready");
        check(irq_spi == 1'b1, "SPI loopback: IRQ asserted");

        ahb_read(SPI_RX_DATA, rd_data);
        check(rd_data[7:0] == 8'hA5, "SPI loopback: received 0xA5");

        @(negedge HCLK);

        //======================================================================
        // Test 9: SPI second byte
        //======================================================================
        $display("\n--- Test 9: SPI second byte ---");

        ahb_write(SPI_TX_DATA, 32'h55);
        repeat(20 * SPI_CLK_DIV_VAL) @(negedge HCLK);

        ahb_read(SPI_RX_DATA, rd_data);
        check(rd_data[7:0] == 8'h55, "SPI loopback: received 0x55");

        @(negedge HCLK);

        //======================================================================
        // Test 10: SRAM direct read/write
        //======================================================================
        $display("\n--- Test 10: SRAM direct R/W ---");

        // Write a pattern to SRAM
        sram_write(SRAM_BASE + 32'h0000, 32'hCAFE_BABE);
        sram_read(SRAM_BASE + 32'h0000, rd_data);
        check(rd_data == 32'hCAFE_BABE, "SRAM: write/read 0xCAFEBABE at base");

        //======================================================================
        // Test 11: SRAM multiple locations
        //======================================================================
        $display("\n--- Test 11: SRAM multiple locations ---");

        sram_write(SRAM_BASE + 32'h0000, 32'h1111_1111);
        sram_write(SRAM_BASE + 32'h0004, 32'h2222_2222);
        sram_write(SRAM_BASE + 32'h0008, 32'h3333_3333);
        sram_write(SRAM_BASE + 32'h000C, 32'h4444_4444);

        sram_read(SRAM_BASE + 32'h0000, rd_data);
        check(rd_data == 32'h1111_1111, "SRAM multi: word 0 = 0x1111_1111");
        sram_read(SRAM_BASE + 32'h0004, rd_data);
        check(rd_data == 32'h2222_2222, "SRAM multi: word 1 = 0x2222_2222");
        sram_read(SRAM_BASE + 32'h0008, rd_data);
        check(rd_data == 32'h3333_3333, "SRAM multi: word 2 = 0x3333_3333");
        sram_read(SRAM_BASE + 32'h000C, rd_data);
        check(rd_data == 32'h4444_4444, "SRAM multi: word 3 = 0x4444_4444");

        //======================================================================
        // Test 12: DMA register access
        //======================================================================
        $display("\n--- Test 12: DMA register access ---");

        // Read reset values (via bridge)
        ahb_read(DMA_SRC_ADDR, rd_data);
        check(rd_data == 32'd0, "DMA: SRC_ADDR reset = 0");

        ahb_read(DMA_STATUS, rd_data);
        check(rd_data[0] == 1'b0, "DMA: STATUS.busy = 0 after reset");
        check(rd_data[1] == 1'b0, "DMA: STATUS.done = 0 after reset");

        // Write and readback
        ahb_write(DMA_SRC_ADDR, 32'h2000_0000);
        ahb_read(DMA_SRC_ADDR, rd_data);
        check(rd_data == 32'h2000_0000, "DMA: SRC_ADDR = 0x2000_0000");

        ahb_write(DMA_DST_ADDR, 32'h2000_0100);
        ahb_read(DMA_DST_ADDR, rd_data);
        check(rd_data == 32'h2000_0100, "DMA: DST_ADDR = 0x2000_0100");

        ahb_write(DMA_COUNT, 32'd4);
        ahb_read(DMA_COUNT, rd_data);
        check(rd_data == 32'd4, "DMA: COUNT = 4");

        //======================================================================
        // Test 13: DMA memory-to-memory transfer
        //======================================================================
        $display("\n--- Test 13: DMA mem-to-mem transfer ---");

        // Preload SRAM source with test data (already done in test 11)
        // Source: 0x2000_0000 = {0x11111111, 0x22222222, 0x33333333, 0x44444444}

        // Configure DMA: src=0x2000_0000, dst=0x2000_0100, count=4
        ahb_write(DMA_SRC_ADDR, 32'h2000_0000);
        ahb_write(DMA_DST_ADDR, 32'h2000_0100);
        ahb_write(DMA_COUNT, 32'd4);

        // Start DMA with interrupt enabled
        ahb_write(DMA_CONTROL, 32'h03);  // start + irq_en

        // Wait for DMA to complete (poll dma_irq with timeout)
        begin : dma_wait_block
            integer timeout;
            timeout = 0;
            while (!dma_irq && timeout < 500) begin
                @(negedge HCLK);
                timeout = timeout + 1;
            end
        end
        check(dma_irq == 1'b1, "DMA: transfer completed (irq asserted)");

        // Verify destination data via SRAM read
        sram_read(SRAM_BASE + 32'h0100, rd_data);
        check(rd_data == 32'h1111_1111, "DMA dst: word 0 = 0x1111_1111");
        sram_read(SRAM_BASE + 32'h0104, rd_data);
        check(rd_data == 32'h2222_2222, "DMA dst: word 1 = 0x2222_2222");
        sram_read(SRAM_BASE + 32'h0108, rd_data);
        check(rd_data == 32'h3333_3333, "DMA dst: word 2 = 0x3333_3333");
        sram_read(SRAM_BASE + 32'h010C, rd_data);
        check(rd_data == 32'h4444_4444, "DMA dst: word 3 = 0x4444_4444");

        // Verify source unchanged
        sram_read(SRAM_BASE + 32'h0000, rd_data);
        check(rd_data == 32'h1111_1111, "DMA src: unchanged after transfer");

        //======================================================================
        // Test 14: DMA interrupt clearing
        //======================================================================
        $display("\n--- Test 14: DMA interrupt clearing ---");

        check(dma_irq == 1'b1, "DMA IRQ: still asserted before STATUS read");

        // Read STATUS to clear done flag
        ahb_read(DMA_STATUS, rd_data);
        check(rd_data[0] == 1'b0, "DMA STATUS: busy = 0");

        @(negedge HCLK);
        check(dma_irq == 1'b0, "DMA IRQ: cleared after STATUS read");

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
