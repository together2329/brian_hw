// =============================================================================
// Testbench: tb_dma_top
// Description: Comprehensive testbench for dma_top AXI4-Lite DMA Controller
//              - AXI4-Lite slave BFM for register access
//              - AXI4 slave memory models for DMA read/write
//              - Self-checking scoreboard
//              - Multiple test cases
// =============================================================================

`timescale 1ns/1ps

module tb_dma_top;

    // =========================================================================
    // Parameters
    // =========================================================================
    parameter DATA_WIDTH    = 32;
    parameter ADDR_WIDTH    = 32;
    parameter MAX_BURST_LEN = 16;
    parameter FIFO_DEPTH    = 8;
    parameter CLK_PERIOD    = 10;  // 100MHz clock

    // Register offsets (must match DUT)
    localparam ADDR_SRC_LO   = 4'h0;
    localparam ADDR_DST_LO   = 4'h8;
    localparam ADDR_XFER_LEN = 4'h10;
    localparam ADDR_CTRL     = 4'h14;
    localparam ADDR_STATUS   = 4'h18;
    localparam ADDR_INT_STAT = 4'h1C;

    // Control register bits
    localparam CTRL_START      = 0;
    localparam CTRL_INT_EN     = 1;
    localparam CTRL_SOFT_RESET = 2;

    // =========================================================================
    // Signals
    // =========================================================================
    logic                     clk;
    logic                     rst_n;

    // AXI4-Lite Slave Interface
    logic [ADDR_WIDTH-1:0]    s_axi_awaddr;
    logic                     s_axi_awvalid;
    logic                     s_axi_awready;
    logic [DATA_WIDTH-1:0]    s_axi_wdata;
    logic [(DATA_WIDTH/8)-1:0] s_axi_wstrb;
    logic                     s_axi_wvalid;
    logic                     s_axi_wready;
    logic [1:0]               s_axi_bresp;
    logic                     s_axi_bvalid;
    logic                     s_axi_bready;
    logic [ADDR_WIDTH-1:0]    s_axi_araddr;
    logic                     s_axi_arvalid;
    logic                     s_axi_arready;
    logic [DATA_WIDTH-1:0]    s_axi_rdata;
    logic [1:0]               s_axi_rresp;
    logic                     s_axi_rvalid;
    logic                     s_axi_rready;

    // AXI4 Master Read Interface (DMA source)
    logic [ADDR_WIDTH-1:0]    m_axi_araddr;
    logic [7:0]               m_axi_arlen;
    logic [2:0]               m_axi_arsize;
    logic [1:0]               m_axi_arburst;
    logic                     m_axi_arvalid;
    logic                     m_axi_arready;
    logic [DATA_WIDTH-1:0]    m_axi_rdata;
    logic [1:0]               m_axi_rresp;
    logic                     m_axi_rlast;
    logic                     m_axi_rvalid;
    logic                     m_axi_rready;

    // AXI4 Master Write Interface (DMA destination)
    logic [ADDR_WIDTH-1:0]    m_axi_awaddr;
    logic [7:0]               m_axi_awlen;
    logic [2:0]               m_axi_awsize;
    logic [1:0]               m_axi_awburst;
    logic                     m_axi_awvalid;
    logic                     m_axi_awready;
    logic [DATA_WIDTH-1:0]    m_axi_wdata;
    logic [(DATA_WIDTH/8)-1:0] m_axi_wstrb;
    logic                     m_axi_wlast;
    logic                     m_axi_wvalid;
    logic                     m_axi_wready;
    logic [1:0]               m_axi_bresp;
    logic                     m_axi_bvalid;
    logic                     m_axi_bready;

    // Interrupt
    logic                     dma_irq;

    // =========================================================================
    // Clock Generation
    // =========================================================================
    initial begin
        clk = 1'b0;
        forever #(CLK_PERIOD/2) clk = ~clk;
    end

    // =========================================================================
    // Reset Generation
    // =========================================================================
    task automatic apply_reset;
        begin
            rst_n = 1'b0;
            repeat(20) @(posedge clk);
            rst_n = 1'b1;
            repeat(5) @(posedge clk);
        end
    endtask

    // =========================================================================
    // DUT Instantiation
    // =========================================================================
    dma_top #(
        .DATA_WIDTH    (DATA_WIDTH),
        .ADDR_WIDTH    (ADDR_WIDTH),
        .MAX_BURST_LEN (MAX_BURST_LEN),
        .FIFO_DEPTH    (FIFO_DEPTH)
    ) uut (
        .clk           (clk),
        .rst_n         (rst_n),

        // AXI4-Lite Slave
        .s_axi_awaddr  (s_axi_awaddr),
        .s_axi_awvalid (s_axi_awvalid),
        .s_axi_awready (s_axi_awready),
        .s_axi_wdata   (s_axi_wdata),
        .s_axi_wstrb   (s_axi_wstrb),
        .s_axi_wvalid  (s_axi_wvalid),
        .s_axi_wready  (s_axi_wready),
        .s_axi_bresp   (s_axi_bresp),
        .s_axi_bvalid  (s_axi_bvalid),
        .s_axi_bready  (s_axi_bready),
        .s_axi_araddr  (s_axi_araddr),
        .s_axi_arvalid (s_axi_arvalid),
        .s_axi_arready (s_axi_arready),
        .s_axi_rdata   (s_axi_rdata),
        .s_axi_rresp   (s_axi_rresp),
        .s_axi_rvalid  (s_axi_rvalid),
        .s_axi_rready  (s_axi_rready),

        // AXI4 Master Read
        .m_axi_araddr  (m_axi_araddr),
        .m_axi_arlen   (m_axi_arlen),
        .m_axi_arsize  (m_axi_arsize),
        .m_axi_arburst (m_axi_arburst),
        .m_axi_arvalid (m_axi_arvalid),
        .m_axi_arready (m_axi_arready),
        .m_axi_rdata   (m_axi_rdata),
        .m_axi_rresp   (m_axi_rresp),
        .m_axi_rlast   (m_axi_rlast),
        .m_axi_rvalid  (m_axi_rvalid),
        .m_axi_rready  (m_axi_rready),

        // AXI4 Master Write
        .m_axi_awaddr  (m_axi_awaddr),
        .m_axi_awlen   (m_axi_awlen),
        .m_axi_awsize  (m_axi_awsize),
        .m_axi_awburst (m_axi_awburst),
        .m_axi_awvalid (m_axi_awvalid),
        .m_axi_awready (m_axi_awready),
        .m_axi_wdata   (m_axi_wdata),
        .m_axi_wstrb   (m_axi_wstrb),
        .m_axi_wlast   (m_axi_wlast),
        .m_axi_wvalid  (m_axi_wvalid),
        .m_axi_wready  (m_axi_wready),
        .m_axi_bresp   (m_axi_bresp),
        .m_axi_bvalid  (m_axi_bvalid),
        .m_axi_bready  (m_axi_bready),

        // Interrupt
        .dma_irq       (dma_irq)
    );

    // =========================================================================
    // Memory Model - Source Memory (responds to DMA read requests)
    // =========================================================================
    logic [DATA_WIDTH-1:0] src_mem [0:65535];  // 256KB source memory
    logic [DATA_WIDTH-1:0] dst_mem [0:65535];  // 256KB destination memory

    // Initialize memories
    initial begin
        for (int i = 0; i < 65536; i++) begin
            src_mem[i] = '0;
            dst_mem[i] = '0;
        end
    end

    // Task to load source memory with a pattern
    task automatic load_src_mem(
        input logic [ADDR_WIDTH-1:0] base_addr,
        input int                    num_words,
        input logic [DATA_WIDTH-1:0] pattern
    );
        int word_offset;
        begin
            word_offset = base_addr / (DATA_WIDTH/8);
            for (int i = 0; i < num_words; i++) begin
                src_mem[word_offset + i] = pattern + i;
            end
        end
    endtask

    // Task to verify destination memory
    task automatic verify_dst_mem(
        input logic [ADDR_WIDTH-1:0] base_addr,
        input int                    num_words,
        input logic [DATA_WIDTH-1:0] expected_pattern,
        output int                   error_count
    );
        int word_offset;
        logic [DATA_WIDTH-1:0] expected_val;
        begin
            error_count = 0;
            word_offset = base_addr / (DATA_WIDTH/8);
            for (int i = 0; i < num_words; i++) begin
                expected_val = expected_pattern + i;
                if (dst_mem[word_offset + i] !== expected_val) begin
                    $display("[SCOREBOARD ERROR] Addr=0x%08h Expected=0x%08h Got=0x%08h",
                             (base_addr + i*(DATA_WIDTH/8)), expected_val, dst_mem[word_offset + i]);
                    error_count++;
                end
            end
        end
    endtask

    // =========================================================================
    // AXI4 Slave Memory Model - Read Response (source side)
    // =========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            m_axi_arready <= 1'b0;
            m_axi_rvalid  <= 1'b0;
            m_axi_rdata   <= '0;
            m_axi_rresp   <= 2'b00;
            m_axi_rlast   <= 1'b0;
        end else begin
            // Read address channel
            if (m_axi_arvalid && !m_axi_arready) begin
                m_axi_arready <= 1'b1;
            end else begin
                m_axi_arready <= 1'b0;
            end

            // Read data channel - respond after address accepted
            if (m_axi_arvalid && m_axi_arready) begin
                m_axi_rdata  <= src_mem[m_axi_araddr / (DATA_WIDTH/8)];
                m_axi_rresp  <= 2'b00;  // OKAY
                m_axi_rlast  <= 1'b1;   // Single beat
                m_axi_rvalid <= 1'b1;
            end else if (m_axi_rvalid && m_axi_rready) begin
                m_axi_rvalid <= 1'b0;
                m_axi_rlast  <= 1'b0;
            end
        end
    end

    // =========================================================================
    // AXI4 Slave Memory Model - Write Response (destination side)
    // =========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            m_axi_awready <= 1'b0;
            m_axi_wready  <= 1'b0;
            m_axi_bvalid  <= 1'b0;
            m_axi_bresp   <= 2'b00;
        end else begin
            // Write address channel
            if (m_axi_awvalid && !m_axi_awready) begin
                m_axi_awready <= 1'b1;
            end else begin
                m_axi_awready <= 1'b0;
            end

            // Write data channel
            if (m_axi_wvalid && m_axi_wready) begin
                dst_mem[m_axi_awaddr / (DATA_WIDTH/8)] <= m_axi_wdata;
                m_axi_wready <= 1'b1;
            end else if (m_axi_awvalid) begin
                m_axi_wready <= 1'b1;
            end else begin
                m_axi_wready <= 1'b0;
            end

            // Write response
            if (m_axi_wvalid && m_axi_wready && m_axi_wlast) begin
                m_axi_bvalid <= 1'b1;
                m_axi_bresp  <= 2'b00;
            end else if (m_axi_bvalid && m_axi_bready) begin
                m_axi_bvalid <= 1'b0;
            end
        end
    end

    // =========================================================================
    // AXI4-Lite Slave BFM - Register Write Task
    // =========================================================================
    task automatic axi_lite_write(
        input logic [ADDR_WIDTH-1:0] addr,
        input logic [DATA_WIDTH-1:0] data
    );
        begin
            // AW phase
            @(posedge clk);
            s_axi_awaddr  <= addr;
            s_axi_awvalid <= 1'b1;
            s_axi_wdata   <= data;
            s_axi_wstrb   <= {(DATA_WIDTH/8){1'b1}};
            s_axi_wvalid  <= 1'b1;
            s_axi_bready  <= 1'b1;

            // Wait for AW ready
            wait(s_axi_awready == 1'b1);
            @(posedge clk);
            s_axi_awvalid <= 1'b0;

            // Wait for W ready
            wait(s_axi_wready == 1'b1);
            @(posedge clk);
            s_axi_wvalid <= 1'b0;

            // Wait for B response
            wait(s_axi_bvalid == 1'b1);
            @(posedge clk);
            s_axi_bready <= 1'b0;

            $display("[AXI_WR] Addr=0x%08h Data=0x%08h at time %0t", addr, data, $time);
        end
    endtask

    // =========================================================================
    // AXI4-Lite Slave BFM - Register Read Task
    // =========================================================================
    task automatic axi_lite_read(
        input  logic [ADDR_WIDTH-1:0] addr,
        output logic [DATA_WIDTH-1:0] data
    );
        begin
            // AR phase
            @(posedge clk);
            s_axi_araddr  <= addr;
            s_axi_arvalid <= 1'b1;
            s_axi_rready  <= 1'b1;

            // Wait for AR ready
            wait(s_axi_arready == 1'b1);
            @(posedge clk);
            s_axi_arvalid <= 1'b0;

            // Wait for R valid
            wait(s_axi_rvalid == 1'b1);
            @(posedge clk);
            data = s_axi_rdata;
            s_axi_rready <= 1'b0;

            $display("[AXI_RD] Addr=0x%08h Data=0x%08h at time %0t", addr, data, $time);
        end
    endtask

    // =========================================================================
    // Helper Tasks
    // =========================================================================

    // Configure and start a DMA transfer
    task automatic configure_dma(
        input logic [ADDR_WIDTH-1:0] src_addr,
        input logic [ADDR_WIDTH-1:0] dst_addr,
        input logic [ADDR_WIDTH-1:0] length,
        input logic                  enable_int
    );
        logic [DATA_WIDTH-1:0] ctrl_val;
        begin
            ctrl_val = (enable_int << CTRL_INT_EN);
            axi_lite_write(ADDR_SRC_LO, src_addr);
            axi_lite_write(ADDR_DST_LO, dst_addr);
            axi_lite_write(ADDR_XFER_LEN, length);
            axi_lite_write(ADDR_CTRL, ctrl_val);
        end
    endtask

    // Start DMA (write start bit)
    task automatic start_dma;
        begin
            axi_lite_write(ADDR_CTRL, 32'h00000001);  // start=1
        end
    endtask

    // Configure and start DMA with interrupt
    task automatic start_dma_with_int;
        begin
            axi_lite_write(ADDR_CTRL, 32'h00000003);  // start=1, int_en=1
        end
    endtask

    // Wait for DMA to complete (poll status)
    task automatic wait_dma_done(
        input int timeout_cycles,
        output logic success
    );
        logic [DATA_WIDTH-1:0] status_val;
        int cycle_count;
        begin
            success = 1'b0;
            cycle_count = 0;
            while (cycle_count < timeout_cycles) begin
                axi_lite_read(ADDR_STATUS, status_val);
                if (status_val[1] == 1'b1) begin  // DONE bit
                    success = 1'b1;
                    $display("[INFO] DMA completed successfully at time %0t", $time);
                    return;
                end
                if (status_val[2] == 1'b1) begin  // ERROR bit
                    success = 1'b0;
                    $display("[ERROR] DMA error detected at time %0t", $time);
                    return;
                end
                cycle_count++;
            end
            $display("[ERROR] DMA timeout after %0d cycles at time %0t", timeout_cycles, $time);
        end
    endtask

    // Wait for interrupt
    task automatic wait_interrupt(
        input int timeout_cycles,
        output logic success
    );
        int cycle_count;
        begin
            success = 1'b0;
            for (cycle_count = 0; cycle_count < timeout_cycles; cycle_count++) begin
                @(posedge clk);
                if (dma_irq) begin
                    success = 1'b1;
                    $display("[INFO] DMA interrupt received at time %0t", $time);
                    return;
                end
            end
            $display("[ERROR] DMA interrupt timeout after %0d cycles", timeout_cycles);
        end
    endtask

    // Clear interrupt
    task automatic clear_interrupt;
        begin
            axi_lite_write(ADDR_INT_STAT, 32'h00000001);
        end
    endtask

    // =========================================================================
    // Scoreboard
    // =========================================================================
    int total_tests;
    int passed_tests;
    int failed_tests;

    task automatic check_result(
        input string test_name,
        input logic   pass
    );
        begin
            total_tests++;
            if (pass) begin
                passed_tests++;
                $display("  ✅ PASS: %s", test_name);
            end else begin
                failed_tests++;
                $display("  ❌ FAIL: %s", test_name);
            end
        end
    endtask

    // =========================================================================
    // Test Cases
    // =========================================================================

    // Test 1: Basic single-word DMA transfer
    task automatic test_basic_single_transfer;
        logic [ADDR_WIDTH-1:0] src_addr, dst_addr, xfer_len;
        logic [DATA_WIDTH-1:0] status_val;
        logic success;
        int errors;
        begin
            $display("\n========================================");
            $display("TEST 1: Basic Single Word DMA Transfer");
            $display("========================================");

            src_addr = 32'h0000_1000;
            dst_addr = 32'h0000_2000;
            xfer_len = 32'h4;  // 4 bytes = 1 word

            // Load source memory
            load_src_mem(src_addr, 1, 32'hDEADBEEF);

            // Configure and start DMA
            configure_dma(src_addr, dst_addr, xfer_len, 1'b0);
            start_dma;

            // Wait for completion
            wait_dma_done(1000, success);
            check_result("basic_single_transfer_done", success);

            // Verify data
            verify_dst_mem(dst_addr, 1, 32'hDEADBEEF, errors);
            check_result("basic_single_transfer_data", (errors == 0));
        end
    endtask

    // Test 2: Multiple word transfer
    task automatic test_multi_word_transfer;
        logic [ADDR_WIDTH-1:0] src_addr, dst_addr, xfer_len;
        logic success;
        int errors;
        int num_words;
        begin
            $display("\n========================================");
            $display("TEST 2: Multi-Word DMA Transfer (8 words)");
            $display("========================================");

            num_words = 8;
            src_addr = 32'h0000_3000;
            dst_addr = 32'h0000_4000;
            xfer_len = num_words * (DATA_WIDTH/8);  // 32 bytes

            // Load source memory with incrementing pattern
            load_src_mem(src_addr, num_words, 32'hA0000000);

            // Configure and start DMA
            configure_dma(src_addr, dst_addr, xfer_len, 1'b0);
            start_dma;

            // Wait for completion
            wait_dma_done(2000, success);
            check_result("multi_word_transfer_done", success);

            // Verify data
            verify_dst_mem(dst_addr, num_words, 32'hA0000000, errors);
            check_result("multi_word_transfer_data", (errors == 0));
        end
    endtask

    // Test 3: DMA transfer with interrupt
    task automatic test_transfer_with_interrupt;
        logic [ADDR_WIDTH-1:0] src_addr, dst_addr, xfer_len;
        logic success_dma, success_irq;
        int errors;
        begin
            $display("\n========================================");
            $display("TEST 3: DMA Transfer with Interrupt");
            $display("========================================");

            src_addr = 32'h0000_5000;
            dst_addr = 32'h0000_6000;
            xfer_len = 32'h4;  // 1 word

            load_src_mem(src_addr, 1, 32'hCAFEBABE);

            configure_dma(src_addr, dst_addr, xfer_len, 1'b1);  // Enable interrupt
            start_dma_with_int;

            wait_dma_done(1000, success_dma);
            check_result("interrupt_transfer_done", success_dma);

            wait_interrupt(500, success_irq);
            check_result("interrupt_received", success_irq);

            verify_dst_mem(dst_addr, 1, 32'hCAFEBABE, errors);
            check_result("interrupt_transfer_data", (errors == 0));

            // Clear interrupt and verify
            clear_interrupt;
            repeat(10) @(posedge clk);
            check_result("interrupt_cleared", (dma_irq == 1'b0));
        end
    endtask

    // Test 4: Back-to-back transfers
    task automatic test_back_to_back;
        logic [ADDR_WIDTH-1:0] src_addr, dst_addr;
        logic success;
        int errors;
        begin
            $display("\n========================================");
            $display("TEST 4: Back-to-Back DMA Transfers");
            $display("========================================");

            // Transfer 1
            src_addr = 32'h0000_7000;
            dst_addr = 32'h0000_8000;
            load_src_mem(src_addr, 2, 32'h11111111);

            configure_dma(src_addr, dst_addr, 32'h8, 1'b0);  // 2 words
            start_dma;
            wait_dma_done(1000, success);
            check_result("back_to_back_xfer1_done", success);

            verify_dst_mem(dst_addr, 2, 32'h11111111, errors);
            check_result("back_to_back_xfer1_data", (errors == 0));

            // Transfer 2 (immediately after)
            src_addr = 32'h0000_9000;
            dst_addr = 32'h0000_A000;
            load_src_mem(src_addr, 2, 32'h22222222);

            configure_dma(src_addr, dst_addr, 32'h8, 1'b0);  // 2 words
            start_dma;
            wait_dma_done(1000, success);
            check_result("back_to_back_xfer2_done", success);

            verify_dst_mem(dst_addr, 2, 32'h22222222, errors);
            check_result("back_to_back_xfer2_data", (errors == 0));
        end
    endtask

    // Test 5: Large transfer (fills FIFO multiple times)
    task automatic test_large_transfer;
        logic [ADDR_WIDTH-1:0] src_addr, dst_addr, xfer_len;
        logic success;
        int errors;
        int num_words;
        begin
            $display("\n========================================");
            $display("TEST 5: Large DMA Transfer (32 words)");
            $display("========================================");

            num_words = 32;
            src_addr = 32'h0000_B000;
            dst_addr = 32'h0000_C000;
            xfer_len = num_words * (DATA_WIDTH/8);  // 128 bytes

            load_src_mem(src_addr, num_words, 32'hB0000000);

            configure_dma(src_addr, dst_addr, xfer_len, 1'b0);
            start_dma;

            wait_dma_done(5000, success);
            check_result("large_transfer_done", success);

            verify_dst_mem(dst_addr, num_words, 32'hB0000000, errors);
            check_result("large_transfer_data", (errors == 0));
        end
    endtask

    // Test 6: Register read-back verification
    task automatic test_register_readback;
        logic [DATA_WIDTH-1:0] rd_val;
        logic pass;
        begin
            $display("\n========================================");
            $display("TEST 6: Register Read-Back Verification");
            $display("========================================");

            pass = 1'b1;

            // Write and read back source address
            axi_lite_write(ADDR_SRC_LO, 32'hAAAA_BBBB);
            axi_lite_read(ADDR_SRC_LO, rd_val);
            if (rd_val !== 32'hAAAA_BBBB) pass = 1'b0;
            check_result("src_addr_readback", pass);

            // Write and read back destination address
            pass = 1'b1;
            axi_lite_write(ADDR_DST_LO, 32'hCCCC_DDDD);
            axi_lite_read(ADDR_DST_LO, rd_val);
            if (rd_val !== 32'hCCCC_DDDD) pass = 1'b0;
            check_result("dst_addr_readback", pass);

            // Write and read back transfer length
            pass = 1'b1;
            axi_lite_write(ADDR_XFER_LEN, 32'h0000_0040);
            axi_lite_read(ADDR_XFER_LEN, rd_val);
            if (rd_val !== 32'h0000_0040) pass = 1'b0;
            check_result("xfer_len_readback", pass);
        end
    endtask

    // Test 7: Reset during transfer
    task automatic test_reset_during_transfer;
        logic [ADDR_WIDTH-1:0] src_addr, dst_addr;
        logic [DATA_WIDTH-1:0] status_val;
        begin
            $display("\n========================================");
            $display("TEST 7: Reset During Transfer");
            $display("========================================");

            src_addr = 32'h0000_D000;
            dst_addr = 32'h0000_E000;
            load_src_mem(src_addr, 16, 32'hD0000000);

            configure_dma(src_addr, dst_addr, 32'h40, 1'b0);  // 16 words
            start_dma;

            // Wait a few cycles then reset
            repeat(20) @(posedge clk);
            apply_reset;

            // Check status is IDLE
            axi_lite_read(ADDR_STATUS, status_val);
            check_result("status_idle_after_reset", (status_val == 32'h0));
        end
    endtask

    // Test 8: Soft reset
    task automatic test_soft_reset;
        logic [DATA_WIDTH-1:0] status_val;
        begin
            $display("\n========================================");
            $display("TEST 8: Soft Reset");
            $display("========================================");

            // Configure some registers
            axi_lite_write(ADDR_SRC_LO, 32'h1234_5678);
            axi_lite_write(ADDR_DST_LO, 32'h8765_4321);

            // Apply soft reset
            axi_lite_write(ADDR_CTRL, 32'h00000004);  // soft_reset=1

            // Verify registers are cleared
            axi_lite_read(ADDR_SRC_LO, status_val);
            check_result("src_cleared_after_soft_reset", (status_val == 32'h0));

            axi_lite_read(ADDR_DST_LO, status_val);
            check_result("dst_cleared_after_soft_reset", (status_val == 32'h0));
        end
    endtask

    // Test 9: Zero-length transfer (should not start)
    task automatic test_zero_length_transfer;
        logic [ADDR_WIDTH-1:0] src_addr, dst_addr;
        logic [DATA_WIDTH-1:0] status_val;
        begin
            $display("\n========================================");
            $display("TEST 9: Zero-Length Transfer");
            $display("========================================");

            src_addr = 32'h0000_F000;
            dst_addr = 32'h0000_F100;

            configure_dma(src_addr, dst_addr, 32'h0, 1'b0);  // 0 bytes
            start_dma;

            // Check status - should be IDLE (not busy)
            repeat(10) @(posedge clk);
            axi_lite_read(ADDR_STATUS, status_val);
            check_result("zero_length_not_busy", (status_val[0] == 1'b0));

            // Verify DMA did not write anything to destination
            axi_lite_read(ADDR_STATUS, status_val);
            check_result("zero_length_no_error", (status_val[2] == 1'b0));
        end
    endtask

    // Test 10: Boundary address transfer
    task automatic test_boundary_address_transfer;
        logic [ADDR_WIDTH-1:0] src_addr, dst_addr, xfer_len;
        logic success;
        int errors;
        begin
            $display("\n========================================");
            $display("TEST 10: Boundary Address Transfer");
            $display("========================================");

            // Use addresses near memory boundaries
            src_addr = 32'h0000_FFF0;  // Near 64KB boundary
            dst_addr = 32'h0000_1000;
            xfer_len = 32'h4;  // 1 word (fits within memory)

            load_src_mem(src_addr, 1, 32'hBOUNDARY);
            configure_dma(src_addr, dst_addr, xfer_len, 1'b0);
            start_dma;

            wait_dma_done(1000, success);
            check_result("boundary_transfer_done", success);

            verify_dst_mem(dst_addr, 1, 32'hBOUNDARY, errors);
            check_result("boundary_transfer_data", (errors == 0));
        end
    endtask

    // Test 11: Same source and destination address
    task automatic test_same_src_dst;
        logic [ADDR_WIDTH-1:0] addr;
        logic success;
        int errors;
        begin
            $display("\n========================================");
            $display("TEST 11: Same Source and Destination Address");
            $display("========================================");

            addr = 32'h0000_5000;
            load_src_mem(addr, 4, 32'hFEEDFACE);

            configure_dma(addr, addr, 32'h10, 1'b0);  // src == dst, 4 words
            start_dma;

            wait_dma_done(2000, success);
            check_result("same_src_dst_done", success);

            verify_dst_mem(addr, 4, 32'hFEEDFACE, errors);
            check_result("same_src_dst_data", (errors == 0));
        end
    endtask

    // Test 12: DMA without configuration (registers at default 0)
    task automatic test_unconfigured_dma;
        logic [DATA_WIDTH-1:0] status_val;
        begin
            $display("\n========================================");
            $display("TEST 12: Unconfigured DMA Start");
            $display("========================================");

            // Apply soft reset to clear registers
            axi_lite_write(ADDR_CTRL, 32'h00000004);

            // Start with all-zero config (src=0, dst=0, len=0)
            start_dma;

            repeat(10) @(posedge clk);
            axi_lite_read(ADDR_STATUS, status_val);
            check_result("unconfigured_dma_idle", (status_val[0] == 1'b0));
        end
    endtask

    // =========================================================================
    // Main Test Sequence
    // =========================================================================
    initial begin
        // Initialize all AXI-Lite signals
        s_axi_awaddr  = '0;
        s_axi_awvalid = 1'b0;
        s_axi_wdata   = '0;
        s_axi_wstrb   = '0;
        s_axi_wvalid  = 1'b0;
        s_axi_bready  = 1'b0;
        s_axi_araddr  = '0;
        s_axi_arvalid = 1'b0;
        s_axi_rready  = 1'b0;

        // Initialize scoreboard
        total_tests  = 0;
        passed_tests = 0;
        failed_tests = 0;

        $display("============================================================");
        $display("  DMA Controller Testbench Starting");
        $display("  CLK_PERIOD=%0d ns, DATA_WIDTH=%0d, FIFO_DEPTH=%0d",
                 CLK_PERIOD, DATA_WIDTH, FIFO_DEPTH);
        $display("============================================================");

        // Apply reset
        apply_reset;

        // Run test cases
        test_register_readback;       // Test 6 (no DMA, safe first)
        test_basic_single_transfer;   // Test 1
        test_multi_word_transfer;     // Test 2
        test_transfer_with_interrupt; // Test 3
        test_back_to_back;            // Test 4
        test_large_transfer;          // Test 5
        test_soft_reset;              // Test 8
        test_reset_during_transfer;   // Test 7 (destructive, last)

        // Print summary
        $display("\n============================================================");
        $display("  TEST SUMMARY");
        $display("============================================================");
        $display("  Total:  %0d", total_tests);
        $display("  Passed: %0d", passed_tests);
        $display("  Failed: %0d", failed_tests);
        $display("============================================================");

        if (failed_tests == 0)
            $display("  🎉 ALL TESTS PASSED!");
        else
            $display("  ⚠️  SOME TESTS FAILED!");
        $display("============================================================\n");

        repeat(100) @(posedge clk);
        $finish;
    end

    // =========================================================================
    // Timeout Watchdog
    // =========================================================================
    initial begin
        #100us;
        $display("[FATAL] Global timeout reached! Testbench hung.");
        $finish;
    end

    // =========================================================================
    // Waveform Generation
    // =========================================================================
    initial begin
        $dumpfile("tb_dma_top.vcd");
        $dumpvars(0, tb_dma_top);
    end

endmodule
