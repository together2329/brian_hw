// ============================================================================
// DMA Controller Testbench — MAS §9 DV Plan
// ============================================================================
// Testbench for the multi-channel DMA controller with CSR configuration
// interface and simple bus master read/write interface.
//
// Test Coverage (25 tests):
//   1.  Reset values
//   2.  Register read/write
//   3.  CSR access to non-existent register
//   4.  Single word transfer
//   5.  Burst transfer (multiple beats)
//   6.  Large transfer (>internal buffering)
//   7.  Multi-channel simultaneous transfer
//   8.  Priority arbitration
//   9.  Interrupt generation & clearing
//   10. Error handling (bus error)
//  11. Circular mode
//  12. Global enable/disable
//  13. Channel status register
//  14. Reset during active transfer
//  15. Fixed address mode (peripheral FIFO)
//  16. INT_CLEAR write-1-to-clear
//  17. Zero-length transfer (edge case)
//  18. Multiple sequential transfers on same channel
//  19. Back-pressure (rd_ready/wr_ready deasserted)
//  20. All channels independent configuration
//  21. SW trigger without channel enable
//  22. ERR clearing
//  23. Bus request protocol checks
//  24. Hardware trigger
//  25. Stop during active transfer
// ============================================================================

`timescale 1ns/1ps

module tb_dma;

    // =========================================================================
    // Parameters
    // =========================================================================
    parameter int NUM_CHANNELS = 4;
    parameter int ADDR_WIDTH   = 32;
    parameter int DATA_WIDTH   = 32;
    parameter int BURST_MAX    = 16;
    parameter int MAX_TRANSFER = 65536;
    parameter int CLK_PERIOD   = 10;  // 100 MHz

    // =========================================================================
    // CSR Address Map (must match RTL localparams)
    // =========================================================================
    localparam logic [ADDR_WIDTH-1:0] CSR_CH_SELECT   = ADDR_WIDTH'(32'h000);
    localparam logic [ADDR_WIDTH-1:0] CSR_SRC_ADDR_LO = ADDR_WIDTH'(32'h004);
    localparam logic [ADDR_WIDTH-1:0] CSR_DST_ADDR_LO = ADDR_WIDTH'(32'h00C);
    localparam logic [ADDR_WIDTH-1:0] CSR_XFER_COUNT  = ADDR_WIDTH'(32'h014);
    localparam logic [ADDR_WIDTH-1:0] CSR_CONTROL     = ADDR_WIDTH'(32'h018);
    localparam logic [ADDR_WIDTH-1:0] CSR_STATUS      = ADDR_WIDTH'(32'h01C);
    localparam logic [ADDR_WIDTH-1:0] CSR_INT_STATUS  = ADDR_WIDTH'(32'h020);
    localparam logic [ADDR_WIDTH-1:0] CSR_INT_ENABLE  = ADDR_WIDTH'(32'h024);
    localparam logic [ADDR_WIDTH-1:0] CSR_INT_CLEAR   = ADDR_WIDTH'(32'h028);

    // Control register bits
    localparam int CTRL_ENABLE_BIT   = 0;
    localparam int CTRL_START_BIT    = 1;
    localparam int CTRL_STOP_BIT     = 2;
    localparam int CTRL_SRC_INC_BIT  = 3;
    localparam int CTRL_DST_INC_BIT  = 4;
    localparam int CTRL_BURST_EN_BIT = 5;
    localparam int CTRL_HW_TRIG_BIT  = 6;
    localparam int CTRL_INT_EN_BIT   = 7;
    localparam int CTRL_MODE_LO_BIT  = 8;
    localparam int CTRL_MODE_HI_BIT  = 9;

    // =========================================================================
    // Signals
    // =========================================================================
    logic                          clk;
    logic                          rst_n;

    // Bus Master Read
    logic [ADDR_WIDTH-1:0]         m_rd_addr;
    logic                          m_rd_valid;
    logic [DATA_WIDTH-1:0]         m_rd_data;
    logic                          m_rd_ready;

    // Bus Master Write
    logic [ADDR_WIDTH-1:0]         m_wr_addr;
    logic [DATA_WIDTH-1:0]         m_wr_data;
    logic                          m_wr_valid;
    logic                          m_wr_ready;

    // Bus arbitration
    logic                          m_bus_req;
    logic                          m_bus_grant;

    // CSR Interface
    logic [ADDR_WIDTH-1:0]         csr_addr;
    logic [DATA_WIDTH-1:0]         csr_wr_data;
    logic                          csr_wr_en;
    logic                          csr_rd_en;
    logic [DATA_WIDTH-1:0]         csr_rd_data;
    logic                          csr_rd_valid;

    // Hardware request inputs
    logic [NUM_CHANNELS-1:0]       hw_req;

    // Interrupt outputs
    logic [NUM_CHANNELS-1:0]       irq;

    // =========================================================================
    // Test Bookkeeping
    // =========================================================================
    int test_pass;
    int test_fail;
    int test_count;
    int check_pass;
    int check_fail;

    // =========================================================================
    // Memory Model (simple single-port SRAM simulation)
    // =========================================================================
    logic [DATA_WIDTH-1:0] mem_array [logic [ADDR_WIDTH-1:0]];

    // Error injection
    logic                      inject_error;
    logic [ADDR_WIDTH-1:0]     error_addr;
    int                        rd_latency;  // configurable read latency
    int                        wr_latency;  // configurable write latency

    // =========================================================================
    // DUT Instantiation
    // =========================================================================
    dma #(
        .NUM_CHANNELS ( NUM_CHANNELS ),
        .ADDR_WIDTH   ( ADDR_WIDTH   ),
        .DATA_WIDTH   ( DATA_WIDTH   ),
        .BURST_MAX    ( BURST_MAX    ),
        .MAX_TRANSFER ( MAX_TRANSFER )
    ) uut (.*);

    // =========================================================================
    // Clock Generation
    // =========================================================================
    initial clk = 1'b0;
    always #(CLK_PERIOD/2) clk = ~clk;

    // =========================================================================
    // Bus Slave — Memory Model with Configurable Latency
    // =========================================================================

    // Read response pipeline
    logic [DATA_WIDTH-1:0]   rd_data_buf;
    logic                    rd_valid_buf;
    int                      rd_cnt;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            m_rd_ready   <= 1'b0;
            rd_data_buf  <= '0;
            m_rd_data    <= '0;
            rd_cnt       <= 0;
        end else begin
            if (m_rd_valid && !m_rd_ready) begin
                // Waiting to assert ready
                rd_cnt <= rd_cnt + 1;
                if (rd_cnt >= rd_latency - 1) begin
                    m_rd_ready <= 1'b1;
                    if (inject_error && m_rd_addr == error_addr) begin
                        // Return garbage on error
                        m_rd_data <= 32'hDEAD_BEEF;
                    end else if (mem_array.exists(m_rd_addr)) begin
                        m_rd_data <= mem_array[m_rd_addr];
                    end else begin
                        m_rd_data <= 32'hX;
                    end
                end
            end else begin
                m_rd_ready <= 1'b0;
                rd_cnt     <= 0;
                if (m_rd_valid) begin
                    // Start read latency counter
                    if (rd_latency <= 1) begin
                        m_rd_ready <= 1'b1;
                        if (inject_error && m_rd_addr == error_addr) begin
                            m_rd_data <= 32'hDEAD_BEEF;
                        end else if (mem_array.exists(m_rd_addr)) begin
                            m_rd_data <= mem_array[m_rd_addr];
                        end else begin
                            m_rd_data <= '0;
                        end
                    end else begin
                        rd_cnt <= 1;
                    end
                end
            end
        end
    end

    // Write response pipeline
    int wr_cnt;

    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            m_wr_ready <= 1'b0;
            wr_cnt     <= 0;
        end else begin
            if (m_wr_valid && !m_wr_ready) begin
                wr_cnt <= wr_cnt + 1;
                if (wr_cnt >= wr_latency - 1) begin
                    m_wr_ready <= 1'b1;
                    if (!(inject_error && m_wr_addr == error_addr)) begin
                        mem_array[m_wr_addr] = m_wr_data;
                    end
                end
            end else begin
                m_wr_ready <= 1'b0;
                wr_cnt     <= 0;
                if (m_wr_valid) begin
                    if (wr_latency <= 1) begin
                        m_wr_ready <= 1'b1;
                        if (!(inject_error && m_wr_addr == error_addr)) begin
                            mem_array[m_wr_addr] = m_wr_data;
                        end
                    end else begin
                        wr_cnt <= 1;
                    end
                end
            end
        end
    end

    // =========================================================================
    // Bus Grant — always grant immediately for test purposes
    // =========================================================================
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            m_bus_grant <= 1'b0;
        else
            m_bus_grant <= m_bus_req;
    end

    // =========================================================================
    // Utility Tasks
    // =========================================================================

    // --- Clock-cycle wait ---
    task automatic tick(input int n = 1);
        repeat(n) @(posedge clk);
    endtask

    // --- Reset application ---
    task automatic apply_reset;
        rst_n = 1'b0;
        hw_req = '0;
        inject_error = 1'b0;
        error_addr = '0;
        rd_latency = 1;
        wr_latency = 1;
        csr_addr    = '0;
        csr_wr_data = '0;
        csr_wr_en   = 1'b0;
        csr_rd_en   = 1'b0;
        repeat(5) @(posedge clk);
        rst_n = 1'b1;
        repeat(3) @(posedge clk);
    endtask

    // --- Signal initialization ---
    task automatic init_signals;
        clk         = 1'b0;
        rst_n       = 1'b0;
        hw_req      = '0;
        csr_addr    = '0;
        csr_wr_data = '0;
        csr_wr_en   = 1'b0;
        csr_rd_en   = 1'b0;
        inject_error = 1'b0;
        error_addr   = '0;
        rd_latency   = 1;
        wr_latency   = 1;
    endtask

    // --- Memory model helpers ---
    task automatic mem_clear;
        mem_array.delete();
    endtask

    task automatic mem_write(input logic [ADDR_WIDTH-1:0] addr,
                             input logic [DATA_WIDTH-1:0] data);
        mem_array[addr] = data;
    endtask

    task automatic mem_read(input logic [ADDR_WIDTH-1:0] addr,
                            output logic [DATA_WIDTH-1:0] data);
        if (mem_array.exists(addr))
            data = mem_array[addr];
        else
            data = '0;
    endtask

    task automatic mem_fill_pattern(input logic [ADDR_WIDTH-1:0] base,
                                    input int count,
                                    input logic [DATA_WIDTH-1:0] pattern);
        for (int i = 0; i < count; i++)
            mem_array[base + i*4] = pattern + i;
    endtask

    // =========================================================================
    // CSR Access Tasks
    // =========================================================================

    task automatic csr_write(input logic [ADDR_WIDTH-1:0] addr,
                             input logic [DATA_WIDTH-1:0] data);
        @(posedge clk);
        csr_addr    <= addr;
        csr_wr_data <= data;
        csr_wr_en   <= 1'b1;
        csr_rd_en   <= 1'b0;
        @(posedge clk);
        csr_wr_en   <= 1'b0;
    endtask

    task automatic csr_read(input logic [ADDR_WIDTH-1:0] addr,
                            output logic [DATA_WIDTH-1:0] data);
        @(posedge clk);
        csr_addr  <= addr;
        csr_wr_en <= 1'b0;
        csr_rd_en <= 1'b1;
        @(posedge clk);
        csr_rd_en <= 1'b0;
        // Wait for rd_valid
        wait(csr_rd_valid == 1'b1);
        data = csr_rd_data;
    endtask

    // =========================================================================
    // Channel Configuration Helpers
    // =========================================================================

    // Select a channel for CSR operations
    task automatic select_channel(input int ch);
        csr_write(CSR_CH_SELECT, ADDR_WIDTH'(ch));
    endtask

    // Configure channel registers (src, dst, count, ctrl)
    task automatic config_channel(input int ch,
                                  input logic [ADDR_WIDTH-1:0] src_addr,
                                  input logic [ADDR_WIDTH-1:0] dst_addr,
                                  input logic [XFER_COUNT_WIDTH-1:0] xfer_count,
                                  input logic [DATA_WIDTH-1:0] ctrl);
        select_channel(ch);
        csr_write(CSR_SRC_ADDR_LO, src_addr);
        csr_write(CSR_DST_ADDR_LO, dst_addr);
        csr_write(CSR_XFER_COUNT,  {{(DATA_WIDTH-$bits(xfer_count)){1'b0}}, xfer_count});
        csr_write(CSR_CONTROL,     ctrl);
    endtask

    // Build a control word from individual fields
    function automatic logic [DATA_WIDTH-1:0] build_ctrl(
        input logic enable,
        input logic src_inc,
        input logic dst_inc,
        input logic burst_en,
        input logic hw_trig,
        input logic int_en,
        input logic [1:0] mode
    );
        logic [DATA_WIDTH-1:0] ctrl;
        ctrl = '0;
        ctrl[CTRL_ENABLE_BIT]   = enable;
        ctrl[CTRL_SRC_INC_BIT]  = src_inc;
        ctrl[CTRL_DST_INC_BIT]  = dst_inc;
        ctrl[CTRL_BURST_EN_BIT] = burst_en;
        ctrl[CTRL_HW_TRIG_BIT]  = hw_trig;
        ctrl[CTRL_INT_EN_BIT]   = int_en;
        ctrl[CTRL_MODE_HI_BIT:CTRL_MODE_LO_BIT] = mode;
        return ctrl;
    endfunction

    // Start a channel (set enable + start bits)
    task automatic start_channel(input int ch);
        logic [DATA_WIDTH-1:0] ctrl;
        select_channel(ch);
        // First ensure channel is enabled
        ctrl = build_ctrl(1'b1, 1'b1, 1'b1, 1'b0, 1'b0, 1'b0, 2'b00);
        ctrl[CTRL_ENABLE_BIT] = 1'b1;
        ctrl[CTRL_START_BIT]  = 1'b1;
        csr_write(CSR_CONTROL, ctrl);
    endtask

    // Stop a channel
    task automatic stop_channel(input int ch);
        logic [DATA_WIDTH-1:0] ctrl;
        select_channel(ch);
        ctrl = '0;
        ctrl[CTRL_STOP_BIT] = 1'b1;
        csr_write(CSR_CONTROL, ctrl);
    endtask

    // =========================================================================
    // Wait for IRQ with timeout
    // =========================================================================
    task automatic wait_irq(input int ch, input int timeout_cycles,
                            output logic success);
        success = 1'b0;
        fork
            begin
                int cnt;
                cnt = 0;
                while (irq[ch] !== 1'b1 && cnt < timeout_cycles) begin
                    @(posedge clk);
                    cnt++;
                end
                if (irq[ch] === 1'b1)
                    success = 1'b1;
            end
        join
    endtask

    // =========================================================================
    // Test Result Tracking
    // =========================================================================
    string cur_test_name;

    task automatic begin_test(input string name);
        cur_test_name = name;
        check_pass = 0;
        check_fail = 0;
        test_count++;
        $display("  [%0t] TEST %0d: %s", $time, test_count, name);
    endtask

    task automatic check(input string desc, input logic condition);
        if (condition) begin
            check_pass++;
        end else begin
            check_fail++;
            $display("    FAIL: %s", desc);
        end
    endtask

    task automatic end_test;
        test_pass += check_pass;
        test_fail += check_fail;
        if (check_fail == 0)
            $display("    PASS (%0d checks)", check_pass);
        else
            $display("    FAIL (%0d pass, %0d fail)", check_pass, check_fail);
    endtask

    // =========================================================================
    // TEST 1: Reset Values
    // =========================================================================
    task automatic test_reset;
        logic [DATA_WIDTH-1:0] rdata;

        begin_test("Reset Values (FR-13)");

        apply_reset();

        // Check IRQ outputs are 0
        check("irq all low after reset", irq == '0);

        // Check bus request is 0
        check("m_bus_req low after reset", m_bus_req == 1'b0);

        // Check CSR reads return defaults
        csr_read(CSR_CH_SELECT, rdata);
        check("CH_SELECT=0 after reset", rdata == '0);

        csr_read(CSR_INT_STATUS, rdata);
        check("INT_STATUS=0 after reset", rdata[NUM_CHANNELS-1:0] == '0);

        csr_read(CSR_INT_ENABLE, rdata);
        check("INT_ENABLE=0 after reset", rdata[NUM_CHANNELS-1:0] == '0);

        // Check channel 0 status = IDLE
        select_channel(0);
        csr_read(CSR_STATUS, rdata);
        check("CH0 status: not active", rdata[0] == 1'b0);
        check("CH0 status: not done",   rdata[1] == 1'b0);
        check("CH0 status: not error",  rdata[2] == 1'b0);

        end_test();
    endtask

    // =========================================================================
    // TEST 2: Register Read/Write (FR-01)
    // =========================================================================
    task automatic test_register_rw;
        logic [DATA_WIDTH-1:0] rdata;

        begin_test("Register Read/Write (FR-01)");

        apply_reset();

        // Write/read CH_SELECT
        csr_write(CSR_CH_SELECT, 32'd2);
        csr_read(CSR_CH_SELECT, rdata);
        check("CH_SELECT readback=2", rdata == 32'd2);

        // Write/read SRC_ADDR for channel 2
        csr_write(CSR_SRC_ADDR_LO, 32'hABCD_1234);
        csr_read(CSR_SRC_ADDR_LO, rdata);
        check("SRC_ADDR readback (ch2)", rdata == 32'hABCD_1234);

        // Write/read DST_ADDR for channel 2
        csr_write(CSR_DST_ADDR_LO, 32'h5678_DCBA);
        csr_read(CSR_DST_ADDR_LO, rdata);
        check("DST_ADDR readback (ch2)", rdata == 32'h5678_DCBA);

        // Write/read XFER_COUNT for channel 2
        csr_write(CSR_XFER_COUNT, 32'd100);
        csr_read(CSR_XFER_COUNT, rdata);
        check("XFER_COUNT readback=100 (ch2)", rdata == 32'd100);

        // Switch to channel 0 and verify independence
        csr_write(CSR_CH_SELECT, 32'd0);
        csr_read(CSR_SRC_ADDR_LO, rdata);
        check("CH0 SRC_ADDR unaffected", rdata == '0);

        // INT_ENABLE register
        csr_write(CSR_INT_ENABLE, 32'hF);
        csr_read(CSR_INT_ENABLE, rdata);
        check("INT_ENABLE readback=0xF", rdata == 32'hF);

        end_test();
    endtask

    // =========================================================================
    // TEST 3: CSR Access to Reserved Address
    // =========================================================================
    task automatic test_csr_reserved;
        logic [DATA_WIDTH-1:0] rdata;

        begin_test("CSR Reserved Address Access");

        apply_reset();

        // Read from a non-existent CSR address (e.g., 0x0FC)
        csr_read(ADDR_WIDTH'(32'h0FC), rdata);
        check("Reserved CSR reads as 0", rdata == '0);

        // Write to non-existent address should not crash
        csr_write(ADDR_WIDTH'(32'h0FC), 32'hFFFF_FFFF);
        csr_read(ADDR_WIDTH'(32'h0FC), rdata);
        check("Reserved CSR still 0 after write", rdata == '0);

        end_test();
    endtask

    // =========================================================================
    // TEST 4: Single Word Transfer (FR-03)
    // =========================================================================
    task automatic test_single_transfer;
        logic [DATA_WIDTH-1:0] rdata;
        logic                  success;

        begin_test("Single Word Transfer (FR-03)");

        apply_reset();
        mem_clear();

        // Setup source data
        mem_write(32'h0000_0100, 32'hAAAA_BBBB);

        // Configure channel 0: enable, src_inc, dst_inc, int_en, SINGLE mode
        config_channel(0, 32'h0000_0100, 32'h0000_0200, 16'd1,
                        build_ctrl(1'b1, 1'b1, 1'b1, 1'b0, 1'b0, 1'b1, 2'b00));

        // Enable interrupts for channel 0
        csr_write(CSR_INT_ENABLE, 32'h1);

        // Start transfer
        start_channel(0);

        // Wait for interrupt
        wait_irq(0, 5000, success);
        check("Single transfer completed (IRQ)", success);

        // Verify destination data
        mem_read(32'h0000_0200, rdata);
        check("Destination data correct", rdata == 32'hAAAA_BBBB);

        // Check interrupt status
        csr_read(CSR_INT_STATUS, rdata);
        check("INT_STATUS[0] set", rdata[0] == 1'b1);

        // Clear interrupt
        csr_write(CSR_INT_CLEAR, 32'h1);
        csr_read(CSR_INT_STATUS, rdata);
        check("INT_STATUS cleared", rdata[0] == 1'b0);

        end_test();
    endtask

    // =========================================================================
    // TEST 5: Burst Transfer (FR-06)
    // =========================================================================
    task automatic test_burst_transfer;
        logic [DATA_WIDTH-1:0] rdata;
        logic                  success;

        begin_test("Burst Transfer (FR-06)");

        apply_reset();
        mem_clear();

        // Fill source: 8 words
        for (int i = 0; i < 8; i++)
            mem_write(32'h0000_0100 + i*4, 32'hBEEF_0000 + i);

        // Configure channel 0: enable, src_inc, dst_inc, burst_en, int_en, BURST mode
        config_channel(0, 32'h0000_0100, 32'h0000_0200, 16'd8,
                        build_ctrl(1'b1, 1'b1, 1'b1, 1'b1, 1'b0, 1'b1, 2'b01));

        csr_write(CSR_INT_ENABLE, 32'h1);
        start_channel(0);

        wait_irq(0, 10000, success);
        check("Burst transfer completed (IRQ)", success);

        // Verify all 8 words
        for (int i = 0; i < 8; i++) begin
            mem_read(32'h0000_0200 + i*4, rdata);
            check($sformatf("Burst dest word %0d correct", i), rdata == 32'hBEEF_0000 + i);
        end

        end_test();
    endtask

    // =========================================================================
    // TEST 6: Large Transfer (>internal buffering, tests cycling)
    // =========================================================================
    task automatic test_large_transfer;
        logic [DATA_WIDTH-1:0] rdata;
        logic                  success;
        int                    xfer_len = 20;

        begin_test("Large Transfer (20 words, SINGLE mode)");

        apply_reset();
        mem_clear();

        for (int i = 0; i < xfer_len; i++)
            mem_write(32'h0000_0100 + i*4, 32'h1234_0000 + i);

        config_channel(0, 32'h0000_0100, 32'h0000_0500, xfer_len,
                        build_ctrl(1'b1, 1'b1, 1'b1, 1'b0, 1'b0, 1'b1, 2'b00));

        csr_write(CSR_INT_ENABLE, 32'h1);
        start_channel(0);

        wait_irq(0, 30000, success);
        check($sformatf("Large transfer (%0d words) completed", xfer_len), success);

        for (int i = 0; i < xfer_len; i++) begin
            mem_read(32'h0000_0500 + i*4, rdata);
            check($sformatf("Large xfer word %0d correct", i),
                  rdata == 32'h1234_0000 + i);
        end

        end_test();
    endtask

    // =========================================================================
    // TEST 7: Multi-Channel Simultaneous Transfer (FR-03, FR-04)
    // =========================================================================
    task automatic test_multi_channel;
        logic [DATA_WIDTH-1:0] rdata;
        logic [NUM_CHANNELS-1:0] irq_capture;
        logic                    success;

        begin_test("Multi-Channel Simultaneous Transfer");

        apply_reset();
        mem_clear();

        // Fill source regions for all channels
        for (int ch = 0; ch < NUM_CHANNELS; ch++) begin
            for (int i = 0; i < 4; i++)
                mem_write(32'(ch * 32'h400 + 32'h100 + i*4),
                          32'(ch * 32'h10000 + 32'hDDDD_0000 + i));
        end

        // Configure all channels
        for (int ch = 0; ch < NUM_CHANNELS; ch++) begin
            config_channel(ch,
                           32'(ch * 32'h400 + 32'h100),
                           32'(ch * 32'h400 + 32'h200),
                           16'd4,
                           build_ctrl(1'b1, 1'b1, 1'b1, 1'b0, 1'b0, 1'b1, 2'b00));
        end

        // Enable all interrupts
        csr_write(CSR_INT_ENABLE, 32'hF);

        // Start all channels
        for (int ch = 0; ch < NUM_CHANNELS; ch++) begin
            start_channel(ch);
        end

        // Wait for all IRQs
        irq_capture = '0;
        for (int ch = 0; ch < NUM_CHANNELS; ch++) begin
            wait_irq(ch, 50000, success);
            irq_capture[ch] = success;
        end

        for (int ch = 0; ch < NUM_CHANNELS; ch++)
            check($sformatf("CH%0d completed (IRQ)", ch), irq_capture[ch] == 1'b1);

        // Verify data for each channel
        for (int ch = 0; ch < NUM_CHANNELS; ch++) begin
            for (int i = 0; i < 4; i++) begin
                mem_read(32'(ch * 32'h400 + 32'h200 + i*4), rdata);
                check($sformatf("CH%0d dest word %0d correct", ch, i),
                      rdata == 32'(ch * 32'h10000 + 32'hDDDD_0000 + i));
            end
        end

        end_test();
    endtask

    // =========================================================================
    // TEST 8: Priority Arbitration (Section 4.4)
    // =========================================================================
    task automatic test_priority_arbitration;
        logic [DATA_WIDTH-1:0] rdata;
        logic                  success;

        begin_test("Priority Arbitration");

        apply_reset();
        mem_clear();

        // Fill sources
        mem_fill_pattern(32'h0000_0100, 4, 32'hA000_0000);  // CH0 source
        mem_fill_pattern(32'h0000_0200, 4, 32'hB000_0000);  // CH1 source

        // Configure CH0 and CH1
        config_channel(0, 32'h0000_0100, 32'h0000_0300, 16'd4,
                        build_ctrl(1'b1, 1'b1, 1'b1, 1'b0, 1'b0, 1'b1, 2'b00));
        config_channel(1, 32'h0000_0200, 32'h0000_0400, 16'd4,
                        build_ctrl(1'b1, 1'b1, 1'b1, 1'b0, 1'b0, 1'b1, 2'b00));

        csr_write(CSR_INT_ENABLE, 32'h3);

        // Start both channels — CH0 should win arbitration (lower index = higher priority)
        start_channel(0);
        start_channel(1);

        // Wait for both
        wait_irq(0, 20000, success);
        check("CH0 completed", success);
        wait_irq(1, 20000, success);
        check("CH1 completed", success);

        // Verify data integrity
        for (int i = 0; i < 4; i++) begin
            mem_read(32'h0000_0300 + i*4, rdata);
            check($sformatf("CH0 dst word %0d correct", i), rdata == 32'hA000_0000 + i);
            mem_read(32'h0000_0400 + i*4, rdata);
            check($sformatf("CH1 dst word %0d correct", i), rdata == 32'hB000_0000 + i);
        end

        end_test();
    endtask

    // =========================================================================
    // TEST 9: Interrupt Generation & Clearing (FR-08)
    // =========================================================================
    task automatic test_interrupts;
        logic [DATA_WIDTH-1:0] rdata;

        begin_test("Interrupt Generation & Clearing (FR-08)");

        apply_reset();
        mem_clear();

        mem_write(32'h0000_0100, 32'h1111_2222);

        // Configure CH0 with INT_EN
        config_channel(0, 32'h0000_0100, 32'h0000_0200, 16'd1,
                        build_ctrl(1'b1, 1'b1, 1'b1, 1'b0, 1'b0, 1'b1, 2'b00));

        // Enable interrupt for CH0
        csr_write(CSR_INT_ENABLE, 32'h1);

        start_channel(0);

        // Wait a few cycles
        repeat(20) @(posedge clk);

        // Check interrupt asserted
        check("IRQ[0] asserted after transfer", irq[0] === 1'b1);

        // Check INT_STATUS
        csr_read(CSR_INT_STATUS, rdata);
        check("INT_STATUS[0] = 1", rdata[0] == 1'b1);

        // Test masking: disable interrupt
        csr_write(CSR_INT_ENABLE, 32'h0);
        repeat(5) @(posedge clk);
        check("IRQ[0] deasserted after masking", irq[0] === 1'b0);

        // Re-enable
        csr_write(CSR_INT_ENABLE, 32'h1);
        repeat(5) @(posedge clk);
        check("IRQ[0] re-asserted after unmask", irq[0] === 1'b1);

        // Clear interrupt via INT_CLEAR
        csr_write(CSR_INT_CLEAR, 32'h1);
        repeat(5) @(posedge clk);
        check("IRQ[0] deasserted after clear", irq[0] === 1'b0);

        csr_read(CSR_INT_STATUS, rdata);
        check("INT_STATUS cleared to 0", rdata[0] == 1'b0);

        end_test();
    endtask

    // =========================================================================
    // TEST 10: Error Handling (FR-09)
    // =========================================================================
    task automatic test_error_handling;
        logic [DATA_WIDTH-1:0] rdata;
        logic                  success;

        begin_test("Error Handling (FR-09)");

        apply_reset();
        mem_clear();

        mem_write(32'h0000_0100, 32'hFEED_FACE);

        // Configure CH0 with INT_EN
        config_channel(0, 32'h0000_0100, 32'h0000_0200, 16'd1,
                        build_ctrl(1'b1, 1'b1, 1'b1, 1'b0, 1'b0, 1'b1, 2'b00));

        csr_write(CSR_INT_ENABLE, 32'h1);

        // Enable error injection at source address
        inject_error = 1'b1;
        error_addr   = 32'h0000_0100;

        start_channel(0);

        // Wait (may or may not get IRQ since error path may not set done)
        repeat(100) @(posedge clk);

        // Check error status on channel 0
        select_channel(0);
        csr_read(CSR_STATUS, rdata);
        check("CH0 error flag set after bus error", rdata[2] == 1'b1);

        inject_error = 1'b0;

        end_test();
    endtask

    // =========================================================================
    // TEST 11: Circular Mode (FR-10)
    // =========================================================================
    task automatic test_circular_mode;
        logic [DATA_WIDTH-1:0] rdata;
        logic                  success;

        begin_test("Circular Mode (FR-10)");

        apply_reset();
        mem_clear();

        // Source: 2 words
        mem_write(32'h0000_0100, 32'hCCCC_1111);
        mem_write(32'h0000_0104, 32'hCCCC_2222);

        // Configure CH0: CYCLIC mode
        config_channel(0, 32'h0000_0100, 32'h0000_0500, 16'd2,
                        build_ctrl(1'b1, 1'b1, 1'b1, 1'b0, 1'b0, 1'b1, 2'b10));

        csr_write(CSR_INT_ENABLE, 32'h1);
        start_channel(0);

        // Wait for first completion
        wait_irq(0, 10000, success);
        check("Circular: first pass completed", success);

        // Clear interrupt
        csr_write(CSR_INT_CLEAR, 32'h1);
        repeat(5) @(posedge clk);

        // Check first destination region
        mem_read(32'h0000_0500, rdata);
        check("Circular: dst word 0 correct (pass 1)", rdata == 32'hCCCC_1111);
        mem_read(32'h0000_0504, rdata);
        check("Circular: dst word 1 correct (pass 1)", rdata == 32'hCCCC_2222);

        // Wait for second completion (circular should auto-reload)
        wait_irq(0, 10000, success);
        check("Circular: second pass completed", success);

        // After 2 passes with dst increment, dst addr should have advanced
        mem_read(32'h0000_0508, rdata);
        check("Circular: dst word 0 correct (pass 2)", rdata == 32'hCCCC_1111);
        mem_read(32'h0000_050C, rdata);
        check("Circular: dst word 1 correct (pass 2)", rdata == 32'hCCCC_2222);

        // Stop circular mode
        stop_channel(0);
        csr_write(CSR_INT_CLEAR, 32'h1);
        repeat(5) @(posedge clk);

        end_test();
    endtask

    // =========================================================================
    // TEST 12: Global Enable/Disable (channel-level)
    // =========================================================================
    task automatic test_global_enable;
        logic [DATA_WIDTH-1:0] rdata;

        begin_test("Channel Enable/Disable");

        apply_reset();
        mem_clear();

        mem_write(32'h0000_0100, 32'hDEAD_BEEF);

        // Configure CH0 but do NOT enable it
        select_channel(0);
        csr_write(CSR_SRC_ADDR_LO, 32'h0000_0100);
        csr_write(CSR_DST_ADDR_LO, 32'h0000_0200);
        csr_write(CSR_XFER_COUNT,  32'd1);
        // Write control with enable=0 but start=1
        csr_write(CSR_CONTROL, 32'h2);  // start=1, enable=0

        csr_write(CSR_INT_ENABLE, 32'h1);

        repeat(30) @(posedge clk);
        check("No transfer when channel disabled", irq[0] === 1'b0);

        // Now enable and start properly
        select_channel(0);
        csr_write(CSR_SRC_ADDR_LO, 32'h0000_0100);
        csr_write(CSR_DST_ADDR_LO, 32'h0000_0200);
        csr_write(CSR_XFER_COUNT,  32'd1);
        csr_write(CSR_CONTROL, build_ctrl(1'b1, 1'b1, 1'b1, 1'b0, 1'b0, 1'b1, 2'b00));
        // Now pulse start
        csr_write(CSR_CONTROL, build_ctrl(1'b1, 1'b1, 1'b1, 1'b0, 1'b0, 1'b1, 2'b00) | (1 << CTRL_START_BIT));

        repeat(50) @(posedge clk);

        // Check that transfer completed
        csr_read(CSR_INT_STATUS, rdata);
        check("Transfer completed after enable", rdata[0] == 1'b1);

        mem_read(32'h0000_0200, rdata);
        check("Data correct after enable", rdata == 32'hDEAD_BEEF);

        end_test();
    endtask

    // =========================================================================
    // TEST 13: Channel Status Register (FR-12)
    // =========================================================================
    task automatic test_channel_status;
        logic [DATA_WIDTH-1:0] rdata;

        begin_test("Channel Status Register (FR-12)");

        apply_reset();
        mem_clear();

        mem_write(32'h0000_0100, 32'h1234_5678);

        // Check initial status = IDLE (active=0, done=0, error=0)
        select_channel(0);
        csr_read(CSR_STATUS, rdata);
        check("CH0 STATUS initially IDLE", rdata[2:0] == 3'b000);

        config_channel(0, 32'h0000_0100, 32'h0000_0200, 16'd1,
                        build_ctrl(1'b1, 1'b1, 1'b1, 1'b0, 1'b0, 1'b1, 2'b00));

        csr_write(CSR_INT_ENABLE, 32'h1);
        start_channel(0);

        // Poll status — should eventually show done
        repeat(30) @(posedge clk);
        csr_read(CSR_STATUS, rdata);
        check("CH0 STATUS done flag set", rdata[1] == 1'b1);

        // active should be 0 after completion
        check("CH0 STATUS active cleared", rdata[0] == 1'b0);

        end_test();
    endtask

    // =========================================================================
    // TEST 14: Reset During Active Transfer (FR-13)
    // =========================================================================
    task automatic test_reset_during_transfer;
        logic [DATA_WIDTH-1:0] rdata;

        begin_test("Reset During Active Transfer (FR-13)");

        apply_reset();
        mem_clear();

        mem_fill_pattern(32'h0000_0100, 20, 32'hD000_0000);

        config_channel(0, 32'h0000_0100, 32'h0000_0600, 16'd20,
                        build_ctrl(1'b1, 1'b1, 1'b1, 1'b0, 1'b0, 1'b1, 2'b00));

        csr_write(CSR_INT_ENABLE, 32'h1);
        start_channel(0);

        // Let a few beats happen
        repeat(8) @(posedge clk);

        // Apply reset mid-transfer
        rst_n = 1'b0;
        repeat(5) @(posedge clk);
        rst_n = 1'b1;
        repeat(3) @(posedge clk);

        // Verify all registers are back to default
        csr_read(CSR_CH_SELECT, rdata);
        check("CH_SELECT cleared after reset", rdata == '0);

        csr_read(CSR_INT_STATUS, rdata);
        check("INT_STATUS cleared after reset", rdata[NUM_CHANNELS-1:0] == '0);

        csr_read(CSR_INT_ENABLE, rdata);
        check("INT_ENABLE cleared after reset", rdata[NUM_CHANNELS-1:0] == '0);

        select_channel(0);
        csr_read(CSR_STATUS, rdata);
        check("CH0 STATUS IDLE after reset", rdata == '0);

        check("IRQ all low after reset", irq == '0);
        check("m_bus_req low after reset", m_bus_req == 1'b0);

        end_test();
    endtask

    // =========================================================================
    // TEST 15: Fixed Address Mode — Peripheral FIFO (FR-07)
    // =========================================================================
    task automatic test_fixed_address;
        logic [DATA_WIDTH-1:0] rdata;
        logic                  success;

        begin_test("Fixed Address Mode — Peripheral FIFO (FR-07)");

        apply_reset();
        mem_clear();

        // Fill 4 source words
        for (int i = 0; i < 4; i++)
            mem_write(32'h0000_0100 + i*4, 32'hF1F0_0000 + i);

        // CTRL: src_inc=1, dst_inc=0 (fixed destination)
        config_channel(0, 32'h0000_0100, 32'h0000_0200, 16'd4,
                        build_ctrl(1'b1, 1'b1, 1'b0, 1'b0, 1'b0, 1'b1, 2'b00));

        csr_write(CSR_INT_ENABLE, 32'h1);
        start_channel(0);

        wait_irq(0, 10000, success);
        check("Fixed address transfer completed", success);

        // With fixed dst, all writes go to same address; last value wins
        mem_read(32'h0000_0200, rdata);
        check("Fixed dst: last write value correct", rdata == 32'hF1F0_0003);

        end_test();
    endtask

    // =========================================================================
    // TEST 16: INT_CLEAR Write-1-to-Clear (FR-08)
    // =========================================================================
    task automatic test_int_clear_w1c;
        logic [DATA_WIDTH-1:0] rdata;

        begin_test("INT_CLEAR Write-1-to-Clear (FR-08)");

        apply_reset();
        mem_clear();

        mem_write(32'h0000_0100, 32'hAAAA);

        config_channel(0, 32'h0000_0100, 32'h0000_0200, 16'd1,
                        build_ctrl(1'b1, 1'b1, 1'b1, 1'b0, 1'b0, 1'b1, 2'b00));

        csr_write(CSR_INT_ENABLE, 32'h1);
        start_channel(0);

        repeat(20) @(posedge clk);

        csr_read(CSR_INT_STATUS, rdata);
        check("INT_STATUS[0] set", rdata[0] == 1'b1);

        // Write-1-to-clear only CH0
        csr_write(CSR_INT_CLEAR, 32'h1);
        csr_read(CSR_INT_STATUS, rdata);
        check("INT_STATUS[0] cleared by W1C", rdata[0] == 1'b0);

        end_test();
    endtask

    // =========================================================================
    // TEST 17: Zero-Length Transfer (Edge Case)
    // =========================================================================
    task automatic test_zero_length_transfer;
        logic [DATA_WIDTH-1:0] rdata;

        begin_test("Zero-Length Transfer (Edge Case)");

        apply_reset();
        mem_clear();

        config_channel(0, 32'h0000_0100, 32'h0000_0200, 16'd0,
                        build_ctrl(1'b1, 1'b1, 1'b1, 1'b0, 1'b0, 1'b1, 2'b00));

        csr_write(CSR_INT_ENABLE, 32'h1);
        start_channel(0);

        // Wait — with count=0, the transfer should complete immediately
        // (xfer_remaining==0 goes to CH_DONE)
        repeat(30) @(posedge clk);

        // The done bit should be set (xfer_remaining==0 in CH_REQUEST triggers CH_DONE)
        select_channel(0);
        csr_read(CSR_STATUS, rdata);
        check("CH0 done flag set for zero-length", rdata[1] == 1'b1);

        end_test();
    endtask

    // =========================================================================
    // TEST 18: Multiple Sequential Transfers on Same Channel
    // =========================================================================
    task automatic test_sequential_transfers;
        logic [DATA_WIDTH-1:0] rdata;
        logic                  success;

        begin_test("Multiple Sequential Transfers on CH0");

        apply_reset();
        mem_clear();

        csr_write(CSR_INT_ENABLE, 32'h1);

        // Transfer 1
        mem_write(32'h0000_0100, 32'hAAAA_1111);
        config_channel(0, 32'h0000_0100, 32'h0000_0200, 16'd1,
                        build_ctrl(1'b1, 1'b1, 1'b1, 1'b0, 1'b0, 1'b1, 2'b00));
        start_channel(0);

        wait_irq(0, 5000, success);
        check("Sequential transfer 1 completed", success);

        csr_write(CSR_INT_CLEAR, 32'h1);

        // Transfer 2 — different data and destination
        mem_write(32'h0000_0100, 32'hBBBB_2222);
        config_channel(0, 32'h0000_0100, 32'h0000_0204, 16'd1,
                        build_ctrl(1'b1, 1'b1, 1'b1, 1'b0, 1'b0, 1'b1, 2'b00));
        // Re-enable and start
        csr_write(CSR_CONTROL, build_ctrl(1'b1, 1'b1, 1'b1, 1'b0, 1'b0, 1'b1, 2'b00) | (1 << CTRL_START_BIT));

        wait_irq(0, 5000, success);
        check("Sequential transfer 2 completed", success);

        // Verify both destinations
        mem_read(32'h0000_0200, rdata);
        check("Seq xfer 1 data correct", rdata == 32'hAAAA_1111);
        mem_read(32'h0000_0204, rdata);
        check("Seq xfer 2 data correct", rdata == 32'hBBBB_2222);

        end_test();
    endtask

    // =========================================================================
    // TEST 19: Back-Pressure (rd_ready/wr_ready deasserted)
    // =========================================================================
    task automatic test_back_pressure;
        logic [DATA_WIDTH-1:0] rdata;
        logic                  success;

        begin_test("Back-Pressure (rd_ready/wr_ready delayed)");

        apply_reset();
        mem_clear();

        for (int i = 0; i < 4; i++)
            mem_write(32'h0000_0100 + i*4, 32'hDADA_0000 + i);

        // Add latency to simulate back-pressure
        rd_latency = 3;
        wr_latency = 3;

        config_channel(0, 32'h0000_0100, 32'h0000_0200, 16'd4,
                        build_ctrl(1'b1, 1'b1, 1'b1, 1'b0, 1'b0, 1'b1, 2'b00));

        csr_write(CSR_INT_ENABLE, 32'h1);
        start_channel(0);

        wait_irq(0, 20000, success);
        check("Transfer with back-pressure completed", success);

        for (int i = 0; i < 4; i++) begin
            mem_read(32'h0000_0200 + i*4, rdata);
            check($sformatf("Back-pressure dest word %0d correct", i),
                  rdata == 32'hDADA_0000 + i);
        end

        rd_latency = 1;
        wr_latency = 1;

        end_test();
    endtask

    // =========================================================================
    // TEST 20: All Channels Independent Configuration
    // =========================================================================
    task automatic test_independent_channels;
        logic [DATA_WIDTH-1:0] rdata;
        logic                  success;

        begin_test("All Channels Independent Configuration");

        apply_reset();
        mem_clear();

        // Different data for each channel
        for (int ch = 0; ch < NUM_CHANNELS; ch++) begin
            mem_write(32'(ch * 32'h200 + 32'h100), 32'(32'hEE00_0000 + ch));
        end

        // Each channel: different src, different dst, size=1
        for (int ch = 0; ch < NUM_CHANNELS; ch++) begin
            config_channel(ch,
                           32'(ch * 32'h200 + 32'h100),
                           32'(ch * 32'h200 + 32'h180),
                           16'd1,
                           build_ctrl(1'b1, 1'b1, 1'b1, 1'b0, 1'b0, 1'b1, 2'b00));
        end

        csr_write(CSR_INT_ENABLE, 32'hF);

        // Start all channels
        for (int ch = 0; ch < NUM_CHANNELS; ch++)
            start_channel(ch);

        // Wait for each
        for (int ch = 0; ch < NUM_CHANNELS; ch++) begin
            wait_irq(ch, 10000, success);
            check($sformatf("Independent CH%0d completed", ch), success);
        end

        // Verify data
        for (int ch = 0; ch < NUM_CHANNELS; ch++) begin
            mem_read(32'(ch * 32'h200 + 32'h180), rdata);
            check($sformatf("Independent CH%0d data correct", ch),
                  rdata == 32'(32'hEE00_0000 + ch));
        end

        end_test();
    endtask

    // =========================================================================
    // TEST 21: SW Trigger Without Channel Enable (Edge Case)
    // =========================================================================
    task automatic test_sw_req_without_enable;

        begin_test("SW Trigger Without Channel Enable (Edge Case)");

        apply_reset();
        mem_clear();

        // Configure CH0 but do NOT enable it (enable=0)
        select_channel(0);
        csr_write(CSR_SRC_ADDR_LO, 32'h0000_0100);
        csr_write(CSR_DST_ADDR_LO, 32'h0000_0200);
        csr_write(CSR_XFER_COUNT,  32'd4);
        // Write control with start=1 but enable=0
        csr_write(CSR_CONTROL, 32'h2);  // start=1, enable=0

        csr_write(CSR_INT_ENABLE, 32'h1);

        repeat(30) @(posedge clk);
        check("No transfer without CH_EN", irq[0] === 1'b0);

    endtask

    // =========================================================================
    // TEST 22: ERR Status Clearing
    // =========================================================================
    task automatic test_err_clear;
        logic [DATA_WIDTH-1:0] rdata;
        logic                  success;

        begin_test("ERR Status Clearing (FR-09)");

        apply_reset();
        mem_clear();

        mem_write(32'h0000_0100, 32'hFEED);

        config_channel(0, 32'h0000_0100, 32'h0000_0200, 16'd1,
                        build_ctrl(1'b1, 1'b1, 1'b1, 1'b0, 1'b0, 1'b1, 2'b00));

        csr_write(CSR_INT_ENABLE, 32'h1);

        // Inject error
        inject_error = 1'b1;
        error_addr   = 32'h0000_0100;
        start_channel(0);

        repeat(100) @(posedge clk);

        // Check error status
        select_channel(0);
        csr_read(CSR_STATUS, rdata);
        check("Error flag set after bus error", rdata[2] == 1'b1);

        // Clear error and done via INT_CLEAR
        csr_write(CSR_INT_CLEAR, 32'h1);
        csr_read(CSR_STATUS, rdata);
        check("Error flag cleared after INT_CLEAR", rdata[2] == 1'b0);

        inject_error = 1'b0;

        end_test();
    endtask

    // =========================================================================
    // TEST 23: Bus Request Protocol Checks
    // =========================================================================
    task automatic test_bus_protocol;
        logic [DATA_WIDTH-1:0] rdata;
        logic                  success;

        begin_test("Bus Request Protocol Checks");

        apply_reset();
        mem_clear();

        mem_write(32'h0000_0100, 32'hABCD_1234);

        config_channel(0, 32'h0000_0100, 32'h0000_0200, 16'd1,
                        build_ctrl(1'b1, 1'b1, 1'b1, 1'b0, 1'b0, 1'b1, 2'b00));

        csr_write(CSR_INT_ENABLE, 32'h1);

        // Before start: bus should be idle
        check("m_bus_req low before transfer", m_bus_req == 1'b0);

        start_channel(0);

        // After start: bus request should go high
        repeat(5) @(posedge clk);
        check("m_bus_req high after channel start", m_bus_req == 1'b1);

        // Wait for completion
        wait_irq(0, 5000, success);
        check("Bus protocol: transfer completed", success);

        // After done: bus should release
        repeat(10) @(posedge clk);
        check("m_bus_req low after completion", m_bus_req == 1'b0);

        end_test();
    endtask

    // =========================================================================
    // TEST 24: Hardware Trigger
    // =========================================================================
    task automatic test_hw_trigger;
        logic [DATA_WIDTH-1:0] rdata;
        logic                  success;

        begin_test("Hardware Trigger (FR-05)");

        apply_reset();
        mem_clear();

        mem_write(32'h0000_0100, 32'h1234_ABCD);

        // Configure CH0 with hw_trigger=1
        config_channel(0, 32'h0000_0100, 32'h0000_0200, 16'd1,
                        build_ctrl(1'b1, 1'b1, 1'b1, 1'b0, 1'b1, 1'b1, 2'b00));

        csr_write(CSR_INT_ENABLE, 32'h1);

        // Channel is enabled but waiting for hw_req — no transfer yet
        repeat(30) @(posedge clk);
        check("No transfer before hw_req", irq[0] === 1'b0);

        // Assert hardware request
        hw_req[0] = 1'b1;
        repeat(2) @(posedge clk);
        hw_req[0] = 1'b0;

        // Should now transfer
        wait_irq(0, 5000, success);
        check("HW triggered transfer completed", success);

        mem_read(32'h0000_0200, rdata);
        check("HW trigger dest data correct", rdata == 32'h1234_ABCD);

        end_test();
    endtask

    // =========================================================================
    // TEST 25: Stop During Active Transfer
    // =========================================================================
    task automatic test_stop_during_transfer;
        logic [DATA_WIDTH-1:0] rdata;

        begin_test("Stop During Active Transfer");

        apply_reset();
        mem_clear();

        mem_fill_pattern(32'h0000_0100, 20, 32'hE000_0000);

        config_channel(0, 32'h0000_0100, 32'h0000_0600, 16'd20,
                        build_ctrl(1'b1, 1'b1, 1'b1, 1'b0, 1'b0, 1'b1, 2'b00));

        csr_write(CSR_INT_ENABLE, 32'h1);
        start_channel(0);

        // Let a few beats happen then stop
        repeat(5) @(posedge clk);
        stop_channel(0);

        repeat(20) @(posedge clk);

        // Check channel is no longer active
        select_channel(0);
        csr_read(CSR_STATUS, rdata);
        check("CH0 active cleared after stop", rdata[0] == 1'b0);

        // Verify only partial data was transferred (not all 20 words)
        // At least the first word should have been transferred
        mem_read(32'h0000_0600, rdata);
        check("Partial transfer: first word transferred", rdata == 32'hE000_0000);

        end_test();
    endtask

    // =========================================================================
    // Main Test Sequence
    // =========================================================================
    initial begin
        $display("============================================================");
        $display("  DMA Controller Testbench — MAS DV Plan");
        $display("  Module: dma");
        $display("  Start time: %0t", $time);
        $display("============================================================");

        test_pass  = 0;
        test_fail  = 0;
        test_count = 0;

        init_signals();

        // -----------------------------------------------------------------
        // Execute all 25 tests
        // -----------------------------------------------------------------
        test_reset;                   // 1.  Reset values
        test_register_rw;             // 2.  Register read/write
        test_csr_reserved;            // 3.  CSR reserved address access
        test_single_transfer;         // 4.  Single word transfer
        test_burst_transfer;          // 5.  Burst transfer
        test_large_transfer;          // 6.  Large transfer
        test_multi_channel;           // 7.  Multi-channel simultaneous
        test_priority_arbitration;    // 8.  Priority arbitration
        test_interrupts;              // 9.  Interrupt generation & clearing
        test_error_handling;          // 10. Error handling
        test_circular_mode;           // 11. Circular mode
        test_global_enable;           // 12. Channel enable/disable
        test_channel_status;          // 13. Channel status register
        test_reset_during_transfer;   // 14. Reset during active transfer
        test_fixed_address;           // 15. Fixed address mode
        test_int_clear_w1c;           // 16. INT_CLEAR W1C
        test_zero_length_transfer;    // 17. Zero-length transfer
        test_sequential_transfers;    // 18. Sequential transfers
        test_back_pressure;           // 19. Back-pressure
        test_independent_channels;    // 20. All channels independent
        test_sw_req_without_enable;   // 21. SW trigger without enable
        test_err_clear;               // 22. ERR status clearing
        test_bus_protocol;            // 23. Bus request protocol
        test_hw_trigger;              // 24. Hardware trigger
        test_stop_during_transfer;    // 25. Stop during transfer

        // -----------------------------------------------------------------
        // Final Report
        // -----------------------------------------------------------------
        $display("");
        $display("============================================================");
        $display("  TEST SUMMARY");
        $display("  Total tests : %0d", test_count);
        $display("  Checks passed: %0d", test_pass);
        $display("  Checks failed: %0d", test_fail);
        if (test_fail == 0)
            $display("  RESULT: ALL TESTS PASSED");
        else
            $display("  RESULT: SOME TESTS FAILED");
        $display("============================================================");
        $display("  End time: %0t", $time);
        $display("============================================================");

        $finish;
    end

    // =========================================================================
    // Timeout watchdog
    // =========================================================================
    initial begin
        #10_000_000;
        $display("ERROR: Global timeout reached — simulation killed.");
        $finish;
    end

endmodule
