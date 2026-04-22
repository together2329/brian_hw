`default_nettype none
`timescale 1ns/1ps

module tb_dma_ctrl;

    // ========================================================================
    // Parameters
    // ========================================================================
    parameter int DATA_WIDTH    = 32;
    parameter int ADDR_WIDTH    = 32;
    parameter int ID_WIDTH      = 4;
    parameter int NUM_CHANNELS  = 8;
    parameter int FIFO_DEPTH    = 16;
    parameter int MAX_BURST_LEN = 16;
    parameter int PERIOD        = 10; // 100 MHz

    // ========================================================================
    // Clock and Reset
    // ========================================================================
    logic axi_clk;
    logic axi_rst_n;

    initial axi_clk = 1'b0;
    always #(PERIOD/2) axi_clk = ~axi_clk;

    // ========================================================================
    // AXI4-Lite Slave Interface (register programming from testbench)
    // ========================================================================
    logic [11:0]  s_axi_awaddr;
    logic [2:0]   s_axi_awprot;
    logic         s_axi_awvalid;
    logic         s_axi_awready;
    logic [31:0]  s_axi_wdata;
    logic [3:0]   s_axi_wstrb;
    logic         s_axi_wvalid;
    logic         s_axi_wready;
    logic [1:0]   s_axi_bresp;
    logic         s_axi_bvalid;
    logic         s_axi_bready;
    logic [11:0]  s_axi_araddr;
    logic [2:0]   s_axi_arprot;
    logic         s_axi_arvalid;
    logic         s_axi_arready;
    logic [31:0]  s_axi_rdata;
    logic [1:0]   s_axi_rresp;
    logic         s_axi_rvalid;
    logic         s_axi_rready;

    // ========================================================================
    // AXI4 Master Interface (DUT drives these; memory model responds)
    // ========================================================================
    logic [ID_WIDTH-1:0]       m_axi_awid;
    logic [ADDR_WIDTH-1:0]     m_axi_awaddr;
    logic [7:0]                m_axi_awlen;
    logic [2:0]                m_axi_awsize;
    logic [1:0]                m_axi_awburst;
    logic [2:0]                m_axi_awprot;
    logic [3:0]                m_axi_awcache;
    logic                      m_axi_awvalid;
    logic                      m_axi_awready;
    logic [DATA_WIDTH-1:0]     m_axi_wdata;
    logic [DATA_WIDTH/8-1:0]   m_axi_wstrb;
    logic                      m_axi_wlast;
    logic                      m_axi_wvalid;
    logic                      m_axi_wready;
    logic [ID_WIDTH-1:0]       m_axi_bid;
    logic [1:0]                m_axi_bresp;
    logic                      m_axi_bvalid;
    logic                      m_axi_bready;
    logic [ID_WIDTH-1:0]       m_axi_arid;
    logic [ADDR_WIDTH-1:0]     m_axi_araddr;
    logic [7:0]                m_axi_arlen;
    logic [2:0]                m_axi_arsize;
    logic [1:0]                m_axi_arburst;
    logic [2:0]                m_axi_arprot;
    logic [3:0]                m_axi_arcache;
    logic                      m_axi_arvalid;
    logic                      m_axi_arready;
    logic [ID_WIDTH-1:0]       m_axi_rid;
    logic [DATA_WIDTH-1:0]     m_axi_rdata;
    logic [1:0]                m_axi_rresp;
    logic                      m_axi_rlast;
    logic                      m_axi_rvalid;
    logic                      m_axi_rready;

    // ========================================================================
    // Peripheral DMA Request Interface
    // ========================================================================
    logic [NUM_CHANNELS-1:0]   dma_req;
    logic [NUM_CHANNELS-1:0]   dma_ack;
    logic [NUM_CHANNELS-1:0]   dma_eop;

    // ========================================================================
    // Interrupt Interface
    // ========================================================================
    logic [NUM_CHANNELS-1:0]   irq;

    // ========================================================================
    // Test tracking
    // ========================================================================
    int test_count;
    int pass_count;
    int fail_count;

    // ========================================================================
    // DUT Instantiation
    // ========================================================================
    dma_ctrl #(
        .DATA_WIDTH    (DATA_WIDTH),
        .ADDR_WIDTH    (ADDR_WIDTH),
        .ID_WIDTH      (ID_WIDTH),
        .NUM_CHANNELS  (NUM_CHANNELS),
        .FIFO_DEPTH    (FIFO_DEPTH),
        .MAX_BURST_LEN (MAX_BURST_LEN)
    ) dut (.*);

    // ========================================================================
    // AXI4-Lite Slave VIP — register read/write tasks
    // ========================================================================
    task axi_lite_write(input logic [11:0] addr, input logic [31:0] data);
        begin
            // AW phase
            @(posedge axi_clk);
            s_axi_awaddr  <= addr;
            s_axi_awprot  <= 3'b000;
            s_axi_awvalid <= 1'b1;
            s_axi_wdata   <= data;
            s_axi_wstrb   <= 4'hF;
            s_axi_wvalid  <= 1'b1;
            s_axi_bready  <= 1'b1;
            // Wait for AW ready
            while (!s_axi_awready) @(posedge axi_clk);
            @(posedge axi_clk);
            s_axi_awvalid <= 1'b0;
            // Wait for W ready
            while (!s_axi_wready) @(posedge axi_clk);
            @(posedge axi_clk);
            s_axi_wvalid <= 1'b0;
            // Wait for B response
            while (!s_axi_bvalid) @(posedge axi_clk);
            @(posedge axi_clk);
            s_axi_bready  <= 1'b0;
            s_axi_awvalid <= 1'b0;
            s_axi_wvalid  <= 1'b0;
        end
    endtask

    task axi_lite_read(input logic [11:0] addr, output logic [31:0] data);
        begin
            @(posedge axi_clk);
            s_axi_araddr  <= addr;
            s_axi_arprot  <= 3'b000;
            s_axi_arvalid <= 1'b1;
            s_axi_rready  <= 1'b1;
            // Wait for AR ready
            while (!s_axi_arready) @(posedge axi_clk);
            @(posedge axi_clk);
            s_axi_arvalid <= 1'b0;
            // Wait for R valid
            while (!s_axi_rvalid) @(posedge axi_clk);
            data = s_axi_rdata;
            @(posedge axi_clk);
            s_axi_rready  <= 1'b0;
            s_axi_arvalid <= 1'b0;
        end
    endtask

    // ========================================================================
    // AXI4 Master Memory Model — responds to DUT's AXI master requests
    // ========================================================================
    // Simple byte-addressed memory: 64KB address space
    localparam MEM_SIZE = 65536;
    logic [7:0] mem_array [0:MEM_SIZE-1];

    // Write address channel tracking
    logic [ADDR_WIDTH-1:0] wr_addr;
    logic [7:0]            wr_len;
    logic [2:0]            wr_size;
    logic [1:0]            wr_burst_type;
    logic                  wr_active;
    logic [7:0]            wr_beat_cnt;

    // Read address channel tracking
    logic [ADDR_WIDTH-1:0] rd_addr;
    logic [7:0]            rd_len;
    logic [2:0]            rd_size;
    logic [1:0]            rd_burst_type;
    logic                  rd_active;
    logic [7:0]            rd_beat_cnt;

    // Error injection control
    logic                  inject_slverr_rd;
    logic                  inject_slverr_wr;

    // AXI Write Address Channel handler
    always @(posedge axi_clk or negedge axi_rst_n) begin
        if (!axi_rst_n) begin
            m_axi_awready <= 1'b1;
            wr_active     <= 1'b0;
            wr_addr       <= '0;
            wr_len        <= '0;
            wr_size       <= '0;
            wr_burst_type <= '0;
        end else begin
            if (!wr_active && m_axi_awvalid && m_axi_awready) begin
                m_axi_awready <= 1'b0;
                wr_addr       <= m_axi_awaddr;
                wr_len        <= m_axi_awlen;
                wr_size       <= m_axi_awsize;
                wr_burst_type <= m_axi_awburst;
                wr_active     <= 1'b1;
                wr_beat_cnt   <= '0;
            end
            if (wr_active) begin
                // Handled in write data phase
            end
        end
    end

    // AXI Write Data Channel handler
    always @(posedge axi_clk or negedge axi_rst_n) begin
        if (!axi_rst_n) begin
            m_axi_wready <= 1'b0;
        end else begin
            if (wr_active)
                m_axi_wready <= 1'b1;
            else
                m_axi_wready <= 1'b0;

            if (wr_active && m_axi_wvalid && m_axi_wready) begin
                // Store data to memory (unrolled for 32-bit DATA_WIDTH)
                if (m_axi_wstrb[0]) mem_array[wr_addr + wr_beat_cnt * 4 + 0] <= m_axi_wdata[7:0];
                if (m_axi_wstrb[1]) mem_array[wr_addr + wr_beat_cnt * 4 + 1] <= m_axi_wdata[15:8];
                if (m_axi_wstrb[2]) mem_array[wr_addr + wr_beat_cnt * 4 + 2] <= m_axi_wdata[23:16];
                if (m_axi_wstrb[3]) mem_array[wr_addr + wr_beat_cnt * 4 + 3] <= m_axi_wdata[31:24];
                if (wr_beat_cnt == wr_len || m_axi_wlast) begin
                    wr_active     <= 1'b0;
                    m_axi_awready <= 1'b1;
                end
                wr_beat_cnt <= wr_beat_cnt + 1'b1;
            end
        end
    end

    // AXI Write Response Channel handler
    logic wr_last_beat_seen;
    always @(posedge axi_clk or negedge axi_rst_n) begin
        if (!axi_rst_n) begin
            m_axi_bvalid <= 1'b0;
            m_axi_bid    <= '0;
            m_axi_bresp  <= 2'b00;
            wr_last_beat_seen <= 1'b0;
        end else begin
            if (wr_active && m_axi_wvalid && m_axi_wready && (wr_beat_cnt == wr_len || m_axi_wlast)) begin
                wr_last_beat_seen <= 1'b1;
                m_axi_bid    <= m_axi_awid;
                m_axi_bresp  <= inject_slverr_wr ? 2'b10 : 2'b00;
            end

            if (wr_last_beat_seen && !m_axi_bvalid) begin
                m_axi_bvalid <= 1'b1;
                wr_last_beat_seen <= 1'b0;
            end else if (m_axi_bvalid && m_axi_bready) begin
                m_axi_bvalid <= 1'b0;
            end
        end
    end

    // AXI Read Address Channel handler
    always @(posedge axi_clk or negedge axi_rst_n) begin
        if (!axi_rst_n) begin
            m_axi_arready <= 1'b1;
            rd_active     <= 1'b0;
            rd_addr       <= '0;
            rd_len        <= '0;
            rd_size       <= '0;
            rd_burst_type <= '0;
        end else begin
            if (!rd_active && m_axi_arvalid && m_axi_arready) begin
                m_axi_arready <= 1'b0;
                rd_addr       <= m_axi_araddr;
                rd_len        <= m_axi_arlen;
                rd_size       <= m_axi_arsize;
                rd_burst_type <= m_axi_arburst;
                rd_active     <= 1'b1;
                rd_beat_cnt   <= '0;
            end
        end
    end

    // AXI Read Data Channel handler
    // Combinational: compute read data from memory
    logic [ADDR_WIDTH-1:0] rd_byte_addr_0, rd_byte_addr_1, rd_byte_addr_2, rd_byte_addr_3;
    logic [31:0] rd_data_comb;

    always_comb begin
        if (rd_burst_type == 2'b00) begin // FIXED
            rd_byte_addr_0 = rd_addr + 0;
            rd_byte_addr_1 = rd_addr + 1;
            rd_byte_addr_2 = rd_addr + 2;
            rd_byte_addr_3 = rd_addr + 3;
        end else begin // INCR
            rd_byte_addr_0 = rd_addr + rd_beat_cnt * (DATA_WIDTH/8) + 0;
            rd_byte_addr_1 = rd_addr + rd_beat_cnt * (DATA_WIDTH/8) + 1;
            rd_byte_addr_2 = rd_addr + rd_beat_cnt * (DATA_WIDTH/8) + 2;
            rd_byte_addr_3 = rd_addr + rd_beat_cnt * (DATA_WIDTH/8) + 3;
        end
        rd_data_comb = '0;
        if (rd_byte_addr_0 < MEM_SIZE) rd_data_comb[7:0]   = mem_array[rd_byte_addr_0];
        if (rd_byte_addr_1 < MEM_SIZE) rd_data_comb[15:8]  = mem_array[rd_byte_addr_1];
        if (rd_byte_addr_2 < MEM_SIZE) rd_data_comb[23:16] = mem_array[rd_byte_addr_2];
        if (rd_byte_addr_3 < MEM_SIZE) rd_data_comb[31:24] = mem_array[rd_byte_addr_3];
    end

    // Make read data combinational (not registered) so it tracks beat count
    assign m_axi_rdata = rd_data_comb;

    always @(posedge axi_clk or negedge axi_rst_n) begin
        if (!axi_rst_n) begin
            m_axi_rvalid <= 1'b0;
            m_axi_rresp  <= 2'b00;
            m_axi_rlast  <= 1'b0;
            m_axi_rid    <= '0;
        end else begin
            if (rd_active) begin
                m_axi_rid    <= m_axi_arid;
                m_axi_rresp  <= inject_slverr_rd ? 2'b10 : 2'b00;
                if (m_axi_rvalid && m_axi_rready) begin
                    // Handshake happened — advance beat count
                    if (rd_beat_cnt == rd_len) begin
                        // Last beat acknowledged — terminate burst
                        rd_active     <= 1'b0;
                        m_axi_arready <= 1'b1;
                        m_axi_rvalid  <= 1'b0;
                        m_axi_rlast   <= 1'b0;
                    end else begin
                        rd_beat_cnt <= rd_beat_cnt + 1'b1;
                        m_axi_rlast <= (rd_beat_cnt + 1'b1 == rd_len);
                    end
                end else begin
                    // No handshake — assert valid and compute rlast
                    m_axi_rvalid <= 1'b1;
                    m_axi_rlast  <= (rd_beat_cnt == rd_len);
                end
            end else begin
                m_axi_rvalid <= 1'b0;
                m_axi_rlast  <= 1'b0;
            end
        end
    end

    // ========================================================================
    // Memory helper tasks
    // ========================================================================
    task mem_write32(input logic [ADDR_WIDTH-1:0] addr, input logic [31:0] data);
        begin
            mem_array[addr+0] <= data[7:0];
            mem_array[addr+1] <= data[15:8];
            mem_array[addr+2] <= data[23:16];
            mem_array[addr+3] <= data[31:24];
        end
    endtask

    task mem_read32(input logic [ADDR_WIDTH-1:0] addr, output logic [31:0] data);
        begin
            data[7:0]   = mem_array[addr+0];
            data[15:8]  = mem_array[addr+1];
            data[23:16] = mem_array[addr+2];
            data[31:24] = mem_array[addr+3];
        end
    endtask

    task mem_fill_pattern(input logic [ADDR_WIDTH-1:0] base, input int len);
        begin
            for (int i = 0; i < len; i = i + 4) begin
                mem_write32(base + i, 32'hA5000000 | i);
            end
        end
    endtask

    task mem_check_pattern(input logic [ADDR_WIDTH-1:0] base, input int len);
        begin
            logic [31:0] expected, actual;
            bit ok;
            ok = 1'b1;
            for (int i = 0; i < len; i = i + 4) begin
                expected = 32'hA5000000 | i;
                mem_read32(base + i, actual);
                if (actual !== expected) begin
                    $display("  [FAIL] mem[%08h] = %08h, expected %08h", base+i, actual, expected);
                    ok = 1'b0;
                end
            end
            if (ok) test_pass("mem_check_pattern");
            else    test_fail("mem_check_pattern");
        end
    endtask

    // ========================================================================
    // Test pass/fail helpers
    // ========================================================================
    task test_pass(input string name);
        begin
            $display("[PASS] %s", name);
            pass_count = pass_count + 1;
            test_count = test_count + 1;
        end
    endtask

    task test_fail(input string name);
        begin
            $display("[FAIL] %s", name);
            fail_count = fail_count + 1;
            test_count = test_count + 1;
        end
    endtask

    task check_eq(input string name, input logic [31:0] actual, input logic [31:0] expected);
        begin
            if (actual === expected) test_pass(name);
            else begin
                $display("  [FAIL] %s: got %08h, expected %08h", name, actual, expected);
                test_fail(name);
            end
        end
    endtask

    // ========================================================================
    // Reset task
    // ========================================================================
    task apply_reset;
        begin
            axi_rst_n = 1'b0;
            repeat(20) @(posedge axi_clk);
            axi_rst_n = 1'b1;
            repeat(4) @(posedge axi_clk);
        end
    endtask

    // ========================================================================
    // Wait for IRQ with timeout
    // ========================================================================
    task wait_irq(input int ch, input int timeout_cycles);
        begin
            int cnt;
            cnt = 0;
            while (!irq[ch] && cnt < timeout_cycles) begin
                @(posedge axi_clk);
                cnt = cnt + 1;
            end
            if (irq[ch])
                test_pass($sformatf("wait_irq[%0d]", ch));
            else
                test_fail($sformatf("wait_irq[%0d] TIMEOUT", ch));
        end
    endtask

    // ========================================================================
    // Idle init
    // ========================================================================
    initial begin
        // AXI-Lite slave init
        s_axi_awvalid = 1'b0;
        s_axi_awaddr  = '0;
        s_axi_awprot  = '0;
        s_axi_wvalid  = 1'b0;
        s_axi_wdata   = '0;
        s_axi_wstrb   = '0;
        s_axi_bready  = 1'b0;
        s_axi_arvalid = 1'b0;
        s_axi_araddr  = '0;
        s_axi_arprot  = '0;
        s_axi_rready  = 1'b0;

        // Peripheral interface init
        dma_req = '0;
        dma_eop = '0;

        // Error injection off
        inject_slverr_rd = 1'b0;
        inject_slverr_wr = 1'b0;

        // Init memory
        for (int i = 0; i < MEM_SIZE; i = i + 1)
            mem_array[i] = 8'd0;

        test_count = 0;
        pass_count = 0;
        fail_count = 0;
    end

    // ========================================================================
    // Waveform dump
    // ========================================================================
    initial begin
        $dumpfile("dma_ctrl_wave.vcd");
        $dumpvars(0, tb_dma_ctrl);
    end

    // ========================================================================
    // Include test cases
    // ========================================================================
    `include "dma_ctrl/tb/tc_dma_ctrl.sv"

    // ========================================================================
    // Main test sequence
    // ========================================================================
    initial begin
        $display("========================================");
        $display("  DMA Controller Testbench");
        $display("========================================");

        // Reset
        apply_reset();

        // Run test sequences
        tc_S1_reset();
        tc_S2_register_rw();
        tc_S3_mem_to_mem();
        tc_S4_mem_to_periph();
        tc_S5_periph_to_mem();
        tc_S6_scatter_gather();
        tc_S7_interrupt_flow();
        tc_S8_error_inject();
        tc_S9_priority_arb();
        tc_S10_pause_abort();

        // Summary
        $display("");
        $display("========================================");
        $display("  Result: %0d/%0d tests passed", pass_count, test_count);
        if (fail_count > 0)
            $display("  FAILED: %0d tests", fail_count);
        else
            $display("  ALL PASSED");
        $display("========================================");

        $finish;
    end

endmodule
