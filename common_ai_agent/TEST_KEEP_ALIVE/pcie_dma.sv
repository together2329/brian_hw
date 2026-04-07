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
    parameter int unsigned DATA_WIDTH     = 128,
    parameter int unsigned ADDR_WIDTH     = 64,
    parameter int unsigned MAX_PAYLOAD    = 256,   // bytes (128, 256, 512, 1024)
    parameter int unsigned MAX_OUTSTANDING = 32,   // max outstanding read tags
    parameter int unsigned KEEP_WIDTH     = DATA_WIDTH / 8
)(
    // ----------------------------------------------------------------
    // Clock & Reset
    // ----------------------------------------------------------------
    input  logic                          clk,
    input  logic                          rst_n,

    // ----------------------------------------------------------------
    // Descriptor / CSR Interface (simple register access)
    // ----------------------------------------------------------------
    input  logic [63:0]                   csr_src_addr,
    input  logic [63:0]                   csr_dst_addr,
    input  logic [31:0]                   csr_xfer_len,  // bytes
    input  logic                          csr_direction,  // 0=PCIe->Local, 1=Local->PCIe
    input  logic                          csr_start,
    output logic                          csr_busy,
    output logic                          csr_done,
    output logic                          csr_error,
    output logic [31:0]                   csr_status,

    // ----------------------------------------------------------------
    // TLP TX Stream (to PCIe core)
    // ----------------------------------------------------------------
    output logic [DATA_WIDTH-1:0]         tx_tlp_data,
    output logic [KEEP_WIDTH-1:0]         tx_tlp_keep,
    output logic                          tx_tlp_valid,
    output logic                          tx_tlp_sop,    // Start of TLP
    output logic                          tx_tlp_eop,    // End of TLP
    input  logic                          tx_tlp_ready,

    // ----------------------------------------------------------------
    // TLP RX Stream (from PCIe core)
    // ----------------------------------------------------------------
    input  logic [DATA_WIDTH-1:0]         rx_tlp_data,
    input  logic [KEEP_WIDTH-1:0]         rx_tlp_keep,
    input  logic                          rx_tlp_valid,
    input  logic                          rx_tlp_sop,
    input  logic                          rx_tlp_eop,
    output logic                          rx_tlp_ready,

    // ----------------------------------------------------------------
    // Local Memory Interface (to BRAM/FIFO)
    // ----------------------------------------------------------------
    output logic [ADDR_WIDTH-1:0]         lcl_mem_addr,
    output logic [DATA_WIDTH-1:0]         lcl_mem_wdata,
    output logic                          lcl_mem_wen,
    input  logic [DATA_WIDTH-1:0]         lcl_mem_rdata,
    output logic                          lcl_mem_ren,
    input  logic                          lcl_mem_rvalid,

    // ----------------------------------------------------------------
    // Interrupt
    // ----------------------------------------------------------------
    output logic                          irq
);

    import pcie_dma_pkg::*;

    // ----------------------------------------------------------------
    // Internal Signals
    // ----------------------------------------------------------------
    dma_state_t   state_reg;
    logic [63:0]  current_addr;
    logic [63:0]  bytes_remaining;   // promote to 64-bit to avoid width mismatch
    logic [63:0]  bytes_requested;
    logic [63:0]  bytes_completed;
    logic [7:0]   next_tag;
    logic [7:0]   outstanding_cnt;

    // Local address pointer for BRAM writes
    logic [ADDR_WIDTH-1:0] lcl_wr_ptr;
    logic [ADDR_WIDTH-1:0] lcl_rd_ptr;

    // ----------------------------------------------------------------
    // TLP Construction Helpers
    // ----------------------------------------------------------------
    logic [31:0] tlp_dw0;
    logic [31:0] tlp_dw1;
    logic [31:0] tlp_dw2;
    logic [31:0] tlp_dw3;
    logic        use_4dw;

    // Determine if we need 4DW header (address > 4GB boundary)
    assign use_4dw = (current_addr[63:32] != 32'h0);

    // Request size calculation (combinational, used in state machine)
    logic [63:0] req_bytes_read;
    logic [63:0] req_bytes_write;
    logic [63:0] max_payload_64;
    assign max_payload_64  = 64'(MAX_PAYLOAD);
    assign req_bytes_read  = (bytes_remaining >= max_payload_64) ? max_payload_64 : bytes_remaining;
    assign req_bytes_write = (bytes_remaining >= max_payload_64) ? max_payload_64 : bytes_remaining;

    // ----------------------------------------------------------------
    // DMA State Machine
    // ----------------------------------------------------------------
    always_ff @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state_reg       <= DMA_IDLE;
            current_addr    <= '0;
            bytes_remaining <= '0;
            bytes_requested <= '0;
            bytes_completed <= '0;
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
            // Default: pulse signals
            csr_done  <= 1'b0;
            irq       <= 1'b0;

            case (state_reg)
                // ----------------------------------------------------
                DMA_IDLE: begin
                    csr_busy <= 1'b0;
                    if (csr_start) begin
                        csr_busy        <= 1'b1;
                        csr_error       <= 1'b0;
                        csr_status      <= '0;
                        current_addr    <= csr_src_addr;
                        bytes_remaining <= 64'(csr_xfer_len);
                        bytes_requested <= '0;
                        bytes_completed <= '0;
                        next_tag        <= '0;
                        outstanding_cnt <= '0;
                        lcl_wr_ptr      <= '0;
                        lcl_rd_ptr      <= '0;
                        state_reg       <= DMA_SETUP;
                    end
                end

                // ----------------------------------------------------
                DMA_SETUP: begin
                    if (bytes_remaining == '0) begin
                        state_reg <= DMA_DONE;
                    end else if (csr_direction == 1'b0) begin
                        // PCIe -> Local: Issue Memory Read TLPs
                        state_reg <= DMA_READ;
                    end else begin
                        // Local -> PCIe: Issue Memory Write TLPs
                        state_reg <= DMA_WRITE;
                    end
                end

                // ----------------------------------------------------
                DMA_READ: begin
                    // Issue Memory Read requests until we run out of
                    // tags or bytes
                    if (bytes_remaining > '0 && outstanding_cnt < 8'(MAX_OUTSTANDING)) begin
                        if (tx_tlp_ready) begin
                            current_addr    <= current_addr + req_bytes_read;
                            bytes_remaining <= bytes_remaining - req_bytes_read;
                            bytes_requested <= bytes_requested + req_bytes_read;
                            next_tag        <= next_tag + 8'd1;
                            outstanding_cnt <= outstanding_cnt + 8'd1;

                            // Done issuing reads?
                            if (bytes_remaining <= req_bytes_read) begin
                                state_reg <= DMA_WAIT;
                            end
                        end
                    end else begin
                        state_reg <= DMA_WAIT;
                    end
                end

                // ----------------------------------------------------
                DMA_WRITE: begin
                    // Issue Memory Write TLPs with data from local memory
                    if (bytes_remaining > '0) begin
                        if (tx_tlp_ready) begin
                            current_addr    <= current_addr + req_bytes_write;
                            bytes_remaining <= bytes_remaining - req_bytes_write;
                            bytes_completed <= bytes_completed + req_bytes_write;
                            lcl_rd_ptr      <= lcl_rd_ptr + req_bytes_write[ADDR_WIDTH-1:0];

                            if (bytes_remaining <= req_bytes_write) begin
                                state_reg <= DMA_DONE;
                            end
                        end
                    end else begin
                        state_reg <= DMA_DONE;
                    end
                end

                // ----------------------------------------------------
                DMA_WAIT: begin
                    // Wait for all outstanding read completions
                    if (outstanding_cnt == '0) begin
                        state_reg <= DMA_DONE;
                    end
                end

                // ----------------------------------------------------
                DMA_DONE: begin
                    csr_busy   <= 1'b0;
                    csr_done   <= 1'b1;
                    csr_status <= 32'h0000_0001; // Success
                    if (csr_start == 1'b0) begin
                        csr_done  <= 1'b0;
                        state_reg <= DMA_IDLE;
                    end
                end

                // ----------------------------------------------------
                DMA_ERROR: begin
                    csr_busy  <= 1'b0;
                    csr_error <= 1'b1;
                    csr_done  <= 1'b1;
                    state_reg <= DMA_IDLE;
                end

                // ----------------------------------------------------
                default: begin
                    state_reg <= DMA_IDLE;
                end
            endcase

            // Handle RX completions (for DMA reads)
            if (rx_tlp_valid && rx_tlp_sop) begin
                // Check for Completion with Data (CPLD)
                logic [4:0] rx_type;
                rx_type = rx_tlp_data[28:24]; // Type field in DW0

                if (rx_type == TYPE_CPLD) begin
                    // Extract byte count from completion
                    logic [11:0] cpl_byte_count;
                    cpl_byte_count = rx_tlp_data[43:32]; // Byte Count in DW1

                    bytes_completed <= bytes_completed + 64'(cpl_byte_count);
                    lcl_wr_ptr      <= lcl_wr_ptr + ADDR_WIDTH'(cpl_byte_count);

                    if (outstanding_cnt > '0) begin
                        outstanding_cnt <= outstanding_cnt - 8'd1;
                    end

                    // Write data to local memory
                    lcl_mem_wen   <= 1'b1;
                    lcl_mem_addr  <= lcl_wr_ptr;
                    lcl_mem_wdata <= rx_tlp_data; // Simplified: real design needs alignment
                end
            end else begin
                lcl_mem_wen <= 1'b0;
            end
        end
    end

    // ----------------------------------------------------------------
    // TLP TX Construction (combinational)
    //   For simplicity, this module builds one TLP per clock.
    //   - 3DW header = 96 bits, fits in 128-bit data with room for payload
    //   - 4DW header = 128 bits, occupies a full 128-bit beat
    //   When DATA_WIDTH >= 256, header + payload can fit in one beat.
    // ----------------------------------------------------------------
    always_comb begin
        tx_tlp_data  = '0;
        tx_tlp_keep  = '0;
        tx_tlp_valid = 1'b0;
        tx_tlp_sop   = 1'b0;
        tx_tlp_eop   = 1'b0;

        tlp_dw0 = '0;
        tlp_dw1 = '0;
        tlp_dw2 = '0;
        tlp_dw3 = '0;

        if (state_reg == DMA_READ) begin
            // Build Memory Read TLP header (no data payload for MRd)
            tx_tlp_valid = 1'b1;
            tx_tlp_sop   = 1'b1;
            tx_tlp_eop   = 1'b1;

            if (use_4dw) begin
                // 4DW Memory Read: 128-bit header, no data
                tlp_dw0 = {FMT_4DW_NO_DATA, TYPE_MRD, 9'b0, 1'b0, 1'b0, 10'd0};
                tlp_dw1 = {16'h0000, next_tag, 4'b0000, 4'b1111}; // Requester ID=0, Tag, BE
                tlp_dw2 = current_addr[63:32];
                tlp_dw3 = {current_addr[31:2], 2'b00};
                tx_tlp_data = {tlp_dw3, tlp_dw2, tlp_dw1, tlp_dw0};
                tx_tlp_keep = 16'hFFFF;
            end else begin
                // 3DW Memory Read: 96-bit header, no data
                tlp_dw0 = {FMT_3DW_NO_DATA, TYPE_MRD, 9'b0, 1'b0, 1'b0, 10'd0};
                tlp_dw1 = {16'h0000, next_tag, 4'b0000, 4'b1111};
                tlp_dw2 = {current_addr[31:2], 2'b00};
                tx_tlp_data[95:0]  = {tlp_dw2, tlp_dw1, tlp_dw0};
                tx_tlp_keep        = 16'h0FFF;
            end
        end else if (state_reg == DMA_WRITE) begin
            // Build Memory Write TLP header + data
            tx_tlp_valid = 1'b1;
            tx_tlp_sop   = 1'b1;
            tx_tlp_eop   = 1'b1;

            if (use_4dw) begin
                // 4DW MWr: header in first 128 bits
                // For DATA_WIDTH=128, header only (data on next beat in real design)
                // For DATA_WIDTH>=256, header + payload in one beat
                tlp_dw0 = {FMT_4DW_DATA, TYPE_MWR, 9'b0, 1'b0, 1'b0, 10'd0};
                tlp_dw1 = {16'h0000, 8'd0, 4'b0000, 4'b1111};
                tlp_dw2 = current_addr[63:32];
                tlp_dw3 = {current_addr[31:2], 2'b00};
                // Place header in lower bits
                tx_tlp_data[127:0] = {tlp_dw3, tlp_dw2, tlp_dw1, tlp_dw0};
                if (DATA_WIDTH >= 256) begin : gen_4dw_payload
                    // Append payload after 128-bit header
                    tx_tlp_data[DATA_WIDTH-1:128] = lcl_mem_rdata[DATA_WIDTH-128-1:0];
                end
                tx_tlp_keep = {KEEP_WIDTH{1'b1}};
            end else begin
                // 3DW MWr: 96-bit header + 32 bits of data in 128-bit beat
                tlp_dw0 = {FMT_3DW_DATA, TYPE_MWR, 9'b0, 1'b0, 1'b0, 10'd0};
                tlp_dw1 = {16'h0000, 8'd0, 4'b0000, 4'b1111};
                tlp_dw2 = {current_addr[31:2], 2'b00};
                // Header (96 bits) + payload (DATA_WIDTH-96 bits)
                tx_tlp_data[95:0] = {tlp_dw2, tlp_dw1, tlp_dw0};
                if (DATA_WIDTH > 96) begin : gen_3dw_payload
                    tx_tlp_data[DATA_WIDTH-1:96] = lcl_mem_rdata[DATA_WIDTH-97:0];
                end
                tx_tlp_keep = {KEEP_WIDTH{1'b1}};
            end
        end
    end

    // ----------------------------------------------------------------
    // Local memory read control (for DMA Write path)
    // ----------------------------------------------------------------
    assign lcl_mem_ren   = (state_reg == DMA_WRITE) ? 1'b1 : 1'b0;
    assign lcl_mem_addr  = (state_reg == DMA_WRITE) ? lcl_rd_ptr : lcl_wr_ptr;

    // ----------------------------------------------------------------
    // RX always ready to accept completions
    // ----------------------------------------------------------------
    assign rx_tlp_ready = 1'b1;

endmodule : pcie_dma
