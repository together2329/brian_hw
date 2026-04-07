// ============================================================================
// pcie_dma.sv - Simple PCIe DMA Engine
//
// Features:
//   - DMA Read  : Reads data from PCIe host memory into a local buffer
//   - DMA Write : Writes data from local buffer to PCIe host memory
//   - Simple descriptor-based programming model
//   - AXI4-Stream style TLP interface to PCIe core
//   - Parameterizable data width (128/256/512-bit)
//   - Tag tracking for outstanding read requests
//
// Interfaces:
//   - TLP TX/RX stream  (connects to PCIe core)
//   - Descriptor registers (CSRs for host/software)
//   - Local memory interface (BRAM/FIFO)
// ============================================================================
module pcie_dma #(
    parameter int unsigned DATA_WIDTH      = 128,
    parameter int unsigned ADDR_WIDTH      = 64,
    parameter int unsigned MAX_PAYLOAD     = 256,
    parameter int unsigned MAX_OUTSTANDING = 32,
    parameter int unsigned KEEP_WIDTH      = DATA_WIDTH / 8
)(
    // Clock & Reset
    input  logic                          clk,
    input  logic                          rst_n,

    // Descriptor / CSR Interface
    input  logic [63:0]                   csr_src_addr,
    input  logic [63:0]                   csr_dst_addr,
    input  logic [31:0]                   csr_xfer_len,
    input  logic                          csr_direction,  // 0=PCIe->Local, 1=Local->PCIe
    input  logic                          csr_start,
    output logic                          csr_busy,
    output logic                          csr_done,
    output logic                          csr_error,
    output logic [31:0]                   csr_status,

    // TLP TX Stream (to PCIe core)
    output logic [DATA_WIDTH-1:0]         tx_tlp_data,
    output logic [KEEP_WIDTH-1:0]         tx_tlp_keep,
    output logic                          tx_tlp_valid,
    output logic                          tx_tlp_sop,
    output logic                          tx_tlp_eop,
    input  logic                          tx_tlp_ready,

    // TLP RX Stream (from PCIe core)
    input  logic [DATA_WIDTH-1:0]         rx_tlp_data,
    input  logic [KEEP_WIDTH-1:0]         rx_tlp_keep,
    input  logic                          rx_tlp_valid,
    input  logic                          rx_tlp_sop,
    input  logic                          rx_tlp_eop,
    output logic                          rx_tlp_ready,

    // Local Memory Interface (to BRAM/FIFO)
    output logic [ADDR_WIDTH-1:0]         lcl_mem_addr,
    output logic [DATA_WIDTH-1:0]         lcl_mem_wdata,
    output logic                          lcl_mem_wen,
    input  logic [DATA_WIDTH-1:0]         lcl_mem_rdata,
    output logic                          lcl_mem_ren,
    input  logic                          lcl_mem_rvalid,

    // Interrupt
    output logic                          irq
);

    import pcie_dma_pkg::*;

    // ----------------------------------------------------------------
    // Internal Signals - all same-width to avoid type mismatch
    // ----------------------------------------------------------------
    dma_state_t             state_reg;

    logic [63:0]            cur_addr;
    logic [63:0]            xfer_left;       // bytes remaining
    logic [63:0]            xfer_done;       // bytes completed
    logic [63:0]            xfer_requested;  // bytes requested (reads)
    logic [7:0]             next_tag;
    logic [7:0]             outstanding_cnt;

    logic [ADDR_WIDTH-1:0]  lcl_wr_ptr;
    logic [ADDR_WIDTH-1:0]  lcl_rd_ptr;

    // ----------------------------------------------------------------
    // Derived signals
    // ----------------------------------------------------------------
    logic       use_4dw;
    logic [7:0] max_outstanding_8;
    logic [63:0] max_payload_64;

    assign use_4dw           = (cur_addr[63:32] != 32'h0);
    assign max_outstanding_8 = 8'(MAX_OUTSTANDING);
    assign max_payload_64    = 64'(MAX_PAYLOAD);

    // Request size for current beat
    logic [63:0] req_size;
    assign req_size = (xfer_left >= max_payload_64) ? max_payload_64 : xfer_left;

    // ----------------------------------------------------------------
    // DMA State Machine (sequential)
    // ----------------------------------------------------------------
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state_reg       <= DMA_IDLE;
            cur_addr        <= '0;
            xfer_left       <= '0;
            xfer_done       <= '0;
            xfer_requested  <= '0;
            next_tag        <= '0;
            outstanding_cnt <= '0;
            lcl_wr_ptr      <= '0;
            lcl_rd_ptr      <= '0;
            csr_busy        <= 1'b0;
            csr_done        <= 1'b0;
            csr_error       <= 1'b0;
            csr_status      <= '0;
            irq             <= 1'b0;
        end else begin
            csr_done <= 1'b0;
            irq      <= 1'b0;

            case (state_reg)

                DMA_IDLE: begin
                    csr_busy <= 1'b0;
                    if (csr_start) begin
                        csr_busy        <= 1'b1;
                        csr_error       <= 1'b0;
                        csr_status      <= '0;
                        cur_addr        <= csr_src_addr;
                        xfer_left       <= {32'h0, csr_xfer_len};
                        xfer_done       <= '0;
                        xfer_requested  <= '0;
                        next_tag        <= '0;
                        outstanding_cnt <= '0;
                        lcl_wr_ptr      <= '0;
                        lcl_rd_ptr      <= '0;
                        state_reg       <= DMA_SETUP;
                    end
                end

                DMA_SETUP: begin
                    if (xfer_left == 64'd0) begin
                        state_reg <= DMA_DONE;
                    end else if (csr_direction == 1'b0) begin
                        state_reg <= DMA_READ;
                    end else begin
                        state_reg <= DMA_WRITE;
                    end
                end

                DMA_READ: begin
                    if ((xfer_left > 64'd0) && (outstanding_cnt < max_outstanding_8)) begin
                        if (tx_tlp_ready) begin
                            cur_addr        <= cur_addr + req_size;
                            xfer_left       <= xfer_left - req_size;
                            xfer_requested  <= xfer_requested + req_size;
                            next_tag        <= next_tag + 8'd1;
                            outstanding_cnt <= outstanding_cnt + 8'd1;
                            if (xfer_left <= req_size) begin
                                state_reg <= DMA_WAIT;
                            end
                        end
                    end else begin
                        state_reg <= DMA_WAIT;
                    end
                end

                DMA_WRITE: begin
                    if (xfer_left > 64'd0) begin
                        if (tx_tlp_ready) begin
                            cur_addr   <= cur_addr + req_size;
                            xfer_left  <= xfer_left - req_size;
                            xfer_done  <= xfer_done + req_size;
                            lcl_rd_ptr <= lcl_rd_ptr + lcl_rd_ptr'(req_size);
                            if (xfer_left <= req_size) begin
                                state_reg <= DMA_DONE;
                            end
                        end
                    end else begin
                        state_reg <= DMA_DONE;
                    end
                end

                DMA_WAIT: begin
                    if (outstanding_cnt == 8'd0) begin
                        state_reg <= DMA_DONE;
                    end
                end

                DMA_DONE: begin
                    csr_busy   <= 1'b0;
                    csr_done   <= 1'b1;
                    csr_status <= 32'h0000_0001;
                    if (csr_start == 1'b0) begin
                        csr_done  <= 1'b0;
                        state_reg <= DMA_IDLE;
                    end
                end

                DMA_ERROR: begin
                    csr_busy  <= 1'b0;
                    csr_error <= 1'b1;
                    csr_done  <= 1'b1;
                    state_reg <= DMA_IDLE;
                end

                default: begin
                    state_reg <= DMA_IDLE;
                end
            endcase

            // Handle RX completions (for DMA reads) u2014 runs in parallel
            if (rx_tlp_valid && rx_tlp_sop) begin
                if (rx_tlp_data[28:24] == TYPE_CPLD) begin
                    logic [31:0] cpl_bc;
                    cpl_bc = {20'h0, rx_tlp_data[43:32]};

                    xfer_done  <= xfer_done + {32'h0, cpl_bc};
                    lcl_wr_ptr <= lcl_wr_ptr + lcl_wr_ptr'(cpl_bc);

                    if (outstanding_cnt > 8'd0) begin
                        outstanding_cnt <= outstanding_cnt - 8'd1;
                    end

                    lcl_mem_wen   <= 1'b1;
                    lcl_mem_addr  <= lcl_wr_ptr;
                    lcl_mem_wdata <= rx_tlp_data;
                end
            end else begin
                lcl_mem_wen <= 1'b0;
            end
        end
    end

    // ----------------------------------------------------------------
    // TLP TX Construction (combinational)
    // ----------------------------------------------------------------
    always_comb begin
        tx_tlp_data  = '0;
        tx_tlp_keep  = '0;
        tx_tlp_valid = 1'b0;
        tx_tlp_sop   = 1'b0;
        tx_tlp_eop   = 1'b0;

        if (state_reg == DMA_READ) begin
            tx_tlp_valid = 1'b1;
            tx_tlp_sop   = 1'b1;
            tx_tlp_eop   = 1'b1;

            if (use_4dw) begin
                tx_tlp_data[31:0]   = {FMT_4DW_NO_DATA, TYPE_MRD, 9'b0, 1'b0, 1'b0, 10'd0};
                tx_tlp_data[63:32]  = {16'h0000, next_tag, 4'b0000, 4'b1111};
                tx_tlp_data[95:64]  = cur_addr[63:32];
                tx_tlp_data[127:96] = {cur_addr[31:2], 2'b00};
                tx_tlp_keep = {KEEP_WIDTH{1'b1}};
            end else begin
                tx_tlp_data[31:0]  = {FMT_3DW_NO_DATA, TYPE_MRD, 9'b0, 1'b0, 1'b0, 10'd0};
                tx_tlp_data[63:32] = {16'h0000, next_tag, 4'b0000, 4'b1111};
                tx_tlp_data[95:64] = {cur_addr[31:2], 2'b00};
                tx_tlp_keep[11:0]  = 12'hFFF;
            end
        end else if (state_reg == DMA_WRITE) begin
            tx_tlp_valid = 1'b1;
            tx_tlp_sop   = 1'b1;
            tx_tlp_eop   = 1'b1;

            if (use_4dw) begin
                // 4DW header = 128 bits, payload follows (only if DATA_WIDTH > 128)
                tx_tlp_data[31:0]   = {FMT_4DW_DATA, TYPE_MWR, 9'b0, 1'b0, 1'b0, 10'd0};
                tx_tlp_data[63:32]  = {16'h0000, 8'd0, 4'b0000, 4'b1111};
                tx_tlp_data[95:64]  = cur_addr[63:32];
                tx_tlp_data[127:96] = {cur_addr[31:2], 2'b00};
                if (DATA_WIDTH > 128) begin : mwr_4dw_payload
                    tx_tlp_data[DATA_WIDTH-1:128] = lcl_mem_rdata[DATA_WIDTH-129:0];
                end
                tx_tlp_keep = {KEEP_WIDTH{1'b1}};
            end else begin
                // 3DW header = 96 bits, payload in remaining bits
                tx_tlp_data[31:0]  = {FMT_3DW_DATA, TYPE_MWR, 9'b0, 1'b0, 1'b0, 10'd0};
                tx_tlp_data[63:32] = {16'h0000, 8'd0, 4'b0000, 4'b1111};
                tx_tlp_data[95:64] = {cur_addr[31:2], 2'b00};
                if (DATA_WIDTH > 96) begin : mwr_3dw_payload
                    tx_tlp_data[DATA_WIDTH-1:96] = lcl_mem_rdata[DATA_WIDTH-97:0];
                end
                tx_tlp_keep = {KEEP_WIDTH{1'b1}};
            end
        end
    end

    // ----------------------------------------------------------------
    // Local memory read control
    // ----------------------------------------------------------------
    assign lcl_mem_ren  = (state_reg == DMA_WRITE) ? 1'b1 : 1'b0;
    assign lcl_mem_addr = (state_reg == DMA_WRITE) ? lcl_rd_ptr : lcl_wr_ptr;

    // RX always ready
    assign rx_tlp_ready = 1'b1;

endmodule : pcie_dma
